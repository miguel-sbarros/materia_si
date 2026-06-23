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

## 6.5 Fluxos da camada CRUD: leads, funil e matrícula

Esta subseção descreve, de forma verbal e detalhada, os principais fluxos lógicos da camada que conecta a interface ao banco de dados persistente. No Captus essa camada não é um conjunto solto de operações de criar, ler, atualizar e apagar registros: ela carrega as regras de negócio do processo comercial de venda de cursos. Cadastrar um lead, mover um card no funil e matricular um aluno são ações que, por baixo, disparam várias escritas coordenadas (o registro principal, o histórico e os vínculos entre tabelas), tudo dentro de uma mesma transação. O objetivo aqui é explicar essas mecânicas uma a uma, sempre apoiado no código real que está no diretório `app/services/` do backend.

Antes de entrar em cada fluxo, vale fixar o padrão arquitetural que se repete em todos eles, porque ele explica a forma de cada função que vem a seguir. A camada é organizada em três degraus: o roteador (em `app/api/routes/`), o serviço (em `app/services/`) e os modelos ORM (em `app/models/`). O roteador é fino de propósito: ele só recebe a requisição HTTP, valida o corpo contra um schema Pydantic, chama o serviço correspondente e devolve a resposta. Toda a regra de negócio (deduplicação, controle de vagas, transições do funil, escrita do histórico) vive no serviço. Os serviços, por sua vez, sinalizam violações de regra de duas maneiras: ou levantam diretamente uma `HTTPException` (quando o serviço já está acoplado ao HTTP, como em `leads.py` e `deals.py`), ou levantam um `ValueError` com mensagem em português, deixando para o roteador a tradução desse erro no código HTTP certo (caminho usado em `catalog.py`, `course_modules.py` e `enrollments.py`). A regra de tradução é simples e consistente: mensagem com "não encontrado" vira 404, conflito de unicidade ("já existe", "já matriculado") vira 409, e violação de regra de processo (turma lotada, motivo de perda ausente, estágio inválido) vira 422.

### Cadastro de lead (REQF01): deduplicação, deal inicial e primeiro evento

O cadastro de um lead é o ponto de entrada do funil. A função `create_lead`, em `app/services/leads.py`, faz três coisas numa única transação: cria o lead, abre o primeiro deal dele numa turma e grava o primeiro evento de histórico desse deal. A ordem importa, porque cada passo depende do `id` gerado no passo anterior.

O primeiro cuidado é a deduplicação de e-mail, que atende a exigência da REQF01 de não cadastrar o mesmo lead duas vezes. Antes de qualquer escrita, o serviço consulta se já existe um lead com aquele e-mail e, se existir, levanta um conflito (409):

```python
# app/services/leads.py
if payload.email:
    if db.scalar(select(Lead).where(Lead.email == payload.email)) is not None:
        raise HTTPException(status_code=409, detail="Já existe um lead com este email")
```

Essa checagem no nível da aplicação é a primeira linha de defesa, voltada para dar uma mensagem clara ao usuário. A garantia de verdade, porém, está no banco: o modelo `Lead` (em `app/models/lead.py`) declara um índice único parcial chamado `uq_leads_email_present`, definido sobre a coluna `email` apenas quando ela não é nula (`postgresql_where=text("email IS NOT NULL")`). Isso resolve um detalhe importante do domínio: leads importados de conversas de WhatsApp muitas vezes não têm e-mail, então vários registros podem ter `email` nulo ao mesmo tempo (o índice parcial ignora os nulos), mas dois leads jamais podem compartilhar o mesmo e-mail preenchido. O índice parcial é exatamente o que permite as duas coisas conviverem.

Confirmado que não há duplicidade, o serviço busca a turma escolhida (404 se ela não existir) e descobre quem é o vendedor corrente. Como a autenticação foi deliberadamente adiada neste ciclo, o "usuário corrente" é resolvido de forma implícita: a função auxiliar `_current_seller` simplesmente pega o primeiro usuário com papel de vendedor cadastrado (a Dra. Ana Costa, do seed). Esse vendedor vira o responsável (`assignee_id`) do lead e o autor dos eventos de histórico.

Com isso, a função cria três registros em sequência, intercalando `db.flush()` para obter os identificadores: primeiro o `Lead`; depois um `Deal` apontando para a turma, já posicionado na coluna inicial do funil (`stage=Novo`, `status=open`); e por fim um `DealEvent` que marca o nascimento do deal, com motivo "Lead criado". Só ao final é que vem o `db.commit()`, de modo que ou tudo é gravado, ou nada é. O retorno é um `DealCard`, o mesmo formato que o quadro Kanban consome, então o card já aparece pronto na coluna "Novo" assim que o lead é cadastrado. Vale notar que o histórico (REQF02) começa a ser escrito aqui, no cadastro, e não só nas movimentações posteriores: o primeiro evento da vida de um deal é a sua própria criação.

### Pipeline e funil (REQF02): mapeamento de coluna para (stage, status) e histórico

O quadro Kanban da interface mostra colunas planas, como o vendedor espera ver: Novo, Contatado, Negociando, Aprovado, Matriculado e Perdido. O modelo de dados, porém, não guarda uma única coluna: ele separa dois campos no deal, o `stage` (posição no funil) e o `status` (estado terminal: aberto, ganho ou perdido). Essa separação é uma decisão de projeto importante, porque "Matriculado" e "Perdido" não são posições do funil, são desfechos. Toda a tradução entre o conceito de coluna da tela e o par de campos do banco vive em `app/services/deals.py`, em duas funções complementares.

A leitura (banco para tela) é feita por `card_column`, que decide qual coluna exibir a partir do status: se o deal foi ganho, mostra "Matriculado"; se foi perdido, mostra "Perdido"; caso contrário, mostra o próprio `stage` (que é uma das colunas abertas).

A escrita (tela para banco) é feita por `move_deal`, que recebe a coluna de destino e a converte de volta nos campos de domínio. As colunas abertas (Novo, Contatado, Negociando, Aprovado) viram `stage` igual à coluna com `status=open`; "Matriculado" vira `status=won`; e "Perdido" vira `status=lost`, mas só depois de exigir um motivo. O trecho central é este:

