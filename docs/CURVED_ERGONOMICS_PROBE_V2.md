# CURVED_ERGONOMICS_PROBE_V2 — lượt 1: DỪNG SỚM vì lỗi BỘ ĐO, không phải lỗi hệ

> Chạy **2026-09-04**, HEAD `532f0b3`, cây sạch. **6 lượt gọi model thật.**
> DỮ LIỆU PHÁT TRIỂN — không nghiệm thu, không bật năng lực sản phẩm.
> V3 **không** chạy, seed **không** rút, pool giữ nguyên niêm phong.
> Số của probe §18 **không hồi tố**.

## 0. Kết luận trước, vì nó đổi việc kế tiếp

```
run_id                        curved-ergonomics-v2
CASES_RUN                     3 / 4        (circumsphere CHƯA CHẠY)
PASS_B                        CHƯA CHẠY
APPLICATION_LLM_CALLS         6            (3 analyze · 3 synthesis · 0 repair)

SYSTEM_FAILURES               0            ← sau khi sửa bộ phân loại
CURVED_GEOMETRY_LAUNDERING    0
CURVED_SYNTHESIS_ERGONOMICS   VẪN PARTIAL — chưa đủ dữ liệu để phán
```

Lượt đo dừng ở ca thứ ba theo đúng luật *"gặp lỗi HỆ bất ngờ thì DỪNG"*. Nhưng
**đó là báo động giả**: lỗi ấy không phải lỗi hệ, và nguyên nhân nằm trong bộ đo
tôi vừa viết ở wave trước.

## 1. Chuyện đã xảy ra

`ball_1` chạy xong, `postconditions_pass = True`, engine giữ `R = 6` và
`V = 288π` — **đúng đáp số**. Nó chết một cổng SAU đó, ở `learner_surface`:

```
error_code   learner_surface_incomplete
reason       'IA_dist' mang dữ liệu đề (mục 'ia_distance') nhưng không có
             binding — học sinh không thấy đầu vào để theo dõi
chương trình visual_bindings: {containers: [], pointers: [], value_boxes: []}
```

`acceptance_verdict.phan_loai` xếp nó `SYSTEM_VERIFICATION_FAILURE`, luật DỪNG
nổ, lượt đo chết giữa chừng.

### Vì sao phân loại ấy SAI

Tôi đọc **nhãn** `failure_category = verification_gap` thay vì đọc **cổng**.
`learner_surface` hỏi *"biến ĐÁNG THẤY có được khai binding không"* — tức hỏi về
thứ **chương trình** cung cấp. Chương trình này khai `visual_bindings` rỗng. Cổng
phán đúng; **mô hình** mới là bên thiếu.

Xếp nó vào cột HỆ là đúng cái lỗi mà cả tuyến `ACCEPTANCE_RUNNER_INTEGRITY` dựng
ra để chặn, chỉ **theo chiều ngược**: thay vì đổ lỗi hệ cho mô hình, nó đổ lỗi
mô hình cho hệ. Một bộ đo như thế sẽ báo *"hệ hỏng"* mãi trong khi prompt mới là
chỗ cần sửa.

Đã sửa: `LEARNER_SURFACE_INCOMPLETE` → `MODEL_FIRST_BINDING_FAILURE`, cùng họ
với stage `binding` (`VisualBindingUnresolved`) — hai chiều của một hợp đồng thị
giác, cả hai do chương trình khai thiếu. `SEMANTIC_VERIFICATION_UNAVAILABLE`
(không có checker) **giữ nguyên** là lỗi HỆ. Khoá bởi
`test_F3b_learner_surface_thieu_binding_la_loi_MO_HINH` +
`test_F3c_KHONG_checker_thi_van_la_loi_HE`.

⚠️ Theo luật, **không sửa mã rồi chạy tiếp cùng `run_id`**. Artifact lượt 1 giữ
nguyên bản phân loại SAI của nó; bản chấm lại nằm ở đây, không ghi đè.

## 2. Kết quả — chấm lại tất định, 0 lượt gọi thêm

| ca | phân loại lượt 1 | **chấm lại** | servable | postcond | đáp số engine |
|---|---|---|---|---|---|
| `ball_2` | `MODEL_SCHEMA_FAILURE` | `MODEL_SCHEMA_FAILURE` | ✗ | ✗ | — |
| `cylinder_2` | `MODEL_SCHEMA_FAILURE` | `MODEL_SCHEMA_FAILURE` | ✗ | ✗ | — |
| `ball_1` | ~~`SYSTEM_VERIFICATION_FAILURE`~~ | **`MODEL_FIRST_BINDING_FAILURE`** | ✗ | **✓** | `R = 6`, `V = 288π` |
| `circumsphere` | — | **CHƯA CHẠY** | — | — | — |

```
INPUT_TOKENS 12564 · OUTPUT_TOKENS 3887 · THOUGHT_TOKENS 6961
TOTAL_TOKENS 23412 · TELEMETRY_MISSING (không)
```

### Một điều hệ đã tốt lên, đo được bằng lượt sống

