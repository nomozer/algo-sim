# Independent review — continuation

## Round 1 (Codex Continuation — `/root/independent_backend_review`)

Reviewer agent: `/root/independent_backend_review` (separate read-only context). This section transcribes the review returned to the coordinator. No file edits or commits by reviewer; no provider/full-suite/browser/T3 execution by reviewer.

Scope: inherited full product diff `43247c9e` → `8b5916e`, connected code/tests, plan/architecture, four previous reviews, evaluation code/results, and Codex fixes through `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee`.

### Findings resolved before candidate freeze 2 (`4fb1045f`)

1. IMPORTANT: `_ref` discarded namespaces. Unknown solid/local vertex references and unknown namespaces in named_intersections keys could serve. Now typed refusals, valid declared qualifiers and edge keys still serve.
2. IMPORTANT: explicit length_unit dropped. Symbolic lengths + unit 1 now refuse NON_HOMOGENEOUS_LENGTHS; explicit a + numeric-only facts refuses BRIDGE_UNSUPPORTED_LENGTH_UNIT (conservative unsupported representation).
3. IMPORTANT: malformed Any premise args could escape as KeyError/AttributeError. Missing/non-string operands and malformed qualifier syntax now return typed refusals. Same Adapter /3 vulnerability is pre-existing and remains outside Session 1.
4. IMPORTANT: declared cutting-plane name dropped. β or reference-plane ABC served as α. Declared names are now preserved and compared against Source Gate verified engine output; bridge does not parse source text.

Independent final confirmation: **12 passed, 54 deselected, 1.41 s** for targeted boundary tests. Direct positive controls: matching unit, known qualified edge keys, metadata goal ID g::S. Seven additional contradictory cut/context probes refused. Source `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee`.

Remaining MINOR/limits: generated premise ID p1 can collide with an authored ID and cause typed false refusal; two-line planes with cut clauses unsupported; derived prisms excluded; quadrilateral/perpendicular plans may exceed IR budget; auxiliary plane points remain visible. These cannot support broad composition or production claims.

---

## Round 2 (Gemini Takeover — `a76efdda-c831-484e-b5f1-382bcf0cc943`)

Reviewer agent: `Independent Continuation Taxonomy & Safety Reviewer` (`a76efdda-c831-484e-b5f1-382bcf0cc943`, separate read-only context).

Scope: continuation product commit `b6684564ac4596da30819da5fcc4c875ebb1a640` (and parent product fix `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee`) across `backend/app/ai/function_route.py`, `backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`, `backend/app/ai/hybrid_preview.py`, `backend/tests/geometry/hybrid_compiler_benchmark.py`, `backend/tests/geometry/test_hybrid_compiler_benchmark.py`, and `backend/tests/test_hybrid_preview_contract.py`.

### Verification summary

1. Confirmed exact root cause of Full T3 Attempt 2 taxonomy failures at `4fb1045f`: `ac719a5b`/`4f3aaea5` introduced `INVALID_TYPED_FACT_NEXT` and `UNKNOWN_VERTEX_REF` on the `TypedFactNext` planner bridge path without registering them in `HB.REFUSAL_CLASS`, and introduced string literals `BRIDGE_UNSUPPORTED_LENGTH_UNIT` and `INVALID_TYPED_FACT_NEXT` in `app/ai/function_route.py` without registering them in `app/ai/hybrid_preview.py::_NHOM`.
2. Confirmed semantic and mathematical accuracy of every classification added in `b6684564ac4596da30819da5fcc4c875ebb1a640`:
   - `INVALID_TYPED_FACT_NEXT` → `"malformed"` (`REFUSAL_CLASS`) & `"EXTRACTION_FAILED"` (`hybrid_preview._NHOM`, `geometry_generation_failed`).
   - `UNKNOWN_VERTEX_REF` → `"malformed"` (`REFUSAL_CLASS`).
   - `BRIDGE_UNSUPPORTED_LENGTH_UNIT` → `"unsupported"` (`REFUSAL_CLASS`) & `"CAPABILITY"` (`hybrid_preview._NHOM`, `capability_gap`).
3. Confirmed zero guards were weakened and zero invalid problems were allowed to serve.
4. Confirmed `test_every_refusal_code_of_the_route_is_classified` and `test_every_literal_route_d_refusal_code_is_classified` pass with `0` unclassified codes, and all governance invariants (`LLM_ONLY`, `flat`, `CACHE_VERSION = 127`, all 5 provider surface fingerprints) remain intact.

- **BLOCKER**: `0`
- **IMPORTANT**: `0`
- **MINOR**: `1` (operational reminder to re-freeze `EVALUATION_CANDIDATE.json` for measured hash `13fd32b498ea9e47f23f01d0f4efc99b7f8d789ed6e59fe814c8fc4891d7e172` and update the `CANDIDATE_DIVERGENCE/1` chain before running Full T3 Attempt 3 — completed).

**INDEPENDENT_REVIEW_PASS (`b6684564ac4596da30819da5fcc4c875ebb1a640`): no BLOCKER or IMPORTANT remains found in reviewed scope.**
