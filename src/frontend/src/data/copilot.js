// ─── Copiloto — dados mock ──────────────────────────────────────────────────
// Fonte de dados do protótipo (prototype/Copiloto WhatsApp.dc.html). Na P4 estes
// dados são substituídos por chamadas reais em lib/copilotApi.js, mantendo o mesmo
// formato (contratos Lead / Draft do PRD) para troca transparente.

// Persona → cor de destaque (avatar/badge).
export const PERSONA_META = {
  'Especialista Analógico': { color: '#2563EB', bg: '#EFF6FF' },
  'Iniciado Digital': { color: '#7C3AED', bg: '#F5F3FF' },
  'Recém-Especializado': { color: '#EA580C', bg: '#FFF7ED' },
  'Focado em Prótese': { color: '#059669', bg: '#ECFDF5' },
}
const DEFAULT_META = { color: '#2563EB', bg: '#EFF6FF' }
export const personaMeta = (persona) => PERSONA_META[persona] || DEFAULT_META

// Tom da variante → cor do badge.
export const TONE_META = {
  Consultivo: { color: '#2563EB', bg: '#EFF6FF' },
  Objetivo: { color: '#059669', bg: '#ECFDF5' },
  Caloroso: { color: '#D97706', bg: '#FFFBEB' },
}
export const toneMeta = (tone) => TONE_META[tone] || DEFAULT_META

// Lead { id, name, initials, persona, stage, course, value, source, phone, lastContact, angle, history:[{fromLead,text}] }
export const COPILOT_LEADS = [
  {
    id: 10, name: 'Elena Rodriguez', initials: 'ER', persona: 'Recém-Especializado',
    stage: 'Negociando', course: 'Especialização em Implantodontia Digital', value: 15000,
    phone: '(11) 99999-0010', source: 'WhatsApp', lastContact: 'há 2h',
    angle: 'Já fez a Imersão — a conversa é de continuidade, não de início. O gatilho é segurança: o fluxo digital como "GPS cirúrgico". Evite preço de cara; reforce a chancela FOUSP e ofereça um próximo passo concreto.',
    history: [
      { fromLead: true, text: 'Olá! Concluí a Imersão em março e foi transformador. Gostaria de avançar para a Especialização. Ela requer tempo mínimo de prática após a Imersão?' },
      { fromLead: false, text: 'Oi Elena! Que ótimo saber disso! Para a Especialização (24 meses, 1.200h, chancela FOUSP/USP-SP), recomendamos pelo menos 6 meses de prática. Você já está aplicando o fluxo digital nos seus casos?' },
      { fromLead: true, text: 'Quais são os pré-requisitos para a Especialização? Já fiz a Imersão com vocês.' },
    ],
  },
  {
    id: 5, name: 'Dra. Helena Martins', initials: 'HM', persona: 'Especialista Analógico',
    stage: 'Negociando', course: 'Master 3.0 — Aperfeiçoamento Clínico', value: 22250,
    phone: '(11) 99999-0005', source: 'Indicação', lastContact: 'hoje',
    angle: '18 anos de prática à mão livre. Valide a experiência clínica ANTES de qualquer argumento tecnológico — o digital amplia o que ela domina, não substitui. Um case de ex-aluna sênior aumenta a conversão.',
    history: [
      { fromLead: true, text: 'Tenho quase 20 anos de prática à mão livre. Sinceramente, não sei se preciso disso agora.' },
      { fromLead: false, text: 'Dra. Helena, sua experiência é justamente o que torna o fluxo digital tão poderoso — ele potencializa o que a senhora já domina.' },
      { fromLead: true, text: 'Me manda mais detalhes do Master 3.0.' },
    ],
  },
  {
    id: 6, name: 'Dr. Paulo Ferreira', initials: 'PF', persona: 'Iniciado Digital',
    stage: 'Negociando', course: 'Imersão em Implantodontia Digital', value: 5900,
    phone: '(11) 99999-0006', source: 'Instagram', lastContact: 'há 2 dias',
    angle: 'Sem contato há 2 dias — risco de esfriamento. A dor é o "ativo imobilizado": scanner caro usado só como moldagem. Reative com urgência genuína e ROI concreto + próximo passo com prazo.',
    history: [
      { fromLead: true, text: 'Tenho scanner Sirios há 8 meses, mas ainda uso só pra moldagem digital.' },
      { fromLead: false, text: 'Dr. Paulo, é exatamente isso que a Imersão resolve — conectar o scanner ao planejamento 3D reverso e à cirurgia guiada. Você sai fazendo na semana seguinte.' },
    ],
  },
  {
    id: 11, name: 'Marcus Chen', initials: 'MC', persona: 'Iniciado Digital',
    stage: 'Contatado', course: 'Master 3.0 — Aperfeiçoamento Clínico', value: null,
    phone: '(11) 99999-0011', source: 'E-mail', lastContact: 'hoje',
    angle: 'Já enviou o comprovante de pagamento do Master — o foco agora é confirmar a matrícula e dar boas-vindas, reduzindo qualquer atrito.',
    history: [
      { fromLead: true, text: 'Tenho scanner intraoral Sirios mas dependo muito do laboratório. O Master resolve isso?' },
      { fromLead: false, text: 'Olá Marcus! O Master 3.0 é exatamente para isso — atendimentos reais supervisionados, do escaneamento à prótese final. É o fim da dependência de laboratório.' },
      { fromLead: true, text: 'Enviei o comprovante de pagamento do Master por e-mail.' },
    ],
  },
  {
    id: 12, name: 'Sarah Jenkins', initials: 'SJ', persona: 'Recém-Especializado',
    stage: 'Contatado', course: 'Imersão em Implantodontia Digital', value: null,
    phone: '(11) 99999-0012', source: 'WhatsApp', lastContact: 'ontem',
    angle: 'Scanner Straumann parado — urgência natural. Use a próxima turma como gatilho e a segurança cirúrgica do fluxo guiado.',
    history: [
      { fromLead: true, text: 'Quando começa a próxima turma da Imersão? Tenho scanner Straumann parado aqui.' },
    ],
  },
  {
    id: 3, name: 'Dr. Ricardo Oliveira', initials: 'RO', persona: 'Focado em Prótese',
    stage: 'Contatado', course: 'Master 3.0 — Aperfeiçoamento Clínico', value: null,
    phone: '(11) 99999-0003', source: 'Instagram', lastContact: 'há 1 dia',
    angle: 'O gatilho é o Planejamento Reverso: controle total da reabilitação antes da cirurgia. Não venda como iniciante — fale de controle do resultado protético.',
    history: [
      { fromLead: true, text: 'Cansei de receber implantes mal posicionados que comprometem minha prótese.' },
      { fromLead: false, text: 'Dr. Ricardo, com o Planejamento Reverso o senhor define a prótese ideal primeiro — a cirurgia segue o seu plano.' },
    ],
  },
]

