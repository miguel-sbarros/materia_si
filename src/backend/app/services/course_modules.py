"""CRUD de módulos de curso (REQF04, conteúdo). Padrão do ``catalog.py``.

Regras viram ``ValueError`` PT — o router fino traduz para 404. O agendamento da
re-ingestão no RAG é responsabilidade do router (``BackgroundTasks``).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Course, CourseModule
from app.schemas.course import ModuleCreate, ModuleUpdate


def list_modules(db: Session, course_id: int) -> list[CourseModule]:
    return list(
        db.scalars(
            select(CourseModule)
            .where(CourseModule.course_id == course_id)
            .order_by(CourseModule.position, CourseModule.id)
        ).all()
    )


def create_module(db: Session, course_id: int, payload: ModuleCreate) -> CourseModule:
    if db.get(Course, course_id) is None:
        raise ValueError("Curso não encontrado")
    module = CourseModule(course_id=course_id, **payload.model_dump())
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def update_module(db: Session, module_id: int, payload: ModuleUpdate) -> CourseModule:
    module = db.get(CourseModule, module_id)
    if module is None:
        raise ValueError("Módulo não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(module, field, value)
    db.commit()
    db.refresh(module)
    return module


def delete_module(db: Session, module_id: int) -> int:
    """Exclui o módulo; retorna o ``course_id`` (para agendar a re-ingestão)."""
    module = db.get(CourseModule, module_id)
    if module is None:
        raise ValueError("Módulo não encontrado")
    course_id = module.course_id
    db.delete(module)
    db.commit()
    return course_id
