import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout'
import { Home, About, AgentList, AgentProfile, Relationships, LiveFeed, Digest, Map, Dashboard } from './pages'
import { AuthProvider } from './context'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="about" element={<About />} />
            <Route path="feed" element={<LiveFeed />} />
            <Route path="agents" element={<AgentList />} />
            <Route path="agents/:agentId" element={<AgentProfile />} />
            <Route path="relationships" element={<Relationships />} />
            <Route path="digest" element={<Digest />} />
            <Route path="map" element={<Map />} />
            <Route path="dashboard" element={<Dashboard />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
