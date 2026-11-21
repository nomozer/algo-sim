# Quyết định cutover production (Gate H10)

## Verdict

| Verdict | Trạng thái | Lý do ngắn |
|---|---|---|
| `BACKEND_LOCAL_ONLY_VERIFIED` | **TRUE** | route local-only thật, keyless, 0 lời gọi AI ngoài, lỗi runtime fail-closed, rollback model |
| `FULL_STACK_LOCAL_ONLY_VERIFIED` | **TRUE (trên nhánh tích hợp)** | frontend keyless thật + backend thật + GGUF thật + trình duyệt thật; 40/40 cảnh đúng toán và đúng hiển thị |
| `LIVE_SIMULATION_ACCEPTED` | **FALSE** | trượt ngưỡng đăng ký trước: completion 0.625 [0.50, 0.73] < 0.85; interaction 159/160 < 1.0 |
| `SCOPED_CUTOVER_READY` | **FALSE** | hệ quả của dòng trên; thêm: SLM không phục vụ được cảnh nào trong bộ này (0/20) |
| `SCOPED_CUTOVER_COMPLETED` | **FALSE** | mặc định vẫn `live` (xác nhận bằng chạy thật); owner chọn không đổi |
| `BLOCKED_OWNERSHIP` | **một phần** | mở rộng câu lệnh mô phỏng ở `local_geometry_parser.py` và thông điệp thiếu dữ kiện cần owner duyệt |
| `BLOCKED_VISUAL_VERIFICATION` | FALSE | đã xem trên trình duyệt |
| `BLOCKED_MATHEMATICAL_CORRECTNESS` | FALSE | 0 cảnh sai, 0 đáp số sai |
| `BLOCKED_PERFORMANCE` | FALSE trên host đo | cảnh phục vụ: first visible p95 456 ms; đường SLM round trip p95 8.4 s (không phục vụ cảnh) |
| `BLOCKED_HARDWARE` | `NOT_MEASURED` | chưa đo máy 4–8 GiB thật |

**Kết luận: `FULL_STACK_LOCAL_ONLY_VERIFIED`, chưa `LIVE_SIMULATION_ACCEPTED`. Không đổi mặc định.**

## Vì sao không đủ điều kiện cutover dù an toàn

1. **An toàn đạt trọn:** không cảnh sai, không đáp số sai, không phục vụ ca âm, không egress, lỗi model báo đúng là lỗi model.
2. **Độ phủ không đạt:** 24/64 đề hợp lệ bị từ chối (an toàn). Root cause chính là độ phủ câu lệnh mô phỏng của parser tất định
   (11 ca SIMULATE_ONLY) và việc SLM không vượt Source Gate cho mục tiêu dựng hình (`SOURCE_OBJECT_MISMATCH`, `AMBIGUOUS_FACT`).
3. **"Local AI" trong bộ này là parser tất định:** 40/40 cảnh phục vụ đi qua `LOCAL_DETERMINISTIC_PARSER` (không LLM); đường
   `LOCAL_SLM_GROUNDED` phục vụ 0/20 (Wilson [0, 0.16]). Không được mô tả là "Model 1 trích xuất đúng quan hệ" trên bộ này.
   Điều này khác với 40 lượt SLM phục vụ của `SLM_V9_UNSEEN_150` ở /9 (bộ khác, đo ở tầng backend) — không mâu thuẫn số học,
   nhưng cho thấy kết quả /9 không chuyển sang được phân bố câu lệnh mô phỏng của run này.
4. Lỗi keep-alive (đã sửa) cho thấy benchmark backend liên tục không thay được live test có quãng nghỉ thật.

## Điều kiện để cân nhắc lại `SCOPED_CUTOVER_READY`

- Owner duyệt và triển khai mở rộng câu lệnh mô phỏng (luật 7b dùng chung, không theo đề) + đo trên một bộ **mới, mù**.
- Thông điệp thiếu dữ kiện đưa câu hỏi làm rõ tới UI; đề không dấu không bị gắn "môn học khác".
- Đo phần cứng đích 4–8 GiB và một phép thử ngắt Internet thật nếu muốn tuyên bố offline hoàn toàn.
- Merge hai commit sản phẩm của nhánh tích hợp (frontend keyless, fix keep-alive) theo quyết định owner — fix keep-alive nên
  vào bất kể cutover, vì nó ảnh hưởng mọi chế độ dùng SLM (`local-*`, `offline-lab`, `local-shadow`).
