"""run_agent (LLM mockado) — loop de tool-use que termina em saída estruturada/texto.

Os testes scriptam a sequência de turnos de ``messages.create`` via
``mock_anthropic.set_create_turns([...])`` usando os builders ``tool_use`` e ``final_text``
da fixture (conftest). ``run_agent`` chama ``client.messages.create``, então esses turnos
falsos dirigem o loop.
"""

import pytest

from app.schemas.copilot import SellerAdvice
from app.services.llm.client import run_agent

# Tool def mínima usada nos testes (o conteúdo não importa para o mock).
_GET_X_TOOL = {
    "name": "get_x",
    "description": "ferramenta de teste",
    "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
}

# JSON de um SellerAdvice válido (3 paths) para o turno final estruturado.
_ADVICE_JSON = (
    '{"reasoning":"r","paths":['
    '{"title":"t","rationale":"ra","message":"m"},'
    '{"title":"t2","rationale":"ra2","message":"m2"},'
    '{"title":"t3","rationale":"ra3","message":"m3"}]}'
)


def test_run_agent_tool_loop(mock_anthropic):
    """tool_use → turno estruturado: roda a ferramenta e devolve o SellerAdvice validado."""
    ran: list[dict] = []

    def get_x(**kwargs):
        ran.append(kwargs)
        return "RESULT"

    mock_anthropic.set_create_turns(
        [
            mock_anthropic.tool_use("get_x", {}),
            mock_anthropic.final_text(_ADVICE_JSON),
        ]
    )

    result = run_agent(
        model="claude-sonnet-4-6",
        system="sys",
        messages=[{"role": "user", "content": "oi"}],
        tools=[_GET_X_TOOL],
        dispatch={"get_x": get_x},
        output_format=SellerAdvice,
    )

    assert isinstance(result, SellerAdvice)
    assert result.reasoning == "r"
    assert len(result.paths) == 3
    assert ran == [{}]  # a ferramenta rodou exatamente uma vez


def test_run_agent_text_mode(mock_anthropic):
    """Sem output_format: o primeiro turno é texto → devolve a string crua."""
    mock_anthropic.set_create_turns([mock_anthropic.final_text("olá")])

    result = run_agent(
        model="claude-sonnet-4-6",
        system="sys",
        messages=[{"role": "user", "content": "oi"}],
        tools=[_GET_X_TOOL],
        dispatch={"get_x": lambda **k: "RESULT"},
        output_format=None,
    )

    assert result == "olá"


def test_run_agent_max_iterations(mock_anthropic):
    """Turnos tool_use infinitos → levanta ValueError ao exceder max_iterations."""
    # Scripta mais turnos de tool_use do que max_iterations: o loop nunca encerra.
    mock_anthropic.set_create_turns([mock_anthropic.tool_use("get_x", {}) for _ in range(5)])

    with pytest.raises(ValueError, match="max_iterations"):
        run_agent(
            model="claude-sonnet-4-6",
            system="sys",
            messages=[{"role": "user", "content": "oi"}],
            tools=[_GET_X_TOOL],
            dispatch={"get_x": lambda **k: "RESULT"},
            output_format=None,
            max_iterations=3,
        )
