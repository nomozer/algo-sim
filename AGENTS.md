# AGENTS.md — AlgoSim Agent Entry Point & Safety Rules

> **Entry Point duy nhất cho Coding Agents và AI Sessions.**
> File này là cổng định hướng ngắn gọn. Tài liệu quy tắc ổn định và chi tiết là [`docs/RULES.md`](docs/RULES.md).
> Tài liệu mâu thuẫn với code hoặc test thật: theo luật **CODE/TESTS** ở [`docs/RULES.md §1`](docs/RULES.md).

---

## 1. Thứ Tự Đọc Bắt Buộc Trước Mọi Thay Đổi

1. **File này (`AGENTS.md`)** — Quy tắc an toàn và bootstrap.
2. **[`docs/RULES.md`](docs/RULES.md)** — Quy tắc cứng, scope guard, checklist chống viết trùng.
3. **[`docs/AI_CONTEXT_BUNDLE.md`](docs/AI_CONTEXT_BUNDLE.md)** — Bản tóm tắt ngữ cảnh bàn giao phiên (handoff).
4. **[`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md)** — Cơ sở sản phẩm, trạng thái kiến trúc, mốc đã chứng minh.
5. **[`docs/OPEN_ISSUES.md`](docs/OPEN_ISSUES.md)** — Các vấn đề kỹ thuật đang mở.
6. **[`docs/ROADMAP.md`](docs/ROADMAP.md)** — Lộ trình ưu tiên khóa luận (P0–P6).
7. **[`docs/CODE_INDEX.md`](docs/CODE_INDEX.md)** — Tra cứu vị trí module / tooling / test đã có (chống viết trùng).
8. **[`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md)** — Tra cứu báo cáo và artifact kiểm chứng.
9. **Code và Test thực tế liên quan trực tiếp.**

---

## 2. Git & Working Tree Safety

- **Bảo toàn thay đổi của người dùng:** Tuyệt đối không sửa, khôi phục (restore), stage hoặc commit bất kỳ thay đổi nào của người dùng ngoài phạm vi nhiệm vụ được giao. Mọi trạng thái working tree chưa commit của người dùng phải được giữ nguyên.
- **Staging Allowlist:** Luôn dùng `git add <từng file cụ thể>`. Tuyệt đối không dùng `git add .` hoặc `git add -A`. Trước khi commit, kiểm tra `git diff --cached --name-only`.
- **Nhánh & Lịch sử:** Làm việc trên nhánh được chỉ định. Mặc định **không merge vào `main`** và **không push**. Chỉ khi user cho phép rõ ràng **và** mọi điều kiện nghiệm thu của task đã đạt mới merge thẳng vào `main`, push `main` và xoá nhánh đã merge. Không bao giờ **rewrite lịch sử** (`git commit --amend` trên commit đã công bố, `git rebase`, force-push).
- **Kiểm chứng độc lập:** Khi cần xác minh có thẩm quyền (authoritative verification), tạo git worktree detached sạch tại commit tương ứng.
- **Việc mới, nhánh mới, wave từ W1:** việc mới chỉ rẽ nhánh từ `main` đã tích hợp và cập nhật; run mới đặt tên theo việc, không mã lượt (`exact-dimensions`, `repo-cleanup`; lần thực hiện thứ hai của cùng việc thêm ngày), mã việc/lượt, ngày, commit nằm trong `run.json`; run cũ `<task-slug>-wNN` giữ tên. Không bao giờ `W1`/`W2` trần trong manifest hay chỉ mục. Luật đầy đủ (gồm tên file/thư mục): [`docs/evaluation/RUN_NAMING.md`](docs/evaluation/RUN_NAMING.md).

---

## 3. Architecture & Product Safety

