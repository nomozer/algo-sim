# CURVED_SECTION_RADIUS_PATH_ADJUDICATION

> 2026-09-05. **`APPLICATION_LLM_CALLS = 0`** · `V3_REEXECUTED = NO` ·
> `V3_ARTIFACTS_CHANGED = NO` · `PRODUCT_CODE_CHANGED = NO` ·
> `PRODUCT_CAPABILITY_CHANGED = NO` · `CACHE_VERSION = 81` (không đổi) ·
> `CANDIDATE_HASH = d105f83e5f7de0cc…` (không đổi, 89 file).
>
> Fixture `c5b` · `c9b` — **`POST_V3_DEVELOPMENT_FIXTURE`**. V3 đã tiêu; đây là
> replay tất định trên dữ liệu đã công bố, **không** phải một lượt acceptance
> mới.

## 0. Phán quyết

**Không có khoảng trống hệ.** Đường `intersect_plane_curved → circle3 →
measure(radius|area)` đã thông **từ lược đồ IR tới khung vẽ 3D** trên đúng
candidate đang đóng băng. Hai ca `c5b`/`c9b` chết trong V3 vì **chương trình mô
hình sinh ra đi nhầm đường**, không vì hệ thiếu đường.

Wave này vì vậy **không thêm một dòng mã sản phẩm nào**. Nó thêm một bộ test
khoá năng lực đang có, và một bản đính chính.

### Đính chính một dự đoán đã công bố

`CURVED_DISTANCE_WITNESS_VERIFICATION.md §12` đặt việc kế tiếp là
`CURVED_SECTION_RADIUS_COVERAGE`, mô tả nó là *"khoảng trống hệ đã khai trong
`contract.py`"*. **Dự đoán ấy sai.** `contract.py` không khai một khoảng trống;
nó khai một **hợp đồng kiểu hẹp có chủ đích** — `intersect_plane_curved` trả
`circle3` và **chỉ** `circle3`, các ca suy biến bị từ chối kèm tên phép dựng
đúng. Đọc lời từ chối ấy như một năng lực còn thiếu là đọc ngược.

Bản đính chính này **đặt cạnh**, không đè lên: §12 của báo cáo kia giữ nguyên
làm dấu vết của điều đã tin lúc đó.

## 1. Ma trận năng lực — tầng · thẩm quyền · ô cho `circle3` · bằng chứng

Mỗi dòng là một tầng phải có ô cho `circle3` thì đường mới thông. Cột **bằng
chứng** trỏ test **đã chạy đỏ được** khi gỡ ô ấy ra (§3), không trỏ một lời
khẳng định.

