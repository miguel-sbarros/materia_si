"""POST /leads (cria lead + deal) e GET /leads/{id}. Critérios 7–9 (REQF01) + 12–13 (P2)."""

from sqlalchemy import select

from app.core.constants import DealStage, DealStatus
from app.models import Deal, DealEvent, Lead, LeadProfile
from app.services.imports import add_manual_message
from tests.factories import make_course, make_lead, make_seller


def test_create_lead_creates_deal(api_client, db_session):
    seller = make_seller(db_session)
    _course, [cohort] = make_course(db_session)

    resp = api_client.post(
        "/leads",
        json={
            "name": "Dr. Novo", "email": "novo@x.com", "phone": "(11) 90000-0000",
            "source": "Instagram", "cohort_id": cohort.id,
        },
    )
    assert resp.status_code == 201
    card = resp.json()
    assert card["column"] == "Novo"
    assert card["name"] == "Dr. Novo"
    assert card["cohortId"] == cohort.id
    assert card["assignee"] == seller.initials

    lead = db_session.scalar(select(Lead).where(Lead.email == "novo@x.com"))
    assert lead is not None
    assert lead.assignee_id == seller.id
    deal = db_session.scalar(select(Deal).where(Deal.lead_id == lead.id))
    assert deal.stage == DealStage.NOVO
    assert deal.status == DealStatus.OPEN
    events = db_session.scalars(select(DealEvent).where(DealEvent.deal_id == deal.id)).all()
    assert len(events) == 1
    assert events[0].to_stage == DealStage.NOVO


def test_create_lead_duplicate_email_409(api_client, db_session):
    make_seller(db_session)
    _course, [cohort] = make_course(db_session)
    make_lead(db_session, name="Existente", email="dup@x.com")

    resp = api_client.post(
        "/leads", json={"name": "Outro", "email": "dup@x.com", "cohort_id": cohort.id}
    )
    assert resp.status_code == 409


def test_get_lead_detail(api_client, db_session):
    _course, [cohort] = make_course(db_session, name="Imersão")
    lead = make_lead(db_session, name="Dra. Detalhe", email="det@x.com")
    db_session.add(Deal(lead_id=lead.id, cohort_id=cohort.id, stage=DealStage.CONTATADO))
    db_session.flush()

    resp = api_client.get(f"/leads/{lead.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Dra. Detalhe"
    assert data["email"] == "det@x.com"
    assert len(data["deals"]) == 1
    assert data["deals"][0]["course"] == "Imersão"
    assert data["deals"][0]["column"] == "Contatado"


def test_lead_detail_has_conversation(api_client, db_session):
    """Critério 12: GET /leads/{id} inclui conversation + perfil placeholder + attributes."""
    make_seller(db_session)
    _course, [cohort] = make_course(db_session, name="Imersão")
    lead = make_lead(db_session, name="Carla Mendes", email="carla@x.com", source="Instagram")
    db_session.add(Deal(lead_id=lead.id, cohort_id=cohort.id, stage=DealStage.CONTATADO))
    db_session.flush()

    # Anexa duas mensagens (lead + vendedor) à conversa do lead.
    add_manual_message(db_session, lead_id=lead.id, text="Olá, tenho interesse", sent=False)
    add_manual_message(db_session, lead_id=lead.id, text="Oi! Como posso ajudar?", sent=True)

    resp = api_client.get(f"/leads/{lead.id}")
    assert resp.status_code == 200
    data = resp.json()

    # conversation: ordenada por sequence
    conv = data["conversation"]
    assert len(conv) == 2
    assert conv[0]["text"] == "Olá, tenho interesse"
    assert conv[0]["sent"] is False
    assert conv[1]["text"] == "Oi! Como posso ajudar?"
    assert conv[1]["sent"] is True
    assert conv[0]["sequence"] < conv[1]["sequence"]

    # sem análise de IA ainda → profile None
    assert data["profile"] is None

    # attributes derivados de leads/deals
    labels = {a["label"] for a in data["attributes"]}
    assert "Curso" in labels
    assert "Origem" in labels
    assert len(data["attributes"]) > 0


def test_lead_detail_includes_profile(api_client, db_session):
    """Subagent D: GET /leads/{id} embute o LeadProfile (perfil de IA) quando existe."""
    _course, [cohort] = make_course(db_session, name="Imersão")
    lead = make_lead(db_session, name="Dr. Perfilado")
    db_session.add(Deal(lead_id=lead.id, cohort_id=cohort.id, stage=DealStage.NEGOCIANDO))
    db_session.add(
        LeadProfile(
            lead_id=lead.id,
            especialidade="protesista",
            experiencia="+10 anos",
            dores_verbalizadas=["sem controle da cirurgia"],
            desejos_expressos=["planejamento reverso"],
            objecoes=["preço alto"],
            comentarios=["exocad"],
            matched_persona="Focado em Prótese",
            persona_confidence=0.9,
            persona_reasoning="Fala em fase protética.",
            current_spin_stage="problem",
            lead_score=72,
            summary="Protesista buscando controle do fluxo cirúrgico.",
            median_seller_latency_seconds=120,
            last_message_sent=True,
            is_abandoned=True,
            abandon_spin_stage="implication",
            model_used="claude-haiku-4-5",
        )
    )
    db_session.flush()

    resp = api_client.get(f"/leads/{lead.id}")
    assert resp.status_code == 200
    prof = resp.json()["profile"]
    assert prof is not None
    assert prof["persona"] == "Focado em Prótese"
    assert prof["leadScore"] == 72
    assert prof["especialidade"] == "protesista"
    assert prof["dores"] == ["sem controle da cirurgia"]
    assert prof["desejos"] == ["planejamento reverso"]
    assert prof["objecoes"] == ["preço alto"]
    assert prof["comentarios"] == ["exocad"]
    assert prof["currentSpinStage"] == "problem"
    assert prof["isAbandoned"] is True
    assert prof["abandonSpinStage"] == "implication"


def test_search_leads(api_client, db_session):
    """Critério 13: GET /leads?q= busca por nome (case-insensitive); vazio → []."""
    make_seller(db_session)
    _course, [cohort] = make_course(db_session)
    maria = make_lead(db_session, name="Maria Silva")
    db_session.add(Deal(lead_id=maria.id, cohort_id=cohort.id, stage=DealStage.NOVO))
    make_lead(db_session, name="João Souza")
    db_session.flush()

    resp = api_client.get("/leads", params={"q": "mar"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    item = results[0]
    assert item["name"] == "Maria Silva"
    assert set(item) >= {"id", "name", "initials", "persona", "stage"}
    assert item["initials"] == "MS"
    assert item["stage"] == "Novo"
    assert item["persona"] is None

    assert api_client.get("/leads", params={"q": ""}).json() == []
    assert api_client.get("/leads", params={"q": "zzz"}).json() == []
