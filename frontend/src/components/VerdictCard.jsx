import { Link } from 'react-router-dom'
import { VerdictBadge, formatDateTime, idLabel } from './common.jsx'
import TracePanel from './TracePanel.jsx'

export default function VerdictCard({ result, name }) {
  const v = result.verdict.toLowerCase()
  // older API responses have no `rule`: fall back to the route shape
  const rule = result.rule || (result.route.length <= 1 && result.verdict === 'ASK' ? 'never_seen' : '')
  const trustedPub = rule === 'trusted_publisher'
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
      {rule === 'never_seen' && <p className="muted">Never seen before. Unknown is not the same as safe, so a human decides.</p>}
      {rule === 'no_track_record' && (
        <p className="muted">No link to known malware, but no track record either. Finding nothing bad isn't proof of safety, so a human decides.</p>
      )}
      {trustedPub && (
        <p className="muted">Allowed on reputation: its publisher has a history of community-vetted skills. Trust only ever turns ASK into ALLOW; a link to malware would still block it.</p>
      )}
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
        <ol className={`route${trustedPub ? ' route-trust' : ''}`} aria-label={trustedPub ? 'Track record' : 'Evidence route'}>
          {result.route.map((id) => (
            <li key={id}>
              <span className="route-kind">{id.split(':')[0]}</span>
              <span className="mono">{idLabel(id)}</span>
            </li>
          ))}
        </ol>
      )}
      <TracePanel trace={result.trace} />
      {result.route.length > 1 && (
        <Link to={`/graph?skill=${encodeURIComponent(name)}`} className="small map-link">See this path on the whole graph →</Link>
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
