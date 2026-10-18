// Graph map: the whole FalkorDB evidence graph on one screen. Type a skill and Bouncer runs a real
// check; the evidence path it found lights up across the map, with the queries that found it.
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import cytoscape from 'cytoscape'
import { checkItem, getGraphMap } from '../api.js'
import { ErrorState, Loading, VerdictBadge } from '../components/common.jsx'
import TracePanel from '../components/TracePanel.jsx'

const SHAPES = { Skill: 'ellipse', Publisher: 'round-rectangle', Domain: 'diamond', IP: 'hexagon', PayloadString: 'tag' }
const TRY = ['demo-crypto-tracker', 'demo-git-tools', 'solana-wallet-tracker']

function colour(n) {
  if (n.common_infra) return '#d4d4d8'
  if (n.type === 'Skill') return n.status === 'known_bad' ? '#dc2626' : n.status === 'trusted' ? '#16a34a' : '#a1a1aa'
  return '#8aa0c4'
}

export default function GraphMap() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [params, setParams] = useSearchParams()
  const [q, setQ] = useState(params.get('skill') || '')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const ref = useRef(null)
  const cy = useRef(null)

  useEffect(() => {
    getGraphMap().then(setData).catch(setError)
  }, [])

  const stats = useMemo(() => {
    if (!data) return null
    const by = (t) => data.nodes.filter((n) => n.type === t).length
    return {
      bad: data.nodes.filter((n) => n.status === 'known_bad').length,
      trusted: data.nodes.filter((n) => n.status === 'trusted').length,
      publishers: by('Publisher'), infra: by('Domain') + by('IP') + by('PayloadString'),
      edges: data.edges.length,
    }
  }, [data])

  useEffect(() => {
    if (!data || !ref.current) return undefined
    const degree = {}
    data.edges.forEach((e) => { degree[e.source] = (degree[e.source] || 0) + 1; degree[e.target] = (degree[e.target] || 0) + 1 })
    const inst = cytoscape({
      container: ref.current,
      elements: [
        ...data.nodes.map((n) => ({
          data: { id: n.id, label: n.label, colour: colour(n), shape: SHAPES[n.type] || 'ellipse',
                  hub: n.type !== 'Skill' && (degree[n.id] || 0) >= 6 && !n.common_infra ? 1 : 0 },
          classes: n.common_infra ? 'common' : '',
        })),
        ...data.edges.map((e, i) => ({ data: { id: `e${i}`, source: e.source, target: e.target } })),
      ],
      style: [
        { selector: 'node', style: { 'background-color': 'data(colour)', shape: 'data(shape)', width: 9, height: 9,
          'border-width': 0, label: '', 'font-family': 'Geist Mono, monospace' } },
        { selector: 'node[hub = 1]', style: { width: 18, height: 18, label: 'data(label)', 'font-size': 11, color: '#3f3f46',
          'text-valign': 'top', 'text-margin-y': -4, 'text-background-color': '#fff', 'text-background-opacity': 0.8,
          'text-background-padding': 2 } },
        { selector: 'node.common', style: { opacity: 0.35 } },
        { selector: 'edge', style: { width: 0.6, 'line-color': '#e4e4e7', 'curve-style': 'haystack' } },
        { selector: '.dim', style: { opacity: 0.12 } },
        { selector: 'node.hit', style: { width: 26, height: 26, label: 'data(label)', 'font-size': 13, 'font-weight': 700,
          'border-width': 3, 'border-color': '#2563eb', opacity: 1, 'z-index': 20, color: '#18181b',
          'text-background-color': '#fff', 'text-background-opacity': 1, 'text-background-padding': 3 } },
        { selector: 'edge.hit', style: { width: 4, 'line-color': '#2563eb', opacity: 1, 'z-index': 19, 'curve-style': 'straight' } },
      ],
      layout: { name: 'cose', animate: false, randomize: true, nodeRepulsion: () => 9000, idealEdgeLength: () => 30,
                gravity: 0.6, numIter: 1200, nodeDimensionsIncludeLabels: false },
      wheelSensitivity: 0.25,
      minZoom: 0.05,
    })
    cy.current = inst
    return () => inst.destroy()
  }, [data])

  // run a real check and light its path up on the map
  const trace = (name) => {
    const n = (name ?? q).trim()
    if (!n) return
    setQ(n)
    setParams({ skill: n }, { replace: true })
    setBusy(true)
    checkItem(n)
      .then((r) => {
        setResult({ name: n, ...r })
        const c = cy.current
        if (!c) return
        c.elements().removeClass('hit').addClass('dim')
        const ids = new Set(r.route)
        const hit = c.nodes().filter((x) => ids.has(x.id()))
        hit.removeClass('dim').addClass('hit')
        for (let i = 0; i + 1 < r.route.length; i++) {
          c.edges().filter((e) => (e.source().id() === r.route[i] && e.target().id() === r.route[i + 1]) ||
            (e.target().id() === r.route[i] && e.source().id() === r.route[i + 1])).removeClass('dim').addClass('hit')
        }
        // the result panel opens next to the map and narrows it: resize first, then zoom to the path
        if (hit.length) setTimeout(() => { c.resize(); c.animate({ fit: { eles: hit, padding: 130 } }, { duration: 900 }) }, 80)
      })
      .catch(setError)
      .finally(() => setBusy(false))
  }

  // a ?skill= link traces straight away once the map is drawn
  useEffect(() => {
    const s = params.get('skill')
    if (data && s) setTimeout(() => trace(s), 300)
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps

  const reset = () => {
    setResult(null)
    setParams({}, { replace: true })
    cy.current?.elements().removeClass('dim hit')
    setTimeout(() => { cy.current?.resize(); cy.current?.animate({ fit: { padding: 20 } }, { duration: 600 }) }, 80)
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Graph map</h1>
          <p className="muted">
            Everything Bouncer knows, live from FalkorDB: every skill, account, server, IP and payload, and how they
            connect. Type a skill to watch the graph find its evidence path.
          </p>
        </div>
      </div>

      <form className="map-search" onSubmit={(e) => { e.preventDefault(); trace() }}>
        <input id="mapq" className="input mono" value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="skill name, e.g. demo-crypto-tracker" aria-label="Skill to trace" />
        <button className="btn btn-primary" disabled={busy || !q.trim()}>{busy ? 'Tracing…' : 'Trace path'}</button>
        {result && <button type="button" className="btn btn-ghost" onClick={reset}>Show all</button>}
      </form>
      <div className="chips">
        <span className="muted small">Try:</span>
        {TRY.map((t) => <button key={t} type="button" className="chip" onClick={() => trace(t)}>{t}</button>)}
      </div>

      {error && <ErrorState error={error} />}
      {!data && !error && <Loading label="Loading the whole graph…" />}
      {data && (
        <div className="map-wrap">
          <div className="card map-card">
            <div ref={ref} className="map-canvas" role="img" aria-label="The whole threat graph" />
            {stats && (
              <div className="map-stats">
                <span><i style={{ background: '#dc2626' }} />{stats.bad} malicious skills</span>
                <span><i style={{ background: '#16a34a' }} />{stats.trusted} vetted skills</span>
                <span><i className="sq" style={{ background: '#8aa0c4' }} />{stats.publishers} accounts · {stats.infra} servers, IPs, payloads</span>
                <span className="muted">{data.nodes.length} nodes · {stats.edges} edges</span>
              </div>
            )}
          </div>
          {result && (
            <aside className="card map-result">
              <div className="verdict-head">
                <div>
                  <div className="eyebrow">Traced</div>
                  <h2 className="mono">{result.name}</h2>
                </div>
                <VerdictBadge verdict={result.verdict} />
              </div>
              <p className="verdict-reason small">{result.reason}</p>
              <TracePanel trace={result.trace} open />
              <Link to={`/check/${encodeURIComponent(result.name)}`} className="small">Full verdict →</Link>
            </aside>
          )}
        </div>
      )}
    </div>
  )
}
