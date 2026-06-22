"""Testes de matrícula (REQF06) — endpoint + integração com o funil.

Matricular cria a ``Enrollment`` e transiciona (ou cria) o ``deal(lead, cohort)`` para
``won`` (coluna "Matriculado"), gravando um ``DealEvent`` e vinculando ``enrollment.deal_id``.
Vagas = ``capacity − matrículas ativas``; turma lotada → 422. Cancelar libera a vaga e
reverte o deal para ``open``/``Negociando``.
"""

from app.core.constants import DealStage, DealStatus, EnrollmentStatus
from app.models import Deal, Enrollment
from tests.factories import make_course, make_deal, make_enrollment, make_lead


def test_enroll_creates_enrollment_and_wins_deal(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso A", n_cohorts=1)
    lead = make_lead(db_session, name="Lead Sem Deal")
    db_session.commit()

    resp = api_client.post(
        f"/cohorts/{cohort.id}/enrollments", json={"lead_id": lead.id, "source": "Indicação"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["leadId"] == lead.id
    assert body["cohortId"] == cohort.id
    assert body["leadName"] == "Lead Sem Deal"
    assert body["status"] == "active"
    assert body["source"] == "Indicação"
    assert body["dealId"] is not None

    # Deal foi criado e está won (coluna Matriculado).
    deal = db_session.get(Deal, body["dealId"])
    assert deal is not None
    assert deal.status == DealStatus.WON
    assert deal.lead_id == lead.id and deal.cohort_id == cohort.id
    # Histórico gravado (REQF02): ao menos um evento terminando em won.
    assert any(ev.to_status == DealStatus.WON for ev in deal.events)
    # enrollment.deal_id vinculado.
    enr = db_session.get(Enrollment, body["id"])
    assert enr.deal_id == deal.id


def test_enroll_existing_open_deal_moves_to_won(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso B", n_cohorts=1)
    lead = make_lead(db_session, name="Lead Com Deal")
    deal = make_deal(
        db_session, cohort, lead=lead, stage=DealStage.NEGOCIANDO, status=DealStatus.OPEN
    )
    db_session.commit()

    resp = api_client.post(f"/cohorts/{cohort.id}/enrollments", json={"lead_id": lead.id})
    assert resp.status_code == 201
    assert resp.json()["dealId"] == deal.id

    db_session.refresh(deal)
    assert deal.status == DealStatus.WON
    assert any(ev.to_status == DealStatus.WON for ev in deal.events)


def test_enroll_duplicate_409(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso C", n_cohorts=1)
    lead = make_lead(db_session)
    make_enrollment(db_session, cohort, lead=lead)
    db_session.commit()

    resp = api_client.post(f"/cohorts/{cohort.id}/enrollments", json={"lead_id": lead.id})
    assert resp.status_code == 409


def test_enroll_unknown_lead_or_cohort_404(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso D", n_cohorts=1)
    db_session.commit()

    # lead inexistente
    resp = api_client.post(f"/cohorts/{cohort.id}/enrollments", json={"lead_id": 999999})
    assert resp.status_code == 404

    # cohort inexistente
    lead = make_lead(db_session)
    db_session.commit()
    resp = api_client.post("/cohorts/999999/enrollments", json={"lead_id": lead.id})
    assert resp.status_code == 404


def test_enroll_full_cohort_422(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso E", n_cohorts=1)
    cohort.capacity = 1
    other = make_lead(db_session, name="Já Matriculado")
    make_enrollment(db_session, cohort, lead=other)  # 1 ativa → lotada
    novo = make_lead(db_session, name="Tarde Demais")
    db_session.commit()

    resp = api_client.post(f"/cohorts/{cohort.id}/enrollments", json={"lead_id": novo.id})
    assert resp.status_code == 422
    assert "lotada" in resp.json()["detail"].lower()


def test_cancel_enrollment_frees_slot_and_reopens_deal(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso F", n_cohorts=1)
    cohort.capacity = 2
    lead = make_lead(db_session, name="Vai Cancelar")
    db_session.commit()

    # Matricula (cria deal won).
    enroll = api_client.post(f"/cohorts/{cohort.id}/enrollments", json={"lead_id": lead.id})
    assert enroll.status_code == 201
    deal_id = enroll.json()["dealId"]

    before = api_client.get(f"/cohorts/{cohort.id}/enrollments").json()
    assert before["enrolled"] == 1 and before["available"] == 1

    # Cancela → libera a vaga.
    resp = api_client.delete(f"/cohorts/{cohort.id}/enrollments/{lead.id}")
    assert resp.status_code == 200

    after = api_client.get(f"/cohorts/{cohort.id}/enrollments").json()
    assert after["enrolled"] == 0 and after["available"] == 2

    # Deal revertido para open/Negociando + evento.
    deal = db_session.get(Deal, deal_id)
    db_session.refresh(deal)
    assert deal.status == DealStatus.OPEN
    assert deal.stage == DealStage.NEGOCIANDO
    assert any(ev.to_status == DealStatus.OPEN for ev in deal.events)


def test_cohort_enrollments_summary_counts_active_only(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso G", n_cohorts=1)
    cohort.capacity = 5
    make_enrollment(db_session, cohort, lead=make_lead(db_session, name="Ativo 1"))
    make_enrollment(db_session, cohort, lead=make_lead(db_session, name="Ativo 2"))
    make_enrollment(
        db_session,
        cohort,
        lead=make_lead(db_session, name="Cancelado"),
        status=EnrollmentStatus.CANCELLED,
    )
    db_session.commit()

    resp = api_client.get(f"/cohorts/{cohort.id}/enrollments")
    assert resp.status_code == 200
    body = resp.json()
    assert body["capacity"] == 5
    assert body["enrolled"] == 2  # só ativas
    assert body["available"] == 3
    # A lista devolve só as matrículas ativas.
    assert len(body["enrollments"]) == 2
    assert {e["leadName"] for e in body["enrollments"]} == {"Ativo 1", "Ativo 2"}


def test_cohort_enrollments_summary_no_capacity(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso H", n_cohorts=1)
    cohort.capacity = None
    make_enrollment(db_session, cohort, lead=make_lead(db_session))
    db_session.commit()

    body = api_client.get(f"/cohorts/{cohort.id}/enrollments").json()
    assert body["capacity"] is None
    assert body["enrolled"] == 1
    assert body["available"] is None
