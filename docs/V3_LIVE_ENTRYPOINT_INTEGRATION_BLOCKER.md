# V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER

> 2026-09-05, phiên evaluator **ĐỘC LẬP** (phiên thứ ba nhận uỷ quyền V3).
>
> ```
> EVALUATOR_INDEPENDENCE = CONFIRMED     ← lần đầu tiên đạt
> PRE_DRAW_GUARD         = BLOCKED       ← hai blocker MỚI, thuộc bộ đo
> CASES_DRAWN            = NO
> APPLICATION_LLM_CALLS  = 0
> V3_SEED                = null          (EXTERNAL_SEED còn nguyên, chưa dùng)
> ```
>
> Tên file **không** phải `CURVED_V3_LIVE_ACCEPTANCE.md`, có chủ đích — tên ấy
> dành cho một báo cáo **có số đo**. Lượt này không có số đo nào.

Bằng chứng máy: `docs/evaluation/geometry/curved-v3/PREDRAW_GUARD_2026-09-05_INDEPENDENT.json`
(băm `3ade2a9e891ab3fe…`).

> ✅ **CẢ HAI BLOCKER ĐÃ ĐÓNG cùng ngày** —
> **`docs/V3_LIVE_ENTRYPOINT_WIRING_REPAIR.md`**. Tài liệu này giữ nguyên làm
> bản ghi của lượt **phát hiện**; đọc nó như lịch sử, không như trạng thái hiện
> tại. Trạng thái hiện hành:
> `READY_FOR_INDEPENDENT_V3_LIVE = YES` ·
> `RECOMMENDED_NEXT_ACTION = INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE` ·
> seed `5324284654432805119` **vẫn chưa dùng**.

## 0. Tóm tắt một đoạn

Blocker ① của hai lượt trước — **độc lập evaluator** — nay ĐÓNG: phiên này
không viết `radius_sq_khai`, không viết `area`/`lateral_area`, không viết
scorer, không viết runner, chưa đọc nội dung V3.

Nhưng phần **cơ học** của tiền kiểm, khi đo lại thay vì đọc bảng bàn giao, phát
hiện hai khiếm khuyết **mới** mà không lượt kiểm nào trước đó chạm tới. Cả hai
nằm ở **đường chạy live thật** của runner:

| | |
|---|---|
| ① `LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL` | `main_async` chạy **corpus phát triển V1/V2**, không phải pool V3 đã rút; không ghi `manifest.json`; không qua identity guard |
| ② `POOL_MONG_TYPE_INCOMPATIBLE` | `mong` của pool V3 là `list`, runner đòi `set` ⇒ `TypeError` **sau** khi ca đó đã tiêu quota |

Nếu rút rồi chạy, kết quả sẽ là: 78 lượt gọi tiêu trên **9 đề đã công bố**, một
file tên `curved_acceptance.json` không có manifest, và **pool held-out mất vĩnh
viễn** (`_rut` từ chối lần hai). Đó đúng là thứ phép đo này tồn tại để chặn.

Cả hai đều nằm trong `backend/scripts/` — **ngoài `MEASURED_SYSTEM_PATHS`** —
nên sửa chúng **không** đụng candidate `a696200e…`, **không** đụng
`pool_hash 36c2153e…`, và **không cần reseal**. Seed vẫn dùng được nguyên vẹn.

## 1. EVALUATOR_ATTESTATION

Căn cứ vào hoạt động thực tế của phiên, không vào tên Git author:

| điều kiện | | bằng chứng |
|---|---|---|
| chưa sửa repository | ✅ | `git status --porcelain` rỗng lúc mở phiên và suốt tiền kiểm; mọi script đo đặt ở scratchpad ngoài kho |
| chưa tạo commit | ✅ | `git log` đỉnh vẫn `e4a929b` suốt Phase 0–1 |
| không viết `radius_sq_khai` (`3ffebcd`) | ✅ | phiên này 0 commit |
| không viết `area`/`lateral_area` (`b146fc8`) | ✅ | |
| không viết scorer expressiveness (`d7eb96b`) | ✅ | |
| không viết runner / measurement policy (`3e6632a`, `d8e86a1`) | ✅ | |
| không viết handoff (`e4a929b`) | ✅ | |
| chưa đọc nội dung V3 | ✅ | chỉ băm, đếm, **tên trường**; `de`/`mong`/`cong_thuc`/ánh xạ id→nội dung chưa mở |
| chưa xem kết quả seed thật | ✅ | chưa rút |
| không kế thừa transcript triển khai | ✅ | phiên mới, không Continue/Resume/fork |

