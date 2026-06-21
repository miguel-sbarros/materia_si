"""Lógica de deals — feed do quadro e movimentação (REQF02).

Mapeamento coluna↔(stage, status):
- ``Novo|Contatado|Negociando`` → stage = coluna, status = open.
- ``Matriculado`` → status = won (mantém stage).
- ``Perdido`` → status = lost (exige lost_reason; mantém stage).
Toda movimentação grava um ``DealEvent`` (histórico).
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import DealStage, DealStatus
from app.models import Cohort, Deal, DealEvent, Lead
from app.schemas.deal import DealCard, DealCreate, DealMove

MATRICULADO = "Matriculado"
PERDIDO = "Perdido"
OPEN_COLUMNS = {s.value for s in DealStage}
BOARD_COLUMNS = [*(s.value for s in DealStage), MATRICULADO, PERDIDO]


def card_column(deal: Deal) -> str:
    """Coluna exibida no quadro: won→Matriculado, lost→Perdido, senão o stage."""
    if deal.status == DealStatus.WON:
        return MATRICULADO
    if deal.status == DealStatus.LOST:
        return PERDIDO
    return deal.stage.value


def _deal_value(deal: Deal) -> Decimal | None:
    cohort = deal.cohort
    if cohort.price_per_slot is not None:
        return cohort.price_per_slot
    return cohort.course.price


def to_card(deal: Deal) -> DealCard:
    lead = deal.lead
    cohort = deal.cohort
    return DealCard(
        id=deal.id,
        leadId=lead.id,
        name=lead.name,
        course=cohort.course.name,
        cohortId=cohort.id,
        cohortName=cohort.name,
        source=lead.source,
        column=card_column(deal),
        stage=deal.stage.value,
        status=deal.status.value,
        value=_deal_value(deal),
        assignee=lead.assignee.initials if lead.assignee else None,
        updatedAt=deal.updated_at.isoformat() if deal.updated_at else None,
    )


def list_deal_cards(
    db: Session, course_id: int | None = None, cohort_id: int | None = None
) -> list[DealCard]:
    stmt = (
        select(Deal)
        .options(
            joinedload(Deal.cohort).joinedload(Cohort.course),
            joinedload(Deal.lead).joinedload(Lead.assignee),
        )
        .order_by(Deal.id)
    )
    if cohort_id is not None:
        stmt = stmt.where(Deal.cohort_id == cohort_id)
    if course_id is not None:
        stmt = stmt.where(
            Deal.cohort_id.in_(select(Cohort.id).where(Cohort.course_id == course_id))
        )
    return [to_card(d) for d in db.scalars(stmt).all()]


def move_deal(db: Session, deal_id: int, move: DealMove) -> DealCard:
    deal = db.get(Deal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal não encontrado")

    column = move.column
    if column not in BOARD_COLUMNS:
        raise HTTPException(status_code=422, detail=f"Coluna inválida: {column}")

    from_stage, from_status = deal.stage, deal.status

    if column in OPEN_COLUMNS:
        deal.stage = DealStage(column)
        deal.status = DealStatus.OPEN
        deal.lost_reason = None
    elif column == MATRICULADO:
        deal.status = DealStatus.WON
        deal.lost_reason = None
    else:  # PERDIDO
        if not (move.lost_reason and move.lost_reason.strip()):
            raise HTTPException(
                status_code=422, detail="lost_reason é obrigatório para mover a Perdido"
            )
        deal.status = DealStatus.LOST
        deal.lost_reason = move.lost_reason.strip()

    db.add(
        DealEvent(
            deal_id=deal.id,
            from_stage=from_stage,
            to_stage=deal.stage,
            from_status=from_status,
            to_status=deal.status,
            reason=deal.lost_reason if deal.status == DealStatus.LOST else None,
            user_id=deal.lead.assignee_id,
        )
    )
    db.commit()
    db.refresh(deal)
    return to_card(deal)


def create_deal_for_lead(db: Session, lead_id: int, payload: DealCreate) -> DealCard:
    """Cria um deal para um lead existente numa turma + estágio aberto escolhidos.

    Usado quando um import cria um novo lead e o usuário o posiciona no Funil.
    Apenas estágios abertos (Novo/Contatado/Negociando); registra o DealEvent inicial.
    """
    if payload.stage not in OPEN_COLUMNS:
        raise HTTPException(
            status_code=422,
            detail=f"Estágio inválido: {payload.stage}. Use Novo, Contatado ou Negociando.",
        )

    lead = db.get(Lead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")

    cohort = db.get(Cohort, payload.cohort_id)
    if cohort is None:
        raise HTTPException(status_code=422, detail="Turma não encontrada")

    existing = db.scalar(
        select(Deal).where(Deal.lead_id == lead_id, Deal.cohort_id == cohort.id)
    )
    if existing is not None:
        raise HTTPException(
            status_code=409, detail="Já existe um deal deste lead nesta turma"
        )

    stage = DealStage(payload.stage)
    deal = Deal(
        lead_id=lead_id, cohort_id=cohort.id, stage=stage, status=DealStatus.OPEN
    )
    db.add(deal)
    db.flush()

    db.add(
        DealEvent(
            deal_id=deal.id,
            to_stage=stage,
            to_status=DealStatus.OPEN,
            reason="Deal criado via import",
            user_id=lead.assignee_id,
        )
    )
    db.commit()
    db.refresh(deal)
    return to_card(deal)


def create_closed_deal(
    db: Session,
    *,
    lead_id: int,
    cohort_id: int,
    status: DealStatus,
    lost_reason: str | None = None,
) -> Deal:
    """Cria (idempotente) um deal JÁ FECHADO (won/lost) — cold-start de dados históricos.

    A turma já aconteceu, então o deal nasce fechado: ``won`` (Matriculado) ou ``lost``
    (Perdido, exige ``lost_reason``). Stage = Negociando (chegou a negociar antes de fechar).
    Registra o histórico (criação Novo/open → fechamento). Se já existir um deal para
    ``(lead, cohort)``, devolve o existente sem duplicar (``UNIQUE(lead_id, cohort_id)``).
    """
    if status not in (DealStatus.WON, DealStatus.LOST):
        raise ValueError("create_closed_deal aceita apenas won ou lost")
    if status == DealStatus.LOST and not (lost_reason and lost_reason.strip()):
        raise ValueError("lost_reason é obrigatório para um deal perdido")

    existing = db.scalar(
        select(Deal).where(Deal.lead_id == lead_id, Deal.cohort_id == cohort_id)
    )
    if existing is not None:
        return existing

    lead = db.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead não encontrado")

    reason = lost_reason.strip() if status == DealStatus.LOST else None
    deal = Deal(
        lead_id=lead_id,
        cohort_id=cohort_id,
        stage=DealStage.NEGOCIANDO,
        status=status,
        lost_reason=reason,
    )
    db.add(deal)
    db.flush()

    uid = lead.assignee_id
    db.add(
        DealEvent(
            deal_id=deal.id,
            to_stage=DealStage.NOVO,
            to_status=DealStatus.OPEN,
            reason="Lead importado (cold start)",
            user_id=uid,
        )
    )
    db.add(
        DealEvent(
            deal_id=deal.id,
            from_stage=DealStage.NOVO,
            to_stage=DealStage.NEGOCIANDO,
            from_status=DealStatus.OPEN,
            to_status=status,
            reason=reason if status == DealStatus.LOST else "Matriculado",
            user_id=uid,
        )
    )
    db.commit()
    db.refresh(deal)
    return deal
