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

### Lệch lần thứ hai — `MAX_NESTING_DEPTH` 6 → 8 (2026-08-24, sau preflight)

Khai ngay, cùng lý do như trên: seed #2 vẫn chưa tồn tại.

**Bối cảnh**: người dùng chạy sản phẩm thật (`SEMANTIC_ROUTE_MODE=serve`) với đề
*"Kiểm tra đóng mở ngoặc hợp lệ bằng Stack"* và nhận `unsupported`. Telemetry
`6b1ee593` cho thấy chuỗi: nghĩa vụ nhận đúng `predicate_verdict` → sinh IR chết
ở **"Độ sâu lồng lệnh (7) vượt quá giới hạn tối đa (6)"** → vòng sửa chạy (lần
đầu quan sát được trong sản phẩm) → chương trình lượt 2 hợp lệ nhưng **rỗng
ruột** (2 bước, `final_memory` toàn `null`, chỉ gán `hop_le=true`) → **C₂ bắt
được và từ chối phát**.

**Vì sao đây KHÔNG phải vá theo ca đã lộ**: (a) đề này là **fixture DEV
`P01_STACK_BRACKET`**, không phải ca SEALED — `freeze_protocol §7.3` cho phép mở
từ DEV; (b) trần chặn theo **hình dạng cú pháp**, mà hình dạng bị thổi lên bởi
một thiếu sót đã biết của IR (**không có `elif`**, mỗi nhánh else-if ăn một
tầng), không phải bởi độ phức tạp thật của bài. Mọi bài có dây "ngược lại,
nếu…" từ ba nhánh trở lên đều chạm cùng bức tường — đó là một LỚP.

**Vì sao 8 chứ không 7**: 7 vừa đúng cái quan sát được, và đặt trần bằng đúng
quan sát cuối cùng chính là cách bản 4 → 6 đã sai một lần rồi.

**Đây là vá HÌNH DẠNG, không phải vá ngữ nghĩa.** Cách sửa thật là cho IR một
`elif`; việc đó đổi schema nên chờ sau lượt #2.

**Kết quả sau khi vá**: rào độ sâu hết, lượt chạy đi xa hơn rồi chết ở **cổng
grounding** — `mo_ngoac_set/dong_ngoac_set: có initial_value nhưng thiếu
source_fact_id`. **KHÔNG vá tiếp**, và đây là quyết định có chủ đích:

- Đó là căng thẳng thiết kế thật, không phải bug: cổng chặn mọi `initial_value`
  không phải hạt khởi tạo để LLM không tuồn dữ liệu đề vào; nhưng bảng cặp
  ngoặc là **hằng số thuật toán**, không có fact nào để ghim. Sửa đúng cách đòi
  thêm cờ "hằng, không phải dữ liệu đề" vào schema ⇒ đổi thẻ văn phạm ⇒ bump
  `CACHE_VERSION` ⇒ **mở IR**, thứ §1.1 ranh giới 2 hoãn có chủ đích.
- Và cùng đề ấy, hai lượt liên tiếp `analyze` trả `bounded_control_flow.
  bounded_loop` rồi `none`. Đuổi theo từng lượt đơn lẻ là **đo nhiễu**
  (`RULES §3c`: DEEP_HARDENING).

Ghi lại làm **phát hiện chờ xử lý sau lượt #2**, không phải việc đang làm dở.

### Lệch lần thứ ba — `MODEL` đọc từ `GEMINI_MODEL` (2026-08-24)

**Mặc định KHÔNG đổi**: vẫn `gemini-2.5-flash`, đúng model của lượt #1. Đây là
thay đổi *cơ chế cấu hình*, không phải thay đổi *hệ*. Khai vì nó chạm
`backend/app` nên `measured_system.tree_hash` trôi, và vì model là **một phần
danh tính của hệ được đo** (`model_target` trong seal manifest).

**Vì sao cần**: `MODEL` đang hardcode, nên mỗi lần thử một model là một lần sửa
mã ⇒ một lần đóng băng lại candidate. Đúng cái vòng đã đóng băng candidate **sáu
lần trong một ngày** (2026-08-23). Đưa ra env thì A/B không còn làm trôi cây mã.

**Model khả dụng với key hiện tại** (`ListModels`, 2026-08-24): `gemini-3.7-flash`
· `3.6-flash` · `3.5-flash` · `3.1-pro-preview` · `3.1-flash-lite` · `3-flash-preview`.
`gemini-2.5-flash` nay **lạc hậu hai thế hệ**.

