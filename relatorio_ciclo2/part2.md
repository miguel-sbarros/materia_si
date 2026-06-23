# 6 Arquitetura e implementação do Backend

No Ciclo 1 o protótipo apresentava quatro telas (Analytics, Funil, Conversas e Cursos). No Ciclo 2 o sistema ganhou uma quinta visão, o Copiloto, um agente de apoio ao vendedor que usa RAG sobre os materiais dos cursos e o histórico do lead. O Copiloto não estava entre os requisitos numerados do Ciclo 1, mas concretiza o "agente copiloto de vendas" já previsto no escopo (seção 2.1) e ilustra uma decisão central deste ciclo: tratar a inteligência artificial como uma preocupação de primeira classe dentro do backend.

## 6.1 Diagrama de arquitetura do sistema (Blueprint) e descrição

A Figura 5 apresenta o blueprint do Captus. O sistema adota uma arquitetura em camadas sobre três tiers físicos, cada um executando como um contêiner próprio, coordenados pelo Docker Compose:

- Tier 1, Frontend: uma Single-Page Application em React (Vite, React Router, TanStack Query). Todo o acesso ao backend passa por uma camada de costura única (`lib/api.js`), o que mantém o contrato HTTP isolado em um só ponto.
- Tier 2, Backend: uma API FastAPI servida por Uvicorn, internamente subdividida em camadas. A camada de API reúne os roteadores finos (`api/routes`), a camada de Services concentra as regras de negócio e é o único ponto de acesso a banco e LLM, e a camada de Models/DB faz o mapeamento objeto-relacional com SQLAlchemy. Dentro dessa camada vive, como módulo de primeira classe, a IA (`services/llm`, `services/rag`, `prompts`), que consome o SDK Anthropic para geração e a API de embeddings da OpenAI. As tarefas longas (análise de conversas, ingestão de conhecimento e re-embedding de conteúdo) rodam em segundo plano com FastAPI BackgroundTasks.
- Tier 3, Banco: PostgreSQL 16 com a extensão pgvector, que guarda tanto as tabelas relacionais quanto os vetores de embedding (`knowledge_chunks`) usados na busca semântica.

![Figura 5. Blueprint da arquitetura: três tiers, layering interno do backend e a camada de IA.](relatorio_ciclo2/diagramas/blueprint.png)

Escolha do estilo e justificativa pelos requisitos não funcionais. Optou-se por um monólito modular em camadas, e não por microsserviços, por ser a forma mais simples de atender aos requisitos não funcionais sem complexidade operacional desnecessária:

- Desempenho (REQNF01): dentro do backend, o caminho de uma requisição (roteador, depois service, depois ORM, depois banco) ocorre no mesmo processo, sem saltos de rede entre camadas, o que sustenta os alvos de latência. O trabalho lento (chamadas ao LLM, geração de embeddings, importações em lote) vai para segundo plano e nunca bloqueia a resposta ao usuário. As agregações do painel são resolvidas pelo próprio banco, perto dos dados. O retorno visual do arraste de cards no funil é entregue pela atualização otimista do TanStack Query no frontend, sem depender da ida e volta ao servidor.
- Escalabilidade de usuários (REQNF02): a separação em tiers torna a camada de aplicação sem estado, já que todo o estado vive no tier de banco. Por isso o backend pode ser replicado horizontalmente atrás de um balanceador sem alteração do código de aplicação, exatamente como o critério exige, e a imagem Docker torna essa replicação simples.
- Escalabilidade de dados (REQNF03): isolar o banco em seu próprio tier permite dimensioná-lo e ajustá-lo de forma independente. Os índices e a extensão pgvector mantêm as consultas rápidas conforme a base cresce.
- Segurança (REQNF04 e REQNF05, ainda não implementados): o layering é o que torna esses requisitos adições baratas no futuro. A autenticação por JWT entra como uma dependência na camada de API, sem tocar os services, e o Row-Level Security é aplicado no tier de banco, como defesa em profundidade.
- Manutenibilidade: roteadores finos, services donos da lógica e modelos isolados fazem com que cada nova funcionalidade siga um padrão repetível, formado por um modelo, um service, um roteador fino e uma migração. Essa separação também viabiliza o desenvolvimento orientado a testes, pois os services são testáveis de forma isolada.

Orquestração pela rede interna do Docker. Os três contêineres sobem de forma integrada com `docker compose up` e se comunicam por nome de serviço em uma rede interna privada. O backend alcança o banco pelo host `db`, e o frontend consome o backend pela porta publicada. Healthchecks ordenam a inicialização: o backend só inicia depois que o banco fica saudável e, ao subir, aplica as migrações antes de servir. Os detalhes de construção e orquestração estão na Seção 7.

## 6.2 Estrutura de pastas e separação de responsabilidades

