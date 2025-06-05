from enum import Enum
from typing import List
from pydantic import BaseModel

class BasicEmotion(str, Enum):
    JOY = "joy"
    ANTICIPATION = "anticipation" 
    ANGER = "anger"
    DISGUST = "disgust"
    SADNESS = "sadness"
    SURPRISE = "surprise"
    FEAR = "fear"
    TRUST = "trust"

class AdvancedEmotion(str, Enum):
    OPTIMISM = "optimism"          # 期待 + 喜び
    PRIDE = "pride"                # 怒り + 喜び
    MORBIDNESS = "morbidness"      # 嫌悪 + 喜び
    AGGRESSIVENESS = "aggressiveness"  # 怒り + 期待
    CYNICISM = "cynicism"          # 嫌悪 + 期待
    PESSIMISM = "pessimism"        # 悲しみ + 期待
    CONTEMPT = "contempt"          # 嫌悪 + 怒り
    ENVY = "envy"                  # 悲しみ + 怒り
    OUTRAGE = "outrage"            # 驚き + 怒り
    REMORSE = "remorse"            # 悲しみ + 嫌悪
    UNBELIEF = "unbelief"          # 驚き + 嫌悪
    SHAME = "shame"                # 恐れ + 嫌悪
    DISAPPOINTMENT = "disappointment"  # 驚き + 悲しみ
    DESPAIR = "despair"            # 恐れ + 悲しみ
    SENTIMENTALITY = "sentimentality"  # 信頼 + 悲しみ
    AWE = "awe"                    # 恐れ + 驚き
    CURIOSITY = "curiosity"        # 信頼 + 驚き
    DELIGHT = "delight"            # 喜び + 驚き
    SUBMISSION = "submission"      # 信頼 + 恐れ
    GUILT = "guilt"                # 喜び + 恐れ
    ANXIETY = "anxiety"            # 期待 + 恐れ
    LOVE = "love"                  # 喜び + 信頼
    HOPE = "hope"                  # 期待 + 信頼
    DOMINANCE = "dominance"        # 怒り + 信頼

class EmotionInfo(BaseModel):
    id: str
    name_ja: str
    name_en: str
    components: List[BasicEmotion] = []

# 感情マッピング
BASIC_EMOTIONS = {
    BasicEmotion.JOY: EmotionInfo(id="joy", name_ja="喜び", name_en="Joy"),
    BasicEmotion.ANTICIPATION: EmotionInfo(id="anticipation", name_ja="期待", name_en="Anticipation"),
    BasicEmotion.ANGER: EmotionInfo(id="anger", name_ja="怒り", name_en="Anger"),
    BasicEmotion.DISGUST: EmotionInfo(id="disgust", name_ja="嫌悪", name_en="Disgust"),
    BasicEmotion.SADNESS: EmotionInfo(id="sadness", name_ja="悲しみ", name_en="Sadness"),
    BasicEmotion.SURPRISE: EmotionInfo(id="surprise", name_ja="驚き", name_en="Surprise"),
    BasicEmotion.FEAR: EmotionInfo(id="fear", name_ja="恐れ", name_en="Fear"),
    BasicEmotion.TRUST: EmotionInfo(id="trust", name_ja="信頼", name_en="Trust"),
}

ADVANCED_EMOTIONS = {
    AdvancedEmotion.OPTIMISM: EmotionInfo(
        id="optimism", name_ja="楽観", name_en="Optimism", 
        components=[BasicEmotion.ANTICIPATION, BasicEmotion.JOY]
    ),
    AdvancedEmotion.LOVE: EmotionInfo(
        id="love", name_ja="愛", name_en="Love",
        components=[BasicEmotion.JOY, BasicEmotion.TRUST]
    ),
    # ... 他の応用感情も同様に定義
}