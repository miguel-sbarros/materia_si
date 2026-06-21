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
from app.schemas.analysis import LeadProfileOut
from app.schemas.deal import DealBrief, DealCard
from app.schemas.lead import AttributeOut, LeadCreate, LeadDetail, LeadSummary
from app.services.conversations import get_lead_conversation
from app.services.deals import _deal_value, card_column, to_card


def _current_seller(db: Session) -> User | None:
    return db.scalars(
        select(User).where(User.role == UserRole.SELLER).order_by(User.id).limit(1)
    ).first()


def _initials(name: str) -> str:
    """Iniciais do nome (primeira letra do primeiro e do último termo), maiúsculas."""
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


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


def _format_money(value) -> str:
    """Formata Decimal como ticket em R$ (pt-BR simplificado). None → '—'."""
    if value is None:
        return "—"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _attributes(lead: Lead) -> list[AttributeOut]:
    """Grade de atributos da página do lead — derivada de leads + deal primário (null-safe)."""
    primary = lead.deals[0] if lead.deals else None
    attrs = [
        AttributeOut(label="Curso", value=primary.cohort.course.name if primary else "—"),
        AttributeOut(label="Estágio", value=card_column(primary) if primary else "—"),
        AttributeOut(
            label="Ticket", value=_format_money(_deal_value(primary)) if primary else "—"
        ),
        AttributeOut(label="Origem", value=lead.source or "—"),
        AttributeOut(label="Telefone", value=lead.phone or "—"),
        AttributeOut(label="Email", value=lead.email or "—"),
        AttributeOut(
            label="Criado em",
            value=lead.created_at.strftime("%d/%m/%Y") if lead.created_at else "—",
        ),
    ]
    return attrs


def get_lead(db: Session, lead_id: int) -> LeadDetail:
    lead = (
        db.scalars(
            select(Lead)
            .where(Lead.id == lead_id)
            .options(
                joinedload(Lead.deals).joinedload(Deal.cohort).joinedload(Cohort.course),
                joinedload(Lead.profile),
            )
        )
        .unique()
        .first()
    )
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    conversation = get_lead_conversation(db, lead_id)["messages"]
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
        conversation=conversation,
        attributes=_attributes(lead),
        # Perfil de IA (P3) — objeto completo quando a análise já rodou; senão None.
        profile=LeadProfileOut.model_validate(lead.profile) if lead.profile else None,
    )


def search_leads(db: Session, q: str, limit: int = 8) -> list[LeadSummary]:
    """Busca leads por nome (ILIKE %q%), cap em ``limit``. q vazio/branco → []."""
    term = (q or "").strip()
    if not term:
        return []
    leads = (
        db.scalars(
            select(Lead)
            .where(Lead.name.ilike(f"%{term}%"))
            .options(joinedload(Lead.deals).joinedload(Deal.cohort).joinedload(Cohort.course))
            .order_by(Lead.name)
            .limit(limit)
        )
        .unique()
        .all()
    )
    summaries = []
    for lead in leads:
        primary = lead.deals[0] if lead.deals else None
        summaries.append(
            LeadSummary(
                id=lead.id,
                name=lead.name,
                initials=_initials(lead.name),
                persona=None,
                stage=card_column(primary) if primary else None,
            )
        )
    return summaries
