# CAPABILITY EXTENSION 02 — THIẾT DIỆN LÀ KẾT QUẢ HẠNG NHẤT

> **Wave đóng 2026-08-30.** Trạng thái phủ sau wave: **PARTIAL**, không phải
> SUPPORTED — lý do ở §6, và nó là một *loại thiết diện chưa xử lý*, không phải
> chuyện chưa đủ test.

---

## 1. Soát đường thiết diện TRƯỚC khi sửa

Đo bằng cách chạy thật một chương trình có `construct_section` qua interpreter →
`build_simulation_state` → `build_scene3d`, không suy từ việc lớp/hàm có tồn tại.

| | Trước wave | Bằng chứng |
|---|---|---|
| `SECTION_REPRESENTABLE` | ✅ | `ConstructSectionStmt(target_var, solid, plane)`; `ir_static_check` đã đòi `solid: solid`, `plane: plane3` |
| `SECTION_EXECUTABLE` | ✅ | `exec_construct_section` → `cross_section` |
| `SECTION_ORDERED` | ✅ | `Section.polygon` đã sắp; `steps` nối đầu-đuôi; `scene3d._TRUONG["section"]` chở nguyên `polygon`·`closed`·`steps` |
| `SECTION_CHECKER` | ❌ | `GEOMETRY_CHECKERS` có 8 kind; kind DUY NHẤT nhận `Section` là `coplanar` |
| `SECTION_SCENE3D` | ✅ | `type: "section"`, `render: "polygon"`, `parent` = khối, `display_group ["construction","section"]` |
| `SECTION_SUBENTITIES` | ❌ | `deriveVisualSubEntities` bỏ qua mọi thứ không phải `type === "solid"` |
| `TRACE` | ⚠️ | chỉ `section_edge` mỗi cạnh; **không** bước nào mang tên khối, tên mặt phẳng, số đỉnh hay chu trình |

Một chỗ nữa, lệch giữa hai bảng: `MemoryType` **không có** `"section"` (thiết
diện phải khai nhờ `polygon3`), trong khi `ir_static_check._KIEU_DUNG` đã coi
`construct_section` sinh ra kiểu `section`. Hai bảng nói hai điều khác nhau về
cùng một vật.

## 2. Vì sao `coplanar` không đủ — đo được, không phải lời khai

Mọi đỉnh thiết diện sinh ra từ giao với **đúng một** mặt phẳng, nên chúng đồng
phẳng **theo định nghĩa**. `coplanar` trên một thiết diện vì thế gần như luôn
xanh, kể cả khi đa giác thiếu đỉnh, thừa đỉnh, hay là một hình nhỏ hơn nằm gọn
bên trong thiết diện thật.

Ca chứng minh — cùng một dữ liệu, hai phán quyết ngược nhau:

```
test_O_DONG_PHANG_DUNG_nhung_DA_GIAC_SAI_thi_FAIL
  coplanar         → ĐƯỢC   (tiền đề của ca này, được assert)
  section_matches  → KHÔNG   "cùng số đỉnh nhưng KHÔNG cùng một đa giác"
```

`test_O2` khái quát: `coplanar` mù với MỌI đa giác con nằm trên mặt cắt.

## 3. Đã sửa ở đâu

| Tầng | Việc |
|---|---|
| `geometry/section.py` | bốn mã suy biến tách rời · `canonical_cycle`/`same_section_cycle` · hậu điều kiện của chính `cross_section` |
| `semantic_program/contract.py` | `section` thành `MemoryType` riêng |
| `semantic_program/obligations.py` | nghĩa vụ thứ chín `section_matches` |
| `semantic_program/geometry_obligations.py` | `check_section_matches` — DỰNG LẠI rồi so chu trình |
| `semantic_program/coverage_gate.py` | nhóm nghĩa vụ thứ BA: CẤU TRÚC (không witness, đòi hai toán hạng) |
| `semantic_program/interpreter.py` | bước KHÉP `construct_section` mang khối · mặt phẳng · số đỉnh · chu trình |
| `learner_surface.py` | `section` là `container` — thiết diện là ĐÁP ÁN của bài, không được giấu |
| `geometry/scene3d-subentities.ts` | đỉnh · cạnh · mặt tô của thiết diện; tên đỉnh theo TRÙNG TOẠ ĐỘ CHÍNH XÁC |
| `geometry/Scene3DExplorer.tsx` | ô soi thiết diện + thao tác «Xem thiết diện» |

