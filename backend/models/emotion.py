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
    AdvancedEmotion.PRIDE: EmotionInfo(
        id="pride", name_ja="プライド", name_en="Pride",
        components=[BasicEmotion.ANGER, BasicEmotion.JOY]
    ),
    AdvancedEmotion.AGGRESSIVENESS: EmotionInfo(
        id="aggressiveness", name_ja="攻撃性", name_en="Aggressiveness",
        components=[BasicEmotion.ANGER, BasicEmotion.ANTICIPATION]
    ),
    AdvancedEmotion.CONTEMPT: EmotionInfo(
        id="contempt", name_ja="軽蔑", name_en="Contempt",
        components=[BasicEmotion.DISGUST, BasicEmotion.ANGER]
    ),
    AdvancedEmotion.REMORSE: EmotionInfo(
        id="remorse", name_ja="後悔", name_en="Remorse",
        components=[BasicEmotion.SADNESS, BasicEmotion.DISGUST]
    ),
    AdvancedEmotion.DISAPPOINTMENT: EmotionInfo(
        id="disappointment", name_ja="失望", name_en="Disappointment",
        components=[BasicEmotion.SURPRISE, BasicEmotion.SADNESS]
    ),
    AdvancedEmotion.AWE: EmotionInfo(
        id="awe", name_ja="畏敬", name_en="Awe",
        components=[BasicEmotion.FEAR, BasicEmotion.SURPRISE]
    ),
    AdvancedEmotion.DELIGHT: EmotionInfo(
        id="delight", name_ja="喜悦", name_en="Delight",
        components=[BasicEmotion.JOY, BasicEmotion.SURPRISE]
    ),
    AdvancedEmotion.SUBMISSION: EmotionInfo(
        id="submission", name_ja="服従", name_en="Submission",
        components=[BasicEmotion.TRUST, BasicEmotion.FEAR]
    ),
    AdvancedEmotion.GUILT: EmotionInfo(
        id="guilt", name_ja="罪悪感", name_en="Guilt",
        components=[BasicEmotion.JOY, BasicEmotion.FEAR]
    ),
    AdvancedEmotion.HOPE: EmotionInfo(
        id="hope", name_ja="希望", name_en="Hope",
        components=[BasicEmotion.ANTICIPATION, BasicEmotion.TRUST]
    ),
    AdvancedEmotion.ANXIETY: EmotionInfo(
        id="anxiety", name_ja="不安", name_en="Anxiety",
        components=[BasicEmotion.ANTICIPATION, BasicEmotion.FEAR]
    ),
    AdvancedEmotion.CYNICISM: EmotionInfo(
        id="cynicism", name_ja="皮肉", name_en="Cynicism",
        components=[BasicEmotion.DISGUST, BasicEmotion.ANTICIPATION]
    ),
    AdvancedEmotion.PESSIMISM: EmotionInfo(
        id="pessimism", name_ja="悲観", name_en="Pessimism",
        components=[BasicEmotion.SADNESS, BasicEmotion.ANTICIPATION]
    ),
    AdvancedEmotion.ENVY: EmotionInfo(
        id="envy", name_ja="嫉妬", name_en="Envy",
        components=[BasicEmotion.SADNESS, BasicEmotion.ANGER]
    ),
    AdvancedEmotion.OUTRAGE: EmotionInfo(
        id="outrage", name_ja="憤慨", name_en="Outrage",
        components=[BasicEmotion.SURPRISE, BasicEmotion.ANGER]
    ),
    AdvancedEmotion.UNBELIEF: EmotionInfo(
        id="unbelief", name_ja="不信", name_en="Unbelief",
        components=[BasicEmotion.SURPRISE, BasicEmotion.DISGUST]
    ),
    AdvancedEmotion.SHAME: EmotionInfo(
        id="shame", name_ja="恥", name_en="Shame",
        components=[BasicEmotion.FEAR, BasicEmotion.DISGUST]
    ),
    AdvancedEmotion.DESPAIR: EmotionInfo(
        id="despair", name_ja="絶望", name_en="Despair",
        components=[BasicEmotion.FEAR, BasicEmotion.SADNESS]
    ),
    AdvancedEmotion.SENTIMENTALITY: EmotionInfo(
        id="sentimentality", name_ja="感傷", name_en="Sentimentality",
        components=[BasicEmotion.TRUST, BasicEmotion.SADNESS]
    ),
    AdvancedEmotion.CURIOSITY: EmotionInfo(
        id="curiosity", name_ja="好奇心", name_en="Curiosity",
        components=[BasicEmotion.TRUST, BasicEmotion.SURPRISE]
    ),
    AdvancedEmotion.DOMINANCE: EmotionInfo(
        id="dominance", name_ja="支配", name_en="Dominance",
        components=[BasicEmotion.ANGER, BasicEmotion.TRUST]
    ),
    AdvancedEmotion.MORBIDNESS: EmotionInfo(
        id="morbidness", name_ja="病的", name_en="Morbidness",
        components=[BasicEmotion.DISGUST, BasicEmotion.JOY]
    ),
}

