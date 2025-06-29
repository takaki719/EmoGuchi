import { VoiceProcessingConfig, VoiceProcessingPattern } from '@/types/game';

export const VOICE_PROCESSING_PATTERNS: Record<VoiceProcessingPattern, VoiceProcessingConfig> = {
  fast_high: {
    pattern: 'fast_high',
    pitch: 2.0,
    tempo: 1.5,
    description: '高速・高ピッチ（興奮・喜びの印象）'
  },
  slow_low: {
    pattern: 'slow_low',
    pitch: -3.0,
    tempo: 0.8,
    description: '低速・低ピッチ（落ち着いた・暗い印象）'
  },
  pitch_up: {
    pattern: 'pitch_up',
    pitch: 3.0,
    tempo: 1.0,
    description: 'ピッチ上昇（可愛さ・軽快さ）'
  },
  tempo_up: {
    pattern: 'tempo_up',
    pitch: 0.0,
    tempo: 1.5,
    description: 'テンポ上昇（緊張・焦り・興奮感）'
  },
  emotion_reverse: {
    pattern: 'emotion_reverse',
    pitch: 0.0, // Will be set based on emotion mapping
    tempo: 1.0, // Will be set based on emotion mapping
    description: '感情逆転変換（反対感情の音声特徴を模倣）'
  }
};

// Plutchik emotion reversal mapping
export const EMOTION_REVERSAL_MAP: Record<string, { pitch: number; tempo: number }> = {
  // Joy → Sadness
  'joy': { pitch: -3.0, tempo: 0.8 },
  'joy_strong': { pitch: -3.0, tempo: 0.8 },
  'joy_medium': { pitch: -3.0, tempo: 0.8 },
  'joy_weak': { pitch: -3.0, tempo: 0.8 },
  
  // Anger → Fear
  'anger': { pitch: -2.0, tempo: 0.85 },
  'anger_strong': { pitch: -2.0, tempo: 0.85 },
  'anger_medium': { pitch: -2.0, tempo: 0.85 },
  'anger_weak': { pitch: -2.0, tempo: 0.85 },
  
  // Trust → Disgust
  'trust': { pitch: -1.5, tempo: 0.9 },
  'trust_strong': { pitch: -1.5, tempo: 0.9 },
  'trust_medium': { pitch: -1.5, tempo: 0.9 },
  'trust_weak': { pitch: -1.5, tempo: 0.9 },
  
  // Anticipation → Surprise
  'anticipation': { pitch: 2.0, tempo: 1.4 },
  'anticipation_strong': { pitch: 2.0, tempo: 1.4 },
  'anticipation_medium': { pitch: 2.0, tempo: 1.4 },
  'anticipation_weak': { pitch: 2.0, tempo: 1.4 },
  
  // Fear → Anger
  'fear': { pitch: 2.0, tempo: 1.6 },
  'fear_strong': { pitch: 2.0, tempo: 1.6 },
  'fear_medium': { pitch: 2.0, tempo: 1.6 },
  'fear_weak': { pitch: 2.0, tempo: 1.6 },
  
  // Sadness → Joy
  'sadness': { pitch: 3.0, tempo: 1.4 },
  'sadness_strong': { pitch: 3.0, tempo: 1.4 },
  'sadness_medium': { pitch: 3.0, tempo: 1.4 },
  'sadness_weak': { pitch: 3.0, tempo: 1.4 },
  
  // Disgust → Trust
  'disgust': { pitch: 2.0, tempo: 1.2 },
  'disgust_strong': { pitch: 2.0, tempo: 1.2 },
  'disgust_medium': { pitch: 2.0, tempo: 1.2 },
  'disgust_weak': { pitch: 2.0, tempo: 1.2 },
  
  // Surprise → Anticipation
  'surprise': { pitch: -1.0, tempo: 0.9 },
  'surprise_strong': { pitch: -1.0, tempo: 0.9 },
  'surprise_medium': { pitch: -1.0, tempo: 0.9 },
  'surprise_weak': { pitch: -1.0, tempo: 0.9 }
};

export function getVoiceProcessingForEmotion(emotionId: string): VoiceProcessingConfig {
  const reversal = EMOTION_REVERSAL_MAP[emotionId];
  if (reversal) {
    return {
      pattern: 'emotion_reverse',
      pitch: reversal.pitch,
      tempo: reversal.tempo,
      description: `感情逆転変換（${emotionId} → 反対感情）`
    };
  }
  
  // Fallback to a random pattern if emotion not found
  const patterns = Object.values(VOICE_PROCESSING_PATTERNS).filter(p => p.pattern !== 'emotion_reverse');
  return patterns[Math.floor(Math.random() * patterns.length)];
}

export function getRandomVoiceProcessingPattern(): VoiceProcessingConfig {
  const patterns = Object.values(VOICE_PROCESSING_PATTERNS);
  return patterns[Math.floor(Math.random() * patterns.length)];
}