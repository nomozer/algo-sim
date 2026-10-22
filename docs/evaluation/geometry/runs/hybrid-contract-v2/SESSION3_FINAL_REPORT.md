# SESSION3_FINAL_REPORT.md — Backend Hybrid Session 3 (`hybrid-contract-v2`)

- **Run Slug**: `hybrid-contract-v2`
- **Authorization**: `GO_HYBRID_SESSION3_CONTRACT_V2_LOCAL_RESEARCH` (`D1 GO`, `D2 GO-conditional`, `D3 GO`, `D4 KEEP 32`, `D5 GO`, `D6 GO-limited`)
- **Branch**: `research/hybrid-backend-session3-contract-v2`
- **Worktree**: `D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-backend-s3`
- **Base Commit (Session 2 HEAD)**: `227d447f5c1ca55a2c4bd68f3c8c583228902cfc`
- **Final Product Commit**: `541803c867adfbc5e85a8109bd0307552090f9df` (`541803c8`)
- **Measured Product Tree (`backend/app`, 116 files)**: `173af8b2604dde4754a602eb868ceb07f8129263f7b80aa9601a9a203aec51d9`
- **Evaluation Classification**: `DEVELOPMENT_EVALUATION_NOT_BLIND` (`0` live provider calls, `ALLOW_LIVE_AI = 0`)

---

## 1. Executive Summary & Handoff Continuation Audit

Session 3 resumed and completed the Backend Hybrid Contract V2, Unified Source Authority, and Planner Migration campaign from Claude Opus 5.5 (`3d7d3f6b` $\to$ `fe6ad30b` $\to$ `4268f4e2` $\to$ `fa1599c6` $\to$ `42f19eec` + uncommitted `P4b` grammar work at the `match: 42 / SERVE: 19/22` checkpoint).

### 1.1 Exact Diagnosis of the Claude Mid-Session Checkpoint (`match: 42`, `SERVE: 19/22`)
1. **What `G7` was**: Closed grammar rule `G7` (`registry.py` + `planner.py`) admitting a section cut clause that redundantly includes the plane's own through-point edge (`"Mặt phẳng (α) qua M ... cắt SA, SB, SC lần lượt tại M, N, P"`, where `M` is already defined on `SA`), reusing `M` at cost `0` (`reuse_through_point`) while recording `stated_point: "M"` so `registry._kiem_dinh_cat` validates the full stated cut list.
2. **Locked set size & pre-evaluation lock**: `grammar-set.json` has **`47` cases** (`22` `SERVE`, `19` `REFUSE_SOURCE`, `4` `REFUSE_GEOMETRY`, `2` `REFUSE_KERNEL`), locked at commit `4268f4e214125fe20c858930bc92b0c5798dfc67` with `SHA-256 = 10c57be7b485d7b3f1a97183ff41b28988e70641e297e01cccf68d1434cc4abe` before any grammar code was written.
3. **Why `3` positive cases (`19/22`) were not yet `SERVED` when Claude hit the session limit**:
   - `PARA-3` (`QUESTION_CONTEXT_UNSUPPORTED`): `"Qua M dựng mặt phẳng (α)..."` contained `"dựng"` at offset `6` inside the already-covered construction span `(0, 44)`; `cover(0, 6)` in `_kiem_du_kien_cau_hoi` checked full containment `a <= x < y <= b` instead of partial overlap `max(a, x) < min(b, y)`.
   - `CORPUS-DEV09-construct` (`SOURCE_PREMISE_UNREAD`): `"Gọi P là điểm trên cạnh BB' sao cho BP = BB'/3."` used `"trên cạnh"` + slash fraction `"BB'/3"`, and `"Dựng thiết diện của hình chóp S.ABC cắt bởi mặt phẳng (α)."` omitted `"từng bước"`.
   - `CORPUS-DEV10-prism-area` (`SECTION_PLANE_NOT_COMPILED`): In `engine.py`, `self.calls` is sorted by `c.fn` where `"ask_section_area" < "section"`. In `_bien_dich_mat_cat` (`engine.py:1444`), iterating `self.of("section", "ask_section_area")` visited `g_area` before `sp`, naming the section plane `mp_td_g_area` instead of `mp_td_sp`.
