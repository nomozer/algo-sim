# Báo cáo — Unified Geometry Visual Language (Scene3D)

Ngày 2026-10-22 · nhánh `research/scene3d-unified-visual-language` · LOCAL ONLY · phê duyệt thị giác của người: **NOT_GRANTED**.

## 1. Danh tính

| mục | giá trị |
|---|---|
| `main` = `origin/main` (không đổi) | `43247c9e9375a3dbf2b5223324a58e6f932ca596` |
| nguồn chiến dịch (baseline) | `f95596716912e5550ed079287221274b2d70f24c` |
| commit sản phẩm | `36dfccef` (hợp nhất vật liệu) → `24e1a9db` (fallback thiết diện cho polygon3 thiếu metadata) → **`34a57d3540f82a78701b0f0caa8dbae746f266d1`** (thứ tự depth/X-ray theo cùng vai trò) |
| commit bằng chứng | `672e8fc60465becd666e8450af55d2ea852d277c` |
| candidate đóng băng | **`dd3bddd48dad7ff865d7c0442c50b6523d87d3c7`** (`commit` = `672e8fc6`, `product_commit_sha` = `34a57d35`, cây sạch: True) |
| mã đo 114 file | `9bf35a1d6f4c3b3e…` — không đổi vì `backend/app` + miền `semantic` không bị chạm; renderer hình học khoá bằng `product_commit_sha` |
| quản trị | `CACHE_VERSION = 127` · `LLM_ONLY` · `flat` · Hybrid NO-GO · `ALLOW_LIVE_AI=0` · 0 lượt gọi provider |

Phạm vi sản phẩm (non-test) từ baseline: đúng ba file `frontend/src/simulations/domains/geometry/scene3d-roles.ts`, `scene3d-view.tsx`, `frontend/src/styles/tokens.css`. Không đổi backend, toạ độ, tô-pô, phép tính, camera, bộ phân loại khuất/hiện, hợp đồng phản hồi. Bề mặt mô hình (lược đồ, thẻ văn phạm, prompt, bảng năng lực): **không đổi** ⇒ không cần đo lại tuyến LLM.

## 2. Lỗi bộ khảo sát A/B/C và cách xác minh lại

Lỗi: override token của khảo sát có thể chạy sau bước biên dịch TypeScript, vẫn được đếm "đã áp dụng" dù hằng số thật không đổi. Mọi lượt A/B/C trước đó bị đánh dấu trong [`survey-validity.json`](survey-validity.json) (`A/`: INVALIDATED; các nhánh `*-complete`, `survey-A/B/C`, `final`, `final-v2`, `final-v3`: SUPERSEDED). Byte cũ giữ nguyên trên đĩa, kiểm được qua [`superseded-evidence-manifest.json`](superseded-evidence-manifest.json) (1435 file, 297 MiB — không commit vì gấp ~10 lần các run trước; `final-v2/receipt.json` được commit đầy đủ).

Xác minh ở runtime (không chỉ unit test):

- Override chạy trước biến đổi TS, phải áp dụng đúng một lần; B cũng đi qua override (cùng đường build với A/C).
- **Probe runtime**: trang đọc hằng `PHONG_CACH_SCENE3D` sống mà renderer nhập; lượt đo dừng (fail closed) nếu nó ≠ đề xuất. Băm probe: A `122d5360`, C `fe7267d0`, B = final `91d9a368` ⇒ mặc định sản phẩm chính là B, đo được trong trình duyệt.
- **Vật liệu WebGL thật**: 217 check token so màu/độ đục vỏ khối (theo vai trò chính/phụ) và vùng tô thiết diện (`MeshBasicMaterial`) với đề xuất của từng nhánh.
- **Nhánh before**: thay ba file nguồn baseline, mỗi file đúng một lần; `tokens.css` thay tại `@import` của `global.css` (Vite gộp CSS `@import` không qua plugin — đây là lỗi review vòng 3 I1); CSS build phải chứa `--geo3d-vai-tro-dich:#2563eb` của baseline.
- Mọi phiên bản harness đứng sau một receipt đều lưu trong `harness-archive/` và khớp băm (trừ `3636d4ad`, trước phiên này, chỉ sinh nhánh `A/` đã vô hiệu).

