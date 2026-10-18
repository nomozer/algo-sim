# Route D offline preview wiring — Codex work recovered and completed by Claude

- **Run:** `hybrid-route-d-preview-wiring` · branch `research/hybrid-route-d-preview-wiring` · base `main` `6592306d`
  (= `origin/main`)
- **Owner scope:** `GO_HYBRID_ROUTE_D_PREVIEW_WIRING`; emergency takeover after Codex GPT-6.1 Sol High hit its usage
  limit mid-regression / mid-review (2026-10-18 ~09:28).
- **Commits:** `902730b9` Codex work as found · `af4bcf47` takeover fixes · `8ffa58f4` freeze (75af7b71…, superseded) ·
  `f6ff8a5e` docs · `93390f58` review fixes (**product commit**) · `dc8e25ba` refreeze · this commit (guard test + docs) ·
  receipts commit.
- **Product identity:** `measured_system.tree_hash` `4c1b9a270430773a0bafede1f86120ea92ad066accdd7163cbe405b50253142d`,
  111 files.
- **Held constant:** `DEFAULT_MODE = LLM_ONLY` · `RESPONSE_CONTRACT = flat` · `HYBRID_PRODUCT_ENABLEMENT = NO-GO` ·
  `ALLOW_LIVE_AI = 0` · `CACHE_VERSION` 125 · prompts / locked v3 schema unchanged · `frontend/src` unchanged.
- **Model requests:** 0.

## 0. Verdict

**`ROUTE_D_PREVIEW_VERIFIED`** — Codex's preview wiring recovered without loss and committed as found; two takeover
defects and the review's findings fixed from RED tests; independent review PASS in two rounds (0 blocking); authoritative
T3 `FULL_PRODUCT_GATE_PASS` on a clean detached checkout of `eb3ca406` (§6.2). Not merged, not pushed; Route D product
enablement and GO LIVE remain NO-GO.

## 1. Forensic takeover (before any edit)

- Worktree `.superpowers/worktrees/hybrid-route-d-preview-wiring`, HEAD `6592306d`, no commits; 8 uncommitted files
  (4 modified, 4 untracked), last write 09:28:01. No python/pytest/reviewer process; `codex.exe` was only the VS Code
  app-server. No other writer: mtimes unchanged across the takeover window.
- Snapshot (zero-loss, refuses overwrite): `.superpowers/takeover-route-d-preview-20261018/` — the 8 files, the
  tracked-file patch, `git status`, Codex's 7 logs, `MANIFEST.sha256` (18 entries; manifest SHA-256 `26c0e6db…`).
- Codex logs (`.superpowers/preview-verification/` in the worktree, gitignored): `baseline.log` 09:21 (131 passed, 4
  ERROR = `PermissionError` creating `pytest-of-Bunny` in the Codex sandbox — not reproducible outside it),
  endpoint RED 09:22 → GREEN 09:23 (1 failing), safety RED 09:25 → GREEN 09:25 (47 passed), boundary RED 09:26,
  `regression.log` 09:27:27 (187 passed, 1 failed = candidate hash pin, refreeze pending). Both test files were edited
  at 09:28:01, AFTER the last regression: no Codex run covers the final state.
- Independent review before takeover: **UNKNOWN / not completed** — no reviewer output, receipt or process exists.
- Codex's state committed byte for byte as `902730b9` (staged from the snapshot blobs), before any takeover change.

## 2. Reconstructed status of the requested items

| # | Item | Status at takeover | After takeover |
|---|---|---|---|
| 1 | RoutePolicy supports D preview | DONE_UNVERIFIED | DONE_VERIFIED |
| 2 | Default OFF | DONE_UNVERIFIED (env `HYBRID_ROUTE_D_PREVIEW=1` required; `preview=True` only from the endpoint/diagnostics) | DONE_VERIFIED |
| 3 | Fingerprint = Registry + Planner + Engine + extraction surface (+ adapter/envelope) | DONE_UNVERIFIED | DONE_VERIFIED |
| 4 | `KetQuaTuyen` → envelope adapter | DONE_UNVERIFIED (versioned preview representation around `compile_semantic_program_to_envelope`) | DONE_VERIFIED + identity re-check |
| 5 | `goal_checks` / `proof_status` / `can_present_as_proven` preserved | DONE_UNVERIFIED | DONE_VERIFIED |
| 6 | `length_unit` through the envelope | DONE_UNVERIFIED (scene + metadata, consistency enforced) | DONE_VERIFIED |
| 7 | Endpoint guarded by env/config | PARTIAL — gates correct, but FastAPI validated the body first (422 + schema to disabled/unauthorized callers) | fixed |
| 8 | No production cache read/write | DONE_UNVERIFIED | DONE_VERIFIED |
| 9 | `/api/analyze` still LLM_ONLY | DONE_UNVERIFIED (byte-hash parity vs pre-wiring baseline) | DONE_VERIFIED |
| 10 | `runtime_identity` shows Route D | DONE_UNVERIFIED | DONE_VERIFIED |
| 11 | RED/GREEN tests | PARTIAL — written and run; last edits not re-run | re-run, extended |
| 12 | Independent review | NOT_COMPLETED | §6.1 |

