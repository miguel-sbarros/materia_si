"""GET /deals (feed do quadro) e PATCH /deals/{id} (mover). Critérios 2–6 (REQF02)."""

from sqlalchemy import select

from app.core.constants import DealStage, DealStatus
from app.models import Deal, DealEvent
from tests.factories import make_course, make_deal


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
