# M17 W2B-LIVE — Failure ledger

STOP condition (§12): **KHÔNG có** điều kiện dừng cứng nào kích hoạt trong run —
0 cell bị sửa, 0 ô-trống-hoá-0, 0 mất/thêm cột, 0 rò rỉ kết quả vào spec, 0 route
sang generic, 0 false-positive simulation, HTTP 18/20, 0 lần cần sửa production
code. Run chạy đủ 6 case.

Case KHÔNG đạt tiêu chí strict: **3/6** (L3, L4, L5).

**Điểm mấu chốt phải nói trước:** *grounding fidelity KHÔNG hề vỡ.* Mọi case
sinh được spec (L1, L2, L4) đều **grounding_perfect = true** — chép đúng từng ô,
đúng kiểu, đúng số dòng/cột, **ô trống giữ nguyên là trống (không hoá 0)**. Ba
lỗi dưới đây nằm ở **operation-completeness**, **robustness ô trống**, và
**độ chính xác lý do từ chối** — KHÔNG phải ở độ trung thực trích bảng.

Tuân thủ §12: KHÔNG sửa fixture/tolerance, KHÔNG sửa production code trong run
này. Mỗi lỗi phân loại theo taxonomy §9 + ghi rõ cần theo dõi ở wave sau.

---

## L4 — spec-generation error (semantic loss: bỏ sót tầng pipeline) · NGHIÊM TRỌNG

**Hiện tượng.** Đề yêu cầu pipeline 5 tầng: *lọc tổ A → chiếu Tên,Điểm → sắp xếp
Điểm giảm dần → **lấy 3 đầu** → **tính trung bình 3 học sinh đó***. Spec live sinh
ra chỉ có `filter + projection + sort`; **thiếu `limit: 3` và `aggregate: avg`**.
Envelope vẫn trả **status=ok** — tức trả lời NỬA VỜI mà báo "xong".

**Bằng chứng.**
- `grounding_perfect = true` (8 dòng, 4 cột, mọi ô/kiểu/ô trống đúng — trích bảng
  hoàn hảo).
- `operations = {filter:true, projection:[Tên,Điểm], sort:(Điểm,desc), limit:None,
  aggregate:None}` so với `expected {..., limit:3, aggregate:(avg,Điểm)}`.
- `actual_final` trả **5 dòng** (chưa limit) không có aggregate; `expected_final`
  là **3 dòng + avg=8.5**.
- `analyze.result_ownership = "algorithmic"`; `simulate_attempts = 1` (chấp nhận
  ngay lần đầu); `reclassification = 0`.

**Root cause.** Completeness gate PHA 2 (`check_represented_coverage`,
`_completeness_phase2`) kiểm **độ phủ CƠ CHẾ theo family** (owned_mechanisms), chứ
KHÔNG kiểm **sự hiện diện từng TẦNG** của một truy vấn bảng. Analyze không ghi
`limit`/`aggregate` thành yêu cầu máy-kiểm được, nên simulate bỏ hai tầng mà không
cổng nào chặn. → **Phân loại §9: spec-generation error.** Đây là lỗ hổng
completeness thật cho *combined pipeline* của `relational_table_query`.

**Theo dõi (wave sau, KHÔNG làm trong run này).** completeness cần soi từng tầng
table-query (limit/aggregate/sort/projection có mặt khi đề yêu cầu) trước khi phát
status=ok — hoặc từ chối `semantic_incomplete` với danh sách tầng bị bỏ.

---

## L3 — robustness ô trống + artefact biểu diễn prompt (KHÔNG phải grounding vỡ)

**Hiện tượng.** Đề AVG với 2 ô trống. Pipeline **RuntimeError sau 3 lần simulate**;
lỗi cuối: `Dòng 2, cột 'Điểm kiểm tra': "trống" không phải số.` → không sinh được
spec.

