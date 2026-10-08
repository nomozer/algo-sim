# ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS

> 2026-09-04. **`APPLICATION_LLM_CALLS = 0`** · `CASES_DRAWN = NO` ·
> `LIVE_V3_EXECUTED = NO` · `RESEAL_PERFORMED = NO` · pool **chưa đọc nội dung**.
> Sửa **chỉ** trong `scripts/` + `tests/` — ngoài `MEASURED_SYSTEM_PATHS`.

## 1. ROOT_CAUSE

Pre-draw guard của `CURVED_V3_LIVE_ACCEPTANCE` đo được: đề cho **đường kính**
`d = 26` thì `r = d/2` là bước **đúng về toán**. Nhưng:

```
static type của `arith(d,"/",2)`   = unknown
ô `radius` nhận                     = ('scalar','float','int')
⇒ stage = ir_static · AMBIGUOUS_FIRST_BINDING
⇒ phan_loai = MODEL_STATIC_FAILURE          ← QUY SAI TRÁCH NHIỆM
```

`SYSTEM_EXPRESSIVENESS_GAP` **không tồn tại** trong `LOP_PHAN_QUYET`. Bộ đo
không có ô nào để nói *"mô hình làm đúng, hệ không có đường"* — nên nó ghi vào
cột năng lực mô hình, đúng chiều sai mà cả tuyến probe này tồn tại để chặn.

## 2. ATTRIBUTION_CONTRACT

| tình huống | valid path | hành vi mô hình | lớp đúng |
|---|---|---|---|
| đề cho đường kính, cần `r=d/2`, IR không có typed-scalar path | **NO** | dùng phép toán ĐÚNG | `SYSTEM_EXPRESSIVENESS_GAP` |
| đề cho bán kính trực tiếp | **YES** | tạo binding mơ hồ | `MODEL_STATIC_FAILURE` |
| IR có đường hợp lệ | **YES** | chọn đường sai | lớp `MODEL_*` tương ứng |
| dữ kiện chưa grounded | *chưa xét* | dùng tên không nguồn | `MODEL_GROUNDING_FAILURE` |
| chưa đủ bằng chứng | **UNKNOWN** | bất kỳ | `ATTRIBUTION_UNRESOLVED` |

Năm điều kiện **đồng thời** cho `SYSTEM_EXPRESSIVENESS_GAP` (§B): yêu cầu toán
học hợp lệ · cần giá trị/thao tác IR không biểu đạt được · reachability chứng
minh không có đường · candidate chết đúng tại ranh giới ấy · không tồn tại đường
hợp lệ khác.

`ERR_RANG_BUOC_MO_HO` và cái tên `radius` **chỉ là dấu hiệu** — chúng không tự
đủ để kết luận. Chúng chỉ đủ để **từ chối kết luận** (xem §5).

## 3. VALID_PATH_PROOF

Dẫn từ **chữ ký**, không từ chuỗi lỗi. Đo bằng máy:

```
ô `radius` NHẬN: ('scalar','float','int')

phép SINH RA giá trị        → kiểu tĩnh
  arith · unary · literal · var → unknown
  measure                       → scalar          ← DUY NHẤT trả `scalar`
  midpoint · project_onto · …   → point3/line3/plane3/…

phép nhận VÔ HƯỚNG và trả VÔ HƯỚNG      : KHÔNG CÓ
…và trong số ấy, kiểu mà `radius` nhận  : KHÔNG CÓ
measure.of nhận vô hướng?                : False
  (nhận: circle3 curved_solid line3 plane3 point3 polygon3 section solid vector3)

⇒ VALID_PATH_EXISTS(vô hướng grounded → BIẾN ĐỔI → radius) = NO
```

**Trục phân biệt** là `can_bien_doi`, không phải tên ô:

```
đề cho THẲNG bán kính  → can_bien_doi=False → kiểu nguồn ∈ kiểu đích → YES
đề cho ĐƯỜNG KÍNH      → can_bien_doi=True  → reachability rỗng      → NO
không có bằng chứng    →                                             → UNKNOWN
```

## 4. IMPLEMENTATION

Tại authority của acceptance verdict (`scripts/acceptance_verdict.py`):

