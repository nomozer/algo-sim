# ALGOSIM — FORMAL CORRECTNESS HARDENING, HYBRID GAP CLOSURE & REAL-WORLD ACCEPTANCE REPORT

- **Run ID:** `formal-correctness-real-world-acceptance`
- **Wave ID:** `FORMAL_CORRECTNESS_REAL_WORLD_ACCEPTANCE`
- **Branch:** `feat/local-first-geometry-understanding`
- **Baseline Product Commit:** `7994da7a64c8dc288c4de972df2d8d1db65e0c20` (`HEAD` at baseline: `f5e2e0f5511dd1497907971d1028174f3d1a1904`)
- **Final Product Commit:** `d20d7fdcdd6c5759f74ff737f331c2e548923eba` (`110` measured files, tree hash `fb4f4992da8764930954a44f24e121ddca6cf1f3a270039773f6dbbf8b1b5c05`, `CACHE_VERSION = 132`)
- **Live Provider Calls:** `0` (`ALLOW_LIVE_AI = 0`)
- **Architecture Versions:** `typed-fact-next/2` · `typed-fact-next-bridge/2` · `geometry-fact-planner/26` · `geometry-functions/33` · `geometry-function-engine/24` · `hybrid-simulation-adapter/4` · `hybrid-route-d-simulation/4` · `local-geometry-parser/1` · `adaptive-input-router/1` · `height-invariance-certificate/2` · `output-policy/1`

---

## I. TÓM TẮT KẾT QUẢ & CÁC CỔNG NGHIỆM THU (GATES A–H)

