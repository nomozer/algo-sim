# Báo cáo — axo-final-reliability-premerge-gate

**Trạng thái cuối: `READY_FOR_OWNER_REVIEW`** — T3 đạt trên cây sạch, lỗi toán học/thẩm quyền và lỗi quota đã biết đã xử lý.
Kèm điều kiện rõ: một phát hiện publication **do task này tạo** trong lịch sử cục bộ chưa push (§9.1), `POSTGRES_NOT_TESTED`,
`LIVE_NOT_TESTED`. Không merge, không push, 0 lượt gọi provider.

Nhánh `integration/axo-hybrid4-reliability`, worktree `.superpowers/worktrees/axo-hybrid4-integration`. Bắt đầu tại `c5cef563`, cây
tracked sạch, seal khớp (VERIFIED). Untracked của các run trước giữ nguyên.

Nhãn: **VERIFIED** · **INFERRED** · **UNVERIFIED** · **BLOCKED** · `POSTGRES_NOT_TESTED` · `LIVE_NOT_TESTED`.

## 1. Nguyên nhân gốc

**P0-1 — lỗi T3 `test_overlapping_analyses_are_charged_only_their_own_tokens` (VERIFIED).** Tái hiện dưới tải CPU có kiểm soát
(4 tiến trình đốt CPU): 7/16 đỏ. Bọc tạm `record_analyze_telemetry` để bắt ngoại lệ đang bị nuốt: `FlushError … NULL identity key`
và `IndexError: tuple index out of range` — dấu hiệu hai luồng dùng chung **một** kết nối sqlite3. Gốc: fixture test `api`
(`backend/tests/conftest_classroom.py`) dùng `StaticPool` (một kết nối cho mọi luồng request). Sản phẩm dùng pool thường nên
không bị đúng lỗi này. Sửa fixture (mỗi luồng một kết nối như engine sản phẩm) ⇒ cùng điều kiện tải 30/30 xanh, 0 ngoại lệ,
60/60 hàng ghi được.

**P0-2 — sổ ghi lượt dùng của sản phẩm (VERIFIED, test đỏ trên tuyến `/api/analyze` thật qua `staging-replay`, 0 lượt gọi
provider).** Lỗi kiểm toán thấy được, độc lập với pool:

| lỗi | cơ chế cũ | bằng chứng đỏ |
|---|---|---|
| khách vượt lượt thử | cổng chỉ **kiểm**, trừ sau khi phục vụ (kiểm-rồi-làm) | giới hạn 1, hai tab ⇒ 2 mô phỏng (200, 200) |
| vượt quota ngày | như trên | còn 1 lượt, 3 lượt đồng thời ⇒ cả 3 phục vụ |
| mất cập nhật | `used_today + 1` đọc-sửa-ghi trong Python | 6 lượt đồng thời ⇒ `used_today` = 1 |
| trừ trùng sau khởi động lại | chỉ có bảng idempotency trong bộ nhớ | retry cùng attempt ID ⇒ trừ 2 |
| phục vụ miễn phí khi ghi lỗi | quota tăng trong background task telemetry, `except: pass` | ghi `user_account_meta` lỗi ⇒ SERVED, `used_today` = 0 |
| telemetry lỗi làm mất quota | quota và telemetry chung một giao dịch nền | lỗi INSERT telemetry ⇒ `used_today` = 0 |

Sửa ở một thẩm quyền (`backend/app/accounts/router.py`): bảng `analysis_usage_ledger` (ràng buộc duy nhất `(scope,
attempt_key)`, migration `e437149641fa`); `reserve_analysis_usage` — cổng tạm khoá/bảo trì, rồi **trong một giao dịch, trước mọi
lời gọi provider**: hàng sổ của attempt + `UPDATE … +1 WHERE còn hạn` một câu lệnh (lượt khách hoặc quota ngày, gồm cả đổi ngày
và lượt thưởng); retry của attempt đã `reserved`/`charged` không tính lại (kể cả sau khởi động lại); `finalize_analysis_usage` —
SERVED ⇒ `charged`, ngược lại ⇒ `released` + hoàn lượt nguyên tử. Lỗi sổ ⇒ 503 `USAGE_LEDGER_UNAVAILABLE`
(`INFRASTRUCTURE_FAILURE`), **không chạy gì**. Telemetry tách hẳn: chỉ quan sát, lỗi được log `algosim.telemetry`, không nuốt im.

