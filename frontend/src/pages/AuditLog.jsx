import { useEffect, useState } from 'react'
import { api, fmtDateTime } from '../api.js'

const PAGE = 100
const ACTIONS = [
  'login', 'login_failed', 'login_blocked', 'logout', 'password_changed',
  'user_created', 'user_updated', 'user_deactivated',
  'task_created', 'task_updated', 'task_deleted', 'comment_added', 'criterion_updated',
]

export default function AuditLog() {
  const [action, setAction] = useState('')
  const [email, setEmail] = useState('')
  const [offset, setOffset] = useState(0)
  const [data, setData] = useState({ items: [], total: 0 })
  const [error, setError] = useState('')

  useEffect(() => {
    const p = new URLSearchParams({ limit: PAGE, offset })
    if (action) p.set('action', action)
    if (email) p.set('user_email', email)
    api.get(`/audit?${p}`).then(setData).catch((e) => setError(e.message))
  }, [action, email, offset])

  return (
    <div className="stack">
      <div className="toolbar">
        <h2 className="section-title">Audit log</h2>
        <select value={action} onChange={(e) => { setAction(e.target.value); setOffset(0) }}
          aria-label="Action">
          <option value="">All actions</option>
          {ACTIONS.map((a) => <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>)}
        </select>
        <input className="search" placeholder="Filter by email…" value={email}
          onChange={(e) => { setEmail(e.target.value); setOffset(0) }} />
      </div>
      <div className="muted small">
        Every sign-in, failed sign-in and change is recorded here and can't be edited from the app.
      </div>
      {error && <div className="error">{error}</div>}
      <div className="card">
        <table className="task-table audit-table">
          <thead>
            <tr><th>When</th><th>Who</th><th>Action</th><th>Target</th><th>Details</th><th>IP</th></tr>
          </thead>
          <tbody>
            {data.items.map((r) => (
              <tr key={r.id} className={r.action.startsWith('login_') ? 'row-warn' : ''}>
                <td className="small nowrap">{fmtDateTime(r.at)}</td>
                <td className="small">{r.user_email || '—'}</td>
                <td className="small">{r.action.replace(/_/g, ' ')}</td>
                <td className="small">
                  {r.entity_type === 'task' && r.entity_id
                    ? <a href={`#/tasks?open=${r.entity_id}`}>task #{r.entity_id}</a>
                    : r.entity_type ? `${r.entity_type} #${r.entity_id ?? ''}` : ''}
                </td>
                <td className="small mono">{r.details === '{}' ? '' : r.details}</td>
                <td className="small mono">{r.ip}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="row gap pager">
          <button className="btn" disabled={offset === 0} onClick={() => setOffset(offset - PAGE)}>Newer</button>
          <span className="muted small">
            {data.total ? `${offset + 1}–${Math.min(offset + PAGE, data.total)} of ${data.total}` : 'No entries'}
          </span>
          <button className="btn" disabled={offset + PAGE >= data.total}
            onClick={() => setOffset(offset + PAGE)}>Older</button>
        </div>
      </div>
    </div>
  )
}
