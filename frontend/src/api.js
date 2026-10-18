// One function per endpoint (contracts/api.md). With VITE_USE_MOCKS=true every function
// returns the matching file from contracts/mocks/ instead of calling the API.
import mockHealth from '../../contracts/mocks/health.json'
import mockBlock from '../../contracts/mocks/check_block.json'
import mockAsk from '../../contracts/mocks/check_ask.json'
import mockAllow from '../../contracts/mocks/check_allow.json'
import mockDecisions from '../../contracts/mocks/decisions.json'
import mockNeighbourhood from '../../contracts/mocks/neighbourhood.json'
import mockCampaigns from '../../contracts/mocks/campaigns.json'
import mockInvestigate from '../../contracts/mocks/investigate.json'
import mockEval from '../../contracts/mocks/eval.json'

export const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
export const USE_MOCKS = String(import.meta.env.VITE_USE_MOCKS ?? 'true').toLowerCase() === 'true'

export class ApiError extends Error {
  constructor(code, message, status) {
    super(message)
    this.code = code
    this.status = status
  }
}

const delay = (value) => new Promise((resolve) => setTimeout(() => resolve(structuredClone(value)), 250))

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    })
  } catch {
    throw new ApiError('unreachable', `Cannot reach the Bouncer API at ${API_URL}`, 0)
  }
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const err = body?.error || {}
    throw new ApiError(err.code || 'http_error', err.message || `HTTP ${res.status}`, res.status)
  }
  return body
}

// In mock mode, pick the mock that matches the demo story for this name.
function mockCheck(name) {
  const n = name.toLowerCase()
  if (n.includes('git') || n.includes('weather')) return mockAllow
  if (n.includes('pdf')) return mockAsk
  return mockBlock
}

export function getHealth() {
  return USE_MOCKS ? delay(mockHealth) : request('/api/health')
}

export function checkItem(name, kind = 'skill') {
  if (USE_MOCKS) return delay(mockCheck(name))
  return request('/api/check', { method: 'POST', body: JSON.stringify({ kind, name, source: 'ui' }) })
}

export function getDecisions(limit = 50) {
  return USE_MOCKS ? delay(mockDecisions) : request(`/api/decisions?limit=${limit}`)
}

export function getNeighbourhood(name, hops = 2) {
  if (USE_MOCKS) return delay(mockNeighbourhood)
  return request(`/api/graph/neighbourhood?name=${encodeURIComponent(name)}&hops=${hops}`)
}

export function getCampaigns() {
  return USE_MOCKS ? delay(mockCampaigns) : request('/api/campaigns')
}

export function investigate(name, text) {
  if (USE_MOCKS) return delay(mockInvestigate)
  return request('/api/investigate', { method: 'POST', body: JSON.stringify({ name, text }) })
}

// The whole evidence graph. Mock mode has no full graph, so it shows the BLOCK example's evidence.
export function getGraphMap() {
  return USE_MOCKS ? delay(mockBlock.evidence) : request('/api/graph/map')
}

export function getEval() {
  return USE_MOCKS ? delay(mockEval) : request('/api/eval')
}
