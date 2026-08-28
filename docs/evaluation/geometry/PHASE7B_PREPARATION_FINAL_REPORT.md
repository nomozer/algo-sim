# PHASE 7B — BÁO CÁO CHUẨN BỊ CUỐI

> Lượt quét tự động toàn kho. **0 API call · không benchmark · không rút seed.**
> Không chạm `backend/app`, metric contract, capability boundary, oracle
> semantics, protocol. Chứng minh ở §12–13.

```
PHASE7B_PREPARATION_STATUS:  NOT_READY
```

---

## 1. CURRENT STATUS

| | |
|---|---|
| M1 (`accepted ≥ 1`) | **BLOCKED** — chờ chữ ký `NGƯỜI CHÉP` |
| Pool | **0/40** bài `accepted` |
| Coverage | **0/20** ô |
| Expectation | **NOT_READY** — chưa có `expectations/holdout.json`, và **đúng quy trình** (chỉ soạn sau M4) |
| Runtime | **STALE** — không dọn ở lượt này, có chủ đích (§9) |
| Seal | **BLOCKED** — thiếu seed GVHD *và* thiếu pool |
| Test | `pytest -q` → **3108 passed · 20 skipped** |
| Freeze | **PASS** — `7ab25683ce4e4e4d…`, 144 file, **không đổi từ 7A.2** |

Phần **dữ liệu** không đổi so với lượt trước. Cái đổi là **bộ đo**: hai lỗ cổng
đã đóng, và một trong hai từng khoá chết 6/20 ô.

---

## 2. COMPLETED AUTOMATIC WORK

### 2a. ⛔ Lỗ #1 — sáu ô tầng B **không nạp được bằng bất kỳ file lô nào**

Nặng nhất trong lượt này, và nó đã nằm đó từ đầu.

```
ingest.phan_tich : ô B CẤM có dòng `ĐÁP ÁN:`  (dòng ấy dựng oracle_result)
seal.kiem_pool   : mọi bài accepted PHẢI có `dap_an_chinh_thuc`
                   và ô B còn phải có `ly_do_ngoai_phu`
khuôn file lô    : KHÔNG có dòng nào sinh ra `ly_do_ngoai_phu`
```

Hai luật đều đúng phần mình. Cùng đọc một bài thì chúng loại trừ nhau ⇒
**B01–B06 chết ở `kiem_pool`**, không lối nào qua. Đo bằng chạy thật:

```
[1/6] ingest — đọc lô, kiểm nguồn + ranh giới + oracle
      · hp_b05_001: thiếu dap_an_chinh_thuc
      · hp_b05_001: thiếu ly_do_ngoai_phu
FAILED_STAGE: kiem_pool
FIX_REQUIRED: Sửa dữ liệu lô. KHÔNG sửa validator.
```

⚠️ `FIX_REQUIRED` bảo *"sửa dữ liệu lô"* — **một việc không làm được**. Cổng
chặn đúng mà **dạy sai** còn tệ hơn cổng chặn sai: người chép sẽ ngồi sửa một
file không có lỗi. Và 6 ô ấy đúng là 6 ô `HOLDOUT_EXPANSION_PLAN §1` gọi là
*"dễ nhất về dữ liệu"* — phần đáng lẽ xong trước lại là phần bị khoá chết.

**Sửa: tách TÊN DÒNG, không nới dòng cũ.**

| Dòng | Chảy vào | Thành `oracle_result`? |
|---|---|:-:|
| `ĐÁP ÁN:` *(chỉ tầng A)* | `dap_an_chinh_thuc` | **có** |
| `ĐÁP ÁN NGUỒN:` *(chỉ tầng B)* | `dap_an_chinh_thuc` | **không bao giờ** |
| `NGOÀI PHỦ VÌ:` *(chỉ tầng B)* | `ly_do_ngoai_phu` | — |

Nới `ĐÁP ÁN:` cho tầng B thì tầng B có oracle, tức **chấm nhầm thang** — đúng
thứ `PHASE7_METRIC_CONTRACT` tách ra. Dùng dòng tầng B ở ô tầng A cũng bị chặn.

Sau khi sửa, cùng lô ấy:

```
[1/6] ✅ 1 bài qua cả ba cổng      [5/6] 1 bài · phủ 1/20 ô · có bài: B05
═══ CHUỖI XONG · accepted = 1/40 ═══
```

### 2b. ⛔ Lỗ #2 — cổng rút bỏ quên vế **≥40 bài**

`HOLDOUT_PROTOCOL §3①` đòi **hai** thứ: *"≥40 bài, phủ ĐỦ 20/20 ô"*. Cổng rút
chỉ canh vế sau; vế trước nằm ở `report_holdout_readiness` dưới dạng số `40`
**viết tay, lặp 4 lần**. Hai cổng đọc cùng một pool bằng hai ngưỡng rời nhau.

Hậu quả cụ thể: pool **đúng một bài mỗi ô** phủ đủ 20/20 và `--chi-kiem-pool`
thoát `0` — trong khi **mọi seed cho ra cùng một tập**. Lúc ấy câu *"seed quyết
định bài nào"* thành lời khai suông, và `HOLDOUT_EXPANSION_PLAN` M4 (*"20/20 ô ·
≥40 bài | `--chi-kiem-pool` thoát 0"*) mô tả một hành vi cổng **không có**.

Sửa: `MOI_O_TOI_THIEU = 1` + `TONG_TOI_THIEU = 40` về **một chủ sở hữu**
(`seal_geometry_holdout`), tách cổng thành `kiem_du_dieu_kien_rut()` để **đỏ
được từ test**, và báo cáo dẫn ngưỡng từ đó thay vì giữ số riêng.

Cổng nay nói đủ hai vế:

```
Pool chỉ 0/40 bài rút được — thiếu 40.
Đủ ô mà thiếu bài thì mọi seed cho ra CÙNG một tập: seed hết quyết
định được gì, tập hết là held-out.
```

Kèm một lỗi đếm nhỏ cùng chỗ: dòng *"Pool hợp lệ"* in `len(cases)` — **đếm cả
bài đã bị loại**, tức tự khai đủ bằng chính những bài vừa bị gạt.

### 2c. Bảng kế hoạch từng ô — **sinh bằng máy** thay vì gõ tay

`COVERAGE_MATRIX §1b` nay sinh 9 cột/ô từ `BANG_O` + `NANG_LUC`: cần · thẻ năng
lực · oracle · chỉ số chấm · nguồn · số bài · chặn ở · việc kế tiếp.

Nó thay bảng gõ tay ở `CANDIDATE_REVIEW §3` — bảng ấy **sai**: cột *"Cần"* khai
hạn ngạch **cứng** (2 · 4 · 6) cho thứ `HOLDOUT_EXPANSION_PLAN §1` cố ý để
**mềm** (*"mỗi ô ≥1; tổng ≥40; ô nào dễ tìm thì lấy"*), và cổng rút cũng chỉ
canh `≥1`. Bảng ấy do **chính tôi viết ở lượt trước** — lần thứ ba trong wave
một con số gõ tay báo tốt hơn sự thật, nên lần này gỡ **nguồn** gõ tay chứ không
sửa con số.

### 2d. `--md` ghi ra ngoài kho — bịt sau khi nó cắn thật

Đường dẫn tương đối ghép vào **gốc kho**, nên `../docs/…` (cách gõ tự nhiên khi
đang đứng ở `backend/`) trỏ **ra ngoài** repo và `mkdir(parents=True)` dựng luôn
cây tài liệu ở đó. Xảy ra trong chính lượt này. Nay từ chối kèm chỉ dẫn.

### 2e. Test — 20 test mới, mọi cái đều đỏ được trước khi sửa

```
tests/geometry   969 passed   (trước lượt: 949)
pytest -q       3108 passed   (trước lượt: 3088) · 20 skipped
```

Trình tự có bằng chứng: 7 test ngưỡng pool + 3 test tầng B **chạy ĐỎ trước**,
xanh sau. Không test nào viết sau khi sửa để hợp thức hoá.

---

## 3. HUMAN-ONLY BLOCKERS

