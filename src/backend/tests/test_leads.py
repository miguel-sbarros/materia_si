"""POST /leads (cria lead + deal) e GET /leads/{id}. Critérios 7–9 (REQF01)."""

from sqlalchemy import select

from app.core.constants import DealStage, DealStatus
from app.models import Deal, DealEvent, Lead
from tests.factories import make_course, make_lead, make_seller


def test_create_lead_creates_deal(api_client, db_session):
    seller = make_seller(db_session)
    _course, [cohort] = make_course(db_session)

    resp = api_client.post(
        "/leads",
        json={
            "name": "Dr. Novo", "email": "novo@x.com", "phone": "(11) 90000-0000",
            "source": "Instagram", "cohort_id": cohort.id,
        },
    )
    assert resp.status_code == 201
    card = resp.json()
    assert card["column"] == "Novo"
    assert card["name"] == "Dr. Novo"
    assert card["cohortId"] == cohort.id
    assert card["assignee"] == seller.initials

    lead = db_session.scalar(select(Lead).where(Lead.email == "novo@x.com"))
    assert lead is not None
    assert lead.assignee_id == seller.id
    deal = db_session.scalar(select(Deal).where(Deal.lead_id == lead.id))
    assert deal.stage == DealStage.NOVO
    assert deal.status == DealStatus.OPEN
    events = db_session.scalars(select(DealEvent).where(DealEvent.deal_id == deal.id)).all()
    assert len(events) == 1
    assert events[0].to_stage == DealStage.NOVO


def test_create_lead_duplicate_email_409(api_client, db_session):
    make_seller(db_session)
    _course, [cohort] = make_course(db_session)
    make_lead(db_session, name="Existente", email="dup@x.com")

    resp = api_client.post(
        "/leads", json={"name": "Outro", "email": "dup@x.com", "cohort_id": cohort.id}
    )
    assert resp.status_code == 409


def test_get_lead_detail(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Imersão")
    lead = make_lead(db_session, name="Dra. Detalhe", email="det@x.com")
    db_session.add(Deal(lead_id=lead.id, cohort_id=cohort.id, stage=DealStage.CONTATADO))
    db_session.flush()

    resp = api_client.get(f"/leads/{lead.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Dra. Detalhe"
    assert data["email"] == "det@x.com"
    assert len(data["deals"]) == 1
    assert data["deals"][0]["course"] == "Imersão"
    assert data["deals"][0]["column"] == "Contatado"
