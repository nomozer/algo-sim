# PROTOCOL LƯỢT ĐO CHÍNH THỨC #2 — chốt TRƯỚC khi có seed

> Mọi thứ trong tài liệu này được quyết định **trước khi tập SEALED #2 tồn tại**
> và **trước khi biết seed #2**. Đó là điều kiện để nó còn là một phép đo chứ
> không phải một lần chỉnh tham số sau khi đã thấy kết quả.
>
> Số của lượt #1 (`results/OFFICIAL_RESULT.md`, candidate `4e13e2b`: A 3/40 ·
> B 1/40) **đã đóng và không đổi**. Lượt #2 không thay thế nó — nó đo một hệ
> KHÁC trên một tập KHÁC, và luận văn phải trình bày cả hai.

## 1. Vì sao đo lại

Sau lượt #1, mã sản phẩm đổi ở những chỗ mà chính lượt #1 chỉ ra:

| Đổi | Bằng chứng thúc đẩy |
|---|---|
| `spec_version` nhận cả `1.0` và `"1.0"` | **17/40** case chết vì đúng lỗi này |
| `container` nhận `{"kind":"var"}`, từ chối CÓ DẠY | lớp lỗi lớn thứ hai |
| `condition` gấp `x` ⇒ `x == true` | probe E2E |
| `MAX_NESTING_DEPTH` 4 → 6 | IR không có `elif`, bài ngăn xếp cần 5 tầng |
| `stage_semantic_program` ≤3 lượt, gửi lỗi ngược | tám lớp lỗi hình dạng liên tiếp |
| C₂ `derived_sequence` chặn nghĩa vụ vô hiệu | một mô phỏng RỖNG đã được phát đi |

`A = 3/40` vì thế **không còn mô tả hệ hiện tại**. Đo lại là cách duy nhất hợp
lệ để biết con số thật — vá rồi chạy lại trên tập cũ thì con dấu mất hiệu lực.

## 2. ĐÓNG BĂNG MÃ — hiệu lực từ bây giờ

Không sửa `backend/app`, prompt (`app/ai/skills/*.md`), schema, taxonomy,
primitive, route, checker cho tới khi lượt #2 chạy xong.

⚠️ **Áp cho MỌI phiên đang làm việc trên kho này**, không riêng một phiên. Trong
ngày 2026-08-23 đã có hai phiên cùng sửa `semantic_program/`, và mỗi lần sửa là
một lần `measured_system.tree_hash` trôi — đóng băng candidate 6 lần trong một
ngày. Còn trôi thì số đo được không gắn với bản nào cả.

Được phép (harness, **không** thuộc `MEASURED_SYSTEM_PATHS`): `backend/scripts/`,
`backend/tests/`, `docs/`.

Cổng kiểm: `python backend/scripts/freeze_evaluation_candidate.py --verify`.

## 3. NGÂN SÁCH — dẫn lại từ call graph, chốt cứng

```
stage_analyze            _call_json(retries=1)                   → tối đa 2
stage_classify lần 1     _call_json(retries=1)                   → tối đa 2
one-route recovery       thêm một stage_classify                 → tối đa 2
stage_semantic_analyze   không retry                             → 1
stage_semantic_program   range(MAX_SEMANTIC_PROGRAM_ATTEMPTS)    → tối đa 3   ← ĐỔI
stage_simulate           for _attempt in range(3)                → tối đa 3
                                                                   ─────────
                                                                   tối đa 13
```

```
N (SEALED #2)     = 40
Trần lượt logic   = 520    (= 13 × 40, CƯỠNG CHẾ)
Trần lần thử HTTP = 620    (~19% headroom, chỉ để chịu transient 429/5xx)
```

**11 → 13 là hệ quả SỐ HỌC của một thay đổi call graph, không phải nới trần vì
số xấu.** Lượt #1 chạy dưới trần của chính nó (205/440 logic · 207/520 HTTP), nên
không có động cơ nào để nới. Khoá bởi `test_sealed_runner.py`, trong đó có một
test **dẫn** bound từ `MAX_SEMANTIC_PROGRAM_ATTEMPTS` thay vì chép tay — đổi hằng
số mà quên ngân sách thì đỏ trước, không phải đứt giữa lượt đo.

