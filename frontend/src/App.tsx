import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'

function Home() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-accent-blue mb-4">Clockwork Hamlet</h1>
      <p className="text-fg-secondary mb-4">
        A persistent, multi-agent village simulation where AI-driven characters
        live, interact, and create emergent narratives.
      </p>
      <div className="terminal p-4">
        <p className="text-fg-dim">[System] Simulation initializing...</p>
        <p className="text-accent-green">[System] Ready.</p>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-bg-primary text-fg-primary font-mono">
        <nav className="border-b border-bg-highlight p-4">
          <div className="flex gap-6">
            <Link to="/" className="text-accent-cyan hover:text-accent-blue transition-colors">
              Home
            </Link>
            <Link to="/feed" className="text-fg-secondary hover:text-accent-blue transition-colors">
              Live Feed
            </Link>
            <Link to="/agents" className="text-fg-secondary hover:text-accent-blue transition-colors">
              Agents
            </Link>
            <Link to="/relationships" className="text-fg-secondary hover:text-accent-blue transition-colors">
              Relationships
            </Link>
          </div>
        </nav>
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/feed" element={<div className="p-8">Live Feed (coming soon)</div>} />
            <Route path="/agents" element={<div className="p-8">Agents (coming soon)</div>} />
            <Route path="/relationships" element={<div className="p-8">Relationships (coming soon)</div>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
