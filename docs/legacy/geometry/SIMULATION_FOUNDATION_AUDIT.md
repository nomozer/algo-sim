# SIMULATION FOUNDATION — AUDIT & KIẾN TRÚC

> Chuyển từ **Geometry Program** sang **mô phỏng 3D tương tác**. Tài liệu thiết
> kế, **chưa code, chưa commit, chưa gọi API**.

---

## 1. Kiến trúc hiện tại — **có nhiều hơn dự kiến**

Audit đọc từ mã, không từ trí nhớ.

### Đã có, và đã chạy

| Lớp | Trạng thái | Nơi |
|---|---|---|
| Nhân hình học hữu tỉ chính xác | ✅ | `geometry/{exact,predicates,kernel,measure,section}.py` |
| `Vec3` `Line3` `Plane3` `Polyhedron` `Section` | ✅ | `exact.py` · `section.py` |
| IR có **câu lệnh dựng** | ✅ | `construct_{point,line,plane,solid,section}` |
| Phép **đo** | ✅ | `MeasureExpr` — distance · angle_cos_sq · volume |
| **Vết dựng từng bước** | ✅ | `SemanticTraceStep` |
| **Đồ thị phụ thuộc** | ✅ | `coverage_gate._phu_thuoc` |
| Khung hình hoá | ✅ | `VisualTraceAdapter` → `VisualFrame[]` |
| **Renderer 3D chạy thật** | ✅ | `encap-ui3d.tsx` · 363 dòng · three.js |
| `three` + `@types/three` | ✅ | đã trong `package.json` |

### Hai thứ quan trọng hơn cả, và đề bài chưa nêu

**① Vết dựng ĐÃ LÀ timeline mà STEP 4 yêu cầu.**

```python
SemanticTraceStep:
    step_index · action · target · details · memory_snapshot · tier1_narration
```

Với `construct_point`, `details` mang `{label, toa_do}`. Với `construct_section`,
kernel sinh **một bước cho MỖI CẠNH**, kèm `face_index` — nên lời kể *"trên mặt
(SBC), nối M với N"* đã nói được. Timeline không cần dựng mới; nó cần **được
phơi ra**.

**② Renderer 3D đã có tiền lệ ĐÚNG hợp đồng STEP 5.**

`encap-ui3d.tsx` tuyên bố ngay trong docstring:

> *"CÙNG module / CÙNG state với renderer 2D: KHÔNG engine 3D, KHÔNG tính lại
> PDU. Mọi toạ độ/camera/mesh là renderer-owned (ref/closure), **KHÔNG BAO GIỜ
> vào store/state**."*

Đó chính xác là `display(state)` mà STEP 5 đòi, và nó đã qua kiểm thử. Wave
renderer hình học **sao chép một khuôn đã chứng minh**, không phát minh lại.

---

## 2. Bảng THIẾU — đối chiếu đúng yêu cầu STEP 1

| Đối tượng | Đề bài đòi | Hiện có | Thiếu |
|---|---|---|---|
| **Point** | `position` · `label` · `visible` | `Vec3(x,y,z)` hữu tỉ · `label` trong `ConstructPointStmt` | `visible` · màu · kiểu hiển thị |
| **Line** | `start` · `end` · `direction` · `visible` | `Line3(điểm, vector chỉ phương)` | `start`/`end` (đoạn để vẽ) · `visible` |
| **Plane** | `vertices` · `normal` · `visible` | `Plane3(normal, d)` — **vô hạn**, không có biên | **đa giác biên để vẽ** · `visible` |
| **Solid** | `vertices` · `edges` · `faces` · `volume` · `visible` | `Polyhedron(vertices, faces)` | **`edges`** (suy được từ `faces`) · `visible` |
| **Trace** | action · object · explanation | ✅ đủ ba | — |
| **Dependency** | đồ thị phụ thuộc | ✅ `_phu_thuoc` | **chưa xuất ra ngoài cổng** |

Ba khoảng trống thật, không phải sáu:

**Ⓐ Không có nguyên thuỷ thị giác 3D nào.** Chín primitive hiện tại đều là khung
nhìn cấu trúc dữ liệu 2D — `array_strip`, `stack_view`, `graph_view`… Không có
`scene3d`. **Đây là chặn cứng của `B` (servable)**: `learner_surface` đòi mọi
container BIẾN ĐỘNG phải có binding, mà một `solid` thì không binding nổi.

**Ⓑ Không có thuộc tính thị giác.** `visible`/`color`/`highlight` không tồn tại
ở bất kỳ tầng nào. Đúng như vậy là **cố ý** cho tới giờ: engine sở hữu ngữ
nghĩa, renderer sở hữu trình bày. Câu hỏi thiết kế là chúng thuộc về đâu — §4.

**Ⓒ Mặt phẳng không có biên.** `Plane3` là `normal·x = d`, vô hạn. Vẽ được thì
phải có một đa giác hữu hạn. Đây là **thiếu sót của tầng TRÌNH BÀY**, không phải
của kernel — kernel đúng khi giữ mặt phẳng vô hạn.

