# PHASE_2_CURVED_SOLID_FOUNDATION — nền khối cong

> Thực hiện **2026-09-03**. **0 lượt gọi model · 0 module riêng theo hình ·
> 0 dependency mới.**
>
> ⚠️ Đây là **NĂNG LỰC HỆ**, không phải **NĂNG LỰC SẢN PHẨM**.
> `CURVED_PRODUCT_ENABLED = NO` cho tới khi Phase 3 đo được.

---

## 1. Hai thứ tách bạch, và tài liệu này không trộn chúng

| | |
|---|---|
| `SYSTEM_CURVED_FOUNDATION` | **CLOSED** — IR, runtime, thẩm định, vết, vận chuyển, vẽ đều có đường hợp lệ |
| `CURVED_PRODUCT_CAPABILITY` | **NO** — lời từ chối trong prompt giữ nguyên, 0 bài mẫu, 0 nút |

Cả hai đều có cổng máy: `test_29_prompt_VAN_tu_choi_hinh_cong__san_pham_chua_mo`
và `test_45_khong_bai_mau_nao_dung_hinh_cong`.

⚠️ **Mâu thuẫn phải khai, không giấu:** thẻ văn phạm nay **dạy**
`construct_curved_solid`, trong khi prompt vẫn **bảo** từ chối mặt cầu. Hai câu
trái nhau cùng gửi cho mô hình. Đó là trạng thái §29 yêu cầu dừng lại ở, và là
việc **đầu tiên** Phase 3 phải dọn.

---

## 2. Một thẩm quyền — `CURVED_KIND_AUTHORITIES = 1`

`geometry/curved.py` giữ `KHOI_CONG`: **ba hàng**, mỗi hàng một hình, kèm neo
bắt buộc · danh từ tiếng Việt · vai điểm thứ hai · hai công thức đo.

Thêm hình thứ tư = thêm **một hàng**. Cổng đếm được (`test_04c`): đúng **hai**
tệp sản phẩm nhắc tên cả ba hình — bảng, và enum hợp đồng. Tệp thứ ba nghĩa là
một tầng đã mọc bản điều phối riêng.

```
SHAPE_SPECIFIC_PRODUCT_MODULES  0   (không sphere.py / cylinder.py / cone.py)
```

---

## 3. Phát hiện trung tâm — ba điểm neo, không (trục, bán kính)

Khai `(trục d, bán kính r)` thì để dựng bất cứ thứ gì trên vành phải tìm
`v ⊥ d, |v| = r`. Với `d = (1,1,1)`, vectơ vuông góc hữu tỉ gần nhất có
`|v| = √2` — **vô tỉ**, và thiết diện qua trục lập tức rời ℚ³.

Ba điểm hữu tỉ giữ mọi toạ độ trong ℚ³ **kể cả khi bán kính vô tỉ và trục xiên**:

```
trục XIÊN (1,2,2), A = (2,−1,0) ⊥ trục ✔
  r² = 5  ⇒ r = √5 VÔ TỈ    h² = 9 ⇒ h = 3
  V = 15π       S_xq = 6π√5      mọi ĐỈNH vẫn hữu tỉ
```

Bán kính được phép vô tỉ vì nó là **đại lượng ĐO**, qua `sqrt_rational` ở đúng
biên đo — y hệt `distance_sq`.

### Hệ quả lớn nhất: thiết diện qua trục cần **0 phép dựng mới**

```
B = divide_segment(A, O, ratio="2")   ← điểm xuyên tâm đối, ratio ngoài [0,1]
td = construct_polygon(S, A, B)
Std = measure area(td)                 ← Phase 1
```

Ba phép đều có TRƯỚC wave này. `NEW_PROBLEM_WITHIN_CURVED_IR_REQUIRES_CODE = NO`
được chứng minh bằng một chương trình chạy thật (`test_38_CONE_2`), không bằng
lập luận.

---

## 4. Biểu diễn

```
ball      (I,  —,  A)   biên: |X−I|² ≤ |A−I|²
cylinder  (O,  O′, A)   biên: chiếu lên OO′ ∈ [0,1] ∧ d²(X,trục) ≤ |A−O|²
cone      (O,  S,  A)   biên: chiếu ∈ [0,1] ∧ d²(X,trục) ≤ (1−t)²|A−O|²
```

