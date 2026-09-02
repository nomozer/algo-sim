# GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT

> Soát ngày **2026-09-02**. **AUDIT ONLY** — `SOURCE_CHANGES = 0`,
> `APPLICATION_LLM_CALLS = 0`, không benchmark mới.
>
> Mọi kết luận dưới đây đọc từ **mã nguồn đang chạy**, không từ tài liệu. Chỗ
> nào tài liệu và mã lệch nhau thì mã thắng, và lệch ấy được ghi ra.
>
> Ba lượt dò kernel (chỉ đọc, 0 model call) dùng để trả lời §6 và §18; kết quả
> chép nguyên văn tại chỗ.

---

## 1. AUTHORITY MAP

| concept | thẩm quyền | nơi ở |
|---|---|---|
| SEMANTIC_TYPE | `MemoryType` — `Literal` đóng, 21 giá trị | `contract.py:185` |
| OPERATOR_SIGNATURE | `_CHU_KY` + `_TOAN_HANG_LENH` | `ir_static_check.py:107,125` |
| MEASURE_SIGNATURE | `BANG_PHEP_DO` | `measure_contract.py` |
| CHECKER | `GEOMETRY_CHECKERS` — 9 mục | `geometry_obligations.py:292` |
| GEOMETRY_RUNTIME | `geometry/{exact,predicates,kernel,measure,radical,section}` | một chiều, không import ngược |
| SOLID_TOPOLOGY | `section.Polyhedron` (`vertices` + `faces`) | `geometry/section.py:63` |
| TRACE | `interpreter.py` phát `action`; `build_timeline` chiếu | `simulation_state.py` |
| SCENE_ADAPTER | **hai chặng**: `build_scene` (kiểu + nhãn) → `build_scene3d` (loại vẽ + nhóm) | `simulation_state.py:205`, `scene3d.py:160` |
| TRANSPORT | `transport.to_transport` | `transport.py` |
| DISPLAY_METADATA | **KHÔNG CÓ MỘT CHỦ** — xem §4 | — |
| RENDER_KIND | `RENDER_HINT` (backend) ‖ `RENDER_KINDS` (frontend) | `scene3d.py:44` ‖ `scene3d-model.ts:61` |
| INTERACTION_STATE | `interaction-state.ts` — một chủ | `domains/geometry/interaction-state.ts` |

### AUTHORITY_DUPLICATIONS

| # | truth bị nhân đôi | có khoá đồng bộ? | đánh giá |
|:-:|---|---|---|
| D1 | chữ ký biểu thức: `_CHU_KY` ‖ luồng `if` trong `eval_geometry_expr` | **CÓ** — `test_type_authority.py` đọc AST của `eval_geometry_expr` rồi so hai tập | chấp nhận được; đã trôi thật 2 lần trước khi có khoá |
| D2 | loại hình vẽ: `RENDER_HINT` (Python) ‖ `RENDER_KINDS` (TS) | **KHÔNG** — ca vitest khoá một **danh sách chữ viết tay**, không dẫn từ backend | thêm một loại vẽ ở backend ⇒ frontend lặng lẽ trả `null`, vật **biến mất khỏi hình**, không đỏ ở đâu |
| D3 | kiểu ngữ nghĩa: `MemoryType` (khai) ‖ chuỗi `isinstance` trong `build_scene` (giá trị) | **KHÔNG** | nguồn của §3 và §19 — chuỗi `isinstance` **thắng**, và nó không phân biệt nổi `point3` với `vector3` |

Lược đồ IR ↔ frontend thì **có** khoá byte-đối-byte (`test_schema_sync.py`), nên
D2 và D3 là hai chỗ hở còn lại giữa hai ngôn ngữ.

---

## 2. SEMANTIC TYPE MATRIX

Đọc từ `MemoryType`, `build_initial`, `_KIEU_DUNG`, `RENDER_HINT`, `_TRUONG`,
`GEOMETRY_CHECKERS`, `BANG_PHEP_DO`.

`S` source-declarable · `D` dựng được · `P` có provenance · `T` vào trace ·
`X` qua transport · `R` vẽ được · `Sel` chọn được · `I` soi được · `H` ẩn được ·
`Iso` cô lập được · `M` đo được · `C` kiểm được · **`N` có tên hiển thị cho
người học**.

| type | S | D | P | T | X | R | Sel | I | H | Iso | M | C | **N** |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `point3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `point_marker` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `label` |
| `vector3` | ✅ | ✅ | ✅ | ✅ | ⚠️ **đi dưới lốt `point3`** | ❌ **bị lọc khỏi khung** | ✅ | ✅ | ✅ | ✅ | ✅ `angle_cos` | ❌ | ✅ `label` |
| `line3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `line` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `plane3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `surface` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `polygon3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `polygon` | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ chỉ `coplanar` | ✅ |
| `solid` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `mesh` | ✅ | ✅ | ✅ | ✅ | ✅ `volume` | ✅ | ✅ |
| `section` | ❌ *(cố ý)* | ✅ | ✅ | ✅ | ✅ | ✅ `polygon` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| `quantity` | — | ✅ | ⚠️ producer có, **nhãn = `None`** | ✅ | ✅ | ✅ `readout` | ❌ | ❌ | ❌ | ❌ | — | ✅ | ❌ **KHÔNG CÓ** |

Ba ô đáng chú ý, và không ô nào là lỗi UI:

- **`vector3` không tồn tại ở phía bên kia dây.** `build_scene` gán kiểu bằng
  `isinstance(gt, Vec3) → "point3"`, mà runtime dùng chung `Vec3` cho cả điểm
  lẫn vectơ. Kiểu KHAI có sẵn ngay tại đó
  (`kieu = {d.name: d.type …}`, `simulation_state.py:220`) và **chỉ được dùng
  cho `quantity`**. `RENDER_HINT` cũng không có ô `vector3`.
- **`quantity` không có ô tên.** `AssignStmt` — câu lệnh duy nhất chở
  `measure` — là câu lệnh dựng **duy nhất không có trường `label`**, và
  `_provenance` ghi thẳng `"label": None` cho nhánh ấy
  (`simulation_state.py:174`).
- **`quantity` khai kiểu `float`/`int`**, không phải một kiểu hình học, nên nó
  không đi qua đường đặt tên của các vật dựng.

---

## 3. REPRESENTATION COMPLETENESS

