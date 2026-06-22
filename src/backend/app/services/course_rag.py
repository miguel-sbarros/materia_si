"""Re-ingestão do conteúdo de um curso no RAG do copiloto (REQF04, reflexo).

Salvar/editar/excluir um módulo agenda ``reingest_course_bg`` (background): re-embeda os
módulos daquele curso em ``knowledge_chunks`` com ``source='course'`` e ``node_ref`` prefixado
por ``course:{course_id}#``. Delete-then-insert por prefixo = idempotente e isolado por curso
(não toca ``kb_graph``/``playbook``). ``rag.retrieve`` é source-agnóstico → o copiloto passa a
saber sem nenhuma mudança no copiloto.
"""

import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Course, CourseModule, KnowledgeChunk
from app.services import rag

SOURCE_COURSE = "course"
CHUNK_TYPE = "course_module"

logger = logging.getLogger(__name__)


def reingest_course(db: Session, course_id: int) -> int:
    """Delete-then-insert dos chunks ``source='course'`` daquele curso. Retorna a contagem.

    Constrói 1 chunk por módulo (``node_ref=f'course:{course_id}#{module.id}'``); embeda o
    conteúdo via ``rag.embed_texts`` e insere. Re-rodar é idempotente (zera o prefixo antes).
    """
    db.execute(
        delete(KnowledgeChunk).where(
            KnowledgeChunk.source == SOURCE_COURSE,
            KnowledgeChunk.node_ref.like(f"course:{course_id}#%"),
        )
    )

    course = db.get(Course, course_id)
    if course is None:
        db.commit()
        return 0

    modules = list(
        db.scalars(
            select(CourseModule)
            .where(CourseModule.course_id == course_id)
            .order_by(CourseModule.position, CourseModule.id)
        ).all()
    )

    chunks = [
        KnowledgeChunk(
            source=SOURCE_COURSE,
            chunk_type=CHUNK_TYPE,
            node_ref=f"course:{course_id}#{m.id}",
            label=None,
            title=m.title,
            content=f"{course.name} — {m.title}: {m.content or ''}".strip(),
            meta={"course_id": course_id, "module_id": m.id},
        )
        for m in modules
    ]
    # A API de embeddings rejeita string vazia — todo chunk carrega ao menos curso + título.
    chunks = [c for c in chunks if c.content and c.content.strip()]
    if not chunks:
        db.commit()
        return 0

    vectors = rag.embed_texts([c.content for c in chunks])
    for chunk, vec in zip(chunks, vectors, strict=True):
        chunk.embedding = vec
    db.add_all(chunks)
    db.commit()
    return len(chunks)


def reingest_course_bg(course_id: int) -> None:
    """Roda ``reingest_course`` em background com ``SessionLocal`` própria.

    Usado como ``BackgroundTask`` após CRUD de módulo — NUNCA deve quebrar o request:
    qualquer erro (embeddings, DB) é logado e engolido.
    """
    try:
        with SessionLocal() as db:
            reingest_course(db, course_id)
    except Exception:  # noqa: BLE001 — falha de re-ingestão não pode quebrar o CRUD.
        logger.exception("Falha na re-ingestão do curso %s no RAG", course_id)
