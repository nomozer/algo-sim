# ALGOSIM — UNIFIED GEOMETRY CAPABILITY EXPANSION & VERIFIED IMAGE-TO-3D REPORT

- **Run Slug:** `unified-angle-geometry-verified-image-to-3d`
- **Wave ID:** `UNIFIED_ANGLE_GEOMETRY_VERIFIED_IMAGE_TO_3D`
- **Branch:** `feat/local-first-geometry-understanding` (single fixed worktree; not merged, not pushed, not deployed)
- **Start Base:** `8eb1cfab7cc515e8b1aca1564fc3913b2775e0a2` (prior product commit `094193d2d02f9438189c1101aa1ff47ae1f9dbb9`)
- **Product Commit SHA:** `c61a3589782bde35b69e8376d8ebf136314e47f3` (`c61a35897`)
- **Measured System Tree Hash:** `69bb83ba51b834f68c106bc4d3948dc02ca35af05eca0d8f50c0e0e4cf047cb4` (`108` measured files, `CACHE_VERSION = 132`)
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`, `OFFLINE_ROUTING_VERIFIED` · `RECORDED_REPLAY_VERIFIED` · `ORACLE_TEXT_DOWNSTREAM_REPLAY` · `LIVE_VISION_NOT_MEASURED`)
- **Component Versions:** `local-geometry-parser/1` · `adaptive-input-router/1` · `typed-fact-next/2` · `typed-fact-next-bridge/2` · `geometry-fact-planner/26` · `geometry-functions/33` · `geometry-function-engine/24` · `hybrid-simulation-adapter/4` · `hybrid-route-d-simulation/4`

---

## I. Executive Summary & Final Acceptance Gates (Section XII)

| Gate | Scope | Status | Epistemic Classification | Authoritative Receipts |
|---|---|---|---|---|
| **Gate A** | Baseline Preservation (`Dev72`, `C26`, `15` strict XFAILs, `38` cached images, Source Gate, Multi-solution) | **`PASS`** (`56/56` `Dev72` supported + `10/10` negative + `6/6` strict XFAIL gaps; `70` `C26` rows & `7/7` section contracts; `38/38` cached external SHA-256 verified) | **`VERIFIED FACT`** | [`baseline_integrity_receipt.json`](baseline_integrity_receipt.json) |
| **Gate B** | Exact Angle-Premise & Dihedral Capability (`line_plane_angle`, `plane_plane_angle`, `dihedral_angle`, `line_line_angle`, `vertex_angle`) | **`PASS`** (`18/18` TDD tests + `6/6` positive + `5/5` negative + `4/4` dihedral cases; acute vs obtuse `[P, edge, Q]` half-plane orientation proved) | **`VERIFIED FACT`** | [`angle_premise_capability_receipt.json`](angle_premise_capability_receipt.json), [`dihedral_angle_correctness_receipt.json`](dihedral_angle_correctness_receipt.json) |
| **Gate C** | Reusable Base Geometry Expansion (`CURRICULUM-FAMILY-1` & `CURRICULUM-FAMILY-2`, distinct from `DEV72-G2/G3`) | **`PASS`** (`7/7` test groups / `26` sub-scenarios + `2` promoted `test_05a` cases; bare `hình thoi` strictly refuses `MISSING_DIMENSION` without assuming `60°`) | **`VERIFIED FACT`** | [`base_geometry_family1_receipt.json`](base_geometry_family1_receipt.json), [`base_geometry_family2_receipt.json`](base_geometry_family2_receipt.json), [`schema-census-extension.json`](schema-census-extension.json) |
| **Gate D** | Verified Image-to-Geometry Pipeline (`38` external images, `verify_ocr_input_fidelity`, `reconcile_dual_ocr_texts`, Vision fallback) | **`PASS`** (`38/38` noisy/diagram/handwritten raw OCR safely blocked; `11/11` shared dual-OCR corruption probes blocked; `ORACLE_TEXT_DOWNSTREAM_REPLAY` promoted `2/17 -> 4/17` solved + `2/17` `MISSING_DIMENSION`; `0` wrong-served) | **`VERIFIED FACT` (offline/recorded) / `NOT_MEASURED` (live Gemini Vision)** | [`external_image_pipeline_receipt.json`](external_image_pipeline_receipt.json), [`ocr_fidelity_regression_receipt.json`](ocr_fidelity_regression_receipt.json), [`adaptive_vision_fallback_receipt.json`](adaptive_vision_fallback_receipt.json) |
| **Gate E** | Mathematical & 12-Point `Scene3D` Parity | **`PASS`** (`100%` match vs pure-stdlib `Fraction` independent oracle; `12/12` `Scene3D` parity checks passed on all `16/16` verified configurations; non-unique circle-locus foot emits `0` arbitrary `Scene3D`) | **`VERIFIED FACT`** | [`exact_kernel_independent_oracle.json`](exact_kernel_independent_oracle.json), [`scene3d_geometry_parity_receipt.json`](scene3d_geometry_parity_receipt.json), [`planner_composition_verification.json`](planner_composition_verification.json) |
| **Gate F** | Resource Efficiency & Low-End Compatibility | **`PASS_HOST_AND_CONSTRAINED_MEASURED`** (`0 MB` `VietOCR-HW ONNX` bloat in default routes; `NO_RUST_NEEDED`; real Chrome `Scene3D` `216–347 ms` first frame, `>130 FPS` orbit; physical 2-core/4 GB laptop `NOT_MEASURED`) | **`VERIFIED FACT` (host & single-thread env) / `NOT_MEASURED` (physical low-end device)** | [`low_end_performance_impact.json`](low_end_performance_impact.json) |
| **Gate G** | Independent `H-1` Evaluation | **`NOT_MEASURED`** (`EXTERNAL_SOURCE_AVAILABLE`, `INDEPENDENT_GROUND_TRUTH_PENDING`; 8-layer contamination scanner run; non-independent diagnostic sets never relabeled as `H-1`) | **`NOT_MEASURED` / `BLOCKED`** | [`independent_corpus_readiness.json`](independent_corpus_readiness.json), [`generalization_evaluation_receipt.json`](generalization_evaluation_receipt.json) |
| **Gate H** | Full Regression, Publication Safety & Candidate Freeze | **`PASS`** (`14,138` backend pytest passed, `0` failed, `15` strict XFAILs preserved; `2,000` frontend Vitest passed; `9/9` + `5/5` Chrome E2E; `5/5` demo replay; `6/6` crash surface; docs IA & publication safety `PASS`; `EVALUATION_CANDIDATE.json` frozen) | **`VERIFIED FACT`** | [`full_regression_summary.json`](full_regression_summary.json), [`run.json`](run.json) |

---

## II. Direct Answers to All 23 Mandatory Questions (Section XIV)

### 1. Đã mở rộng được những quan hệ góc nào?
- **Classification:** `VERIFIED FACT`
- **Answer:** Đã mở rộng khả năng biểu diễn có nguồn dẫn, lập kế hoạch kết hợp và giải chính xác trên `Fraction`/`Radical` cho **5 nhóm giả thiết góc khả hợp** ([`angle_premise_capability_receipt.json`](angle_premise_capability_receipt.json)):
  1. **`line_plane_angle` (`30°, 45°, 60°`):** Suy diễn hai chiều chính xác giữa chiều cao $h$, độ dài hình chiếu ngang $d$ và cạnh xiên $L$ ($h = L\sin\theta = d\tan\theta$, suy ngược cạnh đáy khi đã biết chiều cao lăng trụ/chóp, kết hợp trung điểm/đường cao đáy, và định vị tâm đường tròn ngoại tiếp đáy khi các cạnh bên cùng tạo góc bằng nhau với mặt đáy).
  2. **`plane_plane_angle` (`30°, 45°, 60°, 90°`):** Góc không định hướng giữa hai mặt phẳng trong $[0^\circ, 90^\circ]$ (suy ra chiều cao khối chóp/lăng trụ từ khoảng cách chân đường cao tới giao tuyến: $h = d_\perp \tan\theta$).
  3. **`dihedral_angle` (`[P, edge, Q]` với `30°, 45°, 60°, 90°, 120°, 135°, 150°`):** Góc nhị diện định hướng giữa hai nửa mặt phẳng bờ giao tuyến trong $(0^\circ, 180^\circ)$, kiểm tra cả giá trị $\cos^2\varphi \in \mathbb{Q}$ và dấu tích vô hướng $\langle \vec{r}_P, \vec{r}_Q \rangle_G$.
  4. **`line_line_angle` (`30°, 45°, 60°, 90°`):** Góc không định hướng giữa hai đường thẳng cắt nhau / đồng phẳng thuộc $[0^\circ, 90^\circ]$.
  5. **`vertex_angle` (`30°, 45°, 60°, 90°, 120°, 135°, 150°`):** Góc phẳng định hướng tại đỉnh 3 điểm ($\angle UVW \in (0^\circ, 180^\circ)$) phục vụ tam giác SAS, hình thoi, hình bình hành và hình thang cân.

### 2. Những dạng góc nào vẫn chưa hỗ trợ?
- **Classification:** `VERIFIED FACT`
- **Answer:** Hệ thống từ chối an toàn (fail-closed) đối với các dạng góc ngoài miền đại số chính xác hoặc chưa đủ ràng buộc xác định duy nhất:
  - Góc có $\cos^2\theta \notin \mathbb{Q}$ hoặc làm phát sinh tích Gram vô tỉ ngoài trường hữu tỉ $\mathbb{Q}$ (ví dụ $37^\circ$, hoặc tam giác cân hai cạnh $a$ xen góc $45^\circ$ có $BC^2 = (2-\sqrt{2})a^2 \notin \mathbb{Q}$) $\rightarrow$ từ chối `EXACT_DOMAIN_EXCEEDED`.
  - Góc giữa hai mặt bên xiên hoặc góc giữa hai đường thẳng chéo nhau không vuông góc dùng để suy ngược kích thước cạnh đáy (ví dụ `ext_prt_07_hd_q_1084979`) $\rightarrow$ từ chối `MISSING_DIMENSION` / `CAPABILITY_GAP`.
  - Câu hỏi yêu cầu xuất *số đo góc theo đơn vị độ* (`"Tính số đo góc..."`) thay vì biểu diễn lượng giác chính xác `cos²=...` $\rightarrow$ giữ nguyên chính sách từ chối `QUESTION_CONTEXT_UNSUPPORTED`.

### 3. Có phân biệt đúng line-plane angle và dihedral angle không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Có, phân biệt chặt chẽ ở cả 4 tầng (Parser $\rightarrow$ TypedFactNext `/2` $\rightarrow$ Source Gate $\rightarrow$ Exact Kernel `/24`):**
  - `line_plane_angle` dùng quan hệ $\sin\theta = \frac{|\langle \vec{u}, \vec{n} \rangle|}{\|\vec{u}\|\cdot\|\vec{n}\|} \in [0, 1]$ ($\theta \in [0^\circ, 90^\circ]$).
  - `plane_plane_angle` là góc giữa hai mặt phẳng không định hướng trong $[0^\circ, 90^\circ]$ ($\cos\theta = \frac{|\langle \vec{n}_1, \vec{n}_2 \rangle|}{\|\vec{n}_1\|\cdot\|\vec{n}_2\|}$).
  - `dihedral_angle` `[P, BC, Q]` chiếu trực giao $P$ và $Q$ lên hai tia $\vec{r}_P \perp BC$, $\vec{r}_Q \perp BC$ xuất phát từ giao tuyến $BC$ và bắt buộc kiểm tra **cả độ lớn $\cos^2\varphi$ lẫn dấu của $\langle \vec{r}_P, \vec{r}_Q \rangle_G$**: trên hình chóp $S.ABCD$ đáy hình vuông cạnh $2a$, $SA \perp (ABCD)$, góc nhị diện `[S, BD, A] = 60°` ($\cos > 0$) và góc nhị diện bù `[S, BD, C] = 120°` ($\cos < 0$, vì $A$ và $C$ nằm khác phía đối với $BD$) đều giải đúng $V = \frac{4a^3\sqrt{6}}{3}$, trong khi `[S, BC, A] = 120°` trên $S.ABC$ có $SA \perp (ABC)$ bị từ chối chính xác với `INCONSISTENT_FACTS` vì $SA \perp (ABC)$ buộc `[S, BC, A] < 90°`. Nếu đề chỉ viết `"góc nhị diện cạnh BD bằng 60°"` mà không nêu hai nửa mặt phẳng thì từ chối `AMBIGUOUS_FACT` ([`dihedral_angle_correctness_receipt.json`](dihedral_angle_correctness_receipt.json)).

### 4. Planner có tự kết hợp các primitive không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Có.** `Planner /26` (`planner.py`) tự động lựa chọn và sắp xếp thứ tự phụ thuộc giữa các primitive trong `Registry /33` (`pyramid`/`prism`, `rhombus`/`parallelogram`/`trapezoid`/`isosceles_trapezoid`, `right_angle`, `vertex_angle`, `line_plane_angle`, `plane_plane_angle`, `dihedral_angle`, `midpoint`, `orthogonal_projection`, `intersect_line_line`, `ask_volume`, `ask_distance_point_plane`, `ask_length`), bao gồm cả tìm kiếm bước trung gian động bậc 2 (`DISCOVERED_FUNCTION_COMPOSITION`, `search_generated_steps != []`) trên mặt đáy hình thoi mới mở rộng ([`planner_composition_verification.json`](planner_composition_verification.json)).

### 5. Có handler đặc thù theo từng bài toán không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Không (`0` problem-specific handlers).** Toàn bộ cây mã sản phẩm `backend/app/` đã được quét tự động trong [`planner_composition_verification.json`](planner_composition_verification.json): `0` nhánh theo `case_id`, tên tệp ảnh, nhãn đỉnh cố định hay đáp số mẫu. Mọi primitive mới (`parallelogram`, `rhombus`, `trapezoid`, `isosceles_trapezoid`, `line_plane_angle`, `plane_plane_angle`, `dihedral_angle`, `vertex_angle`) đều là hàm hình học tổng quát bất biến dưới phép đổi tên đỉnh (`S.ABCD -> T.MNPQ -> K.MNPQ`), đảo thứ tự mệnh đề và co giãn tỉ lệ tham số.

### 6. Exact Kernel có trả kết quả chính xác không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Có.** Toàn bộ phép dựng tọa độ khung chuẩn, tích vô hướng ma trận Gram $G \in \mathbb{Q}^{3\times 3}$, bình phương khoảng cách, diện tích, thể tích và $\cos^2$ đều thực thi trên `fractions.Fraction` và `Radical` chính xác, **0 làm tròn số thực dấu phẩy động**. Đối chiếu độc lập với bộ tính công thức đóng thuần `fractions.Fraction` không dùng chung mã với `engine.py` đạt **`14/14` (`100.0%`) khớp tuyệt đối** ([`exact_kernel_independent_oracle.json`](exact_kernel_independent_oracle.json)).

### 7. Các trường hợp thiếu dữ kiện và đa nghiệm được xử lý ra sao?
- **Classification:** `VERIFIED FACT`
- **Answer:** Hệ thống xử lý fail-closed và phân biệt rõ bản chất toán học:
  - **Thiếu kích thước xác định (`MISSING_DIMENSION`):** Hình thoi chỉ cho cạnh mà không cho góc/đường chéo, hình thang thiếu đáy hoặc chiều cao, tam giác cân thiếu cạnh đáy/đường cao, lăng trụ thiếu cạnh bên (`ext_prt_02`, `ext_prt_03#1`) $\rightarrow$ từ chối `MISSING_DIMENSION` và định tuyến về `LOCAL_AMBIGUOUS_CLARIFICATION`.
  - **Quỹ tích chân đường cao chưa xác định duy nhất (`UNDERDETERMINED_POINT`):** Ví dụ cho $S.ABC$ đều cạnh $a$, $SA = 2a$ và $\angle(SA, (ABC)) = 30^\circ$ (chân đường cao $H$ chạy trên đường tròn tâm $A$ bán kính $a\sqrt{3}$ nên $S.ABC$ chưa xác định duy nhất) $\rightarrow$ từ chối `UNDERDETERMINED_POINT`, **không dựng `Scene3D` tùy tiện** (`arbitrary_scene3d_emitted = False`).
  - **Chưa nêu đủ toán hạng định danh góc (`AMBIGUOUS_FACT`):** `"có một góc bằng 60°"` trên hình thoi khi hỏi $SC$, hoặc `"góc nhị diện cạnh BD bằng 60°"` thiếu tên hai nửa mặt phẳng $\rightarrow$ từ chối `AMBIGUOUS_FACT` kèm `route-d-clarification/1`.
  - **Đa nghiệm đối xứng qua mặt đáy ($2^{m-1}$ nhánh dấu `MULTI_SOLUTION_POLICY`):** Nếu mọi đại lượng được hỏi bất biến trên các nhánh hợp lệ thì phục vụ kết quả chứng minh được; nếu đại lượng nhạy gương (như $|SP|$ giữa hai đỉnh khác phía/cùng phía) chưa được đề phân biệt thì từ chối `AMBIGUOUS_FACT`.

