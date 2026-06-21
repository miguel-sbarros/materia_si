"""Conteúdo dos cursos — parser do ``playbook/cursos.md``.

Fonte única compartilhada pela ferramenta ``get_course_ementa`` do copiloto (P4) e pela
página de Cursos do frontend. Parser puro (sem DB, sem LLM), idempotente.

Estrutura do ``cursos.md``: todos os cabeçalhos são ``###``. Um cabeçalho de **curso** é
numerado (``### **1. IMERSÃO ...**``); os demais (``### **Objetivo Central**``,
``### **Temas Abordados**``, ``### **Cronograma Geral (...)**``) são **seções** do último
curso. A ementa (``syllabus``) é derivada dos tópicos da seção "Temas Abordados".
"""

import re
from pathlib import Path


def _locate(rel: str) -> Path:
    """Localiza um recurso do repo (ex.: ``playbook/cursos.md``) de forma robusta entre
    host (``.../materia_si/src/backend/...``) e container (``/app`` + mount ``/app/playbook``):
    sobe pelos diretórios de ``__file__`` e do ``cwd`` até achar ``rel``. Lazy (sem crash no
    import quando a profundidade difere). Fallback = o próprio ``rel`` relativo ao cwd."""
    for base in (Path(__file__).resolve(), Path.cwd().resolve()):
        for parent in (base, *base.parents):
            candidate = parent / rel
            if candidate.exists():
                return candidate
    return Path(rel)

# Cabeçalho de curso: "### **1. IMERSÃO EM IMPLANTODONTIA DIGITAL**".
_COURSE_HEADER = re.compile(r"^###\s+\*\*\s*(\d+)\.\s*(.+?)\s*\*\*\s*$")
# Cabeçalho de seção (qualquer "###" não-numerado): "### **Temas Abordados**".
_SECTION_HEADER = re.compile(r"^###\s+\*\*\s*(.+?)\s*\*\*\s*$")
# Bullet de topo: "- **Título:** corpo" (ou só "- corpo").
_TOP_BULLET = re.compile(r"^-\s+(.*)$")
# Bullet aninhado (indentado): "    - corpo".
_NESTED_BULLET = re.compile(r"^\s+-\s+(.*)$")
# "Carga" embutida no título da seção: "Cronograma Geral (3 dias - 24 horas)".
_CARGA = re.compile(r"\((.*?)\)")

# Palavras genéricas demais para sinalizar um match de nome de curso (já normalizadas).
_STOPWORDS = {
    "curso", "de", "em", "do", "da", "e", "clinico", "digital",
    "implantodontia", "o", "a",
}


def _clean(text: str) -> str:
    """Remove negrito markdown e normaliza espaços (inclui U+00A0)."""
    text = text.replace("\u00a0", " ").replace("\u200e", "")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _split_bullet(line: str) -> tuple[str | None, str]:
    """Separa um bullet "**Título:** corpo" em (titulo, corpo). Título None se ausente."""
    content = _clean(line)
    m = re.match(r"^(.+?):\s*(.*)$", content)
    # Só trata como título se a parte antes do ":" for curta (rótulo, não frase).
    if m and len(m.group(1)) <= 60:
        return m.group(1).strip(), m.group(2).strip()
    return None, content


def _syllabus_from_temas(bullets: list[dict]) -> list[dict]:
    """Converte os tópicos de "Temas Abordados" em linhas de ementa.

    Cada bullet de topo vira uma linha ``{tema, conteudo}``; bullets aninhados são
    concatenados no ``conteudo`` do tópico pai.
    """
    rows: list[dict] = []
    for b in bullets:
        tema, corpo = _split_bullet(b["text"])
        partes = [corpo] if corpo else []
        partes += [_clean(c) for c in b["children"] if _clean(c)]
        conteudo = " ".join(p for p in partes if p)
        rows.append({"tema": tema or conteudo[:60], "conteudo": conteudo})
    return rows


def _carga_from_sections(chosen: dict, sections: list[dict]) -> str | None:
    """Extrai a carga (entre parênteses) do cabeçalho da ementa ou de uma seção "Cronograma".

    "Temas Abordados" não traz carga; o "Cronograma Geral (10 meses - 160 horas)" traz —
    propagamos esse valor para as linhas da ementa quando disponível.
    """
    for sec in (chosen, *(s for s in sections if "cronograma" in s["heading"].lower())):
        m = _CARGA.search(sec["heading"])
        if m:
            return _clean(m.group(1))
    return None


def _parse_bullets(lines: list[str]) -> list[dict]:
    """Agrupa linhas de bullets em ``[{text, children:[...]}]`` (1 nível de aninhamento).

    Um bullet começando na coluna 0 (``- ...``) abre um novo tópico; um bullet indentado
    (``    - ...``) vira filho do último tópico.
    """
    items: list[dict] = []
    for raw in lines:
        if raw and not raw[0].isspace():
            top = _TOP_BULLET.match(raw)
            if top:
                items.append({"text": top.group(1), "children": []})
            continue
        nested = _NESTED_BULLET.match(raw)
        if nested and items:
            items[-1]["children"].append(nested.group(1))
    return items


