# Sources

Every row in `skills.csv`, `infra.csv` and `resolutions.csv` cites one of these ids in `source_report`,
or is marked synthetic. Only public pages were used (Graph Hacks rule 6). Nothing from a malicious skill
was downloaded, opened or run.

id | title | url | what was taken
--- | --- | --- | ---
antiy | ClawHavoc: Analysis of Large-Scale Poisoning Campaign Targeting the OpenClaw Skill Market for AI Agents (Antiy CERT, 6 Feb 2026) | https://www.antiy.net/p/clawhavoc-analysis-of-large-scale-poisoning-campaign-targeting-the-openclaw-skill-market-for-ai-agents/ | 12 publisher handles + package counts (1,184 total, hightower6eu 677), 23 skill names, C2 domain socifiapp[.]com, 5 IPs, rentry[.]co / glot[.]io lure hosts, open-meteo[.]com cover API, MD5s, AMOS config string, Mach-O name, openclaw-core fake dependency, archive passwords, payload hosts denboss99 / Ddoy233 / hedefbari, timeline (first skill 27 Jan, 386 on 31 Jan)
thn341 | Researchers Find 341 Malicious ClawHub Skills Stealing Data from OpenClaw Users (The Hacker News, Feb 2026) | https://thehackernews.com/2026/02/researchers-find-341-malicious-clawhub.html | audit numbers: 341 of 2,857 skills malicious, 335 delivering Atomic Stealer; lure themes (crypto, Polymarket, YouTube, auto-updaters, Google Workspace)
koi | ClawHavoc: 341 Malicious Clawed Skills Found by the Bot They Were Targeting (Koi Security, 1 Feb 2026) | https://www.koi.ai/blog/clawhavoc-341-malicious-clawedbot-skills-found-by-the-bot-they-were-targeting | original disclosure (now redirects; read via Antiy and THN, which quote it); campaign name, Prerequisites/ClickFix lure pattern
volt | VoltAgent/awesome-openclaw-skills (commit ad6cb6c) | https://github.com/VoltAgent/awesome-openclaw-skills | the 131 legitimate skills in legit.csv (name, publisher, clawskills.sh URL); publishers flagged by Antiy (e.g. noypearl) removed

## What is real and what is synthetic

- **Real, cited `antiy`, `synthetic=false`**: `polymarket-trading-bot` by `aslaep123`, 27 Jan 2026 (the
  first malicious skill). Antiy gives the name, author and date.
- **Real name, `synthetic=true`**: the other 22 named skills (`google-k53`, `solana-wallet-tracker`,
  `clawhubb`, ...). Antiy publishes the names, but not always the author or date. Where it doesn't, we
  assign one of the 12 real handles, weighted by their real package counts.
- **Infra rows cited `antiy`**: the indicator value is real ClawHavoc infrastructure from the report.
  Antiy publishes indicators for the campaign as a whole, so *which* skill uses *which* indicator is our
  assignment. The exceptions are the three per-file MD5s (`google-k53`, `polymarket-all-in-one`,
  `rankaj`), which Antiy ties to those skills directly.
- **Synthetic skills (`synthetic=true`)**: extra ClawHavoc-style names that bring the campaign to 150
  rows, keep the real publisher proportions and use only the real infrastructure. The 1,184 real
  packages were removed from ClawHub, so no full name list is public.
- **Fully synthetic**: the `SyntheticBravo` campaign (`update-check-cdn[.]xyz`, `203.0.113[.]77`, a
  TEST-NET address), 10 "lone wolf" skills with no shared indicator, every infra link of a legitimate
  skill, `resolutions.csv`, and everything in `demo/`.
- **legit.csv**: real skill names and publishers from a public community list, linked to their
  clawskills.sh pages. Being listed there does not prove a skill is safe; it is our best public
  approximation of "legitimate".

Regenerate: `python data/make_data.py` (fixed seed, same output every run).
