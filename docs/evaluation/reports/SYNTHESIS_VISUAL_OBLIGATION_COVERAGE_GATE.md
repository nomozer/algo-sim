# SYNTHESIS_VISUAL_OBLIGATION_COVERAGE_GATE

> Nhánh `feat/photo-problem-to-scene` · 2026-09-20.
> START_HEAD `e6ca857` · commit mã `e1ded8e` · `main` giữ `085cae6` (không đổi).
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/synthesis-visual-obligation-coverage-gate/`.
> **0 request Gemini · 0 request mạng.**

```text
SYNTHESIS_VISUAL_OBLIGATION_COVERAGE_GATE = PASS
VISUAL_GATE_POSITION                      = pipeline._semantic_route_attempt, SAU _dung_scene3d, TRƯỚC _emit/envelope/cache
B02_DERIVED_MISSING_SECTION_RESULT        = REJECTED (VISUAL_OBJECT_MISSING)
POLYGON3_AS_SECTION_RESULT                = REJECTED (VISUAL_OBJECT_TYPE_MISMATCH)
VALID_SECTION_RESULT                      = SERVED (không đổi một byte)
VALID_CASE_BEHAVIOR_PARITY                = PASS (p1 · p3 · p4 · p5 vẫn `ok`)
CACHE_POLICY                              = B — BUMP BẮT BUỘC
CACHE_VERSION                             = 95 → 96
CANDIDATE_HASH                            = 544a0b56… → 8159d5a7…
MODEL_FACING_HASHES                       = 5/5 KHÔNG đổi một byte
TRACE_VERSION                             = synthesis-repair-trace/2 (giữ, thêm trường tuỳ chọn)
RAW_PROGRAM_STORED / RAW_SCENE_STORED     = NO / NO
FAULT_INJECTIONS                          = 7/7 bắt được · 7/7 hoàn nguyên trùng byte · 0 dấu tiêm
SECRET_LEAKS                              = 0
```

## 1. Kết luận

Hệ có một lớp thất bại mà **không cổng nào đang hỏi tới**: chương trình chạy trọn,
đáp số đúng tuyệt đối, envelope sạch — mà **vật đề bảo vẽ không có trong cảnh**.
B02 (2026-09-15) là ca đo được: `served`, ba đáp số đúng (`72` · `9` · `3√6`),
**0 vật `section`**.

Wave này thêm một cổng tất định chạy sau khi cảnh được dựng và trước khi kết quả
được đánh dấu `served`. Mỗi nghĩa vụ hợp đồng sinh một **nghĩa vụ trực quan**, và
cảnh phải mang chủ thể ấy **đúng kiểu · truy được xuất xứ · đúng topology**.

Cổng **chỉ HẠ, không bao giờ NÂNG**, và khi mọi nghĩa vụ được phủ nó trả về
**chính đối tượng cũ** — nên ca hợp lệ không đi qua một phép sao chép nào.

## 2. Vì sao luật chạy trên TẬP KIỂU, không trên `section`

Đây là chỗ một thiết kế hiển nhiên sẽ sai, và dữ liệu đã chặn nó **trước** khi
viết dòng mã đầu tiên. Từ `MULTICASE_BENCHMARK_MANIFEST.json`:

| ca | nghĩa vụ | thiết diện là gì | vật cảnh đúng |
|---|---|---|---|
| **B02** | volume · **area** · distance | đa giác | **`section`** |
| **B03** | volume · **area** | **đường tròn** | **`circle3`** |

Cả hai đều là *diện tích một thiết diện*, và hợp đồng của cả hai nói **giống hệt
nhau**: `area(container)`. Nên luật *"mọi `area` đều đòi một vật `section`"* sẽ
đánh trượt B03 — một ca hợp lệ.

Luật thật: `required_scene_kind` **dẫn xuất** từ `OBLIGATION_KINDS`, vốn tự dẫn
từ `measure_contract.BANG_PHEP_DO`. Mở một lượng đo cho kiểu mới là cổng **tự**
nhận kiểu ấy — không có bản sao nào để quên.

```
volume       → {solid, curved_solid}                     (không bao giờ đòi section)
area         → {polygon3, section, circle3, ellipse3}
lateral_area → {curved_solid}
section_matches → {section}   ← CHẶT hơn tầng kiểu hợp đồng, có chủ đích
```

`section_matches` ở tầng **kiểu hợp đồng** nhận cả `polygon3` (cố ý, để chương
trình sinh trước 2026-08-30 không rơi mức yếu). Ở tầng **vật trên màn hình** thì
không: frontend `deriveSectionSubEntities` chỉ nhận `type === "section"`. Hai câu
hỏi khác nhau được phép có hai câu trả lời khác nhau — đó chính là bệnh
`SCENE_TYPE_OR_PROVENANCE_MISMATCH`.

## 3. Khoảng trống hợp đồng — khai thẳng, không vá

`RequestContract` **không phân biệt được** "diện tích đa giác phẳng thường" với
"diện tích thiết diện". Khi nghĩa vụ nhận cả `section` lẫn `polygon3`, vật quan
sát được là `polygon3`, và không có `section_matches` nào phân xử ⇒
**`UNVERIFIABLE`**, route từ chối an toàn.

Không đoán theo tên biến, không dò chuỗi trên đề. Khai `COVERED` là đúng lỗi B02;
khai `UNCOVERED` là kết tội một chương trình có thể đúng. `UNVERIFIABLE` là câu
nói thật duy nhất.

⚠️ **Không sửa trong wave này**: sửa khoảng trống ấy là đổi lược đồ `analyze` ⇒
đổi **bề mặt mô hình** ⇒ phải đo lại. Ghi lại để wave sau quyết.

## 4. Vị trí cổng — và vì sao nó không thể nằm trong `route`

```
verify_and_compile → outcome (scene3d = None, Ô TRỐNG)
  ↓ pipeline._semantic_route_attempt
