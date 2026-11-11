import { useEffect, useState } from 'react'
import { api, fmtDateTime } from '../api.js'

const ROLE_HELP = {
  admin: 'Everything, plus users, deleting tasks and the audit log',
  editor: 'Create and edit tasks, comment, tick exit criteria',
  viewer: 'Read only',
}

function randomPassword() {
  const chars = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  const buf = new Uint32Array(16)
  crypto.getRandomValues(buf)
  return Array.from(buf, (n) => chars[n % chars.length]).join('')
}

export default function Users({ me, onChanged }) {
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [form, setForm] = useState(null)
  const [notice, setNotice] = useState('')

  const load = () => api.get('/users').then(setUsers).catch((e) => setError(e.message))
  useEffect(() => { load() }, [])

  async function create(e) {
    e.preventDefault()
    setError('')
    try {
      await api.post('/users', form)
      setNotice(`Created ${form.email}. Share this temporary password over a private channel: ` +
        `${form.temporary_password} (they must change it at first sign-in).`)
      setForm(null)
      load()
      onChanged()
    } catch (err) {
      setError(err.message)
    }
  }

  async function update(u, body, msg) {
    setError('')
    try {
      await api.patch(`/users/${u.id}`, body)
      if (msg) setNotice(msg)
      load()
      onChanged()
    } catch (err) {
      setError(err.message)
    }
  }

  function resetPassword(u) {
    const pw = randomPassword()
    if (!window.confirm(`Reset ${u.name}'s password? They will be signed out everywhere.`)) return
    update(u, { temporary_password: pw },
      `New temporary password for ${u.email}: ${pw} (they must change it at next sign-in).`)
  }

  return (
    <div className="stack">
      <div className="toolbar">
        <h2 className="section-title">Users</h2>
        <div className="spacer" />
        <button className="btn primary" onClick={() => {
          setForm({ email: '', name: '', role: 'editor', temporary_password: randomPassword() })
          setNotice('')
        }}>+ Add user</button>
      </div>

      <div className="card muted small">
        Deactivate leavers here on their last day: it signs them out immediately. Changing a role
        or resetting a password also ends their current sessions.
      </div>

      {notice && <div className="notice">{notice}</div>}
      {error && <div className="error">{error}</div>}

      {form && (
        <form className="card stack" onSubmit={create}>
          <div className="grid-2">
            <label>
              Name
              <input value={form.name} required onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </label>
            <label>
              Work email
              <input type="email" value={form.email} required
                onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </label>
            <label>
              Role
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                {Object.keys(ROLE_HELP).map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
              <span className="muted small">{ROLE_HELP[form.role]}</span>
            </label>
            <label>
              Temporary password
              <input value={form.temporary_password} minLength={12} required
                onChange={(e) => setForm({ ...form, temporary_password: e.target.value })} />
            </label>
          </div>
          <div className="row gap">
            <button className="btn primary">Create user</button>
            <button type="button" className="btn" onClick={() => setForm(null)}>Cancel</button>
          </div>
        </form>
      )}

      <div className="card">
        <table className="task-table">
          <thead>
            <tr><th>Name</th><th>Email</th><th>Role</th><th>Last sign-in</th><th>Status</th><th /></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className={u.is_active ? '' : 'is-done'}>
                <td>{u.name}{u.id === me.id && <span className="muted"> (you)</span>}</td>
                <td className="small">{u.email}</td>
                <td>
                  <select value={u.role} disabled={u.id === me.id}
                    onChange={(e) => update(u, { role: e.target.value })}>
                    {Object.keys(ROLE_HELP).map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </td>
                <td className="small">{fmtDateTime(u.last_login_at)}</td>
                <td className="small">
                  {!u.is_active ? 'Deactivated' : u.must_change_password ? 'Awaiting first sign-in' : 'Active'}
                </td>
                <td className="row gap">
                  {u.id !== me.id && (
                    <>
                      <button className="btn-link" onClick={() => resetPassword(u)}>Reset password</button>
                      {u.is_active ? (
                        <button className="btn-link danger-text" onClick={() =>
                          window.confirm(`Deactivate ${u.name}? They will be signed out immediately.`) &&
                          update(u, { is_active: false })}>Deactivate</button>
                      ) : (
                        <button className="btn-link" onClick={() => update(u, { is_active: true })}>Reactivate</button>
                      )}
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
