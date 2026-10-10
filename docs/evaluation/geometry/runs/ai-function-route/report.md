# ai-function-route — báo cáo

Trạng thái: **`NEW_ARCHITECTURE_AI_ADAPTER_AND_GEOMETRY_EXPANSION_AWAITING_REVIEW`**. Nhánh nghiên cứu
`feat/text-to-geometry-functions` (local, chưa push/merge). **Số lời gọi Gemini thật: 0.** Mọi kết quả là
`foundation_only`: lời gọi hàm viết tay hoặc phản hồi `generateContent` giả — không nói gì về năng lực của Gemini.

## 1. Đã làm

| phần | kết quả | tài liệu |
|---|---|---|
| B · quyết định | ADR: Text-to-Geometry Functions là kiến trúc đích, `LLM_ONLY` legacy; contract v2; STATUS_LEDGER §0-2026-10-10 + hai mục wave; CURRENT_STATE, ROADMAP §0, AI_CONTEXT_BUNDLE: việc kế tiếp `AI_FUNCTION_ROUTE_BUDGETED_PILOT_DECISION` | `docs/architecture/TEXT_TO_GEOMETRY_FUNCTIONS_{DECISION,CONTRACT}.md` |
| C · review | phát hiện guard `test_Y` bị nới KHÔNG có cơ sở ở lượt trước (ngoại lệ cả thư mục; nhập `geometry_compiler.primitives` thật ra kéo theo cả compiler qua `__init__`) ⇒ dời bộ tạo câu lệnh IR sang `semantic_program/ir_builders.py`, khôi phục bất biến gốc KHÔNG ngoại lệ + bao đóng import AST từ `app.main`/`app.ai.pipeline` có đối chứng dương (`99ecb815`) | §3 |
| D · adapter | `app/ai/function_calling.py`: khai báo hàm Gemini từ registry, ANY + `allowedFunctionNames`, `maxOutputTokens` 8192, bộ đọc phản hồi 13 tình huống hỏng, transport live có cổng (không dùng); 58/58 fixture qua provider giả, 1 lượt gọi/đề | `ADAPTER_REPORT.md` |
| E · độ bền | oracle khoá trước (`f47c56bb`); mốc trước sửa **5/31** + **4 lỗ an toàn** của cổng v1; cổng nguồn 5 tầng + 4 hàm cấu trúc câu chuẩn hoá có tiền điều kiện ⇒ **23/23** | `SEMANTIC_ROBUSTNESS_EVALUATION.md` |
| F · mở rộng | độ dài ký hiệu a, mặt bên ⊥ đáy (chân dẫn xuất), hình chiếu + trọng tâm, góc hai mặt, khoảng cách hai đường ⇒ **8/8** | `GEOMETRY_EXPANSION.md` |
| G · văn liệu | v2: 37 công trình (22 toàn văn), 11 mới, 5 ablation | `LITERATURE_GAP_MATRIX_V2.md` |
| H · giao thức | 6 câu hỏi, pilot P-FC1 có trần (chưa chạy) | `EXPERIMENT_PROTOCOL_V2.md` |

## 2. Đường AI → hàm → engine → Scene3D đã kiểm offline đến đâu

Đầy đủ đầu–cuối trên **phản hồi giả đúng hình dạng `generateContent`**: payload (khai báo 24 hàm, ANY) → phần
`functionCall` song song → bộ đọc phản hồi → lược đồ → cổng nguồn → engine → IR → interpreter/kernel dưới metric →
Scene3D. 58/58 ca khớp kết cục đăng ký trước; renderer `veKhongGian` cho độ dài Euclid trùng metric khung trên 27/27
cảnh (315 cặp điểm). Chưa kiểm: hành vi của mô hình thật (chọn hàm, chép quote, tách mệnh đề, tỉ lệ cắt ở trần token).

## 3. Review kiến trúc đã triển khai (C)

1. Registry 16 → 24 hàm, lược đồ đóng — test: không ô toạ độ, hàm lạ/ô lạ bị bác. 2. Engine — 27 fixture gốc giữ nguyên
kết cục, đáp số, trace và **cả 10 cảnh trùng từng byte**; `results.json` chỉ khác chuỗi phiên bản registry và hai câu lý do.
3. **Phụ thuộc vào compiler — có lỗi, đã sửa**: xem bảng §1. 4. Grounding — có 4 lỗ an toàn (E). 5. Kernel + metric — tái
sử dụng nguyên, không sửa. 6. Scene3D — tái sử dụng nguyên; thêm `length_unit` khi đề dùng a. 7. Trace — mỗi bước mang id
lời gọi; luật chuẩn hoá ghi tên (`altitude_normalized_…`, `face_perpendicular_base_foot_on_AB_t=1/2`). 8. **Guard `test_Y`
không còn ngoại lệ**: ngoài gói compiler không tệp sản phẩm nào nhắc tới nó; đường mặc định không với tới compiler hay đường
mới theo bao đóng import.