Hành vi theo các tình huống yêu cầu:

| tình huống | kết quả | mức |
|---|---|---|
| hai tab cùng khách | đúng giới hạn (1 phục vụ, 1 nhận 402) | VERIFIED |
| hai tài khoản đồng thời | mỗi tài khoản trừ 1 | VERIFIED |
| retry cùng attempt ID (mất response) | replay, không trừ thêm | VERIFIED (test idempotency có sẵn) |
| retry sau lỗi 502/503 | trừ đúng 1 khi lần sau phục vụ | VERIFIED |
| khởi động lại tiến trình rồi retry | không trừ lần 2 (sổ bền trong DB) | VERIFIED |
| DB lock/busy khi giữ chỗ | 503, không gọi provider, không trừ | VERIFIED (tiêm `database is locked`) |
| ghi thành công một phần | không thể: hàng sổ + bộ đếm trong một giao dịch; xung đột chèn ⇒ rollback cả hai | VERIFIED (cấu trúc) + test chèn trùng |
| phân tích xong nhưng chốt sổ lỗi | log lỗi; attempt vẫn bị tính (fail closed) | VERIFIED (mã) |
| tiến trình chết sau phân tích, trước khi chốt | hàng ở `reserved`, lượt đã tính trước khi gọi provider | VERIFIED (test giữ chỗ trước provider) |

**Giới hạn — không tuyên bố "chính xác một lần" tuyệt đối.** (a) Attempt lỗi mà tiến trình chết trước khi hoàn lượt ⇒ người học
mất 1 lượt (fail closed; nhận diện được qua hàng `reserved` cũ). (b) Request không có `Idempotency-Key` (client cũ) được cấp khoá
ngẫu nhiên: không có danh tính retry. (c) Request không có cookie phiên không bị giới hạn (hành vi có từ trước; frontend luôn gọi
`/api/auth/me` trước) — rủi ro mở §9. (d) Token provider trong telemetry: mỗi lần **thực thi** là một hàng (chi phí thật); replay
không ghi; telemetry không gắn attempt ID.

**C — thẩm quyền kết quả toán học (VERIFIED).** `tools/classify_corpus.py` tính lại toàn bộ 1 577 payload TypedFacts v2 duy nhất
trong kho trên backend hiện tại: 436 SERVED có chứng nhận (mọi mục tiêu có đáp số chính xác, `kernel_check` true) · 156 SERVED chỉ
dựng hình · 985 REFUSED đúng nhóm hợp đồng · **0** REFUSED nội bộ/bất thường · **0** SERVED thiếu chứng nhận · **0** lỗi. Phát lại
phía frontend (`tools/classified_audit.vitest.ts.txt`): 436/436 đạt và **đúng giá trị** (góc so theo cos² chính xác), 985/985 từ
chối giữ nguyên mã và nhóm, không hiện cảnh; 156/156 chỉ dựng hình không tự sinh số. Đối chiếu kỳ vọng ghi kèm (934 payload): 61
lệch — **giống hệt trên `main` `bb61a804`** chạy cùng tập payload ⇒ kỳ vọng lịch sử trôi theo thay đổi chính sách trước đó, không
do nhánh này. Nhánh vs `main`: đúng 1 ca khác — nhánh phục vụ thiết diện qua ba trung điểm (S = 4, tính tay: hình vuông cạnh 2),
`main` từ chối. Sửa A-1/A-2/A-3 của run trước giữ nguyên.

