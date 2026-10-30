# W4 current state (living checkpoint)

Owner Master GO `ALGOSIM_W4_END_TO_END_GEOMETRY_AND_PEDAGOGICAL_SIMULATION` (2026-10-30). One epic; internal checkpoints only.

| field | value |
|---|---|
| branch / worktree | `research/w4-geometry-pedagogy` · `.superpowers/worktrees/w4-geometry-pedagogy` (node_modules junction to root) |
| base | `main` = `origin/main` = `e5dc3d28` (verified live 2026-10-30) |
| baseline product / measured | `dd17fbfb` · 118 files `c4fb8613…` · cache 130 · LLM_ONLY · live 0 |
| phase | pre-freeze independent review running (HEAD after `0e555bad`); then docs write-back → freeze → T0–T2 → Full T3 → final review → integration |

## Phase B — first blocking layer of the 22 Wave 3 false refusals (receipt: `capability-matrix.md`)

All 22 stop in the Source Gate (none in Planner / exact geometry / Adapter / frontend):

| cluster | n | first blocking site | root cause |
|---|---|---|---|
| two-line slice solid/premise sentence | 15 | `registry._kiem_nguon_dong` (closed subset for MAT_HAI_DUONG) | SG-3 clause grammar `_phan_tich_cau` cannot parse common connectors ("thỏa mãn", "biết", "với (mặt) đáy", "Trong không gian,"), lexical variants ("vuông ở", "tam giác đáy X vuông tại", "số đo/chiều cao XY ="), and the slice's atomic solid forms lack "Xét", "tam giác/tứ giác", "khối", "lập phương" |
| cube "đáy … là hình vuông (có) cạnh (bằng) N" | 5 | `registry._kiem_nguon` UNGROUNDED_VALUE | same SG-3 parse failure ("… biết mặt đáy …" without comma) leaves the side value unbound |
| conditional clause (W3-B01) | 1 | `vai_tro_ok` CONDITIONAL_CLAUSE | "Thiết lập mặt phẳng (P) …" read as conditional — to examine |
| radical overflow (W3-A06) | 1 | exact kernel RadicalDomainError | radical bound 1e12 — genuine limit, keep refusal |

## Completed
- `0bcfed14` RED preregistration (70-case independent corpus; variants 6/42 at baseline).
- `01b74e39` GREEN: closed SG-3 grammar reads textbook connectors. Dev 42/42 · 18/18 · 10/10; Wave 3 **67/72** served-correct
  (+17), 72/72 negatives, 62/72 reasons, 0 wrong-served; locked 96/96; 203 probes unchanged; full backend 15768 passed, only
  11 pending-freeze + 1 dirty-tree check failing (receipts `green1.json`, `regression-green1.json`).

- `039fa606` pedagogy: certified "Vì sao" for section-edge steps (shared scene builder), keyboard ←/→/Home/End, CACHE 130→131.
- `8fe9f9a3` rubric + real-browser UI evidence + regenerated offline samples; proxies 100/108 edge steps justified.
- `0e555bad` regression after pedagogy: Wave 3 67/72, 72/72, 62/72, 0 wrong-served, 0 leaks; locked 96/96; probes unchanged.
- `capability-matrix.md`: the 22 cases, first blocking layer, capability, location, risk, W4 result.

## Remaining Wave 3 false refusals (5)
W3-B01 conditional reading of "Thiết lập mặt phẳng"; W3-B34/35/36 oblique prism ("hình chiếu … của đỉnh B' lên (BCD) là C",
"khối lăng trụ tam giác"); W3-A06 radical bound (genuine limit). Not tuned on Wave 3 text.

## Next action
Wait for the pre-freeze adversarial review (scratch `w4-review/`). On READY: write back EVIDENCE_INDEX / CURRENT_STATE /
AI_CONTEXT_BUNDLE / STATUS_LEDGER, commit, freeze candidate (separate commit, new divergence layer), T0/T1/T2, Full T3 in a
fresh detached worktree, final independent review, conditional integration under the scoped W4 publication decision.
