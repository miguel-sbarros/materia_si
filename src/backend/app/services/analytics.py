"""Analytics agregada (REQF08) — agregações deterministas, sem LLM.

Duas funções puras de leitura (sem ``commit``):

- ``icp_summary``    — ICP por persona: contagem de leads, taxa de conversão (deals won /
  total) e top dores/desejos (frequência sobre os campos JSONB de ``lead_profiles``).
- ``funnel_analytics`` — funil: deals por coluna/estágio, won/lost, conversão geral e
  medianas de latência + taxa de abandono (de ``lead_profiles``).

Tudo null-safe: perfis podem faltar, listas JSONB podem ser ``NULL``, latências podem ser
``None`` (degradam graciosamente quando a conversa não tem timestamps). Saídas
JSON-serializáveis (``Decimal`` → ``float``).
"""

from collections import Counter
from datetime import date, timedelta
from statistics import median

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import DealStatus
from app.models import Cohort, Conversation, Deal, Lead, LeadProfile, Message, Persona
from app.schemas.analysis import SPINStage, label_to_persona
from app.services.deals import BOARD_COLUMNS, card_column

# Quantos itens (dores/desejos) retornar por persona.
_TOP_N = 5

# Estágios SPIN em ordem + rótulos de exibição PT (propriedade do diálogo).
_SPIN_ORDER: list[SPINStage] = [
    SPINStage.SITUATION,
    SPINStage.PROBLEM,
    SPINStage.IMPLICATION,
    SPINStage.NEED_PAYOFF,
]
SPIN_LABELS: dict[SPINStage, str] = {
    SPINStage.SITUATION: "Situação",
    SPINStage.PROBLEM: "Problema",
    SPINStage.IMPLICATION: "Implicação",
    SPINStage.NEED_PAYOFF: "Necessidade",
}


def _rate(numerator: int, denominator: int) -> float:
    """Razão segura (0.0 quando o denominador é zero), arredondada a 4 casas."""
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _top_items(lists: list[list | None], n: int = _TOP_N) -> list[str]:
    """Itens mais frequentes sobre uma coleção de listas JSONB (null-safe)."""
    return [item for item, _ in _count_items(lists).most_common(n)]


def _count_items(lists: list[list | None]) -> Counter[str]:
    """Contador de itens-string sobre uma coleção de listas JSONB (null-safe)."""
    counter: Counter[str] = Counter()
    for items in lists:
        for item in items or []:
            if isinstance(item, str) and item.strip():
                counter[item.strip()] += 1
    return counter


def _deal_cohort_filter(
    course_id: int | None, cohort_id: int | None
) -> ColumnElement[bool] | None:
    """Condição SQL sobre ``Deal.cohort_id`` para o filtro curso/turma (``None`` = sem filtro).

    Turma tem precedência sobre curso (deal: lead → cohort; o curso é alcançado via cohort).
    """
    if cohort_id is not None:
        return Deal.cohort_id == cohort_id
    if course_id is not None:
        return Deal.cohort_id.in_(
            select(Cohort.id).where(Cohort.course_id == course_id)
        )
    return None


def _filtered_lead_ids(
    db: Session, course_id: int | None, cohort_id: int | None
) -> list[int] | None:
    """Ids dos leads com ≥1 deal que casa o filtro curso/turma (``None`` = sem filtro).

    Métricas baseadas em lead/perfil/mensagem se restringem a este conjunto. Sem filtro,
    devolve ``None`` (o chamador então não aplica restrição → comportamento original).
    """
    cond = _deal_cohort_filter(course_id, cohort_id)
    if cond is None:
        return None
    return list(db.scalars(select(Deal.lead_id).where(cond).distinct()).all())


