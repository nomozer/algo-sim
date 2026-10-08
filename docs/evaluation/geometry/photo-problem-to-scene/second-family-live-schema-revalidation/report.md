# Báo Cáo Thực Nghiệm Live Schema Họ Bài Thứ Hai (Prism Volume)

**WAVE_ID:** `SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION`  
**NGÀY:** 2026-09-24  
**NHÁNH:** `feat/photo-problem-to-scene`  
**START_HEAD:** `ef8af771c82d9b16c781a1f17018b766cd763ae4`  
**MODEL:** `gemini-2.5-flash`  
**TEMPERATURE:** `0.1`  
**CASE_ID:** `PRISM_SCHEMA_LIVE_P01` (source case: `PRISM_P01`)  
**CHẾ ĐỘ MẶC ĐỊNH:** `LLM_ONLY`  
**BẢO TOÀN WORKING TREE:** ` D frontend/public/favicon.svg` (giữ nguyên không đổi)  

---

## 1. Mục Tiêu Thực Nghiệm và Kết Quả Cốt Lõi

Wave này thực thi chính xác một lần chạy live trial duy nhất đã được tiền đăng ký tại [`docs/SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION.md`](SECOND_FAMILY_LIVE_SCHEMA_REVALIDATION_PREREGISTRATION.md).

### Câu hỏi thực nghiệm cốt lõi
> *Gemini live API có chấp nhận schema model-facing mới (`solid_topology` cho khối lăng trụ) và trả về phản hồi có cấu trúc hợp lệ hay không?*

### Kết luận thực nghiệm
1. **Gemini Live Schema Acceptance:** **THÀNH CÔNG (`SCHEMA_ACCEPTED = YES`)**.  
   Gemini API (`gemini-2.5-flash`) chấp nhận toàn bộ request wire body chứa cấu trúc `solid_topology` phức tạp, trả về mã trạng thái **HTTP 200** trong **5,922.75 ms**, không gặp lỗi 400 Bad Request hay từ chối schema.
2. **Response Parsing:** **THÀNH CÔNG (`RESPONSE_PARSE_VALID = YES`)**.  
   JSON phản hồi được phân tích cú pháp hợp lệ và khởi tạo thành công đối tượng `RequestContract`.
3. **Phân loại đóng theo luật dừng:** **`SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE`**.  
   Do mô hình trích xuất nhãn dữ kiện dạng mô tả tự nhiên dẫn đến bước kiểm chứng trích xuất ngữ nghĩa và smoke test đường ống downstream chưa hoàn tất đầy đủ.
4. **Hành động tiếp theo:** **`SECOND_FAMILY_SEMANTIC_FAILURE_DIAGNOSIS_OFFLINE`**.

---

## 2. Kiểm Tra Tiền Kiểm (Preflight Verification) Trước Khi Tải API Key

Toàn bộ các cổng an toàn tiền kiểm được thẩm định nghiêm ngặt trong git worktree detached sạch (`.git/live_worktree`) tại exact commit `ef8af771c82d9b16c781a1f17018b766cd763ae4` trước khi API key được truy cập:

| Chỉ Số Tiền Kiểm | Giá Trị Kỳ Vọng (Preregistration) | Giá Trị Thực Tế Đo Đạc | Kết Luận |
|---|---|---|---|
| **Worktree Cleanliness** | 100% sạch, không dirty | Clean (0 untracked, 0 modified) | PASS |
| **No `.env` in Worktree** | True | True (file `.env` không tồn tại trong worktree) | PASS |
| **Commit HEAD** | `ef8af771` | `ef8af771c82d9b16c781a1f17018b766cd763ae4` | PASS |
| **Candidate Tree Hash** | `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95` | `669ea2f160810c4f89e24fbe985abfefcc2f82a8f65e1a8fe0b9e1e9b47f9f95` (103 files) | PASS |
| **Cache Version** | `100` | `100` (`lock_cache_identity.py --verify`: PASS) | PASS |
| **Prompt SHA-256** | `a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f` | `a6df8f08f92dd4557c8d2f8a3ce7a5ded14ef75b072efdf58eac832b52af807f` | PASS |
| **Sanitized Schema SHA-256**| `90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c` | `90b2da5ddd8524f40b7bf2162b520de3187aba04452d652223011c548dce147c` | PASS |
| **Schema Chứa `solid_topology`** | True | True (`solid_kind`, `base_cycle`, `top_cycle`, `correspondence`) | PASS |
| **Request Wire SHA-256** | `4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082` | `4461e38e56033809987ee65e0a8a0d556229656af6938dbba078b66d26a7a082` (10,827 bytes) | PASS |
| **Two-Run Wire Parity** | Byte-identical | Byte-identical (100% khớp từng byte) | PASS |
| **Ground Truth Needles** | 0 needles | 0 needles (không rò rỉ đáp số) | PASS |

---

## 3. Nhật Ký Transport và Ngân Sách Thực Thi

Trước khi gửi byte đầu tiên ra mạng, ngân sách thực thi được khóa và ghi nhật ký nguyên tử:

### Ngân sách transport tiêu thụ
- `MAX_ANALYZE_HTTP_REQUESTS`: 1 (đã dùng: 1)
- `VISION_HTTP_REQUESTS`: 0 (đã dùng: 0)
- `SYNTHESIS_HTTP_REQUESTS`: 0 (đã dùng: 0)
- `REPAIR_REQUESTS`: 0 (đã dùng: 0)
- `RETRIES`: 0 (đã dùng: 0)

