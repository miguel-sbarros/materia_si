"""Analytics agregada (REQF08) — funções deterministas, sem LLM.

``icp_summary`` (conversão por persona) e ``funnel_analytics`` (taxas + latência), via DB real.
"""

from app.core.constants import DealStage, DealStatus
from app.models import Persona
from app.services.analytics import funnel_analytics, icp_summary
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
