"""Router de catálogo — cursos e turmas (dados de referência + edição) + módulos (ementa)."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
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
    ModuleCreate,
    ModuleOut,
    ModuleUpdate,
)
from app.services import catalog, course_content, course_modules
from app.services.course_rag import reingest_course_bg

router = APIRouter(tags=["catalog"])


def _module_out(module) -> ModuleOut:
    return ModuleOut(
        id=module.id,
        courseId=module.course_id,
        title=module.title,
        content=module.content,
        position=module.position,
        carga=module.carga,
    )


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
    """Curso (linha do DB) + ementa.

    ``syllabus`` é derivado dos módulos do DB (``course_modules``); se o curso não tiver
    módulos cadastrados, faz fallback ao parser de ``playbook/cursos.md`` (bootstrap).
    404 se o curso não existir.
    """
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    modules = course_modules.list_modules(db, course_id)
    if modules:
        ementa = {
            "name": course.name,
            "summary": course.description or "",
            "sections": [],
            "syllabus": [
                {
                    "tema": m.title,
                    "conteudo": m.content or "",
                    **({"carga": m.carga} if m.carga else {}),
                }
                for m in modules
            ],
        }
    else:
        ementa = course_content.course_ementa(course.name)

    return {
        "course": {
            "id": course.id,
            "name": course.name,
            "description": course.description,
            "modality": course.modality,
            "price": str(course.price) if course.price is not None else None,
            "duration": course.duration,
        },
        "ementa": ementa,
    }


@router.get("/courses/{course_id}/modules", response_model=list[ModuleOut])
def list_modules(course_id: int, db: Session = Depends(get_db)) -> list[ModuleOut]:
    return [_module_out(m) for m in course_modules.list_modules(db, course_id)]


@router.post(
    "/courses/{course_id}/modules",
    response_model=ModuleOut,
    status_code=status.HTTP_201_CREATED,
)
def create_module(
    course_id: int,
    payload: ModuleCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ModuleOut:
    try:
        module = course_modules.create_module(db, course_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    background_tasks.add_task(reingest_course_bg, course_id)
    return _module_out(module)


@router.put("/modules/{module_id}", response_model=ModuleOut)
def update_module(
    module_id: int,
    payload: ModuleUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ModuleOut:
    try:
        module = course_modules.update_module(db, module_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    background_tasks.add_task(reingest_course_bg, module.course_id)
    return _module_out(module)


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    module_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> None:
    try:
        course_id = course_modules.delete_module(db, module_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    background_tasks.add_task(reingest_course_bg, course_id)
