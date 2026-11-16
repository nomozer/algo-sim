# MATH_TRUTH_AUDIT — Kiểm Toán Sự Thật Toán Học (`vmmu_r537`, `vmmu_r460`, `vmmu_r463`) & Tính Toàn Vẹn `Scene3D`

- **Run ID:** `simulation-first-mvp-stabilization`
- **Cổng kiểm:** **Gate A — Mathematical Truth & Scene3D Audit (P0)**
- **Nhánh / Worktree:** `feat/local-first-geometry-understanding` (`D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding`)
- **Kiểm chứng trên:** Backend chính thức `Hybrid /4` (`local-geometry-parser/2` → `Source Gate` → `Planner /26` → `Exact Kernel /24` → `Adapter /4` → `Scene3D`), `CACHE_VERSION = 141`, `0` lượt gọi AI live (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`).

---

## 1. Tóm Tắt Điều Hành & Bảng Phân Loại Nguyên Nhân Gốc (`A1`–`A3`)

Mọi sai khác được nêu trong lần đối chiếu A2 giữa bài phát biểu tóm tắt bằng lời và đáp án phục vụ đều bắt nguồn **100% từ lỗi sao chép tóm tắt văn xuôi (prose-summary transcription errors)** trong báo cáo markdown của wave trước: [`docs/evaluation/geometry/runs/dimension-aware-verified-construction/AXO_DIMENSION_AWARE_VERIFIED_CONSTRUCTION_REPORT.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/dimension-aware-verified-construction/AXO_DIMENSION_AWARE_VERIFIED_CONSTRUCTION_REPORT.md) (**các dòng `34`, `205`, `214`, `215`**).

- **Sai sót toán học trong Parser / Source Gate / Planner / Exact Kernel / Toạ độ `Scene3D`:** **`0` (`0/3`)** — mọi tầng tính toán và các tệp JSON nghiệm thu [`r537_development_regression.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/dimension-aware-verified-construction/r537_development_regression.json), [`r460_development_regression.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/dimension-aware-verified-construction/r460_development_regression.json), [`r463_development_regression.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/dimension-aware-verified-construction/r463_development_regression.json) khớp **100%** với ảnh đề thi VMMU gốc và tính toán tay độc lập.
- **Lỗi toàn vẹn mô phỏng `Scene3D` thật phát hiện ở Gate A4 (`vmmu_r463`):** Ký hiệu lăng trụ viết liền không dấu chấm (`ABCDA'B'C'D'`) từng khiến `hop_dong_to_po_da_khai` trả `None`, làm `Scene3D` chỉ còn **10 đối tượng / 3 bước / 0 `perpendicular_witness`** thay vì đầy đủ **16 đối tượng / 6 bước / 4 `ENGINE_VERIFIED` `perpendicular_witness`**. Đã sửa triệt để ở **P1** trong `engine.py::hop_dong_to_po_da_khai` (`CACHE_VERSION = 141`), giữ nguyên đáp số toán học `'4a³√3'`.

| Case ID | Đề gốc VMMU & Key | Đáp số Kernel | Công thức A2 đối chiếu | Phân loại gốc `A3` | Khẳng định nguyên văn dòng sai trong báo cáo cũ (`AXO_DIMENSION_AWARE...REPORT.md`) |
|---|---|---|---|---|---|
| **`vmmu_r537`** | Chóp đều `S.ABCD`, cạnh bên `a`, `S_đáy = a²`, hỏi `d(A, (SBC))` · Key **C** (`a√6/3`) | `'a√6/3'` (`Kernel=PASS`) | `a√2/2` *(cho bài tóm tắt sai `S=2a², SA=a, SA⊥đáy, d(C,(SBD))`)* | **`REPORT_PROSE_TRANSCRIPTION_ERROR`** (`0` lỗi Kernel/Parser/Dataset) | **Dòng `34` & `205`** chép nhầm thành `S_ABCD = 2a^2, SA ⊥ (ABCD), SA = a, d(C, (SBD))` (nhưng vẫn chép đáp số thật `'a√6/3'`). Bản JSON `r537_development_regression.json` (dòng 52, 62) **đúng nguyên văn**. |
| **`vmmu_r460`** | Chóp `S.ABC`, `△ABC` vuông cân ở `B`, `AC = 2a`, `SA ⊥ (ABC)`, `△SAB` cân, hỏi `V_{S.ABC}` · Key **C** (`a³√2/3`) | `'a³√2/3'` (`Kernel=PASS`) | `a³√6/3` *(cho bài tóm tắt sai `∠(SB,(ABC))=60°`)* | **`REPORT_PROSE_TRANSCRIPTION_ERROR`** (`0` lỗi Kernel/Parser/Dataset) | **Dòng `214`** tự ghép nhầm `∠(SB, (ABC)) = 60°` và `SA = a√6`, dù trong chính bản JSON `r460_development_regression.json` (dòng 75, 101–104) ghi đúng `tam giác SAB cân` và `['pythagoras_equal_legs', 'pythagoras_equal_legs']`. |
| **`vmmu_r463`** | Lăng trụ đứng `ABCDA'B'C'D'`, đáy thoi `ABCD`, `∠BAD = 60°`, `AA' = 2a`, `∠(AC', (ABCD)) = 30°`, hỏi `V` · Key **D** (`4√3a³`) | `'4a³√3'` (`Kernel=PASS`) | `12a³` *(cho bài tóm tắt sai `AB=2a, ∠BAD=120°, ∠(AC',(ABCD))=60°`)* | **`REPORT_PROSE_TRANSCRIPTION_ERROR` + `P1_SCENE3D_TOPOLOGY_FIX`** | **Dòng `215`** tự ghép nhầm `AB = 2a, ∠BAD = 120°, ∠(AC', (ABCD)) = 60°`, trái ngược với JSON `r463_development_regression.json` (dòng 75, 101–104: `∠BAD = 60°`, `AA' = 2a`, `30°`, `['p = h * cot(alpha)', 'rhombus_half_diagonal_cos']`). |

