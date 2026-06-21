"""Router de catálogo — cursos e turmas (dados de referência + edição)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Course
from app.schemas.course import (
    CohortCreate,
    CohortOut,
    CohortUpdate,
    CourseCreate,
    CourseOut,
    CourseUpdate,
)
from app.services import catalog, course_content

router = APIRouter(tags=["catalog"])


@router.get("/courses", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db)) -> list[CourseOut]:
    return catalog.list_courses(db)


@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(payload: CourseCreate, db: Session = Depends(get_db)) -> CourseOut:
    try:
        course = catalog.create_course(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CourseOut.model_validate(course)


@router.put("/courses/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int, payload: CourseUpdate, db: Session = Depends(get_db)
) -> CourseOut:
    try:
        course = catalog.update_course(db, course_id, payload)
    except ValueError as exc:
        if "já existe" in str(exc):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CourseOut.model_validate(course)


@router.post(
    "/courses/{course_id}/cohorts",
    response_model=CohortOut,
    status_code=status.HTTP_201_CREATED,
)
def create_cohort(
    course_id: int, payload: CohortCreate, db: Session = Depends(get_db)
) -> CohortOut:
    try:
        cohort = catalog.create_cohort(db, course_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CohortOut.model_validate(cohort)


@router.put("/cohorts/{cohort_id}", response_model=CohortOut)
def update_cohort(
    cohort_id: int, payload: CohortUpdate, db: Session = Depends(get_db)
) -> CohortOut:
    try:
        cohort = catalog.update_cohort(db, cohort_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CohortOut.model_validate(cohort)


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
