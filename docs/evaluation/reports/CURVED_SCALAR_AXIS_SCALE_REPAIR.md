# CURVED_SCALAR_AXIS_SCALE_REPAIR

> 2026-09-07 · `APPLICATION_LLM_CALLS = 0`
>
> ```
> CURVED_SCALAR_AXIS_SCALE_REPAIR = PASS
> DIRECT_RADIUS_ELLIPSE_PATH      = VALID
> POINT_SCALAR_PARITY             = PASS (4 ca parity + 8 ca biên)
> ```
>
> Một hình trụ, hai cách khai, **một hình học**. Lỗi khu trú ở đúng một biểu
> thức, và bản vá là một phép **tổng quát hoá** — không phải một luật mới cho
> một nhánh.

## 1. Tái hiện trước sửa (§2)

Ca đã phát hiện lỗi: `r = 4 · h = 20 · (α): 2x − z + 10 = 0`, oracle `16√5π`,
`z ∈ [2, 18]`.

```
POINT_MODE  (anchor + apex_or_top)  → ELIP, S = 16π√5
SCALAR_MODE (radius + height)       → CURVED_ELLIPSE_CROSSES_CAP
```

Toàn nhánh scalar, không phải một fixture xui — `height² ∈ {100, 400, 1600,
2500}` đều bị từ chối, với `L` lần lượt `5 · 10 · 20 · 25` và `1 − L` lần lượt
`−4 · −9 · −19 · −24`.

## 2. Phân tích đơn vị (§3)

| Đại lượng | Point mode | Scalar mode | Đơn vị đúng |
|---|---|---|---|
| `huong_truc` `u` | `truc`, `\|u\| = h` | `HUONG_TRUC_CANONICAL`, `\|u\| = 1` | vectơ — **hai THANG khác nhau** |
| `L = (tâm−anchor)·u/(u·u)` | `1/2` — **tỉ lệ** | `10` — **khoảng cách** | phụ thuộc thang ⇒ không so trực tiếp được |
| vị trí tâm lát cắt | `(0,0,10)` | `(0,0,10)` | độ dài — **khớp** |
| `duoi_sq = L²·(u·u)` | `100` | `100` | **ĐỘ DÀI²** ✅ |
| `tren_sq = (1−L)²·(u·u)` | `100` | `81` | **ĐỘ DÀI²** ❌ |
| `h_half_sq = r²(\|n\|²\|u\|²−(n·u)²)/(n·u)²` | `64` | `64` | **ĐỘ DÀI²** ✅ (bất biến thang) |
| `height_sq` | `400` | `400` | ĐỘ DÀI² |

**Chứng minh vì sao `tren = 1 − L` đúng một bên và sai bên kia.** Khoảng cách
thật tới đáy trên là `h − L·|u|`.

```
POINT  : |u| = h  ⇒  h − L·h = h(1 − L)  ⇒  (h−duoi)² = (1−L)²·(u·u)   ✅ trùng
SCALAR : |u| = 1  ⇒  h − L                ⇒  (1−L)²·1 = 81 ≠ 100        ❌
```

`1 − L` là *"phần còn lại của một đơn vị"* — chỉ có nghĩa khi `L` là tỉ lệ.

**Kết luận theo dimension analysis, không theo ca chuẩn:** hai trong ba vế của
cap check **đã** ở ĐỘ DÀI² ở cả hai cách khai. Nên đơn vị chuẩn của cả phép
kiểm là ĐỘ DÀI² — **cùng đơn vị mà đường ĐƯỜNG TRÒN đã chọn** (`_giao_tron_xoay`
so `d2` với `height_sq`). Kéo vế thứ ba về đó, chứ không kéo hai vế kia sang
thang tỉ lệ.

## 3. Bản vá (§4)

`_con_cho_toi_day_tren(height_sq, duoi_sq, h_half_sq)` — hỏi `h − duoi ≥ h_half`
mà **không cần biết `h` là số nào**:

