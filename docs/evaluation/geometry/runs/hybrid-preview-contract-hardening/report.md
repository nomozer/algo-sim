# Hybrid preview contract hardening (`hybrid-preview-contract-hardening`)

- **Owner approval:** `GO_HYBRID_PREVIEW_CONTRACT_HARDENING` (2026-10-18) · offline · 0 model calls
- **Branch:** `research/hybrid-preview-contract-hardening` from `main = origin/main = 65d6ee97`
- **Commits:**

  | commit | what |
  |---|---|
  | `caf21513` | product, round 1 |
  | `2a832ae2` | freeze, round 1 |
  | `0a199aa5` | first fixture bundle, now superseded |
  | `413df6c4` | docs, round 1 |
  | `bce21d8b` | product, review fixes, **current product commit** |
  | `f5f483bf` | refreeze: `1b7a6713…`, 111 files, frozen in a clean detached worktree |
  | `aae168e6` | adapter /2 fixtures and fault-injection log |
  | after this report | docs |

- **Not done, by scope:** merge/push, live calls, Hybrid enablement, any `frontend/src` edit, any cleanup

## 0. Verdict

See §6 (set from the second review round and the authoritative T3).

## 1. P0 — preflight

- `main = origin/main = ls-remote = 65d6ee97`.
- Processes: VS Code Codex app-server, two Stitch MCP proxies, this session. No repo writer, no Python/Node test run.
- The active Scene3D worktree `scene3d-plane-grid-camera` (10 modified, 63 untracked) was not touched. Neither were
  research branches with unique commits, the untracked GO MAIN packages on `main`, the orphan folders or `algosim.db`.
- New worktree `.superpowers/worktrees/hybrid-preview-contract-hardening`. Baseline `test_hybrid_preview_api.py`: 89
  passed.

## 2. P1 — refusal classification

**Defect.** Before the fix, every representative refusal answered `failure_category = capability_gap` with no
`refusal_cause` (23/23 in the RED run).

**Fix** (`backend/app/ai/hybrid_preview.py::classify_refusal`, table `_NHOM`). It uses the existing vocabularies only:
- `failure_category` from the values the product already emits and the frontend already labels;
- `refusal_cause` from `refusal_cause.py`.

No new code; `reason_code` is unchanged. `ADAPTER_VERSION` moves to `hybrid-preview-adapter/2` because the refusal
envelope changed.

| group | category | cause | through the endpoint |
|---|---|---|---|
| capability gap | `capability_gap` | UNKNOWN | `UNSUPPORTED_CAPABILITY` (H08), `CONDITIONAL_CLAUSE`, `NEGATED_CLAUSE` from the planner, `OUT_OF_SCOPE` = extraction escape (bundle B25) |
| missing / ambiguous data | `insufficient_specification` | UNKNOWN | `MISSING_DIMENSION` (H10), `UNDERDETERMINED_POINT` (H06), `AMBIGUOUS_FACT` |
| contradictory / degenerate data | `geometry_generation_failed` | SOURCE only when the server's reader finds a length ≤ 0 in the premises | `INCONSISTENT_FACTS` (H09), `COLLINEAR_POINTS`, zero height in the text (SOURCE), zero only in the extraction (UNKNOWN) |
| source not verified | `verification_gap` | UNKNOWN | `SOURCE_OBJECT_MISMATCH`, `GOAL_CLAUSE_NOT_PREMISE`, `REQUEST_NOT_ANSWERED` |
| result / certificate not verified (incl. interpreter/kernel construction failures) | `verification_gap` | UNKNOWN | `PREVIEW_RESULT_INVALID`, `METRIC_NOT_EUCLIDEAN` (adapter), `ENGINE_SELF_CHECK_FAILED` |
| cannot conclude | `verification_gap` | UNKNOWN | `FIGURE_NOT_UNIQUE` (H05), `NEGATED_CLAUSE` with an observation (H13), `PROOF_UNVERIFIABLE` (committed proof-only derivation) |
| extraction / provider | `geometry_generation_failed` | UNKNOWN | `FACT_INCOMPLETE`, `JSON_INVALID` |
| integrity / identity | `geometry_generation_failed` | UNKNOWN | `PREVIEW_IDENTITY_CHANGED`, `PREVIEW_PROOF_STATUS_INVALID`, `PREVIEW_SURFACE_CHANGED` |
| unknown code | `geometry_generation_failed` | UNKNOWN | never `capability_gap` |

