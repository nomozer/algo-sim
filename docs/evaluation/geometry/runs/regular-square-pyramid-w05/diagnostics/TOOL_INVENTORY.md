# Kiểm kê công cụ của xưởng 3D — trước khi sửa (đọc ở `73bc404e`)

Nguồn: `frontend/src/App.tsx`, `components/SimulationWorkspace.tsx`, `simulations/domains/geometry/Scene3DExplorer.tsx`,
`scene3d-playback.tsx`, `scene3d-solution.tsx`. "Sau W05" là nơi công cụ ở sau lượt này.

| Công cụ (trước) | Nơi | Chức năng thật | Sau W05 |
|---|---|---|---|
| Wordmark «AlgoSim» / TopNav (Mô phỏng mới, Bài thực hành, Lớp, Thư viện, Lịch sử) | `nav-bar` toàn cục | điều hướng trang | **không dựng** trong cảnh 3D; đường ra = nút quay lại (về đúng trang trước), từ đó có lại TopNav |
| «Đăng nhập» / «Đăng ký» (khách) | `nav-bar` | mở `AuthGate` | không dựng trong cảnh 3D (brief C) — vẫn ở mọi trang khác |
| Nhãn «Bài: …» (bài được giao) | `nav-bar` | cho học sinh biết đang làm bài giao | hàng trên của xưởng (`daiLop`) |
| «Giao cho lớp» (`AssignDialog`, giáo viên) | `nav-bar` | giao đúng mô phỏng đang xem | hàng trên của xưởng (`daiLop`) |
| «+ Mô phỏng mới» | `nav-bar` | `goHome` | không lặp trong xưởng: nút quay lại → trang trước (TopNav có «Mô phỏng mới») |
| «Giải thích» (`toggleRight`) | `nav-bar` | bật cột Giải thích của đường **2D** | **không tác dụng với cảnh 3D** (`Scene3DExplorer` không đọc `rightOpen`) — công cụ giả, không dựng trong chế độ tập trung |
| Tài khoản / đăng xuất (`TopNavAccount`) | `nav-bar` | trang tài khoản, đăng xuất | ở mọi trang khác (sau khi quay lại) |
| Dải lớp (`LiveClassStrip`) | hàng trên xưởng | chỉ báo / dock giáo viên | giữ ở hàng trên |
| «Hình dựng theo từng bước» | hàng trên xưởng | nhãn tĩnh | thay bằng **tên bài** (`h1`) |
| Chip «Xem đề» | hàng trên | mở bảng Đề bài (`BangNoi de`) | nút chính «Đề bài» |
| Chip «Thành phần» | hàng trên | mở cây (`BangNoi thanh-phan`) | menu «Khám phá» |
| Chip «Đại lượng» (khi có đại lượng) | hàng trên | mở danh sách đại lượng (`BangNoi dai-luong`) | menu «Khám phá» |
| Chip «Hiện tất cả» (khi có nhãn mặc định ẩn) | hàng trên | mọi số đo khả dụng lên hình | menu «Hiển thị» (mục công tắc) |
| Chip «Hình phụ» (khi cảnh có hình phụ) | hàng trên | hiện đường/mặt phụ đã xong việc | menu «Hiển thị» |
| Chip «Lưới» | hàng trên | lưới nền | menu «Hiển thị» («Lưới nền») |
| Chip «Chi tiết» | hàng trên | ô soi thêm «Dựa trên» (phụ thuộc hình học) + «Giả thiết» | **còn chức năng riêng** ⇒ menu «Thêm» («Cách máy dựng»), không còn thường trực |
| Nút nổi «Tách khối»/«Ráp lại» | góc canvas | bung các mặt | giữ; **chỉ dựng khi cảnh có mặt** (trước: nút vô hiệu thường trực) |
| Nút nổi «Xem lại toàn hình» | góc canvas | bỏ chọn/cô lập + đặt lại camera | giữ ở chỗ dễ thấy |
| Ô soi (chọn vật) | `BangNoi soi` | chi tiết vật đang chọn: vai trò, công thức, nguồn số, thao tác cô lập/ẩn | giữ; **luôn mang công thức** (nhánh "lời giải đang mở" gỡ) |
| Trình phát: Bước trước · Phát/Tạm dừng/Xem lại · Bước sau · thanh tua «Bước n/N» · «Các bước dựng» | dưới canvas | thời gian dựng | giữ nguyên |
| Thẻ lời giải (`Scene3DSolution`): «Xem lời giải đầy đủ», Kết quả / Dữ kiện / Các bước tính, «Dựa trên», chú giải màu | dưới thanh phát | lặp đúng tập `quantityChoices` của «Đại lượng»; công thức + nguồn có ở ô soi | **gỡ**; mục «Đại lượng» mang nhãn backend + `ký hiệu = giá trị` + vai trò chuỗi nhân quả; chú giải màu vào menu «Hiển thị» |
| (mới) Toàn màn hình | — | — | menu «Thêm», chỉ khi `document.fullscreenEnabled`; chế độ tập trung không phụ thuộc nó |
