# Hồi quy (P9 · Gate H8)

## T3 — cổng sản phẩm đầy đủ (`frontend/scripts/full-gate.mjs`)

### Lần 1 — HEAD `a0f979392` (sau fix keep-alive + đóng băng lại), cây làm việc có tài liệu run chưa commit

| Cổng con | Kết quả |
|---|---|
| pytest toàn bộ backend | **FAIL** — 15 100 passed, **2 failed**, 9 skipped, 12 xfailed (1116.5 s) |
| vitest toàn bộ frontend | PASS — 143 file, 2066 test |
| typecheck + build | PASS |
| tập demo khoá luận | PASS 5/5 |
| bề mặt sập của demo | PASS 6/6 |

Hai test đỏ: `test_s2_student_language_pilot_runner.py::test_c21_registered_approval_templates_bind_current_runtime_identity_and_stale_runner_is_refused`
và `::test_sha256_file_and_approval_terms_are_invariant_under_windows_crlf_checkout`.
**Root cause:** ba template phê duyệt đang chờ owner (K-1, S-2, R-1, `PENDING_OWNER_DECISION`) ghim `measured_system = a7a6bc41…`;
đóng băng lại candidate (`ce3e3c4b…`) làm chúng lệch — guard hoạt động đúng thiết kế (runner cũ bị từ chối).
**Sửa:** thủ tục có sẵn của kho (như /9): chép `refresh_pending_templates.py` sang run này, gắn lại đúng hai trường
`measured_system`/`measured_system_tree_hash`; `owner_decision` và `paid_project_confirmed` không đổi (diff xác nhận 0 dòng chạm),
bản cũ lưu `logs/prior-*.template.json`, bản ghi `pending_template_refresh.json`. Commit `5a07be9b4`. File test: 106/106.

### Lần 2 — sau khi commit toàn bộ run

Xem mục "Kết quả T3 lần 2" bên dưới (điền từ log thật).

## Hồi quy có mục tiêu đã chạy trong run

| Bộ | Kết quả |
|---|---|
| `test_local_slm_keepalive_stale_socket.py` (mới) | nền đỏ 2/5 → 5/5 |
| runtime/local-only: `test_slm_finetuned_runtime`, `test_local_only_product_and_network_isolation`, `test_scoped_local_routing_policy` | 18/18 (gồm test mới) |
| `test_cache_identity.py`, `test_current_state_identity.py` | 18/18 |
| frontend liên quan (keyless, v28 UX, error experience, failure taxonomy, photo flow, ui-hygiene) | 52/52 |
| `local-ai-keyless-ux.test.tsx` (mới) | nền đỏ 1/4 → 4/4 |
| `test_docs_information_architecture.py` | xanh sau ghi ngược tài liệu |

## Bất biến

- Source Gate, planner, registry, engine, typed facts: **0 dòng thay đổi** (`git diff 38c6efbdb -- backend/app/simulation` rỗng).
- Construction /1–/2 (`backend/experimental/construction_planner/**`) không đổi; run /5–/9 không đổi.
- Không có `APPROVED_BY_USER` nào được ghi; không gọi Gemini.
