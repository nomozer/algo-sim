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

## Fifth continuation (Owner GO option (b): curved geometry on /4), 2026-10-31 — CHECKPOINT REACHED

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

**Fifth continuation: final state (supersedes the "Next exact action" just above).**
- **Further commits:**
  - `face0fc1`: the closed clause grammar.
  - `4074e8b9`: the review recorded READY; the `NON_POSITIVE_LENGTH` fix; regression receipts.
  - `98df8189`: candidate re-freeze.
- **Independent review:** **`INDEPENDENT_CURVED_SLICE_REVIEW_READY`**, round 3 (`curved-slice-review.md`). 19 earlier false serves are refused and locked as tests; 97 probes match hand oracles.
- **Probe:** 18/18 positives exact, plus 30 correct refusals (`curved-probe.json`).
- **Locked regression at `face0fc1`** (`inventory-phase-f.json`): Wave 3 67/72, 0 wrong-served, **0 transitions**; locked 96/96; 203 probes clean.
- **Candidate `98df8189`:** product `4074e8b9`, measured 118 files `2f8c9945…`, cache 131 (no bump). The divergence layer is `runs/hybrid-master-curved-solids/candidate_divergence.json`; `--verify` matches.
- **Full T3 `FULL_PRODUCT_GATE_PASS`** at `98df8189`, attempt 1: pytest 16039 passed, 0 failed; vitest 1424; build, replay and crash surface (6/6 typed, 0 HTTP 500) all pass (`full-t3-98df8189.json`).
- **Status:**
  - `ARCHITECTURE_CAPABILITY_PROGRESS`: curved solids on /4.
  - `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`.
  - Overall `HYBRID_NOT_READY`: no live measurement, no corpus author, no GO.
- **Next exact action, offline and justified:** port the remaining Adapter /3 curved capabilities into the same route and grammar. All of them sit on existing kernel primitives.
  1. Sections parallel to the base: a circle and its area, via `intersect_plane_curved`.
  2. Axial sections.
  3. The cone volume ratio / remaining volume.

  After those come the diameter phrasing and inscribed / circumscribed spheres, which need new relation types.
- **Owner:** the single GO in `owner-go-request.md`, an independent author for the corpus, and the approval file.

---

## Sixth continuation (Owner GO: curved sections, cone ratio, reusable composition), 2026-10-31 — CHECKPOINT REACHED

This section supersedes every earlier "Next exact action".

**Commits:**
- `5dc812ed`: the slice.
- `140ead7a`: review round-1 fixes.
- `142eb9db`: the notation boundary, which restores the Wave 3 W3-N45/N46 reasons.
- `bfe8912f`: duplicate section names (round 2).
- Review record and replay receipts.
- `7a870059`: candidate re-freeze.

**Served on /4 (registry /24, planner /20, engine /16):**
- **Sections parallel to the base, of a cylinder and a cone:** at a stated distance from the base, or, for a cone, through the midpoint of its height. This is the kernel's `intersect_plane_curved` of the plane z = d.
- **Axial sections:** a rectangle or an isosceles triangle, with the plane proven by the kernel to contain the axis.
- **The small cone:** built by the kernel from the apex and the radius it **measures** on the section.
- **Ratio:** by cross-multiplication, in either order the question states.
- **Remaining volume:** by subtraction.
- **Certificates:** each answer has an independent similarity certificate, k = (h − d)/h.
- **Grounding:** closed grammars for the section, derived-cone and question sentences.

**Evidence:**
- Probe `tools/curved_section_probe.py`: 11 positives served exactly correct and 17 refused correctly (`test_route_d_curved_sections.py`).
- **Independent review: `INDEPENDENT_CURVED_SECTION_REVIEW_READY`**, round 3 (`curved-section-review.md`).

**Regression at `bfe8912f`** (`inventory-phase-i.json`):
- Wave 3: 67/72, 0 wrong-served, **0 transitions**.
- Locked cases: 96/96.
- 203 probes: 0 served negatives and 0 internal faults. 12 positive probes moved REFUSED → REFUSED.

**Registered controls:** 32 cells, REFUSED → REFUSED, recorded in the explicit layer `registered-curved-control-transitions.json` and asserted to remain refusals.

**Candidate `7a870059`:** product `bfe8912f`, measured 118 files `277338ce…`, cache 131 (no bump). The divergence layer is `runs/hybrid-master-curved-sections/candidate_divergence.json`.

**Full T3 `FULL_PRODUCT_GATE_PASS`** at `7a870059`: pytest 16071 passed; vitest 1424; build, replay and crash surface all pass (`full-t3-7a870059.json`).

**Status:**
- **`CURVED_PARITY_PARTIAL`.** These are `SUPPORTED_BOTH`: solid measures; parallel and axial sections; cone ratio and remaining volume. Still only on /3: an arbitrary apex ratio, the plane-equation path and ellipse sections, and the solid wordings "tâm đáy O" and "tâm đáy dưới/trên". Sphere sections are unsupported on /4.
- `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`.
- Overall `HYBRID_NOT_READY`.

**Next exact action (offline):**
1. Grammar for the wordings above, in the same closed grammar, each with adversarial locks.
2. An apex ratio "cắt trục SO theo tỉ lệ k tính từ đỉnh S".
3. Design, with failing examples, for a sphere section (`distance_from_center`; a contract change ⇒ model-surface impact).

Then the composite and inscribed/circumscribed design.

## Seventh continuation (Owner GO "REGISTERED CONTRACT AUDIT → GENERALIZED CURVED GEOMETRY → SPHERE SECTIONS → ARCHITECTURE HARDENING"), 2026-10-31: CHECKPOINT REACHED

Offline. `MAX_AUTHORIZED_LIVE_REQUESTS = 0`; 0 provider calls.

