// ─── Current User ────────────────────────────────────────────────────────────
export const currentUser = {
  name: 'Dra. Ana Costa',
  role: 'Coordenadora Comercial',
  initials: 'AC',
}

// ─── Leads ───────────────────────────────────────────────────────────────────
export const leads = [
  { id: 1,  name: 'Dr. Carlos Silva',       email: 'carlos.silva@email.com',   phone: '(11) 99999-0001', source: 'Instagram',  course: 'Imersão em Implantodontia Digital',   stage: 'Novo',        lastContact: '2h atrás',  value: null,  assignee: 'AC' },
  { id: 2,  name: 'Dra. Beatriz Santos',    email: 'beatriz@email.com',        phone: '(11) 99999-0002', source: 'WhatsApp',   course: 'Imersão em Implantodontia Digital',   stage: 'Novo',        lastContact: '5h atrás',  value: null,  assignee: 'AC' },
  { id: 3,  name: 'Dr. Ricardo Oliveira',   email: 'ricardo@email.com',        phone: '(11) 99999-0003', source: 'Instagram',  course: 'Master 3.0 — Aperfeiçoamento Clínico', stage: 'Contatado',   lastContact: '1d atrás',  value: null,  assignee: 'AC' },
  { id: 4,  name: 'Dra. Carla Mendes',      email: 'carla@email.com',          phone: '(11) 99999-0004', source: 'WhatsApp',   course: 'Imersão em Implantodontia Digital',   stage: 'Contatado',   lastContact: '3h atrás',  value: null,  assignee: 'AC' },
  { id: 5,  name: 'Dra. Helena Martins',    email: 'helena@email.com',         phone: '(11) 99999-0005', source: 'Indicação',  course: 'Master 3.0 — Aperfeiçoamento Clínico', stage: 'Negociando',  lastContact: 'Hoje',       value: 22250, assignee: 'AC' },
  { id: 6,  name: 'Dr. Paulo Ferreira',     email: 'paulo@email.com',          phone: '(11) 99999-0006', source: 'Instagram',  course: 'Imersão em Implantodontia Digital',   stage: 'Negociando',  lastContact: '2d atrás',  value: 5900,  assignee: 'AC' },
  { id: 7,  name: 'Dr. Fabio J.',           email: 'fabio@email.com',          phone: '(11) 99999-0007', source: 'Indicação',  course: 'Imersão em Implantodontia Digital',   stage: 'Matriculado', lastContact: '5d atrás',  value: 5900,  assignee: 'AC' },
  { id: 8,  name: 'Dra. Mariana Luz',       email: 'mariana@email.com',        phone: '(11) 99999-0008', source: 'Indicação',  course: 'Master 3.0 — Aperfeiçoamento Clínico', stage: 'Matriculado', lastContact: '1s atrás',  value: 22250, assignee: 'AC' },
  { id: 9,  name: 'Dr. Thiago Costa',       email: 'thiago@email.com',         phone: '(11) 99999-0009', source: 'Instagram',  course: 'Imersão em Implantodontia Digital',   stage: 'Perdido',     lastContact: '2s atrás',  value: null,  assignee: 'AC' },
  { id: 10, name: 'Elena Rodriguez',        email: 'elena@email.com',          phone: '(11) 99999-0010', source: 'WhatsApp',   course: 'Especialização em Implantodontia Digital', stage: 'Negociando',  lastContact: 'Hoje',       value: 15000, assignee: 'AC' },
  { id: 11, name: 'Marcus Chen',            email: 'marcus@email.com',         phone: '(11) 99999-0011', source: 'E-mail',     course: 'Master 3.0 — Aperfeiçoamento Clínico', stage: 'Contatado',   lastContact: 'Hoje',       value: null,  assignee: 'AC' },
  { id: 12, name: 'Sarah Jenkins',          email: 'sarah@email.com',          phone: '(11) 99999-0012', source: 'WhatsApp',   course: 'Imersão em Implantodontia Digital',   stage: 'Contatado',   lastContact: 'Ontem',     value: null,  assignee: 'AC' },
]

