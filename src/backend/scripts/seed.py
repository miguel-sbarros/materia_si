"""Seed idempotente de dados demo (upsert por chave natural; re-execução não duplica).

Cria: 1 admin (Marcelo Romano) + 1 seller (Ana Costa), 3 cursos e suas turmas, incluindo
a turma ABERTA ``Master 3.0 — Turma 2027`` que recebe o pipeline de leads realistas
(``scripts/seed_pipeline.py``). Não cria leads/deals demo aqui: o pipeline de vendas em
aberto é populado pelo ``seed_pipeline.py`` (20 conversas reais analisadas pela IA).

Também semeia os módulos de ementa (``course_modules``) a partir de ``cursos.md`` e garante
uma matrícula ativa para cada deal ``won`` existente (fonte da verdade das vagas).
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.core.constants import CohortStatus, DealStatus, EnrollmentStatus, UserRole
from app.db.session import SessionLocal
from app.models import Cohort, Course, CourseModule, Deal, Enrollment, User
from app.services import course_content


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
        get_or_create(
            session, User, email="marcelo@mrdigital.com",
            defaults={"name": "Prof. Marcelo Romano", "role": UserRole.ADMIN, "initials": "MR"},
        )
        get_or_create(
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

        get_or_create(
            session, Cohort, course_id=imersao.id, name="Imersão — Turma T1 2026",
            defaults={"capacity": 30, "price_per_slot": Decimal("5900.00"),
                      "start_date": date(2026, 3, 10), "end_date": date(2026, 3, 12),
                      "status": CohortStatus.ACTIVE},
        )
        get_or_create(
            session, Cohort, course_id=imersao.id, name="Imersão — Turma T2 2026",
            defaults={"capacity": 30, "price_per_slot": Decimal("5900.00"),
                      "start_date": date(2026, 9, 8), "end_date": date(2026, 9, 10),
                      "status": CohortStatus.OPEN},
        )
        get_or_create(
            session, Cohort, course_id=master.id, name="Master 3.0 — Turma T2 2026",
            defaults={"capacity": 30, "price_per_slot": Decimal("22250.00"),
                      "start_date": date(2026, 5, 5), "end_date": date(2027, 2, 28),
                      "status": CohortStatus.ACTIVE},
        )
        # Turma ABERTA do Master, alvo do pipeline de leads realistas (seed_pipeline.py).
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

        # Invariante de vagas: todo deal won tem uma matrícula ativa correspondente.
        for deal in session.scalars(
            select(Deal).where(Deal.status == DealStatus.WON)
        ).all():
            get_or_create(
                session, Enrollment, lead_id=deal.lead_id, cohort_id=deal.cohort_id,
                defaults={"deal_id": deal.id, "status": EnrollmentStatus.ACTIVE},
            )

        _seed_course_modules(session, [imersao, master, espec])

        session.commit()
    print("Seed concluído (idempotente).")


def _seed_course_modules(session, courses) -> None:
    """Popula ``course_modules`` a partir da ementa parseada de ``cursos.md`` (idempotente).

    Casa cada curso semeado com a entrada do ``cursos.md`` por nome; cria um módulo por
    linha do syllabus (chave natural = ``course_id`` + ``position``). Re-execução não duplica.
    """
    for course in courses:
        ementa = course_content.course_ementa(course.name)
        if not ementa or not ementa.get("syllabus"):
            continue
        for position, row in enumerate(ementa["syllabus"]):
            get_or_create(
                session, CourseModule, course_id=course.id, position=position,
                defaults={"title": row.get("tema") or f"Módulo {position + 1}",
                          "content": row.get("conteudo"), "carga": row.get("carga")},
            )


if __name__ == "__main__":
    run()