| Commit | Content |
|---|---|
| `6e0a6c2c` | Audit, base-centre grammar, apex ratio k, sphere sections (registry /25, planner /21, engine /17) |
| `8b057c0a` | Fixes from review round 1 |
| `d9d11b60` | Fixes from review round 2 (this is the product commit) |
| `0a9e40c2` | Review READY (round 3) and the regression replay (phase-k) |
| `cb06635e` | Candidate re-frozen in its own commit, with a new divergence layer in `runs/hybrid-master-curved-generalization/` that corrects the sixth-continuation layer |

**Registered contract audit** (`registered-curved-controls-audit.md`):

- 32 of 32 controls are still REFUSED, and so are the 12 moved probes; 0 moved REFUSED → SERVED.
- Two refusal-reason regressions were found and fixed: unread wording is now `CURVED_WORDING_UNSUPPORTED`, and several sections in one run is now `CURVED_MULTI_SECTION_UNSUPPORTED`. Both are in the CAPABILITY group.
- The record has three layers. Each later layer corrects the one before, and no layer is edited. `load_transitions` asserts the chain.

**Architecture** (`curved-generalization-audit.md`, `curved-capability.md` §7):

- **Base-centre wordings:** 16/16 probe cases correct.
- **General apex ratio k:** 20/20. The gate converts OM/OS; a named axis point is the section centre.
- **Sphere sections:** 19/19. They use the additive /2 plane kinds `at_distance_from_center` and `through_center` and the kernel's `_giao_cau`, with the certificate r'² = R² − d². d = R refuses as tangent; d > R as missing.
- **Greek plane names** are now read.
- **Model surface:** changed for the /4 arm only. `CACHE_VERSION` 131 is not bumped, because LLM_ONLY is untouched.
- **Planner:** no new search. Each change is backed by a failing case.
- **Trace:** PARTIAL at `cb06635e` (superseded in the eighth continuation below, which exports machine-verified `preconditions` and `postconditions`). Typed steps, dependencies and provenance are present; preconditions and postconditions are enforced but not exported.

**Review** (`curved-generalization-review.md`): three rounds — 5 MAJOR, then 2 MAJOR, then **READY**. 0 BLOCKER in any round. Every finding is locked by a test with its exact code.

**Gates:**

- **Wave 3:** 67/72 served correctly; 72/72 negatives refused; 0 wrong-served.
- **Locked 96:** 96/96.
- **203 probes:** 0 wrong-served.
- **Full T3:** `FULL_PRODUCT_GATE_PASS` on attempt 1, on a fresh detached worktree (`full-t3-cb06635e.json`). pytest 16140/0, vitest 1424, build, demo 5/5, crash surface 6/6.
- **Candidate:** `cb06635e`, product `d9d11b60`, 118 files `4c269bab…`. `--verify` matches.
- **Publication scan** of `f986e897..HEAD`: PASS. 0 `Co-Authored-By` trailers.

**Status:**

- `ARCHITECTURE_CAPABILITY_PROGRESS`.
- `CURVED_PARITY_PARTIAL`: the 8 curved fixtures still refuse, blocked by P-1, P-2 and an unordered ratio.
- `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`: this waits on the Owner live GO.
- Overall: **`HYBRID_NOT_READY`**. Nothing is merged or pushed.

**Next priority:**

1. Owner rulings P-1, P-2 and P-3 (`owner-go-request.md`). These are the only path to curved fixture parity without repinning on our own.
2. The Owner live GO for the paired measurement.

## Eighth continuation (Cross-Agent Handoff from `962a0d53`: role-phrase parity, pedagogical trace pre/postconditions, certified circumscribed spheres on `/4`), 2026-10-31: CHECKPOINT REACHED

Offline. `MAX_AUTHORIZED_LIVE_REQUESTS = 0`; `MAX_AUTHORIZED_LIVE_SPEND_USD = 0`; `0` provider calls. Versions held at `geometry-functions/25`, `geometry-fact-planner/21`, `geometry-function-engine/17`; `DEFAULT_MODE = "LLM_ONLY"` and `CACHE_VERSION = "131"` unchanged; `0` edits to `semantic_program/` or `frontend/`.

| Commit | Content |
|---|---|
| `df81deba` | Slices 1–3 implementation, Round 1 & Round 2 review fixes, `schema-census-extension.json`, `circumscribed_sphere_probe.py`, and regression suites |
| `5e50379d` | Independent review `READY` (Round 2), `phase-l` replay, and doc reconciliation |
| `44a0b79e` | Restore `_khoi_khop` mutant-test line anchor in `registry.py` (this is the final product commit) |
| `37ef4fff` | Re-export 41 Adapter `/2` preview fixtures with trace `preconditions`/`postconditions` (`fixtures-adapter-2-trace-pre-postconditions/`; historical W4 bundle preserved byte-for-byte) |
| `b1b4cf5e` | `phase-l2` regression replay at product `44a0b79e` and Continuation 8 doc sync |
| `db1ac63a` | Candidate re-frozen in its own commit (`runs/hybrid-master-circumscribed-spheres/` correcting `runs/hybrid-master-curved-generalization/`) |

**State restoration from `962a0d53`:**

- Continuation 7 items A–F (`registered-curved-controls-audit.md`, base-centre grammar, general apex ratio $k$, sphere sections, planner audit, Round 3 `READY` + Full T3 at `cb06635e`) verified `COMPLETED_VERIFIED`; item G (`docs/CURRENT_STATE.md` / `docs/EVIDENCE_INDEX.md` / `migration-ledger.md` / `curved-generalization-audit.md` sync) reconciled in this continuation.

**Three offline backend slices delivered on Route D `/4`** (`curved-capability.md` §8, `circumscribed-spheres-review.md`):

