# V3_THRESHOLD_AND_RUN_IDENTITY_POLICY

> Wave 2026-09-05. **0 lượt gọi model.** Không rút ca, không chạy live, không
> reseal. Chỉ sửa bộ đo, chính sách, test và tài liệu — tất cả **ngoài**
> `MEASURED_SYSTEM_PATHS`.
>
> Nội dung `de`, `mong`, tham số và đáp số của V3 **vẫn chưa đọc**.
> `EXTERNAL_SEED = 5324284654432805119` **vẫn chưa dùng**.

## 1. ROOT_CAUSE

Con dấu V3 khoá *"đo CÁI GÌ"* — candidate `a696200e…`, pool `36c2153e…`. Nó
không khoá *"đo NHƯ THẾ NÀO"*. Trước wave này, ba thứ quyết định con số cuối
cùng đều **đổi được sau khi biết kết quả mà không cổng nào thấy**:

1. **Ngưỡng** không tồn tại ở dạng máy đọc được. Nó nằm trong văn xuôi của các
   report V1/V2 — nghĩa là mỗi lượt đọc lại là một lượt diễn giải.
2. **Bộ chấm** (`acceptance_verdict.py`) không được ghim vào `RunManifest`.
   Manifest ghi `runner_hash` và dừng ở đó.
3. **Quy tắc quy trách nhiệm** cho `SYSTEM_EXPRESSIVENESS_GAP` — lớp verdict
   mới nhất và tốn kém nhất — chỉ tồn tại trong docstring của scorer.

Đổi ngưỡng sau khi thấy kết quả là cách rẻ nhất để một phép đo nói bất cứ điều
gì ta muốn, và nó không để lại dấu vết nào trong artifact.

Wave này đóng cả ba, cộng hai lỗ tự tìm ra khi làm (§8).

## 2. PRE_RESULT_THRESHOLD_RATIONALE

Ngưỡng khoá **trước**, nếu không nó chỉ mô tả lại kết quả. Ba lựa chọn thiết
kế đáng nêu, vì cả ba đều có phương án dễ hơn mà sai:

**Ngưỡng dương tính là `1.0`, không phải một tỉ lệ "hợp lý".** V3 rút 9 ca
dương. Với n = 9, mọi ngưỡng kiểu 8/9 chỉ là một ca được tha — và ca được tha
là ca ta sẽ nhìn kỹ nhất sau khi biết nó hỏng. `1.0` không có chỗ cho việc đó.
Nếu 9/9 là quá nghiêm với thực tế, đó là **kết luận của phép đo**, không phải
lý do sửa ngưỡng.

**Mẫu số không bao giờ được hạ.** `never_lower_denominator: true` +
`every_attempt_in_denominator: true`. Family thiếu ca ⇒ `INSUFFICIENT_SAMPLE`,
**không** chấm trên mẫu nhỏ hơn rồi báo tỉ lệ đẹp.

**`eventual` tính trong repair limit đã khoá.** First-attempt và số lượt sửa
báo riêng — chúng là thông tin thật, nhưng chúng không đổi ngưỡng. Sản phẩm
thật chạy với repair, nên nghiệm thu sản phẩm phải đo hành vi có repair.

`limited_reproducibility_allowed` để **`null` có chủ đích** — §6.

## 3. MACHINE_READABLE_POLICY

`backend/scripts/policies/curved_v3_threshold_policy.json`

```
THRESHOLD_POLICY_ID       CURVED_V3_ACCEPTANCE
THRESHOLD_POLICY_VERSION  1.0.0
THRESHOLD_POLICY_HASH     c0a77cd9cd57ca7da96ce2e5c320443c9ea3a815066d245348c754a0e98cbb38
```

Dạng chính tắc: `json.dumps(obj, sort_keys=True, ensure_ascii=False,
separators=(",",":"))`. Reformat file (thụt lề, thứ tự khoá, CRLF↔LF) **không**
đổi băm; đổi một **con số** thì đổi. Đó đúng là ranh giới cần — hình thức tự
do, nội dung bất biến.

`sample_design` (13 ô · 9 dương · 4 âm · 2 bài/ô · rút 1) đo từ **con dấu +
aggregate chỉ-đếm**, không đọc nội dung ca. Ba ô dương mỗi family.