```
h ≥ duoi + h_half
⇔ A ≥ 2√(duoi_sq·h_half_sq),   A = height_sq − duoi_sq − h_half_sq
⇔ A ≥ 0  ∧  A² ≥ 4·duoi_sq·h_half_sq
```

Mọi vế `Fraction`. Bình phương hợp lệ vì hai vế không âm (`A < 0` loại trước).

⚠️ **Ở cách khai bằng ĐIỂM, hàm này cho ĐÚNG phán quyết cũ** — khi `|u| = h`
thì `(h − duoi)² = (1−L)²·(u·u)`, chính là `tren_sq` cũ. Đây là **tổng quát
hoá**, không phải một nhánh riêng.

### Vì sao KHÔNG dùng `_ti_le_truc` như §4 gợi ý

Nó đổi sang thang **tỉ lệ**, và để làm thế nó cần `h = √height_sq` **hữu tỉ** —
chính nó từ chối có mã khi `h` vô tỉ. Nhưng hình trụ **không cần** `h`: bán kính
nó là hằng dọc trục, nên `h² = 300` (`h = 10√3`) hiện vẫn cắt được chính xác, và
đường tròn đang làm đúng thế.

Dùng `_ti_le_truc` sẽ **thu hẹp một năng lực đang chạy** để chữa một lỗi thang.
Giữ nguyên **ý định** của §4 — *"một cap check chỉ dùng một hệ đơn vị"* — và
chọn hệ đơn vị mà mã hiện hành đã dùng: **độ dài**. `test_06` khoá bất biến ấy.

Giữ nguyên: số học `Fraction`/`Radical` · đường `circle3` · điểm neo và hướng
trục · mọi mã lỗi biên · đường point mode · bao đóng exact đã công bố.

## 4. Hội tụ toán hạng `height` (§5)

| Consumer | Thẩm quyền thực tế | Trước sửa | Hậu quả đo được | Sửa |
|---|---|---|---|---|
| `ir_static` | `_TOAN_HANG_LENH` | không có `height` | `height: <tên point3>` **lọt** thẩm định tĩnh, vỡ ở `execution` — mà lỗi runtime **không** được gửi ngược cho vòng sửa | +1 dòng |
| `hoisting.O_TEN` | **dẫn xuất** từ `_TOAN_HANG_LENH` | không coi là ô tên | biểu thức lồng vào `height` không được nâng | tự đúng |
| thẻ văn phạm | **dẫn xuất** từ `O_TEN` | in `height?:tên` trần | mô hình không đọc được ô ấy là gì — góp phần làm một lượt đo phải dừng | tự đúng |
| `coverage_gate._phu_thuoc` | **dẫn xuất** từ `_TOAN_HANG_LENH` | mất mắt xích | C₁b không thấy witness phụ thuộc chiều cao | tự đúng |
| `simulation_state._NGUON_CUA_PHEP_DUNG` | viết tay **có chủ đích** | không có `height` | cây thành phần của học sinh mất mắt xích chiều cao | +1 mục |

**Một dòng thêm vào `_TOAN_HANG_LENH` sửa BỐN consumer.** Chỉ bảng viết tay —
nơi duy nhất nói *"trường nào chở provenance"* — phải sửa riêng, đúng như chú
thích của nó đã dặn cho `radius`.

### Static typing

```
scalar hợp lệ (measure)      → PASS
biến chưa dựng               → static rejection, object_id = h
point3 · vector3 · plane3    → static rejection (trước: LỌT)
```

### Dependency

```
cylinder.depends ⊇ {h} · h.depends ⊇ {O, O′}
dependencyClosure(E) ⊇ {O, O′, h, tru}
```

Kiểm trên **cả hai** bảng — `coverage_gate._phu_thuoc` và bảng cảnh.

### Grammar card

```
height?:tên<scalar|float|int>[ĐẠI LƯỢNG chiều cao, thay điểm thứ hai trên trục]
```

**+84 byte, THUẦN đồng bộ schema–thẻ, không một chữ viết tay**: mô tả ấy đã nằm
ở `contract.ConstructCurvedSolidStmt.height` từ 2026-09-04; thẻ không in nó chỉ
vì `O_TEN` thiếu ô. Card C và hai affordance ratio/provenance **nguyên văn**.

