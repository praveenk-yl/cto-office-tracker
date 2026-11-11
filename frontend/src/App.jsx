import { useCallback, useEffect, useState } from 'react'
import { api, setUnauthorizedHandler } from './api.js'
import Login from './pages/Login.jsx'
import ChangePassword from './pages/ChangePassword.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Tasks from './pages/Tasks.jsx'
import Users from './pages/Users.jsx'
import AuditLog from './pages/AuditLog.jsx'

function useHashRoute() {
  const read = () => window.location.hash.replace(/^#\/?/, '').split('?')[0] || 'dashboard'
  const [route, setRoute] = useState(read)
  useEffect(() => {
    const on = () => setRoute(read())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

export default function App() {
  const [user, setUser] = useState(undefined)
  const [meta, setMeta] = useState(null)
  const [tasks, setTasks] = useState(null)
  const [changingPassword, setChangingPassword] = useState(false)
  const route = useHashRoute()

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null))
    api.get('/auth/me').then(setUser).catch(() => setUser(null))
  }, [])

  const ready = user && !user.must_change_password

  const reload = useCallback(async () => {
    const [m, t] = await Promise.all([api.get('/meta'), api.get('/tasks')])
    setMeta(m)
    setTasks(t)
  }, [])

  useEffect(() => {
    if (ready) reload().catch(() => {})
    else {
      setMeta(null)
      setTasks(null)
    }
  }, [ready, reload])

  const upsertTask = (t) =>
    setTasks((prev) => {
      const i = prev.findIndex((x) => x.id === t.id)
      if (i === -1) return [...prev, t]
      const next = prev.slice()
      next[i] = t
      return next
    })
  const removeTask = (id) => setTasks((prev) => prev.filter((t) => t.id !== id))

  async function logout() {
    await api.post('/auth/logout').catch(() => {})
    setUser(null)
  }

  if (user === undefined) return <div className="center-screen muted">Loading…</div>
  if (user === null) return <Login onLogin={setUser} />
  if (user.must_change_password || changingPassword)
    return (
      <ChangePassword
        forced={user.must_change_password}
        onDone={(u) => {
          setUser(u)
          setChangingPassword(false)
        }}
        onCancel={() => setChangingPassword(false)}
      />
    )

  const canEdit = user.role === 'admin' || user.role === 'editor'
  const isAdmin = user.role === 'admin'
  const nav = [
    ['dashboard', 'Dashboard'],
    ['tasks', 'Tasks'],
    ...(isAdmin ? [['users', 'Users'], ['audit', 'Audit log']] : []),
  ]
  const page = nav.some(([k]) => k === route) ? route : 'dashboard'

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          CTO Office Tracker
        </div>
        <nav className="nav">
          {nav.map(([k, label]) => (
            <a key={k} href={`#/${k}`} className={page === k ? 'active' : ''}>
              {label}
            </a>
          ))}
        </nav>
        <div className="user-menu">
          <span className="user-name">
            {user.name} <span className="role-tag">{user.role}</span>
          </span>
          <button className="btn-link" onClick={() => setChangingPassword(true)}>
            Change password
          </button>
          <button className="btn-link" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <main className="main">
        {!meta || !tasks ? (
          <div className="muted">Loading…</div>
        ) : page === 'dashboard' ? (
          <Dashboard meta={meta} setMeta={setMeta} tasks={tasks} canEdit={canEdit} />
        ) : page === 'tasks' ? (
          <Tasks
            meta={meta}
            tasks={tasks}
            canEdit={canEdit}
            isAdmin={isAdmin}
            onSaved={upsertTask}
            onDeleted={removeTask}
          />
        ) : page === 'users' ? (
          <Users me={user} onChanged={reload} />
        ) : (
          <AuditLog />
        )}
      </main>
    </div>
  )
}