def parse_cursos_md(path: str | Path | None = None) -> list[dict]:
    """Faz o parse do ``cursos.md`` → uma entrada por curso.

    Retorna ``[{name, summary, sections:[{heading,body}], syllabus:[{tema,conteudo,carga?}]}]``.
    A ``syllabus`` vem dos tópicos de "Temas Abordados"; se ausente, dos bullets da primeira
    seção temática do curso. Cada linha carrega ``carga`` quando a seção a expõe entre parênteses.
    """
    md_path = Path(path) if path is not None else _locate("playbook/cursos.md")
    raw = md_path.read_text(encoding="utf-8")
    lines = raw.splitlines()

    courses: list[dict] = []
    current: dict | None = None  # curso em construção
    section: dict | None = None  # {heading, raw_lines}

    def _flush_section() -> None:
        if current is None or section is None:
            return
        heading = section["heading"]
        body_lines = [
            ln for ln in section["raw_lines"] if ln.strip() and not ln.strip().startswith("-")
        ]
        bullets = _parse_bullets(section["raw_lines"])
        body = _clean(" ".join(body_lines))
        current["sections"].append({"heading": heading, "body": body})
        section["bullets"] = bullets
        section["body"] = body
        current["_raw_sections"].append(section)

    for line in lines:
        course_m = _COURSE_HEADER.match(line)
        if course_m:
            _flush_section()
            section = None
            current = {
                "name": _clean(course_m.group(2)),
                "summary": "",
                "sections": [],
                "syllabus": [],
                "_raw_sections": [],
            }
            courses.append(current)
            continue

        section_m = _SECTION_HEADER.match(line)
        if section_m and current is not None:
            _flush_section()
            section = {"heading": _clean(section_m.group(1)), "raw_lines": []}
            continue

        if section is not None:
            section["raw_lines"].append(line)

    _flush_section()

    # Pós-processa cada curso: summary + syllabus a partir das seções coletadas.
    for course in courses:
        raw_sections = course.pop("_raw_sections", [])
        for sec in raw_sections:
            heading_l = sec["heading"].lower()
            if "objetivo" in heading_l and sec["body"]:
                course["summary"] = sec["body"]

        # Ementa: prioriza "Temas Abordados"; senão a 1ª seção com bullets.
        temas = next(
            (s for s in raw_sections if "tema" in s["heading"].lower() and s["bullets"]),
            None,
        )
        chosen = temas or next((s for s in raw_sections if s["bullets"]), None)
        if chosen is not None:
            # Carga: do próprio cabeçalho da ementa, senão de uma seção "Cronograma".
            carga = _carga_from_sections(chosen, raw_sections)
            rows = _syllabus_from_temas(chosen["bullets"])
            if carga:
                for row in rows:
                    row["carga"] = carga
            course["syllabus"] = rows

        if not course["summary"]:
            # Fallback: primeira seção com corpo textual.
            course["summary"] = next(
                (s["body"] for s in raw_sections if s["body"]), ""
            )

    return courses


def course_ementa(name: str) -> dict | None:
    """Retorna a entrada de curso cujo nome melhor casa com ``name`` (case-insensitive).

    Casamento por palavras-chave (substring): "Master" / "Aperfeiçoamento" → curso Master;
    "Imersão" → Imersão. ``None`` se nenhum curso for encontrado.
    """
    if not name or not name.strip():
        return None
    courses = parse_cursos_md()
    query = _normalize(name)

    # Apelidos comuns das turmas MR (rótulo do catálogo ↔ nome no cursos.md).
    aliases = {
        "master": ["master", "aperfeicoamento", "aperfeicoamento clinico"],
        "imersao": ["imersao"],
    }

    best: dict | None = None
    best_score = 0
    q_tokens = set(query.split()) - _STOPWORDS
    for course in courses:
        cname = _normalize(course["name"])
        score = 0
        # Match direto por substring (em qualquer direção), descontando stopwords genéricas.
        if query not in _STOPWORDS and (query in cname or cname in query):
            score = max(score, len(query))
        # Match por tokens significativos compartilhados (ignora "curso", "de", "em"…).
        c_tokens = set(cname.split()) - _STOPWORDS
        score = max(score, len(q_tokens & c_tokens))
        # Match por apelido (Master ↔ Aperfeiçoamento, etc.).
        for canonical, names in aliases.items():
            in_course = canonical in cname or any(a in cname for a in names)
            in_query = canonical in query or any(a in query for a in names)
            if in_course and in_query:
                score = max(score, 5)
        if score > best_score:
            best_score, best = score, course

    return best if best_score > 0 else None


def _normalize(text: str) -> str:
    """Minúsculas sem acentos, para casamento robusto de nomes de curso."""
    import unicodedata

    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()