`ball_1` ở §18 chết **tại** `postconditions` (`'cần một solid'`). Nay nó **đi
qua** cổng ấy: `VOLUME_VERIFICATION_BRIDGE` chứng thực được `curved_solid`, và
`288π` được kiểm chứ không chỉ được tính. Đây là xác nhận SỐNG cho bản vá đó —
lượt §18 không thể cho xác nhận này vì hệ khi ấy còn hỏng.

Nó **không** phải bằng chứng ecgônômi: cái đổi là bộ kiểm, không phải prompt.

## 3. Hình dạng lỗi — đo bằng máy, và vì sao chưa kết luận được

Bộ dò tất định (`curved_ergonomics_metrics`) chấm **cùng một định nghĩa** cho cả
artifact §18 lẫn lượt này. §18 phân lớp bằng đọc tay, mà đọc tay không lặp lại
được — chấm lại §18 bằng máy cho `INVENTED_HELPER_POINT = 2` trong khi bảng viết
tay ghi **1**: bộ dò đếm cả `O` (gốc toạ độ khai không nguồn, không
`model_assumption`), thứ mắt người bỏ qua.

Trên **3 ca thực sự so được**:

| lớp | §18 (3 ca ấy) | lượt này (3 ca) |
|---|---|---|
| `SCHEMA_MISUSE` | 2 | **2** |
| `INVENTED_HELPER_POINT` | 0 | **0** |
| `DECLARED_NOT_CONSTRUCTED` | 0 | **0** |
| `MISSED_EXISTING_COMPOSITION` | không đo được bằng máy | không đo được bằng máy |

**Không có dịch chuyển nào đo được** trên tập này. `ball_2` và `cylinder_2` hỏng
lược đồ ở cả hai lượt.

⚠️ **Không được đọc bảng này thành *"ecgônômi không ăn thua"*.** Ca duy nhất
từng mang `INVENTED_HELPER_POINT` (`circumsphere`, 2 điểm không nguồn ở §18) là
ca **chưa chạy**. Lớp lỗi mà wave ecgônômi nhắm tới chính là lớp chưa được đo
lại. Kết luận `NO_MEASURABLE_GAIN` bây giờ là kết luận trên một tập thiếu đúng
ca quan trọng nhất.

## 4. Điều bộ đo mới đã làm đúng

Lượt này là lần đầu một probe chạy qua `ACCEPTANCE_RUNNER_INTEGRITY`, và tầng ấy
hoạt động:

- **manifest ghi TRƯỚC lượt gọi đầu tiên**, mang HEAD `532f0b3`, năm vân tay,
  `case_set_hash` khớp §18 (`8c6a184f…`);
- **cổng cây bẩn chặn đúng một lần** — lần chạy khô đầu tiên bị từ chối vì chính
  runner chưa commit, buộc tôi commit trước rồi mới đo;
- **chạy khô (provider bị chặn) bắt hai bug trước khi tiêu đồng quota nào**:
  `CA` chở `set` không JSON hoá được, và HEAD in ra là chuỗi giữ chỗ;
- **kết quả trích từ `final_memory`** — nhờ vậy `ball_1` vẫn khai được
  `R = 6, V = 288π` dù `scene3d` không tồn tại (runner cũ sẽ báo rỗng);
- **token dẫn từ một thẩm quyền chuẩn hoá**, `TELEMETRY_MISSING` rỗng;
- **tóm tắt dẫn từ đĩa và tự kiểm khớp**;
- **luật DỪNG chạy đúng cơ chế** — nó dừng thật, không sửa mã rồi đi tiếp.

Cái sai không nằm ở cơ chế mà ở **một dòng ánh xạ mã lỗi**. Và nó bị bắt trong
đúng một lượt đo, thay vì sống sót qua nhiều wave như bảy sự cố trước.

## 5. Trạng thái

```
CURVED_SYNTHESIS_ERGONOMICS   = PARTIAL (không đổi — chưa đủ dữ liệu)
SYSTEM_FAILURES               = 0
R0                            = còn nguyên (CURVED_GEOMETRY_LAUNDERING = 0)
BALL_PRODUCT_ENABLED          = NO
CYLINDER_PRODUCT_ENABLED      = NO
CONE_PRODUCT_ENABLED          = NO
V3                            = NOT RUN · pool niêm phong · seed chưa rút
PROMPT_CHANGED                = NO   (không chỉnh prompt để ép tập phát triển xanh)
```

Không đủ điều kiện `CLOSED` (thiếu ca, thiếu pass B) và cũng **không** đủ điều
kiện tuyên bố `NO_MEASURABLE_GAIN` (ca mang lớp lỗi mục tiêu chưa chạy).

## 6. Việc kế tiếp

Cần một lượt **`run_id` mới** trên bộ phân loại đã sửa, chạy đủ 4 ca + pass B.
Ước lượng: 8 lượt one-shot + tối đa ~9 lượt sửa ≈ **17 lượt gọi**, trần 24.

Lượt 1 đã tiêu 6 lượt vì một lỗi trong bộ đo của tôi — nên lượt kế tiếp là
**khoản chi thứ hai**, và đó là quyết định của user, không phải của tôi
(`CLAUDE.md §4`).