**Khai báo trung thực, một điều phải nói:** trong lúc truy vết call graph, phiên
này **có** đọc văn bản đề của 3 ca thuộc corpus `CA` nằm **inline** trong
`run_curved_acceptance.py` (`circumsphere`, `refuse_oblique`,
`refuse_line_curved`). Đó là **dữ liệu phát triển V1/V2 đã công bố**, không phải
pool V3 — chính runner gọi nó là *"bộ V1/V2 đã chạy và đã công bố"*. Nội dung V3
vẫn chưa đọc. Ghi ra đây vì điểm của attestation là khai đúng cái đã đọc, không
phải khai cái nghe gọn.

```
EVALUATOR_INDEPENDENCE = CONFIRMED
```

## 2. Tiền kiểm CƠ HỌC — đo lại, không chép bảng bàn giao

Bảng ở `CURVED_V3_LIVE_ACCEPTANCE_HANDOFF.md §0` do một evaluator **không** độc
lập đo. Nó được **đối chiếu**, không được tin thay. Mọi dòng dưới đây đo lại
bằng script độc lập (`sha256` trên bytes thật, `json` stdlib, không import
module bộ đo cho phần băm).

### 2a. Kho và candidate

| | | |
|---|---|---|
| HEAD | `e4a929bcd2ed21a9…` | `git rev-parse HEAD` |
| nhánh · cây | `main` · **CLEAN** | `git status --porcelain` rỗng |
| `git diff --check` | exit **0** | |
| pytest toàn bộ | **3518 passed · 1 skipped · 1 deselected**, exit 0, 43.15s | |
| candidate (đo lại) | `a696200e8f8c668c…` · **89 file** | `freeze_evaluation_candidate.py --verify` exit **0** |
| candidate == seal | ✅ | |
| `CACHE_VERSION` | **78** | `app/main.py:421` |
| `ARTIFACT_SCHEMA_VERSION` | **1.2** | `acceptance_integrity.py:66` |

**Commit sau candidate không đụng hệ được đo** — đo bằng máy, không bằng lời:
commit cuối chạm `MEASURED_SYSTEM_PATHS` là `b146fc8`; từ đó tới `HEAD` có 11
commit, chạm đúng `backend/scripts`, `backend/tests`, `docs/` và **không file
nào** khớp `^(backend/app|frontend/src/simulations/domains/semantic)`.

### 2b. Pool và con dấu

| | |
|---|---|
| pool_hash (tính lại) | `36c2153ecefd2dbf…` · **== seal** ✅ |
| pool_size | **26** · **13 ô** · mỗi ô **đúng 2 bài** |
| ô dương · ô âm | **9** · **4** |
| `seed` · `da_rut` | **`null`** · **`null`** |
| `policy.pool_hash` == seal | ✅ |
| `policy.candidate_hash` == seal | ✅ |

### 2c. Danh tính bộ đo — tính lại từ file thật

| | băm | kỳ vọng |
|---|---|---|
| runner `run_curved_acceptance.py` | `55be22b6ddd52992…` | `55be22b6…` ✅ |
| scorer `acceptance_verdict.py` | `4f7cae906500e0b6…` | `4f7cae906500e0b6…` ✅ |
| threshold policy (canonical) | `460e0ce57a304872…` | `460e0ce5…` ✅ |
| attribution rubric (canonical) | `d44f2b7c19b4904f…` | `d44f2b7c…` ✅ |
| policy loader `measurement_policy.py` | `b51e936f809bd314…` | `b51e936f…` ✅ |
| `acceptance_integrity.py` | `7b5e3ed17fd46d44…` | — |
| `certify_acceptance_runner.py` | `81799613f8c01f2d…` | — |
| `seal_curved_v3.py` | `4b17faf28522a21b…` | — |
| `freeze_evaluation_candidate.py` | `6d95e610cf736e49…` | — |

