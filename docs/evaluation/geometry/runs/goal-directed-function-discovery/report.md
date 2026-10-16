# Goal-directed function discovery — khoảng cách từ điểm dẫn xuất không tên (LOCAL, 2026-10-16)

**Kết luận: `FUNCTION_DISCOVERY_SLICE_READY_FOR_REVIEW`** (chi tiết T3/review ở §7). Nhánh
`research/goal-directed-function-discovery`, chồng lên `8c24cb52` = `main` `2a3c0787` + result binding `f83b4ed1` + Scene3D
W1–W3 — **cả hai lớp dưới chưa được tích hợp, Scene3D chưa được review độc lập**. Không merge, không push, 0 lượt gọi
Gemini, `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 125`, Hybrid tắt trên sản phẩm.

Chuỗi commit: tiền đăng ký `66593504` → RED `b30c46af` → sản phẩm `9fec9f43` → tooling `dda0d888` → bằng chứng `98f0d1a1`
→ refreeze `e02b7c7f` (`8f77fec7…`) → tài liệu `ae12069a` → T3 lần 1 **FAIL** → sửa lỗi kế thừa `19eec205` + `36b6d3f9` → T3 lần 2
PASS → review độc lập → sửa sau review `cfa27baa` (**sản phẩm cuối**) → đo lại `313cc537` → refreeze `81315986` (candidate
`093359c2…`, 110 file) → tài liệu + T3 cuối (§7).

## 1. Năng lực mới (trả lời A)

Trước: Planner chỉ phục vụ khoảng cách từ **điểm có tên**. Đề hỏi *"Tính khoảng cách từ trung điểm của SC đến (SAB)"* bị từ
chối (benchmark B27, khoảng trống tổ hợp đăng ký từ 2026-10-11). Sau: Planner tự dựng điểm không tên rồi đo tới

| đích | chuỗi Planner tìm được từ hợp đồng | ví dụ (corpus) |
|---|---|---|
| mặt phẳng có tên | `midpoint` (điểm tươi M) → `ask_distance_point_plane` | trung điểm SC → (SAB): d² = 1 |
| đường có tên | `midpoint` → `orthogonal_projection_line` (chân tươi H) → `ask_length` | trung điểm SC → BD: d² = 9/4 |
| giao tuyến có nguồn | `midpoint` → `intersection_line` (đã khai) → chân H trên giao tuyến → `ask_length` | trung điểm SC → (SAB)∩(SCD): d² = 13/4 |

Ở mọi đích: tái dùng điểm đề đã đặt tên ("Gọi M là trung điểm SC" ⇒ 0 điểm tươi), dùng chung một điểm tươi cho nhiều câu
hỏi, nhãn tươi tránh nhãn của đề (M → M1). Họ hình đã đo: chóp tứ giác, lập phương, hình hộp, lăng trụ đứng tam giác đều
(khung affine + Gram). Cảnh 3D: khối → dựng M ("Dựng M là trung điểm của đoạn SC.") → [giao tuyến] → chân H có ký hiệu
vuông góc → đáp số; với đích mặt phẳng, chọn đại lượng hiện đoạn vuông góc và nhãn `d(M, (SAB)) = 1`
(`visual/images/pyr-midpoint-to-plane-quantity-selected.png`).

## 2. Audit trước khi sửa (§4 của brief)

