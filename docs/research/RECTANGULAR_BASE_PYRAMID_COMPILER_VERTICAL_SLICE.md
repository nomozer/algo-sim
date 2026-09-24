# Báo Cáo Kỹ Thuật: Vertical Slice Trình Biên Dịch Khối Chóp Đáy Hình Chữ Nhật / Hình Vuông

> **Mã nhiệm vụ:** `RECTANGULAR_BASE_PYRAMID_COMPILER_VERTICAL_SLICE`  
> **Nhánh thực hiện:** `feat/rectangular-base-pyramid-compiler`  
> **Họ hình học hỗ trợ:** `rectangular_base_pyramid_volume`  
> **Trạng thái:** HOÀN THÀNH (Đạt toàn bộ kiểm thử dương tính, kiểm thử âm tính fail-closed và hồi quy hệ thống).

---

## 1. Mục Tiêu và Phạm Vi (Scope Boundary)

Mục tiêu của nhiệm vụ là mở rộng kiến trúc tất định (deterministic compiler) hiện tại của AlgoSim để hỗ trợ chu trình đầu-cuối (end-to-end) cho họ bài toán tính thể tích khối chóp đáy hình chữ nhật và hình vuông:

$$\text{RequestContract} \longrightarrow \text{GeometryFactGraph} \longrightarrow \text{Eligibility} \longrightarrow \text{Canonical Layout} \longrightarrow \text{construct\_pyramid} \longrightarrow \text{SemanticProgramSpec} \longrightarrow \text{Interpreter/Kernel} \longrightarrow \text{Scene3D} \longrightarrow \text{Đáp số thể tích chính xác}$$

### Ranh giới họ bài toán (`SUPPORTED_FAMILY_RECT_PYRAMID`)

Họ hình học được định nghĩa chính thức là:
`rectangular_base_pyramid_volume`

Gồm hai biến thể được hỗ trợ:
1. **Biến thể hình chữ nhật (`variant = "rectangle"`):**
   - Đáy $ABCD$ là hình chữ nhật;
   - Cạnh đáy liền kề $AB = a$ và $AD = b$;
   - Cạnh bên $SA$ vuông góc với mặt phẳng đáy $(ABCD)$, chiều cao $SA = h$;
   - Yêu cầu tính thể tích khối chóp $S.ABCD$.
2. **Biến thể hình vuông (`variant = "square"`):**
   - Đáy $ABCD$ là hình vuông;
   - Cạnh đáy $AB = a$ (hoặc $b = a$);
   - Cạnh bên $SA$ vuông góc với mặt phẳng đáy $(ABCD)$, chiều cao $SA = h$;
   - Yêu cầu tính thể tích khối chóp $S.ABCD$.

### Giới hạn kỹ thuật nghiêm ngặt (Limitations)
- **Chân đường cao cố định tại đỉnh đáy $A$:** Compiler hiện tại chuyên biệt hóa cho cấu hình chóp đứng có cạnh bên vuông góc đáy tại một đỉnh đáy ($SA \perp (ABCD)$).
- **Không hỗ trợ chóp tứ giác tổng quát:** Không hỗ trợ đáy hình thang, hình bình hành, hình thoi hoặc tứ giác bất kỳ trong wave này.
- **Không hỗ trợ chóp đều $S.ABCD$ (chân đường cao tại tâm đáy $O$):** Khối chóp tứ giác đều là một family độc lập, không gộp chung vào họ này.
- **Không suy đoán dữ kiện:** Mọi thông tin về quan hệ vuông góc và độ dài phải được cung cấp đầy đủ và nhất quán từ hợp đồng; nếu thiếu bất kỳ dữ kiện nào, hệ thống từ chối an toàn (fail-closed).

---

## 2. Bố Cục Chuẩn Tắc (Canonical Layout)

Hệ tọa độ Decartes được chọn chuẩn tắc để đảm bảo tính tất định, triệt tiêu sai số dấu và phép quay:

- Mặt phẳng đáy $(ABCD)$ đặt trên mặt phẳng $Oxy$ ($z = 0$):
  - Đỉnh $A = (0, 0, 0)$ (chân đường cao);
  - Đỉnh $B = (a, 0, 0)$ (nằm trên trục hoành dương $Ox$);
  - Đỉnh $D = (0, b, 0)$ (nằm trên trục tung dương $Oy$);
  - Đỉnh $C = (a, b, 0)$ (đối diện với $A$).
- Đỉnh chóp $S$:
  - $S = (0, 0, h)$ (nằm trên trục cao dương $Oz$).
- Đối với biến thể hình vuông: $b = a$.

Toàn bộ 5 điểm được khai báo vào `memory_declarations` của `SemanticProgram` với kiểu `point3` và xuất xứ tường minh `provenance = "LAYOUT_DERIVED"`.

---

## 3. Công Thức Tính Thể Tích Chính Xác (Exact Volume Computation)

Thể tích được sinh bằng biểu diễn AST ngữ nghĩa số học tất định, không làm tròn số thực:

- Biến thể hình chữ nhật:
  $$V = \frac{1}{3} \cdot S_{ABCD} \cdot SA = \frac{a \cdot b \cdot h}{3}$$
- Biến thể hình vuông:
  $$V = \frac{1}{3} \cdot a^2 \cdot h = \frac{a^2 \cdot h}{3}$$

Trong chương trình ngữ nghĩa, phép tính được sinh tuần tự qua các phép toán số học chính xác trên trường số hữu tỉ:
1. `s_day = mul(len_ab, len_ad)` (hoặc `len_ab * len_ab`)
2. `tich = mul(s_day, len_sa)`
3. `v = div(tich, 3)`
4. Gán biến nhân chứng (witness) và sinh readout hiển thị trong Scene3D.

