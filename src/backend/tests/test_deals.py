"""GET /deals (feed do quadro) e PATCH /deals/{id} (mover). Critérios 2–6 (REQF02)."""

import pytest
from sqlalchemy import func, select

from app.core.constants import DealStage, DealStatus
from app.models import Deal, DealEvent
from app.services.deals import card_column, create_closed_deal
from tests.factories import make_course, make_deal, make_lead, make_seller


def test_board_feed_maps_columns(api_client, db_session):
    """won→Matriculado, lost→Perdido, senão stage."""
    _course, [cohort] = make_course(db_session)
    make_deal(db_session, cohort, stage=DealStage.NOVO, status=DealStatus.OPEN)
    make_deal(db_session, cohort, stage=DealStage.NEGOCIANDO, status=DealStatus.OPEN)
    make_deal(db_session, cohort, stage=DealStage.NEGOCIANDO, status=DealStatus.WON)
    make_deal(
        db_session, cohort, stage=DealStage.NEGOCIANDO, status=DealStatus.LOST,
        lost_reason="Sem orçamento",
    )

    resp = api_client.get("/deals")
    assert resp.status_code == 200
    assert sorted(c["column"] for c in resp.json()) == sorted(
        ["Novo", "Negociando", "Matriculado", "Perdido"]
    )


def test_board_filters(api_client, db_session):
    course_a, [coh_a] = make_course(db_session, name="Curso A")
    course_b, [coh_b] = make_course(db_session, name="Curso B")
    make_deal(db_session, coh_a)
    make_deal(db_session, coh_b)
    make_deal(db_session, coh_b)

    assert len(api_client.get("/deals").json()) == 3

    by_course = api_client.get(f"/deals?course_id={course_b.id}").json()
    assert len(by_course) == 2
    assert all(c["course"] == "Curso B" for c in by_course)

    by_cohort = api_client.get(f"/deals?cohort_id={coh_a.id}").json()
    assert len(by_cohort) == 1
    assert by_cohort[0]["cohortId"] == coh_a.id


def test_move_stage_writes_event(api_client, db_session):
    _course, [cohort] = make_course(db_session)
    deal = make_deal(db_session, cohort, stage=DealStage.NOVO)

    resp = api_client.patch(f"/deals/{deal.id}", json={"column": "Contatado"})
    assert resp.status_code == 200
    card = resp.json()
    assert card["column"] == "Contatado"
    assert card["stage"] == "Contatado"
    assert card["status"] == "open"

    refreshed = db_session.get(Deal, deal.id)
    assert refreshed.stage == DealStage.CONTATADO
    events = db_session.scalars(select(DealEvent).where(DealEvent.deal_id == deal.id)).all()
    assert len(events) == 1
    assert events[0].from_stage == DealStage.NOVO
    assert events[0].to_stage == DealStage.CONTATADO


def test_move_to_perdido_requires_reason(api_client, db_session):
    _course, [cohort] = make_course(db_session)
    deal = make_deal(db_session, cohort, stage=DealStage.NEGOCIANDO)

    # Negativo: sem motivo → 422 (honra o CHECK ck_deals_lost_reason).
    bad = api_client.patch(f"/deals/{deal.id}", json={"column": "Perdido"})
    assert bad.status_code == 422

    # Positivo: com motivo persiste e registra o histórico.
    good = api_client.patch(
        f"/deals/{deal.id}", json={"column": "Perdido", "lost_reason": "Sem orçamento"}
    )
    assert good.status_code == 200
    card = good.json()
    assert card["column"] == "Perdido"
    assert card["status"] == "lost"

    refreshed = db_session.get(Deal, deal.id)
    assert refreshed.status == DealStatus.LOST
    assert refreshed.lost_reason == "Sem orçamento"
    events = db_session.scalars(select(DealEvent).where(DealEvent.deal_id == deal.id)).all()
    assert any(e.to_status == DealStatus.LOST for e in events)


def test_move_to_matriculado_sets_won(api_client, db_session):
    _course, [cohort] = make_course(db_session)
    deal = make_deal(db_session, cohort, stage=DealStage.NEGOCIANDO)

    resp = api_client.patch(f"/deals/{deal.id}", json={"column": "Matriculado"})
    assert resp.status_code == 200
    card = resp.json()
    assert card["column"] == "Matriculado"
    assert card["status"] == "won"
    assert card["stage"] == "Negociando"  # stage preservado

    refreshed = db_session.get(Deal, deal.id)
    assert refreshed.status == DealStatus.WON
    events = db_session.scalars(select(DealEvent).where(DealEvent.deal_id == deal.id)).all()
    assert any(e.to_status == DealStatus.WON for e in events)


