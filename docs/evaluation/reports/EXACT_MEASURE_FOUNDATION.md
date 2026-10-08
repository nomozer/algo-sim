# EXACT_MEASURE_FOUNDATION — Phase 1 của lộ trình hình học cong

> Thực hiện **2026-09-03**. **0 lượt gọi model · 0 kiểu hình cong · 0 loại vẽ
> mới · 0 dependency mới.**
>
> Đây là **nền số học và phép đo**, không phải hình học cong. Sau wave này
> `CURVED_GEOMETRY_SUPPORT` vẫn là **NONE**.

---

## 1. Hai việc, và vì sao chúng đi cùng nhau

| | trước | sau |
|---|---|---|
| miền số chính xác | `he·√can` | `he·π^mu·√can`, `mu ∈ {0,1}` |
| diện tích phẳng | **không có** | `area_polygon` · IR `measure area` |

π là **tiền đề** của mọi đại lượng cong (`(4/3)πR³`, `πr²h`, `πrl`…). `area`
thì **không cần** π — và đó chính là lý do nó đi trước: nó đóng một lỗ **đang
mở** của hình đa diện, chứ không mở một mặt trận mới.

`CURRENT_ARCHITECTURE_GAP_AUDIT` tìm ra đúng một lỗ nằm ở **cả hai** tầng (IR
lẫn kernel): `area`. Hệ dựng được thiết diện chính xác rồi không nói được nó
rộng bao nhiêu.

---

## 2. Miền số — một trường, không phải một CAS

`Radical` thêm `mu: int = 0`. Mặc định `0` nên `Radical(he, can)` cũ vẫn dựng
đúng số cũ và **so BẰNG** với số dựng sau; miền số không tách làm hai.

### 2.1 `PI_EXPONENT_DOMAIN = (0, 1)` — hẹp có chủ đích

Không phải giới hạn tạm. Kiểm mọi đại lượng cong THPT:

```
V cầu (4/3)πR³ · S cầu 4πR² · V trụ πr²h · S_xq trụ 2πrh
V nón (1/3)πr²h · S_xq nón πrl
```

**Không** cái nào có `mu = 2`, và không phép đo nào của IR chia cho một đại
lượng chứa π (thứ duy nhất sinh `mu` âm). Mở "cho đủ" thì `π²·gì đó` biểu diễn
được mà không phép đo nào sinh ra — tức mở một cửa chỉ dùng để đi nhầm.

### 2.2 Bất biến chính tắc tổng quát hoá

Luật cũ *"`can == 1` ⇒ về `Fraction`"* **sai** khi có π: `2π` có `can == 1` mà
không hữu tỉ. Luật đúng, và nó bao luật cũ:

```
về `Fraction`  ⇔  GIÁ TRỊ hữu tỉ  ⇔  can == 1 VÀ mu == 0
```

Vẫn một cách viết cho một số: `0·π·√5 → 0`, `π√4 → 2π`, `π^0√3 → √3`.

### 2.3 Bốn phép, và ba cánh cửa cố ý KHÔNG mở

| phép | luật |
|---|---|
| `add` | cùng `can` **và** cùng `mu`. `π√5 + 2π√5 = 3π√5`; `π√5 + π`, `π + 1`, `√2 + √3` **từ chối** |
| `multiply` (mới) | `(h₁h₂)·π^(m₁+m₂)·√(c₁c₂)`, chuẩn hoá sau — `√5·√5 = 5`, `π·π` **từ chối** |
| `times_rational` · `divided_by_rational` | giữ nguyên `mu` (hệ số hữu tỉ) |
| `square` | **từ chối** mọi `mu ≠ 0` |

**`square` từ chối là quyết định đáng nói nhất.** `(π√5)² = 5π²` — ngoài miền,
và không phải `Fraction`. `check_distance` so `d² == khai²`, nên trả một
`Fraction` đúng-hệ-số mà sai-giá-trị sẽ làm **bộ chấm nói PASS**. Đó là kiểu
hỏng đắt nhất có thể xảy ra ở tầng này.

Ba cửa không mở, cùng một lý do — **chưa ai đi qua**:
`divide(a, b)` tổng quát · `sqrt(π)` · văn phạm chữ `parse_exact` cho π.

### 2.4 Giới hạn THẬT, khai thẳng

