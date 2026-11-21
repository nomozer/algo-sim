# Baseline & ownership audit (P0)

## Baseline

| mục | giá trị |
|---|---|
| nhánh | `feat/simulation-intent-slm-recovery` (worktree `.superpowers/worktrees/simulation-intent-slm-recovery`), rẽ từ `2f12b96b0` (đầu nhánh /10 sau T3 PASS) |
| `main` | không chạm; không merge, không push |
| đăng ký trước | `5d0e86dad` — `V11_LIVE_ACCEPTANCE_MANIFEST.json` (sha `86136867…`) + `V11_ACCEPTANCE_CRITERIA_PREREGISTERED.json`, commit **trước** dòng mã /11 đầu tiên |
| mặc định | `HYBRID_ROUTE_MODE = live` không đổi (cutover chỉ bằng biến môi trường) |
| Gemini | 0 lượt gọi trong mọi phép thử local-only (proxy hố đen + mẫu TCP, xem `NETWORK_ISOLATION_REVALIDATION.md`) |
| mô hình | `qwen3-0.6b-axo-v9-q4_k_m` sha `73f1484b…`, llama.cpp `b12470`; 0 fine-tuning |

## Quyền sở hữu (owner 2026-11-20, qua câu hỏi trong phiên)

| bề mặt | quyết định | thực tế trong /11 |
|---|---|---|
| Parser cục bộ + SLM adapter (`local_geometry_parser.py`, `local_slm_extractor.py`) | được sửa | `0557dcaf6`, `fcf68e91b` |
| Frontend | được sửa | `3e5eb8809`, `b15fd9e92` |
| Source Gate | chỉ sửa hẹp `_VAT_MO_PHONG` (owner duyệt sau khi thấy SLM20) | `806a7d338` — chỉ văn phạm yêu cầu mô phỏng; không nới toàn cục |
| `detect_domain` (cổng miền) | chỉ patch + handoff | `handoff/domain_gate_diacritic_free.patch`, **không** áp |
| Planner / Engine / Kernel / TypedFactNext | khoá — prototype cô lập + handoff | 0 diff (`git diff 2f12b96b0 HEAD` rỗng trên `planner.py`, `engine.py`, `typed_fact_next_extraction.py`, `adapter4_route.py`, `hybrid_preview.py`, `domain_profile.py`) |
| `hybrid_preview` | không được chọn ⇒ khoá | 0 diff |
| Construction /2 `backend/experimental/construction_planner/` | khoá | giống từng byte với commit đóng băng `03200886a` (`git diff --quiet 03200886a HEAD` ⇒ 0) ⇒ `CANDIDATE_V2_FREEZE_SHA256 = 26c9b505…` vẫn đúng |
| Run đóng băng /5–/10, Construction /1–/2 | bất biến | 0 sửa; công cụ /10 được **chép** vào `tools/` của /11 trước khi dùng |

## Diff sản phẩm của /11 (so với `2f12b96b0`)

`backend/app`: `local_geometry_parser.py`, `local_slm_extractor.py`, `geometry_functions/registry.py` (hẹp), `main.py`
(`CACHE_VERSION` 146). `frontend/src`: `ProblemInput.tsx`, `llm/client.ts`, `scene3d-view.tsx` + 3 test + 1 fixture.
Tổng 10 file, +490/−32.

## Nhận dạng bề mặt mô hình

`semantic_environment_fingerprint` (prompt, thẻ văn phạm, lược đồ, capability hash, bề mặt TypedFactNext/Hybrid)
**không đổi**: `tests/test_cache_identity.py` xanh trước và sau. Bề mặt *quyết định* đổi (Source Gate, parser, SLM
lowering) ⇒ `CACHE_VERSION` 145 → 146, xem `CACHE_SEMANTIC_IDENTITY_DECISION.md`.
