import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuthContext } from '../../context'

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

function LoginModal({ onClose }: { onClose: () => void }) {
  const { login, register, error, isLoading, clearError } = useAuthContext()
  const [isRegister, setIsRegister] = useState(false)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    let success: boolean
    if (isRegister) {
      success = await register(username, email, password)
    } else {
      success = await login(username, password)
    }
    if (success) {
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-bg-secondary border border-bg-highlight rounded-lg p-6 w-96 max-w-full mx-4" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-bold text-fg-primary mb-4">
          {isRegister ? 'Create Account' : 'Sign In'}
        </h2>

        {error && (
          <div className="bg-accent-red/10 border border-accent-red/30 rounded px-3 py-2 mb-4">
            <span className="text-sm text-accent-red">{error}</span>
            <button onClick={clearError} className="ml-2 text-accent-red hover:text-accent-red/80">×</button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-fg-secondary mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-bg-highlight border border-bg-highlight rounded px-3 py-2 text-fg-primary focus:outline-none focus:border-accent-blue"
              required
            />
          </div>

          {isRegister && (
            <div>
              <label className="block text-sm text-fg-secondary mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-bg-highlight border border-bg-highlight rounded px-3 py-2 text-fg-primary focus:outline-none focus:border-accent-blue"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-sm text-fg-secondary mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-bg-highlight border border-bg-highlight rounded px-3 py-2 text-fg-primary focus:outline-none focus:border-accent-blue"
              required
              minLength={8}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-accent-blue hover:bg-accent-blue/80 disabled:bg-bg-highlight disabled:text-fg-dim px-4 py-2 rounded text-sm font-medium transition-colors"
          >
            {isLoading ? 'Loading...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => setIsRegister(!isRegister)}
            className="text-sm text-accent-blue hover:text-accent-cyan"
          >
            {isRegister ? 'Already have an account? Sign in' : "Don't have an account? Create one"}
          </button>
        </div>
      </div>
    </div>
  )
}

export function Header() {
  const { user, isAuthenticated, logout } = useAuthContext()
  const [showLoginModal, setShowLoginModal] = useState(false)

  return (
    <>
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
              <NavLink to="/dashboard">Dashboard</NavLink>
            </nav>

            {/* User / Auth section */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-accent-green rounded-full animate-pulse" />
                <span className="text-fg-dim text-xs hidden sm:block">Live</span>
              </div>

              {isAuthenticated && user ? (
                <div className="flex items-center gap-2">
                  <span className="text-fg-secondary text-sm hidden sm:block">{user.username}</span>
                  <button
                    onClick={logout}
                    className="text-fg-dim hover:text-accent-red text-sm"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="text-accent-blue hover:text-accent-cyan text-sm"
                >
                  Sign In
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {showLoginModal && <LoginModal onClose={() => setShowLoginModal(false)} />}
    </>
  )
}
