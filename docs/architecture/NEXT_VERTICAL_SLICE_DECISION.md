# QUYẾT ĐỊNH CHỌN LÁT CẮT DỌC KIẾN TRÚC TIẾP THEO
## NEXT VERTICAL SLICE DECISION REPORT

> **Mục tiêu:** Lựa chọn đúng một họ bài toán / lát cắt dọc kiến trúc tiếp theo cho AlgoSim Geometry Compiler, bảo đảm tính tổng quát, tối đa hoá tái sử dụng, giữ nguyên tính chính xác của kernel và không đòi hỏi redesign giao diện.  
> *Nguyên tắc bằng chứng:* Mô tả có giới hạn, tránh xác quyết không có đo lường máy hoặc trích dẫn văn bản chính thức.

---

## 1. So Sánh Đánh Giá Các Ứng Viên Kiến Trúc

| Ứng viên (Candidate Family) | Tái sử dụng Primitive | Tính chính xác $\mathbb{Q}^3$ (Không căn ở toạ độ) | Phạm vi chương trình THPT | Rủi ro kiến trúc / Độ phức tạp | Redesign Frontend |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Rectangular Cuboid & Cube (Hình hộp chữ nhật & Hình lập phương)** | **RẤT CAO** (Tái sử dụng `construct_prism`) | **TUYỆT ĐỐI** (Đỉnh hữu tỉ 100%) | **CAO** (Họ bài quen thuộc trong chương trình) | **THẤP** (Đáy chữ nhật đã giải quyết) | **KHÔNG** |
| **2. Regular Pyramid (Chóp đều - tam giác / tứ giác)** | TRUNG BÌNH | **KÉM** (Chóp tam giác đều có toạ độ $\sqrt{3}$) | CAO | **CAO** (Cần RadicalVec3 hoặc tính tâm đáy $O$) | KHÔNG |
| **3. Regular Tetrahedron (Tứ diện đều)** | THẤP | **RẤT KÉM** (Toạ độ 4 đỉnh chứa $\sqrt{2}, \sqrt{3}$) | TRUNG BÌNH | **RẤT CAO** (Phá vỡ tính hữu tỉ của `Vec3`) | KHÔNG |
| **4. Oblique Prism (Lăng trụ xiên)** | THẤP | KHÁ (Nếu vector xiên hữu tỉ) | THẤP | **CAO** (Cần quan hệ góc nghiêng / toạ độ xiên) | KHÔNG |
| **5. Plane Section (Thiết diện đa diện tất định)** | TRUNG BÌNH | TỐT (Kernel đã có `cross_section`) | CAO | **RẤT CAO** (Khó giải tất định quan hệ cắt từ đề chữ) | KHÔNG |
| **6. Triangular Prism Variants (Lăng trụ tam giác đều/xiên)** | TRUNG BÌNH | KÉM (Tam giác đều có $\sqrt{3}$) | CAO | **CAO** (Toạ độ đỉnh rơi khỏi $\mathbb{Q}^3$) | KHÔNG |

---

## 2. Kết Luận Quyết Định

### `NEXT_FAMILY_RECOMMENDED: rectangular_cuboid_and_cube_volume`
**(Họ bài toán tính thể tích hình hộp chữ nhật và hình lập phương)**

---

## 3. Lý Do Lựa Chọn (Rationale)

1. **Bảo tồn tính toán học chính xác trên $\mathbb{Q}^3$:**
   - Trong hình hộp chữ nhật có kích thước $a, b, c \in \mathbb{Q}$, toạ độ của cả 8 đỉnh:
     $$A(0,0,0), B(a,0,0), C(a,b,0), D(0,b,0)$$
     $$A'(0,0,c), B'(a,0,c), C'(a,b,c), D'(0,b,c)$$
     đều là các số hữu tỉ thuần tuý. Kernel không cần mở rộng sang `RadicalVec3`, bảo toàn bất biến số học cốt lõi của đề tài.
2. **Tái sử dụng tối đa năng lực vừa hoàn thành ở Wave Rectangular Pyramid:**
   - Cấu trúc đáy chữ nhật/vuông ($ABCD$), phân loại variant (`rectangle` vs `square`), quan hệ vuông góc giữa các cạnh bên và mặt đáy đã được giải quyết trọn vẹn trong `RangBuocRectPyramid`.
   - Compiler primitive `construct_prism` trong `primitives.py` vốn đã được thiết kế tổng quát cho chu trình đáy $n$ đỉnh ($n \ge 3$), nhận trực tiếp $n = 4$.
3. **Phù hợp chương trình giáo dục phổ thông:**
   - Họ bài quen thuộc trong chương trình Hình học 12, có ground truth rõ ràng và cấu trúc dữ kiện chặt chẽ.
4. **Ứng viên có tính tái sử dụng cao trong phạm vi repository đã kiểm kê:**
   - Mở rộng tự nhiên từ lăng trụ tam giác sang lăng trụ tứ giác trực giao, tạo nền móng vững chắc trước khi mở rộng sang các bài toán hình học tổ hợp đa khối.
5. **Không đòi hỏi redesign Frontend:**
   - Renderer Three.js đã có sẵn các primitive cần thiết (`mesh`, `segment`, `point_marker`, `polygon`). Lưu ý: `cuboid browser evidence` chưa được thiết lập và sẽ là nghĩa vụ kiểm chứng trong wave triển khai.

---

## 4. Nguyên Tắc Triển Khai Kiến Trúc

1. **Cuboid là Specialization của Prism, không phải hệ hình học tách biệt:**
   - Tránh tạo ra một primitive mới không cần thiết (`construct_cuboid` không phải primitive lõi bắt buộc).
   - **Phương án ưu tiên:**
     $$\text{construct\_prism} + \text{base rectangle/square constraints} + \text{lateral edges perpendicular to base} + \text{exact lengths}$$
