# Ponytail review — W19 diff

Phạm vi: `git diff 6d0e6321 -- backend/` (guard `audit_docs_layout`, `NAVIGATION_DOCS`, bốn test, một đường dẫn
trong `test_curriculum_coverage.py`) và sáu script một lần trong `diagnostics/` của run này. Tài liệu không thuộc
phạm vi review này.

## Đã cắt trong lúc làm

- `diagnostics/rewrite_doc_paths.py`:L20: delete: `import os` không dùng. Đã gỡ.
- `diagnostics/verify_frozen_identity.py`: delete: hàm `bang()` không ai gọi (hai vòng `ls-tree`/`ls-files` đọc
  thẳng). Đã gỡ.
- `diagnostics/check_doc_links.py`: shrink: lớp `MERGE` xử lý như `ARCHIVED` bằng một tập, không thêm lớp thứ tư.

## Xét và giữ

- `audit_docs_information_architecture.py` `audit_docs_layout`: lean already — một phép trừ tập cho mỗi lớp lỗi;
  `catalog_count` là chốt chống pass rỗng (FI-18), không phải trang trí.
- Sáu script `diagnostics/*.py`: yagni (đề xuất gom `git()` 3 dòng và luật phân lớp vào một module chung) —
  **giữ**: script trong run folder là bản ghi đóng băng, mỗi file phải chạy một mình sau khi commit; module chung
  làm chúng phụ thuộc nhau.
- `rewrite_doc_paths.py --map`: sinh bảng di chuyển trong cùng script — giữ, vì bảng cần đúng cặp cũ → mới và
  nhật ký mà lượt viết lại vừa ghi.

net: -0 lines possible (ngoài các chỗ đã cắt ở trên).
