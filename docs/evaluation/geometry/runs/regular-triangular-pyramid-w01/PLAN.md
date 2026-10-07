# regular-triangular-pyramid-w01 — REGULAR_TRIANGULAR_PYRAMID_AND_TETRAHEDRON_SLICE · kế hoạch

Viết TRƯỚC mọi thay đổi sản phẩm của run này (2026-10-07). Nhãn corpus: `diagnostics/corpus/LABELS.json`; luật đăng
ký: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §18.

## 0. PRE-FLIGHT (`docs/RULES.md` §2)

```text
Active branch:        feat/regular-square-pyramid (giữ theo lệnh người dùng: "không đổi nhánh chỉ vì tên nhánh khác
                      tên nhiệm vụ"; RUN_NAMING muốn việc mới rẽ từ main đã tích hợp — lệch có chủ ý, ghi ở RUN.json)
HEAD:                 0d4c4f8b (phần dọn Tin học đã commit) trên e9435d67 (W5)
Working tree:         D frontend/public/favicon.svg (của người dùng, không stage)
Current milestone:    W5 của regular-square-pyramid chờ duyệt hình; việc này là lát cắt họ kế tiếp W5 REPORT §7 đề xuất
Task classification:  CORE (họ hình mới trên tuyến sản phẩm) + SUPPORTING (sửa giao diện D, bớt ảnh E)
Thesis relevance:     hình học không gian Toán 11–12 — chóp tam giác đều, tứ diện đều
Existing modules:     shape_constraint (từ vựng đóng), segment_relation (độ dài nguồn, chuỗi bằng nhau W05),
                      assumption_gate (T1–T7), formation (_tam_day_deu), construction_binding (§16 "centre"),
                      grounding_gate (GIVEN căn đã so bằng chữ), quantity_annotations, scene3d (nhãn sự kiện)
Reuse:                MAU_DO_DAI/_cac_doan (chuỗi), _Khuon/_KichThuoc/_ham_keo/_doi_chieu_chinh_tac, radical.square/
                      sign/parse_exact/display/sqrt_rational, QuanHeDung/_so, _tam_day_deu
Source of truth:      đề (câu chữ) cho tiền đề; kernel ℚ³ cho toạ độ; radical.py cho số đo
Files expected:       backend/app/simulation/semantic_program/{segment_relation,shape_constraint,assumption_gate,
                      formation,construction_binding,grounding_gate,postconditions,refusal_cause,scene3d}.py,
                      product_capability.py; frontend geometry (Scene3DExplorer, scene3d-view, scene3d-model,
                      interaction-state, scene3d-playback), global.css; frontend/scripts runner (ảnh)
Contract/cache:       lược đồ IR KHÔNG đổi; prompt/thẻ văn phạm KHÔNG đổi; envelope thiết diện đổi nhãn bước ⇒
                      quyết CACHE_VERSION bằng bằng chứng row; candidate đóng băng lại
Duplicate risk:       bộ đọc độ dài thứ hai — tránh: một mẫu số độ dài trong segment_relation, dùng chung
Dependency-cycle:     shape_constraint không import assumption_gate; formation đã import shape_constraint
Scope-creep risk:     khung đồng dạng λ, toạ độ ℚ(√3), trung đoạn chóp tam giác, góc — KHÔNG làm
Smallest:             §18 của amendment (đọc + T8 + độ dài căn + binding trọng tâm) + xoay hiển thị renderer
Excluded:             OCR, solver tổng quát, compiler-first, họ hình khác, đổi bề mặt mô hình, live call
Stop conditions:      cần đổi kernel/toạ độ; cần đổi prompt để có ca nào chạy; hồi quy bảy họ không sửa được trong
                      thẩm quyền đúng
```

## 1. Biểu diễn — kiểm sớm (quyết định người dùng 2026-10-07: MIỀN HẸP ℚ³)

Toạ độ ℚ³ (`exact.Vec3`, `hf()` từ chối vô tỉ). Tam giác đều đỉnh nguyên có cạnh² ∈ {2, 6, 8, 14, 18, 24, …}
(dò vét `|x|,|y|,|z| ≤ 4`, không cạnh² chính phương) — cạnh² = 2·N với N chuẩn Eisenstein, và 2 trơ trong ℤ[ω] ⇒
không tam giác đều cạnh HỮU TỈ nào có toạ độ hữu tỉ. Mặt phẳng chứa tam giác đều hữu tỉ có pháp tuyến n với |n|² =
3d² ⇒ chiều cao từ đỉnh tới đáy là bội hữu tỉ của √3. Miền hỗ trợ khai ở §18.2: cạnh đáy² ∈ {2k², 6k²}, chiều cao²
= 3t² (k, t hữu tỉ). Ngoài miền ⇒ `TEMPLATE_NOT_REPRESENTABLE T8` (từ chối, không làm tròn). Phương án bị bác:
khung đồng dạng λ (chạm interpreter/measure/postconditions/grounding — rủi ro đáp số sai lặng lẽ), "chỉ khai giới hạn".

