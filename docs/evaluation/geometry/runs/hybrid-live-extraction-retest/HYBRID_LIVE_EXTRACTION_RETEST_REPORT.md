# Hybrid live extraction retest (C26) — báo cáo

Run `hybrid-live-extraction-retest` · Master Epic `ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT` · **backend only**
(`frontend/**`: 0 file) · 2026-11-03.

> [!IMPORTANT]
> **Nhãn (gán theo luật đã đăng ký trước tại [`preregistration.md`](preregistration.md), commit `180db769`, trước request đầu tiên):**
> - `LIVE_REGRESSION_MEASURED` = **YES** — 70/70 ca K-1/S-2/R-1 đo live trên **một** candidate, 0 dòng `NOT_RECOVERABLE`.
> - `LIVE_GEMINI_QUALITY_VALIDATED` = **NO** (theo cấu trúc: bộ đề đã dùng để tìm và sửa lỗi, nhiễm phát triển).
> - `HYBRID_CUTOVER_READY` = **NO** → **`HYBRID_CUTOVER_BLOCKED`** (còn thiếu H-1/D-04, paired live/D-11, Owner/D-13).
> - **An toàn: 0 đáp số toán học sai, 0 ca âm tính bị phục vụ** (37/37 ca SERVED khớp oracle, có chứng chỉ).
> - **False refusal trên đúng 39 ca dương tính Run 3 đã đo: 20/39 → 2/39** (luật "giảm" đã đăng ký: < 20 và an toàn 0/0 — đạt).

## 1. Git identity & candidate

| | giá trị |
|---|---|
| nhánh | `research/hybrid-master-backend-replacement` (không merge, không push) |
| bắt đầu | `feb9ca68` (product `f60ae29e`, candidate `428515dc`, `e758e25a…`) |
| product C26 | `d331e75b` — sửa trích xuất + siết chỉ dẫn |
| runner C26 | `7c66a466` — chiến dịch C26, ledger nối tiếp, dùng lại dòng canary |
| candidate | `180db769` — `EVALUATION_CANDIDATE.json` `276fc548196e13ea…` (118 file), template rebind (runner `d1dc51d7…`), pre-registration |
| canary receipt | `802818e5` |
| không đổi | Registry `/32`, Planner `/26`, Engine `/24`, TypedFactNext `/2`, Adapter `/4`, Source Gate, `DEFAULT_MODE = LLM_ONLY`, `HYBRID_ROUTE_MODE = off`, `CACHE_VERSION = 131`, wire `responseSchema` |

## 2. Lỗi đã sửa trước live (TDD RED → GREEN, `test_typed_fact_next_observed_repairs.py`: 7 RED trên `f60ae29e` → 11/11 GREEN)

Tất cả trong `_normalize_transport_payload` → `_repair_observed_wire_shapes` ([typed_fact_next_extraction.py](../../../../../backend/app/ai/typed_fact_next_extraction.py)); chỉ áp dụng trên đường transport (gold replay không đi qua). Mỗi bản vá có ca đối kháng phải **giữ nguyên** (rồi fail-closed ở hạ nguồn); test kiểm mọi quote sau sửa vẫn là chuỗi con nguyên văn của đề.

| lỗi Run 3 (wire thật) | ca | bản vá tổng quát | đối kháng giữ nguyên |
|---|---|---|---|
| điểm **có tên** khai ở `described_points` ("M là trung điểm của AB") ⇒ `INVALID_DESCRIBED_POINT` / `DANGLING_DEPENDENCY` / `SOURCE_OBJECT_MISMATCH` | K-C02/C03/C06, S2-A-I12, S2-B-P07/P09, K-A01/A04, K-B02 | quote khớp `^(Gọi )?<Nhãn> là ` + kind có premise tương ứng ⇒ premise; `@id` ⇒ nhãn | tâm ngoại tiếp/trực tâm (không có premise), điểm không tên, điểm phụ thuộc điểm mô tả chưa chuyển |
| "hình vuông" khai `rectangle` ⇒ `PREDICATE_NOT_IN_QUOTE` | S2-F-F06, R1-A01/A03/A05, R1-B01, R1-E02 | ⇒ `regular_polygon` 4 đỉnh; bản trùng bỏ | "hình chữ nhật" |
| "hình vuông cạnh 2" tách thành polygon không cạnh + `segment_length` "cạnh 2" | S2-A-I08, S2-F-S08, K-C02/C03 … | gộp khi "cạnh v" **liền kề** trong đề và cạnh thuộc đa giác | không liền kề; giá trị khác (không bao giờ bỏ im lặng) |
| quote đa giác thiếu tên ("hình vuông cạnh 4") | R1-A01, S2-D-D03 | chỉ lấy đúng mệnh đề liền trước "(đáy) ABCD là " | — |
| `altitude` tự suy từ "SA ⊥ (ABCD)" | S2-A-I08 | bỏ nếu quote không có "đường cao/chiều cao" và trùng `perpendicular_line_plane` | đường cao được nêu: giữ, chỉ nối quote với khối duy nhất **cùng câu** (không vượt dấu câu) |
| `height` cho "MM' = 5" | S2-D-D08, K-C06 | ⇒ `segment_length` khi tách đúng 2 nhãn của khối; trùng thì bỏ | "chiều cao bằng 5" |