### 2d. Chính sách và danh tính model

`policy_version` **1.1.0** · `created_before_live_run` **true** ·
`decided_before_live_run` **true** · `limited_reproducibility_allowed` **true** ·
`accepted_verdict` `LIMITED_ACCEPTED` · rubric **1.0.0**, `created_before_live_run` **true**.

```
provider                  gemini
model_name                gemini-2.5-flash        (ALIAS, không phải snapshot)
model_version_or_snapshot null
model_reproducibility     LIMITED_ACCEPTED
temperature               explicit  0.2
top_p                     not_sent  null
max_output_tokens         not_sent  null
repair_limit              3
APPLICATION_CALL_BUDGET   78   = 8A 13×(1+1×1)=26 + 8B 13×(1+3×1)=52
```

Trần **78** dẫn xuất, không phỏng đoán: `tran_luot_goi_v3(13)` trả đúng `78`.

### 2e. Cổng đã chạy

| cổng | kết quả |
|---|---|
| `freeze_evaluation_candidate.py --verify` | exit **0** |
| `certify_acceptance_runner.py` | exit **0** · `RUNNER_CERTIFICATION` **PASS** · `V3_RUNNER_INTEGRATION` **PASS** · `APPLICATION_LLM_CALLS 0` |
| `pytest` 6 file cổng (integrity · v3 manifest · v3 threshold · cache identity · current-state identity · evaluation candidate) | **160 passed**, exit 0 |
| readiness guard `san_sang_live_tu_cau_hinh` | danh sách chặn **RỖNG**; 2 giới hạn đã khai |
| credential | `backend/.env` → `GEMINI_API_KEY` **PRESENT** (giá trị không in) |

Tức là: **mọi cổng mà đề bài §5 liệt kê đều XANH.** Hai blocker dưới đây nằm
đúng ở chỗ không cổng nào nhìn.

## 3. Blocker ① — `LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL`

**Expected.** Đường chạy live (`main_async`, tức lệnh `--out-dir` mà
`…_LIMITED_REPRODUCIBILITY_DECISION.md §15` chỉ định) phải: đọc bộ ca từ
`nap_ca_v3()`; mở lượt bằng `mo_luot_do_v3` → `mo_run` để **ghi `manifest.json`
trước lượt gọi đầu**; và đi qua `canh_gac_truoc_luot_goi` **trước mỗi** lượt gọi
provider.

**Observed.** Phân tích AST trên `run_curved_acceptance.py`, gộp call graph của
`main` + `main_async` + `_chay_mot`:

```
mo_luot_do_v3                KHÔNG
nap_ca_v3                    KHÔNG
mo_run                       KHÔNG
canh_gac_truoc_luot_goi      KHÔNG
kiem_bo_ca_la_pool_v3        KHÔNG
```

Không phải "gọi sai" — **không gọi lần nào**. `nap_ca_v3` chỉ được nhắc ở đúng
một chỗ ngoài định nghĩa: một test khẳng định nó *ném* khi chưa rút.
`mo_luot_do_v3` chỉ được gọi bởi certifier và bởi test.

`main_async` gán bộ ca ở **dòng 558**:

```python
chay = CA          # dòng 558
...
chay = [c for c in CA if c['id'] in muon]    # dòng 565, --ca lọc TRONG CA
```

và `CA` là:

```
len(CA)  = 9
ids      = ball_1 · ball_2 · circumsphere · cone_1 · cone_2 ·
           cylinder_1 · cylinder_2 · refuse_line_curved · refuse_oblique
CA_HASH  = 8c6a184f1c175964…
```

Chính runner khai `CA` là *"corpus V1/V2: 9 đề tôi tự viết, đã chạy, artifact đã
công bố… dữ liệu phát triển"*. Và **guard của chính runner từ chối bộ này**:

```
kiem_bo_ca_la_pool_v3(CA)
→ IntegrityError: CORPUS PHÁT TRIỂN lọt vào chỗ pool V3:
  ['ball_1','ball_2','circumsphere','cone_1','cone_2','cylinder_1',
   'cylinder_2','refuse_line_curved','refuse_oblique']
  `CA` là bộ V1/V2 đã chạy và đã công bố — chấm trên nó không phải phép đo held-out.
```