Todo o código implantável fica sob `src/`, separado do contexto de projeto e da infraestrutura na raiz (`docker-compose.yml`, `specs/`, `data/`, `.github/`). O sistema se divide em dois processos independentes, `src/frontend/` (React) e `src/backend/` (FastAPI):

```
src/
  frontend/                 Tier 1, React + Vite (processo Node)
    src/{pages,components,lib,hooks,data}
  backend/                  Tier 2, FastAPI (processo Python/uvicorn)
    app/
      core/                 config (Settings) e constantes (StrEnums)
      db/                   engine, sessao, Base, enum_column()
      models/               SQLAlchemy ORM (um arquivo por agregado)
      schemas/              contratos Pydantic (entrada e saida)
      services/             regras de negocio e acesso a DB e LLM
        llm/                wrapper do SDK Anthropic
      prompts/              prompts de analise e copiloto
      api/routes/           roteadores finos (HTTP para service)
    alembic/versions/       migracoes versionadas (0001 ate 0009)
    scripts/                seed, ingestao de conhecimento, import em lote
    tests/                  pytest (TDD)
```

Por que processos separados. Frontend e backend rodam separados porque têm runtimes diferentes (Node/Vite e Python/Uvicorn), ciclos de build distintos e perfis de escala diferentes. O frontend é um artefato estático, servível por CDN, e o backend é um serviço que escala horizontalmente. O acoplamento entre eles é apenas o contrato HTTP/JSON descrito pelo OpenAPI, o que permite evoluí-los de forma independente.

Responsabilidades dentro do backend. A regra é "roteadores finos, services completos": nenhum acesso a banco ou LLM acontece fora da camada de services.

| Camada | Pasta | Responsabilidade |
| --- | --- | --- |
| API | `app/api/routes/` | Traduzir HTTP para chamada de service, validar entrada e mapear erros para 404/409/422. Sem lógica de negócio. |
| Services | `app/services/` | Regras de negócio. Único ponto de acesso ao banco (SQLAlchemy) e ao LLM (SDK Anthropic). |
| Models | `app/models/` | Entidades ORM e relacionamentos, um arquivo por agregado, registrados em `__init__.py`. |
| Schemas | `app/schemas/` | Contratos Pydantic de entrada e saída (camelCase no fio quando consumidos pelo frontend). |
| Core e DB | `app/core/`, `app/db/` | Configuração por variáveis de ambiente, constantes (enums) e a infraestrutura de sessão e Base. |

Não há uma camada `repositories/` por decisão deliberada: nesta escala, o próprio SQLAlchemy é a camada de acesso a dados, e um repositório seria abstração sem uso.

## 6.3 Contrato da API (Endpoints e Lógica)

O backend expõe cerca de 28 endpoints REST, organizados por recurso. A tabela lista os principais, e cada rota atende a um requisito.

| Método | Rota | Funcionalidade | Payload (entrada) | Resposta (sucesso) |
| --- | --- | --- | --- | --- |
| GET | `/health` | Liveness e checagem do banco | (nenhum) | `{status, db}` |
| GET | `/courses` | Lista cursos e turmas (REQF04) | (nenhum) | `[CourseOut]` |
| POST | `/courses` | Cria curso | `CourseCreate` | `201 CourseOut` (409 duplicado) |
| PUT | `/courses/{id}` | Edita curso | `CourseUpdate` | `CourseOut` |
| POST | `/courses/{id}/cohorts` | Cria turma | `CohortCreate` | `201 CohortOut` |
| PUT | `/cohorts/{id}` | Edita turma | `CohortUpdate` | `CohortOut` |
| GET | `/courses/{id}/ementa` | Curso e ementa (módulos do banco, com fallback ao arquivo) | (nenhum) | `{course, ementa}` |
| GET | `/courses/{id}/modules` | Lista módulos do conteúdo | (nenhum) | `[ModuleOut]` |
| POST | `/courses/{id}/modules` | Cria módulo e dispara re-ingestão no RAG | `ModuleCreate` | `201 ModuleOut` |
| PUT | `/modules/{id}` | Edita módulo e dispara re-ingestão | `ModuleUpdate` | `ModuleOut` |
| DELETE | `/modules/{id}` | Remove módulo e dispara re-ingestão | (nenhum) | `204` |
| POST | `/cohorts/{id}/enrollments` | Matricula um lead na turma e leva o deal a won (REQF06) | `{lead_id, source?}` | `201 EnrollmentOut` (404, 409, 422 turma lotada) |
| GET | `/cohorts/{id}/enrollments` | Vagas e matriculados | (nenhum) | `{capacity, enrolled, available, enrollments[]}` |
| DELETE | `/cohorts/{id}/enrollments/{lead_id}` | Cancela matrícula e libera vaga | (nenhum) | `200 {status}` |
| POST | `/leads` | Cria lead e deal inicial (REQF01) | `{name, email?, phone?, source?, cohort_id}` | `201 DealCard` (409 e-mail duplicado) |
| GET | `/leads?q=` | Busca leads por nome | (nenhum) | `[LeadSummary]` |
| GET | `/leads/{id}` | Lead com deals e perfil de IA | (nenhum) | `LeadDetail` |
| PATCH | `/leads/{id}` | Edita lead | `LeadUpdate` | `LeadDetail` |
| POST | `/leads/{id}/deals` | Posiciona lead em turma e estágio | `{cohort_id, stage}` | `201 DealCard` |
| POST | `/leads/{id}/analyze` | Análise de conversa e geração de perfil (REQF08) | (nenhum) | `LeadProfileOut` |
| GET | `/deals?course_id=&cohort_id=` | Alimenta o quadro do funil (REQF02) | (nenhum) | `[DealCard]` |
| PATCH | `/deals/{id}` | Move ou transiciona o deal e grava o histórico | `{column, lost_reason?}` | `DealCard` |
| POST | `/imports` | Importa conversa exportada do WhatsApp (.txt ou .zip, REQF03) | multipart | `ImportSummary` |
| GET | `/leads/{id}/conversation` | Histórico da conversa | (nenhum) | `{conversation, messages}` |
| GET | `/conversations` | Lista conversas | (nenhum) | `[ConversationSummary]` |
| POST | `/copilot/sessions/{id}/chat` | Conversa com o Copiloto (RAG) | `{text, command?}` | `MessageOut` |
| GET | `/analytics` | KPIs, funil, ICP, churn por SPIN e receita (REQF07 e REQF08) | (nenhum) | `{kpis, funnel, ...}` |

