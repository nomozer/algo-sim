# Skill đã dùng thật trong W05 (và áp dụng ở đâu)

| Skill | Dùng để | Kết quả áp vào sản phẩm |
|---|---|---|
| UI UX Pro Max (`search.py --domain ux`: "dropdown menu keyboard escape focus", "back navigation predictable") | ưu tiên hành động, menu, điều hướng | vòng tiêu điểm thấy được trên mọi nút/mục menu; Escape đóng và trả tiêu điểm; quay lại dự đoán được (về đúng trang trước, chữ là tên trang đích); vùng chạm 44 px khi `pointer: coarse`/khổ hẹp; không cuộn ngang. Kết quả "Back Button · history.pushState" KHÔNG áp: ứng dụng không có route URL (điều hướng là `view` của store) — thêm lịch sử trình duyệt là ngoài phạm vi, ghi ở báo cáo. |
| Impeccable (chế độ Operate, tinh chỉnh bề mặt có sẵn; `PRODUCT.md` không có, không tạo) | rõ ràng, nhất quán, bỏ thừa | một hệ duy nhất: menu chỉ là lối vào, bảng vẫn là `BangNoi` W4; bỏ thẻ lặp và nút giả («Giải thích» trong 3D, «Tách khối» vô hiệu); token DESIGN.md (một màu nhấn, nút tiện ích bo 8 px, hairline), không thêm màu/bóng mới; biểu tượng SVG dùng chung (`IconCheck`, `IconChevronDown`, `IconBack`), không ký tự Unicode. |
| Superpowers — systematic-debugging | lỗi mobile của đầu dò W5 | gốc: hộp menu `right: 0` neo vào nút ở cột trái ⇒ tràn mép trái và mục «Toàn màn hình» nằm ngoài khung (cú bấm trượt); sửa ở CSS khổ hẹp (neo vào cả hàng nút), không nới ngưỡng. |
| Superpowers — test-driven-development | backend + frontend | test đỏ trước sản phẩm: `RED_CHAIN_READER.log` (11 đỏ), `scene3d-focus-mode.test.tsx` (đỏ vì module/hành vi chưa có); `assessFocusMode` có ca tiêm lỗi từng lý do. |
| Superpowers — verification-before-completion | kết luận | chỉ kết luận từ cổng đã chạy (pytest, vitest, build, node harness, đầu dò, T3 trong worktree sạch). |
| Karpathy Guidelines | phạm vi | thay đổi tối thiểu: không viết lại backend, không route song song; menu là một component nhỏ dùng lại `BangNoi`. |
| Ponytail | rà diff trước nghiệm thu | `PONYTAIL_REVIEW.md`. |

Không dùng hai skill thiết kế để tạo hai hệ UI: UI UX Pro Max chỉ cho luật tương tác/khả năng tiếp cận; hình thức theo DESIGN.md + Impeccable (tinh chỉnh).
