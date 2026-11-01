# Task 3 (offline part) — entry points, migration ledger and gate reassessment

Read from the code at `e33ae978`. Nothing has been retired, and no production routing has changed.

## Production entry points

| entry point | orchestrator today | reaches Hybrid /4? |
|---|---|---|
| `POST /api/analyze` (`main.py`), default | `ai/pipeline.py::run_pipeline`, `LLM_ONLY`. LLM `stage_semantic_program` synthesis, then the deterministic gates. Compiler C is wired through `quyet_dinh_dinh_tuyen` but is `DISABLED` under `LLM_ONLY`. | **No.** The default path's import closure excludes Route D (`test_structured_geometry_relations.py::test_Y_*`, D-01). |
| `POST /api/analyze`, declared opt-in `HYBRID_V2_LOCAL=offline-replay` + loopback | `main._analyze_hybrid_v2_local` → `hybrid_offline` (recorded TypedFactNext /2 extraction) → /4 route → adapter /4; Route D cache (D-02) | **Yes**, offline replay only. There is no live extractor. *Correction (Phase B): the first version of this table missed this pre-existing Stage 2 branch.* |
| `POST /api/image/extract` | `ingestion/image*.py` transcribes the problem; the reviewed text then goes to `/api/analyze`. | No. It has no geometry orchestration of its own. |
| `POST /api/preview/hybrid` | `ai/hybrid_preview.py`. Operator-only: flag, token, loopback, no `Origin`. Offline fixtures only. | Preview of Route D only; not production. |
| `GET /api/diagnostics/*`, `/api/health` | identity and diagnostics | No; they only report policy. |

So there are **three** orchestrators today:
- LLM_ONLY synthesis, the production default;
- compiler C, opt-in and disabled;
- Route D: /4 offline replay on the declared `/api/analyze` opt-in, plus the operator preview. The contract requires one production orchestrator at cutover. That has **not** been reached.

## Migration ledger

| OLD_COMPONENT | NEW_OWNER | LAST_CONSUMER | PARITY_EVIDENCE | REMOVAL_STATUS |
|---|---|---|---|---|
| `pipeline.stage_semantic_program` (LLM program synthesis) | Route D: `typed_fact_next_extraction` → bridge → planner → engine → `adapter4_route`, via the declared `/api/analyze` opt-in | `run_pipeline` ← `/api/analyze` (production default) | Offline only: Wave 3 replay 67/72, locked 96/96, the measurement probe and recomposition evidence. **Live paired differential (D-11): NOT_MEASURED.** | **ACTIVE.** Cannot retire before D-11 and cutover. |
| `geometry_compiler/` (six-family compiler C, `GEOMETRY_COMPILER_MODE`) | Route D planner (Registry effect search) | `pipeline.py` (routing gate) plus 7 `backend/scripts/*` diagnostics | **None.** No corpus exists in both `RequestContract` and TypedFactNext form. | **ACTIVE (opt-in, disabled).** |
| Adapter /3 (`function_route.run_typed_fact_next_route` and its wrapper `ai/adapter3_simulation.py`) | `adapter4_route.py` | Wrapper: 10 test modules only (no `app/` or `scripts/` importer). /3 route: test suites and shared schema/engine code. | **Partial.** Polyhedral parity is the /4 inventory. Curved solids and qualified identity: /4 refuses them by design, so there is no parity. | **ACTIVE.** /3 is the only curved-solid owner. |
| Preview flat-facts contract (`hybrid_preview.run_preview` → `run_ai_fact_route`) | the same `run_fact_route` → planner → engine; /4 TypedFactNext is the target contract | `/api/preview/hybrid` (operator), 41 locked fixtures, `HYBRID_PREVIEW_FRONTEND_CONTRACT.md` | The shared downstream is the same code, so no parity is needed there. The input contract differs (D-04: flat is the product contract; v3 NO-GO). | **ACTIVE.** Locked product contract, not a duplicate authority. |
| `ai/function_calling.py` (route D branch A: AI chooses the function) | branch B: facts + deterministic planner | `fact_extraction.py`, `typed_fact_next_extraction.py` (reuses `_openapi` only), A/B scripts | — | **ACTIVE as a library.** Its schema helper is a live dependency. |
| bridge private identity copy | `typed_fact_next.py::canonical_vertex_ref` | none | `test_bridge_ownership_resolves_identity_through_the_one_canonical_resolver` + identity suites (3384 passed) | **REMOVED** (Task 1, `7bf0a3ab`) |
| Route D "never cached" special case on `/api/analyze` | Route D cache identity (`prepare_local_replay.cache_key` + `ROUTE_D_CACHE_POLICY`) | — | `test_hybrid_route_d_cache_and_rollback.py`, `test_hybrid_v2_local_analyze.py` | **REPLACED** (Phase A, `e9c9b8e9`) |

