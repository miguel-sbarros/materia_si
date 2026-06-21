"""copilot_sessions / copilot_messages — P4b

Revision ID: 0005_copilot_sessions
Revises: 0004_knowledge_chunks
Create Date: 2026-06-20

Aditiva: encadeia em 0004_knowledge_chunks. Mensagens do copiloto são DISTINTAS das
mensagens lead/vendedor (messages). ``lead_id`` nullable; ``UNIQUE(session_id, sequence)``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

from alembic import op

revision: str = "0005_copilot_sessions"
down_revision: str | None = "0004_knowledge_chunks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "copilot_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
    )
    op.create_table(
        "copilot_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("advice", pg.JSONB(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["copilot_sessions.id"]),
        sa.UniqueConstraint("session_id", "sequence", name="uq_copilot_messages_session_seq"),
    )


def downgrade() -> None:
    op.drop_table("copilot_messages")
    op.drop_table("copilot_sessions")
