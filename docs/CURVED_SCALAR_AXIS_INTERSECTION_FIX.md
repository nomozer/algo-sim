# CURVED_SCALAR_AXIS_INTERSECTION_FIX

> 2026-09-05. **`APPLICATION_LLM_CALLS = 0`** · `V3_REEXECUTED = NO` ·
> `PRODUCT_CAPABILITY_CHANGED = NO` · `CACHE_VERSION = 81` (không bump).
>
> Đóng lỗi hệ mà `CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE §3b` tìm ra trong
> gold preflight và đăng ký trước lượt đo.

## 1. Điểm xuất phát, đo lại từ kho

```
HEAD                = 8e6fd58 · WORKING_TREE = CLEAN
CACHE_VERSION       = 81
CANDIDATE_HASH      = d105f83e5f7de0cc…  (89 file, verify exit 0)
BACKEND_BASELINE    = 3738 passed · 1 skipped · 1 deselected
FRONTEND_BASELINE   = 698 passed / 51 file
```

Policy chứa `CURVED_SCALAR_DECLARED_SOLID_CANNOT_BE_CUT`:
[`measurement_policy.json`](evaluation/geometry/curved-section-discoverability-dev-v1/measurement_policy.json).

## 2. `ROOT_CAUSE` — tái hiện trước, kết luận sau

`CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` mở đường khai trụ/nón bằng **hai vô
hướng** cho lớp đề *"hình trụ bán kính 7, chiều cao 10"* — đề không đặt tên điểm
nào nên không `apex_or_top` nào dựng được. Wave ấy thêm `huong_truc`, kèm
docstring nói đúng mục đích:

> *"hướng là thứ duy nhất mà mặt phẳng đáy và trục cần"*

**`_giao_tron_xoay` không bao giờ chuyển sang dùng nó.** Nó vẫn đọc `truc` —
vectơ **mang độ dài** — và `truc` trả `Vec3(0,0,0)` khi `apex_or_top is None`.

Hai chỗ hỏng, không phải một:

| dòng cũ | hỏng thế nào |
|---|---|
| `d = s.truc; if not d.cross(pl.normal).is_zero()` | `cross` của vectơ **không** với bất kỳ vectơ nào **luôn** bằng không ⇒ chốt ⊥ trục **im lặng nhận mọi mặt phẳng**, kể cả xiên |
| `_cat_truc`: `(p−anchor)·d / d.dot(d)` | `d·d = 0` ⇒ **chia cho 0** |

Ví dụ số. Trụ `r = 12`, `h = 20`, khai vô hướng, cắt bởi `z = 5`:

```
truc       = (0, 0, 0)          ← nguyên nhân
huong_truc = (0, 0, 1)          ← thứ đáng lẽ phải đọc
d·d        = 0
t          = (p − anchor)·d / 0 → ZeroDivisionError: Fraction(1, 0)
```

Đây lại đúng hình dạng lỗi cả loạt wave vừa rồi đuổi theo: **một sửa chữa không
nằm trên đường chạy thật.** Thuộc tính được thêm, consumer duy nhất cần nó không
bao giờ chuyển sang.

### `REPRODUCED_BEFORE_FIX`

Bộ test viết **trước** bản vá:
[`test_curved_scalar_axis_intersection.py`](../backend/tests/geometry/test_curved_scalar_axis_intersection.py)
— **34 đỏ / 7 xanh** trên mã chưa sửa.

Các tổ hợp đã tái hiện:

| họ | radius | height | anchor/pose | mặt phẳng | schema/static/grounding | stage | error_code | exception |
|---|---|---|---|---|---|---|---|---|
| cylinder | vô hướng | vô hướng | canonical | `z = h/3` ⊥ trục | — (gọi kernel thẳng) | — | — | `ZeroDivisionError` |
| cone | vô hướng | vô hướng | canonical | `z = h/3` ⊥ trục | — | — | — | `ZeroDivisionError` |
| cylinder | vô hướng | vô hướng | canonical | **xiên** | — | — | — | `ZeroDivisionError` (đáng lẽ `NGOÀI_BAO_ĐÓNG`) |
| cylinder | vô hướng | vô hướng | canonical | `z` ngoài khối | — | — | — | `ZeroDivisionError` (đáng lẽ `KHÔNG_CẮT`) |
| cylinder | vô hướng | vô hướng | `anchor` **có tên** | ⊥ trục, trong khối | **đều PASS** | `execution` | `semantic_program_invalid` / `capability_gap` | `['[ZeroDivisionError]', 'Fraction(1, 0)']` |

