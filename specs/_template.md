# Spec — <feature/step name>

> Spec-Driven Development: escreva esta spec **antes** de construir. Os critérios de
> aceitação viram asserções de pytest (TDD). Uma feature por arquivo.

## Requisito / contexto
- REQ code(s) do rubric (`PRO3151 … Grupo 10.md`) que esta etapa atende.
- Por que esta etapa existe; onde encaixa nas fases P0–P5.

## Escopo
- O que entra.
- O que **não** entra (diferido), com link para a fase futura.

## Schema (Pydantic / DB)
- Tabelas/colunas ou modelos Pydantic introduzidos ou alterados.
- Enums, constraints, índices.

## Critérios de aceitação → casos de teste
| # | Critério | Teste (arquivo::nome) |
|---|----------|------------------------|
| 1 | … | `tests/test_x.py::test_…` |

## Verificação
- Comando(s) que provam a etapa de ponta a ponta.
