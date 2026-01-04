"""initial schema

Revision ID: add40338d5bc
Revises: d46d5571885e
Create Date: 2026-01-03 14:04:25.894587

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add40338d5bc'
down_revision: Union[str, Sequence[str], None] = 'd46d5571885e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
