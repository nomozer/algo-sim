# Plan — `hybrid-reasoning-generalization` (Workstream B)

## PRE-FLIGHT (RULES §2)

```
Active branch:            feat/hybrid-reasoning-generalization
HEAD:                     d79565b52ec19a7b1a75be28c09bb43cc0f6d146 (COMMON_BASE_SHA)
Working tree:             clean at start (only this run directory added)
Current milestone:        Hybrid /4 reasoning & generalization (Planner /26, Registry /33, Engine /24, Adapter /4,
                          typed-fact-next/2, CACHE_VERSION 132 — read from code)
Task classification:      CORE (planner/engine generalization on the product route) + SUPPORTING (dev matrix, tests)
Thesis relevance:         R0 "LLM reads, deterministic engine animates": more textbook configurations served exactly,
                          or refused typed, without any per-problem rule
Existing related modules: geometry_functions/{planner,registry,engine,typed_fact_next_bridge}.py; ai/hybrid_offline.py;
                          runs hybrid-backend-capabilities / hybrid-production-composition / hybrid-goal-driven-planner
                          (tools/measure_*.py); hybrid-independent-h1 (H-1 preregistration + template already exist)
Existing functions/classes that may be reused:
                          run_hybrid_offline + ReplayExtractor (offline product path); _EffectResolver (bounded backward
                          search, memo, reuse, preconditions, telemetry); engine._tam_giac / _mot_buoc / _chieu_cao /
                          _dat_ngoai_day (layout); registry._kiem_result_binding chain verifier; custodian geometry_oracle
Source of truth:          code + tests; AGENTS.md §3; docs/RULES.md
Files expected to change: engine.py (layout), planner.py (budget scope), registry.py (chain quote evidence) — only if a
                          matrix gap proves it; new tests; this run directory; CODE_INDEX entry for the run tool
Contract/cache/history impact:
                          no TypedFactNext / bridge schema / Source Gate interface / API change. CACHE_VERSION decided by
                          evidence: changes may only turn REFUSED → SERVED (refusals are not cached).
Duplicate implementation risk:
                          a second planner/registry, a new oracle, a new H-1 framework — all excluded (exist)
Dependency-cycle risk:    none (edits stay inside geometry_functions; tool imports product read-only)
Scope-creep risk:         bridge-level gaps (described points in line operands, two described points per goal, nested
                          definitions, named three-point planes) touch the bridge contract ⇒ proposals only
Smallest sufficient implementation:
                          one engine layout rule pair, one budget-scope change, one evidence-union line in the verifier
Explicitly excluded work: frontend, ingestion/OCR, bridge/TypedFactNext schema, CURRENT_STATE/EVIDENCE_INDEX/
                          OPEN_ISSUES/AI_CONTEXT_BUNDLE/ROADMAP, live calls, MAX_EFFECT_DEPTH increase, H-1 results
Stop conditions:          a fix needs a shared contract change; a negative becomes served; search unbounded;
                          DEEP_HARDENING signs (RULES §3c)
```

## §2b anti-duplication checklist

1. Exact names searched: `_tam_giac`, `_hai_duong_cat_nhau`, `_chieu_cao`, `MAX_EFFECT_CANDIDATES`, `chain_quotes`,
   `measure_goal_driven_planning`, `geometry_oracle`, `H1_PREREGISTRATION`.
2. Same responsibility, other names: apex placement rules in `engine._mot_buoc` (regular pyramid centre, ⊥ two lines,
   face ⊥ base, `_rang_buoc_vuong`); Pythagoras in `_tam_giac` (right angle inside the base only); budget checks in
   `_EffectResolver._resolve` / `_dinh_nghia`; fresh-call quote evidence in `_kiem_phu` (union over certificates naming
   the construct) vs `_kiem_result_binding.chain` (union over chains only).
3. Callers: `bo_cuc_day` → `_tam_giac` (every triangle base); `giai_phu_thuoc` → `_mot_buoc`; resolver entries
   `goal`/`distance`/`point`; `kiem_nguon` → `_kiem_phu` → `_kiem_result_binding`.
4. CODE_INDEX: planner/registry/engine entries; prior run tools listed.
5. Reuse: prior run tools (`measure_goal_driven_planning.py`) for the measurement method (planner-only / kernel-only /
   cold-warm / tracemalloc) — re-implemented inside the new matrix tool only because that tool hard-wires its 10 cases
   and a sibling worktree path; the oracle is imported, not copied; H-1 framework untouched.

Post-flight: reused / created / duplicate check — see report §9.

## Steps

1. Dev matrix `tools/reasoning_matrix.py` (gold TypedFactNext /2 payloads → `run_hybrid_offline`), oracle values from
   `custodian/geometry_oracle.py`; run on the unmodified base → `results/matrix_before.json`.
2. Attribute each non-success to a root cause; rank; RED tests (+ strict-xfail reproductions for contract-level gaps).
3. Fix in rank order with the smallest diff; negatives + fault injection; bounded search.
4. Re-run the same matrix → `results/matrix_after.json`; render tables; targeted + full pytest; docs IA test.
5. Re-freeze candidate in a separate commit if `backend/app` changed; CACHE_VERSION decision; report + `run.json`.
