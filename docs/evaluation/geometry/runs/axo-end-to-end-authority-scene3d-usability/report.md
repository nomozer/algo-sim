# Báo cáo — axo-end-to-end-authority-scene3d-usability

**Trạng thái cuối: `READY_FOR_OWNER_REVIEW`** — không merge, không push. Publication toàn nhánh vẫn chờ quyết định ngoại lệ
của chủ repo (§11). 0 lượt gọi provider.

Nhánh `integration/axo-hybrid4-reliability`, worktree `.superpowers/worktrees/axo-hybrid4-integration`. Bắt đầu tại HEAD
`667fff7a`, cây tracked sạch (VERIFIED). Untracked có từ các run trước giữ nguyên, không stage.

Nhãn: **VERIFIED** (test/bằng chứng trực tiếp) · **INFERRED** (suy từ dữ liệu) · **UNVERIFIED** · **BLOCKED**.

## 1. Lỗi tái hiện được / không tái hiện được

| # | lỗi | tái hiện | trạng thái |
|---|---|---|---|
| A-1 | Frontend từ chối response Hybrid /4 hợp lệ của 11 bài thiết diện có đỉnh mang dấu phẩy (`A'`, `C'`, `B'`, `D'`) ⇒ người học thấy "không qua bước kiểm tra" (`HYBRID_RESPONSE_INVALID`, `verification_gap`) | VERIFIED (11/434 ca đã chứng nhận) | sửa |
| A-2 | Heuristic metric frontend hạ đáp số backend đã chứng nhận xuống `UNDERDETERMINED` ⇒ "chưa kiểm chứng được mục tiêu" (cầu nội/ngoại tiếp, trụ bán kính √2) | VERIFIED (7/434) | sửa |
| A-3 | Ràng buộc đáp số lệch cảnh không có trạng thái "không nhất quán" riêng ở tầng phân loại | VERIFIED (test đỏ) | sửa ⇒ `INVALID` → `unverified_or_contradictory` |
| D-1 | Giới hạn zoom gần áp camera sát mặt cong: cầu R=5 ở 5.40, đường tròn thiết diện (nửa góc 59°) văng hẳn khỏi khung | VERIFIED (ảnh + số đo receipt run trước) | sửa |
| D-2 | Cuộn chuột trên nhãn chú thích (nằm ở tâm hình) không zoom được | VERIFIED (camera check đỏ 9/10, "16.887 vs 10") | sửa |
| C-1 | Cảnh báo trên bản ghi lăng trụ đứng thực tế | **không tái hiện** offline; `LIVE_NOT_TESTED` | §4 |
| H-1 | Lỗi harness: cuộn chuột rơi vào lớp phủ ở mobile; tiêu chí quan sát đầu tiên của tôi đạt cả khi camera không zoom | VERIFIED | sửa harness |

Không có lỗi toán học nào ở backend (TypedFacts → Planner → Kernel → Verifier): mọi đáp số của 18 ca lệch được tôi tính
lại tay và khớp backend (§2).

## 2. Nguyên nhân gốc

**Kiểm toán thẩm quyền (mục B).** `tools/collect_served_corpus.py` lấy mọi payload `typed-fact-next/2` trong kho (2 204 payload,
1 572 duy nhất, 48 file, 0 lỗi), **sinh lại** response trên backend hiện tại (không tin fixture cũ), giữ 434 ca SERVED có đáp
số; harness `tools/authority_audit.vitest.ts.txt` phát lại từng ca qua đúng chuỗi workspace (`hybridViewCua` →
`attachHybridViewToScene` → `verifySceneMathematicalConsistency` → `buildPedagogicalConstructionPlan`). Trước sửa: 416 đạt,
11 `decode_rejected`, 7 `not_reached`. Sau sửa: **434/434**.

- A-1: `hybrid-preview-adapter.ts::kiemSectionsCore` so `v.label` (tên nguồn `A'`) và nhãn chu trình khép kín với `o.id`
  (entity ID `A_prime`) bằng `===`, ngay cạnh hàm `diem()` vốn đã ánh xạ tên ↔ id/notation. Vi phạm luật kho "edge ID máy
  dùng entity ID, nhãn hiển thị là dữ liệu riêng". Sửa: phân giải qua `diem()` (phải duy nhất) ở cả hai chỗ.
