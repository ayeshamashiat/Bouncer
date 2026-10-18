"""Which shell commands the hook intercepts, and how to pull the item name out.
All patterns live in this one file.

Install syntax confirmed from the OpenClaw/ClawHub docs (docs.openclaw.ai/clawhub):
  clawhub install <slug>            (also via npx clawhub@latest)
  openclaw skills install <slug>
"""
import os
import re

# (kind, regex). Group "name" is the item being installed.
# _P = an optional path before the program name, so "/home/me/bin/clawhub install x" and
# "./node_modules/.bin/clawhub install x" are caught too (not only a bare "clawhub").
_P = r"""(?:["']?[^\s;&|"']*/)?"""
_SKILL = [
    re.compile(r"(?:^|[\s;&|(])" + _P + r"(?:npx\s+(?:-y\s+)?)?clawhub(?:@\S+)?\s+(?:install|add)\s+(?:--?\S+\s+)*(?P<name>[^\s;&|]+)"),
    re.compile(r"(?:^|[\s;&|(])" + _P + r"openclaw\s+skills?\s+(?:install|add)\s+(?:--?\S+\s+)*(?P<name>[^\s;&|]+)"),
]
_MCP = [
    # claude mcp add [options] <name> <command...>
    re.compile(r"(?:^|[\s;&|(])" + _P + r"claude\s+mcp\s+add(?:-json)?\s+(?:(?:-s|--scope|-t|--transport|-e|--env|-H|--header)\s+\S+\s+|--?\S+\s+)*(?P<name>[^\s;&|-][^\s;&|]*)"),
]
# Optional: npm / pip packages. Off unless BOUNCER_HOOK_PACKAGES=1.
_PACKAGE = [
    re.compile(r"(?:^|[\s;&|(])" + _P + r"npm\s+(?:install|i|add)\s+(?:--?\S+\s+)*(?P<name>[^\s;&|-][^\s;&|]*)"),
    re.compile(r"(?:^|[\s;&|(])" + _P + r"pip3?\s+install\s+(?:--?\S+\s+)*(?P<name>[^\s;&|-][^\s;&|]*)"),
]


def _clean(name: str) -> str:
    name = name.strip("'\"")
    if "/" in name and not name.startswith("@"):
        name = name.rstrip("/").rsplit("/", 1)[-1]  # owner/skill -> skill
    name = re.sub(r"@[^/]*$", "", name) if not name.startswith("@") else name  # drop @version
    return name


def match(command: str) -> tuple[str, str] | None:
    """Returns (kind, item_name) if this command installs something, else None."""
    if not command:
        return None
    groups = [("skill", _SKILL), ("mcp", _MCP)]
    if os.getenv("BOUNCER_HOOK_PACKAGES") == "1":
        groups.append(("package", _PACKAGE))
    for kind, patterns in groups:
        for p in patterns:
            m = p.search(command)
            if m:
                name = _clean(m.group("name"))
                if name:
                    return kind, name
    return None


if __name__ == "__main__":
    import sys
    cmd = " ".join(sys.argv[1:])
    print(match(cmd))
