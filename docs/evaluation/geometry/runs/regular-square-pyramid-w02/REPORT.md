# REPORT — regular-square-pyramid-w02

Việc `regular-square-pyramid`, wave W2. Brief: `REGULAR_SQUARE_PYRAMID_PEDAGOGICAL_CLOSURE`.
Thực thi: `CLOUD_IMPLEMENTATION_THEN_LOCAL_ACCEPTANCE` — triển khai trong phiên cloud; máy local nghiệm thu.
Kế hoạch và bảng tái hiện: [`PLAN.md`](PLAN.md). Bàn giao: [`HANDOFF.md`](HANDOFF.md).

Ràng buộc của cả wave:
- `DEFAULT_MODE = LLM_ONLY`, **0 lượt gọi Gemini** (mọi lượt đo chặn mạng / thay chặng LLM bằng hợp đồng đóng băng).
- Không PR, không merge, không push `main`; không sửa artifact W1; stage theo danh sách.
- `frontend/public/favicon.svg` không đụng tới.

Kết luận: **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`** — A–F đã làm và đo trên cloud; mọi cổng ngoài lớp môi trường xanh; T3 và hai cổng trình duyệt đỏ cả ở W1 head trên cloud phải chạy lại ở máy local (`HANDOFF.md` §2). Review người **`NOT_APPROVED`**.

## 0. Tiếp nhận

- `SOURCE_W1_HEAD = e821b9b5330480b791284548c3e49d683955682e` = `origin/feat/regular-square-pyramid` (fetch đầu phiên).
- `main` = `38d4158826cbbffd013d971a9484b9f0fd2a6130` (`origin/main`, không đổi).
- Phiên cloud khởi tạo sẵn trên nhánh `feat/regular-square-pyramid` tại W1 head: không cần fast-forward, không tạo
  nhánh phụ, không đổi ref `main`. Clone ban đầu nông (50 commit) — đã `git fetch --unshallow` để các test đọc lịch sử.

## 1. Đã làm gì

| phần | commit | tóm tắt |
|---|---|---|
| kế hoạch + test đỏ A | `200e30b3` | PLAN; nhãn đoạn trên fixture W1 thật |
| A — nhãn chờ đoạn được dựng | `2a63da7d` | §2 |
| C/E — test đỏ | `687520ce` | SO; lăng trụ cạnh trên tình cờ bằng chiều cao |
| C/E — sản phẩm | `9f454d6b` | §3, §4 |
| B — bảng nổi | `71cf0e80` | §5 |
| D/F — hình phụ, lưới | `6ca3b35e` | §6, §7 |
| F — độ dài ≤ 0 do đề; nhãn token máy | `c86cf53c` | §8 |
| cache 112 → 113 | `e68fa199` | §9 |
| bộ đo W2 + oracle nhãn | `caa9a141` | §10 |
| tự rà soát | `7a88a789` (chú thích bước hình phụ), `c5142f07` (ponytail) | §11 |
| đóng băng 1 | `d72dd350` | candidate `5234c37e` → `d3de9c44` (tại `c5142f07`) |
| bản sửa sau lần đo 1 | `527d642e` | tên nút đóng; đính chính đăng ký PC1-W2 |
| đóng băng 2 | `bac5d80f` | cùng tree hash `d3de9c44`, product commit `527d642e` |
| bản sửa sau lần đo 3 | `75a0af9a` | ngăn và ô soi xếp trên bảng nổi (`z-index`) |
| bộ đo: bước chỉ dựng hình phụ đang ẩn | `445f31a7`, `a4abb188` | oracle độc lập miễn đúng bước ấy (khung tĩnh, tham chiếu, phát) |
| đóng băng 3 | `4a6af4e9` | cùng tree hash `d3de9c44`, product commit `75a0af9a` |
| lượt đo có thẩm quyền (lần 5) | `94200b50` → bằng chứng `c5b39092` | §10 |

## 2. A — nhãn số đo chỉ khi đối tượng mang nó đã được dựng

Tái hiện (test đỏ `200e30b3`, fixture W1 thật, không dựng tay):
- chóp tam giác: `AB = 3`, `AC = 4`, `SA = 5` có nhãn ở bước 0, trước khi dựng đáy và đoạn SA;
- lăng trụ tam giác: `AD = 5` có nhãn trước bước dựng các cạnh bên.

Nguyên nhân gốc: `annotationsAt` chỉ đòi hai ĐIỂM đầu mút có mặt.

Sửa (`scene3d-annotations.ts`): nhãn `anchor: "segment"` cần một đoạn đang có mặt ở bước, đọc theo DANH TÍNH —
`endpoint_ids` của đoạn, cạnh vòng `vertex_ids` của đa giác, `edge_ownership` của khối. Áp dụng ở mọi chế độ:
"Hiện tất cả" và khi đang chọn đại lượng ấy. Không đọc tên họ, tên fixture, lời kể hay chỉ số bước.
- Đối chứng: nhãn diện tích, thể tích (chủ thể là vật) giữ luật cũ; cảnh không lỗi không đổi.
- Dữ kiện vẫn đọc được ở ngăn «Đại lượng» và «Xem đề».
- Nhãn HỢP LỆ nhưng thiếu chỗ được đánh dấu riêng (`data-thieu-cho`, móc `__geo3d_annotation_unplaced`) — khác nhãn
  chưa hợp lệ (không có trong lớp nhãn). Đầu dò W2 kiểm nhãn thiếu chỗ vẫn có trong ngăn.
- Oracle ĐỘC LẬP của bộ đo (`expectedAnnotationIds` + `builtSegmentPairs`) cài lại luật này, không nhập mã sản phẩm.

Hệ quả có khai: đáp số là độ dài của một đoạn KHÔNG được dựng (`w18_projection_line`: "Tính độ dài đoạn SH") không
còn nhãn trên hình; vẫn chọn được qua ngăn, ô soi mở trên nó (đính chính đăng ký PC1-W2, §12; câu hỏi H-W2-2).

## 3. C — đường cao SO của chóp đều

Formation planner dùng chung (`formation._chan_ung_vien`) có nguồn chân đường cao thứ ba, `_tam_day_deu`:
- ràng buộc có kiểu `regular_square_pyramid` của `shape_constraint`, đọc từ PHẦN TIỀN ĐỀ (mục tiêu "chứng minh … đều"
  bị che), cùng đỉnh và cùng tập đỉnh đáy;
- và một điểm chương trình dựng làm tâm đáy: `intersect_line_line` trên hai `construct_line` qua hai cặp đỉnh đối,
  hoặc trung điểm một đường chéo.

Bước bổ sung dựng `construct_segment` "Chiều cao SO", vai `CONSTRUCT_HEIGHT`, ngay trước các cạnh bên. Danh tính,
vai trò và xuất xứ là thật (`producer: construct_segment`, `depends: [O, S]`); tên chân là tên điểm đã dựng (`O`, hay
tên khác nếu chương trình đặt khác). Không toạ độ giả, không bypass binding: đỉnh có thật ở trên tâm không là việc của
chứng chỉ T7 và chặng `construction_binding` — sai thì bài bị từ chối. Đề không nói "đều" (N2) hay tâm sai danh tính
(N4) ⇒ không có đoạn SO (test thẳng trên bước bổ sung).

Nhãn của `d(S, (ABC))`: nhân chứng có chân trùng một điểm cảnh và đoạn tới điểm ấy đã được dựng ⇒ nhãn bám đoạn
(`quantity_annotations._bam_doan_da_dung`), không vẽ thêm nét đứt chồng lên SO. Công thức của đại lượng nói cả hai tên:
`SO = d(S, (ABC)) = 3`.

## 4. E — chiều cao của công thức theo quan hệ, không theo giá trị

Tái hiện (test đỏ `687520ce`): lăng trụ đứng, đáy vuông tại A, AB = 3, AC = 4, chiều cao 4; chương trình khai
`DF_length := AC_length` (cạnh đáy TRÊN, = 4) và đo d(D, (ABC)) = 4. Luật W1 (`98e2b8f7`, chọn cạnh BẰNG khoảng cách đo)
in **`V = S(ABC) × DF = 24`** — sai vai trò.

Sửa: `quantity_annotations.chieu_cao_the_tich` (module được phép dùng kernel; `simulation_state` bị khoá không tính
hình — `test_lop_nay_KHONG_TINH_hinh_hoc`) chọn chiều cao bằng quan hệ hình học kiểm CHÍNH XÁC:
- nguồn số có đoạn (đoạn gắn nhãn, hoặc đoạn tên nó gọi giữa hai đỉnh khối) cùng phương pháp tuyến đáy, một đầu trên
  mặt đáy và đầu kia ngoài; độ dài khớp giá trị chỉ là kiểm NHẤT QUÁN;
- hoặc khoảng cách tới một mặt phẳng trùng mặt đáy.

Nhiều chiều cao thật ⇒ ưu tiên dữ kiện đề cho; còn hơn một ⇒ không in. `scene3d._attach_formulas` dùng lựa chọn ấy và
ký hiệu đoạn đã dựng ("× SO"). Hệ số 1/3 giữ nguyên.

Kết quả: chóp đều `V = 1/3 × S(ABCD) × SO = 16`; lăng trụ trùng giá trị `V = S(ABC) × AD = 24` (khoảng cách đo có chân
A, bám cạnh bên AD đã dựng — đúng chiều cao của lăng trụ đứng; đính chính kỳ vọng PC2-W2); sáu họ cũ giữ nguyên công
thức (test hồi quy) và envelope phục vụ trùng byte (§9). Khoá "hai ứng viên ⇒ không công thức" cũ được viết lại: SA ⊥
đáy nay được chọn bằng quan hệ; ca không có chiều cao kiểm được vẫn không có công thức.

## 5. B — bảng nổi «Các bước dựng»

Thay cột lưới W1 (mở bảng làm canvas co lại) bằng `BangNoi` (`scene3d-floating-panel.tsx`):
- desktop: nổi phía phải vùng mô phỏng; kéo bằng tiêu đề (con trỏ không tới canvas ⇒ không orbit); phím mũi tên dời,
  Shift dời xa; Escape đóng và trả tiêu điểm cho nút; nút về vị trí mặc định, thu gọn, đóng;
- luôn kẹp trong khung canvas khi kéo và khi đổi cỡ cửa sổ (`kepBang`), nên nút đóng luôn thấy được;
- vị trí sống ở trình phát: đóng rồi mở lại giữ chỗ đã kéo; đóng/mở không đổi bước, lựa chọn, nội dung;
- khổ hẹp (≤ 48rem): trong dòng chảy dưới điều khiển, thu gọn được, không kéo, không phủ khung hay nút;
- nút «Các bước dựng» ở cuối thanh điều khiển; `aria-controls` chỉ khi bảng có mặt; nút đóng của bảng mang tên riêng
  "Đóng các bước dựng" (không trùng nút "Đóng" của ngăn).

Chọn bước vẫn dừng phát và đặt neo (luật W1). Ô soi giữ cột riêng của nó (quyết định cũ) — để người dùng quyết
(`ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS`, H-W2-3).

## 6. D — hình phụ

`scene3d-auxiliary.ts` (thuần, không three, không toạ độ):
- hình phụ = đường/mặt phẳng backend gắn đúng một vai `CONSTRUCT_AUXILIARY_GEOMETRY`, không `given`/`target`;
- loại DỰNG (có vật hình học dựng từ nó — AC, BD → O): hiện tới bước mọi vật ấy đã có, rồi ẩn khỏi cảnh trung tính;
- loại ĐO (mặt phẳng chỉ làm toán hạng đại lượng — mặt phẳng qua A, B, C): ẩn mặc định;
- đường đề gọi tên chỉ để đo (BD của "khoảng cách từ S tới BD") và mặt cắt (α) không ẩn;
- chip «Hình phụ» hiện tất cả; chọn hình phụ, hay một vật dựa trên nó, cũng hiện nó;
- dữ liệu, xuất xứ, line3 và timeline không đổi; bước chỉ dựng hình phụ đang ẩn ghi "hình phụ, đang ẩn" ở danh sách.

Danh sách bước nhóm "Giao điểm của AC và BD" với ba bước con (AC, BD, O) bằng `<details>` gốc; mỗi bước con vẫn là
một nút đặt đúng neo, giữ thứ tự và delta hình học.

## 7. F — lưới nền tuỳ chọn

Chip «Lưới», mặc định TẮT: `GridHelper` mảnh, nhạt, nằm dưới đáy hình, ô theo cỡ cảnh, không số, không đơn vị; ngoài
nhóm gốc ⇒ không occlusion, không raycast, không vào khung nhìn. Bật/tắt không đổi camera, bước, lựa chọn, tập vật
dựng; không tính lại occlusion khi nghỉ (đo `recompute_count`).

## 8. Việc nhỏ

- **Độ dài ≤ 0 do chính đề ghi** (`c86cf53c`): thực thi hỏng trên tuyến mặc định mà tiền đề ghi một độ dài ≤ 0 bộ đọc
  server đọc được (đoạn có tên, hay cạnh đáy / chiều cao / cạnh bên / trung đoạn / cạnh lập phương của khối duy nhất)
  ⇒ `NON_POSITIVE_LENGTH`, nguyên nhân SOURCE, chủ thể theo cách học sinh gọi ("cạnh đáy"). Không thì giữ UNKNOWN —
  đề hợp lệ mà chương trình suy biến không bị gọi là đề sai (test đối chứng). `ISSUE-ARCH-DEFAULT-ROUTE-NON-POSITIVE-
  LENGTH-CAUSE` → PARTIAL (sáu họ cũ chưa có hàng gắn nhãn trên tuyến mặc định).
- **Nhãn InputFact kiểu token máy** (gạch dưới, camelCase) không còn được mượn lên bề mặt học sinh (Minor W1).
- **`aria-controls`** của «Các bước dựng» chỉ khi bảng có mặt (Minor W1).

## 9. Cache và candidate

**`CACHE_VERSION` 112 → 113** (`e68fa199`), chứng minh theo hàng (`diagnostics/PROOF_CACHE_ROW_W02.json`, sqlite tạm,
0 lượt gọi): 34 hàng qua `run_pipeline` với W1 head (`e821b9b5`) và với W2 —
- 13 envelope phục vụ dưới 112 vẫn HIT dù W2 dựng khác (chóp đều có SO và "× SO"; chóp chữ nhật hai chiều cao gắn
  `d(S, (ABC))` lên SA; lăng trụ trùng giá trị không còn "× DF"); bump giả lập làm cả 13 MISS;
- sáu họ cũ (chương trình compiler) trùng byte. Môi trường ngữ nghĩa `b1714b56` không đổi; khoá danh tính tạo lại.

**Candidate** `5234c37e…` → **`d3de9c44…`** (110 file). Đóng băng BA lần, mỗi lần trong worktree tách rời sạch
(`core.autocrlf=true`) trong scratchpad: `c5142f07`, `527d642e`, rồi `75a0af9a` (cùng tree hash — `frontend/src` đổi
nên `product_commit_sha` đổi). Parser của script đóng băng được đọc trước: mọi đối số khác `--verify` đều đóng băng, nên chỉ
chạy dạng trơn và `--verify`. Khai ở `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` và `CANDIDATE_DIVERGENCE.json` sống.

## 10. Bằng chứng

Lượt đo có thẩm quyền: **lần 5 tại `94200b50`** — worktree tách rời sạch (`core.autocrlf=true`), đường dẫn có dấu
cách, `diagnostics/w02_measure.sh`, dist dựng trong worktree, Chromium 141 headless + SwiftShader, **0 lượt gọi mô hình**.
Bằng chứng commit `c5b39092`. Bốn lần trước và lý do bị thay: `diagnostics/MEASUREMENT_ATTEMPTS.json`, `diagnostics/logs/`.

| cổng | kết quả | file |
|---|---|---|
| fixture W2 (7 họ; chặng LLM thay bằng hợp đồng đóng băng) | dựng lại tại candidate `d3de9c44` / product `75a0af9a` | `inputs/FIXTURE_MANIFEST.json` |
| đầu dò W2 (`w02-closure-probe.mjs`) | **14/14** (7 họ × desktop 1440×900 + mobile 390×844) | `results/W02_CLOSURE_PROBE.json` |
| bộ đo chính — từ chối | **54/54** | `results/BROWSER_EVIDENCE.json` |
| — phục vụ (W18) | **6/6** (PC1-W2: nhãn `d_kq` vắng, chọn được qua ngăn) | 〃 |
| — chọn từng đại lượng · ngăn «Đại lượng» | **68/68** · **14/14** | 〃 |
| — lượt dương (14) | mọi cổng khác xanh ở mọi lượt có cổng ấy; đỏ chỉ ở `camera_settled_rotated_neutral` (6 desktop) và `causal_restore` thiết diện (desktop + mobile) ⇒ 7/14 lượt xanh trọn | 〃 |
| occlusion | pass, 0 lỗi (`HUMAN_REVIEW_PENDING` của camera W14, như W1) | `results/OCCLUSION_MEASUREMENT.json` |
| phát lại | **14/14** (PASS `afc55159f3ff`) | `results/PLAYBACK_EVIDENCE.json` |
| ảnh | 68 crop cạnh khuất, mọi đầu mút trong crop, 0 bất đồng oracle, 0 cạnh hai chủ | `results/HIDDEN_EDGE_CROPS.json`, `images/` |

Đầu dò W2 kiểm, trên mỗi họ và khổ: bảng mở/đóng không đổi hộp canvas và ma trận camera; kéo tiêu đề bằng sự kiện
chuột thật (CDP) không orbit; phím mũi tên, đổi cỡ cửa sổ, về mặc định, Escape, mở lại giữ chỗ; chọn bước đặt neo và
dừng phát; mobile: bảng trong dòng chảy, thu gọn, không phủ điều khiển; "Hiện tất cả" ở từng bước khớp oracle độc lập
(`builtSegmentPairs`); nhãn thiếu chỗ vẫn có trong ngăn; đoạn chiều cao; hình phụ ẩn/hiện; lưới bật/tắt không đổi
camera, bước, lựa chọn, tập vật dựng, `recompute_count`.

**Lớp môi trường** (`diagnostics/ENV_CAMERA_SETTLE_BASELINE.json`, chạy lại ở W1 head `e821b9b5` + fixture W1):
- `camera_settled_rotated_neutral`: đỏ ở W1 head trên cloud (cửa sổ lắng không đạt dưới nhịp khung SwiftShader); W1
  qua cổng này ở máy Windows của người dùng (`ed37f9fa`).
- `causal_restore` thiết diện: mobile đỏ 3/3 ở cả hai phía với cùng mẫu pixel (15 / 326 / 15); desktop không tất định
  ở cả hai phía (W2 2/3, W1 1/3). Pixel khác nằm trên cùng một đường từ B, cùng hình học, chỉ nhạt hơn ở phần khử răng
  cưa — không vật nào hiện hay ẩn. Phân loại `ENVIRONMENT_SUSPECTED`, CHƯA chứng minh: n = 3 không tách được tỉ lệ.

Hai cổng này là `LOCAL_VERIFICATION_REQUIRED`; nếu máy local vẫn đỏ thì là lỗi thật của W2.

**Cổng repo.** Trong phiên: vitest, `tsc -b` + `vite build`, test node của bộ đo, pytest các test W2 và test khoá
literal, kiểm tài liệu — xanh trừ lớp môi trường đã biết (dưới). T3 (`frontend/scripts/full-gate.mjs`) và
`diagnostics/w02_gates.sh` chạy ở worktree tách rời sạch tại commit tài liệu; log và số liệu ở §10.1 (thêm cùng log).
Lớp lỗi MÔI TRƯỜNG của pytest trên cloud, có trước W2 (cùng tập ở W1 head trong worktree CRLF): thiếu ref `main` cục
bộ (`test_branch_independent_harness` ×9, `test_precheck_kho`, `test_tien_kiem_kho`, `test_12_final_decision…`) và
Python Linux ghi LF vào cây CRLF (`test_exporter_idempotence`, `test_holdout_readiness_7b`). Test node "repo root keeps
a Windows path with spaces" chỉ đúng trên Windows.

## 11. Tự rà soát

- Chú thích "hình phụ, đang ẩn" đọc `focus_ids` của NEO (có thể là sự kiện kết luận) — sửa đọc sự kiện dựng của bước
  (`7a88a789`, đỏ → xanh).
- `ponytail:ponytail-review` (gọi qua Skill tool): cắt `hasAuxiliary` (một nơi gọi) và một lớp CSS rỗng nghĩa; giữ
  `_doan_cua_ten` (ngữ nghĩa khác `_length_joins_vertices`) — `diagnostics/PONYTAIL_REVIEW.json`.
- Lần đo 1 tìm ra nút đóng của bảng trùng tên "Đóng" (lỗi a11y thật, sửa `527d642e`).

## 12. Đính chính đăng ký trước

`diagnostics/PREREGISTRATION_CORRECTIONS.json`:
- **PC1-W2** (sau lần đo 1, trước lần đo 3): `w18_projection_line` kỳ vọng nhãn đáp số `d_kq`. Theo luật A, SH không
  được dựng nên không có nhãn — kỳ vọng W18 chưa được cập nhật khi đăng ký A. Thay bằng khẳng định chặt tương đương:
  nhãn VẮNG trên hình VÀ đáp số chọn được qua ngăn (ô soi mở trên nó).
- **PC2-W2** (trước mọi lần đo trình duyệt): test lăng trụ trùng giá trị kỳ vọng `× d(D, (ABC))`; sản phẩm in `× AD`
  vì khoảng cách bám cạnh bên AD đã dựng — đúng chiều cao. Thuộc tính khoá (DF không là chiều cao) không đổi.

## 13. Giới hạn còn mở

- Đáp số là độ dài của một đoạn không được dựng: không có nhãn trên hình (H-W2-2).
- Ô soi vẫn là cột ở ≥ 1100 px (`ISSUE-ARCH-INSPECTOR-COLUMN-RESIZES-CANVAS`, H-W2-3).
- Độ dài ≤ 0: sáu họ cũ chưa có hàng gắn nhãn trên tuyến mặc định (PARTIAL).
- Nhóm bước con lấy tiêu đề là nhãn của bước chính ("Giao điểm của AC và BD"), không phải "Dựng tâm đáy": hệ không
  suy vai "tâm" ở phía trình bày.
- Từ W1, không đổi: chiều cao vô tỉ, góc, chóp tam giác/lục giác đều; chuỗi `SA = SB = SC = SD = 3`.
- Môi trường cloud (§10): T3 không tái lập được trọn vẹn trên Linux — phải chạy lại ở máy local.

## 14. Skill

Gọi qua Skill tool trong phiên: `ponytail:ponytail-review`. Đọc và áp dụng theo nội dung đã nạp sẵn ở phiên (không gọi
lại qua Skill tool): `superpowers:using-superpowers` (nạp bởi hook khởi động). Áp dụng như quy trình, không nạp nội
dung skill: TDD (test đỏ commit trước bản sửa: `200e30b3`, `687520ce`, các test đỏ→xanh có ghi), gỡ lỗi có hệ thống
(nguyên nhân gốc của lần đo 1, 2), kiểm chứng trước khi tuyên bố. `writing-plans`, `executing-plans`,
`systematic-debugging`, `verification-before-completion`, `karpathy-guidelines`, `test-driven-development` CÓ trong danh
sách skill của phiên nhưng KHÔNG được gọi qua Skill tool — không ghi là đã dùng. Impeccable có cài; hook thiết kế của
nó tự quét file `.tsx` mới ("no deterministic design-quality issues") — skill không được gọi. Không subagent.