Guard nói đúng. Nó chỉ không được đặt trên đường mà lượt live đi qua.

Ba hệ quả đo được:

| | |
|---|---|
| artifact `main_async` ghi | `stage_8a_one_shot.json` · `curved_acceptance.json` — **không có `manifest.json`** |
| ngân sách thực đặt | `ApiBudget(max_api_calls=4n+4, max_logical_calls=3n+5)` → n=9: **40 / 32** |
| trần dẫn xuất đúng cho 13 ca | **78** |

`3n+5` chính là công thức mà `…_DECISION.md §… ` đã gọi là *"một con số có `+5`
mà không ai giải thích được `5` từ đâu"* — nó vẫn nằm nguyên trên đường chạy
thật.

**Vì sao `V3_RUNNER_INTEGRATION PASS` vẫn xanh.**
`certify_acceptance_runner.chung_nhan_runner_v3` dựng **2 ca tổng hợp của chính
nó** (`CERT1`, `CERT2`) rồi gọi **thẳng** `R.mo_luot_do_v3(...)`. Nó chưa bao giờ
chạy `main_async`. Nên nhãn PASS chứng minh **hàm `mo_luot_do_v3` hành xử đúng**
— nó **không** chứng minh đường chạy thật gọi hàm đó. Test `test_J1` cũng vậy:
nó patch `R.mo_luot_do_v3` rồi kiểm **certifier** đỏ, không kiểm entrypoint.

Đây đúng là hình dạng lỗi mà `…_DECISION.md §2` đã chẩn đoán —
*"một guard không nằm trên đường chạy thật thì không bảo vệ gì cả"* — tái diễn
lên một tầng: bản vá được thêm vào như một **hàm**, certifier được trỏ vào hàm,
còn **entrypoint thì không được nối lại**.

⚠️ Hai dòng trong `V3_RUNNER_MANIFEST_INTEGRATION_AND_LIMITED_REPRODUCIBILITY_DECISION.md`
đọc rộng hơn phạm vi chúng chứng minh, cần đọc kèm mục này:
`V3_RUNNER_CALLS_MO_RUN = YES` và `MANIFEST_WRITTEN_BEFORE_FIRST_CALL = YES` —
**đúng với `mo_luot_do_v3`, sai với `main_async`**.

## 4. Blocker ② — `POOL_MONG_TYPE_INCOMPATIBLE`

Độc lập với ①: sửa xong ① mà bỏ ② thì lượt live vẫn hỏng, và hỏng **sau khi đã
tiêu quota**.

**Expected.** `run_curved_acceptance.py:467`

```python
ra["dap_so_khop"] = c["mong"] <= set(ra["dai_luong"])
```

đòi `c["mong"]` là `set` (phép `<=` = tập con).

**Observed.**

```
kiểu `mong` trong CA        ['set']      ← corpus V1/V2, hợp
kiểu `mong` trong POOL V3   ['list']     ← pool đã niêm phong
['X'] <= {'X','Y'}  →  TypeError: '<=' not supported between instances of 'list' and 'set'
```

**18/26** ca dương của pool có `mong` không rỗng. Dòng 467 nằm **sau**
`verify_and_compile`, tức sau lượt analyze **và** lượt tổng hợp của ca đó — quota
đã tiêu rồi lỗi mới nổ. Và vòng lặp 8A chỉ bắt `gemini.BudgetExceeded`, nên
`TypeError` thoát ra và **kết thúc cả lượt**, ngay ở ca dương đầu tiên chạy được.

## 5. Vì sao dừng TRƯỚC khi rút, không dừng sau

`_rut` từ chối lần hai (`"đã rút bằng seed … — không rút lần hai"`). Rút là thao
tác **một chiều**. Ba yêu cầu của đề bài trở thành **không thoả được** với runner
đang đóng băng:

| yêu cầu | trạng thái |
|---|---|
| Phase 2: chạy đúng 13 ca đã rút | ✗ — `main_async` chạy 9 ca corpus |
| Phase 3: `mo_run` ghi manifest **trước** call đầu | ✗ — không ghi manifest |
| Phase 4: **mọi** application call qua identity guard | ✗ — guard không trên đường chạy |

