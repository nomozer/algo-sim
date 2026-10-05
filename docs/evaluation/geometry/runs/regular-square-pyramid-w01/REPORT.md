# REPORT — regular-square-pyramid-w01

Việc `regular-square-pyramid`, wave W1. Nhánh `feat/regular-square-pyramid`, rẽ từ `main` = `38d41588`.
Brief: `REGULAR_SQUARE_PYRAMID_AND_PEDAGOGICAL_UI`. Kế hoạch và nguyên nhân gốc Phase 1: [`PLAN.md`](PLAN.md).
Bàn giao và các câu hỏi chờ người dùng: [`HANDOFF.md`](HANDOFF.md).

Ràng buộc của cả wave:
- `DEFAULT_MODE = LLM_ONLY`, **0 lượt gọi Gemini**.
- Deletion `frontend/public/favicon.svg` của người dùng giữ nguyên ngoài staging.
- Không push, không merge.

Kết luận: mọi cổng tự động đạt ⇒ **`READY_FOR_HUMAN_VISUAL_REVIEW`**. Review người **`NOT_APPROVED`**.

## 1. Đã làm gì

| phần | commit | tóm tắt |
|---|---|---|
| README cho người mới | `ab98a2df` | bỏ danh sách run/SHA/trạng thái; trỏ `docs/README.md`, `docs/CURRENT_STATE.md` |
| đăng ký trước | `e537dbd9` | PLAN, corpus 17 ca có nhãn, oracle độc lập 17/17 — trước mọi sửa sản phẩm |
| năng lực chóp tứ giác đều | `3bdada32` | xem §2 |
| giao diện ROADMAP §0.1 | `ae9c72a5`, `b2d224f6` | xem §3 |
| bộ đo trình duyệt | `c37b2cc4`, `3ad9442f`, `1310658b`, `ed37f9fa` | cổng mới, kịch bản thứ bảy, ảnh mới (§4) |
| hai lỗi thật bắt ở đầu dò cache | `98e2b8f7`, `9d66c603` | §5 |
| `CACHE_VERSION` 111 → 112 | `de5b2331` | §6 |
| đóng băng candidate lần 1 | `5aaf11ee` | `b2d4187a…` → `4629c3e8…` tại `de5b2331` |
| bằng chứng trình duyệt | `025bbff4` | đo tại `ed37f9fa` (§4) |
| kiểm chứng trước tự rà soát | `96181b87` (tài liệu), `c7fcd7dd` (log) | T3 + cổng danh tính đạt; bị thay bởi lượt sửa dưới |
| tự rà soát cuối — lỗi thứ ba | `21c172e8` (lớp nhãn R2, đỏ), `ad7172ab` (sửa T7) | §5 mục 3 |
| đóng băng candidate lần 2 | `b5cf4503` | `4629c3e8…` (trung gian) → **`5234c37e…`** tại `ad7172ab`; cache giữ 112 |
| chuyển tiếp bằng chứng trình duyệt | commit trạng thái | `results/FIXTURE_TRANSFER_b5cf4503_r2.json` (§4) |

## 2. Năng lực chóp tứ giác đều

AI đọc đề; engine dựng, kiểm và tính chính xác. Năng lực nằm **trong** họ `convex_polyhedron` của ma trận năng lực
(SUPPORTED) và `polyhedron` của `product_capability.py`. Không thêm hàng ma trận; ma trận là artifact bất biến.

Ba thay đổi theo nguyên nhân gốc:
- **Bộ đọc** `shape_constraint` (RC1):
  - "chóp tứ giác đều S.ABCD" ⇒ `regular_square_pyramid` + `base_square`;
  - đọc "cạnh đáy", "cạnh bên", "trung đoạn" / "đường cao của mặt bên";
  - đọc tâm đáy đề gọi tên (O là tâm đáy, tâm hình vuông ABCD, giao điểm của AC và BD).

  Bộ đọc chỉ gắn số đo khi đề nêu đúng **một** khối. "Đều" đã đọc không còn bị báo là chữ bị nuốt.