### 8. FAMILY-1 hỗ trợ được những cấu hình nào?
- **Classification:** `VERIFIED FACT`
- **Answer:** `CURRICULUM-FAMILY-1` (tách biệt hoàn toàn với `DEV72-G2` vốn là bài toán điểm mô tả trong toán hạng đường thẳng ở `bridge_v2`) hỗ trợ đầy đủ 4 nhóm cấu hình đáy khả hợp ([`base_geometry_family1_receipt.json`](base_geometry_family1_receipt.json)):
  1. **Hình thang vuông (`right_trapezoid`):** Khai báo `"hình thang vuông tại A và B"` hoặc diễn đạt tương đương hai cạnh đáy song song kèm góc vuông (`"AD song song với BC, góc DAB bằng 90°"`), cho trực tiếp hai đáy + cạnh bên vuông góc hoặc suy ra cạnh bên vuông góc từ hai đáy + cạnh bên xiên qua định lý Pythagoras.
  2. **Hình thang cân (`isosceles_trapezoid`):** Hai đáy song song kèm độ dài cạnh bên, đường chéo, hai đường chéo vuông góc, hoặc góc ở đáy (`30°/45°/60°/120°/135°/150°`).
  3. **Tam giác cân (`isosceles_triangle`):** `"tam giác cân tại <đỉnh>"` cho cạnh bên + cạnh đáy, hoặc cạnh đáy + đường cao hạ từ đỉnh cân, hoặc góc ở đỉnh/đáy trong miền hữu tỉ Gram.
  4. **Đường cao tam giác có tên (`triangle_altitude`):** `"đường cao AH của tam giác ABC bằng ..."` gắn chứng chỉ nguồn chặt chẽ và kết hợp trực tiếp với các giả thiết góc/khoảng cách không gian.