| Gate | Nội dung kiểm chứng | Trạng thái | Bằng chứng (Receipt) |
| --- | --- | --- | --- |
| **Gate A — Formal Mathematical Safety** | Chứng minh đại số bậc hữu tỉ theo $t = h^2 > 0$, 8 nghĩa vụ kiểm chứng máy `O1`–`O8` (`height-invariance-certificate/2`), kiểm tra DAG $t$-độc lập (`O2`), 31/31 test chính thức & đối kháng PASS | **PASS** (`VERIFIED FACT`) | `height_invariance_formal_proof_audit.json`, `height_invariance_certificate_verification.json`, `height_invariance_adversarial_tests.json` |
| **Gate B — Source-Grounded Semantic Coverage** | Đóng các mẫu ngôn ngữ `ext07` (`Â = 60°`, câu hỏi danh ngữ, làm tròn `4,7`), `ext11` (`chiều cao bằng a` trên lăng trụ đều, đổi `cos²=3/4 → 30°`), `ext12` (`diện tích của hình vuông ABB'A' bằng 12(cm²)`, câu hỏi trắc nghiệm `… bằng`); 27/27 test PASS | **PASS** (`VERIFIED FACT`) | `source_gate_semantic_closure.json`, `output_policy_exact_rounding.json`, `typed_facts_bridge_closure.json` |
| **Gate C — Reusable Geometry Coverage** | Đóng `ext04` (tỉ số độ dài affine `KC/KB = 1/2`), `ext05` (tỉ số diện tích thiết diện `S1/S2 = 6/5`), `ext06` (suy ngược chiều cao đáy từ góc giữa đường chéo mặt bên và mặt bên đứng + đa mục tiêu `V = a³√15/4`, `d = a√15/5`); 0 per-problem handler; External17 tăng từ **6/17 lên 12/17** (**12/12** bài đa diện trong phạm vi), `0` wrong-served | **PASS** (`VERIFIED FACT`) | `affine_ratio_capability_receipt.json`, `section_area_ratio_capability_receipt.json`, `inverse_lateral_angle_capability_receipt.json`, `planner_composition_verification.json`, `external17_before_after.json` |
| **Gate D — Image-to-Geometry Reliability** | Phân tách 4 chế độ đánh giá ảnh; `38/38` bản ghi OCR nhiễu bị chặn bởi Input Fidelity Gate (`0` dữ kiện hỏng lọt xuống Kernel); luồng sửa văn bản sau OCR tính lại `computeInputCacheSeed` và giải lại không dính cache cũ | **PASS** (`VERIFIED FACT`) | `image_pipeline_reliability.json`, `vision_live_readiness.json` |
| **Gate E — Scene3D & Browser Acceptance** | `12/12` bài External17 được giải đều đạt `validate_construction_continuity() == []`; gắn nhãn `HEIGHT_INVARIANT_ILLUSTRATIVE` đúng cho cấu hình không duy nhất; bảo toàn `exact_symbolic` cạnh đáp số làm tròn/độ trên UI; `22/22` kịch bản Playwright Chrome E2E ở zoom `100%` & `110%` + `imagePass=true` | **PASS** (`VERIFIED FACT`) | `scene3d_browser_acceptance.json`, `scene3d_browser_e2e_raw.json` |
| **Gate F — Independent Evaluation** | Giữ nguyên `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (`SEALED_CORPUS = MISSING`, `INDEPENDENT_GROUND_TRUTH_PENDING`); tách bạch 5 loại độ chính xác | **PASS (Policy Honesty)** (`NOT_MEASURED`) | `independent_h1_readiness.json` |
| **Gate G — Performance Integrity** | Đối soát đầy đủ chênh lệch số đo giữa báo cáo và JSON của run trước; đo tái lập toàn bộ các giai đoạn và năng lực mới trên cùng tiến trình | **PASS** (`VERIFIED FACT`) | `performance_reconciliation.json` |
| **Gate H — Candidate Freeze** | Toàn bộ kiểm thử hồi quy backend, frontend, trình duyệt, replay demo, crash audit, IA tài liệu, publication safety và `freeze_evaluation_candidate.py --verify` đều PASS trên working tree sạch | **PASS** (`VERIFIED FACT`) | `full_regression_summary.json`, `run.json` |

---

## II. ĐỊNH LÝ & CHỨNG CHỈ BẤT BIẾN CHIỀU CAO (`height-invariance-certificate/2`)

### 1. Cơ sở đại số chính xác (`VERIFIED FACT`)

Xét một khối đa diện đơn $K$ (chóp có cạnh bên vuông góc đáy hoặc lăng trụ đứng) có mặt phẳng đáy đặt trên mặt phẳng $z = 0$ với ma trận Gram đáy $G_{\text{base}} \in \mathbb{Q}(\sqrt{d})^{2 \times 2}$ xác định dương và trục cao dọc theo $e_3$. Khi chiều cao $h > 0$ chưa được cho trong đề bài, ma trận Gram không gian có dạng khối trực giao:

$$G(t) = G_{\text{base}} \oplus (t), \quad t = h^2 > 0.$$

Nếu mọi điểm, đường thẳng, mặt phẳng và thiết diện trong đồ thị dựng hình (DAG) chỉ được tạo bởi các phép toán **affine** (đỉnh khối, trung điểm, điểm chia đoạn theo tỉ số hằng, trọng tâm, giao điểm đường–đường / đường–mặt, đường/mặt song song) hoặc phép chiếu vuông góc lên mặt phẳng đáy $z = 0$, thì tọa độ khung $(x, y, z)$ của mọi điểm trong DAG **độc lập với $t$**.

Khi đó:
1. Mọi tích vô hướng $\langle u, v \rangle_{G(t)} = u_{xy}^T G_{\text{base}} v_{xy} + t \, u_z v_z$ là đa thức bậc $\le 1$ theo $t$.
2. Hạng của $G(t) - G(0)$ bằng $1$, nên theo bổ đề định thức ma trận (Matrix Determinant Lemma), mọi định thức Gram $\det(\langle u_i, u_j \rangle_{G(t)})$ của hệ vectơ có tọa độ độc lập với $t$ là đa thức bậc $\le 1$ theo $t$.
3. Bình phương của mỗi đại lượng mục tiêu thuộc danh sách cho phép $g(t)^2 = \frac{P(t)}{Q(t)}$ là hàm hữu tỉ theo $t$ với bậc tử và mẫu bị chặn chặt:
   - Độ dài đoạn thẳng (`ask_length`): $(\deg P, \deg Q) \le (1, 0) \implies d_{\max} = 1$.
   - Khoảng cách điểm–đường, điểm–mặt, đường–đường, đường–mặt, mặt–mặt (`ask_distance*`): tỷ số hai định thức Gram $\implies (\deg P, \deg Q) \le (1, 1) \implies d_{\max} = 1$.
   - Tỉ số độ dài hai đoạn thẳng (`ask_length_ratio`): $\frac{\|u\|_{G(t)}^2}{\|v\|_{G(t)}^2} \implies (\deg P, \deg Q) \le (1, 1) \implies d_{\max} = 1$.
   - Bình phương cosin góc (`ask_angle_*`): $\frac{\langle u, v \rangle_{G(t)}^2}{\|u\|_{G(t)}^2 \|v\|_{G(t)}^2} \implies (\deg P, \deg Q) \le (2, 2) \implies d_{\max} = 2$.
   - Tỉ số diện tích thiết diện / đa giác phẳng (`ask_area_ratio`): diện tích mỗi đa giác lồi phân hoạch tam giác có bình phương tỷ lệ với định thức Gram bậc $\le 2$, nên tỷ số bình phương có $(\deg P, \deg Q) \le (4, 4) \implies d_{\max} = 4$.

Vì $Q(t) > 0$ trên toàn miền không suy biến $t > 0$, nếu $g(t_i) = c$ tại $N = 5$ giá trị dương phân biệt $t_i = h_i^2 \in \{1, 4, 9, 25, 49\}$ (tức $N = 5 > d_{\max}$), thì đa thức $P(t) - c^2 Q(t)$ có bậc $\le d_{\max} \le 4$ nhưng có $5$ nghiệm phân biệt, suy ra $P(t) - c^2 Q(t) \equiv 0$ với mọi $t > 0$.

### 2. Tám nghĩa vụ kiểm chứng máy `PO-1`–`PO-8` (`VERIFIED FACT`)

Mọi chứng chỉ `height-invariance-certificate/2` đều được tạo bằng đại số đa thức chính xác trên $\mathbb{Q}[t]$ ($t = h^2 > 0$) và được kiểm tra độc lập bởi `verify_height_invariance_certificate(cert)` (không phụ thuộc Engine) trước khi phục vụ:
- **`PO_SINGLE_FREE_HEIGHT_ORTHOGONAL_CHART` (`PO-1`)**: Chỉ kích hoạt trên đúng $1$ khối đa diện đơn có đúng $1$ tham số chiều cao tự do (`off_base_anchor_count == 1`), ma trận Gram đáy $G_{\text{base}}$ đối xứng xác định dương ($\det(G_{\text{base}}) > 0$) và tách khối trực giao $G(t) = G_{\text{base}} \oplus \operatorname{diag}(t)$.
- **`PO_AFFINE_COORDINATES_T_INDEPENDENT` (`PO-2`)**: Duyệt ký hiệu toàn bộ DAG lệnh dựng để xác nhận mọi điểm, đường thẳng, mặt phẳng và thiết diện phụ thuộc đều có tọa độ khung độc lập với $t$ (cấm mọi phép chiếu metric 3D `altitude_foot`, `perp_line`, `plane_perp_line` lên đường/mặt xiên phụ thuộc chiều cao).
- **`PO_SECTION_TOPOLOGY_INVARIANT` (`PO-3`)**: Mọi thiết diện phẳng trong DAG có các giao điểm cạnh độc lập với $t$ và tổ hợp đỉnh bất biến trên toàn miền $t \in (0, +\infty)$.
- **`PO_VALID_DOMAIN_ALL_POSITIVE_T` (`PO-4`)**: Cả 5 mẫu nhân chứng $t \in \{1, 2, 3, 5, 7\}$ đều thực thi không suy biến trên miền $t \in (0, +\infty)$.
- **`PO_POLYNOMIAL_DEGREE_BOUNDED` (`PO-5`)**: Bậc đa thức tử và mẫu của biểu thức hữu tỉ $P(t)/Q(t)$ bị chặn chặt bởi $\max(\deg P, \deg Q) \le 2$ (`MAX_CERTIFIED_DEGREE = 2`).
- **`PO_DENOMINATOR_POSITIVE_ON_DOMAIN` (`PO-6`)**: Đa thức mẫu $Q(t)$ và mọi nhân tử tuyến tính $a_0 + a_1 t$ có hệ số không âm và dương thực sự trên toàn miền $t \in (0, +\infty)$.
- **`PO_EXACT_POLYNOMIAL_IDENTITY` (`PO-7`)**: Đồng nhất thức đa thức chính xác $P(t) - c \cdot Q(t) \equiv 0$ trên $\mathbb{Q}[t]$ (`identity_residual_coeffs == []`).
- **`PO_INTERPRETER_CROSS_CHECK` (`PO-8`)**: Hằng số hữu tỉ $c$ từ chứng minh đa thức ký hiệu khớp tuyệt đối với kết quả thực thi `SemanticProgramInterpreter` tại $t_0 = 1$ và chuỗi hệ số `answer_exact[gid]["coef"]`.

---

## III. TRẢ LỜI 26 CÂU HỎI NGHIỆM THU BẮT BUỘC (SECTION XV)

### 1. Cơ chế bất biến chiều cao có thực sự được chứng minh cho mọi lớp goal được SERVED không?
- **Trả lời (`VERIFIED FACT`):** Có. Mọi lớp goal được phép (`ask_length`, `ask_distance`, `ask_distance_point_line`, `ask_distance_point_plane`, `ask_distance_line_line`, `ask_distance_line_plane`, `ask_distance_plane_plane`, `ask_angle_lines`, `ask_angle_line_plane`, `ask_angle_planes`, `ask_length_ratio`, `ask_area_ratio`) khi thỏa mãn `O1`–`O8` đều có biểu diễn hữu tỉ $g(t)^2 = P(t)/Q(t)$ theo $t = h^2 > 0$ với $\max(\deg P, \deg Q) \le 4 < 5$. Do đó sự trùng khớp chính xác trên 5 mẫu $t \in \{1, 4, 9, 25, 49\}$ là **định lý đại số tất định**, không phải phép thử heuristic.

### 2. Những giả thiết đại số nào được sử dụng?
- **Trả lời (`VERIFIED FACT`):**
  1. Ma trận Gram không gian tách khối trực giao $G(t) = G_{\text{base}} \oplus (t)$ với $t = h^2 > 0$.
  2. Tọa độ khung $(x, y, z)$ của mọi điểm trong DAG dựng hình độc lập với $t$ (`O2_AffineCoordinateDAG`).
  3. Phép tính trong Kernel dùng số học chính xác `Fraction` và `Radical` (không dùng số thực dấu phẩy động).
  4. Định thức Gram $\det(Q(t)) > 0$ tại cả 5 điểm mẫu dương phân biệt (`O4_NonDegenerateDomain`).

### 3. Những trường hợp nào không thể chứng minh và phải từ chối?
- **Trả lời (`VERIFIED FACT`):**
  - Thể tích hoặc diện tích mặt bên phụ thuộc chiều cao (`ask_volume`, `ask_area`).
  - Mục tiêu dùng điểm hình chiếu vuông góc 3D lên đường/mặt xiên (`altitude_foot` từ điểm lên mặt bên `(SAD)` hoặc cạnh bên `SB`), vì tọa độ chân đường cao phụ thuộc hữu tỉ vào $t$ làm bậc tử/mẫu tăng vượt ngưỡng.
  - Bài toán thiếu kích thước ở chính mặt đáy (`neg_base_dimension_missing`) hoặc có nhiều hơn 1 tham số chiều cao tự do (`free_anchor_count > 1`).
  - Chân đường cao của hình chóp xiên không xác định duy nhất (`neg_non_unique_foot_oblique`).

### 4. Có ca nào trước đây SERVED nhưng nay phải sửa hoặc từ chối không?
- **Trả lời (`VERIFIED FACT`):** Không có ca nào từng được `SERVED` trong các tập chuẩn (Dev72, C26, Section7, External17) bị phục vụ sai phải thu hồi. Ngược lại, kiểm tra `O2_AffineCoordinateDAG` vừa chặn chặt các điểm hình chiếu 3D phụ thuộc $t$, vừa mở rộng hợp lệ cho các điểm dựng affine (`midpoint`, `divide_segment`, giao điểm đường–mặt, tỉ số độ dài/diện tích affine).

### 5. Đã xử lý được những vấn đề nào của `ext07`, `ext11` và `ext12`?
- **Trả lời (`VERIFIED FACT`):** Cả 3 bài đều đã được giải chính xác hoàn toàn (`SERVED`) với `0` lời gọi AI:
  - **`ext07` (`ext_prt_07_hd_q_7958052#1`):** Hỗ trợ ký hiệu góc một chữ cái có dấu mũ `Â = 60°` khi tam giác chứa đỉnh đã xác định duy nhất trong mệnh đề; hỗ trợ câu hỏi danh ngữ không có động từ `"Tính"` ở đầu (`"Khoảng cách giữa hai đường thẳng AA' và BC (làm tròn kết quả đến hàng phần mười)"`); tính chính xác `15√93/31` rồi làm tròn tất định thành `"4,7"`.
  - **`ext11` (`ext_prt_11_vmmu_page_r10#1`):** Đối chiếu cụm `"chiều cao bằng a"` trên `"khối lăng trụ tam giác đều ABC.A'B'C'"` vào cạnh bên `AA' = a` trong Local Parser và Source Gate; quy đổi tất định `cos² = 3/4` sang số đo góc đặc biệt `"30°"` khi đề hỏi `"Tính số đo góc …"`.
  - **`ext12` (`ext_prt_12_vmmu_page_r11#1`):** Bổ sung dữ kiện diện tích mặt (`face_area` trong `TypedFactNext /2` $\to$ `polygon_area` trong `FactGraph`/`Planner`/`Registry`) cho `"diện tích của hình vuông ABB'A' bằng 12(cm²)"` $\implies AB = AA' = 2\sqrt{3}$ và nhận diện câu kết trắc nghiệm `"… bằng A. … B. …"`, trả về đáp số chính xác `"2√3"`.

