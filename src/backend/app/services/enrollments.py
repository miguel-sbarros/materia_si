"""Matrícula (REQF06) — fonte da verdade de quem está na turma, integrada ao funil.

``enroll_lead`` cria a ``Enrollment`` E transiciona (ou cria) o ``deal(lead, cohort)`` para
``won`` (coluna "Matriculado"), gravando um ``DealEvent`` e vinculando ``enrollment.deal_id``.
Vagas = ``capacity − matrículas ativas`` (bloqueia turma lotada). Cancelar libera a vaga e
reverte o deal vinculado para ``open``/``Negociando``.

Regras viram ``ValueError`` com mensagem PT — o router fino traduz para 404/409/422.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.constants import DealStage, DealStatus, EnrollmentStatus
from app.models import Cohort, Deal, DealEvent, Enrollment, Lead
from app.schemas.enrollment import CohortEnrollmentsOut, EnrollmentOut


def _to_out(enrollment: Enrollment) -> EnrollmentOut:
    return EnrollmentOut(
        id=enrollment.id,
        leadId=enrollment.lead_id,
        leadName=enrollment.lead.name,
        cohortId=enrollment.cohort_id,
        dealId=enrollment.deal_id,
        status=enrollment.status,
        source=enrollment.source,
        enrolledAt=enrollment.created_at,
    )


def _active_count(db: Session, cohort_id: int) -> int:
    return len(
        db.scalars(
            select(Enrollment.id).where(
                Enrollment.cohort_id == cohort_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
        ).all()
    )


def _win_deal(db: Session, lead: Lead, cohort_id: int) -> Deal:
    """Transiciona o deal aberto (lead, cohort) para won, ou cria um deal won se não existir.

    Grava um ``DealEvent`` da transição. Reaproveita a semântica de ``deals.move_deal``
    (won mantém o stage) e de ``deals.create_closed_deal`` (deal já fechado).
    """
    deal = db.scalar(
        select(Deal).where(Deal.lead_id == lead.id, Deal.cohort_id == cohort_id)
    )
    if deal is None:
        # Sem deal: cria um já fechado (won), com histórico (reuso de create_closed_deal).
        from app.services.deals import create_closed_deal

        return create_closed_deal(
            db, lead_id=lead.id, cohort_id=cohort_id, status=DealStatus.WON
        )

    if deal.status != DealStatus.WON:
        from_stage, from_status = deal.stage, deal.status
        deal.status = DealStatus.WON
        deal.lost_reason = None
        db.add(
            DealEvent(
                deal_id=deal.id,
                from_stage=from_stage,
                to_stage=deal.stage,
                from_status=from_status,
                to_status=DealStatus.WON,
                reason="Matriculado",
                user_id=lead.assignee_id,
            )
        )
    return deal


def enroll_lead(
    db: Session, cohort_id: int, lead_id: int, source: str | None = None
) -> EnrollmentOut:
    cohort = db.get(Cohort, cohort_id)
    if cohort is None:
        raise ValueError("Turma não encontrada")
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead não encontrado")

    if cohort.capacity is not None and _active_count(db, cohort_id) >= cohort.capacity:
        raise ValueError("Turma lotada")

    enrollment = Enrollment(
        lead_id=lead_id, cohort_id=cohort_id, status=EnrollmentStatus.ACTIVE, source=source
    )
    db.add(enrollment)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Lead já matriculado nesta turma") from exc

    deal = _win_deal(db, lead, cohort_id)
    db.flush()
    enrollment.deal_id = deal.id
    db.commit()
    db.refresh(enrollment)
    return _to_out(enrollment)


def cancel_enrollment(db: Session, cohort_id: int, lead_id: int) -> None:
    enrollment = db.scalar(
        select(Enrollment).where(
            Enrollment.cohort_id == cohort_id,
            Enrollment.lead_id == lead_id,
            Enrollment.status == EnrollmentStatus.ACTIVE,
        )
    )
    if enrollment is None:
        raise ValueError("Matrícula não encontrada")

    enrollment.status = EnrollmentStatus.CANCELLED

    # Reverte o deal vinculado para open/Negociando (libera o lead no funil).
    if enrollment.deal_id is not None:
        deal = db.get(Deal, enrollment.deal_id)
        if deal is not None and deal.status != DealStatus.OPEN:
            from_stage, from_status = deal.stage, deal.status
            deal.status = DealStatus.OPEN
            deal.stage = DealStage.NEGOCIANDO
            deal.lost_reason = None
            db.add(
                DealEvent(
                    deal_id=deal.id,
                    from_stage=from_stage,
                    to_stage=DealStage.NEGOCIANDO,
                    from_status=from_status,
                    to_status=DealStatus.OPEN,
                    reason="Matrícula cancelada",
                    user_id=deal.lead.assignee_id,
                )
            )
    db.commit()


def cohort_enrollments(db: Session, cohort_id: int) -> CohortEnrollmentsOut:
    cohort = db.get(Cohort, cohort_id)
    if cohort is None:
        raise ValueError("Turma não encontrada")

    actives = (
        db.scalars(
            select(Enrollment)
            .where(
                Enrollment.cohort_id == cohort_id,
                Enrollment.status == EnrollmentStatus.ACTIVE,
            )
            .options(joinedload(Enrollment.lead))
            .order_by(Enrollment.id)
        )
        .unique()
        .all()
    )
    enrolled = len(actives)
    available = cohort.capacity - enrolled if cohort.capacity is not None else None
    return CohortEnrollmentsOut(
        capacity=cohort.capacity,
        enrolled=enrolled,
        available=available,
        enrollments=[_to_out(e) for e in actives],
    )