**Khối và mặt phẳng của `section_matches` lấy từ phía ĐỀ (`ob.params`), không
từ câu lệnh chương trình.** Lấy từ chương trình thì checker đang hỏi *"cắt cái
anh đã cắt có ra cái anh đã ra không"* — một tautology, và ca *"cắt nhầm mặt
phẳng"* (`test_N`) sẽ không bao giờ bị bắt.

## 4. So chu trình — bất biến với xoay VÀ với đảo hướng

`[A,B,C,D] ≡ [B,C,D,A] ≡ [D,C,B,A]`, nhưng `[A,C,B,D]` là tứ giác **khác** (nối
chéo). Cách làm: sinh cả 2n ảnh của nhóm nhị diện rồi lấy dãy nhỏ nhất theo khoá
`Fraction`. Xoay-về-đỉnh-nhỏ-nhất rẻ hơn nhưng **sai** khi có hai đỉnh cùng nhỏ
nhất. `test_dang_chuan_KHONG_dung_float` quét mã nguồn cấm `float(`/`math.`/
`round(`/`** 0.5` trên đường này.

## 5. Bốn ca suy biến, bốn mã

| Ca | Mã | Ghi chú |
|---|---|---|
| mặt phẳng ngoài khối | `PLANE_DOES_NOT_CUT` | không một điểm chung |
| chạm đúng một đỉnh | `PLANE_TOUCHES_VERTEX` | **mới** — bản cũ gộp vào mã trên VỚI CÂU *"toàn bộ khối nằm về một phía"*, câu ấy SAI ở đây |
| chạm đúng một cạnh | `PLANE_TOUCHES_EDGE` | **mới** — tra bảng mặt để chắc hai đỉnh ấy là một cạnh THẬT |
| chứa trọn một mặt | `CONTAINED_INFINITE_INTERSECTION` | giới hạn đã khai, xem §6 |

## 6. Vì sao VẪN PARTIAL

Sáu điều kiện SUPPORTED của chỉ thị đều đạt (biểu đạt · thẩm định · chạy · checker
riêng · giữ chu trình · dùng được trong Scene3D). Ô vẫn PARTIAL vì còn **hai loại
thiết diện chưa xử lý**:

1. **mặt phẳng cắt TRÙNG một mặt của khối** — về toán, thiết diện khi ấy *là chính
   mặt ấy*; hệ ném `CONTAINED_INFINITE_INTERSECTION` thay vì trả đa giác mặt.
2. **khối KHÔNG LỒI** — ngoài phạm vi từ đầu (thiết diện có thể gồm nhiều mảnh rời).

Số test không nâng claim: 46 ca xanh nói *cái đã làm thì đúng*, không nói *đã làm
hết*.

⚠️ **Khoảng trống ĐO LƯỜNG, khác khoảng trống năng lực.** Ô `A13` của bảng
held-out **đã niêm phong** vẫn gắn `coplanar`. Gắn lại là sửa dụng cụ đo sau khi
niêm phong — đúng thứ con dấu tồn tại để ngăn. Nên trên held-out, thiết diện vẫn
chấm bằng phép kiểm yếu; khai ở
`tests/geometry/test_wave1_oracle_connectivity.py::KHONG_CO_O_DO`, và danh sách
miễn trừ ấy **chỉ được phép ngắn đi** (có test khoá cả hai chiều).

## 7. Bằng chứng chạy được

```bash
cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest -q     # 3508 passed, 18 skipped
cd backend && … -m pytest -q tests/geometry/test_section_capability.py tests/geometry/test_section.py   # 46 passed
cd frontend && npx vitest run && npx tsc -b && npx vite build                  # 1777 passed · build OK
cd backend && … scripts/freeze_evaluation_candidate.py --verify                # khớp bản đã đóng băng
```

`CACHE_VERSION` **51 → 52** (schema đổi vì thêm `MemoryType`, menu nghĩa vụ đổi
vì thêm kind). Taxonomy `2ea8a3d0 → 26cb87b0` · schema `9a4d1c9b → 0660532a` ·
mã sản phẩm `d6265eb4 → 795a77c1`.