Bất biến kiểm ở `CurvedSolid.__post_init__`, so **BẰNG** trên `Fraction`:
vành khác tâm · trục không suy biến · **vành vuông góc trục**. Lệch một phần
triệu vẫn bị từ chối (`test_06b`).

`radius_sq`, `height_sq`, `truc`, `axis` là **`@property` dẫn xuất** — không lưu
trùng. Một sự thật, một chỗ.

```
COORDINATE_DOMAIN_CHANGED   NO
CURVED_POINT_SOLVER_ADDED   NO
```

Giao *đường thẳng* với mặt cong cho `t = (−B±√Δ)/2A` ⇒ toạ độ ∈ `ℚ(√Δ)³`, thứ
`Vec3` không chở nổi. Phép ấy **không tồn tại**, và `test_11` giữ nó không tồn
tại bằng cách đọc bảng chữ ký, không bằng lời hứa trong chú thích.

---

## 5. Hợp đồng kiểu không nói dối — điểm thiết kế then chốt (§16)

`intersect_plane_curved` khai trả `circle3` và **chỉ** trả `circle3`.

| ca suy biến | mã | lời từ chối chỉ sang |
|---|---|---|
| mặt phẳng tiếp xúc cầu | `CURVED_PLANE_TANGENT` | `project_onto(tâm, mp)` |
| mặt phẳng qua đỉnh nón | `CURVED_PLANE_TANGENT` | đỉnh đã là điểm có tên |
| mặt phẳng xiên (elip) | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` | — |
| mặt phẳng qua trục | `CURVED_SECTION_OUTSIDE_V1_CLOSURE` | `divide_segment` + `construct_polygon` |
| ngoài biên / không cắt | `CURVED_PLANE_DOES_NOT_CUT` | — |

**Không ca nào là một năng lực bị cắt** — mỗi ca là một lối được chỉ sang đúng
primitive đã tồn tại. Nhờ vậy `_CHU_KY` khai được đúng một kiểu trả về, và
`STATIC_TYPE_AUTHORITY` khớp `RUNTIME_TRUTH`.

⚠️ Mã lỗi **tách hẳn** khỏi `section.py`. Một mặt phẳng xiên cắt một hình trụ
**hoàn toàn lành lặn** thì khối không hỏng — dùng lại `MALFORMED_SOLID` ở đây là
lặp đúng lỗi mà `SECTION_COPLANAR_EDGE_GAP` đã phải đi sửa. `test_1415` khoá.

---

## 6. Phép đo — từ vựng tối thiểu, và các phép **KHÔNG** thêm

| thêm | vì sao KHÔNG suy ra được |
|---|---|
| `radius(circle3 \| curved_solid)` | `circle3` từ phép giao có tâm/vành **không tên nào trỏ tới** |
| `lateral_area(curved_solid)` | công thức π, không hợp thành được |
| `volume` **mở rộng** nhận `curved_solid` | một tên cho một khái niệm |
| `area` **mở rộng** nhận `circle3` | idem — không đẻ `circle_area` |

**KHÔNG thêm, và có chứng minh:**

```
height  = distance(anchor, apex_or_top)      ← hai ĐIỂM CÓ TÊN
slant   = distance(apex_or_top, rim_point)   ← hai ĐIỂM CÓ TÊN
```

Cổng hợp thành G4 đã cấm thêm cửa cho thứ nói được rồi; luật ấy áp ở đây y
nguyên. `test_38_CONE_1` dùng `distance(S, A)` để lấy đường sinh `√5`.

### `SURFACE_AREA_POLICY` — không hứa diện tích toàn phần

`S_tp` nón `= πrl + πr²`; với `r=1, h=2` là `π√5 + π` — hai căn thức khác nhau,
`radical.add` **từ chối**. `test_42b` chứng minh bằng chính miền số, nên nếu ai
đó thêm `surface_area` sau này thì ca ấy vẫn đỏ ở đúng chỗ: phép cộng.

Ba công thức mặt cong thì **luôn** biểu diễn được — mỗi cái là một hữu tỉ × π ×
đúng một căn. Chứng minh bằng liệt kê 81 tổ hợp neo (`test_19`), không bằng lập
luận.

```
EXACTNESS  ball R²=3 → R=√3 · V=4π√3 · S=12π
           cyl trục xiên → V=15π · S_xq=6π√5
           cone r=1,h=2 → l=√5 · V=2π/3 · S_xq=π√5
           circle r²=5 → S=5π
