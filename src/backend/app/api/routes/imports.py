"""Router de import de WhatsApp — upload de .txt/.zip (REQF03). Router fino → service.

Hospeda também o gatilho de análise automática (P3): após um import bem-sucedido (ou uma
mensagem manual), se a conversa passar de 3 mensagens, agenda ``run_analysis_bg`` como
``BackgroundTask`` (assíncrono; a resposta do import não espera). ``maybe_schedule_analysis``
é o ponto único reutilizado pelo router de mensagem manual.
"""

import io
import zipfile

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Conversation, Message
from app.schemas.conversation import ImportSummary
from app.services.analysis import run_analysis_bg, should_auto_analyze
from app.services.imports import import_chat
from app.services.whatsapp_parser import (
    NotWhatsAppExportError,
    WhatsAppParseError,
    phone_from_filename,
)

router = APIRouter(tags=["imports"])


def _conversation_message_count(db: Session, lead_id: int) -> int:
    """Total de mensagens na conversa WhatsApp do lead (0 se não houver conversa)."""
    return (
        db.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.lead_id == lead_id, Conversation.channel == "WhatsApp")
        )
        or 0
    )


def maybe_schedule_analysis(
    db: Session, background_tasks: BackgroundTasks, lead_id: int
) -> None:
    """Agenda a análise assíncrona se a conversa do lead passar de 3 mensagens (gate P3)."""
    if should_auto_analyze(_conversation_message_count(db, lead_id)):
        background_tasks.add_task(run_analysis_bg, lead_id)


def _read_chat_text(raw: bytes, filename: str) -> str:
    """Extrai o ``_chat.txt`` de um .zip ou decodifica o .txt direto (UTF-8)."""
    if filename.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                member = next(
                    (n for n in zf.namelist() if n.endswith("_chat.txt")), None
                )
                if member is None:
                    raise HTTPException(
                        status_code=422,
                        detail="Zip inválido: nenhum _chat.txt encontrado no arquivo.",
                    )
                return zf.read(member).decode("utf-8", errors="replace")
        except zipfile.BadZipFile as exc:
            raise HTTPException(
                status_code=422, detail="Arquivo .zip corrompido ou inválido."
            ) from exc
    return raw.decode("utf-8", errors="replace")


@router.post("/imports", response_model=ImportSummary)
async def import_whatsapp(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    lead_id: int | None = Form(None),
    lead_name: str | None = Form(None),
    db: Session = Depends(get_db),
) -> ImportSummary:
    raw = await file.read()
    filename = file.filename or ""
    text = _read_chat_text(raw, filename)
    phone = phone_from_filename(filename)

    try:
        summary = import_chat(
            db, text=text, phone=phone, lead_id=lead_id, lead_name=lead_name
        )
    except NotWhatsAppExportError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except WhatsAppParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        # "Lead não encontrado" → 404; demais (sem lead_id/phone) → 422.
        if "não encontrado" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    maybe_schedule_analysis(db, background_tasks, summary.leadId)
    return summary