```python
# app/services/deals.py
if column in OPEN_COLUMNS:
    deal.stage = DealStage(column)
    deal.status = DealStatus.OPEN
    deal.lost_reason = None
elif column == MATRICULADO:
    deal.status = DealStatus.WON
    deal.lost_reason = None
else:  # PERDIDO
    if not (move.lost_reason and move.lost_reason.strip()):
        raise HTTPException(
            status_code=422, detail="lost_reason é obrigatório para mover a Perdido"
        )
    deal.status = DealStatus.LOST
    deal.lost_reason = move.lost_reason.strip()
```

A regra de que mover para "Perdido" exige um motivo é uma regra de processo comercial, não só uma validação técnica: a empresa quer entender por que perde alunos. Por isso, se o motivo vier vazio, a operação é recusada com 422 e nada é gravado. Repare também que, ao reabrir um deal (voltar para uma coluna aberta) ou ao matriculá-lo, o `lost_reason` é zerado, evitando que um motivo de perda antigo fique pendurado num deal que voltou a estar em jogo.

O segundo pilar da REQF02 é o histórico. Toda transição, sem exceção, grava um `DealEvent` antes do commit, e esse evento registra de onde veio e para onde foi, tanto em `stage` quanto em `status`, além do motivo (quando é uma perda) e do autor. A função guarda o `from_stage`/`from_status` logo no começo, antes de alterar o deal, justamente para conseguir registrar o "antes" e o "depois". Assim, a linha do tempo de cada deal fica reconstituível: dá para saber quando ele entrou em cada coluna, quando foi ganho ou perdido e por quê.

A tabela abaixo resume o mapeamento completo entre a coluna do quadro e o par (stage, status):

| Coluna no quadro (UI) | stage gravado | status gravado | Observações |
|---|---|---|---|
| Novo | Novo | open | coluna inicial; também atribuída no cadastro do lead |
| Contatado | Contatado | open | |
| Negociando | Negociando | open | |
| Aprovado | Aprovado | open | última coluna aberta antes do desfecho |
| Matriculado | (mantém o stage atual) | won | desfecho de ganho; integra-se à matrícula (REQF06) |
| Perdido | (mantém o stage atual) | lost | exige `lost_reason`; sem motivo retorna 422 |

Vale registrar que existem outros dois caminhos de escrita de deals em `deals.py`, usados fora do arrasto manual no quadro. O `create_deal_for_lead` cria um deal aberto para um lead que já existe, numa turma e estágio escolhidos (cenário do lead que nasceu de uma importação de conversa e depois é posicionado no funil); ele aceita apenas estágios abertos e bloqueia a duplicidade de deal na mesma turma com 409. Já o `create_closed_deal` cria um deal que já nasce fechado (ganho ou perdido), usado na carga histórica de dados (cold start), quando a turma já aconteceu; ele é idempotente sobre o par (lead, turma), ou seja, se já houver um deal para aquela combinação, devolve o existente em vez de duplicar, respeitando a restrição `UNIQUE(lead_id, cohort_id)`.

### Matrícula e vagas (REQF06): efetivar o aluno e controlar a lotação

A matrícula é o ponto em que o processo comercial encontra a operação do curso. Matricular um lead numa turma não é só marcar um campo: é a fonte da verdade de quem efetivamente está naquela turma, e, ao mesmo tempo, precisa refletir no funil, levando o deal correspondente para o desfecho de ganho. Tudo isso vive em `app/services/enrollments.py`, na função `enroll_lead`, que coordena três preocupações: o controle de vagas, a criação da matrícula e a transição do deal.

O controle de vagas segue uma regra direta: o número de vagas disponíveis é a capacidade da turma menos o número de matrículas ativas. Só matrículas com status `active` contam vaga; matrículas canceladas não ocupam lugar. Antes de criar qualquer coisa, o serviço conta as matrículas ativas e, se elas já alcançaram a capacidade, bloqueia a operação:

```python
# app/services/enrollments.py
if cohort.capacity is not None and _active_count(db, cohort_id) >= cohort.capacity:
    raise ValueError("Turma lotada")
```

Esse `ValueError` é traduzido pelo roteador para um 422, comunicando ao usuário que a turma está lotada. A checagem só acontece quando a turma tem capacidade definida; turmas sem capacidade declarada (`capacity` nulo) não impõem limite. Passada a checagem de vaga, o serviço cria a `Enrollment` com status `active` e tenta o `db.flush()`. Aqui entra uma segunda barreira, agora no nível do banco: o modelo `Enrollment` (em `app/models/enrollment.py`) tem a restrição `UNIQUE(lead_id, cohort_id)`, então, se o mesmo lead já estiver matriculado naquela turma, o flush viola a unicidade, a transação é desfeita e o serviço levanta um erro que o roteador traduz para 409. É a mesma filosofia do cadastro de lead: uma checagem amigável quando possível, e uma garantia dura no banco para fechar a porta de uma vez.

Criada a matrícula, falta amarrá-la ao funil. Isso é feito pela função auxiliar `_win_deal`, que busca o deal daquele lead naquela turma e o leva para ganho. Há dois caminhos. Se já existe um deal aberto, ele recebe `status=won`, tem o eventual `lost_reason` zerado e ganha um `DealEvent` registrando a transição com motivo "Matriculado". Se não existe deal nenhum (situação possível quando alguém é matriculado diretamente, sem ter passado pelo funil), o serviço reaproveita o `create_closed_deal` de `deals.py` para criar um deal já ganho, com o histórico correspondente. Nos dois casos, o resultado é um deal em estado de ganho, que a leitura do quadro vai exibir na coluna "Matriculado". Por fim, o `enrollment.deal_id` é preenchido com o id desse deal, materializando o vínculo entre a matrícula e o deal, e só então vem o `db.commit()`. Esse vínculo é o que permite, no cancelamento, saber exatamente qual deal reverter.

