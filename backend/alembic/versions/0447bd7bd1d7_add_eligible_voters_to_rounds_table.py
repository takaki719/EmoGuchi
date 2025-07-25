"""add eligible_voters to rounds table

Revision ID: 0447bd7bd1d7
Revises: 58d909b82a5f
Create Date: 2025-07-25 19:23:51.676466

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0447bd7bd1d7'
down_revision: Union[str, Sequence[str], None] = '58d909b82a5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('rounds', 
        sa.Column('eligible_voters', sa.Text(), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('rounds', 'eligible_voters')
