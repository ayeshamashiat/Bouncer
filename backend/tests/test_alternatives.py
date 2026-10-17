from bouncer.categories import categories_for
from bouncer.check import check_install


def test_categories_from_name():
    assert categories_for("demo-crypto-tracker") == ["finance & crypto"]
    assert categories_for("git-helper") == ["git & code"]
    assert categories_for("xyz-qwerty") == []


def test_suggestions_share_a_category_and_are_allowed(g):
    # the sample data has trusted pdf/docs/notes skills, so a risky pdf skill gets alternatives
    r = check_install("skill", "pdf-converter-unknown", write_back=False, g=g)
    assert r["verdict"] == "ASK" and r["alternatives"]
    for alt in r["alternatives"]:
        assert "documents & notes" in alt["category"]
        assert check_install("skill", alt["name"], write_back=False, g=g)["verdict"] == "ALLOW"


def test_blocked_suggestions_are_always_safe(g):
    # whatever is suggested for a blocked skill must itself be allowed (may be empty if no trusted peers)
    r = check_install("skill", "demo-crypto-tracker", write_back=False, g=g)
    assert r["verdict"] == "BLOCK"
    assert all(check_install("skill", a["name"], write_back=False, g=g)["verdict"] == "ALLOW" for a in r["alternatives"])


def test_allowed_skill_gets_no_alternatives(g):
    assert check_install("skill", "demo-git-tools", write_back=False, g=g)["alternatives"] == []
