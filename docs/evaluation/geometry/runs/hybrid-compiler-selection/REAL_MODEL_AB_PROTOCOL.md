# Giao thức pilot A/B với mô hình thật (P-AB1) — CHƯA CHẠY, CHƯA DUYỆT

Đề xuất của run `hybrid-compiler-selection`. Mọi lượt gọi Gemini cần **quyết định của người dùng** trước. Giả thuyết lấy từ
[`RESEARCH_GAP_UPDATE.md`](RESEARCH_GAP_UPDATE.md) §5 (H-AB1, H-AB2, H-AB3). Luật đo của kho: ngân sách và luật dừng đăng ký
trước; khai `MEASUREMENT_CLASS` · `HELD_OUT_CLAIM` · `EVALUATOR_INDEPENDENCE`; `ALLOW_LIVE_AI=1` chỉ trong tiến trình đo.
Không dùng pilot `LLM_ONLY` cũ (0/10) làm đối chứng.

## 1. Câu hỏi

Cùng mô hình, cùng đề, cùng `k`, cùng nhiệt độ, cùng trần token: mô hình **chọn hàm** (A) hay mô hình **trích dữ kiện** rồi
planner chọn hàm (B) thì phục vụ đúng nhiều hơn, phục vụ sai ít hơn, từ chối đúng nhiều hơn, tốn ít token hơn?

## 2. Thiết kế

- `MEASUREMENT_CLASS = DEVELOPMENT_ARCHITECTURE_AB_PILOT` · `HELD_OUT_CLAIM = NO` (tác giả đã thấy mọi đề khi viết prompt và
  luật) · `EVALUATOR_INDEPENDENCE = PARTIAL` (chấm tất định trên nhãn của cùng tác giả).
- Model `gemini-2.5-flash`, một phiên bản cố định cho cả hai nhánh, ghi lại `modelVersion` của phản hồi. Giá đã tra
  2026-10-10 (theo `ai-function-route/EXPERIMENT_PROTOCOL_V2.md`): 0,30 / 2,50 USD mỗi triệu token vào / ra (ra gồm thinking).
- Bề mặt: A `09ec4a9d…` (`function_calling.surface_fingerprint`), B `83dcfa7a…` (`fact_extraction.surface_fingerprint`).
  Đổi bề mặt sau khi duyệt thì phải duyệt lại.
- `temperature` và `maxOutputTokens = 8192` như nhau (cùng hằng trong mã). Một lượt gọi mỗi đề mỗi mẫu. Không retry nội dung;
  retry mạng tính vào trần.
- **Corpus (48 đề, băm trước khi chạy):** 34 đề của P-FC1 (16 đề G05 + P01–P10 + X01–X08) + 14 đề holdout H01–H14. Chỉ gửi
  **văn bản**; nhãn kỳ vọng nằm ở bộ chấm.
- **Nhánh:** A và B, `k = 3` ⇒ 48 × 3 × 2 = **288 lượt logic**. Thứ tự nhánh trong mỗi (đề, mẫu) xáo theo hạt giống ghi trước,
  để trôi thời gian không dồn về một nhánh.
- **Nhánh B′ (tuỳ chọn, duyệt riêng):** mô hình trích dữ kiện, rồi chính mô hình chọn hàm từ dữ kiện (hai lượt / đề). Mục đích:
  tách "cách nói khai báo" khỏi "planner tất định" (RESEARCH_GAP_UPDATE §5). **Chưa dựng** — cần prompt thứ hai và runner, 0
  lượt, trước khi duyệt. 14 đề holdout × 3 × 2 lượt = 84 lượt.
- Nếu duyệt P-AB1 thì **không** chạy F-ANY của P-FC1 riêng: nhánh A của P-AB1 đã phủ 34 đề ấy với cùng bề mặt.

## 3. Đo gì

Mỗi lượt có đúng một hạng trong sáu hạng đã đăng ký: `correct_served` · `wrong_served` · `correct_refusal` · `false_refusal` ·
`unsupported` · `infrastructure`. Bộ chấm là `scripts/hybrid_ab_offline.py::phan_hang` trên nhãn kỳ vọng đã có.

| chỉ số | định nghĩa | giả thuyết |
|---|---|---|
| tỉ lệ phục vụ đúng | `correct_served` / lượt trên đề dương | H-AB1 |
| **tỉ lệ phục vụ sai** | `wrong_served` / mọi lượt — chỉ số an toàn chính | H-AB1, H-AB2 |
| từ chối đúng / từ chối oan | trên đề âm / trên đề dương | H-AB2 |
| coverage, selective accuracy | theo cách của SatLM (H01) | H-AB2 |
| nhất quán diễn đạt | P01–P10: cùng đáp số trên mọi cách viết, theo mẫu | tổng quát hoá |
| danh mục lỗi | §4 | H-AB1 |
| token vào / ra / thinking | `usageMetadata` của từng lượt | H-AB3 |
| lượt gọi, độ trễ, chi phí | đếm; đồng hồ tường; theo giá §2 | |