- **Pipeline chính thức (`Hybrid /4`):**
  `Vietnamese Problem → Gemini → TypedFactNext /2 → Source Gate → FactGraph → Planner /26 → Registry /33 → Exact Kernel /24 → Adapter /4 → Scene3D + Construction Steps + Results`
  1. **Gemini** chỉ trích xuất dữ kiện, quan hệ và mục tiêu hình học kèm trích dẫn nguyên văn câu đề (`backend/app/ai/typed_fact_next_extraction.py`).
  2. **`TypedFactNext /2`** (`typed-fact-next/2` tại `backend/app/simulation/geometry_functions/typed_fact_next.py`, qua `bridge_v2` `typed-fact-next-bridge/2`) là hợp đồng trích xuất chính. (`RequestContract` tại `backend/app/simulation/semantic_program/request_contract.py` **không** phải đầu ra trích xuất chính của Gemini; nó chỉ giữ vai trò tương thích nội bộ `COMPATIBILITY_REQUIRED` trong bộ kiểm định IR dùng chung `backend/app/simulation/semantic_program/route.py` và truyền `solid_topology` tất định từ `engine.py` sang `formation.py`.)
  3. **Source Gate** (`registry.kiem_nguon`) xác minh dữ kiện, vai trò mệnh đề, phủ định và số đo theo nguyên văn đề bài trước khi lập kế hoạch.
  4. **FactGraph & Planner `/26`** (`planner.py`, `geometry-fact-planner/26`) tự xác định và kết hợp tất định các hàm có sẵn từ **Registry `/33`** (`registry.py`, `geometry-functions/33`).
  5. **Exact Kernel `/24`** (`engine.py`, `geometry-function-engine/24` + `backend/app/simulation/geometry/` + `semantic_program/interpreter.py`) chịu trách nhiệm hoàn toàn về khung tọa độ/metric Gram chính xác (`Fraction`, `Radical`), thực thi IR và chứng chỉ hình học.
  6. **Adapter `/4`** (`backend/app/ai/adapter4_route.py`, `hybrid-simulation-adapter/4`, envelope `hybrid-route-d-simulation/4`, `CACHE_VERSION = 132` / `ROUTE_D_CACHE_POLICY = 132:route-d`) tạo `Scene3D`, các bước dựng tích lũy liên tục (`construction_continuity.py`) và kết quả chính xác.
  7. **Không sinh chương trình giải riêng cho từng đề:** LLM tuyệt đối không tổng hợp hay sửa chương trình theo từng bài toán; thực thi `LLM_ONLY` (`pipeline.py` — đã xóa), `Adapter /3` (`adapter3_simulation.py` — đã xóa) và `Compiler C` (`geometry_compiler/` — đã xóa) không còn tồn tại.
  8. **Không hardcode:** Tuyệt đối không hardcode case ID, bài toán, nhãn đỉnh, tọa độ hoặc đáp án kỳ vọng vào mã sản phẩm.
