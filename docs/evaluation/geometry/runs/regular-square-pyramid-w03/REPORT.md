# regular-square-pyramid-w03 — nghiệm thu local W2 + hai bản sửa

Việc `regular-square-pyramid`, W3 (2026-10-06), máy local Windows, một agent, 0 lượt gọi Gemini.
Bề mặt mô hình **không đổi** (môi trường ngữ nghĩa `b1714b56…`). `DEFAULT_MODE = LLM_ONLY`.

## 1. Tiếp nhận

| Kiểm | Kết quả |
|---|---|
| `git fetch --prune origin` | `origin/feat/regular-square-pyramid` = `fe68b4ca0e36218fe789a50ded1161775bbccfae` = EXPECTED_CLOUD_HEAD; `origin/main` = `38d41588` |
| W1_HEAD `e821b9b5` là tổ tiên của remote | có |
| commit riêng ở local | 0 → `git merge --ff-only` (26 commit tới) |
| thay đổi chưa lưu của người dùng | `D frontend/public/favicon.svg` — giữ nguyên, không stage, không restore |
| ref `main` mà test cần | có sẵn ở local (`38d41588`); worktree dùng chung ref, không tạo/đổi ref nào |

Commit W2 trên cloud có trailer `Co-Authored-By`; không viết lại lịch sử. Commit W3 không có trailer (kiểm từng commit).

## 2. W2 nguyên trạng tại `fe68b4ca` (worktree tách rời sạch `D:/tmp/rsp w03`, CRLF, có dấu cách)

Log: `diagnostics/baseline_fe68b4ca/logs/`; kết quả JSON: `diagnostics/baseline_fe68b4ca/results/`.

| Cổng | Kết quả |
|---|---|
| `w02_gates.sh fe68b4ca e821b9b5` | candidate `d3de9c44` + cache 113 khớp; schema ×2 trùng byte `d852b47c…`; `LLM_ONLY`; routing không đổi; bề mặt mô hình 0 file; ngoài run chỉ 2 sổ sống; `git diff --check` 0; audit docs PASS; node harness 83 pass / 0 fail / 2 skip |
| T3 `full-gate.mjs` | **`FULL_PRODUCT_GATE_PASS`** — pytest 7152 passed, 1 skipped; vitest 1089/1089; tsc + build; demo 5/5; bề mặt sập 6/6 |
| test node đường dẫn Windows có dấu cách (`full-gate.node-test.mjs`) | 5 pass, 2 skip, 0 fail |
| suite trình duyệt | 7/7 họ PASS; 14/14 lượt dương xanh trọn |
| `camera_settled_rotated_neutral` | lắng ở 14/14 (assertion chỉ sinh khi hết giờ; `camera_settle.rotated_neutral` có ở mọi lượt, 45–107 mẫu) |
| `causal_restore` thiết diện | desktop PASS, mobile PASS |
| đầu dò W2 · occlusion · phát lại · builder | 14/14 · pass, 0 lỗi, `HUMAN_REVIEW_PENDING` (4 cảnh, U2) · PASS · 68 crop, 0 bất đồng |

Phân loại các cổng đỏ của W2 trên cloud: **lỗi môi trường**. Bằng chứng không phải "W1 cũng đỏ": cùng mã `fe68b4ca`, cùng
cấu hình (worktree sạch CRLF, có dấu cách) chạy ở máy local này thì cả hai cổng xanh ở mọi lượt (khác biệt duy nhất là
môi trường dựng hình của trình duyệt; W2 ghi cloud dùng SwiftShader); 13 lỗi pytest của cloud
(ref `main` vắng, ghi LF vào cây CRLF) không tái hiện khi ref có và checkout CRLF thật.

## 3. H-W2-4 — bước mặt phẳng phụ không đổi hình (LỖI, đã sửa `824924d7`)