// Draft { tone:"Consultivo"|"Objetivo"|"Caloroso", text } — Análise (reasoning) + 3 variantes por lead.
export const DRAFTS = {
  10: {
    reasoning: 'Elena é Recém-Especializada — o perfil que mais converte (33%) e com o ciclo mais curto. Como ela já fez a Imersão, a conversa é de continuidade. O gatilho dela é segurança e previsibilidade. Confirme os pré-requisitos de forma simples, reforce que ela já chega na frente e ofereça um próximo passo concreto (conversa com a Profa. Luciana) — sem puxar preço agora.',
    variants: [
      { tone: 'Consultivo', text: 'Oi Elena! Que bom que a Imersão fez sentido pra você 🙌 Pra Especialização (24 meses, 1.200h, chancela FOUSP/USP-SP) o pré-requisito é só registro ativo no CRO + graduação em Odonto — e você já chega na frente por dominar o fluxo digital. Quer que eu agende uma conversa rápida com a Profa. Luciana Yamaguchi essa semana, pra ela te mostrar a jornada completa?' },
      { tone: 'Objetivo', text: 'Elena, sobre a Especialização: os pré-requisitos são registro ativo no CRO e graduação em Odontologia — você cumpre os dois. As inscrições da próxima turma já estão abertas. Posso reservar sua vaga e te enviar o contrato hoje?' },
      { tone: 'Caloroso', text: 'Elena, fiquei muito feliz em saber que a Imersão foi transformadora! 💙 Você tem exatamente o perfil que mais cresce na Especialização. Bora dar esse próximo passo juntas? Me diz o melhor dia que eu organizo tudo pra você.' },
    ],
  },
  5: {
    reasoning: 'Helena é Especialista Analógico (quase 20 anos à mão livre). Regra de ouro: valide a experiência dela ANTES de qualquer argumento técnico. Posicione o digital como amplificação do que ela já domina, conecte aos princípios biológicos que ela conhece e ofereça um case de ex-aluna sênior — isso pode elevar a conversão em até 40%.',
    variants: [
      { tone: 'Consultivo', text: 'Dra. Helena, com quase 20 anos de prática a senhora já tem o mais difícil: o domínio clínico. O Master 3.0 não substitui isso — amplia. O Prof. Marcelo Romano conecta os princípios biológicos que a senhora já aplica ao posicionamento preciso via planejamento digital. 100% clínico, em pacientes reais, chancela FOUSP. Posso te enviar o relato de uma ex-aluna com trajetória parecida com a sua?' },
      { tone: 'Objetivo', text: 'Dra. Helena, segue o resumo do Master 3.0: 10 meses, 160h, 100% clínico em pacientes reais, supervisão FOUSP. A senhora entra usando toda a sua experiência e sai com o fluxo digital dominado. Quer que eu reserve uma vaga na próxima turma?' },
      { tone: 'Caloroso', text: 'Dra. Helena, profissionais com a sua bagagem são os que mais brilham no Master 3.0 — a tecnologia vira só uma extensão da mão experiente. Seria um prazer te acompanhar nessa transição. Posso te ligar amanhã pra conversar, sem compromisso?' },
    ],
  },
  6: {
    reasoning: 'Paulo é Iniciado Digital e está há 2 dias sem resposta — reative com cuidado e urgência genuína. A dor central é o "ativo imobilizado": scanner caro usado só como moldagem. Foque em ROI concreto e ofereça um próximo passo com prazo (vaga na próxima turma).',
    variants: [
      { tone: 'Consultivo', text: 'Dr. Paulo, lembrei do seu caso: scanner Sirios fazendo o trabalho de um alginato — R$ 100k parados. Na Imersão a gente conecta esse scanner ao planejamento 3D reverso e à cirurgia guiada, e você sai fazendo na semana seguinte. A próxima turma tem só 2 vagas. Consigo segurar uma pra você até amanhã?' },
      { tone: 'Objetivo', text: 'Dr. Paulo, retomando nossa conversa: próxima turma da Imersão com 2 vagas — 3 dias, fluxo digital completo, certificado FOUSP. Reservo a sua vaga?' },
      { tone: 'Caloroso', text: 'Oi Dr. Paulo! Não quero que você perca a próxima turma 🙌 Seu scanner tem potencial demais pra ficar só na moldagem. Bora destravar isso? Me chama aqui que eu te explico em 5 minutos.' },
    ],
  },
  11: {
    reasoning: 'Marcus já enviou o comprovante de pagamento do Master 3.0. A venda está fechada — o foco agora é confirmar a matrícula, dar boas-vindas e reduzir qualquer atrito de onboarding.',
    variants: [
      { tone: 'Consultivo', text: 'Marcus, recebi seu comprovante, muito obrigado! 🎉 Sua matrícula no Master 3.0 está confirmada. Vou te adicionar ao grupo da turma e te enviar o material da Fase 1 ainda hoje. Seja muito bem-vindo!' },
      { tone: 'Objetivo', text: 'Marcus, comprovante confirmado e matrícula no Master 3.0 ativa. Os próximos passos (grupo da turma + material da Fase 1) chegam por e-mail em instantes.' },
      { tone: 'Caloroso', text: 'Que alegria ter você no Master 3.0, Marcus! 🙌 Pode comemorar — a partir de agora é só evolução. Já já te mando tudo pra começarmos com o pé direito.' },
    ],
  },
  12: {
    reasoning: 'Sarah é Recém-Especializada com um scanner Straumann parado — há urgência natural. Use a próxima turma como gatilho de escassez e reforce a segurança cirúrgica do fluxo guiado, que é o que mais converte esse perfil.',
    variants: [
      { tone: 'Consultivo', text: 'Oi Sarah! A próxima turma da Imersão abre dia 12 e costuma lotar rápido. Com seu scanner Straumann você já tem metade do caminho — na Imersão a gente conecta ele à cirurgia guiada com guias impressos em 3D (Neodent Easy-Guide). Quer que eu reserve sua vaga?' },
      { tone: 'Objetivo', text: 'Sarah, próxima turma da Imersão: 3 dias, fluxo digital completo, certificado FOUSP. Posso te mandar o link de inscrição agora?' },
      { tone: 'Caloroso', text: 'Sarah, imagina operar com a segurança de um guia impresso, sem aquele frio na barriga? É exatamente isso que a Imersão entrega 💙 Bora colocar esse scanner pra trabalhar?' },
    ],
  },
  3: {
    reasoning: 'Ricardo é Focado em Prótese — o gatilho é o Planejamento Reverso: controle total da reabilitação antes da cirurgia. Não o trate como iniciante; fale a língua dele, de controle sobre o resultado protético final.',
    variants: [
      { tone: 'Consultivo', text: 'Dr. Ricardo, sei que o que mais incomoda é receber implantes em posições que forçam gambiarra protética. No Master 3.0 o senhor assume o Planejamento Reverso — define a prótese ideal primeiro e a cirurgia segue o seu plano. Controle total do resultado. Posso te mostrar um caso real?' },
      { tone: 'Objetivo', text: 'Dr. Ricardo, o Master 3.0 cobre Planejamento Reverso, cirurgia guiada e finalização protética — 100% clínico. Quer ver as datas da próxima turma?' },
      { tone: 'Caloroso', text: 'Dr. Ricardo, chega de herdar cirurgia mal posicionada, né? 😅 No Master 3.0 o plano é seu do início ao fim. Bora conversar sobre como isso muda seus casos?' },
    ],
  },
}

