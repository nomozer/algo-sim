# Hybrid Wave 2C — composite geometry (`composite-geometry`)

- **Branch:** `research/hybrid-wave2c-composite-geometry` from `main` = `origin/main` = `78bd68764a69c513086b844ab3ed5e29ae18ce04`
- **Authorization:** `GO_HYBRID_WAVE2C_LOCAL_RESEARCH` (local only; no GO MAIN)
- **Product:** `739a833a` (Codex, slices) → `deeb1748` (review blocker) → `050bb353` (review round 1 findings)
- **Candidate:** freeze `962b97237246b65bb2d4abc6ebed9bc5b971f5fd`, measured `3e6c403cff0e2c4ae96c4a541f97ecbe92f1efd821e08d5fdb1572d4ee823ab9` (112 files)
- **Full T3:** `FULL_PRODUCT_GATE_PASS` at `0acfa9e96fc41d8ca6ba79983f49391553349a3a` ([`authoritative-t3.json`](verification/authoritative-t3.json))
- **Review:** `INDEPENDENT_REVIEW_PASS` round 2 ([`independent-review.md`](verification/independent-review.md))
- **Contract:** [`COMPOSITE_GEOMETRY_CONTRACT.md`](../../../../architecture/COMPOSITE_GEOMETRY_CONTRACT.md); plan [`plan.md`](plan.md)

## 1. Continuity

The work was started by Codex and interrupted by its usage limit after the product commit `739a833a`, the first freeze
`503c9d6e` and a reviewer BLOCKER. The recovered state was: those two commits, one uncommitted RED test for the blocker,
untracked SGH known-regression results and the frozen development measurement (both on `503c9d6e`), and a copy of the
SGH runner in `.superpowers/tmp/` (preserved). Nothing was restarted; the slices, contract and corpus are Codex's.

## 2. Slices (two, as authorized)

1. **Derived sub-pyramids / parallel sections.** A pyramid may use a base of already-constructed points (midpoints,
   rational division points, centroids, intersections, projections, translations) in the single root Gram chart.
   The root is the only solid none of whose vertices is a construction output, independently of labels and fact order;
   an independent second root is `UNSUPPORTED_MULTIPLE_BASES`. Bases must be coplanar and non-degenerate, faces simple,
   apex off the base plane.
2. **Shared-face sub-pyramids.** Several pyramids share global point IDs with solid-owned face tables; the closed
   sentence `Hai hình chóp X và Y có mặt chung (…)` is checked against both face tables (`_kiem_mat_chung`).

Every asked composite volume must equal an independent certificate (Gram base area² × altitude² / 9) or the route
refuses `ENGINE_SELF_CHECK_FAILED`. Residual-solid / volume-ratio quantities, unnamed section vertices, independent
charts and qualified duplicate labels stay unsupported or `BLOCKED_BY_CONTRACT` (they need TypedFact / Adapter changes).

## 3. Regular derived pyramid blocker

- **Root cause:** `_Dung._dung_khong` accepted `regular_pyramid` with equal lateral edges only. That places the foot at
  the circumcentre, and a non-square rectangle is cyclic. Derived solids skip the root's apex-over-regular-centre
  construction, so nothing else checked the base. Layer: engine validation of a regular-solid premise.
- **Exposure:** direct `run_function_route` calls only. The planner route also emits `regular_polygon` for the derived
  base, which was already checked (RED log: planner-route tests pass on the old engine).
- **Fix (`deeb1748`):** regular pyramid ⇔ exactly regular base (`_canh_da_giac_deu`: equal sides, equal Gram distance to
  the vertex centroid, non-zero) ∧ equal lateral edges ∧ apex off the plane. One predicate for both routes; no rectangle is
  upgraded; generic pyramids on the same rectangle are still served.
- **Round 1 follow-ups (`050bb353`):** `_mat_ben_vuong_goc_day` binds to `self.root` (label-dependent refusal);
  `_hai_duong_cat_nhau` uses root-base heights only; `_canh_da_giac_deu` also requires planarity (a regular
  tetrahedron's skew SABC is no longer accepted as a square).
- **RED/GREEN:** [`regular-blocker-red`](verification/regular-blocker-red.stdout.log) (1 failed: rectangle child served) →
  [`regular-blocker-green`](verification/regular-blocker-green.stdout.log) 39 passed;
  [`review2-red`](verification/review2-red.stdout.log) (2 failed) → [`review2-green`](verification/review2-green.stdout.log) 42 passed.
- **Adversarial coverage:** rectangle / spoofed `regular_polygon` / conflicting lengths / oblique apex with an
  equilateral base / planner route with the source gate bypassed / relabelled root / skew square, plus Codex's missing
  point, degenerate, non-coplanar, crossed, cyclic, independent-root and source-spoofing tests.

## 4. Results (clean detached worktree at `9285075a`, same measured tree)

| Suite | Class | Result |
|---|---|---|
| Development corpus (30 cases) | `DEVELOPMENT_EVALUATION_NOT_BLIND` | 16/16 exact served (baseline main 0/16), 26/26 goals, 14/14 correct refusals, **0 false serves**, 16/16 valid scenes, ≤ 13 calls |
| SGH-01..18 (manifest `268c5d66…`, lock `fe335684…`) | `KNOWN_REGRESSION_NOT_BLIND` | 10/10 positive, 16/16 goals exact, 14/16 strict tuple, 5/5 negative, 1/2 ambiguous — identical to Follow-up A+B |
| SG-1..SG-6 (30) | locked regression | 18/18 served, 12/12 refused, 0 rows changed |
| BH2A-01..18 + variant ABCD | `KNOWN_REGRESSION_NOT_BLIND` | 11/12 + sentinel + variant served, 5/5 refused, 0 rows changed |
| NLU GOLD (60) | declared deltas | 0 changed |
| 174 historical rows, Adapter /2 41 fixtures, Wave 1/2A/2B, Route A, Scene3D/IR | Full T3 | inside 11,391 backend passes |

Raw output: [`results/final-candidate-2/`](results/final-candidate-2/). Earlier receipts (`results/final-candidate/`,
`candidate-frozen.json`, `sgh-candidate.json`) measure superseded candidates and are kept unchanged.

## 5. Full T3

Attempt 1 at `0acfa9e9` failed only in vitest (70 files failed to load) because the T3 harness's `node_modules` junction
used a lowercase drive letter; backend passed 11,391. Attempt 2 on the same commit with the corrected junction:
`FULL_PRODUCT_GATE_PASS` — pytest 11,391 passed / 1 skipped / 2 deselected / 9 xfailed, vitest 70 files / 1,146,
build PASS, demo 5/5, crash surface 6/6, freeze MATCH afterwards. Both attempts' raw logs are in `verification/t3/`.
An earlier T3 at `750c8c49` was cancelled before completion (superseded by review findings; no result claimed).

## 6. Governance

`DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `CACHE_VERSION = 127` (NO_BUMP), Hybrid product NO-GO,
`ALLOW_LIVE_AI = 0`, 0 live calls. Registry `/10`, Engine `/8` (Route D preview identity only), Planner `/10`,
Adapter `/2`; TypedFact and provider surfaces unchanged.

## 7. Open for Wave 3

Residual-solid and volume-ratio goals, unnamed section vertices, independent multi-chart placement and qualified
duplicate labels need a TypedFact/Adapter contract (`BLOCKED_BY_CONTRACT`). Carried-over minor review notes are listed in
`independent-review.md` (code attribution of consumed forged premises, single shared-face wording, certificates only
for composite plans). No blind evaluation of Wave 2C exists; the development corpus is not a holdout.
