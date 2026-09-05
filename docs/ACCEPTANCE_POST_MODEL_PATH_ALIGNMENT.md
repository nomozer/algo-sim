# ACCEPTANCE_POST_MODEL_PATH_ALIGNMENT

> 2026-09-05. **`APPLICATION_LLM_CALLS = 0`** · `PRODUCT_CODE_CHANGED = NO` ·
> `CURRENT_CANDIDATE_CHANGED = NO` · `CACHE_VERSION_CHANGED = NO` ·
> `V3_SOURCE_ARTIFACTS_CHANGED = NO` · `V3_REEXECUTED = NO` ·
> `PRODUCT_CAPABILITY_CHANGED = NO`.
>
> Chỉ `backend/scripts` + `backend/tests` + `docs`. Candidate `93c47d9a…`
> verify exit 0 trước và sau.

## 1. ROOT_CAUSE

Runner acceptance tự dựng **một phép chiếu thứ hai** thay vì gọi thẩm quyền đã
có. Nó đọc đại lượng từ `outcome.envelope["scene3d"]` sau `verify_and_compile`
— nhưng `route` **cố ý** không dựng `scene3d` (hướng phụ thuộc một chiều;
`test_scene3d.py` cấm mọi module dưới `app/simulation` import nó). Người ghép
cảnh là `pipeline._dung_scene3d`, chạy **sau** route.

⇒ Phép chiếu ấy trả **rỗng cho mọi ca**, nên `dap_so_khop` không bao giờ True
được, kể cả với chương trình đúng tuyệt đối.

Điều đáng nói: thẩm quyền đúng **đã nằm sẵn trong scorer**, và docstring của nó
đã cảnh báo trước đúng lỗi này —

> *"KHÔNG chạm `scene3d`: ở đó đại lượng chỉ xuất hiện khi ca đã `servable`,
> nên đọc nó là trộn câu hỏi 'kết quả là gì' với 'hệ có dám phát không'."*
> — `acceptance_verdict.trich_ket_qua`

Runner chỉ không gọi nó.

## 2. Bản đồ thẩm quyền

| câu hỏi | thẩm quyền | nguồn |
|---|---|---|
| đáp số là gì | `acceptance_verdict.trich_ket_qua` | `outcome.final_memory` |
| cảnh dựng được không | `pipeline._dung_scene3d` | `build_scene3d` |
| phán quyết là gì | `acceptance_verdict.phan_loai` | 13 lớp, đọc `servable` |
| ca ÂM từ chối đúng chưa | `_cham_am` + `cham_ranh_gioi` (runner) | **không đổi** |

⚠️ Ca **âm** giữ nguyên đường cũ, có lý do: `phan_loai` trả lời *"chương trình
sai ở đâu"*, còn ca âm hỏi *"hệ có từ chối đúng chỗ không"* — hai câu khác nhau.
`acceptance_verdict.cham_ca_am` là thẩm quyền cho câu thứ hai nhưng nó đòi ca
khai `expected_codes`/`expected_stages`, mà pool V3 không khai. Nới bừa ở đây
sẽ đổi ý nghĩa của cột ca âm; wave này **không** đụng.

## 3. Bốn cột tách rời — `c7a` là fixture chuẩn

```
runtime_executable   True    interpreter chạy được
exact_answer_match   True    l=13 · V=100π · Sxq=65π, khớp trọn
scene3d_pass         True    3 quantity objects
postconditions_pass  False   hệ KHÔNG chứng thực được `distance(curved_solid)`
servable             False   ⇒ không dám phát
canonical_verdict    SYSTEM_VERIFICATION_FAILURE
legacy_verdict       CORRECT_EXECUTABLE_IR
```

Gộp bất kỳ cặp nào cũng xoá mất đúng thông tin `c7a` mang: một chương trình có
thể **đúng** mà hệ vẫn không dám phát, và khi ấy lỗi thuộc về **HỆ**.

### Canonical vs legacy

`run_curved_acceptance.phan_lop` (7 lớp) **không đọc `servable`**, nên nó mù với
`verification_gap` và gọi `c7a` là `CORRECT_EXECUTABLE_IR`. Nó được giữ dưới
`classification.legacy` **chỉ để chẩn đoán** — không tham gia ngưỡng, tổng hợp
hay product eligibility. Phán quyết thuộc `phan_loai`.

## 4. Hợp đồng sau sửa

`cham_ca_theo_duong_san_pham(ca, contract, spec, outcome, *, schema_ok)` trả ba
nhóm, và mỗi bản ghi ca của artifact mang chúng:

```json
{
  "execution":      {"runtime_executable": true, "postconditions_pass": false,
                     "servable": false, "stage_reached": "postconditions",
                     "failure_category": "verification_gap", "error_code": "…"},
  "results":        {"final_memory": {"l": "13", "V": "100π", "Sxq": "65π"},
                     "exact_result_authority": "outcome.final_memory",
                     "exact_answer_match": true, "scene3d_pass": true,
                     "scene_quantities": ["100π", "13", "65π"],
                     "expected": ["100π", "13", "65π"]},
  "classification": {"canonical": "SYSTEM_VERIFICATION_FAILURE",
                     "legacy": "CORRECT_EXECUTABLE_IR"}
}
```