const fmtBRL = (n) => 'R$ ' + Number(n).toLocaleString('pt-BR')

// Atributos exibidos no chip de contexto (rótulo + valor).
export function leadAttrs(lead) {
  return [
    { label: 'Curso', value: lead.course },
    { label: 'Estágio', value: lead.stage },
    { label: 'Ticket', value: lead.value ? fmtBRL(lead.value) : '—' },
    { label: 'Origem', value: lead.source },
    { label: 'Último contato', value: lead.lastContact },
    { label: 'Telefone', value: lead.phone },
  ]
}

// Drafts de fallback para leads sem entrada curada em DRAFTS.
export function craftDrafts(lead) {
  const d = DRAFTS[lead.id]
  if (d) return d
  const first = lead.name.split(' ').slice(-1)[0]
  return {
    reasoning: `${lead.name} — perfil ${lead.persona}. ${lead.angle}`,
    variants: [
      { tone: 'Consultivo', text: `Olá ${first}! Sobre o ${lead.course}, posso te explicar como o fluxo digital se encaixa no seu momento. Quando seria um bom horário pra conversarmos?` },
      { tone: 'Objetivo', text: `${first}, tenho novidades sobre o ${lead.course}. Posso te enviar os detalhes e as próximas datas?` },
      { tone: 'Caloroso', text: `Oi ${first}! Lembrei de você 🙌 Acho que o ${lead.course} faz muito sentido pro seu momento. Bora conversar?` },
    ],
  }
}