O cancelamento, em `cancel_enrollment`, é o espelho da matrícula e é o que efetivamente libera a vaga. Ele localiza a matrícula ativa do lead naquela turma (404 se não houver) e muda seu status para `cancelled`. Como o controle de vagas conta apenas matrículas ativas, mudar o status para cancelado já devolve a vaga ao bolo disponível, sem precisar apagar registro nenhum (o histórico da matrícula fica preservado). Em seguida, se a matrícula estava vinculada a um deal ganho, o cancelamento reverte esse deal para o funil aberto, colocando-o de volta em `status=open` e `stage=Negociando`, e grava um `DealEvent` com motivo "Matrícula cancelada". Ou seja, o lead volta a aparecer no quadro como uma negociação em aberto, pronto para ser retomado. Há ainda a função de leitura `cohort_enrollments`, que monta o resumo de ocupação de uma turma (capacidade, total de ativos e vagas disponíveis), aplicando a mesma conta de capacidade menos matrículas ativas para o campo `available`.

O diagrama a seguir resume o caminho feliz e os pontos de bloqueio do fluxo de matrícula, do momento em que o usuário escolhe o lead e a turma até o deal ficar na coluna "Matriculado".

![Figura 6. Fluxo de matrícula, da escolha do lead ao deal na coluna Matriculado.](relatorio_ciclo2/diagramas/matricula_fluxo.png)

### Catálogo e conteúdo do curso: cursos, turmas e a ementa por módulos

A camada de catálogo cuida dos dados de referência que sustentam todo o resto: os cursos e suas turmas. Ela está em `app/services/catalog.py` e é o exemplo mais puro do padrão de serviço por `ValueError`. A leitura é feita por `list_courses`, que traz os cursos com suas turmas já carregadas (usando `selectinload` para evitar consultas repetidas). A escrita cobre criar e editar cursos e turmas, sem operação de exclusão. Em `create_course` e `update_course`, a regra de negócio relevante é o nome único do curso: como essa unicidade é garantida no banco, o serviço deixa o `db.commit()` tentar, captura o `IntegrityError`, desfaz a transação e o converte num `ValueError` "Curso já existe", que o roteador traduz para 409. Já `create_cohort` e `update_cohort` validam a existência da entidade pai (o curso, no caso da criação de turma) e levantam "não encontrado" quando ela falta, virando 404 no roteador. As edições usam `model_dump(exclude_unset=True)`, o que significa que só os campos efetivamente enviados na requisição são alterados, deixando os demais intactos (atualização parcial).

O conteúdo do curso, isto é, a ementa, é tratado num serviço próprio, `app/services/course_modules.py`, porque a ementa é editável por módulos no banco. Cada módulo é uma linha (`CourseModule`) com título, conteúdo, posição e carga, ligada a um curso. O serviço oferece o CRUD completo dessas linhas: listar (ordenado por posição), criar, atualizar e, neste caso, também apagar. Ele segue o mesmo padrão: valida o curso ou o módulo e levanta "não encontrado" quando falta, deixando o roteador converter para 404.

A leitura consolidada da ementa acontece na rota `GET /courses/{course_id}/ementa`, em `app/api/routes/catalog.py`, e ela tem uma lógica de fallback que vale destacar. Se o curso já tem módulos cadastrados no banco, a ementa (`syllabus`) é montada a partir desses módulos. Se ainda não tem nenhum módulo, a rota cai para uma extração de bootstrap a partir de um arquivo de playbook, garantindo que a tela nunca apareça vazia mesmo antes de o conteúdo ter sido digitado no sistema. Outro ponto que diferencia as rotas de módulos das demais é o uso de `BackgroundTasks`: sempre que um módulo é criado, editado ou apagado, o roteador agenda em segundo plano a reingestão daquele curso na base de conhecimento usada pela IA (`reingest_course_bg`). Assim, a edição da ementa responde rápido ao usuário, e o reprocessamento do material para o copiloto acontece de forma assíncrona, sem travar a requisição.

### O padrão que costura tudo

Olhando os quatro fluxos em conjunto, fica visível a mesma estrutura se repetindo, e é ela que dá previsibilidade ao sistema. O roteador permanece fino: recebe, valida o schema, delega e responde. O serviço concentra a regra de negócio e é o dono do acesso ao banco e da transação, sempre fechando com um `db.commit()` único ao final, de modo que operações compostas (lead mais deal mais evento; matrícula mais deal mais evento mais vínculo) sejam atômicas. As violações de regra viram erros tipados, traduzidos de forma consistente para os códigos HTTP: 404 para entidade inexistente, 409 para conflito de unicidade e 422 para regra de processo violada. E, por fim, o que precisa de garantia forte (e-mail único de lead, par único lead-turma na matrícula e no deal, nome único de curso) é protegido por restrições no próprio banco, com a checagem na aplicação servindo de camada amigável por cima. É esse conjunto de escolhas que faz a camada CRUD do Captus ser, de fato, a camada onde o processo comercial vira dado persistente e auditável.

## 6.6 Importação de conversas e análise comportamental por IA

Esta subseção detalha dois fluxos lógicos que andam juntos no Captus: a importação de conversas exportadas do WhatsApp e a análise comportamental do lead feita com um modelo de linguagem (LLM). O primeiro fluxo traz para dentro do sistema o histórico bruto de uma negociação que aconteceu fora dele, no aplicativo de mensagens. O segundo lê esse histórico e o transforma em um perfil estruturado do lead: quem é a pessoa, quais são suas dores e desejos, em que estágio da conversa de vendas ela está, e qual a chance de fechar. A ideia central é que o vendedor não precisa mais reler conversas longas para lembrar do contexto: o sistema decodifica a conversa por ele.

### Por que importar em vez de integrar direto com a Meta

A forma "oficial" de um sistema externo conversar com o WhatsApp é a WhatsApp Business API da Meta. Ela é robusta, porém burocrática: exige conta verificada, aprovação de número, provedor homologado (BSP) e um processo de cadastro que leva tempo. Para um projeto que precisa funcionar agora, com conversas que já existem, esse caminho é pesado demais. A solução adotada é mais simples e direta: o próprio WhatsApp permite exportar uma conversa como um arquivo (o `_chat.txt`, normalmente dentro de um `.zip` com as mídias). O Captus lê esse arquivo e reconstrói a conversa no banco. Trata-se de uma versão 0 (v0) da futura integração via API: o formato de dados é o mesmo (conversas e mensagens), então quando a integração oficial for ligada, a camada de armazenamento e de análise já estará pronta para recebê-la.

### O parser: como o arquivo exportado vira mensagens