- **Slice 1 — Polyhedral Role-Phrase Source Gate Parity:** `_C_VAI` + `_cua_khop` accept explicit solid nouns without `"của"` (`"chiều cao hình chóp"`, `"cạnh bên hình lăng trụ"`, etc.) while delegating prism-subclass verification (`"lập phương"`, `"hộp chữ nhật"`, `"hộp"`, `"đứng"`, `"đều"`, `"tam/tứ/ngũ/lục giác"`) directly to `_loai_cum_dung` (`test_route_d_role_phrase_parity.py`).
- **Slice 2 — Pedagogical Construction Trace Hardening:** `_gan_dieu_kien_vet` computes and exports machine-verified `preconditions` and `postconditions` (plus auxiliary-step `dependencies`) on `KetQuaTuyen.trace` and `route_d.construction_trace`; strips post-execution kernel claims on every `REFUSED` path (including post-engine `SCENE_BUILD_FAILED`, `NEGATED_CLAUSE`, `PROOF_UNVERIFIABLE`); emits axisless `canonical_origin_center` / `center_at_origin` on standalone spheres (`test_route_d_pedagogical_trace.py`).
- **Slice 3 — Certified Circumscribed Spheres of Polyhedra on `/4`:** additive `SolidSpec.circumscribes` on `typed-fact-next/2` (`schema-census-extension.json`); exact `Fraction` $3 \times 3$ Gram circumcenter solver (`_tam_bon_dinh`) + all-vertex cosphericity certificate (`NO_CIRCUMSCRIBED_SPHERE`); exact `Fraction` Cholesky Euclidean chart normalization (`chuan_hoa_euclid`, refusing irrational charts with `METRIC_REQUIRES_EUCLIDEAN_CHART`); G4 IR perpendicular-bisector construction (`_emit_tam_ngoai_tiep`) + `construct_curved_solid` + independent closed-form cross-check; closed Vietnamese Source Gate grammar (`_CAU_CONG_NGOAI_TIEP`) + composite polyhedron/sphere `ask_volume` disambiguation via `_chi_mot_khoi_3d` (`circumscribed_sphere_probe.py`: `12/12` positives served with exact `π`/radical values, `12/12` adversarial negatives refused fail-closed; `test_route_d_circumscribed_spheres.py`).

**Independent adversarial review** (`circumscribed-spheres-review.md`, subagent `0ef27125-61ad-4f33-b4aa-e126981ee0e6`): two rounds — `2 MAJOR, 2 MINOR, 2 NIT` (`NOT_READY`), then **`READY`** (`0 BLOCKER, 0 MAJOR`; `MINOR-R2-1` also closed).

**Gates:**

- **Wave 3 (`inventory-phase-l2.json`, `wave3-phase-l2.json`):** `67/72` served correctly; `72/72` negatives refused (`62` exact reason); `0` wrong-served; `0` transitions.
- **Locked 96:** `96/96`, `0` wrong-served.
- **203 probes:** `0` served negatives, `0` internal errors (same 12 curved `REFUSED -> REFUSED` transitions).
- **Registered curved controls:** `32/32` remain `REFUSED` (`0` moved `REFUSED -> SERVED`).
- **Candidate:** `db1ac63a`, product `44a0b79e`, 118 files `ccfce08c…`. `freeze_evaluation_candidate.py --verify` matches.
- **Full T3:** `FULL_PRODUCT_GATE_PASS` on attempt 1 of `db1ac63a`, on fresh detached worktree `hm-t3-db1ac63a` (`full-t3-db1ac63a.json`): pytest `16181` passed (`0` failed, `7` skipped, `2` deselected, `15` xfailed), vitest `84` files / `1424` passed, production build `PASS`, demo replay `5/5`, crash surface `6/6`.
- **Publication scan** of `f986e897..HEAD`: `PASS` (`0` violations, `0` `Co-Authored-By` trailers).

**Status:**

- `ARCHITECTURE_CAPABILITY_PROGRESS`.
- `CURVED_PARITY_PARTIAL` (the 8 curved fixtures still refuse on `/4`, gated on `P-1`, `P-2` and unordered ratio).
- `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`.
- Overall: **`HYBRID_NOT_READY`**. Nothing is merged or pushed.

**Next priority (live / human / frontend gates only):**

1. Owner rulings `P-1`, `P-2` and `P-3` (`owner-go-request.md`) if curved fixture repins are desired.
2. Owner live GO + independently authored 60-problem held-out corpus for paired live measurement (`D-04`, `D-11`, `D-13`, `GATE-16`), plus frontend `D-10` and manual QA `GATE-13`/`GATE-15`/`GATE-20` before any cutover decision.

---

## Ninth continuation (Owner Master GO: Multi-Object FactGraph + Composite Geometry + Generalized Geometric Relations), 2026-11-01: CHECKPOINT REACHED

Offline. `MAX_AUTHORIZED_LIVE_REQUESTS = 0`; `MAX_AUTHORIZED_LIVE_SPEND_USD = 0`; `0` provider calls. Versions bumped to `geometry-functions/26`, `geometry-fact-planner/22`, `geometry-function-engine/18`, and `geometric-relation-certificate/1`; `DEFAULT_MODE = "LLM_ONLY"` and `CACHE_VERSION = "131"` unchanged; `0` edits to `adapter3_simulation.py`, `semantic_program/`, or `frontend/`.