### 9. FAMILY-2 hỗ trợ được những cấu hình nào?
- **Classification:** `VERIFIED FACT`
- **Answer:** `CURRICULUM-FAMILY-2` (tách biệt hoàn toàn với `DEV72-G3` vốn là mục tiêu có hai điểm mô tả trong `bridge_v2`) hỗ trợ đầy đủ 3 nhóm cấu hình khung Gram hữu tỉ ([`base_geometry_family2_receipt.json`](base_geometry_family2_receipt.json)):
  1. **Hình thoi (`rhombus`):** Cho cạnh + góc có tên đỉnh (`60°` hoặc `120°`, tự động suy góc kề bù tương ứng), cho hai đường chéo vuông góc tại trung điểm (`AC, BD`), hoặc cho cạnh + một đường chéo. **Tuyệt đối không tự giả định góc `60°`** khi đề chỉ nói `"hình thoi cạnh a"` (`FAM2-NEG-BARE-RHOMBUS-NO-60-ASSUMPTION -> MISSING_DIMENSION`).
  2. **Hình bình hành (`parallelogram`):** Cho hai cạnh kề + góc xen giữa có tên đỉnh (`30°/45°/60°/90°/120°/135°/150°` khi tích vô hướng thuộc $\mathbb{Q}$) hoặc hai cạnh kề + một đường chéo.
  3. **Tam giác biết hai cạnh và góc xen giữa (`triangle_sas`):** Áp dụng định lý cosin chính xác $c^2 = a^2 + b^2 - 2ab\cos\gamma \in \mathbb{Q}$ (gồm cả `60°`, `90°`, `120°`, và `45°/135°` khi tích độ dài khử căn như $AB = a\sqrt{2}, AC = 2a, \angle BAC = 45^\circ \Rightarrow BC = a\sqrt{2}$; từ chối `EXACT_DOMAIN_EXCEEDED` khi $2ab\cos\gamma \notin \mathbb{Q}$).

