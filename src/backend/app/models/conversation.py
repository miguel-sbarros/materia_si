"""Conversation e Message — histórico de WhatsApp por lead (P2, REQF03).

Uma conversa pertence a um lead e agrega as mensagens em ordem (``sequence``).
``sent=True`` ⇔ vendedor; ``sent=False`` ⇔ lead. ``UNIQUE(conversation_id, sequence)``
torna o re-import idempotente.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.lead import Lead


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    channel: Mapped[str] = mapped_column(String(40), server_default="WhatsApp")
    source: Mapped[str | None] = mapped_column(String(60), nullable=True)
    external_user_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unread: Mapped[bool] = mapped_column(Boolean, server_default=sa_text("false"))
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    lead: Mapped["Lead"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.sequence",
    )

    __table_args__ = (
        # Uma conversa por (lead, canal).
        UniqueConstraint("lead_id", "channel", name="uq_conversations_lead_channel"),
        Index("ix_conversations_external_user_id", "external_user_id"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    text: Mapped[str] = mapped_column(Text)
    # True ⇔ vendedor; False ⇔ lead.
    sent: Mapped[bool] = mapped_column(Boolean)
    channel: Mapped[str] = mapped_column(String(40), server_default="WhatsApp")
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sequence: Mapped[int] = mapped_column()
    read: Mapped[bool] = mapped_column(Boolean, server_default=sa_text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    __table_args__ = (
        # Idempotência de import: sequência única por conversa.
        UniqueConstraint(
            "conversation_id", "sequence", name="uq_messages_conversation_sequence"
        ),
    )