---

## 4. Tái Sử Dụng Primitive Khối Chóp (`construct_pyramid`)

Kiểm toán kiến trúc tại Phase 1 cho thấy primitive `construct_pyramid` trong `backend/app/simulation/geometry/primitives.py` đã được thiết kế tổng quát nhận một chu trình đáy tùy ý (`base_cycle: list[Point3D]`) và một đỉnh (`apex: Point3D`). 

Vì vậy, **không cần tạo thêm primitive mới**. Trình biên dịch tạo đa diện gồm:
- $V = 5$ đỉnh: $[A, B, C, D, S]$;
- $E = 8$ cạnh: 4 cạnh đáy $[AB, BC, CD, DA]$ và 4 cạnh bên $[SA, SB, SC, SD]$;
- $F = 5$ mặt: 1 mặt đáy $[A, B, C, D]$ và 4 mặt bên tam giác $[SAB, SBC, SCD, SDA]$;
- Đặc trưng Euler: $\chi = V - E + F = 5 - 8 + 5 = 2$ (mặt cầu tô-pô lồi đóng chuẩn).

---

## 5. Kết Quả Kiểm Thử Chấp Nhận (Acceptance Tests)

Tất cả kiểm thử được triển khai tại:
- `backend/tests/geometry/test_rectangular_pyramid_compiler.py` (11 ca unit và tích hợp)
- `backend/tests/geometry/test_rectangular_pyramid_production_route.py` (2 ca pipeline và định tuyến)

### 5.1. Ca dương bắt buộc

| Ca kiểm thử | Biến thể | Dữ kiện đầu vào | Thể tích kỳ vọng | Thể tích thực tế | Số đỉnh | Số cạnh | Số mặt | Euler | Kết quả |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Case A** | Hình chữ nhật | $AB=3, AD=4, SA=6$ | $24$ | `Fraction(24)` | 5 | 8 | 5 | 2 | **PASSED** |
| **Case B** | Hình vuông | $AB=3, SA=6$ | $18$ | `Fraction(18)` | 5 | 8 | 5 | 2 | **PASSED** |

Các thuộc tính kiểm chứng thêm:
- Toàn bộ 5 điểm có `provenance = "LAYOUT_DERIVED"`.
- `Scene3D` sinh thành công với 1 đối tượng `solid` và 5 đối tượng `point3`.
- Deterministic replay không kích hoạt bất kỳ Gemini request nào (`LLM_REQUESTS = 0`).

### 5.2. Ca âm bắt buộc (Fail-Closed)

| STT | Tình huống âm tính | Tầng phát hiện | Mã trạng thái | Mã lý do lỗi | Kết quả |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Thiếu chiều cao $SA$ | Eligibility | `UNSUPPORTED_MISSING_FACT` | `REQUIRED_FACT_MISSING` (`REQUIRED_LENGTH_MISSING: SA`) | **PASSED** |
| 2 | Hình chữ nhật thiếu cạnh đáy $AD$ | Eligibility | `UNSUPPORTED_MISSING_FACT` | `REQUIRED_FACT_MISSING` (`REQUIRED_LENGTH_MISSING: AD`) | **PASSED** |
| 3 | Mâu thuẫn độ dài cạnh đáy ($AB=3, CD=5$) | FactGraph / Eligibility | `INVALID_CONFLICT` | `RECTANGLE_OPPOSITE_EDGES_UNEQUAL` | **PASSED** |
| 4 | Đáy không phải chữ nhật / thiếu góc vuông đáy | Eligibility | `UNSUPPORTED_STRUCTURED_RELATION_MISSING` | `BASE_NOT_RECTANGLE` | **PASSED** |
| 5 | Cạnh bên $SA$ không vuông góc đáy $(ABCD)$ | Eligibility | `UNSUPPORTED_STRUCTURED_RELATION_MISSING` | `LINE_PLANE_RELATION_MISSING` | **PASSED** |
| 6a | Chu trình đáy có đỉnh trùng lặp ($A, B, C, B$) | Eligibility | `INVALID_CONFLICT` | `DUPLICATE_VERTICES` | **PASSED** |
| 6b | Chu trình đáy không đủ 4 đỉnh (tam giác) | Eligibility | `UNSUPPORTED_MISSING_FACT` | `BASE_NOT_QUADRILATERAL` | **PASSED** |
| 7 | Nghĩa vụ bổ sung chưa hỗ trợ (cosin góc) | Eligibility | `UNSUPPORTED_EXTRA_OBLIGATION` | `EXTRA_OBLIGATION_UNSUPPORTED` | **PASSED** |

---

## 6. Hồi Quy Hệ Thống và Bất Biến Kiến Trúc (Invariants & Regression)

- **Họ hình học hiện có:** Toàn bộ 85 bài kiểm thử hồi quy cho `right_triangle_base_pyramid_volume` và `right_triangle_base_right_prism_volume` đều vượt qua 100%.
- **Chế độ mặc định:** `DEFAULT_MODE = LLM_ONLY` được giữ nguyên tuyệt đối trong mã sản phẩm. Compiler tất định chỉ kích hoạt khi có cờ `GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST`.
- **Bảo mật con dấu và lược đồ:** Schema transport gửi Gemini không bị thay đổi, giữ nguyên con dấu kiểm thử và tính tương thích ngược.
- **Tài nguyên người dùng:** File `frontend/public/favicon.svg` bị xóa ở working tree được bảo toàn hoàn toàn, không bị stage hay phục hồi.
