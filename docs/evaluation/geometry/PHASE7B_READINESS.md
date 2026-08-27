# PHASE 7B — TRẠNG THÁI SẴN SÀNG (cập nhật 2026-08-27, sau Phase 7A.3)

> Lượt chuẩn bị. **0 API call · không chạy benchmark · không sửa `backend/app`,
> prompt, DSL, renderer hay định nghĩa chỉ số.**

```
READY_FOR_PHASE7B:  NO
```

Hạ tầng đo **đã xong** và **giao thức đã đóng băng** (7A.3). Thiếu **dữ liệu**,
và hai mắt xích chính đều nằm ngoài kho mã.

**Băm tài liệu đã đóng băng** — chốt ở `641ac5f`, ghi lại để lượt chạy đối chiếu:

```
holdout_protocol  25c9143b8650d18d5d4836d10fa3cf3cd07e262c767b8a74852d4a1f3b1a62ce
metric_contract   2bb1b1cd64eba3643a27c5fbbbc881c0f9e3a790121cee5beea6ed6341588fe0
k_final           b0c46e403af28a9fa348c02fd8a417ee82df84420d23dcc513b17cded5e123ce
expect_pilot      f9fdd1362b29fa49d0ecde673d15ba56f6a173ec152e8b2b8ef85dcacd8451b5
pool              4c9eba84742c220061895da25e39f662f03b9da277b347be2978635a4cb2e569
expect_holdout    ⛔ THIẾU FILE
```

⚠️ `metric_contract` đổi từ `ae454123…` vì `§7` thêm mục **7A.3**. Đó là **ghi
nhật ký**, không phải đổi định nghĩa chỉ số nào — xem mục ấy.

---

## 1. Đã xong ở lượt này

| # | Việc | Kết quả |
|---|---|---|
| 1 | `holdout/pool.json` | schema đầy đủ · **0 bài `accepted` · 0/20 ô · 1 bài `rejected_capability_boundary`** |
| 1c | `pool.json.__don_vi_oracle__` | quy ước đơn vị oracle **dẫn từ `geometry_exec._do`**, khoá bằng test — khuôn cũ dạy SAI và đã sửa |
| 1d | `CAPABILITY_BOUNDARY.md` + `COVERAGE_MATRIX_BOUNDARY_REVIEW.md` | **ranh giới năng lực đã đóng băng** (7A.5) · `HOLDOUT_PROTOCOL §2b` điều kiện nhận bài |
| 1e | `status` + `capability_tag` | bài bị loại **giữ trong `cases`** kèm lý do, nhưng **không lấp ô** — `duoc_rut()` |
| 1f | **`check_capability_boundary()`** | cổng CHẠY ĐƯỢC (7B-prep): thẻ lệch ô · `answer_shape` ngoài tập đóng · oracle **căn thức** · oracle **thập phân** · thiếu `domain_condition` · chưa đối chiếu nguyên văn |
| 1g | Con dấu mang **danh tính đầy đủ** | `commit` · `measured_system_hash` · `metric_contract_hash` · `capability_boundary_hash` · `expectation_hash` · `pool_hash` · `k` · `budget` |
| 6 | **Runtime** | ✅ `runtime_doctor` **PASS** — `RUNTIME_STALE_IMAGE` đã đóng |
| 1b | `HOLDOUT_ACQUISITION_LOG.md` | sản lượng đo được của từng loại nguồn + **hạn chế của cách thu thập** |
| 2 | `holdout/COVERAGE_MATRIX.md` | sinh từ `holdout_coverage_matrix.py`, 20 ô × 7 họ × 4 hình dạng đáp án |
| 3 | Cổng kỳ vọng | `nap()` nay đòi thêm **`slot` + `oracle_ref`**; `kiem_noi_oracle()` nối con trỏ sang pool |
| 3b | Cổng `can_kiem_tay` | `kiem_pool` **từ chối niêm phong** khi còn bài chưa ai đối chiếu với nguồn |
| 4 | `HOLDOUT_K_DECISION.md` → **`HOLDOUT_K_FINAL.md`** | **`k = 3` ĐÃ CHỐT** (7A.3) · 360/480 · rủi ro chấp nhận đã khai |
| 4b | `HOLDOUT_PROTOCOL` §2 · §5 · §7 | *"một lượt"* đã làm rõ · ngân sách có phép tính · hạn chế "một bài mỗi ô" thu hẹp |
| 4c | `PHASE7B_CHECKLIST.md` | precondition · execution · report — mỗi ô kèm lệnh kiểm hoặc tên cổng máy |
| 5 | Kế hoạch dọn runtime | §4 dưới đây (**chưa** chạy — đúng luật "chỉ sau khi pool + expectation xong") |
| — | Test | `tests/geometry/test_holdout_readiness_7b.py` · `pytest 2982` |

