# report.md — `hybrid-v2-planner-premerge-review`

**Task:** `HYBRID_V2_PLANNER_PREMERGE_CORRECTNESS_REVIEW` (Owner, 2026-10-27).

**Marks:** `AUTHORED_DEVELOPMENT_NOT_HOLDOUT` · `INDEPENDENT_CODE_REVIEW` · `INDEPENDENT_HOLDOUT_NOT_EXECUTED` ·
`LIVE_NL_E2E_NOT_MEASURED` · `BROWSER_EVIDENCE_NOT_MEASURED`.

**Where:** branch `research/hybrid-v2-planner-generalization`, worktree `.superpowers/worktrees/planner-generalization`.
No merge, no push. 0 provider calls. `DEFAULT_MODE = LLM_ONLY`. Hybrid stays opt-in. Adapter `/4` untouched.

## 1. Baseline and inherited evidence

- **Reviewed baseline:** doc commit `81b545a2`; candidate `ca0bb5f2`; product `de7b2813`. The baseline descends from
  `386d2149`. The product tree is identical across `de7b2813..81b545a2`. The worktree was clean, and no foreign process
  was using it.
- **Inherited Full T3 receipt** (`hybrid-v2-planner-generalization/full-t3/receipt.json`): **VERIFIED**.
  - The `stdout.log` / `stderr.log` SHA-256 values match the receipt (`28be73dd…`, `aa9b7207…`).
  - Summary: 12275 backend / 1417 frontend, `FULL_PRODUCT_GATE_PASS`.
  - The freeze at `ca0bb5f2` names product `de7b2813`, 118 files, `316f66cc…`, clean tree.
- **Inherited independent review:** none existed (`INDEPENDENT_REVIEW_NOT_EXECUTED`). This run performs it (`review.md`).

## 2. Kind-only Source Gate binding — reproduction (RED)

**Harness:** `tools/adversarial.py`. It has 124 cases. Each case changes one phrase of an already-served fixture, and its
expectation was written from geometry before any run.

Families covered:
- Right and oblique triangular prisms, the 6 × 8 × 12 box and the 4 × 4 × 4 cube.
- Triangular pyramid S.ABC and square pyramid S.ABCD.
- The area clause, the construction clause, both clauses with facts in reversed order, a renamed fixture, the volume
  question and two prisms in one problem.
- Wordings: "chóp", "hình chóp", "lăng trụ", "lăng trụ đứng", "hình hộp", "hình hộp chữ nhật", "hình lập phương",
  "khối …", "tứ diện"; with a correct symbol, a wrong symbol, or no symbol.

**On the frozen candidate `ca0bb5f2`** (run in a clean detached checkout; file `results/red-before.json`):
- 92/124 cases agree with the expectation.
- **32 are FAIL_OPEN (served when they should refuse). There are 0 false refusals.**

| Fail-open class | Examples | Rows |
|---|---|---|
| Kind-only specific class contradicting the solid | "hình lập phương" / "hình hộp (chữ nhật)" / "khối lập phương" for a triangular prism; "hình lập phương" for the 6 × 8 × 12 box; "tứ diện" for S.ABCD; "lăng trụ đứng" / "hình hộp" for an oblique prism; same on the volume question | 26 |
| Correct symbol + contradicting kind word | "hình lập phương ABC.A'B'C'", "hình chóp ABC.A'B'C'", "hình lập phương ABCD.A'B'C'D'" (box) | 6 |

**Cause:**
- `_khoi_khop` (volume and other ask phrases) and `_cum_goi_khoi` (section reference on a shared plane) only separated
  pyramid-like from prism-like.
- With a symbol present, the kind word was ignored altogether. That second behaviour is a pinned earlier decision.

## 3. Fix (registry `/16`, product `37e84352`)

- **One Source Gate helper:** `registry._loai_cum_dung(cum, solid, calls)`. It is used only on the **no-symbol** branches
  of `_khoi_khop` and `_cum_goi_khoi`.
- **Generic class words** ("chóp", "lăng trụ") keep the `/15` test.
- **Specific class words** are accepted only when the gate's validated calls establish them:

  | Word | Accepted when |
  |---|---|
  | "tứ diện" | pyramid on a triangle |
  | "tam/tứ/ngũ/lục giác" | base vertex count matches |
  | "đứng" | prism with `right` set |
  | "xiên" | prism with `right` not set |
  | "hộp" | prism on a 4-gon with a rectangle/square base call, or the source defines it as a box |
  | "chữ nhật" | right prism with a rectangle/square base |
  | "lập phương", "tứ diện đều" | the solid's own validated definition clause says so (the gate reads no lengths); "tứ diện đều" also needs a `regular_pyramid` call |
  | "đều" | regular base, plus a regular pyramid or a right prism |

