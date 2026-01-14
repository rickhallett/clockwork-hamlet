import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout'
import { Home, About, AgentList, AgentProfile, Relationships, LiveFeed, Digest, Map } from './pages'

function App() {
  return (
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
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
