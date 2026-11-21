# Simulation clarification UX (P5)

## Lỗi /10

Khi backend trả từ chối toán học **có** câu hỏi làm rõ đã kiểm (`unsupported.clarification.question`, ví dụ
`MISSING_DIMENSION`), trang chủ vẫn hiện thông điệp chung "chưa hỗ trợ". Câu hỏi backend đã soạn bị bỏ đi, nên học sinh
không biết phải bổ sung gì. Bằng chứng là response thật N01 của /10, lưu nguyên văn làm fixture
`frontend/src/components/__fixtures__/live-missing-dimension-refusal.response.json`.

## Sửa (`3e5eb8809`, `ProblemInput.tsx::describeHomeRefusal`)

Nếu có `clarification` với `question` và `kind !== "unsupported"`:

- tiêu đề là "Đề bài cần thêm dữ kiện để dựng hình" (`nlu_class = MISSING_DATA`) hoặc "Đề bài có chỗ cần viết rõ hơn";
- thân là chính câu hỏi (qua `normalizeDisplayBrand`);
- gợi ý: "Bạn có thể bổ sung hoặc viết rõ phần đó ngay trên ô nhập rồi nhấn Dựng hình."

Thiếu câu hỏi, hoặc `kind = unsupported` ⇒ giữ đường cũ. Frontend không tự soạn câu hỏi và không đọc reason_code ra màn
hình (`ui-hygiene.test.ts` vẫn xanh).

## Kiểm

- `frontend/src/components/clarification-refusal.test.ts` dùng response thật làm fixture: câu hỏi hiện trên màn hình,
  không có "chưa hỗ trợ" và không có mã kỹ thuật.
- Trình duyệt thật: I05 trong `V11_UI_SCENARIO_RESULTS.json` (từ chối thiếu kích thước của holdout /11 trên backend live).

## Giới hạn

Nội dung câu hỏi thuộc backend (`learner_messages.py`, khoá). /11 chỉ **chuyển tiếp** câu hỏi lên màn hình, không đổi
nội dung.