---

## 3. Phát hiện lớn nhất: **kéo thả KHÔNG cần bộ giải ràng buộc**

Đây là điều làm cả STEP 2 và STEP 3 rẻ hơn hẳn đề bài giả định.

GeoGebra cần một **engine lan truyền phụ thuộc** vì nó lưu đối tượng dưới dạng
**giá trị**: kéo `A` thì phải tìm mọi thứ phụ thuộc `A` rồi tính lại theo đúng
thứ tự.

Hệ này lưu đối tượng dưới dạng **một CHƯƠNG TRÌNH**. Nên:

```
kéo A  ⇒  đổi A.initial_value  ⇒  CHẠY LẠI interpreter
```

Mọi đối tượng dẫn xuất tự tính lại **theo đúng cách nó được dựng**, bằng số hữu
tỉ chính xác, qua đúng kernel đã kiểm chứng. Không cần engine thứ hai.

`SemanticProgramInterpreter.execute(spec)` là **hàm thuần**: bộ nhớ dựng mới mỗi
lượt, không đọc trạng thái ngoài. Chạy lại là an toàn.

### Hệ quả — ba thứ rơi ra miễn phí

| Yêu cầu STEP 3 | Có sẵn nhờ đâu |
|---|---|
| free vs derived | `_producers(statements)` — biến nào có câu lệnh tạo ra nó là **derived**; khai `initial_value` mà không ai tạo là **free** |
| `drag M` phải bị từ chối | `M ∈ _producers` ⇒ derived ⇒ chỉ đọc |
| highlight dependency khi select | `_phu_thuoc` đã trả `{biến: {phụ thuộc}}` |
| bảo toàn tính đúng toán học | kernel tính lại, **không phải renderer** |

### Hai ràng buộc THẬT của cách này, phải nói trước

**① Chuột cho FLOAT, kernel chỉ nhận HỮU TỈ.** Mọi vị ngữ hình học của kernel so
**bằng đúng** (`u·v == 0`), không epsilon. Một toạ độ float sẽ phá tính chính xác
ngay lập tức. Nên kéo phải **bám lưới hữu tỉ** (ví dụ bước `1/4`).

Đây **không phải hạn chế** — nó là điều kiện để giữ được thứ làm hệ này khác
GeoGebra: *"vuông góc"* là một **sự thật kiểm được**, không phải một xấp xỉ.
Bám lưới còn là hành vi sư phạm đúng: học sinh kéo và thấy quan hệ **giữ hoặc
gãy dứt khoát**, không thấy nó "gần đúng".

**② Chi phí chạy lại.** Chương trình ~10 câu lệnh nên rẻ, nhưng chạy lại ở mỗi
khung chuột 60fps thì phải tiết lưu. Không phải chặn kiến trúc, là chi tiết cài
đặt.

---

## 4. Lớp cần bổ sung — bốn, không hơn

Xếp theo thứ tự phụ thuộc.

### L1 · `GeometryScene` — xuất trạng thái hình học ra khỏi bộ nhớ

Hôm nay `memory_snapshot` chứa `Vec3`/`Plane3` dưới dạng **đối tượng Python**.
Cần một phép chiếu sang JSON mà renderer đọc được:

```
point   { id, label, xyz: [num,num,num], free: bool }
line    { id, label, through: [id,id], segment: [xyz,xyz] }
plane   { id, label, normal, boundary: [xyz…] }   ← biên do TẦNG NÀY dựng
solid   { id, label, vertices: [xyz…], edges: [[i,j]…], faces: [[i…]…] }
section { id, polygon: [xyz…], steps: [{face, a, b}…] }
```

**Ai sở hữu `boundary` và `edges`?** Tầng này, **không phải kernel** — chúng là
lựa chọn TRÌNH BÀY (cắt mặt phẳng vô hạn thành một ô vuông vừa khung hình).
Kernel giữ mặt phẳng vô hạn vì đó là sự thật toán học.

`xyz` xuất dạng **chuỗi phân số** (`"1/2"`), không phải float — giữ nguyên tính
chính xác qua biên JSON, và renderer chỉ chuyển sang float ở **bước cuối cùng
trước khi vẽ**.

### L2 · `SimulationState` — cảnh + phụ thuộc + timeline

```
{ scene: GeometryScene, dependencies: {id: [id…]}, free_objects: [id…],
  timeline: [{ step, action, created, explanation, scene }] }
```

`dependencies` và `free_objects` **dẫn xuất** từ `_phu_thuoc`/`_producers` —
không tính lại, chỉ **xuất ra**. Hôm nay chúng bị vứt sau khi C₁a dùng xong.

### L3 · Nguyên thuỷ thị giác `scene3d`

Một mục mới trong `VisualContainerBinding.primitive`, **và** một nhánh trong
`VisualTraceAdapter.HANDLED_PRIMITIVES` — bất biến #33 nói rõ: thêm vào contract
mà quên nhánh adapter thì LLM khai nó sẽ ra **object rỗng, lỗi CÂM** (đã xảy ra
với `bar_chart`).