`_chay_mot` phơi thêm năm trường lên bản ghi ca: `postconditions_pass` ·
`servable` · `scene3d_pass` · `canonical_verdict` ·
`legacy_runner_classification`.

**Repair policy không đổi** (`C5`): `LOP_SUA_DUOC` vẫn là
`("schema", "ir_static", "grounding")`, trần vẫn `tran_luot_goi_v3(13) = 78`.
Đổi thẩm quyền chấm đáp số **không** làm tăng số lượt gọi.

**Không dựng bản thứ hai của bất cứ thứ gì**: runner gọi thẳng
`pipeline._dung_scene3d`, tức dùng chung visual adapter, pacer, `build_scene3d`
và quantity presentation với sản phẩm. Nguồn Scene3D trong `backend/app` giữ
byte-identical.

## 5. Tests

`backend/tests/test_acceptance_post_model_path.py` — **24 test**.

| nhóm | nội dung |
|---|---|
| B (3) | route trả đáp số nhưng không trả scene3d · ranh giới import vẫn một chiều · hai bộ phân lớp lệch ở đúng `c7a` |
| D1 (2) | `c7a` bốn cột tách rời · đáp số đọc từ `final_memory` |
| D2/D3 (5) | 3 control canonical verdict (tái dùng fixture certifier) · ca servable bốn cột xanh · ca âm giữ đường riêng |
| D4 (2) | artifact mang đủ ba nhóm, JSON-hoá được |
| E (6) | tiêm lỗi |
| C5 (1) | repair policy không đổi |
| F (1) | tên trường artifact |
| G (3) | certifier: verdict mới · tiêm sai thẩm quyền ⇒ đỏ · readiness đòi cả hai nhãn |

Nền ĐỎ trước sửa: **10 failed / 8 passed**. Tám xanh sẵn là control — ba tái
hiện gốc rễ (B) và các fixture certifier vốn đã đúng.

### Fault injection

| # | tiêm | test đỏ |
|---|---|---|
| ① | đọc đáp số từ `scene3d` | `test_E1` — phép chiếu cũ rỗng |
| ② | bỏ `_dung_scene3d` | `test_E2` — `scene3d_pass` đỏ, **`exact_answer_match` vẫn xanh** |
| ③ | dùng `phan_lop` làm verdict | `test_E3` — `c7a` bị gọi là ĐÚNG |
| ④ | coi executable là servable | `test_E4` |
| ⑤ | gộp postconditions với exact match | `test_E5` |
| ⑥ | đổi đáp số kỳ vọng | `test_E6` |
| ⑩ | khôi phục phép chiếu cũ | `test_E10` |
| G2 | certifier: sai thẩm quyền đáp số | `test_G2` — verdict mạnh FAIL |
| G3 | certifier: đường hậu-model FAIL | `test_G3` — readiness `NO`, exit 1 |

② là phép tiêm quan trọng nhất: nó chứng minh hai cột **thật sự độc lập** —
mất cảnh không được làm mất đáp số.

## 6. Certifier

Thêm `chung_nhan_duong_hau_model` — chạy trọn đường trên **ca servable thật**
(`duong_1_dung`), rồi trên **ca verification-gap thật** (`duong_4`), chứng minh
sáu điều: ba nhóm đủ trường và JSON-hoá được · thẩm quyền đáp số là
`outcome.final_memory` · Scene3D dựng được · bốn cột xanh trên ca servable ·
verdict canonical đúng · bốn cột **tách được** trên ca verification-gap.

Provider giả phải đi tới một chương trình **executable**, nếu không bài chứng
nhận không chạm tầng hậu-model — đúng lỗi mà wave trước đã trả giá.

```
  RUNNER_CERTIFICATION   PASS
  V3_RUNNER_INTEGRATION  PASS   (phạm vi: hàm `mo_luot_do_v3`)
  V3_LIVE_ENTRYPOINT_INTEGRATION  PASS   (phạm vi: `main_async` — đường chạy THẬT)
  ACCEPTANCE_POST_MODEL_PATH_INTEGRATION  PASS   (phạm vi: đáp số · cảnh · phán quyết)
  APPLICATION_LLM_CALLS  0

  READY_FOR_INDEPENDENT_V3_LIVE  YES
  READY_FOR_FUTURE_CURVED_ACCEPTANCE  YES
```

`READY_FOR_FUTURE_CURVED_ACCEPTANCE` đòi **cả hai** nhãn tích hợp. Lý do: một
lượt đo đi đúng pool mà chấm sai tầng vẫn cho ra con số sai — V3 đã trả giá cho
đúng điều đó.

## 7. Đối chiếu V3

