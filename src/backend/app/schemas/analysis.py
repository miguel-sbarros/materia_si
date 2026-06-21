"""Schemas de análise de conversa (P3, REQF08).

Portados de ``sales_context_system/app/models/graph_schemas.py`` sem ``pydantic_ai``,
LangGraph nem timestamps/bits do Neo4j.

A análise do LLM é feita em **DUAS chamadas ``messages.parse`` pequenas** (``ExtractedEntities``
e ``LeadAssessment``), e não em um único schema grande. Motivo: um único ``output_format`` com
~14 campos + enums estourava o compilador de gramática da saída estruturada da Anthropic
(``400 invalid_request_error: "Grammar compilation timed out."``). Dois schemas enxutos
compilam rápido. ``ChatMetrics`` é o resultado puro do cálculo determinista (não vai ao LLM).
"""

import unicodedata
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SPINStage(StrEnum):
    """Estágios da metodologia SPIN Selling (propriedade do diálogo)."""

    SITUATION = "situation"
    PROBLEM = "problem"
    IMPLICATION = "implication"
    NEED_PAYOFF = "need_payoff"


class PersonaType(StrEnum):
    """Personas mapeadas da MR Digital (valores herdados do projeto Octo)."""

    INICIADO_DIGITAL = "001_iniciado_digital"
    ESPECIALISTA_ANALOGICO = "002_especialista_analogico"
    RECEM_ESPECIALIZADO = "003_recem_especializado"
    FOCADO_EM_PROTESE = "004_protesista"
    INDETERMINADO = "indeterminado"


# Mapeamento PersonaType → rótulo de exibição (casa com `personaMeta` no front).
PERSONA_LABELS: dict[PersonaType, str | None] = {
    PersonaType.INICIADO_DIGITAL: "Iniciado Digital",
    PersonaType.ESPECIALISTA_ANALOGICO: "Especialista Analógico",
    PersonaType.RECEM_ESPECIALIZADO: "Recém-Especializado",
    PersonaType.FOCADO_EM_PROTESE: "Focado em Prótese",
    PersonaType.INDETERMINADO: None,
}


def persona_label(p: PersonaType) -> str | None:
    """Rótulo de exibição PT de uma persona (``None`` para indeterminado)."""

    return PERSONA_LABELS.get(p)


# Mapa reverso: rótulo PT de exibição E nome de nó da KB → PersonaType.
# Usado pelo ingest/RAG e pelo copiloto para mapear o ``matched_persona`` (rótulo PT
# guardado em ``LeadProfile``) ou um nome de nó-persona da KB para o valor do enum.
# A ``LeadProfile.matched_persona`` guarda um rótulo PT, mas o ``persona`` do chunk da
# KB é o valor do enum — este mapa resolve o descasamento.
LABEL_TO_PERSONA: dict[str, PersonaType] = {
    # Rótulos PT de exibição (de PERSONA_LABELS).
    "iniciado digital": PersonaType.INICIADO_DIGITAL,
    "especialista analogico": PersonaType.ESPECIALISTA_ANALOGICO,
    "recem-especializado": PersonaType.RECEM_ESPECIALIZADO,
    "recem especializado": PersonaType.RECEM_ESPECIALIZADO,
    "focado em protese": PersonaType.FOCADO_EM_PROTESE,
    # Valores do enum (caso já venha mapeado).
    PersonaType.INICIADO_DIGITAL.value: PersonaType.INICIADO_DIGITAL,
    PersonaType.ESPECIALISTA_ANALOGICO.value: PersonaType.ESPECIALISTA_ANALOGICO,
    PersonaType.RECEM_ESPECIALIZADO.value: PersonaType.RECEM_ESPECIALIZADO,
    PersonaType.FOCADO_EM_PROTESE.value: PersonaType.FOCADO_EM_PROTESE,
}


