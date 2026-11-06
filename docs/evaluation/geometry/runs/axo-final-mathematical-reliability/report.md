# Báo cáo — axo-final-mathematical-reliability

**Trạng thái cuối: `READY_FOR_OWNER_REVIEW`** (không merge, không push; publication toàn nhánh vẫn chờ quyết định ngoại
lệ của chủ repo như các run trước — xem §11).

Nhánh `integration/axo-hybrid4-reliability`, worktree `.superpowers/worktrees/axo-hybrid4-integration`.
Baseline `59ed17b4`; `main` `bb61a804` không đổi. 0 lượt gọi provider.

Nhãn: **VERIFIED** = kiểm bằng test/bằng chứng trực tiếp · **INFERRED** = suy từ dữ liệu · **UNVERIFIED** = chưa kiểm ·
**BLOCKED** = thiếu điều kiện/quyền.

## 1. Trạng thái Codex để lại và trạng thái khi tiếp quản

- Codex dừng do giới hạn sử dụng, **không commit gì**. HEAD vẫn `59ed17b4`, đúng nhánh (VERIFIED: `git branch`,
  `git log`). `progress.md` dừng ở checkpoint 2 (16:51); `handoff.md`/`run.json` còn ở checkpoint 1 (cũ hơn thực tế).
- Mọi thay đổi chưa commit có mtime 16:36–16:57 ngày 2026-11-06, trùng phiên Codex (VERIFIED: mtime). Các file
  untracked ở thư mục run khác (`perf/`, `two-tab-run-*`, `nav-after/`, `frontend/dist-*`, `frontend/debug.log`)
  có từ trước, **không thuộc task này** và được giữ nguyên, không stage.
- Sau checkpoint 2 Codex đã chạy thêm 3 nhóm trình duyệt (receipt 16:53–16:57): consistency 41/41, corpus 12/12,
  camera 10/10, trên `dist` build lúc 16:50:09 (sau lần sửa src cuối 16:49:53).

## 2. File đã thay đổi trước khi tôi bắt đầu

Tracked, sửa: `frontend/scripts/axo-scene-consistency-browser-check.mjs`, `frontend/src/components/SimulationWorkspace.tsx`,
`frontend/src/components/problem-statement-source.test.tsx`,
`frontend/src/simulations/domains/geometry/{axo-pedagogical-presentation-policy.test.tsx, axo-reliability-gate.test.tsx,
hybrid-preview-adapter.ts, scene3d-semantic-policy.ts}`, `frontend/src/state/{history.ts, store.ts}`, `frontend/vite.config.ts`.
Mới: `backend/tests/geometry/test_hybrid4_mathematical_reliability.py`,
`frontend/src/simulations/domains/geometry/scene3d-goal-authority.test.tsx`, toàn bộ thư mục run này
(`plan.md`, `progress.md`, `handoff.md`, `report.md`, `run.json`, `resources.jsonl`, `tools/`, `inputs/`, `browser-*/`).

## 3. Phần Codex đã làm và tôi giữ nguyên

Commit nguyên trạng ở **`ac71a439`** (blob `store.ts`, `problem-statement-source.test.tsx` và test backend được dựng
lại đúng byte Codex để lại — test backend 3814 byte, `store.ts` +8/−13 như diff ban đầu — để tách khỏi phần của tôi).

| hạng mục kế hoạch | kết quả của Codex | đánh giá của tôi |
|---|---|---|
| Baseline lăng trụ đứng | Tuyến /4 trả 30, `kernel_check` true; cảnh báo trên ảnh chụp cũ **không tái hiện** bằng facts viết tay | giữ; nguyên nhân cảnh báo live **UNVERIFIED** (không được gọi live) |
| Lịch sử làm rơi `hybrid_preview` | sửa trong `sanitizeEnvelope`, giữ khi `kiemHybridView` chấp nhận | đúng, VERIFIED (test + trình duyệt) |
| `UNVERIFIED` ⇒ "chưa đủ dữ kiện" | thay bằng "chưa có chứng nhận" | đúng: `UNDERDETERMINED` ở frontend gồm cả nhánh rơi mặc định và heuristic bậc tự do (`scene3d-model.ts` `classifySceneEntityProvenance`), không phải chứng minh thiếu dữ kiện |
| Bản ghi cũ mượn đề danh mục | bỏ đối chiếu theo `simulation_id+config`; lần mở mẫu tường minh ghi dấu `problem_statement` | đúng về đề, nhưng gây hồi quy §5 |
| Đáp số lưu ghép với cảnh khác | `HybridAnswerView.coefficient` + so khi kiểm lại | đúng, VERIFIED |
| Corpus 12 ca + oracle độc lập | 8 phục vụ chính xác, 4 từ chối đúng nhóm | giữ; chạy lại 13/13 xanh |

