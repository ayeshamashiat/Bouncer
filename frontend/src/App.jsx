import { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import { API_URL, USE_MOCKS, getHealth } from './api.js'
import Feed from './pages/Feed.jsx'
import Verdict from './pages/Verdict.jsx'
import Campaigns from './pages/Campaigns.jsx'
import Investigate from './pages/Investigate.jsx'
import Results from './pages/Results.jsx'
import About from './pages/About.jsx'
import { GitHubIcon } from './components/common.jsx'
import { LINKS } from './links.js'

function useApiStatus() {
  const [status, setStatus] = useState({ ok: true, nodes: null })
  useEffect(() => {
    let alive = true
    const ping = () =>
      getHealth()
        .then((h) => alive && setStatus({ ok: true, nodes: h.nodes }))
        .catch(() => alive && setStatus({ ok: false, nodes: null }))
    ping()
    const t = setInterval(ping, 10000)
    return () => {
      alive = false
      clearInterval(t)
    }
  }, [])
  return status
}

export default function App() {
  const api = useApiStatus()
  return (
    <div className="app">
      <header className="topbar">
        <NavLink to="/" className="brand">
          <svg viewBox="0 0 32 32" width="22" height="22" aria-hidden="true">
            <path d="M16 2 4 7v8c0 7 5 13 12 15 7-2 12-8 12-15V7z" fill="currentColor" />
          </svg>
          Bouncer
        </NavLink>
        <nav className="nav">
          <NavLink to="/" end>Install feed</NavLink>
          <NavLink to="/check">Check</NavLink>
          <NavLink to="/campaigns">Campaigns</NavLink>
          <NavLink to="/investigate">Investigate</NavLink>
          <NavLink to="/results">Results</NavLink>
          <NavLink to="/about">About</NavLink>
        </nav>
        <div className="status">
          {USE_MOCKS ? (
            <span className="pill pill-mock" title="VITE_USE_MOCKS=true">Mock data</span>
          ) : (
            <span className={`pill ${api.ok ? 'pill-ok' : 'pill-bad'}`}>
              {api.ok ? `Live · ${api.nodes ?? '?'} nodes` : 'API offline'}
            </span>
          )}
          {LINKS.repo && (
            <a href={LINKS.repo} className="icon-link" target="_blank" rel="noreferrer" aria-label="Source code on GitHub" title="Source code on GitHub">
              <GitHubIcon size={18} />
            </a>
          )}
        </div>
      </header>
      {!api.ok && !USE_MOCKS && (
        <div className="banner" role="alert">
          Cannot reach the Bouncer API at <code>{API_URL}</code>. Start it with{' '}
          <code>uvicorn api:app --reload</code> in <code>backend/</code>, or set <code>VITE_USE_MOCKS=true</code>.
        </div>
      )}
      <main className="main">
        <Routes>
          <Route path="/" element={<Feed />} />
          <Route path="/check" element={<Verdict />} />
          <Route path="/check/:name" element={<Verdict />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/investigate" element={<Investigate />} />
          <Route path="/results" element={<Results />} />
          <Route path="/about" element={<About />} />
          <Route path="*" element={<p className="muted">Page not found.</p>} />
        </Routes>
      </main>
      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <b>Bouncer</b>
            <span>Attackers work in campaigns. Your agent's defences should too.</span>
          </div>
          <nav className="footer-links">
            <NavLink to="/about">About</NavLink>
            {LINKS.repo && <a href={LINKS.repo} target="_blank" rel="noreferrer">GitHub</a>}
            {LINKS.video && <a href={LINKS.video} target="_blank" rel="noreferrer">Demo video</a>}
            {LINKS.post && <a href={LINKS.post} target="_blank" rel="noreferrer">Write-up</a>}
            <a href={LINKS.hackathon} target="_blank" rel="noreferrer">Graph Hacks 2026</a>
          </nav>
        </div>
        <div className="footer-fine">Built on FalkorDB by Ayesha Mashiat and Mrittika Jahan. Demo data is partly synthetic; see About.</div>
      </footer>
    </div>
  )
}