---

## 2. BLOCKERS

### ✅ B0a — RANH GIỚI NĂNG LỰC: **ĐÃ ĐÓNG BĂNG** (7A.5)

[CAPABILITY_BOUNDARY.md](CAPABILITY_BOUNDARY.md) — `SUPPORTED` / `UNSUPPORTED`,
mỗi mục dẫn từ mã, kèm **lỗi gì nếu đưa vào** và **vì sao KHÔNG phải lỗi AI**.
[COVERAGE_MATRIX_BOUNDARY_REVIEW.md](COVERAGE_MATRIX_BOUNDARY_REVIEW.md) — rà
từng ô: **16/20 trong ranh giới, 4 ô cần điều kiện miền**.
`HOLDOUT_PROTOCOL §2b` — điều kiện nhận bài vào tầng A.

**Không còn mơ hồ về phạm vi đo.** Cái còn thiếu là **dữ liệu**, không phải
định nghĩa.

### ⛔ B0b — Hai ô có thể không lấp nổi *(quyết định của người duyệt)*

Kernel dựng trên `Fraction` (cố ý — so bằng đúng, không epsilon), và hệ quả với
việc **chọn đề**:

| Lớp đề | Ví dụ | Trạng thái |
|---|---|---|
| Tỉ số dữ kiện vô tỉ | *đáy cạnh `a`, `SA = a√3`* | ⛔ ngoài phủ — không hệ trục nào làm cả hai hữu tỉ |
| `distance` ra vô tỉ | `d = 3√6`, `a√3/3` | ⛔ ngoài phủ — `_do` **ném** `GEOMETRY_IRRATIONAL_RESULT` |
| `angle`, `volume` | | ✅ **không** vướng: `cos²`/`sin²` và thể tích luôn hữu tỉ |

Đây là lý do bài duy nhất đã thu **bị loại** (xem B1). Và nó cần **một quyết
định của người duyệt trước khi soạn tiếp**:

| | Đường | Cái giá |
|---|---|---|
| **①** | chỉ nhận đề `distance` **hữu tỉ** vào A11/A12 | tập bớt đại diện; phải khai giới hạn khi báo số. **Rủi ro: có thể không lấp nổi hai ô** |
| **②** | mở **một ô tầng B** cho lớp vô tỉ, chấm bằng *từ chối trung thực* | đúng tinh thần tầng B, nhưng **N đổi khỏi 20** ⇒ ngân sách và `HOLDOUT_K_FINAL` phải chốt lại |
| ~~③~~ | cho `measure` trả bình phương | **SỬA HỆ** — loại ngay, ngoài phạm vi mọi pha 7A/7B |

⚠️ **Đừng soạn A11/A12 trước khi chốt ①/②.** Soạn rồi mới biết phải loại là mất
công hai lần — và tệ hơn, người soạn sẽ bị cám dỗ "chữa" đơn vị oracle cho vừa,
đúng cái vừa suýt xảy ra.

