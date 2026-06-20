"""Contrato do schema core+deal (TDD). Cobre os critérios da spec p0-foundations."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.constants import CohortStatus, DealStage, DealStatus, UserRole
from app.models import Cohort, Course, Deal, DealEvent, Lead, User


def _course_with_cohorts(session, n=1, name="Imersão"):
    course = Course(name=name, price=Decimal("5900.00"))
    session.add(course)
    session.flush()
    cohorts = [Cohort(course_id=course.id, name=f"{name} T{i + 1}", capacity=30) for i in range(n)]
    session.add_all(cohorts)
    session.flush()
    return course, cohorts


def _lead(session, **kwargs):
    lead = Lead(name=kwargs.pop("name", "Lead Teste"), **kwargs)
    session.add(lead)
    session.flush()
    return lead


def test_create_core_entities(db_session):
    user = User(name="Ana Costa", role=UserRole.SELLER, email="ana@mr.com", initials="AC")
    db_session.add(user)
    db_session.flush()
    _course, [cohort] = _course_with_cohorts(db_session)
    lead = _lead(db_session, name="Dr. Carlos", email="carlos@x.com", source="Instagram",
                 assignee_id=user.id)

    assert cohort.status == CohortStatus.OPEN  # default
    fetched = db_session.scalar(select(User).where(User.email == "ana@mr.com"))
    assert fetched.role == UserRole.SELLER
    assert lead.assignee.id == user.id


def test_deal_unique_lead_cohort(db_session):
    _course, [cohort] = _course_with_cohorts(db_session)
    lead = _lead(db_session, name="Repetido")
    db_session.add(Deal(lead_id=lead.id, cohort_id=cohort.id))
    db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(Deal(lead_id=lead.id, cohort_id=cohort.id))


def test_lead_multiple_deals(db_session):
    """Um lead, duas turmas do MESMO curso → dois deals em estágios diferentes."""
    _course, cohorts = _course_with_cohorts(db_session, n=2, name="Master 3.0")
    lead = _lead(db_session, name="Dra. Helena")
    d1 = Deal(lead_id=lead.id, cohort_id=cohorts[0].id, stage=DealStage.NEGOCIANDO)
    d2 = Deal(lead_id=lead.id, cohort_id=cohorts[1].id, stage=DealStage.NOVO)
    db_session.add_all([d1, d2])
    db_session.flush()
    db_session.refresh(lead)

    assert len(lead.deals) == 2
    assert {d.stage for d in lead.deals} == {DealStage.NEGOCIANDO, DealStage.NOVO}
    # Curso alcançado VIA cohort (deal não tem course_id).
    assert d1.cohort.course.name == "Master 3.0"
    assert d1.cohort.course_id == d2.cohort.course_id


def test_lost_requires_reason(db_session):
    _course, [cohort] = _course_with_cohorts(db_session)
    lead = _lead(db_session, name="Dr. Thiago")

    # Negativo: status=lost sem lost_reason viola o CHECK.
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(Deal(lead_id=lead.id, cohort_id=cohort.id, status=DealStatus.LOST))

    # Positivo: com motivo, persiste.
    good = Deal(lead_id=lead.id, cohort_id=cohort.id, status=DealStatus.LOST,
                lost_reason="Sem orçamento neste momento")
    db_session.add(good)
    db_session.flush()
    assert good.id is not None


def test_deal_events_history(db_session):
    """REQF02: cada mudança gera registro; histórico consultável em ordem cronológica."""
    _course, [cohort] = _course_with_cohorts(db_session)
    lead = _lead(db_session, name="Lead Histórico")
    deal = Deal(lead_id=lead.id, cohort_id=cohort.id, stage=DealStage.NOVO)
    db_session.add(deal)
    db_session.flush()

    db_session.add_all([
        DealEvent(deal_id=deal.id, from_stage=DealStage.NOVO, to_stage=DealStage.CONTATADO,
                  reason="Primeiro contato"),
        DealEvent(deal_id=deal.id, from_stage=DealStage.CONTATADO, to_stage=DealStage.NEGOCIANDO),
    ])
    db_session.flush()
    db_session.refresh(deal)

    assert [ev.to_stage for ev in deal.events] == [DealStage.CONTATADO, DealStage.NEGOCIANDO]


def test_lead_email_dedupe(db_session):
    """REQF01: emails não-nulos iguais colidem; múltiplos nulos são permitidos."""
    db_session.add(Lead(name="A", email="dup@x.com"))
    db_session.flush()

    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(Lead(name="B", email="dup@x.com"))

    # Dois leads sem email coexistem (índice único é parcial).
    db_session.add_all([Lead(name="C", email=None), Lead(name="D", email=None)])
    db_session.flush()