## Retirement status (Owner vocabulary, 2026-10-31)

| component | status | reason |
|---|---|---|
| Bridge private identity copy | `RETIRED` | Replaced by `canonical_vertex_ref`. The architecture review found the only behavior change (M-1), which aligns with the Owner-registered R2 oracle and is pinned. |
| Route D "never cached" special case | `RETIRED` | Replaced by the Route D cache identity (D-02). |
| LLM_ONLY program synthesis (`stage_semantic_program`) | `PENDING_PARITY` | The production default. Retire only after the live paired GO criteria pass (protocol §7) and cutover. |
| Compiler C (`geometry_compiler/`) | `PENDING_PARITY` | Opt-in and disabled. No corpus exists in both `RequestContract` and TypedFactNext form; a parity corpus is needed before removal. |
| Adapter /3 (`run_typed_fact_next_route`, `adapter3_simulation.py`) | `RETAINED_WITH_REASON` | The only curved-solid owner. /4 refuses curved solids and qualified multi-solid identity by design (confirmed again by the architecture review). |
| Preview flat-facts contract (`/api/preview/hybrid`) | `RETAINED_WITH_REASON` | A locked operator/frontend contract with 41 fixtures, sharing the same downstream. It is not a duplicate authority. |
| `function_calling.py` | `RETAINED_WITH_REASON` | A live library dependency (`_openapi`, `live_transport` used by the harness). |

`LEGACY_RETIRED` is **not** claimed: LLM_ONLY is still the active production path.

## Gate reassessment (`docs/MIGRATION_CHECKLIST.md`)

**Route D gates (D-01…D-13)** are the gates relevant to Hybrid replacement.

| status | gates |
|---|---|
| PROVED | D-01, D-03, D-05, D-06, D-09; **D-02 and D-12 offline (Phase A, `e9c9b8e9`)** |
| PROVED for preview only | D-07, D-08. The `/api/analyze` opt-in serves the /4 envelope offline; production enablement is still D-13. |
| OPEN | D-10: presentation from certificates is frontend-owned and out of scope for this backend-only epic |
| BLOCKED | D-04 (flat is the product contract; a NEW pre-registered held-out set is needed), D-11 (paired live measurement), D-13 (`NO-GO`) |

This epic changes no gate status. Its new evidence:
- extraction source references, for D-04 provenance;
- one identity authority, for D-05 safety;
- a measured /4 inventory with independent controls, for D-05.

**Section 1 gates (GATE-01…20)** were written for compiler C. GATE-13 canary, GATE-15 holdout, GATE-16 tokens and latency, and GATE-20 user study all need live or human measurement and are `NOT_STARTED` / `NOT_MEASURED`.

## Cutover blocker (Owner decision)

Production cutover needs a measured real-text extraction quality on a new pre-registered held-out set (D-04), plus a paired live differential, reliability, latency and token/cost run against LLM_ONLY (D-11, GATE-16). The contract states: "No live budget is currently authorized." Without these, switching `/api/analyze` to Hybrid would be a mode-name change with no acceptance evidence, which the contract forbids. Retiring LLM_ONLY synthesis is therefore blocked as well.

**What an Owner GO must state:** provider and model; the maximum number of calls and the cost; stop rules; the held-out construction (independent author, pre-registered before any prompt or schema change); `MEASUREMENT_CLASS`, `HELD_OUT_CLAIM` and `EVALUATOR_INDEPENDENCE`.

## Offline work that can continue without a budget

- **D-02:** Route D cache identity (route-aware cache keys, two-way MISS tests).
- **D-12:** rollback tests.
- An opt-in `/api/analyze` Hybrid route behind a **declared** gate (D-01: "cổng nối phải được KHAI"), with an injected extractor and no silent fallback. It stays off by default, and `LLM_ONLY` must stay byte-identical.
- **Adapter /3 → /4 parity:** fail-closed curved support in /4 only with certified exact curved geometry.

