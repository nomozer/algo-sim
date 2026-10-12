# Independent review and Scene3D check of S0 + the section slice

- Reviews [`hybrid-gate-clause-role-fix`](../hybrid-gate-clause-role-fix/report.md) (S0) and [`hybrid-section-slice`](../hybrid-section-slice/report.md).
- Branch `research/hybrid-simulation-capability-audit`, LOCAL, 2026-10-12. Not merged, not pushed.
- LIVE GEMINI CALLS = 0; no paid API. Default `LLM_ONLY`, `CACHE_VERSION` 125, both unchanged.
- **Result:** every Critical and Important finding is closed. The section geometry matches an independent exact oracle. Six real Hybrid scenes render in the Scene3D harness, with one exception: the intersection line `(SAB) ∩ (SCD)` draws no pixels.
- **Residual risk:** pre-existing false serves of the source gate remain (§5). They are recorded, not fixed.

## 1. Method

- **Reviewer:** an independent general-purpose subagent (superpowers requesting-code-review pattern). It reads the code and runs probes only, and writes nothing to the repository.
- **Rounds:** four passes in all:
  1. Full review at `7b72046f`.
  2. Re-verification at `5136127a`.
  3. Re-verification at `e2af448e`.
  4. A capped final pass at `b2e980a6`, asked for false serves only.
- **Fix discipline for each fix round:**
  - A failing test is written first; RED logs are in `red/`.
  - Then the narrowest fix.
  - Then a source mutant per new rule.
  - Then the Hybrid cluster and the 30-case benchmark.
- **Narrowing, not deny-lists:** the fixes narrow what is accepted. A role or ask is read where the object stands in the clause; no list of forbidden sentences is added.

## 2. Findings and RED → GREEN

| ID | Severity | Finding | Fix (commit) |
|---|---|---|---|
| C1 | Critical | An `ask_*` was answered when the sentence did not ask for that object. The required reproduction "Khi khoảng cách từ S đến BD bằng 4 thì SC bằng bao nhiêu?" typed as a distance ask was served | The ask must be for THAT object, read at its anchors (quantity noun or a label set equal to an operand). Accepted: a question verb before it, or "bao nhiêu / mấy / ?" after it; no value assigned to it; not in a proof or conditional clause (`5136127a`). The reproduction is now `CONDITIONAL_CLAUSE` |
| C2 | Critical | Conditional and question clauses other than "nếu" became givens (khi, giả sử, trong trường hợp, "… thì", "Phải chăng …?") | One clause analyser (`_vai_tro_tai`, `_duoc_hoi`) for premises, asks and the auxiliary path; `QUESTION_CLAUSE_NOT_PREMISE` (`5136127a`) |
| I1 | Important | A section / intersection plane could bind to another plane of the sentence | The cutting plane must be the one the quote names after "cắt bởi", "giao tuyến của (P) và (Q)" and similar (`5136127a`). Later narrowed to "the plane is the clause's subject" (`b2e980a6`, N1) |
| I2 | Important | "area + solid + ≥ 3 points" was routed to the section area and changed old polygon-area behaviour | The section area is asked only through "diện tích (của) thiết diện". Both phrases in one fact give `AMBIGUOUS_FACT` (`5136127a`, `e2af448e`) |
| I3 | Important | The section solid was not grounded against the quote | The quoted solid symbol must be the call's, or the problem has exactly one solid. "đáy" means only the solid's base (`5136127a`) |
| M1 | Minor | Degenerate sections lost the kernel's specific code | `PLANE_TOUCHES_VERTEX / _EDGE / PLANE_DOES_NOT_CUT` kept (`5136127a`) |
| M2 | Minor | The same plane named by different point sets gave two section objects | Sections keyed by the normalised plane equation (`5136127a`) |
| M3 | Minor | The merged construct call was missing from the trace | Trace lists every call (`5136127a`) |
| M4 | Minor | A plane equal to a face or the base is served as a "section" (the face itself) | **Not fixed**: whether this is a section or a refusal is a product-contract decision (§5) |
| re-verification 1 | false refusals | Common wordings refused: "khi cắt bởi", "các mặt phẳng", "mp(SAB)", "tạo bởi", "do (P) cắt", "(P) cắt hình chóp … theo thiết diện"; "Chứng minh X và tính Y"; "làm tròn đến 2 chữ số" | Fixed in `e2af448e` |
| N1 | false serve | Planes related to (SAB) ("tạo với", "đối xứng với", "song song với (SAB) cắt") bound to (SAB) | "với (P)" binds only right after "thiết diện của <solid>"; "(P) cắt …" only when (P) is the clause's subject (`b2e980a6`) |
| N2 | false serve | The question verb governed another object ("Tính SC theo khoảng cách …", "tỉ số giữa …", "sao cho … nhỏ nhất") | Object blockers between the verb and the object (`b2e980a6`) |
| yes/no | false serve | "Thể tích … có vượt quá 5 không?" answered with the volume; the earlier minor fix only covered assignment verbs | A yes/no marker after the object without "bao nhiêu / mấy" means a relation is asked, not a value (`b3e946e9`) |

