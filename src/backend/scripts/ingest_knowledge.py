"""Ingestão idempotente da base de conhecimento → ``knowledge_chunks`` (P4a, REQF04).

Duas fontes alimentam o RAG do copiloto:

- ``legacy_neo4j_kb.json`` (``source="kb_graph"``): grafo legado da MR (112 nós + 162
  relacionamentos). Um chunk por nó; a ``justification`` de cada relacionamento é **fundida**
  no conteúdo do nó de origem (``startNode``). Nós ``Script`` carregam ``persona``+``spin_stage``
  (mapeados de ``persona``/``fase_spin`` PT → valores de enum) para o boost de recuperação.
- ``playbook/*.md`` (``source="playbook"``): cada arquivo é quebrado em seções a cada cabeçalho
  de nível 2 ou mais profundo (``##`` … ``######``); um chunk por seção.

Também semeia a tabela ``personas`` a partir dos nós ``Persona`` do grafo (``seed_personas``).

Idempotência = **delete-then-insert por fonte**: re-rodar zera as linhas daquela fonte antes
de reinserir, então a contagem é estável (também respeita ``UNIQUE(source, node_ref)``).
Embeddings via ``rag.embed_texts`` (OpenAI em lote). Precisa de ``OPENAI_API_KEY``.

Uso:
    python scripts/ingest_knowledge.py
"""

import json
import re
import unicodedata
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.knowledge import KnowledgeChunk
from app.models.persona import Persona
from app.schemas.analysis import label_to_persona
from app.services import rag

SOURCE_GRAPH = "kb_graph"
SOURCE_PLAYBOOK = "playbook"


def _locate(rel: str) -> Path:
    """Localiza um recurso do repo (``legacy_neo4j_kb.json`` / ``playbook``) de forma robusta
    entre host e container (mounts ``/app/legacy_neo4j_kb.json`` e ``/app/playbook``): sobe
    pelos diretórios de ``__file__`` e do ``cwd`` até achar ``rel``. Lazy — sem crash no import."""
    for base in (Path(__file__).resolve(), Path.cwd().resolve()):
        for parent in (base, *base.parents):
            candidate = parent / rel
            if candidate.exists():
                return candidate
    return Path(rel)

# fase_spin (PT, com/sem acento) → valor de SPINStage.
_SPIN_MAP = {
    "situacao": "situation",
    "problema": "problem",
    "implicacao": "implication",
    "necessidade": "need_payoff",
}

# Propriedades a concatenar por label (referência do projeto Octo `nodes_to_embed`).
_LABEL_PROPS: dict[str, list[str]] = {
    "Persona": ["nome", "resumo", "descricao"],
    "Dor": ["nome", "descricao"],
    "Desejo": ["nome", "descricao"],
    "Argumento_Valor": ["nome", "descricao_valor"],
    "Filosofia": ["conceito", "descricao"],
    "Metodologia": ["nome", "descricao"],
    "Hardware": ["nome", "descricao"],
    "Software": ["nome", "descricao"],
}


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    )


def _norm(text: str) -> str:
    """Normaliza para casamento: sem acentos, minúsculo, sem espaços nas pontas."""
    return _strip_accents(text or "").strip().lower()


def slug(text: str) -> str:
    """Slug simples: minúsculo, não-alfanumérico → '-', pontas limpas."""
    s = re.sub(r"[^a-z0-9]+", "-", _strip_accents(text or "").lower())
    return s.strip("-")


def _persona_code(label: str | None) -> str | None:
    """Rótulo/nome de persona (ex.: "O Iniciado Digital") → valor de ``PersonaType``.

    Delega ao matcher robusto compartilhado ``app.schemas.analysis.label_to_persona``
    (tolera artigo inicial, acentos e variações). Sem casamento → ``None``.
    """
    persona = label_to_persona(label)
    return persona.value if persona is not None else None


def map_spin_stage(fase_spin: str | None) -> str | None:
    """``fase_spin`` PT (ex.: "Implicação") → valor de ``SPINStage`` (ex.: "implication")."""
    if not fase_spin:
        return None
    return _SPIN_MAP.get(_norm(fase_spin))


