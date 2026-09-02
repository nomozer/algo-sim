# CURVED_GEOMETRY_FOUNDATION_DESIGN — kiến trúc trước khi cài đặt

> Soát + thiết kế, **2026-09-03**. `SOURCE_CHANGES = 0` · `APPLICATION_LLM_CALLS = 0`.
> Không sửa một dòng mã sản phẩm; mọi con số dưới đây đo từ HEAD hoặc tính
> trong REPL trên chính kernel đang chạy.

---

## 1. HEAD

```
HEAD                    594f128 · git clean (0 file)
CACHE_VERSION           63
STABLE_CAPABILITY_HASH  803722ff59dfbdf6…
SEMANTIC_ENV_HASH       f545293124e52891…
EVALUATION_CANDIDATE    7aecc78c21b671f8…  (87 file — khớp bản đã đóng băng)
```

---

## 2. Hình cong hôm nay: KHÔNG CÓ — và nó đóng kín ở bốn tầng

Không phải "chưa làm". Bốn tầng độc lập từ chối, và tầng thứ tư mới là tầng
đáng kể:

| tầng | cơ chế | vị trí |
|---|---|---|
| prompt | *"Đề cần mặt cầu, mặt nón, mặt trụ hoặc quỹ tích — nói thẳng là không diễn đạt được"* | `skills/geometry_program_generator.md:76` |
| lược đồ | không `MemoryType` nào chở mặt cong; `_CHU_KY` không có phép nào trả về nó | `contract.py:194`, `ir_static_check.py:107` |
| kernel | không có kiểu, không có vị từ, không có phép đo | `geometry/` |
| **xuất xứ** | **`ERR_RUA_NANG_LUC`** — mô hình tự giải rồi *giấu định lý vào toạ độ* một điểm nó bịa | `grounding_gate.py:271`, `source_entities.py` |

Tầng thứ tư sinh ra từ `gm_10` (*mặt cầu ngoại tiếp*): mô hình khai
`P_opposite = [2,2,2]` với `model_assumption` nghe hợp lý, lấy `midpoint` ra tâm
mặt cầu, `distance` ra `√3` — **đáp số đúng cho một khái niệm runtime không hề
biểu diễn**. Cổng xuất xứ chặn vì tên ấy không có trong đề.

Đây là ràng buộc thiết kế mạnh nhất của cả wave: **một nền hình cong chỉ hợp lệ
nếu mặt cầu là vật ĐƯỢC DỰNG mà kernel tính bán kính**, không phải một điểm mô
hình khai. Nền nào không đạt điều đó thì chỉ là hợp thức hoá `gm_10`.

---

## 3. Giả định đa diện — bản đồ đo được

Quét toàn đường sản phẩm cho `vertices` / `faces` / `edges_of_face` / `Polyhedron`:

| tệp | lượt | phân loại | mặt cong chạm không |
|---|---|---|---|
| `geometry_exec.py` | 21 | POLYHEDRON_ONLY | **có** — cầu nối IR→kernel, thêm nhánh |
| `simulation_state.py` | 12 | GENERIC_3D (điều phối theo lớp runtime) | **có** — thêm hàng bảng |
| `geometry_obligations.py` | 4 | CHECKER_ONLY | **có** — checker mới |
| `interpreter.py` · `coverage_gate.py` · `validator.py` | 6 | POLYHEDRON_ONLY *ở mức CÂU LỆNH* | **có** — đọc `stmt.vertices` để dựng vết/xuất xứ |
| `contract.py` | 3 | POLYHEDRON_ONLY | **có** — `ConstructSolidStmt` |
| `scene3d.py` | 2 | RENDER_ONLY (`_TRUONG`, `RENDER_HINT`) | **có** — hai hàng bảng |
| `section.py` | cả tệp | POLYHEDRON_ONLY | **KHÔNG** — xem §10 |
| `kernel.py` · `predicates.py` · `measure.py` | 0 | **GENERIC_3D** | mở rộng, không sửa |

Kết luận quan trọng: **hạt nhân toán học không giả định đa diện.** `Vec3`,
`Line3`, `Plane3`, 20 vị từ, 18 phép đo đều làm việc trên điểm/đường/mặt. Giả
định đa diện tập trung ở **cầu nối IR** và **phép thiết diện** — hai chỗ, không
phải khắp nơi.

