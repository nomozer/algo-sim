# ALGOSIM — BÁO CÁO TỔNG HỢP HOÀN THIỆN SẢN PHẨM BACKEND HYBRID (`ALGOSIM_FINAL_BACKEND_PRODUCT_REPORT`)

**Phán quyết nhiệm vụ:** `FUNCTIONAL_BACKEND_COMPLETE`  
**Phạm vi hiệu lực:** Backend Hybrid chức năng đã hoàn thiện end-to-end trong phạm vi hỗ trợ đã kiểm chứng và sẵn sàng đưa vào thử nghiệm sản phẩm thực tế theo cơ chế opt-in (`HYBRID_ROUTE_MODE = staging-replay | live`). Báo cáo này **không** tuyên bố `INDEPENDENTLY_VALIDATED` và **không** tuyên bố `PRODUCTION_CUTOVER_APPROVED`.

---

## 1. Định Danh Commit & Product Candidate Đóng Băng

| Thành phần | Giá trị xác minh |
| :--- | :--- |
| Nhánh làm việc | `research/hybrid-master-backend-replacement` |
| Product commit (`product_commit_sha`) | `d6a53dc6d11273f297b7029f0db07476cd81dcfb` (`d6a53dc6`) |
| Frozen product candidate commit | `017bfb9fd61443f732b3e5f188aca24aa69b3171` (`017bfb9f`) |
| Commit manifest đóng băng (`EVALUATION_CANDIDATE.json`) | `db77322811c43faf798ddbf8c298117a32574be2` (`db773228`) |
| Commit tài liệu cuối (chứa biên nhận T3 + báo cáo này + chỉ mục) | `SELF` (không chạm `measured_system`; `freeze_evaluation_candidate.py --verify` giữ nguyên `MATCH`) |
| Hệ đo (`measured_system`) | `119` file · `tree_hash = b33629d10b9673e1e9eed92ecc09074faccbd6a8ad245658ac4ff45c2f284cbc` |
| Bản lưu candidate trước (`180db769` / `d331e75b`) | `docs/evaluation/geometry/runs/hybrid-master-final-backend-product/frozen-evaluation-candidate.json` |
| Lớp đối chiếu phân kỳ candidate | `docs/evaluation/geometry/runs/hybrid-master-final-backend-product/candidate_divergence.json` |
| Phiên bản thành phần | `geometry-functions/33` · `geometry-fact-planner/26` · `geometry-function-engine/24` · `typed-fact-next/2` · `adapter /4` |
| Cấu hình mặc định sản phẩm (giữ nguyên) | `CHE_DO_MAC_DINH = "LLM_ONLY"` · `HYBRID_ROUTE_MODE = "off"` · `CACHE_VERSION = "131"` |
| Thay đổi trên `frontend/**` | `0` file (`git diff ecd03a7f..HEAD -- frontend` rỗng) |
| Số request Gemini live mới trong nhiệm vụ này | `0` (`ALLOW_LIVE_AI = 0`; toàn bộ biên nhận live C21/C26 giữ nguyên từng byte) |

---

## 2. Các Sửa Đổi Mã Sản Phẩm Thực Tế (`5` file trong `backend/app/`)

1. **`backend/app/simulation/geometry_functions/construction_continuity.py` (module mới, 0-LLM, tất định):**
   - `enrich_construction_continuity`: làm giàu tương thích ngược từng bước trong `scene3d.formation.steps` với `step_id`, `coordinate_frame_id` (`"canonical_chart_v1"`), `depends_on`, `preconditions`, `created_ids`, `reused_ids`, `highlighted_ids`, `retired_ids`, `verification_refs` và tóm tắt sư phạm 5 phần `step_summary` (`what`, `inputs`, `validity`, `result`, `next_use`).
   - `validate_construction_continuity`: cổng kiểm tra tính liên tục hình học tích lũy theo số học hữu tỉ chính xác (`Fraction` + `Metric`), chặn fail-closed cả 7 lớp đứt gãy dựng hình.