def _node_content(label: str, props: dict) -> str:
    """Conteúdo base de um nó não-Script: concatena as props relevantes do label.

    Labels mapeados usam ``_LABEL_PROPS``; os demais (Curso/Modulo/Citacao/Resultado…) usam
    um fallback genérico (nome/id + descricao/resumo + texto + demais strings).
    """
    if label in _LABEL_PROPS:
        keys = _LABEL_PROPS[label]
    else:
        # Fallback genérico: identidade + descrições + qualquer string restante.
        keys = ["nome", "id", "descricao", "resumo", "texto"]
        for k, v in props.items():
            if k not in keys and isinstance(v, str):
                keys.append(k)
    parts = [str(props[k]).strip() for k in keys if props.get(k)]
    # Remove duplicatas mantendo a ordem (nome e id costumam coincidir).
    seen: set[str] = set()
    unique = [p for p in parts if not (p in seen or seen.add(p))]
    return " — ".join(unique)


def _build_graph_chunks(data: list) -> list[KnowledgeChunk]:
    """Constrói (sem embeddings) os chunks do grafo, fundindo justificativas de relação."""
    graph = data[0]["graph_json"]
    nodes = graph["nodes"]
    relationships = graph.get("relationships", [])

    # Conteúdo extra por nó de origem (justificativas das relações de saída).
    extra: dict[int, list[str]] = {}
    for rel in relationships:
        start = rel.get("startNode")
        justification = (rel.get("properties") or {}).get("justification")
        if start is None or not justification:
            continue
        rel_type = rel.get("type", "REL")
        extra.setdefault(start, []).append(f"{rel_type}: {justification}")

    chunks: list[KnowledgeChunk] = []
    for node in nodes:
        node_id = node["id"]
        label = node["labels"][0]
        props = node["properties"]

        if label == "Script":
            base = props.get("texto", "")
            proposito = props.get("proposito", "")
            content = f"{base} — {proposito}" if proposito else base
            chunk = KnowledgeChunk(
                source=SOURCE_GRAPH,
                chunk_type="node",
                node_ref=f"script:{node_id}",
                label="Script",
                title=props.get("script_id"),
                content=content,
                persona=_persona_code(props.get("persona")),
                spin_stage=map_spin_stage(props.get("fase_spin")),
                meta=props,
            )
        else:
            chunk = KnowledgeChunk(
                source=SOURCE_GRAPH,
                chunk_type="node",
                node_ref=f"node:{node_id}",
                label=label,
                title=props.get("nome") or props.get("id"),
                content=_node_content(label, props),
                meta=props,
            )

        # Funde justificativas das relações de saída deste nó.
        if node_id in extra:
            chunk.content = "\n".join([chunk.content, *extra[node_id]])
        chunks.append(chunk)

    return chunks


# Cabeçalho de nível 2+ (``##`` … ``######``) — fronteira de seção. Os playbooks reais
# usam ``###``/``#####`` (não só ``##``), então qualquer heading de nível ≥2 abre uma seção;
# cada seção = sua linha de cabeçalho + o corpo até o próximo heading de nível ≥2.
_HEADING_RE = re.compile(r"^#{2,6}\s+(.*)$")


def _split_md_sections(text: str) -> list[tuple[str, str]]:
    """Quebra um markdown em (cabeçalho, corpo) a cada heading de nível ≥2 (``##``…``######``).

    Conteúdo antes do primeiro heading de nível ≥2 é ignorado. Um ``#`` (H1) não abre seção
    (conta como corpo). Garante ≥1 chunk para todo arquivo que tenha ao menos um heading ≥2.
    """
    sections: list[tuple[str, str]] = []
    header: str | None = None
    body: list[str] = []
    for line in text.splitlines():
        m = _HEADING_RE.match(line)
        if m:
            if header is not None:
                sections.append((header, "\n".join(body).strip()))
            header = m.group(1).strip()
            body = []
        elif header is not None:
            body.append(line)
    if header is not None:
        sections.append((header, "\n".join(body).strip()))
    return sections


