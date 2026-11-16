# CACHE_SEMANTIC_INTEGRITY_REPORT — Kiểm Toán Tính Toàn Vẹn Cache & Nâng `CACHE_VERSION` (`141 -> 142`)

- **Run ID:** `planner-autonomous-composition-and-search-efficiency`
- **Cache Policy mới:** `CACHE_VERSION = "142"` · `ROUTE_D_CACHE_POLICY = "142:route-d"`
- **Lock File:** [`backend/cache_identity.lock.json`](../../../../backend/cache_identity.lock.json) (`semantic_environment_hash = "6233c43c395c9b493d31d3dbb5d0ca952604730f6185cf541d2f179c077f955b"`)

---

## 1. Vì Sao Bắt Buộc Nâng `CACHE_VERSION` Từ `141` Lên `142`

Khóa cache runtime của `/api/analyze` (`SimulationCache`) được tính **trước khi chạy Planner và Engine**, chỉ phụ thuộc văn bản chuẩn hóa, định danh mô hình và chuỗi phiên bản (`ROUTE_D_CACHE_POLICY`), không kiểm định lại nội dung `envelope_json` khi đọc ra từ SQLite (`test_cache_semantic_guard_invalidation.py`):

1. **Thay đổi thực chất đồ thị `Scene3D` trên chuỗi phụ anh em (`T1` / `E1`):**
   - Dưới `141:route-d`, các đề kiểu đoạn thẳng/góc đường thẳng Euler giữa `@orthocenter(SBD)` và `@circumcenter(SBD)` phát sinh **`10`** bước dựng phụ bao gồm một điểm **`H4` trùng tọa độ với `H`** trong `Scene3D`.
   - Dưới thay đổi `_pending` & `_emit` của chiến dịch này, các đề đó còn **`8`** bước dựng phụ (`reused_intermediates = 2`), **`0` điểm trùng tọa độ** và **không có `H4`** trong `Scene3D`. Nếu giữ `141`, bộ đệm cũ sẽ tiếp tục phục vụ lại `Scene3D` có điểm trùng thừa `H4`.
2. **Mở rộng ngữ nghĩa được phục vụ (`ask_distance_lines`, `intersect_line_line`, cross-rule reuse):**
   - Các câu đề hai đường thẳng dẫn xuất hay giao hai đường dẫn xuất không có chữ `"hai"` trước đây từng trả về từ chối hoặc thiếu cầu nối dựng, nay có thể phục vụ hợp lệ (`SERVED` kèm `Scene3D` đầy đủ).

Vì hai lý do trên, nâng `CACHE_VERSION = "142"` là **bắt buộc** để vô hiệu hóa toàn bộ hàng `141:route-d` cũ trên `/api/analyze`.

---

## 2. Kiểm Chứng Khóa Danh Tính & Vô Hiệu Hóa Hàng Cũ Trong SQLite

1. **`backend/scripts/lock_cache_identity.py` & `backend/tests/test_cache_identity.py`:**
   - Cập nhật `backend/cache_identity.lock.json` đồng bộ với `CACHE_VERSION = "142"`; `lock_cache_identity.py --verify` trả mã thoát `0` (`Khoá khớp · CACHE_VERSION 142 · môi trường 6233c43c395c9b49...`).
   - Toàn bộ 20 file test khóa phiên bản `CACHE_VERSION` (bao gồm `test_cache_*_invalidation.py` và `test_api.py`) đồng bộ sang `"142" / "142:route-d"`.
2. **Kiểm chứng vô hiệu hóa qua endpoint thật `POST /api/analyze` (`test_planner_autonomous_composition.py`):**
   - Bơm trực tiếp một bản ghi `SimulationCache` giả lập phiên bản cũ `policy_version = "141:route-d"` chứa dấu vết `STALE_H4_MARKER` và 10 lời gọi cho đúng khóa văn bản `T1`.
   - Gửi `POST /api/analyze` dưới chế độ `HYBRID_ROUTE_MODE = "local-first"`, `ALLOW_LIVE_AI = "0"`: hệ thống **bỏ qua hàng `141:route-d`**, tính lại từ đầu qua Planner/Kernel/Adapter mới (`HTTP 200`, `route_d.status == "SERVED"`, `STALE_H4_MARKER` và `H4` đều không xuất hiện trong `scene3d.objects`, `plan_cost == 8`), rồi dọn sạch khóa thử nghiệm trong DB.