| trạng thái | có? | cụ thể |
|---|:-:|---|
| SEMANTIC_BUT_NOT_TRACEABLE | **KHÔNG** | mọi kiểu hình học đều có `action` riêng trong `interpreter` |
| TRACEABLE_BUT_NOT_RENDERABLE | **CÓ** | `vector3` — vào trace, qua transport, rồi **không được vẽ** |
| RENDERABLE_BUT_NOT_INSPECTABLE | **KHÔNG** | ô soi đọc chung `SceneObject` |
| SEMANTIC_WITHOUT_DISPLAY_METADATA | **CÓ** | `quantity`, và mọi vật LLM không đặt `label` |
| FAKE_RENDER_TYPE | **KHÔNG** | `buildObject3D` khoá mọi nhánh theo **cả** loại vẽ **và** trường dữ liệu bắt buộc; thiếu ⇒ `null` |
| FRONTEND_SEMANTIC_INFERENCE_REQUIRED | **CÓ — 2 chỗ** | dưới đây |

**Hai chỗ frontend buộc phải tự suy ngữ nghĩa:**

1. `scene3d-presentation.laVectoDangDiem` phải đọc
   `producer === "vector_from_points"` để nhận ra một `point3` **thật ra là
   vectơ** — vì kiểu đã mất ở `build_scene`. Tầng trình bày đang suy lại một
   mệnh đề ngữ nghĩa.
2. `scene3d-presentation.kyHieuNgan` phải **đọc ngược `id`** (`X_prime` → `X′`,
   cắt tiền tố `vector_|point_|plane_|…`) để có ký hiệu in cạnh vật — vì `label`
   khi vắng rơi về chính `id`.

`USER_FACING_IR_ID_LEAK` **không phải một bug UI riêng lẻ**: nó là triệu chứng
thứ ba của cùng một khoảng trống, cùng gốc với hai chỗ trên.

---

## 4. DISPLAY CONTRACT AUDIT

Trường thật sự tồn tại trên mỗi `SceneObject` (`scene3d.build_scene3d`):

| ô của chỉ thị | tồn tại? | trường thật | ai đặt |
|---|:-:|---|---|
| id (machine identity) | ✅ | `id` | tên biến IR |
| machine type | ✅ | `type` | `build_scene` — **theo GIÁ TRỊ**, không theo khai |
| producer | ✅ | `producer` | `_provenance` |
| depends | ✅ | `depends` | `dependency_graph` |
| source fact / provenance | ✅ | `source`, `origin`, `display_group`, `parent` | `_provenance` + `_nhom` + `_cha` |
| **human display name** | ⚠️ **một nửa** | `label` — có, nhưng **rơi về `id`** khi LLM không đặt, và **luôn** rơi về `id` với `quantity` | LLM, tuỳ ý |
| **short mathematical notation** | ❌ | không có trường nào | — |
| **long pedagogical description** | ❌ | không có trường nào | — |
| exact result | ✅ | `value` (chuỗi) + `exact` (cấu trúc) | `radical.to_json` |

**Trả lời câu hỏi của §4.** Hợp đồng hiện tại **không** có thẩm quyền tương
đương. Nó có đúng **một** ô tên (`label`), và ô ấy đang gánh ba vai khác nhau —
ký hiệu ngắn in cạnh hình, tên đọc được trong cây thành phần, mô tả dài trong ô
soi — nên tầng trình bày phải tự cắt gọt nó, và khi nó vắng thì phải đọc ngược
`id`. Đó đúng là *"frontend parse id"* mà chỉ thị cấm, và nó đang xảy ra ở mã
đã ship.

Khoảng trống, nói cho hẹp: **thiếu một tên do TẦNG NGỮ NGHĨA sinh ra cho những
vật mà LLM không đặt tên — trước hết là `quantity`.** Không thiết kế lược đồ
mới ở wave này.

⚠️ **Một trường có mà không ai đọc.** `scene.events[].action`
(`INIT|CREATE|EXTEND|MEASURE|STEP`) được backend tính có chủ đích — chú thích ở
`scene3d._HANH_DONG` nói *"`MEASURE` tách khỏi `CREATE` vì animation của chúng
khác"* — nhưng `grep '\.action'` trên toàn `frontend/src` trả **0 kết quả**:
`objectsAt`/`highlightedAt` chỉ dùng `step_index` và `object`. Phân biệt sư phạm
ấy hiện **không tồn tại trên màn hình**. Kèm theo, `_HANH_DONG` thiếu hai khoá
`construct_polygon` và `construct_section` (rơi về `"STEP"`) — vô hại **đúng
vì** không ai đọc.

---

## 5. IR-ID LEAK — ROOT CAUSE

Lần theo đúng chuỗi:

```
AssignStmt(target_var="khoang_cach_hs", expr=MeasureExpr(...))
   ▲ KHÔNG có trường `label`               ← ĐIỂM MẤT THỨ NHẤT (contract.py:688)
→ interpreter:  mem["khoang_cach_hs"] = Fraction | Radical      (tên = khoá bộ nhớ)
→ _provenance:  {"producer": "measure.distance", "label": None}
   ▲ ghi thẳng None                        ← ĐIỂM MẤT THỨ HAI (simulation_state.py:174)
→ build_scene:  "label": p.get("label") or ten   →  "khoang_cach_hs"
   ▲ rơi về id                             ← ĐIỂM MẤT THỨ BA (simulation_state.py:227)
→ scene3d:      chở nguyên `label`
→ transport:    chở nguyên
→ frontend:     <span className="geo3d-readout-ten">{o.label}</span>
```

**`IR_ID_LEAK_ROOT_CAUSE = MISSING_SEMANTIC_METADATA`.** Không phải mất trên
đường truyền: không tầng nào **đánh rơi** một cái tên đã có — cái tên **chưa
từng được tạo ra**. Điểm mất thứ nhất là gốc; hai điểm sau là hệ quả trung thực
của nó.

Cùng gốc, ba triệu chứng: nhãn `khoang_cach_hs` trên dải kết quả · dải tiêu điểm
in `Đang dựng the_tich_sabcd` / `Dựa trên S_ABCD` (đọc thẳng
`tieuDiem.created`/`.depends`, vốn là id trace) · `kyHieuNgan` phải đọc ngược
`id`.

**`IR_ID_LEAK_CORRECT_OWNER` = tầng ngữ nghĩa backend**, nơi sinh tên. Hai cửa,
cả hai trong `backend/app/`:

- `contract` — thêm một ô tên cho câu lệnh mang `measure`;
- `simulation_state` — dẫn tên từ `producer` + `of`/`wrt`, vốn **đã là tên
  vật** chứ không phải id thô. Cửa này không đòi LLM nói thêm gì.

