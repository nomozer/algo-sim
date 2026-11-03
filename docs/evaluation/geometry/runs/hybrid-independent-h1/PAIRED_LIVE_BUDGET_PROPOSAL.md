# Đề Xuất Ngân Sách An Toàn & Ủy Quyền Chạy Live Bắt Cặp H-1 (`PAIRED_LIVE_BUDGET_PROPOSAL`)

**Chiến dịch đề xuất:** `H1_PAIRED_LIVE_EVALUATION` (`60` đề `H-1` × `2` nhánh `LLM_ONLY` và `HYBRID`) · **Model:** `gemini-2.5-flash` (Paid Tier) · **Trạng thái hiện tại:** `PENDING_OWNER_DECISION` (`0` HTTP requests đã gửi trong phiên này).

---

## 1. Nguyên Tắc Cách Ly Chiến Dịch & Ngân Sách (§IV & §VII)

1. **Chiến dịch độc lập hoàn toàn với C21 và C26:**
   - Chiến dịch C21 (`70 / 70` HTTP requests, `\$0.495793` upper) và chiến dịch C26 (`69 / 80` HTTP requests, `\$0.349913` / `\$1.00`) giữ nguyên sổ cái lịch sử bất biến từng byte.
   - Phần dư chưa dùng của C26 (`11` requests / `\$0.650087`) **tuyệt đối không được chuyển sang dùng cho `H-1`**, và ngân sách mới của `H-1` không được dùng để bù đắp bất kỳ chiến dịch cũ nào.
2. **Xác nhận trả phí không đồng nghĩa quyền chi tiêu mở:**
   - Chứng nhận `OWNER_ATTESTED` (`owner-paid-attestation.json`, `sha256 = e89153f5…`) chỉ xác nhận dự án Gemini của Owner thuộc gói trả phí (`paid_project_confirmed`), **không** cấp ngân sách cho chiến dịch mới.
3. **Một file phê duyệt = một lượt chạy live duy nhất:**
   - Bộ chạy [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) khóa cứng cơ chế `claim_approval()` (tạo tệp khóa `<approval>.consumed` độc quyền bằng `O_CREAT | O_EXCL` trước request đầu tiên). File phê duyệt đã tiêu thụ không bao giờ được tự động tái sử dụng hay reset.

---

## 2. Cơ Sở Telemetry Thực Nghiệm & Bảo Toàn Baseline `LLM_ONLY` (§IV.2 – §IV.3)

Đơn giá chuẩn của Google Gemini API cho `gemini-2.5-flash` (Paid Standard Tier, được xác minh cưỡng bức làm sàn tối thiểu trong `check_approval_terms()`):
- **Input tokens (kể cả cached prompt tokens ở cận bảo thủ):** `\$0.30 / 1,000,000 tokens`.
- **Output + Thinking tokens:** `\$2.50 / 1,000,000 tokens`.

### 2.1. Arm B — `HYBRID` (Dữ liệu thực tế từ 69 HTTP 200 của C26 trên `180db769`)

Nguồn: [`HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md`](../hybrid-live-extraction-retest/HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md) §14–16:
- **Số lời gọi / bài:** `0` HTTP nếu bị Domain Gate (`main._ngoai_pham_vi`) chặn sớm, hoặc **đúng `1` HTTP request** trích xuất (`TypedFactNextPayloadV2`, `maxOutputTokens = 8,192`, không có vòng gọi LLM lặp lại).
- **Trần đặt chỗ 1 request (`request_worst_case_usd`):** `8,192` output tokens × `\$2.50 / 1M` + prompt bound $\approx \mathbf{\$0.0215 / \text{request}}$.
- **Chi phí thực tế / lời gọi trên C26:** trung vị `\$0.00500`, trung bình **`\$0.005071`**, p90 `\$0.00702`, cực đại `\$0.01104`.
- **Ước tính cho 60 đề `H-1` trên `HYBRID`:** `55 – 60` requests danh định (tối đa `72` kể cả dự phòng retry `20%`) $\Rightarrow$ chi phí thực tế kỳ vọng **`\$0.28 – \$0.36`** (cận thận trọng p90 + retry: `~\$0.50`).

