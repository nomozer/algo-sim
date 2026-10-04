# CUBOID_CUBE_CONTRACT_DECISION.md — Quyết Định Thiết Kế Hợp Đồng Cho Hình Hộp Chữ Nhật, Hình Lập Phương & Lăng Trụ Đứng Đáy Vuông

> **Mã định danh:** `DECISION-ARCH-CUBOID-CUBE-CONTRACT-01`  
> **Trạng thái:** `APPROVED`  
> **Quyết định chốt:** `CONTRACT_SEMANTICS_READY`  
> **Họ bài toán mục tiêu:** `rectangular_cuboid_volume`, `cube_volume`, và đối chứng `right_square_prism_volume`  
> **Nguyên tắc cốt lõi:** Cuboid và Cube là specialization của primitive `construct_prism`, giữ tính chính xác đại số hữu tỉ $\mathbb{Q}^3$, không suy đoán từ layout toạ độ, phân biệt rạch ròi ba khái niệm hình học và fail-closed khi thiếu căn cứ đề bài.

---

## 1. Bối Cảnh & Đặt Vấn Đề

Trong chương trình Hình học không gian THPT (Toán 11–12), ba khái niệm:
1. **Hình lăng trụ đứng tứ giác có đáy là hình vuông (Right square prism)**;
2. **Hình hộp chữ nhật (Rectangular cuboid)**;
3. **Hình lập phương (Cube)**

có mối quan hệ bao hàm toán học nhưng mang bản chất dữ kiện và ý đồ sư phạm hoàn toàn khác nhau:
- Một hình lập phương là một hình hộp chữ nhật đặc biệt có 3 kích thước bằng nhau.
- Một hình hộp chữ nhật là một hình lăng trụ đứng đặc biệt có đáy là hình chữ nhật.
- Một lăng trụ đứng đáy vuông có đáy là hình vuông nhưng chiều cao có thể hoàn toàn độc lập với cạnh đáy.

### Yêu cầu tiên quyết từ Ranh giới R0 & An toàn ngữ nghĩa:
1. **Tuyệt đối không dùng `base_shape="square"` làm căn cứ duy nhất để kết luận là hình lập phương.** Một lăng trụ đứng đáy vuông cạnh 3, chiều cao 7 có đáy vuông nhưng thể tích $V = 3^2 \times 7 = 63 \neq 3^3$.
2. **Phân loại `cube` phải có căn cứ từ văn bản đề bài (`problem_text` / `source_grounding`), không được suy diễn từ toạ độ hay giả định layout.**
3. **Bài toán cube chỉ cho 1 cạnh vẫn phải tính được:** Đề bài "Cho hình lập phương $ABCD.A'B'C'D'$ cạnh 4" chỉ cung cấp duy nhất 1 con số độ dài. Compiler chỉ được phép gán chiều cao = chiều rộng = chiều dài = 4 khi và chỉ khi hợp đồng xác nhận phân loại `cube` có căn cứ nguồn.
4. **Giữ khả năng mở rộng sang multi-object ở Wave 2:** Cấu trúc định danh không dùng tên biến toàn cục cố định, tách biệt `entity_id` máy với nhãn hiển thị người dùng ($A, B, C, D, A', B', C', D'$).

---

## 2. Phân Tích Bản Chất Hình Học Của Ba Khái Niệm

| Khái niệm | Đáy (`base_cycle`) | Hình dạng đáy (`base_shape`) | Cạnh bên (`lateral_structure`) | Số kích thước độc lập | Công thức thể tích | Dữ kiện tối thiểu để tính $V$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **A. Right square prism** (Lăng trụ đứng đáy vuông) | Tứ giác ($n=4$) | `square` | `right` ($\perp$ đáy) | 2 ($a$ cạnh đáy, $h$ chiều cao) | $V = a^2 \cdot h$ | 1 cạnh đáy + 1 chiều cao |
| **B. Rectangular cuboid** (Hình hộp chữ nhật) | Tứ giác ($n=4$) | `rectangle` | `right` ($\perp$ đáy) | 3 ($a, b$ cạnh đáy, $c$ chiều cao) | $V = a \cdot b \cdot c$ | 2 cạnh đáy kề nhau + 1 chiều cao |
| **C. Cube** (Hình lập phương) | Tứ giác ($n=4$) | `square` | `right` ($\perp$ đáy) | 1 ($a$ cạnh chung) | $V = a^3$ | 1 cạnh duy nhất (với điều kiện contract xác nhận `cube`) |

---

## 3. Đánh Giá Các Phương Án Thiết Kế Biểu Diễn

### Phương án 1: Thêm trường chuỗi `prism_variant` đơn thuần
- **Mô tả:** Thêm `prism_variant: Literal["general", "right_square_prism", "cuboid", "cube"] | None` vào `PrismTopologySpec`.
- **Đánh giá:** Đơn giản nhưng gộp chung nhiều thuộc tính trực giao vào một nhãn duy nhất. Không thể hiện rõ sự độc lập giữa cấu trúc đáy (`base_shape`) và phương cạnh bên (`lateral_structure`). Thiếu trường lưu vết chứng cứ nguồn (`source_grounding`).