def icp_summary(
    db: Session, course_id: int | None = None, cohort_id: int | None = None
) -> dict:
    """Resumo de ICP por persona (``LeadProfile.matched_persona``).

    Para cada persona: ``leads`` (nº de leads com aquele rótulo), ``conversionRate``
    (deals ``won`` / total de deals desses leads; 0.0 se não houver deals) e os tops de
    ``dores``/``desejos`` por frequência. Leads sem perfil/persona caem em "Indeterminado".

    LEFT-merge com a tabela ``personas`` (baseline de catálogo) por código de enum: adiciona
    ``baselineConversao`` (taxa de conversão de catálogo), ``volumeLeads`` (volume estimado)
    e ``description``. Null-safe: sem linha correspondente, esses campos vêm ``None``.
    """
    stmt = select(Lead).options(
        joinedload(Lead.profile),
        joinedload(Lead.deals),
    )
    lead_ids = _filtered_lead_ids(db, course_id, cohort_id)
    if lead_ids is not None:
        stmt = stmt.where(Lead.id.in_(lead_ids))
    leads = db.scalars(stmt).unique().all()

    # persona (rótulo PT) → acumuladores.
    buckets: dict[str, dict] = {}
    total_leads = 0
    for lead in leads:
        total_leads += 1
        profile = lead.profile
        persona = (profile.matched_persona if profile else None) or "Indeterminado"
        bucket = buckets.setdefault(
            persona,
            {"leads": 0, "deals_total": 0, "deals_won": 0, "dores": [], "desejos": []},
        )
        bucket["leads"] += 1
        for deal in lead.deals:
            bucket["deals_total"] += 1
            if deal.status == DealStatus.WON:
                bucket["deals_won"] += 1
        if profile is not None:
            bucket["dores"].append(profile.dores_verbalizadas)
            bucket["desejos"].append(profile.desejos_expressos)

    # Baseline de catálogo por persona (tabela `personas`), indexado por código de enum.
    # LEFT-merge: o rótulo PT vivo → code via `label_to_persona`; sem linha → campos None.
    persona_rows: dict[str, Persona] = {
        row.code: row for row in db.scalars(select(Persona)).all()
    }

    # "Indeterminado" (leads sem perfil/persona) NÃO vira card de persona — conta apenas como
    # denominador + disclaimer (indício de falha na qualificação pelo vendedor).
    indeterminado_count = buckets.pop("Indeterminado", {}).get("leads", 0)

    personas = []
    for persona, data in buckets.items():
        matched = label_to_persona(persona)
        baseline = persona_rows.get(matched.value) if matched is not None else None
        personas.append(
            {
                "persona": persona,
                "leads": data["leads"],
                "conversionRate": _rate(data["deals_won"], data["deals_total"]),
                "topDores": _top_items(data["dores"]),
                "topDesejos": _top_items(data["desejos"]),
                "baselineConversao": baseline.taxa_conversao if baseline else None,
                "volumeLeads": baseline.volume_leads if baseline else None,
                "description": baseline.description if baseline else None,
            }
        )
    # Ordena por nº de leads (desc) para uma narrativa estável.
    personas.sort(key=lambda p: p["leads"], reverse=True)

    return {
        "personas": personas,
        "totalLeads": total_leads,
        "indeterminadoCount": indeterminado_count,
        "indeterminadoRate": _rate(indeterminado_count, total_leads),
    }


def _median_int(values: list[int | None]) -> int | None:
    """Mediana (arredondada a int) de valores latência null-safe; ``None`` se vazio."""
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return int(round(median(nums)))


