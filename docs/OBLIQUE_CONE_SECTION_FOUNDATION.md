# OBLIQUE_CONE_SECTION_FOUNDATION

> 2026-09-08 · `APPLICATION_LLM_CALLS = 0` · **họ hình cuối cùng trong phạm vi**
>
> ```
> ROOT_CAUSE = KERNEL_BRANCH_MISSING   (không phải khoảng trống miền số)
> SYSTEM_EXPRESSIBLE        = YES      DETERMINISTICALLY_CORRECT = YES
> CONIC_CLASSIFICATION_EXACT = YES     FINITE_CONE_CONTAINMENT   = YES
> POINT_SCALAR_PARITY        = YES
> OBLIQUE_CONE_ELLIPSE_AREA  = 12π√6/5   (a² = 32/5 · b² = 27/5)
>
> PARABOLA_FAIL_CLOSED   = CURVED_CONE_SECTION_PARABOLIC
> HYPERBOLA_FAIL_CLOSED  = CURVED_CONE_SECTION_HYPERBOLIC
> CROSSES_BASE_FAIL_CLOSED = CURVED_ELLIPSE_CROSSES_CAP
> DEGENERATE_FAIL_CLOSED   = CURVED_PLANE_DOES_NOT_CUT
>
> CHECK_AREA_PASS = YES · TRACE_PASS = YES · SCENE3D_PASS = YES
> NEW_MEMORY_TYPES = 0 · NEW_IR_OPERATIONS = 0 · NEW_AUTHORITIES = 0
> CARD_DELTA_BYTES = +18 · CARD_DELTA_CLASS = CAPABILITY_SYNC
>
> CAPABILITY_STATUS  EXPRESSIBLE_ONLY → FOUNDATION_ONLY
> FEATURE_SCOPE_COMPLETE = YES
> ```
>
> Khoảng trống hoá ra đúng như roadmap đo: **một nhánh kernel**. Điều roadmap
> chưa nói là chỗ khó thật nằm ở đâu — không phải công thức bán trục, mà là
> **tâm elip**, thứ tôi dẫn sai ngay lần đầu.

## 1. Chẩn — và điều đã bị bác từ wave trước

`MISSING_FAMILY_ROADMAP_REFRESH` đã bác ghi chú registry *"ba nhánh chưa phân
xử"* như một câu về miền số. Wave này xác nhận lại trên đường chạy thật:

```
CURRENT_FAILURE_CODE = CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE
lý do trong mã       = "nón cắt xiên cho elip/parabol/hyperbol tuỳ độ dốc —
                        ba nhánh chưa phân xử"
```

`ROOT_CAUSE = KERNEL_BRANCH_MISSING`. Mọi tầng khác đã sẵn: `ellipse3` là một
`MemoryType`; `BANG_PHEP_DO["area"]` đã nhận `ellipse3`; `scene3d.py` ánh xạ
`ellipse3 → ellipse`; frontend đã có render kind ấy.

## 2. Công thức — không phụ thuộc hệ trục

Ký hiệu: `u` hướng trục (đáy→đỉnh), `n` pháp tuyến, `t = r²/h²`,
`ν² = (n·u)²/(u·u)`, `|m⃗|² = |n|² − ν²`, `K = ν² − t|m⃗|²`. Gọi `T` là giao
điểm trục × mặt phẳng và `q` tỉ lệ từ `T` tới đỉnh, `d² = q²h²ν²`:

```
b² = t·d² / K              a² = t·d²·|n|² / K²
```

Cả hai **hữu tỉ** ⇒ `S = π√(a²b²)` ở lại trong `Radical`.

⚠️ `z = mx + c` **chỉ là oracle**. Mã sản phẩm viết bằng tích vô hướng, và
`test_13`/`test_14` khoá tính bất biến với **tịnh tiến** và **hoán vị trục có
dấu**.

⚠️ **Không dùng điểm đỉnh.** Ở cách khai bằng vô hướng, đỉnh nón không phải một
điểm hữu tỉ khi `h = √7`. Công thức đi qua `_ti_le_doc_truc` — thẩm quyền đã
có, biết `|u|` là `h` hay `1`, và **từ chối có mã** đúng khi `h` vô tỉ.
`NEW_AUTHORITIES = 0` là thật vì lý do này.

## 3. Phân xử conic — một phép so hữu tỉ

