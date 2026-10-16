"""The Cypher that does the detection (Q1-Q5).

Every query uses $parameters, never string formatting of user input.
Detection paths only follow STRONG_RELS (see schema.py) and never pass
through a CommonInfra node (supernodes prove nothing).
"""
from .db import get_graph

STRONG = "PUBLISHED_BY|CONTACTS|RESOLVES_TO|DOWNLOADS_FROM|CONTAINS"

# ---------------------------------------------------------------- Q1 lookup
Q1_LOOKUP = """
MATCH (s:Skill {name: $name})
OPTIONAL MATCH (s)-[:PART_OF]->(c:Campaign)
RETURN s, c.name
"""


def lookup(name: str, g=None):
    """Returns (skill_node, campaign_name) or (None, None) if never seen."""
    g = g or get_graph()
    rows = g.ro_query(Q1_LOOKUP, {"name": name}).result_set
    if not rows:
        return None, None
    return rows[0][0], rows[0][1]


# ---------------------------------------------------------------- Q2 guilt by connection
# One query per path length, tried shortest first ("iterative deepening").
# Why not shortestPath(): in FalkorDB it is directed-only, and our clues point
# both ways (skill -> publisher <- skill). Why not *1..4 in one go: through a
# publisher with hundreds of skills, 4-hop enumeration explodes; stopping at the
# first length that finds anything keeps every check in milliseconds.
# `bad <> s` stops a skill matching itself; Decision/Finding nodes are never
# reached because ABOUT is not in the relationship list.
_Q2_TEMPLATE = """
MATCH p = (s:Skill {name: $name})-[:%s*%d..%d]-(bad:Skill {status: 'known_bad'})
WHERE bad <> s AND none(n IN nodes(p) WHERE n:CommonInfra)
WITH p, bad LIMIT 1
RETURN p, bad.campaign
"""
Q2_BY_LENGTH = {k: _Q2_TEMPLATE % (STRONG, k, k) for k in (2, 3, 4)}


def guilt_by_connection(name: str, max_hops: int = 4, g=None):
    """Shortest evidence path from the skill to a known_bad skill.
    Returns (path, campaign_name) or (None, None)."""
    g = g or get_graph()
    for k in (2, 3, 4):
        if k > max_hops:
            break
        rows = g.ro_query(Q2_BY_LENGTH[k], {"name": name}).result_set
        if rows:
            return rows[0][0], rows[0][1]
    return None, None


# Count of known-bad skills hanging off the shared clue (for the reason text,
# e.g. "shares publisher hightower6eu with 334 known-malicious skills").
# Gotcha: in FalkorDB a second MATCH right after `WHERE id(x) = $id` ignores the
# binding and matches every node. The `WITH x` in between pins it.
Q2_SHARED_COUNT = """
MATCH (x) WHERE id(x) = $id
WITH x
MATCH (x)-[:%s]-(b:Skill {status: 'known_bad'})
RETURN count(DISTINCT b)
""" % STRONG

Q2_SHARED_SAMPLE = """
MATCH (x) WHERE id(x) = $id
WITH x
MATCH (x)-[r:%s]-(b:Skill {status: 'known_bad'})
WHERE b.name <> $exclude
RETURN b, r LIMIT $limit
""" % STRONG


def shared_bad(node_id: int, exclude: str, limit: int = 8, g=None):
    g = g or get_graph()
    count = g.ro_query(Q2_SHARED_COUNT, {"id": node_id}).result_set[0][0]
    sample = g.ro_query(Q2_SHARED_SAMPLE, {"id": node_id, "exclude": exclude, "limit": limit}).result_set
    return count, sample


# ---------------------------------------------------------------- Q3 campaigns (WCC)
# WCC = groups of nodes reachable from each other ignoring arrow direction.
# Only strong evidence relationships and only the 5 evidence labels, so
# CommonInfra (github.com...) and Decision nodes can never glue groups together.
Q3_WCC = """
CALL algo.WCC({nodeLabels: ['Skill', 'Publisher', 'Domain', 'IP', 'PayloadString'],
               relationshipTypes: ['PUBLISHED_BY', 'CONTACTS', 'RESOLVES_TO', 'DOWNLOADS_FROM', 'CONTAINS']})
YIELD node, componentId
WITH componentId, collect(node) AS members
WHERE any(m IN members WHERE m:Skill AND m.status = 'known_bad')
RETURN componentId, members
"""