Vượt trần ⇒ `BUDGET_EXHAUSTED`, `evaluation_complete = false`, **không chạy bù**.

## 4. TẬP SEALED #2 — phải loại 40 bài đã đo

40 ID của lượt #1 **đã lộ ra cho người sửa mã**: chính chúng dẫn dắt các bản vá ở
§1. Rút lại chúng thì con số nói về *"hệ đã được vá theo đúng những bài này"*,
không nói về năng lực.

```
pool đủ tư cách        89
đã đo ở lượt #1      − 40
                     ─────
còn chưa từng đo       49      ← không gian mẫu của lượt #2
```

Cơ chế: `select_by_seed.py --exclude-measured`, đọc `MEASURED_RUN1_IDS.json`
(fingerprint `e2ebcf79…`, kiểm trước khi dùng). Payload ghi
`excluded_measured_count`, `excluded_fingerprint`, `effective_pool_size` — phép
chọn vẫn tái lập và kiểm được.

**Đã chạy thử** bằng seed giả `DRYRUN`: chọn 40/49, **giao với tập đã đo = 0**.

⚠️ **49 cho N=40 là rất sát.** Không còn chỗ loại thêm case nào vì lý do kỹ
thuật. Nếu custodian loại bất kỳ bài nào lúc dựng ground truth thì phải hoặc hạ
`N`, hoặc mở rộng SOURCE UNIVERSE — **quyết trước khi chọn**, không phải sau.

## 5. Việc CHỈ GVHD làm được

Cấp **seed #2**. Tính độc lập của phép chọn nằm ở chỗ seed không đến từ người
viết mã và không được chọn sau khi đã thấy kết quả. Seed #1 là `23082026` do GVHD
cấp; lượt #2 cần một seed mới theo cùng cách.

## 6. Trình tự chạy, sau khi có seed

```bash
# 1. cổng đóng băng — phải xanh trước khi làm gì tiếp
python backend/scripts/freeze_evaluation_candidate.py --verify

# 2. chọn 40 ID từ 49 bài chưa đo (custodian chạy, KHÔNG phải người viết mã)
cd docs/evaluation/semantic-benchmark/custodian
python select_by_seed.py --seed <SEED_GVHD> --exclude-measured --write

# 3. custodian dựng SEALED #2 + ground truth độc lập
python sealed_ground_truth.py        # Python thuần, không import mã sản phẩm

# 4. chạy MỘT LẦN
cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
  .venv/Scripts/python.exe scripts/run_sealed_evaluation.py
```

## 7. Luật của lượt chạy

- **Chạy đúng một lần.** Không vá giữa chừng, không chạy lại, không chọn lượt
  đẹp hơn. Case hỏng ghi đúng như nó hỏng.
- **Không thêm nghĩa vụ / checker để cứu case.** Taxonomy giữ 9 nghĩa vụ,
  `4dd712a3…`. Đề cần `predicate_verdict` vẫn phải trượt — kiểm nó đòi cài lại
  chính thuật toán đang kiểm.
- **Ba con số báo riêng**: `A` executability · `B` internal servable · oracle độc
  lập. `A − B` phải phân rã, không gộp thành `verification_gap`.
- **Kết quả thấp là DỮ LIỆU.** Chuỗi probe cho thấy máy dựng đúng nghĩa vụ và
  đúng cấu trúc nhưng **chưa lượt nào sinh ra chương trình làm đúng việc**. Vào
  lượt đo với kỳ vọng con số phải đẹp là tự đặt mình vào thế phải vá sau khi thấy
  số.

## 8. Điều protocol này KHÔNG hứa

Không hứa `A` sẽ cao hơn. Nó chỉ bảo đảm rằng **nếu** cao hơn thì con số ấy có
nghĩa: đo trên bài chưa từng thấy, ngân sách chốt trước, hệ không đổi giữa chừng.
`LEARNER_IMPACT_NOT_EVALUATED` và `CURRICULUM_SUPPORT_PARTIAL` giữ nguyên — lượt
này không đo gì về người học.
