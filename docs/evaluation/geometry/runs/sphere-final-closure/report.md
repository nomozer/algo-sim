# Chốt hình cầu Scene3D — gói duyệt cho Owner

Trạng thái: **SPHERE_VISUAL_MERGE_GATE_BLOCKED** — chờ hai quyết định chỉ Owner được ghi: (1) duyệt hình cuối,
(2) oracle F2 (hoặc ngoại lệ bằng văn bản cho `cross_section`). Không merge `main`, không cleanup, không push,
0 lượt gọi model, `LLM_ONLY`, `CACHE_VERSION = 130`.

## 1. Lỗi đã sửa (commit `b101dc79`, chỉ renderer mặt cầu)

| | trước | sau |
|---|---|---|
| Đường bao cầu (`SPHERE_SILHOUETTE`) | vành mesh dày 0,6 % bán kính ⇒ ~1 px, xám nhạt, đậm nhạt không đều; mobile gần như mất | một đường kín đặt theo camera như cũ (đường tiếp xúc phối cảnh, toán không đổi), vẽ bằng lượt nét pixel chung ở **độ dày cạnh thấy**, không bị depth test cắt |
| Xích đạo tham chiếu (`REFERENCE_EQUATOR`) | dùng kiểu vành đáy thật ⇒ đậm hơn cả đường bao (ngược thứ bậc) | vai `presentation_reference` (chỉ frontend): xám nét phụ, dải mảnh hơn; trước liền / sau đứt vẫn theo camera |
| Giao tuyến thật (`ACTUAL_SECTION_CURVE`) | — | không đổi; tô cam đất, chọn ⇒ viền xanh, tô vẫn cam |

Ba loại đường giờ có ba quy tắc vẽ riêng. Không đổi camera, background, bố cục, theme hay cảnh đa diện/trụ/nón.
Test đỏ → xanh: `scene3d-curved-transitions.test.ts` (đường bao kín, đúng độ dày pixel cạnh thấy, không depth test;
xích đạo màu nét phụ và mảnh hơn vành thật cùng bán kính). Hai test đếm `Line` được giữ ý đồ (không kinh/vĩ tuyến thừa).

## 2. Oracle hình học (cầu tâm I, R = 5) — `inputs/sphere-plane-oracle.json`

Sinh qua **đường sản phẩm** của bộ dựng mẫu; oracle độc lập: dist = |a·I + d|/|n|, r² = R² − dist², tâm = hình chiếu I.

| ca | mặt phẳng | kết quả |
|---|---|---|
| trên tâm | z = 3 | r² = 16, tâm (0,0,3) — khớp |
| qua tâm | z = 0 | r² = 25, tâm I — khớp |
| nghiêng | x + 2y + 2z = 6 | dist = 2, r² = 21, tâm (2/3, 4/3, 4/3) — khớp |
| tiếp xúc | z = 5 | từ chối `CURVED_PLANE_TANGENT`, không vẽ đường tròn |
| không cắt | z = 6 | từ chối `CURVED_PLANE_DOES_NOT_CUT`, không giao tuyến giả |

## 3. Trình duyệt (0 lượt gọi model) — trước `before-57a4d65c/`, sau `after-b101dc79/` (cây sạch)

4 cảnh (cầu cơ bản, cắt trên tâm, qua tâm, nghiêng) × 7 góc (`front`, `back`, `left`, `right`, `high`, `low`,
`near-edge-on`) × vòng orbit liên tục 24 bước × 1440/390; cảnh cắt thêm chọn/bỏ chọn giao tuyến. 0 lỗi trang.
"Hình phụ" không có trong cảnh cầu cắt (mặt phẳng (P) là đối tượng chính) — ghi N/A.

Quét pixel đường bao trên 24 khung orbit (`tools/silhouette_scan.py`; bộ quét đã được tự chứng trên khung thấy
liền nét — hai phiên bản đầu sai được ghi lại trong docstring):

| | tia mất đường bao / khung (tối đa · tổng) | CV bán kính |
|---|---|---|
| 1440 trước → sau | 39 · 517 → **3 · 19** | 0,004 → 0,007 |
| 390 trước → sau | 330 · 7731 → **6 · 53** | 0,011 → 0,004 |

## 4. Ảnh cần Owner duyệt (mở trực tiếp các PNG)

| nội dung | trước | sau |
|---|---|---|
| cầu cơ bản — phía trước | `before-57a4d65c/basic-1440-front.png` | `after-b101dc79/basic-1440-front.png` |
| cầu cơ bản — phía sau | `…/basic-1440-back.png` | `…/basic-1440-back.png` |
| cầu cơ bản — góc thấp | `…/basic-1440-low.png` | `…/basic-1440-low.png` |
| gần tiếp tuyến | `…/basic-1440-near-edge-on.png` | `…/basic-1440-near-edge-on.png` |
| mobile | `…/basic-390-front.png`, `…/basic-390-low.png` | idem |
| mặt phẳng (P) trên tâm / qua tâm | `…/cut-above-1440-front.png`, `…/cut-through-1440-back.png` | idem |
| mặt phẳng nghiêng | `…/cut-tilted-1440-front.png` | idem |
| chọn / bỏ chọn giao tuyến | `before-57a4d65c-interact/cut-above-1440-section-selected.png` | `after-b101dc79/cut-above-1440-section-selected.png`, `…-section-deselected.png` |
| orbit liên tục | `…/basic-1440-orbit00…23.png` | idem; số đo `silhouette-*.json` |

