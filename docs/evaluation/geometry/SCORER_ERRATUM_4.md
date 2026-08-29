# SCORER ERRATUM #4 — `hp_a04_011` bị chấm SAI, hệ ĐÚNG

**Lượt:** CONFIRMATION V3 · `selection_hash d7b556d7a002bec9…` · 2026-08-29
**Ảnh hưởng:** 2/12 lượt · `UNSAFE_ACCEPTED` **2 → 0** · `SAFE_OUTCOMES` **10 → 12**
**KHÔNG lật phán quyết cổng:** V3 vẫn **FAIL** trước và sau đính chính.

---

## 1. Con số MÁY phát ra, giữ nguyên văn

```
SAFE_OUTCOMES           10/12
UNSAFE_ACCEPTED         2
CORRECT_EXECUTABLE_IR   3/12
hp_a04_011              ['SAI_MA_VAN_NHAN', 'SAI_MA_VAN_NHAN']
oracle_vi_sao           FAIL: ['parallel: máy=None, đề mong True']
```

Không xoá, không sửa `SCORE.json` của lượt chạy. Đây là thứ bộ đo đã nói.

## 2. Con số ĐÚNG, sau khi kiểm bằng hai nguồn độc lập

```
SAFE_OUTCOMES           12/12
UNSAFE_ACCEPTED         0
CORRECT_EXECUTABLE_IR   5/12
hp_a04_011              ['dung', 'dung']
```

## 3. Vì sao — và vì sao không phải "hệ nhận một diễn giải sai"

Đề (`hp_a04_011`, ô A04): *"Gọi M, N lần lượt là trung điểm của AB và BC.
Chứng minh AC // (SMN)."* Kỳ vọng đã niêm phong: `{"parallel": "true"}`.

Trạng thái cuối của chương trình, đọc thẳng từ artifact:

```
A(0,0,0)  B(4,0,0)  C(4,4,0)  S(2,2,6)  M(2,0,0)  N(4,2,0)
```

`M` là trung điểm `AB`, `N` là trung điểm `BC` — đúng đề. Pháp tuyến của
`(SMN)` bằng `(12, −12, 4)`; phương của `AC` bằng `(4, 4, 0)`; tích vô hướng
bằng **0**, và `A` **không** thuộc `(SMN)`. Vậy `AC // (SMN)` là **ĐÚNG**.

Hai nguồn xác nhận, cả hai độc lập với bộ chấm DEV:

| Nguồn | Kết luận |
|---|---|
| `custodian/geometry_oracle.py` — cài đặt RIÊNG, thuật toán khác kernel | `AC // (SMN) = True` |
| C₂ của chính hệ (`constraints_checked → constraints_verified`) | `parallel(AC)` **đã kiểm, ĐẠT** |

## 4. Lỗi nằm ở đâu

Hợp đồng gọi mặt phẳng bằng tên của ĐỀ — `(SMN)`, **có ngoặc**. Bộ nhớ chương
trình gọi nó là `SMN`. Bộ chấm DEV hoà giải tên bằng `khop_ky_hieu`, và

```
khop_ky_hieu("(SMN)", {"SMN", …})  →  None
```

Không có bí danh ⇒ `GEOMETRY_CHECKERS["parallel"]` trả *"cặp đối tượng không
hợp lệ"* ⇒ `_cham_bang_checker` xếp là **không chấm được** ⇒ rơi về nhánh so
boolean ⇒ `final_memory.get("(SMN)")` là `None` ⇒ `bool(None) != True` ⇒ FAIL.

Một lỗi **TRA TÊN** bị đọc thành một lỗi **HÌNH HỌC**.

Hệ không mắc lỗi này vì `check_postconditions` dùng lại `ten_da_hoa_giai` của
C₁a thay vì hoà giải lần thứ hai — đúng luật đã ghi trong chính file ấy.

> **Đây là lần thứ BẢY của cùng một lớp lỗi**: một tầng đọc `final_memory`
> THÔ thay vì hỏi thành phần đã có thẩm quyền về tên.
> C₁a → C₁b → C₂ → `learner_surface` → bộ chấm DEV → bộ chấm pool → **bộ chấm
> xác nhận**. Sáu lần trước đều được vá tại chỗ, và lần thứ bảy chứng minh vá
> tại chỗ không đóng được lớp lỗi này.

**Chưa sửa trong lượt này** — V3 đóng thành bằng chứng, không rerun. Cách sửa
đúng là bộ đo **hỏi** bản đồ tên của C₁a (phát nó ra `SemanticRouteOutcome`),
không phải dạy `khop_ky_hieu` bóc thêm một loại ngoặc.

## 5. Đính chính THỨ HAI, cùng lượt: nhãn tầng lỗi

`_tang_loi` hỏi `"INVALID" in error_code` **trước** khi hỏi chặng. Bốn lượt
chết ở `execution` vì `GEOMETRY_OPERAND_TYPE` đều mang
`error_code = semantic_program_invalid` — route dùng lại mã ấy cho cả lỗi hình
thức lẫn lỗi toán hạng lúc chạy — nên bị dán nhãn `VALIDATOR`.

```
TRƯỚC:  VALIDATOR 4 · MODEL_SYNTHESIS 2 · GROUNDING 1
SAU:    MODEL_SYNTHESIS 6 · GROUNDING 1 · VALIDATOR 0
```

Đã sửa (`st == "semantic_program"` mới là VALIDATOR). Phép sửa này **không**
chuyển một lượt nào giữa SAFE/UNSAFE hay đúng/sai, **không** chạm ngưỡng nào
của `NGUONG`, và làm bức tranh **xấu đi** cho mô hình chứ không đẹp lên.

## 6. Cổng, tính lại bằng số đã đính chính

| Điều kiện | Ngưỡng | Đạt được | |
|---|---|---|---|
| repetitions | 12 | 12 | ✅ |
| provider + tooling | 0 | 0 | ✅ |
| SAFE_OUTCOMES | 12 | **12** | ✅ |
| UNSAFE_ACCEPTED | 0 | **0** | ✅ |
| CORRECT_EXECUTABLE_IR | ≥10 | **5** | ⛔ |
| STABLE_CASES | ≥5/6 | 5/6 | ✅ |
| scope có hệ thống | 0 | 0 | ✅ |
| grounding có hệ thống | 0 | 1 lượt (< k) | ✅ |
| lỗi tất định lặp lại | 0 | 0 | ✅ |

**CONFIRMATION_GATE = FAIL** — và fail vì đúng một điều kiện:
`CORRECT_EXECUTABLE_IR 5/12 < 10`.
