"""Copiloto de Vendas (P4b, REQF04) — sessões + chat agêntico (LLM mockado).

Scripta a sequência de turnos do agente via ``mock_anthropic.set_create_turns([...])``
(``tool_use`` → ``final_text``). O ``mock_embedder`` evita chamadas OpenAI quando o
``search_knowledge`` é exercido. Cobre: criar sessão com lead (título = nome), ordenação
por recência, conselho 3-paths (kind='advice'), modo KB texto, comandos slash e o
mapeamento rótulo→enum de persona no handler ``search_knowledge``.
"""

import json

from app.schemas.analysis import PersonaType
from app.schemas.copilot import SellerAdvice
from app.services import copilot as copilot_service
from app.services import rag
from tests.factories import make_course, make_lead, make_profile

# Input do suggest_messages (3 paths) que o agente "chama" quando o vendedor pede sugestões.
_SUGGEST_INPUT = {
    "reasoning": "análise",
    "paths": [
        {"title": "t1", "rationale": "r1", "message": "m1"},
        {"title": "t2", "rationale": "r2", "message": "m2"},
        {"title": "t3", "rationale": "r3", "message": "m3"},
    ],
}


def test_create_session_with_lead(db_session):
    """Sessão criada com lead → título = nome do lead; ``lead_id`` fixado."""
    lead = make_lead(db_session, name="Dra. Marina")
    session = copilot_service.create_session(db_session, lead.id)

    assert session.id is not None
    assert session.lead_id == lead.id
    assert session.title == "Dra. Marina"


def test_create_session_without_lead(db_session):
    """Sem lead → título padrão e ``lead_id`` nulo (chat só de base de conhecimento)."""
    session = copilot_service.create_session(db_session, None)
    assert session.lead_id is None
    assert session.title == "Nova conversa"


def test_list_sessions_orders_recent(db_session, mock_anthropic):
    """A sessão tocada por último (via chat) sobe ao topo da sidebar."""
    s1 = copilot_service.create_session(db_session, None)
    s2 = copilot_service.create_session(db_session, None)

    # Um chat em s1 bump seu updated_at → s1 deve passar s2.
    mock_anthropic.set_create_turns([mock_anthropic.final_text("resposta")])
    copilot_service.chat(db_session, s1.id, "pergunta")

    sessions = copilot_service.list_sessions(db_session)
    ids = [s.id for s in sessions]
    assert ids.index(s1.id) < ids.index(s2.id)
    # lastSnippet preenchido a partir da última mensagem da thread.
    top = next(s for s in sessions if s.id == s1.id)
    assert top.lastSnippet == "resposta"


def test_chat_agent_suggests_via_tool(db_session, mock_anthropic, mock_embedder):
    """Vendedor pede sugestões: agente chama suggest_messages → kind='advice' (3 paths)."""
    make_course(db_session, name="Imersão", n_cohorts=1)
    lead = make_lead(db_session, name="Dr. Paulo")
    make_profile(db_session, lead, matched_persona="Especialista Analógico")
    session = copilot_service.create_session(db_session, lead.id)

    mock_anthropic.set_create_turns(
        [
            mock_anthropic.tool_use("suggest_messages", _SUGGEST_INPUT),
            mock_anthropic.final_text("Aqui estão as sugestões."),
        ]
    )

    msg = copilot_service.chat(db_session, session.id, "Como respondo a este lead?")

    assert msg.role == "assistant"
    assert msg.kind == "advice"
    assert msg.content is None
    advice = SellerAdvice.model_validate(msg.advice)
    assert advice.reasoning == "análise"
    assert len(advice.paths) == 3

    # A thread tem 2 mensagens com sequences 0 (user) e 1 (assistant).
    stored = copilot_service.get_session(db_session, session.id)["messages"]
    assert [m.role for m in stored] == ["user", "assistant"]


def test_chat_conversational_no_suggest(db_session, mock_anthropic, mock_embedder):
    """Lead anexado mas sem pedido de sugestões: resposta conversacional kind='text'."""
    lead = make_lead(db_session, name="Dra. Bia")
    make_profile(db_session, lead, matched_persona="Especialista Analógico")
    session = copilot_service.create_session(db_session, lead.id)

    # O agente NÃO chama suggest_messages — só responde em prosa.
    mock_anthropic.set_create_turns(
        [mock_anthropic.final_text("Análise: este lead é um Especialista Analógico...")]
    )

    msg = copilot_service.chat(db_session, session.id, "O que você acha deste lead?")

    assert msg.kind == "text"
    assert msg.advice is None
    assert "Análise" in msg.content


def test_chat_kb_mode_text(db_session, mock_anthropic):
    """Sem lead anexado: turno final em texto não-JSON → mensagem kind='text'."""
    session = copilot_service.create_session(db_session, None)
    mock_anthropic.set_create_turns(
        [mock_anthropic.final_text("Resposta livre da base de conhecimento.")]
    )

    msg = copilot_service.chat(db_session, session.id, "Qual a filosofia da MR?")

    assert msg.kind == "text"
    assert msg.content == "Resposta livre da base de conhecimento."
    assert msg.advice is None


