# Cache semantic identity decision (P6)

**Quyết định: bump `CACHE_VERSION` 145 → 146** (`ROUTE_D_CACHE_POLICY = "146:route-d"`), commit `5c25c7ea9`. Candidate
được đóng băng lại ở commit riêng `fad0db5f2` (worktree detached sạch, 123 file, `13a32060…`).

## Bằng chứng

1. **Bề mặt mô hình không đổi.** `semantic_environment_fingerprint` gom prompt, thẻ văn phạm, lược đồ, capability hash,
   bề mặt TypedFactNext và Hybrid; nó không chứa Source Gate, parser hay lowering SLM. `tests/test_cache_identity.py` xanh
   trước bump (15/15) và `cache_identity.lock.json` chỉ đổi đúng trường phiên bản sau khi chạy lại
   `scripts/lock_cache_identity.py`.
2. **Bề mặt quyết định đổi.**
   - Source Gate nhận yêu cầu mô phỏng có danh từ khối.
   - Parser chọn đích 7b theo nhãn hoặc loại khối và phủ đủ mệnh đề.
   - SLM hạ 0 mục tiêu số cho đề chỉ-mô-phỏng và trích `construct_object` từ câu yêu cầu.

   Với cùng một đề, mã mới có thể phục vụ một cảnh khác, hoặc phục vụ đề mà mã cũ từ chối.
3. **Khoá Route D không thấy thay đổi đó.** `prepare_local_first_hybrid` băm route, router version, `parser_version`,
   model, bề mặt trích xuất, preview surface, response contract và text. `local-geometry-parser/2` không đổi, Source Gate
   không có trong khoá, và đọc cache không kiểm lại. Vì vậy một hàng ghi dưới `145:route-d` sẽ được phát lại **thay**
   quyết định mới. Khoá cache SLM thì tự tách, vì nó có `validator_version` = `slm-grounding-validator/5`. Khoá Route D
   thì không.

## Kiểm (nền đỏ + tiêm lỗi)

`backend/tests/test_cache_simulation_intent_invalidation.py`:

- ghi một envelope SERVED **có marker** dưới `145:route-d` cho đề chỉ-mô-phỏng
  "… Hãy mô phỏng hình chóp S.ABCD." ⇒ `POST /api/analyze` trả cảnh mới, không còn marker, và hàng được ghi lại dưới
  `146:route-d`;
- đối chứng: cùng hàng đó ghi dưới chính sách hiện hành ⇒ HIT (marker trở lại), chứng minh không có kiểm lại khi đọc.

Tiêm lỗi: đặt tạm `CACHE_VERSION = "145"` ⇒ hai test đỏ (marker được phát lại). Đặt lại `146` ⇒ xanh.

25 test đang ghim `"145"` được cập nhật bằng Edit (hook chặn `sed -i`). Bảng danh tính `docs/CURRENT_STATE.md` ghi
**146**, khoá bởi `tests/test_current_state_identity.py`.
