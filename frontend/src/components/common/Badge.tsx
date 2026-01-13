import { ReactNode } from 'react'

type BadgeVariant = 'default' | 'blue' | 'green' | 'red' | 'yellow' | 'magenta' | 'cyan' | 'orange'

interface BadgeProps {
  children: ReactNode
  variant?: BadgeVariant
  className?: string
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-bg-highlight text-fg-secondary',
  blue: 'bg-accent-blue/20 text-accent-blue',
  green: 'bg-accent-green/20 text-accent-green',
  red: 'bg-accent-red/20 text-accent-red',
  yellow: 'bg-accent-yellow/20 text-accent-yellow',
  magenta: 'bg-accent-magenta/20 text-accent-magenta',
  cyan: 'bg-accent-cyan/20 text-accent-cyan',
  orange: 'bg-accent-orange/20 text-accent-orange',
}

export function Badge({ children, variant = 'default', className = '' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${variantStyles[variant]} ${className}`}>
      {children}
    </span>
  )
}
