# ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT — current execution state

This is the canonical mutable checkpoint for the one Master Epic. After compaction, resume from Git and this file. Do not repeat W4 audits that are still valid.

**Identity**
- Branch: `research/hybrid-master-backend-replacement`, in worktree `.superpowers/worktrees/hybrid-master-backend-replacement`.
- The worktree has no venv of its own; use the root `backend/.venv`.
- Start baseline: `f986e897`. W4 closure: `main` = `origin/main` = live GitHub.
- W4 first remote verification: `94055c98`.
  - product `61ade29e`, candidate `182a7785`, measured 118 files `54b5b565…`;
  - cache 131, `LLM_ONLY`, live 0;
  - receipts in `../geometry-generalization-and-pedagogical-construction/integration/`.
- Cleanup: `SAFE_CLEANUP_COMPLETE_WITH_RETAINED_EXCEPTIONS`. The root-local log of that step is in `.superpowers/master-hybrid-backend-replacement/`.

**Commits**
- `f5ae588b`: the master contract, plan and this checkpoint.

**Task 1 — canonical source references and one identity authority: DONE** (receipt `task1-green.json`)
- `typed_fact_next_extraction.py`: immutable `SourceReference(path, spans)` on `ExtractionResult.source_references`.
  - It records every exact half-open code-point occurrence of each raw quote, overlapping ones included.
  - It is collected by the existing quote walker before normalization and returned only after full validation; a refusal returns `()`.
  - A provider cannot supply its own reference (`INVALID_TYPED_FACT_NEXT`). The provider schema and prompt are unchanged.
- `typed_fact_next_bridge.py::_kiem_pham_vi_tien_de`: the private identity copy is deleted. The bridge delegates to `canonical_vertex_ref`, the sole authority, and keeps its `TuChoi` code translation.
  - Root identities are unchanged.
  - A derived-solid namespace now resolves through its parent chart.
- Tests:
  - RED, then GREEN, for 5 new extraction tests and 1 bridge authority test.
  - One locked source-text mutant anchor was retargeted; the oracle and the fault (scope ignored) are unchanged.
  - Targeted run: 14679 passed. The only failures are 11 pending-freeze checks plus 1 dirty-tree check.

**Impact**
- `CACHE_VERSION` stays 131: `/api/analyze` cannot reach these modules.
- Model surface unchanged.
- Candidate re-freeze is **pending**. It belongs to Task 4, in a separate commit.

**State**
- Migration coverage: unchanged baseline. Hybrid /4 is local offline-replay opt-in. Live understanding and production cutover are `NOT_MEASURED` / `NOT_READY`.
- Remaining legacy, none retired yet:
  - `/api/analyze` still uses LLM_ONLY synthesis by default;
  - the old six-family compiler is still opt-in;
  - Adapter /3 compatibility capabilities have not migrated to /4.
- Open problems:
  - the canonical model lacks general standalone and composite coverage;
  - /4 refuses curved and qualified-identity cases by design;
  - there is no live provider budget;
  - all 20 migration gates need reconciling against the current code.

**Task 2, part 1 — measured /4 inventory: DONE** (`capability-inventory.md`, `inventory-task2.json`, `wave3-task2.json`)
- Regression after Task 1, against the W4 baseline: Wave 3 67/72, 72/72 refused, 62/72 reasons, 0 wrong-served, **0 transitions**; locked 96/96; 203 probes unchanged.
- Section and area questions: 49 cells `SUPPORTED_END_TO_END`, 2 `SUPPORTED_WITH_LIMITS` (A06 radical bound; B01 conditional reading), 3 `REPRESENTABLE_ONLY` (B34–36). Curved solids are `UNSUPPORTED` with the correct code.
- Distance, angle and volume rows are `NOT_MEASURED` in this inventory.

**W3-N47, re-checked:** this is not a taxonomy defect. The locked CIC-D1 order puts grounding before every capability exit, so N47 is kept as is. An independent height-phrasing probe found one fail-closed lexical gap ("chiều cao hình chóp" without "của"); it is recorded only.

**Task 2, part 2: DONE** (`measurement-probe.json`, `tools/measurement_probe.py`)
- Test solid: an independent S.ABCD, square base of side 2, SA ⊥ base, SA = 2, with a hand-written oracle.
- Positives: 10/10 served correct. They cover 6 distance kinds, 3 angle kinds (cos²) and volume.
- Negatives: 4/4 refused with typed codes.
- Scope: one topology only. Other families are `NOT_MEASURED`.
- No new primitive is justified by the measured gaps.

