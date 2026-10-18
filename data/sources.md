# Sources

Every row in `skills.csv`, `infra.csv` and `resolutions.csv` cites one of these ids in `source_report`,
or is marked synthetic. Only public pages were used (Graph Hacks rule 6). Nothing from a malicious skill
was downloaded, opened or run.

id | title | url | what was taken
--- | --- | --- | ---
antiy | ClawHavoc: Analysis of Large-Scale Poisoning Campaign Targeting the OpenClaw Skill Market for AI Agents (Antiy CERT, 6 Feb 2026) | https://www.antiy.net/p/clawhavoc-analysis-of-large-scale-poisoning-campaign-targeting-the-openclaw-skill-market-for-ai-agents/ | 12 publisher handles + package counts (1,184 total, hightower6eu 677), 23 skill names, C2 domain socifiapp[.]com, 5 IPs, rentry[.]co / glot[.]io lure hosts, open-meteo[.]com cover API, MD5s, AMOS config string, Mach-O name, openclaw-core fake dependency, archive passwords, payload hosts denboss99 / Ddoy233 / hedefbari, timeline (first skill 27 Jan, 386 on 31 Jan)
thn341 | Researchers Find 341 Malicious ClawHub Skills Stealing Data from OpenClaw Users (The Hacker News, Feb 2026) | https://thehackernews.com/2026/02/researchers-find-341-malicious-clawhub.html | audit numbers: 341 of 2,857 skills malicious, 335 delivering Atomic Stealer; lure themes (crypto, Polymarket, YouTube, auto-updaters, Google Workspace)
koi | ClawHavoc: 341 Malicious Clawed Skills Found by the Bot They Were Targeting (Koi Security, 1 Feb 2026) | https://www.koi.ai/blog/clawhavoc-341-malicious-clawedbot-skills-found-by-the-bot-they-were-targeting | original disclosure (now redirects; read via Antiy and THN, which quote it); campaign name, Prerequisites/ClickFix lure pattern
osm | Clawdbot skills ganked your crypto / Malicious ClawHub skills target OpenClaw users (OpenSourceMalware, Feb 2026) | https://opensourcemalware.com/blog/malicious-clawhub-skills-target-openclaw-users | skill → publisher lists for aslaep123, zaycv, jordanprater, gpaitai, lvy19811120-gif, danman60; the payload each skill fetches (PolymarketAuthTool.zip, openclawcli.zip, ClawdAuthenticatorTool.zip, base64 piped to bash); payload GitHub accounts Aslaep123, keepcold131, Ddoy233; zip password "poly"; early-wave dates
snyk-clawdhub | Inside the 'clawdhub' Malicious Campaign (Snyk, 4 Feb 2026) | https://snyk.io/articles/clawdhub-malicious-campaign-ai-agent-skills/ | clawhub and clawdhub1 by zaycv (2–3 Feb), C2 91.92.242[.]30, glot[.]io snippet, decoy download.setup-service[.]com, marker 528n21ktxu08pmer, github Ddoy233/openclawcli, zip password "openclaw"
snyk-google | How a Malicious Google Skill on ClawHub Tricks Users Into Installing Malware (Snyk, 10 Feb 2026) | https://snyk.io/blog/clawhub-malicious-google-skill-openclaw-malware/ | google-qx4, fake dependency openclaw-core, github denboss99, rentry[.]co/openclaw-core, setup-service[.]com
unit42 | OpenClaw's Skill Marketplace and the Emerging AI Supply Chain Threat (Palo Alto Networks Unit 42, 23 Jun 2026) | https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/ | 11 skill names (publishers redacted except krajekisbtc), C2 2.26.75[.]16, "cluw" stealer SHA-256, omnicogg on 91.92.242[.]30, laosji[.]net, letssendit[.]fun, Telegram Bot API exfiltration
polyswarm | The ClawHavoc Campaign (PolySwarm, 27 Feb 2026) | https://blog.polyswarm.io/the-clawhavoc-campaign | the skill name better-polymarket
gh152 | Malicious Skill Report (polymarket-all-in-one), openclaw/clawhub issue #152 (5 Feb 2026) | https://github.com/openclaw/clawhub/issues/152 | polymarket-all-in-one is published by noreplyboter; reverse shell in scripts/polymarket.py
ocsm | adibirzu/openclaw-security-monitor IOC lists (MIT, accessed 18 Oct 2026) | https://github.com/adibirzu/openclaw-security-monitor | rankaj is published by rjnpage (the list cites Bloom Security, whose post we could not open). Only this one fact was taken: the lists also contain entries we could not verify, including a documentation-only IP
volt | VoltAgent/awesome-openclaw-skills (commit ad6cb6c) | https://github.com/VoltAgent/awesome-openclaw-skills | the 131 legitimate skills in legit.csv (name, publisher, clawskills.sh URL); publishers flagged by Antiy (e.g. noypearl) removed

## What is real and what is synthetic

- **Real, named by later reports (18 Oct update)**: 35 skills now come with a real publisher and/or the
  indicators a report ties to that exact skill (`osm`, `snyk-*`, `unit42`, `gh152`, `polyswarm`, `ocsm`).
  Six of them correct a publisher we had assigned before (reddit-trends, base-agent, bybit-agent →
  aslaep123; polymarket-all-in-one → noreplyboter; rankaj → rjnpage; clawdhub1 → zaycv). Where a report
  gives no date we use a day inside the reported wave; Unit 42 rows use the report date. An empty
  publisher means the report redacts it, and such skills get no Publisher node.

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
