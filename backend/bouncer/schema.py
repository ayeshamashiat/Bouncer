"""Graph model: labels, relationship types, indexes (playbook Section 9).

Run: python -m bouncer.schema   (creates the indexes on THREAT_GRAPH)
"""
from .db import get_graph

# label -> key property (the property every MERGE matches on)
KEY_PROPERTY = {
    "Skill": "name",
    "Publisher": "handle",
    "Domain": "name",
    "IP": "addr",
    "PayloadString": "value",
    "CommonInfra": "name",
    "Campaign": "name",
    "Report": "url",
    "Finding": "id",
    "Decision": "id",
}

# Relationships that count as evidence. Used by guilt-by-connection paths,
# WCC campaigns and the neighbourhood view. PART_OF, SOURCED_FROM and ABOUT
# are deliberately NOT here: they are labels/bookkeeping, not shared clues.
STRONG_RELS = ["PUBLISHED_BY", "CONTACTS", "RESOLVES_TO", "DOWNLOADS_FROM", "CONTAINS"]

# Labels that take part in campaign detection. CommonInfra and Decision are
# left out, so supernodes and verdict bookkeeping never merge campaigns.
CAMPAIGN_LABELS = ["Skill", "Publisher", "Domain", "IP", "PayloadString"]


def create_indexes(g=None) -> None:
    g = g or get_graph()
    existing = {(r[0], r[1]) for r in _list_indexes(g)}
    for label, prop in KEY_PROPERTY.items():
        if (label, prop) in existing:
            continue
        g.query(f"CREATE INDEX FOR (n:{label}) ON (n.{prop})")  # labels are constants above, not user input
    if ("Skill", "status") not in existing:
        g.query("CREATE INDEX FOR (n:Skill) ON (n.status)")


def _list_indexes(g):
    try:
        res = g.query("CALL db.indexes() YIELD label, properties RETURN label, properties")
    except Exception:
        return []
    out = []
    for label, props in res.result_set:
        for p in props:
            out.append((label, p))
    return out


if __name__ == "__main__":
    create_indexes()
    for row in _list_indexes(get_graph()):
        print(row)
