"""
database.py — Camada de persistência

Responsabilidade única: falar com o banco de dados.

Este módulo segue o que foi visto nas aulas de forma incremental:

  * Aula 5 (Backend Lab): a "base" começou como uma lista Python em
    memória (SELLERS_DB). Mantemos esse mesmo conceito de fallback em
    memória para que a API continue funcionando mesmo sem o Postgres
    no ar (útil para os screenshots do /docs e /redoc).

  * Aula 6 (Docker Lab): o backend deve consumir os parâmetros do banco
    PostgreSQL via VARIÁVEIS DE AMBIENTE e verificar/reportar o status
    da conexão. É exatamente o que get_status_banco() faz.

  * Aula 7 (Database Lab): as tabelas customers/stores/orders foram
    adaptadas para o domínio do Captus (leads, cursos, turmas,
    matrículas), com PK, FK, UNIQUE e índices.

Estratégia: se o PostgreSQL estiver acessível, usamos psycopg2.
Caso contrário, caímos para o repositório em memória, sinalizando
claramente a fonte de dados em /status.
"""

import os
from datetime import date
from typing import List, Optional

try:
    import psycopg2
    import psycopg2.extras
    _PSYCOPG_DISPONIVEL = True
except ImportError:  # ambiente sem o driver instalado
    _PSYCOPG_DISPONIVEL = False


# --------------------------------------------------------------------------- #
# Configuração via variáveis de ambiente (Aula 6 — Step 17 / 7.3 do roteiro)
# --------------------------------------------------------------------------- #
DB_HOST = os.getenv("DB_HOST", "database")   # nome do serviço no docker-compose
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")


def _conectar():
    """Tenta abrir conexão com o PostgreSQL. Retorna None se indisponível."""
    if not _PSYCOPG_DISPONIVEL:
        return None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=3,
        )
        return conn
    except Exception:
        return None


def banco_disponivel() -> bool:
    conn = _conectar()
    if conn is not None:
        conn.close()
        return True
    return False


def get_status_banco() -> dict:
    """Verifica e reporta o status da conexão (REQNF + Aula 6)."""
    if banco_disponivel():
        return {
            "banco_conectado": True,
            "fonte_de_dados": "PostgreSQL",
            "detalhe": f"Conectado a {DB_HOST}:{DB_PORT}/{DB_NAME}",
        }
    return {
        "banco_conectado": False,
        "fonte_de_dados": "Memória (fallback)",
        "detalhe": "PostgreSQL indisponível; usando repositório em memória.",
    }


# =========================================================================== #
# REPOSITÓRIO EM MEMÓRIA (fallback — evolução direta do SELLERS_DB da Aula 5)
# =========================================================================== #
class _RepositorioMemoria:
    def __init__(self):
        self._reset()

    def _reset(self):
        # Dados simulados com valores realistas (como no protótipo de alta fidelidade)
        self.leads = [
            {"id": 1, "nome": "Dra. Helena Martins", "email": "helena@exemplo.com",
             "telefone": "+5511988887777", "origem": "Indicação", "estagio": "Negociando"},
            {"id": 2, "nome": "Dr. Ricardo Oliveira", "email": "ricardo@exemplo.com",
             "telefone": "+5511977776666", "origem": "Site Direto", "estagio": "Contatado"},
            {"id": 3, "nome": "Dra. Beatriz Santos", "email": "beatriz@exemplo.com",
             "telefone": "+5511966665555", "origem": "Instagram", "estagio": "Novo"},
        ]
        self.cursos = [
            {"id": 1, "nome": "Imersão em Implantodontia Digital",
             "modalidade": "Presencial", "ativo": True},
            {"id": 2, "nome": "Dermato-Cirurgia Avançada",
             "modalidade": "Híbrido", "ativo": True},
        ]
        self.turmas = [
            {"id": 1, "curso_id": 1, "data_inicio": "2026-05-01",
             "vagas_totais": 30, "vagas_ocupadas": 24, "investimento": 22250.0},
            {"id": 2, "curso_id": 2, "data_inicio": "2026-08-15",
             "vagas_totais": 20, "vagas_ocupadas": 5, "investimento": 18000.0},
        ]
        self.matriculas = []
        self._seq = {"leads": 4, "cursos": 3, "turmas": 3, "matriculas": 1}

    def _next(self, chave):
        v = self._seq[chave]
        self._seq[chave] += 1
        return v

    # ---- Leads ----
    def listar_leads(self, estagio=None):
        if estagio:
            return [l for l in self.leads if l["estagio"] == estagio]
        return list(self.leads)

    def obter_lead(self, lead_id):
        return next((l for l in self.leads if l["id"] == lead_id), None)

    def email_existe(self, email):
        return any(l["email"].lower() == email.lower() for l in self.leads)

    def criar_lead(self, dados):
        novo = {"id": self._next("leads"), **dados}
        self.leads.append(novo)
        return novo

    def atualizar_estagio(self, lead_id, estagio):
        lead = self.obter_lead(lead_id)
        if lead:
            lead["estagio"] = estagio
        return lead

    # ---- Cursos / Turmas ----
    def listar_cursos(self):
        return list(self.cursos)

    def criar_curso(self, dados):
        novo = {"id": self._next("cursos"), **dados}
        self.cursos.append(novo)
        return novo

    def listar_turmas(self, curso_id=None):
        if curso_id:
            return [t for t in self.turmas if t["curso_id"] == curso_id]
        return list(self.turmas)

    def obter_turma(self, turma_id):
        return next((t for t in self.turmas if t["id"] == turma_id), None)

    def criar_turma(self, dados):
        novo = {"id": self._next("turmas"), "vagas_ocupadas": 0, **dados}
        self.turmas.append(novo)
        return novo

    # ---- Matrícula (REQF05 + REQF06) ----
    def criar_matricula(self, lead_id, turma_id):
        turma = self.obter_turma(turma_id)
        nova = {
            "id": self._next("matriculas"),
            "lead_id": lead_id,
            "turma_id": turma_id,
            "data_matricula": date.today().isoformat(),
        }
        self.matriculas.append(nova)
        turma["vagas_ocupadas"] += 1
        self.atualizar_estagio(lead_id, "Matriculado")
        return nova


