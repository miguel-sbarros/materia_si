"""Persistência de Conversation/Message; ordenação por sequence; constraints. Critério 1 (P2)."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Conversation, Lead, Message
from tests.factories import make_lead


def test_conversation_message_persist(db_session):
    lead = make_lead(db_session, name="Dr. Persistência")
    conv = Conversation(lead_id=lead.id, external_user_id="5511999999999")
    db_session.add(conv)
    db_session.flush()
    db_session.add_all(
        [
            Message(conversation_id=conv.id, text="Olá, tudo bem?", sent=False, sequence=0),
            Message(conversation_id=conv.id, text="Oi! Tudo ótimo.", sent=True, sequence=1),
        ]
    )
    db_session.commit()
    db_session.expire_all()

    reloaded = db_session.scalar(select(Conversation).where(Conversation.id == conv.id))
    assert [m.sequence for m in reloaded.messages] == [0, 1]
    assert reloaded.messages[0].text == "Olá, tudo bem?"
    assert reloaded.messages[0].sent is False
    assert reloaded.messages[1].sent is True
    assert reloaded.channel == "WhatsApp"


def test_messages_ordered_by_sequence(db_session):
    lead = make_lead(db_session, name="Dra. Ordem")
    conv = Conversation(lead_id=lead.id)
    db_session.add(conv)
    db_session.flush()
    # Inseridas fora de ordem (2, 0, 1).
    db_session.add_all(
        [
            Message(conversation_id=conv.id, text="terceira", sent=False, sequence=2),
            Message(conversation_id=conv.id, text="primeira", sent=False, sequence=0),
            Message(conversation_id=conv.id, text="segunda", sent=True, sequence=1),
        ]
    )
    db_session.commit()
    db_session.expire_all()

    reloaded = db_session.scalar(select(Conversation).where(Conversation.id == conv.id))
    assert [m.sequence for m in reloaded.messages] == [0, 1, 2]
    assert [m.text for m in reloaded.messages] == ["primeira", "segunda", "terceira"]


def test_unique_conversation_sequence(db_session):
    lead = make_lead(db_session, name="Dr. Único Seq")
    conv = Conversation(lead_id=lead.id)
    db_session.add(conv)
    db_session.flush()
    db_session.add(Message(conversation_id=conv.id, text="a", sent=False, sequence=0))
    db_session.flush()

    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(Message(conversation_id=conv.id, text="b", sent=True, sequence=0))
        db_session.flush()


def test_unique_lead_channel(db_session):
    lead = make_lead(db_session, name="Dra. Único Canal")
    db_session.add(Conversation(lead_id=lead.id))
    db_session.flush()

    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(Conversation(lead_id=lead.id))
        db_session.flush()


def test_lead_conversations_relationship(db_session):
    lead = make_lead(db_session, name="Dr. Cascata")
    conv = Conversation(lead_id=lead.id)
    db_session.add(conv)
    db_session.flush()
    db_session.add(Message(conversation_id=conv.id, text="oi", sent=False, sequence=0))
    db_session.flush()

    assert [c.id for c in lead.conversations] == [conv.id]

    # Cascade: deletar o lead remove conversas + mensagens.
    lead_id = lead.id
    conv_id = conv.id
    db_session.delete(lead)
    db_session.flush()
    assert db_session.scalar(select(Lead).where(Lead.id == lead_id)) is None
    assert db_session.scalar(select(Conversation).where(Conversation.id == conv_id)) is None
    assert (
        db_session.scalar(select(Message).where(Message.conversation_id == conv_id)) is None
    )