### 2.2. Arm A — `LLM_ONLY` (Bảo toàn nguyên trạng baseline production)

Nguồn: [`backend/app/ai/pipeline.py`](../../../../../backend/app/ai/pipeline.py) (`MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3`) và `TELEMETRY_BUDGET_LEDGER.json`:
- **Bảo toàn 100% hành vi `LLM_ONLY` (§IV.2):** Không sửa `backend/app/**`, không sửa prompt, không giảm số vòng `semantic_analyze` / `semantic_program`, và **không ép hạ `maxOutputTokens`** trên `LLM_ONLY` (giữ nguyên trần model `65,536` tokens cho mỗi lời gọi).
- **Trần đặt chỗ 1 request (`request_worst_case_usd`):** `65,536` output tokens × `\$2.50 / 1M` + prompt bound $\approx \mathbf{\$0.1693 / \text{request}}$.
- **Cấu trúc đa lời gọi / bài:** `0` call (nếu `detect_domain` chặn) hoặc `1` call `semantic_analyze` (`~\$0.00441/call`) + `1..3` calls `semantic_program` (`~\$0.00961 – \$0.013/call`).
- **Ước tính cho 60 đề `H-1` trên `LLM_ONLY`:** `145 – 165` requests danh định (tối đa đồ thị `240` trước retry) $\Rightarrow$ chi phí thực tế kỳ vọng **`\$1.20 – \$1.55`** (kịch bản nhiều vòng sửa `_prompt_sua` + retry: `~\$2.20 – \$2.80`).

---

## 3. Kiến Trúc Ngân Sách Mới `SafeCampaignBudget` (Thay Thế Cổng Nhân Cứng `\$52.00`)

### 3.1. Giải quyết bài toán ủy quyền tài chính quá mức mà không làm yếu trần chi tiêu

Ở phiên bản cũ, `check_approval_terms()` ép bất đẳng thức tĩnh `max_requests * worst_case_request_usd <= max_usd`, buộc phải ghi `max_usd = 52.00` ($300 \times \$0.1693 \approx \$50.79$) dù chi phí thực tế dự kiến chỉ `\$1.50 – \$2.00`.

Trong C27, [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) đã được thiết kế lại với lớp **`SafeCampaignBudget`** sử dụng số học thập phân chính xác **`decimal.Decimal`** (tránh hoàn toàn sai số làm tròn `float`) và khóa tương tranh **`threading.Lock`**:

1. **Sáu đại lượng kế toán tách biệt minh bạch (`budget_ledger`):**
   - `campaign_max_requests`: Tổng số HTTP requests tối đa được phép gửi (kể cả mọi lần retry).
   - `campaign_max_usd`: Tổng ngân sách tối đa được Owner phê duyệt cho chiến dịch.
   - `request_worst_case_usd`: Trần chi phí xấu nhất của chính payload chuẩn bị gửi (tính từ model thực tế, đơn giá token đã xác minh, cận trên prompt utf-8 bytes + `1,024` overhead và trần `maxOutputTokens` hoặc `65,536`).
   - `spent_usd`: Tổng chi phí đã quyết toán của các request đã hoàn tất.
   - `inflight_reserved_usd`: Tổng khoản dự phòng đang khóa cho các request đang bay trên mạng.
   - `remaining_usd`: Số dư ngân sách còn được phép cấp phát (`campaign_max_usd - spent_usd - inflight_reserved_usd`).
2. **Kiểm tra khả thi ở Preflight (trước request số 1):**
   - Xác minh `single_worst_case_request_usd <= campaign_max_usd` (`\$0.1693 <= \$5.00`), kiểm tra model và sàn đơn giá chuẩn của `gemini-2.5-flash`. Nếu không xác định được cận chi phí đáng tin cậy $\rightarrow$ **fail-closed** (`LiveRefused`).
