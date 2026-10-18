# Hybrid preview contract hardening (`hybrid-preview-contract-hardening`)

- **Owner approval:** `GO_HYBRID_PREVIEW_CONTRACT_HARDENING` (2026-10-18) · offline · 0 model calls
- **Branch:** `research/hybrid-preview-contract-hardening` from `main = origin/main = 65d6ee97`
- **Commits:** `caf21513` product · `2a832ae2` candidate freeze (`53ea8830…`, 111 files, frozen in a clean detached
  worktree) · `0a199aa5` fixtures + lock · docs commit(s) after this report
- **Not done, by scope:** merge/push, live calls, Hybrid enablement, any `frontend/src` edit, any cleanup

## 0. Verdict

See §6 (set from the independent review and the authoritative T3).

## 1. P0 — preflight

- `main = origin/main = ls-remote = 65d6ee97`.
- Processes: VS Code Codex app-server, two Stitch MCP proxies, this session. No repo writer, no Python/Node test run.
- The active Scene3D worktree `scene3d-plane-grid-camera` (10 modified, 63 untracked) was not touched. Neither were
  research branches with unique commits, the untracked GO MAIN packages on `main`, the orphan folders or `algosim.db`.
- New worktree `.superpowers/worktrees/hybrid-preview-contract-hardening`. Baseline `test_hybrid_preview_api.py`: 89
  passed.

## 2. P1 — refusal classification

**Defect.** All 23 representative refusals answered `failure_category = capability_gap` with no `refusal_cause` (probe
before the fix, every row of the RED test).

**Fix** (`backend/app/ai/hybrid_preview.py::classify_refusal`, table `_NHOM`). It uses the existing vocabularies only:
- `failure_category` from the values the product already emits and the frontend already labels
  (`SEMANTIC_FAILURE_CATEGORY`, `pipeline._that_bai_hinh_hoc`, `NHAN_LOAI_VAN_DE`);
- `refusal_cause` from `refusal_cause.py`.

No new code; `reason_code` is unchanged.

| group | category | cause | through the endpoint (RED → GREEN) |
|---|---|---|---|
| capability gap | `capability_gap` / `out_of_scope` | UNKNOWN | `UNSUPPORTED_CAPABILITY` (H08), `CONDITIONAL_CLAUSE`, `NEGATED_CLAUSE` from the planner |
| missing / ambiguous data | `insufficient_specification` | UNKNOWN | `MISSING_DIMENSION` (H10), `UNDERDETERMINED_POINT` (H06), `AMBIGUOUS_FACT` |
| contradictory / degenerate data | `geometry_generation_failed` | SOURCE only for `NON_POSITIVE_LENGTH`, else UNKNOWN | `INCONSISTENT_FACTS` (H09), `COLLINEAR_POINTS`, zero height |
| source not verified | `verification_gap` | UNKNOWN | `SOURCE_OBJECT_MISMATCH`, `GOAL_CLAUSE_NOT_PREMISE`, `REQUEST_NOT_ANSWERED` |
| result / certificate not verified | `verification_gap` | UNKNOWN | `PREVIEW_RESULT_INVALID`, `METRIC_NOT_EUCLIDEAN` (adapter), `ENGINE_SELF_CHECK_FAILED` |
| cannot conclude | `verification_gap` | UNKNOWN | `FIGURE_NOT_UNIQUE` (H05), `NEGATED_CLAUSE` with an observation (H13), `PROOF_UNVERIFIABLE` (committed proof-only derivation) |
| extraction / provider | `geometry_generation_failed` | UNKNOWN | `FACT_INCOMPLETE`, `JSON_INVALID` |
| integrity / identity | `geometry_generation_failed` | UNKNOWN | `PREVIEW_IDENTITY_CHANGED`, `PREVIEW_PROOF_STATUS_INVALID`, `PREVIEW_SURFACE_CHANGED` |
| unknown code | `geometry_generation_failed` | UNKNOWN | never `capability_gap` |

Two codes have two meanings, and they are told apart by structure, not text:
- `NEGATED_CLAUSE` means "cannot conclude" when it carries an observed negated check, and "capability" from the planner.
- `METRIC_NOT_EUCLIDEAN` means a tampered scene when the adapter raises it, and contradictory lengths from the engine.

**Learner text.** Each row is checked for:
- Vietnamese with diacritics, equal to `reason`;
- no `_`, no `{`, no `reason_code`, no exception/trace word;
- no model quote longer than 12 characters.

The refusal envelope has exactly six keys, and planner metadata on a refusal stays limited to
`version / goal_checks / negated_checks`.

**Coverage lock.** `test_every_literal_route_d_refusal_code_is_classified` scans the Route D modules (both quote styles)
and the polyhedral kernel `ERR_*` constants. On its first run it caught three unclassified codes:
`LINE_CONTAINED_IN_PLANE`, `RESULT_BINDING_UNVERIFIED`, and `GEOMETRY_CONSTRUCTION` (a `semantic_kind`, now listed as
not a refusal). `PREVIEW_DISABLED` was added to the adapter table.

## 3. P2 — proof-text backstop

- **RED:** U+2212, U+2796, U+FE63, U+FF0D, U+2E3A, U+02D7 and fullwidth letters between "chứng" and "minh" were served.
- **GREEN:** matching runs on a detection copy (`_ban_do`: NFKC, `Cf` dropped, every `Pd` dash and the minus signs folded
  to `-`, casefold). NBSP and soft hyphen are also covered.
- **Valid mathematical text is served byte-identical:** "AB − CD", "Cần chứng minh rằng SC ⊥ BD; hình chỉ minh họa",
  "chứng tỏ", "x² − 1".
