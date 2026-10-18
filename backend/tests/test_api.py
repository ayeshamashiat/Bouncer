from fastapi.testclient import TestClient

import api

client = TestClient(api.app)
NODE_KEYS = {"id", "label", "type", "status", "common_infra"}


def test_health(g):
    r = client.get("/api/health").json()
    assert r["ok"] is True and r["graph"] == "threat_test" and r["nodes"] > 0


def test_check_shape(g):
    r = client.post("/api/check", json={"kind": "skill", "name": "demo-crypto-tracker", "source": "ui"})
    body = r.json()
    assert r.status_code == 200
    assert set(body) == {"verdict", "rule", "reason", "trace", "route", "evidence", "campaign", "checked_at", "ms", "alternatives"}
    assert all(set(n) == NODE_KEYS for n in body["evidence"]["nodes"])
    assert body["checked_at"].endswith("Z")


def test_decisions_shape(g):
    client.post("/api/check", json={"kind": "skill", "name": "demo-weather", "source": "hook"})
    items = client.get("/api/decisions?limit=5").json()
    assert items and set(items[0]) == {"id", "kind", "name", "verdict", "reason", "campaign", "source", "checked_at"}


def test_errors_are_contract_shaped(g):
    assert client.get("/api/graph/neighbourhood?name=nope").json()["error"]["code"] == "not_found"
    r = client.post("/api/check", json={"kind": "car", "name": "x"})
    assert r.status_code == 400 and "error" in r.json()


def test_campaigns_shape(g):
    c = client.get("/api/campaigns").json()[0]
    assert set(c) == {"campaign_id", "name", "size", "known_bad", "members", "shared_infra"}


def test_graph_map(g):
    body = client.get("/api/graph/map").json()
    types = {n["type"] for n in body["nodes"]}
    assert {"Skill", "Publisher"} <= types and "Decision" not in types
    ids = {n["id"] for n in body["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in body["edges"])
