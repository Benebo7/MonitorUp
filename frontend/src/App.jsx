import { useState, useEffect } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Verify from './pages/Verify'
import './App.css'

function App() {
  const [token, setToken] = useState(null)
  const [loading, setLoading] = useState(true)
  const isVerifyRoute = window.location.pathname === '/verify'

  useEffect(() => {
    if (isVerifyRoute) {
      setLoading(false)
      return
    }
    fetch('/auth/refresh', { method: 'POST', credentials: 'include' })
      .then(res => res.ok ? res.json() : null)
      .then(data => {
        if (data?.access_token) setToken(data.access_token)
      })
      .finally(() => setLoading(false))
  }, [])

  const handleLogin = (accessToken) => setToken(accessToken)

  const handleLogout = async () => {
    try {
      await fetch('/auth/logout', { method: 'POST', credentials: 'include' })
    } catch {
      // clear local state regardless
    }
    setToken(null)
  }

  if (loading) return null

  if (isVerifyRoute) {
    return <Verify onVerified={(accessToken) => {
      window.history.replaceState({}, '', '/')
      setToken(accessToken)
    }} />
  }

  if (!token) return <Login onLogin={handleLogin} />

  return <Dashboard token={token} onLogout={handleLogout} />
}

export default App
