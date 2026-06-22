"""Testes de CRUD de módulos do curso (REQF04, conteúdo) + reflexo na ementa e RAG.

CRUD via ``/courses/{id}/modules`` e ``/modules/{id}``. ``GET /courses/{id}/ementa`` passa a
derivar o ``syllabus`` dos módulos do DB (fallback ao parser de ``cursos.md`` se vazio).
Salvar/editar/excluir um módulo agenda a re-ingestão em background (espião).
"""

from app.models import CourseModule
from tests.factories import make_course, make_course_module


def test_list_modules_empty(api_client, db_session):
    course, _ = make_course(db_session, name="Curso Mod A", n_cohorts=0)
    db_session.commit()

    resp = api_client.get(f"/courses/{course.id}/modules")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_module(api_client, db_session, monkeypatch):
    monkeypatch.setattr("app.api.routes.catalog.reingest_course_bg", lambda cid: None)
    course, _ = make_course(db_session, name="Curso Mod B", n_cohorts=0)
    db_session.commit()

    resp = api_client.post(
        f"/courses/{course.id}/modules",
        json={"title": "Planejamento digital", "content": "TC, escaneamento", "position": 1,
              "carga": "8 horas"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Planejamento digital"
    assert body["courseId"] == course.id
    assert body["content"] == "TC, escaneamento"
    assert body["position"] == 1
    assert body["carga"] == "8 horas"
    assert db_session.get(CourseModule, body["id"]) is not None


def test_create_module_unknown_course_404(api_client, db_session):
    resp = api_client.post("/courses/999999/modules", json={"title": "x"})
    assert resp.status_code == 404


def test_list_modules_ordered_by_position(api_client, db_session):
    course, _ = make_course(db_session, name="Curso Mod C", n_cohorts=0)
    make_course_module(db_session, course, title="Segundo", position=2)
    make_course_module(db_session, course, title="Primeiro", position=1)
    db_session.commit()

    resp = api_client.get(f"/courses/{course.id}/modules")
    titles = [m["title"] for m in resp.json()]
    assert titles == ["Primeiro", "Segundo"]


def test_update_module(api_client, db_session, monkeypatch):
    monkeypatch.setattr("app.api.routes.catalog.reingest_course_bg", lambda cid: None)
    course, _ = make_course(db_session, name="Curso Mod D", n_cohorts=0)
    module = make_course_module(db_session, course, title="Antigo", position=0)
    db_session.commit()

    resp = api_client.put(
        f"/modules/{module.id}", json={"title": "Novo Título", "content": "atualizado"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Novo Título"
    assert body["content"] == "atualizado"


def test_update_module_404(api_client, db_session):
    resp = api_client.put("/modules/999999", json={"title": "x"})
    assert resp.status_code == 404


def test_delete_module(api_client, db_session, monkeypatch):
    monkeypatch.setattr("app.api.routes.catalog.reingest_course_bg", lambda cid: None)
    course, _ = make_course(db_session, name="Curso Mod E", n_cohorts=0)
    module = make_course_module(db_session, course, title="Apagar", position=0)
    db_session.commit()
    module_id = module.id

    resp = api_client.delete(f"/modules/{module_id}")
    assert resp.status_code == 204
    assert db_session.get(CourseModule, module_id) is None


def test_ementa_derives_syllabus_from_db_modules(api_client, db_session, monkeypatch):
    monkeypatch.setattr("app.api.routes.catalog.reingest_course_bg", lambda cid: None)
    course, _ = make_course(db_session, name="Curso Ementa DB", n_cohorts=0)
    make_course_module(
        db_session, course, title="Cirurgia guiada", position=0, content="Passo a passo",
        carga="6 horas",
    )
    make_course_module(
        db_session, course, title="Próteses", position=1, content="Sobre implante",
    )
    db_session.commit()

    resp = api_client.get(f"/courses/{course.id}/ementa")
    assert resp.status_code == 200
    syllabus = resp.json()["ementa"]["syllabus"]
    assert [row["tema"] for row in syllabus] == ["Cirurgia guiada", "Próteses"]
    assert syllabus[0]["conteudo"] == "Passo a passo"
    assert syllabus[0]["carga"] == "6 horas"


def test_ementa_falls_back_to_parser_when_no_modules(api_client, db_session):
    # Curso cujo nome casa com o cursos.md (Master/Aperfeiçoamento) e SEM módulos no DB.
    course, _ = make_course(
        db_session, name="Master 3.0 — Aperfeiçoamento Clínico", n_cohorts=0
    )
    db_session.commit()

    resp = api_client.get(f"/courses/{course.id}/ementa")
    assert resp.status_code == 200
    ementa = resp.json()["ementa"]
    # Fallback ao parser: traz syllabus do cursos.md.
    assert ementa is not None
    assert len(ementa["syllabus"]) > 0


def test_module_save_schedules_reingest(api_client, db_session, monkeypatch):
    """O POST de módulo agenda a re-ingestão em background daquele curso."""
    calls = []
    monkeypatch.setattr(
        "app.api.routes.catalog.reingest_course_bg", lambda cid: calls.append(cid)
    )
    course, _ = make_course(db_session, name="Curso Reingest", n_cohorts=0)
    db_session.commit()

    resp = api_client.post(f"/courses/{course.id}/modules", json={"title": "Novo módulo"})
    assert resp.status_code == 201
    # BackgroundTask roda síncrono no TestClient → o espião viu o curso.
    assert calls == [course.id]
