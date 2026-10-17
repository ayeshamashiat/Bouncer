#!/usr/bin/env python3
"""Claude Code PreToolUse hook: checks every install with Bouncer BEFORE it runs.

Claude Code sends the tool call as JSON on stdin. If the Bash command installs a
skill / MCP server, we ask Bouncer and answer deny / ask / allow with the evidence.
Any other command: exit 0 silently (Claude Code carries on as normal).

Try it:
  echo '{"tool_name":"Bash","tool_input":{"command":"clawhub install demo-crypto-tracker"}}' \
    | python hooks/hook_bouncer.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))          # patterns.py
sys.path.insert(0, str(HERE.parent))   # bouncer package (direct-import fallback)

from patterns import match  # noqa: E402

DECISION = {"BLOCK": "deny", "ASK": "ask", "ALLOW": "allow"}


def ask_api(kind: str, name: str) -> dict:
    url = os.getenv("BOUNCER_API_URL", "http://localhost:8000").rstrip("/") + "/api/check"
    body = json.dumps({"kind": kind, "name": name, "source": "hook"}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def ask_direct(kind: str, name: str) -> dict:
    from bouncer.check import check_install
    return check_install(kind, name, source="hook")


def ascii_only(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def build_reason(kind: str, name: str, r: dict) -> str:
    parts = [f"Bouncer {r['verdict']}: {kind} '{name}' - {r['reason']}."]
    if r.get("campaign"):
        parts.append(f"Campaign: {r['campaign']}.")
    if len(r.get("route") or []) > 1:
        parts.append("Evidence path: " + " -> ".join(r["route"]) + ".")
    parts.append(f"({r.get('ms', '?')} ms)")
    alts = [a["name"] for a in r.get("alternatives") or []]
    if alts:
        parts.append("Safer alternatives (trusted, same category, no link to known attacks): " + ", ".join(alts) + ".")
    return ascii_only(" ".join(parts))


def output(decision: str, reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0  # not our business; never break Claude Code on bad input
    command = (event.get("tool_input") or {}).get("command", "")
    hit = match(command)
    if not hit:
        return 0
    kind, name = hit
    try:
        r = ask_api(kind, name)
    except Exception as api_err:
        try:
            r = ask_direct(kind, name)
        except Exception as db_err:
            # Fail safe, not open: if Bouncer is down, a human decides.
            output("ask", ascii_only(f"Bouncer could not check {kind} '{name}' "
                                     f"(API: {api_err}; DB: {db_err}). Unknown is not safe."))
            return 0
    output(DECISION.get(r.get("verdict"), "ask"), build_reason(kind, name, r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
