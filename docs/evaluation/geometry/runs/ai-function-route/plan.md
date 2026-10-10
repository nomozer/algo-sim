# ai-function-route — kế hoạch và PRE-FLIGHT

Yêu cầu (2026-10-10): Text-to-Geometry Functions được chấp nhận làm hướng chính. Lượt này: ADR; review kiến trúc đã
dựng; adapter Gemini function calling **offline** (provider giả); độ bền trước nhiều cách viết của học sinh; mở rộng hình
học trên kiến trúc mới; văn liệu v2. **0 lượt gọi Gemini.** Không merge/push, không đổi default, không xoá `LLM_ONLY`.

## PRE-FLIGHT (`RULES.md §2`)

```
Active branch:      feat/text-to-geometry-functions (tiếp tục nhánh nghiên cứu theo brief; chưa push)
HEAD:               ba6aedfb lúc bắt đầu (86f683e0 → c71cae4c → ba6aedfb trên main 28ac1d61), cây sạch
Task classification: CORE
Existing modules:   geometry_functions (registry, engine), app/ai/function_route, geometry_compiler (primitives, compiler họ-bài),
                    geometry/{metric,measure,kernel}, semantic_program/{validator,formation,interpreter,simulation_state,scene3d},
                    app/ai/gemini (ApiBudget, record_usage, _sanitize_gemini_schema — chỉ tham khảo, adapter không gọi provider)
Reuse:              registry.REGISTRY/doc_ke_hoach/kiem_nguon; engine._Dung; ir_builders; Metric; kernel measures (skew lines, plane–plane)
Files expected to change: geometry_functions/{registry,engine}.py; MỚI app/ai/function_calling.py; tests + fixtures; run docs;
                    docs/architecture (ADR + contract), STATUS_LEDGER, CURRENT_STATE, ROADMAP, CODE_INDEX
Contract/cache:     bề mặt mô hình của LLM_ONLY KHÔNG đổi (prompt/thẻ văn phạm/lược đồ IR/routing) ⇒ CACHE_VERSION 125 giữ;
                    backend/app đổi ⇒ đóng băng lại candidate ở commit riêng
Duplicate risk:     adapter vs gemini.call_gemini (call_gemini chỉ trả text — không đọc functionCall; adapter có parser riêng,
                    không nhân bản transport khi chưa chạy live); quan hệ mới vs FactGraph `structured_relations` (thuộc
                    RequestContract của LLM_ONLY — không tái dùng được cho lời gọi hàm có nguồn)
Scope-creep risk:   từ đồng nghĩa vô hạn — thay bằng hàm riêng cho từng CẤU TRÚC câu (đường cao, hình chiếu, hai đường vuông góc)
                    + chuẩn hoá có tiền điều kiện trong engine
Stop conditions:    cần sửa kernel/interpreter/lược đồ IR; test cũ phải nới để xanh
```

## Các bước

1. C — review: phát hiện `test_Y` nới không cơ sở (ngoại lệ cả thư mục + nhập `geometry_compiler.primitives` kéo theo cả
   compiler) ⇒ dời bộ tạo câu lệnh IR sang `semantic_program/ir_builders.py`, khôi phục bất biến gốc + bao đóng import
   (`99ecb815`).
2. Tiền đăng ký (commit riêng, TRƯỚC mã): `paraphrase_cases.json` (diễn đạt + cặp gần nghĩa + âm) và
   `geometry_expansion_cases.json` (độ dài ký hiệu `a`, mặt bên ⊥ đáy, trọng tâm, góc hai mặt, khoảng cách hai đường chéo nhau).
3. E — tách cổng nguồn: vai trò mệnh đề (tiền đề / mục tiêu chứng minh / điều kiện), phạm vi phủ định theo mệnh đề, khớp quote
   bỏ qua khoảng trắng, nhiều quote mỗi lời gọi, căn giá trị theo nhãn đoạn, tham chiếu mặt phẳng / vai trò điểm; quan hệ
   tương đương = HÀM riêng (`altitude`, `orthogonal_projection`, `perpendicular_lines`, `equal_length`) chuẩn hoá trong
   engine kèm tiền điều kiện.
4. F — mở rộng trên engine: độ dài ký hiệu (đồng bậc, đơn vị dựng a = 1, đáp số nhân a^d), `face_perpendicular_base`,
   `centroid`, `ask_angle_plane_plane`, `ask_distance_lines`.
5. D — `app/ai/function_calling.py`: khai báo hàm Gemini (OpenAPI subset), payload `ANY` + `allowedFunctionNames`,
   `maxOutputTokens`, bộ đọc phản hồi (finishReason, thiếu/hỏng/trùng/vòng phụ thuộc), provider giả + transport live có cổng
   `ALLOW_LIVE_AI` (không gọi).
6. B — ADR + contract ở `docs/architecture/`; STATUS_LEDGER, CURRENT_STATE, ROADMAP.
7. G — văn liệu v2 (tác tử nền). H — test, đột biến, renderer, đóng băng lại, full suite, báo cáo.
