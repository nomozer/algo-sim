# M17 W2B-PATCH2 LIVE — Root-cause (P2 FAIL, run dừng đúng)

Kết quả live: **strict 0/1 · P2 KHÔNG ĐẠT · run DỪNG tại P2** (đúng stop condition
§3/§9 — P2 không đạt thì không chạy P1/P3/P4). HTTP 5 (analyze 1 + classify 1 +
simulate 3), http-retry 0, transient 0, reclassify 0, cache-hit 0.
**Không sửa production trong run** (`git diff HEAD -- backend/app` rỗng sau live).
Runtime doctor PASS trước live (`9f717df`, cache 21, family 10, target 20, hash
khớp). Env = **local_python** (KHÔNG claim container execution; parity chỉ từ
runtime doctor). Không ghi đè artifact `0afcb37`/`f2b28e2`.

## Sự thật đo được (không suy diễn)

Analyze THẬT có phát `requested_requirements` đủ **5 operation**
(filter/projection/sort/limit/avg), nhưng **để trống THAM SỐ của 4/5 tầng** —
chỉ `sort` được điền tham số:

| stage | tham số analyze điền | manifest grounded? |
|---|---|---|
| filter | `filter_column/op/value` = **null** | **KHÔNG** |
| projection | `projection_columns` = **null** | **KHÔNG** |
| sort | `sort_column="Điểm"`, `sort_direction="desc"` | CÓ |
| limit | `limit` = **null** | **KHÔNG** |
| aggregate (avg) | `aggregate_column` = **null** (func suy được từ op) | **KHÔNG** |

Merge tất định vì thế chỉ ground được `sort` (mà LLM đã có sẵn) ⇒
`deterministic_merge_count = 0`. LLM simulate sinh spec 3 tầng
(filter+projection+sort, thiếu limit+aggregate) cả 3 lượt ⇒ stage-shortfall
gate từ chối fail-closed (`pipeline_stage_incomplete`).

## Đánh giá — cơ chế đúng, GIẢ ĐỊNH ĐẦU VÀO sai

- **Merge KHÔNG bịa** 4 tầng thiếu tham số — đúng §E fail-closed. Nếu bịa
  (vd đoán `limit=3`, `aggregate_column="Điểm"` từ text) thì vi phạm "unresolved
  field không bị tự đoán".
- **Hai lớp phòng thủ giữ nguyên:** semantic-loss 0, false-positive-sim 0,
  generic-leak 0, result-leakage 0 — hệ TỪ CHỐI thay vì trả spec nửa vời.
- **Nhưng §A KHÔNG đạt:** đề 5 tầng hợp lệ vẫn kết thúc bằng từ chối.

**Nguyên nhân gốc nằm ở TRÊN merge:** PATCH2 giả định `requested_requirements`
mang đủ THAM SỐ từng tầng (offline test tôi ĐIỀN TAY các tham số đó — `filter_
value="A"`, `limit=3`, `aggregate_column="Điểm"`). Live gemini-2.5-flash **không**
điền các tham số đó; simulate cũng bỏ hẳn limit+aggregate. Giá trị "3" (limit) và
cột "Điểm" (aggregate) CÓ trong đề nhưng KHÔNG được tầng nào trích vào spec, và
merge không được phép bịa. Vì vậy merge — dù đúng — **không có dữ liệu grounded
để hoàn thiện**, và P2 vẫn fail.

## Ý nghĩa cho quyết định (KHÔNG tự làm)

Đây là finding thật, cần quyết định của người dùng — **không tự mở PATCH3**:

1. **Sửa hợp đồng analyze**: prompt/schema để analyze điền THAM SỐ từng tầng
   trong `requested_requirements` (filter_value, limit, aggregate_column…). Đây
   là thay đổi prompt/schema ⇒ CACHE bump ⇒ phải re-verify. Là fix ĐÚNG CHỖ
   nhưng là một patch mới.
2. **Hoặc sửa hợp đồng simulate**: buộc simulate điền đủ 5 tầng với tham số (đã
   thử qua manifest hint + stage-shortfall retry — live cho thấy retry mù không
   cứu được; hint chưa đủ mạnh).
3. **Hoặc chấp nhận** giới hạn: pipeline nhiều tầng chỉ chạy khi analyze/simulate
   cung cấp đủ tham số; còn lại từ chối trung thực (hành vi hiện tại).

Offline vẫn xanh tại `9f717df` (pytest 1044) vì test dùng analyze ĐIỀN ĐỦ tham
số — **test-vs-live mismatch đã lộ ra**: fixture manifest cần phản ánh việc live
analyze có thể để trống tham số tầng.

**Wave 2B: NOT CLOSED.** Wave 2C KHÔNG mở. Dừng chờ quyết định.
