# W13 — BỎ HÌNH THỨC HỎI-ĐÁP, GIỮ THAO TÁC

> Quyết định của chủ đề tài, 2026-08-17. Không phải "dời" như W4B-2U2 đã làm —
> lần này là **gỡ hẳn** năng lực `predict` khỏi sản phẩm.

## 0. Quyết định (đã chốt, không tự diễn giải lại)

1. **Dải dữ kiện cơ chế GIỮ LẠI**, bỏ giọng hỏi: `"172 > 165 ?"` → mệnh đề
   khẳng định. Và nó hiện **thường trực ở Quan sát**, không còn nấp sau cổng.
2. **`predict` gỡ hẳn khỏi 11 target** — không giữ mã chết.
3. **Bảng quan sát lớp học**: "số lần cam kết" → **số lần thí nghiệm**
   (`action_count` đã có sẵn, không cần cột mới).

## 1. Vì sao được phép làm (scope guard)

- Phân loại: **CORE** (`RULES §3b`) — đổi trực tiếp chức năng học sinh.
- **Bất biến #11 KHÔNG bị phá**: nó nói *ai* được phán đúng/sai (chỉ engine tất
  định), không nói *phải có* phán quyết. Bỏ phán quyết khỏi đường học sinh là
  hợp lệ; điều bị cấm là để LLM hay client phán.
- **Bất biến #27 vẫn đứng**: bảng quan sát chở trạng thái có cấu trúc, không có
  trường `verdict/correct/score`. Đổi `commitmentCount` → thao tác thật ra làm
  bất biến này *chặt hơn*.

## 2. Không target nào trống tay sau khi gỡ

Cả 9 bài thuật toán đã có `explore` → `apply` (không qua chấm):

| target | thao tác còn lại |
|---|---|
| bubble/insertion/selection_sort | tự đổi chỗ hai cột bất kì |
| binary_search | phá thứ tự đã sắp |
| find_max / find_min | đưa cột chưa duyệt vào vùng đã duyệt |
| linear_search | dời giá trị cần tìm |
| sum_if / count_if | đổi điều kiện lọc/đếm (kéo là trang trí ⇒ `mode: hidden`) |
| network.packet_routing | `explore` sẵn có |

Ngoại lệ **đã được quyết định từ trước**: `network.protocol_encapsulation` có
`apply: (s) => s`, nằm trong `KEEP_TRACE` với lý do cơ chế
(`experience-audit-w4b4a.test.ts`). Gỡ quiz ⇒ nó là trace thuần, đúng phán
quyết cũ, **không phải hạ cấp mới**.

## 3. Thứ tự thi hành (mỗi bước phải xanh trước khi sang bước sau)

