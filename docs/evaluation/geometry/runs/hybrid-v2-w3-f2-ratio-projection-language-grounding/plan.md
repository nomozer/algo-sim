# W3-F2 Ratio and Projection Language Grounding Implementation Plan

> For agentic workers: execute inline with `superpowers:executing-plans`; independent whole-change review follows verification.

**Goal:** Ground Vietnamese ratio and plane-projection paraphrases without weakening exact roles, source provenance or fail-closed behavior.
**Architecture:** Extend existing Registry source readers; preserve TypedFactNext schema, planner, engine, adapter and routing. Reuse the exact ratio solver and historical independent Fraction oracle/scorer.
**Tech stack:** Python 3.12, pytest, existing frontend tier tooling.
**Spec:** Owner GO `HYBRID_V2_W3_F2_RATIO_PROJECTION_LANGUAGE_GROUNDING`, supplied 2026-10-28; implementation interpretation in `architecture-decision.md`.

## Global constraints

- Baseline main/origin/main/GitHub: `996f114b3480efe1b0d075dd4342530aaa12ddae`.
- Research branch/worktree only; no main merge, push, cleanup or live provider request.
- Preserve historical Wave 3, W3-F1 and integration evidence byte-for-byte in Git.
- Product scope F2 only; F3/F4/F5, renderer, formation and kernel changes excluded.
- DEFAULT_MODE=LLM_ONLY; ALLOW_LIVE_AI=0; Hybrid opt-in.
- RED corpus/oracle/outcomes must be committed before product changes.
- Every Wave 3 replay is POST_FEEDBACK_DEVELOPMENT_REGRESSION.

## Review focus

- Ratio equality must belong to the point's stated segment, including complemented endpoint conventions.
- Plane projection must not borrow a line/triangle altitude, different foot, primed label or solid.
- Extra contradictory clauses and source roles must remain visible to existing coverage/role gates.
- A recognized word alone licenses no relation; mandatory mutations must fail at a relevant semantic gate.
- Historical W3-A06 exposes an already-existing radical-domain ceiling after F2 normalization; report separately, never fix or hide it here.

## Task 1: Baseline audit and preregistration

Files: this plan, `baseline-audit.md`, `architecture-decision.md`, `inputs/development.json`, `inputs/oracle.json`, `results/red-before.json`; run-local builder/evaluator and `backend/tests/geometry/test_ratio_projection_language.py`.

- [ ] Verify baseline identities, versions, 118-file freeze and W3-F1 23-test baseline.
- [ ] Lock the exact 21 F2 IDs from W3-F1 machine results; separate ratio/projection/combined defects.
- [ ] Build historical cases, independent exact-oracle authored positives, isolated masked-case control and at least 24 distinct semantic mutations.
- [ ] Run RED without product edits; pin input/oracle SHA-256 and expected statuses. Commit explicit files.

Expected: historical 21 show F2 refusal; canonical-normalization diagnostic serves 20 and exposes W3-A06 radical ceiling. New language positives demonstrate baseline false refusals; negatives record exact codes without accepting technical crashes.

## Task 2: Minimal source-reader repair (TDD)

Modify `backend/app/simulation/geometry_functions/registry.py`; test file from Task 1. Reuse `_TY_SO`, `_ty_so_khop`, `_ty_so_tron_cau`, `construction_source_bound`, role/provenance/coverage checks. Search callers and equivalent responsibilities before adding any helper.

- [ ] Extend ratio connectors to `sao cho`, `thỏa mãn`, `với`, including `lấy`/`chọn` fronted membership; retain exact equality, operand matching and 0<t<1.
- [ ] Add bounded explicit plane-altitude forms, binding foot/source/plane together and requiring the entire definition to be read.
- [ ] Run targeted tests RED→GREEN; all mandatory negative classes must refuse at a relevant gate, no wrong-served.
- [ ] Bump Registry only if changed semantics require it; update version-pinned tests/fixture compatibility, documenting cache effect.
- [ ] Commit product and covering tests, leaving all historical artifact files unchanged.

Expected: all preregistered F2 source bindings pass; all authored positives agree exactly with the independent oracle; original W3-A06 can remain refused only by the preregistered independent radical limit.

## Task 3: Regression, freeze, T0/T1/T2 and Full T3

- [ ] Generate GREEN, tamper receipts and 144-case Wave 3 replay in this run only. Compare per case with W3-F1; retain 72/72 negative refusals, reason agreement >=62, zero wrong-served.
- [ ] Run W3-F1, Source Gate, bridge/planner, exact radicals, Category A/B, adapter/certificate, provenance/contradiction, preview, cache, docs and thesis acceptance regressions.
- [ ] Record scope/impact/publication/version/cache/evidence checks as T0 and required frontend/build checks as T2.
- [ ] Freeze candidate and append candidate-divergence declaration. Commit freeze; create clean detached checkout at that exact commit.
- [ ] Run existing complete `frontend/scripts/full-gate.mjs` offline, preserve log bytes and receipt, verify post-T3 freeze and clean source. Do not clean up checkout.

Expected: all required tiers PASS, product freeze MATCH. Full T3 failure is a stop; do not claim a partial gate as Full T3.

## Task 4: Independent review and owner handoff

- [ ] Independent reviewer reads product diff, adversarial cases, source/oracle provenance, W3-F1 regression, version/cache and T3 integrity (12 Owner dimensions).
- [ ] Address BLOCKER/MAJOR within scope and re-review if necessary; stop if resolution requires excluded scope.
- [ ] Write `report.md`, `handoff.md`, `run.json`, `review.md`, `verification/tiers.json`; update living indexes with concrete artifact paths.
- [ ] Verify final product equals detached T3 candidate, all later changes docs/evidence only, publication/docs/freeze gates PASS, research checkout clean; main/remote unchanged.

Expected final status: READY_FOR_OWNER_REVIEW only when all gates pass; otherwise NOT_READY with a takeover checkpoint. No merge, push or cleanup.
