"""Router de leads — cadastro (POST) e detalhe (GET). REQF01."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.deal import DealCard
from app.schemas.lead import LeadCreate, LeadDetail
from app.services import leads as leads_service

router = APIRouter(tags=["leads"])


@router.post("/leads", response_model=DealCard, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> DealCard:
    return leads_service.create_lead(db, payload)


@router.get("/leads/{lead_id}", response_model=LeadDetail)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadDetail:
    return leads_service.get_lead(db, lead_id)
