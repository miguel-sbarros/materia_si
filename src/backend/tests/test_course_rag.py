"""Testes da re-ingestão de conteúdo de curso no RAG do copiloto (REQF04, reflexo).

``reingest_course`` faz delete-then-insert dos chunks ``source='course'`` daquele curso
(prefixo ``course:{id}#`` no ``node_ref``), idempotente, sem tocar ``kb_graph``/``playbook``.
Depois, ``rag.retrieve`` (source-agnóstico) encontra os chunks do curso. Usa ``mock_embedder``.
"""

from sqlalchemy import select

from app.models import CourseModule, KnowledgeChunk
from app.services import rag
from app.services.course_rag import reingest_course
from tests.factories import make_course


def _course_chunks(db, course_id):
    return list(
        db.scalars(
            select(KnowledgeChunk).where(
                KnowledgeChunk.source == "course",
                KnowledgeChunk.node_ref.like(f"course:{course_id}#%"),
            )
        ).all()
    )


def test_reingest_course_creates_one_chunk_per_module(db_session, mock_embedder):
    course, _ = make_course(db_session, name="Curso RAG A", n_cohorts=0)
    db_session.add_all([
        CourseModule(
            course_id=course.id, title="Cirurgia guiada", content="planejamento", position=0
        ),
        CourseModule(course_id=course.id, title="Próteses", content="instalação", position=1),
    ])
    db_session.flush()

    n = reingest_course(db_session, course.id)
    assert n == 2

    chunks = _course_chunks(db_session, course.id)
    assert len(chunks) == 2
    assert all(c.chunk_type == "course_module" for c in chunks)
    assert all(c.content for c in chunks)


def test_reingest_course_idempotent_by_prefix(db_session, mock_embedder):
    # Outro curso (não deve ser afetado) + um chunk kb_graph (intacto).
    course_a, _ = make_course(db_session, name="Curso RAG B", n_cohorts=0)
    course_b, _ = make_course(db_session, name="Curso RAG C", n_cohorts=0)
    db_session.add(CourseModule(course_id=course_a.id, title="Mod A", content="a", position=0))
    db_session.add(CourseModule(course_id=course_b.id, title="Mod B", content="b", position=0))
    db_session.add(
        KnowledgeChunk(
            source="kb_graph", chunk_type="node", node_ref="node:1",
            content="grafo intacto", embedding=mock_embedder("grafo intacto"),
        )
    )
    db_session.flush()

    reingest_course(db_session, course_a.id)
    reingest_course(db_session, course_b.id)
    # Re-rodar A não duplica nem mexe em B/grafo.
    reingest_course(db_session, course_a.id)

    assert len(_course_chunks(db_session, course_a.id)) == 1
    assert len(_course_chunks(db_session, course_b.id)) == 1
    # kb_graph intacto.
    graph = db_session.scalars(
        select(KnowledgeChunk).where(KnowledgeChunk.source == "kb_graph")
    ).all()
    assert len(graph) == 1


def test_reingest_course_removes_chunks_for_deleted_modules(db_session, mock_embedder):
    course, _ = make_course(db_session, name="Curso RAG D", n_cohorts=0)
    m1 = CourseModule(course_id=course.id, title="Mod 1", content="x", position=0)
    m2 = CourseModule(course_id=course.id, title="Mod 2", content="y", position=1)
    db_session.add_all([m1, m2])
    db_session.flush()
    reingest_course(db_session, course.id)
    assert len(_course_chunks(db_session, course.id)) == 2

    # Remove um módulo e re-ingere → 1 chunk.
    db_session.delete(m2)
    db_session.flush()
    reingest_course(db_session, course.id)
    assert len(_course_chunks(db_session, course.id)) == 1


def test_retrieve_finds_course_chunk(db_session, mock_embedder):
    course, _ = make_course(db_session, name="Curso RAG E", n_cohorts=0)
    db_session.add(
        CourseModule(
            course_id=course.id, title="Cirurgia guiada de implantes",
            content="planejamento reverso e guia cirúrgico", position=0,
        )
    )
    # Ruído de outra fonte.
    db_session.add(
        KnowledgeChunk(
            source="kb_graph", chunk_type="node", node_ref="node:99",
            content="financiamento parcelamento matrícula",
            embedding=mock_embedder("financiamento parcelamento matrícula"),
        )
    )
    db_session.flush()
    reingest_course(db_session, course.id)

    results = rag.retrieve(db_session, "cirurgia guiada planejamento implantes", k=3)
    assert results
    assert results[0].source == "course"
    assert results[0].node_ref.startswith(f"course:{course.id}#")