### 3b. Bức tường thật KHÔNG phải tô-pô — mà là MIỀN TOẠ ĐỘ

`Vec3` là **ℚ³** (`x, y, z: Fraction`, `exact.py:79`). Mọi phép của kernel là
hữu tỉ–tuyến tính, nên ℚ³ đóng dưới toàn bộ IR hiện tại.

Giao một **đường thẳng** với một mặt cầu cho nghiệm `t = (−B ± √Δ)/2A`. Toạ độ
giao điểm rơi vào **ℚ(√Δ)³**, và `Vec3` không chở nổi. Đây là ràng buộc **cứng
hơn** "chưa có mặt". Nó quyết định toàn bộ hình dáng của v1:

> **v1 không được sinh ĐIỂM nằm trên mặt cong.**

Mọi thứ dưới đây dẫn từ câu đó.

---

## 4. So sánh representation

| | A. enum hình | B. mặt ẩn `F=0` | C. quadric `xᵀAx+bᵀx+c` | D. tham số hoá | **E. khối cong giải tích có biên** |
|---|---|---|---|---|---|
| chính xác | — | tuỳ `F` | **ℚ đủ** | cần lượng giác ⇒ vô tỉ | **ℚ đủ** |
| giao | mỗi cặp một hàm | không đóng | mp∩quadric = conic | dở | **đóng trong lớp đã khai báo** |
| đo | phải biết là hình gì | không dẫn ra được | **phải phân loại lại** | tốt | **tham số có sẵn tên** |
| tuần tự hoá | tầm thường | biểu thức | 10 số hữu tỉ | hàm số | 3 điểm + thẻ |
| độ phức tạp phía mô hình | thấp | **cao** | **cao** | cao | thấp |
| vết | ok | ok | ok | ok | ok |
| vẽ | ok | tessellate ẩn (đắt) | ok | ok | ok |
| mở rộng | kém | tốt nhất | tốt | tốt | **thêm HÀNG bảng** |

**Chọn E.** Ba lý do, không lý do nào là "ít mã nhất":

1. **Quadric mất BIÊN.** Hình trụ hữu hạn *không phải* một quadric — quadric cho
   ống vô hạn. Muốn có khối thì vẫn phải kèm biên ⇒ đã là E rồi, chỉ khoác áo C.

2. **Quadric mất DANH TÍNH.** Từ `A, b, c` muốn biết "đây là trụ, bán kính r,
   chiều cao h" phải chéo hoá — và trị riêng của ma trận hữu tỉ **không hữu tỉ**.
   Tức tầng đo/hiển thị phải *suy lại* thứ constructor vốn đã biết. Kho này đã gỡ
   đúng lối ấy hai lần (`producer`-sniffing, `TU_PHEP_DUNG`); dựng lại nó ở tầng
   sâu hơn là đi lùi.

3. **Phép đo cần tên tham số, không cần phương trình.** `V = πr²h` cần `r` và `h`
   *được gọi tên*. Quadric không có chúng.

Câu trả lời cho §2 — *"dùng chung một representation giải tích được không?"* —
là: **được về toán, sai về kiến trúc.** Cái đáng chia sẻ không phải *một phương
trình chung* mà là **một giao diện chung**: (i) vị từ thuộc-mặt chính xác,
(ii) tham số hữu tỉ đã có tên, (iii) mô tả biên.

---

## 5. PHÁT HIỆN TRUNG TÂM — khai bằng BA ĐIỂM, không khai bằng (trục, bán kính)

Đây là quyết định làm nên hoặc phá hỏng cả nền, và nó đã được **kiểm bằng số**.

Khai `(trục d, bán kính r)` thì để dựng bất cứ thứ gì trên vành phải tìm
`v ⊥ d, |v| = r`. Với `d = (1,1,1)`, vectơ vuông góc hữu tỉ gần nhất có
`|v| = √2` — **vô tỉ**. Thiết diện qua trục lập tức rời ℚ³.

Khai `(O đáy, O′ đỉnh, A trên vành)` — **ba điểm hữu tỉ, đúng thành ngữ IR đã
dùng cho đa diện** — thì mọi thứ ở lại ℚ³:

```
trụ (O,O′,A) = ((0,0,0), (0,0,2), (1,0,0))
  chữ nhật qua trục:  (1,0,0) (−1,0,0) (−1,0,2) (1,0,2)      ← toàn hữu tỉ
trục XIÊN (1,2,2), A = (2,−1,0):  A ⊥ trục ✔   r² = 5   r = √5
  → bán kính VÔ TỈ mà mọi ĐỈNH vẫn hữu tỉ
```

Bán kính được phép vô tỉ vì nó là **đại lượng đo**, đi qua `sqrt_rational` ở
đúng biên đo — y hệt `distance_sq` hiện nay. Toạ độ thì không bao giờ vô tỉ.

Hệ quả: `B = 2·O − A` (điểm xuyên tâm đối), `A′ = A + (O′−O)` — thiết diện qua
trục là **phép dựng hữu tỉ thuần**, và ba phép trên đã có sẵn trong IR
(`translate`, `divide_segment`).

---

## 6. Kiểu ngữ nghĩa

### Thêm — hai kiểu

| kiểu | WHY_REQUIRED | WHO_PRODUCES | WHO_CONSUMES | RENDERABLE | MEASURABLE | CHECKABLE |
|---|---|---|---|---|---|---|
| `curved_solid` | mặt cầu/trụ/nón phải là **vật dựng được** thì cổng xuất xứ mới không phải chặn nó như `gm_10` | `construct_curved_solid` | đo · giao · checker · cảnh | có (tham số) | V, S, r, h, l | thuộc-mặt, nội/ngoại tiếp |
| `circle3` | `mp ∩ mặt cầu` phải trả về **một vật có tên**; không có nó thì cách duy nhất diễn đạt "đường tròn giao tuyến" là khai thẳng tâm ⇒ đúng lối rửa năng lực | `intersect_plane_curved` | đo (bán kính, diện tích) · cảnh | có | r², area | tâm, đồng phẳng |

⚠️ `circle3` **không** thêm vì UI cần vẽ vòng tròn. Thêm vì **cổng fail-closed**:
thiếu nó, đường tròn giao tuyến chỉ tồn tại được dưới dạng một toạ độ mô hình tự
khai — thứ `grounding_gate` phải từ chối. Đây là câu trả lời cho §8.

### KHÔNG thêm

| | vì sao |
|---|---|
| `curve3` | không phép nào của v1 sinh ra đường cong tổng quát. Thêm để đối xứng = thêm một kiểu rỗng. |
| `surface3` (mặt vô hạn rời) | `curved_solid` đã chở mặt **và** biên; tách ra thì mọi phép đo phải hỏi lại biên ở đâu. |
| `conic3` (elip, parabol) | mp xiên ∩ trụ. Xem §9 — **ngoài closure v1**. |
| `sphere`/`cylinder`/`cone` là ba kiểu riêng | ba kiểu ⇒ ba nhánh ở **mọi** tầng, đúng thứ §4 cấm. Một kiểu + **thẻ `kind` trong dữ liệu** ⇒ điều phối bằng **một bảng, ở một thẩm quyền**. |

---

## 7. Mô hình KHỐI CÓ BIÊN

Mặt vô hạn và khối hữu hạn phải tách bạch, và biên **thuộc ngữ nghĩa**:

```
CurvedSolid(kind, anchor, apex_or_top, rim_point)
  ball      (I, —,  A)   biên: |X−I|² ≤ |A−I|²
  cylinder  (O, O′, A)   biên: hình chiếu lên OO′ ∈ [0,1]  ∧  d²(X, OO′) ≤ |A−O|²
  cone      (O, S,  A)   biên: hình chiếu ∈ [0,1]  ∧  d²(X,trục) ≤ (1−t)²|A−O|²
```

Ba điểm neo, tất cả **hữu tỉ**, tất cả **có tên trong chương trình**. Không tham
số nào là số trần do mô hình khai — mọi thứ dẫn từ điểm đã dựng, R0 nguyên vẹn.

**Renderer không bao giờ suy biên.** Xem §12: payload cảnh chở *tham số*, không
chở mảng đỉnh, nên renderer **không có chỗ** để đặt một biên tự nghĩ ra.