def funnel_analytics(
    db: Session, course_id: int | None = None, cohort_id: int | None = None
) -> dict:
    """Métricas do funil + latência + abandono.

    - ``columns``: contagem de deals por coluna do quadro (mapeamento de ``card_column``:
      won→Matriculado, lost→Perdido, senão o stage).
    - ``won``/``lost``/``total`` e ``conversionRate`` (won/total).
    - ``medianSellerLatencySeconds``/``medianLeadLatencySeconds``/
      ``medianFirstResponseLatencySeconds`` (medianas sobre ``lead_profiles``, null-safe).
    - ``abandonmentRate`` (perfis ``is_abandoned`` / total de perfis).
    """
    deal_stmt = select(Deal)
    cond = _deal_cohort_filter(course_id, cohort_id)
    if cond is not None:
        deal_stmt = deal_stmt.where(cond)
    deals = db.scalars(deal_stmt).all()

    columns = dict.fromkeys(BOARD_COLUMNS, 0)
    won = lost = 0
    for deal in deals:
        columns[card_column(deal)] += 1
        if deal.status == DealStatus.WON:
            won += 1
        elif deal.status == DealStatus.LOST:
            lost += 1
    total = len(deals)

    profile_stmt = select(LeadProfile)
    lead_ids = _filtered_lead_ids(db, course_id, cohort_id)
    if lead_ids is not None:
        profile_stmt = profile_stmt.where(LeadProfile.lead_id.in_(lead_ids))
    profiles = db.scalars(profile_stmt).all()
    abandoned = sum(1 for p in profiles if p.is_abandoned)

    return {
        "columns": columns,
        "won": won,
        "lost": lost,
        "total": total,
        "conversionRate": _rate(won, total),
        "medianSellerLatencySeconds": _median_int(
            [p.median_seller_latency_seconds for p in profiles]
        ),
        "medianLeadLatencySeconds": _median_int(
            [p.median_lead_latency_seconds for p in profiles]
        ),
        "medianFirstResponseLatencySeconds": _median_int(
            [p.first_response_latency_seconds for p in profiles]
        ),
        "abandonmentRate": _rate(abandoned, len(profiles)),
    }


def kpis(
    db: Session, course_id: int | None = None, cohort_id: int | None = None
) -> dict:
    """KPIs de topo: total de leads, novos leads hoje e taxa de conversão (em %).

    ``newLeadsToday`` compara ``Lead.created_at::date`` com a data atual do banco
    (``current_date``) — degrada para 0 quando não há leads de hoje. ``conversionRate``
    reusa o ``funnel_analytics`` (won/total) escalado a percentual e arredondado a 1 casa.
    """
    lead_ids = _filtered_lead_ids(db, course_id, cohort_id)

    total_stmt = select(func.count()).select_from(Lead)
    today_stmt = (
        select(func.count())
        .select_from(Lead)
        .where(func.date(Lead.created_at) == func.current_date())
    )
    if lead_ids is not None:
        total_stmt = total_stmt.where(Lead.id.in_(lead_ids))
        today_stmt = today_stmt.where(Lead.id.in_(lead_ids))

    total_leads = db.scalar(total_stmt) or 0
    new_today = db.scalar(today_stmt) or 0
    conversion = funnel_analytics(db, course_id, cohort_id)["conversionRate"]
    return {
        "totalLeads": int(total_leads),
        "newLeadsToday": int(new_today),
        "conversionRate": round(conversion * 100, 1),
    }


def spin_abandonment(
    db: Session, course_id: int | None = None, cohort_id: int | None = None
) -> list[dict]:
    """Churn por estágio SPIN: % de perfis abandonados em cada estágio (null-safe).

    Para os 4 estágios em ordem [Situação, Problema, Implicação, Necessidade], ``churned`` é a
    fração de perfis ``is_abandoned`` cujo ``abandon_spin_stage`` cai naquele estágio, sobre o
    total de perfis (em pontos percentuais inteiros). ``retained`` = 100 - churned. Sem perfis
    → tudo 0/100.
    """
    stmt = select(LeadProfile)
    lead_ids = _filtered_lead_ids(db, course_id, cohort_id)
    if lead_ids is not None:
        stmt = stmt.where(LeadProfile.lead_id.in_(lead_ids))
    profiles = db.scalars(stmt).all()
    total = len(profiles)

    churn_by_stage: Counter[SPINStage] = Counter()
    for p in profiles:
        if not p.is_abandoned or not p.abandon_spin_stage:
            continue
        try:
            stage = SPINStage(p.abandon_spin_stage)
        except ValueError:
            continue
        churn_by_stage[stage] += 1

    rows = []
    for stage in _SPIN_ORDER:
        churned = round(_rate(churn_by_stage.get(stage, 0), total) * 100)
        rows.append(
            {"stage": SPIN_LABELS[stage], "retained": 100 - churned, "churned": churned}
        )
    return rows


