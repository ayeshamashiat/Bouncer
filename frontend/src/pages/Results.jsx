// Results: hold-out evaluation. Hide 30% of the malicious labels, then see what each method catches.
import { useEffect, useState } from 'react'
import { getEval } from '../api.js'
import { ErrorState, Loading } from '../components/common.jsx'

const pct = (x) => `${Math.round(x * 100)}%`

export default function Results() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const load = () => {
    setError(null)
    getEval().then(setData).catch(setError)
  }
  useEffect(load, [])

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Results</h1>
          <p className="muted">
            Method: we hide the malicious label on a random 30% of campaign skills, then ask each method to find them
            again. Five random splits; caught means the graph links it to known malware.
          </p>
        </div>
      </div>
      {error && <ErrorState error={error} onRetry={load} />}
      {!data && !error && <Loading label="Loading evaluation…" />}
      {data && (
        <>
          {data._note && <div className="banner banner-soft">Placeholder numbers: {data._note}</div>}
          <div className="stat-row">
            <div className="card stat"><span className="stat-big">{pct(data.recall)}</span><span className="stat-l">hidden malicious skills caught by Bouncer</span></div>
            <div className="card stat"><span className="stat-big">{pct(data.blocklist_recall)}</span><span className="stat-l">caught by a blocklist</span></div>
            <div className="card stat"><span className="stat-big">{pct(data.false_alarm_rate)}</span><span className="stat-l">false alarms on legitimate skills</span></div>
            <div className="card stat"><span className="stat-big">{data.avg_ms} ms</span><span className="stat-l">average per check</span></div>
          </div>

          <section className="card">
            <h3 className="card-title">Hidden malicious skills caught</h3>
            <div className="bars">
              <Bar label="Blocklist / name match" value={data.blocklist_recall} cls="bar-muted" />
              <Bar label="Bouncer (graph)" value={data.recall} cls="bar-accent" />
            </div>
            {data.held_rate != null && (
              <p className="muted small">
                The other {pct(data.held_rate)} had no link to malware, but no track record either, so they were
                held for a human (ASK). Let through: {pct(data.allowed_rate ?? 0)}.
              </p>
            )}
          </section>

          <section className="card table-card">
            <table className="table">
              <thead>
                <tr>
                  <th>Seed</th><th>Hidden</th><th>Blocklist caught</th><th>Bouncer caught</th><th>Held</th><th>Legit</th><th>False alarms</th>
                </tr>
              </thead>
              <tbody>
                {data.splits.map((s) => (
                  <tr key={s.seed}>
                    <td>{s.seed}</td><td>{s.hidden}</td><td>{s.blocklist_caught}</td>
                    <td>{s.graph_caught}</td><td>{s.held ?? '—'}</td><td>{s.legit}</td><td>{s.false_alarms}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  )
}

function Bar({ label, value, cls }) {
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track" role="img" aria-label={`${label}: ${pct(value)}`}>
        <div className={`bar-fill ${cls}`} style={{ width: `${Math.max(value * 100, 0.5)}%` }} />
      </div>
      <span className="bar-value">{pct(value)}</span>
    </div>
  )
}
