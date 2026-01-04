"""add chat tables

Revision ID: 8b3210682a04
Revises: add40338d5bc
Create Date: 2026-01-03 19:18:11.447257

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8b3210682a04'
down_revision: Union[str, Sequence[str], None] = 'add40338d5bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "chats",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("chat_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=20)),
        sa.Column("content", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"]),
    )



def downgrade() -> None:
    """Downgrade schema."""
    pass