**Task 3, offline inventory: DONE** (`migration-ledger.md`)
- Production has three orchestrators:
  - LLM_ONLY synthesis, the default for `/api/analyze`;
  - compiler C, opt-in and disabled;
  - Route D, offline replay plus operator preview.
- `/api/analyze` cannot reach /4 (D-01 lock).
- The ledger records last consumers. Only the bridge's private identity copy has been removed.
- Gate reassessment:
  - PROVED: D-01/03/05/06/09; D-07/08 for preview only.
  - PARTIAL: D-02/12.
  - OPEN: D-10 (frontend-owned).
  - BLOCKED: D-04/11/13.

**Continuation 2026-10-31 (Owner Master GO "complete offline architecture")**

**Phase A (`e9c9b8e9`): D-02 and D-12 PROVED offline.**
- The existing declared `/api/analyze` opt-in (`HYBRID_V2_LOCAL=offline-replay` + loopback) is extended, not duplicated.
- Route D cache key: exact source + recorded extraction + surface. `ROUTE_D_CACHE_POLICY` gives two-way isolation. Only SERVED results are stored; a poisoned row is a MISS; a write race is handled.
- Rollback = the switch. LLM_ONLY bytes are identical. There is no silent fallback.
- Typed refusals for missing, contradictory, ownership, ambiguous, unsupported, geometry, deadline and adapter faults.
- The runtime call trace shows extraction → /4 route → adapter /4.
- Tests: `test_hybrid_route_d_cache_and_rollback.py`, 23 tests including 2 mutants.

**Phase B (`f5ad1053`): `architecture-consolidation.md`.**
- Call graph and overlap audit: one interpreter and kernel; three program producers; the preview flat contract is a locked input contract, not a duplicate authority.
- Source spans now reach the execution receipt.
- Recomposition evidence: shared primitives across topologies, no duplicate producers, shallow decomposition (`recomposition-evidence.json`).
- No planner change: no failing case shows an abstraction gap.
- Ledger corrected: the first version missed the pre-existing opt-in branch.

**Phase C:**
- `live-evaluation-protocol.md`: pre-registration draft. `MEASUREMENT_CLASS`, `HELD_OUT_CLAIM` = new set required, `EVALUATOR_INDEPENDENCE` and `AUTHORING_INDEPENDENCE` = NOT_ESTABLISHED.
- Harness `backend/scripts/run_paired_route_evaluation.py` + `tests/test_paired_route_evaluation.py`: `READY_FOR_LIVE_MEASUREMENT` (`live-harness-status.md`).
- `owner-go-request.md`: the single consolidated GO.
- Offline measurement finding: LLM_ONLY production sends no `maxOutputTokens`, and its program request omits the IR schema (`$ref`).
- Finding for D-10: Hybrid target quantities lack `annotation.kind` for line–plane/plane–plane distance and angles. Presentation only; not fixed.

**STOP boundary reached (first continuation):** production cutover and LLM_ONLY retirement need a live-provider budget, a new pre-registered held-out set, and a paired differential, latency and cost run (D-04, D-11, GATE-16). The contract says "No live budget is currently authorized."

The original next actions 2 and 3 of that stop were done in the second continuation; see the Phase A–D entries.

**Phase D (second continuation), gates:**
- Regression at HEAD, against the W4 baseline: 0 transitions (`inventory-phase-d.json`).
- Candidate frozen in its own commit, `bf2c3eaa`: product `f5ad1053`, 118 files `44b02a62…`, cache 131 (no bump; LLM_ONLY bytes identical). New divergence layer in `candidate_divergence.json`.
- T0 `IMPACT_GATE_PASS` (15929/0); T2 PASS (1424 vitest, tsc, build); **Full T3 `FULL_PRODUCT_GATE_PASS`**, attempt 1, on fresh detached `hm-final-t3-bf2c3eaa`, which has since been removed cleanly (`tiers.json`, `full-t3.json`).
- Publication range `f986e897..HEAD`: PASS. 0 `Co-Authored-By` trailers.
- This worktree keeps two gitignored junctions, `backend/.venv` and `frontend/node_modules`, pointing to the main checkout. Remove them with `[IO.Directory]::Delete` before removing the worktree.

