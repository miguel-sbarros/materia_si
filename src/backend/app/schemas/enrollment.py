"""Schemas de matrícula (REQF06). ``*Out`` em camelCase no fio (consumo do frontend)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.constants import EnrollmentStatus


class EnrollmentCreate(BaseModel):
    lead_id: int
    source: str | None = None


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    leadId: int
    leadName: str
    cohortId: int
    dealId: int | None = None
    status: EnrollmentStatus
    source: str | None = None
    enrolledAt: datetime | None = None


class CohortEnrollmentsOut(BaseModel):
    """Resumo de vagas da turma + matrículas ativas (conta só ``active``)."""

    capacity: int | None = None
    enrolled: int
    available: int | None = None
    enrollments: list[EnrollmentOut] = []