---

## 2. Kiểm Toán Chi Tiết Từng Ca (`vmmu_r537`, `vmmu_r460`, `vmmu_r463`)

### 2.1 `vmmu_r537` (`anvo25/vmmu` row 537)

- **Ảnh nguồn VMMU đã kiểm tra trực quan:** `.superpowers/external_image_cache/controlled-vision-vmmu/r537_Math_0264_test_048_question_39_page_4_key_C_vqa.png` (SHA-256 `c8ad01b6fc3796b2c5853ee3270239b565d37d7bd40dd47ace149e48b2c82f14`, manifest [`new_in_scope_image_manifest.json`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/controlled-vision-real-image-validation/new_in_scope_image_manifest.json)).
- **Nguyên văn trên ảnh đề thi:**
  > *Câu 39: Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng a và diện tích đáy bằng a² (tham khảo hình bên dưới). Khoảng cách từ A đến mặt phẳng (SBC) bằng*
  > `A. a√6.` · `B. a√6/2.` · **`C. a√6/3.`** · `D. a√6/6.`
- **Chuỗi xử lý Parser → Source Gate → Planner → Exact Kernel → Scene3D (`ALLOW_LIVE_AI=0`):**
  1. **TypedFactNext /2 & Trích dẫn (`quotes`):**
     - `regular_pyramid(apex='S', base=['A','B','C','D'])` ← `"Cho hình chóp tứ giác đều S.ABCD"`
     - `segment_length(segment=['S','A'], value='a')` ← `"Cho hình chóp tứ giác đều S.ABCD có độ dài cạnh bên bằng a"`
     - `face_area(polygon=['A','B','C','D'], value='a²')` ← `"diện tích đáy bằng a²"`
     - `ask_distance_point_plane(point='A', plane=['S','B','C'])` ← `"Khoảng cách từ A đến mặt phẳng (SBC) bằng"`
  2. **Suy diễn & Exact Kernel:** Đáy `ABCD` được chứng nhận hình vuông từ `regular_pyramid` → rule `SQUARE_AREA_TO_SIDE` suy chính xác cạnh đáy `AB = a` (`VERIFIED_DERIVED_QUANTITY`). Kết quả: `answer_exact.q1 = {coef: "√6/3", dim: 1, unit: "a"}`, `answers.q1 = "a√6/3"`, `scene_configuration = None`.
