# Axo × Hybrid `/4` — tích hợp, định danh lần học và độ tin cậy đầu–cuối

Ngày: 2026-11-05/06. Trạng thái: **READY FOR USER REVIEW — chưa merge vào `main`, chưa push, 0 lời gọi AI live.**
"Đã chạy" và "suy luận" được ghi tách bạch; đường dẫn bằng chứng là tương đối với thư mục run này.

## A. Git baseline

| | |
|---|---|
| `main` | `bb61a804` (Hybrid `/4` cutover), **không bị sửa** |
| Nhánh Axo | `integration/axo-pedagogical-construction-hardening` `67f780ca` |
| Merge base | `f986e897` (= tag `pre-hybrid-cutover-f986e897`); 206 commit chỉ có trên `main`, 91 chỉ có trên Axo; 939 / 883 file đổi mỗi bên, 10 file chồng nhau |
| Nhánh tích hợp | `integration/axo-hybrid4-reliability` (worktree `.superpowers/worktrees/axo-hybrid4-integration`), cắt từ `main` |
| Commit | `75d88a31` merge (cha `bb61a804` + `67f780ca`) · `0d17276c` định danh lần học · `bb2f88a1` E2E · `0151cc68` con dấu + rebind template · `d221c5a4` sửa kiểu test · `1383614d` bằng chứng · `cb564b1e` test auth bỏ literal mật khẩu · commit cập nhật báo cáo. Không `Co-Authored-By`. Commit bằng chứng đầu (`619847bb`, chưa công bố, chứa log pytest có traceback thô) đã được **amend** thành `1383614d` để không đưa traceback vào lịch sử. |
| File bảo vệ | Sửa `frontend/index.html` chưa commit của người dùng nằm ở worktree Axo cũ, **không đụng**. Trong nhánh tích hợp, `index.html` giữ bản `main` (đã gỡ favicon có phép). |
| Không làm | merge vào `main`, push, rebase, cherry-pick, sửa Planner/Compiler/Kernel, gọi AI live |

## B. Hoà giải kiến trúc

Luồng sau tích hợp (đọc từ mã): composer (`ProblemInput.runComposerSubmit`, tạo `attemptId`) → `POST /api/analyze` → Hybrid `/4` (`hybrid_offline` → `typed_fact_next_extraction` → `bridge_v2` → `registry.kiem_nguon` → `planner` → `engine` + kernel → `adapter4_route`) → `docPhanHoiPhanTich`/`docPhanHoiHybrid` (kiểm hợp đồng `/4`) → `store.loadEnvelope(env, sampleId, input, recordId)` → Scene3D (`AxoWorkspaceV62`, kế hoạch sư phạm) + `historyStore` (local) + `/api/history` (máy chủ).

| Thành phần | `main` | Axo | Tích hợp |
|---|---|---|---|
| Tuyến `/api/analyze` | Hybrid `/4` duy nhất | `LLM_ONLY` + Adapter `/3` | **Hybrid `/4`** (`main`) |
| `adapter3_simulation.py` | đã gỡ | +240 dòng tính năng | **gỡ**; 2 test chỉ của Axo gỡ theo (`test_construction_integrity_audit.py`, `test_hybrid_e2e_generalization.py`) |
| `typed_fact_next.SolidSpec` | 6 loại khối | + `"oblique_cylinder"` | **bản `main`** — thêm literal sẽ đổi bề mặt trích xuất (lock, `CACHE_VERSION`) mà engine `main` không xử lý |
| Lịch sử máy chủ, admin, telemetry (`accounts/router.py`, `classroom_models.py`, 2 revision Alembic, middleware `/api/analyze` trong `main.py`) | không có | có | **vào nguyên** (chuỗi Alembic không xung đột) |
| `hybrid-preview-adapter.ts` | validator `/4` (clarification thật, chứng chỉ thiết diện) — bỏ `source_provenance`/`relation_certificates` | validator song song, giữ provenance, clarification dạng khác | **bản `main` + kiểm/mang provenance của Axo** (backend `/4` có gửi hai khối này; Scene3D Axo dùng chúng để gắn dữ kiện với nguồn) |
| `store.setAnalysisError` | phân tích mới lỗi ⇒ xoá mô phỏng/bài giao/lựa chọn cũ | giữ trạng thái + `clientFailure` | **luật `main`** + `clientFailure` và route stack của Axo |
| Đề bài | đóng dấu `envelope.problem_statement` phía client (928fb880) | `active.problemStatement` theo lần mở + nguồn learner/catalog/missing | **hợp nhất** (D) |
| Favicon | đã gỡ (có phép) | còn | **bản `main`**; kiểm 163 file `main` đã xoá: 0 file bị merge thêm lại |