2. **`backend/app/ai/function_route.py`:**
   - Nối `MAT_RANG_BUOC` vào `prefer_declared_plane_names` và `_vai_mat_cat` để mặt phẳng ràng buộc có tên khai báo (ví dụ `(P)`) hiển thị đúng tên đề bài và không rò nhãn chân đường vuông góc dựng phụ (`H1`) vào tên thiết diện hay lời giải thích.
   - Bổ sung `_chuan_hoa_be_mat_khoi_cong` làm sạch bề mặt ngôn ngữ cho khối tròn xoay (`O.O'` → `O.O′`, `S.O`, `O_sphere_O` kể cả mặt cầu ngoại tiếp không đặt tên tâm) và đại lượng tổ hợp `compose_quantity` (thể tích phần còn lại / tỉ số thể tích).
   - Gắn `enrich_construction_continuity` và cổng fail-closed `validate_construction_continuity` (`SCENE_BUILD_FAILED` nếu phát hiện vi phạm liên tục hình học).
3. **`backend/app/ai/typed_fact_next_extraction.py`:**
   - Chuẩn hóa wire-shape `simulation_goals[*].vertex` / `point` sang `target_refs: [tok]` khi và chỉ khi đỉnh đó có mặt nguyên văn trong `quote` của chính mục tiêu mô phỏng; không sửa bất kỳ prompt hay JSON Schema nào gửi lên Gemini (`4/4` surface fingerprints giữ nguyên tuyệt đối).
4. **`backend/app/simulation/geometry_functions/typed_fact_next_bridge.py`:**
   - Trong `bridge_v2`, khi `unresolved` chứa một mục `"unsupported"` đồng thời có mục `"incomplete"`/`"ambiguous"` chỉ bao trùm cùng đoạn trích hoặc cùng `subject_ref`, ưu tiên trả `OUT_OF_SCOPE` (`capability_gap`) thay vì hỏi lại học sinh nhầm bằng `AMBIGUOUS_FACT`.
5. **`backend/app/simulation/geometry_functions/registry.py` (`geometry-functions/33`):**
   - Bổ sung đồng bộ ngữ pháp tiếng Việt tại Source Gate cho cụm `"điểm chính giữa"` (tương đương `"trung điểm"` ở cả điểm đặt tên và `described_points`) và quan hệ đường thẳng `"nối"` / `"(đi) qua"` hai điểm trong câu hỏi góc đường–mặt và góc giữa hai đường thẳng.

Ngoài mã sản phẩm, bộ kiểm thử và biên nhận được cập nhật đồng bộ tại `backend/tests/geometry/test_final_backend_product_completion.py` (`22` bài test mới), `backend/scripts/export_hybrid_preview_fixtures.py`, `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/fixtures-adapter-2-construction-continuity/` (`41` preview fixtures), `r1-live-pilot-gold-replay-final.jsonl`, và `docs/CODE_INDEX.md`.

---

## 3. Những Lỗi Sản Phẩm Cụ Thể Đã Giải Quyết