Rút rồi mới phát hiện = tiêu vĩnh viễn một pool held-out để đổi lấy đúng dòng
`RUN_VALIDITY = INVALID_PRE_CALL`. Dừng trước khi rút giữ nguyên **cả** seed
**và** pool.

`<frozen_scope>` của lượt này cấm sửa runner (*"Giữ nguyên candidate, runner,
scorer, certifier, policy, rubric, loader, pool, seal"*), và mục tiêu là **đo hệ
hiện tại, không phát triển thêm**. Nên lượt này **không** sửa gì; nó ghi lại
điều đo được và trả việc.

## 6. Đường sửa nhỏ nhất — và vì sao KHÔNG cần reseal

Cả hai blocker nằm trong `backend/scripts/run_curved_acceptance.py`.
`MEASURED_SYSTEM_PATHS` = `backend/app` · `frontend/src/simulations/domains/semantic`
(+ schema). `scripts/` là **bộ đo**, không phải hệ được đo ⇒ candidate
`a696200e…` giữ nguyên, `pool_hash 36c2153e…` giữ nguyên, **không reseal**,
seed chưa dùng vẫn dùng được.

Năm việc, theo thứ tự:

1. `main_async`: thay `chay = CA` bằng `ca_v3 = nap_ca_v3()` → `chay = ca_v3`;
   `--ca` lọc **trong** `ca_v3`. Gọi `kiem_bo_ca_la_pool_v3(ca_v3)`.
2. Chuẩn hoá `mong` sang `set` ngay tại `nap_ca_v3()` (một chỗ, không rải rác).
   Pool đã mang đủ trường runner cần — `id`, `hinh`, `loai`, `de`, `mong` — với
   `hinh ∈ {ball, cylinder, cone}` và `loai ∈ {am, duong}`, nên đây là chuyển
   kiểu, **không** phải đổi lược đồ pool. **Không sửa `POOL.json`** — sửa pool
   là làm lệch `pool_hash`.
3. Gọi `mo_luot_do_v3(out, run_id=…, ca=ca_v3)` **trước** lượt gọi provider đầu.
4. Luồn `canh_gac_truoc_luot_goi(out, con_lai=…)` vào `_chay_mot` trước **mỗi**
   lượt gọi provider; thay `ApiBudget(4n+4, 3n+5)` bằng trần dẫn xuất
   `tran_luot_goi_v3(len(chay))`.
5. **Test còn thiếu — đây mới là chỗ trả nợ thật.** Cả 31 test integration đều
   gọi `mo_luot_do_v3` trực tiếp. Cần một test chạy **`main_async`** với provider
   bị stub (0 lượt gọi thật) rồi khẳng định: `manifest.json` tồn tại; bộ ca đã
   chạy khớp `da_rut` của con dấu; mọi lượt gọi đi sau guard. Không có test hình
   dạng đó thì lần nối lại sau vẫn có thể tuột y hệt lần này.

Sau đó chạy lại `certify_acceptance_runner.py`, rồi mới tới `--rut --seed`.

## 7. Còn NOT_MEASURED

Không có số đo nào được sinh ra ở lượt này, nên **không dòng nào** trong
`THESIS_READINESS.md` đổi giá trị:

```
BALL / CYLINDER / CONE ACCEPTANCE          NOT_MEASURED
CENTER_RADIUS_DISCOVERABILITY              NOT_MEASURED
AREA / LATERAL_AREA_OBLIGATION             NOT_MEASURED
PRODUCT_PROMOTION_ELIGIBLE_*               NOT_MEASURED
PRODUCT_CAPABILITY_CHANGED                 NO
ball · cylinder · cone                     foundation_only
```

## 8. RECOMMENDED_NEXT_ACTION

```
V3_LIVE_ENTRYPOINT_WIRING_REPAIR
```

Không phải `MEASUREMENT_INVALIDATION_REVIEW` (không có lượt chạy nào để vô
hiệu), không phải `TARGETED_SYNTHESIS_ERGONOMICS_REPAIR` (chưa đo được gì về mô
hình). Việc kế tiếp là **§6, năm mục**, chạy trong một phiên bất kỳ — nó là bộ
đo, không phải phép đo, nên **không** đòi độc lập evaluator.

Sau khi §6 xong và certifier xanh **trên `main_async`**, lượt live cần lại một
phiên evaluator độc lập, và `EXTERNAL_SEED = 5324284654432805119` vẫn còn nguyên.

---

```text
EVALUATOR_INDEPENDENCE                    CONFIRMED
PRE_DRAW_GUARD                            BLOCKED
  ①                                       LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL
  ②                                       POOL_MONG_TYPE_INCOMPATIBLE
EXTERNAL_SEED                             5324284654432805119  (CHƯA dùng)
RUN_ID                                    —  (không tạo)
CASE_SET_HASH                             —  (chưa rút)
MANIFEST_WRITTEN_BEFORE_FIRST_CALL        N/A — không có lượt chạy
RUN_IDENTITY_STABLE                       N/A
RUN_VALIDITY                              N/A — không có lượt chạy

CANDIDATE_HASH_BEFORE/AFTER               a696200e8f8c668c… / a696200e8f8c668c…  (89 file)
POOL_HASH_BEFORE/AFTER                    36c2153ecefd2dbf… / 36c2153ecefd2dbf…
RUNNER_HASH_BEFORE/AFTER                  55be22b6ddd52992… / 55be22b6ddd52992…
SCORER_HASH_BEFORE/AFTER                  4f7cae906500e0b6… / 4f7cae906500e0b6…
THRESHOLD_POLICY_HASH_BEFORE/AFTER        460e0ce57a304872… / 460e0ce57a304872…
ATTRIBUTION_RUBRIC_HASH_BEFORE/AFTER      d44f2b7c19b4904f… / d44f2b7c19b4904f…
POLICY_LOADER_HASH_BEFORE/AFTER           b51e936f809bd314… / b51e936f809bd314…

MODEL_PROVIDER/NAME                       gemini / gemini-2.5-flash  (ALIAS)
MODEL_VERSION_OR_SNAPSHOT                 null
MODEL_IDENTITY_REPRODUCIBILITY            LIMITED_ACCEPTED
TEMPERATURE/TOP_P/MAX_OUTPUT_TOKENS       explicit 0.2 / NOT_SENT / NOT_SENT
REPAIR_LIMIT                              3
APPLICATION_CALL_BUDGET                   78  (dẫn xuất, chưa dùng)

TOTAL/POSITIVE/NEGATIVE_CASES_SELECTED    0 / 0 / 0
BALL/CYLINDER/CONE_CASES_SELECTED         0 / 0 / 0

APPLICATION_LLM_CALLS                     0
ANALYZE/SYNTHESIS/REPAIR_CALLS            0 / 0 / 0
TOTAL_ATTEMPTS                            0
TOTAL_INPUT/OUTPUT_TOKENS                 0 / 0

FIRST_ATTEMPT_SERVABLE                    NOT_MEASURED
EVENTUAL_SERVABLE                         NOT_MEASURED
EXACT_ANSWER_MATCH                        NOT_MEASURED
POSTCONDITIONS_PASS                       NOT_MEASURED
SCENE3D_PASS                              NOT_MEASURED

SYSTEM_EXPRESSIVENESS_GAP_COUNT           NOT_MEASURED
ATTRIBUTION_UNRESOLVED_COUNT              NOT_MEASURED
MODEL_FAILURE_COUNT                       NOT_MEASURED
NEGATIVE_HONEST_REFUSAL                   NOT_MEASURED
TARGET_BOUNDARY_PASS                      NOT_MEASURED

GENERAL_CURVED_SYNTHESIS_ACCEPTANCE       NOT_MEASURED
PRODUCT_PROMOTION_ELIGIBLE_BALL           NOT_MEASURED
PRODUCT_PROMOTION_ELIGIBLE_CYLINDER       NOT_MEASURED
PRODUCT_PROMOTION_ELIGIBLE_CONE           NOT_MEASURED
PRODUCT_CAPABILITY_CHANGED                NO

RUN_ARTIFACT_HASH                         N/A — không có run artifact
PREDRAW_ARTIFACT_HASH                     3ade2a9e891ab3fe…
REPORT                                    docs/V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER.md
RECOMMENDED_NEXT_ACTION                   V3_LIVE_ENTRYPOINT_WIRING_REPAIR
```
