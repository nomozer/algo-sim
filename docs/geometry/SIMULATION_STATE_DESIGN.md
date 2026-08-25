# SIMULATION STATE — GHI CHÚ THIẾT KẾ (5B)

> **Chưa cài.** Tài liệu này chốt *hình dạng* và *ranh giới sở hữu* để Wave 5B
> không phải quyết định lại giữa lúc viết mã. Không renderer, không UI.

Bối cảnh và bảng thiếu: `SIMULATION_FOUNDATION_AUDIT.md`.

---

## 0. Nguyên tắc quyết định mọi thứ dưới đây

```
AI → Semantic Model → Geometry Kernel → Simulation State → Renderer
                                        └── hai lớp này CHỈ CHIẾU ──┘
```

`GeometryScene` và `SimulationState` **không tính hình học**. Chúng đọc thứ
kernel đã tính và sắp lại cho renderer đọc được. Một dòng `cross_product` lọt vào
đây là dựng engine hình học thứ hai — và hai engine thì sẽ lệch nhau, lệch câm.

---

## 1. `GeometryScene` — chiếu bộ nhớ ra JSON

Hôm nay `memory_snapshot` chứa `Vec3`/`Plane3`/`Polyhedron` dưới dạng **đối
tượng Python**. Renderer không đọc được. Lớp này chiếu chúng.

### Quy ước SỐ — quan trọng nhất, và dễ làm sai nhất

```
xyz: ["0", "1/2", "2"]      ← CHUỖI PHÂN SỐ, không phải float
```

Kernel dựng bằng `Fraction` để mọi vị ngữ so **bằng đúng**, không epsilon. Đổi
sang `float` ở biên JSON là vứt bỏ đúng thứ làm hệ này khác một bộ vẽ hình. Số
được giữ nguyên dạng phân số **tới tận renderer**, và chỉ hoá float ở **bước
cuối cùng trước khi đặt vào buffer của three.js**.

### Năm hình dạng

```
point   { id, label, xyz, free }
line    { id, label, through: [id, id], segment: [xyz, xyz] }
plane   { id, label, normal: xyz, boundary: [xyz, xyz, xyz, xyz] }
solid   { id, label, vertices: [id…], xyz: [xyz…],
          edges: [[i,j]…], faces: [[i…]…] }
section { id, label, polygon: [xyz…],
          steps: [{ face_index, a: xyz, b: xyz }…] }
```

### Ba trường KHÔNG đến từ kernel, và ai sở hữu chúng

| Trường | Vì sao kernel không có | Ai dựng |
|---|---|---|
| `line.segment` | `Line3` là đường **vô hạn** (điểm + vector chỉ phương) | lớp này — cắt theo hai điểm sinh ra nó |
| `plane.boundary` | `Plane3` là `n·x = d`, **vô hạn** | lớp này — cắt thành ô vuông vừa khung |
| `solid.edges` | `Polyhedron` chỉ giữ `faces`; cạnh **suy ra được** | lớp này — gộp cặp kề trong mỗi mặt |

Cả ba là **lựa chọn TRÌNH BÀY**. Kernel giữ mặt phẳng vô hạn vì đó là sự thật
toán học; cắt nó thành hình vuông là việc của người vẽ. Đặt `boundary` vào kernel
sẽ làm một quyết định thẩm mỹ trở thành một mệnh đề toán học.

### `free` — dẫn xuất, không khai

```
free = (id ∉ _producers(statements))
```

Biến có `initial_value` mà không câu lệnh nào tạo ra ⇒ **tự do**. Nằm trong
`_producers` ⇒ **dẫn xuất**. Không thêm cờ nào cho LLM khai — cờ khai được là cờ
khai sai được.

---

## 2. `SimulationState` — cảnh + phụ thuộc + timeline

```
{
  scene:         GeometryScene,          // trạng thái CUỐI
  dependencies:  { id: [id…] },          // từ _phu_thuoc
  free_objects:  [id…],                  // từ _producers
  timeline: [ { step_index, action, target, created,
                explanation, scene } … ]
}
```

### Hai thứ đang bị VỨT ĐI, và đây là chỗ nhặt lại

`_phu_thuoc` và `_producers` được `check_structural_coverage` tính rồi **bỏ**
sau khi C₁a dùng xong. Chúng chính là đồ thị phụ thuộc mà STEP 2 yêu cầu — không
cần tính mới, cần **thôi vứt**.

⚠️ Cả hai đang là **hàm private** của `coverage_gate`. Xuất chúng ra là biến một
chi tiết cài đặt thành API công khai. Nên 5B phải: đổi thành công khai **có tài
liệu**, hoặc thêm một hàm mỏng `dependency_graph(spec)` gọi chúng — và ghi vào
`CODE_INDEX.md` như một export mới.

