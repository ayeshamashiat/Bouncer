"""Rulebook v1: evidence -> ALLOW / ASK / BLOCK.

  known_bad itself                          -> BLOCK
  shares a clue directly (path <= 2 hops)   -> BLOCK
  linked through one intermediary (3-4)     -> ASK
  never seen before                         -> ASK   (unknown is not safe)
  seen, no link after skipping supernodes   -> ALLOW

Thresholds live here only. Change them after the evaluation (A11) and write
the reason in docs/DECISIONS.md.
"""
BLOCK_MAX_HOPS = 2
ASK_MAX_HOPS = 4

ALLOW, ASK, BLOCK = "ALLOW", "ASK", "BLOCK"

# Rule ids, so the UI/tests can tell which rule fired.
R_KNOWN_BAD = "known_bad"
R_DIRECT = "direct_link"
R_INDIRECT = "indirect_link"
R_UNSEEN = "never_seen"
R_CLEAN = "no_link"


def decide(seen: bool, status: str | None, hops: int | None) -> tuple[str, str]:
    """Pure function: (seen?, skill status, path length or None) -> (verdict, rule id)."""
    if status == "known_bad":
        return BLOCK, R_KNOWN_BAD
    if hops is not None and hops <= BLOCK_MAX_HOPS:
        return BLOCK, R_DIRECT
    if hops is not None and hops <= ASK_MAX_HOPS:
        return ASK, R_INDIRECT
    if not seen:
        return ASK, R_UNSEEN
    return ALLOW, R_CLEAN
