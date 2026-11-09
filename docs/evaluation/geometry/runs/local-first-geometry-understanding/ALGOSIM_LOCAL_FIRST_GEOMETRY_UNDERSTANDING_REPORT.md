# ALGOSIM — LOCAL-FIRST GEOMETRY UNDERSTANDING & VERIFIED AI FALLBACK REPORT

> **Run ID:** `local-first-geometry-understanding`  
> **Date:** `2026-11-09`  
> **Branch:** `feat/local-first-geometry-understanding` (cut from `feat/release-stabilization-validation-readiness` `4baf4a304cf930b7a38756e2b4b5428f1f89cf2c`)  
> **Product Commit:** `63539c2f0eeb574a8fb9c195a43480c05936dfe0` (`63539c2f0`)  
> **Measured System (`EVALUATION_CANDIDATE.json`):** `108` files · `tree_hash = 0493da33470c43ec40939bf21c608f2a425ac7721579ca309e51483231b4777d` · `CACHE_VERSION = 132` (`ROUTE_D_CACHE_POLICY = 132:route-d`)  
> **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`)  
> **Primary Verdicts:**  
> `PHASE_0_PREFLIGHT_VERIFIED = YES` · `LOCAL_GEOMETRY_PARSER_IMPLEMENTED_AND_VERIFIED = YES` · `ADAPTIVE_INPUT_ROUTER_IMPLEMENTED_AND_VERIFIED = YES` · `TEXT_ZERO_AI_PATH_VERIFIED = YES` · `IMAGE_SINGLE_AI_CALL_PATH_VERIFIED = YES` · `LOCAL_OCR_PRODUCTION_STATUS = LOCAL_OCR_DIAGNOSTIC_ONLY` · `HYBRID_CAPABILITY_NEXT_PHASE_PLAN = READY` · `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` · `LIVE_VISION_EVALUATION = NOT_MEASURED` · `REAL_WORLD_CORPUS_NOT_AVAILABLE`

---

## Section A — Executive Summary

This wave implements and verifies **Local-First Geometry Understanding & Verified AI Fallback** on top of the official AlgoSim Hybrid `/4` architecture (`Vietnamese Problem -> Local Geometry Parser /1 (or Gemini Fallback) -> TypedFactNext /2 -> Source Gate -> FactGraph -> Planner /26 -> Registry /33 -> Exact Kernel /24 -> Adapter /4 -> Scene3D + Construction Steps + Exact Results`), achieving a substantive, mathematically verified reduction in Gemini provider dependency without rewriting Planner `/26`, Registry `/33`, or Exact Kernel `/24` and without weakening Source Gate or Exact Kernel fail-closed guarantees:

1. **Phase 0 Pre-Flight & Evidence Blockers Closed (`phase0_reconciliation_verification_receipt.json`, `c4453fbbfe11`):**
   - **III.1 (`Development Matrix 72` summary reconciliation):** Reconciled `in_scope_positive_total = 62`, `in_scope_supported_positive_total = 56`, `served_correct = 56`, `supported_served_rate_pct = 100.0`, `all_in_scope_served_rate_pct = 90.32`, `known_gap_probes_count = 6` (`PL5, PA3 [G2], MG5 [G3], SE3 [G4], MG9 [G6], RE10 [G7]`), and `negative_total = 10` (`9` `CORRECT_REFUSAL` + `1` `CORRECT_CLARIFICATION`), `false_refusal = 0`, `wrong_served = 0`.
   - **III.2 (`G2–G7` namespace disambiguation):** Registered explicit `gap_namespace_registry` in `evidence_reconciliation_receipt.json` (`b48d5178a207`) separating `DEV72-G2..G7` (`hybrid-reasoning-generalization` capability gaps) from `W11-G2..G7` (`hybrid-master-backend-replacement` Continuation 11 historical gaps).
   - **III.3 (`benchmark_12_fixtures_reverification`):** Verified `total_fixtures = 12`, `readable_non_blank_fixtures = 12`, `valid_fixtures_holding_all_content = 8` in `correctness_hardening_receipt.json` (`7bfbbd2775bb`).
   - **III.4 (`Exact Kernel Multi-Solution Sign Enumeration`):** Generalized `backend/app/simulation/geometry_functions/engine.py` (`MULTI_SOLUTION_POLICY = "EXHAUSTIVE_HALF_SPACE_SIGN_ENUMERATION"`, `MAX_INDEPENDENT_SIGN_BRANCHES = 16`) so `_dinh_tu_ba_canh_ben` and `_non_empty_anchor_flips` enumerate all $2^{m-1}$ relative half-space sign branches across all independent off-base apices (including trilateration apices without an explicit `altitude` fact), serving the unique valid configuration (`√74/2` on the 3-apex disambiguated fixture) or refusing fail-closed with `AMBIGUOUS_FACT` when multiple valid branches yield distinct mirror-sensitive goal values.
   - **III.5 (`Cross-platform candidate identity`):** Confirmed `backend/scripts/freeze_evaluation_candidate.py::bam_noi_dung` normalizes `\r\n -> \n` before hashing so `EVALUATION_CANDIDATE.json` (`0493da33470c43ec…`) is invariant across Windows CRLF and Linux/macOS LF checkouts.

2. **Deterministic Local Geometry Parser (`backend/app/ai/local_geometry_parser.py`, `local-geometry-parser/1`):**
   - Implements an 8-stage deterministic pipeline:
     $$\text{Problem Text} \to \text{Normalization} \to \text{Lexer/Tokenizer} \to \text{Clause \& Sentence Splitter} \to \text{Grammar Parser} \to \text{Typed Semantic AST} \to \text{Semantic Validation} \to \text{Source-Span Coverage Check} \to \text{Source Gate Verification} \to \text{TypedFactNextPayloadV2}$$
   - Covers polyhedral and curved solids (`pyramid`, `tetrahedron`, `prism`, `box`, `cube`, `cylinder`, `cone`, `sphere`), base/face shapes, perpendicularity/parallelism/altitude premises, metric lengths/angles/areas/volumes (including symbolic scale `a` and radicals), constructed points (`midpoint`, `centroid`, `orthocenter`, `circumcenter`, `divide_segment`, `orthogonal_projection`, `orthogonal_projection_line`, `intersect_line_line`, `intersect_line_plane`), nested `DescribedPointSpec` chains up to depth 2 (`@id`), `DerivedSectionSpec` cutting planes, and measurement/volume-ratio/residual-volume/section goals.
   - Enforces **Source-Span Coverage Verification**: every geometry-bearing clause must be accounted for by a verbatim `quote` span verified by `registry.kiem_nguon`; any unparsed geometry clause sets `coverage_complete = False` and classifies the parse as `LOCAL_PARSE_PARTIAL` (`reason_code = "LOCAL_PARSE_FALLBACK_REQUIRED"`), preventing partial silent solves.
   - Across **196 total benchmark cases** (`Dev72`, `HeldOut46`, `K-1`, `R-1`, `S-2`, and `RenamedAndParaphrased8`), the Local Geometry Parser solves **`139/139 = 100.0%`** supported positive cases with **`0` Gemini calls**, fail-closes **`10/10 = 100.0%`** gap probes and **`47/47 = 100.0%`** negative cases, achieves **`0` `WRONG_SERVED`** and **`0` `FALSE_REFUSAL`**, with `parse_latency_p50_ms = 10.516 ms` (`p95 = 27.460 ms`) and `end_to_end_latency_p50_ms = 28.203 ms` (`p95 = 65.842 ms`).

3. **Adaptive Input Router & Provider Call Reduction (`backend/app/ai/adaptive_input_router.py`, `adaptive-input-router/1`):**
   - **Text Route (`T1` vs `T0`):** Solves `133/133 (100.0%)` supported positive problems across `Dev72 + HeldOut46 + K-1 + R-1 + S-2` with **`0.0` Gemini calls/problem** (down from `1.0` Gemini call/problem in `T0`, a **100.0% AI call reduction** on supported text; `188 -> 0` calls offline).
   - **Image Route (`I1` vs `I0`):** On the 11-class image ingestion benchmark (`8` math image classes `class_01`–`class_08` + `3` rejection classes `class_09`–`class_11`), `I1` uses Gemini Vision once to transcribe the cropped image and then parses and solves the extracted Vietnamese text locally via `local-geometry-parser/1`, reducing Gemini calls on valid math images from **`2.0 -> 1.0` call/image** (`16 -> 8` calls across the 8 math classes, a **50.0% total AI call reduction** and **100.0% elimination of the second `TypedFactNext` AI call**) while preserving `8/8 (100.0%)` exact math answers and `0` `WRONG_SERVED`.
   - **Experimental Zero-AI Local OCR (`I2`):** Evaluated across all `22` items of `ocr_benchmark.json` via `evaluate_local_ocr_gate` (cross-engine math-token agreement between `Tesseract 5.5.3 vie_fast` and `RapidOCR PP-OCRv6 small` + `local-geometry-parser/1` completeness check). The gate holds `22/22` items for Vision or user confirmation (`0` `WRONG_SERVED`), confirming `LOCAL_OCR_PRODUCTION_STATUS = "LOCAL_OCR_DIAGNOSTIC_ONLY"`.

---

## Section B — Phase 0 Reconciliation & Fix Receipts

All five Phase 0 blockers from Section III are closed and machine-verified in [`phase0_reconciliation_verification_receipt.json`](phase0_reconciliation_verification_receipt.json) (`SHA-256 = c4453fbbfe11…`) and [`docs/evaluation/geometry/runs/release-stabilization-validation-readiness/`](../release-stabilization-validation-readiness/):

| Phase 0 Item | Requirement | Resolution & Verification | Receipt & Hash |
|---|---|---|---|
| **III.1** | `Development Matrix 72` summary reconciliation (`in_scope_supported_positive_total` vs `in_scope_positive_total`) | Reconciled in `reconcile_and_verify_readiness.py` and `ALGOSIM_RELEASE_STABILIZATION_REPORT.md`: `total_cases = 72`, `in_scope_positive_total = 62`, `in_scope_supported_positive_total = 56`, `served_correct = 56`, `supported_served_rate_pct = 100.0%`, `all_in_scope_served_rate_pct = 90.32%`, `known_gap_probes_count = 6` (`PL5, PA3 [G2], MG5 [G3], SE3 [G4], MG9 [G6], RE10 [G7]`), `negative_total = 10` (`9` `CORRECT_REFUSAL` + `1` `CORRECT_CLARIFICATION`), `false_refusal = 0`, `wrong_served = 0`. Frozen raw receipts in `independent-geometry-and-vision-evaluation` remain 100% byte-untouched. | `evidence_reconciliation_receipt.json` (`b48d5178a207`) |
| **III.2** | `G2–G7` namespace disambiguation | Added `gap_namespace_registry` in `evidence_reconciliation_receipt.json` explicitly separating `DEV72-G2..DEV72-G7` (active capability boundaries in `hybrid-reasoning-generalization`) from historical `W11-G2..W11-G7` (`hybrid-master-backend-replacement` Continuation 11). | `evidence_reconciliation_receipt.json` (`b48d5178a207`) |
| **III.3** | `benchmark_12_fixtures_reverification` (`total_fixtures == 12`) | Verified all `12/12` synthetic fixtures (`total_fixtures = 12`, `readable_non_blank_fixtures = 12`, `valid_fixtures_holding_all_content = 8`, `crops_requiring_full_retry = 4`). | `correctness_hardening_receipt.json` (`7bfbbd2775bb`) |
| **III.4** | Exact Kernel multi-solution sign enumeration across all $2^{m-1}$ independent off-base apices | Extended `engine.py` (`MULTI_SOLUTION_POLICY = "EXHAUSTIVE_HALF_SPACE_SIGN_ENUMERATION"`, `MAX_INDEPENDENT_SIGN_BRANCHES = 16`): `_dinh_tu_ba_canh_ben` registers trilateration apices in `off_base_anchors` even without an explicit `altitude` fact and respects `flipped_apices` (`-h` vs `+h`), while `_non_empty_anchor_flips` enumerates all $2^{m-1}-1$ non-empty relative sign combinations. Locked by 4 new tests in `test_hybrid_reasoning_generalization.py` (`37 passed, 6 xfailed`). | `correctness_hardening_receipt.json` (`7bfbbd2775bb`) · `phase0_reconciliation_verification_receipt.json` (`c4453fbbfe11`) |
| **III.5** | Cross-platform candidate identity (`CRLF -> LF`) | Confirmed `backend/scripts/freeze_evaluation_candidate.py::bam_noi_dung` normalizes `\r\n -> \n` before SHA-256 hashing across all `108` measured product files (`0493da33470c43ec…`). | `EVALUATION_CANDIDATE.json` · `phase0_reconciliation_verification_receipt.json` (`c4453fbbfe11`) |

---

## Section C — Architecture of Local Geometry Parser (`local-geometry-parser/1`)

Implemented in [`backend/app/ai/local_geometry_parser.py`](../../../../../backend/app/ai/local_geometry_parser.py) (`LOCAL_GEOMETRY_PARSER_VERSION = "local-geometry-parser/1"`), the parser translates Vietnamese 3D geometry problem statements into schema-valid `TypedFactNextPayloadV2` payloads (`typed-fact-next/2`) without LLM calls and without problem-specific hardcoding:

```
Problem Text
   │
   ▼
