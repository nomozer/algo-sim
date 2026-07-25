# M17 W2B-PATCH3 LIVE — Root-cause (P2 FAIL, run dừng đúng)

Kết quả: **strict 0/1 · P2 KHÔNG ĐẠT · run DỪNG tại P2** (Phase A, đúng stop
condition — P2 fail thì không mở Phase B/không chạy P1/P3/P4). HTTP **3** (analyze
1 + classify 1 + simulate 1), http-retry 0, transient 0, reclassify 0, cache-hit
0, deterministic-merge 1. **Không sửa production trong run** (`git diff HEAD --
backend/app` rỗng sau live). Runtime doctor PASS trước live (`0513740`, cache 22,
family 10, target 20, hash khớp). Env = **local_python** (KHÔNG claim container
execution; parity chỉ từ runtime doctor). Không ghi đè artifact
`0afcb37`/`f2b28e2`/`4d9e8ac`.

## 1. PATCH3 ĐẠT ĐÚNG MỤC TIÊU — xác minh LIVE

Defect PATCH2 live (analyze để trống tham số tầng) **ĐÃ HẾT**:

- `valid_analyze_parameters_first_attempt = 1.0` — analyze điền **ĐỦ tham số 5
  tầng NGAY LƯỢT ĐẦU** (filter Tổ=A, projection [Tên,Điểm], sort Điểm desc,
  limit 3, aggregate avg Điểm). Validation decision = **complete**,
  incomplete_before = []. **repair_attempted = 0** (không cần repair — prompt
  analyze.md siết đã đủ).
- manifest **đủ 5 tầng, complete = True**, mọi tầng grounded, unresolved = [].
- raw simulate candidate 3 tầng → **merge chèn limit+aggregate** → merged đủ 5
  tầng; dropped_pipeline_stages = [], mismatched = []; completeness PASS.
- **aggregate value = 8.5, counted = 3 — ĐÚNG.** Dữ liệu 3 dòng An/Dũng/Lan
  (9.0/9.0/7.5) đúng. semantic-loss 0, fp-sim 0, generic-leak 0, result-leak 0.

Tức là toàn bộ chuỗi PATCH3 (parameter grounding → manifest → merge → executor)
hoạt động đúng trên LLM thật, và ca đã từng fail ở PATCH2 (merge=0) nay CHẠY.

## 2. NHƯNG P2 vẫn FAIL — defect MỚI, khác lớp: nhãn cột

Grounding matrix bắt lỗi:

```
added_columns:   ["Tên học sinh", "Điểm số"]
dropped_columns: ["Tên", "Điểm"]
grounding_perfect: False
```

Bảng nguồn P2 có cột **"Tên", "Điểm"** (…, Tổ, Số buổi vắng). Simulate LLM đặt
lại tên cột thành **"Tên học sinh", "Điểm số"** — DIỄN GIẢI LẠI tiêu đề thay vì
chép NGUYÊN VĂN. Giá trị ô đúng (An 9.0, Dũng 9.0, Lan 7.5), chỉ **nhãn cột
lệch** so với đề. `actual_final` rows mang nhãn "Tên học sinh"/"Điểm số" thay vì
"Tên"/"Điểm" ⇒ khác `expected_final` ⇒ FAIL.

**Đây KHÔNG phải lỗi PATCH3.** Schema/nhãn cột do stage SIMULATE sinh (raw
candidate), merge chỉ đụng filter/projection/sort/limit/aggregate — không đụng
schema. Lỗi bị CHE ở mọi run trước vì P2 chưa bao giờ đi tới đây (PATCH2 merge=0
dừng sớm; trước đó thiếu tham số). PATCH3 vá xong lớp tham số → lộ lớp kế tiếp:
**tính trung thực của nhãn cột (grounding/authenticity ở simulate).**

## 3. Đánh giá — hai lớp phòng thủ giữ, oracle không nới

- Spec nội bộ NHẤT QUÁN và CHẠY đúng số (AVG 8.5/3); không rò rỉ kết quả; không
  generic; không semantic loss. Hệ KHÔNG trả sai đáp số — chỉ nhãn cột lệch.
- Oracle P2 KHÓA nhãn cột đúng đề ("Tên"/"Điểm"); grounding matrix bắt đúng
  "schema mất/thêm cột". **KHÔNG nới oracle/tolerance sau khi thấy output**
  (đúng luật): relabel cột LÀ đổi dữ liệu trình bày của đề → đúng phải fail.
- Stop-check §I bắt đúng: supported case grounding không hoàn hảo → dừng ngay ở
  Phase A, không mở Phase B.

## 4. Ý nghĩa cho quyết định (KHÔNG tự làm — §8)

Không tự mở PATCH4, không thu hẹp capability. Chờ quyết định. Các hướng để cân
nhắc (đều là patch/bước MỚI, cần duyệt riêng):

1. **Siết grounding nhãn cột ở simulate**: hợp đồng/prompt buộc `schema[].name`/
   `label` CHÉP NGUYÊN VĂN tiêu đề đề cho; hoặc validator đối chiếu nhãn cột spec
   với tiêu đề nguồn (như đã làm cho rows/cells). Đây là vấn đề authenticity
   tổng quát (không riêng bảng), cần thiết kế cẩn thận để không chặn oan
   normalization hợp lệ (trim/hoa-thường).
2. **Chấp nhận** relabel nhãn cột là biến thể trình bày hợp lệ (nới oracle) —
   NHƯNG mâu thuẫn R0/authenticity ("chép đúng dữ liệu đề cho"), nên cần duyệt
   product rõ ràng, KHÔNG tự làm.
3. **Giữ nguyên**: coi đây là giới hạn đã biết của simulate grounding, ghi
   backlog; capability không thu hẹp.

Offline vẫn xanh tại `0513740` (pytest 1071) — test dùng schema nhãn đúng nên
không lộ; **test-vs-live mismatch mới**: cần fixture simulate relabel cột để bắt
lớp này offline nếu quyết định siết.

**Wave 2B: NOT CLOSED.** Wave 2C KHÔNG mở. Dừng chờ quyết định.
