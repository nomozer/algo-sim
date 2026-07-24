# M17 W2B-PATCH §E — review thị giác CÓ MỤC TIÊU

- Renderer: **database + learner notice** · ảnh **18** · phán quyết chung: **REAL_VISUAL**
- Phạm vi: CHỈ chụp lại phần bản vá động tới (ô trống, pipeline nhiều tầng, ba thông điệp từ chối). 42 ảnh toàn danh mục của RC1 §E KHÔNG chạy lại vì cấu trúc renderer các family khác không đổi.
- Phép đo: Viewport đặt TRƯỚC khi trang dựng, nạp lại trang cho từng viewport — KHÔNG lặp lại artefact phép đo VIS-003 của RC1 §E1.
- Cách đọc số: `engine.result_rows`/`engine.aggregate` trong captures.json là trạng thái engine ĐÃ TÍNH SẴN (engine tất định tính một lần khi init), KHÔNG phải bằng chứng 'đã hiển thị'. Việc hé lộ dần được kiểm bằng MẮT trên ảnh initial/mid/final.

| Fixture | Finding | Trạng thái | Ảnh | Lỗi phát hiện khi review |
|---|---|---|---|---|
| `wp1-L3-avg-empty-markers` | L3 | **REAL_VISUAL** | 6 | — |
| `wp2-L4-five-stage-pipeline` | L4 | **REAL_VISUAL** | 6 | — |
| `wp3-L5-missing-table` | L5 | **REAL_VISUAL** | 2 | — |
| `wp4-L6-two-queries` | L6 | **REAL_VISUAL** | 2 | — |
| `wp5-stage-shortfall` | L4 | **REAL_VISUAL** | 2 | CÓ |

## Quan sát của người review

### wp1-L3-avg-empty-markers — REAL_VISUAL
Hai ô thiếu dữ liệu hiện '— trống —' in nghiêng, PHÂN BIỆT rõ với số 0 (bảng không có ô 0 nào); Inspector và bước cuối cùng ghi 'Trung bình của Điểm kiểm tra = 8.25' — đúng 4 ô có dữ liệu (8+9.5+7+8.5)/4, KHÔNG phải (…)/6. Cả hai viewport giống nhau, không tràn ngang.

*Assertion hỗ trợ (trình duyệt thật):* tràn ngang KHÔNG · phần tử bị cắt 0 · stroke=none (token ma) 0 · viewport desktop, narrow.

### wp2-L4-five-stage-pipeline — REAL_VISUAL
Chỉ báo quy trình hiện ĐỦ 5 bước có đánh số (1. Lọc → 2. Chọn cột → 3. Sắp xếp giảm dần → 4. Lấy 3 dòng → 5. Tính trung bình). Ở bước 1/32 KHÔNG bước nào được đánh dấu và Inspector ghi 'Kết quả hiện dần theo từng bước…' (không lộ đáp án); ở bước 32/32 cả 5 bước có dấu ✓, còn đúng 3 dòng An/Dũng/Lan, hai dòng bị cắt mang nhãn 'Không lấy', kết quả 'Trung bình của Điểm = 8.5'. Cột không chọn bị gạch ngang + mờ. Ở 768px chỉ báo tự xuống dòng, bảng không tràn trang.

*Assertion hỗ trợ (trình duyệt thật):* tràn ngang KHÔNG · phần tử bị cắt 0 · stroke=none (token ma) 0 · viewport desktop, narrow.

### wp3-L5-missing-table — REAL_VISUAL
Tiêu đề 'CHƯA ĐỦ DỮ KIỆN'; nội dung đòi CUNG CẤP BẢNG kèm ví dụ cụ thể; gợi ý 'Bổ sung dữ liệu còn thiếu vào đề rồi gửi lại'. KHÔNG còn câu xui tách truy vấn — đúng bản chất lỗi.

*Assertion hỗ trợ (trình duyệt thật):* tràn ngang KHÔNG · phần tử bị cắt 0 · stroke=none (token ma) 0 · viewport desktop, narrow.

### wp4-L6-two-queries — REAL_VISUAL
Tiêu đề 'TÁCH THÀNH TỪNG YÊU CẦU' + gợi ý 'Mỗi lần hỏi một yêu cầu (giữ nguyên dữ liệu)' — GIỮ NGUYÊN như trước bản vá, đúng cho ca bảng ĐÃ có mà đề hỏi hai truy vấn độc lập.

*Assertion hỗ trợ (trình duyệt thật):* tràn ngang KHÔNG · phần tử bị cắt 0 · stroke=none (token ma) 0 · viewport desktop, narrow.

### wp5-stage-shortfall — REAL_VISUAL
LỖI CHỈ REVIEW ẢNH MỚI THẤY (unit + SSR đều xanh): lần chụp đầu, thông điệp 'chưa dựng được 2 bước' lại đội tiêu đề 'TÁCH THÀNH TỪNG YÊU CẦU' và gợi ý 'Mỗi lần hỏi một yêu cầu' — lời khuyên SAI, vì đề vốn là MỘT truy vấn nhiều bước, tách ra không giúp gì. Nguyên nhân gốc: notice chọn tiêu đề chỉ theo `failure_category`, mà `semantic_incomplete` nay gộp hai ca cần lời khuyên ngược nhau. Đã sửa: thêm mã `PIPELINE_STAGE_INCOMPLETE`, notice đọc `error_code` trước. Ảnh sau khi sửa: tiêu đề 'CHƯA DỰNG ĐỦ CÁC BƯỚC', gợi ý 'Nêu rõ từng bước cần làm rồi gửi lại'.

*Assertion hỗ trợ (trình duyệt thật):* tràn ngang KHÔNG · phần tử bị cắt 0 · stroke=none (token ma) 0 · viewport desktop, narrow.