outcome.model_copy(scene3d = _dung_scene3d(spec, contract))
  ↓
CỔNG PHỦ NGHĨA VỤ TRỰC QUAN        ← wave này
  ↓
_emit("semantic_route")            → observer/trace nhận phán quyết ĐÃ sửa
  ↓
_chay_duong_hinh_hoc đọc servable  → _envelope_tu_route_sinh → status "ok"
  ↓
main.py: ghi cache CHỈ khi status == "ok"
```

`route` **bị cấm** biết tới `scene3d`: `test_KHONG_module_nao_o_TANG_DUOI_nhap_scene3d`
quét AST và cấm mọi file dưới `app/simulation` import nó. Cảnh là một **ô trống**
do `pipeline` đổ vào. Module mới **không import `scene3d`** — nó nhận cảnh dạng
`dict` thuần làm tham số, nên hướng phụ thuộc một chiều nguyên vẹn.

## 5. Cache — chính sách B, và đây là chiều NGƯỢC với các bump trước

Cache hit trả envelope **thẳng**, không chạy lại route, không chạy lại cổng nào:

```python
row = _cache_lookup(session, key)
if row:
    return {**json.loads(row.envelope_json), "cached": True, "source": "exact_cache"}
```

Bump **88** và **93** không cần dọn row nào vì chúng đổi `rejected → served`, mà
lời từ chối **chưa bao giờ được cache**. Wave này đổi **`served → rejected`** —
tức đúng lớp `status == "ok"`, **đúng loại envelope ĐƯỢC cache**. Row v95 có thật
và có hại.

Bằng chứng **row thật** (`CACHE_SAFETY_DECISION.json`): ghi một row `status="ok"`,
`policy_version="95"`, envelope mang cảnh thiếu vật ⇒ `_cache_lookup` trả `None`
sau bump. **Cửa sổ chứng**: chính row ấy dưới version hiện hành ⇒ HIT.

⚠️ **Năm băm model-facing KHÔNG đổi một byte** — bump này không thuộc hạng *"đầu
vào của mô hình đổi"*. Mô hình được hỏi y hệt; thứ đổi là hệ **chấp nhận câu trả
lời nào**.

## 6. Bộ đo đã sai BA lần trong wave này, cả ba tự bắt

Ghi lại vì đây là phần đáng giá nhất, đúng tinh thần `CLAUDE.md §2b 3b.

| # | lỗi | lộ ra nhờ |
|---|---|---|
| ① | **F1 không bắt được gì** — tháo hẳn lời gọi cổng khỏi `pipeline` mà 40 test vẫn xanh. Mọi test khi ấy gọi `VO.ap_dung` **trực tiếp**, nên chúng chứng minh cổng ĐÚNG chứ không chứng minh cổng ĐƯỢC GỌI | chính phép tiêm lỗi |
| ② | **`assert "T" not in json.dumps(...)` đỏ vì chữ `T` nằm trong `"EXACT"`** — một guard ĐỎ báo một lỗi KHÔNG tồn tại | đọc lại thông điệp đỏ thay vì tin nó |
| ③ | **`KIEU_CANH_HOP_LE` chép sai** `RENDER_HINT` (thiếu `vector3`, sai thứ tự) | sync-lock đỏ ngay lần chạy đầu |

① là lớp lỗi kho đã trả giá **hai lần** (certifier gọi thẳng `mo_luot_do_v3` trong
khi `main_async` chạy corpus khác). Bản sửa: hai test đi qua **đường chạy thật** —
quét AST buộc `_semantic_route_attempt` gọi cổng sau `_dung_scene3d`, và một lượt
`run_pipeline` end-to-end (0 mạng) với cảnh bị gỡ vật, kèm **cửa sổ chứng** là
lượt không gỡ vật vẫn `ok`.

② là lý do luật *"tên một ký tự không kiểm được bằng phép tìm chuỗi con"* nay có
test riêng, kèm cửa sổ chứng chứng minh phép đo **không mù**.

## 7. Hai dương tính giả đã đo được và đã sửa — ở LUẬT, không ở triệu chứng

Bản cổng đầu đánh trượt **ca hợp lệ đang được phục vụ**. Cả hai đều là câu hỏi
*"xuất xứ"* bị đặt quá hẹp:

- **p4 (trụ) · p5 (nón)** — chương trình đặt **bí danh** (`assign hình trụ = khối trụ`).
  `assign` không phải phép dựng nên vật bí danh không có `producer`; nó vẫn
  `origin="derived"` và `depends: ["khối trụ"]`, tức **truy được hoàn toàn**.
- **điểm do ĐỀ CHO** (`declare_point`) mang `origin="free"`, không `producer`,
  không `depends` — và đó **đúng**: nó không được dựng, nó được khai, xuất xứ của
  nó là chính đề bài.

Luật đúng: xuất xứ đạt khi có `producer` **hoặc** `depends` **hoặc** `sources`
**hoặc** `origin == "free"`. Cả hai ca có test hồi quy riêng.

## 8. Bằng chứng

| artifact | nội dung |
|---|---|
| `PRECHECK.json` | nhánh · HEAD · candidate · khoá cache · **lệch đã khai: Docker daemon KHÔNG chạy** |
| `VISUAL_GATE_INTEGRATION_AUDIT.json` | thứ tự parse → validate → route → scene → cổng → cache; bằng chứng cache hit đi vòng qua cổng |
| `VISUAL_OBLIGATION_CONTRACT.json` | hợp đồng có kiểu, từ vựng đóng, thứ tự kiểm |
| `B02_DERIVED_FIXTURE_COMPARISON.json` | 10 fixture `DERIVED_STRUCTURAL_FIXTURE`, trước/sau |
| `VALID_CASE_BEHAVIOR_PARITY.json` | p1 · p3 · p4 · p5 + 4 ca âm |
| `CACHE_SAFETY_DECISION.json` | chính sách B, row thật, cửa sổ chứng |
| `TRACE_AND_REDACTION_PROOF.json` | trường tuỳ chọn v2, đọc ngược v1/v2, 0 rò rỉ |
| `FAULT_INJECTIONS.json` | 7 phép tiêm, kể cả F1 thất bại lần đầu |
| `OFFLINE_GATES.json` | mọi cổng đã chạy + cổng cố ý KHÔNG chạy |
| `SECRET_SCAN.json` | 0 |

## 9. Giới hạn — phải đi kèm mọi con số của wave này

1. **Output live B02 KHÔNG phục hồi được** (`HISTORICAL_B02_UNCOVERED_OBLIGATION = NOT_RECOVERABLE`).
   Mọi fixture là `DERIVED_STRUCTURAL_FIXTURE`, **không** phải output lịch sử.
   Wave này **không** chứng minh cổng sẽ bắt đúng cái đã xảy ra ở lượt B02 — nó
   chứng minh cổng bắt **lớp thất bại** mà lượt ấy thuộc về.
2. **Không lượt provider thật nào chạy.** 0 request Gemini. Cổng chưa từng gặp một
   output mô hình mới.
3. **Khoảng trống hợp đồng còn nguyên** (§3): `area` một mình không nói được nó là
   thiết diện. Hệ quả: một bài *"tính diện tích đa giác phẳng"* hợp lệ sẽ nhận
   `UNVERIFIABLE`. Đây là từ chối **an toàn**, nhưng nó **là** một lớp từ chối mới
   trên các đề chưa từng đo.
4. **`cay_lam_viec_sach = false`** trong candidate đã đóng băng — xem §10.

## 10. Cây làm việc: một xung đột không thể đồng thời thoả

- §8 của đặc tả đòi **đóng băng candidate trên cây sạch**.
- §1 · §11 · §12 đòi **giữ nguyên** `D frontend/public/favicon.svg` (thay đổi của
  người dùng, **chưa commit**, cấm khôi phục/stage/commit).

Hai điều kiện loại trừ nhau: `freeze_evaluation_candidate.py` tính "sạch" bằng
`git status --porcelain` **toàn cây**. Wave chọn **giữ favicon** theo chỉ thị lặp
lại ba lần, nên candidate ghi `cay_lam_viec_sach: false`, và hai test đọc trạng
thái cây đang đỏ:

- `test_candidate_ghi_dung_commit_va_cay_sach`
- `test_bao_cao_da_sinh_va_KHONG_TROI` (blocker `CÂY LÀM VIỆC BẨN`)

⚠️ **Đã chứng minh đây KHÔNG phải hồi quy của wave**: dựng worktree tại START_HEAD
`e6ca857` và chạy `test_bao_cao_da_sinh_va_KHONG_TROI` ⇒ **1 passed**. Nó đỏ vì
**trạng thái cây**, không vì một dòng mã nào của wave.

**Quyết định thuộc về người dùng** — xem mục cuối.

```text
SECTION_PROVENANCE_NORMALIZATION = NOT_RUN
GEOMETRY_PRIMITIVE_COMPILER      = NOT_RUN
TOKEN_OPTIMIZATION               = NOT_RUN
MERGE_ALLOWED                    = NO
NEXT_ACTION                      = SECTION_PROVENANCE_NORMALIZATION
```
