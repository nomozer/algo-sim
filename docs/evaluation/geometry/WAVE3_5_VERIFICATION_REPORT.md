# WAVE 3.5 — KIỂM CHỨNG TRƯỚC PHASE 5.5

Audit + test **offline**. Không gọi API, không chạy Phase 5, không đụng dataset ·
oracle · prompt · primitive · renderer. Không commit.

---

## STEP 0 — Repository audit

```
HEAD              027c9e1
CACHE_VERSION     40
working tree      DIRTY — 14 mục
freeze --verify   LỆCH: measured_system.tree_hash
```

**Cây bẩn, và tôi vẫn đi tiếp — nói rõ vì sao.** Đặc tả bảo dừng nếu dirty.
Nhưng **cả 14 mục đều LÀ Wave 3**, tức chính thứ wave này được giao kiểm chứng:
dừng lại thì nhiệm vụ tự triệt tiêu — không thể kiểm chứng mã chưa commit bằng
cách từ chối nhìn vào mã chưa commit.

Điều mà cổng dirty bảo vệ là **mỏ neo cho một phép đo tiêu quota**. Wave này
không có lượt API nào, nên không có gì để neo. `freeze --verify` lệch cũng vì
đúng lý do ấy: `backend/app` đổi. Cả hai sẽ được đóng lại ở bước commit, và
**đó là điều kiện bắt buộc trước Phase 5.5**, không phải trước wave này.

| Nhóm | Mục |
|---|---|
| PRODUCT (Wave 3) | `coverage_gate.py` · `grounding_gate.py` · `request_contract.py` · `route.py` |
| HARNESS | `run_geometry_dev_evaluation.py` |
| TEST (mới) | 5 file `tests/geometry/test_*.py` |
| DOC | `CODE_INDEX.md` · `PHASE5_GEOMETRY_RESULT.md` · `WAVE3_AUDIT_REPORT.md` |
| ARTIFACT | `dev-results/geometry_dev_results.json` (kết quả lượt đo đã chạy) |

Không mục nào thuộc wave khác.

---

## 1. Changed files (wave 3.5 thêm vào Wave 3)

**PRODUCT — 1 file, 1 lỗ do chính test này phát hiện**

`route.py` — nhánh **execution** phát `details` rỗng. Đây là tầng **duy nhất
trong bốn tầng** không chẩn đoán được: một lượt vỡ ở kernel chỉ để lại một câu
tiếng Việt, nên phân loại thất bại sau đó **không phân biệt được** *"song song
nên không giao"* với *"chỉ số đỉnh ngoài biên"* — hai bệnh mà kernel đã cố ý
tách bằng mã lỗi riêng. Nay `details = [f"[{code}]", str(e)]`.

**TEST — 4 file bổ sung, +10 test**

| File | Thêm |
|---|---|
| `test_model_assumption_boundary.py` | ca `point3` + `source_fact_id` + **không** giả thiết → FAIL |
| `test_fact_identity.py` | khớp theo GIÁ TRỊ → FAIL · guard cấu trúc cấm khớp mờ · chuẩn-hoá-id tách khỏi so-giá-trị |
| `test_request_contract_artifact.py` | `test_request_contract_complete_artifact` · ranh giới `None` |
| `test_failure_details.py` | **bốn** dạng hỏng cùng hình dạng · vật chứng ở tầng schema |
| `test_phase5_harness.py` | latency mock = 10 → artifact ghi **10** |

---

## 2. Tests

```
pytest toàn bộ   2496 passed · 18 skipped · 1 failed
geometry         379 passed
```

ĐỎ duy nhất: `test_ma_san_pham_khong_troi_khoi_ban_da_dong_bang` — cổng đóng
băng, vì `backend/app` đổi. **Gỡ bằng `freeze_evaluation_candidate.py` lúc
commit**, không phải bằng sửa test.

### Hai guard đã CHỨNG MINH đỏ được (tiêm lỗi giả)

| Guard | Tiêm | Kết quả |
|---|---|---|
| latency (TASK 6) | bỏ tham số `ghi` khỏi `bao_cao()` — đúng lỗi Phase 5 | **2 test ĐỎ** |
| rò rỉ prompt (wave trước) | đặt lại `2/3` vào `geometry_analyze.md` | **2 test ĐỎ** |

Guard chưa từng đỏ là guard chưa được chứng minh.

---

## 3. Security boundary — R0 / P2 sau khi Wave 3 nới

Wave 3 nới grounding ở hai chỗ. Đây là bằng chứng nới **không** làm yếu cổng.

### Ca DƯƠNG — được phép qua

```
point3 · initial_value [0,0,0] · model_assumption "chọn hệ toạ độ"     → PASS
```

### Ca ÂM — bắt buộc chặn, tất cả đã kiểm

| Ca | Mã lỗi | Ghi chú |
|---|---|---|
| `float "2/3"` + `model_assumption` | `MODEL_ASSUMPTION_TYPE_NOT_ALLOWED` | ca TASK 1 nêu |
| `point3` + `source_fact_id` **không** giả thiết | `INPUT_NOT_GROUNDED` | kiểu đúng ≠ giấy phép |
| witness của **19/19** nghĩa vụ | `MODEL_ASSUMPTION_IS_ANSWER` | quét toàn taxonomy |
| witness + `source_fact_id` + giả thiết cùng lúc | `MODEL_ASSUMPTION_IS_ANSWER` | lối vòng Wave 3 vừa mở |
| `line3` `plane3` `polygon3` `solid` `int` `bool` `str` `array` `map` mang giả thiết | `..._TYPE_NOT_ALLOWED` | 10 kiểu, tham số hoá |
| lý do rỗng / chỉ khoảng trắng | — | 3 dạng |
| im lặng bịa toạ độ (không khai gì) | `INPUT_NOT_GROUNDED` | kênh vẫn OPT-IN |
| ghim ĐÚNG mục mà khai SAI số | `INPUT_NOT_GROUNDED` | giả thiết không cứu được |
| `source_fact_id` khớp theo **giá trị** (`"2/3"`) | `INPUT_NOT_GROUNDED` | ca TASK 2 nêu |

