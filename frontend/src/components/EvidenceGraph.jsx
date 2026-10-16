// Evidence graph (Cytoscape). Nodes coloured by status, shaped by type; the route drawn thicker
// in the accent colour; supernodes (common_infra) dashed and faded. Labels are shown exactly as
// received from the API (already defanged).
import { useEffect, useMemo, useRef, useState } from 'react'
import cytoscape from 'cytoscape'

const SHAPES = {
  Skill: 'ellipse',
  Publisher: 'round-rectangle',
  Domain: 'diamond',
  IP: 'hexagon',
  PayloadString: 'tag',
  Campaign: 'star',
}

const CLUTTER_LIMIT = 80 // more nodes than this: show route + 1-hop neighbours unless toggled

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}

function useColorScheme() {
  const [dark, setDark] = useState(() => window.matchMedia('(prefers-color-scheme: dark)').matches)
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = (e) => setDark(e.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return dark
}

// Route edges = consecutive ids in the route, in either direction.
function routeEdgeKeys(route) {
  const keys = new Set()
  for (let i = 0; i < route.length - 1; i++) {
    keys.add(`${route[i]}|${route[i + 1]}`)
    keys.add(`${route[i + 1]}|${route[i]}`)
  }
  return keys
}

function trimToRoute(nodes, edges, route) {
  const keep = new Set(route)
  for (const e of edges) {
    if (keep.has(e.source) || keep.has(e.target)) {
      keep.add(e.source)
      keep.add(e.target)
    }
  }
  return {
    nodes: nodes.filter((n) => keep.has(n.id)),
    edges: edges.filter((e) => keep.has(e.source) && keep.has(e.target)),
  }
}

export default function EvidenceGraph({ nodes = [], edges = [], route = [], height = 460, onNodeClick }) {
  const ref = useRef(null)
  const dark = useColorScheme()
  const [showAll, setShowAll] = useState(false)
  const tooBig = nodes.length > CLUTTER_LIMIT && route.length > 0

  const shown = useMemo(() => {
    const ids = new Set(nodes.map((n) => n.id))
    const validEdges = edges.filter((e) => ids.has(e.source) && ids.has(e.target))
    return tooBig && !showAll ? trimToRoute(nodes, validEdges, route) : { nodes, edges: validEdges }
  }, [nodes, edges, route, tooBig, showAll])

  useEffect(() => {
    if (!ref.current) return
    const onRoute = new Set(route)
    const routeEdges = routeEdgeKeys(route)
    const c = {
      bad: cssVar('--bad'),
      unknown: cssVar('--unknown'),
      trusted: cssVar('--ok'),
      infra: cssVar('--infra'),
      accent: cssVar('--accent'),
      edge: cssVar('--edge'),
      text: cssVar('--text'),
      bg: cssVar('--surface'),
    }
    const colourOf = (n) =>
      n.status === 'known_bad' ? c.bad : n.status === 'trusted' ? c.trusted : n.status === 'unknown' ? c.unknown : c.infra

    const elements = [
      ...shown.nodes.map((n) => ({
        data: {
          id: n.id,
          label: n.label,
          shape: SHAPES[n.type] || 'ellipse',
          colour: colourOf(n),
        },
        classes: [n.common_infra ? 'common' : '', onRoute.has(n.id) ? 'route' : '', n.id === route[0] ? 'start' : '']
          .filter(Boolean)
          .join(' '),
      })),
      ...shown.edges.map((e, i) => ({
        data: { id: `e${i}`, source: e.source, target: e.target, label: e.type },
        classes: routeEdges.has(`${e.source}|${e.target}`) ? 'route' : '',
      })),
    ]

    const cy = cytoscape({
      container: ref.current,
      elements,
      wheelSensitivity: 0.2,
      minZoom: 0.2,
      maxZoom: 3,
      style: [
        {
          selector: 'node',
          style: {
            shape: 'data(shape)',
            'background-color': 'data(colour)',
            label: 'data(label)',
            color: c.text,
            'font-size': 10,
            'font-family': 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'text-background-color': c.bg,
            'text-background-opacity': 0.85,
            'text-background-padding': 2,
            width: 22,
            height: 22,
            'border-width': 2,
            'border-color': c.bg,
          },
        },
        { selector: 'node.route', style: { width: 30, height: 30, 'border-color': c.accent, 'border-width': 3, 'font-weight': 700, 'z-index': 10 } },
        { selector: 'node.start', style: { width: 36, height: 36, 'font-size': 12 } },
        { selector: 'node.common', style: { opacity: 0.4, 'border-style': 'dashed', 'border-color': c.text, 'border-width': 2 } },
        {
          selector: 'edge',
          style: {
            width: 1.2,
            'line-color': c.edge,
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'target-arrow-color': c.edge,
            'arrow-scale': 0.7,
          },
        },
        {
          selector: 'edge.route',
          style: {
            width: 4,
            'line-color': c.accent,
            'target-arrow-color': c.accent,
            label: 'data(label)',
            'font-size': 9,
            color: c.accent,
            'text-rotation': 'autorotate',
            'text-background-color': c.bg,
            'text-background-opacity': 1,
            'text-background-padding': 2,
            'z-index': 9,
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        randomize: false,
        nodeRepulsion: () => 9000,
        idealEdgeLength: () => 70,
        padding: 30,
      },
    })
    if (onNodeClick) cy.on('tap', 'node', (evt) => onNodeClick(evt.target.id()))
    return () => cy.destroy()
  }, [shown, route, dark, onNodeClick])

  if (!nodes.length) return <div className="state state-empty">No graph evidence for this item.</div>

  return (
    <div className="graph-wrap">
      {tooBig && (
        <div className="graph-toolbar">
          <span>
            Showing {shown.nodes.length} of {nodes.length} nodes
          </span>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowAll((s) => !s)}>
            {showAll ? 'Show route + neighbours only' : 'Show full graph'}
          </button>
        </div>
      )}
      <div ref={ref} className="graph" style={{ height }} aria-label="Evidence graph" role="img" />
      <Legend />
    </div>
  )
}

function Swatch({ cls, shape }) {
  return <span className={`swatch ${cls} shape-${shape}`} aria-hidden="true" />
}

export function Legend() {
  return (
    <div className="legend">
      <div className="legend-group">
        <span className="legend-title">Status</span>
        <span><Swatch cls="c-bad" shape="circle" /> known bad</span>
        <span><Swatch cls="c-unknown" shape="circle" /> unknown</span>
        <span><Swatch cls="c-ok" shape="circle" /> trusted</span>
        <span><Swatch cls="c-infra" shape="circle" /> infrastructure</span>
      </div>
      <div className="legend-group">
        <span className="legend-title">Type</span>
        <span><Swatch cls="c-neutral" shape="circle" /> Skill</span>
        <span><Swatch cls="c-neutral" shape="rect" /> Publisher</span>
        <span><Swatch cls="c-neutral" shape="diamond" /> Domain</span>
        <span><Swatch cls="c-neutral" shape="hex" /> IP</span>
        <span><Swatch cls="c-neutral" shape="tag" /> Payload</span>
      </div>
      <div className="legend-group">
        <span className="legend-title">Lines</span>
        <span><span className="line line-route" aria-hidden="true" /> evidence route</span>
        <span><Swatch cls="c-neutral common" shape="circle" /> shared infra (ignored)</span>
      </div>
    </div>
  )
}
