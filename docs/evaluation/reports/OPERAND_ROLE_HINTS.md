# OPERAND_ROLE_HINTS — ô toán hạng nói ra vai trò của nó

> Thực hiện **2026-09-04**, trên HEAD `fd5b1be`, cây sạch.
> **APPLICATION_LLM_CALLS = 0.** Không đổi tên trường, không alias, không đổi
> IR/runtime/checker/grounding. V3 không chạy, pool niêm phong, seed chưa rút.

## 0. Kết luận trước

```
OPERAND_ROLE_HINTS = CLOSED
ROLE_HINT_AUTHORITIES = 1 · SIGNATURE_AUTHORITIES = 1
VECTOR_FROM_POINTS_ROLE_DISCOVERABILITY = PASS
DIVIDE_SEGMENT_ROLE_AMBIGUITY_REDUCED   = YES
MIDPOINT_FALSE_DIRECTIONAL_HINT = 0 · CONSTRUCT_LINE_FALSE_ORDERING = 0
CURVED_OPERAND_ROLE_DISCOVERABILITY = PASS
CARD_CATEGORY_AFFORDANCE_REGRESSION = 0 · REPAIR_ROLE_HINT_ALIGNMENT = YES
MODEL_FACING_ALIASES_ADDED = 0 · CANONICAL_FIELD_NAMES_CHANGED = 0
CACHE_VERSION 73 → 74
```

⚠️ Wave phải **sửa một mô tả SAI** trước khi phơi nó, và điều đó làm
`synthesis_schema` đổi — nhiều hơn kỳ vọng §26. Audit đầy đủ ở §4.

## 1. Thẩm quyền

| | |
|---|---|
| `ROLE_HINT_METADATA_OWNER` | `Field(description=…)` trong `contract.py` |
| `ROLE_HINT_AUTHORITIES` | **1** |
| `SIGNATURE_AUTHORITIES` | **1** (không đổi) |
| chuỗi dựng | Pydantic field → `_vai_tro` → `_truong` → thẻ → mảnh sửa |

`_vai_tro(f)` đọc `f.description` và làm **đúng một** phép rút gọn: bỏ tiền tố
`"tên "`. Thẻ đã in kiểu ngay trước đó (`tên<point3>`), nên chữ ấy lặp lại thứ
vừa nói. Luật **một dòng, áp cho mọi ô** — không phải bảng rút gọn theo từng
phép, thứ sẽ thành thẩm quyền thứ hai.

Khoá: `test_H6b` quét **cây AST** của `grammar_card` tìm phép gán tên
`OPERAND_ROLE_HINTS`/`ROLE_HINTS`/… (quét chuỗi không được — chính docstring
của `_vai_tro` nhắc tên ấy để nói *đừng tạo nó*), và khẳng định thân `_vai_tro`
không nhắc tên phép nào.

## 2. Trước → sau

```
TRƯỚC
  [BIỂU THỨC→assign] vector_from_points: from_point:tên<point3> to_point:tên<point3>
  [BIỂU THỨC→assign|construct_point] divide_segment: a:tên<point3> b:tên<point3> ratio:tên
  [LỆNH] construct_curved_solid: … anchor:tên<point3> apex_or_top?:tên<point3> rim_point:tên<point3> …

SAU
  [BIỂU THỨC→assign] vector_from_points: from_point:tên<point3>[điểm gốc] to_point:tên<point3>[điểm ngọn]
  [BIỂU THỨC→assign|construct_point] divide_segment: a:tên<point3>[điểm đầu] b:tên<point3>[điểm cuối] ratio:tên
  [LỆNH] construct_curved_solid: … anchor:tên<point3>[TÂM (cầu) hoặc TÂM ĐÁY (trụ, nón)]
         apex_or_top?:tên<point3>[TÂM ĐÁY KIA (trụ) hoặc ĐỈNH (nón). Khối cầu bỏ trống]
         rim_point:tên<point3>[một ĐIỂM trên mặt cầu, hoặc trên vành đáy] …
```

`divide_segment` là ca đáng giá nhất: tên `a`/`b` **đối xứng** trong khi kernel
cho thấy phép **CÓ THỨ TỰ** (`divide_segment(A,B,2) ≠ divide_segment(B,A,2)`).
Gợi ý `[điểm đầu]`/`[điểm cuối]` bù đúng chỗ tên im lặng — **mà không đổi tên**.

## 3. Soát mô tả ↔ ngữ nghĩa kernel (§18) — và một lỗi thật

Mỗi phát biểu dưới đây đo bằng kernel, không suy từ tên:

| phép | đảo thứ tự | phân loại | mô tả CŨ | phán quyết |
|---|---|---|---|---|
| `midpoint` | `midpoint(A,B)==midpoint(B,A)` | UNORDERED | `điểm đầu`/`điểm cuối` | ❌ **SAI** |
| `construct_line` | cùng một đường | UNORDERED | `điểm 1`/`điểm 2` | ✅ |
| `intersect_line_line` | — | UNORDERED | `đường thẳng 1`/`2` | ✅ |
| `intersect_plane_plane` | — | UNORDERED | `mặt phẳng 1`/`2` | ✅ |
| `divide_segment` | kết quả đổi | ORDERED | `điểm đầu`/`điểm cuối` | ✅ |
| `vector_from_points` | dấu đổi | ORDERED | `điểm gốc`/`điểm ngọn` | ✅ |

`midpoint` là phép KHÔNG THỨ TỰ **duy nhất** dùng lối định hướng — và kho **đã
có** quy ước đúng cho nhóm ấy (`1`/`2`), dùng ở ba phép khác. Sửa `MidpointExpr`
theo chính quy ước ấy, **ở model**, không ở thẻ.

> Trước wave này mô tả chỉ nằm trong lược đồ (không gửi cho mô hình), nên sai
> mà vô hại. Từ nay thẻ in nó ra: **một mô tả sai trở thành một lỗi HỢP ĐỒNG.**
> Đó đúng là điều §18 cảnh báo, và nó có thật.

`test_H3b` khoá quy ước ấy cho **mọi** cặp không thứ tự, nên sẽ không có
`midpoint` thứ hai.

## 4. `synthesis_schema` đổi — audit theo §26

Cổng báo **hai** thành phần: `['grammar_card', 'synthesis_schema']`. §26 bảo
audit khi nhiều hơn một. Kết quả:

```
lược đồ SAU KHI BỎ MỌI `description`:  CŨ == MỚI  → True
mô tả đổi: 3
  MidpointExpr                  (docstring lớp, mới)
  MidpointExpr.properties.a     'tên điểm đầu'  → 'tên điểm 1'
  MidpointExpr.properties.b     'tên điểm cuối' → 'tên điểm 2'
```

⇒ **NGÔN NGỮ CHẤP NHẬN không đổi một byte.** Trường, kiểu, tập bắt buộc,
discriminator: y nguyên. Chỉ ba chuỗi mô tả.

Và lược đồ **không được gửi cho mô hình** (`_sanitize_gemini_schema` bỏ nó vì có
`$ref` — `AUDIT_MODEL_FACING_SCHEMA_SURFACE`), nên thay đổi này có **0** tác
động lên hợp đồng mô hình; nó chỉ là sổ sách danh tính.

`SYNTHESIS_SCHEMA_CHANGED = YES` là **lệch khỏi kỳ vọng §28**, và tôi khai
thẳng: §8 đòi `MIDPOINT_FALSE_DIRECTIONAL_HINT = 0`, §18 đòi soát mâu thuẫn.
Không thể vừa phơi mô tả vừa để một mô tả sai. Artifact xuất khẩu đã sinh lại
bằng `scripts/export_semantic_program_schema.py` (hai bản mirror, khoá bởi
`test_schema_sync`).

## 5. Kích thước (§16, §17)

| | trước | sau | Δ |
|---|---|---|---|
| thẻ hình học (GỬI đi) | 4 587 | **5 320** | **+733 · +16.0%** |
| thẻ đầy đủ (không gửi) | 4 703 | 5 436 | +733 |
| hợp đồng mô hình | 11 087 | **11 820** | **+733 · +6.6%** |
| ước lượng token | — | — | **+211 token/lượt** |
| `responseSchema` | 0 | **0** | bị sanitizer bỏ |

Hai trần nâng, mỗi cái ghi lý do vào changelog của chính guard: thẻ hình học
**4650 → 5400**, thẻ đầy đủ **4750 → 5500**. Phân loại theo §16: byte thêm vào
là **nhãn ngữ nghĩa SINH RA**, không phải văn xuôi chép tay (mọi gợi ý phải
BẰNG `Field.description` — `test_H6`), không phải ví dụ theo dạng bài
(`test_H13`), không phải chữ ký lặp lại.

⚠️ **Nợ đã biết, khai thẳng:** vài mô tả chỉ lặp lại chính kiểu vừa in —
`line:tên<line3>[đường thẳng]`, `point:tên<point3>[điểm]`,
`solid:tên<solid>[khối]`. Chúng tốn byte mà không thêm thông tin. **Không** rút
ở tầng thẻ: mọi phép rút theo từng phép sẽ thành thẩm quyền thứ hai (§3 cấm, và
§3 cũng nói rõ nếu không có phép rút tổng quát an toàn thì **giữ mô tả và tính
chi phí**). Chỗ sửa đúng là **mô tả ở `contract.py`** — một lượt dọn riêng.

## 6. Bằng chứng — `test_operand_role_hints.py` (25 ca)