**RED logs** (tests written first, run against the code before each fix):

| Round | Log | RED |
|---|---|---|
| 1 gate | [`red/round1-gate-red-before-5136127a.txt`](red/round1-gate-red-before-5136127a.txt) | 22 failed, 27 passed |
| 1 section | [`red/round1-section-red-before-5136127a.txt`](red/round1-section-red-before-5136127a.txt) | 8 failed, 21 passed |
| 2 | [`red/round2-red-before-e2af448e.txt`](red/round2-red-before-e2af448e.txt) | 16 failed, 83 passed |
| 3 | [`red/round3-red-before-b2e980a6.txt`](red/round3-red-before-b2e980a6.txt) | 9 failed, 99 passed |
| 4 | [`red/round4-red-before-b3e946e9.txt`](red/round4-red-before-b3e946e9.txt) | 2 failed, 6 passed |

**GREEN at `b3e946e9`:**
- Gate, section and decomposition suites: 181 passed.
- Hybrid cluster (20 files): 885 passed, 5 xfailed.
- Source mutants: 14 across the gate and section suites (8 in the gate suite), all killed.
- 30-case benchmark: `metrics.json` byte-identical to [`hybrid-goal-decomposition/after`](../hybrid-goal-decomposition/after/metrics.json) (19/9/0/2).
- Provider surfaces A/B: unchanged (`test_provider_surfaces_are_pinned`).
- Exported scenes: byte-identical after every fix round.

## 3. Independent oracle

- **Oracle:** [`oracle/section_oracle.py`](oracle/section_oracle.py), written by the reviewer. Its output is in [`section_oracle-output.txt`](oracle/section_oracle-output.txt).
- **Method:** exact `Fraction` arithmetic and stdlib only, no product import. It clips the plane against the solid's edges, orders the vertices around the centroid and computes the area as a cross-product sum. This is a different algorithm from the kernel.
- **Comparison:** the product served the same area² and the same edge topology (which edge each vertex lies on, edge parameter) in every row. The reviewer's `p8_topology` passed 7/7.