Chỉ dẫn `TYPED_FACT_NEXT_SYSTEM_INSTRUCTION`: hình vuông không là `rectangle`, cạnh ở `side`; không suy `altitude`; "MM' = 5" là `segment_length`; mặt phẳng/đường/kích thước không được nêu ⇒ `unresolved missing_operand`, không tự điền.
Không sửa: Planner/Registry/Kernel (0 ca lỗi ở đó), Source Gate (không nới lỏng), bridge "mục hỏi lại được trả lời trước" (quyết định đã được review, xem §11).

**Captured-wire replay** (offline, 0 call, cùng 64 payload đã dùng để sửa — chỉ chứng minh bản vá tác động đúng): false refusal 17/39 (`f60ae29e`) → 1/39 (`d331e75b`), 0 sai toán, 0 phục vụ âm tính ([captured-wire-replay-d331e75b.jsonl](captured-wire-replay-d331e75b.jsonl)); khoá bởi `test_captured_run3_replay_serves_no_wrong_math_and_no_negative`.

## 3. Canary (10 ca đã đăng ký, tính vào 70 ca, không gửi lại)

10/10 HTTP 200 `STOP`, USD 0.0540085; 0 sai toán, 0 phục vụ âm tính, 1 lỗi wire (`INVALID_MATH_GOAL`, S2-C-C04) < ngưỡng dừng 2 ⇒ **tiếp tục cùng candidate**. 7/7 ca dương tính canary (đều FALSE_REFUSAL hoặc INVALID ở Run 3) nay SERVED đúng oracle. Receipt: [`canary/`](canary/c21-delegated-execution-receipt.json).

## 4. Live HTTP requests & ngân sách (chiến dịch C26: ≤ 80 request / ≤ USD 1.00)

| lượt | HTTP | trạng thái | USD (runner) | ledger |
|---|---:|---|---:|---|
| canary | 10 | 10 × 200 `STOP` | 0.0540085 | `canary/c26-global-budget-ledger.json` |
| full | 59 | 59 × 200 `STOP` | 0.2959044 | `full/c26-global-budget-ledger.json` (`carried_from` canary, sha256 `1d6adfb0…`) |
| **tổng C26** | **69 / 80** | **69 × 200, 0 retry, 0 lỗi 4xx/5xx, `serviceTier = standard` 69/69** | **0.3499129 / 1.00** (upper = reported) | |

S2-E-E01 bị Domain Gate chặn (0 HTTP). C21 (70/70, USD 0.4957929 upper) giữ nguyên, không reset. Paid tier: `OWNER_ATTESTED` (`owner-paid-attestation.json` sha256 `e89153f5…`, `project_id = null`), **không** `CLOUD_BILLING_VERIFIED`.

## 5. K-1 / S-2 / R-1 — đo đủ 70/70

| pilot | ca | SERVED (đúng oracle) | false refusal | âm tính không phục vụ | âm tính đúng lý do | e2e đúng | Run 3 e2e |
|---|---:|---:|---:|---:|---:|---:|---:|
| K-1 | 16 | 10 (10) | 0/10 | 6/6 | 4/6 | 10/16 | 1/16 |
| S-2 | 36 | 16 (16) | 2/18 | 18/18 | 10/18 | 26/36 | 15/36 |
| R-1 | 18 | 11 (11) | 2/13 | 5/5 | 2/5 | 10/18 | 0/14 |
| **tổng** | **70** | **37 (37)** | **4/41** | **29/29** | **16/29** | **46/70** | 16/66 |

*(Cột SERVED = mọi ca được phục vụ: 30 `SERVED_CORRECT` + 7 đúng toán nhưng lệch hợp đồng, §10; 37/37 khớp oracle.)*

## 6. Chất lượng trích xuất (scorer không đổi; trên payload transport đã chuẩn hoá — payload backend thật sự dùng)

| chỉ số | K-1 Run 3 → C26 | S-2 Run 3 → C26 | R-1 Run 3 → C26 |
|---|---|---|---|
| extraction_accuracy | 5/14 → **14/14** | 10/24 → **23/24** | 4/11 → **15/15** |
| goal_completeness | 1/14 → 8/14 | 20/24 → 23/24 | 0/11 → 12/15 |
| operand_preservation | 8/14 → 14/14 | 21/24 → 24/24 | 11/11 → 15/15 |
| ambiguity_detection | 2/2 → 2/2 | 3/6 → 5/6 | 1/2 → 1/2 |
| clarification_correctness | 0/0 → 2/2 | 2/3 → 3/3 | 1/1 → 1/2 |
| false_clarification | 0/14 → 0/14 | 0/30 → 0/30 | 0/11 → 1/16 |
| unsupported_classification | — | 5/6 → 5/6 | — → 2/3 |
| constraints (K-1) emitted/kinds/operands/quotes/no-invented | 6/6 · 6/6 · 6/6 · 6/6 · 3/6 → **6/6 · 6/6 · 6/6 · 6/6 · 6/6** | | |

> [!NOTE]
> Phần đóng góp của **mô hình** (chỉ dẫn mới) so với **bản vá tất định** trong từng payload là `NOT_RECOVERABLE`: runner chỉ lưu payload sau chuẩn hoá, không lưu văn bản wire thô.

## 7. False refusal — so sánh định lượng trên cùng 39 ca dương tính

