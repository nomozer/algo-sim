# ARCHITECTURE_MAP.md — Bản đồ kiến trúc AlgoSim

Tài liệu **nguồn chân lý bền vững** của repo (CLAUDE.md bị gitignore nên không
mang được sự thật lâu dài). Cập nhật khi **kiến trúc** đổi, không cập nhật theo
từng commit.

## 0. Đọc gì trước khi sửa code

Trước MỌI thay đổi không tầm thường:

1. Đọc `docs/ARCHITECTURE_MAP.md` (file này).
2. Đọc `docs/CURRENT_STATE.md` (milestone, baseline test, gap, việc đã hoãn).
3. Đọc phần liên quan trong `docs/CODE_INDEX.md`.
4. **Đọc chính source file** — docs là bản đồ, không phải lãnh thổ.
5. **Nếu docs mâu thuẫn với code/test → CODE/TEST THẮNG.** Sửa docs, đừng sửa
   code cho khớp docs.

Sau khi xong milestone: cập nhật `CURRENT_STATE.md`; chỉ sửa file này khi kiến
trúc thật sự đổi; sửa `CODE_INDEX.md` khi module/export công khai đổi.

## 1. Hệ thống là gì

Học sinh dán một đề bài bằng lời/hình ảnh → LLM **chỉ** bóc tách dữ kiện có cấu trúc và nghĩa vụ hình học → **engine tất định** (hoặc primitive compiler khi đủ điều kiện) sinh chương trình, diễn giải hoạt cảnh và trạng thái. Toàn bộ chuỗi chữ hiển thị và prompt đều tiếng Việt.

## 2. Luồng xử lý hình học (Pipeline Hiện Tại & Kiến Trúc Đích)

### 2a. Sơ đồ tổng thể

```text
Input text/image
  → Ingestion (chuẩn hóa đầu vào)
  → Analyze LLM (stage_semantic_analyze)
  → RequestContract + structured relations (dữ kiện hình học có cấu trúc)
  → FactGraph (mạng dữ kiện hình học quan hệ)
  → [Rẽ nhánh theo tính hợp lệ / eligible]:
      ├─ Nhánh Thực Nghiệm (Compiler Path):
      │    Deterministic Compiler (primitive_compiler nếu eligible)
      │    → Semantic Program tất định
      └─ Nhánh Mặc Định Hiện Tại (Default LLM Path):
           LLM Synthesis (stage_semantic_program)
           → Semantic Program ứng viên
  → Scene Builder & Interpreter (thực thi chương trình ngữ nghĩa, dẫn xuất tọa độ/bước)
  → Assumption Certificate Gate (w15, chặng `assumption`: giá trị số người học thấy phải có chứng chỉ C0/C1 — §2e)
  → Visual Obligation Gate (kiểm định bao phủ nghĩa vụ trực quan C1/C2)
  → Frontend Step Replay & Scene3D Explorer (diễn hoạt từng bước, tua, tương tác camera)
```

### 2b. Phân định các chế độ kiến trúc

1. **Kiến trúc đang chạy mặc định (`DEFAULT_MODE = LLM_ONLY`):**
   - Đề bài qua Analyze LLM tạo `RequestContract`.
   - `stage_semantic_program` gọi Gemini để tổng hợp `SemanticProgramSpec`.
   - Cổng tất định kiểm định tĩnh, thực thi sinh timeline và kiểm tra nghĩa vụ trực quan.
   - Tuyệt đối chưa thay thế LLM synthesis trên đường mặc định này.

2. **Đường compiler thực nghiệm (Compiler Experimental Slice):**
   - Đã chứng minh trên vertical slice: họ bài chóp đáy tam giác vuông (`right_triangle_base_pyramid_volume`).
     *(w13: danh sách này đã cũ — `geometry_compiler/compiler.py::SUPPORTED_FAMILIES` có sáu họ; mỗi họ còn tự viết chuỗi câu lệnh, xem `ISSUE-ARCH-FORMATION-PER-FAMILY-SEQUENCE`. w14: compiler thôi tự viết đường cao/cạnh bên/đáy trên — bước bổ sung chung ở §2d sinh chúng.)*
   - Sau khi Analyze trích xuất `structured_relations`, `FactGraph` nhận diện cấu trúc và gọi `primitive_compiler` để sinh `SemanticProgramSpec` 100% tất định (0 lượt gọi LLM synthesis).

3. **Kiến trúc đích (Target Architecture: Compiler-First + LLM Fallback):**
   - Đích đến sau khi hoàn thiện các họ hình học: Ưu tiên biên dịch tất định trước (compiler-first).
   - Nếu bài toán thuộc họ đã hỗ trợ (`eligible`) → biên dịch tất định trực tiếp.
   - Nếu bài toán nằm ngoài tập primitive đã hỗ trợ → chuyển tiếp an toàn sang LLM synthesis fallback có giám sát và giới hạn.
   - Chưa được bật cho sản phẩm vì cần đạt đủ 20 cổng tại `docs/MIGRATION_CHECKLIST.md`.

4. **Các thành phần chưa triển khai (Unimplemented Components):**
   - Bộ giải bố cục không gian tổng quát (general 3D spatial layout solver).
   - Đường ống bóc tách vùng ảnh / OCR tự động từ camera điện thoại.
   - Định tuyến compiler-first tự động, cơ chế canary, và rollback production.

### 2c. Scene3D edge identity và occlusion (amendment 2026-09-28)

- Backend là authority của canonical machine edge IDs, edge ownership,
  canonical surfaces, `boundary_edge_ids`, `surface_role` và `occludes_edges`.
  Learner notation chỉ là `display_label`; nó không tham gia exact identity.
- Một logical edge có đúng một visual owner. Các object dẫn xuất chỉ làm
  highlight/hit proxy; chúng không được tạo lớp vẽ solid/dashed thứ hai.
- Product classifier sở hữu `VISIBLE`/`HIDDEN`/`MIXED` spans và recompute theo
  camera/viewport/DPR/matrix/formation/surface signature. Chỉ canonical
  `SOLID_FACE` occlude mặc định.
- Backend phát typed formation events và stable section endpoint provenance;
  frontend không suy semantic kind hoặc section identity từ learner strings.
- Evidence oracle là implementation độc lập: không import classifier,
  triangulator, binning hay epsilon của product. Perspective analytic result
  được cross-check bằng camera ray/triangle reference.

Chi tiết quyết định và trạng thái gate hiện tại nằm ở
[`docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`](architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md).

