"""Gatilho automático de análise no import/mensagem manual. Critério 7 (P3).

A análise auto-disparada é ASSÍNCRONA (BackgroundTasks) e só roda quando o total de
mensagens da conversa for > 3. Aqui fazemos monkeypatch de ``run_analysis_bg`` na
referência do módulo do router (um spy), para não rodar o LLM/SessionLocal reais — o
TestClient executa os BackgroundTasks de forma síncrona após a resposta.
"""

import io
from datetime import datetime, timedelta
from pathlib import Path

from app.models import Conversation, Message
from app.services.analysis import should_auto_analyze
from tests.factories import make_lead, make_seller

FIXTURES = Path(__file__).parent / "fixtures" / "whatsapp"
CLEAN_TXT = FIXTURES / "clean_chat.txt"  # 6 mensagens

# _chat.txt curto com 2 mensagens (≤3 → não dispara análise).
SMALL_CHAT = (
    "[18/01/2026, 09:15:02] ~João Pequeno: Oi, tudo bem?\n"
    "[18/01/2026, 09:16:40] MR Digital: Tudo! Como posso ajudar?\n"
)

T0 = datetime(2026, 1, 21, 10, 0, 0)


class _Spy:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def __call__(self, lead_id: int) -> None:
        self.calls.append(lead_id)


def test_should_auto_analyze_gate():
    assert should_auto_analyze(3) is False
    assert should_auto_analyze(4) is True
    assert should_auto_analyze(0) is False


def test_import_over_3_schedules_analysis(api_client, db_session, monkeypatch):
    """Import de 6 mensagens (>3) → agenda análise uma vez para o lead."""
    spy = _Spy()
    monkeypatch.setattr("app.api.routes.imports.run_analysis_bg", spy)

    make_seller(db_session)
    lead = make_lead(db_session, name="Maria Trigger")

    with CLEAN_TXT.open("rb") as f:
        resp = api_client.post(
            "/imports",
            files={"file": ("clean_chat.txt", f, "text/plain")},
            data={"lead_id": str(lead.id)},
        )
    assert resp.status_code == 200
    assert spy.calls == [lead.id]


def test_import_3_or_fewer_no_analysis(api_client, db_session, monkeypatch):
    """Import de 2 mensagens (≤3) → NÃO agenda análise."""
    spy = _Spy()
    monkeypatch.setattr("app.api.routes.imports.run_analysis_bg", spy)

    make_seller(db_session)
    lead = make_lead(db_session, name="João Small")

    resp = api_client.post(
        "/imports",
        files={"file": ("small_chat.txt", io.BytesIO(SMALL_CHAT.encode("utf-8")), "text/plain")},
        data={"lead_id": str(lead.id)},
    )
    assert resp.status_code == 200
    assert resp.json()["messagesImported"] == 2
    assert spy.calls == []


def test_manual_message_crossing_threshold_schedules(api_client, db_session, monkeypatch):
    """Mensagem manual que leva a conversa de 3 → 4 mensagens agenda análise."""
    spy = _Spy()
    monkeypatch.setattr("app.api.routes.imports.run_analysis_bg", spy)

    make_seller(db_session)
    lead = make_lead(db_session, name="Carlos Threshold")
    conv = Conversation(lead_id=lead.id, channel="WhatsApp")
    db_session.add(conv)
    db_session.flush()
    for i in range(3):  # 3 mensagens pré-existentes (gate ainda fechado)
        db_session.add(
            Message(
                conversation_id=conv.id,
                text=f"msg {i}",
                sent=bool(i % 2),
                channel="WhatsApp",
                sent_at=T0 + timedelta(seconds=30 * i),
                sequence=i,
            )
        )
    db_session.flush()

    resp = api_client.post(
        f"/leads/{lead.id}/messages", json={"text": "Quarta mensagem"}
    )
    assert resp.status_code == 201
    assert spy.calls == [lead.id]


def test_manual_message_below_threshold_no_analysis(api_client, db_session, monkeypatch):
    """Mensagem manual que mantém a conversa em ≤3 mensagens NÃO agenda análise."""
    spy = _Spy()
    monkeypatch.setattr("app.api.routes.imports.run_analysis_bg", spy)

    make_seller(db_session)
    lead = make_lead(db_session, name="Diana Below")

    resp = api_client.post(
        f"/leads/{lead.id}/messages", json={"text": "Primeira mensagem"}
    )
    assert resp.status_code == 201
    assert spy.calls == []
