"""
Kushinada Hubert Large を使用した感情分類推論モジュール
4感情（中立・喜び・怒り・悲しみ）の分類を行う
"""

import torch
import os
import logging
import soundfile as sf
import tarfile
import tempfile
import shutil
from typing import Tuple
from transformers import HubertModel, AutoFeatureExtractor

logger = logging.getLogger(__name__)

def download_model_from_r2():
    """R2からKushinadaモデルをダウンロードして解凍"""
    from config import settings
    from services.storage_service import StorageService
    
    try:
        logger.info("📥 R2からKushinadaモデルをダウンロード中...")
        
        # ローカルパスの確認（Fly.io Volumesでの永続化対応）
        local_model_path = settings.KUSHINADA_LOCAL_PATH
        if os.path.exists(local_model_path) and os.path.exists(os.path.join(local_model_path, "config.json")):
            logger.info(f"✅ モデルは既にローカルに存在: {local_model_path}")
            return local_model_path
        
        logger.info(f"⚠️ モデルがローカルに見つからない、R2からダウンロード必要: {local_model_path}")
        
        # ストレージサービス初期化
        storage = StorageService()
        
        # 一時ファイルにダウンロード
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            
        logger.info(f"📦 ダウンロード中: {settings.KUSHINADA_MODEL_R2_KEY}")
        
        # デバッグ: R2バケットの内容を一覧表示
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.R2_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            
            logger.info("🔍 R2バケットの内容を確認中...")
            response = s3_client.list_objects_v2(Bucket=settings.S3_BUCKET, Prefix='models/')
            
            if 'Contents' in response:
                logger.info(f"📁 models/フォルダ内のファイル:")
                for obj in response['Contents']:
                    logger.info(f"  - {obj['Key']} (サイズ: {obj['Size']} bytes)")
            else:
                logger.warning("⚠️ models/フォルダにファイルが見つかりません")
                
            # すべてのファイルも確認
            response_all = s3_client.list_objects_v2(Bucket=settings.S3_BUCKET, MaxKeys=10)
            if 'Contents' in response_all:
                logger.info(f"📁 バケット内のファイル例 (最初の10件):")
                for obj in response_all['Contents']:
                    logger.info(f"  - {obj['Key']}")
                    
        except Exception as list_error:
            logger.error(f"🔍 バケット内容確認エラー: {list_error}")
        
        # R2からダウンロード
        storage.download_file(settings.KUSHINADA_MODEL_R2_KEY, tmp_path)
        
        logger.info("📂 モデルを解凍中...")
        
        # 親ディレクトリを作成
        os.makedirs(os.path.dirname(local_model_path), exist_ok=True)
        
        # tar.gzを解凍
        with tarfile.open(tmp_path, 'r:gz') as tar:
            tar.extractall(os.path.dirname(local_model_path))
        
        # 一時ファイルを削除
        os.unlink(tmp_path)
        
        logger.info(f"✅ モデル解凍完了: {local_model_path}")
        return local_model_path
        
    except Exception as e:
        logger.error(f"❌ R2からのモデルダウンロード失敗: {e}")
        logger.error(f"📋 詳細: {type(e).__name__}: {str(e)}")
        # R2の設定確認のためのデバッグ情報
        logger.error(f"🔧 設定確認: KUSHINADA_MODEL_SOURCE={settings.KUSHINADA_MODEL_SOURCE}")
        logger.error(f"🔧 設定確認: KUSHINADA_MODEL_R2_KEY={settings.KUSHINADA_MODEL_R2_KEY}")
        logger.error(f"🔧 設定確認: R2_ENDPOINT_URL={getattr(settings, 'R2_ENDPOINT_URL', 'NOT_SET')}")
        raise

