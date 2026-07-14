# RULES.md — Luật cứng hiện hành (bản con trỏ)

Bản thiết kế gốc v0.3 đã được lưu trữ tại `docs/legacy/RULES_v0.3.md` (tài liệu
lịch sử — mô tả các kiến trúc chưa/không xây như tầng sandbox chạy code hay
kịch bản vẽ do AI sinh; **không dùng cho quyết định implementation**).

## Thứ tự đọc bắt buộc trước mọi thay đổi không tầm thường

1. `docs/ARCHITECTURE_MAP.md` — bản đồ kiến trúc, bất biến đánh số, anti-pattern.
2. `docs/CURRENT_STATE.md` — milestone, baseline test, scope freeze, việc đã hoãn.
3. `docs/CORRECTNESS.md` — mô hình đúng đắn canonical ↔ learner.
4. `docs/COVERAGE.md` — nguyên tắc sư phạm, phạm vi phủ, tuyên bố bị cấm.
5. `docs/CODE_INDEX.md` — cái gì đã tồn tại ở đâu.
6. **Code và test thật.**

> Nếu tài liệu mâu thuẫn với code/test: **CODE/TESTS THẮNG** — sửa tài liệu,
> không bẻ code theo tài liệu.

## Các luật cứng bền vững (tóm tắt — nơi thực thi ở ARCHITECTURE_MAP §5)

1. **LLM không bao giờ sở hữu runtime**: không sinh timeline / bước / kết quả.
   LLM chỉ trích xuất ngữ nghĩa, phân loại, điền config được validate.
2. **Engine tất định sở hữu sự thật** — mọi diễn biến từ `init`/`apply`/`timeline`.
3. **Canonical simulation: đúng hoặc `capability_gap`** — không render xấp xỉ
   gây hiểu lầm.
4. **Học sinh được phép sai** — thao tác/dự đoán sai là cơ hội học.
5. **Chỉ rule tất định mới phán đúng/sai** — không có rule → `unsupported_to_verify`;
   LLM không bao giờ là giám khảo.
6. **Renderer không sở hữu sự thật ngữ nghĩa** — chỉ đọc state, phát action;
   bố cục/camera là của renderer, cấm vào engine state.
7. **2D/3D dùng chung module/config/state/timeline** — 3D là renderer,
   không phải domain; không simulation_id "_3d".
8. **Mọi tương tác của người học phải chạm cơ chế ẩn** và sinh hệ quả tất định —
   tương tác trang trí không được admit (COVERAGE §2.6).
9. **Không mở rộng kiểu một-module-một-bài-học** — ưu tiên specialized có sẵn →
   generic DSL → năng lực tái sử dụng → từ chối trung thực.
10. **Test mặc định = 0 API call thật** — live AI là opt-in có ngân sách.
