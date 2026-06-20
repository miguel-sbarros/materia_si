"""Seed idempotente de dados demo (upsert por chave natural — re-execução não duplica).

Cria: 1 admin (Marcelo Romano) + 1 seller (Ana Costa), 3 cursos, turmas, e leads com
deals abrangendo Novo/Contatado/Negociando + won (→ Matriculado) + lost (→ Perdido),
incluindo um lead com dois deals em cursos diferentes (Elena: Imersão won + Especialização).
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.constants import CohortStatus, DealStage, DealStatus, UserRole
from app.db.session import SessionLocal
from app.models import Cohort, Course, Deal, DealEvent, Lead, User


def get_or_create(session, model, defaults=None, **keys):
    obj = session.scalar(select(model).filter_by(**keys))
    if obj is not None:
        return obj, False
    obj = model(**keys, **(defaults or {}))
    session.add(obj)
    session.flush()
    return obj, True


def run() -> None:
    with SessionLocal() as session:
        admin, _ = get_or_create(
            session, User, email="marcelo@mrdigital.com",
            defaults={"name": "Prof. Marcelo Romano", "role": UserRole.ADMIN, "initials": "MR"},
        )
        seller, _ = get_or_create(
            session, User, email="ana.costa@mrdigital.com",
            defaults={"name": "Dra. Ana Costa", "role": UserRole.SELLER, "initials": "AC"},
        )

        imersao, _ = get_or_create(
            session, Course, name="Imersão em Implantodontia Digital",
            defaults={"price": Decimal("5900.00"), "duration": "3 dias (24h)",
                      "description": "Fluxo digital completo e cirurgia guiada. FOUSP/USP-SP."},
        )
        master, _ = get_or_create(
            session, Course, name="Master 3.0 — Aperfeiçoamento Clínico",
            defaults={"price": Decimal("22250.00"), "duration": "10 meses (160h)",
                      "description": "Enfoque clínico com pacientes reais. FOUSP/USP-SP."},
        )
        espec, _ = get_or_create(
            session, Course, name="Especialização em Implantodontia Digital",
            defaults={"duration": "24 meses (1.200h)",
                      "description": "Formação completa em implantodontia digital. FOUSP/USP-SP."},
        )

        imersao_t1, _ = get_or_create(
            session, Cohort, course_id=imersao.id, name="Imersão — Turma T1 2026",
            defaults={"capacity": 30, "price_per_slot": Decimal("5900.00"),
                      "start_date": date(2026, 3, 10), "end_date": date(2026, 3, 12),
                      "status": CohortStatus.ACTIVE},
        )
        imersao_t2, _ = get_or_create(
            session, Cohort, course_id=imersao.id, name="Imersão — Turma T2 2026",
            defaults={"capacity": 30, "price_per_slot": Decimal("5900.00"),
                      "start_date": date(2026, 9, 8), "end_date": date(2026, 9, 10),
                      "status": CohortStatus.OPEN},
        )
        master_t2, _ = get_or_create(
            session, Cohort, course_id=master.id, name="Master 3.0 — Turma T2 2026",
            defaults={"capacity": 30, "price_per_slot": Decimal("22250.00"),
                      "start_date": date(2026, 5, 5), "end_date": date(2027, 2, 28),
                      "status": CohortStatus.ACTIVE},
        )
        espec_t1, _ = get_or_create(
            session, Cohort, course_id=espec.id, name="Especialização — Turma T1 2026",
            defaults={"capacity": 24, "start_date": date(2026, 4, 1),
                      "end_date": date(2028, 3, 31), "status": CohortStatus.ACTIVE},
        )

        # (nome, email, origem, [(cohort, stage, status, lost_reason)])
        seed_leads = [
            ("Dr. Carlos Silva", "carlos.silva@email.com", "Instagram",
             [(imersao_t1, DealStage.NOVO, DealStatus.OPEN, None)]),
            ("Dra. Beatriz Santos", "beatriz@email.com", "WhatsApp",
             [(imersao_t1, DealStage.NOVO, DealStatus.OPEN, None)]),
            ("Dr. Ricardo Oliveira", "ricardo@email.com", "Instagram",
             [(master_t2, DealStage.CONTATADO, DealStatus.OPEN, None)]),
            ("Dra. Carla Mendes", "carla@email.com", "WhatsApp",
             [(imersao_t1, DealStage.CONTATADO, DealStatus.OPEN, None)]),
            ("Dra. Helena Martins", "helena@email.com", "Indicação",
             [(master_t2, DealStage.NEGOCIANDO, DealStatus.OPEN, None)]),
            ("Dr. Paulo Ferreira", "paulo@email.com", "Instagram",
             [(imersao_t1, DealStage.NEGOCIANDO, DealStatus.OPEN, None)]),
            ("Dr. Fabio J.", "fabio@email.com", "Indicação",
             [(imersao_t1, DealStage.NEGOCIANDO, DealStatus.WON, None)]),
            ("Dra. Mariana Luz", "mariana@email.com", "Indicação",
             [(master_t2, DealStage.NEGOCIANDO, DealStatus.WON, None)]),
            ("Dr. Thiago Costa", "thiago@email.com", "Instagram",
             [(imersao_t2, DealStage.NEGOCIANDO, DealStatus.LOST, "Sem orçamento neste momento")]),
            ("Elena Rodriguez", "elena@email.com", "WhatsApp",
             [(imersao_t1, DealStage.NEGOCIANDO, DealStatus.WON, None),
              (espec_t1, DealStage.NEGOCIANDO, DealStatus.OPEN, None)]),
        ]

        for name, email, source, deals in seed_leads:
            lead, _ = get_or_create(
                session, Lead, email=email,
                defaults={"name": name, "source": source, "assignee_id": seller.id},
            )
            for cohort, stage, status, lost_reason in deals:
                deal, created = get_or_create(
                    session, Deal, lead_id=lead.id, cohort_id=cohort.id,
                    defaults={"stage": stage, "status": status, "lost_reason": lost_reason},
                )
                if created:
                    session.add(DealEvent(
                        deal_id=deal.id, to_stage=stage, to_status=status,
                        reason="Criado via seed", user_id=seller.id,
                    ))

        session.commit()
    print("Seed concluído (idempotente).")


if __name__ == "__main__":
    run()
