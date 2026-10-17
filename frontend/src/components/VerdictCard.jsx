import { Link } from 'react-router-dom'
import { VerdictBadge, formatDateTime, idLabel } from './common.jsx'

export default function VerdictCard({ result, name }) {
  const v = result.verdict.toLowerCase()
  const neverSeen = result.route.length <= 1 && result.verdict === 'ASK'
  return (
    <section className={`card verdict-card verdict-${v}`} aria-live="polite">
      <div className="verdict-head">
        <div>
          <div className="eyebrow">Verdict for</div>
          <h2 className="mono">{name}</h2>
        </div>
        <VerdictBadge verdict={result.verdict} size="lg" />
      </div>
      <p className="verdict-reason">{result.reason}</p>
      {neverSeen && <p className="muted">Never seen before. Unknown is not the same as safe, so a human decides.</p>}
      <dl className="facts">
        <div>
          <dt>Campaign</dt>
          <dd>{result.campaign ? <Link to="/campaigns">{result.campaign}</Link> : '—'}</dd>
        </div>
        <div>
          <dt>Checked in</dt>
          <dd>{result.ms} ms</dd>
        </div>
        <div>
          <dt>Checked at</dt>
          <dd>{formatDateTime(result.checked_at)}</dd>
        </div>
      </dl>
      {result.route.length > 1 && (
        <ol className="route" aria-label="Evidence route">
          {result.route.map((id) => (
            <li key={id}>
              <span className="route-kind">{id.split(':')[0]}</span>
              <span className="mono">{idLabel(id)}</span>
            </li>
          ))}
        </ol>
      )}
      {result.alternatives?.length > 0 && (
        <div className="alternatives">
          <div className="eyebrow">Safer alternatives</div>
          <p className="muted small">Trusted skills in the same category that Bouncer checked and would allow.</p>
          <div className="chips">
            {result.alternatives.map((a) => (
              <Link key={a.name} to={`/check/${encodeURIComponent(a.name)}`} className="chip chip-alt" title={a.reason}>
                ✓ {a.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
