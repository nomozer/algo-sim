# Kiểm kê script trình duyệt / chụp ảnh — `frontend/scripts/` (2026-10-14)

Consumer đếm bằng `grep`: npm (`frontend/package.json`), T0/T3 (`impact.mjs`, `full-gate.mjs`), import giữa script,
test (`frontend/src`, `backend/tests`), tài liệu sống (ngoài `docs/evaluation`, `docs/legacy`), bằng chứng run
(`docs/evaluation`). Không có CI (`.github` không tồn tại). **Không npm script nào và không tầng T0–T3 nào gọi một script
trình duyệt** — mọi cổng trình duyệt là lệnh tay ghi trong `CODE_INDEX.md`/run. `docs/evaluation/geometry/runs/
source-grounding-integration/preservation.json` ghim SHA-256 của các script đánh dấu ★ là công cụ nghiên cứu được bảo
toàn — sửa/xoá chúng phá bản ghi bảo toàn ấy.

Playwright CLI (skill `playwright-cli`, thao tác tay) không thay thế các script này: chúng mang phán quyết máy, ngưỡng đặt
trước và receipt JSON gắn bằng chứng; CLI không có phần nào trong số đó.

| script | chức năng | consumer | phân loại |
|---|---|---|---|
| `browser-runner.mjs` | phiên Chrome CDP dùng chung (`BrowserSession`) | 14 script import; node-test riêng | SHARED_UTILITY (đã là tiện ích chung) |
| `compiler-scene-suite.mjs` | thao tác/chụp/khẳng định dùng chung cho cảnh compiler | 7 script import | SHARED_UTILITY |
| `compiler-scene-replay-lib.mjs` | hàm thuần phán quyết playback/orbit/chiếu (`assessPlayback`, `diemTheGioi`…) | 7 import, 2 test, node-test | SHARED_UTILITY |
| `png-pixels.mjs` | giải mã PNG không phụ thuộc | 2 import | SHARED_UTILITY |
| `capture-policy.mjs` · `evidence.mjs` | chính sách chụp; vân tay nguồn của bằng chứng | nhiều import, node-test | SHARED_UTILITY |
| `scene3d-orbit-gate.mjs` | cổng xoay quỹ đạo (CLAUDE.md: chạm `domains/geometry`) | 9 import, node-test, 22 run | KEEP_ACTIVE (đỏ môi trường máy này — `ISSUE-OPS-ORBIT-GATE-UNSETTLED-LOCAL`) |
| `compiler-scene-replay.mjs` | phát lại cảnh compiler trên `dist/` | 5 test, 96 run | KEEP_ACTIVE |
| `scene3d-playback-check.mjs` ★ | playback người học trên trang sản phẩm (fixture) | 65 run | KEEP_ACTIVE |
| `hybrid-section-visual-check.mjs` · `-serve.mjs` · `hybrid-section-visual.tsx/.html` | harness Scene3DWorkspace cho cảnh Hybrid; nay `--playback` | runs hybrid-*, two-line, lượt này | KEEP_ACTIVE (mở rộng nhỏ, không script mới) |
| `check-mobile-layout.mjs` · `check-panels.mjs` · `check-scene-controls.mjs` · `check-focus-mode.mjs` | đầu dò bố cục/bảng/nhãn theo bước/chế độ tập trung trên `dist/` | CODE_INDEX, các run UX | KEEP_ACTIVE |
| `photo-problem-browser-check.mjs` | luồng ảnh đề (CLAUDE.md) | docs, run | KEEP_ACTIVE |
| `certify-*.mjs` (11) | cổng nghiệm thu từng đợt (hidden lines, fidelity, refusal, journey…) | 1–8 run mỗi script, 3 có test | RESEARCH_EVIDENCE_REQUIRED |
| `spot-check-matrix.mjs` ★ · `spot-check-baseline.mjs` ★ · `spot-check-baseline-v2.mjs` ★ · `spot-check-translation.mjs` ★ | ba cảnh AI trong Chrome; ba bản sau là bản sao 172 dòng, lệch `matrix` đúng 6 dòng (nguồn cảnh) | CODE_INDEX, RUN_NAMING, báo cáo demo | DUPLICATED_REPLACEABLE nhưng bị ghim ★ ⇒ giữ; gộp = `--scenes` cho `spot-check-matrix` ở lượt riêng |
| `spot-check-demo.mjs` ★ | tập demo khoá luận trong Chrome | báo cáo demo | RESEARCH_EVIDENCE_REQUIRED |
| `replay-cuboid-cube-browser.mjs` · `replay-rectangular-pyramid-browser.mjs` | replay từng họ trước khi có `compiler-scene-replay` | OPEN_ISSUES, CODE_INDEX, audit run | RESEARCH_EVIDENCE_REQUIRED (chức năng đã do `compiler-scene-replay.mjs` phủ) |
| `scene3d-browser-acceptance.mjs` · `scene3d-acceptance-report.mjs` | cổng nghiệm thu đợt đầu + gom contact sheet với mockup | 1–2 run | RESEARCH_EVIDENCE_REQUIRED |
| `verify-point-projection.mjs` ★ | chiếu toạ độ thế giới rồi bấm đúng chỗ (envelope demo) | CODE_INDEX | RESEARCH_EVIDENCE_REQUIRED (ý tưởng nay nằm trong `--playback`) |
| `scene3d-interaction-probe.mjs` · `measure-page-boot.mjs` · `measure-relaunch-recovery.mjs` · `flake-repeat.mjs` · `diagnose-refusal-flake.mjs` · `faultcheck-refusal-surface.mjs` | đo độ mượt, khởi động trang, phục hồi phiên, flake | 1–3 run | RESEARCH_EVIDENCE_REQUIRED |
| `demo-geometry-interaction.mjs` · `capture-release-demo.mjs` · `audit-layout.mjs` · `accept-live-classroom.mjs` · `accept-product-scope.mjs` · `geometry-library-expansion-visual.tsx/.html` | demo tay, ảnh phát hành, soát bố cục, nghiệm thu lớp/phạm vi, harness thư viện hình | docs + 1–2 run | RESEARCH_EVIDENCE_REQUIRED |

**DEAD_CONFIRMED: 0** — mọi script còn ít nhất một consumer trong tài liệu sống hoặc bằng chứng. **Xoá/gộp trong lượt
này: 0.** Lý do: không script nào thoả đủ năm điều kiện (hết consumer, bảo toàn khẳng định, so sánh trước/sau không mất độ
phủ, không phá tái lập lịch sử, cập nhật tham chiếu); bốn bản `spot-check-*` và các script ★ bị ghim bởi
`preservation.json`. Phần trích xuất chung nhỏ nhất đã có sẵn (`browser-runner`, `compiler-scene-suite`,
`compiler-scene-replay-lib`, `png-pixels`) nên lượt này chỉ mở rộng harness Hybrid (+`--playback`) thay vì thêm script.
Kế hoạch gộp `spot-check-*` (một script + cờ nguồn cảnh, giữ bản ghim bằng commit lịch sử) cần quyết định của người dùng
vì đổi bản ghi bảo toàn.