Three codes are disambiguated from structure, never from text:
- `NEGATED_CLAUSE`: an observation present means "cannot conclude"; from the planner it means "capability".
- `METRIC_NOT_EUCLIDEAN`: raised by the adapter it means a tampered scene; from the engine, contradictory lengths.
- `NON_POSITIVE_LENGTH`: SOURCE only via `refusal_cause.do_dai_de_ghi_khong_duong(problem_text)`.

**Learner text.** Each of the 25 rows is checked for:
- Vietnamese with diacritics, equal to `reason`;
- no `_`, no `{`, no `reason_code`, no exception/trace word;
- no model quote longer than 12 characters;
- unless the cause is SOURCE, no "Đề bài cho" / "kiểm tra lại" / "môn học khác".

The refusal envelope has exactly six keys.

**Coverage lock.** The source scan covers the Route D modules (both quote styles) and the polyhedral kernel `ERR_*`
constants. Its first run caught three gaps: `LINE_CONTAINED_IN_PLANE`, `RESULT_BINDING_UNVERIFIED`, and
`GEOMETRY_CONSTRUCTION` (a `semantic_kind`, now listed as not a refusal).

## 3. P2 — proof-text backstop

- **RED:** U+2212, U+2796, U+FE63, U+FF0D, U+2E3A, U+02D7, fullwidth letters, a stray combining mark (U+034F) and `_`
  between "chứng" and "minh" were served.
- **GREEN:** matching runs on a detection copy (`_ban_do`: NFKC; `Cf` and uncomposed `Mn` dropped; every `Pd` dash and
  the minus signs folded; casefold). The served text is byte-identical. Four valid mathematical titles stay served
  unchanged: "AB − CD", "Cần chứng minh rằng SC ⊥ BD; hình chỉ minh họa", "chứng tỏ", "x² − 1".
- **Not regex-dependent:** with the regex disabled, a promoted `proof_status` is still refused. All 18 served inputs
  (10 corpus positives + 8 served holdout cases) keep every observation `UNVERIFIABLE` / `false`.
- **Residual (by design):** spellings without diacritics, cross-script homoglyphs, "Đ.P.C.M". The old phrase rule also
  refuses "Cần chứng minh được rằng …" (a safe-side false refusal, not changed).

## 4. Fault injection (`verification/fault_injection_plugin.py`, `verification/fault-injection.log`)

| mutation | failures in `test_hybrid_preview_contract.py` (64 tests) |
|---|---|
| original defect: every group `capability_gap` | 34 |
| no minus folding | 4 |
| INTEGRITY → `capability_gap` | 4 |
| drop the adapter-origin flag | 1 |
| ignore the negated observation | 1 |
| drop `LINE_CONTAINED_IN_PLANE` from the table | 1 |
| review finding 2: `NON_POSITIVE_LENGTH` always SOURCE | 1 |
| review finding 1: escape `OUT_OF_SCOPE` as "another subject" | 1 |

Fixture verifier: a copy with one response field changed and its manifest hash recomputed
(`verification/fixture_tamper.py`) makes `--verify` exit 1 with `refusal-integrity-identity: response differs`. This was
checked on both bundles.

## 5. P3 — offline envelope fixtures (`fixtures-adapter-2/`, the contract bundle)

