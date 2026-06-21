"""Schemas do copiloto de vendas (P4, REQF04).

Inclui:
- ``SellerAdvice``/``AdvicePath``: saída estruturada terminal do agente — análise
  (``reasoning``) + exatamente 3 caminhos estratégicos (``paths``), cada um com
  título, racional e mensagem WhatsApp pronta. Schema enxuto de propósito (sem enums,
  sem restrições de tamanho de lista) para a gramática da saída estruturada compilar
  rápido — a regra "exatamente 3" é cobrada no prompt e validada de forma leniente.
- Schemas de wire (camelCase) das sessões/mensagens do copiloto: ``SessionOut``,
  ``MessageOut``, ``ChatIn``, ``SessionCreate``.
- Os ``input_schema`` (JSON Schema) das ferramentas do agente, importados pelo service
  do copiloto ao montar as tool defs.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AdvicePath(BaseModel):
    """Um caminho estratégico de abordagem (distinto de um "tom")."""
    model_config = ConfigDict(extra="forbid")
    title: str = Field(description="Rótulo curto da estratégia")
    rationale: str = Field(description="Por que esta abordagem faz sentido para o lead")
    message: str = Field(description="Mensagem WhatsApp pronta para enviar (PT-BR)")


class SellerAdvice(BaseModel):
    """Saída terminal estruturada do agente quando há lead anexado.

    ``reasoning`` = análise (persona, dores, estágio SPIN, ângulo). ``paths`` = 3
    estratégias distintas. O validador é **leniente**: não falha se != 3 (o prompt pede
    3 e o modelo costuma entregar 3) — apenas garante que haja pelo menos um caminho.
    """
    model_config = ConfigDict(extra="forbid")
    reasoning: str = Field(description="Análise: persona, dores, estágio SPIN, ângulo")
    paths: list[AdvicePath] = Field(
        description="Caminhos estratégicos distintos (idealmente 3)"
    )

    @field_validator("paths")
    @classmethod
    def _at_least_one(cls, v: list[AdvicePath]) -> list[AdvicePath]:
        """Leniente: aceita a lista como veio; só exige ≥1 caminho."""
        if not v:
            raise ValueError("SellerAdvice precisa de pelo menos um caminho (path)")
        return v


# --- Schemas de wire (camelCase a partir do ORM) -----------------------------------


class SessionOut(BaseModel):
    """Item da sidebar de sessões do copiloto."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    leadId: int | None = Field(default=None, validation_alias="lead_id")
    title: str
    updatedAt: object | None = Field(default=None, validation_alias="updated_at")
    lastSnippet: str | None = None


class MessageOut(BaseModel):
    """Mensagem do copiloto (distinta das mensagens lead/vendedor do WhatsApp)."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    role: str  # 'user' | 'assistant'
    kind: str  # 'text' | 'advice'
    content: str | None = None
    advice: dict | None = None


class ChatIn(BaseModel):
    """Corpo do ``POST /copilot/sessions/{id}/chat``."""

    text: str
    command: str | None = None


class SessionCreate(BaseModel):
    """Corpo do ``POST /copilot/sessions`` — ``leadId`` fixo na criação (nullable)."""

    model_config = ConfigDict(populate_by_name=True)

    leadId: int | None = Field(default=None, validation_alias="lead_id")


class SessionAttach(BaseModel):
    """Corpo do ``PATCH /copilot/sessions/{id}`` — anexa um lead à sessão atual."""

    model_config = ConfigDict(populate_by_name=True)

    leadId: int = Field(validation_alias="lead_id")


# --- input_schema das ferramentas do agente ----------------------------------------
# Pequenos e com ``additionalProperties: false`` — importados pelo service do copiloto.

SEARCH_KNOWLEDGE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Termo de busca na base (playbook/personas/scripts SPIN da MR)",
        },
        "persona": {
            "type": "string",
            "description": "Persona do lead p/ priorizar scripts (opcional)",
        },
        "spin_stage": {
            "type": "string",
            "description": "Estágio SPIN p/ priorizar scripts (opcional)",
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}

GET_COHORTS_STATUS_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "course_name": {
            "type": "string",
            "description": "Nome do curso p/ filtrar turmas (opcional; vazio = todas)",
        },
    },
    "required": [],
    "additionalProperties": False,
}

GET_COURSE_EMENTA_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "course_name": {
            "type": "string",
            "description": "Nome do curso cuja ementa/grade detalhar",
        },
    },
    "required": ["course_name"],
    "additionalProperties": False,
}

GET_ICP_STATS_SCHEMA: dict = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}

GET_FUNNEL_ANALYTICS_SCHEMA: dict = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}

# Ferramenta opcional: o agente só a chama quando o vendedor pede sugestões de mensagem.
# O input replica o shape do ``SellerAdvice`` (reasoning + ~3 paths); o handler valida o
# input contra ``SellerAdvice`` e o captura.
SUGGEST_MESSAGES_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "reasoning": {
            "type": "string",
            "description": "Análise: persona, dores, estágio SPIN e ângulo recomendado",
        },
        "paths": {
            "type": "array",
            "description": "Caminhos estratégicos distintos (idealmente 3)",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Rótulo curto da estratégia",
                    },
                    "rationale": {
                        "type": "string",
                        "description": "Por que esta abordagem faz sentido para o lead",
                    },
                    "message": {
                        "type": "string",
                        "description": "Mensagem WhatsApp pronta para enviar (PT-BR)",
                    },
                },
                "required": ["title", "rationale", "message"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["reasoning", "paths"],
    "additionalProperties": False,
}
