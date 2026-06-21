"""Cold start: popula o DB a partir de ``WhatsApp Chat - *.zip`` (re-executável).

Todos os chats referem-se à turma **"Imersão em Implantodontia Digital — Out/25"** (já
ocorrida em 30/10–01/11/2025), então cada deal nasce FECHADO. Para cada zip com **>= 3
mensagens** (conversas menores são PULADAS por inteiro — não viram lead): importa o lead +
conversa + mensagens, roda a análise de IA (``LeadProfile``) e classifica o desfecho
comercial (won/lost) com o LLM, criando um deal fechado na turma.

Idempotente: reimportar não duplica (``UNIQUE`` em mensagens e em ``(lead, cohort)``); a
análise pula leads que já têm perfil (use ``--reanalyze`` para reprocessar). Cada lead é
commitado individualmente, então um lote interrompido retoma de onde parou.

Precisa de ``ANTHROPIC_API_KEY`` (usa o LLM real). Uso:
    python scripts/populate_chats.py --dir /data/Chats_21-01-2026
    python scripts/populate_chats.py --dir /data/Chats_21-01-2026 --reanalyze
"""

import argparse
import hashlib
import zipfile
from datetime import date
from pathlib import Path

from sqlalchemy import select

from app.core.constants import CohortStatus, DealStatus
from app.db.session import SessionLocal
from app.models import Cohort, Conversation, Course, Deal, LeadProfile, Message
from app.schemas.analysis import DealOutcomeStatus
from app.services.analysis import analyze_lead, classify_deal_outcome
from app.services.deals import create_closed_deal
from app.services.imports import import_chat
from app.services.whatsapp_parser import (
    WhatsAppParseError,
    parse_chat,
    phone_from_filename,
)

DEFAULT_DIR = "/data/Chats_21-01-2026"
COURSE_NAME = "Imersão em Implantodontia Digital"
COHORT_NAME = "Imersão em Implantodontia Digital — Out/25"
MIN_MESSAGES = 3  # conversas com menos de 3 mensagens são puladas por inteiro
CHANNEL = "WhatsApp"


def _ensure_cohort(session) -> Cohort:
    """Garante o curso Imersão + a turma Out/25 (finished). Idempotente."""
    course = session.scalar(select(Course).where(Course.name == COURSE_NAME))
    if course is None:
        course = Course(name=COURSE_NAME, modality="Presencial", active=True)
        session.add(course)
        session.flush()
    cohort = session.scalar(
        select(Cohort).where(Cohort.course_id == course.id, Cohort.name == COHORT_NAME)
    )
    if cohort is None:
        cohort = Cohort(
            course_id=course.id,
            name=COHORT_NAME,
            start_date=date(2025, 10, 30),
            end_date=date(2025, 11, 1),
            capacity=40,
            price_per_slot=course.price,
            status=CohortStatus.FINISHED,
        )
        session.add(cohort)
        session.flush()
    session.commit()
    return cohort


def _read_chat_from_zip(zip_path: Path) -> str | None:
    with zipfile.ZipFile(zip_path) as zf:
        member = next((n for n in zf.namelist() if n.endswith("_chat.txt")), None)
        if member is None:
            return None
        return zf.read(member).decode("utf-8", errors="replace")


def _dedup_key(filename: str) -> str | None:
    """Chave de dedup estável a partir do nome do arquivo (cabe em ``phone`` varchar(40)).

    Arquivos nomeados por telefone → o próprio telefone. Arquivos nomeados por pessoa
    (token > 40 chars) → ``wa-<hash>`` curto e estável (idempotente). O nome real do lead
    vem do chat (``infer_lead_name``), não deste token.
    """
    token = phone_from_filename(filename)
    if not token:
        return None
    token = token.strip()
    if len(token) <= 40:
        return token
    return "wa-" + hashlib.sha1(token.encode("utf-8")).hexdigest()[:16]


def _transcript_for(session, lead_id: int) -> str:
    """Transcrito 'Lead:/Vendedor:' da conversa do lead (para a classificação de desfecho)."""
    conv = session.scalar(
        select(Conversation).where(
            Conversation.lead_id == lead_id, Conversation.channel == CHANNEL
        )
    )
    if conv is None:
        return ""
    msgs = session.scalars(
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.sequence)
    ).all()
    return "\n".join(("Vendedor" if m.sent else "Lead") + f": {m.text}" for m in msgs)


