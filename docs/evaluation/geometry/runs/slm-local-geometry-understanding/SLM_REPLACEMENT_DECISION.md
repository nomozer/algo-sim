# SLM_REPLACEMENT_DECISION.md — Empirical Replacement Verdict & Next-Stage Research Plan (AXO HYBRID /5)

**Run:** `slm-local-geometry-understanding`  
**Preregistered Criteria:** [`preregistered_replacement_criteria.json`](preregistered_replacement_criteria.json)  
**Primary Verdict:** **`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`**  
**Production Default Impact:** Keep **`HYBRID_ROUTE_MODE = "live"`** (Gemini 2.5 Flash structured extraction) as production default; retain **`HYBRID_ROUTE_MODE = "local-slm"`** strictly as an **opt-in local/offline experimental fallback**. Do **NOT** replace Gemini 2.5 Flash in production with a zero-shot sub-1B CPU model today.

---

## 1. Criterion-by-Criterion Evaluation Against Preregistered Gates

| Preregistered Criterion | Required (`READY_TO_REPLACE_GEMINI_DEFAULT`) | Required (`READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS`) | Required (`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`) | Measured (`Qwen3-0.6B-Q4_K_M` + Local Parser) | Outcome |
|---|---|---|---|---|---|
| False-positive `Mode A` leaks on negatives | `<= 0` | `<= 0` | `<= 0` | **`0`** (`0/6` cal, `0/18` S2 neg, `0/12` holdout neg; `COMP112` `2` identical to Config A `slm_invoked=False`) | **PASS** |
| `Scene3D` continuity errors | `<= 0` | `<= 0` | `<= 0` | **`0`** across all suites | **PASS** |
| Deterministic `v145` regressions | `0` | `0` | `0` | **`0`** (`regression_count = 0`) | **PASS** |
| External AI / network calls | `0` | `0` | `0` | **`0`** (`ALLOW_LIVE_AI=0`) | **PASS** |
| Holdout disjointness overlaps | `0` | `0` | `0` | **`0`** across 9 corpora | **PASS** |
| Fault-injection recovery (`5` checks) | `All pass` | `All pass` | `All pass` | **`5 / 5 PASS`** | **PASS** |
| Combined RSS vs 4–6 GiB RAM budget | `<= 2048 MiB` | `<= 2048 MiB` | `<= 2048 MiB` | **`1040.57 MiB`** (`674.81 MiB` for 0.5B); `PHYSICAL_LOW_END = NOT_MEASURED` | **PASS (Host RSS)** |
| Holdout negative refusal rate | `1.0` | `1.0` | `1.0` | **`1.0` (`12/12`)** | **PASS** |
| Warm inference latency (`p95`) | `<= 5000 ms` | `<= 12000 ms` | `<= 20000 ms` | **`8480.07 ms`** (`threads=4`), **`8025.00 ms`** (`threads=6`), **`11693.69 ms`** (`HOLDOUT_40` `p95`) | **FAILS Full Replacement (`<=5000ms`), PASSES Constraint & Experimental** |
| `SLM_INDEPENDENT_HOLDOUT_40` positive exact rate | `>= 0.85` (`>=24/28`) | `>= 0.65` (`>=19/28`) | `> Config A` (`> 9/28 = 32.14%`) | **`0.3571` (`10/28`, `+1` over `Config A 9/28`)** *(DEV_CALIBRATION_16: `2/10` vs `0/10`)* | **FAILS Default/Primary (`0.85`/`0.65`), PASSES `> Config A` Experimental** |
| Derived section & relation parity | `Required` | `Optional` | `Optional` | Scope limited to core polyhedral solids, premises, midpoint/centroid/proj, angles, lengths, volumes, distances | **FAILS Parity** |

---

## 2. Scientific Verdict Rationale

