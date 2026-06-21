"""add 'Aprovado' open stage to deal_stage CHECK constraints

Revision ID: 0007_deal_stage_aprovado
Revises: 0006_personas
Create Date: 2026-06-20

Nova coluna aberta "Aprovado" no funil (lead sinalizou querer o curso, mas ainda
não matriculado), após "Negociando". Os estágios são enums VARCHAR + CHECK
(native_enum=False), então atualizamos as três CHECKs nomeadas (deal_stage,
deal_event_from_stage, deal_event_to_stage) para incluir 'Aprovado'.

Os DROPs usam ``IF EXISTS`` porque o SQLAlchemy 2.0 não materializa a CHECK
nomeada por padrão (``create_constraint=False``) — esta migração também passa a
garantir que as constraints existam e reflitam o enum.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007_deal_stage_aprovado"
down_revision: str | None = "0006_personas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (constraint name, table, column)
_STAGE_CHECKS = [
    ("deal_stage", "deals", "stage"),
    ("deal_event_from_stage", "deal_events", "from_stage"),
    ("deal_event_to_stage", "deal_events", "to_stage"),
]


def upgrade() -> None:
    values = "'Novo', 'Contatado', 'Negociando', 'Aprovado'"
    for name, table, column in _STAGE_CHECKS:
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{name}"')
        op.create_check_constraint(name, table, f"{column} IN ({values})")


def downgrade() -> None:
    values = "'Novo', 'Contatado', 'Negociando'"
    for name, table, column in _STAGE_CHECKS:
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS "{name}"')
        op.create_check_constraint(name, table, f"{column} IN ({values})")
