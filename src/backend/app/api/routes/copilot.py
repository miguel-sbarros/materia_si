"""Router do Copiloto de Vendas (P4b, REQF04). Router fino → ``services/copilot``.

Sessões persistidas + chat agêntico. As respostas de chat com lead anexado são conselhos
estruturados (``kind="advice"``); sem lead/com comando, são texto (``kind="text"``).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.copilot import (
    ChatIn,
    MessageOut,
    SessionAttach,
    SessionCreate,
    SessionOut,
)
from app.services import copilot as copilot_service

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionOut:
    try:
        session = copilot_service.create_session(db, payload.leadId)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SessionOut.model_validate(session)


@router.get("/sessions", response_model=list[SessionOut])
def list_sessions(db: Session = Depends(get_db)) -> list[SessionOut]:
    return copilot_service.list_sessions(db)


@router.get("/sessions/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return copilot_service.get_session(db, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/sessions/{session_id}", response_model=SessionOut)
def attach_lead(
    session_id: int, payload: SessionAttach, db: Session = Depends(get_db)
) -> SessionOut:
    """Anexa um lead à sessão atual (sem lead). Já tem lead → 409; inexistente → 404."""
    try:
        session = copilot_service.attach_lead(db, session_id, payload.leadId)
    except ValueError as exc:
        if "já tem um lead" in str(exc):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SessionOut.model_validate(session)


@router.post("/sessions/{session_id}/chat", response_model=MessageOut)
def chat(
    session_id: int, payload: ChatIn, db: Session = Depends(get_db)
) -> MessageOut:
    try:
        return copilot_service.chat(db, session_id, payload.text, payload.command)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
