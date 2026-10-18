# Bouncer API contract (v1)

**Never change this alone.** A change = ONE commit that updates this file **and** the matching
files in `contracts/mocks/`, then a message to the other person.

Base URL: `http://localhost:8000` locally (`VITE_API_URL`). All responses are JSON.

## 1. Endpoints

| Method + path | Called by | Request | Response | Mock |
|---|---|---|---|---|
| `GET /api/health` | Both | – | `{"ok": true, "graph": "threat", "nodes": 1234}` | `health.json` |
| `POST /api/check` | Hook, MCP, UI | `{"kind", "name", "source"}` | CheckResponse | `check_block.json`, `check_ask.json`, `check_allow.json` |
| `GET /api/decisions?limit=50` | UI feed | query `limit` (1–500, default 50) | `[DecisionItem]`, newest first | `decisions.json` |
| `GET /api/graph/neighbourhood?name=X&hops=2` | UI graph | query `name`, `hops` (1–3) | `{"nodes": [Node], "edges": [Edge]}` (max 150 nodes) | `neighbourhood.json` |
| `GET /api/campaigns` | UI | – | `[Campaign]` | `campaigns.json` |
| `POST /api/investigate` | UI | `{"name", "text"}` | InvestigateResponse | `investigate.json` |
| `GET /api/eval` | UI | – | EvalResponse | `eval.json` |

Request details:
- `kind`: `skill` | `mcp` | `package`.
- `source`: `hook` | `mcp` | `ui`. May also be sent as header `X-Bouncer-Source`. Default `ui`.
- `name` for neighbourhood: a skill name, or any node id from a Node (`publisher:hightower6eu`, `domain:socifiapp[.]com`, ...).

## 2. Shared objects

```
Node   { "id": "skill:crypto-tracker-pro",   // prefix:value
         "label": "crypto-tracker-pro",      // display text, already defanged
         "type": "Skill",                    // see list below
         "status": "known_bad",              // see list below
         "common_infra": false }             // true = supernode: draw dashed + faded
       // id prefix: skill | publisher | domain | ip | payload | campaign
       // type:      Skill | Publisher | Domain | IP | PayloadString | Campaign
       // status:    known_bad | unknown | trusted | null (non-skills)

Edge   { "source": "skill:crypto-tracker-pro",
         "target": "publisher:hightower6eu",
         "type": "PUBLISHED_BY" }
       // type: PUBLISHED_BY | CONTACTS | RESOLVES_TO | DOWNLOADS_FROM | CONTAINS | PART_OF

DecisionItem { "id": "dec_0042", "kind": "skill", "name": "crypto-tracker-pro",
               "verdict": "BLOCK", "reason": "...", "campaign": "ClawHavoc",
               "source": "hook", "checked_at": "2026-10-16T10:22:05Z" }

Error  { "error": { "code": "not_found", "message": "No item named X" } }   // HTTP 400 / 404 / 500
```

## 3. Main responses