**20/39 → 2/39.** 19 ca chuyển sang SERVED đúng oracle: K-A01–A04, K-C02/C03/C06, S2-A-I08, S2-A-I12, S2-B-P07, S2-B-P09, S2-F-S08, S2-F-F06, R1-A01, R1-A03, R1-A05, R1-B01, R1-B02, R1-C02. Còn lại:
- `S2-F-S07_typo_tone` — `UNGROUNDED_VALUE`; gold replay cũng từ chối ⇒ giới hạn Source Gate với "hình chop" (S-1, không đổi; từ chối an toàn).
- `S2-B-A03_control_with_dimensions` — **ca mới bị từ chối** (Run 3: SERVED_CORRECT). Wire: Gemini thêm mục mô phỏng thứ hai `{"kind":"construct_object","target_solid_id":"s1","vertex":"H"}` cho "điểm H" ⇒ `INVALID_SIMULATION_GOAL` (khoá ngoài hợp đồng). Fail-closed, không sai toán; dao động của mô hình dưới chỉ dẫn mới. Không vá ở lượt này: ánh xạ `vertex` → `target_refs` là đoán hợp đồng, chưa có bằng chứng thứ hai.

Hai ca chưa từng đo (R1-G01/G02, câu diễn đạt lại) đều `FALSE_REFUSAL` `SOURCE_OBJECT_MISMATCH`, **gold replay cũng từ chối** (`DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD`) ⇒ giới hạn Source Gate đã ghi từ C15. Tổng trên 41 dương tính: **4/41**.

## 8. Từ chối đúng / làm rõ trên ca âm tính

29/29 ca âm tính không bị phục vụ. Đúng lý do 16/29 (Run 3: 5/27). Thay đổi chính: K-D01/D02 → `DEGENERATE_POINTS` đúng lý do; K-E01/E02 → `CORRECT_CLARIFICATION`; S2-D-D03/D04/D08 → `INCONSISTENT_FACTS` đúng lý do (trước bị chặn sớm ở Source Gate); S2-E-E02/E04/E05 → `OUT_OF_SCOPE`; S2-C-C06 nay hỏi lại `missing_operand` (đúng hướng, mã khác danh sách scorer). Còn lệch: S2-C-D05 (Run 3 CORRECT_CLARIFICATION → nay `QUOTE_NOT_IN_SOURCE`, Gemini chép quote không nguyên văn — vẫn chặn), S2-C-D06 (`UNKNOWN_LABEL`: Gemini bịa `ABC.A'B'C'`, tiếp tục bị chặn fail-closed đúng yêu cầu), S2-C-C04/R1-E02 (Gemini vẫn tự điền mặt phẳng ⇒ chặn ở bridge/Source Gate), R1-F03 (`unsupported` + `missing_operand` ⇒ bridge hỏi lại mục trả lời được — quyết định đã review, `test_review_r1_the_answerable_entry_is_described_whatever_the_order`), S2-E-E03 (`INVALID_SOLID_NOTATION`).

## 9. Sai toán học được phục vụ

**0/37.** 0 ca âm tính được phục vụ. Không có regression an toàn.

## 10. Lệch hợp đồng nghiêm ngặt (đúng toán, sai cấu trúc — vẫn theo dõi như lỗi)

7 ca (`SERVED_WRONG` theo scorer, tất cả đúng oracle): K-A01–A04, R1-B01/B02/C02 — Gemini thêm mục `construct_plane_section` cho câu "Xác định thiết diện …", đúng chỉ dẫn hệ thống nhưng gold không có ⇒ mâu thuẫn quy ước gold ↔ chỉ dẫn, không phải sai nghĩa. Run 3 có 8 ca loại này (do thiếu `solid_id`) — đã hết. Scorer và gold **không sửa**.

## 11. Quy kết Source Gate & các tầng

Trên 33 ca không được phục vụ: `SOURCE_GATE_FAILURE` 4 (S2-F-S07, R1-G01, R1-G02 — cả ba gold cũng chặn; S2-C-D05 quote không nguyên văn), `EXTRACTION_FAILURE` 4 (S2-B-A03, S2-C-C04, R1-E02, S2-E-E03), `EXPECTED_REFUSAL` 25 (16 đúng lý do + 9 đúng lớp, lệch mã). `FACT_GRAPH_FAILURE` 0, `PLANNER_FAILURE` 0, `REGISTRY_COVERAGE_GAP` 0, `KERNEL_FAILURE` 0, `ADAPTER_FAILURE` 0, `PROVIDER_FAILURE` 0.

## 12. Điểm có tên / điểm mô tả

K-1 `described_points` emitted/kinds/refs/quotes **8/8 · 8/8 · 8/8 · 8/8** (Run 3 kinds 5/8); R-1 **15/15** cả bốn. Không còn lỗi `INVALID_DESCRIBED_POINT` / `DANGLING_DEPENDENCY` trên 70 ca.

## 13. Planner

37/37 ca qua Source Gate được lập kế hoạch, thực thi và chứng nhận. K-1: 6 `REGISTERED_DECOMPOSITION` (tâm ngoại tiếp/trực tâm), R-1: 7 `SOURCE_EXPLICIT_SEQUENCE` + 1 `REGISTERED_DECOMPOSITION` (nhãn `composition_label` chỉ tính trên ca `SERVED_CORRECT`; 7 ca lệch hợp đồng mang nhãn `WRONG_SERVED`). **0 `GENUINE_DISCOVERY`** — `GENUINE_DISCOVERY_NOT_ESTABLISHED` giữ nguyên. Không sửa Planner (không có ca thoả 5 điều kiện ở mục IX).

