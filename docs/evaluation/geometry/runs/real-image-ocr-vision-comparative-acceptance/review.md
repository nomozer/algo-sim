# Independent task-delta review

Reviewed 2026-11-11 against `6bb22fa3bb183ad28cdf1395c99e5eb375fac97c` in the owner-designated worktree. Initial measurement receipts identify `4ab43853edc030beda13ef017d4b6c51cf24127a0a41dd9149e640f4cffdbce3` / 115 files; the numeric review fixes below postdate those measurements, so a final candidate identity and stable-source checks remain parent-owned gates. This is a read-only review of product code, connected callers, tests and existing receipts; the only written file is this review. No full test suite, benchmark or live provider call was run. Small offline Python probes exercised the comparator directly.

## Strengths

- The worker reader now binds its output queue per process, signals EOF and rejects non-object JSON. Shutdown waits for the process and closes its pipes. The new lifecycle tests use actual subprocesses rather than mocked transport.
- Frontend span replacement now uses Unicode code points, matching Python offsets, and edits invalidate global confirmation. The change is limited to the existing reducer and span helper.
- Resource accounting follows the full FastAPI descendant tree, including the Windows venv launcher's real interpreter. The receipt explicitly describes RSS double counting and the 25 ms sampling lower bound. Crash recovery and explicit shutdown receipts report no surviving Python descendants from the recorded worker trees.
- The automatic API arm submits returned OCR text directly. Reference text enters only the separately labelled simulated correction arm (`tools/evaluate_acceptance.py:194–201`). New-corpus solver outputs remain ungraded without a mathematical oracle. Live Vision and real student usability are explicitly unmeasured; no parser/kernel implementation changes appear in the product delta.

## Important findings

1. **Concurrent prepare acceptance has a 25% unhandled-error rate, and its stated cause has no supporting receipt.**

   `ocr_worker_resource_profile.json:1369–1378` records 15 HTTP 200 and 5 HTTP 500 responses out of 20 requests. `tools/evaluate_acceptance.py:294` hardcodes the cause as `see failure_surface.json: concurrent_new_guest_sessions_sqlite`, but `failure_surface.json` contains no such case or exception evidence and identifies the older `b79cd3bc…` measurement. The harness drops non-JSON bodies to `NON_JSON_RESPONSE` (`tools/evaluate_acceptance.py:141–147`) and does not retain a sanitized exception type or failing server stage. Therefore the failure rate is observed; a SQLite root cause is not established by the committed evidence.

   There is a concrete source-level suspect: the async prepare handler calls the synchronous session gate (`backend/app/main.py:1458`), whose commits run on the event loop (`backend/app/main.py:1085`). Session lookup dirties `last_seen_at` (`backend/app/accounts/service.py:69`). Concurrent `/api/auth/me` creates/flushed sessions in a sync handler and commits only in the dependency teardown (`backend/app/accounts/router.py:266–286`, `296–301`). Synchronous local OCR also blocks the event loop (`backend/app/ingestion/unified_input.py:499`). Lock ownership and teardown scheduling could explain the roughly five-second failures, but this remains a hypothesis until a bounded reproduction records the exception and stage. Capture that minimal evidence and either fix the confirmed blocker or report the concurrent acceptance gate as failed; do not describe the 15 successful requests as concurrency acceptance.

   Classification: observed acceptance blocker; connected product paths are pre-existing, not introduced by the three-file delta.

2. **The new numeric check creates conflicts for unchanged geometry.**

   `backend/app/ai/adaptive_input_router.py:1017–1020` compares every lexer `value` string, including problem-header numerals and spacing-sensitive scalar forms. Direct offline probes confirm both regressions relative to the same function without the new block:

   - `Câu 1: Cho hình chóp S.ABC có cạnh đáy 2a. Tính thể tích.` versus the same text without `Câu 1:`: previous conflict list `[]`, current `['NUMERIC_ASSIGNMENT_CONFLICT']`; the extra value is the header's `1`.
   - `Cho hình chóp S.ABC có cạnh đáy 2a. Tính thể tích.` versus the same text with `2 a`: previous `[]`, current `['NUMERIC_ASSIGNMENT_CONFLICT']`; lexer values are `['2a']` versus `['2', 'a']`.

   The caller converts this into `VISION_NEEDS_CONFIRMATION` (`backend/app/ai/adaptive_input_router.py:1310–1320`), requiring an unnecessary student intervention after a valid Vision fallback. Restrict comparison to mathematical dimension spans and canonicalize equivalent scalar spelling, with negative-control tests for headers and coefficient spacing. The radical/fraction comparator already has separate normalization limitations; those are not claimed as new regressions here.

   Classification: new product regression, P2. **Resolved in review follow-up:** the parent replaced the global bag with descriptor/value pairs taken from worded dimension spans, excluding exam headers and joining coefficient whitespace. I inspected the replacement and reran both direct probes: both now return no conflict. Regression tests for both controls are present. The parent owns the running targeted suite and final regression results.

3. **A sorted bag of worded values does not verify which dimension owns each value.**

   At `backend/app/ai/adaptive_input_router.py:1017–1019`, sorting removes object binding. A direct probe comparing `cạnh đáy 2a và chiều cao 3a` against `cạnh đáy 3a và chiều cao 2a` returns no conflict at all. Both sides contain the same scalar bag, but represent different volumes. These phrases have no equals-sign assignment, so the preceding assignment comparator cannot catch the swap. When otherwise clean OCR competes with Vision, the caller can proceed with the changed dimensions without the promised conflict confirmation.

   Keep dimension-to-value associations, or conservatively require review when a worded dimension cannot be compared with its corresponding operand. Add a swapped-dimension test alongside the new `cạnh 2a` versus `cạnh a` tests. This is a pre-existing safety gap left open by the new scalar check, not a newly introduced wrong-serve regression; this review does not claim an image-to-wrong-answer reproduction.

   Classification: incomplete coverage of the task's mathematical-conflict requirement, P2. **Resolved for the reproduced case in review follow-up:** the parent retains descriptor/value pairs. My rerun now reports `NUMERIC_ASSIGNMENT_CONFLICT` for swapped edge/height values and no conflict when the unchanged dimensions are reordered. A swapped-binding test is present. This does not establish support for arbitrary natural-language dimension descriptions.

## Declined to judge

- Live OCR/Vision quality and cost: no authorized live measurement; the receipts correctly mark them unmeasured.
- Real student speed or usability: scripted browser actions and oracle-driven corrections are not a human study.
- Independent H-1 validity or general geometric coverage: the corpus is eight agent-transcribed images with acknowledged domain gaps and no mathematical oracle, and it is not labelled independent H-1.
- Full final regression readiness: the available summary is `INTERRUPTED_FOR_CONFIRMED_PRODUCT_FIX`; the parent owns the stable-source rerun. No completed-suite claim is inferred from it.
- Hypothetical worker process-tree leaks on other operating systems: the recorded Windows lifecycle checks pass; no failure reproduction was found in the reviewed environment.

## Assessment

**Ready for acceptance: pending the concurrency diagnosis and stable-source verification.** The two numeric findings are addressed for the reproduced cases and their negative controls. The parent is adding sanitized exception capture to a fresh loopback server to diagnose the concurrent HTTP 500s; until that bounded reproduction completes, the failure remains unresolved and the original receipt's causal attribution is unsupported.