3. **Cấp phát dự phòng nguyên tử TRƯỚC mỗi HTTP request (kể cả retry):**
   $$\texttt{spent\_usd} + \texttt{inflight\_reserved\_usd} + \texttt{request\_worst\_case\_usd} \le \texttt{campaign\_max\_usd}$$
   $$\texttt{actual\_http\_request\_count} + \texttt{inflight\_request\_count} < \texttt{campaign\_max\_requests}$$
   Nếu một trong hai điều kiện vi phạm, request bị chặn **trước khi chạm socket mạng** (`BudgetExceeded`).
4. **Quyết toán bảo thủ sau mỗi HTTP attempt:**
   - Chỉ khi nhận HTTP `200` kèm `usageMetadata` đầy đủ (`promptTokenCount` + `candidatesTokenCount` nguyên không âm, khớp quy tắc `thoughtsTokenCount` / `totalTokenCount`), hệ thống mới giải phóng phần chênh lệch và ghi nhận chi phí token thực tế (tính đủ giá cho cả cached tokens để không đánh giá thấp chi phí).
   - Nếu gặp **HTTP timeout, lỗi mạng, HTTP `400`/`429`/`500`, hoặc thiếu / khuyết một phần `usageMetadata`**, hệ thống quyết toán nguyên giá trị **`request_worst_case_usd`** vào `spent_usd` (**tuyệt đối không bao giờ hạch toán `\$0`** và không giải phóng nhầm khoản dự phòng).

### 3.2. Bảng tổng hợp hạn mức đề xuất chờ Owner phê duyệt (`PENDING_OWNER_DECISION`)

| Hạng mục | Arm B (`HYBRID`) | Arm A (`LLM_ONLY`) | Đề xuất toàn chiến dịch `H-1` (`60` cặp) |
|---|---:|---:|---:|
| Số đề đánh giá | `60` | `60` | `60` cặp (`120` lượt đánh giá cấp bài) |
| HTTP calls danh định (không lỗi mạng) | `55 – 60` | `145 – 165` *(tối đa đồ thị: `240`)* | **`200 – 225` requests** |
| Dự phòng retry HTTP `429`/`5xx` | `+12` | `+25 – 40` | `+35 – 55` requests |
| Trần đặt chỗ 1 request (`request_worst_case_usd`) | `~\$0.0215` | `~\$0.1693` | Kiểm tra động trước từng request |
| **Đề xuất `campaign_max_requests`** | — | — | **`300` HTTP requests** |
| **Chi phí thực tế dự kiến (Expected Spend)** | **`\$0.28 – \$0.36`** | **`\$1.20 – \$1.55`** | **`\$1.50 – \$2.00`** *(p95 thực tế `< \$3.50`)* |
| **Đề xuất `campaign_max_usd`** | — | — | **`\$5.00`** *(thay thế hoàn toàn mức `\$52.00` cũ)* |

> [!NOTE]
> **Hành vi dừng an toàn nếu `LLM_ONLY` lặp sửa quá nhiều:**
> Với `campaign_max_usd = \$5.00` (cao gấp `~2.5–3.3×` mức chi thực tế dự kiến `\$1.50 – \$2.00`), chiến dịch dư sức hoàn thành toàn bộ 60 cặp trong điều kiện bình thường mà Owner không phải ủy quyền `\$52.00`. Trong trường hợp bất thường `LLM_ONLY` kích hoạt quá nhiều vòng sửa lỗi/retry hoặc gặp hàng loạt lỗi thiếu `usageMetadata` khiến `spent_usd` tiến sát trần (hoặc chạm ngưỡng dừng sớm `80%` = `\$4.00`), bộ chạy sẽ **dừng an toàn trước khi vượt trần**, ghi `run_status = "INCOMPLETE_PAIRED_EVALUATION"`, `paired_live_evaluation_complete = "NO"`, báo cáo chính xác số cặp đã hoàn tất và giữ phán quyết `HYBRID_CUTOVER_NO_GO` (không tự tăng trần, không kết luận GO trên mẫu thiếu).