Cada linha de uma exportação do WhatsApp segue um formato fixo: um timestamp entre colchetes, o nome do remetente, e o corpo da mensagem. Por exemplo: `[30/10/2025, 14:03:21] ~Dr. Paulo: Quero saber sobre a imersão`. O detalhe que organiza tudo é o til (`~`): no formato exportado, o remetente que é um contato externo (ou seja, o lead) aparece com til na frente do nome, enquanto as mensagens do dono da conta (o vendedor) vêm sem til. O parser usa esse sinal para decidir de quem é cada mensagem, gravando um booleano `sent` onde `True` significa vendedor e `False` significa lead.

O parsing (em `app/services/whatsapp_parser.py`) acontece em duas etapas. Primeiro, o texto é fatiado em blocos usando o timestamp como fronteira: toda vez que aparece um carimbo de data/hora, começa uma mensagem nova. Isso é importante porque uma única mensagem pode ter várias linhas (alguém aperta Enter no meio do texto), e o fatiamento por fronteira de timestamp mantém esse texto multi-linha junto, como um bloco só. Depois, cada bloco é casado contra uma expressão regular que separa timestamp, remetente e corpo:

```python
# app/services/whatsapp_parser.py
_TS_BOUNDARY = re.compile(r"\[(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\]")
_MSG = re.compile(r"\[(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}:\d{2})\] ([^:]+): (.+)", re.DOTALL)
...
sender = sender.strip()
sent = not sender.startswith("~")  # vendedor não tem til
```

Ao longo do caminho, o parser faz uma limpeza que evita lixo no banco. Mensagens de sistema em português (o aviso de criptografia de ponta a ponta, o aviso de conversa iniciada por anúncio no Facebook) são filtradas. Caracteres invisíveis de marcação de direção de texto (o U+200E que o WhatsApp insere) são removidos. Mídias (áudios, imagens, documentos, anexos ocultos) não têm conteúdo textual aproveitável, então viram um marcador legível em português no lugar do texto, como `[áudio]`, `[imagem]` ou `[documento]`. Cada mensagem que sobra recebe um número de ordem (`sequence`), contíguo e começando em zero, atribuído depois da filtragem. Esse número é a peça-chave da idempotência, como será explicado adiante. Por fim, dois auxiliares cuidam de casos de borda: `infer_lead_name` descobre o nome do lead pegando o remetente com til mais frequente (sem o til), e `phone_from_filename` extrai o telefone do nome de arquivos no padrão `WhatsApp Chat - <telefone>.zip`. Se o arquivo estiver vazio ou não tiver nenhum timestamp no formato esperado, o parser levanta erros tipados (`EmptyChatError` e `NotWhatsAppExportError`), que o sistema converte em uma resposta de erro clara.

### Da rota ao banco: conversas, mensagens e idempotência

O fluxo de importação é orquestrado por uma rota fina (`POST /imports`, em `app/api/routes/imports.py`) que delega o trabalho ao serviço. A rota recebe o upload, e se for um `.zip` ela abre o arquivo e procura o membro `_chat.txt` dentro dele; se for um `.txt` direto, apenas decodifica o conteúdo em UTF-8. Em seguida, o serviço `import_chat` (em `app/services/imports.py`) resolve para qual lead a conversa pertence: pode ser um lead já existente (informado por id), um lead identificado pelo telefone do nome do arquivo (com deduplicação por `external_user_id`), ou um lead novo criado a partir de um nome. Resolvido o lead, o serviço garante a existência de uma conversa para aquele lead.

No banco (modelos em `app/models/conversation.py`), há duas tabelas. A tabela `conversations` guarda uma conversa por lead e por canal, garantida por uma restrição de unicidade `UNIQUE(lead_id, channel)`: importar o mesmo lead duas vezes não cria duas conversas, apenas reaproveita a que já existe. A tabela `messages` guarda cada mensagem com seu texto, o booleano `sent`, o timestamp e a tal `sequence`. A restrição que torna toda a importação segura para repetir é a unicidade da sequência dentro da conversa:

```python
# app/models/conversation.py
UniqueConstraint("conversation_id", "sequence", name="uq_messages_conversation_sequence")
```

É isso que torna a importação idempotente, ou seja, segura para rodar de novo sem efeitos colaterais. Quando o mesmo arquivo é importado uma segunda vez, o serviço primeiro lê quais números de sequência já existem na conversa e simplesmente pula esses ao inserir, contando apenas as mensagens realmente novas. Reimportar a mesma conversa não duplica nada; reimportar uma conversa que cresceu (ganhou mensagens novas no fim) acrescenta só o trecho novo. Esse mesmo desenho serve à carga em lote: o script `scripts/populate_chats.py` percorre uma pasta inteira de exportações reais e, como cada lead é gravado individualmente, um lote interrompido no meio pode ser retomado de onde parou sem reprocessar o que já entrou. Esse script foi usado na carga de cold-start do corpus real (a turma Imersão Out/25), importando centenas de leads de uma vez, cada um já com sua conversa, seu perfil de IA e o desfecho comercial classificado.

### Como a análise é disparada

A análise comportamental nunca trava a importação, e isso é uma decisão de projeto. Existem três formas de dispará-la. A primeira é automática, logo após uma importação bem-sucedida (ou após o envio de uma mensagem manual): se a conversa passar de três mensagens, o sistema agenda a análise. O limiar de três mensagens evita gastar uma chamada de LLM em conversas vazias ou que mal começaram, onde não há contexto suficiente para extrair um perfil. Esse gate é uma função simples e testável:

```python
# app/services/analysis.py
AUTO_ANALYZE_MIN_MESSAGES = 3

def should_auto_analyze(message_count: int) -> bool:
    return message_count > AUTO_ANALYZE_MIN_MESSAGES
```

A segunda forma é manual, sob demanda, através do endpoint `POST /leads/{id}/analyze`. Ele roda a análise de forma síncrona e devolve o perfil atualizado na hora, útil quando o vendedor quer forçar um reprocessamento depois de uma conversa nova. A terceira forma é o pano de fundo de tudo: a análise automática roda como uma tarefa em segundo plano (`BackgroundTask` do FastAPI), executada por `run_analysis_bg`. Essa tarefa abre a sua própria sessão de banco (`SessionLocal`), separada da sessão do request que já foi respondido, e envolve a análise inteira em um tratamento de erro que registra a falha mas a engole. A consequência prática é que, se o LLM estiver fora do ar ou a análise falhar por qualquer motivo, a importação continua valendo: as mensagens já estão salvas, e só o perfil de IA fica faltando (podendo ser gerado depois pelo endpoint manual). A análise é um enriquecimento, não uma dependência do dado bruto.