`backend/scripts/export_hybrid_preview_fixtures.py --out` was run once, at `f5f483bf`, with `backend/app` and all inputs
clean.
- Every fixture is the real endpoint response: in-process, loopback peer, an ephemeral token never written, the socket
  layer blocked, `ALLOW_LIVE_AI=0`, empty API key.
- Inputs come only from committed sources:
  - the contract-driven-goal-composition corpus and its 174-row bundle (B25);
  - the hybrid holdout cases;
  - the benchmark section problems;
  - the committed zero-length and proof-only derivations, plus the review's zero-not-in-text derivation of the same
    helper;
  - the declared faults of the contract test.
- Two generations gave identical response hashes.

| kind | n | covers (read from the response) |
|---|---|---|
| served | 12 | multi-goal (5), symbolic `length_unit` (7), goal observation (H07), auxiliary points, `section`, `line3` |
| refusal | 25 | every group of §2; 6 carry a declared injected fault (tampered result / identity / surface / proof status) |
| gate | 4 | 404 disabled, 403 forbidden, 422 body invalid, 503 fixture missing |

Each fixture carries:
- `source` (+ `input_sha256`);
- `injection`;
- `producer` (commit `f5f483bf`, product `bce21d8b`, `measured_system_hash` `1b7a6713…` / 111 files, adapter `/2`,
  envelope `/1`, both dirty flags false);
- `expected`, `response`, `response_sha256`.

The lock (`test_hybrid_preview_fixtures.py`) checks:
- regeneration is identical;
- `--out` refuses to overwrite;
- file hashes match the manifest;
- no secret;
- the inventory covers the contract;
- no observation is presented as a proof.

The first bundle `fixtures/` (39 files, `0a199aa5`) is superseded. It predates the review fixes and carries the adapter
`/1` label of the pre-classification adapter. It is kept unchanged; nothing points to it.

## 6. Independent review and authoritative T3

**Round 1** (read-only general-purpose agent, on `65d6ee97..413df6c4`): **FAIL**, two blocking findings. All findings
were verified against the code before fixing.

| # | finding | disposition |
|---|---|---|
| 1 BLOCKING | Route D `OUT_OF_SCOPE` (extraction escape on a geometry problem) → `out_of_scope` → "Bài này thuộc môn học khác" | FIXED `bce21d8b`: CAPABILITY; row `capability-escape-unsupported` (B25); mutation test |
| 2 BLOCKING | `NON_POSITIVE_LENGTH` → SOURCE, justified by "passed the source gate", but `doc_so` refuses 0 before the quote check (text "3", extraction "0" still blamed the problem) | FIXED `bce21d8b`: SOURCE only via the server's reader of `problem_text`; row `invalid-zero-not-in-text`; mutation test |
| 3 | INTEGRITY sentence false for `ENGINE_EXECUTION_FAILED` / kernel construction failures | FIXED: moved to RESULT_UNVERIFIED; dedicated test |
| 4 | contract §7 overclaimed refusal-cause hints for `insufficient_specification` | FIXED in the contract; new F6 / `ISSUE-ARCH-SCENE3D-INSUFFICIENT-SPEC-HINT` |
| 5 NIT | `Mn` / `_` slipped the backstop | FIXED; "Đ.P.C.M" and the old false refusal recorded as residual (§3) |
| 6 NIT | exporter checked only `backend/app` for dirtiness | FIXED: `inputs_dirty` (`INPUT_PATHS`) |

Also found while fixing: `caf21513` changed the refusal envelope without bumping `ADAPTER_VERSION`. It is now `/2`.

RED for the fixes: the updated test file run against the unfixed product (`413df6c4`, throwaway detached worktree)
failed exactly the 5 new checks.

**Round 2** (same reviewer, on `413df6c4..1839abe3`): **PASS_WITH_FINDINGS**, 0 blocking. All six round-1 findings were
confirmed fixed; the reviewer re-ran its probes and the endpoint rows, and the regression set gave 349 passed with freeze
MATCH.

