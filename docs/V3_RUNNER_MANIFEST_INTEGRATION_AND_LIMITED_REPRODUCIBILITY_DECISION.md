# V3_RUNNER_MANIFEST_INTEGRATION_AND_LIMITED_REPRODUCIBILITY_DECISION

> Wave 2026-09-05. **0 lượt gọi model.** Không rút ca, không chạy live, không
> reseal. Chỉ sửa bộ đo, chính sách, test và tài liệu — tất cả **ngoài**
> `MEASURED_SYSTEM_PATHS`.
>
> Nội dung `de`, `mong`, tham số và đáp số của V3 **vẫn chưa đọc**.
> `EXTERNAL_SEED = 5324284654432805119` **vẫn chưa dùng**.

## 1. EXTERNAL_REPRODUCIBILITY_DECISION

```
LIMITED_REPRODUCIBILITY_ALLOWED = true      ← quyết định của người hướng dẫn
```

Ghi vào `curved_v3_threshold_policy.json`, bump `1.0.0 → 1.1.0`, băm lại. Khoá
**trước** mọi kết quả V3 — và tính "trước" ấy là thứ duy nhất làm quyết định
này có giá trị, nên nó được khai thành trường kiểm được (`decided_before_live_
run`, `decided_by`) chứ không chỉ nằm trong văn xuôi.

**Quyết định này không biến alias thành snapshot.** Nó cho phép một lượt đo
được **ghi nhận trung thực kèm giới hạn đã khai trước**. Chính sách nói thẳng
ba điều bị cấm (`limited_forbids`):

1. hiển thị alias thành `PINNED`;
2. tuyên bố tái lập bit-for-bit;
3. điền một con số giả cho tham số **không** được gửi.

Đổi lại, `limited_requires_recorded` liệt 11 thứ **phải** có trong manifest —
provider, alias chính xác, UTC start/end, SDK + version, endpoint class, tham
số thực sự gửi, tham số không gửi ở trạng thái typed, metadata provider trả về
(nếu SDK đưa ra), raw response metadata, raw candidate mọi attempt, mọi attempt.

Verdict mới `LIMITED_ACCEPTED` **không phải** `PINNED` đổi tên: danh sách
"thiếu" vẫn khai alias là alias. Chấp nhận một giới hạn không xoá được giới hạn
ấy — `test_F2g` neo đúng điều đó (danh sách giới hạn rỗng ⇒ đỏ), và
`test_F2h` chứng minh cổng **đóng lại được** (đặt `false` ⇒ alias trở lại thành
chặn; đặt `null` ⇒ quay về `CONDITIONAL`).

## 2. ROOT_CAUSE

Phân biệt ba câu, và trước wave này câu thứ ba là **sai** trong khi hai câu đầu
đều đúng:

1. **Thẩm quyền toàn vẹn đã tồn tại** — `RunManifest` 1.1, bốn băm bộ đo,
   `kiem_ghim_bo_do`, guard danh tính model. Wave trước dựng xong.
2. **Runner V3 không dùng thẩm quyền đó.** `run_curved_acceptance.py` có
   `_moi_truong()` riêng, ghi artifact bằng `write_text` thẳng, và **không gọi
   `mo_run` một lần nào**.
3. ⇒ **Một guard không nằm trên đường chạy thật thì không bảo vệ gì cả.** Nó
   chỉ làm người đọc yên tâm — mà đó là tác dụng ngược của một cổng.

Chứng minh bằng máy, không bằng lời (§A, đo trước khi sửa):

```
pytest tests/test_v3_runner_manifest_integration.py -q
31 failed, 3 passed
```

Ba cái xanh sẵn là **control**: ngưỡng số học chưa trôi, LIMITED-off vẫn chặn,
call graph pipeline đúng hình. Chúng xanh vì chúng khẳng định thứ đã đúng —
nếu chúng cũng đỏ thì bộ test đang đo sai chỗ.

⚠️ Và một hệ quả dễ bỏ qua: **`RUNNER_CERTIFICATION = PASS` xanh suốt quãng
đó.** Certifier chạy bài kiểm tổng hợp **của chính nó**, nên nó không bao giờ
chạm runner V3 thật. "Chứng nhận PASS" và "runner V3 đã lắp" là hai câu.

