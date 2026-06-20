"""Schemas de lead — criação (LeadCreate) e detalhe com deals (LeadDetail)."""

from pydantic import BaseModel

from app.schemas.deal import DealBrief


class LeadCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    cohort_id: int


class LeadDetail(BaseModel):
    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    deals: list[DealBrief] = []
