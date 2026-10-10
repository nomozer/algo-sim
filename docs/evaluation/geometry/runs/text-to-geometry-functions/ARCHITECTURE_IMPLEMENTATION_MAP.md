# Bản đồ kiến trúc Text-to-Geometry Functions — kiểm toán mã thật (2026-10-10)

Nguồn: đọc mã + chạy test trên nhánh `feat/text-to-geometry-functions` (rẽ từ `main` = `28ac1d61`). Không suy từ báo
cáo cũ. Nhãn: **IMPLEMENTED** (có mã + test xanh trên đường dùng được), **PARTIAL** (có nhưng thiếu một phần cần cho
kiến trúc mới), **MISSING**, **LEGACY-ONLY** (chỉ phục vụ `LLM_ONLY`), **UNVERIFIED** (có mã, chưa có bằng chứng chạy).

## 1. Thành phần

| thành phần | vị trí | trạng thái trước run | sau run | ghi chú |
|---|---|---|---|---|
| RequestContract | `semantic_program/request_contract.py`, `analyze_contract.py` | IMPLEMENTED (cho LLM_ONLY) | không đổi, **không dùng** ở đường mới | đầu ra LLM analyze; pilot G05 chết ở đây (P1: lệch lược đồ `solid_topology` + `ValueError` không bắt) |
| FactGraph | `geometry_compiler/fact_graph.py`, `contract_adapter.py` | PARTIAL | không đổi, không dùng | dựng từ RequestContract, không từ lời gọi hàm có nguồn |
| Compiler tất định (compiler-first) | `geometry_compiler/compiler.py`, `routing.py` | PARTIAL · opt-in `GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST`, **không nối** vào `app/ai`/`main.py` | không đổi | 9 họ: chóp/lăng trụ đáy tam giác vuông, chóp đáy chữ nhật, hộp, lập phương, lăng trụ đáy vuông, lăng trụ xiên (chân tại đỉnh), chóp/lăng trụ đáy chuỗi góc vuông. Chỉ **thể tích**; toạ độ Euclid hữu tỉ ⇒ không có đa giác đều |
| Primitive dựng câu lệnh IR | `geometry_compiler/primitives.py` | IMPLEMENTED (bộ tạo câu lệnh, tổng quát) | **tái sử dụng** | `declare_point`, `construct_polygon/pyramid/prism/line`, `measure_quantity`, `memory_declaration`… |
| Function registry cho AI | — | **MISSING** (registry cũ là của compiler, AI không chọn) | IMPLEMENTED `geometry_functions/registry.py` | 16 hàm, lược đồ đóng, khai báo function calling |
| Hợp đồng lời gọi có nguồn + cổng nguồn | — | **MISSING** | IMPLEMENTED `registry.kiem_nguon` | 6 mã từ chối nguồn |
| Giải phụ thuộc + thứ tự dựng | compiler: thứ tự cố định theo họ | PARTIAL | IMPLEMENTED `engine._Dung.giai_phu_thuoc` | điểm theo phụ thuộc, bất biến khi xáo lời gọi |
| Bố cục khung affine + metric Gram | `geometry/metric.py` (`Metric`, `using`); `assumption_gate.do_luong_cua` suy metric từ **văn bản** theo khuôn T8/T11/T12 | PARTIAL · LEGACY-ONLY về cách suy | IMPLEMENTED: engine dựng `Metric` từ **lời gọi có kiểu** (khối G₂ ⊕ h²), không khuôn | tái sử dụng `Metric`, `using` |
| Source grounding (LLM_ONLY) | `semantic_program/grounding_gate.py` | IMPLEMENTED · LEGACY-ONLY | không dùng | kiểm xuất xứ khai báo trong chương trình LLM |
| C0 / assumption gate / T8–T12 | `semantic_program/assumption_gate.py`, `shape_constraint.py` | IMPLEMENTED · LEGACY-ONLY | không dùng | đọc đề bằng luật để chặn LLM; đường mới thay bằng kiểm lại mọi dữ kiện trên bố cục |
| Nhân hình học | `geometry/` (exact, radical, kernel, measure, metric) | IMPLEMENTED | **tái sử dụng**, không sửa | |
| Interpreter IR | `semantic_program/interpreter.py`, `validator.py`, `formation.py` | IMPLEMENTED | **tái sử dụng**, không sửa | |
| Scene3D | `semantic_program/simulation_state.py`, `scene3d.py`; frontend `scene3d-chart.ts::veKhongGian` | IMPLEMENTED | **tái sử dụng**, không sửa | `contract=None` hợp lệ |
| Construction trace | `simulation_state` timeline (bước IR); compiler `BuocDung` | PARTIAL (trace IR, không nối về mệnh đề đề) | IMPLEMENTED `KetQuaTuyen.trace`: mỗi bước ↔ id lời gọi ↔ quote | |
| Router / feature flag | `geometry_compiler/routing.py` (2 chế độ) | PARTIAL | **không đổi**; đường mới vào qua `app/ai/function_route.run_function_route` (không ai trên đường mặc định gọi nó) | không đổi default |
| Test chứng nhận theo họ | `tests/geometry/test_*_compiler.py` (134 hàm test) | IMPLEMENTED cho compiler | + `test_text_to_geometry_functions.py` (64 test sau tham số hoá) | |

