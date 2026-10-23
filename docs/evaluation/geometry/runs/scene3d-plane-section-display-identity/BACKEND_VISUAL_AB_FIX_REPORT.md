# Sửa lỗi hiển thị A/B ở backend (tuyến D, Adapter /4)

Authorization `GO_LOCAL_PUBLICATION_REMEDIATION_MERGE_AND_BACKEND_VISUAL_AB_FIX`. Nhánh
`research/scene3d-plane-section-display-identity` từ local `main` = `50cee9035d664d7d3d39762610af740a8b8cd558`.
**Chưa merge vào `main`.** 0 lượt gọi model.

## 1. Gốc lỗi (tái hiện từ dữ liệu, có nền đỏ)

| lỗi | gốc | bằng chứng |
|---|---|---|
| **A** `(MHH1)` thay vì `(α)` | Thẩm quyền đặt tên dùng chung (`display_names.py`) chỉ giữ tên khai làm ký hiệu khi `prefer_declared_plane_names=True`; `function_route.py` chỉ bật cờ cho mặt hai-đường (`MAT_HAI_DUONG`). Mặt "qua M ∥ (ABC)" dựng bằng hai điểm tịnh tiến H, H1 ⇒ ký hiệu ghép `(MHH1)`, lọt vào `notation` (nhãn canvas, `kyHieu`) và `reference` (inspector, `Scene3DExplorer.tsx::ten`). Test review round 2 chỉ kiểm role/events/steps, phân biệt hoa thường ⇒ bỏ sót `reference`/`notation` và role "Mặt phẳng qua M, H, H1" | nền đỏ: 22/22 cảnh có thiết diện đỏ A |
| **B** "Thiết diện HMH1" / "Đỉnh 1 – M – Đỉnh 3" | Lăng trụ đứng: H = M + AB ≡ I (BB′∩(α)), H1 = M + AC ≡ I1 (CC′∩(α)), trùng chính xác. `simulation_state.py` gọi tên chu trình thiết diện bằng điểm có tên **đầu tiên** trùng toạ độ ⇒ "HMH1", tức đặt tên cho hai đỉnh `STATED_UNNAMED` qua điểm phụ; lan sang đại lượng `Diện tích HMH1` / `S(HMH1)`. Frontend `_banDoDiem` cố ý không đặt tên khi hai điểm trùng ⇒ "Đỉnh k" | nền đỏ: test B lăng trụ |
| **B′** (cùng họ, phát hiện khi rà) | `PLANE-ONLY-ratio-described`: nhánh `else` của `_an_dinh_thiet_dien_phu` dán nhãn **"Đoạn của thiết diện"** cho đại lượng thể tích và tỉ số; `formula.text` lộ `V(S.MII1)` | nền đỏ: test B′ |

`simulation_state.py`/`display_names.py` dùng chung với tuyến mặc định LLM_ONLY ⇒ **không sửa ở đó** (sẽ đổi envelope mặc định, trái `CACHE_VERSION=127`). Mọi sửa nằm ở lớp trình bày chỉ của tuyến D.

## 2. Sửa (`backend/app/ai/function_route.py`, product commit cuối `41c7e6f8`)

Chuỗi: `ec17602a` (bản đầu) → `665f542c` (agent tự rà diff: giữ văn bản event của thiết diện) → `41c7e6f8` (review F1–F3).

1. `run_function_route`: `prefer_declared_plane_names` bật cho **mọi** mặt thiết diện dẫn xuất (`MAT_SONG_SONG`, `MAT_VUONG_DUONG`, `DINH_CAT_CANH`; hai-đường đã bật từ trước), có hay không có cạnh cắt được khai ⇒ mặt cắt mang `(α)` ở `label`/`display_label`/`reference`/`notation`. Id, `depends` (H, H1, M), toạ độ, phép dựng giữ nguyên.
2. `_an_dinh_thiet_dien_phu`: tên ghép `(MHH1)` dựng lại từ **thứ tự toán hạng của planner** (`d["plane"]`; `depends` bị sắp chữ) để thay trong role/label/reference của các vật nhắc tới mặt toán hạng (ví dụ "Giao điểm của SB và (MHH1)").
3. Thiết diện của mặt cắt có đỉnh không tên **không giữ chu trình**: "Thiết diện bởi (α)", `notation = None`, giống mọi thiết diện có đỉnh không tên khác. Event của nó giữ nguyên văn bản (chỉ thay tên chu trình cũ, giữ hoa/thường).
4. Đại lượng dựng trên vật đã đổi tên giữ **loại** ("Diện tích…", "Tỉ số…", "Thể tích…"), `notation = None`, tên trong `label`/`formula.text`/event được thay bằng cách gọi mô tả.
5. `_vai_mat_cat` (mới): role của mặt cắt nói đúng quan hệ nguồn: "Mặt phẳng qua M và song song với (ABCD)" / "… vuông góc với SA" / hai-đường. Mặt tham chiếu được gọi **đúng như câu nguồn viết** (mặt của khối chứa điểm tham chiếu, hoặc điểm của planner, chọn cái mà quote chứa).
6. `_thay_ten` (mới, cấp module): thay ký hiệu cũ như một **tên trọn**, không bao giờ bên trong tên có dấu chấm/phẩy trên ("MII1" trong "S.MII1"); giữ chữ hoa đầu câu.

