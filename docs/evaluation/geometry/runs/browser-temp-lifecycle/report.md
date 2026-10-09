# browser-temp-lifecycle — báo cáo (hồ sơ Chrome tồn dư của bộ đo trình duyệt)

Việc hạ tầng kiểm thử, máy local, 0 lượt gọi model. Không đổi sản phẩm (`backend/app`, `frontend/src`), candidate,
`CACHE_VERSION`, giao diện, dựng hình. Sửa: `frontend/scripts/browser-runner.mjs`, `frontend/scripts/compiler-scene-suite.mjs`
(`openFixture`), test mới `frontend/scripts/browser-runner.node-test.mjs`.

## 1. Nguyên nhân (mã + tái hiện)

| # | Bằng chứng | Hệ quả |
|---|---|---|
| 1 | `browser-runner.mjs` (trước sửa) dòng 118: `--user-data-dir=${mkdtempSync(join(tmpdir(), "w12-"))}` — đường dẫn không được giữ; `close()` (390–395) chỉ `ws.close()` + `chrome.kill()` | MỖI `open()` để lại một hồ sơ, thành công hay hỏng. Tái hiện `diagnostics/repro-leak.mjs`: 3 phiên mở/đóng ⇒ 3 thư mục mới, 0 Chrome còn sống |
| 2 | Nhánh mở lại khi trang không dựng (209): `kill` rồi `return this.open()` | thêm một hồ sơ mỗi lần mở lại |
| 3 | Lỗi trong `open()` (`WS_OPEN_TIMEOUT` 132/135) ném mà không diệt Chrome vừa sinh | Chrome + hồ sơ mồ côi |
| 4 | `compiler-scene-suite.openFixture`: `POLL_TIMEOUT`/`TEXTAREA_NOT_READY`/`SUBMIT_NOT_CLICKED` SAU `open()` — người gọi chưa nhận `session` nên không `close()` | Chrome WebGL phần mềm (~5 nhân khi dựng) chạy tới hết script — tăng tải, có thể góp phần vào chuỗi `WS_OPEN_TIMEOUT`/`POLL_TIMEOUT` ở các lượt đo gần đây (giả thuyết, chưa đo riêng) |
| 5 | Mỗi ca của bộ đo mở MỘT phiên (`openFixture`): một lượt `measure.sh` ≈ 56 + 24 + 16 + 24 + 24 + suite phiên | khoảng 1.700 hồ sơ sau vài lượt đo |

Chỉ `browser-runner.mjs` tạo tiền tố `w12-` (tìm mã: 20 script độc lập khác dùng `offl-`, `curved-`, `integ-`, `live-`,
`scope-`, `algosim-audit-`… và cũng không xoá hồ sơ — ngoài phạm vi, §6). `scoped_dir*` là thư mục tạm CHROME tự tạo
(tên mang pid tiến trình tạo; nội dung `CRX_INSTALL`, `<uuid>.tmp` — cài thành phần): phiên ngắn không tạo; phiên 150 s
tạo `<uuid>.tmp` + `chrome_Unpacker_BeginUnzipping…`. Mọi Chromium trên máy (kể cả trình duyệt cá nhân) cũng tạo loại này.

## 2. Sửa

- **Thư mục phiên có chủ**: `<gốc>/w12-XXXX/{owner.json, profile/, tmp/}`; gốc `ALGOSIM_BROWSER_TMP` → `D:/tmp/algosim-browser`
  (Windows, ghi được) → `%TEMP%/algosim-browser`. `owner.json` ghi chủ sở hữu, `runner_pid`, `chrome_pid`, giờ tạo, script —
  ghi TRƯỚC khi Chrome chạy.
- **Chrome viết tạm vào phiên**: `TEMP`/`TMP` của TIẾN TRÌNH CON = `tmp/` của phiên — không đổi môi trường hệ thống; mọi
  `scoped_dir*` của Chrome bộ đo nằm trong phiên và bị xoá cùng phiên.
