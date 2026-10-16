// Install feed: every check (from the hook, the MCP server or this UI), newest first, polled every 3 s.
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getDecisions } from '../api.js'
import { Empty, ErrorState, Loading, VerdictBadge, formatTime } from '../components/common.jsx'

const POLL_MS = 3000

export default function Feed() {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    let alive = true
    const load = () =>
      getDecisions(50)
        .then((d) => {
          if (!alive) return
          setRows(d)
          setError(null)
        })
        .catch((e) => alive && setError(e))
    load()
    const t = setInterval(load, POLL_MS)
    return () => {
      alive = false
      clearInterval(t)
    }
  }, [])

  const counts = (rows || []).reduce((acc, r) => ({ ...acc, [r.verdict]: (acc[r.verdict] || 0) + 1 }), {})

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Install feed</h1>
          <p className="muted">Every install your agents tried, and what Bouncer decided. Updates every 3 seconds.</p>
        </div>
        {rows && (
          <div className="counters">
            {['BLOCK', 'ASK', 'ALLOW'].map((v) => (
              <div key={v} className={`counter counter-${v.toLowerCase()}`}>
                <span className="counter-n">{counts[v] || 0}</span>
                <VerdictBadge verdict={v} />
              </div>
            ))}
          </div>
        )}
      </div>

      {error && !rows && <ErrorState error={error} />}
      {error && rows && <p className="muted small">Last refresh failed: {error.message}. Showing the previous data.</p>}
      {!rows && !error && <Loading label="Loading decisions…" />}
      {rows && rows.length === 0 && (
        <Empty>No installs checked yet. Try one on the <Link to="/check">Check</Link> page or run the hook in Claude Code.</Empty>
      )}
      {rows && rows.length > 0 && (
        <div className="card table-card">
          <table className="table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Item</th>
                <th>Kind</th>
                <th>Verdict</th>
                <th className="col-reason">Reason</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.id}
                  tabIndex={0}
                  className="clickable"
                  onClick={() => navigate(`/check/${encodeURIComponent(r.name)}`)}
                  onKeyDown={(e) => e.key === 'Enter' && navigate(`/check/${encodeURIComponent(r.name)}`)}
                >
                  <td className="mono nowrap">{formatTime(r.checked_at)}</td>
                  <td className="mono">{r.name}</td>
                  <td>{r.kind}</td>
                  <td><VerdictBadge verdict={r.verdict} /></td>
                  <td className="col-reason"><span className="one-line" title={r.reason}>{r.reason}</span></td>
                  <td><span className={`source source-${r.source}`}>{r.source}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