1. Normalization (`normalize_problem_text`)
   │  Unicode NFC, math symbol unification (⊥, ∥, √, ², ³, ′ -> '), whitespace & span map
   ▼
2. Lexer / Tokenizer (`tokenize_geometry_text`)
   │  Point/solid notations (S.ABCD, ABC.A'B'C'), plane refs ((ABC), (α)), numbers/radicals/fractions
   ▼
3. Clause & Sentence Splitter (`split_into_clauses`)
   │  Exact character offsets (start_char, end_char), geometry-signal classification
   ▼
4. Grammar Parser & 5. Typed Semantic AST (`LocalParseResult`)
   │  Solids, base/face shapes, perpendicularity/parallelism/angles/lengths,
   │  DescribedPointSpec (@id chains up to depth 2), DerivedSectionSpec, MathGoalSpec
   ▼
6. Semantic Validation & 7. Source-Span Coverage Check (`SourceCoverageReport`)
   │  Checks that 100% of geometry-bearing clauses are covered by verbatim quotes
   │  and that the solid has sufficient metric determination
   ▼
8. Source Gate Verification (`bridge_v2` + `registry.kiem_nguon` + `planner.lap_ke_hoach`)
   │  Verifies verbatim quotes, object ownership, and plan constructibility before accepting
   ▼
TypedFactNextPayloadV2  (or fail-closed status: AMBIGUOUS / UNSUPPORTED / PARTIAL)
```

### Key Correctness & Fail-Closed Invariants
1. **No Problem-ID or Coordinate Hardcoding:** Vertex labels (`S.ABCD`, `S.MNPQ`, `P.ABCD`, `O.ABC`, `MNP.M'N'P'`), edge lengths, angles, and goals are parsed compositionally from Vietnamese grammar rules and verified against `TypedFactNextPayloadV2` + `bridge_v2` + `registry.kiem_nguon`.
2. **Source-Span Coverage Check (`SourceCoverageReport`):** If a sentence contains an unrecognized geometric constraint (e.g., `"Biết mặt phẳng (P) quay quanh trục đối xứng tạo góc 37 độ với tiếp tuyến quỹ tích"` in `GEN-07`), `unparsed_geometry_clauses` is non-empty, `coverage_complete` is `False`, and the parser returns `LOCAL_PARSE_PARTIAL` (`reason_code = "LOCAL_PARSE_FALLBACK_REQUIRED"`, `payload = None`) rather than ignoring the unparsed clause and serving a wrong answer.
3. **Fail-Closed Classification:**
   - `LOCAL_PARSE_COMPLETE`: 100% clause coverage + passes `TypedFactNextPayloadV2` validation, `bridge_v2`, and `Source Gate`.
   - `LOCAL_PARSE_AMBIGUOUS`: Missing dimensions, underdetermined solid, or resolvable `UnresolvedSpec` (`AMBIGUOUS_FACT` / `MISSING_DIMENSION` / `UNDERDETERMINED_POINT`).
   - `LOCAL_PARSE_UNSUPPORTED`: Explicit out-of-scope domain (`GATE_OUT_OF_SCOPE`) or unsupported capability (`OUT_OF_SCOPE`, `UNSUPPORTED_CAPABILITY`, `CURVED_WORDING_UNSUPPORTED`, `BRIDGE_UNSUPPORTED_DESCRIBED_POINT`).
   - `LOCAL_PARSE_PARTIAL`: Contains geometry clauses beyond the local grammar (`LOCAL_PARSE_FALLBACK_REQUIRED`), triggering Gemini fallback only when `allow_live_ai=True`.

---

## Section D — Local Parser Benchmark Results (`local_parser_benchmark_receipt.json`)

Measured offline (`ALLOW_LIVE_AI = 0`, `0` provider calls) by [`tools/evaluate_local_first_understanding.py`](tools/evaluate_local_first_understanding.py) and recorded in [`local_parser_benchmark_receipt.json`](local_parser_benchmark_receipt.json) (`SHA-256 = 50f5d31ab8eb…`):

| Benchmark Suite | Total Cases | Supported Positive | Solved Locally (`0` AI Calls) | Gap Probes (`G2–G7`) | Gap Probes Fail-Closed | Negative Cases | Negative Correct | `WRONG_SERVED` | `FALSE_REFUSAL` | Parse `p50 / p95` (ms) | E2E `p50 / p95` (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **`Dev72`** (`hybrid-reasoning-generalization`) | `72` | `57` | **`57/57 (100.0%)`** | `6` | `6/6` | `9` | `9/9` | `0` | `0` | `10.404 / 20.067` | `27.681 / 52.332` |
| **`HeldOut46`** (`independent-geometry` Workstream B) | `46` | `35` | **`35/35 (100.0%)`** | `4` | `4/4` | `7` | `7/7` | `0` | `0` | `10.116 / 17.614` | `26.242 / 50.181` |
| **`K-1`** (`C26` core textbook suite) | `16` | `10` | **`10/10 (100.0%)`** | `0` | `0/0` | `6` | `6/6` | `0` | `0` | `14.720 / 29.367` | `42.782 / 71.090` |
| **`R-1`** (`C26` multi-step composition suite) | `18` | `14` | **`14/14 (100.0%)`** | `0` | `0/0` | `4` | `4/4` | `0` | `0` | `9.867 / 29.766` | `27.148 / 66.984` |
| **`S-2`** (`C26` student-language & shorthand suite) | `36` | `17` | **`17/17 (100.0%)`** | `0` | `0/0` | `19` | `19/19` | `0` | `0` | `3.924 / 11.418` | `12.986 / 29.827` |
| **`RenamedAndParaphrased8`** (`GEN-01`..`GEN-08`) | `8` | `6` | **`6/6 (100.0%)`** | `0` | `0/0` | `2` | `2/2` | `0` | `0` | `9.090 / 25.302` | `24.139 / 81.790` |
| **Aggregate Total** | **`196`** | **`139`** | **`139/139 (100.0%)`** | **`10`** | **`10/10`** | **`47`** | **`47/47`** | **`0`** | **`0`** | **`10.516 / 27.460`** | **`28.203 / 65.842`** |

*Note on `Dev72` (`N3`) and `HeldOut46` (`HB43`):* In the stored replay suites, `N3` and `HB43` were negative Source Gate tamper tests where the stored JSON payload injected a forged quote (`"SA = 7"` on `N3`, `"SA = 99"` on `HB43`) against a valid problem text (`"SA = 2"` on `N3`, `"SA = 3"` on `HB43`). When parsing the clean Vietnamese problem text directly from source, `local-geometry-parser/1` extracts the true verbatim quote (`"SA = 2"` -> exact answer `√2`; `"SA = 3"` -> exact answer `12/5`). Similarly, on `R1-F01` (where live Gemini failed to nest `@m1` inside `@h1` in C26), `local-geometry-parser/1` constructs the exact depth-2 `DescribedPointSpec` chain and serves `√6/2`.

---

## Section E — Adaptive Input Router & AI Call Reduction (`T0/T1/I0/I1/I2`)

Implemented in [`backend/app/ai/adaptive_input_router.py`](../../../../../backend/app/ai/adaptive_input_router.py) (`ADAPTIVE_INPUT_ROUTER_VERSION = "adaptive-input-router/1"`) and integrated into [`backend/app/ai/hybrid_offline.py`](../../../../../backend/app/ai/hybrid_offline.py), [`backend/app/main.py`](../../../../../backend/app/main.py) (`HYBRID_ROUTE_MODE = "local-first"` or `HYBRID_LOCAL_FIRST = 1`), and [`backend/app/ingestion/unified_input.py`](../../../../../backend/app/ingestion/unified_input.py) (`provenance["local_geometry_parse"]`).

### E.1 Text Route Comparison (`T0` vs `T1` across `188` Standard Cases)

From [`comparative_routes_t0_t1_i0_i1_i2_receipt.json`](comparative_routes_t0_t1_i0_i1_i2_receipt.json) (`SHA-256 = e3b55ab36b4b…`):

| Metric | `T0` (Baseline: Gemini `TypedFactNext /2` on Every Text) | `T1` (Local-First Geometry Parser + Verified Fallback) | Improvement / Delta |
|---|---:|---:|---:|
| **Standard Corpus Size (`Dev72 + HeldOut46 + K-1 + R-1 + S-2`)** | `188` (`133` pos + `55` neg/gap) | `188` (`133` pos + `55` neg/gap) | Same corpus |
| **Supported Positive Solved** | `132/133 (99.25%)` (`R1-F01` failed in stored Gemini extraction) | **`133/133 (100.0%)`** | **`+0.75%` (`+1` case `R1-F01`)** |
| **Negative & Gap Probes Fail-Closed** | `55/55 (100.0%)` | **`55/55 (100.0%)`** | `100.0%` preserved |
| **`WRONG_SERVED` / `FALSE_REFUSAL`** | `0 / 1` (`R1-F01`) | **`0 / 0`** | **`0` wrong-served** |
| **Gemini Provider Calls per Supported Problem** | `1.0` | **`0.0`** | **`-100.0%` (`0` AI calls)** |
| **Total Gemini Calls across 188 Cases (Offline)** | `188` (stored replay of 188 calls) | **`0`** | **`-100.0%`** |
| **Parse Latency (`p50 / p95`)** | `2,500–4,500 ms` (live provider) | **`10.516 ms / 27.460 ms`** | **>99% faster than live LLM** |
| **End-to-End Local Route Latency (`p50 / p95`)** | `~2,500+ ms` (live) / `~24 ms` (replay) | **`28.203 ms / 65.842 ms`** | Deterministic sub-60ms `p95` |
| **Peak Working Set (RSS)** | `~55 MB` | **`56.43 MB`** | No external ML weights loaded |

### E.2 Image Route Comparison (`I0` vs `I1` across `11` Image Ingestion Classes)

| Metric | `I0` (Baseline: Vision Call #1 + `TypedFactNext` Call #2) | `I1` (Adaptive: Vision Call #1 + Local Parser `0` Call #2) | Improvement / Delta |
|---|---:|---:|---:|
| **Math Image Classes (`class_01`..`class_08`) Served Exact** | `8/8 (100.0%)` | **`8/8 (100.0%)`** | `100.0%` exact agreement (`4`) |
| **Rejection Classes (`class_09`..`class_11`) Handled** | `3/3 (100.0%)` | **`3/3 (100.0%)`** | `100.0%` preserved |
| **`WRONG_SERVED`** | `0` | **`0`** | `0` |
| **Gemini Vision Calls per Valid Math Image** | `1.0` | **`1.0`** | Vision used once for image transcription |
| **Gemini `TypedFactNext` Calls per Valid Math Image** | `1.0` | **`0.0`** | **`-100.0%` (2nd AI call eliminated)** |
| **Total Gemini Calls per Valid Math Image** | `2.0` (`16` across 8 classes) | **`1.0` (`8` across 8 classes)** | **`-50.0%` total AI calls on math images** |
| **Total Gemini Calls across All 11 Classes** | `19` | **`11`** | **`-42.11%` overall (`19 -> 11`)** |
| **Local Parse + Hybrid Solve Latency (`p50 / p95`)** | N/A (requires 2nd LLM call) | **`29.767 ms / 30.728 ms`** | Eliminates 2nd network round-trip |
| **User Edit After Image Extraction (`user_edited_text`)** | `1` `TypedFactNext` call | **`0` Vision + `0` `TypedFactNext` calls** | **`0` AI calls on user re-submit** |

---

## Section F — Image OCR Safety Evaluation (`I2` vs `I1`)

Route `I2` (`Image -> Local Pre-Gate/Auto-Crop -> Local OCR + Strict Math Token Gate -> Local Geometry Parser /1 -> Hybrid /4`) was evaluated across all `22` items of [`docs/evaluation/geometry/runs/adaptive-local-ocr-fallback/ocr_benchmark.json`](../adaptive-local-ocr-fallback/ocr_benchmark.json) using `evaluate_local_ocr_gate` (`Tesseract 5.5.3 vie_fast` primary text + `RapidOCR PP-OCRv6 small` secondary cross-engine math-token check + `local-geometry-parser/1` completeness verification):

| Metric | Value | Evidence / Finding |
|---|---:|---|
| **OCR Benchmark Items Evaluated** | `22` | `c01`–`c22` in `ocr_benchmark.json` |
| **Items Passing Cross-Engine Math Token + Local Parser Gate** | `0 / 22` | Even when math tokens agree (`c01_ro_chop_thiet_dien`), Tesseract corrupts `(α) -> (a)` or Vietnamese clause structure so `local_parser_complete = False` |
| **Items Held for Vision or User Confirmation** | `22 / 22 (100.0%)` | Prevents any OCR corruption (`(A'BC) -> (ABC)`, `SA=3 -> SA=8`, `(β) -> (B)`) from reaching the Exact Kernel unverified |
| **Silent `WRONG_SERVED` on `I2`** | **`0`** | Fail-closed safety invariant preserved (`0` wrong answers) |
| **Gate + Local Parse Latency (`p50 / p95`)** | `1.183 ms / 4.191 ms` | Fast diagnostic gate |
| **Official Production Status** | **`LOCAL_OCR_DIAGNOSTIC_ONLY`** | Route `I1` (single Gemini Vision call + `local-geometry-parser/1` with `0` `TypedFactNext` calls) is the production default for image inputs |

---

## Section G — Hybrid Capability Next-Phase Plan (`G2, G3, G4, G6, G7`)

In accordance with Section VIII, the 15 `strict=True` XFAIL regression probes (`9` in `test_hybrid_completion_matrix.py` + `6` in `test_hybrid_reasoning_generalization.py`) remain untouched, and the concrete design specification for closing `DEV72-G2`, `DEV72-G3`, `DEV72-G4`, `DEV72-G6`, and `DEV72-G7` in a dedicated capability-expansion wave is established (`HYBRID_CAPABILITY_NEXT_PHASE_PLAN = READY`, cross-referenced with [`architecture_gap_decisions_receipt.json`](../release-stabilization-validation-readiness/architecture_gap_decisions_receipt.json)):

| Gap ID | Probe Cases | Current Failure Stage & Code | Target Module(s) & Concrete Design Specification | Estimated Complexity |
|---|---|---|---|---|
| **`DEV72-G2`** | `PL5`, `PA3`, `HB35` | `bridge_v2` (`BRIDGE_INVALID_REFERENCE`: `@id` described point inside `line: ["A", "@m1"]`) | **`typed_fact_next.py` + `typed_fact_next_bridge.py` + `registry.py`:** Extend `DESCRIBED_GOAL_KEYS` to allow at most one `@id` endpoint in `line`/`line1`/`line2` slots of `distance` and `angle` goals (`["A", "@m1"]`), lower `@m1` into an auxiliary `midpoint`/`centroid`/`projection` step in `_mo_ta_phang`, and bind the resulting synthetic point symbol into the goal call's `source.quotes` + `effect-chain` certificate. Fail-closed if the two endpoints of `line` coincide (`DEGENERATE_LINE`). | **Low–Medium** (~120 LOC across bridge + registry; 0 kernel changes) |
| **`DEV72-G3`** | `MG5` | `bridge_v2` (`BRIDGE_INVALID_REFERENCE`: `@id` described point inside `polygon: ["A", "B", "@m1"]` of `area` goal) | **`typed_fact_next.py` + `typed_fact_next_bridge.py` + `registry.py`:** Allow `@id` references in `polygon` list of `measurement(goal_type="area")`, lower each `@id` via `_mo_ta_phang` before emitting `ask_area`, and verify non-collinearity of the resolved polygon vertices in `engine.py` (`COLLINEAR_POINTS`). | **Low–Medium** (~90 LOC across bridge + registry) |
| **`DEV72-G4`** | `SE3`, `HB36` | `Source Gate` (`SOURCE_OBJECT_MISMATCH`: unnamed cutting plane through `"trung điểm của SC"` and parallel to `(ABCD)`) | **`typed_fact_next_bridge.py` + `registry.py` + `planner.py`:** Allow `DerivedSectionSpec.constraints` with `kind="contains_point"` to reference a `DescribedPointSpec` `@id` (`point="@m1"`), lower `@m1` into `plan.auxiliary` before constructing `MAT_RANG_BUOC` (`plane_parallel_through`), and extend `registry.mat_cat_dung_nguon` to accept described-point quotes inside constrained section clauses. | **Medium** (~160 LOC across bridge, registry, planner) |
| **`DEV72-G6`** | `MG9`, `HB37` | `Source Gate` / `Registry` (`OUT_OF_SCOPE`: `"Tính diện tích toàn phần"` / `"diện tích xung quanh"` of a polyhedron) | **`registry.py` + `planner.py` + `engine.py`:** Add `ask_polyhedron_surface_area(solid, mode="lateral"|"total")` contract to `Registry /33` that decomposes into the sum of exact areas of all lateral faces (plus base face(s) for `total`), using exact radical arithmetic in `engine.py` (`Radical` sum when all face areas share a common radical radicand, or fail-closed `EXACT_DOMAIN_EXCEEDED` when face areas have incommensurable radicals $\sqrt{p} + \sqrt{q}$). | **Medium** (~180 LOC across registry + engine) |
| **`DEV72-G7`** | `RE10`, `HB38` | `bridge_v2` (`BRIDGE_UNSUPPORTED_POINT_CONSTRUCTION`: `"trung điểm M của đoạn nối hai trung điểm..."` — named premise point over described endpoints) | **`typed_fact_next.py` + `typed_fact_next_bridge.py` + `planner.py`:** Allow `PremiseSpec(kind="midpoint" | "divide_segment" | "orthogonal_projection")` to reference `@id` described points in its segment/target operands (bounded to total depth $\le 2$), lower the inner `@id` points in topological order in `bridge_v2`, and emit chained `source_defined_steps` with composite verbatim quote spans. | **Medium** (~150 LOC across schema, bridge, planner) |

---

## Section H — Verification Gate Results

Executed on `feat/local-first-geometry-understanding` (`product_commit_sha = 63539c2f0eeb574a8fb9c195a43480c05936dfe0`, `measured_system.tree_hash = 0493da33470c43ec40939bf21c608f2a425ac7721579ca309e51483231b4777d`, `ALLOW_LIVE_AI = 0`):

1. **Focused New Suites & Multi-Anchor Sign Enumeration:**
   - `backend/tests/geometry/test_local_geometry_parser.py`: **`9 passed`** (`0 failed`)
   - `backend/tests/geometry/test_adaptive_input_router.py`: **`6 passed`** (`0 failed`)
   - `backend/tests/geometry/test_hybrid_reasoning_generalization.py`: **`37 passed, 6 xfailed`** (`0 failed`)
2. **Full Backend Pytest (`pytest -q -m "not live_provider"`):**
   - **`14,060 passed, 7 skipped, 3 deselected, 15 xfailed, 0 failed`** (up from `14,041` passed in `release-stabilization-validation-readiness`, `+19` new tests = `9` in `test_local_geometry_parser.py` + `6` in `test_adaptive_input_router.py` + `4` multi-anchor sign enumeration tests in `test_hybrid_reasoning_generalization.py`; all `15` strict XFAILs preserved).
3. **Frontend Verification (`npx vitest run` & `npm run build`):**
   - `npx vitest run`: **`2,000 passed`** across `136` test files (`0 failed`).
   - `npm run build`: **PASS** (`tsc -b && vite build` clean).
4. **Candidate Freeze & Standalone Gates:**
   - `backend/scripts/freeze_evaluation_candidate.py --verify`: **PASS** (`108` measured files, `tree_hash = 0493da33470c43ec40939bf21c608f2a425ac7721579ca309e51483231b4777d`, `cay_lam_viec_sach = true`).
   - `backend/scripts/replay_demo_cases.py`: **`5/5` PASS**.
   - `backend/scripts/audit_demo_crash_surface.py`: **`6/6` PASS** (`0` thrown).
   - `backend/scripts/audit_docs_information_architecture.py`: **PASS** (`0` uncataloged or missing doc targets).
   - `backend/scripts/check_publication_safety.py --range main..HEAD`: **PASS** (`0` findings).

---

## Section I — Remaining Honest Boundaries

In strict compliance with `AGENTS.md §3–§4` and `docs/RULES.md`:

- `PHASE_0_PREFLIGHT_VERIFIED = YES`
- `LOCAL_GEOMETRY_PARSER_IMPLEMENTED_AND_VERIFIED = YES`
- `ADAPTIVE_INPUT_ROUTER_IMPLEMENTED_AND_VERIFIED = YES`
- `TEXT_ZERO_AI_PATH_VERIFIED = YES`
- `IMAGE_SINGLE_AI_CALL_PATH_VERIFIED = YES`
- `LOCAL_OCR_PRODUCTION_STATUS = LOCAL_OCR_DIAGNOSTIC_ONLY` (local OCR does **not** ship as an autonomous zero-AI production image solver because single-engine and dual-engine local OCR still fail or require fallback on Vietnamese math symbols; `I1` single-Vision-call + local parser is the verified production image path)
- `HYBRID_CAPABILITY_NEXT_PHASE_PLAN = READY` (`G2, G3, G4, G6, G7` remain fail-closed with 15 strict XFAILs until implemented in a dedicated capability wave)
- `HYBRID_DEFAULT_CUTOVER_COMPLETE = YES`
- `LEGACY_EXECUTION_RETIRED = YES`
- `LEGACY_FULLY_RETIRED = NO` (`semantic_program/route.py` + IR verifier remain `COMPATIBILITY_REQUIRED`)
- `PRODUCTION_DEPLOYMENT_VERIFIED = NO`
- `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (none of `Dev72`, `HeldOut46`, `C26`, or the 196-case local-first benchmark is claimed as an external blind `H-1` evaluation)
- `LIVE_VISION_EVALUATION = NOT_MEASURED` (`ALLOW_LIVE_AI = 0`, `0` live Gemini calls made)
- `REAL_WORLD_CORPUS_NOT_AVAILABLE` (`0` real camera photos or physical scans in the repository)
