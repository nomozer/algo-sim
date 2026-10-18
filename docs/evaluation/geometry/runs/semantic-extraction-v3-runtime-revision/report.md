# Semantic Extraction v3 — Runtime Revision & Offline Evaluation Report

Status: **OFFLINE_COMPLETE_AUTHORITATIVE_T3_PASS_AWAITING_LIVE_PILOT_GO** (`0` live model calls).

This run (`docs/evaluation/geometry/runs/semantic-extraction-v3-runtime-revision/`) executes the owner-approved
`GO_RUNTIME_RECOVERY_AND_OFFLINE_REVISION` scope from parent checkpoint `7168d26963011433889dc907492df87ac62140f7`
above the original frozen protocol lock `5c58774dbc57b3416337d97dab7db8ee1932894b`. The parent run directory
`docs/evaluation/geometry/runs/semantic-extraction-schema-contract/` and parent worktree
`.superpowers/worktrees/semantic-extraction-v3` remain byte-for-byte unchanged (`verification/parent-preservation.json`).

## 1. Provenance & Chain of Custody (Claude → Codex → Claude → Codex → Gemini)

- **Original lock (`5c58774dbc57b3416337d97dab7db8ee1932894b`):** Frozen protocol `f97af99e…` and product candidate
  `1ff71da7…` on `research/semantic-extraction-v3`. Offline batch task `bufr6nkj1` stalled indefinitely in `_vung_hoi`
  on held-out case `h07` due to catastrophic regex backtracking in `_SAU_HOP_LE` combined with whole-corpus routing
  before `PILOT`/`LOCKED` filtering.
- **First takeover diagnostic (`7168d26963011433889dc907492df87ac62140f7`):** Preserved the stalled attempt without
  killing or duplicating it, proved the root causes, and stopped at `WAITING_OWNER_PROTOCOL_DECISION`.
- **Owner limited approval (`GO_RUNTIME_RECOVERY_AND_OFFLINE_REVISION`):** Authorized stopping only the verified
  `bufr6nkj1` process tree, fixing `_SAU_HOP_LE` backtracking, isolating `PILOT`/`LOCKED` splits before routing,
  creating a separately identified protocol revision, and executing the 8 offline invocations. Excluded `GO LIVE` and
  `GO INTEGRATION`.
- **Codex runtime revision (`283813b2` → `4fdb6308`) & Gemini takeover (`da5b407d` → `2b955ead` → `04b0db37`):**
  1. Verified and terminated stalled task tree `bufr6nkj1` (`5684 → 1304 → 10692 → 21180 → 16508`, plus `22304`) with
     archived log (`08ac45c04abf3617ee722c0483cb1f27d1440202385015e85794cac27903378b`) and `0` surviving processes
     (`recovery/termination.json`).
  2. Replaced `[\s,;:]+` with possessive `[\s,;:]++` in `_SAU_HOP_LE` (`backend/app/simulation/geometry_functions/registry.py`,
     commit `283813b2`), preserving the exact accepted language and match spans while eliminating $O(2^N)$ separator
     backtracking.
  3. Isolated `PILOT` (12 dev) and `LOCKED` (24 held-out) via `selected(data)` in `harness(arm, inp, mode)`
     (`backend/scripts/run_schema_contract_evaluation.py`) before `gold_route(data)` and `evaluate(...)`, while
     preserving full locked artifact hashes in `identity` and preserving registered case order.
  4. Added sequential 8-cell offline launcher `backend/scripts/run_schema_contract_offline.py` with a 120-second
     process-tree watchdog, collision-free per-output-root log paths, fail-closed `WATCHDOG_TERMINATION_FAILED` handling
     when `taskkill /T` returns non-zero even if the parent exited (completed in commit `da5b407d` after Codex hit its
     session limit right after writing the 2 RED tests in `test_schema_contract_offline.py`), and post-run receipt
     verification.
  5. Refroze candidate (`product_sha256 = 6ba9033bfca06d671cd27891e2dad06c7d44f365fed45527123c907d664b65ed`, 110 files,
     product commit `283813b23afd5a3235cd5d944ef30ebbe9d0691a`), recorded `candidate_divergence.json` and independent
     read-only review `review-gates/revision.json` (`PASS`, `0` blocking issues), and locked revision protocol
     `inputs/protocol.json` (`protocol_sha256 = 4e0ec65e3f93f00c5dc41ebd0df20644661c25e56a50bbd87eb848d813c05a5b`,
     commit `2b955ead`).