**KHÔNG phải owner:** renderer. Đọc ngược `id` ở frontend là bịa tên hiển thị —
đúng điều ba dòng chú thích đầu `scene3d-presentation.ts` tự cấm.

---

## 6. SOLID MODEL

**`SOLID_MODEL = GENERIC_TOPOLOGY`.**

`Polyhedron` là `vertices: tuple[Point3]` + `faces: tuple[tuple[int]]` — không
trường "họ", không enum hình dạng. `exec_construct_solid` chỉ kiểm chỉ số trong
biên và mỗi mặt ≥ 3 đỉnh. `volume_polyhedron` phân rã quạt qua **mọi** mặt,
không giả định số mặt hay hình dạng.

`section.box()` và `section.pyramid_square()` tồn tại nhưng **không được mã sản
phẩm dùng**: chúng chỉ xuất hiện trong `backend/tests/geometry/`. Phân loại
**DEMO/TEST_ONLY** — không nằm trên tuyến ngữ nghĩa.

**`ARBITRARY_CONVEX_POLYHEDRON = YES`.** Không suy từ số mẫu — dò thẳng kernel
bằng hai khối **chưa từng có helper nào trong kho**:

```
[1] BÁT DIỆN ĐỀU (6 đỉnh, 8 mặt tam giác)
  OK   volume: 4/3
  OK   section z=1/2: 4 đỉnh
[2] LĂNG TRỤ TAM GIÁC dựng thô từ vertices+faces
  OK   volume: 1
  OK   section z=1: 3 đỉnh
```

VALIDATE · BUILD · INTERSECT · SECTION · MEASURE · TRACE · RENDER — cả bảy chặng
đi được, với đúng một điều kiện ở SECTION: xem §18.

---

## 7. FAMILY SPECIAL-CASE SEARCH

`grep -niE "chop|pyramid|lang_tru|prism|lap_phuong|cube|tu_dien|tetrahedron|hinh_hop|cuboid|hinh_thoi|rhombus"`
trên toàn `backend/app/**.py`:

| nơi | phân loại |
|---|---|
| `measure.volume_tetrahedron`, `volume_pyramid_fan` | **TOPOLOGY_HELPER_GENERAL** — nhận 4 điểm / đỉnh + đáy bất kỳ, không phải một họ đề |
| `section.pyramid_square`, `section.box` | **DEMO/TEST_ONLY** — 0 lượt import từ mã sản phẩm |
| `session_router.py:29`, `classroom_models.py:171` (`chop::face:1`) | **PRESENTATION_ONLY** — ví dụ trong chú thích, không phải mã |
| `obligations.TERM_TRANSFORMS`, `postconditions` `"cube"` | **DEAD/HISTORICAL** — phép `x³` của miền số học, không phải khối lập phương |
| `domain_profile._MANH_DANH_TU_KHOI` (`hình chóp`, `lăng trụ`, `hình lập phương`…) | **TYPE_DISPATCH_GENERAL** — quyết **MIỀN** (Toán ‖ Tin), không quyết năng lực; chú thích trong file khai điều đó, và khai luôn rằng `mặt cầu`/`hình nón` cố ý có mặt dù kernel không dựng được |

**`PROBLEM_FAMILY_SPECIAL_CASES_ON_SEMANTIC_ROUTE` = KHÔNG CÓ.** Không
`simulation_id ==`, không `demo_id`, không so khớp mảnh văn bản đề trên tuyến
sinh — `grep` trả rỗng cả ba.

⚠️ Một giới hạn thật, nhưng **ở tầng định tuyến, không ở tầng dựng**: nhận miền
chạy trên **danh sách từ khoá**. Đề dùng danh từ khối ngoài danh sách
(`hình chóp cụt`, `bát diện đều`, `khối mười hai mặt`) mà không đủ ba cụm yếu sẽ
bị đẩy sang `GATE_OUT_OF_SCOPE` — đúng lỗ đã đo ở Phase 7B với `hình lập phương`,
và đã vá bằng cách **thêm từ**, không bằng cách đổi cơ chế.

---

## 8. CONSTRUCTION LANGUAGE

8 biểu thức hình học (`_CHU_KY` + `measure`), 7 câu lệnh dựng
(`_KIEU_DUNG` + `declare_point`):

| nhóm | phép | vào | ra | ghép | cần họ riêng | runtime | hệ quả vẽ |
|---|---|---|---|:-:|:-:|:-:|---|
| SOURCE | `declare_point(at)` | số hữu tỉ | `point3` | ✅ | ❌ | ✅ | marker |
| SOURCE | `memory_declaration(initial_value)` | JSON | `point3`·`vector3`·`line3`·`plane3`·`polygon3`·`solid` | ✅ | ❌ | ✅ | theo kiểu |
| POINT | `midpoint(a,b)` | 2×`point3` | `point3` | ✅ | ❌ | ✅ | marker |
| POINT | `divide_segment(a,b,ratio)` | 2×`point3` + phân số | `point3` | ✅ | ❌ | ✅ | marker |
| POINT | `translate(point,vector)` | `point3` + `vector3` | `point3` | ✅ | ❌ | ✅ | marker |
| POINT | `project_onto(point,target)` | `point3` + (`plane3`‖`line3`) | `point3` | ✅ | ❌ | ✅ | marker |
| VECTOR | `vector_from_points(from,to)` | 2×`point3` | `vector3` | ✅ | ❌ | ✅ | **không vẽ** |
| INTERSECTION | `intersect_line_plane` | `line3`+`plane3` | `point3` | ✅ | ❌ | ✅ | marker |
| INTERSECTION | `intersect_line_line` | 2×`line3` | `point3` | ✅ | ❌ | ✅ | marker |
| INTERSECTION | `intersect_plane_plane` | 2×`plane3` | `line3` | ✅ | ❌ | ✅ | line |
| LINE | `construct_line(a,b)` | 2×`point3` | `line3` | ✅ | ❌ | ✅ | line |
| PLANE | `construct_plane(through[3])` | 3×`point3` | `plane3` | ✅ | ❌ | ✅ | surface |
| POLYGON | `construct_polygon(vertices[≥3])` | n×`point3` | `polygon3` | ✅ | ❌ | ✅ | polygon |
| SOLID | `construct_solid(vertices,faces)` | n×`point3` + bảng mặt | `solid` | ✅ | ❌ | ✅ | mesh |
| SECTION | `construct_section(solid,plane)` | `solid`+`plane3` | `section` | ✅ | ❌ | ⚠️ §18 | polygon, **nhiều bước** |
| MEASURE | `measure(distance‖angle_cos_sq‖angle_cos‖volume)` | §13 | `quantity` | ⚠️ ngõ cụt | ❌ | ✅ | readout |
| ARITHMETIC | `arith`, `unary` | số | số | ✅ | ❌ | ✅ | — |

