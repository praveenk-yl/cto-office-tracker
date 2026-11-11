import { useEffect, useMemo, useState } from 'react'
import { api, fmtDate, isOverdue, STATUSES } from '../api.js'
import { PriorityTag, StatusPill } from '../components/bits.jsx'
import TaskPanel from '../components/TaskPanel.jsx'

function hashParams() {
  const q = window.location.hash.split('?')[1] || ''
  return Object.fromEntries(new URLSearchParams(q))
}

const EMPTY = { phase: '', workstream: '', status: '', owner: '', q: '' }

export default function Tasks({ meta, tasks, canEdit, isAdmin, onSaved, onDeleted }) {
  const [filters, setFilters] = useState(() => ({ ...EMPTY, ...hashParams() }))
  const [openId, setOpenId] = useState(() => {
    const id = Number(hashParams().open)
    return id || null
  })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    const on = () => {
      const p = hashParams()
      setFilters({ ...EMPTY, ...p })
      if (p.open) setOpenId(Number(p.open))
    }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])

  const set = (k) => (e) => setFilters((f) => ({ ...f, [k]: e.target.value }))
  const userName = Object.fromEntries(meta.users.map((u) => [u.id, u.name]))
  const wsName = Object.fromEntries(meta.workstreams.map((w) => [w.id, w.name]))
  const activeUsers = meta.users.filter((u) => u.is_active)

  const filtered = useMemo(() => {
    const q = filters.q.trim().toLowerCase()
    return tasks.filter(
      (t) =>
        (!filters.phase || String(t.phase_id) === filters.phase) &&
        (!filters.workstream || String(t.workstream_id) === filters.workstream) &&
        (!filters.status ||
          (filters.status === 'open' ? t.status !== 'done' :
            filters.status === 'overdue' ? isOverdue(t) : t.status === filters.status)) &&
        (!filters.owner ||
          (filters.owner === 'none' ? !t.owner_id : String(t.owner_id) === filters.owner)) &&
        (!q || t.title.toLowerCase().includes(q) || t.description.toLowerCase().includes(q)),
    )
  }, [tasks, filters])

  const groups = [
    ...meta.phases.map((p) => ({ key: p.id, title: `${p.name}: ${p.subtitle}`, phase: p })),
    { key: 'none', title: 'No phase', phase: null },
  ]
    .map((g) => ({
      ...g,
      items: filtered
        .filter((t) => (g.phase ? t.phase_id === g.phase.id : !t.phase_id))
        .sort((a, b) => a.sort - b.sort || a.id - b.id),
    }))
    .filter((g) => g.items.length)

  async function quickStatus(task, status) {
    onSaved(await api.patch(`/tasks/${task.id}`, { status }))
  }

  const hasFilters = Object.values(filters).some(Boolean)
  const openTask = tasks.find((t) => t.id === openId)

  return (
    <div className="stack">
      <div className="toolbar">
        <input className="search" placeholder="Search tasks…" value={filters.q} onChange={set('q')} />
        <select value={filters.phase} onChange={set('phase')} aria-label="Phase">
          <option value="">All phases</option>
          {meta.phases.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <select value={filters.workstream} onChange={set('workstream')} aria-label="Workstream">
          <option value="">All workstreams</option>
          {meta.workstreams.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
        <select value={filters.status} onChange={set('status')} aria-label="Status">
          <option value="">Any status</option>
          <option value="open">Not done</option>
          <option value="overdue">Overdue</option>
          {STATUSES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
        </select>
        <select value={filters.owner} onChange={set('owner')} aria-label="Owner">
          <option value="">Any owner</option>
          <option value="none">No owner</option>
          {meta.users.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
        </select>
        {hasFilters && (
          <button className="btn-link" onClick={() => {
            setFilters(EMPTY)
            window.history.replaceState(null, '', '#/tasks')
          }}>Clear</button>
        )}
        <div className="spacer" />
        {canEdit && (
          <button className="btn primary" onClick={() => setCreating(true)}>+ New task</button>
        )}
      </div>

      <div className="muted small">{filtered.length} of {tasks.length} tasks</div>

      {groups.map((g) => (
        <section key={g.key} className="card task-group">
          <h2 className="section-title">{g.title}</h2>
          <table className="task-table">
            <thead>
              <tr>
                <th className="col-status">Status</th>
                <th>Task</th>
                <th className="col-ws">Workstream</th>
                <th className="col-owner">Owner</th>
                <th className="col-prio">Priority</th>
                <th className="col-due">Due</th>
              </tr>
            </thead>
            <tbody>
              {g.items.map((t) => (
                <tr key={t.id} className={t.status === 'done' ? 'is-done' : ''}
                  onClick={() => setOpenId(t.id)}>
                  <td className="col-status" onClick={(e) => canEdit && e.stopPropagation()}>
                    {canEdit ? (
                      <select className={`status-select status-${t.status}`} value={t.status}
                        aria-label="Status" onChange={(e) => quickStatus(t, e.target.value)}>
                        {STATUSES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
                      </select>
                    ) : (
                      <StatusPill status={t.status} />
                    )}
                  </td>
                  <td className="col-title">
                    <span className="task-title">{t.title}</span>
                    {t.comment_count > 0 && (
                      <span className="muted small"> · {t.comment_count} comment{t.comment_count > 1 ? 's' : ''}</span>
                    )}
                  </td>
                  <td className="col-ws small">{wsName[t.workstream_id] || '—'}</td>
                  <td className="col-owner small">
                    {userName[t.owner_id] || <span className="muted">Unassigned</span>}
                  </td>
                  <td className="col-prio"><PriorityTag priority={t.priority} /></td>
                  <td className={`col-due small ${isOverdue(t) ? 'overdue' : ''}`}>
                    {fmtDate(t.due_date)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
      {groups.length === 0 && <div className="card muted">No tasks match these filters.</div>}

      {(openTask || creating) && (
        <TaskPanel
          key={creating ? 'new' : openTask.id}
          task={creating ? null : openTask}
          defaults={{
            phase_id: filters.phase ? Number(filters.phase) : meta.phases[0]?.id ?? null,
            workstream_id: filters.workstream ? Number(filters.workstream) : null,
          }}
          meta={meta}
          users={activeUsers}
          canEdit={canEdit}
          isAdmin={isAdmin}
          onClose={() => {
            setOpenId(null)
            setCreating(false)
            if (hashParams().open) window.history.replaceState(null, '', '#/tasks')
          }}
          onSaved={(t) => {
            onSaved(t)
            if (creating) {
              setCreating(false)
              setOpenId(t.id)
            }
          }}
          onDeleted={(id) => {
            onDeleted(id)
            setOpenId(null)
          }}
        />
      )}
    </div>
  )
}