| | |
|---|---|
| **BLOCKER** | `batch_001.txt` còn 11 chỗ trống; dòng `NGƯỜI CHÉP:` chưa ký |
| **WHY** | Giao thức đòi đề **NGUYÊN VĂN**, và mọi kênh tự động đã đo được là hỏng **IM LẶNG** (MathType ⇒ công thức là OLE + WMF, không bao giờ là text; trích PDF rơi `⊥`; `2a` không phân biệt được với `a√2` — hỏng theo hướng **nhận nhầm**) |
| **IMPACT** | `accepted = 0` ⇒ M1 chưa đạt ⇒ 20 ô trống ⇒ không seal được |
| **CAN_AUTOMATE** | **KHÔNG, và cố ý không.** Cổng không hỏi *"có text không"* mà hỏi *"ai chịu trách nhiệm text này"*. Máy ký thay thì tập mất đúng tính chất làm nó là held-out |
| **OWNER** | người mở nguồn |
| **NEXT_ACTION** | gõ nguyên văn một đề vào `batch_001.txt`, ký `NGƯỜI CHÉP:` |

**Đường ngắn hơn, mới mở ở lượt này**: 6 ô tầng B **không cần đáp án đúng, không
cần soi toạ độ hữu tỉ, không cần luật sàng nào** — chỉ cần đề đúng LOẠI. Trước
lượt này chúng không nạp được (§2a); nay được. Khuôn ở cuối
`batch_001.candidates.txt`. Đây là cách rẻ nhất để M1 xảy ra.

---

## 4. GVHD DECISIONS

| | |
|---|---|
| **BLOCKER** | **SEED** — một số nguyên |
| **WHY** | Người đo chọn seed thì chọn được cả tập ⇒ tự huỷ tính held-out |
| **IMPACT** | chặn bước `seal`; **không** chặn thu thập dữ liệu |
| **CAN_AUTOMATE** | KHÔNG — `--seed` cố ý không có mặc định |
| **OWNER** | GVHD |
| **NEXT_ACTION** | xin một số nguyên, **sau khi pool đủ** — seed chỉ tiêu được một lần |

---

## 5. BUDGET DECISIONS

| | |
|---|---|
| **BLOCKER** | **360 logic / 480 HTTP** (`k = 3`, 20 ô) chưa duyệt |
| **IMPACT** | chặn lượt chạy `k` lượt — quota thật |
| **OWNER** | người dùng |
| **NEXT_ACTION** | duyệt — nhưng **quyết định ① trước** (§9 · C‑3): mở ô tầng B cho lớp vô tỉ ⇒ `N` đổi khỏi 20 ⇒ ngân sách phải chốt lại |

---

## 6. DATA STATUS

```
accepted              0
rejected              2   hp_a11_001 · hp_a14_cand_001   (ngoài ranh giới)
needs_manual_review   1   hp_a14_cand_002                (dạng trắc nghiệm)
tổng dòng trong pool  3   — chưa case nào đi qua `ingest`
```

Ứng viên đã soi và **đã xác minh bằng cách đọc ảnh trang**, sẵn để chép:

| id | Vị trí | `ĐÁP ÁN` | Rủi ro |
|---|---|---|---|
| `cand_A14_01` | tr 80 · Câu 1 | `2/3` | **thấp nhất** — không bước nào sinh căn |
| `cand_A14_02` | tr 82 · Câu 7 | `8/3` | trung bình — `SA` là **suy ra** (bộ ba 3-4-5) |

---

## 7. COVERAGE STATUS

`0/20` ô. Bảng đầy đủ 9 cột mỗi ô:
**[COVERAGE_MATRIX.md §1b](holdout/COVERAGE_MATRIX.md)** — sinh ra, không gõ tay.

| Nhóm | Ô | Chặn ở |
|---|---|---|
| tầng B | B01–B06 | ⛔ chưa có bài — **nay nạp được**, và không đòi đáp án đúng |
| tầng A có nguồn | A01–A10 · A13 · A14 | ⛔ chưa có bài — chờ người chép |
| tầng A chờ quyết định | A11 · A12 | ⛔ **quyết định ①**, không phải thiếu nguồn |

## 8. EXPECTATION STATUS

**NOT_READY, và đúng quy trình.** `HOLDOUT_EXPANSION_PLAN` cấm soạn kỳ vọng
trước M4: soạn kỳ vọng cho bài chưa biết có vào tập hay không là soạn cho một
tập khác. Chặng `[4/6]` in `⏸ bỏ qua, ĐÚNG quy trình` thay vì báo lỗi.

