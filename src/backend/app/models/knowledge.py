"""KnowledgeChunk — corpus RAG da base de conhecimento (P4a).

Um chunk por nó do grafo legado (``legacy_neo4j_kb.json``) ou por seção de
``playbook/*.md``. Embedding via OpenAI (``text-embedding-3-small``, 1536-dim) em
``pgvector``. Recuperação por similaridade de cosseno (``rag.retrieve``); chunks de
``Script`` carregam ``persona``+``spin_stage`` para boost por persona/estágio SPIN.

Idempotência da ingestão: ``UNIQUE(source, node_ref)`` (re-rodar substitui, não duplica).
A coluna ``tsv`` é criada agora (decisão CLAUDE.md) mas fica não-populada — BM25/RRF diferido.
"""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import get_settings
from app.db.base import Base

EMBEDDING_DIM = get_settings().embedding_dim


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # 'kb_graph' (legacy_neo4j_kb.json) | 'playbook' (playbook/*.md)
    source: Mapped[str] = mapped_column(String(40))
    # 'node' | 'playbook_section'
    chunk_type: Mapped[str] = mapped_column(String(40))
    # Chave natural dentro da fonte: f"node:{id}" / f"script:{id}" / "file.md#slug".
    node_ref: Mapped[str] = mapped_column(String(200))
    label: Mapped[str | None] = mapped_column(String(60), nullable=True)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    # Persona/estágio SPIN (valores de enum) — só em chunks Script; alimentam o boost.
    persona: Mapped[str | None] = mapped_column(String(60), nullable=True)
    spin_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    # Construído agora, populado depois (BM25/RRF diferido).
    tsv: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("source", "node_ref", name="uq_knowledge_chunks_source_ref"),
    )
