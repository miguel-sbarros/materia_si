"""Importa todos os modelos para registrar mapeamentos no metadata da Base.

Importar ``app.models`` garante que ``Base.metadata`` conheça todas as tabelas
(create_all nos testes; autogenerate do Alembic).
"""

from app.models.course import Cohort, Course
from app.models.deal import Deal, DealEvent
from app.models.lead import Lead
from app.models.user import User

__all__ = ["User", "Course", "Cohort", "Lead", "Deal", "DealEvent"]