4. **Post-fix result on the untouched locked set (`after-p4b-grammar.json`)**:
   - `SERVE`: **`22/22` (`100%`)** with exact oracle answers (`wrong_served: []`, `served_without_gate: []`)
   - `REFUSE_GEOMETRY`: **`4/4`**
   - `REFUSE_KERNEL`: **`2/2`**
   - `REFUSE_SOURCE`: **`18/19`** (`NEG-per-edge-same-name` refused earlier at the `/2` schema boundary `DerivedPlaneSectionSpecV2` with `INVALID_DERIVED_SECTION` $\to$ `REFUSE_OTHER`, pinned by `test_v2_section_shape_is_closed`)
   - Binary serve/refuse accuracy: **`47/47` (`100%`)**; exact category match: **`46/47` (`97.9%`)**.

---

## 2. Implementation Summary Across `P1`–`P8`

| Phase | Owner Decision | Deliverable & Verification Receipt |
|---|---|---|
| **P1** | Input & Fault Safety | `_ARGS_LOI` / `_kiem_args` in `typed_fact_next.py` (`INVALID_PREMISE_ARGS`); technical fault catch (`ADAPTER_INTERNAL_ERROR` / `ROUTE_INTERNAL_ERROR`) in `adapter3_simulation.py`, `adapter4_route.py`, `function_route.py`. Fuzz receipts: `verification/fuzz/p1-adapter3.json` & `p1-planner.json` (`500` cases each, `0` crashes). |
| **P2** | `D1 GO`, `D5 GO` | Canonical `typed-fact-next/2` (`StatedIntersectionSpec`, `DerivedPlaneSectionSpecV2`, `TypedFactNextPayloadV2`, `parse_typed_fact_next_v2`) and explicit route-labeled converter `convert_v1_to_v2(raw, route="bridge"\|"adapter3")` (`ROUTE_LABEL_REQUIRED`, `SCHEMA_VERSION_MISMATCH`). |
| **P3** | `D6 GO-limited` | `PlanningContract` on `REGISTRY["intersect_line_plane"]` (`effect=Meet`, `fresh="I"`); cost-0/1/2 candidate selection in `planner._dinh_cat_canh` (`derived_fresh` only when closed boundary required); engine closure certificate `chung_chi_khep_kin` (`same_section_cycle`); internal label stripping `_an_dinh_thiet_dien_phu`. Fuzz receipt: `verification/fuzz/p3-v2.json` (`500` cases, `0` crashes). |
| **P4a/b** | `D2 GO-cond`, `D3 GO` | Locked 47-case `grammar-set.json` (`4268f4e2`, `10c57be7...`); closed Source Gate grammar `G1`–`G7` in `registry.py` + `planner.py`; section-before-area plane ownership in `engine._bien_dich_mat_cat`. Receipts: `verification/grammar/baseline-before-grammar.json` (`10/22` SERVE) $\to$ `verification/grammar/after-p4b-grammar.json` (`22/22` SERVE, `46/47` match). |
| **P5** | `D1 GO`, `D2 GO-cond`, `D5 GO` | `backend/app/ai/adapter4_route.py` (`ADAPTER_V4_VERSION = "hybrid-simulation-adapter/4"`, `ROUTE_D_SIMULATION_V4_SCHEMA_VERSION = "hybrid-route-d-simulation/4"`, `run_typed_fact_next_v2_route`) delegating exclusively to `bridge_v2` + planner + engine with `100%` `registry.kiem_nguon` authority (`0` legacy substring fallback). |
| **P6** | `D4 KEEP 32` | IR budget audit confirming `MAX_MEMORY_DECLARATIONS = 32` unchanged; `gop_doi_tuong_trung` keeps `plane_constructions_per_section = 1.0` and `18–30 <= 32` declarations across all 3- and 4-sided pyramid/prism section plans while hexagonal pyramids (`33–36`) deterministically refuse with `IR_MEMORY_BUDGET_EXCEEDED`. |
| **P7** | Offline Evaluation | `evaluate_session3.py` across Families A–H (`verification/evaluation/session3-evaluation-summary.json` & `session3-evaluation-full.json`): `0` `wrong_served` across all `562` evaluations. |
| **P8** | Independent Review & Full T3 | Read-only subagent review (`61217726-a797-4a91-b722-e4393c7e11c9`), remediation of `I-1` (`541803c8`) and `I-2` (`EVALUATION_CANDIDATE.json` refreeze), and authoritative clean detached Full T3 gate (`FULL_PRODUCT_GATE_PASS`). |

---

## 3. Comprehensive Offline Evaluation Summary (`session3-evaluation-summary.json`)