- **Gốc:** `geometryTimeline` mở bước ở sự kiện `GEOMETRY_CONSTRUCTION` làm đổi chữ ký hình; mặt phẳng qua A, B, C (chỉ
  là toán hạng của chiều cao) có trong chữ ký dù cảnh trung tính không vẽ nó ⇒ bước «Mặt phẳng qua A, B, C» không đổi
  hình khi hình phụ tắt — trái bất biến W12. W2 nới ba cổng (`no_static_frames`, phép miễn `a` của tham chiếu cấu trúc
  qua `stepOnlyBuildsHiddenHelper`, `every_geometry_step_changes_the_figure`) và thêm chú thích «hình phụ, đang ẩn».
- **Sửa:** `measurementOnlyPlanes` (scene3d-model) là thẩm quyền duy nhất của loại hình phụ ĐO; `_chuKyHinh` bỏ qua nó
  ⇒ sự kiện chỉ dựng nó nhập vào bước trước, không phụ thuộc công tắc. `scene3d-auxiliary` đọc cùng tập. Chú thích và CSS
  của nó gỡ (thành mã chết). Oracle bộ đo cài độc lập (`matPhangChiDeDo`); miễn trừ của W2 gỡ ở cả hai cổng.
- **Test đỏ trước:** `scene3d-steps-panel.test.tsx` (bước tĩnh `[8]`; bước mặt phẳng có trong danh sách; đối chứng 9 ≠ 10),
  node test (`[[0,0],[1,1],[2,2]]` ≠ `[[0,0],[1,2]]`). Test W2 khẳng định chú thích được thay bằng test mới (hành vi đổi có chủ đích).
- **Kết quả đo:** chóp đều còn 8 bước; phát lại "mọi bước dựng đổi hình" xanh ở 14/14 lượt không có miễn trừ.

## 4. H-W2-2 — đáp số là đoạn chưa được dựng (LỖI, đã sửa `45beaed3`)

- **Gốc:** luật A của W2 (nhãn độ dài chỉ khi đoạn mang nó đã dựng — yêu cầu người dùng) đúng; nhưng chương trình
  "Tính độ dài đoạn SH" chỉ đo d(S, H) và không dựng SH ⇒ chọn đáp số không còn gì trên hình. Kỳ vọng W18
  (`annotation_id: d_kq`) bị W2 hạ thành `annotation_absent_id` (PC1-W2) — hạ cổng.
- **Phương án loại:** vẽ nhân chứng S–H ở frontend — trái yêu cầu A (đoạn không được "dựng").
- **Sửa:** bước bổ sung dựng hình (`formation._doan_duoc_hoi`, một thẩm quyền với SO của W2): witness của nghĩa vụ là
  khoảng cách giữa HAI ĐIỂM mà chưa đoạn/cạnh đa giác/cạnh mặt khối nào nối chúng trước phép đo ⇒ `construct_segment`
  "Đoạn SH" ngay trước phép đo, tên theo thứ tự đề viết ("đoạn AK" dù chương trình đo d(K, A)). Khoảng cách tới
  đường/mặt giữ nhân chứng W18. Kỳ vọng W18 khôi phục; nhánh `annotation_absent_id` của suite gỡ.
- **Test đỏ trước:** `test_regular_square_pyramid_w03.py` (không có đoạn SH), `test_mocked_production_e2e.py` (`doan_KA` ≠
  `doan_AK`). Ba đối chứng: đoạn đã có không dựng lần hai, điểm–đường không thêm đoạn, không phải witness không thêm gì.
- **Giới hạn đã biết:** đoạn được hỏi nằm trên một cạnh có sẵn mà không trùng hai đầu mút sẽ vẽ chồng
  (`ISSUE-ARCH-ASKED-SEGMENT-OVER-EXISTING-EDGE`).
- **Kết quả đo:** `projection_correct` desktop + mobile: `annotation_present` d_kq PASS; ảnh `served.png` có «Dựng đoạn SH».

## 5. Cache và candidate