**S1 — kiểu + store (gốc phụ thuộc).**
`simulations/types.ts` gỡ `PredictionCapability` + trường `predict`.
`state/store.ts` gỡ `prediction`, `submitPrediction`, `challengeOpen`,
`openChallenge/closeChallenge`.
⚠️ KHÔNG đụng `InteractionFeedback` của miền generic — đó là feedback theo rule
của engine (bất biến #11/#12), không phải quiz.

**S2 — vỏ.** `SimulationWorkspace.tsx` gỡ `challengeEntry`,
`challengeSurfaceVisible`, chỗ dựng `PredictionBar`. Xoá `PredictionBar.tsx`.

**S3 — ba vùng cam kết gộp làm một.** Bỏ nút + dòng phán quyết khỏi
`ScanActionZone`/`SearchActionZone`/`SortActionZone`. Còn lại cả ba đều là
*tiêu đề + chip dữ kiện + mệnh đề* ⇒ gộp thành **một** component dùng chung
(`MechanismFactStrip`), đúng luật reuse `RULES §2b`. `searchSceneRegions`
(vùng bấm trên sân khấu) là bề mặt cam kết ⇒ gỡ theo.

**S4 — miền.** Gỡ khối `predict:` ở `domains/algorithm/index.ts`,
`domains/network/index.ts`, `domains/network/encap.ts`.
`decision.ts`: giữ `expression`/`facts`/`title`, bỏ `options`/`expectedId`/
`evidence`/`actions`. Đổi `expression` sang thể khẳng định.
`interaction-policy.ts`: `experimentGated` + `commitmentSurfaceVisible` +
`challengeEntryOf` hết lý do tồn tại; `toolAffordanceOpen` bỏ tham số
`challengeOpen` (công cụ dùng được ngay, không còn câu hỏi nào để nhường chỗ).

**S5 — lớp học.** `PracticeReporter` bỏ `commitmentCount`/`challengeOpen`, báo
`actionCount`. `classroom_router.py` bỏ hai trường tương ứng.
`classroom_models.py` bỏ hai cột ⇒ **bắt buộc** `alembic revision
--autogenerate` + `upgrade head` (bất biến #19, `test_migration_drift.py`).

**S6 — test.** Viết lại/gỡ: `dequiz-observe`, `prediction`,
`interaction-family-w1/w2/sorting-w3b`, `m8-acceptance`, `scan-semantics-w3b1`,
`experiment-gate-w4b2b`, `secondary-actions-w4b2w`, `target-certification`,
`experience-*`, `test_classroom_api.py`. Thêm guard mới: **không bề mặt học sinh
nào phát ngôn đúng/sai** (quét chuỗi `Chính xác`/`Chưa đúng`/`verdict`).

**S7 — tài liệu + bằng chứng.** `ARCHITECTURE_MAP` (#11 ghi rõ phạm vi, #27),
`CORRECTNESS §4`, `SIMULATION_SURFACE_COMPOSITION_CONTRACT §57-59/§96/§146`,
`STATUS_LEDGER`, `CURRENT_STATE`, `CODE_INDEX`. Bỏ `quiz-dominance-w12.mjs`
(câu hỏi nó đo không còn tồn tại). Sinh lại bằng chứng: sửa mã ⇒ mọi artifact cũ
`STALE_SOURCE`, `assertFresh()` sẽ từ chối.

## 3b. TIẾN ĐỘ (cập nhật 2026-08-17, phiên 1)

**Cây đang ĐỎ giữa wave** — `tsc -b` chưa xanh. Đây là trạng thái đã biết, không
phải hỏng ngoài ý muốn: `predict` đã gỡ ở gốc (kiểu + store + 3 miền) nên mọi
consumer chưa sửa đều báo lỗi, và chính danh sách lỗi đó là bảng công việc.

XONG:
- **S1** `simulations/types.ts` (gỡ `PredictionCapability`/`PredictionResult`/
  `PredictionChallenge`/`PredictionOption`/`PredictionVerdict` + trường
  `predict`), `state/store.ts` (gỡ `prediction`, `submitPrediction`,
  `clearPrediction`, `challengeOpen`, `setChallengeOpen`).
- **S2** xoá `components/PredictionBar.tsx`; `SimulationWorkspace.tsx` gỡ chỗ
  dựng + `challengeSurfaceVisible`/`challengeEntry`/`DEFAULT_CHALLENGE`;
  `SimulationControls.tsx` còn đúng MỘT cửa (Khám phá).
- **S4 (một phần)** gỡ khối `predict` ở `domains/algorithm/index.ts`,
  `domains/network/index.ts`, `domains/network/encap.ts` + import chết.
- **S5 (một phần)** `PracticeReporter.tsx` báo `actionCount`, hết
  `commitmentCount`/`challengeOpen`.

### Phiên 2 — thêm phần này (2026-08-18)

Hai việc ĐỘC LẬP đã tách ra commit riêng để không nằm chung đống với wave dở:
`5c194cd` (thanh cuộn `color-scheme: light`) · `c7b796f` (guard chặn Bash ghi
mã nguồn). Cả hai xanh, có bằng chứng. W13 nay đứng một mình, hoàn nguyên được
mà không mất hai thứ đó.

XONG THÊM:
- `tool-affordance.ts` — `toolAffordanceOpen` co lại còn `!busy`. W12 §6
  (Policy B) tự tiêu: không còn chế độ nào phải mở trước mới có công cụ.
- `interaction-policy.ts` — `whatIfDragAllowed` bỏ `answered`/`challengeOpen`;
  §15 ("hoãn kéo khi có cam kết đang chờ") hết đối tượng, còn lại R3.3a.
- `domains/algorithm/ui.tsx` — gỡ `prediction`/`submitPrediction`, gỡ khay
  `.experiment-tool` kèm nút `×`, gỡ `sceneRegions`/`onRegionAct`, gộp hai hàng
  `.hint` thành một. Dải dữ kiện nay **thường trực**, không sau cổng.
- `domains/network/ui.tsx` — `editable = toolAffordanceOpen({ busy })`.
- `components/SortActionZone.tsx` — thành DẢI DỮ KIỆN thuần: còn tiêu đề + chip
  + mệnh đề; hết nút, hết dòng mời, hết phán quyết.

CÒN LẠI, theo thứ tự:
1. `ScanActionZone.tsx` + `SearchActionZone.tsx` — cùng phép rút như
   `SortActionZone`. **Rồi mới quyết** có gộp ba thành một `MechanismFactStrip`
   không: rút xong mới nhìn được hình dạng thật của chúng, gộp trước là
   refactor theo phỏng đoán.
2. `domains/algorithm/ui.tsx` — dọn import chết (`searchSceneRegions`,
   `commitmentSurfaceKind`, `commitmentSurfaceVisible`, `IconInfo`,
   `exploreOpen`).
3. `state/classroom.ts` — `ProgressBody` bỏ `challengeOpen`/`commitmentCount`.
4. `decision.ts` — bỏ `options`/`expectedId`/`evidence`/`actions`; đổi
   `expression` sang thể khẳng định (`"172 > 165 ?"` → `"172 > 165"`).
   ⚠️ Đây là quyết định #1 của chủ đề tài, đừng bỏ sót.
5. `interaction-policy.ts` — `commitmentSurfaceVisible`/`commitmentSurfaceKind`/
   `challengeEntryOf`/`experimentGated` nay không ai gọi: xoá, đừng để mã chết.
6. **S5 backend** — `classroom_router.py` + `classroom_models.py` bỏ
   `commitment_count`/`challenge_open` + **Alembic revision**.
7. **S6** 27 file test (danh sách lấy bằng `npx tsc -b`), thêm guard `no-verdict`.
8. **S7** tài liệu + sinh lại bằng chứng. Dòng cụ thể phải sửa, đã tìm được:
   `SIMULATION_SURFACE_COMPOSITION_CONTRACT.md` §CHALLENGE ghi *"Năng lực
   `predict` không được xoá — nó là bất biến #11"*. Câu này vừa **chặn đúng
   quyết định W13**, vừa **trích sai #11** (#11 nói CHỈ ENGINE mới được phán
   đúng/sai, không nói phải CÓ phán quyết). Sửa cả hai lỗi cùng lúc.

## 4. Rủi ro đã biết

- **S3 dễ đẻ hồi quy bố cục**: ba zone đang có `chrome: panel|tool`; gộp mà
  quên `.action-zone.is-tool` thì dải rơi ra ngoài `.experiment-tool`.
  `styles/tokens.test.ts` không bắt được lỗi này — phải đo bằng `audit-layout`.
- **S5 chạm DB**: quên Alembic ⇒ `test_migration_drift.py` đỏ ở suite mặc định.
- Guard SSR: `renderToString` chỉ đi qua trạng thái đầu
  (`ARCHITECTURE_MAP §8` #8/#13) — test "không còn nút" phải gọi **hàm thuần**,
  không dựng `<SimulationWorkspace/>`, nếu không sẽ xanh vì màn hình rỗng.