def _build_playbook_chunks(directory: Path) -> list[KnowledgeChunk]:
    """Constrói (sem embeddings) um chunk por seção ``##`` de cada ``*.md`` do diretório."""
    chunks: list[KnowledgeChunk] = []
    for md_path in sorted(directory.glob("*.md")):
        text = md_path.read_text(encoding="utf-8")
        # Índice posicional no node_ref: headings repetidos (ex.: "Objetivo Central" em
        # cada curso de cursos.md) colidiriam no UNIQUE(source, node_ref) sem ele.
        for i, (header, body) in enumerate(_split_md_sections(text)):
            chunks.append(
                KnowledgeChunk(
                    source=SOURCE_PLAYBOOK,
                    chunk_type="playbook_section",
                    node_ref=f"{md_path.name}#{i:02d}-{slug(header)}",
                    label=None,
                    title=header,
                    content=body,
                    meta={"file": md_path.name},
                )
            )
    return chunks


def _embed_and_persist(db: Session, source: str, chunks: list[KnowledgeChunk]) -> int:
    """Delete-then-insert de uma fonte: zera a fonte, embeda os conteúdos e insere."""
    db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.source == source))
    # Descarta chunks de conteúdo vazio/branco — a API de embeddings rejeita string vazia.
    chunks = [c for c in chunks if c.content and c.content.strip()]
    if not chunks:
        db.commit()
        return 0
    vectors = rag.embed_texts([c.content for c in chunks])
    for chunk, vec in zip(chunks, vectors, strict=True):
        chunk.embedding = vec
    db.add_all(chunks)
    db.commit()
    return len(chunks)


def ingest_graph(db: Session, data: list) -> int:
    """Ingere os chunks do grafo (idempotente). Retorna a contagem inserida."""
    chunks = _build_graph_chunks(data)
    return _embed_and_persist(db, SOURCE_GRAPH, chunks)


def ingest_playbook(db: Session, directory: Path | str) -> int:
    """Ingere os chunks do playbook (idempotente). Retorna a contagem inserida."""
    chunks = _build_playbook_chunks(Path(directory))
    return _embed_and_persist(db, SOURCE_PLAYBOOK, chunks)


def seed_personas(db: Session, data: list) -> int:
    """Semeia a tabela ``personas`` a partir dos nós ``Persona`` do grafo (idempotente).

    Delete-then-insert: zera a tabela e reinsere uma linha por nó ``Persona`` cujo ``nome``
    casa com uma ``PersonaType`` (``code`` = valor do enum). Re-rodar mantém a contagem.
    Retorna o nº de personas semeadas.
    """
    nodes = data[0]["graph_json"]["nodes"]
    db.execute(delete(Persona))
    seeded = 0
    for node in nodes:
        if node["labels"][0] != "Persona":
            continue
        props = node["properties"]
        code = _persona_code(props.get("nome"))
        if code is None:
            continue
        db.add(
            Persona(
                code=code,
                name=props["nome"],
                summary=props.get("resumo"),
                description=props.get("descricao"),
                desejos=props.get("desejos_principais"),
                medos=props.get("medos"),
                volume_leads=props.get("volume_leads"),
                taxa_conversao=props.get("taxa_conversao"),
                palavras_chave=props.get("palavras_chave"),
            )
        )
        seeded += 1
    db.commit()
    return seeded


def main() -> None:
    data = json.loads(_locate("legacy_neo4j_kb.json").read_text(encoding="utf-8"))
    with SessionLocal() as db:
        n_graph = ingest_graph(db, data)
        n_playbook = ingest_playbook(db, _locate("playbook"))
        n_personas = seed_personas(db, data)
    print(
        f"Ingeridos {n_graph} chunks do grafo + {n_playbook} do playbook; "
        f"{n_personas} personas semeadas."
    )


if __name__ == "__main__":
    main()
