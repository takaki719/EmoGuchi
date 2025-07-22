"""
Kushinada Hubert Large を使用した感情分類推論モジュール
4感情（中立・喜び・怒り・悲しみ）の分類を行う
"""

import torch
import os
import logging
import soundfile as sf
from typing import Tuple
from transformers import HubertModel, AutoFeatureExtractor

logger = logging.getLogger(__name__)

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
        self.model = "imprt/kushinada-hubert-large"
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
                
                # Hugging Face認証トークンの設定
                token_kwargs = {}
                if settings.HUGGINGFACE_TOKEN:
                    token_kwargs['token'] = settings.HUGGINGFACE_TOKEN
                    logger.info("🔐 Hugging Face認証トークンを使用")
                
                # AutoFeatureExtractor を使用
                self.feature_extractor = AutoFeatureExtractor.from_pretrained(
                    self.model, **token_kwargs
                )
                logger.info("✅ AutoFeatureExtractor 読み込み完了")
                
                # HubertModel の読み込み
                self.upstream = HubertModel.from_pretrained(
                    self.model, **token_kwargs
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
    """感情分類器のシングルトンインスタンスを取得"""
    global _classifier
    if _classifier is None:
        _classifier = EmotionClassifier()
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