### ⛔ B1 — Pool 0 bài `accepted`, phủ 0/20 ô *(chặn cứng)*

```
pool: 0 bài dùng được · phủ 0/20 ô · 1 bài không vào rổ rút
seal_geometry_holdout.py --seed 0 --chi-kiem-pool  →  exit 2, KHÔNG sinh con dấu
```

`hp_a11_001` (Câu 6 mã đề 0103, TN THPT 2026) là đề **thật**, thu đúng quy
trình, nhưng **đáp án `3√6` vô tỉ** ⇒ hệ không phục vụ được. Nó **vẫn nằm trong
`cases`** với `status: rejected_capability_boundary` + `reason` — xoá đi là
**loại im lặng**, và loại im lặng là một dạng chọn tập. Nhưng nó **không vào rổ
rút và không lấp ô A11**: lấp một ô bằng bài hệ không phục vụ được là dựng một ô
**chắc chắn trượt** rồi ghi cái trượt ấy thành *"mô hình không làm được khoảng
cách"* — đúng loại sai lệch Phase 7A.1 đã phải đi sửa một lần.

**Rào thứ hai — định dạng:** chuyên đề tổng hợp nằm trong **PDF**, lời giải đề
thi chính thức nằm trong **ảnh**, trang SGK chỉ có **lời giải mà không có đề
bài**. Loại duy nhất đọc được dạng văn bản là *bài viết riêng cho từng câu*
(1 bài/trang). Đường nhanh hơn cần người: chép từ **PDF chuyên đề** — và chép
từ PDF là **chép nguyên văn thật**, hạ được `can_kiem_tay` ngay lúc chép.

### ⛔ B1b — KHÔNG kênh tự động nào cho NGUYÊN VĂN *(chặn cứng · cần người)*

Đo được ở lượt 7B-prep, hai thư viện độc lập (`pymupdf`, `pypdf`) cùng kết quả
trên `chuyen-de-quan-he-vuong-goc…pdf` (toanmath, **217 trang**):

| `=` | `⊥` | `√` | `∈` | `∥` |
|--:|--:|--:|--:|--:|
| 1303 | **0** | **0** | **0** | **0** |

**`⊥` xuất hiện đúng 0 lần trong một tài liệu 217 trang về quan hệ vuông góc.**
Font toán không có ánh xạ Unicode ⇒ trình trích **bỏ im lặng** đúng những ký
hiệu mang hình học:

```
NGUỒN            …AB = a, AD = a√3, SA ⊥ (ABCD) và SA = a…
TRÍCH TỰ ĐỘNG    … 3  ,,AB a AD a SA ABCD và  SA a .…
```

Bản trích **vẫn đọc như một đề bài** — đó là chỗ nguy hiểm. Cộng với công cụ
đọc web (đi qua một mô hình tóm tắt), **cả hai kênh tự động đều hỏng, và đều
hỏng im lặng**.

⇒ `problem_text_verified` **chỉ người hạ được**. `kiem_pool` từ chối niêm phong
khi nó chưa `true`; bài chưa xác minh mang `status: rejected_unverified`.

**Kênh thứ ba GIỮ được nguyên văn, và nó hiệu quả.** `curl` trả byte gốc, toán
nằm sẵn dưới dạng LaTeX (`\(ABCD.MNPQ\)`) — không bước nào diễn giải lại. Đóng
gói ở `harvest_holdout_candidates.py`. Quét đầy đủ 344 bài 2026:

```
344 url → 208 có khối đề → 125 SẠCH → 26 hình học không gian → 8 trong ranh giới
```

⇒ **Người chỉ còn phải ĐỌC SOÁT, không phải GÕ LẠI.** Đó là phần rào 3 đã giải.

### ⛔ B1d — LỆCH KIỂU NHIỆM VỤ: **92% đề là TRẮC NGHIỆM** *(rào nặng nhất)*

