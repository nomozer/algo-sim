# SCENE3D_CAMERA_FRAMING_REPORT (`AXO HYBRID /12` P7 §18 — `V11-VIS-1`)

## 1. Nguyên nhân Gốc (`V11-VIS-1`)

1. Trong `frontend/src/simulations/domains/geometry/scene3d-view.tsx`, `cam.setViewOffset(w, h, -lechOngKinhNgang * (w * 0.5), lechOngKinhDoc * (h * 0.5), w, h)` làm dịch chuyển tọa độ NDC chiếu trên màn hình thêm `(+dichTamNgang, +dichTamDoc)` (đến `+0.32` theo chiều dọc khi thanh điều khiển dưới đáy xuất hiện và dịch ngang theo panel phải).
2. Hàm `vungAnToanTuTuyChon` trước `/12` tính `[xMin, xMax] × [yMin, yMax]` thuần theo `tc.tiLeNgang / tc.tiLeDoc` mà **không trừ đi phần dịch chuyển `dichTamNgang / dichTamDoc` và khoảng đệm pixel cho nhãn đỉnh**, khiến đỉnh trên cao (vd `S07`, `Q01`, chóp cao `SA = 6`) có thể chạm hoặc vượt rìa trên/trái khung canvas ngay ở khung hình đầu tiên trước khi người dùng orbit/reset.
3. Hàm `tinhViTriNhanDiem` chấm điểm và đặt góc nhãn đỉnh `(lx, ly)` mà không phạt hoặc kẹp (clamp) theo biên pixel thực `[pad, w - pad] × [pad, h - pad]`.

## 2. Sửa đổi Triển khai

- `frontend/src/simulations/domains/geometry/scene3d-view.tsx`:
  - Xuất hàm thuần `tinhVungAnToanKhungNhin(tc, w, h)` (gọi bởi `vungAnToanTuTuyChon`): trừ phần dịch thấu kính `(dichTamNgang, dichTamDoc)` khỏi cận an toàn trên màn hình và chừa lề pixel theo kích thước khung (`padX`, `padTop`, `padBot`), giữ nguyên an toàn tối thiểu `±0.18`.
  - Mở rộng `tinhViTriNhanDiem(..., khung?: { w: number; h: number; pad?: number })`: cộng hình phạt mạnh (`180 + over * 10`) khi hộp nhãn tràn biên để tự xoay hướng nhãn vào trong canvas, và kẹp `(bestLx, bestLy)` trong `[pad, w - pad - cw] × [pad, h - pad - ch]`; truyền `{ w, h, pad: 8 }` tại `chieuNhan`.
- `frontend/src/simulations/domains/geometry/scene3d-v12-camera-framing.test.ts`:
  - Kiểm chứng toán học phép chiếu `THREE.PerspectiveCamera + setViewOffset + khungNhinQuanhTam + tinhVungAnToanKhungNhin` và kẹp nhãn `tinhViTriNhanDiem` trên cả 4 kích thước (`1920x1080`, `1366x768`, `768x1024`, `390x844`).

## 3. Kết quả Kiểm chứng Thực nghiệm

1. **Vitest (`frontend`):** `npx vitest run` — **146/146 files, 2077/2077 tests PASSED** (gồm `scene3d-v12-camera-framing.test.ts` và `transition-semantics.test.ts`; `tokens.css` & `transition-semantics.test.ts` giữ `0` diff).
2. **Playwright Chromium trên `vite preview` + backend cục bộ (khung hình ban đầu TRƯỚC khi reset/orbit, và sau kéo chuột orbit):**

| Viewport | Canvas `(w×h)` | Case | Đỉnh thiếu ban đầu | Nhãn tràn biên ban đầu | Nhãn tràn biên sau orbit | Lề nhỏ nhất ban đầu (px) | Kết quả |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1920x1080` | `1560×1034` | `S07` | `[]` | `[]` | `[]` | `167` | PASS |
| `1920x1080` | `1560×1034` | `Q01` | `[]` | `[]` | `[]` | `134` | PASS |
| `1920x1080` | `1560×1034` | `S09_ELONGATED` (`SA=6`) | `[]` | `[]` | `[]` | `140` | PASS |
| `1366x768` | `1006×722` | `S07` | `[]` | `[]` | `[]` | `111` | PASS |
| `1366x768` | `1006×722` | `Q01` | `[]` | `[]` | `[]` | `85` | PASS |
| `1366x768` | `1006×722` | `S09_ELONGATED` (`SA=6`) | `[]` | `[]` | `[]` | `89` | PASS |
| `768x1024` | `472×978` | `S07` | `[]` | `[]` | `[]` | `19` | PASS |
| `768x1024` | `472×978` | `Q01` | `[]` | `[]` | `[]` | `23` | PASS |
| `768x1024` | `472×978` | `S09_ELONGATED` (`SA=6`) | `[]` | `[]` | `[]` | `28` | PASS |
| `390x844` | `390×438` | `S07` | `[]` | `[]` | `[]` | `15` | PASS |
| `390x844` | `390×438` | `Q01` | `[]` | `[]` | `[]` | `15` | PASS |
| `390x844` | `390×438` | `S09_ELONGATED` (`SA=6`) | `[]` | `[]` | `[]` | `9` | PASS |