// ─── Base de conhecimento (sem lead anexado) ────────────────────────────────
export function kbResponse(text) {
  const t = (text || '').toLowerCase()
  if (/(curso|imers|master|especializa|portf|produto|oferec|temos)/.test(t)) {
    return 'Portfólio MR Digital — todos com chancela FOUSP/USP-SP:\n\n1. Imersão em Implantodontia Digital — 3 dias (24h), presencial. R$ 5.900. Fluxo digital completo: enceramento digital, planejamento 3D reverso, cirurgia guiada (Neodent Easy-Guide) e impressão 3D. Indicado para Especialista Analógico e Recém-Especializado.\n\n2. Master 3.0 — Aperfeiçoamento Clínico — 10 meses (160h). R$ 22.250. 100% clínico, atendimento de pacientes reais supervisionado por mestres e doutores da FOUSP. Indicado para Iniciado Digital (upsell) e Focado em Prótese.\n\n3. Especialização em Implantodontia Digital — 24 meses (1.200h). A formação mais completa: biologia peri-implantar, regeneração tecidual, PRF, CAD/CAM, levantamento de seio maxilar.'
  }
  if (/(persona|perfil|converte|público|publico|icp|cliente ideal)/.test(t)) {
    return 'As 4 personas do funil MR:\n\n• Recém-Especializado (14% dos leads, conv. 33%) — a maior conversão e o ciclo mais curto. Dor: insegurança cirúrgica. Gatilho: segurança via "GPS cirúrgico".\n\n• Especialista Analógico (58%, conv. 16%) — jornada longa. Nunca trate como iniciante: valide a experiência clínica antes de qualquer argumento técnico.\n\n• Iniciado Digital (19%, conv. 12,5%) — já tem scanner, mas subutilizado. Maior LTV potencial (upsell para o Master 3.0).\n\n• Focado em Prótese (9%) — não converte na Imersão; encaminhe direto ao Master 3.0 com o argumento de Planejamento Reverso.'
  }
  if (/(spin|abordagem|metodologia|vender|venda|argument|objeç|objec)/.test(t)) {
    return 'Modelo consultivo SPIN da MR:\n\n• Situação — entenda o contexto clínico antes de qualquer pitch.\n• Problema — identifique a dor real (dependência de laboratório, scanner parado, insegurança cirúrgica).\n• Implicação — aprofunde o custo de não resolver. É aqui que a maioria abandona (45%) — invista tempo nesta etapa.\n• Necessidade — só então apresente o curso como a solução.\n\nRegra de ouro: nunca apresente preço antes de a dor estar clara. Quer que eu monte a abordagem para um lead específico? Anexe-o com @.'
  }
  if (/(churn|risco|esfri|perder|parado|sem contato)/.test(t)) {
    return 'Leads em risco de esfriamento (sem contato recente):\n\n• Dr. Paulo Ferreira — 2 dias sem resposta, Negociando (Imersão). Perfil: Iniciado Digital.\n• Dr. Ricardo Oliveira — 1 dia sem contato, Contatado (Master 3.0). Perfil: Focado em Prótese.\n• Sarah Jenkins — sem resposta desde ontem (Imersão). Perfil: Recém-Especializada.\n\nAnexe qualquer um deles com @ que eu gero as mensagens de reativação.'
  }
  if (/(semana|performance|resumo|número|numero|métrica|metrica|kpi)/.test(t)) {
    return 'Resumo desta semana:\n\n• Leads novos: 12 (+4,2% vs. semana anterior)\n• Conversas ativas: 4\n• Matriculados: 2 (Dr. Fabio J. — Imersão · Dra. Mariana Luz — Master 3.0)\n• Receita fechada: R$ 28.150\n• Tempo médio de resposta: 4m12s (abaixo da meta)\n\nAtenção: 3 leads em Negociando sem contato há +48h — risco de esfriamento. Recomendo reativação hoje.'
  }
  if (/(oi|olá|ola|bom dia|boa tarde|tudo bem|ajuda|pode fazer|o que voc)/.test(t)) {
    return 'Posso ajudar de duas formas:\n\n1. Como base de conhecimento — pergunte sobre os cursos, as 4 personas do funil, a metodologia SPIN, leads em risco ou o resumo da semana.\n\n2. Para redigir uma mensagem de WhatsApp, anexe um lead com @ — eu carrego o perfil e o histórico e sugiro as melhores abordagens.'
  }
  return 'Posso responder sobre os cursos da MR, as 4 personas do funil, a metodologia SPIN, leads em risco e o resumo da semana. Para eu redigir uma mensagem sob medida, anexe um lead com @ — assim trago o perfil e o histórico de conversas para o contexto.'
}