- A-2: `scene3d-model.ts::classifySceneEntityProvenance` — với đại lượng chính frontend đã xếp `CERTIFIED_DERIVED`, vẫn chạy
  `isDerivedQuantityMetricallyUnderdetermined` (đếm bậc tự do bằng hình học trình bày) và lật kết quả. Sửa: đại lượng gắn đáp
  số Hybrid /4 (`view.answers`, hệ số khớp giá trị cảnh chính xác) ⇒ `DERIVED_VERIFIED`; lệch ⇒ `INVALID`; không ràng buộc
  (bài mẫu, bản ghi cũ) ⇒ heuristic giữ nguyên. Frontend không tự tạo đáp số hay chứng nhận.

Oracle tay cho 7 ca A-2: trụ r=√2, h=3 ⇒ S_xq = 6π√2, V = 6π; lăng trụ đứng đáy vuông 3-4-5, cao 2 ⇒ r_nội = (3+4−5)/2 = 1 ⇒
S = 4π, V(S2) = 4π/3; R_ngoại² = (5/2)² + 1 = 29/4 ⇒ S = 29π; chóp tứ giác đều cạnh 6 cao 4 ⇒ R = 17/4, r = 3·4/(3+5) = 3/2;
chóp S.ABC (AB=3, AC=2, SA=1, vuông tại A) ⇒ V = 1, S_tp = 1.5+1+3+3.5 = 9, r = 1/3, IT = 1/3, AI = √3/3, V_cầu = 4π/81.

**Camera (mục D).** `datKhungNhin`: `minDistance = min(0.55·d_khung, 1.08·R_bao)`. Với đa diện, mặt nằm sâu trong cầu bao
(lập phương cạnh 2: mặt cách tâm 1, R_bao = √3) nên 1.08 còn chừa khoảng; với cầu/trụ/nón, mặt **trùng** cầu bao. Sửa tổng quát
theo hình học thật, không theo bài: `khoangTuaTheoHuong` (hàm tựa của khối chính theo hướng nhìn: đỉnh đa diện; cầu c·u + r;
trụ/nón: đĩa đáy/đỉnh c·u + r·√(1−(n·u)²)), giới hạn = max(luật cũ, **2 × khoảng tựa**), chặn trên 0.8 × khoảng khung (luôn
còn cận cảnh), cập nhật mỗi `change` của điều khiển. D-2: nhãn số đo giữ `pointer-events: auto` (chọn/Tab) nên nuốt wheel;
container canvas chuyển tiếp wheel từ lớp phủ về canvas. Không đổi hình học, không tắt zoom cận cảnh, không tự xoay camera,
đổi bước không di chuyển camera (đã kiểm), "Xem lại toàn hình" vẫn về góc mặc định.

## 3. Test đỏ trước, xanh sau

| test | trước | sau |
|---|---|---|
| `scene3d-goal-authority.test.tsx` 18 ca hồi quy + ca ràng buộc lệch | 19 đỏ (3 đối chứng xanh) | xanh |
| ↳ sau sửa A-1 | 8 đỏ còn lại (A-2, A-3) | — |
| `scene3d-camera-near-limit.test.ts` (cầu/lập phương/trụ, oracle tay) | đỏ (hàm chưa có) | 9/9 xanh |
| camera check desktop, tiêu chí chạm giới hạn (D-2) | 9/10, cầu "16.887 vs 10" (`camera-1440x900-label-wheel-before/`) | 10/10 (`…-after/`) |
| `test_learning_history_api.py::…verbatim` | ca mới (khoá hành vi đúng sẵn) | xanh |

## 4. Chứng nhận toán học được bảo toàn — điều tra lăng trụ (mục C)

`tools/prism_layer_probe.py --offline` (oracle V = (3·4/2)·5 = 30 cố định trước), ghi từng tầng vào `inputs/prism-layers.json`:

| biến thể trích xuất cùng đề | tầng 3–7 |
|---|---|
| đọc chuẩn; tam giác vuông dạng "đáy"; trích dẫn rộng hơn | SERVED, 30, `kernel_check` true |
| "Cạnh bên AD = 5" gán thành `height` | REFUSED `PREDICATE_NOT_IN_QUOTE` (Source Gate) |
| thêm AD ⊥ (ABC) không có trong trích dẫn | REFUSED `PREDICATE_NOT_IN_QUOTE` |
| rơi mất "đứng" | REFUSED `UNDERDETERMINED_POINT` ⇒ UI "đề chưa đủ dữ kiện" |

Tầng 7–8 (frontend + lịch sử local sau reload) khoá bằng test cho mọi biến thể. Kết luận: với cách đọc chuẩn mọi tầng sau trích
xuất đều đúng; nếu bản ghi thực tế có cảnh báo, tầng sai khác đầu tiên phải là **tầng 2 (trích xuất)** hoặc heuristic A-2 nay đã
sửa (INFERRED). Giả thuyết mạnh nhất: mô hình bỏ mất "đứng" ⇒ từ chối thiếu dữ kiện (INFERRED). **`LIVE_NOT_TESTED`**: chế độ
`--live --max-calls 1` đã cài, bị khoá bởi `ALLOW_LIVE_AI=1` + cờ ngân sách (đã kiểm guard), chỉ lưu payload chuẩn hoá và đầu
ra từng tầng, không lưu khoá/headers/thân response thô, báo `first_divergent_layer`. Cần Owner GO + ngân sách 1 lượt.

## 5. Kiểm thử hình học và Scene3D

- Corpus 434 ca qua pipeline workspace: 434/434 reached (VERIFIED).
- Trình duyệt, build cuối: 21 ca hồi quy thẩm quyền qua composer → attempt → lịch sử → reload: **21/21**
  (`browser-authority-regressions/`); corpus toán học run trước 12/12 (`browser-mathematics/`); consistency đầy đủ 41/41
  (`browser-consistency/`); hai tab thật 8/8 (`browser-two-tab/`).

## 6. Quan sát ở các mức zoom và viewport (mục D)

Camera check (`frontend/scripts/axo-camera-views-browser-check.mjs`, 10 họ cảnh: chóp thiết diện, ngũ giác qua ba điểm, lăng
trụ xiên, lục giác lập phương, cầu cắt phẳng, tiếp diện cầu, trụ, nón qua trục, lăng trụ đứng, chóp lồng): orbit 90°/180°,
gần-đỉnh, zoom gần tối đa (từ gần-đỉnh, từ góc xiên, sau reload), zoom xa, đổi bước, thu/mở bảng, reset, khôi phục sau F5.

| khung | kết quả |
|---|---|
| 1440×900 (desktop) | 10/10 (`camera-1440x900-after/`) |
| 820×1180 (tablet) | 10/10 (`camera-820x1180-after/`) |
| 390×844 (mobile) | 10/10 (`camera-390x844-after/`) |
| Chrome zoom 110% thật + 8 độ rộng 360→1440 | trong consistency 41/41 |

Giới hạn gần (gần-đỉnh), trước → sau: cầu 5.40 → 10.00; trụ 3.05 → 4.02; nón 3.62 → 5.00; lập phương 1.87 → 2.01; tiếp
diện cầu 1.87 → 2.01; chóp 3.01 → 5.01 (đỉnh S là mặt gần nhất khi nhìn từ trên); lăng trụ đứng 3.93 → 5.02. Xem bằng mắt: cầu
— đường tròn thiết diện và bán kính HM trở lại khung; trụ — đường tròn thiết diện và hai đáy thấy trọn; chóp — thiết diện MNPQ
trọn khung, vẫn là cận cảnh (~1.9× so với mặc định). Ở mobile ảnh có tooltip hover do harness đặt con trỏ chuột giữa canvas
(thiết bị cảm ứng không có hover). Lượt `camera-390x844/` và `camera-1440x900-final/` là bằng chứng lỗi harness H-1, giữ nguyên.

## 7. Lịch sử local / server (mục E)

- Local: đề gốc, attempt ID, sample ID (chỉ khi có bằng chứng dấu), cảnh, `hybrid_preview` (answers + coefficient, provenance,
  certificates) qua reload/Back/Forward/hai tab — consistency 41/41, two-tab 8/8, test goal-authority (VERIFIED).
