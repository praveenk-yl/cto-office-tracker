export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

let onUnauthorized = () => {}
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn
}

async function request(method, path, body) {
  const res = await fetch(`/api${path}`, {
    method,
    credentials: 'same-origin',
    headers: {
      'X-Requested-With': 'tracker',
      ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    let msg = data.detail
    if (Array.isArray(msg)) msg = msg.map((d) => d.msg).join('; ')
    if (res.status === 401 && !path.startsWith('/auth/login')) onUnauthorized()
    throw new ApiError(res.status, msg || `Request failed (${res.status})`)
  }
  return data
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, b = {}) => request('POST', p, b),
  patch: (p, b) => request('PATCH', p, b),
  del: (p) => request('DELETE', p),
}

export const STATUSES = [
  { key: 'not_started', label: 'Not started' },
  { key: 'in_progress', label: 'In progress' },
  { key: 'blocked', label: 'Blocked' },
  { key: 'done', label: 'Done' },
]
export const STATUS_LABEL = Object.fromEntries(STATUSES.map((s) => [s.key, s.label]))
export const PRIORITIES = ['high', 'medium', 'low']

export function todayISO() {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export function isOverdue(task) {
  return task.status !== 'done' && task.due_date && task.due_date < todayISO()
}

export function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso.length === 10 ? iso + 'T00:00:00' : iso + (iso.endsWith('Z') ? '' : 'Z'))
  return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export function fmtDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z')
  return d.toLocaleString(undefined, {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}