## 4. Diễn đạt đã kiểm và giới hạn

Đã kiểm (lời gọi viết tay): câu chính quy, ký hiệu ⊥, "mặt phẳng đáy", đường cao, hình chiếu vuông góc, hai đường vuông góc,
dữ kiện trải nhiều câu, câu hỏi đứng trước + "biết", viết tắt học sinh, không khoảng trắng, nhiều số một câu, đại lượng
bằng nhau; âm: đọc nhầm đường–đường thành đường–mặt, một đường vuông góc, đường cao của tam giác, ảnh hình chiếu sai, "nếu
… thì", điều phải chứng minh, phủ định ngoài quote, mâu thuẫn, thiếu dữ kiện. **Không** tuyên bố AI hiểu paraphrase.
Giới hạn: `SEMANTIC_ROBUSTNESS_EVALUATION.md` §4.

## 5. Hình / phép dựng mới; tái sử dụng; trùng lặp

Mới: độ dài ký hiệu (đồng bậc), mặt bên ⊥ đáy, trọng tâm tam giác, hình chiếu vuông góc, đường cao, hai đường vuông góc,
độ dài bằng nhau, góc hai mặt, khoảng cách hai đường. Tái sử dụng: kernel, metric, IR (`divide_segment` cho trọng tâm),
interpreter, Scene3D; 8/12 bộ tạo câu lệnh IR chung. Trùng lặp với compiler họ-bài: chồng PHẠM VI ở 6/9 họ thể tích, khác
cơ chế; engine chưa phủ lăng trụ xiên và đáy chuỗi góc vuông k > 4 (`GEOMETRY_EXPANSION.md` §4).

## 6. Test

| bộ | kết quả |
|---|---|
| `test_ai_function_route.py` (diễn đạt, mở rộng, tiền điều kiện, adapter) | 49 passed (đỏ trước khi có module) |
| `test_text_to_geometry_functions.py` (27 fixture gốc) | 64 passed, không sửa test cũ |
| guard + compiler + Scene3D liên quan | 311 passed (lượt chạy cụm) |
| đột biến | 12/12 bị bắt (`diagnostics/mutation_check.log`) |
| renderer metric | RENDER_METRIC_OK 27/27 cảnh |
| full backend suite (cây sạch sau đóng băng) | __SUITE__ |
| cổng tài liệu | 67/67 |
| danh tính | candidate `93077b51` → `8f12f4ab` → **`168a086e…`** (108 tệp, đóng băng trong worktree sạch tại `d5f72ae7`); `CACHE_VERSION` 125, khoá cache khớp |

Không chạy T3/vitest: không đổi `frontend/src`; chỉ đổi ghim manifest Tier-A (node harness 88/88).

## 7. Khoảng trống nghiên cứu còn phải xác minh

Câu trích lấy từ `pdftotext` — phải đối chiếu trang gốc trước khi vào khoá luận; 15 công trình chỉ đọc tóm tắt; hai số
liệu `UNCLEAR` do bố cục cột (GeoBuildBench Bảng 1, API-Bank "32%"). Tập đọc không có số đo về token theo loại IR, về
chuẩn hoá có tiền điều kiện, về DSL/FactGraph/constrained decoding trên Gemini ⇒ **không thêm tầng nào** ở lượt này.
Đính chính đáng chú ý: tỉ lệ "2,42% thất bại" của FormalGeo không tính timeout (63,84% ở Bảng 1).

## 8. Pilot đề xuất (chưa chạy)

P-FC1: 34 đề × k = 3 (ANY) + 48 lượt VALIDATED tuỳ chọn; trần 160 lượt logic · 240 HTTP · 2,8 triệu token · 4 USD (xấu
nhất ≈ 3,5 USD theo giá Standard đã tra; dự kiến 0,6–1,2 USD) — `EXPERIMENT_PROTOCOL_V2.md` §2. Cần phê duyệt.

## 9. Skills đã dùng

`superpowers:verification-before-completion`, `superpowers:test-driven-development`, `mattpocock-skills:domain-modeling`
(khuôn ADR — đặt ADR ở `docs/architecture/` theo luật kho thay cho `docs/adr/` của skill), `mattpocock-skills:research`
(tác tử nền cho văn liệu v2).
