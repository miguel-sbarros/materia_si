"""lead_profiles (análise de conversa por lead, 1:1) — P3 / REQF08

Revision ID: 0003_lead_profiles
Revises: 0002_conversations_messages
Create Date: 2026-06-20

Migração aditiva: encadeia em 0002_conversations_messages. ``UNIQUE(lead_id)`` torna o
perfil 1:1 com o lead (upsert na re-análise). Listas/dicts em colunas ``JSONB``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

from alembic import op

revision: str = "0003_lead_profiles"
down_revision: str | None = "0002_conversations_messages"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lead_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        # Entidades.
        sa.Column("especialidade", sa.String(length=160), nullable=True),
        sa.Column("experiencia", sa.String(length=160), nullable=True),
        sa.Column("cidade_estado", sa.String(length=160), nullable=True),
        sa.Column("course_interest", sa.String(length=160), nullable=True),
        sa.Column("dores_verbalizadas", pg.JSONB(), nullable=True),
        sa.Column("desejos_expressos", pg.JSONB(), nullable=True),
        sa.Column("objecoes", pg.JSONB(), nullable=True),
        # comentarios engloba hardware/software, termos técnicos e marcadores de contexto.
        sa.Column("comentarios", pg.JSONB(), nullable=True),
        # Persona.
        sa.Column("matched_persona", sa.String(length=60), nullable=True),
        sa.Column("persona_confidence", sa.Float(), nullable=True),
        sa.Column("persona_reasoning", sa.Text(), nullable=True),
        # Diálogo.
        sa.Column("current_spin_stage", sa.String(length=40), nullable=True),
        sa.Column("lead_score", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        # Métricas da conversa.
        sa.Column("median_seller_latency_seconds", sa.Integer(), nullable=True),
        sa.Column("median_lead_latency_seconds", sa.Integer(), nullable=True),
        sa.Column("first_response_latency_seconds", sa.Integer(), nullable=True),
        sa.Column("last_message_sent", sa.Boolean(), nullable=True),
        sa.Column(
            "is_abandoned",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("abandon_spin_stage", sa.String(length=40), nullable=True),
        # Metadados.
        sa.Column("model_used", sa.String(length=60), nullable=True),
        sa.Column("raw", pg.JSONB(), nullable=True),
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
        sa.UniqueConstraint("lead_id", name="uq_lead_profiles_lead"),
    )


def downgrade() -> None:
    op.drop_table("lead_profiles")
