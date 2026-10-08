# `FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE`

**2026-09-09 · 0 lượt gọi model · 0 lượt gọi provider thật.**
Wave kỹ thuật cuối. Sau wave này **đóng phát triển tính năng**.

```
FINAL_SYSTEM_RELEASE = PASS
ROOT_CAUSE      = transport giữa headless Chrome và Vite DEV SERVER
SELECTED_BRANCH = C (khác biệt môi trường) + một khiếm khuyết NHÃN thuộc nhánh B
```

---

## §1 · Flake: từ "17–19/21" tới một nguyên nhân tất định

Wave trước bàn giao `certify-refusal-surface.mjs` chập chờn, chưa có nguyên
nhân. Đo lại **10 lượt liên tiếp, giữ từng assertion** (`flake-repeat.mjs`):

```
LƯỢT SẠCH 1/10 · FLAKE_RATE 0.9
  6/10  OUT_OF_DOMAIN · nhãn            6/10  OUT_OF_DOMAIN · có đường quay lại
  3/10  UNSUPPORTED_CAPABILITY · nhãn   3/10  UNSUPPORTED_CAPABILITY · …
  3/10  GROUNDING_FAILURE · nhãn        3/10  GROUNDING_FAILURE · …
```

Ba dấu hiệu loại ngay giả thuyết "nhãn sai": đỏ luôn đi **theo cặp**
(`nhãn` + `đường quay lại`), luôn rơi vào **kịch bản chạy đầu**, và **không lần
nào** là một nhãn SAI — chỉ là nhãn RỖNG. Trang chưa có gì cả.

Chẩn đoán từng lượt (`diagnose-refusal-flake.mjs`) xác nhận:

```
readyState = complete · url đúng · #root có 0 con · suốt 60 giây
Network.loadingFailed: Script net::ERR_CONNECTION_REFUSED
                       Script net::ERR_NETWORK_ACCESS_DENIED
```

JS chưa bao giờ tới nơi. Không có ngoại lệ sản phẩm nào, vì không có sản phẩm
nào được chạy.

### Bốn phép đo phân xử nhánh

| câu hỏi | phép đo | kết quả |
|---|---|---|
| trang **chậm** hay **kẹt**? | kiên nhẫn 60 s | **kẹt** — 60 s vẫn `#root` rỗng |
| lỗi ở sản phẩm hay ở máy chủ? | `measure-page-boot.mjs`, 15 lượt mỗi bên | Vite dev **kẹt 2/15** · **bản dựng sản phẩm 0/15** |
| tải lại có cứu được? | reload trong cùng phiên | **0/2** — không |
| phiên Chrome mới có cứu được? | `measure-relaunch-recovery.mjs`, 20 lượt | **6/10** — có ích, **không** phải thuốc chữa |

Một giả thuyết bị **bác bằng số**: `127.0.0.1` thay `localhost` không phải lối
thoát — nó **tệ hơn hẳn** (12/12 kẹt, so với 0/12 cùng lúc trên `localhost`).

⇒ `ROOT_CAUSE`: **transport của Vite dev server dưới headless Chrome**, ngắt
quãng và theo cụm. Không phải sản phẩm. Không phải assertion.

---

## §2 · Nhưng bộ đo VẪN có một khiếm khuyết thật, và nó tệ hơn chập chờn

Cổng cũ báo *"nhãn rỗng"* — một khẳng định về **NỘI DUNG** — cho một sự cố
**HẠ TẦNG**. Ai đọc artifact `17/21` sẽ đi sửa `UnsupportedNotice`, tức sửa
đúng thứ đang chạy tốt. Ba nguyên nhân, cả ba là lỗi bộ đo (nhánh B):

1. **Ngủ cố định** `3000 ms` sau `Page.navigate` rồi hỏi một lần.
2. **Không phân biệt** "trang chưa tải" với "trang tải rồi nhưng nội dung sai".
3. **Locator không neo**: `document.querySelector('.eyebrow')` lấy thẻ
   `.eyebrow` ĐẦU TIÊN của tài liệu — trang chủ còn khối *"Gợi ý khám phá"* mang
   lớp ấy. Phát hiện bằng **phép tiêm lỗi**: bỏ nhãn thẻ từ chối mà cổng vẫn
   xanh, vì nó đọc nhãn của thẻ hàng xóm.