---

## 8. Ma trận chính xác — đo thật, không suy đoán

Miền hiện tại: `Fraction ∪ Radical(he·√can)`, `MAX_RADICAND = 10¹²`, và
`add` **từ chối** `√2 + √3` (`radical.py:238`).

| đại lượng | cầu | trụ | nón | phân loại |
|---|---|---|---|---|
| vị từ thuộc mặt | `\|X−I\|² = r²` | `d²(X,trục) = r²` | `(v·d)² = cos²θ·\|v\|²\|d\|²` | **EXACT_WITH_CURRENT_DOMAIN** |
| vị từ trong khối | ≤ | ≤ ∧ chiếu ∈[0,1] | ≤ ∧ chiếu ∈[0,1] | **EXACT_WITH_CURRENT_DOMAIN** |
| mp ∩ mặt (⊥ trục / mọi mp với cầu) | → `circle3` tâm ℚ³, r² ∈ ℚ | idem | idem | **EXACT_WITH_CURRENT_DOMAIN** |
| đường ∩ mặt | toạ độ ∈ ℚ(√Δ) | idem | idem | **REQUIRES_DOMAIN_EXTENSION → NGOÀI v1** |
| mp xiên ∩ trụ/nón | — | elip | conic | **NGOÀI v1** (cần kiểu conic) |
| thiết diện qua trục | — | chữ nhật ℚ³ ✔ | tam giác ℚ³ ✔ | **EXACT** — nhờ §5 |
| khoảng cách tâm→mp | ✔ | ✔ | ✔ | **EXACT** (đã có) |
| bán kính, chiều cao | `√(r²)` | ✔ | ✔ | **EXACT** |
| đường sinh nón | — | — | `√(r²+h²)` = **một** căn | **EXACT** |
| **diện tích đa giác/thiết diện** | — | — | — | **EXACT_WITH_CURRENT_DOMAIN** ⟵ §11 |
| V, S mặt cong | `(4/3)πR³`, `4πR²` | `πr²h`, `2πrh` | `(1/3)πr²h`, `πrl` | **EXACT_WITH_EXTENSION (π)** |

### 8b. Mở rộng miền: **một trường**, không phải một CAS

Mọi đại lượng cong của chương trình THPT có đúng dạng `he · π^mu · √can`.
Kiểm bằng REPL trên kernel thật:

```
① area(tam giác (0,0,0)(1,0,0)(0,1,0)) = 1/2      area(thiết diện 4 đỉnh) = √2
②  l(r=1,h=2) = √5        ⇒ S_xq = πrl  ⇒ (he=1, mu=1, can=5)
③  R² = 3 ⇒ R³ = 3√3      ⇒ V  = (4/3)πR³ ⇒ (he=4, mu=1, can=3)
④  π√5 + π·1              ⇒ TỪ CHỐI (RadicalDomainError) — giới hạn THẬT
⑤  πr²h − (1/3)πr²h       ⇒ cùng can, cùng mu ⇒ CỘNG ĐƯỢC = (2/3)πr²h
```

`Radical` thêm **một** số nguyên `mu`. Luật cộng giữ nguyên tinh thần fail-closed,
chỉ thêm một điều kiện: cùng `can` **và** cùng `mu`.

⚠️ **Giới hạn phải khai, không được giấu (dòng ④):** `S_tp` của nón `= πrl + πr²`
có hai căn khác nhau ⇒ **từ chối**. Đây **không** phải một loại giới hạn mới —
nó đúng là giới hạn `√2 + √3` mà kho đã cố ý chọn, chỉ lộ ra ở chỗ khác. Mở tổng
tuỳ ý = biến `radical.py` thành CAS, và kho đã viết ra lý do không làm thế.

⛔ **Không epsilon, không float, không dung sai** ở bất kỳ tầng nào. `float` chỉ
tồn tại ở `length()` / `degrees()` — biên **trình bày** đã có sẵn.

---

## 9. Bao đóng giao — v1 khai chính xác, không hứa quá

