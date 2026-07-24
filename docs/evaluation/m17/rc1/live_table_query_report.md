# M17 W2B-LIVE — Grounding Verification `database.relational_table_query`

Kiểm chứng production LLM orchestration THẬT có grounding trung thực — không phải routing smoke.

- Model **gemini-2.5-flash** · env **local_python** · SHA `88618ac865a8` · cache **19** · family **10** · target **20** · hash `48b6d50e3da7`
- Case **3/6** đạt · supported **2/4** · negative **1/2**
- HTTP **18** · retry **0** · transient **0** · reclassification **0**
- routing **0.8333** · grounding **0.75** · generic-leak **0** · false-positive-sim **0** · false-refusal **0** · result-leakage **0**
- STOP: **không** · all_passed: **False**

| Case | Loại | HTTP | route | grounding | leak | final | đạt |
|---|---|---|---|---|---|---|---|
| L1 | supported | 3 | `database.relational_table_query` | perfect | — | khớp | ✔ |
| L2 | supported | 3 | `database.relational_table_query` | perfect | — | khớp | ✔ |
| L3 | supported | 5 | `None` | LỖI | — | LỆCH | ✘ |
| L4 | supported | 3 | `database.relational_table_query` | perfect | — | LỆCH | ✘ |
| L5 | refusal | 2 | unsupported/semantic_incomplete | — | — | — | ✘ |
| L6 | refusal | 2 | unsupported/semantic_incomplete | — | — | — | ✔ |

## Chi tiết từng case

### L1 — ĐẠT
- prompt: `Giữ các học sinh có điểm từ 8 trở lên và chỉ hiển thị Tên, Điểm.`
- route: initial=`database.relational_table_query` → final=`database.relational_table_query` · reclassify=0 · simulate_attempts=1
- analyze: result_ownership='algorithmic' · prescribed=None
- grounding: rows 6→6 · cols 3→3 · cells 18 · modified=0 · empty→0=0 · added/dropped rows=0/0 · type_mismatch=0
- operations: {'filter': True, 'projection': ['Tên', 'Điểm'], 'sort': None, 'limit': None, 'aggregate': None}  (mong {'filter': True, 'projection': ['Tên', 'Điểm'], 'sort': None, 'limit': None, 'aggregate': None})
- executor: expected_final={'rows': [{'Tên': 'Bình', 'Điểm': 8.0}, {'Tên': 'Chi', 'Điểm': 9.25}, {'Tên': 'Hà', 'Điểm': 8.5}, {'Tên': 'Lan', 'Điểm': 9.0}], 'aggregate': None} · actual_final={'rows': [{'Tên': 'Bình', 'Điểm': 8.0}, {'Tên': 'Chi', 'Điểm': 9.25}, {'Tên': 'Hà', 'Điểm': 8.5}, {'Tên': 'Lan', 'Điểm': 9.0}], 'aggregate': None} · oracle_agreement=True · leakage=[]

### L2 — ĐẠT
- prompt: `Sắp xếp giảm dần theo Điểm.`
- route: initial=`database.relational_table_query` → final=`database.relational_table_query` · reclassify=0 · simulate_attempts=1
- analyze: result_ownership='algorithmic' · prescribed=None
- grounding: rows 6→6 · cols 3→3 · cells 18 · modified=0 · empty→0=0 · added/dropped rows=0/0 · type_mismatch=0
- operations: {'filter': False, 'projection': None, 'sort': ('Điểm', 'desc'), 'limit': None, 'aggregate': None}  (mong {'filter': None, 'projection': None, 'sort': ('Điểm', 'desc'), 'limit': None, 'aggregate': None})
- executor: expected_final={'rows': [{'STT': 2, 'Tên': 'Bình', 'Điểm': 9.0}, {'STT': 5, 'Tên': 'Hà', 'Điểm': 9.0}, {'STT': 1, 'Tên': 'An', 'Điểm': 8.5}, {'STT': 3, 'Tên': 'Chi', 'Điểm': 8.5}, {'STT': 6, 'Tên': 'Lan', 'Điểm': 8.5}, {'STT': 4, 'Tên': 'Dũng', 'Điểm': 7.0}], 'aggregate': None} · actual_final={'rows': [{'STT': 2, 'Tên': 'Bình', 'Điểm': 9.0}, {'STT': 5, 'Tên': 'Hà', 'Điểm': 9.0}, {'STT': 1, 'Tên': 'An', 'Điểm': 8.5}, {'STT': 3, 'Tên': 'Chi', 'Điểm': 8.5}, {'STT': 6, 'Tên': 'Lan', 'Điểm': 8.5}, {'STT': 4, 'Tên': 'Dũng', 'Điểm': 7.0}], 'aggregate': None} · oracle_agreement=True · leakage=[]