def _has_profile(session, lead_id: int) -> bool:
    return (
        session.scalar(select(LeadProfile.id).where(LeadProfile.lead_id == lead_id))
        is not None
    )


def run(directory: str, *, reanalyze: bool = False) -> None:
    base = Path(directory)
    if not base.is_dir():
        print(f"Diretório não encontrado: {directory}")
        return
    zips = sorted(base.glob("WhatsApp Chat - *.zip"))
    if not zips:
        print(f"Nenhum 'WhatsApp Chat - *.zip' em {directory}.")
        return

    stats = {
        "imported": 0,
        "skipped_short": 0,
        "parse_err": 0,
        "analyzed": 0,
        "won": 0,
        "lost": 0,
    }

    with SessionLocal() as session:
        cohort = _ensure_cohort(session)
        for zip_path in zips:
            text = _read_chat_from_zip(zip_path)
            if text is None:
                print(f"  ⚠️  {zip_path.name}: sem _chat.txt, pulando.")
                stats["parse_err"] += 1
                continue
            # Conta mensagens ANTES de importar — pula conversas com < 3 (decisão do usuário).
            try:
                parsed = parse_chat(text)
            except WhatsAppParseError as exc:
                print(f"  ⚠️  {zip_path.name}: {exc}")
                stats["parse_err"] += 1
                continue
            if len(parsed) < MIN_MESSAGES:
                stats["skipped_short"] += 1
                continue

            key = _dedup_key(zip_path.name)
            try:
                summary = import_chat(session, text=text, phone=key)
            except Exception as exc:  # noqa: BLE001 — um zip ruim não aborta o lote.
                session.rollback()
                print(f"  ⚠️  {zip_path.name}: {exc}")
                stats["parse_err"] += 1
                continue
            lead_id = summary.leadId
            stats["imported"] += 1

            # Análise de IA (LeadProfile) — pula se já tem perfil e não --reanalyze.
            if reanalyze or not _has_profile(session, lead_id):
                try:
                    analyze_lead(session, lead_id)
                    stats["analyzed"] += 1
                except Exception as exc:  # noqa: BLE001 — análise não aborta o lote.
                    session.rollback()
                    print(f"  ⚠️  análise lead {lead_id}: {exc}")

            # Desfecho comercial → deal fechado na turma Out/25 (idempotente).
            existing = session.scalar(
                select(Deal).where(
                    Deal.lead_id == lead_id, Deal.cohort_id == cohort.id
                )
            )
            if existing is None:
                try:
                    outcome = classify_deal_outcome(_transcript_for(session, lead_id))
                    if outcome.status == DealOutcomeStatus.WON:
                        create_closed_deal(
                            session,
                            lead_id=lead_id,
                            cohort_id=cohort.id,
                            status=DealStatus.WON,
                        )
                        stats["won"] += 1
                    else:
                        reason = (
                            outcome.lost_reason.strip() or "Sem evidência de matrícula"
                        )
                        create_closed_deal(
                            session,
                            lead_id=lead_id,
                            cohort_id=cohort.id,
                            status=DealStatus.LOST,
                            lost_reason=reason,
                        )
                        stats["lost"] += 1
                except Exception as exc:  # noqa: BLE001 — desfecho não aborta o lote.
                    session.rollback()
                    print(f"  ⚠️  desfecho lead {lead_id}: {exc}")

    print(
        f"Importados {stats['imported']} | pulados <3 msgs {stats['skipped_short']} | "
        f"erros {stats['parse_err']} | analisados {stats['analyzed']} | "
        f"deals won {stats['won']} / lost {stats['lost']}."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cold start: importa + analisa + fecha deals de exports de WhatsApp."
    )
    parser.add_argument("--dir", default=DEFAULT_DIR, help="Diretório com os .zip")
    parser.add_argument(
        "--reanalyze",
        action="store_true",
        help="Reprocessa a análise mesmo de leads que já têm perfil.",
    )
    args = parser.parse_args()
    run(args.dir, reanalyze=args.reanalyze)
