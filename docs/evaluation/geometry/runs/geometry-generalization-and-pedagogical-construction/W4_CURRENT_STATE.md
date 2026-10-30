# W4 current state (living checkpoint)

Owner Master GO `ALGOSIM_W4_END_TO_END_GEOMETRY_AND_PEDAGOGICAL_SIMULATION` (2026-10-30). One epic; internal checkpoints only.

| field | value |
|---|---|
| branch / worktree | `research/w4-geometry-pedagogy` · `.superpowers/worktrees/w4-geometry-pedagogy` (node_modules junction to root) |
| base | `main` = `origin/main` = `e5dc3d28` (verified live 2026-10-30) |
| baseline product / measured | `dd17fbfb` · 118 files `c4fb8613…` · cache 130 · LLM_ONLY · live 0 |
| phase | F slice 1 GREEN at `01b74e39` (product `registry.py` +6 regex lines); next: Phases C–E (construction steps, pedagogy, Scene3D) |

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

## Remaining Wave 3 false refusals (5)
W3-B01 conditional reading of "Thiết lập mặt phẳng"; W3-B34/35/36 oblique prism ("hình chiếu … của đỉnh B' lên (BCD) là C",
"khối lăng trụ tam giác"); W3-A06 radical bound (genuine limit). Not tuned on Wave 3 text.

## Next action
Phase A audit result → Phases C–E: verify the step/scene/explanation pipeline for newly served hybrid outputs; improve
step navigation and explanation traceability reusing existing abstractions.