| Family | Description | Cases | Key Results | `wrong_served` |
|---|---|---:|---|---:|
| **Family A** | Locked `/2` Grammar & Contract Set (`10c57be7...`) | `47` | `22/22` `SERVE` (exact oracle match), `18/19` `REFUSE_SOURCE` (`+1 REFUSE_OTHER` at schema boundary), `4/4` `REFUSE_GEOMETRY`, `2/2` `REFUSE_KERNEL`, `0` served without gate | `0` |
| **Family B** | Session 1 Replay & `/1` vs `/2` Dual-Run | `60` | `/1` Bridge: `49/49` served (`43/43` exact answers); `/2` Adapter `/4`: `49/49` agree `100%` + `S-open-cycle` newly served (`50` served, `50/50` valid scenes, `0` label leaks, `100%` `registry.kiem_nguon`), `6/6` invalid refused | `0` (on `/1` Bridge & `/2` Adapter `/4`) |
| **Family C** | Contract Parity Grid (`ABC`/`ABCD`, `∥`/`⊥`, `t`, all `cut` subsets) | `316` | `/1` Bridge `36`, `/2` from Bridge `36`; `/1` Adapter `/3` `20`, `/2` from Adapter `/3` `20`; `0` route disagreements | `0` |
| **Family D** | Metamorphic Invariance (permutation, relabel, goal order, paraphrase) | `33` | `1/1` ref, `24/24` premise permutation, `2/2` relabel, `1/1` goal order, `5/5` paraphrase (`33/33` across `/1` Bridge, `/1` Adapter `/3`, `/2` Adapter `/4`) | `0` |
| **Family E** | Adversarial Negative Controls (`10 × 2` conventions) | `20` | `/1` Bridge: `0/20` served; `/1` Adapter `/3`: `1/20` served (`N-anonymous-ratio-operand-triangle/convention`); **`/2` Adapter `/4`: `0/20` served (`100%` refused)** | `0` (on `/2`) |
| **Family F** | IR Budget (`D4 KEEP 32`) & Planner Composition | `8 + 38` | `6/8` (3- & 4-sided bases) `SERVED` (`24–30 <= 32` decls), `2/8` (hexagon) `REFUSED` (`IR_MEMORY_BUDGET_EXCEEDED`, `33–36` decls); `38` plans: `0` duplicate calls, `1.0` plane/section | `0` |
| **Family G** | Adapter `/3` Dev Corpus Raw Dual-Run (`corpus-dev.json`) | `16` | `/1` Adapter `/3`: `7` SERVED (legacy fallback), `9` REFUSED; `/2` raw un-reauthored: `16/16` REFUSED (re-authored `/2` equivalents in Family A: `5/5` positive SERVED, `2/2` negative REFUSED) | `0` |
| **Family H** | Route-B Compiler Benchmark (`30 × 2` arms) | `60` | `38` `correct_served`, `18` `correct_refusal`, `4` `false_refusal` (locked capability gaps) | `0` |

---

## 4. Companion Reports in `docs/evaluation/geometry/runs/hybrid-contract-v2/`

1. [`CONTRACT_V2_IMPLEMENTATION_REPORT.md`](CONTRACT_V2_IMPLEMENTATION_REPORT.md) — Canonical `typed-fact-next/2` schema, `convert_v1_to_v2`, `bridge_v2` `/2`, and `Adapter /4`.
2. [`SOURCE_GATE_COVERAGE_MATRIX.md`](SOURCE_GATE_COVERAGE_MATRIX.md) — Locked 47-case evaluation set, closed grammar `G1`–`G7`, and resolution of the 3 mid-session cases.
3. [`PLANNER_COMPOSITION_AND_REUSE_REPORT.md`](PLANNER_COMPOSITION_AND_REUSE_REPORT.md) — Bounded `D6` section-vertex derivation (`PlanningContract` on `intersect_line_plane`), closure certificate, and `D4 KEEP 32` IR budget audit.
4. [`BACKEND_MIGRATION_READINESS.md`](BACKEND_MIGRATION_READINESS.md) — Assessment of `S3-1..7`, `D-01..13`, and `GATE-01..20`.
5. [`INDEPENDENT_REVIEW.md`](INDEPENDENT_REVIEW.md) — Read-only subagent quality gate audit (`61217726-a797-4a91-b722-e4393c7e11c9`) and `I-1`/`I-2` remediation.
6. [`SESSION3_RESUME_STATE.md`](SESSION3_RESUME_STATE.md) — Takeover and completion state ledger.
