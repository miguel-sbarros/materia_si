"""CourseModule — módulo/tema da ementa de um curso (REQF04, conteúdo).

Migra o conteúdo antes parseado de ``playbook/cursos.md`` para o banco, tornando a ementa
editável (CRUD). Salvar/editar/excluir um módulo agenda a re-ingestão dos chunks daquele
curso no RAG do copiloto (``source='course'``), de forma idempotente.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.course import Course


class CourseModule(Base):
    __tablename__ = "course_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Ordem de exibição na ementa.
    position: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    # Carga horária do módulo (ex.: "3 dias - 24 horas").
    carga: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course: Mapped["Course"] = relationship(back_populates="modules")
