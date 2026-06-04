-- =========================================================================
-- create_tables.sql — Esquema relacional do Captus (PostgreSQL)
-- PRO3151 · Ciclo 2 · Camada de persistência (item 8 do roteiro)
--
-- Adaptado do script da Aula 7 (customers / stores / orders_analytics)
-- para o domínio do Captus: leads, cursos, turmas e matriculas.
--
-- Demonstra: PRIMARY KEY, FOREIGN KEY (integridade referencial),
-- UNIQUE, NOT NULL, CHECK e índices de apoio a busca/join.
-- Executado automaticamente pelo Postgres na primeira subida (compose).
-- =========================================================================

-- Garante reexecução limpa em ambiente de desenvolvimento
DROP TABLE IF EXISTS matriculas CASCADE;
DROP TABLE IF EXISTS turmas     CASCADE;
DROP TABLE IF EXISTS cursos     CASCADE;
DROP TABLE IF EXISTS leads      CASCADE;

-- -------------------------------------------------------------------------
-- LEADS (REQF01, REQF02)
-- -------------------------------------------------------------------------
CREATE TABLE leads (
    id        SERIAL       PRIMARY KEY,                 -- PK: identidade do registro
    nome      VARCHAR(120) NOT NULL,                    -- regra de negócio: nome obrigatório
    email     VARCHAR(150) NOT NULL UNIQUE,             -- impede leads duplicados (REQF01)
    telefone  VARCHAR(20),
    origem    VARCHAR(50)  NOT NULL,
    estagio   VARCHAR(20)  NOT NULL DEFAULT 'Novo'
              CHECK (estagio IN ('Novo','Contatado','Negociando','Matriculado','Perdido'))
);

-- -------------------------------------------------------------------------
-- CURSOS (REQF04)
-- -------------------------------------------------------------------------
CREATE TABLE cursos (
    id          SERIAL       PRIMARY KEY,
    nome        VARCHAR(150) NOT NULL,
    modalidade  VARCHAR(20)  NOT NULL DEFAULT 'Presencial'
                CHECK (modalidade IN ('Presencial','Híbrido','Online')),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE
);

-- -------------------------------------------------------------------------
-- TURMAS (REQF04, REQF05) — relação 1:N com cursos
-- -------------------------------------------------------------------------
CREATE TABLE turmas (
    id             SERIAL  PRIMARY KEY,
    curso_id       INT     NOT NULL
                   REFERENCES cursos(id) ON DELETE RESTRICT,  -- FK: integridade referencial
    data_inicio    DATE    NOT NULL,
    vagas_totais   INT     NOT NULL CHECK (vagas_totais > 0),
    vagas_ocupadas INT     NOT NULL DEFAULT 0 CHECK (vagas_ocupadas >= 0),
    investimento   NUMERIC(10,2) NOT NULL CHECK (investimento >= 0),
    -- REQF05: nunca ocupar mais do que o total de vagas
    CONSTRAINT chk_vagas CHECK (vagas_ocupadas <= vagas_totais)
);

-- -------------------------------------------------------------------------
-- MATRICULAS (REQF06) — associa lead a turma
-- -------------------------------------------------------------------------
CREATE TABLE matriculas (
    id             SERIAL PRIMARY KEY,
    lead_id        INT    NOT NULL REFERENCES leads(id)  ON DELETE CASCADE,
    turma_id       INT    NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    data_matricula DATE   NOT NULL DEFAULT CURRENT_DATE,
    -- um mesmo lead não pode ser matriculado duas vezes na mesma turma
    CONSTRAINT uq_lead_turma UNIQUE (lead_id, turma_id)
);

-- -------------------------------------------------------------------------
-- ÍNDICES de apoio a busca e join (como na Aula 7)
-- -------------------------------------------------------------------------
CREATE INDEX idx_leads_estagio        ON leads (estagio);
CREATE INDEX idx_turmas_curso         ON turmas (curso_id);
CREATE INDEX idx_matriculas_lead_turma ON matriculas (lead_id, turma_id);

-- =========================================================================
-- DADOS DE EXEMPLO (seed) — valores realistas, como no protótipo funcional
-- =========================================================================
INSERT INTO cursos (nome, modalidade, ativo) VALUES
    ('Imersão em Implantodontia Digital', 'Presencial', TRUE),
    ('Dermato-Cirurgia Avançada',         'Híbrido',    TRUE);

INSERT INTO turmas (curso_id, data_inicio, vagas_totais, vagas_ocupadas, investimento) VALUES
    (1, '2026-05-01', 30, 24, 22250.00),
    (1, '2026-09-10', 30,  3, 22250.00),
    (2, '2026-08-15', 20,  5, 18000.00);

INSERT INTO leads (nome, email, telefone, origem, estagio) VALUES
    ('Dra. Helena Martins', 'helena@exemplo.com',  '+5511988887777', 'Indicação',   'Negociando'),
    ('Dr. Ricardo Oliveira','ricardo@exemplo.com', '+5511977776666', 'Site Direto', 'Contatado'),
    ('Dra. Beatriz Santos', 'beatriz@exemplo.com', '+5511966665555', 'Instagram',   'Novo'),
    ('Dr. Lucas Mendes',    'lucas@exemplo.com',   '+5511955554444', 'WhatsApp',    'Matriculado'),
    ('Dra. Elena Rodriguez','elena@exemplo.com',   '+5511944443333', 'Indicação',   'Matriculado');

INSERT INTO matriculas (lead_id, turma_id, data_matricula) VALUES
    (4, 1, '2026-03-12'),
    (5, 1, '2026-03-18');
