"""Endpoint de saúde — usado pelo healthcheck do compose e pelo smoke-test de CI."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - caminho de erro de infra
        db_status = "error"
    return {"status": "ok", "db": db_status}