### Bản vá

**`certify-refusal-surface.mjs` viết lại** — ba thay đổi, mỗi cái đóng một lỗ:

* **chạy trên BẢN DỰNG SẢN PHẨM** (`vite preview`), thứ buổi demo thật sự chạy;
* **đi qua UI thật + biên `/api/analyze`** thay cho `import('/src/state/…')` —
  vừa chạy được trên bản dựng, vừa đo thêm cả response adapter;
* **chờ theo trạng thái**, và quá hạn thì ném `PAGE_NOT_LOADED` **chứ không ghi
  21 khẳng định rác**.

Vẫn đúng **21** phép kiểm — không assertion nào bị bỏ.

**`browser-runner.mjs`** (dùng chung cho các cổng còn lại): kiên nhẫn 16 s → 40 s;
lỗi đổi tên thành `PAGE_NOT_LOADED` với nguyên nhân thật; **mở lại Chrome có
trần (2) và có ĐẾM** — `pageLoadRetries` báo riêng, không bao giờ gộp vào số
lượt đạt.

---

## §3 · Kiểm tra lặp

| bộ | EXEC | ASSERT/exec | PASS | FAIL | RETRY (mở lại trình duyệt) | FLAKE_RATE |
|---|---|---|---|---|---|---|
| `certify-refusal-surface` **trước** | 10 | 21 | 17–21 | 0–4 | 0 | **0.9** |
| `certify-refusal-surface` **sau** | 10 | 21 | 21 ×10 | 0 | **0 ×10** | **0** |
| `certify-product-ui-rendering` | 3 | 73 | 73 ×3 | 0 | **1, 2, 1** | 0 |
| `certify-scene3d-hidden-lines` | 3 | 23 | — (exit 0 ×3) | 0 | **2, 1, 0** | 0 |
| `scene3d_world_oracles.py` | 3 | 7 ca | exit 0 ×3 | 0 | 0 | 0 |

> Con số đáng chú ý nhất không phải `0`: cổng đã chuyển sang **bản dựng** cần
> **0 lần mở lại** trong 10 lượt, còn hai cổng vẫn chạy trên **dev server** cần
> 1–2 lần mỗi lượt. Đó là cùng một nguyên nhân, nhìn từ hai phía.

---

## §4 · Ma trận bản release

**Bảy ca dương** — `certify-product-ui-rendering` 73/73, ba lượt liên tiếp:
response `ok` · đáp số chính xác từng ký tự · **12/12 đại lượng**
(`doi_chieu_ket_qua_cuoi.py`, 0/31 trường lệch) · trace phát lại được · Scene3D
đúng loại vật · khung nhìn ôm trọn cảnh · nét thấy/khuất đổi theo camera
(`certify-scene3d-hidden-lines` 23/23) · 0 ngoại lệ · 0 rò trạng thái giữa các ca.

**Hai ca âm** — fail-closed giữ nguyên; đủ `stage_reached` · `failure_category` ·
`error_code` · `learner_reason`; nội dung UI không mâu thuẫn (đoạn trùng dài
nhất giữa lý do và gợi ý: `n1` 12 ký tự · `n2` 6, ngưỡng 40); frontend không suy
mã từ chuỗi (guard kiến trúc); envelope cũ thiếu trường vẫn hiện *"Không xác
định được từ phản hồi cũ"*.

**Phép tiêm lỗi** `faultcheck-refusal-surface.mjs`: **4/4 DETECTED** — bỏ nhãn ·
in mã thô · dựng khung 3D dưới lời từ chối · trỏ vào cổng chết (phải là
`PAGE_NOT_LOADED`, exit 2, **không** ghi artifact nghiệm thu).

---

## §5 · Cổng

| cổng | kết quả |
|---|---|
| `pytest -q` | **4807 pass**, 1 skip, 1 deselect — 0 đỏ, cây sạch @ `7dacced` |
| `vitest run` | **813 pass** / 55 file |
| `npm run build` | PASS |
| `certify-product-ui-rendering` | 73/73 ×3 |
| `certify-refusal-surface` | 21/21 ×10 |
| `certify-scene3d-hidden-lines` | 23/23 |
| `scene3d_world_oracles.py` | 7/7 tolerance 0 ×3 |
| `replay_demo_cases` · `audit_demo_crash_surface` | exit 0 · 6/6 biên, 0 ném |
| `doi_chieu_ket_qua_cuoi` | 12/12 · 0/31 lệch |
| `freeze --verify` · `lock_cache_identity --verify` | exit 0 · exit 0 @ v94 |
| artifact lượt live | **45/45 BYTE-IDENTICAL** |
| `git diff --check` | sạch |