**E — lăng trụ đứng (V = 30).** Đầu vào → Typed Facts → Planner → Kernel → chứng nhận → Goal Summary → lịch sử đã đúng ở run trước
cho cách đọc chuẩn. Thêm: cùng tuyến thật với các biến thể gõ (NFD tổ hợp dấu, khoảng trắng kép, không cách quanh "=", khoảng trắng
không ngắt) ⇒ đều SERVED 30 (`tools/prism_text_variants.py`, `logs/prism-text-variants.log`). Nguyên nhân cảnh báo trên bản ghi
thực tế **UNVERIFIED** — không quy cho LLM khi chưa có bản trích xuất thật; đầu dò live 1 lượt
(`axo-end-to-end-authority-scene3d-usability/tools/prism_layer_probe.py --live --max-calls 1`) khoá, `LIVE_NOT_TESTED`.

## 2. Test đỏ trước sửa, xanh sau sửa

| test | trước | sau |
|---|---|---|
| `test_overlapping_analyses…` dưới tải | 7/16 đỏ | 30/30 (sửa fixture), 20/20 (sau sửa sổ) |
| `test_analysis_usage_ledger.py` (11) | 8 đỏ / 3 xanh | 11/11; 10 lượt dưới tải = 110/110 |
| `test_v28…telemetry` | — | cập nhật: lượt phục vụ được trừ bởi sổ (đường thật), thêm kiểm giữ chỗ cũng chặn 429 |
| `test_two_independent_submits…` | đỏ khi tôi import hằng theo tên | xanh: đọc `policy.GUEST_TRIAL_LIMIT` lúc gọi |

## 3. Kiểm thử đồng thời

Xem §1 bảng tình huống. Ổn định: 10 lượt bộ sổ (110 test) và 20 lượt test telemetry, tất cả dưới 4 tiến trình đốt CPU: 0 đỏ.

## 4. Đối chiếu baseline / candidate

- Kết quả toán học: nhánh so với `main` trên cùng 1 577 payload — 1 khác biệt có chủ đích (năng lực mới), §1.
- Frontend: không đổi trong task này (`git diff e1309a79..HEAD -- frontend` rỗng) ⇒ hiệu năng Scene3D đo ở run trước giữ nguyên.
- Backend: thêm 2 giao dịch ngắn mỗi `/api/analyze` (giữ chỗ, chốt) — số đo ở §7.

## 5. Kết quả toán học

§1 mục C: 1 577/1 577 nhất quán backend ↔ frontend; 0 kết quả thiếu chứng nhận; 0 từ chối bất thường.

## 6. Scene3D

Build mới, frontend không đổi: camera 10 họ cảnh (chóp + thiết diện, ngũ giác ba điểm, lăng trụ xiên, lục giác lập phương, cầu cắt
phẳng, tiếp diện cầu, trụ, nón qua trục, lăng trụ đứng, chóp lồng) × 1440×900 / 820×1180 / 390×844 = **30/30** (gồm tiêu chí quan sát
zoom gần từ gần-đỉnh, góc xiên, sau reload); consistency **41/41** (8 độ rộng 360→1440, Chrome zoom 110% thật, F5, Back/Forward);
hai tab **8/8**.

## 7. T3 và các lần thất bại

| lượt | cây | kết quả |
|---|---|---|
| T3 run trước (`b1282aee`) lượt 1 | — | FAIL (test telemetry) — đã chẩn đoán và sửa gốc ở §1 P0-1; receipt giữ trong run trước |
| T3 run trước (`b1282aee`) lượt 2 | — | PASS (giữ nguyên trong run trước) |
| **T3 run này**, một lượt, worktree detached sạch tại `4a05ccff` | `git status` sạch trước/sau | **FULL_PRODUCT_GATE_PASS** 501 s: pytest 13 874 passed / 7 skipped / 3 deselected / 9 xfailed; vitest 133 file / 2 000; build; demo; crash surface (`logs/t3-full-gate-4a05ccff.log`) |
| node harness, cùng cây | | 155: 153 pass, 0 fail, 2 skip môi trường |
| pytest ngoài geometry (trong lúc sửa) | | 1 997 passed; còn seal (đóng băng lại ⇒ xanh) |
| seal / template / migration drift / cache identity | | 191 passed; `alembic upgrade → downgrade → upgrade` + `alembic check` sạch |
| chi phí sổ ghi (`tools/measure_usage_ledger.py`, SQLite tạm, 200 attempt) | | trung vị 12.4 ms (khách) / 14.5 ms (học sinh), p95 16.1 / 18.5 ms |