```
L = (n·u)²(r² + h²)     R = r²(n·n)(u·u)
L > R → ellipse    L = R → parabola    L < R → hyperbola
```

`test_06` ghim rằng thân hàm không chứa `float(`, `sqrt`, `math.`, `** 0.5`.
`test_07` kiểm chéo bằng dấu của `k = 1 − m²tan²α` — **một đường dẫn khác
hẳn** — trên sáu độ dốc.

⚠️ Mặt phẳng **song song trục** cho `L = 0 < R` ⇒ hyperbol, và với nón điều đó
**đúng** — khác hẳn hình trụ, nơi cùng cấu hình cho một cặp đường sinh. Nhánh
nón vì thế không dùng lại phép loại trừ của nhánh trụ.

## 4. Chứa trong nón hữu hạn

```
q > 0                                        (không qua đỉnh, đúng nappe)
K − q·ν² ≥ 0   và   (K − q·ν²)² ≥ |m⃗|²·t·q²·ν²
```

Cả hai vế bình phương ⇒ **không cần biết `h` là số nào**, cùng kỹ thuật
`_con_cho_toi_day_tren` đã dùng cho hình trụ. Đẳng thức = **chạm đáy**, và nó
được **NHẬN** (`test_11`): chặn nó là chặn oan một hình hợp lệ.

Phía đỉnh không cần kiểm — với `K > 0` và `q > 0`, đại số cho thấy điều kiện
*"không vượt qua đỉnh"* tự thoả.

## 5. Ba oracle

| # | Đường | Kết quả |
|---|---|---|
| ① | hoàn thành bình phương, tay, hệ chính tắc | `144/25 × 10/9 = 32/5` · `b² = 27/5` |
| ② | coordinate-free (chính mã sản phẩm) | `a² = 32/5` · `b² = 27/5` |
| ③ | 20 000 mẫu trên giao tuyến + shoelace 3D | lệch `< 1e-4` |

Ca chạm đáy: `a² = 128/5`, `b² = 108/5`, `S = 48√6π/5`.

## 6. Chỗ khó thật — TÂM elip, và tôi dẫn sai lần đầu

Với hình trụ, tâm elip **là** giao điểm trục × mặt phẳng. Với nón thì **không**:
bán kính co dần dọc trục nên hai đầu trục lớn không cách đều điểm ấy.

Lần dẫn đầu tiên tôi ra `κ = t·q·uu·nu/(K·nn)`. Oracle số nói tâm ở `(0.6, 0,
3.2)`; kernel trả `(−92.16, 0, −27.72)` — **lệch 97.8**. Bán trục thì đã đúng
ngay từ đầu (`2a = 5.059644` cả hai bên), nên nếu chỉ kiểm diện tích thì lỗi
này **đi lọt hoàn toàn**.

Dẫn lại đúng:

```
C − T = (ξ_T·t/K)·(|n|²·û − ν·n)     và   |n|²u − (n·u)n  =  n × (u × n) = major_dir
⇒  C = T − (q·t·(h/√(u·u)) / K) · major_dir
```

`h/√(u·u)` là **1** ở point mode và **h** ở scalar mode — đúng cái thang mà
`_ti_le_doc_truc` sở hữu, nên lấy nó bằng `1/_ti_le_doc_truc(s, 1)` thay vì
viết một nhánh `if`. Đo lại: `κ = −1/40`, `C = (3/5, 0, 16/5)`, khớp oracle.

> Bài học ghi lại: **một phép kiểm diện tích không kiểm được vị trí.**
> `test_20` vì thế thay bằng phép mạnh hơn — bốn đầu mút trục phải thoả **cả
> hai** phương trình (mặt phẳng và mặt nón) và nằm trong `0 ≤ z ≤ 8`. Ô ấy
> kiểm `center`, hai `dir` và hai bán trục **cùng lúc**.

## 7. Ma trận biên — đo được, không suy