_memoria = _RepositorioMemoria()


# =========================================================================== #
# API pública do módulo — escolhe Postgres ou memória de forma transparente
# =========================================================================== #
def _usar_pg():
    return banco_disponivel()


def listar_leads(estagio: Optional[str] = None) -> List[dict]:
    if not _usar_pg():
        return _memoria.listar_leads(estagio)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if estagio:
                cur.execute("SELECT * FROM leads WHERE estagio = %s ORDER BY id", (estagio,))
            else:
                cur.execute("SELECT * FROM leads ORDER BY id")
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def obter_lead(lead_id: int) -> Optional[dict]:
    if not _usar_pg():
        return _memoria.obter_lead(lead_id)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM leads WHERE id = %s", (lead_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def email_existe(email: str) -> bool:
    if not _usar_pg():
        return _memoria.email_existe(email)
    conn = _conectar()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM leads WHERE LOWER(email) = LOWER(%s)", (email,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def criar_lead(dados: dict) -> dict:
    if not _usar_pg():
        return _memoria.criar_lead(dados)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO leads (nome, email, telefone, origem, estagio)
                   VALUES (%(nome)s, %(email)s, %(telefone)s, %(origem)s, %(estagio)s)
                   RETURNING *""",
                dados,
            )
            conn.commit()
            return dict(cur.fetchone())
    finally:
        conn.close()


def atualizar_estagio(lead_id: int, estagio: str) -> Optional[dict]:
    if not _usar_pg():
        return _memoria.atualizar_estagio(lead_id, estagio)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "UPDATE leads SET estagio = %s WHERE id = %s RETURNING *",
                (estagio, lead_id),
            )
            conn.commit()
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def listar_cursos() -> List[dict]:
    if not _usar_pg():
        return _memoria.listar_cursos()
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM cursos ORDER BY id")
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def criar_curso(dados: dict) -> dict:
    if not _usar_pg():
        return _memoria.criar_curso(dados)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO cursos (nome, modalidade, ativo)
                   VALUES (%(nome)s, %(modalidade)s, %(ativo)s) RETURNING *""",
                dados,
            )
            conn.commit()
            return dict(cur.fetchone())
    finally:
        conn.close()


def listar_turmas(curso_id: Optional[int] = None) -> List[dict]:
    if not _usar_pg():
        return _memoria.listar_turmas(curso_id)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if curso_id:
                cur.execute("SELECT * FROM turmas WHERE curso_id = %s ORDER BY id", (curso_id,))
            else:
                cur.execute("SELECT * FROM turmas ORDER BY id")
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def obter_turma(turma_id: int) -> Optional[dict]:
    if not _usar_pg():
        return _memoria.obter_turma(turma_id)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM turmas WHERE id = %s", (turma_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def criar_turma(dados: dict) -> dict:
    if not _usar_pg():
        return _memoria.criar_turma(dados)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO turmas (curso_id, data_inicio, vagas_totais, vagas_ocupadas, investimento)
                   VALUES (%(curso_id)s, %(data_inicio)s, %(vagas_totais)s, 0, %(investimento)s)
                   RETURNING *""",
                dados,
            )
            conn.commit()
            return dict(cur.fetchone())
    finally:
        conn.close()


def criar_matricula(lead_id: int, turma_id: int) -> dict:
    if not _usar_pg():
        return _memoria.criar_matricula(lead_id, turma_id)
    conn = _conectar()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO matriculas (lead_id, turma_id, data_matricula)
                   VALUES (%s, %s, CURRENT_DATE) RETURNING *""",
                (lead_id, turma_id),
            )
            matricula = dict(cur.fetchone())  # captura antes dos UPDATEs
            # REQF05: controle automático de vagas
            cur.execute(
                "UPDATE turmas SET vagas_ocupadas = vagas_ocupadas + 1 WHERE id = %s",
                (turma_id,),
            )
            cur.execute(
                "UPDATE leads SET estagio = 'Matriculado' WHERE id = %s",
                (lead_id,),
            )
            conn.commit()
            return matricula
    finally:
        conn.close()
