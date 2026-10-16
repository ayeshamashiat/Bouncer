"""Tests run against a separate graph (threat_test) loaded from data/sample/,
so they never touch the demo graph. Needs FalkorDB running (docker start falkordb)."""
import os
import sys
from pathlib import Path

import pytest

os.environ["THREAT_GRAPH"] = "threat_test"
BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
SAMPLE = BACKEND.parent / "data" / "sample"


@pytest.fixture(scope="session")
def g():
    from bouncer.db import get_db, get_graph
    try:
        get_db().list_graphs()
    except Exception as e:
        pytest.skip(f"FalkorDB not reachable: {e}")
    from bouncer.loaders import load_all
    graph = get_graph("threat_test")
    load_all(SAMPLE, graph, reset=True)
    yield graph
    graph.delete()