Hai freeze trung gian bị thay: `f8ec3222` (chưa đo) và `8efb32b4` (đã đo: T3 PASS + browser PASS tại `65cbdd6f`; giữ làm bằng chứng trung gian ở `verification/superseded-665f542c/`).

## 3. Trước/sau (từ `results/adapter4-export-final/before-after.json`, 22 cảnh, 94 trường tên)

| cảnh | trường | trước | sau |
|---|---|---|---|
| 19 cảnh | `mp_td_*.notation` / `reference` | `(MHH1)` | `(α)` |
| 2 cảnh ⊥ | `mp_td_*.notation` / `reference` | `(MH2H3)` | `(α)` |
| `RELABEL-TDEF` | `mp_td_*.notation` / `reference` | `(KHH1)` | `(α)` |
| 22 cảnh | `mp_td_*.role` | "Mặt phẳng qua M, H, H1" | "Mặt phẳng qua M và song song với (ABC)" (16), "… (ABCD)" (3: DEV01, DEV09, PARTIAL-2of3, đúng chữ của đề), "… vuông góc với SA" (2), "qua K … (DEF)" (1) |
| prism | `td_sp` label / notation | "Thiết diện HMH1" / `HMH1` | "Thiết diện bởi (α)" / `null` |
| prism | `kq_g_area` | "Diện tích HMH1", `S(HMH1)`, "S(HMH1) = √3/4" | "Diện tích thiết diện bởi (α)", `null`, "S(thiết diện bởi (α)) = √3/4" |
| plane-only ratio | hai đại lượng | "Đoạn của thiết diện", "V(S.MII1)/V(S.ABC) = 1/8" | "Thể tích khối chóp đỉnh S cắt bởi (α)", "Tỉ số của V(khối chóp đỉnh S cắt bởi (α)) và V(S.ABC)", "V(khối chóp đỉnh S cắt bởi (α))/V(S.ABC) = 1/8" |
| plane-only ratio | 2 event + 2 bước | "Nối các giao điểm của thiết diện." (sai) | văn bản gốc của đại lượng, tên khối được thay |

Không đổi (assert trong `export_fixtures.py` và guard `test_presentation_fix_moves_no_geometry_provenance_answer_or_order`): mọi khoá, độ dài danh sách và giá trị không phải tên; id, type, xyz, depends, polygon, origin, render; giá trị `formula.value`/`value`; thứ tự event (object, action, step_index); `visible_ids` của từng bước; toàn bộ `route_d` (sections, provenance, closure certificate, answers, answer_exact) ở cả 22 cảnh; 25 refusal giống Session 5.

## 4. Còn lại, cần Owner quyết

- Inspector lăng trụ vẫn "Các đỉnh: Đỉnh 1 – M – Đỉnh 3": frontend tra đỉnh theo toạ độ và cố ý bỏ tên khi hai điểm ngữ nghĩa trùng (H ≡ I). Trung thực, nhưng kém thông tin. Review F4 chỉ ra có thể sửa **ở frontend bằng dữ liệu đã có** (`endpoint_entities`, nhãn mô tả của I/I1), không cần đổi contract; nhưng `sectionDetails` dùng chung với tuyến mặc định ⇒ không làm trong phạm vi "chỉ sửa backend". Phương án: `SCENE3D_PROVENANCE_COMPATIBILITY.md` §4. Trên canvas, nhãn H, H1 vẫn hiện tại hai đỉnh (điểm dựng phụ có thật của planner).
- R1: `explanation` của event dựng mặt phẳng còn "qua ba điểm M, H, H1" (không render khi có `learner_text`).
- F5: `envelope.config.frames[].narration` còn tên điểm dựng (không render trên đường Scene3D, có trong payload API).
- Nhánh "khối không có `kd`" trong `_an_dinh_thiet_dien_phu` chưa fail-closed (không với tới từ corpus).

## 5. Kiểm

| kiểm | kết quả |
|---|---|
| nền đỏ trên mã `main` | 26 đỏ (22 A + 2 B + 2 test cũ mở rộng), 22 guard xanh |
| sau sửa | `test_section_display_identity.py` + `test_typedfactnext_planner_bridge.py`: 117 passed |
| assert hồi quy (văn bản event thiết diện) | đỏ trên `c276b785`, xanh từ `665f542c` |
| nền đỏ cho review F1–F3 | 8 đỏ trước `41c7e6f8` (F1 1, F2 3, F3 4), xanh sau |
| tiêm lỗi (trên `ec17602a`) | bỏ cờ tên khai: 24 đỏ · tắt luật chu trình: 2 đỏ · tắt đổi tên đại lượng: 3 đỏ · bỏ role nguồn: 24 đỏ |
| quét toàn `tests/geometry` sau `41c7e6f8` (trước freeze) | 9,211 passed; chỉ 11 test họ "candidate cũ" đỏ, giải bằng freeze `56bdf9b9` |
| export Adapter /4 cuối | 47 case, 22 served / 25 refused, 0 network, chỉ đổi trường tên (94) |
| Full T3, browser, review | `FINAL_OWNER_HANDOFF.md` |
