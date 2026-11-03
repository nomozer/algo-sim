# Continuation 21 — Ủy quyền thực thi tự động (`EXPLICIT_OWNER_DELEGATED_EXECUTION`) và kiểm chứng cổng Live Hybrid

**Kết luận thực thi:** `DELEGATED_AUTOMATION_READY_AND_VERIFIED` · **Live execution:** `BLOCKED_PREFLIGHT` tại **`PAID_PROJECT_NOT_VERIFIED`** (`0` HTTP requests gửi tới Gemini, `USD 0.00`).

Thao tác PowerShell thủ công cho từng pilot đã được loại bỏ hoàn toàn: một lệnh duy nhất `--delegated-c21` trong `backend/scripts/run_s2_student_language_pilot.py` nay tự động kiểm tra candidate/corpus/template, đọc cấu hình từ môi trường hoặc `backend/.env` gốc trong bộ nhớ, xác minh điều kiện paid project, phát hành approval ủy quyền (`DELEGATED_BY_EXPLICIT_OWNER_INSTRUCTION`, không bao giờ mạo danh `APPROVED_BY_USER`), và chạy tuần tự `K-1 → S-2 → R-1` dưới kiểm soát ngân sách hai tầng (`70` requests / `USD 4.00`) tại thư mục chiến dịch dùng chung. Trong môi trường hiện tại, runner đã dừng chính xác trước request đầu tiên với mã `PAID_PROJECT_NOT_VERIFIED` theo đúng Mục I & IV của chỉ thị Continuation 21 (chỉ thị ủy quyền không tự xác nhận paid project, và máy thực thi không có `GOOGLE_CLOUD_PROJECT` / Cloud Billing OAuth hoặc tuyên bố xác nhận paid riêng của Owner).

---

## 1. Candidate và Git identity

- **Repository / Worktree:** `D:\Documents\projects\algo-sim\.superpowers\worktrees\hybrid-master-backend-replacement`
- **Branch:** `research/hybrid-master-backend-replacement` (baseline đầu phiên C21: `3a70f9f19116e9b689a418e8764231c2b2285dc8`)
- **Frozen Candidate:** `15d236eb` · **Product commit:** `51ba6135a76e1daf761c021ce5c03de34acbae62` (**không thay đổi product code**, không chạy lại Full T3)
- **Measured system (`118` files):** `3711d4eeee260ffdbe50871c59b66922d470c99908eead729810c473d6ef8773` (`freeze_evaluation_candidate.py --verify` → `MATCH`)
- **Contract / Engine versions:** Registry `/31`, Planner `/26`, Engine `/22`, Adapter `/4`, `TypedFactNext` `/2`, `CACHE_VERSION = 131`, `DEFAULT_MODE = LLM_ONLY`
- **Tooling / Harness hashes (C21):**
  - `runner_sha256` (`backend/scripts/run_s2_student_language_pilot.py`): `8691bf113b57a78094bd7738719cfdf2f0ec2dfcd0631687afaf7e4798213423` (làm mới từ `e3d3b2ec…` của C19 do bổ sung `EXPLICIT_OWNER_DELEGATED_EXECUTION`, kiểm chứng paid project và ngân sách hai tầng)
  - `paired_harness_sha256`: `2ac9577ff68e15ebdf345577bea20ae4116ce26654b64d63e82b92b7619e5ada` (giữ nguyên)
  - `scorer_sha256`: `8c330bd493f9d401f579b6383f1a1df2bc9172eee2530cf187be2024801b5a2d` (giữ nguyên)

## 2. Owner authorization source và phạm vi

