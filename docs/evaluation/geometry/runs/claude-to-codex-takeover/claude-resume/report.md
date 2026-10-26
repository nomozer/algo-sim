# Báo cáo tiếp quản lần 2 (Claude → Codex → Claude), 2026-10-26

Trạng thái: **LOCAL_PARTIAL_WITH_GAPS** · Scene3D **SCENE3D_VISUAL_PARTIAL_WITH_GAPS** · không merge, không push,
0 lượt gọi model, `LLM_ONLY` mặc định, `CACHE_VERSION = 130`, Hybrid production NO-GO.

## 1. HEAD/branch/worktree lúc tiếp quản

Chi tiết và bằng chứng: [`../../scene3d-codex-takeover/CLAUDE_RESUME_CHECKPOINT.md`](../../scene3d-codex-takeover/CLAUDE_RESUME_CHECKPOINT.md).
Nguồn sự thật cuối của Codex: worktree `s3d-hybrid-v2-codex`, nhánh `research/scene3d-hybrid-v2-codex`, HEAD `e336e0df`
+ 69 file evidence chưa commit. Dòng commit tuyến tính `08929b89 → … → 11188e7a (Codex #1) → 3dcd6d9f (Claude) →
e336e0df (Codex #2)`. Claude làm tiếp ở worktree **mới** `s3d-hybrid-v2-claude`, nhánh
`research/scene3d-hybrid-v2-claude-resume` (không ghi vào cây của Codex/Claude cũ, vì app-server Codex còn sống).

## 2. Codex đã làm gì, Claude làm tiếp gì

Codex #2: cầu góc V2 + tuyến phát lại cục bộ, kiểm "chéo nhau" (engine `/12`), NFC/NFD, chặn ảnh trước Vision,
`no-store`; Full T3 dở. Claude: hoàn tất bump `/12` dở dang, chẩn đoán T3, LF/CRLF, Scene3D Checkpoint C, Hybrid V2
Checkpoint D. Không làm lại phần đã chứng minh.

## 3. Bảo toàn file chưa commit

112 file của Claude: băm lại khớp 112/112; archive `8db6107d…` không đổi. 69 file evidence của Codex: chuyển sang
worktree mới bằng tar, `sha256sum -c` 69/69. Thay đổi chưa commit của Owner ở root (19 file tracked + 60 untracked):
sao lưu nguyên byte ở `.superpowers/backups/codex-to-claude-20261026-1440/`, **không** chạm; mọi file tracked đã sửa ở
root đều có đúng byte trong một commit cũ (không có công việc bị bỏ rơi).

## 4. LF/CRLF

Nguyên nhân: `core.autocrlf=true` ở cấp **system**, kho không có `.gitattributes` gốc. Manifest evidence băm **byte
thô**: 53 file viết CRLF bị lưu blob LF; 11 file viết LF bị checkout mới đổi CRLF. Candidate hash sản phẩm không bị
ảnh hưởng (`bam_noi_dung` chuẩn hoá CRLF). Sửa theo quy ước sẵn có (`.gitattributes` `-text` theo từng thư mục run):
hoàn thiện bản dở của Codex + thêm hai path `official-inputs-e336e0df*`; blob đã stage = byte gốc của cây viết ra.
Không áp `-text`/`eol=lf` toàn cục. Chưa kiểm: các run lịch sử khác có thể mang cùng lệch tiềm ẩn.

## 5. Full T3 "27 %" thực sự hỏng gì

PID launcher đã chết, không receipt ⇒ **INCOMPLETE**. Ánh xạ vị trí ký tự vào thứ tự collect rồi chạy lại từng id;
pytest đầy đủ (chẩn đoán) ở `e336e0df`: 8 failed / 11976 passed; vitest 1 failed / 1407. Chín lỗi, **0 regression sản
phẩm**: docs-gate (bundle 303 > 300 dòng) ×2, pin engine `/11` ×3, taxonomy thiếu `SKEW_CLAIM_CONTRADICTED`, fixture
chỉ lệch danh tính `/12` (khai `IDENTITY_DELTAS`), thiếu lớp khai candidate, test vitest phụ thuộc EOL. Bảng đầy đủ:
[`t3-diagnosis.json`](t3-diagnosis.json).

## 6. Test chạy lại có mục tiêu