## 2. Trả lời sáu câu hỏi kiểm toán

1. **Compiler-first đã dựng được gì?** Chín họ thể tích kể trên, trên fixture `RequestContract` (0 lượt gọi model). Toạ độ
   Euclid hữu tỉ ⇒ không tam giác đều / lục giác đều / chóp đều; không khoảng cách / góc; không trung điểm làm chân.
2. **Gì vẫn phụ thuộc LLM sinh SemanticProgram?** Mọi thứ trên đường sản phẩm (`run_pipeline`, `LLM_ONLY`): đa giác đều
   (T8/T11/T12 là cổng kiểm *chương trình LLM viết*), mọi đại lượng ngoài thể tích, mọi tổ hợp ngoài chín họ. Compiler họ-bài
   cũng cần `RequestContract` do LLM analyze sinh.
3. **AI đã chọn hàm từ registry chưa?** Trước run: **chưa** — `primitives.REGISTRY` là bảng nội bộ của compiler; việc chọn
   phép dựng nằm trong mã `_danh_gia_eligibility_*` theo từng họ. Sau run: có hợp đồng + registry cho AI, nhưng **AI chưa được
   nối** (đầu ra AI đang là fixture gán nhãn tay).
4. **Primitive kết hợp được hay template?** Bộ tạo câu lệnh IR là kết hợp được; *việc chọn* là template theo họ. Engine mới
   bỏ tầng họ: cùng 16 hàm dựng COMP2 (đáy lục giác đều + chân tại đỉnh) và COMP3 (chân tại trung điểm cạnh) — hai tổ hợp
   không có họ/khuôn nào.
5. **Thay đổi tối thiểu cho đường độc lập LLM_ONLY?** Đúng những gì run này thêm: registry + cổng nguồn + engine bố cục/phụ
   thuộc/kiểm (gói mới `geometry_functions/`), phát ra IR sẵn có. Không sửa kernel, interpreter, Scene3D, lược đồ IR, prompt.
6. **Lỗi pilot cũ có nằm trên đường dùng chung?** P1 (`solid_topology`, analyze) — **không** (đường mới không dựng
   RequestContract). P3 (khung affine không tới mô hình) — **được giải** (engine chọn khung). P2 (`TypeError Radical × int` ở
   interpreter) — interpreter **dùng chung**, nhưng đường mới không phát phép `arith`; lỗi vẫn mở cho LLM_ONLY. Lỗi bộ đo
   F1–F6 thuộc công cụ pilot, không thuộc đường mới.

## 3. Luồng sau run

```
đề ──(AI: fixture hôm nay; Gemini function calling ở bước kế)──► lời gọi {fn, args, source.quote}
  registry.doc_ke_hoach  (lược đồ đóng, extra=forbid, 16 hàm)          ── SCHEMA_INVALID
  registry.kiem_nguon    (quote ⊂ đề · nhãn ⊂ đề · phủ định · vị từ · số) ── QUOTE_NOT_IN_SOURCE … UNGROUNDED_VALUE
  engine._Dung: khối → bố cục đáy (khung + G₂) → phụ thuộc (trung điểm, ⊥, tâm, tịnh tiến) → h² → kiểm MỌI dữ kiện
                                                                        ── UNDERDETERMINED_POINT, MISSING_DIMENSION,
                                                                           INCONSISTENT_FACTS, ENGINE_SELF_CHECK_FAILED …
  → IR (primitives) → validate_semantic_program → hoan_thien_dung_hinh → Interpreter dưới metric.using(G)
  → kiểm chéo điểm kernel = bố cục                                     [app/simulation/geometry_functions]
  → build_simulation_state + build_scene3d + chart_metric → KetQuaTuyen(SERVED, answers, trace, scene3d)
                                                                        [app/ai/function_route — tầng được bày cảnh]
```