| câu hỏi | trước (`geometry-fact-planner/5`) | sau (`/6`) |
|---|---|---|
| Registry khai gì cho Planner | 3 contract (input/effect/kiểu) nhưng **không** khai cách viết lời gọi | contract mang khuôn đối số `call`, gốc nhãn tươi `fresh`, `descriptor` + cụm nguồn `phrase` |
| `_EffectResolver` tìm ngược thế nào | lặp REGISTRY theo tên, hợp nhất slot theo **tên** (gộp env), `_emit` là `switch` 3 nhánh theo `source_policy` | hợp nhất theo **vị trí** toán hạng của hiệu ứng; lọc kiểu Point/Line/Plane **trước** khi đếm candidate; phát lời gọi bằng `render_call` dùng chung với cổng |
| goal còn phụ thuộc expansion viết sẵn | mọi câu hỏi trừ khoảng cách điểm–đường; `_mat_qua_diem` (mặt song song) | vẫn vậy — chỉ câu hỏi `distance` vào resolver (thêm một goal entry cho toán hạng mô tả) |
| hàm mới đăng ký có được khám phá | **không**: có contract vẫn chết ở `_emit` (`producer chưa được khai`) | **có**, nếu hiệu ứng thuộc loại đã có và engine có vị từ kiểm cho mô tả (§5) |
| sinh đối tượng trung gian không tên | chỉ chân vuông góc (H) | chân + điểm mô tả (trung điểm; trọng tâm khi thêm contract) |
| tái dùng, chu trình, mơ hồ, mâu thuẫn | memo + available binding cho chân; `DEPENDENCY_CYCLE`; mâu thuẫn do engine | available binding cho **mọi** contract `fresh`; giữ nguyên phần còn lại |
| đúng/sai phụ thuộc thứ tự Registry | không (sắp theo tên) | không — đo: Registry đảo thứ tự cho kế hoạch **trùng từng ca** (§4) |

## 3. Vì sao là năng lực mới, không phải cách diễn đạt mới

Toán hạng không tên không có trong IR như một đối tượng của đề: Planner phải **sinh** một lời gọi dựng chưa từng có trong
dữ kiện, chọn producer qua hợp đồng, gắn nó vào chuỗi đo, và cổng phải chấp nhận một nhãn không có trong đề mà vẫn
fail-closed. Không thêm hàm hình học, phép IR, Kernel hay trường lược đồ nào; không có công thức theo dạng bài.
Ngoài phạm vi (cố ý): chân vuông góc lên mặt phẳng như **bước dựng** (hiện là nhân chứng của đại lượng), giao điểm không tên
của hai đường (lược đồ không có chỗ cho hai nhóm toán hạng), góc, diện tích, thể tích qua resolver, CEGIS/chứng minh.

## 4. Thực nghiệm so sánh (tiền đăng ký `preregistration.md`, cùng một bundle Typed Facts `56a4fe1c…`)

Ba nhánh mã chạy trong worktree tách rời; nhãn và oracle không sửa sau RED. Số liệu: `results/comparison.json` (NEW tại
`9fec9f43`) và `results/final-cfa27baa/comparison.json` (NEW tại sản phẩm cuối — trùng từng ca).

| corpus | FIXED `2a3c0787` (/4) | BOUNDED `8c24cb52` (/5) | NEW `9fec9f43` = `cfa27baa` (/6) |
|---|---|---|---|
| dương mới (9) | 0 đúng · 9 từ chối nhầm | 0 · 9 từ chối nhầm | **9 đúng chính xác** · 0 sai |
| âm mới (16) | 1 đúng mã · 15 sai mã | 1 · 15 sai mã | **15 đúng mã** · 1 sai mã (D-1) · 0 phục vụ |
| benchmark 30 (đông cứng) | 19 / 9 / 0 / 2 | 19 / 9 / 0 / 2 | 19 / 9 / 0 / 2 |
| result binding 18 | 0 / 6 từ chối nhầm; 12 âm sai mã | 6 đúng · 12 đúng mã | 6 · 12 (trùng BOUNDED) |
| hai-đường dev 45 / held-out 32 | 12+33 / 11+21 | như FIXED | như FIXED |

Cặp NEW–BOUNDED: **0/125** ca hồi quy khác `(status, code, answers)`. Mọi khác biệt nằm ở 28 ca mới.
B27 của benchmark vẫn là từ chối nhầm vì dữ kiện đông cứng của nó mã hoá câu hỏi là `unsupported` (không sửa nhãn).

**Tách ảnh hưởng của Registry (cùng mã NEW, chỉ đổi dữ liệu catalog):**