```
POST /api/check   { "kind": "skill", "name": "crypto-tracker-pro", "source": "ui" }
-> CheckResponse
{ "verdict": "BLOCK",                               // ALLOW | ASK | BLOCK
  "rule": "direct_link",                            // which rule fired: known_bad | direct_link | indirect_link |
                                                    // never_seen | vetted_skill | trusted_publisher | no_track_record
  "reason": "shares publisher hightower6eu with 334 known-malicious skills",
  "route": ["skill:crypto-tracker-pro", "publisher:hightower6eu", "skill:solana-wallet-x"],
  "evidence": { "nodes": [Node, ...], "edges": [Edge, ...] },   // includes every node in route
  "campaign": "ClawHavoc",                          // or null
  "checked_at": "2026-10-16T10:22:05Z",             // ISO 8601, UTC
  "ms": 12,
  "alternatives": [                                 // only for BLOCK / ASK; [] for ALLOW
    { "name": "aave-liquidation-monitor", "category": "finance & crypto",
      "reason": "trusted skill in the same category (finance & crypto), no link to known attacks" } ] }

GET /api/campaigns
-> [ { "campaign_id": 0, "name": "ClawHavoc", "size": 41, "known_bad": 29,
       "members": ["skill:...", "..."],
       "shared_infra": ["domain:socifiapp[.]com", "ip:91.92.242[.]30"] } ]

POST /api/investigate   { "name": "demo-pdf-helper", "text": "<SKILL.md contents>" }
-> { "facts": { "domains": [...], "urls": [...], "ips": [...], "commands": [...] },
     "added": { "nodes": 3, "edges": 4 },
     "result": CheckResponse }

GET /api/eval
-> { "splits": [ { "seed": 0, "hidden": 12, "blocklist_caught": 0, "graph_caught": 10,
                   "held": 2, "false_alarms": 2, "legit": 60 } ],
     "recall": 0.83,                     // linked to known malware by a graph path
     "held_rate": 0.17,                  // no link, but no track record -> ASK
     "allowed_rate": 0.0,                // slipped through as ALLOW
     "false_alarm_rate": 0.04, "blocklist_recall": 0.0, "avg_ms": 11 }
```

Notes for the UI:
- `route` is the evidence path; draw those edges thicker in the accent colour.
- For a never-seen item, `route` has one id and `evidence` has one Skill node with `status: "unknown"`.
- Facts in `investigate` come back **defanged** (`hxxps://evil[.]com`); show them exactly as received.
- `eval.json` mock carries `"_note": "placeholder"`; the live endpoint never does.

## 4. CSV columns (Ayesha fixes, Mrittika fills)

| File | Columns | Example row |
|---|---|---|
| `data/skills.csv` | skill_name, publisher, published_at, status, campaign, source_report, synthetic | `solana-wallet-x, hightower6eu, 2026-01-31, known_bad, ClawHavoc, antiy, false` |
| `data/infra.csv` | skill_name, kind (domain \| ip \| payload), value_defanged, source_report | `solana-wallet-x, domain, socifiapp[.]com, antiy` |
| `data/legit.csv` | skill_name, publisher, published_at, source_url | `git-tools, someauthor, 2025-11-02, <public list URL>` |
| `data/sources.md` | One line per report: `id \| title \| url \| what was taken` | `antiy \| ClawHavoc analysis \| <url> \| accounts, C2 domain, IPs, timeline` |
| `data/demo/demo_items.csv` | skill_name, publisher, expected_verdict, scene, text_file | `demo-crypto-tracker, hightower6eu, BLOCK, 1, demo-crypto-tracker.md` |
| `data/resolutions.csv` *(optional)* | domain, ip, source_report | `pdfhelper-cdn[.]top, 91.92.242[.]30, synthetic` |

Rules the loader enforces (`python -m bouncer.loaders ../data/` prints every problem):
- Every row has `source_report` (an id from `sources.md`) or `synthetic=true`. In `infra.csv`/`resolutions.csv` use `source_report=synthetic` for invented rows.
- Defang everything: `socifiapp[.]com`, `91.92.242[.]30`, `hxxp://`. Live `http(s)://` or plain dotted IPs are rejected (except `legit.csv` `source_url`).
- Skill names are unique across `skills.csv` and `legit.csv`; every `infra.csv` skill exists in skills/legit/demo.
- `demo_items.csv`: a row with an **empty publisher** is treated as never-seen (not preloaded). Use that for the Scene 2 investigator item.

## 5. Acceptance tests at H4

```
curl -s localhost:8000/api/health
curl -s -X POST localhost:8000/api/check -H 'Content-Type: application/json' \
     -d '{"kind":"skill","name":"demo-crypto-tracker","source":"ui"}'
curl -s 'localhost:8000/api/decisions?limit=5'
curl -s 'localhost:8000/api/graph/neighbourhood?name=demo-crypto-tracker&hops=2'
# Each response must have exactly the fields in Sections 2-3.
```
