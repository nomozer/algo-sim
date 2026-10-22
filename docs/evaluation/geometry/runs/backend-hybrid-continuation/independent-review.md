# Independent review — continuation

Reviewer agent: `/root/independent_backend_review` (separate read-only context). This file transcribes the review returned to the coordinator. No file edits or commits by reviewer; no provider/full-suite/browser/T3 execution by reviewer.

Scope: inherited full product diff `43247c9e` → `8b5916e`, connected code/tests, plan/architecture, four previous reviews, evaluation code/results, and Codex fixes through `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee`.

## Findings resolved before candidate freeze

1. IMPORTANT: `_ref` discarded namespaces. Unknown solid/local vertex references and unknown namespaces in named_intersections keys could serve. Now typed refusals, valid declared qualifiers and edge keys still serve.
2. IMPORTANT: explicit length_unit dropped. Symbolic lengths + unit 1 now refuse NON_HOMOGENEOUS_LENGTHS; explicit a + numeric-only facts refuses BRIDGE_UNSUPPORTED_LENGTH_UNIT (conservative unsupported representation).
3. IMPORTANT: malformed Any premise args could escape as KeyError/AttributeError. Missing/non-string operands and malformed qualifier syntax now return typed refusals. Same Adapter /3 vulnerability is pre-existing and remains outside Session 1.
4. IMPORTANT: declared cutting-plane name dropped. β or reference-plane ABC served as α. Declared names are now preserved and compared against Source Gate verified engine output; bridge does not parse source text.

Independent final confirmation: **12 passed, 54 deselected, 1.41 s** for targeted boundary tests. Direct positive controls: matching unit, known qualified edge keys, metadata goal ID g::S. Seven additional contradictory cut/context probes refused. Final source `4f3aaea5e0d3b5c1fe1537bd3ddf4bc73cbe88ee`.

Remaining MINOR/limits: generated premise ID p1 can collide with an authored ID and cause typed false refusal; two-line planes with cut clauses unsupported; derived prisms excluded; quadrilateral/perpendicular plans may exceed IR budget; auxiliary plane points remain visible. These cannot support broad composition or production claims.

Correction-layer approach is compliant if historical receipts stay byte-identical and EVIDENCE_INDEX registers CORRECTED_BY. Product fixes require a new measured hash and clean freeze.

**INDEPENDENT_REVIEW_PASS: no BLOCKER or IMPORTANT remains found in reviewed scope.** Proceed to fresh freeze and Full T3. Hybrid production remains NO-GO. This verdict is code review, not a Full T3 result.