**Fourth continuation (2026-10-31):**
- **M-3 closed** (`14155201`): a doubly-faulted adapter returns a typed technical refusal, not HTTP 500; any fault of ours past argument validation is `ROUTE_INTERNAL_ERROR`. There is still no fallback to LLM_ONLY.
- **Parity:** LLM_ONLY's "lần lượt" projection grounding (W18) now exists on Route D (registry /22).
- **Remaining parity gap blocking retirement:** curved solids. Adapter /3 and LLM_ONLY serve them; /4 refuses them.
- **Unchanged:** retirement statuses and gate states D-01…D-13.

**Fifth continuation (2026-10-31): curved solids on /4.**
- **Served on /4:**
  - cylinder, cone and sphere: volume, lateral area, sphere surface, radius;
  - the total area of a cylinder or cone (exact, or `EXACT_DOMAIN_EXCEEDED`);
  - a cone height derived from its slant;
  - the symbolic unit a.
- **Grounding:** a closed clause grammar. The independent review is READY after 3 rounds.
- **Parity with Adapter /3: PARTIAL.** Adapter /3 still owns:
  - sections parallel to the base and axial sections;
  - the cone volume ratio / remaining volume.
- **Retirement:** Adapter /3 and LLM_ONLY are not retired on curved problems.

**Sixth continuation (2026-10-31): curved sections and cone ratio on /4.**
- **Now `SUPPORTED_BOTH` on /3 and /4:**
  - sections parallel to the base (cylinder, cone) at a distance from the base;
  - axial sections;
  - the cone volume ratio and remaining volume.
- **Only on /4:** the derived height, the total area, and the canonical pose.
- **Partial or still only on /3:**
  - an arbitrary ratio from the apex (/4 reads only the midpoint wording);
  - a plane given by an equation, and ellipse sections;
  - the wordings "tâm đáy O" and "tâm đáy dưới/trên".
- **Sphere sections:** unsupported on /4; they need a contract field.
- **Retirement:** Adapter /3 is still not retired for curved problems.

**Seventh continuation (2026-10-31): registered contract audit, base-centre grammar, apex ratio k, sphere sections (commit `6e0a6c2c`).**

- **Now `SUPPORTED_BOTH` on /3 and /4:**
  - an arbitrary ratio from the apex, k = SM/SO, including OM/OS converted by the gate;
  - the wordings "tâm đáy O" and "tâm đáy dưới/trên".
- **On /4 under a new contract kind:** sphere sections at a distance from the centre and through the centre.
  - Adapter /3 serves spheres only through `plane_equation`, which needs coordinates, and the registered sphere controls use
    exactly that.
  - Status: REPRESENTABLE_AND_PROBED until the independent review returns READY.
- **Still only on /3:**
  - a plane given by an equation;
  - ellipse sections;
  - coordinated question lists (P-1);
  - several sections in one run (P-2).
- **Retirement:** Adapter /3 is still not retired for curved problems. The 8 curved fixtures still refuse on /4, because of
  P-1, P-2 and an unordered ratio question.

## Update after eighth continuation (`44a0b79e`, 2026-10-31)

- **Role-phrase Source Gate parity (`/4`):** `_C_VAI` + `_cua_khop` accept explicit solid nouns without `"của"` while delegating prism-subclass checks to `_loai_cum_dung` (`test_route_d_role_phrase_parity.py`).
- **Pedagogical construction trace (`/4`):** `preconditions` and `postconditions` are exported on `KetQuaTuyen.trace` and `route_d.construction_trace` (`_gan_dieu_kien_vet`), stripped of post-execution kernel claims on all `REFUSED` paths (`test_route_d_pedagogical_trace.py`). Frontend trace presentation remains part of D-10.
- **Certified circumscribed spheres of polyhedra (`/4`):** additive `SolidSpec.circumscribes` on `typed-fact-next/2`, exact `Fraction` Gram circumcenter + all-vertex cosphericity certificate (`NO_CIRCUMSCRIBED_SPHERE`), exact `Fraction` Cholesky Euclidean chart normalization (`chuan_hoa_euclid`), G4 IR perpendicular-bisector construction, independent closed-form cross-check, and closed Vietnamese Source Gate grammar (`circumscribed_sphere_probe.py` `12/12` pos + `12/12` neg; `circumscribed-spheres-review.md` Round 2 `READY`; `inventory-phase-l2.json` Wave 3 `67/72`, `72/72`, `0` wrong-served, `96/96` locked, `203` probes clean).
- **Retirement & live gates:** unchanged — Adapter `/3` and compiler `C` remain unretired (not expanded for circumscribed spheres), `DEFAULT_MODE = "LLM_ONLY"` and `CACHE_VERSION = "131"` are untouched, and D-04 / D-11 / D-13 / GATE-16 await the Owner live GO.

