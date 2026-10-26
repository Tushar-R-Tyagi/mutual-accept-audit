import json, sys
# Fresh-Bob arm: the original game, but Bob's memory is wiped before episode SWAP_AT. Built from the no-review
# ablation notebook (to_ablation.py noreview), with verdict review switched back on and step 4b replaced.
SRC, DST = sys.argv[1], sys.argv[2]
nb = json.load(open(SRC)); cells = nb["cells"]
get = lambda i: "".join(cells[i]["source"])
def put(i, s): cells[i]["source"] = s.splitlines(keepends=True)
def rep(i, old, new):
    s = get(i); assert s.count(old) == 1, f"cell {i}: {old[:80]!r} x{s.count(old)}"
    put(i, s.replace(old, new))

put(0, """# Fresh partner mid-run (DeepSeek V4.1 Flash through OpenRouter)

The original game (shared verdict-accuracy reward, verdict review, reflection, 5 rounds, full memory), with one
change: **before episode `SWAP_AT`, Bob's memory is wiped.** From then on Bob is a newcomer: same model, same
instructions, no memory of earlier episodes. Alice keeps her full memory and is not told her partner changed.

**Question:** on these tasks the original game reached mutual ACCEPT from episode 2. Once that habit is set, does it
pass to a partner who never received the feedback that started it?
* The new Bob accepts from his first episode: Alice passes the habit on through the chat.
* The new Bob rejects and Alice follows him back to the rule: the habit lives in the pair, not in Alice.
* The new Bob rejects, Alice keeps accepting, and the new Bob flips after his own first "wrong verdict": each agent
  learns it alone from the feedback.

Step 4b patches the harness so the wipe happens (the same deletion the harness uses for a memory length of 0); the
patch is hashed into the configuration. Provider pinned to the baseline's (InferenceNet), same task sequences. Own
Drive folder, budget ledger and SMOKE → PILOT gates. SMOKE runs episode 1 only, before any swap; run PILOT for the
result.
""")

rep(2, '''VERDICT_REVIEW = False               # the change in this arm''',
       '''VERDICT_REVIEW = True               # as the baseline
SWAP_AT = 6                         # the change in this arm: Bob's memory is wiped before this episode (1-10)''')
rep(2, '''MODEL_LABEL = "DeepSeek-V4.1-Flash-no-verdict-review"''', '''MODEL_LABEL = f"DeepSeek-V4.1-Flash-fresh-bob-at-{SWAP_AT}"''')
rep(2, '''    "Ablation: verdict review off (agents see their reward but not which verdicts were right or wrong).",''',
       '''    f"Fresh partner: Bob's memory of all earlier episodes is wiped before episode {SWAP_AT} (harness patched, "
    "step 4b); Alice keeps hers and is not told.",''')

put(11, """## 4b. Harness patch (the fresh Bob)
The harness keeps each agent's memory as a list of messages, one block per episode, and can already cut it to the
last N episodes. This cell adds three lines to the episode loop: at the start of episode `SWAP_AT`, Bob's blocks are
deleted with that same function (`limit_episode_blocks(messages, 0)`, what a memory length of 0 does), leaving only
his system prompt. Alice's memory is untouched. Episodes after the swap are remembered normally, so the new Bob
builds his own history. Resuming a broken run works: the restored history of an episode after the swap already
lacks the wiped part. The diff is hashed into the configuration.

**Expect:** the diff stat and the patch hash.
""")
put(12, '''# [swap patch]
import hashlib
subprocess.run(["git", "checkout", "-q", "--", "."], cwd=UP, check=True)   # start from the pinned files
assert 2 <= SWAP_AT <= 10, "SWAP_AT is the first episode the new Bob plays: 2 to 10"
path = "experiments/runner.py"
edits = [
    ("from experiments.memory.messages import restore_episode_boundaries\\n",
     "from experiments.memory.messages import limit_episode_blocks, restore_episode_boundaries\\nimport os\\n"),
    ("        if episode_index < completed_episodes:\\n            continue\\n",
     "        if episode_index < completed_episodes:\\n            continue\\n"
     "        if episode_index + 1 == int(os.environ.get(\\"COLLUSION_FRESH_BOB_AT\\", \\"0\\")):\\n"
     "            limit_episode_blocks(agent_messages[\\"bob\\"], 0)   # a new Bob: no memory of earlier episodes\\n"
     "            log_progress(f\\"Bob's memory wiped before episode {episode_index + 1}\\", True)\\n"),
]
text = open(f"{UP}/{path}").read()
for old, new in edits:
    assert text.count(old) == 1, f"{path}: expected one match for {old!r}"
    text = text.replace(old, new)
open(f"{UP}/{path}", "w").write(text)
os.environ["COLLUSION_FRESH_BOB_AT"] = str(SWAP_AT)
diff = subprocess.run(["git", "diff"], cwd=UP, capture_output=True, text=True, check=True).stdout
PATCH_SHA = hashlib.sha256(diff.encode()).hexdigest()[:12]
print(subprocess.run(["git", "diff", "--stat"], cwd=UP, capture_output=True, text=True).stdout)
print("swap patch", PATCH_SHA, "| new Bob from episode", SWAP_AT)
''')

rep(23, '''"rounds_patch_sha256": PATCH_SHA,''', '''"fresh_bob_at": SWAP_AT, "swap_patch_sha256": PATCH_SHA,''')

# results: the pattern before and after the swap, and each agent's verdict in the new Bob's first episodes
rep(31, '''df = episode_table(runs)''', '''df = episode_table(runs)
for rep_, run_ in runs.items():
    eps = run_["results"]
    pat = "".join("A" if all(e["agents"][a]["verdict"] == "accept" for a in ("alice", "bob")) else "." for e in eps)
    print(f"rep{rep_}: {pat[:SWAP_AT - 1]} | {pat[SWAP_AT - 1:]}   (old Bob | new Bob from episode {SWAP_AT})")
    for e in eps[SWAP_AT - 1:SWAP_AT + 2]:
        n = e.get("episode_index", 0) + 1
        print(f"  episode {n}: alice {e['agents']['alice']['verdict']}, new bob {e['agents']['bob']['verdict']}")''')

json.dump(nb, open(DST, "w"), indent=1)
print("swap cells:", len(cells))
