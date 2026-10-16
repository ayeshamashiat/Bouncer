from bouncer import queries
from bouncer.serialize import path_json


def test_lookup_known_bad(g):
    s, campaign = queries.lookup("solana-wallet-x", g)
    assert s.properties["status"] == "known_bad" and campaign == "ClawHavoc"


def test_lookup_never_seen(g):
    assert queries.lookup("does-not-exist", g) == (None, None)


def test_shared_publisher_is_two_hops(g):
    path, campaign = queries.guilt_by_connection("demo-crypto-tracker", g=g)
    route, _ = path_json(path)
    assert len(path.edges()) == 2
    assert route[1] == "publisher:hightower6eu"
    assert campaign == "ClawHavoc"


def test_supernode_is_skipped(g):
    # demo-git-tools only touches github.com, which known-bad skills also touch
    path, _ = queries.guilt_by_connection("demo-git-tools", g=g)
    assert path is None


def test_no_self_match(g):
    path, _ = queries.guilt_by_connection("solana-wallet-x", g=g)
    assert path is None or path.nodes()[-1].properties["name"] != "solana-wallet-x"


def test_campaigns_found(g):
    names = {c["name"] for c in queries.campaigns(g)}
    assert {"ClawHavoc", "SyntheticBravo"} <= names


def test_neighbourhood_capped(g):
    start = queries.find_node("publisher:hightower6eu", g)
    nodes, _ = queries.neighbourhood(start, hops=3, limit=150, g=g)
    assert 1 < len(nodes) <= 150