// ─── Slash-commands ─────────────────────────────────────────────────────────
const TODAY_TASKS = 'Suas tarefas de hoje:\n\n☐ Reativar Dr. Paulo Ferreira — Negociando há 2 dias sem contato (Imersão)\n☐ Enviar proposta do Master 3.0 para Dra. Helena Martins\n☐ Confirmar matrícula de Marcus Chen (comprovante recebido)\n☐ Responder Elena Rodriguez sobre os pré-requisitos da Especialização\n☐ Follow-up com Sarah Jenkins (scanner Straumann parado)\n\n5 ações priorizadas por probabilidade de conversão. Anexe qualquer lead com @ que eu redijo a mensagem.'

export const COMMANDS = [
  { cmd: '/weekly-review', label: 'Revisão da semana', desc: 'Resumo de leads, conversas, receita e alertas' },
  { cmd: '/today-tasks', label: 'Tarefas de hoje', desc: 'Ações priorizadas por probabilidade de conversão' },
  { cmd: '/at-risk', label: 'Leads em risco', desc: 'Quem está esfriando e precisa de reativação' },
  { cmd: '/personas', label: 'Personas do funil', desc: 'As 4 personas e suas taxas de conversão' },
  { cmd: '/courses', label: 'Cursos da MR', desc: 'Portfólio completo: Imersão, Master 3.0 e Especialização' },
  { cmd: '/spin', label: 'Método SPIN', desc: 'A abordagem consultiva de vendas da MR' },
]

// Executa um comando → texto de resposta da KB.
export function runCommand(cmd) {
  switch (cmd) {
    case '/weekly-review': return kbResponse('resumo semana')
    case '/today-tasks': return TODAY_TASKS
    case '/at-risk': return kbResponse('risco churn')
    case '/personas': return kbResponse('personas')
    case '/courses': return kbResponse('cursos')
    case '/spin': return kbResponse('spin')
    default: return kbResponse(cmd)
  }
}