| # | Tầng | Thẩm quyền (file:dòng) | Ô cho `circle3` | Bằng chứng |
|---|---|---|---|---|
| ① | Lược đồ IR | `contract.IntersectPlaneCurvedExpr` — [contract.py:490](../backend/app/simulation/semantic_program/contract.py#L490) | `solid: GeometryName` · `plane: GeometryName` → `circle3` | schema JSON đã sinh, khớp byte |
| ② | Thẩm định tĩnh | `ir_static_check._CHU_KY` — [ir_static_check.py:139](../backend/app/simulation/semantic_program/ir_static_check.py#L139) | `(("solid",("curved_solid",)),("plane",("plane3",))) → "circle3"` | `test_G_authority…` · tiêm ③ |
| ③ | Bảng phép đo | `measure_contract.BANG_PHEP_DO` — [measure_contract.py:125](../backend/app/simulation/semantic_program/measure_contract.py#L125),[:143](../backend/app/simulation/semantic_program/measure_contract.py#L143) | `area.kieu_of ∋ circle3` · `radius.kieu_of ∋ circle3` | tiêm ①② |
| ④ | Thẩm định tĩnh phép đo | `ir_static_check._KIEU_DO` — **dẫn xuất lúc import** từ ③ | dẫn xuất, không viết tay | tiêm ①② (phải tiêm **cả hai**) |
| ⑤ | Cổng phủ | `coverage_gate` — đọc `memory_declarations` | chấp nhận `circle3` làm container của `radius`/`area` | `test_T4b` |
| ⑥ | Kernel | `curved.intersect_plane_curved` — [curved.py:571](../backend/app/simulation/geometry/curved.py#L571) · `_giao_tron_xoay` [:611](../backend/app/simulation/geometry/curved.py#L611) | `Circle3(center, normal, radius_sq)` trong ℚ | `test_P1`…`test_P5` |
| ⑦ | Bất biến kiểu | `curved.Circle3.__post_init__` — [curved.py:146](../backend/app/simulation/geometry/curved.py#L146) | `radius_sq > 0` — bán kính 0 là một ĐIỂM | tiêm ⑪ |
| ⑧ | Hậu điều kiện | `GEOMETRY_CHECKERS`, dẫn xuất từ ③ | `area` tự nhận `circle3` | `test_P2_P3` |
| ⑨ | Cảnh 3D (BE) | `scene3d.RENDER_HINT` [:56](../backend/app/simulation/semantic_program/scene3d.py#L56) · `_TRUONG` [:99](../backend/app/simulation/semantic_program/scene3d.py#L99) | `"circle3" → "circle"` · `("center","normal","radius_sq")` | `test_P7_P8_P9` · tiêm ⑤⑥ |
| ⑩ | Khung vẽ (FE) | `scene3d-view.tsx` — [:171](../frontend/src/simulations/domains/geometry/scene3d-view.tsx#L171) | `render === "circle"` → `RingGeometry`, `Math.sqrt` **chỉ ở biên hiển thị** | đọc mã; `scene3d.test.tsx` khoá |

Mười ô, không ô nào trống. `radius_sq` đi nguyên si từ kernel tới `scene3d-view`
và phép căn duy nhất nằm ở dòng vẽ — miền chính xác không bị thủng ở tầng nào.

## 2. Replay: chuyện gì thật sự đã xảy ra với `c5b` và `c9b`

Chương trình mô hình sinh, lấy nguyên từ
`docs/evaluation/geometry/curved-acceptance-v3/curved_acceptance.json`:

```
c5b  decl   hinh_tru: solid  · C: section
     #4     construct_section(target=C, solid=hinh_tru, plane=mp_C)
     #5,#6  measure(radius, of=C) · measure(area, of=C)

c9b  decl   hinh_non: curved_solid · C: section
     #2     divide_segment(a=S, b=O, ratio="9/6")
     #4     construct_section(target=C, solid=hinh_non, plane=mat_phang_P)
     #5     measure(radius, of=C)
```

Cả hai chọn `construct_section` — phép dựng thiết diện của khối **đa diện**, trả
`section` (đa giác) — rồi đo `radius` trên nó. `radius` không nhận `section`, nên
cổng phủ bác: `requested_operation_uncovered`.

Hai phép dựng, hai miền, hai kiểu trả về, và ranh giới ấy là **có chủ đích**:

```
construct_section        khối ĐA DIỆN   → section  (đa giác)
intersect_plane_curved   curved_solid   → circle3  (đường tròn)
```

## 3. Ablation vét cạn — delta nào CẦN, delta nào chỉ là trang trí

Áp từng tập con của các delta lên **chính chương trình mô hình đã sinh** (không
dựng lại bằng tay), chạy tất định. Bảng đầy đủ, `SERVED` in đậm:

### `C5B_MINIMAL_DELTA`

| delta áp vào | stage | error_code | đáp số |
|---|---|---|---|
| *(gốc, không sửa)* | `structural_coverage` | `requested_operation_uncovered` | — |
| `khai[hinh_tru: solid→curved_solid]` | `structural_coverage` | `requested_operation_uncovered` | — |
| `khai[C: section→circle3]` | `ir_static` | `semantic_program_invalid` | — |
| `producer[construct_section→intersect_plane_curved]` | `structural_coverage` | `requested_operation_uncovered` | — |
| `khai[hinh_tru]` + `khai[C]` | `ir_static` | `semantic_program_invalid` | — |
| `khai[hinh_tru]` + `producer` | `structural_coverage` | `requested_operation_uncovered` | — |
| **`khai[C]` + `producer`** | **`served`** | — | **`r_C = 9` · `area_C = 81π`** |
| `khai[hinh_tru]` + `khai[C]` + `producer` | `served` | — | `r_C = 9` · `area_C = 81π` |

**Delta tối thiểu = 2**, và `hinh_tru: solid → curved_solid` **không nằm trong
đó**. Bỏ nó vẫn `served`.

Vì sao: `ir_static_check` suy kiểu của vật dựng ra từ **câu lệnh dựng**
(`co[st.target_var] = _KIEU_DUNG[k]`), không từ dòng khai báo — quyết định đã ra
từ sự cố `circumsphere`. Ghi delta ấy vào bảng là quy cho hệ một đòi hỏi mà hệ
không đặt ra. Khoá bởi `test_T4a`.

### `C9B_MINIMAL_DELTA`

| delta áp vào | stage | error_code | đáp số |
|---|---|---|---|
| *(gốc, không sửa)* | `structural_coverage` | `requested_operation_uncovered` | — |
| `khai[C: section→circle3]` | `ir_static` | `semantic_program_invalid` | — |
| `producer[construct_section→intersect_plane_curved]` | `structural_coverage` | `requested_operation_uncovered` | — |
| `ratio[9/6→3/5]` | `structural_coverage` | `requested_operation_uncovered` | — |
| `khai[C]` + `producer` | **`execution`** | `semantic_program_invalid` | — |
| `khai[C]` + `ratio` | `ir_static` | `semantic_program_invalid` | — |
| `producer` + `ratio` | `structural_coverage` | `requested_operation_uncovered` | — |
| **`khai[C]` + `producer` + `ratio`** | **`served`** | — | **`ban_kinh_c = 6`** |

**Delta tối thiểu = 3**, cả ba đều cần: bỏ bất kỳ cái nào cũng bác lại.

### `c9b` có HAI khiếm khuyết độc lập, và cổng phủ che cái thứ hai

Dòng `khai[C]` + `producer` là dòng đáng đọc nhất: nó **không** `served`, nhưng
chết **sâu hơn** — ở `execution`, mã `CURVED_PLANE_DOES_NOT_CUT`, *vị trí `−1/2`
trên trục*. Tức khiếm khuyết thứ hai chỉ lộ ra **sau khi** vá khiếm khuyết thứ
nhất; trước đó cổng phủ bác trước nên nó vô hình.

`DivideSegmentExpr` định nghĩa `ratio` là tham số `t` (**`t=0` là `a`, `t=1` là
`b`**). Với `a=S`, `b=O`, `SO=15` và `SM=9`, giá trị đúng là `t = 9/15 = 3/5`.
Mô hình viết `9/6` — nó đọc dữ kiện thành **tỉ số `SM:MO` = 9:6**, một cách đọc
hợp lý về hình học và sai về hợp đồng IR.

Điều này đổi cách chấm `c9b`: đây **không** phải một ca *"mô hình đúng, hệ
thiếu"*. Nó là **hai** lỗi mô hình chồng lên nhau.

## 4. Đường đã có chạy tới đâu — bằng chứng dương

Dựng bằng chính các primitive đang có, không sửa gì:

```
construct_curved_solid  K  cylinder  anchor=P0 apex_or_top=P1 rim_point=P2
construct_line          TR through P1,P0
construct_point         MM = divide_segment(a=P1, b=P0, ratio=1/2)
assign                  MP = plane_perpendicular_to_line(point=MM, line=TR)
assign                  C  = intersect_plane_curved(solid=K, plane=MP)
assign                  W_R = measure(radius, of=C)
assign                  W_A = measure(area,   of=C)
```

→ `served` · `W_R = 9` · `W_A = 81π` (chính xác, không phải số thập phân).

Nón `r=10, h=15`, cắt cách đỉnh 9 → `W_R = 6` — tỉ lệ đồng dạng `(1−t)²` do
kernel tính, không do ai khai.

Cảnh 3D dựng đủ, phụ thuộc đúng chiều:

```
circle3  | C    | producer= intersect_plane_curved | depends= [K, MP]
quantity | W_R  | producer= measure.radius         | depends= [C]
quantity | W_A  | producer= measure.area           | depends= [C]
```

## 5. Phát hiện phụ — MỘT sự thật, HAI tầng trả lời khác nhau

Ablation làm lộ một bất đối xứng chưa được ghi ở đâu:

| khai báo sai | hậu quả |
|---|---|
| `hinh_tru: solid` (đáng lẽ `curved_solid`) | **vô hại** — `served`, đáp số đúng |
| `C: section` (đáng lẽ `circle3`) | **chí mạng** — `structural_coverage` / `requested_operation_uncovered` |

Nguyên nhân: `ir_static_check` suy kiểu từ **câu lệnh dựng**; `coverage_gate`
đọc **`memory_declarations`** rồi coi đó là toàn bộ chương trình (chính
docstring của `ir_static_check` đã nói ra điều này). Hai tầng trả lời câu hỏi
*"`C` kiểu gì?"* bằng hai nguồn khác nhau, và khi nguồn lệch thì một chương
trình **tính đúng** vẫn bị bác vì một dòng khai báo.

Đây đúng hình dạng lỗi mà cả loạt wave vừa rồi đuổi theo: **một cổng đứng ngoài
đường chạy thật thì không bảo vệ được gì** — ở đây là chiều ngược lại, một cổng
đọc nguồn sự thật thứ hai.

**KHÔNG sửa trong wave này.** Charter nói rõ: chỉ bổ sung mã sản phẩm khi replay
chứng minh khoảng trống **của đường đang xét** còn tồn tại. Nó không tồn tại —
`c5b`/`c9b` chết vì `construct_section`, không vì bất đối xứng này. Hành vi đang
có đã được **khoá** bằng `test_T4b` để nó không trôi trong im lặng, và test ấy
nói rõ nó khoá *hành vi*, không tuyên bố hành vi ấy **đúng**.

## 6. Test đã thêm — `backend/tests/geometry/test_curved_section_radius_path.py`

**32 passed**, 0 lượt gọi model. Ba nhóm:

| nhóm | nội dung |
|---|---|
| **Dương (P0–P10)** | trụ/nón cắt ⊥ trục cho `circle3`; giá trị chính xác `9` · `81π` · `6`; trace + `scene3d` mang đúng `producer`/`depends`; delta tối thiểu của `c5b`/`c9b` đủ để `served`; đường mô hình đã chọn **vẫn** bị bác |
| **Biên (B1–B10)** | ranh giới `section` ↔ `circle3` giữ nguyên; mặt phẳng ngoài khối / tiếp xúc / xiên trả **đúng ba mã đã công bố**; mọi delta đều CẦN; `c9b` có hai khiếm khuyết độc lập; hồi quy `c7a`; tên biến trung tính cho kết quả y hệt |
| **Tiêm lỗi (①–⑪)** | 11 lượt, mỗi lượt gỡ **đúng một** thẩm quyền rồi chứng minh hệ đổi hành vi |

Bộ tiêm lỗi, từng cái một:

| # | gỡ gì | hệ làm gì sau khi gỡ |
|---|---|---|
| ①② | `circle3` khỏi `BANG_PHEP_DO[radius\|area].kieu_of` **và** `_KIEU_DO` | bác |
| ③ | đổi kiểu trả về của `intersect_plane_curved` thành `section` | bác |
| ⑤⑥ | `circle3` khỏi `scene3d.RENDER_HINT` / `_TRUONG` | mất vật khỏi cảnh, hoặc mất `radius_sq` |
| ⑦ | chốt ⊥ trục | **phục vụ một elip** như thể là đường tròn |
| ⑧⑨ | chốt miền cắt (`t∉[0,1]`, qua đỉnh) | **phục vụ một thiết diện không tồn tại** |
| ⑩ | hệ số đồng dạng `(1−t)²` của nón | **xanh, và sai**: `W_R` thành `10` thay vì `6` |
| ⑪ | chốt tiếp xúc **rồi** bất biến `radius_sq > 0` | hai lớp: gỡ lớp ngoài vẫn bị lớp trong đỡ; gỡ nốt thì phục vụ `r = 0` |

Tiêm ①② đáng ghi riêng: sửa `BANG_PHEP_DO` lúc chạy **không đủ**, phải sửa cả
`_KIEU_DO`. Đó là bằng chứng dẫn xuất chỉ chạy **một lần lúc import** — không
phải một lỗi, nhưng là một sự thật cần biết trước khi ai đó tưởng mình đã tiêm.

Tiêm ⑩ là lượt nguy hiểm nhất và là lý do bộ test khoá **giá trị** chứ không
khoá riêng `servable`: không cổng nào bắt được nó, vì kiểu vẫn đúng và chương
trình vẫn chạy — chỉ đáp số sai.

## 7. Năm mức

| mức | `radius`/`area` của thiết diện tròn |
|---|---|
| `EXPRESSIBLE` | **YES** — IR có đủ từ, không cần thêm |
| `DETERMINISTICALLY_CORRECT` | **YES** — `9`, `81π`, `6`, chính xác trong ℚ+radical |
| `MODEL_DISCOVERABLE` | **NOT_MEASURED** — 0 lượt gọi model trong wave này |
| `STABLE` | **NOT_MEASURED** |
| `PRODUCT_SUPPORTED` | **NO** — trụ/nón/cầu vẫn `foundation_only`, nút chưa hiện |

Hai ca V3 `c5b`/`c9b` vì vậy phải đọc là bằng chứng về **`MODEL_DISCOVERABLE`**,
không phải về `DETERMINISTICALLY_CORRECT`. Chúng nói: mô hình **không tìm ra**
`intersect_plane_curved` dù nó có trong văn phạm được gửi.

## 8. Gates

| | |
|---|---|
| `tests/geometry/test_curved_section_radius_path.py` (MỚI) | **32 passed** |
| full backend pytest | **3703 passed** · 1 skipped · 1 deselected, exit 0 (cây sạch) |
| frontend vitest | **698 passed** · 51 file, exit 0 |
| candidate verification | exit **0** — `d105f83e5f7de0cc…`, 89 file, **không đổi** |
| cache identity | passed · `CACHE_VERSION = 81`, **không bump** |
| `replay_demo_cases.py` | **5/5** · reduced-chain 1/1 |
| `audit_demo_crash_surface.py` | biên **6/6** · ném ra ngoài **0** |
| `certify_acceptance_runner.py` | exit **0** · 4 nhãn PASS · 2 readiness YES |
| `git diff --check` | exit **0** |

Không file frontend nào đổi; vitest chạy để chứng minh điều đó, không để đóng
một cổng.

## 9. Giới hạn

**① Không đo được gì về mô hình.** `APPLICATION_LLM_CALLS = 0` theo charter.
Mọi câu trong báo cáo này nói về **hệ**, không nói về khả năng AI tự tìm ra
đường. `c5b`/`c9b` là hai điểm dữ liệu cũ, không phải một phép đo mới.

**② Bao đóng v1 hẹp, và hẹp có chủ đích.** Chỉ mặt phẳng **⊥ trục** cho đường
tròn. Mặt xiên → elip → `CURVED_SECTION_OUTSIDE_V1_CLOSURE`. Thiết diện **qua
trục** là đa giác, dựng bằng `divide_segment` + `construct_polygon`. Không ca
nào là năng lực bị cắt; mỗi ca được chỉ sang một primitive đã có.

**③ Bất đối xứng ở §5 chưa được sửa.** Đã khoá hành vi, chưa phán nó đúng.

**④ `test_T4b` khoá một hành vi có thể sẽ đổi.** Nếu wave sau hợp nhất hai
nguồn kiểu, test ấy phải được sửa **kèm lời giải thích tại chỗ** — nó khoá
trạng thái, không khoá luật, và điều đó được nói ra ngay trong docstring của nó.

**⑤ Ablation chỉ vét cạn trên tập delta tôi liệt.** Nó chứng minh tập ấy tối
thiểu **trong phạm vi các delta được xét**; nó không chứng minh không tồn tại
một cách sửa khác, ít delta hơn, theo một hướng khác.

## 10. Khối kết quả

```
CURVED_SECTION_RADIUS_EXPRESSIBLE            = YES
CURVED_SECTION_RADIUS_DETERMINISTICALLY_CORRECT = YES
CURVED_SECTION_RADIUS_MODEL_DISCOVERABLE     = NOT_MEASURED
SYSTEM_IMPLEMENTATION_GAP                    = NO

BRANCH                                       = A
PRODUCT_CODE_CHANGED                         = NO
SCHEMA_CHANGED                               = NO
PROMPT_CHANGED                               = NO
CACHE_VERSION                                = 81   (không bump)
CANDIDATE_HASH                               = d105f83e5f7de0cc…  (không đổi)

APPLICATION_LLM_CALLS                        = 0
V3_REEXECUTED                                = NO
V3_ARTIFACTS_CHANGED                         = NO
PRODUCT_CAPABILITY_CHANGED                   = NO

C5B_MINIMAL_DELTA                            = 2  (khai[C:circle3] + producer)
C9B_MINIMAL_DELTA                            = 3  (khai[C:circle3] + producer + ratio)
C9B_INDEPENDENT_MODEL_DEFECTS                = 2
C5B_NON_LOAD_BEARING_DELTA                   = khai[hinh_tru:curved_solid]

NEW_TESTS                                    = 32
FAULT_INJECTIONS_DEMONSTRATED_RED            = 11
BACKEND_PYTEST                               = 3703 passed · 1 skipped · 1 deselected
FRONTEND_VITEST                              = 698 passed · 51 file
ALL_GATES                                    = PASS

SECONDARY_FINDING = COVERAGE_GATE_TRUSTS_DECLARATION_WHILE_STATIC_CHECK_DERIVES_TYPE
SECONDARY_FINDING_FIXED                      = NO  (ngoài charter; đã khoá hành vi)
```

## 11. RECOMMENDED_NEXT_ACTION

```
CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE
```

Câu hỏi còn mở **không phải** *"hệ có làm được không"* — §0 đã đóng câu đó bằng
replay. Câu còn mở là: **vì sao mô hình không tìm ra `intersect_plane_curved`**
dù phép ấy nằm trong văn phạm được gửi, và `construct_section` — phép sai — lại
là thứ nó với tới trước.

Hai giả thuyết tách được bằng đo, không bằng suy luận:

- **tên gọi**: `construct_section` đọc như *"dựng thiết diện"*, đúng thứ đề hỏi;
  `intersect_plane_curved` đọc như một phép giao kỹ thuật.
- **thiếu tín hiệu định tuyến**: không chỗ nào trong prompt nói *khối cong thì
  đi lối khác*.

Wave ấy **tiêu quota** và cần một pool niêm phong riêng — V3 đã tiêu, không được
dùng lại.
