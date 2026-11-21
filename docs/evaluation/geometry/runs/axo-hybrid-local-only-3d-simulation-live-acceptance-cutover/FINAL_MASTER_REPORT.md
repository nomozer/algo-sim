# AXO HYBRID /10 — Local-only 3D simulation live acceptance & controlled cutover

Run `axo-hybrid-local-only-3d-simulation-live-acceptance-cutover` · 2026-11-19 · nhánh `integration/local-only-3d-live-acceptance`
(từ `38c6efbdb`), commit sản phẩm cuối `a0f979392` (cây đo `ce3e3c4b…`, 123 file), `CACHE_VERSION 145`. Không merge, không push,
`main` không đổi, mặc định `HYBRID_ROUTE_MODE=live` không đổi.

## Kết luận

**`FULL_STACK_LOCAL_ONLY_VERIFIED` = TRUE · `LIVE_SIMULATION_ACCEPTED` = FALSE · `SCOPED_CUTOVER_READY` = FALSE ·
`SCOPED_CUTOVER_COMPLETED` = FALSE.**

Axo chạy được trọn vòng không khoá Gemini: trình duyệt thật → backend thật → llama.cpp + AxoV9 thật → Scene3D hiển thị và tương tác.
Mọi thứ được phục vụ đều đúng (40/40 cảnh, 252 quan hệ, 0 vi phạm; 26/26 đáp số; 0 egress). Nhưng hệ chỉ hoàn tất 62.5% đề hợp lệ
(ngưỡng đăng ký trước 85%), và **mọi cảnh phục vụ đến từ parser tất định — đường SLM phục vụ 0/20**. Run tìm và sửa một lỗi runtime
nghiêm trọng mà benchmark backend /9 không thấy (keep-alive: cứ sau > 5 s nghỉ là một lượt SLM 503).

## Đã làm

| Pha | Kết quả |
|---|---|
| P0 | Danh tính /9 xác minh bằng mã, git, `--verify`, sha256 model, `llama-server --version`; owner quyết quyền: frontend trên nhánh tích hợp, giữ mặc định, không sửa planner/registry/typed facts |
| P1–P2 | Kiểm toán hợp đồng từ đường thực thi thật; ba chế độ A/B/C đo trên trình duyệt |
| P3 | Frontend keyless tích hợp thật (`e10697092`): bản vá /9 kiểm lại + thông điệp 503 cục bộ + test có nền đỏ |
| P4–P6 | 64 + 18 ca đóng băng (`451a59040`), 2 lượt trình duyệt đầy đủ + 15 ca chạy lại, oracle hình học độc lập, 16 kịch bản UI/runtime |
| P7 | Bằng chứng mạng 4 lớp có cửa sổ chứng; 6 kịch bản lỗi runtime; fix keep-alive `7554e2b72` + đóng băng lại `a0f979392` |
| P8 | Rehearsal staging bằng biến môi trường; rollback model hai chiều, cấu hình, mã |
| P9 | T3 `FULL_PRODUCT_GATE_PASS` tại `28badc70b` (pytest 15 102 passed, vitest 2066, build, demo) — lần chạy đầu đỏ 2 test do template chờ owner ghim candidate cũ, đã gắn lại bằng thủ tục có sẵn |
| P10 | `PRODUCTION_CUTOVER_DECISION.md` |

## 30 câu hỏi nghiệm thu

