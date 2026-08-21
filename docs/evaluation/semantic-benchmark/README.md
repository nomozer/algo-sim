# Benchmark của route sinh ngữ nghĩa — DEV, SEALED, và danh tính bản được đo

## Hai hash, đọc kỹ kẻo hiểu nhầm

Manifest luôn ghi **commit của bản được đo**; commit *chứa* manifest thì là
commit kế tiếp. Một hash trả lời *"đo bản nào"*, hash kia trả lời *"bản ghi nằm
ở đâu"* — đọc lẫn là tưởng manifest trỏ nhầm.

| lần đóng băng | candidate source commit (ghi trong manifest) | freeze/manifest commit |
|---|---|---|
| 2026-08-21, bản đầu | `9898d13` | `5506027` |
| 2026-08-21, sau khi nối route | `c6c5c28` | `901182c` |
| 2026-08-21, sau sáu điểm sửa phương pháp đo | `89fee9b` | `b141788` |
| 2026-08-22, ngân sách cuối | `36bae92` | `2fa3e88` |
| **2026-08-22, sau pilot — BẢN ĐEM ĐO** | **`4e13e2b`** | `4945be6` |

> **`36bae92` nay là SUPERSEDED.** Nó được đóng băng trước khi route từng chạy
> với API thật; bốn lượt pilot cho thấy nó **chưa gọi nổi API một lần nào** (schema
> có `$ref` treo ⇒ HTTP 400 toàn bộ). Đo trên nó là đo một hệ không chạy.
>
> Bản đem đo nay là dòng cuối, sau khi sửa: schema/thẻ văn phạm, thứ tự shadow,
> danh xưng chung giữa hai lượt LLM, và **hai lỗi fail-closed của C₂**. Chi tiết
> ở `pilot-results-4/PHAT_HIEN.md`.
>
> Từ đây **không sửa hệ nữa**, và **không chạy lại 40 case pilot** — tập đó đã bị
> đốt qua bốn lượt và chỉ còn giá trị như nhật ký kỹ thuật.

Mỗi lần, hash bên trái là **cha trực tiếp** của hash bên phải
(`git rev-parse <phải>^` → `<trái>`), và manifest được sinh **trên cây sạch**
(`cay_lam_viec_sach: true`). Commit bên phải chỉ thêm manifest cùng test khoá
nó — **không đụng** một dòng nào của hệ được đo.

**Vì sao có lần thứ hai.** Phát hiện `stage_semantic_program` **không có một ai
gọi**: route ngữ nghĩa chưa bao giờ đi qua `run_pipeline`, nên bản `9898d13` đo
được các *mảnh* chứ không đo được *đường đi*. Nối xong, `CACHE_VERSION` 33 → 34.

**Vì sao có lần thứ ba.** Soát lại toàn bộ đường đo và sửa **sáu lỗi phương
pháp** — lớn nhất là semantic shadow bị classifier legacy quyết định có được
chạy hay không, khiến claim A hoá ra là một claim về *classifier*. Chi tiết
từng điểm nằm trong commit `89fee9b`.

Taxonomy, tập primitive, schema và DEV giữ **nguyên hash** qua cả ba lần — thay
đổi nằm ở chỗ nối dây và ở cách đo, không ở hợp đồng. Cả ba đều là thay đổi pha
DEV và đều xảy ra **trước khi SEALED được niêm phong**, nên luật con dấu không
bị đụng tới lần nào.

Kiểm bất cứ lúc nào bằng:

```bash
cd backend && .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
```

## `34a10a9c…` là INTERNAL LIVE PILOT — đã lưu trữ, KHÔNG tái sử dụng

Tập fingerprint **`34a10a9c…`** nằm ở `pilot/sealed-pilot-34a10a9c/` là **pilot
nội bộ**, không phải SEALED. Nó **không được** dùng lại làm SEALED hay làm số
liệu Task 12.

