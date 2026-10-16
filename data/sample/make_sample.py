"""Generates the SYNTHETIC sample dataset in data/sample/ (fixed seed, reproducible).

This is only for building and testing the backend before Mrittika's real CSVs land (H3).
Real facts (cited to Antiy Labs): publisher hightower6eu, domain socifiapp[.]com and the
five IPs. Every skill name and every other account here is invented and marked synthetic.

Run: python data/sample/make_sample.py
"""
import csv
import random
from pathlib import Path

HERE = Path(__file__).parent
rng = random.Random(42)

REAL_IPS = ["91.92.242[.]30", "95.92.242[.]30", "96.92.242[.]30", "202.161.50[.]59", "54.91.154[.]110"]
REAL_DOMAIN = "socifiapp[.]com"
PUBLISHERS = ["hightower6eu"] + [f"synthetic-acct-{i:02d}" for i in range(1, 12)]
WORDS_A = ["crypto", "wallet", "solana", "eth", "defi", "nft", "token", "yield", "swap", "airdrop", "ledger", "phantom"]
WORDS_B = ["tracker", "helper", "monitor", "sync", "bot", "alerts", "toolkit", "scanner", "bridge", "manager"]
PAYLOADS = ["AMOS-stealer-marker-01", "osascript-display-dialog-pw", "curl-pipe-bash-b64"]

skills, infra, legit = [], [], []
names = set()


def new_name(prefix=""):
    while True:
        n = f"{prefix}{rng.choice(WORDS_A)}-{rng.choice(WORDS_B)}-{rng.randint(1, 999)}"
        if n not in names:
            names.add(n)
            return n


# --- Campaign 1: ClawHavoc-style, 120 synthetic skills on real infrastructure
skills.append(["solana-wallet-x", "hightower6eu", "2026-01-31", "known_bad", "ClawHavoc", "", "true"])
names.add("solana-wallet-x")
infra += [["solana-wallet-x", "domain", REAL_DOMAIN, "antiy"], ["solana-wallet-x", "ip", REAL_IPS[0], "antiy"]]
for i in range(120):
    n = new_name()
    # hightower6eu publishes the most (like the real 677/1184 split)
    pub = "hightower6eu" if rng.random() < 0.45 else rng.choice(PUBLISHERS[1:])
    day = rng.choice(["2026-01-27", "2026-01-28", "2026-01-29", "2026-01-31", "2026-01-31"])
    skills.append([n, pub, day, "known_bad", "ClawHavoc", "", "true"])
    r = rng.random()
    if r < 0.5:
        infra.append([n, "domain", REAL_DOMAIN, "antiy"])
    if r > 0.3:
        infra.append([n, "ip", rng.choice(REAL_IPS), "antiy"])
    if rng.random() < 0.3:
        infra.append([n, "payload", rng.choice(PAYLOADS), "synthetic"])
    if rng.random() < 0.1:
        infra.append([n, "domain", "github[.]com", "synthetic"])  # bad skills also touch supernodes

# --- Campaign 2: a small separate synthetic cluster with its own infra
for i in range(12):
    n = new_name("x-")
    pub = rng.choice(["synthetic-bravo-1", "synthetic-bravo-2"])
    skills.append([n, pub, "2026-02-10", "known_bad", "SyntheticBravo", "", "true"])
    infra.append([n, "domain", "update-check-cdn[.]xyz", "synthetic"])
    if rng.random() < 0.5:
        infra.append([n, "ip", "203.0.113[.]77", "synthetic"])

# --- Hard cases so the evaluation is not trivially perfect:
# "lone wolf" malicious skills: fresh account, no shared infra -> undetectable when hidden
for i in range(10):
    n = new_name("lw-")
    skills.append([n, f"synthetic-lone-{i:02d}", "2026-02-03", "known_bad", "ClawHavoc", "", "true"])
    infra.append([n, "domain", "pypi[.]org", "synthetic"])

# --- Legitimate skills (synthetic): many use github.com, three share a docs host
LEGIT_PUBS = [f"legit-author-{i:02d}" for i in range(1, 26)]
for i in range(45):
    n = f"{rng.choice(['git', 'docs', 'test', 'lint', 'calendar', 'notes', 'pdf', 'csv', 'image', 'weather'])}-{rng.choice(['tools', 'helper', 'runner', 'viewer', 'kit'])}-{i}"
    names.add(n)
    legit.append([n, rng.choice(LEGIT_PUBS), "2025-11-02", "synthetic"])
    if rng.random() < 0.7:
        infra.append([n, "domain", "github[.]com", "synthetic"])
    if rng.random() < 0.3:
        infra.append([n, "domain", "pypi[.]org", "synthetic"])
    if i < 3:
        infra.append([n, "domain", "docs-host[.]io", "synthetic"])  # degree check -> CommonInfra
    if i in (10, 11):
        # legit skills hosted on the same cloud IP range a campaign used -> honest false alarms
        infra.append([n, "ip", "54.91.154[.]110", "synthetic"])

# --- Demo items (Mrittika owns the real list, M1b). Empty publisher = never seen before.
demo = [
    ["demo-crypto-tracker", "hightower6eu", "BLOCK", "1", "demo-crypto-tracker.md"],
    ["demo-pdf-helper", "", "ASK", "2", "demo-pdf-helper.md"],
    ["demo-git-tools", "gitfan-dev", "ALLOW", "3", "demo-git-tools.md"],
    ["demo-weather", "weatherly", "ALLOW", "3", "demo-weather.md"],
    ["solana-wallet-x", "hightower6eu", "BLOCK", "1", ""],
]
infra += [["demo-git-tools", "domain", "github[.]com", "synthetic"],
          ["demo-weather", "domain", "api.open-weather-demo[.]org", "synthetic"]]


def write(name, header, rows):
    with (HERE / name).open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


write("skills.csv", ["skill_name", "publisher", "published_at", "status", "campaign", "source_report", "synthetic"], skills)
write("infra.csv", ["skill_name", "kind", "value_defanged", "source_report"], infra)
write("legit.csv", ["skill_name", "publisher", "published_at", "source_url"], legit)
write("demo/demo_items.csv", ["skill_name", "publisher", "expected_verdict", "scene", "text_file"], demo)
# Synthetic passive-DNS fact: the Scene 2 domain points at a campaign IP
write("resolutions.csv", ["domain", "ip", "source_report"], [["pdfhelper-cdn[.]top", REAL_IPS[0], "synthetic"]])

(HERE / "sources.md").write_text(
    "# Sources (SAMPLE - Mrittika replaces with the real list in data/sources.md)\n\n"
    "id | title | url | what was taken\n"
    "--- | --- | --- | ---\n"
    "antiy | ClawHavoc: Analysis of Large-Scale Poisoning Campaign Targeting the OpenClaw Skill Market (Antiy Labs) | url-pending | publisher hightower6eu, C2 domain, IPs, timeline\n"
    "thn341 | Researchers Find 341 Malicious ClawHub Skills Stealing Data from OpenClaw Users (The Hacker News) | url-pending | 341/2,857 audit numbers\n"
)
print(f"{len(skills)} skills, {len(legit)} legit, {len(infra)} infra rows")