// ─── Conversations ────────────────────────────────────────────────────────────
export const conversations = [
  { id: 1, leadId: 10, name: 'Elena Rodriguez',     lastMessage: 'Quais são os pré-requisitos para a Especialização? Já fiz a Imersão com vocês.',      timestamp: '12:45', unread: 2, channel: 'WhatsApp' },
  { id: 2, leadId: 11, name: 'Marcus Chen',         lastMessage: 'Enviei o comprovante de pagamento do Master por e-mail.',                               timestamp: '10:12', unread: 0, channel: 'E-mail'   },
  { id: 3, leadId: 12, name: 'Sarah Jenkins',       lastMessage: 'Quando começa a próxima turma da Imersão? Tenho scanner Straumann parado aqui.',        timestamp: 'Ontem', unread: 1, channel: 'WhatsApp' },
  { id: 4, leadId: 4,  name: 'Dra. Carla Mendes',  lastMessage: 'O certificado da Imersão é reconhecido pelo CFO? Preciso levar para o conselho.',       timestamp: '24 Out', unread: 0, channel: 'E-mail'  },
]

// ─── Messages (leadId → messages[]) ─────────────────────────────────────────
export const messages = {
  10: [
    { id: 1, text: 'Olá! Concluí a Imersão em março e foi transformador. Gostaria de avançar para a Especialização em Implantodontia Digital. Ela requer algum tempo mínimo de prática após a Imersão?', sent: false, timestamp: '12:40', channel: 'WhatsApp', read: true },
    { id: 2, text: 'Oi Elena! Que ótimo saber que a Imersão foi bem! Para a Especialização (24 meses, 1.200h com chancela FOUSP/USP-SP), recomendamos pelo menos 6 meses de prática após a Imersão. Você já está aplicando o fluxo digital nos seus casos?', sent: true, timestamp: '12:43', channel: 'WhatsApp', read: true },
    { id: 3, text: 'Quais são os pré-requisitos para a Especialização? Já fiz a Imersão com vocês.', sent: false, timestamp: '12:45', channel: 'WhatsApp', read: false },
  ],
  11: [
    { id: 1, text: 'Tenho scanner intraoral Sirios há 8 meses mas ainda dependo muito do laboratório. O Master resolve isso?', sent: false, timestamp: '09:20', channel: 'E-mail', read: true },
    { id: 2, text: 'Olá Marcus! O Master 3.0 é exatamente para isso — você fará atendimentos reais em pacientes supervisionado pelos Profs. Marcelo Romano e Eduardo Perissinoto, dominando todo o fluxo do escaneamento à prótese final. É o fim da dependência de laboratório.', sent: true, timestamp: '09:35', channel: 'E-mail', read: true },
    { id: 3, text: 'Enviei o comprovante de pagamento do Master por e-mail.', sent: false, timestamp: '10:12', channel: 'E-mail', read: true },
  ],
  12: [
    { id: 1, text: 'Quando começa a próxima turma da Imersão? Tenho scanner Straumann parado aqui.', sent: false, timestamp: 'Ontem', channel: 'WhatsApp', read: false },
  ],
  4: [
    { id: 1, text: 'O certificado da Imersão é reconhecido pelo CFO? Preciso levar para o conselho.', sent: false, timestamp: '24 Out', channel: 'E-mail', read: true },
  ],
}

// ─── Courses ─────────────────────────────────────────────────────────────────
export const courses = [
  {
    id: 1,
    name: 'Imersão em Implantodontia Digital',
    description: '3 dias intensivos (24h) para dominar o fluxo digital completo: enceramento digital, planejamento 3D reverso, cirurgia guiada (Neodent Easy-Guide) e impressão 3D. Certificado FOUSP/USP-SP.',
    modalities: ['Presencial'],
    activeCohorts: 3,
  },
  {
    id: 2,
    name: 'Master 3.0 — Aperfeiçoamento Clínico',
    description: '10 meses (160h) com enfoque 100% clínico — atendimento de pacientes reais supervisionado por mestres e doutores da FOUSP. Do planejamento digital à finalização protética. Certificado FOUSP/USP-SP.',
    modalities: ['Presencial'],
    activeCohorts: 1,
  },
  {
    id: 3,
    name: 'Especialização em Implantodontia Digital',
    description: '24 meses de formação completa (1.200h): biologia peri-implantar, fluxo digital integral, regeneração tecidual, PRF, levantamento de seio maxilar e CAD/CAM. A maior chancela: FOUSP/USP-SP.',
    modalities: ['Presencial'],
    activeCohorts: 1,
  },
]