## 3. POLICY_VERSION_DELTA

```
THRESHOLD_POLICY_VERSION   1.0.0 → 1.1.0
THRESHOLD_POLICY_HASH      c0a77cd9cd57ca7d… → 460e0ce57a304872…
ATTRIBUTION_RUBRIC_HASH    d44f2b7c19b4904f…   (KHÔNG đổi)
```

Semantic diff canonical — **chỉ** trong `model_identity_policy`:

| khoá | trước | sau |
|---|---|---|
| `limited_reproducibility_allowed` | `null` | `true` |
| `accepted_verdict` | — | `"LIMITED_ACCEPTED"` |
| `decided_by` · `decided_before_live_run` | — | người hướng dẫn · `true` |
| `limited_forbids` | — | 3 mục |
| `limited_requires_recorded` | — | 11 mục |
| `decoding_parameter_modes` | — | 3 chế độ |

Mọi ngưỡng **số học** giữ nguyên byte-nghĩa — 13 ca · 9 dương · 4 âm · 3 ca/
family · eventual 1.0 · exact 1.0 · Scene3D 1.0 · refusal 4/4 · boundary 4/4 ·
R0 laundering 0 · gap và unresolved đều chặn promotion. `test_B2` khoá từng con
số một; bump version mà ngưỡng trôi theo thì bump đã thành cái cớ.

## 4. DECODING_PARAMETER_CONTRACT

`ARTIFACT_SCHEMA_VERSION` **1.1 → 1.2**. Ba trường phẳng
`temperature`/`top_p`/`max_output_tokens` thành **một khối có kiểu**:

```json
{"temperature":      {"mode": "explicit",   "value": 0.2},
 "top_p":            {"mode": "not_sent",   "value": null},
 "max_output_tokens":{"mode": "not_sent",   "value": null}}
```

**Vì sao ba trạng thái chứ không hai.** 1.1 chỉ có "có số" và `None`, và `None`
gộp hai chuyện khác hẳn nhau: *"không gửi"* với *"provider có mặc định mà ta
không quan sát được"*. Cái đầu ta biết hết; cái sau ta chỉ biết là mình không
biết. Một phép đo phải nói được sự khác nhau ấy.

Luật, mỗi luật chặn đúng một cách nói dối:

| luật | chặn |
|---|---|
| `explicit` phải kèm **số** | `bool` không tính — `True` là `int` trong Python |
| `not_sent` phải kèm `value = null` | điền số cho tham số không gửi = bịa lại lịch sử request |
| `provider_default_unobserved` chỉ hợp lệ trong LIMITED | ngoài LIMITED, "provider có mặc định nào đó" là câu chưa đo được |
| chuỗi văn xuôi không thay được giá trị có kiểu | `{"mode": …}` là chỗ tiếp theo văn xuôi sẽ lẻn vào |

Đọc từ `call_gemini`: `generationConfig` chỉ mang `temperature` (mặc định 0.2);
`top_p` và `max_output_tokens` **không có mặt** trong payload — nên chúng là
`not_sent`, không phải "null".

Version dispatch **rõ ràng**: `PHIEN_BAN_DOC_DUOC = ("1.0","1.1","1.2")`.
Artifact 1.0/1.1 vẫn đọc được nguyên vẹn và được **miễn** phép kiểm đủ-trường
của 1.2; `kiem_danh_tinh_model` giữ nhánh phẳng cho manifest 1.1. Historical
artifacts không đổi một byte.

## 5. APPLICATION_CALL_BUDGET

```
APPLICATION_CALL_BUDGET          78
APPLICATION_CALL_BUDGET_FORMULA  8A: 13 × (1 + 1×1) = 26
                                 8B: 13 × (1 + 3×1) = 52   (worst case: MỌI ca
                                                            repair-eligible)
                                 tổng                  78
```

`derive_application_call_budget(selected_cases, analyze_calls_per_case,
synthesis_attempt_limit, calls_per_attempt)` = `n × (a + s×c)`.

