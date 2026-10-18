// About: what Bouncer is, how it decides, how to plug it in, who built it. For first-time visitors and judges.
import { Link } from 'react-router-dom'
import { LINKS } from '../links.js'
import { GitHubIcon } from '../components/common.jsx'

const RULES = [
  ['block', 'BLOCK', 'Directly shares an account, server, IP or malware marker with known malware', '2 steps away'],
  ['ask', 'ASK', 'Linked through one middle step, which could be coincidence', '3–4 steps away'],
  ['ask', 'ASK', "Never seen, or nothing vouches for it. Unknown isn't the same as safe", 'no record'],
  ['allow', 'ALLOW', 'No link to malware, and a track record: the skill or its publisher is community-vetted', 'trusted'],
]

const WAYS = [
  ['Claude Code hook', 'Enforcement', 'Runs before every shell command. Spots skill and MCP installs, and answers deny, ask or allow. The agent can’t skip it.'],
  ['MCP server', 'Consultation', 'Gives any agent check_install and explain_verdict, so it can ask before it chooses what to install.'],
  ['This website', 'Visibility', 'A live feed of every decision, the evidence graph behind each one, campaigns, and an investigator for unknown skills.'],
]

const STACK = ['FalkorDB 6.0.1', 'Cypher', 'WCC algorithm', 'FastAPI', 'React + Vite', 'Cytoscape.js', 'MCP', 'Claude Code hooks', 'Docker', 'Render']

export default function About() {
  return (
    <div className="page about">
      <section className="about-hero">
        <div className="eyebrow">Graph Hacks 2026 · Agents That Act on Connected Data</div>
        <h1 className="about-title">A bouncer for your AI agent’s installs.</h1>
        <p className="about-lede">
          AI agents install skills and MCP servers on their own. In January 2026 the ClawHavoc campaign put
          1,184 malicious skills on ClawHub. Every skill looked new, but they came from 12 accounts and talked to
          one server. Bouncer keeps those connections in a FalkorDB graph and checks every install against them, in
          milliseconds, with the path that proves the verdict.
        </p>
        <div className="about-actions">
          <Link to="/check/demo-crypto-tracker" className="btn btn-primary">See a block</Link>
          {LINKS.repo && (
            <a href={LINKS.repo} className="btn btn-ghost btn-icon" target="_blank" rel="noreferrer">
              <GitHubIcon /> Source on GitHub
            </a>
          )}
          {LINKS.video && <a href={LINKS.video} className="btn btn-ghost" target="_blank" rel="noreferrer">Watch the demo</a>}
          {LINKS.post && <a href={LINKS.post} className="btn btn-ghost" target="_blank" rel="noreferrer">Read the write-up</a>}
        </div>
      </section>

      <section className="about-grid">
        <div className="card about-stat"><span className="stat-big">95%</span><span className="stat-l">hidden malicious skills linked back to their campaign</span></div>
        <div className="card about-stat"><span className="stat-big">0%</span><span className="stat-l">caught by a blocklist on the same test</span></div>
        <div className="card about-stat"><span className="stat-big">~5 ms</span><span className="stat-l">per check, with the evidence path</span></div>
      </section>

      <section className="card">
        <h3 className="card-title">How it decides</h3>
        <p className="muted small about-note">
          It searches the graph for a path from the new skill to known malware. Sites everyone uses, like github.com,
          are ignored as evidence. The rules decide, never an AI, and bad evidence always beats trust.
        </p>
        <ul className="rule-list">
          {RULES.map(([cls, verdict, what, when], i) => (
            <li key={i}>
              <span className={`badge badge-sm badge-${cls}`}>{verdict}</span>
              <span>{what}</span>
              <span className="muted small nowrap">{when}</span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="about-h">Three ways in, one graph</h3>
        <div className="about-grid">
          {WAYS.map(([name, kind, text]) => (
            <div key={name} className="card about-way">
              <div className="eyebrow">{kind}</div>
              <h3>{name}</h3>
              <p className="muted small">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="about-grid about-grid-2">
        <div className="card">
          <h3 className="card-title">Built with</h3>
          <div className="chips">{STACK.map((s) => <span key={s} className="chip chip-static">{s}</span>)}</div>
        </div>
        <div className="card">
          <h3 className="card-title">Team</h3>
          <ul className="team">
            <li><span className="avatar">AM</span><div><b>Ayesha Mashiat</b><span className="muted small">Graph, backend, AI and integrations</span></div></li>
            <li><span className="avatar">MJ</span><div><b>Mrittika Jahan</b><span className="muted small">Threat data and frontend</span></div></li>
          </ul>
        </div>
      </section>

      <section className="card">
        <h3 className="card-title">About the data</h3>
        <p className="muted small about-note">
          Attacker accounts, servers, IPs and 23 skill names are real, from public reports by{' '}
          <a href="https://www.antiy.net/p/clawhavoc-analysis-of-large-scale-poisoning-campaign-targeting-the-openclaw-skill-market-for-ai-agents/" target="_blank" rel="noreferrer">Antiy CERT</a>,{' '}
          <a href="https://thehackernews.com/2026/02/researchers-find-341-malicious-clawhub.html" target="_blank" rel="noreferrer">The Hacker News</a> and{' '}
          <a href="https://www.koi.ai/blog/clawhavoc-341-malicious-clawedbot-skills-found-by-the-bot-they-were-targeting" target="_blank" rel="noreferrer">Koi Security</a>.
          The full list of malicious skills was taken down, so clearly labelled synthetic skills fill in the campaign
          on the real infrastructure. Every <span className="mono">demo-*</span> skill is synthetic. No malicious
          file was ever downloaded or run, and every indicator is stored defanged (<span className="mono">socifiapp[.]com</span>).
        </p>
      </section>
    </div>
  )
}
