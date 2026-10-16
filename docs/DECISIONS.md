# Decisions

One line per important choice: what, why, who. Newest at the bottom.

| Date | Decision | Why | Who |
|---|---|---|---|
| 16 Oct | Graph model = Skill, Publisher, Domain, IP, PayloadString, CommonInfra, Campaign, Report, Finding, Decision (playbook §9). | Every shared clue is its own node, so two skills that share it are 2 hops apart. | Ayesha |
| 16 Oct | Load with `UNWIND $rows` + `MERGE` on the key property only, then `SET` the rest. | Shared clues must be ONE node or nothing connects; running the loader twice gives the same graph. | Ayesha |
| 16 Oct | One canonical spelling for indicators: lowercase, last dot as `[.]` (`socifiapp[.]com`, `91.92.242[.]30`). Loader and investigator use the same function (`defang.py`). | Two spellings of the same domain would be two nodes and the link would be lost. | Ayesha |
| 16 Oct | Supernodes get their own label `CommonInfra` (allowlist such as github.com, pypi.org + degree check: used by ≥3 legit skills). | FalkorDB algorithms filter by label, not property. Paths through github.com prove nothing. | Ayesha |
| 16 Oct | Guilt-by-connection uses one query per path length (2, then 3, then 4) and stops at the first hit, instead of `shortestPath()` or one `*1..4` query. | `shortestPath()` is directed-only in FalkorDB; our clues point both ways. A single `*1..4` query explodes through a publisher with hundreds of skills. | Ayesha |
| 16 Oct | Rulebook v1: known_bad → BLOCK; ≤2 hops → BLOCK; 3–4 hops → ASK; never seen → ASK; seen, no link → ALLOW. | 2 hops = a directly shared clue; 4 = one intermediary; longer chains are weak evidence. Unknown is not safe. | Ayesha |
| 16 Oct | Campaigns = WCC over the 5 evidence labels and 5 strong relationship types only; a group needs ≥2 skills and ≥1 known_bad. | One weak link would merge everything; excluding CommonInfra/PART_OF/ABOUT keeps groups meaningful. | Ayesha |
| 16 Oct | Every verdict writes `(:Decision)-[:ABOUT]->(:Skill)`; never-seen items get a Decision without the ABOUT edge and **no** Skill node. | Creating a Skill for a never-seen name would turn the next check from ASK into ALLOW. | Ayesha |
| 16 Oct | `demo_items.csv` rows with an empty publisher are not preloaded (= never seen). | Scene 2: the item is unknown until the investigator reads its text. | Ayesha |
| 16 Oct | Optional `data/resolutions.csv` (domain → IP, passive-DNS style facts). | The investigator never resolves or fetches anything, so domain→IP facts must come from reports. | Ayesha |
| 16 Oct | Investigator: LLM only fills `{domains, urls, ips, commands}`; output validated item by item; unioned with regex results; regex-only fallback; rules decide. | Prompt-injection safety: attacker text can neither add a verdict nor hide an indicator. | Ayesha |
| 16 Oct | Hook: BLOCK→deny, ASK→ask, ALLOW→allow. If the API and DB are both unreachable → **ask** (fail safe, not open). Packages (npm/pip) only with `BOUNCER_HOOK_PACKAGES=1`. | A security hook that silently allows when broken is worse than none. | Ayesha |
| 16 Oct | Gotcha: in FalkorDB `MATCH (x) WHERE id(x)=$id MATCH (x)-[]-()` ignores the binding; we add `WITH x` between. | Found while testing; counts were 133 instead of 51. | Ayesha |
| 16 Oct | Evaluation runs on `GRAPH.COPY threat → threat_eval`, 5 seeds, 30% of known_bad hidden, ASK or BLOCK = flagged. | Testing on labels we loaded would be circular; the demo graph must stay untouched. | Ayesha |