| Commit | Content |
|---|---|
| `fa1ed277` | Multi-object FactGraph audit, additive `typed-fact-next/2` relation contract, certified polyhedron insphere (`_tam_noi_tiep_da_dien`), certified sphere–plane tangency (`_chan_tiep_xuc_mat`), axial cylinder/cone + sphere composites (`_dung_cong_ghep`), planner DAG + `composition_classification`, Source Gate closed grammar, 4-layer `relation_certificates`, Round 1–3 review fixes, `composite_relations_probe.py`, and `test_route_d_composite_relations.py` (`54/54`) |
| `625da863` | Re-export 41 Adapter `/2` preview fixtures with `composition_classification` and `relation_certificates` (`fixtures-adapter-2-composition-classification/`; earlier bundles preserved byte-for-byte) |
| `f6a605f5` | `phase-m` regression replay at product `fa1ed277` (`inventory-phase-m.json`, `wave3-phase-m.json`) and Continuation 9 capability/index docs |
| `17e4a326` | Candidate re-frozen in its own commit (`runs/hybrid-master-composite-relations/` correcting `runs/hybrid-master-circumscribed-spheres/`) |

**Capabilities delivered on Route D `/4`** (`multi-object-factgraph-audit.md`, `curved-capability.md` §9, `composite-relations-review.md`):

- **Workstream A — Multi-Object & Relation Audit + Additive V2 Contract:** 16-dimension architectural audit (`multi-object-factgraph-audit.md`) evaluating all 12 candidate relations; additive `GeometricRelationSpecV2` (`circumscribes`, `inscribed_in`, `tangent_to` with optional `contact_ref`) and `SolidSpec.inscribed_in` in `typed-fact-next/2` (`typed-fact-next/1` schema untouched), unique `relation_id` validation, `solid_scope` disambiguation for dual unnamed `"()"` solids, and `schema-census-extension.json` closure (`test_scope_census_closure.py`).
- **Workstream B — Certified Insphere (5A), Certified Sphere–Plane Tangency (5B), and Composite Topologies (5C/5D):**
  - **5A (`_tam_noi_tiep_da_dien`):** exact `Fraction` + integer `isqrt` + multiquadratic `_QField` ($m \le 4$) solver across **all** boundary faces (`NO_INSCRIBED_SPHERE` when tangential compatibility fails; `EXACT_DOMAIN_EXCEEDED`; `METRIC_REQUIRES_EUCLIDEAN_CHART`), enforcing face coplanarity (`NON_COPLANAR_POINTS`), strict polygon convexity (`DEGENERATE_SOLID`), strict inward half-space signs, strict relative-interior face polygon contacts $T_k \in \operatorname{relint}(F_k)$, and independent pure-`Fraction` volume-surface identity ($9V^2 = r^2 (\sum_k S_k)^2$).
  - **5B (`_chan_tiep_xuc_mat`):** exact Euclidean chart distance $d^2(O, (\alpha)) = R^2$ vs. secant (`PLANE_INTERSECTS_SPHERE_NOT_TANGENT`, $d^2 < R^2$) vs. disjoint (`PLANE_DOES_NOT_TOUCH_SPHERE`, $d^2 > R^2$), certified non-collinear witness triple for G4 IR `construct_plane`, and optional named contact point verification (`INCONSISTENT_FACTS` on mismatch, usable in downstream metric goals).
  - **5C & 5D (`_dung_cong_ghep` & polyhedral composites):** multi-polyhedron (`shared_faces` / `shared_vertices`) + spheres; dual spheres (`(S1)` circumscribed + `(S2)` inscribed, plus dual unnamed `"()"` spheres via synthetic `(out:...)` / `(in:...)` symbols); polyhedron plane section + sphere coexistence; axial cylinder/cone hosts (`O.O'`, `(T)`, `S.O`, `(N)`) + circumscribed/inscribed/dual spheres (`NO_INSCRIBED_SPHERE` when cylinder $h \ne 2R$); multi-goal cross-solid queries; unanchored multi-curved payloads remain fail-closed (`BRIDGE_UNSUPPORTED_CURVED_COMPOSITE`).
- **Workstreams C–F — Planner DAG, Source Gate Grounding, 4-Layer `relation_certificates` & Scene3D:** explicit multi-object dependency DAG (`DEPENDENCY_CYCLE` detection) + honest `composition_classification`; closed Vietnamese Source Gate grammar (`_CAU_CONG_NGOAI_TIEP`, `_CAU_TIEP_XUC_MP`, `_host_cum`, multi-sphere disambiguation, negation/conditional/goal rejection); 4-layer `relation_certificates` (`SOURCE_GROUNDING_PROOF`, `GEOMETRIC_RELATION_PROOF`, `KERNEL_EXECUTION_PROOF`, `RESULT_CERTIFICATE`) cleared on all `REFUSED` envelopes; composite `construction_trace` and `Scene3D` (`0` edits to `frontend/`).

**Independent adversarial review** (`composite-relations-review.md`, subagent `117e0e72-2c22-4db8-a8de-066bc0ccf54a`): three rounds — Round 1 (`1 BLOCKER, 4 MAJOR, 3 MINOR, 2 NIT`), Round 2 (`1 BLOCKER, 2 MAJOR, 2 MINOR`), Round 3 **`READY`** (`0 BLOCKER, 0 MAJOR, 0 MINOR, 1 NIT` closed before commit; `54/54` tests in `test_route_d_composite_relations.py`, `17/17` positives & `19/19` negatives in `composite_relations_probe.py`).

**Gates:**

