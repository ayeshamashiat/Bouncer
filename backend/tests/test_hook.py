import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
from patterns import match  # noqa: E402

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "hook_bouncer.py"


def test_patterns():
    assert match("clawhub install demo-crypto-tracker") == ("skill", "demo-crypto-tracker")
    assert match("npx clawhub@latest install me/foo@1.0.0") == ("skill", "foo")
    assert match("openclaw skills install bar") == ("skill", "bar")
    assert match("claude mcp add -s user weather -- npx w") == ("mcp", "weather")
    # called by full or relative path (Claude Code sometimes does this)
    assert match("/home/me/bouncer-demo/bin/clawhub install demo-crypto-tracker") == ("skill", "demo-crypto-tracker")
    assert match("cd x && ./node_modules/.bin/clawhub install foo") == ("skill", "foo")
    assert match("/usr/local/bin/claude mcp add weather -- npx w") == ("mcp", "weather")
    assert match("cat /home/me/bin/clawhub") is None
    assert match("ls -la") is None
    assert match("npm install left-pad") is None  # packages are opt-in


def test_hook_silent_on_other_commands():
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": "echo hi"}}), capture_output=True, text=True)
    assert out.returncode == 0 and out.stdout == ""
