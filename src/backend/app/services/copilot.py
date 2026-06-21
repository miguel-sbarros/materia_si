"""Serviço do Copiloto de Vendas (P4b, REQF04) — sessões + agente com ferramentas.

Gere sessões persistidas (``CopilotSession``/``CopilotMessage`` — distintas das mensagens
lead/vendedor do WhatsApp) e roda o agente: um loop de tool-use da Anthropic (``run_agent``)
fundamentado em RAG (``search_knowledge``), no catálogo (``get_cohorts_status``/
``get_course_ementa``) e na analytics agregada (``get_icp_stats``/``get_funnel_analytics``).

O agente roda SEMPRE em modo texto (conversa) e tem uma ferramenta opcional
``suggest_messages`` que ele só chama quando o vendedor pede explicitamente sugestões de
mensagem ("como respondo?", "me dá sugestões"). Quando essa ferramenta é chamada, a
resposta é persistida como ``kind='advice'`` (os 3 caminhos estratégicos capturados);
caso contrário, como ``kind='text'`` (resposta conversacional em markdown).

Comandos slash (``/icp``, ``/analytics``, ``/courses``, ``/spin``) têm precedência: rodam
em modo texto com uma instrução PT que orienta o agente a chamar a ferramenta certa.
Quando há lead anexado (sem comando), o contexto do lead (perfil + histórico) é injetado
para fundamentar a conversa e eventuais sugestões.
"""

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models import (
    Cohort,
    Conversation,
    CopilotMessage,
    CopilotSession,
    Course,
    Lead,
    Message,
)
from app.prompts.copilot import COPILOT_SYSTEM_PROMPT, build_copilot_content
from app.schemas.analysis import label_to_persona
from app.schemas.copilot import (
    GET_COHORTS_STATUS_SCHEMA,
    GET_COURSE_EMENTA_SCHEMA,
    GET_FUNNEL_ANALYTICS_SCHEMA,
    GET_ICP_STATS_SCHEMA,
    SEARCH_KNOWLEDGE_SCHEMA,
    SUGGEST_MESSAGES_SCHEMA,
    MessageOut,
    SellerAdvice,
    SessionOut,
)
from app.services import analytics, course_content, rag
from app.services.analysis import _transcript
from app.services.llm.client import run_agent

CHANNEL = "WhatsApp"

# Comandos slash → instrução PT que orienta o agente (todos rodam em modo texto).
_COMMAND_INSTRUCTIONS: dict[str, str] = {
    "/icp": (
        "Rode a análise de ICP: chame get_icp_stats e resuma, em português, as personas, "
        "a taxa de conversão de cada uma e as principais dores e desejos agregados."
    ),
    "/analytics": (
        "Rode a análise do funil: chame get_funnel_analytics e resuma, em português, as "
        "taxas de conversão (geral e por estágio), as latências de resposta e a taxa de "
        "abandono."
    ),
    "/courses": (
        "Detalhe o portfólio de cursos da MR: use get_course_ementa e/ou search_knowledge "
        "e resuma, em português, os cursos disponíveis e suas ementas."
    ),
    "/spin": (
        "Oriente sobre a metodologia SPIN da MR: use search_knowledge para buscar os scripts "
        "e técnicas SPIN no playbook e resuma, em português, como aplicá-los."
    ),
}


