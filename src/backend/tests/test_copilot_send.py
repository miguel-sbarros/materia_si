"""Send-to-history (P4b, C-08/C-09): uma mensagem sugerida pelo copiloto enviada via
``POST /leads/{id}/messages`` cai no histórico WhatsApp do lead (tabela ``messages``) e é
uma LINHA DISTINTA de qualquer ``CopilotMessage`` — prova que as duas tabelas são separadas.

Reaproveita o seam já existente (``add_manual_message``); não há backend novo aqui.
"""

from sqlalchemy import func, select

from app.models import CopilotMessage, Message
from app.services import copilot as copilot_service
from app.services.conversations import get_lead_conversation
from tests.factories import make_lead


def test_send_suggested_message_lands_in_whatsapp_history(api_client, db_session):
    """A mensagem sugerida vira uma mensagem WhatsApp do vendedor (sent=True)."""
    lead = make_lead(db_session, name="Dr. Caio")
    suggested = "Olá Dr. Caio, vi que você busca previsibilidade no fluxo digital..."

    resp = api_client.post(
        f"/leads/{lead.id}/messages", json={"text": suggested, "sent": True}
    )
    assert resp.status_code == 201

    conv = get_lead_conversation(db_session, lead.id)
    texts = [m.text for m in conv["messages"]]
    assert suggested in texts
    # Mensagem do vendedor (sent=True) no histórico do lead.
    sent_msg = next(m for m in conv["messages"] if m.text == suggested)
    assert sent_msg.sent is True


def test_sent_message_is_distinct_row_from_copilot_message(api_client, db_session):
    """A mensagem enviada vive em ``messages``, não em ``copilot_messages``."""
    lead = make_lead(db_session, name="Dra. Bia")

    # Cria uma sessão de copiloto (com sua própria tabela) para o lead.
    copilot_service.create_session(db_session, lead.id)

    suggested = "Mensagem sugerida pelo copiloto."
    resp = api_client.post(
        f"/leads/{lead.id}/messages", json={"text": suggested, "sent": True}
    )
    assert resp.status_code == 201

    # A linha está em messages...
    in_messages = db_session.scalar(
        select(func.count()).select_from(Message).where(Message.text == suggested)
    )
    assert in_messages == 1
    # ...e NÃO em copilot_messages (tabelas distintas).
    in_copilot = db_session.scalar(
        select(func.count())
        .select_from(CopilotMessage)
        .where(CopilotMessage.content == suggested)
    )
    assert in_copilot == 0
