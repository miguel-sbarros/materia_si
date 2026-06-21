"""Parser de ``playbook/cursos.md`` (sem DB, sem LLM) — fonte da ementa dos cursos.

Nota: o ``cursos.md` real documenta **2 cursos em detalhe** (Imersão e Master/Aperfeiçoamento).
O portfólio MR tem uma 3ª trilha (Especialização), mas ela não está descrita em ``cursos.md``;
os testes afirmam o que realmente existe na fonte (≥2 cursos com ementa não-vazia).
"""

from app.services.course_content import course_ementa, parse_cursos_md


def test_parse_cursos_md_returns_courses():
    """Faz o parse do arquivo real → cursos com nome, resumo e ementa não-vazia."""
    courses = parse_cursos_md()
    assert len(courses) >= 2

    for course in courses:
        assert course["name"]
        assert isinstance(course["sections"], list) and course["sections"]
        # Cada curso tem uma ementa (syllabus) com linhas estruturadas.
        assert isinstance(course["syllabus"], list)
        assert len(course["syllabus"]) >= 1
        for row in course["syllabus"]:
            # Linhas têm uma chave de tema/módulo e o conteúdo.
            assert row.get("tema") or row.get("modulo")
            assert "conteudo" in row

    # Pelo menos um curso traz um resumo (vindo de "Objetivo Central").
    assert any(c["summary"] for c in courses)


def test_parse_cursos_md_carga_attached():
    """A carga horária do cabeçalho de cronograma é propagada quando exposta."""
    master = course_ementa("Master")
    assert master is not None
    # O Master expõe carga ("10 meses - 160 horas - Semanal") no cabeçalho da seção.
    assert any("carga" in row for row in master["syllabus"])


def test_course_ementa_matches_by_name():
    """Casa o nome do curso (substring/apelido, case-insensitive)."""
    master = course_ementa("Master")
    assert master is not None
    assert "MASTER" in master["name"].upper() or "APERFEI" in master["name"].upper()

    # Apelido do catálogo: "Aperfeiçoamento Clínico" → mesmo curso Master.
    aperf = course_ementa("Aperfeiçoamento Clínico")
    assert aperf is not None and aperf["name"] == master["name"]

    # "Imersão" (com nome de turma) → curso Imersão.
    imersao = course_ementa("Imersão T3 - 2026")
    assert imersao is not None
    assert "IMERS" in imersao["name"].upper()

    # Nome sem correspondência → None.
    assert course_ementa("Curso Inexistente XYZ") is None
    assert course_ementa("") is None
