# AXO HYBRID /12 — Thesis Evidence Summary (Tóm tắt Bằng chứng Khóa luận)

## 1. Câu hỏi Nghiên cứu & Đóng góp Hệ thống

Chiến dịch **AXO HYBRID /12** giải quyết nút thắt ngôn ngữ phức hợp (*compositional geometry language*) được cô lập từ `/11` — khi học sinh viết gộp lệnh yêu cầu mô phỏng 3D, khai báo giả thiết lồng ghép, câu không dấu tiếng Việt, hoặc mục tiêu hỗn hợp (`vẽ + tính`):

1. **Tầng Phân tích Mệnh đề & Nhận diện Miền Tất định (`compositional-clause-analyzer/1`, `domain_profile.py`):**
   - Tách rõ vai trò từng mệnh đề (`SIMULATION_REQUEST`, `OBJECT_DECLARATION`, `PREMISE`, `METRIC_GOAL`, `SIMULATION_GOAL`) với độ chính xác offset nguyên văn `0` sai lệch (`242` mệnh đề, `114` ca dev `/11`).
   - Hỗ trợ nhận diện miền hình học tiếng Việt không dấu với ranh giới từ chặt chẽ và bộ loại nhiễu (`8/8` TP, `0/12` FP dev; `6/6` ca ngoại miền trong `V12` vẫn bị `gate_out_of_scope` chặn sạch).
2. **Mở rộng Bộ đọc Cục bộ, Source Gate & Grounded SLM Extractor (`local-geometry-parser/3`, `geometry-functions/33`, `local-slm-extractor/6`, `slm-grounding-validator/6`):**
   - Khôi phục `29/29` ca lỗi phi-D phát triển của `/11` (`28 DETERMINISTIC_ONLY` + `1 SLM_CONTRIBUTED`).
   - Trên tập kiểm thử blind tác giả tự soạn `V12_ACCEPTANCE_MANIFEST.json` (`105` in-scope + `6` bất định + `28` phủ định, `sha256 = f2fabd0b43fbe1d2cab1c1eeecdd2e143bf162cdd825b75b44bf209e38f13a86`, chạy đúng **1 lượt duy nhất** không tuning hậu kiểm qua trình duyệt thật Playwright Chromium + Vite preview + FastAPI/uvicorn + `Qwen3-0.6B-AxoV9-Q4_K_M`, `ALLOW_LIVE_AI = 0`):
     - **Hoàn thành đầu-cuối in-scope:** tăng từ `0.625` (`/10`) → `0.659` (`/11`) → **`88/105 = 0.8381`** (gần ngưỡng `>= 0.85`, thiếu `2` ca).
     - **Phục hồi SLM sống có kiểm chứng (`SLM_VERIFIED_SCENE_RATE`):** tăng từ `0/20` (`/10`) → `4/30 = 0.133` (`/11`) → **`17/32 = 0.5312`** trên tầng `SLM_REQUIRED` của ứng viên (`17 >= 5`, vượt ngưỡng `>= 0.30`), cộng thêm **`39` ca** nâng cấp tất định so với baseline P2 (`34 -> 73 PARSER_COMPLETE`).
     - **Độ tin cậy toán học & an toàn tuyệt đối:** Oracle `Fraction`/Gram độc lập (`scene_oracle.py`) xác nhận **`88/88 MATHEMATICALLY_VALID`** (`0` invalid, `0` lỗi), **`wrong_served = 0`**, **`grounding_violations_served = 0`**, **`unverified_relations_served = 0`**, **`fabricated_numeric_goals = 0`**, **`served_numeric_mismatch = 0`**, **`safe_refusal_rate = 28/28 (1.0)`**, **`external_ai_calls = 0`** (xác chứng bởi proxy ghi-chặn `18999`, `netstat` `763` nhịp / `0` non-loopback, và mạng Playwright `0` request ngoài).
3. **Sửa lỗi Căn khung Camera & Nhãn Ban đầu `Scene3D` (`V11-VIS-1`, `scene3d-view.tsx`):**
   - Khấu trừ phần dịch `setViewOffset` trong `tinhVungAnToanKhungNhin` và kẹp vị trí nhãn theo biên canvas trong `tinhViTriNhanDiem` đưa **`initial_visual_pass` trước khi người dùng orbit/reset lên `88/88 = 1.0`** (`min_canvas_ink = 0.80349`, `0` nhãn tràn biên, `0` đỉnh ngoài NDC, `0` lỗi console, `0` cảnh cũ đọng), cùng `88/88 (1.0)` tương tác xoay/zoom/step/reset trên `0` request `/api/analyze` phát sinh.

---

## 2. Khẳng định Trung thực cho Chương Đánh giá Khóa luận

| Hạng mục Khẳng định | Bằng chứng Hỗ trợ | Giới hạn Tuyệt đối Phải Nêu Rõ |
| --- | --- | --- |
| **An toàn & Chính xác Toán học Ngoại tuyến** | `88/88` Scene3D hợp lệ (`Fraction` + Gram `chart_metric`), `0` wrong-served qua `/10`, `/11`, `/12`; `28/28` ca phủ định chặn sạch; `0` request ra mạng ngoài. | Áp dụng cho bài toán trong năng lực `Registry /33`, `Planner /26`, `Engine /24`. Các ca ngoài miền/chưa hỗ trợ bị từ chối bảo thủ (`REFUSED` / `gate_out_of_scope`), không phải sai số hình học. |
| **Khả năng Cộng tác SLM Nhỏ (< 1B) + Grounding** | `Qwen3-0.6B-AxoV9-Q4_K_M` đạt `17/32 (53.12%)` `LOCAL_SLM_GROUNDED` sống trong tầng `SLM_REQUIRED` (tất cả đều `MATHEMATICALLY_VALID` và hiển thị đầy đủ trên trình duyệt), tách biệt rạch ròi với `39` ca tất định. | Tác giả thiết kế cả hệ và bộ `V12` (`EXTERNAL_INDEPENDENCE = NOT_MEASURED`; kho `H-1` độc lập và `GEMINI_PARITY` chưa đo). |
| **Ngưỡng Nghiệm thu & Hiệu năng Thực tế** | Tỷ lệ hoàn thành nhảy lên `0.8381` (`88/105`) và hiển thị ban đầu `1.0` (`88/88`) với `p50` nhánh tất định `152.0 ms`. | Chưa đạt ngưỡng preregistered `0.85` (`LIVE_SIMULATION_ACCEPTED = FALSE`), nhánh SLM sống có `p95 = 6,703.0 ms` trên CPU dev `15.78 GiB` (`PHYSICAL_TARGET_HARDWARE = NOT_MEASURED`, `REAL_STUDENT_USABILITY = NOT_MEASURED`). |