Test sửa vì đã khoá **hợp đồng không tồn tại**: fixture ma trận `/4` của Axo dùng `plane_rule`, `rule`, `producer` mà backend không bao giờ phát (đã thay bằng hằng thật `registry.MAT_SONG_SONG`, `engine.PLANE_SECTION_CERTIFICATE_RULE/_PRODUCER`, assertion giữ nguyên); test F2 của Axo kiểm dạng clarification khác schema `route-d-clarification/1` thật (gỡ; hợp đồng thật khoá ở `hybrid-product-integration.test.tsx`). Test quét chuỗi nguồn của `main` cho đề bài được thay bằng kiểm hành vi tương đương.

## C. Định danh

| Khái niệm | Hiện thực | Dùng cho |
|---|---|---|
| Geometry identity | `historyIdOf(env)` = `simulation_id + config` (không đổi) | nhận bài mẫu; khoá mở không kèm đề |
| **Attempt identity** | `newAttemptId()` = `a` + 128 bit ngẫu nhiên (`getRandomValues`), tạo **một lần khi bấm gửi** (`runComposerSubmit`, dựng từ ảnh) | khoá bản ghi lịch sử local + `history_key` máy chủ (chuỗi mờ ≤ 80) |
| Scene identity | `sceneDigestOf(env)` (băm `scene3d`, bỏ khoá `_…`) | khoá nội dung cũ; kiểm nhất quán |
| Presentation context | `activeSampleId` chỉ cho mở không kèm đề / mở mẫu tường minh; nguồn đề `learner`/`catalog`/`missing` | URL, snapshot UI, Đề bài |

Quy tắc: thử lại mạng nằm **trong** một lời gọi `analyzeViaServer` ⇒ cùng một attempt; bấm gửi lần nữa ⇒ attempt mới (kể cả cùng đề, cùng hình); `reopenFromHistory` truyền chính ID bản ghi ⇒ reload/Back/Forward giữ ID; attempt mới **không bao giờ** nhập vào bản ghi cũ trùng nội dung; khoá nội dung chỉ còn cho mở không có attempt (bài mẫu, bài giao, bản ghi cũ). Idempotency phía máy chủ: không thêm — cache envelope Hybrid khoá theo nguyên văn đề + bề mặt tuyến, nên thử lại sau một phản hồi SERVED là cache hit (suy luận từ mã `hybrid_offline.py`, không đo).

Kiểm (đã chạy, đường gửi thật): `attempt-identity.test.tsx` 5 ca (đỏ khi bỏ `attemptId`: 2 ca); E2E "real composer" — hai lần gửi cùng đề ⇒ 2 attempt `a…`; 502 rồi 200 ⇒ 2 lời gọi, 1 attempt; reload và Back/Forward giữ attempt; `submission-identity.test.tsx`, `record-scene-identity.test.tsx` (trùng tiêu đề, A→B→A, server history khoá cũ/mới). Hai tab: hai `historyStore` dùng chung một storage giữ bản ghi của nhau (đơn vị); **không** chạy hai tab trình duyệt thật đồng thời.

## D. Nguồn đề bài

Nơi đề tồn tại: ô soạn (tạm, **không** dùng làm đề) → request `/api/analyze` → backend (chỉ băm `source_sha256`, không trả) → client đóng dấu `envelope.problem_statement` + `active.problemStatement` → lịch sử local (`originalInput`, `problem_statement` nay được giữ khi sanitize) → máy chủ (`original_input` theo `history_key`) → bài giao (envelope đã đóng dấu). Bài mẫu: đề lấy từ `GEOMETRY_SAMPLES`.

