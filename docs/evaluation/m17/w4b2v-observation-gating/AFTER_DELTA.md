# W4B-2V Commit B — AFTER DELTA

Root cause đã sửa: **#1 `OBSERVATION_STATE_OWNED_BY_COMMITMENT_ZONE`**
`THESIS_SCOPE = T3` — biểu diễn mô phỏng sư phạm.

> Bản audit BEFORE (`docs/SIMULATION_VISUAL_LANGUAGE_AUDIT.md`, đóng băng tại
> `fe6b0d5`) **không bị sửa một dòng nào**. Đây là phần chênh lệch, chỉ ghi
> những target thực sự bị bản vá chạm tới.

## 1. Sự cố đã sửa

`SearchActionZone` sở hữu **hai trách nhiệm khác loại** trong cùng một
`<section>`, rồi `AlgorithmWorkspace` gác cả cây con bằng `commitmentVisible`:

| Nội dung | Loại | Trước | Sau |
|---|---|---|---|
| tiền đề "chỉ đúng khi dãy đã sắp" | quan sát | còn (W4B-2D đã cứu riêng) | còn |
| chip `Phần tử vị trí N` · `cần tìm X` · `vùng xét L–R` | **quan sát** | **MẤT khi cổng đóng** | **còn** |
| khối chi phí `đã so sánh · chưa xét · xấu nhất` | **quan sát** | **MẤT khi cổng đóng** | **còn** |
| quan hệ `105 = 189 ?` | **quan sát** | **MẤT khi cổng MỞ** *(dải nhân quả bị tắt bởi `!(search && commitmentVisible)`, mà vùng cam kết không mang `expression`)* | **còn ở cả hai** |
| lời nhắc · nút hành động · phản hồi | cam kết | ẩn khi cổng đóng | ẩn khi cổng đóng |

Hai chiều của **cùng một lỗi**: một dữ kiện quan sát bị buộc vào công tắc của
cổng. Chiều thứ hai (mở cổng làm mất quan hệ) chưa từng được ghi nhận trước
wave này — nó lộ ra khi phát biểu bất biến đơn điệu.

## 2. Thay đổi quyền sở hữu

| | trước | sau |
|---|---|---|
| trạng thái quan sát của bước tìm kiếm | `SearchActionZone` (bị gác) | **`SearchStateView`** — mới, **ngoài cổng** |
| quan hệ (`expression`) | `.decision-strip` ở `ui.tsx` (bị tắt khi cổng mở) | **`SearchStateView`** — chủ sở hữu duy nhất ở họ này |
| điều khiển cam kết | `SearchActionZone` | `SearchActionZone` — nay **chỉ** còn lời nhắc + nút + phản hồi |
| quyết định hiện/ẩn cam kết | `commitmentSurfaceVisible(policy, labOpen)` | **không đổi** |

Phân loại: **EXTRACT_SHARED trong phạm vi họ** — tách một component sẵn có thành
hai trách nhiệm, **không** dựng framework phổ quát. Không thêm nhánh theo
`algorithm_id`/`simulation_id`/nội dung đề.

## 3. Delta phân loại

