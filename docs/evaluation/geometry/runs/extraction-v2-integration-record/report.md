# Extraction v2 — bản ghi tích hợp thật (lớp đính chính, 2026-10-18)

Lớp đính chính cho wave `HYBRID_SEMANTIC_EXTRACTION_V2` (`../hybrid-semantic-extraction-v2/`). Chỉ docs: không đổi mã,
prompt, lược đồ, `CACHE_VERSION` (125) hay bằng chứng; 0 lượt gọi model. Các file của run gốc **giữ nguyên byte** —
chỉ trường `CORRECTED_BY` của entry trong `docs/EVIDENCE_INDEX.md` trỏ sang đây.

## 1. Cái gì sai trong bản ghi cũ

Entry `HYBRID_SEMANTIC_EXTRACTION_V2` trên `main` (đến `551a3541`) vẫn mô tả trạng thái trước quyết định của owner:

| trường / tài liệu | ghi | thực tế |
|---|---|---|
| `CLASSIFICATION` | `integration PENDING_OWNER_GO` | prompt v2 **NO-GO** (`../hybrid-semantic-extraction-v2/disposition.md` mục 2); phần an toàn đã **nằm trên `main`** (mục 2 dưới) |
| `CODE_COMMIT` | `69fa9be8` (prompt v2 + Source Grounding) | `69fa9be8` **không** thuộc `main`; mã đã vào `main` là `e4fff851` + `0507cb01` |
| `../hybrid-semantic-extraction-v2/handoff.md` | "Integration (separate owner GO): fast-forward `main` …" (toàn nhánh, kể cả prompt v2) | không xảy ra; chỉ tích hợp chọn lọc |

Bản nháp `integration.md` từng nằm untracked trong worktree `integration/extraction-v2-safety` **không được dùng**: nó
trích `verification/t3-safety.json` (file không tồn tại), candidate `6a4414d5…` @ `330a222a` và `e3827c00` — hai commit
sau không thuộc `main`. Bản nháp đó được sao lưu nguyên trạng ngoài Git (gói bảo toàn 2026-10-18), không vào kho.

## 2. Cái gì thật sự đã vào `main`

| commit | nội dung | thuộc `main`? | đường vào |
|---|---|---|---|
| `e4fff851` | Source Grounding trong `geometry_functions/registry.py` ("hộp chữ nhật", "dài bao nhiêu", mạo từ đầu câu, "hình hộp" trần không chứng nhận lăng trụ đứng) + scorer `/2` + test | có | merge `a94a54d0` (hybrid-backend tích hợp `research/semantic-extraction-v3-runtime-revision`) |
| `aa0da02b` | refreeze: `product_commit_sha` `e4fff851`, `tree_hash` `9da80c6f3e8efbf8371b29949d7e03abebf5e3b46a5d090615feea4f7f8f78d8`; `../hybrid-semantic-extraction-v2/candidate_divergence.json` | có | cùng đường |
| `0507cb01` | dấu hiệu lăng trụ đứng phải gọi tên chính khối đó (cherry-pick của `e3827c00`, cùng `patch-id --stable`) | có | cùng đường (qua nhánh v3; `../semantic-extraction-schema-contract/takeover-inventory.md`) |
| `69fa9be8` | prompt v2 trong `backend/app/ai/fact_extraction.py` | **không** | owner NO-GO; chỉ ở `research/hybrid-semantic-extraction-v2` + tag local `evidence/extraction-v2-pilot` |
| `e3827c00`, `330a222a` | bản gốc của `0507cb01`; refreeze candidate `6a4414d5…` (cây cũ) | **không** | chỉ ở `integration/extraction-v2-safety`; `330a222a` không có giá trị merge |

Kiểm: `git merge-base --is-ancestor <c> main` cho từng dòng; `git cherry main integration/extraction-v2-safety`
(`e3827c00` là `-`).

## 3. Bằng chứng phủ phần đã vào

- Freeze tại `e4fff851`: 110 file, `--verify` MATCH (`candidate_divergence.json` của run gốc). **Không có T3 riêng** tại
  `e4fff851`/`aa0da02b`/`0507cb01`: `t3-safety.json` chưa từng tồn tại ⇒ T3 tại đúng các commit đó là `UNKNOWN`.
- T3 có thẩm quyền **đầu tiên chứa cả ba commit**: `1abc0a51`, FULL_PRODUCT_GATE_PASS
  (`../hybrid-pre-main-hardening/verification/authoritative-t3.json`). Cùng run đó chạy file probe an toàn của
  `integration/extraction-v2-safety` trên cây: 35/35 hành vi, superset trong cây 72/72
  (`../hybrid-pre-main-hardening/report.md` §3).
- Mọi T3 có thẩm quyền sau đó trên dòng `main` cũng chứa chúng, gần nhất là candidate `14c26f3f`
  (`../scene3d-metric-boundary/run.json`).
- Prompt sản phẩm và bề mặt provider của tuyến mặc định không đổi (`candidate_divergence.json`: chỉ `registry.py`;
  `LLM_ONLY` không nhập `registry`/`function_route`).

## 4. Không đổi

Số đo của pilot ghép cặp, held-out niêm phong (chưa chạy), quyết định trong `disposition.md`, mọi receipt của run gốc.
Không đánh giá lại, không chấm lại. Các commit nghiên cứu (prompt v2, pilot) vẫn chỉ ở local — được bảo toàn bằng bundle
ngoài Git ngày 2026-10-18; việc push tag/nhánh lên origin là quyết định riêng của owner.