### Phương án 2: Typed Solid Classification + Structural Attributes (PHƯƠNG ÁN ĐƯỢC CHỌN)
- **Mô tả:** Mở rộng `PrismTopologySpec` với bộ 4 thuộc tính trực giao có kiểu:
  ```python
  class PrismTopologySpec(BaseModel, frozen=True):
      solid_kind: Literal["prism"] = "prism"
      base_cycle: tuple[str, ...]
      top_cycle: tuple[str, ...]
      correspondence: tuple[tuple[str, str], ...]
      base_shape: str | None = None            # "rectangle" | "square" | None
      lateral_structure: str | None = "right"  # "right" | "oblique"
      solid_subkind: str | None = None         # "cuboid" | "cube" | "right_square_prism" | None
      source_grounding: str | None = None      # Căn cứ văn bản đề bài (vd "hình lập phương", "hình hộp chữ nhật")
  ```
- **Đánh giá:**
  - Nhỏ nhất nhưng đầy đủ ngữ nghĩa (minimal sufficient representation).
  - Tách bạch rõ ràng 3 trục:
    1. Hình học đáy: `base_shape` ("rectangle" vs "square").
    2. Phương cạnh bên: `lateral_structure` ("right" vs "oblique").
    3. Phân loại khối: `solid_subkind` ("cube" vs "cuboid" vs "right_square_prism").
    4. Căn cứ nguồn gốc: `source_grounding` truy vết về câu chữ đề bài.
  - Ngăn ngừa hoàn toàn ngộ nhận: `base_shape="square"` KHÔNG tự động biến thành `cube` nếu thiếu `solid_subkind="cube"` và `source_grounding`.

### Phương án 3: Equality Constraint Groups (Nhóm ràng buộc đẳng thức)
- **Mô tả:** Khai báo danh sách các nhóm cạnh bằng nhau trong `RequestContract`.
- **Đánh giá:** Quá phức tạp (overkill) cho LLM Analyze, phình to schema, phá vỡ tính trực quan sư phạm THPT (trong SGK không ai định nghĩa hình lập phương bằng cách liệt kê 12 đoạn thẳng trong equivalence class). Rủi ro ảo giác phân tích rất cao.

### Phương án 4: Kết hợp Topology thuần túy với Structured Relations
- **Mô tả:** Giữ nguyên topology hiện tại, chỉ dựa vào `geometric_relations` và `source_invariants`.
- **Đánh giá:** **Bế tắc hoàn toàn với Cube.** Đề bài CUBE_P01 chỉ cho $AB = 4$. Nếu không có phân loại ngữ nghĩa `solid_subkind = "cube"`, FactGraph chỉ thấy 1 cạnh duy nhất và compiler buộc phải báo thiếu chiều cao $AA'$ và thiếu cạnh đáy $AD$, dẫn đến từ chối oan một bài toán hợp lệ.

---

## 4. Quyết Định Thiết Kế Chi Tiết (Design Specification)

### 4.1. Hợp đồng Nội Bộ Server (`RequestContract`)
Cập nhật `PrismTopologySpec` trong `backend/app/simulation/semantic_program/request_contract.py`:
```python
class PrismTopologySpec(BaseModel):
    """Cấu trúc tô-pô bất biến của khối lăng trụ (kể cả hình hộp chữ nhật và hình lập phương)."""

    model_config = ConfigDict(frozen=True)

    solid_kind: Literal["prism"] = "prism"
    base_cycle: tuple[str, ...]
    top_cycle: tuple[str, ...]
    correspondence: tuple[tuple[str, str], ...]
    base_shape: str | None = None
    lateral_structure: str | None = "right"
    solid_subkind: str | None = None
    source_grounding: str | None = None
```

### 4.2. Lược đồ Model-Facing (`_luoc_do_solid_topology`)
Cập nhật `_luoc_do_solid_topology()` trong `backend/app/simulation/semantic_program/analyze_contract.py`:
- `base_shape`: `{"type": "STRING", "enum": ["rectangle", "square"], "description": "Dạng hình học của đáy nếu xác định được ('rectangle' hoặc 'square')."}`
- `lateral_structure`: `{"type": "STRING", "enum": ["right", "oblique"], "description": "Cấu trúc cạnh bên: 'right' (vuông góc với mặt đáy) hoặc 'oblique' (xiên)."}`
- `solid_subkind`: `{"type": "STRING", "enum": ["cuboid", "cube", "right_square_prism"], "description": "Phân loại chuyên biệt của khối lăng trụ: 'cuboid' (hình hộp chữ nhật), 'cube' (hình lập phương), 'right_square_prism' (lăng trụ đứng đáy vuông)."}`
- `source_grounding`: `{"type": "STRING", "description": "Cụm từ trong đề bài làm căn cứ xác nhận phân loại (vd: 'hình lập phương', 'hình hộp chữ nhật')."}`