- **Khuôn C1 T7** `assumption_gate._khuon_chop_deu` (RC2):
  - đáy vuông, chân đường cao ở tâm đáy;
  - chiều cao lấy trực tiếp, từ SO, từ trung đoạn (h² = m² − s²/4) hoặc từ cạnh bên (h² = l² − s²/2);
  - cạnh bên lấy từ cụm "cạnh bên bằng l" **hoặc** từ độ dài server tự đọc cho đoạn nối đỉnh với một đỉnh đáy
    (`SA = 3`, "cạnh bên SA = 3") — bổ sung của tự rà soát cuối (`ad7172ab`).
  - Từ chối có cấu trúc:
    - hai nguồn chiều cao lệch nhau ⇒ `TEMPLATE_CONTRADICTION T7`;
    - hai cạnh bên khác nhau ⇒ `TEMPLATE_CONTRADICTION T7: lateral edges …`;
    - h² ≤ 0 ⇒ suy biến;
    - h² không là bình phương hữu tỉ ⇒ `TEMPLATE_NOT_REPRESENTABLE T7`, ngoài miền toạ độ hữu tỉ, không làm tròn.
- **Gắn tâm theo danh tính** `construction_binding` (RC3):
  - "X là giao điểm của PQ và RT" và "X là tâm (của) đáy / hình vuông ABCD" là quan hệ dựng;
  - `intersect_line_line` trên đúng hai đường, hoặc trung điểm một đường chéo, ⇒ MATCHED;
  - trung điểm cạnh ⇒ MISMATCHED, từ chối với nguyên nhân CONSTRUCTION.

Ngoài ra:
- **Chiều cao đo được** (RC4): `simulation_state` nhận khoảng cách từ đỉnh ngoài đáy tới mặt phẳng qua các đỉnh đáy làm
  nguồn số của thể tích. Công thức tham chiếu `S(ABCD)` và chiều cao.
- **Nhãn dữ kiện:** GIVEN không ký hiệu ("cạnh đáy bằng 4") mượn nhãn của InputFact. Học sinh đọc "Cạnh đáy = 4" thay
  vì "đại lượng = 4".

Không đổi: lược đồ, prompt, thẻ văn phạm, bảng năng lực (môi trường ngữ nghĩa `b1714b56…`). Không có mã theo tên họ;
dùng lại formation `PYRAMID_LIKE`.

**Corpus W1 — hai lớp, đều ghi trước bản sửa tương ứng** (`tests/geometry/test_regular_square_pyramid.py`, 51 test):

| lớp | tệp | khớp nhãn | ca |
|---|---|---|---|
| 1 (trước sản phẩm) | `diagnostics/corpus/LABELS.json`; oracle `oracle_rsp_w01.py` 17/17 | **17/17** | S1–S7 phục vụ (16 · 48 · 48 · 16/3 · √17 · 16 đổi tên · 16 tâm gọi tên); N1–N7 từ chối (thiếu chiều cao · không đều · mâu thuẫn · tâm sai danh tính · đỉnh lệch tâm · "chứng minh … đều" · chiều cao chỉ ở đầu ra mô hình); U1–U3 ngoài phạm vi (chiều cao vô tỉ · góc · chóp tam giác đều) |
| R2 (tự rà soát cuối) | `diagnostics/corpus/LABELS_R2.json`; oracle `oracle_rsp_w01_r2.py` 7/7 | **7/7** | S8–S10 phục vụ 16/3 (`AB = 4, SA = 3` · "cạnh bên SA = 3" · `SC = 3`); N8/U4 từ chối ở `source_invariant` (PC2); N9 mâu thuẫn hai cạnh bên, chương trình khớp mọi độ dài, từ chối ở `assumption`; L1 chuỗi `SA = SB = SC = SD = 3` — giới hạn của bộ đọc độ dài (`product_limit`) |

Mọi ca `served` qua được cổng phạm vi. Chạy qua `run_pipeline` (đầu dò cache, §6): 12 ca phục vụ = S1–S10 + 2 ca dò.
Nhãn không hạ sau khi thấy kết quả (đính chính có khai ở §7).

## 3. Giao diện — chín mục ROADMAP §0.1

