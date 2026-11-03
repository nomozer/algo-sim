# Báo Cáo Đánh Giá Thực Nghiệm Gemini Live & Quyết Định Chuyển Đổi Kiến Trúc Hybrid

Run `hybrid-live-validation` · Master Epic `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · Phạm vi: **BACKEND ONLY** (`frontend/**` giữ nguyên tuyệt đối, `0` file sửa) · Ngày đo: `2026-11-03`.

> [!IMPORTANT]
> **Tóm tắt trung thực hai chiều:**
> 1. **`LIVE_GEMINI_MEASURED = YES` (`VERIFIED_LIVE`):** Đã thực thi chiến dịch đo thật trên `gemini-2.5-flash` (`serviceTier = "standard"`) với xác nhận trả phí nguyên văn của Owner (`"tôi dùng tiền mà ko free"`, nguồn `OWNER_ATTESTED` / `EXPLICIT_OWNER_PAID_ATTESTATION`, **không phải** `CLOUD_BILLING_VERIFIED`, `project_id = null`), sử dụng đúng **`70 / 70` HTTP requests** trong trần ủy quyền (`<= 70` requests / `<= USD 4.00`). Ở lượt đo chính (Run 3, candidate `44568bc9` / product `8853c4b0`), **`64 / 64` (`100%`) HTTP requests trả về `HTTP 200` với `finishReason = "STOP"`**, `0` retry, `0` lỗi `403`/`429`/quota/billing.
> 2. **`LIVE_GEMINI_QUALITY_VALIDATED = NO` & `HYBRID_CUTOVER_BLOCKED` (`NO-GO`):**
>    - **An toàn toán học đạt tuyệt đối (`0 / 65` ca phục vụ đáp số sai):** Cả **`19 / 19` ca `SERVED`** trên đường live đều khớp **100% đáp số biểu tượng chính xác của oracle độc lập** với `certificate_verified = True`; mọi ca đề mơ hồ, thiếu dữ kiện hoặc mâu thuẫn đều bị chặn fail-closed (`0` ca bịa hình được phục vụ).
>    - **Tuy nhiên tỷ lệ hoàn thành end-to-end live còn thấp** do ma sát trích xuất `TypedFactNext /2` (`K-1`: `1/16` khớp tuyệt đối chữ ký scorer / `3/16` `SERVED` đúng đáp số oracle; `S-2`: `15/36` end-to-end đúng / `11/36` `SERVED` đúng đáp số oracle; `R-1`: `0/13` khớp tuyệt đối chữ ký scorer / `5/13` `SERVED` đúng đáp số oracle; `false_refusal` từ `38.9%` đến `70.0%`), cộng thêm `4` ca cuối của `R-1` (`R1-F02`, `R1-F03`, `R1-G01`, `R1-G02`) chưa đo vì chạm trần `70` request toàn chiến dịch và `H-1` độc lập + đối chiếu cặp live với `LLM_ONLY` chưa đo. Do đó **giữ nguyên `DEFAULT_MODE = LLM_ONLY`, `HYBRID_ROUTE_MODE = off`, `CACHE_VERSION = 131`, không xóa `LLM_ONLY`**.

---

## 1. Bảng Nhãn Trạng Thái Ràng Buộc Bằng Chứng

| Nhãn trạng thái | Phán quyết | Bằng chứng máy |
|---|---|---|
| `LIVE_GEMINI_MEASURED` | **YES (`VERIFIED_LIVE`)** | `live-pilots-8853c4b0/c21-delegated-execution-receipt.json` (`64/64` HTTP 200 `STOP` ở Run 3; tổng chiến dịch `3 + 3 + 64 = 70` HTTP requests) |
| `PAID_TIER_VERIFICATION_SOURCE` | **`OWNER_ATTESTED` (`EXPLICIT_OWNER_PAID_ATTESTATION`)** | `owner-paid-attestation.json` (`sha256 = e89153f533827db33572314c977e73cf1d24d8db611358f3302eccdc87fb12e0`; `cloud_billing_verified = false`, `project_id = null`) |
| `LIVE_MATHEMATICAL_WRONG_ANSWER_SERVED` | **`0 / 65` (`0.0%`)** | Mục 5 & Mục 8 — `19 / 19` ca `SERVED` khớp 100% đáp số biểu tượng oracle và `certificate_verified = True`; `8` ca bị scorer gắn `SERVED_WRONG` đều chỉ do khuyết trường tùy chọn `MathGoalSpec.solid_id` khi bài chỉ có 1 khối |
| `LIVE_GEMINI_QUALITY_VALIDATED` | **NO** | Mục 5 & Mục 7 — tỷ lệ `false_refusal` live còn cao (`38.9%`–`70.0%`); `4` ca `R-1` chưa đo (`GLOBAL_REQUEST_CAP`); chưa có vòng đo live mới sau bản vá `f60ae29e` |
| `BACKEND_HYBRID_OFFLINE_VERIFIED` | **YES** | `HYBRID_BACKEND_VALIDATION_AND_CUTOVER_REPORT.md` (`full-t3-79bbc053.json`) + bộ kiểm hồi quy sau `f60ae29e` / `428515dc` |
| `PLANNER_COMPOSITION_VERIFIED` | **YES (dưới dạng `REGISTERED_DECOMPOSITION`)** | Mục 6 — `4` ca live `SERVED` đi qua chuỗi phân rã định nghĩa đã đăng ký (`K-C01`, `K-C04`, `K-C05`, `R1-A02`) + `15` ca `SOURCE_EXPLICIT_SEQUENCE` |
| `GENUINE_DISCOVERY_NOT_ESTABLISHED` | **KHÔNG ĐỔI (`0` ca `GENUINE_DISCOVERY`)** | Mục 6 — trung thực theo chuẩn C16/C18 |
| `HYBRID_CUTOVER_BLOCKED` | **BLOCKED (`NO-GO`)** | Mục 10 & Mục 11 — giữ `DEFAULT_MODE = LLM_ONLY`, `HYBRID_ROUTE_MODE = off` |
| `LEGACY_REMOVAL_BLOCKED` | **BLOCKED** | Mục 11 — giữ toàn bộ `13` module `LEGACY_ONLY` và `74` module `SHARED_COMPONENT` |

---

## 2. Xác Nhận Dịch Vụ Trả Phí & Chuỗi Danh Tính Candidate

### 2.1. Xác nhận dịch vụ trả phí (`owner-paid-project-attestation/1`)

- **Tệp xác nhận:** [`owner-paid-attestation.json`](owner-paid-attestation.json)
- **SHA-256:** `e89153f533827db33572314c977e73cf1d24d8db611358f3302eccdc87fb12e0`
- **Lời xác nhận nguyên văn của Owner (`statement_quote`):** `"tôi dùng tiền mà ko free"`
- **Mã tham chiếu (`statement_ref`):** `OWNER_DIRECT_STATEMENT_2026_11_03T145305_PLUS0700`
- **Phân loại nguồn xác minh:** `verification_status = "OWNER_ATTESTED"`, `authorization_source = "EXPLICIT_OWNER_SEPARATE_STATEMENT"`, recorded bởi runner dưới mã `source = "EXPLICIT_OWNER_PAID_ATTESTATION"`.
- **Ranh giới trung thực:** `cloud_billing_verified = false`, `project_id = null`. Không gọi Cloud Billing API, không bịa Project ID, không nâng khống thành `CLOUD_BILLING_VERIFIED`.

### 2.2. Chuỗi candidate xuyên suốt chiến dịch (`54ad1f00` → `428515dc`)

| Giai đoạn | Product commit | Candidate commit | `measured_system.tree_hash` (118 files) | Vai trò & kết quả |
|---|---|---|---|---|
| Xuất phát (`C24`) | `57457fc4c59094c5e57dd934bffd73533d82b81e` | `79bbc0531df89d3757ae16a6d8c5c0388fdac84b` | `6202a6a67b555a0d18b59c0edbea7c396b8fe6f1488fb1984f4e7663be1e1421` | **Live Run 1** (`live-pilots-79bbc053/`): `3` HTTP 400 (`INVALID_ARGUMENT`: OpenAPI `ARRAY` thiếu `items` do `prefixItems` của JSON Schema tuple). Dừng an toàn bởi `INFRASTRUCTURE_STREAK` |
| Sửa wire #1 | `48372208` | `8c4f4f201be96098b32049db628a69bc212d6328` | `ad615326b7f0ff10ff1fae5a7d4abb1130f8e23f87d7f83df44a6325ff5e73b5` | Chuyển `prefixItems` → `items` trong `function_calling.py`. **Live Run 2** (`live-pilots-48372208/`): `3` HTTP 400 (`The specified schema produces a constraint that has too many states for serving` trên schema `16,541` byte). Dừng an toàn bởi `INFRASTRUCTURE_STREAK` |
| Sửa wire #2 (Candidate đo chính) | `8853c4b0` | `44568bc9c8154161e9c42a73a33532b62abeea07` | `5c0175289995b921007fb2d9275caad9bf839b857030280807094b5b98319046` | Wire schema phẳng gọn `4,333` byte (`propertyOrdering`) + `_normalize_transport_payload` trong `typed_fact_next_extraction.py`. **Live Run 3** (`live-pilots-8853c4b0/`): **`64 / 64` HTTP 200 `STOP`**, `0` retry (`K-1` `16/16`, `S-2` `36/36`, `R-1` `14/18` tới sát trần `70` request) |
| Sửa hậu nghiệm sau Run 3 (Offline) | `f60ae29e5c6d1b39057743ef05948a0ad06f4fca` | `428515dc` (`EVALUATION_CANDIDATE.json` + `../hybrid-live-gemini-execution/`) | `e758e25af26707c2aa0a43c66ccbb4e59350aac0596b90d136c03be3c14c4d65` | Chuẩn hóa 3 dạng lệch wire thực tế phát hiện ở Run 3 + siết hướng dẫn trích xuất `v2` (`0` live call mới vì ngân sách `70/70` đã dùng hết; kết quả replay offline được tách riêng tuyệt đối tại Mục 9) |

Các phiên bản tầng toán học giữ nguyên xuyên suốt cả 4 mốc: Registry `geometry-functions/32`, Planner `geometry-fact-planner/26`, Engine `geometry-function-engine/24`, Contract `typed-fact-next/2`, Adapter `hybrid-simulation-adapter/4`, `runner_sha256 = e9c6ad4388032f06949ac6c0dd5d06b2882be576c0564ff4a5143e6e48229438`, `scorer_sha256 = 8c330bd493f9d401f579b6383f1a1df2bc9172eee2530cf187be2024801b5a2d`.

---

## 3. Sổ Cái Ngân Sách, Provider, Token, Độ Trễ & Chi Phí Thực Tế

### 3.1. Tổng hợp ngân sách toàn chiến dịch (Trần cứng: `70` HTTP requests / `USD 4.00`)

| Lượt chạy | Thư mục biên nhận | Candidate | HTTP requests (kể cả retry) | Retry | Mã HTTP từ Google | USD báo cáo (runner uncached rate) | USD trần bảo thủ (`GlobalBudgetLedger`) | Lý do kết thúc |
|---|---|---|---:|---:|---|---:|---:|---|
| Run 1 | [`live-pilots-79bbc053/`](live-pilots-79bbc053/c21-delegated-execution-receipt.json) | `79bbc053` | `3` | `0` | `3 × HTTP 400` (`USD 0.00` Google thu, tính trần nội bộ) | `UNKNOWN` | `USD 0.073800` | `INFRASTRUCTURE_STREAK` (schema `prefixItems`) |
| Run 2 | [`live-pilots-48372208/`](live-pilots-48372208/c21-delegated-execution-receipt.json) | `8c4f4f20` | `3` | `0` | `3 × HTTP 400` (`USD 0.00` Google thu, tính trần nội bộ) | `UNKNOWN` | `USD 0.081529` | `INFRASTRUCTURE_STREAK` (constrained-decoding FSM state limit) |
| **Run 3 (Chính)** | [`live-pilots-8853c4b0/`](live-pilots-8853c4b0/c21-delegated-execution-receipt.json) | `44568bc9` | **`64`** | **`0`** | **`64 × HTTP 200` (`finishReason = STOP`, `serviceTier = standard`)** | **`USD 0.340464`** | **`USD 0.340464`** | `K-1` COMPLETE (`16`), `S-2` COMPLETE (`35` HTTP + `1` domain gate), `R-1` dừng trước `R1-F01` tại `GLOBAL_REQUEST_CAP` (`13` HTTP) |
| **Tổng cộng** | — | — | **`70 / 70`** | **`0`** | `6 × HTTP 400` + `64 × HTTP 200` (`0` lỗi `403`/`429`/`5xx`) | **`USD 0.340464`** (Run 3; chiết khấu implicit cache: **`USD 0.318308`**) | **`USD 0.495793` / `USD 4.00`** | Tuân thủ tuyệt đối trần `<= 70` request và `<= USD 4.00` |

### 3.2. Phân phối Token của `gemini-2.5-flash` trên 64 lời gọi HTTP 200 (Run 3)

> Ghi chú trung thực về `cachedContentTokenCount`: Google `usageMetadata` trả trường `cachedContentTokenCount` ở `43 / 64` lời gọi (implicit prefix caching cho system instruction + wire schema) và **không xuất trường này** ở `21 / 64` lời gọi. Theo `AGENTS.md §4`, `21` lời gọi vắng trường được ghi rõ là `ABSENT`, không gán bằng `0`; thống kê `cachedContentTokenCount` dưới đây chỉ tính trên `43` lời gọi có trường.

| Tập đo | Số lời gọi HTTP 200 | `promptTokenCount` (min / p50 / mean / p90 / max / sum) | `candidatesTokenCount` — Output (min / p50 / mean / p90 / max / sum) | `thoughtsTokenCount` — Thinking (min / p50 / mean / p90 / max / sum) | `cachedContentTokenCount` khi có mặt (`n` · min / p50 / mean / max / sum) | `totalTokenCount` (min / p50 / mean / p90 / max / sum) |
|---|---:|---|---|---|---|---|
| **`K-1`** | `16` | `2,184` / `2,199.0` / `2,199.8` / `2,221` / `2,221` / `35,197` | `721` / `916.5` / `878.6` / `951` / `1,029` / `14,057` | `808` / `1,148.5` / `1,517.1` / `2,423` / `3,489` / `24,274` | `n=11` (`5 ABSENT`) · `1,915` / `1,920` / `1,921.5` / `1,935` / `21,137` | `3,974` / `4,151.5` / `4,595.5` / `5,537` / `6,645` / `73,528` |
| **`S-2`** | `35` *(+1 domain gate 0 HTTP)* | `2,128` / `2,162.0` / `2,160.7` / `2,171` / `2,192` / `75,624` | `217` / `577.0` / `551.0` / `690` / `742` / `19,284` | `137` / `1,071.0` / `1,179.0` / `1,986` / `2,469` / `41,266` | `n=27` (`8 ABSENT`) · `1,888` / `1,904` / `1,902.7` / `1,919` / `51,374` | `2,482` / `3,765.0` / `3,890.7` / `4,701` / `5,375` / `136,174` |
| **`R-1`** | `13` *(+1 dừng trần, 4 chưa đo)* | `2,166` / `2,170.0` / `2,175.7` / `2,198` / `2,199` / `28,284` | `393` / `672.0` / `674.5` / `840` / `884` / `8,769` | `574` / `722.0` / `911.0` / `1,423` / `2,468` / `11,843` | `n=5` (`8 ABSENT`) · `1,905` / `1,907` / `1,910.0` / `1,923` / `9,550` | `3,346` / `3,625.0` / `3,761.2` / `4,196` / `5,027` / `48,896` |
| **Gộp `64` lời gọi** | **`64`** | `2,128` / `2,168.0` / `2,173.5` / `2,209` / `2,221` / **`139,105`** | `217` / `627.5` / `658.0` / `928` / `1,029` / **`42,110`** | `137` / `1,038.5` / `1,209.1` / `2,201` / `3,489` / **`77,383`** | `n=43` (`21 ABSENT`) · `1,888` / `1,906` / `1,908.4` / `1,935` / **`82,061`** | `2,482` / `3,952.5` / `4,040.6` / `5,122` / `6,645` / **`258,598`** |

**Nhận xét kỹ thuật về token:**
- `promptTokenCount` cực kỳ ổn định (`2,128`–`2,221` token/bài) nhờ wire schema phẳng gọn `4,333` byte và không cần nhồi few-shot dài dòng.
- `thoughtsTokenCount` chiếm trung bình **`1,209.1` token/bài** (`~30%` tổng token, gấp `1.84×` output JSON `658.0` token), tăng mạnh ở các bài mâu thuẫn hình học (`K-B02`: `3,489` thinking token; `S2-E-E06`: `2,469`; `R1-E01`: `2,468`; `S2-D-D04`: `2,463`) khi model tự kiểm tra tính tương thích dữ kiện trước khi điền JSON.

### 3.3. Tách Bạch Độ Trễ Provider HTTP vs Độ Trễ Backend Tất Định & Chi Phí Mỗi Bài

| Tập đo | Provider HTTP latency (s) — min / p50 / mean / p90 / max | Backend tất định (s) — min / p50 / mean / p90 / max | End-to-End case latency (s) — p50 / p90 | Chi phí / lời gọi HTTP (USD, runner uncached) — mean / max / sum | Chi phí / lời gọi HTTP (USD, có chiết khấu cache) — p50 / mean / sum |
|---|---|---|---|---|---|
| **`K-1`** (`n=16` HTTP) | `8.17` / `9.45` / `10.91` / `14.23` / `20.86` | `0.048` / `0.055` / `0.116` / `0.159` / `0.801` | `9.86` / `14.34` | `USD 0.006649` / `USD 0.011751` / `USD 0.106387` | `USD 0.005519` / `USD 0.006292` / `USD 0.100680` |
| **`S-2`** (`n=35` HTTP; E2E `n=36`) | `3.06` / `8.46` / `9.36` / `14.54` / `18.06` | `0.049` / `0.064` / `0.067` / `0.087` / `0.125` | `8.51` / `14.60` | `USD 0.004973` / `USD 0.008677` / `USD 0.174062` | `USD 0.004492` / `USD 0.004577` / `USD 0.160191` |
| **`R-1`** (`n=13` HTTP) | `6.48` / `7.68` / `8.40` / `11.66` / `13.90` | `0.073` / `0.198` / `0.191` / `0.276` / `0.369` | `7.89` / `11.85` | `USD 0.004617` / `USD 0.007802` / `USD 0.060015` | `USD 0.003926` / `USD 0.004418` / `USD 0.057437` |
| **Toàn bộ `64` lời gọi** | **`3.06` / `8.59` / `9.55` / `13.90` / `20.86`** | **`0.048` / `0.066` / `0.104` / `0.206` / `0.801`** | — | **`USD 0.005320`** mean / **`USD 0.340464`** sum | **`USD 0.004683`** p50 / **`USD 0.004974`** mean / **`USD 0.318308`** sum |

**Phát hiện quan trọng cho vận hành sản phẩm (Production SLA):**
- **98.9% độ trễ nằm ở Gemini HTTP (`p50 = 8.59s`, `p90 = 13.90s`, `max = 20.86s`), trong khi toàn bộ chuỗi tất định `Source Gate → FactGraph → Planner → Exact Kernel → Adapter /4` chỉ mất trung vị `55–198 ms` (tối đa `801 ms`).**
- Trong route sản phẩm `backend/app/ai/hybrid_offline.py` hiện tại, deadline mặc định tổng thể đang đặt `15.0s` (`per-attempt timeout` thấp hơn đỉnh `20.86s` quan sát được ở `K-B02` và `18.06s` ở `S2-E-E06`). Nếu giữ deadline `15.0s` khi bật live cho người dùng, khoảng `~6%`–`10%` câu hỏi phức tạp của `gemini-2.5-flash` (khi thinking > `2,200` token) sẽ bị cắt `504 GATEWAY_TIMEOUT` dù model đang suy nghĩ hợp lệ. Trước khi cutover cần nâng deadline route D live lên `25s`–`30s` hoặc giới hạn `thinkingBudget` có kiểm chứng.

---

## 4. Bảng Chi Tiết Từng Bài Toán Trên Cả 3 Tập Pilot (66 Ca Đã Chạy + 4 Ca Chưa Đo)

### 4.1. Danh sách 4 ca chưa đo (`NOT_MEASURED` / `UNKNOWN`)

Do Run 1 (`3` HTTP requests) và Run 2 (`3` HTTP requests) đã tiêu thụ `6` requests vào trần chiến dịch `70` requests trước khi sửa xong wire schema, Run 3 dừng chính xác tại request thứ `70` ngay trước khi gửi `R1-F01`. Bốn ca cuối của `R-1` hoàn toàn chưa được gửi lên Gemini và được ghi trung thực là `NOT_MEASURED` (`UNKNOWN`, `0` suy đoán):
- `R1-F02` (stratum `R1-F`) — `NOT_MEASURED` (`GLOBAL_REQUEST_CAP`)
- `R1-F03` (stratum `R1-F`) — `NOT_MEASURED` (`GLOBAL_REQUEST_CAP`)
- `R1-G01` (stratum `R1-G`) — `NOT_MEASURED` (`GLOBAL_REQUEST_CAP`)
- `R1-G02` (stratum `R1-G`) — `NOT_MEASURED` (`GLOBAL_REQUEST_CAP`)

### 4.2. Bảng 66 ca đã thực thi trong Run 3 (`live-pilots-8853c4b0`)

*(Cột `Input / Out / Think / Cache / Total tok`: `ABSENT` nghĩa là Google `usageMetadata` không xuất trường `cachedContentTokenCount` ở lời gọi đó. Cột `Oracle vs Served`: đối chiếu trực tiếp `observed.answers` với `expected_answers` của oracle độc lập.)*

| Pilot | Case ID | Stratum | Expected | Observed | Scorer Outcome | Code / Stage | Input / Out / Think / Cache / Total tok | HTTP / E2E lat (s) | Chi phí báo cáo | Oracle vs Served |
|---|---|---|---|---|---|---|---:|---:|---:|---|
| `K-1` | `K-A01` | `K-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2209 / 928 / 999 / ABSENT / 4136 | 9.06 / 9.86 | USD 0.005480 | — |
| `K-1` | `K-A02` | `K-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2209 / 938 / 1020 / ABSENT / 4167 | 8.60 / 8.65 | USD 0.005558 | — |
| `K-1` | `K-A03` | `K-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2221 / 951 / 1353 / ABSENT / 4525 | 11.28 / 11.33 | USD 0.006426 | — |
| `K-1` | `K-A04` | `K-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2221 / 1029 / 808 / 1935 / 4058 | 8.17 / 8.22 | USD 0.005259 | — |
| `K-1` | `K-B01` | `K-B` | `REFUSED_UNDERDETERMINED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2209 / 886 / 1041 / ABSENT / 4136 | 9.01 / 9.06 | USD 0.005480 | — |
| `K-1` | `K-B02` | `K-B` | `REFUSED_INCONSISTENT` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2210 / 946 / 3489 / 1929 / 6645 | 20.86 / 20.91 | USD 0.011751 | — |
| `K-1` | `K-C01` | `K-C` | `SERVED` | `SERVED` | `SERVED_WRONG` | PASS (`Adapter /4`) | 2184 / 768 / 1155 / 1915 / 4107 | 8.69 / 8.85 | USD 0.005463 | `{"distance": ["1"]}` == oracle (khớp chính xác; thiếu `solid_id`) |
| `K-1` | `K-C02` | `K-C` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_DESCRIBED_POINT` (`extraction`) | 2186 / 829 / 1019 / ABSENT / 4034 | 8.57 / 8.62 | USD 0.005276 | — |
| `K-1` | `K-C03` | `K-C` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_DESCRIBED_POINT` (`extraction`) | 2186 / 806 / 1142 / 1916 / 4134 | 9.84 / 9.89 | USD 0.005526 | — |
| `K-1` | `K-C04` | `K-C` | `SERVED` | `SERVED` | `SERVED_WRONG` | PASS (`Adapter /4`) | 2198 / 929 / 902 / 1922 / 4029 | 8.59 / 8.71 | USD 0.005237 | `{"distance": ["2"]}` == oracle (khớp chính xác; thiếu `solid_id`) |
| `K-1` | `K-C05` | `K-C` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2194 / 920 / 2423 / 1920 / 5537 | 14.23 / 14.34 | USD 0.009016 | `{"distance": ["√673/8"]}` == oracle |
| `K-1` | `K-C06` | `K-C` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_DESCRIBED_POINT` (`extraction`) | 2200 / 913 / 2009 / 1923 / 5122 | 12.29 / 12.34 | USD 0.007965 | — |
| `K-1` | `K-D01` | `K-D` | `REFUSED_INCONSISTENT` | `REFUSED` | `WRONG_REASON_REFUSAL` | `DEGENERATE_POINTS` (`deterministic_route`) | 2184 / 824 / 966 / 1915 / 3974 | 8.59 / 8.66 | USD 0.005130 | — |
| `K-1` | `K-D02` | `K-D` | `REFUSED_INCONSISTENT` | `REFUSED` | `WRONG_REASON_REFUSAL` | `DEGENERATE_POINTS` (`deterministic_route`) | 2186 / 721 / 2057 / 1916 / 4964 | 12.06 / 12.13 | USD 0.007601 | — |
| `K-1` | `K-E01` | `K-E` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2209 / 935 / 2201 / 1928 / 5345 | 13.59 / 13.64 | USD 0.008503 | — |
| `K-1` | `K-E02` | `K-E` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INVALID_TYPED_FACT_NEXT` (`extraction`) | 2191 / 734 / 1690 / 1918 / 4615 | 11.13 / 11.19 | USD 0.006717 | — |
| `S-2` | `S2-A-I02_ve` | `S2-A` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2152 / 507 / 710 / 1897 / 3369 | 6.40 / 6.47 | USD 0.003688 | `{}` == oracle |
| `S-2` | `S2-A-I04_mo_phong` | `S2-A` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2154 / 458 / 655 / 1898 / 3267 | 5.56 / 5.63 | USD 0.003429 | `{}` == oracle |
| `S-2` | `S2-A-I05_cho_minh_xem` | `S2-A` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2153 / 509 / 318 / 1897 / 2980 | 4.47 / 4.55 | USD 0.002713 | `{}` == oracle |
| `S-2` | `S2-A-I08_trailing_ve` | `S2-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `PREDICATE_NOT_IN_QUOTE` (`deterministic_route`) | 2159 / 577 / 1743 / 1901 / 4479 | 10.39 / 10.46 | USD 0.006448 | — |
| `S-2` | `S2-A-I09_trailing_mo_phong_hinh` | `S2-A` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2157 / 509 / 721 / ABSENT / 3387 | 6.27 / 6.36 | USD 0.003722 | `{}` == oracle |
| `S-2` | `S2-A-I12_trailing_point` | `S2-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `DANGLING_DEPENDENCY` (`extraction`) | 2168 / 581 / 1016 / ABSENT / 3765 | 8.45 / 8.52 | USD 0.004643 | — |
| `S-2` | `S2-B-I07_ve_va_tinh` | `S2-B` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2162 / 548 / 768 / 1902 / 3478 | 6.23 / 6.30 | USD 0.003939 | `{"volume": ["8/3"]}` == oracle |
| `S-2` | `S2-B-I10_ve_roi_tinh` | `S2-B` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2164 / 546 / 1071 / ABSENT / 3781 | 7.78 / 7.86 | USD 0.004692 | `{"volume": ["8/3"]}` == oracle |
| `S-2` | `S2-B-I11_mo_phong_va_tinh_SC` | `S2-B` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2163 / 543 / 1036 / 1903 / 3742 | 7.47 / 7.55 | USD 0.004596 | `{"distance": ["2√3"]}` == oracle |
| `S-2` | `S2-B-P07_shared_intermediate_two_goals` | `S2-B` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `SOURCE_OBJECT_MISMATCH` (`deterministic_route`) | 2174 / 690 / 616 / 1909 / 3480 | 6.36 / 6.41 | USD 0.003917 | — |
| `S-2` | `S2-B-P09_student_chain` | `S2-B` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `SOURCE_OBJECT_MISMATCH` (`deterministic_route`) | 2169 / 705 / 711 / 1906 / 3585 | 6.76 / 6.82 | USD 0.004191 | — |
| `S-2` | `S2-B-A03_control_with_dimensions` | `S2-B` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2192 / 657 / 1084 / 1919 / 3933 | 8.67 / 8.80 | USD 0.005010 | `{"volume": ["√3"]}` == oracle |
| `S-2` | `S2-C-A01_goc_chieu` | `S2-C` | `CLARIFY` | `CLARIFY` | `FALSE_CLARIFICATION` | `AMBIGUOUS_FACT` (`deterministic_route`) | 2136 / 231 / 1618 / 1888 / 3985 | 9.28 / 9.33 | USD 0.005263 | — |
| `S-2` | `S2-C-D05_projection_missing_target` | `S2-C` | `CLARIFY` | `CLARIFY` | `CORRECT_CLARIFICATION` | `AMBIGUOUS_FACT` (`deterministic_route`) | 2167 / 613 / 1589 / 1905 / 4369 | 11.03 / 11.09 | USD 0.006155 | — |
| `S-2` | `S2-C-D06_unnamed_prism` | `S2-C` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `UNKNOWN_LABEL` (`deterministic_route`) | 2128 / 217 / 137 / ABSENT / 2482 | 3.06 / 3.11 | USD 0.001523 | — |
| `S-2` | `S2-C-C04_angle_plane_missing` | `S2-C` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `SOURCE_OBJECT_MISMATCH` (`deterministic_route`) | 2159 / 596 / 665 / 1901 / 3420 | 6.35 / 6.41 | USD 0.003800 | — |
| `S-2` | `S2-C-C05_draw_then_compute` | `S2-C` | `CLARIFY` | `CLARIFY` | `WRONG_REASON_CLARIFICATION` | `AMBIGUOUS_FACT` (`deterministic_route`) | 2156 / 528 / 1601 / 1899 / 4285 | 9.87 / 9.92 | USD 0.005969 | — |
| `S-2` | `S2-C-C06_square_without_side` | `S2-C` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `MISSING_DIMENSION` (`deterministic_route`) | 2152 / 464 / 1147 / 1897 / 3763 | 8.32 / 8.38 | USD 0.004673 | — |
| `S-2` | `S2-D-D03_contradictory_length` | `S2-D` | `REFUSED_INCONSISTENT` | `REFUSED` | `WRONG_REASON_REFUSAL` | `OBJECT_NOT_IN_QUOTE` (`deterministic_route`) | 2165 / 466 / 1045 / 1904 / 3676 | 7.60 / 7.65 | USD 0.004427 | — |
| `S-2` | `S2-D-D04_two_values_same_segment` | `S2-D` | `REFUSED_INCONSISTENT` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INCONSISTENT_FACTS` (`deterministic_route`) | 2165 / 666 / 2463 / 1904 / 5294 | 14.97 / 15.03 | USD 0.008472 | — |
| `S-2` | `S2-D-D07_cube_rectangle_base` | `S2-D` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` (`deterministic_route`) | 2173 / 703 / 1746 / 1909 / 4622 | 12.62 / 12.69 | USD 0.006774 | — |
| `S-2` | `S2-D-D08_cube_tall` | `S2-D` | `REFUSED_INCONSISTENT` | `REFUSED` | `WRONG_REASON_REFUSAL` | `PREDICATE_NOT_IN_QUOTE` (`deterministic_route`) | 2171 / 593 / 2396 / 1907 / 5160 | 14.54 / 14.60 | USD 0.008124 | — |
| `S-2` | `S2-D-D09_base_edge_perp_base` | `S2-D` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` (`deterministic_route`) | 2169 / 630 / 1611 / 1906 / 4410 | 13.54 / 13.60 | USD 0.006253 | — |
| `S-2` | `S2-D-D10_square_diagonal_3` | `S2-D` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` (`deterministic_route`) | 2165 / 613 / 1304 / 1904 / 4082 | 13.79 / 13.86 | USD 0.005442 | — |
| `S-2` | `S2-E-E01_oxyz` | `S2-E` | `REFUSED_UNSUPPORTED` | `REFUSED` | `CORRECT_REFUSAL` | `gate_out_of_scope` (`domain_gate`) | 0 HTTP (`domain_gate`) | — / 0.000 | USD 0.000000 | — |
| `S-2` | `S2-E-E02_truncated_pyramid` | `S2-E` | `REFUSED_UNSUPPORTED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INVALID_TYPED_FACT_NEXT` (`extraction`) | 2164 / 289 / 1514 / 1904 / 3967 | 14.99 / 15.04 | USD 0.005157 | — |
| `S-2` | `S2-E-E03_volume_maximum` | `S2-E` | `REFUSED_UNSUPPORTED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `OUT_OF_SCOPE` (`deterministic_route`) | 2144 / 571 / 1986 / ABSENT / 4701 | 13.19 / 13.24 | USD 0.007036 | — |
| `S-2` | `S2-E-E06_word_problem_rate` | `S2-E` | `REFUSED_UNSUPPORTED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `OUT_OF_SCOPE` (`deterministic_route`) | 2164 / 742 / 2469 / 1904 / 5375 | 18.06 / 18.12 | USD 0.008677 | — |
| `S-2` | `S2-E-E04_locus` | `S2-E` | `REFUSED_UNSUPPORTED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `OUT_OF_SCOPE` (`deterministic_route`) | 2166 / 541 / 664 / 1905 / 3371 | 8.46 / 8.52 | USD 0.003662 | — |
| `S-2` | `S2-E-E05_translation` | `S2-E` | `REFUSED_UNSUPPORTED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `OUT_OF_SCOPE` (`deterministic_route`) | 2170 / 579 / 1563 / 1907 / 4312 | 12.84 / 12.90 | USD 0.006006 | — |
| `S-2` | `S2-F-S02_vuong_goc_day` | `S2-F` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2156 / 537 / 1248 / ABSENT / 3941 | 10.21 / 10.28 | USD 0.005109 | `{"volume": ["8/3"]}` == oracle |
| `S-2` | `S2-F-S03_symbol_perp` | `S2-F` | `SERVED` | `SERVED` | `SERVED_CORRECT` | PASS (`Adapter /4`) | 2157 / 509 / 958 / 1900 / 3624 | 8.65 / 8.72 | USD 0.004315 | `{"volume": ["8/3"]}` == oracle |
| `S-2` | `S2-F-S07_typo_tone` | `S2-F` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `UNGROUNDED_VALUE` (`deterministic_route`) | 2160 / 596 / 637 / 1901 / 3393 | 6.93 / 6.99 | USD 0.003730 | — |
| `S-2` | `S2-F-S08_altitude_wording` | `S2-F` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `PREDICATE_NOT_IN_QUOTE` (`deterministic_route`) | 2153 / 582 / 1220 / 1897 / 3955 | 10.76 / 10.83 | USD 0.005151 | — |
| `S-2` | `S2-F-F05_kc_mp_shorthand` | `S2-F` | `SERVED` | `SERVED` | `SERVED_WRONG` | PASS (`Adapter /4`) | 2159 / 594 / 628 / ABSENT / 3381 | 6.80 / 6.90 | USD 0.003703 | `{"distance": ["√2"]}` == oracle (khớp chính xác; thiếu `solid_id`) |
| `S-2` | `S2-F-F06_dt_mp_shorthand` | `S2-F` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `PREDICATE_NOT_IN_QUOTE` (`deterministic_route`) | 2158 / 594 / 608 / ABSENT / 3360 | 6.92 / 6.99 | USD 0.003652 | — |
| `R-1` | `R1-A01` | `R1-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `PREDICATE_NOT_IN_QUOTE` (`deterministic_route`) | 2166 / 671 / 787 / 1905 / 3624 | 7.58 / 7.65 | USD 0.004295 | — |
| `R-1` | `R1-A02` | `R1-A` | `SERVED` | `SERVED` | `SERVED_WRONG` | PASS (`Adapter /4`) | 2172 / 600 / 574 / ABSENT / 3346 | 6.48 / 6.69 | USD 0.003587 | `{"distance": ["2√6/3"]}` == oracle (khớp chính xác; thiếu `solid_id`) |
| `R-1` | `R1-A03` | `R1-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `PREDICATE_NOT_IN_QUOTE` (`deterministic_route`) | 2166 / 672 / 618 / ABSENT / 3456 | 6.97 / 7.12 | USD 0.003875 | — |
| `R-1` | `R1-A04` | `R1-A` | `SERVED` | `SERVED` | `SERVED_WRONG` | PASS (`Adapter /4`) | 2169 / 678 / 687 / ABSENT / 3534 | 7.54 / 7.81 | USD 0.004063 | `{"angle_cos_sq": ["2/3"]}` == oracle (khớp chính xác; thiếu `solid_id`) |
| `R-1` | `R1-A05` | `R1-A` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `PREDICATE_NOT_IN_QUOTE` (`deterministic_route`) | 2167 / 672 / 584 / ABSENT / 3423 | 6.56 / 6.67 | USD 0.003790 | — |
| `R-1` | `R1-B01` | `R1-B` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2199 / 840 / 678 / 1923 / 3717 | 7.93 / 8.09 | USD 0.004455 | — |
| `R-1` | `R1-B02` | `R1-B` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2192 / 581 / 1423 / ABSENT / 4196 | 11.66 / 11.85 | USD 0.005668 | — |
| `R-1` | `R1-C01` | `R1-C` | `SERVED` | `SERVED` | `SERVED_WRONG` | PASS (`Adapter /4`) | 2178 / 703 / 1069 / ABSENT / 3950 | 9.30 / 9.67 | USD 0.005083 | `{"distance": ["2", "√6"]}` == oracle (khớp chính xác; thiếu `solid_id`) |
| `R-1` | `R1-C02` | `R1-C` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_SIMULATION_GOAL` (`extraction`) | 2198 / 884 / 722 / ABSENT / 3804 | 8.13 / 8.39 | USD 0.004674 | — |
| `R-1` | `R1-D01` | `R1-D` | `SERVED` | `SERVED` | `SERVED_WRONG` | PASS (`Adapter /4`) | 2173 / 751 / 765 / 1909 / 3689 | 7.44 / 7.67 | USD 0.004442 | `{"distance": ["√41/2"]}` == oracle (khớp chính xác; thiếu `solid_id`) |
| `R-1` | `R1-D02` | `R1-D` | `SERVED` | `SERVED` | `SERVED_WRONG` | PASS (`Adapter /4`) | 2170 / 625 / 830 / 1907 / 3625 | 7.68 / 7.89 | USD 0.004288 | `{"distance": ["√3/3"]}` == oracle (khớp chính xác; thiếu `solid_id`) |
| `R-1` | `R1-E01` | `R1-E` | `CLARIFY` | `CLARIFY` | `WRONG_REASON_CLARIFICATION` | `AMBIGUOUS_FACT` (`deterministic_route`) | 2166 / 393 / 2468 / ABSENT / 5027 | 13.90 / 14.05 | USD 0.007802 | — |
| `R-1` | `R1-E02` | `R1-E` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `SOURCE_OBJECT_MISMATCH` (`deterministic_route`) | 2168 / 699 / 638 / 1906 / 3505 | 7.96 / 8.06 | USD 0.003993 | — |
| `R-1` | `R1-F01` | `R1-F` | `REFUSED_UNSUPPORTED` | `NOT_RECOVERABLE` | `INFRASTRUCTURE_FAILURE` | `PROVIDER_ERROR` (`extraction`) | `NOT_RECOVERABLE` (`0` HTTP; `GLOBAL_REQUEST_CAP`) | `UNKNOWN` / 0.010 | `UNKNOWN` | — |

---

## 5. Đánh Giá Chất Lượng Trích Xuất `TypedFactNext /2` & Pipeline Hybrid End-to-End (Run 3 Live)

### 5.1. Tám chỉ số chuẩn của Scorer (`score_s2_student_language_pilot.py`) trên dữ liệu Live Run 3

| Chỉ số (`s2-student-language-pilot-score/1`) | `K-1` (`16/16` evaluable) | `S-2` (`36/36` evaluable) | `R-1` (`13/14` evaluable; `1` `NOT_RECOVERABLE`; `4` `NOT_MEASURED`) | Diễn giải kỹ thuật trung thực |
|---|---|---|---|---|
| 1. `extraction_accuracy` | `5 / 14` (`35.7%`) | `10 / 24` (`41.7%`) | `4 / 11` (`36.4%`) | Khớp chính xác tuyệt đối tập chữ ký `facts_signature` với `gold_extraction` |
| 2. `goal_completeness` | `1 / 14` (`7.1%`) | `20 / 24` (`83.3%`) | `0 / 11` (`0.0%`) | Thấp ở `K-1`/`R-1` chủ yếu vì Gemini bỏ trống `MathGoalSpec.solid_id` tùy chọn trên bài 1 khối và đặt `construct_object(target_section_id)` cho thiết diện |
| 3. `operand_preservation` | `8 / 14` (`57.1%`) | `21 / 24` (`87.5%`) | `11 / 11` (`100.0%`) | Nhãn điểm, con số và trích dẫn nguyên văn (`quotes_verbatim`) được giữ rất tốt (`100%` trên `R-1`, `87.5%` trên `S-2`) |
| 4. `ambiguity_detection` | `2 / 2` (`100.0%`) | `3 / 6` (`50.0%`) | `1 / 2` (`50.0%`) | `4` ca mơ hồ Gemini cố đoán tiếp (`S2-C-D06`, `S2-C-C04`, `S2-C-C06`, `R1-E02`) đều bị chặn fail-closed bởi tầng tất định |
| 5. `clarification_correctness` | `0 / 0` (`UNKNOWN`) | `2 / 3` (`66.7%`) | `1 / 1` (`100.0%`) | Ở `K-E01`/`K-E02` Gemini đã nhận diện đúng `unresolved`, nhưng rơi vào lỗi wire `INVALID_SIMULATION_GOAL` / tag ngoài enum trước khi xuất `CLARIFY` |
| 6. `false_clarification` | `0 / 14` (`0.0%`) | `0 / 30` (`0.0%`) | `0 / 11` (`0.0%`) | **Không có bài rõ nghĩa nào bị hỏi vặn sai (`0 / 55`)** *(Lưu ý: `S2-C-A01_goc_chieu` vốn là đề mơ hồ `is_ambiguous = True`, nhưng `hybrid_outcome` gắn `FALSE_CLARIFICATION` do mã `UNRECOGNIZED_WORDING` lệch danh sách `['AMBIGUOUS','MISSING_DATA']`)* |
| 7. `unsupported_classification` | `0 / 0` (`UNKNOWN`) | `5 / 6` (`83.3%`) | `0 / 0` (`UNKNOWN`) | `5/6` ca ngoài phạm vi ở `S-2` trả đúng mã `OUT_OF_SCOPE` / `gate_out_of_scope`; ca thứ 6 (`S2-E-E02_truncated_pyramid`) cũng từ chối an toàn (`REFUSED`) |
| 8. `wrong_served_end_to_end` (theo chữ ký scorer) | `2 / 16` (`12.5%`)* | `1 / 36` (`2.8%`)* | `5 / 13` (`38.5%`)* | *Xem giải trình ngay bên dưới: **cả `8 / 8` ca này đều trả đáp số toán học khớp 100% oracle** |
| **Đáp số toán học sai thực tế (`answers != expected_answers` hoặc phục vụ nhầm đề âm tính)** | **`0 / 16` (`0.0%`)** | **`0 / 36` (`0.0%`)** | **`0 / 13` (`0.0%`)** | **`19 / 19` ca `SERVED` khớp 100% oracle độc lập và `certificate_verified = True`** |
| `end_to_end_correct` (bổ trợ §V) | `1 / 16` (`6.25%`) | `15 / 36` (`41.7%`) | `0 / 13` (`0.0%`) | Tỷ lệ khớp đồng thời cả trạng thái, đáp số, chữ ký mục tiêu và mã lý do |
| `false_refusal` trên đề dương tính | `7 / 10` (`70.0%`) | `7 / 18` (`38.9%`) | `6 / 11` (`54.5%`) | Tổng `20 / 39` (`51.3%`) đề dương tính bị từ chối nhầm do lỗi trích xuất / quote Source Gate |

### 5.2. Độ chính xác trích xuất thành phần chuyên biệt (`constraints` & `described_points`)

- **Ràng buộc mặt phẳng ẩn `constraints` trên `K-1` (`K-A01..K-A04`, `K-B01`, `K-B02`):**
  - `emitted`: **`6 / 6` (`100%`)**
  - `kinds_match`: **`6 / 6` (`100%`)**
  - `operands_match`: **`6 / 6` (`100%`)**
  - `quotes_verbatim`: **`6 / 6` (`100%`)**
  - Gemini hiểu chính xác cấu trúc ngữ nghĩa tiếng Việt của mặt phẳng đi qua điểm và song song/vuông góc đường/mặt! Lý do duy nhất khiến `K-A01..K-A04` bị chặn ở Run 3 là Gemini xuất thêm một mục `simulation_goals` với `kind = "construct_object"` + `target_section_id = "sec1"` thay vì `kind = "construct_plane_section"`.
- **Điểm mô tả không tên `described_points` trên `R-1` và `K-1`:**
  - Trên **`R-1` (`11` ca dương tính):** `emitted = 11/11 (100%)`, `kinds_match = 11/11 (100%)`, `refs_resolve = 11/11 (100%)`, `quotes_verbatim = 11/11 (100%)`! Gemini trích xuất hoàn hảo các cụm danh ngữ hình học không tên (hình chiếu vuông góc, trung điểm ẩn, giao điểm ẩn, tâm đường tròn ngoại tiếp, trực tâm).
  - Trên **`K-1` (`8` ca):** `emitted = 8/8 (100%)`, `refs_resolve = 8/8 (100%)`, `quotes_verbatim = 8/8 (100%)`, `kinds_match = 5/8 (62.5%)` — `3` ca lệch (`K-C02`, `K-C03`, `K-C06`) là do đề đặt tên tường minh cho điểm (`G`, `O`, `H`, `M`) nhưng Gemini đặt vào `described_points` kèm trường `label` (vốn bị contract cấm cho điểm đã đặt tên).

### 5.3. Hoạt động của các tầng Backend tất định trên 65 ca hợp lệ của Run 3

1. **Domain Gate:** Chặn chính xác `S2-E-E01_oxyz` (`gate_out_of_scope`) trong `0.000s` với `0` lời gọi Gemini.
2. **TypedFactNext `/2` Decoder:** Chặn tại chỗ `15` payload vi phạm hình thức contract (`10` `INVALID_SIMULATION_GOAL`, `3` `INVALID_DESCRIBED_POINT`, `2` `INVALID_TYPED_FACT_NEXT` do tag `UnresolvedSpec` ngoài từ điển).
3. **Source Gate (`kiem_nguon`):** Bảo vệ tuyệt đối ranh giới chống ảo giác:
   - Khi Gemini tự bịa tên đỉnh `ABC.A'B'C'` cho đề `"Vẽ lăng trụ đứng tam giác đều cạnh 2"` (`S2-C-D06`), Source Gate chặn ngay với `UNKNOWN_LABEL`.
   - Khi đề thiếu cạnh đáy (`S2-C-C06`) hoặc thiếu mặt phẳng tính góc (`S2-C-C04`, `R1-E02`) mà Gemini không bật `unresolved`, Source Gate / Bridge chặn ngay với `MISSING_DIMENSION` / `SOURCE_OBJECT_MISMATCH`.
   - Điểm nghẽn còn lại: `9` ca đề hợp lệ bị từ chối `PREDICATE_NOT_IN_QUOTE` / `SOURCE_OBJECT_MISMATCH` vì Gemini cắt `quote` quá hẹp (chỉ chép vế sau của câu, thiếu tên khối hoặc vế vuông góc ở đầu câu) và `1` ca gõ thiếu dấu tiếng Việt (`S2-F-S07_typo_tone`: `"hình chop"` → `UNGROUNDED_VALUE`, thuộc phạm vi `S-1`).
4. **FactGraph → Planner `/26` → Registry `/32` → Exact Kernel `/24` → Adapter `/4`:**
   - **Tỷ lệ thành công hạ nguồn khi qua khỏi Source Gate trên các đề khả giải:** **`19 / 19` (`100%`)** ca đi tới Planner đều lập kế hoạch thành công, thực thi kernel biểu tượng chính xác, vượt qua kiểm định chứng chỉ (`certificate_verified = True`), đóng gói thành công qua Adapter `/4`, và cho đáp số trùng khớp 100% với oracle (`0` lỗi FactGraph, `0` lỗi Planner, `0` thiếu hụt Registry trên tập đã đo, `0` lỗi Kernel, `0` lỗi Adapter `/4`).
   - Trên `2` đề mâu thuẫn hình học ngầm (`K-D01`, `K-D02`: chân đường cao trùng đỉnh tạo tam giác suy biến), Kernel bắt chính xác bằng `DEGENERATE_POINTS`.

---

## 6. Kết Quả Tổ Hợp Hàm Của Planner Trên Dữ Liệu Gemini Live

Trên `19` ca `SERVED` thực tế của Run 3:
- **`REGISTERED_DECOMPOSITION`: `4` ca** (`K-C01`, `K-C04`, `K-C05`, `R1-A02`) — Planner tự động phân rã định nghĩa toán học đã đăng ký (`DINH_NGHIA_DIEM` cho `circumcenter` / `orthocenter` hoặc chiếu vuông góc hai bước) thành chuỗi nhiều hàm nguyên tử có sẵn trong Registry `/32` và tạo điểm trung gian mới:
  - `K-C01` (khoảng cách từ tâm đường tròn ngoại tiếp tam giác đáy tới mặt bên `= 1`): `2 × orthogonal_projection_line` → `intersect_line_line` → `ask_distance_point_plane`.
  - `K-C04` (khoảng cách từ trực tâm mặt bên tới mặt đáy `= 2`): `2 × orthogonal_projection_line` → `intersect_line_line` → `ask_distance_point_plane`.
  - `K-C05` (độ dài đoạn nối đỉnh với trực tâm `= √673/8`): `2 × orthogonal_projection_line` → `intersect_line_line` → `ask_length`.
  - `R1-A02` (khoảng cách giữa hai điểm hình chiếu không tên `= 2√6/3`): `orthogonal_projection` (mặt) → `orthogonal_projection_line` (cạnh) → `ask_length`.
- **`SOURCE_EXPLICIT_SEQUENCE`: `15` ca** (`S2-A-I02/I04/I05/I09`, `S2-B-I07/I10/I11/A03`, `S2-F-S02/S03/F05`, `R1-A04`, `R1-C01`, `R1-D01`, `R1-D02`).
- **`GENUINE_DISCOVERY`: `0` ca** (`GENUINE_DISCOVERY_NOT_ESTABLISHED` vẫn giữ nguyên trung thực như C16/C18).

---

## 7. Phân Loại Thực Nghiệm Toàn Bộ 66 Ca Theo 10 Nhóm Nguyên Nhân Chuẩn

| Nhóm phân loại | Số ca (`/ 66`) | Danh sách ca & căn nguyên thực nghiệm |
|---|---:|---|
| *(Thành công chuẩn)* `SERVED_CORRECT` | `11` | `K-C05`, `S2-A-I02`, `S2-A-I04`, `S2-A-I05`, `S2-A-I09`, `S2-B-I07`, `S2-B-I10`, `S2-B-I11`, `S2-B-A03`, `S2-F-S02`, `S2-F-S03` |
| `EXPECTED_REFUSAL` | `14` | `5` ca khớp tuyệt đối mã từ chối/hỏi lại (`S2-C-D05`, `S2-D-D07`, `S2-D-D09`, `S2-D-D10`, `S2-E-E01_oxyz`) + `9` ca từ chối/hỏi lại đúng bản chất bảo thủ nhưng mã chi tiết khác kỳ vọng chặt của scorer (`K-D01`, `K-D02` `DEGENERATE_POINTS`; `S2-D-D04` `INCONSISTENT_FACTS` ở bước đối chiếu sau; `S2-E-E03`, `S2-E-E04`, `S2-E-E05`, `S2-E-E06` `OUT_OF_SCOPE`; `S2-C-C05` `CLARIFY: MISSING_DATA`; `R1-E01` `CLARIFY: AMBIGUOUS`) |
| `EXTRACTION_FAILURE` | `30` | **(a) `8` ca thiếu `MathGoalSpec.solid_id` tùy chọn trên bài 1 khối (nhưng đáp số toán học đúng 100% oracle):** `K-C01`, `K-C04`, `S2-F-F05`, `R1-A02`, `R1-A04`, `R1-C01`, `R1-D01`, `R1-D02`.<br>**(b) `10` ca wire `simulation_goals` ghi `kind="construct_object"` + `target_section_id` thay vì `"construct_plane_section"`:** `K-A01..K-A04`, `K-B01`, `K-B02`, `K-E01`, `R1-B01`, `R1-B02`, `R1-C02`.<br>**(c) `6` ca đưa điểm đã đặt tên vào `described_points` (hoặc dây phụ thuộc kéo theo):** `K-C02`, `K-C03`, `K-C06`, `S2-A-I12`, `S2-B-P07`, `S2-B-P09`.<br>**(d) `2` ca sinh tag gợi ý ngoài từ điển đóng trong `UnresolvedSpec`:** `K-E02`, `S2-E-E02`.<br>**(e) `4` ca đề mơ hồ Gemini không gắn `unresolved` hoặc chọn nhầm mã `UNRECOGNIZED_WORDING` (đều bị tầng tất định chặn an toàn):** `S2-C-A01`, `S2-C-C04`, `S2-C-C06`, `R1-E02`. |
| `SOURCE_GATE_FAILURE` | `10` | **(a) `1` ca hạn chế đã biết của Source Gate trước tiếng Việt gõ thiếu dấu (`S-1`):** `S2-F-S07_typo_tone` (`"hình chop"` → `UNGROUNDED_VALUE`).<br>**(b) `9` ca tương tác trích xuất quote hẹp / paraphrase giữa Gemini và `kiem_nguon` (chặn fail-closed):** `S2-A-I08`, `S2-C-D06` (`UNKNOWN_LABEL` chặn nhãn bịa), `S2-D-D03`, `S2-D-D08`, `S2-F-S08`, `S2-F-F06`, `R1-A01`, `R1-A03`, `R1-A05`. |
| `FACT_GRAPH_FAILURE` | `0` | Không phát sinh lỗi biểu diễn FactGraph |
| `PLANNER_FAILURE` | `0` | `19/19` ca qua Source Gate đều lập kế hoạch đúng |
| `REGISTRY_COVERAGE_GAP` | `0` | Không phát sinh ca khả giải nào qua được Source Gate mà thiếu hàm trong Registry `/32` |
| `KERNEL_FAILURE` | `0` | `0` lỗi số học/căn thức/suy biến sai; mọi chứng chỉ hình học đều xác minh chính xác |
| `ADAPTER_FAILURE` | `0` | `19/19` kế hoạch thực thi đều chuyển đổi sang envelope `/4` hợp lệ |
| `PROVIDER_FAILURE` | `1` *(ngân sách nội bộ, `0` lỗi Google ở Run 3)* | `R1-F01` bị chặn **trước khi gửi request** bởi `GlobalBudgetLedger` nội bộ khi tổng chiến dịch chạm đúng `70 / 70` HTTP requests. *(Ở Run 1 & Run 2 trước đó, `6` lỗi `HTTP 400` là lỗi tương thích `responseSchema` của client với Gemini constrained decoding, không phải lỗi 403/429/billing, và đã được sửa triệt để ở `8853c4b0`.)* |
| `UNKNOWN` | `0` *(trong 66 ca đã chạy; `4` ca `R1-F02..R1-G02` là `NOT_MEASURED`)* | Không có lỗi không xác định trong 66 ca đã chạy |

---

## 8. Các Bản Sửa Lỗi Backend Thực Nghiệm Đã Triển Khai (TDD `RED -> GREEN`)

Toàn bộ các sửa đổi đều nằm gọn trong `backend/app/ai/` (`0` thay đổi trên `frontend/**`, `0` thay đổi trên `LLM_ONLY`, `0` thay đổi trên Kernel/Planner/Registry):

1. **Sửa lỗi tương thích OpenAPI `ARRAY` tuple (`48372208`, `backend/app/ai/function_calling.py`):**
   - **Lỗi thực tế (Run 1):** Google Gemini trả `HTTP 400 INVALID_ARGUMENT: GenerateContentRequest.generation_config.response_schema.properties[premises].items.properties[operands].items: missing field` vì JSON Schema draft 2020-12 dùng `prefixItems` cho tuple cố định, còn Gemini OpenAPI subset bắt buộc `items` đơn.
   - **Khắc phục:** Hợp nhất schema phần tử của `prefixItems` thành `items` chuẩn OpenAPI và kiểm thử TDD.
2. **Sửa lỗi tràn trạng thái FSM của Constrained Decoding (`8853c4b0`, đóng băng tại `44568bc9`, `backend/app/ai/typed_fact_next_extraction.py`):**
   - **Lỗi thực tế (Run 2):** Google Gemini trả `HTTP 400 INVALID_ARGUMENT: The specified schema produces a constraint that has too many states for serving` trên schema đệ quy/enum lồng nhau `16,541` byte.
   - **Khắc phục:** Thiết kế wire schema phẳng `4,333` byte (`3,339` structural bytes) với `propertyOrdering` tường minh + bộ chuẩn hóa tất định `_normalize_transport_payload` trước khi đưa vào `decode_typed_fact_next_v2_payload` giữ nguyên 100% kiểm tra fail-closed. **Đã kiểm chứng live thành công tuyệt đối ở Run 3 (`64 / 64` HTTP 200 `STOP`).**
3. **Sửa lỗi chuẩn hóa wire hậu nghiệm từ dữ liệu Run 3 (`f60ae29e`, đóng băng tại `428515dc`, `backend/app/ai/typed_fact_next_extraction.py`):**
   - **Lỗi thực tế (Run 3):** Ba mẫu lệch hình thức trên wire JSON của Gemini: (i) ghi `simulation_goals` thiết diện bằng `kind="construct_object"` + `target_section_id` (không có `target_solid_id`) thay vì `kind="construct_plane_section"`; (ii) lược bỏ `solid_id` tùy chọn trên `MathGoalSpec(kind="measurement")` khi bài chỉ có đúng 1 khối gốc và không dựng khối dẫn xuất; (iii) sinh chuỗi gợi ý tự do trong `unresolved.missing_roles` / `unresolved.candidate_relations` do wire schema đã bỏ `enum` để tránh tràn FSM.
   - **Khắc phục (TDD `RED -> GREEN`, `30/30` test trong `test_typed_fact_next_extraction.py`):**
     - Ánh xạ `construct_object` + `target_section_id` (khi không xung đột `target_solid_id`) về `construct_plane_section` khớp đúng `SimulationGoalSpec` và `typed_fact_next_bridge.py` (trường hợp có cả `target_solid_id` và `target_section_id` vẫn bị chặn fail-closed `INVALID_SIMULATION_GOAL`).
     - Điền mặc định `solid_id` duy nhất cho `MathGoalSpec(kind="measurement")` trên bài 1 khối khi không có khối dẫn xuất hay xung đột `target`.
     - Lọc `missing_roles` / `candidate_relations` theo tập từ điển đóng `MISSING_ROLES` / `CANDIDATE_RELATIONS` (`[:3]`), trong khi `unresolved.kind` sai vẫn bị từ chối fail-closed.
     - Bổ sung quy tắc ngắn gọn trong `TYPED_FACT_NEXT_SYSTEM_INSTRUCTION` cho điểm có tên (`premises`, không đưa vào `described_points`), `construct_plane_section`, `solid_id`, và trích dẫn `quote` trọn câu; kích thước wire `responseSchema` giữ nguyên `4,333` byte.

---

## 9. Chẩn Đoán Replay Offline Tách Biệt Sau Bản Vá `f60ae29e` (`0` Live Call Mới)

> [!WARNING]
> **Ranh giới minh bạch (`AGENTS.md §4`):** Bảng dưới đây là **chẩn đoán replay offline (`OFFLINE_CAPTURED_WIRE_REPLAY`)** chạy lại chính `64` JSON wire thô đã thu ở Run 3 qua `_normalize_transport_payload` mới tại commit `f60ae29e` (`0` HTTP request mới). Kết quả này **tuyệt đối không được gọi là số đo live mới** và không dùng để thay thế bảng Live Run 3 ở Mục 5; nó chỉ chứng minh tác động cô lập của bộ chuẩn hóa wire trước khi Owner cấp ngân sách cho vòng live kế tiếp.

| Tập & Chỉ số | Live Run 3 gốc (`44568bc9`, đã đóng băng) | Replay Offline cùng 64 wire payload sau `f60ae29e` (`0` HTTP call) | Thay đổi đã chứng minh |
|---|---|---|---|
| **`K-1` `end_to_end_correct`** | `1 / 16` (`6.25%`) | **`6 / 16` (`37.5%`)** | Tăng `+5` ca (`K-C01`, `K-C04`, `K-D02`, `K-E01`, `K-E02`); số ca `SERVED` tăng `3 → 4` (thêm thiết diện `K-A02` diện tích `3√2/2` khớp oracle), `clarification_correctness = 2/2 (100%)` |
| **`K-1` `wrong_served_end_to_end` (scorer)** | `2 / 16` (`12.5%`) | `1 / 16` (`6.25%` — `K-A02` đúng đáp số `3√2/2`, chỉ dư goal mô phỏng thiết diện so với gold) | Xóa bỏ hoàn toàn lỗi thiếu `solid_id` ở `K-C01`, `K-C04`; **`0 / 16` đáp số toán học sai** |
| **`S-2` `end_to_end_correct`** | `15 / 36` (`41.7%`) | **`16 / 36` (`44.4%`)** | `S2-F-F05` (`√2`) chuyển từ `SERVED_WRONG` sang `SERVED_CORRECT` (`11` ca `SERVED_CORRECT`) |
| **`S-2` `wrong_served_end_to_end` (scorer)** | `1 / 36` (`2.8%`) | **`0 / 36` (`0.0%`)** | **`0 / 36` cả theo chữ ký scorer lẫn theo oracle toán học** |
| **`R-1` `end_to_end_correct`** | `0 / 13` (`0.0%`) | **`5 / 13` (`38.5%`)** | Tăng `+5` ca (`R1-A02`, `R1-A04`, `R1-C01`, `R1-D01`, `R1-D02`); số ca `SERVED` tăng `5 → 7` (thêm thiết diện `R1-B02 = 4` và `R1-C02 = 3/2`, cả `7/7` khớp 100% oracle); `goal_completeness` tăng `0/11 → 8/11 (72.7%)` |
| **`R-1` `wrong_served_end_to_end` (scorer)** | `5 / 13` (`38.5%`) | `2 / 13` (`15.4%` — `R1-B02`, `R1-C02` đúng đáp số `4` và `3/2`, chỉ lệch chữ ký goal thiết diện) | Xóa bỏ toàn bộ `5/5` lỗi thiếu `solid_id`; **`0 / 13` đáp số toán học sai** |

---

## 10. Trả Lời Trực Tiếp 10 Câu Hỏi Quyết Định Cutover (Mục VII)

1. **Gemini live trích xuất `TypedFactNext /2` chính xác đến mức nào trên đề tiếng Việt thực tế?**
   - Về bảo toàn toán hạng và trích dẫn (`operand_preservation`): đạt `87.5%` trên `S-2` (`21/24`), `100%` trên `R-1` (`11/11`), `100%` trên `constraints` (`6/6`) và `100%` trên `described_points` không tên của `R-1` (`11/11`). Tuy nhiên khớp tuyệt đối toàn bộ chữ ký `extraction_accuracy` mới đạt `35.7%`–`41.7%` do 3 lỗi chính: đặt điểm có tên vào `described_points`, cắt `quote` thiếu ngữ cảnh đầu câu khiến Source Gate từ chối, và lệch quy ước goal thiết diện/`solid_id` (lỗi thứ ba đã xử lý ở `f60ae29e`).
2. **Khi Gemini trích xuất sai, thiếu hoặc bịa, hệ thống Hybrid có chặn được hoàn toàn không?**
   - **CÓ (`100%` trên toàn bộ `65` ca đánh giá live).** Không có một ca nào Gemini bịa đỉnh (`S2-C-D06`), bỏ sót sự mơ hồ (`S2-C-C04`, `S2-C-C06`, `R1-E02`) hay gặp đề mâu thuẫn (`K-B02`, `K-D01/D02`, `S2-D-*`) mà lọt qua được `Source Gate` / `Bridge` / `Exact Kernel`. Số ca phục vụ đáp số sai toán học là **`0 / 65`**.
3. **Chi phí và độ trễ mỗi bài của Gemini 2.5 Flash trên kiến trúc Hybrid là bao nhiêu?**
   - Chi phí rất thấp: trung bình **`USD 0.00532` / lời gọi** theo giá chuẩn không cache (`USD 0.00497` / lời gọi khi tính chiết khấu implicit cache), tức ~`190`–`200` bài toán cho mỗi `USD 1.00`.
   - Độ trễ: Backend tất định cực nhanh (`p50 = 66 ms`, `max = 801 ms`), nhưng Gemini HTTP mất **`p50 = 8.59s`, `p90 = 13.90s`, `max = 20.86s`** do suy luận `thoughtsTokenCount` (`mean = 1,209` token).
4. **Planner `/26` và Exact Kernel `/24` hoạt động thế nào trước đầu ra thật của Gemini?**
   - Đạt **`19 / 19` (`100%`)** chính xác tuyệt đối trên mọi payload vượt qua `Source Gate`, bao gồm `4` chuỗi phân rã định nghĩa nhiều bước (`circumcenter`, `orthocenter`, khoảng cách hai hình chiếu ẩn) và các căn thức biểu tượng phức tạp (`√673/8`, `2√6/3`, `√41/2`, `3√2/2`).
5. **Nguyên nhân lớn nhất làm giảm tỷ lệ phục vụ (`false_refusal`) hiện nay nằm ở đâu?**
   - **100% nằm ở ranh giới `Gemini Extraction ↔ Source Gate`**, không nằm ở Planner, Registry hay Kernel. Sau khi `f60ae29e` gỡ nút thắt wire `construct_plane_section` và `solid_id`, hai nguyên nhân còn lại là: (i) Gemini đặt điểm có tên tường minh vào `described_points` (`6` ca) và (ii) Gemini chép `quote` quá ngắn làm `kiem_nguon` từ chối `PREDICATE_NOT_IN_QUOTE` / `SOURCE_OBJECT_MISMATCH` (`9` ca), cộng `1` ca tiếng Việt không dấu (`S2-F-S07`).
6. **Các bản sửa ở commit `f60ae29e` đã đủ để tuyên bố Hybrid vượt qua kiểm định live chưa?**
   - **CHƯA.** Dù replay offline trên `64` wire payload thực tế cho thấy `end_to_end_correct` tăng mạnh (`K-1`: `6.25% → 37.5%`, `R-1`: `0% → 38.5%`, `S-2` `wrong_served = 0%`), phần thay đổi `TYPED_FACT_NEXT_SYSTEM_INSTRUCTION` (nhằm sửa lỗi `described_points` cho điểm có tên và độ phủ `quote`) **bắt buộc phải được đo lại bằng một lượt gọi Gemini live mới** mới có giá trị thực nghiệm.
7. **Deadline và cấu hình timeout của route sản phẩm hiện tại đã an toàn cho lưu lượng thật chưa?**
   - **CHƯA ĐỦ DƯ ĐỊA.** Đỉnh latency đơn lẻ của `gemini-2.5-flash` trên Run 3 là `20.86s` (`K-B02`) và `18.06s` (`S2-E-E06`), vượt ngưỡng `15.0s` E2E deadline mặc định của `hybrid_offline.py`. Cần điều chỉnh cấu hình timeout/thinking trước khi mở mặc định.
8. **Đã đủ điều kiện chuyển `DEFAULT_MODE` từ `LLM_ONLY` sang Hybrid chưa?**
   - **KHÔNG (`HYBRID_CUTOVER_BLOCKED` / `NO-GO`).** Chưa đạt độ phủ phục vụ đề dương tính trên live, còn `4` ca `R-1` chưa đo, chưa chạy bộ `H-1` độc lập (`60` bài do tác giả độc lập biên soạn) và chưa chạy đánh giá bắt cặp live `Hybrid vs LLM_ONLY` (`D-11`).
9. **Có được phép xóa `LLM_ONLY` hoặc các module legacy ngay bây giờ không?**
   - **TUYỆT ĐỐI KHÔNG (`LEGACY_REMOVAL_BLOCKED`).** `LLM_ONLY` vẫn là route mặc định đang phục vụ sản phẩm; ngoài ra `74` module (`49,012` dòng) là `SHARED_COMPONENT` mà Adapter `/4` dùng chung, và `hybrid_offline.py` vẫn nhập `RoutePolicy` từ `app.ai.pipeline`.
10. **Điều kiện tối thiểu, chính xác và ngắn nhất để mở khóa Cutover ở vòng tiếp theo là gì?**
    1. Owner cấp ngân sách live bổ sung nhỏ (ví dụ `<= 80` requests / `USD 1.00`) trên candidate `428515dc` (`f60ae29e`) để đo lại trọn vẹn `K-1 (16) + S-2 (36) + R-1 (18 = đủ cả 4 ca cuối)` và xác nhận `false_refusal` đã giảm mạnh mà vẫn giữ `0` đáp số toán học sai.
    2. Tinh chỉnh `HYBRID_LIVE_DEADLINE_S` (hoặc `thinkingBudget`) để không cắt nhầm đuôi `p95`–`p99` (`18s`–`21s`) của `gemini-2.5-flash`.
    3. Hoàn tất bộ đề độc lập `H-1` (`D-04`) và lượt đo đối chiếu bắt cặp live `LLM_ONLY vs Hybrid` (`D-11`, `GATE-16`), sau đó trình Owner phê duyệt `D-13`.

---

## 11. Đối Chiếu Cổng Chuyển Đổi (`docs/MIGRATION_CHECKLIST.md`)

- **Các điều kiện đã đóng hoặc tiến triển bằng bằng chứng thật trong lượt này:**
  - **Cổng hạ tầng & đo lường live bước đầu (`GATE-16` một phần):** Đã thu thập số liệu thật đầu tiên về token (`prompt`, `output`, `thinking`, `cached`), độ trễ tách lớp (`HTTP` vs `deterministic backend`), và chi phí USD thực tế của `gemini-2.5-flash` trên `64` lời gọi HTTP 200.
  - **Độ tin cậy toán học & fail-closed (`D-02`, `D-06`, `D-12`):** Được củng cố bằng bằng chứng live (`19/19` ca `SERVED` đúng đáp số biểu tượng chính xác, `0/65` ca phục vụ sai, `0` ca lọt lưới ảo giác, rollback `HYBRID_ROUTE_MODE=off` nguyên vẹn).
- **Các cổng còn mở chặn Cutover (`HYBRID_CUTOVER_BLOCKED`):**
  - **`D-04` (Held-out độc lập `H-1`):** Chưa có tập đề từ người biên soạn độc lập ngoài agent phát triển.
  - **`D-11` & `GATE-16` (Đánh giá bắt cặp live `Hybrid vs LLM_ONLY` trên cùng tập đề):** Chưa thực thi; đồng thời cần đo lại `K-1/S-2/R-1` (gồm `4` ca cuối của `R-1`) trên candidate `428515dc` sau bản sửa `f60ae29e`.
  - **`D-13` (Phê duyệt Cutover của Owner):** `NO-GO` — giữ nguyên `DEFAULT_MODE = LLM_ONLY`, `HYBRID_ROUTE_MODE = off`, `CACHE_VERSION = 131`, giữ nguyên toàn bộ mã `LLM_ONLY`.
