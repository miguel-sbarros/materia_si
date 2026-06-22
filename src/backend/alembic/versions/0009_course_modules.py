"""course_modules — módulos/ementa de curso (REQF04, conteúdo)

Revision ID: 0009_course_modules
Revises: 0008_enrollments
Create Date: 2026-06-22

Aditiva: encadeia em 0008_enrollments. Conteúdo da ementa editável no banco; reflete no
RAG do copiloto via re-ingestão em background.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009_course_modules"
down_revision: str | None = "0008_enrollments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "course_modules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column("carga", sa.String(length=80), nullable=True),
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
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
    )


def downgrade() -> None:
    op.drop_table("course_modules")
