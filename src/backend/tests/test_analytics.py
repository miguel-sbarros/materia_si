"""Analytics agregada (REQF08) — funções deterministas, sem LLM.

``icp_summary`` (conversão por persona) e ``funnel_analytics`` (taxas + latência), via DB real.
"""

from datetime import UTC, datetime

from app.core.constants import DealStage, DealStatus
from app.models import Conversation, Message, Persona
from app.schemas.analysis import SPINStage
from app.services.analytics import (
    funnel_analytics,
    icp_summary,
    kpis,
    revenue_summary,
    spin_abandonment,
)
from tests.factories import make_course, make_deal, make_lead, make_profile


def test_icp_summary_conversion_by_persona(db_session):
    """2 leads "Especialista Analógico" (1 won, 1 open) + 1 "Iniciado Digital".

    Conversão da persona Analógico = 1 won / 2 deals = 0.5; Iniciado sem deals = 0.0.
    Tops de dores/desejos agregados por frequência.
    """
    _course, [cohort] = make_course(db_session)

    # Baseline de catálogo só para o Analógico → enriquecimento LEFT-merge por código de enum.
    db_session.add(
        Persona(
            code="002_especialista_analogico",
            name="O Especialista Analógico",
            description="Mestre da implantodontia analógica.",
            volume_leads="58%",
            taxa_conversao="16%",
        )
    )
    db_session.flush()

    ana1 = make_lead(db_session, name="Ana 1")
    make_profile(
        db_session, ana1, matched_persona="Especialista Analógico",
        dores=["medo da tecnologia", "curva de aprendizado"],
        desejos=["proteger o legado"],
    )
    make_deal(db_session, cohort, lead=ana1, stage=DealStage.NEGOCIANDO, status=DealStatus.WON)

    ana2 = make_lead(db_session, name="Ana 2")
    make_profile(
        db_session, ana2, matched_persona="Especialista Analógico",
        dores=["medo da tecnologia"],
        desejos=["proteger o legado", "ganhar precisão"],
    )
    make_deal(db_session, cohort, lead=ana2, stage=DealStage.CONTATADO, status=DealStatus.OPEN)

    ini = make_lead(db_session, name="Ini 1")
    make_profile(
        db_session, ini, matched_persona="Iniciado Digital",
        dores=["insegurança"], desejos=["modernizar"],
    )
    # Iniciado sem nenhum deal.

    summary = icp_summary(db_session)
    assert summary["totalLeads"] == 3
    by_persona = {p["persona"]: p for p in summary["personas"]}

    analogico = by_persona["Especialista Analógico"]
    assert analogico["leads"] == 2
    assert analogico["conversionRate"] == 0.5  # 1 won / 2 deals
    # "medo da tecnologia" aparece 2x → primeiro no ranking.
    assert analogico["topDores"][0] == "medo da tecnologia"
    assert "proteger o legado" in analogico["topDesejos"]
    # Enriquecimento do baseline da tabela `personas` (LEFT-merge por código de enum).
    assert analogico["baselineConversao"] == "16%"
    assert analogico["volumeLeads"] == "58%"
    assert analogico["description"] == "Mestre da implantodontia analógica."

    iniciado = by_persona["Iniciado Digital"]
    assert iniciado["leads"] == 1
    assert iniciado["conversionRate"] == 0.0  # sem deals → 0.0, não divide por zero
    # Sem linha de baseline correspondente → campos enriquecidos vêm None (null-safe).
    assert iniciado["baselineConversao"] is None
    assert iniciado["volumeLeads"] is None
    assert iniciado["description"] is None


def test_icp_summary_lead_without_profile_is_indeterminado(db_session):
    """Lead sem perfil cai no bucket 'Indeterminado' (null-safe)."""
    make_lead(db_session, name="Sem Perfil")
    summary = icp_summary(db_session)
    assert summary["totalLeads"] == 1
    assert summary["personas"][0]["persona"] == "Indeterminado"
    assert summary["personas"][0]["topDores"] == []


