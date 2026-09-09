# THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW

**Ngày:** 2026-09-09 · **Loại wave:** rà soát tài liệu · **0 lượt gọi model**

```
OBJECTIVE_SOURCE            = docs/THESIS_DRAFT.md §3 · §4 · §6 · §1.6 · §1.7
OBJECTIVES_REVIEWED         = 5   (MT1–MT5) + 7 đóng góp (ĐG1–ĐG7)
RQS_REVIEWED                = 5   (RQ1–RQ5, ma trận ĐĂNG KÝ TRƯỚC)
CLAIMS_REVIEWED             = 29  (5 MT · 7 ĐG · 5 RQ · 9 C · 3 phát biểu phạm vi)

PROVED_ON_FROZEN_BENCHMARK  = 13
PARTIAL                     = 8
NOT_MEASURED                = 2
OUT_OF_SCOPE                = 2
CONTRADICTED                = 4
NOT_LOCATED                 = 0

DOCUMENTATION_CORRECTIONS   = 4   (D-1 … D-4; ba đính chính viết vào bản thảo)
DISPLAY_NAME_FOLLOW_UP      = OPTIONAL_POLISH
RESPONSE_CONTRACT_FOLLOW_UP = REQUIRED_BEFORE_FINAL_DEMO

APPLICATION_LLM_CALLS       = 0
REAL_PROVIDER_CALLS         = 0
PRODUCT_CODE_CHANGED        = NO
MODEL_FACING_CHANGED        = NO
CACHE_VERSION_BEFORE/AFTER  = 94 / 94
CANDIDATE_BEFORE/AFTER      = d72db7c3… / d72db7c3…
WORKING_TREE                = sạch
NEXT_ACTION                 = PRODUCT_RESPONSE_CONTRACT_ALIGNMENT
```

Ma trận đầy đủ: **`docs/thesis/CLAIM_EVIDENCE_MATRIX.md`**.

---

## 1. Nguồn mục tiêu — tìm thấy, không phải dựng ra

`rg` trên `docs/` cho ra **một** văn bản mang mục tiêu học thuật:
`docs/THESIS_DRAFT.md` — §3 *Mục tiêu nghiên cứu* (tổng quát + 5 mục tiêu cụ
thể), §4 *Đối tượng và phạm vi*, §6 *Đóng góp chính* (7 mục), §1.6 *phát biểu
bài toán*, §1.7 *"Điều đề tài có / không chứng minh"*.

`OBJECTIVE_SOURCE ≠ NOT_LOCATED`. Không mục tiêu nào phải suy từ tên file, từ
ledger kỹ thuật, hay từ trạng thái hiện tại của hệ.

Thứ tự thẩm quyền áp dụng: bản thảo → Chương 1 → ma trận acceptance đã đăng ký
→ Chương 4–5 → ledger. Ledger kỹ thuật **không** được dùng làm nguồn đặt mục
tiêu, kể cả khi nó đúng hơn.

## 2. Mọi số bàn giao đã ĐO LẠI, không mặc định

Không con số nào ở §3 của đặc tả wave được lấy nguyên; tất cả tra lại từ artifact
có băm hoặc chạy lại công cụ tất định.

