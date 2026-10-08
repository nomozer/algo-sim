# V3_LIVE_ENTRYPOINT_WIRING_REPAIR

> 2026-09-05. **`APPLICATION_LLM_CALLS = 0`** · `CASES_DRAWN = NO` ·
> `seed = null` · `da_rut = null` · `RESEAL_PERFORMED = NO` ·
> `PRODUCT_CAPABILITY_CHANGED = NO`.
>
> Wave **bộ đo**: chỉ `backend/scripts`, `backend/tests`, `docs`. Hệ được đo
> không đụng — candidate `a696200e…` khớp, `--verify` exit 0.
>
> Nội dung V3 thật (`de`, `mong`, tham số, đáp số, ánh xạ ID→nội dung) **chưa
> mở**. Mọi fixture ở đây là pool/seal **tổng hợp** trong thư mục tạm.
>
> Phiên này là **phiên triển khai**. Lượt V3 live tiếp theo phải dùng evaluator
> mới — không Continue, Resume hay fork từ đây.

## 1. ROOT_CAUSE

Một bản vá được thêm vào như **hàm**, cổng chứng nhận được trỏ vào hàm, còn
**entrypoint thì không được nối lại**.

Wave `V3_RUNNER_MANIFEST_INTEGRATION` (2026-09-05) dựng `mo_luot_do_v3`,
`nap_ca_v3`, `canh_gac_truoc_luot_goi` và 31 test cho chúng. Cả 31 test gọi
**thẳng** `mo_luot_do_v3`; `certify_acceptance_runner.chung_nhan_runner_v3`
cũng vậy, với hai ca tổng hợp của chính nó. Không cái nào chạy `main_async` —
đường mà lệnh `--out-dir` ở `…_DECISION.md §15` thật sự chạy.

Nên `main_async` giữ nguyên nết cũ: `chay = CA`, không manifest, không guard,
trần `3n+5`. Và `V3_RUNNER_INTEGRATION PASS` xanh suốt.

Đây **cùng một hình dạng lỗi** mà `…_DECISION.md §2` đã chẩn đoán — *"một guard
không nằm trên đường chạy thật thì không bảo vệ gì cả"* — tái diễn lên một
tầng. Lần trước là guard không nằm trên đường chạy; lần này là **bài chứng nhận**
không nằm trên đường chạy.

Blocker ② (`mong` là `list`) là một lỗi **độc lập**, cùng chỗ: nó chỉ lộ ra khi
đường dây đã nối, vì trước đó không ca V3 nào tới được dòng 467.

## 2. Tái hiện TRƯỚC sửa

### 2a. Call graph (AST, `main` + `main_async` + `_chay_mot`)

```
mo_luot_do_v3                KHÔNG
nap_ca_v3                    KHÔNG
mo_run                       KHÔNG
canh_gac_truoc_luot_goi      KHÔNG
kiem_bo_ca_la_pool_v3        KHÔNG
main_async corpus            CA (phát triển), dòng 558 `chay = CA`
manifest trước lượt gọi đầu  KHÔNG   (chỉ ghi stage_8a_one_shot + curved_acceptance)
```

Guard của chính runner từ chối bộ mà live path chạy:

```
kiem_bo_ca_la_pool_v3(CA)
→ IntegrityError: CORPUS PHÁT TRIỂN lọt vào chỗ pool V3: ['ball_1',…]
```

Test đo trước sửa, thất bại **đúng lý do**:

| test | lỗi trước sửa |
|---|---|
| `test_D1a_nap_ca_v3_tra_mong_kieu_set` | `ValueError: too many values to unpack (expected 3)` |
| `test_D2a_manifest_ton_tai_TRUOC_luot_goi_provider_dau_tien` | `AssertionError: không ghi manifest` |
| `test_D3a_nhanh_8B_tra_ca_trong_tap_V3` | `assert 7 == 9` — chạy 9 ca corpus, 7 dương |

`7 == 9` là bằng chứng gọn nhất: mẫu số của lượt "nghiệm thu 13 ca held-out"
thật ra là corpus phát triển 9 ca.

Toàn bộ file: **21 failed, 6 passed** trước sửa. 6 xanh sẵn là **control** —
chúng khẳng định thứ đã đúng (pool không bị ghi đè, `--out-dir` đã có nội dung
thì dừng, cơ học `ApiBudget`, guard chống corpus còn nguyên, `list <= set` ném,
công thức trần). Nếu chúng cũng đỏ thì bộ test đang đo sai chỗ.

