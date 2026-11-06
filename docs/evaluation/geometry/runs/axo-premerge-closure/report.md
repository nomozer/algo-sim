# Báo cáo — axo-premerge-closure

**Trạng thái cuối: `READY_TO_MERGE` theo phương án _squash merge_** (mô phỏng tại HEAD cuối `7c52aecc`, cây `0d7ddd8a`: 0 phát
hiện publication mới reachable từ `main`; T3 đạt trên cây `aacd8777` của `33e1cda2`, khác cây cuối chỉ ở `docs/`). Theo phương án
_merge giữ lịch sử_: **`BLOCKED`** cho tới khi Owner duyệt **ba** ngoại lệ blob (`23109136`, `28be1ef6`, `f4b76988`; §3). **Chưa merge, chưa push** — task này không có quyền Owner rõ ràng để làm việc đó. Điều kiện còn mở cho
**triển khai** (không chặn merge mã): `POSTGRES_NOT_TESTED`, chạy migration `e437149641fa`. 0 lượt gọi provider.

Nhãn: VERIFIED · INFERRED · UNVERIFIED · BLOCKED.

## 1. Trạng thái Git (VERIFIED từ repository, không từ báo cáo)

| mục | giá trị |
|---|---|
| nhánh / worktree | `integration/axo-hybrid4-reliability` @ `.superpowers/worktrees/axo-hybrid4-integration` |
| HEAD lúc bắt đầu | `b0c2dfe5` (run trước), cây tracked sạch |
| `main` local = `origin/main` = merge-base | `bb61a804` — `main` chưa đi tiếp ⇒ không xung đột, cây sau merge = cây nhánh |
| nhánh trên remote | **không** có; 68/139 commit của nhánh đã công bố qua `origin/integration/axo-pedagogical-construction-hardening` (gồm `6533b586`) |
| tiến trình/agent khác | không thấy (không `index.lock`, không tiến trình node/python/chrome của test khi bắt đầu); chỉ một phiên ghi |
| cây ứng viên đã kiểm (T3) | `33e1cda2`, tree `aacd8777` |
| repo công khai hay riêng tư | UNVERIFIED (`gh` chưa đăng nhập) |

## 2. Thay đổi trong run này

| commit | nội dung |
|---|---|
| `8db058d3` | không phiên ⇒ không gọi provider: `/api/analyze` và `/api/image/extract` cấp phiên khách phía server, trả 401 `session_required`; client gửi lại đúng một lần; test tuyến không thuộc quota đăng nhập qua `tests/route_client.py` |
| `9a7c0ce9` | sửa lỗi kiểu của test mới (tsc bắt, vitest không bắt) |
| `cee124a1` | kiểm tra `session_required` trong Chrome thật |
| `33e1cda2` | đóng băng candidate 103 file `09c1a089…`, `CACHE_VERSION` 132, rebind template K-1/R-1/S-2 (không ghi phê duyệt) |
| commit kế tiếp | báo cáo/bằng chứng (chỉ tài liệu) |

Không đổi: Typed Facts, Hybrid Planner/Compiler, kernel chính xác, verifier, Scene3D contract và frontend Scene3D, trình tự dựng.
Không thêm tính năng trả đáp số, trắc nghiệm hay giao diện giải toán.

## 3. Publication safety

**Mô phỏng merge trong worktree tạm** (detached tại `bb61a804`, đã gỡ): cả hai phương án cho tree `aacd8777` = tree của `33e1cda2`.

| phương án | reachable mới từ `main` (`check_publication_safety.py --range bb61a804..<sim>`) |
|---|---|
| merge giữ lịch sử (`--no-ff`) | BLOCKED 2: `conftest_classroom.py` blob `23109136` (tạo ở `38cb181d` run trước), `test_auth_api.py` blob `28be1ef6` (`6533b586`, đã công bố trên nhánh remote khác) |
| squash | **PASS, 0** (3 047 blob, 1 message) |
| **lần cuối, tại HEAD `7c52aecc`** — merge giữ lịch sử | BLOCKED 3: thêm `logs/an1.log` blob `f4b76988` (xem dưới) |
| **lần cuối, tại HEAD `7c52aecc`** — squash | **PASS, 0** (3 328 blob) |