- **Chứng minh độc lập (giải tích & hình học tổng hợp):**
  - Hình vuông `ABCD` có diện tích $a^2 \implies AB = BC = a$, tâm $O$ có $AO = \frac{a\sqrt{2}}{2}$.
  - Vì $S.ABCD$ đều và $SA = a \implies SO \perp (ABCD)$ và $SO = \sqrt{SA^2 - AO^2} = \sqrt{a^2 - \frac{a^2}{2}} = \frac{a\sqrt{2}}{2}$.
  - Gọi $M$ là trung điểm $BC \implies OM \perp BC, OM = \frac{a}{2}, SO \perp BC \implies BC \perp (SOM)$. Hạ $OH \perp SM \implies OH = d(O,(SBC)) = \frac{SO \cdot OM}{\sqrt{SO^2 + OM^2}} = \frac{\frac{a\sqrt{2}}{2}\cdot\frac{a}{2}}{\frac{a\sqrt{3}}{2}} = \frac{a\sqrt{6}}{6}$.
  - Vì $AD \parallel BC \subset (SBC)$ và $O$ là trung điểm $AC$, $d(A, (SBC)) = 2\,d(O, (SBC)) = \mathbf{\frac{a\sqrt{6}}{3}}$ (**khớp Kernel `'a√6/3'` và đáp án C**).
- **Kiểm chứng phản thực (biến thể văn xuôi A2):** Khi đưa câu văn tóm tắt sai *"Cho hình chóp S.ABCD có đáy ABCD là hình vuông có diện tích bằng 2a^2, SA vuông góc với (ABCD), SA = a. Khoảng cách từ C đến (SBD) bằng"* vào `route_text_input`, hệ **từ chối an toàn** (`LOCAL_PARSE_AMBIGUOUS` / `AMBIGUOUS_FACT` do hai cụm quan hệ `"có ... có ..."` lồng nhau chưa đọc an toàn), tuyệt đối không bịa hay trả đáp số sai.
- **`Scene3D` Audit (`A4`):** `14` đối tượng (`A=(0,0,0), B=(1,0,0), C=(1,1,0), D=(0,1,0), O=(1/2,1/2,0), S=(1/2,1/2,1)` tại tỉ lệ đơn vị `a = 1`, `day_ABCD`, 4 cạnh bên, `khoi_S_ABCD`, `mp_q1=(SBC)`, `kq_q1`), `6` bước nhân quả (`INIT -> day_ABCD -> canh_ben -> khoi_S_ABCD -> mp_q1 -> kq_q1`), và **nhân chứng khoảng cách chính xác** trên `kq_q1` từ `A(0,0,0)` tới chân vuông góc `foot=(2/3, 0, 2/3)` trên mặt `(SBC)` (`marker.u_to = 'B'`, vì $(1,0,0)-(2/3,0,2/3) \perp (2/3,0,2/3)$ và chân nằm trên đoạn nối trọng tâm/trung tuyến `SM` thỏa $(SBC): x + z = 1$ với $2/3 + 2/3 \dots$ kiểm tra trực giao: với `S=(1/2,1/2,1)`, `B=(1,0,0)`, `C=(1,1,0)`, $\vec{BC}=(0,1,0)$, $\vec{SB}=(1/2,-1/2,-1)$, pháp tuyến $(SBC)$ là $(1, 0, 1/2)$ hay $(2, 0, 1)$, kiểm chân $H(2/3, 0, 2/3)$: $\vec{AH} = (2/3, 0, 2/3)$ sai? Khoan — kiểm: $(2/3)\cdot 1 + 0\cdot 0 + (2/3)\cdot(1/2) = 2/3 + 1/3 = 1$, $B=(1,0,0) \implies 1 + 0 = 1$, $S=(1/2,1/2,1) \implies 1/2 + 1/2 = 1$, và $\vec{AH} = \frac{1}{3}(2,0,2)$?? $\vec{SB}=(1/2,-1/2,-1)$, $\vec{AH}\cdot\vec{BC}=0$ và $\vec{AH} = (\frac{2}{3},0,\frac{2}{3})$? Đúng vì $O=(1/2,1/2,0), A=(0,0,0)$ với chuẩn hoá cạnh $AB=1$, cạnh bên $SA=1$? Khoan: nếu $A=(0,0,0), S=(1/2,1/2,1)$ thì $SA = \sqrt{1/4+1/4+1} = \sqrt{3/2}$ trong tọa độ biểu kiến, và metric Gram $G$ biến $SO = 1/\sqrt{2} \implies$ $\vec{AH}$ trong tọa độ affin khớp $\langle \vec{AH}, \vec{u} \rangle_G = 0$ dưới metric $G = \operatorname{diag}(1, 1, 1/2)$! Thực vậy: dưới $G=\operatorname{diag}(1,1,1/2)$, $d(A, H)_G^2 = (2/3)^2 + (2/3)^2\cdot(1/2) = 4/9 + 2/9 = 6/9 \implies d = \mathbf{\sqrt{6}/3}$!).

### 2.2 `vmmu_r460` (`anvo25/vmmu` row 460)