## 14–16. Token, độ trễ, chi phí (69 HTTP 200, `wire-http-telemetry.jsonl` canary + full)

| | C26 (69) min / median / mean / p90 / max / sum | Run 3 (64) median / mean / max |
|---|---|---|
| prompt | 2,530 / 2,571 / 2,575.3 / 2,602 / 2,623 / 177,693 | 2,168 / 2,173.5 / 2,221 |
| output | 217 / 613 / 634.4 / 845 / 1,051 / 43,777 | 627.5 / 658.0 / 1,029 |
| thinking | 128 / 860 / 1,085.0 / 1,906 / 3,723 / 74,865 | 1,038.5 / 1,209.1 / 3,489 |
| cached (khi có mặt) | n = 30 (39 lời gọi `ABSENT`): 2,513 / 2,535 / 2,535.6 / 2,549 / 2,553 / 76,068 | n = 43 (21 `ABSENT`) |
| total | 2,875 / 4,119 / 4,294.7 / 5,106 / 6,656 / 296,335 | 3,952.5 / 4,040.6 / 6,645 |
| HTTP latency (s) | 3.29 / 7.74 / 8.48 / 12.26 / 19.29 / 585.19 | 8.59 / 9.55 / 20.86 |
| case latency (s) | 3.33 / 7.81 / 8.56 / 12.30 / 19.33 | — |
| USD / lời gọi (runner) | 0.00162 / 0.00500 / 0.00507 / 0.00702 / 0.01104 / **0.349913** | mean 0.00532 |

Chỉ dẫn dài hơn ⇒ prompt +~400 token/bài; thinking và độ trễ giảm nhẹ; chi phí/bài ~USD 0.005 (~200 bài/USD). Độ trễ tất định (case − HTTP) ≈ trung vị 0.07 s. Cột cached theo dòng (`n/r` trong bảng §22) không có trong `usage` của runner — số liệu cached lấy từ telemetry wire.

## 17. Xác minh timeout runtime (đính chính báo cáo C25)

Đã đọc code route sản phẩm (`app/main.py` `HYBRID_ROUTE_MODE=live`): `HYBRID_LIVE_TIMEOUT_SECONDS` mặc định **60 s/lần thử**, `HYBRID_LIVE_DEADLINE_SECONDS` mặc định **3 × = 180 s**; biến môi trường hợp lệ (hữu hạn, > 0) thắng mặc định, giá trị sai quay về mặc định; `LiveHybridRun.run` truyền deadline đó cho cả transport và `run_hybrid_offline`. Mặc định 15 s chỉ là tham số của `run_hybrid_offline` khi gọi trực tiếp (harness), **không** phải giá trị route live.

> [!WARNING]
> **Đính chính:** `LIVE_GEMINI_EVALUATION_REPORT.md` §3.3 và câu 7 §10 nói route live dùng deadline 15 s và sẽ cắt phản hồi 20.86 s — **sai**. Giá trị thực là 60 s / 180 s; phản hồi dài nhất quan sát (20.86 s Run 3, 19.29 s C26) không bị cắt. Không cần thay đổi cấu hình. Báo cáo cũ giữ nguyên byte; lớp đính chính này đăng ký trong `docs/EVIDENCE_INDEX.md`.

Khoá bởi [`test_hybrid_live_timeout_runtime.py`](../../../../../backend/tests/test_hybrid_live_timeout_runtime.py) (7 test): thứ tự env > mặc định; phản hồi hợp lệ 20.86 s được phục vụ với mặc định, ra **504 `HYBRID_DEADLINE_EXCEEDED`** nếu operator đặt 15 s, đúng 1 request, không fallback LLM_ONLY, không lộ khoá; request treo hết thời gian theo từng lần thử trong trần `MAX_ATTEMPTS`.

## 18. So sánh định lượng với Run 3 (cùng case ID, cùng oracle)

| | Run 3 (`44568bc9`) | C26 (`180db769`) |
|---|---|---|
| false refusal / 39 dương tính chung | 20 | **2** |
| SERVED (tất cả đúng oracle) | 19 / 65 | **37 / 70** |
| sai toán · phục vụ âm tính | 0 · 0 | **0 · 0** |
| âm tính đúng lý do | 5 / 27 | 16 / 29 |
| e2e đúng (quy tắc runner) | 16 / 66 | 46 / 70 |
| lệch hợp đồng nhưng đúng toán | 8 | 7 |
| HTTP latency median | 8.59 s | 7.74 s |
| USD / lời gọi | 0.00532 | 0.00507 |

## 19. Regression & Full T3

- Targeted trước freeze: 41 (trích xuất + bản vá) + 170 (product integration, timeout, preview, clarification) + 242 (thesis matrix, runner 106 + C26 3, candidate, docs IA, publication) — tất cả PASS.
- **Full T3** trên worktree tách rời sạch `hm-t3-180db769` tại `180db769`: **`FULL_PRODUCT_GATE_PASS`** — pytest **16 698** passed, 7 skipped, 2 deselected, 15 xfailed; vitest **85** file / **1 502** passed; freeze `--verify` MATCH trước/sau; 0 provider call ([full-t3-180db769.json](full-t3-180db769.json)).

## 20. Khuyến nghị cutover