Dòng cuối là ca đi qua **đường sản phẩm thật**: chương trình grounded, hợp lệ
lược đồ, hợp lệ tĩnh — rồi vỡ ở kernel. Ba hệ quả: phân loại **sai** thành
`capability_gap` (năng lực **có**), tên ngoại lệ Python **rò lên `details`**
(bề mặt học sinh), và thông điệp gửi vào vòng sửa là vô nghĩa.

Fixture đối chứng dùng `apex_or_top` biểu diễn **cùng khối, cùng vị trí, cùng
mặt phẳng** — luôn đúng, cả trước lẫn sau.

## 3. Bản vá — dẫn từ công thức

### Ý nghĩa từng đại lượng

| ký hiệu | là gì | hữu tỉ? |
|---|---|---|
| `u = huong_truc` | **hướng** trục | luôn |
| `truc` | vectơ đáy→đỉnh, **mang độ dài** `h` | chỉ khi khai bằng điểm |
| `h² = height_sq` | chiều cao² | luôn |
| `h` | chiều cao | không phải lúc nào cũng |
| `L = (p−anchor)·u / (u·u)` | vị trí giao điểm **theo đơn vị `|u|`** | luôn |
| `t` | **tỉ lệ** dọc trục, `0` ở đáy `1` ở đỉnh | xem dưới |

### `AXIS_AUTHORITY` — và vì sao đổi `truc → huong_truc` là **chưa đủ**

`huong_truc` **không chuẩn hoá**, có chủ đích: khai bằng điểm thì nó *là* `truc`,
mang đúng `h`. Nên cùng một biểu thức cho hai đại lượng khác nhau:

```
khai bằng ĐIỂM      |u| = h   ⇒  L đã LÀ tỉ lệ t (0…1)
khai bằng VÔ HƯỚNG  |u| = 1   ⇒  L là KHOẢNG CÁCH tuyệt đối từ đáy (0…h)
```

Đổi `truc → huong_truc` mà quên thang đo thì **trụ vẫn đúng** — bán kính nó
không phụ thuộc vị trí — còn **nón sai im lặng**. Đó là lý do bản vá tách riêng
`_ti_le_doc_truc`, và là lý do có hai phép tiêm (②, ④) chỉ để bắt đúng chỗ ấy.

### `HEIGHT_SCALE_PRESERVED` — ba thay đổi

**① Chốt ⊥ trục đọc HƯỚNG.**

```python
u = s.huong_truc
if not u.cross(pl.normal).is_zero():  raise ERR_NGOAI_BAO_DONG
```

**② Tâm đường tròn LÀ giao điểm trục × mặt phẳng** — bỏ hẳn `anchor + truc·t`.

```python
tam = intersect_line_plane(s.axis, pl)
```

`s.axis` vốn **đã** dùng `huong_truc`, nên giao điểm hữu tỉ ở **cả hai** cách
khai. Phép cũ cần một vectơ mang độ dài, thứ cách khai vô hướng không có.

**③ Kiểm biên bằng BÌNH PHƯƠNG, nên không cần `√h`.**

```python
L  = (tam − s.anchor)·u / (u·u)
d2 = L² · (u·u)                       # khoảng cách² từ đáy
if L < 0 or d2 > s.height_sq:  raise ERR_KHONG_CAT
```

Tương đương đại số với luật cũ ở nhánh khai bằng điểm: ở đó `u·u = h²`, nên
`L²h² > h² ⟺ L² > 1 ⟺ L > 1` (với `L ≥ 0`) — **đúng bằng** `t < 0 or t > 1`.
Nhánh khai bằng điểm vì vậy **không đổi một bit nào**.

**④ Đổi thang chỉ ở nhánh cần nó** (`_ti_le_doc_truc`):

```python
if s.apex_or_top is not None:  return L      # |u| ≡ h ⇒ L đã là t
if L == 0:                     return 0      # đáy: t = 0 bất kể h
h = sqrt_rational(s.height_sq)
if not isinstance(h, Fraction): raise ERR_NGOAI_BAO_DONG   # h vô tỉ
return L / h
```

Với nón, `t` đo **từ đáy** (`t = 0` ở đáy, `1` ở đỉnh) và hệ số bán kính là
`(1 − t)`, hệ số bình phương là `(1 − t)²` — giữ nguyên quy ước cũ. Phép tiêm ④
đảo gốc đo tại một lát cắt **bất đối xứng** (`z = 3` trên `h = 15`: đúng `r' = 8`,
đảo cho `r' = 2`) nên quy ước này có lưới thật.

### Miền số — biên được nói ra, không bị giấu

