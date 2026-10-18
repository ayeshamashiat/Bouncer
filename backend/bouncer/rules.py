"""Rulebook v2: evidence -> ALLOW / ASK / BLOCK.

  known_bad itself                          -> BLOCK
  shares a clue directly (path <= 2 hops)   -> BLOCK
  linked through one intermediary (3-4)     -> ASK
  never seen before                         -> ASK   (unknown is not safe)
  no link, and the skill itself is vetted   -> ALLOW (on the community-vetted list)
  no link, publisher has a track record     -> ALLOW (trusted publisher, see TRUSTED_*)
  no link, but nothing vouches for it       -> ASK   (no track record: finding no bad
                                                      evidence is not proof of safety)

Trust only ever turns ASK into ALLOW, and it is checked last, so bad evidence always wins:
a trusted publisher whose new skill links to malware is still blocked.

Thresholds live here only. Change them after the evaluation (A11) and write
the reason in docs/DECISIONS.md.
"""
BLOCK_MAX_HOPS = 2
ASK_MAX_HOPS = 4

# A publisher earns trust with at least this many OTHER community-vetted skills, none of their
# skills malicious, and the oldest vetted one at least this many days old, so a sleeper account
# has to wait it out. A vetted skill with no date doesn't count: the record's age is unknown.
TRUSTED_MIN_VETTED = 2
TRUSTED_MIN_AGE_DAYS = 30

ALLOW, ASK, BLOCK = "ALLOW", "ASK", "BLOCK"

# Rule ids, so the UI/tests can tell which rule fired.
R_KNOWN_BAD = "known_bad"
R_DIRECT = "direct_link"
R_INDIRECT = "indirect_link"
R_UNSEEN = "never_seen"
R_VETTED = "vetted_skill"
R_TRUSTED_PUBLISHER = "trusted_publisher"
R_NO_RECORD = "no_track_record"


def publisher_is_trusted(vetted: int, known_bad: int, age_days: int | None) -> bool:
    """vetted = the publisher's other vetted skills; age_days = age of the oldest dated one."""
    return (known_bad == 0 and vetted >= TRUSTED_MIN_VETTED
            and age_days is not None and age_days >= TRUSTED_MIN_AGE_DAYS)


def decide(seen: bool, status: str | None, hops: int | None,
           trusted_publisher: bool = False) -> tuple[str, str]:
    """Pure function: (seen?, skill status, path length or None, publisher trusted?) -> (verdict, rule id)."""
    if status == "known_bad":
        return BLOCK, R_KNOWN_BAD
    if hops is not None and hops <= BLOCK_MAX_HOPS:
        return BLOCK, R_DIRECT
    if hops is not None and hops <= ASK_MAX_HOPS:
        return ASK, R_INDIRECT
    if not seen:
        return ASK, R_UNSEEN
    if status == "trusted":
        return ALLOW, R_VETTED
    if trusted_publisher:
        return ALLOW, R_TRUSTED_PUBLISHER
    return ASK, R_NO_RECORD