- **Authorization mode:** `EXPLICIT_OWNER_DELEGATED_EXECUTION`
- **Authorization source:** `EXPLICIT_OWNER_INSTRUCTION` (`directive_id = CONTINUATION_21_MASTER_DIRECTIVE`, quyết định ghi máy `DELEGATED_BY_EXPLICIT_OWNER_INSTRUCTION` tuân thủ `AGENTS.md §4`: tự động hóa không bao giờ ghi chuỗi dành riêng cho thao tác tay của người dùng; đường CLI đơn lẻ `--live` từ chối mọi file ủy quyền để bắt buộc đi qua `--delegated-c21` dưới sổ cái tổng)
- **Phạm vi được ủy quyền (`LIVE_DEVELOPMENT_PILOT`):**
  - `K-1`: tối đa `16` HTTP requests, trần `USD 1.00`
  - `S-2`: tối đa `36` HTTP requests, trần `USD 2.00`
  - `R-1`: tối đa `18` HTTP requests, trần `USD 1.00`
- **Tổng trần toàn chiến dịch C21:** `MAX_TOTAL_REQUESTS = 70`, `MAX_TOTAL_SPEND_USD = 4.00` (mọi retry tính vào cả trần từng pilot lẫn trần tổng; khóa độc quyền nguyên tử `.lock` + sổ cái bền `c21-global-budget-ledger.json` gắn cố định vào thư mục chiến dịch của 3 template, ghi nhận đầy đủ cả khi bị ngắt giữa chừng, chặn hai tiến trình hoặc hai `--out-dir` nhân đôi ngân sách)
- **Model được ủy quyền duy nhất:** `gemini-2.5-flash` (không fallback)
- **Phạm vi bị loại trừ cứng (runner từ chối bằng code):** `H-1` (`INDEPENDENT_HYBRID_EVALUATION`), chuyển đổi chế độ mặc định production (`DEFAULT_MODE`), và `merge`/`push`.

## 3. Paid-project verification

- **Kết quả kiểm chứng:** **`PAID_PROJECT_NOT_VERIFIED`** (`verified = false`)
- **Receipt kiểm toán:** `c21-delegated-attempt/c21-delegated-execution-receipt.json` (`sha256 = 356fafb9a0035ef99c634230a09f2bcd1e3b615af0db91b499a20b3468cad522`)
- **Các nguồn đã kiểm tra an toàn (không in / sao chép / lưu secret):**
  1. `D:\Documents\projects\algo-sim\backend\.env` tại checkout gốc: có mặt `GEMINI_API_KEY` (định dạng khóa Google AI Studio `AQ.…`, nạp chỉ trong bộ nhớ; đã vá thêm `check_publication_safety.py` và `redact_secrets()` để chặn rò rỉ cả khóa `AQ.…` lẫn Google OAuth token `ya29.…`). Google `generativelanguage.googleapis.com` không có bất kỳ endpoint hay response header nào cho biết project gắn với API key thuộc gói Paid hay Free Tier (nơi Google lưu/duyệt nội dung prompt theo `provider-facts.md`).
  2. Google Cloud Billing API (`cloudbilling.googleapis.com/v1/projects/{project}/billingInfo`): biến môi trường và `.env` đều không có `GOOGLE_CLOUD_PROJECT` / `GCP_PROJECT` hay `GOOGLE_OAUTH_ACCESS_TOKEN`; máy không cài `gcloud` và không có Application Default Credentials (`ADC`).
  3. Tuyên bố xác nhận riêng của Owner (`owner-paid-project-attestation/1`): chưa có; Mục I của chỉ thị Continuation 21 nêu rõ *“Tôi không xác nhận chỉ bằng prompt này rằng một paid project đã được bật. Agent phải xác minh điều đó bằng nguồn đáng tin cậy hoặc có một tuyên bố Owner riêng xác nhận rõ ràng. Không được đặt `paid_project_confirmed = true` chỉ vì có API key hoặc file `.env`.”* (`verify_paid_project()` cũng từ chối cứng mọi attestation tự viện dẫn chính `CONTINUATION_21_MASTER_DIRECTIVE`).
- Do đó, `verify_paid_project()` trả về `PAID_PROJECT_NOT_VERIFIED` và chặn toàn bộ chuỗi thực thi trước request đầu tiên.

