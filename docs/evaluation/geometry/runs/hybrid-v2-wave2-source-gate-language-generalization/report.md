# Source Gate language generalization

Status: **NOT_READY_ACCEPTANCE_GATE_FAILED**. W2-M1/M2/M3 are repaired within the Source Gate.
The locked development corpus still contains one correct positive refused at the explicitly excluded W2-M4 radical
ceiling. No READY or migration claim is supported. Full T3 completed with the same single failing acceptance test.

## Identity and scope

| Identity | Value |
|---|---|
| Baseline HEAD = main = last-fetched origin/main | d7a94d3cd4bbdea3df99e383bec78425fcc8bf1c |
| Baseline measured product | 84ccf653441d1bd54f352756b9a5e917ee02a9ea11a83ac60585dfc585f3f99f |
| Preregistration / RED commit | 6554d733203619dad9ea8c4c640fc80ee5782a34 |
| Product commit | c6f6b64bda6473c175a32a7875a9dd9831ae7c6d |
| T3 candidate | b9e3d0966e14acb1d44f2f9c7cd7a3bf49ac54a9 |
| Candidate freeze: 118 files | 8baf3205006d097efdd21087b9d52e85625fa1263e9125b418cf658ccac18d25 |
| Final branch HEAD | final documentation commit carrying this report; resolve research/hybrid-v2-wave2-source-gate-language-generalization; exact SHA emitted in the session handoff after commit to avoid self-reference |

Product files changed: only `backend/app/simulation/geometry_functions/registry.py`.
Registry /18 -> /19; Planner /17, Engine /14, Adapter /4, section certificate /1 unchanged.
Version pins and the exact IDENTITY_DELTAS pair were updated in supporting tests/tooling.
Product diff SHA-256: `51030a2772a8d5693ff1d6318805b2c2c8f4d81ea410ece3762a473036fb0857`.
This matches the recorded precommit diff in both GREEN and the 96-case replay.

No kernel, Radical, planner construction, engine arithmetic, Adapter, Scene3D, OCR, provider schema/prompt or default
routing change. CACHE_VERSION130 / LLM_ONLY / Hybrid opt-in remain unchanged.
Cache lock MATCH and41/41 stored preview fixtures verify with only declared identity restoration
(`verification/cache-and-fixtures.json`). No live provider call, merge, push, worktree deletion or cleanup.

## Repair

W2-M1 extends the existing exact ratio reader to inverted edge-point clauses; point, source edge,
both equation operands, endpoint direction and complementary ratio remain bound by one Fraction solver.
The complete-premise reader is reused for construction/number ownership and MAT_HAI_DUONG coverage.

W2-M2 accepts the target noun “đỉnh” only if the image is a vertex of the unique solid owning the source point
and target plane/line. Primed targets are tested for both “là” and “trùng với”. Derived midpoints cannot become vertices.

W2-M3 reads whole ratio premises with that same reader and admits generic/oblique prism words through the existing
kind/identity checks. A standalone named right-triangle premise delegates operand checks to the existing construction
binder. Unknown tails, omitted premises, wrong solid kinds and contradictory relationships remain refused.
No new geometry authority, inferred input fact, fallback or exception-to-SERVED path was added.

## Locked development evidence

The new mathematical configurations and expected outcomes preceded product execution. The 24 positive and 37
initially labeled negative rows are independent of Wave2 cases/oracle; six families, four syntax/order variants each.
Independent review recomputed all 24 positive boundaries and squared areas from exact coordinate intersections and
cross-product area, with 24/24 agreement. Scoring requires the actual route + Adapter4 + envelope to serve.

| Original locked subset | RED baseline | GREEN raw |
|---|---:|---:|
| Original positives served correct | 6/24 | 23/24 |
| Original positives false refusal | 18/24 | 1/24 |
| Initially labeled negatives refused | 37/37 | 36/37 |
| Raw scorer WRONG_SERVED labels | 0 | 1 |

The raw WRONG_SERVED row, `NEG-unproven-two-line-premise`, appends AC perpendicular AB to a source already giving
angle BAC=90. Independent review established it is a valid redundant assertion, and verified the actual served
section (area squared11664, exact boundary). The immutable raw tally stays unchanged; the additive
`results/development-adjudication.json` records its interpretation separately.

After adjudication: all 36 genuinely adversarial rows refuse in registered codes, the mislabeled valid row is
SERVED_CORRECT, 0 genuine wrong-served, and exact oracle agreement is24/24 among served rows including that row.
The original positive denominator stays24, with 23 served and one false refusal. The literal locked acceptance remains
NOT_MET. No supplemental case replaces that failed row.

The residual `DEV-1-3` is a correct section of T.EFG (EF13, EG19, TE11, TJ/TE=5/11).
Independent area squared38130625/58564 is unchanged. Engine refuses intermediate radicand2233081922500 >10^12.
This is W2-M4; MAX_RADICAND is unchanged and no out-of-scope repair was attempted.

Seven additive controls pass: two primed-target positives with exact oracle agreement and five adversarial refusals
(including the actually false AC perpendicular BC premise). Eleven direct ratio direction/value/operand/tail controls
also pass. Earlier pre-product gold operand corrections are retained as separate input/RED artifacts and explained
in preregistration.md; neither original mathematical outcomes nor oracles were changed.