Dẫn từ **call graph**, không từ số đã dùng ở V1/V2 — một trần suy từ lượt trước
là một trần **đã biết kết quả**: nó vừa khít với thứ đã xảy ra thay vì với thứ
có thể xảy ra. `test_D4` đọc `app/ai/pipeline.py` bằng AST và khoá: đúng **hai**
chỗ gọi provider trên đường hình học (`stage_semantic_analyze` 1 lượt ·
`stage_semantic_program` 1 lượt/attempt), `MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3`.
Thêm một chỗ gọi thứ ba trong `app/` sẽ làm test đỏ, chứ không lặng lẽ làm trần
hụt.

⚠️ **Trần cũ vừa không dẫn xuất vừa HỤT.** Runner ghi
`max_logical_calls = 3n + 5` — một con số có `+5` mà không giải thích được `5`
từ đâu. Với n = 13 nó cho 44, **thấp hơn** worst case thật (78): lượt đo sẽ
`BudgetExceeded` giữa chừng và người đọc sau sẽ tưởng mô hình hỏng, trong khi
thứ hỏng là cái phanh.

## 6. V3_RUNNER_INTEGRATION

`_moi_truong()` nay là **wrapper mỏng** gọi `acceptance_integrity.
moi_truong_hien_tai()`, chỉ thêm đúng thứ runner sở hữu (`case_set_hash`). Bảng
thứ hai luôn trôi khỏi bản gốc, và cái trôi sẽ là cái không ai nhìn.

`mo_luot_do_v3()` — mười bước, **đúng thứ tự**, tất cả trước lượt gọi đầu tiên:

```
① bộ ca có phải pool V3     ⑥ đọc LẠI manifest TỪ ĐĨA
② con dấu + candidate khớp   ⑦ kiem_ghim_bo_do (4 băm)
③ thư mục MỚI               ⑧ guard danh tính model
④ mo_run                    ⑨ trần lượt gọi
⑤ ghi manifest nguyên khối   ⑩ …rồi mới được gọi provider
```

Thứ tự không tuỳ tiện: manifest phải nằm trên đĩa **trước** lượt gọi đầu, nếu
không nó là ảnh chụp của một hệ đã bị lượt gọi ấy chạm vào. Và phải **đọc lại
từ đĩa** rồi mới kiểm — kiểm bản trong bộ nhớ là kiểm thứ vừa tự tính ra.

**Nguồn bộ ca.** `nap_ca_v3()` đọc đúng những ca con dấu đã rút, kiểm `pool_
hash` **và** `case_set_hash`. Chưa rút ⇒ NÉM (`seed` còn `null` nên hôm nay nó
dừng ngay dòng đầu — đúng như phải thế). `kiem_bo_ca_la_pool_v3()` từ chối
corpus V1/V2 theo **id**: `CA` là 9 đề tôi tự viết, đã chạy, artifact đã công
bố — chấm trên nó không phải phép đo held-out, và nó sẽ hỏng theo chiều **luôn
đẹp lên**.

## 7. PER_CALL_IDENTITY_GUARDS

`canh_gac_truoc_luot_goi(thu_muc, con_lai=…)` chạy trước **mỗi** analyze, tổng
hợp và sửa. Kiểm: đủ trường 1.2 · bốn băm bộ đo · tham số giải mã typed · trần
dẫn xuất khớp · trần còn lại > 0 · môi trường/capability · manifest tồn tại.

Đọc lại manifest **mỗi lượt**, không cache: thứ đang canh là *file trên đĩa đổi
giữa hai lượt gọi*, nên đọc một lần rồi giữ trong bộ nhớ là bỏ đúng thứ cần canh.

**Không tự cập nhật manifest cho khớp file mới.** Manifest là ảnh chụp trước
kết quả; sửa nó cho khớp hiện tại là xoá đúng bằng chứng của việc trôi. Trôi ⇒
ghi `integrity_stop.json` rồi NÉM; artifact đã ghi giữ nguyên, và lần dừng
**đầu** là lần được giữ (lần sau không đè lên).

## 8. MODEL_RESPONSE_METADATA

```
RESPONSE_MODEL_VERSION = UNAVAILABLE_TO_RUNNER
MODEL_IDENTITY_REPRODUCIBILITY = LIMITED_ACCEPTED
```