```
INTERSECTION_CLOSURE_V1
  mp ∩ ball                     → circle3 | point3 | ∅        (mọi mặt phẳng)
  mp ⊥ trục ∩ cylinder          → circle3
  mp ⊥ trục ∩ cone              → circle3 | point3(đỉnh)
  mp chứa trục ∩ cylinder/cone  → polygon3  (chữ nhật / tam giác — §5)
  ────────────────────────────────────────────────────────────
  NGOÀI closure, TỪ CHỐI CÓ MÃ, không xấp xỉ:
  đường ∩ mặt cong              → CURVED_INTERSECTION_LEAVES_RATIONAL_DOMAIN
  mp xiên ∩ trụ/nón             → CURVED_SECTION_NOT_A_CIRCLE
  mặt cong ∩ mặt cong           → ngoài v1
```

Không hứa "giao hai mặt ẩn bất kỳ". Bao đóng nào không chứng minh được là hữu tỉ
thì không vào.

---

## 10. Mô hình thiết diện — chọn **C + B hẹp**

Ba lựa chọn §10, và lý do **không** chọn A:

`Section` chở `steps: tuple[SectionStep(face_index, a, b)]` — một **lời kể dựng
hình trên các mặt của đa diện** (*"trên mặt (SBC), nối M với N"*). Đường tròn
không có lời kể ấy. Nhét nó vào `Section` làm `steps` rỗng nghĩa và làm checker
`section_matches` (so chu trình đỉnh) vô nghĩa.

```
SECTION_MODEL_V1
  `section`  GIỮ NGUYÊN — đa giác, đa diện. 0 dòng đổi trong section.py.
  `circle3`  vật ĐỘC LẬP do phép giao sinh ra, KHÔNG phải một biến thể của section.
  thiết diện qua trục → `polygon3` (đỉnh hữu tỉ), dùng lại checker đa giác đã có.
```

Chọn theo tính nhất quán: **một kiểu = một bất biến**. `section` bất biến "chu
trình cạnh trên mặt khối"; `circle3` bất biến "tâm + pháp + r²". Gộp là mất cả hai.

---

## 11. Phép đo — và vì sao `area` đi TRƯỚC

`MEASURE_MODEL_V1` cần: `radius` · `height` · `slant` · `distance` · `area` ·
`surface_area` · `volume` · `angle`.

`area` **đang thiếu ở kernel đa diện** — đây là lỗ duy nhất mà
`CURRENT_ARCHITECTURE_GAP_AUDIT` tìm thấy ở **cả hai tầng** (IR lẫn kernel).

Và nó **chính xác với miền hiện tại, không cần mở rộng gì**:

```
area(đa giác phẳng) = ½·|Σᵢ Pᵢ × Pᵢ₊₁|
```

Tổng **các tích có hướng** cộng trong ℚ³ trước, rồi lấy **một** căn duy nhất ở
cuối — nên không bao giờ chạm luật từ chối `√2+√3`. Đã kiểm: `½` và `√2` ở §8b①.

Nên câu trả lời cho §11 là: **mở một thẩm quyền `area` chung, và mở nó TRƯỚC hình
cong** — không phải vì tiện, mà vì (i) nó là tiền đề của mọi `S_xq`, `S_tp`, (ii)
nó đóng một lỗ đang mở của đa diện, (iii) nó **không chạm từ vựng hình dạng gửi
cho mô hình**, nên không thể tạo ra một nút UI hứa quá.

---

## 12. Vẽ — và bất biến tessellation ở dạng CẤU TRÚC

`RENDER_KINDS` hiện có `point_marker · line · surface · mesh · polygon · readout ·
non_visual`, đồng bộ cứng với `scene3d.RENDER_HINT` (khoá bởi
`test_scene3d_ts_sync.py`). Thêm **hai hàng**: `circle`, `curved_solid`.

```
_TRUONG["curved_solid"] = ("kind", "anchor", "apex_or_top", "rim_point")
_TRUONG["circle3"]      = ("center", "normal", "radius_sq")
```

⚠️ **Không có `vertices` trong hai hàng đó — và đó là toàn bộ cơ chế.**