## 4. Phần tôi tiếp tục

1. Kiểm toán ca biên còn thiếu trong corpus (§5): giao điểm hai đường **ngoài đoạn**, song song, chéo nhau, suy biến,
   quan hệ dễ hiểu nhầm. Đã có test cho giao đường–mặt ngoài đoạn (`test_hybrid4_case_c_exterior_intersection.py`) nên
   không viết trùng.
2. Chạy vitest **đầy đủ** (Codex chỉ chạy tập liên quan) ⇒ phát hiện hồi quy, sửa (§5).
3. `CODE_INDEX.md` (sửa mục "Statement provenance" đã sai sau thay đổi, thêm mục run), `EVIDENCE_INDEX.md`.
4. Chạy lại 4 nhóm trình duyệt trên build đã sửa, đóng băng lại candidate, T3, node harness, quét publication.

## 5. Lỗi phát hiện, tái hiện, nguyên nhân, cách sửa

**Lỗi R-1 (hồi quy do sửa của Codex, không phải lỗi toán học) — VERIFIED.** Mở lại bản ghi của một lần mở bài mẫu
tường minh từ lịch sử làm mất `activeSampleId` ⇒ URL chuẩn đổi từ `/simulation/<mẫu>` sang đường dẫn lịch sử, khoá
snapshot UI đổi (`sample:<id>`), và `data-statement-source` thành `learner`.
- Tái hiện: `phase-b-views.test.tsx` (test có sẵn) đỏ `expected null to be 'thiet-dien-chop'`
  (`logs/vitest-full-1.log`); test mới trong `problem-statement-source.test.tsx` đỏ tương tự trước khi sửa.
- Nguyên nhân: `reopenFromHistory` bỏ hẳn mọi nhận diện bài mẫu thay vì chỉ bỏ nhận diện **không có bằng chứng**.
- Sửa (`e2f0cb90`, đúng một chỗ `store.ts::reopenFromHistory`): bản ghi là bài mẫu chỉ khi chính nó mang bằng chứng —
  không có đề người học, khoá `historyIdOf` của mẫu, và dấu `problem_statement` trùng `problemText` của mẫu (dấu do lần
  mở tường minh ghi). Bản ghi cũ không dấu vẫn "thiếu đề" như Codex dự định.
- Tiêm lỗi: bỏ điều kiện dấu ⇒ test "unstamped record" đỏ; hoàn nguyên ⇒ xanh.

**Không tìm thấy lỗi toán học ở backend (Typed Facts → Planner → Engine → Kernel → Verifier).** Oracle tính tay trước
khi chạy, khung A=(0,0,0) B=(4,0,0) C=(4,4,0) D=(0,4,0) S=(0,0,3):

| ca | oracle | kết quả tuyến /4 |
|---|---|---|
| I = DM ∩ BC (M trung điểm AB), BI | I=(4,−4,0), ngoài đoạn BC, BI = 4 | SERVED, 4, I = B + t(C−B) với t = −1 trong khung affine |
| SI cùng cấu hình | √(16+16+9) = √41 | SERVED, `√41` |
| AB ∩ CD | song song ⇒ từ chối INVALID_DATA | `PARALLEL_NO_INTERSECTION` / `geometry_generation_failed` |
| SB ∩ CD | chéo nhau ⇒ từ chối INVALID_DATA | `SKEW_NO_INTERSECTION` / `geometry_generation_failed` |
| SA = 0 | suy biến | `NON_POSITIVE_LENGTH` / `geometry_generation_failed` |
| chỉ "SA ⊥ BC", hỏi thể tích | chân S chưa xác định ⇒ thiếu dữ kiện | `UNDERDETERMINED_POINT` / `insufficient_specification` |
| đối chứng SA ⊥ (ABCD) | 4²·3/3 = 16 | SERVED, 16 |