Đọc từ mã, không đoán: `call_gemini` trả về **đúng một chuỗi text**.
`body["modelVersion"]`, `finishReason`, request-id đều bị bỏ ngay tại chỗ parse
— caller không có đường nào chạm tới. Ghi thành **hằng số có tên** thay vì để
trống, vì "không có" và "chưa điền" đọc giống nhau trong artifact mà nghĩa thì
khác hẳn.

Cái **có** thì ghi đủ: provider · alias · SDK (`httpx` + version — kho gọi REST
thẳng, không qua SDK google-genai) · endpoint class · `transport_retry_policy`
đọc từ `MAX_ATTEMPTS`/`BACKOFF_BASE_SECONDS`/`TRANSIENT_STATUS`. Usage metadata
đã có sẵn qua `telemetry.usage_report()`.

Sửa `app/ai/gemini.py` để phơi `modelVersion` **ngoài phạm vi wave này** —
`app/` nằm trong `MEASURED_SYSTEM_PATHS`, đụng vào là phá đóng băng candidate
và buộc reseal V3. Đây là **giới hạn của instrumentation trên hệ được đo**,
không phải chỗ để điền dữ liệu suy đoán.

Không log credential: `quet_bi_mat()` quét artifact tìm khoá dạng Google API
key và cặp `api_key/authorization/bearer`. Chưa từng rò — và cách giữ nguyên
như thế là **có một guard**, không phải có một thói quen.

## 9. ATTRIBUTION_ARTIFACT_PATH

`ghi_bang_chung_quy_trach_nhiem(thu_muc, bc)` → `<run>/attribution/<case>.json`.
Wave này chỉ **lắp đường**; chưa rút nên chưa có ca nào để phán.

Từ chối bằng chứng thiếu bất kỳ trường nào trong 9 trường rubric đòi, cộng
`evaluator`. Ghi thêm `rubric_hash` vào **chính** artifact: bằng chứng phải mang
theo bản rubric đã dùng, không trỏ suông sang "rubric hiện hành" — rubric hiện
hành sẽ đổi. Sửa ⇒ **version mới** (`.v2.json`), bản đầu giữ nguyên.

Thiếu bằng chứng trong tình huống cần attribution ⇒ `ATTRIBUTION_UNRESOLVED`
(rubric §C3, đã khoá từ wave trước).

## 10. CERTIFIER_PROOF

`chung_nhan_runner_v3()` — 12 phép kiểm chạm **runner V3 thật**, provider giả,
0 lượt gọi:

| # | kiểm | # | kiểm |
|---|---|---|---|
| ① | manifest có TRƯỚC lượt giả đầu | ⑦ | `top_p`/`max_output_tokens` = `NOT_SENT` |
| ② | `artifact_schema_version` = 1.2 | ⑧ | trần ghi trước lượt đầu |
| ③ | bốn băm bộ đo đúng | ⑨ | mọi lượt giả đi qua cổng và được đếm |
| ④ | policy version 1.1.0 + băm đúng | ⑩ | trôi trước lượt hai ⇒ guard ĐỎ |
| ⑤ | LIMITED ghi đúng, **không** gọi là PINNED | ⑪ | tóm tắt dẫn từ đĩa |
| ⑥ | `temperature` ở trạng thái `explicit` | ⑫ | thư mục cũ bị từ chối |

```
RUNNER_CERTIFICATION   PASS
V3_RUNNER_INTEGRATION  PASS
APPLICATION_LLM_CALLS  0
  runner V3         mo_run ✓ · 3 lượt giả · trần 12
```

## 11. FAULT_INJECTION

Mọi injection **đỏ trước, xanh sau**.

| §J | tiêm | guard | test |
|---|---|---|---|
| 1 | runner bỏ gọi `mo_run` | certification ĐỎ | `test_J1` |
| 2 | manifest ghi sau lượt gọi đầu | `canh_gac` NÉM | `test_J2` |
| 3–6 | scorer · threshold · rubric · loader đổi giữa hai lượt | `kiem_ghim_bo_do` | `test_J3456` (4 ca) |
| 7 | alias ghi thành `PINNED` | certification ĐỎ | `test_J7` |
| 8 | `NOT_SENT` thay bằng "provider default" | type guard | `test_J8` |
| 9 | `temperature = True` | type guard | `test_J9` |
| 10 | hết trần | dừng đúng chỗ | `test_J10` |
| 11 | tăng quota sau khi mở run | trần lệch dẫn xuất | `test_J11` |
| 12 | bằng chứng thiếu `reason`/`authority_hashes` | lược đồ rubric | `test_H2` |
| 13 | artifact mang credential | `quet_bi_mat` | `test_J13` |
| 14 | corpus phát triển thay pool V3 | `kiem_bo_ca_la_pool_v3` | `test_E2` |

