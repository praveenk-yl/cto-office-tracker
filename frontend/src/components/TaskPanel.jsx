import { useEffect, useState } from 'react'
import { api, fmtDateTime, PRIORITIES, STATUSES, STATUS_LABEL } from '../api.js'

const FIELD_LABEL = {
  title: 'title', description: 'description', phase_id: 'phase', workstream_id: 'workstream',
  owner_id: 'owner', status: 'status', priority: 'priority', due_date: 'due date',
}

function describe(entry, meta) {
  let d = {}
  try { d = JSON.parse(entry.details || '{}') } catch { /* ignore */ }
  const name = (field, v) => {
    if (v === null || v === undefined || v === '') return 'none'
    if (field === 'owner_id') return meta.users.find((u) => u.id === v)?.name || `user ${v}`
    if (field === 'phase_id') return meta.phases.find((p) => p.id === v)?.name || v
    if (field === 'workstream_id') return meta.workstreams.find((w) => w.id === v)?.name || v
    if (field === 'status') return STATUS_LABEL[v] || v
    return String(v)
  }
  switch (entry.action) {
    case 'task_created': return 'created the task'
    case 'comment_added': return 'added a comment'
    case 'task_updated':
      return Object.entries(d)
        .map(([f, c]) => (f === 'description' || f === 'title'
          ? `edited the ${FIELD_LABEL[f]}`
          : `changed ${FIELD_LABEL[f] || f} from ${name(f, c.from)} to ${name(f, c.to)}`))
        .join('; ')
    default: return entry.action.replace(/_/g, ' ')
  }
}