### L3 — KHÔNG ĐẠT
- prompt: `Tính điểm trung bình của các ô có dữ liệu.`
- route: initial=`database.relational_table_query` → final=`None` · reclassify=0 · simulate_attempts=3
- analyze: result_ownership='algorithmic' · prescribed=None
- grounding: rows None→None · cols None→None · cells None · modified=0 · empty→0=0 · added/dropped rows=None/None · type_mismatch=0
- operations: None  (mong {'filter': None, 'projection': None, 'sort': None, 'limit': None, 'aggregate': ('avg', 'Điểm kiểm tra')})
- executor: expected_final={'rows': [{'Học sinh': 'An', 'Điểm kiểm tra': 8}, {'Học sinh': 'Bình', 'Điểm kiểm tra': None}, {'Học sinh': 'Chi', 'Điểm kiểm tra': 9.5}, {'Học sinh': 'Dũng', 'Điểm kiểm tra': 7}, {'Học sinh': 'Hà', 'Điểm kiểm tra': None}, {'Học sinh': 'Lan', 'Điểm kiểm tra': 8.5}], 'aggregate': {'value': 8.25, 'counted': 4}} · actual_final=None · oracle_agreement=None · leakage=[]
- **VẤN ĐỀ:** ['status=error (mong ok)', 'route=None', 'không có config hợp lệ để audit']

### L4 — KHÔNG ĐẠT
- prompt: `Trong tổ A, chỉ hiển thị Tên và Điểm, sắp xếp Điểm giảm dần, lấy 3 học sinh đầu, rồi tính điểm trung bình của 3 học sinh đó.`
- route: initial=`database.relational_table_query` → final=`database.relational_table_query` · reclassify=0 · simulate_attempts=1
- analyze: result_ownership='algorithmic' · prescribed=None
- grounding: rows 8→8 · cols 4→4 · cells 32 · modified=0 · empty→0=0 · added/dropped rows=0/0 · type_mismatch=0
- operations: {'filter': True, 'projection': ['Tên', 'Điểm'], 'sort': ('Điểm', 'desc'), 'limit': None, 'aggregate': None}  (mong {'filter': True, 'projection': ['Tên', 'Điểm'], 'sort': ('Điểm', 'desc'), 'limit': 3, 'aggregate': ('avg', 'Điểm')})
- executor: expected_final={'rows': [{'Tên': 'An', 'Điểm': 9.0}, {'Tên': 'Dũng', 'Điểm': 9.0}, {'Tên': 'Lan', 'Điểm': 7.5}], 'aggregate': {'value': 8.5, 'counted': 3}} · actual_final={'rows': [{'Tên': 'An', 'Điểm': 9.0}, {'Tên': 'Dũng', 'Điểm': 9.0}, {'Tên': 'Lan', 'Điểm': 7.5}, {'Tên': 'Chi', 'Điểm': 6.0}, {'Tên': 'Minh', 'Điểm': 6.0}], 'aggregate': None} · oracle_agreement=True · leakage=[]
- **VẤN ĐỀ:** ['engine final ≠ expected (operation/spec sai)']

### L5 — KHÔNG ĐẠT
- prompt: `Lọc các học sinh có điểm từ 8 trở lên và sắp xếp giảm dần.`
- route: initial=`database.relational_table_query` → final=`None` · reclassify=0 · simulate_attempts=0
- analyze: result_ownership='algorithmic' · prescribed=None
- learner_reason: 'Đề đang hỏi 2 truy vấn độc lập, nhưng mỗi lần mô phỏng chỉ trình bày được MỘT. Em hãy tách thành từng lần hỏi (giữ nguyên bảng, mỗi lần một yêu cầu) để xem đầy đủ từng bước.'
- **VẤN ĐỀ:** ['failure_category=semantic_incomplete (mong insufficient_specification)']

### L6 — ĐẠT
- prompt: `Đếm số học sinh tổ A và đếm số học sinh tổ B.`
- route: initial=`database.relational_table_query` → final=`None` · reclassify=0 · simulate_attempts=0
- analyze: result_ownership='rule_derivable' · prescribed=None
- learner_reason: 'Đề đang hỏi 2 truy vấn độc lập, nhưng mỗi lần mô phỏng chỉ trình bày được MỘT. Em hãy tách thành từng lần hỏi (giữ nguyên bảng, mỗi lần một yêu cầu) để xem đầy đủ từng bước.'

