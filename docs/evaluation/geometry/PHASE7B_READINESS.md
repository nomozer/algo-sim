# PHASE 7B — TRẠNG THÁI SẴN SÀNG (2026-08-27)

> Lượt chuẩn bị. **0 API call · không chạy benchmark · không sửa `backend/app`,
> prompt, DSL hay hợp đồng chỉ số.**

```
READY_FOR_PHASE7B:  NO
```

Hạ tầng đo **đã xong**. Thiếu **dữ liệu**, và cả hai mắt xích thiếu đều nằm
ngoài kho mã.

---

## 1. Đã xong ở lượt này

| # | Việc | Kết quả |
|---|---|---|
| 1 | `holdout/pool.json` | schema đầy đủ, **`cases: []`**, tự khai `__trang_thai__: EMPTY` |
| 2 | `holdout/COVERAGE_MATRIX.md` | sinh từ `holdout_coverage_matrix.py`, 20 ô × 7 họ × 4 hình dạng đáp án |
| 3 | Cổng kỳ vọng | `nap()` nay đòi thêm **`slot` + `oracle_ref`**; `kiem_noi_oracle()` nối con trỏ sang pool |
| 4 | `HOLDOUT_K_DECISION.md` | ba phương án + chi phí + khuyến nghị (**chưa** triển khai) |
| 5 | Kế hoạch dọn runtime | §4 dưới đây (**chưa** chạy) |
| — | Test | **29 test mới** · `tests/geometry/test_holdout_readiness_7b.py` · `pytest 2979` |

---

## 2. BLOCKERS

### ⛔ B1 — Pool chưa có bài nào *(chặn cứng)*

```
pool: 0 bài · phủ 0/20 ô
Ô TRỐNG (20): A01 … B06
seal_geometry_holdout.py --seed 0 --chi-kiem-pool  →  exit 2, KHÔNG sinh con dấu
```

Cần **≥40 bài** trích từ **đề thi / đề minh hoạ / chuyên đề có lời giải chi
tiết**, mỗi bài kèm `dap_an_chinh_thuc` **nguyên văn** và `nguon.url` tra ngược
được, phủ đủ 20/20 ô.

**Không tôi tự soạn.** `HOLDOUT_PROTOCOL §0`: bất kỳ đề nào tôi viết ra thì tôi
đã nhìn, và bốn wave vừa rồi đã sửa hệ theo đúng chỗ tập DEV hỏng. Bảo đảm thật
không phải *"tôi chưa nhìn"* mà là **"tôi không viết được ra chúng và không sửa
được đáp án"**.

### ⛔ B2 — Chưa có seed của GVHD *(chặn cứng)*

`--seed` **không có mặc định** — cố ý. Tôi chọn seed thì tôi chọn được cả tập:
chạy thử vài seed rồi lấy cái cho điểm đẹp nhất.

### ⛔ B3 — Chưa chốt `k` và ngân sách *(chặn, phải xong TRƯỚC seed)*

`HOLDOUT_PROTOCOL §2` (*"chạy MỘT LƯỢT"*) và `PHASE7_METRIC_CONTRACT §2⑤`
(*`k ≥ 3`*) đọc như mâu thuẫn. Phân tích ở
[HOLDOUT_K_DECISION.md](HOLDOUT_K_DECISION.md): mâu thuẫn thật chỉ là **ngân
sách**, vì *"một lượt"* cấm **lặp có sửa**, không cấm `k` lượt trong một phiên
đã niêm phong.

**Khuyến nghị: `k=3` toàn bộ · 360 logic / 480 HTTP (3,0× trần đã duyệt).**
Lui về `k=3` tầng A + `k=1` tầng B (288/384) nếu ngân sách bị từ chối. **Không**
lui về `k=1`: nó buộc phải phá chỉ số ⑤ vừa đóng băng ở 7A.2.

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
① SOẠN POOL          ≥40 bài, nguồn ngoài, phủ 20/20 ô        ← làm được NGAY
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

- **Không** soạn một bài nào. `cases: []`.
- **Không** sinh expectation nào cho held-out.
- **Không** rút, không niêm phong, không chạy.
- **Không** chọn `k` thay người trả ngân sách.
- **Không** rebuild container.
- **Không** đụng `backend/app`, prompt, DSL, hợp đồng chỉ số. `freeze --verify`
  vẫn PASS trên cùng băm `7ab25683…` của Phase 7A.2.