## 5. Ca kiểm thử (§6)

**Parity bốn ca** — cùng verdict · cùng tâm · cùng hai bán trục · cùng diện
tích:

| ca | mặt phẳng | kết quả |
|---|---|---|
| `r=4 h=20` | `2x − z + 10 = 0` | `16π√5` ở cả hai |
| `r=3 h=10` | `x − z + 5 = 0` | elip, hai mode khớp |
| `r=5 h=40` lệch đáy dưới | `x − 2z + 10 = 0` | elip, hai mode khớp |
| `r=5 h=50` lệch đáy trên | `x − 2z + 90 = 0` | elip, hai mode khớp |

⚠️ Parity mà cả hai cùng SAI thì vô nghĩa, nên `test_02` neo ca chuẩn vào
oracle độc lập: `center = (0,0,10)` · `b² = 16` · `a² = 80` · `S = 16π√5`.

**Biên** — `h_half = r·|a/c| = 8`, trụ cao 20 ⇒ tâm phải trong `[8, 12]`:

```
d = 8  vừa CHẠM đáy dưới   → elip ✅ (đẳng thức được nhận)
d = 12 vừa CHẠM đáy trên   → elip ✅
d = 7  vượt đáy dưới       → CURVED_ELLIPSE_CROSSES_CAP
d = 13 vượt đáy trên       → CURVED_ELLIPSE_CROSSES_CAP
vượt CẢ HAI đáy (trụ cao 4) → CURVED_ELLIPSE_CROSSES_CAP
mp ∥ trục · mp ⊥ trục      → CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE
tâm ngoài khối             → CURVED_PLANE_DOES_NOT_CUT
circle3 ⊥ trục             → parity, radius_sq = 16
chiều cao VÔ TỈ (h² = 300) → cắt được CHÍNH XÁC
```

Mọi ca biên đều khẳng định **cùng phán quyết ở hai cách khai**.

**Bất biến tỉ lệ** — nhân mọi độ dài bởi `s ∈ {3, 1/2, 5/3}`: bán trục² × `s²`,
tâm × `s`, và **phân loại giữ nguyên** cả ở ca được nhận lẫn ca bị từ chối.

## 6. Replay đường sản phẩm (§7)

```
POINT MODE            → served · 16π√5 · nguồn passed=1
SCALAR MODE trung thực → served · 16π√5 · nguồn passed=1
                         (h = measure(distance, O, O′))
```

Đường scalar **trước bản vá chết ở `execution`** với `CROSSES_CAP`. Chiều cao
do chương trình **ĐO**, nên grounding bỏ qua đúng luật — nó là giá trị tính ra,
không phải dữ kiện khai. Trace và Scene3D đầy đủ; `tru.depends` chứa `h`.

⚠️ Ca `height = 20` khai thẳng thiếu nguồn **giữ nguyên** verdict grounding.
Fixture ấy chứng minh grounding còn chặt, **không** chứng minh kernel lỗi.

## 7. Bảo toàn (§8)

```
plane_equation bác `2x − z + 11 = 0`   ✅ (violated=1, đáp số VẪN 16π√5)
điểm vành tự tạo                        ✅ UNANCHORED_DERIVED_ASSUMPTION
direct-radius + chiều cao dẫn xuất      ✅ served
circle3 point/scalar parity             ✅ radius_sq 16 = 16
cone point/scalar                       ✅ verdict hiện hành (radius_sq = 9)
ball                                    ✅ không đụng
```

## 8. Tiêm lỗi (§9)

| # | tiêm | quan sát |
|---|---|---|
| ① | khôi phục `tren = 1 − L` | point mode qua, scalar mode `CROSSES_CAP` — parity vỡ |
| ② | bỏ quy đổi (coi `height_sq` như đã ở thang tỉ lệ) | scalar mode `CROSSES_CAP` |
| ③ | đảo đáy trên ↔ đáy dưới | ca `d = 13` (dưới hở 13, trên hở 7) **lọt** ở cả hai mode |
| ④ | gỡ `height` khỏi static operands | `height: point3` đi lọt `ir_static` |
| ⑤ | gỡ `height` khỏi dependency sources | `tru.sources` mất `h` |

