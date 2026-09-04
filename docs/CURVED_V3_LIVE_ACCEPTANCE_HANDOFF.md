# CURVED_V3_LIVE_ACCEPTANCE — HANDOFF (lượt đo KHÔNG chạy)

> 2026-09-04. **`APPLICATION_LLM_CALLS = 0`** · `CASES_DRAWN = NO` ·
> `seed` vẫn `null` · pool **chưa bị đọc nội dung**.
>
> ⚠️ **CẬP NHẬT 2026-09-05 — CẢ BA blocker của §2 ĐÃ ĐÓNG, và quyết định học
> thuật đã có.** ② đóng bởi `ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS`; ③ đóng
> bởi `V3_THRESHOLD_AND_RUN_IDENTITY_POLICY`; runner + quyết định `LIMITED`
> đóng bởi **`V3_RUNNER_MANIFEST_INTEGRATION_AND_LIMITED_REPRODUCIBILITY_DECISION`**
> (`docs/V3_RUNNER_MANIFEST_INTEGRATION_AND_LIMITED_REPRODUCIBILITY_DECISION.md`).
>
> ```
> READY_FOR_INDEPENDENT_V3_LIVE = YES        ← ĐÃ BỊ BÁC BỎ, xem §0b
> RECOMMENDED_NEXT_ACTION       = INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE
> ```
>
> ⛔ **HAI DÒNG TRÊN TỪNG SAI — đo bằng máy 2026-09-05, xem §0b.** Một phiên
> evaluator **độc lập** đã đo lại phần cơ học và tìm ra hai blocker ở **đường
> chạy live thật**: `main_async` chạy corpus phát triển V1/V2 chứ không phải
> pool V3 đã rút, không ghi `manifest.json`, không qua identity guard; và
> `mong` của pool là `list` trong khi runner đòi `set`.
>
> ✅ **CẢ HAI ĐÃ ĐÓNG** — `V3_LIVE_ENTRYPOINT_WIRING_REPAIR` (2026-09-05,
> `docs/V3_LIVE_ENTRYPOINT_WIRING_REPAIR.md`). `main_async` nay nạp bộ ca từ
> `nap_ca_v3()`, gọi `mo_luot_do_v3` trước lượt gọi đầu, đặt cổng canh ở ranh
> giới `call_gemini` (không phải `_chay_mot` — hàm ấy có tới 4 lượt gọi), và
> mang trần dẫn xuất **78**. Certifier có nhãn mạnh mới
> **`V3_LIVE_ENTRYPOINT_INTEGRATION`** chạy **chính `main_async`**;
> `READY_FOR_INDEPENDENT_V3_LIVE = YES` chỉ phát khi nhãn ấy PASS. Bộ đo đổi
> băm (runner `55be22b6…` → `6570b57b…`, certifier `81799613…` → `070189b5…`);
> candidate · pool · seal · `CACHE_VERSION` **không đổi**, seed vẫn `null`.
>
> Trạng thái hiện hành:
> `READY_FOR_INDEPENDENT_V3_LIVE = YES` ·
> `RECOMMENDED_NEXT_ACTION = INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE`.
> Bản ghi blocker: `docs/V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER.md`.
>
> Còn đúng **①** — và nó **không sửa được bằng code**: lượt live phải chạy
> trong một **phiên evaluator mới**, chưa từng triển khai `radius_sq_khai` ·
> `area`/`lateral_area` · scorer · runner, và chưa đọc nội dung V3. Trình tự
> ba bước: `…_LIMITED_REPRODUCIBILITY_DECISION.md` §15 — **nhưng chỉ chạy được
> sau khi §0b đóng.** (Điều kiện ① tự nó đã đạt ở lượt 0b; cái chặn nay là bộ
> đo, không phải người đo.)
>
> Mục §3 và §5 dưới đây giữ nguyên làm bằng chứng của lượt 2026-09-04; đọc
> chúng như lịch sử, không như trạng thái hiện tại.
>
> Tên file có hậu tố `_HANDOFF` **có chủ đích**: `CURVED_V3_LIVE_ACCEPTANCE.md`
> là tên dành cho một báo cáo có số đo. Lượt này không có số đo nào; đặt tên ấy
> lên một tài liệu rỗng kết quả là mời người đọc sau tưởng V3 đã chạy.

