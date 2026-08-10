# W4B-2I — MÔ HÌNH TƯƠNG TÁC: QUAN SÁT TRƯỚC, THAO TÁC SAU

`THESIS_SCOPE = T3`. Baseline `fc0634a`. Tài liệu **audit**, không phải báo cáo
trạng thái — số sống ở `docs/CURRENT_STATE.md`.

## 1. Đính chính tiền đề trước khi sửa bất cứ thứ gì

Bản yêu cầu wave này mô tả sản phẩm hiện tại là *"chạy → dừng ở bước quyết định
→ bắt học sinh trả lời → mới chạy tiếp"*. **Đọc mã thì tiền đề đó SAI**, và sai
theo hướng quan trọng: nếu tin nó rồi dựng một cổng `BASELINE_OBSERVED`, ta sẽ
thêm một cái khoá để chữa một chứng bệnh không tồn tại.

Bằng chứng, bốn đường độc lập:

| Điều bị cho là đang xảy ra | Sự thật tại `fc0634a` |
|---|---|
| Lượt chạy đầu dừng chờ trả lời | `SimulationControls.tsx:38` — tự chạy là `setInterval(nextStep)`, không cổng nào |
| Timeline bị chặn bởi câu trả lời | `store.ts:333` — `nextStep` không hề đọc `prediction` |
| Quiz cắt ngang quan sát | `PredictionBar.tsx:75` — `if (busy) return null`; ngoài ra mặc định THU GỌN |
| Thao tác sai làm hỏng canonical | `store.ts:318` — `submitPrediction` chỉ ghi `prediction`, không đụng `active.state` |

Hệ quả: năm bất biến §54 (`OBSERVE_REQUIRES_NO_ANSWER`,
`AUTOPLAY_REQUIRES_NO_LEARNER_ANSWER`, `TIMELINE_REQUIRES_NO_LEARNER_ANSWER`,
`WRONG_DIRECT_ACTION_PRESERVES_CANONICAL_STATE`, `ENGINE_OWNS_ACTION_VERDICT`)
**đã đúng từ trước wave này** và đã có test khoá
(`experiment-gate-w4b2b.test.tsx`, `observation-preservation.test.tsx`).

Thêm nữa, 7/9 target đã ẩn vùng cam kết sau cổng do học sinh tự mở
(`interaction-policy.ts:252`). Các ví dụ được nêu — `[LEFT][MID][RIGHT]`,
`[COUNT][SKIP]`, `[SHIFT][STOP]` — đều thuộc nhóm ĐÃ GÁC CỔNG, nghĩa là chúng
chỉ hiện ra **sau khi học sinh chủ động mở Thí nghiệm**.

**Lời phê bình đúng, sau khi đính chính:** vấn đề không phải thiếu cổng. Vấn đề
là **thứ nằm sau cổng là một hàng nút rời, không phải sân khấu**.

### 1b. Vì sao KHÔNG dựng `BASELINE_OBSERVED`

1. **Nó lấy đi quyền, không thêm quyền.** Hiện học sinh mở Thí nghiệm được ngay
   ở bước 1. Cổng theo lượt-chạy-đầu bắt xem hết mới được thao tác — ít tự chủ hơn.
2. **Nó chính là thứ nó tự nhận không phải.** "Chưa hoàn thành thì chưa mở khoá"
   là khuôn gamification, dù không gắn huy hiệu.
3. **`RULES.md §3c`.** Bề mặt cam kết đã qua W4B-2B → 2C → 2D → 2V → 2V/C2. Một
   wave thứ sáu **thêm khoá** vào đúng capability đó là DEEP_HARDENING theo dấu
   hiệu "một capability phụ cần từ ba patch wave trở lên".
4. Tiền lệ gần nhất nói ngược lại: `fb78d7b fix(algorithm): gate the learner's
   agency, not the simulation's state`.

Quyết định (user duyệt): **bỏ `BASELINE_OBSERVED`**, giữ cổng do học sinh mở,
tiêu wave vào ba việc thật ở §4.

## 2. Ma trận TƯƠNG TÁC TRỰC TIẾP — 9 target (suy từ nguồn)

Nguồn: `ALGORITHM_IDS` (9) · `decision.ts` · `interaction-policy.ts` · `ui.tsx`.

