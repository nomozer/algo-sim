# MISSING_FAMILY_ROADMAP_REFRESH

> 2026-09-08 · `APPLICATION_LLM_CALLS = 0` · wave **lập bản đồ và chọn hướng**
>
> ```
> ROADMAP_REFRESH = PASS
>
> SUPPORTED              point_line_vector_plane · polygon_and_planar_section
>                        convex_polyhedron
> DEVELOPMENT_CONFIRMED  nonconvex_polyhedron · oblique_cylinder_ellipse
> FOUNDATION_ONLY        ball · cylinder · cone · curved_circular_section
> EXPRESSIBLE_ONLY       oblique_cone_section
> OUT_OF_SCOPE           solid_of_revolution_general · composite_boolean
> UNSUPPORTED            (rỗng)
>
> SELECTED_NEXT_FAMILY = oblique_cone_section
> NEXT_ACTION          = OBLIQUE_CONE_SECTION_FOUNDATION
> FEATURE_SCOPE_COMPLETE = NO   (đúng MỘT họ còn lại; sau nó thì YES)
>
> PRODUCT_CODE_CHANGED = NO · CACHE_VERSION 93 → 93 · candidate không đổi
> ```
>
> Kết luận đắt nhất của wave: ghi chú registry *"nón cắt xiên … ba nhánh chưa
> phân xử"* mô tả **việc chưa làm**, và tôi đã đọc nó suốt hai wave như thể nó
> mô tả một **khoảng trống miền số**. Đo lại thì hai câu ấy khác nhau.

## 1. Ma trận — thẩm quyền là MÃ NGUỒN, không phải tài liệu

Bản đồ đầy đủ mười hai họ, mười một cột mỗi hàng:
`docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json`

Nó **kiểm được bằng máy**: `tests/geometry/test_missing_family_roadmap.py`
(26 ca) đối chiếu từng khẳng định với registry và mã đang chạy — **cả hai
chiều**:

* thứ ma trận nói **đã sẵn sàng** phải có mặt;
* thứ ma trận nói **chưa có** phải thật sự vắng.

Chiều thứ hai quan trọng hơn, vì đó mới là chỗ một bản đồ cũ nói dối, và nó
nói dối theo hướng làm người đọc **bỏ lỡ việc dễ** — đúng như
`curved_oblique_section` từng bị khai `unsupported` với lý do *"không có kiểu
conic trong IR"*, một câu **sai**.

Bốn phép tiêm chứng minh guard có răng: `TONG_KET` gõ lệch → đỏ · khai
`STABILITY` khác `NOT_MEASURED` → đỏ · đảo dấu phép phân xử conic → đỏ · và
phép quét "vắng mặt" đọc thật **45** file `.py` (không rỗng vô nghĩa).

## 2. Ứng viên A — thiết diện xiên của hình nón

### Điều đã bị bác

Registry ghi: *"nón cắt xiên cho elip, parabol hoặc hyperbol tuỳ độ dốc — ba
nhánh chưa phân xử"*. Câu ấy **đúng về công việc** và **im lặng về miền số**;
tôi đã đọc nó như thể nó nói cả hai.

### Phép đo

Nón đỉnh gốc, trục `Oz`, `t = tan²α = r²/h²`; mặt phẳng `z = m·x + c`;
`k = 1 − m²t`:

```
b² = c²·t / k                 a² = c²·t·(1 + m²) / k²
```

`t`, `m`, `c` hữu tỉ ⇒ **`a²` và `b²` hữu tỉ** ⇒ diện tích `π√(a²b²)` là đúng
dạng `Radical(he·√can·π^mu)` mà kernel đã có. Bốn ca, mỗi ca đối chiếu một
**oracle số độc lập** (lấy mẫu 400 000 điểm trên giao tuyến rồi shoelace 3D):