```python
# app/services/analysis.py
def run_analysis_bg(lead_id: int) -> None:
    try:
        with SessionLocal() as db:
            analyze_lead(db, lead_id)
    except Exception:  # falha de análise não pode quebrar o import
        logger.exception("Falha na análise automática do lead %s", lead_id)
```

### A análise com LLM: por que duas chamadas em vez de uma

O coração da análise é a função `analyze_lead`. Ela carrega a conversa do lead, monta um transcrito legível (cada linha prefixada com `Lead:` ou `Vendedor:`), calcula as métricas deterministas e então conversa com o modelo de linguagem. O ponto mais importante do desenho é que a análise faz **duas** chamadas de saída estruturada, e não uma só. Saída estruturada significa que pedimos ao modelo que devolva os dados já no formato de um schema Pydantic conhecido (via `client.messages.parse(output_format=...)`), em vez de texto livre que precisaríamos depois interpretar à mão.

A razão de serem duas chamadas é uma lição aprendida na prática. A primeira tentativa usava um único schema grande, com cerca de quatorze campos somando texto, listas e enumerações. A API da Anthropic, ao preparar a saída estruturada, compila uma "gramática" que força o modelo a respeitar exatamente aquele formato, e um schema grande demais estourava o tempo desse compilador, retornando o erro `Grammar compilation timed out`. A correção não foi mudar a forma de chamar a API, e sim diminuir o tamanho de cada schema: dois schemas pequenos compilam rápido. Daí a regra adotada no projeto, registrada no próprio código: mantenha cada `output_format` enxuto (algo em torno de oito a dez campos) e prefira dividir em vez de empilhar muitos campos com enumerações em um schema único.

```python
# app/services/analysis.py: duas chamadas pequenas, não um schema único grande
entities: ExtractedEntities = parse_structured(
    model=settings.model_extraction, system=ANALYSIS_SYSTEM_PROMPT,
    messages=[{"role": "user", "content": user_content}],
    output_format=ExtractedEntities, max_tokens=1500,
)
assessment: LeadAssessment = parse_structured(
    model=settings.model_extraction, system=ANALYSIS_SYSTEM_PROMPT,
    messages=[{"role": "user", "content": user_content}],
    output_format=LeadAssessment, max_tokens=1500,
)
```

A primeira chamada usa o schema `ExtractedEntities` e cuida da **decodificação**: extrai os fatos objetivos que aparecem na fala do lead. São a especialidade (implantodontista, protesista, e assim por diante), o nível de experiência, a cidade/estado, o curso de interesse, e três listas centrais para vendas consultivas: as dores verbalizadas (problemas da prática clínica, como "dependo do laboratório"), os desejos expressos (o que o lead busca, como "quero autonomia") e as objeções de venda (barreiras à compra, como "achei caro" ou "vou pensar", que o prompt cuida de não confundir com dores). Há ainda um campo `comentarios` que reúne informações úteis variadas: equipamentos e softwares citados, termos técnicos e marcadores de contexto. Um detalhe técnico relevante para a gramática: esse schema não usa campos opcionais, porque uma união com `null` viraria um `anyOf` e incharia a gramática; em vez disso, ausência de evidência é representada por string vazia ou lista vazia, e o sistema normaliza essas strings vazias para `None` na hora de salvar.

A segunda chamada usa o schema `LeadAssessment` e faz a **avaliação** estratégica do diálogo. Ela classifica o lead em uma das quatro personas da MR Digital (Iniciado Digital, Especialista Analógico, Recém-Especializado, Focado em Prótese, ou indeterminado quando não há sinais suficientes), com uma confiança de 0 a 1 e uma justificativa. Define o estágio SPIN atual da conversa, que descreve a maturidade do diálogo de vendas seguindo a metodologia SPIN: Situação, Problema, Implicação e Necessidade. É importante não confundir esse estágio SPIN, que é uma propriedade da conversa, com o estágio comercial do funil (Kanban), que é uma propriedade do negócio (deal); são dois conceitos distintos que o sistema nunca mistura. O SPIN é sempre uma enumeração fixa (`SPINStage`), nunca texto livre, decisão de produto para garantir consistência. O schema também devolve um `lead_score` de 0 a 100, estimando a maturidade e a probabilidade de conversão, e um resumo conciso da situação. O prompt que guia as duas chamadas (em `app/prompts/analysis.py`) é compartilhado e traz, além das definições, exemplos curtos de classificação SPIN (por exemplo, "Quero informações sobre a imersão" indica estágio de situação, enquanto "Perco horas de cadeira e a confiança do paciente fica abalada" indica implicação), o que ajuda o modelo a calibrar o julgamento.

A análise ainda é "update-aware": quando o lead já tem um perfil, o perfil atual é incluído no conteúdo enviado ao modelo, com a instrução de revisar apenas o que mudou. Assim, reprocessar uma conversa que cresceu refina o perfil em vez de jogá-lo fora.

### As métricas deterministas da conversa

Nem tudo precisa de inteligência artificial. Algumas informações valiosas podem ser calculadas diretamente dos timestamps, sem custo de LLM e sem margem de erro de interpretação. É o que faz `compute_chat_metrics`, uma função pura (sem banco e sem modelo) que recebe as mensagens ordenadas e mede o ritmo da conversa. A ideia é olhar para cada "virada" de remetente, ou seja, cada vez que quem fala muda de lado. Quando o lead manda uma mensagem e em seguida o vendedor responde, o intervalo entre as duas é a latência do vendedor; quando o vendedor fala e o lead responde depois, o intervalo é a latência do lead. Dessas listas de intervalos, a função tira a mediana (mais robusta a valores extremos do que a média), além de registrar a latência da primeira resposta do vendedor.

