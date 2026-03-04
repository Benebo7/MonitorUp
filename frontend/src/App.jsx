import { useState, useEffect } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import './App.css'

function App() {
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data?.access_token) setToken(data.access_token)
      })
      .finally(() => setLoading(false))
  }, [])

  const handleLogin = (accessToken) => setToken(accessToken)

  const handleLogout = () => setToken(null)

  if (loading) return null

  if (!token) return <Login onLogin={handleLogin} />

  return <Dashboard token={token} onLogout={handleLogout} />
}

export default App
