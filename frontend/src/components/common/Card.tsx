import { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  title?: string
  subtitle?: string
  className?: string
  onClick?: () => void
  hoverable?: boolean
}

export function Card({ children, title, subtitle, className = '', onClick, hoverable = false }: CardProps) {
  const hoverClass = hoverable ? 'hover:border-accent-blue/50 cursor-pointer transition-colors' : ''

  return (
    <div
      className={`bg-bg-secondary border border-bg-highlight rounded-lg p-4 ${hoverClass} ${className}`}
      onClick={onClick}
    >
      {(title || subtitle) && (
        <div className="mb-3">
          {title && <h3 className="text-fg-primary font-semibold">{title}</h3>}
          {subtitle && <p className="text-fg-dim text-sm">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  )
}

interface CardGridProps {
  children: ReactNode
  columns?: 1 | 2 | 3 | 4
  className?: string
}

export function CardGrid({ children, columns = 3, className = '' }: CardGridProps) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  }

  return (
    <div className={`grid ${gridCols[columns]} gap-4 ${className}`}>
      {children}
    </div>
  )
}
