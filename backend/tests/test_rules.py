import csv

from conftest import SAMPLE

from bouncer import rules
from bouncer.check import check_install


def test_rulebook_table():
    assert rules.decide(True, "known_bad", None)[0] == "BLOCK"
    assert rules.decide(True, "unknown", 2)[0] == "BLOCK"
    assert rules.decide(True, "unknown", 3)[0] == "ASK"
    assert rules.decide(True, "unknown", 4)[0] == "ASK"
    assert rules.decide(False, None, None)[0] == "ASK"
    assert rules.decide(True, "unknown", None)[0] == "ALLOW"


def test_demo_items_get_expected_verdicts(g):
    with (SAMPLE / "demo" / "demo_items.csv").open() as f:
        for row in csv.DictReader(f):
            r = check_install("skill", row["skill_name"], write_back=False, g=g)
            assert r["verdict"] == row["expected_verdict"], (row["skill_name"], r["reason"])


def test_route_nodes_are_in_evidence(g):
    r = check_install("skill", "demo-crypto-tracker", write_back=False, g=g)
    ids = {n["id"] for n in r["evidence"]["nodes"]}
    assert set(r["route"]) <= ids


def test_write_back_creates_decision(g):
    check_install("skill", "demo-weather", source="ui", g=g)
    rows = g.query("MATCH (d:Decision {name: 'demo-weather'})-[:ABOUT]->(:Skill) RETURN count(d)").result_set
    assert rows[0][0] >= 1