## 9. Identity và cache (§11)

| thành phần | trước | sau |
|---|---|---|
| `grammar_card` | `285292fe…` | **`2cc55280…`** |
| `capability` | `4b1e2f80…` | **`72edf39f…`** |
| `synthesis_schema` | `6ccef323…` | `6ccef323…` |
| `prompts` | `55ac1ca6…` | `55ac1ca6…` |
| `analyze_schema` | `515001b5…` | `515001b5…` |
| `semantic_environment` | `05b5c6bb…` | **`4d2a555a…`** |

⚠️ **`synthesis_schema` KHÔNG đổi**, và đó là một khẳng định đáng ghi: lược đồ
Pydantic vốn đã có ô `height`. Thứ đổi là những gì hệ **KIỂM** và những gì mô
hình **ĐỌC THẤY** về ô ấy — không phải hình dạng JSON nó được phép viết.

**Quyết định cache bằng hai bằng chứng:**

```
chiều envelope        = rejected → served   (KHÔNG có served → rejected)
model-facing changed  = YES (grammar_card + capability)
routing changed       = NO
```

Không envelope `ok` nào hoá sai: bản vá chỉ **nới** cap check, còn phần **siết**
(`height` bị kiểm kiểu tĩnh) chỉ đổi chỗ chết của một chương trình vốn đã vỡ ở
`execution` — cả hai trạng thái đều không `ok`.

**Bump 89 → 90** theo luật *"đầu vào của mô hình đổi"*, cùng hạng 86/87/89.
Bốn cổng cùng commit + làm mới `cache_identity.lock.json`. Candidate
`422a9e7b…` → **`27f5c076…`** (commit riêng).

## 10. Xử lý test lịch sử (§10)

`test_10_pv7b…` khoá hành vi lỗi và **tự khai sẽ đỏ khi lỗi được sửa**. Nó đã
đỏ. Cùng ba test nữa của wave trước:

| test | trước | nay |
|---|---|---|
| `test_10_pv7b…KHONG_cat_ra_elip` | khoá lỗi | **`…CAT_RA_elip_y_HET_hai_diem`** — khẳng định parity |
| `test_12…khong_co_chieu_cao_nao_di_duoc` | khoá lỗi | **`…moi_chieu_cao_deu_PARITY`** — mạnh hơn: `h` nhỏ thì **cả hai cùng từ chối** |
| `test_13…tien_de_KHONG_dung` | tiền đề bị bác | **`…tien_de_NAY_DUNG`** |
| `test_16` | ghi bất đối xứng thẻ | khẳng định `height?` có đủ kiểu + vai trò |

Cả bốn **giữ chú thích lịch sử** về việc probe đã tìm ra lỗi thế nào. Bộ test
parity mới là authority đầy đủ; các test khoá **luật**, không khoá trạng thái
lỗi đã hết hạn.

## 11. Báo cuối (§14)