| `m` | `c` | `a²` | `b²` | công thức | oracle số | lệch |
|---|---|---|---|---|---|---|
| 1/4 | 4 | 626688/61009 | 2304/247 | 30.751859 | 30.751859 | 1.3e−09 |
| 1/2 | 6 | 20736/605 | 1296/55 | 89.280340 | 89.280340 | 4.6e−09 |
| 0 | 4 | 9 | 9 | 28.274334 | 28.274334 | 1.0e−09 |
| −1/3 | 5 | 160/9 | 15 | 51.301993 | 51.301993 | 2.3e−09 |

**Phân xử ba nhánh là một phép so HỮU TỈ**, không cần khai căn:

```
ellipse  ⇔ (n·u)²(r² + h²)  >  r²|n|²|u|²
parabol  ⇔ bằng
hyperbol ⇔ nhỏ hơn
```

Kiểm chéo bằng dấu của `k` — một đường dẫn khác hẳn — khớp cả năm ca thử.

### Khoảng trống, theo từng tầng

```
NEW_MEMORY_TYPES_REQUIRED        0    ellipse3 đã có
NEW_IR_OPERATIONS_REQUIRED       0    intersect_plane_curved_ellipse đã có chữ ký
NUMBER_DOMAIN_GAP                0    đo ở trên
KERNEL_GAP                       1 nhánh: phân xử conic + hai bán trục + chứa trong khối
STATIC_TYPE_GAP                  0    kết quả vẫn ellipse3
GROUNDING_OR_SOURCE_INVARIANT_GAP 0   dùng lại plane_equation + point_coordinate
CHECKER_GAP                      0    check_area DẪN kiểu từ BANG_PHEP_DO
TRACE_GAP                        0
SCENE3D_GAP                      0    render kind `ellipse` có ở CẢ HAI đầu
MODEL_FACING_GAP                 1 chuỗi gợi ý: `solid:tên<curved_solid>[hình trụ]`
CACHE_IMPACT                     bump MỘT lần; chiều rejected → served, không có chiều ngược
```

Chỗ duy nhất cần cân nhắc kỹ: phép kiểm *"elip nằm trọn giữa đỉnh và đáy"* khi
`r` vô tỉ. Kỹ thuật đã có sẵn — nhánh hình trụ so **bình phương ở cả hai đầu**
(`h_half²`) chính vì lý do ấy.

## 3. Ứng viên B — khối tròn xoay tổng quát

`OUT_OF_SCOPE`, và lý do là **kiến trúc**, không phải *"chưa ai làm"*:

* `grep sympy|def tich_phan|def integrate` trong `backend/app/simulation` →
  **0 kết quả** (quét 45 file);
* `MemoryType` **không có** kiểu biểu thức hàm nào (`function`/`expression`/
  `curve` đều vắng);
* `Radical` **không đóng** dưới tích phân tổng quát;
* renderer cần một `RENDER_KIND` mặt tròn xoay mới.

⚠️ Ba khối tròn xoay **phổ thông nhất — cầu, trụ, nón — đã có** và nằm ở ba
hàng riêng. Thứ còn thiếu là trường hợp **tổng quát**, và nó là cả một hệ con.

## 4. Ứng viên C — khối ghép · cắt · bù

`OUT_OF_SCOPE`, và lý do mạnh hơn *"chưa có thẩm quyền boolean"*: nó cần đúng
điều kiện mà hệ **đã khai là không kiểm được**.

`kiem_mat_phang_don` soát từng mặt phẳng và đơn; điều kiện *"hai MẶT KHÁC NHAU
xuyên qua nhau"* là **toàn cục** và nằm ngoài bao đóng v1
(`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`). Biên CSG sinh ra đúng tình huống
ấy thường xuyên.

⚠️ **Lối tắt "tổng đại số các thể tích" là một cái bẫy**: nó cho **đáp số**
đúng mà **hình** sai — hệ đọc to một con số cho một khối nó không dựng ra. Đó
là đúng lớp lỗi mà `NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` vừa đóng (`28` vs
`20`), nên đi lối tắt ở đây là mở lại nó.

## 5. So bảy tiêu chí

