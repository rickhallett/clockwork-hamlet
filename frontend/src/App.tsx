import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components/layout'
import { Home, AgentList, AgentProfile, Relationships, LiveFeed } from './pages'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="feed" element={<LiveFeed />} />
          <Route path="agents" element={<AgentList />} />
          <Route path="agents/:agentId" element={<AgentProfile />} />
          <Route path="relationships" element={<Relationships />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
