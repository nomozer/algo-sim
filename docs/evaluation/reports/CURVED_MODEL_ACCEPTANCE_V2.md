# CURVED_MODEL_ACCEPTANCE_V2 — đo riêng ảnh hưởng của cầu nối

> Chạy **2026-09-03**, cùng bộ ca đã khoá `8c6a184f1c175964…`.
> `HISTORICAL_BENCHMARKS_RERUN = NO` · `CURVED_MODEL_ACCEPTANCE_V1` bất biến.
>
> **Kết luận: DỪNG.** V2 xác nhận cầu nối chạy đúng, và tìm ra **một lỗ cùng
> họ chưa đóng**. Không vá trong lượt đo.

---

## 1. Môi trường — đúng thứ V2 phải đo riêng

| | V1 | V2 |
|---|---|---|
| `case_set_hash` | `8c6a184f1c175964…` | **giống hệt** |
| prompt · thẻ · lược đồ | — | **không đổi một byte** |
| `cache_version` | 66 | **67** |
| `stable_capability_hash` | `8d51b70f…` | **`100c71f0…`** |

Chỉ **một** thứ đổi giữa hai lượt: `CURVED_OBLIGATION_COVERAGE_BRIDGE`.

---

## 2. Con số

```
MODEL_CASES_TOTAL                  9
ONE_SHOT_MODEL_CALLS              18
ONE_SHOT_EXECUTABLE_IR             1      (V1: 0)
ONE_SHOT_CORRECT (đã chấm lại)     3      = 1 ca dương + 2 ca từ chối
ONE_SHOT_HONEST_REFUSALS         2/2      (nhưng xem §6 — chưa chạm ranh giới)
REPAIR_ELIGIBLE_FAILURES           1      (cylinder_2, lỗi schema)
REPAIR_CALLS                       1 ca / 4 lượt
FINAL_CORRECT                      3
FINAL_EXECUTABLE_IR                1

TOTAL_APPLICATION_LLM_CALLS       22      (V1: 26)
TOTAL_INPUT_TOKENS            47.423
TOTAL_OUTPUT_TOKENS           15.428
TOTAL_THOUGHT_TOKENS          54.928
TOTAL_TOKENS                 117.779      (V1: 146.444)
TOKENS_PER_CORRECT_EXECUTABLE_IR  117.779  (1 ca dương chạy trọn)
```

⚠️ **Runner in `ONE_SHOT_CORRECT = 2`. Con số đúng là 3.** Xem §5 — lỗi của
dụng cụ đo, đã chấm lại tất định.

---

## 3. Từng ca, phân lớp đúng cột

| ca | phân lớp | chi tiết |
|---|---|---|
| `ball_1` | **SYSTEM_FAILURE** | `volume(S)` **PHỦ ✔** (cầu nối chạy) · `distance(I)` BÁC — xem §4 |
| `ball_2` | MODEL_GROUNDING_FAILURE | bịa `P_on_sphere` |
| `cylinder_1` | MODEL_GROUNDING_FAILURE | bịa `O_prime` — **vật cản HỆ đã hết** |
| `cylinder_2` | MODEL_SCHEMA_FAILURE | `construct_plane.through = null`; sau sửa vẫn hỏng |
| `cone_1` | **CORRECT_EXECUTABLE_IR** | chạy trọn, `10 · 96π · 60π` — **khớp tuyệt đối** |
| `cone_2` | MODEL_GROUNDING_FAILURE | dữ liệu không truy được về đề |
| `circumsphere` | **SYSTEM_FAILURE** | `distance(OABC)` BÁC — cùng lỗ với `ball_1` |
| `refuse_oblique` | HONEST_REFUSAL | fail-closed ✔ · **chạm ranh giới ✘** |
| `refuse_line_curved` | HONEST_REFUSAL | fail-closed ✔ · **chạm ranh giới ✘** |

### V1 → V2, ba ca bị hệ chặn

```
            SYSTEM_BLOCKED_IN_V1   SYSTEM_BLOCKED_IN_V2   EXECUTABLE_IN_V2
ball_1              YES                  YES (lỗ KHÁC)          NO
cylinder_1          YES                  NO                     NO (lỗi mô hình)
cone_1              YES                  NO                     **YES, ĐÚNG**
```

`V1_V2_DELTA`: vật cản **hệ** biến mất ở 2/3 ca. Ca thứ ba đổi sang một lỗ hệ
**khác**, không phải lỗ cũ.

---

## 4. Lỗ CÙNG HỌ chưa đóng — và nó bác bỏ phán quyết của chính tôi

Tách từng nghĩa vụ, tất định:

```
ball_1        volume(S)      → PHỦ ✔          ← cầu nối chạy đúng
              distance(I)    → BÁC: kiểu 'curved_solid' không hợp
circumsphere  distance(OABC) → BÁC: kiểu 'solid' không hợp
```

Cả hai chương trình dùng `measure radius`. `analyze` thì diễn *"tính bán
kính"* thành một nghĩa vụ **`distance`**, vì taxonomy **không có nghĩa vụ
`radius`** — rồi container của nó rơi vào khối cong.

⚠️ **Điều này bác bỏ phán quyết của wave trước.** `CURVED_OBLIGATION_COVERAGE_
BRIDGE §3` ghi:

> `RADIUS_OBLIGATION_NEEDED  NO  (chưa có phép đo nào chứng minh là cần)`