## 2. Bảng phạm vi (mục B)

| Yêu cầu | Đã có | Còn thiếu | Caller dùng | Kiểm |
|---|---|---|---|---|
| "chóp tam giác đều S.ABC" là ràng buộc | `_KHOI_CHOP` nuốt chữ "tam giác đều" (không phát) | phát `regular_triangular_pyramid` + `base_equilateral` | `assumption_gate._khuon_chop` (T8), `formation._tam_day_deu`, `phan_chua_doc` | `test_regular_triangular_pyramid.py` (bộ đọc), nhãn P1 |
| tứ diện đều ABCD | không đọc "tứ diện" | `pyramid(A,B,C,D)` + `regular_tetrahedron` + cạnh | như trên | P3, U2 |
| "tất cả các cạnh bằng a" | không | `regular_tetrahedron` + `edge_all` | T8 | P4 |
| `AB = BC = CA = b`, `SA = SB = SC = a` | chuỗi bằng nhau (W05) cho số hữu tỉ | số căn `k√n` trong độ dài nguồn | grounding, bất biến nguồn, T8 (đáy đều/cạnh bên bằng nhau suy từ độ dài) | P5, P6, N8 |
| đáy đều ⇒ chân đường cao = trọng tâm | T7 (tâm hình vuông) | T8: đáy đều + chân ở trọng tâm, nguồn h: chiều cao/SG/cạnh bên/tứ diện | `kiem_gia_dinh` trên route | P1–P11, N1–N9 |
| trọng tâm có danh tính | `centre` (§16, giao hai đường chéo) | `centroid`: giao hai trung tuyến, hoặc `divide_segment(đỉnh, trung điểm cạnh đối, 2/3)` | `formation._tam_day_deu` (chân đường cao), `construction_binding` | P9, N6 |
| số đo căn: chiều cao √3, diện tích 9√3/2 | `radical.py`, `geometry_exec` | không | `quantity_annotations`, scene | P1 (scene) |
| ngoài miền biểu diễn | — | `TEMPLATE_NOT_REPRESENTABLE T8` | `kiem_gia_dinh` | U1–U4 |
| khung nghiêng hiện đúng chiều | camera z-up khoá (`scene3d-zup-lifecycle`) | phép xoay TRÌNH BÀY đưa pháp tuyến đáy chóp về +z | `scene3d-view` (nhóm gốc, nhãn, khung) | vitest + ảnh duyệt |
| D1 thể tích thiết diện trống | ô soi chỉ hiện giá trị trong công thức | giá trị luôn hiện; nguồn hình học khi không có nguồn số | `Scene3DExplorer` | vitest + ảnh |
| D2 chọn SO / S(đáy) | chuỗi nhân quả theo `depends` | chủ thể của nhãn đại lượng vào tầng đích | `tangNhanManh` (mọi nơi gọi) | vitest + ảnh |
| D3 icon điều khiển | `.geo3d-btn` không flex | inline-flex, gap token | `scene3d-playback` | ảnh |
| D4 tên bước trùng | nhãn sự kiện thiết diện = nhãn thiết diện | nhãn riêng mỗi cạnh ("Giao tuyến với mặt SAB"); lời kể không lặp tiêu đề | `scene3d.build_scene_events`, bảng bước | pytest + vitest |
| D5 mobile | canvas cao, hình bám chiều rộng | đo trước; chỉ sửa nếu không làm hình nhỏ | `scene3d-playback` | đo kích thước hình px |
| D6 camera | W5 giữ khung qua bảng/bước | kiểm, không đổi | — | đầu dò W05 |
| E ảnh | runner chụp mọi trạng thái (W5: 768 ảnh) | chính sách lưu: bắt buộc / duyệt / lỗi | `compiler-scene-suite.mjs` + đầu dò | node harness |

## 3. Thứ tự

1. Nhãn + oracle độc lập + §18 (commit riêng, trước sản phẩm). 2. Backend theo §18, test đỏ trước. 3. Renderer xoay
trình bày + D1–D6. 4. Fixture họ mới + bộ đo tám họ. 5. Chính sách ảnh. 6. Đóng băng candidate, đo trong worktree
sạch, T3. 7. Tài liệu sống + REPORT/HANDOFF/REVIEW.