| biến thể | dương mới | discovery (3) | âm | ghi chú |
|---|---|---|---|---|
| production | 9/9 | 0 (`UNSUPPORTED_CAPABILITY`) | 15 + D-1 | |
| bỏ contract `midpoint` | 0/9 | 0 | — | năng lực mất đúng chỗ phụ thuộc |
| bỏ contract `ask_distance_point_plane` | 3/9 (chỉ đích là đường) | 0 | — | 6 ca đích mặt phẳng `UNSUPPORTED_CAPABILITY` |
| **+ contract `centroid` (thử nghiệm)** | 9/9 | **3/3 đúng chính xác** (16/9, 25/9, 40/9) | 14 + D-1 + 1* | 0 dòng thay đổi ở `planner.py` / cổng / engine |
| Registry đảo thứ tự | 9/9 | 0 | như production | kế hoạch **trùng từng ca** |
| contract nói dối (mô tả `centroid` gắn vào hàm `midpoint`) | 0/9 | 0 (`ENGINE_SELF_CHECK_FAILED`) | — | **0 phục vụ sai** |

\* `centroid-without-contract` là ca âm *có điều kiện Registry sản phẩm*; dưới Registry thử nghiệm nó chính là ca discovery
X1 và được phục vụ 4/3 = √(16/9) — đúng oracle; bộ phân loại máy ghi `wrong_served` theo nhãn, không phải đáp số sai.

**Tìm kiếm và tài nguyên (NEW, 12 ca phục vụ):** needs 6–9 (trần 32), candidates 3–5 (trần 8), độ sâu lớn nhất 3 (= trần,
chỉ ở lá mặt phẳng của giao tuyến), điểm tươi ≤ 2 mỗi đề (trần 8), 5–9 lời gọi, `lap_ke_hoach` 2,1–7,2 ms, cả tuyến 6,7–18 ms,
đỉnh bộ nhớ planner ≤ 90,5 KB. Một mô tả lồng thêm một tầng (điểm mô tả từ điểm mô tả) sẽ chạm `PLAN_TOO_LARGE`. Mỗi trần
hạ xuống đều từ chối `PLAN_TOO_LARGE`, không phục vụ một phần (test).

**Số quy tắc phối hợp phải thêm:** 1 nhánh goal entry (toán hạng mô tả → `AnswerDistance`) phủ 2 mô tả × 3 loại đích = 6
dạng; 0 công thức. Fixed-rule Planner cần ≥ 6 công thức cho cùng phạm vi. Hàm hình học mới: 0. Hàm Registry tái dùng: 5.

**Metamorphic (test):** đổi tên điểm, đảo thứ tự dữ kiện, toán hạng `CS`/`SC`, co giãn ×2 (bình phương ×4), va chạm nhãn
(M → M1) — giữ đáp số trên cả 3 loại đích. **Giả mạo:** sửa env, toán hạng mô tả, đích, quote, nhãn tươi trùng đề, bỏ
chứng chỉ, tuyến A tự dùng nhãn tươi — đều bị từ chối tại cổng (`AUXILIARY_RULE_MISMATCH` / `UNKNOWN_LABEL`).

## 5. Thuật toán: Bounded Effect Planner → Goal-directed function discovery (có biên)

1. **Hợp đồng là dữ liệu đủ để viết lời gọi.** `PlanningContract(inputs, effect, call, fresh, descriptor, phrase)`;
   `render_call` là bộ viết duy nhất, dùng chung cho Planner (phát) và cổng (kiểm lại).
2. **Hợp nhất theo vị trí:** đầu vào `Foot(F,P,L)` của `ask_length` nhận giá trị từ hiệu ứng `Foot(F,P,L)` của producer theo
   vị trí, không theo trùng tên slot — một hàm mới không cần đặt tên slot giống hàm cũ.
3. **Lọc kiểu trước khi đếm:** toán hạng Point/Line/Plane sai kiểu loại candidate trước khi tốn ngân sách.
4. **Nhu cầu `Point` là mô tả** `("desc", kind, operands)`: giải bằng producer có `descriptor` cùng loại và cùng arity.
5. **Tái dùng** lời gọi sẵn có cùng hiệu ứng (so khớp khuôn, đường/mặt không thứ tự); memo giữa các câu hỏi.
6. **Chọn** chi phí nhỏ nhất (số phép dựng mới), hoà theo tên hàm — không theo thứ tự catalog.
7. **Kiểm độc lập:** cổng đọc chứng chỉ `effect-chain` như một cây dẫn xuất (mỗi cạnh: lời gọi = khuôn(env), đầu vào không
   phải lá phải được sinh trong chuỗi); engine kiểm **vị từ theo mô tả** (`2X = P + Q`, `3G = A + B + C`) và đối chiếu
   đáp số² với khoảng cách² tới đích tính trực tiếp bằng Gram. Vì thế hợp đồng nói dối không thể phục vụ sai.

