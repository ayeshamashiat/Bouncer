"""Skill categories, used to suggest safer alternatives when an install is blocked.

Every skill gets (:Skill)-[:IN_CATEGORY]->(:Category) edges from keywords in its name.
A blocked crypto tracker then finds trusted skills through
    blocked skill -> Category <- trusted skill
and each candidate is re-checked before it is suggested. Categories are never evidence:
IN_CATEGORY is not in the detection relationship list, so it can't make anything look malicious.
"""
import re

# category -> words that put a skill name in it. Kept small and readable on purpose.
CATEGORY_KEYWORDS = {
    "finance & crypto": {
        "crypto", "wallet", "solana", "sol", "eth", "ethereum", "bitcoin", "btc", "binance", "bybit", "defi",
        "aave", "token", "nft", "coin", "polymarket", "trading", "trader", "trade", "stock", "allstock", "share",
        "market", "budget", "accounting", "akaunting", "rebalancer", "portfolio", "price", "finance", "invest",
        "liquidation", "airdrop", "yield", "swap", "ledger", "phantom",
    },
    "git & code": {"git", "github", "gitops", "commit", "changelog", "readme", "code", "repo"},
    "documents & notes": {"pdf", "doc", "docs", "watermark", "notes", "writer", "writing", "academic", "slides", "brain"},
    "weather": {"weather", "forecast", "meteo"},
    "video & audio": {"youtube", "video", "music", "audio", "lyrics", "acestep", "tiktok", "summarize"},
    "social & messaging": {"reddit", "twitter", "telegram", "4chan", "messenger", "mail", "chat", "agentchat", "trends"},
    "calendar & tasks": {"calendar", "todo", "4todo", "tasks", "planner", "cron", "sprint", "reminder"},
    "google workspace": {"google", "gmail", "gdrive", "drive", "workspace"},
    "security": {"security", "guardian", "sentinel", "password", "1password", "passport", "verification", "crypt"},
}
_WORD_TO_CATS: dict[str, set[str]] = {}
for _cat, _words in CATEGORY_KEYWORDS.items():
    for _w in _words:
        _WORD_TO_CATS.setdefault(_w, set()).add(_cat)


def categories_for(name: str) -> list[str]:
    """'demo-crypto-tracker' -> ['finance & crypto'] (sorted, may be empty)."""
    words = re.split(r"[^a-z0-9]+", name.lower())
    cats = set()
    for w in words:
        cats |= _WORD_TO_CATS.get(w, set())
    return sorted(cats)
