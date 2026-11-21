# Grounded SLM recovery (P3) — kết quả

**Phán quyết: `GROUNDED_SLM_RECOVERY_VERIFIED = FALSE`.** Lượt mù cho thấy Qwen3-AxoV9 tự sinh được cảnh đúng: 4 cảnh có
nguồn gốc SLM, đúng toán, sống, không cache. Nhưng tầng SLM_REQUIRED chỉ đạt **4/30 = 0.133** (Wilson 95% [0.053, 0.297]),
dưới ngưỡng đăng ký trước (≥ 0.30 **và** ≥ 5 cảnh).

## 1. Đã sửa gì (trước lượt mù)

| commit | lớp | nội dung |
|---|---|---|
| `fcf68e91b` | SLM adapter | nhánh GBNF chỉ-mô-phỏng `g:[]`; `u` chỉ khi `r:[]` (`SIM_ONLY_UNRESOLVED_WITHOUT_FACTS`); `construct_object` trích câu yêu cầu; cue góc vuông `vuông (tại\|ở) <đỉnh>`; `local-slm-extractor/5`, `slm-grounding-validator/5` |
| `806a7d338` | Source Gate (hẹp, owner duyệt) | `_VAT_MO_PHONG` đọc danh từ khối có nhãn |
| `0557dcaf6` | parser | văn phạm yêu cầu dùng chung với SLM (`_SIM_REQUEST_RE`) |

Không fine-tuning. Không đổi mô hình (`73f1484b…`). Không nới grounding: validator vẫn kiểm từng trích dẫn trên văn
bản đã chuẩn hoá.

## 2. Bằng chứng tích cực (lượt mù, `V11_SLM_REQUIRED_EVALUATION.json`)

| ca | ý định | cảnh | oracle | đáp số |
|---|---|---|---|---|
| S19 | SIMULATE_ONLY ("Hai mặt phẳng (SAB) và (SAD) cùng vuông góc với đáy … Hãy dựng hình.") | SERVED `LOCAL_SLM_GROUNDED` | MATHEMATICALLY_VALID | — |
| S36 | SIMULATE_ONLY (lăng trụ, "Mô phỏng lăng trụ.") | SERVED `LOCAL_SLM_GROUNDED` | MATHEMATICALLY_VALID | — |
| Q07 | SIMULATE_AND_QUERY ("Dựng hình lăng trụ đứng … rồi tính thể tích.") | SERVED `LOCAL_SLM_GROUNDED` | MATHEMATICALLY_VALID | CORRECT |
| C17 | QUERY_WITH_SCENE (lập phương, trung điểm M) | SERVED `LOCAL_SLM_GROUNDED` | MATHEMATICALLY_VALID | CORRECT |

Luật nguồn gốc (đăng ký trước): một cảnh chỉ được tính cho Model 1 khi `route_d.extraction_mode` bắt đầu bằng `LOCAL_SLM`
và response được tạo sống trong lượt này. Cả 4 cảnh đều thoả. Ở /10, con số này là 0/20.

## 3. Vì sao 26 ca còn lại không được phục vụ (hậu kiểm, `evidence/slm_stratum/v11_slm_stratum_audit.json`)

Chạy lại ngoại tuyến **sau** lượt mù, không đổi kết quả lượt mù.

| lớp hỏng đầu tiên | số ca | ca |
|---|---|---|
| Source Gate từ chối payload SLM đã grounded | 13 | S11 S13 S28 S34 Q04 Q05 Q06 Q08 Q09 Q10 Q12 Q13 Q14 |
| SLM tự báo `u` (chưa rõ/mâu thuẫn) | 8 | S09 S12 S16 S17 S20 S22 S32 Q02 |
| parser từ chối trước khi gọi SLM | 2 | S15 ("3cm" viết liền), S21 |
| cổng miền (đề không dấu) | 3 | S37 S38 C24 |

**Nguyên nhân gốc chung, do thiết kế /11 bỏ sót:** câu yêu cầu **có khai báo lồng bên trong**, ví dụ
"Hãy vẽ giúp em hình chóp tam giác đều S.ABC, cạnh đáy bằng 2a…" hay "Mô phỏng hình chóp S.ABCD có đáy … và tính …".
`_SIM_REQUEST_RE` neo vào **toàn mệnh đề**, nên câu có khai báo không khớp. Hệ quả:

- (a) SLM không được áp nhánh chỉ-mô-phỏng, dù mô hình vẫn sinh đúng dữ kiện. S09, S12, S17, S20 và S32 có `r` đúng nhưng
  vẫn kèm `u`, là điều văn phạm chỉ-mô-phỏng đáng lẽ đã cấm.
- (b) Source Gate không đọc được câu lệnh, nên trả `QUESTION_CONTEXT_UNSUPPORTED` / `SOURCE_OBJECT_MISMATCH`.

Kiểm giả thuyết bằng phép tách máy móc ("Cho <khai báo>. Hãy mô phỏng hình [và tính …].", không dùng gold): **11 ca được
phục vụ, đúng theo oracle**, qua tuyến tất định (S12 S16 S20 S34 Q04 Q08 Q09 Q10 Q12 Q13 Q14).

Lỗi mô hình thật: S22. Mô hình gắn `contra` cho một hình chữ nhật AB = 3, BC = 4 hoàn toàn hợp lệ. Người học vì thế nhận
thông báo "dữ kiện mâu thuẫn" cho một đề đúng. Đây là từ chối an toàn (không phục vụ sai), nhưng là chẩn đoán sai.

## 4. Đóng góp riêng của mô hình

- Ở tập /10 (đã lộ), hồi phục chủ yếu đến từ parser: 11/12 ca được phục vụ đi qua parser (`SLM_RECOVERY_ABLATION.json`).
- Ở lượt mù: 4 cảnh **chỉ** SLM tạo ra được (tầng SLM_REQUIRED theo định nghĩa không có payload parser hoàn chỉnh).
- Không tuyên bố hồi phục Model 1 chỉ vì parser giải được nhiều hơn (DoD §37).

## 5. Fine-tuning hay mô hình lớn hơn?

Chưa. Trong 26 ca hỏng, 21 ca hỏng ở hợp đồng giữa mô hình và hạ tầng (khai báo lồng, văn phạm Source Gate) và 3 ca ở
cổng miền. Chỉ 1–2 ca là lỗi mô hình (S22, có thể thêm C25 từ /10). Huấn luyện lại không sửa được các lớp kia.
Bước kế tiếp đúng thứ tự là nhận diện yêu cầu có khai báo lồng ở cả ba người đọc, đo trên một **holdout mới**.
