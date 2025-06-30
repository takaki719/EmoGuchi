"""
完全にtorchに依存しないシンプルなダミー感情分類器
開発・テスト用（torch無しでも動作）
"""

import logging
import random
import math
import json
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class SimpleDummyClassifier:
    """torch無しのシンプルなダミー感情分類器"""
    
    def __init__(self):
        self.label_map = {
            0: "中立（neutral）",
            1: "喜び（happy）", 
            2: "怒り（angry）",
            3: "悲しみ（sad）"
        }
        self._is_initialized = False
        
    def _initialize_models(self):
        """ダミー初期化"""
        if self._is_initialized:
            return
        logger.info("🎭 シンプルダミー感情分類器を初期化中...")
        self._is_initialized = True
        logger.info("✅ シンプルダミー感情分類器の初期化完了")
    
    def _analyze_audio_file(self, wav_path: str) -> Dict[str, float]:
        """音声ファイルの簡単な分析（ダミー）"""
        try:
            import os
            file_size = os.path.getsize(wav_path)
            
            # ファイルサイズから特徴を推定
            duration_estimate = file_size / 32000  # 大雑把な時間推定
            
            return {
                "duration": duration_estimate,
                "file_size": file_size,
                "amplitude_estimate": random.uniform(0.1, 0.9)
            }
        except:
            return {
                "duration": 2.0,
                "file_size": 50000,
                "amplitude_estimate": 0.5
            }
    
    def classify_emotion(self, wav_path: str) -> Tuple[str, int, list]:
        """
        シンプルダミー感情分類
        
        Returns:
            Tuple[感情ラベル, 予測クラスID, ロジット（リスト形式）]
        """
        self._initialize_models()
        
        try:
            logger.info(f"🎵 シンプルダミー音声処理中: {wav_path}")
            
            # 音声ファイルの簡単な分析
            audio_features = self._analyze_audio_file(wav_path)
            duration = audio_features["duration"]
            amplitude = audio_features["amplitude_estimate"]
            
            logger.info(f"📊 推定音声情報 - 長さ: {duration:.2f}秒, 振幅: {amplitude:.2f}")
            
            # 音声特徴に基づく簡単なルール
            base_logits = [0.0, 0.0, 0.0, 0.0]  # [中立, 喜び, 怒り, 悲しみ]
            
            # 時間ベースの調整
            if duration > 3.0:
                base_logits[0] += 0.5  # 長い音声は中立傾向
            elif duration < 1.0:
                base_logits[3] += 0.3  # 短い音声は悲しみ傾向
            
            # 振幅ベースの調整
            if amplitude > 0.7:
                base_logits[2] += 0.6  # 大きな音声は怒り傾向
                base_logits[1] += 0.4  # または喜び傾向
            elif amplitude < 0.3:
                base_logits[0] += 0.3  # 小さな音声は中立傾向
                base_logits[3] += 0.4  # または悲しみ傾向
            else:
                base_logits[1] += 0.3  # 中程度は喜び傾向
            
            # ランダム要素を追加してリアルさを演出
            for i in range(4):
                base_logits[i] += random.uniform(-0.3, 0.3)
            
            # 予測クラス（最大値のインデックス）
            pred_class = base_logits.index(max(base_logits))
            emotion_label = self.label_map.get(pred_class, "不明")
            
            logger.info(f"🎭 シンプルダミー推論結果: {emotion_label} (クラス{pred_class})")
            logger.info(f"📊 ロジット: {base_logits}")
            
            return emotion_label, pred_class, base_logits
            
        except Exception as e:
            logger.error(f"❌ シンプルダミー分類エラー: {e}")
            # エラー時はランダム結果
            random_class = random.randint(0, 3)
            random_logits = [random.uniform(-1, 1) for _ in range(4)]
            random_logits[random_class] += 1.0
            return self.label_map[random_class], random_class, random_logits

def calc_score_softmax_based(logits: list, target_label: int) -> int:
    """
    リストのロジットからソフトマックス確率を計算し、100点満点でスコア化
    """
    try:
        # ソフトマックス計算（torch無し）
        max_logit = max(logits)
        exp_logits = [math.exp(x - max_logit) for x in logits]  # 数値安定性のため
        sum_exp = sum(exp_logits)
        probs = [x / sum_exp for x in exp_logits]
        
        # 目標ラベルの確率を取得
        target_prob = probs[target_label]
        score = round(target_prob * 100)
        
        logger.info(f"📊 スコア計算: 目標クラス{target_label}の確率={target_prob:.4f} → {score}点")
        return score
        
    except Exception as e:
        logger.error(f"❌ スコア計算エラー: {e}")
        return random.randint(20, 95)

# グローバルインスタンス
_simple_classifier = None

def get_emotion_classifier():
    """シンプルダミー感情分類器のシングルトンインスタンス"""
    global _simple_classifier
    if _simple_classifier is None:
        _simple_classifier = SimpleDummyClassifier()
    return _simple_classifier

def classify_emotion_with_score(wav_path: str, target_emotion: int) -> dict:
    """
    シンプルダミー感情分類とスコア計算
    """
    try:
        classifier = get_emotion_classifier()
        
        # 感情分類実行
        emotion_label, pred_class, logits = classifier.classify_emotion(wav_path)
        
        # スコア計算
        score = calc_score_softmax_based(logits, target_emotion)
        
        # 予測クラスの確信度
        max_logit = max(logits)
        exp_logits = [math.exp(x - max_logit) for x in logits]
        sum_exp = sum(exp_logits)
        probs = [x / sum_exp for x in exp_logits]
        confidence = probs[pred_class]
        
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
        
        logger.info(f"🎯 シンプルダミー最終結果: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ シンプルダミー分類処理エラー: {e}")
        # 完全なフォールバック
        return {
            "emotion": "中立（neutral）",
            "predicted_class": 0,
            "target_class": target_emotion,
            "score": random.randint(30, 90),
            "confidence": random.randint(60, 95),
            "is_correct": False
        }