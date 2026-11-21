# Tóm tắt gate H0–H10

Số liệu chính: lượt 2 (candidate `a0f979392`, cây `ce3e3c4b…`), trình duyệt thật, `local-only-scoped`, manifest đóng băng
`8c00975c…` (64 hợp lệ / 18 âm). Lượt 1 (mù, candidate /9) báo song song. Wilson 95%.

## Ngưỡng đăng ký trước (`ACCEPTANCE_FREEZE.json`, commit `451a59040`) so với kết quả

| Ngưỡng | Lượt 1 | Lượt 2 | Đạt? |
|---|---|---|---|
| Cảnh phục vụ sai toán học = 0 | 0/38 | 0/40 | ✅ |
| Đáp số phục vụ sai = 0 | 0/25 | 0/26 | ✅ |
| Ca âm phục vụ sai = 0; toạ độ tiêm bị làm theo = 0 | 0; 0 | 0; 0 | ✅ |
| Request trình duyệt ra ngoài = 0; bản ghi proxy egress = 0; lượt gọi provider = 0 | 0; 0; 0 | 0; 0; 0 | ✅ |
| Lỗi hạ tầng hiển thị thành từ chối hình học = 0 | 0 | 0 | ✅ |
| Hiển thị: mỗi cảnh phục vụ đạt đủ tiêu chí | 38/38 | 40/40 | ✅ |
| Simulation Completion Rate ≥ 0.85 | 0.59 [0.47, 0.71] | **0.625 [0.50, 0.73]** | ❌ |
| Geometry Correctness = 1.0 | 1.0 | 1.0 [0.91, 1.00] | ✅ |
| Visual Rendering Success = 1.0 | 1.0 | 1.0 [0.91, 1.00] | ✅ |
| Interaction Success = 1.0 | 0.993 | **0.994** (159/160) | ❌ (V17 xoay) |
| Safe Refusal = 1.0 | 1.0 | 1.0 [0.82, 1.00] | ✅ |
| First visible scene p95 ≤ 5000 ms (host này) | 8827 ms | **456 ms** | lượt 2 ✅ |

Numeric Answer Accuracy (chỉ ca có hỏi số): lượt 2 26/26 = 1.0 [0.87, 1.00].

## Gate

| Gate | Trạng thái | Căn cứ |
|---|---|---|
| H0 Baseline | **PASS** | `BASELINE_AND_OWNERSHIP_AUDIT.md` |
| H1 Simulation intent | **PASS** (đã đánh giá ba chế độ; 0 mục tiêu số bịa; hình chưa xác định được phân loại an toàn) — nhưng độ phủ Mode A thấp | `SIMULATION_GOAL_SEMANTICS.md` |
| H2 Mathematical scene correctness | **PASS** | 40/40 cảnh, 252 quan hệ, 0 vi phạm; oracle độc lập |
| H3 Live browser rendering | **PASS** | `BROWSER_RENDER_VERIFICATION_REPORT.md` |
| H4 Interaction | **PASS có ghi chú** — ngưỡng 1.0 trượt 1 thao tác (V17), U08 lệch nhãn 8 px | idem |
| H5 Keyless UX | **PASS** + 3 giới hạn UX | `LOCAL_ONLY_FRONTEND_INTEGRATION_REPORT.md` |
| H6 Offline security | **PASS** cho `NO_EXTERNAL_AI`; `FULLY_OFFLINE_RUNTIME` không tuyên bố | `OFFLINE_NETWORK_LIVE_TEST_REPORT.md` |
| H7 Performance & resource | **PARTIAL** — xem `END_TO_END_SIMULATION_PERFORMANCE.json`, `FULL_STACK_MEMORY_REPORT.md`; phần cứng 4–8 GiB `NOT_MEASURED` | |
| H8 Regression | **PASS** — T3 `FULL_PRODUCT_GATE_PASS` tại `28badc70b` (pytest 15 102, vitest 2066, build, demo); lần 1 đỏ 2 test vì template chờ owner ghim candidate cũ — đã gắn lại (metadata) | `SIMULATION_REGRESSION_REPORT.md` |
| H9 Cutover rehearsal | **PASS (staging bằng biến môi trường)**; rollback PASS; default không đổi theo owner | `CUTOVER_REHEARSAL_REPORT.md`, `ROLLBACK_VALIDATION_REPORT.md` |
| H10 Release decision | `FULL_STACK_LOCAL_ONLY_VERIFIED`; `LIVE_SIMULATION_ACCEPTED = FALSE`; `SCOPED_CUTOVER_COMPLETED = FALSE` | `PRODUCTION_CUTOVER_DECISION.md` |
