"""
開発用ダミー感情分類器
実際のkushinada-hubert-largeモデルがない場合のテスト用実装
"""

import torch
import torchaudio
import os
import logging
import random
from typing import Tuple

logger = logging.getLogger(__name__)

class DummyEmotionClassifier:
    """ダミー感情分類器（開発・テスト用）"""
    
    def __init__(self, ckpt_path: str = "./ckpt/dev-best.ckpt"):
        self.ckpt_path = ckpt_path
        self.label_map = {
            0: "中立（neutral）",
            1: "喜び（happy）", 
            2: "怒り（angry）",
            3: "悲しみ（sad）"
        }
        self._is_initialized = False
        
    def _initialize_models(self):
        """ダミーモデルの初期化"""
        if self._is_initialized:
            return
            
        logger.info("🤖 ダミー感情分類器を初期化中...")
        
        # チェックポイントファイルが存在しない場合は作成
        if not os.path.exists(self.ckpt_path):
            logger.warning(f"⚠️ チェックポイントファイルが見つかりません: {self.ckpt_path}")
            logger.info("🔧 ダミーチェックポイントを作成します...")
            self._create_dummy_checkpoint()
        
        self._is_initialized = True
        logger.info("✅ ダミー感情分類器の初期化完了")
    
    def _create_dummy_checkpoint(self):
        """ダミーチェックポイントを作成"""
        dummy_weights = {
            "Downstream": {
                "projector.weight": torch.randn(256, 1024),
                "projector.bias": torch.randn(256),
                "model.post_net.linear.weight": torch.randn(4, 256),
                "model.post_net.linear.bias": torch.randn(4),
            }
        }
        
        os.makedirs(os.path.dirname(self.ckpt_path), exist_ok=True)
        torch.save(dummy_weights, self.ckpt_path)
        logger.info(f"✅ ダミーチェックポイント作成完了: {self.ckpt_path}")
    
    def classify_emotion(self, wav_path: str) -> Tuple[str, int, torch.Tensor]:
        """
        ダミー感情分類（ランダム + 音声長さベース）
        """
        self._initialize_models()
        
        try:
            logger.info(f"🎵 ダミー音声処理中: {wav_path}")
            
            # 音声ファイルの基本情報を取得
            waveform, sr = torchaudio.load(wav_path)
            duration = waveform.shape[-1] / sr
            
            logger.info(f"📊 音声情報 - 長さ: {duration:.2f}秒, サンプルレート: {sr}Hz")
            
            # ダミーロジット生成（音声の長さや特徴に基づく簡単な規則）
            # 実際のモデルに近い分布を模擬
            base_logits = torch.randn(1, 4) * 0.5
            
            # 音声の長さに基づく簡単な特徴
            if duration > 3.0:
                base_logits[0][0] += 0.3  # 長い音声は中立傾向
            elif duration < 1.0:
                base_logits[0][3] += 0.2  # 短い音声は悲しみ傾向
            
            # 音声の振幅に基づく調整
            amplitude = torch.abs(waveform).mean()
            if amplitude > 0.1:
                base_logits[0][2] += 0.4  # 大きな音声は怒り傾向
                base_logits[0][1] += 0.3  # または喜び傾向
            else:
                base_logits[0][0] += 0.2  # 小さな音声は中立傾向
                base_logits[0][3] += 0.2  # または悲しみ傾向
            
            # 予測クラス
            pred_class = torch.argmax(base_logits, dim=-1).item()
            emotion_label = self.label_map.get(pred_class, "不明")
            
            logger.info(f"🎭 ダミー推論結果: {emotion_label} (クラス{pred_class})")
            logger.info(f"📊 ロジット: {base_logits[0].tolist()}")
            
            return emotion_label, pred_class, base_logits
            
        except Exception as e:
            logger.error(f"❌ ダミー分類エラー: {e}")
            # エラー時はランダム結果を返す
            random_class = random.randint(0, 3)
            random_logits = torch.randn(1, 4)
            random_logits[0][random_class] += 1.0  # 選択されたクラスを強調
            return self.label_map[random_class], random_class, random_logits

def calc_score_softmax_based(logits: torch.Tensor, target_label: int) -> int:
    """
    ロジット x から softmax を計算し、target_label に対応する確率を 100点満点で返す
    """
    try:
        probs = torch.softmax(logits, dim=-1)
        target_prob = probs[0][target_label].item()
        score = round(target_prob * 100)
        
        logger.info(f"📊 スコア計算: 目標クラス{target_label}の確率={target_prob:.4f} → {score}点")
        return score
        
    except Exception as e:
        logger.error(f"❌ スコア計算エラー: {e}")
        return random.randint(20, 95)  # ダミースコア

# グローバルインスタンス
_dummy_classifier = None

def get_emotion_classifier():
    """ダミー感情分類器のシングルトンインスタンスを取得"""
    global _dummy_classifier
    if _dummy_classifier is None:
        _dummy_classifier = DummyEmotionClassifier()
    return _dummy_classifier

def classify_emotion_with_score(wav_path: str, target_emotion: int) -> dict:
    """
    ダミー感情分類とスコア計算
    """
    try:
        classifier = get_emotion_classifier()
        
        # ダミー感情分類実行
        emotion_label, pred_class, logits = classifier.classify_emotion(wav_path)
        
        # スコア計算
        score = calc_score_softmax_based(logits, target_emotion)
        
        # 予測クラスの確信度
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
        
        logger.info(f"🎯 ダミー最終結果: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ ダミー分類処理エラー: {e}")
        # 完全なフォールバック
        return {
            "emotion": "中立（neutral）",
            "predicted_class": 0,
            "target_class": target_emotion,
            "score": random.randint(30, 90),
            "confidence": random.randint(60, 95),
            "is_correct": False
        }