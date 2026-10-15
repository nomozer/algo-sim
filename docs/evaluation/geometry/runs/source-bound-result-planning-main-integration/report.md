# Result binding — tích hợp main LOCAL (2026-10-15)

**Trạng thái: `RESULT_BINDING_MAIN_INTEGRATION_BLOCKED`.** Không fast-forward, không push, 0 lượt gọi model.
Luật của task: review độc lập thấy Critical/Important ⇒ dừng. Reviewer độc lập báo 2 IMPORTANT. Cả hai là lỗi có
từ trước và **cũng có trên `main`**: delta không tạo ra chúng, còn nhánh nghiên cứu thì từ chối nhiều ca hơn main. Tích
hợp hay không là quyết định của người dùng.

## 1. Review delta còn thiếu

Reviewer fresh-context, read-only kiểm `10dd6d6e..efb756aa`. Receipt: [`review-efb756aa-delta.md`](review-efb756aa-delta.md).

- Delta: **PASS**. `_CHAN_TAN_NGU` trùng từng byte với main. Hai kiểm tra cục bộ chỉ thêm điều kiện từ chối. Delta không
  tạo serve mới nào (36 probe). Nó lấy lại được lần diệt mutant `words before the phrase not checked` (đỏ ở `10dd6d6e`).
- **IMPORTANT-1** (có từ trước): `_kiem_phu` kiểm bổ ngữ trên văn bản đã ghép quote của AI. Quote bị bỏ dấu cách
  ("bìnhphương") nên vượt được guard ⇒ phục vụ `√11`, trong khi đề hỏi bình phương (= 11).
- **IMPORTANT-2** (có từ trước): đường khoảng cách điểm–đường thẳng phụ dùng denylist mở hai từ, không dùng văn phạm
  đóng `_GIUA_HOP_LE`. Vì vậy "hai lần", "căn bậc hai của", "lập phương", "nghịch đảo", "một phần ba", "1/2" và
  "… BD bình phương." đều được phục vụ `√11`.
- Phiên tích hợp đã tự chạy lại 4 probe tại tip nghiên cứu và tại `main` trong worktree sạch: kết quả trùng khớp,
  `SERVED √11` trên cả hai cây.
- Probe 36 ca: 10 ca phục vụ sai trên nhánh thì main cũng phục vụ sai y hệt. Main còn phục vụ sai thêm 11 ca mà nhánh
  đã từ chối. Nhánh không thêm serve sai nào.
- Phạm vi ảnh hưởng: tuyến nghiên cứu D (Hybrid B), không nối vào `/api/analyze`; Hybrid sản phẩm vẫn NO-GO.
  Lớp lỗi này nằm trong `ISSUE-ARCH-HYBRID-GATE-RESIDUAL-FALSE-SERVES` (nhóm C, "quantity modifiers ignored"); đường
  `_kiem_phu` nay được ghi cụ thể ở đó.

## 2. Preflight (đạt hết, chỉ bị chặn bởi §1)

| mục | kết quả |
|---|---|
| `main` = `origin/main` = remote thật (`ls-remote`) | `2a3c0787cc35d2e5530d77658225039ab4c5991e` |
| research tip lúc kiểm | `d3323447608f5ab248913fd02bdf0e7536fb6e1f`; ahead 13 / behind 0; `merge-base --is-ancestor` OK |
| diff | 0 xoá; artifact lịch sử bị sửa: chỉ `EVALUATION_CANDIDATE.json` (đóng băng lại); manifest dependency, `main.py`, `ai/pipeline.py`, `geometry_compiler/`, `semantic_program/`, `frontend/src` không đổi |
| sản phẩm sau `efb756aa` | rỗng (`backend/app`, `backend/tests`, `frontend/src`) |
| candidate `--verify` | khớp, 110 file, `c0a8792f1c491ae4…` |
| provider | A `7ea511a6…`, B `485d3834…`, khai báo hàm `5ceb0f99…` = `provider-surfaces.json` current |
| corpus / tiền đăng ký | `6587fabf…` / `14303fa0…`, chỉ commit `19140e2f` |
| `CACHE_VERSION` / mặc định | `"125"` / `LLM_ONLY` |
| `frontend/public/` | untracked, cả `main` lẫn research đều không track; `favicon.svg` sha256 `c5172af1…` không bị đụng |

## 3. Không làm

Không switch, không merge, không push, không xoá nhánh, không sửa receipt cũ, không sửa mã. Worktree tạm đã gỡ hết.
Scene3D parity audit chưa bắt đầu (xem handoff).
