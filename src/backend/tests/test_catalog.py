"""Catálogo — GET (referência) + edição (criar/editar cursos e turmas, sem delete).

``test_list_courses`` (Critério 1) cobre o feed do frontend; os demais cobrem os contratos
de escrita consumidos pelos modais de edição, incluindo erros (nome duplicado → 409,
entidade inexistente → 404).
"""

from app.models import Cohort, Course
from tests.factories import make_course


def test_list_courses(api_client, db_session):
    make_course(db_session, name="Imersão", n_cohorts=2)
    make_course(db_session, name="Master 3.0", price="22250.00", n_cohorts=1)

    resp = api_client.get("/courses")
    assert resp.status_code == 200

    by_name = {c["name"]: c for c in resp.json()}
    assert {"Imersão", "Master 3.0"} <= by_name.keys()
    assert len(by_name["Imersão"]["cohorts"]) == 2

    cohort = by_name["Imersão"]["cohorts"][0]
    assert {"id", "course_id", "name", "status", "price_per_slot"} <= cohort.keys()


def test_create_course_returns_fields(api_client, db_session):
    resp = api_client.post(
        "/courses",
        json={
            "name": "Curso Novo",
            "description": "Implantodontia digital",
            "modality": "Presencial",
            "price": "5900.00",
            "duration": "3 dias",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Curso Novo"
    assert body["description"] == "Implantodontia digital"
    assert body["modality"] == "Presencial"
    assert body["duration"] == "3 dias"
    assert body["cohorts"] == []
    assert db_session.get(Course, body["id"]) is not None


def test_create_course_duplicate_name_conflict(api_client, db_session):
    make_course(db_session, name="Imersão Out")
    db_session.commit()

    resp = api_client.post("/courses", json={"name": "Imersão Out"})
    assert resp.status_code == 409


def test_update_course_edits_fields(api_client, db_session):
    course, _ = make_course(db_session, name="Curso Editável", price="100.00")
    db_session.commit()

    resp = api_client.put(
        f"/courses/{course.id}",
        json={"description": "Atualizada", "price": "1234.50", "modality": "Online"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "Atualizada"
    assert body["modality"] == "Online"
    assert body["price"] == "1234.50"
    assert body["name"] == "Curso Editável"  # inalterado


def test_update_course_missing_is_404(api_client, db_session):
    resp = api_client.put("/courses/999999", json={"description": "x"})
    assert resp.status_code == 404


def test_create_cohort_under_course(api_client, db_session):
    course, _ = make_course(db_session, name="Curso C", n_cohorts=0)
    db_session.commit()

    resp = api_client.post(
        f"/courses/{course.id}/cohorts",
        json={
            "name": "Turma Q1",
            "capacity": 25,
            "price_per_slot": "4500.00",
            "status": "open",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Turma Q1"
    assert body["course_id"] == course.id
    assert body["capacity"] == 25
    assert body["price_per_slot"] == "4500.00"
    assert body["status"] == "open"
    assert db_session.get(Cohort, body["id"]) is not None


def test_create_cohort_missing_course_is_404(api_client, db_session):
    resp = api_client.post("/courses/999999/cohorts", json={"name": "Fantasma"})
    assert resp.status_code == 404


def test_update_cohort_edits_fields(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Curso D", n_cohorts=1)
    db_session.commit()

    resp = api_client.put(
        f"/cohorts/{cohort.id}",
        json={"name": "Turma Renomeada", "status": "active", "price_per_slot": "9999.00"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Turma Renomeada"
    assert body["status"] == "active"
    assert body["price_per_slot"] == "9999.00"


def test_update_cohort_missing_is_404(api_client, db_session):
    resp = api_client.put("/cohorts/999999", json={"name": "x"})
    assert resp.status_code == 404