## 4. Model availability

- **Trạng thái live:** `NOT_MEASURED_PRE_REQUEST_GATE_BLOCKED` (`0` HTTP requests gửi ra ngoài do cổng `PAID_PROJECT_NOT_VERIFIED` chặn trước request số 1).
- **Kiểm chứng cấu hình và bảo vệ mã nguồn:** `app.ai.gemini.MODEL == "gemini-2.5-flash"`; `_guard_pilot_sends` khóa cứng URL `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent`, từ chối mọi model khác (`UNAUTHORIZED_ENDPOINT_OR_MODEL`), phân loại HTTP `404` / lỗi model `400`/`403` thành `PROVIDER_MODEL_UNAVAILABLE` để dừng ngay toàn chuỗi mà không chuyển sang model dự phòng, và chỉ ghi `VERIFIED_LIVE` khi có ít nhất một phản hồi live thành công (`live_answered_rows > 0`).

## 5. Các approval được tạo

- **Approval thực thi được tạo trên đĩa trong phiên live attempt:** **`0` file** (`approvals_created = []` trong `c21-delegated-execution-receipt.json`, vì `issue_delegated_approval()` từ chối phát hành file khi `paid_verification.verified != true`).
- **Làm mới các approval templates theo `runner_sha256` mới (`8691bf11…`, Mục III):**
  - `k1-owner-approval.template.json`: blob C19 `a6ccbf2e572489ce845582a2968adb7b97647c31` (đã xác minh khớp trước khi cập nhật) → blob C21 **`ee581d674cbc578731422f58c2b6376b24198cfe`** (`corpus_sha256 = 6eeab278…`, `16` req / `USD 1.00`)
  - `s2-owner-approval.template.json`: blob C19 `05f2a5463d0ab63964cde93f05a8c377b70f0411` (đã xác minh khớp trước khi cập nhật) → blob C21 **`528622dda95180b022ab0c0580a0ebf04dc83d19`** (`corpus_sha256 = 3f1682bd…`, `36` req / `USD 2.00`)
  - `r1-owner-approval.template.json`: blob C19 `71792f77918ab6cd1dec3164cd07813ea55fb986` (đã xác minh khớp trước khi cập nhật) → blob C21 **`f20279a96e6dd0ac71a4526e7f0333209b811707`** (`corpus_sha256 = 250466eb…`, `18` req / `USD 1.00`)
  - Cả 3 template giữ nguyên `"owner_decision": "PENDING_OWNER_DECISION"` và `"paid_project_confirmed": false`, đồng thời được kiểm tra đầy đủ ở preflight (`pilot`, trạng thái pending, hạn mức và `runtime_identity()`) và khóa tự động qua pytest.

## 6. Request count theo pilot

- **K-1:** `0` / `16` (`NOT_MEASURED` — dừng ở preflight `PAID_PROJECT_NOT_VERIFIED`)
- **S-2:** `0` / `36` (`NOT_MEASURED` — dừng ở preflight `PAID_PROJECT_NOT_VERIFIED`)
- **R-1:** `0` / `18` (`NOT_MEASURED` — dừng ở preflight `PAID_PROJECT_NOT_VERIFIED`)

## 7. Actual USD spend theo pilot

- **K-1:** `USD 0.00` (`spent_reported_usd = NOT_MEASURED`, trần `USD 1.00`)
- **S-2:** `USD 0.00` (`spent_reported_usd = NOT_MEASURED`, trần `USD 2.00`)
- **R-1:** `USD 0.00` (`spent_reported_usd = NOT_MEASURED`, trần `USD 1.00`)

## 8. Tổng requests và USD