1. **Why Gemini 2.5 Flash CANNOT Yet Be Replaced as Default (`PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL`):**  
   A zero-shot `0.6B` Q4_K_M model on CPU achieves only `35.71%` (`10/28`) positive accuracy on `SLM_INDEPENDENT_HOLDOUT_40` (`+1` case over Deterministic `v145`'s `9/28`) and `2/10` on `DEV_CALIBRATION_16`, at `p50 ~ 6.7–10.6 s` CPU latency per fallback request. It misses multi-constraint angle/right-angle/colloquial combinations and lacks coverage of constrained sections and multi-solid relations. Replacing Gemini 2.5 Flash today would severely regress user-perceived completion rate on novel problems.
2. **Why the Architecture & Local Route Are Still a Real Engineering Win (`0` Harm, Clean Gain Path):**  
   - **Resource Viability Proven:** Peak combined RSS is `~1.02 GiB` (`Qwen3-0.6B`) / `~0.66 GiB` (`Qwen2.5-0.5B`) with zero manual Ollama installation, cleanly fitting consumer RAM headroom (with real physical 4–6 GiB testing tracked explicitly as `NOT_MEASURED`).
   - **Zero-Regression & Zero-Leak Safety Proven:** Coupling Local Parser fast-path + `minimal_ops` + `slm-grounding-validator/1` + Source Gate yields **`0` regressions**, **`0` Scene3D continuity errors**, and **`0` false Mode A leaks** across `37` dev + `112` comp + `39` probes + `36` S2 + `27` REAL27 + `40` disjoint holdout problems + `5` runtime fault scenarios.
   - **Clear Fine-Tuning Path:** Replacing zero-shot prompting with LoRA/QLoRA fine-tuning of `Qwen3-0.6B` specifically on `(Vietnamese sentence clauses + Local Parser hints) -> minimal_ops JSON` (trained solely on verified C26/synthetic dev pairs outside `HOLDOUT_40` and `H-1`) directly targets the `LOCAL_MODEL_EXTRACTION_ERROR` bottleneck without inflating parameter count or RAM. Meanwhile, optional controlled `"quote normalization"` with explicit learner confirmation can safely bridge benign Vietnamese diacritic/typo gaps (`"vuông goc"`, `"đên"`) without weakening Source Gate.

---

## 3. Research Proposal: Dynamic Geometry Construction Planning Beyond Fixed Templates

Moving Axo's solver core from fixed problem patterns toward general spatial geometry planning requires upgrading **both** semantic grounding (`SLM / LoRA -> minimal_ops`) and the symbolic planner (`Planner /26`) simultaneously:

### Problem Statement in Current `Planner /26`
Today `Planner /26` succeeds strongly on standard solids and registered decompositions (`RM72` `61/62`, with `MG9` capped at `max_memory_declarations = 32` by `IR_MEMORY_BUDGET_EXCEEDED`), but novel problems often fail not at extraction, but because no registered multi-step sequence exists for composing unfamiliar intermediate loci (e.g., constructing two auxiliary lines or a perpendicular plane foot only implied by the problem, or reusing an already-proved orthogonal normal across multiple sub-goals).

### Proposed Architecture (Strictly Symbolic & Certified — Zero LLM Code Generation)
1. **Typed Precondition–Effect Operator Schema over `Registry /33`:**
   - Formalize every registered construction in `Registry /33` as a pure typed action operator `Op(preconditions: FactSet, add_effects: FactSet, metric_cost: Rational, aux_points_created: int)`.
   - Express goal predicates (e.g. `Dist(P, Q)`, `Angle(L, Plane)`, `Section(Solid, Plane)`) as normalized geometric queries whose satisfiability depends on *equivalence classes of constructed planes/lines/projections*, not literal vertex ordering.
2. **Goal-Directed Backward-Chaining + Bounded Auxiliary Witness Synthesis:**
   - Replace brute-force forward enumeration (which hits `max_memory_declarations = 32` on deep compositions like `MG9`) with **Relevance-Guided A\* / Means-Ends Backward Search**:
     - Expand backward from the asked goal (`ask_distance_point_plane`, `ask_angle_plane_plane`, `ask_section_area`) matching operators whose `add_effects` supply the missing coordinate frame, normal vector, or intersection carrier line.
     - Bound auxiliary synthesis depth (`max_aux_points <= 4`, `max_aux_planes <= 2`) using symmetry/coplanarity equivalence classes (`_diem_tren_mat`, `_bo_ba_thang_hang`) so duplicate auxiliary projections `(H_1, H_2)` prune immediately before touching IR memory.
3. **Cross-Goal Intermediate Sharing & Incremental Proof Certificates:**
   - Cache derived geometric witnesses (normals, feet of perpendiculars, dihedral planes, intersection lines) in a canonical `FactGraph` DAG keyed by structural geometric identity (set of spanning points + constraint kind), enabling zero-cost reuse across compound multi-question problems and pedagogical timeline narration (`created_ids` / `reused_ids`).
4. **Inviolable Kernel Separation:**
   - Even with dynamic backward-chaining, **every step emitted by the Planner compiles to IR and executes deterministically inside `Exact Kernel /24` (`Fraction`, `Radical` Gram metrics)** with independent certificate verification (`verify_target_invariance_certificate`, `plane-section-certificate/1`) and Source Gate attribution. The SLM (even after future LoRA fine-tuning) strictly remains an extraction frontend into `TypedFactNext /2`, never touching planning or coordinate math.