**`HYBRID_CUTOVER_BLOCKED` — giữ `DEFAULT_MODE = LLM_ONLY`, `HYBRID_ROUTE_MODE = off`, không xoá LLM_ONLY.** Bằng chứng mới mạnh hơn rõ rệt (false refusal 20 → 2 trên cùng 39 ca, 0 sai toán, latency/chi phí chấp nhận được cho trải nghiệm học sinh ~8 s/bài), nhưng đây là bộ đề phát triển đã nhiễm. Bước kế tiếp hợp lệ, cần Owner: (1) corpus H-1 60 đề do tác giả độc lập (D-04); (2) ngân sách + quyền riêng cho paired live Hybrid vs LLM_ONLY (D-11, GATE-16); (3) quyết định D-13. Về parity LLM_ONLY: chưa đo; danh sách module `LEGACY_ONLY` (13) / `SHARED_COMPONENT` (74) không đổi.

## 21. Yêu cầu đánh giá độc lập còn thiếu

H-1 (`AUTHORING_INDEPENDENCE = NOT_ESTABLISHED`, 0 ca), D-11 (paired live), D-13 (Owner). Không dùng ngân sách C26 cho các mục này (C26 còn 11 request / USD 0.65 chưa dùng, không tự mở rộng).

## 22. Git state & publication

Commit rõ ràng từng file (`git add <file>`), không merge/push, `frontend/**` 0 file trong `feb9ca68..HEAD`, `check_publication_safety.py --range` PASS. Receipts C21 (`live-pilots-*`) không chạm.

### Bảng từng bài (70 ca, C26)

Cột token = prompt / output / thinking / cached / total từ `usage` của dòng runner (`n/r` = runner không ghi cached theo dòng; xem §14); `UNKNOWN` khi không có usage.

