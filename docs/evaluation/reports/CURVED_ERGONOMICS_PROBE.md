# CURVED_ERGONOMICS_PROBE — §18, 4 ca phát triển

> Chạy **2026-09-03**, commit `546c5ec`, cây sạch. **16 lượt gọi model.**
> DỮ LIỆU PHÁT TRIỂN, **không phải nghiệm thu**. Bộ ca `8c6a184f…` không đổi.
> `CURVED_ACCEPTANCE_V1`/`V2` bất biến, không chạy lại.

## 0. Kết luận trước, vì nó đổi việc kế tiếp

```
CURVED_SYNTHESIS_ERGONOMICS = PARTIAL
SYSTEM_BUG_FOUND            = CO  →  DỪNG theo luật; KHÔNG vá trong lượt này
NEXT                        = KHÔNG chạy V3 cho tới khi lỗi hệ được đóng
```

Có cải thiện đo được ở đúng hai lớp wave nhắm, nhưng **một lỗi hệ có trước**
làm hỏng chính ca cải thiện rõ nhất, và nó sẽ làm hỏng **3/9 ô dương của V3**.
Chạy V3 bây giờ là đo một hệ đang hỏng.

## 1. Tiền điều kiện

Docker **không chạy**, nên không có tiến trình backend nào giữ prompt cũ; runner
gọi thẳng `run_pipeline` trong tiến trình Python mới, đọc prompt từ đĩa. Điều
kiện này mạnh hơn restart. Xác nhận bằng máy trước khi gọi lượt nào:

```
CACHE_VERSION  70
env hash       a4aa4d6eefa3e9a1   = bản đã khoá sau ecgônômi
  prompts      55ac1ca6a6df92ce   (đổi)
  capability   024799b84cf528db   (không đổi)
load_skill("geometry_program_generator") → 5674 byte, có đủ 3 bất biến mới,
                                            KHÔNG còn câu cũ "Toạ độ bạn chọn khai"
```

Không sửa source/prompt sau khi bắt đầu. Diff `app/` trong lúc đo: **rỗng**.

## 2. Số

```
DEVELOPMENT_CASES        4
ONE_SHOT_CORRECT         0
ONE_SHOT_EXECUTABLE_IR   1        (ball_1)
REPAIR_ELIGIBLE          2        ← bộ đo chạy 2; LUẬT SẢN PHẨM cho 3 (xem §5)
REPAIR_CALLS             2
FINAL_CORRECT            0
FINAL_EXECUTABLE_IR      1

APPLICATION_LLM_CALLS    16       (trần 20)
INPUT_TOKENS             37840
OUTPUT_TOKENS            13708
THOUGHT_TOKENS           24476
TOTAL_TOKENS             76024

SYSTEM_FAILURES          1
CURVED_GEOMETRY_LAUNDERING   0
BALL_PRODUCT_ENABLED  NO   CYLINDER_PRODUCT_ENABLED  NO   CONE_PRODUCT_ENABLED  NO
```

⚠️ `ONE_SHOT_CORRECT = 0` **không** đọc được là *"prompt mới không ăn thua"*.
Một trong bốn ca viết ra chương trình đúng và bị **hệ** chặn. Xem §3.

## 3. Từng ca

| ca | phân lớp | chi tiết |
|---|---|---|
| `ball_1` | **SYSTEM_FAILURE** | chương trình ĐÚNG; engine ra `R = 6`, `V = 288π`; chặn ở `postconditions` |
| `ball_2` | MODEL_SCHEMA_FAILURE | `construct_plane.through = null` → sửa → `intersect_plane_curved` dùng làm CÂU LỆNH |
| `cylinder_2` | MODEL_SCHEMA_FAILURE | `construct_plane.through = null` → sửa → bịa `declare_vector` |
| `circumsphere` | MODEL_GROUNDING_FAILURE | `D_aux = (2,2,2)` bịa ra, không nguồn không giả định |

### `ball_1` — lỗi hệ, chứng minh tất định

```
executable  True      servable  False
stage       postconditions · postcondition_violated · ['cần một `solid`']
engine ra   {'R': '6', 'V': '288π'}        ← ĐÚNG ĐÁP SỐ
```