| # | mục | trạng thái | khoá |
|---|---|---|---|
| 1 | ẩn card Kết quả mặc định | card chỉ có khi lời giải mở | `scene3d-steps-panel.test.tsx`; cổng `RESULT_CARD_SHOWN_COLLAPSED` |
| 2 | mọi kết quả qua chọn đại lượng + một ô chi tiết | chip «Đại lượng»: Kết quả → trung gian → dữ kiện; chọn ⇒ ô soi | `quantityChoices`; cổng `quantity_picker` 14/14 |
| 3 | nút «Các bước dựng» (desktop: panel cạnh khung) | lưới `.co-cac-buoc` ≥ 1100 px | `geometryStepList`; ảnh `steps_panel_open/closed` |
| 4 | mobile: panel thu gọn, hình + điều khiển dùng được | panel trong dòng chảy, cuộn bên trong, không phủ khung | test CSS; ảnh mobile |
| 5 | chọn bước đồng bộ hình / timeline / phát lại | chọn ⇒ dừng phát, đặt neo; đóng/mở không reset | cổng `steps_panel` 14/14 (tiến, lùi, nhảy khi đang phát, đóng) |
| 6 | tách bước dựng khỏi bước tính | có từ W12, giữ | `geometry.checks` 14/14 |
| 7 | chọn độ dài tô đoạn, diện tích tô vùng | có từ W12/W18, giữ | chọn từng đại lượng 68/68 |
| 8 | bớt dòng mô tả lặp | gỡ dải «Đang dựng / Dựa trên»; nhãn bước ở panel; "Dựa trên" ở lời giải và ô soi | test cũ viết lại cùng nội dung |
| 9 | tách cuộn bộ đo khỏi cuộn người học | panel cuộn bên trong; mỗi ảnh ghi `scroll` {x, y} | `capture`/`captureElement` |

## 4. Bằng chứng (đo tại `ed37f9fa`; chuyển tiếp sang candidate `5234c37e`)

Cách đo:
- Worktree tách rời sạch, đường dẫn có dấu cách (`D:/tmp/rsp w01`), `npm ci --offline`.
- Candidate `4629c3e8…` và cache 112 được verify ngay trong worktree.
- Fixture sinh tại chỗ (`inputs/`, 37 fixture). Dist do bộ đo tự build.

| cổng | kết quả |
|---|---|
| bộ trình duyệt (`results/BROWSER_EVIDENCE.json`) | **7/7 họ PASS**; desktop 1440×900 + mobile 390×844 |
| — chi tiết | 14/14 ca dương · 54/54 ca từ chối · 6/6 ca phục vụ thêm · chọn từng đại lượng 68/68 · 88/88 bước formation (lời giải, nhãn, nét đứt) · đáp số đúng một lần khi lời giải mở 14/14, vắng khi thu gọn 14/14 · ngăn đại lượng 14/14 · panel bước 14/14 · 0 exception |
| chóp tứ giác đều | V = 16 · bao đóng nhân quả = oracle đăng ký trước = khai báo sự kiện (cả hai khổ) · 4 loại từ chối, mỗi loại mã riêng |
| occlusion (`results/OCCLUSION_MEASUREMENT.json`) | pass, 0 lỗi · `HUMAN_REVIEW_PENDING` cho bốn cảnh W14 như trước · chóp đều: product = oracle ở bốn trạng thái |
| playback (`results/PLAYBACK_EVIDENCE.json`) | 14/14, có `--lap-orbit 5` |
| ảnh | sheet + filmstrip mỗi họ (`images/<họ>/`), `images/overview/INDEX.png` · 68 crop cạnh khuất, 0 bất đồng oracle, 0 owner trùng |
| **chuyển tiếp sang `5234c37e`** (`results/FIXTURE_TRANSFER_b5cf4503_r2.json`) | **TRANSFERS** — 37 fixture tái sinh trong worktree sạch tại `b5cf4503`: 37/37 envelope trùng byte, chỉ khác hai trường danh tính; manifest fixture đã đo tái lập trùng byte; `frontend/src` không đổi từ `ed37f9fa` (`frontend/scripts` chỉ đổi danh tính ở manifest bộ đo) |
| **T3 tại commit tài liệu cuối `7b99ccaa`**, đường dẫn có dấu cách, log ngoài worktree | **`FULL_PRODUCT_GATE_PASS`** — pytest 7131/0 (1 skipped, 2 deselected) · vitest 1071/1071 · build · demo 5/5 · bề mặt sập 6/6 · git status 0 trước/sau |
| **cổng danh tính tại `7b99ccaa`** (`diagnostics/w01_gates.sh`) | candidate `5234c37e` + cache 112 verify · schema ×2 trùng byte · `LLM_ONLY` · 0 file bề mặt mô hình đổi · ngoài run chỉ hai registry sống đổi, 0/180 báo cáo lịch sử đổi · `git diff --check` 0 · audit tài liệu PASS · node harness 76/0 (2 skip môi trường) |
| T3 tại `96181b87` (trước tự rà soát) | `FULL_PRODUCT_GATE_PASS` — pytest 7118/0 · vitest 1071/1071 · build · demo 5/5 · bề mặt sập 6/6 (lần 1 đỏ một test vì log của chính nó nằm trong worktree) |
| cổng danh tính tại `96181b87` | candidate + cache verify · schema ×2 trùng byte · `LLM_ONLY` · 0 file bề mặt mô hình đổi · 0/180 báo cáo lịch sử đổi · audit tài liệu PASS · node harness 76/0 (2 skip môi trường) |

