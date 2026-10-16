# Bouncer frontend

Vite + React + Cytoscape.js. Pages: install feed, check (verdict + evidence graph), campaigns, investigate, results.

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Settings come from the repo-root `.env` (`envDir: '..'`):

- `VITE_USE_MOCKS=true` serves every page from `contracts/mocks/`. Set it to `false` once the API is live (H4).
- `VITE_API_URL` is the API base URL (default `http://localhost:8000`).

All API calls live in `src/api.js`, with one function per endpoint from `contracts/api.md`. The evidence graph
(`src/components/EvidenceGraph.jsx`) works like this:

- Node colour shows status and node shape shows type.
- The `route` is drawn thick in the accent colour.
- `common_infra` nodes are dashed and faded.
- Graphs over 80 nodes show only the route and its 1-hop neighbours, with a toggle for the full graph.
