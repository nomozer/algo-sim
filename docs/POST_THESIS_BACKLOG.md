# POST_THESIS_BACKLOG.md — ý tưởng đáng làm, **sau** khoá luận

> Danh sách này tồn tại để ý tưởng không bị mất mà sản phẩm vẫn có biên. Mỗi mục
> phải nói **vì sao nó không cần cho khoá luận** — nếu không nói được, nó thuộc
> phạm vi lõi chứ không thuộc đây.
>
> Khoá phạm vi ở `STATUS_LEDGER.md §0` là nguồn phán quyết.

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

## Các mục khác (ghi để không mất, không có kế hoạch)

- Mở rộng LMS: sổ điểm, điểm danh, thời khoá biểu, học phí — **NON-GOAL** theo
  khoá phạm vi; tầng lớp học cố ý dừng ở đăng nhập + lớp + giao bài + luyện tập
  + quan sát.
- Trình soạn thảo tự do (HTML/CSS/JS, thuật toán, cây, topology) — phá ranh giới
  "hiện vật có ràng buộc" vốn là điều khiến engine tất định phán được đúng/sai.
- Môn học khác ngoài Tin học THPT — cổng phạm vi (W3) tồn tại để từ chối chúng.
- Phân tích học tập nâng cao, cộng tác thời gian thực, hiệu ứng 3D mở rộng.
- Nghiên cứu đối chứng trên người học — đây là **giới hạn nghiên cứu**, không
  phải khiếm khuyết hiện thực; `LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên.