## Wave2 post-feedback regression

Classification: **POST_FEEDBACK_DEVELOPMENT_REGRESSION**. This is not an independent holdout PASS.

| Measure | Historical adjudicated baseline | Current actual product |
|---|---:|---:|
| Positive SERVED_CORRECT | 5/48 | 45/48 |
| Positive FALSE_REFUSAL | 43/48 | 3/48 |
| Negatives REFUSED | 48/48 | 48/48 |
| Correct refusal-reason category | 33/48 | 36/48 |
| Refusal-reason mismatches | 15/48 | 12/48 |
| Genuine WRONG_SERVED | 0/96 | 0/96 |
| Served exact-oracle agreement | 5/5 | 45/45 |

All96 rows were independently re-executed on the frozen product and matched the stored replay row by row.

| Family | Positive served correct | Negatives refused |
|---|---:|---:|
| Triangular pyramid | 9/9 | 32/32 |
| Quadrilateral pyramid | 8/9 | 5/5 |
| Right triangular prism | 7/8 | 3/3 |
| Oblique triangular prism | 7/7 | 0/0 |
| Cuboid | 7/8 | 3/3 |
| Cube | 7/7 | 1/1 |
| Other negative configurations | 0/0 | 4/4 |

Zero denominators in this table mean no corpus member in that stratum, not a missing measurement.
Category B:36/36 positives correct. Category A:9/12; exactly three remaining excluded failures.

| Plane relation | Positive served correct | Negatives refused |
|---|---:|---:|
| Parallel plane | 12/12 | 28/28 |
| Parallel two lines | 12/12 | 2/2 |
| Perpendicular line | 12/12 | 8/8 |
| Stated intersections | 9/12 | 6/6 |
| Other | 0/0 | 4/4 |

First-refusal residuals: W2-A04 ENGINE_EXECUTION_FAILED / RADICAL_DOMAIN_OVERFLOW (W2-M4);
W2-A07 and W2-A10 PREVIEW_VALIDATION_FAILED at Adapter4 (W2-M5).
Reason-category mismatches: W2-N06,N23,N25,N29,N30,N34,N35,N36,N41,N42,N43,N44.
The replay JSON retains every first code/layer/category and family/relation stratum. The observed 40 recovered
positives confirm the registered hypothesis through product execution, not an in-memory diagnostic.

## Verification and independent review

T0 selected nonempty backend + code-index coverage. Source-scope/pins/publication checks pass; publication candidate
receipt: 43 scanned objects,3 commit messages,0 violations. Dry impact selection alone is not IMPACT_GATE_PASS.
T1/source/certificate targeted run:570 passed,1 failed (the preserved DEV-1-3 acceptance blocker).
I-1/two-line independent review run:218 passed. Supplemental + ratio controls:18 passed.
T2 legacy integrations:124 passed plusone temporary-directory setup error; only that errored test was retried after
creating the missing parent and passed. Setup failures/retries remain in separate logs.

Full T3 executed all five gates on clean detached b9e3d096.
**FULL_PRODUCT_GATE_FAIL**: backend 12,549 passed,1 failed,1 skipped,2 deselected,15 xfailed;
sole failed test `test_source_language_product_outcome[DEV-1-3]`.
Frontend 83 files / 1,417 tests pass; typecheck + production build pass; thesis demo replay passes;
all six crash-boundary checks pass. No gate was skipped.
Source tree was clean before and after; HEAD unchanged; post-T3 freeze MATCH (118 files,8baf3205…).
Receipt: `verification/full-t3/receipt.json`. Full log SHA-256:
`38358b1a3ce1185ffa60995c1ca216e797345b4e2e89e313e114e4f0f6499476`.
Receipt time:2026-10-28 07:58:22–08:08:13 Asia/Bangkok; duration587.9s for the five gates.
The failed backend test is retained. No new exclusion was added for the failed test; no gate was skipped or relabeled as PASS.

Independent review and machine checks: review-first-pass.md; results/independent-final-checks.json;
final review.md records the final receipts and unresolved acceptance MAJOR. No remaining source-binding
fail-open was established; the literal positive acceptance gate prevents READY.

## Preservation and limits

Original Wave2 lives at retained commit ecdc26b012c8ce80d53524a98dc75cdcb020079d.
All34 historical files, manifest identities, both scored-run histories, corpus/oracle and adjudication hashes were
verified without editing historical files. Four historical narrative discrepancies are corrected separately in
correction-layer.md and correction-addendum.md, with CORRECTED_BY links in the living evidence index.
Primary historical results remain5/48,43/48,48/48,33/48,0/96,oracle5/5.

The evaluator/unit tests reuse the exact hash-verified scorer from that preserved Git object. A shallow or single-branch
clone must fetch the retained Wave2 branch/commit; this prerequisite is a disclosed reproducibility limitation.
No full Vietnamese-language coverage, live extraction quality, browser E2E or production migration readiness is claimed.
Work ends at review, with the excluded W2-M4/M5 defects and the failed locked acceptance gate explicitly open.