A função também detecta abandono de forma simples e confiável: se a última mensagem da conversa foi do vendedor, significa que o lead parou de responder, e a conversa é marcada como abandonada (`is_abandoned`). Esse sinal determinista tem um papel curioso na análise de IA: o modelo sempre devolve um "estágio SPIN de abandono" (onde a conversa esfriou), mas esse valor só é de fato persistido quando a métrica determinista confirma que houve abandono. Em outras palavras, é o cálculo objetivo dos timestamps, e não o LLM, que decide se a conversa esfriou; o LLM só rotula em que ponto da venda isso aconteceu. Vale notar uma degradação graciosa: importações sem timestamp simplesmente não geram latências (os pares sem horário são ignorados), então as métricas ficam nulas sem quebrar nada.

### Persistência no LeadProfile e uso posterior

Todo o resultado é consolidado em uma única tabela, `lead_profiles` (modelo em `app/models/lead_profile.py`), que tem relação um para um com o lead, garantida por `UNIQUE(lead_id)`. A gravação é um upsert: existe um único registro de perfil por lead, e cada nova análise atualiza a mesma linha em vez de criar uma nova. A função `analyze_lead` busca o perfil existente (ou cria um novo), aplica sobre ele as entidades, a avaliação e as métricas, e dá commit. As listas (dores, desejos, objeções, comentários) e o objeto bruto da resposta são guardados como JSONB; a persona é gravada já com seu rótulo de exibição em português; o estágio SPIN, que é enumeração no schema, é gravado como texto.

A tabela abaixo resume os campos do `LeadProfile` agrupados por origem, deixando claro o que vem do LLM e o que é calculado deterministicamente:

| Origem | Campos | Como é produzido |
|---|---|---|
| Entidades (`ExtractedEntities`, 1ª chamada LLM) | `especialidade`, `experiencia`, `cidade_estado`, `course_interest`, `dores_verbalizadas`, `desejos_expressos`, `objecoes`, `comentarios` | Extração estruturada das falas do lead pelo modelo |
| Avaliação (`LeadAssessment`, 2ª chamada LLM) | `matched_persona`, `persona_confidence`, `persona_reasoning`, `current_spin_stage`, `abandon_spin_stage`, `lead_score`, `summary` | Classificação e julgamento estratégico pelo modelo |
| Métricas (`compute_chat_metrics`, sem LLM) | `median_seller_latency_seconds`, `median_lead_latency_seconds`, `first_response_latency_seconds`, `last_message_sent`, `is_abandoned` | Cálculo determinista a partir dos timestamps |
| Metadados | `model_used`, `raw`, `created_at`, `updated_at` | Rastreabilidade da análise (modelo usado e resposta bruta) |

Depois de gravado, o perfil é a fonte única de verdade para várias telas. O endpoint de detalhe do lead embute o perfil, e a página do lead (LeadPage) renderiza a seção "Análise da conversa (IA)" com o resumo, o score, o estágio SPIN traduzido, a especialidade, a experiência, as latências, a marcação de abandono e os chips de dores, desejos, objeções e comentários, além de tingir o avatar conforme a persona. O painel direito da página de Conversas mostra uma versão compacta (persona, score, SPIN, dores e desejos). E, num nível mais alto, a página de Analytics agrega esses perfis individuais em métricas do conjunto: a Analytics é construída sobre as análises por lead, mas não é o `LeadProfile` em si, são camadas distintas. Assim, o caminho completo fecha o ciclo: uma conversa de WhatsApp exportada entra como texto bruto, vira mensagens estruturadas, e termina como um perfil que o vendedor pode ler em segundos.

### Diagrama do fluxo

![Figura 7. Fluxo de importação e análise comportamental.](relatorio_ciclo2/diagramas/analise_fluxo.png)

## 6.7 Copiloto: atendimento assistido por IA (RAG)

O Copiloto é a quarta funcionalidade do Captus e, de certa forma, o ponto onde tudo o que o sistema já sabe sobre um lead vira ação prática. A ideia central, que vale repetir porque muda completamente o desenho do produto, é esta: o Copiloto NÃO é um robô que conversa com o lead no lugar do vendedor. Ele não envia mensagens sozinho, não responde automaticamente no WhatsApp e não toma decisões comerciais por ninguém. O Copiloto é um consultor que fica do lado do vendedor, lê o contexto, busca o material certo da empresa e devolve uma recomendação para que o vendedor, esse sim, decida o próximo passo e aperte o botão de enviar. O próprio prompt do sistema deixa isso explícito logo na primeira linha: "Seu papel é ACONSELHAR O VENDEDOR: você NÃO conversa com o lead nem envia mensagens automaticamente."

Essa escolha tem uma consequência direta no comportamento padrão. Por padrão, o agente responde em prosa, analisando o lead e respondendo perguntas, do mesmo jeito que um colega de equipe mais experiente faria numa conversa de bastidor. Ele só monta sugestões de mensagem prontas quando o vendedor pede de forma explícita ("como respondo?", "me dá sugestões"). Sem esse pedido, ele continua sendo um consultor que orienta, não um gerador de textos.

### O que o Copiloto faz e como o vendedor conversa com ele

A interface do Copiloto (página `Copiloto.jsx`, com a lógica de estado em `useCopilot.js`) lembra um chat moderno, com uma barra lateral de sessões à esquerda e a conversa à direita. O vendedor digita num campo único e tem três gestos possíveis dentro desse mesmo campo: escrever uma pergunta normal, digitar "@" para anexar um lead, ou digitar "/" para disparar um comando. A detecção de qual gesto está em jogo é feita por expressões regulares aplicadas ao final do que está sendo digitado, em `useCopilot.js`:

```js
const slash = val.match(/^\/([\w-]*)$/)        // abre o menu de comandos
const m = val.match(/(^|\s)@([^\s@]*)$/u)       // abre o seletor de leads
```

Cada turno de conversa é persistido no banco. Existem duas tabelas próprias do Copiloto, `CopilotSession` (a sessão, que aparece na barra lateral) e `CopilotMessage` (cada mensagem trocada), e é importante notar que elas são distintas das mensagens de WhatsApp entre lead e vendedor. Uma coisa é o histórico real da conversa com o cliente, outra coisa é o histórico de conselhos que o vendedor pediu ao Copiloto. Cada sessão fica normalmente ligada a um lead, de modo que o vendedor pode voltar depois e reabrir a conversa de aconselhamento sobre aquele cliente específico.

### Fluxo de RAG: buscar o trecho certo por similaridade de sentido

