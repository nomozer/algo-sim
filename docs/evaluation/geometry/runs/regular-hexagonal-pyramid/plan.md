# regular-hexagonal-pyramid — G05 lát cắt: chóp lục giác đều

Cloud, nhánh `feat/g05-geometry-capability-expansion` từ `origin/main` = `f20caf8a` (khớp; Policy A `56692926` trong
`main`). Candidate `b13a3ef1…`, `CACHE_VERSION` 123, `LLM_ONLY` mặc định, compiler opt-in, frontend không đổi, 0 lượt gọi
model.

## 1. Khảo sát G05 (mã + test tại `f20caf8a`)

| năng lực (G05 = lăng trụ/chóp đáy đa giác) | trạng thái | bằng chứng |
|---|---|---|
| chóp/lăng trụ đứng đáy tam giác vuông, chữ nhật, vuông (T1–T6) | hỗ trợ, kiểm chứng (cả compiler) | corpus gold, 6 họ compiler |
| chóp tứ giác đều (T7), chóp tam giác đều / tứ diện đều (T8, khung affine + metric) | hỗ trợ, kiểm chứng; T8 `foundation_only` | `test_regular_square_pyramid`, `test_regular_triangular_pyramid` |
| đáy theo chuỗi góc vuông — hình thang vuông, đa giác k góc vuông liên tiếp (T10) | hỗ trợ, `foundation_only` (cả compiler) | `test_general_polygon_base` |
| lăng trụ xiên (T9) | hỗ trợ, `foundation_only` | `test_oblique_prism` |
| **chóp lục giác đều** | **chưa hỗ trợ**: bộ đọc chỉ phát `pyramid` (không "đều", không cạnh đáy); không khuôn; toạ độ Euclid vô tỉ | probe `diagnostics/probe_f20caf8a.log`: 7/8 hàng dương bị từ chối, H5 PHỤC VỤ SAI (1 thay 6√3 — lối "có đỉnh … và đáy …" ngoài vùng từ chối) |
| lăng trụ lục giác đều, lăng trụ tam giác đều | chưa hỗ trợ: bộ đọc không nhận ký hiệu lăng trụ "lục giác"; "lăng trụ tam giác đều" chỉ là `prism` | `doc_rang_buoc` |
| chóp/lăng trụ ngũ giác đều | ngoài miền: ngũ giác đều không có khung affine hữu tỉ (tỉ số vàng) | — |
| hình bình hành/thoi theo góc (độ) | chưa hỗ trợ — cần grounding góc (thuộc G16, L03) | `ISSUE-ARCH-G05-REMAINING-BASES` (2) |
| đáy lõm | chưa hỗ trợ — thuộc G06 | (3) |
| đa giác cho bằng toạ độ trên compiler | chưa (compiler lùi về LLM; LLM_ONLY phục vụ qua C0) | (4) |
| hình thang vuông viết khác | chưa | (5) |
| chóp đều không tên có tên điểm thiếu toạ độ | từ chối có chủ đích (Policy A) | `unnamed-pyramid-vertex-binding` |

Kernel có sẵn cho lát cắt: khung affine + metric Gram hữu tỉ (`geometry/metric.py`, `gram_from_lengths` từ bốn điểm và
sáu độ dài của ĐỀ), thể tích/độ dài/khoảng cách theo metric (√det G), Scene3D mang `chart_metric` cho renderer (frontend
`scene3d-chart.ts`). Thiếu: bộ đọc (L03), khuôn C1 (L06/certificate), dẫn xuất metric cho đáy lục giác.

## 2. Lát cắt chọn: chóp lục giác đều (một cơ chế dùng chung với T8)

Lục giác đều HỮU TỈ trong khung affine (cơ sở u, v góc 60°): tâm O, đỉnh O+u, O+v, O+v−u, O−u, O−v, O+u−v. Metric dẫn xuất
từ đề (b², h²) qua S, A, B, C: AB² = BC² = b², AC² = 3b², SA² = SB² = SC² = b² + h². Mở rộng:
1. bộ đọc: `regular_hexagonal_pyramid` + `base_regular_hexagon` cho `chóp lục giác đều X.Y`, `chóp đều X.Y` (đáy 6 đỉnh),
   `chóp lục giác đều có đỉnh X và đáy Y`; cạnh đáy/cạnh bên của khối duy nhất;
2. khuôn **T11** (cùng hợp đồng `_Khuon` với T8, `can=True`): đáy lục giác đều theo metric (đối xứng tâm O = A + C − B,
   ba cạnh liên tiếp bằng nhau), đỉnh trên pháp tuyến tại O, kích thước b, h; một thẩm quyền kích thước
   (`kich_thuoc_t11`) cho khuôn và metric;
3. `do_luong_cua`: metric cho chóp lục giác đều.
Không: lăng trụ lục giác đều (ký hiệu + metric lăng trụ — lát cắt sau), chóp lục giác đều không tên, compiler (opt-in),
frontend, Policy A, C0 toạ độ lục giác (vô tỉ).

## 3. Tiêu chí (đăng ký trước)

`labels.json` 17 hàng (8 dương H1–H8, 9 biên N1–N9) + `oracle.py` độc lập (V = (√3/2)·b²·h, SA² = h² + b²);
`diagnostics/cases.py` dựng hợp đồng + chương trình kiểu mô hình (khung affine). Thành công = hàng H từ chối/phục vụ sai
trên `main` → phục vụ ĐÚNG giá trị oracle với chứng chỉ C1 và Scene3D có `chart_metric`; hàng N vẫn từ chối. Bảo vệ:
C0 §21–§25, T7/T8, G04/G05, Policy A, compiler, toàn bộ pytest so baseline sạch; cache theo probe trước/sau.