Ba lần đo, giữ cả hai lần hỏng ([`diagnostics/MEASUREMENT_ATTEMPTS.json`](diagnostics/MEASUREMENT_ATTEMPTS.json)):
1. `3ad9442f` — dừng ở kiểm manifest. Hash nguồn oracle lấy trước khi thêm hai test vào file ấy.
2. `1310658b` — mọi ca âm và ca phục vụ đạt. Mọi ca dương đỏ ở tham chiếu cấu trúc (b), vì bộ đo còn tìm dòng Kết quả
   trong lời giải thu gọn. Riêng thiết diện còn đỏ ở CSS và màu vai trò, vì dòng duy nhất của nó là kết quả. Đây là lỗi
   **bộ đo**, không phải lỗi sản phẩm.
3. `ed37f9fa` — đạt hết.

Vì sao chuyển tiếp thay vì đo lại sau bản sửa `ad7172ab`:
- Bản sửa chỉ đổi `assumption_gate` (backend).
- Mọi envelope mà renderer đọc trùng byte, và frontend không đổi. Ảnh chụp lại sẽ cùng đầu vào, cùng mã vẽ.
- Cùng cách của run `cuboid-merge` (người dùng đã chấp nhận).
- Lần chạy đầu của script chuyển tiếp so hash manifest ở dạng LF, trong khi bộ đo băm byte thô (CRLF trên Windows), nên
  báo sai `DOES_NOT_TRANSFER`. Bản ghi giữ ở `results/FIXTURE_TRANSFER_b5cf4503.json` (SUPERSEDED).

**Tiêm lỗi cho cổng mới** (node, `compiler-scene-replay-lib.node-test.mjs`, 78/78) — mỗi lỗi làm đúng mã của nó đỏ:
- `assessQuantityPicker`: 6 mã;
- `assessStepsPanel`: 7 mã;
- `evaluateEvidenceGates`: 4 mã;
- tham chiếu cấu trúc có/không có ngăn;
- playback thu gọn.

Không chạy tiêm lỗi sản phẩm ở mức trình duyệt (mỗi lượt bộ đo ~50 phút). Lần đo 2 cho thấy cổng mới nối đúng: nó đỏ
khi card bị đọc sai chỗ.

## 5. Ba lỗi thật

Hai lỗi đầu do đầu dò cache qua `run_pipeline` bắt được; test của route (`verify_and_compile`) bỏ sót cả hai. Lỗi thứ
ba do tự rà soát cuối bắt được.

1. **Công thức thể tích biến mất.**
   - Triệu chứng: chóp đáy chữ nhật mà chương trình vừa khai `SA_length` vừa đo d(S, (ABC)) mất công thức
     `V = 1/3 × S(ABCD) × SA = 24`, vốn được phục vụ trước W1. Luật chiều cao W1 tạo ứng viên thứ hai.
   - Sửa `98e2b8f7`: khi có chiều cao đo, một cạnh chỉ là chiều cao của công thức nếu **bằng** nó. Nếu không, chiều cao
     là khoảng cách đo. Cạnh bên xiên của chóp đều (kể cả khi mô hình đặt tên `SA_length`) không vào công thức.
   - Test RED → GREEN.