| symbol mới | vai trò |
|---|---|
| `SYSTEM_EXPRESSIVENESS_GAP` | lớp: hệ không có đường |
| `ATTRIBUTION_UNRESOLVED` | lớp: chưa đủ bằng chứng để quy trách nhiệm |
| `YeuCauNangLuc` | **input contract** — khai bằng KIỂU, không bằng đề bài |
| `duong_hop_le_ton_tai` | `YES`/`NO`/`UNKNOWN`, dẫn từ chữ ký |
| `_phep_bien_doi_giu_kieu` | reachability trên `_CHU_KY` + `BANG_PHEP_DO` |
| `o_vo_huong_bi_rang_buoc_mo_ho` | nhận diện HÌNH DẠNG, chỉ để **từ chối** kết luận |

```
NEW_MEASUREMENT_AUTHORITIES = 1   (YeuCauNangLuc + predicate, cạnh scorer)
NEW_PRODUCT_AUTHORITIES     = 0
```

`YeuCauNangLuc` cố ý **không** chở đề bài, đáp số hay case id — bộ đo không được
nhận ra một ca bằng nội dung, chỉ bằng hình dạng năng lực. `kieu_o_dich` dẫn từ
`_TOAN_HANG_LENH`, nên thêm một ô vô hướng sau này là quy tắc **tự nhận**.

### Thứ tự ưu tiên (§D5) — một quyết định, không ngẫu nhiên

```
schema hỏng                    → MODEL_SCHEMA_FAILURE
servable                       → CORRECT_SERVABLE_RESULT
mã lỗi hệ (coverage/verify/…)  → SYSTEM_*
grounding                      → MODEL_GROUNDING_FAILURE      ← TRƯỚC quy tắc năng lực
ir_static | structural_coverage:
    valid_path = NO            → SYSTEM_EXPRESSIVENESS_GAP
    valid_path = UNKNOWN + hình dạng khoảng trống
                               → ATTRIBUTION_UNRESOLVED
ir_static                      → MODEL_STATIC_FAILURE
binding / execution / …        → như cũ
```

`grounding` đứng **trước**: một dữ kiện chưa truy được về đề thì câu hỏi *"hệ có
đường không"* còn chưa đặt ra được — chương trình đang nói về một bài KHÁC. Che
nó bằng lớp năng lực là xoá mất lớp lỗi R0.

### Mặc định khi KHÔNG có bằng chứng

Không bằng chứng **và** thất bại mang hình dạng khoảng trống (ràng buộc mơ hồ
nuôi một ô đòi vô hướng) ⇒ `ATTRIBUTION_UNRESOLVED`. Ngoài hình dạng ấy,
`ir_static` vẫn là lỗi soạn thảo như trước.

Đo trước khi chọn mặc định này: **0 artifact lịch sử** có `stage=ir_static`, nên
nó **không xếp lại** một dòng lịch sử nào.

## 5. FALSE_POSITIVE_GUARDS

Mệnh đề trung tâm, `test_E2f`: **cùng một chương trình, hai bằng chứng khác
nhau ⇒ hai verdict khác nhau.**

```
_spec(CHIA_DOI) + yc(can_bien_doi=True)  → SYSTEM_EXPRESSIVENESS_GAP
_spec(CHIA_DOI) + yc(can_bien_doi=False) → MODEL_STATIC_FAILURE
```

Bảy guard chống dương tính giả: bán kính trực tiếp + `arith` mơ hồ → lỗi model ·
quên khai vô hướng → lỗi model · biến chưa grounded → grounding · biểu thức mơ
hồ **không** nuôi ô radius → không được hưởng lớp chưa-kết-luận · chương trình
hợp lệ vẫn `CORRECT_SERVABLE_RESULT` · lớp hệ khác giữ nguyên ưu tiên · không
bằng chứng + không hình dạng → **không** system gap.

## 6. FAULT_INJECTION