## 0b. LƯỢT 2026-09-05 (B) — evaluator ĐỘC LẬP **đạt**; runner **chưa nối** vào pool

> Lượt mới nhất. §0 bên dưới là lượt **trước đó** cùng ngày; đọc §0b trước.

Phiên thứ ba nhận uỷ quyền, và là phiên **đầu tiên** vượt được điều kiện độc
lập: không viết `radius_sq_khai`, không viết `area`/`lateral_area`, không viết
scorer, không viết runner, chưa đọc nội dung V3, không kế thừa transcript.

```
EVALUATOR_INDEPENDENCE = CONFIRMED     ← ① của §2 nay ĐÓNG
PRE_DRAW_GUARD         = BLOCKED       ← hai blocker MỚI, ở BỘ ĐO
CASES_DRAWN            = NO
APPLICATION_LLM_CALLS  = 0
V3_SEED                = null          (EXTERNAL_SEED còn nguyên)
```

Phần cơ học của tiền kiểm **đo lại** (không chép bảng §0) và **khớp toàn bộ**:
candidate `a696200e8f8c668c…` 89 file verify exit 0 · pool `36c2153ecefd2dbf…`
26 bài/13 ô (9 dương · 4 âm, mỗi ô đúng 2) · `seed`/`da_rut` `null` ·
runner `55be22b6…` · scorer `4f7cae906500e0b6…` · threshold `460e0ce5…` v1.1.0 ·
rubric `d44f2b7c…` v1.0.0 · loader `b51e936f…` · `CACHE_VERSION` 78 ·
`ARTIFACT_SCHEMA` 1.2 · `LIMITED_ACCEPTED` · trần **78** · pytest **3518 passed**
· `RUNNER_CERTIFICATION` **PASS** · `V3_RUNNER_INTEGRATION` **PASS**.

**Mọi cổng mà đề bài liệt kê đều XANH.** Hai blocker nằm đúng chỗ không cổng nào
nhìn — **đường chạy live thật**:

| | |
|---|---|
| ① `LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL` | `main_async:558` gán `chay = CA` — corpus phát triển V1/V2 (9 đề **đã công bố**, `CA_HASH 8c6a184f…`), không phải pool V3. Call graph `main`+`main_async`+`_chay_mot` **không gọi** `nap_ca_v3`, `mo_luot_do_v3`, `mo_run`, `canh_gac_truoc_luot_goi`, `kiem_bo_ca_la_pool_v3`. Không ghi `manifest.json`. Trần đặt là `3n+5` (n=9 ⇒ 32), không phải 78. |
| ② `POOL_MONG_TYPE_INCOMPATIBLE` | `mong` pool V3 là `list`; `run_curved_acceptance.py:467` làm `c["mong"] <= set(…)` ⇒ `TypeError`, **sau** khi ca đó đã tiêu quota. 18/26 ca dương chạm được dòng này. |

`V3_RUNNER_INTEGRATION PASS` xanh vì certifier gọi **thẳng** `mo_luot_do_v3` với
2 ca tổng hợp của chính nó — nó chưa bao giờ chạy `main_async`. Nhãn ấy chứng
minh **hàm** đúng, không chứng minh **đường chạy thật gọi hàm đó**. Đây đúng là
hình dạng lỗi `…_DECISION.md §2` đã chẩn đoán, tái diễn lên một tầng.

Cả hai nằm trong `backend/scripts/` ⇒ **ngoài `MEASURED_SYSTEM_PATHS`** ⇒ sửa
**không** đụng candidate, **không** cần reseal, seed vẫn dùng được.

Bằng chứng máy: `docs/evaluation/geometry/curved-v3/PREDRAW_GUARD_2026-09-05_INDEPENDENT.json`
(`3ade2a9e891ab3fe…`). Báo cáo + đường sửa 5 bước:
**`docs/V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER.md`**.

```
RECOMMENDED_NEXT_ACTION = V3_LIVE_ENTRYPOINT_WIRING_REPAIR   ← ĐÃ LÀM XONG
```

> ✅ **Đóng cùng ngày** bởi `V3_LIVE_ENTRYPOINT_WIRING_REPAIR`
> (`docs/V3_LIVE_ENTRYPOINT_WIRING_REPAIR.md`): 37 test mới chạy **chính
> `main_async`**, 10 phép tiêm lỗi, certifier có nhãn mạnh
> `V3_LIVE_ENTRYPOINT_INTEGRATION`. Candidate/pool/seal/seed không đụng.
> Khuyến nghị hiện hành: **`INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE`**.

