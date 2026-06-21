import ReactMarkdown from 'react-markdown'

// Renderiza markdown do agente (títulos, negrito, listas, parágrafos) com estilo
// alinhado ao chat. @tailwindcss/typography não está instalado, então cada
// elemento ganha classes explícitas via overrides de `components`.
const COMPONENTS = {
  h1: ({ children }) => (
    <h1 className="text-[15px] font-bold text-slate-900 font-headline mt-3 mb-1.5 first:mt-0">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-sm font-bold text-slate-900 font-headline mt-3 mb-1.5 first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-[13px] font-bold text-slate-800 mt-2.5 mb-1 first:mt-0">
      {children}
    </h3>
  ),
  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
  strong: ({ children }) => (
    <strong className="font-semibold text-slate-900">{children}</strong>
  ),
  em: ({ children }) => <em className="italic">{children}</em>,
  ul: ({ children }) => (
    <ul className="list-disc pl-5 mb-2 last:mb-0 space-y-1">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-5 mb-2 last:mb-0 space-y-1">{children}</ol>
  ),
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  a: ({ children, href }) => (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className="text-[#2563EB] underline hover:text-[#1D4ED8]"
    >
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="px-1 py-0.5 rounded bg-slate-100 text-[0.85em] font-mono text-slate-800">
      {children}
    </code>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-slate-200 pl-3 italic text-slate-500 my-2">
      {children}
    </blockquote>
  ),
  hr: () => <hr className="my-3 border-slate-100" />,
}

export default function Markdown({ children, className = '' }) {
  return (
    <div className={className}>
      <ReactMarkdown components={COMPONENTS}>{children || ''}</ReactMarkdown>
    </div>
  )
}
