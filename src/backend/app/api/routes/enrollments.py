"""Router de matrícula (REQF06) — router fino → ``services/enrollments.py``.

Mensagens PT do service viram 404 (não encontrado), 409 (já matriculado) ou 422 (turma lotada).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.enrollment import CohortEnrollmentsOut, EnrollmentCreate, EnrollmentOut
from app.services import enrollments as enrollments_service

router = APIRouter(tags=["enrollments"])


@router.post(
    "/cohorts/{cohort_id}/enrollments",
    response_model=EnrollmentOut,
    status_code=status.HTTP_201_CREATED,
)
def enroll_lead(
    cohort_id: int, payload: EnrollmentCreate, db: Session = Depends(get_db)
) -> EnrollmentOut:
    try:
        return enrollments_service.enroll_lead(
            db, cohort_id, payload.lead_id, payload.source
        )
    except ValueError as exc:
        msg = str(exc)
        if "não encontrad" in msg.lower():
            raise HTTPException(status_code=404, detail=msg) from exc
        if "já matriculad" in msg.lower():
            raise HTTPException(status_code=409, detail=msg) from exc
        raise HTTPException(status_code=422, detail=msg) from exc  # turma lotada


@router.get("/cohorts/{cohort_id}/enrollments", response_model=CohortEnrollmentsOut)
def cohort_enrollments(
    cohort_id: int, db: Session = Depends(get_db)
) -> CohortEnrollmentsOut:
    try:
        return enrollments_service.cohort_enrollments(db, cohort_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/cohorts/{cohort_id}/enrollments/{lead_id}", status_code=status.HTTP_200_OK)
def cancel_enrollment(
    cohort_id: int, lead_id: int, db: Session = Depends(get_db)
) -> dict:
    try:
        enrollments_service.cancel_enrollment(db, cohort_id, lead_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "cancelled"}
