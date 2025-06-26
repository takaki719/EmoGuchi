import { PlutchikEmotion, IntensityLevel, calculateEmotionDistance, getEmotionById } from '../types/plutchikEmotions';

export interface PlutchikScoringResult3Layer {
  score: number;
  axisDistance: number;
  intensityDistance: number;
  totalDistance: number;
  relationship: 'exact' | 'same_axis' | 'adjacent_axis' | 'opposite_axis' | 'distant_axis';
  intensityMatch: 'exact' | 'close' | 'far';
  maxScore: number;
}

// Emotion axis positions on the wheel (0-7)
const AXIS_POSITIONS: Record<string, number> = {
  'joy': 0,
  'trust': 1,
  'fear': 2,
  'surprise': 3,
  'sadness': 4,
  'disgust': 5,
  'anger': 6,
  'anticipation': 7
};

const INTENSITY_VALUES: Record<IntensityLevel, number> = {
  'weak': 0,
  'medium': 1,
  'strong': 2
};

export function calculateAxisDistance(axis1: string, axis2: string): number {
  const pos1 = AXIS_POSITIONS[axis1];
  const pos2 = AXIS_POSITIONS[axis2];
  
  if (pos1 === undefined || pos2 === undefined) {
    throw new Error(`Invalid axis: ${axis1}, ${axis2}`);
  }
  
  if (pos1 === pos2) return 0;
  
  const directDistance = Math.abs(pos1 - pos2);
  const circularDistance = 8 - directDistance;
  
  return Math.min(directDistance, circularDistance);
}

export function calculateIntensityDistance(intensity1: IntensityLevel, intensity2: IntensityLevel): number {
  const val1 = INTENSITY_VALUES[intensity1];
  const val2 = INTENSITY_VALUES[intensity2];
  return Math.abs(val1 - val2);
}

export function getAxisRelationship(axis1: string, axis2: string): PlutchikScoringResult3Layer['relationship'] {
  if (axis1 === axis2) return 'same_axis';
  
  const distance = calculateAxisDistance(axis1, axis2);
  
  switch (distance) {
    case 1:
      return 'adjacent_axis';
    case 4:
      return 'opposite_axis';
    case 2:
    case 3:
      return 'distant_axis';
    default:
      return 'distant_axis';
  }
}

export function getIntensityMatch(intensity1: IntensityLevel, intensity2: IntensityLevel): PlutchikScoringResult3Layer['intensityMatch'] {
  const distance = calculateIntensityDistance(intensity1, intensity2);
  
  switch (distance) {
    case 0:
      return 'exact';
    case 1:
      return 'close';
    case 2:
      return 'far';
    default:
      return 'far';
  }
}

export function calculatePlutchikScore3Layer(
  correctEmotionId: string, 
  guessedEmotionId: string,
  maxScore: number = 100
): PlutchikScoringResult3Layer {
  const correctEmotion = getEmotionById(correctEmotionId);
  const guessedEmotion = getEmotionById(guessedEmotionId);
  
  if (!correctEmotion || !guessedEmotion) {
    throw new Error(`Invalid emotion IDs: ${correctEmotionId}, ${guessedEmotionId}`);
  }

  // Exact match
  if (correctEmotionId === guessedEmotionId) {
    return {
      score: maxScore,
      axisDistance: 0,
      intensityDistance: 0,
      totalDistance: 0,
      relationship: 'exact',
      intensityMatch: 'exact',
      maxScore
    };
  }

  const axisDistance = calculateAxisDistance(correctEmotion.axis, guessedEmotion.axis);
  const intensityDistance = calculateIntensityDistance(correctEmotion.intensity, guessedEmotion.intensity);
  const totalDistance = calculateEmotionDistance(correctEmotion, guessedEmotion);
  
  const relationship = getAxisRelationship(correctEmotion.axis, guessedEmotion.axis);
  const intensityMatch = getIntensityMatch(correctEmotion.intensity, guessedEmotion.intensity);

  let score = 0;

  // Base score calculation based on axis relationship
  switch (relationship) {
    case 'same_axis':
      // Same emotion axis, different intensity
      switch (intensityMatch) {
        case 'close':
          score = Math.round(maxScore * 0.85); // 85% for adjacent intensity
          break;
        case 'far':
          score = Math.round(maxScore * 0.70); // 70% for opposite intensity
          break;
      }
      break;
      
    case 'adjacent_axis':
      // Adjacent emotion on the wheel
      switch (intensityMatch) {
        case 'exact':
          score = Math.round(maxScore * 0.60); // 60% for adjacent axis, same intensity
          break;
        case 'close':
          score = Math.round(maxScore * 0.45); // 45% for adjacent axis, close intensity
          break;
        case 'far':
          score = Math.round(maxScore * 0.30); // 30% for adjacent axis, far intensity
          break;
      }
      break;
      
    case 'opposite_axis':
      // Opposite emotions (180 degrees apart)
      switch (intensityMatch) {
        case 'exact':
          score = Math.round(maxScore * 0.10); // 10% for opposite axis, same intensity
          break;
        case 'close':
          score = Math.round(maxScore * 0.05); // 5% for opposite axis, close intensity
          break;
        case 'far':
          score = 0; // 0% for opposite axis, far intensity
          break;
      }
      break;
      
    case 'distant_axis':
      // 2-3 steps away on the wheel
      switch (intensityMatch) {
        case 'exact':
          score = Math.round(maxScore * 0.25); // 25% for distant axis, same intensity
          break;
        case 'close':
          score = Math.round(maxScore * 0.15); // 15% for distant axis, close intensity
          break;
        case 'far':
          score = Math.round(maxScore * 0.05); // 5% for distant axis, far intensity
          break;
      }
      break;
  }

  return {
    score,
    axisDistance,
    intensityDistance,
    totalDistance,
    relationship,
    intensityMatch,
    maxScore
  };
}

export function calculateSpeakerBonus3Layer(
  correctEmotionId: string, 
  votes: Record<string, string>, 
  basePoints: number = 10
): number {
  let totalBonus = 0;
  
  for (const vote of Object.values(votes)) {
    const result = calculatePlutchikScore3Layer(correctEmotionId, vote, basePoints);
    totalBonus += result.score;
  }
  
  return totalBonus;
}

// Helper function to get scoring explanation
export function getScoreExplanation(result: PlutchikScoringResult3Layer): string {
  if (result.relationship === 'exact') {
    return '完全一致！';
  }
  
  let explanation = '';
  
  switch (result.relationship) {
    case 'same_axis':
      explanation = '同じ感情軸';
      break;
    case 'adjacent_axis':
      explanation = '隣接する感情軸';
      break;
    case 'opposite_axis':
      explanation = '対極の感情軸';
      break;
    case 'distant_axis':
      explanation = '離れた感情軸';
      break;
  }
  
  switch (result.intensityMatch) {
    case 'exact':
      explanation += '、同じ強度';
      break;
    case 'close':
      explanation += '、近い強度';
      break;
    case 'far':
      explanation += '、離れた強度';
      break;
  }
  
  return explanation;
}