Ngưỡng khoá đúng các giá trị prompt yêu cầu — kiểm bằng máy ở
`tests/test_v3_threshold_and_run_identity.py` §B, đối chiếu `sample_design` với
seal thật chứ không với giả định.

## 4. ATTRIBUTION_RUBRIC

`backend/scripts/policies/curved_v3_attribution_rubric.json`

```
ATTRIBUTION_RUBRIC_HASH   d44f2b7c19b4904fee661de7c9b62f934c70b0f2108c519099ab30370d70572b
```

`valid_path = NO` ⇒ `SYSTEM_EXPRESSIVENESS_GAP`, và chỉ khi **đủ cả sáu** điều
kiện. Rubric liệt luôn bốn **tín hiệu KHÔNG đủ** — `AMBIGUOUS_FIRST_BINDING`
một mình, tên ô toán hạng là `radius`, chuỗi "đường kính" trong đề, đáp số
không khớp. Bốn cái đó đọc rất giống bằng chứng và không phải bằng chứng.

`valid_path = UNKNOWN` ⇒ `ATTRIBUTION_UNRESOLVED`: không tính lỗi model, không
tính system gap **đã chứng minh**, chặn product promotion, **không** làm hỏng
run. Bộ đo thà ghi "chưa biết" còn hơn quy sai trách nhiệm.

Precedence: grounding và schema đứng **trước** quy tắc năng lực — dữ kiện chưa
truy được về đề thì câu hỏi *"hệ có đường không"* còn chưa đặt ra được.

Rubric tổng quát theo **năng lực/kiểu**; `case_id_decides_verdict: false`.

## 5. RUN_MANIFEST_CONTRACT

`ARTIFACT_SCHEMA_VERSION` **1.0 → 1.1**. Đây là version của **bộ đo**, không
phải `CACHE_VERSION` (giữ nguyên 78).

Trường mới, tất cả có kiểu và có guard đọc:

| nhóm | trường |
|---|---|
| bộ chấm & chính sách | `scorer_path` · `scorer_hash` · `threshold_policy_path` · `threshold_policy_hash` · `attribution_rubric_hash` · `policy_loader_hash` |
| danh tính model | `model_provider` · `model_name` · `model_version_or_snapshot` |
| tham số giải mã | `temperature` · `top_p` · `max_output_tokens` · `repair_limit` |
| hạ tầng | `transport_retry_policy` · `application_call_budget` |

Băm ghi **lúc mở lượt đo**, không phải lúc chấm — băm lúc chấm là băm thứ đang
chạy, và nó khớp chính nó dù ai đó vừa sửa bộ chấm giữa chừng.

`kiem_ghim_bo_do()` nhận **dict đọc từ đĩa**, không nhận `RunManifest` trong bộ
nhớ. Đó là toàn bộ điểm của nó: ghim rồi recompute trong cùng một tiến trình là
phép so **luôn đúng** — giữa hai lần đọc file không có gì kịp đổi. Trôi chỉ
thành quan sát được khi so bản đã ghi của lượt trước với hiện tại.

Tương thích lịch sử bằng **version dispatch rõ ràng**: manifest 1.0 vẫn đọc
được (thiếu trường ⇒ `None`, không phải lỗi đọc) nhưng `kiem_ghim_bo_do` trả 4
lỗi "THIẾU" cho nó. Đọc được và dùng để nghiệm thu được là **hai câu khác
nhau**, và guard nói cả hai thành tiếng.

## 6. MODEL_IDENTITY_POLICY

Đọc từ cấu hình thật của kho, **không gọi provider** — câu hỏi *"alias này trỏ
snapshot nào"* chỉ provider trả lời được, và một lượt gọi để hỏi cũng là một
lượt gọi.

```
MODEL_PROVIDER                  gemini
MODEL_NAME                      gemini-2.5-flash        (alias, GEMINI_MODEL)
MODEL_VERSION_OR_SNAPSHOT       null
TEMPERATURE                     0.2                     (mặc định call_gemini)
TOP_P                           null                    (KHÔNG gửi)
MAX_OUTPUT_TOKENS               null                    (KHÔNG gửi)
REPAIR_LIMIT                    3                       (MAX_SEMANTIC_PROGRAM_ATTEMPTS)
MODEL_IDENTITY_REPRODUCIBILITY  LIMITED
```