Khôi phục bản chuẩn ⇒ `test_I_chung_nhan_runner_v3_XANH_khi_khoi_phuc` xanh.
Nếu bản chuẩn không xanh lại thì cái đỏ ở trên không chứng minh được gì.

**Một lỗi thật do §J1 lôi ra**, không có trong đề bài: khi manifest vắng mặt,
`chung_nhan_runner_v3` **ném `FileNotFoundError`** thay vì báo FAIL. Một bài
chứng nhận ném stack trace đọc như lỗi hạ tầng, và lỗi hạ tầng thì người ta
chạy lại chứ không đọc. Đã sửa thành dừng sạch kèm câu nói rõ nguyên nhân.

## 12. MEASUREMENT_IDENTITY_DELTA

Đo bằng `git stash` (trước) và tính lại (sau), không suy từ diff.

| | trước | sau | |
|---|---|---|---|
| `run_curved_acceptance.py` | `11e4b620…` | `55be22b6…` | **ĐỔI** |
| `acceptance_integrity.py` | `ae42adce…` | `7b5e3ed1…` | ĐỔI |
| `certify_acceptance_runner.py` | `9f514137…` | `81799613…` | ĐỔI |
| `measurement_policy.py` | `379b9a14…` | `b51e936f…` | ĐỔI |
| threshold policy | `c0a77cd9…` v1.0.0 | `460e0ce5…` v1.1.0 | ĐỔI |
| `acceptance_verdict.py` (scorer) | `4f7cae90…` | `4f7cae90…` | KHÔNG đổi |
| attribution rubric | `d44f2b7c…` | `d44f2b7c…` | KHÔNG đổi |
| `ARTIFACT_SCHEMA_VERSION` | 1.1 | **1.2** | ĐỔI |
| candidate | `a696200e…` (89 file) | `a696200e…` | KHÔNG đổi · verify exit 0 |
| `CACHE_VERSION` | 78 | 78 | KHÔNG đổi |
| pool | `36c2153e…` | `36c2153e…` | KHÔNG đổi |
| `V3_SEAL.json` | `490300a4…` | `490300a4…` | KHÔNG đổi |
| seed · `da_rut` | `null` · `null` | `null` · `null` | KHÔNG đổi |

```
V3_RUNNER_HASH_CHANGED          YES
MEASUREMENT_TOOLING_CHANGED     YES
THRESHOLD_POLICY_HASH_CHANGED   YES
POLICY_VERSION_CHANGED          YES
SCORER_HASH_CHANGED             NO
ATTRIBUTION_RUBRIC_CHANGED      NO
CANDIDATE_HASH_CHANGED          NO
CACHE_VERSION_CHANGED           NO
MODEL_FACING_CONTRACT_CHANGED   NO
POOL_HASH_CHANGED               NO
SEAL_CHANGED                    NO
SEED_ASSIGNED                   NO
CASES_DRAWN                     NO
PRODUCT_CAPABILITY_CHANGED      NO
```

Mọi kỳ vọng §K khớp. Bộ đo nằm ngoài `MEASURED_SYSTEM_PATHS` nên candidate
`a696200e…` vẫn được con dấu hiện hành đo — **không reseal**.

## 13. TEST_RESULTS

