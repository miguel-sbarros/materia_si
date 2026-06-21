"""Persistência de LeadProfile; 1:1 com lead (UNIQUE lead_id); cascade. Critério 1 (P3)."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Lead, LeadProfile
from app.schemas.analysis import PersonaType, persona_label
from tests.factories import make_lead


def test_lead_profile_persist(db_session):
    lead = make_lead(db_session, name="Dr. Perfil")
    profile = LeadProfile(
        lead_id=lead.id,
        especialidade="implantodontista",
        experiencia="+10 anos",
        cidade_estado="São Paulo/SP",
        course_interest="Imersão",
        dores_verbalizadas=["medo de errar", "falta de prática clínica"],
        desejos_expressos=["dominar implantes", "aumentar faturamento"],
        objecoes=["preço alto", "sem tempo"],
        comentarios=["CBCT", "Blue Sky Plan", "guia cirúrgica", "indicado por colega"],
        matched_persona="Especialista Analógico",
        persona_confidence=0.82,
        persona_reasoning="Décadas de experiência, transição para o digital.",
        current_spin_stage="problem",
        lead_score=72,
        summary="Lead experiente, busca digitalizar a prática.",
        median_seller_latency_seconds=120,
        median_lead_latency_seconds=300,
        first_response_latency_seconds=45,
        last_message_sent=True,
        is_abandoned=False,
        abandon_spin_stage=None,
        model_used="claude-haiku-4-5",
        raw={"persona_indicators": ["analógico"]},
    )
    db_session.add(profile)
    db_session.commit()
    db_session.expire_all()

    reloaded = db_session.scalar(
        select(LeadProfile).where(LeadProfile.lead_id == lead.id)
    )
    assert reloaded is not None
    # Round-trip de escalares.
    assert reloaded.especialidade == "implantodontista"
    assert reloaded.persona_confidence == 0.82
    assert reloaded.lead_score == 72
    assert reloaded.last_message_sent is True
    assert reloaded.is_abandoned is False
    # Round-trip de listas (JSONB).
    assert reloaded.dores_verbalizadas == ["medo de errar", "falta de prática clínica"]
    assert reloaded.objecoes == ["preço alto", "sem tempo"]
    assert reloaded.comentarios == [
        "CBCT",
        "Blue Sky Plan",
        "guia cirúrgica",
        "indicado por colega",
    ]
    # Round-trip de dict (JSONB).
    assert reloaded.raw == {"persona_indicators": ["analógico"]}
    # created_at/updated_at preenchidos pelos server defaults.
    assert reloaded.created_at is not None
    assert reloaded.updated_at is not None

    # Relationship 1:1.
    db_session.refresh(lead)
    assert lead.profile is not None
    assert lead.profile.id == reloaded.id


def test_lead_profile_unique_per_lead(db_session):
    lead = make_lead(db_session, name="Dra. Única")
    db_session.add(LeadProfile(lead_id=lead.id))
    db_session.flush()

    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(LeadProfile(lead_id=lead.id))
        db_session.flush()


def test_lead_profile_cascade_delete(db_session):
    lead = make_lead(db_session, name="Dr. Cascata Perfil")
    profile = LeadProfile(lead_id=lead.id)
    db_session.add(profile)
    db_session.flush()

    lead_id = lead.id
    profile_id = profile.id
    db_session.delete(lead)
    db_session.flush()

    assert db_session.scalar(select(Lead).where(Lead.id == lead_id)) is None
    assert (
        db_session.scalar(select(LeadProfile).where(LeadProfile.id == profile_id))
        is None
    )


def test_persona_label_map():
    assert persona_label(PersonaType.FOCADO_EM_PROTESE) == "Focado em Prótese"
    assert persona_label(PersonaType.INDETERMINADO) is None