Không có lượt T3 thất bại trong run này.

## 8. Commit và thay đổi

| commit | nội dung |
|---|---|
| `38cb181d` | fixture `api` bỏ `StaticPool` |
| `43e8fb8c` | sổ ghi lượt dùng + migration + test |
| `4bcc1368` | mật khẩu test sinh lúc chạy (gỡ phát hiện publication khỏi HEAD) |
| `4a05ccff` | đóng băng candidate (103 file `5a7f4eba…`, `CACHE_VERSION` 132), rebind template K-1/R-1/S-2 |

Không đổi: TypedFact schema, API công khai (thêm mã hạ tầng `USAGE_LEDGER_UNAVAILABLE` trong nhóm `INFRASTRUCTURE_FAILURE` có sẵn),
`CACHE_VERSION`, bề mặt mô hình, frontend. **Có migration mới** (`e437149641fa`, chỉ thêm bảng) ⇒ triển khai cần `alembic upgrade
head` (launcher dev dừng trước revision mới — đúng thiết kế).

## 9. Rủi ro còn mở

1. **Publication do task này gây ra:** commit `38cb181d` tạo blob `23109136` của `conftest_classroom.py` còn chứa hằng mật khẩu
   test (đã gỡ khỏi HEAD ở `4bcc1368`). Quét phạm vi task: BLOCKED 1. Không viết lại lịch sử khi chưa được phép.
2. `POSTGRES_NOT_TESTED` (Docker tắt): migration, cô lập tài khoản, ghi đồng thời, rollback trên PostgreSQL chưa chạy.
3. `LIVE_NOT_TESTED`: nguyên nhân cảnh báo lăng trụ thực tế.
4. Request không cookie phiên không bị giới hạn lượt (có từ trước).
5. Idempotency vẫn trong bộ nhớ một tiến trình (sổ ghi thì bền); triển khai nhiều worker cần idempotency dùng DB.
6. 61 kỳ vọng lịch sử trong fixture cũ lệch hiện trạng (giống `main`) — nên cập nhật hoặc đánh dấu lỗi thời ở task riêng.

## 10. Quyết định của Owner

1. Publication: blob `23109136` do task này tạo (chấp nhận ngoại lệ theo blob, **hoặc** cho phép gộp commit cục bộ chưa push
   `38cb181d` trước khi merge) và 97 mục đang chờ + fixture `28be1ef6` theo bảng §11.
2. Migration `e437149641fa` (chỉ thêm bảng) — cần chạy `alembic upgrade head` khi triển khai.
3. Môi trường PostgreSQL được phép (Docker) để chạy `-m postgres` + migration lên/xuống.
4. GO + ngân sách 1 lượt live cho đầu dò lăng trụ.
5. Chính sách cho request không có cookie phiên (hiện không giới hạn).
6. Merge/push.

## 11. Publication — phân loại theo file/blob

HEAD: 97 phát hiện, tất cả là ngoại lệ đang chờ (trước task: 98; mục `conftest_classroom.py` đã gỡ khỏi HEAD). Không thêm ngoại lệ.
Bảng (metadata-only, không giá trị nào bị in):

