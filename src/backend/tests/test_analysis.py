"""analyze_lead (LLM mockado) cria/atualiza LeadProfile. Critérios 3–5, 9 (P3).

A análise faz DUAS chamadas ``parse`` (entidades + avaliação); os testes scriptam ambas via
``mock_anthropic.set_returns([ExtractedEntities(...), LeadAssessment(...)])``.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.models import Conversation, LeadProfile, Message
from app.schemas.analysis import (
    DealOutcome,
    DealOutcomeStatus,
    ExtractedEntities,
    LeadAssessment,
    PersonaType,
    SPINStage,
    persona_label,
)
from app.services.analysis import analyze_lead, classify_deal_outcome
from tests.factories import make_lead

T0 = datetime(2026, 1, 21, 10, 0, 0)


def _seed_conversation(db, lead_id, n=5):
    """Cria conversa + n mensagens alternando lead/vendedor com timestamps."""
    conv = Conversation(lead_id=lead_id, channel="WhatsApp")
    db.add(conv)
    db.flush()
    for i in range(n):
        db.add(
            Message(
                conversation_id=conv.id,
                text=f"mensagem {i}",
                sent=bool(i % 2),  # i par = lead (False), ímpar = vendedor (True)
                channel="WhatsApp",
                sent_at=T0 + timedelta(seconds=30 * i),
                sequence=i,
            )
        )
    db.flush()
    return conv


def test_analyze_creates_profile(db_session, mock_anthropic):
    lead = make_lead(db_session, name="Dr. Análise")
    _seed_conversation(db_session, lead.id, n=5)

    mock_anthropic.set_returns(
        [
            ExtractedEntities(
                especialidade="protesista",
                experiencia="+10 anos",
                cidade_estado="São Paulo/SP",
                course_interest="Master",
                dores_verbalizadas=[
                    "herança cirúrgica ruim",
                    "sem controle da cirurgia",
                ],
                desejos_expressos=[
                    "planejamento reverso",
                    "perfil de emergência ideal",
                ],
                objecoes=["a Imersão não cobre prótese"],
                comentarios=["exocad", "planejamento reverso", "reabilitador oral"],
            ),
            LeadAssessment(
                matched_persona=PersonaType.FOCADO_EM_PROTESE,
                persona_confidence=0.88,
                persona_reasoning="Fala em fase protética e perfil de emergência.",
                current_spin_stage=SPINStage.PROBLEM,
                lead_score=64,
                summary="Protesista buscando controle do fluxo cirúrgico.",
                abandon_spin_stage=SPINStage.IMPLICATION,
            ),
        ]
    )

    profile = analyze_lead(db_session, lead.id)

    assert isinstance(profile, LeadProfile)
    # Rótulo de exibição PT (não o valor do enum).
    assert profile.matched_persona == "Focado em Prótese"
    assert profile.especialidade == "protesista"
    assert profile.dores_verbalizadas == [
        "herança cirúrgica ruim",
        "sem controle da cirurgia",
    ]
    assert profile.objecoes == ["a Imersão não cobre prótese"]
    assert profile.desejos_expressos == [
        "planejamento reverso",
        "perfil de emergência ideal",
    ]
    assert profile.comentarios == ["exocad", "planejamento reverso", "reabilitador oral"]
    assert profile.current_spin_stage == "problem"
    # n=5: última msg é do lead → não abandonado → abandon_spin_stage None.
    assert profile.abandon_spin_stage is None
    assert profile.lead_score == 64
    assert profile.persona_confidence == 0.88
    # Métricas deterministas populadas (gaps de 30s alternados).
    assert profile.median_seller_latency_seconds == 30
    assert profile.median_lead_latency_seconds == 30
    assert profile.first_response_latency_seconds == 30
    # n=5: sequence 4 (par) = lead → última msg é do lead → não abandonado.
    assert profile.last_message_sent is False
    assert profile.is_abandoned is False
    # Metadados.
    assert profile.model_used == "claude-haiku-4-5"
    assert profile.raw is not None
    assert profile.raw["assessment"]["matched_persona"] == PersonaType.FOCADO_EM_PROTESE.value

    # Exatamente uma linha de perfil para o lead.
    count = db_session.scalar(
        select(func.count()).select_from(LeadProfile).where(
            LeadProfile.lead_id == lead.id
        )
    )
    assert count == 1


def test_reanalyze_updates_in_place(db_session, mock_anthropic):
    lead = make_lead(db_session, name="Dra. Reanálise")
    _seed_conversation(db_session, lead.id, n=4)

    mock_anthropic.set_returns(
        [
            ExtractedEntities(),
            LeadAssessment(
                matched_persona=PersonaType.INICIADO_DIGITAL,
                persona_confidence=0.6,
                lead_score=40,
                summary="Primeira análise.",
            ),
        ]
    )
    first = analyze_lead(db_session, lead.id)
    first_id = first.id
    assert first.matched_persona == "Iniciado Digital"

    # Segunda rodada: persona diferente.
    mock_anthropic.set_returns(
        [
            ExtractedEntities(),
            LeadAssessment(
                matched_persona=PersonaType.RECEM_ESPECIALIZADO,
                persona_confidence=0.9,
                lead_score=75,
                summary="Reavaliado após nova mensagem.",
                abandon_spin_stage=SPINStage.IMPLICATION,
            ),
        ]
    )
    second = analyze_lead(db_session, lead.id)

    # Mesma linha, campos atualizados.
    assert second.id == first_id
    assert second.matched_persona == "Recém-Especializado"
    assert second.lead_score == 75
    assert second.summary == "Reavaliado após nova mensagem."
    # n=4: última msg é do vendedor → abandonado → abandon_spin_stage persistido.
    assert second.is_abandoned is True
    assert second.abandon_spin_stage == "implication"

    count = db_session.scalar(
        select(func.count()).select_from(LeadProfile).where(
            LeadProfile.lead_id == lead.id
        )
    )
    assert count == 1


def test_persona_label_map():
    assert persona_label(PersonaType.INICIADO_DIGITAL) == "Iniciado Digital"
    assert persona_label(PersonaType.ESPECIALISTA_ANALOGICO) == "Especialista Analógico"
    assert persona_label(PersonaType.RECEM_ESPECIALIZADO) == "Recém-Especializado"
    assert persona_label(PersonaType.FOCADO_EM_PROTESE) == "Focado em Prótese"
    assert persona_label(PersonaType.INDETERMINADO) is None


def test_analyze_indeterminate_persona_stores_none(db_session, mock_anthropic):
    lead = make_lead(db_session, name="Dr. Indeterminado")
    _seed_conversation(db_session, lead.id, n=4)
    mock_anthropic.set_returns(
        [
            ExtractedEntities(),
            LeadAssessment(matched_persona=PersonaType.INDETERMINADO, lead_score=10),
        ]
    )
    profile = analyze_lead(db_session, lead.id)
    assert profile.matched_persona is None


def test_classify_deal_outcome_won(mock_anthropic):
    mock_anthropic.set_return(DealOutcome(status=DealOutcomeStatus.WON))
    out = classify_deal_outcome("Lead: quero fechar\nVendedor: te envio o link\nLead: paguei!")
    assert out.status == DealOutcomeStatus.WON


def test_classify_deal_outcome_lost(mock_anthropic):
    mock_anthropic.set_return(
        DealOutcome(status=DealOutcomeStatus.LOST, lost_reason="Sumiu após orçamento")
    )
    out = classify_deal_outcome("Lead: quanto custa?\nVendedor: R$ ...\n(sem resposta)")
    assert out.status == DealOutcomeStatus.LOST
    assert out.lost_reason == "Sumiu após orçamento"


def test_analyze_lead_not_found(db_session, mock_anthropic):
    with pytest.raises(ValueError, match="não encontrado"):
        analyze_lead(db_session, 999999)


def test_analyze_no_conversation(db_session, mock_anthropic):
    lead = make_lead(db_session, name="Sem Conversa")
    with pytest.raises(ValueError, match="conversa"):
        analyze_lead(db_session, lead.id)


def test_analyze_endpoint(api_client, db_session, mock_anthropic):
    """POST /leads/{id}/analyze → 200 + LeadProfileOut com os campos mapeados. Critério 6."""
    lead = make_lead(db_session, name="Dr. Endpoint")
    _seed_conversation(db_session, lead.id, n=5)

    mock_anthropic.set_returns(
        [
            ExtractedEntities(
                especialidade="protesista",
                experiencia="+10 anos",
                cidade_estado="São Paulo/SP",
                course_interest="Master",
                dores_verbalizadas=["sem controle da cirurgia"],
                desejos_expressos=["planejamento reverso"],
                objecoes=["preço alto"],
                comentarios=["exocad", "planejamento reverso", "reabilitador oral"],
            ),
            LeadAssessment(
                matched_persona=PersonaType.FOCADO_EM_PROTESE,
                persona_confidence=0.88,
                persona_reasoning="Fala em fase protética.",
                current_spin_stage=SPINStage.PROBLEM,
                lead_score=64,
                summary="Protesista buscando controle do fluxo cirúrgico.",
                abandon_spin_stage=SPINStage.IMPLICATION,
            ),
        ]
    )

    resp = api_client.post(f"/leads/{lead.id}/analyze")
    assert resp.status_code == 200
    body = resp.json()
    # Persona (rótulo de exibição PT) + entidades remapeadas em camelCase.
    assert body["persona"] == "Focado em Prótese"
    assert body["personaConfidence"] == 0.88
    assert body["personaReasoning"] == "Fala em fase protética."
    assert body["dores"] == ["sem controle da cirurgia"]
    assert body["desejos"] == ["planejamento reverso"]
    assert body["objecoes"] == ["preço alto"]
    assert body["especialidade"] == "protesista"
    assert body["experiencia"] == "+10 anos"
    assert body["cidadeEstado"] == "São Paulo/SP"
    assert body["courseInterest"] == "Master"
    assert body["comentarios"] == ["exocad", "planejamento reverso", "reabilitador oral"]
    # Diálogo + score + summary.
    assert body["currentSpinStage"] == "problem"
    assert body["leadScore"] == 64
    assert body["summary"] == "Protesista buscando controle do fluxo cirúrgico."
    # Métricas deterministas (gaps de 30s alternados; última msg = lead → não abandonado).
    assert body["medianSellerLatencySeconds"] == 30
    assert body["medianLeadLatencySeconds"] == 30
    assert body["firstResponseLatencySeconds"] == 30
    assert body["lastMessageSent"] is False
    assert body["isAbandoned"] is False
    # n=5: não abandonado → abandonSpinStage None.
    assert body["abandonSpinStage"] is None
    # Metadados.
    assert body["modelUsed"] == "claude-haiku-4-5"
    assert body["updatedAt"]


def test_analyze_endpoint_lead_not_found(api_client, db_session, mock_anthropic):
    """Lead inexistente → 404."""
    resp = api_client.post("/leads/999999/analyze")
    assert resp.status_code == 404


def test_analyze_endpoint_no_conversation(api_client, db_session, mock_anthropic):
    """Lead sem conversa → 422."""
    lead = make_lead(db_session, name="Sem Conversa Endpoint")
    resp = api_client.post(f"/leads/{lead.id}/analyze")
    assert resp.status_code == 422


@pytest.mark.integration
def test_live_extraction(db_session):
    """Extração real (LLM ao vivo) devolve um LeadProfile válido. Critério 9.

    Roda só com ``-m integration`` (precisa de ANTHROPIC_API_KEY). Não roda na suíte mockada.
    """
    lead = make_lead(db_session, name="Dr. Live")
    conv = Conversation(lead_id=lead.id, channel="WhatsApp")
    db_session.add(conv)
    db_session.flush()
    turns = [
        (False, "Faço implante há mais de 30 anos, sempre à mão livre."),
        (True, "Que experiência incrível! O que te traz ao digital agora?"),
        (False, "Meu protético está se aposentando e quero mais autonomia."),
        (True, "Faz sentido. A tecnologia conecta sua experiência ao fluxo digital."),
        (False, "Mas não sou expert em informática. 3 dias bastam?"),
    ]
    for i, (sent, txt) in enumerate(turns):
        db_session.add(
            Message(
                conversation_id=conv.id,
                text=txt,
                sent=sent,
                channel="WhatsApp",
                sent_at=T0 + timedelta(minutes=i),
                sequence=i,
            )
        )
    db_session.flush()

    profile = analyze_lead(db_session, lead.id)
    assert isinstance(profile, LeadProfile)
    assert profile.summary
    assert profile.model_used == "claude-haiku-4-5"
    # current_spin_stage deve ser um SPINStage válido (ou None).
    assert profile.current_spin_stage in {
        "situation",
        "problem",
        "implication",
        "need_payoff",
        None,
    }
