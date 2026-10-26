import json, sys
# Remove printed dollar estimates and projections; keep the hard cap and the actual-spend ledger.
EDITS = [
    ("are ranked by estimated cost per trajectory.", "are ranked by price."),
    ('''print(f"chosen: {chosen.provider} ({pick}, {chosen.quantization}), about ${chosen['est. $/trajectory']} per trajectory "
      f"with caching, ${PRIOR_TRAJECTORY_USD} without")''',
     '''print(f"chosen: {chosen.provider} ({pick}, {chosen.quantization})")'''),
    ('print("estimated USD per episode, full trajectory:", [round(x, 2) for x in EST], f"= ${sum(EST):.2f}")\n', ""),
    ('''print(f"{MODE} still needs about ${sum(need.values()):.2f}: " + ", ".join(f"rep{r} ${v:.2f}" for r, v in need.items()))\n''', ""),
    ('    print("direct mode: estimates are shown only; nothing stops the run except the hard cap on real spend")\n', ""),
    ('''    print(f"rep{rep}: {'resuming' if state == 'partial' else 'starting'}, estimated ${need:.2f}, "
          f"${SPEND_LIMIT_USD - SPENT:.2f} left  (log: {log_path})")''',
     '''    print(f"rep{rep}: {'resuming' if state == 'partial' else 'starting'}  (log: {log_path})")'''),
    ('EST = estimates()\nprint(f"estimated full trajectory now: ${sum(EST):.2f}")\n', ""),
    ('left = sum(sum(EST[len(runs_all[r]["results"]) if r in runs_all else 0:]) for r in range(1, N_TRAJ + 1))\n'
     'print(f"estimated cost to finish BASELINE ({N_TRAJ} trajectories): ${left:.2f}")\n', ""),
    ("output tokens (thinking included), and USD. Then the measured cost per episode and what the remaining modes should\ncost.",
     "output tokens (thinking included), and USD, then the measured cost per saved episode."),
    ("""* A trajectory starts only if its next episode's estimate fits the budget.
* During it, the gate refuses the first request of an episode whose estimate no longer fits, and any request whose
  worst case could cross the limit. Saved episodes are kept; rerun this cell after raising the limit to resume.""",
     """* The gate refuses any request whose worst case could cross `SPEND_LIMIT_USD`. Saved episodes are kept; rerun this
  cell after raising the limit to resume."""),
]
STEP7 = """## 7. Spend so far
Reads every API call ever journaled under this model's Drive folder (failed ones included) and prices each one
from its own token counts. The only spending control is the hard cap on real spend, `SPEND_LIMIT_USD`.

**Expect:** a spend table (empty on the first run) and the remaining budget.
"""
for path in sys.argv[1:]:
    nb = json.load(open(path)); hits = 0
    for c in nb["cells"]:
        s = "".join(c["source"])
        if c["cell_type"] == "markdown" and s.startswith("## 7. Spend so far and the cost of this mode"):
            s = STEP7; hits += 1
        for old, new in EDITS:
            if old in s:
                s = s.replace(old, new); hits += 1
        c["source"] = s.splitlines(keepends=True)
    json.dump(nb, open(path, "w"), indent=1)
    print(hits, path)