## 6.4 Documentação e integração com o Frontend

O FastAPI gera de forma automática a especificação OpenAPI, exposta como documentação interativa (Swagger UI) em `/docs`. Como cada entrada e saída é um schema Pydantic (`CourseOut`, `DealCard`, `EnrollmentOut`, `ModuleOut`), o `/docs` documenta payloads, exemplos e códigos de status sem esforço manual, e funcionou como o contrato vivo entre os dois processos do sistema.

Do lado do React, todo o acesso passa pela costura única `lib/api.js`, em que cada função corresponde a um endpoint. O TanStack Query cuida do estado de servidor, com cache por chaves e atualização otimista no arraste do funil e nas matrículas. O contrato fixa três convenções que o frontend consome direto: camelCase no fio para os modelos lidos pela interface (por exemplo `DealCard.leadId` e `EnrollmentOut.enrolledAt`), dinheiro como `Decimal` serializado em texto, sem perda, convertido com `Number()` no cliente, e enums pelos seus valores legíveis. Na prática, o `/docs` permitiu exercitar os endpoints antes mesmo da interface existir, por exemplo disparar uma matrícula e observar o retorno `422 Turma lotada`, o que acelerou a integração e revelou divergências de contrato cedo.

# 7 Infraestrutura e conteinerização (Docker)

O Captus é totalmente conteinerizado. O comando `docker compose up` sobe os três tiers (frontend, backend e banco) de forma integrada, em uma rede interna isolada. Esta seção descreve as receitas de construção, a orquestração e a configuração por variáveis de ambiente.

## 7.1 Receitas de construção (Dockerfiles)

Backend (`src/backend/Dockerfile`). Imagem Python enxuta que instala o pacote em modo editável e sobe o servidor:

