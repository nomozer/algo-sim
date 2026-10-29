# Closed input contract after source-grammar adjudication: NOT_READY, stopped at Gate D (MAJOR)

Owner decision `W3-F2 CLOSED INPUT CONTRACT ADJUDICATION`, 2026-10-30. Continuation of `../report.md`, which is left unchanged.
Branch `research/hybrid-v2-w3-f2-ratio-projection-language-grounding`. Main `996f114b` was not touched. 0 provider calls.
`DEFAULT_MODE=LLM_ONLY`, Hybrid opt-in, `ALLOW_LIVE_AI=0`, `CACHE_VERSION` 130.

## Commits

| commit | content |
|---|---|
| `4b361c47` | verbatim checkpoint of the uncommitted state on `5e44d5da` (backup with SHA-256 manifest first) |
| `aa245717` | registration: Owner addendum, amendment 1, acceptance manifest v2, pending and supported controls, qualification on `main` and HEAD |
| `39cad680` | tests follow manifest v2 + Gate A v2 receipts |
| this commit | Gate C/D receipts, stop finding CIC-D1, docs |

## Results

| gate | result |
|---|---|
| A: Closed Input Contract acceptance | **PASS**: 635 passed / 0 failed / 6 skipped (pre-existing); 9 mandatory mutants killed; 5 registered supported-positive nodes; 203 reviewer probes give 0 served negatives, 0 internal results, 0 positive losses, identical to `../stopped-product-probes.json` (`gate-a-v2.json`) |
| A: source-grammar diagnostics (separate) | **PENDING_SOURCE_GRAMMAR_SUPPORT**: 4 failed, `QUESTION_CONTEXT_UNSUPPORTED`; not counted as pass and not claimed as product support |
| B | PASS: since `5e44d5da` only the three authorized product files changed; kernel, engine, Registry /21, Planner /18 unchanged |
| C | PASS: locked 96/96, 0 wrong-served |
| D | **FAIL**: entire backend pytest: 13 failed / 13312 passed. 11 are stale freeze identity, failing identically at `5e44d5da`. 1 is an environment artifact: the tree was dirty during the run. **1 is a regression of a locked contract (CIC-D1)** (`gate-d-stop.json`) |

## CIC-D1 (MAJOR): locked V2 distance refusal changed

Locked test: `test_typed_fact_next_v2_distance_bridge.py::test_malformed_distance_target_is_refused[target8]` (since
`82097186`). Target `{"point": "A'", "plane": ["A","B","C"], "solid": "pr"}` must be `REFUSED INVALID_MATH_GOAL` on
Adapter /4. It passes on `main` and on `5e44d5da`. On this product it is **SERVED**. The same holds for `solid_id`.

The cause is `typed_fact_next.py::_validate_goal_target`, which admits `solid`/`solid_id` next to geometric operands as
ownership assertions (`../operand-grammar.md`). No wrong answer is served: the scope is the owning solid, and a foreign
scope is still refused on every route. Before the patch, Adapter /3 already served this input while Adapter /4 refused
it; the patch made both routes consistent but chose the opposite of the locked Adapter /4 contract.

The conflict comes from the contract itself. The preregistered N2 tests
(`test_legacy_constructed_ownership_precedes_capability[solid|solid_id]`) put a scope key inside a distance target and
expect `SOURCE_OBJECT_MISMATCH`, so they require that key to be read. The locked V2 contract refuses any scope key there.
Both cannot hold. I did not edit the product, change an expectation, or add xfail/skip.

Owner choice needed:
- (a) Keep the locked V2 contract. Scope keys are refused inside geometric targets, and ownership is asserted through the goal's `solid_id`.
  This is a product edit in `typed_fact_next.py`, plus a versioned amendment of the N2 expectations for the in-target forms.
- (b) Adopt the new grammar. This is a versioned, Owner-signed amendment of the locked `target8` expectation, applied the same way on every route.

Either path then reruns Gates A–D before the review.

## Not run (stopped by contract)

Independent pre-freeze adversarial review, Wave 3 replay, T0/T1/T2, new candidate freeze, Full T3, final review.
`tools/gates_v2.py` is prepared for gates/replay but was not run (it refuses this state). The freeze-dependent checks stay
`PENDING_NEW_FREEZE`. Not `READY_FOR_OWNER_REVIEW`.