- **Wave 3 (`inventory-phase-m.json`, `wave3-phase-m.json`):** `67/72` served correctly; `72/72` negatives refused (`62` exact reason); `0` wrong-served; `0` transitions.
- **Locked 96:** `96/96`, `0` wrong-served.
- **203 probes:** `0` served negatives, `0` internal errors (same 12 curved `REFUSED -> REFUSED` transitions).
- **Registered curved controls:** `32/32` remain `REFUSED` (`0` moved `REFUSED -> SERVED`).
- **Candidate:** `17e4a326`, product `fa1ed277`, 118 files `9583018d…`. `freeze_evaluation_candidate.py --verify` matches.
- **Full T3:** `FULL_PRODUCT_GATE_PASS` on attempt 1 of `17e4a326`, on fresh detached worktree `hm-t3-17e4a326` (`full-t3-17e4a326.json`): pytest `16237` passed (`0` failed, `7` skipped, `2` deselected, `15` xfailed), vitest `84` files / `1424` passed, production build `PASS`, demo replay `5/5`, crash surface `6/6`.
- **Publication scan** of `f986e897..HEAD`: `PASS` (`0` violations, `0` `Co-Authored-By` trailers).

**Status:**

- `ARCHITECTURE_CAPABILITY_PROGRESS`.
- `CURVED_PARITY_PARTIAL` (the 8 curved fixtures still refuse on `/4`, gated on `P-1`, `P-2` and unordered ratio).
- `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`.
- Overall: **`HYBRID_NOT_READY`**. Nothing is merged or pushed.

**Next priority (live / human / frontend / deferred geometry frontiers):**

1. Owner rulings `P-1`, `P-2` and `P-3` (`owner-go-request.md`) if curved fixture repins are desired.
2. Owner live GO + independently authored 60-problem held-out corpus for paired live measurement (`D-04`, `D-11`, `D-13`, `GATE-16`), plus frontend `D-10` and manual QA `GATE-13`/`GATE-15`/`GATE-20` before any cutover decision.
3. Optional subsequent offline geometry frontiers (`curved-capability.md` §9): polyhedron–cylinder/cone inscription (`Group 7` / prism–cylinder in `Group 8`), standalone pyramid/cone frustum (`Group 10`), and Oxyz coordinate input (`Groups 17–18`).

---

## Tenth continuation (Owner Master Task: student natural-language understanding), 2026-11-01

Offline only; `MAX_AUTHORIZED_LIVE_REQUESTS = 0`; 0 provider calls. `DEFAULT_MODE = "LLM_ONLY"` and `CACHE_VERSION = "131"` unchanged; 0 edits to `frontend/`, `semantic_program/` or `adapter3_simulation.py`. Report: `student-language-audit.md`.

| Commit | Content |
|---|---|
| `c9f54828` | Development probe `tools/student_language_probe.py` and its baseline at product `fa1ed277` (before any code change) |
| `020263cf` | SL-1 simulation-request reader, `_C_VUONG` / `_C_DOAN` wording, SL-2 `/2` honest exit + `route-d-clarification/1`, D02 empty base ⇒ `MISSING_DIMENSION` |
| `6637f6fd` | Registry /27, engine /19 (D-02 cache identity), preview identity delta |
| `d3dc97fc` | Probe after the fix, corrected baseline at `fa1ed277`, `phase-n` replay |
| `58888d7c` | Review round-1 fixes (B1 class words, B2 undrawn mentions, PE-1 dropped requests, SL-2 MINORs) |
| `35cac578` | Review round-2 fixes (anaphor-only reading, closed intersection operands, raw-source spans) |
| `fb67cfb2` | Review round-3 fix (anaphor noun ↔ its own call) — **final product commit** |
| `8b25df71` | Candidate re-frozen in its own commit (`runs/hybrid-master-student-language/` correcting `runs/hybrid-master-composite-relations/`) |