| Cấu hình | Phân xử | Kết quả |
|---|---|---|
| `x − 3z + 9 = 0` | ellipse | `ellipse3` · `32/5, 27/5` |
| `x − 3z + 18 = 0` (chạm đáy) | ellipse | `ellipse3` · `128/5, 108/5` |
| `x + 3z − 9 = 0` (xiên âm) | ellipse | `ellipse3` · `32/5, 27/5` |
| `4x − 3z + 12 = 0` | **parabola** | `CURVED_CONE_SECTION_PARABOLIC` |
| `2x − z + 3 = 0` | **hyperbola** | `CURVED_CONE_SECTION_HYPERBOLIC` |
| `x = 3` (∥ trục) | **hyperbola** | `CURVED_CONE_SECTION_HYPERBOLIC` |
| `x − 3z + 21 = 0` | ellipse | `CURVED_ELLIPSE_CROSSES_CAP` |
| `x − 3z − 9 = 0` (nappe đối) | ellipse | `CURVED_PLANE_DOES_NOT_CUT` |
| `x − 3z = 0` (qua đỉnh) | ellipse | `CURVED_PLANE_DOES_NOT_CUT` |
| `z = 3` (⊥ trục) | ellipse | `CURVED_ELLIPSE_OUTSIDE_V1_CLOSURE` → chỉ sang `intersect_plane_curved` |

Artifact: `docs/evaluation/geometry/oblique-cone-section-foundation/BOUNDARY_MATRIX.json`.

## 8. Gold đi trọn pipeline

```
GOLD_SERVABLE   = YES      stage = served      envelope = ok
EXACT_AREA      = 12π√6/5
WEAK_KINDS      = []       (checker `area` THẬT SỰ chạy)
SOURCE_INVARIANTS = 4 passed / 0 violated / 0 unresolved
TRACE_DEPENDENCY  non → {H,V,A} · E → {non, alpha} · dien_tich_E → {E}
SCENE3D_KIND      ellipse   (không nhánh renderer riêng cho nón)
```

Bốn bất biến nguồn đạt là ba **toạ độ điểm** (bộ phát của
`POINT_COORDINATE_SOURCE_INVARIANT`) cộng **phương trình mặt phẳng** — cả hai
bộ phát có sẵn tự nhận ca nón, không cần bộ phát mới.

## 9. Một hồi quy đã ĐỔI KHẲNG ĐỊNH, và nó bác điều tôi đoán

`test_12_truyen_HINH_NON_vao_duong_elip_bi_phan_loai_dung` khoá hành vi cũ:
nón bị từ chối bằng `OUTSIDE_V1_CLOSURE`, và ghim thêm
`code != ERR_ELIP_CAT_DAY`.

Viết lại ô ấy, tôi **đoán** ca đó là hyperbol. Đo ra là **ELIP**: nón
`r = 12, h = 18` có `tan α = 2/3`, và ngưỡng elip là `m < cot α = 3/2`,
**không** phải `m < tan α`. Mặt phẳng `z = x + 10` có `m = 1 < 3/2`.

Nó vẫn bị từ chối — nhưng bằng đúng cái mã mà bản cũ ghim là *"khác"*: ở `z = 0`
mặt phẳng cắt qua đĩa đáy, nên giao tuyến là cung elip ghép cung tròn ⇒
`ERR_ELIP_CAT_DAY`. Dòng `!= ERR_ELIP_CAT_DAY` của bản cũ hoá ra khẳng định một
điều **sai** về chính ca nó chọn.

`test_12b` thêm mặt kia của đồng xu: hạ độ dốc xuống dưới ngưỡng thì **chính
khối nón ấy** cho một elip đầy đủ — nếu ô ấy đỏ thì `test_12` đang gác rộng hơn
nó nên gác.

## 10. Tám phép tiêm

| # | Tiêm | Đo được |
|---|---|---|
| ① | khôi phục nhánh từ chối cone | gold đỏ, `OUTSIDE_V1_CLOSURE` |
| ② | đảo phân loại ellipse ↔ hyperbola | ca chuẩn đỏ `HYPERBOLIC` |
| ③ | biến parabol thành ellipse | bất biến chéo `K ≤ 0` bắt, `MALFORMED` |
| ④ | bỏ finite-cap check | `x − 3z + 21 = 0` lọt qua |
| ⑤ | dùng công thức bán trục của TRỤ | `b² = 36 ≠ 27/5` |
| ⑥ | bỏ `_ti_le_doc_truc` | scalar mode đỏ, `q = −4 < 0` |
| ⑦ | thẻ vẫn nói riêng "hình trụ" | parity thẻ ↔ năng lực đỏ |
| ⑧ | đảo một phương trục | diện tích và tâm giữ nguyên (elip là cùng một hình) |

## 11. Thẻ văn phạm và cache