## 3. A/B/C — cùng cảnh, hình, camera, viewport

33 cảnh phục vụ + 1 cảnh từ chối, 1440×900, DPR1, Playwright Chromium/SwiftShader, cùng fixture `c6dcd1c8`, cùng harness `c34ec0c6`, cùng nguồn `34a57d35`; camera mặc định = baseline ở dung sai tuyệt đối 1e-9.

| nhánh | đặc điểm token (proposals.json) | ΔRGB trung bình so với before (trung vị / max) |
|---|---|---|
| A Conservative | vỏ xám ấm, tô thiết diện cam đậm 0.28 | 2.376 / 3.964 |
| **B Academic (mặc định)** | vỏ xanh trời 0.18, thiết diện hổ phách nhạt 0.38, viền cam | 1.862 / 3.535 |
| C High Contrast | cạnh đen dày 1.5, thiết diện 0.52, nét khuất đậm hơn | 2.571 / 4.454 |
| final | = B (probe trùng) | 1.862 / 3.533 |

Ảnh đối chiếu before | A | B | C | final cho từng cảnh: [`comparison/`](comparison/). Không có điểm thẩm mỹ nào được suy ra; B là lựa chọn mặc định của kế hoạch, Owner quyết định cuối.

## 4. Hồi quy thị giác (final-r2, `browser-metrics.json`: AUTOMATED_TECHNICAL_PASS, 1542/1542)

- Cạnh hiện/khuất: span cạnh và chữ ký nét đứt ở camera mặc định trùng baseline cho mọi cảnh; chọn đối tượng và X-ray không đổi span; không có visual owner trùng.
- Thiết diện: cùng màu/độ đục/kiểu vật liệu cho polygon, circle, ellipse, polygon3 AUXILIARY_SURFACE và polygon3 thiếu metadata (ví dụ mẫu công khai `public-non-thiet-dien-truc`: trước 24e1a9db tô tím mặt phẳng 0.055; nay hổ phách 0.38, order 7, lộ ra chỉ khi X-ray). Pixel riêng của vùng tô > 0 ở normal hoặc orbit.
- Normal/X-ray: probe tường độc lập 11 + 11 mẫu đạt (Normal chặn, X-ray xuyên).
- Nhiều khối & vai trò: ẩn / chỉ xem phần này / bước lùi / đảo thứ tự trên `family07`, `family10`, `family05` — vai trò chính/phụ và màu không đổi.
- Chọn: id được chọn khác null, vật liệu nhấn mạnh khác trạng thái trung tính; Mode A không mở bảng đáp án.
- Khung camera & bảng: chồng lấn panel = 0 ở 33 trạng thái desktop và 66 trạng thái 1024×768 / 820×640.
- Nhãn: cỡ chữ ≥ 12 px, không phát sinh va chạm nhãn mới; tương phản nền: UNKNOWN.
- CSS: 0 biến chưa định nghĩa; 0 ngoại lệ bảng màu theo id cảnh/họ.
- Hiệu năng (SwiftShader, không phải FPS thiết bị thật): occlusion p50 5.3 ms / p95 13.9 ms (751 mẫu); orbit lặp: 0 cấp phát vật liệu.

## 5. Sửa đổi điều chỉnh SAU khi quan sát (công khai)

