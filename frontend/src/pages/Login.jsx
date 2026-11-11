import { useState } from 'react'
import { api } from '../api.js'

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      onLogin(await api.post('/auth/login', { email, password }))
    } catch (err) {
      setError(err.message)
      setPassword('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="center-screen">
      <form className="card auth-card" onSubmit={submit}>
        <div className="brand auth-brand">
          <span className="brand-mark" aria-hidden="true" />
          CTO Office Tracker
        </div>
        <p className="muted">Sign in with the account your admin created for you.</p>
        <label>
          Email
          <input type="email" autoComplete="username" value={email} required autoFocus
            onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input type="password" autoComplete="current-password" value={password} required
            onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <div className="error">{error}</div>}
        <button className="btn primary" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  )
}
