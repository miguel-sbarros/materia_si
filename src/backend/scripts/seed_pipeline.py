"""Seed do pipeline de vendas EM ABERTO do Master 3.0 (re-executável).

Popula a turma ABERTA ``Master 3.0 — Turma 2027`` com 20 leads realistas (conversas
escritas à mão em ``scripts/pipeline_chats/*.txt``), distribuídos pelas colunas abertas do
funil (Novo/Contatado/Negociando/Aprovado). Para cada lead do manifesto: cria/recupera o
lead (chave natural = e-mail ``pipeline-NN@captus.demo``), importa a conversa de WhatsApp,
cria um deal ABERTO na turma e roda a análise de IA (``LeadProfile``: persona/SPIN/score).

Idempotente: reimportar não duplica (lead por e-mail; mensagens por sequence; deal por
``(lead, cohort)`` → 409 ignorado; análise pula leads que já têm perfil). Cada lead é
commitado individualmente e isolado em try/except, então um erro não aborta o lote.

Precisa de ``ANTHROPIC_API_KEY`` (a análise usa o LLM real). Uso:
    python scripts/seed_pipeline.py
    python scripts/seed_pipeline.py --reset   # apaga antes os leads-demo antigos
"""

import argparse
from datetime import date
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select

from app.core.constants import CohortStatus, UserRole
from app.db.session import SessionLocal
from app.models import Cohort, Course, Lead, LeadProfile, User
from app.schemas.deal import DealCreate
from app.services.analysis import analyze_lead
from app.services.deals import create_deal_for_lead
from app.services.imports import import_chat

CHATS_DIR = Path(__file__).parent / "pipeline_chats"
COURSE_NAME = "Master 3.0 — Aperfeiçoamento Clínico"
COHORT_NAME = "Master 3.0 — Turma 2027"

# E-mails dos leads-demo fictícios do seed antigo — removidos com --reset (cascateia
# para deals/conversas/perfis via cascade="all, delete-orphan" do relacionamento).
STALE_DEMO_EMAILS = [
    "carlos.silva@email.com",
    "beatriz@email.com",
    "ricardo@email.com",
    "carla@email.com",
    "helena@email.com",
    "paulo@email.com",
    "fabio@email.com",
    "mariana@email.com",
    "thiago@email.com",
    "elena@email.com",
]

# (arquivo, nome do lead, e-mail, telefone, origem, estágio do deal)
# O estágio casa com o prefixo do arquivo (situation→Novo, problem→Contatado,
# implication→Negociando, need_payoff→Aprovado).
MANIFEST = [
    ("01_novo_iniciado_ana-souza.txt", "Ana Souza", "pipeline-01@captus.demo",
     "+55 11 98123-0001", "Instagram", "Novo"),
    ("02_novo_analogico_joao-bittencourt.txt", "Dr. João Bittencourt", "pipeline-02@captus.demo",
     "+55 21 99456-0002", "Indicação", "Novo"),
    ("03_novo_recem_marina-castro.txt", "Marina Castro", "pipeline-03@captus.demo",
     "+55 31 98765-0003", "Site Direto", "Novo"),
    ("04_novo_protesista_eduardo-prado.txt", "Eduardo Prado", "pipeline-04@captus.demo",
     "+55 41 99234-0004", "Site Direto", "Novo"),
    ("05_novo_iniciado_patricia-nunes.txt", "Patrícia Nunes", "pipeline-05@captus.demo",
     "+55 51 98567-0005", "Instagram", "Novo"),
    ("06_contatado_analogico_roberto-lima.txt", "Dr. Roberto Lima", "pipeline-06@captus.demo",
     "+55 11 99678-0006", "WhatsApp", "Contatado"),
    ("07_contatado_recem_camila-rocha.txt", "Camila Rocha", "pipeline-07@captus.demo",
     "+55 19 98345-0007", "E-mail", "Contatado"),
    ("08_contatado_protesista_sergio-andrade.txt", "Sérgio Andrade", "pipeline-08@captus.demo",
     "+55 27 99876-0008", "Indicação", "Contatado"),
    ("09_contatado_iniciado_luciana-freitas.txt", "Luciana Freitas", "pipeline-09@captus.demo",
     "+55 62 98432-0009", "WhatsApp", "Contatado"),
    ("10_contatado_analogico_fernanda-dias.txt", "Dra. Fernanda Dias", "pipeline-10@captus.demo",
     "+55 71 99543-0010", "Instagram", "Contatado"),
    ("11_negociando_recem_bruno-tavares.txt", "Bruno Tavares", "pipeline-11@captus.demo",
     "+55 11 98654-0011", "WhatsApp", "Negociando"),
    ("12_negociando_protesista_renata-coelho.txt", "Renata Coelho", "pipeline-12@captus.demo",
     "+55 48 99765-0012", "Indicação", "Negociando"),
    ("13_negociando_iniciado_marcelo-vidal.txt", "Marcelo Vidal", "pipeline-13@captus.demo",
     "+55 85 98876-0013", "Site Direto", "Negociando"),
    ("14_negociando_analogico_gustavo-pereira.txt", "Dr. Gustavo Pereira",
     "pipeline-14@captus.demo", "+55 11 99987-0014", "Indicação", "Negociando"),
    ("15_negociando_recem_tatiane-moraes.txt", "Tatiane Moraes", "pipeline-15@captus.demo",
     "+55 81 98098-0015", "Instagram", "Negociando"),
    ("16_negociando_protesista_andre-figueiredo.txt", "Dr. André Figueiredo",
     "pipeline-16@captus.demo", "+55 11 99109-0016", "E-mail", "Negociando"),
    ("17_aprovado_iniciado_carolina-mendonca.txt", "Carolina Mendonça", "pipeline-17@captus.demo",
     "+55 11 98210-0017", "WhatsApp", "Aprovado"),
    ("18_aprovado_analogico_ricardo-bastos.txt", "Dr. Ricardo Bastos", "pipeline-18@captus.demo",
     "+55 21 99321-0018", "Indicação", "Aprovado"),
    ("19_aprovado_recem_juliana-peixoto.txt", "Juliana Peixoto", "pipeline-19@captus.demo",
     "+55 31 98432-0019", "Site Direto", "Aprovado"),
    ("20_aprovado_protesista_henrique-vasques.txt", "Dr. Henrique Vasques",
     "pipeline-20@captus.demo", "+55 11 99543-0020", "Indicação", "Aprovado"),
]


