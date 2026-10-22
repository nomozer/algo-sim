# T3 failure root cause and correction

## 1. Full T3 Attempt 1 (`404f0568a00651505ec0773754a04ef5c493f5f9`)

Classification: **candidate/freeze metadata contract mismatch**, not a demonstrated mathematical regression.

Original immutable candidate: `404f0568a00651505ec0773754a04ef5c493f5f9`, product `8b5916e7309a8939f0c462367120360391ccb70c`, measured hash `2711d78e401234a2bea98a983d94fe1b29973b4482b407c5529307e38f67b16d` / 115 files. Full T3 attempt 1 remains FAIL: 1 failed, 11492 passed, 1 skipped, 2 deselected, 9 xfailed; frontend 1156 passed, build/demo/crash gates passed. Elapsed 617.84 s. Original logs and receipt remain in `../typedfactnext-planner-bridge/verification/t3-attempt1/`; original stream SHA256 and bytes are recorded in `recovery-inventory.json`.

Exact failure: `backend/tests/geometry/test_thesis_acceptance_matrix.py::test_C2b_candidate_hien_tai_phai_duoc_KHAI`, line 347, `KeyError: run_candidate_hash`. The correction-chain resolver selects the Session 1 layer, which omitted the historical thesis run link. Its current product hash was correct. The previous layer in `simulation-demo6b-renderer-fix/candidate_divergence.json` includes the key and matches immutable `thesis-final-acceptance/IDENTITY_LOCK.json`; Git source at `43247c9e` has that valid layer. Baseline comparison is source/receipt evidence, not an invented new baseline execution.

Fresh isolated reproduction: `verification/repro-c2b/execution.json`, exit 1, 4.72 s; same missing key. Minimal remedy: NEW `candidate_divergence.json` in this run, correcting the Session 1 layer and restoring `run_candidate_hash` and `run_id` from the unchanged lock. No weakened assertions, changed expected answers, skipped tests, altered thesis policy or rewritten receipt. `verification/targeted-governance/` then passed 53 tests in 41.47 s (pytest 40.57 s). Focused backend: 239 passed in 19.41 s (pytest 18.48 s), before the later review fixes.

Independent review subsequently required bridge safety fixes (`ac719a5b` and `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee`). Those change product bytes; therefore the metadata-only correction here retains its old identity and is superseded by `../backend-hybrid-bridge-safety/candidate_divergence.json` for `4f3aaea5`.

---

## 2. Full T3 Attempt 2 (`4fb1045f40a326f9d23e2fdad9fcd5b2290697f2`) & Gemini Takeover Correction (`b6684564ac4596da30819da5fcc4c875ebb1a640`)

Classification: **incomplete refusal-code taxonomy registration after `4f3aaea5` bridge safety fixes + environment temp-path file-lock collision**, not a mathematical or source-gate regression.

Immutable candidate executed in `.superpowers/worktrees/hybrid-backend-continuation-verify`: `4fb1045f40a326f9d23e2fdad9fcd5b2290697f2`, product `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee`, measured hash `22c4fc6de9350cfee55d3eb4a4b3497410214ba39ac18c2f9a5db4384631ef51` / 115 files. Full T3 attempt 2 remains FAIL (`verification/full-t3/execution.json`, exit 1, 559.31 s): 3 failed, 11502 passed, 1 skipped, 2 deselected, 9 xfailed; frontend 1156 passed (`72/72` files), build/demo (`5/5`)/crash (`6/6`) gates passed.

Exact failures and root causes:
1. `tests/geometry/test_hybrid_compiler_benchmark.py::test_every_refusal_code_of_the_route_is_classified` — `AssertionError: ['INVALID_TYPED_FACT_NEXT', 'UNKNOWN_VERTEX_REF']`:
   - In `ac719a5b` / `4f3aaea5`, Codex added `TuChoi("INVALID_TYPED_FACT_NEXT", ...)` (`typed_fact_next_bridge.py:36,45`), `KetQuaTuyen("REFUSED", "INVALID_TYPED_FACT_NEXT", ...)` (`function_route.py:264`), and `TuChoi("UNKNOWN_VERTEX_REF", ...)` (`typed_fact_next_bridge.py:69`).
   - `_route_refusal_codes()` in `test_hybrid_compiler_benchmark.py` scans all `backend/app/simulation/geometry_functions/*.py` and `backend/app/ai/function_route.py`. Codex registered `BRIDGE_UNSUPPORTED_LENGTH_UNIT` and `QUALIFIED_LABEL_COLLISION` in `hybrid_compiler_benchmark.py::REFUSAL_CLASS`, but omitted `INVALID_TYPED_FACT_NEXT` and `UNKNOWN_VERTEX_REF`.
   - Both codes are genuine malformed-input refusals (`"malformed"`), identical in taxonomy class to `SCHEMA_INVALID`, `FACT_INCOMPLETE`, and `UNKNOWN_SOLID`.
