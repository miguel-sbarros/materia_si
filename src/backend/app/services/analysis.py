"""Motor de análise de conversa (P3, REQF08).

- ``compute_chat_metrics``: função PURA (sem DB, sem LLM) — latências de resposta e ponto
  de abandono a partir dos timestamps das mensagens.
- ``analyze_lead``: carrega a conversa do lead, calcula as métricas deterministas, chama o
  LLM em DUAS passagens estruturadas (``ExtractedEntities`` + ``LeadAssessment``) de forma
  *update-aware* e faz upsert no ``LeadProfile``. Duas chamadas pequenas em vez de um schema
  único grande — este último estourava o compilador de gramática da saída estruturada.
"""

import logging
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models import Conversation, Lead, LeadProfile, Message
from app.prompts.analysis import (
    ANALYSIS_SYSTEM_PROMPT,
    DEAL_OUTCOME_PROMPT,
    build_user_content,
)
from app.schemas.analysis import (
    ChatMetrics,
    DealOutcome,
    ExtractedEntities,
    LeadAssessment,
    PersonaType,
    persona_label,
)
from app.services.llm.client import parse_structured

CHANNEL = "WhatsApp"
AUTO_ANALYZE_MIN_MESSAGES = 3

logger = logging.getLogger(__name__)


def compute_chat_metrics(messages) -> ChatMetrics:
    """Métricas deterministas da conversa a partir de mensagens ordenadas por ``sequence``.

    ``messages`` é uma sequência de objetos com ``.sent`` (True=vendedor) e
    ``.sent_at`` (datetime|None).

    - Latência = diferença em segundos entre mensagens consecutivas de remetentes diferentes
      (uma "flip"). lead→vendedor conta como latência do VENDEDOR; vendedor→lead como
      latência do LEAD. Pares sem ``sent_at`` em qualquer ponta são ignorados.
    - ``first_response_latency_seconds`` = primeira flip lead→vendedor (1ª resposta do
      vendedor).
    - ``is_abandoned`` = True sse a última mensagem é do vendedor (lead parou de responder).
    """
    if not messages:
        return ChatMetrics()

    seller_latencies: list[float] = []
    lead_latencies: list[float] = []
    first_response: int | None = None

    for prev, cur in zip(messages, messages[1:], strict=False):
        if prev.sent == cur.sent:
            continue  # mesmo remetente: não é um turno de resposta
        if prev.sent_at is None or cur.sent_at is None:
            continue  # sem timestamps (ex.: import de all_chats.json)
        gap = (cur.sent_at - prev.sent_at).total_seconds()
        if not prev.sent and cur.sent:  # lead → vendedor
            seller_latencies.append(gap)
            if first_response is None:
                first_response = int(gap)
        else:  # vendedor → lead
            lead_latencies.append(gap)

    last_message_sent = messages[-1].sent
    return ChatMetrics(
        median_seller_latency_seconds=(
            int(median(seller_latencies)) if seller_latencies else None
        ),
        median_lead_latency_seconds=(
            int(median(lead_latencies)) if lead_latencies else None
        ),
        first_response_latency_seconds=first_response,
        last_message_sent=last_message_sent,
        is_abandoned=bool(last_message_sent),
    )


def _transcript(messages) -> str:
    """Transcrito legível: 'Lead: …' / 'Vendedor: …' por linha."""
    lines = []
    for m in messages:
        speaker = "Vendedor" if m.sent else "Lead"
        lines.append(f"{speaker}: {m.text}")
    return "\n".join(lines)


def _none_if_empty(value: str) -> str | None:
    """Normaliza o sentinela "" (sem evidência) para ``None`` ao persistir.

    Os schemas de saída usam "" em vez de ``Optional`` (para evitar ``anyOf`` na gramática
    da saída estruturada); as colunas do ``LeadProfile`` permanecem nuláveis.
    """
    return value or None