- **Cache** (`diagnostics/PROOF_CACHE_ROW_W03.json`, script `proof_cache_row_w03.py`, sqlite tạm, 0 lượt gọi): 58 row —
  corpus W2 (34, trùng byte), corpus construction-binding, một đối chứng điểm–đường. 13 envelope phục vụ dưới 113 vẫn
  HIT dù W3 dựng khác (các ca khoảng cách hai điểm: B1, B3, B6, B8, B10, B12, B14, B15, B17, B18, B20, B22, B23); bump giả
  lập làm chúng MISS ⇒ **113 → 114**. Chứng minh chạy sau khi đã bump trong mã, nên trường `cache_version_current` ghi 114
  và bump giả lập là 115 — logic không phụ thuộc số. Envelope trước/sau để ngoài kho; sha256 `090f4e9d…` (trước,
  worktree `fe68b4ca`) / `0a474135…` (sau).
- **Candidate:** một lần đóng băng tại `45beaed3` trong worktree tách rời sạch `D:/tmp/rsp w03b`; `d3de9c44` → **`5dec4572`**
  (110 file); `--verify` khớp ở worktree và cây chính (`diagnostics/logs/FREEZE_45beaed3.log`). Khai ở lớp mới
  `inputs/CANDIDATE_DIVERGENCE_CORRECTION.json` (đính chính lớp W2) và `CANDIDATE_DIVERGENCE.json`.

## 6. Đo có thẩm quyền

`MEASUREMENT_ATTEMPTS.json`. Lượt 1 tại `47941832` dừng ở cổng provenance (`PRODUCT_PROVENANCE_MISMATCH`: tệp kịch bản
ghim `product_tree_sha` cũ — bản đóng băng chỉ dời `product_commit_sha`) trước mọi lượt trình duyệt; sửa `a5d233ce`.
Lượt 2 tại `a5d233ce` (worktree `D:/tmp/rsp w03b`, sạch, có dấu cách) — bằng chứng `0d0d1de3`:

| Cổng | Kết quả |
|---|---|
| candidate / cache verify trước khi đo | `5dec4572` khớp; khoá 114 khớp |
| suite | 7/7 họ PASS; 14/14 lượt dương xanh trọn (camera lắng ở mọi trạng thái; causal_restore mọi họ, kể cả thiết diện desktop + mobile) |
| ca phục vụ | `projection_correct` d_kq có nhãn (H-W2-2), `point_construction_witness`, `correct_plane` PASS |
| đầu dò W2 | 14/14 |
| occlusion | pass, 0 lỗi, `HUMAN_REVIEW_PENDING` (4 cảnh W14, U2) |
| phát lại | PASS; mọi bước dựng đổi hình, không miễn trừ |
| builder | 68 crop, đầu mút trong khung, 0 bất đồng oracle, 0 chủ sở hữu trùng |

T3 và cổng danh tính tại commit cuối: ghi ở `HANDOFF.md` §2 và commit kèm log (`diagnostics/logs/T3_*`, `GATES_*`).

Kiểm trong cây chính trước commit sản phẩm: vitest 1091/1091; node harness 84 pass / 0 fail; tsc + vite build (ra thư
mục tạm — `frontend/dist/assets` ở cây chính bị một tiến trình khác khoá, `EPERM`, lỗi môi trường); pytest 7143 passed /
13 failed — 11 do candidate cũ trước khi đóng băng lại, 2 do cây chính bẩn (xoá favicon của người dùng), không lỗi hành vi.

## 7. Không làm

Không mở họ hình mới, không chuyển kiến trúc, không đổi bề mặt mô hình, không gọi live, không merge/push/PR, không ghi
`APPROVED_BY_USER`, không sửa artifact W1/W2 (PC1-W2 được đính chính bằng lớp W3 — `EVIDENCE_INDEX.md`). H-W2-3 và H-W2-5
không đổi (lựa chọn trình bày — `REVIEW.md` §3).

## 8. Skill thực dùng

`superpowers:verification-before-completion`, `superpowers:systematic-debugging`, `superpowers:test-driven-development`
(được gọi trong phiên). Không tạo subagent. Google Drive MCP cần cấp quyền — không dùng.
