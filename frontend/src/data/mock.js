// ─── Current User ────────────────────────────────────────────────────────────
export const currentUser = {
  name: 'Dra. Ana Costa',
  role: 'Coordenadora Comercial',
  initials: 'AC',
}

// ─── Leads ───────────────────────────────────────────────────────────────────
export const leads = [
  { id: 1, name: 'Dr. Silva', email: 'silva@email.com', phone: '(11) 99999-0001', source: 'Instagram', course: 'Implantodontia Avançada', stage: 'Novo', lastContact: '2h atrás', value: null, assignee: 'AC' },
  { id: 2, name: 'Dra. Beatriz Santos', email: 'beatriz@email.com', phone: '(11) 99999-0002', source: 'WhatsApp', course: 'Harmonização Orofacial', stage: 'Novo', lastContact: '5h atrás', value: null, assignee: 'AC' },
  { id: 3, name: 'Dr. Ricardo Oliveira', email: 'ricardo@email.com', phone: '(11) 99999-0003', source: 'Site Direto', course: 'Cirurgia Bucomaxilo', stage: 'Contatado', lastContact: '1d atrás', value: null, assignee: 'AC' },
  { id: 4, name: 'Dra. Carla Mendes', email: 'carla@email.com', phone: '(11) 99999-0004', source: 'WhatsApp', course: 'Ortodontia Avançada', stage: 'Contatado', lastContact: '3h atrás', value: null, assignee: 'AC' },
  { id: 5, name: 'Dra. Helena Martins', email: 'helena@email.com', phone: '(11) 99999-0005', source: 'Indicação', course: 'Especialização Ortodontia', stage: 'Negociando', lastContact: 'Hoje', value: 12400, assignee: 'AC' },
  { id: 6, name: 'Dr. Paulo Ferreira', email: 'paulo@email.com', phone: '(11) 99999-0006', source: 'Instagram', course: 'Implantodontia Avançada', stage: 'Negociando', lastContact: '2d atrás', value: 8900, assignee: 'AC' },
  { id: 7, name: 'Dr. Fabio J.', email: 'fabio@email.com', phone: '(11) 99999-0007', source: 'Site Direto', course: 'Imersão Resinas Compostas', stage: 'Matriculado', lastContact: '5d atrás', value: 9800, assignee: 'AC' },
  { id: 8, name: 'Dra. Mariana Luz', email: 'mariana@email.com', phone: '(11) 99999-0008', source: 'Indicação', course: 'Harmonização Orofacial', stage: 'Matriculado', lastContact: '1s atrás', value: 7500, assignee: 'AC' },
  { id: 9, name: 'Dr. Thiago Costa', email: 'thiago@email.com', phone: '(11) 99999-0009', source: 'Instagram', course: 'Cirurgia Bucomaxilo', stage: 'Perdido', lastContact: '2s atrás', value: null, assignee: 'AC' },
  { id: 10, name: 'Elena Rodriguez', email: 'elena@email.com', phone: '(11) 99999-0010', source: 'WhatsApp', course: 'Dermato-Cirurgia Avançada', stage: 'Negociando', lastContact: 'Hoje', value: 15000, assignee: 'AC' },
  { id: 11, name: 'Marcus Chen', email: 'marcus@email.com', phone: '(11) 99999-0011', source: 'E-mail', course: 'Implantodontia Avançada', stage: 'Contatado', lastContact: 'Hoje', value: null, assignee: 'AC' },
  { id: 12, name: 'Sarah Jenkins', email: 'sarah@email.com', phone: '(11) 99999-0012', source: 'WhatsApp', course: 'Nutrição Pediátrica', stage: 'Contatado', lastContact: 'Ontem', value: null, assignee: 'AC' },
]