### 2b. Kiểu `mong`

```
kiểu `mong` trong POOL V3   ['list']
['X'] <= {'X','Y'}          TypeError: '<=' not supported between instances of 'list' and 'set'
set(['X']) <= {'X','Y'}     True
```

18/26 ca dương của pool có `mong` không rỗng. Dòng 467 nằm **sau**
`verify_and_compile`, tức sau lượt analyze **và** lượt tổng hợp của ca đó; vòng
lặp 8A chỉ bắt `gemini.BudgetExceeded`, nên `TypeError` thoát ra và kết thúc cả
lượt — **quota đã tiêu**.

## 3. Bảng ĐẦY ĐỦ consumer `CA` / `CA_HASH`

Không chỉ dòng `chay = CA`. Mười một chỗ, xử lý thống nhất:

| dòng (trước) | vai | sau sửa |
|---|---|---|
| 145 `_moi_truong` → `case_set_hash: CA_HASH` | môi trường artifact | `_moi_truong(case_set_hash)` — **tham số** |
| 558 `chay = CA` | nguồn bộ ca | `ca_v3, ca_tho, case_set_hash = nap_ca_v3()` |
| 561 `co = {c["id"] for c in CA}` | kiểm `--ca` | `theo_id` dựng từ `ca_v3` |
| 565 `chay = [c for c in CA …]` | lọc `--ca` | lọc trong `ca_v3` |
| 571 log `len(CA)` · `CA_HASH` | nhật ký | `len(ca_v3)` · `case_set_hash` |
| 572–573 `chay is not CA` | cờ probe | `la_probe = len(chay) != len(ca_v3)` |
| 607 artifact 8A `case_set_hash` | băm bộ ca | `case_set_hash` (từ con dấu) |
| 608 `None if chay is CA else …` | `tap_con` | `… if la_probe else None` |
| **621 `next(x for x in CA if …)`** | **tra ca 8B** | `theo_id[r["id"]]` |
| 654 `"CASE_SET_HASH": CA_HASH` | artifact cuối | `case_set_hash` |
| 655 `PROBE_SUBSET` | artifact cuối | `… if la_probe else None` |

Dòng 621 là chỗ nguy hiểm nhất: với id ô (`C1`…`N4`) thì `next()` ném
`StopIteration` — nhánh sửa chết ngay ca đầu, **sau khi 8A đã tiêu hết lượt**.

Giữ lại có chủ đích: `kiem_bo_ca_la_pool_v3` (dòng 164, 168) vẫn đọc `CA` — nó
là **guard**, không phải nguồn. Khoá bởi `test_D5c`.

## 4. Hợp đồng SAU sửa

### 4a. `nap_ca_v3()` — trả BA thứ

```python
ca_chuan, ca_tho, case_set_hash = nap_ca_v3()
```

- `ca_chuan` — để **CHẠY**. `mong` là `set`.
- `ca_tho` — để **NIÊM PHONG**. `mong` giữ `list`; `seal_bo_ca` băm bằng
  `json.dumps` và `set` không JSON-hoá được.
- `case_set_hash` — lấy từ **con dấu**, không tính lại theo đường khác.

Băm **trước** chuẩn hoá, chuẩn hoá trên `deepcopy`. `POOL.json` byte-identical
(`test_D1b`), và `seal_bo_ca(ca_tho)["case_set_hash"] == case_set_hash`
(`test_D1g`) — hai hàm `_bam` ở `seal_curved_v3` và `acceptance_integrity` là
cùng một công thức, nên đẳng thức này đúng chứ không phải trùng hợp.

### 4b. Cổng canh ở ĐÚNG ranh giới application call

`_chay_mot` **không** có đúng một lượt gọi:

```
_chay_mot
 ├─ pipeline.stage_semantic_analyze  → call_gemini  ×1
 └─ pipeline.stage_semantic_program  → call_gemini  ×1..MAX_SEMANTIC_PROGRAM_ATTEMPTS
```