def test_funnel_analytics_rates_and_latency(db_session):
    """Deals em vários estágios + perfis com latência → contagens, conversão e medianas."""
    _course, [cohort] = make_course(db_session)

    # 1 Novo, 1 Negociando (open), 1 won, 1 lost.
    novo_lead = make_lead(db_session, name="Novo")
    make_deal(db_session, cohort, lead=novo_lead, stage=DealStage.NOVO, status=DealStatus.OPEN)
    make_profile(
        db_session, novo_lead, median_seller_latency_seconds=100,
        median_lead_latency_seconds=300, first_response_latency_seconds=50,
        is_abandoned=False,
    )

    neg_lead = make_lead(db_session, name="Neg")
    make_deal(
        db_session, cohort, lead=neg_lead, stage=DealStage.NEGOCIANDO, status=DealStatus.OPEN
    )
    make_profile(
        db_session, neg_lead, median_seller_latency_seconds=200,
        median_lead_latency_seconds=600, first_response_latency_seconds=150,
        is_abandoned=True,
    )

    won_lead = make_lead(db_session, name="Won")
    make_deal(
        db_session, cohort, lead=won_lead, stage=DealStage.NEGOCIANDO, status=DealStatus.WON
    )

    lost_lead = make_lead(db_session, name="Lost")
    make_deal(
        db_session, cohort, lead=lost_lead, stage=DealStage.NEGOCIANDO,
        status=DealStatus.LOST, lost_reason="Sem orçamento",
    )

    funnel = funnel_analytics(db_session)

    assert funnel["columns"]["Novo"] == 1
    assert funnel["columns"]["Negociando"] == 1
    assert funnel["columns"]["Matriculado"] == 1
    assert funnel["columns"]["Perdido"] == 1
    assert funnel["total"] == 4
    assert funnel["won"] == 1
    assert funnel["lost"] == 1
    assert funnel["conversionRate"] == 0.25  # 1 won / 4 deals

    # Medianas sobre os 2 perfis com latência (100, 200) → 150; (300, 600) → 450; (50,150)→100.
    assert funnel["medianSellerLatencySeconds"] == 150
    assert funnel["medianLeadLatencySeconds"] == 450
    assert funnel["medianFirstResponseLatencySeconds"] == 100
    # 1 de 2 perfis abandonado → 0.5.
    assert funnel["abandonmentRate"] == 0.5


def test_funnel_analytics_empty_is_null_safe(db_session):
    """Sem deals nem perfis: taxas 0.0 e latências None (degrada graciosamente)."""
    funnel = funnel_analytics(db_session)
    assert funnel["total"] == 0
    assert funnel["conversionRate"] == 0.0
    assert funnel["abandonmentRate"] == 0.0
    assert funnel["medianSellerLatencySeconds"] is None


# --- Agregadores do painel GET /analytics --------------------------------------------------


def test_kpis_total_and_conversion(db_session):
    """totalLeads = nº de leads; conversionRate = won/total escalado a % (1 casa)."""
    _course, [cohort] = make_course(db_session)
    won = make_lead(db_session, name="Won")
    make_deal(db_session, cohort, lead=won, status=DealStatus.WON)
    open_lead = make_lead(db_session, name="Open")
    make_deal(db_session, cohort, lead=open_lead, status=DealStatus.OPEN)

    result = kpis(db_session)
    assert result["totalLeads"] == 2
    # 1 won / 2 deals = 0.5 → 50.0%.
    assert result["conversionRate"] == 50.0
    # Leads recém-criados → newLeadsToday cobre os de hoje (>= 0, int).
    assert isinstance(result["newLeadsToday"], int)
    assert result["newLeadsToday"] >= 0


def test_spin_abandonment_buckets_churn_at_stage(db_session):
    """Um perfil abandonado em IMPLICATION mostra churn no bucket 'Implicação'."""
    lead = make_lead(db_session, name="Abandonado")
    make_profile(
        db_session, lead, is_abandoned=True,
        abandon_spin_stage=SPINStage.IMPLICATION.value,
    )

    rows = spin_abandonment(db_session)
    assert [r["stage"] for r in rows] == ["Situação", "Problema", "Implicação", "Necessidade"]
    by_stage = {r["stage"]: r for r in rows}
    # 1 de 1 perfil abandonado em Implicação → 100% churn.
    assert by_stage["Implicação"]["churned"] == 100
    assert by_stage["Implicação"]["retained"] == 0
    # Estágios sem abandono → 0% churn.
    assert by_stage["Situação"]["churned"] == 0
    assert by_stage["Situação"]["retained"] == 100


def test_spin_abandonment_empty_is_null_safe(db_session):
    """Sem perfis: todos os estágios 0% churn / 100% retained."""
    rows = spin_abandonment(db_session)
    assert len(rows) == 4
    assert all(r["churned"] == 0 and r["retained"] == 100 for r in rows)


