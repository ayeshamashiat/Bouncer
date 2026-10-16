// Investigate: paste an unknown skill's SKILL.md. The investigator extracts facts into a fixed shape,
// writes them into the graph, and the rules (not the AI) decide the verdict.
import { useState } from 'react'
import { investigate } from '../api.js'
import { ErrorState, Loading } from '../components/common.jsx'
import EvidenceGraph from '../components/EvidenceGraph.jsx'
import VerdictCard from '../components/VerdictCard.jsx'
import pdfHelperText from '../../../data/sample/demo/demo-pdf-helper.md?raw'

const FACT_GROUPS = [
  ['domains', 'Domains'],
  ['urls', 'URLs'],
  ['ips', 'IPs'],
  ['commands', 'Commands'],
]

export default function Investigate() {
  const [name, setName] = useState('')
  const [text, setText] = useState('')
  const [state, setState] = useState({ loading: false, data: null, error: null })

  const run = (e) => {
    e?.preventDefault()
    if (!name.trim() || !text.trim()) return
    setState({ loading: true, data: null, error: null })
    investigate(name.trim(), text)
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((error) => setState({ loading: false, data: null, error }))
  }

  const loadExample = () => {
    setName('demo-pdf-helper')
    setText(pdfHelperText)
  }

  const r = state.data?.result

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Investigate an unknown skill</h1>
          <p className="muted">
            Bouncer reads the text safely. It never fetches or runs anything, extracts the clues and links them into the
            threat graph.
          </p>
        </div>
      </div>

      <form className="card investigate-form" onSubmit={run}>
        <div className="field">
          <label htmlFor="inv-name">Skill name</label>
          <input id="inv-name" className="input mono" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="demo-pdf-helper" spellCheck="false" />
        </div>
        <div className="field">
          <label htmlFor="inv-text">SKILL.md contents</label>
          <textarea id="inv-text" className="input mono textarea" value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Paste the skill's SKILL.md here" spellCheck="false" />
        </div>
        <div className="form-actions">
          <button type="button" className="btn btn-ghost" onClick={loadExample}>Load demo example</button>
          <button type="submit" className="btn btn-primary" disabled={!name.trim() || !text.trim() || state.loading}>
            Investigate
          </button>
        </div>
        <p className="notice">The text cannot change the verdict; rules decide.</p>
      </form>

      {state.loading && <Loading label="Extracting facts…" />}
      {state.error && <ErrorState error={state.error} onRetry={run} />}
      {state.data && (
        <>
          <section className="card">
            <h3 className="card-title">
              Extracted facts{' '}
              <span className="muted small">
                (+{state.data.added.nodes} nodes, +{state.data.added.edges} edges written to the graph)
              </span>
            </h3>
            <div className="fact-groups">
              {FACT_GROUPS.map(([key, label]) => (
                <div key={key} className="fact-group">
                  <div className="eyebrow">{label}</div>
                  <div className="chips">
                    {state.data.facts[key].length === 0 && <span className="muted small">none</span>}
                    {state.data.facts[key].map((f) => (
                      <span key={f} className="chip chip-static mono">{f}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
          <div className="verdict-layout">
            <VerdictCard result={r} name={name} />
            <section className="card">
              <h3 className="card-title">Evidence graph</h3>
              <EvidenceGraph nodes={r.evidence.nodes} edges={r.evidence.edges} route={r.route} />
            </section>
          </div>
        </>
      )}
    </div>
  )
}
