"""check_install(kind, name) -> CheckResponse dict (contracts/api.md, 7.3).

Flow: Q1 lookup -> Q2 guilt by connection -> rules.decide -> evidence graph
-> write a (:Decision)-[:ABOUT]->(:Skill) node -> return.
"""
import time
from datetime import datetime, timezone

from . import queries, rules
from .categories import categories_for
from .db import get_graph
from .serialize import graph_json, node_id, path_json

KINDS = {"skill", "mcp", "package"}
SOURCES = {"hook", "mcp", "ui"}

_CLUE_WORDS = {
    "Publisher": ("shares publisher", "with"),
    "Domain": ("contacts domain", "used by"),
    "IP": ("downloads from IP", "used by"),
    "PayloadString": ("contains payload marker", "found in"),
}


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _age_days(day: str | None) -> int | None:
    if not day:
        return None
    try:
        then = datetime.strptime(day[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - then).days


def _describe_clue(n) -> tuple[str, str]:
    label = next((l for l in n.labels if l in _CLUE_WORDS), "Domain")
    value = n.properties.get({"Publisher": "handle", "IP": "addr", "PayloadString": "value"}.get(label, "name"))
    return label, value


def check_install(kind: str, name: str, source: str = "ui", write_back: bool = True, g=None,
                  suggest: bool = True) -> dict:
    t0 = time.perf_counter()
    g = g or get_graph()
    trace = []  # every graph query this check ran, with its result and time (the UI shows it)
    tq = time.perf_counter()
    skill, campaign = queries.lookup(name, g)
    seen = skill is not None
    status = skill.properties.get("status") if seen else None
    trace.append({"query": "Q1 · do we know this skill?", "cypher": queries.Q1_LOOKUP.strip(),
                  "result": f"found, status {status}" if seen else "not in the graph",
                  "ms": round((time.perf_counter() - tq) * 1000, 2)})

    path, path_campaign, hops = None, None, None
    if seen and status != "known_bad":
        path, path_campaign = queries.guilt_by_connection(name, rules.ASK_MAX_HOPS, g, trace=trace)
        hops = len(path.edges()) if path is not None else None

    # Good evidence is only looked up when nothing bad was found (trust can't cancel a block).
    record, trusted = None, False
    if seen and hops is None and status not in ("known_bad", "trusted"):
        tq = time.perf_counter()
        record = queries.track_record(name, g)
        if record:
            dated = [v for v in record["vetted"] if v.properties.get("published_at")]
            trusted = rules.publisher_is_trusted(len(dated), record["known_bad"], _age_days(record["since"]))
        trace.append({"query": "Q7 · does the publisher have a track record?", "cypher": queries.Q7_TRACK_RECORD.strip(),
                      "result": (f"{record['publisher'].properties['handle']}: {len(record['vetted'])} vetted, "
                                 f"{record['known_bad']} malicious" + (" → trusted" if trusted else " → not enough"))
                      if record else "no publisher with other skills",
                      "ms": round((time.perf_counter() - tq) * 1000, 2)})

    verdict, rule = rules.decide(seen, status, hops, trusted)
    trace.append({"query": f"Rules · {rule.replace('_', ' ')}", "cypher": "", "result": verdict, "ms": 0})

    # ---- reason + route + evidence
    if rule == rules.R_KNOWN_BAD:
        nodes, edges = queries.neighbourhood(skill, hops=1, limit=25, g=g)
        evidence = graph_json(nodes, edges)
        route = [node_id(skill)]
        reason = "already known malicious" + (f" (campaign {campaign})" if campaign else "")
    elif rule in (rules.R_DIRECT, rules.R_INDIRECT):
        route, evidence = path_json(path)
        campaign = path_campaign
        clue = path.nodes()[-2]  # the node the known-bad skill hangs off
        label, value = _describe_clue(clue)
        count, sample = queries.shared_bad(clue.id, exclude=path.nodes()[-1].properties["name"], g=g)
        # Light up the campaign: other known-bad skills on the same clue
        extra = graph_json([clue] + [b for b, _ in sample], [r for _, r in sample])
        have = {n["id"] for n in evidence["nodes"]}
        evidence["nodes"] += [n for n in extra["nodes"] if n["id"] not in have]
        evidence["edges"] += [e for e in extra["edges"] if e not in evidence["edges"]]
        verb, prep = _CLUE_WORDS[label]
        bad_name = path.nodes()[-1].properties["name"]
        if rule == rules.R_DIRECT:
            reason = f"{verb} {value} {prep} {count} known-malicious skill{'s' if count != 1 else ''}"
        else:
            via = " -> ".join(n.split(":", 1)[1] for n in route[1:-1])
            reason = (f"linked in {hops} hops to known-malicious skill {bad_name} via {via}; "
                      f"{label if label == 'IP' else label.lower()} {value} is used by {count} known-malicious "
                      f"skill{'s' if count != 1 else ''}")
    elif rule == rules.R_UNSEEN:
        route = [f"skill:{name}"]
        evidence = {"nodes": [{"id": f"skill:{name}", "label": name, "type": "Skill",
                               "status": "unknown", "common_infra": False}], "edges": []}
        reason = "never seen before: no record of this item, and unknown is not safe"
    elif rule == rules.R_TRUSTED_PUBLISHER:
        nodes, edges = queries.neighbourhood(skill, hops=1, limit=25, g=g)
        pub, vetted = record["publisher"], record["vetted"]
        extra_nodes, extra_edges = queries.publisher_skills(pub, [v.properties["name"] for v in vetted], g)
        evidence = graph_json(nodes + [n for n in extra_nodes if n.id not in {x.id for x in nodes}],
                              edges + extra_edges)
        route = [node_id(skill), node_id(pub), node_id(vetted[0])]
        n = len(vetted)
        reason = (f"trusted publisher {pub.properties['handle']}: {n} community-vetted skill{'s' if n != 1 else ''} "
                  f"since {record['since']}, none malicious, and no link to any known-malicious skill")
    elif rule == rules.R_VETTED:
        nodes, edges = queries.neighbourhood(skill, hops=1, limit=25, g=g)
        evidence = graph_json(nodes, edges)
        route = [node_id(skill)]
        reason = ("community-vetted skill with no link to any known-malicious skill "
                  "(shared infrastructure like github.com is ignored)")
    else:  # R_NO_RECORD
        nodes, edges = queries.neighbourhood(skill, hops=1, limit=25, g=g)
        evidence = graph_json(nodes, edges)
        route = [node_id(skill)]
        reason = ("no link to known malware, but nothing vouches for it either: not community-vetted and "
                  "its publisher has no track record, so a human decides")

    checked_at = now_iso()
    ms = round((time.perf_counter() - t0) * 1000)
    result = {"verdict": verdict, "rule": rule, "reason": reason, "trace": trace, "route": route, "evidence": evidence,
              "campaign": campaign or None, "checked_at": checked_at, "ms": ms,
              "alternatives": suggest_alternatives(name, g) if suggest and verdict != rules.ALLOW else []}
    if write_back:
        write_decision(g, kind, name, source, result)
    return result


def suggest_alternatives(name: str, g=None, limit: int = 3) -> list[dict]:
    """Trusted skills in the same category that Bouncer itself would ALLOW right now.
    Comes only from the graph: nothing is suggested that wasn't re-checked."""
    g = g or get_graph()
    out = []
    for alt, shared in queries.alternatives(categories_for(name), exclude=name, g=g):
        if check_install("skill", alt, write_back=False, g=g, suggest=False)["verdict"] == rules.ALLOW:
            cat = ", ".join(shared)
            out.append({"name": alt, "category": cat,
                        "reason": f"trusted skill in the same category ({cat}), no link to known attacks"})
            if len(out) == limit:
                break
    return out


_WRITE_DECISION = """
MERGE (m:Meta {key: 'decisions'})
ON CREATE SET m.n = 0
SET m.n = m.n + 1
WITH m.n AS seq
OPTIONAL MATCH (s:Skill {name: $name})
CREATE (d:Decision {id: 'dec_' + right('0000' + toString(seq), 4), seq: seq, kind: $kind, name: $name,
                    verdict: $verdict, reason: $reason, route: $route, source: $source, at: $at,
                    campaign: $campaign, ms: $ms})
WITH d, s
FOREACH (_ IN CASE WHEN s IS NULL THEN [] ELSE [1] END | CREATE (d)-[:ABOUT]->(s))
RETURN d.id
"""


def write_decision(g, kind, name, source, result) -> str:
    # The id comes from a counter incremented inside the same query. FalkorDB runs writes one at a
    # time, so two checks arriving together can't get the same id (counting Decision nodes could).
    rows = g.query(_WRITE_DECISION, {
        "kind": kind, "name": name, "verdict": result["verdict"],
        "reason": result["reason"], "route": result["route"], "source": source,
        "at": result["checked_at"], "campaign": result["campaign"] or "", "ms": result["ms"],
    }).result_set
    return rows[0][0]


_LIST_DECISIONS = """
MATCH (d:Decision)
RETURN d.id, d.kind, d.name, d.verdict, d.reason, d.campaign, d.source, d.at
ORDER BY d.seq DESC LIMIT $limit
"""


def list_decisions(limit: int = 50, g=None) -> list[dict]:
    g = g or get_graph()
    try:
        rows = g.ro_query(_LIST_DECISIONS, {"limit": limit}).result_set
    except Exception:
        return []
    return [{"id": r[0], "kind": r[1], "name": r[2], "verdict": r[3], "reason": r[4],
             "campaign": r[5] or None, "source": r[6], "checked_at": r[7]} for r in rows]


_LAST_DECISION = """
MATCH (d:Decision {name: $name})
RETURN d.verdict, d.reason, d.route, d.campaign, d.at, d.source
ORDER BY d.seq DESC LIMIT 1
"""


def last_decision(name: str, g=None) -> dict | None:
    g = g or get_graph()
    rows = g.ro_query(_LAST_DECISION, {"name": name}).result_set
    if not rows:
        return None
    v, reason, route, campaign, at, source = rows[0]
    return {"verdict": v, "reason": reason, "route": route, "campaign": campaign or None,
            "checked_at": at, "source": source}
