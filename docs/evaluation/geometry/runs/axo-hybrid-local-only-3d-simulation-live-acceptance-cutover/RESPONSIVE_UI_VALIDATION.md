# Giao diện đáp ứng (P6 · Phase H)

Đề C09 (khoảng cách A → (SBD)) gửi qua UI thật ở bốn viewport; mỗi viewport một phiên mới. Nguồn: `evidence/ui4/ui_scenarios.json`,
ảnh `evidence/ui4/screenshots/U16_*.png`.

| Viewport | Khung nhập | Canvas (w×h) | Tỉ lệ canvas / viewport | Tràn ngang | Nhãn trong canvas | Kết quả |
|---|---|---|---|---|---|---|
| 1920×1080 | hiện | 1560×1034 | 0.78 | không | có | PASS |
| 1366×768 | hiện | 1006×722 | 0.69 | không | có | PASS |
| 768×1024 | hiện | 472×978 | 0.59 | không | có | PASS |
| 390×844 | hiện | 390×438 | 0.52 | không | có | PASS |

Quan sát trực tiếp ảnh: canvas 3D là vùng chính (trái ở desktop/tablet, trên ở mobile); "Đề bài", "Các bước dựng", chip đối tượng
nằm ở bảng bổ trợ, không che mô hình; thanh bước và thanh công cụ 3D nằm trong canvas, không đè nhãn đỉnh. Ở 768×1024 khối sát
mép trái (đỉnh B ≈ 35 px) nhưng vẫn trong canvas. Trạng thái loading ("Đang dựng hình…" + nút Huỷ) và toast lỗi đã quan sát ở
1366×768 (`evidence/browser/screenshots/acceptance_V02.png`, `pass2_*`). Không thiết kế lại UI.

Ngưỡng "canvas ≥ 30% viewport" do run đặt cho kịch bản này (không có trong bản đóng băng).