// ─── Cohort Detail ─────────────────────────────────────────────────────────
export const cohort = {
  id: 1,
  courseId: 2,
  name: 'Master 3.0 — Turma T2 2026',
  metrics: {
    enrolled: 24,
    capacity: 30,
    startDate: '05 Mai 2026',
    endDate: '28 Fev 2027',
    modalities: ['Presencial'],
    pricePerSlot: 22250,
    projectedRevenue: 534000,
  },
  schedule: [
    { id: 1, date: '05 Mai', title: 'Fase 1: Fundamentos e Fluxo Digital', time: '08:00 – 18:00', location: 'Laboratório MR — FOUSP', description: 'Filosofia MR (Golden Circle), biologia peri-implantar, treinamento em Meshmixer e BlueSky. Hands-on de escaneamento com scanner Sirios.', mandatory: false },
    { id: 2, date: '19 Mai', title: 'Fase 1: Planejamento Reverso e Enceramento Digital', time: '08:00 – 18:00', location: 'Laboratório MR — FOUSP', description: 'Planejamento tridimensional do posicionamento apical dos implantes, desenho do perfil de emergência e confecção de guias cirúrgicos. Introdução ao CodiagnostiX.', mandatory: false },
    { id: 3, date: '16 Jun', title: 'Fase 2: Cirurgia Guiada — Paciente 1', time: '08:00 – 18:00', location: 'Clínica Parceira FOUSP', description: 'Realização da primeira cirurgia guiada em paciente real, sob supervisão direta do Prof. Dr. Marcelo Romano e da Profa. Luciana Yamaguchi.', mandatory: true },
    { id: 4, date: '14 Jul', title: 'Fase 4: Reabilitação Protética e Finalização', time: '09:00 – 17:00', location: 'Laboratório MR — FOUSP', description: 'Condicionamento tecidual, escaneamento pós-operatório, confecção e instalação da prótese definitiva. Maquiagem e glazeamento com o Prof. Marcos Venturini.', mandatory: true },
  ],
  documents: [
    { id: 1, name: 'Ementa Completa Master 3.0 T2-2026.pdf', type: 'PDF', uploadedAt: '02 Abr 2026' },
    { id: 2, name: 'Contrato de Matrícula Master 3.0.docx', type: 'DOCX', uploadedAt: '10 Mar 2026' },
    { id: 3, name: 'Material Didático — Fase 1 Fundamentos.zip', type: 'ZIP', uploadedAt: '28 Abr 2026' },
  ],
  students: [
    { id: 1, name: 'Dr. Fabio J.',        email: 'fabio@email.com',    enrolledAt: '15 Mar 2026', status: 'Pago',      attendance: 100 },
    { id: 2, name: 'Dra. Mariana Luz',    email: 'mariana@email.com',  enrolledAt: '20 Mar 2026', status: 'Parcelado', attendance: 92  },
    { id: 3, name: 'Dr. Carlos Viana',    email: 'carlos@email.com',   enrolledAt: '22 Mar 2026', status: 'Pago',      attendance: 100 },
    { id: 4, name: 'Dra. Fernanda Rocha', email: 'fernanda@email.com', enrolledAt: '01 Abr 2026', status: 'Parcelado', attendance: 88  },
  ],
}

