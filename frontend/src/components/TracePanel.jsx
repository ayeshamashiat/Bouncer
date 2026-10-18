// "How the graph decided": every Cypher query one check ran, what it returned and how long it took.
// The steps come straight from the API (check_install records them as it runs), so this is the real work.
export default function TracePanel({ trace, open = false }) {
  if (!trace?.length) return null
  const total = trace.reduce((s, t) => s + (t.ms || 0), 0)
  return (
    <div className="trace">
      <div className="trace-head">
        <div className="eyebrow">How the graph decided</div>
        <span className="muted small">{trace.filter((t) => t.cypher).length} queries · {total.toFixed(1)} ms in FalkorDB</span>
      </div>
      <ol className="trace-steps">
        {trace.map((t, i) => (
          <li key={i} className={t.cypher ? '' : 'trace-rule'}>
            <details open={open && i === trace.length - 2}>
              <summary>
                <span className="trace-q">{t.query}</span>
                <span className="trace-r mono">{t.result}</span>
                {t.cypher ? <span className="trace-ms mono">{t.ms} ms</span> : <span />}
              </summary>
              {t.cypher && <pre className="trace-cypher"><code>{t.cypher}</code></pre>}
            </details>
          </li>
        ))}
      </ol>
    </div>
  )
}