```
ROOT_CAUSE = `tren = 1 − L` la khoang cach toi day tren theo TI LE, chi dung
             khi |u| = h. `huong_truc` tra vecto DON VI o nhanh vo huong, nen
             `L` la khoang cach TUYET DOI va `1 − L` mat nghia (L=10 ⇒ −9)
UNIT_ANALYSIS = h_half_sq 64↔64 · duoi_sq 100↔100 (deu DO DAI², BAT BIEN
             thang) · tren_sq 100↔81 (le). Hai trong ba ve DA dung don vi
CANONICAL_AXIS_SCALE = DO DAI² — cung don vi duong TRON da chon
             (`_giao_tron_xoay` so `d2` voi `height_sq`)
SCALAR_MODE_BEFORE = CURVED_ELLIPSE_CROSSES_CAP voi MOI chieu cao
SCALAR_MODE_AFTER  = ELIP, 16π√5, trung khop point mode tung truong
POINT_MODE_REGRESSION = KHONG — ban va la TONG QUAT HOA: khi |u| = h thi
             `(h−duoi)² = (1−L)²·(u·u)`, dung `tren_sq` cu
POINT_SCALAR_PARITY = PASS (4 ca parity + 8 ca bien + bat bien ti le)
EXACT_AREA = 16π√5  (b² = 16 · a² = 80 · tam (0,0,10))
ELLIPSE_CAP_CLASSIFICATION = giu nguyen o moi ca bien; dang thuc (vua CHAM
             day) van duoc NHAN, y nhu truoc
CIRCLE_PATH_REGRESSION = KHONG (radius_sq 16 = 16 o ca hai cach khai)
CONE_PATH_REGRESSION   = KHONG (`_ti_le_doc_truc` van la tham quyen cua non)

HEIGHT_STATIC_TYPING = PASS — scalar qua; chua dung, point3/vector3/plane3
             bi tu choi o TANG TINH (truoc: lot, vo o execution)
HEIGHT_DEPENDENCY    = PASS — ca `coverage_gate._phu_thuoc` (dan xuat) lan
             `_NGUON_CUA_PHEP_DUNG` (viet tay); bao dong cua elip ve du O, O′
HEIGHT_CARD_ROLE     = PASS — `height?:tên<scalar|float|int>[ĐẠI LƯỢNG chiều
             cao…]`, +84 B THUAN dong bo schema–the, khong mot chu viet tay
MODEL_FACING_CONTRACT_CHANGED = YES (grammar_card + capability);
             synthesis_schema · prompts · analyze_schema KHONG doi mot byte
APPLICATION_LLM_CALLS = 0

FAULT_INJECTION_COUNT = 5
CACHE_VERSION_BEFORE/AFTER  = 89 → 90
CANDIDATE_HASH_BEFORE/AFTER = 422a9e7b… → 27f5c076…  (91 file)
PRODUCT_CAPABILITY_CHANGED  = NO  (curved_oblique_section giu foundation_only)
TEST_RESULTS = wave 37 pass (5 tiem) · pytest 4385 pass, 0 do ·
               vitest 698/51 · build PASS · replay 5/5 · crash 6/6 nem 0 ·
               certify PASS · cache identity exit 0 @ v90 ·
               freeze --verify exit 0 (91 file) · diff --check sach
COMMITS      = 3
WORKING_TREE = sach
RECOMMENDED_NEXT_ACTION = OBLIQUE_ELLIPSE_FRESH_E2E_RERUN
```

## 12. Giới hạn (§12)

- **Wave không đo mô hình.** `APPLICATION_LLM_CALLS = 0`. Việc mô hình có tự
  chọn direct-radius hay rim-point giữ **`NOT_MEASURED`**.
- `curved_oblique_section` giữ `foundation_only`;
  `PRODUCT_PROMOTION_ELIGIBLE = NO`.
- Bao đóng V1 **không nới**: vẫn chỉ hình trụ, mặt phẳng xiên, elip nằm trọn
  giữa hai đáy. Nón xiên vẫn ngoài phạm vi.
- Bản vá **fail-open theo đúng chỗ đáng**: nó gỡ một từ chối OAN, không nới một
  phép kiểm đang gác đúng — mọi ca vượt đáy thật vẫn bị bắt, ở cả hai cách khai.

**Việc kế tiếp: `OBLIQUE_ELLIPSE_FRESH_E2E_RERUN`.** Đề · oracle · gold ·
registration đã sẵn (`docs/evaluation/geometry/oblique-ellipse-e2e-after-plane-equation/`);
cập nhật identity mới (`CACHE_VERSION 90`, `grammar_card 2cc55280…`,
`capability 72edf39f…`, candidate `27f5c076…`), trần **5 logical application
calls**. Tiền đề §10 của lượt ấy — *"hình trụ có đường hợp lệ
`radius + height`"* — **nay đứng vững**, nên kết luận về `rim_point` đọc được.