Cả hai blob trên: dòng bị gắn cờ có **hash trùng khít** một dòng đang nằm trên `origin/main` (`1a16c593`, `60bbfa27`) ⇒ không làm lộ
nội dung nào chưa công bố (VERIFIED bằng so hash, không in giá trị); máy quét chặn vì ngoại lệ khoá theo blob.

HEAD (`--head`): 97 phát hiện, **tất cả cùng blob với cây `origin/main`** ⇒ merge không thêm độ phơi bày; trạng thái ngoại lệ đang
chờ của chúng không đổi (bảng phân loại theo file/blob: `axo-final-reliability-premerge-gate/report.md §11`). Không tạo/sửa ngoại lệ.
Trước khi commit, mọi file sửa trong run này được đối chiếu với danh sách đường dẫn bị gắn cờ: không file nào trùng.

| phát hiện | xử lý | còn lại | rủi ro | cần Owner |
|---|---|---|---|---|
| `23109136` (hằng test) | gỡ khỏi HEAD ở run trước; squash ⇒ không reachable | trong lịch sử cục bộ chưa push | rất thấp (nội dung đã có trên `origin/main`) | chọn phương án merge; nếu giữ lịch sử thì duyệt ngoại lệ blob |
| `28be1ef6` (hằng test) | squash ⇒ không reachable từ `main` | đã công bố trên `origin/integration/axo-pedagogical-construction-hardening` | rất thấp (nội dung đã có trên `origin/main`) | như trên |
| 97 mục HEAD | không đổi | đã có trên `origin/main` | theo bảng run trước (90 traceback có tên người dùng OS: thấp–vừa) | quyết định ngoại lệ/dọn dẹp riêng |

**Phát hiện do chính run này tạo (đã xử lý ở HEAD):** commit bằng chứng `78819539` chép `logs/an1.log` (lượt test trước khi sửa), trong
đó traceback in lại hằng **khoá giả** của test (`GOOGLE_API_KEY` pattern; chuỗi sentinel "TEST_DO_NOT_LEAK" có sẵn trong test trên
`main`, không phải khoá thật). Bộ lọc trước khi chép của tôi chỉ kiểm traceback Python và chuỗi mật khẩu, không kiểm mẫu khoá. Đã gỡ
khỏi HEAD, thay bằng `logs/an1-summary.log`; quét mẫu khoá trên mọi log còn lại: 0. Blob `f4b76988` còn trong commit cục bộ chưa push
⇒ squash: không reachable (kiểm lại bên dưới); merge giữ lịch sử: thêm một ngoại lệ blob thứ ba.

Đánh đổi của squash: các hash bằng chứng trong `EVIDENCE_INDEX`/báo cáo (vd `751d9eff`, `43e8fb8c`, `33e1cda2`) không reachable từ
`main`; 68 commit vẫn có trên nhánh remote khác, 71 commit còn lại chỉ ở nhánh cục bộ ⇒ cần **giữ** nhánh cục bộ (hoặc một tag cục bộ)
làm lưu trữ, không push nó (push sẽ công bố `23109136`). Không viết lại commit nào.

## 4. Session và quota (mục C) — VERIFIED

Lỗ hổng (test đỏ trên tuyến thật): request không cookie được phục vụ; bỏ cookie mỗi lần ⇒ phục vụ mỗi lần; cookie giả ⇒ phục vụ; đọc
ảnh không phiên ⇒ chạy tiếp. Sửa: không phiên hợp lệ ⇒ server tự cấp phiên khách (`issue_guest_session`, cookie `httponly`
`samesite=lax` qua `set_session_cookie` duy nhất), trả 401 `session_required`, **không chạy gì**; client không bao giờ tự khai danh tính.

| tình huống | kết quả |
|---|---|
| khách mới (chưa có phiên) | 401 + cookie, client gửi lại cùng attempt ⇒ phục vụ, trừ 1 lượt (backend test + Chrome thật) |
| khách đã có phiên | phục vụ, trừ 1 lượt |
| cố tình bỏ cookie | 0 lượt chạy provider sau 5 lần gửi; trình duyệt: đúng 1 lần gửi lại, không hiện cảnh |
| cookie giả | 401, 0 lượt chạy |
| hai tab đồng thời | đúng giới hạn (run trước, giữ nguyên) |
| retry cùng attempt ID / qua khởi động lại | không trừ lần 2 (sổ ghi) |
| nhiều request khi quota gần hết | không vượt hạn |

