"""Wrapper fino do cliente Anthropic (SDK oficial).

Os services chamam ``get_client().messages.parse(...)`` com ``output_format`` Pydantic.
Os testes fazem monkeypatch desta função para devolver instâncias Pydantic reais,
sem chamadas de rede. Chamadas ao vivo ficam atrás de ``@pytest.mark.integration``.
"""

from collections.abc import Callable
from functools import lru_cache

from anthropic import Anthropic
from pydantic import BaseModel

from app.core.config import get_settings


@lru_cache
def get_client() -> Anthropic:
    return Anthropic(api_key=get_settings().anthropic_api_key)


def parse_structured(
    *,
    model: str,
    system: str,
    messages: list[dict],
    output_format: type[BaseModel],
    max_tokens: int = 2000,
    **kwargs,
) -> BaseModel:
    """Chama ``messages.parse`` e normaliza o objeto estruturado da resposta.

    O SDK real devolve um ``ParsedMessage`` com o objeto em ``.parsed_output``; o stub
    dos testes devolve a instância Pydantic crua. Eventualmente o modelo não emite uma
    saída estruturada limpa (ex.: preâmbulo de texto) e ``parsed_output`` volta ``None`` —
    nesse caso tentamos UMA vez mais antes de falhar (o stub devolve a instância crua na 1ª
    tentativa, então não dispara o retry). Persistindo a falha, levantamos erro tipado.
    """
    client = get_client()
    for _ in range(2):
        resp = client.messages.parse(
            model=model,
            system=system,
            messages=messages,
            output_format=output_format,
            max_tokens=max_tokens,
            **kwargs,
        )
        out = getattr(resp, "parsed_output", None)
        if out is None:
            out = resp  # o mock devolve o modelo cru
        if isinstance(out, output_format):
            return out
    raise ValueError("Resposta do LLM não corresponde ao schema esperado")


def _output_config(output_format: type[BaseModel]) -> dict:
    """Monta o ``output_config`` de saída estruturada a partir de um modelo Pydantic.

    Shape documentado da Anthropic: ``output_config={"format": {"type": "json_schema",
    "schema": <json schema>}}`` em ``messages.create`` (pode ir junto com ``tools``).
    O SDK descarta restrições não suportadas; mantemos ``additionalProperties: false``.
    """

    schema = output_format.model_json_schema()
    schema.setdefault("additionalProperties", False)
    return {"format": {"type": "json_schema", "schema": schema}}


def run_agent(
    *,
    model: str,
    system: str,
    messages: list[dict],
    tools: list[dict],
    dispatch: dict[str, Callable[..., str]],
    output_format: type[BaseModel] | None = None,
    max_tokens: int = 2000,
    max_iterations: int = 6,
) -> BaseModel | str:
    """Loop agêntico de tool-use que termina em saída estruturada opcional.

    Roda o loop manual de tool-use do SDK Anthropic (``messages.create``). Enquanto o
    modelo pede ferramentas (``stop_reason == "tool_use"``), executa cada bloco via
    ``dispatch[nome](**input)`` e devolve os ``tool_result`` num único turno ``user``.
    Ao terminar (``end_turn``), retorna o primeiro bloco de texto — validado contra
    ``output_format`` se fornecido, ou como string crua caso contrário.

    Parâmetros:
    - ``tools``: lista de tool defs Anthropic (``{"name","description","input_schema"}``).
    - ``dispatch``: mapeia nome da ferramenta → handler que devolve string (o conteúdo
      do ``tool_result``). Handler ausente ou que levanta exceção → ``tool_result`` de erro.
    - ``output_format``: modelo Pydantic da saída terminal estruturada (opcional).

    Levanta ``ValueError`` se exceder ``max_iterations`` sem o modelo encerrar.
    """

    client = get_client()
    convo = list(messages)
    extra = _output_config(output_format) if output_format else {}

    for _ in range(max_iterations):
        resp = client.messages.create(
            model=model,
            system=system,
            messages=convo,
            tools=tools,
            max_tokens=max_tokens,
            **({"output_config": extra} if extra else {}),
        )

        if resp.stop_reason != "tool_use":
            # Turno final: pega o primeiro bloco de texto.
            text = next(
                (b.text for b in resp.content if getattr(b, "type", None) == "text"),
                "",
            )
            if output_format:
                return output_format.model_validate_json(text)
            return text

        # Registra o turno do assistente (com os blocos tool_use) antes de responder.
        convo.append({"role": "assistant", "content": resp.content})

        tool_results: list[dict] = []
        for block in resp.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            handler = dispatch.get(block.name)
            result_block: dict = {"type": "tool_result", "tool_use_id": block.id}
            if handler is None:
                result_block["content"] = f"Ferramenta desconhecida: {block.name}"
                result_block["is_error"] = True
            else:
                # noqa BLE001: o loop precisa SEMPRE devolver um tool_result (mesmo em erro).
                try:
                    result_block["content"] = handler(**(block.input or {}))
                except Exception as exc:  # noqa: BLE001
                    result_block["content"] = f"Erro ao executar {block.name}: {exc}"
                    result_block["is_error"] = True
            tool_results.append(result_block)

        convo.append({"role": "user", "content": tool_results})

    raise ValueError("run_agent excedeu max_iterations sem encerrar o loop de ferramentas")