## 0. LƯỢT 2026-09-05 — attestation LẠI hỏng, tiền kiểm đã đo sẵn

Một phiên nữa nhận uỷ quyền rút seed và chạy live. Nó **dừng ở attestation**,
cùng lý do và cùng con người: phiên ấy là phiên đã **viết** bốn thứ V3 sinh ra
để đo. Tự chấm ở đây không phải khiếm khuyết thủ tục — nó phá đúng thứ phép đo
này tồn tại để cung cấp.

```
EVALUATOR_INDEPENDENCE = HANDOFF_REQUIRED     (4/8 điều kiện HỎNG)
CASES_DRAWN            = NO
APPLICATION_LLM_CALLS  = 0
V3_SEED                = null   (EXTERNAL_SEED còn nguyên, chưa dùng)
```

| điều kiện | | bằng chứng git |
|---|---|---|
| không viết `radius_sq_khai` | ❌ | `3ffebcd` |
| không viết checker `area`/`lateral_area` | ❌ | `b146fc8` |
| không viết scorer expressiveness | ❌ | `d7eb96b` |
| không viết V3 runner / measurement policy | ❌ | `3e6632a` · `d8e86a1` |
| chưa đọc `POOL.json` theo nội dung | ✅ | chỉ dùng băm + aggregate chỉ-đếm |
| chưa đọc `de`/`mong`/tham số/đáp số | ✅ | |
| chưa biết ánh xạ case ID → nội dung | ✅ | |
| chưa xem kết quả seed thật | ✅ | chưa rút |

**Phần CƠ HỌC của Phase 1 đã đo và ĐẠT** (0 lượt gọi, không đọc nội dung pool,
không rút). Bảng dưới để evaluator mới **đối chiếu**, không phải để tin thay:

| | |
|---|---|
| HEAD · cây | `1da83a0` · **CLEAN** |
| candidate | `a696200e8f8c668c…` · 89 file · **== seal** ✅ · verify exit 0 |
| pool | `36c2153ecefd2dbf…` · **== seal** ✅ · 26 bài / 13 ô (9 dương · 4 âm) |
| `seed` · `da_rut` | **`null`** · **`null`** |
| `CACHE_VERSION` · `ARTIFACT_SCHEMA` | **78** · **1.2** |
| scorer | `4f7cae906500e0b6…` |
| V3 runner | `55be22b6ddd52992…` |
| acceptance integrity | `7b5e3ed17fd46d44…` |
| certifier | `81799613f8c01f2d…` |
| policy loader | `b51e936f809bd314…` |
| threshold policy | `460e0ce57a304872…` · **v1.1.0** · `decided_before_live_run = true` |
| attribution rubric | `d44f2b7c19b4904f…` · v1.0.0 |
| danh tính model | **`LIMITED_ACCEPTED`** · `temperature` explicit 0.2 · `top_p` **NOT_SENT** · `max_output_tokens` **NOT_SENT** · `repair_limit` 3 |
| trần lượt gọi (13 ca) | **78** — dẫn xuất, không phỏng đoán |
| chứng nhận | `RUNNER_CERTIFICATION` **PASS** · `V3_RUNNER_INTEGRATION` **PASS** · 0 lượt gọi |
| readiness | `READY_FOR_INDEPENDENT_V3_LIVE` **YES** · danh sách chặn **rỗng** |
| credential | `backend/.env` có `GEMINI_API_KEY` (kiểm bằng đường no-call; giá trị KHÔNG in ra) |

⚠️ **Bảng này do một evaluator KHÔNG độc lập đo.** Nó rút ngắn được thời gian
cho người kế tiếp, nhưng **không thay** Phase 1 của người ấy: cả giá trị của
Phase 1 nằm ở chỗ chính người sắp tiêu seed là người đo.

```
EVALUATOR_INDEPENDENCE = HANDOFF_REQUIRED
PRE_DRAW_GUARD         = BLOCKED  (ba nguyên nhân ĐỘC LẬP)
CASES_DRAWN            = NO
APPLICATION_LLM_CALLS  = 0
```

## 1. EVALUATOR_ATTESTATION

