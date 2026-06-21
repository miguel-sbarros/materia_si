"""Router de conversas — mensagem manual, thread do lead e feed do painel (REQF03).

A rota de mensagem manual dispara a análise automática (P3) via
``imports.maybe_schedule_analysis`` — o gatilho vive em ``imports`` (ponto único) e é
referenciado pelo módulo para que o monkeypatch de ``run_analysis_bg`` nos testes pegue.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.routes import imports
from app.db.session import get_db
from app.schemas.conversation import ConversationSummary, ManualMessageIn, MessageOut
from app.services import conversations as conv_service
from app.services.imports import add_manual_message

router = APIRouter(tags=["conversations"])


@router.post(
    "/leads/{lead_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
def post_manual_message(
    lead_id: int,
    payload: ManualMessageIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> MessageOut:
    try:
        msg = add_manual_message(db, lead_id=lead_id, text=payload.text, sent=payload.sent)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    imports.maybe_schedule_analysis(db, background_tasks, lead_id)
    return MessageOut.model_validate(msg)


@router.get("/leads/{lead_id}/conversation")
def get_lead_conversation(lead_id: int, db: Session = Depends(get_db)) -> dict:
    return conv_service.get_lead_conversation(db, lead_id)


@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(db: Session = Depends(get_db)) -> list[ConversationSummary]:
    return conv_service.list_conversations(db)