**Delivered on Route D `/4`** (registry /27, planner /22, engine /19; `student-language-audit.md`):
- SL-1: simulation requests are read by one closed reader that adds no fact (generic solid word + own notation, built points; opener only before the solid's attributes).
- SL-2: `typed-fact-next/2` honest exit `unresolved`; refused with AMBIGUOUS_FACT / OUT_OF_SCOPE and a server-built `route-d-clarification/1` record in `route_d.refusal`; frontend envelope unchanged; `/1` untouched; census extension +7 METADATA rows.
- D02: an unconstrained base is `MISSING_DIMENSION`. PE-1 (pre-existing): a request sentence no call answers is refused.

**Development probe (authored, offline, not held-out, not live)**, same probe before/after: on 60 shared gold rows SERVED_CORRECT 22 → 45, FALSE_REFUSAL 26 → 3, clarification 0 → 5, wrong class 2 → 0; 0 WRONG_SERVED before and after; adversarial 20/20 refused. Seven longer composition chains added after the fix are served exactly (52 served-correct of 67 gold rows in total). No planner (B), registry (C) or kernel (F) gap found.

**Independent review:** four rounds — NOT_READY (2 BLOCKER), NOT_READY (1 BLOCKER), NOT_READY (1 MAJOR), **READY** (0/0). Every finding is locked by a test.

**Gates:**
- Wave 3 67/72, 72/72 negatives refused (62 exact reason), 0 wrong-served, 0 transitions; locked 96/96; 203 probes 0 served negatives, 0 internal (`inventory-phase-n4.json`). Earlier curved, section, sphere, apex, base-centre, topology, measurement and composite probes identical to baseline.
- Candidate `8b25df71`: product `fb67cfb2`, 118 files `42347fbe…`, cache 131 (no bump); `--verify` matches.
- **Full T3 `FULL_PRODUCT_GATE_PASS`** on attempt 1 of `8b25df71` (`full-t3-8b25df71.json`): pytest 16324 passed, 0 failed; vitest 1424; build; demo 5/5; crash surface 6/6.
- Publication scan of `f986e897..HEAD`: PASS, 0 `Co-Authored-By` trailers.

**Status:** `ARCHITECTURE_CAPABILITY_PROGRESS` (student language); `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`; overall **`HYBRID_NOT_READY`**. Nothing merged or pushed.

**Open (recorded):** no-diacritic input refused at the domain gate on every route (`ISSUE-ARCH-ROUTE-D-DIACRITIC-FREE-INPUT`, Owner S-1); lowercase labels and tone typos unread; PE-2 solid-class word uncertified (`ISSUE-ARCH-ROUTE-D-SOLID-CLASS-WORD-UNCERTIFIED`); simulation requests on curved solids unread; live use of the honest exit unmeasured.

**Next exact action (one Owner decision point, `owner-go-request.md` + addendum):**
1. S-1: keep the domain gate, or authorize the diacritic-restoration slice (default-route behaviour change).
2. S-2: GO / defer for a live student-wording study (budget + author), separate from the locked protocol.
3. The existing live paired GO: name the corpus author; `--manifest` now prints the new `measured_system`.
Without these, the next offline item is PE-2 (solid-class certificate), with a RED test on its repro.

---

## Eleventh continuation (Owner Master Directive: Semantic Correctness, Generalized Planner Recomposition & Live Readiness), 2026-11-01: CHECKPOINT REACHED

Offline only; `MAX_AUTHORIZED_LIVE_REQUESTS = 0`; `MAX_AUTHORIZED_LIVE_SPEND_USD = 0`; `0` provider calls. Versions bumped to `geometry-functions/28`, `geometry-fact-planner/23`, and `geometry-function-engine/20`; `DEFAULT_MODE = "LLM_ONLY"` and `CACHE_VERSION = "131"` unchanged; `0` edits to `frontend/`, `semantic_program/`, or `adapter3_simulation.py`; locked schema/surface SHA-256 pins preserved (`flat = 485d3834…`, `v3 = 4bff35bb…`, Route A `= 7ea511a6…`, `TypedFact = aa9d93ee…`, `function_declarations = 5ceb0f99…`). Reports: `planner-recomposition-audit.md`, `s1-diacritic-free-offline-audit.md`, `s2-student-language-pilot-protocol.md`, `continuation11-adversarial-review.md`.

| Commit | Content |
|---|---|
| `9e059eb7` | PE-2 solid/2D shape-kind invariant certification (`doc_khang_dinh_loai_hinh` + `kiem_khang_dinh_loai_hinh`), unanswered-request refusal (`SOURCE_GOAL_UNANSWERED`), pre-placed non-degeneracy checks (`_dung_khong` / `_mot_buoc`), generalized `Point` descriptor `PlanningContract`s + auxiliary-plane recomposition + 2D `carrier_planes` perpendicular anchors (`_chon_moc_vuong_duong`) + `search_telemetry`, standalone `planning_oracle.py`, isolated `s1_diacritic_offline.py` & `score_s2_student_language_pilot.py`, Round 1–4 review fixes, and `results/historical-gold-delta.json` — **final product commit** |
| `ab5fabcc` | Re-export 41 Adapter `/2` preview fixtures with `search_telemetry` (`fixtures-adapter-2-search-telemetry/`; earlier bundles preserved byte-for-byte) |
| `69da35a1` | `phase-o` regression replay, `student-language-probe-c11.json`, `planner-recomposition-matrix.json`, audits, protocols, Round 4 `READY` review, and index updates |
| `800ab355` | Candidate re-frozen in its own commit (`runs/hybrid-master-semantic-planner-recomposition/` correcting `runs/hybrid-master-student-language/`) |

**Delivered on Route D `/4` and offline readiness tooling:**

- **Priority A — Semantic Correctness & PE-2 Closure (`ISSUE-ARCH-ROUTE-D-SOLID-CLASS-WORD-UNCERTIFIED` closed):**
  - `registry.py::doc_khang_dinh_loai_hinh` extracts premise-level 3D solid-class claims (`cube`, `cuboid`, `right_parallelepiped`, `parallelepiped`, `regular_prism`, `right_prism`, `oblique_prism`, `regular_pyramid`, `regular_tetrahedron`) and 2D polygon claims (`square`, `rhombus`, `rectangle`, `parallelogram`, `trapezoid`, `isosceles_trapezoid`, `right_trapezoid`, `regular_hexagon`, `equilateral_triangle`, `isosceles_triangle`, `right_triangle`, `right_isosceles_triangle`), binding prose solid symbols by ordered apex/base and lateral-edge correspondence (`_khop_ky_hieu_khoi`) and multi-solid coordination (`_day_khoi_cho_menh_de`).
  - `engine.py::kiem_khang_dinh_loai_hinh` certifies every extracted assertion in exact `Fraction` Gram arithmetic across root and sub-solids (`"Cho hình lập phương ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 3, AA' = 4."` deterministically refuses `INCONSISTENT_FACTS`; `41/41` in `test_route_d_semantic_shape_invariants.py`).
  - Unanswered / operand-less imperative requests (`"Vẽ hình rồi tính."`, `"Tìm."`, `"Xác định."`) refuse fail-closed with `SOURCE_GOAL_UNANSWERED` while preserving `SL-1` simulation-only requests (`student-language-probe-c11.json` identical to `student-language-probe-final.json`).
  - `engine._dung_khong` and `_mot_buoc` enforce positive squared lengths, non-zero area cross products, and non-collinear projection planes (`COLLINEAR_POINTS`) on pre-placed points.
- **Priority B — Generalized Planner Recomposition & Independent Planning Oracle (`planner-recomposition-audit.md`):**
  - Audited all 49 `REGISTRY` `FunctionSpec`s across 11 contract dimensions (`audit_registry_contracts()`).
  - Extended `Point` descriptor `PlanningContract`s in `registry.py` from 2 (`midpoint`, `centroid`) to all 6 general point constructors (`orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`), connected `_EffectResolver.point` to auxiliary planes (`MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`), generalized `_chon_moc_vuong_duong` over 2D `carrier_planes` and `perp_faces`, enforced independent Gram/affine postcondition verification in `_MO_TA`, and added explicit `search_telemetry` (`SOURCE_EXPLICIT_SEQUENCE` / `REGISTERED_DECOMPOSITION` / `DISCOVERED_FUNCTION_COMPOSITION`, `SEARCH_EXHAUSTED` budget guard).
  - Built standalone `backend/scripts/planning_oracle.py` (`0` imports from `planner.py`): on the 24-case `planner-recomposition-matrix.json`, `DISCOVERED_FUNCTION_COMPOSITION` increased `0 -> 9` (including §4.2 `"Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với (SBC)..."` without step hints, shared multi-goal intermediate reuse, derived perpendicular axes, and right prisms), `REACHABLE_BUT_SEARCH_MISSED` dropped `11 -> 2` (the remaining `D1`/`D2` cases require recursive/two-descriptor question fields beyond the locked flat `TypedFact` schema), `24/24` agree with the independent oracle and Exact Kernel, and `wrong_served = 0` (`26/26` in `test_planner_recomposition_oracle.py`).
- **Priority C — Isolated `S-1` Diacritic-Free Prototype & `S-2` Pilot Harness:**
  - `S-1`: `backend/scripts/s1_diacritic_offline.py` (`0` imports in `backend/app/`, `detect_domain` untouched) preserves 1-to-1 `norm_char_to_raw_span`, mixed-IME `_ascii_fold`, `verify_no_forged_quotes`, and `NEEDS_CLARIFICATION` flags on polysemous ASCII tokens (`goc`, `day`, `tam`, `canh`, `duong`) and lowercase solid notations (`16/16` in `s1-diacritic-development-corpus.json`, `6/6` in `test_s1_diacritic_free_offline.py`).
  - `S-2`: `backend/scripts/score_s2_student_language_pilot.py` + `s2-student-language-pilot-protocol.md` provide a deterministic 8-metric scorer (`ALLOW_LIVE_AI=0`, `0` live calls, `NOT_MEASURED`/`NOT_RECOVERABLE` preserved without coercing to `0`, `5/5` in `test_s2_student_language_pilot_harness.py`).

**Independent adversarial review** (`continuation11-adversarial-review.md`, subagent `76cc54fa-371c-4f90-80a2-36b259724296`): four rounds — Round 1 (`4 BLOCKER, 3 MAJOR, 1 MINOR, 1 NIT`), Round 2 (`3 BLOCKER, 1 MAJOR, 1 MINOR`), Round 3 (`READY`, `0 BLOCKER, 0 MAJOR, 1 MINOR, 1 NIT`), Round 4 **`READY`** (`0 BLOCKER, 0 MAJOR, 0 MINOR`; `NIT-R3-1` closed by candidate freeze `800ab355`).

**Gates:**
- **Wave 3 (`inventory-phase-o.json`, `wave3-phase-o.json`):** `67/72` served correctly; `72/72` negatives refused (`62` exact reason); `0` wrong-served; `0` transitions.
- **Locked 96:** `96/96`, `0` wrong-served.
- **203 probes:** `0` served negatives, `0` internal errors (same 12 curved `REFUSED -> REFUSED` transitions).
- **Registered curved controls:** `32/32` remain `REFUSED`.
- **Student-language probe (`student-language-probe-c11.json`):** `52` `SERVED_CORRECT`, `5` `NEEDS_CLARIFICATION_CORRECT`, `3` `FALSE_REFUSAL`, `7` `CORRECT_REFUSAL`, `20/20` adversarial `SAFE_REFUSAL`, `0` `WRONG_SERVED` (identical to `student-language-probe-final.json`).
- **Preview fixtures (`fixtures-adapter-2-search-telemetry/`):** `41/41` regenerated identically from `POST /api/preview/hybrid` (`test_hybrid_preview_fixtures.py` `6/6`).
- **Candidate:** `800ab355`, product `9e059eb7`, `118` files `184c64ff1810ec20…`, cache `131` (no bump); `freeze_evaluation_candidate.py --verify` matches.
- **Full T3:** `FULL_PRODUCT_GATE_PASS` on attempt 1 of `800ab355`, on fresh detached worktree `hm-t3-800ab355` (`full-t3-800ab355.json`): pytest `16408` passed (`0` failed, `7` skipped, `2` deselected, `15` xfailed), vitest `84` files / `1424` passed, production build `PASS`, demo replay `5/5`, crash surface `6/6`.
- **Publication scan** of `f986e897..HEAD`: `PASS` (`scanned=623`, `messages=82`, `violations=0`, `0` `Co-Authored-By` trailers).

**Status:** `ARCHITECTURE_CAPABILITY_PROGRESS` (PE-2 closed + generalized planner recomposition); `OFFLINE_BACKEND_READY_FOR_LIVE_EVALUATION`; overall **`HYBRID_NOT_READY`**. Nothing merged or pushed.

**Next exact action (one consolidated Owner decision point, `owner-go-request.md`):**
1. **Live paired evaluation GO (`D-04`, `D-11`, `D-13`, `GATE-16`):** name the independent 60-problem corpus author and provide the Owner approval JSON binding candidate `800ab355` (`tree_hash = 184c64ff1810ec20af5f5ba1451cfcac082de65876fbf8bbfc63a7f012afe26d`, product `9e059eb7`).
2. **Optional `S-2` live student-language pilot (`<= 36` requests):** authorize the 6 parameters in `s2-student-language-pilot-protocol.md` §4, or defer.
3. **Policy decision `S-1` (diacritic-free input):** keep the current domain gate, or authorize integrating a `route-d-clarification/1` confirmation flow backed by `s1_diacritic_offline.py` (never silent guessing).
4. **Optional curved grammar rulings (`P-1`, `P-2`, `P-3`):** if repinning the 8 legacy curved fixtures is desired.

---

## Twelfth continuation (Owner Master Directive: real-world generalization, live validation & production readiness), 2026-11-01: CHECKPOINT REACHED — `OFFLINE_READY_AWAITING_OWNER_GO`

Offline only; `0` provider calls; `USD 0`. **No Owner approval file exists**, so no live call was made (the directive itself is not a spending approval, §V). `0` edits to `backend/app`, `frontend/`, schemas or prompts: candidate `800ab355` (product `9e059eb7`, 118 files `184c64ff…`) still verifies and still binds every approval. `DEFAULT_MODE = "LLM_ONLY"`, `CACHE_VERSION = "131"`.

**Restored from Git:** branch HEAD `e466deca` matched the handoff; tree clean; `main` (`f986e897`) is an ancestor; `freeze_evaluation_candidate.py --verify` matches.

**Delivered:**
1. **S-2 made runnable (it was not):** the protocol had a scorer but no corpus and no code that turns a route outcome into its records.
   - `s2-student-language-pilot-corpus.json` (36 = 6 strata × 6; 21 reused from the C10 probe with its gold and hand expectations, 15 new; hand oracles cross-checked against the probe's own; sha `3f1682bd…`).
   - `backend/scripts/run_s2_student_language_pilot.py`, reusing the paired harness's budget, send guard and transport; test file with 28 tests, 5 injected faults all caught.
   - The mock live tests caught a real defect before any spend: the scorer refuses to run under `ALLOW_LIVE_AI=1`, so a paid run would have lost its summary. The runner now clears the flag around the pure scorer call; the scorer is unchanged.
   - Gold replay (`s2-pilot-gold-replay.jsonl`): 8 metrics all perfect, yet end-to-end is only **33/36**. The scorer has no false-refusal count, so the runner adds `supplementary` and a per-row `attribution` by gold reproduction (protocol §5).
   - The 3 false refusals are Source Gate gaps on the **gold** extraction: `k/c`, `mp`, `đt`, and "hình chop" (`ISSUE-ARCH-ROUTE-D-STUDENT-SHORTHAND-UNREAD`). They are recorded, not fixed: a fix would change the candidate that approvals bind to.
2. **Correction of the C11 `/4` planner claim** (`planner-recomposition-route-d4-correction.md`, `route-d4-representation-probe.json`):
   - The 9 discovered compositions are real on the flat route B only.
   - On `/4`, a goal or section plane with an unnamed described point is refused (`INVALID_MATH_GOAL` / `INVALID_QUALIFIED_REF`), and 0 of 52 served `/4` gold rows are `DISCOVERED_FUNCTION_COMPOSITION`.
   - D1, D2 and the 9 C cases are `REPRESENTATION_BLOCKED` on `/4`, not search misses. Two named controls are served, both hand-checked (2√6/3, 3√2/2).
   - Usage evidence: 3/60 problems in the blind-agent NLU corpus (`described-point-usage-scan.json`; an earlier unreceipted 2/60 was a case-sensitive filter miss); 0/220 in Waves 2–3. Not implemented: it would change the Hybrid model surface; Owner decision R-1 (`ISSUE-ARCH-ROUTE-D4-UNNAMED-DESCRIBED-POINT-GOAL`).

**Tests run this continuation:** listed in the commit; no Full T3, because no product change was made.

**Verified capabilities (this checkpoint):** unchanged from C11 on `/4` for named chains + 2 registered decompositions; route-B discovered composition as C11 measured it.
**Unsupported / blocked on `/4`:** unnamed described points (R-1), nested descriptors (D1), student shorthand (SL-3), diacritic-free input (S-1).
**Not measured:** every live metric: S-2, live paired, latency, cost, real student wording.
**Open blockers (Owner only):** S-2 GO; R-1; SL-3 timing; the paired corpus author; S-1; integration permission. All are in `owner-go-request.md` (twelfth-continuation addendum).
**Git:** `INTEGRATION_PENDING_OWNER_GO`. Nothing merged or pushed; the worktree is kept.

**Next exact action:**
- Owner decides S-2 / R-1 / SL-3, plus the paired author.
- With a valid S-2 approval file: `run_s2_student_language_pilot.py --live --approval-file <file>`, once, then an independent review of the results.
- Without one: no offline item in this epic is blocked except by those decisions.

**Review round 1 of this continuation** (fresh-context, after `5e613816`): verdict `NOT_READY` — 0 BLOCKER, 3 MAJOR, 6 MINOR, 8 NIT.
- **Fixed, each locked by a test and an injected fault (runner tests 28 → 41):**
  - M1: a reversed segment no longer turns a correct serve into a wrong-serve.
  - M2: an inconsistent case must be refused as `INVALID_DATA`.
  - M3: the deterministic layer is blamed only when gold ends the same way.
  - m1: NaN or ≤ 0 terms are refused.
  - m3: unknown spend is reported as `UNKNOWN`.
  - m4: the usage scan now has a tool and a receipt. It found 3/60, not 2/60: the first count's filter was case-sensitive.
  - m5: wording.
  - m6: the approval is now a `PENDING_OWNER_DECISION` template plus one blob-keyed command, dry-run with a non-approval value.
- **Kept on purpose:** m2. Tests never write the approval value.
- Protocol §5.8 lists the changes. The new runner sha is `d5a923bf…`. The gold replay `s2-pilot-gold-replay-r1.jsonl` replaces the first one and is unchanged in result (33/36, 0 wrong-served).
- **Found while checking:** a literal BACKSPACE byte in a bridge regex (`ISSUE-ARCH-ROUTE-D-BRIDGE-LITERAL-BACKSPACE-REGEX`). It is a product defect, impact `NOT_MEASURED`; it will be fixed with the next product change.