Tôi **không** đạt điều kiện độc lập. Hai trong năm điều kiện hỏng, và hỏng dứt
khoát — chứng minh bằng git, không bằng lời khai:

| điều kiện | trạng thái | bằng chứng |
|---|---|---|
| không tham gia triển khai `radius_sq_khai` | ❌ **HỎNG** | `3ffebcd feat(geometry): khối cầu khai được bằng TÂM + BÁN KÍNH` — do chính phiên này viết |
| không triển khai `area`/`lateral_area` | ❌ **HỎNG** | `b146fc8 feat(program): area và lateral_area thành nghĩa vụ có checker` — cùng phiên |
| không đọc `de`/`mong`/tham số/đáp số V3 | ✅ đạt | chỉ dùng aggregate chỉ-đếm suốt ba wave |
| không biết ánh xạ case ID → nội dung | ✅ đạt | chưa mở `POOL.json` |
| chưa xem kết quả seed thật | ✅ đạt | chưa rút |

Tôi là **tác giả của đúng hai năng lực mà V3 sinh ra để đo**. Chấm chính mình ở
đây không phải một khiếm khuyết thủ tục — nó phá đúng thứ phép đo này tồn tại
để cung cấp. Và phép rút là **một lần duy nhất** (`_rut` từ chối lần hai), nên
rút sai người sẽ tiêu vĩnh viễn một pool held-out.

Theo đúng nhánh mà đề bài đã định: dừng **trước** thao tác rút và **trước** mọi
application LLM call.

## 2. PRE_DRAW_GUARD — ba blocker ĐỘC LẬP

Mỗi cái tự nó đủ để dừng. Hai cái sau **không liên quan gì** tới độc lập của
tôi — chúng sẽ chặn bất kỳ evaluator nào.

### ① `HANDOFF_REQUIRED` — độc lập evaluator (§1)

### ② `BLOCKED_ERROR_CLASSIFICATION` — §5 guard ĐỎ

> ✅ **ĐÃ ĐÓNG 2026-09-04** — `docs/ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS.md`.
> `SYSTEM_EXPRESSIVENESS_GAP` và `ATTRIBUTION_UNRESOLVED` nay có trong
> `LOP_PHAN_QUYET`; fixture đường kính ra `SYSTEM_EXPRESSIVENESS_GAP` khi có
> bằng chứng năng lực, `ATTRIBUTION_UNRESOLVED` khi không. Scorer
> `98cc19c8…` → `4f7cae90…`; candidate/pool/seal/seed không đụng. Phần dưới
> giữ nguyên làm bản ghi lịch sử của lượt phát hiện.

Fixture tổng hợp **ngoài V3** (đường kính 26 → `arith(d,"/",2)` → radius):

```
stage    = ir_static
code     = semantic_program_invalid
details  = "#2 AMBIGUOUS_FIRST_BINDING: 'r' — cần scalar hoặc float hoặc int,
            có ràng buộc bằng một biểu thức không suy ra kiểu hình học
            (arith/literal/…) — hãy dùng một phép DỰNG"
→ phan_loai = MODEL_STATIC_FAILURE          ← SAI LỚP
```

`SYSTEM_EXPRESSIVENESS_GAP` **không tồn tại** trong `LOP_PHAN_QUYET`:

```
CORRECT_SERVABLE_RESULT · CORRECT_EXECUTABLE_IR · HONEST_UNSUPPORTED_REFUSAL ·
UNRELATED_FAIL_CLOSED · SYSTEM_COVERAGE_FAILURE · SYSTEM_VERIFICATION_FAILURE ·
SYSTEM_RUNTIME_FAILURE · SYSTEM_TRANSPORT_FAILURE · MODEL_SCHEMA_FAILURE ·
MODEL_STATIC_FAILURE · MODEL_GROUNDING_FAILURE · MODEL_FIRST_BINDING_FAILURE ·
MODEL_COMPOSITION_FAILURE
```

**Vì sao đây là blocker thật, không phải chi tiết:** đề cho **đường kính** thì
`r = d/2` là bước ĐÚNG về toán. Hệ hiện không biểu đạt được nó
(`arith` cho kiểu tĩnh `unknown`, và `radius` chỉ nhận `scalar|float|int`). Nếu
V3 chạy bây giờ và tập rút có một ca phát biểu bằng đường kính, thất bại ấy sẽ
được ghi là **lỗi mô hình** — đúng kiểu quy sai trách nhiệm mà cả tuyến probe
này tồn tại để chặn, và đúng rủi ro mà báo cáo reseal đã nêu ở §9.

