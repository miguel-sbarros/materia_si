"""Seed idempotente de dados demo (upsert por chave natural — re-execução não duplica).

Cria: 1 admin (Marcelo Romano) + 1 seller (Ana Costa), 3 cursos e suas turmas — incluindo
a turma ABERTA ``Master 3.0 — Turma 2027`` que recebe o pipeline de leads realistas
(``scripts/seed_pipeline.py``). Não cria leads/deals demo aqui: o pipeline de vendas em
aberto é populado pelo ``seed_pipeline.py`` (20 conversas reais analisadas pela IA).
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.constants import CohortStatus, UserRole
from app.db.session import SessionLocal
from app.models import Cohort, Course, User


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
        # Turma ABERTA do Master — alvo do pipeline de leads realistas (seed_pipeline.py).
        get_or_create(
            session, Cohort, course_id=master.id, name="Master 3.0 — Turma 2027",
            defaults={"capacity": 30, "price_per_slot": Decimal("22250.00"),
                      "start_date": date(2027, 3, 1), "end_date": date(2027, 12, 18),
                      "status": CohortStatus.OPEN},
        )
        get_or_create(
            session, Cohort, course_id=espec.id, name="Especialização — Turma T1 2026",
            defaults={"capacity": 24, "start_date": date(2026, 4, 1),
                      "end_date": date(2028, 3, 31), "status": CohortStatus.ACTIVE},
        )

        session.commit()
    print("Seed concluído (idempotente).")


if __name__ == "__main__":
    run()
