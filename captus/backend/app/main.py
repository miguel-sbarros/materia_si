"""
main.py — Camada de API (FastAPI)

Responsabilidade única: expor os endpoints HTTP, validar entrada/saída
com os schemas de models.py e delegar a persistência para database.py.

Seguindo o que foi visto na Aula 5 (Backend Lab):
  - from fastapi import FastAPI, HTTPException
  - modelagem de respostas com Pydantic
  - documentação automática em /docs (Swagger) e /redoc

A separação main.py / models.py / database.py reflete o item 6.1 do
roteiro (estrutura de pastas e separação de responsabilidades).
"""

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from . import database
from .models import (
    Curso,
    CursoCreate,
    EstagioFunil,
    Lead,
    LeadCreate,
    LeadUpdateEstagio,
    Matricula,
    MatriculaCreate,
    MensagemResposta,
    StatusBanco,
    Turma,
    TurmaCreate,
)

app = FastAPI(
    title="Captus API",
    description=(
        "Backend do Captus — plataforma de CRM e gestão de turmas para o "
        "setor educacional (MR Digital). Integra gestão de leads (funil), "
        "cursos/turmas e controle automático de vagas."
    ),
    version="2.0.0",
)

# O frontend Streamlit roda em outro processo/porta; liberamos CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Saúde / status do banco (Aula 6 — backend reporta o status da conexão)
# --------------------------------------------------------------------------- #
@app.get("/", tags=["Status"], summary="Healthcheck")
def raiz():
    return {"servico": "Captus API", "versao": "2.0.0", "status": "no ar"}


@app.get("/status", response_model=StatusBanco, tags=["Status"],
         summary="Verifica a conexão com o banco de dados")
def status_banco():
    return database.get_status_banco()


# --------------------------------------------------------------------------- #
# LEADS (REQF01, REQF02)
# --------------------------------------------------------------------------- #
@app.get("/leads/", response_model=List[Lead], tags=["Leads"],
         summary="Lista leads (opcionalmente filtrados por estágio)")
def listar_leads(estagio: Optional[EstagioFunil] = Query(default=None)):
    valor = estagio.value if estagio else None
    return database.listar_leads(valor)


@app.get("/leads/{lead_id}", response_model=Lead, tags=["Leads"],
         summary="Busca um lead pelo ID")
def obter_lead(lead_id: int):
    lead = database.obter_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return lead


@app.post("/leads/", response_model=Lead, status_code=status.HTTP_201_CREATED,
          tags=["Leads"], summary="Cadastra um novo lead (REQF01)")
def criar_lead(payload: LeadCreate):
    # Critério de aceitação do REQF01: impedir duplicidade de e-mail
    if database.email_existe(payload.email):
        raise HTTPException(status_code=409, detail="Já existe um lead com este e-mail")
    dados = payload.model_dump()
    dados["estagio"] = payload.estagio.value
    dados["email"] = str(payload.email)
    return database.criar_lead(dados)


@app.patch("/leads/{lead_id}/estagio", response_model=Lead, tags=["Leads"],
           summary="Move o lead no funil (REQF02 — drag and drop)")
def mover_lead(lead_id: int, payload: LeadUpdateEstagio):
    if not database.obter_lead(lead_id):
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    return database.atualizar_estagio(lead_id, payload.estagio.value)


# --------------------------------------------------------------------------- #
# CURSOS e TURMAS (REQF04, REQF05) — relação 1:N
# --------------------------------------------------------------------------- #
@app.get("/cursos/", response_model=List[Curso], tags=["Cursos"],
         summary="Lista cursos ativos")
def listar_cursos():
    return database.listar_cursos()


@app.post("/cursos/", response_model=Curso, status_code=status.HTTP_201_CREATED,
          tags=["Cursos"], summary="Cadastra um curso (REQF04)")
def criar_curso(payload: CursoCreate):
    return database.criar_curso(payload.model_dump())


@app.get("/turmas/", response_model=List[Turma], tags=["Turmas"],
         summary="Lista turmas (opcionalmente de um curso)")
def listar_turmas(curso_id: Optional[int] = Query(default=None)):
    return database.listar_turmas(curso_id)


@app.get("/turmas/{turma_id}", response_model=Turma, tags=["Turmas"],
         summary="Detalhe de uma turma com ocupação de vagas")
def obter_turma(turma_id: int):
    turma = database.obter_turma(turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    return turma


@app.post("/turmas/", response_model=Turma, status_code=status.HTTP_201_CREATED,
          tags=["Turmas"], summary="Cadastra uma turma vinculada a um curso (REQF04)")
def criar_turma(payload: TurmaCreate):
    cursos = {c["id"] for c in database.listar_cursos()}
    if payload.curso_id not in cursos:
        raise HTTPException(status_code=404, detail="Curso informado não existe")
    dados = payload.model_dump()
    dados["data_inicio"] = payload.data_inicio.isoformat()
    return database.criar_turma(dados)


# --------------------------------------------------------------------------- #
# MATRÍCULA (REQF05 + REQF06)
# --------------------------------------------------------------------------- #
@app.post("/matriculas/", response_model=Matricula,
          status_code=status.HTTP_201_CREATED, tags=["Matrículas"],
          summary="Matricula um lead em uma turma (REQF06) e atualiza vagas (REQF05)")
def criar_matricula(payload: MatriculaCreate):
    lead = database.obter_lead(payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    turma = database.obter_turma(payload.turma_id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    # Critério de aceitação do REQF05: impedir matrícula em turma lotada
    disponiveis = turma["vagas_totais"] - turma["vagas_ocupadas"]
    if disponiveis <= 0:
        raise HTTPException(status_code=409, detail="Turma lotada — sem vagas disponíveis")
    return database.criar_matricula(payload.lead_id, payload.turma_id)