FLOAT_FALLBACK  0
```

---

## 7. Mặt cầu ngoại tiếp — §8 trả lời bằng chương trình chạy thật

```
GENERAL_CIRCUMSPHERE_CONSTRUCTION   SUPPORTED
```

Tâm = giao **ba mặt trung trực**, và mặt trung trực dựng được bằng
`plane_perpendicular_to_line(midpoint, line)` — phép của **G4**, có trước wave
này. **Không primitive nào được thêm cho riêng bài toán này.**

Tứ diện vuông `A(0,0,0) B(2,0,0) C(0,2,0) D(0,0,2)` ⇒ tâm `(1,1,1)`, `R = √3`,
và `test_08` kiểm **cách đều bốn đỉnh** bằng kernel chứ không tin tên biến.

Đối chiếu với `gm_10` cũ: cùng đáp số `√3`, nhưng nay tâm do **kernel tính** từ
các điểm đã dựng, thay vì mô hình giấu định lý vào toạ độ một điểm nó bịa.

```
CURVED_OBJECT_IS_RUNTIME_OBJECT   YES
CURVED_GEOMETRY_LAUNDERING        0
R0                                PASS
```

`_KIEU_DUOC_GIA_THIET` là danh sách **trắng** `{point3, vector3}` — hai kiểu cong
không có tên trong đó, nên không có đường nào khai một mặt cầu bằng toạ độ.
`test_40c` dựng lại nguyên lớp lỗi `gm_10` và cổng xuất xứ từ chối.

---

## 8. Vết · vận chuyển · vẽ

```
TRACE       một khối cong = MỘT câu lệnh = MỘT bước = MỘT khung. Bất biến #31
            nguyên vẹn; không mesh animation, không hình học lấy mẫu.
TRANSPORT   CURVED_SCENE_HAS_VERTICES  NO
            CURVED_SCENE_HAS_FACES     NO
