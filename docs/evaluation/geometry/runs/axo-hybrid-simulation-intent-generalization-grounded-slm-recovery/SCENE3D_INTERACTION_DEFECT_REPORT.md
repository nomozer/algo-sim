# Scene3D interaction defects (P7)

Bằng chứng: `V17_POINTER_INTERACTION_RESULTS.json`, `V11_UI_SCENARIO_RESULTS.json` và ảnh chụp trong `evidence/v17/`,
`evidence/ui/screenshots/`. Mọi lượt dùng trình duyệt thật (Playwright Chromium, WebGL qua SwiftShader) trên app thật,
backend sống.

## V17 — kéo từ giữa canvas không xoay (đã sửa)

- **Nguyên nhân gốc (dò con trỏ):** chip số đo `.geo3d-so-do` (role=button, `pointer-events: auto`) nằm đúng tâm canvas
  và nhận `pointerdown`. OrbitControls nghe trên canvas nên cú kéo không bao giờ tới nó. Trước sửa: 0/4 lần kéo từ tâm
  xoay được (ở mọi độ trễ 0/500/1500/3000 ms); kéo từ chỗ trống: xoay được.
- **Sửa** (`b15fd9e92`, `scene3d-view.tsx`): một cú kéo bắt đầu trên lớp phủ và đi ≥ 4 px được chuyển sang canvas
  (`pointerdown` tổng hợp tại điểm bắt đầu, rồi `pointermove`). Cú bấm không di chuyển vẫn thuộc về chip.
- **Sau sửa:** kéo từ tâm xoay được 4/4. I01: 4/4 cảnh (V17 của /10 có chip ở tâm, cộng C09, S01, C13). I02: kéo bắt đầu
  trên cạnh, trên chip và cạnh nhãn đều xoay được. I03: xoay được sau đặt lại góc nhìn và sau khi đổi đề.
- Ghi chú: bấm chip cho `aria-pressed=false` ở **cả** build trước sửa lẫn sau sửa, tức là hành vi có từ trước, không phải
  hồi quy.

## U08 — đặt lại góc nhìn lần hai làm nhãn lệch (đã sửa, kiểm sau lượt mù)

- **Đo trên build mù:** sau hai lần đặt lại, nhãn lệch 4 px (lượt chính), rồi 3 px (lượt chạy lại), và giữ nguyên từ
  100 ms tới 4.5 s. Khung ảnh (camera) gần như trùng, tức không phải camera lệch.
- **Nguyên nhân gốc:** `lamMuotLechNhan` (owner P5, 2026-10-26) mỗi khung đưa nhãn đi nửa quãng còn lại. Nhưng vòng vẽ
  theo yêu cầu dừng sau một khung, nên sau cú nhảy camera nhãn **dừng giữa đường**, và lần vẽ không liên quan tiếp theo
  (lần đặt lại thứ hai) đẩy nó thêm vài px.
- **Sửa** (`31e6b47c9`): `nhanChuaToiCho` đánh dấu còn nhãn đang trượt; `isAnimationActive` giữ vòng vẽ thức tới khi
  nhãn tới đích. Hàm trượt `lamMuotLechNhan` co về đích khi lệch < 0.5 px nên vòng vẽ chắc chắn dừng. Test 4d trong
  `simulation-visual-consistency-session1.test.tsx`.
- **Sau sửa (cùng harness, build `dist-u08`):** lệch **0 px** ở mọi mốc 100 ms tới 4.5 s (`ui_scenarios_post_u08_fix.json`).
  Đây là kiểm sau lượt mù. Chỉ số tương tác của lượt mù (232/232) không đổi.

## V11-VIS-1 — đỉnh bị cắt ở mép canvas (mới, chưa sửa)

S07 (`O.ABC`, OA, OB, OC đôi một vuông góc) và Q01 (`S.ABC`, SA ⊥ (ABC)): đỉnh B nằm ngoài mép dưới canvas ở khung
ban đầu (`labels.outside_canvas = ["B"]`, ảnh `v11_S07.png`, `v11_Q01.png`). Cảnh vẫn đúng toán. Kiểu hình chung: một
đỉnh rất gần camera, bị co phối cảnh mạnh. Nghi ở hàm khớp khung `khungNhinQuanhTam` (vùng an toàn tính theo bán kính
quanh tâm xoay, không chiếu từng đỉnh). Phát hiện sau lượt mù nên chưa sửa; ghi vào `OWNER_HANDOFF.md`.

## Điểm O suy ra trình bày như điểm tự do (còn, ngoài quyền)

Ở 7 cảnh khối đều (S03, S04, S25, S33, C04, C05, C19), đề không nêu O nhưng envelope có điểm `O` với `origin: "free"`,
`source.provenance: "LAYOUT_DERIVED"`, nhãn "Điểm O". Tức tâm đáy hay chân đường cao **do hệ suy ra** được trình như một
điểm tự do, không có lineage "tâm của …". Toán vẫn đúng: oracle chấp nhận nó là `derived_auxiliary_points`. Người tạo
trường `origin`/`provenance` là adapter/engine (khoá), nên mục này được bàn giao. /11 không sửa dữ kiện để đổi nhãn.

## V20 — quan hệ đã kiểm nhưng không có bước diễn giải

Không đổi trong /11: thiếu presentation step cho quan hệ đó là capability gap của tầng trình bày. Không tích hợp
Construction Planner /2 để vá (theo prompt §14).
