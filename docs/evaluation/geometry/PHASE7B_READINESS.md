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
| 1 | `holdout/pool.json` | schema đầy đủ · **1/40 bài · 1/20 ô** — bài duy nhất là đề THẬT từ đề thi chính thức |
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

### ⛔ B1 — Pool mới có 1/40 bài, phủ 1/20 ô *(chặn cứng)*

```
pool: 1 bài · phủ 1/20 ô
Ô TRỐNG (19): A01 A02 A03 A04 A05 A06 A07 A08 A09 A10 A12 A13 A14 B01 … B06
seal_geometry_holdout.py --seed 0 --chi-kiem-pool  →  exit 2, KHÔNG sinh con dấu
```

Bài đã có (`hp_a11_001`, ô A11) là đề **thật**: Câu 6 Phần III mã đề 0103, đề
thi chính thức TN THPT 2026, có url và đáp án nguồn. Chi tiết + nguồn nào lấy
được / không lấy được: [HOLDOUT_ACQUISITION_LOG.md](HOLDOUT_ACQUISITION_LOG.md).

**Vì sao mới một bài** — không phải thiếu nguồn mà là **định dạng**: chuyên đề
tổng hợp nằm trong **PDF**, lời giải đề thi chính thức nằm trong **ảnh**, và loại
duy nhất đọc được dạng văn bản là *bài viết riêng cho từng câu* (1 bài/trang).
Đường nhanh hơn cần người: tải PDF chuyên đề (toanmath có tài liệu 217–704 trang
kèm lời giải) rồi chép đề — và **chép từ PDF là chép nguyên văn thật**.

### ⛔ B1b — Nợ đối chiếu văn bản đề *(chặn cứng, và không lệnh nào bắt hộ)*

Công cụ đọc web trả nội dung **đã đi qua một mô hình tóm tắt**, nên
`problem_text` là bản **chép LẠI**, không phải **chép NGUYÊN VĂN**. Một chữ sai
trong đề hình học làm bài toán thành **bài khác** — và nó vẫn đọc trôi chảy, vẫn
giải được, vẫn ra một số. Chỉ lộ ra khi có người mở url đối chiếu từng chữ.

Nên mọi bài thu kiểu này mang `can_kiem_tay: true`, và cổng đã chặn thật:

```
POOL KHÔNG HỢP LỆ — 1 lỗi:
  · hp_a11_001: can_kiem_tay còn true — chưa ai đối chiếu problem_text với
    nguồn. Niêm phong một đề chép sai là niêm phong một bài toán KHÁC.
```

Trả nợ = mở url, đọc, sửa nếu lệch, **rồi mới** xoá cờ.

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

### ⚠️ B5 — `RUNTIME_STALE_IMAGE` *(không chặn phép đo, chặn hồ sơ bằng chứng)*

Xem §4.

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
