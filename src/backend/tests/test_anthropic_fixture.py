"""Linchpin do TDD das fases de IA: a fixture mock-Anthropic devolve Pydantic real, sem rede."""

from pydantic import BaseModel

from app.services.llm import client as llm_client


class _PersonaSample(BaseModel):
    persona: str
    score: int


def test_mock_anthropic_returns_pydantic(mock_anthropic):
    expected = _PersonaSample(persona="Recém-Especializado", score=88)
    mock_anthropic.set_return(expected)

    result = llm_client.get_client().messages.parse(
        model="claude-haiku-4-5",
        messages=[{"role": "user", "content": "extraia o perfil"}],
        output_format=_PersonaSample,
    )

    assert isinstance(result, _PersonaSample)
    assert result.persona == "Recém-Especializado"
    assert result.score == 88
