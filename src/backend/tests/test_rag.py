"""Testes do RAG (P4a): ordenação por cosseno, boost de Script, filtro None, UNIQUE.

Usam ``mock_embedder`` (vetores determinísticos bag-of-words 1536-d; palavras compartilhadas
→ maior similaridade) e o DB Postgres/pgvector real via ``db_session``. ``rag.embed_query``
está monkeypatchado, então ``retrieve`` usa o mesmo esquema dos embeddings dos chunks.
"""

import math

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.knowledge import KnowledgeChunk
from app.services import rag


def _chunk(embed, *, node_ref, content, **kw) -> KnowledgeChunk:
    return KnowledgeChunk(
        source="kb_graph",
        chunk_type="node",
        node_ref=node_ref,
        content=content,
        embedding=embed(content),
        **kw,
    )


def test_retrieve_orders_by_cosine(db_session, mock_embedder):
    # Três chunks; um compartilha palavras com a consulta → deve ranquear primeiro.
    db_session.add_all(
        [
            _chunk(
                mock_embedder,
                node_ref="node:1",
                content="cirurgia guiada planejamento digital implante",
            ),
            _chunk(
                mock_embedder,
                node_ref="node:2",
                content="financiamento preço parcelamento matrícula",
            ),
            _chunk(
                mock_embedder,
                node_ref="node:3",
                content="agenda turma data início aula",
            ),
        ]
    )
    db_session.flush()

    results = rag.retrieve(db_session, "cirurgia guiada planejamento", k=3)

    assert results
    assert results[0].node_ref == "node:1"


def test_retrieve_script_boost_persona_stage(db_session, mock_embedder):
    # Um nó genérico casa muito bem por cosseno; um Script casa persona+SPIN mas pior por
    # cosseno → com o boost, o Script sobe ao topo mesmo assim.
    db_session.add(
        _chunk(
            mock_embedder,
            node_ref="node:10",
            content="cirurgia guiada planejamento digital implante reverso",
            label="Dor",
        )
    )
    db_session.add(
        _chunk(
            mock_embedder,
            node_ref="script:11",
            content="texto de script totalmente diferente sem palavras em comum",
            label="Script",
            persona="001_iniciado_digital",
            spin_stage="implication",
        )
    )
    db_session.flush()

    results = rag.retrieve(
        db_session,
        "cirurgia guiada planejamento",
        persona="001_iniciado_digital",
        spin_stage="implication",
        k=2,
    )

    assert results[0].node_ref == "script:11"


def test_retrieve_filters_none_passthrough(db_session, mock_embedder):
    # Sem persona/SPIN → top-k por cosseno puro (o Script NÃO recebe boost).
    db_session.add(
        _chunk(
            mock_embedder,
            node_ref="node:20",
            content="cirurgia guiada planejamento digital implante reverso",
            label="Dor",
        )
    )
    db_session.add(
        _chunk(
            mock_embedder,
            node_ref="script:21",
            content="texto de script totalmente diferente sem palavras em comum",
            label="Script",
            persona="001_iniciado_digital",
            spin_stage="implication",
        )
    )
    db_session.flush()

    results = rag.retrieve(db_session, "cirurgia guiada planejamento", k=2)

    assert results[0].node_ref == "node:20"


def test_knowledge_chunk_unique_source_noderef(db_session, mock_embedder):
    db_session.add(_chunk(mock_embedder, node_ref="node:1", content="a"))
    db_session.flush()

    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.add(_chunk(mock_embedder, node_ref="node:1", content="b"))
        db_session.flush()


@pytest.mark.integration
def test_live_embedding():
    """Embedding real OpenAI: 1536-dim e cosseno(relacionados) > cosseno(não relacionado).

    Precisa de ``OPENAI_API_KEY``. Marcado integration → pulado por padrão.
    """

    def cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb)

    base = rag.embed_query("cirurgia guiada de implantes dentários")
    related = rag.embed_query("planejamento digital para colocação de implantes")
    unrelated = rag.embed_query("receita de bolo de cenoura com cobertura")

    assert len(base) == 1536
    assert len(related) == 1536
    assert cosine(base, related) > cosine(base, unrelated)
