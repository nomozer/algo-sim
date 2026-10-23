# Nghiệm thu giao diện còn mở: Adapter /4 offline consumer

**Phân loại: `VISUAL_FIX_REQUIRED`** (A và B tái hiện được từ dữ liệu cảnh; sửa nằm ở backend, chưa sửa).
C và D đạt kiểm máy. **Human visual approval: `PENDING`.** Agent không ghi `HUMAN_VISUAL_APPROVED`.

Nguồn: 6 PNG của `hybrid-offline-consumer/results/browser-final-9f06ed2b/` (SHA-256 khớp receipt) và envelope Scene3D
thật của các fixture đó (`results/fixtures.json` → `row.reference` → bundle lịch sử, kiểm băm như harness Session 5).

## A. `(MHH1)` so với `(α)`

| lớp | giá trị trong cảnh `CORPUS-DEV10-prism-area` (giống hệt ở `PARA-0`, `PARTIAL-1of2-construct`) |
|---|---|
| nguồn đề | bridge khai `declared_plane_names: {sp: "α"}`; đề gọi mặt phẳng là (α) |
| toán học | `mp_td_sp`: mặt phẳng qua M, H, H1; H = M + AB, H1 = M + AC (điểm phụ planner dựng để có mặt song song với (ABC)); đúng mặt (α) |
| định danh | hai vật cùng mặt: `derived_I_plane` (`non_visual`, nhãn (α)) và `mp_td_sp` (`surface`) |
| nhãn hiển thị | `mp_td_sp.display_label = "(α)"`, **`notation = "(MHH1)"`, `reference = "(MHH1)"`** |
| frontend | `Scene3DExplorer.tsx:312` `ten()` ưu tiên `reference` ("cách gọi ngắn" backend dựng riêng cho vai này), nên dòng "Mặt phẳng cắt" và nhãn trên canvas hiện `(MHH1)`, trong khi mô tả thiết diện (role do backend phát) nói "cắt bởi (α)" |

**Kết luận: lỗi thật, trái quyết định đã duyệt.**
`backend/tests/geometry/test_typedfactnext_planner_bridge.py::test_cut_vertices_and_their_operand_planes_speak_the_source_plane_name`
(review round 2, IMPORTANT 2) ghi: tên ghép từ điểm `(MHH1)` *"never reach the learner; the source name (α) does"*. Test đó
chỉ kiểm `role`, `events` và `formation`. Nó bỏ sót trường `reference`/`notation`, mà frontend hiển thị. Frontend dùng
`reference` đúng hợp đồng của nó, nên gốc lỗi nằm ở backend: `display_names.py` chỉ lấy tên khai làm ký hiệu khi
`prefer_declared_plane_names=True`, còn `ai/function_route.py:191` chỉ bật cờ đó cho mặt dựng kiểu hai-đường
(`MAT_HAI_DUONG`). Mặt "qua điểm, song song mặt" dựng bằng H/H1 nên không được bật.

## B. `Thiết diện HMH1` với "Đỉnh 1 – M – Đỉnh 3"

| đỉnh polygon (thứ tự kernel) | toạ độ chính xác | điểm ngữ nghĩa ở đó | `route_d.sections` |
|---|---|---|---|
| 1 | (1, 0, 1/2) | **H** (phụ, tịnh tiến) **và I** (giao BB′ ∩ (α), `notation null`) | I, `STATED_UNNAMED` |
| 2 | (0, 0, 1/2) | M | M, `THROUGH_POINT_REUSE` |
| 3 | (0, 1, 1/2) | **H1 và I1** (giao CC′ ∩ (α)) | I1, `STATED_UNNAMED` |

- Toán: đúng. H ≡ I, H1 ≡ I1 trùng chính xác (lăng trụ đứng, tịnh tiến theo AB/AC rơi đúng lên BB′/CC′). Chu trình
  H→M→H1 trùng thứ tự polygon. Thiết diện plane-only, `closure_certificate = null`, đã khai từ Session 5.
- Tiêu đề "Thiết diện HMH1": backend ghép từ ký hiệu các điểm có tên tại đỉnh, nên chọn H/H1, là điểm phụ không có trong đề.
- "Đỉnh 1 / Đỉnh 3": `scene3d-subentities.ts::_banDoDiem` cố ý trả `null` khi **hai** điểm ngữ nghĩa trùng toạ độ
  (luật khử nhập nhằng có ghi lý do trong code), nên rơi về "Đỉnh k".
