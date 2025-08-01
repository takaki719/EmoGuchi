"""Add Plutchik 24 emotions for wheel mode

Revision ID: 41203faded38
Revises: 60fb25ac48e3
Create Date: 2025-08-01 21:50:18.741673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41203faded38'
down_revision: Union[str, Sequence[str], None] = '60fb25ac48e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Plutchik 24 emotions for wheel mode."""
    # Get connection
    connection = op.get_bind()
    
    # Define all 24 Plutchik emotions with 3 intensity levels
    plutchik_emotions = [
        # Joy axis (0°)
        ("joy_strong", "陶酔", "Ecstasy"),
        ("joy_medium", "喜び", "Joy"),
        ("joy_weak", "平穏", "Serenity"),
        
        # Trust axis (45°)
        ("trust_strong", "敬愛", "Admiration"),
        ("trust_medium", "信頼", "Trust"),
        ("trust_weak", "容認", "Acceptance"),
        
        # Fear axis (90°)
        ("fear_strong", "恐怖", "Terror"),
        ("fear_medium", "恐れ", "Fear"),
        ("fear_weak", "不安", "Apprehension"),
        
        # Surprise axis (135°)
        ("surprise_strong", "驚嘆", "Amazement"),
        ("surprise_medium", "驚き", "Surprise"),
        ("surprise_weak", "放心", "Distraction"),
        
        # Sadness axis (180°)
        ("sadness_strong", "悲嘆", "Grief"),
        ("sadness_medium", "悲しみ", "Sadness"),
        ("sadness_weak", "哀愁", "Pensiveness"),
        
        # Disgust axis (225°)
        ("disgust_strong", "強い嫌悪", "Loathing"),
        ("disgust_medium", "嫌悪", "Disgust"),
        ("disgust_weak", "うんざり", "Boredom"),
        
        # Anger axis (270°)
        ("anger_strong", "激怒", "Rage"),
        ("anger_medium", "怒り", "Anger"),
        ("anger_weak", "苛立ち", "Annoyance"),
        
        # Anticipation axis (315°)
        ("anticipation_strong", "攻撃", "Vigilance"),
        ("anticipation_medium", "期待", "Anticipation"),
        ("anticipation_weak", "関心", "Interest"),
    ]
    
    # Insert emotions that don't already exist
    for emotion_id, name_ja, name_en in plutchik_emotions:
        # Check if emotion already exists
        existing = connection.execute(
            sa.text("SELECT id FROM emotion_types WHERE id = :emotion_id"),
            {"emotion_id": emotion_id}
        ).fetchone()
        
        if not existing:
            connection.execute(
                sa.text("""
                    INSERT INTO emotion_types (id, name_ja, name_en, created_at)
                    VALUES (:id, :name_ja, :name_en, CURRENT_TIMESTAMP)
                """),
                {"id": emotion_id, "name_ja": name_ja, "name_en": name_en}
            )


def downgrade() -> None:
    """Remove Plutchik 24 emotions."""
    # Get connection
    connection = op.get_bind()
    
    # List of Plutchik emotion IDs to remove
    plutchik_emotion_ids = [
        "joy_strong", "joy_medium", "joy_weak",
        "trust_strong", "trust_medium", "trust_weak",
        "fear_strong", "fear_medium", "fear_weak",
        "surprise_strong", "surprise_medium", "surprise_weak",
        "sadness_strong", "sadness_medium", "sadness_weak",
        "disgust_strong", "disgust_medium", "disgust_weak",
        "anger_strong", "anger_medium", "anger_weak",
        "anticipation_strong", "anticipation_medium", "anticipation_weak",
    ]
    
    # Remove the emotions (only if they exist and don't have foreign key references)
    for emotion_id in plutchik_emotion_ids:
        try:
            connection.execute(
                sa.text("DELETE FROM emotion_types WHERE id = :emotion_id"),
                {"emotion_id": emotion_id}
            )
        except Exception:
            # Ignore errors (likely due to foreign key constraints)
            pass