## 2. Revision Identity vs Frozen Parent Lock

| Component | Parent Lock (`5c58774d`) | Runtime Revision (`2b955ead`) | Status |
|---|---|---|---|
| `corpus.json` SHA-256 | `86a42751d04276f7832f9aa3020ba769f08200d9fe6ee4499b4559e078df85db` | `86a42751d04276f7832f9aa3020ba769f08200d9fe6ee4499b4559e078df85db` | UNCHANGED |
| `gold_facts.json` SHA-256 | `bd449d9f3b7ae618c73b6a5de963d7c34ed59b411dc7c428a03381a65b157bae` | `bd449d9f3b7ae618c73b6a5de963d7c34ed59b411dc7c428a03381a65b157bae` | UNCHANGED |
| Flat surface SHA-256 | `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a` | `485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a` | UNCHANGED |
| v3 surface SHA-256 | `90bf8f039df830062e068adcf1d243643c8ebebfde5b4a5cf9ec340078ea7aab` | `90bf8f039df830062e068adcf1d243643c8ebebfde5b4a5cf9ec340078ea7aab` | UNCHANGED |
| Scorer (`grounded-source-obligations/3`) | `325e7c91dba80c88a360aa0866056b35d13b9e47e65598bed8a8a9ea14cdc0fa` | `325e7c91dba80c88a360aa0866056b35d13b9e47e65598bed8a8a9ea14cdc0fa` | UNCHANGED |
| Base runner / helpers SHA-256 | `9c517d80…` / `f456cf95…` | `9c517d80…` / `f456cf95…` | UNCHANGED |
| `PILOT` / `LOCKED` schedule SHA-256 | `5fa6aecf…` / `c353fc75…` | `5fa6aecf…` / `c353fc75…` | UNCHANGED |
| Product candidate SHA-256 | `1ff71da76d999370897edd3a2dfaf161113e4d24f39dd41cda640ce2aa53dbc7` | `6ba9033bfca06d671cd27891e2dad06c7d44f365fed45527123c907d664b65ed` | REVISED (`registry.py`) |
| Contract runner SHA-256 | `7964113d4f8aea103250c87361aafbc9cdf870789178e60eb9003b518a7b0d39` | `a91f3256ed473656f573ac198b55ad50f65f6f08bfc9c48c56d6e75b5fb6ee80` | REVISED (split-before-route) |
| Offline launcher SHA-256 | None (ad-hoc `-c` loop) | `06d911ff8533afe472b5464fbb73e34c99423f82cf729795d440a912c580f94c` | NEW (`run_schema_contract_offline.py`) |
| Canonical `protocol_sha256` | `f97af99e54aeb27bc18d244577ec01e92f137e164ff362339ba02a23247f9c68` | `4e0ec65e3f93f00c5dc41ebd0df20644661c25e56a50bbd87eb848d813c05a5b` | REVISED |

**Blindness disclosure:** Held-out case `h07` (`split: "heldout"`) had its source text and question-tail span inspected
during runtime stall diagnosis. Consequently, the 24-case `LOCKED` split in this corpus is classified as
`REUSED_DIAGNOSTIC_NOT_FRESH_BLIND`, not fresh implementer-blind held-out evidence.

## 3. Offline Evaluation Matrix (`8/8` Complete, `0` Live Calls)

Executed sequentially at `measurement_commit = 2b955ead0b0a1d2190395fe50627b0fc3f75f6da` via
`backend/scripts/run_schema_contract_offline.py` into `results/offline/` (`invocations.json`, committed at `04b0db37`).