Năng lực theo tầng (17 nhóm hình × 17 tầng) và các giả định tuyệt đối còn phải
sửa: [`docs/architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md`](architecture/GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md)
(w13). Hướng thay chuỗi câu lệnh viết tay theo từng họ bằng dựng hình theo **lớp
hình** (vai trò gắn ở producer, bước con là sự kiện trace thật — #31/#35 giữ) và
chính sách giả định/mặc định: [`GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md`](architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md)
— tiền đăng ký w13; Track A (dựng hình) và C (nguồn độ dài) triển khai ở w14 (§2d),
Track B (chính sách giả định) dừng ở bước đo.
Việc triển khai hidden-line không đồng nghĩa verification sạch — trạng thái gate
hiện hành chỉ nằm ở `docs/CURRENT_STATE.md`.

### 2d. Dựng hình theo lớp hình và chính sách nguồn (w14)

- **Một bước bổ sung, mọi tuyến.** `semantic_program/formation.py::hoan_thien_dung_hinh`
  chạy ngay đầu `route.verify_and_compile` và `pipeline._dung_scene3d`: cùng đầu vào
  tất định ⇒ cùng spec, nên số khung envelope = số bước formation (#31). Nó chèn
  đáy/đáy trên còn thiếu, đường cao và cạnh bên thành câu lệnh thật trước
  `construct_solid` — mỗi bước là một sự kiện trace thật — cho chương trình compiler
  LẪN LLM. Không đổi bản gốc, lũy đẳng; đầu ra phải qua lược đồ + `kiem_tinh`, hỏng
  thì giữ bản gốc (`COMPLETION_REJECTED_INVALID_OUTPUT`). Bước này ở server nên bề
  mặt mô hình không đổi.
- **Thẩm quyền topology, theo thứ tự:** `contract.solid_topology` khớp khối → quan hệ
  CÓ KIỂU (`perpendicular_line_plane` của hợp đồng, chân `project_onto` của chương
  trình) → bảng mặt không mơ hồ (lá `solid_faces.py`, không import `app`). Nhiều cách
  đọc không tương đương ⇒ `AMBIGUOUS_TOPOLOGY`, khối để nguyên; không bao giờ chọn
  theo tên, nhãn, thứ tự đỉnh/mặt hay tên `*_length`. Bảng mặt hỏng ⇒ chặng
  `formation`, `SOLID_TOPOLOGY_MALFORMED`.
- **Vai trò ở producer.** `simulation_state.build_simulation_state` gọi
  `formation.gan_vai_tro_dung` (topology thuần, không tính hình); `scene3d.py` (chỉ
  import `__future__`/`typing`) chỉ chở `formation_roles`, `shape_class`,
  `formation_requirements` và hợp vai trò theo bước. Frontend và harness không suy
  vai trò từ chữ.
- **Chính sách nguồn.** `check_grounding` / `verify_and_compile` nhận
  `nguon: NguonDe = CAN_DE`; đề rỗng ⇒ `SOURCE_TEXT_MISSING`, không gửi đi sửa.
  `NguonDe.FIXTURE_TIN_CAY` là đối số Python tường minh của test/script cô lập —
  không đọc từ HTTP, mô hình hay cấu hình; không đường sản phẩm nào khai.
- **Một từ vựng nối độ dài** (`segment_relation._NOI_DO_DAI`) dùng chung cho bộ đọc
  độ dài và nhãn bằng chứng GIVEN.
- **Chưa có:** dựng hình khối cong; đường cao khi chân là điểm dẫn xuất chưa dựng.
  (Cổng giả định: có từ w15 — §2e.)

### 2e. Ràng buộc đọc từ đề và chứng chỉ giả định (w15)

Thẩm quyền đăng ký: [`docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`](architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md)
(viết TRƯỚC mã; mã khác văn bản ấy là lỗi của mã).

- **Bộ đọc cùng họ với `point_coordinate` / `plane_equation` / `segment_relation`.**
  `semantic_program/shape_constraint.py::doc_rang_buoc` đọc CÂU ĐỀ theo từ vựng ĐÓNG và trả
  `RangBuoc` do server sở hữu, gắn đúng thực thể. Từ vựng gồm: vuông góc đường–mặt, đường–
  đường, `góc … = 90°`; ký hiệu chóp/lăng trụ; kiểu khối/đáy; tam giác/đáy vuông tại một
  đỉnh; một lăng trụ đứng không tên. Bộ đọc chỉ để XÁC NHẬN tiền đề và kiểm phản ví dụ:
  không vào fact graph, không nâng fact của mô hình thành GIVEN. `phan_chua_doc` báo phần
  dữ kiện không bộ đọc nào đọc trọn; `neu_khoi_da_dien` là vị từ phạm vi U3.
- **Cổng, một hàm.** `assumption_gate.kiem_gia_dinh` chạy trong `route._sau_grounding`,
  sau hậu điều kiện và trước khi biên dịch để phục vụ. Gốc là mọi giá trị SỐ người học
  thấy: bước `MEASUREMENT` và witness của nghĩa vụ. Lát cắt đi theo định nghĩa với tới
  DUY NHẤT trên trace; nhiều định nghĩa ⇒ `CLOSURE_MULTIPLE_DEFINITIONS`. Chứng chỉ có ba:
  - **C0:** mọi literal là `SOURCE_DATUM` của CÙNG thực thể.
  - **C1:** khuôn T1–T6 khớp ràng buộc ĐỌC ĐƯỢC, đỉnh khuôn thoả chính xác, đối chiếu
    bằng chạy lại trên hiện thực chính tắc; chỉ cho thể tích, diện tích, khoảng cách.
  - **Phản ví dụ:** chỉ khi đề đọc trọn và mọi ràng buộc là tiền đề khuôn ⇒
    `DEPENDENT_ON_UNSTATED_ASSUMPTION`.

  Còn lại là `UNDETERMINED`. Tiền đề chỉ đến từ bộ đọc và các bộ phát bất biến gọi KHÔNG
  kèm hợp đồng — chú thích của mô hình không bao giờ là tiền đề.
- **W16 (§14 của amendment).**
  - *Tiền đề đọc từ đề đã che mệnh đề mục tiêu.* `shape_constraint.khoang_muc_tieu` /
    `che_muc_tieu` che các mệnh đề `chứng minh`, `chứng tỏ`, `CMR`, `kiểm tra`, `hỏi` và
    câu kết bằng `?`; việc khớp làm trên bản NFC theo từng cụm. Bản che giữ nguyên độ
    dài, nên span của mọi bộ đọc vẫn trỏ đúng đề gốc. Ràng buộc đọc được trong mục tiêu
    không là tiền đề nhưng VẪN chặn phản ví dụ.
  - *Literal của `construct_plane_from_equation` gắn với đúng mặt phẳng đề*
    (`assumption_gate.gan_mat_phang`). Gắn theo tên viết trong mệnh đề phương trình
    (`plane_equation.doc_mat_phang_de`, `ten_mat_phang_cua_bien`), hoặc duy nhất theo đếm
    (`so_lan_nhac_mat_phang`). Không gắn được thì không có vai trò, detail ghi
    `PLANE_BINDING`.
  - *Không đổi:* `SourceInvariant plane_equation` của sản phẩm và hậu điều kiện của nó.
- **W17 (§15 của amendment).**
  - *Phép cắt gắn với câu cắt của đề.* `shape_constraint.doc_quan_he_cat` đọc câu cắt trên
    đề đã che mục tiêu, theo từ vựng ĐÓNG (ba lối nói; tân ngữ của "song song/vuông góc với
    (X)" không bao giờ là mặt phẳng cắt). `assumption_gate._kiem_phep_dung` đòi mọi
    `construct_section` trên lát cắt dùng CÙNG danh tính mặt phẳng và CÙNG khối với câu cắt.
    Danh tính mặt phẳng: theo nguồn `source_fact_id`, rồi tên hoặc duy nhất; mặt phẳng gọi
    qua điểm là tập điểm. Danh tính khối: tập đỉnh. Lệch chắc chắn (hai danh tính đều biết
    và khác nhau) ⇒ `CONSTRUCTION_NOT_TEXT_BOUND`; không ghim được ⇒
    `ASSUMPTION_INVARIANCE_UNPROVEN`.
  - *Grounding đọc trên đề đã che mục tiêu ở MỌI vùng* (`grounding_gate.check_grounding`).
    Lượt thứ hai trên đề gốc chỉ PHÂN LOẠI lời từ chối là `GIVEN_ONLY_IN_GOAL_CLAUSE`.
  - *Nguyên nhân từ chối có cấu trúc* (`refusal_cause.py`): SOURCE / CONSTRUCTION / UNKNOWN
    theo mã đăng ký; `learner_messages` chọn lời theo nguyên nhân, chỉ SOURCE bảo sửa đề.
  - *Số đo trên hình.* Backend gắn đại lượng ↔ chủ thể (`quantity_annotations.gan_so_do` →
    `annotation` trên vật cảnh). Frontend chỉ chiếu, đặt chỗ và bật/tắt
    (`scene3d-annotations.ts::placeAnnotationLabels`), không suy luận hình học.
- **W18 (§16 của amendment).**
  - *Phép dựng điểm gắn với quan hệ của đề.* Thứ tự route: execution → realized_coverage →
    **`construction_binding`** → source_invariant → postconditions → assumption → …
    `construction_binding.doc_quan_he_dung` đọc quan hệ trung điểm (cả danh sách "lần lượt")
    và hình chiếu/chân đường vuông góc trên đề đã che mục tiêu, theo từ vựng ĐÓNG.
    `doi_chieu_phep_dung` đối chiếu từng phép dựng điểm theo DANH TÍNH, dùng các thẩm quyền
    sẵn có: bí danh, `assumption_gate._khoa`, nhãn, fact nguồn, lưới hoà giải. Trùng toạ độ
    hay trùng giá trị không bao giờ là trùng thực thể.
  - *Phán quyết.* MISMATCHED ⇒ từ chối ở MỌI vùng (`CONSTRUCTION_NOT_TEXT_BOUND`, nguyên nhân
    CONSTRUCTION). UNVERIFIED ⇒ từ chối trong U3 (`CONSTRUCTION_BINDING_UNVERIFIED`, nguyên
    nhân UNKNOWN, không gửi đi sửa). Bất biến toạ độ `segment_division` giữ làm lưới thứ hai.
  - *Dữ liệu trình bày do backend sở hữu:* `annotation.role`; `same_as` theo cùng chủ thể;
    nhân chứng khoảng cách (chân chính xác từ `kernel.project_point_onto_line/plane`);
    `source.binding` của điểm dựng; ký hiệu `S(T)`. Frontend chỉ lọc theo lựa chọn và
    "Hiện tất cả", đặt chỗ và vẽ, không tính chân (guard 5D).
- **W20 (§17 của amendment).** Đích của quan hệ mà chương trình đặt bằng TOẠ ĐỘ — của chính tên
  ấy hay của điểm nó là bí danh (`assign X = var Y`), kể cả rồi mới dựng lại, kể cả lấy trùng một
  đỉnh đề cho — có trạng thái `DEFINED_BY_COORDINATES` và bị từ chối ở MỌI vùng
  (`CONSTRUCTION_REPLACED_BY_COORDINATES`, nguyên nhân CONSTRUCTION, không gửi đi sửa). Module chỉ
  hỏi CÓ toạ độ, không đọc giá trị. Grounding ⑥/⑦ vẫn chặn sớm hơn các ca của chúng.
- **Thi hành.** Từ chối ở chặng `assumption` (`INPUT_NOT_GROUNDED`;
  `ASSUMPTION_DETERMINES_ANSWER` nêu đại lượng thiếu, hoặc `ASSUMPTION_INVARIANCE_UNPROVEN`);
  `pipeline.KHONG_SUA_NGUON` không gửi đi sửa; `learner_messages` có hai câu tiếng Việt.
  U3: chỉ TỪ CHỐI khi `neu_khoi_da_dien` đúng; ngoài vùng ghi `assumption_enforced = false`.
  U5: `CLOSURE_MULTIPLE_DEFINITIONS` bị từ chối ở MỌI vùng. Lỗi bên trong cổng ⇒ từ chối
  có mã trong vùng, không bao giờ HTTP 500.
- **Phần tô thiết diện khép kín** là vật riêng `section_fill:<id>`. Thứ tự vẽ là
  `THU_TU_TO_THIET_DIEN = 7` (W16): sau mặt khối và mặt cắt, TRƯỚC mọi nét trong suốt. Vì
  vậy cạnh khối chuẩn vẽ đè lên phần tô; ở thứ tự 10 của W15, phần tô phủ hổ phách lên
  cạnh. Nét liền thuộc hàng đợi đục vẫn đi trước cả hàng đợi trong suốt
  (`ISSUE-ARCH-SECTION-FILL-OPAQUE-AUXILIARY-LINES`). Phần tô KHÔNG kiểm và KHÔNG ghi chiều
  sâu. Thiết diện nằm TRONG khối, mà lớp chiều sâu đục
  của khối chạy trước toàn bộ hàng đợi trong suốt; kiểm chiều sâu thì phần tô bị loại ở
  mọi điểm ảnh. Viền thiết diện vẫn hai lượt thấy/khuất. Móc đo
  `__geo3d_set_section_fill_visible` chỉ dành cho harness.
- **Bằng chứng (U2).** `measure_scene3d_occlusion --pending-human-review`: cảnh mà người đã
  duyệt trên hình CŨ được tính `HUMAN_REVIEW_PENDING`, không tính lỗi. Điều kiện: oracle
  độc lập tái hiện tập đã duyệt ở camera đăng ký lẫn camera mới, và sản phẩm = oracle trên
  mọi trạng thái; khác đi là lỗi. Registry người không bao giờ bị sửa.

**Ranh giới R0 nằm ngay sau bước sinh chương trình ngữ nghĩa.** Không có lượt gọi model nào sau đó; `servable` quyết định có phát canonical.

Chi tiết dành cho khoá luận — sơ đồ, vùng LLM/tất định, đường từ chối:
**`docs/research/thesis/THESIS_ARCHITECTURE.md`**.

> ⛔ **Luồng CŨ (miền Tin học) đã gỡ**, giữ lại đây một dòng để tra lịch sử:
> `stage_analyze` → `representation` (plan + capability gate) → `stage_classify`
> → 4 cổng (computation · mechanism · input-sufficiency · completeness) →
> `[pattern reuse]` hoặc `stage_simulate` → validate 2 tầng
> (`dsl/validator.py` + `validation/` — đã gỡ). Con đường thứ ba — chỉnh sửa tăng dần
> qua `SimulationPatch` (`/api/edit`) — cũng đã gỡ cùng `patch.py`/`edit_policy.py`.
> Không cổng nào trong số đó **phán quyết được** về một đề hình học; xem
> docstring `pipeline._chay_duong_hinh_hoc`.

## 3. Sở hữu sự thật (source-of-truth ownership)

| Thứ | Ai sở hữu | Ghi chú |
|---|---|---|
| Thẩm quyền KIỂU của IR | `semantic_program/ir_static_check.py` — `_CHU_KY` · `_KIEU_DUNG` · `_TOAN_HANG_LENH` | mọi allowlist/enum/prompt/thẻ văn phạm **dẫn xuất** từ đây |
| Thẩm quyền PHÉP ĐO | `semantic_program/measure_contract.py::BANG_PHEP_DO` → `_KIEU_DO` | đo đại lượng gì, *của* gì, *so với* gì |
| Luật hợp lệ của spec | `semantic_program/contract.py` (Pydantic) + `ir_static_check.kiem_tinh` (+ mirror JSON Schema, hai bản) | lược đồ rồi mới tới thẩm định tĩnh |
| Timeline / state / kết quả | **engine tất định** (`semantic_program/interpreter.py` + `simulation/geometry/`) | LLM **không bao giờ** |
| Đại lượng (khoảng cách, góc, thể tích) | `simulation/geometry/measure.py` — `Fraction` + `Radical` | **không có `float`** trong miền hình học |
| **Chương trình ngữ nghĩa (IR)** | LLM tổng hợp, **server đóng băng nghĩa vụ trước** (`RequestContract`) | IR là *chương trình ứng viên*; chạy nó KHÔNG phải việc của LLM |
| **Trace thực thi** | `semantic_program/interpreter.py` — **authority tất định** | ngân sách **thực thi**; chạm trần phải BÁO |
| **Khung hình (frame)** | `semantic_program/visual_adapter.py` | song ánh `frame k ⇔ trace[k]` — điều kiện để bất biến #31 là định lý |
| **Topology + trạng thái đỉnh của `graph_view`** | `visual_adapter.py` đọc `memory_snapshot`; chương trình KHAI BÁO biến mang trạng thái (`visited_ref`/`current_ref`) | renderer **cấm** tự chạy lại BFS/DFS — làm thế là dựng engine thứ hai ở tầng trình bày |
| **Bước xem (view step)** | `semantic_program/pacer.py` | ngân sách **trình bày**, tách hẳn ngân sách thực thi; gộp KHÔNG bỏ |
| Vị trí object lúc chạy | `GenericState.pos` (engine-owned, **toạ độ miền 0–100**) | spec bất biến; drag chỉ đổi state |
| **Bố cục/kích thước canvas** | **RENDERER** — không bao giờ là engine state | xem quy tắc renderer-neutral bên dưới |
| Định tuyến bài → mô phỏng | `domain_profile.co_duong_thuc_thi` (TẤT ĐỊNH, 0 lượt gọi) | không còn classify; đề không ánh xạ tới nghĩa vụ có checker ⇒ chặn trước mọi lượt gọi |
| Phán quyết "có phát hay không" | `route.verify_and_compile` → `servable` | `executable` mà `not servable` = `verification_gap`, **không** được gộp |
| Đúng/sai của thao tác học sinh | **chỉ rule tất định** | không có rule → `unsupported_to_verify` |
| Cấu hình đang chạy | store (`active.config`) — **opaque**, bất biến | store mù domain |
| **Visual mode (2D/3D) đang hiển thị** | store — **lát trình bày** (`visualMode`, cạnh `leftOpen`) | M8: không bao giờ vào engine state/spec; **không do LLM chọn**; đổi mode không đụng active/cursor/prediction |
| Renderer khả dụng của một module | hợp đồng module (`supportedVisualModes` ∩ `renderers`) qua `simulations/renderer.ts` | **cấm** switch-case theo simulation_id |
| Mặt trình bày đang mở (home/workspace/history) | store — `view` (M9-UX1) | như visualMode: trình bày thuần, không đụng engine |
| **Chế độ học sinh đang mở (Khám phá / Thử thách)** | store — `exploreOpen` / `challengeOpen` (W4B-3A), **mù domain** | HAI cờ vì hai chế độ khác nhau ở chỗ AI PHÁN XÉT (xem bất biến #24); trước đây là `useState` cục bộ tên `labOpen` trong hai renderer miền |
| **Chỗ đặt lối vào hai chế độ** | `components/SimulationControls.tsx` — chủ sở hữu **DUY NHẤT** | renderer miền **cấm** dựng `sim-secondary-action`; miền chỉ cấp CÂU MỜI qua `predict.entry`/`explore.entry` |
| **Lịch sử học BỀN** | `state/history.ts` → localStorage (schema v1, whitelist) | M9-UX1: envelope ĐÃ VALIDATE + tiến độ trình bày an toàn (lastCursor/visualMode); **runtime reset/goHome không phá lịch sử** |

## 3b. Quy tắc RENDERER-NEUTRAL STATE (M7.FREEZE — điều kiện để có 3D)

**Engine state chỉ chứa sự thật NGỮ NGHĨA. Bố cục là chuyện của renderer.**

- Vị trí trong không gian **mô phỏng** (vd `GenericState.pos`, toạ độ miền 0–100)
  là ngữ nghĩa → ở engine. **Toạ độ pixel / kích thước canvas / viewBox** là
  trình bày → **cấm** nằm trong state.
- Diễn biến chuyển động diễn đạt bằng **định danh ngữ nghĩa**, không bằng toạ độ:
  `Frame.entityPos: entityId → **nodeId**` (generic) và `NetStep.packetAt =
  **nodeId**` (network). Nhờ vậy renderer 3D tính vị trí riêng mà **dùng lại
  nguyên state**.
- 2D và 3D **dùng chung** config/state/timeline/action của **cùng một module**.
  **Không** tạo `simulation_id` riêng cho 3D, **không** fork engine.

*Tiền lệ đã sửa (M7.FREEZE):* `NetworkState` từng chứa `positions` là **toạ độ
pixel** do `layout()` sinh (COL=150, X0=80…) — dữ liệu trình bày lọt vào state
quyền uy. Nay `layout2d` sống trong `network/ui.tsx`; state chỉ còn topology +
route (BFS) + steps + cursor. Khóa bằng test: state không được chứa
`positions/width/height` hay bất kỳ `"x"/"y"` số nào.

*Quy tắc này ĐÃ ĐƯỢC HIỆN THỰC HÓA (M8):* `network/ui3d.tsx` là renderer 3D
(Three.js) đọc **nguyên** NetworkState đó — `layout3d` (nodeId → Vector3),
camera, mesh, nội suy chuyển động đều renderer-owned trong ref/closure của
component; state không thêm một trường nào (khoá bởi `render3d.test.tsx`).
Renderer 3D được phép **nội suy hình ảnh** giữa hai bước ngữ nghĩa nhưng không
bịa trạng thái trung gian: sự thật vẫn là `packetAt` của bước hiện tại.

## 4. Hướng phụ thuộc (không được đảo)

```
manifest ← validator ← catalog ← pipeline ← main
manifest ← representation / semantic / patterns / patch
types ← registry ← store ← components
module (domain) → types/registry;  renderer → state (chỉ ĐỌC)

# Route sinh ngữ nghĩa (2026-08-20) — KHÔNG được đảo:
contract ← validator ← interpreter ← visual_adapter ← pacer ← envelope
```

Renderer **không bao giờ** nắm state quyền uy; nó phát `SimAction` và đọc lại.
Store **không** biết domain (không import Trace/SimulationSpec/mảng).

## 5. Bất biến (mỗi cái kèm nơi thực thi + test khóa)

> **Đối chiếu con trỏ (2026-10-05, run `cuboid-acceptance`).** Ghi chú của `cuboid-final-review` đếm 22 hàng có
> con trỏ chết; đúng là **24** — #9 và #12 ghi "như trên" nên thừa hưởng con trỏ chết của #8 và #11. Cả 24 hàng đã
> đối chiếu từng hàng (yêu cầu · miền áp dụng · cài đặt · assertion cụ thể): **9 đang khoá** (#1, #2, #3, #8, #9, #11,
> #21, #22, #29 — hai cột cuối nay chỉ nêu file còn sống), **1 chưa đủ bằng chứng** (#14, nhãn **UNVERIFIED**,
> `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM`), **14 lịch sử** (nhãn **LỊCH SỬ** đầu hàng: chủ thể của yêu cầu không còn tới
> được sản phẩm, hoặc một hàng sau đã thay — lý do, bằng chứng tuyến sản phẩm và hàng kế nhiệm ở cột "Thực thi ở"),
> **0 vi phạm**. Chữ ở cột yêu cầu giữ nguyên văn (kể cả các con số của danh mục cũ trong hàng lịch sử); nội dung cũ
> của hai cột con trỏ — ở #18, #20–#26 gồm cả phần diễn giải — đọc ở bản đồ tại `903e874c`. Con trỏ cũ và commit gỡ
> từng file:
> [`INVARIANT_RECONCILIATION.json`](evaluation/geometry/runs/cuboid-acceptance/results/INVARIANT_RECONCILIATION.json)
> (và bản đồ tại `903e874c`). Số hàng giữ nguyên vì mã và test trích theo số.

| # | Bất biến | Thực thi ở | Test |
|---|---|---|---|
| 1 | LLM không phải nguồn state runtime | `contract.py` (câu lệnh dựng không có trường kết quả; biểu thức hình học chỉ nhận TÊN) + `validator.py::validate_semantic_program` (cấm gán literal cho kiểu hình học) + `geometry_exec.py` (không import tầng AI) + `pipeline_adapter.py::compile_semantic_program_to_envelope` (khung từ trace, #31); kênh toạ độ điểm gốc do #36/#37 chặn | `test_geometry_ir.py::test_R0_cau_lenh_dung_KHONG_co_truong_toa_do_ket_qua` · `test_geometry_ir.py::test_R0_bieu_thuc_hinh_hoc_chi_nhan_TEN` · `test_geometry_ir.py::test_R0_geometry_exec_khong_import_tang_AI` · `test_refusal_truthful.py::test_moi_kieu_hinh_hoc_deu_CAM_gan_literal` · `test_frame_state_invariant.py` |
| 2 | Engine tất định là nguồn chân lý | `exact.py` → predicates → kernel → measure (số học chính xác) + `interpreter.py`; oracle cài độc lập `geometry_oracle.py` | `test_geometry_kernel.py::test_toa_do_la_HUU_TI_khong_phai_float` · `test_geometry_kernel.py::test_dong_phang_o_ca_ma_FLOAT_TRA_LOI_SAI` · `test_oracle_independence.py` (không import mã sản phẩm; khớp kernel; bắt được thiết diện bị tiêm lỗi) · `interaction-state.test.ts` (E: bung hình không đổi số nào; J: cùng bước ⇒ cùng kết quả) |
| 3 | Renderer không sở hữu state | `Scene3DExplorer.tsx` vẽ `scene3d` của envelope tại một bước (`scene3d-model.ts::objectsAt`); chọn/tua/bung/ẩn là biến đổi trình bày (`interaction-state.ts`); tên hiển thị do backend (`display_names.py`). Đường 2D dự phòng vẫn qua `WorkspaceProps` | `interaction-state.test.ts` (E, J) · `scene3d-geometry-timeline.test.tsx` (tua tiến/lùi) · `semantic-dumb-frontend.test.ts` · `test_frame_state_invariant.py` |
| 4 | **LỊCH SỬ** — Manifest là từ vựng capability | Không áp dụng: manifest DSL và enum dẫn xuất đã gỡ (`e664f683`, 2026-09-02). Kế nhiệm: từ vựng IR một nguồn `contract.py` → hai bản xuất (`export_semantic_program_schema.py`); năng lực sản phẩm `product_capability.py` | kế nhiệm: `test_schema_sync.py` |
| 5 | **LỊCH SỬ** — Specialized **không** bị chặn bởi gap của DSL generic | Không áp dụng: không còn module specialized lẫn DSL generic — registry có đúng một module, `run_pipeline` không còn nhánh Tin học (gỡ `6d5f5fda`) | bằng chứng: `registry.test.ts` · `test_geometry_route_independence.py` |
| 6 | **LỊCH SỬ** — Pattern reuse chỉ **sau classify**, chỉ `generic.rule_scene` | Không áp dụng: pattern store, classify và `generic.rule_scene` đã gỡ (`e664f683`, `6d5f5fda`) | bằng chứng: `test_geometry_route_independence.py` (classify bị cấm trên tuyến hình học) |
| 7 | **LỊCH SỬ** — Reuse **không** bypass validation (4 cổng) | Không áp dụng: pattern reuse đã gỡ (`e664f683`). Cache phản hồi của `/api/analyze` là cơ chế riêng có từ trước (chỉ cache `status == "ok"`, khoá theo `CACHE_VERSION`, bump quyết bằng bằng chứng), không thuộc hàng này | liên quan: `test_api.py::test_cache_version_9_cu_bi_invalidate_sau_bump_10` · `test_api.py::test_khong_cache_ket_qua_unsupported` |
| 8 | Thà `capability_gap` còn hơn mô phỏng xấp xỉ gây hiểu lầm | `domain_profile.py::detect_domain` (không phải hình học ⇒ đóng) · `coverage_gate.py` (C₁a/C₁b) · `grounding_gate.py::check_grounding` · `assumption_gate.py::kiem_gia_dinh` · `construction_binding.py::doi_chieu_phep_dung` · `product_capability.py` · thứ tự chặng `route.py::verify_and_compile` | `test_geometry_coverage_gate.py` (khai hay gán thẳng đáp án ⇒ trượt) · `test_assumption_gate.py` (kênh `LAYOUT_DERIVED` bị từ chối; hết ngân sách không thành an toàn) · `test_construction_binding.py` · `test_source_grounding_closure.py` |
| 9 | Canonical simulation: đúng hoặc từ chối trung thực | đáp số phục vụ qua `geometry_obligations.py::GEOMETRY_CHECKERS` + hậu điều kiện; lời từ chối mang chặng, mã và câu chọn theo mã (`learner_messages.py`, `refusal_cause.py`) | `test_product_response_contract.py` · `test_refusal_truthful.py` · `test_oracle_independence.py` · trình duyệt: `BROWSER_REFUSAL_CFR.json` (run `cuboid-final-review`) |
| 10 | **LỊCH SỬ** — Learner **được phép sai** | Không áp dụng: không thao tác nào của học sinh đổi được mô hình — module duy nhất có `apply` đồng nhất, không khai `explore`; tương tác Scene3D là chọn/tua/bung (kéo nằm ngoài phạm vi, #31); W13 gỡ `predict`. Test cũ gỡ ở `6703c48a` | bằng chứng: `registry.test.ts` · `interaction-state.test.ts` (E) · `no-verdict.test.ts` |
| 11 | Chỉ engine/rule tất định mới phán đúng/sai | mọi phán đúng/sai còn lại là của mã tất định: `geometry_obligations.py::GEOMETRY_CHECKERS`, hậu điều kiện, oracle; không còn bề mặt phán quyết cho học sinh (W13) | `no-verdict.test.ts` · `test_geometry_obligations.py` · `test_geometry_ir.py::test_R0_geometry_exec_khong_import_tang_AI` |
| 12 | **LỊCH SỬ** — Feedback là **state data**, không phải lượt chat | Không áp dụng: sản phẩm hình học không phản hồi thao tác của học sinh; lời còn lại (từ chối) chọn theo mã (#9); panel chat và `/api/explain` đã gỡ (run `repo-cleanup`; route trả 404, khoá ở `test_api.py::test_endpoint_tutor_flow_da_xoa`) | bằng chứng: `ux-shell.test.tsx` (panel Giải thích không còn control AI) · `test_product_response_contract.py` |
| 13 | `pytest`/`vitest` mặc định = **0 call AI thật** | `backend/conftest.py`, `frontend/src/test-setup.ts` | `test_offline_guard.py`, `offline-guard.test.ts` |
| 14 | **UNVERIFIED** — Live eval là **opt-in**, không phải thói quen | `conftest.py` của backend (bộ test mặc định 0 lượt gọi, #13) + opt-in theo từng script (`ALLOW_LIVE_AI` ở 30 script; `--live` hoặc `--execute-live --confirm-live-execution` ở 5). **Chưa đủ bằng chứng:** không khoá nào phủ cả `backend/scripts`; `run_live_gemini_semantic_smoke.py` đã retire, còn `run_rectangular_pyramid_live_analyze.py` gọi live không cần opt-in (dò tĩnh, chưa tái hiện bằng lượt chạy) — `ISSUE-OPS-LIVE-OPT-IN-NOT-UNIFORM` | `test_geometry_dev_runner.py::test_khong_co_ALLOW_LIVE_AI_thi_TU_CHOI` · `test_holdout_protocol.py::test_khong_co_con_dau_thi_KHONG_chay_duoc` · `test_offline_guard.py` |
| 15 | **LỊCH SỬ** — Patch fail → spec hiện tại **nguyên vẹn** | Không áp dụng: `/api/edit` đã gỡ (chú thích có ngày trong `main.py`) — config hình học là artifact đã biên dịch, không phải đặc tả để vá; mã patch gỡ ở `e664f683` | bằng chứng: không còn mã nào gọi `/api/edit` (client `editViaServer` gỡ ở run `repo-cleanup`) |
| 16 | **LỊCH SỬ** — **3D là renderer, không phải domain** (M8): 2D/3D dùng chung module/config/state/timeline/action/prediction; `visualMode` là trình bày thuần; renderer khả dụng dẫn xuất từ hợp đồng module | Không áp dụng: toggle 2D/3D trên các module Tin học đã gỡ (`6703c48a`); `SimulationWorkspace.tsx` trả `Scene3DExplorer` khi envelope có `scene3d` hợp lệ, trước logic chế độ 2D. Kế nhiệm: #31 và #35 | kế nhiệm: `test_frame_state_invariant.py` · `scene3d-geometry-timeline.test.tsx` |
| 17 | **Mở lại từ lịch sử = ZERO-AI** (M9-UX1): lưu envelope ĐÃ VALIDATE, mở lại qua `loadEnvelope` + engine tất định — không đi pipeline, không LLM; chỉ persist trường whitelist (không prediction/branch/camera/secret); runtime reset không phá lịch sử | `state/history.ts` + `store.reopenFromHistory` | `history.test.ts`, `view-history.test.tsx` |
| 18 | **LỊCH SỬ** — **Nghĩa của chiều sâu 3D phải TRUNG THỰC, và chỉ nghĩa SƯ PHẠM mới được bày cho học sinh** (M10, siết ở W4B-2R): module có 3D khai `threeD.role` = `pedagogical` (Z mã hoá biến khái niệm thật — `network.protocol_encapsulation`: **Z = tầng giao thức**, X = chiều truyền). W4B-2R nâng M10 từ *khai báo trung thực* lên *chính sách*: `architectural_poc` (Z chỉ là bố cục) **KHÔNG đủ tư cách bày toggle 2D/3D** — đó chính là `2D_AND_3D_BY_DEFAULT`. Tiền lệ: `network.packet_routing` tự khai `architectural_poc` + `meaningOfZ = "bố cục, không mang nghĩa khái niệm"`, nên W4B-2R **hạ nó về 2D_ONLY và gỡ `ui3d.tsx`**. Danh mục nay **22 × 2D_ONLY · 0 × 3D_ONLY · 1 × 2D_AND_3D_JUSTIFIED**. PDU là state ngữ nghĩa dùng chung (2D+3D đọc cùng), 3D không tính lại PDU | Không áp dụng như đã viết: chính sách biểu diễn quản các module Tin học tự chọn nghĩa cho Z; ở hình học Z là toạ độ thật từ kernel chính xác. Glyph mạng và hai test gỡ ở `6703c48a`; `threeD` và `representationPolicyOf` còn sót trong `types.ts`, `renderer.ts`, không module nào khai. Kế nhiệm: hợp đồng khuất/hiện `OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md` (sản phẩm phân loại, oracle độc lập kiểm) | kế nhiệm: `scene3d-occlusion-gates.test.ts`; bốn cảnh W14 đổi còn chờ người duyệt (`ISSUE-EVAL-HUMAN-VISIBILITY-REGISTRY-PREDATES-S4`) |
| 19 | **Alembic sở hữu schema Postgres bền** (DB-HARDEN-2, *chất lượng triển khai — không phải đóng góp học thuật*): tạo & tiến hoá schema PostgreSQL do **Alembic** sở hữu DUY NHẤT (`alembic upgrade head` ở entrypoint Docker). `create_all()` chỉ dành cho SQLite ephemeral/test, KHÔNG phải cơ chế migration của Postgres; runtime **không** lặng lẽ `create_all()` trên Postgres (quyết định theo `engine.dialect.name`, không string-check URL). Không tự động `stamp` DB lạ | `db.py::init_db` (gate qua `sqlite_owns_schema`) + entrypoint Docker | `test_db_ownership.py`, `test_migration_drift.py` (cổng chống trôi, có fault-injection proof), `test_postgres_integration.py` (smoke opt-in) |
| 20 | **LỊCH SỬ** — **Toán hạng numeric/logical của một rule generic phải có nguồn giá trị theo hợp đồng ngữ nghĩa DẪN XUẤT TỪ MANIFEST — không có thì reject, không bao giờ hoá 0 im lặng** (M13): validator hai tầng từ chối operand không phải *value-provider* của role rule cần (`INVALID_SOURCE` — vd `edge`/`node` không có `value`) và từ chối derived-target sai role theo `role_satisfies()` — subtyping **MỘT CHIỀU** dẫn xuất từ `role_compatibility` trong contract (M13 hotfix: `logical` satisfies `numeric` — boolean executor sinh đúng 0/1, KHÔNG runtime conversion; vd `weighted_sum` numeric vẫn không được ghi vào `node` relational). Mọi cặp khác **DENY mặc định**; chiều ngược `numeric ↛ logical` LUÔN deny (đó chính là coercion ngầm `v>=1` mà check này sinh ra để diệt) — chỉ mở cặp mới khi matrix audit chứng minh được fixture thật; runtime hai tầng KHÔNG BAO GIỜ seed/fallback một giá trị thiếu/chưa resolve thành 0 — ném lỗi TYPED fail-closed tại ranh giới evaluator (4 mã: `invalid_numeric_source` / `missing_weight` / `unresolved_dependency_after_bound` / `non_finite_numeric_value`). Sự cố gốc đã sửa: `weighted_sum` ăn input là id một `edge` (fixture "pseudo-Dijkstra" — TÁI DỰNG, artifact gốc không khôi phục được từ cache/localStorage) từng lặng lẽ hoá 0 → cảnh "chạy" đủ bước, kết quả sai câm; validator siết chặt tự động bảo vệ luôn cả đường pattern-reuse (fixture cũ mang shape cấm bị chặn ngay ở cổng 1 `run_gates`, không cần sửa riêng) | Không áp dụng: rule generic, DSL và hợp đồng dẫn xuất từ manifest đã gỡ (`e664f683`, `6703c48a`). Kế nhiệm trong IR: toán hạng là TÊN; validator và static check từ chối tên chưa khai, sai kiểu, dùng trước khi dựng, bằng mã có kiểu; phép dựng hỏng làm chương trình hỏng | kế nhiệm: `test_geometry_ir.py::test_tham_chieu_ten_KHONG_KHAI_bi_VALIDATOR_bat_tinh` · `test_geometry_ir.py::test_dung_SAI_KIEU_thi_hong` · `test_geometry_ir.py::test_giao_duong_CHEO_NHAU_thi_chuong_trinh_HONG` |
| 22 | **Bộ đo phải gọi đúng production orchestration của `/api/analyze`; không tái dựng riêng chuỗi analyze → synthesize → gate → execute.** Observer chỉ được thu event, không đổi routing/retry/gate/output; `observer=None` phải giữ hành vi sản phẩm. Runner nghiệm thu hiện hành gọi các stage sản phẩm và cửa `route.py::verify_and_compile`; bằng chứng catalog Tin học M14/M16 đã retire sau khi consumer nghiên cứu của nó kết thúc. | `pipeline.py::run_pipeline` · `run_thesis_final_acceptance.py` · `semantic_program/route.py::verify_and_compile` | `test_synthesis_repair_trace.py::test_F2_pipeline__final_memory_chuong_trinh_so_luot_GIONG_khi_co_observer` · `test_thesis_runner_alignment.py` |
| 23 | **LỊCH SỬ** — **Mechanism ownership được khai ở mức FamilyMembership; mechanism taxonomy dùng canonical namespaced IDs với một compatibility alias boundary duy nhất; consistency gate so sánh tín hiệu cơ chế có cấu trúc trên final route sau bounded reclassification** (M15). Giải thích: family mới khai `owned_mechanisms` máy-đọc-được ngay trên membership; giá trị analyze legacy được normalize tại ĐÚNG MỘT chỗ (`canonical_mechanism` — alias một chiều, không phải taxonomy thứ hai); gate và descriptor CHỈ so canonical values; route-consistency chạy trên FINAL route (không route-dependent gate nào chạy trên route tạm — `analyze → classify → recovery ≤1 reclassify → FINAL ROUTE → gates → simulate`); cơ chế không sở hữu → retry có giới hạn (cross-family mismatch, `ROUTE_MECHANISM_FAMILY_MISMATCH`) hoặc fail-closed `capability_gap` (cùng-family unowned, `GATE_MECHANISM_OWNERSHIP`); định tuyến KHÔNG dựa keyword-patch — chỉ so tín hiệu cấu trúc. Giá trị analyze-exposed không ai sở hữu phải khai tường minh trong `INTENTIONAL_GAP_MECHANISMS` (owned XOR intentional-gap) | Không áp dụng: classify, họ và taxonomy cơ chế đã gỡ (`e664f683`, `6d5f5fda`); tuyến hình học không classify (`domain_profile.py::detect_domain` tất định) | bằng chứng: `test_geometry_route_independence.py` (vòng phục hồi của classifier nằm trong danh sách tên bị cấm trên tuyến hình học) |
| 21 | *Đang khoá ở dạng hiện hành (2026-10-05): yêu cầu giữ nguyên, cơ chế đổi — cổng phủ C₁a/C₁b; phần cơ chế M13 dưới đây là lịch sử.* **Yêu cầu tính-kết-quả-thuật-toán mà không có executor tất định nào sở hữu → `capability_gap` trên đường generic, KHÔNG dựng cảnh minh hoạ đáp án** (M13): SERVER ra phán quyết cuối, tất định, trên **tín hiệu CÓ CẤU TRÚC** — hai kênh bổ sung nhau: (1) `known_gap_roles()` lọt vào `unsupported_capabilities` của representation plan (vd role `arbitrary_algorithm`); (2) `analysis.result_ownership` **fail-closed** — chỉ `"provided"`/`"rule_derivable"` được đi tiếp, `"algorithmic"` HOẶC thiếu/ngoài enum đều → gap (không default sang giá trị nào). Kênh 2 bắt được cả khi kênh 1 bị bỏ sót role (không phụ thuộc MỘT kênh prompt duy nhất). Giữ nguyên carve-out chuyên biệt (bất biến #5 — gap của DSL generic không lây sang specialized). Đây là lớp phòng thủ TRƯỚC khi simulate chạy (chặn ở classify/analyze), bổ sung — không thay thế — invariant #20 (chặn Ở VALIDATOR nếu vẫn lọt qua tới đó); artifact "pseudo-Dijkstra" là ca cụ thể bị #20 chặn, còn #21 là cơ chế chặn SỚM HƠN dựa trên ý định của đề bài | `coverage_gate.py` — C₁a: mọi nghĩa vụ cần một bước phủ; C₁b: nhân chứng phải dẫn xuất từ dữ liệu, đáp án khai hay gán thẳng bị từ chối; họ ngoài phạm vi: `product_capability.py`. Cơ chế M13 gỡ ở `e664f683` | `test_geometry_coverage_gate.py` (khai/gán thẳng đáp án ⇒ trượt; phụ thuộc rỗng ⇒ cả ca đúng cũng trượt — khoá hồi quy) · `test_coverage_gate_c1a.py` |

| 24 | **LỊCH SỬ** — **KHÁM PHÁ và THỬ THÁCH là hai trách nhiệm khác nhau, phân biệt bằng AI PHÁN XÉT — và LỐI VÀO của chúng thuộc shell, không thuộc renderer miền** (W4B-3A). Thử thách: học sinh CAM KẾT một quyết định, `predict.check` (engine tất định) phán đúng/sai. Khám phá: học sinh ĐỔI mô hình, `module.apply` tính lại, **không ai phán gì** — hệ quả tất định LÀ câu trả lời. Một cửa cho cả hai dạy học sinh rằng kéo một cột cũng là "trả lời đúng/sai". Sự cố gốc: cả hai từng nằm sau MỘT `useState` cục bộ tên `labOpen` do renderer miền tự dựng nút mở, nên (a) dưới sân khấu luôn thừa một dải `experimentTrigger` (đo được ở 8 target thuật toán + `packet_routing`, cả 4 bề rộng), (b) chuyển phiên là mất chế độ, (c) SSR luôn thấy `false` nên không test nào chạm được trạng thái MỞ (xem §8 #13). Hệ quả kèm theo: `presentedInStage` từng tắt CẢ lối vào chứ không chỉ bề mặt thứ hai — đó mới là thứ ép miền phải tự dựng nút. Luật nay: `presentedInStage` chỉ chặn `PredictionBar`; **một cửa, nhiều nhất một bề mặt**; lối vào ở bước không dùng được thì **MỜ, không biến mất** (4/13 → 21/40 bước mời được tuỳ bài — tự gỡ mình là nhấp nháy). Store vẫn **mù domain**: nó giữ hai boolean và không biết "khám phá" ở bài này là kéo cột hay bấm liên kết mạng | Không áp dụng: Thử thách gỡ ở W13; không module nào khai `explore` (module duy nhất `generic.semantic_program`); đường Scene3D vẽ trước khay điều khiển 2D. Lối vào cũ gỡ ở `6703c48a`; mã Khám phá còn sót (`exploreOpen` trong `store.ts`, `exploreEntry`, nút trong `SimulationControls.tsx`) chờ quyết định H-W20-4 | bằng chứng: `no-verdict.test.ts` (store không còn `challengeOpen`) · `registry.test.ts` (một module) · `ux-shell.test.tsx` (khay 2D ẩn khi cảnh là 3D) |

| 25 | **LỊCH SỬ** — **Tiêu đề là ĐỀ BÀI, mô hình là thứ học sinh đang cầm — và khi hai bên lệch nhau thì màn hình phải NÓI RA** (W4B-4D). Trước khi có tham số đổi được, hai thứ này luôn trùng nên bất biến chưa cần tồn tại. Từ khi `count_if`/`sum_if` đổi được điều kiện, `tree`/`graph_traversal` đổi được cách duyệt, `database` đổi được truy vấn, `binary` đổi được cơ số/văn bản, thì đề viết "đếm học sinh **từ 8,0 trở lên**" trong khi mô hình đang đếm từ 6 — và con số cuối cùng đọc như đáp số của bài gốc. Đó là màn hình **khẳng định một điều sai**, không phải chuyện thẩm mỹ. Chủ sở hữu là SHELL, không phải từng miền: một chỗ so, một nhãn, không miền nào phải tự nhớ. Hai luật của phép so: (a) so bằng **GIÁ TRỊ** — mọi `apply` dựng config mới nên so tham chiếu sẽ báo "đã đổi" vĩnh viễn kể từ thao tác đầu, kể cả khi học sinh vừa quay về đúng chỗ cũ; (b) so **ĐÚNG các khoá module khai** — `web` giữ kiểu trong state nên phải tự dựng lại hình dạng config và nó không giữ `notes` của đề, so cả khối thì mọi đề có `notes` đều "đã đổi" ngay khi vừa mở. Nhãn kêu oan là nhãn bị học sinh học cách phớt lờ, đúng lúc nó cần được đọc. Module KHÔNG khai `currentConfig` ⇒ không so, không nhãn — bài không đổi được tham số thì không lệch được; và thao tác KHÔNG rời đề (bật một đầu vào của mạch logic) phải để nhãn IM | Không áp dụng: học sinh không đổi được tham số — `apply` đồng nhất, không khai `currentConfig` ⇒ `specDrift` luôn `false`; đường Scene3D trả về trước. Test gốc (spec-drift-w4b4d.test.tsx; bản đồ cũ ghi đuôi ts) và bảy module gỡ ở `6703c48a` | bằng chứng: `registry.test.ts` (một module) |

| 26 | **LỊCH SỬ** — **Một lối vào Khám phá phải dẫn tới thao tác CÓ HỆ QUẢ; và "thao tác được" phải đo bằng CỬA THẬT, không bằng cờ khai báo** (W4B-4A/4D). Hai vế của cùng một bất biến. Vế trình bày: module mời vào Khám phá mà không action nào đổi được mô hình thì lời mời là hứa suông (COVERAGE §2.6 cấm bày tương tác trang trí). Vế ĐO: phép đo phủ danh mục từng đọc `!!mod.explore`, mà **mọi** module thuật toán khai chung một khối `explore` — nên cờ ấy `true` kể cả ở bài `explore.entry()` trả `null` và học sinh không thấy cửa nào. Hệ quả đo được: `count_if`/`sum_if` tính là "thao tác được" suốt từ baseline nhờ `whatif_swap` mà chính sách của chúng TẮT — **dương tính giả**, và nó che mất việc hai bài này thật sự không có gì để khám phá. Đọc `explore.entry()` thì hết lọt. Kèm theo: quyết định GIỮ TRACE phải khai lý do **CƠ CHẾ** trong `KEEP_TRACE`, guard hai chiều (thiếu lý do là đỏ; lý do còn sót sau khi target đã có tương tác cũng đỏ — giải thích lỗi thời đánh lừa người đọc sau), và lý do nói "chưa kịp"/"TODO" bị từ chối | Không áp dụng: không còn lối vào Khám phá nào (#24); phép đo, chính sách tương tác và miền điều kiện gỡ ở `6703c48a` | bằng chứng: `registry.test.ts` |

| 27 | **Tầng lớp học ĐỌC bằng chứng, KHÔNG phán đúng/sai** (M18). Correctness thuộc về engine tất định và `predict.check`; LLM không phán, và bảng quan sát của giáo viên cũng không. Bảng đó chở TRẠNG THÁI CÓ CẤU TRÚC — vị trí trên timeline (đọc qua hợp đồng `timeline` của module, KHÔNG đọc renderer), cờ Khám phá/Thử thách đang mở, số thao tác, số lần đã cam kết — và không có trường nào tên `verdict`/`correct`/điểm. Cũng KHÔNG chiếu màn hình hay chụp DOM: nặng hơn, lộ nhiều thứ ngoài giờ học hơn, và buộc phải dựng một hạ tầng truyền hình ảnh mà kiến trúc này không có. Đọc màn hình thay vì đọc hợp đồng sẽ khiến bằng chứng lớp học đổi theo renderer nào đang vẽ và panel nào đang mở | `accounts/classroom_router.py::observe_class` + `components/PracticeReporter.tsx` (chuyển state engine → bằng chứng) + `persistence/classroom_models.py::PracticeSession` | `test_classroom_api.py` (bảng quan sát không chứa verdict/correct/score, không chứa screenshot/DOM; con số bị KẸP về miền hợp lệ thay vì tin client) · (đầu dò trình duyệt `accept-classroom-m18.mjs` gỡ ở run `repo-cleanup`: nó giao bài `logic.and_gate`, target router nay từ chối) |

| 28 | **Chữ của giáo viên không bao giờ thành sự thật runtime** (M18). Giao bài = giao một **envelope ĐÃ QUA `SimSpec.validate`**, đúng cổng mà pipeline LLM đi; lời dặn là CHỮ hiển thị cạnh mô phỏng. Hai hệ quả bắt buộc: (a) mở bài KHÔNG gọi LLM — sinh lại lúc mở nghĩa là ba mươi học sinh mở ra ba mươi mô phỏng khác nhau và giáo viên không giao được thứ mình đã xem; (b) config lưu là bản ĐÃ CHUẨN HOÁ của validator, không phải bản thô của client. Bỏ cổng này thì một config engine không chạy nổi sẽ nổ trên màn hình học sinh giữa tiết | `accounts/classroom_router.py::_validated_envelope` + `persistence/classroom_models.py::Assignment.envelope_json` | `test_classroom_api.py` (envelope sai config/target lạ/chưa phân tích xong đều 400; hai học sinh mở ra CÙNG một envelope) · (đầu dò trình duyệt `accept-classroom-m18.mjs` gỡ ở run `repo-cleanup`: nó giao bài `logic.and_gate`, target router nay từ chối) |

| 29 | **Vai trò do MÁY CHỦ sở hữu; thanh điều hướng ứng dụng nằm NGOÀI lưới workspace** (M18). Client gửi `role` gì cũng không đổi được quyền — server tra `users.role` theo phiên, và đăng ký thường luôn ra học sinh (vai trò giáo viên cần mã mời; không cấu hình ⇒ ĐÓNG). Vai trò ở frontend là bản chiếu để VẼ: sửa nó trong devtools thì thấy được thanh điều hướng giáo viên và không gọi nổi endpoint nào. Về bố cục: thanh điều hướng mới KHÔNG được lặp lại cột 208px đã gỡ ở W4B-3B — cột đó nằm TRONG lưới workspace nên nó trải qua cả hàng sân khấu lẫn hàng điều khiển và bóp cả hai. Thanh mới nằm ngoài lưới, thu gọn thành dải biểu tượng trong mô phỏng, và thành ngăn kéo tạm dưới 900px | `policy.py::resolve_signup_role` + `router.py` (`require_role`) của `accounts` + `TopNav.tsx::itemsForRole` — điều hướng là một hàng trong thanh trên, ngoài lưới workspace (cột trái `AppSidebar` thay bằng thanh trên ở `75b981d6`, 2026-09-03; luật "ngoài lưới" giữ nguyên) | `test_auth_api.py` (`TestVaiTro`: tự khai giáo viên bị chặn, thiếu cấu hình vẫn đóng; client gửi vai giáo viên không thành giáo viên) · `test_classroom_api.py` · `canvas-first-shell.test.tsx` (không còn cột thường trực; hàng điều hướng luôn hiện) · `ux-shell.test.tsx` (hai vai không chung thanh điều hướng) |

| 30 | **Khung mô phỏng lấy bề rộng từ CƠ CHẾ, và mọi thứ của cùng một cơ chế đứng trên MỘT rail** (M19). Trước wave này thẻ luôn 1624px @1920 trong khi mực dao động 276–1597px, và từng renderer tự căn giữa hình bên trong lớp giãn ấy — đo được 23/23 target hỏng, rail lệch tới 722px. Nguyên nhân là một: thẻ là flex column STRETCH nên con nào cũng giãn hết cửa sổ rồi phải tự căn giữa lại. Luật nay: cột nội dung + thẻ đều `fit-content`, có SÀN SƯ PHẠM `min-width` (không bóp sát từng pixel SVG — phải còn chỗ cho nhãn/chú giải/một câu thuyết minh), và MỌI con lấp trọn thẻ nên mép trái của hình CHÍNH LÀ rail của chữ. Khay điều khiển nằm cùng cột nên tự bằng bề rộng thẻ (giữ W4B-3H). SVG sân khấu phải khai bề rộng THẬT qua `stageSvgSize` — `width="100%"` không sizing được cha `fit-content` (Chrome rơi về 300px mặc định) và buộc phải `margin: 0 auto`, chính là rail thứ hai. Ngoại lệ phải KHAI kèm lý do cơ chế: `web.style_model` được bám cửa sổ (trang web lấp bề rộng khả dụng LÀ hành vi đang dạy), `logic.boolean_dag` được đặt chú giải cạnh sơ đồ | `styles/global.css` (`.app-layout` cột `auto` + `.workspace-card` `fit-content` + `.workspace-card > * { width: 100% }`) + `simulations/stage-size.ts` | `frontend/scripts/audit-composition.mjs` — 23 target × 4 bề rộng, hai lỗi tách bạch. **Lỗi A đo bằng câu FALSIFIABLE "khung có bám cửa sổ không"** (so 1920 vs 1366): so mực/khung là không thể sai vì chữ luôn giãn đầy khung. Tiêm lỗi: cột `1fr` + thẻ `100%` ⇒ ĐỎ · căn giữa hình ⇒ ĐỎ rail · nới khoảng cách cột sơ đồ ⇒ ĐỎ ở `dag.test` |

| 31 | **Khung hình thứ `k` suy được HOÀN TOÀN từ `trace[k].memory_snapshot` qua `visual_bindings`, không phụ thuộc gì khác** (2026-08-20). Đây là bất biến khoá trục hiển thị, và nó sinh ra từ một bug đã ship: cầu nối giữ `frames[0].objects` rồi vứt mọi khung sau, nên lời thuyết minh chạy tới bước 15 trong khi ngăn xếp trên hình vẫn RỖNG và các ô giá trị vẫn `0`. Chương trình do AI sinh **đúng**, interpreter chạy **đúng**, trace **đúng** — chỉ khúc nối vứt trạng thái; chẩn đoán nhầm thành "lỗi của AI" sẽ dẫn tới quyết định kiến trúc sai. Hệ quả bắt buộc: envelope mang **toàn bộ** chuỗi khung với snapshot đầy đủ mỗi khung (không delta — logic replay chính là chỗ trục hiển thị lệch khỏi trục ngữ nghĩa); renderer chỉ ĐỌC, được nội suy **pixel** giữa hai khung nhưng **cấm** bịa trạng thái ngữ nghĩa trung gian | `semantic_program/pipeline_adapter.py::compile_semantic_program_to_envelope` + `visual_adapter.py` | `test_frame_state_invariant.py` (envelope giữ đủ mọi khung của adapter; và hồi quy trực tiếp: không được mọi khung đều có ngăn xếp rỗng) |

| 32 | **Gộp bước nằm NGOÀI adapter, và pacer PHÂN HOẠCH chứ không CẮT** (2026-08-20). Gộp đặt trong `VisualTraceAdapter` là phá song ánh `frame k ⇔ trace[k]`, tức phá luôn tư cách định lý của bất biến #31 — nên nó thuộc `PresentationPacer`, chạy sau. Bất biến của pacer yếu hơn nhưng vẫn kiểm được: mỗi bước xem là một đoạn **liên tiếp** các khung máy; các đoạn phân hoạch **đầy đủ**, **không chồng lấn**, **không sinh khung mới**. Ngân sách trình bày tách hẳn ngân sách thực thi: chạm trần trình bày KHÔNG phải lỗi (hạ mức chi tiết cho tới khi vừa, và khai đang xem ở mức gộp nào), còn chạm trần thực thi thì phải BÁO. Gộp hai con số này làm một chính là nguyên nhân gốc của `MAX_REVEAL_STEPS` cắt `steps[:20]` không báo lỗi | `semantic_program/pacer.py::pace` | `test_pacer_partition.py` (phân hoạch đầy đủ · không chồng lấn · tổng khung bảo toàn ở 5000 khung — cắt là ĐỎ) |

| 33 | **Mọi primitive khai trong enum của contract BẮT BUỘC có nhánh xử lý trong adapter** (2026-08-20). Sinh ra từ `bar_chart`: contract liệt kê nó trong `VisualContainerBinding.primitive` nhưng `_adapt_single_step` không có nhánh nào, nên LLM khai `bar_chart` là ra object rỗng — lỗi CÂM, không đỏ ở đâu. Vá riêng một nhánh thì primitive kế tiếp lại rơi y hệt; nên luật là **đối sánh hai chiều** giữa enum và `HANDLED_PRIMITIVES`, thiếu hoặc thừa đều ĐỎ | `semantic_program/visual_adapter.py::VisualTraceAdapter.HANDLED_PRIMITIVES` | `test_primitive_coverage.py` (enum ⊆ handled **và** handled ⊆ enum) · `test_primitive_set_frozen.py` (2026-08-21 — TẬP primitive đã ĐÓNG BĂNG, kèm ba primitive **cố ý loại** và lý do: `graph_editor` vì sửa đồ thị là đổi ĐỀ BÀI chứ không phải tham gia cơ chế · `force_layout` vì layout phải TẤT ĐỊNH, force-directed cho hình khác nhau mỗi lượt nên ảnh chụp hết so được · `camera_3d` vì route này 2D only) |

| 34 | **Binding bắt buộc không phân giải được → FAIL-CLOSED, không render một phần** (2026-08-20). Luật **không phải** "bỏ con trỏ rồi vẫn vẽ phần còn lại" — đó là hạ cấp âm thầm, đúng loại lỗi đã sinh ra bất biến #31 (con trỏ `i` neo vào container rỗng nên đè lên dòng chữ thuyết minh). Một `visual_binding` bắt buộc mà không phân giải được ở **bất kỳ** khung nào là hỏng hợp đồng: adapter/validation thất bại và **không phát canonical envelope**. Học sinh thà không thấy gì còn hơn thấy một cảnh thiếu thành phần mà không ai nói cho biết là đang thiếu. Lưu ý phạm vi: đòi phân giải **ít nhất một lần trong trace**, không đòi ở mọi khung — một con trỏ chưa được gán ở bước 0 là bình thường | `semantic_program/pipeline_adapter.py::_assert_bindings_resolvable` | `test_binding_fail_closed.py` (`VisualBindingUnresolved` khi binding không bao giờ phân giải) |

| 35 | **Thanh bước của Scene3D đi qua BƯỚC DỰNG — một phân hoạch của trace, không phải một trục thứ hai** (W12, 2026-09-30). Review người W12: thanh bước đi qua cả sự kiện chỉ tính số/kết luận, chỉ số tăng mà hình đứng yên. `geometryTimeline` gộp sự kiện thành bước dựng theo đúng khuôn #32 (liên tiếp · đầy đủ · không chồng lấn · không sinh khung): bước mới CHỈ mở ở sự kiện `GEOMETRY_CONSTRUCTION` làm đổi chữ ký hình (vật vẽ được + tiến độ thiết diện); `MEASUREMENT`/`EXPLANATION`/`FINAL_RESULT` nhập vào bước đang mở và lên LỚP LỜI GIẢI (bảng dưới thanh bước). Khung hiện của một bước là `trace[anchor]` với `anchor` = sự kiện cuối đoạn ⇒ #31 giữ nguyên. Loại sự kiện đọc từ `semantic_kind` có cấu trúc — không đoán từ lời kể/tiêu đề/action/id; cảnh không gõ loại ⇒ mỗi sự kiện một bước. Backend không xoá sự kiện nào | `frontend/src/simulations/domains/geometry/scene3d-model.ts` (`geometryTimeline`, `solutionAt`) + `scene3d-playback.tsx` + `scene3d-solution.tsx` | `scene3d-geometry-timeline.test.tsx` (sáu cảnh w11, số bước từ phép đếm ĐỘC LẬP; 0 khung tĩnh; tới/lùi trả đúng snapshot) + bộ đo trình duyệt (`assessGeometrySteps`) |

| 36 | **Một GIVEN phải được CÂU ĐỀ chứng minh — lời khai `analyze` không phải nguồn** (W12, 2026-09-30). Tuyến LLM từng nhận một độ dài chỉ có trong mục `analyze` (đề không ghi) rồi gắn GIVEN. Cổng grounding đọc bằng chứng từ câu đề: độ dài `XY_length` cần con số của đề (nguyên/thập phân `.`/`,`/phân số/căn), không bị nhãn đoạn khác hay đơn vị khác mâu thuẫn; nguyên tử chỉ khớp giá trị P1 không chứng minh được ⇒ `GIVEN_VALUE_NOT_IN_SOURCE`; span P1 không cắt đúng chữ ⇒ `SOURCE_SPAN_MISMATCH`; mâu thuẫn ⇒ `SOURCE_EVIDENCE_CONFLICT`; toạ độ ghim vào mục mang số đề không ghi ⇒ từ chối. Ba mã KHÔNG gửi đi sửa. Lời khai chưa chứng minh không DỰNG bất biến nguồn (vẫn phủ quyết phép chia nó mâu thuẫn). P1 tính lại từ đề, một hàm dùng chung cho biên đóng băng · cổng · bộ phát bất biến. Giới hạn đã khai: kênh toạ độ `model_assumption`/`LAYOUT_DERIVED` vẫn có thể cố định một kích thước đề không cho (`ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION`; w15: đóng trong vùng đa diện — #37) | `semantic_program/grounding_gate.py` (`_bang_chung_do_dai`, `MA_LOI_NGUON`) + `literal_extractor.py::gia_tri_khong_chung_minh_duoc` + `segment_relation.py::_van_ban` + `ai/pipeline.py::KHONG_SUA_NGUON` | `test_source_grounding_closure.py` (tuyến sản phẩm với transport giả, 0 lượt gọi model) + fixture âm `_ungrounded` sáu họ |

| 37 | **Trong vùng đa diện, một giá trị SỐ người học thấy phải có CHỨNG CHỈ — bố cục hay giả thiết của mô hình không được quyết định đáp số** (W15, 2026-10-03). Hai phép dò W12 từng được phục vụ với `V = 30` khi đề không cho AD: chương trình giữ AD bằng toạ độ `LAYOUT_DERIVED`/`model_assumption`, không kênh nào khai GIVEN nên grounding không có gì để kiểm. Nay route chỉ phục vụ giá trị có chứng chỉ (`PROVEN_SAFE`). **C0:** mọi literal trên lát cắt là dữ kiện đề CÙNG thực thể. **C1:** khuôn T1–T6 khớp ràng buộc server đọc từ đề. Lát cắt đi theo định nghĩa với tới DUY NHẤT trên trace, giá trị lấy tại lúc định nghĩa. Phản ví dụ hợp lệ ⇒ `ASSUMPTION_DETERMINES_ANSWER`, nêu đại lượng thiếu; còn lại ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN`. Cả hai từ chối ở chặng `assumption` và KHÔNG gửi đi sửa. Tiền đề chỉ đến từ CÂU ĐỀ (bộ đọc + bộ phát bất biến gọi không kèm hợp đồng) — chú thích quan hệ của mô hình không bao giờ là tiền đề. Phạm vi thi hành theo U3: đề nêu khối đa diện theo từ vựng đóng; ngoài vùng chỉ ghi. Nhiều định nghĩa với tới bị từ chối ở MỌI vùng (U5). W16 (amendment §14): "CÙNG thực thể" gồm cả mặt phẳng cho bằng phương trình — gắn theo tên hoặc duy nhất theo đếm, trùng bộ số không là căn cứ; mọi tiền đề đọc từ đề đã che mệnh đề mục tiêu (`Chứng minh …`, `CMR`, `Kiểm tra …`, câu hỏi) | `semantic_program/assumption_gate.py::kiem_gia_dinh` + `shape_constraint.py` (`doc_rang_buoc`, `phan_chua_doc`, `neu_khoi_da_dien`) + `route.py::_sau_grounding` + `ai/pipeline.py::KHONG_SUA_NGUON` | `test_assumption_gate.py` (tuyến route) · `test_assumption_certificate.py` (C0/C1/phản ví dụ, định nghĩa với tới gồm ca lệnh dựng tự đọc, vai trò literal, metamorphic) · `test_shape_constraint.py` · census vòng 3 + tiêm lỗi FI1–FI14 trong run `w15-assumption-closure` · `test_plane_from_equation.py` (tên mặt phẳng) + census vòng 2 + tiêm lỗi FG/FA/FB/FD trong run `w16-premerge-closure` |
| 38 | **Một phép cắt được chứng nhận phải là phép cắt ĐỀ nói, và mọi con số trên hình do backend gắn** (W17, 2026-10-04). Giới hạn A′ của W16: (T) cắt bởi (α) đã ghim đúng, trong khi đề nói (β), vẫn được chứng nhận C0 và phục vụ (hiện 9, đề cho 16). Nay mọi `construct_section` trên lát cắt của giá trị hiển thị phải dùng cùng mặt phẳng (theo nguồn, rồi tên/duy nhất; mặt phẳng gọi qua điểm = tập điểm) và cùng khối (tập đỉnh) với câu cắt đọc từ đề đã che mục tiêu. Lệch chắc chắn ⇒ `CONSTRUCTION_NOT_TEXT_BOUND` (nguyên nhân CONSTRUCTION); danh tính không ghim được ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN`. Grounding cũng đọc trên đề đã che mục tiêu ở mọi vùng. Nhãn số đo trên hình: backend gắn đại lượng ↔ chủ thể (độ dài đề cho được kiểm bằng khoảng cách chính xác); frontend chỉ chiếu, đặt chỗ, bật/tắt; nhãn đáp số chỉ có từ bước kết luận. Giới hạn: chỉ phép cắt được đối chiếu với đề (`ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`) | `semantic_program/shape_constraint.py::doc_quan_he_cat` + `assumption_gate.py::_kiem_phep_dung` + `grounding_gate.py::check_grounding` + `refusal_cause.py` + `quantity_annotations.py::gan_so_do` + `frontend/src/simulations/domains/geometry/scene3d-annotations.ts` | `test_assumption_certificate.py` · `test_shape_constraint.py` · `test_source_grounding_closure.py` · `test_refusal_cause.py` · `test_scene3d_annotations.py` · `scene3d-annotations.test.ts` · census vòng 2 + tiêm lỗi backend 23/23, frontend 18/18 trong run `w17-operation-annotations` |
| 39 | **Một điểm đề gọi tên bằng quan hệ (trung điểm, hình chiếu) phải được dựng trên ĐÚNG thực thể đề nêu, xét theo DANH TÍNH; mọi số trên hình do backend gắn vai trò, và một nơi giải thích nó** (W18, 2026-10-04). Trước W18, chiếu lên sai đường/mặt, tráo danh sách "lần lượt", đổi tên đích, hay một điểm trùng toạ độ nhưng khác danh tính đều được PHỤC VỤ, vì mọi cổng chỉ hỏi điểm NẰM ĐÂU. Nay chặng `construction_binding` (sau thực thi, trước `source_invariant`) đối chiếu từng phép dựng điểm với quan hệ đọc từ đề (từ vựng đóng) qua các thẩm quyền danh tính sẵn có; toạ độ hay giá trị bằng nhau không bao giờ là bí danh. Lệch ⇒ `CONSTRUCTION_NOT_TEXT_BOUND` ở mọi vùng; chưa đối chiếu được ⇒ `CONSTRUCTION_BINDING_UNVERIFIED` trong vùng đa diện, lời không bao giờ nói đề sai. Trình bày: `role`, `same_as` theo chủ thể, nhân chứng khoảng cách chân chính xác — frontend chỉ lọc theo lựa chọn/"Hiện tất cả", không tính hình. W20 (§17): đích khai bằng toạ độ, trực tiếp hay qua bí danh ⇒ `CONSTRUCTION_REPLACED_BY_COORDINATES` ở mọi vùng. Giới hạn: tâm, giao điểm, cách nói ngoài từ vựng (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`) | `semantic_program/construction_binding.py` (`doc_quan_he_dung`, `doi_chieu_phep_dung`) + `route.py` (chặng `construction_binding`) + `quantity_annotations.py::_nhan_chung` + `scene3d.py::_gan_so_do` + `frontend/src/simulations/domains/geometry/scene3d-annotations.ts::annotationsAt` | `test_construction_binding.py` · `test_scene3d_annotations.py` · `scene3d-annotations.test.ts` · `Scene3DExplorer.test.tsx` · census W18 + tiêm lỗi backend 12/12 và frontend 12/12 (vòng 2) trong run `w18-binding-focus` · `test_construction_binding_literal.py` + probe, census và tiêm lỗi trong run `w20-cleanup-premerge` |

## 6. Bốn trục khái niệm

*Hai trục của hệ Tin học — specialized ↔ generic DSL, interaction ↔ edit (EditPolicy v1) — đã gỡ cùng mã:
nguyên văn ở [`legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md`](legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md).*

**Canonical ↔ Learner.** Mô phỏng hệ sinh ra: đúng hoặc `capability_gap`. Thao
tác học sinh: được phép sai; sai mà có rule kiểm được → feedback; không có rule →
`unsupported_to_verify`, **không phán bừa**. Chi tiết: `docs/CORRECTNESS.md`.

**Offline ↔ Live.** Test mặc định không chạm mạng (guard ở biên httpx/fetch).
Live eval opt-in, có suite (smoke/full/boundary) và ngân sách API.

## 7. Điểm mở rộng

- **Năng lực hình học mới** (phép dựng, phép đo, quan hệ): mở IR — lược đồ
  `backend/app/simulation/semantic_program/contract.py`, `ir_static_check.py`, cầu nối `geometry_exec.py`;
  sinh lại hai bản lược đồ bằng `backend/scripts/export_semantic_program_schema.py` (`test_schema_sync.py`).
  Lược đồ, thẻ văn phạm (`grammar_card.py`), prompt (`backend/app/ai/skills/*.md`) và bảng năng lực là bề mặt
  mô hình: đổi chúng thì phải đo lại. Hỏi trước: thiếu năng lực thật, hay chỉ thiếu cách nói cho mô hình biết?
- **Họ hình mới**: đi qua `backend/app/simulation/product_capability.py` và
  `docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json` trước khi viết mã.
- **Lý do từ chối mới**: mã lý do ở chặng sinh ra nó, câu cho người học ở `backend/app/learner_messages.py`, nhãn
  ở `frontend/src/components/SimulationWorkspace.tsx`; không lộ định danh kĩ thuật
  (`frontend/src/components/ui-hygiene.test.ts`).
- **Điều khiển giao diện mới**: không khai năng lực thì không có điều khiển — vắng mặt, không mờ đi (chống
  affordance rỗng, `DESIGN_BRIEF.md` §3.2).

Năm điểm mở rộng của hệ Tin học (`catalog.py`, manifest DSL, `dataset.py`, capability của `SimulationModule`,
renderer theo module): nguyên văn ở [`legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md`](legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md).

## 8. Anti-pattern (đã từng gây bug thật)

1. **Viết tay enum song song manifest** — `_GENERIC_SCHEMA` từng thiếu `drag` →
   Gemini **không thể** phát ra dù prompt cho phép; fail cả 3 retry, không manh
   mối. Mọi enum phải dẫn xuất từ manifest.
2. **Hard-code theo tên bài/môn/tiêu đề** ("triangle", "web", "tam giác") — mọi
   quyết định phải suy từ **capability/cấu trúc spec**.
3. **Vá capability gap bằng tọa độ LLM đoán** — tạo "hình nhìn có vẻ đúng" mà sai
   bản chất (kéo M thì E/F/P đứng yên). Phải `capability_gap`.
4. **Mock LLM ở module consumer** — `call_gemini` được import vào 4 module với 4
   binding riêng; mock một chỗ không che chỗ khác. Guard phải ở **biên mạng**.
5. **Renderer tự sửa state/spec** — mọi biến đổi qua `apply` hoặc patch.
6. **Toolbar/affordance vô điều kiện** — UI phải dẫn xuất từ capability. Đã sửa
   ở M7.14D: `EditPolicy` suy từ chính spec (`edit_policy.py` + mirror
   `generic/edit-policy.ts`), thực thi ở **cả ba tầng** (affordance UI, patch FE,
   patch/edit BE) — ẩn nút là KHÔNG đủ.
7. **Chạy full live eval theo thói quen** — tốn quota; theo chính sách trong
   `CORRECTNESS.md §7`.
8. **`renderToString(<App/>)` để kiểm một view CÓ DỮ LIỆU** (M9-UX4) — zustand v5
   dùng `useSyncExternalStore`; khi SSR, React lấy **getServerSnapshot = initial
   state**, nên state vừa mutate KHÔNG hiện ra. Test kiểu này xanh/đỏ vì lý do
   sai: một assert `toContain("Thuật toán")` tưởng là đang kiểm thẻ Lịch sử, thực
   ra khớp nhãn domain của starter card ở **Home**. **Luật**: test SSR qua `App`
   chỉ hợp lệ ở **trạng thái đầu**; muốn kiểm view có dữ liệu thì **render thẳng
   component với prop** (vd `SessionCard` nhận `item`) hoặc assert trên `store()`.
9. **Ký tự Unicode hình khối làm icon** (M9-UX4) — `◧`/`◨` (U+25E7/25E8) không có
   glyph trong font hệ thống Windows → hiện **ô vuông rỗng (tofu)** ngay trên
   header. Icon phải là SVG, đừng phụ thuộc font.
10. **Chuỗi kĩ thuật lọt lên UI học sinh** (M9-UX3/UX4) — `simulation_id`
   (`algorithm.bubble_sort`) từng bị render ở `InputPanel` rồi `HistoryView`. Vá
   một chỗ **không** vá chỗ kia: luật phạm vi phải áp ở **mọi bề mặt** học sinh
   thấy, và tốt nhất là gom về **một component chung** (nay là `SessionCard`).
14. **Tin một bản soát "sạch" mà không chứng minh nó bắt được lỗi** (M9-UX7) —
   `scripts/audit-layout.mjs` lần chạy đầu báo "TẤT CẢ SẠCH". Đó đúng là loại kết
   quả xanh vì **đo nhầm trang** (cùng họ với anti-pattern #13). Hai thứ bắt buộc
   phải có trước khi tin: (a) **dấu vân tay trang** — soát xong phải khẳng định
   mình đã ở đúng route, sai thì thoát mã 2; (b) **tiêm lỗi giả** — cố ý thêm
   `margin-top: 7px` + icon lệch 9px, chạy lại, thấy nó bắt đủ, rồi mới trả CSS về.
   Một guard chưa từng thấy màu đỏ là một guard chưa được chứng minh.
12. **Tự chế ngôn ngữ thị giác trong khi dự án ĐÃ CÓ `DESIGN.md`** (M9-UX6) —
   `DESIGN.md` §Don't nói rõ: *"Don't paint a CTA or structural fill in any
   sticker-palette colour — those are decoration only"* và *"Don't introduce a
   second structural accent alongside primary"*. Tím/hồng/cam/teal là **trang trí**
   (chấm phân loại, minh hoạ); màu DUY NHẤT sơn hành động là `--primary`. Muốn một
   thẻ nổi lên thì dùng **surface tint** (`canvas-soft`), KHÔNG viền màu — đúng
   khuôn `pricing-plan-card-featured`. Ngoại lệ hợp lệ: §Semantic cho phép sticker
   palette mang **status** (xanh lá = đúng, cam = sai). Khoá bằng
   `components/ui-hygiene.test.ts`.
13. **Đặt guard ở chỗ phụ thuộc route** (M9-UX6) — guard cấm-emoji đầu tiên quét
   `renderToString(<App/>)`, mà SSR chỉ đi qua **trạng thái đầu** (Home) nên không
   bao giờ chạm workspace: emoji 🔮 (`PredictionBar`) và chuỗi `find_max`
   (`AnalysisCard`) **lọt qua guard xanh lè**. Guard vệ sinh phải quét **MÃ NGUỒN**,
   không quét HTML đã render — như vậy mọi component đều bị soi, kể cả component
   chưa có test nào đi qua.
11. **`var(--token)` trỏ vào token KHÔNG TỒN TẠI** (M9-UX5) — lỗi **IM LẶNG** và
   nguy hiểm nhất trong CSS: trình duyệt vứt **cả dòng khai báo**, không cảnh báo,
   không đỏ ở đâu. `global.css` gọi `var(--sp-2xl)` trong khi token thật là
   `--sp-xxl` → `.home-composer` mất `margin: 0 auto` → **ô nhập lệch hẳn sang
   trái**, `.home-title` mất margin → **chữ dí sát ô**, `.app-single` mất padding
   đáy. Trôi từ M9-UX1 tới M9-UX5 mới bị phát hiện — bằng cách **đo trong browser
   thật**, không phải bằng đọc code. Cùng lúc lộ thêm `--border`/`--radius-sm`/
   `--radius-md` (M8-PRE-LIP): `PredictionBar` suốt nay **không có viền, không bo
   góc**. Nay khoá bằng `styles/tokens.test.ts` (mọi `var()` phải có định nghĩa).

15. **Cầu nối giữ khung ĐẦU rồi phát narration chạy** (2026-08-20) — đã ship bug
    thật. `compile_semantic_program_to_envelope` lấy `frames[0].objects` rồi vứt
    toàn bộ khung còn lại, nên trên màn hình: thuyết minh đọc *"lấy `[` ra khỏi
    ngăn xếp, so với `]`, khớp nhau"* — **chính xác từng chi tiết** — trong khi
    ngăn xếp RỖNG, "Ký tự hiện tại" = `0`, "Kết quả" = `0`, con trỏ đè lên chữ.
    Hai bài học tách bạch: (a) **hình đóng băng mà lời vẫn chạy là lỗi CẦU NỐI,
    không phải lỗi của LLM** — chương trình sinh ra đúng, interpreter chạy đúng,
    trace đúng; đổ cho AI ở đây là chẩn đoán nhầm rồi sửa nhầm chỗ. (b) lỗi này
    **không có test nào bắt được** vì hợp đồng envelope không hề đòi khung thứ
    `k` phải khớp trạng thái bước `k` — cho tới khi bất biến #31 được viết ra.
    Cùng họ với #13: chỗ nào không có bất biến thì chỗ đó trôi im lặng.

## 9. Vị trí cache & pattern reuse

- **Tầng 1 — exact cache** (`main.py`, bảng `simulation_cache`): trước pipeline;
  version ở **cột** (`dsl_version`/`policy_version`), lệch → miss. Chỉ cache
  `status == "ok"`.
- *Tầng 2 (pattern reuse, `patterns.py`) và đường edit M7.14 đã gỡ cùng hệ Tin học: nguyên văn ở
  [`legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md`](legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md).*

## 10. Hướng khả dĩ trong tương lai (chưa làm, không phải cam kết)

Hướng phát triển hiện hành: [`ROADMAP.md`](ROADMAP.md) và [`POST_THESIS_BACKLOG.md`](POST_THESIS_BACKLOG.md). Hai hướng của hệ Tin học (M7.15, `code_experiment`): nguyên văn ở [`legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md`](legacy/ARCHITECTURE_MAP_INFORMATICS_ERA.md).