Đây là thứ mở khoá `B`.

### L4 · Renderer + tương tác

Sao khuôn `encap-ui3d.tsx`. `display(state)`, không tính, toạ độ/camera/mesh
renderer-owned.

---

## 5. Rủi ro làm sai hướng nghiên cứu

**① Renderer tự tính hình học ⇒ R0 sụp.** Cám dỗ cụ thể: *"tính giao tuyến ngay
trong three.js cho mượt"*. Khi ấy luận điểm *"LLM đọc đề, engine tất định diễn
hoạt"* mất hiệu lực — vì engine diễn hoạt trở thành hai engine, và cái thứ hai
không được kiểm chứng. Tiền lệ `encap-ui3d` cho thấy tránh được.

**② RỦI RO LỚN NHẤT, và nó thuộc về đề tài chứ không về mã: renderer chỉ chạy
được trên 4/10 bài.** `A = 4/10`. Sáu bài còn lại **không sinh ra gì để vẽ**.
Làm renderer bây giờ nghĩa là demo được trên bốn bài, và bốn bài ấy do một tập
DEV mà hệ đã được sửa theo. Nếu hội đồng hỏi *"cho xem bài thứ năm"*, chưa có
câu trả lời.

**③ Trượt thành bản sao GeoGebra.** Kéo–thả–xoay là thứ GeoGebra làm 20 năm nay.
Đóng góp của đề tài **không** nằm ở đó; nó nằm ở *"AI đọc đề bằng ngôn ngữ tự
nhiên rồi sinh ra phép dựng, và phép dựng ấy được kiểm chứng độc lập"*. Wave
renderer phải là **cách trình bày** kết quả ấy, không được nuốt mất nó.

**④ Chấm bằng "hình nhìn đẹp".** `COVERAGE.md` đã cấm; nhắc lại vì renderer là
lúc cám dỗ mạnh nhất.

**⑤ `visible`/`color` trôi vào state ngữ nghĩa.** `ARCHITECTURE_MAP §3` chốt:
renderer sở hữu layout/camera. Thuộc tính thị giác thuộc **L1 (chiếu)**, không
thuộc engine state — nếu không, một thay đổi màu sẽ làm bẩn `measured_system_hash`.

---

## 6. Kế hoạch theo phase

| Wave | Nội dung | Mở khoá | Rủi ro |
|---|---|---|---|
| **5A** | Sửa `construct_solid.faces` nhận **tên đỉnh** | `A` 4/10 → cao hơn | thấp — 3 ca bằng chứng |
| **5B** | L1 `GeometryScene` + L2 `SimulationState`, **xuất** `_phu_thuoc`/`_producers` | timeline + free/derived | thấp — chỉ chiếu, không tính |
| **5C** | L3 `scene3d` + nhánh adapter | **`B` đo được lần đầu** | trung bình — đụng tập primitive đóng băng |
| **5D** | Renderer `display(state)`, xoay/zoom/select | thấy hình | thấp — có khuôn `encap-ui3d` |
| **5E** | Kéo free object = **chạy lại chương trình**, bám lưới hữu tỉ | tương tác | trung bình — tiết lưu, bám lưới |
| **5F** | 5 bài benchmark mô phỏng (STEP 6) | bằng chứng | — |

### Vì sao 5A đứng trước

Không phải để "tăng điểm". Vì **renderer không có gì để vẽ nếu chương trình
không chạy được**, và 3 trong 6 ca thất bại hiện tại chết ở đúng một trường hợp
đồng đã có ba lần bằng chứng. Làm renderer trước 5A là dựng sân khấu trước khi
có diễn viên.

### Vì sao 5C phải tách khỏi 5D

`scene3d` chạm **tập nguyên thuỷ đã đóng băng** (`primitive set · 9 ·
9357dab18fe3bce1` trong candidate) và `VisualTraceAdapter` — hai chỗ có sync-lock
và bất biến #33. Trộn nó vào wave renderer thì một lỗi hợp đồng sẽ bị chẩn đoán
nhầm thành lỗi hiển thị.

---

## 7. Ranh giới giữ nguyên

```
AI  →  Semantic Model  →  Geometry Kernel  →  Simulation State  →  Renderer
```

Chuỗi này **không đổi**. Bốn lớp mới nằm gọn giữa `Kernel` và `Renderer`, và
không lớp nào được phép tính hình học — chúng **chiếu** thứ kernel đã tính.

Renderer nhận `SimulationState`, trả pixel. Không tính, không suy luận, không
sửa dữ liệu sai.

---

## 8. Điều chưa được nói, kể cả sau khi có renderer

`B` (servable) mở ra chỉ chứng minh **hệ bày được kết quả cho học sinh**. Nó
**không** chứng minh mô phỏng **dạy được** — câu đó cần người học thật, và nó
nằm ngoài mọi phép đo hiện có.

Và cho tới khi có bài ngoài tập DEV: mọi con số vẫn là **DEV**, không phải
benchmark.
