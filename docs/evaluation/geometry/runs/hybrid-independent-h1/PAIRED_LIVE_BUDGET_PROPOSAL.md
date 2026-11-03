# Đề Xuất Ngân Sách & Ủy Quyền Chạy Live Bắt Cặp H-1 (`PAIRED_LIVE_BUDGET_PROPOSAL`)

**Chiến dịch đề xuất:** `H1_PAIRED_LIVE_EVALUATION` (`60` đề `H-1` × `2` nhánh `LLM_ONLY` và `HYBRID`) · **Model:** `gemini-2.5-flash` (Paid Tier) · **Trạng thái hiện tại:** `AWAITING_OWNER_CORPUS_AND_BUDGET_GO` (`0` HTTP requests đã gửi trong phiên này).

---

## 1. Nguyên Tắc Cách Ly Chiến Dịch & Ngân Sách (§VI)

1. **Chiến dịch độc lập hoàn toàn với C21 và C26:**
   - Chiến dịch C21 (`70 / 70` HTTP requests, `$0.495793` upper) và chiến dịch C26 (`69 / 80` HTTP requests, `$0.349913` / `$1.00`) giữ nguyên sổ cái lịch sử bất biến.
   - Phần dư chưa dùng của C26 (`11` requests / `$0.650087`) **tuyệt đối không được tự ý chuyển sang dùng cho `H-1`**.
2. **Xác nhận trả phí không đồng nghĩa quyền chi tiêu mở:**
   - Chứng nhận `OWNER_ATTESTED` (`owner-paid-attestation.json`, `sha256 = e89153f5…`) chỉ xác nhận tài khoản API của Owner thuộc gói trả phí, **không** cấp ngân sách cho chiến dịch mới.
3. **Một file phê duyệt = một lượt chạy live duy nhất:**
   - Bộ chạy [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) khóa cứng cơ chế `claim_approval()` (tạo `<approval>.consumed` độc quyền trước request đầu tiên). Không tự động chạy lại bằng cùng một file phê duyệt nếu lượt chạy bị ngắt giữa chừng.

---

## 2. Cơ Sở Telemetry Thực Nghiệm Cho Hai Nhánh

Đơn giá chuẩn của Google Gemini API cho `gemini-2.5-flash` (Paid Standard Tier, xác minh từ telemetry thực tế):
- **Input tokens:** `$0.30 / 1,000,000 tokens`.
- **Output + Thinking tokens:** `$2.50 / 1,000,000 tokens`.

### 2.1. Arm B — `HYBRID` (Dữ liệu thực tế từ 69 HTTP 200 của C26 trên `180db769`)

Nguồn: [`HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md`](../hybrid-live-extraction-retest/HYBRID_LIVE_EXTRACTION_RETEST_REPORT.md) §14–16:
- **Số lời gọi / bài:** `0` HTTP nếu bị Domain Gate (`main._ngoai_pham_vi`) chặn sớm (các bài ngoài miền không chứa từ khóa hình học), hoặc **đúng `1` HTTP request** cho mọi bài còn lại (không có vòng gọi LLM lặp lại).
- **Token trung bình / lời gọi:** `2,575.3` prompt tokens · `634.4` output tokens · `1,085.0` thinking tokens (tổng `4,294.7` tokens/call; p90 `5,106`; max `6,656`).
- **Chi phí thực tế / lời gọi:** trung vị `$0.00500`, trung bình **`$0.005071`**, p90 `$0.00702`, cực đại `$0.01104`.
- **Ước tính cho 60 đề `H-1` trên `HYBRID`:**
  - Số HTTP calls danh định: **`55 – 60` requests** (tùy bao nhiêu trong 5 đề `OUT_OF_DOMAIN` đi qua Domain Gate từ khóa).
  - Dự phòng retry lỗi mạng/429 tạm thời (`20%`): **`+12` requests** $\Rightarrow$ tối đa **`72` requests**.
  - Chi phí thực tế kỳ vọng của Arm B: **`$0.28 – $0.36`** (cận thận trọng p90 + retry: `~$0.50`).

### 2.2. Arm A — `LLM_ONLY` (Dữ liệu từ đồ thị lời gọi `pipeline.py` & `TELEMETRY_BUDGET_LEDGER.json`)