2. **Cổng phạm vi từ chối câu hỏi độ dài.**
   - Triệu chứng: "Tính độ dài cạnh bên SA" (S5, `MUST_SERVE`) bị từ chối ở `scope` trước analyze, vì bảng manh mối
     không có "độ dài".
   - Sửa `9d66c603`: thêm manh mối "độ dài" cho nghĩa vụ `distance`. Test mới: mọi ca `served` của corpus qua được
     cổng phạm vi.
   - Lỗi này cũng đóng `ISSUE-ARCH-SCOPE-GATE-LENGTH-CLUE` (W18). Đầu dò chấp nhận cho kết quả B18 phục vụ, B19 từ
     chối ở `construction_binding` (`diagnostics/SCOPE_LENGTH_CLUE_PROBE_1310658b.json`).
3. **Khuôn T7 bỏ qua cạnh bên gọi bằng tên đoạn** (tự rà soát cuối, mức Important).
   - Triệu chứng: "Cho hình chóp tứ giác đều S.ABCD có AB = 4, SA = 3" (cách viết sách giáo khoa phổ biến nhất) và
     "cạnh đáy bằng 4, cạnh bên SA = 3" bị từ chối với `ASSUMPTION_INVARIANCE_UNPROVEN`. Chính chứng chỉ ghi
     `CE_INVALID breaks |AS| = 3`: server đã đọc |SA| = 3 từ đề nhưng T7 chỉ lấy cạnh bên từ cụm "cạnh bên bằng …".
   - Không bao giờ ra đáp số sai (đóng an toàn), nhưng từ chối đề hợp lệ của chính họ vừa thêm.
   - Sửa `ad7172ab`: cạnh bên còn lấy từ bất biến độ dài của đoạn nối đỉnh với một đỉnh đáy — cùng hạng bằng chứng
     nguồn với cạnh đáy `AB`. Hai cạnh bên khác nhau là mâu thuẫn của đề.
   - Lớp nhãn R2 ghi và commit đỏ trước bản sửa (`21c172e8`); RED → GREEN 51/51; geometry + semantic_program chỉ
     còn lớp candidate cũ / cây bẩn.

## 6. Cache và candidate

**`CACHE_VERSION` 111 → 112** (`de5b2331`).
- Bằng chứng:
  - hai yêu cầu được phục vụ trước W1, lưu thành row v111 trong sqlite tạm, vẫn HIT dù W1 dựng envelope khác: nhãn
    "Cạnh = 4", và cạnh nguồn số của thể tích;
  - sau khi tăng phiên bản, cả hai MISS (`diagnostics/PROOF_CACHE_ROW_W01.json`, 0 lượt gọi).
- Khoá danh tính tạo lại bằng `lock_cache_identity.py`; môi trường ngữ nghĩa `b1714b56…` không đổi.
- Chiều refused → served của cổng phạm vi không tạo row cũ (lời từ chối không được cache).

**Bản sửa `ad7172ab`: `CACHE_VERSION` giữ 112** (`diagnostics/PROOF_CACHE_ROW_W01_R2.json`, trước = `de5b2331`, sau =
`ad7172ab`, 26 hàng):
- 9/9 envelope được phục vụ dưới 112 trùng byte sau bản sửa.
- Ba ca mới phục vụ (S8–S10) bị từ chối dưới 112, nên không có row cache cũ.

**Candidate** `b2d4187a…` → `4629c3e8…` (trung gian) → **`5234c37e…`**:
- Đóng băng **hai lần**, mỗi lần trong worktree tách rời sạch:
  - lần 1 tại `de5b2331` (`5aaf11ee`);
  - lần 2 tại `ad7172ab` sau bản sửa của tự rà soát (`b5cf4503`).
- Khai ở `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` (có candidate trung gian) và `CANDIDATE_DIVERGENCE.json` sống.
- Một lần chạy nhầm `freeze_evaluation_candidate.py --help` (script không có cờ help) đã ghi vào cây chính bẩn. File ấy
  được khôi phục bằng `git checkout` trước mọi commit; đó không phải một lần đóng băng.
- Lượt backend đầy đủ trước mỗi lần đóng băng: 13 lỗi (`de5b2331`) và 11 lỗi (`ad7172ab`), đều thuộc lớp candidate cũ
  hoặc cây bẩn (`diagnostics/logs/PRE_FREEZE_FULL_BACKEND_*.log`).

## 7. Đính chính đăng ký trước

`diagnostics/PREREGISTRATION_CORRECTIONS.json`:

- **PC1** — ghi trước mọi lần chạy trình duyệt.
  - Đăng ký ban đầu: ca âm topo/kernel của chóp đều chép kỳ vọng của sáu họ cũ (`semantic_analyze` /
    `NON_POSITIVE_LENGTH`).
  - Nguyên nhân: sáu họ cũ sinh fixture bằng compiler (`DETERMINISTIC_FIRST`). Chóp đều đi tuyến mặc định `LLM_ONLY`,
    nơi kernel từ chối đáy suy biến ở `execution` với nguyên nhân UNKNOWN.
  - Đăng ký đã sửa theo hành vi thật của route; `LABELS.json` không đổi.
  - Giới hạn này mở thành issue `ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE`.
- **PC2** — ghi sau lượt đỏ, trước bản sửa.
  - R2 N8 và U4 được dự đoán từ chối ở `assumption`. Thực tế chúng bị từ chối ở `source_invariant`, chặng chạy trước
    chứng chỉ trên route: chương trình đã đăng ký đặt đỉnh trên tâm và phạm một độ dài đề nêu.
  - Kết cục (từ chối) không đổi; nhãn đầu giữ trong `expect_first_registration`.
  - Thêm N9: cùng đề N8, chương trình khớp mọi độ dài, để chỉ chứng chỉ có thể từ chối.

## 8. Giới hạn còn mở (không che)

- **Chưa phục vụ:**
  - chiều cao vô tỉ (U1, R2 U4 — ngoài miền toạ độ hữu tỉ);
  - dữ kiện góc (U2);
  - chóp tam giác / lục giác đều (U3).
- **Chuỗi bằng nhau** `SA = SB = SC = SD = 3`: bộ đọc độ dài chỉ gắn số cho đoạn liền trước (SD), nên grounding từ chối
  với `SOURCE_EVIDENCE_CONFLICT` dù đề xác định đáp số (R2 L1, `ISSUE-ARCH-SOURCE-LENGTH-CHAINED-EQUALITY`; bộ đọc không
  đổi ở W1).
- **Nguồn số thừa:** chương trình vừa cho SA vừa đo d(S, (ABC)) mang thêm một cạnh nguồn số `h` của V. Công thức vẫn
  `× SA`; chuỗi nhân quả có thêm `h`.
- **Lời từ chối độ dài ≤ 0** trên tuyến mặc định nói nguyên nhân UNKNOWN (`ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-LENGTH-CAUSE`).
- **Từ vựng gắn phép dựng:** tâm và giao điểm hai đường đã gắn. Trọng tâm, trực tâm, điểm đối xứng, giao với mặt phẳng
  vẫn `OUT_OF_SCOPE` (`ISSUE-ARCH-CONSTRUCTION-BINDING-VOCABULARY`, PARTIAL).
- **Compiler** không có họ chóp đều (không nằm trên tuyến mặc định; DEFERRED).
- **Hai việc nhỏ hoãn** (tự rà soát cuối):
  - `_nhan_du_kien_tu_fact` mượn nguyên nhãn InputFact (viết hoa chữ đầu). Một nhãn mô hình có dấu gạch dưới sẽ lên bề
    mặt học sinh; cổng token thô của trình duyệt chỉ phủ các fixture đã đo.
  - Nút «Các bước dựng» có `aria-controls` trỏ tới panel chỉ tồn tại khi mở.

## 9. Skill và rà soát

Gọi qua Skill tool cho W1: `superpowers:test-driven-development`.

Áp dụng theo hướng dẫn đã nạp trong cùng phiên, không gọi lại:
- `superpowers:writing-plans` (PLAN.md);
- `superpowers:executing-plans` (ledger, ruling, rà soát cuối);
- `superpowers:systematic-debugging` (RC1–RC4, ba lỗi, ba lần đo, lần chuyển tiếp hỏng);
- `superpowers:verification-before-completion`;
- `andrej-karpathy-skills:karpathy-guidelines`;
- `ponytail:ponytail-review` (`diagnostics/PONYTAIL_REVIEW.json`, không cắt gì).

Rà soát cuối của cả nhánh là **tự rà soát** theo danh mục `requesting-code-review/code-reviewer.md`, vì brief cấm
subagent. Nó yếu hơn một người rà soát mới, và người dùng quyết có đủ trước khi merge hay không.
- Kết quả: một mục Important đã sửa (§5 mục 3) và hai việc nhỏ hoãn (§8).

Không tạo subagent.
