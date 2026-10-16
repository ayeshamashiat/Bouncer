"""Builds Bouncer's real dataset in data/ from the public reports (fixed seed, reproducible).

Source of truth for what is real vs synthetic: data/sources.md. In short:
  REAL (Antiy Labs report): the 12 publisher handles and their package counts, 24 skill names,
       the C2 domain socifiapp[.]com, the 5 IPs, the clipboard hosts rentry[.]co / glot[.]io,
       file hashes, AMOS config string, fake dependency name, archive passwords, release dates
       of the first malicious skills.
  ASSIGNED BY US: which named skill links to which indicator (Antiy publishes the indicators for
       the campaign as a whole, not per skill), and the publisher of named skills whose author
       Antiy does not state. Those rows keep source_report=antiy for the name and are marked
       synthetic=true.
  SYNTHETIC: extra skill names to reach ~150 campaign rows, a second small campaign, "lone wolf"
       hard cases, and infra links for legit skills (github.com, open-meteo.com).

legit.csv is NOT generated here: it was curated once from VoltAgent/awesome-openclaw-skills
(commit ad6cb6c) with every publisher Antiy flags removed. This script only reads it.

Run from the repo root:  python data/make_data.py
Never download, open or run anything from the malicious skills. Metadata and text only.
"""
import csv
import random
from pathlib import Path

HERE = Path(__file__).parent
rng = random.Random(2026)

# ---------------------------------------------------------------- real facts (Antiy Labs)
C2_DOMAIN = "socifiapp[.]com"
IPS = ["91.92.242[.]30", "95.92.242[.]30", "96.92.242[.]30", "202.161.50[.]59", "54.91.154[.]110"]
CLIPBOARD_HOSTS = ["rentry[.]co", "glot[.]io"]

# handle -> malicious packages Antiy attributes to it (sums to 1,184)
PUBLISHERS = {
    "hightower6eu": 677, "sakaen736jih": 390, "moonshine-100rze": 60, "zaycv": 19,
    "aslaep123": 14, "jordanprater": 10, "noreplyboter": 4, "rjnpage": 2, "gpaitai": 2,
    "lvy19811120-gif": 2, "danman60": 2, "noypearl": 2,
}

# Payload markers from the report (CONTAINS edges). Hashes are MD5s from Antiy's partial IOC list.
AMOS_BINARY_MD5 = "md5:be24b44d4895c6bc14e3f98a9687a399"
AMOS_CONFIG = "amos-config:jhzhhfomng"
MACHO_NAME = "macho:sujwb2nsdn93d79q"
FAKE_DEP = "fake-dependency:openclaw-core"
ZIP_PASSWORDS = ["zip-password:1202", "zip-password:openclaw", "zip-password:1234"]
PAYLOAD_HOSTS = ["payload-host:github-denboss99", "payload-host:ddoy233", "payload-host:hedefbari"]
CAMPAIGN_PAYLOADS = [AMOS_BINARY_MD5, AMOS_CONFIG, MACHO_NAME, FAKE_DEP] + ZIP_PASSWORDS + PAYLOAD_HOSTS