| Case | Oracle area² | Product |
|---|---|---|
| pyramid (MAB), M = mid SC | 117/16 (vertices A, B, mid SC, mid SD) | equal |
| pyramid (SAC) | 18 | equal |
| pyramid (mid SA, SB, SC) | 1 | equal |
| pyramid (C, mid SA, mid SB) | 225/16 | equal |
| pyramid (M, I, K), I/K outside the base | 125/144 | equal |
| pyramid (S, I, K) touches a vertex | degenerate | `PLANE_TOUCHES_VERTEX` |
| pyramid (S, C, I) touches an edge | degenerate | `PLANE_TOUCHES_EDGE` |
| pyramid face (SAB) / base (ABC) | 9 / 16 | served (M4) |
| collinear plane points | refuse | refused |
| cube (A'BD) | 12 | equal |
| cube hexagon through 3 edge midpoints | 27 | equal |
| regular tetrahedron, two cuts | 3/16, 1 | equal |
| (SAB) ∩ (SCD) | through S, parallel to AB | equal |
| (SAC) ∩ (SBD) | through S and O | equal |
| (MNP) ∥ (ABC) | parallel | `PARALLEL_PLANES` |

`EVALUATOR_INDEPENDENCE = PARTIAL`: the oracle author is a separate agent, but the case list comes from the same session.

## 4. Scene3D check (Playwright)

**What was run:**
- **Scenes:** six real Hybrid route outputs (typed facts → planner → gate → engine → IR → kernel → `scene3d`), exported by `backend/scripts/export_hybrid_section_scenes.py` into [`visual/scenes.json`](visual/scenes.json).
- **Renderer:** the product component `Scene3DWorkspace`, mounted by the harness `frontend/scripts/hybrid-section-visual.{html,tsx}`.
- **Checker:** `frontend/scripts/hybrid-section-visual-check.mjs`. Playwright chromium with SwiftShader WebGL, through a Vite dev server of this checkout.
- **Results:** [`visual/browser-check/`](visual/browser-check/browser-check.json); one PNG per case.

**What this is not:**
- It is not the product page. Hybrid is not wired into `/api/analyze`, the store or the UI, so there is no store, no API and no model in the loop.
- It is not a human visual acceptance.
- It is not product E2E.

| Case | Model vertices | Own pixels of the target | Built after its dependencies | Orbit / zoom / reset | Console errors |
|---|---|---|---|---|---|
| section (MAB) trapezoid | 4 | 80 102 | yes (step 6 of 11) | change, settle / ink ×1.60 / residual 0 | 0 |
| section (SAC) triangle | 3 | 7 024 | yes (5 of 9) | ok / ×1.42 / 0 | 0 |
| section (MNP) mid-square | 4 | 2 602 | yes (8 of 13) | ok / ×1.59 / 0 | 0 |
| cube (A'BD) | 3 | 114 031 | yes (3 of 7) | ok / ×1.59 / 0 | 0 |
| giao tuyến (SAB) ∩ (SCD) | — | **0** | yes (6 of 7) | ok / ×1.34 / 0 | 0 |
| auxiliary foot S → BD | — | (line pixels 288) | — | ok / ×1.87 / 0 | 0 |

- **Own pixels:** the frame with and without the target (`hide=<id>`) at the last step. 0 means the object draws nothing visible.
- **Section shape:** the screenshots show the amber section polygon of the expected shape, with the cutting plane translucent.
- **Model data:** the vertex count and positions come from the scene data and are checked against the oracle in §3. Pixels do not prove vertex positions.
- **Section vertices are unlabeled** in the scene.

**Defect found:** the intersection line `gt_f5` is in `__geo3d_rendered_object_ids` but contributes 0 pixels. That stays 0 with the planes hidden and the auxiliary layer shown.
- **Diagnostics through the harness `set=`:** a line at S with direction (−1,1,0) or (0,1,0) renders. Directions (1,0,0), (1,1,0) and (1,0,1) do not, and nothing renders at the interior point (½,½,½).
- **Control:** the auxiliary line `derived_H_line` renders 1 754 pixels.
- **Data is correct:** the oracle direction of (SAB) ∩ (SCD) is (−24,0,0), parallel to AB.
- **Root cause in the renderer:** UNKNOWN. It is recorded as `ISSUE-ARCH-SCENE3D-INTERSECTION-LINE-INVISIBLE` and is not fixed in this run. The LLM_ONLY renderer path is the same component, so the defect may also exist there; that has not been checked.

**Compared with the orbit P1 baseline** (`ISSUE-ARCH-ORBIT-P1-SECTION-SCENE-DOES-NOT-SETTLE`):
- All six Hybrid scenes settle within 10 s after orbit, zoom and reset; the P1 fixture does not.
- **Weaker check than gate v3:** this harness loads each scene in a fresh document and does not count GPU resources. It neither confirms nor rules out the P1 defect for these scenes, and P1 is not fixed.

**Harness stability:** the first page load timed out waiting for the canvas (90 s) in 2 of the last 4 runs, then passed on rerun. The cause is not measured; Vite cold transforms under SwiftShader are suspected.

## 5. Residual risk (recorded, not fixed)

Source: the capped final pass. The probe file [`residual/false_serve_probes.py`](residual/false_serve_probes.py) holds about 80 inputs; its output at `b3e946e9` is in [`false_serve_probes-output-at-b3e946e9.txt`](residual/false_serve_probes-output-at-b3e946e9.txt). A line marked `!!` was served. Not every served line is wrong: some are controls or correct readings.

| Group | On `main` before this branch? | Examples (served) |
|---|---|---|
| A. Non-premise clauses as givens: goal verbs other than "chứng minh" (chỉ ra, giải thích vì sao, tìm điều kiện để), questions without "không", reported claims, weak negation / modality / disjunction (không hề, chẳng, có thể, hoặc) | yes | "Hãy chỉ ra rằng SA vuông góc với (ABCD)." typed as a premise → SC = √17 |
| B. A length value from a non-equality | yes | "SA ≠ 4.", "SA ≥ 3.", "SA xấp xỉ 3.", "SA bằng 3 lần AB." typed as SA = number |
| C. Asked operands not bound to the quote; quantity modifiers ignored | yes | "Tính khoảng cách từ A đến (SBC)." typed as S → (ABCD); "Tính bình phương khoảng cách …"; "Tính độ dài hình chiếu của SC …" |
| D. Sections | **new surface** | one quote naming two sections binds the wrong one (a given area served as the answer); "diện tích hình chiếu của thiết diện" falls back to `ask_area` of triangle MAB; optimisation / change wordings ("lớn nhất khi M chạy", "khi SA tăng gấp đôi"); the solid word is not checked against the single solid |
| M4 | new surface | a face or base plane served as a section |

**Assessment:**
- C and D are the most likely to give a confident wrong answer.
- All five groups are reachable only through the Hybrid route, which `/api/analyze` does not call.
- The regex grammar of the gate cannot be complete for adversarial wording. Its long-term fix is operand binding of asks (C) plus a closed list of accepted ask shapes, not more blockers.
- Recorded as `ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES`.

Pre-existing false refusals that remain: "SC dài bao nhiêu?" (`PREDICATE_NOT_IN_QUOTE`) and "(SAB) và (SCD) cắt nhau theo giao tuyến nào?".

## 6. Candidate, surfaces, gates

- **Candidate:**
  - Product `b3e946e9`, tree `451b046c…`.
  - Refrozen in a clean detached worktree: `542e3894`. An intermediate refreeze for `b2e980a6`, `65126be0`, was superseded the same day.
  - Declared in [`candidate_divergence.json`](candidate_divergence.json), which corrects the `hybrid-section-slice` declaration.
- **Unchanged:** the locked A/B candidate `12da4768…`, historical evidence and frozen benchmarks.
- **Model surface:** provider surfaces A/B unchanged. `contract.py`, prompts, `grammar_card` and the capability table are untouched.
- **T3:** see `run.json`, in a clean detached worktree at the docs commit.

## 7. GO / NO-GO

- **Fast-forward of `main` to this branch: GO with declared residual risk.**
  - `main` is an ancestor, so it is a fast-forward.
  - Every review finding except M4 is closed with RED → GREEN.
  - The section geometry is exact against the oracle.
  - The Hybrid route stays unreachable from `/api/analyze`, and `LLM_ONLY` stays default.
  - The residual false serves (§5) and the invisible intersection line (§4) go to `main` as open issues, not as fixed. The user decides; this run does not merge or push.
- **Enabling Hybrid in the product, or a live pilot: NO-GO.** Groups C and D must be fixed first, and the intersection line must render.
