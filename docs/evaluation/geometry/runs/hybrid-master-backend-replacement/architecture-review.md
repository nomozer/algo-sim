# Independent backend architecture review: `INDEPENDENT_BACKEND_ARCHITECTURE_REVIEW_READY`

- **Reviewer:** a fresh-context subagent of this session. It was interrupted once by the session usage limit and resumed from its own saved work.
- **Scope:** product runtime `f986e897..cc2d56b9` under `backend/app`. HEAD was `6f01309c` at the time; nothing under `backend/app` changed after `cc2d56b9`.
- **Conditions:** read-only (`git status` clean at the end); 0 provider calls. Probes and logs stayed in the session scratch directory and are not copied here.

**Result:** 0 BLOCKER, 0 MAJOR, 4 MINOR.

## Findings and disposition

| id | finding | disposition |
|---|---|---|
| M-1 | Delegating the bridge identity changes one refusal path. Before Task 1, `top_pyramid::S` with two roots owning `S` was `AMBIGUOUS_REFERENCE`. It now resolves through the parent and is refused downstream. Observed as 12 old/new disagreements over 13 354 tests, all `R2.derived_*`, all still never served. | **Closed (test).** The old behavior contradicted the Owner-registered R2 oracle (`_r2_identity_oracle`: a derived solid resolves through its parent), so the delegation fixed an inconsistency. The new refusal code `BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY` on `pl` and `a4` is pinned by `test_typedfactnext_planner_bridge.py::test_derived_namespace_refusal_after_delegation_is_a_capability_code`. |
| M-2 | Route D cache identity covers version constants, not code. A kernel or validator fix without a version bump would keep serving old SERVED rows. | **Closed (rule).** The bump rule is written into `MIGRATION_CHECKLIST.md` D-02. This is the same discipline as the LLM_ONLY cache. |
| M-3 | If `build_adapter4_response` also raises while building the refusal envelope, the request returns HTTP 500. No cache row is written and there is no fallback. The code comment promises "never a 500". | **Deferred to the next product change.** Any `backend/app` edit invalidates the frozen candidate and Full T3, and this is a doubly-faulted adapter whose effect is a 500, not a wrong-served result. It is fixed together with the next product change, which at the latest is cutover preparation. |
| M-4 | Stale docstrings: `main._hybrid_v2_local` still says "không đọc, không ghi cache", and `adapter4_route` still says "not wired to /api/analyze". The ops script `cache_clear.py --de` could not delete Route D rows. | **Script closed:** `--de` now also deletes Route D rows whose stored text matches exactly (`test_hybrid_route_d_cache_and_rollback.py::test_the_ops_script_can_delete_a_route_d_row_by_its_exact_text`). `--cu` treating `131:route-d` as current is correct. **Docstrings deferred** with M-3, for the same reason. |

## What the reviewer verified, with its own probes

- **Existing suites:** the 10 named suites passed, 2456 passed and 6 skipped.
- **18 new probes:** 18/18 pass. They used new prism payloads under the conftest network guard. Results:
  - Route D really executes, and LLM_ONLY never runs.
  - 9 grounding-bypass mutations are refused and not cached: `UNGROUNDED_VALUE`, `QUOTE_NOT_IN_SOURCE`, `SOURCE_OBJECT_MISMATCH`, `REPLAY_SOURCE_IDENTITY_MISMATCH`.
  - Exact versus normalized key: an upper-cased variant is not a hit.
  - Cache isolation both ways: `131` and `131:route-d` rows coexist.
  - Rollback: an entry removed from the corpus is refused, never served stale.
  - Poisoned rows are a MISS.
  - A route fault becomes `ROUTE_INTERNAL_ERROR`.
  - `kernel_check=False` is never served.
  - A non-loopback client never sees Route D.
- **LLM_ONLY section of `analyze()`:** byte-identical to `f986e897`. `ROUTE_D_CACHE_POLICY` fits `String(16)`. The adapter adds no geometry authority.
- **Retain until parity:** Adapter /3 (curved solids), qualified identity, and compiler C. This was read from code, not probed.
