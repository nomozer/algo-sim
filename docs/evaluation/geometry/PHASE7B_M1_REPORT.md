# PHASE 7B — BÁO CÁO MỐC M1

> **0 API call. Không chạy benchmark. Không sửa `backend/app`, prompt, DSL,
> kernel, renderer, metric, capability boundary.**

```
M1 (accepted ≥ 1):   CHƯA ĐẠT
accepted:            0
rejected:            2   (`hp_a11_001`, `hp_a14_cand_001` — ngoài ranh giới)
needs_manual_review: 1   (`hp_a14_cand_002` — dạng trắc nghiệm)
tổng case trong pool: 3   (không case nào đi qua `ingest` — đều soạn tay ở pha trước)
READY_FOR_PHASE7B:   NO
```

**Chặn ở đúng MỘT chỗ: chữ ký `NGƯỜI CHÉP`.** Mọi cổng khác đã qua — chứng
minh bên dưới.

> ### ⛔ Bản nháp đã bị LOẠI khỏi danh sách nguồn
>
> Phase 7B · TASK 1 ghi thẳng: *"Không dùng: `batch_001.draft.txt` · OCR
> output · text trích từ PDF · **nội dung AI đọc lại**"*.
>
> Bản nháp tôi soạn ở lượt trước thuộc mục cuối, nên nó **không** phải lối
> tắt: đề trong `batch_001.txt` phải do **người mở nguồn gốc, đọc trực tiếp,
> chép nguyên văn**. Bản nháp giữ lại chỉ để ghi nhận nó từng tồn tại và để
> lưu phần phân tích Câu 2; đã dán cảnh báo ở đầu file.
>
> Đây cũng là câu trả lời cho đề nghị tôi nêu ở lượt trước ("tôi có thể soạn
> nháp nếu bạn muốn"): **không**, và ranh giới ấy nay đã rõ.

---

## 1. Bài ứng viên — `Câu 1 trang 80`

| | |
|---|---|
| `case_id` (khi nạp) | `hp_a14_001` |
| Ô coverage | **A14** |
| `capability_tag` | `rational_volume` |
| `answer_shape` | `exact_fraction` |
| `oracle_ref` | `volume` |
| `oracle_result` | `{"volume": "2/3"}` |
| `expected_obligations` | `["volume"]` |
| Nguồn | *Tài liệu chuyên đề khối đa diện và thể tích khối đa diện* — **trang 80, Câu 1** |

**Đề** *(bản nháp máy đọc — chờ người đối chiếu)*:

> Cho hình chóp `S.ABC` có đáy `ABC` là tam giác vuông tại `A`, `AB = a`,
> `AC = 2a`. Cạnh bên `SA` vuông góc với đáy và `SA = 2a`. Tính thể tích `V`
> của khối chóp `S.ABC`.

**Đáp án**, theo lời giải in ngay dưới đề cùng trang:
`S_ABC = AB·AC/2 = a²` · `V = (1/3)·S_ABC·SA = 2a³/3` → gán `a = 1` ⇒ **`2/3`**.

**Toạ độ hữu tỉ hoá được**: `A(0,0,0)` · `B(1,0,0)` · `C(0,2,0)` · `S(0,0,2)`.

## 2. Trạng thái cổng — chạy thật trên bài này

```
phan_tich            : không lỗi
capability_boundary  : PASS
kiem_pool            : PASS
ingest (bản nháp)    : ⛔ 1 LỖI — "THIẾU dòng NGƯỜI CHÉP:"
```

Chỉ **một** lỗi, và nó là lỗi **cố ý không sửa được bằng máy**. Thêm chữ ký
thì cả dây qua sạch — đã mô phỏng để xác nhận, **không** ghi vào pool.

## 3. ⚠️ `Câu 2 trang 80` — ĐÃ SOI VÀ PHẢI LOẠI

Phase này chỉ định dùng cả Câu 1 và Câu 2. **Câu 2 không dùng được.**

> *"Cho hình chóp `S.ABC` có `SA ⊥ (ABC)`, `△ABC` vuông cân tại `A`,
> `SA = BC = a`. Tính theo `a` thể tích `V`."*

Đáp án `V = a³/12` — **hữu tỉ**. Dữ kiện `SA = BC = a` — **không một dấu căn**.
Vẫn ngoài ranh giới:

```
vuông cân tại A, cạnh huyền BC = a  ⇒  AB = AC = a/√2
tỉ số AB : BC = 1 : √2  →  VÔ TỈ
⇒ không hệ trục nào đặt được cả ba đỉnh vào toạ độ hữu tỉ
```

### Đây là LỚP THỨ TƯ của rào vô tỉ — và nó phá luật sàng của lượt trước

| | Lớp | Dữ kiện | Đáp án | Toạ độ |
|---|---|:-:|:-:|:-:|
| §2.1 | `distance` vô tỉ | hữu tỉ | **vô tỉ** | — |
| §2.2 | tỉ số dữ kiện vô tỉ | **vô tỉ** | — | vô tỉ |
| §2.2b | căn sinh khi giải | hữu tỉ | **vô tỉ** | vô tỉ |
| **MỚI** | **Câu 2** | hữu tỉ | **hữu tỉ** | **vô tỉ** |

Lượt trước tôi đưa luật *"nhìn ĐÁP ÁN trước"*. **Câu 2 phá luật ấy**: đáp án
sạch mà bài vẫn ngoài phủ.

> **LUẬT SÀNG ĐỦ — và là luật duy nhất đủ:**
> **"Đặt được cả hình vào toạ độ HỮU TỈ không?"**
>
> Kiểm nhanh — mọi **tỉ số độ dài suy ra được từ đề** có hữu tỉ không?
>
> | Hình | Tỉ số | |
> |---|---|:-:|
> | tam giác vuông cân | `1 : 1 : √2` | ⛔ |
> | tam giác đều (đường cao) | `a√3/2` | ⛔ |
> | góc `30°` · `60°` · `120°` | `tan`/`cos` sinh `√3` | ⛔ |
> | tam giác vuông, hai cạnh góc vuông **bội nguyên của `a`** | `1 : 2 : √5` nhưng **cạnh huyền không dùng tới** | ✅ |
>
> ⚠️ Ô cuối là chỗ tinh tế: Câu 1 có `BC = a√5` (cạnh huyền vô tỉ), **vẫn
> dùng được**, vì thể tích chỉ cần `AB`, `AC`, `SA` — cả ba hữu tỉ. Cái quyết
> định là **toạ độ đỉnh**, không phải mọi độ dài trong hình.

Pha này cấm sửa `capability_boundary`, nên ghi ở đây như **đề nghị bổ sung
`§2.2c`** cho lượt nào được phép sửa tài liệu ấy.

## 4. Coverage

```
A01 0  A02 0  A03 0  A04 0  A05 0  A06 0  A07 0
A08 0  A09 0  A10 0  A11 0  A12 0  A13 0  A14 0
B01 0  B02 0  B03 0  B04 0  B05 0  B06 0
```

## 5. Việc còn lại để đạt M1

1. Mở [tài liệu](https://toanmath.com/2023/07/tai-lieu-chuyen-de-khoi-da-dien-va-the-tich-khoi-da-dien.html)
   → **trang 80** → đọc **Câu 1** trên chính trang đó.
2. **Gõ lại nguyên văn** vào `holdout/batch_001.txt`, giữ đủ `= ⊥ √ ∥`.
   *(Không chép từ bản nháp — TASK 1 loại nó khỏi danh sách nguồn.)*
3. `NGUỒN:` — tên tài liệu + trang 80 + Câu 1.
4. `ĐÁP ÁN: 2/3` — lời giải in ngay dưới đề cho `V = 2a³/3`; gán `a = 1`.
5. `NGƯỜI CHÉP: <tên> · <ngày> · <tài liệu, trang>`.
6. `ingest_holdout_batch.py … ` (soi) → `--ghi`.

Khối cần điền, đúng khuôn:

```
NGƯỜI CHÉP: <tên bạn> · 2026-08-28 · Khối đa diện & thể tích, trang 80

[A14] <gõ nguyên văn Câu 1 từ trang 80>
      NGUỒN: Tài liệu chuyên đề khối đa diện và thể tích khối đa diện — trang 80, Câu 1
      ĐÁP ÁN: 2/3
```

Ba dòng còn lại (`NGUỒN`, `ĐÁP ÁN`) đã xác định chắc chắn; dòng duy nhất cần
bạn đọc nguồn để viết là **đề bài**.

---

## 6. PHÂN LOẠI BLOCKER — bốn nhóm, chỉ nhóm A tôi tự xử

Chia theo **ai gỡ được**, không theo mức nghiêm trọng. Đây là điểm mấu chốt:
mọi blocker còn lại đều **không** thuộc kho mã, nên viết thêm code không nhích
được cái nào.

| Nhóm | Nghĩa | Số blocker | Tôi xử được? |
|---|---|:-:|:-:|
| **A** | lỗi mã / tài liệu trong repo | **3** | ✅ **đã xử — mục 6a** |
| **B** | thiếu **dữ liệu** người phải chép | **1** | ⛔ chỉ người mở nguồn |
| **C** | chờ **quyết định** (người / GVHD) | **3** | ⛔ không được tự quyết |
| **D** | môi trường / hạ tầng | **1** | ⚙️ theo thứ tự, đúng lúc |

### 6a. Nhóm A — đã đóng ở lượt này

| # | Triệu chứng | Cách xử |
|---|---|---|
| A‑1 | `PHASE7B_CHECKLIST §A` ghi **`1/40 bài · 1/20 ô`** — số của lượt cũ, cao hơn thực tế | sửa thành `0/40 · 0/20`, khớp `--chi-kiem-pool` |
| A‑2 | Checklist trỏ *"nguồn trạng thái sống"* sang `PHASE7B_READINESS.md` — file **gõ tay, đông cứng ở `641ac5f`**, chỉ khác file sinh ra đúng một chữ `_REPORT` | trỏ lại sang `PHASE7B_READINESS_REPORT.md` (sinh bằng script) + dán cảnh báo phân biệt hai file |
| A‑3 | Kế hoạch 40 bài thiếu **`oracle type`** và **chỉ số sẽ chấm** từng ô | dựng lại bảng `CANDIDATE_REVIEW §3`, tách tầng A / tầng B, **đối chiếu máy** với `NANG_LUC` |

⚠️ A‑1 và A‑2 cùng một giống: **tài liệu báo tốt hơn sự thật.** A‑1 khai dư một
bài không tồn tại; A‑2 đưa người đọc tới ảnh chụp cũ mà tưởng là trạng thái nay.
Cả hai đều **không** làm test đỏ — không cổng máy nào canh số trong bảng
markdown — nên chúng chỉ lộ khi có người đối chiếu tay, và đó là lý do ghi ra
đây thay vì sửa im lặng.

### 6b. Nhóm B — một blocker, và nó là **cái duy nhất** chặn M1

```
B‑1  batch_001.txt còn 11 chỗ trống; dòng NGƯỜI CHÉP chưa ký
     ⇒ ingest từ chối cả lô  ⇒ accepted = 0  ⇒ M1 CHƯA ĐẠT
```

**Tác động**: chặn dây chuyền tại chặng **đầu tiên**. `pool → scaffold → freeze
→ coverage → seal` đều đã chạy được, nhưng không có gì để chảy qua.

**Việc phải làm**: đúng **một** dòng — gõ lại nguyên văn `Câu 1 trang 80` rồi ký
`NGƯỜI CHÉP`. Ba dòng còn lại (`NGUỒN`, `ĐÁP ÁN: 2/3`) đã xác định bằng soi
nguồn. Khuôn sẵn ở `holdout/batch_001.candidates.txt`.

> Cổng chữ ký **cố ý không tự động hoá được**. Nó không kiểm *"có text không"*
> mà kiểm *"có người chịu trách nhiệm text này không"* — máy không ký thay được,
> và nếu tôi ký thì tập held-out mất đúng cái tính chất làm nó là held-out.

### 6c. Nhóm C — chờ quyết định, **không** chờ code

| # | Quyết định | Ai | Chặn cái gì |
|---|---|---|---|
| C‑1 | **Seed** — một số nguyên | **GVHD** | bước `seal`. Người đo chọn seed thì chọn được cả tập ⇒ tự huỷ tính held-out |
| C‑2 | **Ngân sách** 360 logic / 480 HTTP (`k=3`) | người dùng | bước chạy `k` lượt — quota thật |
| C‑3 | **A11 · A12**: chỉ nhận `distance` hữu tỉ, hay mở ô tầng B cho lớp vô tỉ | người dùng | 4/40 bài. **Không chặn 36 bài kia** |

⚠️ C‑3 nếu chọn hướng "mở ô tầng B" thì `N` đổi khỏi 20 ⇒ **phải chốt lại ngân
sách C‑2**. Hai quyết định này dính nhau, quyết C‑3 trước.

### 6d. Nhóm D — hạ tầng, đúng thứ tự thì không phải blocker

```
D‑1  runtime_doctor → RUNTIME_STALE_IMAGE
```

**Không phải lỗi.** Nó so **git SHA**, nên *mọi* commit — kể cả commit chỉ sửa
tài liệu, như chính lượt này — làm image cũ đi. Vì thế nó nằm ở
`CHECKLIST §B` bước áp chót: dựng lại image **sau commit cuối**, ngay trước
`seal`. Dọn nó bây giờ là dọn một thứ sẽ bẩn lại ngay.

---

## 7. Vì sao lượt này không sinh được báo cáo "chuỗi đã chạy"

Phase yêu cầu chứng minh `Natural Language → Geometry Understanding →
Construction → Verification → Evaluation` chạy trên **một ca thật**. Không sinh
được, và lý do phải nói thẳng: **chưa có ca thật nào.** Chuỗi ấy khởi động từ
`problem_text`, mà `problem_text` là thứ duy nhất máy không được phép tự tạo.

Cái **đã** chứng minh được, bằng chạy thật chứ không bằng lập luận:

| | Bằng chứng |
|---|---|
| dây chuyền nạp liệu chạy hết chặng | `run_m1_pipeline.py` dừng đúng chặng đầu, in `FAILED_STAGE` · `REASON` · `FIX_REQUIRED` |
| không chặng nào qua **im lặng** | test tiêm lỗi ở **bốn chặng** (`HOLDOUT_EXPANSION_PLAN §1`); `pytest tests/geometry -q` → **949 passed, 2 skipped** |
| bảng ô ↔ oracle **khớp máy** | đối chiếu `CANDIDATE_REVIEW §3` với `NANG_LUC` ⇒ `KHỚP` |
| hệ được đo **không đổi** từ 7A.2 | `freeze --verify` → exit 0, `7ab25683ce4e4e4d…`, **144 file** |

Nói cách khác: **bộ đo xong, hệ đo đóng băng, thiếu vật đo.**