Quyết định **không thêm `problem` vào envelope backend**: đề đã có ở ngữ cảnh request/bản ghi; cache envelope dùng chung giữa các request **cùng nguyên văn**, nên đưa đề vào đó không thêm thông tin mà kéo đề vào bộ nhớ dùng chung. Không đổi `CACHE_VERSION` (vẫn 132 của `main`). Thiếu đề gốc ⇒ "Bản ghi này không lưu đề gốc." (mô tả backend chỉ hiện sau nhãn). Bản ghi bị ghép trước khi có khoá lần học: **NOT_RECOVERABLE** (dữ liệu đã bị ghi đè trước đây).

## E. Bất biến Scene3D

Đã chạy (E2E, bản build tích hợp): đóng băng sâu `scene3d` của envelope rồi chạy render, mọi bước, phát/phát lại, xoay, zoom, chọn, ẩn, cô lập, khôi phục, thu/mở dock, đổi bài, mở lại từ lịch sử — trên 3 cảnh (`cau-cat-mat-phang`, `thiet-dien-chop`, `non-thiet-dien-truc`): **0 lỗi ghi**, JSON cảnh không đổi, bản ghi giữ ID. **Cửa sổ chứng**: đưa lại phép ghi `_auxiliaryShown` tại chỗ ⇒ cả hai kiểm đỏ (`logs/` không lưu lượt tiêm lỗi; mô tả trong commit `bb2f88a1`). Không deep-clone cảnh mỗi frame. Lưu lịch sử chỉ sao chép nông + JSON. Không kiểm: chế độ lớp học trực tiếp (`phien`).

## F. Kiểm thử (đã chạy)

| Cổng | Kết quả | Bằng chứng |
|---|---|---|
| **T3** `scripts/full-gate.mjs`, worktree sạch tại `d221c5a4` | **FULL_PRODUCT_GATE_PASS**: pytest 13782 passed (7 skipped, 9 xfailed), vitest 128 file / 1925, typecheck + build, demo replay, crash surface | `logs/t3-full-gate-d221c5a4.log` |
| T3 lần 1 tại `0151cc68` | **FAIL** ở typecheck: test mới truyền HistoryItem cho DTO máy chủ (lỗi của tôi, sửa ở `d221c5a4`) | `logs/t3-full-gate-0151cc68-build-fail.log` |
| pytest trên cây merge trước con dấu | 17 FAIL / 13765 pass; **cả 17 PASS trên `main`** ⇒ do merge: hash hệ được đo đổi (Axo account backend) và đường dẫn `CODE_INDEX` cũ; sửa bằng đóng băng lại + rebind 3 template (cùng cách `db773228`) + sửa `CODE_INDEX` | `logs/pytest-merged-before-seal-summary.txt`, `logs/pytest-17-on-main.log` |
| Vitest với giới hạn worker | `maxWorkers = floor(luồng/2)` còn hiệu lực; 0 timeout | `logs/vitest-merged-summary.json`, T3 |
| Browser E2E | **36/36** | `browser/receipt.json`, `logs/e2e-final.log` |
| UI harness đầy đủ | **2 × 40/40** | `ui-run-1/`, `ui-run-2/` |
| Candidate seal | đóng băng trong worktree sạch, `--verify` PASS (102 file, `731ee939…`, `CACHE_VERSION` 132) | commit `0151cc68` |
| Publication safety `--head` | **BLOCKED như `main`**: 98 vi phạm, **cả 98** đã ở trạng thái `PENDING_OWNER_DECISION` (bằng chứng lịch sử); `main` 99 cùng trạng thái; **0 vi phạm mới** | chạy lại `scripts/check_publication_safety.py --head` |
| Publication safety `--range bb61a804..HEAD` | **BLOCKED, 1 vi phạm**: `HARDCODED_PASSWORD` ở blob lịch sử của commit Axo `6533b586` (`backend/tests/test_auth_api.py`, mật khẩu kiểm thử literal). Cây hiện tại đã sửa (`cb564b1e`); xoá khỏi lịch sử đòi viết lại lịch sử nhánh Axo ⇒ **không làm**; cần ngoại lệ do chủ sở hữu ghi | `--range` |