RAG quer dizer "geração aumentada por recuperação". Na prática, antes de o modelo escrever qualquer coisa sobre os dados da empresa, ele busca na base de conhecimento da MR os trechos mais parecidos com o que está em jogo, e responde fundamentado nesses trechos, em vez de responder "de memória". Isso evita que o agente invente cursos, preços ou argumentos que não existem.

A peça que faz essa busca é a função `retrieve`, em `app/services/rag.py`. O caminho é o seguinte. Primeiro, o texto da consulta é transformado num vetor de números (um "embedding") que representa o sentido daquele texto. Depois, o banco PostgreSQL, com a extensão pgvector, compara esse vetor com os vetores de todos os trechos guardados, usando a distância de cosseno (o operador `<=>` do pgvector), e devolve os mais próximos. Distância de cosseno, de forma simples, é uma medida de "quão parecido em significado" um texto é de outro: quanto menor a distância, mais parecidos. A geração de embeddings (`embed_query` e `embed_texts`) é uma decisão consciente do projeto: ela usa a OpenAI (`text-embedding-3-small`, 1536 dimensões), enquanto toda a geração de texto continua na Anthropic (Claude).

As fontes desse conhecimento são variadas e ficam todas na tabela `knowledge_chunks`, cada uma com um campo `source` que diz de onde veio: o grafo legado da MR (`kb_graph`), o playbook em markdown com a filosofia e os scripts SPIN (`playbook`), e o conteúdo dos cursos (`course`, do qual falaremos mais adiante). Entre esses trechos há um tipo especial, os de rótulo `Script`, que carregam duas marcações extras: a persona a que se destinam (por exemplo, "Especialista Analógico") e o estágio SPIN da venda (Situação, Problema, Implicação, Necessidade).

É aqui que entra o que o projeto chama de "boost". Quando o Copiloto sabe a persona e o estágio SPIN do lead, ele passa essas duas informações para o `retrieve`, que então prioriza os scripts feitos exatamente para aquela combinação, elevando-os ao topo da lista, com a distância de cosseno servindo como critério de desempate. O trecho que implementa isso é curto e direto, em `app/services/rag.py`:

```python
boost = case(
    (
        (KnowledgeChunk.label == "Script")
        & (KnowledgeChunk.persona == persona)
        & (KnowledgeChunk.spin_stage == spin_stage),
        0,
    ),
    else_=1,
)
order_by.append(boost.asc())   # 0 sobe, 1 desce
order_by.append(distance.asc())  # cosseno como desempate
```

Na leitura simples: trechos do tipo Script que batem persona e estágio recebem valor 0 e vão para frente; todos os outros recebem 1 e ficam atrás; dentro de cada grupo, ordena-se pela proximidade de sentido. O resultado é que o vendedor recebe o argumento certo para o cliente certo, no momento certo da conversa. Sem persona ou sem estágio, o `retrieve` simplesmente devolve os trechos mais próximos por cosseno, sem priorização especial.

### O loop do agente com ferramentas (tool use)

O Copiloto é um agente, e não apenas uma única chamada ao modelo. Isso significa que o modelo pode pedir para usar ferramentas, receber o resultado e continuar raciocinando, repetindo esse ciclo até concluir a resposta. O motor desse ciclo é a função `run_agent`, em `app/services/llm/client.py`. Ela roda o loop manual de tool-use do SDK da Anthropic: enquanto o modelo sinaliza que quer uma ferramenta (`stop_reason == "tool_use"`), o código executa o que foi pedido, devolve o resultado e deixa o modelo seguir; quando o modelo encerra o turno, a resposta final é retornada.

As ferramentas são montadas em `app/services/copilot.py`, na função `_build_tools`. São seis no total, e vale descrevê-las porque elas definem o que o Copiloto consegue "saber" antes de aconselhar:

| Ferramenta | Para que serve |
|---|---|
| `search_knowledge(query, persona?, spin_stage?)` | Busca no RAG (playbook, dossiês de persona, scripts SPIN). É aqui que entra o boost por persona e estágio. |
| `get_cohorts_status(course_name?)` | Consulta o status real das turmas: datas, capacidade, situação e preço por vaga. |
| `get_course_ementa(course_name)` | Detalha um curso: resumo e grade curricular, a partir do conteúdo dos cursos. |
| `get_icp_stats()` | Estatísticas de ICP por persona: número de leads, taxa de conversão, dores e desejos agregados. |
| `get_funnel_analytics()` | Métricas do funil: conversão geral e por estágio, latências de resposta, taxa de abandono. |
| `suggest_messages(reasoning, paths)` | Ferramenta opcional. O agente só a chama quando o vendedor pede sugestões de mensagem; ela captura a análise e os 3 caminhos estratégicos. |

Um detalhe de robustez que merece nota: cada handler de ferramenta é à prova de exceção. Se algo der errado numa busca ou numa consulta ao banco, o handler devolve uma string de erro em vez de levantar uma exceção. Isso garante que o loop do agente sempre receba um resultado e consiga terminar, em vez de travar no meio. A definição de uma ferramenta, no código, junta a descrição em português (que orienta o modelo sobre quando usá-la) ao esquema de entrada:

```python
{
    "name": "search_knowledge",
    "description": (
        "Busca na base de conhecimento da MR (playbook, dossiês de persona e scripts "
        "SPIN)... Passe persona e spin_stage quando souber, para priorizar os scripts."
    ),
    "input_schema": SEARCH_KNOWLEDGE_SCHEMA,
}
```

Quando o turno termina, a função `chat` decide como guardar a resposta: se o agente chamou `suggest_messages`, a mensagem é persistida com `kind='advice'` (os caminhos estratégicos capturados); caso contrário, com `kind='text'` (a resposta conversacional em markdown). Essa distinção é o que a interface usa depois para escolher entre mostrar uma bolha de texto ou os cartões de sugestão.

### Os slash commands (o menu de "/")

Os slash commands são atalhos para tarefas analíticas que o vendedor faz com frequência. Ao digitar "/", abre-se um menu (`CommandMenu.jsx`) com os comandos disponíveis, e escolher um deles dispara um fluxo já preparado no backend. No código, cada comando vira uma instrução em português que orienta o agente a chamar a ferramenta certa, em `_COMMAND_INSTRUCTIONS` (arquivo `app/services/copilot.py`). Por exemplo, o `/analytics` instrui o agente a chamar `get_funnel_analytics` e resumir as taxas de conversão, as latências e a taxa de abandono. Os comandos têm precedência sobre o resto: quando há um comando, é a instrução dele que comanda o turno.