Lý do nó bị loại tư cách đã ghi ngay trong dữ liệu (`cases.json`, khối
`custodian_declaration`): custodian không độc lập với tác giả hệ thống. Ngoài
ra nó đã bị chạy **bốn lượt** và hệ được sửa dựa trên chính nó, nên tính
held-out bằng không.

Việc dời chỗ **không phá con dấu pilot**: nội dung không đổi một byte,
`cases.json` và `FINGERPRINT.txt` đi cùng nhau, hash vẫn đúng `34a10a9c…`.
Giữ lại làm bằng chứng lịch sử — bốn lượt chạy tương ứng ở `pilot-results/`
→ `pilot-results-4/`, và các phát hiện ở
`pilot-results-4/PHAT_HIEN.md`.

`ground_truth_solver.py` đi cùng tập vì nó sinh ra **đúng 40 case ấy** — nó là
một phần của dataset, không phải công cụ chung của benchmark.

`sealed/` nay **trống**, dành riêng cho custodian thứ ba.

## Ba tập dữ liệu, ba vai trò khác hẳn nhau

| | Ai soạn | Được nhìn? | Đổi được cái gì |
|---|---|---|---|
| **DEV** (20 case) | agent phát triển | có | **hệ** — IR, schema, prompt, taxonomy |
| **SEALED** (40 case) | **custodian độc lập** | **không**, tới Task 12 | **kết luận của luận văn** |
| **EVALUATION_CANDIDATE** | sinh từ nguồn | có | không đổi gì — nó là ảnh chụp danh tính |

Luật con dấu (spec §7.4), viết gọn:

> **DEV được phép làm thay đổi HỆ. SEALED chỉ được phép làm thay đổi KẾT LUẬN.**

## SEALED phải được chuẩn bị NGOÀI development context

Đây không phải hình thức. Nếu agent viết hệ đọc SEALED trước khi niêm phong thì
con dấu **đã vỡ ngay lúc ấy**: mọi lựa chọn sau đó — thêm một checker, nới một
miền kiểu, sửa một câu prompt — đều có thể bị dẫn dắt bởi thứ đã thấy, và không
ai chứng minh được là không.

Quy trình đúng:

```
CUSTODIAN ĐỘC LẬP
  40 case text
  → audit eligibility theo rubric §7.2
  → dựng ground truth ĐỘC LẬP
  → kiểm 4 metadata guard
  → seal + fingerprint
  → giao cho phía phát triển ĐÚNG hai thứ: đường dẫn + fingerprint

                 ↓ khi Task 12 bắt đầu

PHÍA PHÁT TRIỂN
  candidate đã đóng băng
  → mở SEALED ĐÚNG MỘT LẦN
  → chạy evaluation
  → TUYỆT ĐỐI không sửa hệ
  → báo A · B · A−B (đã phân rã) · oracle độc lập · D1 · D2
```

> Sau khi mở SEALED, case nào hỏng vì thiếu checker / thiếu primitive / IR không
> diễn đạt được thì **ghi đúng cái hỏng đó**. Không vá rồi chạy lại. Một lần vá
> là con dấu mất hiệu lực và phải niêm phong tập mới.

## Dạng dữ liệu SEALED

`docs/evaluation/semantic-benchmark/sealed/cases.json` — một object, khoá `cases`
là mảng:

```json
{
  "case_id": "sealed_001",
  "source": { "book": "tin-hoc-11-cs.pdf", "location": "trang 62, bài 3" },
  "problem_text": "…đề bài nguyên văn, tiếng Việt…",
  "eligibility_audit": {
    "discrete": true,
    "finite_input": true,
    "deterministic_bounded_procedure": true,
    "allowed_state_family": ["array", "int"],
    "allowed_operation_family": ["gán", "so sánh", "duyệt"],
    "in_scope": true
  },
  "metadata": {
    "no_specialized_module": true,
    "no_target_template": true,
    "not_prompt_example": true,
    "expressible_in_ir": true
  },
  // ↑ BA guard đầu là CỨNG (đều nói về nhiễm dữ liệu).
  //   `expressible_in_ir` chỉ là GHI CHÚ MÔ TẢ — `false` hợp lệ, và KHÔNG BAO
  //   GIỜ là lý do loại case. Xem "Năng lực của hệ không phải bộ lọc" bên dưới.
  "prescribed_procedure": null,
  "ground_truth": {
    "kind": "human | independent_solver | property_oracle",
    "provenance": "…dựng bằng gì, ai dựng…",
    "expected": [
      { "obligation_kind": "extremum", "value": 89 }
    ]
  },
  "expected_obligations": []
}
```

