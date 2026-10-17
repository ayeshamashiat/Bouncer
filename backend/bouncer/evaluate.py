"""Hold-out evaluation: can Bouncer catch malicious skills it was NOT told about?

Method (one sentence for the results page):
  For each of 5 random seeds we hide the known_bad label on 30% of malicious skills,
  then run check_install on the hidden ones and on every legitimate skill;
  ASK or BLOCK counts as flagged.

  * Baseline: a blocklist / name match. It catches 0% of hidden items by construction,
    because hiding the label is exactly "not on the blocklist".
  * Works on a COPY of the graph (GRAPH.COPY threat -> threat_eval) so the demo graph
    is never touched.
  * If recall is 100% with 0 false alarms, the test is probably too easy: say so.

Run from backend/:  python -m bouncer.evaluate
"""
import json
import random
import sys
from pathlib import Path

from .check import check_install
from .db import get_db, get_graph, graph_name

HIDE_FRACTION = 0.30
SEEDS = [0, 1, 2, 3, 4]
RESULTS_FILE = Path(__file__).resolve().parents[1] / "eval_results.json"
EVAL_GRAPH_SUFFIX = "_eval"


def _fresh_copy():
    src = graph_name()
    dst = src + EVAL_GRAPH_SUFFIX
    db = get_db()
    if dst in db.list_graphs():
        db.select_graph(dst).delete()
    get_graph(src).copy(dst)
    return db.select_graph(dst)


def run(seeds=SEEDS, hide_fraction=HIDE_FRACTION) -> dict:
    splits, total_ms, n_checks = [], 0.0, 0
    for seed in seeds:
        g = _fresh_copy()
        bad = sorted(r[0] for r in g.query("MATCH (s:Skill {status: 'known_bad'}) RETURN s.name").result_set)
        legit = sorted(r[0] for r in g.query("MATCH (s:Skill {status: 'trusted'}) RETURN s.name").result_set)
        hidden = random.Random(seed).sample(bad, max(1, round(len(bad) * hide_fraction)))
        g.query("UNWIND $names AS n MATCH (s:Skill {name: n}) SET s.status = 'unknown'", {"names": hidden})
        blocklist = set(bad) - set(hidden)

        graph_caught = blocklist_caught = false_alarms = 0
        for name in hidden:
            r = check_install("skill", name, write_back=False, g=g, suggest=False)
            total_ms += r["ms"]; n_checks += 1
            graph_caught += r["verdict"] in ("ASK", "BLOCK")
            blocklist_caught += name in blocklist
        for name in legit:
            r = check_install("skill", name, write_back=False, g=g, suggest=False)
            total_ms += r["ms"]; n_checks += 1
            false_alarms += r["verdict"] in ("ASK", "BLOCK")
        splits.append({"seed": seed, "hidden": len(hidden), "blocklist_caught": blocklist_caught,
                       "graph_caught": graph_caught, "false_alarms": false_alarms, "legit": len(legit)})
        g.delete()

    hidden_total = sum(s["hidden"] for s in splits) or 1
    legit_total = sum(s["legit"] for s in splits) or 1
    return {
        "splits": splits,
        "recall": round(sum(s["graph_caught"] for s in splits) / hidden_total, 3),
        "false_alarm_rate": round(sum(s["false_alarms"] for s in splits) / legit_total, 3),
        "blocklist_recall": round(sum(s["blocklist_caught"] for s in splits) / hidden_total, 3),
        "avg_ms": round(total_ms / n_checks, 1) if n_checks else 0.0,
    }


def load_or_run(force: bool = False) -> dict:
    if not force and RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text())
    res = run()
    RESULTS_FILE.write_text(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    res = load_or_run(force=True)
    print(f"{'seed':>4} {'hidden':>6} {'blocklist':>9} {'bouncer':>7} {'false_alarms':>12} {'legit':>5}")
    for s in res["splits"]:
        print(f"{s['seed']:>4} {s['hidden']:>6} {s['blocklist_caught']:>9} {s['graph_caught']:>7} "
              f"{s['false_alarms']:>12} {s['legit']:>5}")
    print(f"\nrecall {res['recall']:.1%}  vs blocklist {res['blocklist_recall']:.1%}  |  "
          f"false alarms {res['false_alarm_rate']:.1%}  |  avg {res['avg_ms']} ms/check")
    if res["recall"] == 1.0 and res["false_alarm_rate"] == 0.0:
        print("WARNING: perfect score. The test data is probably too easy; say so honestly in the README.")
    print(f"saved to {RESULTS_FILE}")
    sys.exit(0)
