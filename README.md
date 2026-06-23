# Captus

CRM com IA nativa para o setor de educação. Cliente: MR Digital, empresa afiliada à FOUSP que vende cursos presenciais de implantodontia digital em turmas com vagas limitadas.

Projeto da disciplina PRO3151 (Laboratório de Sistemas de Informação), Grupo 10.

## O que é

O diferencial do Captus frente a um CRM genérico é que leads, cursos, turmas e vagas são integrados, e a inteligência artificial é parte nativa da ferramenta. O modelo de dados é centrado no negócio (deal): cada negócio liga um lead a uma turma, então o mesmo lead pode avançar em ritmos diferentes para turmas diferentes.

## Funcionalidades

- Funil de vendas em Kanban, ligado ao banco, com histórico de cada movimentação (REQF01 e REQF02).
- Importação de conversas exportadas do WhatsApp, como alternativa à API da Meta (REQF03).
- Análise comportamental por IA: cada conversa vira um perfil do lead com persona, dores, desejos, estágio SPIN e pontuação (REQF08).
- Copiloto: um agente que apoia o vendedor, com RAG sobre os materiais dos cursos e a base de conhecimento, somado ao histórico e ao perfil do lead.
- Cursos, turmas, conteúdo editável e matrícula com controle de vagas (REQF04, REQF05 e REQF06).
- Painel de Analytics com métricas do funil e de público (REQF07).

## Arquitetura

Três tiers, cada um em seu contêiner, orquestrados pelo Docker Compose:

- Frontend: React, Vite, React Router e TanStack Query.
- Backend: FastAPI (Python), SQLAlchemy e Alembic, em camadas (api, services, models), com a IA como módulo de primeira classe.
- Banco: PostgreSQL 16 com a extensão pgvector.
- IA: SDK Anthropic (Claude) para geração de texto; OpenAI (text-embedding-3-small) para os embeddings do RAG.

## Como executar

Pré-requisitos: Docker e Docker Compose.

1. Crie o arquivo de ambiente do backend a partir do exemplo e preencha as chaves:

   ```bash
   cp src/backend/.env.example src/backend/.env
   ```

   Defina `ANTHROPIC_API_KEY` e `OPENAI_API_KEY`. Sem elas o núcleo do CRM funciona, mas o copiloto, a análise e os embeddings ficam indisponíveis.

2. Suba os três serviços de forma integrada:

   ```bash
   docker compose up
   ```

3. Popule os dados de demonstração:

   ```bash
   docker compose exec backend python scripts/seed.py
   docker compose exec backend python scripts/seed_pipeline.py
   ```

4. Acesse:

   - Interface: http://localhost:5173
   - API e documentação interativa: http://localhost:8000/docs
   - Saúde: http://localhost:8000/health

## Estrutura do repositório

- `src/backend`: API FastAPI (`app/{api,services,models,schemas,core,db,prompts}`), migrações Alembic, scripts e testes.
- `src/frontend`: SPA em React (pages, components, lib, hooks).
- `specs/`: especificações por feature (desenvolvimento guiado por especificação).
- `relatorio_ciclo2/`: material do relatório do Ciclo 2 (texto, diagramas e o `.docx`).
- `docs/SRD.md`: documento de requisitos original.
- `docker-compose.yml`: orquestração dos três serviços.

## Testes e qualidade

- Testes: `docker compose exec backend pytest`
- Lint: `docker compose exec backend ruff check .`
- Build do frontend: `cd src/frontend && npm run build`
- Integração contínua (GitHub Actions): lint, testes, build das imagens e um teste de fumaça com docker compose a cada mudança.

## Documentação

- Relatório completo do trabalho: `PRO3151 - Laboratório de Sistemas de Informações - Relatório do Trabalho da disciplina - Grupo 10.md`
- Especificações de cada feature: `specs/`
- Requisitos originais (SRD): `docs/SRD.md`

## Grupo 10

- Felipe Smaniotto Costa (16865335)
- Henrique Guaré Romano (6610082)
- Murilo Dib Abud (16893751)
- Ulisses Calixto Aquino Fontoura (16903160)
- Miguel Francisco Soares Barros (15586304)
