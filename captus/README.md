# Captus — CRM e Gestão de Turmas (Ciclo 2)

Plataforma de CRM para o setor educacional (cliente: MR Digital), desenvolvida na
disciplina **PRO3151 — Laboratório de Sistemas de Informação**. Este repositório
contém a implementação do Ciclo 2: backend FastAPI, frontend Streamlit, banco
PostgreSQL e orquestração com Docker Compose.

## Arquitetura

```
Streamlit Frontend  (porta 8501)
        ↓ HTTP
FastAPI Backend     (porta 8000)
        ↓ SQL
PostgreSQL Database (porta 5432)
```

Cada serviço roda em um container próprio, comunicando-se pela rede interna do
Docker. O frontend chama o backend por `http://backend:8000`; o backend acessa o
banco pelo host `database`.

## Estrutura de pastas

```
captus/
├── backend/
│   ├── app/
│   │   ├── main.py        # camada de API (endpoints FastAPI)
│   │   ├── models.py      # schemas Pydantic (validação)
│   │   └── database.py    # camada de persistência (PostgreSQL + fallback)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app.py             # aplicação Streamlit
│   ├── Dockerfile
│   └── requirements.txt
├── database/
│   ├── create_tables.sql       # esquema relacional (PK, FK, UNIQUE, CHECK, índices)
│   └── consultas_negocio.sql   # consultas analíticas (SELECT, GROUP BY, JOIN)
├── docker-compose.yml
├── .env.example
└── README.md
```

## Como executar

### Com Docker (recomendado)

```bash
# na raiz do projeto
docker compose up --build
```

- Frontend: http://localhost:8501
- Backend (Swagger): http://localhost:8000/docs
- Backend (ReDoc): http://localhost:8000/redoc
- Banco: localhost:5432 (user `user` / senha `password` / db `postgres`)

O schema `create_tables.sql` é aplicado automaticamente na primeira subida do
container do banco.

### Execução local sem Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (em outro terminal)
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run app.py
```

Sem PostgreSQL acessível, o backend usa automaticamente um repositório em
memória (fallback), sinalizado em `GET /status`.

## Banco de dados (DBeaver)

Parâmetros de conexão (Aula 7):

| Parâmetro | Valor       |
|-----------|-------------|
| Host      | localhost   |
| Porta     | 5432        |
| Database  | postgres    |
| Usuário   | user        |
| Senha     | password    |

## Variáveis de ambiente

Veja `.env.example`. As credenciais do banco são injetadas via variáveis de
ambiente, mantendo segurança e portabilidade entre ambientes local e nuvem.
