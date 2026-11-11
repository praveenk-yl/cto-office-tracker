import { api, fmtDate, isOverdue, STATUS_LABEL } from '../api.js'
import { Progress, StatusPill } from '../components/bits.jsx'

function stats(list) {
  const done = list.filter((t) => t.status === 'done').length
  return {
    total: list.length,
    done,
    inProgress: list.filter((t) => t.status === 'in_progress').length,
    blocked: list.filter((t) => t.status === 'blocked').length,
    pct: list.length ? Math.round((done / list.length) * 100) : 0,
  }
}

export default function Dashboard({ meta, setMeta, tasks, canEdit }) {
  const all = stats(tasks)
  const overdue = tasks.filter(isOverdue)
  const blocked = tasks.filter((t) => t.status === 'blocked')
  const unowned = tasks.filter((t) => t.status !== 'done' && !t.owner_id)
  const userName = Object.fromEntries(meta.users.map((u) => [u.id, u.name]))
  const wsName = Object.fromEntries(meta.workstreams.map((w) => [w.id, w.name]))

  async function toggleCriterion(phaseId, crit) {
    const updated = await api.patch(`/criteria/${crit.id}`, { is_met: !crit.is_met })
    setMeta((m) => ({
      ...m,
      phases: m.phases.map((p) =>
        p.id !== phaseId
          ? p
          : { ...p, criteria: p.criteria.map((c) => (c.id === updated.id ? updated : c)) },
      ),
    }))
  }

  const attention = [
    ...blocked.map((t) => ({ t, why: 'Blocked' })),
    ...overdue.filter((t) => t.status !== 'blocked').map((t) => ({ t, why: 'Overdue' })),
  ]

  return (
    <div className="stack-lg">
      <section className="kpis">
        <div className="card kpi">
          <div className="kpi-label">Overall progress</div>
          <div className="kpi-value">{all.pct}%</div>
          <Progress value={all.pct} />
          <div className="muted small">{all.done} of {all.total} tasks done</div>
        </div>
        <div className="card kpi">
          <div className="kpi-label">In progress</div>
          <div className="kpi-value">{all.inProgress}</div>
        </div>
        <div className={`card kpi ${blocked.length ? 'kpi-warn' : ''}`}>
          <div className="kpi-label">Blocked</div>
          <div className="kpi-value">{blocked.length}</div>
        </div>
        <div className={`card kpi ${overdue.length ? 'kpi-bad' : ''}`}>
          <div className="kpi-label">Overdue</div>
          <div className="kpi-value">{overdue.length}</div>
        </div>
        <div className="card kpi">
          <div className="kpi-label">Open with no owner</div>
          <div className="kpi-value">{unowned.length}</div>
        </div>
      </section>

      <section>
        <h2 className="section-title">30/60/90-day roadmap</h2>
        <p className="muted small">
          Each phase has a gate: don't move on until its exit criteria are met.
        </p>
        <div className="phase-grid">
          {meta.phases.map((p) => {
            const s = stats(tasks.filter((t) => t.phase_id === p.id))
            const met = p.criteria.filter((c) => c.is_met).length
            return (
              <div key={p.id} className="card phase-card">
                <div className="phase-head">
                  <div>
                    <div className="phase-name">{p.name}</div>
                    <div className="muted">{p.subtitle}</div>
                  </div>
                  <div className="phase-due muted small">Ends {fmtDate(p.end_date)}</div>
                </div>
                <div className="row between small">
                  <span>{s.done}/{s.total} tasks done</span>
                  <span className="muted">{s.pct}%</span>
                </div>
                <Progress value={s.pct} />
                <div className="criteria">
                  <div className="criteria-head small">
                    Exit criteria <span className="muted">({met}/{p.criteria.length} met)</span>
                  </div>
                  {p.criteria.map((c) => (
                    <label key={c.id} className={`criterion ${c.is_met ? 'met' : ''}`}>
                      <input type="checkbox" checked={c.is_met} disabled={!canEdit}
                        onChange={() => toggleCriterion(p.id, c)} />
                      {c.text}
                    </label>
                  ))}
                </div>
                <a className="small" href={`#/tasks?phase=${p.id}`}>View tasks →</a>
              </div>
            )
          })}
        </div>
      </section>

      <div className="two-col">
        <section className="card">
          <h2 className="section-title">Workstreams</h2>
          <div className="stack">
            {meta.workstreams.map((w) => {
              const s = stats(tasks.filter((t) => t.workstream_id === w.id))
              return (
                <a key={w.id} className="ws-row" href={`#/tasks?workstream=${w.id}`}>
                  <div className="row between">
                    <span className="ws-name">{w.name}</span>
                    <span className="muted small">
                      {s.done}/{s.total}
                      {s.blocked ? ` · ${s.blocked} blocked` : ''}
                    </span>
                  </div>
                  <Progress value={s.pct} />
                </a>
              )
            })}
          </div>
        </section>

        <section className="card">
          <h2 className="section-title">Needs attention</h2>
          {attention.length === 0 ? (
            <p className="muted">Nothing blocked or overdue.</p>
          ) : (
            <ul className="attention">
              {attention.map(({ t, why }) => (
                <li key={t.id}>
                  <a href={`#/tasks?open=${t.id}`}>{t.title}</a>
                  <div className="muted small">
                    <StatusPill status={t.status} label={why === 'Overdue' ? `Overdue · due ${fmtDate(t.due_date)}` : STATUS_LABEL[t.status]} />
                    {' '}{wsName[t.workstream_id] || ''} · {userName[t.owner_id] || 'No owner'}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
