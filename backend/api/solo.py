"""
ソロ感情演技モード用APIエンドポイント
音声アップロード → AI推論 → スコア返却
"""

import os
import tempfile
import shutil
import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import random


logger = logging.getLogger(__name__)

# LLMサービスをインポート
from services.llm_service import get_llm_service

# 実際のモデルが利用可能かチェックして適切なモジュールをインポート
try:
    from transformers import HubertModel
    # 実際のHubertモデルが利用可能な場合
    from kushinada_infer import classify_emotion_with_score
    MODEL_TYPE = "REAL"
    logger.info("🤖 実際のKushinada Hubertモデルを使用します")
except ImportError:
    # Transformersが利用できない場合はダミーモデルを使用
    from kushinada_infer_dummy import classify_emotion_with_score
    MODEL_TYPE = "DUMMY"
    logger.info("🎭 ダミーモデルを使用します（開発・テスト用）")

router = APIRouter(prefix="/api/v1/solo", tags=["solo"])

# 感情マッピング（ソロモード用）
SOLO_EMOTIONS = {
    0: {"name_ja": "中立", "name_en": "neutral"},
    1: {"name_ja": "喜び", "name_en": "happy"},
    2: {"name_ja": "怒り", "name_en": "angry"},
    3: {"name_ja": "悲しみ", "name_en": "sad"}
}

class PredictionResponse(BaseModel):
    """推論結果のレスポンスモデル"""
    emotion: str  # 推論された感情ラベル
    predicted_class: int  # 推論されたクラスID (0-3)
    target_class: int  # 目標クラスID (0-3)
    score: int  # スコア (0-100)
    confidence: float  # 予測クラスの確信度 (0-100)
    is_correct: bool  # 正解かどうか
    message: str  # 結果メッセージ

class DialogueRequest(BaseModel):
    """セリフ生成リクエストモデル"""
    emotion_id: int  # 感情ID (0-3)

class DialogueResponse(BaseModel):
    """セリフ生成レスポンスモデル"""
    emotion_id: int  # 感情ID
    emotion_name: str  # 感情名
    dialogue: str  # 生成されたセリフ

def convert_audio_to_wav(input_file_path: str, output_file_path: str) -> bool:
    """
    音声ファイルをWAV形式に変換
    
    Args:
        input_file_path: 入力ファイルパス
        output_file_path: 出力WAVファイルパス
        
    Returns:
        変換成功かどうか
    """
    try:
        from pydub import AudioSegment
        
        logger.info(f"🔄 音声変換開始: {input_file_path} → {output_file_path}")
        
        # 音声ファイルの読み込み（pydubが自動でフォーマット判定）
        audio = AudioSegment.from_file(input_file_path)
        
        # WAVフォーマットで保存（16kHz, モノラル）
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_file_path, format="wav")
        
        logger.info(f"✅ 音声変換完了: {output_file_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 音声変換エラー: {e}")
        return False

@router.get("/dialogue")
async def generate_dialogue():
    """
    ランダム感情とLLM生成セリフを返す
    """
    try:
        logger.info("🎭 ソロモード用セリフ生成開始")
        
        # ランダムに感情を選択
        emotion_id = random.randint(0, 3)
        emotion_info = SOLO_EMOTIONS[emotion_id]
        
        logger.info(f"🎲 選択された感情: {emotion_info['name_ja']} (ID: {emotion_id})")
        
        # LLMサービスでセリフ生成
        llm_service = get_llm_service()
        
        # シンプルなセリフ生成（感情は既に選択済み）
        if llm_service.client:
            try:
                dialogue = await llm_service._generate_phrase_with_openai()
            except Exception as e:
                logger.warning(f"⚠️ LLM生成エラー、フォールバック使用: {e}")
                dialogue = random.choice(llm_service.fallback_phrases)
        else:
            logger.info("🎭 LLMクライアント未初期化、フォールバック使用")
            dialogue = random.choice(llm_service.fallback_phrases)
        
        response = DialogueResponse(
            emotion_id=emotion_id,
            emotion_name=emotion_info['name_ja'],
            dialogue=dialogue
        )
        
        logger.info(f"✅ セリフ生成完了: {dialogue} ({emotion_info['name_ja']})")
        return response
        
    except Exception as e:
        logger.error(f"❌ セリフ生成エラー: {e}", exc_info=True)
        # フォールバック
        fallback_emotion = 0  # 中立
        fallback_dialogue = "こんにちは"
        
        return DialogueResponse(
            emotion_id=fallback_emotion,
            emotion_name=SOLO_EMOTIONS[fallback_emotion]['name_ja'],
            dialogue=fallback_dialogue
        )