def _apply_analysis(
    profile: LeadProfile,
    entities: ExtractedEntities,
    assessment: LeadAssessment,
    metrics: ChatMetrics,
    model: str,
) -> None:
    """Mapeia entidades + avaliação + métricas sobre o LeadProfile (in place)."""
    # Entidades ("" → None para manter as colunas nuláveis / contrato do wire).
    profile.especialidade = _none_if_empty(entities.especialidade)
    profile.experiencia = _none_if_empty(entities.experiencia)
    profile.cidade_estado = _none_if_empty(entities.cidade_estado)
    profile.course_interest = _none_if_empty(entities.course_interest)
    profile.dores_verbalizadas = entities.dores_verbalizadas
    profile.desejos_expressos = entities.desejos_expressos
    profile.objecoes = entities.objecoes
    profile.comentarios = entities.comentarios
    # Persona — armazena o rótulo de exibição PT (None para indeterminado).
    profile.matched_persona = persona_label(assessment.matched_persona)
    profile.persona_confidence = assessment.persona_confidence
    profile.persona_reasoning = _none_if_empty(assessment.persona_reasoning)
    # Diálogo (SPINStage enum → str ao persistir).
    profile.current_spin_stage = assessment.current_spin_stage.value
    # abandon_spin_stage só faz sentido quando a conversa esfriou (métrica determinista).
    profile.abandon_spin_stage = (
        assessment.abandon_spin_stage.value if metrics.is_abandoned else None
    )
    profile.lead_score = assessment.lead_score
    profile.summary = _none_if_empty(assessment.summary)
    # Métricas deterministas.
    profile.median_seller_latency_seconds = metrics.median_seller_latency_seconds
    profile.median_lead_latency_seconds = metrics.median_lead_latency_seconds
    profile.first_response_latency_seconds = metrics.first_response_latency_seconds
    profile.last_message_sent = metrics.last_message_sent
    profile.is_abandoned = metrics.is_abandoned
    # Metadados.
    profile.model_used = model
    profile.raw = {
        "entities": entities.model_dump(mode="json"),
        "assessment": assessment.model_dump(mode="json"),
    }


def analyze_lead(db: Session, lead_id: int) -> LeadProfile:
    """Analisa a conversa do lead e faz upsert do ``LeadProfile`` (update-aware).

    Levanta ``ValueError`` se o lead não existe ("Lead não encontrado") ou se não há
    conversa/mensagens para analisar ("Lead sem conversa para analisar").
    """
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead não encontrado")

    conv = db.scalar(
        select(Conversation).where(
            Conversation.lead_id == lead_id, Conversation.channel == CHANNEL
        )
    )
    if conv is None:
        raise ValueError("Lead sem conversa para analisar")

    messages = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.sequence)
        ).all()
    )
    if not messages:
        raise ValueError("Lead sem conversa para analisar")

    metrics = compute_chat_metrics(messages)

    existing = lead.profile
    settings = get_settings()
    user_content = build_user_content(_transcript(messages), existing)
    # Duas chamadas pequenas (evita o timeout de compilação de gramática de um schema único).
    entities: ExtractedEntities = parse_structured(
        model=settings.model_extraction,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        output_format=ExtractedEntities,
        max_tokens=1500,
    )
    assessment: LeadAssessment = parse_structured(
        model=settings.model_extraction,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
        output_format=LeadAssessment,
        max_tokens=1500,
    )

    profile = existing or LeadProfile(lead_id=lead_id)
    _apply_analysis(profile, entities, assessment, metrics, settings.model_extraction)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def classify_deal_outcome(transcript: str) -> DealOutcome:
    """Classifica o desfecho comercial (won/lost) de uma conversa histórica (cold-start).

    Chamada pequena e isolada (2 campos) — separada da análise de perfil para manter a
    gramática da saída estruturada enxuta. Na dúvida o modelo retorna ``lost``.
    """
    return parse_structured(
        model=get_settings().model_extraction,
        system=DEAL_OUTCOME_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"## CONVERSA\n{transcript}\n\nClassifique o desfecho comercial.",
            }
        ],
        output_format=DealOutcome,
        max_tokens=300,
    )


def should_auto_analyze(message_count: int) -> bool:
    """Gate da análise automática: só dispara com mais de 3 mensagens na conversa."""
    return message_count > AUTO_ANALYZE_MIN_MESSAGES


def run_analysis_bg(lead_id: int) -> None:
    """Roda ``analyze_lead`` em segundo plano com uma ``SessionLocal`` própria.

    Usado como ``BackgroundTask`` após import/mensagem manual — NUNCA deve quebrar o
    fluxo do request: qualquer erro (LLM, DB) é logado e engolido.
    """
    try:
        with SessionLocal() as db:
            analyze_lead(db, lead_id)
    except Exception:  # noqa: BLE001 — falha de análise não pode quebrar o import.
        logger.exception("Falha na análise automática do lead %s", lead_id)


__all__ = [
    "compute_chat_metrics",
    "analyze_lead",
    "classify_deal_outcome",
    "should_auto_analyze",
    "run_analysis_bg",
    "PersonaType",
]
