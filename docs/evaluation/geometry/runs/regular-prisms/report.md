# regular-prisms — báo cáo (G05)

Nhánh `feat/g05-regular-prisms` từ `ea85216b`. Cloud, 0 lượt gọi model, `LLM_ONLY` mặc định, compiler opt-in, frontend
không đổi. Tiền đăng ký `680d830` (khảo sát + ma trận năng lực, 25 nhãn, oracle độc lập, probe baseline) trước mọi sửa
sản phẩm; sản phẩm `00770c3` + sửa `d8b9da7`. Kết luận: **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`**.

## A. Bằng chứng năng lực

**Lát cắt:** lăng trụ lục giác đều (ưu tiên) và lăng trụ tam giác đều — cùng một cơ chế, không refactor rộng: khuôn
**T12** trên hợp đồng khung affine + metric dẫn xuất từ đề của T8/T11. Không engine hình học thứ hai; `solid_topology`
chỉ là vũ trụ đỉnh của grounding, không phải bằng chứng; không mã ca, đáp số hay tên đỉnh trong sản phẩm.

**Phép dùng chung mới:** (1) bộ đọc: `lăng trụ tam giác/lục giác đều X.Y` ⇒ `right_prism` + đáy đều đúng tập đỉnh đáy;
`lăng trụ đứng … có đáy … là lục giác đều` (tam giác đều đã có); cạnh đáy / cạnh bên của lăng trụ đều duy nhất; phủ định
và mệnh đề mục tiêu không thành tiền đề; (2) khuôn T12 — mặt trên tịnh tiến của đáy, cạnh bên ⊥ mọi cạnh đáy và đáy đều
**theo metric**, cạnh đáy, chiều cao; (3) một thẩm quyền kích thước `kich_thuoc_t12` (chiều cao từ "chiều cao" hoặc "cạnh
bên"; hai nguồn khác nhau ⇒ mâu thuẫn); (4) `do_luong_cua` dẫn xuất metric lăng trụ qua A, B, C, A′ (phần đuôi dùng chung
`_gram_khung`; nhánh chóp giữ nguyên); (5) C0 kiểm lục giác đều và cạnh bên lăng trụ trên toạ độ đề cho.

**Bài trước không giải được, nay giải đúng** (`results/transitions.json`; route sản phẩm, chứng chỉ C1, giá trị = oracle
`oracle.py`, Scene3D qua `_dung_scene3d` của pipeline):

| hàng | trước (`ea85216b`) | sau | Scene3D (đỉnh/mặt/cạnh) |
|---|---|---|---|
| X1 lục giác cạnh 2, chiều cao 3 | từ chối | V = 18√3 | 12/8/18 |
| X2 lục giác cạnh 2, cạnh bên 3 | từ chối | V = 18√3 | 12/8/18 |
| X3 đổi tên MNPQRS.M′…, 1 và 2 | từ chối | V = 3√3 | 12/8/18 |
| X4 cạnh √3, cao 2 | từ chối | V = 9√3 | 12/8/18 |
| X5 cạnh 1/2, cao 4 | từ chối | V = 3√3/2 | 12/8/18 |
| X6 "lăng trụ đứng … đáy là lục giác đều" | từ chối | V = 18√3 | 12/8/18 |
| X7 "khối lăng trụ lục giác đều" | từ chối | V = 18√3 | 12/8/18 |
| T1 tam giác cạnh 2, cao 3 | từ chối | V = 3√3 | 6/5/9 |
| T2 cạnh 2, cạnh bên 3 | từ chối | V = 3√3 | 6/5/9 |
| T3 "lăng trụ đứng … đáy ABC là tam giác đều" | từ chối (T3 cần góc vuông) | V = 3√3 | 6/5/9 |
| T4 cạnh 2√3, cao 1 | từ chối | V = 3√3 | 6/5/9 |
| T5 cạnh 2/3, cao 9 | từ chối | V = √3 | 6/5/9 |
| T6 đổi tên MNP.QRS, 4 và 1 | từ chối | V = 4√3 | 6/5/9 |

Mọi hàng phục vụ: khối đóng (Euler 2), mỗi cạnh thuộc đúng hai mặt, không mặt suy biến, 2 đáy k-giác + k mặt bên tứ giác,
`chart_metric` có mặt (`tests/geometry/test_regular_prisms.py::test_route_theo_nhan`).

**Biên vẫn từ chối (12/12, khớp nhãn):** thiếu chiều cao (NX1, NT1), chiều cao ≠ cạnh bên (NX2, NT2 —
`TEMPLATE_CONTRADICTION T12`), đáy chương trình không đều (NX3), mặt trên không tịnh tiến (NX4, NT3 — mặt không phẳng),
phủ định (NX5), mệnh đề chứng minh (NX6), ngũ giác đều (NX7, ngoài miền), lăng trụ xiên (NT4), đề không nói đáy đều (NT5).
Không đính chính nhãn.

**Ngoài nhãn** (`diagnostics/probe_extra.py`, hai cây): bố cục Euclid (không phải lưới) — đề cho chiều cao ⇒ phục vụ
đúng giá trị của ĐỀ (3/2; 3 khi đề nói 2√3 dù bố cục cao √3 — ngữ nghĩa khung affine, như T8/T11); đề thiếu chiều cao ⇒
`ASSUMPTION_DETERMINES_ANSWER`. C0 (toạ độ hữu tỉ, lục giác trên x + y + z = 0, tam giác (1,0,0),(0,1,0),(0,0,1)): khớp
⇒ phục vụ 9 / 3/2; cạnh bên không ⊥ đáy, cạnh bên hoặc cạnh đáy đề nói trái toạ độ ⇒ `SOURCE_SHAPE_CONTRADICTS_COORDINATES`.

**Đường chạy đã kiểm:** route sản phẩm của **LLM_ONLY** trên chương trình kiểu mô hình (đáy trong khung affine). **Chưa
đo** mô hình thật có tự sinh chương trình ấy ⇒ `regular_prism` = `foundation_only`. **Compiler:** không có họ này (opt-in,
không đổi). Không tuyên bố cải thiện Gemini/LLM_ONLY trên đề thật.

**Vẫn chưa hỗ trợ:** chóp/lăng trụ đều không tên, lăng trụ xiên đáy đều, ngũ giác đều, đáy theo góc, đáy lõm, đa giác toạ
độ trên compiler (`ISSUE-ARCH-G05-REMAINING-BASES`). Lăng trụ tứ giác đều: đường T3–T6 sẵn có, không đổi. Thiếu chiều
cao trên khung lưới: từ chối với `ASSUMPTION_INVARIANCE_UNPROVEN` (lý do kém cụ thể hơn bố cục Euclid, vẫn từ chối).

## B. Bằng chứng kỹ thuật

- Mã: `shape_constraint.py` (bộ đọc), `assumption_gate.py` (T12, `kich_thuoc_t12`, metric lăng trụ, `_gram_khung`, C0
  `base_regular_hexagon` + `lateral_prism`), `product_capability.py` (một dòng), `main.py` (cache). Amendment §27.
- Sửa trong lượt (trước commit sản phẩm, phát hiện bằng probe ngoài nhãn): `lateral_edge` trên lăng trụ từng bị C0 kiểm
  như cạnh bên CHÓP ⇒ đề C0 đúng ("cạnh bên bằng √3" khớp toạ độ) bị từ chối; nay ánh xạ sang `lateral_prism` (mọi AA′).
- Sửa sau so sánh toàn bộ pytest lần 1 (`d8b9da7`): ghim `test_shape_constraint` "lăng trụ đứng tam giác đều … 'đều'
  chưa đọc" đỏ — đúng thay đổi có chủ đích của T12; ghim chuyển sang "lăng trụ đứng tứ giác đều" (vẫn chưa đọc), cùng
  tính chất. Kiểm ghim ấy lộ "lăng trụ XIÊN tam giác đều" phát `right_prism` cạnh `oblique_prism`; nay danh từ có "xiên"
  không phát khẳng định T12 (đáy đều + xiên ≠ lăng trụ đều). Probe nhãn và ngoài nhãn không đổi.
- Test: `test_regular_prisms.py` 64/64 (oracle, 25 hàng route + Scene3D, bộ đọc, xiên, metric, bố cục Euclid, 8 cặp C0); nạp
  `cases.py` dưới tên module riêng (hai run cùng có `diagnostics/cases.py`). Bộ liên quan trong toàn bộ pytest.
- Không hồi quy: toàn bộ pytest (worktree sạch, cùng máy) `d8b9da7` 7589 passed / 136 failed / 4 errors; `ea85216b`
  7530 / 131 / 4 — 131 + 4 có sẵn trùng hệt; 5 đỏ mới = danh tính candidate (LOCAL đóng băng) —
  `results/pytest_compare.json`. Bộ liên quan (T7/T8/T11, C0 §21–§26, C1, Policy A, chóp đều, lăng trụ T3–T6/T9/T10,
  G04/G05, cổng giả định, bộ đọc) nằm trong đó.
- Probe các run trước (C1 chóp đều 235 dòng gồm Policy A, C0 của c0-whole-solid-grounding 29 + reader gap 3,
  c0-whole-solid-reader 27, unnamed-regular-pyramid-grounding 11, general-polygon-base C0 6, chóp lục giác đều 17):
  `ea85216b` ↔ `d8b9da7` trùng byte. 49/49 fixture Tier-A trùng byte (`cache/fixture_diff.json`). Demo 5/5, bề mặt sập 6/6 (0 lỗi 500) trên cả hai worktree.
- Cache: **`CACHE_VERSION` 124 → 125** (`cache/decision.json`): 6 đề C0 "lăng trụ … đều" có toạ độ mâu thuẫn từng phục
  vụ nay từ chối. Bề mặt mô hình không đổi; khoá sinh bằng script, `--verify` khớp; 7 ghim cập nhật. Candidate CHƯA đóng
  băng lại (LOCAL).
- Không chạy trên Cloud: T3 trình duyệt (frontend không đổi mã; hiển thị khung affine lăng trụ cần T3), mô hình thật.
