# AXO HYBRID /9 — Owner Handoff Package (Read-Only Patches for Restricted Surfaces)

> **Ownership Compliance:** `frontend/**`, `registry.py`, `planner.py`, `engine.py`, `backend/experimental/construction_planner/**`, and all 4 locked Gemini surfaces remained untouched (`0` working-tree edits) during `AXO HYBRID /9`.  
> All owner-only changes are delivered below as dry-run verified (`git apply --check`) unified patches under [`handoff/`](./handoff/).

---

## 1. Patch Inventory & Verification Status

| Patch File | Target Surface | Purpose | `git apply --check` | Apply When |
| --- | --- | --- | --- | --- |
| [`frontend_local_ai_status_and_keyless_ux.patch`](./handoff/frontend_local_ai_status_and_keyless_ux.patch) | `frontend/src/llm/client.ts`, `frontend/src/components/ProblemInput.tsx` | Consume `/api/health` additive fields (`aiAvailable`, `localOnlyMode`, `localSlmReady`) via `isAiAvailable(health)` so keyless local deployments stop showing missing cloud key errors. | **PASSED (`exit 0`)** | When enabling `local-only-scoped` or `local-only-general` in UI |
| [`default_cutover_local_only_scoped.patch`](./handoff/default_cutover_local_only_scoped.patch) | `backend/app/main.py` (`hybrid_route_mode`) | Switch default fallback when `HYBRID_ROUTE_MODE` is unset from `"live"` to `"local-only-scoped"`. | **PASSED (`exit 0`)** | Only when owner explicitly approves offline scoped production cutover |
| [`source_gate_optional_grammar.patch`](./handoff/source_gate_optional_grammar.patch) | `backend/app/simulation/geometry_functions/registry.py` (`atomic_forms`) | Optional conversational Vietnamese lead-ins (`một`, `ta có`, `đề yêu cầu khảo sát`) for `pyramid`/`rectangle` atomic forms without relaxing vertex or quote strictness (addresses `SOURCE_PREMISE_UNREAD` observed on `/7` residual holdouts). | **PASSED (`exit 0`)** | Optional owner review after verifying Source Gate invariants |

---

## 2. Explicit Scope Boundaries Maintained

- Default production behavior when `HYBRID_ROUTE_MODE` is unset remains **`"live"`** (Gemini `typed-fact-next/2`).
- Enabling `HYBRID_ROUTE_MODE=local-only-general` requires an explicit operator acknowledgement flag (`AXO_ALLOW_GENERAL_LOCAL_CUTOVER=1`); otherwise the server fails closed (`503 LOCAL_ONLY_GENERAL_NOT_APPROVED`).
- Cloud vision endpoints (`/api/image/extract`, scanned images in `/api/input/prepare`) remain explicitly disabled in local-only modes (`503 LOCAL_ONLY_CLOUD_VISION_DISABLED`) because Qwen3-0.6B is text-only and physical OCR coverage on arbitrary photos requires either cloud VLM or user confirmation.
