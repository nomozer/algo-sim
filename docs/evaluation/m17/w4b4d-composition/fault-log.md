# W4B-4D — Nhật ký tiêm lỗi (mutation log)

Kỷ luật: một guard chưa từng ĐỎ là một guard chưa được chứng minh. Mỗi dòng dưới
đây là một đột biến tiêm vào mã sản phẩm (hoặc phép đo), chạy trọn `vitest run`,
rồi khôi phục nguyên trạng. Suite nền: **1276 test / 92 file, xanh** trước và
sau toàn bộ đợt tiêm.

⚠️ Đợt chạy ĐẦU của batch này vô giá trị: runner gọi vitest qua
`subprocess.run(["npx.cmd", ...])` làm **cả 92 file fail lúc collect** — mọi
fault đều "ĐỎ" nhưng là đỏ của harness, không phải của guard. Bằng chứng: lượt
đối chứng KHÔNG tiêm gì cũng đỏ y hệt. Toàn bộ kết quả dưới đây là của đợt chạy
lại bằng bash (baseline xanh đã xác nhận trước khi tiêm).

| # | Đột biến | Kết quả | Guard bắt |
|---|---|---|---|
| F1 | web: `selected` bị nuốt — bấm chọn khối thành trang trí | ĐỎ | `direct-manipulation-w4b4d` |
| F2 | web: `htmlTextOf` in thứ tự VIẾT CỨNG, không theo `state.order` | ĐỎ | `direct-manipulation-w4b4d` (hai bản chiếu lệch) |
| F3 | web: Về-ban-đầu chỉ trả kiểu, bỏ quên cấu trúc | ĐỎ | `direct-manipulation-w4b4d` |
| F4 | web: `selectNode` nhận mọi tên (miền mở) | ĐỎ | `direct-manipulation-w4b4d` (fail-closed) |
| F5 | logic: SVG quay lại `width="100%"` — cha `fit-content` bóp về 300px | ĐỎ | `dag.test` (bề rộng riêng) |
| F6 | logic: `PAD=0` — khung nét đứt cổng đầu ra bị viewBox cắt | ĐỎ | `ui-clarity-w1` (viewBox 694) |
| F7 | logic: câu hướng dẫn viết cứng "A, B" | ĐỎ | `dag.test` (dẫn xuất từ config) |
| F8 | algorithm: ngưỡng ngoài miền bị **KẸP** thay vì từ chối | **XANH → LỖ THẬT** | vá bằng `condition-param.test.ts`, tiêm lại: ĐỎ (3 test) |
| F9 | shell: `specDrift` so bằng THAM CHIẾU — nhãn kêu vĩnh viễn | ĐỎ | `spec-drift-w4b4d` |
| F10 | catalog: đổi `id` của một mẫu | XANH — đột biến VÔ HẠI thật (simId đọc từ envelope, không từ id) |
| F10′ | catalog: **gỡ hẳn** một target khỏi `offlineCatalog()` | **XANH → LỖ THẬT** | vá bằng phép so registry-phủ-toàn-bộ trong `experience-audit-w4b4a`, tiêm lại: ĐỎ |
| F11 | probe: đọc lại cờ KHAI BÁO thay vì CỬA thật | XANH — **mutant tương đương hôm nay**: hai phép đo trùng nhau trên mọi target hiện có. Sự phân biệt đã chứng minh hai chiều lúc dựng (gỡ `exploreLabel` của `count_if` ⇒ guard cửa-thật đỏ, guard khai-báo thì không). Chấp nhận, có ghi lại. |

Ngoài batch: F12 (quyết định tương tác theo `config.notes`) đã tiêm ở lượt
trước — lọt qua scanner chỉ quét `summary|title`, vá bằng nới pattern sang
`notes|description` + mồi hai chiều trong `spec-reuse.test.tsx`, tiêm lại: ĐỎ.

Hai lỗ F8/F10′ nói cùng một điều với các wave trước: chỗ hỏng không nằm ở
guard sai mà ở **luật chỉ sống trong comment** (từ-chối-không-kẹp) và **sàn đo
quá thấp** (`rows.length > 10` nuốt mất một target biến mất).