## 9. RUNTIME STATUS

**STALE — không dọn, có chủ đích.** `runtime_doctor` so **git SHA**, nên *mọi*
commit — kể cả commit chỉ sửa tài liệu, như chính lượt này — làm image cũ đi.
Dọn bây giờ là dọn thứ sẽ bẩn lại ngay ở commit kế tiếp. Vị trí đúng của nó là
`CHECKLIST §B` bước **áp chót**, sau commit cuối cùng và ngay trước `seal`.

## 10. SEAL STATUS

**BLOCKED**, hai lý do độc lập: thiếu pool (§6) *và* thiếu seed (§4). Thứ tự bắt
buộc: `commit cuối → rebuild image → runtime_doctor → seed → duyệt ngân sách →
seal`. Không tiêu seed ở lượt chuẩn bị.

## 11. TEST STATUS

```
pytest -q                 3108 passed · 20 skipped · 1 deselected
pytest tests/geometry -q   969 passed ·  2 skipped
```

## 12. FREEZE STATUS

```
freeze_evaluation_candidate.py --verify  → exit 0
measured_system_hash  7ab25683ce4e4e4d…  · 144 file  · KHÔNG đổi từ 7A.2
```

Mọi thay đổi ở lượt này nằm trong `backend/scripts`, `backend/tests`, `docs/` —
**bộ đo**, không phải **hệ được đo**. Ranh giới ấy là lý do băm không nhúc nhích.

## 13. FILES CHANGED

| File | Đổi gì |
|---|---|
| `scripts/seal_geometry_holdout.py` | `MOI_O_TOI_THIEU` · `TONG_TOI_THIEU` · `kiem_du_dieu_kien_rut()`; đếm bài **rút được** thay vì đếm dòng |
| `scripts/ingest_holdout_batch.py` | `ĐÁP ÁN NGUỒN:` · `NGOÀI PHỦ VÌ:` cho ô tầng B; gỡ mọi dòng siêu dữ liệu khỏi `problem_text` |
| `scripts/holdout_coverage_matrix.py` | `O_NGUON` · `O_CHO_QUYET_DINH` · `_bang_ke_hoach()`; `--md` từ chối đường ra ngoài kho |
| `scripts/report_holdout_readiness.py` | dẫn ngưỡng từ `seal_geometry_holdout`, bỏ 4 chỗ `40` viết tay |
| `tests/geometry/test_holdout_readiness_7b.py` | **+20 test**, mọi cái đỏ được trước khi sửa |
| `docs/…/CANDIDATE_REVIEW.md` | gỡ bảng gõ tay, trỏ sang bảng sinh ra |
| `docs/…/COVERAGE_MATRIX.md` | sinh lại, có §1b |
| `docs/…/batch_001.candidates.txt` | khuôn ô tầng B |
| `docs/…/PHASE7B_CHECKLIST.md` | ghi rõ cổng canh **cả hai** ngưỡng |
| `docs/CODE_INDEX.md` | ba entry: hai ngưỡng · hai dòng tầng B · bảng sinh ra |

## 14. COMMITS

| SHA | |
|---|---|
| `ef2994d` | *(lượt trước)* phân loại blocker; sửa hai chỗ tài liệu báo tốt hơn thật |
| *(lượt này)* | đóng hai lỗ cổng; bảng kế hoạch sinh bằng máy |

## 15. NEXT SINGLE ACTION

> **Chép một đề vào `batch_001.txt` và ký `NGƯỜI CHÉP:`.**
>
> Rẻ nhất là **một ô tầng B** (`B01`–`B06`): không cần đáp án đúng, không cần
> soi toạ độ hữu tỉ, không luật sàng nào — chỉ cần đề đúng loại. Khuôn ở cuối
> `batch_001.candidates.txt`.
>
> Hoặc `cand_A14_01` (tr 80 · Câu 1 · `ĐÁP ÁN: 2/3`) nếu muốn M1 chạy trên
> nhánh **có oracle**.
>
> Rồi: `python scripts/run_m1_pipeline.py …/batch_001.txt --ghi`

Mọi thứ sau bước ấy đã chạy được, và đã có test chứng minh chạy được.