## G. Kiểm toán toán học và sư phạm

- Backend toán học là của `main` (Planner/Engine/Kernel không đổi); toàn bộ bộ pytest hình học `main` xanh trong T3. Hai test Adapter `/3` của Axo gỡ cùng module; bất biến trụ xiên, 15π, chứng chỉ hình vuông, khoảng cách chéo nhau có test `main` (22–101 file mỗi chủ đề). **Khoảng trống:** "Case C" (điểm Q ngoài so với thiết diện ngũ giác bị chặn) **không** có test `main` tương ứng.
- 11 route mẫu: đề, tiêu đề, đối tượng render cùng cảnh, không bề mặt đáp án (E2E). Ảnh bước đầu/giữa/cuối + 2 góc xoay cho 5 cảnh: `browser/scene-{thiet-dien-chop,mat-cheo-sac,tru-truc-xien,non-thiet-dien-truc,cau-cat-mat-phang}-{first,middle,last,last-angle-a,last-angle-b}.png`; kiểm mắt: `mat-cheo-sac` bước 3/6 chưa có mặt phẳng/thiết diện; trụ nghiêng giữ OO′ ⊥ OA, nét khuất đáy đứt khi xoay.
- Không tái xuất "Xem kết quả", "KẾT LUẬN", popup, bước kết luận (`scene3d-no-answer-surface.test.tsx` + E2E mọi route).

## H. Hiệu năng (đã chạy, Chrome 157.0.8103.38, Intel UHD Graphics, 1440×900, DPR 1, build production, tuần tự)

**Baseline `main` không đo được bằng cùng kịch bản**: UI `main` không có thư viện/dock bước/chip của Axo (`data-lib-prob`, `dock-steps-ul`, `data-entity-chip`: 0 file trên `main`); harness hết giờ chờ (`perf-before/`, `nav-before/` — giữ làm bằng chứng). Baseline dùng là **Axo `67f780ca`** (UI giống hệt), đo liền nhau với candidate `d221c5a4`.

| Cảnh | Frame median/P95 ms | Render/frame | Đổi bước median/P95 ms | Mở bài median ms | Long task | GPU buffer tạo/xoá | WebGL |
|---|---|---|---|---|---|---|---|
| thiet-dien-chop | 7.0/13.9 → 7.0/13.8 | 1 → 1 | 144.1/190.9 → 104.6/167.6 | 177.7 → 188.1 | 2 → 2 | cân bằng | 1 |
| cau-cat-mat-phang | 7.0/13.9 → 7.0/14.1 | 1 → 1 | 64.0/90.6 → 98.1/170.7 | 180.6 → 173.6 | 0 → 1 | cân bằng | 1 |
| non-thiet-dien-truc | 7.0/14.0 → 7.0/13.9 | 1 → 1 | 76.4/156.9 → 54.4/130.5 | 112.3 → 104.5 | 0 → 0 | cân bằng | 1 |
| tru-thiet-dien-tron | 7.0/14.0 → 7.0/13.9 | 1 → 1 | 77.2/168.4 → 62.5/135.2 | 137.5 → 137.6 | 2 → 1 | cân bằng | 1 |
| cube-hexagon | 7.0/13.9 → 7.0/14.0 | 1 → 1 | 115.9/173.1 → 95.8/143.9 | 289.9 → 188.4 | 2 → 2 | cân bằng | 1 |
| oblique-prism | 7.0/13.9 → 6.9/7.1 | 1 → 1 | 51.9/93.4 → 45.5/61.2 | 109.0 → 104.2 | 0 → 1 | cân bằng | 1 |
| dense-multi-solid | 6.9/7.1 → 7.0/7.2 | 1 → 1 | 75.2/171.6 → 102.9/176.4 | 200.5 → 199.5 | 0 → 2 | cân bằng | 1 |
| **Gộp** | **7.0/13.9 → 7.0/13.9** | **1** | **76.4/173.1 → 80.7/166.2** (n 168) | **137.5/427.9 → 159.5/242.0** (n 21) | **6 → 9** | cân bằng | **1** |