def test_revenue_summary_sums_won_deals(db_session):
    """total = soma dos valores dos deals ganhos (price_per_slot da turma)."""
    _course, [cohort] = make_course(db_session, price="5900.00")
    won1 = make_lead(db_session, name="W1")
    make_deal(db_session, cohort, lead=won1, status=DealStatus.WON)
    won2 = make_lead(db_session, name="W2")
    make_deal(db_session, cohort, lead=won2, status=DealStatus.WON)
    # Um deal aberto não conta para a receita.
    open_lead = make_lead(db_session, name="O1")
    make_deal(db_session, cohort, lead=open_lead, status=DealStatus.OPEN)

    revenue = revenue_summary(db_session)
    assert revenue["total"] == 11800.0  # 2 × 5900
    assert isinstance(revenue["byMonth"], list)
    assert sum(m["value"] for m in revenue["byMonth"]) == 11800.0


def test_revenue_summary_empty(db_session):
    """Sem deals ganhos: total 0.0 e byMonth vazio."""
    revenue = revenue_summary(db_session)
    assert revenue["total"] == 0.0
    assert revenue["byMonth"] == []


def test_get_analytics_endpoint_shape(api_client, db_session):
    """GET /analytics → 200 com todas as chaves de topo e tipos corretos."""
    _course, [cohort] = make_course(db_session)
    won = make_lead(db_session, name="Won")
    make_deal(db_session, cohort, lead=won, status=DealStatus.WON)
    make_profile(
        db_session, won, matched_persona="Especialista Analógico",
        dores=["medo da tecnologia"], desejos=["proteger o legado"],
        is_abandoned=True, abandon_spin_stage=SPINStage.PROBLEM.value,
    )
    # Mensagem com timestamp → alimenta messageActivity.
    conv = Conversation(lead_id=won.id, channel="WhatsApp")
    db_session.add(conv)
    db_session.flush()
    db_session.add(
        Message(
            conversation_id=conv.id, text="oi", sent=False, sequence=0,
            sent_at=datetime(2025, 10, 30, 14, 0, tzinfo=UTC),
        )
    )
    db_session.flush()

    resp = api_client.get("/analytics")
    assert resp.status_code == 200
    body = resp.json()

    for key in (
        "kpis", "funnelStages", "spin", "personas", "painPoints",
        "revenue", "latency", "abandonmentRate", "messageActivity",
    ):
        assert key in body, f"chave ausente: {key}"

    assert set(body["kpis"]) == {"totalLeads", "newLeadsToday", "conversionRate"}
    assert isinstance(body["funnelStages"], list)
    assert all({"name", "count"} <= set(s) for s in body["funnelStages"])
    assert len(body["spin"]) == 4
    assert {"stage", "retained", "churned"} <= set(body["spin"][0])
    assert isinstance(body["personas"], list)
    assert all(
        {"persona", "leads", "conversionRate", "topDores", "topDesejos", "description"}
        == set(p)
        for p in body["personas"]
    )
    assert all({"rank", "title", "count"} <= set(p) for p in body["painPoints"])
    assert {"total", "byMonth"} <= set(body["revenue"])
    assert {"medianSellerSeconds", "medianLeadSeconds", "firstResponseSeconds"} == set(
        body["latency"]
    )
    assert isinstance(body["abandonmentRate"], (int, float))
    assert {"weekly", "peakHour", "avgResponseSeconds"} == set(body["messageActivity"])
    # painPoints reflete a dor verbalizada.
    assert body["painPoints"][0]["title"] == "medo da tecnologia"
    # messageActivity tem a semana e a hora de pico da mensagem com timestamp.
    assert body["messageActivity"]["peakHour"] == 14
    assert len(body["messageActivity"]["weekly"]) == 1


def test_get_analytics_empty_db_is_null_safe(api_client):
    """Banco vazio: o endpoint ainda devolve a forma completa com zeros/None/[]."""
    resp = api_client.get("/analytics")
    assert resp.status_code == 200
    body = resp.json()

    assert body["kpis"] == {"totalLeads": 0, "newLeadsToday": 0, "conversionRate": 0.0}
    assert body["personas"] == []
    assert body["painPoints"] == []
    assert body["revenue"] == {"total": 0.0, "byMonth": []}
    assert body["abandonmentRate"] == 0.0
    assert body["latency"] == {
        "medianSellerSeconds": None,
        "medianLeadSeconds": None,
        "firstResponseSeconds": None,
    }
    assert body["messageActivity"] == {
        "weekly": [], "peakHour": None, "avgResponseSeconds": None,
    }
    # funnelStages e spin têm sempre as colunas/estágios fixos, mesmo zerados.
    assert len(body["spin"]) == 4
    assert all(s["count"] == 0 for s in body["funnelStages"])
