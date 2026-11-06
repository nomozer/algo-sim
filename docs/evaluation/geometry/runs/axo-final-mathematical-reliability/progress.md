# Progress

Checkpoint 1 — 2026-11-06. Branch integration/axo-hybrid4-reliability, HEAD 59ed17b4. Tracked files clean; numerous prior-run perf images/traces/logs untracked and protected. Owner explicitly confirmed exclusive write access.

Read: AGENTS/RULES bootstrap, current guidance entry sections, prior viewer report/handoff/manifest, existing provenance/goal policy/history/adapter and publication gate. No product edits yet.

Baseline offline probe (manually authored V2 facts, not live extraction): exact original ABC.DEF prism -> SERVED; kernel_check true; answer q coefficient 30; Adapter scene quantity kq_q=30. An initial system-Python probe could not import pydantic; existing root backend/.venv works. A terminal cp1252 output issue was corrected by ASCII JSON output, no product failure inferred.

Active: read-only publication HEAD/integration scan, exec session 29055. No pytest/Vitest/build/browser sessions started. No provider calls.

Next: reproduce frontend goal summary on the same emitted scene, add red regression, locate first incorrect classification. Check publication scan session before starting heavy tests.

## Checkpoint 2 — product and regression work

Exclusive access confirmed. HEAD still 59ed17b4; no commit yet. Heavy suites were sequential; no browser started. Publication baseline completed: HEAD 28,963 blobs / 98 pending findings (95 traceback, 2 bearer placeholders, 1 test fixture); integration bb61a804..HEAD 2,726 blobs / 125 messages / 1 historical password-fixture finding at blob 28be1ef6, line 197. No exception changed. The scanner peaked near 3.29 GiB process working set; measured system available RAM 5.65 GiB then 7.121 GiB before integration.

Findings and corrections to early hypotheses:
- The exact requested prism is ALREADY SOLVED on this HEAD in the fresh Hybrid /4 route AND frontend (30, reached). The previous screenshot warning is not reproduced by the manually authored facts. Live extraction forbidden/unmeasured; no claim its cause is known.
- History whitelist really loses hybrid_preview/source provenance. RED regression observed; fixed by retaining the existing validated scene-bound view. This data-integrity defect was real but does not by itself reproduce the prism warning (the baseline prism also reaches without metadata).
- An UNVERIFIED quantity really produces the false claim that mathematical givens are insufficient. RED observed. Replaced that diagnosis with missing certification; current backend refusal categories remain unchanged.
- Legacy history with equivalent catalog config wrongly borrows catalog original text. RED observed. Catalog source now requires explicit sample ID; explicit catalog opens save existing problem_statement field for later history reopening, preserving IDs. No migration/version bump.
- Saved answer metadata was accepted with another scene coefficient. RED observed. Retain existing exact coefficient in the optional frontend view field and compare it on revalidation.

Modified product: history.ts, store.ts, hybrid-preview-adapter.ts, goal summary copy, workspace statement/copy, Vitest cap 2. No backend/app, Planner, Compiler, Kernel, CACHE_VERSION or wire schema change.

Tests: backend mathematical suite 13/13; 12 cases (8 exact served, 4 classified refusals), formulas plus one-condition oblique non-uniqueness witness. Backend related integration 164 passed, 12 setup errors solely old pytest temp directory ACL; failed publication module rerun alone in a fresh unique basetemp -> 13 passed. No assertions/timeouts weakened. Frontend first related set 88 passed in 6 files. Second set 158 passed / 5 failures in 2 files due old wording assertions; updated to require neutral missing-certificate text and forbid unsupported insufficiency claim; failed files rerun -> 35 passed. Typecheck caught unused imports and test-only source typing, fixed; build currently session 59196 (check completion before scheduling browser).

Next: final product build, browser scene consistency/two-tab/camera, publication consumer inventory, fresh review, commit checked changes, clean detached T3. Do not rerun already-passed backend suites except final single T3. Preserve historical untracked artifacts.

## Checkpoint 3 — Claude resume (final)

Codex stopped uncommitted after checkpoint 2 plus three browser groups. Claude committed the Codex state unchanged
(ac71a439), found by a full Vitest run that reopening an explicit sample record lost its sample identity (R-1), fixed it
at reopenFromHistory with red/green and fault injection (e2f0cb90), added seven hand-oracle edge cases to the backend
suite (no backend defect; two mutants killed), refroze the candidate (5af750e8), ran T3 PASS and the node harness on a
clean detached worktree, reran all browser groups on the fixed build and the publication scans. Final status
READY_FOR_OWNER_REVIEW; details in report.md.