1. **Mô phỏng không cần câu hỏi tính toán?** Có. `TypedFactNext /2` là simulation-first (`construct_object`, `math_goals` tuỳ chọn); 14 ca chỉ-mô-phỏng được phục vụ với `answers={}`.
2. **Giới hạn ở đâu?** Không ở hợp đồng mà ở độ phủ câu lệnh mô phỏng của parser tất định (luật 7b chỉ nhận "mô phỏng/vẽ hình (chóp|lăng trụ)") và việc SLM không vượt Source Gate cho mục tiêu dựng (11/28 ca A).
3. **Hình minh hoạ khi không xác định duy nhất?** Có cho một số đại lượng hỏi đã chứng minh bất biến (`*_ILLUSTRATIVE` + chứng chỉ, công khai trong `scene_configuration`). **Không** cho đề chỉ-mô-phỏng thiếu kích thước — hệ từ chối và (ở backend) hỏi làm rõ.
4. **Model 1 trích xuất đúng quan hệ?** Trên bộ này không có bằng chứng tích cực: 0/20 đề đi đường SLM được phục vụ (các đề đều bị Source Gate chặn — an toàn). Không ca SLM nào phục vụ sai.
5. **Exact Kernel xác minh toàn bộ ràng buộc dùng để dựng?** Mọi cảnh phục vụ thoả toàn bộ 252 quan hệ gold theo oracle độc lập (Fraction, Gram metric); không thấy quan hệ nào chỉ được "giả định".
6. **Scene3D thật từ kết quả Local AI?** Từ pipeline local thật, nhưng phần "hiểu đề" của 40/40 cảnh là parser tất định, không phải LLM.
7. **Hình trên màn hình đúng dữ kiện?** Có: 40/40 đạt tiêu chí hiển thị, nhãn đỉnh đúng tập gold và nằm trong canvas; đã xem trực tiếp ảnh mẫu.
8. **Sai toạ độ/cạnh/mặt/quan hệ?** Không (Euler, mặt phẳng, không suy biến, không tham chiếu treo, 0 vi phạm). Phát hiện phụ: điểm bố trí `O` (đúng là tâm đáy) gắn nhóm `given`.
9. **Xoay/phóng to được?** Có: 159/160 thao tác; thất bại duy nhất là xoay V17 bắt đầu từ tâm canvas (chưa rõ nguyên nhân; xoay từ vùng trống đạt).
10. **Tương tác đổi hình học gốc?** Không: tập nhãn giữ nguyên, 0 lượt `/api/analyze` trong khi tương tác.
11. **Thay đề có giữ hình cũ?** Không (U02, U03, U04).
12. **Bước dựng hiện có đúng?** Có (prev/next/phát; bước tích luỹ). Construction /2 `NOT_IN_PRODUCT`.
13. **Đúng đáp số nhưng mô phỏng sai?** 0 ca.
14. **Mô phỏng đúng nhưng thiếu dữ kiện tính?** Hệ không phục vụ riêng phần hình: N02/N14 từ chối toàn bộ (`MISSING_DIMENSION`); C20 (góc xác định tới đồng dạng) cũng bị từ chối.
15. **Đã bỏ cảnh báo thiếu khoá Gemini ở UI local-only?** Có trên nhánh tích hợp: 0/179 lượt hiện chữ khoá đám mây; thiếu model hiện "Bộ đọc đề trên máy chưa sẵn sàng".
16. **Hoạt động khi không gọi AI cloud?** Có — mọi lượt chạy với 0 lời gọi provider.
17. **Bằng chứng runtime network isolation?** Có: proxy egress (0 bản ghi), bảng TCP tiến trình (0), request trình duyệt (0), telemetry route (0); hai bộ đo có cửa sổ chứng.
18. **Cần Internet sau khi cài?** Không quan sát thấy phụ thuộc nào được dùng và `dist/` không tham chiếu tài nguyên ngoài; **chưa** thử ngắt mạng thật ⇒ `FULLY_OFFLINE_RUNTIME` không tuyên bố.
19. **Model chạy trên thiết bị nào?** Trên máy chạy backend (llama-server cạnh backend); ở run này là máy dev Windows 11, 15.78 GiB, CPU 6 luồng. Không phải trên máy của mọi học sinh.
20. **Thời gian thấy hình?** Lượt 2: first visible scene p50 256 ms, p95 456 ms (40 cảnh, đều đường tất định); khởi động lạnh 1455 ms. Lượt 1 (lỗi keep-alive) p95 8827 ms.
21. **Thời gian tới khi tương tác được?** p50 1114 ms, p95 1341 ms (gồm ~0.5 s chờ của harness).
22. **CPU/RAM toàn ứng dụng?** Trong một phiên trình duyệt: backend ≤ 116 MB WS, llama-server ≤ 903 MB, Chromium headless ≤ 500 MB; tổng đồng thời ≤ 1519 MB. CPU toàn máy suốt lượt 2: trung bình 37%, p95 88% (máy dev đang chạy nhiều thứ khác). Chi tiết `FULL_STACK_MEMORY_REPORT.md`.
23. **Máy 4–8 GiB đã thử thật?** Chưa (`NOT_MEASURED`).
24. **Đề vẫn ngoài khả năng?** Cầu/nón/trụ, Oxyz, phẳng thuần, giải tích, lập trình (từ chối đúng); trong miền: câu lệnh mô phỏng ngoài mẫu 7b, "biểu diễn …", đề không dấu, "tất cả các cạnh đều bằng", tiêu đề đề thi "Câu 2 (2 điểm)." (`SOURCE_PREMISE_UNREAD`), đề thiếu kích thước, góc không cho cạnh.
25. **Lỗi C60 / unseen /9 ảnh hưởng Scene3D thật?** Có cùng lớp: các ca hỏng ở /9 là lỗi đọc đề (không phục vụ), và trên sản phẩm thật chúng hiện thành từ chối an toàn — không thành cảnh sai. Đường SLM không đóng góp cảnh nào trong bộ này.
26. **Frontend tích hợp thật hay chỉ patch?** Tích hợp thật trên nhánh tích hợp (build + test + trình duyệt); chưa vào `main`.
27. **Mặc định đã chuyển local-only?** Chưa (owner quyết định giữ `live`; xác nhận bằng chạy thật).
28. **Rollback chạy thử thật?** Có: model v9→v7→v9 (llama-server nạp đúng file v7), cấu hình về `live`, mã về candidate /9 (lượt 1).
29. **Lỗi an toàn toán học chưa giải quyết?** Không có lỗi an toàn toán học nào quan sát được. Các vấn đề mở là độ phủ và UX.
30. **Đủ điều kiện nghiệm thu local-only scoped?** Chưa: an toàn đạt, nhưng completion 0.625 < 0.85 và interaction 159/160 < 1.0 (ngưỡng đăng ký trước).

## Mức chứng cứ — không đánh đồng

| Mức | Đạt? |
|---|---|
| `BACKEND_VERIFIED` | Có |
| `SCENE3D_RENDER_VERIFIED` | Có (40/40 trên trình duyệt thật) |
| `LIVE_PRODUCT_ACCEPTED` | **Chưa** |

## Giới hạn của chính run này

- Bộ đề do agent viết (`AUTHOR_CONSTRUCTED`), không độc lập. Lượt 2 không còn mù (tác giả đã thấy lượt 1).
- Oracle được sửa sau lượt 1 (v2: định dạng `cos²`, điểm tâm đáy, kiểu đối tượng) — output v1 giữ nguyên; mỗi sửa đổi kiểm tay.
- Kịch bản UI do run tự đặt ngưỡng (U08 ≤ 2 px, U16 ≥ 30%), không nằm trong bản đóng băng.
- Không tiêm được timeout (45 s cố định trong mã); hành vi timeout lấy từ quan sát tự nhiên ở lượt 1.
- CSV tài nguyên ghi số có dấu nghìn — đã phân tích lại có kiểm (685/686 dòng).

Chi tiết: `LIVE_ACCEPTANCE_GATE_SUMMARY.md`, `PRODUCTION_CUTOVER_DECISION.md`, `OWNER_HANDOFF.md`.
