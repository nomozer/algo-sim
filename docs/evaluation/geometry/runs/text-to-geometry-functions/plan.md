# text-to-geometry-functions — kế hoạch và PRE-FLIGHT

Yêu cầu (2026-10-10): tiếp tục kiến trúc mới theo ý GVHD — *"bóc tách các hình thành hàm cơ bản để vẽ … AI đọc đề sử dụng
các hàm có sẵn để vẽ hình chứ không để AI vẽ hết"*: kiểm toán phần đã có, dựng một vertical slice chạy thật
text/facts → function calls → dựng tất định → kiểm → Scene3D, nghiên cứu khoảng trống. 0 lượt Gemini, không merge `main`,
không xoá `LLM_ONLY`, không sửa dữ liệu pilot cũ.

## PRE-FLIGHT (`RULES.md §2`)

```
Active branch:      feat/text-to-geometry-functions (rẽ từ main = origin/main = 28ac1d61)
HEAD:               28ac1d61 lúc bắt đầu
Working tree:       sạch
Current milestone:  G05 họ hình trên kiến trúc sẵn có (ROADMAP §0); pilot G05 thật nằm ở feat/real-model-pilot-tooling @ 471a2c79 (local, chờ review — giữ nguyên)
Task classification: CORE (chức năng trực tiếp: dựng hình 3D có kiểm chứng từ đề) — đường mới, nhánh nghiên cứu
Thesis relevance:   ranh giới R0 chặt hơn: AI chỉ chọn hàm có nguồn, engine sở hữu bố cục/toạ độ/kiểm
Existing related modules: geometry_compiler (FactGraph, primitives, compiler họ-bài, routing opt-in), geometry/metric (khung affine + Gram),
                    semantic_program (validator, formation, interpreter, simulation_state, scene3d), assumption_gate (T8/T11/T12, LLM_ONLY)
Reuse:              primitives.* (bộ tạo câu lệnh IR), metric.Metric/using, validate_semantic_program, hoan_thien_dung_hinh,
                    SemanticProgramInterpreter, build_simulation_state, build_scene3d, frontend veKhongGian
Source of truth:    mã + test (kiểm toán: ARCHITECTURE_IMPLEMENTATION_MAP.md)
Files expected to change: backend/app/simulation/geometry_functions/ (MỚI), backend/scripts/run_text_to_functions_fixtures.py (MỚI),
                    backend/tests/geometry/test_text_to_geometry_functions.py + fixtures/text_to_functions_cases.json (MỚI),
                    docs/CODE_INDEX.md (một hàng), thư mục run này
Contract/cache/history impact: KHÔNG đổi lược đồ IR, prompt, thẻ văn phạm, routing, run_pipeline ⇒ bề mặt mô hình KHÔNG đổi,
                    CACHE_VERSION giữ 125. Thêm tệp dưới backend/app ⇒ candidate --verify ĐỎ trên nhánh này (chấp nhận:
                    không đo live; đóng băng lại chỉ trước một lượt đo)
Duplicate implementation risk: (1) registry hàm vs primitives.REGISTRY — khác trách nhiệm: primitives là bộ tạo câu lệnh IR
                    nội bộ, registry mới là hợp đồng AI-facing có nguồn; tái sử dụng primitives để phát IR.
                    (2) bố cục vs compiler họ-bài — compiler đặt toạ độ Euclid theo họ cố định; engine mới đặt khung affine +
                    Gram theo lời gọi, không họ. (3) metric vs do_luong_cua — do_luong_cua suy từ VĂN BẢN theo khuôn; engine
                    dựng Metric từ lời gọi có kiểu, tái sử dụng metric.Metric.
Dependency-cycle risk: geometry_functions → geometry_compiler.primitives, geometry.metric, semantic_program.* ; không ai import ngược;
                    không import app.ai (test AST)
Scope-creep risk:   thư viện hàm phình thành DSL tổng quát — giữ 16 hàm, chỉ thêm khi một đề thật cần
Smallest sufficient implementation: một gói 2 module + fixture runner + 1 file test
Explicitly excluded work: nối Gemini thật; đổi default/routing; sửa P1/P2 của LLM_ONLY; frontend; OCR; độ dài ký hiệu `a`;
                    song song, mặt bên ⊥ đáy, góc nhị diện, thiết diện, khối tròn
Stop conditions:    cần sửa kernel/interpreter/Scene3D/lược đồ IR để đường mới chạy; test cũ đỏ do mã mới
```

## Các bước

1. Kiểm toán mã thật → `ARCHITECTURE_IMPLEMENTATION_MAP.md`.
2. Fixture đăng ký TRƯỚC (`text_to_functions_cases.json`, 27 ca: chóp, lăng trụ, tổ hợp, chóp đều, diễn đạt khác, thiếu,
   mâu thuẫn, ngoài phạm vi, phủ định, 7 đầu ra AI cố ý sai) + test → đỏ (thiếu module).
3. Registry + cổng nguồn + engine → xanh; kiểm đột biến 6 lỗi cài sẵn phải bị bắt.
4. Fixture runner ghi `offline/results.json` + cảnh; kiểm biến đổi renderer `scene_world_metric_check.ts` + tiêm lỗi.
5. Nghiên cứu văn liệu song song (skill research, tác tử nền) → `LITERATURE_GAP_MATRIX.md`.
## Sửa kế hoạch trong lúc làm (ghi lại, không xoá dòng trên)

- Full suite lần 1 đỏ ở ba guard hướng phụ thuộc ⇒ bày cảnh dời sang tệp MỚI `backend/app/ai/function_route.py` (tầng
  điều phối); `test_structured_geometry_relations.py::test_Y…` loại trừ đích danh gói nghiên cứu và siết thêm điều kiện
  đường mặc định. Thêm tệp dưới `backend/app` ⇒ đóng băng lại candidate ở commit riêng (worktree sạch), như luật kho.

6. Full backend suite, cổng tài liệu; `FUNCTION_REGISTRY_SPEC.md`, `EXPERIMENT_PROTOCOL.md`, `report.md`, `handoff.md`, `run.json`.