class EmotionClassifier:
    """感情分類器クラス"""
    
    def __init__(self, ckpt_path: str = "./ckpt/dev-best.ckpt"):
        self.ckpt_path = ckpt_path
        self.label_map = {
            0: "中立（neutral）",
            1: "喜び（happy）", 
            2: "怒り（angry）",
            3: "悲しみ（sad）"
        }
        # モデルパスを設定から取得
        from config import settings
        self.model_source = settings.KUSHINADA_MODEL_SOURCE
        self.model_path = settings.KUSHINADA_LOCAL_PATH if self.model_source == "r2" else "imprt/kushinada-hubert-large"
        self.feature_extractor = None
        self.upstream = None
        self.projector = None
        self.post_net = None
        self._is_initialized = False
        
    def _initialize_models(self):
        """モデルの初期化（遅延読み込み）"""
        if self._is_initialized:
            return
            
        try:
            logger.info("🤖 Kushinada Hubert Large モデルを初期化中...")
            
            # Feature Extractor と Upstream モデルの読み込み
            try:
                from config import settings
                
                # モデルソースに応じてパスを決定（フォールバック付き）
                model_loaded = False
                
                if self.model_source == "r2":
                    try:
                        logger.info("📥 R2からモデルをダウンロード中...")
                        model_path = download_model_from_r2()
                        logger.info(f"✅ R2からのダウンロード完了: {model_path}")
                        
                        # ローカルパスから読み込み
                        self.feature_extractor = AutoFeatureExtractor.from_pretrained(model_path)
                        self.upstream = HubertModel.from_pretrained(model_path).eval()
                        logger.info("✅ R2からのKushinada Hubertモデル読み込み完了")
                        model_loaded = True
                        
                    except Exception as r2_error:
                        logger.warning(f"⚠️ R2からのダウンロード失敗: {r2_error}")
                        logger.info("🔄 Hugging Faceにフォールバック中...")
                
                # R2が失敗した場合、またはデフォルトでHugging Faceを使用
                if not model_loaded:
                    # Hugging Face認証トークンの設定
                    token_kwargs = {}
                    if settings.HUGGINGFACE_TOKEN:
                        token_kwargs['token'] = settings.HUGGINGFACE_TOKEN
                        logger.info("🔐 Hugging Face認証トークンを使用")
                    
                    # AutoFeatureExtractor を使用
                    self.feature_extractor = AutoFeatureExtractor.from_pretrained(
                        "imprt/kushinada-hubert-large", **token_kwargs
                    )
                    logger.info("✅ AutoFeatureExtractor 読み込み完了")
                    
                    # HubertModel の読み込み
                    self.upstream = HubertModel.from_pretrained(
                        "imprt/kushinada-hubert-large", **token_kwargs
                    ).eval()
                    logger.info("✅ Kushinada Hubert モデル読み込み完了")
                
                self.use_kushinada = True
            except Exception as e:
                logger.warning(f"⚠️ Kushinada モデル読み込み失敗: {e}")
                logger.warning("🎭 ダミーモデルにフォールバック中...")
                
                # ダミーモデルにフォールバック
                try:
                    from kushinada_infer_dummy import DummyEmotionClassifier
                    self._dummy_classifier = DummyEmotionClassifier()
                    self._dummy_classifier._initialize_models()
                    self.use_kushinada = False
                    logger.info("✅ ダミーモデル初期化完了（開発・テスト用）")
                except Exception as dummy_error:
                    logger.error(f"❌ ダミーモデルも初期化失敗: {dummy_error}")
                    raise RuntimeError("モデル初期化に完全に失敗しました")
            
            logger.info("✅ Upstream モデル読み込み完了")
            
            # チェックポイントファイルの存在確認
            if not os.path.exists(self.ckpt_path):
                raise FileNotFoundError(f"チェックポイントファイルが見つかりません: {self.ckpt_path}")
            
            # Downstream モデルの読み込み
            logger.info(f"📦 チェックポイントを読み込み中: {self.ckpt_path}")
            ckpt = torch.load(self.ckpt_path, map_location="cpu", weights_only=False)["Downstream"]
            
            # Projector レイヤーの初期化
            projector_weight_shape = ckpt["projector.weight"].shape
            self.projector = torch.nn.Linear(projector_weight_shape[1], projector_weight_shape[0])
            self.projector.load_state_dict({
                "weight": ckpt["projector.weight"],
                "bias": ckpt["projector.bias"]
            })
            self.projector.eval()
            logger.info("✅ Projector レイヤー初期化完了")
            
            # Post-net レイヤーの初期化
            post_net_weight_shape = ckpt["model.post_net.linear.weight"].shape
            self.post_net = torch.nn.Linear(post_net_weight_shape[1], post_net_weight_shape[0])
            self.post_net.load_state_dict({
                "weight": ckpt["model.post_net.linear.weight"],
                "bias": ckpt["model.post_net.linear.bias"]
            })
            self.post_net.eval()
            logger.info("✅ Post-net レイヤー初期化完了")
            
            self._is_initialized = True
            logger.info("🎉 感情分類器の初期化が完了しました")
            
        except Exception as e:
            logger.error(f"❌ モデル初期化エラー: {e}")
            raise
    
    def classify_emotion(self, wav_path: str) -> Tuple[str, int, torch.Tensor]:
        """
        音声ファイルから感情を分類する
        
        Args:
            wav_path: WAVファイルのパス
            
        Returns:
            Tuple[感情ラベル, 予測クラスID, ロジット]
        """
        # 遅延初期化：実際に推論が必要になった時にモデルを初期化
        if not self._is_initialized:
            logger.info("🚀 初回推論実行 - モデルを初期化中...")
            self._initialize_models()
        
        # ダミーモデルを使用する場合
        if hasattr(self, '_dummy_classifier') and not self.use_kushinada:
            logger.info("🎭 ダミーモデルで推論実行")
            return self._dummy_classifier.classify_emotion(wav_path)
        
        try:
            logger.info(f"🎵 音声ファイルを処理中: {wav_path}")
            
            # soundfile を使用して音声ファイルを読み込み
            audio_array, sr = sf.read(wav_path)
            logger.info(f"📊 読み込み完了 - サンプルレート: {sr}Hz, 形状: {audio_array.shape}")
            
            # AutoFeatureExtractor を使用して前処理
            logger.info("🔄 AutoFeatureExtractor による前処理中...")
            inputs = self.feature_extractor(
                audio_array, 
                sampling_rate=sr, 
                return_tensors="pt",
                padding=True
            )
            
            logger.info(f"✅ 前処理完了 - 入力形状: {inputs.input_values.shape}")
            
            # 推論実行
            with torch.no_grad():
                # 特徴抽出（Upstream）
                logger.info("🧠 特徴抽出中...")
                features = self.upstream(inputs.input_values).last_hidden_state.mean(dim=1)
                logger.info(f"📈 特徴抽出完了 - 特徴量形状: {features.shape}")
                
                # Projector通過
                x = self.projector(features)
                logger.info(f"🔄 Projector通過完了 - 形状: {x.shape}")
                
                # Post-net通過（最終ロジット）
                logits = self.post_net(x)
                logger.info(f"🎯 Post-net通過完了 - ロジット形状: {logits.shape}")
                
                # 予測クラス
                pred_class = torch.argmax(logits, dim=-1).item()
                emotion_label = self.label_map.get(pred_class, "不明")
                
                logger.info(f"🎭 推論結果: {emotion_label} (クラス{pred_class})")
                
                return emotion_label, pred_class, logits
                
        except Exception as e:
            logger.error(f"❌ 感情分類エラー: {e}")
            raise

