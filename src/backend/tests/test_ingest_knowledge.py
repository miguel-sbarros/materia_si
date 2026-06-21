"""Testes da ingestão da base de conhecimento (P4a): mapeamento de enums em Script,
fusão da justificativa de relação, split do playbook em ``##`` e idempotência.

Usam ``mock_embedder`` (sem OpenAI) + ``db_session`` (Postgres/pgvector real). Os fixtures
são pequenos dicts ``graph_json`` em memória e um ``.md`` temporário — não carregam o arquivo
real de 122 KB (o ``main()`` usa caminhos padrão, não exercitados aqui).
"""

from sqlalchemy import select

from app.models.knowledge import KnowledgeChunk
from app.models.persona import Persona
from scripts import ingest_knowledge as ik


def _graph(nodes, relationships=None):
    return [{"graph_json": {"nodes": nodes, "relationships": relationships or []}}]


def test_ingest_scripts_map_enums(db_session, mock_embedder):
    data = _graph(
        [
            {
                "id": 92,
                "labels": ["Script"],
                "properties": {
                    "script_id": "ID-S-01",
                    "texto": "Olá! Já tem um scanner, ótimo.",
                    "proposito": "Validar a decisão.",
                    "fase_spin": "Implicacao",
                    "persona": "O Iniciado Digital",
                },
            }
        ]
    )

    n = ik.ingest_graph(db_session, data)

    assert n == 1
    chunk = db_session.scalar(
        select(KnowledgeChunk).where(KnowledgeChunk.node_ref == "script:92")
    )
    assert chunk is not None
    assert chunk.spin_stage == "implication"
    assert chunk.persona == "001_iniciado_digital"
    assert chunk.label == "Script"
    assert chunk.title == "ID-S-01"
    # texto + proposito fundidos.
    assert "Validar a decisão." in chunk.content


def test_ingest_folds_relationship_justification(db_session, mock_embedder):
    data = _graph(
        nodes=[
            {
                "id": 0,
                "labels": ["Persona"],
                "properties": {"nome": "O Especialista Analógico", "resumo": "Mestre."},
            },
            {
                "id": 1,
                "labels": ["Dor"],
                "properties": {"nome": "Imprevisibilidade", "descricao": "Frustração."},
            },
        ],
        relationships=[
            {
                "id": 999,
                "startNode": 0,
                "endNode": 1,
                "type": "SENTE",
                "properties": {
                    "confidence_score": 10,
                    "justification": "O texto descreve a frustração recorrente.",
                },
            }
        ],
    )

    ik.ingest_graph(db_session, data)

    source = db_session.scalar(
        select(KnowledgeChunk).where(KnowledgeChunk.node_ref == "node:0")
    )
    assert source is not None
    assert "O texto descreve a frustração recorrente." in source.content
    # A justificativa NÃO vai para o nó de destino.
    target = db_session.scalar(
        select(KnowledgeChunk).where(KnowledgeChunk.node_ref == "node:1")
    )
    assert "frustração recorrente" not in target.content


def test_ingest_playbook_splits_on_headings(db_session, mock_embedder, tmp_path):
    """Qualquer heading de nível ≥2 abre seção: ``##`` E ``###`` viram chunks.

    Regressão do bug em que só ``##`` quebrava — ``cursos.md``/``about_mr.md`` (só ``###``/
    ``#####``) rendiam 0 chunks. O H1 (``#``) NÃO abre seção (conta como corpo do H2 anterior).
    """
    md = tmp_path / "guia.md"
    md.write_text(
        "# Título H1 ignorado antes do primeiro heading ≥2\n"
        "## Primeira Seção\n"
        "corpo da primeira seção\n"
        "### Subseção H3\n"
        "corpo da subseção\n"
        "##### Seção Profunda & Tática\n"
        "corpo profundo\n",
        encoding="utf-8",
    )

    n = ik.ingest_playbook(db_session, tmp_path)

    assert n == 3  # ## + ### + ##### → 3 seções
    refs = set(
        db_session.scalars(
            select(KnowledgeChunk.node_ref).where(
                KnowledgeChunk.source == "playbook"
            )
        ).all()
    )
    # node_ref carrega um índice posicional por arquivo (desambigua headings repetidos).
    assert refs == {
        "guia.md#00-primeira-secao",
        "guia.md#01-subsecao-h3",
        "guia.md#02-secao-profunda-tatica",
    }
    first = db_session.scalar(
        select(KnowledgeChunk).where(
            KnowledgeChunk.node_ref == "guia.md#00-primeira-secao"
        )
    )
    assert first.title == "Primeira Seção"
    assert first.content == "corpo da primeira seção"
    assert first.chunk_type == "playbook_section"
    # O ``###`` virou uma seção própria (não foi engolido pelo ``##``).
    h3 = db_session.scalar(
        select(KnowledgeChunk).where(KnowledgeChunk.node_ref == "guia.md#01-subsecao-h3")
    )
    assert h3.title == "Subseção H3"
    assert h3.content == "corpo da subseção"


def test_ingest_idempotent(db_session, mock_embedder, tmp_path):
    data = _graph(
        [
            {
                "id": 1,
                "labels": ["Dor"],
                "properties": {"nome": "Dor X", "descricao": "desc"},
            },
            {
                "id": 2,
                "labels": ["Desejo"],
                "properties": {"nome": "Desejo Y", "descricao": "desc"},
            },
        ]
    )
    md = tmp_path / "p.md"
    md.write_text("## Só Uma\ncorpo\n", encoding="utf-8")

    def total() -> int:
        return len(db_session.scalars(select(KnowledgeChunk.id)).all())

    ik.ingest_graph(db_session, data)
    ik.ingest_playbook(db_session, tmp_path)
    first = total()

    ik.ingest_graph(db_session, data)
    ik.ingest_playbook(db_session, tmp_path)
    second = total()

    assert first == 3  # 2 nós + 1 seção
    assert second == first  # delete-then-insert → contagem estável


def test_seed_personas_upserts(db_session):
    """Nós ``Persona`` → tabela ``personas`` (code = valor do enum); re-rodar mantém 1 linha."""
    data = _graph(
        [
            {
                "id": 0,
                "labels": ["Persona"],
                "properties": {
                    "nome": "O Especialista Analógico",
                    "resumo": "Um mestre da implantodontia analógica.",
                    "descricao": "Profissional com mais de 10 anos.",
                    "desejos_principais": "Preservar o legado.",
                    "medos": "Obsolescência.",
                    "volume_leads": "58%",
                    "taxa_conversao": "16%",
                    "palavras_chave": ["protocolo", "décadas de experiência"],
                },
            },
            # Nó não-Persona é ignorado pela semeadura.
            {"id": 1, "labels": ["Dor"], "properties": {"nome": "X", "descricao": "y"}},
        ]
    )

    def rows() -> list[Persona]:
        return db_session.scalars(select(Persona)).all()

    n = ik.seed_personas(db_session, data)
    assert n == 1
    personas = rows()
    assert len(personas) == 1
    p = personas[0]
    assert p.code == "002_especialista_analogico"
    assert p.name == "O Especialista Analógico"
    assert p.taxa_conversao == "16%"
    assert p.volume_leads == "58%"
    assert p.palavras_chave == ["protocolo", "décadas de experiência"]

    # Re-rodar é idempotente (delete-then-insert): ainda 1 linha.
    ik.seed_personas(db_session, data)
    assert len(rows()) == 1
