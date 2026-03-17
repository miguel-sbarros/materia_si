Software Requirements Document
MR Digital - Plataforma de CRM & Gestão de Leads
Grupo 10 | 2026
Felipe Smaniotto, Henrique Guaré, Miguel Barros, Murilo Abud, Ulisses Calixto
________________________________________
1. Visão Geral do Sistema
•	Nome do sistema: MR Digital CRM - Plataforma de Gestão de Leads & Cursos
•	Objetivo de negócio: Estruturar e automatizar a área comercial da MR Digital, reduzindo a perda de leads qualificados e melhorando as taxas de conversão para cursos de pós-graduação em odontologia.
•	Usuários principais: Equipe de vendas, coordenadores e administradores da MR Digital (afiliada à FOUSP).
•	Crescimento esperado de dados: Dezenas a centenas de leads por turma de curso; múltiplas turmas por ano. O sistema deve suportar até 10.000 registros de leads sem degradação no tempo de resposta, permitindo crescimento à medida que a empresa expanda seus canais de marketing.
•	Restrições regulatórias: A LGPD (Lei Geral de Proteção de Dados do Brasil) aplica-se a todos os dados pessoais coletados dos leads, incluindo CPF e informações de contato.
•	Limites orçamentários/operacionais: A solução deve ser econômica; preferência por integrações open-source e SaaS de baixo custo.
________________________________________
2. Requisitos Funcionais
Abaixo estão os requisitos funcionais detalhados do sistema:
•	FR-01 (Prioridade: Alta): O sistema deve permitir que usuários autorizados criem e atualizem leads, incluindo dados pessoais (nome, e-mail, telefone) e canal de origem.
•	FR-02 (Prioridade: Alta): O sistema deve permitir mover leads entre etapas definidas do pipeline de vendas (ex.: Novo, Contatado, Negociando, Matriculado, Perdido).
•	FR-03 (Prioridade: Alta): O sistema deve registrar o histórico completo de interações com cada lead (ligações, e-mails, mensagens de WhatsApp, anotações), garantindo rastreabilidade das atividades comerciais.
•	FR-04 (Prioridade: Alta): O sistema deve permitir criar, editar e desativar cursos (ex.: Implantodontia Digital) e suas respectivas turmas.
•	FR-05 (Prioridade: Alta): O sistema deve acompanhar o número de vagas disponíveis por turma e atualizá-lo automaticamente após uma matrícula.
•	FR-06 (Prioridade: Alta): O sistema deve permitir associar um lead a uma turma de curso e registrar a matrícula.
•	FR-07 (Prioridade: Média): O sistema deve enviar e-mails automatizados para leads em etapas configuráveis do funil de vendas.
•	FR-08 (Prioridade: Média): O sistema deve suportar o envio automatizado ou manual de mensagens de WhatsApp para leads.
•	FR-09 (Prioridade: Média): O sistema deve fornecer um painel com métricas do pipeline: total de leads, taxa de conversão por etapa e próximas turmas.
•	FR-10 (Prioridade: Alta): O sistema deve suportar controle de acesso baseado em papéis com pelo menos três níveis: Usuário, Admin e Super Admin.
________________________________________
3. Requisitos Não Funcionais
Abaixo estão as métricas e metas para os requisitos não funcionais:
•	Performance (Tempo de resposta da API sob carga): Respostas da API para consultas relacionadas a leads devem ser $< 200\text{ms no percentil 95 sob 50 usuários simultâneos}$.
•	Escalabilidade (Volume de dados): O sistema deve suportar até 10.000 registros de leads sem degradação perceptível no tempo de resposta.
•	Escalabilidade (Usuários ativos simultâneos): Até 50 usuários simultâneos.
•	Disponibilidade (Tempo de atividade do sistema): 99,5% de uptime mensal.
•	Segurança - Auth (Autenticação de usuários): Tokens de sessão baseados em JWT com expiração.
•	Segurança - Controle de Acesso: Todos os dados de leads devem ser protegidos por controle de acesso baseado em papéis (RBAC).
•	Segurança - RLS (Row Level Security): Papéis de Usuário, Admin e Super Admin aplicados no nível do banco de dados.
•	Segurança - Chaves (Armazenamento de chaves de API): Armazenadas em variáveis de ambiente, nunca no código-fonte.
•	Privacidade de dados (Conformidade com LGPD): CPF e endereço criptografados em repouso (AES-256).
•	Usabilidade (Tempo de onboarding): Fluxos principais operáveis em até 30 minutos sem treinamento.
•	Manutenibilidade (Cobertura de código): $>=70%$ de cobertura de testes unitários para módulos críticos.
•	Observabilidade (Logs e rastreamento): Logs estruturados para todas as chamadas de API; alertas de erro habilitados.
________________________________________
4. Premissas & Restrições
•	O sistema será acessado via navegador web; nenhum aplicativo móvel nativo é necessário na versão inicial.
•	Os dados de leads serão inseridos manualmente pela equipe de vendas.
•	Importação automática de plataformas externas de marketing (ex.: Facebook Ads) está fora do escopo da v1.
•	A integração com WhatsApp depende de acesso à API oficial do WhatsApp Business, que requer aprovação da Meta.
•	A equipe utilizará um banco de dados gerenciado em nuvem (ex.: Supabase) para reduzir a sobrecarga de infraestrutura.
•	A conformidade com a LGPD deve ser implementada desde o primeiro dia; conformidade retroativa não é aceitável.
•	Espera-se no máximo 3 turmas simultâneas por curso no curto prazo.
________________________________________
5. Mapeamento de Arquitetura
Decisões arquiteturais baseadas nos requisitos não funcionais (NFR):
•	Row Level Security (RLS) & Níveis de Acesso: Aplicar políticas de RLS na camada de banco de dados (ex.: Supabase/PostgreSQL RLS). O frontend renderiza apenas ações permitidas com base no papel retornado no token de autenticação.
•	Conformidade com LGPD & Criptografia: Criptografar campos sensíveis (CPF e endereço) em repouso usando AES-256 no banco de dados. Implementar logs de auditoria para acesso a dados pessoais identificáveis (PII).
•	Segurança de Chaves de API: Usar variáveis de ambiente ou um gerenciador de segredos (ex.: Doppler, AWS Secrets Manager). Nunca enviar credenciais para controle de versão.
•	Performance (< 200ms): Implementar indexação no banco de dados para campos frequentemente consultados, como status do lead e identificação da turma. Usar pool de conexões e cachear dados frequentemente acessados (ex.: lista de cursos).
•	Escalabilidade: Backend stateless (FastAPI) implantável como contêineres. Escalonamento horizontal via provedor de nuvem (ex.: Railway, Fly.io, AWS ECS). A arquitetura deve suportar 50 usuários simultâneos e pelo menos 10.000 registros de leads sem perda de desempenho.
•	Envio de Email/WhatsApp: Integrar com provedor de e-mail (ex.: SendGrid) e API do WhatsApp Business. Usar uma fila (ex.: Redis + Celery) para envio assíncrono, evitando bloquear respostas da API.
