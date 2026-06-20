"""Base declarativa do SQLAlchemy 2.0 e helper de coluna enum.

Enums são armazenados como VARCHAR + CHECK (``native_enum=False``), guardando o
``.value`` legível (ex.: "Novo", "open") em vez do nome do membro.
"""

from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def enum_column(enum_cls: type, name: str) -> SAEnum:
    """Coluna enum portável: VARCHAR + CHECK constraint nomeada, guardando os values."""

    return SAEnum(
        enum_cls,
        name=name,
        native_enum=False,
        values_callable=lambda c: [member.value for member in c],
    )