`TESSELLATION_POLICY`: renderer **được phép** chia lưới để hiện hình. Lưới ấy
**không bao giờ** trở thành hình học ngữ nghĩa, và cách bảo đảm không phải một
lời dặn mà là **không có đường dẫn**: payload không chở đỉnh, nên không có chỗ
nào để một đỉnh nội suy đi ngược lên checker hay phép đo. So sánh: `solid` chở
`vertices` vì đỉnh đa diện **là** ngữ nghĩa; `curved_solid` thì không.

Test khoá đề xuất: quét `SceneObject` loại `curved_solid`/`circle3` — có khoá
`vertices`/`faces` là **ĐỎ**.

---

## 13. Vết

```
Semantic Program → vật giải tích chính xác → vết tất định
                 → hình học trình bày tất định → renderer chia lưới
```

Khả thi, **không đụng bất biến #31** (`frame k ⇔ trace[k]`): một `curved_solid` là
**một bước dựng**, một khung. Không có gì liên tục đi vào dòng thời gian — đúng
ranh giới §1b đã đặt khi loại "kéo để thấy bất biến" ra ngoài phạm vi.

`SectionStep` không cần đổi vì §10 giữ `section` nguyên vẹn.

---

## 14. IR gửi cho mô hình

```
MODEL_FACING_IR_DELTA
  MemoryType          +2   circle3 · curved_solid
  _KIEU_DUNG          +1   construct_curved_solid(kind, anchor, apex_or_top, rim_point)
  _CHU_KY             +2   intersect_plane_curved → circle3
                           axial_section → polygon3
  measure             +4   area · surface_area · radius · slant
  GEOMETRY_CHECKERS   +2   point_on_curved_surface · inscribed/circumscribed
  ────────────────────────────────────────────────────
  tổng ≈ 11 hàng bảng. KHÔNG có mã theo họ bài toán.
```

Phân loại theo §14:

| | |
|---|---|
| **FOUNDATIONAL_PRIMITIVE** | `construct_curved_solid` · `intersect_plane_curved` · `area` · `volume/surface_area` |
| **DERIVED_COMPOSITION** | điểm xuyên tâm đối (`divide_segment`/`translate` đã có) · trục (`construct_line`) · mặt đáy (`plane_perpendicular_to_line` — đã có từ G4) · thiết diện qua trục (dựng 4 điểm rồi `construct_polygon`) |
| **DISPLAY_ONLY** | lưới tam giác · số vòng chia · nhãn `(S)`, `(C)` |

Không có `construct_sphere_problem_1`. Không có `kind` nào mã hoá một dạng đề.

---

## 15. Phép thử NEW SHAPE ≠ NEW CODE — sáu bài đại diện

| # | bài | biểu diễn bằng IR đề xuất | cần mã mới? |
|---|---|---|---|
| 1 | mặt cầu `I`, `R=3`; `(P): z=2` cắt theo `(C)`, tính bán kính `(C)` | `declare I, A` → `construct_curved_solid(ball, I, —, A)` → `construct_plane P` → `intersect_plane_curved` → `measure radius` = **√5** | **KHÔNG** |
| 2 | thể tích khối cầu bán kính `a` | ball + `measure volume` = `(4/3)πa³` | **KHÔNG** (cần π ở Phase 1) |
| 3 | trụ `r`, `h`: diện tích xung quanh | `construct_curved_solid(cylinder, O, O′, A)` + `measure surface_area` | **KHÔNG** |
| 4 | mp ∥ đáy cách đáy `d`, cắt trụ theo đường tròn — tính bán kính | `translate` → `plane_perpendicular_to_line` (đã có, G4) → `intersect_plane_curved` → `measure radius` | **KHÔNG** |
| 5 | nón `r`, `h`: đường sinh và thể tích | cone + `measure slant` = `√(r²+h²)` + `measure volume` | **KHÔNG** |
| 6 | thiết diện qua trục của nón — tính diện tích | `B = 2·O − A` (`divide_segment`) → `construct_polygon(S, A, B)` → `measure area` | **KHÔNG** |

```
NEW_PROBLEM_WITHIN_CURVED_IR_REQUIRES_CODE   NO   (6/6, trong closure §9)
NEW_SHAPE_REQUIRES_MODULE                    NO   (một HÀNG bảng, không một module)
```