- **Fail-closed (không tự bịa giả thiết, không trả kết quả thiếu căn cứ, không fallback về legacy):** Phân biệt rõ các nhóm khái niệm và bám đúng enum/schema thực tế trong `backend/app/` (không tự đặt mã mới):
  - `MISSING_DATA` (thiếu dữ kiện): nhóm `MISSING_DATA` → `failure_category="insufficient_specification"` (vd: `MISSING_DIMENSION`, `UNDERDETERMINED_POINT`, `PLANE_NOT_UNIQUE`, `FOOT_NOT_DETERMINED`, `AMBIGUOUS_FACT`, `AMBIGUOUS_REFERENCE`, `SECTION_NOT_CLOSED_ON_LATERAL_EDGES`), hoặc `FACT_INCOMPLETE` ở biên đầu vào.
  - `CONTRADICTORY_DATA` (dữ kiện mâu thuẫn / suy biến): nhóm `INVALID_DATA` → `failure_category="geometry_generation_failed"` (vd: `INCONSISTENT_FACTS`, `NON_POSITIVE_LENGTH`, `DEGENERATE_SOLID`, `COLLINEAR_POINTS`, `NON_COPLANAR_POINTS`, `PARALLEL_NO_INTERSECTION`, `PLANE_DOES_NOT_CUT`, `NO_CIRCUMSCRIBED_SPHERE`, `NO_INSCRIBED_SPHERE`); dữ kiện chưa đối chiếu được nguồn rơi vào `verification_gap` (vd: `QUOTE_NOT_IN_SOURCE`, `UNGROUNDED_VALUE`, `SOURCE_OBJECT_MISMATCH`).
  - `OUT_OF_SCOPE` (ngoài năng lực hỗ trợ / ngoài miền): cổng miền trước provider trả `status="unsupported"`, `failure_category="out_of_scope"`, `error_code="GATE_OUT_OF_SCOPE"`; câu đề hình học vượt ngoài thư viện hàm trên Route D thuộc nhóm `CAPABILITY` → `failure_category="capability_gap"` (vd: `OUT_OF_SCOPE`, `UNSUPPORTED_CAPABILITY`, `BRIDGE_UNSUPPORTED_*`, `CURVED_WORDING_UNSUPPORTED`, `EXACT_DOMAIN_EXCEEDED`).
  - `CLARIFICATION` (cần người dùng làm rõ): mục `UnresolvedSpec` khả giải (`ambiguous`, `missing_operand`, `unrecognized_term`) từ chối với `reason_code="AMBIGUOUS_FACT"` kèm bản ghi máy chủ dựng `route-d-clarification/1` (`nlu_class` thuộc `AMBIGUOUS` / `MISSING_DATA` / `UNRECOGNIZED_WORDING`).
  - `INFRASTRUCTURE_FAILURE` (lỗi provider / cấu hình / hạ tầng): trả HTTP `502`/`503`/`504` (`Cache-Control: no-store`, `failure_kind="INFRASTRUCTURE_FAILURE"`, không ghi cache, không gán nhãn thành từ chối toán học) theo `HYBRID_INFRASTRUCTURE_CODES` (vd: `MISSING_API_KEY`, `LIVE_AI_DISABLED`, `INVALID_HYBRID_ROUTE_MODE`, `STAGING_CORPUS_UNAVAILABLE`, `HYBRID_DEADLINE_EXCEEDED`, `PROVIDER_ERROR`, `PROVIDER_RESPONSE_INVALID`, `JSON_INVALID`, `RESPONSE_TRUNCATED`, `MAX_TOKENS`, `SCHEMA_VERSION_MISMATCH`, `ROUTE_INTERNAL_ERROR`, `ADAPTER_INTERNAL_ERROR`).
- **Routing, Cấu hình & Rollback:**
  - **Hybrid `/4`** là tuyến chính thức của `POST /api/analyze` (`backend/app/main.py`, `backend/app/ai/route_policy.py` với `default_route_mode = "HYBRID"`).
  - `HYBRID_ROUTE_MODE=live` là mặc định; thiếu `GEMINI_API_KEY` ở chế độ `live` trả lỗi kỹ thuật HTTP `503` (`reason_code="MISSING_API_KEY"`, `failure_kind="INFRASTRUCTURE_FAILURE"`); `ALLOW_LIVE_AI=0` là công tắc dừng khẩn cấp tùy chọn trả HTTP `503` (`reason_code="LIVE_AI_DISABLED"`).
  - `HYBRID_ROUTE_MODE=staging-replay` dành cho replay offline trong development/test (`HYBRID_REPLAY_CORPUS`; thiếu kho trả HTTP `503 STAGING_CORPUS_UNAVAILABLE`).
  - `HYBRID_ROUTE_MODE=off` (hoặc giá trị không nhận diện) **không còn rollback về `LLM_ONLY`** mà trả lỗi HTTP `503` (`reason_code="INVALID_HYBRID_ROUTE_MODE"`).
  - **Rollback kiến trúc** là rollback phiên bản Git/deployment trước cutover (tag `pre-hybrid-cutover-f986e897`) hoặc tạo commit `git revert` tiến tới. Không hướng dẫn bật `HYBRID_V2_LOCAL`, `GEOMETRY_COMPILER_MODE` hoặc khôi phục đường thực thi `LLM_ONLY` đã xóa.
- **Giới hạn kiểm chứng hiện hành:** Giữ phân định trung thực ([`docs/CURRENT_STATE.md`](docs/CURRENT_STATE.md), [`docs/MIGRATION_CHECKLIST.md`](docs/MIGRATION_CHECKLIST.md)): `HYBRID_DEFAULT_CUTOVER_COMPLETE = YES` · `LEGACY_EXECUTION_RETIRED = YES` · `LEGACY_FULLY_RETIRED = NO` · `PRODUCTION_DEPLOYMENT_VERIFIED = NO` · `INDEPENDENT_H1_VALIDATION = NOT_MEASURED` (không mô tả C26 hay Full T3 offline thành kiểm định độc lập trên H-1; không tuyên bố Hybrid giải mọi bài hình học không gian).