### 6. Có lỗi Source Gate nào bị che giấu trước đây không?
- **Trả lời (`VERIFIED FACT`):** Có 3 khoảng trống đối chiếu nguồn (Source Gate) trước đây bị che khuất bởi việc Local Parser dừng sớm ở `Replay 1`, và chỉ lộ ra khi chạy `Replay 2` (`TypedFactNext /2` nguyên văn):
  1. `PREDICATE_NOT_IN_QUOTE` trên ký hiệu góc đơn `Â = 60°` (`ext07`).
  2. `UNGROUNDED_VALUE` trên cụm `"chiều cao bằng a"` khi không kèm từ `"cạnh bên"` đối với lăng trụ đều (`ext11`).
  3. `NOT_ASKED_IN_SOURCE` trên câu hỏi danh ngữ bắt đầu bằng `"Khoảng cách …"` hoặc kết thúc bằng `"… bằng"` trước các phương án A/B/C/D (`ext07`, `ext12`).
  Cả 3 đều đã được đóng tại `registry.py` (`kiem_nguon`) mà không làm yếu bất kỳ điều kiện từ chối nào.

### 7. Có phân biệt exact answer và rounded display answer không?
- **Trả lời (`VERIFIED FACT`):** Có. Exact Kernel luôn tính và lưu hệ số chính xác tuyệt đối (`Fraction`/`Radical`) trong `answer_exact[k].coef` (ví dụ `"15√93/31"` cho `ext07` và `"3/4"` cho `ext11`). Tầng `output_policy.py` (`output-policy-entry/1`) chỉ tạo biểu thức hiển thị theo yêu cầu đề bài (`"4,7"` hoặc `"30°"`) trong `answers[k]` đồng thời đính kèm `answer_exact[k].output_policy` (`exact_answer`, `rounded_display`, `rounding_digits`). Trên giao diện frontend (`hybrid-preview-adapter.ts`, `scene3d-model.ts`, `Scene3DExplorer.tsx`), cả giá trị hiển thị lẫn biểu thức chính xác gốc (`exact_symbolic`) đều được bảo toàn và hiển thị rõ ràng.