**TRANSFORM: chỉ có `translate`.** Không quay, không vị tự, không đối xứng.

**Closure**: mọi phép sinh vật hình học đều nhận **tên** vật cùng lớp và trả một
vật lại làm được đầu vào — trừ `measure`, cố ý là ngõ cụt (số không dựng tiếp
được gì).

---

## 9. COMPOSITIONAL CLOSURE

Chuỗi mẫu của chỉ thị **đi được trọn vẹn**:
`intersect_plane_plane → line3` → `intersect_line_line → point3` →
`construct_plane(through=[…]) → plane3` → `project_onto → point3` →
`measure(distance) → quantity`. Không chữ ký nào chặn giữa chừng.

### COMPOSITION_BREAKS

| # | về toán học đáng ghép được | chặn bởi | runtime đã có? |
|:-:|---|---|:-:|
| **B1** | *"mặt phẳng qua M **song song** với (SBC)"* | không biểu thức/câu lệnh nào; `construct_plane` chỉ nhận **3 tên điểm** | ✅ `kernel.plane_through_point_parallel_to` |
| **B2** | *"mặt phẳng qua M **vuông góc** với d"* | như trên | ✅ `kernel.plane_through_point_perpendicular_to` |
| **B3** | *"đường qua M **song song** với d"* | `construct_line` chỉ nhận 2 tên điểm | ✅ `kernel.line_through_point_parallel_to` |
| **B4** | *"đường vuông góc hạ từ P xuống (P)"* | không có | ✅ `kernel.perpendicular_foot_line` |
| **B5** | `translate(A, vector_from_points(B,D))` một dòng | mọi ô toán hạng là `str` | — cố ý; viết hai câu là đủ, không mất năng lực |
| **B6** | đo `area` của `polygon3`/`section` | `quantity` không có `area` | ❌ **kernel cũng không có** |

**B1–B4 là cùng một lớp, và là lớp đáng chú ý nhất.** Bốn hàm kernel tồn tại,
chính xác, đã kiểm — và `grep` cho thấy **0 lượt gọi** từ bất kỳ đâu ngoài chính
`kernel.py`. Chúng là **năng lực đã trả tiền mà hệ không dùng được**, đúng lớp
với hai lỗ đã vá trước đây (`intersect_line_line`, `distance` cặp đường–đường)
mà chú thích trong `geometry_exec.py` gọi thẳng tên:

> *"Một năng lực không có cầu nối là một năng lực KHÔNG TỒN TẠI với hệ."*

Và chúng phủ đúng **một trong ba loại hoạt động trong phạm vi** (`CLAUDE.md
§1b`): *quan hệ song song – vuông góc*. Hiện chỉ **kiểm** được quan hệ ấy (§14),
chưa **dựng** được theo nó.

B5 là ràng buộc R0 có chủ đích, không phải khiếm khuyết. B6 thiếu thật ở cả hai
tầng.

---

## 10. NEW PROBLEM ≠ NEW CODE

**`NEW_PROBLEM_WITHIN_IR_REQUIRES_CODE = NO`**, xác định bằng cấu trúc chứ không
bằng demo:

| cơ chế có thể phá bất biến | có trong mã? |
|---|:-:|
| registry theo bài | **không** — `registerAllSimulations()` gọi đúng **một** dòng `registerSemanticDomain()` |
| module theo họ hình | **không** — §7 |
| dispatch theo `simulation_id` | **không** — `grep` rỗng trên tuyến ngữ nghĩa |
| prompt template theo bài | **không** — một `geometry_program_generator.md`, 82 dòng, 0 ví dụ theo bài, 0 nhánh theo họ |
| tuyến render riêng | **không** — envelope có `scene3d` hợp lệ ⇒ `Scene3DExplorer`; 6 loại vẽ, đóng |

Điều kiện *"within existing IR"* là ràng buộc thật: bài **ngoài** IR (mặt cong,
dựng theo song song/vuông góc — B1–B4, diện tích) vẫn cần mở IR. Đó là câu khác
với câu đang hỏi.

---

## 11–12. AI SYNTHESIS BOUNDARY

**`AI_SYNTHESIS_CLASS = B`** — AI tổng hợp một **Semantic Program thực thi
được**; hệ tất định sinh 3D.

Bằng chứng **tĩnh** cho việc nó không chỉ chọn template:

1. **Không có tập template nào để chọn** — §10: không registry, không họ, không
   dispatch theo id.
2. **Thẻ văn phạm SINH TỪ Pydantic** (`grammar_card.py`), nên thứ gửi cho mô
   hình là **văn phạm đóng**, không phải danh mục bài. Thêm một `kind` là thẻ tự
   có.
3. **Đầu ra bị thẩm định như một chương trình**, không như một lựa chọn:
   `ir_static_check` kiểm kiểu từng toán hạng theo `_CHU_KY`, kiểm thứ tự
   định-nghĩa–sử-dụng; `hoisting` xử lý biểu thức lồng. Một enum chọn template
   không cần bất kỳ thứ nào trong đó.
4. **Prompt dạy nguyên tắc, không dạy bài**: chọn hệ trục, thứ tự dựng, chọn
   phép đo bằng câu hỏi *"kết luận có đổi khi đảo chiều một toán hạng không?"*.
   Không một ví dụ theo dạng đề nào.

**`AI_CAN_SYNTHESIZE`** — chọn phép dựng · thứ tự ghép · toạ độ **điểm gốc**
(kèm `model_assumption`/`source_fact_id`) · tên biến · quan hệ phụ thuộc (qua
tên) · bảng mặt `faces` (cấu trúc tổ hợp đọc từ đề) · chọn phép đo · `label` ·
`description`/`pedagogical_intent`.

**`AI_CANNOT_SYNTHESIZE`** — toạ độ **kết quả** (mọi ô toán hạng hình học là
`str`, cưỡng chế ở lược đồ; `tu_choi_toa_do_trong_construct_point`) · primitive
mới (`Literal` đóng) · checker mới (`GEOMETRY_CHECKERS` đóng) · loại vẽ mới
(`RENDER_HINT` đóng) · mã Python · vượt `grounding_gate` · khai một giá trị dẫn
xuất như dữ kiện gốc · viết lời kể từng bước (engine sinh).

