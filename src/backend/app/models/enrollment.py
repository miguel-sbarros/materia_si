"""Enrollment — matrícula de um lead numa turma (REQF06).

A matrícula é a fonte da verdade de quem está na turma. Matricular cria a ``Enrollment``
E transiciona o ``deal(lead, cohort)`` para ``won`` (coluna "Matriculado"), criando o deal
se não existir; ``enrollment.deal_id`` materializa esse vínculo. Vagas disponíveis =
``capacity − matrículas ativas``. ``UNIQUE(lead_id, cohort_id)`` impede duplicidade.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EnrollmentStatus
from app.db.base import Base, enum_column

if TYPE_CHECKING:
    from app.models.course import Cohort
    from app.models.deal import Deal
    from app.models.lead import Lead


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"))
    # Deal que materializa a matrícula (won). Nullable até ser vinculado.
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("deals.id"), nullable=True)
    status: Mapped[EnrollmentStatus] = mapped_column(
        enum_column(EnrollmentStatus, "enrollment_status"),
        default=EnrollmentStatus.ACTIVE,
        server_default=EnrollmentStatus.ACTIVE.value,
    )
    source: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lead: Mapped["Lead"] = relationship(back_populates="enrollments")
    cohort: Mapped["Cohort"] = relationship(back_populates="enrollments")
    deal: Mapped["Deal | None"] = relationship()

    __table_args__ = (
        UniqueConstraint("lead_id", "cohort_id", name="uq_enrollments_lead_cohort"),
    )
