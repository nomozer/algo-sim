# R1 / F5 / nhánh thiếu `kd`

## R1: `explanation` của event dựng mặt cắt (đã sửa, tuyến D)

Trước: "Dựng mặt phẳng (α) qua ba điểm M, H, H1." Câu này đọc như H, H1 định nghĩa (α). Sau (22/22 cảnh):
"Dựng (α): mặt phẳng qua M và song song với (ABC); dựng qua M và các điểm dựng phụ H, H1." Định nghĩa theo đề đứng
trước, phép dựng thật đứng sau. Không xoá bước dựng nào. Ca ⊥ ghi H2, H3: đúng là các điểm mà mặt đi qua, còn H1 ở
đó là chân đường vuông góc nên không thuộc mặt. `learner_text` "Dựng (α)." không đổi. `explanation` chỉ là phương án dự phòng
khi bước không có `learner_text` hợp lệ (`scene3d-model.ts::narrationGoc`). Test: `test_R1_…` (22, nền đỏ 22).

Cùng họ, phát hiện khi review và đã sửa: dấu phẩy trên ASCII trong văn bản người học **có hiển thị**. Cụ thể là nhãn
"Giao điểm của BB' và (α)" (N2) mà C0 làm lộ ra trên inspector, và bước "Xét mặt phẳng (α) để tìm giao điểm với BB'." (P1).
Nay cả hai ghi BB′. Còn lại, có từ trước và không hiển thị: `explanation` dự phòng "Dựng khối ABC.A'B'C'…".

## F5: `envelope.config.frames[].narration` (kiểm chứng, không sửa)

Do `compile_semantic_program_to_envelope` sinh ra, **dùng chung với LLM_ONLY**. Sửa ở đó sẽ đổi envelope mặc định và
contract config đã đóng băng, nên không sửa.

- **Bằng chứng chính (đường mã):** envelope có `scene3d` hợp lệ rẽ ngay sang `Scene3DExplorer`
  (`SimulationWorkspace.tsx:497-525`), trước `NarrationSlot`. Explorer không nhận `config`. Ngoài
  `domains/semantic/`, không mã nào đọc `.frames`/`.narration`.
- **Nhân chứng (trình duyệt):** `check-adapter4-browser.mjs` kiểm ở mọi khung, cả hai viewport, rằng không narration nào
  của frames (trừ câu trùng văn bản bước của chính cảnh, dài > 12) xuất hiện trong `body.innerText`. Có 16–23 narration
  ẩn mỗi cảnh, tất cả vắng mặt. Giới hạn: phép kiểm chỉ thấy panel ở trạng thái mặc định, không đọc
  `title`/`aria-label`, và không bắt narration bị biến đổi (review N1).
- **Negative control:** cài một narration ẩn vào `display_label` của mọi event thiết diện (`PARA-0`), probe xác nhận nó
  lên trang ⇒ harness **FAIL** "envelope frame narration rendered at 13". Ba lần cài trước vào nhãn thiết diện, nhãn khối
  và event bước đại lượng **không lên trang** ở trạng thái mặc định, nên không có giá trị bằng chứng (khai minh bạch).
- Payload API vẫn mang các narration này (ví dụ "Dựng điểm H1 = …", "Dựng khối S.MII1…"), nhưng chỉ trong tuyến
  Hybrid đang tắt. Nếu sau này cần sạch cả payload, phải mở một quyết định về contract config.

## Nhánh thiếu `kd` (đã xử lý)

- **Hợp đồng:** `kd` (bản ghi `derived` của mặt cắt) là **bắt buộc**. Source Gate chỉ nhận lời gọi `pyramid` của khối
  dẫn xuất qua bản ghi đó (`registry.py`, `khoi_dan_xuat`). Thiếu bản ghi ⇒ đường thật từ chối `AUXILIARY_RULE_MISMATCH`
  trước khi dựng cảnh. Test tái hiện bằng cách bỏ `derived` khỏi kế hoạch.
- **Lớp trình bày:** trước kia khối thiếu `kd` rơi vào nhánh "Đoạn của thiết diện". Nay nó ném `_KhoiKhongKhai`, và
  `run_function_route` **bắt riêng** (trước handler rộng) để trả `SCENE_BUILD_FAILED` kèm lý do. Không nhãn, thể tích hay
  tỉ số giả; mã đã có trong taxonomy nên không đổi contract.
- **Test:** từ chối ở Source Gate; ở lớp trình bày, fail-closed và không có nhãn giả; route ánh xạ đúng mã và lý do.
  Có 21 ca hợp lệ mang khối dẫn xuất vẫn được phục vụ. Reviewer probe thêm cảnh hai thiết diện: SERVED, không ném.
