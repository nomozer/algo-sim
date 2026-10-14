# Kiểm toán dựng hình Scene3D — ba cảnh two-line (LOCAL, 2026-10-14)

**Kết luận: `READY_FOR_HUMAN_VISUAL_REVIEW`.** 0 sai toán học, 0 sai phép biến đổi/chiếu của renderer trên ba cảnh;
một lỗi loại D (nhãn đỉnh bị giấu oan) đã sửa ở `eea6f3df`; một hạn chế loại E (thứ tự dựng) ghi OPEN theo quyết định
người dùng. T3 sạch PASS tại `b8e96a86`. Không gọi Gemini, không bật Hybrid, không merge/push; chưa có `APPROVED_BY_USER`.
Nhánh `research/goal-directed-two-line-plane-section`; main = origin/main `5270f3dd` không đổi.

## 1. Phạm vi và cách đo

Ba cảnh phục vụ (`two-line-pyramid`, `two-line-prism`, `two-line-cuboid`) và một cảnh từ chối (`two-line-refused`,
`PLANE_NOT_UNIQUE`) của run `two-line-plane-section`. Xuất lại cảnh từ mã hiện hành cho `scenes.json` trùng byte (SHA-256
`a4efde63…`) ⇒ bằng chứng nói về đúng mã đang chạy. Hai oracle tách biệt:

- **Toán** (`backend/scripts/audit_scene3d_construction.py`, 0 lượt gọi model): mỗi điểm theo producer trong toạ độ KHUNG
  (trung điểm, vectơ hai đầu mút, tịnh tiến; đỉnh đề cho so fixture độc lập; producer lạ ⇒ đỏ); H, H1 dùng hai đường đề
  cho KHÁC nhau, M, H, H1 không thẳng hàng; (P) là covector qua M, H, H1 và song song NGHIÊM NGẶT với hai đường (phương
  trong mặt, điểm của đường ngoài mặt); thiết diện so `two_line_plane_oracle.py` (nửa không gian mặt khối + bao lồi +
  diện tích Gram — thuật toán khác sản phẩm, cùng tác giả); đỉnh thiết diện trên đúng cạnh khối được đặt tên; bốn đoạn
  dựng dần đúng bằng bốn cạnh vòng, mỗi đoạn trong đúng mặt lời kể gọi tên. Không có tích vô hướng Euclid trên toạ độ
  khung. Toạ độ thế giới renderer nhận: |w(p)−w(q)|² = (p−q)ᵀG(p−q) cho mọi cặp điểm. Mỗi bước trace: đầu vào, đầu ra mới,
  phụ thuộc đã có ở bước trước, không vật nào biến mất, phân loại INIT/CONSTRUCTION/INTERPRETIVE. Biến thể metamorphic
  chạy lại route Hybrid thật (đổi thứ tự hai đường, đảo đầu mút từng đường, đảo hai đầu trung điểm, đặt tên trung điểm là H)
  qua cùng các phép kiểm điểm/thiết diện/bước. Tiêm lỗi: `backend/tests/geometry/test_scene3d_construction_audit.py`
  — 12 lỗi × 3 cảnh đều đỏ, cảnh thật xanh.
- **Hình** (`frontend/scripts/hybrid-section-visual-check.mjs --scenes two-line --playback`, harness Scene3DWorkspace qua
  route Hybrid, không phải trang sản phẩm/API): tua bằng `<input range>` của harness tới khung `anchor` của TỪNG bước học
  trong `geometryTimeline` — đúng khung `scene3d-playback.tsx` hiện cho bước học; camera cố định. Mỗi bước một ảnh trung
  tính; `objectsAt` (frontend) = `formation.visible_ids` (backend); vật vẽ ⊆ vật có mặt; vật vẽ được có mặt ⊆ vật vẽ; mỗi
  điểm vẽ có chấm đỉnh; neo nhãn điểm = phép chiếu của toạ độ payload chính xác qua `view × model × T` (đường tính của bộ
  đo khác đường `qRef·world → cam.project` của renderer); nhãn bị giấu phải chạm hộp một nhãn đang hiện, nhãn đang hiện
  không chồng nhau; neo nhãn và tập cạnh khuất của khối không đổi giữa các bước; quay lại một bước ⇒ trùng từng điểm ảnh;
  góc nhìn thứ hai (xoay) với cùng phép kiểm; chọn H, H1; contact sheet.

## 2. A. Construction correctness

