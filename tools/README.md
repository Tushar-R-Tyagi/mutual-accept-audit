# How the notebooks were derived

Every game notebook starts from the replication notebook in the pre-sprint repository. Each script below takes a
notebook and writes a new one, changing only the cells it names, so the difference between any two arms can be read
from the script that separates them.

| Script | Input → output |
|---|---|
| `to_silent.py` | no-verdict-review screen → no reward, no review screen |
| `to_split.py` | → reward-instruction-only screen, and the feedback-only (symmetric) arm |
| `to_swap.py` | → fresh-Bob screen (Bob's memory wiped before episode 6) |
| `to_direct.py` | any game notebook → direct mode (no SMOKE gate, no estimate gates; the hard spend cap stays) |
| `to_asym.py` | feedback-only arm → asymmetric feedback, `chat` or `nochat` |
| `to_plant.py` | asymmetric arm → positive control, `chat` or `nochat` |
| `fix_proposal.py` | report cell: the first-ACCEPT-proposal heuristic fix (paper, Section 2) |
| `no_estimates.py` | removes printed cost estimates; the hard spend cap and the spend ledger stay |

The five main notebooks were then set to `MODE = "BASELINE"` and `N_TRAJ = 5`, the settings of the reported runs.
