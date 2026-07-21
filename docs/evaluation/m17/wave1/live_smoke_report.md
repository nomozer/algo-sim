# M17-Lite Wave 1 — Targeted Live Smoke Report

> **Budget user duyệt:** ≤6 case / ≤20 HTTP · `gemini-2.5-flash` · production
> `run_pipeline` thật. **Đã dùng: 16/20 HTTP · 0 retry · 0 transient · 0
> reclassification.** Runner reproducible:
> `backend/scripts/live_smoke_m17_wave1.py` (ALLOW_LIVE_AI=1). Artifact máy-đọc:
> `live_smoke.json`. Không đụng frozen M16, không chỉnh expectation để pass.

## Kết quả: 5/6 PASS trên acceptance nghiêm ngặt

| # | Case | Prompt (cơ chế tự nhiên) | Kết quả | HTTP |
|---|---|---|---|---|
| 1 | selection_sort | "mỗi lượt chọn phần tử nhỏ nhất còn lại đưa về đầu" | ✅ `algorithm.selection_sort` (family comparison_sort) | 3 |
| 2 | base_conversion | "3A hệ 16 sang hệ 2, mô phỏng từng bước" | ✅ `binary.base_conversion` (positional_representation) | 3 |
| 3 | boolean_dag | "F = (A AND B) XOR (NOT C) + bảng chân trị" | ✅ `logic.boolean_dag` (boolean_composition) | 3 |
| 4 | graph_traversal DFS | "duyệt chiều sâu từ A, cạnh A-B/A-C/B-D/C-E" | ✅ `network.graph_traversal`, variant=dfs | 3 |
| 5 | near-miss quicksort | "Quick Sort, partition đệ quy" | ✅ unsupported · **capability_gap** · gate mechanism | 2 |
| 6 | base ngoài phạm vi | "243 hệ 5 sang hệ 10" | ⚠️ unsupported (an toàn) nhưng tag **plain** không `capability_gap` | 2 |

## Acceptance checklist (đối chiếu từng dòng user nêu)

| Tiêu chí | Kết quả |
|---|---|
| 4/4 supported đúng final family/capability | ✅ 4/4 |
| 4/4 có validated spec + deterministic executor đúng target | ✅ 4/4 (mỗi case simulate_attempts=1, envelope concrete) |
| DFS KHÔNG route về packet_routing | ✅ (route=graph_traversal, variant=dfs) |
| Boolean DAG KHÔNG hạ thành and_gate đơn | ✅ (route=logic.boolean_dag) |
| Selection Sort KHÔNG thành Bubble/Insertion | ✅ (route=algorithm.selection_sort) |
| Base conversion KHÔNG dùng đáp số LLM làm authoritative | ✅ (config chỉ {sourceBase,targetBase,inputValue,strategy}; đáp số do engine FE) |
| 2/2 unsupported trả **capability gap** trung thực | ⚠️ **1/2** — quicksort ✅ capability_gap; base-5 là unsupported an toàn nhưng tag plain (xem dưới) |
| generic leak = 0 | ✅ 0 |
| false-positive simulation = 0 | ✅ 0 |
| false refusal = 0 | ✅ 0 (base-5 ĐÁNG bị từ chối — không phải false refusal) |
| ghi retry/reclassification/transient/HTTP | ✅ 0 retry · 0 reclassify · 0 transient · 16 HTTP |
| không sửa frozen M16 | ✅ |
| không chỉnh expectation để pass | ✅ |

## Phân tích case #6 (base-5) — vì sao plain unsupported, không capability_gap

**Đường đi thực:** analyze → classify **từ chối thẳng** (initial_route=None, 2
HTTP, không gate nào bắn) → `status=unsupported`, `failure_category=None`.
LLM đọc classify.md rule 2d ("cơ số ngoài {2,8,10,16} → unsupported") và từ
chối ngay ở classify.

**Mọi thuộc tính AN TOÀN đều đạt:** unsupported ✔ · route=None (0 false-sim) ✔
· không generic leak ✔ · đúng phải từ chối (không false-refusal) ✔. Rẻ nhất
(2 HTTP), không 422, không đốt retry.

**Vì sao KHÔNG hit blocking condition user nêu:** blocking = {supported case
sai route, generic leak, executor ownership sai}. Base-5 là *unsupported*,
không leak, không ownership issue → KHÔNG blocking.

**Vì sao tag plain hợp lý về mặt kiến trúc:** `capability_gap` trong hệ là
phán quyết của GATE "không engine nào sở hữu CƠ CHẾ". Cơ chế của base-5 là
`non_binary_base` — mà `binary.base_conversion` **CÓ** sở hữu (cho hex/octal).
Không có mechanism-gap; "gap" nằm ở mức THAM SỐ (giá trị cơ số), là mối quan
tâm của classify/validation, không phải mechanism gate. Vì thế classify-refusal
→ plain unsupported (cùng idiom với TCP-advanced) là tag *chính xác hơn*
capability_gap cho trường hợp này.

**So với M16:** case M16 `m16-cr-positional-fail` (cũng base-5) từng ra
capability_gap vì thời điểm đó CHƯA có base_conversion → route generic →
route-mismatch. Nay base_conversion tồn tại nên classify từ chối sớm hơn, rẻ
hơn, tag khác (plain). Frozen M16 KHÔNG đổi — overlay đã ghi.

## Trạng thái close — QUYẾT ĐỊNH USER: chấp nhận + backlog

- **Blocking conditions user nêu: 0 hit.** 4/4 supported đúng trọn, 0 generic
  leak, 0 false-positive sim, 0 false refusal.
- **Lệch DUY NHẤT so acceptance chữ:** tag `capability_gap` trên 1/2 unsupported
  (base-5 ra plain unsupported an toàn).
- **User CHẤP NHẬN** base-5 plain unsupported là từ chối trung thực hợp lệ →
  **Wave 1 CLOSE (offline + live)**.
- **BACKLOG (NON-BLOCKING):** cân nhắc để base ngoài {2,8,10,16} → `capability_gap`
  (route base_conversion + validator phát gap thay vì classify-refusal / 422)
  ở wave sau — vd khi làm coverage dashboard Wave 3. KHÔNG làm trong Wave 1.
