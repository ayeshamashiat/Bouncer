"""Bouncer MCP server: lets AI agents CONSULT Bouncer before choosing what to install.
(The hook ENFORCES; this is the polite "ask first" path.)

MCP SDK v2: MCPServer (FastMCP is gone). stdio transport. Never print() to stdout
here: stdout is the protocol channel. Debug output goes to stderr only.

Register with Claude Code (absolute paths):
  claude mcp add bouncer -- /ABS/PATH/.venv/bin/python /ABS/PATH/backend/mcp_server.py
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server import MCPServer  # noqa: E402

from bouncer.check import check_install as _check, last_decision  # noqa: E402
from bouncer import queries  # noqa: E402

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="[bouncer-mcp] %(message)s")
log = logging.getLogger("bouncer-mcp")

mcp = MCPServer(
    name="bouncer",
    instructions=(
        "Bouncer checks AI-agent skills and MCP servers against a threat graph of known "
        "malicious campaigns. Call check_install BEFORE installing any skill, plugin or MCP "
        "server, and follow its verdict: BLOCK = do not install; ASK = stop and ask the user, "
        "showing them the reason; ALLOW = fine to proceed."
    ),
)


@mcp.tool()
def check_install(kind: str, name: str) -> dict:
    """Check whether an item is safe to install. Call this BEFORE installing anything.

    kind: "skill" for ClawHub/OpenClaw skills, "mcp" for MCP servers, "package" for npm/pip.
    name: the item's name or slug, e.g. "crypto-tracker-pro".

    Returns verdict (ALLOW | ASK | BLOCK), a one-line reason, the evidence route through
    the threat graph and the campaign name if any. If the verdict is BLOCK, do not install
    and tell the user why. If ASK, show the reason to the user and wait for their decision.
    """
    if kind not in ("skill", "mcp", "package"):
        kind = "skill"
    log.info("check_install %s %s", kind, name)
    r = _check(kind, name, source="mcp")
    return {"verdict": r["verdict"], "reason": r["reason"], "route": r["route"],
            "campaign": r["campaign"], "checked_at": r["checked_at"], "ms": r["ms"]}


@mcp.tool()
def explain_verdict(name: str) -> str:
    """Explain in plain English why Bouncer gave its latest verdict for an item.
    Use this when the user asks "why was X blocked?". Checks the item first if it was never checked.
    """
    d = last_decision(name)
    if d is None:
        r = _check("skill", name, source="mcp")
        d = {"verdict": r["verdict"], "reason": r["reason"], "route": r["route"],
             "campaign": r["campaign"], "checked_at": r["checked_at"]}
    lines = [f"Verdict for {name}: {d['verdict']} (checked {d['checked_at']}).", f"Reason: {d['reason']}."]
    route = d.get("route") or []
    if len(route) > 1:
        lines.append("Evidence path through the threat graph: " + " -> ".join(route) + ".")
        lines.append(f"That is {len(route) - 1} hops. 2 hops = a directly shared clue "
                     "(same publisher, server, IP or payload); 3-4 hops = linked through one intermediary.")
    if d.get("campaign"):
        lines.append(f"Linked campaign: {d['campaign']}.")
    for node in route:
        if node.startswith("publisher:"):
            rep = queries.publisher_reputation(node.split(":", 1)[1])
            if rep:
                lines.append(f"Publisher {rep['handle']}: {rep['skills']} skills, {rep['known_bad']} known-malicious "
                             f"({rep['known_bad_share']:.0%}), first seen {rep['first_seen']}.")
    lines.append("Verdicts come from fixed graph rules, not from an AI reading the skill's text.")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run("stdio")