def calc_score_softmax_based(logits: torch.Tensor, target_label: int) -> int:
    """
    ロジット x から softmax を計算し、target_label に対応する確率を 100点満点で返す
    
    Args:
        logits: モデル出力のロジット [batch_size, num_classes]
        target_label: 目標感情のクラスID (0-3)
        
    Returns:
        100点満点のスコア
    """
    try:
        # ソフトマックスで確率に変換
        probs = torch.softmax(logits, dim=-1)
        
        # 目標ラベルの確率を取得
        target_prob = probs[0][target_label].item()
        
        # 100点満点でスコア化
        score = round(target_prob * 100)
        
        logger.info(f"📊 スコア計算: 目標クラス{target_label}の確率={target_prob:.4f} → {score}点")
        
        return score
        
    except Exception as e:
        logger.error(f"❌ スコア計算エラー: {e}")
        return 0

# グローバルインスタンス（シングルトン）
_classifier = None

def get_emotion_classifier() -> EmotionClassifier:
    """感情分類器のシングルトンインスタンスを取得（遅延初期化）"""
    global _classifier
    if _classifier is None:
        _classifier = EmotionClassifier()
        # 初期化は実際に推論が必要になった時まで遅延
    return _classifier

def classify_emotion_with_score(wav_path: str, target_emotion: int) -> dict:
    """
    音声ファイルから感情を分類し、スコアも計算する
    
    Args:
        wav_path: WAVファイルのパス
        target_emotion: 目標感情のクラスID (0-3)
        
    Returns:
        {
            "emotion": "感情ラベル",
            "predicted_class": 予測クラスID,
            "target_class": 目標クラスID,
            "score": スコア(0-100),
            "confidence": 予測クラスの確信度,
            "is_correct": 正解かどうか
        }
    """
    try:
        classifier = get_emotion_classifier()
        
        # 感情分類実行
        emotion_label, pred_class, logits = classifier.classify_emotion(wav_path)
        
        # スコア計算
        score = calc_score_softmax_based(logits, target_emotion)
        
        # 予測クラスの確信度も計算
        probs = torch.softmax(logits, dim=-1)
        confidence = probs[0][pred_class].item()
        
        # 正解判定
        is_correct = (pred_class == target_emotion)
        
        result = {
            "emotion": emotion_label,
            "predicted_class": pred_class,
            "target_class": target_emotion,
            "score": score,
            "confidence": round(confidence * 100, 2),
            "is_correct": is_correct
        }
        
        logger.info(f"🎯 最終結果: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ 分類処理エラー: {e}")
        raise