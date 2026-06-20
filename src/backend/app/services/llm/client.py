"""Wrapper fino do cliente Anthropic (SDK oficial).

Os services chamam ``get_client().messages.parse(...)`` com ``output_format`` Pydantic.
Os testes fazem monkeypatch desta função para devolver instâncias Pydantic reais,
sem chamadas de rede. Chamadas ao vivo ficam atrás de ``@pytest.mark.integration``.
"""

from functools import lru_cache

from anthropic import Anthropic

from app.core.config import get_settings


@lru_cache
def get_client() -> Anthropic:
    return Anthropic(api_key=get_settings().anthropic_api_key)