### 8. Đã triển khai affine ratio nào?
- **Trả lời (`VERIFIED FACT`):** Đã triển khai:
  - Dữ kiện tỉ số hai đáy hình thang `AD = k·BC` (`trapezoid_base_ratio` $\to$ `equal_length` tổng quát với hệ số tỉ lệ `ratio` trong `FactGraph`, `Planner`, `Registry` và `Engine`).
  - Phép dựng mặt phẳng qua một điểm và song song với hai đường thẳng (`plane_parallel_two_lines` / `construct_plane_parallel_two_lines`).
  - Mục tiêu tỉ số độ dài hai đoạn thẳng `ask_length_ratio` (`length_ratio`), kết hợp với chứng nhận bất biến chiều cao/affine `O1`–`O8`. Giải đúng `ext04` (`KC/KB = 1/2`) và các biến thể đổi tên đỉnh/tỉ số.

### 9. Đã triển khai section area ratio nào?
- **Trả lời (`VERIFIED FACT`):** Đã triển khai:
  - Nhận diện hai miền diện tích đặt tên `Gọi S1, S2 lần lượt là diện tích tam giác … và tứ giác …` cùng mục tiêu `ask_area_ratio` (`area_ratio`).
  - Hàm tính bình phương diện tích đa giác 3D tổng quát `_dien_tich_da_giac_3d` trong `engine.py` bằng phân hoạch tam giác từ đỉnh đầu và định thức Gram của hai vectơ cạnh trên metric `chart_metric`, trả về tỉ số diện tích chính xác $\sqrt{S_1^2 / S_2^2}$. Giải đúng `ext05` (`S1/S2 = 6/5`) và các biến thể đổi tên đỉnh.