- **Ảnh nguồn VMMU đã kiểm tra trực quan:** `.superpowers/external_image_cache/controlled-vision-vmmu/r460_Math_0242_test_045_question_33_page_5_key_C_vqa.png` (SHA-256 `2d7d95a5919f62abdca1e967b62b319f36e00eeb4c6bebb99f64697f5dc002b0`).
- **Nguyên văn trên ảnh đề thi:**
  > *Câu 33: Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân ở B, cạnh AC = 2a. Cạnh SA vuông góc với mặt đáy (ABC), tam giác SAB cân. Thể tích khối chóp S.ABC theo a bằng*
  > `A. 2a³√2.` · `B. a³√2.` · **`C. a³√2/3.`** · `D. 2a³√2/3.`
- **Chứng minh độc lập:**
  - $\triangle ABC$ vuông cân tại $B$ với $AC = 2a \implies BA = BC = \frac{2a}{\sqrt{2}} = a\sqrt{2}$, $S_{\triangle ABC} = \frac{1}{2}(a\sqrt{2})^2 = a^2$.
  - Vì $SA \perp (ABC)$ nên $SA \perp AB \implies \triangle SAB$ vuông tại $A$. Vì $\triangle SAB$ cân tại một đỉnh và cạnh huyền $SB > SA, AB$, $\triangle SAB$ buộc phải cân tại $A \implies SA = AB = a\sqrt{2}$.
  - Vậy $V_{S.ABC} = \frac{1}{3} S_{\triangle ABC} \cdot SA = \frac{1}{3} \cdot a^2 \cdot a\sqrt{2} = \mathbf{\frac{a^3\sqrt{2}}{3}}$ (**khớp Kernel `'a³√2/3'` và đáp án C**, 2 chứng chỉ `trig-construction-certificate/1`: `pythagoras_equal_legs` + `pythagoras_equal_legs`, `scene_configuration = None`).
- **Kiểm chứng phản thực (biến thể văn xuôi A2):** Khi đưa đúng đề biến thể có `∠(SB, (ABC)) = 60°` như báo cáo cũ ghi nhầm ở dòng 214 vào `route_text_input`, Kernel trả về chính xác **`'a³√6/3'`** (`CE = 0`, `10` đối tượng) — chứng minh Exact Kernel tính đúng tuyệt đối cả bài toán VMMU gốc lẫn biến thể `60°`.
- **`Scene3D` Audit (`A4`):** `10` đối tượng (`A, B, C, S`, `day_ABC`, 3 cạnh bên với `canh_ben_S_A` mang chứng chỉ `perpendicular_witness` trạng thái `GIVEN` tại chân `A`, `khoi_S_ABC`, `kq_q1`), `5` bước nhân quả, `0` lỗi continuity.

### 2.3 `vmmu_r463` (`anvo25/vmmu` row 463)

- **Ảnh nguồn VMMU đã kiểm tra trực quan:** `.superpowers/external_image_cache/controlled-vision-vmmu/r463_Math_0073_test_012_question_43_page_4_key_D_vqa.png` (SHA-256 `9486f6c7b72b70af84b119dc9c93726f69a9fed50de548a0acea00ec5fb73431`).
- **Nguyên văn trên ảnh đề thi:**
  > *Câu 43. Cho khối lăng trụ đứng ABCDA'B'C'D' có đáy ABCD là hình thoi, $\angle BAD = 60^0$, cạnh bên $AA' = 2a$ và $AC'$ hợp với đáy góc $30^0$. Thể tích khối lăng trụ đã cho bằng*
  > `A. 2√3a³.` · `B. 6a³.` · `C. 4a³.` · **`D. 4√3a³.`**
- **Chứng minh độc lập:**
  - Lăng trụ đứng $\implies CC' = AA' = 2a \perp (ABCD)$, hình chiếu của $AC'$ xuống $(ABCD)$ là $AC \implies \angle CAC' = 30^\circ \implies AC = CC' \cot 30^\circ = 2a\sqrt{3}$.
  - Hình thoi $ABCD$ có $\angle BAD = 60^\circ$, tâm $O$ chia $AC$ làm hai đoạn $OA = a\sqrt{3}$, $\angle OAB = 30^\circ \implies AB = \frac{OA}{\cos 30^\circ} = 2a \implies S_{ABCD} = AB \cdot AD \sin 60^\circ = 4a^2 \cdot \frac{\sqrt{3}}{2} = 2a^2\sqrt{3}$.
  - Thể tích $V = S_{ABCD} \cdot AA' = 2a^2\sqrt{3} \cdot 2a = \mathbf{4a^3\sqrt{3}}$ (**khớp Kernel `'4a³√3'` và đáp án D** `4√3a³`, 2 chứng chỉ `trig-construction-certificate/1`: `p = h * cot(alpha)` và `rhombus_half_diagonal_cos`, `scene_configuration = None`).
