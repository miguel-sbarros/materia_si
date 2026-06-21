"""Leitura de conversas — thread por lead e feed do painel de Conversas (P2)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Conversation
from app.schemas.conversation import ConversationSummary, MessageOut

CHANNEL = "WhatsApp"


def get_lead_conversation(db: Session, lead_id: int) -> dict:
    """Thread WhatsApp do lead: ``{conversationId, messages: [MessageOut]}``."""
    conv = db.scalar(
        select(Conversation)
        .where(Conversation.lead_id == lead_id, Conversation.channel == CHANNEL)
        .options(joinedload(Conversation.messages))
    )
    if conv is None:
        return {"conversationId": None, "messages": []}
    return {
        "conversationId": conv.id,
        "messages": [MessageOut.model_validate(m) for m in conv.messages],
    }


def list_conversations(db: Session) -> list[ConversationSummary]:
    """Feed do painel esquerdo: 1 linha por conversa, ordenada por atividade recente."""
    convs = db.scalars(
        select(Conversation)
        .options(joinedload(Conversation.lead), joinedload(Conversation.messages))
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc())
    ).unique().all()

    summaries = []
    for conv in convs:
        last = conv.messages[-1].text if conv.messages else None
        summaries.append(
            ConversationSummary(
                id=conv.id,
                leadId=conv.lead_id,
                name=conv.lead.name if conv.lead else "—",
                lastMessage=last,
                lastMessageAt=conv.last_message_at,
                unread=conv.unread,
                channel=conv.channel,
            )
        )
    return summaries
