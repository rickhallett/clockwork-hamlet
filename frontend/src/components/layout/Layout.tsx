import { Outlet } from 'react-router-dom'
import { Header } from './Header'

export function Layout() {
  return (
    <div className="min-h-screen bg-bg-primary text-fg-primary font-mono">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
      <footer className="border-t border-bg-highlight py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-fg-dim text-sm text-center">
            Clockwork Hamlet - AI Village Simulation
          </p>
        </div>
      </footer>
    </div>
  )
}
