"""Harness de testes: DB Postgres/pgvector real + fixture mock-Anthropic.

- ``engine`` (session): garante o banco de testes, habilita ``vector``, cria as tabelas.
- ``db_session`` (function): conexão + transação com savepoints, rollback ao final (isolamento).
- ``client``: ``TestClient`` do FastAPI (``/health`` bate no DB real configurado).
- ``mock_anthropic``: faz monkeypatch de ``get_client`` para devolver Pydantic real, sem rede.
"""

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


@pytest.fixture
def mock_anthropic(monkeypatch):
    """Stub de cliente Anthropic; ``set_return(obj)`` define o retorno de ``messages.parse``."""

    class _Messages:
        return_value = None

        def parse(self, *args, **kwargs):
            return self.return_value

    class _Stub:
        def __init__(self) -> None:
            self.messages = _Messages()

        def set_return(self, obj):
            self.messages.return_value = obj
            return obj

    stub = _Stub()
    monkeypatch.setattr("app.services.llm.client.get_client", lambda: stub)
    return stub