Cổng trước `_chay_mot` sẽ **bỏ sót mọi lượt sửa**. Ranh giới thật là
`call_gemini` — một lượt gọi hàm ấy = một application call, đúng thứ
`ApiBudget.note_call` đếm (`gemini.py:208`). Bọc ở `scripts/`, **không** đụng
`app/`, nên candidate không phải mở.

Bọc/gỡ quanh **từng ca** trong `finally`: một bản vá toàn cục sống sót qua ngoại
lệ sẽ rò sang lượt sau, và thứ rò ra là một cổng trỏ vào thư mục của lượt đã
kết thúc. `test_F4` khoá điều này.

### 4c. Ngân sách

```
max_logical_calls = tran_luot_goi_v3(len(chay))          = 78  (13 ca)
max_api_calls     = 78 × gemini.MAX_ATTEMPTS             = 312
```

78 vào `max_logical_calls` vì đó là trường đếm application call.
`max_api_calls` đếm request HTTP, tức đã gồm retry transport. Công thức cũ
`3n+5` cho 13 ca ra **44** — thấp hơn worst case thật, một cái phanh hụt.

Probe 2 ca mang trần `tran_luot_goi_v3(2) = 12`, không mang trần của lượt 13 ca
(`test_D2m`).

### 4d. `--ca` giữ lại, nhưng không thể giả làm nghiệm thu

Lọc **trong** `ca_v3`; id corpus phát triển bị từ chối (`test_D2l`); artifact
mang `PROBE_SUBSET` không rỗng; `CASE_SET_HASH` **giữ nguyên của bộ đầy đủ**
(`test_D2k`) — nếu lọc mà băm cũng đổi theo thì mỗi probe lại sinh một "bộ ca"
mới trông như hợp lệ.

## 5. Chứng minh THỨ TỰ SỰ KIỆN

`test_D2a`/`test_D2b` chạy chính `main_async` với provider stub và ghi nhật ký:

```
load_sealed_cases → validate_sealed_cases → write_manifest
→ identity_guard → provider_call → identity_guard → provider_call → …
```

- `manifest.json` tồn tại trên đĩa **trước** `provider_call` đầu tiên;
- mỗi `provider_call` có đúng một `identity_guard` đi trước (đếm bằng ngăn xếp);
- guard hỏng ⇒ **`provider_call` count giữ nguyên 0** (`test_D2h`);
- 13 ca × 1 analyze = **13 lượt gọi**, tất cả qua stub ⇒ 0 network call.

## 6. Tiêm lỗi — mỗi bản vá bị hoàn tác phải ĐỎ

| # | tiêm | test | đỏ vì |
|---|---|---|---|
| ① | nguồn ca về `CA` | `test_D6a` | `IntegrityError: CORPUS PHÁT TRIỂN` · `goi == []` |
| ② | bỏ chuẩn hoá `mong` | `test_D6b` | `TypeError: '<=' not supported` |
| ③ | bỏ mở manifest | `test_D6c` | `IntegrityError: chưa có manifest` · `goi == []` |
| ④ | guard ném | `test_D2h` | provider không được gọi lần nào |
| ⑤ | khôi phục `3n+5` | `test_D6d` | `44 ≠ 78` |
| ⑥ | tra ca sửa trong `CA` | `test_D3a` | trước sửa `StopIteration`; nay `REPAIR_CALLS == 9` |
| ⑦ | ghi `CA_HASH` vào artifact | `test_D6e` | băm bộ ca V3 ≠ `CA_HASH` |
| ⑧ | certifier: nguồn về `CA` | `test_F2` | verdict mạnh FAIL |
| ⑨ | certifier: bỏ manifest | `test_F3` | FAIL, thông điệp chứa "manifest" |
| ⑩ | bỏ cổng readiness | `test_F5` | **đã đo thật**: gỡ khối `if not ok4` ⇒ in `YES` ⇒ đỏ; khôi phục ⇒ xanh |

⑩ được kiểm bằng cách **thật sự gỡ** khối gate rồi chạy `test_F5`:

```
AssertionError: assert 'READY_FOR_INDEPENDENT_V3_LIVE  CONDITIONAL' in '…YES…'
1 failed in 2.08s
```

rồi khôi phục. Một guard chưa từng đỏ là guard chưa được chứng minh.

## 7. Certifier — trước / sau