@router.post("/predict", response_model=PredictionResponse)
async def predict_emotion(
    file: UploadFile = File(...),
    target_emotion: int = Form(...),
    device_id: str = Form(None)
):
    """
    音声ファイルから感情を推論し、スコアを算出
    
    Args:
        file: アップロードされた音声ファイル（WebM/WAV等）
        target_emotion: 目標感情のクラスID (0=中立, 1=喜び, 2=怒り, 3=悲しみ)
        device_id: 端末固定ID（統計管理用）
        
    Returns:
        推論結果とスコア
    """
    temp_input_path = None
    temp_wav_path = None
    
    try:
        # リクエストパラメータのデバッグログ
        logger.info(f"🔍 受信パラメータ - file: {file}, target_emotion: {target_emotion}, device_id: {device_id}")
        logger.info(f"🔍 ファイル詳細 - filename: {file.filename if file else 'None'}, content_type: {file.content_type if file else 'None'}")
        
        # device_idがNoneの場合はランダムUUIDを生成
        if device_id is None:
            device_id = str(uuid.uuid4())
            logger.info(f"📱 デバイスIDが未指定のため、一時ID生成: {device_id}")
        
        # session_idをDB制限の36文字以内に調整
        if len(device_id) > 36:
            # "device_"プレフィックスを削除してUUID部分のみ使用
            if device_id.startswith("device_"):
                session_id = device_id[7:]  # "device_"を削除
            else:
                # 長すぎる場合は最初の36文字を使用
                session_id = device_id[:36]
            logger.info(f"📱 デバイスID調整: {device_id} -> {session_id}")
        else:
            session_id = device_id
        
        logger.info(f"🎤 音声推論リクエスト受信 - ファイル: {file.filename}, 目標感情: {target_emotion}, セッションID: {session_id}")
        
        # バリデーション
        if target_emotion not in [0, 1, 2, 3]:
            raise HTTPException(
                status_code=400,
                detail="target_emotion は 0-3 の範囲で指定してください（0=中立, 1=喜び, 2=怒り, 3=悲しみ）"
            )
        
        if not file.filename:
            raise HTTPException(status_code=400, detail="ファイルが指定されていません")
        
        # ファイルサイズチェック（10MB制限）
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(status_code=413, detail="ファイルサイズが大きすぎます（10MB以下にしてください）")
        
        logger.info(f"📁 受信ファイル情報 - サイズ: {len(file_content)} bytes, 形式: {file.content_type}")
        
        # ハイブリッドストレージに永続保存
        from services.storage_service import get_storage_service
        storage_service = get_storage_service()
        
        # 一時ファイルに保存（変換用）
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_input:
            temp_input.write(file_content)
            temp_input_path = temp_input.name
        
        # WAVファイルに変換
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            temp_wav_path = temp_wav.name
        
        # 音声変換実行
        conversion_success = convert_audio_to_wav(temp_input_path, temp_wav_path)
        if not conversion_success:
            raise HTTPException(status_code=400, detail="音声ファイルの変換に失敗しました")
        
        # 永続ストレージに保存
        with open(temp_wav_path, 'rb') as wav_file:
            wav_data = wav_file.read()
        
        # 調整済みのセッションIDを使用
        audio_url = storage_service.save_audio(wav_data, session_id)
        logger.info(f"💾 音声ファイル永続保存完了: {audio_url}")
        
        # AI推論用のファイルパス取得
        audio_path = storage_service.get_audio_path(audio_url)
        
        # AI推論実行
        logger.info("🧠 AI推論実行中...")
        result = classify_emotion_with_score(audio_path, target_emotion)
        
        # スコア計算：正解なら60点ボーナス
        base_score = result["score"]
        bonus_score = 50 if result["is_correct"] else 0
        final_score = min(base_score + bonus_score, 100)  # 100点上限
        
        logger.info(f"📊 スコア計算: ベース{base_score}点 + ボーナス{bonus_score}点 = {final_score}点")
        
        # 結果メッセージ生成
        emotion_names = {0: "中立", 1: "喜び", 2: "怒り", 3: "悲しみ"}
        target_name = emotion_names.get(target_emotion, "不明")
        
        if result["is_correct"]:
            message = f"🎉 正解！{target_name}の感情を正確に演技できました！(+60点ボーナス)"
        else:
            predicted_name = emotion_names.get(result["predicted_class"], "不明")
            message = f"目標は「{target_name}」でしたが、「{predicted_name}」として認識されました。"
        
        # データベースに保存
        try:
            logger.info("🔍 Starting database save process")
            from services.database_service import get_database_service
            db_service = await get_database_service()
            logger.info("🔍 Got database service instance")
            
            # 調整済みのsession_idを使用
            user_session_id = session_id
            
            # 感情ID変換（数値から文字列へ）
            emotion_id_map = {0: "neutral", 1: "joy", 2: "anger", 3: "sadness"}
            target_emotion_str = emotion_id_map.get(target_emotion, "neutral")
            predicted_emotion_str = emotion_id_map.get(result["predicted_class"], "neutral")
            
            # 台詞取得（実際のアプリではフロントエンドから受信）
            prompt_text = f"AI生成セリフ - {target_name}の感情演技"
            
            # DB保存用データ作成
            session_data = {
                "session_id": user_session_id,
                "target_emotion_id": target_emotion_str,
                "prompt_text": prompt_text,
                "ai_predicted_emotion_id": predicted_emotion_str,
                "ai_confidence": result["confidence"] / 100.0,  # 0-1の範囲に変換
                "is_correct": result["is_correct"],
                "base_score": base_score,
                "bonus_score": bonus_score,
                "final_score": final_score,
                "audio_url": audio_url,
                "duration": None  # 音声長は後で実装
            }
            
            # セッションIDの長さを確認
            logger.info(f"🔍 session_id length: {len(user_session_id)} chars")
            logger.info(f"🔍 About to save session_data: {session_data}")
            solo_session_id = await db_service.save_solo_session(session_data)
            logger.info(f"💾 ソロセッションDB保存完了: {solo_session_id}")
            
        except Exception as db_error:
            logger.warning(f"⚠️ DB保存エラー（処理は継続）: {db_error}")
        
        # レスポンス作成（修正されたスコアを使用）
        response = PredictionResponse(
            emotion=result["emotion"],
            predicted_class=result["predicted_class"],
            target_class=result["target_class"],
            score=final_score,
            confidence=result["confidence"],
            is_correct=result["is_correct"],
            message=message
        )
        
        logger.info(f"🎉 推論完了 - 最終スコア: {final_score}点, 正解: {result['is_correct']}")
        
        return response
        
    except HTTPException as he:
        # HTTPExceptionの詳細をログに記録
        logger.error(f"❌ HTTPException: status={he.status_code}, detail={he.detail}")
        raise he
    except Exception as e:
        logger.error(f"❌ 予期しないエラー: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"内部サーバーエラー: {str(e)}")
    
    finally:
        # 一時ファイルのクリーンアップ
        for temp_path in [temp_input_path, temp_wav_path]:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.info(f"🗑️ 一時ファイル削除: {temp_path}")
                except Exception as e:
                    logger.warning(f"⚠️ 一時ファイル削除失敗: {temp_path} - {e}")

@router.get("/health")
async def health_check():
    """ソロモード機能のヘルスチェック"""
    try:
        # 使用中のモジュールに応じて適切なインポート
        if MODEL_TYPE == "REAL":
            from kushinada_infer import get_emotion_classifier
        else:
            from kushinada_infer_dummy import get_emotion_classifier
        
        classifier = get_emotion_classifier()
        
        # チェックポイントファイルの存在確認
        ckpt_path = "./ckpt/dev-best.ckpt"
        ckpt_exists = os.path.exists(ckpt_path)
        
        return {
            "status": "healthy",
            "model_type": MODEL_TYPE,
            "checkpoint_exists": ckpt_exists,
            "checkpoint_path": ckpt_path,
            "message": f"ソロ感情演技モード（{MODEL_TYPE}モデル）は正常に動作しています"
        }
    except Exception as e:
        logger.error(f"❌ ヘルスチェックエラー: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "model_type": MODEL_TYPE,
                "error": str(e),
                "message": "ソロ感情演技モードでエラーが発生しています"
            }
        )

@router.get("/stats/{device_id}")
async def get_solo_stats(device_id: str):
    """ソロプレイ統計取得（端末別）"""
    try:
        from services.database_service import get_database_service
        db_service = await get_database_service()
        
        stats = await db_service.get_solo_stats(device_id)
        logger.info(f"📊 統計取得完了: {device_id}")
        
        return {
            "status": "success",
            "device_id": device_id,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ 統計取得エラー: {e}")
        raise HTTPException(status_code=500, detail="統計の取得に失敗しました")

@router.get("/history/{device_id}")
async def get_solo_history(device_id: str, limit: int = 10):
    """ソロプレイ履歴取得（端末別）"""
    try:
        from services.database_service import get_database_service
        db_service = await get_database_service()
        
        history = await db_service.get_recent_solo_sessions(device_id, limit)
        logger.info(f"📜 履歴取得完了: {device_id} ({len(history)}件)")
        
        return {
            "status": "success",
            "device_id": device_id,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"❌ 履歴取得エラー: {e}")
        raise HTTPException(status_code=500, detail="履歴の取得に失敗しました")