2. `tests/test_hybrid_preview_contract.py::test_every_literal_route_d_refusal_code_is_classified` — `AssertionError: ['BRIDGE_UNSUPPORTED_LENGTH_UNIT', 'INVALID_TYPED_FACT_NEXT']`:
   - `_ROUTE_D_SOURCES` in `test_hybrid_preview_contract.py` scans `app/ai/function_route.py` for uppercase refusal literals and asserts none classify to `FALLBACK` in `app/ai/hybrid_preview.py::classify_refusal`.
   - Because `4f3aaea5` added string literals `"INVALID_TYPED_FACT_NEXT"` and `"BRIDGE_UNSUPPORTED_LENGTH_UNIT"` to `app/ai/function_route.py:264,270` without adding them to `app/ai/hybrid_preview.py::_NHOM`, both fell through to `FALLBACK`.
   - `"BRIDGE_UNSUPPORTED_LENGTH_UNIT"` is a genuine capability-boundary refusal (`"CAPABILITY"` / `capability_gap`) when `TypedFactNextPayload.length_unit` declares `"a"` without symbolic length facts, and `"INVALID_TYPED_FACT_NEXT"` is a genuine malformed-payload refusal (`"EXTRACTION_FAILED"` / `geometry_generation_failed`).
3. `tests/geometry/test_hybrid_ab_pilot_runner.py::test_runner_executes_both_real_adapters_with_separate_telemetry_and_resume[FULL_AB-288]` — `PilotStopped: PERSISTENCE_FAILED`:
   - Full T3 Attempt 2 was invoked with `PYTEST_DEBUG_TEMPROOT=D:\Documents\projects\algo-sim\.superpowers\pt-22172` (inside the tracked workspace tree scanned by Windows Defender / filesystem indexers), causing a transient `WinError 5` lock on `os.replace(runs.jsonl.tmp, runs.jsonl)` during 288 rapid sequential atomic rewrites. Running pytest with standard OS `%TEMP%` passes `79 passed` in `test_hybrid_ab_pilot_runner.py` without modifying `run_hybrid_ab_pilot.py` (which hashes its own source via `runner_sha256`).

Minimal remedy in `b6684564ac4596da30819da5fcc4c875ebb1a640`:
- Added `"INVALID_TYPED_FACT_NEXT": "malformed", "UNKNOWN_VERTEX_REF": "malformed"` to `REFUSAL_CLASS` in `backend/tests/geometry/hybrid_compiler_benchmark.py`.
- Added `"BRIDGE_UNSUPPORTED_LENGTH_UNIT"` to `"CAPABILITY"` and `"INVALID_TYPED_FACT_NEXT"` to `"EXTRACTION_FAILED"` in `backend/app/ai/hybrid_preview.py::_NHOM`.
- No guard was weakened, no expected answer was changed, and no invalid problem was allowed to serve. Because `backend/app/ai/hybrid_preview.py` is inside `MEASURED_SYSTEM_PATHS`, the measured system hash updates to `13fd32b498ea9e47f23f01d0f4efc99b7f8d789ed6e59fe814c8fc4891d7e172` (`115` files), declared in `../backend-hybrid-taxonomy-completion/candidate_divergence.json` and re-frozen for Authoritative Full T3 Attempt 3.

---

## 3. Historical RED / Failed Attempts Preserved

Earlier focused failures inherited from Claude remain failures: pre-review and post-review 1/2/3 candidate fingerprint guard, before freeze (1902 pass, 1 fail, 1 xfail in post-review3). New RED attempts intentionally failed 8/9, then 2/2 qualifier cases, then 2/2 plane/ID cases. Full T3 Attempt 1 (`t3-attempt1/`) and Full T3 Attempt 2 (`full-t3/`) remain recorded as FAIL. Their local raw logs are not committed (raw tracebacks); command/exit/hash receipts are retained. PASS attempts do not erase these attempts.
