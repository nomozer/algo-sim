# CORRECTNESS.md — phần đã tách, chép nguyên văn

> Tách khỏi [`CORRECTNESS.md`](../CORRECTNESS.md) ở run `cuboid-final-review` (2026-10-05): tiền lệ, taxonomy, phân loại và chính sách của các miền Tin học đã gỡ; nguyên tắc chung (§1, §1a, §2, §2b, §4, §7) ở lại.
> Nguồn: `docs/CORRECTNESS.md` tại commit `4048ff83d14ad2a1fcd940d127590ca777dbc7cf` (blob `f6ece816a02e98684e51950ea40769163e17767b`). Mỗi khối dưới đây là **nguyên văn** (byte-identical)
> các dòng ghi trong chú thích của nó, theo thứ tự của bản gốc. Đây là lịch sử: không sửa, không thêm.
> Đường dẫn tương đối trong các khối viết cho thư mục `docs/`, nên từ `legacy/` chúng trỏ lệch một cấp
> (`README.md`). Kiểm lại: `docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --verify`.

<!-- khối 1/6 · dòng 60–67 của bản gốc · §2 precedent: what-if branch of the removed algorithm domain · sha256 b664c8f97b46c96721ed611827682c53d22bb1ad0506567b02fad8398cb38447 -->
**Precedent kiến trúc:** what-if branch của domain algorithm
(`frontend/src/simulations/domains/algorithm/index.ts`) — học sinh đổi chỗ hai
phần tử ("sai" so với thuật toán chuẩn), hệ không chặn: engine chạy lại tất
định trên dãy đã sửa, kết quả sống trong `state.branch`, dòng chính (trace
canonical) bất khả xâm phạm, `exit_branch` quay về. Generic experimental branch
tương lai theo đúng khuôn này: **branch chỉ có giá trị khi engine tính được hậu
quả** — chưa có rule thì chưa có branch, không "giả vờ biết".

<!-- hết khối 1 -->

<!-- khối 2/6 · dòng 208–233 của bản gốc · §3 PatchResult taxonomy of the removed generic DSL edit path · sha256 d2568bca0630984c4e5eff603db909353b4f8349fcaab8147ba3ca9b06f299f6 -->
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

<!-- hết khối 2 -->

<!-- khối 3/6 · dòng 246–300 của bản gốc · §5 A/B/C classification and §6 node/edge claims of the informatics system · sha256 4b0113e520247edea612af532b80a86a8a290bb62b05afd676f67f3652a47408 -->
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

<!-- hết khối 3 -->

<!-- khối 4/6 · dòng 311–317 của bản gốc · §7: the removed live.py runner and its suites · sha256 6980e4f34c186747d2176ebec8824f3d200800960cc777e61c8a0cc461a077a3 -->
- `live.py` **bắt buộc `ALLOW_LIVE_AI=1`**, có `--suite smoke|full|boundary` và
  ngân sách `--max-cases/--max-api-calls/--max-retries`; report in số request
  thật, retry, transient 429/5xx, và lý do dừng nếu chạm trần.
- Khi nào tiêu call live: UI/CSS/viewport → không cần; engine/validator tất định
  → offline trước; prompt/schema/classifier → smoke; kết thúc milestone hoặc lấy
  số liệu → full. **Không chạy full theo thói quen.**

<!-- hết khối 4 -->

<!-- khối 5/6 · dòng 318–322 của bản gốc · §7: gap_gate_recall metric of the removed capability gate · sha256 9c797aea3797186667341445eb68c5054ca6ec99770c2967b8bbe8e9051b1057 -->
Metric `gap_gate_recall` (M7.14T) đo **chính capability gate** ở §5 bằng
`build_representation_plan` — chạy SONG SONG với các metric cũ (được tính từ
classify), nên số liệu lịch sử vẫn so sánh được. Trước M7.14T, benchmark **không
hề đo** cái gate này: `unsupported_recall` khi đó phản ánh classify tự từ chối.

<!-- hết khối 5 -->

<!-- khối 6/6 · dòng 323–344 của bản gốc · §8 known-gap roadmap and §9 binary_search policy · sha256 cc20d892ce4bfaa78de76c61312482ac8ab7262c1d46dc179ad6910ed146c7eb -->
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
<!-- hết khối 6 -->