| Mã / Trường hợp | Hiện tượng trước khi sửa (`180db769`) | Nguyên nhân gốc | Kết quả sau khi sửa (`017bfb9f`) |
| :--- | :--- | :--- | :--- |
| **`S2-B-A03`** (`S-2` live replay) | Từ chối `INVALID_SIMULATION_GOAL` dù phần toán học và dữ kiện đúng | Gemini xuất `simulation_goals[1].vertex = "H"` thay vì `target_refs: ["H"]` | Chuẩn hóa an toàn có kiểm chứng `quote` → `SERVED` đúng đáp số `√3`; biến thể đối kháng lệch `quote` hoặc đỉnh lạ `Z` vẫn bị chặn (`INVALID_SIMULATION_GOAL`, `UNKNOWN_VERTEX_REF`) |
| **`R1-G01`** (`R-1` gold & live replay) | Từ chối giả tại Source Gate (`PREDICATE_NOT_IN_QUOTE`) | Câu hỏi góc viết `"đường thẳng đi qua A và trọng tâm..."` chưa khớp mẫu câu hỏi góc | `SERVED` chính xác (`arctan(√11/11)`), nâng `R-1` lên `13/13` đề dương; biến thể đổi đỉnh `A → B` bị chặn `SOURCE_OBJECT_MISMATCH` |
| **`R1-G02`** (`R-1` gold & live replay) | Từ chối giả tại Source Gate (`PREDICATE_NOT_IN_QUOTE`) | Cụm `"điểm chính giữa cạnh SB"` chưa đồng bộ với `"trung điểm"` ở Source Gate | `SERVED` chính xác (`√2/2`) cho cả điểm ẩn danh `@dp1` và điểm đặt tên `M`; biến thể lệch cạnh `SC` bị chặn `SOURCE_OBJECT_MISMATCH` |
| **`R1-F03`** (`R-1` capability-gap) | Trả `AMBIGUOUS_FACT` (hỏi lại học sinh) trên bài vượt phạm vi multi-point `@`-refs | Mục `incomplete` của câu hỏi đứng trước/che khuất mục `unsupported` con trong `unresolved` | Trả đúng `OUT_OF_SCOPE` (`failure_category = "capability_gap"`), giữ nguyên `AMBIGUOUS_FACT` cho cả 4 ca mơ hồ thật (`K-E01`, `K-E02`, `S2-C-A01`, `R1-E01`) |
| **`K-A01`** (thiết diện mặt phẳng ràng buộc `(P)`) | Nhãn chân vuông góc phụ `H1` rò vào tên thiết diện / câu giải thích giao tuyến | `MAT_RANG_BUOC` chưa đi qua nhánh đặt tên mặt phẳng khai báo trong `function_route.py` | Hiển thị sạch `Thiết diện bởi (P)` và câu giải thích theo `(P)`, không còn `H1` trong chuỗi hiển thị cho học sinh |
| **Khối tròn xoay & `compose_quantity`** | Rò ký hiệu nội bộ `O.O'`, `S.O`, `O_sphere_O` hoặc câu chung `"«Thể tích khối cong» trừ «Thể tích khối cong»"` | Chuỗi mô tả mặc định của Adapter chưa chuẩn hóa dấu phẩy trên `′` và nhãn mặt cầu/nón cụt | Chuẩn hóa sạch (`O.O′`, `"mặt cầu ngoại tiếp"`, diễn đạt hiệu/tỉ số cụ thể), `0` dấu gạch dưới `_` hay tọa độ thô trên bề mặt học sinh |
| **Liên tục bước dựng & giải thích bước** | Bước dựng chỉ có `visible_ids` / `focus_ids` mà thiếu trạng thái tích lũy tường minh và cấu trúc 5 câu hỏi sư phạm | Chưa có lớp làm giàu trạng thái bước và cổng kiểm tra bất biến liên tục | Mọi bước có `step_id`, `coordinate_frame_id`, `depends_on`, `preconditions`, `created_ids`, `reused_ids`, `highlighted_ids`, `retired_ids`, `verification_refs`, `step_summary` 5 phần và cổng fail-closed `SCENE_BUILD_FAILED` |

---

## 4. Kết Quả Kiểm Thử Toán Học, Scene3D và Tính Liên Tục Dựng Hình

### 4.1. Kiểm thử toán học (Mathematical Validity)

- **Replay trên 70 payload Gemini live đã ghi nhận ở C26** *(lưu ý trung thực: đây là replay tất định offline trên dữ liệu wire thật của C26 thuộc tập phát triển K-1/S-2/R-1, không phải lượt gọi Gemini live mới và không phải tập độc lập H-1)*:
  - **Đề hợp lệ cần giải (`41` đề):** **`40/41` (`97.56%`) `SERVED` khớp tuyệt đối đáp số symbolic oracle** (tăng từ `37/41 = 90.24%` ở `180db769`):
    - `K-1`: **`10/10` (`100%`)** (trước đó `10/10`).
    - `S-2`: **`17/18` (`94.44%`)** (tăng từ `16/18`; ca duy nhất còn từ chối là `S2-F-S07` gõ không dấu `"hình chop"` theo đúng chính sách S-1 không đoán lỗi chính tả).
    - `R-1`: **`13/13` (`100%`)** (tăng từ `11/13`).
  - **Đề thiếu dữ kiện / mâu thuẫn / ngoài phạm vi (`29` đề):** **`29/29` (`100%`) từ chối đúng chiều an toàn** (`K-1` `6/6`, `S-2` `18/18`, `R-1` `5/5`), **`0` false clarification**.
  - **Sai số toán học được phục vụ (`wrong-served`):** **`0/70` (`0.0%`)**.
