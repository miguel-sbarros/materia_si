"""enrollments — matrícula de lead em turma (REQF06)

Revision ID: 0008_enrollments
Revises: 0007_deal_stage_aprovado
Create Date: 2026-06-22

Aditiva: encadeia em 0007_deal_stage_aprovado. Enum status (VARCHAR + CHECK).
UNIQUE(lead_id, cohort_id) impede matrícula duplicada.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_enrollments"
down_revision: str | None = "0007_deal_stage_aprovado"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("cohort_id", sa.Integer(), nullable=False),
        sa.Column("deal_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "active", "cancelled", name="enrollment_status", native_enum=False
            ),
            server_default="active",
            nullable=False,
        ),
        sa.Column("source", sa.String(length=60), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"]),
        sa.ForeignKeyConstraint(["cohort_id"], ["cohorts.id"]),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
        sa.UniqueConstraint("lead_id", "cohort_id", name="uq_enrollments_lead_cohort"),
    )


def downgrade() -> None:
    op.drop_table("enrollments")
