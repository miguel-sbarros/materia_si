"""Curso e Turma (cohort). Um curso tem N turmas; o deal aponta para a turma."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CohortStatus
from app.db.base import Base, enum_column

if TYPE_CHECKING:
    from app.models.deal import Deal


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    modality: Mapped[str] = mapped_column(
        String(40), default="Presencial", server_default="Presencial"
    )
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(80), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    cohorts: Mapped[list["Cohort"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )


class Cohort(Base):
    __tablename__ = "cohorts"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    name: Mapped[str] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_per_slot: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[CohortStatus] = mapped_column(
        enum_column(CohortStatus, "cohort_status"),
        default=CohortStatus.OPEN,
        server_default=CohortStatus.OPEN.value,
    )

    course: Mapped["Course"] = relationship(back_populates="cohorts")
    deals: Mapped[list["Deal"]] = relationship(back_populates="cohort")
