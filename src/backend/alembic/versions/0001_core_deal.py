"""core + deal schema (users, courses, cohorts, leads, deals, deal_events) + pgvector ext

Revision ID: 0001_core_deal
Revises:
Create Date: 2026-06-20

Enums são VARCHAR + CHECK (native_enum=False), guardando os values legíveis.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_core_deal"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensão pgvector (prova a imagem; colunas vector chegam em P4).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column(
            "role",
            sa.Enum("seller", "admin", name="user_role", native_enum=False),
            server_default="seller",
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("initials", sa.String(length=8), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "modality", sa.String(length=40), server_default="Presencial", nullable=False
        ),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("duration", sa.String(length=80), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.UniqueConstraint("name", name="uq_courses_name"),
    )

    op.create_table(
        "cohorts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("price_per_slot", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "open", "active", "finished", name="cohort_status", native_enum=False
            ),
            server_default="open",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
    )

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("source", sa.String(length=60), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("external_user_id", sa.String(length=120), nullable=True),
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
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.UniqueConstraint("external_user_id", name="uq_leads_external_user_id"),
    )
    # REQF01: dedupe de email quando informado (índice único parcial).
    op.create_index(
        "uq_leads_email_present",
        "leads",
        ["email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("cohort_id", sa.Integer(), nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "Novo", "Contatado", "Negociando", name="deal_stage", native_enum=False
            ),
            server_default="Novo",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "won", "lost", name="deal_status", native_enum=False),
            server_default="open",
            nullable=False,
        ),
        sa.Column("lost_reason", sa.Text(), nullable=True),
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
        sa.UniqueConstraint("lead_id", "cohort_id", name="uq_deals_lead_cohort"),
        sa.CheckConstraint(
            "status <> 'lost' OR lost_reason IS NOT NULL", name="ck_deals_lost_reason"
        ),
    )

    op.create_table(
        "deal_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("deal_id", sa.Integer(), nullable=False),
        sa.Column(
            "from_stage",
            sa.Enum(
                "Novo",
                "Contatado",
                "Negociando",
                name="deal_event_from_stage",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "to_stage",
            sa.Enum(
                "Novo",
                "Contatado",
                "Negociando",
                name="deal_event_to_stage",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "from_status",
            sa.Enum(
                "open", "won", "lost", name="deal_event_from_status", native_enum=False
            ),
            nullable=True,
        ),
        sa.Column(
            "to_status",
            sa.Enum(
                "open", "won", "lost", name="deal_event_to_status", native_enum=False
            ),
            nullable=True,
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "ts",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("deal_events")
    op.drop_table("deals")
    op.drop_index("uq_leads_email_present", table_name="leads")
    op.drop_table("leads")
    op.drop_table("cohorts")
    op.drop_table("courses")
    op.drop_table("users")
