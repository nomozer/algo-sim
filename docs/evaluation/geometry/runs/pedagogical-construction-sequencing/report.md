# Trình tự dựng hình cho người học — Hybrid Scene3D (LOCAL, 2026-10-14)

**Kết luận: `READY_FOR_HUMAN_VISUAL_REVIEW`.** Khối cơ sở được dựng trước các điểm phụ (M, H, H1); lăng trụ và hình hộp
hình thành theo bước; điểm dựng được kể bằng phép dựng thật. Không đổi một giá trị toán học nào. Đóng
`ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID` trên nhánh nghiên cứu. Không gọi Gemini, Hybrid vẫn tắt, không merge/push,
không `APPROVED_BY_USER`. Nhánh `research/goal-directed-two-line-plane-section`; main = origin/main `5270f3dd`.

## 1. Chọn cách làm (kiểm toán A/B/C)

Khung k là `trace[k]` (bất biến #31) ⇒ một dòng thời gian riêng ở frontend (B) sẽ phá bất biến. Thứ tự câu lệnh IR CHÍNH
LÀ thứ tự người học thấy, nên chọn **A — sắp xếp lại tô-pô các phép đã có**, ở đúng hai chỗ chỉ Hybrid dùng:

- `geometry_functions/engine.py::bien_dich` phát mọi khối điểm (M, vectơ, H, H1) trước khối đa diện. Nay `thu_tu_su_pham`
  tách: khối điểm mà khối đa diện CẦN (đỉnh, chân đường cao do chính `formation._chan_ung_vien` nhận, và mọi thứ chúng đọc)
  → khối đa diện → các điểm phụ còn lại theo thứ tự cũ. Cùng câu lệnh, cùng giá trị.
- `hop_dong_to_po_da_khai` chỉ khai tô-pô cho chóp `pyramid` ⇒ bước bổ sung dựng hình CÓ SẴN (`formation.hoan_thien_dung_hinh`,
  dùng chung, không sửa) không phân loại được lăng trụ/hộp/chóp đều và vẽ chúng trong một bước. Nay khai thêm `prism`
  (`ABC.A'B'C'`, ′ ’ ≡ ') và `regular_pyramid` (`S.ABC`) — CHỈ khi câu nguồn viết đúng ký hiệu ấy.
- Lời kể "Dựng M." đến từ `scene3d.py` (dùng chung với LLM_ONLY — không sửa). Tầng cảnh Hybrid (`ai/function_route.py`)
  viết lại lời bước dựng điểm từ producer + ký hiệu toán hạng; producer khác dùng vai do `display_names` phát.

Không dựng planner thứ hai, thẩm quyền ngữ nghĩa mới hay hệ hoạt hình mới. Bước đáy/đáy trên/cạnh bên/khép khối là bước
TRÌNH BÀY của bước bổ sung có sẵn (`construct_polygon`/`construct_segment` trên đỉnh đã có), không phải suy luận mới.

## 2. Trước / sau (chi tiết từng bước: [`steps.md`](steps.md))

| họ | trước (bước học / trace) | sau | thứ tự sau |
|---|---|---|---|
| chóp S.ABCD | 13 / 16 — M, H, H1 rồi đáy, cạnh bên, khối | 13 / 16 | đáy → cạnh bên → khối → M → H → H1 → (P) → 4 cạnh thiết diện → khép + diện tích |
| lăng trụ đứng ABC.A′B′C′ | 11 / 14 — M, H, H1 rồi khối MỘT bước | 14 / 17 | đáy dưới → đáy trên → cạnh bên → khối → M → H → H1 → (P) → … |
| hộp ABCD.A′B′C′D′ | 11 / 14 — như trên | 14 / 17 | đáy dưới → đáy trên → cạnh bên → khối → M → H → H1 → (P) → … |

Lời kể mới: "Dựng M là trung điểm của đoạn AB." · "Qua M dựng điểm H sao cho vectơ MH bằng vectơ BC." · "Qua M dựng
điểm H1 sao cho vectơ MH1 bằng vectơ AS/BB′." (đúng nghĩa: H = M + (C − B)).

**Không theo gợi ý "cạnh bên trước đáy trên" cho lăng trụ/hộp:** thứ tự đáy → đáy trên → cạnh bên → khép là hợp đồng
`formation.TOI_THIEU` dùng chung với LLM_ONLY; đổi nó là đổi cảnh của tuyến mặc định — ngoài phạm vi.

## 3. Kiểm chứng

- **Corpus tiền đăng ký** `inputs/corpus.json` (`09b29d48`, trước mọi sửa): 6 phát triển (chóp, lăng trụ, hộp, từ chối,
  đổi nhãn S→T…, trung điểm tên H) + 30 kiểm thứ tự chưa dùng cho phát triển (9 ca SERVED còn lại của corpus toán two-line
  + 21 ca SERVED-kỳ vọng của benchmark lịch sử). Heldout 32 two-line KHÔNG nằm trong corpus.
- **Hợp đồng** (`backend/tests/geometry/construction_sequencing.py`): O1 phụ thuộc trước · O2 điểm/vectơ/mặt phụ ngoài
  bao phụ thuộc của khối + vật dựng khối xuất hiện SAU khi khép khối · O3 vai trò dựng khối mỗi vai một bước riêng, đúng thứ
  tự (khi nguồn khai tô-pô) · O4 lời kể nêu phép dựng, toán hạng và chiều vectơ · O5 trạng thái, mã từ chối, đáp số, dấu
  vân tay toán học chính xác không đổi · O6 định danh và toạ độ vật không đổi; thêm: không vai trò dựng nào mất so với `5bd28d73`.
- **Phát triển**: 5 served + 1 từ chối, O1–O6 PASS (`after-final/development.json`).
- **Kiểm thứ tự (held-out đúng nghĩa)** — lượt đầu tại freeze `b0a853a0` (`after/ordering_check.json`): toán học 30/30 bất
  biến; thứ tự **27/28 served PASS**, 1 FAIL: benchmark-B02 (chóp tam giác đều `S.ABC` vẽ một bước — `regular_pyramid`
  chưa được khai tô-pô, có từ trước sửa). Sửa ở `c217aade` sau khi xem kết quả ⇒ các lượt sau (28/28 served + 2 từ chối giữ
  nguyên) **không** còn là held-out.
- **Review** phát hiện hồi quy C1 (mất bước chiều cao khi chóp có hình chiếu đỉnh lên đáy) — tái hiện, RED → sửa
  `a5a0797c`; corpus không có ca này, nay có test riêng và phép so "vai trò không mất" trên cả 36 ca.
- **Bất biến lịch sử** (phép kiểm, không phải held-out): two-line phát triển 45 (12/33) và heldout 32 (11/21) trùng từng
  dòng; benchmark lịch sử 30 `metrics.json` trùng byte (19/9/0/2) — `verification/`.
- **Trình duyệt** (`hybrid-section-visual-check.mjs --scenes sequencing --playback`, harness Scene3DWorkspace qua Hybrid,
  không phải trang sản phẩm/API): SwiftShader + Intel UHD D3D11, mọi bước học: vị trí chấm/nhãn = phép chiếu toạ độ
  chính xác, `objectsAt` = `formation.visible_ids`, vật vẽ ⊆ vật có mặt, nhãn giấu chỉ khi chạm thật, nhãn hiện không chồng,
  cạnh khuất ổn định, quay lại bước trùng điểm ảnh, góc xoay thứ hai, chọn H/H1 — **0 lỗi**. `visual/scenes.json` xuất lại
  ở product cuối trùng byte ⇒ receipt (đo ở `38c304ce`) đúng với product cuối. Contact sheet: `after/{swiftshader,intel-d3d11}/
  <cảnh>/contact-sheet.png`; trước: `../scene3d-construction-audit/after/<gpu>/<cảnh>/contact-sheet.png`.
- **Candidate**: freeze `f227dd72`, product `a5a0797c`, tree hash `26698338…` (110 file); trung gian `21ed6faa…` (`0dd7f4cc`)
  và `8e5a155a…` (`c217aade`) ghi trong `inputs/candidate_divergence.json`; `CACHE_VERSION` 125 giữ (`cache/decision.json`:
  `main.py`/`pipeline.py` không nhập module Hybrid).
- **T3** sạch tách rời: §5.

## 4. Không sắp xếp được / giới hạn

- Điểm mà khối CẦN (đỉnh dựng, chân đường cao) phải đứng trước khối — đúng hợp đồng; chân chóp hiện trước đáy (bước bổ
  sung chèn đáy/chiều cao ngay trước khối).
- Khối không có tô-pô khai từ nguồn (vd "tứ diện ABCD") vẫn vẽ một bước — không bịa tô-pô. Nhiều khối trong một bài: tập
  "cần" là hợp của các khối (O2 khi ấy yếu) — Hybrid hiện không có ca nhiều khối.
- Dòng thời gian sản phẩm gộp bước "Lấy vectơ BC." (không vẽ) vào bước học TRƯỚC nó, nên lời phụ của bước "Dựng M…" kèm
  "· Lấy vectơ BC." — luật gộp dùng chung ở frontend, không đổi.
- O4 với ký hiệu một chữ là kiểm yếu; O5/O6 gần như tất yếu do bố cục chạy trước `bien_dich` — chứng cứ chính của bất biến
  là thiết kế (tách tô-pô cùng câu lệnh) + so dấu vân tay.
- UX còn mở (không sửa ở lượt này): tên (P) chưa vẽ trên canvas; chế độ chọn làm cảnh nhạt; phân biệt nét khuất / mặt phụ /
  thiết diện cần người duyệt; nhãn chồng thật ở vài góc xoay (vd B ≈ A′ ở hộp).
- Orbit gate trên máy này vẫn KHONG_ON_DINH (`ISSUE-OPS-ORBIT-GATE-UNSETTLED-LOCAL`) — không tính là PASS.
- Commit `0dd7f4cc` sửa test RED tiền đăng ký (kiểm nhầm `RequestContract`, không thể xanh) — công bố ở `review.md`.

## 5. Cổng và Git

**T3** sạch tách rời tại `f227dd72` (product `a5a0797c`): **FULL_PRODUCT_GATE_PASS** — backend 9329 passed (skip 1,
deselected 2, xfail 6), frontend 1055/68 file, build, tập demo, bề mặt sập; 0 lần thử lại socket (`verification/t3-pass.json`).
Lượt trước sửa review tại `38c304ce` cũng PASS (9327) — giữ `verification/t3-38c304ce-*`, đã bị thay thế. Docs/identity/secret: §6.

Commit: `09b29d48` tiền đăng ký · `0dd7f4cc` sửa thứ tự · `b0a853a0` freeze · `93b24383` held-out + RED chóp đều ·
`c217aade` sửa chóp đều · `ea02ae64` freeze · `38c304ce` nguồn harness · `1cd29fe8` RED review · `a5a0797c` sửa review ·
`f227dd72` freeze cuối · commit tài liệu. Push NONE. Dọn: `cleanup.json`.

## 6. Tài liệu, danh tính, bí mật

`test_docs_information_architecture.py` + `test_current_state_identity.py` 45 PASS; `audit_docs_information_architecture.py`:
OPEN_ISSUES hợp lệ, next action chuẩn, gốc `docs/` đóng, rò bí mật 0. Candidate `--verify` khớp `26698338…`.

Codex tiếp quản phần kết thúc: chạy lại 45 kiểm tra trên và audit, xác minh hash log T3 cuối, xuất lại bốn scene
trùng byte với dữ liệu browser đã đo; receipt: `verification/takeover-closure.json`. Không chạy lại T3/browser dài,
không sửa mã sản phẩm. `review.md` ghi review độc lập trước sửa cuối; receipt targeted re-review sau `a5a0797c`
chưa tìm thấy (`NOT_VERIFIED`), không nâng thành phê duyệt của người. Cleanup còn scratch hỗn hợp mà lần trước đã
bị từ chối ở permission prompt; giữ nguyên, không thử xóa lại và không công bố cleanup toàn máy hoàn tất.