- **Dọn có thứ tự**: `_donDep()` diệt ĐÚNG cây tiến trình của phiên (`taskkill /PID <pid> /T /F`, không bao giờ theo tên
  `chrome.exe`), chờ thoát (≤ 10 s), rồi xoá thư mục (thử lại 20 × 250 ms khi tệp còn bị giữ; hỏng thì `owner.json` ở lại
  cho lượt quét sau). Gọi ở `close()`, khi `open()` ném, trước khi mở lại; phiên còn mở lúc Node thoát được dọn đồng bộ
  (`exit`; SIGINT/SIGTERM/SIGBREAK đổi thành thoát có `exit` nếu script chưa tự xử lý).
- **Orphan khi bị giết cứng** (`timeout --signal=KILL`): `open()` đầu tiên mỗi tiến trình gọi `donOrphan(gốc)` — chỉ
  thư mục `w12-*` có `owner.json` của runner; `laOrphan` (hàm thuần) → `GIU` nếu thiếu/sai chứng nhận hoặc `runner_pid`
  còn sống (pid tái dùng ⇒ giữ — an toàn), `DIET_ROI_DON` nếu Chrome của phiên còn sống VÀ dòng lệnh của nó chứa đúng thư
  mục, ngược lại `DON`. Không dựa vào tuổi hay tiền tố.
- **`openFixture`** đóng phiên khi bước sau `open()` hỏng rồi ném tiếp.

## 3. Kiểm chứng (`results/LIFECYCLE_VERIFICATION.json`, Chrome thật, gốc `D:/tmp/algosim-browser`)

| Kịch bản | Kết quả |
|---|---|
| A · 5 phiên tuần tự | ✓ gốc 0 → 0 thư mục, Chrome của bộ đo 0 → 0 |
| B · 3 phiên song song, đóng một | ✓ đỉnh 3 thư mục / 30 tiến trình Chrome; đóng một ⇒ 2 thư mục còn, hai phiên kia vẫn trả lời CDP; đóng hết ⇒ 0 |
| C · Chrome chết lúc khởi động | ✓ `WS_OPEN_TIMEOUT`, thư mục đã xoá |
| D · lỗi trong phiên, `close()` ở `finally` | ✓ |
| E · Chrome sập giữa phiên rồi `close()` | ✓ |
| F · `openFixture` hỏng sau `open()` (`POLL_TIMEOUT`) | ✓ không còn Chrome, không còn thư mục |
| G · runner bị giết cứng (`SIGKILL`) | ✓ thư mục mồ côi còn lại; tiến trình sau quét và xoá («dọn 1 thư mục phiên mồ côi đã xác nhận») |

Mọi kịch bản: `%TEMP%\w12-*` 674 → 674 (không tăng), Chrome ngoài gốc 0 → 0. Giới hạn: ở G Chrome của runner bị giết đã tự
thoát, nên nhánh `DIET_ROI_DON` chỉ được kiểm ở unit test; không có Chrome cá nhân đang chạy trong lúc kiểm (trình duyệt
của người dùng là Brave) — mã không bao giờ khớp tiến trình theo tên. Phiên dài 150 s: `tmp/` của phiên chứa
`<uuid>.tmp` + thư mục giải nén thành phần, 0 `scoped_dir*` mới trong `%TEMP%`, phiên đóng ⇒ thư mục mất.
Bộ đo thật qua `openFixture` (W05, họ cuboid, bản dựng cũ): 3/3, gốc 0 → 0, `%TEMP%` không đổi, 0 Chrome còn lại.
Unit `browser-runner.node-test.mjs` 5/5; tiêm lỗi (bỏ điều kiện «chủ sở hữu còn sống ⇒ giữ») ⇒ 2 test đỏ, khôi phục ⇒ xanh.
Node harness 102/102. T3 + cổng danh tính: `handoff.md` §2.

## 4. Kiểm kê `%TEMP%` (dry-run, `results/TEMP_INVENTORY.json`, chỉ tên)

