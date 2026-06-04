-- =========================================================================
-- consultas_negocio.sql — Consultas de inteligência do Captus
-- PRO3151 · Ciclo 2 · item 8.3 do roteiro
--
-- Pelo menos 3 consultas com SELECT, GROUP BY e JOIN que extraem
-- inteligência do sistema para o usuário final (equipe comercial /
-- administradores da MR Digital).
-- =========================================================================

-- -------------------------------------------------------------------------
-- Consulta 1 — Distribuição de leads por estágio do funil (REQF07)
-- Responde: "quantos leads há em cada fase do pipeline?"
-- Usa: SELECT + GROUP BY
-- -------------------------------------------------------------------------
SELECT
    estagio,
    COUNT(*) AS total_leads
FROM leads
GROUP BY estagio
ORDER BY total_leads DESC;

-- -------------------------------------------------------------------------
-- Consulta 2 — Ocupação e receita prevista por turma (REQF05)
-- Responde: "qual a taxa de ocupação e a receita prevista de cada turma?"
-- Usa: SELECT + JOIN (cursos x turmas) + expressões calculadas
-- -------------------------------------------------------------------------
SELECT
    c.nome                                            AS curso,
    t.id                                              AS turma,
    t.data_inicio,
    t.vagas_ocupadas || '/' || t.vagas_totais         AS vagas,
    ROUND(100.0 * t.vagas_ocupadas / t.vagas_totais, 1) AS ocupacao_pct,
    (t.vagas_ocupadas * t.investimento)               AS receita_realizada,
    (t.vagas_totais   * t.investimento)               AS receita_potencial
FROM turmas t
JOIN cursos c ON c.id = t.curso_id
ORDER BY ocupacao_pct DESC;

-- -------------------------------------------------------------------------
-- Consulta 3 — Matrículas por curso (REQF06)
-- Responde: "quantos alunos cada curso converteu (somando suas turmas)?"
-- Usa: SELECT + JOIN (cursos x turmas x matriculas) + GROUP BY
-- -------------------------------------------------------------------------
SELECT
    c.nome                  AS curso,
    COUNT(m.id)             AS total_matriculas
FROM cursos c
JOIN turmas t      ON t.curso_id = c.id
LEFT JOIN matriculas m ON m.turma_id = t.id
GROUP BY c.nome
ORDER BY total_matriculas DESC;

-- -------------------------------------------------------------------------
-- Consulta 4 (extra) — Conversão por canal de origem
-- Responde: "qual canal de captação mais gera matrículas?"
-- Usa: SELECT + JOIN (leads x matriculas) + GROUP BY
-- -------------------------------------------------------------------------
SELECT
    l.origem,
    COUNT(DISTINCT l.id)                                          AS leads_captados,
    COUNT(DISTINCT m.lead_id)                                     AS leads_matriculados,
    ROUND(100.0 * COUNT(DISTINCT m.lead_id)
          / NULLIF(COUNT(DISTINCT l.id), 0), 1)                   AS taxa_conversao_pct
FROM leads l
LEFT JOIN matriculas m ON m.lead_id = l.id
GROUP BY l.origem
ORDER BY taxa_conversao_pct DESC;
