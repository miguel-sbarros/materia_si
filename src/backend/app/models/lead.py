"""Lead — identidade/contato. O funil NÃO vive aqui: a posição comercial está em ``deals``.

REQF01: nome, email, telefone, origem; dedupe por email (parcial — quando informado).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.deal import Deal
    from app.models.user import User


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    source: Mapped[str | None] = mapped_column(String(60), nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    # Chave natural de importação (P2). Único quando presente.
    external_user_id: Mapped[str | None] = mapped_column(
        String(120), unique=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    assignee: Mapped["User | None"] = relationship()
    deals: Mapped[list["Deal"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # REQF01: impedir duplicidade de email quando informado (índice único parcial).
        Index(
            "uq_leads_email_present",
            "email",
            unique=True,
            postgresql_where=text("email IS NOT NULL"),
        ),
    )
