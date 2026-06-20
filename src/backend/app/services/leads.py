"""Lógica de leads — cadastro (REQF01) e detalhe.

``create_lead`` cria o lead + um deal inicial ``Novo``/``open`` na turma escolhida +
o ``DealEvent`` inicial. Dedupe de email (409). Auth diferida: o lead é atribuído ao
seller seedado (usuário corrente implícito).
"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import DealStage, DealStatus, UserRole
from app.models import Cohort, Deal, DealEvent, Lead, User
from app.schemas.deal import DealBrief, DealCard
from app.schemas.lead import LeadCreate, LeadDetail
from app.services.deals import card_column, to_card


def _current_seller(db: Session) -> User | None:
    return db.scalars(
        select(User).where(User.role == UserRole.SELLER).order_by(User.id).limit(1)
    ).first()


def create_lead(db: Session, payload: LeadCreate) -> DealCard:
    if payload.email:
        if db.scalar(select(Lead).where(Lead.email == payload.email)) is not None:
            raise HTTPException(status_code=409, detail="Já existe um lead com este email")

    cohort = db.get(Cohort, payload.cohort_id)
    if cohort is None:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    seller = _current_seller(db)
    seller_id = seller.id if seller else None

    lead = Lead(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        source=payload.source,
        assignee_id=seller_id,
    )
    db.add(lead)
    db.flush()

    deal = Deal(
        lead_id=lead.id, cohort_id=cohort.id, stage=DealStage.NOVO, status=DealStatus.OPEN
    )
    db.add(deal)
    db.flush()

    db.add(
        DealEvent(
            deal_id=deal.id,
            to_stage=DealStage.NOVO,
            to_status=DealStatus.OPEN,
            reason="Lead criado",
            user_id=seller_id,
        )
    )
    db.commit()
    db.refresh(deal)
    return to_card(deal)


def get_lead(db: Session, lead_id: int) -> LeadDetail:
    lead = (
        db.scalars(
            select(Lead)
            .where(Lead.id == lead_id)
            .options(joinedload(Lead.deals).joinedload(Deal.cohort).joinedload(Cohort.course))
        )
        .unique()
        .first()
    )
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return LeadDetail(
        id=lead.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        source=lead.source,
        deals=[
            DealBrief(
                id=d.id,
                course=d.cohort.course.name,
                cohortName=d.cohort.name,
                column=card_column(d),
                stage=d.stage.value,
                status=d.status.value,
            )
            for d in lead.deals
        ],
    )