Mỗi bản sửa: test đỏ trước rồi xanh; file test liên quan; miền geometry frontend; build. Pytest đầy đủ chạy hai lần
để chẩn đoán (không phải T3). Full T3 có thẩm quyền: mục 13.

## 7. Lỗi hình đã sửa / chưa sửa

Đã sửa ([`SCENE3D_CHECKPOINT_C.md`](SCENE3D_CHECKPOINT_C.md)): chấm chân thừa tô đỉnh đề cho thành điểm dẫn xuất;
panel lặp "X = hệ trục…" ×5; cỡ chữ dòng không bấm được; ký hiệu vuông góc 12–18 → 16–22 px (mobile bị chấm đỉnh che);
dấu đại diện không đặt chồng lên chân đã có dấu riêng. Chưa sửa (cần Owner): độ đậm cung tham chiếu mặt cầu, đường
thẳng đang xét vẽ nhô quá đầu mút, khung bị cắt ở một số góc xoay Mode B, chấm điểm trên đường cong đậm khó thấy.

## 8. Hình cần Owner duyệt

`p0-after-size/` (60 khung: `the-tich-chop`, `mp-vuong-goc-duong`, `vuong-goc-chop`), `common-perpendicular-browser/`
(60 khung: AA′–BC, AB–B′C, H11), cùng các mục ở §7.

## 9. Official Visual Suite

**7/8** kế thừa (`cross_section`: oracle F2 khoá vs chính sách cam đất/viền xanh của Owner). Không chạy lại, không đổi
oracle, không gọi là 8/8. Lượt chạy Playwright của Codex hỏng hạ tầng (CDP `Page.enable`), receipt giữ nguyên.

## 10. Hybrid V2 có thêm gì

Khoảng cách hai đường chéo nhau giờ dựng **đoạn vuông góc chung chính xác** (hai chân, hai dấu, phần kéo dài khi chân
ngoài cạnh), tự kiểm `|PQ|² = d²`, chỉ ở tuyến D (LLM_ONLY không đổi byte ⇒ NO_BUMP có test khoá). Bằng chứng E2E
offline: test tuyến D thật, 41 fixture Adapter /2 xuất lại, 60 khung trình duyệt. Chi tiết:
[`HYBRID_V2_CHECKPOINT_D.md`](HYBRID_V2_CHECKPOINT_D.md).

## 11. Độ phủ 18 họ

Không đổi hạng: **0 FULL_E2E_VERIFIED / 9 PARTIAL / 7 RENDER_ONLY / 2 UNSUPPORTED**
(`../families.md`). Họ 2 (`hai_dt_cheo_nhau`): đóng khoảng trống "thiếu đoạn vuông góc chung", vẫn PARTIAL.

## 12. Holdout/review còn thiếu

Holdout độc lập: chưa có. Chất lượng trích xuất NL: UNKNOWN. Review độc lập: chưa (không gọi subagent nội bộ là độc lập).
Owner duyệt hình: PENDING.

## 13. Candidate, product, verification

Product `1faee1db`; candidate `96415cbd` (`3850e787…`, 118 file), khai ở `../inputs/candidate_divergence.json`.
Full T3: **FULL_PRODUCT_GATE_PASS** tại `57a4d65c` trên worktree detached sạch `t3-claude-resume`
([`t3-receipt.json`](t3-receipt.json); wrapper `tools/run-t3.py`): pytest 11993 passed / 1 skipped / 15 xfailed,
vitest 1414/1414 (83 file), typecheck + build PASS, demo replay và crash surface PASS, cây sạch trước và sau,
post-freeze `--verify` MATCH (`3850e787…`). Log thô ở root `.superpowers/claude-resume-t3-57a4d65c/` (ngoài Git).
Đây là kiểm chứng máy, không phải review độc lập.

## 14. Quyết định còn cần Owner

(a) bật đoạn vuông góc chung cho LLM_ONLY (kèm bump cache 130 → 131); (b) cỡ 16–22 px của ký hiệu vuông góc;
(c) các điểm trình bày ở §7; (d) xung đột oracle F2; (e) phạm vi lát Hybrid kế tiếp (cung góc không vuông là ứng viên).

## 15. Bàn giao

[`NEXT_AGENT_HANDOFF.md`](NEXT_AGENT_HANDOFF.md).