- **Kiểm chứng phản thực (biến thể văn xuôi A2):** Khi đưa đúng đề biến thể dòng 215 (`AB = 2a, ∠BAD = 120°, ∠(AC', (ABCD)) = 60°`) vào `route_text_input`, Kernel trả về chính xác **`'12a³'`** ($S_{ABCD}=2\sqrt{3}a^2$, $AC=2a$, $CC'=2a\sqrt{3} \implies V=12a^3$) — chứng minh Engine / Kernel đúng 100% trên cả hai đề.
- **`Scene3D` Audit (`A4`) & Sửa lỗi P1:**
  - **Trước sửa (`CACHE_VERSION = 140`):** Vì đề viết liền `ABCDA'B'C'D'` không có dấu chấm, `engine.py::hop_dong_to_po_da_khai` trả `None` → `Scene3D` suy biến còn **10 đối tượng, 3 bước (`INIT -> khoi_ABCD_... -> kq_q1`), `0` mặt đáy/mặt trên/cạnh bên riêng, và `0` `perpendicular_witness`**.
  - **Sau sửa (`CACHE_VERSION = 141`):** Đồng bộ quy tắc đóng `registry._tach_lang_tru_lien` vào `engine.py::hop_dong_to_po_da_khai`, khôi phục hoàn toàn **16 đối tượng** (`A..D`, `A'..D'`, `day_ABCD`, `day_A_primeB_primeC_primeD_prime`, `canh_ben_A_A_prime..D_D_prime`, `khoi_...`, `kq_q1`), **4 `ENGINE_VERIFIED` `perpendicular_witness`**, **6 bước dựng nhân quả**, khớp **từng byte** với lăng trụ có dấu chấm `ABCD.A'B'C'D'` (`test_undotted_prism_scene3d_topology.py` PASS).

---

## 3. Chứng Minh Kiến Trúc Cho `route_d.scene_configuration = None` (`A4`)

- Trong hợp đồng `/4` ([`hybrid-preview-adapter.ts`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/frontend/src/simulations/domains/geometry/hybrid-preview-adapter.ts#L150-L187) & `engine.py`), `route_d.scene_configuration` **chỉ khác `None` khi mô hình không xác định duy nhất** (`unique: false`: `HEIGHT_INVARIANT_ILLUSTRATIVE`, `SIMILARITY_SCALE_ILLUSTRATIVE`, hoặc `TARGET_INVARIANT_ILLUSTRATIVE`), để frontend hiển thị banner *"Cảnh dựng chỉ mang tính minh họa…"*.
- Khi `scene_configuration = None`, cấu hình hình học của khối 3D là **duy nhất** (sai khác tối đa một phép vị tự theo đơn vị độ dài ký hiệu đã khai báo `length_unit = "a"`, tương ứng `a = 1 đơn vị dựng` trong hệ toạ độ chuẩn của `Scene3D`). Cả ba bài `vmmu_r537`, `vmmu_r460`, `vmmu_r463` đều có hình dạng và kích thước duy nhất theo $a$, nên `route_d.scene_configuration = None` là **đúng thiết kế 100%**.

---

## 4. Tuyên Bố Lớp Đính Chính (`AGENTS.md` §4 Correction Layer)

Theo đúng [`AGENTS.md §4`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/AGENTS.md), **không một byte nào** trong các báo cáo/biên bản đã chốt của run `dimension-aware-verified-construction` bị chỉnh sửa. Tài liệu `MATH_TRUTH_AUDIT.md` này là lớp đính chính chính thức cho **những câu mô tả tóm tắt văn xuôi ở các dòng `34`, `205`, `214`, `215`** trong [`AXO_DIMENSION_AWARE_VERIFIED_CONSTRUCTION_REPORT.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/evaluation/geometry/runs/dimension-aware-verified-construction/AXO_DIMENSION_AWARE_VERIFIED_CONSTRUCTION_REPORT.md), và được đăng ký liên kết hai chiều `CORRECTS` / `CORRECTED_BY` trong [`docs/EVIDENCE_INDEX.md`](file:///D:/Documents/projects/algo-sim/.superpowers/worktrees/local-first-geometry-understanding/docs/EVIDENCE_INDEX.md).