**Third continuation (Owner GO "independent review → live readiness → cutover → retirement"), in progress:**
- **`d9615cdb`, harness hardening (scripts/tests/docs only; the candidate is unchanged and still verifies):**
  - per-request hard USD cap on the exact payload for both arms;
  - production-equivalent Hybrid transport (`live_transport`, the same retry and 120 s timeout as `call_gemini`, a 480 s deadline);
  - corpus integrity checks and a contamination scan;
  - an identity stop;
  - mock-provider tests for every failure mode (27 tests).
- **Provider facts verified** against Google docs (`provider-facts.md`): 2.5 access is limited to past users; a paid tier is required for privacy; output 65 536 including thinking; no instant provider-side hard cap.
- **`heldout-authoring/` package:** no cases and no author written.
- **Independent architecture review: `INDEPENDENT_BACKEND_ARCHITECTURE_REVIEW_READY`** — 0 BLOCKER, 0 MAJOR, 4 MINOR (`architecture-review.md`, `c14189d6`).
  - Closed: M-1 (pinned test), M-2 (bump rule in D-02), and the M-4 ops script.
  - Deferred to the next product change: M-3 (a doubly-faulted adapter returns 500) and the M-4 docstrings. Any `backend/app` edit invalidates the candidate and T3.
- **Ledger:** retirement statuses are in `migration-ledger.md` (`934ad0c0`).
- **Live-evaluation readiness review, first pass: `NOT_READY`** — 3 BLOCKER, 4 MAJOR.
  - The blockers were π dropped, curved solids treated as refuse, and missing `assign.*` producers.
  - All were verified and fixed in the harness, tests and protocol at `edbc54b7` (32 tests; `evaluation-readiness-review.md`). The implementer also found and fixed the missing production domain gate on the Hybrid arm.
  - Round 2: `NOT_READY`, with 2 new BLOCKERs (proof requests treated as refuse; a lenient rule that scored a shown wrong value as correct), a regressed scan path, and an interrupted run reported as complete. All fixed at `cbab8fde`.
  - **Round 3: `LIVE_EVALUATION_READINESS_REVIEW_READY`.** 0 BLOCKER, 0 MAJOR. The two MINORs are covered by authoring rules. Harness tests: 38.
- **Candidate:** still `bf2c3eaa` / `44b02a62…`. No product code has changed since the Full T3 PASS. The deferred MINORs M-3 and M-4 (docstrings) wait for the next product change.
- **Status:** `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`; overall `HYBRID_NOT_READY`.
- **Next (the real boundary, an Owner decision):**
  1. Give the GO in `owner-go-request.md`, including the paid project and confirmation of `gemini-2.5-flash` access.
  2. Name an independent author, who writes the 60 problems.
  3. Run `--manifest`; the Owner writes the approval file.
  4. `--live`: the agent runs the whole evaluation without asking per request.

  Without these: no live call, no cutover, no retirement.

**Final status of the second continuation:**
- Offline backend: **`OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`**.
- Overall: **`HYBRID_NOT_READY`**. There has been no live measurement and no cutover; LLM_ONLY is not retired. Nothing is merged or pushed: this epic has no publication or integration authorization yet.

**Remaining gates:**
- D-04, D-11, D-13 and GATE-13/15/16/20: live and human measurements.
- D-10: frontend presentation, including the missing `annotation.kind` on some Hybrid quantities.
- An independent architecture review before any cutover or integration.

**Next exact action:**
1. The Owner decides on `owner-go-request.md` and names an independent author for the held-out set.
2. With a GO: freeze the corpus and oracle hashes into the protocol, then run `backend/scripts/run_paired_route_evaluation.py --live` under the approved terms.
3. Without a GO: no further offline item in this epic is blocked. Optional: an independent architecture review of `f986e897..HEAD` before an integration request.

---

## Fourth continuation (Owner Master GO "architecture generalization + pre-live acceptance hardening"), 2026-10-31

This section supersedes the "Next exact action" above. Earlier sections are kept as history.

**Commits on the branch, in order:**
- `5bec390f`, `9e2cfe80`, `383fd4f7`, `9aa74c58`, `15a7fbd6`: the acceptance contract (harness, tests, protocol revisions A–D).
- `14155201`: M-3.
- `b249d82a`: registry /22.
- `e20f30e7`: regression receipts.
- `5caa6e94`: candidate re-freeze.

