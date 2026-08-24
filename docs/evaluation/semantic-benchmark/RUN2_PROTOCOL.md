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
- **Không thêm nghĩa vụ / checker để cứu case.** ⚠️ **Câu này đã BỊ LỆCH — đọc
  §7b trước khi trích.** Bản gốc chốt *"taxonomy giữ 9 nghĩa vụ `4dd712a3…`; đề
  cần `predicate_verdict` vẫn phải trượt"*. Hệ sẽ đo ở lượt #2 có **11 nghĩa vụ**
  (`b30e45da…`), gồm cả `predicate_verdict`. Sai lệch được khai đầy đủ ở §7b,
  ghi ngày 24/08 trước khi có seed. Luật gốc — *không thêm checker để cứu một
  case cụ thể* — vẫn còn hiệu lực nguyên vẹn cho lượt chạy.
- **Ba con số báo riêng**: `A` executability · `B` internal servable · oracle độc
  lập. `A − B` phải phân rã, không gộp thành `verification_gap`.
- **Kết quả thấp là DỮ LIỆU.** Chuỗi probe cho thấy máy dựng đúng nghĩa vụ và
  đúng cấu trúc nhưng **chưa lượt nào sinh ra chương trình làm đúng việc**. Vào
  lượt đo với kỳ vọng con số phải đẹp là tự đặt mình vào thế phải vá sau khi thấy
  số.

## 7b. SAI LỆCH SO VỚI TIỀN ĐĂNG KÝ — khai báo 2026-08-24, TRƯỚC khi có seed

> Ghi ở đây vì đó là cách duy nhất trung thực để xử lý một tiền đăng ký bị lệch:
> **khai ra, có ngày tháng, trước khi biết seed và trước khi thấy bất kỳ số nào**.
> Một sai lệch được khai trước khi đo là dữ liệu; phát hiện sau khi đo là vết
> bẩn không rửa được.

### Lệch cái gì

§2 tuyên bố đóng băng mã lúc `70867ce` (23/08 19:37). Sau mốc đó, `backend/app`
đã đổi ở **bốn** commit:

| commit | giờ | đụng gì |
|---|---|---|
| `12085d5` | 24/08 00:07 | **taxonomy 9 → 11 nghĩa vụ** + 2 lớp hình dạng wire |
| `0727275` | 24/08 00:15 | telemetry route ngữ nghĩa |
| `3e0d67c` | 24/08 00:49 | coverage-gate: witness phải DẪN XUẤT từ dữ liệu |
| `096270d` | 24/08 | bộ đếm coercion + token đầu ra (**quan trắc thuần**) |

Nghiêm trọng nhất là commit đầu, vì nó chạm đúng một câu đã tiền đăng ký ở §7:

> ~~"Taxonomy giữ **9 nghĩa vụ**, `4dd712a3…`. Đề cần `predicate_verdict` vẫn
> phải trượt."~~

`predicate_verdict` và `scalar_accumulation` nay **đã có trong taxonomy** (11
nghĩa vụ, `b30e45da…`). Câu §7 ở trên **không còn mô tả hệ sẽ được đo**.

### Lập luận BÊNH cho thay đổi

`12085d5` không thêm nghĩa vụ để cứu một case cụ thể. Nó xuất phát từ một phép
đo cơ học trên chính `OBLIGATION_KINDS`: **0/10 nghĩa vụ nhận được chủ thể VÔ
HƯỚNG** — toàn bộ taxonomy mang hình dạng container, trong khi *vòng lặp tích
luỹ trên một biến số* và *câu hỏi đúng/sai trên một số* là hai kiến trúc cơ bản
nhất của Tin học 10. Đó là một lỗ hổng **cấu trúc**, cùng loại với bốn biên
chuẩn hoá, không phải một lần vá theo ca.

Cả hai lớp mới đi qua **tập ĐÓNG** (`_PREDS` có sẵn · `op ∈ {sum,product}` ×
`TERM_TRANSFORMS`). Vị từ ngoài tập vẫn là `verification_gap`. Đóng là điều kiện
của tính độc lập: mở cho biểu thức bất kỳ thì checker phải đánh giá biểu thức
của chương trình, tức chạy lại chính nó.

### Lập luận CHỐNG — phải đọc kèm, không được bỏ

Dù lập luận trên đúng, **nó được nghĩ ra sau khi đã thấy kết quả lượt #1**. Đúng
5 case của lượt #1 chết vì thiếu chủ thể vô hướng. Một người ngoài có quyền hỏi:
*nếu lượt #1 không phơi ra 5 case ấy, phép đo cơ học kia có được chạy không?*
Không ai trả lời trung thực được câu đó, kể cả người viết mã.

Đó chính là rủi ro mà §7 được viết ra để chặn, và nó đã không chặn được.

### Hệ quả cho việc trình bày

1. §7 câu "giữ 9 nghĩa vụ / `4dd712a3…`" **bị thay** bởi mục này. Hằng số đúng
   của lượt #2 là **11 nghĩa vụ, `b30e45da…`**, đóng băng ở `EVALUATION_CANDIDATE.json`
   (`b407af0`, cây sạch).
2. Luận văn **phải nêu sai lệch này khi báo số lượt #2**, không được trình bày
   lượt #2 như một phép đo tiền đăng ký sạch. Câu đúng: *"lượt #2 đo trên bài
   chưa từng thấy, nhưng taxonomy đã mở thêm hai lớp sau khi thấy kết quả lượt
   #1; mức độ held-out của TẬP ĐỀ là nguyên vẹn, còn mức độ tiền-đăng-ký của
   TAXONOMY thì không."*
3. Quyết định nhận hay hoàn taxonomy về 9 thuộc **GVHD**, và phải chốt **trước
   khi cấp seed**. Hoàn về 9 thì lượt #2 sạch tiền đăng ký nhưng bỏ đi một bản
   vá cấu trúc có thật; giữ 11 thì phải mang theo lời khai này.
4. `096270d` là **quan trắc thuần** — không đụng prompt · schema · taxonomy ·
   primitive · route · checker; bốn hash ngữ nghĩa không đổi. Nó không tạo thêm
   sai lệch nào, chỉ làm `measured_system.tree_hash` trôi nên phải đóng băng lại.

### Kỷ luật từ đây

Đóng băng mã ở §2 **có hiệu lực trở lại** kể từ `b407af0`. Cổng kiểm:
`freeze_evaluation_candidate.py --verify`. Lần này nếu còn commit nào chạm
`backend/app` trước lượt chạy, nó phải được khai vào chính mục này.

## 8. Điều protocol này KHÔNG hứa

Không hứa `A` sẽ cao hơn. Nó chỉ bảo đảm rằng **nếu** cao hơn thì con số ấy có
nghĩa: đo trên bài chưa từng thấy, ngân sách chốt trước, hệ không đổi giữa chừng.
`LEARNER_IMPACT_NOT_EVALUATED` và `CURRICULUM_SUPPORT_PARTIAL` giữ nguyên — lượt
này không đo gì về người học.
