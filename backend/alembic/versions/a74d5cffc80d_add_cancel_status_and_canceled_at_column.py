"""add CANCEL status and canceled_at column

Revision ID: a74d5cffc80d
Revises: d3f3fe3ddc15
Create Date: 2026-02-11 14:32:11.658228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a74d5cffc80d'
down_revision: Union[str, Sequence[str], None] = 'd3f3fe3ddc15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE casestatus ADD VALUE IF NOT EXISTS 'CANCEL'")
    op.add_column('cs_cases', sa.Column('canceled_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('cs_cases', 'canceled_at')
