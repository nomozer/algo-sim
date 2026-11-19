# Baseline, repository & ownership (P0 · Gate H0)

## Danh tính đã xác minh (2026-11-19)

| Hạng mục | Bàn giao /9 | Xác minh /10 | Cách kiểm |
|---|---|---|---|
| Worktree /9 | `.superpowers/worktrees/local-first-geometry-understanding` | có, sạch | `git worktree list`, `git status` |
| Nhánh / HEAD /9 | `feat/local-first-geometry-understanding` @ `38c6efbdb` | khớp | `git log` |
| Quan hệ với `main` | — | `main` = `bb046fa22`; nhánh /9 đi trước 285 commit, sau 0 | `git rev-list --count` |
| Candidate đo /9 | cây `a7a6bc41…`, 123 file | khớp | `freeze_evaluation_candidate.py --verify` |
| `CACHE_VERSION` | 145 | 145 | `backend/app/main.py:950` |
| Mặc định `HYBRID_ROUTE_MODE` | `live` | `live` (xác nhận cả bằng chạy thật: không đặt biến ⇒ `routeMode=live`, `503 MISSING_API_KEY`) | `main.py::hybrid_route_mode`, `evidence/runtime/rollback_route_default_live.jsonl` |
| Model AxoV9 | `73f1484b…dc6cc35` | khớp (sha256sum file thật) | `%LOCALAPPDATA%/axo-slm/models/…AxoV9…gguf` |
| Model AxoV7 (rollback) | `36e784d1…5e148` | khớp | idem |
| llama.cpp | b12470 | `version 1.0.0-dev (build 12470, commit dde9de82c)` | `llama-server --version` |
| Namespace cache SLM | `HYBRID_V9_LOCAL_SLM` | có trong mã | `local_slm_runtime.py:38` |
| Run /5–/9 đông cứng | không đổi | run này không ghi vào thư mục run cũ nào | `git diff --stat` của nhánh tích hợp |

## Bản vá bàn giao /9 — kiểm lại, không áp nguyên xi

| Bản vá | Kết quả kiểm | Quyết định |
|---|---|---|
| `frontend_local_ai_status_and_keyless_ux.patch` | Phủ đủ 4 chỗ đọc `hasKey` trong `frontend/src` (grep); `git apply --check` sạch; worktree chủ frontend `axo-geometry-library` không sửa dở hai file này. **Thiếu** một chỗ: 503 cục bộ vẫn hiện câu "chưa bật kết nối AI". | Áp trên nhánh tích hợp + bổ sung (commit `e10697092`) |
| `default_cutover_local_only_scoped.patch` | Áp được; đổi mặc định khi biến trống. | **Không áp** (quyết định owner) |
| `source_gate_optional_grammar.patch` | Chạm `registry.py` (Source Gate). | **Không áp** (owner: không sửa planner/registry/typed facts) |

## Quyền sở hữu — quyết định của owner trong phiên này

| Câu hỏi | Owner chọn |
|---|---|
| Frontend `frontend/**` | Được sửa **trên nhánh tích hợp mới** `integration/local-only-3d-live-acceptance` (từ `38c6efbdb`); không merge, không push |
| Mặc định `live` → `local-only-scoped` | **Không đổi**; chỉ rehearsal bằng biến môi trường |
| Planner / Registry / TypedFacts | **Không sửa**; chỉ ghi giới hạn và đề xuất |

Ngoài ba vùng trên, run sửa đúng một module backend: `backend/app/ai/local_slm_runtime.py` (lỗi keep-alive tìm thấy bằng live
test, không thuộc vùng bị khoá), có test nền đỏ, và đóng băng lại candidate ở commit riêng.

## Commit của nhánh tích hợp

| Commit | Nội dung |
|---|---|
| `e10697092` | frontend keyless: bản vá /9 + thông điệp 503 cục bộ + test `local-ai-keyless-ux.test.tsx` + mục CODE_INDEX |
| `451a59040` | đóng băng manifest, oracle, harness và **ngưỡng nghiệm thu** trước lượt chạy đầu |
| `7554e2b72` | fix(local-slm): socket keep-alive cũ ⇒ kết nối lại, không báo crash; test `test_local_slm_keepalive_stale_socket.py` |
| `a0f979392` | đóng băng lại candidate (cây `ce3e3c4b…`, 123 file) trong worktree detached sạch |

**Gate H0: PASS** (danh tính khớp; quyền sở hữu được owner giải quyết trong phạm vi nêu trên).
