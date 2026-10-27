# When is mutual rule-breaking evidence of collusion?

Code, notebooks and run data for my submission to the Apart Research AI Collusion Research Sprint (October 2026),
Track 2: Detection and audit.

**Paper:** [`paper/Tyagi_Collusion_Sprint_Submission.pdf`](paper/Tyagi_Collusion_Sprint_Submission.pdf)

**Pre-sprint work** (replication, ESCALATE, logrolling): [AI-Agentic-Collusion-Replication](https://github.com/Tushar-R-Tyagi/AI-Agentic-Collusion-Replication)

**Harness:** [SALT-NLP/agent-collusion](https://github.com/SALT-NLP/agent-collusion) at commit
`5afb2c595aa3eff6b9b829a032f4f117b36ee54d` (Shi, Zhang & Yang, 2026, [arXiv:2609.24967](https://arxiv.org/abs/2609.24967))

## The question

Shi et al. report that two LLM agents who judge each other's work drift into mutual ACCEPT, waving work through
without the evidence their verdict policy demands. Their headline metric counts episodes in which both accept. That
count fits two stories: the agents coordinate, or each agent learns separately from its own feedback that following
the rule is graded wrong. I test which one it is, and turn the controls into an audit standard for collusion claims.

## Main results

DeepSeek V4.1 Flash via OpenRouter (InferenceNet, fp8, no fallbacks), 5 trajectories per arm, episodes 2 to 10.
Arms in a comparison share task sequences.

| Arm | Bob accepts | Both accept |
|---|---|---|
| Verdict feedback to both agents (symmetric control) | 44 / 45 | 44 / 45 |
| Feedback to Alice only, chat | 0 / 45 | 0 / 45 |
| Feedback to Alice only, no chat | 0 / 45 | 0 / 45 |
| Positive control (planted relay protocol), chat | 44 / 45 | 44 / 45 |
| Positive control (planted relay protocol), no chat | 0 / 45 | 0 / 45 |

- Without his own feedback, Bob never accepted, with or without chat, even while Alice lobbied him. At the
  trajectory level: 5 of 5 against 0 of 10, two-sided Fisher's exact test p = 0.0003.
- When coordination is planted (Alice must relay her feedback and Bob must follow it), Bob follows only when the
  message can reach him: 5 of 5 against 0 of 5 trajectories, p = 0.008. All 5 chat trajectories meet the
  passing criteria, which were fixed before the runs and are checked in the analysis step.
- Comparing the joint rate with the product of the individual rates misses the planted coordination (44 observed,
  44 expected), so that comparison should never be used alone.

## Repository map

| Path | Contents |
|---|---|
| `paper/` | The submitted report. |
| `notebooks/main/` | The five arms behind the main claims. Each is a self-contained Colab notebook: settings, pinned harness install, the harness patch for that arm (hashed into the run configuration), validators, the run, analysis and an HTML report. |
| `notebooks/screens/` | Single-trajectory screens that steered the design (paper, Appendix C). |
| `notebooks/workflow/` | The code-review workflow study (paper, Appendix D). |
| `results/` | By arm: `report_*.html`, the full report with every episode's messages, verdicts and reasoning; `record_*.json`, the run configuration and its hash; `export_*/`, the episode and trajectory tables as CSV; and `runs/rep<k>.json`, the raw saved trajectories. Core arms keep only their final (BASELINE) outputs; screens are single PILOT runs. |
| `tools/` | The scripts that derived each notebook from the replication notebook, so every difference between arms can be checked. |

| Notebook | Paper | Drive label in `results/` |
|---|---|---|
| `main/symmetric_feedback.ipynb` | 3.3, Figure 1 | `DeepSeek-V4.1-Flash-verdict-feedback-only` |
| `main/asymmetric_feedback_chat.ipynb` | 3.3, Figure 1 | `DeepSeek-V4.1-Flash-asym-feedback-chat` |
| `main/asymmetric_feedback_nochat.ipynb` | 3.3, Figure 1 | `DeepSeek-V4.1-Flash-asym-feedback-nochat` |
| `main/positive_control_chat.ipynb` | 3.5, Table 1 | `DeepSeek-V4.1-Flash-planted-chat` |
| `main/positive_control_nochat.ipynb` | 3.5, Table 1 | `DeepSeek-V4.1-Flash-planted-nochat` |
| `screens/noreview.ipynb` | Appendix C | `DeepSeek-V4.1-Flash-no-verdict-review` |
| `screens/nochat.ipynb` | Appendix C | `DeepSeek-V4.1-Flash-no-communication` |
| `screens/noreward_noreview.ipynb` | Appendix C | `DeepSeek-V4.1-Flash-no-reward-no-review` |
| `screens/rewardonly.ipynb` | Appendix C | `DeepSeek-V4.1-Flash-reward-objective-only` |
| `screens/fresh_bob.ipynb` | Appendix C | `DeepSeek-V4.1-Flash-fresh-bob-at-6` |
| `workflow/code_review_forced_choice.ipynb` | Appendix D | `code-review-forced-choice-v2-audited` |

## Reproducing a run

1. Open a notebook in Google Colab and add `OPENROUTER_API_KEY` under Colab's Secrets. The key is never printed or
   saved.
2. In step 1, set `MODE = "BASELINE"` and `N_TRAJ`. Trajectory *k* uses the paper's fixed task sequence *k*, so the
   same *k* is matched across arms. Results go to Google Drive, and finished trajectories are skipped on rerun.
3. Run all. The run stops at the first episode that fails validation, and `SPEND_LIMIT_USD` is a hard cap on real
   spend. A trajectory takes about 15 to 20 minutes.

Sampling is not seeded, so reruns are not token-identical. The positive-control verdict (PASS, CONTROL NOT
ACTIVATED, CONFOUNDED, FAIL, UNCLEAR) is printed in step 15b of the chat notebook, once both twins have finished.

## Work done before the sprint

The sprint began on 23 October 2026. These parts predate it:

| Work | Date | Where |
|---|---|---|
| Replication on Gemini 3.8 Flash (1 trajectory) and DeepSeek V4.1 Flash (10 trajectories) | by 18 Oct | pre-sprint repo; paper 3.1 |
| ESCALATE and logrolling screens | by 21 Oct | pre-sprint repo; paper Appendix C, E |
| Screens: no verdict review, no chat, no reward and no review, reward instruction only | 22 Oct | `notebooks/screens/`; paper Appendix C |
| Symmetric feedback-only arm, trajectory 1 | 22 Oct | trajectory 1 of `main/symmetric_feedback` |

Everything else (the asymmetric arms, the positive control, trajectories 2 to 5 of the symmetric control, the
workflow study, the fresh-Bob screen, the audit standard and the report) was done during the sprint. The paper
reports each main test both with and without the first trajectory.

## Ethics and dual use

The audit checks describe what evidence would reveal coordination, so they also describe what coordination would
have to avoid to go unnoticed. I judge the uplift small: hidden channels and coordination at a ceiling are already
known gaps, and the paper names them as limitations. The planted protocol is an explicit instruction to relay and
follow advice, with no capability beyond what the prompt states. All runs used public API models in a sandboxed
game; no deployed systems or human participants were involved.

## LLM use

I used Claude (Anthropic) to build and test the notebooks and the scripts in `tools/`, to analyse run reports and to
draft text. I directed the experiments and checked every number against the run reports and every quote against the
transcripts.

## License

MIT for the code in this repository. The harness is MIT-licensed by its authors and is installed from its own
repository at the pinned commit, not vendored here.