| # | tiêm | kỳ vọng | thực tế |
|---|---|---|---|
| 1 | gỡ lớp khỏi taxonomy | guard đỏ | ✅ `test_F1` |
| 2 | ép mọi ràng buộc mơ hồ thành system gap | chống-dương-tính-giả đỏ | ✅ `test_F2` |
| 3 | bỏ kiểm `valid_path_exists` | negative control đỏ | ✅ `test_F3` |
| 4 | biến `UNKNOWN` thành `NO` | test chưa-kết-luận đỏ | ✅ `test_F4` |
| 5 | đặt năng lực TRƯỚC grounding | guard grounding đỏ | ✅ `test_F5` |
| 6 | gỡ trường bắt buộc của evidence | hợp đồng đỏ | ✅ `test_F6` |
| 7 | khôi phục scorer cũ | guard đường kính đỏ | ✅ `test_F7` — trả lại `MODEL_STATIC_FAILURE` |

Cả bảy nằm **trong suite** (`monkeypatch`), không phải một lần thử tay.

## 7. HISTORICAL_RECLASSIFICATION

Chấm lại mọi `final.json` có cả contract lẫn chương trình (**4 artifact**), bằng
scorer mới, **không** truyền bằng chứng — đúng cách runner cũ gọi:

| artifact | lớp GHI trong artifact | scorer mới | nguyên nhân |
|---|---|---|---|
| `ball_1` | `SYSTEM_VERIFICATION_FAILURE` | `CORRECT_SERVABLE_RESULT` | `VOLUME_VERIFICATION_BRIDGE` (cache 71) |
| `ball_1` | `MODEL_FIRST_BINDING_FAILURE` | `CORRECT_SERVABLE_RESULT` | `SCALAR_FACT_VISIBILITY` (cache 72) |
| `cylinder_2` | `SYSTEM_COVERAGE_FAILURE` | `MODEL_COMPOSITION_FAILURE` | đính chính classifier `1b2479a` |
| `circumsphere` | `MODEL_COMPOSITION_FAILURE` | `CORRECT_SERVABLE_RESULT` | `OBLIGATION_BINDING_CONTRACT` (cache 75) |

**Không thay đổi nào đến từ wave này.** Bằng chứng: hai lớp mới
(`SYSTEM_EXPRESSIVENESS_GAP`, `ATTRIBUTION_UNRESOLVED`) **không xuất hiện** trong
kết quả chấm lại. Bốn khác biệt trên đều là hệ **đã thật sự sửa** ở các wave
trước, và đó là lý do artifact lịch sử phải giữ nguyên byte: điểm số lịch sử gắn
với hệ tại thời điểm chúng, không gắn với hệ hôm nay.

`HISTORICAL_ARTIFACTS_CHANGED = NO` — chỉ chấm lại trong bộ nhớ.

## 8. MEASUREMENT_IDENTITY_DELTA

```
scorer          98cc19c898b73a52 → 4f7cae906500e0b6   ĐỔI  (đúng mục tiêu wave)
runner          11e4b6200f817593                       KHÔNG ĐỔI
certifier       07c550f524f3387f                       KHÔNG ĐỔI
candidate       a696200e8f8c668c                       KHÔNG ĐỔI
pool_hash       36c2153ecefd2dbf                       KHÔNG ĐỔI
cache_version   78                                     KHÔNG ĐỔI
grammar_card · analyze_schema · synthesis_schema · prompts · capability
                                                        KHÔNG ĐỔI
seal            seed=null · da_rut=null · system==candidate ✅
```

Scorer nằm ngoài `MEASURED_SYSTEM_PATHS` ⇒ **không phát sinh reseal**. Runner
certification vẫn PASS sau khi scorer đổi — certifier không ghim scorer hash,
nên không cần cập nhật expected identity.

⚠️ Hệ quả phải khai: vì certifier **không** ghim scorer hash, việc scorer đổi
giữa reseal và lượt live sẽ **không** bị certification bắt. `RunManifest` cũng
chưa ghi scorer hash. Đây là một trong hai khiếm khuyết phụ mà handoff đã nêu và
`V3_THRESHOLD_POLICY` phải đóng cùng.

## 9. TEST_RESULTS

| gate | lệnh | exit | kết quả |
|---|---|---|---|
| scorer expressiveness (mới) | `pytest tests/test_scorer_expressiveness_class.py` | 0 | **27 pass** |
| acceptance-runner-integrity | `pytest tests/test_acceptance_runner_integrity.py` | 0 | **43 pass** |
| runner certification | `certify_acceptance_runner.py` | 0 | PASS, 0 lượt gọi |
| candidate verification | `freeze_evaluation_candidate.py --verify` | 0 | `a696200e…` |
| cache identity | `pytest tests/test_cache_identity.py` | 0 | **15 pass** |
| full backend | `pytest -q` | 0 | **3430 pass**, 1 skip, 1 deselect |
| `git diff --check` | — | 0 | sạch |