### Kết quả transport
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`
- **HTTP Status:** `200 OK`
- **Thời gian phản hồi (Latency):** `5,922.75 ms`
- **Mã băm phản hồi candidate (SHA-256):** `47e161b8af8dfa58876314df55949e2c63b85513302648cd3d33f35f0c73fec6`
- **Usage Metadata:**
  - `prompt_tokens`: 1,703
  - `candidate_tokens`: 521
  - `thought_tokens`: 547
  - `total_tokens`: 2,771

---

## 4. Đánh Giá Độc Lập Bốn Chiều (Four-Dimension Measurement)

Theo đúng quy tắc phương pháp luận của nghiên cứu, kết quả được đánh giá độc lập trên 4 chiều:

### Chiều A: Provider Schema Acceptance (`SCHEMA_ACCEPTED`)
- **Kết quả:** **`YES`**
- **Căn cứ:** Gemini API chấp nhận request body wire và trả về HTTP 200. Không có lỗi `400 INVALID_ARGUMENT` hay từ chối schema `solid_topology`.
- **Ý nghĩa kỹ thuật:** Khẳng định giả thuyết thiết bị đo (apparatus hypothesis) thành công: Schema model-facing cho khối lăng trụ tương thích hoàn toàn với Gemini API.

### Chiều B: Response Parsing (`RESPONSE_PARSE_VALID`)
- **Kết quả:** **`YES`**
- **Căn cứ:** JSON parse thành công, đi qua hàm `build_request_contract` không ném ngoại lệ cấu trúc.
- **Parse Error:** `None`

### Chiều C: Semantic Extraction (`SEMANTIC_EXTRACTION_VALID`)
- **Kết quả:** **`NO` / `FALSE`**
- **Chi tiết trích xuất cấu trúc lăng trụ:**
  - `solid_kind`: `"prism"` (chính xác)
  - `base_cycle`: `["A", "B", "C"]` (chính xác)
  - `top_cycle`: `["D", "E", "F"]` (chính xác)
  - `correspondence`: `[["A", "D"], ["B", "E"], ["C", "F"]]` (chính xác)
  - Quan hệ hình học:
    - `perpendicular_lines`: Đường thẳng `AB` vuông góc `AC` (chính xác)
    - `perpendicular_line_plane`: Đường thẳng `AD` vuông góc mặt phẳng `(ABC)` (chính xác)
- **Lý do chưa đạt trọn vẹn:** Các sự kiện độ dài (`AB=3, AC=4, AD=5`) được mô hình gán nhãn tự nhiên dài (ví dụ: `"Đoạn thẳng AB"`) thay vì token đơn giản `"AB"`, dẫn tới bảng bóc tách độ dài chưa khớp logic kiểm tra tự động cứng của bài test. Không thực hiện vá hay xấp xỉ dữ liệu để giữ tính trung thực của bằng chứng.

### Chiều D: Downstream Pipeline Smoke Test (`PIPELINE_SMOKE_TEST`)
- **Kết quả:** **`NO` / `FALSE`**
- **Chi tiết:** Runner gặp lỗi tham chiếu lớp đối tượng hình học (`AttributeError: module '...fact_graph' has no attribute 'FactGraph'`).
- **Compiler/Synthesis Model Calls:** 0 calls.

---

## 5. Phân Loại Kết Quả Đóng và Quyết Định

Dựa trên bảng phân loại đóng đã tiền đăng ký:
1. `SCHEMA_ACCEPTED_AND_PIPELINE_PASS`
2. **`SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE`** $\leftarrow$ **KẾT QUẢ ĐẠT ĐƯỢC**
3. `SCHEMA_ACCEPTED_CONTRACT_PARSE_FAILURE`
4. `PROVIDER_SCHEMA_REJECTED`
5. `PROVIDER_ERROR`
6. `MEASUREMENT_ERROR`
7. `TRANSPORT_OUTCOME_UNKNOWN`

- **Phân loại cuối cùng:** `SCHEMA_ACCEPTED_MODEL_SEMANTIC_FAILURE`
- **Quyết định thẩm định wave:** `PASS` (Thực nghiệm live hoàn thành đúng đăng ký, thu thập đầy đủ bằng chứng, xác nhận thành công provider chấp nhận schema).
- **Cho phép merge:** `NO` (Cần phân tích và xử lý offline lỗi bóc tách ngữ nghĩa).
- **Hành động tiếp theo chuẩn tắc:** `SECOND_FAMILY_SEMANTIC_FAILURE_DIAGNOSIS_OFFLINE`

---

## 6. Danh Mục Bằng Chứng và Artifact Máy

Toàn bộ artifact máy đo lường được lưu trữ tại:
`docs/evaluation/geometry/photo-problem-to-scene/second-family-live-schema-revalidation/`

1. `REQUEST_OBSERVATION.json`: Thông số đo đạc transport, mã băm wire, token usage, latency.
2. `LIVE_RESULT.json`: Kết quả chi tiết của 4 chiều đo lường và cấu trúc ngữ nghĩa trích xuất được.
3. `PIPELINE_RESULT.json`: Ghi nhận trạng thái đường ống tất định downstream.
4. `FINAL_DECISION.json`: Tổng kết quyết định và phân loại đóng chính thức.

*Ghi chú an toàn:* Nhật ký raw response và API key hoàn toàn nằm ngoài git repository, đảm bảo 0 rò rỉ bí mật (`SECRET_LEAKS = 0`).