**Phân tích (quan trọng — hệ hành xử ĐÚNG ở điểm cốt lõi).** Prompt của fixture mã
hoá ô trống bằng **đúng chữ "trống"** trong bảng văn bản. LLM chép nguyên chữ
"trống" vào ô số. Validator `_coerce` **fail-closed TỪ CHỐI** ép `"trống"→số` —
tức **KHÔNG hề biến ô trống thành 0** (đúng bất biến empty≠0, đúng tinh thần chống
bịa số). Cái giá: end-to-end không hoàn tất được AVG-bỏ-ô-trống vì marker rỗng là
một *từ* chứ không phải null.

**Root cause kép:**
1. *Artefact fixture* — biểu diễn "trống" bằng chữ trong prompt (không sửa theo
   §12; nhưng ghi nhận là ambiguous: học sinh thật thường để trống hẳn hoặc "—").
2. *Robustness gap* — đường AVG-với-ô-trống mong manh với cách viết chữ "trống":
   LLM nên map "trống"/"—"/ô rỗng → null; ở đây nó copy literal, và không có lần
   thử nào phục hồi. → **Phân loại §9: normalization error (marker rỗng chưa được
   chuẩn hoá về null trước khi coerce).**

**Không phải lỗi grounding:** empty-to-zero = 0, không bịa số. Hệ thà từ chối còn
hơn tính sai — đúng right-or-refuse.

**Theo dõi (wave sau).** Chuẩn hoá marker rỗng phổ biến ("trống", "—", rỗng, "N/A")
→ null tại biên trích/validator, để AVG-bỏ-ô-trống hoàn tất thay vì exhaust.

---

## L5 — độ chính xác lý do từ chối (từ chối AN TOÀN nhưng sai category)

**Hiện tượng.** Đề "Lọc điểm ≥ 8 và sắp xếp giảm dần" **không kèm bảng**. Hệ **từ
chối an toàn** (route=None, KHÔNG dựng bảng mẫu, KHÔNG executor, KHÔNG generic) —
đạt yêu cầu an toàn cốt lõi. Nhưng category = `semantic_incomplete` ("2 truy vấn
độc lập, tách ra") thay vì `insufficient_specification` (thiếu bảng).

**Root cause.** Combination gate diễn giải "lọc **và** sắp xếp" thành **hai goal
độc lập** (trong khi đây là MỘT pipeline hợp lệ — y như L1/L4 đã qua cổng này bình
thường khi CÓ bảng). Vì không có bảng, đường sufficiency/combination cho ra
`semantic_incomplete` trước khi kịp báo "thiếu bảng". Thông điệp learner ("tách
thành 2 truy vấn") **lạc hướng** so với vấn đề thật (chưa cung cấp bảng). →
**Phân loại §9: refusal-reason accuracy (không phải false-refusal — vẫn từ chối
đúng việc, chỉ sai LÝ DO).**

**Không vi phạm stop-condition:** không bịa bảng, không chạy nửa vời, không generic.

**Theo dõi (wave sau).** Ưu tiên kiểm "thiếu bảng" (insufficient_specification)
TRƯỚC combination check; và xét lại vì sao filter+sort bị coi là 2 goal độc lập khi
vắng bảng.

---

## Kết luận ledger

- **Grounding (mục tiêu 1-4, 6, 9 của wave): ĐẠT** trên mọi spec sinh ra — trích
  đúng schema/hàng/ô, giữ kiểu, **empty≠0 tuyệt đối**, 0 rò rỉ kết quả, executor
  sở hữu toàn bộ đáp án. Đây là điều wave đặt ra để chứng minh, và nó đứng vững.
- **Ba lỗ hổng cần vá trước khi Wave 2B CLOSE:** completeness từng-tầng cho
  combined pipeline (L4 — nghiêm trọng nhất), chuẩn hoá marker rỗng (L3), ưu tiên
  category "thiếu bảng" (L5). Cả ba là **product follow-up**, KHÔNG sửa trong live
  run này.
- **Đề xuất:** Wave 2B **CHƯA CLOSE** (không đạt 6/6). Grounding-verification phần
  cốt lõi PASS; ba finding trên mở một wave vá riêng (có approval).
