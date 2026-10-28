# W3-F2 baseline audit and preregistration

Date: 2026-10-28. Task classification: CORE (Vietnamese source interpretation for exact 3D geometry), with SUPPORTING evaluation.

## Preflight

- Active branch: research/hybrid-v2-w3-f2-ratio-projection-language-grounding.
- Branch creation HEAD/main/origin/main/GitHub main: 996f114b3480efe1b0d075dd4342530aaa12ddae, verified by fetch and ls-remote before branch creation.
- New isolated worktree: .superpowers/worktrees/w3-f2-ratio-projection-language-grounding. Root had no reported tracked/untracked changes; pre-existing ignored cache/temp ACL warnings preserved. Registered historical/active worktrees and old backups were untouched; no process command line referenced the new worktree.
- Current milestone: main-integrated W3-F1 product a609c487, frozen candidate b02b2c42. Fresh baseline freeze MATCH: 118 measured files, 918d3404ac60e81d62c75f6bfb7067ea25a4e27c197e3584075edef42e441f72. W3-F1 tests: 23 passed.
- Versions verified in source: Registry /20, Planner /18, Engine /14, Adapter /4, Certificate /1, cache130; default LLM_ONLY, Hybrid opt-in, live0.
- Existing/reused modules: registry.py (_TY_SO, _ty_so_khop, _ty_so_tron_cau, construction_source_bound, kiem_nguon, _doc_phep_dung_cau_hoi); existing exact Fraction oracle and qualified scorer from historical Wave 3; current freeze/cache/impact/full-gate tooling.
- Source of truth: Owner specification, actual Registry/bridge/planner code, locked per-case Wave 3/W3-F1 artifacts and independent geometry.
- Expected product changes: registry.py only. Supporting changes: targeted tests, exact Registry version pins in existing tests, fixture exporter compatibility delta, current candidate manifest, run-local evidence, living indexes. No default/cache/kernel/schema change without measured justification.
- Contract/history impact: broader recognized F2 language requires Registry version pin; no planner/schema expansion. All historical evaluation files stay unchanged. Duplicate implementation risk bounded by extending existing readers; no new product module. No new dependency or cycle.
- Smallest sufficient implementation: closed language forms plus exact existing role/ratio/geometric checks. Scope creep guard: do not repair masked radical ceiling, F3/F4/F5, planner/adapter behavior, Scene3D or production routing.
- Stop conditions: unexpected baseline, wrong-served, weakened negatives, unrelated regression, historical evidence mutation, freeze/T3 failure, unresolved independent-review blocker/major, or unsafe worktree state.

## Exact historical 21-case inventory

W3-B02, W3-B04, W3-B06, W3-B12, W3-B14, W3-B20, W3-B22, W3-B24, W3-B28, W3-B30, W3-B31, W3-B32, W3-B38, W3-B40, W3-B42, W3-B46, W3-A02, W3-A06, W3-A10, W3-A12, W3-A16

Original 14 first-refusal F2 cases plus 7 exposed by W3-F1 are preserved verbatim. Root-cause groups: ratio-only 17, projection-only 2, combined 2. Locked current first-refusal counts from the W3-F1 correction are F2=21, F3=16, F4=5, F5=1.

The keyword gate accepts only `sao cho` for divide_segment and `hình chiếu` for orthogonal_projection; the construction readers likewise lack the new connectors/plane-altitude forms. No synonym-only bypass is permitted.

## Preregistered development corpus and RED

96 cases: 21 verbatim historical F2 positives; 24 new authored ratio cases across six solid families; 26 authored projection cases across triangular/quadrilateral pyramids and oblique prisms (including two separately declared midpoint feet and Unicode prime source text); one smaller isolated A06 language control; 24 mandatory negative/tamper classes. New authored cases have changed labels, dimensions and ratios, and explicit exact geometry. They are development/metamorphic data, not independent holdout data.

Every positive has locked typed/source relations, exact source quotes, expected route behavior and a geometry/section oracle computed by the existing standalone Fraction implementation with no product geometry import. The standard disposition remains SERVE even for the preregistered masked historical case; the evaluator separately records that limit rather than calling it served-correct.

RED on unchanged baseline: historical 0/21 served; authored ratio 6/24 served; authored projection 6/26 served; isolated 0/1 served; mandatory negatives 24/24 refused; zero wrong-served. Baseline canonical-language diagnostic verifies 71/72 positive geometries serve correctly when ONLY F2 language is normalized to old supported forms.

**Masked independent limit:** W3-A06 still refuses with ENGINE_EXECUTION_FAILED / RadicalDomainError after canonical language normalization. Its unreduced radical exceeds the existing bounded kernel ceiling. Original source/corpus/oracle stay intact. The registered smaller A06 control uses SE=7a instead of 15a and passes the canonical baseline oracle/route. Closing F2 is measured separately from whether the original case can finish downstream. Expected Wave 3 reference is therefore at most 49/72 served if this is the only exposed independent limit; 50/72 is not promised.

## Corpus calibration before preregistration lock

All preparation occurred before product modification and before the preregistration commit. Three diagnostic intake packets are preserved under diagnostics/: `intake` used unsupported uppercase Ω and a noncanonical structured Unicode notation; `capability-intake` exposed a pre-existing duplicate IR-memory declaration when adding a redundant projection fact to right prisms/cuboids/cubes; `unicode-intake` checked the legacy whole-solid Unicode source path. These are measurement-apparatus/capability diagnostics, not product repair scores. Final registered projection inputs use currently composable families, canonical structured identities and Unicode in ratio/projection source quotes. The fixed historical set of 21 was never changed. No product workaround was added for these unrelated paths.

## Frozen inputs and expected outcomes

- inputs/development.json SHA256_LF: cbf6926e159a9db9340fdb3fcc6b095a6eabd45e0aebc229f94b998ee7aeea26
- inputs/oracle.json SHA256_LF: 9c16b140c4c773c38cb12de15319f701e73949dc3ed256a40052400ab49e79c0
- results/red-before.json is the final preregistered RED receipt; earlier intake receipts remain separate.
- Acceptance: all authored and isolated positives served-correct with exact independent oracle and source provenance; all 21 historical F2 source relations pass, with original A06 allowed only its specifically diagnosed independent radical refusal; 24/24 mandatory negatives refused at the locked relevant codes; zero wrong-served.
- Wave 3 replay remains POST_FEEDBACK_DEVELOPMENT_REGRESSION; preserve all previous served cases and all 72 negative refusals, reason agreement >=62/72. Report every newly exposed independent refusal honestly.
