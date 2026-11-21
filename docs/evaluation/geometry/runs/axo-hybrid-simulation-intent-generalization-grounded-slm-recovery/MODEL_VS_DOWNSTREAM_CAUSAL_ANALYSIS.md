# Model vs downstream: causal analysis of the /10 SLM 0/20 (P1–P3)

Câu hỏi: ở /10, tuyến SLM phục vụ 0/20 là vì **mô hình** sai, hay vì **hạ tầng sau mô hình** (văn phạm, lowering, Source
Gate) từ chối đầu ra đúng? Câu trả lời dựa trên can thiệp gold 5 nhánh
(`SLM20_GOLD_INTERVENTION_RESULTS.json`) và ablation văn phạm (`SLM_RECOVERY_ABLATION.json`). Không dựa trên suy diễn.

## 1. Phán quyết theo ca (`SLM20_ROOT_CAUSE_AUDIT.json`)

| nhận định | số ca /20 |
|---|---|
| đầu ra mô hình đúng ngữ nghĩa | **17** |
| không biểu đạt được dưới văn phạm cũ (đề không hỏi gì; lối hợp lệ duy nhất là `u:[ambig]`) | 2 (V02, V19) |
| lỗi năng lực mô hình thật | **1** (C25: mệnh đề cụt sau 4 lần viết lại VN06/VN07, mô hình chọn `ambig`) |
| văn phạm **buộc** bịa mục tiêu số cho đề chỉ-mô-phỏng | 8 |

Nguyên nhân gốc chính: `TYPED_FACT_CONTRACT_MISMATCH` 11, `SOURCE_GATE_GRAMMAR_GAP` 7,
`SOURCE_QUOTE_ALIGNMENT_FAILURE` 1, `MODEL_RELATION_EXTRACTION_ERROR` 1.

**Kết luận 1:** con số 0/20 ở /10 chủ yếu không đo năng lực mô hình. Trong 20 ca, 19 ca hỏng ở hợp đồng giữa mô hình và
hạ tầng, chỉ 1 ca hỏng ở chính mô hình.

## 2. Bằng chứng can thiệp

- Nhánh E (diễn đạt chuẩn tắc, tuyến tất định): 24/24 phục vụ, 24/24 hợp lệ theo oracle. Hạ tầng dựng được mọi cảnh.
- Nhánh B (payload SLM đi thẳng vào hạ tầng) cho đúng mã từ chối của nhánh A ở mọi ca có payload. Định tuyến không phải
  nguyên nhân.
- Nhánh D (bỏ mục tiêu bịa): với 7 ca SIMULATE_ONLY, lỗi đầu tiên đổi `SOURCE_OBJECT_MISMATCH` → `SOURCE_PREMISE_UNREAD`.
  Mục tiêu bịa và văn phạm yêu cầu hẹp là **hai** nguyên nhân độc lập chồng nhau.

## 3. Ablation văn phạm (64 ca hợp lệ /10, tập đã lộ — hồi quy, không phải holdout)

| biến thể | slm_ok | phục vụ & hợp lệ | phục vụ sai | chỉ-mô-phỏng hợp lệ | `u` kèm dữ kiện | SLM-thuần phục vụ |
|---|---|---|---|---|---|---|
| U (`u` được phép cạnh dữ kiện) | 35 | 29 | 0 | 3 | 21 | 1/10 |
| **S** (`u` chỉ khi `r:[]`, chọn cho sản phẩm) | **51** | **41** | 0 | **15** | 5 | 1/10 |

Biến thể S giảm đầu ra "bỏ cuộc giữa chừng" (`u` cạnh dữ kiện đúng) từ 21 xuống 5 và nâng số ca phục vụ hợp lệ từ 29
lên 41, không thêm ca phục vụ sai nào.

## 4. Sau sửa: hồi phục đến từ đâu

`evidence/slm20/slm20_audit_after_fix.json`: nhánh A phục vụ **12/20**, cả 12 hợp lệ theo oracle. Nhưng **11/12** đi qua
`LOCAL_DETERMINISTIC_PARSER`, vì parser đã tổng quát hoá và nay đọc chính các đề đó. Chỉ **Q10** đi qua `LOCAL_SLM_GROUNDED`.
Ở ablation, các ca mà parser không có payload (SLM-thuần) được phục vụ 1/10 ở cả U lẫn S.

**Kết luận 2 (trung thực):** sửa hợp đồng làm *đầu ra* của SLM hợp lệ hơn nhiều (slm_ok 35 → 51). Tuy vậy, trên tập /10,
phần lớn ca hồi phục được parser tất định phục vụ trước khi SLM được gọi. Đóng góp riêng của mô hình được đo ở tầng
SLM_REQUIRED của lượt mù /11 (`V11_SLM_STRATUM_RESULTS.json`), không suy ra từ tập đã lộ này.

## 5. Chặn SLM-thuần còn lại (luật đã khoá, không phải mô hình)

"tất cả các cạnh (đều) bằng" (V05, C03) · "biểu diễn <đại lượng>" không phải câu hỏi (Q04, Q05) · tiêu đề đề thi
"Câu 2 (2 điểm)." / "Bài 3." (C26, V16) · đề không dấu bị cổng miền chặn (V18, C24) · C25 (mô hình).

## 6. Fine-tuning

Không làm. Lỗi mô hình là 1/20 và chưa được xác nhận lặp lại. Mọi nguyên nhân khác nằm ở hợp đồng, nên huấn luyện lại
không sửa được chúng (`RULES`: "không fine-tuning nếu chưa có bằng chứng cần thiết").