- **Các bộ kiểm chứng hồi quy & probe chuyên biệt:**
  - Gold replay `K-1`: **`16/16`**; `S-2`: **`35/36`** (`0` wrong-served); `R-1` (`r1-live-pilot-gold-replay-final.jsonl`): **`18/18`** (`13/13` dương + `5/5` âm, `0` wrong-served).
  - Wave 3 post-feedback regression (`144` ca): **`72/72` đề dương `SERVED_CORRECT`**, **`72/72` đề âm từ chối**, **`0/144` wrong-served**.
  - Locked V2 contract: **`96/96`**; bộ `203` adversarial probes: **`0` wrong-served**; C17 constrained witness: **`407/407`** served exact + **`1,124/1,124`** từ chối đúng; C18 definition composition: **`480/480`** served exact + **`24/24`** suy biến bị chặn; curved/sphere probes (`curved_probe`, `curved_section_probe`, `circumscribed_sphere_probe`, `sphere_section_probe`): **100% khớp oracle**.

### 4.2. Kiểm thử hợp đồng `Scene3D` (Scene3D Contract Validity)

- Xuất mới và kiểm chứng **`41/41` preview fixtures** tại `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/fixtures-adapter-2-construction-continuity/` (`test_hybrid_preview_fixtures.py` và `test_hybrid_preview_contract.py`: `64/64` đạt).
- Toàn bộ **`85/85` file kiểm thử frontend (`1,502/1,502` bài test Vitest)** — bao gồm `hybrid-preview-contract.test.tsx`, `hybrid-product-integration.test.tsx`, `scene3d-steps-panel.test.tsx`, `scene3d-step-justification.test.tsx`, `scene3d-geometry-timeline.test.tsx` — đều **PASS 100%** mà không sửa bất kỳ dòng nào trong `frontend/**`.
- Các trường mở rộng trong `scene3d.formation.steps` là bổ sung tương thích ngược 100% với bộ tiêu thụ TypeScript hiện hành.

### 4.3. Kiểm thử tính liên tục các bước dựng & lời giải sư phạm (Construction & Pedagogical Coherence)

- **Kiểm chứng 7 lớp lỗi đứt gãy hình học đối kháng (`test_final_backend_product_completion.py`):**
  1. `DEPENDENCY_BEFORE_CREATION` — bước dựng tham chiếu đối tượng chưa xuất hiện ở trạng thái tích lũy.
  2. `OBJECT_IDENTITY_MUTATION` — trùng ID đối tượng hoặc hai điểm khác nhau dùng chung ký hiệu `notation`.
  3. `GEOMETRIC_STEP_CONTRADICTION` — đổi `coordinate_frame_id` giữa các bước, metric không xác định dương (SPD), hoặc đầu mút đoạn thẳng / chân vuông góc lệch tọa độ điểm gốc.
  4. `MISSING_OBJECT_PROVENANCE` — đối tượng dẫn xuất xuất hiện sau bước 0 nhưng không có `producer` hoặc không có sự kiện dựng hình tương ứng.
  5. `UNEXPLAINED_OBJECT_DISAPPEARANCE` — khối chính, thiết diện, đỉnh gốc hoặc đối tượng đang hiển thị biến mất ở bước sau mà không được khai báo trong `retired_ids`.
  6. `MEASUREMENT_USES_UNDETERMINED_OBJECT` — bước đo hoặc `FINAL_RESULT` đọc đại lượng chưa có `value`/`exact` hoặc phụ thuộc đối tượng chưa xác định.
  7. `SECTION_OR_INTERSECTION_MISMATCH` — đa giác thiết diện không khép kín, có đỉnh lệch khỏi phương trình mặt phẳng cắt hoặc vượt bao lồi khối gốc; giao tuyến đường tròn lệch mặt phẳng; giao điểm đường–mặt lệch đường hoặc mặt.
  - Cả **7/7** đột biến đối kháng đều bị `validate_construction_continuity` bắt chính xác và bị `function_route.py` chặn fail-closed với mã `SCENE_BUILD_FAILED`.