**Phase A — acceptance contract: `ACCEPTANCE_CONTRACT_REVIEW_READY`.** It took 4 rounds with a fresh-context reviewer, recorded in `evaluation-readiness-review.md` under "Acceptance contract".
- §7 is now **code**: `acceptance()` in `run_paired_route_evaluation.py`, and the run summary carries the verdict.
- **Criterion 1 (A1):** 0 observed Hybrid wrong-serves, plus no excess over the control. Wilson intervals over exercised rows are reported and never compared. The old rule gave 0/60 vs 0/60 ⇒ NO-GO.
- **A2:** the control arm is never stopped, because stopping it made a GO unreachable exactly when LLM_ONLY was the unsafe arm.
- **Criterion 5:** Hybrid's charged upper bound against the control's lower bound, which uses reported usage only with cached prompt tokens at 0. Reviewer findings B1, M1, N1 and N3 were each a false-GO or unreachable-GO path, and each is fixed and tested.
- **Precondition 0:** composition 45 + 5 + 5 + 5; a complete run; `stop_reason` null; paired ids equal to the corpus ids.
- The approval must state `corpus_author`, `authoring_independence` and `evaluator_independence`.
- The thresholds of criteria 2–7 are unchanged.
- **Stated limitations:** McNemar never binds beside −5 pp at n = 45; there is no served-correct floor (the `CONTROL_ARM_DEGENERATE` flag covers that).
- An end-to-end GO is reachable through `evaluate()`. Harness tests: 46.

**Phase B — M-3: CLOSED.** The fault handler re-ran `build_adapter4_response`, so a fault in its refusal path (`classify_refusal`) escaped as HTTP 500.
- **Fix:** `adapter4_route.adapter_fault_response` builds the envelope from constants; it is test-locked equal to the normal refusal path.
- `run_hybrid_offline` returns `ROUTE_INTERNAL_ERROR` for any other fault of ours, past argument validation.
- **Tests:** RED → GREEN for 4 tests (repeated faults; recovery with no poisoned state; a broken classifier on a refused route; an unexpected exception without leaked prose). A mutant that restores the re-call fails them.
- M-4 docstrings are closed.
- This is a technical refusal, not a semantic one: it is classified technical in receipts and in the harness.

**Phase C — architecture (`architecture-capability-audit.md`):**
- **Development probe** `tools/topology_probe.py` → `topology-probe.json`: 4 new topologies, 36 hand-oracle questions, **36/36 exact** at registry /22. It was 35/36 before the fix below.
- **Components A–J are classified;** the planner is a **bounded effect planner** (needs/effects producer selection, shallow decomposition).
  - The probe found no gap where existing primitives could reach a goal the planner misses.
  - **So no planner change is justified.**
- **Implemented: Source Gate registry /22.** "H, K lần lượt là hình chiếu … của A trên SB, SC" is now read with ordered pairing (`test_respectively_projection_grounding.py`, 8 tests including a pairing mutant).
  - This was a parity gap with LLM_ONLY (W18).
  - The preview fixture chain is extended (`export_hybrid_preview_fixtures.py`), and the 5 version pins are updated.
- **18-group delta:** curved (7–9, 14–16), frustum (10) and Oxyz (17–18) stay REFUSED on /4.

**Gates at `5caa6e94`:**
- Geometry suite before the freeze: 13353 passed. The 11 failures were all freeze-pending or dirty-tree checks, and the identity tests pass after the freeze (168/168).
- Locked regression (`inventory-phase-e.json`): Wave 3 67/72, 0 wrong-served, **0 transitions**; locked 96/96; 203 probes with 0 served negatives, 0 internal, 0 transitions.
- **Candidate `5caa6e94`:** product `b249d82a`, measured 118 files `f0ebd8df…`, cache 131 (no bump).
  - The divergence layer is `inputs/candidate_divergence.json`.
  - `--verify` matches.
- **Full T3:** see `full-t3-5caa6e94.json`. T0 and T2 are subsets of T3: pytest, vitest, build, replay, crash surface.

**Status:**
- `ARCHITECTURE_CAPABILITY_PROGRESS`: Source Gate parity /22; M-3 closed; the planner is classified.
- `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`: Full T3 `FULL_PRODUCT_GATE_PASS` at `5caa6e94`, attempt 1; pytest 15984 passed, 0 failed; vitest 1424; build, replay and crash surface (6/6 typed, 0 HTTP 500) all pass (`full-t3-5caa6e94.json`).
- Overall `HYBRID_NOT_READY`.
- Not `LIVE_MEASUREMENT_READY`: there is no corpus author and no GO.