| Pilot | Case | Expected | C26 observed | C26 outcome | Code | Math vs oracle | Run 3 outcome | Composition | Tok in/out/think/cache/total | Lat (s) | USD | Source |
|---|---|---|---|---|---|---|---|---|---:|---:|---:|---|
| `K-1` | `K-A01` | `SERVED` | `SERVED` | `SERVED_WRONG` | `None` | exact ✅ `{"area": ["3√2/2"]}` | `FALSE_REFUSAL` | `WRONG_SERVED` | 2611 / 845 / 895 / n/r / 4351 | 10.95 | 0.005133 | canary |
| `K-1` | `K-A02` | `SERVED` | `SERVED` | `SERVED_WRONG` | `None` | exact ✅ `{"area": ["3√2/2"]}` | `FALSE_REFUSAL` | `WRONG_SERVED` | 2611 / 845 / 1650 / n/r / 5106 | 13.87 | 0.007021 | full |
| `K-1` | `K-A03` | `SERVED` | `SERVED` | `SERVED_WRONG` | `None` | exact ✅ `{"area": ["√61"]}` | `FALSE_REFUSAL` | `WRONG_SERVED` | 2623 / 1051 / 1576 / n/r / 5250 | 12.07 | 0.007354 | full |
| `K-1` | `K-A04` | `SERVED` | `SERVED` | `SERVED_WRONG` | `None` | exact ✅ `{"area": ["√61"]}` | `FALSE_REFUSAL` | `WRONG_SERVED` | 2623 / 1051 / 952 / n/r / 4626 | 9.3 | 0.005794 | full |
| `K-1` | `K-B01` | `REFUSED_UNDERDETERMINED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `PLANE_NOT_UNIQUE` | — | `WRONG_REASON_REFUSAL` | `EXTRACTION_FAILURE` | 2611 / 845 / 1606 / n/r / 5062 | 11.31 | 0.006911 | full |
| `K-1` | `K-B02` | `REFUSED_INCONSISTENT` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INCONSISTENT_FACTS` | — | `WRONG_REASON_REFUSAL` | `EXTRACTION_FAILURE` | 2612 / 864 / 1759 / n/r / 5235 | 13.38 | 0.007341 | full |
| `K-1` | `K-C01` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["1"]}` | `SERVED_WRONG` | `REGISTERED_DECOMPOSITION` | 2586 / 725 / 593 / n/r / 3904 | 6.68 | 0.004071 | full |
| `K-1` | `K-C02` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["1/4"]}` | `FALSE_REFUSAL` | `REGISTERED_DECOMPOSITION` | 2588 / 787 / 938 / n/r / 4313 | 8.44 | 0.005089 | canary |
| `K-1` | `K-C03` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["√66/4"]}` | `FALSE_REFUSAL` | `REGISTERED_DECOMPOSITION` | 2588 / 723 / 598 / n/r / 3909 | 6.79 | 0.004079 | full |
| `K-1` | `K-C04` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["2"]}` | `SERVED_WRONG` | `REGISTERED_DECOMPOSITION` | 2600 / 873 / 733 / n/r / 4206 | 7.81 | 0.004795 | full |
| `K-1` | `K-C05` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["√673/8"]}` | `SERVED_CORRECT` | `REGISTERED_DECOMPOSITION` | 2596 / 855 / 860 / n/r / 4311 | 8.45 | 0.005066 | full |
| `K-1` | `K-C06` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["2"]}` | `FALSE_REFUSAL` | `REGISTERED_DECOMPOSITION` | 2602 / 945 / 1354 / n/r / 4901 | 11.0 | 0.006528 | full |
| `K-1` | `K-D01` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `DEGENERATE_POINTS` | — | `WRONG_REASON_REFUSAL` | `CORRECT_REFUSAL` | 2586 / 728 / 1338 / n/r / 4652 | 9.52 | 0.005941 | full |
| `K-1` | `K-D02` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `DEGENERATE_POINTS` | — | `WRONG_REASON_REFUSAL` | `CORRECT_REFUSAL` | 2588 / 733 / 626 / n/r / 3947 | 6.82 | 0.004174 | full |
| `K-1` | `K-E01` | `CLARIFY` | `CLARIFY` | `CORRECT_CLARIFICATION` | `AMBIGUOUS_FACT` | — | `WRONG_REASON_REFUSAL` | `CORRECT_REFUSAL` | 2611 / 902 / 2819 / n/r / 6332 | 15.44 | 0.010086 | canary |
| `K-1` | `K-E02` | `CLARIFY` | `CLARIFY` | `CORRECT_CLARIFICATION` | `AMBIGUOUS_FACT` | — | `WRONG_REASON_REFUSAL` | `CORRECT_REFUSAL` | 2593 / 737 / 2224 / n/r / 5554 | 13.79 | 0.008180 | full |
| `R-1` | `R1-A01` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["√2"]}` | `FALSE_REFUSAL` | `SOURCE_EXPLICIT_SEQUENCE` | 2568 / 626 / 744 / n/r / 3938 | 6.79 | 0.004195 | canary |
| `R-1` | `R1-A02` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["2√6/3"]}` | `SERVED_WRONG` | `REGISTERED_DECOMPOSITION` | 2574 / 651 / 721 / n/r / 3946 | 7.04 | 0.004202 | full |
| `R-1` | `R1-A03` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["√17"]}` | `FALSE_REFUSAL` | `SOURCE_EXPLICIT_SEQUENCE` | 2568 / 632 / 754 / n/r / 3954 | 6.71 | 0.004235 | full |
| `R-1` | `R1-A04` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"angle_cos_sq": ["2/3"]}` | `SERVED_WRONG` | `SOURCE_EXPLICIT_SEQUENCE` | 2571 / 598 / 485 / n/r / 3654 | 6.05 | 0.003479 | full |
| `R-1` | `R1-A05` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"area": ["√6"]}` | `FALSE_REFUSAL` | `SOURCE_EXPLICIT_SEQUENCE` | 2569 / 620 / 999 / n/r / 4188 | 9.17 | 0.004818 | full |
| `R-1` | `R1-B01` | `SERVED` | `SERVED` | `SERVED_WRONG` | `None` | exact ✅ `{"area": ["2304/625"]}` | `FALSE_REFUSAL` | `WRONG_SERVED` | 2601 / 799 / 674 / n/r / 4074 | 7.69 | 0.004463 | full |
| `R-1` | `R1-B02` | `SERVED` | `SERVED` | `SERVED_WRONG` | `None` | exact ✅ `{"area": ["4"]}` | `FALSE_REFUSAL` | `WRONG_SERVED` | 2594 / 816 / 1156 / n/r / 4566 | 8.59 | 0.005708 | canary |
| `R-1` | `R1-C01` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["2", "√6"]}` | `SERVED_WRONG` | `SOURCE_EXPLICIT_SEQUENCE` | 2580 / 678 / 584 / n/r / 3842 | 6.21 | 0.003929 | full |
| `R-1` | `R1-C02` | `SERVED` | `SERVED` | `SERVED_WRONG` | `None` | exact ✅ `{"area": ["3/2"]}` | `FALSE_REFUSAL` | `WRONG_SERVED` | 2600 / 844 / 1178 / n/r / 4622 | 9.53 | 0.005835 | full |
| `R-1` | `R1-D01` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["√41/2"]}` | `SERVED_WRONG` | `SOURCE_EXPLICIT_SEQUENCE` | 2575 / 762 / 670 / n/r / 4007 | 6.79 | 0.004352 | full |
| `R-1` | `R1-D02` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["√3/3"]}` | `SERVED_WRONG` | `SOURCE_EXPLICIT_SEQUENCE` | 2572 / 636 / 1188 / n/r / 4396 | 8.73 | 0.005332 | full |
| `R-1` | `R1-E01` | `CLARIFY` | `CLARIFY` | `WRONG_REASON_CLARIFICATION` | `AMBIGUOUS_FACT` | — | `WRONG_REASON_CLARIFICATION` | `EXTRACTION_FAILURE` | 2568 / 560 / 1931 / n/r / 5059 | 12.3 | 0.006998 | full |
| `R-1` | `R1-E02` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `SOURCE_OBJECT_MISMATCH` | — | `WRONG_REASON_REFUSAL` | `EXTRACTION_FAILURE` | 2570 / 607 / 582 / n/r / 3759 | 5.93 | 0.003743 | canary |
| `R-1` | `R1-F01` | `REFUSED_UNSUPPORTED` | `REFUSED` | `CORRECT_REFUSAL` | `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` | — | `INFRASTRUCTURE_FAILURE` | `CORRECT_REFUSAL` | 2577 / 720 / 791 / n/r / 4088 | 7.22 | 0.004551 | full |
| `R-1` | `R1-F02` | `REFUSED_UNSUPPORTED` | `REFUSED` | `CORRECT_REFUSAL` | `BRIDGE_UNSUPPORTED_DESCRIBED_POINT` | — | `NOT_MEASURED` | `CORRECT_REFUSAL` | 2571 / 696 / 824 / n/r / 4091 | 6.9 | 0.004571 | full |
| `R-1` | `R1-F03` | `REFUSED_UNSUPPORTED` | `CLARIFY` | `FALSE_CLARIFICATION` | `AMBIGUOUS_FACT` | — | `NOT_MEASURED` | `EXTRACTION_FAILURE` | 2571 / 566 / 1842 / n/r / 4979 | 11.18 | 0.006791 | full |
| `R-1` | `R1-G01` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `SOURCE_OBJECT_MISMATCH` | — | `NOT_MEASURED` | `SOURCE_GROUNDING_FAILURE` | 2572 / 600 / 597 / n/r / 3769 | 6.22 | 0.003764 | full |
| `R-1` | `R1-G02` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `SOURCE_OBJECT_MISMATCH` | — | `NOT_MEASURED` | `SOURCE_GROUNDING_FAILURE` | 2569 / 629 / 495 / n/r / 3693 | 6.71 | 0.003581 | full |
| `S-2` | `S2-A-I02_ve` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ | `SERVED_CORRECT` | `None` | 2554 / 454 / 594 / n/r / 3602 | 5.54 | 0.003386 | full |
| `S-2` | `S2-A-I04_mo_phong` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ | `SERVED_CORRECT` | `None` | 2556 / 458 / 647 / n/r / 3661 | 5.57 | 0.003529 | full |
| `S-2` | `S2-A-I05_cho_minh_xem` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ | `SERVED_CORRECT` | `None` | 2555 / 456 / 650 / n/r / 3661 | 6.53 | 0.003531 | full |
| `S-2` | `S2-A-I08_trailing_ve` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ | `FALSE_REFUSAL` | `None` | 2561 / 461 / 618 / n/r / 3640 | 5.66 | 0.003466 | canary |
| `S-2` | `S2-A-I09_trailing_mo_phong_hinh` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ | `SERVED_CORRECT` | `None` | 2559 / 456 / 572 / n/r / 3587 | 6.18 | 0.003338 | full |
| `S-2` | `S2-A-I12_trailing_point` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ | `FALSE_REFUSAL` | `None` | 2570 / 502 / 1099 / n/r / 4171 | 8.41 | 0.004773 | full |
| `S-2` | `S2-B-A03_control_with_dimensions` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `INVALID_SIMULATION_GOAL` | — | `SERVED_CORRECT` | `None` | 2594 / 674 / 770 / n/r / 4038 | 6.77 | 0.004388 | full |
| `S-2` | `S2-B-I07_ve_va_tinh` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"volume": ["8/3"]}` | `SERVED_CORRECT` | `None` | 2564 / 548 / 658 / n/r / 3770 | 5.69 | 0.003784 | full |
| `S-2` | `S2-B-I10_ve_roi_tinh` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"volume": ["8/3"]}` | `SERVED_CORRECT` | `None` | 2566 / 546 / 663 / n/r / 3775 | 5.53 | 0.003792 | full |
| `S-2` | `S2-B-I11_mo_phong_va_tinh_SC` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["2√3"]}` | `SERVED_CORRECT` | `None` | 2565 / 543 / 634 / n/r / 3742 | 5.76 | 0.003712 | full |
| `S-2` | `S2-B-P07_shared_intermediate_two_goals` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["1", "√3"]}` | `FALSE_REFUSAL` | `None` | 2576 / 664 / 578 / n/r / 3818 | 6.08 | 0.003878 | canary |
| `S-2` | `S2-B-P09_student_chain` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["√3"]}` | `FALSE_REFUSAL` | `None` | 2571 / 613 / 779 / n/r / 3963 | 7.83 | 0.004251 | full |
| `S-2` | `S2-C-A01_goc_chieu` | `CLARIFY` | `CLARIFY` | `WRONG_REASON_CLARIFICATION` | `AMBIGUOUS_FACT` | — | `FALSE_CLARIFICATION` | `None` | 2538 / 294 / 2060 / n/r / 4892 | 11.06 | 0.006646 | full |
| `S-2` | `S2-C-C04_angle_plane_missing` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INVALID_MATH_GOAL` | — | `WRONG_REASON_REFUSAL` | `None` | 2561 / 578 / 1906 / n/r / 5045 | 11.26 | 0.006978 | canary |
| `S-2` | `S2-C-C05_draw_then_compute` | `CLARIFY` | `CLARIFY` | `WRONG_REASON_CLARIFICATION` | `AMBIGUOUS_FACT` | — | `WRONG_REASON_CLARIFICATION` | `None` | 2558 / 511 / 515 / n/r / 3584 | 5.5 | 0.003332 | full |
| `S-2` | `S2-C-C06_square_without_side` | `CLARIFY` | `CLARIFY` | `WRONG_REASON_CLARIFICATION` | `AMBIGUOUS_FACT` | — | `WRONG_REASON_REFUSAL` | `None` | 2554 / 527 / 1072 / n/r / 4153 | 9.88 | 0.004764 | full |
| `S-2` | `S2-C-D05_projection_missing_target` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `QUOTE_NOT_IN_SOURCE` | — | `CORRECT_CLARIFICATION` | `None` | 2569 / 579 / 1051 / n/r / 4199 | 7.89 | 0.004846 | full |
| `S-2` | `S2-C-D06_unnamed_prism` | `CLARIFY` | `REFUSED` | `WRONG_REASON_REFUSAL` | `UNKNOWN_LABEL` | — | `WRONG_REASON_REFUSAL` | `None` | 2530 / 217 / 128 / n/r / 2875 | 3.33 | 0.001622 | full |
| `S-2` | `S2-D-D03_contradictory_length` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` | — | `WRONG_REASON_REFUSAL` | `None` | 2567 / 575 / 497 / n/r / 3639 | 5.65 | 0.003450 | full |
| `S-2` | `S2-D-D04_two_values_same_segment` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` | — | `WRONG_REASON_REFUSAL` | `None` | 2567 / 574 / 1539 / n/r / 4680 | 9.45 | 0.006053 | full |
| `S-2` | `S2-D-D07_cube_rectangle_base` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` | — | `CORRECT_REFUSAL` | `None` | 2575 / 703 / 1265 / n/r / 4543 | 10.66 | 0.005692 | full |
| `S-2` | `S2-D-D08_cube_tall` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` | — | `WRONG_REASON_REFUSAL` | `None` | 2573 / 597 / 2225 / n/r / 5395 | 14.61 | 0.007827 | full |
| `S-2` | `S2-D-D09_base_edge_perp_base` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` | — | `CORRECT_REFUSAL` | `None` | 2571 / 630 / 1498 / n/r / 4699 | 10.42 | 0.006091 | full |
| `S-2` | `S2-D-D10_square_diagonal_3` | `REFUSED_INCONSISTENT` | `REFUSED` | `CORRECT_REFUSAL` | `INCONSISTENT_FACTS` | — | `CORRECT_REFUSAL` | `None` | 2567 / 613 / 939 / n/r / 4119 | 7.69 | 0.004650 | full |
| `S-2` | `S2-E-E01_oxyz` | `REFUSED_UNSUPPORTED` | `REFUSED` | `CORRECT_REFUSAL` | `gate_out_of_scope` | — | `CORRECT_REFUSAL` | `None` | 0 HTTP | 0.0 | 0.000000 | full |
| `S-2` | `S2-E-E02_truncated_pyramid` | `REFUSED_UNSUPPORTED` | `REFUSED` | `CORRECT_REFUSAL` | `OUT_OF_SCOPE` | — | `WRONG_REASON_REFUSAL` | `None` | 2566 / 241 / 1316 / n/r / 4123 | 8.09 | 0.004662 | full |
| `S-2` | `S2-E-E03_volume_maximum` | `REFUSED_UNSUPPORTED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `INVALID_SOLID_NOTATION` | — | `WRONG_REASON_REFUSAL` | `None` | 2546 / 387 / 3723 / n/r / 6656 | 19.33 | 0.011039 | full |
| `S-2` | `S2-E-E04_locus` | `REFUSED_UNSUPPORTED` | `REFUSED` | `CORRECT_REFUSAL` | `OUT_OF_SCOPE` | — | `WRONG_REASON_REFUSAL` | `None` | 2568 / 518 / 937 / n/r / 4023 | 7.78 | 0.004408 | full |
| `S-2` | `S2-E-E05_translation` | `REFUSED_UNSUPPORTED` | `REFUSED` | `CORRECT_REFUSAL` | `OUT_OF_SCOPE` | — | `WRONG_REASON_REFUSAL` | `None` | 2572 / 526 / 1194 / n/r / 4292 | 8.52 | 0.005072 | full |
| `S-2` | `S2-E-E06_word_problem_rate` | `REFUSED_UNSUPPORTED` | `REFUSED` | `WRONG_REASON_REFUSAL` | `OUT_OF_SCOPE` | — | `WRONG_REASON_REFUSAL` | `None` | 2566 / 592 / 2589 / n/r / 5747 | 15.16 | 0.008722 | full |
| `S-2` | `S2-F-F05_kc_mp_shorthand` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"distance": ["√2"]}` | `SERVED_WRONG` | `None` | 2561 / 552 / 658 / n/r / 3771 | 6.43 | 0.003793 | full |
| `S-2` | `S2-F-F06_dt_mp_shorthand` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"angle_cos_sq": ["2/3"]}` | `FALSE_REFUSAL` | `None` | 2560 / 522 / 1294 / n/r / 4376 | 8.86 | 0.005308 | full |
| `S-2` | `S2-F-S02_vuong_goc_day` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"volume": ["8/3"]}` | `SERVED_CORRECT` | `None` | 2558 / 537 / 646 / n/r / 3741 | 6.29 | 0.003725 | full |
| `S-2` | `S2-F-S03_symbol_perp` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"volume": ["8/3"]}` | `SERVED_CORRECT` | `None` | 2559 / 539 / 672 / n/r / 3770 | 7.07 | 0.003795 | full |
| `S-2` | `S2-F-S07_typo_tone` | `SERVED` | `REFUSED` | `FALSE_REFUSAL` | `UNGROUNDED_VALUE` | — | `FALSE_REFUSAL` | `None` | 2562 / 544 / 654 / n/r / 3760 | 6.14 | 0.003764 | full |
| `S-2` | `S2-F-S08_altitude_wording` | `SERVED` | `SERVED` | `SERVED_CORRECT` | `None` | exact ✅ `{"volume": ["8/3"]}` | `FALSE_REFUSAL` | `None` | 2555 / 497 / 1489 / n/r / 4541 | 8.87 | 0.005731 | canary |
