# QUYẾT ĐỊNH CHỌN LÁT CẮT DỌC KIẾN TRÚC TIẾP THEO
## NEXT VERTICAL SLICE DECISION REPORT

> **Mục tiêu:** Lựa chọn đúng một họ bài toán / lát cắt dọc kiến trúc tiếp theo cho AlgoSim Geometry Compiler, bảo đảm tính tổng quát, tối đa hoá tái sử dụng, giữ nguyên tính chính xác của kernel và không đòi hỏi redesign giao diện.

---

## 1. So Sánh Đánh Giá Các Ứng Viên Kiến Trúc

| Ứng viên (Candidate Family) | Tái sử dụng Primitive | Tính chính xác $\mathbb{Q}^3$ (Không căn ở toạ độ) | Phạm vi đề thi THPT | Rủi ro kiến trúc / Độ phức tạp | Redesign Frontend |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Rectangular Cuboid & Cube (Hình hộp chữ nhật & Hình lập phương)** | **RẤT CAO** (90%) | **TUYỆT ĐỐI** (Đỉnh hữu tỉ 100%) | **RẤT CAO** (~40% câu hỏi khối đa diện) | **THẤP** (Đáy chữ nhật đã xong) | **KHÔNG** |
| **2. Regular Pyramid (Chóp đều - tam giác / tứ giác)** | TRUNG BÌNH (50%) | **KÉM** (Chóp tam giác đều có toạ độ $\sqrt{3}$) | CAO | **CAO** (Cần RadicalVec3 hoặc tính tâm đáy $O$) | KHÔNG |
| **3. Regular Tetrahedron (Tứ diện đều)** | THẤP (30%) | **RẤT KÉM** (Toạ độ 4 đỉnh chứa $\sqrt{2}, \sqrt{3}$) | TRUNG BÌNH | **RẤT CAO** (Phá vỡ tính hữu tỉ của `Vec3`) | KHÔNG |
| **4. Oblique Prism (Lăng trụ xiên)** | THẤP (30%) | KHÁ (Nếu vector xiên hữu tỉ) | THẤP | **CAO** (Cần quan hệ góc nghiêng / toạ độ xiên) | KHÔNG |
| **5. Plane Section (Thiết diện đa diện tất định)** | TRUNG BÌNH (40%) | TỐT (Kernel đã có `cross_section`) | RẤT CAO | **RẤT CAO** (Khó giải tất định quan hệ cắt từ đề chữ) | KHÔNG |
| **6. Triangular Prism Variants (Lăng trụ tam giác đều/xiên)** | TRUNG BÌNH (50%) | KÉM (Tam giác đều có $\sqrt{3}$) | CAO | **CAO** (Toạ độ đỉnh rơi khỏi $\mathbb{Q}^3$) | KHÔNG |

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
   - Primitive `construct_prism` trong `primitives.py` vốn đã được thiết kế tổng quát cho chu trình đáy $n$ đỉnh ($n \ge 3$), nhận trực tiếp $n = 4$.
3. **Phù hợp chương trình SGK và đề thi THPT:**
   - Hình hộp chữ nhật và hình lập phương là dạng bài toán thể tích quen thuộc nhất trong chương trình Hình học 12 và chiếm tỉ trọng áp đảo trong các đề thi THPT Quốc gia.
4. **Bàn đạp lý tưởng cho bài toán ảnh (Image/OCR Ingestion):**
   - Các bài toán thực tế (bể nước, căn phòng, kiện hàng...) trong đề thi minh hoạ có hình vẽ thực tế hầu hết là hình hộp chữ nhật.
5. **Không đòi hỏi thay đổi Frontend:**
   - Three.js renderer đã hỗ trợ `mesh` (cho solid), `segment` (cho cạnh), `point_marker` (cho đỉnh), nét đứt khuất và tô mờ đáy.

---

## 4. Phân Tích Kỹ Thuật

### A. Primitives Tái Sử Dụng (Reused Primitives)
- `declare_point`: Đặt toạ độ 8 đỉnh (`LAYOUT_DERIVED`).
- `construct_prism`: Dựng khối lăng trụ 8 đỉnh, 6 mặt tứ giác.
- `construct_segments_group`: Dựng đồng thời 4 cạnh đáy dưới, 4 cạnh bên, 4 cạnh đáy trên theo từng bước sư phạm.
- `measure_quantity`: Biểu thức đo thể tích `volume`.
- `assign_final_memory`: Gán kết quả vào `witness`.
- `memory_declaration`: Khai báo bộ nhớ chuẩn.

### B. Thành Phần Mới Cần Triển Khai
- **Bộ ràng buộc `RangBuocCuboid`** trong `compiler.py`:
  - Nhận diện 8 đỉnh từ `solid_topology` hoặc từ các quan hệ vuông góc/song song.
  - Phân xử 3 kích thước: chiều dài ($a$), chiều rộng ($b$), chiều cao ($c$).
  - Đối với hình lập phương: $a = b = c$ (chỉ cần 1 cạnh).
- **Mở rộng `PrismTopologySpec`**:
  - Bổ sung trường tuỳ chọn `base_shape: Literal["rectangle", "square"] | None` tương tự như `PyramidTopologySpec`.

### C. Kế Hoạch Ca Kiểm Thử (Test Cases)

1. **Ca Dương (Positive Ground Truth):**
   - `CUBOID_01`: Hình hộp chữ nhật $ABCD.A'B'C'D'$ có $AB=3, AD=4, AA'=5$. Kỳ vọng $V = 60$.
   - `CUBE_01`: Hình lập phương $ABCD.A'B'C'D'$ cạnh $a=4$. Kỳ vọng $V = 64$.
   - `CUBOID_SQUARE_BASE`: Hình hộp có đáy là hình vuông cạnh 3, chiều cao 7. Kỳ vọng $V = 63$.
2. **Ca Âm / Từ Chối Fail-Closed (Negative Ground Truth):**
   - `CUBOID_NEG_NON_POSITIVE`: Kích thước cạnh $\le 0$ $\rightarrow$ `INVALID_NON_POSITIVE_LENGTH`.
   - `CUBOID_NEG_CONFLICT`: Đoạn $AB$ vừa khai bằng 3 vừa khai bằng 5 $\rightarrow$ `INVALID_CONFLICT`.
   - `CUBOID_NEG_MISSING_HEIGHT`: Cho đáy chữ nhật nhưng thiếu thông tin chiều cao $\rightarrow$ `UNSUPPORTED_MISSING_FACT`.

---

## 5. Cổng Nghiệm Thu Đề Xuất (Acceptance Gates)

1. `GATE_1`: `PrismTopologySpec` hỗ trợ `base_shape` chuẩn hoá.
2. `GATE_2`: `GeometryFactGraph` và `compiler.py` phân xử thành công `RangBuocCuboid` cho cả `cuboid` và `cube`.
3. `GATE_3`: 100% test compiler và contract adapter vượt qua (exit 0).
4. `GATE_4`: Sinh trace sư phạm 8 đỉnh, 12 cạnh, nhãn thể tích `V(ABCD.A'B'C'D')`.
5. `GATE_5`: Không có toạ độ vô tỉ; `freeze_evaluation_candidate.py --verify` và `lock_cache_identity.py --verify` đều PASS.
6. `GATE_6`: Bộ test Playwright visual replay tạo contact sheet độc lập xác nhận hiển thị trực quan 3D không suy biến.
