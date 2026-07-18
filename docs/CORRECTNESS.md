# CORRECTNESS.md — Audit tính đúng đắn & nguyên tắc giáo dục (M7.14C)

Tài liệu này là kết quả **Simulation Correctness Audit** (M7.14C) và là nơi ghi
các nguyên tắc ràng buộc mọi milestone sau. Khi code và tài liệu này lệch nhau,
sửa một trong hai — không được để lệch im lặng.

Bối cảnh: một bài hình học phức tạp (chân đường cao, đường vuông góc, giao điểm,
đường tròn ngoại tiếp, giao điểm thứ hai, quỹ tích) từng được hệ render bằng
node/edge với **tọa độ do LLM đoán** — hình "nhìn có vẻ đúng" nhưng sai bản chất:
kéo M thì E/F/P đứng yên. Đây là vi phạm R0 ở tầng ngữ nghĩa.

---

## 1. Nguyên tắc nền (đã chốt)

1. **Canonical simulation phải đúng hoặc capability_gap.** Mô phỏng hệ thống
   sinh ra phải đúng theo deterministic rules/capabilities; engine chưa đủ năng
   lực thì từ chối trung thực — **không dựng xấp xỉ rồi giả vờ đúng**.
2. **Learner action được phép sai.** Thao tác/chỉnh sửa của học sinh có thể sai;
   nếu trạng thái sai vẫn có ý nghĩa học tập thì không nhất thiết reject.
3. **Chỉ deterministic engine/rule mới có quyền xác định đúng/sai.**
4. **Không có rule → `unsupported_to_verify`** — không phán đúng/sai giả tạo.
5. **Feedback là state/result data, không phải hội thoại chatbot.**
6. **LLM không bao giờ là judge correctness.** LLM chỉ trích xuất/phân loại/
   điền config/đề xuất patch — mọi phán quyết đúng-sai thuộc engine.

Một câu: *hệ mô phỏng thì đúng, học sinh thì được sai — và chỉ engine mới có
quyền nói học sinh sai ở đâu.*

## 2. Hai trục tách bạch: canonical vs learner

| | Canonical simulation | Learner action / edit |
|---|---|---|
| Ai tạo | Pipeline (compose/reuse) hoặc patch đã validate | Học sinh (drag, toggle, what-if, edit) |
| Được sai không | **Không** — đúng hoặc capability_gap | **Được** — sai là cơ hội học |
| Ai phán | Validator + engine tất định | Engine, và CHỈ khi có rule tất định |
| Sai thì sao | Từ chối/gap, không render | Giữ thành trạng thái/nhánh + feedback nếu có rule |

**Precedent kiến trúc:** what-if branch của domain algorithm
(`frontend/src/simulations/domains/algorithm/index.ts`) — học sinh đổi chỗ hai
phần tử ("sai" so với thuật toán chuẩn), hệ không chặn: engine chạy lại tất
định trên dãy đã sửa, kết quả sống trong `state.branch`, dòng chính (trace
canonical) bất khả xâm phạm, `exit_branch` quay về. Generic experimental branch
tương lai theo đúng khuôn này: **branch chỉ có giá trị khi engine tính được hậu
quả** — chưa có rule thì chưa có branch, không "giả vờ biết".

## 3. Taxonomy kết quả patch/edit (PatchResult) — TÁCH với interaction feedback

Cho **patch/edit** (đổi cấu trúc spec):

- `valid` — patch áp được, spec mới qua đủ validate → rebuild.
- `structurally_invalid` — id trùng, tham chiếu treo, chu trình parent, vượt
  limit, type ngoài manifest… → **hard reject**, spec hiện tại nguyên vẹn.
