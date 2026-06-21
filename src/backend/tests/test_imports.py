"""Import de WhatsApp + mensagem manual + leitura de conversas. Critérios 7–11 (REQF03).

Usa ``api_client`` (get_db na sessão isolada) + factories + fixtures commitadas.
"""

from pathlib import Path

from sqlalchemy import func, select

from app.models import Conversation, Lead, Message
from tests.factories import make_lead, make_seller

FIXTURES = Path(__file__).parent / "fixtures" / "whatsapp"
CLEAN_TXT = FIXTURES / "clean_chat.txt"
NOT_WPP_TXT = FIXTURES / "not_whatsapp.txt"
CHAT_ZIP = FIXTURES / "WhatsApp Chat - +55 11 99999-0001.zip"


def test_import_txt(api_client, db_session):
    """Upload de .txt COM lead_id pré-existente → mensagens importadas, conversa criada."""
    make_seller(db_session)
    lead = make_lead(db_session, name="Maria Silva")

    with CLEAN_TXT.open("rb") as f:
        resp = api_client.post(
            "/imports",
            files={"file": ("clean_chat.txt", f, "text/plain")},
            data={"lead_id": str(lead.id)},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["leadId"] == lead.id
    assert body["createdLead"] is False
    assert body["messagesImported"] == 6

    conv = db_session.scalar(select(Conversation).where(Conversation.lead_id == lead.id))
    assert conv is not None
    count = db_session.scalar(
        select(func.count()).select_from(Message).where(Message.conversation_id == conv.id)
    )
    assert count == 6


def test_import_zip(api_client, db_session):
    """Upload do .zip (sem lead_id) → cria lead pelo telefone do nome + conversa + mensagens."""
    make_seller(db_session)

    with CHAT_ZIP.open("rb") as f:
        resp = api_client.post(
            "/imports",
            files={"file": (CHAT_ZIP.name, f, "application/zip")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["createdLead"] is True
    assert body["messagesImported"] == 6
    assert body["leadName"] == "Maria Silva"  # eco do nome p/ o modal de posicionamento

    lead = db_session.get(Lead, body["leadId"])
    assert lead is not None
    assert lead.external_user_id == "+55 11 99999-0001"
    assert lead.name == "Maria Silva"  # inferido do remetente ~


def test_import_txt_create_new_lead(api_client, db_session):
    """Upload de .txt nu (sem telefone/lead_id) + lead_name → cria lead novo + importa."""
    make_seller(db_session)

    with CLEAN_TXT.open("rb") as f:
        resp = api_client.post(
            "/imports",
            files={"file": ("clean_chat.txt", f, "text/plain")},
            data={"lead_name": "Dr. Teste"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["createdLead"] is True
    assert body["messagesImported"] == 6

    lead = db_session.get(Lead, body["leadId"])
    assert lead is not None
    assert lead.name == "Dr. Teste"
    assert lead.external_user_id is None  # criado sem dedup

    conv = db_session.scalar(select(Conversation).where(Conversation.lead_id == lead.id))
    assert conv is not None
    count = db_session.scalar(
        select(func.count()).select_from(Message).where(Message.conversation_id == conv.id)
    )
    assert count == 6


def test_import_txt_no_lead_info_422(api_client, db_session):
    """Upload de .txt nu sem lead_id/lead_name/telefone → 422 (lead indefinido)."""
    make_seller(db_session)

    with CLEAN_TXT.open("rb") as f:
        resp = api_client.post(
            "/imports",
            files={"file": ("clean_chat.txt", f, "text/plain")},
        )
    assert resp.status_code == 422


def test_import_idempotent(api_client, db_session):
    """Reimportar o mesmo .zip não cria mensagens novas (UNIQUE(conv, sequence))."""
    make_seller(db_session)

    with CHAT_ZIP.open("rb") as f:
        first = api_client.post("/imports", files={"file": (CHAT_ZIP.name, f, "application/zip")})
    assert first.status_code == 200
    assert first.json()["messagesImported"] == 6

    total_after_first = db_session.scalar(select(func.count()).select_from(Message))

    with CHAT_ZIP.open("rb") as f:
        second = api_client.post("/imports", files={"file": (CHAT_ZIP.name, f, "application/zip")})
    assert second.status_code == 200
    assert second.json()["messagesImported"] == 0

    total_after_second = db_session.scalar(select(func.count()).select_from(Message))
    assert total_after_second == total_after_first


def test_import_bad_file_422(api_client, db_session):
    """Arquivo sem timestamps de WhatsApp → 422 com erro tipado."""
    make_seller(db_session)
    lead = make_lead(db_session, name="Qualquer")

    with NOT_WPP_TXT.open("rb") as f:
        resp = api_client.post(
            "/imports",
            files={"file": ("not_whatsapp.txt", f, "text/plain")},
            data={"lead_id": str(lead.id)},
        )
    assert resp.status_code == 422


def test_manual_message(api_client, db_session):
    """POST /leads/{id}/messages anexa 1 mensagem (201) à conversa do lead."""
    make_seller(db_session)
    lead = make_lead(db_session, name="Dr. Manual")

    resp = api_client.post(
        f"/leads/{lead.id}/messages", json={"text": "Mensagem manual do vendedor"}
    )
    assert resp.status_code == 201
    msg = resp.json()
    assert msg["text"] == "Mensagem manual do vendedor"
    assert msg["sent"] is True
    assert msg["sequence"] == 0

    # Segunda mensagem incrementa a sequência.
    resp2 = api_client.post(
        f"/leads/{lead.id}/messages", json={"text": "Outra", "sent": False}
    )
    assert resp2.status_code == 201
    assert resp2.json()["sequence"] == 1
    assert resp2.json()["sent"] is False


def test_get_conversation(api_client, db_session):
    """GET /leads/{id}/conversation devolve a thread; GET /conversations lista a conversa."""
    make_seller(db_session)
    lead = make_lead(db_session, name="Maria Silva")
    with CLEAN_TXT.open("rb") as f:
        api_client.post(
            "/imports",
            files={"file": ("clean_chat.txt", f, "text/plain")},
            data={"lead_id": str(lead.id)},
        )

    resp = api_client.get(f"/leads/{lead.id}/conversation")
    assert resp.status_code == 200
    thread = resp.json()
    assert thread["conversationId"] is not None
    assert len(thread["messages"]) == 6
    assert thread["messages"][0]["sequence"] == 0
    assert thread["messages"][0]["sent"] is False  # lead começa

    feed = api_client.get("/conversations")
    assert feed.status_code == 200
    rows = feed.json()
    assert any(r["leadId"] == lead.id for r in rows)
    row = next(r for r in rows if r["leadId"] == lead.id)
    assert row["name"] == "Maria Silva"
    assert row["lastMessage"]  # texto da última mensagem


def test_get_conversation_empty(api_client, db_session):
    """Lead sem conversa → messages vazio, conversationId None."""
    make_seller(db_session)
    lead = make_lead(db_session, name="Sem Conversa")
    resp = api_client.get(f"/leads/{lead.id}/conversation")
    assert resp.status_code == 200
    assert resp.json() == {"conversationId": None, "messages": []}
