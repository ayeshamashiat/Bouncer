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
    assert rules.decide(True, "trusted", None) == ("ALLOW", "vetted_skill")
    assert rules.decide(True, "unknown", None, trusted_publisher=True) == ("ALLOW", "trusted_publisher")
    assert rules.decide(True, "unknown", None) == ("ASK", "no_track_record")


def test_bad_evidence_beats_trust():
    # a trusted publisher (or a vetted skill) that links to malware is still blocked / asked
    assert rules.decide(True, "unknown", 2, trusted_publisher=True)[0] == "BLOCK"
    assert rules.decide(True, "unknown", 4, trusted_publisher=True)[0] == "ASK"
    assert rules.decide(True, "trusted", 2)[0] == "BLOCK"


def test_publisher_trust_thresholds():
    assert rules.publisher_is_trusted(vetted=2, known_bad=0, age_days=60)
    assert not rules.publisher_is_trusted(vetted=1, known_bad=0, age_days=60)    # too little history
    assert not rules.publisher_is_trusted(vetted=5, known_bad=1, age_days=400)   # ever published malware
    assert not rules.publisher_is_trusted(vetted=5, known_bad=0, age_days=10)    # sleeper: too new
    assert not rules.publisher_is_trusted(vetted=5, known_bad=0, age_days=None)  # age unknown


def test_trusted_publisher_evidence(g):
    r = check_install("skill", "demo-git-tools", write_back=False, g=g)
    assert r["rule"] == "trusted_publisher"
    assert "gitfan-dev" in r["reason"] and "2 community-vetted skills" in r["reason"]
    assert r["route"] == ["skill:demo-git-tools", "publisher:gitfan-dev", "skill:commit-message-coach"]
    assert set(r["route"]) <= {n["id"] for n in r["evidence"]["nodes"]}


def test_no_track_record_is_asked(g):
    r = check_install("skill", "demo-notes-sync", write_back=False, g=g)
    assert (r["verdict"], r["rule"]) == ("ASK", "no_track_record")


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


def test_trace_shows_the_graph_work(g):
    r = check_install("skill", "demo-crypto-tracker", write_back=False, g=g)
    steps = [s["query"] for s in r["trace"]]
    assert steps[0].startswith("Q1") and steps[1].startswith("Q2 · path of 2 hops")
    assert r["trace"][1]["result"].startswith("found") and "MATCH p =" in r["trace"][1]["cypher"]
    assert r["trace"][-1]["result"] == "BLOCK"
