# CURVED_MODEL_ACCEPTANCE_V1 — §8, và cái nó tìm ra

> Chạy **2026-09-03**. Phép đo **MỚI**, không phải chạy lại benchmark lịch sử.
> `HISTORICAL_BENCHMARKS_RERUN = NO` · `HISTORICAL_SCORES_CHANGED = NO`.
>
> **Kết luận: DỪNG.** Phép đo tìm ra một lỗ NỀN, và theo §19 nó không được vá
> giữa chừng rồi chạy tiếp cùng bộ ca.

---

## 1. Môi trường đã chốt trước khi tiêu lượt nào

```
cache_version             66
semantic_environment      6aefad0315e6f8c0…
stable_capability_hash    8d51b70f2d52fd2d…
case_set_hash             8c6a184f1c175964…   (9 ca, khoá ở commit f880729)
```

Runner khoá **trước** lượt gọi đầu tiên. Băm bộ ca đi vào artifact: sửa một
chữ trong đề là băm đổi, và lượt sau không so được với lượt này.

---

## 2. Con số

```
MODEL_CASES_TOTAL                  9   (2 ball · 2 cylinder · 2 cone
                                        · 1 circumsphere · 2 ca ÂM)
ONE_SHOT_MODEL_CALLS               18  (9 analyze + 9 tổng hợp)
ONE_SHOT_CORRECT                   2
ONE_SHOT_EXECUTABLE_IR             0
ONE_SHOT_HONEST_REFUSALS           2/2

REPAIR_ELIGIBLE_FAILURES           2   (ball_2, cylinder_2 — lỗi schema)
REPAIR_CALLS                       2   ca, 8 lượt gọi
FINAL_CORRECT_AFTER_REPAIR         2

TOTAL_APPLICATION_LLM_CALLS        26
TOTAL_INPUT_TOKENS                 57.677
TOTAL_OUTPUT_TOKENS                17.850
  (+ thoughts_tokens               70.917)
TOTAL_TOKENS                       146.444
TOKENS_PER_CORRECT_EXECUTABLE_IR   — không xác định (mẫu số = 0)
```

⚠️ `TOTAL_INPUT/OUTPUT_TOKENS` in ra `0` trong dòng tổng kết của runner: tên
trường của tôi (`input`/`output`) không khớp tên telemetry dùng
(`prompt_tokens`/`candidates_tokens`). **Lỗi báo cáo, không phải lỗi đo** —
`TOTAL_TOKENS` và bảng `token_theo_stage` trong artifact đúng, và các con số
trên đây lấy từ bảng ấy.

---

## 3. BLOCKER — `CURVED_OBLIGATION_COVERAGE_GAP`

**Ba ca dương (`ball_1`, `cylinder_1`, `cone_1`) sinh ra chương trình ĐÚNG** —
đúng hệt bản tôi viết tay cho bài mẫu — rồi bị từ chối ở **cổng phủ**:

```json
{"kind": "construct_curved_solid", "target_var": "S",
 "curved_kind": "ball", "anchor": "I", "rim_point": "A"}
{"kind": "assign", "target_var": "R", "expr": {"kind": "measure",
 "quantity": "radius", "of": "S"}}
{"kind": "assign", "target_var": "V", "expr": {"kind": "measure",
 "quantity": "volume", "of": "S"}}
```

```
route.py → check_structural_coverage → REQUESTED_OPERATION_UNCOVERED
  volume(S): kiểu 'curved_solid' không hợp với nghĩa vụ này
```

Tái hiện **tất định, 0 lượt gọi model**:

```
OBLIGATION_KINDS['volume']  chủ thể hợp lệ = ['solid']      ← thiếu curved_solid
nghĩa vụ cho radius / lateral_area                          ← KHÔNG CÓ
```

Đây **không phải lỗi mô hình**. Tầng nghĩa vụ/phủ chưa bao giờ được mở cho hình
cong: Phase 2 mở IR · runtime · vết · cảnh, và cố ý **không** thêm checker nào
(`test_26`) vì taxonomy nghĩa vụ đã niêm phong cùng baseline nghiên cứu. Quyết
định ấy đúng với phạm vi Phase 2, nhưng nó để lại đúng lỗ này.

### 3b. Đính chính một khẳng định của tôi ở Phase 2

Báo cáo Phase 2 viết: *"Sáu nhân chứng §38 chạy hết đường IR → thẩm định tĩnh →
grounding → runtime → vết → cảnh: 6/6."*

Chính xác hơn: sáu nhân chứng gọi `kiem_tinh` → `SemanticProgramInterpreter` →
`build_scene`. Chúng **không** đi qua `verify_and_compile`, tức **không** qua
cổng grounding lẫn **cổng phủ**. Grounding có test riêng (`test_40c`); **cổng
phủ thì chưa từng được chạy với một khối cong**. Chính lượt đo này tìm ra điều
đó — và đó là lý do một phép đo live có giá trị mà một bộ test không thay được.