V2 **chính là phép đo ấy**, và nó nói **CẦN**. Lập luận cũ không sai về logic —
nó sai vì tôi coi "chưa có bằng chứng" là bằng chứng cho chiều ngược lại.

Đây là lỗ **cùng họ** với lỗ vừa đóng: từ vựng nghĩa vụ hẹp hơn từ vựng phép
đo, nên `analyze` phải ép một câu hỏi vào một nghĩa vụ không đúng nó.

---

## 5. Lỗi của DỤNG CỤ ĐO — khai ra, không giấu

Runner đọc đại lượng từ `outcome.envelope["scene3d"]`. Nhưng `route` **cố ý
không dựng cảnh** (hướng phụ thuộc một chiều; `pipeline` mới đổ), nên ô ấy
**luôn rỗng** — và **không ca dương nào có thể ghi điểm**.

V1 không lộ ra vì `ONE_SHOT_EXECUTABLE_IR = 0`. V2 lộ ngay ở ca đầu tiên chạy
được: `cone_1` bị chấm là hỏng trong khi nó **đúng**.

Chấm lại tất định (0 lượt gọi model, cùng đường sản phẩm, cùng chương trình đã
bắt được) — `docs/evaluation/geometry/curved-acceptance-v2/rescored_deterministic.json`:

```
cone_1   executable=True  khớp=True
         do_dai_duong_sinh 10 · the_tich_khoi_non 96π · dien_tich_xung_quanh 60π
```

Đây là **lần đầu tiên** một chương trình hình cong do **mô hình sinh từ đề
tiếng Việt** chạy trọn đường sản phẩm và cho đáp số chính xác.

---

## 6. Hai ca ÂM — fail-closed, nhưng **chưa chứng minh ranh giới**

```
refuse_oblique       fail_closed ✔   chạm_đúng_ranh_giới ✘   (UNANCHORED: bịa 'O')
refuse_line_curved   fail_closed ✔   chạm_đúng_ranh_giới ✘   (UNANCHORED: bịa 'A_on_d')
OBLIQUE_CONIC_REFUSAL   NOT_DEMONSTRATED
LINE_CURVED_REFUSAL     NOT_DEMONSTRATED
```

Cả hai chết ở cổng xuất xứ **trước khi** chạm tới chỗ hệ phải nói *"elip,
không biểu diễn được"* hoặc *"toạ độ vô tỉ"*. Hệ fail-closed đúng — nhưng tính
đó là bằng chứng cho ranh giới cong sẽ là tự khen, và tiêu chí V2 cấm đúng
điều ấy.

⚠️ V1 tính `refuse_line_curved` là **chạm đúng ranh giới** (mô hình thử
`intersect_line_curved_solid`, một `kind` không tồn tại). V2 thì không — cùng
một đề, mô hình đi một đường khác. Đó là **biến thiên của mô hình**, không phải
hệ đổi.

---

## 7. R0

```
CURVED_GEOMETRY_LAUNDERING   0
```

Năm lần mô hình bịa điểm — `P_on_sphere`, `O_prime`, `O`, `A_on_d`, và một ca
`cone_2` — **cả năm** bị `UNANCHORED_DERIVED_ASSUMPTION` chặn, không lần nào
cho sửa. 0 envelope chạy được cho một đề ngoài bao đóng. 0 dựng gần đúng.

---

## 8. Quyết định bật năng lực

```
BALL_MODEL_ACCEPTANCE          0/2 dương   (1 lỗ hệ · 1 lỗi mô hình)
CYLINDER_MODEL_ACCEPTANCE      0/2 dương   (2 lỗi mô hình)
CONE_MODEL_ACCEPTANCE          1/2 dương   (cone_1 ĐÚNG · cone_2 lỗi mô hình)
CIRCUMSPHERE_MODEL_ACCEPTANCE  0/1         (lỗ hệ)

BALL_PRODUCT_ENABLED       NO
CYLINDER_PRODUCT_ENABLED   NO
CONE_PRODUCT_ENABLED       NO
```

`cone` là hình duy nhất có một ca dương ĐẠT, nhưng tiêu chí đòi **các** ca dương
của chính hình ấy qua — `cone_2` hỏng. Không bật.

`product_capability.py` **không đổi một dòng**.

---

## 9. Việc tiếp theo — hai thứ tách bạch

**① Lỗ hệ còn lại** (`ball_1`, `circumsphere`): từ vựng nghĩa vụ thiếu `radius`.
Cùng họ với lỗ vừa đóng, và cùng cách sửa: cho nghĩa vụ dẫn từ hợp đồng phép
đo. Nhưng nó **thêm một nghĩa vụ vào taxonomy**, tức đổi lược đồ `analyze`
(model-facing) và đổi băm taxonomy — một quyết định phạm vi, không phải một bản
vá.

**② Sức tổng hợp của mô hình** — bốn ca hỏng vì mô hình **bịa điểm thay vì
dựng**, ở cả bốn hình. Prompt đã dạy lối đúng (`divide_segment`,
`plane_perpendicular_to_line`); mô hình vẫn khai toạ độ. Đó là
`CURVED_SYNTHESIS_ERGONOMICS`, và §"không thêm primitive/kernel chỉ để cứu
model" áp nguyên.

```
SYSTEM_CLEAN_FOR   volume(curved_solid) · area(circle3) · cone đường đầy đủ
SYSTEM_GAP_LEFT    nghĩa vụ `radius`
MODEL_WEAKNESS     dựng điểm phụ (4/7 ca dương)
```