| số bàn giao | đo lại được | nguồn |
|---|---|---|
| 7 ca dương · 2 ca âm | 7 · 2 ✓ | `FINAL_SUMMARY.json` |
| first-attempt servable 6/7 | `FIRST_ATTEMPT_SERVABLE = 6` ✓ | `FINAL_SUMMARY.json` |
| eventual servable 7/7 | `FINAL_SERVABLE = 7` ✓ | `FINAL_SUMMARY.json` |
| exact values 12/12 | **12** mục `quantities_SUA`, **12** khớp ✓ | `SCORING_CORRECTION.json` |
| negative fail-closed 2/2 | `NEGATIVE_FAIL_CLOSED = 2` ✓ | `FINAL_SUMMARY.json` |
| silent wrong answer 0 | `SILENT_WRONG_ANSWER_COUNT = 0` ✓ | `FINAL_SUMMARY.json` |
| dynamic hidden lines PASS | 23/23 phép kiểm, 0 ngoại lệ ✓ | `HIDDEN_LINE_MATRIX.json` |
| UI 7/7 dương · 2/2 âm | 66/66 phép kiểm, 7 · 2 ✓ | `UI_ACCEPTANCE_MATRIX.json` |
| visual fidelity `PARTIAL` | 39/41 ✓ | `AFTER_VISUAL_MATRIX.json` |
| `DISPLAY_NAME_PASS = 10/12` | 2 ca đỏ (`p6`, `p7`: *"Diện tích «đối tượng»"*) ✓ | `AFTER_VISUAL_MATRIX.json` |
| `STABILITY_UNDER_ACCEPTANCE` | `NOT_MEASURED` ✓ | `FINAL_SUMMARY.json` |
| `PRODUCT_DEPLOYMENT_READY` | `NOT_CLAIMED`; `PRODUCT_PROMOTION_ELIGIBLE = NO` ✓ | `FINAL_SUMMARY.json` |
| tròn xoay tổng quát · boolean ngoài phạm vi kiến trúc | chứng minh **vắng mặt**, `ABSENCE_PROOF 2/2` ✓ | `CAPABILITY_MATRIX.json` |
| feature development đã đóng | `FEATURE_SCOPE_COMPLETE = YES` ✓ | `CAPABILITY_MATRIX.json` |

Cộng thêm hai phép chạy lại tất định trong wave này:
`doi_chieu_ket_qua_cuoi.py` → `DOCUMENTATION_INPUT_CONSISTENCY = PASS`, 0/31
trường lệch, 12/12 đáp số; `scene3d_world_oracles.py` → **7/7**, tolerance 0.

## 3. Bốn tuyên bố ĐÃ TRÔI

### D-1 · Ma trận đăng ký ghi "11 đại lượng", artifact nói **12**

`CLAIMS_MATRIX` / Bảng 2 ghi mẫu số RQ2 là *"11 đại lượng / 7 ca"*.
`SCORING_CORRECTION.json` có **12** mục `quantities_SUA`, tất cả
`exact_answer_match = true`.

**Không sửa** văn bản đăng ký trước — sửa nó sau khi thấy kết quả là xoá đúng
thứ nó tồn tại để giữ. Đính chính đã ghi ở Chương 4 Bảng 4.6 và ở ba sổ vận hành
từ wave `PRODUCT_UI_RESULT_RENDERING`.

### D-2 · Bảng "ngoài phạm vi" của bản thảo đã bị bằng chứng bác

`THESIS_DRAFT §4` khai **mặt cong**, **khối không lồi** và **phương trình mặt
phẳng** là NGOÀI phạm vi; tóm tắt khai *"chỉ khối đa diện lồi, không mặt cong"*.
Lượt đánh giá cuối **phục vụ đúng cả ba**: `p3` cầu, `p4` trụ, `p5` nón, `p2` đáy
ngũ giác **lõm**, `p6` mặt phẳng cho bằng phương trình `2x − z + 12 = 0`, cộng
`p6`/`p7` thiết diện elip xiên.

**Đã ghi đính chính bên trên bảng gốc**; bảng gốc giữ nguyên. Phạm vi ngoài còn
đúng thu lại còn ba dòng cuối, cộng hai họ ngoài phạm vi vì **lý do kiến trúc**.

### D-3 · `product_capability.py` ghi lý do *"MÔ HÌNH: chưa đo"*

Ba dòng khối cong (cầu · trụ · nón) mang lý do *"hệ: Phase 2 CLOSED · offline: 2
bài mẫu · **MÔ HÌNH: chưa đo**"*. Mô hình **đã được đo** ở lượt cuối: 5/5 họ
phục vụ đúng.

⚠️ **Trạng thái `foundation_only` vẫn ĐÚNG** — `n = 1` mỗi họ không đủ để bật cho
người học. Chỉ **chuỗi lý do** đã cũ. Sửa nó chạm `backend/app` ⇒ đổi candidate ⇒
**ngoài phạm vi wave này** (§1 cấm sửa mã sản phẩm). Chuyển thành nợ, ghi ở
`CLAIM_EVIDENCE_MATRIX §D-3`.