`r'² = r²(h−L)²/h²` chứa `h`. Khi `h` vô tỉ thì `r'²` rơi ra ngoài ℚ, tức ngoài
kiểu `Circle3.radius_sq: Fraction`.

| | trụ | nón |
|---|---|---|
| `h` hữu tỉ | ✓ | ✓ |
| `h` vô tỉ (vd `h² = 7`) | ✓ — `r' = r`, không cần hỏi `h` | **từ chối có mã** `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |

Từ chối **nêu tên lối đi đúng**: khai khối bằng một điểm trên trục thì tỉ lệ dọc
trục là số hữu tỉ và ca ấy tính được.

**Phạm vi sửa**: đúng một hàm (`_giao_tron_xoay`) + thay `_cat_truc` bằng
`_ti_le_doc_truc`, trong [`curved.py`](../backend/app/simulation/geometry/curved.py).
Không đụng constructor, IR, lược đồ, grounding hay miền exact.

## 4. Oracle — đáp số tính TRỰC TIẾP từ dữ kiện

Không lấy số của kernel rồi so với chính nó. Nón dùng tam giác đồng dạng
`r' = r(h−L)/h`; trụ thì hằng.

| khối | r | h | L | `r'` kỳ vọng | diện tích | vô hướng | ba điểm |
|---|--:|--:|--:|--:|--:|:--:|:--:|
| cylinder | 9 | 20 | 4 | 9 | 81π | ✓ | ✓ |
| cylinder | 9 | 20 | 10 | 9 | 81π | ✓ | ✓ |
| cylinder | 9 | 20 | 16 | 9 | 81π | ✓ | ✓ |
| cone | 10 | 15 | 3 | 8 | 64π | ✓ | ✓ |
| cone | 10 | 15 | 6 | 6 | 36π | ✓ | ✓ |
| cone | 10 | 15 | 12 | 2 | 4π | ✓ | ✓ |
| cone | 3/2 | 5/2 | 1 | 9/10 | 81π/100 | ✓ | ✓ |

`POINT_AND_SCALAR_REPRESENTATION_PARITY`: mỗi cặp cho **cùng** tâm, cùng mặt
phẳng, cùng `radius_sq`, cùng bán kính và cùng diện tích chính xác. Pháp tuyến
so theo **tương đương hình học** (`cross` bằng không), vì hệ số và dấu không
mang nghĩa cho một mặt phẳng.

## 5. Đường sản phẩm và ranh giới

Hai ca — một trụ, một nón — đi trọn với cách khai `height`:

```
RequestContract + SemanticProgramSpec → static → grounding → coverage
→ interpreter/kernel → postconditions → exact từ final_memory
→ Scene3D qua pipeline._dung_scene3d → served
```

| | |
|---|---|
| trụ `r=9 h=20`, cắt `z=10` | `served` · `radius = 9` · `area = 81π` |
| nón `r=10 h=15`, cắt `z=6` | `served` · `radius = 6` |
| `circle3` trong cảnh | `producer = intersect_plane_curved`, `depends = {Khoi, MpCat}` |
| số đo trong cảnh | `9` và `81π` — khớp kết quả exact |
| cách khai `height` còn nguyên trong chương trình được thực thi | ✓ (test khẳng định `apex_or_top is None`) |

`SEMANTIC_POINT_PROVENANCE_PRESERVED`: bản vá **không** mua `served` bằng cách
nới grounding. Test bỏ dữ kiện xuất xứ của `Tam`/`Moc` ⇒ dừng đúng ở
`grounding`.

Ranh giới đã khoá, đọc mã hiện hành chứ không bịa mã mới:

| ca | mã |
|---|---|
| mặt phẳng xiên | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |
| mặt phẳng ngoài chiều cao (`z = −1, 21, 100`) | `CURVED_PLANE_DOES_NOT_CUT` |
| mặt phẳng qua đỉnh nón | `CURVED_PLANE_TANGENT` |
| nón, `h` vô tỉ | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` |
| đáy nón (`L = 0`) | phục vụ, `r' = r` |
| xiên qua **đường sản phẩm** | lỗi hình học có cấu trúc, **không** `ZeroDivisionError` |

`BOUNDARY_REGRESSION`: cầu (cả hai cách khai) · trụ/nón khai bằng điểm ·
`volume`/`lateral_area` ở cả hai cách khai · `c1a` · `c7a` · bộ thiết diện tròn
đã có (`test_curved_section_radius_path.py`, 32 test) — tất cả xanh.

## 6. Fault injection

`FAULT_INJECTIONS_VERIFIED = 5`