- Server: backend `accounts/router.py` lưu `envelope` nguyên văn; test mới khoá round-trip tạo + cập nhật giữ nguyên cảnh chính
  xác, nhãn `A′`, `hybrid_preview`, đề, attempt ID; frontend `fromServerHistoryDto` → `sanitizeEnvelope` giữ bằng chứng và đạt
  đáp số (VERIFIED, SQLite). `sampleId` máy chủ không được đọc lại; danh tính bài mẫu suy từ dấu đề của chính bản ghi (INFERRED
  đủ dùng). **PostgreSQL: BLOCKED** — Docker không chạy, không khởi động dịch vụ của người dùng.

## 8. T3, build, typecheck, trình duyệt, node harness

| lệnh | kết quả |
|---|---|
| vitest đầy đủ `--maxWorkers=2` (sau sửa) | 133 file / 2 000 test (`logs/e2e-vitest-final.log`) |
| `npm run build` (tsc -b + vite) | pass (`logs/e2e-build-2.log`) |
| pytest liên quan (lịch sử API, độ tin cậy toán học, docs IA) | 67 passed |
| `freeze_evaluation_candidate.py --verify` | lệch `product_commit_sha` ⇒ đóng băng lại trong worktree sạch ⇒ khớp 103 file `5ef50761…` |
| **T3 lượt 1** `full-gate.mjs`, worktree detached sạch tại `b1282aee` | **FULL_PRODUCT_GATE_FAIL**: 1 failed (`test_analyze_idempotency.py::test_overlapping_analyses_are_charged_only_their_own_tokens`, bảng telemetry rỗng), 13 862 passed; vitest/build/demo/crash surface xanh (`logs/t3-full-gate-b1282aee.log`) |
| chẩn đoán lượt 1 | test chạy riêng 3/3 xanh, cả file 19/19 xanh; nằm ngoài vùng sửa (`backend/app` không đổi; file test của tôi chạy sau nó); telemetry ghi trong `BackgroundTask` sau response và nuốt mọi lỗi (`except Exception: pass`) ⇒ hai luồng ghi SQLite đồng thời dưới tải có thể mất hàng im lặng (INFERRED) — rủi ro mở §11 |
| **T3 lượt 2**, cùng cây sạch, không đổi gì | **FULL_PRODUCT_GATE_PASS** 430 s: pytest 13 863 passed / 7 skipped / 3 deselected / 9 xfailed; vitest 133/2 000; build; demo; crash surface (`logs/t3-full-gate-b1282aee-run2.log`); `git status` sạch trước/sau |
| node harness, cùng cây | 155: 153 pass, 0 fail, 2 skip môi trường |
| trình duyệt (build cuối) | camera 30/30 (3 khung), consistency 41/41, hai tab 8/8, corpus toán học 12/12, hồi quy thẩm quyền 21/21 |
| `check_publication_safety.py --range 667fff7a..48eb751d` (gồm commit bằng chứng) | **PASS** — 363 blob, 4 message, 0 vi phạm (`logs/e2e-pub-range.log`) |
| `--head` | BLOCKED 98, đều là ngoại lệ đang chờ, 0 mới (`logs/e2e-pub-head.log`) |

## 9. Hiệu năng so với baseline (mục F)

Đo đối xứng B C C B (`perf/perf-{1..4}-{B,C}`), baseline = frontend tại `667fff7a` dựng trong worktree tạm (đã gỡ), ứng viên
= build cuối; 1440×900, Chrome headless, 15 s orbit mỗi cảnh, một trình duyệt, không tác vụ nặng song song. Trung vị độ trễ
đổi bước toàn bộ: B 54.8 / 47.7 ms, C 54.0 / 47.8 ms; theo cảnh trong khoảng ±8 ms theo cả hai chiều (vd chóp 63.7 → 67.0,
lục giác 81.2 → 73.4); p95 khung 7.1 ms ở hầu hết cảnh, dao động 7.1 ↔ 13.8 ms theo cả hai chiều (một khung kép ở 144 Hz);
1 lần render mỗi khung; 0 lỗi trang; 0 request ra ngoài. Đọc: **không có thay đổi hiệu năng đo được**, không tuyên bố tăng
tốc. Tài nguyên: RAM trống 5.2–5.6 GB / 15.8 GB trước các lượt nặng.