Không tính ý nghĩa thống kê. 48 đề × 3 mẫu là pilot. Báo khoảng tin cậy bootstrap **theo đề** cho từng chỉ số.

## 4. Danh mục lỗi (đăng ký trước, gán nhãn tất định bằng diff với tập chuẩn của đề)

| nhóm | lỗi | nhánh |
|---|---|---|
| chọn / ghép | sai hàm cho kiểu quan hệ · tham chiếu chưa định nghĩa · mở rộng định nghĩa sai · sai thứ tự / phụ thuộc | A (B: do planner) |
| trích | bỏ sót dữ kiện · thừa dữ kiện đề không nói · sai `role` · sai `negated` · sai `measure` · cờ `ambiguous` thừa / thiếu | B (A: tương ứng ở lời gọi) |
| neo nguồn | quote không nguyên văn · số không có trong quote | cả hai |
| năng lực | không có luật planner · không có hàm registry | B / cả hai |
| hạ tầng | `RESPONSE_TRUNCATED` · `JSON_INVALID` · `MALFORMED_FUNCTION_CALL` · lỗi provider | cả hai |

H-AB1 bác bỏ khi: (a) nhóm "chọn / ghép" của B không thấp hơn A quá **5 điểm %**; hoặc (b) nhóm "trích" của B không cao hơn A.
H-AB2 bác bỏ khi: `wrong_served` của B không thấp hơn A, **hoặc** từ chối đúng trên đề âm không cao hơn, **hoặc** từ chối oan
trên đề dương của B vượt A quá **10 điểm %**. H-AB3 bác bỏ khi trung vị token ra mỗi đề của B cao hơn A quá **10 %**. Ngưỡng
là đề xuất, chốt khi duyệt, không đổi sau khi thấy dữ liệu.

## 5. Ngân sách và luật dừng

Mỗi lượt xấu nhất: khoảng 9 000 token vào (ước theo payload A; B nhỏ hơn nhưng chưa đo) + 8 192 token ra, tức
(9 000 × 0,30 + 8 192 × 2,50) / 10⁶ ≈ 0,023 USD.

| | lượt logic | lần thử HTTP | token | USD (trần) | xấu nhất ước tính |
|---|---|---|---|---|---|
| A + B | 300 | 450 | 5,2 triệu | 7,00 | 288 × 0,023 ≈ 6,7 |
| B′ (duyệt riêng) | 90 | 135 | 1,6 triệu | 2,10 | 84 × 0,023 ≈ 1,9 |

Dự kiến thấp hơn nhiều: P-FC1 ước 0,004–0,008 USD/lượt ⇒ A + B ≈ 1,2–2,3 USD.

Dừng ngay khi:

- chạm bất kỳ trần nào (kiểm **trước** mỗi lượt);
- thiếu `usageMetadata`;
- hai lỗi provider liên tiếp;
- khoá API xuất hiện trong thư mục ra;
- `RESPONSE_TRUNCATED` vượt 30 % ở 10 lượt đầu của một nhánh (không tự nâng trần);
- bề mặt của một nhánh khác dấu vân tay đã duyệt.

**Không** dừng vì kết quả xấu của một nhánh.

## 6. Việc phải làm trước khi chạy (0 lượt gọi)

1. Runner có ngân sách theo khuôn `run_g05_real_model_pilot.py` (ApiBudget, chặn trước mỗi lượt, quét khoá), gọi
   `run_ai_function_route` và `run_ai_fact_route` với cùng `live_transport`; ghi usage **theo nhãn nhánh**. Hiện
   `live_transport` ghi mọi payload dưới nhãn `"function_calling"` (`PLANNER_MAP.md` §5).
2. Lưu mỗi lượt: băm payload, phản hồi **thô** đã che khoá, `finishReason`, usage vào / ra / thinking, độ trễ, kết cục + mã,
   trace planner (B), hạng.
3. Tách lỗi sản phẩm khỏi lỗi công cụ (F1–F6 của pilot cũ).
4. Chứng nhận runner bằng provider giả trên đủ 48 đề × 2 nhánh. Băm corpus và nhãn; commit **trước** lượt đầu.
5. Restart tiến trình đo (prompt không bị cache trong tiến trình cũ).

## 7. Diễn giải

- Kết quả chỉ nói về `gemini-2.5-flash` trên 48 đề đã thấy. Không tổng quát hoá ra mô hình khác hay đề khác.
- B tốt hơn trên pilot **không** đủ để đổi kiến trúc đích. Cần đề giữ ngoài (do người khác viết), B′ để quy nguyên nhân, và một
  quyết định riêng của người dùng / GVHD.
- B kém hơn cũng không xoá B. Ghi lại theo danh mục lỗi.
