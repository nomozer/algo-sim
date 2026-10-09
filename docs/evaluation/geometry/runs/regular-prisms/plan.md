# regular-prisms — G05: lăng trụ lục giác đều + lăng trụ tam giác đều

Cloud, nhánh `feat/g05-regular-prisms` từ `origin/main` = `ea85216b` (khớp; T11 `6c792434` trong `main`). Candidate
`cf47dd61…`, `CACHE_VERSION` 124, `LLM_ONLY` mặc định, compiler opt-in, frontend không đổi, 0 lượt gọi model. (Ghi nhận:
remote còn các nhánh cũ `feat/*`, `fix/*`, `claude/*` — không đụng.)

## 1. Khảo sát (mã tại `ea85216b`)

| câu hỏi brief | trả lời |
|---|---|
| 1. lăng trụ đứng / tam giác đều hỗ trợ tới đâu | lăng trụ đứng đáy tam giác vuông (T3), hộp (T4), lập phương (T5), đáy vuông (T6), chuỗi góc vuông (T10), xiên (T9). **Lăng trụ đáy tam giác đều: KHÔNG** — "lăng trụ tam giác đều X.Y" chỉ là `prism` (không đứng, không đáy đều); "lăng trụ đứng … đáy là tam giác đều" đọc đủ nhưng T3 đòi góc vuông ⇒ từ chối |
| 2. tái dùng được | `_khuon_lang_tru` (tịnh tiến, cạnh bên ⊥ đáy, chiều cao — nhưng `.dot` Euclid thô), khung affine + metric (`do_luong_cua`, `gram_from_lengths`), `base_equilateral` (bộ đọc + C0 §21), `base_regular_hexagon` (T11), Scene3D `chart_metric` |
| 3. metric T8 | S, A, B, C: ba cạnh đáy b², ba cạnh bên b²/3 + h² ⇒ Gram duy nhất |
| 4. metric T11 | S, A, B, C: AB² = BC² = b², AC² = 3b², cạnh bên² = b² + h² |
| 5. lăng trụ đứng kiểm thế nào | tịnh tiến từng đỉnh (affine), cạnh bên ⊥ mọi cạnh đáy, cạnh bên ≠ 0, cạnh bên² = h² — tất cả bằng `.dot` Euclid ⇒ không dùng được trong khung affine |
| 6. Scene3D mặt lục giác | có: T11 phục vụ chóp lục giác (mặt 6 đỉnh) với `chart_metric`; LOCAL đã kiểm trình duyệt ở run trước |
| 7. thuộc G05 hay khác | lăng trụ đều đáy tam giác/lục giác: G05 (đáy đa giác đều). Ngũ giác đều: không có khung affine hữu tỉ. "Lăng trụ tứ giác đều" (đáy vuông): bộ đọc chưa coi là "đứng" — cùng họ, NGOÀI lát cắt này (T6 sẵn có) |

Baseline (`diagnostics/probe_ea85216b.log`): 13/13 hàng dương bị từ chối ở `assumption`; 12/12 biên từ chối.

## 2. Lát cắt: lăng trụ ĐỀU đáy tam giác và lục giác — một khuôn **T12**

Định nghĩa SGK: lăng trụ đều = lăng trụ đứng có đáy là đa giác đều. Một cơ chế cho k ∈ {3, 6}:
1. bộ đọc: `lăng trụ tam|lục giác đều X.Y` ⇒ `right_prism` + `base_equilateral` / `base_regular_hexagon`; `đáy là lục
   giác đều (cạnh a)` như `tam giác đều`; cạnh đáy / cạnh bên của lăng trụ đều duy nhất (cạnh bên = chiều cao);
2. khuôn **T12** (ID trống — registry T1–T11): tịnh tiến (affine), cạnh bên ⊥ đáy THEO METRIC, đáy đều theo metric
   (k = 3: ba cạnh bằng nhau; k = 6: đối xứng tâm O = A + C − B + AB = BC = CD), cạnh đáy, chiều cao; `can=True`; một
   thẩm quyền kích thước `kich_thuoc_t12`;
3. `do_luong_cua`: metric cho lăng trụ đều qua A, B, C, A' (k = 3: AB² = BC² = CA² = b²; k = 6: AC² = 3b²; AA'² = h²,
   BA'² = b² + h², CA'² = AC² + h²);
4. C0 §22: `base_regular_hexagon` kiểm trên toạ độ.
Không: lăng trụ tứ giác đều, lăng trụ xiên đều, compiler, frontend.

## 3. Tiêu chí

`labels.json` 25 hàng (13 dương: 7 lục giác, 6 tam giác — nguyên, phân số, căn, đổi tên, ba lối viết; 12 biên) +
`oracle.py` độc lập (V = (3√3/2)b²h | (√3/4)b²h, cạnh bên = h). Thành công: hàng dương từ chối trên `main` → phục vụ
đúng oracle, C1, Scene3D 12 đỉnh / 8 mặt / 18 cạnh (lục giác) hoặc 6 / 5 / 9 (tam giác), Euler, `chart_metric`. Bảo vệ:
T7/T8/T11, C0 §21–§26, Policy A, lăng trụ đang hỗ trợ (T3–T6, T9, T10), compiler, toàn bộ pytest so baseline sạch; cache
theo probe trước/sau.