def get_emotions_for_mode(mode: str, vote_type: str = None) -> dict:
    """Get emotions dictionary based on game mode and vote type"""
    # Handle wheel mode
    if mode == "wheel" or vote_type == "wheel":
        # Wheel mode uses 24 emotions from emotion_3_layer (3-layer wheel)
        from models.emotion_3_layer import get_emotions_for_3_layer_mode
        return get_emotions_for_3_layer_mode()
    
    # Handle choice-based modes
    if vote_type == "4choice":
        # 4-choice mode: only use 4 core emotions
        four_choice_emotions = {
            BasicEmotion.JOY: BASIC_EMOTIONS[BasicEmotion.JOY],
            BasicEmotion.ANGER: BASIC_EMOTIONS[BasicEmotion.ANGER], 
            BasicEmotion.SADNESS: BASIC_EMOTIONS[BasicEmotion.SADNESS],
            BasicEmotion.SURPRISE: BASIC_EMOTIONS[BasicEmotion.SURPRISE],
        }
        return four_choice_emotions
    elif vote_type == "8choice":
        # 8-choice mode: use all 8 basic emotions
        return BASIC_EMOTIONS
    
    # Fallback based on mode for backward compatibility
    if mode == "advanced":
        return BASIC_EMOTIONS  # Changed from ADVANCED_EMOTIONS to BASIC_EMOTIONS for 8-choice
    elif mode == "wheel":
        from models.emotion_3_layer import get_emotions_for_3_layer_mode
        return get_emotions_for_3_layer_mode()
    
    # Default to 4-choice emotions for basic mode
    four_choice_emotions = {
        BasicEmotion.JOY: BASIC_EMOTIONS[BasicEmotion.JOY],
        BasicEmotion.ANGER: BASIC_EMOTIONS[BasicEmotion.ANGER], 
        BasicEmotion.SADNESS: BASIC_EMOTIONS[BasicEmotion.SADNESS],
        BasicEmotion.SURPRISE: BASIC_EMOTIONS[BasicEmotion.SURPRISE],
    }
    return four_choice_emotions

def get_emotion_choices_for_voting(mode: str, correct_emotion_id: str, choice_count: int = None, vote_type: str = None) -> List[EmotionInfo]:
    """Get emotion choices for voting, including the correct one and random others"""
    import random
    
    # For wheel mode, we don't need voting choices since users select from the wheel
    if mode == "wheel" or vote_type == "wheel":
        return []
    
    emotions_dict = get_emotions_for_mode(mode, vote_type)
    all_emotions = list(emotions_dict.values())
    
    # Set default choice count based on vote_type or mode if not specified
    if choice_count is None:
        if vote_type == "8choice":
            choice_count = 8
        elif vote_type == "4choice":
            choice_count = 4
        else:
            # Fallback based on mode
            choice_count = 8 if mode == "advanced" else 4
    
    # Find the correct emotion
    correct_emotion = next((e for e in all_emotions if e.id == correct_emotion_id), None)
    if not correct_emotion:
        raise ValueError(f"Emotion {correct_emotion_id} not found in {mode} mode with vote_type {vote_type}")
    
    # Get other emotions (excluding the correct one)
    other_emotions = [e for e in all_emotions if e.id != correct_emotion_id]
    
    # Randomly select other emotions to fill up to choice_count
    selected_others = random.sample(other_emotions, min(choice_count - 1, len(other_emotions)))
    
    # Combine and shuffle
    choices = [correct_emotion] + selected_others
    random.shuffle(choices)
    
    return choices