⚠️ **Ràng buộc thật, không phải thiếu sót của wave này.** Ghi `modelVersion` từ
response metadata đòi sửa `app/ai/gemini.py` — nằm **trong**
`MEASURED_SYSTEM_PATHS`, tức phá đóng băng candidate `a696200e…` và buộc reseal
V3. Ba đường ra, và cả ba là quyết định của người ngoài:

1. **Reseal** sau khi thêm ghi `modelVersion` — được ghim thật, tốn một chu kỳ
   đóng băng.
2. **Đặt `GEMINI_MODEL`** thành một snapshot có ngày — không sửa mã, nhưng đổi
   *model nào đang được đo*.
3. **Chấp nhận `LIMITED`** — ghi alias + UTC run time + response metadata đầy
   đủ, và khai giới hạn trong khoá luận.

`limited_reproducibility_allowed` để **`null`**: "khoá luận có chấp nhận
`LIMITED` không" là quyết định **học thuật của người hướng dẫn**, không phải
của bộ đo. Bộ đo tự đặt giá trị đó là bộ đo tự cho mình quyền nới chuẩn.

## 7. CERTIFIER_HARDENING

`certify_acceptance_runner.py` nay kiểm thêm: bốn băm bộ đo (đọc manifest **từ
đĩa**), `artifact_schema_version`, và `MP.kiem_chinh_sach` — chính sách có đủ
trường, `created_before_live_run` có `true`, và có trỏ **đúng** candidate + pool
đang đo không.

**Tách verdict, có chủ đích.** Lượt chứng nhận chạy trên ca **tổng hợp** với
`model={"provider": "gia"}`. Bắt nó ghim snapshot model là bắt một ca giả khai
danh tính thật, và cách duy nhất để nó xanh là **nói dối**. Nên:

```
RUNNER_CERTIFICATION           PASS          ← bộ đo có chấm đúng không
READY_FOR_INDEPENDENT_V3_LIVE  CONDITIONAL   ← lượt live có tái lập được không
```

Readiness đo trên **cấu hình thật** của kho và **không** đổi mã thoát: bộ đo
đúng là một chuyện, lượt live được phép chạy là chuyện khác — và chuyện thứ hai
còn chờ một quyết định học thuật, không phải một lỗi cần sửa. Gộp hai câu vào
một verdict thì hoặc chứng nhận đỏ oan, hoặc readiness xanh oan.

Certifier in thẳng bốn dòng còn thiếu, nên §13 dưới đây là **số máy đo**, không
phải nhận định của tôi.

## 8. FAULT_INJECTION

Mọi injection đều **đỏ trước, xanh sau** — guard chưa từng đỏ là guard chưa
được chứng minh.

| # | tiêm | guard | test |
|---|---|---|---|
| 1 | `eventual_servable_rate` 1.0 → 0.8 | băm chính sách lệch | `test_F1` |
| 2 | scorer đổi một byte | `kiem_ghim_bo_do` | `test_F2`, `test_F2b` |
| 3 | rubric `UNKNOWN → MODEL_STATIC_FAILURE` | băm rubric lệch | `test_F3` |
| 4 | manifest thiếu bất kỳ băm nào trong bốn | nhánh "THIẾU" | `test_F2b` |
| 5 | model chỉ có alias | `MODEL_IDENTITY_UNPINNED` | `test_E1` |
| 6 | `top_p` / `max_output_tokens` trống | `DECODING_INCOMPLETE` | `test_E1` |
| 7 | threshold đổi sau khi manifest tạo | `threshold_policy_hash` lệch | `test_F2b` |
| 8 | hạ mẫu số | băm chính sách lệch | `test_F4` |
| 9 | `UNRELATED_FAIL_CLOSED` coi là đạt | băm chính sách lệch | `test_F5` |
| 10 | bằng chứng attribution thiếu `reason`/`authority_hashes` | `kiem_bang_chung_quy_trach_nhiem` | `test_F2f` |
| 11 | manifest 1.1 thiếu trường bắt buộc | `kiem_manifest_du_truong` | `test_F2d` |
| 12 | thiếu file chính sách | `FileNotFoundError`, không im lặng | `test_F6` |
| 13 | chính sách trỏ sai candidate | `kiem_chinh_sach` | `test_F7` |
| 14 | chạy lại vào thư mục cũ | resume guard | `test_D5` |