Codex's "four fail-closed situations" match the `boundary-red.log` additions: `answer_unit`, `duplicate_object`,
`surface` (extraction fingerprint mismatch) and `metric_mismatch`. All four reproduce RED → GREEN.

## 3. What the takeover changed (`af4bcf47`, RED first)

1. **Identity change mid-request was served under the old identity.** The snapshot names Registry/Planner/Engine,
   but nothing re-checked them after execution; Codex's own test asserted serving continues when `REGISTRY_VERSION`
   changes mid-request. RED: 3/3 served `ok`. Fix: `adapt_result` refuses `PREVIEW_IDENTITY_CHANGED` when the current
   `preview_identity` or the planner version the result records differs from the snapshot (a refusal before planning
   keeps its own code). The env-flip test keeps its env/contract flips, still served under the snapshot.
2. **Gate after body validation.** RED: 6/6 (off/unauthorized × extra field / wrong field / non-JSON) answered 422
   listing `problem_text`. Fix: async handler; 404 / 403 first, then `HybridPreviewBody.model_validate_json`
   (`PREVIEW_BODY_INVALID`), Route D work in `run_in_threadpool`.
3. **New locks (already correct):** five malformed/truncated/refused provider responses keep their code
   (`RESPONSE_TRUNCATED`, `JSON_INVALID`, `MALFORMED_RESPONSE_PART`, `NO_CANDIDATE`, `PROVIDER_REFUSED`) and serve
   nothing; `ALLOW_LIVE_AI=1` + key present still has no transport (sockets blocked in the test); zero lengths keep
   `NON_POSITIVE_LENGTH` with a filled Vietnamese message.

### 3.1 Review-driven fixes (`93390f58`, RED first; test-only guard follow-up in this commit)

| Review finding | Fix |
|---|---|
| 1 `/api/health` (Docker healthcheck every 30 s, frontend) loaded Route D even with the preview OFF | OFF ⇒ `hybrid_route_d_preview = {"enabled": false}`, no Route D import (subprocess test); ON reports `token_configured` |
| 2 refusals echoed model-supplied quotes (planner calls/trace/auxiliary) | refusal keeps only planner `version` + goal/negated observations |
| 3 four checks removable with no test failing | fault cases `proof_status`, `negated_proven`, `dependency_order`, `kernel_check`, `result_metric`; identity changes of extraction surface and adapter version; the reviewer's mutations now each turn their case red |
| 4 proof-text backstop narrow | NFC + format characters stripped, hyphen variants, `chứng minh được/xong`, `điều phải chứng minh`, `đpcm` |
| 5 declared preview edges could hide a module-level import | guard requires each import resolving to `app.ai.hybrid_preview` (all four spellings) inside a function body |
| 6 CORS `*` + loopback: a browser page could reach the gate | any request with an `Origin` header ⇒ 403 |
| 7 bare `except` hid adapter bugs | exception type logged server-side; HTTP unchanged |
| 8 NITs | real Route D grounding codes for the source message; served result without planner version refused |

## 4. Safety properties (endpoint level)