**Trước:** `chung_nhan` (5 kịch bản tổng hợp) + `chung_nhan_runner_v3` (gọi
thẳng `mo_luot_do_v3`, 2 ca của chính nó). Cả hai xanh trong khi entrypoint
chạy corpus phát triển.

**Sau:** thêm `chung_nhan_live_entrypoint` — chạy **chính `main_async`** với
pool/seal tổng hợp đã rút (`_pool_gia`: 26 bài / 13 ô) + provider stub, chứng
minh **bảy** điều: bộ ca đến từ con dấu · corpus phát triển không lọt · manifest
trước lượt gọi đầu · guard trước mỗi lượt gọi · trần 78 · `mong` đã chuẩn hoá ·
băm bộ ca V3 ở mọi artifact và không có `CA_HASH`.

Hai nhãn **tách rời, và in kèm phạm vi** — chỗ hiểu rộng chính là chỗ wave
trước để lọt:

```
  RUNNER_CERTIFICATION   PASS
  V3_RUNNER_INTEGRATION  PASS   (phạm vi: hàm `mo_luot_do_v3`)
  V3_LIVE_ENTRYPOINT_INTEGRATION  PASS   (phạm vi: `main_async` — đường chạy THẬT)
  APPLICATION_LLM_CALLS  0

  READY_FOR_INDEPENDENT_V3_LIVE  YES
    · giới hạn đã khai: `model_version_or_snapshot` trống — alias trôi
    · giới hạn đã khai: tái lập ở mức LIMITED_ACCEPTED
```

`READY_FOR_INDEPENDENT_V3_LIVE = YES` nay **chỉ** phát khi nhãn mạnh PASS.

## 8. Bảng danh tính

| | trước | sau | đổi |
|---|---|---|---|
| runner `run_curved_acceptance.py` | `55be22b6ddd52992…` | `6570b57bd6ac1fe4…` | **YES** |
| certifier `certify_acceptance_runner.py` | `81799613f8c01f2d…` | `070189b54af2b2ae…` | **YES** |
| scorer `acceptance_verdict.py` | `4f7cae906500e0b6…` | `4f7cae906500e0b6…` | NO |
| threshold policy | `460e0ce57a304872…` | `460e0ce57a304872…` | NO |
| attribution rubric | `d44f2b7c19b4904f…` | `d44f2b7c19b4904f…` | NO |
| policy loader `measurement_policy.py` | `b51e936f809bd314…` | `b51e936f809bd314…` | NO |
| `acceptance_integrity.py` | `7b5e3ed17fd46d44…` | `7b5e3ed17fd46d44…` | NO |
| `seal_curved_v3.py` | `4b17faf28522a21b…` | `4b17faf28522a21b…` | NO |
| candidate | `a696200e8f8c668c…` (89) | `a696200e8f8c668c…` (89) | **NO** |
| pool | `36c2153ecefd2dbf…` | `36c2153ecefd2dbf…` | NO |
| seal `seed` · `da_rut` | `null` · `null` | `null` · `null` | NO |
| `CACHE_VERSION` | 78 | 78 | NO |

```
NUMERIC_THRESHOLDS_CHANGED = NO
MEASURED_SYSTEM_CHANGED    = NO
RESEAL_PERFORMED           = NO
PRODUCT_CAPABILITY_CHANGED = NO
```

**Không có policy bump.** Băm runner/certifier chỉ được ghim ở **tài liệu**, và
trong `RunManifest` — nơi nó được tính **lúc mở lượt**, không hằng số hoá. Quét
toàn kho `55be22b6` / `81799613`: chỉ trúng `docs/`. Nên `curved_v3_threshold_
policy.json` không đổi một byte, ngưỡng số học không đổi, và tính "khoá trước
kết quả" của policy `1.1.0` còn nguyên.

## 9. Cổng đã chạy

| | |
|---|---|
| `tests/test_v3_live_entrypoint_wiring.py` (MỚI) | **37 passed** |
| full backend pytest (cây SẠCH, sau commit) | **3555 passed** · 1 skipped · 1 deselected · **0 failed**, exit 0 |
| `certify_acceptance_runner.py` | exit **0** · 3 nhãn PASS · 0 lượt gọi |
| `freeze_evaluation_candidate.py --verify` | exit **0** — 89 file, `a696200e…` |
| quét nguồn `CA` / `CA_HASH` trong live path | `test_D5a`/`D5b` **0 / 0** |
| pool/seal byte compare | `git diff --stat docs/evaluation/geometry/curved-v3/` **rỗng** |
| `git diff --check` | exit **0** |
| network / application call | **0** — mọi lượt qua stub |

