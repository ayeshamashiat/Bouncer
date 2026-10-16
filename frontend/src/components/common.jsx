// Small shared pieces: verdict badge, loading / error / empty states, time formatting.

export function VerdictBadge({ verdict, size = 'sm' }) {
  const v = (verdict || '').toUpperCase()
  const icon = { BLOCK: '⛔', ASK: '?', ALLOW: '✓' }[v] || ''
  // The word is always shown: colour is never the only signal.
  return (
    <span className={`badge badge-${v.toLowerCase()} badge-${size}`}>
      <span aria-hidden="true">{icon}</span> {v}
    </span>
  )
}

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="state" role="status">
      <span className="spinner" aria-hidden="true" /> {label}
    </div>
  )
}

export function ErrorState({ error, onRetry }) {
  return (
    <div className="state state-error" role="alert">
      <strong>{error?.code === 'not_found' ? 'Not found' : 'Something went wrong'}</strong>
      <span>{error?.message || String(error)}</span>
      {onRetry && (
        <button className="btn btn-ghost" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}

export function Empty({ children }) {
  return <div className="state state-empty">{children}</div>
}

export function formatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

// "skill:foo" -> "foo"
export function idLabel(id) {
  const i = id.indexOf(':')
  return i < 0 ? id : id.slice(i + 1)
}
