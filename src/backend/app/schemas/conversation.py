"""Schemas de conversa/mensagem (P2, REQF03).

Wire em camelCase (mesmo padrão de DealCard/LeadDetail). ``MessageOut`` é montado a
partir do ORM (``from_attributes``): os campos camelCase leem os atributos snake_case
via ``validation_alias``.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    text: str
    sent: bool
    sentAt: datetime | None = Field(default=None, validation_alias="sent_at")
    sequence: int
    read: bool


class ConversationSummary(BaseModel):
    id: int
    leadId: int
    name: str
    lastMessage: str | None = None
    lastMessageAt: datetime | None = None
    unread: bool
    channel: str


class ImportSummary(BaseModel):
    leadId: int
    leadName: str
    conversationId: int
    messagesImported: int
    createdLead: bool


class ManualMessageIn(BaseModel):
    text: str
    sent: bool = True