- **Tổng HTTP requests đã gửi:** `0` / `70`
- **Tổng chi phí bảo lưu cận trên (`total_spent_upper_usd`):** `USD 0.00` / `USD 4.00`
- **Tổng chi phí báo cáo từ usage (`total_spent_reported_usd`):** `NOT_MEASURED` (quy tắc hạch toán đảm bảo mọi response thiếu `promptTokenCount > 0`, thiếu token đầu ra, hoặc có retry một phần khiến `reported_calls < row_requests` đều ghi `row["usd"] = UNKNOWN` / `spent_reported_usd = UNKNOWN` và trừ nguyên `request_ceiling_usd` cho mọi lượt không có usage trên cận trên `usd_upper`, không bao giờ tính `0.0`).

## 9. K-1 measured results

- **`NOT_MEASURED`** (`16/16` ca chưa chạy live do cổng `PAID_PROJECT_NOT_VERIFIED` chặn trước request đầu tiên; không báo lại trần gold offline làm kết quả đo live).

## 10. S-2 measured results

- **`NOT_MEASURED`** (`36/36` ca chưa chạy live do cổng `PAID_PROJECT_NOT_VERIFIED` chặn trước request đầu tiên).

## 11. R-1 measured results

- **`NOT_MEASURED`** (`18/18` ca chưa chạy live do cổng `PAID_PROJECT_NOT_VERIFIED` chặn trước request đầu tiên).

## 12. Extraction accuracy

- **`NOT_MEASURED`** (chưa có response live từ `gemini-2.5-flash`).

## 13. Goal completeness

- **`NOT_MEASURED`** trên đường live.

## 14. False refusals

- **`NOT_MEASURED`** trên đường live.

## 15. Wrong-served

- **`NOT_MEASURED`** trên đường live.

## 16. Correct clarifications

- **`NOT_MEASURED`** trên đường live.

## 17. Constraint extraction

- **`NOT_MEASURED`** trên đường live (`K-1` chưa gửi request).

## 18. Described-point extraction

- **`NOT_MEASURED`** trên đường live (`R-1` và `K-1` chưa gửi request).

## 19. Orthocenter/circumcenter extraction

- **`NOT_MEASURED`** trên đường live (`K-1` chưa gửi request).

## 20. Kernel verification

- **`NOT_MEASURED`** trên đầu ra trích xuất live (không thay đổi Exact Geometry Kernel `/22` so với candidate `15d236eb`).

## 21. Scene3D contract

- **`NOT_MEASURED`** trên đầu ra trích xuất live (không thay đổi Adapter `/4` hay hợp đồng Scene3D so với candidate `15d236eb`).

## 22. Latency

- **`NOT_MEASURED`** (không có lượt gọi mạng tới Gemini API).

## 23. Failure attribution

- **Tầng dừng của phiên C21:** `INFRASTRUCTURE` / `AUTHORIZATION_PREFLIGHT` — mã dừng chính xác **`PAID_PROJECT_NOT_VERIFIED`** trước request thứ nhất (`0` ca thất bại sản phẩm, `0` ca quy lỗi cho `DOMAIN_GATE`, `LLM_EXTRACTION`, `TYPEDFACTNEXT`, `SOURCE_GATE`, `FACTGRAPH`, `PLANNER`, `COMPILER`, `ENGINE`, `EXACT_KERNEL`, hay `ADAPTER`).

## 24. Independent review