| Property | Evidence |
|---|---|
| OFF ⇒ 404 before any Route D import, no network | subprocess test: `app.ai.hybrid_preview` / `fact_extraction` / `function_route` / `geometry_functions` absent from `sys.modules` |
| Operator-only: env + server token ≥ 32 chars + matching header + loopback peer; `X-Forwarded-For` ignored | 4 parametrised denials |
| Not discoverable by schema: OpenAPI excludes it; disabled/unauthorized callers get no 422 | `test_diagnostics_…`, `test_gate_answers_before_body_validation` |
| No provider path: fixture data from `app.state` only; clients cannot send facts or flags | `test_api_key_…`, `test_live_flag_…`, `test_clients_cannot_supply_…` |
| No product cache: `_cache_lookup` / `SessionLocal` forbidden in the test; `_policy_identity` raises for a preview policy | `test_preview_on_serves_…`, `test_preview_policy_does_not_change_…` |
| `/api/analyze` LLM_ONLY byte parity with the pre-wiring baseline (full HTTP response SHA-256 `e6695fe6…`), flag on or off | `test_llm_only_byte_parity_against_pre_wiring_baseline` |
| default runtime never loads Route D even with the flag on | `test_default_runtime_never_loads_route_d_even_with_preview_flag_on` + `test_Y_*` |
| one snapshot per request; env / contract flips mid-request do not change it; version change refuses | 3 tests |
| answers equal independent corpus expectations (Fraction), timeline closed, step-math oracle VERIFIED | 10 positive cases |
| grounding / unsupported inputs refuse with expected codes, no scene, no technical id in learner text | 17 negative cases |
| corrupted outputs refuse: non-SPD / mismatched metric, missing / inconsistent unit, proof flag or proof text, broken dependency, duplicate object, changed surface | 9 faults |
| real PlanningContract / engine tampering | `AUXILIARY_RULE_MISMATCH`, `ENGINE_SELF_CHECK_FAILED` |
| goal observations never promoted: `proof_status=UNVERIFIABLE`, `can_present_as_proven=false`, description says observation, not proof | `test_symbolic_unit_and_goal_observation_…` |

## 5. Regression on the first frozen candidate (`af4bcf47`, working tree, before the docs commit)

(Superseded for the final candidate by the authoritative T3, §6.2.)

| Check | Result |
|---|---|
| targeted (preview, guards, cache, integration incl. 174 rows / timeline / metric, API, grounding 72, identity/prompt fingerprints) | 553 passed, 1 failed = candidate hash pin before the freeze |
| full backend after the freeze | 10739 passed, 1 skipped, 2 deselected, 9 xfailed, 1 failed: `test_holdout_readiness::test_bao_cao_da_sinh_va_KHONG_TROI` — its only blocker is "CÂY LÀM VIỆC BẨN" (these uncommitted docs); clean-tree check, decided by the T3 |
| frontend vitest / build | 68 files, 1079 passed / PASS |
| `CACHE_VERSION` | no bump: default identity unchanged; preview has no cache |

## 6. Verification

### 6.1 Independent review — PASS (two rounds, one reviewer)

The Codex reviewer left no result and no process, so one read-only reviewer (0 live calls, 0 modifications) reviewed
`6592306d..f6ff8a5e`: **PASS, 0 blocking**, 7 non-blocking findings + NITs (§3.1). The same reviewer re-reviewed the
code that changed afterwards (`93390f58`, `dc8e25ba`): **PASS**, all nine items fixed (its mutations re-run), no new
defect; residuals: the laziness guard checked one import spelling (fixed in this commit, test only) and U+2212 between
the two syllables passes the proof-text backstop (§7).

### 6.2 Authoritative T3 — `FULL_PRODUCT_GATE_PASS`

Clean detached checkout of `eb3ca406` (receipt `verification/authoritative-t3.json`, log SHA-256 `ecb255c7…`): backend
10757 passed, 1 skipped, 2 deselected, 9 xfailed (the same strict preregistered set as before; none added) · frontend
68 files / 1079 passed · typecheck + build PASS · demo replay 5/5 · crash surface 6/6, 0 uncaught · candidate `--verify`
MATCH (111 files, `4c1b9a27…`). The `test_holdout_readiness` failure of §5 (dirty tree) does not occur on the clean
checkout. The detached checkout was removed afterwards (junction first).

## 7. Remaining limits

- Offline preview only: no live provider path exists, by design; Route D is not served by `/api/analyze`; no Route D
  product cache; the frontend does not consume `route_d` (F1–F4 of `hybrid-pre-main-hardening/frontend-handoff.md`
  remain).
- Loopback peer means the preview is unusable behind the Docker bridge / a reverse proxy (fails closed with 403). The
  loopback check assumes uvicorn is not started with `--forwarded-allow-ips="*"` (nowhere in the repo); the token
  gate holds regardless. Browser-based operator tools are refused (Origin header).
- With the flag ON, `/api/health` and `/api/diagnostics/runtime` import Route D metadata modules (never execute
  extraction or planning); OFF they import nothing from Route D.
- Proof-text backstop is defence in depth over deterministic engine text: U+2212 (minus sign) between "chứng" and "minh"
  is not matched (re-review NIT, not fixed to avoid another product cycle for text no producer emits).
- The preview exposes its existence when OFF (404 with `PREVIEW_DISABLED`), but nothing else, and cannot be enabled
  by a request.
- Refusal envelopes use `failure_category = capability_gap` for every code (the machine `reason_code` is exact).
