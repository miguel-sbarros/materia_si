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
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.constants import DealStatus
from app.models import Deal, Lead, LeadProfile, Persona
from app.schemas.analysis import label_to_persona
from app.services.deals import BOARD_COLUMNS, card_column

# Quantos itens (dores/desejos) retornar por persona.
_TOP_N = 5


def _rate(numerator: int, denominator: int) -> float:
    """Razão segura (0.0 quando o denominador é zero), arredondada a 4 casas."""
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _top_items(lists: list[list | None], n: int = _TOP_N) -> list[str]:
    """Itens mais frequentes sobre uma coleção de listas JSONB (null-safe)."""
    counter: Counter[str] = Counter()
    for items in lists:
        for item in items or []:
            if isinstance(item, str) and item.strip():
                counter[item.strip()] += 1
    return [item for item, _ in counter.most_common(n)]


def icp_summary(db: Session) -> dict:
    """Resumo de ICP por persona (``LeadProfile.matched_persona``).

    Para cada persona: ``leads`` (nº de leads com aquele rótulo), ``conversionRate``
    (deals ``won`` / total de deals desses leads; 0.0 se não houver deals) e os tops de
    ``dores``/``desejos`` por frequência. Leads sem perfil/persona caem em "Indeterminado".

    LEFT-merge com a tabela ``personas`` (baseline de catálogo) por código de enum: adiciona
    ``baselineConversao`` (taxa de conversão de catálogo), ``volumeLeads`` (volume estimado)
    e ``description``. Null-safe: sem linha correspondente, esses campos vêm ``None``.
    """
    leads = db.scalars(
        select(Lead).options(
            joinedload(Lead.profile),
            joinedload(Lead.deals),
        )
    ).unique().all()

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

    return {"personas": personas, "totalLeads": total_leads}


def _median_int(values: list[int | None]) -> int | None:
    """Mediana (arredondada a int) de valores latência null-safe; ``None`` se vazio."""
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return int(round(median(nums)))


def funnel_analytics(db: Session) -> dict:
    """Métricas do funil + latência + abandono.

    - ``columns``: contagem de deals por coluna do quadro (mapeamento de ``card_column``:
      won→Matriculado, lost→Perdido, senão o stage).
    - ``won``/``lost``/``total`` e ``conversionRate`` (won/total).
    - ``medianSellerLatencySeconds``/``medianLeadLatencySeconds``/
      ``medianFirstResponseLatencySeconds`` (medianas sobre ``lead_profiles``, null-safe).
    - ``abandonmentRate`` (perfis ``is_abandoned`` / total de perfis).
    """
    deals = db.scalars(select(Deal)).all()

    columns = dict.fromkeys(BOARD_COLUMNS, 0)
    won = lost = 0
    for deal in deals:
        columns[card_column(deal)] += 1
        if deal.status == DealStatus.WON:
            won += 1
        elif deal.status == DealStatus.LOST:
            lost += 1
    total = len(deals)

    profiles = db.scalars(select(LeadProfile)).all()
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
