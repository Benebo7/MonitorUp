import { useState } from 'react'
import './Login.css'

function Login({ onLogin }) {
  const [isSignup, setIsSignup] = useState(false)
  const [user, setUser] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [emailSent, setEmailSent] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    const endpoint = isSignup ? '/auth/signup' : '/auth/login'
    const body = isSignup
      ? { user, email, password }
      : { email, password }

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(body),
      })

      const data = await res.json()

      if (!res.ok) {
        // Login blocked because the email isn't verified yet — a new link was sent.
        if (res.status === 401 && data.detail === 'Email not verified') {
          setEmailSent(true)
          return
        }
        setError(data.detail || 'Something went wrong')
        return
      }

      // Signup succeeds but returns no token (account needs verification first).
      if (data.access_token) {
        onLogin(data.access_token)
      } else {
        setEmailSent(true)
      }
    } catch (err) {
      setError('Connection failed')
    } finally {
      setLoading(false)
    }
  }

  if (emailSent) {
    return (
      <div className="login-container">
        <div className="login-card check-email">
          <div className="check-icon">✉</div>
          <h1>Check your email</h1>
          <p className="subtitle">
            We sent a verification link to <strong>{email}</strong>.
            Click it to activate your account.
          </p>
          <p className="hint">Didn't get it? Check your spam folder.</p>
          <p
            className="toggle"
            onClick={() => { setEmailSent(false); setIsSignup(false); setError('') }}
          >
            Back to login
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>MonitorUp</h1>
        <p className="subtitle">Uptime monitoring made simple</p>

        <form onSubmit={handleSubmit}>
          {isSignup && (
            <input
              type="text"
              placeholder="Username"
              value={user}
              onChange={(e) => setUser(e.target.value)}
              required
            />
          )}
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <p className="error">{error}</p>}

          <button type="submit" disabled={loading}>
            {loading ? 'Loading...' : isSignup ? 'Sign Up' : 'Log In'}
          </button>
        </form>

        <p className="toggle" onClick={() => { setIsSignup(!isSignup); setError('') }}>
          {isSignup ? 'Already have an account? Log in' : "Don't have an account? Sign up"}
        </p>
      </div>
    </div>
  )
}

export default Login
