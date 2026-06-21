"""Schemas de lead — criação (LeadCreate), detalhe (LeadDetail) e busca (LeadSummary)."""

from pydantic import BaseModel

from app.schemas.analysis import LeadProfileOut
from app.schemas.conversation import MessageOut
from app.schemas.deal import DealBrief


class LeadCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    cohort_id: int


class LeadUpdate(BaseModel):
    """Edição dos dados de contato do lead (parcial). Campos de IA/deals não entram aqui."""

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    source: str | None = None


class AttributeOut(BaseModel):
    """Par rótulo/valor da grade de atributos da página do lead (PT, null-safe)."""

    label: str
    value: str


class LeadDetail(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    deals: list[DealBrief] = []
    conversation: list[MessageOut] = []
    attributes: list[AttributeOut] = []
    # Perfil de IA (P3) — objeto completo (persona, dores, desejos, SPIN, score, métricas).
    # None até a análise rodar (REQF08). Mesmo shape de POST /leads/{id}/analyze.
    profile: LeadProfileOut | None = None


class LeadSummary(BaseModel):
    """Resultado da busca da Topbar — iniciais derivadas do nome; persona placeholder."""

    id: int
    name: str
    initials: str
    persona: str | None = None
    stage: str | None = None