def _normalize_label(text: str) -> str:
    """Normaliza um rótulo: remove artigo inicial 'O '/'A ', baixa caixa, tira acentos."""

    s = text.strip()
    low = s.lower()
    for artigo in ("o ", "a "):
        if low.startswith(artigo):
            s = s[len(artigo):]
            break
    s = s.lower()
    # Remove acentos (NFD → descarta os combining marks).
    s = "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))
    return s.strip()


def label_to_persona(text: str | None) -> PersonaType | None:
    """Mapeia um rótulo PT (ou nome de nó da KB) para ``PersonaType`` (``None`` se indeterminado).

    Normaliza o texto (tira artigo inicial, caixa, acentos) e casa por palavra-chave —
    robusto a variações como "O Iniciado Digital", "iniciado_digital", "Especialista Analógico".
    """

    if not text:
        return None
    norm = _normalize_label(text)
    if not norm:
        return None
    # Casamento exato primeiro (rótulos e valores de enum conhecidos).
    if norm in LABEL_TO_PERSONA:
        return LABEL_TO_PERSONA[norm]
    # Casamento difuso por palavra-chave.
    if "iniciado" in norm:
        return PersonaType.INICIADO_DIGITAL
    if "analogico" in norm:
        return PersonaType.ESPECIALISTA_ANALOGICO
    if "recem" in norm:
        return PersonaType.RECEM_ESPECIALIZADO
    if "protes" in norm:
        return PersonaType.FOCADO_EM_PROTESE
    return None


class ExtractedEntities(BaseModel):
    """1ª chamada do LLM (``output_format``): entidades extraídas da conversa (Etapa 1).

    Enxuto para a gramática da saída estruturada: **sem campos opcionais** (uniões com
    ``null`` viram ``anyOf`` e incham a gramática) — tudo REQUIRED com default; sem evidência
    → ``""`` ou ``[]``. ``comentarios`` engloba hardware/software, termos técnicos e marcadores
    de contexto num único campo compacto (antes eram três).
    """

    especialidade: str = Field("", description="Área de atuação ('' se ausente)")
    experiencia: str = Field("", description="Nível de experiência ('' se ausente)")
    cidade_estado: str = Field("", description="Cidade/estado ('' se ausente)")
    course_interest: str = Field("", description="Curso de interesse ('' se ausente)")
    dores_verbalizadas: list[str] = Field(
        default_factory=list, description="Problemas, frustrações ou dificuldades"
    )
    desejos_expressos: list[str] = Field(
        default_factory=list, description="Objetivos, metas ou o que o lead busca"
    )
    objecoes: list[str] = Field(
        default_factory=list,
        description="Objeções de venda (preço, tempo, etc.) — distinto de dores",
    )
    comentarios: list[str] = Field(
        default_factory=list,
        description=(
            "Informações úteis diversas: hardware/software citados (TRIOS, exocad…), "
            "termos técnicos (cirurgia guiada, planejamento reverso…) e marcadores de "
            "contexto (indicado por colega, protético se aposentando…)."
        ),
    )


class LeadAssessment(BaseModel):
    """2ª chamada do LLM (``output_format``): persona + SPIN + qualificação (Etapas 3).

    Schema pequeno (7 campos) para a gramática compilar rápido. SPIN é o ``SPINStage`` enum
    (decisão do produto: nunca string livre). ``abandon_spin_stage`` é só significativo quando
    a conversa de fato esfriou — quem decide isso é a métrica determinista ``is_abandoned``;
    aqui o modelo sempre devolve um estágio (o do último engajamento do lead).
    """

    matched_persona: PersonaType = Field(
        PersonaType.INDETERMINADO, description="Persona ('indeterminado' se incerto)"
    )
    persona_confidence: float = Field(0.0, ge=0.0, le=1.0)
    persona_reasoning: str = Field("", description="Justificativa da persona")
    current_spin_stage: SPINStage = Field(
        SPINStage.SITUATION, description="Estágio SPIN atual do diálogo"
    )
    abandon_spin_stage: SPINStage = Field(
        SPINStage.SITUATION,
        description="Estágio SPIN no último engajamento do lead (usado só se abandonado)",
    )
    lead_score: int = Field(0, description="Score de qualificação 0–100 (0 se incerto)")
    summary: str = Field("", description="Resumo conciso da conversa")