// ─── AI Analysis Data ────────────────────────────────────────────────────────
// Source: playbook/ personas + argumentos_valor + filosofia (MR Digital / FOUSP)
export const aiAnalysis = {
  icp: {
    summary:
      'Cirurgião-dentista implantodontista ou em transição para a especialidade. Busca previsibilidade clínica ("eliminar surpresas cirúrgicas"), autonomia sobre o laboratório e a credencial acadêmica da FOUSP/USP-SP como ativo de reputação. Motivado por ROI e diferenciação competitiva no mercado.',
    attributes: [
      { label: 'Faixa Etária', value: '30 – 55 anos' },
      { label: 'Perfil Dominante', value: 'Implantodontista / Clínico Geral' },
      { label: 'Tecnologia', value: 'Scanner intraoral (tem ou quer)' },
      { label: 'Ticket Médio', value: 'R$ 5,9k – 22,2k' },
      { label: 'Canal Principal', value: 'WhatsApp / Indicação' },
      { label: 'Chancela-Gatilho', value: 'Selo FOUSP / USP-SP' },
    ],
    insight:
      'O Recém-Especializado converte 2× mais rápido (33%) que o Especialista Analógico (16%). Leads por Indicação fecham em média 2.1× mais rápido que leads de Instagram.',
  },
  personas: [
    {
      id: 1,
      name: 'O Especialista Analógico',
      description:
        '10+ anos de prática "à mão livre". Cético com tecnologia, mas motivado pela ameaça de obsolescência e pela perda de parceiros-chave (protéticos se aposentando). Compra uma "ponte segura", não um recomeço.',
      traits: [
        'Validado pela própria experiência clínica',
        'Jornada lenta e reflexiva — dor crônica',
        'Gatilho: "conectar experiência ao digital"',
      ],
      painPoint: 'Dependência crítica do laboratório e imprevisibilidade protética — "cada caso é uma surpresa".',
      channel: 'WhatsApp / Indicação',
      badge: '58% · conv. 16%',
      color: 'blue',
    },
    {
      id: 2,
      name: 'O Iniciado Digital',
      description:
        'Já investiu em scanner intraoral (R$ 80k–120k) mas o usa apenas como substituto de moldagem. Frustrado com o "ativo imobilizado" — depende do laboratório para as etapas que gerariam diferencial.',
      traits: [
        'Já convencido do "porquê" digital',
        'Busca destravar o ROI do scanner',
        'Alto potencial de upsell para o Master 3.0',
      ],
      painPoint: 'Scanner subutilizado gerando dissonância cognitiva diária — investimento que não retorna.',
      channel: 'Instagram / Google',
      badge: '19% · conv. 12,5%',
      color: 'purple',
    },
    {
      id: 3,
      name: 'O Recém-Especializado',
      description:
        'Concluiu a especialização recentemente. Base teórica sólida mas insegurança cirúrgica aguda — medo de erros irreversíveis na prática real. Busca um "GPS cirúrgico" para operar com a confiança de um sênior.',
      traits: [
        'Dor aguda → ciclo de venda mais curto',
        'Maior taxa de conversão: 33%',
        'Gatilho: segurança e previsibilidade',
      ],
      painPoint: 'Ansiedade com estruturas anatômicas vitais (nervo alveolar, seio maxilar) e medo do erro irreversível.',
      channel: 'Instagram / Indicação',
      badge: '14% · conv. 33%',
      color: 'orange',
    },
    {
      id: 4,
      name: 'O Focado em Prótese',
      description:
        'Protesista ou reabilitador frustrado com a "herança cirúrgica" de colegas — implantes mal posicionados que comprometem sua obra protética. Quer controlar o planejamento cirúrgico via Planejamento Reverso.',
      traits: [
        'Conv. 0% na Imersão (produto errado)',
        'Candidato ideal ao Master 3.0',
        'Gatilho: Planejamento Reverso / controle total',
      ],
      painPoint: 'Receber implantes em posições que forçam "gambiarras" protéticas — perda de controle sobre o resultado final.',
      channel: 'Indicação / LinkedIn',
      badge: '9% dos leads',
      color: 'emerald',
    },
  ],
  painPoints: [
    { rank: 1, title: 'Imprevisibilidade Cirúrgica',        description: '"Cada caso é uma surpresa" — falta de controle sobre o posicionamento tridimensional do implante.', severity: 'high',   affected: '71%' },
    { rank: 2, title: 'Dependência Crítica de Laboratório', description: 'Risco de perda de parceiro-chave (protético aposentando) e falta de controle sobre prazos e qualidade.',   severity: 'high',   affected: '63%' },
    { rank: 3, title: 'ROI do Scanner Subutilizado',        description: 'Investimento em scanner (R$ 80k–120k) usado apenas como substituto de moldagem — ROI negativo percebido.',    severity: 'high',   affected: '51%' },
    { rank: 4, title: 'Insegurança com Anatomia Vital',     description: 'Medo de proximidade com nervo alveolar inferior e seio maxilar em cirurgias sem guia digital.',               severity: 'medium', affected: '44%' },
    { rank: 5, title: 'Curva de Aprendizado em Software',   description: 'Resistência e ansiedade com Meshmixer, BlueSky e CodiagnostiX sem suporte clínico estruturado.',              severity: 'medium', affected: '38%' },
  ],
}