| # | finding | disposition |
|---|---|---|
| 1 NON_BLOCKING | the shared length reader (`do_dai_trong_de`) reads `XY = 0` in vector or dot notation as a zero premise, so a mis-extracted zero on such a valid problem is still SOURCE | RECORDED: `ISSUE-ARCH-SOURCE-LENGTH-READER-VECTOR-ZERO`, contract §6, §9 below. The reader is default-route product code, so fixing it is a separate wave |
| 2 NIT | `bce21d8b` and `f5f483bf` fail collection (`test_hybrid_preview_fixtures.py` reads a bundle first committed in `aae168e6`) | NOTED: T3 runs on the final docs HEAD (same product tree `1b7a6713…`), not on the freeze commit |
| 3 NIT | stale `_ban_do` description in CODE_INDEX | FIXED |
| 4 NIT | "exactly six keys" needs an adapter qualifier | FIXED in contract §6 (six keys from adapter `/2`; `/1` had five; absent `refusal_cause` ⇒ `UNKNOWN`) |

**Authoritative T3:** PENDING.

## 7. P4 — frontend contract

`docs/architecture/HYBRID_PREVIEW_FRONTEND_CONTRACT.md` covers:
- the envelope and `route_d` structure;
- **observation on the constructed figure ≠ general proof** (MUST rules and wording);
- `length_unit` / `display_scale`;
- source provenance;
- the refusal table and what may be shown to a learner;
- backward compatibility;
- F1–F6 acceptance.

New frontend findings:
- F5: the frontend has no title/hint branch for `verification_gap`.
- F6: the hint for `insufficient_specification` ignores `refusal_cause`.

No `frontend/src` change and no browser caller.

## 8. P5 — regression (`ALLOW_LIVE_AI=0`, empty API key; `verification/p5-regression.log`, HEAD `aae168e6`)

| group | result |
|---|---|
| preview API: OFF by default, operator gate, no provider, no product cache, LLM_ONLY byte parity, adapter identity | 89 passed |
| preview contract (P1/P2) | 64 passed |
| fixtures | 5 passed |
| 174 historical cases | 1 passed (the 174-case regression test) |
| Hybrid backend integration (versions, surfaces, live tree = frozen candidate) | 52 passed |
| source grounding (closure, reliability, review, safety) | 130 passed, 1 xfailed (preregistered) |
| correctness / negative cases | 23 passed |
| default route never loads Route D | 71 passed |
| cache isolation | 8 passed |
| existing mathematical oracle (independence, section witness) | 35 passed |
| envelope schema compatibility, learner messages | 19 passed |
| candidate freeze | 26 passed |

**Model surface:** unchanged (no prompt, schema, grammar card or capability table edited).

**`CACHE_VERSION`:** 125, not bumped. The preview never reads or writes the cache, and `/api/analyze` is byte-identical.

## 9. Remaining limits

- The preview is offline and operator-only. Route D is not in `/api/analyze`, there is no provider transport, and the
  frontend consumes nothing (F1–F6 open).
- The groups are a server-side table, and several share a category; `reason_code` and `learner_reason` tell them apart.
- `refusal_cause` is SOURCE only where the server reads the cause in the text: today only `NON_POSITIVE_LENGTH` through
  `do_dai_de_ghi_khong_duong`. Other data refusals stay UNKNOWN rather than blame the problem. That reader misreads
  vector or dot notation (`GA + GB + GC = 0`) as a zero length. A mis-extracted zero on such a problem is still blamed
  on the text (`ISSUE-ARCH-SOURCE-LENGTH-READER-VECTOR-ZERO`; shared product reader, separate wave).
- The source-scan lock covers literal codes and the scanned kernel files. A new pass-through of codes from an unscanned
  module would not be caught (review NIT).
- The fixtures are bound to adapter `/2`. Any change in served output makes the lock red, so a new contract needs a new
  bundle.
- Historical cache mode: UNKNOWN (`ISSUE-OPS-CACHE-HISTORICAL-MODE-UNKNOWN`).