### 4.3. Quy Tắc Kiểm Định Ngữ Nghĩa (Semantic Validation Rules)
Trong `_doc_solid_topology` và `contract_adapter`:
1. **Quy tắc Cube (`RULE_CUBE_CONSISTENCY`):**
   - Nếu `solid_subkind == "cube"`:
     - `len(base_cycle) == 4` và `len(top_cycle) == 4`.
     - `base_shape` phải là `"square"`.
     - `lateral_structure` phải là `"right"`.
     - `source_grounding` hoặc `problem_text` phải chứa căn cứ khẳng định hình lập phương (từ khóa "lập phương", "cube", hoặc đẳng thức tất cả các cạnh).
     - Nếu đề bài cho nhiều cạnh mà các độ dài khác nhau $\implies$ từ chối ngay với mã `INVALID_CONFLICT` (`CUBE_EDGES_UNEQUAL`).
2. **Quy tắc Cuboid (`RULE_CUBOID_CONSISTENCY`):**
   - Nếu `solid_subkind == "cuboid"`:
     - `len(base_cycle) == 4` và `len(top_cycle) == 4`.
     - `base_shape` phải là `"rectangle"` hoặc `"square"`.
     - `lateral_structure` phải là `"right"`.
     - Nếu đề bài khai cạnh bên xiên (`lateral_structure == "oblique"`) $\implies$ từ chối với mã `INVALID_CONFLICT` (`OBLIQUE_LATERAL_EDGE_FOR_CUBOID`).
3. **Quy tắc Right Square Prism (`RULE_SQUARE_PRISM_CONTROL`):**
   - Nếu `base_shape == "square"` và `solid_subkind != "cube"`:
     - Khối được phân loại là `right_square_prism`.
     - Bắt buộc phải có cả dữ kiện cạnh đáy và chiều cao. Nếu thiếu chiều cao, không bao giờ được tự suy diễn chiều cao bằng cạnh đáy; phải từ chối `UNSUPPORTED_MISSING_FACT` (`REQUIRED_LENGTH_MISSING`).

---

## 5. Bảng Đối Chuẩn Nghiệm Thu Phase 1 (Acceptance Verification)

| Mã ca thử nghiệm | Đề bài vắn tắt | Dữ kiện trích xuất | Phân loại ngữ nghĩa (`solid_subkind`) | Căn cứ nguồn (`source_grounding`) | Kết quả xử lý kỳ vọng | Lý do nghiệm thu |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **CUBE_P01** | Hình lập phương $ABCD.A'B'C'D'$ cạnh 4. | $AB = 4$ | `cube` | "hình lập phương" | **PASS** (Thể tích = 64) | Tính được từ 1 cạnh vì có contract xác nhận `cube` hợp lệ. |
| **SQUARE_PRISM_CONTROL** | Lăng trụ đứng $ABCD.A'B'C'D'$ đáy vuông cạnh 3, chiều cao 7. | $AB = 3, AA' = 7$ | `right_square_prism` | "lăng trụ đứng" | **PASS** (Thể tích = 63) | Phân loại là `prism`/`right_square_prism`, không bị nhầm thành `cube`. |
| **CUBOID_P01** | Hình hộp chữ nhật $ABCD.A'B'C'D'$ $AB=3, AD=4, AA'=5$. | $AB=3, AD=4, AA'=5$ | `cuboid` | "hình hộp chữ nhật" | **PASS** (Thể tích = 60) | Ba kích thước độc lập, phân loại `cuboid` chính xác. |
| **CUBE_CONFLICT_01** | Hình lập phương cạnh 4 nhưng cho thêm $AD=5$. | $AB=4, AD=5$ | `cube` | "hình lập phương" | **FAIL-CLOSED** (`INVALID_CONFLICT`) | Cạnh mâu thuẫn bị chặn lập tức. |
| **CUBE_UNGROUNDED_01** | Lăng trụ đứng đáy vuông cạnh 4, không nói lập phương, thiếu chiều cao. | $AB = 4$ | `right_square_prism` | "lăng trụ đứng" | **FAIL-CLOSED** (`UNSUPPORTED_MISSING_FACT`) | Không dùng đáy vuông để suy diễn cube khi thiếu chiều cao. |
| **CUBOID_OBLIQUE_01** | Hình hộp có cạnh bên xiên góc 60 độ nhưng khai cuboid. | $AB=3, AD=4, AA'=5$ | `cuboid` | "hình hộp xiên" | **FAIL-CLOSED** (`INVALID_CONFLICT`) | Cạnh bên xiên không thể là hình hộp chữ nhật. |

---

## 6. Kết Luận Chính Thức

Hợp đồng phân biệt rõ ràng và đầy đủ ba khái niệm hình học, bảo đảm tính bất biến R0 và tuân thủ nguyên tắc fail-closed.

```text
FINAL_DECISION = CONTRACT_SEMANTICS_READY
PHASE_1_GATE = PASS
PROCEED_TO_PHASE_2 = YES
```