# Named skills: (name, publisher or None if Antiy does not say, date or None, per-file MD5 or None)
NAMED = [
    ("polymarket-trading-bot", "aslaep123", "2026-01-27", None),   # first malicious skill
    ("reddit-trends", None, "2026-01-28", None),
    ("base-agent", None, "2026-01-28", None),
    ("bybit-agent", None, "2026-01-29", None),
    ("google-k53", None, None, "md5:5e4428176aeb8cfc7f0391654d683a2a"),
    ("polymarket-all-in-one", None, None, "md5:a3365c837ec2659c2aa04e7010a0db15"),
    ("rankaj", None, None, "md5:2444b3ab5de42fcca22e6025cf018e3b"),
    ("solana-wallet-tracker", None, None, None),
    ("polymarket-trader", None, None, None),
    ("binance-agent", None, None, None),
    ("google-workspace", None, None, None),
    ("gmail-integration", None, None, None),
    ("excel-helper", None, None, None),
    ("youtube-summarize-pro", None, None, None),
    ("x-trends-tracker", None, None, None),
    ("twitter-monitor", None, None, None),
    ("auto-updater", None, None, None),
    ("clawhub-cli", None, None, None),
    ("mac-optimizer", None, None, None),
    ("clawhubb", None, None, None),     # typosquats of clawhub
    ("cllawhub", None, None, None),
    ("clawwhub", None, None, None),
    ("clawdhub1", None, None, None),    # variant cited by Snyk
]
MASS_DAY = "2026-01-31"  # 386 skills from 7 accounts, 354 of them by hightower6eu
CAMPAIGN_DAYS = ["2026-01-27", "2026-01-28", "2026-01-29", "2026-01-30", MASS_DAY, MASS_DAY, MASS_DAY,
                 "2026-02-01", "2026-02-02"]

# Lure themes Koi/Antiy describe: crypto wallets, Polymarket bots, YouTube, auto-updaters, Google Workspace
WORDS_A = ["solana", "phantom", "wallet", "crypto", "polymarket", "bybit", "binance", "youtube",
           "gmail", "gdrive", "x", "reddit", "clawhub", "openclaw"]
WORDS_B = ["tracker", "trader", "bot", "summarize", "monitor", "helper", "sync", "updater", "agent",
           "alerts", "pro", "cli"]
TARGET_CAMPAIGN_ROWS = 150

SKILL_HEADER = ["skill_name", "publisher", "published_at", "status", "campaign", "source_report", "synthetic"]
INFRA_HEADER = ["skill_name", "kind", "value_defanged", "source_report"]

skills, infra = [], []
names: set[str] = set()


def weighted_publisher() -> str:
    handles, weights = zip(*PUBLISHERS.items())
    return rng.choices(handles, weights=weights)[0]


def link_campaign_infra(name: str, source: str) -> None:
    """Attach 1-3 real campaign indicators to a campaign skill (the assignment itself is ours)."""
    r = rng.random()
    if r < 0.55:
        infra.append([name, "domain", C2_DOMAIN, source])
    if r > 0.35:
        infra.append([name, "ip", rng.choice(IPS), source])
    if rng.random() < 0.35:
        infra.append([name, "payload", rng.choice(CAMPAIGN_PAYLOADS), source])
    if rng.random() < 0.12:
        infra.append([name, "domain", rng.choice(CLIPBOARD_HOSTS), source])
    if rng.random() < 0.10:
        infra.append([name, "domain", "github[.]com", "synthetic"])  # bad skills touch supernodes too


def new_name(prefix: str = "") -> str:
    while True:
        n = f"{prefix}{rng.choice(WORDS_A)}-{rng.choice(WORDS_B)}-{rng.randint(2, 999)}"
        if n not in names:
            names.add(n)
            return n


# --- 1. Named ClawHavoc skills (real names)
for name, pub, day, md5 in NAMED:
    names.add(name)
    known_pub = pub is not None
    skills.append([name, pub or weighted_publisher(), day or rng.choice(CAMPAIGN_DAYS), "known_bad",
                   "ClawHavoc", "antiy", "false" if (known_pub and day) else "true"])
    link_campaign_infra(name, "antiy")
    if md5:
        infra.append([name, "payload", md5, "antiy"])  # per-file hash: Antiy ties it to this skill
infra.append(["google-k53", "payload", FAKE_DEP, "antiy"])  # the openclaw-core lure

# Every one of the 12 real accounts publishes at least one skill in our data
covered = {row[1] for row in skills}
for handle in PUBLISHERS:
    if handle not in covered:
        n = new_name()
        skills.append([n, handle, rng.choice(CAMPAIGN_DAYS), "known_bad", "ClawHavoc", "antiy", "true"])
        link_campaign_infra(n, "antiy")

