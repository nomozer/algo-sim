# W3-F2 ratio and projection grounding — blocked handoff

Task: `HYBRID_V2_W3_F2_RATIO_PROJECTION_LANGUAGE_GROUNDING`. Started 2026-10-28; safety handoff 2026-10-29.

**Final decision: NOT_READY.** Owner GO §15 requires a stop when negative/tamper cases become served or any WRONG_SERVED appears. The registered safety suite exposes two such cases. Product editing stopped; this branch is a research checkpoint, not an accepted candidate. No merge, push, cleanup or live provider call occurred.

## Identity and scope

- Baseline local main = origin/main = GitHub main: **996f114b3480efe1b0d075dd4342530aaa12ddae**, verified before creating the branch.
- Branch: `research/hybrid-v2-w3-f2-ratio-projection-language-grounding`.
- Worktree: `.superpowers/worktrees/w3-f2-ratio-projection-language-grounding`.
- Preregistration/RED commit: **90f58c4c6de102d58d971e890347e59f4bdc7bda**.
- WIP product checkpoint: **e9d5a9d73064a15b7702eb32c008835bc99fba6d**.
- Frozen candidate: **NOT_CREATED**. Full T3 receipt: **NOT_PRODUCED**.
- Baseline accepted freeze: **918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72**, 118 files.
- Working product diagnostic content hash: **e8c58cf9a03a3ed24a5720969acd5a204b6c651800716f296ff13a59b77ef82e**, 118 files; this is **not a frozen/verified candidate**.

Only `backend/app/simulation/geometry_functions/registry.py` changed in product. No Planner, bridge, engine, adapter, schema, frontend or default-route product changes were made. [Architecture decision](architecture-decision.md) and [baseline audit](baseline-audit.md) record the intended bounds and exact 21 historical IDs.

## Root cause and implemented checkpoint

F2-A has two narrow language barriers: Registry keywords accepted only `sao cho`, and the exact membership/equality reader had the same connector limitation plus fronted `lấy` only. The WIP extends those forms to `thỏa mãn`, `với` and `chọn`, continuing to solve the ratio with the existing Fraction reader and its operand/direction/0<t<1 checks. The equation must still be attached to explicit segment membership.

F2-B previously recognized `hình chiếu` only. The new bounded reader accepts explicit plane-altitude definitions in foot-first, source-first and hạ/kẻ forms. It binds source, foot and plane together, consumes the whole definition and retains the existing quote/role/negation/coverage and engine checks. Bare triangle/line altitudes are not promoted to plane projection facts.

No corpus IDs, answers or oracle values were introduced into product. Existing readers/modules were reused; one narrow Registry helper was added. No new product module or dependency was created. The evidence tool reuses the existing independent Fraction oracle and qualified Wave 3 scorer.

## RED/GREEN development evidence

Classification: **DEVELOPMENT_EVALUATION**, not independent blind holdout. Preregistration locked 96 cases before the product commit: 21 verbatim historical F2 cases (17 ratio-only, 2 projection-only, 2 combined), 24 authored ratio, 26 authored projection, one smaller isolated A06 control and 24 mandatory negative/tamper classes.

| Slice | RED served-correct | WIP after served-correct | Notes |
|---|---:|---:|---|
| Historical F2 | 0/21 | 20/21 | Original A06 remains an independent radical-ceiling refusal. |
| Authored ratio | 6/24 | 24/24 | Exact oracle and typed/source provenance agree. |
| Authored projection | 6/26 | 26/26 | Includes declared midpoint feet and Unicode-prime source quotes. |
| Isolated smaller A06 | 0/1 | 1/1 | Exact geometry validates F2 independently of the original radical limit. |
| Mandatory negatives | 24/24 refused | **22/24 refused** | **2 WRONG_SERVED; gate FAIL.** |

The 71 served positive cases agree with the independent exact section/area oracle; the original A06 is never counted as served-correct. Its radical refusal was preregistered after reproducing it with old supported wording on unchanged baseline. Closing a language gate is distinct from closing a downstream kernel bound.

`results/green-after.json` is the **failed after-change measurement**, not a GREEN acceptance verdict. `results/tamper-results.json` preserves all 24 actual outcomes. Locked expected outcomes/codes were not relaxed after these failures.

## Safety blockers

1. **BLOCKER — foreign declared premise scope is lost:** DEV-NEG-08 (ratio) and DEV-NEG-23 (projection) declare only s1 but attach the premise to foreign. PremiseSpec.solid_id is a real contract field. `typed_fact_next_bridge.py` ignores _id fields during qualified-reference validation and drops scope when translating these relations. Both now serve, classified WRONG_SERVED. This is invalid provenance, without a claim of incorrect arithmetic. Unchanged main Registry /20 also serves both after only canonical wording replacement, proving a baseline-masked defect whose reachability expands with F2. See [baseline reproduction](verification/baseline-foreign-scope-reproduction.json).
2. **MAJOR — projection incidence test not demonstrated:** DEV-NEG-20 refuses with UNDERDETERMINED_POINT, outside the locked reason codes. The intended off-plane-foot contradiction check has not been demonstrated. It remains refused and classified REFUSED_REASON_DISAGREEMENT; do not relabel it as an exact reason pass.

[Independent review](review.md) confirms the findings and the mandatory stop. It independently ran F2 + F1: **116 passed, 4 failed** (NEG08/20/23 and the /20→/21 version pin). F1's **22 behavioral checks pass**; its full suite is not green because the version pin is unfinished. The original baseline F1 suite passed all 23 before product edits.

## Verification and versions

[Verification tiers](verification/tiers.json): T0 baseline/scope/evidence checks are recorded; cache/fixture compatibility and final version bookkeeping remain incomplete. T1 is **94 passed, 3 failed**. T2 and Full T3 were **not run because Owner safety-stop conditions triggered**. No frozen candidate or T3 inheritance claim exists.

Registry /21 is provisional for the expanded language. Planner /18, Engine /14, Adapter /4, Certificate /1 and cache130 remain. Fixture exporter/version-pinned test updates are unfinished and must precede any new freeze. Cache invalidation decision is **NOT_FINALIZED**. DEFAULT_MODE=LLM_ONLY, Hybrid opt-in, ALLOW_LIVE_AI=0, live calls=0 remain; no production routing was changed.

Full 144-case Wave 3 post-feedback replay is **NOT_RUN_DUE_TO_SAFETY_STOP**; its after-F2 aggregate counts are **UNKNOWN**. Do not publish 49/72 or 50/72 as measured results. The previous main W3-F1 record stays 29/72 served, 43 false refusals, 72/72 negatives refused, 62/72 reasons and 0/144 wrong-served. Previous remaining F3/F4/F5 counts 16/5/1 are baseline facts, not newly measured after-F2 counts. Any eventual replay must be POST_FEEDBACK_DEVELOPMENT_REGRESSION.

## Evidence and continuation

[Scope/evidence receipt](verification/scope-and-evidence.json): locked input/oracle/RED hashes MATCH; historical Wave 3, W3-F1 and prior integration Git blobs/checkouts remain unchanged. No original scorer, oracle, corpus, result or receipt was overwritten. Calibration intake packets remain separately classified; they are not accepted product measurements. Previous 772-file backups and ACL-locked directories were untouched.

[Takeover checkpoint](takeover.md) records the stop, commits, files, exact failing cases, missing gates and next decision. A future authorized change should validate premise scope before bridge translation erases it, cover references to a second declared solid and isolate the off-plane projection test. It must keep the current exact math/Source Gate rules and must not repair F3/F4/F5 or kernel limits merely to increase counts.
