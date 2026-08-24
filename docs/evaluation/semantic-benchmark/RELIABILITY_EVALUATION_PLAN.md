# RELIABILITY EVALUATION V2 — protocol đo, chốt TRƯỚC khi có seed

> Mọi quyết định trong file này được chốt **trước khi tập SEALED #2 tồn tại** và
> **trước khi biết seed**. Đó là điều kiện duy nhất để nó còn là một phép đo.
>
> **Quan hệ với `RUN2_PROTOCOL.md`: MỞ RỘNG, không thay thế.** §1–§8 và toàn bộ
> §7b của protocol ấy **còn nguyên hiệu lực**. File này thêm hai tầng mà protocol
> cũ không đo (**multi-input replay** và **renderer**) và các chỉ số đi kèm.
> Chỗ nào hai file mâu thuẫn thì `RUN2_PROTOCOL` thắng, trừ những điểm được nêu
> đích danh ở §2 dưới đây.

---

## 0. Vì sao cần V2 — và vì sao KHÔNG được coi nó là "lượt #2 tốt hơn"

Sau lượt #1 (`4e13e2b`, A 3/40 · B 1/40), hệ đã đổi ở bốn nhóm, tất cả đã khai
ở `RUN2_PROTOCOL §7b`:

| Đổi | Ảnh hưởng dự kiến tới số |
|---|---|
| 4 biên chuẩn hoá ký pháp | **tăng** — 22/27 ca trượt cú pháp nay qua được |
| vòng sửa ≤3 lượt (chưa từng chạy ở #1) | **tăng** |
| taxonomy 9 → 11 nghĩa vụ | **tăng** |
| `MAX_NESTING_DEPTH` 6 → 8 | **tăng** |
| **interpreter fail-closed** | **GIẢM** ← đọc kỹ |

Mục cuối phải nói trước, vì nếu không nó sẽ bị đọc ngược: chương trình từng
"chạy xong" nhờ **nuốt lỗi biên** (`pop` trên rỗng thành no-op) nay
`executable=false`. **`A` cũ đếm cả những lượt chạy trên hư không.** Nếu `A` của
V2 thấp hơn 3/40 thì đó **không** phải hồi quy — đó là con số đầu tiên không
tính gian.

---

## 1. DATASET

### 1.1 Không gian mẫu

```
SOURCE UNIVERSE V2   4a9c3564…   189 bài · audit cả 5 SGK · 708 trang
  → SELECTION POOL   34d11adc…    89 bài đủ tư cách theo eligibility rubric
  − đã đo ở lượt #1  e2ebcf79…  − 40 bài (đã lộ cho người sửa mã)
  − DEV                           −  0 bài  (DEV nằm NGOÀI selection pool)
                                 ─────
  KHÔNG GIAN MẪU V2                49 bài chưa từng đo
```

### 1.2 Ba nguồn bị loại, và lý do từng nguồn

| Nguồn | Loại vì |
|---|---|
| 18 fixture `fixtures_coverage_18.py` | **fixture nội bộ** — viết ra để hệ chạy được, không phải để đo |
| 20 case DEV (`dev/cases.json`) | tự khai *"dùng để chỉnh IR/schema/prompt"*; hệ đã được tune trên chính chúng |
| 40 case SEALED #1 | đã lộ cho người sửa mã; chính chúng dẫn dắt bốn nhóm vá ở §0 |

`TIM_MAX`/`GAN_CUNG` trong `replay_harness.py` là **fixture đối chứng của công
cụ đo**, không phải case đánh giá — chúng không nằm trong bất kỳ mẫu số nào.

### 1.3 N — phải quyết TRƯỚC seed

⚠️ **49 bài cho N=40 để lại đúng 9 bài dự phòng.** Custodian loại quá 9 bài lúc
dựng ground truth thì lượt đo **không chạy được**, và lúc ấy mọi lựa chọn đều là
lựa chọn sau khi đã biết vấn đề.

V2 thêm một cách nữa để một case bị loại: nó phải dựng được **bề mặt thị giác**.
Nên dự phòng 9 bài mỏng hơn so với lượt #1.

Ba phương án, chọn một **trước khi cấp seed**:

| | N | Dự phòng | Ngân sách logic | Đánh đổi |
|---|---:|---:|---:|---|
| **P1** | 40 | 9 | 520 | giữ đúng `RUN2_PROTOCOL §3`; hết dự phòng thì kẹt |
| **P2** | 35 | 14 | 455 | an toàn hơn; mọi tỉ lệ rộng hơn, và **đổi một hằng số đã tiền đăng ký** |
| **P3** | 40 | mở rộng SOURCE UNIVERSE trước | 520 | đúng nhất về phương pháp; tốn công custodian |

**Khuyến nghị: P3, lùi về P1 nếu không kịp.** Hạ `N` là cách đắt nhất để mua an
toàn — nó làm yếu **mọi** claim, kể cả những claim không liên quan gì tới việc
thiếu bài.

### 1.4 Việc chỉ GVHD làm được

**Cấp seed #2.** Tính độc lập của phép chọn nằm ở chỗ seed không đến từ người
viết mã và không được chọn sau khi đã thấy kết quả. Seed #1 là `23082026`.

Và **quyết định về sai lệch taxonomy** (`RUN2_PROTOCOL §7b`): giữ 11 nghĩa vụ
kèm lời khai, hay hoàn về 9. Phải chốt trước seed.

---

## 2. PROTOCOL — bảy tầng, mỗi tầng một cổng

```
đề bài SGK (văn xuôi tiếng Việt, KHÔNG kèm pseudocode)
 │
 ├─① analyze + RequestContract ──────────► G0  hợp đồng dựng được
 ├─② LLM sinh Semantic IR (≤3 lượt sửa) ─► G1  qua schema Pydantic
 ├─③ validate_semantic_program ─────────► G2  qua thẩm định ngữ nghĩa
 ├─④ interpreter (FAIL-CLOSED) ─────────► A   chạy trọn, 0 vi phạm biên
 ├─⑤ multi-input replay (0 call LLM) ───► R   không INPUT_IGNORED/DEAD_STATE
 ├─⑥ C₁a → C₁b → C₂ → assurance ────────► B   đủ điều kiện phát
 └─⑦ renderer 4 bề rộng, trình duyệt ───► V   dựng được cảnh đọc được
                                          └─► O   oracle độc lập chấm
```

### 2.1 Hai điều tuyệt đối không được làm ở tầng ⑤

1. **Replay KHÔNG gác cửa phát.** Nó là **quan trắc**. Cho nó chặn `servable` là
   đổi hành vi sản phẩm — ngoài phạm vi task này, và biến `B` của V2 thành thứ
   không so được với `B` của #1.
2. **Không sinh lại IR cho biến thể.** Cùng một chương trình, chỉ đổi
   `initial_value`. Sinh lại là đo LLM lần nữa, không phải đo chương trình.

### 2.2 Tầng ⑦ — cái bẫy đã cắn hai lần trong wave này

> **`status=ok` không phải bằng chứng.** Lần một: runner tiêm envelope thẳng vào
> store nên chứng minh renderer chứ không chứng minh đường sinh. Lần hai:
> envelope `ok` với 5 khung mà **mọi khung đều rỗng** — chỉ lộ khi mở ảnh ra xem.

Nên tầng ⑦ có **ba điều kiện bắt buộc**, thiếu một là bỏ toàn bộ bằng chứng thị
giác của lượt đo:

- **Đi đường thật.** Envelope phải do `run_pipeline` phát ra trong chính lượt
  đo, **cấm** tiêm vào store.
- **Dấu vân tay trang.** Khẳng định đúng mô phỏng đã nạp; sai thì thoát != 0.
- **Tiêm lỗi giả.** `--faultcheck` phải làm bản soát **ĐỎ**. Guard chưa từng đỏ
  là guard chưa được chứng minh.

Vận hành: hai pha. Pha A (backend, tốn quota) ghi envelope; pha B (trình duyệt,
**0 call LLM**) chạy trên chính các envelope ấy. Pha B hỏng thì **không** phải
chạy lại pha A.

### 2.3 Ngân sách

**Không đổi.** Tầng ⑤ và ⑦ tiêu **0 lượt LLM**. Trần vẫn dẫn từ call graph:
`13 × N` lượt logic, headroom HTTP 1,19. Vượt trần ⇒ `BUDGET_EXHAUSTED`,
`evaluation_complete=false`, **không chạy bù**.

### 2.4 Luật của lượt chạy

Kế thừa nguyên `RUN2_PROTOCOL §7`: chạy **đúng một lần** · không vá giữa chừng ·
không chọn lượt đẹp hơn · không thêm nghĩa vụ/checker để cứu case · case hỏng
ghi đúng như nó hỏng.

**Đóng băng mã có hiệu lực lại kể từ commit đóng băng gần nhất.** Bốn lần lệch
đã khai ở §7b; lần thứ năm phải khai tiếp, hoặc không xảy ra.

---

## 3. METRICS

### 3.1 ⚠️ XUNG ĐỘT TÊN — phải đọc trước khi trích bất kỳ chữ cái nào

Yêu cầu task đặt tên `A/B/C/D` cho bốn chỉ số **khác** với `A/B` đã tiền đăng ký
ở `RUN2_PROTOCOL §3`. Đổi nghĩa một chữ cái đã đóng băng là cách chắc chắn nhất
để hai lượt đo không còn so được.

**Giải quyết: giữ nguyên `A` và `B` cũ, đặt tên RIÊNG cho các chỉ số mới.**

| Task gọi | Tên chính thức V2 | Nghĩa | Quan hệ với #1 |
|---|---|---|---|
| A — generation success | **G1**, **G2** | qua schema · qua thẩm định ngữ nghĩa | mới, tách từ nhánh trượt của #1 |
| — | **A** *(giữ nguyên)* | generative executability | **so trực tiếp được** với #1 |
| B — semantic correctness | **O** | oracle độc lập chấm PASS | tương ứng `dung_theo_oracle_doc_lap` của #1 |
| C — replay pass | **R** | qua replay đa đầu vào | **mới hoàn toàn** |
| D — served | **B** *(giữ nguyên)* + **V** | qua cổng nội bộ · dựng được cảnh | `B` so được với #1; `V` mới |

### 3.2 Định nghĩa, và điều mỗi chỉ số KHÔNG nói

| Ký hiệu | Mẫu số | Đo cái gì | **KHÔNG** phải |
|---|---|---|---|
| **G1** | N | IR qua schema Pydantic | không nói chương trình có nghĩa |
| **G2** | N | qua `validate_semantic_program` | ba dạng vô nghĩa vẫn lọt (§5.3) |
| **A** | N | interpreter chạy trọn, **0 vi phạm biên** | **không** phải correctness |
| **R** | *ca có A* | không `INPUT_IGNORED`/`DEAD_STATE` | không chứng minh đúng; chỉ chứng minh **có dùng đầu vào** |
| **B** | N | qua hết chuỗi assurance nội bộ | **không** phải "đúng" — cổng nội bộ không phải oracle |
| **O** | *ca chấm được* | khớp ground truth độc lập | UNGRADED/NO_RESULT đếm **riêng**, không vào tử lẫn mẫu |
| **V** | *ca có B* | cảnh dựng được, 4 bề rộng, faultcheck đỏ được | không nói cảnh **dạy tốt** |

**`A` và `B` vẫn ĐỒNG-PRIMARY.** `A − B` phải **phân rã**; gọi cả khối là
`verification_gap` là báo cáo sai (chỉ một nhánh trong đó mới là thiếu checker).

### 3.3 Luật báo cáo cho mẫu nhỏ — tiền đăng ký

Đây là chỗ dễ overclaim nhất, nên chốt thành luật cứng:

1. **Luôn báo số ĐẾM THÔ** (`k/n`), ở mọi chỉ số, mọi lúc.
2. **Tỉ lệ phần trăm chỉ được viết khi mẫu số ≥ 20.**
3. **Mẫu số < 10 ⇒ CẤM viết phần trăm.** Chỉ liệt kê case đích danh. Điều này
   gần như chắc chắn áp cho `R`, `O`, `V` — vì mẫu số của chúng là *số ca đã qua
   tầng trước*, mà ở #1 con số đó là **3** và **1**.
4. **Cấm khoảng tin cậy.** Một lượt chạy, không lấy mẫu lại, không có mô hình
   sinh — mọi CI ở đây đều là trang trí thống kê.
5. **Cấm gộp mẫu số khác nhau.** `R` tính trên ca có `A`, không tính trên `N`.
   Trộn hai mẫu số là bịa ra một con số không tồn tại.
6. **Cấm so `A` của V2 với `A` của #1 mà không kèm §0** — fail-closed đã đổi
   nghĩa của "chạy xong".

---

## 4. FAILURE TAXONOMY

Sáu lớp, **loại trừ lẫn nhau**, gán theo **cổng đầu tiên** case chết. Mỗi lớp
gắn mã lỗi máy đọc được để không ai phải phân loại bằng cảm nhận.

| # | Lớp | Cổng | Mã lỗi | Nghĩa |
|---|---|---|---|---|
| 0 | **contract failure** | ① | `input_not_grounded`, `GATE_SCOPE_*` | không dựng nổi hợp đồng, hoặc đề ngoài phạm vi (**có thể ĐÚNG**) |
| 1 | **generation failure** | ② | JSON cụt, `MAX_TOKENS`, hết 3 lượt sửa | LLM không phát nổi một đầu ra dùng được |
| 2 | **schema failure** | ② | `semantic_program_invalid` (Pydantic) | sai **cách viết** — đây là lớp bốn biên chuẩn hoá nhắm vào |
| 3 | **semantic validation failure** | ③ | `validate_semantic_program` từ chối | tham chiếu/kiểu/ràng buộc sai |
| 4 | **interpreter failure** | ④ | `SemanticExecutionError` (4 mã), `limit_reached` | **mới đo được từ V2** — trước đây nuốt im lặng |
| 5 | **replay failure** | ⑤ | `INPUT_IGNORED`, `DEAD_STATE` | chương trình không dùng đầu vào |
| 6 | **assurance failure** | ⑥ | `requested_operation_uncovered`, `postcondition_violated`, `verification_gap` | chạy được nhưng không đủ bằng chứng để phát |
| 7 | **rendering failure** | ⑦ | binding không phân giải, khung rỗng, vân tay trang sai | dựng không nổi cảnh đọc được |

**Hai luật gán nhãn:**

- **Lớp 0 không phải lúc nào cũng là thất bại.** Đề ngoài môn bị chặn là hành vi
  **đúng**. Báo riêng, cấm gộp vào tử số thất bại.
- **`capability_gap` ≠ `verification_gap`.** Nói "không làm được" về một bài máy
  vừa làm xong là báo cáo sai năng lực của chính mình.

---

## 5. CLAIM

### 5.1 Được phép ghi — nếu lượt đo hoàn tất

- *"Trên N bài SGK chưa từng dùng để phát triển, hệ sinh được chương trình ngữ
  nghĩa chạy trọn cho **k/N** bài; **m/N** đủ điều kiện phục vụ."* — kèm §0.
- *"Interpreter fail-closed ở mọi vi phạm biên container"* — 11 test RED→GREEN.
- *"Hệ phát hiện được chương trình không dùng đầu vào"* — replay, có ca đối
  chứng cố ý **qua được kiểm tĩnh** C₁b.
- *"Ground truth do người ngoài dựng, tính bằng Python thuần, không import một
  dòng mã sản phẩm."*
- *"Chi phí LLM không tăng theo số bước mô phỏng"* — claim **cấu trúc** (D1),
  kiểm bằng call graph.
- *"Đề ngoài năng lực bị từ chối trung thực thay vì dựng mô phỏng gần đúng."*

### 5.2 CẤM ghi — kể cả khi số đẹp

- ~~"AI sinh mô phỏng đáng tin cậy"~~ — không chỉ số nào trong §3 đo được chữ
  "đáng tin cậy"; nó là kết luận, không phải số đo.
- ~~"Hệ sinh đúng X %"~~ khi mẫu số < 20 (§3.3).
- ~~"Mô phỏng phản ánh đúng thuật toán"~~ chỉ dựa vào `R` — replay chứng minh
  **có dùng đầu vào**, không chứng minh **dùng đúng**.
- ~~"`B` là độ chính xác"~~ — `B` là quyết định assurance **nội bộ**; cổng nội
  bộ không phải oracle.
- ~~"Phủ chương trình Tin học THPT"~~ — `CURRICULUM_SUPPORT_PARTIAL` giữ nguyên.
- ~~Bất kỳ claim nào về **người học**~~ — `LEARNER_IMPACT_NOT_EVALUATED` giữ
  nguyên; lượt này không đo gì về người học.
- ~~"Mô phỏng tương tác"~~ trên route sinh — `apply` hiện là hàm đồng nhất; học
  sinh chỉ xem từng bước.
- ~~So sánh trực tiếp với ALGOGEN/Code2Video~~ — họ nhận **pseudocode** kèm đề
  và chấm bằng **LLM-as-judge**; khác population, khác oracle, không so được.

### 5.3 Ba lỗ đã biết, phải nêu trong phần hạn chế

1. `validate_semantic_program` **cho qua** ba dạng vô nghĩa, đo được 2026-08-24:
   `statements: []` · gán vào biến chưa khai · `value_box` trỏ biến lạ.
2. Cổng grounding chặn **hằng số thuật toán** (bảng cặp ngoặc) vì không có fact
   để ghim — căng thẳng thiết kế thật, chưa sửa, có chủ đích.
3. Bằng chứng thị giác cho envelope **do route phát** trước V2 là `PARTIAL` —
   ảnh cũ chụp đúng một lượt **dương tính giả**.

---

## 6. Trình tự chạy

```bash
# 0. cổng đóng băng — phải xanh
python backend/scripts/freeze_evaluation_candidate.py --verify

# 1. custodian chọn (KHÔNG phải người viết mã)
cd docs/evaluation/semantic-benchmark/custodian
python select_by_seed.py --seed <SEED_GVHD> --exclude-measured --write
python sealed_ground_truth.py

# 2. PHA A — backend, tốn quota, MỘT LẦN
cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
  .venv/Scripts/python.exe scripts/run_sealed_evaluation.py

# 3. PHA B — trình duyệt, 0 call LLM, chạy lại được
cd frontend && npm run dev        # cửa sổ khác
node scripts/verify-semantic-e2e-render.mjs --faultcheck   # phải ĐỎ
node scripts/verify-semantic-e2e-render.mjs
```

**Điều kiện tiên quyết chưa xong** — cả hai đều thuộc GVHD, và cả hai phải xong
**trước** bước 1: quyết định taxonomy (§7b) · seed #2.

**Điều kiện kỹ thuật chưa xong** — runner phải ghi thêm `G1/G2/R/V` và phân loại
theo §4. Đó là việc **harness** (`backend/scripts`), 0 API call, không chạm hệ
được đo, và **chưa làm** tính tới lúc viết file này.
