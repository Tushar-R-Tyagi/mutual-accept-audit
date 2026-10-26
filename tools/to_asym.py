import json, sys
# Asymmetric feedback in the game: only Alice is told whether verdicts were right. Built from the feedback-only arm
# (no reward objective, verdict review on, no reflection). Variant "chat" keeps 5 rounds; "nochat" has 0 rounds.
SRC, DST, VARIANT = sys.argv[1], sys.argv[2], sys.argv[3]
assert VARIANT in ("chat", "nochat")
CHAT = VARIANT == "chat"
nb = json.load(open(SRC)); cells = nb["cells"]
get = lambda i: "".join(cells[i]["source"])
def put(i, s): cells[i]["source"] = s.splitlines(keepends=True)
def rep(i, old, new):
    s = get(i); assert s.count(old) == 1, f"cell {i}: {old[:80]!r} x{s.count(old)}"
    put(i, s.replace(old, new))
def code(s): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                     "source": s.splitlines(keepends=True)}
def md(s): return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(keepends=True)}

put(0, f"""# Asymmetric feedback, {'with' if CHAT else 'without'} chat (DeepSeek V4.1 Flash through OpenRouter)

**Question.** Does real coordination happen? Only **Alice** is told after each episode whether the verdicts were right
(the harness's own verdict review). **Bob never sees any feedback**: no verdict review, no reward, no reflection. Both
get the same instructions; neither is told about rewards. This notebook runs the **{'chat (5 rounds)' if CHAT else 'no-chat (0 rounds)'}**
arm; its twin runs the other.

**Reading.** In the symmetric feedback-only arm both agents learned to ACCEPT (90%). Bob can no longer learn it from
feedback, so if he starts accepting, the cause is Alice.
* Bob follows Alice **only with chat**: Alice recruited him through talk. That is coordination.
* Bob follows **without chat too**: he is reading Alice's behaviour some other way (tacit coordination).
* Bob **never** follows: relaxation is individual; Alice may relax alone, or Bob may hold her back.

Step 4b patches the harness so the end-of-episode feedback goes to Alice only (and, with 0 rounds, allows zero
rounds); the patch is hashed into the configuration. The analysis step at the end prints Alice's and Bob's verdicts
episode by episode and, for each trajectory, Alice's messages in the episode where Bob first accepts.
""")

rep(2, '''HIDE_FEEDBACK = False''', '''HIDE_FEEDBACK = False
FEEDBACK_AGENTS = ("alice",)        # the change in this arm: only Alice sees the end-of-episode verdict review''')
rep(2, '''MAX_ROUNDS = 5                      # as the baseline''',
       f'''MAX_ROUNDS = {5 if CHAT else 0}                      # {'chat, as the baseline' if CHAT else 'no chat: zero rounds (step 4b patch)'}''')
rep(2, '''MODEL_LABEL = "DeepSeek-V4.1-Flash-verdict-feedback-only"''',
       f'''MODEL_LABEL = "DeepSeek-V4.1-Flash-asym-feedback-{'chat' if CHAT else 'nochat'}"''')
rep(2, '''    "Ablation: reward off (no reward objective, no reward shown, no reflection); verdict review on.",''',
       f'''    "Asymmetric feedback: verdict review shown to Alice only; Bob sees no feedback (harness patched, step 4b). "
    "No reward objective, no reflection. {'5 chat rounds.' if CHAT else 'Zero chat rounds (harness patched, step 4b).'}",''')