// ─── Conversations ────────────────────────────────────────────────────────────
export const conversations = [
  { id: 1, leadId: 10, name: 'Elena Rodriguez', lastMessage: 'Poderia esclarecer os pré-requisitos para o curso de Dermato-Cirurgia Avançada?', timestamp: '12:45', unread: 2, channel: 'WhatsApp' },
  { id: 2, leadId: 11, name: 'Marcus Chen', lastMessage: 'Enviei o comprovante de pagamento por e-mail.', timestamp: '10:12', unread: 0, channel: 'E-mail' },
  { id: 3, leadId: 12, name: 'Sarah Jenkins', lastMessage: 'Quando começa a próxima turma de Nutrição Pediátrica?', timestamp: 'Ontem', unread: 1, channel: 'WhatsApp' },
  { id: 4, leadId: 4, name: 'Dr. Julian Voss', lastMessage: 'Os detalhes da certificação do conselho médico não foram anexados.', timestamp: '24 Out', unread: 0, channel: 'E-mail' },
]

// ─── Messages (leadId → messages[]) ─────────────────────────────────────────
export const messages = {
  10: [
    { id: 1, text: 'Olá! Estou interessada no curso de Dermato-Cirurgia Avançada. Poderia esclarecer se as horas clínicas podem ser concluídas remotamente ou se a presença no local é obrigatória?', sent: false, timestamp: '12:42', channel: 'WhatsApp', read: true },
    { id: 2, text: 'Oi Elena! Para o programa de Dermato-Cirurgia Avançada, 40% das horas clínicas exigem participação presencial em nossas clínicas parceiras para procedimentos cirúrgicos supervisionados. O restante pode ser via simulação.', sent: true, timestamp: '12:45', channel: 'WhatsApp', read: true },
    { id: 3, text: 'Poderia esclarecer os pré-requisitos para o curso de Dermato-Cirurgia Avançada?', sent: false, timestamp: '12:46', channel: 'WhatsApp', read: false },
  ],
  11: [
    { id: 1, text: 'Olá! Gostaria de confirmar minha inscrição no curso.', sent: false, timestamp: '09:30', channel: 'E-mail', read: true },
    { id: 2, text: 'Olá Marcus! Sua inscrição foi confirmada. Você receberá os detalhes por e-mail.', sent: true, timestamp: '09:45', channel: 'E-mail', read: true },
    { id: 3, text: 'Enviei o comprovante de pagamento por e-mail.', sent: false, timestamp: '10:12', channel: 'E-mail', read: true },
  ],
  12: [
    { id: 1, text: 'Quando começa a próxima turma de Nutrição Pediátrica?', sent: false, timestamp: 'Ontem', channel: 'WhatsApp', read: false },
  ],
  4: [
    { id: 1, text: 'Os detalhes da certificação do conselho médico não foram anexados.', sent: false, timestamp: '24 Out', channel: 'E-mail', read: true },
  ],
}

// ─── Courses ──────────────────────────────────────────────────────────────────
export const courses = [
  {
    id: 1,
    name: 'Imersão em Implantodontia Digital',
    description: 'Formação completa em implantes com foco em tecnologia CAD/CAM e fluxo digital.',
    modalities: ['Presencial', 'Híbrido'],
    activeCohorts: 2,
  },
  {
    id: 2,
    name: 'Harmonização Orofacial Avançada',
    description: 'Técnicas de preenchimento, toxina botulínica e fios para cirurgiões-dentistas.',
    modalities: ['EAD', 'Híbrido'],
    activeCohorts: 1,
  },
  {
    id: 3,
    name: 'Ortodontia com Alinhadores',
    description: 'Planejamento e execução de tratamentos com alinhadores invisíveis.',
    modalities: ['EAD'],
    activeCohorts: 3,
  },
]