RENDER_KINDS_ADDED   2   (`circle`, `curved_solid`) — KHÔNG ba
```

`TESSELLATION_POLICY`: renderer chia lưới **chỉ để vẽ**, và bảo đảm là **cấu
trúc** chứ không phải lời dặn — payload không có ô nào để một đỉnh nội suy đi
ngược lên phép đo hay checker.

⚠️ **Cổng renderer đã chứng minh mình có răng.** Bản đầu của tôi tự đo khoảng
cách giữa hai điểm neo để lấy `r` và `h` — tức tầng vẽ đang **làm hình học**.
`scene3d.test.tsx` bắt được ngay lần đầu tiên nó cần. Sửa: backend gửi
`radius_sq`/`height_sq`, tầng vẽ chỉ lấy căn ở biên hiển thị.

Cổng *"không primitive ngoài hợp đồng ngữ nghĩa"* được thay bằng một cổng
**chặt hơn**: thay vì liệt kê thứ bị cấm (một danh sách luôn thiếu), nó đòi
chiều ngược lại — **mọi hình cong renderer vẽ phải truy được về một `curved_kind`
ở backend**. `Torus`/`Tube`/`Lathe`/`Extrude`/`Shape` vẫn cấm tuyệt đối.

---

## 9. Hợp đồng model-facing

```
MEMORY_TYPES_ADDED    2   circle3 · curved_solid   (KHÔNG sphere/cylinder/cone)
câu lệnh              +1  construct_curved_solid   (MỘT cho ba hình)
biểu thức             +1  intersect_plane_curved
lượng đo              +2  radius · lateral_area
CHECKERS_ADDED        0
```

**0 checker**, có lý do kép: taxonomy nghĩa vụ **đã niêm phong** cùng baseline
nghiên cứu (§44 cấm chạm), và không nghĩa vụ v1 nào **đòi** một checker cong.
Thêm cho đối xứng là thêm mã chết.

| | trước | sau | Δ |
|---|---|---|---|
| thẻ đầy đủ | 4436 | **4703** | +267 |
| thẻ `hinh_hoc` (**thứ mô hình nhận**) | 4035¹ | **4035** | — |
| lược đồ tổng hợp | 103051 | **111152** | +8101 |

¹ Sau khi cắt gọn bốn chuỗi `nghia` đang nhắc lại thứ dòng chữ ký đã in
(4183 → 4035); trần thẻ hình học nay có cổng riêng ở `test_grammar_card`.

```
MODEL_FACING_SCHEMA_CHANGED   YES     GRAMMAR_CARD_CHANGED   YES
MODEL_DISCOVERABILITY         NOT_MEASURED_THIS_WAVE   (0 lượt gọi model)
```

---

## 10. Phiên bản

Cổng danh tính cache **đỏ trước khi làm mới**, và nêu đúng ba thành phần:

```
thành phần đổi: ['grammar_card', 'synthesis_schema', 'capability']
```

`prompts` **không** đổi — bằng chứng máy cho §29.

```
CACHE_VERSION            64 → 65
STABLE_CAPABILITY_HASH   6153fdc38b1968a2… → 8d51b70f2d52fd2d…   ĐỔI
SEMANTIC_ENV_HASH        69bb7cf8d04d2587… → 15ac9710ffb2dd1d…
PRODUCT_CANDIDATE        dcce61e26c14b059… → 25de3a88ba6f8dc9…  (87 → 88 file)
SEALED_RESEARCH_BASELINE a075e9f5…  KHÔNG đổi, không chạy lại
HISTORICAL_SCORES_CHANGED  NO       APPLICATION_LLM_CALLS  0
```

Lý do bump: cache giữ **cả envelope**. Envelope đã cache đến từ một hệ **không
có khái niệm khối cong**, và cả chương trình không cong cũng sinh dưới một hợp
đồng khác (`volume` nhận thêm kiểu, enum `quantity` dài thêm hai).

---

## 11. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **2977 passed**, 1 skipped (+65 ca mới) |
| `vitest` | **690 passed** (50 tệp) |
| `npm run build` | PASS |
| `replay_demo_cases` | 5/5 · chuỗi rút gọn 1/1 |
| `audit_demo_crash_surface` | 6/6 · **ném 0** |
| `lock_cache_identity --verify` | exit 0 · version 65 |
| `freeze --verify` | 88 file · `25de3a88ba6f8dc9…` |
| tám phép đo trình duyệt | 8/8 · 7/7 · 7/7 · 9/9 · 4/4 · 13/13 · 11/11 · 21/21 · **LOI_CONSOLE 0** |

Sáu nhân chứng §38: **6/6**.

> ⚠️ **ĐÍNH CHÍNH 2026-09-03** (`CURVED_MODEL_ACCEPTANCE_V1`). Câu này ban đầu
> viết *"chạy hết đường IR → thẩm định tĩnh → grounding → runtime → vết →
> cảnh"*. Chính xác hơn: sáu nhân chứng gọi `kiem_tinh` →
> `SemanticProgramInterpreter` → `build_scene`, và **không** đi qua
> `verify_and_compile` — tức không qua cổng grounding lẫn **cổng phủ**.
> Grounding có test riêng (`test_40c`); cổng phủ thì **chưa từng chạy với một
> khối cong**, và lượt đo live đã tìm ra đúng lỗ đó
> (`CURVED_OBLIGATION_COVERAGE_GAP`).

---

## 12. Giới hạn còn lại, khai chính xác

1. **Bao đóng giao hẹp và cố ý.** Chỉ mặt phẳng ⊥ trục (trụ, nón) và mọi mặt
   phẳng cắt cầu. Elip, conic, giao đường–mặt cong, giao cong–cong đều từ chối
   có mã. Đây là ranh giới của **miền toạ độ**, không của cài đặt.
2. **`S_tp` không viết được** — giới hạn của miền số (§6).
3. **Thẻ và prompt đang mâu thuẫn** (§1) — Phase 3 phải dọn.
4. **`MODEL_DISCOVERABILITY` chưa đo.** Ta biết mô hình *được dạy* từ vựng cong;
   ta **không** biết nó dùng đúng không. Không lượt gọi model nào trong wave này.
5. **Chưa có bằng chứng trình duyệt cho hình cong** — không bài mẫu nào dùng nó,
   đúng theo §45. Tuyến vẽ được chứng minh ở tầng test và ở cổng `curved_kind ↔
   backend`, không ở Chrome.
