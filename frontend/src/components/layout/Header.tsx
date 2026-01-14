import { Link, useLocation } from 'react-router-dom'

interface NavLinkProps {
  to: string
  children: React.ReactNode
}

function NavLink({ to, children }: NavLinkProps) {
  const location = useLocation()
  const isActive = location.pathname === to ||
    (to !== '/' && location.pathname.startsWith(to))

  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        isActive
          ? 'text-accent-cyan bg-bg-highlight'
          : 'text-fg-secondary hover:text-accent-blue hover:bg-bg-secondary'
      }`}
    >
      {children}
    </Link>
  )
}

export function Header() {
  return (
    <header className="bg-bg-primary border-b border-bg-highlight sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <div className="w-8 h-8 bg-accent-magenta/20 rounded-lg flex items-center justify-center">
              <span className="text-accent-magenta font-bold">CH</span>
            </div>
            <span className="text-fg-primary font-bold text-lg hidden sm:block">
              Clockwork Hamlet
            </span>
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            <NavLink to="/">Home</NavLink>
            <NavLink to="/about">About</NavLink>
            <NavLink to="/feed">Live Feed</NavLink>
            <NavLink to="/agents">Agents</NavLink>
            <NavLink to="/relationships">Relationships</NavLink>
            <NavLink to="/map">Map</NavLink>
            <NavLink to="/digest">Digest</NavLink>
          </nav>

          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse" />
            <span className="text-fg-dim text-xs hidden sm:block">Live</span>
          </div>
        </div>
      </div>
    </header>
  )
}