`S_tp` của nón `= πrl + πr²` — hai căn thức khác nhau ⇒ **không viết được**.

Đây **không** phải một giới hạn mới. Nó đúng là `√2 + √3` mà kho đã cố ý chọn,
chỉ lộ ra ở một chỗ khác. Mở tổng tuỳ ý là bước đầu tiên của một CAS.

---

## 3. Toạ độ KHÔNG đổi — bất biến đắt nhất của wave

```
COORDINATE_DOMAIN_CHANGED   NO
```

`Vec3` vẫn là **ℚ³**; `hf()` vẫn từ chối mọi thứ không hữu tỉ. Mở miền **ĐO**
không mở miền **TOẠ ĐỘ**, và hai thứ ấy phải tách bạch:

- toạ độ vô tỉ làm hỏng **mọi** vị từ so bằng của kernel (`same_point`,
  `coplanar`, `point_on_plane`) — chúng hoặc sai, hoặc phải học so gần đúng, mà
  so gần đúng chính là thứ `Fraction` được chọn để tránh;
- đại lượng vô tỉ chỉ là **một đáp số bình thường**.

Khoá bởi `test_pi_exact_domain.py::test_N10_*` — ba loại số vô tỉ, cả ba bị
`Vec3.of` từ chối.

---

## 4. Diện tích — MỘT thẩm quyền, và thứ tự phép toán là điều kiện tồn tại

```
S = ½ · | Σᵢ Pᵢ × Pᵢ₊₁ |
```

⚠️ **Cộng các tích có hướng trong ℚ³ TRƯỚC, lấy căn ĐÚNG MỘT LẦN ở cuối.**

Cộng diện tích từng tam giác thì mỗi hạng tử **đã là một căn**, và `add` từ chối
tổng nhiều căn khác căn thức — cách ấy hỏng ở đúng những đa giác thú vị nhất.
Thiết diện lục giác của hộp 2×2×2 (`3√3`) là ca chứng minh: nếu ai đó "đơn giản
hoá" thành tổng tam giác, `test_A2` và `test_A5` ĐỎ.

Nên thứ tự ở đây **không phải tối ưu — nó là điều kiện để hàm này tồn tại trong
miền số của kho**.

| | |
|---|---|
| `AREA_MATHEMATICAL_AUTHORITIES` | **1** — `area_section` là adapter 3 câu lệnh |
| đồng phẳng | **kiểm**, dùng lại `predicates.coplanar`, so BẰNG trên `Fraction` |
| không phẳng | **từ chối**, không chiếu xấp xỉ |
| suy biến (thẳng hàng) | trả **0** — câu trả lời đúng |
| thứ tự biên | giữ **nguyên** thứ tự `cross_section` dựng; không `sort` |

**Vì sao suy biến trả 0 chứ không từ chối:** từ chối ở đây là đặt một luật thẩm
định vào một phép **ĐO** — sai thẩm quyền. `exec_construct_polygon` mới là nơi
quyết một dãy đỉnh có phải đa giác hợp lệ hay không, và nó cố ý không cấm thẳng
hàng.

`test_MOT_tham_quyen_toan_hoc` cấm luôn việc đẻ `area_triangle`/`area_quad`, và
đếm **câu lệnh** của adapter bằng `ast` (đếm dòng thì một docstring dài làm cổng
đỏ, và một cổng đỏ vì lý do sai sẽ bị nới cho xong).

---

## 5. IR — một hàng ở thẩm quyền chữ ký

`measure_contract.BANG_PHEP_DO["area"]`: nhận `polygon3` · `section`, **một**
toán hạng. Validator tự sinh câu *"Chỉ volume, area đo trên một đối tượng"* từ
chính bảng ấy — không thêm một nhánh `if` nào.

⚠️ **KHÔNG nhận `solid`.** "Diện tích toàn phần một khối" là đại lượng khác, và
tổng diện tích các mặt rơi đúng vào tổng nhiều căn thức bị từ chối. Hứa nó là
dạy mô hình một cửa dẫn tới **lỗi runtime** — mà lỗi runtime không được gửi
ngược để sửa, nên nó giết cả ca.

