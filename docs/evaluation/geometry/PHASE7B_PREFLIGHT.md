# PHASE 7B — PREFLIGHT: STEP 0 + STEP 1 (2026-08-27)

> Phase 7B là **phép đo**, và giao thức của chính nó đặt hai cổng trước lượt
> chạy: STEP 0 (đóng băng môi trường) và STEP 1 (thẩm định tập held-out).
> *"Nếu bất kỳ thứ gì không khớp: DỪNG. Không chạy benchmark."*
>
> **Kết quả: DỪNG ở STEP 1.** Tập held-out chưa tồn tại. **0 API call đã tiêu.**
>
> Văn bản này là vết của lượt tiền kiểm — để lần chạy thật tra ngược được rằng
> STEP 0 đã đo *trước* khi có bất kỳ số nào.

---

## STEP 0 — ENVIRONMENT FREEZE CHECK

```
ENVIRONMENT:
- git_sha:               124e71125ec1c97fc05901f74b9e508820dc8f09
- cache_version:         46
- skill_hash:            6208fc2a2d5ba98d31f56ace90d6f6e35edf5a013082553f7299146405e30a42
- prompt_hash:           446b076922120cd426d68843537e91f95339b415f75beeaa66bd53722b6fa23b   (grammar_card)
    geometry_analyze:            604768bbf466aaf2000d026bb25d683e703dbcdb1d3a926fc7d86f53a89ed6bd
    geometry_program_generator:  b5916c98c5f2e1480b3de546cc7a8057956849c3e1923c01e44f4296fe4a4132
- metric_contract_hash:  ae454123cbbfe676a4dfc9a11d6ebe84c02a749dfcde385e46f23dd5a681d738
- expectation_hash:      ⛔ THIẾU FILE — expectations/holdout.json chưa tồn tại
    (pilot.json, không dùng cho 7B:  f9fdd1362b29fa49d0ecde673d15ba56f6a173ec152e8b2b8ef85dcacd8451b5)
- dirty_files:           (không có — cây sạch)
```

Cộng thêm hai băm mà giao thức held-out đòi nhưng STEP 0 không liệt kê:

```
- measured_system_hash:  7ab25683ce4e4e4d0e56efb3cb291378e7bde7127cd316eefe9702981735ce00  (144 file)
- freeze --verify:       PASS — candidate khớp bản đã đóng băng
```

### Ba mục ĐẠT

| Mục | Trạng thái |
|---|---|
| Cây làm việc sạch | ✅ `git status --porcelain` rỗng |
| `CACHE_VERSION` | ✅ 46 — khớp `CURRENT_STATE.md` |
| Hệ được đo | ✅ `freeze --verify` PASS · nguồn **là** bản đã đóng băng |
| Thước | ✅ `PHASE7_METRIC_CONTRACT §6` đã đóng băng ở 7A.2, trước lượt này |

### Một mục LỆCH — `runtime_doctor` FAIL

```
[RUNTIME_STALE_IMAGE]
  source : 124e71125ec1…   (HEAD hiện tại)
  runtime: 7e732916e527…   (image build từ mốc Phase 6.8)
```

**Đọc cho đúng mức, hai chiều:**

- Container **không nằm trên đường đo**. `run_geometry_dev_evaluation`,
  `measure_geometry_stability` và `run_phase7a_pilot` gọi thẳng `run_pipeline`
  trong tiến trình, **không qua HTTP** — cố ý, để không có cache nào cho một
  kết quả cũ lẻn về. Nên lượt 7B *"chạy trên image cũ"* là **không** xảy ra.
- Nhưng lệch vẫn phải sửa **trước** khi đo. `skill/card/cache` của container
  khớp source; chỉ SHA lệch, và lệch vì bốn commit sau `7e73291` có đụng
  `backend/app` (hai bản vá của 7A.1). Để nguyên thì hồ sơ bằng chứng có hai
  danh tính cùng lúc, và câu *"đo bản nào"* mất một câu trả lời duy nhất — đúng
  thứ mà cả `freeze_evaluation_candidate` lẫn `HOLDOUT_SEAL` sinh ra để chống.

**Sửa** (kèm danh tính build, thiếu là doctor chỉ so được cache/hash):

```bash
GIT_SHA=$(git rev-parse HEAD) BUILD_TIME=$(date -u +%FT%TZ) \
  docker compose up -d --build --force-recreate backend
cd backend && .venv/Scripts/python.exe scripts/runtime_doctor.py
```

Chưa chạy trong lượt này: rebuild là một hành động có tác dụng phụ ngoài kho mã,
và STEP 1 đằng nào cũng chặn nên chưa cần thiết.

### Ghi chú `semantic_route_mode = off`

Cờ sản phẩm đang `off` (đúng `STATUS_LEDGER §4h`: chưa có bằng chứng route sinh
mô phỏng đúng thì bật là sớm). Ba runner đo **tự truyền** `semantic_route="serve"`
nên không bị chặn. Nêu ra vì đây là loại chi tiết sẽ bị đọc nhầm thành *"7B đo
một đường không bật trong sản phẩm"* — nó **là** đường sản phẩm, chỉ chưa mở cho
người dùng.

---

## STEP 1 — HELDOUT DATASET VALIDATION → ⛔ **BLOCKED**

```
TOTAL_CASES:            0
DOMAIN_DISTRIBUTION:    —
OBLIGATION_DISTRIBUTION: —
```