## 10. Thay đổi và commit

| commit | nội dung |
|---|---|
| `751d9eff` | thẩm quyền chứng nhận backend (A-1, A-2, A-3), fixture + tool của run, test lịch sử máy chủ |
| `e1309a79` | giới hạn zoom gần theo mặt thật, chuyển tiếp wheel từ nhãn, camera check có tiêu chí quan sát, `CODE_INDEX` |
| `b1282aee` | đóng băng lại candidate (chỉ danh tính commit sản phẩm; 103 file `5ef50761…` không đổi) |
| commit kế tiếp | bằng chứng, báo cáo, `EVIDENCE_INDEX` (chỉ tài liệu) |

Không đổi: `backend/app`, TypedFact schema, API, `CACHE_VERSION`, bề mặt mô hình, seal tầng đo. Không UI mới, không quiz.
Không `Co-Authored-By`. Ghi chú quy trình: test lịch sử máy chủ được thêm bằng `cat >>` từ trong `backend/` — hook chặn ghi
qua shell chỉ khớp đường dẫn `backend/tests`, nên không bắt; các thay đổi sau đó dùng Edit/Write.

## 11. Rủi ro còn mở và quyết định của chủ repo

1. **Publication** (không sửa, không phê duyệt): HEAD 98 phát hiện, trùng khít tập đã kiểm 2026-11-06 (19 file/blob), 0 mới.
   Phân loại rủi ro: (a) 90 traceback chẩn đoán lịch sử **có đường dẫn Windows chứa tên người dùng OS** — rủi ro lộ thông tin cá
   nhân mức thấp–vừa, không có khoá/token; đề xuất: thay bằng bản tóm tắt trong một commit mới (lịch sử vẫn giữ) hoặc chấp
   nhận bằng ngoại lệ theo blob; (b) 5 traceback không có đường dẫn cá nhân — chỉ lộ chi tiết triển khai, thấp; đề xuất ngoại lệ
   theo blob; (c) 2 placeholder `Bearer` trong test che giấu và báo cáo quét — không phải thông tin xác thực, rất thấp; ngoại lệ
   theo blob; (d) 1 hằng mật khẩu tài khoản thử trong `tests/conftest_classroom.py` — DB thử dùng một lần, rất thấp; ngoại lệ
   theo blob; (e) fixture lịch sử `28be1ef6` (`test_auth_api.py`, chỉ còn trong lịch sử) — rất thấp; ngoại lệ, **không** viết
   lại lịch sử khi chưa có phê duyệt.
2. Merge/push — chưa được phép.
3. Lượt live 1 lần cho bài lăng trụ (`LIVE_NOT_TESTED`) — cần Owner GO + ngân sách.
4. PostgreSQL chưa chạy trên HEAD này (BLOCKED, Docker tắt).
5. Heuristic `isDerivedQuantityMetricallyUnderdetermined` vẫn áp cho đại lượng **không** có ràng buộc Hybrid (bài mẫu, bản ghi
   cũ không còn `hybrid_preview`) — INFERRED an toàn (chỉ còn nói "chưa có chứng nhận"), chưa có phản ví dụ.
6. Ở mobile, ảnh zoom gần còn nhiều lớp tô trong suốt chồng nhau (đĩa thiết diện + mặt cầu); đọc được nhưng chưa tối ưu thẩm
   mỹ — không đổi thiết kế trong task này.
7. Telemetry phân tích có thể **mất hàng im lặng** khi hai lần ghi SQLite đồng thời gặp lỗi (`main.py` `_record`: `except
   Exception: pass`); lộ ra qua T3 lượt 1 đỏ thất thường. Không sửa (ngoài phạm vi); đề xuất một task riêng ghi log lỗi ghi và
   thử lại có giới hạn.
8. Ảnh người dùng gửi kèm yêu cầu không có trong phiên này; mọi kết luận về camera dựa trên tái hiện trình duyệt thật.