Stress: bộ 15 test sổ ghi + phiên × 10 lượt dưới 4 tiến trình đốt CPU = **150/150**.
**Giới hạn:** chống vượt quota **theo phiên**; **không** chống lạm dụng tuyệt đối theo người (một client có thể xoá cookie, nhận phiên
khách mới và dùng 1 lượt thử của phiên đó) — cần giới hạn theo IP/thiết bị ở task khác.

## 5. PostgreSQL (mục D) — `POSTGRES_NOT_TESTED`

Docker không chạy, không có dịch vụ PostgreSQL, cổng 5432 đóng; không khởi động gì. Đã kiểm trên SQLite: upgrade/downgrade/upgrade +
`alembic check` (run trước), ràng buộc duy nhất, giữ chỗ/chốt nguyên tử, đồng thời, rollback khi ghi lỗi, retry qua khởi động lại.
Trên PostgreSQL các câu `UPDATE … WHERE còn hạn` và ràng buộc duy nhất là SQL chuẩn, khoá theo hàng (INFERRED, chưa kiểm).
Nhiều worker: sổ ghi (DB) giữ đúng quota giữa các worker; **idempotency vẫn trong bộ nhớ một tiến trình** ⇒ hai worker cùng nhận một
attempt có thể cùng thực thi (chỉ trừ 1 lượt, nhưng 2 lượt gọi provider). Dockerfile chạy một tiến trình
(`test_shipped_deployment_runs_one_server_process`) ⇒ giới hạn có kiểm soát.

## 6. Kiểm thử

| kiểm thử | kết quả |
|---|---|
| pytest các file gọi `/api/analyze`/`/api/image/extract` | 579 passed |
| pytest đầy đủ trước đóng băng | 13 864 passed, 14 failed — **cả 14 là trôi seal** (`measured_system` đổi do sửa `backend/app`), hết sau đóng băng (`logs/pytest-before-refreeze-summary.log`) |
| vitest đầy đủ | 134 file / 2 003 |
| build (tsc -b + vite) | lần đầu **FAIL** (lỗi kiểu trong test mới) ⇒ sửa `9a7c0ce9` ⇒ PASS; hai lượt trình duyệt chạy trên `dist` cũ trước đó được giữ là `stale-dist-*`, **không tính** |
| trình duyệt (build đúng) | consistency 41/41 (8 độ rộng + Chrome 110% thật), hai tab 8/8, camera 30/30 (1440×900, 820×1180, 390×844), `session_required` 2/2 |
| seal | khớp 103 file `09c1a089…` |
| **T3** `full-gate.mjs`, worktree detached sạch tại `33e1cda2`, **một lượt** | **FULL_PRODUCT_GATE_PASS** 636 s: pytest 13 878 passed / 7 skipped / 3 deselected / 9 xfailed; vitest 134/2 003; build; demo; crash surface; `git status` sạch trước/sau |
| node harness, cùng cây | 155: 153 pass, 0 fail, 2 skip môi trường |
| publication | §3 |

## 7. Giới hạn còn tồn tại

1. `POSTGRES_NOT_TESTED` — điều kiện mở cho triển khai.
2. Migration `e437149641fa` phải chạy khi triển khai (launcher dev dừng trước revision mới, đúng thiết kế).
3. Không chống lạm dụng tuyệt đối theo người (§4).
4. Idempotency một tiến trình (§5).
5. 97 phát hiện publication có sẵn trên `main` vẫn chờ quyết định ngoại lệ/dọn dẹp.
6. `LIVE_NOT_TESTED` cho bài lăng trụ; không gọi live trong task này.
7. 61 kỳ vọng lịch sử trong fixture cũ lệch hiện trạng (giống `main`).

## 8. Quyết định của Owner

1. **Cho phép merge + push** và chọn phương án: **squash** (khuyến nghị: 0 phát hiện mới; giữ nhánh cục bộ làm lưu trữ bằng chứng) hoặc
   **merge giữ lịch sử** (cần duyệt ngoại lệ cho blob `23109136`, `28be1ef6` và `f4b76988`).
2. Môi trường PostgreSQL được phép trước khi triển khai.
3. Kế hoạch cho 97 phát hiện publication đang có trên `main`.
4. Sau merge: dọn nhánh/worktree — chỉ khi Owner đồng ý; danh sách hiện có trong `handoff.md`.