1. **Reset camera**: so tương đối 1e-9 thay vì tuyệt đối. Hai cảnh (`regular-hexagonal-pyramid-hex`, `regular-prisms-6`) lệch ~4e-9 trên |x|≈10 (~4e-10 tương đối), trùng bit trong nhánh development; diff sản phẩm không chạm camera. Kết quả tuyệt đối vẫn lưu ở `camera_reset_observations`.
2. **Orbit lặp**: `final-v2` một lần ghi `[3,0]` cấp phát ở `family07_multi_solid_composition` (warmup 0). Check đổi từ `[0,0]` tuyệt đối sang "cấp phát = tăng trưởng pool" (không cấp phát lại kiểu đã gặp), giữ kết quả tuyệt đối làm quan sát. Lượt có đo pool (`final-v3`, `final-r2`) toàn 0 ⇒ `[3,0]` **không tái hiện, nguyên nhân chưa xác minh** ("kiểu nét khuất gặp lần đầu do camera trôi" chỉ là giả thuyết). Check chứng minh không cấp phát lại, không chứng minh khoá giới hạn (khoá chứa độ mờ/chu kỳ nét).

## 6. Review độc lập

Vòng 1–2 (trước phiên này), [vòng 3](review-round3.md) (2 Important: I1 CSS before no-op, I2 polygon3 thiếu metadata — đã sửa), [vòng 4](review-round4.md) (0 Critical/Important; M-a sửa ở `34a57d35`, M-b công khai), [vòng 5](review-round5.md) (0 Critical/Important trên `34a57d35`). `expected_roles`/`is_section` trong validate.py là phát biểu lại luật sản phẩm, chứng minh token tới đúng đối tượng chứ không chứng minh luật đúng.

## 7. Kiểm thử

- Focused (vitest geometry/styles/components): 60 file, 1064 test pass tại `34a57d35`; test mới đỏ trước sửa (`[legacy, 0xd6b6f6, 0.055]`, rồi `[legacy, 0, true, true]`) và xanh sau sửa.
- Docs gate: 41 pass; `test_inv_20` đỏ trước khi đóng băng (candidate cũ) — đóng băng lại ở `dd3bddd4`.
- **Authoritative Full T3** ([`t3-attempt2/`](t3-attempt2/execution.json)) trên candidate `dd3bddd4` trong worktree detached sạch: **`FULL_PRODUCT_GATE_PASS`**, 570.3 s — pytest 11 442 passed (1 skipped, 2 deselected, 9 xfailed), vitest 76 file / 1192 test, `tsc -b && vite build` PASS, demo khoá luận 5/5, bề mặt sập 6/6; cây sạch trước và sau. Lượt 1 ([`t3/`](t3/invocation.json)) bị ngắt khi phiên Claude trước kết thúc ở ~91% pytest backend, không có `execution.json` ⇒ không có kết quả, byte giữ nguyên.
- **Freeze sau T3** ([`post-t3-freeze/`](post-t3-freeze/execution.json)): `MATCH` (114 file, `9bf35a1d…`). Đối chiếu danh tính ở [`validation.json`](validation.json): 15/15 (candidate = HEAD của T3 và freeze, `commit` = `672e8fc6`, `product_commit_sha` = `34a57d35` là tổ tiên và không có thay đổi sản phẩm sau nó, băm stdout/stderr khớp receipt, nhánh trình duyệt final đo đúng `34a57d35`).

## 8. Giới hạn còn lại

- M-b: polygon3 thiếu metadata có `parent` (mặt khối trong envelope cũ, ví dụ `scene3d-circumsphere-fixture.json`, lịch sử localStorage) nay hiển thị như thiết diện (màu, order 7, lộ khi X-ray) dù backend sẽ gắn BASE_REGION; trước chiến dịch cũng hổ phách. Sửa đúng cần luật tô-pô cạnh của backend ở frontend — backlog.
- Ảnh cảnh cong (trụ/nón) không lặp lại bit-chính-xác giữa hai lần chụp cùng trạng thái (tối đa ~1290 px, có từ trước); vật liệu và span cạnh trùng.
- Cảnh offline không chứng minh E2E NLU sống; SwiftShader không chứng minh FPS thiết bị; tương phản nhãn trên mọi nền: UNKNOWN.
- Không có chấm điểm thẩm mỹ tự động; **phê duyệt thị giác thuộc Owner**.