- **Not regex-dependent:** with the regex disabled, a promoted `proof_status` is still refused
  (`PREVIEW_PROOF_STATUS_INVALID`). All 18 served inputs (10 corpus positives + 8 served holdout cases) keep every observation
  `UNVERIFIABLE` / `false` and the fixed description.
- **Residual (by design):** spellings without diacritics and cross-script homoglyphs. Folding diacritics would match
  "chúng mình" and refuse valid narration.

## 4. Fault injection (each must turn a test red)

Tool: `verification/fault_injection_plugin.py`, which patches the module at session start; no product edit.

| mutation | failures in `test_hybrid_preview_contract.py` |
|---|---|
| original defect: every group `capability_gap` | 31 |
| no minus folding | 4 |
| INTEGRITY → `capability_gap` | 4 |
| drop the adapter-origin flag | 1 |
| ignore the negated observation | 1 |
| drop `LINE_CONTAINED_IN_PLANE` from the table | 1 |

Fixture verifier: a copy with one response field changed and its manifest hash recomputed
(`verification/fixture_tamper.py`) makes `--verify` exit 1 with `refusal-integrity-identity: response differs`.

## 5. P3 — offline envelope fixtures

`backend/scripts/export_hybrid_preview_fixtures.py --out fixtures/` was run once, at `2a832ae2`, with `backend/app`
clean.
- Every fixture is the real endpoint response: in-process, loopback peer, an ephemeral token never written, the socket
  layer blocked, `ALLOW_LIVE_AI=0`, empty API key.
- Inputs come only from committed sources: the contract-driven-goal-composition corpus, the hybrid holdout cases, the
  benchmark section problems, the committed zero-length and proof-only derivations, and the declared faults of the
  contract test.
- Two generations gave identical response hashes. Total about 690 KB.

| kind | n | covers (read from the response) |
|---|---|---|
| served | 12 | multi-goal (5), symbolic `length_unit` (7), goal observation (H07), auxiliary points, `section`, `line3` |
| refusal | 23 | every group of §2; 6 carry a declared injected fault (tampered result / identity / surface / proof status) |
| gate | 4 | 404 disabled, 403 forbidden, 422 body invalid, 503 fixture missing |

Each fixture carries:
- `source` (origin, problem text, provider body, `input_sha256`);
- `injection`;
- `producer` (commit `2a832ae2`, product commit `caf21513`, `measured_system_hash` `53ea8830…` / 111 files,
  adapter/envelope versions);
- `expected`, `response`, `response_sha256`.

`manifest.json` lists the file hashes. Locks (`backend/tests/test_hybrid_preview_fixtures.py`):
- `--verify` regenerates the bundle identically;
- `--out` refuses to overwrite;
- file hashes match the manifest;
- no secret string;
- the inventory covers the contract;
- no served fixture presents an observation as a proof.

## 6. Independent review and authoritative T3

PENDING.

## 7. P4 — frontend contract

`docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md` covers:
- the envelope and `route_d` structure;
- **observation on the constructed figure ≠ general proof** (MUST rules and wording);
- `length_unit` / `display_scale`;
- source provenance;
- the refusal table and what may be shown to a learner;
- backward compatibility;
- F1–F5 acceptance.

New finding, F5: the frontend has no title/hint branch for `verification_gap`, so it would show "NGOÀI DANH MỤC MÔ
PHỎNG" (`ISSUE-ARCH-SCENE3D-VERIFICATION-GAP-PRESENTATION`). No `frontend/src` change and no browser caller.

## 8. P5 — regression (`ALLOW_LIVE_AI=0`, empty API key; `verification/p5-regression.log`)

| group | result |
|---|---|
| preview API: OFF by default, operator gate, no provider, no product cache, LLM_ONLY byte parity, adapter identity | 89 passed |
| preview contract (P1/P2) | 59 passed |
| fixtures | 5 passed |
| 174 historical cases | 1 passed (the 174-case regression test) |
| Hybrid backend integration (incl. versions, surfaces, live tree = frozen candidate) | 52 passed |
| source grounding (closure, reliability, review, safety) | 130 passed, 1 xfailed (preregistered) |
| correctness / negative cases (`test_hybrid_safety_readiness`) | 23 passed |
| default route never loads Route D (`test_structured_geometry_relations`) | 71 passed |
| cache isolation | 8 passed |
| existing mathematical oracle (independence, section witness) | 35 passed |
| envelope schema compatibility (`test_schema_sync`), learner messages | 19 passed |
| candidate freeze | 26 passed |

The pre-commit full backend run on the dirty tree showed 10806 passed and 12 failures. All 12 were freeze drift and
dirty-tree prechecks (cleared by `2a832ae2`, re-checked above); none was functional. The authoritative result is the T3
of §6.

**Model surface:** unchanged. No prompt, schema, grammar card or capability table was edited, and the extraction surface
fingerprint is pinned in `test_hybrid_backend_integration`.

**`CACHE_VERSION`:** 125, not bumped. The preview never reads or writes the cache, and `/api/analyze` output is
byte-identical (parity test).

## 9. Remaining limits

- The preview is offline and operator-only. Route D is not in `/api/analyze`, there is no provider transport, and the
  frontend consumes nothing (F1–F5 open).
- The groups are a server-side table. Several share a category (for example, integrity and contradictory data are both
  `geometry_generation_failed`); `reason_code` and `learner_reason` tell them apart.
- `refusal_cause` is `SOURCE` only where a structured fact proves it (`NON_POSITIVE_LENGTH`). Other data refusals stay
  `UNKNOWN` rather than blame the problem.
- The fixtures are bound to `hybrid-route-d-preview/1`. Any change to served output makes the lock red, so a new
  contract needs a new run.
- Historical cache mode: UNKNOWN (`ISSUE-OPS-CACHE-HISTORICAL-MODE-UNKNOWN`).