---

## 4. Evidence & Documentation Safety

- **Bằng chứng còn được sử dụng phải giữ nguyên nội dung:** Không sửa byte của kết quả đo, input/output, manifest hoặc báo cáo đang làm căn cứ cho sản phẩm, nghiên cứu hiện hành hay khả năng tái lập đã cam kết. Được đổi tên/chuyển file hoặc folder khi cập nhật đồng bộ consumer, manifest và index; run ID giữ trong metadata khi cần. Được xoá tài liệu/artifact đã đọc và xác minh không còn phục vụ ba mục đích trên. Nhãn `historical`/`frozen` hoặc một test pin, tự nó, không phải lý do giữ; việc xoá phải có inventory, kiểm tham chiếu và đường khôi phục bằng commit Git.
- **Nháp của công cụ agent không tự động là bằng chứng bất biến:** plan, brief, report, ledger và gói review do skill/agent sinh (`.superpowers/` — nháp local, gitignore).
- **Kế hoạch/spec của skill theo cấu trúc dự án:** thiết kế là contract đang hiệu lực ⇒ `docs/architecture/`; kế hoạch triển khai ⇒ `plan.md` trong thư mục run của việc. Không tạo `docs/superpowers/` hay thư mục tài liệu mới; không nhân bản một kế hoạch ở nhiều nơi. Chi tiết: [`docs/README.md`](docs/README.md) §8.
- **Dọn có kiểm:** bản trùng, plan bỏ dở, bằng chứng hết consumer và tài liệu ngoài phạm vi được xoá sau khi đọc nội dung, kiểm mọi tham chiếu (code, test, tooling, docs, manifest) và chuyển thông tin duy nhất sang tài liệu có thẩm quyền kèm nguồn; nhóm trộn phải xử lý từng phần; xoá theo đường dẫn chính xác, ghi nhật ký xoá.
- **Test không ghi vào bằng chứng đông cứng:** output tái sinh đi vào thư mục tạm hoặc một run mới.
- **Phê duyệt là của người:** tự động hoá (script, test, agent) không bao giờ ghi `APPROVED_BY_USER`.
- **Báo cáo wave mới nằm trong thư mục run** (`docs/evaluation/geometry/runs/<run>/`), không ở gốc `docs/`. Báo cáo cũ được tra qua [`docs/evaluation/HISTORICAL_REPORTS.md`](docs/evaluation/HISTORICAL_REPORTS.md): report có package đo thì nằm cạnh artifact, report theo chủ đề nằm ở `docs/evaluation/reports/`; chỉ ngoại lệ path-bound được ghi từng file mới ở gốc `docs/`. Bộ kiểm tài liệu đỏ với file chưa phân lớp hoặc đích catalog mất. Cổng điều hướng: [`docs/README.md`](docs/README.md).
- **Correction Layer:** Khi phát hiện báo cáo cũ có sai sót hoặc cần đính chính cách diễn giải, tạo một wave mới với lớp đính chính (correction layer) và đăng ký chuỗi `CORRECTED_BY` vào [`docs/EVIDENCE_INDEX.md`](docs/EVIDENCE_INDEX.md).
- **Tính trung thực của bằng chứng:**
  - Dữ liệu thiếu hoặc lỗi đo lường phải ghi rõ `UNKNOWN` hoặc `NOT_RECOVERABLE`, không được gán bằng `0`.
  - Không nâng mối tương quan (association) thành quan hệ nhân quả (causality).
  - Khẳng định `PROVED` bắt buộc phải có hash bằng chứng máy đi kèm.
- **Bảo mật & Tối giản:** Không lưu API key, token bí mật, traceback thô hoặc model output raw vào tài liệu hay git tree.
- **Đo lường có trần:** Mọi request live ra provider bên ngoài phải đăng ký trước ngân sách và luật dừng bắt buộc.