// ─── Copiloto seed messages ───────────────────────────────────────────────────
// Demonstra abordagem SPIN + conhecimento das 4 personas MR Digital
export const coPilotoSeedMessages = [
  {
    id: 1,
    role: 'assistant',
    text: 'Olá, Dra. Ana! Sou o Copiloto MR, seu assistente de inteligência comercial. Conheço as 4 personas do funil MR (Especialista Analógico, Iniciado Digital, Recém-Especializado e Focado em Prótese), a filosofia de vendas SPIN e o portfólio completo — Imersão, Master 3.0 e Especialização. Como posso ajudar?',
    timestamp: '14:02',
  },
  {
    id: 2,
    role: 'user',
    text: 'Quais leads estão mais quentes agora e o que devo fazer?',
    timestamp: '14:03',
  },
  {
    id: 3,
    role: 'assistant',
    text: 'Com base no funil atual, identifiquei 3 oportunidades prioritárias:\n\n1. Elena Rodriguez — Negociando, R$ 15.000, Especialização. Perfil: Recém-Especializada (33% de conversão). Última mensagem há 2h. Argumente com segurança e o "GPS cirúrgico" do fluxo digital — é o gatilho principal para esse perfil.\n\n2. Dra. Helena Martins — Negociando, R$ 22.250, Master 3.0. Perfil: Especialista Analógico. Valide a experiência dela antes de qualquer argumento técnico. Envie case de ex-aluna com bagagem similar.\n\n3. Dr. Paulo Ferreira — Negociando, Imersão. Sem contato há 2 dias — risco de esfriamento. Perfil: Iniciado Digital. Argumento central: destravar o ROI do scanner com o fluxo completo da Imersão.',
    timestamp: '14:03',
  },
]

// ─── Analytics Data ───────────────────────────────────────────────────────────
export const analyticsData = {
  kpis: {
    totalLeads: 250,
    newLeadsToday: 12,
    conversionRate: 18,
  },
  funnelStages: [
    { name: 'Novo',        count: 42, color: '#2563EB' },
    { name: 'Contatado',   count: 68, color: '#D97706' },
    { name: 'Negociando',  count: 31, color: '#EA580C' },
    { name: 'Matriculado', count: 85, color: '#2563EB' },
    { name: 'Perdido',     count: 24, color: '#94A3B8' },
  ],
  spinAbandonment: [
    { stage: 'Situação',   retained: 88, churned: 12 },
    { stage: 'Problema',   retained: 72, churned: 28 },
    { stage: 'Implicação', retained: 55, churned: 45 },
    { stage: 'Necessidade', retained: 85, churned: 15 },
  ],
  conversationTrends: [
    { period: 'Sem 1', whatsapp: 42, calls: 18 },
    { period: 'Sem 2', whatsapp: 58, calls: 22 },
    { period: 'Sem 3', whatsapp: 75, calls: 15 },
    { period: 'Sem 4', whatsapp: 91, calls: 30 },
    { period: 'Sem 5', whatsapp: 68, calls: 25 },
    { period: 'Sem 6', whatsapp: 110, calls: 35 },
  ],
  revenue: [
    { month: 'Jan', value: 85000,  projected: false },
    { month: 'Fev', value: 92000,  projected: false },
    { month: 'Mar', value: 78000,  projected: false },
    { month: 'Abr', value: 115000, projected: false },
    { month: 'Mai', value: 138000, projected: false },
    { month: 'Jun', value: 125000, projected: false },
    { month: 'Jul', value: 145000, projected: true  },
    { month: 'Ago', value: 160000, projected: true  },
    { month: 'Set', value: 155000, projected: true  },
    { month: 'Out', value: 172000, projected: true  },
    { month: 'Nov', value: 185000, projected: true  },
    { month: 'Dez', value: 198000, projected: true  },
  ],
  avgResponseTime: '4m 12s',
  peakHour: '14:00 – 16:00',
  totalRevenue: 1428500,
  revenueGrowth: '+15.4%',
}