---

## 13. MEASUREMENT SIGNATURES

`IR` = `_KIEU_DO` cho qua · `RT` = có nhánh trong `_do()` · `EX` = chính xác ·
`CK` = có checker · `DP` = hiện lên màn hình.

| lượng đo | chữ ký | IR | RT | EX | CK | DP |
|---|---|:-:|:-:|:-:|:-:|:-:|
| `distance` | điểm–điểm | ✅ | ✅ | ✅ `a√b` | ✅ | ✅ |
| | điểm–đường / đường–điểm | ✅ | ✅ | ✅ | ✅ | ✅ |
| | điểm–mặt / mặt–điểm | ✅ | ✅ | ✅ | ✅ | ✅ |
| | đường–đường (cắt · song song · **chéo**) | ✅ | ✅ | ✅ | ✅ | ✅ |
| | đường–mặt / mặt–đường | ✅ | ✅ | ✅ | ✅ | ✅ |
| | mặt–mặt | ✅ | ✅ | ✅ | ✅ | ✅ |
| | **đa giác · khối · thiết diện** | ❌ *(hẹp có chủ đích)* | ❌ | — | — | — |
| `angle_cos_sq` | đường–đường · mặt–mặt · đường–mặt (+ cặp đảo) | ✅ | ✅ | ✅ `Fraction` | ✅ | ✅ |
| | vectơ–vectơ | ❌ | ✅ qua `cos_sq_giua` | ✅ | ✅ | ✅ |
| `angle_cos` | **vectơ–vectơ, CÓ DẤU** | ✅ | ✅ | ✅ | ✅ | ✅ |
| | đường–đường | ❌ *(cố ý: đường không có chiều)* | ❌ | — | — | — |
| `volume` | khối lồi bất kỳ, phân rã quạt | ✅ | ✅ | ✅ `Fraction` | ✅ | ✅ |
| `area` | — | ❌ | ❌ | ❌ | ❌ | ❌ |
| `ratio` | — | ❌ | ❌ | ❌ | ❌ | ❌ |

`angle_cos_sq` khai `("line3","plane3")` ở `BANG_PHEP_DO`, nên **model-facing
hẹp hơn runtime-accepted** — có chủ đích, chú thích ở `measure_contract.py` khai
rõ lý do.

---

## 14. RELATIONS / CHECKERS

9 checker. Cột **Dựng** = có phép dựng nào **tạo ra** quan hệ ấy không.

| quan hệ | Dựng | Khai được | Kiểm được | chỉ nhìn thấy |
|---|:-:|:-:|:-:|:-:|
| `point_on_line` | ✅ gián tiếp | ✅ | ✅ | |
| `point_on_plane` | ✅ gián tiếp | ✅ | ✅ | |
| `parallel` (đ–đ · m–m · đ–m) | ❌ **B1/B3** | ✅ | ✅ | |
| `perpendicular` (đ–đ · đ–m · m–m) | ❌ **B2/B4** | ✅ | ✅ | |
| `coplanar` | ✅ gián tiếp | ✅ | ✅ | |
| `section_matches` | ✅ | ✅ | ✅ | |
| `distance` · `angle` · `volume` | ✅ | ✅ | ✅ | |
| `skew_lines` (chéo nhau) | — | ❌ | ❌ **kernel có `P.skew_lines`, không checker** | ✅ |
| `line_in_plane` | — | ❌ | ❌ **kernel có, không checker** | ✅ |

Phủ **checker** ≠ phủ **dựng**: hai hàng `parallel`/`perpendicular` kiểm được
nhưng **không dựng theo được** — chính là §9 B1–B4 nhìn từ phía kia.

---

## 15. EXACT NUMBER DOMAIN

**`EXACT_NUMERIC_DOMAIN`** = `Fraction` ∪ `Radical(he·√can)`, với `can` nguyên
không chính phương và `MAX_RADICAND = 10¹²`. Toạ độ **luôn** `Fraction` thuần;
căn thức chỉ xuất hiện ở **kết quả đo**. `add` chỉ cộng khi cùng căn thức —
`√2 + √3` **từ chối tường minh**, không xấp xỉ, không âm thầm dựng cây biểu
thức.

**`SYMBOLIC_DOMAIN` = KHÔNG CÓ.** Không tham số ký hiệu (`a`, `h`), không tổng
nhiều căn, không cây biểu thức, không CAS. Chú thích `radical.add` nói thẳng lý
do: *"một CAS nửa vời sai ở chỗ không ai kiểm."*

⚠️ Hệ quả cho phạm vi, cần khai: đề *"cạnh a, chiều cao 2a"* xử lý được **chỉ
vì** prompt dặn thay `a = 1` — tức bằng **chuẩn hoá tỉ lệ**, không bằng đại số
ký hiệu. Kết luận về **quan hệ** thì bất biến theo tỉ lệ; kết luận về **số đo
mang tham số** thì không diễn đạt được.

---

## 16. CONTROL FLOW MODEL

**`CONTROL_FLOW_MODEL = HYBRID`** — IR có `if` · `while` · `for_range` ·
`for_each` · `break` · `return` (di sản miền Tin học, vẫn sống trong
`SemanticStatement`), nhưng chương trình hình học trên thực tế là
**STRAIGHT_LINE**.

**`CONTROL_FLOW_DEFINITE_ASSIGNMENT = PARTIAL`** — giữ nguyên, có bằng chứng.
`ir_static_check` **fail-open trong nhánh lồng**: trong `if`/`while`/`for` chỉ
hỏi *"tên có được định nghĩa ở đâu đó không"*, không hỏi *"lượt chạy này có đi
qua không"*. Chú thích đầu file khai thẳng hệ quả và cấm phát biểu mạnh hơn:

> *"None không bao giờ tới kernel" là một tuyên bố SAI. Đúng là: ba họ lỗi đã
> QUAN SÁT ĐƯỢC ở V3 không còn tới kernel nữa.*

Kernel vẫn fail-closed (`GEOMETRY_UNDECLARED` / `GEOMETRY_OPERAND_TYPE`), nên
kết cục an toàn — chỉ bị bắt muộn một tầng, và **lỗi runtime không được gửi
ngược để mô hình sửa**.

**Ảnh hưởng tới bài hình học phổ thông trong scope: gần như bằng không.** Không
dạng bài nào trong ba loại hoạt động cần rẽ nhánh; thiết diện lặp theo mặt thì
`construct_section` đã tự lo bên trong kernel.
`test_GIOI_HAN_nhanh_khong_chay_van_lot` khoá cho lời khai này không tự mục đi.