Bài #6 là bài đáng kể nhất: nó **chỉ** ra được vì §5 chọn khai bằng ba điểm. Khai
`(trục, bán kính)` thì #6 rơi khỏi ℚ³ và phải từ chối. Đó là lý do §5 là quyết
định trung tâm chứ không phải chi tiết.

---

## 16. Phạm vi THPT — giá trị / độ phức tạp

| | giá trị | độ phức tạp | phán |
|---|---|---|---|
| **SPHERE** | cao — mặt cầu ngoại tiếp là dạng đề rất phổ biến, và `gm_10` cho thấy hệ đang **thua đúng ở đó** | **thấp nhất** — mọi mp cắt cầu đều cho đường tròn hữu tỉ | **v1** |
| **CYLINDER** | cao — trụ + thiết diện qua trục | thấp, **với** khai ba điểm | **v1** |
| **CONE** | cao — đường sinh, thiết diện qua trục, nón nội tiếp | thấp | **v1** |
| ellipsoid / paraboloid / hyperboloid | ~0 trong chương trình | trung bình | **KHÔNG** |

Không dựng engine hình học tính toán cho mọi quadric. Ba hình, vì chương trình
có ba hình.

---

## 17. Khối tròn xoay

Nền §7 tổng quát hoá **một nửa**:

- **KHUNG thì có.** `(trục, điểm vành)` chính là khung của mọi mặt tròn xoay;
  cầu/trụ/nón là các ca profile = cung tròn / đoạn ∥ trục / đoạn xiên.
- **PHÉP ĐO thì không.** Profile tổng quát cần biểu diễn đường cong, và
  `V = π∫f²dx` / Pappus **nằm ngoài** `ℚ(√, π)`. Không có tích phân ký hiệu nào
  trong kho, và thêm vào là thêm một CAS.

```
SOLID_OF_REVOLUTION = PHA KIEN TRUC THU HAI
```

Không ép v1 chở nó. Ghi rõ ở đây để lần sau không ai coi đó là "chỉ thêm một hàng".

---

## 18. Khối ghép / khối bù

Tách làm ba, vì chúng **không** cùng độ khó:

| | cần gì | phán |
|---|---|---|
| vị từ trong/ngoài | đã có sẵn ở §8 (`≤` + biên) | **rẻ** |
| **số học trên đại lượng** — `V = V_trụ − V_nón` | một phép `combine_quantity`; §8b⑤ cho thấy `πr²h − (1/3)πr²h` **cộng được** vì cùng `can`, cùng `mu` | **LATER_FOUNDATION** (nhỏ, gần như rơi ra từ π) |
| **CSG biên** — mặt của hiệu hai khối | phức hợp ô hỗn hợp, tô-pô mới, và diện tích/thể tích của nó nói chung ngoài `ℚ(√,π)` | **OUT_OF_SCOPE** |

Điểm đáng nói: *"khối ghép/bù"* ở đề THPT gần như luôn là **số học trên thể
tích**, không phải CSG hình học. Đừng trả giá CSG cho một nhu cầu cộng trừ.

---

## 19. Trung thực năng lực

Sau v1, một nút chỉ được hiện là **supported** khi có đường hợp lệ qua **cả bảy**:
IR · runtime · thẩm định · vết · vận chuyển · vẽ · fail-closed.

Cụ thể cho wave này:

- **Không** hiện nút *hình cầu* chỉ vì `scene3d-view.tsx` vẽ được một mặt cầu.
- Câu từ chối trong prompt (`skills/…:76`) **phải hẹp lại chứ không xoá**: mở
  đúng closure §9, và **giữ nguyên** lời từ chối cho quỹ tích, mp xiên ∩ trụ,
  đường ∩ mặt cong.
- `ERR_RUA_NANG_LUC` **giữ nguyên**. Nó không phải rào tạm — nó là thứ bảo đảm
  mặt cầu được **dựng** chứ không được **khai**.

---

## 20. Ba pha

