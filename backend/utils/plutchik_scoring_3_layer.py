from typing import Dict, List, Tuple
from models.emotion_3_layer import (
    EMOTIONS_3_LAYER, 
    Emotion3Layer, 
    EmotionAxis, 
    IntensityLevel,
    get_emotion_by_id
)

class PlutchikScoringResult3Layer:
    def __init__(self, score: int, axis_distance: int, intensity_distance: int, 
                 total_distance: float, relationship: str, intensity_match: str, max_score: int):
        self.score = score
        self.axis_distance = axis_distance
        self.intensity_distance = intensity_distance
        self.total_distance = total_distance
        self.relationship = relationship
        self.intensity_match = intensity_match
        self.max_score = max_score

# Emotion axis positions on the wheel (0-7)
AXIS_POSITIONS: Dict[EmotionAxis, int] = {
    EmotionAxis.JOY: 0,
    EmotionAxis.TRUST: 1,
    EmotionAxis.FEAR: 2,
    EmotionAxis.SURPRISE: 3,
    EmotionAxis.SADNESS: 4,
    EmotionAxis.DISGUST: 5,
    EmotionAxis.ANGER: 6,
    EmotionAxis.ANTICIPATION: 7
}

INTENSITY_VALUES: Dict[IntensityLevel, int] = {
    IntensityLevel.WEAK: 0,
    IntensityLevel.MEDIUM: 1,
    IntensityLevel.STRONG: 2
}

def calculate_axis_distance(axis1: EmotionAxis, axis2: EmotionAxis) -> int:
    """Calculate the distance between two emotion axes on Plutchik's wheel."""
    pos1 = AXIS_POSITIONS[axis1]
    pos2 = AXIS_POSITIONS[axis2]
    
    if pos1 == pos2:
        return 0
    
    direct_distance = abs(pos1 - pos2)
    circular_distance = 8 - direct_distance
    
    return min(direct_distance, circular_distance)

def calculate_intensity_distance(intensity1: IntensityLevel, intensity2: IntensityLevel) -> int:
    """Calculate the distance between two intensity levels."""
    val1 = INTENSITY_VALUES[intensity1]
    val2 = INTENSITY_VALUES[intensity2]
    return abs(val1 - val2)

def calculate_emotion_distance(emotion1: Emotion3Layer, emotion2: Emotion3Layer) -> float:
    """Calculate total distance between two emotions considering both axis and intensity."""
    axis_distance = calculate_axis_distance(emotion1.axis, emotion2.axis)
    intensity_distance = calculate_intensity_distance(emotion1.intensity, emotion2.intensity)
    
    # Combine both distances with weighting (axis distance is more important)
    return axis_distance + (intensity_distance * 0.5)

def get_axis_relationship(axis1: EmotionAxis, axis2: EmotionAxis) -> str:
    """Get the relationship type between two emotion axes."""
    if axis1 == axis2:
        return 'same_axis'
    
    distance = calculate_axis_distance(axis1, axis2)
    
    if distance == 1:
        return 'adjacent_axis'
    elif distance == 4:
        return 'opposite_axis'
    else:
        return 'distant_axis'

def get_intensity_match(intensity1: IntensityLevel, intensity2: IntensityLevel) -> str:
    """Get the intensity match type between two intensity levels."""
    distance = calculate_intensity_distance(intensity1, intensity2)
    
    if distance == 0:
        return 'exact'
    elif distance == 1:
        return 'close'
    else:
        return 'far'

def calculate_plutchik_score_3_layer(
    correct_emotion_id: str, 
    guessed_emotion_id: str, 
    max_score: int = 100
) -> PlutchikScoringResult3Layer:
    """
    Calculate score based on 3-layer Plutchik wheel distance.
    
    Args:
        correct_emotion_id: The correct emotion ID
        guessed_emotion_id: The guessed emotion ID
        max_score: Maximum possible score (default 100)
    
    Returns:
        PlutchikScoringResult3Layer with detailed scoring information
    """
    try:
        correct_emotion = get_emotion_by_id(correct_emotion_id)
        guessed_emotion = get_emotion_by_id(guessed_emotion_id)
    except ValueError as e:
        raise ValueError(f"Invalid emotion ID: {e}")

    # Exact match
    if correct_emotion_id == guessed_emotion_id:
        return PlutchikScoringResult3Layer(
            score=max_score,
            axis_distance=0,
            intensity_distance=0,
            total_distance=0.0,
            relationship='exact',
            intensity_match='exact',
            max_score=max_score
        )

    axis_distance = calculate_axis_distance(correct_emotion.axis, guessed_emotion.axis)
    intensity_distance = calculate_intensity_distance(correct_emotion.intensity, guessed_emotion.intensity)
    total_distance = calculate_emotion_distance(correct_emotion, guessed_emotion)
    
    relationship = get_axis_relationship(correct_emotion.axis, guessed_emotion.axis)
    intensity_match = get_intensity_match(correct_emotion.intensity, guessed_emotion.intensity)

    score = 0

    # Base score calculation based on axis relationship
    if relationship == 'same_axis':
        # Same emotion axis, different intensity
        if intensity_match == 'close':
            score = int(max_score * 0.85)  # 85% for adjacent intensity
        elif intensity_match == 'far':
            score = int(max_score * 0.70)  # 70% for opposite intensity
    elif relationship == 'adjacent_axis':
        # Adjacent emotion on the wheel
        if intensity_match == 'exact':
            score = int(max_score * 0.60)  # 60% for adjacent axis, same intensity
        elif intensity_match == 'close':
            score = int(max_score * 0.45)  # 45% for adjacent axis, close intensity
        elif intensity_match == 'far':
            score = int(max_score * 0.30)  # 30% for adjacent axis, far intensity
    elif relationship == 'opposite_axis':
        # Opposite emotions (180 degrees apart)
        if intensity_match == 'exact':
            score = int(max_score * 0.10)  # 10% for opposite axis, same intensity
        elif intensity_match == 'close':
            score = int(max_score * 0.05)  # 5% for opposite axis, close intensity
        else:  # far
            score = 0  # 0% for opposite axis, far intensity
    else:  # distant_axis
        # 2-3 steps away on the wheel
        if intensity_match == 'exact':
            score = int(max_score * 0.25)  # 25% for distant axis, same intensity
        elif intensity_match == 'close':
            score = int(max_score * 0.15)  # 15% for distant axis, close intensity
        elif intensity_match == 'far':
            score = int(max_score * 0.05)  # 5% for distant axis, far intensity

    return PlutchikScoringResult3Layer(
        score=score,
        axis_distance=axis_distance,
        intensity_distance=intensity_distance,
        total_distance=total_distance,
        relationship=relationship,
        intensity_match=intensity_match,
        max_score=max_score
    )