- **Reviewer:** Fresh-context `research` subagent (`Independent Continuation 21 Adversarial Reviewer`, chế độ chỉ đọc, không mở `backend/.env`).
- **Round 1:** `NOT_READY` (`0 BLOCKER`, `4 MAJOR`, `4 MINOR`, `2 NIT`):
  - `MAJOR-1`: đường CLI `--live --approval-file` và `evaluate(..., global_budget=None)` chấp nhận file ủy quyền ngoài `--delegated-c21`, bỏ qua `GlobalBudgetLedger` và `.consumed` per-send → đã khóa cứng (`authorize_live(..., allow_delegated=False)` mặc định, `evaluate()` bắt buộc `global_budget` cho mọi approval ủy quyền, `main()` truyền `approval_path=a.approval_file`).
  - `MAJOR-2`: `GlobalBudgetLedger` đặt theo `--out-dir` và mất ghi nhận khi ngắt giữa chừng → đã chuyển mặc định `ledger_dir` về thư mục chiến dịch của 3 template (không có cờ CLI ghi đè), bổ sung kiểm tra nguyên tử `FileExistsError` trong `acquire()`, cập nhật `finish_pilot` trong `evaluate()` `finally:` (kể cả request đang bay `in_arm`), và ghi `c21-delegated-execution-receipt.json` (`status = INTERRUPTED`) trong `run_delegated_c21_suite` `finally:`.
  - `MAJOR-3`: retry tạm thời một phần (`503 -> 200` có usage) tính `row["usd"]` theo lượt 2 (ngầm gán `0.0` cho lượt 1) → đã yêu cầu `reported_calls == row_requests` mới công nhận `verified_usage`; nếu thiếu usage của bất kỳ lượt nào thì `row["usd"] = "UNKNOWN"` và `spent_reported_usd = "UNKNOWN"`, trong khi `usd_upper` vẫn tính đủ trần cho lượt thiếu.
  - `MAJOR-4`: `model_availability` ghi `VERIFIED_LIVE` cả khi 100% request lỗi mạng/400/5xx → đã sửa để chỉ ghi `VERIFIED_LIVE` khi `live_answered_rows > 0`.
  - `MINOR-1..4` & `NIT-1..2`: bổ sung chặn/che `ya29.…` và `GOOGLE_OAUTH_ACCESS_TOKEN` trong `check_publication_safety.py` + `redact_secrets()`; chặn attestation tự dẫn chiếu `CONTINUATION_21_MASTER_DIRECTIVE`, chuẩn hóa `project_id` + đường dẫn tương đối `attestation_path`; kiểm tra đầy đủ trường template ngay tại preflight; cập nhật đồng bộ tài liệu trạng thái / `EVIDENCE_INDEX.md` (`CORRECTED_BY` trên C19); bỏ ghép chuỗi thừa trong test và ghi rõ giả định gắn kết `GOOGLE_CLOUD_PROJECT` ở §28 Cách B.
- **Round 2:** **`READY` (`0 BLOCKER`, `0 MAJOR`, `0 MINOR`, `0 NIT`)** — toàn bộ `10/10` phát hiện của vòng 1 được xác nhận đã đóng hoàn toàn qua kiểm toán độc lập chỉ đọc (`freeze_evaluation_candidate.py --verify` → `MATCH`, `214 passed` pytest, đối chiếu trực tiếp SHA-256/Git blob của runner `8691bf11…`, 3 templates `ee581d67…`/`528622dd…`/`f20279a9…`, receipt `356fafb9…`, và `0` phát hiện trong `check_publication_safety.findings_in()`).

## 25. Product improvement recommendations

- **`NONE_WITHOUT_LIVE_EVIDENCE`:** Tuân thủ Mục VIII (*không tự động tune product trước khi có dữ liệu đo baseline live*). Không đề xuất chỉnh sửa Source Gate, `TypedFactNext`, Planner, Registry, Engine hay Gemini prompt khi chưa có phân phối lỗi thực tế từ `K-1`, `S-2`, `R-1`.

## 26. H-1 readiness

- **Trạng thái:** `NOT_AUTHORIZED_IN_C21` · `AWAITING_INDEPENDENT_AUTHOR`
- Giao thức `hybrid-only-independent-evaluation/1` và cổng kiểm tra trong runner đã sẵn sàng, đồng thời `_check_delegated_terms()` từ chối cứng `H-1` dưới chế độ `EXPLICIT_OWNER_DELEGATED_EXECUTION`. Để đo `H-1` cần một tác giả độc lập do Owner chỉ định và một phê duyệt riêng của Owner cho hash corpus `H-1`.

## 27. Git status

