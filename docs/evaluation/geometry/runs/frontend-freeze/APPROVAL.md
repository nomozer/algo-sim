# APPROVAL — tích hợp baseline frontend tạm thời có ngoại lệ (nhánh feat/regular-square-pyramid)

Lớp ghi nhận mới của run `frontend-freeze`, 2026-10-09. Ghi bởi agent theo lời người dùng (tiền lệ
`runs/cuboid-merge/APPROVAL.md`); agent không tự phê duyệt, không suy phê duyệt từ kết quả tự động, và không sửa lịch sử kiểm
thử. Đây KHÔNG phải `APPROVED_BY_USER` cho chất lượng giao diện.

## Nguyên văn (tin nhắn của người dùng trong phiên, 2026-10-09)

```text
Tôi xác nhận các quyết định sau:

**1. Đồng ý tích hợp baseline frontend tạm thời có ngoại lệ.**

Tôi đã xem bộ ảnh C1–C6 nhưng chưa phê duyệt chất lượng giao diện là hoàn chỉnh. Tôi quyết định tạm hoãn phát triển frontend để ưu tiên mở rộng hình học và backend.

Các mục P1–P6 chưa được kiểm tra thực tế tiếp tục giữ PENDING. Các vấn đề UX còn tồn tại giữ OPEN/DEFERRED. W14 chưa có phê duyệt trực quan và W05 giữ kết quả 23/24 ở lượt đo chính.

Tôi chấp nhận các giới hạn và rủi ro còn mở này **cho mục đích tích hợp baseline hiện tại**, không công nhận chúng đã PASS hoặc được khắc phục.

**2. Tôi cho phép fast-forward branch `feat/regular-square-pyramid` vào `main` và push `main` lên remote**, sau khi xác minh lại trạng thái Git và bảo đảm điều kiện tích hợp theo repository.

Ghi nguyên văn quyết định này trong `frontend-freeze/APPROVAL.md`, giữ nguyên lịch sử kiểm thử. Nếu có xung đột, remote thay đổi ngoài dự kiến hoặc điều kiện bắt buộc không thể đáp ứng bằng ngoại lệ đã được xác nhận, hãy dừng và báo cáo.

Chỉ chạy cổng tích hợp thực sự cần thiết, không lặp lại toàn bộ screenshot hoặc T3 nếu bằng chứng hiện có vẫn hợp lệ và quy định không yêu cầu.

**3. Chưa cho phép xóa nhánh.** Giữ nhánh sau khi merge/push, chờ quyết định riêng.

**4. Điều chỉnh định hướng công việc tiếp theo:**

Kiến trúc hình học theo hàm đã được xây dựng trước đó. Không giao Cloud nghiên cứu, thiết kế lại hoặc xây dựng kiến trúc mới từ đầu.

Giai đoạn tiếp theo là **mở rộng các họ hình còn thiếu theo roadmap đã thống nhất**, tận dụng kiến trúc, các hàm và cơ chế hiện có. Không hardcode theo từng đề và không thay đổi pipeline mặc định khi chưa được cho phép.

Sau khi hoàn thành giai đoạn mở rộng hình học, tiếp tục triển khai OCR theo kế hoạch.

Frontend tiếp tục đóng băng, chỉ sửa lỗi nghiêm trọng ảnh hưởng đến chức năng cốt lõi.

Khi tích hợp thành công, báo cáo SHA `main` local/remote, các cổng đã kiểm chứng, trạng thái Git và phạm vi công việc Cloud tiếp theo. Không tự bắt đầu nhiệm vụ Cloud trong lượt LOCAL này.
```

## Phạm vi

| | |
|---|---|
| Được chấp nhận | tích hợp baseline frontend tạm thời có ngoại lệ (mã đã ổn định); KHÔNG công bố frontend hoàn thiện |
| C1–C6 | ĐÃ XEM, **chưa phê duyệt** chất lượng giao diện |
| Giới hạn chấp nhận cho mục đích tích hợp, **vẫn mở** | P1–P6 PENDING (chưa thử thật); UX debt OPEN/DEFERRED (`ISSUE-ARCH-LANDSCAPE-FLOATING-PANEL-COVERS-CANVAS`, `ISSUE-ARCH-ORBIT-LABELS-LEAVE-CANVAS-LOW-SCREEN`, `ISSUE-ARCH-CLASSROOM-BAND-CROWDS-PHONE-TOP-ROW` (giới hạn chip), `ISSUE-ARCH-MOBILE-HEADER-TOOLBAR-LAYOUT`); W14 chưa duyệt bằng mắt (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4` OPEN); W05 23/24 lượt chính |
| Danh tính tại lúc ghi | product `45f5a7f0`; candidate `7f3f042309dd1c54767d60d111c445298e081e726389bbce2048171613c4d1c0` (102 file); `CACHE_VERSION` 118; `LLM_ONLY`; T3 `FULL_PRODUCT_GATE_PASS` tại `ac55186e` (không có thay đổi ngoài `docs/` từ đó) |
| Uỷ quyền tích hợp | fast-forward `main` lên nhánh, push `main` (không force); KHÔNG xoá nhánh; KHÔNG PR |
| Cổng tích hợp | như `cuboid-merge`: candidate, cache, `LLM_ONLY`, tài liệu trên cây tích hợp — không chạy lại T3/bộ đo trình duyệt |
| Việc kế tiếp | `MISSING_FAMILY_EXPANSION_ON_EXISTING_ARCHITECTURE` (ROADMAP §0.2, trên kiến trúc/hàm sẵn có; không kiến trúc mới, không hardcode, không đổi tuyến mặc định), rồi OCR; frontend đóng băng (`handoff.md`) |
| Tham chiếu | `APPROVAL_REFERENCE = frontend-freeze/APPROVAL.md (lời người dùng 2026-10-09)` |