### 10. Bao nhiêu bài cũ vẫn PASS?
- **Classification:** `VERIFIED FACT`
- **Answer:** **100% các bài toán và hợp đồng baseline cũ vẫn PASS không suy giảm** ([`baseline_integrity_receipt.json`](baseline_integrity_receipt.json), [`full_regression_summary.json`](full_regression_summary.json)):
  - **`Dev72`:** `56/56` bài dương đã hỗ trợ vẫn giải đúng chính xác (`0` AI calls), `10/10` bài âm vẫn từ chối đúng, `6/6` gap probes (`PL5, PA3, MG5, SE3, MG9, RE10`) giữ nguyên từ chối an toàn.
  - **`C26` (`70` ca live-replay):** Bảo toàn toàn bộ kết quả replay và cả **`7/7`** ca hợp đồng nghiêm ngặt `construct_plane_section` (`K-A01..K-A04, R1-B01, R1-B02, R1-C02`).
  - **Toàn bộ pytest backend:** **`14,138 passed, 9 skipped, 1 deselected, 15 xfailed, 0 failed`** (tất cả `15` strict XFAILs giữ nguyên).
  - **Toàn bộ Vitest frontend + build + demo:** **`2,000/2,000`** Vitest tests passed (`136/136` files), `5/5` demo replay PASS, `6/6` crash surface PASS.

