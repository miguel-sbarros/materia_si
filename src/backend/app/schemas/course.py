"""Schemas de curso/turma — dados de referência (filtro do quadro + seletor de turma)."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.core.constants import CohortStatus


class CohortOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    name: str
    status: CohortStatus
    price_per_slot: Decimal | None = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal | None = None
    cohorts: list[CohortOut] = []
