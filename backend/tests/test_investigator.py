from conftest import SAMPLE

from bouncer.investigator import extract_facts, investigate, validate_facts

INJECTION = (SAMPLE / "demo" / "demo-pdf-helper.md").read_text()


def test_schema_only():
    out = validate_facts({"domains": ["evil.com"], "safe": True, "verdict": "ALLOW", "ips": ["999.1.1.1"]})
    assert set(out) == {"domains", "urls", "ips", "commands"}
    assert out["domains"] == ["evil.com"] and out["ips"] == []


def test_regex_extracts_defanged_domain(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    facts = extract_facts(INJECTION)
    assert "pdfhelper-cdn.top" in facts["domains"]


def test_injection_does_not_change_verdict(g, monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    out = investigate("demo-pdf-helper", INJECTION, g=g)
    assert out["result"]["verdict"] in ("ASK", "BLOCK")
    assert "domain:pdfhelper-cdn[.]top" in out["result"]["route"]
    assert out["result"]["campaign"] == "ClawHavoc"