Giới hạn thật của "khám phá": chỉ trong các **loại hiệu ứng đã có** (Point, Foot, Line, AnswerDistance); mô tả phải biểu
diễn được bằng `point_kind` của lược đồ (midpoint, centroid, …) và có vị từ trong engine; goal entry chỉ cho `distance`.

## 6. Lệch so với tiền đăng ký (ghi nhận, không sửa nhãn)

- **D-1:** `parallel-result-line` (lập phương + giao tuyến của hai mặt song song) bị từ chối `SOURCE_PREMISE_UNREAD`, không phải
  `PARALLEL_*`: văn phạm tiền đề đóng của mọi đề có `line_ref` (có từ run trước) không đọc "hình lập phương". Ca vẫn là từ
  chối đúng về an toàn nhưng **không thử được điều nó định thử**. Bổ sung sau đăng ký (test, không phải hàng corpus): cùng
  mục tiêu trên hình hộp ⇒ `PARALLEL_NO_INTERSECTION`. Issue `ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE`.
- **Sửa trong lúc làm (RED → GREEN, trước commit sản phẩm):** (i) so khớp chân có sẵn phụ thuộc thứ tự viết đường (`DB` ≠
  `BD`) — hồi quy do bản nháp đầu, đã có test, sửa trong `same_call`; (ii) quét nhãn H hai nơi làm mutant "scanner-only label
  choice" thành tương đương — gộp về một chỗ; (iii) tra cứu chân của đường cũ ném `StopIteration` dưới mutant — nay từ chối
  có mã. Mutant "asks the wrong segment" chuyển sang phép gán theo vị trí (cùng phép kiểm diệt), vì phân đoạn hỏi nay do khuôn
  contract viết.

## 7. Cổng, review, Git (trả lời G)

**Review độc lập** (tác nhân riêng, ngữ cảnh mới, chỉ đọc; báo cáo là kết quả hội thoại, không phải artifact kho):
`PASS_WITH_FINDINGS`, **0 phục vụ sai** trên mọi probe; tự dựng lại base `8c24cb52` và xác nhận 125 ca hồi quy trùng cả ở
mức lời gọi/trace/cảnh, kế hoạch không đổi khi đảo Registry (153 ca), D-1 có từ trước, mutant dời là có nghĩa.

| phát hiện | xử lý |
|---|---|
| IMP-1 không test nào khoá ràng buộc **đích** trong cổng chuỗi (mutant phục vụ khoảng cách tới đích khác) | test mới (đường AC, mặt (SAD), "đáy") ⇒ `SOURCE_OBJECT_MISMATCH`; mã vốn đúng |
| IMP-2 cổng phủ đọc **mọi** cụm mô tả trong quote đã chứng nhận ⇒ câu hỏi thứ hai cùng quote bị bỏ im lặng | `cfa27baa`: chỉ span đã buộc được tính là đã đọc (`kiem_nguon` truyền span) ⇒ `QUESTION_CONTEXT_UNSUPPORTED`; RED → GREEN |
| IMP-3 lỗ văn phạm kế thừa từ đường điểm có tên (`(SABC)` chung 3 điểm, ", AC", "sau đó tính thể tích…" chỉ trả một đáp số) | **không sửa** (có từ `8c24cb52`, ngoài lát); ghi vào `ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES` |
| MINOR-4 chứng chỉ dị dạng tự viết ném ngoại lệ | `cfa27baa`: `AUXILIARY_RULE_MISMATCH` có mã; 6 test |
| MINOR-5 kiểm đáp số engine, va chạm nhãn tươi, bộ lọc kiểu không có test | 3 test mới, mỗi test diệt đúng mutant ấy |
| MINOR-6 hai bộ sinh nhãn tươi; văn phạm đích thứ hai | gộp `_NHAN_PHU = _nhan_tuoi("H")`; trùng văn phạm đích ghi nợ (§9) |
| MINOR-7 lời kể "đoạn CS" khi đề viết SC | do thứ tự `depends` của tầng cảnh, có từ trước (trung điểm đề đặt tên cũng vậy) — giới hạn trình bày, không sửa |
| MINOR-8 `points_b` trùng nhãn ⇒ mã sai | `FACT_INCOMPLETE` |