| cảnh | bước trace / bước học | điểm có tên | toán | metamorphic (5) | neo nhãn lệch tối đa |
|---|---|---|---|---|---|
| chóp S.ABCD, G chéo, đáp số 9/4 | 16 / 13 | 8 | PASS | PASS | ≤0.001 px |
| lăng trụ đứng ABC.A′B′C′, G KHÔNG chéo, 3 | 14 / 11 | 9 | PASS | PASS | ≤0.001 px |
| hộp ABCD.A′B′C′D′, G chéo, 12 | 14 / 11 | 11 | PASS | PASS | ≤0.001 px |

Tổng 44 bước trace (35 bước học), 28 điểm có tên + 12 đỉnh thiết diện (thực thể riêng). Bảng từng bước: [`steps.md`](steps.md);
định nghĩa/toạ độ/quan hệ/trong-ngoài khối từng điểm: `after/audit-*/construction-audit.json`.

- **Không có sai toạ độ toán học (A), sai phép biến đổi renderer (B) hay sai chiếu màn hình (C).** Chứng cứ độc lập cho
  B/C là kiểm metric thế giới (TᵀT = G, sai số ≤1e-6, 28/36/55 cặp) và neo nhãn (≤0.001 px, cả hai GPU, cả góc xoay).
  Chấm đỉnh trả về toạ độ khung sai ≤3e-10 (làm tròn 1e-9 ở biên hiển thị) — phép này dùng lại T của chính renderer nên
  chỉ là kiểm nhất quán, không độc lập.
- **H, H1 ngoài khối là đúng**: H = M + BC, H1 = M + AS (chóp) / M + BB′ (lăng trụ, hộp); chóp: H1 ngoài khối; lăng
  trụ: H ngoài khối. Trùng toạ độ khác danh tính, có chủ đích: M ≡ đỉnh thiết diện trên AB (cả ba); H ≡ đỉnh trên CD (chóp,
  hộp); H1 ≡ đỉnh trên A′B′ (lăng trụ, hộp). Đặt tên trung điểm là H ⇒ điểm phụ thành H1, H2, không trùng id.
- **Thứ tự**: không vật nào hiện trước phụ thuộc hay biến mất; thiết diện chỉ hiện sau (P) và khối; bốn cạnh thiết diện
  lần lượt đúng mặt lời kể gọi (chóp ABCD → SCD → SBC → SAB; lăng trụ ABC → CAA′C′ → A′B′C′ → ABB′A′; hộp ABCD → CDD′C′
  → A′B′C′D′ → ABB′A′), khép ở cạnh thứ tư, tô ở bước khép. Bước "Lấy vectơ …" là bước diễn giải hợp đồng
  (`MEASUREMENT`, `non_visual`), nhập vào bước học trước; không bước dựng nào thiếu vật dựng.
- **Lỗi D đã sửa**: `locNhanChongNhau` coi hai nhãn chồng khi neo cách < 68×22 px cố định (cỡ cho câu mô tả dài thời
  trước). Trước sửa: chóp mất **S** từ bước học 4 tới cuối (cả khi chọn H1 — S thuộc chuỗi phụ thuộc); hộp mất **A′, B′**
  từ bước 4 trong khi lời kể nói "cạnh A′B′"; lăng trụ mất B ở góc xoay. Sửa: so hộp nhãn thật (`offsetWidth/Height`,
  cùng quy ước `translate(-50%,-140%)`) + khe 2 px; đọc cỡ một lần mỗi khung trước khi ghi style. RED `632d7e15` →
  GREEN `eea6f3df`. Sau sửa nhãn duy nhất còn giấu là B ở góc xoay của hộp — B chiếu gần trùng A′, hộp chạm thật.
- **Hạn chế E còn mở** (`ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`): Planner dựng M, H, H1 trước đáy/cạnh/khối — bước
  "Dựng M" hiện M khi chưa có đoạn AB. Đúng toán; sửa cần đổi Planner + đo lại dev/heldout; người dùng chọn ghi lại.

## 3. B. Visual evidence

