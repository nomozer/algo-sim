# hybrid-compiler-selection — kế hoạch và PRE-FLIGHT

Yêu cầu (2026-10-10): dựng nhánh THỰC NGHIỆM B (AI trích dữ kiện có kiểu → planner/compiler chọn và kết hợp hàm) chạy
OFFLINE và so có kiểm soát với nhánh A (AI chọn hàm, run `ai-function-route`). Giả thuyết, KHÔNG phải kết luận. 0 lượt gọi
Gemini; không đổi mặc định; không merge/push; không xoá LLM_ONLY hay kết quả cũ; ADR giữ nguyên (đánh giá ghi thành tài liệu riêng).

## PRE-FLIGHT

```
Branch / HEAD:   feat/text-to-geometry-functions @ 3bb38fc7 (local, chưa push); cây: chỉ frontend/public/favicon.svg chưa theo dõi
                 (của người dùng — giữ nguyên, không stage)
Candidate:       168a086e… (108 tệp) --verify khớp; CACHE_VERSION 125, khoá cache khớp
Classification:  CORE (thí nghiệm kiến trúc trên đường đích), nhánh B không thay mặc định
Reuse:           REGISTRY + kiem_nguon + engine (dung_tu_loi_goi) + function_route (Scene3D) + function_calling (_openapi,
                 live_transport, MAX_OUTPUT_TOKENS) — B đổ vào ĐÚNG đường sau `{"calls": [...]}` của A, không có back end thứ hai
New:             geometry_functions/planner.py (Typed Facts + planner), ai/fact_extraction.py (adapter dữ kiện, provider giả),
                 run_fact_route (function_route.py)
Duplicate risk:  FactGraph của compiler cũ (fact_graph.py) đọc RequestContract của LLM_ONLY — không nhận dữ kiện có nguồn/vai trò;
                 không tái dùng, không mở rộng. Planner KHÔNG có họ bài: ánh xạ từng loại dữ kiện → hàm + mở rộng định nghĩa.
Contract/cache:  bề mặt LLM_ONLY không đổi; thêm từ khoá "lập phương"/"chữ nhật" vào cổng nguồn (áp cho cả A và B) ⇒ ghi rõ
Stop:            phải sửa kernel/interpreter/IR; phải nới cổng nguồn để B qua
```

## Bước

1. Tiền đăng ký 14 ca holdout mới (`hybrid_holdout_cases.json`): lời gọi A + dữ kiện B + kỳ vọng + hạng + oracle tay.
2. Test (đỏ) → planner + adapter dữ kiện + `run_fact_route` → xanh; dữ kiện B cho 58 ca cũ sinh bằng bộ chuyển đổi CƠ HỌC
   (giả định AI trích hoàn hảo — chỉ kiểm PARITY, không kiểm tổng quát hoá).
3. A/B offline trên 58 + 14 ca, phân hạng (correct served / wrong served / correct refusal / false refusal / unsupported /
   infrastructure), đột biến, renderer metric.
4. Tài liệu: so sánh kiến trúc, hợp đồng Typed Facts, bản đồ planner, kết quả A/B, oracle, phân tích từ chối, kiểm toán tái
   dùng, cập nhật khoảng trống (tác tử nền), giao thức A/B thật (CHƯA chạy). Đóng băng lại candidate; full suite trong worktree sạch.
