"""Importa todos os modelos para registrar mapeamentos no metadata da Base.

Importar ``app.models`` garante que ``Base.metadata`` conheça todas as tabelas
(create_all nos testes; autogenerate do Alembic).
"""

from app.models.conversation import Conversation, Message
from app.models.copilot import CopilotMessage, CopilotSession
from app.models.course import Cohort, Course
from app.models.deal import Deal, DealEvent
from app.models.knowledge import KnowledgeChunk
from app.models.lead import Lead
from app.models.lead_profile import LeadProfile
from app.models.persona import Persona
from app.models.user import User

__all__ = [
    "User",
    "Course",
    "Cohort",
    "Lead",
    "Deal",
    "DealEvent",
    "Conversation",
    "Message",
    "LeadProfile",
    "KnowledgeChunk",
    "CopilotSession",
    "CopilotMessage",
    "Persona",
]
