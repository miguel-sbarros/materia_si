"""Router de analytics — um endpoint agregador (REQF08).

``GET /analytics`` compõe os agregadores deterministas de ``app.services.analytics`` num único
payload (camelCase) que o front consome direto. Tudo null-safe: sem dados, degrada para
zeros/None/listas vazias mantendo a forma do contrato.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import analytics

router = APIRouter(tags=["analytics"])

# Campos de persona expostos ao front (subconjunto enxuto de icp_summary).
_PERSONA_KEYS = ("persona", "leads", "conversionRate", "topDores", "topDesejos", "description")


@router.get("/analytics")
def get_analytics(
    course_id: int | None = None,
    cohort_id: int | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """Painel de analytics agregado a partir de dados reais (sem LLM).

    Filtros opcionais por curso/turma (deal: lead → cohort) escopam todas as métricas ao
    subconjunto correspondente; sem filtros, devolve a visão global.
    """
    funnel = analytics.funnel_analytics(db, course_id, cohort_id)
    icp = analytics.icp_summary(db, course_id, cohort_id)

    funnel_stages = [
        {"name": name, "count": count} for name, count in funnel["columns"].items()
    ]
    personas = [
        {key: p.get(key) for key in _PERSONA_KEYS} for p in icp["personas"]
    ]

    return {
        "kpis": analytics.kpis(db, course_id, cohort_id),
        "funnelStages": funnel_stages,
        "spin": analytics.spin_abandonment(db, course_id, cohort_id),
        "personas": personas,
        "indeterminadoCount": icp["indeterminadoCount"],
        "indeterminadoRate": icp["indeterminadoRate"],
        "painPoints": analytics.pain_points(db, course_id=course_id, cohort_id=cohort_id),
        "revenue": analytics.revenue_summary(db, course_id, cohort_id),
        "latency": {
            "medianSellerSeconds": funnel["medianSellerLatencySeconds"],
            "medianLeadSeconds": funnel["medianLeadLatencySeconds"],
            "firstResponseSeconds": funnel["medianFirstResponseLatencySeconds"],
        },
        "abandonmentRate": funnel["abandonmentRate"],
        "messageActivity": analytics.message_activity(db, course_id, cohort_id),
    }