### 11. Bao nhiêu bài mới được giải đúng?
- **Classification:** `VERIFIED FACT`
- **Answer:** Trên các bộ kiểm thử phát triển, biến đổi đẳng cấu và đối chiếu văn bản đề thực tế (`0` AI calls, kiểm chứng độc lập bằng oracle):
  - **Bộ kiểm thử TDD & biên nhận mới:** `18` bài/nhóm kiểm thử góc & nhị diện trong [`test_angle_premise_and_dihedral_geometry.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_angle_premise_and_dihedral_geometry.py), `26` kịch bản dương/âm trong [`test_reusable_base_geometry_families.py`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/backend/tests/geometry/test_reusable_base_geometry_families.py), `3` bài kiểm thử biến đổi đổi tên đỉnh/đảo câu/co giãn tỉ lệ (`META-01..03`), và **`2` bài toán trước đây bị chặn không hỗ trợ trong `test_correctness_ocr_performance.py::test_05a`** (chóp đáy hình thoi `∠BAD = 60°` $\rightarrow$ `8√3`; chóp đáy tam giác cân tại `A` $\rightarrow$ `16`) nay đã giải chính xác hoàn toàn.
  - **Tập 17 câu đề thi bên ngoài (`ORACLE_TEXT_DOWNSTREAM_REPLAY`):** Tăng gấp đôi số câu đề thực tế giải đúng hoàn chỉnh từ **`2/17` lên `4/17`** (`+2` câu đề thiếu chiều cao được phát hiện chính xác `MISSING_DIMENSION` = **`6/17` xử lý trọn vẹn ở `LOCAL_PARSE_COMPLETE` với `0` AI calls**), cụ thể giải mới thành công câu đề chữ in `ext_prt_01_hd_q_5259753#1` (`"a³√3/3"`) và câu đề viết tay `ext_hw_b1_01_hd_a_6043187#1` (`"a³√3"`) hoàn toàn nhờ kết hợp các primitive tổng quát mà không hề viết quy tắc riêng cho đề.

### 12. Có bài nào wrong-served không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **`0` (`wrong_served = 0`)** trên toàn bộ mọi tập đã đo: `Dev72` (`0/72`), `C26` (`0/70`), các bộ kiểm thử Gate 1 & Gate 2 (`0`), `38` ảnh OCR thực tế bên ngoài (`0/38`), `11` phép thử làm hỏng ký hiệu OCR đơn và kép (`0/11`), và `17` câu đề bên ngoài (`0/17`).

### 13. Scene3D có đúng với phép dựng toán học không?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Có.** Toàn bộ **`16/16` cấu hình hình học mới** được kiểm tra tự động qua **12 tiêu chí `Scene3D` bắt buộc (Section VIII)** trong [`scene3d_geometry_parity_receipt.json`](scene3d_geometry_parity_receipt.json): (1) đáp số khớp chứng chỉ đại số, (2) đúng loại khối đa diện, (3) đủ đỉnh/cạnh/mặt/đại lượng, (4) tích vô hướng và tích có hướng trên ma trận Gram `chart_metric` xác nhận chính xác quan hệ vuông góc/song song, (5) vị trí chân đường cao đúng tọa độ chứng minh, (6) góc đường-mặt, góc đỉnh và **dấu định hướng nửa mặt phẳng của góc nhị diện nhọn `60°` vs tù `120°`** trên tọa độ 3D khớp tuyệt đối với đề bài, (7) đủ các bước dựng kèm `step_summary`, (8) đúng thứ tự phụ thuộc tô-pô, (9) **0 điểm của bước tương lai xuất hiện sớm** (`validate_construction_continuity == []`), (10) giữ nguyên khung chuẩn `canonical_chart_v1` cho quay/phóng to/thu nhỏ, (11) liên tục tích lũy giữa các bước, và (12) khung cuối khớp cấu hình đã chứng minh. Khi bài toán có quỹ tích chân đường cao là đường tròn chưa xác định duy nhất (`ANG-NEG-NONUNIQUE-FOOT`), hệ thống từ chối và **không sinh `Scene3D` tùy tiện**.

### 14. Đường ảnh thực → geometry đã được kiểm chứng đến đâu?
- **Classification:** `VERIFIED FACT` (offline routing, OCR fidelity & recorded replay) / `NOT_MEASURED` (live Gemini Vision)
- **Answer:** Đã kiểm chứng toàn diện **4 đường đầu vào tách biệt** (`Text`, `Printed image`, `Handwritten image`, `Mixed text + diagram`) trên bộ `38` ảnh thực tế lưu tại `.superpowers/external_image_cache/` cùng các payload OCR/Vision ghi nhận ([`external_image_pipeline_receipt.json`](external_image_pipeline_receipt.json), [`ocr_fidelity_regression_receipt.json`](ocr_fidelity_regression_receipt.json), [`adaptive_vision_fallback_receipt.json`](adaptive_vision_fallback_receipt.json)):
  - Đã phát hiện và vá **3 lỗ hổng thực tế trong `adaptive_input_router.py`**: (i) chặn `reconcile_dual_ocr_texts` vô tình bỏ qua cờ `has_diagram=True` / `has_figure=True` và `is_handwritten=True`; (ii) bổ sung nhận diện cụm tham chiếu hình vẽ thực tế của đề thi VMMU (`như hình bên`, `tham khảo hình bên`, `xem hình vẽ`, `ghi trên hình`) và kiểm tra miền độ $(0^\circ, 180^\circ)$ chống lỗi OCR đọc nhầm `60° -> 600°`; (iii) mở rộng `_OCR_CORRUPTION_ARTIFACT_RE` bắt các lỗi thực tế `aV7`, `S,ABCD`, `ABC-ABC`, `S.A8CD`, `48C`, `2/2/2/2` và vạch phân số nhiều dòng `\n---\n` để cả khi hai engine OCR cùng đọc sai cũng không lọt vào Kernel, đồng thời rác OCR chữ viết tay không chặn nhầm kết quả Vision hợp lệ ở bước kiểm tra xung đột.
  - Đã chứng minh rõ sự phân tách giữa **`OFFLINE_ROUTING_VERIFIED`**, **`RECORDED_REPLAY_VERIFIED`** (ví dụ ảnh viết tay `hd_a_6043187` có OCR lỗi nặng được chuyển sang bản chép Vision đã ghi nhận $\rightarrow$ Local Parser $\rightarrow$ Planner $\rightarrow$ Exact Kernel $\rightarrow$ `Scene3D` giải đúng `"a³√3"`), **`ORACLE_TEXT_DOWNSTREAM_REPLAY`** (`4/17` câu đề giải đúng + `2/17` phát hiện thiếu kích thước), và **`LIVE_VISION_NOT_MEASURED`** (`0` cuộc gọi Gemini thật do `ALLOW_LIVE_AI = 0`).

### 15. Bao nhiêu ảnh giải được hoàn toàn từ OCR local?
- **Classification:** `VERIFIED FACT`
- **Answer:**
  - Trên **38 ảnh bên ngoài thực tế** trong `.superpowers/external_image_cache/`: **`0/38` ảnh** được phép vượt qua cổng `verify_ocr_input_fidelity` chỉ bằng OCR cục bộ (`local_ocr_served_correctly = 0`, `ocr_rejected_safely = 38`, `wrong_served = 0`), bởi vì 16 ảnh viết tay và 7 ảnh chỉ có hình vẽ bị chặn theo đúng thiết kế, còn 15 ảnh chữ in bên ngoài đều kèm hình minh họa (`has_diagram=True` / câu tham chiếu hình) hoặc nhiễu ký hiệu toán học từ camera/scan.
  - Trên **ảnh chữ in tự chứa không phụ thuộc hình vẽ (`Case A`)** khi OCR hai engine sạch và đồng thuận 100% token toán học (như `s05_dau_tieng_viet` clean hoặc đề in tự chứa): hệ thống giải trực tiếp qua `LOCAL_OCR_VERIFIED_ZERO_AI` với **`0` cuộc gọi AI** (`"5√2/3"`, `"a³√3/2"`).

### 16. Bao nhiêu ảnh cần Vision hoặc xác nhận?
- **Classification:** `VERIFIED FACT`
- **Answer:** Trong **38 ảnh bên ngoài**:
  - **16/38 ảnh chứa đề toán hoàn chỉnh** (`15` ảnh đề chữ in + `1` ảnh đề viết tay `B1` `hd_a_6043187.jpg`, trong đó `hd_q_7509702.jpg` còn yêu cầu chọn 1 trong `2` câu đề trên trang) được định tuyến an toàn sang **Vision fallback (hoặc xác nhận của người dùng khi có xung đột số liệu)**.
  - **22/38 ảnh không chứa đề hoàn chỉnh** (`9` ảnh vở giải viết tay `B2`, `7` ảnh cắt riêng hình 3D `Nhóm D`, `6` ảnh dòng chữ viết tay rời `B3`) bị chặn/từ chối an toàn hoặc yêu cầu xác nhận, tuyệt đối không tự giả định có đề toán hoàn chỉnh.

### 17. Vision đã được kiểm thử live hay mới offline?
- **Classification:** `VERIFIED FACT`
- **Answer:** **Mới kiểm thử offline (`OFFLINE_ROUTING_VERIFIED` và `RECORDED_REPLAY_VERIFIED`); chưa kiểm thử Gemini Vision live (`LIVE_VISION_NOT_MEASURED`, `live_gemini_calls = 0`)** theo đúng quy định `ALLOW_LIVE_AI = 0` của nhiệm vụ. Tuyệt đối không tuyên bố `LIVE_IMAGE_TO_GEOMETRY_VERIFIED`.

### 18. Có cải thiện được khả năng nhận diện ký hiệu viết tay không?
- **Classification:** `VERIFIED FACT`
- **Answer:**
  - **Về kiểm định an toàn ký hiệu viết tay & điều phối fallback:** **Có cải thiện thực chất.** Đã bổ sung kiểm tra `is_handwritten` và các mẫu lỗi ký hiệu viết tay thực tế từ `VietOCR-HW ONNX` (`aV7`, `ABC-ABC`, `2/2/2/2`, độ thiếu ký hiệu `°`) trong `adaptive_input_router.py`, đảm bảo: (1) đầu ra OCR viết tay bị hỏng ký hiệu toán không bao giờ tự đi vào Exact Kernel, và (2) khi có kết quả Vision hợp lệ, rác ký hiệu của OCR viết tay không còn gây chặn giả `OCR_VISION_MATH_CONFLICT`, giúp luồng `Handwritten Image -> Recorded Vision -> Local Parser -> Exact Kernel -> Scene3D` giải trọn vẹn bài viết tay `hd_a_6043187` ra `"a³√3"`.
  - **Về bộ trọng số mô hình nhận dạng chữ viết tay (`VietOCR-HW ONNX`):** **Giữ nguyên ở trạng thái chẩn đoán (`LOCAL_OCR_DIAGNOSTIC_ONLY`, không huấn luyện lại và không nạp mặc định)** vì bộ từ vựng tiền huấn luyện thiếu `√, ⊥, ∥, °`; không đoán mò ký hiệu toán bằng ngữ cảnh.

### 19. Tài nguyên RAM/CPU thay đổi thế nào?
- **Classification:** `VERIFIED FACT` (host & single-thread env) / `NOT_MEASURED` (physical low-end laptop)
- **Answer:** Đo thực nghiệm trong [`low_end_performance_impact.json`](low_end_performance_impact.json) xác nhận **không phát sinh gánh nặng tài nguyên hay rò rỉ bộ nhớ**:
  - **Model & RAM:** `VietOCR-HW ONNX` không được nạp trong tiến trình mặc định (`vietocr_hw_onnx_loaded_by_default = False`, **`0.0 MB` bloat**). Qua 50 lượt giải liên tiếp các bài toán góc & hình đáy mới, RSS chỉ dịch chuyển từ **`114.62 MB` lên `114.92 MB` (`+0.30 MB`)**, `tracemalloc` đỉnh **`854.54 KB`**, bộ đệm `_PARSER_CACHE` giữ trần cứng `<= 256` mục (`unbounded_memory_growth = False`).
  - **Độ trễ CPU trên máy phát triển (`HOST_BENCHMARK`) và chế độ đơn luồng (`OMP_NUM_THREADS=1`):** Local Parser cold `p50 = 10.683 ms` (`p95 = 17.485 ms`) và cached **`p50 = 0.048 ms`** (`p95 = 0.065 ms`); Planner `p50 = 0.418 ms`; Registry Source Gate `p50 = 7.920 ms`; Exact Kernel tổng thể **`p50 = 12.801 ms`** (`p95 = 20.903 ms`; baseline chóp vuông `11.107 ms`, góc mới `20.864 ms`, `FAMILY-1` hình thang vuông `13.444 ms`, `FAMILY-2` hình thoi `12.145 ms`); Region Detection trên ảnh chụp đề thực `p50 = 22.925 ms`; Adaptive Router E2E cached **`p50 = 24.211 ms`** (`p95 = 34.645 ms`); chế độ đơn luồng `OMP_NUM_THREADS=1` đạt **`p50 = 29.241 ms`** ([`low_end_performance_impact.json`](low_end_performance_impact.json)).
  - **Trình duyệt thực (`Scene3D` trên Headless Chrome):** Thời gian lên khung hình 3D khả dụng đầu tiên đạt **`216.3–346.6 ms`**, bộ nhớ JS Heap chỉ **`14.18–17.41 MB`**, tốc độ quay quỹ đạo chuột đạt **`130.0–143.0 FPS`**, `0` lỗi console trên cả 5 cấu hình baseline và mới.
  - **Thiết bị vật lý cấu hình thấp (2 nhân / 4 GB RAM thật):** Ghi nhận trung thực là **`NOT_MEASURED`**.

### 20. H-1 độc lập đã đo được chưa?
- **Classification:** `NOT_MEASURED` / `BLOCKED`
- **Answer:** **Chưa (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`, `INDEPENDENT_GROUND_TRUTH_PENDING`).** Bộ quét chống nhiễm bẩn 8 lớp (`scan_eight_layer_contamination` trong `score_independent_holdout_equivalence.py`) đã sẵn sàng và đã chạy kiểm tra trên các câu đề bên ngoài ([`independent_corpus_readiness.json`](independent_corpus_readiness.json)), nhưng vì 17 câu đề bên ngoài đã được đọc khi phân tích khoảng trống năng lực nên chúng được phân loại trung thực là tập đánh giá chẩn đoán/phát triển, không bao giờ gắn nhãn thành `H-1` độc lập mù. Việc đo `H-1` cần một bộ đề độc lập có ground truth do chuyên gia con người xác minh trước khi chạy hệ thống và ngân sách chiến dịch live được Owner phê duyệt.

### 21. Những capability nào nên mở rộng tiếp?
- **Classification:** `INFERENCE` (dựa trên phân bố 11/17 câu đề bên ngoài còn fail-closed và 6 strict XFAIL của `Dev72`)
- **Answer:** Theo thứ tự tác động thực nghiệm cao nhất trên đề thi THPT thực tế:
  1. **Tỉ số tổng quát trên cạnh bên & tỉ số thể tích / diện tích thiết diện tổng quát** (`SE = 3EC`, `KC/KB`, tỉ số `S1/S2` như `ext_prt_04_hd_q_8436784`, `ext_prt_05_hd_q_7451806`).
  2. **Mở rộng hợp đồng cầu nối `bridge_v2` cho điểm mô tả (`DEV72-G2` `PL5, PA3` và `DEV72-G3` `MG5`)** — đường thẳng đi qua điểm mô tả và khoảng cách giữa hai điểm mô tả không đặt tên.
  3. **Giả thiết diện tích mặt bên / thiết diện để suy ngược cạnh hoặc chiều cao** (như `ext_prt_12_vmmu_page_r11` cho diện tích mặt bên lăng trụ bằng `12 cm²`).
  4. **Biểu diễn góc đầu ra theo đơn vị độ cho các góc đặc biệt (`30°, 45°, 60°, 90°`)** khi câu hỏi hỏi trực tiếp số đo độ (như `ext_prt_11_vmmu_page_r10`), nếu Owner đồng ý mở rộng chính sách đầu ra góc.

### 22. Có cần Rust hoặc huấn luyện OCR trong giai đoạn sau không?
- **Classification:** `VERIFIED FACT` (Rust) & `INFERENCE` (huấn luyện OCR)
- **Answer:**
  - **Rust: KHÔNG CẦN (`NO_RUST_NEEDED`).** Toàn bộ chuỗi Local Parser + Planner `/26` + Source Gate + Exact Kernel `/24` thực thi trên CPU trong vài chục mili-giây với `Fraction`/`Radical` thuần Python; không tồn tại nút thắt CPU nào biện minh cho chi phí bảo trì biên FFI Python–Rust ([`low_end_performance_impact.json`](low_end_performance_impact.json)).
  - **Huấn luyện / fine-tune OCR toán viết tay cục bộ: Chưa cần trong ngắn hạn nếu có Gemini Vision fallback có kiểm chứng; chỉ đáng đầu tư nghiên cứu riêng nếu muốn giải ảnh viết tay hoàn toàn offline `0` Vision calls**, khi đó hướng khả thi là fine-tune bộ giải mã ký tự nhẹ (`< 80 MB` ONNX) bổ sung bảng ký hiệu toán học (`√, ⊥, ∥, °, ′, ∠`) trên tập dòng toán viết tay có nhãn chuẩn.

### 23. Candidate đã sẵn sàng để owner review ở mức nào?
- **Classification:** `VERIFIED FACT`
- **Answer:** Candidate tại product commit **`c61a3589782bde35b69e8376d8ebf136314e47f3`** (`measured_system = 69bb83ba51b834f68c106bc4d3948dc02ca35af05eca0d8f50c0e0e4cf047cb4`, `108` files, `CACHE_VERSION = 132`) **đã sẵn sàng đầy đủ để Owner review kỹ thuật và tích hợp nhánh (`CANDIDATE_FROZEN_READY_FOR_OWNER_REVIEW`)** với tất cả các cổng offline xanh (`Gates A, B, C, D, E, F, H = PASS`, `0` wrong-served, full backend/frontend/browser regressions PASS, `EVALUATION_CANDIDATE.json` khớp tuyệt đối). Đồng thời, báo cáo giữ nguyên sự trung thực khoa học: **chưa tuyên bố `PRODUCTION_READY`** vì `PRODUCTION_DEPLOYMENT_VERIFIED = NO`, `LIVE_VISION_EVALUATION = NOT_MEASURED` (`ALLOW_LIVE_AI = 0`), và `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (`Gate G = NOT_MEASURED`).

---

## III. Complete Deliverable Inventory (Section XI)

All 16 machine-verifiable JSON receipts plus `schema-census-extension.json` and the reproducible evaluation tool are stored in `docs/evaluation/geometry/runs/unified-angle-geometry-verified-image-to-3d/` (exact SHA-256 checksums recorded in [`run.json`](run.json)):

1. [`baseline_integrity_receipt.json`](baseline_integrity_receipt.json)
2. [`angle_premise_capability_receipt.json`](angle_premise_capability_receipt.json)
3. [`dihedral_angle_correctness_receipt.json`](dihedral_angle_correctness_receipt.json)
4. [`base_geometry_family1_receipt.json`](base_geometry_family1_receipt.json)
5. [`base_geometry_family2_receipt.json`](base_geometry_family2_receipt.json)
6. [`planner_composition_verification.json`](planner_composition_verification.json)
7. [`exact_kernel_independent_oracle.json`](exact_kernel_independent_oracle.json)
8. [`scene3d_geometry_parity_receipt.json`](scene3d_geometry_parity_receipt.json)
9. [`external_image_pipeline_receipt.json`](external_image_pipeline_receipt.json)
10. [`ocr_fidelity_regression_receipt.json`](ocr_fidelity_regression_receipt.json)
11. [`adaptive_vision_fallback_receipt.json`](adaptive_vision_fallback_receipt.json)
12. [`independent_corpus_readiness.json`](independent_corpus_readiness.json)
13. [`generalization_evaluation_receipt.json`](generalization_evaluation_receipt.json)
14. [`low_end_performance_impact.json`](low_end_performance_impact.json)
15. [`full_regression_summary.json`](full_regression_summary.json)
16. [`run.json`](run.json)
- Schema census contract lock: [`schema-census-extension.json`](schema-census-extension.json)
- Reproducible offline runner: [`tools/evaluate_unified_geometry_image_to_3d.py`](tools/evaluate_unified_geometry_image_to_3d.py)