**Đường sửa nhỏ nhất:** thêm lớp `SYSTEM_EXPRESSIVENESS_GAP` vào
`acceptance_verdict.LOP_PHAN_QUYET`, và ở `phan_loai` phân biệt
`ERR_RANG_BUOC_MO_HO` trên một ô **đòi vô hướng** (`radius`) khỏi lỗi soạn thảo
thường. Kèm test hai chiều + tiêm lỗi. Đây là bộ đo (`scripts/`), **ngoài**
`MEASURED_SYSTEM_PATHS`, nên nó **không** đụng candidate và **không** cần
reseal.

### ③ `BLOCKED_THRESHOLD_POLICY` — §4 không có ngưỡng nào

Quét toàn kho: ngưỡng chỉ tồn tại ở `score_mini_stability.NGUONG` (phép đo
KHÁC) và `finalize_phase7b_holdout` (pool Phase 7B, KHÁC). **Không** ngưỡng nào
cho V3 hình cong — không theo attempt, theo case, theo family, không
exact-match, không servable, không refusal, không trần lỗi hệ, không điều kiện
đề xuất `supported`.

`V3_SEAL.json` cũng không chở ngưỡng (đã khai ở `SEAL_COVERAGE` của wave
trước). Chạy trước rồi mới đặt ngưỡng là mở đường cho ngưỡng được chọn sau khi
biết kết quả — thứ làm con số mất hết giá trị.

## 3. Hai khiếm khuyết PHỤ (không tự mình chặn, nhưng phải sửa trước live)

**§2 — `RunManifest` thiếu danh tính scorer.** Nó ghi `runner` + `runner_hash`,
`model`, `chinh_sach_sua`, `ngan_sach_goi`, `seal`, `moi_truong`, `git`,
`tao_luc`, `artifact_schema_version` — nhưng **không** ghi hash của
`acceptance_verdict.py` (scorer) hay của threshold policy. Đề bài §2 đòi cả
hai. Sửa: thêm hai trường vào `RunManifest`.

**§3 — model KHÔNG ghim phiên bản.** `gemini.MODEL = os.getenv("GEMINI_MODEL",
"gemini-2.5-flash")` — một **alias trôi**, không phải snapshot. `temperature`
mặc định `0.2`; `top_p` và `max_output_tokens` **không** được đặt (mặc định
provider, không ghi lại). `REPAIR_LIMIT = MAX_SEMANTIC_PROGRAM_ATTEMPTS = 3`.
Một phép đo niêm phong nên ghim snapshot cụ thể, nếu không lượt sau không tái
lập được.

Môi trường: `backend/.env` tồn tại; `ALLOW_LIVE_AI` và `GEMINI_API_KEY` **chưa
đặt trong shell** của lượt này (không in giá trị nào).

## 4. SEALED_MEASUREMENT_IDENTITY (đã xác minh, chưa đụng)

| | |
|---|---|
| HEAD · cây | `6129d86` · **CLEAN** |
| candidate | `a696200e8f8c668c…` · 89 file · **== seal** ✅ · verify exit 0 |
| `CACHE_VERSION` | **78** |
| pool_hash (tính lại) | `36c2153ecefd2dbf…` · **== seal** ✅ |
| seed · da_rut | **`null`** · **`null`** |
| grammar_card | `24e550ad1c57a2aa…` |
| analyze_schema | `515001b503af5c7c…` |
| synthesis_schema | `82dbff3f62ee26fb…` |
| prompts | `55ac1ca6a6df92ce…` |
| capability | `85bd316781b86576…` |
| semantic_environment | `30502a4404cbe6aa…` |
| runner certification | **PASS** exit 0 |

Danh tính bộ đo (ghi để lượt live so trước/sau):

```
run_curved_acceptance.py        11e4b6200f817593…
acceptance_integrity.py         323ced722d1dd365…
acceptance_verdict.py           98cc19c898b73a52…
certify_acceptance_runner.py    07c550f524f3387f…
freeze_evaluation_candidate.py  6d95e610cf736e49…
seal_curved_v3.py               4b17faf28522a21b…
```

`EXTERNAL_SEED = 5324284654432805119` — **ghi lại, CHƯA dùng.** Seed chưa vào
seal, nên nó vẫn dùng được nguyên vẹn cho lượt live thật.

