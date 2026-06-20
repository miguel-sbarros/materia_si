"""Deal (lead → cohort) e seu histórico (deal_events).

O deal relaciona um lead a uma turma (cohort); o curso vem via ``deal.cohort.course``.
Um lead pode ter vários deals ao longo do tempo (turmas/cursos iguais ou diferentes).
REQF02: cada mudança de estágio gera um registro em ``deal_events``.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DealStage, DealStatus
from app.db.base import Base, enum_column

if TYPE_CHECKING:
    from app.models.course import Cohort
    from app.models.lead import Lead


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"))
    stage: Mapped[DealStage] = mapped_column(
        enum_column(DealStage, "deal_stage"),
        default=DealStage.NOVO,
        server_default=DealStage.NOVO.value,
    )
    status: Mapped[DealStatus] = mapped_column(
        enum_column(DealStatus, "deal_status"),
        default=DealStatus.OPEN,
        server_default=DealStatus.OPEN.value,
    )
    lost_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lead: Mapped["Lead"] = relationship(back_populates="deals")
    cohort: Mapped["Cohort"] = relationship(back_populates="deals")
    events: Mapped[list["DealEvent"]] = relationship(
        back_populates="deal", cascade="all, delete-orphan", order_by="DealEvent.id"
    )

    __table_args__ = (
        # Um deal por (lead, turma).
        UniqueConstraint("lead_id", "cohort_id", name="uq_deals_lead_cohort"),
        # lost_reason obrigatório quando status = lost.
        CheckConstraint(
            "status <> 'lost' OR lost_reason IS NOT NULL",
            name="ck_deals_lost_reason",
        ),
    )


class DealEvent(Base):
    __tablename__ = "deal_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("deals.id"))
    from_stage: Mapped[DealStage | None] = mapped_column(
        enum_column(DealStage, "deal_event_from_stage"), nullable=True
    )
    to_stage: Mapped[DealStage | None] = mapped_column(
        enum_column(DealStage, "deal_event_to_stage"), nullable=True
    )
    from_status: Mapped[DealStatus | None] = mapped_column(
        enum_column(DealStatus, "deal_event_from_status"), nullable=True
    )
    to_status: Mapped[DealStatus | None] = mapped_column(
        enum_column(DealStatus, "deal_event_to_status"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    deal: Mapped["Deal"] = relationship(back_populates="events")
