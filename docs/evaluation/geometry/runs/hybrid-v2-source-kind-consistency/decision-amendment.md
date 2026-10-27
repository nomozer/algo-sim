# Policy Decision Amendment — `SOURCE_CONTRADICTION_MUST_FAIL_CLOSED` (`I-1`)

- **Run**: `hybrid-v2-source-kind-consistency`
- **Date**: `2026-10-27`
- **Owner Decision**: `SOURCE_CONTRADICTION_MUST_FAIL_CLOSED`
- **Supersedes**: `solid_symbol_outranks_the_solid_word` (introduced in run `hybrid-semantic-hardening` and pinned in `backend/tests/geometry/test_hybrid_ask_operand_binding.py::test_solid_symbol_outranks_the_solid_word`).

---

## 1. Historical Policy and Origin

During run `hybrid-semantic-hardening` (`S1` ask-operand binding), `_khoi_khop` in `backend/app/simulation/geometry_functions/registry.py` added a check on the solid-kind phrase (`_TU_KHOI`) in `ask_volume` and `ask_section_area`. Because `backend/tests/geometry/test_geometry_library_expansion.py::run` hardcoded `query = f"Tính thể tích hình chóp {solid}."` even when `test_projection_waits_for_right_prism_top` monkeypatched the fixture to a cube (`solid="ABCD.EFGH"`), `_khoi_khop` exempted phrases carrying an explicit solid symbol (`and not sym and not tu`) under the rationale:

> *"từ loại chỉ xét khi KHÔNG có ký hiệu: ký hiệu đúng đã định danh khối ('hình chóp ABCD.EFGH' gọi đúng lăng trụ ấy)"*

The same exemption was mirrored in `_cum_goi_khoi` during `hybrid-v2-planner-generalization` (`if ky := ...: return all(...)`), where a matching solid symbol returned `True` before calling `_loai_cum_dung`.

---

## 2. Why the Historical Policy Was Unsafe (`I-1`)

In run `hybrid-v2-planner-premerge-review`, the 124-case adversarial solid-kind suite (`docs/evaluation/geometry/runs/hybrid-v2-planner-premerge-review/tools/adversarial.py`) demonstrated that exempting the kind check whenever a symbol is present creates a systematic fail-open hole (`6/124` cases in the registered suite, `15/31` in the supplementary symbol suite):

- A right triangular prism (`Cho lăng trụ đứng ABC.A'B'C'`) asked as `"hình lập phương ABC.A'B'C'"` or `"hình chóp ABC.A'B'C'"` was served.
- A `6 × 8 × 12` rectangular cuboid (`Cho hình hộp chữ nhật ABCD.A'B'C'D'`) asked as `"hình lập phương ABCD.A'B'C'D'"` was served.
- An oblique prism (`Cho lăng trụ ABC.A'B'C'`) asked as `"lăng trụ đứng ABC.A'B'C'"` was served.

While a correct solid symbol identifies *which* object in the problem is being referenced, an explicit geometric kind phrase (`"hình lập phương"`, `"hình chóp"`, `"lăng trụ đứng"`, etc.) is a source-level geometric claim. Under `AGENTS.md §3` (*Fail-closed: Bất kỳ mâu thuẫn dữ kiện nào trong đề bài phải dẫn đến từ chối an toàn*), a contradiction between the grounded solid's verified kind and the kind claimed in a question or section clause must refuse with `SOURCE_OBJECT_MISMATCH`.

---

## 3. Amended Policy (`Registry /17`)

1. **Symbol Identity**: When a solid symbol (`sym` / `tu` / `ky`) is written in a question or section phrase, it must match the target solid's vertex symbol. When no symbol is written, the problem must have a single unambiguous solid (`len(khoi) == 1`).
2. **Kind Compatibility (`_loai_cum_dung`)**: Whenever an explicit solid-kind phrase is written — **whether or not a solid symbol is also present** — that kind phrase must be true of the referenced solid according to the calls validated by `kiem_nguon`:
   - Compatible generic kinds (e.g., `"lăng trụ ABC.A'B'C'"` for a right prism, `"hình hộp ABCD.A'B'C'D'"` for a cuboid/cube, `"hình hộp chữ nhật ABCD.A'B'C'D'"` or `"lăng trụ đứng ABCD.A'B'C'D'"` for a cube) remain **accepted (`SERVED`)**.
   - Contradictory or ungrounded specific kinds (e.g., `"hình lập phương ABC.A'B'C'"` or `"hình chóp ABC.A'B'C'"` for a triangular prism, `"hình lập phương ABCD.A'B'C'D'"` for a cuboid not declared as a cube, `"lăng trụ đứng ABC.A'B'C'"` for an oblique prism) **fail closed (`REFUSED` / `SOURCE_OBJECT_MISMATCH`)**.
3. **Test Migration**:
   - `backend/tests/geometry/test_geometry_library_expansion.py::test_projection_waits_for_right_prism_top` now passes `kind="hình lập phương"` for `solid="ABCD.EFGH"`.
   - `backend/tests/geometry/test_hybrid_ask_operand_binding.py::test_solid_symbol_outranks_the_solid_word` is updated to assert refusal on `"Tính thể tích hình chóp ABCD.EFGH."` for a prism/cube and acceptance on `"Tính thể tích hình lập phương ABCD.EFGH."` / `"Tính thể tích khối lăng trụ ABCD.EFGH."`.