def calculate_speaker_bonus_3_layer(
    correct_emotion_id: str, 
    votes: Dict[str, str], 
    base_points: int = 10
) -> int:
    """
    Calculate speaker bonus based on how well listeners understood the emotion.
    Uses 3-layer scoring to give partial credit for close guesses.
    
    Args:
        correct_emotion_id: The emotion the speaker was expressing
        votes: Dictionary of player_id -> emotion_id votes
        base_points: Base points per listener
    
    Returns:
        Total bonus points for the speaker
    """
    total_bonus = 0
    
    for vote in votes.values():
        try:
            result = calculate_plutchik_score_3_layer(correct_emotion_id, vote, base_points)
            total_bonus += result.score
        except ValueError:
            # Skip invalid votes
            continue
    
    return total_bonus

def get_adjacent_emotions_3_layer(emotion_id: str) -> List[str]:
    """Get adjacent emotions for a given emotion in 3-layer model."""
    try:
        emotion = get_emotion_by_id(emotion_id)
    except ValueError:
        return []
    
    adjacent = []
    
    # Get emotions on adjacent axes with same intensity
    for other_emotion in EMOTIONS_3_LAYER.values():
        if other_emotion.id == emotion_id:
            continue
            
        axis_distance = calculate_axis_distance(emotion.axis, other_emotion.axis)
        intensity_distance = calculate_intensity_distance(emotion.intensity, other_emotion.intensity)
        
        # Adjacent if on neighboring axis with same intensity, or same axis with neighboring intensity
        if (axis_distance == 1 and intensity_distance == 0) or \
           (axis_distance == 0 and intensity_distance == 1):
            adjacent.append(other_emotion.id)
    
    return adjacent

def get_opposite_emotion_3_layer(emotion_id: str) -> str:
    """Get the opposite emotion for a given emotion in 3-layer model."""
    try:
        emotion = get_emotion_by_id(emotion_id)
    except ValueError:
        return ""
    
    # Find emotion on opposite axis with same intensity
    for other_emotion in EMOTIONS_3_LAYER.values():
        axis_distance = calculate_axis_distance(emotion.axis, other_emotion.axis)
        intensity_distance = calculate_intensity_distance(emotion.intensity, other_emotion.intensity)
        
        if axis_distance == 4 and intensity_distance == 0:
            return other_emotion.id
    
    return ""

def is_emotion_adjacent_3_layer(emotion1_id: str, emotion2_id: str) -> bool:
    """Check if two emotions are adjacent in the 3-layer model."""
    try:
        emotion1 = get_emotion_by_id(emotion1_id)
        emotion2 = get_emotion_by_id(emotion2_id)
    except ValueError:
        return False
    
    axis_distance = calculate_axis_distance(emotion1.axis, emotion2.axis)
    intensity_distance = calculate_intensity_distance(emotion1.intensity, emotion2.intensity)
    
    # Adjacent if neighboring on axis with same intensity, or same axis with neighboring intensity
    return (axis_distance == 1 and intensity_distance == 0) or \
           (axis_distance == 0 and intensity_distance == 1)

def is_emotion_opposite_3_layer(emotion1_id: str, emotion2_id: str) -> bool:
    """Check if two emotions are opposite in the 3-layer model."""
    try:
        emotion1 = get_emotion_by_id(emotion1_id)
        emotion2 = get_emotion_by_id(emotion2_id)
    except ValueError:
        return False
    
    axis_distance = calculate_axis_distance(emotion1.axis, emotion2.axis)
    return axis_distance == 4