| target | họ | mô hình | hành động ngữ nghĩa | chỉ số sân khấu có trong model? | cổng | phân loại |
|---|---|---|---|---|---|---|
| `linear_search` | search | `searchInteractionOf` | `found` · `continue` | **có** — `currentIndex` + `visualRole` | có | **DIRECT_SCENE_READY** |
| `binary_search` | search | `searchInteractionOf` | `search-left` · `search-right` · `found` | **có** — `activeRange{left,right,middle}` + `visualRole` | có | **DIRECT_SCENE_READY** |
| `bubble_sort` | sort | `sortInteractionOf` | đổi chỗ · giữ nguyên | không (chỉ chuỗi "Vị trí n" trong `facts`) | **KHÔNG** | SCENE_ADJACENT_READY |
| `selection_sort` | sort | `sortInteractionOf` | chọn cực trị mới · giữ | không (như trên) | **KHÔNG** | SCENE_ADJACENT_READY |
| `insertion_sort` | sort | `sortInteractionOf` | dời phải · dừng | không (như trên) | có | SCENE_ADJACENT_READY |
| `find_max` | scan | `scanInteractionOf` | đặt max mới · giữ | không (chỉ `candidateLabel` chuỗi) | có | SCENE_ADJACENT_READY |
| `find_min` | scan | `scanInteractionOf` | đặt min mới · giữ | không | có | SCENE_ADJACENT_READY |
| `count_if` | scan | `scanInteractionOf` | đếm · bỏ qua | không | có | SCENE_ADJACENT_READY |
| `sum_if` | scan | `scanInteractionOf` | cộng · bỏ qua | không | có | SCENE_ADJACENT_READY + **biến tích luỹ chưa chiếu lên sân khấu** |

### 2b. Vì sao họ TÌM KIẾM là pilot đúng, không phải chọn bừa

`SearchInteractionModel` là mô hình DUY NHẤT đã mang **toạ độ ngữ nghĩa thật**:
`currentIndex` (số), `activeRange` (số), và `SearchAction.visualRole` — một từ
vựng vị trí sân khấu (`left-region` · `middle-item` · `right-region` ·
`current-item` · `continue-region`) **đã tồn tại từ W2** nhưng tới nay chỉ được
tiêu vào một tên class CSS (`SearchActionZone.tsx:164`).

Nói cách khác: từ vựng gắn-hành-động-vào-sân-khấu **đã có sẵn trong tầng sở hữu
ngữ nghĩa**, chưa ai nối nó vào renderer. Nối lại = REUSE, không phải abstraction
mới. Hai họ kia muốn scene-bound thì phải **thêm chỉ số vào model trước** — đó là
việc thật, không giấu được, và không thuộc wave này.

Thêm một lý do: `binary_search` là quyết định **KHÔNG GIAN** thật (loại nửa nào),
đúng chỗ thao tác trực tiếp có nghĩa nhất — và cũng chính là ví dụ chủ đạo của
bản yêu cầu.

### 2c. `count_if` / `sum_if` — vì sao KHÔNG ép thành DIRECT

Hành động ở đây là một vị từ (`đếm` / `bỏ qua`), không phải một vị trí. Phần tử
đang xét đã được tô sáng; bấm vào chính nó không phân biệt được "đếm" với "bỏ
qua" nếu không đẻ thêm affordance thứ hai ở chỗ khác. Ép scene-bound sẽ làm UI
**khó hiểu hơn** để đổi lấy một ô xanh trong ma trận. Phân loại trung thực là
**SCENE_ADJACENT**. `sum_if` còn thêm rào: biến tích luỹ chưa được chiếu lên sân
khấu (`ScanInteractionModel.accumulatorValue` chỉ tới vùng hành động), nên "cộng
vào tổng" chưa có hệ quả thị giác trên sân khấu — ghi nhận là blocker, **không**
mở màn thiết kế lại biểu diễn trong wave này.

## 3. Ma trận WHAT-IF — 22 target (suy từ `apply`)

Phép thử tất định: `apply` có phải identity không, và có đường engine tính lại không.

| phân loại | số | target |
|---|---|---|
| `WHAT_IF_INPUT_READY` | **12** | 9 target thuật toán trực tiếp (`whatif_swap` → nhánh, engine chạy lại) · `logic.and_gate` · `logic.boolean_dag` (bật/tắt tín hiệu vào) · `binary.decimal_to_binary` |
| `WHAT_IF_STRUCTURE_READY` | **1** | `generic.rule_scene` (drag + `EditPolicy`/`SimulationPatch`) |
| `WHAT_IF_BLOCKED` (`apply` = identity) | **9** | `algorithm.scan` · `algorithm.bounded_control_flow` · `binary.base_conversion` · `binary.character_encoding` · `database.relational_table_query` · `network.protocol_encapsulation` · `network.graph_traversal` · `tree.traversal` · **`network.packet_routing`** |

