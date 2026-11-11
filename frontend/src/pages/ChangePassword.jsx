import { useState } from 'react'
import { api } from '../api.js'

export default function ChangePassword({ forced, onDone, onCancel }) {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (next !== confirm) return setError("The new passwords don't match.")
    setBusy(true)
    setError('')
    try {
      onDone(await api.post('/auth/change-password', {
        current_password: current, new_password: next,
      }))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="center-screen">
      <form className="card auth-card" onSubmit={submit}>
        <h2>{forced ? 'Set your password' : 'Change password'}</h2>
        {forced && (
          <p className="muted">
            You signed in with a temporary password. Choose your own to continue. Use at least
            12 characters; a passphrase from your password manager is best.
          </p>
        )}
        <label>
          Current password
          <input type="password" autoComplete="current-password" value={current} required
            autoFocus onChange={(e) => setCurrent(e.target.value)} />
        </label>
        <label>
          New password
          <input type="password" autoComplete="new-password" minLength={12} value={next} required
            onChange={(e) => setNext(e.target.value)} />
        </label>
        <label>
          Confirm new password
          <input type="password" autoComplete="new-password" minLength={12} value={confirm}
            required onChange={(e) => setConfirm(e.target.value)} />
        </label>
        {error && <div className="error">{error}</div>}
        <div className="row gap">
          <button className="btn primary" disabled={busy}>Save password</button>
          {!forced && <button type="button" className="btn" onClick={onCancel}>Cancel</button>}
        </div>
      </form>
    </div>
  )
}