**Hai lỗ tự tìm ra khi làm wave này**, không có trong đề bài:

**① Guard nói chuyện được bằng văn xuôi.** Phép kiểm tham số giải mã ban đầu là
`is not None`. `run_curved_ergonomics_v2.py:297` ghi thật
`"repair_attempts": "mặc định sản phẩm"` — một chuỗi văn xuôi vượt qua phép ấy,
đọc như đã khai, và **không** nói con số nào đã dùng. Đo bằng máy:

```
guard TRƯỚC khi cứng : PINNED
guard SAU  khi cứng  : DECODING_INCOMPLETE
```

Đã cứng bằng `_la_so` (loại cả `bool` — `True` là `int` trong Python).
`test_E2b` neo đúng tiền lệ thật trong kho; `test_E2c` neo cái bẫy `bool`.

**② Chuỗi ghim hở ở mắt cuối.** Cả ba băm chính sách đều do
`measurement_policy` **tính ra**. Không ghim chính nó thì còn một nước đi: đổi
phép băm **trước** khi mở lượt đo — manifest và certifier sẽ nhất trí với nhau,
và cùng sai. Đóng bằng `policy_loader_hash`.

## 9. MEASUREMENT_IDENTITY_DELTA

Đo bằng `git stash` (trước) và tính lại (sau), không suy từ diff.

| | trước | sau | |
|---|---|---|---|
| `run_curved_acceptance.py` | `11e4b620…` | `11e4b620…` | **KHÔNG đổi** |
| `acceptance_verdict.py` (scorer) | `4f7cae90…` | `4f7cae90…` | **KHÔNG đổi** |
| `acceptance_integrity.py` | `c18d1531…` | `ae42adce…` | ĐỔI |
| `certify_acceptance_runner.py` | `4f1692b6…` | `9f514137…` | ĐỔI |
| `measurement_policy.py` | (chưa có) | `379b9a14…` | MỚI |
| threshold policy | (chưa có) | `c0a77cd9…` | MỚI |
| attribution rubric | (chưa có) | `d44f2b7c…` | MỚI |
| `ARTIFACT_SCHEMA_VERSION` | 1.0 | **1.1** | ĐỔI |
| candidate | `a696200e…` (89 file) | `a696200e…` | KHÔNG đổi · verify exit 0 |
| `CACHE_VERSION` | 78 | 78 | KHÔNG đổi |
| pool | `36c2153e…` | `36c2153e…` | KHÔNG đổi |
| `V3_SEAL.json` | `490300a4…` | `490300a4…` | KHÔNG đổi |
| seed · `da_rut` | `null` · `null` | `null` · `null` | KHÔNG đổi |

```
MEASUREMENT_TOOLING_CHANGED    YES
RUNNER_HASH_CHANGED            NO    ← đề bài kỳ vọng YES; xem ghi chú
CERTIFIER_HASH_CHANGED         YES
SCORER_HASH_CHANGED            NO
CANDIDATE_HASH_CHANGED         NO
CACHE_VERSION_CHANGED          NO
MODEL_FACING_CONTRACT_CHANGED  NO
POOL_HASH_CHANGED              NO
SEAL_CHANGED                   NO
SEED_ASSIGNED                  NO
CASES_DRAWN                    NO
PRODUCT_CAPABILITY_CHANGED     NO
```

⚠️ **`RUNNER_HASH_CHANGED = NO`, trong khi đề bài kỳ vọng `YES`.** Báo số đo
được, không báo số được kỳ vọng. `run_curved_acceptance.py` **không bị sửa một
byte nào**: thứ đổi là `acceptance_integrity.py` (nơi sở hữu `RunManifest` mà
runner import) và certifier. Hệ quả vận hành đáng nêu: **`runner_hash` một mình
không đại diện được cho danh tính bộ đo** — hành vi của runner đổi mà băm của
nó không đổi. Đó chính là lý do wave này ghim thêm bốn băm nữa, và
`RUNNER_HASH_CHANGED = NO` là bằng chứng cho sự cần thiết ấy chứ không phải một
thiếu sót.

## 10. TEST_RESULTS