### Năng lực của hệ KHÔNG phải bộ lọc population

Sửa 2026-08-22, trước khi giao custodian. `expressible_in_ir` từng nằm trong
nhóm guard cứng và bị bắt phải `true`. Đó là dùng **năng lực hiện tại của IR**
làm điều kiện loại case — tức lọc bỏ trước đúng những bài đáng lẽ phải ở lại để
thành `capability_gap` trung thực. Hệ quả: tỉ lệ **A** cao lên một cách giả tạo,
và cao đúng ở chỗ không ai kiểm được.

Luật đúng, vốn đã có sẵn trong `eligibility_rubric.md`:

| tình huống | xử lý |
|---|---|
| Không thoả rubric §7.2 | **ngoài population** — không đưa vào |
| Thoả rubric, **IR hiện tại chịu thua** | **VẪN Ở TRONG** — kết quả `capability_gap` |

`capability_gap` là **kết quả có giá trị**, không phải sự cố. Sửa IR để cứu một
case như thế sau khi mở SEALED là **phá con dấu**.

### `expected` KHÔNG được nhắc tên biến

Custodian khai **nghĩa vụ + giá trị đúng**. Tên biến trong bộ nhớ là do LLM tự
đặt, nên bắt custodian đoán nó là bắt đoán sai: một chương trình hoàn toàn đúng
gọi biến `ket_qua` trong khi custodian ghi `max_value` sẽ **FAIL oan**, và cái
FAIL oan ấy đi thẳng vào con số chính của luận văn. Runner đọc ánh xạ
nghĩa-vụ → tên-biến từ `RequestContract` mà server đã đóng băng.

`obligation_kind` lấy từ taxonomy (`OBLIGATION_KINDS`, 9 giá trị). Đề có **nhiều
nghĩa vụ cùng loại** thì thêm `"index": 0|1|…`; thiếu index mà nhập nhằng thì
runner trả `UNGRADED` chứ không đoán.

Ba điều bắt buộc:

- `ground_truth.kind` **không bao giờ** được là hệ đang bị kiểm. Lấy
  `SemanticProgramInterpreter` làm thước đo chính nó thì mọi con số thu được đều
  rỗng nghĩa.
- `expected_obligations` **chỉ điền nếu custodian tự xác lập trước khi seal**.
  Để hệ hiện tại sinh trường đó rồi dùng lại làm ground truth là tự chấm bằng
  chính đầu ra của mình — bỏ trống còn hơn.
- Đề **không đòi kết quả cụ thể** (chỉ yêu cầu quan sát diễn biến) thì để
  `expected` rỗng. Case ấy được đếm `UNGRADED` và **không** vào tử số lẫn mẫu số
  của bất kỳ tỉ lệ nào.

`prescribed_procedure`: `null` khi đề **không ép** thủ tục. Có ép thì dùng giá
trị trong `SEMANTIC_PRESCRIBED_PROCEDURES`, và oracle sẽ so **canonical
mechanism events** chứ không so raw trace 1:1 (spec §5.5).

## Chạy Task 12

Sau khi custodian giao đường dẫn + fingerprint, **một lệnh, một lần**:

```bash
cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
  .venv/Scripts/python.exe scripts/run_sealed_evaluation.py \
  --out-dir ../docs/evaluation/semantic-benchmark/results
```