| # | gỡ gì | test bắt |
|---|---|---|
| ① | khôi phục đường đọc `truc` cũ | `test_TIEM_1` — scalar-mode ném lại |
| ② | bỏ phép đổi thang `L → t` | `test_TIEM_2` — nón `h ≠ 1` sai bán kính |
| ③ | bỏ hệ số đồng dạng `(1−t)²` | `test_TIEM_3` — cả ba vị trí trả bán kính đáy |
| ④ | đảo gốc đo đáy ↔ đỉnh | `test_TIEM_4` — lát cắt bất đối xứng lộ ngay |
| ⑤ | từ chối mọi scalar-mode | `test_TIEM_5` — ca `served` ở §5 sập |

② và ④ là hai lưới cho đúng cái bẫy thang đo ở §3 — lỗi chỉ hiện ra ở **một
nửa** miền, và trụ thì không bao giờ bắt được nó.

## 7. Identity và cache

| | trước | sau |
|---|---|---|
| `analyze_schema` | `515001b503af5c7c…` | **không đổi** |
| `synthesis_schema` | `8c57c9de49824d61…` | **không đổi** |
| `grammar_card` | `e0fbbc8456da57ae…` | **không đổi** |
| `prompts` | `55ac1ca6a6df92ce…` | **không đổi** |
| `stable_capability_hash` | `85bd316781b86576…` | **không đổi** |
| `semantic_environment_hash` | `f7def6207f5741d9…` | **không đổi** |
| `CACHE_VERSION` | 81 | **81** |
| `candidate` | `d105f83e5f7de0cc…` | **`a5b63aa3cb38e81f…`** (89 file) |

`MODEL_FACING_CONTRACT_CHANGED = NO`. Delta thực tế **đúng bằng** dự kiến: chỉ
hành vi thực thi đổi.

### `CACHE_DECISION_AND_REASON = KHÔNG BUMP`

Hai căn cứ độc lập, cả hai đo được:

**① Luật kho** (`CLAUDE.md §3`): bump khi *"đổi prompt hoặc policy định tuyến"*.
Wave này đổi **không** cái nào — sáu băm model-facing ở trên đều byte-identical.

**② Đường cache thật**: `main.py:713` và `:748` chỉ cache khi
`envelope["status"] == "ok"`. Bản vá **chỉ** biến *từ chối → phục vụ*; nó không
biến một `ok` thành một `ok` khác, vì nhánh khai bằng điểm tương đương đại số
với luật cũ (§3 ③) và 3 777 test xác nhận. Nên **không** envelope đã cache nào
hoá sai.

Candidate đã đóng băng lại vì `backend/app` đổi.

`HISTORICAL_ARTIFACTS_CHANGED = NO` — pool/seal/seed/artifact V3 và toàn bộ
`curved-section-discoverability-dev-v1/` giữ nguyên byte. `measurement_policy.json`
vẫn ghi `"why_not_fixed_here"`; đó là sự thật **của lượt đo ấy**, và bản vá này
đặt cạnh chứ không sửa lên.

⚠️ **Một test lịch sử đã đỏ đúng như nó tự dự báo.**
`test_LOI_HE_khoi_cong_khai_bang_VO_HUONG_khong_cat_duoc` (viết ở wave probe)
khoá **hành vi hỏng** kèm dòng *"sẽ ĐỎ khi lỗi được sửa, và đỏ là ĐÚNG"*. Nó đỏ.
Luật nó bảo vệ là *"lỗi này không được trôi trong im lặng"* — luật ấy nay do
[`test_curved_scalar_axis_intersection.py`](../backend/tests/geometry/test_curved_scalar_axis_intersection.py)
giữ, đầy đủ hơn. Test cũ được **viết lại thành khẳng định về hành vi đúng** và
**giữ tại chỗ** làm bằng chứng lịch sử rằng probe đã tìm ra lỗi trước khi tiêu
quota. Test anh em của nó (`volume`/`lateral_area` không dính) vẫn đúng nguyên
văn.

## 8. Gates

| | |
|---|---|
| `tests/geometry/test_curved_scalar_axis_intersection.py` (MỚI) | **41 passed** (nền đỏ **34/41**) · 5 phép tiêm |
| `tests/geometry/test_curved_section_radius_path.py` | 32 passed |
| `tests/test_section_discoverability_probe.py` | 31 passed (2 test lịch sử viết lại) |
| full backend pytest | **3779 passed** · 1 skipped · 1 deselected, exit 0 (cây sạch) |
| frontend vitest | **698 passed** / 51 file |
| cache identity | passed · `CACHE_VERSION` 81 → 81 |
| candidate verification | exit **0** — `a5b63aa3cb38e81f…` |
| `certify_acceptance_runner.py` | exit **0** · 4 nhãn PASS · 2 readiness YES |
| `replay_demo_cases.py` · `audit_demo_crash_surface.py` | 5/5 · 6/6 · ném ra ngoài 0 |
| `gold_section_discoverability.py` | 7/7 · exact 7/7 · Scene3D 7/7 · biên PASS |
| `git diff --check` | exit **0** |