def _ensure_cohort(session) -> Cohort:
    """Garante o curso Master + a turma ABERTA 2027 (mesma de scripts/seed.py). Idempotente."""
    course = session.scalar(select(Course).where(Course.name == COURSE_NAME))
    if course is None:
        course = Course(
            name=COURSE_NAME,
            price=Decimal("22250.00"),
            duration="10 meses (160h)",
            description="Enfoque clínico com pacientes reais. FOUSP/USP-SP.",
            modality="Presencial",
            active=True,
        )
        session.add(course)
        session.flush()
    cohort = session.scalar(
        select(Cohort).where(Cohort.course_id == course.id, Cohort.name == COHORT_NAME)
    )
    if cohort is None:
        cohort = Cohort(
            course_id=course.id,
            name=COHORT_NAME,
            start_date=date(2027, 3, 1),
            end_date=date(2027, 12, 18),
            capacity=30,
            price_per_slot=Decimal("22250.00"),
            status=CohortStatus.OPEN,
        )
        session.add(cohort)
        session.flush()
    session.commit()
    return cohort


def _current_seller(session) -> User | None:
    """Seller seedado (usuário corrente implícito), espelhando services/leads.py."""
    return session.scalars(
        select(User).where(User.role == UserRole.SELLER).order_by(User.id).limit(1)
    ).first()


def _get_or_create_lead(session, *, name, email, phone, source, seller) -> tuple[Lead, bool]:
    lead = session.scalar(select(Lead).where(Lead.email == email))
    if lead is not None:
        return lead, False
    lead = Lead(
        name=name,
        email=email,
        phone=phone,
        source=source,
        assignee_id=seller.id if seller else None,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    return lead, True


def _has_profile(session, lead_id: int) -> bool:
    return (
        session.scalar(select(LeadProfile.id).where(LeadProfile.lead_id == lead_id))
        is not None
    )


def _reset_demo_leads(session) -> int:
    """Apaga os leads-demo fictícios antigos (cascateia deals/conversas/perfis)."""
    leads = session.scalars(
        select(Lead).where(Lead.email.in_(STALE_DEMO_EMAILS))
    ).all()
    for lead in leads:
        session.delete(lead)
    session.commit()
    return len(leads)


def run(*, reset: bool = False) -> None:
    if not CHATS_DIR.is_dir():
        print(f"Diretório de conversas não encontrado: {CHATS_DIR}")
        return

    stats = {"created": 0, "skipped": 0, "errors": 0, "deleted": 0}

    with SessionLocal() as session:
        if reset:
            stats["deleted"] = _reset_demo_leads(session)
            if stats["deleted"]:
                print(f"--reset: {stats['deleted']} leads-demo antigos removidos.")

        cohort = _ensure_cohort(session)
        seller = _current_seller(session)

        for filename, name, email, phone, source, stage in MANIFEST:
            path = CHATS_DIR / filename
            if not path.is_file():
                print(f"  ⚠️  {filename}: arquivo não encontrado, pulando.")
                stats["errors"] += 1
                continue

            try:
                lead, created = _get_or_create_lead(
                    session, name=name, email=email, phone=phone,
                    source=source, seller=seller,
                )

                # Lead já analisado → nada a fazer (idempotente).
                if not created and _has_profile(session, lead.id):
                    print(f"  ↷  {name}: já existe com perfil, pulando.")
                    stats["skipped"] += 1
                    continue

                text = path.read_text(encoding="utf-8")
                import_chat(session, text=text, lead_id=lead.id, source=source)

                try:
                    create_deal_for_lead(
                        session, lead.id, DealCreate(cohort_id=cohort.id, stage=stage)
                    )
                except HTTPException as exc:
                    if exc.status_code != 409:  # 409 = deal já existe; outro erro propaga.
                        raise
                    session.rollback()

                analyze_lead(session, lead.id)
                print(f"  ✓  {name} → {stage} ({source})")
                stats["created"] += 1
            except Exception as exc:  # noqa: BLE001 — um lead ruim não aborta o lote.
                session.rollback()
                print(f"  ⚠️  {name}: {exc}")
                stats["errors"] += 1

    print(
        f"Pipeline: {stats['created']} criados | {stats['skipped']} pulados | "
        f"{stats['errors']} erros"
        + (f" | {stats['deleted']} demo-antigos removidos" if reset else "")
        + "."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed do pipeline de vendas em aberto do Master 3.0 (importa + analisa)."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Apaga os leads-demo fictícios antigos antes de popular o pipeline.",
    )
    args = parser.parse_args()
    run(reset=args.reset)