Runner tự từ chối chạy nếu candidate đã lệch, nếu chưa có vân tay, hoặc nếu
`cases.json` bị sửa sau khi niêm phong. Nó chạy ở chế độ **shadow** nên một lượt
đo được cả hai route và người học không nhận đầu ra khác đi.

Runner được viết **trước khi thấy SEALED**, và phần chấm/tổng kết của nó bị khoá
offline bởi `tests/semantic_program/test_sealed_runner.py` — vì nó chỉ được chạy
một lần, sai từ lượt đầu là không cứu được.

## Niêm phong

```bash
cd backend && .venv/Scripts/python.exe scripts/seal_benchmark.py
```

Lần đầu ghi `sealed/FINGERPRINT.txt`; các lần sau **kiểm** và thoát != 0 khi
lệch. `tests/semantic_program/test_benchmark_seal.py` chạy cùng suite mặc định:
hiện nó SKIP vì `sealed/cases.json` chưa tồn tại, và sẽ tự bật khi có.

## Ngân sách Task 12 — đã duyệt, không nâng sau khi thấy số

```
N = 40  ·  trần logic 440  ·  trần HTTP 520
```

Đường **hạnh phúc** là 4 lượt/case: `analyze` · `classify` · `semantic_analyze` ·
`semantic_program`. Nhưng 4 **không phải upper bound** — bound thật dẫn từ call
graph là **11** (`freeze_protocol.md §2`), và `440 = 11 × 40`.

`440` không cho phép hệ "thử 11 lần cho đẹp": mỗi stage vẫn giữ retry bound
riêng đã có sẵn trong production code. Nó chỉ là tổng trần của những đường
retry/reclassify **đã tồn tại từ trước evaluation**.

Trần cũ `160` bị bỏ vì nó **xung đột với protocol**: 4×40 = 160 đúng bằng trần,
nên một lần retry duy nhất cũng đủ làm evaluation không đạt `N=40` — trong khi
`N=40` là mục tiêu nghiên cứu đã khoá. Ngân sách phải phủ worst case.

Cả hai trục được **cưỡng chế** trong `ApiBudget`, không chỉ đếm. Vượt ⇒
`BUDGET_EXHAUSTED`, `evaluation_complete: false`, **không chạy bù**.

> Chốt 2026-08-22, trước khi niêm phong. **Không nâng sau khi SEALED được mở.**

## "Hệ được đo = `36bae92`" nay là mệnh đề MÁY KIỂM ĐƯỢC

Trước 2026-08-22, `--verify` chỉ so **taxonomy · primitive · schema · DEV ·
`CACHE_VERSION`** — tức chỉ khoá **hợp đồng**. Nó hoàn toàn **mù** trước việc
sửa `pipeline.py`, `route.py`, interpreter, validator hay bất kỳ checker nào:
`--verify` vẫn xanh trong khi ngữ nghĩa hệ đã đổi. Đúng loại lỗ mà sự cố *"route
chưa từng được nối"* đã cho thấy là có thật.

Manifest nay có thêm:

```json
"measured_system": {
  "paths": ["backend/app", "frontend/src/simulations/domains/semantic", …],
  "so_file": 125,
  "tree_hash": "5608fbfe…"
}
```

Ranh giới chọn theo **nguyên tắc**, không theo phán đoán từng file:

| | thuộc về |
|---|---|
| `backend/app/**` + module 2D + schema mirror | **hệ được đo** — đổi một dòng là `--verify` ĐỎ |
| `backend/scripts/**`, `backend/tests/**`, `docs/**` | **bộ đo** — được siết chặt tự do |

Nhờ vậy harness cứng cáp thêm mà **không** phải đóng băng lại candidate, còn một
dòng mã sản phẩm đổi thì không lọt được.

**Đã chứng minh bằng tiêm lỗi**: thêm một dòng *comment* vào `route.py` ⇒
`--verify` đỏ, exit 1, kèm sẵn lệnh `git diff --stat` để tra. Khôi phục ⇒ hash
trùng khít trở lại.

