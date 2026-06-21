"""CopilotSession / CopilotMessage — conversas do copiloto (P4b).

Uma sessão é uma thread do copiloto; ``lead_id`` é fixado na criação e é nullable
(chats só de base de conhecimento). **Estas mensagens são distintas das mensagens
lead/vendedor** (``app.models.conversation.Message``): aqui guardamos o turno do
vendedor com o copiloto (pergunta) e a resposta do agente (texto ou conselho).

``kind='advice'`` guarda o ``SellerAdvice`` em ``advice`` (JSONB); ``kind='text'``
guarda texto livre em ``content``. ``UNIQUE(session_id, sequence)`` ordena a thread.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class CopilotSession(Base):
    __tablename__ = "copilot_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lead: Mapped["Lead | None"] = relationship()
    messages: Mapped[list["CopilotMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="CopilotMessage.sequence",
    )


class CopilotMessage(Base):
    __tablename__ = "copilot_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("copilot_sessions.id"))
    role: Mapped[str] = mapped_column(String(20))  # 'user' | 'assistant'
    kind: Mapped[str] = mapped_column(String(20))  # 'text' | 'advice'
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    advice: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["CopilotSession"] = relationship(back_populates="messages")

    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_copilot_messages_session_seq"),
    )