Ba file bắt buộc, **cả ba đều chưa tồn tại**:

| File | Vai trò | Trạng thái |
|---|---|---|
| `holdout/pool.json` | ≥40 bài trích từ **đề thi công khai**, kèm đáp án chính thức + `nguon.url` | ⛔ chỉ có `pool.template.json` |
| `holdout/cases.json` + `HOLDOUT_SEAL.json` | 20 bài **rút bằng seed của GVHD** + con dấu | ⛔ chưa rút |
| `expectations/holdout.json` | nghĩa vụ **dựng/kiểm** kèm `ly_do` trích từ đề | ⛔ chỉ có `holdout.template.json` |

Cổng máy đã sẵn sàng và **đang chặn đúng**:

```
run_geometry_dev_evaluation.py --holdout
  → DungSach: "Không có con dấu … Không có con dấu trong lịch sử thì không
     chứng minh được tập đề không bị sửa sau khi thấy kết quả."
```

### Vì sao tôi KHÔNG tự lấp chỗ trống này

STEP 1 nói *"Không tự tạo bài."* `HOLDOUT_PROTOCOL §0` nói cùng một câu, mạnh
hơn: **"Tôi không thể tự tạo một tập held-out."** Bất kỳ đề nào tôi viết ra thì
tôi đã nhìn, và bốn wave vừa rồi đã sửa hệ theo đúng những chỗ tập DEV hỏng. Một
tập tự soạn sẽ cho một con số **đẹp và vô nghĩa**, và cái tệ hơn là nó **trông
giống** một con số held-out trong luận văn.

Cùng lý do với `expectations/holdout.json`: `geometry_expectations.nap()` **từ
chối nạp** một tập held-out khai `nguoi_danh_gia.loai = "nguoi_do"` (cổng dựng ở
7A.2). Tôi tự soạn kỳ vọng held-out thì chính cổng tôi vừa dựng sẽ chặn — và nó
đúng khi chặn.

### Hai mắt xích, và cả hai nằm NGOÀI kho mã

| # | Mắt xích | Ai cấp | Vì sao không thể là tôi |
|---|---|---|---|
| ① | **Pool ≥40 bài** từ đề thi/đề minh hoạ công khai, có **đáp án chính thức** và **url tra ngược được**, phủ đủ 20 ô của `BANG_O` | nguồn ngoài (Bộ GD-ĐT / sở / trường) | bảo đảm thật không phải *"tôi chưa nhìn"* mà là **"tôi không viết được ra chúng và không sửa được đáp án"** |
| ② | **Một số nguyên làm seed** | **GVHD** | tôi chọn seed thì tôi chọn được cả tập: chạy thử vài seed rồi lấy cái cho điểm đẹp nhất |

Quy trình đầy đủ sau khi có hai thứ trên: `HOLDOUT_PROTOCOL §5` (soạn pool →
seed → rút tất định → niêm phong → **chạy MỘT lượt** → báo cáo).

---

## Việc CÓ THỂ làm ngay, không cần GVHD

Không cái nào tiêu call, và không cái nào đụng hệ được đo:

1. **Soạn `pool.json`** — việc nặng nhất và hoàn toàn nằm trong tay ta. Cần đề
   thật + đáp án chính thức + url, ≥40 bài, phủ 20 ô. Soi bằng
   `seal_geometry_holdout.py --seed 0 --chi-kiem-pool` (chỉ kiểm, không niêm
   phong). `kiem_pool` chặn sẵn: thiếu url · thiếu `phep_chuyen` · ô B mang
   `oracle_result` · `chua_chay_he` ≠ true · **đề trùng tập DEV**.
2. **Soạn `expectations/holdout.json`** theo pool, dùng
   `expectations/holdout.template.json`. Hai cổng sẽ tự bật khi file xuất hiện
   (hiện đang `skip`): mọi bài trong pool phải có kỳ vọng, và ô `A*` phải khớp
   nghĩa vụ mà `BANG_O` gán.
3. **Rebuild container** để đóng `RUNTIME_STALE_IMAGE`.
4. **Chốt ngân sách**: `HOLDOUT_PROTOCOL §5` đã duyệt **6 logic / 8 HTTP mỗi
   bài**; N=20 ⇒ **120 logic / 160 HTTP** cho `k=1`. ⚠️ Giao thức held-out là
   **chạy MỘT lượt** (§2), còn STEP 2 của Phase 7B đòi `k ≥ 3`. **Hai luật này
   mâu thuẫn nhau và phải hoà giải TRƯỚC khi rút seed**, không phải sau: `k=3`
   ⇒ 360 logic / 480 HTTP, gấp ba trần đã duyệt, và câu *"chạy một lượt, trượt
   thì ghi là trượt"* sẽ phải viết lại.

---

## Điều lượt này KHÔNG kết luận

- **Không** một con số nào về chất lượng hệ. Không có tập thì không có phép đo.
- **Không** dùng số DEV thay số held-out. Baseline DEV có sẵn ở
  `dev-results/` · `dev-results-55/` · `PHASE5_5_GEOMETRY_RESULT.md`, và nó là
  **đối chứng cho STEP 6**, không phải kết quả 7B.
- **Không** chấm lại artifact pilot rồi gọi đó là 7B. `construction_match` vẫn
  **chưa từng được đo trong một lượt chạy thật** — đúng như 7A.2 đã ghi.
