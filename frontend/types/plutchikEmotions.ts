export type IntensityLevel = 'weak' | 'medium' | 'strong';

export interface PlutchikEmotion {
  id: string;
  axis: string; // Base emotion axis (joy, anger, etc.)
  intensity: IntensityLevel;
  nameJa: string;
  nameEn: string;
  color: string;
  angle: number;
  emoji: string;
}

// 24 emotions with 3 intensity levels for each of the 8 basic axes
export const PLUTCHIK_EMOTIONS_3_LAYER: PlutchikEmotion[] = [
  // Joy axis (0°)
  {
    id: 'joy_strong',
    axis: 'joy',
    intensity: 'strong',
    nameJa: '陶酔',
    nameEn: 'Ecstasy',
    color: '#FFD700',
    angle: 0,
    emoji: '🤩'
  },
  {
    id: 'joy_medium',
    axis: 'joy',
    intensity: 'medium',
    nameJa: '喜び',
    nameEn: 'Joy',
    color: '#FFE55C',
    angle: 0,
    emoji: '😊'
  },
  {
    id: 'joy_weak',
    axis: 'joy',
    intensity: 'weak',
    nameJa: '平穏',
    nameEn: 'Serenity',
    color: '#FFF2B8',
    angle: 0,
    emoji: '😌'
  },

  // Trust axis (45°)
  {
    id: 'trust_strong',
    axis: 'trust',
    intensity: 'strong',
    nameJa: '敬愛',
    nameEn: 'Admiration',
    color: '#32CD32',
    angle: 45,
    emoji: '🤝'
  },
  {
    id: 'trust_medium',
    axis: 'trust',
    intensity: 'medium',
    nameJa: '信頼',
    nameEn: 'Trust',
    color: '#90EE90',
    angle: 45,
    emoji: '😊'
  },
  {
    id: 'trust_weak',
    axis: 'trust',
    intensity: 'weak',
    nameJa: '容認',
    nameEn: 'Acceptance',
    color: '#C8F7C5',
    angle: 45,
    emoji: '🙂'
  },

  // Fear axis (90°)
  {
    id: 'fear_strong',
    axis: 'fear',
    intensity: 'strong',
    nameJa: '恐怖',
    nameEn: 'Terror',
    color: '#800080',
    angle: 90,
    emoji: '😱'
  },
  {
    id: 'fear_medium',
    axis: 'fear',
    intensity: 'medium',
    nameJa: '恐れ',
    nameEn: 'Fear',
    color: '#9370DB',
    angle: 90,
    emoji: '😰'
  },
  {
    id: 'fear_weak',
    axis: 'fear',
    intensity: 'weak',
    nameJa: '不安',
    nameEn: 'Apprehension',
    color: '#C8A2C8',
    angle: 90,
    emoji: '😟'
  },

  // Surprise axis (135°)
  {
    id: 'surprise_strong',
    axis: 'surprise',
    intensity: 'strong',
    nameJa: '驚嘆',
    nameEn: 'Amazement',
    color: '#1E90FF',
    angle: 135,
    emoji: '😱'
  },
  {
    id: 'surprise_medium',
    axis: 'surprise',
    intensity: 'medium',
    nameJa: '驚き',
    nameEn: 'Surprise',
    color: '#87CEEB',
    angle: 135,
    emoji: '😲'
  },
  {
    id: 'surprise_weak',
    axis: 'surprise',
    intensity: 'weak',
    nameJa: '放心',
    nameEn: 'Distraction',
    color: '#B6E2FF',
    angle: 135,
    emoji: '😐'
  },

  // Sadness axis (180°)
  {
    id: 'sadness_strong',
    axis: 'sadness',
    intensity: 'strong',
    nameJa: '悲嘆',
    nameEn: 'Grief',
    color: '#000080',
    angle: 180,
    emoji: '😭'
  },
  {
    id: 'sadness_medium',
    axis: 'sadness',
    intensity: 'medium',
    nameJa: '悲しみ',
    nameEn: 'Sadness',
    color: '#4169E1',
    angle: 180,
    emoji: '😢'
  },
  {
    id: 'sadness_weak',
    axis: 'sadness',
    intensity: 'weak',
    nameJa: '哀愁',
    nameEn: 'Pensiveness',
    color: '#87CEEB',
    angle: 180,
    emoji: '😔'
  },

  // Disgust axis (225°)
  {
    id: 'disgust_strong',
    axis: 'disgust',
    intensity: 'strong',
    nameJa: '強い嫌悪',
    nameEn: 'Loathing',
    color: '#654321',
    angle: 225,
    emoji: '🤮'
  },
  {
    id: 'disgust_medium',
    axis: 'disgust',
    intensity: 'medium',
    nameJa: '嫌悪',
    nameEn: 'Disgust',
    color: '#8B4513',
    angle: 225,
    emoji: '🤢'
  },
  {
    id: 'disgust_weak',
    axis: 'disgust',
    intensity: 'weak',
    nameJa: 'うんざり',
    nameEn: 'Boredom',
    color: '#D2B48C',
    angle: 225,
    emoji: '😒'
  },

  // Anger axis (270°)
  {
    id: 'anger_strong',
    axis: 'anger',
    intensity: 'strong',
    nameJa: '激怒',
    nameEn: 'Rage',
    color: '#DC143C',
    angle: 270,
    emoji: '😡'
  },
  {
    id: 'anger_medium',
    axis: 'anger',
    intensity: 'medium',
    nameJa: '怒り',
    nameEn: 'Anger',
    color: '#FF4500',
    angle: 270,
    emoji: '😠'
  },
  {
    id: 'anger_weak',
    axis: 'anger',
    intensity: 'weak',
    nameJa: '苛立ち',
    nameEn: 'Annoyance',
    color: '#FF8C69',
    angle: 270,
    emoji: '😤'
  },

  // Anticipation axis (315°)
  {
    id: 'anticipation_strong',
    axis: 'anticipation',
    intensity: 'strong',
    nameJa: '攻撃',
    nameEn: 'Vigilance',
    color: '#FF8C00',
    angle: 315,
    emoji: '👁️'
  },
  {
    id: 'anticipation_medium',
    axis: 'anticipation',
    intensity: 'medium',
    nameJa: '期待',
    nameEn: 'Anticipation',
    color: '#FFA500',
    angle: 315,
    emoji: '🤔'
  },
  {
    id: 'anticipation_weak',
    axis: 'anticipation',
    intensity: 'weak',
    nameJa: '関心',
    nameEn: 'Interest',
    color: '#FFCC99',
    angle: 315,
    emoji: '🧐'
  }
];

