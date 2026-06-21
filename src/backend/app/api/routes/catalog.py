"""Router de catálogo — cursos e turmas (dados de referência)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Course
from app.schemas.course import CourseOut
from app.services import catalog, course_content

router = APIRouter(tags=["catalog"])


@router.get("/courses", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db)) -> list[CourseOut]:
    return catalog.list_courses(db)


@router.get("/courses/{course_id}/ementa")
def get_course_ementa(course_id: int, db: Session = Depends(get_db)) -> dict:
    """Curso (linha do DB) + ementa parseada do ``playbook/cursos.md`` (404 se inexistente)."""
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return {
        "course": {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "modality": course.modality,
            "price": str(course.price) if course.price is not None else None,
            "duration": course.duration,
        },
        "ementa": course_content.course_ementa(course.name),
    }
