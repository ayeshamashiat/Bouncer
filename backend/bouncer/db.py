"""FalkorDB connection + graph names. Everything reads settings from env (.env)."""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from falkordb import FalkorDB

# .env lives at the repo root (one level above backend/)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

THREAT_GRAPH = os.getenv("THREAT_GRAPH", "threat")


@lru_cache(maxsize=1)
def get_db() -> FalkorDB:
    return FalkorDB(
        host=os.getenv("FALKORDB_HOST", "localhost"),
        port=int(os.getenv("FALKORDB_PORT", "6379")),
        username=os.getenv("FALKORDB_USERNAME") or None,
        password=os.getenv("FALKORDB_PASSWORD") or None,
    )


def get_graph(name: str | None = None):
    return get_db().select_graph(name or os.getenv("THREAT_GRAPH", THREAT_GRAPH))


def graph_name() -> str:
    return os.getenv("THREAT_GRAPH", THREAT_GRAPH)