Trong 26 câu hình học không gian tách được: **24 trắc nghiệm 4 phương án**.
Trong 8 câu **trong ranh giới năng lực**: **7 trắc nghiệm**; câu tự luận duy
nhất chính là bài A11 đã loại vì vô tỉ. ⇒ **0 bài dùng được.**

Hệ **dựng cảnh và kiểm nghĩa vụ**, nó **không "chọn phương án"**. Một câu có
hình học hoàn toàn trong ranh giới vẫn không dùng được nếu câu hỏi là *"chọn
một trong bốn"* — không có nghĩa vụ nào để khai.

**Ba đường, cần người quyết:**

| | Đường | Cái giá |
|---|---|---|
| **①** | nhận nguyên văn đề trắc nghiệm | ô **chắc chắn trượt**, và trượt vì lệch kiểu nhiệm vụ chứ không vì mô hình kém |
| **②** | viết lại thành đề dựng/chứng minh | ⛔ **CẤM** — *"không tự biến đổi đề"*; viết lại là tôi soạn đề |
| **③** | đổi nguồn sang **đề TỰ LUẬN** (SGK · chuyên đề · HSG) | tồn tại, nhưng nằm trong PDF/ảnh ⇒ quay lại cần người chép |

Ví dụ cụ thể đã đưa vào `cases` để quyết định có vật đối chiếu:
`hp_a14_cand_002` — dữ kiện hữu tỉ hoàn toàn (đáy vuông cạnh 2, `SA = 3`,
`V = 4`), thoả **mọi** điều kiện năng lực, kẹt **chỉ** vì bốn phương án.

### ⛔ B1c — Nợ đối chiếu văn bản đề *(chặn cứng, và không lệnh nào bắt hộ)*

Công cụ đọc web trả nội dung **đã đi qua một mô hình tóm tắt**, nên
`problem_text` là bản **chép LẠI**, không phải **chép NGUYÊN VĂN**. Một chữ sai
trong đề hình học làm bài toán thành **bài khác** — và nó vẫn đọc trôi chảy, vẫn
giải được, vẫn ra một số. Chỉ lộ ra khi có người mở url đối chiếu từng chữ.

Nên mọi bài thu kiểu này mang `can_kiem_tay: true`, và cổng chặn thật —
`kiem_pool` từ chối niêm phong khi cờ còn `true`. Trả nợ = mở url, đọc, sửa nếu
lệch, **rồi mới** xoá cờ.

Hiện **không bài nào** mang cờ (pool rỗng sau khi loại `hp_a11_001`), nhưng cổng
đứng sẵn cho lô đề tiếp theo. Cách tránh nợ hẳn: **chép từ PDF**, không qua công
cụ đọc web.

### ⛔ B2 — Chưa có seed của GVHD *(chặn cứng)*

`--seed` **không có mặc định** — cố ý. Tôi chọn seed thì tôi chọn được cả tập:
chạy thử vài seed rồi lấy cái cho điểm đẹp nhất.

### ✅ B3 — `k` và giao thức: **ĐÃ CHỐT** (7A.3)

`k = 3` cho cả 20 ô · **360 logic / 480 HTTP** ·
[HOLDOUT_K_FINAL.md](HOLDOUT_K_FINAL.md).

Mâu thuẫn cũ đã hoà giải bằng **làm rõ**, không phải nới lỏng: *"chạy MỘT LƯỢT"*
cấm **lặp CÓ SỬA**, không cấm cỡ mẫu — `k` lượt trong **một phiên đã niêm phong**
là `k` phép lấy mẫu của **một** phép đo (`HOLDOUT_PROTOCOL §2`).

⛔ **Còn lại: ngân sách 360/480 chưa được duyệt.** Con số đã ghi ra; người duyệt
là người trả. Phương án lui nếu từ chối: `k=3` tầng A + `k=1` tầng B (288/384),
kèm nghĩa vụ khai *"tầng B chưa đo được độ ổn định của từ chối"*.

