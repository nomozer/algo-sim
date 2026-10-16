# Handoff — goal-directed-function-discovery

- **Status:** `FUNCTION_DISCOVERY_SLICE_READY_FOR_REVIEW` (T3 + review: `report.md` §7).
- **Branch:** `research/goal-directed-function-discovery`, stacked on `8c24cb52` (result binding `f83b4ed1` + Scene3D W1–W3,
  both not integrated; Scene3D independent review still pending). `main` = `origin/main` = `2a3c0787`; nothing pushed.
- **Commits:** preregistration `66593504` · RED `b30c46af` · product `9fec9f43` → review fixes `cfa27baa` (final product) ·
  inherited Scene3D test typing fix `19eec205` · final refreeze `81315986` (candidate `093359c2…`, 110 files, frozen at
  `313cc537`) · docs (SELF). Full chain and both T3 attempts: `run.json`, `report.md` §7.
- **Invariants:** `LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid product enablement NO-GO, 0 Gemini calls, provider surfaces
  A `7ea511a6…` / B `485d3834…` / declarations `5ceb0f99…` / fact schema `282f5f76…` unchanged, `frontend/public/` (user) untouched.

## What a successor needs

1. Integration order is forced by the stack: result binding (user GO/NO-GO) → Scene3D W1–W3 (independent review, its own
   refreeze/T3 are subsumed by this run's candidate only for backend paths) → this slice. A cherry-pick of this slice onto a
   different base is possible: it touches only route-D backend files, two frontend harness scripts and docs.
2. Reproduce: `backend/scripts/measure_function_discovery.py` (`bundle` → `arm` per worktree/variant → `compare`; `scenes`
   for the harness). Inputs are frozen (`corpus.json`, `oracle.py`, bundle sha in `baseline/bundle.sha256`).
3. Open: `ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE` (D-1), the remaining items of
   `ISSUE-ARCH-PLANNER-RESULT-BINDING-AND-EFFECT-DISCOVERY`, live extraction of the descriptor transport (`NOT_MEASURED`;
   the provider prompt was deliberately not changed), human visual review of the 6 fixtures (`visual/images/`).
4. Next slice proposal: `report.md` §9 (general question goal entry first). Not started; needs the user's decision.