### D-4 · Bản thảo có **hai thân Chương 4 rời nhau**

`THESIS_DRAFT` mô tả **bốn lượt niêm phong, n = 4–6**, và **không nhắc một chữ
nào** về lượt đánh giá cuối (`rg` cho 0 kết quả). `docs/thesis/CHAPTER_4` mô tả
lượt cuối, 9 ca, n = 1 mỗi họ.

Đã ghi đính chính ở tóm tắt và ở §1.7 của bản thảo. **Hợp nhất hai thân** là
việc của wave tích hợp bản thảo, không phải của wave rà soát này.

## 4. Một khoảng trống truy xuất đã vá trong wave này

`PRODUCT_UI_RESULT_RENDERING_AND_DEMO_ACCEPTANCE.md` ghi *"6/6 phép tiêm đỏ đúng
chỗ"*, nhưng `UI_ACCEPTANCE_MATRIX.json` trên đĩa ghi `FAULT_INJECTIONS = 0` —
lượt chạy **sạch** cuối cùng đã ghi đè artifact của lượt có `--faultcheck`. Con
số trong báo cáo **đúng** nhưng **không truy được** tới artifact nữa.

Đã chạy lại `certify-product-ui-rendering.mjs --faultcheck` (0 lượt gọi model):
artifact nay ghi `FAULT_INJECTIONS = 6`, `FAULT_INJECTIONS_PROVEN_RED = 6`,
`66/66` phép kiểm. Đây đúng lớp lỗi cổng §10 tồn tại để chặn: *một con số dùng
được nhưng không dẫn về đâu*.

## 5. Ranh giới đã giữ

**Khả năng sinh.** Kết luận chỉ đóng khung trong *"các ca của benchmark cuối"*.
Không câu nào dùng một lượt trên mỗi ca để nói mô hình ổn định trên mọi đề cùng
họ. Mọi chỗ nhắc 6/7 hay 85,7 % đều in kèm mẫu số và kèm `n = 1`.

**Tính đúng — năm mức tách riêng.** đúng đáp số (12/12) · đúng hình học (oracle
không gian thế giới 7/7, tolerance 0) · đúng bước dựng (7/7 `TRACE_PASS`) ·
đúng trace (song ánh khung ⇔ bước) · đúng Scene3D (7/7 `SCENE3D_PASS`). Con số
"12/12" chỉ được ghi sau khi đối chiếu trực tiếp với `SCORING_CORRECTION.json`.

**Hiển thị.** Hidden-line động **PASS** theo oracle pháp tuyến độc lập và phép
đo điểm ảnh; quy ước nét thấy–khuất đổi theo camera trên `p3`/`p6`/`p7` (41–50
trên 72 điểm mẫu đổi vai sau khi xoay). Nhưng **visual fidelity tổng thể vẫn
`PARTIAL`** — 39/41 — và bản này **không** đổi nó thành PASS. Chưa đo zoom cực
trị · chưa có oracle độc lập tương đương cho thiết diện đa diện · visual review
do chính tác giả wave thực hiện · display name còn **10/12**.

**Phạm vi hình học.** Không dùng câu *"đã hỗ trợ đầy đủ mọi hình học"*. Ba nhóm
tách bạch ở `CLAIM_EVIDENCE_MATRIX §F`: đã chứng minh (10 họ) · `foundation_only`
(khối cong, lõm, thiết diện xiên) · ngoài phạm vi vì kiến trúc (tròn xoay tổng
quát, ghép–bù boolean).

**Danh tính phép đo.** Candidate **lịch sử** `d72db7c3…` (ghim trong hợp đồng
`created_before_live_run = true`) và candidate **hiện tại** `d72db7c3…` được ghi
thành **hai trường**, dù đang trùng nhau. Không cập nhật giá trị lịch sử.

## 6. Hai follow-up — quyết định dẫn nguyên văn mục tiêu

### `DISPLAY_NAME_AUTHORITY_ELLIPSE_AND_CURVED_KIND` → **OPTIONAL_POLISH**

Mục tiêu chính thức, `THESIS_DRAFT §1.6`, đầu ra khi thành công:

> *"(i) chuỗi bước dựng hình tất định, (ii) **các đại lượng được hỏi, tính bằng
> số học chính xác**, (iii) một cảnh ba chiều tua được theo bước, mỗi vật mang
> xuất xứ."*

Ba mục tiêu cụ thể liên quan (MT2, MT4) và hai đóng góp (ĐG4, ĐG5) đòi **giá trị
số chính xác** và **cảnh dẫn xuất từ vết** — **không** đòi chất lượng tên gọi.
`rg` trên toàn bản thảo không tìm thấy một cam kết nào về nhãn/tên đại lượng cho
người học; mọi cam kết "tiếng Việt cho người học" đều nằm ở **đường từ chối**
(§1.6, §3.9), không ở đường phục vụ.

Nhãn *"Diện tích «đối tượng»"* là một khiếm khuyết trình bày thật, nhưng nó
**không chạm mục tiêu nào đã đăng ký**. `10/12` được giữ nguyên và khai rõ.

### `PRODUCT_RESPONSE_CONTRACT_ALIGNMENT` → **REQUIRED_BEFORE_FINAL_DEMO**

Mục tiêu chính thức, `THESIS_DRAFT §1.6`:

> *"**Đầu ra, khi không thành công:** một **từ chối có cấu trúc** — nêu **giai
> đoạn dừng, loại thất bại, mã lỗi**, và một thông điệp tiếng Việt cho người
> học."*

Và `§3.9` nhắc lại nguyên văn:

> *"Mỗi chỗ dừng trả một từ chối *có cấu trúc*: **giai đoạn dừng + loại thất bại
> + mã lỗi** + thông điệp tiếng Việt cho người học."*

Đo được trên ca âm `n1` của lượt cuối:

| trường cam kết | `n1` | `n2` |
|---|---|---|
| giai đoạn dừng (`stage_reached`) | **`null`** ✗ | `structural_coverage` ✓ |
| loại thất bại (`failure_category`) | `geometry_generation_failed` ✓ | ✓ |
| mã lỗi (`error_code`) | **`null`** ✗ | `requested_operation_uncovered` ✓ |
| thông điệp tiếng Việt | ✓ | ✓ |

`n1` giao **hai trên bốn** trường mà mục tiêu cam kết. Hành vi fail-closed vẫn
đúng (không phát đại lượng nào), nhưng **hợp đồng phản hồi không giao đủ thứ đã
hứa** — và đó là một mục tiêu đã đăng ký, không phải một mong muốn thêm.

Đây cũng là chỗ chặn bản vá giao diện của hai wave trước: thiếu `error_code`,
tầng trình bày **không có gì để đọc** nên `n1` vẫn nhận câu gợi ý chung.

**Kết luận:** một follow-up bắt buộc, một tuỳ chọn. `NEXT_ACTION` chọn cái bắt
buộc.

## 7. Cổng hoàn thành

| cổng §10 | kết quả |
|---|---|
| mọi mục tiêu và RQ tìm thấy đều có một hàng trong ma trận | ✓ 29 hàng |
| mọi số liệu dùng trong bản thảo truy được tới artifact hoặc test | ✓ — một khoảng trống đã vá, xem §4 |
| không còn câu tuyên bố ổn định khi `STABILITY = NOT_MEASURED` | ✓ — quét `rg "ổn định"` trên bản thảo và hai chương, lọc bỏ câu phủ định: còn **ba** lần xuất hiện, không lần nào là một tuyên bố. `C7` *"mã **ổn định**"* dùng chữ ấy theo nghĩa **mã lỗi không đổi tên**, không phải độ ổn định thống kê; một dòng là **tên mức** trong ma trận (đánh dấu `NOT_MEASURED`); một dòng thuộc **hướng phát triển** |
| hidden-line PASS không đổi visual fidelity từ `PARTIAL` sang `PASS` | ✓ — giữ 39/41 và `PARTIAL` |
| artifact lịch sử không đổi byte | ✓ — `ARTIFACT_HASH_VERIFICATION PASS` (26 file · 19 raw) |
| mã sản phẩm không đổi | ✓ — `freeze --verify` exit 0, `d72db7c3…`, 92 file |
| không có lượt gọi model | ✓ — 0 |
| test tài liệu · reconciliation · freeze · cache identity | ✓ — xem §8 |
| `git diff --check` | ✓ sạch |