### ⚠️ B4 — `expectations/holdout.json` chưa soạn *(phụ thuộc B1)*

Khuôn đã sẵn và cổng đã đòi đủ: nguồn người đánh giá · lý do từng nghĩa vụ ·
nghĩa vụ dựng · nghĩa vụ kiểm · con trỏ oracle. Soạn được **ngay sau** khi có
pool — không cần seed.

### ⚙️ B5 — Runtime: **ĐÃ CHỨNG MINH DỌN ĐƯỢC, nhưng KHÔNG phải việc làm một lần**

Đã build lại kèm `GIT_SHA`/`BUILD_TIME` và `runtime_doctor` **PASS**:

```
source : sha=53ed4dbdb32f cache=46 skill=11/6208fc2a card=446b0769
runtime: sha=53ed4dbdb32f cache=46 skill=11/6208fc2a card=446b0769
KẾT LUẬN: PASS — runtime khớp source.
```

⚠️ **Rồi FAIL lại ngay ở commit kế tiếp** — và đó là hành vi ĐÚNG của cổng, không
phải hồi quy. `runtime_doctor` so **git SHA**, nên *mọi* commit đều làm image
cũ đi, kể cả commit chỉ sửa tài liệu.

**Hệ quả vận hành, sửa lại chỗ bản trước ghi nhầm là "đã dọn xong":** dọn runtime
là **bước áp chót**, ngay trước `seal`, **sau** khi commit cuối cùng — không phải
một ô tick được một lần rồi giữ mãi. Đưa nó lên đầu checklist là tự tạo một cổng
luôn đỏ.

Xem `PHASE7B_CHECKLIST.md` §B — thứ tự ở đó đã đúng: dọn runtime nằm **trong**
EXECUTION, không nằm trong PRECONDITION.

---

## 3. Phát hiện từ ma trận độ phủ — có TRƯỚC khi pool có bài nào

Hai chỗ hai trục không khít. Cả hai **giữ nguyên có chủ đích**, và cả hai đều
dẫn từ ánh xạ trong mã (`test_phat_hien_hai_cho_KHONG_KHIT_duoc_DAN_TU_ANH_XA`
khoá lại), không chép tay.

**① Họ `proof_verification` không có ô tầng A nào.** Trong `BANG_O`, việc
*chứng minh* không có ô riêng mà nằm lồng trong sáu ô quan hệ A03–A08 — đề
*"chứng minh AB ⊥ (SCD)"* rơi vào A06/A07/A08.

> **Hệ quả phải khai khi báo cáo 7B:** không tách được *"hệ **chứng minh** được
> quan hệ"* khỏi *"hệ **nhận ra** quan hệ"*. Muốn tách thì phải mở ô mới trong
> `BANG_O` — việc **trước** khi niêm phong, không phải sau.

**② Ô `B04` không thuộc họ nào.** Viết phương trình mặt phẳng trong Oxyz là bài
**biểu diễn đại số**, không phải một trong bảy họ hình học. Vẫn là ô tầng B hợp
lệ — B chấm bằng *từ chối trung thực*, không cần thuộc họ nào.

Phân bố ô theo họ (chưa có bài nào, nên đây là phân bố **thiết kế**):

```
point_construction  A:1   line_relation  A:4   plane_construction  A:3
intersection        A:1   solid_geometry A:1   measurement         A:4
proof_verification  A:0                        (B04 không thuộc họ nào)
```

⚠️ `measurement` và `line_relation` chiếm **8/14 ô tầng A**. Tập này *đại diện
chủ đề*, **không** *đại diện tần suất đề thi* — chưa ai đếm mỗi chủ đề chiếm bao
nhiêu phần trăm đề thi thật (`HOLDOUT_PROTOCOL §7`).

---

## 4. Kế hoạch dọn runtime — lệnh cần chạy, CHƯA chạy