---

## 17. CURVED GEOMETRY

| | IR | RUNTIME | CHECKER | TRACE | RENDER |
|---|:-:|:-:|:-:|:-:|:-:|
| circle · sphere · cylinder · cone · curve · surface · quadric | ❌ | ❌ | ❌ | ❌ | ❌ |

**`CURVED_GEOMETRY = NONE`**, và sự vắng mặt được **cưỡng chế ở ba tầng**:
`MemoryType` đóng · `RENDER_HINT` đóng (chú thích: thêm ở đây là *"để tầng trình
bày đẻ ra năng lực mà tầng sinh không có"*) · ca vitest cấm
`CylinderGeometry`/`ConeGeometry`/`TorusGeometry`/`TubeGeometry`/`LatheGeometry`/`ExtrudeGeometry`
trong `scene3d-view.tsx`.

Prompt dặn mô hình **nói thẳng là không diễn đạt được**, không thay bằng khối đa
diện gần giống. `domain_profile` vẫn định tuyến `mặt cầu`/`hình nón` **về** hình
học rồi từ chối trung thực ở cổng sau — cố ý, và đúng.

---

## 18. POLYHEDRAL BOUNDARY

| | |
|---|---|
| lồi | **bắt buộc** — khai ở đầu `section.py` |
| lõm | không nhận (thiết diện có thể gồm nhiều mảnh rời) |
| manifold | không kiểm tường minh; hỏng lộ ra ở bước nối chu trình |
| mặt hở | không nhận |
| mặt suy biến | `MALFORMED_SOLID` khi mặt < 3 đỉnh |
| đỉnh nằm trên mặt cắt | **xem dưới** |

### `SECTION_VERTEX_INTERSECTION_GAP` — tên trong tài liệu SAI, điều kiện thật hẹp hơn

`STATUS_LEDGER`, `CODE_INDEX §190` và `THESIS_ARCHITECTURE` đều mô tả gap là
*"mặt cắt qua ĐỈNH khối"*. **Dò kernel cho thấy điều đó không đúng.** Bảng dưới
là đầu ra nguyên văn trên hình lập phương:

```
  OK  3 đỉnh    | đỉnh trên mp=3  cạnh TRONG mp=0 []            | A,C,B′
  OK  4 đỉnh    | đỉnh trên mp=2  cạnh TRONG mp=0 []            | A,C′ + một điểm giữa
  NEM MALFORMED | đỉnh trên mp=2  cạnh TRONG mp=1 [[0,4]]       | chứa cạnh AA′
  NEM MALFORMED | đỉnh trên mp=2  cạnh TRONG mp=1 [[0,1]]       | chứa cạnh AB
  NEM MALFORMED | đỉnh trên mp=4  cạnh TRONG mp=2 [[2,6],[0,4]] | mặt chéo ACC′A′
```

Biến quyết định là **số CẠNH của khối nằm trọn trong mặt phẳng cắt**, không phải
số đỉnh: 3 đỉnh trên mặt phẳng mà 0 cạnh ⇒ chạy tốt; 2 đỉnh mà 1 cạnh ⇒ hỏng.
Tên đúng phải là **`SECTION_COPLANAR_EDGE_GAP`**.

Đây không phải chuyện chữ nghĩa — nó quyết định **cái gì hỏng**:

```
CHÓP S.ABCD    mặt chéo (SAC)   → NEM MALFORMED_SOLID
               mặt chéo (SBD)   → NEM MALFORMED_SOLID
LẬP PHƯƠNG     mặt chéo ACC′A′  → NEM MALFORMED_SOLID
```

Ba mặt phẳng phổ biến bậc nhất của hình học không gian THPT. Còn *"qua đỉnh"*
theo nghĩa rộng thì **chạy đúng**: thiết diện qua đỉnh S và hai trung điểm cho
ra đúng tam giác `[(1,½,0), (0,½,0), (0,0,2)]`.

⚠️ **Và thông điệp lỗi đổ tội nhầm chỗ.** Nó nói *"bảng mặt khai thiếu"* /
*"khối có thể KHÔNG LỒI"* trong khi khối khai hoàn toàn đúng và lồi. Vòng sửa
≤3 lượt sẽ đẩy mô hình đi sửa một bảng `faces` vốn không sai. Hai khiếm khuyết
chồng lên nhau, và cái thứ hai **tiêu quota thật**.

---

## 19. VISUALIZATION COVERAGE

| semantic | → trace | → scene object | → render kind | → thấy được? |
|---|:-:|---|---|---|
| `point3` | ✅ | `point3` | `point_marker` | ✅ |
| **`vector3`** | ✅ | **`point3`** ⚠️ kiểu mất | `point_marker` | ❌ **bị lọc bỏ có chủ đích** |
| `line3` | ✅ | `line3` | `line` | ✅ renderer cắt đoạn từ `depends` |
| `plane3` | ✅ | `plane3` | `surface` | ✅ biên do renderer quyết |
| `polygon3` | ✅ | `polygon3` | `polygon` | ✅ |
| `solid` | ✅ | `solid` | `mesh` | ✅ |
| `section` | ✅ | `section` | `polygon` | ✅ |
| `quantity` | ✅ | `quantity` | `readout` | ✅ nhưng **không có tên** (§5) |

**Giải thích phát hiện vectơ, ở đúng chỗ của nó** — không phải một quyết định UI
tuỳ tiện:

1. runtime dùng chung `Vec3` cho `point3` và `vector3`;
2. `build_scene` gán kiểu bằng `isinstance`, nên `vector3` → `"point3"`, **dù
   kiểu khai có sẵn ngay tại dòng đó**;
3. `xyz` khi ấy là **thành phần vectơ**, không phải toạ độ một điểm của hình;
4. vẽ nó thành chấm là đặt lên hình một vật **không tồn tại trong bài** — đo
   được: `vector_AA′` hiện thành chấm ở (1,1,3), nơi không có điểm nào của hình;
5. tầng trình bày chọn **không vẽ**, giữ vật trong cây thành phần và ô soi.

Bước 5 là lựa chọn bảo thủ **đúng** cho một tầng không được suy ngữ nghĩa. Bước
2 là **khiếm khuyết thật**, và nó nằm ở backend.

**`SEMANTIC_BUT_NOT_RENDERABLE` = { `vector3` }.** Không có *visual chỉ là xấp
xỉ*; không có *visual type khác semantic type* ngoài đúng ca `vector3`.

---

## 20. INTERACTION ARCHITECTURE

| thao tác | phân loại | chủ trạng thái |
|---|---|---|
| select / hide / isolate | GENERAL_OBJECT_INTERACTION | `InteractionState` |
| inspect | GENERAL_OBJECT_INTERACTION | `Scene3DExplorer` cục bộ (`ngan`, `chiTiet`) |
| explode | SCENE_ONLY, theo `display_group` | `InteractionState.exploded_groups` |
| playback (step / scrub / play) | SCENE_ONLY | `InteractionState.current_step` + `dangPhat` cục bộ |
| camera / fit | SCENE_ONLY | ref trong `scene3d-view` + `fitToken` |
| reset | SCENE_ONLY | `interaction-state.reset()` |

**Không còn nguồn sự thật kép.** `state/classroom-sync.apDungPhien` **không**
phải một store thứ hai: nó là **reducer thuần** nhận `(local, phiên, mốc)` và
trả một `InteractionState` mới — kênh lệnh từ xa chiếu **một chiều** vào đúng
một chủ. `visual_transform` do server phát luôn là đồng nhất thức; trạng thái
bung hình sống ở client. Cả hai đều đúng.

⚠️ **Một tương tác còn lại giữa bản vá đổi bài và chế độ theo dõi lớp học** —
chưa phải bug đo được, ghi để không mất. Hiệu ứng reset chạy theo `[scene]`, còn
`apDungPhien` chỉ áp lệnh khi `phien.cmdId > daThay.cmdId`. Nếu cảnh đổi **giữa**
một round mà giáo viên không phát lệnh mới, học sinh ở chế độ `follow` sẽ về bước
1 và ở đó cho tới lệnh kế tiếp. Điều kiện hẹp; xếp P2.

---

## 21. ERROR CONTAINMENT

**`REACT_ERROR_BOUNDARY = ABSENT`** — xác nhận lại: 0 `componentDidCatch`,
0 `getDerivedStateFromError`, 0 `ErrorBoundary` trong toàn `frontend/src`.

Miền hỏng, theo cây `App.tsx`:

| miền | mất gì nếu ném | có lối tự phục hồi? |
|---|---|---|
| `HOME` / các route danh mục | cả trang | không |
| `WORKSPACE` (`SimulationWorkspace`) | cả trang | không |
| `SCENE3D` (`scene3d-view`, WebGL) | cả trang | không |
| `INSPECTOR` (ô soi) | cả trang | không |
| `PLAYBACK` (thanh tua) | cả trang | không |

Năm miền, **một** số phận. Vị trí hợp lý: **MULTI_LEVEL** — một ở `APP_ROOT`
(giữ vỏ + điều hướng) và một quanh `SCENE3D` (miền rủi ro nhất: WebGL, dữ liệu
do LLM sinh, mã ma trận). Chỉ một tầng ở root thì lỗi renderer vẫn nuốt luôn
thanh điều hướng, và người dùng không quay ra được.

**Priority `P1_PRODUCT`, không phải P0** — hiện chưa có đường ném nào đo được:
`buildObject3D` fail-closed, `hienSo` không ném, 4 dạng envelope hỏng đã đo đều
đi qua êm (`certify-refusal-surface.mjs` 21/21). Nó là **phòng thủ theo chiều
sâu**, không phải vá một lỗ đang chảy.

---

## 22. INTEGRATION FINDINGS RECHECK

**A. stale `InteractionState` → `STATE_AUTHORITY_DRIFT = NO`.** Bản vá đặt đúng
chỗ: `InteractionState` vẫn là chủ duy nhất, hiệu ứng chỉ **gọi lại**
`taoTrangThai()` của chính module ấy khi `scene` đổi — không dựng bản trạng thái
thứ hai, không sao chép luật reset. Kẹp dùng `clampStep` đã có trong
`scene3d-model`, không viết lại phép kẹp. **Không phải che triệu chứng**:
triệu chứng là `current_step` sống lâu hơn cảnh sinh ra nó, và bản vá gắn vòng
đời trạng thái vào đúng vòng đời cảnh.

**B. guest Menu → `DEAD_AFFORDANCE = NO`.** Điều kiện hiện diện của lối ra nay
**dẫn từ cùng một sự thật** đã quyết định cột điều hướng có mount hay không
(`user`), thay vì là một hằng số song song. Ca guard đã đổi từ khoá chữ viết
sang khoá bất biến ấy.

---

## 23. CURRICULUM ≠ EXPRESSIVENESS

Ba con số độc lập, **không được thay nhau**:

| | là gì | giá trị | nguồn |
|---|---|---|---|
| `CURRICULUM_MEASUREMENT_FRAME` | khung **đo** phủ chương trình của đề tài | 21 chủ đề khảo sát ↔ 15 đầu mục chính thức | `GEOMETRY_CURRICULUM_COVERAGE §1` |
| `IR_EXPRESSIVENESS` | ngôn ngữ dựng **thật sự** diễn đạt được gì | 8 kiểu · 8 biểu thức · 7 câu lệnh dựng · 4 lượng đo · 9 checker — đóng, hợp thành được | §8, §9 |
| `VISUALIZATION_COVERAGE` | vật ngữ nghĩa nào **thấy được** | 7/8 kiểu vẽ được; `vector3` không | §19 |

15/21 là số của **một phép đo phủ chương trình**. Nó không nói gì về tính tổng
quát của kiến trúc, và dùng nó làm số đo kiến trúc là đổi đơn vị giữa chừng.

---

## 24. TITLE FIT

**`TITLE_FIT = ACCEPTABLE_WITH_SCOPE`.**

*Đạt phần khó*: hệ **là** một kiến trúc tổng quát, không phải tập demo. Ba bằng
chứng cấu trúc — không phải bằng chứng demo:

- 0 special-case theo họ hình trên tuyến ngữ nghĩa (§7);
- khối là `vertices` + `faces` tổng quát, chạy đúng trên **bát diện đều** chưa
  từng có helper nào trong kho (§6);
- bài mới trong IR không cần một dòng mã (§10).

*Cần khai phạm vi* vì tên đề rộng hơn thứ dựng được: **không mặt cong** (§17) ·
**chỉ khối lồi** (§18) · **không đại số ký hiệu** (§15) · và hiện **không dựng
được theo quan hệ song song/vuông góc** (§9 B1–B4) dù kiểm được (§14). Tên không
đòi phủ hết, nhưng bản thảo phải nói phạm vi ở chỗ người đọc gặp tên — §5.3 đang
làm việc đó và **không được xoá đi**.

---

## 25–26. GAP CLASSIFICATION & PRIORITY

### P0_ARCHITECTURE

| id | gap | nhóm | vì sao P0 |
|---|---|---|---|
| **G1** | **Không có thẩm quyền tên hiển thị ngữ nghĩa.** `quantity` không có ô tên; `label` vắng thì rơi về `id`. Hệ quả đo được: `khoang_cach_hs √22` trên bề mặt học sinh, và `kyHieuNgan` **phải đọc ngược `id`**. | DISPLAY_CONTRACT | trúng thẳng tiêu chí *"renderer phải tự suy semantics"*, và nó đang xảy ra ở mã đã ship, hai chỗ (§3) |
| **G2** | **Kiểu ngữ nghĩa `vector3` mất ở tầng chiếu cảnh**, buộc frontend nhận diện lại bằng `producer`. Một vật ngữ nghĩa hợp lệ **không đi hết** pipeline. | SCENE3D + DISPLAY_CONTRACT | cùng hai tiêu chí P0; cùng gốc với G1 |

G1 và G2 là **một khoảng trống nhìn từ hai phía**: tầng chiếu cảnh vứt đi siêu
dữ liệu ngữ nghĩa mà chính nó đang cầm trên tay (tên ở `p["label"]`, kiểu ở
`kieu[ten]` — hai biến cách nhau bảy dòng).

### P1_PRODUCT

| id | gap | nhóm |
|---|---|---|
| **G3** | `SECTION_COPLANAR_EDGE_GAP` — thiết diện hỏng khi mặt cắt **chứa trọn một cạnh** của khối: (SAC), (SBD), ACC′A′. Kèm thông điệp lỗi **đổ tội nhầm** cho bảng `faces`, làm vòng sửa tiêu quota vô ích. Tên trong 3 tài liệu đang **SAI**. | GEOMETRY_RUNTIME |
| **G4** | B1–B4: **không dựng được** *"qua M song song / vuông góc với …"*, dù 4 hàm kernel đã có và chính xác. Phủ đúng một trong ba loại hoạt động trong phạm vi. | IR_EXPRESSIVENESS |
| **G5** | `REACT_ERROR_BOUNDARY = ABSENT` — 5 miền hỏng, 1 số phận. | ERROR_CONTAINMENT |
| **G6** | `RENDER_HINT` ‖ `RENDER_KINDS` không có khoá đồng bộ liên ngôn ngữ (D2). | DISPLAY_CONTRACT |

### P2_POLISH

| id | gap | nhóm |
|---|---|---|
| G7 | `scene.events[].action` tính rồi chở đi nhưng **0 người đọc**; `_HANH_DONG` thiếu 2 khoá. | DISPLAY_CONTRACT |
| G8 | Nhận miền bằng danh sách từ khoá — danh từ khối lạ bị `GATE_OUT_OF_SCOPE`. | GROUNDING |
| G9 | `skew_lines`, `line_in_plane`: kernel có vị từ, **không** có checker. | CHECKER |
| G10 | Reset-theo-cảnh × chế độ `follow` của lớp học (§20). | INTERACTION_STATE |
| G11 | Tài liệu gọi sai tên G3 ở 3 chỗ (`STATUS_LEDGER`, `CODE_INDEX §190`, `THESIS_ARCHITECTURE`). | — |

### OUT_OF_SCOPE

Mặt cong (§17) · đại số ký hiệu / CAS (§15) · khối lõm và mặt hở (§18) ·
`area` / `ratio` (§13) · kéo–thả liên tục kiểu GeoGebra (phá bất biến #31) ·
phép biến hình quay / vị tự / đối xứng.

> **Không** xếp mặt cong là P0. Nó vắng mặt **có chủ đích, cưỡng chế ở ba
> tầng**, và mô hình được dặn từ chối thẳng thay vì thay bằng khối gần giống.
> Vắng-mà-trung-thực không phải một khiếm khuyết kiến trúc.

---

## FINAL

```
ARCHITECTURE_GENERALITY: MIXED
    lõi dựng / thực thi:  STRONG   (§6 §7 §8 §9 §10 §11)
    biên trình bày:       WEAK     (§3 §4 §5 §19 → G1, G2)

SOURCE_CHANGES:        0
APPLICATION_LLM_CALLS: 0
```

Không chọn **STRONG**: chỉ thị đặt *"renderer phải tự suy semantics"* vào tiêu
chí P0, và điều đó **đang xảy ra ở mã đã ship**, hai chỗ. Nói STRONG là bỏ qua
đúng tiêu chí vừa đặt ra.

Không chọn **WEAK**: không một special-case theo họ hình nào trên tuyến ngữ
nghĩa, khối tổng quát thật, bài mới không cần mã. Đó là phần khó của tính tổng
quát, và nó đứng vững.

### NEXT_ACTION — đúng một gap

**G1 + G2: dựng THẨM QUYỀN SIÊU DỮ LIỆU HIỂN THỊ ở tầng ngữ nghĩa backend.**

Chúng là **một** gap: cùng một tầng (`simulation_state.build_scene`) đang cầm
sẵn cả kiểu khai lẫn tên vật rồi vứt đi cả hai. Tách làm hai lượt là sửa cùng
một dòng hai lần.

Chọn nó, không chọn G3 hay G4, vì:

- **Nó là P0 duy nhất.** G3 và G4 **thu hẹp phủ**; chúng không làm sai một luận
  điểm nào — từ chối vẫn trung thực. G1/G2 thì làm sai: bề mặt học sinh in định
  danh máy, và tầng trình bày đang suy lại ngữ nghĩa — đúng hai điều đề tài
  tuyên bố là không xảy ra.
- Nó đóng `USER_FACING_IR_ID_LEAK` (đang OPEN) **tại đúng owner** đã xác định ở
  §5, thay vì vá ở renderer.
- Nó gỡ cả hai chỗ `FRONTEND_SEMANTIC_INFERENCE_REQUIRED`, trả
  `scene3d-presentation.ts` về đúng vai *trình bày thuần*.
- Không chọn theo việc dễ sửa: G5 rẻ hơn hẳn và vẫn xếp sau.

**Cái giá, nói trước.** Đụng `backend/app/**` là **candidate đã đóng băng hết
hiệu lực** — mọi số đo hiện có mất chỗ bám cho tới khi đóng băng lại. Người dùng
đã cho phép (`ACTIVE_DEVELOPMENT`, *"không coi sealed baseline là lệnh cấm phát
triển source hiện tại"*); **điểm số lịch sử không đổi**, chỉ candidate mới cần
đóng lại.