Nguồn: [`backend/app/ai/pipeline.py`](../../../../../backend/app/ai/pipeline.py) (`MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3`) và sổ cái telemetry live `LLM_ONLY` đã ghi nhận trong kho (`thesis-final-20260908T160224Z/TELEMETRY_BUDGET_LEDGER.json`):
- **Cấu trúc đa lời gọi trên mỗi bài (không phải 1 đề = 1 HTTP request):**
  1. Nếu `detect_domain` chặn ngoài miền phi hình học (`0..5` bài): `0` HTTP request.
  2. **Bước 1 — `stage_semantic_analyze` (`1` HTTP call / bài qua cổng miền):** trung bình `1,242.3` prompt tokens, `433.6` output tokens, `1,182.0` thinking tokens $\Rightarrow$ **`~$0.00441` / call**. Nếu bước này trả về `out_of_scope` / `not_simulation_suitable` (thường gặp trên một phần trong 15 bài `REFUSE`), pipeline dừng tại đây (`1` call).
  3. **Bước 2 — `stage_semantic_program` (`1` đến `3` HTTP calls tuần tự / bài đi tiếp):**
     - Lần gọi tổng hợp đầu tiên: trung bình `3,830.0` prompt tokens, `1,048.8` output tokens, `2,336.0` thinking tokens $\Rightarrow$ **`~$0.00961` / call**.
     - Nếu chương trình sinh ra trượt validator hình học/cú pháp, `run_pipeline` gọi tiếp `_prompt_sua` tối đa **2 lần sửa nữa** (tổng tối đa `3` lời gọi `semantic_program` / bài; prompt sửa dài ~`4,800` tokens $\Rightarrow$ **`~$0.011 – $0.013` / lần sửa**).
- **Ước tính cho 60 đề `H-1` trên `LLM_ONLY`:**
  - Bước `semantic_analyze`: **`55 – 60` HTTP calls** (`~$0.24 – $0.27`).
  - Bước `semantic_program` (trên 45 bài `SERVE` + các bài `CONTRADICTORY_DATA` / `MISSING_DATA` lọt qua `analyze`, tính cả tỉ lệ vòng sửa `_prompt_sua` thực tế $1.8\times$ – $2.1\times$): **`90 – 110` HTTP calls** (`~$0.95 – $1.25`). *(Trần lý thuyết đồ thị lời gọi nếu mọi bài đều chạy đủ 1 analyze + 3 program là `60 × 4 = 240` lời gọi trước retry).*
  - Cộng dự phòng retry tạm thời (`~15%`): tổng Arm A kỳ vọng **`145 – 165` HTTP calls** (ngân sách tối đa cấp cho Arm A trong tổng trần: tới `228` requests).
  - Chi phí thực tế kỳ vọng của Arm A: **`$1.20 – $1.55`** (kịch bản nhiều vòng sửa/retry: `~$2.20 – $2.80`).

---

## 3. Bảng Tổng Hợp Ngân Sách Đề Xuất Cho Phê Duyệt Của Owner

| Hạng mục | Arm B (`HYBRID`) | Arm A (`LLM_ONLY`) | Tổng chiến dịch Bắt cặp (`H-1`, 60 đề) |
|---|---:|---:|---:|
| Số đề đánh giá | `60` | `60` | `60` cặp (`120` lượt đánh giá cấp bài) |
| HTTP calls danh định (không lỗi mạng) | `55 – 60` | `145 – 165` *(tối đa đồ thị: `240`)* | **`200 – 225` requests** |
| Dự phòng retry HTTP `429`/`5xx` | `+12` | `+25 – 40` | `+35 – 55` requests |
| **Trần cứng `max_requests` đề xuất** | — | — | **`300` HTTP requests** |
| **Chi phí thực tế dự kiến (Expected Spend)** | **`$0.28 – $0.36`** | **`$1.20 – $1.55`** | **`$1.50 – $2.00`** *(p95 thực tế `< $3.50`)* |
| Trần đặt chỗ kỹ thuật `max_usd` trong JSON | — | — | **`$52.00`** *(xem giải trình bắt buộc ở Mục 3.1)* |
| Cảnh báo chi tiêu thực tế trên Cloud Billing | — | — | Khuyến nghị đặt alert ngoài ở **`$5.00`** |

### 3.1. Giải trình kỹ thuật về con số đặt chỗ `max_usd = 52.0` trong `paired-live-owner-approval.json`

> [!WARNING]
> **Sự khác biệt giữa Chi phí thực tế dự kiến (`$1.50 – $2.00`) và Trần đặt chỗ preflight (`max_usd = 52.0`):**
> Trong [`run_paired_route_evaluation.py`](../../../../../backend/scripts/run_paired_route_evaluation.py) (dòng `420–427`), hàm `check_approval_terms()` thực thi một bất đẳng thức kiểm tra cứng trước request đầu tiên:
> $$\texttt{max\_requests} \times \texttt{worst\_case\_request\_usd} \le \texttt{max\_usd}$$
> Vì nhánh sản phẩm `LLM_ONLY` hiện **không đặt `maxOutputTokens`**, giao thức bắt buộc đặt `llm_only_output_reservation_tokens = 65536` (trần output tối đa của model `gemini-2.5-flash`). Do đó:
> - Trần lý thuyết của **1 request đơn lẻ** khi chưa biết usage là: $65{,}536 \times $2.50 / 10^6 + \text{prompt} \approx \mathbf{$0.1693 / \text{request}}$.
> - Với `max_requests = 300`, tích số kiểm tra ở cổng preflight là $300 \times $0.1693 \approx \mathbf{$50.79}$. Nếu ghi `max_usd = 5.0` vào file JSON, `check_approval_terms()` sẽ **từ chối chạy ngay ở bước preflight** trước request số 1!
> - Trong khi chạy thật, sau mỗi request trả về `usageMetadata` hợp lệ, bộ đếm `CostCappedBudget` chỉ cộng **chi phí token thực tế phát sinh** (`~$0.005–$0.011`), chỉ giữ phần đặt chỗ `$0.169` cho đúng request đang bay trên mạng hoặc request lỗi không trả về `usageMetadata`. Vì vậy **số tiền thực tế bị trừ trên hóa đơn Google Cloud dự kiến chỉ khoảng `$1.50 – $2.00`**, dù trường `max_usd` trong file JSON cần cấp `52.0` để vượt qua cổng toán học worst-case của `LLM_ONLY` không giới hạn output.
> - Nếu Owner muốn hạ `max_usd` xuống thấp hơn (ví dụ `42.0`), có thể giảm `max_requests` xuống `245` (vẫn đủ cho kỳ vọng `200–225` calls nhưng biên độ dự phòng vòng sửa `_prompt_sua` + retry hẹp hơn). Không được chỉnh sửa `LLM_ONLY` để ép thêm `maxOutputTokens` vì điều đó làm sai lệch đường cơ sở production đang cần so sánh.

