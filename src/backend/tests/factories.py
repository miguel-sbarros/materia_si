"""Fábricas de teste — montam entidades reais na sessão (mesmo padrão de test_models)."""

from decimal import Decimal

from app.core.constants import DealStage, DealStatus, UserRole
from app.models import Cohort, Course, Deal, Lead, User


def make_seller(session, email="ana.costa@mr.com", initials="AC"):
    user = User(name="Dra. Ana Costa", role=UserRole.SELLER, email=email, initials=initials)
    session.add(user)
    session.flush()
    return user


def make_course(session, name="Imersão", price="5900.00", n_cohorts=1):
    course = Course(name=name, price=Decimal(price))
    session.add(course)
    session.flush()
    cohorts = [
        Cohort(
            course_id=course.id, name=f"{name} T{i + 1}", capacity=30,
            price_per_slot=Decimal(price),
        )
        for i in range(n_cohorts)
    ]
    session.add_all(cohorts)
    session.flush()
    return course, cohorts


def make_lead(session, name="Lead Teste", **kwargs):
    lead = Lead(name=name, **kwargs)
    session.add(lead)
    session.flush()
    return lead


def make_deal(
    session, cohort, lead=None, stage=DealStage.NOVO, status=DealStatus.OPEN,
    lost_reason=None, assignee_id=None,
):
    if lead is None:
        lead = make_lead(session, assignee_id=assignee_id)
    deal = Deal(
        lead_id=lead.id, cohort_id=cohort.id, stage=stage, status=status,
        lost_reason=lost_reason,
    )
    session.add(deal)
    session.flush()
    return deal