**Decisive capability finding for cutover.** The pre-registered corpus admits curved solids as expected-serve, because LLM_ONLY serves them. /4 refuses them all (`BRIDGE_UNSUPPORTED_CURVED`), and criterion 2 tolerates a net loss of at most 2 of 45. So **a corpus with ≥ 3 curved serve cases makes `HYBRID_CUTOVER_NO_GO` near-certain under the current product.**

**Next exact action:**
1. **Architecture, offline and justified:** curved solids on /4 inside the one planner. No second compiler, and no bridge into Adapter /3.
   - **Scope:** Registry functions for cylinder, cone and sphere on exact ℚ³ anchors (`geometry/curved.py` exists); Source Gate grammar; planner effects; engine certificates for π-exact volume, area and radius; the /4 scene.
   - **Start with:** a RED development probe of curved volume, area and radius, with hand π oracles; then the Registry function design and its exact pre/postconditions.
2. **Owner, one consolidated decision:** `owner-go-request.md`. Either run the live evaluation on the current product, knowing it measures the curved gap, or after step 1. In both cases the Owner names the independent corpus author.
3. With a GO: freeze the corpus hash into a protocol amendment, then `--live`.

---

## Fifth continuation (Owner GO option (b): curved geometry on /4), 2026-10-31 — IN PROGRESS

This section supersedes the fourth continuation's "Next exact action".

**Commits:**
- `588cdf03`: the curved slice.
- `e58d319a`: kind dispatch moved into the kernel table, the registered boundaries kept, the planner-only functions recorded.
- `38e1a0bf`: grounding fixes after independent review round 1.

**What is served on /4.** Details are in `curved-capability.md`, with hand oracles in `tools/curved_probe.py` → `curved-probe.json`.
- **Solids:** cylinder, cone and sphere, declared with centre, top/apex and rim, radius and height. Named points are optional, and the canonical pose is used when none are named.
- **Measures:** volume, lateral area, sphere surface, radius, and the total area of a cylinder or cone. The total is composed as lateral area plus base circle(s), and unlike radical terms give `EXACT_DOMAIN_EXCEEDED`.
- **Derived dimension:** a cone's height from its slant, by Pythagoras.
- **Symbolic unit a.**
- **Probe:** 16/16 served exactly correct, plus 24 correct refusals: 1 domain case, 12 adversarial cases, and 11 reproductions from the review.

**Design.** There is still one route: bridge → planner `_ke_hoach_cong` → Source Gate `_khoi_cong_dung_nguon` / `_cong_khop` → engine `_dung_cong`, a canonical-pose layout beside `_Dung` → the existing curved IR / interpreter / kernel → Adapter /4.
- Per-kind facts come only from `curved.KHOI_CONG`, through `LOAI_TU_NGUON`.
- The certificate `_chung_chi_cong` checks arithmetic. Grounding is the Source Gate's job.
- Versions: registry /23, planner /19, engine /15.
- Route A's provider surface and LLM_ONLY are unchanged; no `CACHE_VERSION` bump.

**Still refused, typed:**
- curved sections, relations and composites, including inscribed / circumscribed solids;
- the standalone frustum;
- diameter / circumference phrasings;
- the legacy /1 bridge.

The Owner-registered curved controls keep `BRIDGE_UNSUPPORTED_CURVED`.

**Parity:** PARTIAL. Adapter /3 still owns parallel and axial sections and the cone ratio / remaining volume.

**Independent review:**
- Round 1: `NOT_READY`, with 3 blockers, all wrong-serve paths.
- After the fix: re-review round 2 is pending.

**Next exact action:**
1. Get review round 2 to READY.
2. Full backend suite.
3. Regression replay: `tools/capability_inventory.py phase-f`.
4. Re-freeze the candidate, in its own commit, with a new divergence layer in its own run folder, `runs/hybrid-master-curved-solids/candidate_divergence.json`, correcting the 5caa6e94 layer. Both layer paths in this run folder are already taken.
5. Full T3 on a fresh detached worktree.
6. Write back: CODE_INDEX, ledger, owner-go-request (measured system), and this file.