class DealOutcomeStatus(StrEnum):
    """Desfecho comercial fechado de uma conversa histórica (cold-start)."""

    WON = "won"
    LOST = "lost"


class DealOutcome(BaseModel):
    """Classificação do desfecho comercial (won/lost) de uma conversa já encerrada.

    Schema mínimo (cold-start): a turma Imersão Out/25 já aconteceu, então todo deal é fechado —
    o LLM decide se o lead matriculou (won) ou não (lost). Na dúvida → lost.
    """

    status: DealOutcomeStatus = Field(
        DealOutcomeStatus.LOST, description="won se matriculou; lost caso contrário"
    )
    lost_reason: str = Field(
        "", description="Motivo curto da perda (preencher quando status=lost)"
    )


class ChatMetrics(BaseModel):
    """Métricas deterministas da conversa (calculadas por timestamps; não vão ao LLM)."""

    median_seller_latency_seconds: int | None = None
    median_lead_latency_seconds: int | None = None
    first_response_latency_seconds: int | None = None
    last_message_sent: bool | None = None
    is_abandoned: bool = False


class LeadProfileOut(BaseModel):
    """Resposta do ``POST /leads/{id}/analyze`` — wire em camelCase a partir do ORM.

    Lê os atributos snake_case do ``LeadProfile`` via ``validation_alias`` e os expõe em
    camelCase. ``matched_persona`` já guarda o rótulo de exibição PT (``None`` p/
    indeterminado); ``dores_verbalizadas``/``desejos_expressos`` viram ``dores``/``desejos``.
    Colunas de lista podem ser ``NULL`` no banco → coagidas para ``[]`` (o front sempre
    recebe lista).
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # Persona.
    persona: str | None = Field(default=None, validation_alias="matched_persona")
    personaConfidence: float | None = Field(
        default=None, validation_alias="persona_confidence"
    )
    personaReasoning: str | None = Field(
        default=None, validation_alias="persona_reasoning"
    )
    # Entidades.
    especialidade: str | None = None
    experiencia: str | None = None
    cidadeEstado: str | None = Field(default=None, validation_alias="cidade_estado")
    courseInterest: str | None = Field(default=None, validation_alias="course_interest")
    dores: list[str] = Field(
        default_factory=list, validation_alias="dores_verbalizadas"
    )
    desejos: list[str] = Field(
        default_factory=list, validation_alias="desejos_expressos"
    )
    objecoes: list[str] = Field(default_factory=list)
    comentarios: list[str] = Field(default_factory=list)
    # Diálogo.
    currentSpinStage: str | None = Field(
        default=None, validation_alias="current_spin_stage"
    )
    leadScore: int | None = Field(default=None, validation_alias="lead_score")
    summary: str | None = None
    # Métricas da conversa.
    medianSellerLatencySeconds: int | None = Field(
        default=None, validation_alias="median_seller_latency_seconds"
    )
    medianLeadLatencySeconds: int | None = Field(
        default=None, validation_alias="median_lead_latency_seconds"
    )
    firstResponseLatencySeconds: int | None = Field(
        default=None, validation_alias="first_response_latency_seconds"
    )
    lastMessageSent: bool | None = Field(
        default=None, validation_alias="last_message_sent"
    )
    isAbandoned: bool = Field(default=False, validation_alias="is_abandoned")
    abandonSpinStage: str | None = Field(
        default=None, validation_alias="abandon_spin_stage"
    )
    # Metadados.
    modelUsed: str | None = Field(default=None, validation_alias="model_used")
    updatedAt: datetime | None = Field(default=None, validation_alias="updated_at")

    @field_validator("dores", "desejos", "objecoes", "comentarios", mode="before")
    @classmethod
    def _none_to_list(cls, v: object) -> object:
        """Colunas JSONB nuláveis: ``None`` → ``[]`` (o front sempre recebe lista)."""
        return v if v is not None else []