Frontend/build **kế thừa** tại cùng candidate `a696200e…` (698 pass / 51 file,
build PASS): wave này không chạm một byte nào của mã sản phẩm.

## 10. LIMITATIONS

- **`can_bien_doi` chưa dẫn được từ metadata cấu trúc của V3.** Lược đồ pool là
  `{cong_thuc, de, hinh, id, loai, mong, o}`, và tham số công thức mặt cầu luôn
  tên `R` — nên metadata **không** phân biệt được *"đề phát biểu bán kính"* với
  *"đề phát biểu đường kính"*. Chỉ `de` phân biệt được, và `de` chỉ đọc được
  **sau khi rút** (§C mục 5). Nên ở lượt live, bằng chứng phải sinh sau draw từ
  problem text, hoặc dùng adjudication theo rubric đã khoá (§C mục 6). Không có
  ⇒ `ATTRIBUTION_UNRESOLVED`, không đoán.
- Predicate xét **kiểu**, không xét **giá trị**: nó chứng minh được "không có
  phép nào giữ kiểu", không chứng minh được "phép này cho đúng con số".
- `certify_acceptance_runner` và `RunManifest` **chưa ghim scorer hash** (§8).
- Quy tắc chỉ phủ hai giai đoạn `ir_static` và `structural_coverage`. Khoảng
  trống năng lực lộ ra ở `execution` sẽ vẫn rơi vào lớp cũ.

## 11. RECOMMENDED_NEXT_ACTION

```
V3_THRESHOLD_POLICY
```

Blocker ② của handoff đã đóng có bằng chứng chạy được. Blocker ③ (không có
ngưỡng nào cho V3) vẫn nguyên, và nó phải đóng **trước** khi biết kết quả —
kèm theo, đóng luôn hai khiếm khuyết phụ: ghim scorer hash + threshold hash vào
`RunManifest` và certifier, và ghim snapshot model thay cho alias.

Blocker ① (evaluator độc lập) vẫn cần một phiên/người khác.

---

```
DIAMETER_DERIVED_RADIUS_CLASS_BEFORE      MODEL_STATIC_FAILURE
DIAMETER_DERIVED_RADIUS_CLASS_AFTER       SYSTEM_EXPRESSIVENESS_GAP  (có bằng chứng)
                                          ATTRIBUTION_UNRESOLVED     (không bằng chứng)
DIRECT_RADIUS_BAD_PROGRAM_CLASS           MODEL_STATIC_FAILURE
UNGROUNDED_RADIUS_CLASS                   MODEL_GROUNDING_FAILURE
UNKNOWN_VALID_PATH_CLASS                  ATTRIBUTION_UNRESOLVED

SYSTEM_EXPRESSIVENESS_GAP_ADDED           YES
ATTRIBUTION_UNRESOLVED_ADDED              YES
CLASSIFICATION_EVIDENCE_STRUCTURED        YES  (YeuCauNangLuc)
FALSE_POSITIVE_GUARDS                     7
HISTORICAL_ARTIFACTS_CHANGED              NO

SCORER_HASH_BEFORE                        98cc19c898b73a52…
SCORER_HASH_AFTER                         4f7cae906500e0b6…
RUNNER_HASH_BEFORE / AFTER                11e4b6200f817593… / không đổi
RUNNER_CERTIFICATION                      PASS

CANDIDATE_HASH_BEFORE / AFTER             a696200e8f8c668c… / không đổi
CACHE_VERSION_BEFORE / AFTER              78 / 78
POOL_HASH_BEFORE / AFTER                  36c2153ecefd2dbf… / không đổi
SEAL_CHANGED                              NO
V3_SEED                                   null
V3_DA_RUT                                 null

APPLICATION_LLM_CALLS                     0
CASES_DRAWN                               NO
LIVE_V3_EXECUTED                          NO
PRODUCT_CAPABILITY_CHANGED                NO
WORKING_TREE                              CLEAN
```
