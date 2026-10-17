"""Bouncer HTTP API. Serves the contract in contracts/api.md exactly.

Run from backend/:  uvicorn api:app --reload
"""
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

from bouncer import evaluate, queries
from bouncer.check import KINDS, SOURCES, check_install, list_decisions
from bouncer.db import get_graph, graph_name
from bouncer.investigator import investigate
from bouncer.loaders import load_all
from bouncer.serialize import graph_json, node_id

DATA_DIR = Path(os.getenv("BOUNCER_DATA_DIR", Path(__file__).resolve().parents[1] / "data"))


def ensure_loaded(attempts: int = 20) -> None:
    """A fresh database (e.g. on first deploy) is empty: load the threat data once.
    Never reloads a graph that already has skills, so recorded decisions survive restarts."""
    for i in range(attempts):
        try:
            g = get_graph()
            try:
                skills = g.ro_query("MATCH (s:Skill) RETURN count(s)").result_set[0][0]
            except Exception:
                skills = 0  # graph never written yet
            if skills == 0:
                print(f"[bouncer] graph '{graph_name()}' is empty, loading {DATA_DIR}", file=sys.stderr)
                load_all(DATA_DIR, g)
            return
        except Exception as e:  # FalkorDB may still be starting
            print(f"[bouncer] waiting for FalkorDB ({e}); retry {i + 1}/{attempts}", file=sys.stderr)
            time.sleep(3)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if os.getenv("BOUNCER_AUTOLOAD", "1") == "1":
        ensure_loaded()
    yield


app = FastAPI(title="Bouncer", version="1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip().rstrip("/") for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- contract models (7.2 / 7.3)
class Node(BaseModel):
    id: str
    label: str
    type: Literal["Skill", "Publisher", "Domain", "IP", "PayloadString", "Campaign"]
    status: Literal["known_bad", "unknown", "trusted"] | None
    common_infra: bool


class Edge(BaseModel):
    source: str
    target: str
    type: Literal["PUBLISHED_BY", "CONTACTS", "RESOLVES_TO", "DOWNLOADS_FROM", "CONTAINS", "PART_OF"]


class Graph(BaseModel):
    nodes: list[Node]
    edges: list[Edge]


class CheckRequest(BaseModel):
    kind: str = "skill"
    name: str = Field(min_length=1, max_length=200)
    source: str | None = None


class Alternative(BaseModel):
    name: str
    category: str
    reason: str


class CheckResponse(BaseModel):
    verdict: Literal["ALLOW", "ASK", "BLOCK"]
    reason: str
    route: list[str]
    evidence: Graph
    campaign: str | None
    checked_at: str
    ms: int
    alternatives: list[Alternative] = []


class DecisionItem(BaseModel):
    id: str
    kind: str
    name: str
    verdict: Literal["ALLOW", "ASK", "BLOCK"]
    reason: str
    campaign: str | None
    source: str
    checked_at: str


class Campaign(BaseModel):
    campaign_id: int
    name: str
    size: int
    known_bad: int
    members: list[str]
    shared_infra: list[str]


class InvestigateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=50_000)


class Facts(BaseModel):
    domains: list[str]
    urls: list[str]
    ips: list[str]
    commands: list[str]


class Added(BaseModel):
    nodes: int
    edges: int


class InvestigateResponse(BaseModel):
    facts: Facts
    added: Added
    result: CheckResponse


class EvalSplit(BaseModel):
    seed: int
    hidden: int
    blocklist_caught: int
    graph_caught: int
    false_alarms: int
    legit: int


class EvalResponse(BaseModel):
    splits: list[EvalSplit]
    recall: float
    false_alarm_rate: float
    blocklist_recall: float
    avg_ms: float


class Health(BaseModel):
    ok: bool
    graph: str
    nodes: int


# ---------------------------------------------------------------- errors: always {"error": {code, message}}
class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _err(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@app.exception_handler(ApiError)
async def _api_error(_: Request, e: ApiError):
    return _err(e.status, e.code, e.message)


@app.exception_handler(RequestValidationError)
async def _validation_error(_: Request, e: RequestValidationError):
    first = e.errors()[0] if e.errors() else {}
    where = ".".join(str(x) for x in first.get("loc", []) if x not in ("body", "query"))
    return _err(400, "bad_request", f"{where}: {first.get('msg', 'invalid request')}".strip(": "))


@app.exception_handler(StarletteHTTPException)
async def _http_error(_: Request, e: StarletteHTTPException):
    return _err(e.status_code, "not_found" if e.status_code == 404 else "http_error", str(e.detail))


@app.exception_handler(Exception)
async def _server_error(_: Request, e: Exception):
    return _err(500, "internal", f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- endpoints
@app.get("/api/health", response_model=Health)
def health():
    try:
        n = queries.node_count(get_graph())
    except Exception as e:
        raise ApiError(500, "db_unreachable", f"FalkorDB unreachable: {e}")
    return {"ok": True, "graph": graph_name(), "nodes": n}


@app.post("/api/check", response_model=CheckResponse)
def check(req: CheckRequest, x_bouncer_source: str | None = Header(default=None)):
    if req.kind not in KINDS:
        raise ApiError(400, "bad_kind", f"kind must be one of {sorted(KINDS)}")
    source = req.source or x_bouncer_source or "ui"
    if source not in SOURCES:
        raise ApiError(400, "bad_source", f"source must be one of {sorted(SOURCES)}")
    return check_install(req.kind, req.name.strip(), source=source)


@app.get("/api/decisions", response_model=list[DecisionItem])
def decisions(limit: int = Query(50, ge=1, le=500)):
    return list_decisions(limit)


@app.get("/api/graph/neighbourhood", response_model=Graph)
def neighbourhood(name: str = Query(..., min_length=1), hops: int = Query(2, ge=1, le=3)):
    g = get_graph()
    start = queries.find_node(name, g)
    if start is None:
        raise ApiError(404, "not_found", f"No item named {name}")
    nodes, edges = queries.neighbourhood(start, hops=hops, limit=150, g=g)
    return graph_json(nodes, edges)


@app.get("/api/campaigns", response_model=list[Campaign])
def campaigns():
    out = []
    for c in queries.campaigns():
        out.append({
            "campaign_id": c["component_id"], "name": c["name"], "size": len(c["skills"]),
            "known_bad": len(c["bad"]), "members": [node_id(s) for s in c["skills"]],
            "shared_infra": [node_id(n) for n in c["infra"]],
        })
    return out


@app.post("/api/investigate", response_model=InvestigateResponse)
def investigate_endpoint(req: InvestigateRequest):
    return investigate(req.name.strip(), req.text)


@app.get("/api/eval", response_model=EvalResponse)
def eval_results(refresh: bool = False):
    return evaluate.load_or_run(force=refresh)


# ---------------------------------------------------------------- optional: serve the built website
# Set FRONTEND_DIST (e.g. in the single-container deploy) and the API also serves the React app,
# so the site and API share one URL. Registered last, so every /api route above wins.
_DIST = Path(os.getenv("FRONTEND_DIST", "")) if os.getenv("FRONTEND_DIST") else None
if _DIST and (_DIST / "index.html").is_file():
    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise ApiError(404, "not_found", f"No endpoint /{path}")
        f = (_DIST / path).resolve()
        if path and f.is_file() and _DIST.resolve() in f.parents:
            return FileResponse(f)
        return FileResponse(_DIST / "index.html")   # client-side routes like /check/<name>
