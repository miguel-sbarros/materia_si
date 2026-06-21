"""Router de leads — cadastro (POST), detalhe (GET) e análise sob demanda (P3). REQF01/REQF08."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import LeadProfileOut
from app.schemas.deal import DealCard, DealCreate
from app.schemas.lead import LeadCreate, LeadDetail, LeadSummary
from app.services import analysis as analysis_service
from app.services import deals as deals_service
from app.services import leads as leads_service

router = APIRouter(tags=["leads"])


@router.post("/leads", response_model=DealCard, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> DealCard:
    return leads_service.create_lead(db, payload)


@router.post(
    "/leads/{lead_id}/deals",
    response_model=DealCard,
    status_code=status.HTTP_201_CREATED,
)
def create_deal_for_lead(
    lead_id: int, payload: DealCreate, db: Session = Depends(get_db)
) -> DealCard:
    return deals_service.create_deal_for_lead(db, lead_id, payload)


@router.get("/leads", response_model=list[LeadSummary])
def search_leads(q: str = "", db: Session = Depends(get_db)) -> list[LeadSummary]:
    return leads_service.search_leads(db, q)


@router.get("/leads/{lead_id}", response_model=LeadDetail)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadDetail:
    return leads_service.get_lead(db, lead_id)


@router.post("/leads/{lead_id}/analyze", response_model=LeadProfileOut)
def analyze_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadProfileOut:
    """Reprocessa a conversa do lead → LeadProfile (síncrono). Upsert na mesma linha."""
    try:
        profile = analysis_service.analyze_lead(db, lead_id)
    except ValueError as exc:
        # "não encontrado" → 404; "sem conversa" → 422 (PT).
        if "não encontrado" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return LeadProfileOut.model_validate(profile)
