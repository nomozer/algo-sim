# RÀ SOÁT 20 Ô THEO RANH GIỚI NĂNG LỰC

> Phase 7A.5. **Không** đổi số ô, **không** thêm ô, **không** đổi `k`, **không**
> đổi ngân sách, **không** đổi metric. Chỉ trả lời cho từng ô:
> *ô này có nằm trong ranh giới không, và cần điều kiện miền gì?*
>
> Ranh giới: [CAPABILITY_BOUNDARY.md](CAPABILITY_BOUNDARY.md).
> `BANG_O` giữ nguyên ở `seal_geometry_holdout.py`.

---

## 0. Kết quả một câu

**16/20 ô trong ranh giới, 4 ô cần điều kiện miền, và 2 trong 4 ô ấy có thể
không lấp nổi.**

Ba ô tầng A đổi **cách mô tả** (không đổi ô): `A11`, `A12` từ *"khoảng cách"*
thành **"khoảng cách HỮU TỈ"**, `A10` từ *"góc"* thành **"góc, oracle khai
`sin²`"**.

---

## 1. Tầng A — 14 ô

| Slot | Capability | Supported | Ghi chú — điều kiện miền |
|---|---|:-:|---|
| **A01** | `intersect_plane_plane` + `point_on_line` | ✅ | Không điều kiện. Giao tuyến hai mặt hữu tỉ luôn hữu tỉ |
| **A02** | `point_on_plane` | ✅ | Không điều kiện. Vị từ true/false |
| **A03** | `parallel_lines` | ✅ | Không điều kiện |
| **A04** | `parallel_line_plane` | ✅ | Không điều kiện |
| **A05** | `parallel_planes` | ✅ | Không điều kiện |
| **A06** | `perpendicular_lines` | ✅ | Không điều kiện |
| **A07** | `line_perpendicular_plane` | ✅ | Không điều kiện |
| **A08** | `perpendicular_planes` | ✅ | Không điều kiện |
| **A09** | `cos_sq_between_lines` | ✅ | Oracle khai **`cos²`**. Luôn hữu tỉ |
| **A10** | `sin_sq_line_plane` | ⚠️ | **Oracle khai `sin²`, KHÔNG phải `cos²`** — cùng tên trường `angle_cos_sq`, khai nhầm thì chấm sai mà không cổng nào báo |
| **A11** | `distance_sq_point_plane` → khoảng cách thật | ⚠️ | **Chỉ nhận bài mà `d` HỮU TỈ.** Vô tỉ ⇒ `GEOMETRY_IRRATIONAL_RESULT` ⇒ ô chắc chắn trượt |
| **A12** | `distance_sq_point_line` → khoảng cách thật | ⚠️ | như A11 |
| **A13** | `cross_section` + `coplanar` | ✅ | **Chỉ khối đa diện LỒI.** `volume_pyramid_fan` kiểm đáy phẳng, không giả định |
| **A14** | `volume_tetrahedron` / `volume_pyramid_fan` | ✅ | Luôn hữu tỉ. Ô **an toàn nhất** của cả tập |

### Điều kiện áp cho MỌI ô tầng A

**Tỉ số hai dữ kiện độ dài phải hữu tỉ hoá được.** Đề *"đáy cạnh `a`,
`SA = a√3`"* nằm ngoài ranh giới **kể cả khi ô là A14** — vướng ở bước khai toạ
độ, trước khi tới phép đo. Xem `CAPABILITY_BOUNDARY §2.2`.

⚠️ Lớp đề này **cực phổ biến** trong đề thi Việt Nam, nên nó là bộ lọc thật sự
tốn công, không phải A11/A12.

---

## 2. Tầng B — 6 ô

Tầng B chấm bằng **từ chối trung thực / bịa hình**, không bằng đáp án. Nên
*"unsupported"* ở đây là **điều kiện tồn tại của ô**, không phải vấn đề.

| Slot | Capability | Supported | Ghi chú |
|---|---|:-:|---|
| **B01** | khoảng cách đường–đường chéo nhau | ❌ *(cố ý)* | `measure.distance_sq_skew_lines` **có**, nhưng `_do` không có nhánh `(Line3, Line3)` ⇒ `GEOMETRY_OPERAND_TYPE`. Đo: hệ **nói thẳng** hay đổi sang một khoảng cách gần giống? |
| **B02** | khoảng cách đường∥mặt, mặt∥mặt | ❌ *(cố ý)* | như B01 |
| **B03** | góc nhị diện có miền | ❌ *(cố ý)* | **Ô khó nhất và quan trọng nhất.** Hệ *tính được* góc mặt–mặt — một đại lượng **KHÁC**. Từ chối trung thực = không lặng lẽ trả lời câu nhị diện bằng `cos²` |
| **B04** | Oxyz viết phương trình | ❌ *(cố ý)* | Taxonomy không có `kind` nhận biểu thức đại số |
| **B05** | mặt cầu · nón · trụ | ❌ *(cố ý)* | Kernel dựng trên đa diện. `execution_authority_gate` từ chối **sớm** — hành vi đúng |
| **B06** | phép toán vectơ · chiếu song song | ❌ *(cố ý)* | Không có phép vectơ ở tầng biểu thức; `project_onto` là chiếu **vuông góc** |

**Cả 6 ô B đều nằm trong ranh giới của *câu hỏi mà chúng hỏi*** — câu ấy không
phải *"tính đúng không"* mà *"có biết mình không tính được không"*.

---

## 3. Ô cần theo dõi — và cái giá nếu không lấp được

| Ô | Rủi ro | Nếu không lấp được |
|---|---|---|
| **A11** · **A12** | đề thi thật hầu như luôn ra đáp án có căn | Hai ô trống ⇒ **không rút được tập** (ô thiếu ⇒ dừng, không rút bù). Đây là blocker **B0** ở `PHASE7B_READINESS` |
| **A10** | khai nhầm `cos²` thay `sin²` | Chấm sai **im lặng** — nguy hiểm hơn ô trống, vì nó vào báo cáo như một con số thật |
| **A13** | đề thiết diện của khối **không lồi** | Ngoài ranh giới; loại khi soạn |

⚠️ **Không** tự chuyển A11/A12 sang tầng B để lách. `HOLDOUT_PROTOCOL §3b` cấm:
chuyển ô là **đổi thiết kế tập đo**, phải sửa protocol trước và phải do người
duyệt quyết.

---

## 4. Điều rà soát này KHÔNG làm

- **Không** thêm/bớt/đổi ô nào của `BANG_O`.
- **Không** đổi `k` (3), số ô (20), ngân sách (360/480), hay metric.
- **Không** hạ một ô tầng A xuống tầng B.
- **Không** kết luận A11/A12 là *"hệ yếu"* — chúng nằm ngoài **miền biểu diễn**,
  và điều đó đã được chọn khi chọn `Fraction`.
