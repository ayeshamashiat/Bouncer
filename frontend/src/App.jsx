import { useEffect, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { API_URL, USE_MOCKS, getHealth } from './api.js'
import Feed from './pages/Feed.jsx'
import Verdict from './pages/Verdict.jsx'
import Campaigns from './pages/Campaigns.jsx'
import Investigate from './pages/Investigate.jsx'
import Results from './pages/Results.jsx'
import Landing from './pages/Landing.jsx'
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

// New page: start at the top. A #hash (like /#install): scroll to it once the page has rendered.
function useScrollOnNavigate(pathname, hash) {
  useEffect(() => {
    if (!hash) {
      window.scrollTo(0, 0)
      return undefined
    }
    const t = setTimeout(() => document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: 'smooth' }), 60)
    return () => clearTimeout(t)
  }, [pathname, hash])
}

export default function App() {
  const api = useApiStatus()
  const { pathname, hash } = useLocation()
  const isLanding = pathname === '/'
  useScrollOnNavigate(pathname, hash)
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
          <NavLink to="/" end>Overview</NavLink>
          <NavLink to="/feed">Install feed</NavLink>
          <NavLink to="/check">Check</NavLink>
          <NavLink to="/campaigns">Campaigns</NavLink>
          <NavLink to="/investigate">Investigate</NavLink>
          <NavLink to="/results">Results</NavLink>
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
      <main className={`main${isLanding ? ' main-landing' : ''}`}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/feed" element={<Feed />} />
          <Route path="/check" element={<Verdict />} />
          <Route path="/check/:name" element={<Verdict />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/investigate" element={<Investigate />} />
          <Route path="/results" element={<Results />} />
          <Route path="/about" element={<Navigate to="/" replace />} />
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
            <NavLink to="/" end>Overview</NavLink>
            <a href="/#install">Install</a>
            {LINKS.repo && <a href={LINKS.repo} target="_blank" rel="noreferrer">GitHub</a>}
            {LINKS.video && <a href={LINKS.video} target="_blank" rel="noreferrer">Demo video</a>}
            {LINKS.post && <a href={LINKS.post} target="_blank" rel="noreferrer">Write-up</a>}
            <a href={LINKS.hackathon} target="_blank" rel="noreferrer">Graph Hacks 2026</a>
          </nav>
        </div>
        <div className="footer-fine">Built on FalkorDB by Ayesha Mashiat and Mrittika Jahan. Demo data is partly synthetic.</div>
      </footer>
    </div>
  )
}