Đúng **một** chuỗi đổi: `description` của trường `solid`, `"tên hình trụ"` →
`"tên hình trụ hoặc hình nón"` (**+18 byte**, `CARD_DELTA_CLASS =
CAPABILITY_SYNC`). Không thêm ví dụ, không thêm tên điểm, không thêm đáp số,
không thêm quy tắc giải.

⚠️ Chuỗi ấy là `description` của một trường Pydantic, nên nó nằm **đồng thời**
trong thẻ văn phạm và trong lược đồ gửi đi. **Một chuỗi, hai băm.**

```
CACHE_DECISION_AND_REASON  BUMP — đầu vào của mô hình đổi (thẻ + lược đồ)
CACHE_VERSION_BEFORE/AFTER 93 → 94
PROMPT_CHANGED             NO   55ac1ca6a6df92ce
GRAMMAR_CARD_CHANGED       YES  cc105e4f1da84d23 → 6cbba1885b2073fa
SYNTHESIS_SCHEMA_CHANGED   YES  6ccef3230c003d61 → 08dae8dc5a90bcae
ANALYZE_SCHEMA_CHANGED     NO   515001b503af5c7c
CAPABILITY_CHANGED         NO   72edf39f6c10220d
SEMANTIC_ENVIRONMENT       YES  a483ced9fd7546df → 12542444d2295c4d  (dẫn xuất)
CANDIDATE_HASH_BEFORE/AFTER 9bb796e9eb5e96a8 → 07a10a2c8b7b3a5e
```

⚠️ **Chiều envelope là `rejected → served` và CHỈ chiều ấy.** Nón cắt xiên
trước đây luôn chết ở `OUTSIDE_V1_CLOSURE`, tức chưa từng có envelope `ok` nào;
đường hình trụ không đổi một bit (`test_oblique_cylinder_ellipse` 30 pass). Nên
không envelope `ok` nào hoá sai — bump vì mô hình nay **đọc một câu khác** về
phép ấy.

Ba test ghim danh tính lượt đo live cũ được sửa theo cùng nguyên tắc đã dùng ở
hai wave trước, nhưng **chính xác hơn**: thay vì bỏ so, chúng nay khẳng định
`grammar_card`/`synthesis_schema` **phải khác** (vì wave này đổi chúng có chủ
đích) còn ba băm còn lại **phải khớp** — chúng là thứ nói rằng lượt đo không bị
một thay đổi prompt nào làm nhiễu.

## 12. Phạm vi — và điểm dừng mở rộng

```
oblique_cone_section: EXPRESSIBLE_ONLY → FOUNDATION_ONLY
MODEL_DISCOVERABLE = NOT_MEASURED   STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
PRODUCT_PROMOTION_ELIGIBLE = NO
```

Bao đóng v1 của họ này, nói thẳng: **nón hữu hạn**, mặt phẳng **xiên**, phân xử
hữu tỉ cho **ellipse**, elip nằm **trọn** giữa đỉnh và đáy (chạm đáy được nhận).
Scalar mode với `h` **vô tỉ** bị `_ti_le_doc_truc` từ chối — giới hạn CŨ, không
phải giới hạn mới.

```
FEATURE_SCOPE_COMPLETE = YES
solid_of_revolution_general = OUT_OF_SCOPE
composite_boolean           = OUT_OF_SCOPE
```

Hai họ ngoài phạm vi giữ nguyên lý do kiến trúc đã đo ở
`MISSING_FAMILY_ROADMAP_REFRESH`; wave này không đụng tới chúng.

## 13. Cổng

```
targeted        test_oblique_cone_section.py            48 pass
                test_oblique_cylinder_ellipse.py        30 pass
                test_curved_foundation · test_curved_section · registry  pass
                test_missing_family_roadmap.py          26 pass
pytest          4652 pass + 1 skip (cây sạch), 0 đỏ
vitest          52 file · 718 pass          (CHẠY THẬT — schema mirror đổi)
npm run build   ✔ tsc -b + vite build       (CHẠY THẬT)
replay_demo     5/5 · REDUCED_CHAIN 1/1
crash_surface   6/6 · ném ra ngoài 0
certify         RUNNER_CERTIFICATION PASS · APPLICATION_LLM_CALLS 0
cache identity  lock sinh lại @ v94
freeze --verify exit 0 sau commit đóng băng lại
git diff --check sạch
```

`RECOMMENDED_NEXT_ACTION = THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION`
