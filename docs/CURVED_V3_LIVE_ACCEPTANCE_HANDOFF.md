# CURVED_V3_LIVE_ACCEPTANCE — HANDOFF (lượt đo KHÔNG chạy)

> 2026-09-04. **`APPLICATION_LLM_CALLS = 0`** · `CASES_DRAWN = NO` ·
> `seed` vẫn `null` · pool **chưa bị đọc nội dung**.
>
> ⚠️ **CẬP NHẬT 2026-09-05 — hai trong ba blocker của §2 ĐÃ ĐÓNG.** ② đóng bởi
> `ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS`; ③ đóng bởi
> **`V3_THRESHOLD_AND_RUN_IDENTITY_POLICY`** (`docs/V3_THRESHOLD_AND_RUN_IDENTITY_POLICY.md`)
> — ngưỡng và rubric nay máy đọc được, đã băm và ghim vào `RunManifest` 1.1.
> Còn lại **①** (đổi evaluator) và **một quyết định học thuật**:
> `limited_reproducibility_allowed` trong threshold policy còn `null`, nên
> `READY_FOR_INDEPENDENT_V3_LIVE = CONDITIONAL`. Mục §3 và §5 dưới đây giữ
> nguyên làm bằng chứng của lượt 2026-09-04; đọc chúng như lịch sử, không như
> trạng thái hiện tại.
>
> Tên file có hậu tố `_HANDOFF` **có chủ đích**: `CURVED_V3_LIVE_ACCEPTANCE.md`
> là tên dành cho một báo cáo có số đo. Lượt này không có số đo nào; đặt tên ấy
> lên một tài liệu rỗng kết quả là mời người đọc sau tưởng V3 đã chạy.

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

> **2026-09-05 — cả hai đã xong.** Khuyến nghị hiện hành:
> ```
> EXTERNAL_REPRODUCIBILITY_DECISION
> ```
> Người hướng dẫn ghi `limited_reproducibility_allowed` (`true`/`false`) vào
> `backend/scripts/policies/curved_v3_threshold_policy.json`, rồi bump
> `policy_version` và băm lại. Chi tiết ba đường ra:
> `V3_THRESHOLD_AND_RUN_IDENTITY_POLICY.md §6`.
>
> Và **một việc kỹ thuật còn nợ**: `run_curved_acceptance.py` chưa gọi
> `mo_run`, nên những gì manifest 1.1 ghim sẽ **không có mặt** trong artifact
> V3 nếu chạy nguyên trạng. Phải nối trước lượt live.

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
