# Real-image OCR/Vision comparative acceptance implementation plan

**Goal:** Evaluate and improve image input without weakening mathematical correctness.
**Spec:** Owner's unified master task, supplied 2026-11-10 (attachment).
**Architecture:** Reuse the existing local OCR sidecar, reconciliation, fidelity gate, span confirmation, local parser and Hybrid /4 solver. Keep recognition, parsing, solving and rendering measurements separate.
**Execution:** Continuous in the existing worktree; independent evidence reconciliation and corpus acquisition delegated with exclusive file ownership. Parent owns product changes, regression, measurements and integration.

## Global constraints

- Existing branch `feat/local-first-geometry-understanding`; baseline `6bb22fa3bb183ad28cdf1395c99e5eb375fac97c`.
- No new branch/worktree; no merge, push or deploy. Preserve root untracked `ocr_reconcile.py`.
- `ALLOW_LIVE_AI=0`; no paid provider calls without separate owner authorization.
- Preserve historical evidence bytes. Agent transcriptions are unverified references, never human verification or independent H-1.
- No geometry expansion or Planner/Kernel rewrite; preserve contracts /26, /33, /24 and cache132 unless a proven correctness regression requires a scoped fix.
- New images remain in ignored local cache; corpus split is frozen before OCR evaluation. No tuning on evaluation images.

## Review focus

1. A dropped prime or changed radical must not become automatically accepted mathematical input.
2. Multiple spans must retain correct offsets after Unicode edits and cancellation.
3. OCR worker crashes/timeouts must fail closed and release resources.
4. Combined memory includes the OCR child; warm/cache measurements cannot replace cold request latency.
5. An answer without a source-independent oracle remains ungraded, even when the solver returns a scene.

## Tasks

- [x] 1. Verify Git ancestry, frozen candidate and historical receipt hashes; independently recompute CER with original normalization and explicit case filter. Write baseline and correction receipts.
- [ ] 2. Run canonical full backend pytest and frontend `test:wave` against unchanged baseline. Record command, exclusions, environment, output hashes, real counts and failures.
- [x] 3. Acquire new real image candidates with provenance; exclude previously used hashes; freeze development/evaluation split and agent-transcribed references before OCR.
- [x] 4. Evaluate local OCR and actual prepare/analyze API paths. Record recognition fidelity, critical tokens, acceptance/refusal, parsing, solving, scene and oracle status separately. Prepare authorization-gated live comparison; mark live unmeasured.
- [x] 5. Diagnose development failures; reproduce any product bug in a failing regression test, apply minimal fix, verify targeted tests and development before/after. Lock candidate before evaluation split.
- [x] 6. Validate span confirmation in real Chromium at 100%/110%, keyboard and small viewport, stale input/cache and Scene3D update. Label scripted correction simulated; real students unmeasured.
- [x] 7. Measure cold/warm/cache requests and process-tree RSS during actual inference, repetitions and bounded concurrency. Check worker failure/recovery and cleanup; physical low-end unmeasured.
- [ ] 8. Run full final regression, demo replay, crash audit, docs IA, publication safety and candidate verification. Review evidence, write report answering all 32 owner questions and architectural decision with explicit limitations. Commit allowlisted changes and verify clean freeze if gates permit.

## Execution ledger

- 2026-11-10: Verified specified worktree initially clean at baseline HEAD; root has unrelated untracked file, preserved. Existing graphify graph absent; use canonical CODE_INDEX and focused searches without creating a new repository graph.
- Ruling: The owner's detailed spec and continuous execution directive authorize implementation without an additional design approval checkpoint. Live provider authorization remains separate and absent.
- Ruling: No detached verification worktree may be created; measurements here are in the owner-designated worktree and are not described as independent clean-worktree verification.
- 2026-11-10: Historical metric reconciliation completed: 5-polyhedral median CER 0.1135; all-12 median 0.1040, original receipt scores reproducible, report 0.0110 not reproducible. Original files preserved.
- 2026-11-10: RED witnessed: three frontend regressions (non-BMP codepoint positions and confirmation invalidation), five worker transport/lifecycle regressions. GREEN: 6 worker tests and 13 frontend targeted tests. Fixed only local_ocr.py and photo-problem-flow.ts; no geometry changes.
- 2026-11-10: Actual OCR rerun completed for all 16 prior images/17 problem variants: 1 automatic served and 10 simulated-corrected served against existing mathematical oracles; 6 not served. These categories remain separate. See prior_corpus_actual_rerun.json.
- 2026-11-10: Production build passed; actual Chromium historical scenarios 6/6, added confirmation audit 4/4. Added audit covers keyboard, CSS zoom 100/110 (explicitly not browser chrome zoom), mobile viewport and cancellation. Screenshots remain ignored locally because they contain external source image crops.
- 2026-11-11: Session resumed. Original long-running regression process and API server no longer available; no full-suite completion receipt recovered. Mark interrupted attempt NOT_RECOVERABLE and run full final checks, never copy old PASS counts. Preserved completed receipts and product changes.
- 2026-11-11: Corpus frozen8 relevant images/31 fresh downloads, split2 development/6 evaluation. All references agent-only; no new handwriting. Target20–30 not reached, source429 stopped acquisition. No recognition heuristics tuned to these images.
- 2026-11-11: Review found header/spacing false conflicts and swapped dimension binding missed by the initial numeric bag; tests reproduced RED then target-bound lexical comparison passed50 related tests. Six development mock fixtures now preserve3 conflicts/3 controls.
- 2026-11-11: Controlled real-SQLite lock test RED→GREEN after moving prepare session guard to existing thread pool;44 related API/OCR tests passed. Follow-up HTTP10/10 before and10/10 after, so no causal claim that this removes the prior5/20 stochastic500s. Exact original cause remains UNKNOWN.
- 2026-11-11: Product/test checkpoints2969e9e76 and7b1700214. The latter removes a pre-existing reviewed-status glyph rejected by the full UI hygiene gate;26 focused UI tests passed. Candidate115/hash a068b6f6586c1b12… cache132 verified before full stable-source regression. No geometry change.
- Ruling: Resource files identify measured precursor4ab43853 and shared workstation contention. They are retained with their true identity; later guard/comparison/UI fixes are not relabelled as the same performance measurement.
- Ruling: New corpus includes only one named-polyhedron distance problem within the solver's intended scope and predominantly unsupported application/curved problems. It is useful boundary/recognition evidence, not a representative solve-rate benchmark; pilot remains restricted and architecture winner pending live evidence.