---

## 4. Bảy ca dương — quy trách nhiệm cho đúng

| ca | lớp hỏng | thuộc về |
|---|---|---|
| `ball_1` · `cylinder_1` · `cone_1` | `REQUESTED_OPERATION_UNCOVERED` | **HỆ** — chương trình đúng bị chặn |
| `ball_2` · `cylinder_2` | one-shot: schema (`construct_plane.through = null`); sau sửa: `UNANCHORED_DERIVED_ASSUMPTION` | **MÔ HÌNH** |
| `cone_2` | `UNANCHORED_DERIVED_ASSUMPTION` — khai `B` thay vì dựng bằng `divide_segment` | **MÔ HÌNH** (prompt có dạy đúng lối này) |
| `circumsphere` | `UNANCHORED_DERIVED_ASSUMPTION` — khai `P_diag` | **MÔ HÌNH** |

Nói *"0/7"* mà không tách hai cột này là gán một lỗi hệ cho khả năng của mô
hình. Con số trung thực là: **3 ca hệ chặn · 4 ca mô hình hỏng · 0 ca hệ chạy
trọn**.

---

## 5. R0 giữ vững — kết quả dương rõ ràng nhất của lượt đo

```
CURVED_GEOMETRY_LAUNDERING   0
```

Bốn lần mô hình bịa một điểm để lấy tâm/vành/đỉnh — `B`, `P_diag`, `P_rim_sphere`,
`M1`, `O_bottom` — và **cả năm lần** cổng xuất xứ chặn bằng
`UNANCHORED_DERIVED_ASSUMPTION`, không lần nào cho sửa (đúng thiết kế: lỗi trung
thực năng lực không phải sai sót sửa được).

Không envelope nào chạy được cho một đề ngoài bao đóng. **0 dựng gần đúng, 0
điểm bịa lọt, 0 đa giác giả.**

---

## 6. Hai ca ÂM — đạt, và nói rõ đạt bằng đường nào

| ca | đường từ chối | đúng ranh giới? |
|---|---|---|
| `refuse_line_curved` | mô hình thử `intersect_line_curved_solid` — `kind` không tồn tại ⇒ schema từ chối | **có** — đúng ranh giới giao đường–mặt cong |
| `refuse_oblique` | mô hình bịa `O_bottom` ⇒ cổng xuất xứ chặn | **fail-closed đúng, nhưng không phải vì ranh giới conic** |

Cả hai đạt tiêu chí *"từ chối, không dựng gần đúng"*. Nhưng ca thứ hai chết ở
R0 **trước khi** chạm tới ranh giới elip, nên nó **chưa chứng minh** hệ từ chối
đúng vì conic. Ghi ra thay vì tính nó thành một bằng chứng nó không phải.

---

## 7. Quyết định bật năng lực

```
BALL_PRODUCT_ENABLED       NO
CYLINDER_PRODUCT_ENABLED   NO
CONE_PRODUCT_ENABLED       NO
SOLID_OF_REVOLUTION_ENABLED     NO   (không tự mở)
COMPOSITE_SUBTRACTIVE_ENABLED   NO   (không tự mở)
```

Không hình nào có ca dương ĐẠT, nên không hình nào chuyển
`foundation_only → supported`. Bảng `product_capability.py` **không đổi**.

---

## 8. Việc tiếp theo, và nó là một WAVE RIÊNG

```
BLOCKER   CURVED_OBLIGATION_COVERAGE_GAP
```

Cần mở tầng nghĩa vụ cho hình cong:
`OBLIGATION_KINDS["volume"]` nhận thêm `curved_solid`, và cân nhắc nghĩa vụ cho
`radius`/`lateral_area`.

⚠️ **Nó chạm taxonomy nghĩa vụ, thứ đã niêm phong cùng baseline nghiên cứu.** Đó
là một quyết định phạm vi, không phải một bản vá — và chính vì thế Phase 2 đã cố
ý không đụng vào. Phải cân: mở taxonomy thì băm taxonomy đổi, và mọi so sánh với
baseline SEALED phải khai điều đó.

Sau khi sửa: chạy **một acceptance MỚI, ghi rõ version**, không dùng lại số của
lượt này. Bộ ca có thể giữ nguyên (băm `8c6a184f1c175964…`) để so được hai lượt.

```
MODEL_DISCOVERABILITY   MIXED, ĐO MỘT PHẦN
  · mô hình DÙNG ĐÚNG `construct_curved_solid` ở 3/3 ca nó tới được tầng ấy
  · mô hình HỎNG ở việc DỰNG điểm phụ thay vì khai (4 ca)
  · 3 ca chưa đo được vì hệ chặn trước
```
