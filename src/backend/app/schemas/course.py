"""Schemas de curso/turma — dados de referência (filtro do quadro + seletor de turma).

Inclui os schemas de escrita (create/update) que tornam cursos e turmas editáveis pela
UI (criar + editar; sem delete). Os campos extras de leitura prefilam os modais de edição.
"""

from datetime import date
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
    start_date: date | None = None
    end_date: date | None = None
    capacity: int | None = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal | None = None
    description: str | None = None
    modality: str
    duration: str | None = None
    cohorts: list[CohortOut] = []


class CourseCreate(BaseModel):
    name: str
    description: str | None = None
    modality: str = "Presencial"
    price: Decimal | None = None
    duration: str | None = None


class CourseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    modality: str | None = None
    price: Decimal | None = None
    duration: str | None = None


class CohortCreate(BaseModel):
    name: str
    start_date: date | None = None
    end_date: date | None = None
    capacity: int | None = None
    price_per_slot: Decimal | None = None
    status: CohortStatus = CohortStatus.OPEN


class CohortUpdate(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    capacity: int | None = None
    price_per_slot: Decimal | None = None
    status: CohortStatus | None = None
