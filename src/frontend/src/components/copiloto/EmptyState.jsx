import { Sparkles } from 'lucide-react'

// Estado vazio do copiloto: saudação, composer (injetado via children) e
// dica de uso de comandos (/) e menções (@).
export default function EmptyState({ userName, children }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-[680px]">
        <h2 className="font-headline text-4xl font-extrabold tracking-tight text-slate-900 leading-tight mb-8">
          Olá, {userName}.
          <br />
          <span className="text-slate-400 font-bold">Qual mensagem vamos preparar?</span>
        </h2>

        {children}

        <p className="text-center mt-4 text-xs text-slate-400 flex items-center justify-center gap-1.5">
          <Sparkles size={13} />
          Pergunte sobre cursos e personas, use <strong className="text-slate-600">/</strong> para
          comandos, ou <strong className="text-slate-600">@</strong> para anexar um lead.
        </p>
      </div>
    </div>
  )
}
