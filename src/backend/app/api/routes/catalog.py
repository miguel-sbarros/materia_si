"""Router de catálogo — cursos e turmas (dados de referência)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.course import CourseOut
from app.services import catalog

router = APIRouter(tags=["catalog"])


@router.get("/courses", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db)) -> list[CourseOut]:
    return catalog.list_courses(db)
