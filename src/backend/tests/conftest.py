"""Harness de testes: DB Postgres/pgvector real + fixture mock-Anthropic.

- ``engine`` (session): garante o banco de testes, habilita ``vector``, cria as tabelas.
- ``db_session`` (function): conexão + transação com savepoints, rollback ao final (isolamento).
- ``client``: ``TestClient`` do FastAPI (``/health`` bate no DB real configurado).
- ``mock_anthropic``: faz monkeypatch de ``get_client`` para devolver Pydantic real, sem rede.
"""

from types import SimpleNamespace

import psycopg
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base


def _test_db_url() -> str:
    settings = get_settings()
    if settings.test_database_url:
        return settings.test_database_url
    url = make_url(settings.database_url)
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


def _ensure_database(url_str: str) -> None:
    """Cria o banco de testes se ainda não existir (conecta ao 'postgres')."""
    url = make_url(url_str)
    kwargs = {
        "host": url.host,
        "port": url.port or 5432,
        "user": url.username,
        "dbname": "postgres",
        "autocommit": True,
    }
    if url.password:
        kwargs["password"] = url.password
    with psycopg.connect(**kwargs) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (url.database,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{url.database}"')


@pytest.fixture(scope="session")
def engine():
    url = _test_db_url()
    _ensure_database(url)
    eng = create_engine(url, future=True)
    with eng.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    import app.models  # noqa: F401  (popula Base.metadata)

    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api_client(db_session):
    """TestClient com ``get_db`` apontando para a sessão isolada (savepoint-rollback).

    Os services chamam ``db.commit()``; o rollback da transação externa do
    ``db_session`` garante o isolamento entre testes.
    """
    from app.db.session import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _text_block(text: str):
    return SimpleNamespace(type="text", text=text)


def _tool_use_block(name: str, inp: dict, tool_use_id: str):
    return SimpleNamespace(type="tool_use", name=name, input=inp, id=tool_use_id)


def _fake_message(content: list, stop_reason: str):
    return SimpleNamespace(content=content, stop_reason=stop_reason)


@pytest.fixture
def mock_anthropic(monkeypatch):
    """Stub de cliente Anthropic para ``messages.parse`` (análise P3) e ``messages.create``
    (loop de agente do copiloto P4).

    parse:
    - ``set_return(obj)``: devolve sempre o mesmo objeto Pydantic.
    - ``set_returns([a, b, ...])``: um por chamada (análise = 2 chamadas).

    create (loop de tool-use):
    - ``set_create_turns([msg, ...])``: um *Message* falso por turno, em ordem.
      Construa-os com ``mock_anthropic.tool_use(name, input)`` (stop_reason='tool_use')
      e ``mock_anthropic.final_text(texto_ou_json)`` (stop_reason='end_turn').
    """

    class _Messages:
        def __init__(self) -> None:
            self.return_value = None
            self.queue: list | None = None
            self.create_queue: list | None = None

        def parse(self, *args, **kwargs):
            if self.queue is not None:
                assert self.queue, (
                    "mock_anthropic: mais chamadas parse do que retornos configurados"
                )
                return self.queue.pop(0)
            return self.return_value

        def create(self, *args, **kwargs):
            assert self.create_queue, (
                "mock_anthropic: mais chamadas create do que turnos configurados"
            )
            return self.create_queue.pop(0)

    class _Stub:
        def __init__(self) -> None:
            self.messages = _Messages()

        def set_return(self, obj):
            self.messages.return_value = obj
            self.messages.queue = None
            return obj

        def set_returns(self, objs):
            self.messages.queue = list(objs)
            return objs

        def set_create_turns(self, turns):
            self.messages.create_queue = list(turns)
            return turns

        # Builders de Message falso para o loop do agente.
        def tool_use(self, name, inp=None, tool_use_id="tu_1"):
            return _fake_message([_tool_use_block(name, inp or {}, tool_use_id)], "tool_use")

        def final_text(self, text):
            return _fake_message([_text_block(text)], "end_turn")

    stub = _Stub()
    monkeypatch.setattr("app.services.llm.client.get_client", lambda: stub)
    return stub


def _deterministic_embed(text: str) -> list[float]:
    """Embedding determinístico p/ testes: bag-of-words → 1536-d (hash da palavra → índice).

    Textos que compartilham palavras ficam próximos por cosseno — torna a ordenação do
    ``retrieve`` assertável com fixtures em linguagem natural, sem carregar modelo real.
    """
    dim = get_settings().embedding_dim
    vec = [0.0] * dim
    for word in (text or "").lower().split():
        vec[hash(word) % dim] += 1.0
    return vec


@pytest.fixture
def mock_embedder(monkeypatch):
    """Faz monkeypatch de ``app.services.rag.embed_query``/``embed_texts`` → vetores
    determinísticos (sem chamada OpenAI). Devolve a função de embed p/ os testes
    construírem os ``KnowledgeChunk`` com o mesmo esquema."""

    monkeypatch.setattr("app.services.rag.embed_query", _deterministic_embed)
    monkeypatch.setattr(
        "app.services.rag.embed_texts",
        lambda texts: [_deterministic_embed(t) for t in texts],
    )
    return _deterministic_embed