## 5. Việc phải làm trước khi mở lại lượt live

Theo thứ tự, ba cái đầu là bắt buộc:

1. **`ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS`** — thêm
   `SYSTEM_EXPRESSIVENESS_GAP`, phân biệt derived-radius khỏi lỗi soạn thảo.
   Chỉ `scripts/`, 0 lượt gọi, **không** đụng candidate/seal.
2. **`V3_THRESHOLD_POLICY`** — khai ngưỡng máy đọc được **trước** khi biết kết
   quả, băm và liên kết bất biến với run ID.
3. **`RunManifest` + ghim model** — thêm scorer hash và threshold hash; ghim
   snapshot model thay cho alias.
4. **Đổi evaluator** — người/phiên KHÔNG viết `radius_sq_khai`,
   `area`/`lateral_area`, và chưa đọc nội dung V3.

Cả bốn đều **ngoài `MEASURED_SYSTEM_PATHS`** ⇒ candidate `a696200e…` và
`pool_hash 36c2153e…` giữ nguyên, **không cần reseal lần nữa**.

## 6. RECOMMENDED_NEXT_ACTION

```
ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS
```

Chọn nó trước `V3_THRESHOLD_POLICY` vì nó là blocker **có bằng chứng chạy được**
(guard ĐỎ ngay lượt này), rẻ, và nếu bỏ qua thì mọi con số V3 về sau đều mang
nguy cơ quy sai trách nhiệm cho mô hình.

> **2026-09-05 — tất cả đã xong.** Khuyến nghị hiện hành:
> ```
> INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE
> ```
> `limited_reproducibility_allowed = true` đã ghi (policy `1.1.0`, băm
> `460e0ce5…`), khoá **trước** mọi kết quả. `run_curved_acceptance.py` nay
> gọi `mo_run` thật và canh bốn băm bộ đo **trước mỗi** lượt gọi provider;
> `certify_acceptance_runner.py` in thêm `V3_RUNNER_INTEGRATION PASS`.
>
> Trần lượt gọi cho 13 ca: **78** (8A 26 + 8B 52), dẫn từ call graph.

---

```
EVALUATOR_INDEPENDENCE                        HANDOFF_REQUIRED
EXTERNAL_SEED                                 5324284654432805119  (chưa dùng)
RUN_ID                                        —  (không tạo)

PRE_DRAW_GUARD                                BLOCKED
  ①                                           HANDOFF_REQUIRED
  ②                                           BLOCKED_ERROR_CLASSIFICATION
  ③                                           BLOCKED_THRESHOLD_POLICY
RUNNER_CERTIFICATION                          PASS (exit 0)
MODEL_PROVIDER                                gemini
MODEL_NAME                                    gemini-2.5-flash (alias, KHÔNG ghim)
MODEL_VERSION_OR_SNAPSHOT                     KHÔNG CÓ

CANDIDATE_HASH_BEFORE / AFTER                 a696200e8f8c668c… / không đổi
POOL_HASH_BEFORE / AFTER                      36c2153ecefd2dbf… / không đổi
CASE_SET_HASH                                 —  (chưa rút)
TOTAL_CASES_SELECTED                          0
TOTAL_CELLS_SELECTED                          0

APPLICATION_LLM_CALLS                         0
ANALYZE_CALLS / SYNTHESIS_CALLS / REPAIR_CALLS 0 / 0 / 0
TOTAL_ATTEMPTS                                0

V3_SEED                                       null
V3_DA_RUT                                     null
V3_RUN_VALID                                  N/A — không có lượt chạy
RUN_IDENTITY_STABLE                           N/A
RUN_ARTIFACT_HASH                             N/A

BALL_ACCEPTANCE                               NOT_MEASURED
CYLINDER_ACCEPTANCE                           NOT_MEASURED
CONE_ACCEPTANCE                               NOT_MEASURED
CENTER_RADIUS_DISCOVERABILITY                 NOT_MEASURED
AREA_OBLIGATION_DISCOVERABILITY               NOT_MEASURED
LATERAL_AREA_OBLIGATION_DISCOVERABILITY       NOT_MEASURED

PRODUCT_CAPABILITY_CHANGED                    NO
BALL / CYLINDER / CONE                        foundation_only
WORKING_TREE                                  CLEAN
```