Sau sửa: 6 biến thể × 153 ca **trùng từng ca** với lần đo ở `9fec9f43` (`results/final-cfa27baa/`); cảnh xuất lại trùng byte,
nên receipt trình duyệt giữ hiệu lực.

**T3:** lần 1 tại `ae12069a` **FAIL** (`verification/t3-attempt1-ae12069a-FAIL.log`): (i) lớp divergence của run chưa nối chuỗi
`corrects` ⇒ `test_C2b` đỏ; (ii) `scene3d-auxiliary.test.ts` của Scene3D W1–W3 gọi `withSubEntities` với hai đối số ⇒
`tsc -b` đỏ (vitest vẫn xanh; wave ấy chưa từng chạy build). Sửa ở `36b6d3f9`, `19eec205` (chỉ test, không đổi hành vi).
Lần 2 tại `36b6d3f9`: `FULL_PRODUCT_GATE_PASS` (pytest 10101/0, vitest 1061/1061, build, demo 5/5, bề mặt sập 6/6) — trên
sản phẩm `9fec9f43`, nay đã bị thay. Lần cuối trên sản phẩm `cfa27baa`: `verification/t3-authoritative.log` (dòng kết ở
`verification/t3-pass.json`).

**Git:** `main` = `origin/main` = `2a3c0787`; không merge, không push, không viết lại lịch sử; `frontend/public/` của người dùng
không đụng; không trailer `Co-Authored-By`. Điều kiện tích hợp: (1) người dùng quyết result binding; (2) review độc lập
Scene3D W1–W3; (3) quyết định lát này — hợp nhất fast-forward cả chồng hoặc cherry-pick lát (chỉ chạm tuyến D + 2 script harness
+ 1 test Scene3D + tài liệu). Hybrid trong sản phẩm vẫn NO-GO.

## 8. Phần nghiên cứu (cho khoá luận / bài báo)

1. **Vấn đề.** Trong một thư viện hàm hình học đóng, một Planner có thể tự tổng hợp chuỗi dựng cho dạng đề mới từ hợp đồng
   hiệu ứng, thay vì viết công thức cho từng dạng, mà vẫn giữ "đúng hoặc từ chối"?
2. **Khoảng trống ứng viên** (chưa đối chiếu tài liệu — *không* tuyên bố novelty): kết hợp lập kế hoạch ngược kiểu STRIPS/HTN
   có biên trên một catalog hàm hình học **với** chứng chỉ dẫn xuất được cổng nguồn và engine chính xác kiểm lại từng cạnh,
   trong bối cảnh đề tiếng Việt và mô phỏng học tập. Cần một wave đọc tài liệu (`THESIS_REFERENCES.md`, luật mức xác minh).
3. **Baseline và phương pháp.** FIXED (luật ánh xạ + công thức độ sâu 1), BOUNDED (resolver có trần, phát lời gọi bằng
   switch), NEW (§5). Cùng bundle Typed Facts đã kiểm; ảnh hưởng Registry tách bằng ablation trên cùng mã.
4. **Thành phần mới/mở rộng.** Khuôn lời gọi trong hợp đồng + bộ viết dùng chung; hợp nhất theo vị trí; nhu cầu mô tả; chứng
   chỉ chuỗi kiểm cạnh; vị từ ngữ nghĩa theo mô tả trong engine (bất biến với producer được chọn).
5. **Thiết kế và dữ liệu.** 9 dương + 16 âm + 3 discovery do tác giả viết cùng lúc với lát (`NOT_HELD_OUT`), oracle độc lập
   Fraction/Gram; hồi quy 125 ca của các run trước (một phần là held-out lịch sử của run hai-đường).
6. **Kết quả quan sát.** §4. Tóm tắt: năng lực mới 9/9 với 0 phục vụ sai; 0 hồi quy trên 125 ca; một hợp đồng thêm dưới dạng
   dữ liệu mở 3 dạng đề mới với 0 dòng mã Planner/cổng/engine; hợp đồng sai bị engine bắt.