| Tiêu chí | A · nón xiên | B · tròn xoay | C · boolean |
|---|:---:|:---:|:---:|
| ① giá trị với bài phổ thông | **HIGH** — thiết diện conic có trong chương trình | MEDIUM | LOW |
| ② tái dùng IR/kernel | **HIGH** — 0 phép mới, 0 kiểu mới | LOW | LOW |
| ③ giữ tính toán chính xác | **HIGH** — đo ở §2 | LOW | MEDIUM |
| ④ dựng Scene3D đúng | **HIGH** — `ellipse` có sẵn hai đầu | LOW | LOW |
| ⑤ authority mới cần thêm | **0** | ≥ 2 | ≥ 1 lớn |
| ⑥ blast radius | **LOW** — một nhánh kernel + một chuỗi thẻ | HIGH | HIGH |
| ⑦ chi phí kiểm thử | **LOW** — foundation cần `0` lượt gọi model | HIGH | HIGH |

## 6. Quyết định

```
NEXT_FOUNDATION_FAMILY = oblique_cone_section
NEXT_ACTION            = OBLIQUE_CONE_SECTION_FOUNDATION
FEATURE_SCOPE_COMPLETE = NO
```

**Phạm vi nhỏ nhất chứng minh được** cho wave kế tiếp:

> Thiết diện của **hình nón tròn xoay hữu hạn** cắt bởi một mặt phẳng **xiên**,
> **khi và chỉ khi** phép phân xử hữu tỉ cho `ellipse` **và** elip nằm trọn
> giữa đỉnh và đáy. Hai nhánh `parabol`/`hyperbol` **fail-closed** bằng hai mã
> ổn định riêng, không đoán.

```
EXPECTED_NEW_MEMORY_TYPES           = 0
EXPECTED_NEW_IR_OPERATIONS          = 0
EXPECTED_PRODUCT_SURFACE            = 1 chuỗi gợi ý trong thẻ văn phạm
EXPECTED_MODEL_CALLS_FOR_FOUNDATION = 0
```

⚠️ **Sau họ này, mọi họ còn lại đều `OUT_OF_SCOPE`.** Nên next action kế tiếp
đã xác định trước: `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION`. Wave này
**không** chọn nó ngay, vì một họ có khoảng trống bằng **một nhánh kernel** và
**không** thêm authority nào thì tỉ lệ giá trị/chi phí còn rõ ràng thuận.

## 7. Điều wave này KHÔNG làm

Ma trận chia họ **mịn hơn** registry sản phẩm (registry gom `cone` với thiết
diện xiên của nó). Nó **không nâng** registry: `nonconvex_polyhedron` và
`oblique_cylinder_ellipse` đạt `DEVELOPMENT_CONFIRMED` ở ma trận, còn năng lực
**sản phẩm** vẫn `foundation_only`. Hai câu khác nhau — `product_capability.py`
vẫn là thẩm quyền của câu thứ hai, và `test_19` khoá rằng chúng không nói
ngược nhau.

Không họ nào được khai `STABILITY_UNDER_ACCEPTANCE` khác `NOT_MEASURED`
(`test_05`): chưa lượt acceptance nào chạy.

## 8. Danh tính và cổng

```
CACHE_VERSION_BEFORE/AFTER    93 → 93
CANDIDATE_HASH_BEFORE/AFTER   9bb796e9eb5e96a8 → 9bb796e9eb5e96a8
MODEL_FACING_HASHES_CHANGED   NO (cả sáu)
PRODUCT_CODE_CHANGED          NO  (git diff -- backend/app frontend/src rỗng)
PRODUCT_CAPABILITY_CHANGED    NO

test_missing_family_roadmap   26 pass
test_curved_foundation · test_oblique_cylinder_ellipse ·
  test_scope_gate_quantity_obligation_clues (registry)        pass
pytest (đủ, vì có thêm TEST bytes)   4605 pass + 1 skip, 0 đỏ
cache identity                15 pass @ v93
freeze --verify               exit 0
git diff --check              sạch
FRONTEND_RESULT = INHERITED · BUILD_RESULT = INHERITED  @ 3667713
FRONTEND_TRACKED_BYTES_CHANGED = NO
```
