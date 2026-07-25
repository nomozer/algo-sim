# M17 W2B-PATCH LIVE — kiểm chứng lại 3 finding đã vá

- Model **gemini-2.5-flash** · env **local_python** · SHA `8bd23249aa24` · cache **20** · family **10** · target **20** · hash `4f2a93ec2be3`
- Strict **1/3** · supported **0/2** · negative **1/1**
- HTTP **14**/14 · http-retry **0** · transient **0** · reclassify **0** · cache-hit **0**
- valid-spec-first-attempt **0.0** · simulate attempts {'P1': 3, 'P2': 3, 'P3': 0}
- grounding **1.0** · empty→0 **0** · modified cells **0** · generic-leak **0** · fp-sim **0** · false-refusal **1** · result-leak **0** · semantic-loss **0**
- STOP: **BUDGET: Đã chạm trần 14 API call — dừng để không đốt thêm quota.** · all_passed: **False**

> production run_pipeline (bất biến #22), pattern_store=None nên KHÔNG có đường cache/pattern-reuse: mỗi case đi FRESH analyze → classify → simulate. Danh tính container xác minh RIÊNG bằng runtime_doctor (runtime_identity_w2b_patch.json) — PASS trước khi chạy live.

> `http_retry` = retry ở TẦNG HTTP (transient). `simulate_attempts` = lượt sinh spec của product semantics — HAI thứ KHÁC NHAU, báo riêng.

| Case | Finding | Loại | HTTP | sim | route | grounding | final | đạt |
|---|---|---|---|---|---|---|---|---|
| P1 | L3 | supported | 5 | 3 | `database.relational_table_query` | perfect | LỆCH | ✘ |
| P2 | L4 | supported | 5 | 3 | `None` | LỖI | LỆCH | ✘ |
| P3 | L5 | refusal | 2 | 0 | unsupported/insufficient_specification | — | — | ✔ |

## Chi tiết từng case

### P1 (L3) — KHÔNG ĐẠT
- kỳ vọng: AVG bỏ 2 ô trống: sum=33, count=4, avg=8.25 (empty≠0).
- prompt: `Tính điểm trung bình của các ô có dữ liệu.`
- route: initial=`database.relational_table_query` → final=`database.relational_table_query` · reclassify=0 · simulate_attempts=3 · valid-spec-first=False · cache_hit=False
- analyze: result_ownership='rule_derivable' · requested_operations=None
- **PHẢN HỒI GIỮA CÁC LƯỢT SIMULATE:**
  - lượt 0: ok=False · code=structural_invalid · Điều kiện lọc không hợp lệ: giá trị so sánh của cột 'Điểm kiểm tra': "trống" không phải số.
  - lượt 1: ok=False · code=structural_invalid · Điều kiện lọc không hợp lệ: giá trị so sánh của cột 'Điểm kiểm tra': "" không phải số.
  - lượt 2: ok=True · code=None · 
- grounding: rows 6→6 · cols 2→2 · cells 12 · modified=0 · empty→0=0 · type_mismatch=0 · order_preserved=True
- tầng: mong ['aggregate'] · dựng được ['filter', 'aggregate'] · thiếu []
- operations: {'filter': True, 'projection': None, 'sort': None, 'limit': None, 'aggregate': ('avg', 'Điểm kiểm tra')}  (mong {'filter': None, 'projection': None, 'sort': None, 'limit': None, 'aggregate': ('avg', 'Điểm kiểm tra')})
- executor: expected_final={'rows': [{'Học sinh': 'An', 'Điểm kiểm tra': 8}, {'Học sinh': 'Bình', 'Điểm kiểm tra': None}, {'Học sinh': 'Chi', 'Điểm kiểm tra': 9.5}, {'Học sinh': 'Dũng', 'Điểm kiểm tra': 7}, {'Học sinh': 'Hà', 'Điểm kiểm tra': None}, {'Học sinh': 'Lan', 'Điểm kiểm tra': 8.5}], 'aggregate': {'value': 8.25, 'counted': 4}} · actual_final={'rows': [{'Học sinh': 'An', 'Điểm kiểm tra': 8}, {'Học sinh': 'Chi', 'Điểm kiểm tra': 9.5}, {'Học sinh': 'Dũng', 'Điểm kiểm tra': 7}, {'Học sinh': 'Lan', 'Điểm kiểm tra': 8.5}], 'aggregate': {'value': 8.25, 'counted': 4}} · leakage=[]
- **VẤN ĐỀ:** ['engine final ≠ expected (operation/spec sai)']

### P2 (L4) — KHÔNG ĐẠT
- kỳ vọng: NĂM tầng; aggregate SAU limit. Tổ A 5 hs → sort desc [An9,Dũng9,Lan7.5,Chi6,Minh6] → limit3 → avg=8.5.
- prompt: `Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 học sinh đầu, rồi tính điểm trung bình của 3 học sinh đó.`
- route: initial=`database.relational_table_query` → final=`None` · reclassify=0 · simulate_attempts=3 · valid-spec-first=False · cache_hit=False
- analyze: result_ownership='algorithmic' · requested_operations=None
- **PHẢN HỒI GIỮA CÁC LƯỢT SIMULATE:**
  - lượt 0: ok=False · code=semantic_incomplete · Đề yêu cầu một QUY TRÌNH gồm các bước: filter, projection, sort, limit, aggregate (chạy đúng thứ tự filter → projection → sort → limit → aggregate). Spec vừa gửi THIẾU các trường: limit, aggregate. Hãy điền đủ, KHÔNG bỏ bước nào.
  - lượt 1: ok=False · code=semantic_incomplete · Đề yêu cầu một QUY TRÌNH gồm các bước: filter, projection, sort, limit, aggregate (chạy đúng thứ tự filter → projection → sort → limit → aggregate). Spec vừa gửi THIẾU các trường: limit, aggregate. Hãy điền đủ, KHÔNG bỏ bước nào.
  - lượt 2: ok=False · code=semantic_incomplete · Đề yêu cầu một QUY TRÌNH gồm các bước: filter, projection, sort, limit, aggregate (chạy đúng thứ tự filter → projection → sort → limit → aggregate). Spec vừa gửi THIẾU các trường: limit, aggregate. Hãy điền đủ, KHÔNG bỏ bước nào.
- grounding: rows None→None · cols None→None · cells None · modified=0 · empty→0=0 · type_mismatch=0 · order_preserved=None
- tầng: mong ['filter', 'projection', 'sort', 'limit', 'aggregate'] · dựng được None · thiếu []
- operations: None  (mong {'filter': True, 'projection': ['Tên', 'Điểm'], 'sort': ('Điểm', 'desc'), 'limit': 3, 'aggregate': ('avg', 'Điểm')})
- executor: expected_final={'rows': [{'Tên': 'An', 'Điểm': 9.0}, {'Tên': 'Dũng', 'Điểm': 9.0}, {'Tên': 'Lan', 'Điểm': 7.5}], 'aggregate': {'value': 8.5, 'counted': 3}} · actual_final=None · leakage=[]
- **VẤN ĐỀ:** ['status=unsupported (mong ok)', 'route=None', 'không có config hợp lệ để audit']

### P3 (L5) — ĐẠT
- kỳ vọng: KHÔNG có bảng → đòi bảng, KHÔNG xui tách truy vấn.
- prompt: `Lọc các học sinh có điểm từ 8 trở lên và sắp xếp giảm dần.`
- route: initial=`database.relational_table_query` → final=`None` · reclassify=0 · simulate_attempts=0 · valid-spec-first=False · cache_hit=False
- analyze: result_ownership='algorithmic' · requested_operations=None
- failure_category=`insufficient_specification` · error_code=`input_insufficient` · simulation_created=False
- input_sufficiency: {'target_id': 'database.relational_table_query', 'required_grounded_inputs': ['table_schema_and_rows'], 'missing_inputs': ['table_schema_and_rows'], 'satisfied_inputs': [], 'generated_defaults_allowed': False}
- learner_reason: 'Đề chưa cho bảng dữ liệu cụ thể (tên các cột và các dòng dữ liệu). Em hãy chép rõ bảng vào đề — ví dụ: cột Tên, Điểm, Tổ; rồi từng dòng An 8.5 A, Bình 6.0 B… — hệ không tự tạo bảng thay em.'

