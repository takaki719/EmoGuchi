"""add voting timeout fields to rounds table

Revision ID: 60fb25ac48e3
Revises: 0447bd7bd1d7
Create Date: 2025-07-25 19:35:54.906093

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60fb25ac48e3'
down_revision: Union[str, Sequence[str], None] = '0447bd7bd1d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('rounds', 
        sa.Column('voting_started_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column('rounds', 
        sa.Column('vote_timeout_seconds', sa.Integer(), nullable=True, default=30)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('rounds', 'vote_timeout_seconds')
    op.drop_column('rounds', 'voting_started_at')
