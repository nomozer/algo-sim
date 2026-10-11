# Quyết định kiến trúc: Hybrid B là kiến trúc đích bên trong Text-to-Geometry Functions

**Status:** accepted — 2026-10-11 (người dùng). Bất biến: bản này không sửa; quyết định sau thay nó bằng một tệp mới và ghi
`superseded by` ở đây. Tinh chỉnh — **không thay thế** — [`TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md`](TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md).

## Quyết định

Trong kiến trúc Text-to-Geometry Functions, hướng ưu tiên là **Hybrid B**:

```
đề tiếng Việt → AI trích Typed Facts có nguồn (app/ai/fact_extraction.py)
             → Compiler/Planner tất định chọn và kết hợp Geometry Functions (geometry_functions/planner.py)
             → cổng nguồn → Engine → Kernel → IR → Scene3D  (dùng chung với A, không có engine thứ hai)
```

Lý do:

- AI chỉ làm phần nó làm được: đọc mệnh đề và trích dữ kiện có kiểu, mỗi dữ kiện chép nguyên văn đoạn đề làm căn cứ.
- Việc **chọn và kết hợp hàm** là việc của compiler tất định — kiểm toán được từng quyết định (trace `fact → rule → fn`).
- Registry 27 hàm, Engine, Kernel, IR, Scene3D là **một** bộ dùng chung; A và B khác nhau ở đầu vào của compiler, không ở
  toán học.
- Toán học được kiểm chứng tất định (kernel chính xác, kiểm lại mọi dữ kiện trên hình đã dựng).

## Giới hạn của quyết định — phải đọc cùng

- Đây là quyết định **thiết kế dựa trên kết quả offline**: A/B offline (`hybrid-compiler-selection`,
  `hybrid-ab-pilot-readiness`) và benchmark năng lực compiler (`hybrid-compiler-capability-audit`).
- **Chưa có bằng chứng** Hybrid B chính xác hơn hay tiết kiệm tổng token hơn A khi chạy Gemini thật. Pilot A/B thật chưa
  chạy; trần token của pilot khoá cho bề mặt cũ, bề mặt hiện tại NO-GO (`tests/geometry/test_hybrid_ab_branch_readiness.py`).
- **A** (AI chọn hàm qua function calling) **tiếp tục tồn tại làm baseline đối chứng**, không phải hướng sản phẩm ưu tiên;
  bằng chứng thực nghiệm của A được giữ nguyên.
- **Chưa** chuyển Hybrid thành production default: `LLM_ONLY` vẫn là mặc định; đổi mặc định đi qua
  [`../MIGRATION_CHECKLIST.md`](../MIGRATION_CHECKLIST.md).
- Không tạo kiến trúc hay Geometry Engine thứ hai. Năng lực mới của B đi vào compiler hiện có (`planner.py`) hoặc Registry
  dùng chung.

## Hệ quả

- Năng lực "kết hợp" của compiler phải được đo trên benchmark độc lập
  (`backend/tests/geometry/hybrid_compiler_benchmark.py`), không suy ra từ fixture chuyển đổi A→B.
- Planner hiện là bộ ánh xạ một-dữ-kiện → một-lời-gọi; mọi tìm kiếm chuỗi phép dựng theo mục tiêu là một **thay đổi thiết
  kế** cần phê duyệt riêng (đề xuất ở run `hybrid-compiler-capability-audit/design.md`).
