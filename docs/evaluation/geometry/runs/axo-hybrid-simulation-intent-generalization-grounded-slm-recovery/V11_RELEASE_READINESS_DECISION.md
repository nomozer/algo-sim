# V11 release readiness decision (Gate J10)

Quyết định lấy từ lượt mù (`V11_LIVE_ACCEPTANCE_RESULTS.json`) đo trên candidate đã đóng băng, chấm theo tiêu chí đăng ký
trước (`V11_ACCEPTANCE_CRITERIA_PREREGISTERED.json`). Mỗi verdict đứng riêng; không gộp thành một PASS.

| verdict | giá trị | bằng chứng |
|---|---|---|
| `SIMULATION_INTENT_GENERALIZATION_VERIFIED` | **FALSE (một phần)** | Câu yêu cầu đứng riêng: parser 31 test, Source Gate 34 test, hợp đồng SLM 6 test; tầng PARSER_COMPLETE hoàn tất 52/55. Câu yêu cầu **có khai báo lồng** chưa được nhận ở cả ba người đọc; SIMULATE_ONLY mù 22/39 = 0.564 |
| `GROUNDED_SLM_RECOVERY_VERIFIED` | **FALSE** | SLM_REQUIRED 4/30 = 0.133 [0.053, 0.297] < 0.30, và 4 < 5. Có bằng chứng tích cực: 4 cảnh SLM sống, đúng toán (/10: 0) |
| `FULL_STACK_LOCAL_ONLY_VERIFIED` | **TRUE** | backend thật + GGUF thật + trình duyệt thật; 58/58 đúng toán, 35/35 đáp số, 0 phục vụ sai, 0 mục tiêu bịa, 0 lượt gọi ngoài (4 lớp), 0 lỗi hạ tầng; T3 xem `V11_REGRESSION_REPORT.md` |
| `LIVE_SIMULATION_ACCEPTED` | **FALSE** | hoàn tất 56/85 = **0.659** [0.553, 0.751] < 0.85 |
| `SCOPED_CUTOVER_READY` | **FALSE** | theo sau `LIVE_SIMULATION_ACCEPTED` |
| `SCOPED_CUTOVER_COMPLETED` | **FALSE** | mặc định `HYBRID_ROUTE_MODE=live` không đổi; không có owner approval |
| `BLOCKED_SOURCE_GROUNDING` | **YES** | 13/26 ca SLM hỏng ở Source Gate với payload đã grounded; câu có khai báo lồng; luật "tất cả các cạnh", "biểu diễn <đại lượng>", tiêu đề đề thi |
| `BLOCKED_OWNERSHIP` | **YES** | Source Gate ngoài `_VAT_MO_PHONG`, cổng miền (patch không áp), planner/engine (underdetermined), adapter (nguồn gốc điểm O) |
| `BLOCKED_MODEL_EXTRACTION` | **NO** | lỗi mô hình thật 1–2 ca (S22 `contra`; C25 của /10) trên 26 + 20 ca đã kiểm |
| `BLOCKED_DOWNSTREAM_CAPABILITY` | **PARTIAL** | D02/D03 (hình xác định sai khác đồng dạng) bị báo "chưa hỗ trợ"; xem `UNDERDETERMINED_SIMULATION_SEMANTICS.md` |
| `BLOCKED_VISUAL_INTERACTION` | **NO** | tương tác 232/232; V17 và U08 đã sửa; còn mở V11-VIS-1 (2/58 cảnh cắt đỉnh), chưa đủ mức chặn |
| `BLOCKED_PERFORMANCE` | **NO (host dev)** | tuyến nhanh p95 62.7 ms; tuyến SLM p95 5172 ms; stack WS tối đa 2223 MB |
| `NOT_MEASURED` | — | độc lập ngoài (`EXTERNAL_INDEPENDENCE`), máy RAM 4–8 GiB thật, người học thật, tương đương Gemini |

## Quy tắc áp dụng

Độ phủ < 85% và SLM chưa đạt ngưỡng phục hồi ⇒ `LIVE_SIMULATION_ACCEPTED = FALSE`. Không có owner approval đổi mặc định
⇒ `SCOPED_CUTOVER_COMPLETED = FALSE`. Không tuyên bố hồi phục Model 1 dựa trên phần parser giải thêm.

## Việc kế tiếp duy nhất

Nhận diện **câu yêu cầu có khai báo lồng** ("Vẽ/Mô phỏng <khối> có/với/, <dữ kiện> [và/rồi tính …]") bằng một văn phạm
dùng chung cho parser, nhánh chỉ-mô-phỏng của SLM và văn phạm yêu cầu của Source Gate (cần owner mở thêm quyền Source
Gate). Đo trên **holdout mới** được viết và khoá trước khi sửa. Ở hậu kiểm, phép tách máy móc đã cứu 11/26 ca SLM_REQUIRED.
