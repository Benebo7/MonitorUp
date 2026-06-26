import { useState, useEffect } from 'react'
import './Verify.css'

function Verify({ onVerified }) {
  const [status, setStatus] = useState('loading') // loading | success | error
  const [message, setMessage] = useState('')

  useEffect(() => {
    const token = new URLSearchParams(window.location.search).get('token')

    if (!token) {
      setStatus('error')
      setMessage('No verification token was found in the link.')
      return
    }

    fetch(`/auth/verify?token=${encodeURIComponent(token)}`, { credentials: 'include' })
      .then(async (res) => {
        const data = await res.json().catch(() => ({}))
        if (!res.ok) {
          setStatus('error')
          setMessage(data.detail || 'This verification link is invalid or has expired.')
          return
        }
        setStatus('success')
        if (data.access_token) {
          setTimeout(() => onVerified(data.access_token), 1800)
        }
      })
      .catch(() => {
        setStatus('error')
        setMessage('Could not reach the server. Please try again.')
      })
  }, [])

  return (
    <div className="verify-container">
      <div className="verify-card">
        <h1>Monitor<span>Up</span></h1>

        {status === 'loading' && (
          <>
            <div className="verify-spinner" />
            <p className="verify-text">Verifying your email…</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="verify-icon success">✓</div>
            <h2 className="verify-title">Email verified</h2>
            <p className="verify-text">All set! Taking you to your dashboard…</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="verify-icon error">✕</div>
            <h2 className="verify-title">Verification failed</h2>
            <p className="verify-text">{message}</p>
            <a className="verify-button" href="/">Back to login</a>
          </>
        )}
      </div>
    </div>
  )
}

export default Verify