Kết quả test xanh **không** phải `OWNER_VISUAL_APPROVED`.

## 5. Official Visual Suite (oracle khoá, không sửa) — `visual/official-run-3994f603/`

**7/8.** Chỉ `cross_section` hỏng, đúng chữ ký kế thừa: `canvas_role_hues.cam` → `causal_closure`, `evidence_gates`
(desktop + mobile) — oracle đếm mọi pixel cam ở trạng thái chọn là vi phạm, trong khi chính sách F2 của Owner giữ tô cam
và chỉ đổi viền sang xanh. Đầu vào khoá rebind chỉ danh tính (49 đầu vào, 0 envelope/kịch bản/oracle đổi:
`official-inputs-3994f603-rebinding.json`). Chưa viết oracle F2 mới: việc đó cần Owner duyệt và review oracle riêng.

## 6. Candidate và cổng

Product `b101dc79`, candidate `3994f603` (`3850e787…`, 118 file; cây sạch).

Full T3 lần 1 tại `7e545f66`: **FULL_PRODUCT_GATE_FAIL** — 1 test (`test_hybrid_ab_pilot_runner` `FULL_AB-288`,
`PERSISTENCE_FAILED`), 11992 passed, vitest 1416/1416; receipt giữ nguyên ở `t3-fail-7e545f66.json`. Backend giống hệt
lượt T3 PASS trước (`57a4d65c`); chạy lại file trên cùng cây sạch đỏ 3/11 lần; lỗi bị nuốt được bắt bằng hook chẩn đoán
ngoài kho: `PermissionError [WinError 5]` ở `os.replace` (`t3-fail-root-cause-oserror.log`) — khoá file tạm thời của
Windows, không phải hồi quy sản phẩm. Sửa ở `backend/scripts/run_hybrid_ab_pilot.py` (`682568be`, ngoài đường đo,
candidate không đổi): thử lại có giới hạn, khoá kéo dài vẫn fail-closed; 2 test mới (đỏ → xanh), 9/9 lượt chạy lại xanh.
Full T3 lần 2: xem `t3-receipt.json`.

| điều kiện merge (P2.5) | trạng thái |
|---|---|
| lỗi cầu ưu tiên đã khép, regression có mục tiêu xanh, không lỗi hình học mới | đạt |
| freeze sạch + Full T3 PASS | xem `t3-receipt.json` |
| Official Visual theo oracle được duyệt **hoặc** ngoại lệ Owner bằng văn bản | **chưa** (7/8) |
| Owner xác nhận hình cuối | **chưa** |
| review độc lập | **chưa có** (ghi rõ; merge local khi Hybrid tắt cần Owner chấp thuận phạm vi rủi ro) |

## 7. Đã chuẩn bị cho P3/P4 (chưa thực hiện)

- Merge: `main` = `9978e512` là tổ tiên của candidate (147 commit) ⇒ `git merge --ff-only` khả thi; `origin/main`
  (`43247c9e`) là tổ tiên của `main`. Candidate có `cacheDir: ".vite-cache"` + `.gitignore`, `CACHE_VERSION = 130`,
  mặc định `LLM_ONLY`. Root checkout đang bẩn (27 mục) ⇒ không merge từ root; cách cập nhật `main` an toàn phải chọn khi
  được duyệt (root đang ở nhánh khác, nên `main` không bị checkout ở đâu).
- Nhánh có commit ngoài candidate (giữ, không merge, không xoá): `research/nl-to-scene3d-e2e-readiness`,
  `research/hybrid-next-architecture-gap-audit`, `integration/extraction-v2-safety`, `research/hybrid-semantic-extraction-v2`,
  `research/compact-geometry-dsl`, `feat/real-model-pilot-tooling`, `docs/real-model-e2e-readiness`.
- Kiểm kê 41 worktree (chỉ đọc): 12 đăng ký mất thư mục (`prunable`), 9 worktree bẩn (giữ), còn lại sạch và nằm trong
  candidate. Không xoá gì trước khi `main` được tích hợp.

## 8. Owner cần trả lời

1. Duyệt hình cuối ở §4 (hoặc chỉ ra ảnh/góc còn sai).
2. F2: (a) chấp thuận ngoại lệ bằng văn bản cho `cross_section` để merge với 7/8, hoặc (b) giao viết oracle F2 mới theo
   chính sách (đúng mã màu, mọi thiết diện, fault injection, review riêng) — khi đó merge chờ oracle mới.
3. Chấp thuận phạm vi rủi ro merge local khi chưa có review độc lập (Hybrid vẫn tắt).
