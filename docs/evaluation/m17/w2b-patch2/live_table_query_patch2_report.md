# M17 W2B-PATCH2 LIVE — kiểm chứng lại 3 finding đã vá

- Model **gemini-2.5-flash** · env **local_python** · SHA `9f717df8aca8` · cache **21** · family **10** · target **20** · hash `4f2a93ec2be3`
- Strict **0/1** · supported **0/1** · negative **0/0**
- HTTP **5**/14 · http-retry **0** · transient **0** · reclassify **0** · cache-hit **0**
- valid-RAW-candidate-first **0.0** · valid-MERGED-candidate-first **0.0** · deterministic-merge **0** · simulate attempts {'P2': 3}
- grounding **None** · empty→0 **0** · modified cells **0** · generic-leak **0** · fp-sim **0** · false-refusal **1** · result-leak **0** · semantic-loss **0**
- STOP: **P2: supported case status='unsupported' (mong 'ok')** · all_passed: **False**

> production run_pipeline (bất biến #22), pattern_store=None nên KHÔNG có đường cache/pattern-reuse: mỗi case đi FRESH analyze → classify → simulate. Danh tính container xác minh RIÊNG bằng runtime_doctor (runtime_identity_w2b_patch2.json) — PASS trước khi chạy live.

> `http_retry` = retry ở TẦNG HTTP (transient). `simulate_attempts` = lượt sinh spec của product semantics — HAI thứ KHÁC NHAU, báo riêng.

| Case | Finding | Loại | HTTP | sim | route | grounding | final | đạt |
|---|---|---|---|---|---|---|---|---|
| P2 | L4 | supported | 5 | 3 | `None` | LỖI | LỆCH | ✘ |

## Chi tiết từng case

### P2 (L4) — KHÔNG ĐẠT
- kỳ vọng: NĂM tầng; aggregate SAU limit. Tổ A 5 hs → sort desc [An9,Dũng9,Lan7.5,Chi6,Minh6] → limit3 → avg=8.5.
- prompt: `Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 học sinh đầu, rồi tính điểm trung bình của 3 học sinh đó.`
- route: initial=`database.relational_table_query` → final=`None` · reclassify=0 · simulate_attempts=3 · valid-raw-first=False · valid-merged-first=False · merge=0 · cache_hit=False
- analyze: result_ownership='algorithmic' · requested_operations=['relational_table_query:filter', 'relational_table_query:projection', 'relational_table_query:sort', 'relational_table_query:limit', 'relational_table_query:avg']
- **PHẢN HỒI GIỮA CÁC LƯỢT SIMULATE:**
  - lượt 0: ok=False · code=semantic_incomplete · Đề yêu cầu một QUY TRÌNH gồm các bước: filter, projection, sort, limit, aggregate (chạy đúng thứ tự filter → projection → sort → limit → aggregate). Spec vừa gửi THIẾU các trường: limit, aggregate. Hãy điền đủ, KHÔNG bỏ bước nào.
  - lượt 1: ok=False · code=semantic_incomplete · Đề yêu cầu một QUY TRÌNH gồm các bước: filter, projection, sort, limit, aggregate (chạy đúng thứ tự filter → projection → sort → limit → aggregate). Spec vừa gửi THIẾU các trường: limit, aggregate. Hãy điền đủ, KHÔNG bỏ bước nào.
  - lượt 2: ok=False · code=semantic_incomplete · Đề yêu cầu một QUY TRÌNH gồm các bước: filter, projection, sort, limit, aggregate (chạy đúng thứ tự filter → projection → sort → limit → aggregate). Spec vừa gửi THIẾU các trường: limit, aggregate. Hãy điền đủ, KHÔNG bỏ bước nào.
- grounding: rows None→None · cols None→None · cells None · modified=0 · empty→0=0 · type_mismatch=0 · order_preserved=None
- tầng: mong ['filter', 'projection', 'sort', 'limit', 'aggregate'] · dựng được None · thiếu []
- operations: None  (mong {'filter': True, 'projection': ['Tên', 'Điểm'], 'sort': ('Điểm', 'desc'), 'limit': 3, 'aggregate': ('avg', 'Điểm')})
- executor: expected_final={'rows': [{'Tên': 'An', 'Điểm': 9.0}, {'Tên': 'Dũng', 'Điểm': 9.0}, {'Tên': 'Lan', 'Điểm': 7.5}], 'aggregate': {'value': 8.5, 'counted': 3}} · actual_final=None · leakage=[]
- **VẤN ĐỀ:** ['status=unsupported (mong ok)', 'route=None', 'không có config hợp lệ để audit']

