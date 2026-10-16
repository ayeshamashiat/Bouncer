// Verdict page: search an item -> POST /api/check (source "ui") -> verdict card + evidence graph.
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { checkItem } from '../api.js'
import { ErrorState, Loading } from '../components/common.jsx'
import EvidenceGraph from '../components/EvidenceGraph.jsx'
import VerdictCard from '../components/VerdictCard.jsx'

const EXAMPLES = ['demo-crypto-tracker', 'demo-pdf-helper', 'demo-git-tools', 'solana-wallet-tracker']

export default function Verdict() {
  const { name } = useParams()
  const navigate = useNavigate()
  const [query, setQuery] = useState(name || '')
  const [state, setState] = useState({ loading: false, result: null, error: null })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    setQuery(name || '')
    if (!name) {
      setState({ loading: false, result: null, error: null })
      return
    }
    let alive = true
    setState({ loading: true, result: null, error: null })
    checkItem(name)
      .then((result) => alive && setState({ loading: false, result, error: null }))
      .catch((error) => alive && setState({ loading: false, result: null, error }))
    return () => {
      alive = false
    }
  }, [name, attempt])

  const submit = (e) => {
    e.preventDefault()
    const q = query.trim()
    if (!q) return
    if (q === name) setAttempt((a) => a + 1)
    else navigate(`/check/${encodeURIComponent(q)}`)
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Check an install</h1>
          <p className="muted">Ask Bouncer about any skill name. The verdict comes with the graph path that proves it.</p>
        </div>
      </div>

      <form className="search" onSubmit={submit} role="search">
        <label htmlFor="q" className="sr-only">Skill name</label>
        <input
          id="q"
          className="input mono"
          placeholder="skill name, e.g. demo-crypto-tracker"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoComplete="off"
          spellCheck="false"
        />
        <button className="btn btn-primary" type="submit" disabled={!query.trim() || state.loading}>
          Check
        </button>
      </form>
      <div className="examples">
        <span className="muted small">Try:</span>
        {EXAMPLES.map((ex) => (
          <button key={ex} className="chip" onClick={() => navigate(`/check/${ex}`)}>
            {ex}
          </button>
        ))}
      </div>

      {state.loading && <Loading label={`Checking ${name}…`} />}
      {state.error && <ErrorState error={state.error} onRetry={() => setAttempt((a) => a + 1)} />}
      {state.result && (
        <div className="verdict-layout">
          <VerdictCard result={state.result} name={name} />
          <section className="card">
            <h3 className="card-title">Evidence graph</h3>
            <EvidenceGraph
              nodes={state.result.evidence.nodes}
              edges={state.result.evidence.edges}
              route={state.result.route}
              onNodeClick={(id) => id.startsWith('skill:') && navigate(`/check/${encodeURIComponent(id.slice(6))}`)}
            />
          </section>
        </div>
      )}
      {!name && !state.loading && (
        <div className="state state-empty">Enter a skill name above to see its verdict.</div>
      )}
    </div>
  )
}