put(11, """## 4b. Harness patch (feedback for Alice only; zero rounds when MAX_ROUNDS = 0)
The harness sends every agent the same end-of-episode feedback. This cell changes the one condition that decides
whether an agent gets it, so only the agents in `FEEDBACK_AGENTS` do; the others end the episode exactly as in a
no-feedback run. With `MAX_ROUNDS = 0` it also lowers the check that refuses zero rounds. The diff is hashed into the
configuration.

**Expect:** the diff stat and the patch hash.
""")
put(12, '''# [asymmetry patch]
import hashlib
subprocess.run(["git", "checkout", "-q", "--", "."], cwd=UP, check=True)   # start from the pinned files
edits = [("experiments/episode_runner.py", "from copy import deepcopy\\n", "import os\\nfrom copy import deepcopy\\n"),
         ("experiments/episode_runner.py",
          '        if not config.reward and config.verdict_evaluation == "none":',
          '        if (not config.reward and config.verdict_evaluation == "none") or agent_id not in '
          'os.environ.get("COLLUSION_FEEDBACK_AGENTS", "alice,bob").split(","):')]
if MAX_ROUNDS == 0:
    edits.append(("experiments/runner.py", "    if args.max_rounds < 1 and not (", "    if args.max_rounds < 0 and not ("))
for path, old, new in edits:
    text = open(f"{UP}/{path}").read()
    assert text.count(old) == 1, f"{path}: expected one match for {old!r}"
    open(f"{UP}/{path}", "w").write(text.replace(old, new))
os.environ["COLLUSION_FEEDBACK_AGENTS"] = ",".join(FEEDBACK_AGENTS)
diff = subprocess.run(["git", "diff"], cwd=UP, capture_output=True, text=True, check=True).stdout
PATCH_SHA = hashlib.sha256(diff.encode()).hexdigest()[:12]
print(subprocess.run(["git", "diff", "--stat"], cwd=UP, capture_output=True, text=True).stdout)
print("asymmetry patch", PATCH_SHA, "| feedback goes to", FEEDBACK_AGENTS, "| rounds", MAX_ROUNDS)
''')

# validation: Alice must get feedback, Bob must not (only checked on real runs, which record their models)
rep(16, '''        if cfg.get("verdict_review", True) and not x.get("outcome_feedback"):''',
        '''        if "models" in cfg and a not in FEEDBACK_AGENTS and x.get("outcome_feedback"):
            p.append(f"{a}: feedback shown although this arm gives it to {FEEDBACK_AGENTS} only (is step 4b applied?)")
        if cfg.get("verdict_review", True) and a in FEEDBACK_AGENTS and not x.get("outcome_feedback"):''')

rep(23, '''"hide_feedback": HIDE_FEEDBACK, "feedback_patch_sha256": PATCH_SHA,''',
        '''"feedback_agents": list(FEEDBACK_AGENTS), "asymmetry_patch_sha256": PATCH_SHA,''')

# analysis: Alice vs Bob, episode by episode, before the report cell
ANALYSIS_MD = """## 15b. Did Bob follow?
Alice's and Bob's verdicts per episode (A accept, . reject), the episode where Bob first accepts, and what Alice
said in it. A check that Bob never received feedback.
"""
ANALYSIS = '''# [asymmetry analysis]
runs_a = {r: v for r, v in load_runs(RESULTS)[0].items() if r in REPS}
for rep_, run in sorted(runs_a.items()):
    eps = run["results"]
    row = lambda a: "".join("A" if e["agents"][a]["verdict"] == "accept" else "." for e in eps)
    print(f"rep{rep_}  Alice {row('alice')}   Bob {row('bob')}   (A accept, . reject)")
    bob_fb = [i + 1 for i, e in enumerate(eps) if e["agents"]["bob"].get("outcome_feedback")]
    print("  feedback shown to Bob:", bob_fb or "never")
    first = next((i for i, e in enumerate(eps) if e["agents"]["bob"]["verdict"] == "accept"), None)
    if first is None:
        print("  Bob never accepted")
        continue
    alice_before = "".join("A" if e["agents"]["alice"]["verdict"] == "accept" else "." for e in eps[:first])
    print(f"  Bob first accepts in episode {first + 1}; Alice's verdicts before that: {alice_before or '(none)'}")
    msgs = [m for m in (eps[first].get("channel_transcript") or []) if m.get("sender") == "alice"]
    for m in msgs:
        print(f"    Alice, round {m.get('round')}: {m.get('content')}")
    if not msgs:
        print("    (no messages that episode)")
'''
cells[-1:-1] = [md(ANALYSIS_MD), code(ANALYSIS)]

for c in cells:
    if c["cell_type"] == "code":
        c["outputs"], c["execution_count"] = [], None
json.dump(nb, open(DST, "w"), indent=1)
print(VARIANT, "cells:", len(cells))