Frontend **không chạy**: wave này không đổi file frontend nào.

## 10. Giới hạn — phải đọc

**① Trong lúc phát triển có ĐÚNG một test đỏ, và nó đỏ vì cây bẩn.**
`tests/geometry/test_holdout_readiness_7b.py::test_bao_cao_da_sinh_va_KHONG_TROI`
khẳng định báo cáo Phase 7B nói `READY_FOR_PHASE7B: NO` đúng khi có blocker, và
blocker duy nhất khi ấy là `CÂY LÀM VIỆC BẨN — niêm phong đòi cây sạch`. Bản đo
trước commit là **3554 passed / 1 failed**; sau commit, trên cây sạch, là
**3555 passed / 0 failed** (§9). Ghi cả hai vì con số ở §9 phải là bản đo trên
cây sạch, còn việc nó từng đỏ thì không nên giấu.

**② Bài chứng nhận dùng pool TỔNG HỢP.** Nó chứng minh **đường dây** — bộ ca
đến từ con dấu, manifest trước lượt gọi, guard trước mỗi lượt, băm nhất quán.
Nó **không** chứng minh gì về nội dung pool V3 thật, và không thể: đọc nội dung
ấy là việc của evaluator độc lập, sau khi rút.

**③ Provider stub trả JSON không parse được**, nên mọi ca dừng ở `analyze` —
1 application call/ca. Nhánh 8B được chứng minh riêng (`test_D3a`) bằng cách
stub hai stage để sinh lỗi `schema`. Tức: đường dây đã chứng minh, còn hành vi
của mô hình thì **chưa đo** — đó là việc của lượt live.

**④ `mong` chuẩn hoá ở loader, KHÔNG ở pool.** `POOL.json` giữ nguyên byte, và
phải giữ nguyên: sửa pool là làm lệch `pool_hash` và phá con dấu.

**⑤ Tái lập model vẫn `LIMITED`** — không đổi ở wave này. Alias
`gemini-2.5-flash`, không snapshot. Giới hạn đã khai ở policy `1.1.0`.

## 11. Điều kiện hoàn thành

```
LIVE_ENTRYPOINT_USES_SEALED_V3_POOL          YES
DEVELOPMENT_CORPUS_REACHABLE_FROM_LIVE_PATH  NO
POOL_MONG_NORMALIZED_AT_LOADER               YES
POOL_BYTES_CHANGED                           NO
MANIFEST_WRITTEN_BEFORE_FIRST_CALL           PROVED_BY_MAIN_ASYNC_TEST
IDENTITY_GUARD_BEFORE_EVERY_CALL             PROVED_BY_PROVIDER_EVENT_LOG
V3_CALL_BUDGET                               78
V3_LIVE_ENTRYPOINT_INTEGRATION               PASS
APPLICATION_LLM_CALLS                        0
CASES_DRAWN                                  NO
V3_SEED · V3_DA_RUT                          null · null
CANDIDATE_HASH_CHANGED                       NO
POOL_HASH_CHANGED · SEAL_CHANGED             NO · NO
RESEAL_PERFORMED                             NO
PRODUCT_CAPABILITY_CHANGED                   NO
```

## 12. RECOMMENDED_NEXT_ACTION

```
INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE
```

`EXTERNAL_SEED = 5324284654432805119` **vẫn chưa dùng**. Trình tự giữ nguyên
(`…_DECISION.md §15`), và nay `certify_acceptance_runner.py` chứng nhận **đường
chạy thật** chứ không chỉ một hàm nằm cạnh nó:

```bash
cd backend
.venv/Scripts/python.exe scripts/certify_acceptance_runner.py     # 3 nhãn PASS
.venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify
.venv/Scripts/python.exe scripts/seal_curved_v3.py --rut --seed 5324284654432805119
ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 \
  .venv/Scripts/python.exe scripts/run_curved_acceptance.py --out-dir <thư mục MỚI>
```

Phiên này là **phiên triển khai bộ đo** ⇒ không đủ điều kiện chạy lượt live.
