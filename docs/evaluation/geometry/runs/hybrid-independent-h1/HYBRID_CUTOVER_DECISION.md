# Báo Cáo Tổng Hợp & Quyết Định Chuyển Đổi Kiến Trúc Hybrid (`HYBRID_CUTOVER_DECISION`)

**Run:** `hybrid-independent-h1` · **Master Epic:** `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · **Nhiệm vụ:** `C28` · **Phạm vi:** `BACKEND_ONLY` (`frontend/**` và `backend/app/**`: `0` thay đổi) · **Ngày lập:** `2026-11-03`.

> [!IMPORTANT]
> **Phán quyết hiện hành dựa trên hợp đồng nghiệm thu (`0` lượt gọi Gemini live trong phiên C28):**
> - `EXECUTION_GATE_STATUS` = **`BLOCKED_EXTERNAL_AUTHOR`** (chưa có tệp `h1-independent-corpus.json` trên đĩa; tuân thủ C28 §III & §XIII không tự sáng tác đề và không tạo báo cáo kết quả giả).
> - `H1_AUTHORING_INDEPENDENCE` = **`NOT_ESTABLISHED`**.
> - `H1_MEASUREMENT` = **`NOT_MEASURED`**.
> - `PAIRED_LIVE_EVALUATION_COMPLETE` = **`NO`**.
> - `LIVE_GEMINI_QUALITY_VALIDATED` = **`NO`** (dữ liệu live hiện có là C26 trên `K-1/S-2/R-1` đã dùng trong quá trình phát triển).
> - `PEDAGOGICAL_HUMAN_VALIDATION` = **`NOT_EVALUATED`** (`H-1` loại trừ bài chỉ dựng hình / bài chứng minh và không thay thế đánh giá của giáo viên/học sinh).
> - `HYBRID_CUTOVER_DECISION` = **`HYBRID_CUTOVER_BLOCKED`** (`DEFAULT_MODE = "LLM_ONLY"` và `HYBRID_ROUTE_MODE = "off"` giữ nguyên).
> - `LEGACY_REMOVAL_DECISION` = **`LEGACY_REMOVAL_BLOCKED`** (`LLM_ONLY` chưa được phép gỡ bỏ).

*(Tuân thủ C28 §X & §XIII: Tệp `H1_PAIRED_LIVE_EVALUATION_REPORT.md` **không được tạo** khi phép đo live trên `H-1` chưa diễn ra; không tạo báo cáo kết quả giả hoặc bảng trống).*

---

## 1. Trả Lời Trực Tiếp 6 Câu Hỏi Cốt Lõi Của C27 (§0)

1. **Hybrid có thực sự hiểu và xử lý được đề toán hình học tiếng Việt chưa từng dùng để phát triển không?**
   - **Chưa được chứng minh trên tập độc lập mù (`NOT_MEASURED` trên `H-1`).** Trên tập hồi quy live C26 (`70` đề `K-1/S-2/R-1` trên `gemini-2.5-flash`), `HYBRID` phục vụ đúng toán học `37 / 41` đề khả giải (`90.24%`) và giảm false refusal từ `20 / 39` xuống `2 / 39`, nhưng `K-1/S-2/R-1` đã nhiễm phát triển nên bắt buộc phải kiểm chứng trên 60 đề `H-1` độc lập.
2. **Hybrid có đúng toán học và an toàn hơn hoặc ít nhất đáp ứng được tiêu chí thay thế `LLM_ONLY` không?**
   - **Về an toàn toán học trên dữ liệu đã đo:** `HYBRID` đạt **`0 / 70` ca `wrong_served`** (`37 / 37` ca phục vụ khớp chính xác biểu thức căn thức/$\pi$ kèm chứng chỉ exact kernel, `0 / 29` bài âm tính bị phục vụ). Tuy nhiên, **chưa đủ điều kiện thay thế `LLM_ONLY`** vì phép đo bắt cặp trực tiếp trên cùng 60 đề `H-1` độc lập chưa được thực thi (Tiêu chí `0..7` của Hợp đồng §7 chưa thể đánh giá).
3. **Hybrid có đáp ứng yêu cầu cấu trúc mô phỏng và dựng hình không?**
   - **Có về mặt hợp đồng cấu trúc `Scene3D` trong phạm vi `geometry-functions/32` đã đăng ký, kèm ranh giới sư phạm minh bạch (C28 §IX).** Adapter `/4` xuất đầy đủ hợp đồng `scene3d` (đỉnh, cạnh, mặt, giao tuyến/thiết diện có giải thích bước dựng, đại lượng mục tiêu và chứng chỉ kiểm chứng), giữ nguyên tương thích 100% với frontend hiện hữu (`41 / 41` preview fixtures khóa cứng, Full T3 `16,698` pytest + `1,502` vitest PASS tại `180db769`), và bộ chạy bắt cặp kiểm toán tự động 6 bất biến `audit_scene_contract()` trên mọi ca `SERVED` của cả hai nhánh. Tuy nhiên, `H-1` loại trừ bài chỉ dựng hình / bài chứng minh nên **không chứng minh chất lượng sư phạm đã được con người kiểm chứng** (`PEDAGOGICAL_HUMAN_VALIDATION = NOT_EVALUATED`). Với câu gộp *"Xác định thiết diện… và tính diện tích"*, chính sách **P1** (`h1-section-determination-equivalence/1`) xác nhận `HYBRID` xuất đồng thời cả đối tượng mô phỏng `construct_plane_section` và đại lượng `area` đúng hợp đồng sản phẩm.
4. **Chi phí, token và độ trễ của Hybrid so với `LLM_ONLY` như thế nào?**
   - **So sánh bắt cặp trực tiếp trên `H-1` đang ở trạng thái `NOT_MEASURED`;** trên telemetry thực tế hiện có, `HYBRID` tốn đúng `1` lời gọi trích xuất/bài qua cổng miền (trung bình `4,295` tokens/call, **`\$0.00507`/call**, độ trễ trung vị **`7.81 s`/bài** trên C26), trong khi `LLM_ONLY` cần chuỗi `1` lời gọi `semantic_analyze` + `1..3` lời gọi `semantic_program` tuần tự (ước tính **`~\$0.020 – \$0.026`/bài**). Kiểm định chính thức Tiêu chí 4 (latency) và Tiêu chí 5 (USD upper của `HYBRID` $\le$ USD lower của `LLM_ONLY`) sẽ được quyết định trên lượt chạy bắt cặp `H-1`.
5. **Có thể chuyển `/api/analyze` sang Hybrid mà không làm mất những chức năng quan trọng không?**
   - **Về mặt tích hợp kỹ thuật và cơ chế rollback thì đã sẵn sàng, nhưng về mặt nghiệm thu sản phẩm thì CHƯA được phép lật mặc định.** Tuyến `/api/analyze` đã tích hợp sẵn công tắc `HYBRID_ROUTE_MODE`, giữ nguyên envelope API, Scene3D, ingestion ảnh, lớp học/lưu trữ (`74` mô-đun dùng chung) và có cơ chế rollback tức thì `HYBRID_ROUTE_MODE=off` cách ly cache hai chiều (`ROUTE_D_CACHE_POLICY`). Tuy nhiên, một số dạng ngoài `geometry-functions/32` (hoặc một vài dạng mặt phẳng tọa độ/giao tuyến cong cũ) sẽ từ chối an toàn (`fail-closed`), nên bắt buộc phải có số liệu bắt cặp `H-1` chứng minh tỷ lệ phục vụ đúng không kém hơn `LLM_ONLY` quá `5 pp` trước khi chuyển đổi.
6. **Nếu chưa thể cutover, chính xác còn thiếu bằng chứng hoặc năng lực nào?**
   - Toàn bộ phần kỹ thuật backend và công cụ đánh giá an toàn đã hoàn tất; hiện chỉ còn thiếu **đúng 2 đầu vào từ phía con người/Owner** để chạy phép đo quyết định:
     1. **Bộ đề độc lập `H-1` (`h1-independent-corpus.json`, `60` đề = `45 SERVE + 5/5/5 REFUSE`)** kèm dẫn xuất oracle chính xác từ một tác giả con người độc lập theo [`H1_AUTHORING_HANDOFF.md`](H1_AUTHORING_HANDOFF.md).
     2. **File ủy quyền ngân sách chiến dịch `paired-live-owner-approval.json`** của Owner cho `campaign_max_requests = 300`, `campaign_max_usd = 5.0` (`\$5.00`, chi phí thực tế dự kiến chỉ `\$1.50 – \$2.00`), sau đó vượt qua 8 tiêu chí §7 và quyết định `D-13` của Owner.

---

## 2. Candidate Identity, Harness Hashes & Kiểm Thử C27–C28 (§I, §IV, §IX)

Toàn bộ kiểm tra xác nhận mã sản phẩm không thay đổi kể từ Full T3 PASS của C26, an toàn công bố trên nhánh đạt `PASS` ([`publication-safety-receipt.json`](publication-safety-receipt.json): `--range main..HEAD` quét `1,342` đối tượng + `194` commit message, `0` vi phạm; `--head` không phát sinh vi phạm mới ngoài `103` mục `PENDING_OWNER_DECISION` tồn tại sẵn từ `main`), và bộ công cụ tiếp nhận/chấm điểm C28 đã được khóa mã băm mới tại [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json):

- **Frozen candidate commit:** `180db769` (`EVALUATION_CANDIDATE.json` `sha256 = 218404c8794861b1…`, `freeze_evaluation_candidate.py --verify` $\rightarrow$ **`MATCH`**).
- **Product commit:** `d331e75b5bbf15722eca77c54e398173eefec98d` (`measured_system = 276fc548196e13ea…`, `118` files).
- **Phiên bản các tầng tất định:** `geometry-functions/32` · `geometry-fact-planner/26` · `geometry-function-engine/24` · `typed-fact-next/2` · `hybrid-simulation-adapter/4`.
- **Cấu hình an toàn sản phẩm hiện hành:** `DEFAULT_MODE = "LLM_ONLY"`, `HYBRID_ROUTE_MODE = "off"`, `CACHE_VERSION = "131"`, `model = "gemini-2.5-flash"`.
- **Mã băm công cụ đánh giá đã khóa:**
  - `paired_harness_sha256` ([`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py)): `8af7ca1f27e7ca3fb4e58ba7e0e067bc17973d8254a086e6c39d896078cd2e1f`.
  - `equivalence_scorer_sha256` ([`score_independent_holdout_equivalence.py`](../../../../../backend/scripts/score_independent_holdout_equivalence.py)): `7ada8a0616e9482b4984e92e86804bfc60deab540a505a10da65d8436ceba391`.
- **Kiểm chứng TDD RED $\rightarrow$ GREEN trong C27–C28:**
  - [`test_paired_live_safe_budget.py`](../../../../../backend/tests/geometry/test_paired_live_safe_budget.py): **`18 / 18` PASS** (14 kịch bản ngân sách `SafeCampaignBudget`, kiểm toán 6 bất biến hợp đồng `Scene3D`, phân loại `planner_composition`, `clarification_requested`, chấm ba tầng thời gian thực và ma trận bắt cặp $2 \times 2$).
  - [`test_independent_holdout_equivalence.py`](../../../../../backend/tests/geometry/test_independent_holdout_equivalence.py): **`9 / 9` PASS** (chính sách P1 Trường hợp A/B/C, phát hiện chép nguyên văn ví dụ handoff & sao chép khung đề đổi tên đỉnh/số đo, kiểm tra 10 điều kiện tiếp nhận §IV gồm độ phủ `≥ 3` bài cho đủ `7` họ hình và `5` nhóm câu hỏi, nhất quán `semantic_annotations` hai chiều, mẫu khung sạch [`h1-corpus-template.json`](h1-corpus-template.json) và kết xuất bảng đối chiếu bắt cặp).
  - Hồi quy bộ công cụ hiện hữu: `test_paired_route_evaluation.py` (**`54 / 54` PASS**), `test_s2_student_language_pilot_runner.py` + `test_s2_student_language_pilot_harness.py` (**`109 / 109` PASS**).

---

## 3. Tóm Tắt Thực Nghiệm Hiện Có vs Khoảng Trống Đo Lường H-1

| Chỉ số yêu cầu | Hybrid trên C26 (`K-1/S-2/R-1`, `70` ca — ĐÃ NHIỄM PHÁT TRIỂN) | Hybrid trên `H-1` (`60` ca độc lập) | `LLM_ONLY` trên `H-1` (`60` ca độc lập) | So sánh bắt cặp `H-1` (`HYBRID` vs `LLM_ONLY`) |
|---|---|---|---|---|
| **Outcomes tổng thể** | `37` SERVED, `25` REFUSED, `8` CLARIFY (`69` HTTP 200 + `1` Domain Gate) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Mathematical Correctness** | **37 / 41 (90.24%)** · `wrong_served`: **0 / 70 (0.0%)** | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Semantic Goal Correctness (P1)** | **37 / 41 (90.24%)** (`goal_completeness`: **52 / 53**, `wrong_served`: **0 / 70**) | `NOT_MEASURED` | Không áp dụng | Báo cáo riêng cho `HYBRID` |
| **Strict Contract Correctness** | **30 / 41 (73.17%)** (`7` ca câu gộp *"Xác định thiết diện… và tính diện tích"* so với gold rút gọn lịch sử) | `NOT_MEASURED` | Không áp dụng | Báo cáo riêng cho `HYBRID` |
| **False refusal** | **4 / 41 (9.76%)** toàn tập (`2 / 39` trên tập dương tính chung với Run 3, giảm từ `20 / 39`) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Clarification & Refusal correctness** | `29 / 29` âm tính không phục vụ; đúng lý do nghiêm ngặt `16 / 29` (semantic P1 `18 / 29`); clarification đúng mã `6 / 7` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Latency (HTTP / Case)** | Median `7.74 s` HTTP (`7.81 s` case) · Mean `8.48 s` · p90 `12.26 s` · Max `19.33 s` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Tokens (`69` calls)** | Tổng `177,693` in / `43,777` out / `74,865` think (`296,335` total; trung bình `4,294.7` tok/call) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Cost (USD)** | Tổng **`\$0.349913`** (`\$0.005071` / call; `\$0.009457` / ca SERVED đúng toán) | `NOT_MEASURED` *(dự kiến `\$0.28–\$0.36`)* | `NOT_MEASURED` *(dự kiến `\$1.20–\$1.55`)* | `NOT_MEASURED` *(tổng dự kiến `\$1.50–\$2.00` dưới trần `\$5.00`)* |
| **Failure attribution** | `EXPECTED_REFUSAL` 25 · `SOURCE_GATE_FAILURE` 4 · `EXTRACTION_FAILURE` 4 · Planner/Registry/Kernel/Adapter/Provider `0` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Statistical uncertainty** | Wilson 95% CI cho `wrong_served` (`0/70`): `[0.0%, 5.21%]` (chỉ trên tập phát triển) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |

---

## 4. Kế Hoạch Chuyển Đổi, Rollback & Nghỉ Hưu Legacy (Chỉ Thi Hành Sau Khi Đạt GO + Owner Duyệt D-13)

1. **Căn chỉnh cấu hình runtime trước khi lật mặc định:** Đồng bộ `HYBRID_LIVE_TIMEOUT_SECONDS` / `HYBRID_LIVE_DEADLINE_SECONDS` trong `backend/app/main.py` với thông số đã được chứng nhận thực nghiệm và tăng `CACHE_VERSION`.
2. **Cutover có kiểm soát & Rollback tức thì (`D-12`):** Lật tuyến mặc định `/api/analyze` sang `HYBRID_ROUTE_MODE = "live"` (không silent fallback sang `LLM_ONLY`). Nếu cần quay lui, đặt `HYBRID_ROUTE_MODE=off` lập tức khôi phục 100% đường `LLM_ONLY` nhờ cách ly cache hai chiều `ROUTE_D_CACHE_POLICY`.
3. **Thứ tự nghỉ hưu `LLM_ONLY` (`LEGACY_REMOVAL_BLOCKED` cho tới sau chu kỳ ổn định hậu-Cutover):** Giữ nguyên `6` mô-đun `HYBRID_REQUIRED` và `74` mô-đun `SHARED_COMPONENT`; chỉ sau lệnh riêng của Owner mới tách `RoutePolicy` khỏi `ai/pipeline.py`, gỡ `13` mô-đun `LEGACY_ONLY` (`geometry_compiler/*` và chuỗi tổng hợp `semantic_program` của `LLM_ONLY`), và chốt 3 mô-đun `UNCERTAIN_DEPENDENCY` (`adapter3_simulation.py`).

---

## 5. Hành Động Cụ Thể Duy Nhất Cần Từ Owner Để Thực Thi Ngay H-1 Paired Live (C28 §III & §XIII)

1. **Bàn giao gói tài liệu sạch cho tác giả độc lập để tạo bộ đề `H-1` (60 đề):**
   - Gửi trực tiếp **hai tệp tự chứa duy nhất** trong thư mục này cho tác giả con người độc lập: [`H1_AUTHORING_HANDOFF.md`](H1_AUTHORING_HANDOFF.md) và [`h1-corpus-template.json`](h1-corpus-template.json) để biên soạn `docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json` (`45 SERVE` phủ đủ `≥ 3` bài cho cả `7` họ hình và `5` nhóm câu hỏi + `5 OUT_OF_DOMAIN` + `5 CONTRADICTORY_DATA` + `5 MISSING_DATA`, đạt đủ 10 điều kiện nghiệm thu đầu vào ở `H1_AUTHORING_HANDOFF.md` §6).
2. **Phê duyệt ngân sách an toàn `\$5.00` trong `paired-live-owner-approval.json`:**
   - Sau khi chạy lệnh niêm phong Bước 1 ở [`PAIRED_LIVE_BUDGET_PROPOSAL.md`](PAIRED_LIVE_BUDGET_PROPOSAL.md) §5 để lấy `corpus_sha256` và `oracle_sha256`, Owner tạo `docs/evaluation/geometry/runs/hybrid-independent-h1/paired-live-owner-approval.json` từ mẫu [`paired-live-owner-approval.template.json`](paired-live-owner-approval.template.json) với:
     - `paid_project_confirmed = true`,
     - `authoring_independence = "ESTABLISHED"`, `evaluator_independence = "ESTABLISHED"`, `corpus_author = "<tên tác giả độc lập>"`,
     - `campaign_max_requests = 300`, `campaign_max_usd = 5.0` (`max_requests = 300`, `max_usd = 5.0`; chi phí thực tế dự kiến **`\$1.50 – \$2.00`**),
     - và trường quyết định phê duyệt của Owner theo quy định của harness.

Ngay khi có đủ hai tệp hợp lệ trên, lệnh chạy tại [`PAIRED_LIVE_BUDGET_PROPOSAL.md`](PAIRED_LIVE_BUDGET_PROPOSAL.md) §5 sẽ thực thi tự động trọn vẹn 60 cặp `LLM_ONLY` vs `HYBRID` trên `gemini-2.5-flash`, xuất `H1_PAIRED_LIVE_EVALUATION_REPORT.md` và cập nhật phán quyết cutover cuối cùng.
