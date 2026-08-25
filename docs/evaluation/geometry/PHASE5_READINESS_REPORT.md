# PHASE 5 — READINESS REPORT

> Wave **hardening trước phép đo**. Không gọi API, không đánh giá LLM, không
> đổi dataset/primitive/taxonomy/renderer. Ngày 2026-08-25.

---

## Repository

| | |
|---|---|
| HEAD | `3364aa2` · nhánh `main` |
| dirty **toàn kho** | ❌ **22 mục** |
| dirty **hệ được đo** | ✅ **0 mục** |
| `measured_system_hash` | `24e80b8ff48ac361…` · 141 file |

Hai con số dirty ấy **không thay thế được cho nhau**, và toàn bộ phán quyết của
báo cáo này nằm ở chỗ phân biệt chúng — xem §Final.

## Freeze

`freeze --verify` → **PASS**, exit 0.
`Candidate khớp bản đã đóng băng (mã sản phẩm: 141 file, 24e80b8ff48ac361…)`

## Environment

`CACHE_VERSION` = **40**, khớp `backend/app/main.py:179`.

## Runner

| STEP 3 đòi | Trước wave | Nay |
|---|---|---|
| commit hash | ❌ thiếu | ✅ `neo.commit` |
| dirty state | ❌ thiếu | ✅ `neo.dirty_toan_kho` + `neo.dirty_he_duoc_do` |
| model · API usage · generated_raw · generated_program · failure_layer · failure_reason · obligation_match · oracle status | ✅ | ✅ |

**Không có PASS/FAIL tổng chung.** Artifact chỉ đếm theo từng cổng
(`G1_schema` · `G2_semantic` · `A_executable` · `O_oracle`) cộng
`phan_bo_that_bai` theo tầng. Oracle giữ **bốn trạng thái** phân biệt —
`PASS` · `FAIL` · `UNGRADED` · `NO_RESULT` — nên "không chấm được" không bao giờ
bị đếm thành "sai".

## Dataset

**10/10 sạch.** Mỗi bài có đề · nghĩa vụ kỳ vọng · `oracle_result` · ít nhất một
khoá trùng tên nghĩa vụ để bám vào khi chấm. Phủ **8/8** nghĩa vụ hình học:

```
point_on_plane 3 · perpendicular 2 · volume 2
point_on_line 1 · parallel 1 · coplanar 1 · distance 1 · angle 1
```

Không sửa gì. Không sửa đáp án.

## Prompt

**Sạch.** 12 test rò rỉ PASS. Không `case_id`, không đoạn đề bài (cửa sổ 40 ký
tự), không `ghi_chu_kiem_tay` (lời giải của custodian), không đáp án phân số
của DEV — dò **cả hai chiều**.

Rò rỉ duy nhất từng có (`2/3` trong `geometry_analyze.md`, đúng đáp án `geo_09`
và `geo_10`) đã vá ở `ed580cd` và **đã tiêm lỗi giả để chứng minh guard đỏ được**.

## Regression

| | |
|---|---|
| pytest | **2411 passed** · 18 skipped · **1 failed** (§Final) |
| vitest | **KHÔNG chạy** — có chủ đích, xem dưới |

Chạy `vitest` sẽ **ghi đè 5 artifact bằng chứng** (`docs/evaluation/m17|m20/*.json`)
mà wave W13-A11Y đang dở. STEP 1 cấm đụng file của wave khác, và ghi đè là đụng.
Route ngữ nghĩa thuần backend nên `vitest` không phải cổng của phép đo này.

**Bất biến giữ nguyên hết:**

```
target Tin học   24        obligation   19 = 11 tin_hoc + 8 hinh_hoc
checker C₂       18        geometry     8/8, không nghĩa vụ nào thiếu checker
oracle custodian CÓ (8 234 byte)
```

---

## STEP 0 — phân loại phát hiện

### B. Thuộc wave khác — 22 mục, **không đụng**

Wave **W13-A11Y** của một phiên chạy song song (môi trường có project riêng cho
frontend). Theo dõi qua bốn lượt, nó lan dần: `wcag.mjs` → `global.css` →
`tokens.css` → 6 module UI.

```
frontend/src/components/ArrayView.tsx · SamplePreview.tsx
frontend/src/simulations/domains/{algorithm/program-module,binary/ui,
                                  database/table-module,logic/dag-module}.tsx
frontend/src/styles/{global,tokens}.css · tokens.test.ts
frontend/scripts/certify-a11y-w13.mjs   (chưa theo dõi)
frontend/wcag.mjs                        (chưa theo dõi)
docs/CODE_INDEX.md                       (2 hunk W13-A11Y)
docs/evaluation/m17|m20/*.json           (5 artifact tự sinh khi chạy vitest)
docs/evaluation/m20/w13-a11y.json        (chưa theo dõi)
```

**Mức ảnh hưởng: KHÔNG chạm hệ được đo.** Kiểm cơ học: 0/22 mục nằm trong
`MEASURED_SYSTEM_PATHS`. Đó là lý do `freeze --verify` vẫn PASS.