2. **Semantic Constraints xác định hình:**
   - Ràng buộc đáy chữ nhật/vuông và chiều cao đến từ các quan hệ cấu trúc có kiểu (`perpendicular_line_plane`, `perpendicular_lines`).
3. **Chuẩn bị cho Multi-object SceneGraph:**
   - Mọi thực thể và quan hệ trong lát cắt này phải tuân thủ ID đối tượng ổn định để dễ dàng mở rộng sang mô hình đa khối ở các wave sau.
4. **Không hardcode renderer theo họ bài:**
   - Renderer tiếp tục chỉ đọc `render_hint` và toạ độ, không nhận diện case ID hay tên họ hình.

---

## 5. Lộ Trình Kiến Trúc Đề Xuất (Architecture Roadmap)

### WAVE 1: `rectangular_cuboid_and_cube_volume`
- **Mục tiêu:** Hoàn thiện họ hình hộp chữ nhật và hình lập phương như một specialization của lăng trụ đứng tứ giác.
- **Phạm vi kỹ thuật:**
  - Tái sử dụng `construct_prism` với $n=4$.
  - Toạ độ hữu tỉ chính xác trong $\mathbb{Q}^3$.
  - Compiler rule `RangBuocCuboid` trong `compiler.py`.
  - Từ chối fail-closed cho dữ kiện thiếu/mâu thuẫn.
  - Trace sư phạm 8 đỉnh, 12 cạnh, nhãn thể tích $V(ABCD.A'B'C'D')$.
  - Thiết lập bộ bằng chứng Playwright browser replay và contact sheet tối thiểu cho cuboid/cube.

### WAVE 2: `multi_object_contract_and_relation_foundation`
- **Mục tiêu:** Mở rộng kiến trúc từ đơn khối (`SINGLE_SOLID_ONLY`) sang hỗ trợ đa khối và quan hệ xuyên khối.
- **Phạm vi kỹ thuật:**
  - `Object Registry` quản lý định danh thực thể toàn cục ổn định.
  - Mở rộng `RequestContract` với `solid_topologies: list[TopologySpec]` (hoặc SceneGraph) thay cho trường đơn `solid_topology`.
  - Thêm `SphereTopologySpec` vào hợp đồng.
  - Mở rộng `RELATION_KINDS` với các quan hệ xuyên khối (`inscribed_in`, `circumscribed_about`, `tangent`, `concentric`).
  - Truy vết xuất xứ và bao đóng phụ thuộc (provenance closure) xuyên đối tượng trong FactGraph.

### WAVE 3: `sphere_primitive_and_first_composite_slice`
- **Mục tiêu:** Lát cắt dọc hình học tổ hợp đầu tiên: Hình chóp tam giác vuông nội tiếp mặt cầu ngoại tiếp.
- **Phạm vi kỹ thuật:**
  - Đỉnh chóp $S, A, B, C$ nằm trên mặt cầu tâm $I$, bán kính $R$.
  - Tính toán bán kính chính xác bằng exact geometry kernel.
  - Scene3D điều phối hiển thị đồng thời khối đa diện mờ bên trong mặt cầu bán trong suốt (xử lý depth write, tránh z-fighting).
  - Trace sư phạm thể hiện mối liên hệ giữa tâm/bán kính mặt cầu và hình chóp nội tiếp.

---

## 6. Kế Hoạch Ca Kiểm Thử Cho Wave 1 (Cuboid / Cube)

1. **Ca Dương (Positive Ground Truth):**
   - `CUBOID_01`: Hình hộp chữ nhật $ABCD.A'B'C'D'$ có $AB=3, AD=4, AA'=5$. Kỳ vọng $V = 60$.
   - `CUBE_01`: Hình lập phương $ABCD.A'B'C'D'$ cạnh $a=4$. Kỳ vọng $V = 64$.
   - `CUBOID_SQUARE_BASE`: Hình hộp có đáy là hình vuông cạnh 3, chiều cao 7. Kỳ vọng $V = 63$.
2. **Ca Âm / Từ Chối Fail-Closed (Negative Ground Truth):**
   - `CUBOID_NEG_NON_POSITIVE`: Kích thước cạnh $\le 0$ $\rightarrow$ `INVALID_NON_POSITIVE_LENGTH`.
   - `CUBOID_NEG_CONFLICT`: Đoạn $AB$ vừa khai bằng 3 vừa khai bằng 5 $\rightarrow$ `INVALID_CONFLICT`.
   - `CUBOID_NEG_MISSING_HEIGHT`: Cho đáy chữ nhật nhưng thiếu thông tin chiều cao $\rightarrow$ `UNSUPPORTED_MISSING_FACT`.

---

## 7. Cổng Nghiệm Thu Wave 1 (Acceptance Gates)

1. `GATE_1`: `PrismTopologySpec` hỗ trợ `base_shape` chuẩn hoá.
2. `GATE_2`: `GeometryFactGraph` và `compiler.py` phân xử thành công `RangBuocCuboid` cho cả `cuboid` và `cube`.
3. `GATE_3`: 100% test compiler và contract adapter vượt qua (exit 0).
4. `GATE_4`: Sinh trace sư phạm 8 đỉnh, 12 cạnh, nhãn thể tích $V(ABCD.A'B'C'D')$.
5. `GATE_5`: Không có toạ độ vô tỉ; `freeze_evaluation_candidate.py --verify` và `lock_cache_identity.py --verify` đều PASS.
6. `GATE_6`: Bộ test Playwright visual replay tạo contact sheet độc lập xác nhận hiển thị trực quan 3D không suy biến.