# Optional comparison: label propagation finds tighter sub-groups.
Q3_CDLP = """
CALL algo.labelPropagation({nodeLabels: ['Skill', 'Publisher', 'Domain', 'IP', 'PayloadString'],
               relationshipTypes: ['PUBLISHED_BY', 'CONTACTS', 'RESOLVES_TO', 'DOWNLOADS_FROM', 'CONTAINS']})
YIELD node, communityId
RETURN communityId, count(node) AS size ORDER BY size DESC
"""


MIN_CAMPAIGN_SKILLS = 2


def campaigns(g=None) -> list[dict]:
    g = g or get_graph()
    out = []
    for comp_id, members in g.ro_query(Q3_WCC).result_set:
        skills = [m for m in members if "Skill" in m.labels]
        if len(skills) < MIN_CAMPAIGN_SKILLS:
            continue  # one skill on its own is not a campaign
        bad = [m for m in skills if m.properties.get("status") == "known_bad"]
        names = {}
        for m in bad:
            c = m.properties.get("campaign")
            if c:
                names[c] = names.get(c, 0) + 1
        name = max(names, key=names.get) if names else f"Campaign {comp_id}"
        infra = [m for m in members if {"Domain", "IP", "PayloadString"} & set(m.labels)]
        out.append({"component_id": comp_id, "name": name, "skills": skills, "bad": bad, "infra": infra,
                    "publishers": [m for m in members if "Publisher" in m.labels]})
    out.sort(key=lambda c: -len(c["bad"]))
    return out


# ---------------------------------------------------------------- Q4 publisher reputation
Q4_PUBLISHER = """
MATCH (p:Publisher {handle: $handle})<-[:PUBLISHED_BY]-(s:Skill)
RETURN p.handle, p.first_seen, count(s) AS skills,
       sum(CASE WHEN s.status = 'known_bad' THEN 1 ELSE 0 END) AS known_bad
"""


def publisher_reputation(handle: str, g=None) -> dict | None:
    g = g or get_graph()
    rows = g.ro_query(Q4_PUBLISHER, {"handle": handle}).result_set
    if not rows:
        return None
    h, first, n, bad = rows[0]
    n, bad = int(n), int(bad)
    return {"handle": h, "first_seen": first, "skills": n, "known_bad": bad,
            "known_bad_share": round(bad / n, 3) if n else 0.0}


# ---------------------------------------------------------------- Q5 neighbourhood
# Hop count cannot be a parameter in Cypher, so we keep one fixed query per value.
_Q5_TEMPLATE = """
MATCH (s) WHERE id(s) = $id
WITH s
MATCH p = (s)-[:%s|PART_OF*1..%d]-(n)
RETURN p LIMIT 3000
"""
Q5_BY_HOPS = {h: _Q5_TEMPLATE % (STRONG, h) for h in (1, 2, 3)}

Q5_FIND = {
    "skill": "MATCH (n:Skill {name: $v}) RETURN n",
    "publisher": "MATCH (n:Publisher {handle: $v}) RETURN n",
    "domain": "MATCH (n) WHERE (n:Domain OR n:CommonInfra) AND n.name = $v RETURN n",
    "ip": "MATCH (n) WHERE (n:IP AND n.addr = $v) OR (n:CommonInfra AND n.name = $v) RETURN n",
    "payload": "MATCH (n:PayloadString {value: $v}) RETURN n",
    "campaign": "MATCH (n:Campaign {name: $v}) RETURN n",
}


def find_node(name: str, g=None):
    """Accepts a bare skill name or a contract id like 'publisher:hightower6eu'."""
    g = g or get_graph()
    prefix, _, value = name.partition(":")
    if value and prefix in Q5_FIND:
        rows = g.ro_query(Q5_FIND[prefix], {"v": value}).result_set
    else:
        rows = g.ro_query(Q5_FIND["skill"], {"v": name}).result_set
    return rows[0][0] if rows else None


def neighbourhood(start_node, hops: int = 2, limit: int = 150, g=None):
    """Returns (nodes, edges) as raw FalkorDB objects, capped at `limit` nodes."""
    g = g or get_graph()
    nodes = {start_node.id: start_node}
    edges = {}
    for (p,) in g.ro_query(Q5_BY_HOPS[hops], {"id": start_node.id}).result_set:
        pn = p.nodes()
        if any(n.id not in nodes for n in pn) and len(nodes) + sum(n.id not in nodes for n in pn) > limit:
            continue
        for n in pn:
            nodes[n.id] = n
        for e in p.edges():
            edges[e.id] = e
    return list(nodes.values()), list(edges.values())


# ---------------------------------------------------------------- misc
def node_count(g=None) -> int:
    g = g or get_graph()
    try:
        return g.ro_query("MATCH (n) RETURN count(n)").result_set[0][0]
    except Exception:
        return 0  # ro_query on a graph that was never written errors
