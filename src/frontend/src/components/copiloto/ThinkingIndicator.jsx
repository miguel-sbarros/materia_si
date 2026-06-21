import { useEffect, useState } from 'react'
import { Sparkles } from 'lucide-react'

// Sequência rotativa de frases enquanto o agente trabalha (ciclo a cada ~1,8s).
const PHRASES = [
  'Analisando o perfil do lead',
  'Conectando com a filosofia MR',
  'Estruturando resposta',
]

const INTERVAL_MS = 1800

// Indicador "processando" do copiloto: alterna as frases acima enquanto visível.
// O intervalo é limpo ao desmontar (o componente só monta quando isTyping é true).
export default function ThinkingIndicator() {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const id = setInterval(
      () => setIndex((i) => (i + 1) % PHRASES.length),
      INTERVAL_MS,
    )
    return () => clearInterval(id)
  }, [])

  return (
    <div className="flex items-center gap-2">
      <span className="w-5 h-5 rounded-md bg-[#2563EB] flex items-center justify-center">
        <Sparkles size={11} className="text-white animate-pulse" />
      </span>
      <span key={index} className="text-sm text-slate-500 animate-mrfade">
        {PHRASES[index]}
        <span className="inline-flex ml-1 align-middle gap-0.5">
          <span
            className="w-1 h-1 rounded-full bg-slate-400 animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="w-1 h-1 rounded-full bg-slate-400 animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <span
            className="w-1 h-1 rounded-full bg-slate-400 animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </span>
      </span>
    </div>
  )
}