## Update after ninth continuation (`fa1ed277`, 2026-11-01)

- **Multi-object FactGraph & generalized geometric relations (`/4`, Registry `/26`, Planner `/22`, Engine `/18`, `geometric-relation-certificate/1`):**
  - Additive `typed-fact-next/2` contract (`GeometricRelationSpecV2` kinds `circumscribes`, `inscribed_in`, `tangent_to` + `contact_ref`; `SolidSpec.inscribed_in`), preserving `typed-fact-next/1` byte-for-byte compatibility (`schema-census-extension.json`, `test_scope_census_closure.py`).
  - Certified sphere inscribed in any convex polyhedron across **all** boundary faces (`_tam_noi_tiep_da_dien` over exact `Fraction` + `_QField` multiquadratic arithmetic, face coplanarity & convexity checks, strict inward half-spaces, strict `relint` face contacts, and independent $9V^2 = r^2 (\sum_k S_k)^2$ identity).
  - Certified sphere–plane tangency (`_chan_tiep_xuc_mat`, $d^2 = R^2$ vs. `PLANE_INTERSECTS_SPHERE_NOT_TANGENT` vs. `PLANE_DOES_NOT_TOUCH_SPHERE` + named contact verification), dual spheres (`(S1)`/`(S2)` and dual unnamed `"()"`), polyhedron section + sphere coexistence, multi-polyhedron `shared_faces` + sphere, and axial cylinder/cone + circumscribed/inscribed spheres (`_dung_cong_ghep`).
  - Explicit multi-object planner dependency DAG + `composition_classification` + 4-layer `relation_certificates` (`composite_relations_probe.py`: `17/17` pos + `19/19` neg; `composite-relations-review.md` Round 3 `READY`; `inventory-phase-m.json` Wave 3 `67/72`, `72/72`, `0` wrong-served, `0` transitions, `96/96` locked, `203` probes clean, `32/32` curved controls `REFUSED`).
- **Retirement & live gates:** unchanged — Adapter `/3` (`0` edits in Continuation 9) and compiler `C` remain unretired, `DEFAULT_MODE = "LLM_ONLY"` and `CACHE_VERSION = "131"` are untouched, and D-04 / D-11 / D-13 / GATE-16 await the Owner live GO.

## Update after tenth continuation (student language, 2026-11-01)

- **No legacy consumer changed.** The slice extends the Route D readers (Source Gate SL-1, `/2` honest exit SL-2, engine empty-base class D02; registry /27, engine /19). LLM_ONLY, compiler C and Adapter /3 are untouched; `DEFAULT_MODE = "LLM_ONLY"`, `CACHE_VERSION = "131"`.
- **New input to the cutover decision:** learner wording without diacritics is refused as out of scope by `detect_domain` on every route, the default included (`student-language-audit.md` §7). A live paired run on a corpus with such wording would show both arms failing at the same gate; the corpus author should know that.
- Retirement and live gates: unchanged (D-04 / D-11 / D-13 / GATE-16 await the Owner live GO).

## Update after eleventh continuation (`9e059eb7`, 2026-11-01)

- **Semantic correctness & PE-2 closure (`/4`, Registry `/28`, Planner `/23`, Engine `/20`):**
  - Premise-level solid-class and 2D polygon assertions (`cube`, `cuboid`, `right_parallelepiped`, `parallelepiped`, `regular_prism`, `right_prism`, `oblique_prism`, `regular_pyramid`, `regular_tetrahedron`, `square`, `rhombus`, `rectangle`, `parallelogram`, `trapezoid`, `isosceles_trapezoid`, `right_trapezoid`, `regular_hexagon`, and triangle classes) are extracted by `doc_khang_dinh_loai_hinh` and certified in exact `Fraction` Gram arithmetic by `kiem_khang_dinh_loai_hinh` (`test_route_d_semantic_shape_invariants.py` `41/41`; `ISSUE-ARCH-ROUTE-D-SOLID-CLASS-WORD-UNCERTIFIED` closed on the research branch).
  - Unanswered / operand-less imperative requests (`"Vẽ hình rồi tính."`, `"Tìm."`, `"Xác định."`) refuse fail-closed (`SOURCE_GOAL_UNANSWERED`) while preserving legitimate `SL-1` simulation-only requests (`"Vẽ hình chóp ..."`).
