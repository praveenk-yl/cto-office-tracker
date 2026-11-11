import { STATUS_LABEL } from '../api.js'

export function Progress({ value }) {
  return (
    <div className="progress" role="progressbar" aria-valuenow={value} aria-valuemin={0}
      aria-valuemax={100}>
      <div className="progress-fill" style={{ width: `${value}%` }} />
    </div>
  )
}

export function StatusPill({ status, label }) {
  return <span className={`pill status-${status}`}>{label || STATUS_LABEL[status]}</span>
}

export function PriorityTag({ priority }) {
  return <span className={`prio prio-${priority}`}>{priority}</span>
}