def _won_deal_value(deal: Deal) -> float:
    """Valor de um deal (turma > curso), Decimal→float (0.0 se ausente)."""
    cohort = deal.cohort
    price = cohort.price_per_slot if cohort.price_per_slot is not None else cohort.course.price
    return float(price) if price is not None else 0.0


def revenue_summary(
    db: Session, course_id: int | None = None, cohort_id: int | None = None
) -> dict:
    """Receita realizada (deals ``won``): total + série mensal (Decimal→float).

    Mês derivado do ``updated_at`` do deal (data do fechamento; cai para ``created_at``). Sem
    deals ganhos → ``{"total": 0.0, "byMonth": []}``.
    """
    stmt = (
        select(Deal)
        .options(joinedload(Deal.cohort).joinedload(Cohort.course))
        .where(Deal.status == DealStatus.WON)
    )
    cond = _deal_cohort_filter(course_id, cohort_id)
    if cond is not None:
        stmt = stmt.where(cond)
    deals = db.scalars(stmt).all()

    total = 0.0
    by_month: dict[str, float] = {}
    for deal in deals:
        value = _won_deal_value(deal)
        total += value
        when = deal.updated_at or deal.created_at
        if when is not None:
            key = when.strftime("%Y-%m")
            by_month[key] = by_month.get(key, 0.0) + value

    months = [
        {"month": m, "value": round(by_month[m], 2)} for m in sorted(by_month)
    ]
    return {"total": round(total, 2), "byMonth": months}


def message_activity(
    db: Session, course_id: int | None = None, cohort_id: int | None = None
) -> dict:
    """Atividade de mensagens por timestamp (``Message.sent_at``; ``NULL`` é ignorado).

    - ``weekly``: contagem por semana (segunda-feira como início, ``YYYY-MM-DD``).
    - ``peakHour``: hora do dia (0–23) com mais mensagens (``None`` sem timestamps).
    - ``avgResponseSeconds``: reusa a mediana de latência do vendedor do funil.
    Sem timestamps → ``{"weekly": [], "peakHour": None, "avgResponseSeconds": None}``.
    """
    sent_stmt = select(Message.sent_at).where(Message.sent_at.is_not(None))
    lead_ids = _filtered_lead_ids(db, course_id, cohort_id)
    if lead_ids is not None:
        sent_stmt = sent_stmt.where(
            Message.conversation_id.in_(
                select(Conversation.id).where(Conversation.lead_id.in_(lead_ids))
            )
        )
    sent_ats = db.scalars(sent_stmt).all()

    avg_response = funnel_analytics(db, course_id, cohort_id)["medianSellerLatencySeconds"]

    if not sent_ats:
        return {"weekly": [], "peakHour": None, "avgResponseSeconds": avg_response}

    weekly: dict[date, int] = {}
    hours: Counter[int] = Counter()
    for ts in sent_ats:
        week_start = (ts - timedelta(days=ts.weekday())).date()
        weekly[week_start] = weekly.get(week_start, 0) + 1
        hours[ts.hour] += 1

    weekly_rows = [
        {"week": wk.isoformat(), "count": weekly[wk]} for wk in sorted(weekly)
    ]
    peak_hour = hours.most_common(1)[0][0] if hours else None
    return {
        "weekly": weekly_rows,
        "peakHour": peak_hour,
        "avgResponseSeconds": avg_response,
    }


def pain_points(
    db: Session,
    n: int = _TOP_N,
    course_id: int | None = None,
    cohort_id: int | None = None,
) -> list[dict]:
    """Top dores verbalizadas agregadas sobre todos os ``LeadProfile`` (por frequência).

    Retorna ``[{"rank": 1-based, "title": str, "count": int}]`` (vazio sem dores).
    """
    stmt = select(LeadProfile)
    lead_ids = _filtered_lead_ids(db, course_id, cohort_id)
    if lead_ids is not None:
        stmt = stmt.where(LeadProfile.lead_id.in_(lead_ids))
    profiles = db.scalars(stmt).all()
    counts = _count_items([p.dores_verbalizadas for p in profiles])
    return [
        {"rank": i, "title": title, "count": count}
        for i, (title, count) in enumerate(counts.most_common(n), start=1)
    ]