**Có cần sửa không: KHÔNG, và không được phép.** Không commit hộ, không revert,
không xoá.

### A. Thuộc Phase 5 readiness — 2 lỗ, **đã vá**

Cả hai là **harness thuần**, đúng thứ STEP 3 đòi:

1. `neo_kho_ma()` — artifact nay tự khai commit + trạng thái bẩn. Trước bản này
   `geometry_dev_results.json` chỉ có điểm số, **không buộc được vào commit nào**;
   người đọc sau ba tháng không tái lập được, và không biết cây có bẩn lúc chạy.
2. Bốn test khoá nó, gồm một test **chứng minh** câu khẳng định trong artifact
   (`file ngoài phạm vi không làm đổi hash hệ đo`) thay vì để nó là lời tuyên bố.

### C. Lỗi product — **không có**

---

## STEP 2 — tái lập artifact: **PASS toàn bộ, không cần vá**

| Kiểm | Kết quả |
|---|---|
| `bam_noi_dung`: cùng nội dung, LF vs CRLF | ✅ **cùng hash** `64c3b26e…` |
| `measured_system_hash` ổn định qua hai lần gọi | ✅ |
| DEV fingerprint ổn định qua hai lần dựng | ✅ `8a3de7a3f9530942…` |
| File ngoài `MEASURED_SYSTEM_PATHS` làm đổi hash | ✅ **không** — nay có test |

---

## Final: **BLOCKED**

### Blocker

`backend/tests/semantic_program/test_evaluation_candidate.py::test_candidate_ghi_dung_commit_va_cay_sach`

```
AssertionError: Candidate được đóng băng trên cây làm việc BẨN —
commit ghi trong đó không định danh được bản thật sự đem đo.
```

### File

`docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json` →
`cay_lam_viec_sach: false`, do **22 mục dirty của wave W13-A11Y**.

### Blocker này là THỦ TỤC, không phải THỰC CHẤT — và tôi vẫn không tự gỡ

Bằng chứng cho vế đầu, đo được chứ không suy đoán:

```
dirty trong MEASURED_SYSTEM_PATHS   0/22
measured_system_hash                ổn định, freeze --verify PASS
```

Nói cách khác: **commit `3364aa2` ĐÃ định danh chính xác hệ sắp được đo.**
Cái không định danh được là *phần còn lại của kho*.

Kho này còn giữ hai định nghĩa khác nhau cho cùng chữ "bẩn":

| Nơi | Phạm vi | Lý do đã viết ra |
|---|---|---|
| `evidence.mjs::dirtyRelevantSources` | chỉ `SOURCE_PATHS` | *"sửa một file `docs/` rồi đo thì phép đo vẫn tái lập được, nên gọi nó là bẩn sẽ làm cảnh báo mất giá trị và người ta thôi đọc"* |
| `freeze_evaluation_candidate::cay_lam_viec_sach` | **toàn kho** | — |

Thu hẹp cổng thứ hai về đúng `MEASURED_SYSTEM_PATHS` sẽ làm nó nói đúng thứ
manifest thật sự ghim, và khớp nguyên tắc kho đã tự chốt. **Tôi không làm.**
Sửa một cổng trong lúc chính cổng ấy đang chặn mình thì dù lập luận có đúng,
thời điểm cũng biến nó thành động cơ — và đó là quyết định của bạn, không phải
của tôi. Runner vì thế **ghi cả hai con số** và không đứng về phe nào.

### Cách gỡ

**A — chờ W13-A11Y commit** (sạch nhất, không quyết định gì):

```bash
backend/.venv/Scripts/python.exe backend/scripts/freeze_evaluation_candidate.py
```

⚠️ Năm artifact `docs/evaluation/m17|m20/*.json` **tự sinh lại mỗi lần chạy
`vitest`**, nên cửa sổ sạch phải rơi **sau** lượt test cuối của wave kia.

**B — bạn chốt phạm vi của `cay_lam_viec_sach`.** Nếu bạn quyết thu hẹp về
`MEASURED_SYSTEM_PATHS`, đó là sửa harness (`backend/scripts` + `backend/tests`),
nằm trong phạm vi STEP 2 cho phép, và cây hiện tại sẽ **PASS ngay** — nhưng phải
là quyết định được nói ra, không phải hệ quả phụ của việc muốn chạy.

### Còn lại đều xanh

```
freeze --verify   PASS      CACHE_VERSION  40, khớp nguồn
dataset           10/10     prompt         12 test rò rỉ PASS
runner            10/10 trường STEP 3      pytest  2411 passed
tái lập LF/CRLF   PASS      bất biến Tin học + geometry giữ nguyên
```

---

## Ngoài phạm vi, nhắc lại để không ai tuyên bố quá

`B` (**servable**) vẫn chặn: tập nguyên thuỷ thị giác **không có nguyên thuỷ 3D
nào**. Phase 5 đo được `G1` · `G2` · `A` · `O` · `obligation_match`; **không**
đo được `B`, và không đo được gì về renderer hay tương tác 3D.
