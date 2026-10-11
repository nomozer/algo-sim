# S0: clause role inside the quote, and asks that are not questions

- Approved by the user on 2026-10-11, as S0 of [`hybrid-simulation-capability-audit`](../hybrid-simulation-capability-audit/report.md).
- Branch `research/hybrid-simulation-capability-audit`, LOCAL. LIVE GEMINI CALLS = 0. Default `LLM_ONLY`.

## Defects fixed

| Issue | Before | After |
|---|---|---|
| `ISSUE-ARCH-GATE-CLAUSE-ROLE-INSIDE-QUOTE` (CRITICAL) | A premise quote carrying its own "Nếu … thì" or "Chứng minh" was used as a given. Example: SC = √17 served where the figure is undetermined; same in route A. The consequent of "Nếu … thì X", quoted alone, was also accepted | Roles are read at every anchor of the call inside the quote (predicate cue, the call's labels, construction phrase), and any earlier "nếu" in the sentence makes the clause `CONDITIONAL`. Result: `CONDITIONAL_CLAUSE` / `GOAL_CLAUSE_NOT_PREMISE` |
| `ISSUE-ARCH-ASK-GATE-NO-QUESTION-CHECK` | `ask_*` answered "Hãy chỉ ra rằng khoảng cách … bằng 3", "Chứng minh rằng thể tích … bằng 4", "Góc … có cos² bằng 9/17" | The sentence must ask (tính / tìm / xác định / hỏi / bao nhiêu / ?), otherwise `NOT_ASKED_IN_SOURCE` |

**Residual limit.** A question whose sentence asks something else while asserting a value of the asked quantity, e.g. "Khi khoảng cách … bằng 4 thì SC bằng bao nhiêu?" typed as `ask_distance`, is still answered by the generic `ask_*` path. A generic asserted-value check would also refuse "Tính thể tích … biết SA = 3". Only the point–line path (slice 1 review) has the phrase-bound check.

## Evidence

| Check | Result |
|---|---|
| RED at `d5a963e4` | 11 failed, 5 passed ([log](red-at-d5a963e4.txt)) |
| `test_source_gate_clause_role.py` | 16 passed, 3 source mutants killed. The mutants are patched where the engine holds its reference |
| Audit probes | the 4 strict xfails became regression tests |
| Hybrid / route-A cluster (13 files) | 704 passed, 5 xfailed (B27, B28 × 2, centre-label crash) — no fixture, holdout or frozen A/B runner changed |
| Benchmark | rows byte-identical (19/9/0/2) |
| Candidate | `fd71f0b4…` (product `8129f4ed`, refreeze `f8b50b46`), declared in [`candidate_divergence.json`](candidate_divergence.json) |
| Surfaces | provider surfaces, Registry, IR and engine unchanged |
