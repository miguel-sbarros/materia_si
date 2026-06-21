"""Import de conversas do WhatsApp + mensagem manual (P2, REQF03).

``import_chat`` resolve/cria o lead, faz upsert da conversa (1 por lead+canal) e insere
as mensagens parseadas pulando ``sequence`` já existentes (re-import idempotente).
``add_manual_message`` anexa uma única mensagem ao fim da conversa do lead.

Erros de parsing (``EmptyChatError``/``NotWhatsAppExportError``) propagam para o router,
que os mapeia para 422. Auth diferida: leads criados aqui herdam o seller seedado.
"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Conversation, Lead, Message
from app.schemas.conversation import ImportSummary
from app.services.leads import _current_seller
from app.services.whatsapp_parser import infer_lead_name, parse_chat

CHANNEL = "WhatsApp"


def _get_or_create_conversation(
    db: Session, lead_id: int, *, source: str | None = None, external_user_id: str | None = None
) -> Conversation:
    conv = db.scalar(
        select(Conversation).where(
            Conversation.lead_id == lead_id, Conversation.channel == CHANNEL
        )
    )
    if conv is None:
        conv = Conversation(
            lead_id=lead_id, channel=CHANNEL, source=source, external_user_id=external_user_id
        )
        db.add(conv)
        db.flush()
    else:
        if source is not None:
            conv.source = source
        if external_user_id is not None:
            conv.external_user_id = external_user_id
    return conv


def import_chat(
    db: Session,
    *,
    text: str,
    phone: str | None = None,
    lead_id: int | None = None,
    lead_name: str | None = None,
    source: str = "import",
) -> ImportSummary:
    """Importa um ``_chat.txt`` para o lead (por id, telefone do nome do arquivo, ou novo lead).

    Resolução do lead:
    - ``lead_id`` informado → usa o lead (ValueError se não existir → 404 no router).
    - senão ``phone`` → upsert por ``external_user_id == phone`` (nome = ``lead_name`` se
      informado, senão inferido do chat).
    - senão ``lead_name`` → cria um lead NOVO com esse nome (sem ``external_user_id``, sem dedup).
    - senão → ValueError (→ 422 no router).
    """
    created_lead = False
    name_override = lead_name.strip() if lead_name and lead_name.strip() else None

    if lead_id is not None:
        lead = db.get(Lead, lead_id)
        if lead is None:
            raise ValueError("Lead não encontrado")
    elif phone:
        lead = db.scalar(select(Lead).where(Lead.external_user_id == phone))
        if lead is None:
            seller = _current_seller(db)
            lead = Lead(
                name=name_override or infer_lead_name(text) or phone,
                phone=phone,
                external_user_id=phone,
                source=source,
                assignee_id=seller.id if seller else None,
            )
            db.add(lead)
            db.flush()
            created_lead = True
    elif name_override:
        seller = _current_seller(db)
        lead = Lead(
            name=name_override,
            source=source,
            assignee_id=seller.id if seller else None,
        )
        db.add(lead)
        db.flush()
        created_lead = True
    else:
        raise ValueError(
            "Informe lead_id, lead_name ou um arquivo .zip com telefone no nome."
        )

    parsed = parse_chat(text)  # pode levantar EmptyChatError/NotWhatsAppExportError

    conv = _get_or_create_conversation(
        db, lead.id, source=source, external_user_id=phone
    )

    existing_seqs = set(
        db.scalars(
            select(Message.sequence).where(Message.conversation_id == conv.id)
        ).all()
    )

    imported = 0
    last_at: datetime | None = conv.last_message_at
    for pm in parsed:
        if pm.sequence in existing_seqs:
            continue
        db.add(
            Message(
                conversation_id=conv.id,
                text=pm.text,
                sent=pm.sent,
                channel=CHANNEL,
                sent_at=pm.sent_at,
                sequence=pm.sequence,
            )
        )
        imported += 1
        if last_at is None or pm.sent_at > last_at:
            last_at = pm.sent_at

    if last_at is not None:
        conv.last_message_at = last_at
    # Não lida se a última mensagem (maior sequence) é do lead.
    if parsed:
        conv.unread = not parsed[-1].sent

    db.commit()
    db.refresh(conv)
    return ImportSummary(
        leadId=lead.id,
        leadName=lead.name,
        conversationId=conv.id,
        messagesImported=imported,
        createdLead=created_lead,
    )


def add_manual_message(
    db: Session, *, lead_id: int, text: str, sent: bool = True
) -> Message:
    """Anexa 1 mensagem ao fim da conversa do lead (cria a conversa se necessário)."""
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead não encontrado")

    conv = _get_or_create_conversation(db, lead.id)
    next_seq = db.scalar(
        select(func.coalesce(func.max(Message.sequence), -1)).where(
            Message.conversation_id == conv.id
        )
    )
    now = datetime.now()
    msg = Message(
        conversation_id=conv.id,
        text=text,
        sent=sent,
        channel=CHANNEL,
        sent_at=now,
        sequence=next_seq + 1,
    )
    db.add(msg)
    conv.last_message_at = now
    conv.unread = not sent  # mensagem do lead deixa não lida; do vendedor zera
    db.commit()
    db.refresh(msg)
    return msg
