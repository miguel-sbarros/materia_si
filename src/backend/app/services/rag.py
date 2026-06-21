"""RAG sobre ``knowledge_chunks`` — embeddings OpenAI + recuperação por cosseno (P4a).

Os embeddings usam a OpenAI (``text-embedding-3-small``, 1536-dim) — override consciente
do CLAUDE.md (a geração continua na Anthropic; só os embeddings usam OpenAI). ``embed_query``
e ``embed_texts`` são o **ponto de monkeypatch** dos testes (o ``mock_embedder`` substitui as
duas por vetores determinísticos), por isso ficam como funções de módulo, não métodos.

``retrieve`` ordena por distância de cosseno (pgvector ``<=>``) e aplica um **único boost**:
chunks ``Script`` que batem ``persona``+``spin_stage`` sobem para o topo. Corpus pequeno
(~130 linhas) → varredura exata, sem índice de vetor.
"""

from functools import lru_cache

import openai
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.knowledge import KnowledgeChunk


@lru_cache
def _get_openai_client() -> openai.OpenAI:
    """Cliente OpenAI memoizado (chave do ambiente via ``Settings``)."""
    return openai.OpenAI(api_key=get_settings().openai_api_key)


def embed_query(text: str) -> list[float]:
    """Embedding de um único texto (consulta). Seam de monkeypatch dos testes."""
    client = _get_openai_client()
    resp = client.embeddings.create(model=get_settings().embedding_model, input=text)
    return resp.data[0].embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeddings em lote (ingestão). Seam de monkeypatch dos testes."""
    client = _get_openai_client()
    resp = client.embeddings.create(model=get_settings().embedding_model, input=texts)
    return [item.embedding for item in resp.data]


def retrieve(
    db: Session,
    query: str,
    persona: str | None = None,
    spin_stage: str | None = None,
    k: int = 8,
) -> list[KnowledgeChunk]:
    """Top-``k`` chunks por similaridade de cosseno, com boost de Script por persona/SPIN.

    Sem ``persona``/``spin_stage`` → top-``k`` por cosseno puro. Com ambos, um chunk
    ``Script`` cujo ``persona`` **e** ``spin_stage`` batem é elevado ao topo (boost primeiro,
    depois cosseno crescente como desempate).
    """
    vec = embed_query(query)
    distance = KnowledgeChunk.embedding.cosine_distance(vec)

    order_by: list = []
    if persona is not None and spin_stage is not None:
        # Boost: 0 (sobe) para Script que casa persona+SPIN, 1 para os demais.
        boost = case(
            (
                (KnowledgeChunk.label == "Script")
                & (KnowledgeChunk.persona == persona)
                & (KnowledgeChunk.spin_stage == spin_stage),
                0,
            ),
            else_=1,
        )
        order_by.append(boost.asc())
    order_by.append(distance.asc())

    stmt = select(KnowledgeChunk).order_by(*order_by).limit(k)
    return list(db.scalars(stmt).all())
