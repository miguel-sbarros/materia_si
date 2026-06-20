"""Router de deals — feed do quadro (GET) e movimentação (PATCH). REQF02."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.deal import DealCard, DealMove
from app.services import deals as deals_service

router = APIRouter(tags=["deals"])


@router.get("/deals", response_model=list[DealCard])
def list_deals(
    course_id: int | None = None,
    cohort_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[DealCard]:
    return deals_service.list_deal_cards(db, course_id=course_id, cohort_id=cohort_id)


@router.patch("/deals/{deal_id}", response_model=DealCard)
def move_deal(deal_id: int, move: DealMove, db: Session = Depends(get_db)) -> DealCard:
    return deals_service.move_deal(db, deal_id, move)