Điều hướng (12 chu kỳ, median/P95 ms): Thư viện lạnh 271.8/318.7 → 260.9/327.3; mở bài lạnh 287.5/332.6 → **311.3/435.4**; mở lại/chuyển bài ấm (= khôi phục lịch sử) 274.6/332.4 → 268.4/337.5; Back 160.7/220.5 → 107.7/135.8; Forward 210.9/242.7 → 215.1/298.1. Phản hồi zoom 30.8/44.2 → 28.7/37.5. 22 lần đổi bài: 1 WebGL context; heap sau GC 17.30 → 19.91 MiB.

**Đánh giá:** frame time, render/frame, context, GPU buffer không đổi. Các số điều hướng ở lượt này **gần gấp đôi** các lượt sáng cùng ngày cho **cả hai** bản ⇒ máy chậm hơn lúc đo. Mở bài lạnh P95 +31 % và median +8 % ở candidate: một lượt 12 chu kỳ, **chưa giải thích được** — không quy cho tích hợp, không loại trừ. Không tuyên bố cải thiện. Không đo được tách thời gian backend (đo offline, không request thật).

## I. Rủi ro còn lại

| Hạng mục | Trạng thái |
|---|---|
| Nhánh tích hợp chạy Hybrid `/4` + Scene3D/trình tự dựng Axo; T3 xanh | **DONE** |
| Định danh lần học (attempt) tách khỏi hình học/cảnh; thử lại không nhân bản | **DONE** (đường gửi thật, E2E) |
| Hai tab trình duyệt thật gửi đồng thời | **NOT TESTED** (chỉ đơn vị với storage chung; localStorage không có giao dịch) |
| Idempotency phía máy chủ cho thử lại trước khi có phản hồi | **NOT IMPLEMENTED** — thử lại sau 502 có thể chạy tuyến hai lần (quota); cần khoá idempotency ở `/api/analyze` nếu muốn chặn |
| Publication safety `--range` | **BLOCKED** — 1 blob lịch sử Axo (`6533b586`, mật khẩu kiểm thử); cần ngoại lệ do chủ sở hữu ghi (agent không ghi) |
| Nguồn đề, không fallback âm thầm | **DONE** (frontend); bản ghi cũ đã bị ghép: **NOT_RECOVERABLE** |
| Bất biến Scene3D | **DONE** cho mọi tương tác đã liệt kê; chế độ lớp học trực tiếp **NOT TESTED** |
| "Case C" (Q ngoài / ngũ giác) không có test `main` | **PARTIAL** — cần một test Hybrid `/4` tương đương |
| Mở bài lạnh P95 cao hơn ở một lượt | **UNEXPLAINED** — cần đo lặp trên máy rảnh |
| Middleware telemetry Axo đệm toàn bộ thân phản hồi `/api/analyze` | **PARTIAL** — chạy được trong T3; chưa đo chi phí bộ nhớ với phản hồi lớn |
| Chrome Ctrl+= thủ công, thiết bị di động thật | **NOT TESTED** (zoom thật 110 % qua tuỳ chọn trình duyệt có trong E2E) |

## J. Mức sẵn sàng merge

**Có thể xem xét merge sau khi chủ sở hữu duyệt**, với các điều kiện: (1) duyệt quyết định không mang `"oblique_cylinder"` và gỡ hai test Adapter `/3`; (2) chấp nhận hoặc yêu cầu xử lý idempotency máy chủ và test Case C; (3) đo lại mở bài lạnh trên máy rảnh; (4) duyệt việc đưa backend tài khoản/lịch sử/telemetry của Axo (2 revision Alembic) vào `main` — chạy `alembic upgrade head` khi triển khai; (5) chủ sở hữu ghi ngoại lệ publication safety cho blob lịch sử `6533b586` (hoặc quyết định khác) vì `--range` đang BLOCKED. Bằng chứng đủ để quyết định; **chưa** tuyên bố "sẵn sàng merge" vô điều kiện.