---

## 4. Luật Dừng Bắt Buộc (`Stop Rules`) Đã Kiểm Chứng Bằng 14 Nhóm Test (`test_paired_live_safe_budget.py`)

1. **Dừng an toàn tức thì trên nhánh `HYBRID` (`SERVED_EXPECTED_REFUSAL`):** Nếu `HYBRID` phục vụ (`status == "ok"`) bất kỳ đề nào có `expect != "SERVE"`, nhánh `HYBRID` dừng ngay lập tức; nhánh `LLM_ONLY` ghi nhận độc lập theo quy tắc A2.
2. **Trần số lượng request trước khi gửi (`REQUEST_CAP`):** Chặn cứng ngay trước khi gửi request thứ `campaign_max_requests + 1` (`301`), tính cả mọi lần retry.
3. **Trần chi phí nguyên tử trước khi gửi (`COST_CEILING` & `USD_80_PERCENT`):** Chặn cứng trước khi gửi nếu `spent_usd + inflight_reserved_usd + request_worst_case_usd > campaign_max_usd`; dừng sớm sau mỗi arm nếu `spent_usd >= 0.80 * campaign_max_usd` (`\$4.00`).
4. **Chuỗi lỗi hạ tầng (`INFRASTRUCTURE_STREAK` / `PROVIDER_BLOCK`):** Dừng ngay nếu có `3` lỗi kỹ thuật liên tiếp sau khi đã retry hoặc gặp provider block (`401`/`403`/billing).
5. **Biến động danh tính (`IDENTITY_CHANGED`):** Dừng ngay nếu `measured_system`, `cache_version`, `model`, `skills_sha256` hoặc `paired_harness_sha256` thay đổi giữa chừng.

---

## 5. Quy Trình Kích Hoạt Tự Động Một Bước Khi Đủ Hai Đầu Vào Từ Owner

Mẫu cấu hình chờ duyệt tại [`paired-live-owner-approval.template.json`](paired-live-owner-approval.template.json) đang để `"owner_decision": "PENDING_OWNER_DECISION"`, `"paid_project_confirmed": false`, `"campaign_max_requests": 300`, `"campaign_max_usd": 5.0` (agent tuyệt đối không tự ký phê duyệt).

Khi Owner cung cấp:
1. File bộ đề độc lập `docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json` (từ tác giả con người độc lập kèm dẫn xuất oracle), và
2. File phê duyệt `docs/evaluation/geometry/runs/hybrid-independent-h1/paired-live-owner-approval.json`,

trình tự thực thi tự động xuyên suốt gồm đúng 3 lệnh:

```powershell
# Bước 1: Kiểm tra định dạng, quét nhiễm & khung đề toàn repo, xác minh độc lập tác giả và ghi corpus_sha256 + oracle_sha256 (0 live call)
.\backend\.venv\Scripts\python.exe backend/scripts/score_independent_holdout_equivalence.py integrity `
  --corpus docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json `
  --out docs/evaluation/geometry/runs/hybrid-independent-h1/H1_CORPUS_INTEGRITY.json

# Bước 2: Chạy manifest preflight của paired harness để đối chiếu runtime_identity & contamination (0 live call)
.\backend\.venv\Scripts\python.exe backend/scripts/run_paired_route_evaluation.py `
  --corpus docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json `
  --manifest

# Bước 3: Thực thi tự động toàn bộ chiến dịch Paired Live (chỉ chạy sau khi Owner cấp paired-live-owner-approval.json hợp lệ)
$env:ALLOW_LIVE_AI = "1"
.\backend\.venv\Scripts\python.exe backend/scripts/run_paired_route_evaluation.py `
  --corpus docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json `
  --approval-file docs/evaluation/geometry/runs/hybrid-independent-h1/paired-live-owner-approval.json `
  --live `
  --out docs/evaluation/geometry/runs/hybrid-independent-h1/h1-paired-live-results.jsonl
```