| cổng | lệnh | kết quả |
|---|---|---|
| chính sách + rubric + manifest + tiêm lỗi | `pytest tests/test_v3_threshold_and_run_identity.py -q` | **46 passed** |
| runner integrity | `pytest tests/test_acceptance_runner_integrity.py -q` | **PASS** |
| scorer expressiveness | `pytest tests/test_scorer_expressiveness_class.py -q` | **PASS** |
| cache + current-state + runtime identity | `pytest tests/test_cache_identity.py tests/test_current_state_identity.py tests/test_runtime_identity.py -q` | **PASS** |
| chứng nhận bộ đo | `python scripts/certify_acceptance_runner.py` | **PASS**, exit 0, 0 lượt gọi |
| candidate | `python scripts/freeze_evaluation_candidate.py --verify` | **exit 0**, khớp seal |
| pool + chính sách trỏ đúng hệ | trong certifier (`kiem_chinh_sach`) | **PASS** |
| toàn bộ backend | `pytest -q` | **3477 passed**, 1 skip, 1 deselect |
| khoảng trắng | `git diff --check` | sạch |

Frontend **không** chạy lại: candidate `a696200e…` không đổi và không file nào
dưới `frontend/` bị đụng — đối chiếu bằng candidate hash đúng như §I cho phép.

Trên cây **bẩn**, `tests/geometry/test_holdout_readiness_7b.py::
test_bao_cao_da_sinh_va_KHONG_TROI` đỏ: nó khẳng định báo cáo Phase 7B nói
`READY_FOR_PHASE7B: NO` **khi và chỉ khi** có blocker, và "cây làm việc bẩn" tự
nó là một blocker. Đây là hành vi **đúng** của guard, không phải hồi quy — nó
xanh lại sau commit (số trong bảng trên là bản đã commit).

## 11. LIMITATIONS

1. **Model chưa ghim được, và không ghim được từ trong wave này** (§6). Đây là
   giới hạn duy nhất chặn `READY = YES`.
2. **`policy_loader_hash` bảo vệ phép băm, không bảo vệ người ghi chính sách.**
   Ai sửa JSON *trước* khi mở lượt đo vẫn có một chính sách hợp lệ — cái chặn
   việc đó là `created_before_live_run` + commit history, không phải băm.
3. **`scorer_hash` băm bytes thô.** Kho không có `.gitattributes`, nên
   checkout trên máy đổi CRLF sẽ cho băm khác **cùng một nội dung**. Băm chính
   sách miễn nhiễm (băm object đã parse); băm file thì không. Lượt live nên
   chạy trên cùng một checkout.
4. **Certifier chỉ chứng minh ĐƯỜNG ĐI của drift-check chạy được**, không bắt
   được trôi trong chính lượt của nó — vì nó tạo manifest và tính lại trong
   cùng một tiến trình. Việc bắt trôi thật thuộc về lượt live, khi manifest đã
   ghi từ trước. `test_F2b` chứng minh phép so đó đỏ được.
5. **Ngưỡng chưa được chấm thử trên dữ liệu thật** — theo thiết kế. Chấm thử
   là biết kết quả, và biết kết quả là mất quyền khoá trước.
6. **`sample_design` tin vào aggregate chỉ-đếm của con dấu.** Nếu cấu trúc mẫu
   thật khác giả định, family verdict là `INSUFFICIENT_SAMPLE` — chính sách
   chọn dừng thay vì tự hạ mẫu số.

## 12. LIVE_HANDOFF

Còn đúng **một** việc trước lượt live, và nó **không phải việc kỹ thuật**:

> Người hướng dẫn ghi giá trị cho `limited_reproducibility_allowed` trong
> `curved_v3_threshold_policy.json` — `true` (chấp nhận `LIMITED`, khai giới
> hạn trong khoá luận) hoặc `false` (đòi snapshot bất biến, kéo theo một trong
> ba đường ở §6).

Ghi xong ⇒ băm chính sách đổi ⇒ **bump `policy_version`** và ghi lại băm mới
vào handoff. Rồi:

1. Đổi evaluator — người/phiên **không** viết `radius_sq_khai`, **không** viết
   `area`/`lateral_area`, **chưa** đọc nội dung V3. Phiên hiện tại đã viết cả
   ba, nên `EVALUATOR_INDEPENDENCE = HANDOFF_REQUIRED` vẫn còn hiệu lực
   (`CURVED_V3_LIVE_ACCEPTANCE_HANDOFF.md §1`).