// ─── Cohort Detail ────────────────────────────────────────────────────────────
export const cohort = {
  id: 1,
  courseId: 1,
  name: 'Turma T2 — 2026',
  metrics: {
    enrolled: 24,
    capacity: 30,
    startDate: '01 Mai 2026',
    endDate: '12 Dez 2026',
    modalities: ['Presencial', 'Híbrido'],
    pricePerSlot: 22250,
    projectedRevenue: 534000,
  },
  schedule: [
    { id: 1, date: '05 Mai', title: 'Módulo 01: Fundamentos', time: '08:00 – 18:00', location: 'Laboratório A', description: 'Anatomia cirúrgica e protocolos básicos de implantes.', mandatory: false },
    { id: 2, date: '19 Mai', title: 'Módulo 02: Planejamento Digital', time: '08:00 – 18:00', location: 'Laboratório B', description: 'Uso de CBCT, software de planejamento e guias cirúrgicos.', mandatory: false },
    { id: 3, date: '02 Jun', title: 'Avaliação Prática 01', time: '09:00 – 13:00', location: 'Clínica Parceira', description: 'Procedimentos supervisionados em pacientes reais.', mandatory: true },
    { id: 4, date: '16 Jun', title: 'Módulo 03: Carga Imediata', time: '08:00 – 18:00', location: 'Laboratório A', description: 'Protocolos de carga imediata e provisórios.', mandatory: false },
  ],
  documents: [
    { id: 1, name: 'Ementa Completa T2-2026.pdf', type: 'PDF', uploadedAt: '02 Abr 2026' },
    { id: 2, name: 'Contrato de Matrícula.docx', type: 'DOCX', uploadedAt: '10 Mar 2026' },
    { id: 3, name: 'Material Didático — Módulo 01.zip', type: 'ZIP', uploadedAt: '28 Abr 2026' },
  ],
  students: [
    { id: 1, name: 'Dr. Fabio J.', email: 'fabio@email.com', enrolledAt: '15 Mar 2026', status: 'Pago', attendance: 100 },
    { id: 2, name: 'Dra. Mariana Luz', email: 'mariana@email.com', enrolledAt: '20 Mar 2026', status: 'Parcelado', attendance: 92 },
    { id: 3, name: 'Dr. Carlos Viana', email: 'carlos@email.com', enrolledAt: '22 Mar 2026', status: 'Pago', attendance: 100 },
    { id: 4, name: 'Dra. Fernanda Rocha', email: 'fernanda@email.com', enrolledAt: '01 Abr 2026', status: 'Parcelado', attendance: 88 },
  ],
}

// ─── Analytics Data ───────────────────────────────────────────────────────────
export const analyticsData = {
  kpis: {
    totalLeads: 250,
    newLeadsToday: 12,
    conversionRate: 18,
  },
  funnelStages: [
    { name: 'Novo', count: 42, color: '#2563EB' },
    { name: 'Contatado', count: 68, color: '#D97706' },
    { name: 'Negociando', count: 31, color: '#EA580C' },
    { name: 'Matriculado', count: 85, color: '#2563EB' },
    { name: 'Perdido', count: 24, color: '#94A3B8' },
  ],
  spinAbandonment: [
    { stage: 'Situação', retained: 88, churned: 12 },
    { stage: 'Problema', retained: 72, churned: 28 },
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
    { month: 'Jan', value: 85000, projected: false },
    { month: 'Fev', value: 92000, projected: false },
    { month: 'Mar', value: 78000, projected: false },
    { month: 'Abr', value: 115000, projected: false },
    { month: 'Mai', value: 138000, projected: false },
    { month: 'Jun', value: 125000, projected: false },
    { month: 'Jul', value: 145000, projected: true },
    { month: 'Ago', value: 160000, projected: true },
    { month: 'Set', value: 155000, projected: true },
    { month: 'Out', value: 172000, projected: true },
    { month: 'Nov', value: 185000, projected: true },
    { month: 'Dez', value: 198000, projected: true },
  ],
  avgResponseTime: '4m 12s',
  peakHour: '14:00 – 16:00',
  totalRevenue: 1428500,
  revenueGrowth: '+15.4%',
}
