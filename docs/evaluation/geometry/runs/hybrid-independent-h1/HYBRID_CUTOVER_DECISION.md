# Báo Cáo Tổng Hợp & Quyết Định Chuyển Đổi Kiến Trúc Hybrid (`HYBRID_CUTOVER_DECISION`)

**Run:** `hybrid-independent-h1` · **Master Epic:** `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · **Phạm vi:** `BACKEND_ONLY` (`frontend/**`: `0` thay đổi) · **Ngày lập:** `2026-11-03`.

> [!IMPORTANT]
> **Phán quyết hiện hành dựa trên hợp đồng nghiệm thu (0 lượt gọi Gemini live trong phiên này):**
> - `H1_AUTHORING_INDEPENDENCE` = **`NOT_ESTABLISHED`** (chưa có tác giả con người độc lập do Owner chỉ định và chưa có bộ 60 đề `H-1` trên đĩa).
> - `H1_MEASUREMENT` = **`NOT_MEASURED`**.
> - `PAIRED_LIVE_EVALUATION_COMPLETE` = **`NO`**.
> - `LIVE_GEMINI_QUALITY_VALIDATED` = **`NO`** (bằng chứng live hiện có thuộc chiến dịch C26 trên `K-1/S-2/R-1` đã dùng cho phát triển).
> - `HYBRID_CUTOVER_DECISION` = **`HYBRID_CUTOVER_BLOCKED`** (`DEFAULT_MODE = "LLM_ONLY"` và `HYBRID_ROUTE_MODE = "off"` giữ nguyên).
> - `LEGACY_REMOVAL_DECISION` = **`LEGACY_REMOVAL_BLOCKED`** (`LLM_ONLY` chưa được phép gỡ bỏ).

*(Lưu ý tuân thủ §XII: Báo cáo `H1_PAIRED_LIVE_EVALUATION_REPORT.md` **không được tạo** ở thời điểm này vì phép đo live trên `H-1` chưa diễn ra; tuyệt đối không tạo tệp chứa số liệu giả hay bảng trống giả danh kết quả thực nghiệm).*

---

## 1. Candidate Identity & Bằng Chứng Đóng Băng (§I – §II)

Toàn bộ kiểm tra Git và biên nhận máy tại [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json) xác nhận candidate mục tiêu không hề thay đổi kể từ Full T3 PASS của C26:

- **Frozen candidate commit:** `180db769` (`EVALUATION_CANDIDATE.json` `sha256 = 218404c8794861b140a8c16ffd8dcdca30c4bfaaf8cee33332b0e4ff2ac5dcb9`, `freeze_evaluation_candidate.py --verify` $\rightarrow$ **`MATCH`**).
- **Product commit:** `d331e75b5bbf15722eca77c54e398173eefec98d`.
- **Measured system:** `276fc548196e13eaa0ca7635428248dcaee7be79b79dff58c24a0478cddd4c63` (`118` files).
- **Phiên bản các tầng tất định:** `geometry-functions/32` · `geometry-fact-planner/26` · `geometry-function-engine/24` · `typed-fact-next/2` · `hybrid-simulation-adapter/4`.
- **Cấu hình an toàn sản phẩm hiện hành:** `DEFAULT_MODE = "LLM_ONLY"`, `HYBRID_ROUTE_MODE = "off"`, `CACHE_VERSION = "131"`, `model = "gemini-2.5-flash"`.
- **Nền tảng kiểm thử đã chứng nhận trên đúng `180db769`:** Full T3 `FULL_PRODUCT_GATE_PASS` (`16,698` pytest PASS, `1,502` vitest PASS, [`full-t3-180db769.json`](../hybrid-live-extraction-retest/full-t3-180db769.json)) cộng `5 / 5` kiểm thử mới cho bộ chấm ba tầng và niêm phong `H-1` ([`test_independent_holdout_equivalence.py`](../../../../../backend/tests/geometry/test_independent_holdout_equivalence.py)).

---

## 2. Trạng Thái H-1 Authoring Independence, Corpus/Oracle Hashes & Acceptance Criteria

| Hạng mục bắt buộc (§XII) | Giá trị xác minh hiện tại | Nguồn / Biên nhận |
|---|---|---|
| **H-1 authoring independence evidence** | `NOT_ESTABLISHED` — chưa có tác giả con người độc lập được chỉ định; agent tuân thủ lệnh cấm tự sáng tác 60 đề | [`H1_AUTHORING_HANDOFF.md`](H1_AUTHORING_HANDOFF.md), [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json) |
| **`corpus_sha256` / `oracle_sha256`** | `null` / `null` (sẽ được đóng dấu tự động ở Bước 1 niêm phong ngay khi nhận `h1-independent-corpus.json`) | [`H1_CORPUS_INTEGRITY.json`](H1_CORPUS_INTEGRITY.json) |
| **Acceptance criteria** | Khóa trước 8 tiêu chí `0..7` của Giao thức §7 (`0` wrong-served trên `HYBRID`, `served_correct` $\ge \text{LLM\_ONLY} - 5\text{ pp}$ & McNemar không nghiêng về `LLM_ONLY`, `100%` refusal trên 15 bài âm tính & đúng lý do $\ge \text{LLM\_ONLY}$, median latency $\le \text{LLM\_ONLY}$ & p90 $\le 1.5\times$, USD upper/served-correct $\le \text{LLM\_ONLY}$ lower, lỗi kỹ thuật $\le 5\%$, độc lập tác giả `ESTABLISHED`) | [`H1_PREREGISTRATION.md`](H1_PREREGISTRATION.md) §4.2, [`live-evaluation-protocol.md`](../hybrid-master-backend-replacement/live-evaluation-protocol.md) §7 |
| **Quy tắc Strict vs Semantic (§III)** | Khóa trước chính sách `h1-section-determination-equivalence/1`: tách minh bạch **Mathematical** / **Semantic Goal** / **Strict Contract** mà không sửa bất kỳ nhãn gold lịch sử nào | [`H1_PREREGISTRATION.md`](H1_PREREGISTRATION.md) §2, [`c26-three-tier-verification.json`](c26-three-tier-verification.json) |

---

## 3. Tóm Tắt Kết Quả Thực Nghiệm Hiện Có vs Khoảng Trống Đo Lường H-1 (§XII)

Bảng dưới đây phân tách rạch ròi giữa **số liệu đã đo thật trên tập phát triển C26** (không đủ điều kiện kết luận cutover do nhiễm phát triển) và **trạng thái của phép đo bắt cặp độc lập H-1**:

| Chỉ số yêu cầu | Hybrid trên C26 (`K-1/S-2/R-1`, `70` ca — ĐÃ NHIỄM PHÁT TRIỂN) | Hybrid trên `H-1` (`60` ca độc lập) | `LLM_ONLY` trên `H-1` (`60` ca độc lập) | So sánh bắt cặp `H-1` (`HYBRID` vs `LLM_ONLY`) |
|---|---|---|---|---|
| **Outcomes tổng thể** | `37` SERVED, `25` REFUSED, `8` CLARIFY (`69` HTTP 200 + `1` Domain Gate) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Correct-served (Mathematical / Semantic)** | **37 / 41 (90.24%)** theo cả Mathematical và Semantic (`h1-section-determination-equivalence/1`) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Correct-served (Strict Contract)** | **30 / 41 (73.17%)** (`7` ca câu gộp *"Xác định thiết diện… và tính diện tích"* thêm `construct_plane_section` đúng chỉ dẫn so với gold rút gọn `area`) | `NOT_MEASURED` | Không áp dụng (`LLM_ONLY` không xuất `TypedFactNext`) | Báo cáo riêng cho `HYBRID` |
| **Mathematical wrong-served** | **0 / 70 (0.0%)** (`37/37` khớp chính xác oracle kèm chứng chỉ; `0/29` ca âm tính bị phục vụ) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **False refusal** | **4 / 41 (9.76%)** toàn tập (`2 / 39` trên tập dương tính chung với Run 3, giảm từ `20 / 39`) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Clarification & Refusal correctness** | `29 / 29` âm tính không phục vụ; đúng lý do nghiêm ngặt `16 / 29` (semantic `18 / 29`); clarification đúng mã `6 / 7` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Latency (HTTP / Case)** | Median `7.74 s` HTTP (`7.81 s` case) · Mean `8.48 s` · p90 `12.26 s` · Max `19.33 s` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Tokens (`69` calls)** | Tổng `177,693` in / `43,777` out / `74,865` think (`296,335` total; trung bình `4,294.7` tok/call) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Cost (USD)** | Tổng **`$0.349913`** (`$0.005071` / call; `$0.009457` / ca SERVED đúng toán) | `NOT_MEASURED` *(dự kiến `$0.28–$0.36`)* | `NOT_MEASURED` *(dự kiến `$1.20–$1.55`)* | `NOT_MEASURED` *(tổng dự kiến `$1.50–$2.00`)* |
| **Failure attribution** | `EXPECTED_REFUSAL` 25 · `SOURCE_GATE_FAILURE` 4 · `EXTRACTION_FAILURE` 4 · Planner/Registry/Kernel/Adapter/Provider `0` | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |
| **Statistical uncertainty** | Wilson 95% CI cho `wrong_served` (`0/70`): `[0.0%, 5.21%]` (chỉ trên tập phát triển) | `NOT_MEASURED` | `NOT_MEASURED` | `NOT_MEASURED` |

---

## 4. Kế Hoạch Chuyển Đổi, Rollback & Dọn Legacy (Sẵn Sàng Thi Hành Khi Đạt GO + Owner Duyệt D-13)

Mặc dù hiện tại quyết định là **`HYBRID_CUTOVER_BLOCKED`** và **`LEGACY_REMOVAL_BLOCKED`**, toàn bộ lộ trình kỹ thuật khi phép đo `H-1` đạt `HYBRID_CUTOVER_GO` và được Owner phê duyệt cổng `D-13` đã được đối chiếu đầy đủ từ mã nguồn thực tế:

### 4.1. Kế hoạch chuyển `/api/analyze` sang Hybrid & Đồng bộ cấu hình runtime

1. **Căn chỉnh deadline live trước khi bật mặc định:** Trong giao thức bắt cặp, `HYBRID` được đo với `HYBRID_LIVE_DEADLINE_S = 480 s` (`120 s` mỗi lần thử × `4` lần thử), trong khi `backend/app/main.py` hiện đặt mặc định `HYBRID_LIVE_TIMEOUT_SECONDS = 60` và `HYBRID_LIVE_DEADLINE_SECONDS = 180` (đã đủ cho max thực tế `19.33 s` ở C26 nhưng ngắn hơn mức đo của harness). Trước khi lật mặc định, thống nhất tham số cấu hình theo đúng giá trị đã được chứng nhận thực nghiệm và bump `CACHE_VERSION`.
2. **Chuyển cờ mặc định có kiểm soát (giai đoạn Canary / Cutover 1 bản phát hành):** Đổi tuyến mặc định của `POST /api/analyze` sang `HYBRID_ROUTE_MODE = "live"` (khi có `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`), giữ nguyên tính bất biến của phản hồi lỗi kỹ thuật có mã (`502`/`503`/`504`, `no-store`) và **tuyệt đối không fallback ngầm sang `LLM_ONLY`**.
3. **Cơ chế Rollback tức thì (`D-12`, đã chứng minh offline tại `test_hybrid_route_d_cache_and_rollback.py`):**
   - Đặt biến môi trường `HYBRID_ROUTE_MODE=off` lập tức đưa `/api/analyze` quay về `LLM_ONLY` nguyên vẹn từng byte mà không cần sửa code hay redeploy image.
   - Nhờ chính sách cách ly hai chiều `ROUTE_D_CACHE_POLICY`, các bản ghi cache của `HYBRID` không bao giờ nhiễm sang `LLM_ONLY` khi rollback và ngược lại.

### 4.2. Đối chiếu Legacy Dependency Inventory & Thứ tự nghỉ hưu `LLM_ONLY`

Kiểm kê phụ thuộc trên 96 mô-đun backend liên quan (đối chiếu từ [`migration-ledger.md`](../hybrid-master-backend-replacement/migration-ledger.md) và [`HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md`](../hybrid-live-validation/HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md) §18):

- **`6` mô-đun `HYBRID_REQUIRED` (Giữ & làm trục chính):** `typed_fact_next.py`, `typed_fact_next_extraction.py`, `typed_fact_next_bridge.py`, `adapter4_route.py`, `hybrid_offline.py`, cùng hệ `geometry_functions/{registry,planner,engine}.py`.
- **`74` mô-đun `SHARED_COMPONENT` (Bắt buộc giữ nguyên để bảo toàn API & Scene3D):** Toàn bộ exact kernel (`geometry/radical.py`, `metric.py`, `curved.py`, …), trình thông dịch IR, bộ biên dịch đối tượng `scene3d`, `function_calling.py` (`_openapi`, `live_transport`), `hybrid_preview.py` (hợp đồng 41 fixtures khóa cứng), `runtime_identity.py`, ingestion ảnh và tầng lưu trữ/lớp học.
- **`13` mô-đun `LEGACY_ONLY` (Chỉ được gỡ sau khi qua giai đoạn giữ rollback sau Cutover GO):**
  - Chuỗi tổng hợp chương trình `LLM_ONLY` (`ai/pipeline.py::run_pipeline` & `stage_semantic_program`, `semantic_program/{route,analyze_contract,grammar_card,learner_surface,section_provenance,visual_obligations}.py`).
  - Nhánh Compiler C 6 họ cũ đang tắt (`simulation/geometry_compiler/*` gồm 6 mô-đun và 7 script chẩn đoán).
- **`3` mô-đun `UNCERTAIN_DEPENDENCY` (Xử lý từng mục sau kiểm tra parity cuối):** `ai/adapter3_simulation.py` và nhánh cong `/3` trong `function_route.py` (hiện chỉ còn 10 file test gọi trực tiếp wrapper, nhưng một số dạng mặt phẳng tọa độ / giao tuyến elip trên `/3` vẫn là từ chối chủ đích trên `/4`).

**Thứ tự gỡ bỏ an toàn 7 bước (chỉ thực hiện khi có lệnh riêng của Owner sau Cutover GO):**
1. Tách `RoutePolicy` và `route_policy_snapshot` ra khỏi `ai/pipeline.py` sang mô-đun trung lập để `main.py`, `hybrid_offline.py` và `runtime_identity.py` không còn import `pipeline.py`.
2. Lật mặc định `/api/analyze` sang `HYBRID` kèm bump `CACHE_VERSION`, giữ `HYBRID_ROUTE_MODE=off` làm công tắc rollback ít nhất qua một chu kỳ vận hành ổn định.
3. Gỡ bỏ `simulation/geometry_compiler/*` (Compiler C đang tắt) và các script chẩn đoán riêng của nó.
4. Chuyển `runtime_identity.py` và mã lỗi của `main.py` khỏi các hằng của `analyze_contract` / `grammar_card`, sau đó gỡ `pipeline.run_pipeline` cùng cụm `semantic_program` chỉ phục vụ `LLM_ONLY`.
5. Giữ nguyên 100% `74` mô-đun `SHARED_COMPONENT`.
6. Quyết định dứt điểm 3 mô-đun `UNCERTAIN_DEPENDENCY` (`adapter3_simulation.py`) kèm bộ test của chúng.
7. Chạy lại Full T3 và kiểm toán an toàn xuất bản trước khi tích hợp lên `main`.

### 4.3. Quy trình xử lý nếu `H-1` trả về `HYBRID_CUTOVER_NO_GO`

- Giữ nguyên `DEFAULT_MODE = "LLM_ONLY"` và `HYBRID_ROUTE_MODE = "off"`; tuyệt đối không hạ ngưỡng §7 và không sửa đáp án chuẩn `H-1`.
- Quy kết từng ca lỗi vào đúng 11 nhóm tại [`H1_PREREGISTRATION.md`](H1_PREREGISTRATION.md) §5 để xác định thứ tự ưu tiên sửa backend có bằng chứng.
- Nếu sửa mã sản phẩm dựa trên lỗi của `H-1`, đánh dấu `H-1` đã chuyển thành tập hồi quy phát triển, đóng băng candidate mới và yêu cầu tập đề mù mới (`H-2`) cho lần kiểm chứng tổng quát hóa kế tiếp.

---

## 5. Hành Động Cụ Thể Cần Owner Thực Hiện Để Mở Khóa Phép Đo (§XIII)

Agent đã hoàn thành tối đa toàn bộ công việc kỹ thuật hợp lệ mà không cần sự can thiệp của con người (chốt quy tắc ba tầng, cài đặt & kiểm thử bộ chấm/niêm phong, chuẩn bị hướng dẫn độc lập không nhiễm, tiền đăng ký giao thức và tính toán ngân sách). Để chuyển sang bước thực thi tự động `H-1` Paired Live ngay lập tức, Owner chỉ cần thực hiện **2 đầu vào con người bắt buộc**:

1. **Bàn giao bộ đề độc lập `H-1` (60 đề):**
   - Giao tài liệu [`H1_AUTHORING_HANDOFF.md`](H1_AUTHORING_HANDOFF.md) (và mẫu [`corpus-template.json`](../hybrid-master-backend-replacement/heldout-authoring/corpus-template.json)) cho một tác giả độc lập (hoặc tự biên soạn nếu đáp ứng điều kiện độc lập) để tạo tệp `docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json` (`45 SERVE` + `5 OUT_OF_DOMAIN` + `5 CONTRADICTORY_DATA` + `5 MISSING_DATA`).
2. **Cấp phê duyệt ngân sách chiến dịch Paired Live:**
   - Sau khi chạy Bước 1–2 ở [`PAIRED_LIVE_BUDGET_PROPOSAL.md`](PAIRED_LIVE_BUDGET_PROPOSAL.md) §5 để điền `corpus_sha256` và tên `corpus_author`, Owner tạo tệp `docs/evaluation/geometry/runs/hybrid-independent-h1/paired-live-owner-approval.json` từ mẫu [`paired-live-owner-approval.template.json`](paired-live-owner-approval.template.json) với:
     - `authoring_independence = "ESTABLISHED"`, `evaluator_independence = "ESTABLISHED"`,
     - `max_requests = 300`, `max_usd = 52.0` (chi phí thực tế kỳ vọng trên hóa đơn Gemini chỉ khoảng **`$1.50 – $2.00`**),
     - và trường quyết định của người dùng theo đúng quy định của harness.
   - *(Tùy chọn)* Xác nhận Phương án **P1** hoặc **P2** tại [`H1_PREREGISTRATION.md`](H1_PREREGISTRATION.md) §2.3 cho quy ước câu gộp *"Xác định thiết diện… và tính diện tích"*.

Ngay khi hai tệp trên có mặt và hợp lệ, agent sẽ tự động niêm phong manifest, chạy trọn vẹn 60 cặp `LLM_ONLY` vs `HYBRID` trên `gemini-2.5-flash`, xuất `H1_PAIRED_LIVE_EVALUATION_REPORT.md` và cập nhật phán quyết cutover cuối cùng.
