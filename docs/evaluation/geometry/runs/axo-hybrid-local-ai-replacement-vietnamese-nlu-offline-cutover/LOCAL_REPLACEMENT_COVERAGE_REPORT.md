# AXO HYBRID /9 — Local Replacement Coverage Report

> Companion coverage summary for `GEMINI_DEPENDENCY_INVENTORY.json` and `GEMINI_REPLACEMENT_COVERAGE_REPORT.md` (§18 & §39).

- **Generated:** `2026-11-19`
- **External AI Calls:** `0`
- **Total Gemini Dependency Surfaces Audited:** `9` across `11` backend files and `4` frontend files.

## Coverage Summary by Migration Category

| Migration Status | Count | Surfaces Covered | Local-Only Product Disposition |
|---|---:|---|---|
| `REPLACE_WITH_LOCAL` | `3` | `GEM-01`, `GEM-02`, `GEM-08` (backend part) | Handled locally without `GEMINI_API_KEY` via `HYBRID_ROUTE_MODE=local-only-scoped`, `offline-lab`, `LocalSlmHybridRun` (`slm-verified-normalizer/3` + `Qwen3-0.6B-AxoV9-Q4_K_M` + `slm-grounding-validator/4`), and `/api/health` readiness flags. |
| `REPLACE_WITH_DETERMINISTIC` | `1` | `GEM-04` (`/api/input/prepare`) | Deterministic `.docx` / text-layer PDF + local OCR (`run_local_ocr_route` + span confirmation); `vision_allowed=False` and `api_key=None` enforced in local-only modes. |
| `DISABLE_AS_UNSUPPORTED` | `2` | `GEM-03` (legacy `input.type=='image'`), `GEM-05` (`/api/image/extract`) | Hard-blocked in local-only modes (`400 IMAGE_DIRECT_UNSUPPORTED` / `503 LOCAL_ONLY_CLOUD_VISION_DISABLED`), zero fallback to `call_gemini`. |
| `RETAIN_CODE_DISABLED` | `2` | `GEM-06` (4 locked Gemini modules), `GEM-07` (`skills/*.md`) | Locked upstream surfaces preserved byte-identical (`typed_fact_next_surface = 33197a45…`) and never called on local-only routes. |
| `OUTSIDE_APPROVED_SCOPE` | `1` | `GEM-09` (frontend `AuthGate.tsx`, `ProblemInput.tsx`, `client.ts`) | `BLOCKED_OWNERSHIP` in separate `axo-geometry-library` worktree; additive UX patch delivered cleanly in `handoff/frontend_local_ai_status_and_keyless_ux.patch` (`git apply --check` PASS). |

## Remaining Replacement Gaps

1. **Owner-gated default cutover & frontend UX:** Default `HYBRID_ROUTE_MODE` remains `"live"` until the owner applies `handoff/default_cutover_local_only_scoped.patch` and `handoff/frontend_local_ai_status_and_keyless_ux.patch`.
2. **Multimodal cloud vision OCR:** Scanning handwritten/noisy photos without local span confirmation still requires cloud VLM in `"live"` mode and is explicitly disabled (`503 LOCAL_ONLY_CLOUD_VISION_DISABLED`) in local-only mode.
3. **Full details:** See [`GEMINI_DEPENDENCY_INVENTORY.json`](GEMINI_DEPENDENCY_INVENTORY.json) and [`GEMINI_REPLACEMENT_COVERAGE_REPORT.md`](GEMINI_REPLACEMENT_COVERAGE_REPORT.md).
