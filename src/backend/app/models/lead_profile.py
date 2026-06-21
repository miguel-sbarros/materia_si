"""LeadProfile — artefato de análise de conversa por lead (P3, REQF08).

1:1 com ``leads`` (``UNIQUE(lead_id)``). Guarda entidades extraídas + persona + estágio
SPIN + score/summary + métricas deterministas da conversa. Recalculável a cada
re-análise (upsert na mesma linha). Listas/dicts persistem como ``JSONB``.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class LeadProfile(Base):
    __tablename__ = "lead_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))

    # Entidades (porte de ExtractedEntities).
    especialidade: Mapped[str | None] = mapped_column(String(160), nullable=True)
    experiencia: Mapped[str | None] = mapped_column(String(160), nullable=True)
    cidade_estado: Mapped[str | None] = mapped_column(String(160), nullable=True)
    course_interest: Mapped[str | None] = mapped_column(String(160), nullable=True)
    dores_verbalizadas: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    desejos_expressos: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    objecoes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # comentarios engloba hardware/software, termos técnicos e marcadores de contexto.
    comentarios: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Persona (de LeadAssessment). matched_persona = rótulo de exibição PT.
    matched_persona: Mapped[str | None] = mapped_column(String(60), nullable=True)
    persona_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    persona_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Diálogo.
    current_spin_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    lead_score: Mapped[int | None] = mapped_column(nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Métricas da conversa (deterministas + SPIN de abandono).
    median_seller_latency_seconds: Mapped[int | None] = mapped_column(nullable=True)
    median_lead_latency_seconds: Mapped[int | None] = mapped_column(nullable=True)
    first_response_latency_seconds: Mapped[int | None] = mapped_column(nullable=True)
    last_message_sent: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_abandoned: Mapped[bool] = mapped_column(
        Boolean, server_default=sa_text("false")
    )
    abandon_spin_stage: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Metadados.
    model_used: Mapped[str | None] = mapped_column(String(60), nullable=True)
    raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lead: Mapped["Lead"] = relationship(back_populates="profile")

    __table_args__ = (
        # 1:1 com lead.
        UniqueConstraint("lead_id", name="uq_lead_profiles_lead"),
    )
