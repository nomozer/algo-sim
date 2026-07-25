# M17 W2B-PATCH3 LIVE — kiểm chứng lại 3 finding đã vá

- Model **gemini-2.5-flash** · env **local_python** · SHA `0513740a2d74` · cache **22** · family **10** · target **20** · hash `4f2a93ec2be3`
- Strict **0/1** · supported **0/1** · negative **0/0**
- HTTP **3**/14 · http-retry **0** · transient **0** · reclassify **0** · cache-hit **0**
- valid-RAW-candidate-first **0.0** · valid-MERGED-candidate-first **1.0** · deterministic-merge **1** · simulate attempts {'P2': 1}
- grounding **0.0** · empty→0 **0** · modified cells **0** · generic-leak **0** · fp-sim **0** · false-refusal **0** · result-leak **0** · semantic-loss **0**
- STOP: **P2: schema mất/thêm cột** · all_passed: **False**

> production run_pipeline (bất biến #22), pattern_store=None nên KHÔNG có đường cache/pattern-reuse: mỗi case đi FRESH analyze → classify → simulate. Danh tính container xác minh RIÊNG bằng runtime_doctor (runtime_identity_w2b_patch3.json) — PASS trước khi chạy live.

> `http_retry` = retry ở TẦNG HTTP (transient). `simulate_attempts` = lượt sinh spec của product semantics — HAI thứ KHÁC NHAU, báo riêng.

| Case | Finding | Loại | HTTP | sim | route | grounding | final | đạt |
|---|---|---|---|---|---|---|---|---|
| P2 | L4 | supported | 3 | 1 | `database.relational_table_query` | LỖI | LỆCH | ✘ |

## Chi tiết từng case

### P2 (L4) — KHÔNG ĐẠT
- kỳ vọng: NĂM tầng; aggregate SAU limit. Tổ A 5 hs → sort desc [An9,Dũng9,Lan7.5,Chi6,Minh6] → limit3 → avg=8.5.
- prompt: `Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 học sinh đầu, rồi tính điểm trung bình của 3 học sinh đó.`
- route: initial=`database.relational_table_query` → final=`database.relational_table_query` · reclassify=0 · simulate_attempts=1 · valid-raw-first=False · valid-merged-first=True · merge=1 · cache_hit=False
- analyze: result_ownership='algorithmic' · requested_operations=['relational_table_query:filter', 'relational_table_query:projection', 'relational_table_query:sort', 'relational_table_query:limit', 'relational_table_query:avg']
- analyze-params: first-attempt-valid=True · incomplete_before=[] · missing={} · repair_attempted=False · repair_succeeded=False · incomplete_after=[]
- manifest: prompt=['filter', 'projection', 'sort', 'limit', 'aggregate'] · analyze=['filter', 'projection', 'sort', 'limit', 'aggregate'] · manifest=['filter', 'projection', 'sort', 'limit', 'aggregate'] · complete=True · raw=['filter', 'projection', 'sort'] → merged=['filter', 'projection', 'sort', 'limit', 'aggregate'] · inserted=['limit', 'aggregate'] · corrected=[] · fidelity=True
- grounding: rows 8→8 · cols 4→4 · cells 16 · modified=0 · empty→0=0 · type_mismatch=0 · order_preserved=True
- tầng: mong ['filter', 'projection', 'sort', 'limit', 'aggregate'] · dựng được ['filter', 'projection', 'sort', 'limit', 'aggregate'] · thiếu []
- operations: {'filter': True, 'projection': ['Tên học sinh', 'Điểm số'], 'sort': ('Điểm số', 'desc'), 'limit': 3, 'aggregate': ('avg', 'Điểm số')}  (mong {'filter': True, 'projection': ['Tên', 'Điểm'], 'sort': ('Điểm', 'desc'), 'limit': 3, 'aggregate': ('avg', 'Điểm')})
- executor: expected_final={'rows': [{'Tên': 'An', 'Điểm': 9.0}, {'Tên': 'Dũng', 'Điểm': 9.0}, {'Tên': 'Lan', 'Điểm': 7.5}], 'aggregate': {'value': 8.5, 'counted': 3}} · actual_final={'rows': [{'Tên học sinh': 'An', 'Điểm số': 9.0}, {'Tên học sinh': 'Dũng', 'Điểm số': 9.0}, {'Tên học sinh': 'Lan', 'Điểm số': 7.5}], 'aggregate': {'value': 8.5, 'counted': 3}} · leakage=[]
- **VẤN ĐỀ:** ['grounding không hoàn hảo', 'engine final ≠ expected (operation/spec sai)']