| Comando | O que dispara |
|---|---|
| `/icp` | Análise de ICP: chama `get_icp_stats` e resume personas, conversão por persona e top dores/desejos. |
| `/analytics` | Análise do funil: chama `get_funnel_analytics` e resume conversão, latências e abandono. |
| `/courses` | Portfólio de cursos: usa `get_course_ementa` e/ou `search_knowledge` e resume os cursos e suas ementas. |
| `/spin` | Metodologia SPIN: busca os scripts e técnicas SPIN no playbook e explica como aplicá-los. |

### Anexar um lead com "@" (injeção de contexto)

Quando o vendedor digita "@", abre-se um seletor de leads filtrável por nome (`MentionMenu`), e escolher um lead o anexa à sessão. Anexar não é um gesto cosmético: ele injeta, dentro do turno enviado ao agente, todo o contexto que o sistema já produziu sobre aquele lead. Isso inclui o perfil gerado pela análise de IA da etapa anterior (persona, dores verbalizadas, desejos, objeções, estágio SPIN, resumo) e também o histórico real da conversa de WhatsApp entre o lead e o vendedor. Essa montagem fica na função `build_copilot_content`, em `app/prompts/copilot.py`, que produz um bloco de contexto legível com cabeçalhos como "## LEAD ANEXADO" e "## CONVERSA (WhatsApp)".

Na prática, é isso que faz a diferença entre um conselho genérico e um conselho sob medida. Com o perfil em mãos, o agente sabe que está diante, por exemplo, de um Especialista Analógico com objeção de tempo, e que a conversa está no estágio de Implicação; com isso, ao chamar `search_knowledge`, ele passa persona e estágio e recebe, pelo boost, justamente os scripts pensados para esse caso. No frontend, o vínculo lead↔sessão é tratado como fixo: cada lead anexado corresponde a uma sessão, e trocar de lead numa sessão que já tem um lead leva a uma confirmação de "nova conversa", o que evita o dessincronismo entre o que aparece na tela e o que está vinculado no banco.

### A saída: rascunhos de resposta em tons e estratégias diferentes

Quando o vendedor pede sugestões de mensagem, o agente chama `suggest_messages` e devolve uma análise mais três caminhos estratégicos distintos. É importante a palavra "distintos": o prompt pede que sejam estratégias diferentes de abordagem (por exemplo, "ancorar na dor de previsibilidade", "gatilho de escassez da próxima turma", "prova social mais ROI"), e não apenas três variações de tom da mesma frase. Cada caminho traz um título curto, o racional (por que aquela abordagem faz sentido para aquele lead agora) e a mensagem de WhatsApp pronta, em português, escrita num tom consultivo e terminando com uma pergunta que ajude a avançar o funil.

Na tela, cada caminho vira um cartão (`DraftCard.jsx`) com dois botões: Copiar, que usa a área de transferência do navegador e dá um retorno visual rápido, e Enviar, que grava aquele texto no histórico de WhatsApp do lead anexado. Vale reforçar o ponto de partida: mesmo o botão Enviar grava no histórico do próprio sistema, não dispara nada automaticamente para o cliente. A interface inclusive lembra isso embaixo do campo: "As mensagens são sugestões, revise antes de enviar ao histórico do lead." O vendedor segue no controle, escolhe a estratégia, ajusta o texto se quiser e só então decide o que fazer.

### Conteúdo vivo: editar a ementa de um curso realimenta o Copiloto

Um aspecto elegante do desenho é que o conhecimento do Copiloto não fica congelado. Quando alguém edita o conteúdo de um curso no sistema (cria, altera ou exclui um módulo), o backend agenda automaticamente uma re-ingestão daquele curso no RAG, sem que ninguém precise rodar script algum. Isso acontece na rota de catálogo (`app/api/routes/catalog.py`), que dispara `reingest_course_bg` como tarefa em segundo plano após o CRUD de módulo.

A re-ingestão em si está em `app/services/course_rag.py`. A lógica é "apagar e reinserir" por curso: ela remove os trechos antigos daquele curso (identificados pelo prefixo `course:{course_id}#` no campo `node_ref`), monta um trecho por módulo, gera os embeddings com `rag.embed_texts` e grava de volta. Por trabalhar isolada por curso e por prefixo, a operação é idempotente (pode rodar de novo sem duplicar) e não toca nas outras fontes, como o grafo legado ou o playbook. E como a função de busca `retrieve` é agnóstica em relação à fonte, o efeito é direto: assim que a ementa atualizada é re-embedada, o Copiloto já passa a recuperar e citar o conteúdo novo, sem nenhuma mudança no código do agente. Por segurança, a tarefa engole e apenas registra qualquer erro de re-ingestão, justamente para que uma falha de embedding nunca derrube a edição do curso.

### Diagrama do turno de chat

O diagrama abaixo resume o caminho de um turno do Copiloto, da entrada do vendedor até os rascunhos ou a resposta em prosa. O fonte está em `relatorio_ciclo2/diagramas/copiloto_fluxo.mmd`.

![Figura 8. Fluxo de um turno de chat do Copiloto.](relatorio_ciclo2/diagramas/copiloto_fluxo.png)

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

A Figura 9 apresenta o modelo entidade-relacionamento completo. O núcleo comercial forma a espinha do sistema: um curso oferece várias turmas, cada lead é atribuído a um vendedor, e cada deal conecta um lead a uma turma. Toda transição de um deal é registrada em `deal_events`, o que materializa o histórico exigido pelo REQF02. O bloco de comunicação anexa a cada lead suas conversas e mensagens (REQF03) e um perfil 1 para 1 com a análise comportamental por IA (REQF08). O bloco de IA sustenta o Copiloto: `knowledge_chunks` guarda o corpus vetorizado para busca semântica, e as tabelas de sessão e mensagens do copiloto persistem o diálogo do agente.

![Figura 9. Modelo entidade-relacionamento do Captus, com 15 tabelas e a espinha centrada no negócio.](relatorio_ciclo2/diagramas/er_modelo.png)

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