> **Đọc `commit` trong manifest cho đúng.** Trường `commit` ghi thời điểm
> manifest được **sinh ra**; danh tính của **hệ được đo** nằm ở `tree_hash`.
> Hai thứ tách nhau từ khi harness được phép đổi độc lập. Kiểm được:
> `git diff 36bae92 HEAD -- backend/app` **rỗng**, và `tree_hash` giữ nguyên
> `5608fbfe…` qua mọi lần đóng băng kể từ `36bae92`.

## Hai danh tính trong artifact Task 12

Báo cáo ghi **riêng** hai hash, và chúng trả lời hai câu khác nhau:

```json
"measured_system_candidate": "36bae92",
"evaluation_harness_commit": { "commit": "…", "cay_sach": true }
```

| trường | câu hỏi |
|---|---|
| `measured_system_candidate` | **đo bản nào** của hệ sinh mô phỏng |
| `evaluation_harness_commit` | **bộ đo phiên bản nào** đã đo nó (HEAD lúc chạy) |

Tách ra vì harness — runner, validator, test instrumentation — vẫn còn có thể
được siết chặt trước SEALED, và **không có lý do gì đóng băng lại candidate chỉ
vì bộ đo cứng cáp hơn**, miễn thay đổi ấy không đụng vào **ngữ nghĩa** của hệ
được đo. Gộp hai hash làm một thì hoặc phải refreeze mỗi lần thêm một test,
hoặc phải im lặng để candidate trôi khỏi HEAD — cả hai đều tệ.

`cay_sach: false` **không chặn** lượt chạy: harness bẩn không làm sai kết quả
đo. Nhưng nó được ghi lại, vì người đọc có quyền biết bộ đo lúc ấy chưa commit.

## Các con số phải báo — và đừng gộp chúng

| | nghĩa |
|---|---|
| **A** | dựng được mô phỏng **chạy được** |
| **B** `B_internal_servable` | qua **hết cổng nội bộ** (STRONG-assurance). **Không phải "đúng"** — cổng nội bộ không phải oracle độc lập |
| **A − B** | chạy được nhưng không phát được. **Phải phân rã**: `verification_gap` · C₁b · C₂ · binding/compile |
| oracle độc lập | pass / fail / **ungraded** / **no_result**, tách hẳn khỏi B |
| **D1** | claim **cấu trúc**: sau khi IR sinh xong, interpreter chạy bao nhiêu bước cũng không tốn thêm lượt LLM nào. Kiểm bằng call graph |
| **D2** | claim **thực nghiệm** về token, chỉ trên matched subset |

Hai chỗ dễ viết sai vào luận văn:

- Gọi cả khối **A − B** là `verification_gap`. Chỉ một nhánh trong đó là "thiếu
  cách kiểm chứng"; ba nhánh còn lại là chương trình **tự mâu thuẫn** (C₁b/C₂)
  hoặc không dựng nổi bề mặt thị giác.
- Gọi token/case là **D1**. Đó là telemetry hỗ trợ. D1 là claim cấu trúc, và
  bằng chứng của nó là *số lượt LLM đứng yên trong khi số bước trải rộng*.

Case `servable=true` mà oracle độc lập nói **sai** được nêu đích danh trong báo
cáo (`phat_nhung_oracle_noi_SAI`). Khác 0 ⇒ cổng nội bộ chưa đủ, và **không được
viết rằng những case ấy "an toàn"**.

Vượt trần ⇒ dừng và ghi `BUDGET_EXHAUSTED`. Trần HTTP rộng hơn trần logic **chỉ
để chịu lỗi tạm thời**, không phải để dò tìm kết quả tốt hơn.

D2 dùng đúng matched-subset rule đã khoá ở `freeze_protocol.md`: tối đa 12 case,
chọn tất định theo `case_id`, **không chọn lại sau khi biết kết quả**.
