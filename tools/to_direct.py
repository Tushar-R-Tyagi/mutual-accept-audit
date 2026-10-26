import json, re, sys
# Direct mode for any of the DeepSeek notebooks: starts in PILOT, no SMOKE-first gate, no cost estimates that block a
# run. One safety stays: the launcher refuses a request that could push the real spend past SPEND_LIMIT_USD.
SRC, DST = sys.argv[1], sys.argv[2]
nb = json.load(open(SRC)); cells = nb["cells"]
src = lambda c: "".join(c["source"])
def put(c, s): c["source"] = s.splitlines(keepends=True)

def edit(pattern, repl, flags=0):
    """Apply a regex to the one cell that matches it; fail loudly if zero or several cells match."""
    hits = [c for c in cells if re.search(pattern, src(c), flags)]
    assert len(hits) == 1, f"{pattern[:60]!r} matched {len(hits)} cells"
    put(hits[0], re.sub(pattern, repl, src(hits[0]), count=1, flags=flags))

# 1. start in PILOT; the cap is now only a hard stop on real spend
edit(r'MODE = "SMOKE"', 'MODE = "PILOT"                      # direct mode: no SMOKE run needed first')
edit(r'SPEND_LIMIT_USD = [\d.]+ *#[^\n]*',
     'SPEND_LIMIT_USD = 5.0               # hard stop only: a request that could push real spend past this is refused')

# 2. no "run SMOKE first" gate, and so no config-hash check against a passed SMOKE
edit(r'PREVIOUS = \{"PILOT": "SMOKE", "BASELINE": "PILOT"\}\.get\(MODE\)\n',
     'PREVIOUS = None   # direct mode: PILOT and BASELINE start without an earlier passed mode\n')

# 3. no budget checks from cost estimates: before the run, before each trajectory, or before each episode
edit(r'\n    assert SPENT \+ COMPAT_RESERVE \+ nxt <= SPEND_LIMIT_USD, \(\n.*?\n.*?Raise SPEND_LIMIT_USD in step 1 if you mean to\."\)\n',
     '\n', re.S)
edit(r'\n    if SPENT \+ nxt > SPEND_LIMIT_USD:\n        raise RuntimeError\(.*?rerun steps 1-10 to continue"\)\n', '\n', re.S)
edit(r'"episode_estimates_usd": EST\[:EPISODES\]', '"episode_estimates_usd": []')   # no per-episode estimate gate
edit(r'    fits = sum\(need\.values\(\)\) \+ COMPAT_RESERVE <= SPEND_LIMIT_USD - SPENT\n    print\(.*?\(measured costs replace the projection as episodes finish\)"\)\n?',
     '    print("direct mode: estimates are shown only; nothing stops the run except the hard cap on real spend")\n', re.S)

# 4. say so at the top
first = cells[0]
put(first, src(first).rstrip("\n") + """

**Direct mode.** This notebook starts in PILOT: no SMOKE run first, and no cost estimates that stop a run. The only
safety left is a hard stop: the launcher refuses a request that could push the real spend past `SPEND_LIMIT_USD`.
Each arm still has its own Drive folder, so give a changed arm a new `MODEL_LABEL`.
""")

for c in cells:
    if c["cell_type"] == "code":
        c["outputs"], c["execution_count"] = [], None
json.dump(nb, open(DST, "w"), indent=1)
print("direct:", DST)
