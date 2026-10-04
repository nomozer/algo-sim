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

> **Con trỏ thực thi đã cũ (2026-10-05, `cuboid-final-review`).** Hai cột cuối ghi nơi khoá *lúc thêm hàng*. Ở 22
> hàng — #1–#8, #10, #11, #14–#16, #18, #20–#26, #29 — ít nhất một file được nêu đã gỡ (phần lớn cùng miền Tin học,
> `LEGACY_INFORMATICS_REMOVAL` 2026-09-02); ở #1–#8, #11, #14, #15 thì không file nào còn. Nguyên tắc của các hàng
> ấy có thể vẫn đúng, nhưng nơi khoá hiện hành **chưa được ghi**: đừng coi chúng là đang được test khoá. Danh sách
> theo hàng: `docs/evaluation/geometry/runs/cuboid-final-review/inventory/DOCS_INVENTORY.json`
> (`architecture_map_invariant_pointers`); đối chiếu lại từng hàng: `ISSUE-DOCS-INVARIANT-ENFORCEMENT-POINTERS-STALE`.

| # | Bất biến | Thực thi ở | Test |
|---|---|---|---|
| 1 | LLM không phải nguồn state runtime | `skills/*.md` cấm sinh timeline; validator có `FORBIDDEN` keys | `test_pipeline::test_simulate_sinh_timeline_bi_chan` |
| 2 | Engine tất định là nguồn chân lý | `init/apply/timeline` của module | `algorithms.test.ts`, `generic.test.ts` |
| 3 | Renderer không sở hữu state | `WorkspaceProps` chỉ có `state` + `dispatch` | `patch.test.ts` (drag qua action) |
| 4 | Manifest là từ vựng capability | mọi enum/allowlist dẫn xuất | `test_manifest::*_dan_xuat_tu_manifest` |
| 5 | Specialized **không** bị chặn bởi gap của DSL generic | `pipeline.run_pipeline` (gate chỉ chặn đường generic) | `test_capability_boundary::test_gap_role_khong_va_lay_specialized` |
| 6 | Pattern reuse chỉ **sau classify**, chỉ `generic.rule_scene` | `pipeline.run_pipeline` | `test_reuse::test_case_g_specialized_khong_dung_store` |
| 7 | Reuse **không** bypass validation (4 cổng) | `patterns.run_gates` | `test_patterns::test_run_gates_khong_bypass_validation` |
| 8 | Thà `capability_gap` còn hơn mô phỏng xấp xỉ gây hiểu lầm | `representation.build_representation_plan` + `semantic.check_semantic_compatibility` | `test_capability_boundary::*` |
| 9 | Canonical simulation: đúng hoặc từ chối trung thực | như trên | như trên |
| 10 | Learner **được phép sai** | what-if branch (algorithm), drag tự do | `registry.test.ts`, `patch.test.ts` |
| 11 | Chỉ engine/rule tất định mới phán đúng/sai | `InteractionFeedback` sinh từ rule | `patch.test.ts::drag bounds` |
| 12 | Feedback là **state data**, không phải lượt chat | `GenericState.feedback` | như trên |
| 13 | `pytest`/`vitest` mặc định = **0 call AI thật** | `backend/conftest.py`, `frontend/src/test-setup.ts` | `test_offline_guard.py`, `offline-guard.test.ts` |
| 14 | Live eval là **opt-in**, không phải thói quen | `evaluation/live.py` (`ALLOW_LIVE_AI=1`) | `test_live_budget::test_live_khong_co_opt_in_thi_abort` |
| 15 | Patch fail → spec hiện tại **nguyên vẹn** | `patch.py` áp trên bản sao | `test_patch::test_patch_fail_giua_chung_khong_mutate_spec` |
| 16 | **3D là renderer, không phải domain** (M8): 2D/3D dùng chung module/config/state/timeline/action/prediction; `visualMode` là trình bày thuần; renderer khả dụng dẫn xuất từ hợp đồng module | `simulations/renderer.ts` + `SimulationWorkspace` (không switch-case id) | `visual-mode.test.tsx`, `render3d.test.tsx`, `m8-acceptance.test.tsx` |
| 17 | **Mở lại từ lịch sử = ZERO-AI** (M9-UX1): lưu envelope ĐÃ VALIDATE, mở lại qua `loadEnvelope` + engine tất định — không đi pipeline, không LLM; chỉ persist trường whitelist (không prediction/branch/camera/secret); runtime reset không phá lịch sử | `state/history.ts` + `store.reopenFromHistory` | `history.test.ts`, `view-history.test.tsx` |
| 18 | **Nghĩa của chiều sâu 3D phải TRUNG THỰC, và chỉ nghĩa SƯ PHẠM mới được bày cho học sinh** (M10, siết ở W4B-2R): module có 3D khai `threeD.role` = `pedagogical` (Z mã hoá biến khái niệm thật — `network.protocol_encapsulation`: **Z = tầng giao thức**, X = chiều truyền). W4B-2R nâng M10 từ *khai báo trung thực* lên *chính sách*: `architectural_poc` (Z chỉ là bố cục) **KHÔNG đủ tư cách bày toggle 2D/3D** — đó chính là `2D_AND_3D_BY_DEFAULT`. Tiền lệ: `network.packet_routing` tự khai `architectural_poc` + `meaningOfZ = "bố cục, không mang nghĩa khái niệm"`, nên W4B-2R **hạ nó về 2D_ONLY và gỡ `ui3d.tsx`**. Danh mục nay **22 × 2D_ONLY · 0 × 3D_ONLY · 1 × 2D_AND_3D_JUSTIFIED**. PDU là state ngữ nghĩa dùng chung (2D+3D đọc cùng), 3D không tính lại PDU | `SimulationModule.threeD` (`types.ts`) + **`renderer.ts::representationPolicyOf` / `representationPolicyProblems`** (chủ sở hữu chính sách). **W4B-2S siết tiếp**: `role: "pedagogical"` chỉ là NHÃN TỰ NHẬN nên chưa đủ — target có 3D phải khai `threeD.pedagogicalFit[]` (3D thắng ở tiêu chí nào) **và** `whyNot2d` (vì sao 2D không diễn đạt được). Kèm luật thứ hai: **vai trò miền phải chở bằng HÌNH, không bằng chữ** — chủ sở hữu `domains/network/node-glyph.ts` (`NodeType` engine → hình), khoá bằng phép thử XOÁ HẾT CHỮ | `representation-policy-w4b2r.test.ts` (guard toàn danh mục, dẫn xuất từ registry), `encap-render3d.test.tsx` (encap=pedagogical) |
| 19 | **Alembic sở hữu schema Postgres bền** (DB-HARDEN-2, *chất lượng triển khai — không phải đóng góp học thuật*): tạo & tiến hoá schema PostgreSQL do **Alembic** sở hữu DUY NHẤT (`alembic upgrade head` ở entrypoint Docker). `create_all()` chỉ dành cho SQLite ephemeral/test, KHÔNG phải cơ chế migration của Postgres; runtime **không** lặng lẽ `create_all()` trên Postgres (quyết định theo `engine.dialect.name`, không string-check URL). Không tự động `stamp` DB lạ | `db.py::init_db` (gate qua `sqlite_owns_schema`) + entrypoint Docker | `test_db_ownership.py`, `test_migration_drift.py` (cổng chống trôi, có fault-injection proof), `test_postgres_integration.py` (smoke opt-in) |
| 20 | **Toán hạng numeric/logical của một rule generic phải có nguồn giá trị theo hợp đồng ngữ nghĩa DẪN XUẤT TỪ MANIFEST — không có thì reject, không bao giờ hoá 0 im lặng** (M13): validator hai tầng từ chối operand không phải *value-provider* của role rule cần (`INVALID_SOURCE` — vd `edge`/`node` không có `value`) và từ chối derived-target sai role theo `role_satisfies()` — subtyping **MỘT CHIỀU** dẫn xuất từ `role_compatibility` trong contract (M13 hotfix: `logical` satisfies `numeric` — boolean executor sinh đúng 0/1, KHÔNG runtime conversion; vd `weighted_sum` numeric vẫn không được ghi vào `node` relational). Mọi cặp khác **DENY mặc định**; chiều ngược `numeric ↛ logical` LUÔN deny (đó chính là coercion ngầm `v>=1` mà check này sinh ra để diệt) — chỉ mở cặp mới khi matrix audit chứng minh được fixture thật; runtime hai tầng KHÔNG BAO GIỜ seed/fallback một giá trị thiếu/chưa resolve thành 0 — ném lỗi TYPED fail-closed tại ranh giới evaluator (4 mã: `invalid_numeric_source` / `missing_weight` / `unresolved_dependency_after_bound` / `non_finite_numeric_value`). Sự cố gốc đã sửa: `weighted_sum` ăn input là id một `edge` (fixture "pseudo-Dijkstra" — TÁI DỰNG, artifact gốc không khôi phục được từ cache/localStorage) từng lặng lẽ hoá 0 → cảnh "chạy" đủ bước, kết quả sai câm; validator siết chặt tự động bảo vệ luôn cả đường pattern-reuse (fixture cũ mang shape cấm bị chặn ngay ở cổng 1 `run_gates`, không cần sửa riêng) | Validator: `dsl/validator.py` (khối coherence, dòng ~369) + mirror `generic/validate.ts` (dòng ~339, import trực tiếp `dsl-contract.json` — không hằng viết tay). Runtime: `generic_engine.py` (`GenericEvaluationError`) + mirror `generic/model.ts` (`GenericExecutionError`) + `state/store.ts` bọc `mod.init` fail-closed. Nguồn hợp đồng: `manifest.py::dsl_semantic_contract()` → sinh `dsl-contract.json` (`scripts/generate_dsl_contract.py`, chạy tay, sync-lock chống trôi) | `test_dsl.py` khối M13 Task 3 · `test_generic_engine_m13.py` · `generic.test.ts` (`describe("M13 operand coherence")`, `describe("M13: valuesOf ba trạng thái...")`) · `test_manifest_providers.py` (bao gồm `test_dsl_contract_json_khong_troi_khoi_manifest` — sync-lock) · fixture pseudo-Dijkstra: `test_m13_dijkstra_fixture.py` (validator reject) + `generic.test.ts` describe `"M13 Task 7"` (history reopen fail-closed, không throw) + `test_m13_pattern_revalidate.py` (chặn ở cổng 1 khi thử reuse) |
| 22 | **Evaluation của luồng AI tạo mô phỏng phải thực thi CÙNG production orchestration với `/api/analyze`; evaluator KHÔNG được tái dựng riêng chuỗi analyze→classify→gate→simulate** (M14). `evaluate_item` gọi THẲNG `run_pipeline` với `observer` THỤ ĐỘNG (chỉ thu event; không đổi routing/retry/gate/output; `observer=None` → hành vi production không đổi một bit). Hệ quả: computation gate (M13) + mechanism gate (M14) NAY sống trong eval — case bị gate từ chối được chấm ĐÚNG là honest refusal (trước M14 harness bỏ qua gate, chấm sai). Side-effect isolation: eval `pattern_store=None` (reuse/persist bị guard bỏ qua) + `run_pipeline` không chứa code cache (cache sống ở `main.py`) → 0 row mới ở `simulation_cache`/`simulation_patterns`/`reuse_metrics`. `_simulate_with_metrics` (mirror chép tay, known-issue #1 drift) ĐÃ RETIRE sau transcript-parity proof. KHÔNG áp cho `/api/edit`, history reopen, offline catalog, renderer init. **M16 chứng minh bất biến này ở quy mô TOÀN catalog**: offline scripted evaluation (50 case, provider mock per-case, fault-injection) chứng minh **pipeline/gate correctness** — mọi record đi qua `run_pipeline` thật, parity 50/50; live evaluation (24 case baseline, user duyệt) đo **hành vi LLM thật** trên cùng orchestration, parity 24/24; observer THỤ ĐỘNG (diff pipeline toàn M16 = 2 dòng `_emit` no-op khi `observer=None`); pre-fix baseline giữ nguyên vẹn (trace + artifacts `docs/evaluation/m16/*-baseline.json`), correction count = 0. Hai lớp offline/live là hai run_label RIÊNG, không ghi đè | `ai/pipeline.py::run_pipeline(observer=...)` + `evaluation/observer.py::AttemptObserver` + `evaluation/harness.py::evaluate_item` (+ M16: `evaluation/m16_record.py`, `evaluation/m16_metrics.py`, `evaluation/m16_offline_scripts.py`) | `test_eval_convergence.py` (đi qua run_pipeline, observer passive), `test_eval_parity.py` (parity proof — skip sau retire), `test_eval_side_effects.py` (0-row lock + fault-injection: classify qua nhưng gate chặn → honest refusal), M16: `test_m16_offline_eval.py` (50/50 qua production pipeline + hard correctness + parity 1.0) |
| 23 | **Mechanism ownership được khai ở mức FamilyMembership; mechanism taxonomy dùng canonical namespaced IDs với một compatibility alias boundary duy nhất; consistency gate so sánh tín hiệu cơ chế có cấu trúc trên final route sau bounded reclassification** (M15). Giải thích: family mới khai `owned_mechanisms` máy-đọc-được ngay trên membership; giá trị analyze legacy được normalize tại ĐÚNG MỘT chỗ (`canonical_mechanism` — alias một chiều, không phải taxonomy thứ hai); gate và descriptor CHỈ so canonical values; route-consistency chạy trên FINAL route (không route-dependent gate nào chạy trên route tạm — `analyze → classify → recovery ≤1 reclassify → FINAL ROUTE → gates → simulate`); cơ chế không sở hữu → retry có giới hạn (cross-family mismatch, `ROUTE_MECHANISM_FAMILY_MISMATCH`) hoặc fail-closed `capability_gap` (cùng-family unowned, `GATE_MECHANISM_OWNERSHIP`); định tuyến KHÔNG dựa keyword-patch — chỉ so tín hiệu cấu trúc. Giá trị analyze-exposed không ai sở hữu phải khai tường minh trong `INTENTIONAL_GAP_MECHANISMS` (owned XOR intentional-gap) | `simulation/mechanisms.py` (taxonomy đóng + `canonical_mechanism` + `INTENTIONAL_GAP_MECHANISMS` + `FORMALIZED_FAMILIES`) + `descriptor.py::FamilyMembership.owned_mechanisms` + `mechanism_gate.py::check_mechanism_consistency_for_target` + `ai/pipeline.py::classify_with_one_route_recovery` | `test_mechanisms.py` (taxonomy/alias/exposed) · `test_descriptor.py` (owned canonical, family-prefix khớp) · `test_capability_descriptors.py` (khóa-2 XOR + K1 14/14) · `test_pipeline_mechanism_consistency.py` (ordering, budget analyze=1/classify≤2/simulate≤1, no-bypass, no-recursion) · `test_mechanism_gate.py` (3 nhánh 2 mã) |
| 21 | **Yêu cầu tính-kết-quả-thuật-toán mà không có executor tất định nào sở hữu → `capability_gap` trên đường generic, KHÔNG dựng cảnh minh hoạ đáp án** (M13): SERVER ra phán quyết cuối, tất định, trên **tín hiệu CÓ CẤU TRÚC** — hai kênh bổ sung nhau: (1) `known_gap_roles()` lọt vào `unsupported_capabilities` của representation plan (vd role `arbitrary_algorithm`); (2) `analysis.result_ownership` **fail-closed** — chỉ `"provided"`/`"rule_derivable"` được đi tiếp, `"algorithmic"` HOẶC thiếu/ngoài enum đều → gap (không default sang giá trị nào). Kênh 2 bắt được cả khi kênh 1 bị bỏ sót role (không phụ thuộc MỘT kênh prompt duy nhất). Giữ nguyên carve-out chuyên biệt (bất biến #5 — gap của DSL generic không lây sang specialized). Đây là lớp phòng thủ TRƯỚC khi simulate chạy (chặn ở classify/analyze), bổ sung — không thay thế — invariant #20 (chặn Ở VALIDATOR nếu vẫn lọt qua tới đó); artifact "pseudo-Dijkstra" là ca cụ thể bị #20 chặn, còn #21 là cơ chế chặn SỚM HƠN dựa trên ý định của đề bài | `simulation/computation_gate.py::check_computation_ownership`, gọi trong `ai/pipeline.py::run_pipeline` **sau classify**, scoped vào đường generic bằng kết quả classify (giữ carve-out chuyên biệt); taxonomy dạy bằng ví dụ ở `analyze.md`/`classify.md` (KHÔNG keyword-patch), `CACHE_VERSION` 9→10 | `test_m13_routing.py` (2 kênh, kể cả khi kênh 1 bị bỏ sót role) — offline, mock. **Verify LIVE CHƯA CHẠY**: eval case `cap-dijkstra-gap` (`evaluation/datasets/capability.py`) là bài kiểm thật với LLM thật, nằm sau Task 14 (STOP GATE, chờ `ALLOW_LIVE_AI=1`) |

| 24 | **KHÁM PHÁ và THỬ THÁCH là hai trách nhiệm khác nhau, phân biệt bằng AI PHÁN XÉT — và LỐI VÀO của chúng thuộc shell, không thuộc renderer miền** (W4B-3A). Thử thách: học sinh CAM KẾT một quyết định, `predict.check` (engine tất định) phán đúng/sai. Khám phá: học sinh ĐỔI mô hình, `module.apply` tính lại, **không ai phán gì** — hệ quả tất định LÀ câu trả lời. Một cửa cho cả hai dạy học sinh rằng kéo một cột cũng là "trả lời đúng/sai". Sự cố gốc: cả hai từng nằm sau MỘT `useState` cục bộ tên `labOpen` do renderer miền tự dựng nút mở, nên (a) dưới sân khấu luôn thừa một dải `experimentTrigger` (đo được ở 8 target thuật toán + `packet_routing`, cả 4 bề rộng), (b) chuyển phiên là mất chế độ, (c) SSR luôn thấy `false` nên không test nào chạm được trạng thái MỞ (xem §8 #13). Hệ quả kèm theo: `presentedInStage` từng tắt CẢ lối vào chứ không chỉ bề mặt thứ hai — đó mới là thứ ép miền phải tự dựng nút. Luật nay: `presentedInStage` chỉ chặn `PredictionBar`; **một cửa, nhiều nhất một bề mặt**; lối vào ở bước không dùng được thì **MỜ, không biến mất** (4/13 → 21/40 bước mời được tuỳ bài — tự gỡ mình là nhấp nháy). Store vẫn **mù domain**: nó giữ hai boolean và không biết "khám phá" ở bài này là kéo cột hay bấm liên kết mạng | `state/store.ts` (`exploreOpen`/`challengeOpen`; M18-UI: nhiều phiên đã gỡ, hai cờ nay ở thẳng store) + `components/SimulationControls.tsx` (chủ sở hữu DUY NHẤT của lối vào) + `components/SimulationWorkspace.tsx` (`challengeEntry`/`exploreEntry`/`challengeSurfaceVisible`) + hợp đồng `ExploreCapability`/`PresentationEntry` (`simulations/types.ts`) + `domains/algorithm/interaction-policy.ts` (`challengeEntryOf`/`exploreEntryOf`, hàm thuần) | `explore-ownership-w4b3a.test.ts` · `secondary-actions-w4b2w.test.ts` (0 dải `experiment-trigger`, đúng MỘT chủ sở hữu) · `workspace-lifecycle.test.ts` (bài mới luôn mở ở Quan sát, đổi bài 0 fetch) · `interaction-family-w1.test.tsx` (cửa ≠ bề mặt) · nghiệm thu trình duyệt 4 bề rộng `frontend/scripts/accept-w4b3a.mjs` |

| 25 | **Tiêu đề là ĐỀ BÀI, mô hình là thứ học sinh đang cầm — và khi hai bên lệch nhau thì màn hình phải NÓI RA** (W4B-4D). Trước khi có tham số đổi được, hai thứ này luôn trùng nên bất biến chưa cần tồn tại. Từ khi `count_if`/`sum_if` đổi được điều kiện, `tree`/`graph_traversal` đổi được cách duyệt, `database` đổi được truy vấn, `binary` đổi được cơ số/văn bản, thì đề viết "đếm học sinh **từ 8,0 trở lên**" trong khi mô hình đang đếm từ 6 — và con số cuối cùng đọc như đáp số của bài gốc. Đó là màn hình **khẳng định một điều sai**, không phải chuyện thẩm mỹ. Chủ sở hữu là SHELL, không phải từng miền: một chỗ so, một nhãn, không miền nào phải tự nhớ. Hai luật của phép so: (a) so bằng **GIÁ TRỊ** — mọi `apply` dựng config mới nên so tham chiếu sẽ báo "đã đổi" vĩnh viễn kể từ thao tác đầu, kể cả khi học sinh vừa quay về đúng chỗ cũ; (b) so **ĐÚNG các khoá module khai** — `web` giữ kiểu trong state nên phải tự dựng lại hình dạng config và nó không giữ `notes` của đề, so cả khối thì mọi đề có `notes` đều "đã đổi" ngay khi vừa mở. Nhãn kêu oan là nhãn bị học sinh học cách phớt lờ, đúng lúc nó cần được đọc. Module KHÔNG khai `currentConfig` ⇒ không so, không nhãn — bài không đổi được tham số thì không lệch được; và thao tác KHÔNG rời đề (bật một đầu vào của mạch logic) phải để nhãn IM | `components/SimulationWorkspace.tsx` (`specDrift` — hàm thuần, tách khỏi JSX vì luật chôn trong JSX là luật chỉ kiểm được bằng trình duyệt) + hợp đồng `currentConfig?` (`simulations/types.ts`) + 7 module khai (`algorithm` · `binary.base_conversion` · `binary.character_encoding` · `network.graph_traversal` · `tree.traversal` · `database` · `web`) | `spec-drift-w4b4d.test.ts` (im lúc mở trên TOÀN danh mục · bật khi đổi ở 8 target · tắt khi quay về giá trị cũ · chỉ so khoá đã khai) · nghiệm thu Chrome 4 bề rộng `frontend/scripts/accept-experience-w4b4c.mjs` (SSR không chạm tới được — zustand trả trạng thái ĐẦU cho server snapshot, xem §8 #13) |

| 26 | **Một lối vào Khám phá phải dẫn tới thao tác CÓ HỆ QUẢ; và "thao tác được" phải đo bằng CỬA THẬT, không bằng cờ khai báo** (W4B-4A/4D). Hai vế của cùng một bất biến. Vế trình bày: module mời vào Khám phá mà không action nào đổi được mô hình thì lời mời là hứa suông (COVERAGE §2.6 cấm bày tương tác trang trí). Vế ĐO: phép đo phủ danh mục từng đọc `!!mod.explore`, mà **mọi** module thuật toán khai chung một khối `explore` — nên cờ ấy `true` kể cả ở bài `explore.entry()` trả `null` và học sinh không thấy cửa nào. Hệ quả đo được: `count_if`/`sum_if` tính là "thao tác được" suốt từ baseline nhờ `whatif_swap` mà chính sách của chúng TẮT — **dương tính giả**, và nó che mất việc hai bài này thật sự không có gì để khám phá. Đọc `explore.entry()` thì hết lọt. Kèm theo: quyết định GIỮ TRACE phải khai lý do **CƠ CHẾ** trong `KEEP_TRACE`, guard hai chiều (thiếu lý do là đỏ; lý do còn sót sau khi target đã có tương tác cũng đỏ — giải thích lỗi thời đánh lừa người đọc sau), và lý do nói "chưa kịp"/"TODO" bị từ chối | `simulations/experience-audit-w4b4a.test.ts` (`hasExploreEntry` + `KEEP_TRACE`, ghi `docs/evaluation/m17/w4b4a-experience/probe.json`) + `domains/algorithm/interaction-policy.ts` (`exploreEntryOf` — không khai `exploreLabel` ⇒ không cửa) + `domains/algorithm/condition-param.ts` (miền đóng của điều kiện: `count_if`/`sum_if` nay có thao tác THẬT) | `experience-audit-w4b4a.test.ts` (phép đo phủ ĐÚNG registry — sàn `rows.length > 10` cũ nuốt mất một target biến mất khỏi catalog) · `explore-ownership-w4b3a.test.ts` (cửa ⇒ hệ quả; và tiền đề "hoán vị không đổi tổng/đếm" nay được ĐO chứ không tin) · `condition-param.test.ts` (từ chối ≠ kẹp) |

| 27 | **Tầng lớp học ĐỌC bằng chứng, KHÔNG phán đúng/sai** (M18). Correctness thuộc về engine tất định và `predict.check`; LLM không phán, và bảng quan sát của giáo viên cũng không. Bảng đó chở TRẠNG THÁI CÓ CẤU TRÚC — vị trí trên timeline (đọc qua hợp đồng `timeline` của module, KHÔNG đọc renderer), cờ Khám phá/Thử thách đang mở, số thao tác, số lần đã cam kết — và không có trường nào tên `verdict`/`correct`/điểm. Cũng KHÔNG chiếu màn hình hay chụp DOM: nặng hơn, lộ nhiều thứ ngoài giờ học hơn, và buộc phải dựng một hạ tầng truyền hình ảnh mà kiến trúc này không có. Đọc màn hình thay vì đọc hợp đồng sẽ khiến bằng chứng lớp học đổi theo renderer nào đang vẽ và panel nào đang mở | `accounts/classroom_router.py::observe_class` + `components/PracticeReporter.tsx` (chuyển state engine → bằng chứng) + `persistence/classroom_models.py::PracticeSession` | `test_classroom_api.py` (bảng quan sát không chứa verdict/correct/score, không chứa screenshot/DOM; con số bị KẸP về miền hợp lệ thay vì tin client) · `accept-classroom-m18.mjs` |

| 28 | **Chữ của giáo viên không bao giờ thành sự thật runtime** (M18). Giao bài = giao một **envelope ĐÃ QUA `SimSpec.validate`**, đúng cổng mà pipeline LLM đi; lời dặn là CHỮ hiển thị cạnh mô phỏng. Hai hệ quả bắt buộc: (a) mở bài KHÔNG gọi LLM — sinh lại lúc mở nghĩa là ba mươi học sinh mở ra ba mươi mô phỏng khác nhau và giáo viên không giao được thứ mình đã xem; (b) config lưu là bản ĐÃ CHUẨN HOÁ của validator, không phải bản thô của client. Bỏ cổng này thì một config engine không chạy nổi sẽ nổ trên màn hình học sinh giữa tiết | `accounts/classroom_router.py::_validated_envelope` + `persistence/classroom_models.py::Assignment.envelope_json` | `test_classroom_api.py` (envelope sai config/target lạ/chưa phân tích xong đều 400; hai học sinh mở ra CÙNG một envelope) · `accept-classroom-m18.mjs` (envelope hỏng ⇒ 400 ở cả 4 bề rộng) |

| 29 | **Vai trò do MÁY CHỦ sở hữu; thanh điều hướng ứng dụng nằm NGOÀI lưới workspace** (M18). Client gửi `role` gì cũng không đổi được quyền — server tra `users.role` theo phiên, và đăng ký thường luôn ra học sinh (vai trò giáo viên cần mã mời; không cấu hình ⇒ ĐÓNG). Vai trò ở frontend là bản chiếu để VẼ: sửa nó trong devtools thì thấy được thanh điều hướng giáo viên và không gọi nổi endpoint nào. Về bố cục: thanh điều hướng mới KHÔNG được lặp lại cột 208px đã gỡ ở W4B-3B — cột đó nằm TRONG lưới workspace nên nó trải qua cả hàng sân khấu lẫn hàng điều khiển và bóp cả hai. Thanh mới nằm ngoài lưới, thu gọn thành dải biểu tượng trong mô phỏng, và thành ngăn kéo tạm dưới 900px | `accounts/policy.py::resolve_signup_role` + `accounts/router.py::Caller.require_role` + `components/AppSidebar.tsx` + `.app-root/.app-nav` (global.css) | `test_auth_api.py` (tự khai giáo viên bị chặn; thiếu cấu hình vẫn đóng) · `test_classroom_api.py` (6 ca từ chối của `§36`) · `ux-shell.test.tsx` (hai vai không dùng chung thanh điều hướng) · `accept-classroom-m18.mjs` (403 ở cả 4 bề rộng) |

| 30 | **Khung mô phỏng lấy bề rộng từ CƠ CHẾ, và mọi thứ của cùng một cơ chế đứng trên MỘT rail** (M19). Trước wave này thẻ luôn 1624px @1920 trong khi mực dao động 276–1597px, và từng renderer tự căn giữa hình bên trong lớp giãn ấy — đo được 23/23 target hỏng, rail lệch tới 722px. Nguyên nhân là một: thẻ là flex column STRETCH nên con nào cũng giãn hết cửa sổ rồi phải tự căn giữa lại. Luật nay: cột nội dung + thẻ đều `fit-content`, có SÀN SƯ PHẠM `min-width` (không bóp sát từng pixel SVG — phải còn chỗ cho nhãn/chú giải/một câu thuyết minh), và MỌI con lấp trọn thẻ nên mép trái của hình CHÍNH LÀ rail của chữ. Khay điều khiển nằm cùng cột nên tự bằng bề rộng thẻ (giữ W4B-3H). SVG sân khấu phải khai bề rộng THẬT qua `stageSvgSize` — `width="100%"` không sizing được cha `fit-content` (Chrome rơi về 300px mặc định) và buộc phải `margin: 0 auto`, chính là rail thứ hai. Ngoại lệ phải KHAI kèm lý do cơ chế: `web.style_model` được bám cửa sổ (trang web lấp bề rộng khả dụng LÀ hành vi đang dạy), `logic.boolean_dag` được đặt chú giải cạnh sơ đồ | `styles/global.css` (`.app-layout` cột `auto` + `.workspace-card` `fit-content` + `.workspace-card > * { width: 100% }`) + `simulations/stage-size.ts` | `frontend/scripts/audit-composition.mjs` — 23 target × 4 bề rộng, hai lỗi tách bạch. **Lỗi A đo bằng câu FALSIFIABLE "khung có bám cửa sổ không"** (so 1920 vs 1366): so mực/khung là không thể sai vì chữ luôn giãn đầy khung. Tiêm lỗi: cột `1fr` + thẻ `100%` ⇒ ĐỎ · căn giữa hình ⇒ ĐỎ rail · nới khoảng cách cột sơ đồ ⇒ ĐỎ ở `dag.test` |

| 31 | **Khung hình thứ `k` suy được HOÀN TOÀN từ `trace[k].memory_snapshot` qua `visual_bindings`, không phụ thuộc gì khác** (2026-08-20). Đây là bất biến khoá trục hiển thị, và nó sinh ra từ một bug đã ship: cầu nối giữ `frames[0].objects` rồi vứt mọi khung sau, nên lời thuyết minh chạy tới bước 15 trong khi ngăn xếp trên hình vẫn RỖNG và các ô giá trị vẫn `0`. Chương trình do AI sinh **đúng**, interpreter chạy **đúng**, trace **đúng** — chỉ khúc nối vứt trạng thái; chẩn đoán nhầm thành "lỗi của AI" sẽ dẫn tới quyết định kiến trúc sai. Hệ quả bắt buộc: envelope mang **toàn bộ** chuỗi khung với snapshot đầy đủ mỗi khung (không delta — logic replay chính là chỗ trục hiển thị lệch khỏi trục ngữ nghĩa); renderer chỉ ĐỌC, được nội suy **pixel** giữa hai khung nhưng **cấm** bịa trạng thái ngữ nghĩa trung gian | `semantic_program/pipeline_adapter.py::compile_semantic_program_to_envelope` + `visual_adapter.py` | `test_frame_state_invariant.py` (envelope giữ đủ mọi khung của adapter; và hồi quy trực tiếp: không được mọi khung đều có ngăn xếp rỗng) |

| 32 | **Gộp bước nằm NGOÀI adapter, và pacer PHÂN HOẠCH chứ không CẮT** (2026-08-20). Gộp đặt trong `VisualTraceAdapter` là phá song ánh `frame k ⇔ trace[k]`, tức phá luôn tư cách định lý của bất biến #31 — nên nó thuộc `PresentationPacer`, chạy sau. Bất biến của pacer yếu hơn nhưng vẫn kiểm được: mỗi bước xem là một đoạn **liên tiếp** các khung máy; các đoạn phân hoạch **đầy đủ**, **không chồng lấn**, **không sinh khung mới**. Ngân sách trình bày tách hẳn ngân sách thực thi: chạm trần trình bày KHÔNG phải lỗi (hạ mức chi tiết cho tới khi vừa, và khai đang xem ở mức gộp nào), còn chạm trần thực thi thì phải BÁO. Gộp hai con số này làm một chính là nguyên nhân gốc của `MAX_REVEAL_STEPS` cắt `steps[:20]` không báo lỗi | `semantic_program/pacer.py::pace` | `test_pacer_partition.py` (phân hoạch đầy đủ · không chồng lấn · tổng khung bảo toàn ở 5000 khung — cắt là ĐỎ) |

| 33 | **Mọi primitive khai trong enum của contract BẮT BUỘC có nhánh xử lý trong adapter** (2026-08-20). Sinh ra từ `bar_chart`: contract liệt kê nó trong `VisualContainerBinding.primitive` nhưng `_adapt_single_step` không có nhánh nào, nên LLM khai `bar_chart` là ra object rỗng — lỗi CÂM, không đỏ ở đâu. Vá riêng một nhánh thì primitive kế tiếp lại rơi y hệt; nên luật là **đối sánh hai chiều** giữa enum và `HANDLED_PRIMITIVES`, thiếu hoặc thừa đều ĐỎ | `semantic_program/visual_adapter.py::VisualTraceAdapter.HANDLED_PRIMITIVES` | `test_primitive_coverage.py` (enum ⊆ handled **và** handled ⊆ enum) · `test_primitive_set_frozen.py` (2026-08-21 — TẬP primitive đã ĐÓNG BĂNG, kèm ba primitive **cố ý loại** và lý do: `graph_editor` vì sửa đồ thị là đổi ĐỀ BÀI chứ không phải tham gia cơ chế · `force_layout` vì layout phải TẤT ĐỊNH, force-directed cho hình khác nhau mỗi lượt nên ảnh chụp hết so được · `camera_3d` vì route này 2D only) |

| 34 | **Binding bắt buộc không phân giải được → FAIL-CLOSED, không render một phần** (2026-08-20). Luật **không phải** "bỏ con trỏ rồi vẫn vẽ phần còn lại" — đó là hạ cấp âm thầm, đúng loại lỗi đã sinh ra bất biến #31 (con trỏ `i` neo vào container rỗng nên đè lên dòng chữ thuyết minh). Một `visual_binding` bắt buộc mà không phân giải được ở **bất kỳ** khung nào là hỏng hợp đồng: adapter/validation thất bại và **không phát canonical envelope**. Học sinh thà không thấy gì còn hơn thấy một cảnh thiếu thành phần mà không ai nói cho biết là đang thiếu. Lưu ý phạm vi: đòi phân giải **ít nhất một lần trong trace**, không đòi ở mọi khung — một con trỏ chưa được gán ở bước 0 là bình thường | `semantic_program/pipeline_adapter.py::_assert_bindings_resolvable` | `test_binding_fail_closed.py` (`VisualBindingUnresolved` khi binding không bao giờ phân giải) |

| 35 | **Thanh bước của Scene3D đi qua BƯỚC DỰNG — một phân hoạch của trace, không phải một trục thứ hai** (W12, 2026-09-30). Review người W12: thanh bước đi qua cả sự kiện chỉ tính số/kết luận, chỉ số tăng mà hình đứng yên. `geometryTimeline` gộp sự kiện thành bước dựng theo đúng khuôn #32 (liên tiếp · đầy đủ · không chồng lấn · không sinh khung): bước mới CHỈ mở ở sự kiện `GEOMETRY_CONSTRUCTION` làm đổi chữ ký hình (vật vẽ được + tiến độ thiết diện); `MEASUREMENT`/`EXPLANATION`/`FINAL_RESULT` nhập vào bước đang mở và lên LỚP LỜI GIẢI (bảng dưới thanh bước). Khung hiện của một bước là `trace[anchor]` với `anchor` = sự kiện cuối đoạn ⇒ #31 giữ nguyên. Loại sự kiện đọc từ `semantic_kind` có cấu trúc — không đoán từ lời kể/tiêu đề/action/id; cảnh không gõ loại ⇒ mỗi sự kiện một bước. Backend không xoá sự kiện nào | `frontend/src/simulations/domains/geometry/scene3d-model.ts` (`geometryTimeline`, `solutionAt`) + `scene3d-playback.tsx` + `scene3d-solution.tsx` | `scene3d-geometry-timeline.test.tsx` (sáu cảnh w11, số bước từ phép đếm ĐỘC LẬP; 0 khung tĩnh; tới/lùi trả đúng snapshot) + bộ đo trình duyệt (`assessGeometrySteps`) |

| 36 | **Một GIVEN phải được CÂU ĐỀ chứng minh — lời khai `analyze` không phải nguồn** (W12, 2026-09-30). Tuyến LLM từng nhận một độ dài chỉ có trong mục `analyze` (đề không ghi) rồi gắn GIVEN. Cổng grounding đọc bằng chứng từ câu đề: độ dài `XY_length` cần con số của đề (nguyên/thập phân `.`/`,`/phân số/căn), không bị nhãn đoạn khác hay đơn vị khác mâu thuẫn; nguyên tử chỉ khớp giá trị P1 không chứng minh được ⇒ `GIVEN_VALUE_NOT_IN_SOURCE`; span P1 không cắt đúng chữ ⇒ `SOURCE_SPAN_MISMATCH`; mâu thuẫn ⇒ `SOURCE_EVIDENCE_CONFLICT`; toạ độ ghim vào mục mang số đề không ghi ⇒ từ chối. Ba mã KHÔNG gửi đi sửa. Lời khai chưa chứng minh không DỰNG bất biến nguồn (vẫn phủ quyết phép chia nó mâu thuẫn). P1 tính lại từ đề, một hàm dùng chung cho biên đóng băng · cổng · bộ phát bất biến. Giới hạn đã khai: kênh toạ độ `model_assumption`/`LAYOUT_DERIVED` vẫn có thể cố định một kích thước đề không cho (`ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION`; w15: đóng trong vùng đa diện — #37) | `semantic_program/grounding_gate.py` (`_bang_chung_do_dai`, `MA_LOI_NGUON`) + `literal_extractor.py::gia_tri_khong_chung_minh_duoc` + `segment_relation.py::_van_ban` + `ai/pipeline.py::KHONG_SUA_NGUON` | `test_source_grounding_closure.py` (tuyến sản phẩm với transport giả, 0 lượt gọi model) + fixture âm `_ungrounded` sáu họ |

| 37 | **Trong vùng đa diện, một giá trị SỐ người học thấy phải có CHỨNG CHỈ — bố cục hay giả thiết của mô hình không được quyết định đáp số** (W15, 2026-10-03). Hai phép dò W12 từng được phục vụ với `V = 30` khi đề không cho AD: chương trình giữ AD bằng toạ độ `LAYOUT_DERIVED`/`model_assumption`, không kênh nào khai GIVEN nên grounding không có gì để kiểm. Nay route chỉ phục vụ giá trị có chứng chỉ (`PROVEN_SAFE`). **C0:** mọi literal trên lát cắt là dữ kiện đề CÙNG thực thể. **C1:** khuôn T1–T6 khớp ràng buộc server đọc từ đề. Lát cắt đi theo định nghĩa với tới DUY NHẤT trên trace, giá trị lấy tại lúc định nghĩa. Phản ví dụ hợp lệ ⇒ `ASSUMPTION_DETERMINES_ANSWER`, nêu đại lượng thiếu; còn lại ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN`. Cả hai từ chối ở chặng `assumption` và KHÔNG gửi đi sửa. Tiền đề chỉ đến từ CÂU ĐỀ (bộ đọc + bộ phát bất biến gọi không kèm hợp đồng) — chú thích quan hệ của mô hình không bao giờ là tiền đề. Phạm vi thi hành theo U3: đề nêu khối đa diện theo từ vựng đóng; ngoài vùng chỉ ghi. Nhiều định nghĩa với tới bị từ chối ở MỌI vùng (U5). W16 (amendment §14): "CÙNG thực thể" gồm cả mặt phẳng cho bằng phương trình — gắn theo tên hoặc duy nhất theo đếm, trùng bộ số không là căn cứ; mọi tiền đề đọc từ đề đã che mệnh đề mục tiêu (`Chứng minh …`, `CMR`, `Kiểm tra …`, câu hỏi) | `semantic_program/assumption_gate.py::kiem_gia_dinh` + `shape_constraint.py` (`doc_rang_buoc`, `phan_chua_doc`, `neu_khoi_da_dien`) + `route.py::_sau_grounding` + `ai/pipeline.py::KHONG_SUA_NGUON` | `test_assumption_gate.py` (tuyến route) · `test_assumption_certificate.py` (C0/C1/phản ví dụ, định nghĩa với tới gồm ca lệnh dựng tự đọc, vai trò literal, metamorphic) · `test_shape_constraint.py` · census vòng 3 + tiêm lỗi FI1–FI14 trong run `w15-assumption-closure` · `test_plane_from_equation.py -k w16` (tên mặt phẳng) + census vòng 2 + tiêm lỗi FG/FA/FB/FD trong run `w16-premerge-closure` |
| 38 | **Một phép cắt được chứng nhận phải là phép cắt ĐỀ nói, và mọi con số trên hình do backend gắn** (W17, 2026-10-04). Giới hạn A′ của W16: (T) cắt bởi (α) đã ghim đúng, trong khi đề nói (β), vẫn được chứng nhận C0 và phục vụ (hiện 9, đề cho 16). Nay mọi `construct_section` trên lát cắt của giá trị hiển thị phải dùng cùng mặt phẳng (theo nguồn, rồi tên/duy nhất; mặt phẳng gọi qua điểm = tập điểm) và cùng khối (tập đỉnh) với câu cắt đọc từ đề đã che mục tiêu. Lệch chắc chắn ⇒ `CONSTRUCTION_NOT_TEXT_BOUND` (nguyên nhân CONSTRUCTION); danh tính không ghim được ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN`. Grounding cũng đọc trên đề đã che mục tiêu ở mọi vùng. Nhãn số đo trên hình: backend gắn đại lượng ↔ chủ thể (độ dài đề cho được kiểm bằng khoảng cách chính xác); frontend chỉ chiếu, đặt chỗ, bật/tắt; nhãn đáp số chỉ có từ bước kết luận. Giới hạn: chỉ phép cắt được đối chiếu với đề (`ISSUE-ARCH-CONSTRUCTION-RELATION-BEYOND-SECTION-CUT`) | `semantic_program/shape_constraint.py::doc_quan_he_cat` + `assumption_gate.py::_kiem_phep_dung` + `grounding_gate.py::check_grounding` + `refusal_cause.py` + `quantity_annotations.py::gan_so_do` + `frontend/src/simulations/domains/geometry/scene3d-annotations.ts` | `test_assumption_certificate.py -k w17` · `test_shape_constraint.py -k w17` · `test_source_grounding_closure.py -k w17` · `test_refusal_cause.py` · `test_scene3d_annotations.py` · `scene3d-annotations.test.ts` · census vòng 2 + tiêm lỗi backend 23/23, frontend 18/18 trong run `w17-operation-annotations` |
| 39 | **Một điểm đề gọi tên bằng quan hệ (trung điểm, hình chiếu) phải được dựng trên ĐÚNG thực thể đề nêu, xét theo DANH TÍNH; mọi số trên hình do backend gắn vai trò, và một nơi giải thích nó** (W18, 2026-10-04). Trước W18, chiếu lên sai đường/mặt, tráo danh sách "lần lượt", đổi tên đích, hay một điểm trùng toạ độ nhưng khác danh tính đều được PHỤC VỤ, vì mọi cổng chỉ hỏi điểm NẰM ĐÂU. Nay chặng `construction_binding` (sau thực thi, trước `source_invariant`) đối chiếu từng phép dựng điểm với quan hệ đọc từ đề (từ vựng đóng) qua các thẩm quyền danh tính sẵn có; toạ độ hay giá trị bằng nhau không bao giờ là bí danh. Lệch ⇒ `CONSTRUCTION_NOT_TEXT_BOUND` ở mọi vùng; chưa đối chiếu được ⇒ `CONSTRUCTION_BINDING_UNVERIFIED` trong vùng đa diện, lời không bao giờ nói đề sai. Trình bày: `role`, `same_as` theo chủ thể, nhân chứng khoảng cách chân chính xác — frontend chỉ lọc theo lựa chọn/"Hiện tất cả", không tính hình. W20 (§17): đích khai bằng toạ độ, trực tiếp hay qua bí danh ⇒ `CONSTRUCTION_REPLACED_BY_COORDINATES` ở mọi vùng. Giới hạn: tâm, giao điểm, cách nói ngoài từ vựng (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`) | `semantic_program/construction_binding.py` (`doc_quan_he_dung`, `doi_chieu_phep_dung`) + `route.py` (chặng `construction_binding`) + `quantity_annotations.py::_nhan_chung` + `scene3d.py::_gan_so_do` + `frontend/src/simulations/domains/geometry/scene3d-annotations.ts::annotationsAt` | `test_construction_binding.py` · `test_scene3d_annotations.py -k w18` · `scene3d-annotations.test.ts` · `Scene3DExplorer.test.tsx` · census W18 + tiêm lỗi backend 12/12 và frontend 12/12 (vòng 2) trong run `w18-binding-focus` · `test_construction_binding_literal.py` + probe, census và tiêm lỗi trong run `w20-cleanup-premerge` |

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