Tiêm lỗi: tắt phân loại chéo nhau ở engine ⇒ ca `skew-lines` đỏ; cho bridge đọc "SA ⊥ BC" thành SA ⊥ (ABCD) ⇒ ca
`line-perp-line-is-not-height` đỏ (bị Source Gate chặn sớm hơn — phòng thủ nhiều lớp). Cả hai bị giết, chỉ trong
tiến trình test, không sửa file sản phẩm.

Quan sát phụ (không sửa, **INFERRED** là vấn đề trình bày, không phải sai toán): ảnh lăng trụ đứng có dấu vuông ở B —
đó là `BE ⊥ (ABC)` đã chứng nhận (`ENGINE_VERIFIED`), đúng; góc vuông đề cho tại A không có dấu riêng ở bước cuối
(các bước khác **UNVERIFIED**).

## 6. Test đỏ trước sửa / xanh sau sửa

| test | trước | sau |
|---|---|---|
| `phase-b-views.test.tsx` › reopenFromHistory giữ bài mẫu | đỏ | xanh |
| `problem-statement-source.test.tsx` › explicit catalog open … reopens as that sample | đỏ | xanh |
| `problem-statement-source.test.tsx` › unstamped record stays without statement | xanh (sửa của Codex) / đỏ dưới mutant | xanh |
| `test_hybrid4_mathematical_reliability.py` › 7 ca biên | ca mới, không có lỗi để làm đỏ; đỏ dưới 2 mutant | xanh |

Codex ghi các test đỏ của Codex (lịch sử mất evidence, UNVERIFIED ⇒ thiếu dữ kiện, mượn đề, hệ số lệch) trong
`progress.md`; tôi không quan sát lại phần đỏ đó, chỉ xác nhận chúng xanh (**VERIFIED xanh, đỏ = theo Codex**).

## 7. Kiểm thử đã chạy (tuần tự, không chồng tác vụ nặng)

| lệnh | kết quả |
|---|---|
| `pytest tests/geometry/test_hybrid4_mathematical_reliability.py` (trước/sau mở rộng) | 13 → 20 passed |
| `vitest run` 2 file mục tiêu Codex | 22 passed |
| `npm run test:impact` (T0, leo thang `src/` + pytest đầy đủ) | pytest 13 862 passed; vitest 1 đỏ (R-1) ⇒ `IMPACT_GATE_FAIL` |
| `vitest run --maxWorkers=2 src/` trước / sau sửa | 1963: 1 fail / **1964 passed** (`logs/vitest-full-{1,2}.log`) |
| `npm run build` (tsc -b + vite) | pass (`logs/build-1.log`) |
| `pytest tests/geometry/test_docs_information_architecture.py` | 42 passed |
| trình duyệt corpus `--mathematical-corpus` | 12/12 (`browser-mathematics-after-reopen-fix/`) |
| trình duyệt consistency đầy đủ (8 độ rộng, zoom 110% thật, F5, Back/Forward) | 41/41 |
| trình duyệt hai tab thật | 8/8, 29 attempt, 14 request |
| trình duyệt camera 10 họ cảnh | 10/10 |
| `freeze_evaluation_candidate.py --verify` | lệch `product_commit_sha` (frontend/src đổi) ⇒ đóng băng lại trong worktree sạch ở `5af750e8` ⇒ khớp, 103 file `5ef50761…` |
| **T3** `full-gate.mjs`, worktree detached sạch tại `5af750e8` | **FULL_PRODUCT_GATE_PASS** 508 s: pytest 13 862 passed / 7 skipped / 3 deselected / 9 xfailed; vitest 132 file / 1 964; build; demo; crash surface 6/6 (`logs/t3-full-gate-5af750e8.log`); `git status` sạch trước/sau |
| `node --test "scripts/*.node-test.mjs"`, cùng cây | 155: 153 pass, 0 fail, 2 skip môi trường |
| `check_publication_safety.py --range 59ed17b4..HEAD` | **PASS** (189 blob, 3 message) |
| `--head` | BLOCKED 98, đều là ngoại lệ đang chờ, 0 mới (95 traceback, 2 bearer placeholder, 1 fixture) |
| `--range bb61a804..HEAD` | BLOCKED 1, fixture lịch sử `28be1ef6` (đã biết) |