### `timeline` — đã có sẵn, chỉ cần chiếu

`SemanticExecutionResult.trace` là `SemanticTraceStep[]`, mỗi bước mang
`memory_snapshot` **đầy đủ**. Nên `timeline[k].scene` = chiếu snapshot thứ `k`.

Bất biến #31 (`frame k ⇔ trace[k]`) áp thẳng: một mục timeline cho đúng một bước,
không gộp, không cắt.

`construct_section` đã sinh **một bước cho MỖI CẠNH** kèm `face_index`, nên bài
"dựng thiết diện" có timeline đúng như STEP 4 mô tả mà không cần thêm gì.

---

## 3. Kéo thả — **chạy lại chương trình**, không phải lan truyền

```
kéo A  →  spec.memory_declarations["A"].initial_value = xyz mới
       →  SemanticProgramInterpreter().execute(spec)
       →  SimulationState mới
```

`execute` là hàm thuần (bộ nhớ dựng mới mỗi lượt, không đọc trạng thái ngoài).
Mọi đối tượng dẫn xuất tính lại **theo đúng cách nó được dựng**, qua đúng kernel
đã kiểm chứng. Không có engine ràng buộc thứ hai.

### Ba luật của thao tác kéo

**① Chỉ kéo được `free_objects`.** `M = midpoint(A,B)` nằm trong `_producers` ⇒
từ chối, và **nói vì sao**: *"M được dựng từ A và B — hãy kéo A hoặc B"*. Đó là
một câu dạy học, không phải một lỗi.

**② Bám lưới hữu tỉ.** Chuột cho float; kernel so bằng đúng. Vị trí kéo phải
làm tròn về một lưới (đề xuất bước `1/4`) **trước khi** vào `initial_value`.

Không phải hạn chế — là điều kiện giữ được thứ khác GeoGebra: *"vuông góc"* là
**sự thật kiểm được**, không phải xấp xỉ. Học sinh kéo và thấy quan hệ **giữ
hoặc gãy dứt khoát**, chứ không thấy nó "gần đúng".

**③ Chạy lại có thể HỎNG, và hỏng là thông tin.** Kéo `A` tới vị trí làm ba điểm
thẳng hàng ⇒ `construct_plane` ném `COLLINEAR_POINTS`. Không được nuốt: hiện lên
*"ba điểm A, B, C đã thẳng hàng — không xác định được mặt phẳng"*. Đó đúng là
điều bài học muốn cho thấy.

---

## 4. Ranh giới với renderer

Renderer nhận `SimulationState`, trả pixel.

**KHÔNG được**: tính giao điểm/giao tuyến · suy ra quan hệ · sửa dữ liệu sai ·
giữ toạ độ trong store.

**Tiền lệ đã chứng minh**: `encap-ui3d.tsx` (363 dòng, three.js) —
*"CÙNG state với renderer 2D, KHÔNG engine 3D, KHÔNG tính lại. Mọi toạ độ/
camera/mesh là renderer-owned (ref/closure), KHÔNG BAO GIỜ vào store."*

Wave renderer sao khuôn đó, không phát minh lại.

---

## 5. Thứ tự phụ thuộc, và vì sao 5C tách khỏi 5D

```
5B  GeometryScene + SimulationState        chỉ chiếu — rủi ro thấp
5C  primitive `scene3d` + nhánh adapter    ĐỤNG tập đã đóng băng
5D  renderer display(state)                có khuôn sẵn
5E  kéo = chạy lại + bám lưới
```

`scene3d` chạm `primitive set · 9 · 9357dab18fe3bce1` (đã ghi trong candidate)
**và** `VisualTraceAdapter.HANDLED_PRIMITIVES`. Bất biến #33 nói rõ: thêm vào
contract mà quên nhánh adapter thì LLM khai nó sẽ ra **object rỗng, lỗi CÂM** —
đã xảy ra thật với `bar_chart`.

Trộn 5C vào wave renderer thì một lỗi hợp đồng sẽ bị chẩn đoán nhầm thành lỗi
hiển thị, và đó là kiểu nhầm tốn nhiều ngày nhất.

---

## 6. Điều tài liệu này KHÔNG quyết định

- Hình dạng cụ thể của `scene3d` binding (5C).
- Bước lưới kéo — `1/4` là **đề xuất**, cần thử với bài thật.
- Camera, ánh sáng, bảng màu (renderer sở hữu).
- Có bày `boundary` mặt phẳng bằng lưới hay bằng mặt mờ.
