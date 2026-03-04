import { useState } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import './App.css'

function App() {
  const [token, setToken] = useState(localStorage.getItem('access_token'))

  const handleLogin = (accessToken) => {
    localStorage.setItem('access_token', accessToken)
    setToken(accessToken)
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    setToken(null)
  }

  if (!token) {
    return <Login onLogin={handleLogin} />
  }

  return <Dashboard token={token} onLogout={handleLogout} />
}

export default App
