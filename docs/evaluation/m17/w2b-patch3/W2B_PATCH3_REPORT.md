# M17 Wave 2B-PATCH3 — Analyze Parameter Grounding (offline)

Đóng root defect PATCH2 live: analyze nhận đủ 5 operation nhưng để TRỐNG tham số
bắt buộc của 4/5 tầng. **Offline XONG; LIVE CHƯA CHẠY — dừng chờ duyệt (§M).**
Không mở Wave 2C. Không ghi đè artifact live cũ (`0afcb37`, `f2b28e2`, `4d9e8ac`).
Không nới completeness gate, không cho manifest đoán từ prose.

## 0. Trạng thái

| Gate | Trước (`9f717df`) | Sau PATCH3 |
|---|---|---|
| pytest | 1044 | **1071** (2 skip, 1 deselect) |
| vitest | 596 / 46 | **596 / 46** (FE không đổi) |
| build · conformance | sạch · 20/0 | **sạch · 20/0** |
| `CACHE_VERSION` | 21 | **22** |
| `config_contract_version` · `HISTORY_SCHEMA_VERSION` | table-1.1 · 2 | **không đổi** |

## 1. §A — Product decision

`database.relational_table_query` công bố hỗ trợ pipeline 5 tầng. Analyze **không
được** phát trạng thái "operation được yêu cầu nhưng tham số bắt buộc null" rồi
cho pipeline đi tiếp. Một requested stage chỉ **grounded** khi TOÀN BỘ tham số
bắt buộc đã trích từ evidence. Fail-closed vẫn giữ nếu không xác định được sau
bounded repair.

## 2. §C — Deterministic parameter completeness validator

`app/simulation/analyze_table_params.py::validate_table_parameters` chạy SAU
analyze, TRƯỚC classify/manifest. Báo cáo máy-đọc: `requested_stages`,
`grounded_stages`, `incomplete_stages`, `missing_parameters_by_stage`,
`invalid_parameters_by_stage`, `unknown_column_references`,
`analyze_parameter_decision` ∈ {not_applicable, complete, incomplete}.

**Trên EXACT live P2 payload (`4d9e8ac`, không hand-populate):** decision =
incomplete; grounded = [sort]; incomplete = [filter, projection, limit,
aggregate]; missing = {filter:[column,op,value], projection:[columns],
limit:[limit], aggregate:[aggregate_column]}. **Operation name một mình KHÔNG
đủ evidence.**

Luật §B: filter cần column+op+value (trừ null-operator); projection cần columns
≥1; sort cần column; limit cần int ≥1; aggregate cần func + column (trừ
COUNT(\*)). Ngoại lệ khai rõ: IS NULL/IS NOT NULL không cần value; COUNT(\*)
không cần column. `count_mode='star'` KÈM column = mâu thuẫn → invalid (không tự
đoán). Chỉ áp `relational_table_query`; family khác → not_applicable.

## 3. §E — Bounded analyze repair (đúng MỘT lượt)

`stage_repair_table_params`: gửi requested_requirements cũ + tham số thiếu ĐÍCH
DANH + tiêu đề cột đề cho + đề gốc, yêu cầu chỉ ĐIỀN field thiếu khi đề nêu rõ,
KHÔNG đoán, KHÔNG tính kết quả. Rồi `patch_requirements` (TẤT ĐỊNH, thuần): chỉ
điền field còn thiếu, **KHÔNG ghi đè field đã hợp lệ** (sort giữ nguyên), **KHÔNG
thêm stage mới** ngoài original, chỉ nhận field trong tập đóng `_PATCHABLE_FIELDS`
(repair không chèn kết quả). Bản patch chỉ được nhận nếu giảm số tầng thiếu.

Không dùng prose chung; không regenerate toàn bộ analyze. `_call_json(..., retries=0)`
→ đúng một HTTP repair, KHÔNG gộp vào simulate attempts.

## 4. §F — Post-repair

Repair đủ → RequiredTablePipeline đủ 5 tầng grounded → simulate + merge (PATCH2)
như cũ (raw simulate candidate KHÔNG cần tự nhớ đủ tầng). Vẫn thiếu → để nguyên;
manifest chỉ ground phần có, cổng completeness fail-closed dưới dòng từ chối —
KHÔNG simulate/executor/generic, KHÔNG bịa từ prose. Learner-facing refusal
KHÔNG đổi (message cũ giữ nguyên → không cần recapture visual).

## 5. §G/§H — Regression từ EXACT live symptom

- Bắt đầu từ **exact live P2 requested_requirements** (5 op, 4 tầng thiếu tham
  số) — **không hand-populate trước validator**.
- Validator phát hiện incomplete → repair điền đúng 4 stage param → manifest 5
  tầng → raw 3-stage simulate candidate merge thành 5 → validator/completeness
  PASS → An/Dũng/Lan · AVG **8.5** · counted **3** · result-leakage 0.
- §H matrix: positive 1-10 (gồm IS NOT NULL không cần value, COUNT(\*) không cần
  column, COUNT(column) cần column, analyze đủ ngay attempt đầu không repair);
  negative 1-10 (không đoán limit/aggregate column, filter thiếu value, limit
  0/âm/thập phân invalid, count(\*)→count(column) không tự đổi, repair không chèn
  kết quả/không đổi rows-schema, family khác không phát sinh repair).

## 6. §I — Metrics (báo riêng, không gộp vào simulate attempts)

Observer (passive #22) phát `analyze_param_check` (decision + incomplete stages +
missing params) và `analyze_param_repair` (attempted/succeeded + incomplete
before/after + repaired_requirements). Runner ghi
`valid_analyze_parameters_first_attempt`, `analyze_repair_attempted/succeeded`,
`incomplete_stages_before/after_repair` (đã sẵn cho live). Final case có thể PASS
dù analyze attempt đầu thiếu param, nhưng phải báo
`valid_analyze_parameters_first_attempt = false`.

## 7. §J — Cache / history

`CACHE_VERSION` **21→22** (analyze prompt/schema `count_mode` + tham số tầng bắt
buộc + validator + repair — hợp đồng analyze đổi). `config_contract_version` GIỮ
`table-1.1`; `HISTORY_SCHEMA_VERSION` GIỮ 2 (shape envelope lưu không đổi). Repair
chỉ chạy khi có table requirements incomplete → selector/generic/pattern-reuse/
recovery bất biến (full suite chứng minh). Skill `analyze.md` đổi → phải restart
process/container (đã tính cho bước rebuild trước live).

## 8. §L — Offline acceptance (tất cả PASS)

pytest **1071** (2 skip, 1 deselect) · vitest **596/46** (FE + engine trace shape
KHÔNG đổi → không recapture visual) · build sạch · conformance 20/0 · descriptors
không trôi · exact live P2 payload phát hiện incomplete + repair + AVG 8.5/3 ·
L1/L2/L3/L5/L6 + P1 equivalence không regression · semantic-loss/fp-sim/generic-
leak/result-leakage = 0 · không xfail.

## 9. LIVE — chưa chạy (§M)

Runner `scripts/live_table_query_patch.py` đã có §I metrics + P2-first order.
**Chưa chạy live.** Trước live: commit, rebuild container kèm danh tính, runtime
doctor PASS ở HEAD mới (cache **22**). Wave 2B vẫn CHƯA CLOSE. Wave 2C KHÔNG mở.