| # | file | blob | where | rule × lines | data type | risk if public | proposed handling | owner decision |
|---|---|---|---|---|---|---|---|---|
| 1 | `backend/tests/conftest_classroom.py` | `1a16c593` | history only (removed from HEAD in `4bcc1368`) | HARDCODED_PASSWORD×1 | test-account password constant (throw-away DB) | very low: constant of a disposable test DB, never a service credential | blob exception; no history rewrite | required |
| 2 | `backend/tests/test_dev_backend_launcher.py` | `5aa9000c` | HEAD | BEARER_TOKEN×1 | `Bearer` placeholder in a redaction test / its report (not a credential) | very low: no secret | blob exception | required |
| 3 | `docs/evaluation/geometry/photo-problem-to-scene/docker-backend-dev-auto-refresh/SECRET_SCAN.json` | `d2a4702c` | HEAD | BEARER_TOKEN×1 | `Bearer` placeholder in a redaction test / its report (not a credential) | very low: no secret | blob exception | required |
| 4 | `docs/evaluation/geometry/runs/classroom-band-fit/diagnostics/attempts/a1_9284202d/fixtures_9284202d.log` | `d7292aab` | HEAD | PY_TRACEBACK×17 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 5 | `docs/evaluation/geometry/runs/cuboid-final-review/results/logs/PRE_FREEZE_FULL_BACKEND_fac2769e.log` | `a23e7b70` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 6 | `docs/evaluation/geometry/runs/exact-dimensions/diagnostics/attempt2/evidence_fe83c46e.log` | `6df0a514` | HEAD | PY_TRACEBACK×6 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 7 | `docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/logs/PRE_FREEZE_FULL_BACKEND_ad7172ab.log` | `47af9153` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 8 | `docs/evaluation/geometry/runs/regular-square-pyramid-w01/diagnostics/logs/PRE_FREEZE_FULL_BACKEND_de5b2331.log` | `ccb887b7` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 9 | `docs/evaluation/geometry/runs/regular-square-pyramid-w03/diagnostics/attempts/attempt1_47941832/EVIDENCE_BUILDER_47941832.log` | `20d5ae68` | HEAD | PY_TRACEBACK×6 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 10 | `docs/evaluation/geometry/runs/regular-square-pyramid-w03/diagnostics/attempts/attempt1_47941832/OCCLUSION_47941832.log` | `02896a37` | HEAD | PY_TRACEBACK×6 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 11 | `docs/evaluation/geometry/runs/regular-triangular-pyramid-w01/diagnostics/attempts/attempt2_1bb11018/EVIDENCE_BUILDER_1bb11018.log` | `2dfd119f` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) | low: implementation detail only | blob exception | required |
| 12 | `docs/evaluation/geometry/runs/shared-ask-grammar-safety/evidence-reconciliation-55c657b8/green-55c657b8/suite6-full-geometry-regression-55c657b8.txt` | `ccc702fb` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 13 | `docs/evaluation/geometry/runs/shared-ask-grammar-safety/verification/suite6-full-geometry-regression.txt` | `2f84e90a` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 14 | `docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/logs/PONYTAIL_FULL_SUITE.log` | `05bac6a4` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 15 | `docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/logs/PRE_FREEZE_FULL_BACKEND_cd3a0efa_FULL_OUTPUT.log` | `03215c3a` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 16 | `docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/logs/PRE_FREEZE_FULL_BACKEND_d3817d5f.log` | `96204c6f` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 17 | `docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/logs/PRE_FREEZE_FULL_BACKEND_fadfd10e.log` | `441c021a` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 18 | `docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/logs/PRE_FREEZE_FULL_BACKEND_7a06ee47.log` | `7aff35e7` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 19 | `docs/evaluation/geometry/runs/w20-cleanup-premerge/results/logs/PRE_FREEZE_FULL_BACKEND_8b6a1a3a.log` | `75ddf888` | HEAD | PY_TRACEBACK×5 | Python traceback (local paths, implementation detail) + OS user name | low–medium: discloses the Windows OS user name in paths | replace with a summary in a new commit, or blob exception | required |
| 20 | `backend/tests/test_auth_api.py` | `28be1ef6` | history only | HARDCODED_PASSWORD×1 | test-account password constant (throw-away DB) | very low: constant of a disposable test DB, never a service credential | blob exception; no history rewrite | required |
| 21 | `backend/tests/conftest_classroom.py` | `23109136` | history only — **created by this task** (`38cb181d`) | HARDCODED_PASSWORD×1 | test-account password constant (throw-away DB) | very low: same disposable constant as `1a16c593` | blob exception, or approve squashing local unpushed `38cb181d` before merge | required |
