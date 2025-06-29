from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel

class VoiceProcessingPattern(str, Enum):
    FAST_HIGH = "fast_high"
    SLOW_LOW = "slow_low"
    PITCH_UP = "pitch_up"
    TEMPO_UP = "tempo_up"
    EMOTION_REVERSE = "emotion_reverse"

class VoiceProcessingConfig(BaseModel):
    pattern: VoiceProcessingPattern
    pitch: float  # Semitones (-12 to +12)
    tempo: float  # Multiplier (0.5 to 2.0)
    description: str

# Predefined voice processing patterns based on requirements
VOICE_PROCESSING_PATTERNS: Dict[VoiceProcessingPattern, VoiceProcessingConfig] = {
    VoiceProcessingPattern.FAST_HIGH: VoiceProcessingConfig(
        pattern=VoiceProcessingPattern.FAST_HIGH,
        pitch=6.0,  # Much more noticeable for testing
        tempo=2.0,  # Much faster for testing
        description="高速・高ピッチ（興奮・喜びの印象）"
    ),
    VoiceProcessingPattern.SLOW_LOW: VoiceProcessingConfig(
        pattern=VoiceProcessingPattern.SLOW_LOW,
        pitch=-3.0,
        tempo=0.8,
        description="低速・低ピッチ（落ち着いた・暗い印象）"
    ),
    VoiceProcessingPattern.PITCH_UP: VoiceProcessingConfig(
        pattern=VoiceProcessingPattern.PITCH_UP,
        pitch=3.0,
        tempo=1.0,
        description="ピッチ上昇（可愛さ・軽快さ）"
    ),
    VoiceProcessingPattern.TEMPO_UP: VoiceProcessingConfig(
        pattern=VoiceProcessingPattern.TEMPO_UP,
        pitch=0.0,
        tempo=1.5,
        description="テンポ上昇（緊張・焦り・興奮感）"
    )
}

# Plutchik emotion reversal mapping
EMOTION_REVERSAL_MAP: Dict[str, Dict[str, float]] = {
    # Joy → Sadness
    'joy': {'pitch': -3.0, 'tempo': 0.8},
    'joy_strong': {'pitch': -3.0, 'tempo': 0.8},
    'joy_medium': {'pitch': -3.0, 'tempo': 0.8},
    'joy_weak': {'pitch': -3.0, 'tempo': 0.8},
    
    # Anger → Fear
    'anger': {'pitch': -2.0, 'tempo': 0.85},
    'anger_strong': {'pitch': -2.0, 'tempo': 0.85},
    'anger_medium': {'pitch': -2.0, 'tempo': 0.85},
    'anger_weak': {'pitch': -2.0, 'tempo': 0.85},
    
    # Trust → Disgust
    'trust': {'pitch': -1.5, 'tempo': 0.9},
    'trust_strong': {'pitch': -1.5, 'tempo': 0.9},
    'trust_medium': {'pitch': -1.5, 'tempo': 0.9},
    'trust_weak': {'pitch': -1.5, 'tempo': 0.9},
    
    # Anticipation → Surprise
    'anticipation': {'pitch': 2.0, 'tempo': 1.4},
    'anticipation_strong': {'pitch': 2.0, 'tempo': 1.4},
    'anticipation_medium': {'pitch': 2.0, 'tempo': 1.4},
    'anticipation_weak': {'pitch': 2.0, 'tempo': 1.4},
    
    # Fear → Anger
    'fear': {'pitch': 2.0, 'tempo': 1.6},
    'fear_strong': {'pitch': 2.0, 'tempo': 1.6},
    'fear_medium': {'pitch': 2.0, 'tempo': 1.6},
    'fear_weak': {'pitch': 2.0, 'tempo': 1.6},
    
    # Sadness → Joy
    'sadness': {'pitch': 3.0, 'tempo': 1.4},
    'sadness_strong': {'pitch': 3.0, 'tempo': 1.4},
    'sadness_medium': {'pitch': 3.0, 'tempo': 1.4},
    'sadness_weak': {'pitch': 3.0, 'tempo': 1.4},
    
    # Disgust → Trust
    'disgust': {'pitch': 2.0, 'tempo': 1.2},
    'disgust_strong': {'pitch': 2.0, 'tempo': 1.2},
    'disgust_medium': {'pitch': 2.0, 'tempo': 1.2},
    'disgust_weak': {'pitch': 2.0, 'tempo': 1.2},
    
    # Surprise → Anticipation
    'surprise': {'pitch': -1.0, 'tempo': 0.9},
    'surprise_strong': {'pitch': -1.0, 'tempo': 0.9},
    'surprise_medium': {'pitch': -1.0, 'tempo': 0.9},
    'surprise_weak': {'pitch': -1.0, 'tempo': 0.9}
}

def get_voice_processing_config_for_emotion(emotion_id: str) -> VoiceProcessingConfig:
    """Get emotion reversal voice processing config for a specific emotion"""
    reversal = EMOTION_REVERSAL_MAP.get(emotion_id)
    if reversal:
        return VoiceProcessingConfig(
            pattern=VoiceProcessingPattern.EMOTION_REVERSE,
            pitch=reversal['pitch'],
            tempo=reversal['tempo'],
            description=f"感情逆転変換（{emotion_id} → 反対感情）"
        )
    
    # Fallback to fast_high if emotion not found
    return VOICE_PROCESSING_PATTERNS[VoiceProcessingPattern.FAST_HIGH]

def get_random_voice_processing_config() -> VoiceProcessingConfig:
    """Get a random voice processing configuration"""
    import random
    
    # 20% chance for each of the 4 basic patterns + emotion reversal (total 100%)
    patterns = list(VOICE_PROCESSING_PATTERNS.values())
    
    # Add emotion reversal as a possibility (will be configured later based on emotion)
    patterns.append(VoiceProcessingConfig(
        pattern=VoiceProcessingPattern.EMOTION_REVERSE,
        pitch=0.0,  # Will be set based on emotion
        tempo=1.0,  # Will be set based on emotion
        description="感情逆転変換"
    ))
    
    return random.choice(patterns)