| Invocation | Mode | Rows | Exit | Duration (s) | Parsed | Invented / Ungrounded | Goal Match (All / Expr.) | Intent / Operand / Solid / Premise | E2E (`CC` / `FR_CAP` / `FM` / `SR` / `WS`) | `score.json` SHA-256 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `gold-flat-PILOT` | `PILOT` | 12 | 0 | 1.203 | 12/12 | 0 / 0 | 16/16 (11/11) | 16/16 · 8/8 · 6/6 · 53/53 | `2 / 5 / 0 / 5 / 0` | `a4d832c5…` |
| `replay-flat-PILOT` | `PILOT` | 12 | 0 | 1.703 | 12/12 | 0 / 0 | 16/16 (11/11) | 16/16 · 8/8 · 6/6 · 53/53 | `2 / 5 / 0 / 5 / 0` | `66627603…` |
| `gold-v3-PILOT` | `PILOT` | 12 | 0 | 1.203 | 12/12 | 0 / 0 | 16/16 (11/11) | 16/16 · 8/8 · 6/6 · 53/53 | `2 / 5 / 0 / 5 / 0` | `2dc90f43…` |
| `replay-v3-PILOT` | `PILOT` | 12 | 0 | 1.640 | 12/12 | 0 / 0 | 16/16 (11/11) | 16/16 · 8/8 · 6/6 · 53/53 | `2 / 5 / 0 / 5 / 0` | `84c43f57…` |
| `gold-flat-LOCKED` | `LOCKED` | 24 | 0 | 1.296 | 24/24 | 0 / 0 | 49/49 (43/43) | 49/49 · 31/31 · 33/33 · 99/99 | `6 / 14 / 3 / 1 / 0` | `9e432cc2…` |
| `replay-flat-LOCKED` | `LOCKED` | 24 | 0 | 2.469 | 24/24 | 0 / 0 | 49/49 (43/43) | 49/49 · 31/31 · 33/33 · 99/99 | `6 / 14 / 3 / 1 / 0` | `04fb3e4c…` |
| `gold-v3-LOCKED` | `LOCKED` | 24 | 0 | 1.328 | 24/24 | 0 / 0 | 49/49 (43/43) | 49/49 · 31/31 · 33/33 · 99/99 | `2 / 18 / 3 / 1 / 0` | `6672bd36…` |
| `replay-v3-LOCKED` | `LOCKED` | 24 | 0 | 2.172 | 24/24 | 0 / 0 | 49/49 (43/43) | 49/49 · 31/31 · 33/33 · 99/99 | `2 / 18 / 3 / 1 / 0` | `0a59d1b2…` |

- **Split isolation verified:** `PILOT` processed only the 12 dev cases (`h07` absent from all 4 `PILOT` manifests/scores);
  `LOCKED` processed only the 24 held-out cases in registered order.
- **`h07` runtime resolution:** In all 4 `LOCKED` invocations, `h07` completed within the `1.296s–2.469s` total batch window
  with `extraction.correct = true` (`goal_match = 2/2`, `operand_correct = 1/1`, `solid_correct = 3/3`, `premise_match = 3/3`)
  and safe deterministic refusal `route_code = NOT_ASKED_IN_SOURCE` (`FALSE_REFUSAL_CAPABILITY_GAP`), with `0` timeouts and
  `0` silent errors.
- **Why `LOCKED` `e2e` differs between `flat` (`6` `CORRECT_COMPLETE`) and `v3` (`2` `CORRECT_COMPLETE`):**
  In `LOCKED`, 16 authored gold rows intentionally exercise schema-gap / multi-base / conditional / unsupported shapes that
  `schema_accepts(..., "v3")` rejects upfront with `RESPONSE_CONTRACT_INVALID: 16` before route execution (including 4 rows
  where `flat` proceeds to route execution), while extraction-level obligation metrics (`49/49` goals, `31/31` operands,
  `33/33` solids, `99/99` premises, `23/23` multi-goal completeness, `5/5` schema-gap flagging) are identical across both
  arms, and unsafe outcomes (`WRONG_SILENT`, `OVER_GENERATION`, `hallucinated_entity_rows`) are `0` in all 8 cells.

## 4. Results by Evidence Class

- **A — Live model extraction quality:** `NOT_MEASURED` (`0` live calls; authored-fact GOLD and synthetic REPLAY do not
  measure live model extraction accuracy).
- **B — Gold deterministic ceiling (`GOLD`):** `MEASURED_OFFLINE` across `PILOT` (`2/12` `CORRECT_COMPLETE`, `5/12`
  `SAFE_REFUSAL`, `5/12` `FALSE_REFUSAL_CAPABILITY_GAP`, `0` unsafe) and diagnostic `LOCKED` (`flat`: `6/24`
  `CORRECT_COMPLETE`; `v3`: `2/24` `CORRECT_COMPLETE` due to strict `v3` contract gate on 16 non-v3-conforming gold rows;
  `0` unsafe).