| cổng | lệnh | kết quả |
|---|---|---|
| tái hiện khoảng hở (TRƯỚC khi sửa) | `pytest tests/test_v3_runner_manifest_integration.py -q` | **31 failed, 3 passed** |
| lắp runner + ngân sách + tiêm lỗi (SAU) | như trên | **39 passed** |
| ngưỡng + danh tính lượt đo | `pytest tests/test_v3_threshold_and_run_identity.py -q` | **48 passed** |
| runner integrity | `pytest tests/test_acceptance_runner_integrity.py -q` | **PASS** |
| scorer expressiveness | `pytest tests/test_scorer_expressiveness_class.py -q` | **PASS** |
| chứng nhận bộ đo + runner V3 | `python scripts/certify_acceptance_runner.py` | **PASS / PASS**, exit 0, 0 lượt gọi |
| candidate | `python scripts/freeze_evaluation_candidate.py --verify` | **exit 0**, 89 file |
| cache + current-state + runtime identity | `pytest tests/test_cache_identity.py tests/test_current_state_identity.py tests/test_runtime_identity.py -q` | **PASS** |
| toàn bộ backend (cây sạch) | `pytest -q` | **3513 passed**, 1 skip, 1 deselect |
| khoảng trắng | `git diff --check` | sạch |

Frontend **không** chạy lại: candidate `a696200e…` không đổi và không file nào
dưới `frontend/` bị đụng — đối chiếu bằng candidate hash đúng như §L cho phép.

## 14. LIMITATIONS

1. **Model vẫn là alias.** `LIMITED_ACCEPTED` là ghi nhận trung thực, không
   phải ghim. Không tuyên bố tái lập bit-for-bit; lượt sau có thể gặp một
   snapshot khác dưới cùng cái tên `gemini-2.5-flash`.
2. **`modelVersion` từ response không tới được runner** — `call_gemini` bỏ nó
   tại chỗ parse. Sửa được, nhưng phải đụng `app/` ⇒ reseal.
3. **`scorer_hash` băm bytes thô.** Kho không có `.gitattributes`; checkout
   trên máy đổi CRLF cho băm khác **cùng một nội dung**. Băm chính sách miễn
   nhiễm (băm object đã parse); băm file thì không. Lượt live nên chạy trên
   cùng một checkout.
4. **Đường V3 chưa chạy end-to-end với ca thật** — không thể, vì `da_rut` còn
   `null`. `nap_ca_v3()` được kiểm ở nhánh **từ chối**; nhánh chấp nhận sẽ chỉ
   chạy lần đầu trong lượt live. Đây là hệ quả trực tiếp của việc giữ pool
   chưa đọc, và tôi chọn giữ pool.
5. **`chung_nhan_runner_v3` dùng ca tổng hợp** (`CERT1`, `CERT2`), không phải
   ca V3. Nó chứng minh **thứ tự và cổng**, không chứng minh nội dung.
6. **`tran_luot_goi_v3` giả định runner giữ hình dạng 8A/8B.** Đổi số chặng mà
   quên sửa trần thì trần lại hụt — `test_D2` khoá đúng công thức hai chặng,
   nhưng nó không tự biết runner đã đổi hình.

## 15. INDEPENDENT_EVALUATOR_HANDOFF

Còn đúng **một** điều kiện, và nó **không phải kỹ thuật**: đổi người.

Phiên hiện tại **không** đạt độc lập — đã viết `radius_sq_khai`,
`area`/`lateral_area`, scorer và runner. Điều đó không sửa được bằng code.

Lượt live phải chạy trong **phiên evaluator mới**, chưa từng triển khai
`radius_sq_khai` · `area` · `lateral_area` · scorer · runner, và **chưa đọc nội
dung V3**. Trình tự:

```bash
cd backend
# ① rút — MỘT LẦN DUY NHẤT, seed từ người ngoài
.venv/Scripts/python.exe scripts/seal_curved_v3.py --rut --seed 5324284654432805119
# ② xác minh bộ đo trước khi tiêu quota (0 lượt gọi)
.venv/Scripts/python.exe scripts/certify_acceptance_runner.py
.venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
# ③ lượt live — TIÊU QUOTA THẬT, trần 78 lượt logic
ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
  .venv/Scripts/python.exe scripts/run_curved_acceptance.py --out-dir <thư mục MỚI>
```

`_rut` **từ chối lần hai** — rút sai người sẽ tiêu vĩnh viễn một pool held-out.

Ghi vào phần **giới hạn phương pháp** của khoá luận: model gọi bằng alias
`gemini-2.5-flash`; tái lập ở mức `LIMITED`; alias, thời điểm UTC, SDK, tham số
gửi và toàn bộ raw output được lưu đủ; **không** tuyên bố tái lập bit-for-bit.