Bản đính chính lịch sử (`V3_PRODUCT_PATH_PARITY_CORRECTION`) và runner mới nói
cùng một điều về `c7a`:

```
C7A_EXACT_ANSWER_MATCH   = true
C7A_SCENE3D_PASS         = true
C7A_POSTCONDITIONS_PASS  = false
C7A_SERVABLE             = false
C7A_CANONICAL_VERDICT    = SYSTEM_VERIFICATION_FAILURE
```

Số V3 **giữ nguyên** — wave này không chạy lại gì:

```
V3_FIRST_ATTEMPT_SERVABLE       0/9
V3_EXACT_ANSWER_MATCH_CORRECTED 1/9
V3_SCENE3D_PASS_CORRECTED       1/9
V3_GENERAL_ACCEPTANCE           FAIL
```

Correction artifact tiếp tục là **lớp đính chính lịch sử**; runner mới áp cho
các lượt acceptance **tương lai**.

## 8. Identity

| | trước | sau | đổi |
|---|---|---|---|
| runner | `6570b57bd6ac1fe4…` | `3cabd2070f0a6bb7…` | **YES** |
| certifier | `ce0d44d9d38c6787…` | `bbbed77b5e104e3b…` | **YES** |
| scorer | `4f7cae906500e0b6…` | `4f7cae906500e0b6…` | NO |
| threshold policy | `460e0ce57a304872…` | `460e0ce57a304872…` | NO |
| attribution rubric | `d44f2b7c19b4904f…` | `d44f2b7c19b4904f…` | NO |
| policy loader | `d8edfe6c699deee8…` | `d8edfe6c699deee8…` | NO |
| candidate | `93c47d9a4ff9ffd2…` | `93c47d9a4ff9ffd2…` | NO (verify exit 0) |
| `CACHE_VERSION` | 79 | 79 | NO |

⚠️ **Đính chính một số của đề bài**: đề ghi `POLICY_LOADER_HASH = b51e936f…`.
Giá trị ấy **cũ** — nó đổi ở `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` khi
`measurement_policy.py` nhận thêm `chinh_sach_da_tieu`. Giá trị thật, đo từ
file, là `d8edfe6c699deee8…`, và nó **không đổi** ở wave này.

Ghi để V4 seal dùng sau: **runner `3cabd2070f0a6bb7…` · certifier
`bbbed77b5e104e3b…`**.

## 9. Gates

| | |
|---|---|
| `tests/test_acceptance_post_model_path.py` (MỚI) | **24 passed** |
| `test_v3_live_entrypoint_wiring` + `test_v3_product_path_parity` | **76 passed** (cùng lượt) |
| full backend pytest | **3621 passed** · 1 skipped · 1 deselected (1 đỏ là cổng "cây sạch", xanh sau commit) |
| `certify_acceptance_runner.py` | exit **0** · 4 nhãn PASS · 2 nhãn readiness YES |
| candidate verification | exit **0** — 89 file, `93c47d9a…` |
| V3 artifact + con dấu | `git status docs/evaluation/` **rỗng** |
| `git diff --check` | exit **0** |
| secret scan | sạch |

Frontend **không chạy**: không file frontend nào đổi.

## 10. Giới hạn

**① Ca âm chưa dùng thẩm quyền canonical.** `cham_ca_am` đòi
`expected_codes`/`expected_stages`; pool V3 không khai. Pool tương lai nên khai,
và khi ấy ca âm mới chuyển sang thẩm quyền chung được.

**② `legacy_runner_classification` vẫn còn.** Giữ để chẩn đoán và để so hai
thước; nó **không** tham gia ngưỡng. Nếu sau vài lượt không ai đọc, nên bỏ —
một trường không ai đọc là một trường sẽ trôi.

**③ Wave này sửa BỘ ĐO, không sửa hệ.** Lỗ chứng thực `distance(curved_solid)`
— thứ làm `c7a` không servable — **chưa sửa**. Nó vẫn là lỗi HỆ đang mở.

**④ Chưa có lượt live nào chạy qua runner mới.** Hợp đồng được chứng minh bằng
fixture tất định và replay; nó **chưa** được kiểm bởi một lượt đo thật.

**⑤ V3 vẫn đã tiêu.** Runner mới áp cho lượt sau, trên pool mới.

## 11. RECOMMENDED_NEXT_ACTION

```
CURVED_OBLIGATION_SURFACE_ALIGNMENT
```

Bộ đo nay đã thẳng hàng với sản phẩm ở cả hai tầng — pool và chấm điểm. Nút
thắt kế tiếp là thứ `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` §10① đã định vị
và chưa ai đóng: `analyze` phát nghĩa vụ `area` cho *"diện tích mặt cầu"*,
trong khi `area` chỉ nhận `polygon3|section|circle3` — mặt cong là
`lateral_area`. Nghĩa là ngay ca cầu đơn giản nhất vẫn chết ở cổng phủ, và mọi
thứ hai wave vừa rồi mở ra không tới được mô hình.
