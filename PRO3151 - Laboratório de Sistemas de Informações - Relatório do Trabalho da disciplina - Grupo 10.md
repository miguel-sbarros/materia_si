# 

# **Trabalho da disciplina**

Profs. Drs. Mauro Spinola e Marcelo Pessôa. Monitores Caio Azevedo e Priscila Bayer

Versão 1.0 (28-04-2026)

Sumário

[**1 Caracterização do Projeto**](#caracterização-do-projeto)	**2**

[1.1 Identificação do Projeto](#identificação-do-projeto)	2

[1.2 Organização e Cliente](#organização-cliente)	2

[1.3 Problema Identificado](#problema-identificado)	2

[1.4 Objetivo do Software](#objetivo-do-software)	3

[1.5 Público-alvo/Usuários](#público-alvo/usuários)	3

[**2 Escopo do sistema**](#escopo-do-sistema)	**4**

[2.1 Escopo incluído](#escopo-incluído)	4

[2.2 Fora do escopo](#fora-do-escopo)	4

[**3 Requisitos do sistema**](#requisitos-do-sistema)	**5**

[3.1 Matriz geral de requisitos](#matriz-geral-de-requisitos)	5

[3.2 Requisitos funcionais](#requisitos-funcionais)	6

[3.3 Requisitos não funcionais](#requisitos-não-funcionais)	9

[**4 Prototipação da solução	1**](#heading=h.blscxkhvhuvf)**2**

[4.1 Objetivos do protótipo	1](#heading=h.tbtm6592kgkm)2

[4.2 Protótipo de baixa fidelidade	1](#heading=h.jg76nfuswgdv)2

[4.3 Protótipo de alta fidelidade ou funcional	1](#heading=h.mszvke82ox1x)8

[4.4 Aprendizados obtidos com o protótipo](#heading=h.326idh5yngnq)	20

[**5 Conclusão do Ciclo 1**](#heading=h.cfq95m7sebn)	**21**  



# 

1. # **Caracterização do Projeto** {#caracterização-do-projeto}

   1. ## ***Identificação do Projeto*** {#identificação-do-projeto}

Nome do Projeto: Captus \- Plataforma de CRM e Gestão de Turmas  
Grupo: 10  
Integrantes:

* Felipe Smaniotto Costa (16865335);  
* Henrique Guaré Romano (6610082);  
* Murilo Dib Abud (16893751);  
* Ulisses Calixto Aquino Fontoura (16903160);  
* Miguel Francisco Soares Barros (⁠15586304).

Data da entrega: 09/06  
Versão do documento: 2.0

2. ## ***Organização Cliente*** {#organização-cliente}

O sistema proposto é direcionado à empresa MR Digital. MR Digital é uma empresa filiada à FOUSP que oferece cursos presenciais de pós-graduação de odontologia, mais especificamente implantodontia digital. A organização possui como característica central a comercialização de cursos estruturados em turmas, com número limitado de vagas e datas previamente definidas, o que diferencia significativamente sua dinâmica de vendas em relação a outros setores.

Atualmente, o processo comercial de instituições como a cliente é frequentemente conduzido por meio de ferramentas genéricas de gestão de relacionamento com clientes (CRMs) ou até mesmo por planilhas, que não foram projetadas para lidar com as especificidades do contexto educacional. Nesse cenário, leads são cadastrados manualmente, o acompanhamento do funil de vendas é fragmentado e o controle de vagas por turma ocorre de forma descentralizada, muitas vezes sem integração com o processo comercial.

O cliente, nesse contexto, assume um papel duplo no projeto. Por um lado, atua como usuário final do sistema, por meio do gerenciamento dos seus clientes, alunos e cursos. Por outro, exerce o papel de patrocinador da solução, ao demandar uma ferramenta que aumente a eficiência operacional e a taxa de conversão de alunos.

3. ## ***Problema identificado*** {#problema-identificado}

O desenvolvimento do sistema é motivado por um problema recorrente no setor educacional: a inadequação das ferramentas disponíveis para a gestão do processo comercial. Soluções tradicionais de CRM tratam cada lead como uma oportunidade isolada, desconsiderando o fato de que, nesse contexto, o cliente potencial está vinculado a turmas específicas, com vagas limitadas e datas de início definidas.

Na prática, isso gera uma série de dificuldades operacionais. Em primeiro lugar, há perda de leads qualificados devido à falta de acompanhamento estruturado ao longo do funil de vendas. Além disso, a ausência de integração entre o pipeline comercial e o controle de vagas impede que as equipes tenham visibilidade em tempo real sobre a ocupação das turmas, resultando tanto em desperdício de vagas quanto em frustração de clientes interessados.

Outro problema relevante é a incapacidade de lidar com múltiplos interesses de um mesmo lead. Diferentemente de outros setores, é comum que um potencial aluno esteja simultaneamente interessado em diferentes cursos ou turmas, o que não é adequadamente suportado por CRMs genéricos. Como consequência, há perda de informações, retrabalho operacional e dificuldade na tomada de decisão baseada em dados.

Esses problemas impactam diretamente a eficiência das equipes comerciais e a sustentabilidade do negócio, reduzindo taxas de conversão, aumentando custos operacionais e limitando a capacidade de crescimento das instituições.

Além disso, ressalta-se a inadequação dos CRMs tradicionais ao uso nativo de IA generativa. 

4. ## ***Objetivo do software*** {#objetivo-do-software}

Diante desse contexto, o objetivo do sistema é estruturar e aumentar o processo comercial da empresa, integrando, de forma nativa, a gestão de leads com o controle de cursos, turmas e vagas disponíveis à geração de conteúdos.

A proposta central é oferecer uma plataforma capaz de acompanhar todo o ciclo de vida de um lead, desde o primeiro contato até a efetivação da matrícula, considerando as restrições reais do negócio, como limitação de vagas e datas de início das turmas. Diferentemente de soluções genéricas, o sistema é projetado especificamente para refletir a lógica do setor educacional, no qual a conversão depende não apenas do interesse do lead, mas também da disponibilidade de vagas. A partir das análises das conversas, o sistema será capaz de extrapolar métricas comportamentais e de público-alvo, como persona e perfis ideais de clientes, para uso em campanhas de marketing. 

Espera-se que a adoção do sistema gere benefícios significativos, como o aumento das taxas de conversão, a redução da perda de oportunidades comerciais, a melhoria na organização do pipeline de vendas e conexão efetiva entre vendas e marketing. Além disso, o sistema permitirá maior controle sobre a ocupação das turmas e facilitará a comunicação com os leads, por meio de automações integradas.

Para atingir esses objetivos, o sistema deverá oferecer funcionalidades como cadastro e gestão de leads, controle do funil de vendas, gerenciamento de cursos e turmas, controle automatizado de vagas, lista de espera, identificação de leads potenciais para uma determinada turma, criação de campanhas direcionadas e análise de métricas comportamentais dos leads.

5. ## ***Público-alvo/Usuários*** {#público-alvo/usuários}

O sistema tem como principal grupo de usuários a equipe ou o responsável pelas vendas, cadastro de leads, acompanhamento do funil comercial e registro de interações com potenciais alunos. Esses usuários utilizam o sistema de forma operacional, sendo diretamente impactados pela usabilidade e eficiência da interface. 

Além disso, há os administradores, que desempenham funções de gestão, como criação de cursos, definição de turmas, controle de vagas e acompanhamento de métricas de desempenho e de público. Esses usuários demandam uma visão mais analítica e estratégica do sistema.

Por fim, o sistema contempla um nível superior de acesso, denominado super administrador, responsável pela gestão de usuários, definição de permissões e configuração geral da plataforma. Esse perfil garante o controle institucional do sistema e a segurança das informações.

Todos os usuários acessam o sistema por meio de um navegador web, não sendo prevista, na versão inicial, a existência de aplicações mobile nativas.

2. # **Escopo do sistema** {#escopo-do-sistema}

   1. ## ***Escopo incluído*** {#escopo-incluído}

O escopo do sistema abrange o desenvolvimento de uma plataforma web voltada à gestão do processo comercial de empresas de educação, com foco na integração entre o acompanhamento de leads e o controle de turmas e vagas. Nesse sentido, o sistema incluirá funcionalidades que permitam o cadastro e gerenciamento de leads, o controle do pipeline de vendas e o registro completo do histórico de interações entre a equipe comercial e os potenciais alunos.

Adicionalmente, o sistema contemplará a gestão de cursos e turmas, possibilitando a criação, edição e desativação de ofertas educacionais, bem como o controle automático do número de vagas disponíveis. A associação entre leads e turmas será um elemento central da solução, permitindo que um mesmo lead seja vinculado a múltiplas oportunidades, com acompanhamento independente em cada uma delas.

Outro componente importante do escopo é a implementação de análise baseada em Inteligência Artificial, como lead score, identificação de *personas* mais relevantes no público e determinação de perfil ideal de cliente. Esse conhecimento será base para um agente copiloto de vendas, que auxiliará o atendimento aos alunos e identificação de oportunidades prioritárias para determinadas turmas. 

2. ## ***Fora do escopo*** {#fora-do-escopo}

Para garantir a viabilidade do projeto dentro do escopo da disciplina, algumas funcionalidades foram deliberadamente excluídas da versão inicial do sistema. Entre elas, destaca-se a ausência de um aplicativo mobile nativo, sendo o acesso restrito ao ambiente web.

Além disso, não está prevista a automação completa do atendimento aos alunos, com envio de mensagens no WhatsApp e disparo de cold emails. Funcionalidades relacionadas a pagamentos online também não fazem parte do escopo.

Essas exclusões permitem concentrar o desenvolvimento nas funcionalidades essenciais do sistema, garantindo maior qualidade na entrega e possibilitando futuras expansões de forma estruturada.

3. # **Requisitos do sistema** {#requisitos-do-sistema}

   1. ## ***Matriz geral de requisitos*** {#matriz-geral-de-requisitos}

A matriz geral de requisitos consolida, de forma resumida, os oito requisitos funcionais e seis requisitos não funcionais do sistema. Ela permite visualizar o escopo do produto de maneira estruturada, relacionando cada requisito a uma necessidade concreta do negócio. No caso do Captus, os requisitos foram definidos a partir da proposta de uma plataforma de CRM voltada ao setor educacional, com foco em gestão de leads, turmas, vagas e comunicação comercial.

| Código | Nome | Tipo | Descrição resumida |
| :---: | :---: | :---: | :---: |
| REQF01 | Cadastrar leads | F | Permite o cadastro de leads com dados pessoais e origem |
| REQF02 | Gerenciar pipeline | F | Permite controlar a etapa comercial de cada lead |
| REQF03 | Registrar interações | F | Armazena histórico de ligações, e-mails, mensagens e anotações |
| REQF04 | Gerenciar cursos e turmas | F | Permite criar, editar e desativar cursos e turmas |
| REQF05 | Controlar vagas | F | Atualiza automaticamente a disponibilidade de vagas por turma |
| REQF06 | Registrar matrícula | F | Associa leads a turmas e registra matrícula |
| REQF07 | Exibir painel de métricas | F | Apresenta indicadores comerciais e operacionais |
| REQF08 | Análise comportamental | F | Extrair métricas comportamentais e de público-alvo a partir da análise consolidada de mensagens e vendas. |
| REQNF01 | Desempenho | NF | Respostas em menos de 2 segundos |
| REQNF02 | Escalabilidade de usuários | NF | Suporta 50 usuários simultâneos sem degradação perceptível  |
| REQNF03 | Escalabilidade de dados | NF | Suporta 1.000 leads e 100 turmas sem queda de desempenho  |
| REQNF04 | Segurança de autenticação | NF | Autenticação via JWT (access 1h / refresh 7 dias) sobre HTTPS  |
| REQNF05 | Segurança em nível de dados | NF | Row-Level Security no PostgreSQL aplicada a 100% das tabelas com dados sensíveis  |
| REQNF06 | Usabilidade | NF | 90% dos novos usuários completam fluxos principais em até 2 minutos sem treinamento  |

## 

2. ## ***Requisitos funcionais*** {#requisitos-funcionais}

### Os requisitos funcionais descrevem as funcionalidades que o sistema deve oferecer para atender ao problema identificado no contexto do projeto. No caso do Captus, esses requisitos refletem tanto as necessidades operacionais da equipe comercial quanto as especificidades do setor educacional, no qual leads, cursos, turmas e vagas precisam estar integrados dentro de uma mesma lógica de negócio. 

**REQF01 \- Cadastrar leads**

* **Descrição:** O sistema deve permitir que usuários autorizados cadastrem leads, incluindo dados pessoais, como nome, e-mail, telefone e canal de origem.  
* **Critérios de aceitação:**  
  * O sistema deve permitir o preenchimento de nome, e-mail, telefone e origem do lead.  
  * O sistema deve restringir o cadastro a usuários autenticados.  
  * O sistema deve impedir duplicidade de registros com o mesmo e-mail, quando aplicável.  
  * O cadastro deve ficar disponível para consulta e edição posterior.

**REQF02 \- Gerenciar pipeline de vendas**

* **Descrição:** O sistema deve permitir gerenciar o estágio de contato de cada lead no funil de vendas, contemplando etapas como novo, contatado, negociando, matriculado ou perdido.  
* **Critérios de aceitação:**  
  * O sistema deve permitir alterar o estágio comercial de um lead.  
  * Cada mudança de estágio deve ficar registrada no histórico.  
  * O estágio atual do lead deve ficar visível na interface principal.  
  * O sistema deve permitir acompanhar o avanço do lead no funil.

**REQF03 \- Registrar histórico de interações**

* **Descrição:** O sistema deve registrar o histórico de interações com cada lead, incluindo ligações, e-mails, mensagens de WhatsApp e anotações feitas pela equipe comercial.  
* **Critérios de aceitação:**  
  * O sistema deve armazenar a data, o tipo de interação e o responsável pelo registro.  
  * O histórico deve permanecer associado ao lead correspondente.  
  * As interações devem ser listadas em ordem cronológica.  
  * O usuário deve conseguir consultar esse histórico em tela.

**REQF04 \- Gerenciar cursos e turmas**

* **Descrição:** O sistema deve permitir criar, editar e desativar cursos e suas respectivas turmas, sem depender de um domínio específico.  
* **Critérios de aceitação:**  
  * O sistema deve permitir cadastrar curso com nome e informações básicas.  
  * O sistema deve permitir vincular uma ou mais turmas a cada curso.  
  * Cada turma deve possuir capacidade máxima de vagas.  
  * O sistema deve permitir editar ou desativar cursos e turmas já existentes.

**REQF05 \- Controlar vagas por turma**

* **Descrição:** O sistema deve controlar o número de vagas disponíveis por turma, atualizá-lo automaticamente após uma matrícula e acionar mecanismos relacionados à lista de espera quando houver liberação de vaga. Esse requisito é um dos diferenciais centrais da solução proposta.  
* **Critérios de aceitação:**  
  * O sistema deve reduzir automaticamente o número de vagas disponíveis após a matrícula de um lead.  
  * O sistema deve impedir novas matrículas quando a turma estiver lotada.  
  * O sistema deve identificar quando uma vaga for liberada.  
  * Ao surgir vaga, o sistema deve permitir o acionamento da lista de espera.

**REQF06 \- Associar lead a turma e registrar matrícula**

* **Descrição:** O sistema deve permitir associar um lead a uma turma específica e registrar sua matrícula, integrando o processo comercial ao preenchimento real da turma.  
* **Critérios de aceitação:**  
  * O sistema deve permitir selecionar um lead e vinculá-lo a uma turma.  
  * O sistema deve registrar a matrícula com data e vínculo correspondente.  
  * A matrícula deve impactar automaticamente a disponibilidade de vagas.  
  * O status comercial do lead deve poder refletir essa mudança.

**REQF07 \- Exibir painel com métricas do pipeline**

* **Descrição:** O sistema deve disponibilizar um painel contendo métricas relevantes do processo comercial, como total de leads, taxa de conversão por etapa e visualização das próximas turmas.  
* **Critérios de aceitação:**  
  * O painel deve exibir o total de leads cadastrados.  
  * O painel deve apresentar indicadores por etapa do pipeline.  
  * O painel deve mostrar informações sobre turmas próximas ou em andamento.  
  * Os dados exibidos devem refletir o estado atualizado do sistema.

**REQF08 \- Análise comportamental**

* **Descrição:** O sistema deve ser capaz de extrair métricas comportamentais e de público-alvo a partir da análise consolidada de mensagens e vendas.  
* **Critérios de aceitação:**  
  * O sistema deve gerar métricas a partir de dados de mensagens e vendas.  
  * Deve apresentar indicadores básicos (ex: conversão, volume de interações e tempo de resposta).  
  * Os dados devem ser exibidos em formato visual (dashboard/gráficos).  
  * Deve garantir integridade e atualização dos dados em tempo adequado.

  3. ## ***Requisitos não funcionais*** {#requisitos-não-funcionais}

**REQNF01 \- Desempenho**

* **Descrição:** O sistema deve manter tempos de resposta compatíveis com uso operacional intensivo, mesmo sob carga típica das equipes comerciais.  
* **Critérios de aceitação:**  
  * O tempo de resposta da API deve ser de no máximo 500ms no percentil 95 para operações de leitura.  
  * O tempo de resposta da API deve ser de no máximo 1.000ms no percentil 95 para operações de escrita.  
  * O carregamento inicial do dashboard (aba Analytics) deve ocorrer em até 2 segundos com base de 10.000 leads.  
  * A movimentação de cards no Kanban (drag and drop) deve apresentar feedback visual em até 200ms.

**REQNF02 \- Escalabilidade de usuários**

* **Descrição:** O sistema deve suportar o número de usuários simultâneos previsto para a operação inicial, com margem de crescimento.  
* **Critérios de aceitação:**  
  * Suportar 50 usuários simultâneos sem degradação perceptível dos tempos definidos no REQNF01.  
  * Manter os tempos de resposta dentro de uma margem de até 30% de aumento em pico de 100 usuários simultâneos.  
  * Permitir escalonamento horizontal do backend sem alteração do código de aplicação.

**REQNF03 \- Escalabilidade de dados**

* **Descrição:** O sistema deve manter desempenho adequado conforme a base de dados cresce ao longo do uso da plataforma.  
* **Critérios de aceitação:**  
  * Suportar até 1.000 leads cadastrados sem queda de desempenho além do limite definido no REQNF01.  
  * Suportar até 100 turmas ativas e até 10.000 de registros de interações.

**REQNF04 \- Segurança de autenticação**

* **Descrição:** O sistema deve autenticar usuários de forma segura e proteger as sessões contra acessos indevidos.  
* **Critérios de aceitação:**  
  * Autenticação realizada por meio de tokens JWT, com access token de validade máxima de 1 hora e refresh token de validade máxima de 7 dias.  
  * Toda comunicação entre cliente e servidor deve ocorrer sobre HTTPS com TLS 1.2 ou superior.  
  * Bloqueio temporário da conta após 5 tentativas de login falhas em 10 minutos.

**REQNF05 \- Segurança em nível de dados**

* **Descrição:** O controle de acesso definido pelo papel do usuário deve ser aplicado também na camada de banco de dados, garantindo defesa em profundidade.  
* **Critérios de aceitação:**  
  * Row-Level Security (RLS) habilitada em 100% das tabelas que armazenam dados de leads, turmas, interações e matrículas.  
  * Toda consulta deve ser filtrada automaticamente pelo identificador da organização e pelo papel do usuário autenticado.  
  * Tentativas de acesso a registros fora do escopo do usuário devem ser bloqueadas pelo banco e registradas como evento de auditoria.

**REQNF06 \- Usabilidade**

* **Descrição:** A interface deve permitir que novos usuários executem os fluxos principais com pouco ou nenhum treinamento.  
* **Critérios de aceitação:**  
  * Em testes com usuários reais, ao menos 90% deles devem concluir o cadastro de um lead em até 2 minutos sem treinamento prévio.  
  * Os fluxos principais (cadastrar lead, mover no pipeline, registrar matrícula) devem ser concluídos em no máximo 4 cliques a partir de qualquer aba.

# **4  Prototipação da solução**

## ***4.1  Objetivos do protótipo***

A prototipação do Captus teve como objetivo central validar, de forma antecipada, as principais hipóteses de uso e de interação do sistema antes do início do desenvolvimento. Como a plataforma é voltada a equipes comerciais de empresas de educação \- usuários que operam sob pressão de tempo e precisam de respostas rápidas \-, era fundamental garantir que os fluxos principais fossem intuitivos, eficientes e aderentes à lógica real do negócio.

Especificamente, a prototipação buscou avaliar os seguintes aspectos:

•        Fluxo de uso do sistema: verificar se a sequência de ações necessárias para cadastrar um lead, movê-lo no pipeline, associá-lo a uma turma e registrar sua matrícula era compreensível e fluída, sem exigir treinamento prévio.

•        Estrutura e hierarquia das telas: avaliar se a organização visual das informações \- painéis de métricas, quadro Kanban, histórico de conversas e detalhes de turmas \- permitia que o usuário localizasse rapidamente o que precisava.

•        Interação com funcionalidades críticas: testar se os diferenciais centrais do sistema (controle de vagas em tempo real, pipeline multi-curso por lead, lista de espera, conversações integradas) eram representáveis de forma clara na interface, sem ambiguidade.

•        Navegação por abas: confirmar que a divisão do sistema em quatro seções principais \- Analytics, Funil, Conversas e Cursos \- organizava as funcionalidades de forma lógica e previsível, permitindo que o usuário transitasse entre contextos sem perder referência.

Além disso, a prototipação serviu como instrumento de comunicação com o cliente (MR Digital), permitindo alinhar expectativas sobre o produto final e coletar feedback qualitativo sobre prioridades e ajustes necessários antes de qualquer investimento em código.

## ***4.2  Protótipo de baixa fidelidade***

O protótipo de baixa fidelidade foi construído na forma de wireframes esquemáticos, com foco na estrutura de informação e na disposição dos elementos em tela. O objetivo era representar a arquitetura de navegação e os fluxos operacionais do sistema de maneira rápida e iterativa, facilitando discussões internas no grupo e com o cliente.

A navegação do sistema foi organizada em quatro abas principais, acessíveis por um menu lateral fixo presente em todas as telas: Analytics, Funil, Conversas e Cursos. Essa estrutura reflete a separação lógica entre as preocupações do usuário: visão estratégica (Analytics), operação comercial (Funil), comunicação com leads (Conversas) e gestão da oferta educacional (Cursos). As principais telas são descritas a seguir.

### **Aba Analytics**

A aba Analytics funciona como dashboard de performance de vendas e é a primeira tela exibida após o login. O wireframe define a disposição dos blocos de informação em três camadas. Na parte superior, três cards de destaque apresentam indicadores-chave: total de leads no funil, novos leads captados no dia e taxa de conversão geral. Logo abaixo, uma barra horizontal de status exibe a distribuição quantitativa dos leads por estágio do funil (Novo, Contatado, Negociando, Matriculado e Perdido), oferecendo uma fotografia instantânea do volume em cada fase.

Na metade inferior, dois painéis lado a lado apresentam: um gráfico de abandono (churn) por estágio da conversa por WhatsApp, baseado na metodologia SPIN (Situação, Problema, Implicação, Necessidade de Solução), que indica em qual fase da interação a perda de leads é mais crítica; e um gráfico de tendências de conversação ao longo do tempo, com indicadores de tempo médio de resposta e horário de pico. Por fim, um gráfico de faturamento mensal com projeção de crescimento fecha a tela. ![][image1]

*Figura 1 \- Protótipo da aba Analytics (dashboard de performance).*

### **Aba Funil**

A aba Funil é o espaço operacional central do sistema, onde a equipe de vendas gerencia o avanço dos leads no processo comercial. O wireframe representa um quadro no formato Kanban com colunas correspondentes aos estágios: Novo, Contatado e Negociando (com rolagem horizontal para Matriculado e Perdido). Cada coluna exibe um contador de leads.

Cada card de lead apresenta: o canal de origem identificado por um badge colorido (Instagram, Site Direto, WhatsApp, Indicação, entre outros), o nome do lead, o curso de interesse, o tempo decorrido desde a última movimentação e, quando aplicável, indicadores de prioridade, valor da negociação (ex.: R$ 12.400,00) e data de follow-up agendado. Na parte superior da tela, dois botões de ação permitem importar leads em lote ou cadastrar um novo lead manualmente (REQF01). O wireframe valida o fluxo de movimentação de leads entre colunas via drag and drop (REQF02) e o acesso rápido ao detalhe de cada lead ao clicar no card. ![][image2]

*Figura 2 \- Protótipo da aba Funil (pipeline Kanban).*

### **Aba Conversas**

A aba Conversas centraliza toda a comunicação com os leads e está vinculada aos requisitos REQF03 (histórico de interações), REQF07 (e-mails automatizados) e REQF08 (mensagens via WhatsApp). O wireframe organiza a tela em três paineis. À esquerda, uma lista de leads ativos com filtros por status (Todos, Não Lidos, WhatsApp), exibindo nome, prévia da última mensagem, horário e canal de origem. No centro, o histórico completo da conversa selecionada em formato de chat, com balões diferenciados por remetente, timestamps e indicadores de leitura, além de campo de envio rápido de mensagem na parte inferior.

À direita, um painel de contexto do lead consolida informações estratégicas para o vendedor: foto e dados do lead, botões de ação rápida (Perfil e Matricular), curso de interesse, estágio atual no funil com probabilidade de conversão estimada (lead score), notas rápidas com dores identificadas e observações qualitativas, e uma timeline de atividade recente. Essa tela permite que o vendedor tenha contexto completo do lead sem sair da conversa, integrando comunicação e inteligência comercial em um único ponto.

![][image3]

*Figura 3 \- Protótipo da aba Conversas (histórico de interações e contexto do lead).*

### **Aba Cursos**

A aba Cursos é voltada à gestão da oferta educacional e atende diretamente aos requisitos REQF04 (gerenciar cursos e turmas) e REQF05 (controlar vagas). A tela inicial apresenta uma listagem de todos os cursos ativos com suas turmas vinculadas. É importante destacar a relação 1:N entre curso e turmas: um mesmo curso pode ter múltiplas turmas, diferenciadas pela data de início.

Ao clicar em uma turma específica, o usuário acessa a tela de detalhe, que consolida todas as informações operacionais em quatro seções. No topo, cards de destaque exibem: número de matrículas versus vagas totais com barra de progresso (ex.: 24/30, 80%), período letivo (datas de início e término), modalidade (Presencial, Híbrido) e identificador da turma, além do investimento por vaga e receita prevista para a turma. Dois botões de ação estão disponíveis: Editar Ementa e Matricular Aluno, sendo este último o ponto de integração entre a gestão de cursos e o pipeline comercial (REQF06).

A seção de Cronograma do Curso apresenta uma timeline visual com os módulos, datas, locais, descrições e alertas de presença obrigatória. Em seguida, a seção Gerenciar Documentos permite o upload e download de editais, contratos e materiais de apoio associados ao curso. Por fim, a seção Alunos Matriculados lista os perfis ativos da turma com status de pagamento (Pago & Ativo, Parcelado), frequência e data de matrícula, oferecendo ao administrador controle completo sobre a turma.

![][image4]

*Figura 4 \- Protótipo da aba Cursos (detalhe de turma com cronograma, documentos e alunos).*

### **Aspectos de UX**

Em termos de UX, o protótipo priorizou três aspectos fundamentais. O primeiro é a simplicidade e intuição: todas as telas foram desenhadas para que os fluxos principais (cadastrar lead, mover no pipeline, conversar, matricular) pudessem ser concluídos em no máximo três a quatro cliques a partir de qualquer aba. O menu lateral com as quatro seções permanece visível em todas as telas, e a barra de busca global no topo permite localizar leads, cursos ou turmas de qualquer contexto.

O segundo é a densidade informacional controlada: cada tela agrega informações complementares sem sobrecarregar \- a aba Conversas, por exemplo, combina chat, dados do lead e atividade recente em três paineis que podem ser consumidos de forma independente. O terceiro é a consistência visual: badges de canal, indicadores numéricos e botões de ação seguem o mesmo padrão em todas as abas, reduzindo a carga cognitiva ao transitar entre seções.

Quanto à portabilidade, embora o MVP seja exclusivamente web, o protótipo foi estruturado com layout responsivo em mente: o menu lateral colapsa em telas menores e os cards se reorganizam verticalmente em dispositivos com largura reduzida.

## ***4.3  Protótipo de alta fidelidade ou funcional***

O protótipo de alta fidelidade foi desenvolvido como uma aplicação web funcional, construída em React, que permite navegação real entre as quatro abas do sistema e interação com os elementos de interface. Diferentemente do protótipo de baixa fidelidade, esta versão incorpora a identidade visual definitiva do Captus (paleta baseada em tons de azul e branco, tipografia limpa, iconografia consistente), dados simulados com valores realistas e comportamentos interativos como drag and drop no pipeline, filtros dinâmicos e transições entre telas.

O objetivo deste protótipo é duplo: validar a experiência de uso com fidelidade próxima ao sistema final e servir como base de código reutilizável para o desenvolvimento do produto. A seguir são descritas as telas e o fluxo de interação.

### **Aba Analytics**

O dashboard funcional exibe dados simulados em tempo real, com todos os componentes visuais interativos. Os cards de KPI no topo (Total de Leads, Novos Leads Hoje, Taxa de Conversão) atualizam-se dinamicamente conforme o filtro de período selecionado (Últimos 30 Dias por padrão). A distribuição do funil por estágio é clicável, redirecionando o usuário ao Funil já filtrado no estágio correspondente. Os gráficos de abandono por estágio SPIN e tendências de conversação são renderizados com bibliotecas de visualização (Recharts), com tooltips ao passar o mouse. O botão Exportar Relatório permite download dos dados consolidados.

### **Aba Funil**

O pipeline Kanban funcional implementa drag and drop entre colunas, permitindo que o usuário arraste cards de lead entre os estágios (Novo, Contatado, Negociando, Matriculado e Perdido). Cada movimentação gera um registro automático no histórico do lead (REQF02). Os cards exibem badge de canal de origem, nome, curso, tempo no estágio, valor e data de follow-up. Ao clicar em um card, um drawer lateral abre com os detalhes do lead. Filtros por curso e turma no topo do quadro permitem isolar o pipeline de uma turma específica . O botão “+ Novo Lead” abre um modal de cadastro rápido (REQF01).

### **Aba Conversas**

A tela de Conversas funcional implementa o layout de três paineis com navegação em tempo real. A lista de leads à esquerda suporta filtros (Todos, Não Lidos, WhatsApp) e busca por nome. Ao selecionar um lead, o painel central carrega o histórico de mensagens com balões estilizados, timestamps e status de leitura, enquanto o painel direito exibe o contexto consolidado: curso de interesse, estágio no funil com lead score (probabilidade de conversão), notas rápidas editáveis e timeline de atividade recente. O campo de envio de mensagem na parte inferior permite compor e enviar mensagens diretamente. Os botões Perfil e Matricular no painel direito oferecem atalhos diretos para as ações comerciais mais frequentes.

### **Aba Cursos**

A aba Cursos funcional apresenta a listagem de cursos ativos com expansão para as turmas vinculadas (relação 1:N, onde cada turma é diferenciada pela data de início). Ao clicar em uma turma, a tela de detalhe carrega com quatro seções interativas: cards de métricas (matrículas/vagas com barra de progresso, período letivo, investimento e receita prevista), cronograma visual do curso com módulos navegáveis por mês, área de upload e download de documentos, e lista de alunos matriculados com status de pagamento e frequência. O botão Matricular Aluno integra a gestão de turmas ao pipeline comercial (REQF06), e a barra de progresso de vagas reflete o controle automático do REQF05.

### **Fluxo de interação do usuário**

O fluxo típico de uso do sistema, conforme implementado no protótipo funcional, segue a sequência:

1\. 	O usuário acessa o sistema pelo navegador e realiza login com e-mail e senha. Após autenticação, é redirecionado à aba Analytics, onde visualiza os KPIs consolidados e identifica oportunidades de atuação.

2\. 	Ao identificar que o estágio “Novo” concentra leads sem contato, o usuário navega à aba Funil, localiza os cards nessa coluna e inicia o processo de abordagem.

3\. 	Para abordar um lead, o usuário alterna para a aba Conversas, seleciona o lead na lista, consulta o painel de contexto (curso de interesse, notas, lead score) e envia uma mensagem pelo campo de chat.

4\. 	Conforme a negociação avança, o usuário retorna ao Funil e arrasta o card do lead para o estágio seguinte (Contatado → Negociando).

5\. 	Quando a negociação é concluída, o usuário navega à aba Cursos, seleciona a turma de interesse, clica em Matricular Aluno e vincula o lead. O número de vagas é atualizado automaticamente e o card no Funil move-se para “Matriculado”.

6\. 	O usuário encerra a sessão pelo botão de logout no menu lateral.

Esse fluxo demonstra como os requisitos REQF01 (cadastro de lead), REQF02 (gestão de pipeline), REQF03 (histórico de interações), REQF05 (controle de vagas) e REQF06 (registro de matrícula) se conectam em uma sequência coesa através das quatro abas.

## ***4.4  Aprendizados obtidos com o protótipo***

O processo de prototipação gerou aprendizados significativos que influenciaram diretamente o refinamento dos requisitos e a estratégia de desenvolvimento do Captus.

O primeiro aprendizado diz respeito à importância do painel de contexto na aba Conversas. Nos esboços iniciais, o histórico de mensagens e os dados do lead estavam em telas separadas. Após simulações de uso, ficou evidente que o vendedor precisava consultar informações como curso de interesse, estágio no funil, lead score e notas qualitativas sem sair da conversa. Esse feedback resultou no design de três paineis integrados, refinando os critérios de aceitabilidade do REQF03 para exigir que o histórico de interações esteja sempre acompanhado do contexto comercial do lead.

O segundo aprendizado foi sobre a complexidade visual do pipeline multi-curso. Foi previsto que um mesmo lead pode estar em estágios diferentes para turmas distintas. Nos primeiros esboços, isso gerava confusão visual, pois o mesmo lead aparecia múltiplas vezes no quadro Kanban sem distinção clara de contexto. A solução identificada foi implementar filtros por curso e turma no topo do Funil, além de exibir o badge do curso de interesse em cada card. Esse refinamento transformou um requisito que poderia gerar ambiguidade em uma experiência de uso clara.

O terceiro aprendizado está relacionado à integração entre a aba Cursos e o pipeline. Inicialmente, o botão de matrícula existia apenas no Funil. Após os testes, percebeu-se que o fluxo era mais natural quando o administrador podia matricular diretamente a partir da tela de detalhe da turma \- onde já tinha visão do número de vagas disponíveis. Isso levou à adição do botão “Matricular Aluno” na aba Cursos, refinando o critério de aceitabilidade do REQF06 para exigir que o registro de matrícula esteja acessível tanto a partir do lead (Funil/Conversas) quanto a partir da turma (Cursos).

O quarto aprendizado envolve a visibilidade da análise de churn por estágio SPIN no dashboard. O gráfico de abandono revelou que a maior perda de leads ocorre no estágio de “Implicação” (45% de churn), o que levou à inclusão de uma recomendação automática no dashboard sugerindo refinamento dos roteiros de proposta de valor. Esse insight reforçou a necessidade de que o painel de métricas não seja apenas descritivo, mas também prescritivo, oferecendo sinalizações acionáveis para a equipe comercial.

Por fim, a prototipação reforçou a importância de manter a interface adaptada aos diferentes perfis de usuário. O protótipo evidenciou que certas ações \- como editar ementa de cursos ou gerenciar documentos \- não deveriam sequer aparecer para o perfil de Usuário comum, evitando sobrecarga cognitiva. A informação do perfil logado (ex.: “Dr. Lucas Mendes \- Diretor Clínico”) aparece no rodapé do menu lateral, reforçando ao usuário qual nível de acesso está ativo.

# **5  Conclusão do Ciclo 1**

O Ciclo 1 do projeto Captus cumpriu seu objetivo central: definir, de forma estruturada e validada, os alicerces de uma plataforma de CRM projetada nativamente para o setor educacional.

A partir da identificação do problema \- a inadequação de CRMs genéricos para empresas cujo ciclo de vendas gira em torno de turmas, vagas e calendário acadêmico \-, o grupo definiu uma proposta de valor clara: oferecer uma ferramenta onde a gestão de leads e o controle de turmas são elementos integrados, e não módulos desconectados. Essa visão orientou todas as decisões de escopo, requisitos e arquitetura.

Durante o ciclo, foram especificados 12 requisitos funcionais e 12 requisitos não funcionais, cobrindo desde operações básicas como cadastro de leads e gestão de pipeline até funcionalidades diferenciais como o controle automatizado de vagas por turma, a lista de espera com priorização automática e o pipeline multi-curso por lead .

A arquitetura do sistema foi desenhada para atender aos requisitos não funcionais de desempenho, segurança e escalabilidade. A stack definida \- React no frontend, FastAPI no backend, Supabase/PostgreSQL como banco de dados, Redis e Celery para processamento assíncrono, SendGrid e WhatsApp Business API para comunicação \- reflete um compromisso entre robustez técnica e custo operacional compatível com o porte do projeto.

A prototipação, conduzida em duas fases (baixa e alta fidelidade), permitiu validar os fluxos principais de uso e identificar refinamentos relevantes nos requisitos. Os aprendizados obtidos \- como a necessidade do painel de contexto integrado às conversas, os filtros por turma no pipeline, a dupla entrada para matrícula (via lead e via turma) e as recomendações acionáveis no dashboard \- demonstram que a prototipação cumpriu seu papel de antecipar problemas e refinar o escopo.

Como próximos passos para o Ciclo 2, o grupo planeja:

•        Iniciar o desenvolvimento do backend, implementando as rotas de API para cadastro de leads, gestão de pipeline e controle de turmas/vagas, priorizando os requisitos funcionais de maior impacto (REQF01, REQF02, REQF04, REQF05).

•        Desenvolver o frontend com base nos protótipos validados, conectando as telas às APIs do backend e reutilizando os componentes já implementados no protótipo funcional.

•        Implementar o mecanismo de autenticação e autorização por papéis, garantindo que a segurança de acesso esteja operacional desde as primeiras versões.

•        Configurar a infraestrutura de deploy (Railway ou Fly.io) e o pipeline de integração contínua.

•        Iniciar os testes com dados simulados para validar os critérios de aceitação definidos nos requisitos.