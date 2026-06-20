"""Catálogo — cursos e suas turmas (dados de referência para o frontend)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Course


def list_courses(db: Session) -> list[Course]:
    return list(
        db.scalars(
            select(Course).options(selectinload(Course.cohorts)).order_by(Course.id)
        ).all()
    )