## 8. Không chạy được / không chạy

- Gọi provider live — cấm; nguyên nhân cảnh báo lăng trụ trên ảnh chụp live cũ vẫn **UNVERIFIED**.
- PostgreSQL opt-in (`-m postgres`) — không chạm persistence, không bật Docker theo chỉ dẫn (**UNVERIFIED** trên HEAD này).
- Đường lịch sử **máy chủ** (`upsertServerHistory`/`fetchServerHistory`) có giữ `hybrid_preview` hay không — **UNVERIFIED**;
  chỉ lịch sử cục bộ được kiểm.
- "Tối giản log nhạy cảm" của kế hoạch Codex (mục 5) — **không làm**: mâu thuẫn ràng buộc "evidence bytes stay
  unchanged" của chính kế hoạch và cần quyết định của chủ repo.

## 9. Tác động

- **Kiến trúc**: Hybrid /4 vẫn là tuyến duy nhất; không khôi phục Adapter /3; không chạm `backend/app`, Planner,
  Compiler, Kernel. Mọi sửa nằm ở frontend tầng lưu trữ/trình bày.
- **API/lược đồ**: không đổi wire schema, TypedFact, `CACHE_VERSION`, seal tầng đo (`measured_system` không đổi).
  `HybridAnswerView.coefficient` là trường tuỳ chọn phía client; bản ghi cũ không có trường vẫn hợp lệ.
- **Dữ liệu cũ**: bản ghi bài mẫu tạo trước thay đổi (không dấu) giờ mở lại là "Bản ghi này không lưu đề gốc" và
  không mang URL bài mẫu — đánh đổi có chủ đích để không gán đề cho bản ghi không chứng minh được nguồn.
- **Hiệu năng**: thêm một `kiemHybridView` khi ghi lịch sử và một `find` trên 11 mẫu khi mở lại; không đo (INFERRED
  không đáng kể). Vitest giới hạn 2 worker theo yêu cầu tài nguyên.
- **Tính chính xác**: không có giá trị chính xác nào bị thay bằng xấp xỉ; không nới assertion hay timeout.

## 10. Commit, file, worktree

| commit | nội dung |
|---|---|
| `ac71a439` | công việc Codex nguyên trạng (12 file mã/test + bằng chứng Codex) |
| `e2f0cb90` | sửa R-1, test biên backend, `CODE_INDEX`, bằng chứng trình duyệt sau sửa |
| `5af750e8` | đóng băng lại candidate (chỉ danh tính commit sản phẩm) |
| commit kế tiếp | báo cáo/handoff/run.json/progress, `logs/`, `EVIDENCE_INDEX` (chỉ tài liệu, sau cây đã đo) |

Không `Co-Authored-By`. Worktree tạm `wt-gate` (scratchpad) đã gỡ, junction tháo trước. Untracked có từ trước vẫn còn
nguyên, chưa stage.

## 11. Rủi ro chưa giải quyết / quyết định của chủ repo

1. Publication toàn nhánh: 98 ngoại lệ đang chờ + fixture `28be1ef6` — `OWNER_DECISION_REQUIRED` (không tự phê duyệt).
2. Merge/push — chưa được phép cho task này.
3. Cảnh báo lăng trụ trên ảnh chụp live gốc chưa tái hiện được offline; cần một lượt live có đăng ký ngân sách nếu
   muốn biết nguyên nhân (trích xuất của mô hình hay tầng khác).
4. Lịch sử máy chủ và PostgreSQL chưa kiểm (§8).
5. Heuristic `isDerivedQuantityMetricallyUnderdetermined` ở frontend vẫn có thể hạ một đại lượng backend đã chứng nhận
   xuống `UNDERDETERMINED` trong cấu hình chưa có trong corpus; nay hệ quả chỉ là "chưa có chứng nhận" (không còn khẳng
   định thiếu dữ kiện), nhưng thẩm quyền đúng là chứng nhận backend — **INFERRED**, chưa có ca phản ví dụ.
