"""Catálogo — cursos e suas turmas (dados de referência para o frontend).

Leitura (``list_courses``) + escrita: criar/editar cursos e turmas (sem delete). Os
services devolvem objetos ORM; os routers serializam com ``CourseOut``/``CohortOut``.
Conflitos de regra de negócio (nome duplicado, entidade inexistente) viram ``ValueError``
com mensagem em PT — o router traduz para 404/409.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Cohort, Course
from app.schemas.course import CohortCreate, CohortUpdate, CourseCreate, CourseUpdate


def list_courses(db: Session) -> list[Course]:
    return list(
        db.scalars(
            select(Course).options(selectinload(Course.cohorts)).order_by(Course.id)
        ).all()
    )


def create_course(db: Session, payload: CourseCreate) -> Course:
    course = Course(**payload.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Curso já existe") from exc
    db.refresh(course)
    return course


def update_course(db: Session, course_id: int, payload: CourseUpdate) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise ValueError("Curso não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Curso já existe") from exc
    db.refresh(course)
    return course


def create_cohort(db: Session, course_id: int, payload: CohortCreate) -> Cohort:
    if db.get(Course, course_id) is None:
        raise ValueError("Curso não encontrado")
    cohort = Cohort(course_id=course_id, **payload.model_dump())
    db.add(cohort)
    db.commit()
    db.refresh(cohort)
    return cohort


def update_cohort(db: Session, cohort_id: int, payload: CohortUpdate) -> Cohort:
    cohort = db.get(Cohort, cohort_id)
    if cohort is None:
        raise ValueError("Turma não encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cohort, field, value)
    db.commit()
    db.refresh(cohort)
    return cohort