Tên hiển thị do **backend** sở hữu: `_CACH_GOI["measure.area"]` → *"Diện tích
ABCD"* / `S(ABCD)`, cùng họ ký hiệu với `V(…)`. Không bảng nào ở frontend.

---

## 6. Tuần tự hoá — payload cũ không đổi một byte

`to_json` **bỏ** trường `pi` khi `mu == 0`.

Phát `"pi": 0` cho mọi số cũ sẽ đổi **byte** của mọi payload đang tồn tại
(fixture, envelope đã cache, artifact đánh giá) mà **không** đổi một giá trị
toán học nào.

```
SERIALIZATION_CHANGED               YES (chỉ THÊM trường tuỳ chọn `pi`)
WIRE_FORMAT_CHANGED_FOR_OLD_VALUES  NO  (byte-đối-byte)
MATHEMATICAL_PAYLOAD_CHANGED        NO
```

Mặc định *"vắng ⇒ `mu = 0`"* thuộc về **`from_json`**, và mirror TS chỉ lặp lại
nó. Frontend `hienSo` đọc `x.pi ?? 0`, và **từ chối** số mũ ngoài `{0,1}` —
tới đó nghĩa là backend đã mở miền mà phía này chưa biết; đoán bừa sẽ in ra một
đại lượng không tồn tại.

---

## 7. Cổng danh tính cache đỏ được — chứng minh (§27)

Trước khi làm mới khoá, cổng bắt đúng thứ đã đổi:

```
MÔI TRƯỜNG SINH NGỮ NGHĨA ĐÃ ĐỔI.
  khoá:  version 63 · f545293124e52891…
  hiện:  version 63 · 69bb7cf8d04d2587…
  thành phần đổi: ['grammar_card', 'synthesis_schema', 'capability']
```

Ba thành phần, đúng ba thứ thật sự đổi. `prompts` và `analyze_schema` **không**
đổi — và cổng nói đúng điều đó.

### Quyết định bump: 63 → **64**

Cache giữ **cả envelope** (`row.envelope_json`), không chỉ lượt phân tích. Một
envelope sinh trước wave này đến từ một hệ **không diễn đạt được diện tích**, nên
một đề hỏi *"tính diện tích thiết diện"* đã phân tích dưới thẻ cũ sẽ **mãi mãi**
trả về một mô phỏng thiếu phép đo ấy. Đúng loại hồi quy câm mà con số này tồn
tại để chặn.

Bốn cổng bump, cùng một commit: `main.py` · `test_api.py` · `CURRENT_STATE.md` ·
`test_evaluation_candidate.py`.

---

## 8. Hợp đồng model-facing — đo, không dự đoán

Đo bằng một **worktree tách riêng ở HEAD**, không chép số từ báo cáo trước:

| | trước | sau | Δ |
|---|---|---|---|
| thẻ văn phạm `hinh_hoc` (**thứ mô hình thật sự nhận**) | 3316 | **3484** | +168 |
| thẻ đầy đủ | 4431 | **4436** | +5 |
| lược đồ tổng hợp | 103043 | **103051** | +8 |

```
MODEL_FACING_SCHEMA_CHANGED   YES  (enum `quantity` thêm "area")
GRAMMAR_CARD_CHANGED          YES  (+168 byte ở thẻ hình học)
MODEL_DISCOVERABILITY         NOT_MEASURED_THIS_WAVE  (0 lượt gọi model)
STABLE_CAPABILITY_HASH        803722ff59dfbdf6… → 6153fdc38b1968a2…  ĐỔI
```

Băm năng lực **có** bao chữ ký phép đo (qua `_KIEU_DO`) — nên nó đổi, đúng như
mong đợi. Nếu nó **không** đổi thì đó mới là chỗ phải soát.

Dòng thật trong thẻ:

```
measure: quantity(distance|angle_cos_sq|angle_cos|volume|area) of:tên wrt?:tên
area(of:tên<polygon3|section>) — không có wrt
  diện tích một hình PHẲNG — đa giác hoặc thiết diện. Chỉ cần `of`, không có `wrt`
```

---

## 9. KHÔNG có hình cong nào lọt vào (§24)

Soát diff sản phẩm (`backend/app` + `frontend/src`):

