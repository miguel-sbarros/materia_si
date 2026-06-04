"""
models.py — Esquemas de dados (Pydantic)

Define os contratos de entrada e saída da API do Captus.
Centralizar os schemas em um módulo separado é parte da
separação de responsabilidades: a validação de dados fica
isolada da lógica de rotas (main.py) e do acesso ao banco
(database.py).
"""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class EstagioFunil(str, Enum):
    """Estágios do pipeline comercial (REQF02)."""

    NOVO = "Novo"
    CONTATADO = "Contatado"
    NEGOCIANDO = "Negociando"
    MATRICULADO = "Matriculado"
    PERDIDO = "Perdido"


# --------------------------------------------------------------------------- #
# LEADS (REQF01, REQF02)
# --------------------------------------------------------------------------- #
class LeadBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120, examples=["Dra. Helena Martins"])
    email: EmailStr = Field(..., examples=["helena@exemplo.com"])
    telefone: Optional[str] = Field(None, max_length=20, examples=["+5511999998888"])
    origem: str = Field(..., examples=["Instagram", "Site Direto", "Indicação"])
    estagio: EstagioFunil = Field(default=EstagioFunil.NOVO)


class LeadCreate(LeadBase):
    """Payload de entrada para cadastro de lead."""


class LeadUpdateEstagio(BaseModel):
    """Payload para mover o lead no funil (drag and drop do Kanban)."""

    estagio: EstagioFunil


class Lead(LeadBase):
    """Representação completa de um lead retornada pela API."""

    id: int


# --------------------------------------------------------------------------- #
# CURSOS e TURMAS (REQF04, REQF05) — relação 1:N
# --------------------------------------------------------------------------- #
class CursoBase(BaseModel):
    nome: str = Field(..., examples=["Imersão em Implantodontia Digital"])
    modalidade: str = Field(default="Presencial", examples=["Presencial", "Híbrido"])
    ativo: bool = Field(default=True)


class CursoCreate(CursoBase):
    pass


class Curso(CursoBase):
    id: int


class TurmaBase(BaseModel):
    curso_id: int = Field(..., examples=[1])
    data_inicio: date = Field(..., examples=["2026-05-01"])
    vagas_totais: int = Field(..., gt=0, examples=[30])
    investimento: float = Field(..., ge=0, examples=[22250.0])


class TurmaCreate(TurmaBase):
    pass


class Turma(TurmaBase):
    id: int
    vagas_ocupadas: int = Field(default=0)

    @property
    def vagas_disponiveis(self) -> int:
        return self.vagas_totais - self.vagas_ocupadas


# --------------------------------------------------------------------------- #
# MATRÍCULA (REQF06)
# --------------------------------------------------------------------------- #
class MatriculaCreate(BaseModel):
    lead_id: int = Field(..., examples=[1])
    turma_id: int = Field(..., examples=[1])


class Matricula(BaseModel):
    id: int
    lead_id: int
    turma_id: int
    data_matricula: date


# --------------------------------------------------------------------------- #
# RESPOSTAS GENÉRICAS
# --------------------------------------------------------------------------- #
class MensagemResposta(BaseModel):
    status: str
    detalhe: Optional[str] = None


class StatusBanco(BaseModel):
    banco_conectado: bool
    fonte_de_dados: str
    detalhe: str