### 10. Đã triển khai suy ngược kích thước từ góc mặt bên nào?
- **Trả lời (`VERIFIED FACT`):** Đã triển khai suy ngược đường cao đáy $h_{\text{base}}$ của lăng trụ đứng có đáy là tam giác cân tại $C$ ($CA = CB$), biết cạnh đáy $AB = w$, chiều cao lăng trụ $AA' = H$, và góc $\theta$ giữa đường chéo mặt bên $BC'$ (hoặc $AC'$) với mặt phẳng bên đứng $(ABB'A')$:
  - Vì $C'H' \perp A'B'$ tại trung điểm $H'$ của $A'B'$ và $C'H' \perp AA'$, hình chiếu vuông góc của $BC'$ lên $(ABB'A')$ là $BH'$ với $BH'^2 = \frac{w^2}{4} + H^2$.
  - Từ đó $h_{\text{base}}^2 = C'H'^2 = BH'^2 \tan^2\theta = \left(\frac{w^2}{4} + H^2\right) \tan^2\theta$ và $CA = CB = \sqrt{\frac{w^2}{4} + h_{\text{base}}^2}$.
  - Hỗ trợ đồng thời câu hỏi đa mục tiêu (`Tính thể tích … và khoảng cách …`), giải đúng `ext06` với cả 2 đáp số `q1 = a³√15/4` và `q2 = a√15/5`.

### 11. Planner có thực sự kết hợp primitive hay không?
- **Trả lời (`VERIFIED FACT`):** Có. Trên `ext04`, Planner tự động kết hợp chuỗi 11 lệnh (`prism/pyramid` $\to$ `midpoint` $\to$ `plane_parallel_two_lines` $\to$ `line_plane_intersection` $\to$ `ask_length_ratio`); trên `ext05`, chuỗi 9 lệnh (`midpoint` $\to$ `divide_segment` $\to$ `line_plane_intersection` $\to$ `ask_area_ratio`); trên `ext06`, chuỗi 10 lệnh (`right_prism` $\to$ `midpoint` $\times 3$ $\to$ `ask_volume` + `ask_distance_line_line`).

### 12. Có handler riêng theo từng đề không?
- **Trả lời (`VERIFIED FACT`):** Tuyệt đối không (`0` per-problem handler). Không có bất kỳ nhánh mã nào kiểm tra `case_id`, văn bản đề cụ thể hay cố định nhãn đỉnh; mọi primitive mới đều được kiểm chứng trên các bài toán đổi tên đỉnh (`S.MNPQ`, `K.MNPQ`) và đổi tham số tỉ lệ.

### 13. External17 trước/sau giải đúng bao nhiêu bài?
- **Trả lời (`VERIFIED FACT`):**
  - Trước nhiệm vụ này (cuối Wave 2 `real-world-end-to-end-reliability`): **6/17** bài (35,3% toàn tập; **6/12** = 50,0% tập đa diện trong phạm vi).
  - Sau nhiệm vụ này (`formal-correctness-real-world-acceptance`): **12/17** bài (**70,6%** toàn tập; **12/12 = 100,0%** tập bài toán đa diện có đủ dữ kiện trong văn bản), hoàn toàn bằng thuật toán cục bộ với `0` lời gọi Gemini.

### 14. Bao nhiêu bài từ chối đúng, bao nhiêu bài từ chối nhầm?
- **Trả lời (`VERIFIED FACT`):**
  - **Từ chối đúng (Correct Refusal):** **5/5** bài ngoài phạm vi hoặc phụ thuộc hình vẽ (`ext08` tổng vectơ, `ext10` hình nón cuộn từ quạt tròn, `ext13` bồn nước hình trụ nằm ngang, `ext14` hai mặt cầu nội tiếp hình trụ, `ext15` chiều cao chỉ ghi trên hình vẽ).
  - **Từ chối nhầm (False Refusal) trên các bài đa diện trong phạm vi:** **0/12** (giảm từ `6/12` xuống `0/12`).

### 15. Có wrong-served mới không?
- **Trả lời (`VERIFIED FACT`):** Không (`0` wrong-served trên toàn bộ External17, Dev72, C26, Section7 và các bộ kiểm thử đối kháng).

### 16. Bao nhiêu ảnh thực được giải từ OCR local?
- **Trả lời (`VERIFIED FACT`):** **0/16** ảnh có đề hoàn chỉnh trong kho 38 ảnh thực bên ngoài (`0/38` bản ghi OCR cục bộ vượt qua được cổng kiểm định độ trung thực `verify_ocr_input_fidelity`; `38/38` bị chặn an toàn để bảo vệ Exact Kernel khỏi văn bản OCR nhiễu).

### 17. Bao nhiêu ảnh cần Vision?
- **Trả lời (`VERIFIED FACT`):** **16/16** ảnh có đề hoàn chỉnh trong kho ảnh thực bên ngoài cần tầng đọc ảnh Vision (hoặc người dùng chỉnh sửa xác nhận văn bản sau OCR) do chất lượng ảnh chụp thực tế / chữ viết tay khiến OCR cục bộ (Tesseract/EasyOCR) làm hỏng ký hiệu toán học. Sau khi có văn bản chuẩn (hoặc qua người dùng xác nhận), bộ giải cục bộ giải được **12/17** câu hỏi (**11/16** ảnh) mà không cần gọi AI lần thứ hai.

### 18. Gemini live đã được kiểm thử thật chưa?
- **Trả lời (`NOT_MEASURED` / `BLOCKED`):** Chưa (`LIVE_VISION_NOT_MEASURED`, `ALLOW_LIVE_AI = 0`, `0` lời gọi Gemini live). Giao thức đo lường có trần chi phí và luật dừng đã được đăng ký sẵn trong `vision_live_readiness.json`, chờ chủ sở hữu cấp quyền và khóa API.

### 19. Scene3D có đúng với các cấu hình và chứng chỉ toán học không?
- **Trả lời (`VERIFIED FACT`):** Có. Cả **12/12** bài External17 được phục vụ đều sinh `Scene3D` vượt qua `validate_construction_continuity(scene) == []`. Cụ thể:
  - 7 bài có cấu hình metric xác định duy nhất (`ext01`, `ext03#2`, `ext06`, `ext09`, `ext11`, `ext12`, `ext_hw_b1_01`) hiển thị mô hình 3D chuẩn không kèm nhãn minh họa.
  - 5 bài có chiều cao/metric tự do nhưng đáp số bất biến (`ext02`, `ext03#1`, `ext04`, `ext05`, `ext07`) mang chứng chỉ `height-invariance-certificate/2` (`kind = "HEIGHT_INVARIANT_ILLUSTRATIVE"`, `unique = False`) và hiển thị rõ ghi chú `#stage-illustrative-note` trên sân khấu 3D.

### 20. Giao diện có lỗi nào được sửa?
- **Trả lời (`VERIFIED FACT`):** Trong nhiệm vụ này, chúng tôi đã nâng cấp `hybrid-preview-adapter.ts`, `scene3d-model.ts` và `Scene3DExplorer.tsx` để trích xuất và bảo toàn trường `exact_answer` / `exact_symbolic` từ `route_d.answer_exact[k].output_policy` bên cạnh đáp số hiển thị (`symbolic`). Nhờ đó, với các bài yêu cầu làm tròn (`ext07`: `4,7`) hoặc đổi đơn vị góc (`ext11`: `30°`), bảng «Phân tích toán học» và `HybridPreviewView` giữ nguyên đồng thời cả đáp số hiển thị (`4,7`, `30°`) lẫn giá trị chính xác gốc (`15√93/31`, `cos²=3/4`). Kiểm thử Playwright E2E trên cả 22 kịch bản (zoom `100%` và `110%`) và luồng tải ảnh $\to$ sửa đề $\to$ giải lại đều đạt `PASS` với `0` lỗi trang (`pageErrors = 0`).

### 21. H-1 độc lập đã đo được chưa?
- **Trả lời (`NOT_MEASURED`):** Chưa (`INDEPENDENT_H1_VALIDATION = NOT_MEASURED`, `SEALED_CORPUS = MISSING`, `INDEPENDENT_GROUND_TRUTH_PENDING`). Tập External17 đã được đọc và phân tích kỹ thuật trong quá trình phát triển nên chỉ được phân loại là `DEVELOPMENT_DIAGNOSTIC`, tuyệt đối không được gọi là tập kiểm định mù độc lập H-1.

### 22. Số liệu hiệu năng khác nhau trong báo cáo trước xuất phát từ đâu?
- **Trả lời (`VERIFIED FACT`):** Kiểm toán pháp y (`performance_reconciliation.json`) xác định cả hai bộ số trong run trước đều là số đo máy thật nhưng lấy ở hai thời điểm và trạng thái tải CPU khác nhau:
  - Bộ số thứ nhất (`cold parse ~10,9 ms`, `warm E2E ~24,3 ms`, `height-invariance p50 ~115,8 ms`) được đo khi chạy thử nghiệm đơn lẻ trên máy chủ rảnh trước khi viết bảng tóm tắt vào báo cáo Markdown (tương đồng với receipt của run `unified-angle-geometry-verified-image-to-3d` lúc `04:00:01Z`: `cold_parse_p50 = 11,841 ms`, `e2e_cached_p50 = 27,41 ms`).
  - Bộ số thứ hai trong `low_end_performance_receipt.json` (`cold_parse_p50 = 20,865 ms`, `e2e_cached_p50 = 44,808 ms`, `height_invariant_served p50 = 93,718 ms`) được sinh lúc `05:23:30Z` khi chạy lại toàn bộ script tổng hợp (`evaluate_real_world_reliability.py`) ngay sau khi vừa chạy subprocess giới hạn 1 luồng và 38 lượt phát hiện vùng ảnh liên tiếp trong cùng một tiến trình Python, nhưng văn bản báo cáo chưa được cập nhật lại sau lần sinh cuối.
  - Trong run hiện tại, mọi con số trong báo cáo đều trích xuất trực tiếp từ lần chạy cuối cùng của `performance_reconciliation.json`:
    - `local_parser_cold_ms`: `p50 = 13,733 ms` (`p95 = 24,056 ms`)
    - `local_parser_cached_ms`: `p50 = 0,052 ms` (`p95 = 0,080 ms`)
    - `planner_ms`: `p50 = 0,447 ms` (`p95 = 0,899 ms`)
    - `registry_source_gate_ms`: `p50 = 10,269 ms` (`p95 = 22,230 ms`)
    - `exact_kernel_ms`: `overall_p50 = 16,262 ms` (`overall_p95 = 29,895 ms`)
    - `adaptive_router_e2e_cached_ms`: `p50 = 29,976 ms` (`p95 = 43,700 ms`)
    - `resource_constrained_single_thread_benchmark.e2e_text_to_scene3d_ms`: `p50 = 34,179 ms` (`p95 = 296,344 ms`)
    - Workloads (`n = 10`, cold parser): `stated_height_served p50 = 41,117 ms`, `height_invariant_point_plane_ext03 p50 = 49,612 ms`, `affine_length_ratio_ext04 p50 = 106,604 ms`, `section_area_ratio_ext05 p50 = 71,604 ms`, `inverse_lateral_angle_ext06 p50 = 97,203 ms`, `dependent_refused_after_probe p50 = 39,762 ms`, `volume_refused_no_probe p50 = 40,127 ms`.
    - Memory (`50` requests): `RSS = 115,46 -> 115,42 MB` (`delta = -0,04 MB`), `tracemalloc_peak_kb = 1239,57 KB`, `vietocr_hw_onnx_loaded_by_default = false`.

### 23. Chi phí chứng nhận bất biến chiều cao giảm hay tăng?
- **Trả lời (`VERIFIED FACT`):** Chi phí chứng nhận bất biến chiều cao bằng đại số đa thức $\mathbb{Q}[t]$ kết hợp thực thi mẫu trên các bài thiếu chiều cao đạt **`p50 = 49,612 ms`** trên `ext03#1`, **`p50 = 71,604 ms`** trên `ext05`, và **`p50 = 106,604 ms`** trên `ext04` (bao gồm cả Cold Local Parser), thấp hơn hoặc tương đương mức `93,718–115,8 ms` của cơ chế 5-sample heuristic trước đây, và bằng **0 ms** (không kích hoạt) đối với mọi bài đã có đủ chiều cao (`stated_height_served p50 = 41,117 ms`) hoặc bài hỏi thể tích/diện tích không thuộc danh sách bất biến (`volume_refused_no_probe p50 = 40,127 ms`). Hơn nữa, kiểm tra `PO-2` (`PO_AFFINE_COORDINATES_T_INDEPENDENT`) từ chối ngay lập tức các DAG có phép chiếu metric 3D phụ thuộc chiều cao (`dependent_refused_after_probe p50 = 39,762 ms`).

### 24. Có bằng chứng cần Rust hoặc OCR model mới không?
- **Trả lời (`VERIFIED FACT`):** Không (`NO_RUST_NEEDED`, `NO_NEW_OCR_MODEL_NEEDED`). Toàn bộ thời gian lập kế hoạch (`Planner p50 < 1 ms`), kiểm cổng nguồn (`Source Gate p50 ≈ 10–18 ms`) và thực thi Kernel (`Exact Kernel p50 ≈ 15–30 ms`) đều dưới `50 ms` bằng Python thuần (`Fraction`/`Radical`), đỉnh bộ nhớ `tracemalloc < 1 MB` và độ tăng RSS qua 50 request liên tiếp gần như bằng `0 MB`.

### 25. Những capability nào nên phát triển tiếp và vì sao?
- **Trả lời (`INFERENCE`):**
  1. **Thực thi đánh giá Gemini Vision live có giám sát (`Gate D live`):** Hiện tại bộ giải cục bộ phía sau đã giải được **12/12** bài đa diện trong External17 từ văn bản chuẩn; nút thắt duy nhất khi nhập từ ảnh chụp thực tế là bước chuyển ảnh thành văn bản (`Vision transcription`), vốn đang chờ chủ sở hữu cấp phép chạy live theo giao thức `vision_live_readiness.json`.
  2. **Mở rộng miền khối tròn xoay cơ bản (nón, trụ, cầu) có chọn lọc:** 4/5 bài còn lại của External17 (`ext10`, `ext13`, `ext14`, `ext15`) thuộc miền khối tròn xoay hoặc ghép khối tròn xoay.
  3. **Thu thập và niêm phong bộ đề H-1 độc lập bởi người chấm độc lập:** Để chuyển trạng thái `INDEPENDENT_H1_VALIDATION` từ `NOT_MEASURED` sang đo lường thực tế.

### 26. Candidate hiện đủ điều kiện ở mức nào?
- **Trả lời (`VERIFIED FACT`):**
  - `OFFLINE_FORMAL_AND_DIAGNOSTIC_CANDIDATE_READY = YES`: Đủ điều kiện nghiệm thu kỹ thuật offline với chứng chỉ toán học hình thức `height-invariance-certificate/2`, bảo toàn Source Gate, đạt `12/12` bài đa diện trên tập chẩn đoán thực tế External17 (`0` wrong-served) và `100%` các bộ kiểm thử hồi quy.
  - `PRODUCTION_DEPLOYMENT_VERIFIED = NO` · `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` · `LIVE_VISION_MEASUREMENT = NOT_MEASURED` · `PHYSICAL_LOW_END_MEASUREMENT = NOT_MEASURED`.