### PHASE 1 — `EXACT_MEASURE_FOUNDATION` *(không có hình cong nào)*
```
radical.py   +1 trường `mu` (số mũ π) · luật cộng: cùng can ∧ cùng mu
             · display / to_json / from_json / parse_exact
measure.py   +area_polygon, area_section        ← chính xác, KHÔNG cần mở miền
IR           +measure "area"                    MemoryType: KHÔNG đổi
cảnh/renderer  KHÔNG đổi (`quantity` đã chở `exact`)
CACHE_VERSION  BUMP (thẻ văn phạm đổi) · capability hash đổi · đóng băng lại candidate
```
Đóng lỗ `area` của **đa diện**. Có giá trị **kể cả khi hình cong không bao giờ mở**.

### PHASE 2 — `CURVED_SOLID_FOUNDATION`
```
exact.py     +Circle3, +CurvedSolid(kind, 3 điểm neo) · MỘT bảng `_MAT_CONG`
predicates   +point_on_curved_surface, +point_inside_curved_solid
kernel       +intersect_plane_curved → Circle3 | Point3 | từ chối có mã
measure      +volume/surface_area/radius/slant (dùng π từ Phase 1)
IR           +2 MemoryType · +1 câu lệnh dựng · +2 biểu thức · +2 checker
scene3d      +2 hàng — THAM SỐ, không đỉnh
frontend     RENDER_KINDS +circle +curved_solid · chia lưới CHỈ ở scene3d-view.tsx
section.py   KHÔNG ĐỔI MỘT DÒNG
```

### PHASE 3 — `CURVED_PRODUCT_INTEGRATION`
```
prompt + thẻ văn phạm: hẹp lời từ chối đúng closure §9 (KHÔNG xoá)
bài mẫu hình cong (build_geometry_samples.py) · learner_surface · nút UI
đo lại: candidate mới, và MỌI tuyên bố năng lực phải đo lại — số cũ không chuyển sang
```

Ba pha. Không mười.

---

## 21. Quyết định

```
SHOULD_CURVED_GEOMETRY_BE_NEXT      YES — nhưng KHÔNG bắt đầu bằng hình cong

FIRST_IMPLEMENTATION_TARGET         PHASE 1 · EXACT_MEASURE_FOUNDATION
                                    (π trong miền số + `area`)

FOUNDATION                          Khối cong giải tích có biên (E), khai bằng
                                    BA ĐIỂM HỮU TỈ, điều phối bằng MỘT bảng ở
                                    MỘT thẩm quyền

FIRST_SUPPORTED_SHAPES              ball · cylinder · cone  (Phase 2)

DEFER                               conic (mp xiên) · đường ∩ mặt cong ·
                                    tròn xoay tổng quát · CSG biên ·
                                    quadric ngoài ba hình
```

Vì sao Phase 1 đi trước, gọn trong ba câu: mọi phép đo cong đều là `π ×` một đại
lượng dạng diện tích, nên π và `area` là **tiền đề**, không phải bạn đồng hành.
`area` đang thiếu ở đa diện — làm nó trước đóng một lỗ **đang mở**, thay vì mở
một mặt trận mới. Và Phase 1 **không chạm từ vựng hình dạng gửi cho mô hình**,
nên nó không thể sinh ra một nút hứa quá — đúng luật §19.

---

## 22. Điều wave này KHÔNG quyết được, và người phải quyết

Ba hệ quả nằm ngoài thẩm quyền của một bản thiết kế:

1. **Phá đóng băng.** `CLAUDE.md §0` ghi `IMPLEMENTATION_FROZEN_FOR_THESIS`.
   Phase 1 chạm `backend/app/**` ⇒ candidate hết hiệu lực và phải đóng băng lại.
   Baseline nghiên cứu đã niêm phong (`a075e9f5…`) **không** bị chạm — nhưng nó
   cũng **không** nói được gì về năng lực mới.
2. **Phase 3 buộc phải tiêu quota.** Mở từ vựng gửi cho mô hình mà không đo lại
   thì không có tuyên bố nào dùng được. `§0` đang ghi benchmark **CLOSED**.
3. **Phạm vi khoá luận.** `STATUS_LEDGER §0-2026-08-24` không liệt hình cong.
   Mở nó là một quyết định phạm vi, không phải một wave kỹ thuật.

Phase 1 là bước duy nhất **không** kích hoạt (2) và (3): nó đóng một lỗ đã có,
không hứa một năng lực mới nào với người dùng.

---

```
SOURCE_CHANGES         0
APPLICATION_LLM_CALLS  0
```