def test_create_deal_for_lead(api_client, db_session):
    """POST /leads/{id}/deals → cria deal no estágio escolhido, aparece no quadro, grava evento."""
    seller = make_seller(db_session)
    _course, [cohort] = make_course(db_session)
    lead = make_lead(db_session, name="Lead Sem Deal", assignee_id=seller.id)

    resp = api_client.post(
        f"/leads/{lead.id}/deals", json={"cohort_id": cohort.id, "stage": "Contatado"}
    )
    assert resp.status_code == 201
    card = resp.json()
    assert card["leadId"] == lead.id
    assert card["cohortId"] == cohort.id
    assert card["column"] == "Contatado"
    assert card["stage"] == "Contatado"
    assert card["status"] == "open"

    deal = db_session.scalar(select(Deal).where(Deal.lead_id == lead.id))
    assert deal is not None
    assert deal.stage == DealStage.CONTATADO
    assert deal.status == DealStatus.OPEN
    events = db_session.scalars(select(DealEvent).where(DealEvent.deal_id == deal.id)).all()
    assert len(events) == 1
    assert events[0].from_stage is None
    assert events[0].to_stage == DealStage.CONTATADO
    assert events[0].to_status == DealStatus.OPEN

    # Aparece no feed do quadro.
    board = api_client.get("/deals").json()
    assert any(c["id"] == card["id"] for c in board)


def test_create_deal_invalid_stage_422(api_client, db_session):
    """Estágio terminal (Matriculado/Perdido) não é permitido aqui → 422."""
    _course, [cohort] = make_course(db_session)
    lead = make_lead(db_session, name="Lead X")

    resp = api_client.post(
        f"/leads/{lead.id}/deals", json={"cohort_id": cohort.id, "stage": "Matriculado"}
    )
    assert resp.status_code == 422


def test_create_deal_duplicate_409(api_client, db_session):
    """Mesmo lead + turma duas vezes → 409 (honra UNIQUE(lead_id, cohort_id))."""
    _course, [cohort] = make_course(db_session)
    lead = make_lead(db_session, name="Lead Dup")

    first = api_client.post(
        f"/leads/{lead.id}/deals", json={"cohort_id": cohort.id, "stage": "Novo"}
    )
    assert first.status_code == 201

    second = api_client.post(
        f"/leads/{lead.id}/deals", json={"cohort_id": cohort.id, "stage": "Novo"}
    )
    assert second.status_code == 409


def test_create_closed_deal_won(db_session):
    """Cold start: deal nasce fechado (won → Matriculado) com histórico de 2 eventos."""
    _course, [cohort] = make_course(db_session)
    lead = make_lead(db_session)
    deal = create_closed_deal(
        db_session, lead_id=lead.id, cohort_id=cohort.id, status=DealStatus.WON
    )
    assert deal.status == DealStatus.WON
    assert deal.lost_reason is None
    assert card_column(deal) == "Matriculado"
    events = db_session.scalars(select(DealEvent).where(DealEvent.deal_id == deal.id)).all()
    assert len(events) == 2
    assert events[-1].to_status == DealStatus.WON


def test_create_closed_deal_lost(db_session):
    _course, [cohort] = make_course(db_session)
    lead = make_lead(db_session)
    deal = create_closed_deal(
        db_session,
        lead_id=lead.id,
        cohort_id=cohort.id,
        status=DealStatus.LOST,
        lost_reason="Achou caro",
    )
    assert deal.status == DealStatus.LOST
    assert deal.lost_reason == "Achou caro"
    assert card_column(deal) == "Perdido"


def test_create_closed_deal_lost_requires_reason(db_session):
    _course, [cohort] = make_course(db_session)
    lead = make_lead(db_session)
    with pytest.raises(ValueError, match="lost_reason"):
        create_closed_deal(
            db_session, lead_id=lead.id, cohort_id=cohort.id, status=DealStatus.LOST
        )


def test_create_closed_deal_idempotent(db_session):
    """Mesmo (lead, turma) duas vezes → devolve o existente, não duplica."""
    _course, [cohort] = make_course(db_session)
    lead = make_lead(db_session)
    first = create_closed_deal(
        db_session, lead_id=lead.id, cohort_id=cohort.id, status=DealStatus.WON
    )
    again = create_closed_deal(
        db_session,
        lead_id=lead.id,
        cohort_id=cohort.id,
        status=DealStatus.LOST,
        lost_reason="x",
    )
    assert again.id == first.id
    assert again.status == DealStatus.WON  # mantém o original
    count = db_session.scalar(
        select(func.count()).select_from(Deal).where(Deal.lead_id == lead.id)
    )
    assert count == 1