7. **Giới hạn và đe doạ hiệu lực.** Corpus nhỏ, cùng tác giả, không held-out; Typed Facts do người viết (trích xuất live dạng
   toán hạng mô tả `NOT_MEASURED` — prompt provider không đổi nên mô hình chưa được dặn dạng này); khám phá chỉ trong các loại
   hiệu ứng có sẵn và cần vị từ engine; một ca âm lệch mã (D-1); FIXED/BOUNDED/NEW khác cả Registry (đã tách bằng ablation);
   thời gian đo trên một máy, một lượt; không đo người học.
8. **Tuyên bố được phép** (đề xuất hàng `A4` cho `research/CLAIM_EVIDENCE_MAP.md`, mức `MEASURED (offline)`): *"Trên corpus phát
   triển 28 ca và 125 ca hồi quy, Planner tổ hợp theo hợp đồng phục vụ đúng 9/9 dạng khoảng cách từ điểm dẫn xuất không tên
   mà hai Planner trước từ chối, không đổi kết quả nào của 125 ca cũ; thêm một hợp đồng dưới dạng dữ liệu mở thêm 3 dạng mà
   không sửa mã Planner."* Không được viết: "Planner giải được bài hình học tổng quát", "khám phá hàm bất kỳ", "giảm token",
   "chính xác với Gemini", "giúp học sinh hiểu hơn". `IMPLEMENTED`: lát này; `MEASURED`: §4 (offline); `HUMAN_REVIEWED`: không;
   `NOT_MEASURED`: trích xuất live, token, độ trễ live, tác động học tập.

## 9. Bước mở rộng kế tiếp đề xuất (trả lời F)

Theo blocker thật của run này, theo thứ tự:

1. **Goal entry chung cho câu hỏi** (góc đường–mặt, diện tích, thể tích đi qua resolver, `ask_*` hiện có làm producer chi
   phí 0) — điều kiện để "khám phá" không chỉ ở khoảng cách. Rủi ro: hồi quy cổng câu hỏi; cần đo bất biến như §4.
2. **G16 góc đường–mặt dựng hình chiếu** (chân S lên mặt + góc tại giao điểm) — cần một hàm đo góc giữa hai đường và cung
   đánh dấu góc (L11 thiếu); chân lên mặt nên thành hiệu ứng `Foot` qua `orthogonal_projection` (đã dựng tiến được).
3. **Transport hai nhóm toán hạng** (giao điểm không tên của hai đường) — đổi lược đồ Typed Facts ⇒ cần phê duyệt riêng.
4. `ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE` (nhỏ, an toàn) và lỗ văn phạm IMP-3 (một văn phạm đích chung cho ba đường
   khoảng cách thay cho ba bản hiện có).
G05/G17/hình cong không bị lát này mở khoá; giữ thứ tự ROADMAP.

## 10. Trả lời B–E, G

- **B.** Planner tự chọn và phối hợp producer qua hợp đồng; đã chứng minh bằng thí nghiệm thêm hợp đồng dạng dữ liệu (0 dòng
  mã Planner). Vẫn còn một nhánh goal entry viết tay (theo *loại câu hỏi*, không theo dạng bài).
- **C.** Corpus mới, NEW: 9 phục vụ đúng, 0 phục vụ sai, 15 từ chối đúng mã, 1 từ chối khác mã (D-1), 0 từ chối nhầm dương.
- **D.** Dùng chung cho mọi khối engine dựng được (đã đo chóp tứ giác, lập phương, hình hộp, lăng trụ tam giác đều); mọi đích
  mặt / đường / giao tuyến; mô tả: trung điểm (sản phẩm), trọng tâm tam giác (thử nghiệm).
- **E.** Đủ cho một mục khoá luận ở mức `MEASURED (offline, NOT_HELD_OUT)` với các giới hạn §8.7. Hạt nhân có thể thành bài
  báo: "hợp đồng hiệu ứng có khuôn + chứng chỉ dẫn xuất kiểm cạnh + vị từ ngữ nghĩa trong engine" — cần tập độc lập, so sánh
  tài liệu, và trích xuất live trước khi gửi.
- **G.** §7.