Chạy **sau khi dữ liệu held-out hoàn tất**, và **trước** khi rút seed — vì con
dấu ghi `measured_system_hash`, nên mọi thứ chạm `backend/app` phải xong trước.

```bash
# ① Build lại KÈM danh tính — thiếu hai biến này thì doctor chỉ so được
#    cache/hash chứ không so được git SHA.
GIT_SHA=$(git rev-parse HEAD) BUILD_TIME=$(date -u +%FT%TZ) \
  docker compose up -d --build --force-recreate backend

# ② Phải nói KHỚP. Thoát != 0 là còn lệch — đừng rút seed khi còn lệch.
cd backend && .venv/Scripts/python.exe scripts/runtime_doctor.py

# ③ Hệ được đo vẫn là bản đã đóng băng.
cd backend && .venv/Scripts/python.exe scripts/freeze_evaluation_candidate.py --verify

# ④ Chỉ khi ①–③ đều xanh và pool + kỳ vọng đã xong:
cd backend && .venv/Scripts/python.exe scripts/seal_geometry_holdout.py --seed <SỐ CỦA GVHD>
```

**Vì sao ① cần dù container không nằm trên đường đo:** ba runner gọi
`run_pipeline` thẳng, không qua HTTP, nên lượt 7B *không* chạy trên image cũ.
Nhưng để nguyên thì hồ sơ bằng chứng mang **hai danh tính** cùng lúc (`source
124e711` ≠ `runtime 7e73291`), và câu *"đo bản nào"* mất câu trả lời duy nhất.
Đó đúng là thứ mà cả cổng đóng băng lẫn con dấu sinh ra để chống.

---

## 5. Thứ tự việc còn lại

```
① SOẠN POOL          còn 39 bài / 19 ô                        ← làm được NGAY
   + trả nợ `can_kiem_tay` cho mọi bài thu bằng công cụ đọc web
   kiểm: seal_geometry_holdout.py --seed 0 --chi-kiem-pool
         holdout_coverage_matrix.py --md …/COVERAGE_MATRIX.md

② SOẠN KỲ VỌNG       expectations/holdout.json theo khuôn      ← ngay sau ①
   kiểm: pytest tests/geometry/test_holdout_readiness_7b.py -q
         (hai cổng đang `skip` ở test_expectation_contract_7a2 sẽ TỰ BẬT)

③ CHỐT k + NGÂN SÁCH  + sửa ba chỗ tài liệu ở K_DECISION §5    ← song song ①

④ DỌN RUNTIME        §4 bên trên

⑤ XIN SEED (GVHD)    → rút tất định → niêm phong → COMMIT

⑥ CHẠY 7B            một phiên, không sửa gì giữa chừng
```

Bước ① là đường găng và **không** cần GVHD.

---

## 6. Điều lượt này KHÔNG làm

- **Không** sáng tác một đề nào. Bài duy nhất trong pool là đề thi chính thức,
  có url tra ngược được.
- **Không** tự tạo đáp án. `dap_an_chinh_thuc` chép từ nguồn; `phep_chuyen` là
  phần **duy nhất** người soạn được tính, và nó hiện ra để người khác kiểm lại.
- **Không** hạ cờ `can_kiem_tay` cho bài mình vừa thu — nợ đối chiếu phải do
  người trả.
- **Không** sinh expectation nào cho held-out (chờ pool hợp lệ).
- **Không** rút, không niêm phong, không chạy benchmark, không gọi LLM của hệ.
- **Không** chọn `k` thay người trả ngân sách.
- **Không** rebuild container — đúng luật *"chỉ sau khi pool + expectation
  hoàn thành"*.
- **Không** đụng `backend/app`, prompt, DSL, hợp đồng chỉ số, validator,
  frontend. `freeze --verify` vẫn PASS trên cùng băm `7ab25683…` của Phase 7A.2.
