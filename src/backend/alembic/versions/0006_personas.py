"""personas (tabela de referência das 4 personas-alvo) — P4

Revision ID: 0006_personas
Revises: 0005_copilot_sessions
Create Date: 2026-06-20

Aditiva: encadeia em 0005_copilot_sessions. Semeada pela ingestão a partir dos nós
``Persona`` do grafo legado (upsert idempotente em ``code``).
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

from alembic import op

revision: str = "0006_personas"
down_revision: str | None = "0005_copilot_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "personas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("desejos", sa.Text(), nullable=True),
        sa.Column("medos", sa.Text(), nullable=True),
        sa.Column("volume_leads", sa.String(length=20), nullable=True),
        sa.Column("taxa_conversao", sa.String(length=20), nullable=True),
        sa.Column("palavras_chave", pg.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("code", name="uq_personas_code"),
    )


def downgrade() -> None:
    op.drop_table("personas")