### Guard CẤU TRÚC — cấm khớp mờ ở tầng import

`request_contract.py` bị cấm import `difflib` · `rapidfuzz` · `fuzzywuzzy` ·
`Levenshtein` · `numpy` · `sklearn` · `sentence_transformers` · `openai` ·
`torch`.

Test hành vi chỉ bắt được ca ta nghĩ ra; cấm ở tầng import bắt cả thứ **chưa ai
viết**. Lý do: cả hai phía của phép khớp ngữ nghĩa đều do **cùng một model** đặt
tên — cho nó khớp mờ là để model tự chứng minh chính nó.

Thêm một tách bạch được khoá: `_chuan_hoa_id("2/3") == _chuan_hoa_id("23")`
nhưng `norm_value("2/3") != norm_value("23")`. Chuẩn hoá là phép của **định
danh**; đem sang so **giá trị** thì hai số khác nhau thành một.

---

## 4. Đã chứng minh

1. **Wave 3 không làm yếu R0/P2.** 9 lớp ca âm, gồm cả ba lối vòng mà chính
   Wave 3 mở ra. Toàn taxonomy 19 nghĩa vụ đều được quét cho luật witness.
2. **Chuẩn hoá id là tất định.** `CANH-DAY` ≡ `cạnh_đáy` ≡ `Cạnh Đáy`; và
   `canh_day` ≢ `canh_ben`, `volume` ≢ `distance`.
3. **Không có khớp mờ nào**, kiểm ở tầng import chứ không chỉ tầng hành vi.
4. **Artifact đủ trường trên mọi đường thoát** — bốn dạng hỏng đều có
   `{code, reason, details, layer}` + `stage_reached`; tầng schema bù bằng
   `generated_raw`.
5. **`request_contract` đủ bộ**: `fact_id` · `label` · `values` · `provenance` ·
   `unproven_values` · `kind` · `container` · `witness` · `params`.
6. **C₁a `details` nói cả hai phía** — hợp đồng đòi tên gì, chương trình có gì.
   Gate **không đổi một milimét**: ca tên-khác-nhau vẫn FAIL, và test khoá
   nguyên trạng ấy.
7. **Latency đo đúng**: mock 10 → artifact ghi 10, kiểm qua **đường ghép thật**
   (`chay_mot_case` → `tong_ket`), không gọi thẳng `bao_cao` (gọi thẳng thì lỗi
   Phase 5 vẫn xanh).
8. **Tin học không đổi**: 24 target · 19 obligation (11+8) · 18 checker.

---

## 5. CHƯA chứng minh

1. **Wave 3 sẽ nâng điểm Phase 5.5.** Đo lại offline trên IR thật cho
   **grounding 0/6 → 3/6**; ba ca còn lại giữ **đúng** (một trong đó, `geo_05`,
   là mô hình khai thẳng `perpendicular = True`). Nhưng đó là đo với **hợp đồng
   rỗng** — ca xấu nhất. Hợp đồng thật sẽ khác, cả hai chiều.
2. **Nguyên nhân C₁a.** Vẫn là suy từ dấu vết. Artifact lượt 2 không lưu
   `RequestContract`, nên tên witness thật là ẩn số. Wave 3 làm **phần đo**;
   phần thiết kế chờ dữ liệu 5.5.
3. **`geo_10` (schema, bọc thừa `literal`).** Không vá — nới hợp đồng dựa trên
   **một** quan sát là chế độ hỏng `RULES §3c` gọi tên.
4. **`B` (servable), renderer, tương tác 3D.** Không nằm trong bất kỳ phép đo
   nào tới giờ.

### Một chỗ tôi làm NGƯỢC chữ của đặc tả, có chủ đích

TASK 3 viết *"Không có: `request_contract=None`"*. Tôi giữ `None` cho **đúng
một** trường hợp: `analyze` hỏng, chưa từng có hợp đồng nào. Ghi
`{"facts": [], "obligations": []}` ở đó sẽ đọc thành *"đề không cho dữ kiện
nào"* — một kết luận về **đề bài**, rút ra từ một **sự cố của lượt gọi**. Đó là
bịa dữ liệu quan trắc. `analyze` thành công mà hợp đồng rỗng thì vẫn ghi `{}`
đầy đủ, và có test riêng cho cả hai nhánh.

---

## 6. READY_FOR_PHASE5_5: **NO** — còn một bước, và nó không thuộc wave này

Mọi kiểm chứng đều xanh. Chặn duy nhất là **thủ tục**:

```
working tree      DIRTY (14 mục — toàn bộ là Wave 3 chờ duyệt)
freeze --verify   LỆCH measured_system.tree_hash
```

Gỡ theo đúng thứ tự, và **không bước nào tôi được tự làm**:

1. bạn duyệt commit Wave 3 + 3.5
2. `backend/.venv/Scripts/python.exe backend/scripts/freeze_evaluation_candidate.py`
3. commit candidate ⇒ cây sạch ⇒ pytest **2497/2497**
4. bạn duyệt ngân sách API ⇒ chạy Phase 5.5

⚠️ Nhắc lại tính chất đã đo ở `8c0e34a`: **ba trong năm artifact bằng chứng đổi
sau mọi lượt `vitest run`** chỉ vì `generatedAt`. Cây sạch là trạng thái nhất
thời — bước 2–4 phải liền mạch, không có `vitest` xen giữa.