## 16. RECOMMENDED_NEXT_ACTION

```
READY_FOR_INDEPENDENT_V3_LIVE = YES
RECOMMENDED_NEXT_ACTION       = INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE
```

---

```text
LIMITED_REPRODUCIBILITY_ALLOWED          true
MODEL_IDENTITY_REPRODUCIBILITY           LIMITED_ACCEPTED
MODEL_PROVIDER                           gemini
MODEL_NAME                               gemini-2.5-flash   (alias)
MODEL_VERSION_OR_SNAPSHOT                null
RESPONSE_MODEL_VERSION_POLICY            UNAVAILABLE_TO_RUNNER — `call_gemini`
                                         chỉ trả text; sửa được nhưng phải
                                         đụng `app/` ⇒ reseal

TEMPERATURE_MODE                         explicit
TEMPERATURE_VALUE                        0.2
TOP_P_MODE                               not_sent
TOP_P_VALUE                              null
MAX_OUTPUT_TOKENS_MODE                   not_sent
MAX_OUTPUT_TOKENS_VALUE                  null
REPAIR_LIMIT                             3
APPLICATION_CALL_BUDGET                  78
APPLICATION_CALL_BUDGET_FORMULA          8A 13×(1+1×1)=26 · 8B 13×(1+3×1)=52

ARTIFACT_SCHEMA_VERSION_BEFORE           1.1
ARTIFACT_SCHEMA_VERSION_AFTER            1.2
THRESHOLD_POLICY_VERSION_BEFORE          1.0.0
THRESHOLD_POLICY_VERSION_AFTER           1.1.0
THRESHOLD_POLICY_HASH_BEFORE             c0a77cd9cd57ca7d…
THRESHOLD_POLICY_HASH_AFTER              460e0ce57a304872…
ATTRIBUTION_RUBRIC_HASH                  d44f2b7c19b4904f…  (KHÔNG đổi)
POLICY_LOADER_HASH                       b51e936f809bd314…

V3_RUNNER_CALLS_MO_RUN                   YES
MANIFEST_WRITTEN_BEFORE_FIRST_CALL       YES
PER_CALL_IDENTITY_GUARD                  YES  (analyze · tổng hợp · sửa)
SCORER_HASH_PINNED                       YES
THRESHOLD_HASH_PINNED                    YES
RUBRIC_HASH_PINNED                       YES
LOADER_HASH_PINNED                       YES
MODEL_CONFIGURATION_TYPED                YES  (explicit · not_sent ·
                                              provider_default_unobserved)
ATTRIBUTION_EVIDENCE_SUPPORTED           YES  (đường lưu lắp xong, chưa dùng)

V3_RUNNER_HASH_BEFORE                    11e4b6200f817593…
V3_RUNNER_HASH_AFTER                     55be22b6ddd52992…
SCORER_HASH_BEFORE                       4f7cae906500e0b6…
SCORER_HASH_AFTER                        4f7cae906500e0b6…
CERTIFIER_HASH_BEFORE                    9f514137d43ef268…
CERTIFIER_HASH_AFTER                     81799613f8c01f2d…

CANDIDATE_HASH_BEFORE                    a696200e8f8c668c…
CANDIDATE_HASH_AFTER                     a696200e8f8c668c…
CACHE_VERSION_BEFORE                     78
CACHE_VERSION_AFTER                      78
POOL_HASH_BEFORE                         36c2153ecefd2dbf…
POOL_HASH_AFTER                          36c2153ecefd2dbf…
SEAL_CHANGED                             NO
V3_SEED                                  null   (EXTERNAL_SEED chưa dùng)
V3_DA_RUT                                null

APPLICATION_LLM_CALLS                    0
CASES_DRAWN                              NO
LIVE_V3_EXECUTED                         NO
RUNNER_CERTIFICATION                     PASS  (+ V3_RUNNER_INTEGRATION PASS)
READY_FOR_INDEPENDENT_V3_LIVE            YES
PRODUCT_CAPABILITY_CHANGED               NO   (ball · cylinder · cone vẫn
                                              foundation_only)
WORKING_TREE                             CLEAN
COMMITS                                  1
```
