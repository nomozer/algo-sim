# M17 — Quyết định phạm vi family

## Quyết định: **`FREEZE_AT_11_FAMILIES`**

Khoá catalog ở **11 family / 22 target**. Không mở family thứ 12, không thêm
target thứ 23.

## Vì sao không phải `ADD_ONE_FINAL_CAPABILITY`

§12B đòi một khoảng trống thoả **đồng thời** bảy điều kiện. Điều kiện đầu tiên đã
trượt: **không tìm được khoảng trống chương trình nào có neo trong nguồn hiện
có mà family hiện tại không biểu diễn được.**

Ba family bị chấm `NEEDS_REVIEW` (`tree_traversal`,
`relational_table_query`, `bounded_control_flow`) **không** phải khoảng trống năng
lực — chúng đã ship, có engine tất định, có test, có neo bài SGK. Cái chúng thiếu
là **siêu dữ liệu sư phạm**: chưa case nào khai `learning_objective`. Vá bằng cách
thêm eval case qua `check_admission` — rẻ, có cổng, đúng kiến trúc — và **thêm
family sẽ không sửa được điều đó**, chỉ làm catalog to hơn.

Điều kiện 5 ("tạo giá trị luận văn rõ, không chỉ tăng catalog") cũng trượt: bốn
năng lực đại diện đã phủ **đủ bốn kiểu tương tác** và **cả ba mức thẩm quyền kết
quả**, nên năng lực thứ 12 sẽ lặp lại một kiểu đã có bằng chứng.

## Vì sao không phải `FIX_EXISTING_ALIGNMENT_BEFORE_FREEZE`

§12C dành cho trường hợp có target cốt lõi **không thể pilot**: learner task bất
khả thi, interaction thực sự không đủ, hoặc UI dựng sai cơ chế. Không ca nào rơi
vào đó:

| Target | Interaction fit | Có chặn pilot không |
|---|---|---|
| `algorithm.bubble_sort` | SUFFICIENT | không |
| `network.protocol_encapsulation` | SUFFICIENT | không |
| `logic.boolean_dag` | SUFFICIENT | không |
| `binary.character_encoding` | SUFFICIENT_WITH_SCAFFOLD | không |

`binary.character_encoding` chỉ có `TIMELINE_CONTROL`, nhưng §12C **cấm** chọn C
chỉ vì một module dùng timeline. Mục tiêu của nó là *quan sát và giải thích một cơ
chế tất định*, và timeline phục vụ đúng mục tiêu đó; phần "giải thích" bù bằng
phiếu học tập theo §13 (ưu tiên scaffold hơn sửa engine/UI).

Hai rủi ro hiểu nhầm chưa xử lý (trục Z đọc thành khoảng cách; code point nhầm
với byte UTF-8) là **việc chú thích**, không phải lỗi cơ chế — không đủ để chặn.

## Vì sao `FREEZE` là đúng

1. Bốn năng lực đại diện phủ **PREDICTION_OR_WHAT_IF · MECHANISM_ACTION ·
   TIMELINE_CONTROL · 2D_AND_3D** — đã xác minh bằng hợp đồng module, không phải
   giả định.
2. Ba mức thẩm quyền đều có đại diện: **computation** (10 family) và
   **representation** (`generic.rule_scene`, giữ REPRESENTATION_ONLY).
3. Luận điểm cốt lõi của đề tài — *LLM đọc đề, engine tất định diễn hoạt* — đã có
   bằng chứng đủ tầng: REAL_SIMULATION, REAL_VISUAL, live NL integration (PARTIAL,
   đóng trung thực), và handoff live → engine → trình duyệt đối chiếu bằng hash.
4. Việc còn thiếu là **neo mục tiêu và bằng chứng người học**, không phải năng lực
   mô phỏng. Thêm family sẽ **trì hoãn** pilot mà không lấp được thứ đang thiếu.
5. `RULES §3c` xếp *"test/audit/tooling tăng mạnh nhưng học sinh không có chức năng
   mới"* là dấu hiệu đi quá đề tài. Mở family thứ 12 lúc này đúng vào dấu hiệu đó.

## Hệ quả

- `family_count = 11` · `target_count = 22` — **khoá**.
- Việc kế tiếp có giá trị cao nhất **không phải** viết code: bổ sung
  `learning_objective` cho 3 family `NEEDS_REVIEW` + 2 target
  `CURRICULUM_ANCHOR_INCOMPLETE`, rồi nhờ giáo viên rà.
- Mở family mới sau này phải là một checkpoint riêng có approval, với khoảng trống
  chương trình được chứng minh **trước**, không phải phát hiện sau khi đã xây.