---

## 4. Luật Dừng Bắt Buộc (`Stop Rules`) Đã Khóa Trong Harness

Bộ chạy dừng tự động ngay lập tức khi chạm bất kỳ điều kiện nào sau đây ([`live-evaluation-protocol.md`](../hybrid-master-backend-replacement/live-evaluation-protocol.md) §5):

1. **Dừng an toàn tức thì trên nhánh `HYBRID` (`SAFETY_STOP`):** Nếu `HYBRID` phục vụ (`status == "ok"`) bất kỳ đề nào có `expect == "REFUSE"`, nhánh `HYBRID` dừng ngay lập tức (Tiêu chí 1 đã trượt dứt khoát); nhánh `LLM_ONLY` vẫn chạy nốt hoặc ghi nhận lỗi tương ứng theo quy tắc A2.
2. **Trần số lượng request (`REQUEST_CAP`):** Dừng ngay trước khi gửi request thứ `max_requests + 1` (`301`).
3. **Trần chi phí theo từng payload (`COST_CEILING` & `USD_80_PERCENT`):** Trước mỗi request, kiểm tra `chi phí đã hạch toán + trần chính xác của payload sắp gửi <= max_usd`; dừng sớm sau mỗi arm nếu tổng chi phí hạch toán chạm `80%` `max_usd`.
4. **Chuỗi lỗi hạ tầng (`INFRASTRUCTURE_STREAK` / `PROVIDER_BLOCK`):** Dừng nếu có `3` lỗi kỹ thuật liên tiếp sau khi đã retry hoặc gặp provider block/safety refusal.
5. **Biến động danh tính (`IDENTITY_CHANGED`):** Dừng ngay nếu `measured_system`, `cache_version`, `model`, `skills_sha256` hoặc `harness_sha256` thay đổi giữa chừng.

---

## 5. Quy Trình Kích Hoạt Một Bước Khi Đủ Hai Đầu Vào Từ Owner

Mẫu cấu hình chờ duyệt đã được chuẩn bị sẵn tại [`paired-live-owner-approval.template.json`](paired-live-owner-approval.template.json) (đang để `"owner_decision": "PENDING_OWNER_DECISION"` — agent tuyệt đối không tự điền giá trị phê duyệt).

Khi Owner cung cấp:
1. File bộ đề độc lập `docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json`, và
2. Phê duyệt ngân sách + xác nhận độc lập trong `paired-live-owner-approval.json`,

trình tự thực thi tự động không cần hỏi lặp lại gồm đúng 3 lệnh:

```powershell
# Bước 1: Kiểm tra định dạng, quét nhiễm toàn repo, xác minh phân tầng 45+5/5/5 và niêm phong SHA-256 (0 live call)
.\backend\.venv\Scripts\python.exe backend/scripts/score_independent_holdout_equivalence.py integrity `
  --corpus docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json `
  --out docs/evaluation/geometry/runs/hybrid-independent-h1/H1_CORPUS_INTEGRITY.json

# Bước 2: Chạy manifest preflight của paired harness để đối chiếu mã băm vào file approval (0 live call)
.\backend\.venv\Scripts\python.exe backend/scripts/run_paired_route_evaluation.py `
  --corpus docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json `
  --manifest

# Bước 3: Thực thi tự động toàn bộ chiến dịch Paired Live (chỉ chạy sau khi Owner cấp paired-live-owner-approval.json)
$env:ALLOW_LIVE_AI = "1"
.\backend\.venv\Scripts\python.exe backend/scripts/run_paired_route_evaluation.py `
  --corpus docs/evaluation/geometry/runs/hybrid-independent-h1/h1-independent-corpus.json `
  --approval docs/evaluation/geometry/runs/hybrid-independent-h1/paired-live-owner-approval.json `
  --live `
  --out docs/evaluation/geometry/runs/hybrid-independent-h1/h1-paired-live-results.jsonl
```
