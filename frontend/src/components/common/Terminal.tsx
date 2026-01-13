import { ReactNode } from 'react'

interface TerminalProps {
  children: ReactNode
  title?: string
  className?: string
}

export function Terminal({ children, title, className = '' }: TerminalProps) {
  return (
    <div className={`bg-bg-secondary border border-bg-highlight rounded-lg overflow-hidden ${className}`}>
      {title && (
        <div className="bg-bg-highlight px-4 py-2 border-b border-bg-highlight flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-accent-red" />
            <div className="w-3 h-3 rounded-full bg-accent-yellow" />
            <div className="w-3 h-3 rounded-full bg-accent-green" />
          </div>
          <span className="text-fg-dim text-sm ml-2">{title}</span>
        </div>
      )}
      <div className="p-4 font-mono text-sm">
        {children}
      </div>
    </div>
  )
}