- **Kết luận: lệch trình bày tái hiện được**, gốc ở backend: cảnh phát hai điểm ngữ nghĩa trùng nhau (điểm phụ dựng mặt
  và giao điểm). Frontend làm đúng luật của nó. Không có sai về hình học.

## Vì sao chưa sửa A/B ở lượt này

Chỗ sửa nằm trong `backend/app` (measured system, tuyến Hybrid D). Sửa sẽ đổi envelope `/4`, vốn đang được pin là
fixture lịch sử bất biến (`results/fixtures.json` kiểm `envelope_sha256`). Nó cũng buộc quyết lại assert
`notation != "(α)"` đang bị khoá. Hệ quả kéo theo: candidate mới, đóng băng lại, review độc lập, browser acceptance và
Full T3. Owner đã ghi "không triển khai lại Hybrid Backend", nên việc này cần GO riêng.
Hướng sửa đề xuất (cho Owner chọn):

1. Backend, trong một thẩm quyền: khi bridge khai tên mặt phẳng, dùng tên đó cho `reference` của mặt cắt (giữ
   `notation` nội bộ nếu cần cho khử trùng), và mở rộng test IMPORTANT 2 để kiểm cả `reference`.
2. Backend: không phát điểm phụ H/H1 như điểm ngữ nghĩa có nhãn khi chúng trùng giao điểm đã khai (hoặc ẩn như
   `aux_hidden_points` của Adapter /3); tiêu đề thiết diện khi đó thành "Thiết diện bởi (α)".
3. Không sửa frontend: `ten()` và `_banDoDiem` là hành vi của sản phẩm mặc định (LLM_ONLY) và đang đúng hợp đồng.

## C. Màn từ chối

Harness mới `check_refusal_screens.mjs` (0 lượt gọi model, không backend) nạp mỗi fixture từ chối **ngay sau** một cảnh
served `PARA-0` đã có canvas, ở 1440×900 và 390×844. Receipt: [`refusal-screens/receipt.json`](refusal-screens/receipt.json).

| kiểm | kết quả |
|---|---|
| hàng | 50/50 PASS (25 fixture × 2 viewport); `REFUSAL_SCREEN_CHECK_PASS`, source `76c6795c`, `tree_clean: true`, harness SHA-256 `e6305a61…` |
| canvas sau khi từ chối | 0 ở mọi hàng (canvas cũ đã gỡ) |
| thông điệp người học (`learner_reason`) hiện | mọi hàng |
| mã từ chối / tên nội bộ (`_`, `::`) lộ | 0 |
| tiêu đề cảnh cũ còn sót ("Thiết diện MNPQ") | 0 |
| tràn ngang | 0 |
| lỗi trang/console, request bị chặn | 0 / 0 |
| ảnh | 20 PNG = 10 mã × 2 viewport (một ảnh đại diện cho mỗi mã) |

Ghi chú cho Owner khi xem ảnh: dải cam "Máy chủ thiếu khóa AI" đến từ `/api/health` giả lập `allow_live_ai: false`
của harness, không phải trạng thái sản phẩm. Dòng "Dừng ở bước: Không xác định được" là nội dung sản phẩm hiện hành; Owner xem có chấp nhận không.

## D. Ratio / residual

- Chính sách hiện hành: simulation-first, đáp số ẩn khỏi UI người học. Kiểm trong mã: `Scene3DExplorer.tsx:546` chỉ đọc
  `hybridTaiBuoc(...).observations`; `answers` và `giaTriDapSo` không được render ở UI người học (chỉ dùng trong test và
  readout operator của harness).
- Giá trị: `PARA-0` `g_ratio = 1/8`, `g_res = 7a³/24`, khớp oracle (`oracle_answers_match` true, `answers_bound_in_scene`
  true), có kiểm ở `adapter4-consumer.test.tsx` (vitest xanh, `POST_MAIN_REGRESSION_REPORT.md`).
- Không tự bật hiển thị đáp số. Ảnh `PARA-0` chỉ cho thấy cảnh và khối con S.MNPQ, không có số. Đúng chủ ý.

## Bản ghi Owner (agent không điền)

| mục | quyết định | ghi chú |
|---|---|---|
| A `(MHH1)`/(α) | PENDING | |
| B HMH1 / Đỉnh k | PENDING | |
| C màn từ chối (20 ảnh) | PENDING | |
| D ẩn đáp số | PENDING | |
| 6 ảnh Session 5 | PENDING | |
