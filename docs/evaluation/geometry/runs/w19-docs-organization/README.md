# Run `w19-docs-organization`

`W19_DOCS_REORGANIZATION_AND_RESEARCH_EVIDENCE_CURATION` — tổ chức lại `docs/`, một bản đồ tuyên bố ↔ bằng chứng,
gốc `docs/` đóng. Chỉ tài liệu và công cụ kiểm tài liệu; 0 thay đổi sản phẩm; 0 lượt gọi model.

Bắt đầu từ [`HANDOFF.md`](HANDOFF.md); diễn giải ở [`REPORT.md`](REPORT.md); siêu dữ liệu ở [`RUN.json`](RUN.json);
băm từng file ở [`MANIFEST.json`](MANIFEST.json).

| thư mục | nội dung |
|---|---|
| `inputs/` | `W19_SCOPE_DECISIONS.json` — bất biến của brief, luật R1–R12, bản ghi skill |
| `inventory/` | `INVENTORY.json` (mọi tài liệu + nhóm artifact + ngoài docs + tạm, tại `6d0e6321`) · `MIGRATION_MAP.json` (cũ → mới, blob trước/sau) · `REWRITE_LOG.json`, `REWRITE_LOG_MERGE.json` (từng dòng đường dẫn viết lại) · `AUTHORITY_RETARGET.json` (con trỏ thẩm quyền đổi sang bản đồ) |
| `verification/` | `LINKS_BEFORE.json` → `LINKS_FINAL.json` (link/anchor/đường dẫn), `OLD_PATH_CONSUMERS_FINAL.json`, `FROZEN_IDENTITY.json`, `DOCS_TREE_BEFORE_AFTER.txt`; các bản `*_TASK2.json`, `*_TASK3.json` là lượt trung gian; `logs/` (candidate, cache, bộ kiểm tài liệu, test) |
| `diagnostics/` | script một lần của W19 (đều chạy từ gốc kho, chỉ đọc trừ `rewrite_doc_paths.py` và `build_report_catalog.py`), `TEMP_FILE_INVENTORY.json`, `PONYTAIL_REVIEW_W19.md`, `build_manifest.py` |

Tái lập (0 lượt gọi model, từ gốc kho, Python `backend/.venv/Scripts/python.exe`):

```bash
backend/.venv/Scripts/python.exe <run>/diagnostics/check_doc_links.py --inventory <run>/inventory/INVENTORY.json --out <file>
backend/.venv/Scripts/python.exe <run>/diagnostics/check_old_path_consumers.py --map <run>/inventory/MIGRATION_MAP.json --inventory <run>/inventory/INVENTORY.json --out <file>
backend/.venv/Scripts/python.exe <run>/diagnostics/verify_frozen_identity.py --base 6d0e6321 --inventory <run>/inventory/INVENTORY.json --map <run>/inventory/MIGRATION_MAP.json --out <file>
cd backend && .venv/Scripts/python.exe scripts/audit_docs_information_architecture.py
```

`inventory_docs.py` chỉ chạy được trên cây bằng `6d0e6321` (nó từ chối cây đã lệch); `rewrite_doc_paths.py` đã áp
dụng — chạy lại với `--dry-run` cho 0 thay đổi.