Frontend chạy dù không có file frontend nào đổi: hợp đồng cảnh (`RENDER_HINT`,
`_TRUONG`) không đổi, và chạy rẻ hơn tranh luận.

## 9. Giới hạn

**①** Wave này **chỉ** xác nhận đường dựng bằng `height` được cắt và đo đúng.
`CURVED_SECTION_MODEL_DISCOVERABILITY = WEAK` (tự phát hiện 0/6) và
`STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` **giữ nguyên** mức bằng chứng đã
công bố — không lượt gọi model nào ở đây.

**②** Nón + chiều cao vô tỉ vẫn **không** phục vụ được. Đó là biên của miền số,
được nói ra bằng mã lỗi kèm lối đi thay thế, không phải một lỗi còn mở.

**③** Pose của nhánh vô hướng vẫn là hướng trục canonical `(0,0,1)`. Đề muốn một
trục nghiêng phải khai bằng điểm — hợp đồng ấy không đổi trong wave này.

**④** `PRODUCT_CAPABILITY_CHANGED = NO`: ba họ vẫn `foundation_only`, nút chưa
hiện.

## 10. Khối kết quả

```
ROOT_CAUSE = `_giao_tron_xoay` đọc `truc` (vectơ trục, = vectơ KHÔNG khi khối
             khai bằng `height`) thay vì `huong_truc` — thuộc tính mà
             CURVED_CONSTRUCTION_GROUNDING_FOUNDATION thêm đúng cho ca này.
             Hai hỏng: chốt ⊥ trục im lặng nhận mọi mặt phẳng, và phép chia
             `d·d = 0` ném ZeroDivisionError trần.
REPRODUCED_BEFORE_FIX = YES  (34/41 đỏ; 5 tổ hợp, 1 qua đường sản phẩm thật)
AXIS_AUTHORITY = CurvedSolid.huong_truc  (+ `s.axis`, vốn đã dùng nó)
HEIGHT_SCALE_PRESERVED = YES — `_ti_le_doc_truc` đổi thang CHỈ ở nhánh vô
             hướng; nhánh khai bằng điểm tương đương đại số với luật cũ
SCALAR_CYLINDER_INTERSECTION = SERVED  (mọi h, kể cả h vô tỉ)
SCALAR_CONE_INTERSECTION = SERVED khi h hữu tỉ · REFUSED_WITH_CODE khi h vô tỉ
POINT_AND_SCALAR_REPRESENTATION_PARITY = 7/7 cặp: tâm · mặt phẳng · radius_sq
             · bán kính · diện tích đều khớp
EXACT_RADIUS_AND_AREA_ORACLE = 7/7 khớp giá trị tính trực tiếp từ dữ kiện
PRODUCT_PATH_SERVABLE = 2/2 (trụ 9/81π · nón 6) — Scene3D đúng producer/depends
BOUNDARY_REGRESSION = PASS (xiên · ngoài chiều cao · qua đỉnh · suy biến ·
             ngoài miền số · cầu · khai bằng điểm · volume/lateral_area · c1a ·
             c7a · 32 test thiết diện tròn)
SEMANTIC_POINT_PROVENANCE_PRESERVED = YES (grounding không bị nới)
FAULT_INJECTIONS_VERIFIED = 5
TEST_RESULTS = mục tiêu 41 · full backend 3779 passed · 1 skipped · 1 deselected
             · vitest 698/51
MODEL_FACING_CONTRACT_CHANGED = NO  (6 băm byte-identical)
CACHE_DECISION_AND_REASON = KHÔNG BUMP — không đổi prompt/policy định tuyến, và
             `main.py` chỉ cache `status == "ok"` nên không envelope nào hoá sai
CACHE_VERSION_BEFORE/AFTER = 81 / 81
CANDIDATE_HASH_BEFORE/AFTER = d105f83e5f7de0cc… / a5b63aa3cb38e81f…
HISTORICAL_ARTIFACTS_CHANGED = NO
APPLICATION_LLM_CALLS = 0
PRODUCT_CAPABILITY_CHANGED = NO
WORKING_TREE = CLEAN
COMMITS = 2  (bản vá + đóng băng lại candidate)
RECOMMENDED_NEXT_ACTION = MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT
```