2. Rút bằng `EXTERNAL_SEED = 5324284654432805119` — **chưa dùng, còn nguyên**.
3. Runner V3 phải gọi `mo_run` với `model` đủ bảy trường; readiness guard đỏ
   nếu thiếu.

⚠️ **`run_curved_acceptance.py` hiện KHÔNG gọi `mo_run`** — nó có `_moi_truong()`
riêng và không ghi `RunManifest`. Việc nối nó vào manifest 1.1 chưa làm trong
wave này (đề bài giới hạn ở policy + pinning + certification), và **phải làm
trước lượt live** — nếu không, mọi thứ wave này ghim sẽ không có mặt trong
artifact của lượt V3.

## 13. RECOMMENDED_NEXT_ACTION

```
READY_FOR_INDEPENDENT_V3_LIVE = CONDITIONAL
RECOMMENDED_NEXT_ACTION       = EXTERNAL_REPRODUCIBILITY_DECISION
```

`CONDITIONAL` chứ không `NO`: mọi guard kỹ thuật đã đạt và tự chứng minh đỏ
được. `CONDITIONAL` chứ không `YES`: provider không cấp snapshot bất biến, và
policy **cố ý** chưa nói `LIMITED` có được chấp nhận hay không.

---

```text
THRESHOLD_POLICY_ID                      CURVED_V3_ACCEPTANCE
THRESHOLD_POLICY_VERSION                 1.0.0
THRESHOLD_POLICY_HASH                    c0a77cd9cd57ca7d…
ATTRIBUTION_RUBRIC_HASH                  d44f2b7c19b4904f…
THRESHOLDS_FIXED_BEFORE_RESULTS          YES

SELECTED_CASES_REQUIRED                  13
POSITIVE_CASES_REQUIRED                  9
NEGATIVE_CASES_REQUIRED                  4
FAMILY_SAMPLE_REQUIRED                   3
FAMILY_EVENTUAL_SERVABLE_THRESHOLD       1.0
ATTRIBUTION_UNRESOLVED_TREATMENT         không phải lỗi model · không phải gap
                                         đã chứng minh · family INCONCLUSIVE_
                                         ATTRIBUTION · chặn promotion · KHÔNG
                                         làm hỏng run
SYSTEM_EXPRESSIVENESS_GAP_TREATMENT      không phải lỗi model · TÍNH lỗi hệ ·
                                         chặn family pass · chặn promotion ·
                                         KHÔNG làm hỏng run

RUN_MANIFEST_SCHEMA_VERSION              1.1
RUNNER_HASH                              11e4b6200f817593…  (KHÔNG đổi)
SCORER_HASH                              4f7cae906500e0b6…  (KHÔNG đổi)
CERTIFIER_HASH                           9f514137d43ef268…  (đổi)
SCORER_HASH_PINNED                       YES
THRESHOLD_HASH_PINNED                    YES
RUBRIC_HASH_PINNED                       YES

MODEL_PROVIDER                           gemini
MODEL_NAME                               gemini-2.5-flash   (alias trôi)
MODEL_VERSION_OR_SNAPSHOT                null
MODEL_IDENTITY_REPRODUCIBILITY           LIMITED
TEMPERATURE                              0.2
TOP_P                                    null   (KHÔNG gửi tới provider)
MAX_OUTPUT_TOKENS                        null   (KHÔNG gửi tới provider)
REPAIR_LIMIT                             3
APPLICATION_CALL_BUDGET                  chưa đặt — lượt live khai trước khi rút

CANDIDATE_HASH_BEFORE                    a696200e8f8c668c…
CANDIDATE_HASH_AFTER                     a696200e8f8c668c…
CACHE_VERSION_BEFORE                     78
CACHE_VERSION_AFTER                      78
POOL_HASH_BEFORE                         36c2153ecefd2dbf…
POOL_HASH_AFTER                          36c2153ecefd2dbf…
SEAL_CHANGED                             NO
V3_SEED                                  null
V3_DA_RUT                                null

APPLICATION_LLM_CALLS                    0
CASES_DRAWN                              NO
LIVE_V3_EXECUTED                         NO
PRODUCT_CAPABILITY_CHANGED               NO   (ball · cylinder · cone vẫn
                                              foundation_only)
RUNNER_CERTIFICATION                     PASS
WORKING_TREE                             CLEAN
COMMITS                                  1
```