| target | BEFORE | AFTER | lý do |
|---|---|---|---|
| `algorithm.linear_search` | `REPRESENTATION_GAP` | **`VISUAL_WITH_SHORT_CAPTION`** | chip vị trí/đích, quan hệ và **khối chi phí** — cơ chế đáng học của tìm tuần tự — nay đọc được ở Quan sát; vẫn cần một caption bước |
| `algorithm.binary_search` | `REPRESENTATION_GAP` | **`VISUAL_WITH_SHORT_CAPTION`** | vùng xét `L–R`, phần tử giữa, đích, quan hệ, tiền đề đều ở Quan sát. **Vẫn chưa** vẽ được tính *đã-sắp* — tiền đề còn là câu chữ (root cause #3, ngoài phạm vi) |
| `algorithm.selection_sort` | `REPRESENTATION_GAP` | **`REPRESENTATION_GAP`** *(không đổi)* | cùng khuyết tật cấu trúc ở `SortActionZone`, nhưng bài **chưa gác cổng** nên chưa mất gì. Không sửa: xem §4 |

Không target nào khác bị chạm. Chín `REPRESENTATION_GAP` còn lại giữ nguyên
phân loại — bản vá này **không** nhằm vào chúng.

## 4. `SortActionZone` — DEFERRED_TO_W4B2E_WITH_KNOWN_ROOT_CAUSE

`SortActionZone` **có cùng khuyết tật cấu trúc** (`.sort-state` nằm chung
`<section>` với nút và phản hồi). Nhưng cả ba bài sắp xếp hiện KHÔNG mất gì:
`bubble_sort`/`selection_sort` chưa gác cổng, còn `insertion_sort` đã gác mà vẫn
`VISUAL_SELF_SUFFICIENT` vì khay HELD/GAP nằm trên **sân khấu**, ngoài zone.

Vì thế tách nó lúc này là refactor **không** sửa lỗi nào đang xảy ra, và điều
kiện "chứng minh 0 thay đổi hành vi" sẽ tốn hơn giá trị nó mang lại trong wave
này. Ghi lại thành nợ có tên: **khi W4B-2E gác `selection_sort`, phải tách
trách nhiệm TRƯỚC khi thêm cờ, nếu không sẽ tái diễn đúng hồi quy W4B-2D.**

## 5. Bằng chứng

**Bất biến mới** — `simulations/observation-preservation.test.tsx`
(`CORE_OBSERVATION_STATE_PRESERVED_UNDER_GATING`).

`labOpen` là `useState` cục bộ nên SSR không mở được cổng
(`ARCHITECTURE_MAP §8` #13). Thay vì giả lập, bất biến được chứng minh **theo
cấu trúc** — mạnh hơn, vì nó đúng với mọi state chứ không riêng fixture:

1. mọi probe cơ chế lõi nằm trong phần **không** bị gác;
2. phần **bị** gác không chứa probe lõi nào;
   ⇒ mở cổng chỉ **thêm** quyền hành động, không thể dời hay lấy mất thông tin.

Probe suy từ chính state engine (`searchInteractionOf` + `decisionPointOf`),
không phải chuỗi viết tay: đích · phần tử đang xét · vị trí/vùng xét · quan hệ ·
chi phí · tiền đề.

Ngoại lệ có tên **`PRESENTATION_COPY_TRANSITION`**: teaser ↔ framing ↔ nhãn nút
↔ phản hồi được phép đổi khi mở/đóng cổng — chúng là lời mời và lời chấm, không
phải trạng thái cơ chế. Có test riêng khoá việc chúng **không** bị đưa vào tập
probe, để sau này không ai phải nới lỏng bất biến khi teaser đổi.

**Tiêm lỗi (đã chạy, không commit):**

| Lỗi tiêm | Kết quả |
|---|---|
| gác lại trạng thái quan sát (tái tạo đúng W4B-2D) | **ĐỎ** — *"linear_search: Quan sát mất «quan hệ đang xét»"* |
| lộ bề mặt cam kết ra Quan sát | **ĐỎ** — 4 test, gồm cả bất biến bề mặt cam kết sẵn có |
| khôi phục | **XANH** |

**Trình duyệt** (`browser/`, Vite mới, cổng 3000, `strictPort`):
`linear_search` · `binary_search` · `insertion_sort` — **54/54 PASS**,
`canonical_stable_across_ui_modes = true` cả ba, 0 rò đáp án.
Ảnh `linear_search-1-observe.png` cho thấy khối chi phí hiện khi Thí nghiệm
**đóng** — thứ trước wave này chỉ thấy được sau khi mở cổng.

**Responsive** `1366×768 · 1920×1080 · 768×900`: PASS.
Chồng lấp Explain+Experiment ở 768×900 vẫn là nợ vỏ dùng chung, **không** cản
bất biến này (đo được ở lượt trên).

## 6. Điều bản vá này KHÔNG làm

Giữ nguyên, đúng phạm vi đã chốt: `sum_if` (thiếu phóng chiếu biến tích luỹ) ·
`algorithm.scan` · `bounded_control_flow` · `binary.base_conversion` ·
`packet_routing` (vai trò đích) · `tree.traversal` (luật DFS) ·
`generic.rule_scene` · `database.relational_table_query` · trùng lặp kênh
thuyết minh · vẽ tính đã-sắp cho nhị phân · rollout họ Sort.

Không tuyên bố gì về kết quả học tập: `LEARNER_IMPACT_NOT_EVALUATED`,
`CURRICULUM_SUPPORT_PARTIAL`.
