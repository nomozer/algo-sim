# Câu hỏi thí nghiệm và giao thức (CHƯA chạy — đăng ký trước cho bước kế)

Run này **0 lượt gọi model**. Mọi lượt dưới đây cần quyết định của người dùng, ngân sách và luật dừng đăng ký trước
(`AGENTS.md §4`), khai `MEASUREMENT_CLASS` · `HELD_OUT_CLAIM` · `EVALUATOR_INDEPENDENCE` · trần lượt gọi. Giả thuyết
nguồn: `LITERATURE_GAP_MATRIX.md §5`; thêm bài học từ pilot G05 (`feat/real-model-pilot-tooling`, `471a2c79`).

## Q0 — tiền đề, 0 lượt gọi (đã làm ở run này)

Engine có dựng đúng khi đầu vào lời gọi đúng không, và từ chối đúng khi không dựng được? Kết quả: 27/27 fixture khớp kết
cục đăng ký trước (`offline/results.json`). Đây là **foundation_only**: chứng minh engine, không nói gì về mô hình.

## Q1 (H1) — chọn hàm theo mệnh đề vs viết cả chương trình

- **Tuyên bố:** cùng `gemini-2.5-flash`, cùng 16 đề pilot G05 (`PILOT_CASES.json`, băm `fda51779…`), tỉ lệ dương phục vụ
  đúng của đường function calls > của `LLM_ONLY`; lỗi tham chiếu/lược đồ không chuyển sang một họ lỗi khác cùng tần suất.
- **Bác bỏ khi:** tỉ lệ phục vụ đúng không cao hơn, hoặc phân bố lỗi chỉ dịch chuyển.
- **Thiết kế:** cùng đề, cùng model, `k = 3`, hai tuyến; `LLM_ONLY` lấy lượt mới (không dùng lại k=1 của pilot làm nhóm
  đối chứng duy nhất). Phân loại theo hạng của pilot (10 hạng) + mã từ chối của đường mới.
- **Cần làm trước:** nối Gemini function calling (`function_declarations()` → `tools`, chế độ ANY, danh sách hàm cho
  phép), sửa P1 cho nhóm `LLM_ONLY` hoặc khai rõ nó là nhiễu, sửa F1–F6 của bộ đo pilot.

## Q2 (H2) — neo nguồn bắt buộc

- **Tuyên bố:** kiểm `quote` tất định giảm tham số bịa mà không giảm độ phủ quá ngưỡng đăng ký trước (đề xuất: ≤ 1/10 dương
  bị từ chối chỉ vì quote).
- **Đo:** trên chính các lượt Q1, chạy engine hai lần OFFLINE trên cùng đầu ra mô hình — có/không `kiem_nguon` — 0 lượt gọi
  thêm. Đếm: lời gọi có số không nằm trong quote; dương bị từ chối bởi mã nguồn; phục vụ sai khi tắt cổng.

## Q3 (H3) — token theo loại IR

- **Tuyên bố:** token **ra + thinking** mỗi đề của function calls < `LLM_ONLY` ở độ chính xác ≥.
- **Đo:** `usageMetadata` của Q1, tách vào / ra / thinking. Pilot G05 cho mốc: thinking = 107 170/224 023 token, 74 % chi
  phí; đề dương LLM_ONLY tốn 16–45 nghìn token (`runs/g05-real-model-pilot/report.md` trên nhánh pilot).
- **Rủi ro cần đo, không suy:** ép định dạng chặt có thể làm giảm suy luận (W26 trong ma trận văn liệu).

## Q4 — tổ hợp (compositionality), 0 lượt gọi được

- Tách tập đề theo "tổ hợp có trong fixture" vs "tổ hợp mới" (vd chân tại trung điểm cạnh với đáy tam giác đều; hai khối
  chung đáy với điểm dựng từ điểm dựng). Engine không có mã theo họ ⇒ dự đoán: tỉ lệ dựng đúng không phụ thuộc tổ hợp có
  trong fixture hay không. Bác bỏ khi tổ hợp mới cần sửa engine.

## Ngân sách mẫu (điền khi được duyệt)

`MEASUREMENT_CLASS = DEVELOPMENT_FUNCTION_CALLS_VS_LLM_ONLY` · `HELD_OUT_CLAIM = NO` (corpus đã nhìn) ·
`EVALUATOR_INDEPENDENCE = PARTIAL` · 16 đề × 2 tuyến × k=3 = 96 lượt đề; trần đề xuất 400 lượt logic / 600 HTTP /
2,5 triệu token, **đặt `maxOutputTokens`** cho đường mới để trần token là trần cứng (bài học R1/F4 của pilot) — đổi tham
số gọi provider là đổi bề mặt mô hình ⇒ phải khai và đo lại.
