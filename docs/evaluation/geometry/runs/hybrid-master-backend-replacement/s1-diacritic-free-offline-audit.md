# Kiểm toán Rủi ro & Prototype Offline `S-1` cho Đề Tiếng Việt Không Dấu (Continuation 11 — §5.1)

> **Trạng thái phê duyệt**: **CHƯA ĐƯỢC OWNER PHÊ DUYỆT CHO PRODUCTION** (`S-1` mở).
> **Cô lập kiến trúc**: Prototype nằm hoàn toàn tại `backend/scripts/s1_diacritic_offline.py` (`0` import trong `backend/app/`, `detect_domain` tại `backend/app/simulation/semantic_program/domain_profile.py` giữ nguyên 100%).
> **Live provider calls**: `0` (`ALLOW_LIVE_AI=0`).

---

## 1. Phân tích Rủi ro Ngữ nghĩa khi Khôi phục Dấu Tự động

Việc tự động thêm dấu tiếng Việt vào đề toán không dấu trước khi đi vào Source Gate tiềm ẩn **3 rủi ro nghiêm trọng** nếu đưa thẳng vào tuyến mặc định:

1. **Rủi ro thay đổi nghĩa toán học do từ đa nghĩa ASCII (Polysemy Collision)**:
   - `goc` → `góc` (angle) vs `gốc` (origin, vd *"khoảng cách từ gốc O"* vs *"góc O"*).
   - `day` → `đáy` (base of solid) vs `dây` (chord of circle/base) vs `dãy` (sequence).
   - `tam` → `tam` (`tam giác` = triangle) vs `tâm` (center `tâm O`) vs `tám` (number `8`, vd *"cạnh bằng tám"*).
   - `canh` → `cạnh` (edge) vs `cánh` (`hình cánh quạt`).
   - `duong` → `đường` (`đường thẳng`, `đường cao`) vs `dương` (`số dương`).
2. **Rủi ro giả mạo trích dẫn gốc (`FORGED_NORMALIZED_QUOTE`)**:
   - Nếu LLM hoặc bộ trích xuất nhận chuỗi đã thêm dấu và trích xuất `quote = "SA vuông góc với (ABCD)"` trong khi đề gốc của người dùng là `"SA vuong goc voi (ABCD)"`, việc dùng chuỗi chuẩn hóa thay cho `raw_source` sẽ làm mất tính xác thực nguyên văn của Source Grounding.
3. **Rủi ro nhập nhằng tên đỉnh viết thường (`s.abcd`, `ab`)**:
   - Trong câu không dấu, từ tiếng Việt thường và ký hiệu hình học viết thường (`a`, `sa`, `ab`, `tam`) có thể va chạm trực tiếp.

---

## 2. Thiết kế Prototype Offline Cô lập (`backend/scripts/s1_diacritic_offline.py`)

1. **Bảo toàn tuyệt đối `raw_source` và ánh xạ span 1-1 (`norm_char_to_raw_span`)**:
   - Mọi ký tự trong `normalized_candidate` lưu chính xác cặp chỉ số `[raw_start, raw_end)` trên `raw_source`.
   - Hàm `extract_raw_quote_from_normalized_span(...)` luôn cắt chuỗi nguyên văn từ `raw_source`.
   - Cổng `verify_no_forged_quotes(raw_source, quotes)` từ chối fail-closed với mã `FORGED_NORMALIZED_QUOTE` nếu bất kỳ quote nào chứa dấu khôi phục không nằm nguyên văn trong `raw_source`.
2. **Khôi phục theo cụm cố định, phát hiện câu trộn có dấu/không dấu (mixed-IME) & từ chối đoán mò khi đa nghĩa (`NEEDS_CLARIFICATION`)**:
   - Phát hiện cả câu hoàn toàn không dấu lẫn câu gõ trộn một phần có dấu / một phần mất dấu (`has_missing_diacritics` dựa trên `_MISSING_DIACRITIC_CUES` dẫn xuất trực tiếp từ bảng khôi phục, loại trừ các từ tiếng Việt không dấu hợp lệ như `trong`, `tam giác`, `cho`, `so`, `do`) và bảo toàn nguyên vẹn các từ đã có dấu sẵn cùng ánh xạ span `raw_source` qua `_ascii_fold`.
   - Chỉ khôi phục các cụm thuật ngữ hình học đóng không nhập nhằng (`hinh chop` → `hình chóp`, `vuong goc` → `vuông góc`, `goc giua` → `góc giữa`, `goc toa do` → `gốc tọa độ`, `mat phang day` → `mặt phẳng đáy`, `tam giac` → `tam giác`, `trong tam` → `trọng tâm`, ...).
   - Mọi token đa nghĩa (`goc`, `day`, `tam`, `canh`, `duong`) nằm ngoài ngữ cảnh đóng hoặc ký hiệu khối viết thường (`s.abcd`) đều sinh `AmbiguousTokenFlag` với danh sách ứng viên tường minh và trả `status = "NEEDS_CLARIFICATION"` (`AMBIGUOUS_DIACRITIC_RESTORATION` / `LOWERCASE_VERTEX_AMBIGUITY`), **không bao giờ tự chọn một quan hệ hình học**.

---

## 3. Kết quả Đo trên Development Corpus Offline (`s1-diacritic-development-corpus.json`)

Kiểm chứng bởi `backend/tests/geometry/test_s1_diacritic_free_offline.py` (`0` live calls):

| Nhóm kiểm thử | Số ca | Kết quả mong đợi | Kết quả thực tế | Quote giả mạo |
| --- | ---: | --- | ---: | ---: |
| Đề không dấu rõ nghĩa (chóp, lăng trụ, lập phương, mặt cầu, góc giữa, thiết diện) | 6 | `RESTORED_UNAMBIGUOUS` | **6/6** | 0 |
| Đề chuẩn có dấu sẵn | 1 | `PASSTHROUGH_HAS_DIACRITICS` | **1/1** | 0 |
| Đa nghĩa `goc` / `day` / `tam` / `canh` / `duong` | 8 | `NEEDS_CLARIFICATION` | **8/8** | 0 |
| Ký hiệu khối viết thường (`s.abcd`) | 1 | `NEEDS_CLARIFICATION` | **1/1** | 0 |
| **Tổng cộng** | **16** | **100% khớp** | **16/16** | **0** |

---

## 4. Điểm Quyết định Owner cho `S-1`

Trước khi cân nhắc tích hợp `S-1` vào bất kỳ tuyến sản phẩm nào, cần Owner quyết định chính sách sản phẩm:
1. Từ chối hoàn toàn đề không dấu kèm thông báo yêu cầu gõ tiếng Việt có dấu; **hoặc**
2. Cho phép tầng tiền xử lý hiển thị bản đề xuất có dấu để người dùng xác nhận (`route-d-clarification/1`) trước khi chạy trích xuất ngữ nghĩa, tuyệt đối không tự động đoán ngầm.