export default function TaskPanel({ task, defaults, meta, users, canEdit, isAdmin, onClose, onSaved, onDeleted }) {
  const isNew = !task
  const [form, setForm] = useState(() => ({
    title: task?.title ?? '',
    description: task?.description ?? '',
    phase_id: task?.phase_id ?? defaults.phase_id,
    workstream_id: task?.workstream_id ?? defaults.workstream_id,
    owner_id: task?.owner_id ?? null,
    status: task?.status ?? 'not_started',
    priority: task?.priority ?? 'medium',
    due_date: task?.due_date ?? (meta.phases.find((p) => p.id === defaults.phase_id)?.end_date || null),
  }))
  const [comments, setComments] = useState([])
  const [history, setHistory] = useState([])
  const [comment, setComment] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [savedAt, setSavedAt] = useState(null)

  const loadActivity = () => {
    if (isNew) return
    api.get(`/tasks/${task.id}/comments`).then(setComments).catch(() => {})
    api.get(`/tasks/${task.id}/history`).then(setHistory).catch(() => {})
  }
  useEffect(loadActivity, [task?.id]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const set = (k, num = false) => (e) => {
    const v = e.target.value
    setForm((f) => ({ ...f, [k]: v === '' ? null : num ? Number(v) : v }))
  }

  const dirty = isNew || Object.keys(form).some((k) => (form[k] ?? null) !== (task[k] ?? null))

  async function save(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const body = { ...form, title: form.title.trim(), description: form.description || '' }
      const saved = isNew
        ? await api.post('/tasks', body)
        : await api.patch(`/tasks/${task.id}`, body)
      onSaved(saved)
      setSavedAt(new Date())
      loadActivity()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function addComment(e) {
    e.preventDefault()
    if (!comment.trim()) return
    try {
      const c = await api.post(`/tasks/${task.id}/comments`, { body: comment })
      setComments((cs) => [...cs, c])
      setComment('')
      onSaved({ ...task, comment_count: (task.comment_count || 0) + 1 })
      loadActivity()
    } catch (err) {
      setError(err.message)
    }
  }

  async function remove() {
    if (!window.confirm('Delete this task? This cannot be undone.')) return
    try {
      await api.del(`/tasks/${task.id}`)
      onDeleted(task.id)
    } catch (err) {
      setError(err.message)
    }
  }

  const ro = !canEdit

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside className="panel" role="dialog" aria-label={isNew ? 'New task' : 'Task details'}>
        <div className="panel-head">
          <h2>{isNew ? 'New task' : 'Task'}</h2>
          <button className="btn-link" onClick={onClose} aria-label="Close">Close ✕</button>
        </div>
        <form className="stack" onSubmit={save}>
          <label>
            Title
            <textarea rows={2} value={form.title} required readOnly={ro} onChange={set('title')} />
          </label>
          <div className="grid-2">
            <label>
              Status
              <select value={form.status} disabled={ro} onChange={set('status')}>
                {STATUSES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
              </select>
            </label>
            <label>
              Owner
              <select value={form.owner_id ?? ''} disabled={ro} onChange={set('owner_id', true)}>
                <option value="">Unassigned</option>
                {users.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
                {form.owner_id && !users.some((u) => u.id === form.owner_id) && (
                  <option value={form.owner_id}>
                    {meta.users.find((u) => u.id === form.owner_id)?.name || 'Unknown'} (inactive)
                  </option>
                )}
              </select>
            </label>
            <label>
              Phase
              <select value={form.phase_id ?? ''} disabled={ro} onChange={set('phase_id', true)}>
                <option value="">No phase</option>
                {meta.phases.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </label>
            <label>
              Workstream
              <select value={form.workstream_id ?? ''} disabled={ro} onChange={set('workstream_id', true)}>
                <option value="">None</option>
                {meta.workstreams.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select>
            </label>
            <label>
              Priority
              <select value={form.priority} disabled={ro} onChange={set('priority')}>
                {PRIORITIES.map((p) => <option key={p} value={p}>{p[0].toUpperCase() + p.slice(1)}</option>)}
              </select>
            </label>
            <label>
              Due date
              <input type="date" value={form.due_date ?? ''} readOnly={ro} onChange={set('due_date')} />
            </label>
          </div>
          <label>
            Notes
            <textarea rows={5} value={form.description} readOnly={ro} onChange={set('description')}
              placeholder={ro ? '' : 'Details, links, decisions…'} />
          </label>
          {error && <div className="error">{error}</div>}
          {canEdit && (
            <div className="row gap">
              <button className="btn primary" disabled={busy || !dirty}>
                {isNew ? 'Create task' : 'Save changes'}
              </button>
              {savedAt && !dirty && <span className="muted small">Saved</span>}
              <div className="spacer" />
              {!isNew && isAdmin && (
                <button type="button" className="btn danger" onClick={remove}>Delete</button>
              )}
            </div>
          )}
        </form>

        {!isNew && (
          <>
            <h3 className="panel-sub">Comments</h3>
            <div className="stack">
              {comments.length === 0 && <div className="muted small">No comments yet.</div>}
              {comments.map((c) => (
                <div key={c.id} className="comment">
                  <div className="small"><strong>{c.user_name}</strong>{' '}
                    <span className="muted">{fmtDateTime(c.created_at)}</span></div>
                  <div className="comment-body">{c.body}</div>
                </div>
              ))}
              {canEdit && (
                <form onSubmit={addComment} className="stack">
                  <textarea rows={2} value={comment} placeholder="Add a comment…"
                    onChange={(e) => setComment(e.target.value)} />
                  <div><button className="btn" disabled={!comment.trim()}>Comment</button></div>
                </form>
              )}
            </div>

            <h3 className="panel-sub">History</h3>
            <ul className="history">
              {history.map((h) => (
                <li key={h.id} className="small">
                  <span className="muted">{fmtDateTime(h.at)}</span>{' '}
                  <strong>{h.user_email || 'system'}</strong>{' '}
                  {describe(h, meta)}
                </li>
              ))}
              {history.length === 0 && <li className="muted small">Seeded from the CTO office plan.</li>}
            </ul>
          </>
        )}
      </aside>
    </div>
  )
}