**Cache**: wave này **không đụng mã sản phẩm** (`PRODUCT_CODE_CHANGED = NO`) —
chỉ bộ đo và tài liệu. Candidate đo lại: `e40de3b1…`, **không đổi**; model-facing
5/5 **không đổi**. Không có gì để bump, và `CACHE_VERSION` giữ **94**.

---

## §6 · Bàn giao

```
docs/evaluation/geometry/final-system-release/
  RELEASE_MANIFEST.json          hai candidate · 5 băm model-facing · api hash ·
                                 băm cây `dist/` · phạm vi · giới hạn · test_results
  DEMO_SCREENSHOTS.json          12 ảnh, mỗi ảnh: case_id · băm đề · băm phản hồi ·
                                 camera pose · candidate · thời điểm
  demo-screenshots/              9 ca + 3 ảnh SAU XOAY (p3, p6, p7)
  PAGE_BOOT_MEASUREMENT.json     dev 2/15 kẹt · bản dựng 0/15
  RELAUNCH_RECOVERY.json         mở lại gỡ 6/10
  FLAKE_DIAGNOSIS.json           từng lượt + ảnh lúc trượt
  REPEAT_*.json                  5 bộ chạy lặp, giữ từng assertion
  FAULT_INJECTIONS_refusal_surface.json   4/4
docs/DEMO_RUNBOOK.md             12 mục, đủ để người khác chạy
```

⚠️ **Hai danh tính, ghi thành hai trường và không gộp**: `candidate_hash`
(`e40de3b1…`, bản đang đóng gói) và `historical_candidate_hash` (`d72db7c3…`,
bản mà lượt live ĐÃ đo). Cũng vậy với `live_evidence` (bất biến) và
`replay_evidence` (dựng lại hôm nay). **Không viết lại** candidate trong
registration cũ.

---

## §7 · Giới hạn — nói thẳng

* **Cổng trình duyệt trên dev server vẫn có rủi ro môi trường.** Đã giảm bằng
  kiên nhẫn + mở lại có trần, và mở lại được **đếm và báo riêng** — nhưng
  `certify-product-ui-rendering` và `certify-scene3d-hidden-lines` vẫn còn
  `s.mods.store` (import đường dẫn NGUỒN) nên **chưa chạy được trên bản dựng**.
  Chuyển chúng sang bản dựng là việc đúng, và nó **không** được làm trong wave
  này: đó là sửa ba bộ đo vào phút cuối của kỳ đóng băng, đổi lấy một rủi ro
  lớn hơn thứ nó gỡ. Ghi thành nợ: `BROWSER_GATES_ON_PRODUCTION_BUILD`.
* **`DEMO_RUNBOOK` vì thế nói rõ: demo chạy từ BẢN DỰNG**, không từ dev server.
* **Nhãn hiển thị `10/12`** giữ `OPTIONAL_POLISH` — thấy được trên ảnh
  (`Diện tích «đối tượng»`). Sửa nó chạm candidate đã đăng ký.
* **`TARGET_BOUNDARY_PASS = 1/2`** không đổi: `n1` vẫn dừng trước cổng phủ.
* **Ảnh PNG không trùng byte giữa các máy** — theo đúng `§9`, phán quyết thuộc
  oracle ngữ nghĩa/raster đã đăng ký, không thuộc phép so ảnh.
* Một guard đỏ theo thiết kế khi cây bẩn (`test_holdout_readiness_7b`); cây sạch
  thì xanh.

---

## §8 · Đóng phát triển tính năng

`FEATURE_DEVELOPMENT_STATUS = CLOSED`. Từ đây, mọi đề xuất mới ghi vào
`docs/POST_THESIS_BACKLOG.md` mục *Hướng phát triển* — **không** nhập tiếp vào
bản dùng cho khoá luận. Việc còn lại là hợp nhất bản thảo:
`THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW`.