## 8. Cổng đã chạy

| cổng | kết quả |
|---|---|
| `doi_chieu_ket_qua_cuoi.py` | PASS · 26 file · 19 raw nguyên byte · 0/31 lệch · 12/12 đáp số |
| `scene3d_world_oracles.py` | **7/7**, tolerance 0 |
| `certify-product-ui-rendering.mjs --faultcheck` | **66/66** · 6/6 phép tiêm · 0 ngoại lệ |
| `pytest -q` | **4781 pass, 1 skip, 1 deselect** — 0 đỏ, cây sạch @ `a411ea8` |
| `npx vitest run` | **798 pass / 54 file** — 0 đỏ |
| `freeze_evaluation_candidate.py --verify` | exit 0 — 92 file, `d72db7c3…` |
| `lock_cache_identity.py --verify` | exit 0 @ `CACHE_VERSION = 94` |
| `git diff --check` | sạch |

## 8b. ⚠️ Một dao động của bộ test, ghi lại chứ không giấu

Bốn lượt `pytest -q` liên tiếp trong wave này:

```
lượt 1   3 đỏ   test_holdout_readiness_7b (guard cây-bẩn) + test_counter_decomposition::
                test_C3_TIEM_LOI_dem_kieu_cu_thi_ra_so_da_cong_bo[asyncio] + 1 nữa
lượt 2   1 đỏ   chỉ guard cây-bẩn
lượt 3   1 đỏ   chỉ guard cây-bẩn
lượt 4   1 đỏ   chỉ guard cây-bẩn  ·  4780 pass, 1 skip, 1 deselect
```

`test_counter_decomposition.py` chạy riêng: **12/12 xanh**. Không có thay đổi mã
nào giữa các lượt. Đây là **dao động của bộ test**, không phải hồi quy — nhưng
một phép tiêm lỗi đỏ *ngẫu nhiên* là thứ làm mất niềm tin vào chính lớp guard
mà kho này dựa vào, nên nó được ghi ở đây thay vì bỏ qua. Chưa định vị được
nguyên nhân trong phạm vi wave rà soát này.

## 9. Reused / created

**Reused**: `doi_chieu_ket_qua_cuoi.py` · `scene3d_world_oracles.py` ·
`certify-product-ui-rendering.mjs` · `freeze_evaluation_candidate` ·
`CLAIMS_MATRIX.json` · `FINAL_SUMMARY.json` · `SCORING_CORRECTION.json` · bốn
ma trận hiển thị.

**Created**: `docs/THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW.md` ·
`docs/thesis/CLAIM_EVIDENCE_MATRIX.md`.

**Modified**: `docs/THESIS_DRAFT.md` (ba khối đính chính, **không xoá một câu
gốc nào**) · ba sổ vận hành · `UI_ACCEPTANCE_MATRIX.json` (chạy lại có
`--faultcheck`).

**Duplicate check**: `THESIS_READINESS.md` là bảng *tuyên bố ↔ bằng chứng ↔ giới
hạn* ở mức **vận hành**; ma trận mới ở mức **học thuật** (mục tiêu · RQ · đóng
góp · câu được/không được phép viết). Hai bảng không thay nhau; ma trận mới trỏ
về `THESIS_READINESS` cho số sống thay vì chép lại.

---

```
NEXT_ACTION = PRODUCT_RESPONSE_CONTRACT_ALIGNMENT
```

Chọn nó vì đó là follow-up duy nhất **chạm một mục tiêu đã đăng ký** (`§1.6`,
`§3.9` — từ chối có cấu trúc phải nêu giai đoạn dừng và mã lỗi), và vì nó là
điều kiện tiên quyết của `DISPLAY_NAME_AUTHORITY…` lẫn của bản demo cuối.
`THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW` đứng sau nó: hợp nhất hai thân
Chương 4 khi hợp đồng phản hồi đã đúng thì chỉ phải viết một lần.