- **Kiểm chứng bề mặt lời giải cho học sinh:**
  - `0` vi phạm liên tục dựng hình trên toàn bộ `40/40` ca C26 được phục vụ và `9/9` ca đại diện của 7 họ hình học.
  - Mỗi bước đều có `step_summary` trả lời đủ 5 câu hỏi (`what`, `inputs`, `validity`, `result`, `next_use`), độ dài `learner_text <= 240` ký tự, ký hiệu toán học nhất quán (`′`, `√`, `π`, phân số tối giản), không rò tọa độ thô `(x, y, z)` và không dùng LLM làm nguồn chứng minh định lý.

---

## 5. Phạm Vi Hình Học Hỗ Trợ Thực Tế Trên 7 Họ Đã Đăng Ký

| Họ hình học | `SUPPORTED` (đã kiểm chứng end-to-end) | `SUPPORTED_WITH_LIMITS` (hỗ trợ có điều kiện rõ ràng) | `UNSUPPORTED` (từ chối rõ mã lỗi) |
| :--- | :--- | :--- | :--- |
| **1. Hình chóp (`pyramid`)** | Chóp tam giác/tứ giác đều, chóp có cạnh bên $\perp$ đáy, mặt bên $\perp$ đáy, giao hai mặt $\perp$ đáy, hình chiếu đỉnh lên đáy (đỉnh/trung điểm/trọng tâm); dựng trung điểm, trọng tâm, chia đoạn theo tỉ số, hình chiếu, giao điểm đường–mặt, giao hai đường, trực tâm/tâm ngoại tiếp tam giác; thể tích, tỉ số/phần còn lại thể tích, diện tích, khoảng cách (điểm–điểm/đường/mặt, đường–đường chéo nhau, đường//mặt), góc (hai đường, đường–mặt, nhị diện); thiết diện qua 3 điểm, song song mặt/2 đường, vuông góc đường, mặt phẳng ràng buộc `MAT_RANG_BUOC`; mặt cầu ngoại tiếp/nội tiếp và tiếp xúc mặt phẳng | Đa giác đáy giới hạn ở tam giác và tứ giác có đủ dữ kiện định vị metric chính xác (vuông, chữ nhật, thoi có góc/đường chéo, thang vuông, đều); điểm mô tả ẩn danh giới hạn ở các mẫu `midpoint`, `centroid`, `divide_segment`, `projection`, `intersection`, `orthocenter`, `circumcenter` | Chóp đáy đa giác $\ge 5$ cạnh bất kỳ chưa định chuẩn metric; cực trị hình học, quỹ tích điểm di động, tâm nội tiếp đa giác bất kỳ (`D1`/`D2` → `BRIDGE_UNSUPPORTED_DESCRIBED_POINT`) |
| **2. Hình lăng trụ (`prism`)** | Lăng trụ đứng đáy tam giác/tứ giác chuẩn, lăng trụ đều, lăng trụ xiên định vị bằng hình chiếu đỉnh tầng trên xuống đáy và độ dài/góc cạnh bên; thể tích, diện tích, khoảng cách, góc, thiết diện Category A & Category B (`ENGINE_DERIVED_SECTION`), mặt cầu ngoại tiếp lăng trụ đứng đủ điều kiện | Lăng trụ xiên yêu cầu đề bài nêu rõ hình chiếu vuông góc của một đỉnh đáy trên xuống mặt đáy dưới và độ dài/góc định cỡ | Lăng trụ xiên thiếu chân đường cao hoặc cho bằng hệ ràng buộc góc chéo tự do nhiều bậc chưa đăng ký |
| **3. Hình hộp (`cuboid`)** | Hình hộp chữ nhật (`right_prism` + `rectangle`), hình hộp đứng/xiên đủ dữ kiện vectơ tịnh tiến; thể tích, diện tích, đường chéo, khoảng cách, góc, thiết diện phẳng, mặt cầu ngoại tiếp | Hình hộp tổng quát không vuông cần đủ dữ kiện góc mặt đáy và hình chiếu cạnh bên như lăng trụ | Bài toán tối ưu tham số trên hình hộp biến thiên |
| **4. Hình lập phương (`cube`)** | Hình lập phương với ký hiệu chuẩn (`ABCD.A'B'C'D'`) hoặc nhãn đỉnh tùy ý (`MNPQ.M'N'P'Q'`); đầy đủ phép dựng điểm, đường, mặt, thiết diện đa giác (3–6 cạnh), khoảng cách, góc, thể tích, mặt cầu ngoại tiếp/nội tiếp | Cùng giới hạn chung về loại câu hỏi đo lường và điểm ẩn danh của hệ đa diện | Cực trị, quỹ tích hoặc tọa độ hóa giải tích `Oxyz` |
| **5. Hình cầu (`sphere`)** | Mặt cầu độc lập từ bán kính/đường kính; mặt cầu ngoại tiếp/nội tiếp khối đa diện, trụ, nón; tiếp xúc mặt cầu–mặt phẳng; giao mặt phẳng với mặt cầu tạo đường tròn giao tuyến (`circle3`: bán kính, chu vi/diện tích thiết diện); diện tích mặt cầu $4\pi R^2$, thể tích $\frac{4}{3}\pi R^3$ | Hỗ trợ tối đa tổ hợp mặt cầu gắn với khối chuẩn hoặc mặt phẳng cắt có khoảng cách xác định tới tâm; không hỗ trợ giao của nhiều mặt cầu tự do | Giao tuyến hai hay nhiều mặt cầu lệch trục bất kỳ, chỏm cầu thể tích tích phân tổng quát (`OUT_OF_SCOPE`) |
| **6. Hình trụ (`cylinder`)** | Hình trụ tròn xoay đứng (từ bán kính đáy $R$, chiều cao $h$ / đường sinh $l$); thể tích, diện tích xung quanh, diện tích toàn phần; thiết diện qua trục (hình chữ nhật), thiết diện song song đáy (hình tròn), thiết diện song song trục cách trục khoảng $d < R$; mặt cầu ngoại tiếp/nội tiếp đồng trục | Chỉ hỗ trợ hình trụ tròn xoay đứng; mặt phẳng cắt giới hạn ở song song đáy, chứa trục, hoặc song song trục có khoảng cách xác định | Hình trụ xiên, thiết diện elip cắt xiên trục bất kỳ (`OUT_OF_SCOPE` / `BRIDGE_UNSUPPORTED_*`) |
| **7. Hình nón (`cone`)** | Hình nón tròn xoay đứng (hai trong ba đại lượng $R, h, l$ với $l^2 = R^2 + h^2$); thể tích, diện tích xung quanh, diện tích toàn phần; thiết diện qua trục (tam giác cân), mặt phẳng song song đáy chia nón theo tỉ số đỉnh $k$ (bán kính thiết diện, tỉ số thể tích, thể tích phần nón cụt còn lại); mặt cầu ngoại tiếp/nội tiếp đồng trục | Hình nón cụt được hỗ trợ khi biểu diễn qua phép cắt hình nón bởi mặt phẳng song song đáy; chưa có khai báo khối `frustum` độc lập trực tiếp | Hình nón xiên, mặt phẳng cắt nón tạo parabol/hyperbol/elip xiên, khối nón cụt nhập rời không qua hình nón gốc (`OUT_OF_SCOPE`) |

---

## 6. Những Giới Hạn Còn Lại (Công Bố Trung Thực)

1. **Lỗi chính tả mất dấu tiếng Việt (`S2-F-S07` — `"hình chop"`):** Vẫn từ chối an toàn (`UNGROUNDED_VALUE`) theo đúng chính sách S-1 không tự đoán từ sai chính tả để tránh suy diễn nhầm giả thiết.
2. **Đánh giá độc lập `H-1` (`BLOCKED_EXTERNAL_AUTHOR`):** Tập 60 đề độc lập do tác giả bên ngoài biên soạn chưa được cung cấp và chưa chạy Gemini live đối chứng; do đó chưa mở khóa quyết định thay thế mặc định `LLM_ONLY` trên môi trường production.
3. **Đánh giá sư phạm thực nghiệm với người học thật (`PEDAGOGICAL_HUMAN_VALIDATION = NOT_EVALUATED`):** Cấu trúc 5 câu hỏi giải thích bước, độ ngắn gọn và tính liên tục hình học đã được kiểm chứng tự động, nhưng mức độ dễ hiểu thực tế với học sinh phổ thông cần khảo sát người dùng thật.
4. **Các lớp toán học ngoài phạm vi thiết kế hiện tại:** Hình giải tích tọa độ `Oxyz`, bài toán quỹ tích/cực trị tham số, khối nón cụt khai báo độc lập, trụ/nón xiên, và mục tiêu mô phỏng đơn lẻ gom nhiều điểm ẩn danh `@dp*` cùng lúc — tất cả đều trả mã lỗi có kiểu rõ ràng (`OUT_OF_SCOPE`, `BRIDGE_UNSUPPORTED_*`), không phục vụ xấp xỉ sai.

---

## 7. API Opt-in, Hiệu Năng, Hồi Quy & Cổng Cuối Full T3

### 7.1. Chế độ API Opt-in và Rollback tức thời

- **Mặc định an toàn (Production Default):** `CHE_DO_MAC_DINH = "LLM_ONLY"`, `HYBRID_ROUTE_MODE = "off"`, `CACHE_VERSION = "131"`. Khi `off`, đường `LLM_ONLY` giữ nguyên hành vi cũ và cô lập lazy-import Route D.
- **Thử nghiệm sản phẩm Opt-in:**
  - `HYBRID_ROUTE_MODE=staging-replay` + `HYBRID_REPLAY_CORPUS=<path>` (`ALLOW_LIVE_AI=0`): chạy toàn bộ pipeline Hybrid `/4` qua `POST /api/analyze` bằng dữ liệu replay, gắn nhãn minh bạch `REPLAY_STAGING_SIMULATED` (`simulated: true`).
  - `HYBRID_ROUTE_MODE=live` + `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`: chạy trích xuất Gemini thật với timeout `60 s`/lần thử, deadline tổng `180 s`, cache tách biệt theo `runtime_identity` (`geometry-functions/33`), và trả lỗi chuẩn hóa `502`/`503`/`504` (`INFRASTRUCTURE_FAILURE`, `Cache-Control: no-store`) khi lỗi mạng — tuyệt đối không fallback ngầm sang `LLM_ONLY`.
- **Rollback:** Đặt lại `HYBRID_ROUTE_MODE=off` (hoặc bỏ biến môi trường này) lập tức đưa toàn bộ lưu lượng về `LLM_ONLY` mà không cần sửa code hay xóa cache.

### 7.2. Độ trễ & Bộ nhớ khi xử lý liên tiếp (`140` lượt end-to-end liên tiếp)

- Chạy `140` lượt liên tiếp (`70` đề C26 × `2` vòng sau warmup) qua `run_hybrid_offline` + `enrich_construction_continuity` + `validate_construction_continuity`:
  - Độ trễ xử lý backend tất định: **`p50 = 75.17 ms`**, **`mean = 82.44 ms`**, **`p95 = 222.64 ms`**, **`max = 264.86 ms`**.
  - Bộ nhớ Python (`tracemalloc`): đỉnh **`1.69 MB`**, chênh lệch heap ròng sau `140` lượt chỉ **`+77.34 KB`** (`~0.55 KB`/lượt) — không rò rỉ bộ nhớ, không tạo vòng lặp bước dựng hay tính lại hình học dư thừa.

### 7.3. Kiểm chứng cổng cuối Full T3 & Publication Safety

- **Authoritative Full T3** chạy trên worktree tách rời sạch `hm-t3-017bfb9f` tại frozen candidate `017bfb9fd61443f732b3e5f188aca24aa69b3171` (`2026-11-03T15:38:14Z` → `2026-11-03T15:51:59Z`; biên nhận máy: `docs/evaluation/geometry/runs/hybrid-master-backend-replacement/full-t3-017bfb9f.json`, `stdout_log_sha256 = 93fd90e1d238fe34066403ce89c09b386a57220fb2db71e9928f5ab7d71a8764`):
  - *(Ghi chú minh bạch quá trình chạy cổng: Lượt chạy đầu của script bọc tạm dùng chữ thường ổ đĩa `d:\` trên Windows làm Vitest nạp hai bản module qua junction `node_modules` dù `16,749` pytest backend, build và demo đều đạt; sau khi sửa đường dẫn chuẩn `D:\` trong script bọc — không đổi bất kỳ byte nào của repo — lượt chạy chính thức đạt toàn bộ 5/5 cổng con.)*
  - `pytest (toàn bộ backend)`: **PASS (`16,749 passed, 7 skipped, 2 deselected, 15 xfailed` trong `801.28s`, `0 failed`)**.
  - `vitest (toàn bộ frontend)`: **PASS (`85/85` test files, `1,502/1,502` tests trong `10.3s`, `0 failed`)**.
  - `typecheck + build production` (`tsc -b && vite build`): **PASS (`5.6s`)**.
  - `tập demo khoá luận` (`replay_demo_cases.py`): **PASS (`5/5` demo + `1/1` chuỗi rút gọn)**.
  - `bề mặt sập của demo` (`audit_demo_crash_surface.py`): **PASS (`6/6` biên từ chối đúng kiểu, `0` lỗi 500)**.
  - `freeze_evaluation_candidate.py --verify` trước và sau T3: **PASS (`exit_code = 0`, `source_tree_before = ""`, `source_tree_after = ""`, `freeze_sha256 = facaeff3…` không đổi)**.
  - Phán quyết cổng T3: **`FULL_PRODUCT_GATE_PASS`**.
- **Publication Safety (`check_publication_safety.py --range main..HEAD`):** **`PASS` (`violations = 0`, `pending_exception = 0`)**.

---

## 8. Trạng Thái Thực Tế Của Sản Phẩm & Việc Còn Cần Xử Lý (`≤ 3`)

- **Trạng thái thực tế:** **`FUNCTIONAL_BACKEND_COMPLETE`**. Backend Hybrid đã hoàn chỉnh chức năng từ đầu vào tiếng Việt đến `Scene3D`, chuỗi bước dựng tích lũy có kiểm chứng liên tục, giải thích 5 phần gắn với đối tượng hình học và đáp số chính xác có chứng chỉ. Hệ thống sẵn sàng cho thử nghiệm sản phẩm thực tế qua cấu hình opt-in mà không ảnh hưởng nhánh mặc định `LLM_ONLY`.

### Tối đa 3 việc còn cần Owner hoặc Frontend Session xử lý

1. **Frontend Session (tuỳ chọn nâng cấp giao diện học tập):** Hiển thị trực quan trường `step_summary` (`what`, `inputs`, `validity`, `result`, `next_use`) và các tập `created_ids` / `reused_ids` / `highlighted_ids` đã được backend xuất sẵn trong `scene3d.formation.steps` lên bảng chi tiết bước dựng (hiện frontend đã tương thích ngược 100%).
2. **Owner (triển khai thử nghiệm sản phẩm opt-in):** Bật `HYBRID_ROUTE_MODE=staging-replay` (offline) hoặc `HYBRID_ROUTE_MODE=live` (kèm `ALLOW_LIVE_AI=1` và `GEMINI_API_KEY`) trên môi trường thử nghiệm người dùng để thu thập phản hồi sư phạm thực tế; giữ `HYBRID_ROUTE_MODE=off` làm công tắc rollback tức thời.
3. **Owner & Tác giả độc lập (khi cần quyết định chuyển mặc định khỏi `LLM_ONLY`):** Cung cấp bộ 60 đề độc lập `H-1` theo gói `docs/evaluation/geometry/runs/hybrid-independent-h1/H1_AUTHORING_HANDOFF.md` và phê duyệt ngân sách live tương ứng để thực hiện đánh giá đối chứng độc lập trước khi cutover production.