| Nhóm | Số | Dung lượng | Lớp |
|---|---|---|---|
| `w12-*` | 671 | 33,5 GB | `VERIFIED_ORPHAN` — tiền tố chỉ `browser-runner` tạo + bố cục hồ sơ Chrome + không tiến trình nào tham chiếu; tạo 2026-10-08 22:08Z → 2026-10-09 06:47Z (các lượt đo phone-landscape-layout / classroom-band-fit) |
| `scoped_dir*` | 229 | 1,3 GB | `UNKNOWN` — không chứng minh được chủ (Chromium nào cũng tạo) |
| `scoped_dir*` | 5 | 1 MB | `ACTIVE` — pid tạo đang sống |

Đã tự dọn: 3 hồ sơ do bước tái hiện của CHÍNH việc này tạo (`w12-D7v70g`, `w12-Ednq8X`, `w12-yEGYcf`), sau khi xác nhận
không tiến trình nào tham chiếu. Không xoá gì khác. Sau bản sửa không có gì tạo `%TEMP%\w12-*` cấp gốc nữa (dự phòng là
thư mục con `%TEMP%\algosim-browser`), nên 671 thư mục là di sản.

**Cần người dùng phê duyệt** — xoá đúng 671 tên trong manifest, kiểm lại từng tên không bị tiến trình nào tham chiếu
(PowerShell, từ gốc kho):

```powershell
$m = Get-Content docs/evaluation/geometry/runs/browser-temp-lifecycle/results/TEMP_INVENTORY.json -Raw | ConvertFrom-Json
$cmd = (Get-CimInstance Win32_Process | Select-Object -ExpandProperty CommandLine) -join "`n"
foreach ($e in $m.entries | Where-Object { $_.kind -eq 'w12' -and $_.class -eq 'VERIFIED_ORPHAN' }) {
  $p = Join-Path ([IO.Path]::GetTempPath()) $e.name
  if ((Test-Path -LiteralPath $p) -and ($cmd -notlike "*$($e.name)*")) { Remove-Item -LiteralPath $p -Recurse -Force }
}
```

`scoped_dir*` `UNKNOWN`: không đề xuất xoá tự động; nếu muốn, chỉ xoá khi mọi Chrome/Brave/Edge đã đóng.

## 5. Ảnh và artifact

Chính sách hiện có đáp ứng phần lớn (`capture-policy.mjs`: quyết trước khi chụp, `toi-thieu` mặc định — ảnh oracle, tập
duyệt chọn trước, ảnh lỗi; JSON ghi số lượt gọi/ảnh tạo/bỏ qua). Bổ sung luật còn thiếu vào `docs/TEST_TIERS.md` (không
thêm mã): ảnh không phải bằng chứng ghi vào thư mục tạm của lượt đo và xoá khi xong; cảnh đã duyệt mà thành phần liên quan
không đổi thì dùng lại bằng chứng cũ; tài nguyên trình duyệt ở gốc có chủ.

## 6. Ngoài phạm vi — ghi nhận

- 20 script độc lập (`certify-*`, `accept-*`, `spot-check-*`, `audit-layout`, `measure-*`, `diagnose-refusal-flake`)
  tự mở Chrome với hồ sơ trong `%TEMP%` và không xoá — mỗi lượt chạy một hồ sơ; hiện không còn thư mục nào của chúng. Cách
  sửa gọn: chuyển sang `BrowserSession`.
- `sourceFingerprint` (`frontend/scripts/evidence.mjs`) băm cả `frontend/scripts` ⇒ artifact dùng hợp đồng provenance v2
  sẽ báo `STALE_SOURCE` nếu kiểm lại — như mọi lần sửa `frontend/src` trước đây; không cổng nào chặn trên điều này.
- Ảnh/log trung gian của các lượt đo trước ở `D:/tmp/classband-logs-*` (log đã chép vào kho) — chưa xoá, chờ người dùng.