- **Generalized planner recomposition (`/23`) & independent oracle:**
  - `Point` descriptor `PlanningContract`s extended to all 6 general point constructors (`midpoint`, `centroid`, `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`) with zero change to locked `TypedFact` / `flat` / `v3` / Route A schema SHAs, connected to auxiliary planes (`MAT_SONG_SONG`, `MAT_HAI_DUONG`, `MAT_VUONG_DUONG`), 2D `carrier_planes` perpendicular anchors (`_chon_moc_vuong_duong`), independent Gram postcondition verification (`_MO_TA`), and explicit `search_telemetry` (`planner-recomposition-matrix.json`: `9` newly unlocked `DISCOVERED_FUNCTION_COMPOSITION` chains, `24/24` agreement with `backend/scripts/planning_oracle.py`, `0` wrong-served).
- **Isolated `S-1` & `S-2` offline readiness (`0` live calls, `0` `backend/app/` routing change):**
  - `backend/scripts/s1_diacritic_offline.py` (`16/16` dev corpus + mixed-IME safety, `0` forged quotes, `detect_domain` untouched) and `backend/scripts/score_s2_student_language_pilot.py` (`8` deterministic metrics, `ALLOW_LIVE_AI=0`).
- **Retirement & live gates:** unchanged — `LLM_ONLY`, compiler `C`, and Adapter `/3` (`0` edits) keep their retirement statuses, `DEFAULT_MODE = "LLM_ONLY"` and `CACHE_VERSION = "131"` are untouched, `phase-o` replay holds Wave 3 `67/72` + `72/72` (`0` wrong-served, `0` transitions), locked `96/96`, and `203` probes clean, and D-04 / D-11 / D-13 / GATE-16 await the consolidated Owner GO.

## Update after thirteenth continuation (`9503482a`, 2026-11-01)

- **`R-1` unnamed described points end-to-end on Hybrid `/4` (`typed-fact-next/2`, Registry `/29`, Planner `/23`, Engine `/20`):**
  - `TypedFactNextPayloadV2.described_points` (`DescribedPointSpec`, `@id` refs, canonical alias deduplication, explicit cycle/depth validation, multi-consumer `scope_records` ownership checks, verbatim quote span provenance) + `typed_fact_next_bridge.py` (`_mo_ta_phang`, `_cau_hoi_mo_ta`, `_mat_fact`) connect `/4` goals and auxiliary section through-points directly to the existing Registry descriptor contracts, Planner `_EffectResolver`, Source Gate `effect-chain` certificates, and Exact Kernel (`9/9` Continuation 11 `DISCOVERED_FUNCTION_COMPOSITION` cases `C1a..C7` + `angle(line1, line2)` now served end-to-end on `/4`; `D1`/`D2` representable on `/2` and refused fail-closed `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` until Source Gate multi/recursive chain certification is authorized).
- **`SL-3` student shorthands & bridge regex repair:**
  - `registry.py` (`/29`) reads `k/c` (case-insensitive) and `đt` before line labels across named and described-point goals (`S-2` gold replay ceiling `33/36 -> 35/36`, `0` wrong-served; `"hình chop"` remains governed under `S-1`).
  - `typed_fact_next_bridge.py::_v2_plane_def_quotes` literal `0x08` (`BACKSPACE`) byte replaced with `\b` + word-for-word imperative restatement deduplication (`0` ASCII control bytes across `backend/`).
- **Preview fixtures & retirement status:** `export_hybrid_preview_fixtures.py` records the declared `("geometry-functions/28", "geometry-functions/29")` identity delta (`41/41` fixtures verified, `0` non-identity diffs; historical bundles untouched); `phase-p2` replay holds Wave 3 `67/72` + `72/72` (`0` wrong-served, `0` transitions), locked `96/96`, and `203` probes clean; `LLM_ONLY`, compiler `C`, Adapter `/3`, `DEFAULT_MODE = "LLM_ONLY"`, and `CACHE_VERSION = "131"` remain unchanged.