Hệ tính xong rồi **từ chối phục vụ chính con số nó vừa tính**. Nguyên nhân là
một chỗ lệch giữa hai thẩm quyền, và bảng này là toàn bộ bằng chứng:

| nghĩa vụ | `BANG_PHEP_DO` nhận | bộ kiểm nhận |
|---|---|---|
| `distance` | line3 · plane3 · point3 | `Vec3` `Line3` `Plane3` |
| `radius` | circle3 · **curved_solid** | `CurvedSolid` `Circle3` |
| **`volume`** | **curved_solid** · solid | **`Polyhedron` — CHỈ THẾ** |

Đúng **một** dòng lệch. `CURVED_OBLIGATION_COVERAGE_BRIDGE` nới `volume` sang
`curved_solid` ở **cổng phủ**; `check_volume` vẫn đòi `Polyhedron`.

**Lỗi này là của tôi, hai wave trước.** `RADIUS_VERIFICATION_BRIDGE` đóng đúng
chỗ hụt ấy cho `radius` — rồi tôi không kiểm dòng `volume` mà wave TRƯỚC ĐÓ vừa
nới. Sửa hàng đang nhìn, không soát bảng.

Và nhân chứng tôi khai lúc đó **đọc mạnh hơn nó thật sự là**:

> `V1_BALL_CLEAN_ROUTE  PASS · servable=True · R = 6 · V = 288π`

`test_T6` chỉ truyền nghĩa vụ **`radius`**; `288π` là giá trị đọc từ
`final_memory`, **chưa bao giờ đi qua `check_volume`**. Dòng ấy đọc như một
lượt kiểm đầu-cuối cho thể tích. Nó không phải. Đây là lần thứ hai tôi mắc đúng
hình lỗi này (lần đầu: nhân chứng Phase 2 gọi `kiem_tinh` thay vì
`verify_and_compile`) — nhân chứng phải đi ĐÚNG đường sản phẩm với ĐÚNG bộ
nghĩa vụ, nếu không nó chứng minh một thứ hẹp hơn câu mình viết.

Theo luật §"trong lúc chạy": **DỪNG, không vá rồi tiếp tục**. Không dòng
`app/` nào bị sửa.

## 4. So với V1/V2 — chỉ trên 4 ca này

Lấy quan trắc **gần nhất** của mỗi ca làm mốc.

| lớp | BEFORE | AFTER | ca |
|---|---|---|---|
| `INVENTED_HELPER_POINT` | **2** | **1** | `ball_2` (V2 `P_on_sphere`) · `circumsphere` (V1 `P_diag` → nay `D_aux`) |
| `DECLARED_NOT_CONSTRUCTED` | **1** | **0** | `ball_1` |
| `MISSED_COMPOSITION` | **1** | **1** | `cylinder_2` |
| `GROUNDING_FAILURES` | **2** | **1** | |

### Cái đã ăn

`ball_1` là thay đổi rõ nhất và **kiểm được từ chương trình đã lưu**: V2 khai
`I`, `S` kiểu `curved_solid` rồi không bao giờ dựng. Nay:

```
I  ← source_fact_id=sphere_center       A ← source_fact_id=sphere_point + model_assumption
construct_curved_solid S(ball, anchor=I, rim_point=A)
measure radius → R      measure volume → V
```

Đúng thứ mục 2 của prompt yêu cầu. Ca này **chỉ trượt vì lỗi hệ ở §3**.

`circumsphere` cũng dựng `Circumcenter` bằng `construct_point` thay vì khai toạ
độ — nửa còn lại của hướng dẫn đã ăn.

### Cái chưa ăn, và một hiệu ứng phụ phải nói

`circumsphere` **vẫn bịa** `D_aux = (2,2,2)` (đỉnh đối của khối lập phương —
chính là `P_diag` của V1 đổi tên). Điểm bịa chuyển chỗ chứ không biến mất.

Và mã lỗi đổi từ `UNANCHORED_DERIVED_ASSUMPTION` (**cấm sửa**) sang
`input_not_grounded` (**sửa được**) — **không phải vì hành vi tốt lên**, mà vì
mô hình nay bỏ luôn `model_assumption` thay vì khai một cái. Cùng một nước đi,
sổ sách tệ hơn, lại rơi vào lớp nhẹ hơn. Đọc bảng lớp lỗi mà không mở chương
trình ra sẽ tưởng đây là tiến bộ.

