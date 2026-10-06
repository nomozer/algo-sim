# Ponytail review — diff W05 (`73bc404e..` + cây làm việc trước commit giao diện)

Phạm vi: `segment_relation.py`, `grounding_gate.py`, `quantity_annotations.py`, `App.tsx`, `store.ts`, `TopNav.tsx`,
`SimulationWorkspace.tsx`, `Scene3DExplorer.tsx`, `scene3d-tool-menu.tsx`, `scene3d-playback.tsx`, `global.css`,
harness (`compiler-scene-suite.mjs`, `compiler-scene-replay-lib.mjs`, `w05-focus-probe.mjs`, ba đầu dò cũ).

- `segment_relation.py:_do_dai_doan`: shrink — bản regex thứ hai của cùng phép đọc. **Đã làm**: một dòng gọi `_moi_doan_co_do_dai`.
- `scene3d-solution.tsx`: delete — thẻ lặp tập `quantityChoices`. **Đã làm** (151 dòng + ~130 dòng CSS `.geo3d-lg-*`).
- `compiler-scene-suite.mjs:DOC_DAI_LUONG/solutionState`: delete `body_collapsed: false` + `solution_collapsed` chuyền qua — khái niệm của thẻ đã gỡ, hằng số chết. **Đã làm**.
- `compiler-scene-suite.mjs:setSolutionOpen/clickSolutionRow`: delete — **đã làm**; nhánh "lời giải MỞ" trong chọn từng đại lượng gỡ theo.
- `scene3d-tool-menu.tsx:hoTroToanManHinh`: giữ — một dòng nhưng là chỗ kiểm được của luật "chỉ khi hỗ trợ" (SSR + test thuần).
- `Scene3DExplorer.tsx:lopDaiLuong`: giữ — thay `lopDongLoiGiai` đã gỡ (không phải bản sao: nguồn cũ đã xoá).
- `SimulationWorkspace` slot `daiLop`: giữ — một prop sẵn có mang thêm hai phần tử vỏ thay vì thêm prop mới.
- `w05-focus-probe.mjs`: yagni? — không: là cổng trình duyệt duy nhất cho C/D (vỏ, menu, toàn màn hình, quay lại); dùng lại `phucVu`/`openFixture`/`trustedClick`/`capture`.

net: −~300 dòng sản phẩm (thẻ lời giải + CSS + regex thứ hai) đã cắt; không còn mục cắt được trong phạm vi.