# --- 2. Synthetic ClawHavoc skills on the real infrastructure, in the real publisher proportions
while len(skills) < TARGET_CAMPAIGN_ROWS:
    n = new_name()
    pub = weighted_publisher()
    day = MASS_DAY if pub == "hightower6eu" and rng.random() < 0.5 else rng.choice(CAMPAIGN_DAYS)
    skills.append([n, pub, day, "known_bad", "ClawHavoc", "antiy", "true"])
    link_campaign_infra(n, "antiy")

# --- 3. A second, small, fully synthetic campaign with its own infrastructure (tests WCC separation)
for _ in range(12):
    n = new_name("x-")
    skills.append([n, rng.choice(["synthetic-bravo-1", "synthetic-bravo-2"]), "2026-02-10", "known_bad",
                   "SyntheticBravo", "", "true"])
    infra.append([n, "domain", "update-check-cdn[.]xyz", "synthetic"])
    if rng.random() < 0.5:
        infra.append([n, "ip", "203.0.113[.]77", "synthetic"])  # TEST-NET-3: never a real host

# --- 4. "Lone wolf" malicious skills: fresh account, no shared indicator. Undetectable by design once
#        hidden, so the evaluation cannot be trivially perfect.
for i in range(10):
    n = new_name("lw-")
    skills.append([n, f"synthetic-lone-{i:02d}", "2026-02-03", "known_bad", "ClawHavoc", "", "true"])
    infra.append([n, "domain", "pypi[.]org", "synthetic"])

# --- 5. Infra for legitimate skills (synthetic links; the skills themselves are real, see legit.csv)
legit = list(csv.DictReader((HERE / "legit.csv").open(encoding="utf-8")))
for r in legit:
    n = r["skill_name"]
    if "git" in n:
        infra.append([n, "domain", "github[.]com", "synthetic"])  # supernode case (Scene 3)
    elif rng.random() < 0.35:
        infra.append([n, "domain", rng.choice(["github[.]com", "pypi[.]org", "registry.npmjs[.]org"]),
                      "synthetic"])
weather_like = [r["skill_name"] for r in legit if any(w in r["skill_name"] for w in ("weather", "travel", "flight",
                                                                                       "farm", "garden"))]
for n in (weather_like + [r["skill_name"] for r in legit[:6]])[:4]:
    # open-meteo.com: a legitimate API the campaign used as cover (Antiy). Used by >=3 legit skills,
    # so the degree check makes it CommonInfra.
    infra.append([n, "domain", "open-meteo[.]com", "synthetic"])
for n in [r["skill_name"] for r in legit[40:42]]:
    # Legit skills on the same AWS IP range one campaign IP sits in: honest false-alarm candidates.
    infra.append([n, "ip", "54.91.154[.]110", "synthetic"])

# --- 6. Demo items (data/demo/demo_items.csv): their pre-known infrastructure
infra += [["demo-git-tools", "domain", "github[.]com", "synthetic"],
          ["demo-weather", "domain", "open-meteo[.]com", "synthetic"]]


def write(name: str, header: list[str], rows: list[list[str]]) -> None:
    p = HERE / name
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# de-duplicate identical infra rows (same skill linked twice to the same indicator)
seen, unique = set(), []
for row in infra:
    key = tuple(row[:3])
    if key not in seen:
        seen.add(key)
        unique.append(row)

write("skills.csv", SKILL_HEADER, skills)
write("infra.csv", INFRA_HEADER, unique)
# Scene 2: the new domain in demo-pdf-helper's SKILL.md points at a campaign IP (synthetic passive-DNS fact)
write("resolutions.csv", ["domain", "ip", "source_report"], [["pdfhelper-cdn[.]top", IPS[0], "synthetic"]])

real = sum(1 for s in skills if s[6] == "false")
print(f"{len(skills)} malicious skills ({real} fully real rows, {len(NAMED)} real names), "
      f"{len(legit)} legit, {len(unique)} infra rows")