```
CURVED_TYPES_ADDED         0   (MemoryType không đổi một dòng)
CURVED_RENDER_KINDS_ADDED  0   (RENDER_HINT · RENDER_KINDS không đổi)
section.py                 0 dòng đổi
renderer                   0 mesh cầu/trụ/nón mới
số lượt `sphere|cylinder|cone|circle3|curved_solid` trong diff:  0
CURVED_GEOMETRY_SUPPORT    NONE
```

Hai lượt khớp `Sphere` ở `scene3d-view.tsx` là **chấm điểm** vẽ bằng hình cầu
nhỏ, có từ trước, không nằm trong diff. Lời từ chối mặt cong trong prompt
**giữ nguyên**, `ERR_RUA_NANG_LUC` **giữ nguyên**.

```
PI_EXACT_QUANTITY  FOUNDATIONAL_NUMERIC_EXTENSION
AREA_POLYGON       FOUNDATIONAL_MEASUREMENT_EXTENSION
AREA_SECTION       COMPOSITION/ADAPTER
```

---

## 10. Ca thử — 65 ca mới, ba nhóm

| nhóm | tệp | ca |
|---|---|---|
| số học | `test_pi_exact_domain.py` | **34** |
| diện tích | `test_area_polygon.py` | **19** |
| IR | `test_measure_area_ir.py` | **12** |

Nhóm IR đo **đường**, không đo công thức: `area_polygon` đúng mà không ai gọi
được thì diện tích vẫn **không tồn tại** với hệ — đúng bài học
`distance_sq_skew_lines` (kernel có sẵn phép tính, cầu nối chưa nối, `hp_b01_032`
chết hai lượt ở Phase 7B).

Ba kết quả kiểm tay đáng ghi:

```
tứ giác nghiêng ABCD            √2      (I1, A2)
tam giác ABD                    √2/2    (I1b)
thiết diện lục giác hộp 2×2×2   3√3     (I2, A5)
```

---

## 11. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **2912 passed**, 1 skipped (+66 ca) |
| `vitest` | **689 passed** (50 tệp, +4 ca) |
| `npm run build` | PASS |
| `replay_demo_cases` | 5/5 · chuỗi rút gọn 1/1 |
| `audit_demo_crash_surface` | 6/6 biên đúng · **ném 0** |
| `lock_cache_identity --verify` | exit 0 · version 64 · `69bb7cf8d04d2587…` |
| `freeze --verify` | 87 file · `dcce61e26c14b059…` |
| tám phép đo trình duyệt | 8/8 · 7/7 · 7/7 · 9/9 · 4/4 · 13/13 · 11/11 · 21/21 · **LOI_CONSOLE 0** |

---

## 12. Giới hạn còn lại, khai chính xác

1. **`area` chưa có bằng chứng trình duyệt riêng.** Không bài mẫu nào dùng nó,
   nên không phép đo nào trong Chrome chạm tới. Tuyến hiển thị thì **đã** được
   chứng minh giống hệt: `test_I6` cho thấy `area` sinh ra cùng loại vật cảnh
   (`quantity → readout`) với `volume`/`distance`, mà hai cái ấy có bằng chứng
   trình duyệt. Câu đúng: *"đường hiển thị đã được chứng minh, phép đo cụ thể
   thì chưa được nhìn thấy trong trình duyệt."*
2. **`S_tp` không viết được** (§2.4) — giới hạn của miền, không phải của cài đặt.
3. **π chưa có người sinh.** Không phép đo nào trả về đại lượng chứa π sau wave
   này. Nền đã sẵn; Phase 2 mới dùng tới.
4. **`MODEL_DISCOVERABILITY` chưa đo** — 0 lượt gọi model theo yêu cầu wave. Ta
   biết mô hình **được dạy** `area`; ta **không** biết nó có dùng đúng không.

---

## 13. Phiên bản

```
CACHE_VERSION            63 → 64
STABLE_CAPABILITY_HASH   803722ff59dfbdf6… → 6153fdc38b1968a2…
SEMANTIC_ENV_HASH        f545293124e52891… → 69bb7cf8d04d2587…
PRODUCT_CANDIDATE        7aecc78c21b671f8… → dcce61e26c14b059…  (87 file)
SEALED_RESEARCH_BASELINE a075e9f5…  KHÔNG đổi, không chạy lại
HISTORICAL_SCORES_CHANGED  NO
APPLICATION_LLM_CALLS      0
```