def create_session(db: Session, lead_id: int | None = None) -> CopilotSession:
    """Cria uma sessão do copiloto. Com ``lead_id``, o título vira o nome do lead.

    Levanta ``ValueError`` ("Lead não encontrado") se ``lead_id`` for informado e não existir.
    """
    title = "Nova conversa"
    if lead_id is not None:
        lead = db.get(Lead, lead_id)
        if lead is None:
            raise ValueError("Lead não encontrado")
        title = lead.name

    session = CopilotSession(lead_id=lead_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def attach_lead(db: Session, session_id: int, lead_id: int) -> CopilotSession:
    """Anexa um lead a uma sessão SEM lead, ligando-o à sessão atual.

    Levanta ``ValueError``:
    - "Sessão não encontrada" se a sessão não existir (rota → 404);
    - "Lead não encontrado" se o lead não existir (rota → 404);
    - "sessão já tem um lead" se a sessão já estiver vinculada (rota → 409).
    """
    session = db.get(CopilotSession, session_id)
    if session is None:
        raise ValueError("Sessão não encontrada")
    lead = db.get(Lead, lead_id)
    if lead is None:
        raise ValueError("Lead não encontrado")
    if session.lead_id is not None:
        raise ValueError("Esta sessão já tem um lead")

    session.lead_id = lead_id
    session.title = lead.name
    db.commit()
    db.refresh(session)
    return session


def _snippet(message: CopilotMessage, limit: int = 80) -> str | None:
    """Resumo curto da última mensagem para a sidebar (texto truncado ou rótulo p/ advice)."""
    if message.kind == "advice":
        return "Sugestão de mensagem"
    text = message.content or ""
    text = text.strip()
    if not text:
        return None
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def list_sessions(db: Session) -> list[SessionOut]:
    """Sessões ordenadas por ``updated_at`` desc, cada uma com ``lastSnippet``."""
    sessions = db.scalars(
        select(CopilotSession)
        .options(joinedload(CopilotSession.messages))
        .order_by(CopilotSession.updated_at.desc(), CopilotSession.id.desc())
    ).unique().all()

    out: list[SessionOut] = []
    for session in sessions:
        last = session.messages[-1] if session.messages else None
        item = SessionOut.model_validate(session)
        item.lastSnippet = _snippet(last) if last else None
        out.append(item)
    return out


def get_session(db: Session, session_id: int) -> dict:
    """Sessão + mensagens ordenadas: ``{session: SessionOut, messages: [MessageOut]}``.

    Levanta ``ValueError`` ("Sessão não encontrada") se a sessão não existir.
    """
    session = db.scalar(
        select(CopilotSession)
        .where(CopilotSession.id == session_id)
        .options(joinedload(CopilotSession.messages))
    )
    if session is None:
        raise ValueError("Sessão não encontrada")

    last = session.messages[-1] if session.messages else None
    session_out = SessionOut.model_validate(session)
    session_out.lastSnippet = _snippet(last) if last else None
    return {
        "session": session_out,
        "messages": [MessageOut.model_validate(m) for m in session.messages],
    }


# --- Ferramentas do agente ----------------------------------------------------------


def _build_tools(db: Session) -> tuple[list[dict], dict, list[SellerAdvice]]:
    """Monta as 6 tool defs (PT) + um ``dispatch`` ligado a ``db`` + um ``captured``.

    Cada handler é **à prova de exceção** (devolve string de erro, nunca levanta) para que
    o loop do agente sempre receba um ``tool_result`` e possa terminar. Todos devolvem string
    (resultados estruturados são serializados com ``json.dumps``).

    A 6ª ferramenta ``suggest_messages`` é opcional: o agente só a chama quando o vendedor
    pede sugestões de mensagem. Seu handler valida o input contra ``SellerAdvice`` e o
    acumula em ``captured`` (lista capturada no closure), devolvendo um ack curto.
    ``chat()`` lê ``captured`` após o loop: se não-vazio → persiste ``kind='advice'``.
    """

    captured: list[SellerAdvice] = []

    def search_knowledge(
        query: str, persona: str | None = None, spin_stage: str | None = None
    ) -> str:
        try:
            persona_enum = label_to_persona(persona)
            chunks = rag.retrieve(
                db,
                query,
                persona=persona_enum.value if persona_enum else None,
                spin_stage=spin_stage,
                k=6,
            )
            if not chunks:
                return "Nenhum trecho relevante encontrado na base de conhecimento."
            return "\n\n---\n\n".join(
                f"{c.title or c.label or 'Trecho'}:\n{c.content}" for c in chunks
            )
        except Exception as exc:  # noqa: BLE001 — handler de ferramenta nunca levanta.
            return f"Erro ao buscar na base de conhecimento: {exc}"

    def get_cohorts_status(course_name: str | None = None) -> str:
        try:
            stmt = select(Cohort).join(Course, Cohort.course_id == Course.id)
            if course_name and course_name.strip():
                stmt = stmt.where(Course.name.ilike(f"%{course_name.strip()}%"))
            stmt = stmt.options(joinedload(Cohort.course)).order_by(Cohort.id)
            cohorts = db.scalars(stmt).unique().all()
            rows = [
                {
                    "course": c.course.name if c.course else None,
                    "cohort": c.name,
                    "start": c.start_date.isoformat() if c.start_date else None,
                    "end": c.end_date.isoformat() if c.end_date else None,
                    "capacity": c.capacity,
                    "status": str(c.status),
                    "price": str(c.price_per_slot) if c.price_per_slot is not None else None,
                }
                for c in cohorts
            ]
            if not rows:
                return "Nenhuma turma encontrada para o critério informado."
            return json.dumps(rows, ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            return f"Erro ao consultar turmas: {exc}"

    def get_course_ementa(course_name: str) -> str:
        try:
            ementa = course_content.course_ementa(course_name)
            if ementa is None:
                return f"Curso não encontrado: {course_name}"
            return json.dumps(ementa, ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            return f"Erro ao consultar a ementa do curso: {exc}"

    def get_icp_stats() -> str:
        try:
            return json.dumps(analytics.icp_summary(db), ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            return f"Erro ao calcular o ICP: {exc}"

    def get_funnel_analytics() -> str:
        try:
            return json.dumps(analytics.funnel_analytics(db), ensure_ascii=False)
        except Exception as exc:  # noqa: BLE001
            return f"Erro ao calcular o funil: {exc}"

    def suggest_messages(**kwargs) -> str:
        """Captura sugestões de mensagem (reasoning + paths) validadas como SellerAdvice."""
        try:
            captured.append(SellerAdvice.model_validate(kwargs))
            return "Sugestões registradas."
        except Exception as exc:  # noqa: BLE001
            return f"Erro ao registrar sugestões: {exc}"

    tools = [
        {
            "name": "search_knowledge",
            "description": (
                "Busca na base de conhecimento da MR (playbook, dossiês de persona e scripts "
                "SPIN). Use para argumentos de valor, scripts de abordagem e contorno de "
                "objeção. Passe persona e spin_stage quando souber, para priorizar os scripts."
            ),
            "input_schema": SEARCH_KNOWLEDGE_SCHEMA,
        },
        {
            "name": "get_cohorts_status",
            "description": (
                "Consulta o status real das turmas (curso, datas, capacidade, situação e "
                "preço por vaga). Filtra por nome do curso quando informado."
            ),
            "input_schema": GET_COHORTS_STATUS_SCHEMA,
        },
        {
            "name": "get_course_ementa",
            "description": (
                "Detalha um curso da MR: resumo e grade curricular (ementa) a partir do "
                "playbook de cursos."
            ),
            "input_schema": GET_COURSE_EMENTA_SCHEMA,
        },
        {
            "name": "get_icp_stats",
            "description": (
                "Estatísticas de ICP por persona: nº de leads, taxa de conversão e top "
                "dores/desejos agregados."
            ),
            "input_schema": GET_ICP_STATS_SCHEMA,
        },
        {
            "name": "get_funnel_analytics",
            "description": (
                "Métricas do funil: conversão (geral e por estágio), latências de resposta "
                "e taxa de abandono."
            ),
            "input_schema": GET_FUNNEL_ANALYTICS_SCHEMA,
        },
        {
            "name": "suggest_messages",
            "description": (
                "Registra 3 sugestões estratégicas de mensagem de WhatsApp para o vendedor "
                "enviar ao lead. Chame esta ferramenta APENAS quando o vendedor pedir "
                "explicitamente sugestões de mensagem / como responder. Informe uma análise "
                "(reasoning) e EXATAMENTE 3 caminhos estratégicos distintos (paths), cada um "
                "com título, racional e a mensagem pronta em PT-BR."
            ),
            "input_schema": SUGGEST_MESSAGES_SCHEMA,
        },
    ]
    dispatch = {
        "search_knowledge": search_knowledge,
        "get_cohorts_status": get_cohorts_status,
        "get_course_ementa": get_course_ementa,
        "get_icp_stats": get_icp_stats,
        "get_funnel_analytics": get_funnel_analytics,
        "suggest_messages": suggest_messages,
    }
    return tools, dispatch, captured


def _lead_transcript(db: Session, lead_id: int) -> str:
    """Transcrito WhatsApp do lead ('Lead:'/'Vendedor:' por linha; vazio se sem conversa)."""
    conv = db.scalar(
        select(Conversation).where(
            Conversation.lead_id == lead_id, Conversation.channel == CHANNEL
        )
    )
    if conv is None:
        return ""
    messages = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.sequence)
        ).all()
    )
    return _transcript(messages)


def _next_sequence(db: Session, session_id: int) -> int:
    """Próximo ``sequence`` da thread (0 quando ainda não há mensagens)."""
    current = db.scalar(
        select(CopilotMessage.sequence)
        .where(CopilotMessage.session_id == session_id)
        .order_by(CopilotMessage.sequence.desc())
        .limit(1)
    )
    return 0 if current is None else current + 1


def chat(
    db: Session, session_id: int, text: str, command: str | None = None
) -> MessageOut:
    """Roda um turno do copiloto na sessão e persiste pergunta + resposta.

    O agente roda SEMPRE em modo texto com o conjunto completo de ferramentas. Se o
    vendedor pedir sugestões de mensagem, o agente chama ``suggest_messages`` — nesse
    caso persistimos ``kind='advice'`` com os caminhos capturados; caso contrário,
    ``kind='text'`` com a resposta conversacional.

    Levanta ``ValueError`` ("Sessão não encontrada") se a sessão não existir.
    Retorna a mensagem ``assistant`` (wire ``MessageOut``).
    """
    session = db.get(CopilotSession, session_id)
    if session is None:
        raise ValueError("Sessão não encontrada")

    seq = _next_sequence(db, session_id)
    user_label = text or (command or "")
    db.add(
        CopilotMessage(
            session_id=session_id,
            role="user",
            kind="text",
            content=user_label,
            sequence=seq,
        )
    )
    db.flush()

    tools, dispatch, captured = _build_tools(db)
    settings = get_settings()
    question = text or ""

    if command and command in _COMMAND_INSTRUCTIONS:
        # Modo comando: instrução PT orientando a ferramenta certa (tem precedência).
        instruction = _COMMAND_INSTRUCTIONS[command]
        content = f"{instruction}\n\nPergunta do vendedor: {question}".strip()
    elif session.lead_id is not None:
        # Lead anexado: injeta perfil + histórico para fundamentar a conversa/sugestões.
        lead = db.get(Lead, session.lead_id)
        profile = lead.profile if lead else None
        transcript = _lead_transcript(db, session.lead_id)
        content = build_copilot_content(
            profile, transcript, lead_name=lead.name if lead else None
        )
        if question:
            content = f"{content}\n\n## PERGUNTA DO VENDEDOR\n{question}"
    else:
        # Modo base de conhecimento.
        content = build_copilot_content(None, "")
        if question:
            content = f"{content}\n\n## PERGUNTA DO VENDEDOR\n{question}"

    final_text = run_agent(
        model=settings.model_copilot,
        system=COPILOT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
        tools=tools,
        dispatch=dispatch,
        output_format=None,
    )

    if captured:
        # O agente chamou suggest_messages → persiste o conselho (última captura).
        assistant = CopilotMessage(
            session_id=session_id,
            role="assistant",
            kind="advice",
            content=None,
            advice=captured[-1].model_dump(),
            sequence=seq + 1,
        )
    else:
        assistant = CopilotMessage(
            session_id=session_id,
            role="assistant",
            kind="text",
            content=final_text,
            advice=None,
            sequence=seq + 1,
        )
    db.add(assistant)
    # Toca updated_at com relógio de parede: ``func.now()`` no Postgres é o horário de
    # início da transação (constante dentro dela), o que não garante recência entre chats
    # na mesma transação de teste. Um datetime Python é estritamente crescente por chamada.
    session.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(assistant)
    return MessageOut.model_validate(assistant)
