"""Configurações da aplicação (lidas de variáveis de ambiente / .env).

Nunca embuta segredos no código: a chave da Anthropic vem sempre do ambiente.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Banco de dados (SQLAlchemy URL, driver psycopg 3)
    database_url: str = "postgresql+psycopg://captus:captus@db:5432/captus"
    # Banco de testes; se ausente, o conftest deriva um "<db>_test" a partir de database_url.
    test_database_url: str | None = None

    # LLM
    anthropic_api_key: str | None = None
    model_copilot: str = "claude-opus-4-8"
    model_extraction: str = "claude-haiku-4-5"

    # Embeddings (constante de configuração — trocável via migração)
    embedding_dim: int = 384

    # CORS (origem do frontend Vite em dev)
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
