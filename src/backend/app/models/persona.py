"""Persona — as 4 personas-alvo da MR, persistidas em tabela (P4).

Dados de referência (não derivados em runtime): nome, resumo, dores/desejos, medos,
volume de leads e taxa de conversão "de catálogo". Semeadas a partir dos nós ``Persona``
do grafo legado (``legacy_neo4j_kb.json``) pela ingestão (upsert idempotente em ``code``).
``code`` = valor do enum ``PersonaType`` (ex.: ``002_especialista_analogico``).

A análise (REQF08) liga ``LeadProfile.matched_persona`` (rótulo PT) a esta tabela; o ICP
combina o baseline daqui com a conversão real calculada sobre os deals.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(60))  # PersonaType value
    name: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    desejos: Mapped[str | None] = mapped_column(Text, nullable=True)
    medos: Mapped[str | None] = mapped_column(Text, nullable=True)
    volume_leads: Mapped[str | None] = mapped_column(String(20), nullable=True)
    taxa_conversao: Mapped[str | None] = mapped_column(String(20), nullable=True)
    palavras_chave: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("code", name="uq_personas_code"),)
