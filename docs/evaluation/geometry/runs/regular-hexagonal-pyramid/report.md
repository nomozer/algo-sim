# regular-hexagonal-pyramid — báo cáo (G05)

Nhánh `feat/g05-geometry-capability-expansion` từ `f20caf8a`. Cloud, 0 lượt gọi model, `LLM_ONLY` mặc định, compiler
opt-in, frontend không đổi. Tiền đăng ký `3357994` (khảo sát G05 + ma trận năng lực, 17 nhãn, oracle, probe baseline)
trước mọi sửa sản phẩm. Kết luận: **`CLOUD_IMPLEMENTATION_COMPLETE_LOCAL_VERIFICATION_REQUIRED`**.

## A. Bằng chứng năng lực

**Lát cắt:** chóp lục giác đều — khoảng trống G05 ROADMAP §0.2 nêu tên (đa giác đều ngoài hình vuông: toạ độ vô tỉ L06;
"lục giác đều" chưa grounding L03). Tái dùng cơ chế khung affine + metric dẫn xuất từ đề của T8; không engine mới.

**Phép dùng chung mới:** (1) bộ đọc: `regular_hexagonal_pyramid`, `base_regular_hexagon` cho ba lối viết + cạnh
đáy/cạnh bên của khối duy nhất; (2) khuôn **T11** (đáy lục giác đều theo metric — đối xứng tâm O = A + C − B, ba cạnh
liên tiếp bằng nhau; đỉnh trên pháp tuyến tại O); (3) một thẩm quyền kích thước `kich_thuoc_t11` (chiều cao trực tiếp hoặc
từ cạnh bên, mâu thuẫn, suy biến) dùng chung cho khuôn và metric; (4) `do_luong_cua` dẫn xuất metric lục giác qua S, A, B,
C; (5) C0 kiểm khẳng định lục giác đều trên toạ độ đề cho.

**Bài trước không giải được, nay giải đúng** (`results/transitions.json`; route sản phẩm, chứng chỉ C1, giá trị = oracle):

| hàng | trước (`f20caf8a`) | sau |
|---|---|---|
| H1 cạnh đáy 2, chiều cao 3 | từ chối | V = 6√3 |
| H2 cạnh đáy 2, cạnh bên 4 | từ chối | V = 12 |
| H3 đổi tên S.MNPQRT, 1 và 2 | từ chối | V = √3 |
| H4 "hình chóp đều S.ABCDEF" | từ chối | V = 6√3 |
| H5 "… có đỉnh S và đáy ABCDEF" | **phục vụ SAI 1** | V = 6√3 |
| H6 cạnh đáy √3, chiều cao 2 | từ chối | V = 3√3 |
| H7 hỏi cạnh bên SA | từ chối | SA = √13 |
| H8 cạnh đáy 1/2, chiều cao 6 | từ chối | V = 3√3/4 |

**Biên vẫn từ chối:** thiếu chiều cao, mâu thuẫn (cạnh bên ≠ √(h² + b²)), suy biến (h² = 0), đáy chương trình không phải
lục giác đều, đề không "đều", mệnh đề chứng minh, phủ định, ngũ giác đều (ngoài miền). **Đính chính nhãn** (công khai,
`label_corrections.json`): N4 — chương trình đặt đỉnh trên một đỉnh đáy TRONG KHUNG affine — được phục vụ đúng 6√3, vì
khung không mang độ dài; metric từ đề quyết vuông góc (cùng luật, cùng kết cục với hàng `N5_apex_over_vertex` của T8).

**Scene3D:** khối 7 đỉnh, 7 mặt, toạ độ khung chính xác + `chart_metric` cho renderer (`scene3d-chart.ts` sẵn có) — kiểm
qua `_dung_scene3d` của pipeline trên mọi hàng phục vụ. **C0:** lục giác đều có toạ độ hữu tỉ (mặt x + y + z = 0) phục vụ
V = 3; đỉnh lệch trục ⇒ `SOURCE_SHAPE_CONTRADICTS_COORDINATES`.

**Đường chạy đã kiểm:** route sản phẩm của **LLM_ONLY** trên chương trình kiểu mô hình (đáy trong khung affine 60°).
**Chưa đo** mô hình thật có tự sinh chương trình ấy ⇒ `regular_hexagonal_pyramid` = `foundation_only`. **Compiler:** không
có họ này (opt-in, không đổi). Không tuyên bố cải thiện LLM_ONLY trên đề thật.

**Vẫn chưa hỗ trợ:** lăng trụ lục giác đều và lăng trụ tam giác đều (ký hiệu lăng trụ + metric lăng trụ — ứng viên kế tiếp,
cùng cơ chế), chóp lục giác đều không tên, ngũ giác đều, đáy theo góc, đáy lõm, đa giác toạ độ trên compiler
(`ISSUE-ARCH-G05-REMAINING-BASES`). Thiếu kích thước ở chóp lục giác: từ chối với `ASSUMPTION_INVARIANCE_UNPROVEN` (khung
affine không có hiện thực Euclid hữu tỉ để dựng phản ví dụ — lý do kém cụ thể hơn T7, vẫn từ chối).

## B. Bằng chứng kỹ thuật

- Mã: `shape_constraint.py` (bộ đọc), `assumption_gate.py` (T11, `kich_thuoc_t11`, metric, C0), `product_capability.py`
  (một dòng), `main.py` (cache). Amendment §26.
- Test: `test_regular_hexagonal_pyramid.py` 38/38 (oracle, 17 hàng route + Scene3D, bộ đọc, metric, cặp C0); bộ liên quan
  (T7/T8, C0 §21–§25, Policy A, G04, G05, cổng giả định) xanh.
- Không hồi quy: toàn bộ pytest (worktree sạch, cùng máy) `6c79243` 7525 passed / 136 failed / 4 errors; `f20caf8a`
  7492 / 131 / 4 — 131 + 4 có sẵn trùng hệt; 5 đỏ mới = danh tính candidate (LOCAL đóng băng) —
  `results/pytest_compare.json`. Log C1 chóp đều (gồm Policy A), nhãn C0 ba run trước: trùng hệt. 49/49 fixture Tier-A
  trùng byte; demo 5/5; bề mặt sập 6/6 (worktree sạch).
- Cache: **`CACHE_VERSION` 123 → 124** (`cache/decision.json`): H5 từng phục vụ giá trị sai nay đổi; C0 lục giác mâu thuẫn
  served → refused. Bề mặt mô hình không đổi; khoá sinh bằng script; ghim cập nhật. Candidate `b13a3ef1…` CHƯA đóng băng
  lại (LOCAL).
- Không chạy trên Cloud: T3 trình duyệt (frontend không đổi mã; hiển thị khung affine lục giác cần T3), mô hình thật.