- **Branch:** `research/hybrid-master-backend-replacement` (không merge vào `main`, không push, không xóa nhánh/worktree).
- **Product freeze (`EVALUATION_CANDIDATE.json`):** `MATCH` (`3711d4eeee260ffdbe50871c59b66922d470c99908eead729810c473d6ef8773`, `118` files; `DEFAULT_MODE = LLM_ONLY`, `CACHE_VERSION = 131`, Adapter `/3`, Compiler C và `frontend/` hoàn toàn không chạm).
- **Thay đổi trong C21 (chỉ hạ tầng đánh giá, kiểm thử an toàn và tài liệu):**
  - `backend/scripts/run_s2_student_language_pilot.py`
  - `backend/scripts/check_publication_safety.py`
  - `backend/tests/geometry/test_s2_student_language_pilot_runner.py`
  - `backend/tests/test_publication_safety_gate.py`
  - Làm mới `runner_sha256` trong `{k1,s2,r1}-owner-approval.template.json`
  - Receipt preflight `c21-delegated-attempt/c21-delegated-execution-receipt.json`, báo cáo này (`hybrid-live-validation-c21.md`) và cập nhật các tài liệu trạng thái/chỉ mục (`HYBRID_MASTER_EPIC_CURRENT_STATE.md`, `owner-go-request.md`, `docs/CURRENT_STATE.md`, `docs/CODE_INDEX.md`, `docs/EVIDENCE_INDEX.md`).
- **Publication safety scan:** toàn bộ tệp C21 trên cây làm việc đạt `0` vi phạm theo `check_publication_safety.findings_in()` + `audit_secret_scan()`, không có bản sao `.env` trong worktree; cổng đối tượng Git `check_publication_safety.py --range f986e897..HEAD` được chạy xác nhận trực tiếp ngay sau bước commit allowlist C21.

## 28. Remaining Owner decisions

1. **Mở khóa cổng `PAID_PROJECT_NOT_VERIFIED` để kích hoạt chạy tự động `K-1 → S-2 → R-1` (không cần bất kỳ lệnh PowerShell tạo JSON nào):** chỉ cần chọn **một trong hai** cách sau:
   - **Cách A (nhanh nhất — xác nhận bằng lời trong tin nhắn kế tiếp):** gửi một câu xác nhận riêng rõ ràng của Owner rằng project gắn với `D:\Documents\projects\algo-sim\backend\.env` đã bật Paid Cloud Billing (agent sẽ ghi tệp đối chiếu `owner-paid-project-attestation/1` trích dẫn nguyên văn thông điệp đó và chạy thẳng `--delegated-c21 --paid-attestation ...` cho trọn chuỗi `K-1 → S-2 → R-1`), **hoặc**
   - **Cách B (xác minh tự động qua API):** bổ sung `GOOGLE_CLOUD_PROJECT=<project-id>` (chính là GCP project đã phát hành `GEMINI_API_KEY`; lưu ý `CLOUD_BILLING_API` xác minh `billingEnabled == true` trên project được khai báo đó vì REST API công khai của Google không tự giải mã ánh xạ từ chuỗi khóa `AQ.`/`AIza` sang `project_id`) cùng quyền đọc Cloud Billing (`gcloud auth application-default login` hoặc `GOOGLE_OAUTH_ACCESS_TOKEN` có quyền `cloudbilling.projects.getBillingInfo`).
2. **Đánh giá độc lập `H-1`:** chỉ định tác giả độc lập xây dựng corpus `H-1` (13 nhóm) và cấp phê duyệt riêng sau khi có corpus.
3. **Các quyết định sản phẩm / tích hợp đang treo từ C19:** mở rộng văn phạm Source Gate cho `R1-G01`/`R1-G02` (chỉ xét sau khi có kết quả live), đóng tuyên bố discovery trong khóa luận, và quyết định tích hợp nhánh nghiên cứu (`INTEGRATION_PENDING_OWNER_GO`).
