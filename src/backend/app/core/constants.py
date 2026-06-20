"""Constantes e enums de domínio do Captus.

Dois conceitos de "estágio" que NUNCA se confundem:
- ``DealStage`` — posição comercial no funil (Kanban), por deal (lead × cohort).
- O estágio SPIN (análise de diálogo) vive do lado da conversa/perfil — não aqui.
"""

from enum import StrEnum

# Dimensão do vetor de embeddings (também em Settings; constante para migrações/schemas).
EMBEDDING_DIM = 384


class UserRole(StrEnum):
    """Papéis de acesso. Enforcement de autorização faz parte da auth (diferida)."""

    SELLER = "seller"
    ADMIN = "admin"


class DealStage(StrEnum):
    """Posição no funil comercial (colunas abertas do Kanban)."""

    NOVO = "Novo"
    CONTATADO = "Contatado"
    NEGOCIANDO = "Negociando"


class DealStatus(StrEnum):
    """Estado terminal do deal. A API mapeia won→'Matriculado', lost→'Perdido'."""

    OPEN = "open"
    WON = "won"
    LOST = "lost"


class CohortStatus(StrEnum):
    """Ciclo de vida da turma (janela de tempo)."""

    OPEN = "open"
    ACTIVE = "active"
    FINISHED = "finished"
