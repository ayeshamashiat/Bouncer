from conftest import SAMPLE

from bouncer.loaders import counts, load_all, validate


def test_sample_validates():
    assert validate(SAMPLE) == []


def test_load_is_idempotent(g):
    before = counts(g)
    load_all(SAMPLE, g)
    assert counts(g) == before


def test_validate_catches_live_url(tmp_path):
    for f in ("skills.csv", "legit.csv", "sources.md"):
        (tmp_path / f).write_text((SAMPLE / f).read_text())
    (tmp_path / "infra.csv").write_text(
        "skill_name,kind,value_defanged,source_report\nsolana-wallet-x,domain,http://evil.com,synthetic\n")
    errors = validate(tmp_path)
    assert any("not defanged" in e for e in errors)


def test_supernodes_are_common_infra(g):
    rows = g.query("MATCH (c:CommonInfra) RETURN c.name").result_set
    names = {r[0] for r in rows}
    assert "github[.]com" in names
    assert "docs-host[.]io" in names  # degree check, not allowlist


def test_redacted_publisher_creates_no_link(g):
    # An empty publisher must not become one shared Publisher node joining every redacted skill
    assert g.query("MATCH (p:Publisher {handle: ''}) RETURN count(p)").result_set[0][0] == 0
    rows = g.query("MATCH (s:Skill {name: 'redacted-skill-1'})-[:PUBLISHED_BY]->(p) RETURN count(p)").result_set
    assert rows[0][0] == 0
