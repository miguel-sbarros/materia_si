"""conversations + messages (histórico de WhatsApp por lead) — P2 / REQF03

Revision ID: 0002_conversations_messages
Revises: 0001_core_deal
Create Date: 2026-06-20

Migração aditiva: encadeia em 0001_core_deal. ``UNIQUE(conversation_id, sequence)``
torna o re-import idempotente; índice em ``external_user_id`` para upsert por chave natural.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_conversations_messages"
down_revision: Union[str, None] = "0001_core_deal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column(
            "channel", sa.String(length=40), server_default="WhatsApp", nullable=False
        ),
        sa.Column("source", sa.String(length=60), nullable=True),
        sa.Column("external_user_id", sa.String(length=120), nullable=True),
        sa.Column(
            "unread", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.UniqueConstraint(
            "lead_id", "channel", name="uq_conversations_lead_channel"
        ),
    )
    op.create_index(
        "ix_conversations_external_user_id",
        "conversations",
        ["external_user_id"],
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("sent", sa.Boolean(), nullable=False),
        sa.Column(
            "channel", sa.String(length=40), server_default="WhatsApp", nullable=False
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("read", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
        sa.UniqueConstraint(
            "conversation_id", "sequence", name="uq_messages_conversation_sequence"
        ),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_index("ix_conversations_external_user_id", table_name="conversations")
    op.drop_table("conversations")