`cylinder_2` vẫn không tìm ra `plane_perpendicular_to_line`. Không đổi.

### Một dự đoán của wave trước được xác nhận

Báo cáo ecgônômi §6 ghi: *"`intersect_plane_curved` chỉ nằm trong `ValueExpr` —
mô hình phải tới qua `assign`, hình dạng câu lệnh khác `construct_*`."* Lượt sửa
của `ball_2` làm **đúng** lỗi đó: dùng `intersect_plane_curved` như một `kind`
câu lệnh. `cylinder_2` bịa `declare_vector`. Hai trong bốn ca hỏng vì **hình
dạng câu lệnh**, không vì hình học. Sửa nó là đổi IR — ngoài phạm vi §2.

## 5. Một sai lệch của BỘ ĐO, phải khai

Hai chỗ, đều ở `scripts/run_curved_acceptance.py` (bộ đo, không phải hệ):

**① Không ca dương nào ghi điểm được.** `dai_luong` đọc từ
`envelope["scene3d"]`, mà `verify_and_compile` **cố ý không dựng scene**
(`pipeline._dung_scene3d` mới dựng). Nên `dai_luong` luôn rỗng. Đây là lỗi đã
lộ ở V2 và **vẫn còn**. Mọi số ở §2 đã chấm lại tất định từ `final_memory`,
**0 lượt gọi thêm**.

**② `circumsphere` đáng được một lượt sửa mà không nhận.** Bộ đo dán
`lop_loi="runtime"` cho **mọi** ca không thực thi, không đọc `error_code`. Mã
thật là `input_not_grounded`, **không** thuộc `KHONG_DUOC_SUA`
(`{UNANCHORED_DERIVED_ASSUMPTION, DERIVED_ENTITY_WITHOUT_PRODUCER}`), nên đường
sản phẩm **có** sửa nó. `REPAIR_ELIGIBLE` đúng luật là **3**, chạy **2**.

Hệ quả: `FINAL_CORRECT = 0` là số **bi quan có kiểm soát** — thiếu một lượt sửa
mà chính sách cho phép. Không chạy bù, vì luật đã yêu cầu DỪNG khi gặp lỗi hệ,
và tiêu thêm quota trong lúc hệ đang hỏng thì con số cũng không dùng được.

Cả hai đều nằm ở bộ đo. Ranh giới đóng băng cố ý cho phép làm cứng `scripts/`;
sẽ sửa ở lượt sau, **cùng lượt đóng lỗi hệ**, rồi mới đo lại.

## 6. Vì sao KHÔNG chạy V3 ngay

Lỗi ở §3 chạm **3 trong 9 ô dương** của pool V3 đã niêm phong — mọi ô hỏi thể
tích khối cong:

```
C1  the_tich_cau     C4  the_tich_tru     C7  the_tich_non
```

Chạy V3 bây giờ là tiêu quota để đo một hệ đang hỏng ở chỗ đã biết, và **đốt
mất tính held-out** của pool: V3 chỉ rút được **một lần**
(`seal_curved_v3.py --rut` từ chối lần hai). Pool giữ nguyên, `36c2153e…`,
chưa có seed.

## 7. Việc kế tiếp, theo thứ tự

1. **Đóng lỗi hệ** — `volume` phải kiểm được `curved_solid`, cùng hình dạng
   `check_radius` đã làm (so trên miền hữu tỉ, hình nào là **dữ liệu**). Kèm
   một guard bắt **mọi** dòng lệch giữa `BANG_PHEP_DO` và `GEOMETRY_CHECKERS`,
   để không phải phát hiện dòng thứ ba bằng một lượt đo nữa.
2. **Sửa hai sai lệch bộ đo** ở §5.
3. Chỉ khi đó mới bàn V3.

Prompt **không sửa thêm** — §20: có cải thiện đo được ở hai lớp nhắm, và tiếp
tục chỉnh prompt cho tới khi 4/4 xanh là tuning lên dữ liệu phát triển.
