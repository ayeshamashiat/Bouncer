// Campaigns: groups of skills linked by shared infrastructure (WCC), one card each.
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCampaigns, getNeighbourhood } from '../api.js'
import { Empty, ErrorState, Loading, idLabel } from '../components/common.jsx'
import EvidenceGraph from '../components/EvidenceGraph.jsx'

export default function Campaigns() {
  const [campaigns, setCampaigns] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)
  const [graph, setGraph] = useState({ loading: false, data: null, error: null })
  const navigate = useNavigate()

  const load = () => {
    setError(null)
    getCampaigns().then(setCampaigns).catch(setError)
  }
  useEffect(load, [])

  const open = (c) => {
    setSelected(c)
    const centre = c.shared_infra[0] || c.members[0]
    setGraph({ loading: true, data: null, error: null })
    getNeighbourhood(centre, 2)
      .then((data) => setGraph({ loading: false, data, error: null }))
      .catch((error) => setGraph({ loading: false, data: null, error }))
  }

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1>Campaigns</h1>
          <p className="muted">
            Skills that share publishers, servers or payloads form one campaign. Shared infrastructure such as github.com
            is ignored.
          </p>
        </div>
      </div>
      {error && <ErrorState error={error} onRetry={load} />}
      {!campaigns && !error && <Loading label="Finding campaigns…" />}
      {campaigns && campaigns.length === 0 && <Empty>No campaigns found in the graph.</Empty>}
      {campaigns && campaigns.length > 0 && (
        <div className="campaign-grid">
          {campaigns.map((c) => (
            <button
              key={c.campaign_id}
              className={`card campaign-card ${selected?.campaign_id === c.campaign_id ? 'selected' : ''}`}
              onClick={() => open(c)}
            >
              <div className="campaign-head">
                <h3>{c.name}</h3>
                <span className="muted small">#{c.campaign_id}</span>
              </div>
              <div className="campaign-stats">
                <div><span className="stat-n">{c.size}</span><span className="stat-l">skills</span></div>
                <div><span className="stat-n stat-bad">{c.known_bad}</span><span className="stat-l">known bad</span></div>
                <div><span className="stat-n">{c.shared_infra.length}</span><span className="stat-l">shared clues</span></div>
              </div>
              <div className="chips">
                {c.shared_infra.slice(0, 8).map((id) => (
                  <span key={id} className="chip chip-static mono" title={id}>
                    <span className="route-kind">{id.split(':')[0]}</span> {idLabel(id)}
                  </span>
                ))}
                {c.shared_infra.length > 8 && <span className="muted small">+{c.shared_infra.length - 8} more</span>}
              </div>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <section className="card">
          <h3 className="card-title">
            {selected.name}: neighbourhood of <span className="mono">{idLabel(selected.shared_infra[0] || selected.members[0])}</span>
          </h3>
          {graph.loading && <Loading label="Loading graph…" />}
          {graph.error && <ErrorState error={graph.error} onRetry={() => open(selected)} />}
          {graph.data && (
            <EvidenceGraph
              nodes={graph.data.nodes}
              edges={graph.data.edges}
              height={520}
              onNodeClick={(id) => id.startsWith('skill:') && navigate(`/check/${encodeURIComponent(id.slice(6))}`)}
            />
          )}
        </section>
      )}
    </div>
  )
}
