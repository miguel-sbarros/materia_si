"""knowledge_chunks (corpus RAG, pgvector) — P4a

Revision ID: 0004_knowledge_chunks
Revises: 0003_lead_profiles
Create Date: 2026-06-20

Aditiva: encadeia em 0003_lead_profiles. Embedding OpenAI text-embedding-3-small (1536-dim).
A extensão ``vector`` já é habilitada em 0001; o CREATE EXTENSION aqui é no-op defensivo.
``tsv`` criado mas não populado (BM25/RRF diferido). ``UNIQUE(source, node_ref)`` = idempotência.
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0004_knowledge_chunks"
down_revision: str | None = "0003_lead_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("chunk_type", sa.String(length=40), nullable=False),
        sa.Column("node_ref", sa.String(length=200), nullable=False),
        sa.Column("label", sa.String(length=60), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("persona", sa.String(length=60), nullable=True),
        sa.Column("spin_stage", sa.String(length=40), nullable=True),
        sa.Column("meta", pg.JSONB(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("tsv", pg.TSVECTOR(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("source", "node_ref", name="uq_knowledge_chunks_source_ref"),
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