Mỗi cảnh trong `after/swiftshader/` và `after/intel-d3d11/` (đối chiếu: `before/swiftshader/`): `contact-sheet.png`
(+`.html`), `step-NN.png` từng bước học, ảnh trung tính cuối = bước học cuối, `final-orbit.png` (góc thứ hai),
`selected-H.png`, `selected-H1.png`; `two-line-refused/refused.png` (không canvas, có mã). Ảnh chụp thẳng từ
Scene3DWorkspace, không xử lý ảnh. Chưa kết luận được bằng máy: mức nhạt của chế độ chọn; độ phân biệt nét khuất / cạnh
thiết diện / mặt phụ; khoảng trống canvas (phần xám dưới khung là container harness, không phải sản phẩm) — để người
nghiệm thu. Tên mặt (P) vẫn không vẽ trên canvas (chỉ trong bộ chọn/chi tiết) — hạn chế cũ, không đổi. Nút/thanh điều
khiển của harness nay cách nhau (`flex`, gap 16 px) — chỉ harness.

## 4. C. Playwright audit

[`playwright-audit.md`](playwright-audit.md): DEAD_CONFIRMED 0; xoá/gộp 0. Bốn bản `spot-check-*` là bản sao (lệch 6 dòng)
nhưng bị ghim SHA-256 ở `source-grounding-integration/preservation.json`; gộp cần quyết định riêng. Lượt này chỉ mở
rộng harness Hybrid hiện có (`--playback`).

## 5. D. Regression

- Toán: `after/audit-swiftshader`, `after/audit-intel-d3d11` 0 lỗi; `before/audit` đỏ đúng các bước hình (19 bước học).
- Hình: trước sửa 19 lỗi "nhãn giấu không chạm" (đúng các bước nêu trên), sau sửa 0 trên SwiftShader và Intel UHD
  D3D11; 2 và 1 lần thử lại mạng cục bộ được ghi trong receipt. Bundle đo của từng lượt: `verification/bundles.json`
  (`git_head` trong receipt là cây chạy bộ đo `d4327342`; lượt "trước" phục vụ bundle có luật cũ).
- Vitest liên quan 581/581, `tsc -b` PASS (riêng commit RED `632d7e15` đỏ `tsc` vì truyền `w`/`h` trước khi kiểu có).
  Bộ đo bố cục tám họ (`check-mobile-layout.mjs`, desktop + dọc): 16/16 PASS trước và sau, số nhãn và độ lấp từng họ không
  đổi (`verification/layout-probe-*`) — chỉ khung đầu, góc mặc định. Rủi ro còn mở: luật mới giấu nhiều hơn luật cũ khi
  hai nhãn rộng trung bình > ~66 px (nhãn ký hiệu dài như "H1′" hiếm).
- `scene3d-orbit-gate.mjs` KHONG_ON_DINH p1/p6/p7 giống hệt trên bản trước sửa ⇒ môi trường máy này, không do sửa; cổng
  này không cho tín hiệu (`ISSUE-OPS-ORBIT-GATE-UNSETTLED-LOCAL`; `verification/orbit-gate*`).
- Candidate đóng băng lại ở worktree sạch tách rời: product `eea6f3df`, freeze `bfda732c`, tree hash `c2ac6dbe…` không đổi
  (renderer ngoài `MEASURED_SYSTEM_PATHS`), divergence cộng thêm `inputs/candidate_divergence.json` (nối chuỗi `corrects`
  sau two-line; hoàn thiện lược đồ ở `b8e96a86`); `CACHE_VERSION` 125 giữ (`cache/decision.json`). Dev 45 / heldout 32 /
  lịch sử 30 không đo lại — không đổi backend.
- **T3** (worktree sạch tách rời): lần 1 tại `bfda732c` FAIL 1 test (`test_C2b…`, lớp divergence thiếu trường) — giữ
  `verification/t3-first-failure.json`, không ghi công; lần 2 tại `b8e96a86` **FULL_PRODUCT_GATE_PASS**: backend 9300 passed
  (skip 1, deselected 2, xfail 6), frontend 1055/68 file, build, tập demo, bề mặt sập 6/6; 0 lần thử lại socket
  (`verification/t3-pass.json`, log SHA-256 `5b6570be…`).
- **Review độc lập** (subagent, chỉ đọc): NONBLOCKING, 16 phát hiện — 9 sửa ở `d4327342` (bộ đo, không phải sản phẩm,
  T3 không phải chạy lại; `test_scene3d_construction_audit.py` 36/36), còn lại ghi giới hạn; [`review.md`](review.md).

## 6. Git & cleanup

Commit: `3db3a50f` audit + harness · `632d7e15` RED · `eea6f3df` sửa nhãn · `bfda732c` đóng băng · `b8e96a86` lược đồ
divergence · `d4327342` sửa khoảng hở review · commit tài liệu cuối. Push NONE; main không đổi. Dọn: `cleanup.json`.
