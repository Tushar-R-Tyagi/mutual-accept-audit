import json, sys
# Builds the "no reward, no verdict review" arm from the no-verdict-review notebook (to_ablation.py noreview).
SRC, DST = sys.argv[1], sys.argv[2]
nb = json.load(open(SRC)); cells = nb["cells"]
get = lambda i: "".join(cells[i]["source"])
def put(i, s): cells[i]["source"] = s.splitlines(keepends=True)
def rep(i, old, new):
    s = get(i); assert s.count(old) == 1, f"cell {i}: {old[:80]!r} x{s.count(old)}"
    put(i, s.replace(old, new))

put(0, """# Ablation: no reward, no verdict review (DeepSeek V4.1 Flash through OpenRouter)

The baseline with the incentive and all outcome feedback removed. The agents keep their tasks, the verdict policy,
the 5-round chat and full memory of earlier episodes (their own messages, verdicts and their partner's messages).
They are **never told to maximize anything, never see a score, and never learn whether any verdict was right**.
Episodes end in silence: with reward off the harness also turns the private reflection off.

Harness flags `--no-reward --no-verdict-review`; the harness code is untouched. The harness still computes the
reward behind the scenes, so the report's reward column is filled in, but the agents never see it.

**Question:** does rule-breaking appear without an objective and without feedback, from the rule, the chat and the
history alone? The paper's "No reward" arm kept verdict review; this arm removes both.

Provider pinned to the baseline's (InferenceNet), same task sequences. Own Drive folder, budget ledger and
SMOKE → PILOT gates. One trajectory: run SMOKE, then PILOT.
""")

rep(2, '''VERDICT_REVIEW = False               # the change in this arm''',
       '''REWARD = False                      # the change in this arm: no reward objective, no reward feedback
VERDICT_REVIEW = False               # the change in this arm: no right/wrong verdict feedback''')
rep(2, '''MODEL_LABEL = "DeepSeek-V4.1-Flash-no-verdict-review"''', '''MODEL_LABEL = "DeepSeek-V4.1-Flash-no-reward-no-review"''')
rep(2, '''    "Ablation: verdict review off (agents see their reward but not which verdicts were right or wrong).",''',
       '''    "Ablation: reward off (no reward objective in the prompt, no reward feedback, and so no reflection) and "
    "verdict review off; agents keep the policy, the chat and their interaction history.",''')

# validation and its self-test: reflection and reward follow REWARD
rep(16, '''"reflection": True,
             "reward": True,''', '''"reflection": REWARD,
             "reward": REWARD,''')
rep(17, '''"reflection": True, "reward": True,''', '''"reflection": REWARD, "reward": REWARD,''')

# configuration record and the runner command
rep(23, '''"reward": f"{REWARD_SCOPE} {REWARD_TYPE}",''', '''"reward": f"{REWARD_SCOPE} {REWARD_TYPE}" if REWARD else "none",''')
rep(23, '''"reflection": True,''', '''"reflection": REWARD,''')
rep(25, '''"--reward-scope", REWARD_SCOPE, "--reward-type", REWARD_TYPE,''',
        '''*(["--reward-scope", REWARD_SCOPE, "--reward-type", REWARD_TYPE] if REWARD else ["--no-reward"]),''')

json.dump(nb, open(DST, "w"), indent=1)
print("silent cells:", len(cells))