def test_chat_command_icp_calls_tool(db_session, mock_anthropic):
    """Comando /icp → modo texto; o agente chama get_icp_stats (tool roda)."""
    session = copilot_service.create_session(db_session, None)
    mock_anthropic.set_create_turns(
        [
            mock_anthropic.tool_use("get_icp_stats", {}),
            mock_anthropic.final_text("Resumo de ICP: personas e conversão."),
        ]
    )

    msg = copilot_service.chat(db_session, session.id, "", command="/icp")

    assert msg.kind == "text"
    assert "ICP" in msg.content
    # A pergunta do usuário foi persistida com o rótulo do comando.
    stored = copilot_service.get_session(db_session, session.id)["messages"]
    assert stored[0].content == "/icp"


def test_chat_command_routes_kb(db_session, mock_anthropic, mock_embedder):
    """Comando /spin → modo texto; o agente roteia para search_knowledge."""
    session = copilot_service.create_session(db_session, None)
    mock_anthropic.set_create_turns(
        [
            mock_anthropic.tool_use("search_knowledge", {"query": "SPIN implicação"}),
            mock_anthropic.final_text("Técnicas SPIN da MR."),
        ]
    )

    msg = copilot_service.chat(db_session, session.id, "", command="/spin")

    assert msg.kind == "text"
    assert "SPIN" in msg.content


def test_persona_label_to_enum_seed(db_session, monkeypatch):
    """O handler search_knowledge mapeia o rótulo PT da persona → valor do enum.

    Espiona ``rag.retrieve`` e confere que ``persona`` chega como
    ``PersonaType.FOCADO_EM_PROTESE.value`` quando o rótulo "Focado em Prótese" entra.
    """
    seen: dict = {}

    def spy_retrieve(db, query, persona=None, spin_stage=None, k=8):
        seen["persona"] = persona
        seen["query"] = query
        return []

    monkeypatch.setattr(rag, "retrieve", spy_retrieve)
    _tools, dispatch, _captured = copilot_service._build_tools(db_session)

    dispatch["search_knowledge"](query="cirurgia guiada", persona="Focado em Prótese")

    assert seen["persona"] == PersonaType.FOCADO_EM_PROTESE.value


def test_chat_persists_distinct_advice_json(db_session, mock_anthropic, mock_embedder):
    """O advice persistido é o dump JSONB do SellerAdvice capturado (3 paths)."""
    lead = make_lead(db_session, name="Dra. Lia")
    make_profile(db_session, lead)
    session = copilot_service.create_session(db_session, lead.id)
    mock_anthropic.set_create_turns(
        [
            mock_anthropic.tool_use("suggest_messages", _SUGGEST_INPUT),
            mock_anthropic.final_text("Sugestões a seguir."),
        ]
    )

    msg = copilot_service.chat(db_session, session.id, "me dá sugestões de mensagem")

    assert json.loads(json.dumps(msg.advice))["paths"][0]["title"] == "t1"


def test_get_session_404(db_session):
    """Sessão inexistente → ValueError 'não encontrada'."""
    import pytest

    with pytest.raises(ValueError, match="não encontrada"):
        copilot_service.get_session(db_session, 999_999)


def test_chat_session_404(db_session):
    """Chat em sessão inexistente → ValueError 'não encontrada'."""
    import pytest

    with pytest.raises(ValueError, match="não encontrada"):
        copilot_service.chat(db_session, 999_999, "oi")


def test_session_404_endpoint(api_client):
    """GET /copilot/sessions/{id} inexistente → 404 via router."""
    resp = api_client.get("/copilot/sessions/999999")
    assert resp.status_code == 404


def test_create_session_endpoint(api_client, db_session):
    """POST /copilot/sessions com leadId → 201 e título = nome do lead."""
    lead = make_lead(db_session, name="Lead API")
    resp = api_client.post("/copilot/sessions", json={"leadId": lead.id})
    assert resp.status_code == 201
    body = resp.json()
    assert body["leadId"] == lead.id
    assert body["title"] == "Lead API"


def test_attach_lead_to_leadless_session(db_session):
    """Sessão sem lead → attach vincula o lead e adota o nome como título."""
    session = copilot_service.create_session(db_session, None)
    assert session.lead_id is None
    lead = make_lead(db_session, name="Dr. Anexado")

    updated = copilot_service.attach_lead(db_session, session.id, lead.id)

    assert updated.lead_id == lead.id
    assert updated.title == "Dr. Anexado"


def test_attach_lead_conflict_when_already_has_lead(api_client, db_session):
    """PATCH com lead numa sessão que já tem lead → 409."""
    first = make_lead(db_session, name="Lead 1")
    second = make_lead(db_session, name="Lead 2")
    session = copilot_service.create_session(db_session, first.id)

    resp = api_client.patch(
        f"/copilot/sessions/{session.id}", json={"leadId": second.id}
    )
    assert resp.status_code == 409


def test_attach_lead_endpoint(api_client, db_session):
    """PATCH /copilot/sessions/{id} numa sessão sem lead → 200 e leadId/título setados."""
    session = copilot_service.create_session(db_session, None)
    lead = make_lead(db_session, name="Lead PATCH")

    resp = api_client.patch(
        f"/copilot/sessions/{session.id}", json={"leadId": lead.id}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["leadId"] == lead.id
    assert body["title"] == "Lead PATCH"
