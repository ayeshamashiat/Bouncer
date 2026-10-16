"""FalkorDB nodes/edges/paths -> contract Node and Edge dicts (contracts/api.md, 7.2)."""

# label -> (contract id prefix, contract type, key property)
_LABELS = {
    "Skill": ("skill", "Skill", "name"),
    "Publisher": ("publisher", "Publisher", "handle"),
    "Domain": ("domain", "Domain", "name"),
    "IP": ("ip", "IP", "addr"),
    "PayloadString": ("payload", "PayloadString", "value"),
    "Campaign": ("campaign", "Campaign", "name"),
}


def node_id(n) -> str:
    return to_node(n)["id"]


def to_node(n) -> dict:
    props = n.properties
    if "CommonInfra" in n.labels:
        kind = props.get("kind", "Domain")
        prefix = "ip" if kind == "IP" else "domain"
        return {"id": f"{prefix}:{props['name']}", "label": props["name"], "type": kind,
                "status": None, "common_infra": True}
    for label in n.labels:
        if label in _LABELS:
            prefix, typ, key = _LABELS[label]
            value = props.get(key, "")
            return {"id": f"{prefix}:{value}", "label": value, "type": typ,
                    "status": props.get("status") if typ == "Skill" else None,
                    "common_infra": False}
    raise ValueError(f"node with labels {n.labels} is not part of the contract")


def to_edge(e, id_by_internal: dict) -> dict:
    return {"source": id_by_internal[e.src_node], "target": id_by_internal[e.dest_node], "type": e.relation}


def graph_json(nodes, edges) -> dict:
    """Raw nodes + edges -> {"nodes": [Node], "edges": [Edge]}; drops anything off-contract."""
    out_nodes, ids = [], {}
    for n in nodes:
        try:
            cn = to_node(n)
        except ValueError:
            continue
        if n.id not in ids:
            ids[n.id] = cn["id"]
            out_nodes.append(cn)
    out_edges, seen = [], set()
    for e in edges:
        if e.src_node in ids and e.dest_node in ids:
            ce = to_edge(e, ids)
            key = (ce["source"], ce["target"], ce["type"])
            if key not in seen:
                seen.add(key)
                out_edges.append(ce)
    return {"nodes": out_nodes, "edges": out_edges}


def path_json(path) -> tuple[list[str], dict]:
    """Path -> (route as list of contract ids, evidence graph)."""
    nodes = path.nodes()
    return [node_id(n) for n in nodes], graph_json(nodes, path.edges())