- **C — Synthetic replay wiring (`REPLAY`):** `MEASURED_OFFLINE` (`4/4` replay cells match their corresponding `GOLD`
  extraction and E2E counts byte-for-byte with `execution_class = FAKE` and `live_model_calls = 0`).
- **D — Safety & refusal invariants:** `MEASURED_OFFLINE` (`0` `WRONG_SILENT`, `0` `OVER_GENERATION`, `0`
  `hallucinated_entity_rows`, `0` `ungrounded_quote_facts` across all 8 offline cells).
- **E — Unsupported / schema limitations:** `MEASURED_OFFLINE` (`schema_gap_flagged`: `1/1` in `PILOT`, `5/5` in `LOCKED`;
  `RESPONSE_CONTRACT_INVALID`: `16` in `v3-LOCKED`).
- **F — Provider live (`gemini-2.5-flash`):** `NOT_RUN` / `NOT_AUTHORIZED`. Live acceptance of the 34-branch `v3`
  `responseJsonSchema` remains `NOT_MEASURED`.

## 5. Verification & Authoritative T3 (`verification/authoritative-t3-20261018.json`)

Executed on clean detached `HEAD` at `04b0db373380d980c82e7b7e58cb3fc51b71812f` (product commit `283813b2`,
`ALLOW_LIVE_AI=0`):

| Gate | Result |
|---|---|
| Targeted 11-file revision & grounding suite | `445 passed, 1 xfailed` in `46.89s`, exit `0` |
| Candidate freeze & thesis acceptance matrix | `MATCH` (`6ba9033b…`, 110 files) + `78 passed` in `55.53s`, exit `0` |
| Independent read-only review (`review-gates/revision.json`) | `PASS` (`0` blocking issues; all 4 required file hashes verified) |
| Full backend (`pytest` on detached `04b0db37`, `--basetemp .superpowers/b2`) | `10,508 passed, 1 skipped, 2 deselected, 9 xfailed` in `386.34s`, exit `0` |
| Full frontend (`npm run test:wave` + production `vite build`) | `68 files, 1,079 passed`, typecheck `PASS`, build `PASS` (`2.88s`), exit `0` |
| Locked demo replay (`replay_demo_cases.py`) | `5/5` cases, `1/1` reduced chain, exit `0` |
| Crash-surface audit (`audit_demo_crash_surface.py`) | `6/6` expected boundaries, `0` uncaught exceptions, exit `0` |
| Independent oracle (`inputs/oracle.py`) | `PASS` (`12` dev, `24` heldout, `20` families, `65` requests, `0` mutations), exit `0` |
| Documentation & index gates (`test_docs_information_architecture.py` + `code-index-sync.test.ts`) | `42 passed` (backend) + `3 passed` (frontend), exit `0` |
| Final Authoritative T3 | `FULL_PRODUCT_GATE_PASS` on clean detached `04b0db37` |

*(Note: An initial full-backend run using long path `.superpowers/test-tmp/full-backend-t3-20261018` hit Windows `MAX_PATH`
inside `test_hybrid_ab_pilot_runner.py::test_runner_executes_both_real_adapters_with_separate_telemetry_and_resume[FULL_AB-288]`
with `10,507 passed, 1 failed`; re-running with short `--basetemp .superpowers/b2` on the identical detached commit passed
`10,508/10,508` with `0` failures. Both logs and SHA-256 digests are recorded in `verification/authoritative-t3-20261018.json`.)*

## 6. Stopping Point & Next Owner Decision

Execution stops at **`GO_LIVE_PILOT_REQUIRED`**. See [`approval-request.md`](approval-request.md) and
[`approval-identities.json`](approval-identities.json) for the exact revision identities (`flat-PILOT`, `v3-PILOT`).
`DEFAULT_MODE = LLM_ONLY`, `RESPONSE_CONTRACT = flat`, `CACHE_VERSION = 125`, and `HYBRID_PRODUCT_ENABLEMENT = NO-GO`
remain unchanged.