12 + 1 + 9 = 22.

**`network.packet_routing` là ca đặc biệt và là lý do nó được chọn làm pilot:**
nó nằm nhóm BLOCKED vì `apply: (state) => state`
(`network/index.ts:112`) — nhưng đường **engine tính lại đã có sẵn và tất định**:
`bfsRoute()` + `buildSteps()` là hàm thuần của `(nodes, links, source,
destination)` (`network/model.ts:59,94`). Nghĩa là nó BLOCKED vì thiếu *hợp đồng
thao tác*, không vì thiếu *engine*. Đây là khoảng cách rẻ nhất và mang nhiều
bằng chứng T3 nhất trong cả danh mục.

### 3b. Ràng buộc thật khi mở what-if cấu trúc cho mạng

`validateNetworkConfig` **từ chối fail-closed** khi không có đường đi
(`network/index.ts:63`), và `buildSteps` sẽ **ném lỗi** với route rỗng
(`byId[route[0]]` → `undefined.type`, `model.ts:96`).

Nên "ngắt liên kết rồi thấy gói tin không tới được" — tình huống sư phạm đắt giá
nhất của bài này — **không biểu diễn được nếu không đụng engine**. Đây là mâu
thuẫn nội tại của bản yêu cầu: nó đòi *"engine sinh trạng thái không-tới-được
tất định"* đồng thời đòi `NO_ENGINE_TRUTH_CHANGE`.

Quyết định (user duyệt): **thêm trạng thái không-tới-được TƯỜNG MINH**. Đây
không phải sự thật mới — BFS đã trả `[]` từ trước; chỉ là làm cho `[]` trở thành
trạng thái **hợp lệ và biểu diễn được**, thay vì một ca ném lỗi. Ranh giới R0
không đổi: renderer vẫn không tự tính định tuyến.

## 4. Phạm vi wave này

| # | Việc | Vì sao |
|---|---|---|
| I-B | Gác cổng `bubble_sort` + `selection_sort` (7/9 → 9/9) | hai bài DUY NHẤT còn bày vùng cam kết + câu "Em hãy quyết định bước tiếp theo." ngay ở Quan sát. Đây mới đúng là chỗ rò quiz-like |
| I-C | Gắn hành động vào sân khấu + bàn phím cho **họ tìm kiếm** | `visualRole`/`activeRange` đã có; renderer chưa dùng. `ArrayView` hiện `role="img"`, kéo bằng chuột, **không phím** |
| I-D | What-if cấu trúc cho `network.packet_routing` + trạng thái không-tới-được | engine đã sở hữu tính lại; chứng minh sửa-mô-hình → engine → hệ quả thị giác |

**KHÔNG làm trong wave này:** `BASELINE_OBSERVED` · scene-bind họ scan/sort
(cần thêm chỉ số vào model trước) · `sum_if` accumulator · các mục §62.

## 5. Bảng sở hữu (trước khi sửa)

| trách nhiệm | chủ sở hữu hiện tại |
|---|---|
| vòng đời/timeline/autoplay | `state/store.ts` (`nextStep`/`goToStep`/`resetSim`) + `SimulationControls` (bộ đếm giờ) |
| trạng thái hoàn tất | `timeline.currentStep === stepCount - 1` (dẫn xuất, không lưu) |
| điểm quyết định + hành động ngữ nghĩa | `domains/algorithm/decision.ts` |
| chính sách hiện/ẩn công cụ | `domains/algorithm/interaction-policy.ts` (`experimentGated`, `commitmentSurfaceVisible`) |
| trạng thái mở Thí nghiệm | `labOpen` — cục bộ trong `AlgorithmWorkspace`, KHÔNG vào store |
| chấm thao tác | `module.predict.check` — **bên chấm DUY NHẤT** |
| kết quả chấm | `store.prediction` (tách khỏi `active.state`) |
| hit target sân khấu dãy | `components/ArrayView.tsx` — chỉ pointer drag, `role="img"` |
| topology mạng + định tuyến | `domains/network/model.ts` (`bfsRoute`, `buildSteps`) |

## 6. Tuyên bố được phép

Được nói: hệ chạy trọn lượt canonical mà không cần học sinh trả lời; thao tác
được engine tất định chấm; sửa mô hình có ràng buộc thì engine tính lại và hệ
quả hiện ra. **Không** được nói gì về kết quả học tập —
`LEARNER_IMPACT_NOT_EVALUATED`, `CURRICULUM_SUPPORT_PARTIAL`.
