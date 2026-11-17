# SLM_ARCHITECTURE.md — Local Sub-1B Geometry Understanding Architecture (AXO HYBRID /5)

**Run:** `slm-local-geometry-understanding`  
**Candidate:** `96791162f` (product `a182b5460`, `122` files, `tree_hash = 771fe868279c814f…`, `CACHE_VERSION = 145` MATCH)  
**Contracts:** `local-slm-runtime/1` · `local-slm-extractor/1` · `slm-grounding-validator/1` · `slm-grounding-envelope/1`

---

## 1. Architectural Principle & Strict Boundaries

Axo Hybrid `/5` extends the official Hybrid `/4` architecture with an **opt-in local sub-1B CPU SLM fallback** (`HYBRID_ROUTE_MODE=local-slm`) without loosening any deterministic mathematical verification guarantee:

```text
Vietnamese Geometry Problem
  │
  ▼
Local Deterministic Geometry Parser (`local-geometry-parser/2`, 0 SLM calls, ~2–10 ms)
  │
  ├── LOCAL_PARSE_COMPLETE / AMBIGUOUS / OUT_OF_SCOPE ───────────────────────────────┐
  │                                                                                  ▼
  └── Incomplete (`LOCAL_PARSE_PARTIAL` / `LOCAL_PARSE_UNSUPPORTED`)        Source Gate (`kiem_nguon`)
        │                                                                            ▲
        ▼                                                                            │
  Local Sub-1B SLM (`llama.cpp b12470` loopback CPU server, `0` external calls)      │
        │                                                                            │
        ▼                                                                            │
  Deterministic Source Grounding & Validator (`slm-grounding-validator/1`) ─────────┘
        │ (rejected hallucinations / conflicts / prompt injections fail closed; never cached)
        ▼
  Planner /26 -> Registry /33 -> Exact Kernel /24 -> Adapter /4 -> Scene3D + Steps + Results
```

### Non-Negotiable Architecture Rules Preserved
1. **Zero LLM Code / Program Generation:** The local SLM never generates Python, JS, coordinates, proofs, or numerical answers. It only emits structured geometric facts citing verbatim source clauses.
2. **Parser-First Fast Path:** `route_text_input_local_slm` (`backend/app/ai/adaptive_input_router.py`) calls deterministic `route_text_input(..., allow_live_ai=False)` first. Problems resolved deterministically never invoke the local SLM (`slm_invoked = false`).
3. **Hard Grounding Before Planning:** Source Gate (`registry.kiem_nguon`), Exact Kernel (`engine.py`), Planner `/26` (`planner.py`), and `TypedFactNext /2` contracts remain untouched; an upstream deterministic validator (`slm-grounding-validator/1`) rejects ungrounded SLM emissions before they even enter `extract_typed_fact_next_v2`.
4. **Zero Impact on Production Default / Cache `145`:** `HYBRID_ROUTE_MODE` defaults to `"live"` and `CACHE_VERSION` remains `"145"`. Local SLM execution uses opt-in `HYBRID_ROUTE_MODE=local-slm` backed by `LocalSlmHybridRun` (`prepare_local_slm_hybrid`) and an isolated cache key (`HYBRID_V5_LOCAL_SLM`, binding `router_version`, `parser_version`, `runtime_version`, `extractor_version`, `model_key`, `model_sha256`, `strategy`, `extraction_surface`, `surface`, and exact source text).

---

## 2. Two Extraction Strategies Evaluated (Approach A vs Approach B)

| Strategy | Module / Schema | How SLM Outputs Map to `TypedFactNext /2` | Empirical `DEV_CALIBRATION_16` (`Qwen3-0.6B-Q4_K_M`) |
|---|---|---|---|
| **Approach A (`direct_wire`)** | `DIRECT_WIRE_JSON_SCHEMA` (`backend/app/ai/local_slm_extractor.py`) | SLM directly outputs nested `key=value` wire strings and verbatim `quote` substrings under constrained JSON schema | **`0/10` pos**, `6/6` neg, `0` leaks · `total p50 = 13962.67 ms`, `p95 = 17047.14 ms` — fails primarily on minor quote-span paraphrases (`QUOTE_NOT_IN_SOURCE`) |
| **Approach B (`minimal_ops`)** | `MINIMAL_OPS_JSON_SCHEMA` + `validate_and_lower_minimal_ops` | SLM outputs flat clause-indexed `{solid, ops, goals, unresolved}`; Python deterministically resolves exact verbatim clause substrings and lowers into `TypedFactNext /2` | **`2/10` pos**, `6/6` neg, `0` leaks · `total p50 = 8381.93 ms`, `SLM p50 = 8364.31 ms`, `p95 = 14730.26 ms` (winner locked before holdout) |

### Why Approach B (`minimal_ops`) Won Calibration
Quantized sub-1B models (`0.5B–0.6B` Q4_K_M) frequently drop or alter a single Vietnamese word or punctuation mark when asked to copy multi-clause verbatim `quote` fields inside nested `key=value` wire JSON (`direct_wire`). Compacting the generation schema to flat `(clause_id, kind, a, b, pt, val, unit)` ops reduced token length (~`13.96 s` → `~8.36 s` p50) and let deterministic Python code construct exact `norm_text` substrings cleanly while checking grounding invariants.

---

## 3. Deterministic Source Grounding & Anti-Hallucination (`slm-grounding-validator/1`)

Every `minimal_ops` emission undergoes six deterministic checks in `validate_and_lower_minimal_ops` (`backend/app/ai/local_slm_extractor.py`) before lowering:

1. **Pre-Inference Prompt-Injection Gate (`detect_prompt_injection`):** Rejects jailbreak / source-override phrases (e.g., `ignore ... previous instructions`, `bypass source gate`, `bỏ qua mọi quy tắc`) before calling the SLM (`PROMPT_INJECTION_REJECTED` -> `UNGROUNDED_VALUE`, `0` SERVED leaks).
2. **Verbatim Clause Resolution & Quote Selection (`_clause_supports_op`, `select_clean_quote`):** Indexes sentences via `split_into_Sentences(norm_text)`. If an SLM `clause_id` is off-by-one, searches for a verbatim clause supporting ALL of the op's required tokens, cues, and quantities, while trapping any negated/ambiguous match; constructs exact `norm_text` substrings trimming benign conversational prefixes (`_strip_conversational_prefix`).
3. **Closed Lexical Cue & Role Guards:** Enforces `_PREDICATE_LEXICAL_CUES` per predicate kind, rejects pure question clauses used as premises (`_PURE_QUESTION_RE`), and rejects negated predicate clauses (`_NEGATED_PREDICATE_RE` -> `INCONSISTENT_FACTS`).
4. **Strict Point, Proximity & Symbolic Quantity Grounding:**
   - Every vertex label must match `[A-Z][0-9]*'*` and exist in the problem text vertex pool (`extract_geometry_points`).
   - `segment_length` requires segment endpoints to appear together (`PQ` / `QP`) in proximity to the scalar/symbolic value (`UNGROUNDED_VALUE:segment_length_proximity`).
   - Values are checked against clause candidate quantities via syntactic canonicalization and `parse_quantity_expr` equivalence (`is_value_grounded_in_clause`).
5. **Singular Indirect-Reference Ambiguity Guard:** Non-unique `"cạnh bên"` or `"mặt bên"` clauses without universal quantifiers or explicit labels fail closed with `AMBIGUOUS_REFERENCE`.
6. **Parser-First Consistency Check (`PARSER_SLM_CONFLICT`):** Any discrepancy between Local Parser's detected solid notation or scalar edge lengths and SLM output fails closed immediately.
