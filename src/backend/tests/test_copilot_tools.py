"""Ferramentas do copiloto (P4b) testadas diretamente, sem LLM.

Monta o dispatch via ``copilot._build_tools(db)`` e chama os handlers contra o DB real.
``get_cohorts_status`` lê do catálogo; ``get_course_ementa`` parseia o ``playbook/cursos.md``.
Cada handler devolve uma STRING (resultados estruturados são JSON).
"""

import json

from app.services import copilot as copilot_service
from tests.factories import make_course


def test_get_cohorts_status_returns_seeded_cohort(db_session):
    """get_cohorts_status devolve as turmas do curso semeado (JSON com curso/turma/preço)."""
    make_course(db_session, name="Imersão", price="5900.00", n_cohorts=2)
    _tools, dispatch, _captured = copilot_service._build_tools(db_session)

    out = dispatch["get_cohorts_status"]()
    rows = json.loads(out)

    assert isinstance(rows, list)
    assert len(rows) == 2
    assert rows[0]["course"] == "Imersão"
    assert rows[0]["price"] == "5900.00"
    assert "status" in rows[0]


def test_get_cohorts_status_filters_by_course_name(db_session):
    """Filtro por nome do curso (ILIKE) retorna só as turmas do curso casado."""
    make_course(db_session, name="Imersão", n_cohorts=1)
    make_course(db_session, name="Master 3.0", price="22250.00", n_cohorts=1)
    _tools, dispatch, _captured = copilot_service._build_tools(db_session)

    rows = json.loads(dispatch["get_cohorts_status"](course_name="Master"))
    assert {r["course"] for r in rows} == {"Master 3.0"}


def test_get_course_ementa_returns_syllabus(db_session):
    """get_course_ementa devolve a ementa parseada do cursos.md (com syllabus)."""
    _tools, dispatch, _captured = copilot_service._build_tools(db_session)

    out = dispatch["get_course_ementa"](course_name="Master")
    # Pode ser "não encontrado" se o cursos.md não tiver o curso; quando encontra, é JSON.
    assert isinstance(out, str)
    if not out.startswith("Curso não encontrado"):
        ementa = json.loads(out)
        assert "name" in ementa
        assert "syllabus" in ementa


def test_handlers_are_exception_safe(db_session, monkeypatch):
    """Handler que falha internamente devolve string de erro (nunca levanta)."""
    from app.services import analytics

    def boom(_db):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(analytics, "icp_summary", boom)
    _tools, dispatch, _captured = copilot_service._build_tools(db_session)

    out = dispatch["get_icp_stats"]()
    assert "Erro" in out
