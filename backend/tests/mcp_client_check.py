"""Manual MCP smoke test: starts mcp_server.py over stdio, lists tools, calls them.
Run from backend/:  python tests/mcp_client_check.py
"""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER = Path(__file__).resolve().parents[1] / "mcp_server.py"


async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            print("tools:", [t.name for t in tools.tools])
            r = await s.call_tool("check_install", {"kind": "skill", "name": "demo-crypto-tracker"})
            print("check_install:", r.content[0].text)
            r = await s.call_tool("explain_verdict", {"name": "demo-crypto-tracker"})
            print("explain_verdict:\n" + r.content[0].text)


asyncio.run(main())
