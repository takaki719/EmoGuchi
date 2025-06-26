from enum import Enum
from typing import List, Dict
from pydantic import BaseModel

class IntensityLevel(str, Enum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"

class EmotionAxis(str, Enum):
    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"

class Emotion3Layer(BaseModel):
    id: str
    axis: EmotionAxis
    intensity: IntensityLevel
    name_ja: str
    name_en: str
    color: str
    angle: float
    emoji: str

# 24 emotions with 3 intensity levels for each of the 8 basic axes
EMOTIONS_3_LAYER: Dict[str, Emotion3Layer] = {
    # Joy axis (0°)
    "joy_strong": Emotion3Layer(
        id="joy_strong", axis=EmotionAxis.JOY, intensity=IntensityLevel.STRONG,
        name_ja="陶酔", name_en="Ecstasy", color="#FFD700", angle=0, emoji="🤩"
    ),
    "joy_medium": Emotion3Layer(
        id="joy_medium", axis=EmotionAxis.JOY, intensity=IntensityLevel.MEDIUM,
        name_ja="喜び", name_en="Joy", color="#FFE55C", angle=0, emoji="😊"
    ),
    "joy_weak": Emotion3Layer(
        id="joy_weak", axis=EmotionAxis.JOY, intensity=IntensityLevel.WEAK,
        name_ja="平穏", name_en="Serenity", color="#FFF2B8", angle=0, emoji="😌"
    ),

    # Trust axis (45°)
    "trust_strong": Emotion3Layer(
        id="trust_strong", axis=EmotionAxis.TRUST, intensity=IntensityLevel.STRONG,
        name_ja="敬愛", name_en="Admiration", color="#32CD32", angle=45, emoji="🤝"
    ),
    "trust_medium": Emotion3Layer(
        id="trust_medium", axis=EmotionAxis.TRUST, intensity=IntensityLevel.MEDIUM,
        name_ja="信頼", name_en="Trust", color="#90EE90", angle=45, emoji="😊"
    ),
    "trust_weak": Emotion3Layer(
        id="trust_weak", axis=EmotionAxis.TRUST, intensity=IntensityLevel.WEAK,
        name_ja="容認", name_en="Acceptance", color="#C8F7C5", angle=45, emoji="🙂"
    ),

    # Fear axis (90°)
    "fear_strong": Emotion3Layer(
        id="fear_strong", axis=EmotionAxis.FEAR, intensity=IntensityLevel.STRONG,
        name_ja="恐怖", name_en="Terror", color="#800080", angle=90, emoji="😱"
    ),
    "fear_medium": Emotion3Layer(
        id="fear_medium", axis=EmotionAxis.FEAR, intensity=IntensityLevel.MEDIUM,
        name_ja="恐れ", name_en="Fear", color="#9370DB", angle=90, emoji="😰"
    ),
    "fear_weak": Emotion3Layer(
        id="fear_weak", axis=EmotionAxis.FEAR, intensity=IntensityLevel.WEAK,
        name_ja="不安", name_en="Apprehension", color="#C8A2C8", angle=90, emoji="😟"
    ),

    # Surprise axis (135°)
    "surprise_strong": Emotion3Layer(
        id="surprise_strong", axis=EmotionAxis.SURPRISE, intensity=IntensityLevel.STRONG,
        name_ja="驚嘆", name_en="Amazement", color="#1E90FF", angle=135, emoji="😱"
    ),
    "surprise_medium": Emotion3Layer(
        id="surprise_medium", axis=EmotionAxis.SURPRISE, intensity=IntensityLevel.MEDIUM,
        name_ja="驚き", name_en="Surprise", color="#87CEEB", angle=135, emoji="😲"
    ),
    "surprise_weak": Emotion3Layer(
        id="surprise_weak", axis=EmotionAxis.SURPRISE, intensity=IntensityLevel.WEAK,
        name_ja="放心", name_en="Distraction", color="#B6E2FF", angle=135, emoji="😐"
    ),

    # Sadness axis (180°)
    "sadness_strong": Emotion3Layer(
        id="sadness_strong", axis=EmotionAxis.SADNESS, intensity=IntensityLevel.STRONG,
        name_ja="悲嘆", name_en="Grief", color="#000080", angle=180, emoji="😭"
    ),
    "sadness_medium": Emotion3Layer(
        id="sadness_medium", axis=EmotionAxis.SADNESS, intensity=IntensityLevel.MEDIUM,
        name_ja="悲しみ", name_en="Sadness", color="#4169E1", angle=180, emoji="😢"
    ),
    "sadness_weak": Emotion3Layer(
        id="sadness_weak", axis=EmotionAxis.SADNESS, intensity=IntensityLevel.WEAK,
        name_ja="哀愁", name_en="Pensiveness", color="#87CEEB", angle=180, emoji="😔"
    ),

    # Disgust axis (225°)
    "disgust_strong": Emotion3Layer(
        id="disgust_strong", axis=EmotionAxis.DISGUST, intensity=IntensityLevel.STRONG,
        name_ja="強い嫌悪", name_en="Loathing", color="#654321", angle=225, emoji="🤮"
    ),
    "disgust_medium": Emotion3Layer(
        id="disgust_medium", axis=EmotionAxis.DISGUST, intensity=IntensityLevel.MEDIUM,
        name_ja="嫌悪", name_en="Disgust", color="#8B4513", angle=225, emoji="🤢"
    ),
    "disgust_weak": Emotion3Layer(
        id="disgust_weak", axis=EmotionAxis.DISGUST, intensity=IntensityLevel.WEAK,
        name_ja="うんざり", name_en="Boredom", color="#D2B48C", angle=225, emoji="😒"
    ),

    # Anger axis (270°)
    "anger_strong": Emotion3Layer(
        id="anger_strong", axis=EmotionAxis.ANGER, intensity=IntensityLevel.STRONG,
        name_ja="激怒", name_en="Rage", color="#DC143C", angle=270, emoji="😡"
    ),
    "anger_medium": Emotion3Layer(
        id="anger_medium", axis=EmotionAxis.ANGER, intensity=IntensityLevel.MEDIUM,
        name_ja="怒り", name_en="Anger", color="#FF4500", angle=270, emoji="😠"
    ),
    "anger_weak": Emotion3Layer(
        id="anger_weak", axis=EmotionAxis.ANGER, intensity=IntensityLevel.WEAK,
        name_ja="苛立ち", name_en="Annoyance", color="#FF8C69", angle=270, emoji="😤"
    ),

    # Anticipation axis (315°)
    "anticipation_strong": Emotion3Layer(
        id="anticipation_strong", axis=EmotionAxis.ANTICIPATION, intensity=IntensityLevel.STRONG,
        name_ja="攻撃", name_en="Vigilance", color="#FF8C00", angle=315, emoji="👁️"
    ),
    "anticipation_medium": Emotion3Layer(
        id="anticipation_medium", axis=EmotionAxis.ANTICIPATION, intensity=IntensityLevel.MEDIUM,
        name_ja="期待", name_en="Anticipation", color="#FFA500", angle=315, emoji="🤔"
    ),
    "anticipation_weak": Emotion3Layer(
        id="anticipation_weak", axis=EmotionAxis.ANTICIPATION, intensity=IntensityLevel.WEAK,
        name_ja="関心", name_en="Interest", color="#FFCC99", angle=315, emoji="🧐"
    ),
}

# Helper functions
def get_emotions_by_axis(axis: EmotionAxis) -> List[Emotion3Layer]:
    """Get all emotions for a specific axis"""
    return [emotion for emotion in EMOTIONS_3_LAYER.values() if emotion.axis == axis]

def get_emotions_by_intensity(intensity: IntensityLevel) -> List[Emotion3Layer]:
    """Get all emotions for a specific intensity level"""
    return [emotion for emotion in EMOTIONS_3_LAYER.values() if emotion.intensity == intensity]

def get_emotion_by_id(emotion_id: str) -> Emotion3Layer:
    """Get emotion by ID"""
    emotion = EMOTIONS_3_LAYER.get(emotion_id)
    if not emotion:
        raise ValueError(f"Emotion with ID {emotion_id} not found")
    return emotion

def get_all_axes() -> List[EmotionAxis]:
    """Get all emotion axes"""
    return list(EmotionAxis)

def get_all_intensity_levels() -> List[IntensityLevel]:
    """Get all intensity levels"""
    return list(IntensityLevel)

def get_emotions_for_3_layer_mode() -> Dict[str, Emotion3Layer]:
    """Get all emotions for 3-layer wheel mode"""
    return EMOTIONS_3_LAYER

# Mapping for compatibility with existing emotion system
def get_base_emotion_from_3_layer(emotion_id: str) -> str:
    """Convert 3-layer emotion ID to base emotion axis for compatibility"""
    try:
        emotion = get_emotion_by_id(emotion_id)
        return emotion.axis.value
    except ValueError:
        return emotion_id  # Return as-is if not found