| | |
|---|---|
| H1 | `vector_from_points`: hai gợi ý có mặt và **khác nhau**; tiền đề *phép có thứ tự* kiểm bằng kernel |
| H2 | `divide_segment`: gợi ý có mặt, khác nhau; tiền đề thứ tự kiểm bằng kernel |
| H3 | `midpoint` **không** mang từ định hướng (`đầu/cuối/gốc/ngọn/nguồn/đích/trước/sau`) |
| H3b | **mọi** cặp không thứ tự dùng lối đánh số — chống một `midpoint` thứ hai |
| H4 | `construct_line` không mang từ định hướng |
| H5 | khối cong: ba vai trò **phân biệt được**, đều có trên dòng |
| H6 | mỗi gợi ý **bằng đúng** `_vai_tro(model.model_fields[...])` |
| H6b | quét AST: **không** bảng gợi ý chép tay; thân `_vai_tro` không nhắc tên phép |
| H7 | đổi `description` ⇒ thẻ **tự đổi** |
| H8 | nhãn `[LỆNH]` / `[BIỂU THỨC→…]` còn nguyên |
| H9 | mảnh sửa mang theo gợi ý |
| H10 | `alias`, `validation_alias`, `populate_by_name`: **không có** |
| H11 | tập tên trường chính tắc y nguyên |
| H12 | chương trình lịch sử (`ball_1` của run2) vẫn parse; `from_point`/`to_point` vẫn nhận |
| H13 | không mẫu theo dạng bài |

Hai test cũ khoá **byte-đối-byte** một dòng thẻ phải đổi sang khẳng định **ngữ
nghĩa** (`test_translate`, `test_geometry_ir`): ý định của chúng — *thẻ phải
quảng cáo phép này với đúng kiểu ô* — giữ nguyên, chỉ thôi khoá chuỗi liền mạch.

## 7. Danh tính

| | trước | sau |
|---|---|---|
| `prompts` | `55ac1ca6a6df92ce…` | **không đổi** |
| `analyze_schema` | `a4d5ed7c65a68007…` | **không đổi** |
| `stable_capability_hash` | `5b61b9ea76d0c764…` | **không đổi** |
| `grammar_card` | `e0790ba831c23718…` (đổi) |
| `synthesis_schema` | `8e47707d478f92c4…` (đổi — §4) |
| `CACHE_VERSION` | `73` | **`74`** |

### Vì sao bump (§27)

Cùng chính sách `CARD_CATEGORY_AFFORDANCE`: bề mặt mô hình đổi, cache khoá theo
*text đã chuẩn hoá + `CACHE_VERSION`*, nên một đề đã cache sẽ trả lại chương
trình sinh bởi **thẻ CŨ** — và lượt đo sau sẽ đo thẻ mới bằng kết quả thẻ cũ.
Tiền lệ 65 · 70 · 73.

## 8. Đối chứng — vẫn MỞ

```
BALL_2_AFFECTED                   NO
BALL_CENTER_RADIUS_EXPRESSIVENESS OPEN   (tâm + số vẫn không sinh được điểm vành)
STRICT_OPERAND_DIAGNOSTIC         OPEN   (extra="forbid" chưa audit tương thích)
DOMAIN_ROOT_TIGHTENING            OPEN   (`push` vẫn tới `served`)
CIRCUMSPHERE_MODEL_SUCCESS        NOT_MEASURED  (§22 — không lượt gọi nào)
R0_POLICY_CHANGED                 NO
IR_LANGUAGE_CHANGED               NO
GEOMETRY_RUNTIME_CHANGED          NO
```

⚠️ Wave này **không** tuyên bố `circumsphere` đã sửa. Nó cải thiện
**deterministically** khả năng tra vai trò ô toán hạng; có sửa được hay không
chỉ một lượt sống mới trả lời.

## 9. Hồi quy — 0 API call

| cổng | kết quả |
|---|---|
| pytest | **3299 pass**, 1 skip, 1 deselect |
| vitest | **687 pass / 50 file** |
| `tsc -b && vite build` | PASS |
| `replay_demo_cases.py` | **5/5** · `REDUCED_CHAIN 1/1` |
| `certify_acceptance_runner.py` | **PASS** |
| `test_schema_sync` | PASS sau khi xuất lại hai bản mirror |
| `lock_cache_identity.py --verify` | PASS |
| `freeze_evaluation_candidate.py --verify` | PASS sau khi đóng băng lại |

## 10. Việc kế tiếp

```
NEXT_ACTION = SMALL_DEVELOPMENT_PROBE  (circumsphere + cylinder_2, run_id MỚI)
```

Ba wave hợp đồng liên tiếp — nhãn loại, mảnh sửa đầy đủ, gợi ý vai trò — đều
**chưa được đo bằng một lượt sống nào**. Trước khi mở
`STRICT_OPERAND_DIAGNOSTIC` (thứ hẹp tập chấp nhận và có rủi ro hồi quy), nên
tiêu một lượt nhỏ hai ca để biết ba wave ấy có dịch chuyển gì không. Runner đã
lưu **văn bản thô**, nên lượt này sẽ trả lời dứt điểm câu mà audit trước phải để
ngỏ: mô hình gõ sai tên, hay gửi `null`.

⚠️ **KHÔNG chạy V3.** Pool giữ niêm phong, seed chưa rút.