- `unsupported_to_verify` — yêu cầu cần năng lực hệ chưa có (vd "thêm chân
  đường cao"): từ chối **nói thật lý do**, không đoán tọa độ, không phán hộ.
- `invalid_with_feedback` — *reserved*: patch hợp lệ cấu trúc nhưng vi phạm một
  rule NGỮ NGHĨA mà engine CÓ (chưa có producer nào ở M7.14; sẽ có khi M7.15
  đem geometry constraints về).

Cho **runtime interaction** (không đổi cấu trúc): dùng kênh riêng
`InteractionFeedback` trong state — KHÔNG trộn với PatchResult. Ví dụ duy nhất
ở M7.14: kéo chạm biên `bounds` → feedback *"đối tượng chỉ di chuyển được trong
vùng tương tác cho phép"*. **Cấm suy diễn ngữ nghĩa chưa có**: bounds là hộp do
spec khai, KHÔNG phải "đoạn BC" — chừng nào chưa có geometry constraint, message
không được nhắc tới quan hệ hình học.

Ví dụ tương lai (M7.15, khi có projection/perpendicular rule):
- Học sinh đặt D trên BC nhưng AD chưa vuông góc BC → `invalid_with_feedback`:
  "Điểm D đang nằm trên BC, nhưng AD chưa vuông góc với BC. Vì vậy D chưa phải
  là chân đường cao." (engine đo được nên mới được nói).
- Kéo M ra ngoài đoạn BC (khi có on-segment constraint) → feedback tương ứng.

## 4. Ba luật chống trượt thành tutor/chatbot

1. **Feedback là dẫn xuất của rule, không phải văn của LLM.** Message sinh từ
   rule bị vi phạm (rule → chuỗi tiếng Việt cố định trong engine), không gọi
   mạng, không sinh văn tự do.
2. **Feedback là field của state, không phải lượt hội thoại.** Render trong
   workspace/inspector; không turn-taking, không lịch sử chat, không "AI nhận
   xét bài làm".
3. **`/api/explain` là bề mặt Q&A LLM duy nhất** — đọc snapshot state thật để
   giải thích, không phán xét, không điều khiển mô phỏng. Không thêm endpoint
   hội thoại.

## 5. Phân loại A/B/C toàn hệ (audit M7.14C)

**A — Deterministically correct** (engine tự tính kết quả):

| Case | Source of truth | Engine tính |
|---|---|---|
| algorithm.* (8 id: find_max/find_min/sum_if/count_if/linear_search/binary_search/bubble_sort/insertion_sort) | dữ liệu đề (input) | toàn bộ trace/steps/kết quả/what-if (`core/algorithms.ts`) |
| logic.and_gate | trạng thái toggle | bảng chân trị |
| binary.decimal_to_binary | decimal/bit toggle | bits ⇄ decimal (`bitsOf`/`decimalOf`) |
| network.packet_routing | topology từ đề | **route = BFS tất định** + steps (không từ LLM) |
| generic boolean/weighted_sum | giá trị khởi tạo | giá trị dẫn xuất lan truyền đến ổn định |
| cơ học timeline/reveal/move/drag | spec | tích lũy visibility, hops, clamp/snap/visible-gating |

**B — Structurally correct** (đúng như đề mô tả, không cần solver):

- Trang web/tài liệu structural (container/heading/paragraph/text — layout engine).
- Dựng điểm/đoạn **được nêu tên tường minh** (tam giác ABC từng bước).
- Điểm kéo tự do (draggable free points) — vị trí engine-owned, không ràng buộc
  ngữ nghĩa nào bị giả mạo.
- `move_along_path` với waypoint tường minh. *Giới hạn đã biết (giữ có chủ
  đích):* validator không bắt path phải đi theo edge tồn tại — waypoint không
  cần cạnh là hợp lệ (vd "vật đi qua 4 điểm A→B→C→D"); bài routing thật được
  bảo vệ bởi specialized BFS + classify.

**C — Potentially misleading → capability_gap** (cấm render xấp xỉ):

Vai trò gap trong taxonomy (không primitive nào cover — `known_gap_roles()`):
`geometric_projection`, `geometric_perpendicular`, `geometric_intersection`,
`geometric_circle`, `geometric_locus`, `numeric_threshold`,
`continuous_motion`, `arbitrary_algorithm`.

Cơ chế thực thi (máy sẵn từ M7.11, M7.14C nạp vai trò + sửa một bug thiết kế):
analyze gắn vai trò → `build_representation_plan` → vai trò không cover được →
**capability_gap chặn ĐƯỜNG GENERIC**. Classify vẫn chạy: bài được route về
mô-đun CHUYÊN BIỆT (có engine riêng, không dùng DSL) đi tiếp bình thường —
gap của DSL không được vạ lây specialized (bug lộ ra live: "tính tổng các số
lớn hơn 4" bị gắn `numeric_threshold` oan suýt chặn `algorithm.sum_if`).
Classify chọn generic hoặc từ chối → trả `capability_gap`; simulate và pattern
reuse tuyệt đối không chạy cho các đề này. Cổng hai:
`check_semantic_compatibility` trong stage simulate (chỉ generic). Phụ thuộc
trung thực: việc GẮN vai trò là LLM analyze — khóa hai chiều bằng eval (bài
dẫn xuất phải gap; bài tường minh/specialized không được gap oan) trong
`tests/test_capability_boundary.py` + dataset live.

## 6. Giới hạn tuyên bố của node/edge generic (chính sách)

node/edge generic **chỉ đủ** cho: cấu trúc dạng đồ thị; dựng điểm/đoạn đơn
giản tường minh; reveal các object khai báo; điểm kéo tự do.

node/edge generic **KHÔNG đủ** cho: chân đường cao; giao điểm; vuông góc dẫn
xuất; tiếp tuyến; đường tròn ngoại tiếp; quỹ tích; giao điểm thứ hai;
hình học kiểu chứng minh. Đề cần các quan hệ đó khi DSL chưa có solver →
`capability_gap`. **Không dùng tọa độ LLM đoán để giả các quan hệ này** — kể cả
qua patch/edit (xem §3, `unsupported_to_verify`).

## 7. Chính sách kiểm thử: offline-first, live là opt-in (M7.14T)

Correctness guard chỉ có giá trị nếu **chạy được thường xuyên mà không đốt
quota**. Vì vậy:

- `pytest` và `vitest` **luôn = 0 API call thật**. Guard nằm ở BIÊN MẠNG
  (`backend/conftest.py` patch transport httpx; `frontend/src/test-setup.ts`
  stub `fetch`), nên **suite xanh ⇔ không có call nào** — quên mock là đỏ ngay,
  không âm thầm gọi thật. Guard cũng gỡ `GEMINI_API_KEY` khỏi env (backend/.env
  được `load_dotenv` nạp lúc import → key thật vốn nằm sẵn trong tiến trình test).
- `live.py` **bắt buộc `ALLOW_LIVE_AI=1`**, có `--suite smoke|full|boundary` và
  ngân sách `--max-cases/--max-api-calls/--max-retries`; report in số request
  thật, retry, transient 429/5xx, và lý do dừng nếu chạm trần.
- Khi nào tiêu call live: UI/CSS/viewport → không cần; engine/validator tất định
  → offline trước; prompt/schema/classifier → smoke; kết thúc milestone hoặc lấy
  số liệu → full. **Không chạy full theo thói quen.**

Metric `gap_gate_recall` (M7.14T) đo **chính capability gate** ở §5 bằng
`build_representation_plan` — chạy SONG SONG với các metric cũ (được tính từ
classify), nên số liệu lịch sử vẫn so sánh được. Trước M7.14T, benchmark **không
hề đo** cái gate này: `unsupported_recall` khi đó phản ánh classify tự từ chối.

## 8. Trạng thái known-gap & lộ trình

- `numeric_threshold` ("ít nhất 2 trong 3"): unsupported đúng — muốn support
  thật thì thêm rule threshold tất định vào DSL (quyết định riêng, ngoài M7.14).
- `continuous_motion` (quỹ đạo): unsupported đúng.
- `arbitrary_algorithm` (thuật toán tự nghĩ): unsupported đúng.
- `geometric_*`: unsupported đúng cho tới **M7.15 — Minimal Constraint-Aware
  Geometry** (projection/perpendicular/intersection/circle như rule tất định);
  khi đó `invalid_with_feedback` mới có producer thật và generic experimental
  branch mới có nền để làm.

## 9. Chính sách normalize-not-refuse của binary_search

Đề cho dãy **chưa sắp** cho `binary_search` không bị refuse: server
(`validate_algorithm_config`) tự sắp dãy tất định trước khi phát config, **labels
đi theo giá trị** (giữ liên kết tên↔số), và gắn chú thích sư phạm ("Dãy đã được
sắp xếp trước — tìm kiếm nhị phân chỉ chạy trên dãy có thứ tự") vào `notes` thay
vì âm thầm sửa. Trace của engine (BE lẫn FE) chạy trên dãy **đã normalize**, không
phải dãy gốc trong đề. Khoá bằng `backend/tests/test_algo_entry_policy_locks.py`
(4 proof: normalize tất định, label giữ liên kết, annotation tồn tại, idempotent)
và `frontend/.../algorithm/binary-normalized.test.ts` (proof thứ tư: trace chạy
trên normalized input).
