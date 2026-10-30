# ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT — current execution state

This is the canonical mutable checkpoint for the one Master Epic. After compaction, resume from Git and this file. Do not repeat W4 audits that are still valid.

**Identity**
- Branch: `research/hybrid-master-backend-replacement`, in worktree `.superpowers/worktrees/hybrid-master-backend-replacement`.
- The worktree has no venv of its own; use the root `backend/.venv`.
- Start baseline: `f986e897`. W4 closure: `main` = `origin/main` = live GitHub.
- W4 first remote verification: `94055c98`.
  - product `61ade29e`, candidate `182a7785`, measured 118 files `54b5b565…`;
  - cache 131, `LLM_ONLY`, live 0;
  - receipts in `../geometry-generalization-and-pedagogical-construction/integration/`.
- Cleanup: `SAFE_CLEANUP_COMPLETE_WITH_RETAINED_EXCEPTIONS`. The root-local log of that step is in `.superpowers/master-hybrid-backend-replacement/`.

**Commits**
- `f5ae588b`: the master contract, plan and this checkpoint.

**Task 1 — canonical source references and one identity authority: DONE** (receipt `task1-green.json`)
- `typed_fact_next_extraction.py`: immutable `SourceReference(path, spans)` on `ExtractionResult.source_references`.
  - It records every exact half-open code-point occurrence of each raw quote, overlapping ones included.
  - It is collected by the existing quote walker before normalization and returned only after full validation; a refusal returns `()`.
  - A provider cannot supply its own reference (`INVALID_TYPED_FACT_NEXT`). The provider schema and prompt are unchanged.
- `typed_fact_next_bridge.py::_kiem_pham_vi_tien_de`: the private identity copy is deleted. The bridge delegates to `canonical_vertex_ref`, the sole authority, and keeps its `TuChoi` code translation.
  - Root identities are unchanged.
  - A derived-solid namespace now resolves through its parent chart.
- Tests:
  - RED, then GREEN, for 5 new extraction tests and 1 bridge authority test.
  - One locked source-text mutant anchor was retargeted; the oracle and the fault (scope ignored) are unchanged.
  - Targeted run: 14679 passed. The only failures are 11 pending-freeze checks plus 1 dirty-tree check.

**Impact**
- `CACHE_VERSION` stays 131: `/api/analyze` cannot reach these modules.
- Model surface unchanged.
- Candidate re-freeze is **pending**. It belongs to Task 4, in a separate commit.

**State**
- Migration coverage: unchanged baseline. Hybrid /4 is local offline-replay opt-in. Live understanding and production cutover are `NOT_MEASURED` / `NOT_READY`.
- Remaining legacy, none retired yet:
  - `/api/analyze` still uses LLM_ONLY synthesis by default;
  - the old six-family compiler is still opt-in;
  - Adapter /3 compatibility capabilities have not migrated to /4.
- Open problems:
  - the canonical model lacks general standalone and composite coverage;
  - /4 refuses curved and qualified-identity cases by design;
  - there is no live provider budget;
  - all 20 migration gates need reconciling against the current code.

**Next exact action:** Task 2, recomposition and capability inventory.
1. Reconcile planner, Registry and engine against the contract, using the existing composition tests.
2. Record family states (`SUPPORTED_END_TO_END` / `SUPPORTED_WITH_LIMITS` / `REPRESENTABLE_ONLY` / `UNSUPPORTED`) per route in `capability-inventory.md`.

**Verdict so far:** `HYBRID_NOT_READY`. No production cutover and no legacy retirement is claimed.
