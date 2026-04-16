import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Journal from './pages/Journal'
import History from './pages/History'
import Chat from './pages/Chat'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="journal"   element={<Journal />} />
          <Route path="history"   element={<History />} />
          <Route path="chat"      element={<Chat />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}