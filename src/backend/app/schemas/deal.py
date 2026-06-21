"""Schemas de deal — card do quadro (DealCard), resumo (DealBrief) e movimento (DealMove).

``column`` é o conceito da UI (5 colunas do Kanban); ``stage``/``status`` são os campos
de domínio. O mapeamento coluna↔(stage,status) vive em ``app/services/deals.py``.
"""

from decimal import Decimal

from pydantic import BaseModel


class DealCard(BaseModel):
    id: int  # id do deal — alvo do drag/PATCH
    leadId: int
    name: str
    course: str
    cohortId: int
    cohortName: str
    source: str | None = None
    column: str
    stage: str
    status: str
    value: Decimal | None = None
    assignee: str | None = None
    updatedAt: str | None = None


class DealBrief(BaseModel):
    id: int
    course: str
    cohortName: str
    column: str
    stage: str
    status: str


class DealMove(BaseModel):
    column: str
    lost_reason: str | None = None


class DealCreate(BaseModel):
    cohort_id: int
    stage: str  # estágio aberto: Novo | Contatado | Negociando