- **Calls context:** the calls of one `kiem_nguon` run are held in `_GOI_NGUON`, which is reset with a token afterwards.
  Outside the gate, a specific class cannot be verified and is refused.
- **What did not change:**
  - Quote verification, question/premise roles, and the planner (`/16`).
  - Engine `/14`, the bridge, Adapter `/4`, schema/IR and provider surfaces.
  - `CACHE_VERSION 130`: no bump (`candidate_divergence.json`).
  - Route identity moves through `IDENTITY_DELTAS` (registry `/15 → /16`).
- **Acceptance only narrows.** Every new path can only add a refusal after the `/15` test.

## 4. Before / after

| Measure | `ca0bb5f2` (RED) | `99faf026` (GREEN) |
|---|---|---|
| Adversarial cases agreeing with expectation | 92/124 | **118/124** |
| FAIL_OPEN | 32 | **6** (all from the symbol-outranks-kind policy, open for the Owner) |
| False refusal | 0 | **0** |
| Changed outcomes | — | exactly the 26 kind-only FAIL_OPEN rows, now `SOURCE_OBJECT_MISMATCH` |
| Development positives served / exact oracle agreement | 10/10 · 10/10 (inherited) | **10/10 · 10/10** (`results/development-regression-registry16.json`) |
| Development negatives refused with the registered code | 8/8 (inherited) | **8/8** |
| Wrong-served on the registered corpus + adversarial set | 32 (adversarial) | 6 (adversarial, policy) · 0 (corpus) |

Section and area goals on one derived plane are covered by every prism row: both clauses, each clause alone, and
reversed facts.

The pyramid regressions all pass:
- the existing perpendicular-section test;
- the `S.ABC` / `S.ABCD` kind rows;
- `test_pyramid_shared_plane_area_question_must_name_the_cut_solid`.

## 5. Test tiers and candidate

| Tier | Result |
|---|---|
| T0 `impact.mjs --base 81b545a2` | `IMPACT_GATE_PASS` (12344 passed, 18 xfailed) |
| T1 `tests/geometry` + `tests/semantic_program` | 11133 passed, 18 xfailed |
| T2 `vitest` | 83 files, 1417 passed |
| Freeze | `dd5b1f55`: product `37e84352`, 118 files, `1377e65411c8375c…`, clean tree |
| Candidate (freeze + divergence) | `99faf026bdcbcaa2f32e07a9f1687416a820dffd` |
| **Full T3** (clean detached checkout of `99faf026`) | **`FULL_PRODUCT_GATE_PASS`**: 12344 backend (1 skipped, 18 xfailed), 1417 frontend, build PASS, demo 5/5, crash surface 6/6; tree unchanged before/after; **post-T3 freeze MATCH** (`full-t3/receipt.json`) |

The xfail count went from 15 to 18. The 3 new xfails are the `xfail(strict=True)` pins of the symbol policy.

An earlier T0 run on `0a5ec06f`, before the freeze, failed only on 12 candidate-identity tests (expected before a
re-freeze). It was superseded by the run above and is not claimed.

## 6. Independent review

See `review.md`:
- **BLOCKER:** 0.
- **I-1 (open, Owner decision):** a correct symbol outranks a contradicting kind word.
- **I-2:** fixed.
- **MINOR 1 and 3:** fixed. **MINOR 2, 4, 5 and 6:** documented.
- The remediation delta `0a5ec06f..37e84352` received **INDEPENDENT_REVIEW_PASS**.

## 7. Remaining limitations

- **Symbol-outranks-kind (I-1).** Six adversarial rows are still served. It needs an Owner decision: reversing it changes
  `test_solid_symbol_outranks_the_solid_word` (run `hybrid-semantic-hardening`).
- **Narrow kind vocabulary.** "lăng trụ xiên" / "ngũ giác" are not in the section-phrase vocabulary (conservative false
  refusal). "hộp" is narrower than the geometric parallelepiped. "lập phương" is only accepted when the source itself
  defines the solid as a cube (no length reading).
- **Scope of the evidence.** The kind check covers only the phrases that `_khoi_khop` / `_cum_goi_khoi` bind. This is not
  a proof that the Source Gate is correct for all Vietnamese.
- **Development data only.** The data is authored development data (`AUTHORED_DEVELOPMENT_NOT_HOLDOUT`). The 10/10 rate is
  not a success rate on the high-school (THPT) curriculum.
- **`ADAPTER_INTEGRATION_GAP` unchanged.** `/4` refuses plane-only derived sections with `PREVIEW_RESULT_INVALID`. This is
  pinned, and it is not an E2E Hybrid PASS.
- **Not measured:** no independent holdout, no live NL E2E, no browser evidence.
- **Excluded metric.** `evaluate.py::dependency_depth` (predecessor tool) is not used as a metric.

## 8. Status

`READY_FOR_OWNER_GO_MAIN_REVIEW`. The handoff is `handoff.md`.