// Helper functions
export function getEmotionsByAxis(axis: string): PlutchikEmotion[] {
  return PLUTCHIK_EMOTIONS_3_LAYER.filter(emotion => emotion.axis === axis);
}

export function getEmotionsByIntensity(intensity: IntensityLevel): PlutchikEmotion[] {
  return PLUTCHIK_EMOTIONS_3_LAYER.filter(emotion => emotion.intensity === intensity);
}

export function getEmotionById(id: string): PlutchikEmotion | undefined {
  return PLUTCHIK_EMOTIONS_3_LAYER.find(emotion => emotion.id === id);
}

export function getAxes(): string[] {
  return Array.from(new Set(PLUTCHIK_EMOTIONS_3_LAYER.map(emotion => emotion.axis)));
}

export function getIntensityLevels(): IntensityLevel[] {
  return ['weak', 'medium', 'strong'];
}

// Calculate distance between two emotions considering both axis and intensity
export function calculateEmotionDistance(emotion1: PlutchikEmotion, emotion2: PlutchikEmotion): number {
  // Calculate axis distance (0-4 on the wheel)
  const angle1 = emotion1.angle;
  const angle2 = emotion2.angle;
  const angleDiff = Math.abs(angle1 - angle2);
  const axisDistance = Math.min(angleDiff, 360 - angleDiff) / 45; // Convert to 0-4 scale

  // Calculate intensity distance (0-2)
  const intensityLevels = ['weak', 'medium', 'strong'];
  const intensity1Index = intensityLevels.indexOf(emotion1.intensity);
  const intensity2Index = intensityLevels.indexOf(emotion2.intensity);
  const intensityDistance = Math.abs(intensity1Index - intensity2Index);

  // Combine both distances with weighting
  // Axis distance is more important than intensity difference
  return axisDistance + (intensityDistance * 0.5);
}