**Khoá bằng `tests/test_gemini_model_config.py`**: mặc định phải bằng model lượt
#1 (đổi ngầm là ĐỎ, kèm lời nhắc khai vào chính mục này) · env phải THẬT SỰ có
tác dụng (không thì một lượt A/B chạy hai lần cùng model mà không ai biết) · tên
model chỉ được xuất hiện MỘT lần trong mã · runner phải ghi `model` vào artifact.

**Runner nay ghi `model` thật vào báo cáo** — trước đây suy từ mặc định, mà mặc
định không còn là sự thật.

> ⚠️ **Model KHÔNG giải thích được `A = 3/40`.** Chẩn đoán lượt #1: LLM sai
> thuật toán thật chỉ **3/40**, còn 30/40 chết vì hợp đồng đòi cách viết khác.
> Nói *"tại model cũ"* là báo cáo sai nguyên nhân. Model là đòn bẩy **bổ sung**,
> đo được bằng A/B trên DEV, không phải lời giải thích cho số cũ.

### Lệch lần thứ tư — interpreter FAIL-CLOSED (2026-08-24)

Khai ngay: seed #2 vẫn chưa tồn tại.

**Audit tìm thấy**: `semantic_program/interpreter.py` im lặng cho qua MỌI vi
phạm biên — `pop`/`dequeue` trên rỗng là **no-op không ghi bước**, `peek` trên
rỗng trả `None`, chỉ số ngoài biên trả `None`, `length` trên tên sai trả `0`.

**Vì sao là lỗi SOUNDNESS, không phải thiếu năng lực**: một chương trình sai
sinh ra trace **trông hợp lý**. Học sinh xem một mô phỏng có bước biến mất mà
không ai nói cho biết là đang thiếu — cùng họ với lỗi đã sinh ra bất biến #31.

**Có tiền lệ ĐÚNG ngay trong kho**: M13-SOUNDNESS đã sửa chính lớp lỗi này cho
`generic_engine` (*"numeric silent-zero… KHÔNG còn seed/fallback 0"* →
`GenericEvaluationError`, 4 mã, fail-closed). `interpreter.py` là **chủ sở hữu
thứ hai** và đã tái tạo lại nó cho container. Bản vá này đưa nó về cùng khuôn:
`SemanticExecutionError` + 4 mã (`EMPTY_CONTAINER` · `INDEX_OUT_OF_RANGE` ·
`UNDECLARED_CONTAINER` · `CONTAINER_TYPE_MISMATCH`).

**KHÔNG mở phạm vi**: không domain mới, không primitive mới, taxonomy KHÔNG đổi.
Route đã sẵn dịch mọi `Exception` của interpreter thành `servable=False` nên
không phải sửa. `map_get` có `default` **tường minh** vẫn hợp lệ — chỉ khoá chỗ
hệ **âm thầm** bịa giá trị.

**Bằng chứng RED→GREEN**: 11 fault test viết TRƯỚC, tất cả ĐỎ (`ImportError`,
rồi 6 ca không ném lỗi), sau bản vá **11/11 GREEN**. Và **không một test cũ nào
vỡ** (2071 passed) — các nhánh im lặng ấy chết thật, không đang gánh việc.

**Ảnh hưởng tới lượt #2**: có thể **hạ** `A`. Chương trình từng "chạy xong" nhờ
nuốt lỗi biên nay sẽ `executable=false`. Đó là **đúng**: `A` cũ đếm cả những lượt
chạy trên hư không. Phải nêu điều này khi so #1 với #2.

### Kèm theo — `replay_harness.py` (harness, không lệch)

`backend/scripts/` nên không chạm hệ được đo. Chạy một chương trình trên nhiều
đầu vào, phát hiện `INPUT_IGNORED` · `DEAD_STATE` · `HARD_CODED?` mà **không cần
oracle**. Phủ đúng chỗ kiểm tĩnh C₁b không với tới.

### Kỷ luật từ đây

Đóng băng mã ở §2 **có hiệu lực trở lại** kể từ `b407af0`. Cổng kiểm:
`freeze_evaluation_candidate.py --verify`. Lần này nếu còn commit nào chạm
`backend/app` trước lượt chạy, nó phải được khai vào chính mục này.

## 8. Điều protocol này KHÔNG hứa

Không hứa `A` sẽ cao hơn. Nó chỉ bảo đảm rằng **nếu** cao hơn thì con số ấy có
nghĩa: đo trên bài chưa từng thấy, ngân sách chốt trước, hệ không đổi giữa chừng.
`LEARNER_IMPACT_NOT_EVALUATED` và `CURRICULUM_SUPPORT_PARTIAL` giữ nguyên — lượt
này không đo gì về người học.