```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install --no-cache-dir -e ".[dev]"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Frontend (`src/frontend/Dockerfile`). Imagem Node Alpine que separa a instalação de dependências do código-fonte, aproveitando o cache de camadas do Docker (as dependências só são reinstaladas quando `package*.json` muda):

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

Elementos-chave nas duas imagens: imagem base mínima, diretório de trabalho `/app`, instalação de dependências isolada (pip e `npm ci`) e comando de inicialização. A próxima evolução natural do frontend para produção é um build em múltiplos estágios servindo arquivos estáticos por Nginx, no lugar do servidor de desenvolvimento.

## 7.2 Orquestração de serviços (Docker Compose)

O `docker-compose.yml` coordena os três serviços. Trecho comentado:

```yaml
services:
  db:                                   # Tier 3, PostgreSQL + pgvector
    image: pgvector/pgvector:pg16
    environment: { POSTGRES_USER: captus, POSTGRES_PASSWORD: captus, POSTGRES_DB: captus }
    volumes: [ pgdata:/var/lib/postgresql/data ]   # persistencia entre reinicios
    healthcheck:                        # pg_isready libera quem depende do banco
      test: ["CMD-SHELL", "pg_isready -U captus -d captus"]

  backend:                              # Tier 2, FastAPI
    build: ./src/backend
    depends_on: { db: { condition: service_healthy } }
    env_file: [ ./src/backend/.env ]
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    ports: ["8000:8000"]

  frontend:                             # Tier 1, React/Vite
    build: ./src/frontend
    depends_on: [ backend ]
    environment: { VITE_API_URL: http://localhost:8000 }
    ports: ["5173:5173"]

volumes: { pgdata: {} }
```

Rede interna do Docker. Os serviços compartilham a rede padrão criada pelo Compose e se resolvem por nome de serviço. O backend alcança o banco pelo host `db` na porta 5432, exatamente o que está em `DATABASE_URL`, sem expor o banco à máquina hospedeira para a comunicação entre serviços. Há uma distinção importante e proposital: o frontend é uma SPA que roda no navegador do usuário, não dentro do contêiner, por isso a sua `VITE_API_URL` aponta para `http://localhost:8000`, que é a porta publicada do backend, acessível ao navegador. Já o tráfego entre backend e banco trafega pela rede interna pelo nome `db`.

Ordem de subida e resiliência. O `depends_on` com `service_healthy` garante que o backend só inicie quando o `pg_isready` do banco passar. Ao subir, o backend aplica as migrações (`alembic upgrade head`) antes de servir, e o healthcheck próprio do backend sinaliza prontidão ao Compose e ao teste de fumaça do CI. O volume nomeado `pgdata` mantém os dados do PostgreSQL entre reinícios, o que sustenta a transição de protótipo volátil para aplicação persistente descrita na Seção 9.

## 7.3 Padronização e variáveis de ambiente

A configuração fica centralizada em `app/core/config.py` (classe `Settings`, com pydantic-settings), que lê de variáveis de ambiente e de um arquivo `.env`. Segredos nunca são versionados: o `.env` está no `.gitignore` e um `.env.example` documenta o contrato. Isso garante segurança e flexibilidade, pois a mesma imagem roda em ambiente local ou em nuvem trocando apenas o ambiente, sem alterar código.

| Variável | Tipo | Uso |
| --- | --- | --- |
| `DATABASE_URL` | configuração | URL SQLAlchemy do Postgres (driver psycopg 3); por padrão aponta para o host interno `db`. |
| `TEST_DATABASE_URL` | configuração | banco de testes; se ausente, o conftest deriva um `<db>_test`. |
| `ANTHROPIC_API_KEY` | segredo | acesso ao SDK Anthropic (copiloto e análise). |
| `OPENAI_API_KEY` | segredo | acesso à API de embeddings (RAG). |
| `MODEL_COPILOT` e `MODEL_EXTRACTION` | configuração | modelos LLM (`claude-sonnet-4-6` e `claude-haiku-4-5`). |
| `EMBEDDING_MODEL` e `EMBEDDING_DIM` | configuração | modelo e dimensão dos vetores (`text-embedding-3-small`, 1536). |
| `CORS_ORIGINS` | configuração | origens permitidas (o frontend Vite em desenvolvimento: `http://localhost:5173`). |

As credenciais do banco entram pelo Compose (variáveis `POSTGRES_*`) e são consumidas pelo backend por meio do `DATABASE_URL`. As chaves de LLM e de embeddings entram pelo `env_file` do serviço de backend. A separação explícita entre segredos (chaves e senha do banco) e configuração (modelos, dimensões e CORS) mantém o que é sensível fora do código e do versionamento.

# 8 Camada de persistência (Banco de Dados)

A persistência do Captus usa PostgreSQL 16 com a extensão pgvector, executando como serviço próprio e isolado no Compose. O esquema foi desenhado em torno de uma decisão estrutural que dá nome ao modelo de dados, o grão centrado no negócio (`deal: lead para cohort`). Diferente de um CRM genérico, em que cada lead é uma oportunidade única, no Captus um mesmo lead pode ocupar estágios comerciais distintos para turmas diferentes, e cada vínculo desses é um registro próprio na tabela `deals`. O modelo final reúne 15 tabelas, introduzidas de forma incremental por 9 migrações Alembic, organizadas em três blocos: núcleo comercial (`users`, `courses`, `cohorts`, `leads`, `deals`, `deal_events`, `enrollments`, `course_modules`), comunicação e análise (`conversations`, `messages`, `lead_profiles`) e camada de IA (`knowledge_chunks`, `personas`, `copilot_sessions`, `copilot_messages`).

## 8.1 Modelo relacional e esquema de tabelas

A Figura 6 apresenta o modelo entidade-relacionamento completo. O núcleo comercial forma a espinha do sistema: um curso oferece várias turmas, cada lead é atribuído a um vendedor, e cada deal conecta um lead a uma turma. Toda transição de um deal é registrada em `deal_events`, o que materializa o histórico exigido pelo REQF02. O bloco de comunicação anexa a cada lead suas conversas e mensagens (REQF03) e um perfil 1 para 1 com a análise comportamental por IA (REQF08). O bloco de IA sustenta o Copiloto: `knowledge_chunks` guarda o corpus vetorizado para busca semântica, e as tabelas de sessão e mensagens do copiloto persistem o diálogo do agente.

![Figura 6. Modelo entidade-relacionamento do Captus, com 15 tabelas e a espinha centrada no negócio.](relatorio_ciclo2/diagramas/er_modelo.png)

A seguir, o script SQL das tabelas principais, no estado final do esquema. As chaves primárias (PK) e estrangeiras (FK) estão indicadas:

```sql
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(120) NOT NULL,
    role       VARCHAR      NOT NULL DEFAULT 'seller',   -- seller ou admin
    email      VARCHAR(255) NOT NULL,
    initials   VARCHAR(8),
    active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE TABLE courses (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,
    description TEXT,
    modality    VARCHAR(40)  NOT NULL DEFAULT 'Presencial',
    price       NUMERIC(10,2),
    duration    VARCHAR(80),
    active      BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_courses_name UNIQUE (name)
);

CREATE TABLE cohorts (
    id             SERIAL PRIMARY KEY,
    course_id      INTEGER NOT NULL REFERENCES courses(id),   -- FK
    name           VARCHAR(200) NOT NULL,
    start_date     DATE,
    end_date       DATE,
    capacity       INTEGER,
    price_per_slot NUMERIC(10,2),
    status         VARCHAR NOT NULL DEFAULT 'open'
                   CHECK (status IN ('open','active','finished'))
);

CREATE TABLE leads (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(160) NOT NULL,
    email            VARCHAR(255),
    phone            VARCHAR(40),
    source           VARCHAR(60),
    assignee_id      INTEGER REFERENCES users(id),           -- FK
    external_user_id VARCHAR(120),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_leads_external_user_id UNIQUE (external_user_id)
);
-- Dedupe de e-mail apenas quando informado (REQF01):
CREATE UNIQUE INDEX uq_leads_email_present
    ON leads (email) WHERE email IS NOT NULL;

CREATE TABLE deals (
    id          SERIAL PRIMARY KEY,
    lead_id     INTEGER NOT NULL REFERENCES leads(id),       -- FK
    cohort_id   INTEGER NOT NULL REFERENCES cohorts(id),     -- FK
    stage       VARCHAR NOT NULL DEFAULT 'Novo'
                CHECK (stage IN ('Novo','Contatado','Negociando','Aprovado')),
    status      VARCHAR NOT NULL DEFAULT 'open',             -- open, won, lost
    lost_reason TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_deals_lead_cohort UNIQUE (lead_id, cohort_id),
    CONSTRAINT ck_deals_lost_reason CHECK (status <> 'lost' OR lost_reason IS NOT NULL)
);

CREATE TABLE enrollments (
    id         SERIAL PRIMARY KEY,
    lead_id    INTEGER NOT NULL REFERENCES leads(id),        -- FK
    cohort_id  INTEGER NOT NULL REFERENCES cohorts(id),      -- FK
    deal_id    INTEGER REFERENCES deals(id),                 -- deal que materializa a matricula
    status     VARCHAR NOT NULL DEFAULT 'active'
               CHECK (status IN ('active','cancelled')),
    source     VARCHAR(60),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_enrollments_lead_cohort UNIQUE (lead_id, cohort_id)
);

CREATE TABLE course_modules (
    id         SERIAL PRIMARY KEY,
    course_id  INTEGER NOT NULL REFERENCES courses(id),      -- FK
    title      VARCHAR(300) NOT NULL,
    content    TEXT,
    position   INTEGER NOT NULL DEFAULT 0,
    carga      VARCHAR(80),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE knowledge_chunks (
    id         SERIAL PRIMARY KEY,
    source     VARCHAR(40)  NOT NULL,
    node_ref   VARCHAR(200) NOT NULL,
    content    TEXT NOT NULL,
    persona    VARCHAR(60),
    spin_stage VARCHAR(40),
    embedding  VECTOR(1536) NOT NULL,   -- pgvector: busca semantica
    tsv        TSVECTOR,                -- preparado para BM25 (adiado)
    CONSTRAINT uq_knowledge_chunks_source_ref UNIQUE (source, node_ref)
);
```

As duas tabelas centrais do domínio aparecem detalhadas abaixo. A tabela `leads` representa a entidade principal, o potencial aluno. A tabela `deals` é a tabela de relacionamento que conecta lead e turma, semelhante a um pedido, onde fica a lógica do funil.

Tabela `leads` (entidade, potencial aluno):

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | SERIAL | PK, NOT NULL | Identificador único e imutável do lead. |
| `name` | VARCHAR(160) | NOT NULL | Nome do potencial aluno. |
| `email` | VARCHAR(255) | UNIQUE parcial (`WHERE email IS NOT NULL`) | Dedupe de e-mail quando informado (REQF01). Permite leads sem e-mail, importados do WhatsApp só com telefone. |
| `phone` | VARCHAR(40) | (nenhuma) | Telefone ou identificador de origem. |
| `source` | VARCHAR(60) | (nenhuma) | Canal de captação (Instagram, Indicação, WhatsApp). |
| `assignee_id` | INTEGER | FK para `users(id)` | Vendedor responsável pelo lead. |
| `external_user_id` | VARCHAR(120) | UNIQUE | Chave natural externa; garante idempotência na importação. |
| `created_at`, `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Auditoria temporal. |

Tabela `deals` (relacionamento, negócio entre lead e turma):

| Coluna | Tipo | Restrições | Descrição |
| --- | --- | --- | --- |
| `id` | SERIAL | PK, NOT NULL | Identificador único do negócio. |
| `lead_id` | INTEGER | FK para `leads(id)`, NOT NULL | Lead vinculado ao negócio. |
| `cohort_id` | INTEGER | FK para `cohorts(id)`, NOT NULL | Turma do negócio (o curso é alcançado pela turma). |
| `stage` | VARCHAR | NOT NULL, CHECK | Estágio no funil: Novo, Contatado, Negociando, Aprovado. |
| `status` | VARCHAR | NOT NULL | Desfecho: open, won (vira "Matriculado") ou lost (vira "Perdido"). |
| `lost_reason` | TEXT | CHECK `ck_deals_lost_reason` | Motivo obrigatório quando `status = 'lost'`. |
| (`lead_id`, `cohort_id`) | (par) | UNIQUE `uq_deals_lead_cohort` | No máximo um negócio por par lead e turma. |

## 8.2 Integridade de dados e restrições (constraints)

Um princípio de projeto do Captus foi empurrar regras de negócio para o banco de dados, transformando-o na última linha de defesa da integridade, independente da aplicação. A tabela a seguir resume as principais restrições e a regra que cada uma garante:

| Constraint | Tipo | Tabela | Regra de negócio garantida |
| --- | --- | --- | --- |
| `uq_users_email` | UNIQUE | `users` | Não existem dois usuários com o mesmo e-mail. |
| `uq_courses_name` | UNIQUE | `courses` | Catálogo sem cursos duplicados. |
| `uq_leads_email_present` | UNIQUE parcial | `leads` | REQF01: impede dois leads com o mesmo e-mail quando informado, e permite vários leads sem e-mail. |
| `uq_deals_lead_cohort` | UNIQUE | `deals` | Materializa o grão `deal: lead para cohort`, um negócio por par lead e turma. |
| `ck_deals_lost_reason` | CHECK | `deals` | Um negócio perdido exige motivo registrado. |
| `deal_stage` | CHECK | `deals` | Estágio restrito a Novo, Contatado, Negociando, Aprovado. |
| `uq_enrollments_lead_cohort` | UNIQUE | `enrollments` | Um lead se matricula no máximo uma vez por turma. |
| `enrollment_status` | CHECK | `enrollments` | Status restrito a active ou cancelled; cancelar libera a vaga. |
| FKs (`assignee_id`, `course_id`, `cohort_id`, `lead_id`, `deal_id`) | FOREIGN KEY | várias | Integridade referencial, sem registros órfãos. |
| `uq_conversations_lead_channel` | UNIQUE | `conversations` | Uma conversa por canal por lead, o que torna a reimportação idempotente. |
| `uq_messages_conversation_sequence` | UNIQUE | `messages` | Ordem estável das mensagens e idempotência da reimportação. |
| `uq_lead_profiles_lead` | UNIQUE | `lead_profiles` | Perfil 1 para 1 com o lead. |
| `uq_knowledge_chunks_source_ref` | UNIQUE | `knowledge_chunks` | Idempotência da ingestão do corpus de RAG. |

Exemplo concreto (REQF01). A regra de não cadastrar dois leads com o mesmo e-mail é imposta pelo índice único parcial `uq_leads_email_present`. A escolha pelo índice parcial (`WHERE email IS NOT NULL`) é proposital e ditada pelo domínio: leads importados de conversas de WhatsApp muitas vezes não têm e-mail, apenas telefone, e um UNIQUE comum bloquearia mais de um lead sem e-mail, já que todos seriam nulos e tratados como iguais. O índice parcial garante a deduplicação onde ela faz sentido sem penalizar a importação real.

Observação sobre os enums. Os enums são declarados como `VARCHAR` com restrição `CHECK`, guardando o valor legível no banco (por exemplo `'Negociando'`), o que mantém o banco fácil de inspecionar. As três restrições de estágio do funil são materializadas no banco; os demais conjuntos de valores são validados também na camada de aplicação, formando uma estratégia de defesa em profundidade. Já o bloqueio de turma lotada (matrículas ativas maiores ou iguais à capacidade) é validado na camada de aplicação, com retorno 422, por ser uma contagem dinâmica e não uma invariante estática de linha.

## 8.3 Consultas de negócio e análise de dados

A inteligência exibida no painel e usada pelo Copiloto vem de consultas agregadas sobre o esquema. As três consultas a seguir, todas com `JOIN` e `GROUP BY`, ilustram como o banco extrai conhecimento operacional.

Consulta 1. Distribuição do funil por coluna do quadro e valor potencial. Mapeia status e stage para a coluna visível no Kanban e soma o valor de cada negócio (preço da turma, com fallback no preço do curso):

```sql
SELECT CASE WHEN d.status = 'won'  THEN 'Matriculado'
            WHEN d.status = 'lost' THEN 'Perdido'
            ELSE d.stage END                         AS coluna,
       COUNT(*)                                      AS negocios,
       SUM(COALESCE(co.price_per_slot, c.price))     AS valor_potencial
FROM deals d
JOIN cohorts co ON co.id = d.cohort_id
JOIN courses c  ON c.id  = co.course_id
GROUP BY coluna
ORDER BY negocios DESC;
```

Consulta 2. Conversão por persona, que é o Perfil Ideal de Cliente. Cruza leads, o perfil gerado por IA e os negócios para revelar qual persona converte mais, ligando a análise comportamental (REQF08) à decisão comercial. Os `LEFT JOIN` preservam leads sem perfil ou sem negócio:

```sql
SELECT COALESCE(lp.matched_persona, 'Indeterminado')          AS persona,
       COUNT(DISTINCT l.id)                                   AS leads,
       COUNT(d.id)                                            AS negocios,
       COUNT(*) FILTER (WHERE d.status = 'won')               AS matriculas,
       ROUND(COUNT(*) FILTER (WHERE d.status = 'won')::numeric
             / NULLIF(COUNT(d.id), 0), 4)                     AS taxa_conversao
FROM leads l
LEFT JOIN lead_profiles lp ON lp.lead_id = l.id
LEFT JOIN deals d          ON d.lead_id  = l.id
GROUP BY persona
ORDER BY leads DESC;
```

Consulta 3. Ocupação e receita por turma, a partir das matrículas ativas, que são a fonte da verdade das vagas. Reflete cancelamentos que liberam vaga:

```sql
SELECT c.name AS curso, co.name AS turma,
       COUNT(*) FILTER (WHERE e.status = 'active')                              AS matriculas,
       co.capacity                                                             AS vagas,
       SUM(COALESCE(co.price_per_slot, c.price)) FILTER (WHERE e.status='active') AS receita
FROM enrollments e
JOIN cohorts co ON co.id = e.cohort_id
JOIN courses c  ON c.id  = co.course_id
GROUP BY c.name, co.name, co.capacity
ORDER BY receita DESC NULLS LAST;
```

Consulta de IA (busca vetorial do RAG). Embora não seja uma agregação, vale registrar a consulta que distingue o Captus de um CRM tradicional, a recuperação semântica do corpus pelo pgvector. O operador `<=>` calcula a distância de cosseno entre o embedding da pergunta e os trechos armazenados, e retorna os mais relevantes, com filtro opcional pela persona do lead:

```sql
SELECT node_ref, title, content
FROM knowledge_chunks
WHERE persona = :persona               -- filtro opcional pela persona do lead
ORDER BY embedding <=> :query_embedding   -- distancia de cosseno (pgvector)
LIMIT 5;
```

# 9 Conclusão do Ciclo 2

O Ciclo 2 transformou o protótipo do Ciclo 1 em uma aplicação completa e persistente. No Ciclo 1 a interface existia como uma página React isolada, com dados fictícios que se perdiam a cada recarregamento. Ao longo do Ciclo 2 o sistema ganhou um backend em camadas, um banco de dados real e uma infraestrutura conteinerizada, e passou a guardar de fato leads, conversas, negócios, matrículas e conteúdo de cursos. O estado de entrega de cada requisito está consolidado na matriz de status abaixo.

| Requisito | Status | Observação |
| --- | --- | --- |
| REQF01 Cadastrar leads | Implementado | dedupe de e-mail por índice parcial |
| REQF02 Pipeline de vendas | Implementado | colunas mais histórico em `deal_events` |
| REQF03 Histórico de interações | Implementado | import WhatsApp .txt e .zip (versão inicial; a WhatsApp Business API ficou fora do ciclo) |
| REQF04 Cursos e turmas | Implementado | inclui gestão de conteúdo e módulos editáveis |
| REQF05 Controlar vagas | Parcial | decremento, bloqueio e liberação prontos; lista de espera adiada |
| REQF06 Matrícula | Implementado | `enrollments` mais deal won mais controle de vaga (corrigido neste ciclo) |
| REQF07 Painel de métricas | Implementado | Analytics agregada real |
| REQF08 Análise comportamental | Implementado | perfil por IA mais agregações |
| REQNF01 Desempenho | Parcial | alvo de projeto; sem benchmark formal de carga |
| REQNF02 Escala de usuários | Adiado | não testado em carga; backend sem estado permite escala horizontal |
| REQNF03 Escala de dados | Parcial | corpus real carregado; limite de 10 mil interações não exercitado |
| REQNF04 Autenticação (JWT) | Adiado | decisão de projeto |
| REQNF05 Segurança em nível de dados (RLS) | Adiado | decisão de projeto |
| REQNF06 Usabilidade | Parcial | heurístico de poucos cliques; sem teste formal com usuários |

Visão geral. O sistema cobre hoje todo o ciclo de vida de um lead, do cadastro à matrícula, com análise comportamental por IA e um agente de apoio ao vendedor.

Sobrevivência da aplicação. A passagem de protótipo volátil para aplicação persistente se apoia em três pilares. O PostgreSQL com um volume dedicado guarda os dados entre reinícios, o que dá confiabilidade. O backend não guarda estado de sessão, então pode ser replicado para atender mais usuários sem mudança de código, o que atende ao requisito de escalabilidade. E a integração contínua, que roda lint, testes, build da imagem e um teste de fumaça a cada mudança, mantém a qualidade ao longo do tempo.

Reconciliação com o plano do Ciclo 1. A conclusão do Ciclo 1 previa Supabase, Redis, Celery e a WhatsApp Business API. O sistema construído seguiu um caminho mais enxuto, adequado à escala do projeto: pgvector no próprio PostgreSQL no lugar do Supabase, e BackgroundTasks do FastAPI no lugar de Redis e Celery para o processamento assíncrono. A integração com a WhatsApp Business API ficou fora deste ciclo por causa da complexidade de homologação, que envolve verificação de número junto à Meta e configuração de webhooks, e por isso o REQF03 foi entregue em uma primeira versão por meio da importação de conversas exportadas em arquivo.

Próximos passos. Ativar a autenticação por JWT (REQNF04) e o controle de acesso no banco (REQNF05); implementar a lista de espera por turma (REQF05); integrar a WhatsApp Business API; executar testes de carga para validar os alvos de desempenho e escala; e servir o frontend como estático em produção.

# 10 Conclusão do Trabalho

Análise dos resultados. O produto confirma a hipótese central do projeto: um CRM pensado para o setor educacional, em que leads, cursos, turmas e vagas formam um todo integrado e a inteligência artificial é parte nativa da ferramenta. O modelo centrado no negócio, com um negócio por lead e por turma, representa com fidelidade um mesmo lead que avança em ritmos diferentes para turmas diferentes, algo que um CRM genérico não trata bem. O Copiloto e a análise automática das conversas mostram, na prática, como a IA agrega valor ao trabalho diário do vendedor.

Aprendizado. Quatro práticas estruturaram o trabalho e ficam como aprendizado: o desenvolvimento guiado por especificação, em que cada funcionalidade começou por um documento com critérios de aceitação que viraram testes; o desenvolvimento orientado a testes; a arquitetura em camadas, que manteve as mudanças localizadas; e a conteinerização desde o primeiro dia. O reaproveitamento de materiais de um projeto anterior, como os prompts, o leitor de conversas e o mapa de personas, acelerou a entrega. Uma lição técnica concreta foi manter pequenos os esquemas de saída estruturada da IA, dividindo a extração em chamadas menores em vez de acumular muitos campos em uma só, o que evitou falhas de processamento no modelo.

Avaliação da disciplina. O roteiro do trabalho orientou bem cada etapa, e a exigência de Docker, integração contínua e testes aproximou o projeto de uma prática profissional de engenharia de software. Como sugestão de aprimoramento, exemplos curtos de referência para cada seção do relatório e um pouco mais de tempo dedicado à fase de integração ajudariam os grupos a chegar ao fim do ciclo com mais folga.

# Anexo: Entrega do produto

O produto está disponível em repositório público, contendo o código-fonte, os prints das principais telas e a documentação completa, que é este relatório.

- Repositório: (link do GitHub do Grupo 10).
- Como executar: com Docker instalado, rodar `docker compose up` na raiz do projeto, o que sobe o banco, o backend e o frontend de forma integrada. Em seguida, popular os dados de demonstração com `scripts/seed.py` e o pipeline de leads com `scripts/seed_pipeline.py`. A interface fica em `http://localhost:5173` e a documentação da API em `http://localhost:8000/docs`.
- Prints das principais telas (inserir as capturas):
  - [Inserir print: Analytics, painel de métricas]
  - [Inserir print: Funil, quadro Kanban]
  - [Inserir print: Conversas, chat e contexto do lead]
  - [Inserir print: Página do Lead, análise por IA]
  - [Inserir print: Cursos, detalhe da turma com vagas e matrícula]
  - [Inserir print: Copiloto, sugestão de resposta]
  - [Inserir print: Swagger em /docs, contrato da API]
