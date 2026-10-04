# POST_THESIS_BACKLOG.md — phần đã tách, chép nguyên văn

> Tách khỏi [`POST_THESIS_BACKLOG.md`](../POST_THESIS_BACKLOG.md) ở run `cuboid-final-review` (2026-10-05): ý tưởng của sản phẩm Tin học (quyết định thuật toán trên sân khấu, đợt nâng trải nghiệm toàn danh mục 23 target) — phạm vi đã bỏ từ 2026-08-24.
> Nguồn: `docs/POST_THESIS_BACKLOG.md` tại commit `4048ff83d14ad2a1fcd940d127590ca777dbc7cf` (blob `658666ee7dd92903911e2dda28e817973398cc74`). Mỗi khối dưới đây là **nguyên văn** (byte-identical)
> các dòng ghi trong chú thích của nó, theo thứ tự của bản gốc. Đây là lịch sử: không sửa, không thêm.
> Đường dẫn tương đối trong các khối viết cho thư mục `docs/`, nên từ `legacy/` chúng trỏ lệch một cấp
> (`README.md`). Kiểm lại: `docs/evaluation/geometry/runs/cuboid-final-review/diagnostics/split_history_cfr.py --verify`.

<!-- khối 1/2 · dòng 9–64 của bản gốc · two informatics-era idea sections · sha256 8085ff2339c71a4bb3cfea5b59d3cdc3b62018a265e791a8ceaf683274be0644 -->
## Cam kết cơ chế ở tầng sân khấu cho điểm quyết định thuật toán

**Ý tưởng.** Học sinh quyết định ngay trên sân khấu tại điểm quyết định của
thuật toán — bấm vào cột ứng viên để đặt làm max, hoặc bấm vào mốc max hiện tại
để giữ — thay vì chỉ dự đoán trong Thử thách.

**Vì sao đáng làm.** Soát toàn hệ (W12, 11 target họ `algorithm`) cho thấy
`module.apply` nhận `whatif_swap` (đổi thứ tự dãy vào) và `set_param` (đổi điều
kiện), nhưng **không có action nào cho chính quyết định của thuật toán**. Quyết
định ấy chỉ sống trong `predict`, tức chỉ trong Thử thách. Một
`commit_decision { decisionId, choice }` dẫn từ `decisionPointOf` sẽ đưa quyết
định về đúng chỗ của nó.

**Vì sao KHÔNG cần cho khoá luận.** Kiến trúc đề tài — LLM đề xuất spec có ràng
buộc → validate tất định → engine tất định sở hữu kết quả → biểu diễn tương tác
— đã được chứng minh bằng 11 target `INTERACTIVE_MODEL` và 9 công cụ tham số.
Chín target thuật toán được **mô tả trung thực** là công cụ tham số + trace +
thử thách tuỳ chọn; không có tuyên bố nào bị thổi phồng. Thêm hợp đồng mới lúc
này là một `SimAction` dùng chung chạm 11 target, cần nhánh sai tất định,
affordance, đường bàn phím và parity mẫu↔AI — một wave sản phẩm riêng, không
phải điều kiện để chứng nhận trung thực kiến trúc hiện có.

**Chủ sở hữu khi làm.** `domains/algorithm/decision.ts` (đã sở hữu ngữ nghĩa
quyết định) + `SimAction` + `ArrayView`.

## Đợt nâng chất lượng trải nghiệm toàn danh mục (quyết định 2026-08-16)

**Ý tưởng.** Một đợt rà soát sản phẩm quét cả danh mục: thống nhất họ cơ số và
họ thuật toán quanh "công cụ có ràng buộc" (F, G), luồng điều khiển (H), định
tuyến mạng dạy được việc CHỌN đường (I), đóng gói giao thức (J), truy vấn CSDL
(K), tải nhận thức của `web.style_model` (L), rồi chứng nhận bằng ma trận thị
giác **23 × 4 bề rộng × nhiều trạng thái** (P), teacher test 23/23 (Q) và rubric
10 tiêu chí × 23 target (R).

**Vì sao đáng làm.** Đó là con đường từ "kiến trúc đã chứng minh" tới "sản phẩm
dùng được trong lớp thật". Mỗi mục đều truy được về một quan sát cụ thể đã ghi
trong `STATUS_LEDGER`.

**Vì sao KHÔNG cần cho khoá luận.** Luận điểm của đề tài là **ranh giới R0**
(LLM đọc đề, engine tất định diễn hoạt) và hệ quả của nó (**đúng-hoặc-
`capability_gap`**) — không phải độ phủ, cũng không phải độ hoàn thiện UX.
Bằng chứng cho ranh giới ấy đã đủ: bất biến đánh số có test khoá, cổng năng lực
+ ca từ chối, 24 target / 12 family với conformance·ownership·parity = 0, và
W5A vừa chứng minh chi phí mở rộng là **một `SimSpec` + một dòng đăng ký**, còn
23 test đỏ lên là hệ tự đòi khai báo đủ chứ không phải phải sửa pipeline.
Ma trận 92 ảnh không làm lập luận ấy mạnh thêm; **4–6 target đại diện cho bốn
archetype, chụp trước/sau kèm phân tích** là mức bằng chứng đúng cho một khoá
luận, và `COVERAGE.md §"CẤM tuyên bố"` vốn đã chặn mọi cách đọc con số thành
tuyên bố phủ chương trình.

**Vẫn thuộc phạm vi lõi, KHÔNG hoãn:** ngữ nghĩa Khám phá ≠ Trace ở họ logic
(E), rà `generic.rule_scene` bị dùng sai ngữ nghĩa (M), và nhất quán
trạng-thái ↔ chữ trên toàn danh mục (N). Ba mục này là **tính đúng**, không phải
polish: màn hình nói sai một giá trị engine đã biết thì chính luận điểm
"đúng-hoặc-từ-chối" bị phản chứng ngay trên bề mặt.

<!-- hết khối 1 -->

<!-- khối 2/2 · dòng 72–72 của bản gốc · scope line of the informatics topic · sha256 1e7e454e049e22c9a30a6fd1ce8a34b16f229a713e75d890d174ae171f97d41a -->
- Môn học khác ngoài Tin học THPT — cổng phạm vi (W3) tồn tại để từ chối chúng.
<!-- hết khối 2 -->
