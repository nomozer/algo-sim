# CODE_INDEX.md — Chỉ mục module + BỘ NHỚ KIẾN TRÚC

Mục đích: biết **cái gì đã tồn tại và ở đâu** trước khi viết mới (chống trùng
helper, chống hard-code vòng qua abstraction sẵn có). **Không chép thân hàm.**
Helper private nhỏ được bỏ qua có chủ ý.

Đây là **file canonical cho vai trò project index / architecture memory**, dùng
kèm `docs/ARCHITECTURE_MAP.md` (kiến trúc, bảng sở hữu, hướng phụ thuộc, bất
biến đánh số). Trước khi thêm bất cứ thứ gì: đọc `docs/RULES.md` §2b.

---

## 0. Danh tính kho mã (kiểm lại bằng lệnh, đừng tin trí nhớ)

| Hạng mục | Giá trị | Kiểm bằng |
|---|---|---|
> ⚠️ **Số sống nằm ở `docs/CURRENT_STATE.md`, không ở đây.** Bảng này từng chép
> `CACHE_VERSION` **27** và *Family/Target* **12/23** — cả hai đã sai nhiều
> milestone trước khi ai nhận ra, vì không gì khoá một con số chép tay. Dưới đây
> chỉ giữ những hạng mục **kiểm được bằng một lệnh**, và hạng mục nào cũng phải
> kèm lệnh ấy.

| Hạng mục | Giá trị | Kiểm bằng |
|---|---|---|
| Active mainline | `main` | `git branch --show-current` |
| `simulation_id` sản phẩm phát ra | `generic.semantic_program` (DUY NHẤT) | `GET /api/diagnostics/runtime`; khoá: `tests/test_runtime_identity.py` |
| Năng lực hình học | biểu thức / phép dựng / phép đo / nghĩa vụ | `runtime_identity()` — dẫn từ `ir_static_check`, KHÔNG chép tay |
| `CACHE_VERSION` | xem `docs/CURRENT_STATE.md` | `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
| `HISTORY_SCHEMA_VERSION` | **2** | `frontend/src/state/history.ts:33` |
| Archive (read-only) | tag `m17-w2b-deep-hardening-archive` → `feb12d8` | `git rev-parse m17-w2b-deep-hardening-archive` |

⛔ **Ba dòng đã GỠ khỏi bảng** — *Family/Target*, *computation/representation*,
*Trình bày 2D/2D+3D*: cả ba đếm danh mục 24 target Tin học, gỡ ở
`LEGACY_INFORMATICS_REMOVAL`. `catalog_runtime_matrix.py` và
`capability-descriptors.test.ts` (lệnh kiểm của chúng) cũng không còn. Dòng
*Archive* trước đây trỏ một **nhánh đã xoá** 2026-08-24 — nay trỏ tag.

Danh tính runtime (so source ↔ container) do `backend/app/runtime_identity.py` +
`backend/scripts/runtime_doctor.py` lo — endpoint `GET /api/diagnostics/runtime`.
Nó so **năm** thứ: `git_sha` · `CACHE_VERSION` · catalog hash · **vân tay prompt**
· **thẻ văn phạm**. Hai cái sau thêm 2026-08-25 vì ba cái đầu đều KHỚP khi backend
đang gửi cho LLM một prompt cũ — không cái nào đọc một file `.md`.
`skill_fingerprint()` băm **thứ tiến trình ĐANG GIỮ** (`gemini._skill_cache`),
không phải thứ trên đĩa: đọc lại đĩa rồi băm sẽ báo "khớp" trong đúng ca nó sinh
ra để bắt. `da_nap` rỗng lúc mới khởi động là ĐÚNG. Khoá bởi
`tests/test_prompt_fingerprint.py` (11), có tiêm lỗi cho cả ba mã mới.

⚠️ **`grammar_card` trong vân tay băm CẢ HAI bản từ 2026-09-04.** Bản trước băm
`grammar_card()` — bản MẶC ĐỊNH, tức thẻ Tin học — trong khi thứ thật sự ghép
vào user message của sản phẩm là `grammar_card("hinh_hoc")`. Hệ quả: đổi đúng
cái thẻ mô hình đọc thì vân tay **không nhúc nhích**, còn đổi một thẻ không ai
gửi thì nó đỏ. Đúng lớp lỗi *"nghĩa đổi mà danh tính không đổi"* mà chính vân
tay này sinh ra để chặn — và nó nằm ngay trong vân tay ấy. Phát hiện khi
`CARD_CATEGORY_AFFORDANCE` sửa thẻ hình học và cổng khoá cache lẽ ra phải đỏ
thì lại im.
"catalog hash" nay là **`stable_capability_hash()`** — băm `_CHU_KY`,
`_KIEU_DUNG`, `_TOAN_HANG_LENH`, `_KIEU_DO`, `MemoryType`, `GEOMETRY_CHECKERS`,
`OBLIGATION_KINDS` (`nghia_vu_chu_the`) và **`kiem_chung_do`** thay cho `CATALOG`
đã gỡ.

⚠️ Ba trường cuối trả lời **ba câu khác nhau**, và mỗi câu được thêm sau khi một
lỗ danh tính thật lộ ra — đừng gộp chúng lại:

| trường | câu nó trả lời | thêm sau sự cố |
|---|---|---|
| `nghia_vu` | hệ có **tên** checker nào | — |
| `nghia_vu_chu_the` | **cổng phủ CHO PHÉP** chủ thể kiểu nào | `CURVED_OBLIGATION_COVERAGE_BRIDGE` |
| `kiem_chung_do` | bộ kiểm **CHỨNG THỰC ĐƯỢC** kiểu nào | `VOLUME_VERIFICATION_BRIDGE` |

`kiem_chung_do` là **hiệu** `kieu_chu_the_nghia_vu(nv) − KHONG_KIEM_DUOC`, chỉ
cho nghĩa vụ ĐO có checker (`distance`, `angle`, `volume`, `radius`) — đúng tập
mà `test_measure_checker_subject_drift` chứng minh được. Nó **không băm mã
nguồn**: sửa chú thích hay tách hàm không được thành "đổi năng lực", vì báo động
giả là cách nhanh nhất để một cổng bị tắt. Khoá bởi
`tests/test_verification_capability_identity.py` (13, có 7 phép tiêm I1–I7).

### Khoá 1:1 năng lực backend ↔ module frontend

`tests/test_runtime_identity.py::test_frontend_dang_ky_DUNG_nhung_id_backend_phat_ra`
đọc thẳng `frontend/src/simulations/index.ts` → các `register…Domain()` được gọi
→ hằng `id:` trong module tương ứng, rồi đòi tập ấy **bằng đúng**
`runtime_identity()["simulation_id"]`. Có ca tiêm lỗi (`…_DO_DUOC_khi_frontend_lech`)
và một ca chống rỗng-mà-xanh.

Nó **thay** `capability-descriptors.test.ts` (gỡ cùng test Tin học). Khác biệt cố
ý: bản cũ so qua artifact trung gian `capability-descriptors.json` nên có thêm
một khoảng lệch — "đã chạy generator" ≠ "đã đúng"; bản này không có artifact nào
để quên sinh lại. Chỉ đi qua các `register…Domain()` **được gọi thật**: một
module tồn tại mà không ai gọi thì không phải năng lực đang chạy.

⚠️ `frontend/src/simulations/capability-descriptors.json` **ở lại nguyên byte
nhưng đã ĐÔNG CỨNG** — 24 target Tin học, không generator, không sync-lock. Nó
là referent của `docs/SIMULATION_VISUAL_LANGUAGE_AUDIT.md` (một `*_AUDIT.md` =
bằng chứng wave đã qua, khoá bởi `visual-audit-completeness.test.ts`). Sinh lại
nó theo năng lực hình học sẽ biến bảng audit ấy thành 22 dòng nói về target
không còn tồn tại — tức viết lại bằng chứng lịch sử. **Đừng regenerate.**

## 0b. Điểm vào (entry point) — đã xác minh tồn tại ở baseline này

| Vai trò | Vị trí |
|---|---|
| HTTP surface | `backend/app/main.py` — `/api/analyze`, `/api/explain`, `/api/health`, `/api/diagnostics/runtime`, `/api/diagnostics/semantic` |
| Router gắn thêm | `accounts/router.py` · `accounts/classroom_router.py` · `accounts/session_router.py` (`include_router` ở `main.py`) |
| Production pipeline | `ai/pipeline.py::run_pipeline(text, api_key, pattern_store=None, observer=None)` |
| Hai stage LLM (tất cả) | `ai/pipeline.py::stage_semantic_analyze` (đề → `RequestContract`) · `stage_semantic_program` (contract → IR ứng viên, ≤`TRAN_SUA` lượt sửa) |
| Phán quyết tất định | `semantic_program/route.py::verify_and_compile` — MỘT cửa, mọi cổng nằm sau nó |
| Fail-closed ngoài miền | `main.py` (biên API) và `pipeline.py::run_pipeline` — đề không phải hình học ⇒ `unsupported` + `out_of_scope`, **0 lượt gọi** |
| Registry (FE) | `simulations/registry.ts` — `registerSimulation` / `getSimulation` / `listSimulations`; nạp qua `simulations/index.ts::registerAllSimulations()` gọi ở `main.tsx` **trước** render |
| Executor dispatch (FE) | `state/store.ts::loadEnvelope` gọi `getSimulation(id).validateConfig/init` — store **domain-blind** |
| Mặt 3D | `components/SimulationWorkspace.tsx` gắn `Scene3DExplorer` khi envelope mang `scene3d` hợp lệ (`hopLeScene3D`) — **không** đi qua registry |
| Lịch sử zero-AI | `state/history.ts` — `HISTORY_SCHEMA_VERSION`, `createHistoryStore`, `historyStore` |
| Đo lường telemetry & audit tài liệu | `backend/scripts/audit_docs_information_architecture.py` · `backend/scripts/collect_docs_telemetry_evidence.py` · `backend/scripts/pytest_telemetry_plugin.py` |

⛔ **Đã gỡ khỏi bảng này** (`GEOMETRY_PRODUCT_CUTOVER` → `FINAL_DEAD_EVALUATION_CLEANUP`):
`/api/edit`, `/api/manifest`; ba stage `stage_analyze`/`stage_classify`/`stage_simulate`;
`classify_with_one_route_recovery`; `app/validation/` (12 validator);
⛔ `simulation/catalog.py::CATALOG` — tất cả đều **đã gỡ**, tra ở git history.

## 0c. Trừu tượng DÙNG CHUNG — bắt buộc reuse, cấm viết bản thứ hai

Mỗi ô dưới đây có **một** chủ. Trước khi viết bất kỳ hàm nào chạm một trách
nhiệm ở đây, mở đúng module đó — bản thứ hai là cách kho này đã ship bug thật.

| Trách nhiệm | Module | Ghi chú |
|---|---|---|
| Dò miền + đường thực thi | `semantic_program/domain_profile.py` | `DOMAIN_HINH_HOC`, `co_duong_thuc_thi`, `khop_ky_hieu`, `program_skill_for`/`analyze_skill_for`. **Tất định, 0 lượt gọi.** Đề không ánh xạ được tới một nghĩa vụ CÓ checker ⇒ chặn trước mọi lượt LLM |
| Hợp đồng yêu cầu | `semantic_program/request_contract.py` + `analyze_contract.py` | `RequestContract` — dữ kiện đề bài **đã đóng băng** sau analyze. Mọi cổng phía sau đối chiếu với nó, không đối chiếu với văn bản gốc |
| Hợp đồng IR | `semantic_program/contract.py` | `SemanticProgramSpec` (Pydantic) + `SPEC_VERSION` + bốn biên chuẩn hoá. Sinh JSON Schema qua `scripts/export_semantic_program_schema.py` (**hai bản**, khoá bởi `test_schema_sync.py`) |
| Thẩm quyền KIỂU | `semantic_program/ir_static_check.py` | `_CHU_KY` (chữ ký biểu thức) · `_KIEU_DUNG` (phép dựng sinh ra gì) · `_TOAN_HANG_LENH` (ô toán hạng). **Nguồn duy nhất** — prompt, validator, grammar card đều dẫn xuất |
| Thẩm quyền PHÉP ĐO | `semantic_program/measure_contract.py::BANG_PHEP_DO` → `_KIEU_DO` | đại lượng nào đo được, đo *của* gì và *so với* gì |
| Thẻ văn phạm cho LLM | `semantic_program/grammar_card.py` | bề mặt IR mà mô hình đọc, **sinh từ Pydantic** — không gõ tay. ⚠️ **`_KIEU_TIN_HOC`** (2026-09-07): danh sách kiểu khai được nay dẫn bằng cách **LOẠI TRỪ** tập Tin học đã đóng băng, không bằng cách liệt kê tập hình học — bản liệt-kê-cái-được đã trôi HAI lần (thiếu `circle3`/`curved_solid`, rồi `ellipse3`), và hậu quả đo được là một lượt sửa mất trắng. ⚠️ **MỘT ngoại lệ từ 2026-09-07**: hằng `_DONG_XUAT_XU` là dòng **văn xuôi viết tay** duy nhất, nói *khi nào dùng ô xuất xứ nào* — quan hệ GIỮA ba trường, không thuộc `Field.description` của trường nào nên không sinh được. Khoá bằng `test_grammar_card.py::test_dong_xuat_xu_la_quy_tac_CHUNG` (cấm mọi tên điểm/fact/đáp số). `_VAN_XUOI["ratio"]` cũng viết tay nhưng là **nhãn của một trường có thật** — cùng hạng với `title`/`label` |
| Chuẩn hoá công thái | `semantic_program/hoisting.py` | nâng biểu thức lồng thành binding tạm; `contract.canonical_geometry_name` bóc `{"kind":"var"}`. Hai cơ chế, **cố ý không gộp** |
| Cổng grounding | `semantic_program/grounding_gate.py` | chương trình lấy dữ liệu ở đâu ra. Không truy được về đề ⇒ `INPUT_NOT_GROUNDED` |
| Cổng phủ (trung thực năng lực) | `semantic_program/coverage_gate.py` | `check_structural_coverage` (C₁a, trước khi chạy) + `check_realized_coverage` (C₁b, sau khi chạy). Phân biệt *không có đường* (chặn) với *có đường, thiếu checker* (đi tiếp, `servable=False`) |
| Compiler hình học TẤT ĐỊNH (OPT-IN) | `simulation/geometry_compiler/` | `fact_graph.py` (GeometryFactGraph, canonical + `kiem_mau_thuan`/`kiem_xuat_xu`; từ 2026-09-21 `kiem_mau_thuan` có lớp thứ ba `_kiem_nhieu_dinh_vuong` — luật `LUAT_NHIEU_DINH_VUONG` = `MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE`, mã `MA_MAU_THUAN_QUAN_HE` = `STRUCTURED_RELATION_CONTRADICTION`; `MA_MAU_THUAN` là bảng DUY NHẤT các mã "dữ kiện tự mâu thuẫn" mà định tuyến đọc; `MauThuanFact` mang `rule_id`/`chan_doan`/`bang_chung` từ vựng đóng) · `contract_adapter.py` (RequestContract → FactGraph; `KetQuaAdapter.rule_id` + `evidence`) · `primitives.py` (registry gồm 7 hàm, có `construct_prism`, biên dịch về IR HIỆN CÓ) · `compiler.py` (hỗ trợ 2 họ: pyramid và prism `SUPPORTED_FAMILY_PRISM` = `right_triangle_base_right_prism_volume`, eligibility + canonical layout + 7 bước `BuocDung` trace) · `routing.py` (`LLM_ONLY` mặc định / `DETERMINISTIC_FIRST` opt-in; mâu thuẫn ⇒ `REFUSE`, không lùi về LLM). ⚠️ **CHƯA nối vào `app/ai`** — hành vi mặc định không đổi |
| Chuẩn hoá xuất xứ THIẾT DIỆN | `semantic_program/section_provenance.py` | `normalize_section_provenance` · `chan_doan_chuan_hoa` · `CANONICAL_SECTION_KIND`. `polygon3` → `section` CHỈ KHI có `section_matches` với `solid`/`plane` giải được và chu trình khớp `cross_section`. Chạy ở `pipeline._dung_scene3d` NGAY SAU `build_scene3d`, TRƯỚC cổng trực quan. Immutable · idempotent · không import `scene3d` |
| Cổng phủ TRỰC QUAN | `semantic_program/visual_obligations.py` | `check_visual_obligations` · `ap_dung` · `chan_doan_truc_quan` · `kieu_canh_yeu_cau`. Hỏi *vật đề bảo VẼ có trong cảnh không* — kiểu · xuất xứ · topology. Chạy ở `pipeline` SAU `_dung_scene3d`, TRƯỚC `served`; **không import `scene3d`** (nhận cảnh dạng dict). Phát `ErrorCode.VISUAL_OBLIGATION_UNCOVERED` |
| Hậu điều kiện | `semantic_program/postconditions.py` | C₂ server-owned + `check_source_invariants` |
| Nghĩa vụ hình học | `semantic_program/geometry_obligations.py::GEOMETRY_CHECKERS` | 10 checker tất định (`point_on_line`, `point_on_plane`, `parallel`, `perpendicular`, `coplanar`, `distance`, `angle`, `volume`, `section_matches`, `radius`). Chủ thể mỗi checker phải phủ đúng `BANG_PHEP_DO` — khoá bởi `test_measure_checker_subject_drift.py` |
| Máy thực thi IR | `semantic_program/interpreter.py` + `geometry_exec.py` | `SemanticProgramInterpreter` — cầu nối IR ↔ nhân hình học |
| Nhân hình học CHÍNH XÁC | `simulation/geometry/` | bốn tầng **một chiều** `exact → predicates → kernel → measure` (+ `radical.py`, `section.py`, `curved.py`). `Fraction` + `Radical(he·π^mu·√can)`, **không float** |
| Bề mặt học sinh | `semantic_program/learner_surface.py` + `app/learner_messages.py` | KHÔNG để lộ token kỹ thuật; FE render qua MỘT `UnsupportedNotice`. `learner_reason` tra `_MSG_THEO_MA[error_code]` **trước** `failure_category` — mã chi tiết hơn loại, và lời khuyên đúng cho mã này là lời hứa sai cho mã kia |
| Từ chối CÓ CẤU TRÚC | `route.hong_truoc_khi_dung_ir` + `pipeline._that_bai_hinh_hoc` + `UnsupportedNotice::NHAN_GIAI_DOAN`/`NHAN_LOAI_VAN_DE` | Backend sở hữu `stage_reached`·`failure_category`·`error_code`; FE chỉ TRA NHÃN tiếng Việt (khoá kĩ thuật vào, tên ra). Thiếu trường ⇒ *"Không xác định được từ phản hồi cũ"*, **không** dò chuỗi. Khoá: `test_product_response_contract.py` + `refusal-contract.test.tsx` |
| Transport / envelope | `semantic_program/transport.py` + `pipeline_adapter.py` | `check_envelope_transport`; `SIMULATION_ID = "generic.semantic_program"` — id DUY NHẤT sản phẩm phát ra |
| Trace → cảnh 3D | `semantic_program/scene3d.py` + `visual_adapter.py` + `simulation_state.py` | `RENDER_HINT` khoá đồng bộ với `scene3d-model.ts::RENDER_KINDS` (`test_scene3d_ts_sync.py`) |
| Danh tính runtime | `app/runtime_identity.py` + `scripts/runtime_doctor.py` | `stable_capability_hash()` dẫn từ bốn bảng thẩm quyền — thêm một phép dựng là hash đổi, không sửa tay |
| Observer đánh giá | `evaluation/observer.py` | THỤ ĐỘNG — `None` ⇒ production không đổi một bit (bất biến #22). *2026-10-05 (`cuboid-acceptance`):* tham số thụ động là `run_pipeline(observer=…)` (khoá: `test_synthesis_repair_trace.py::test_F2_…`); lớp `AttemptObserver` không còn nơi nào dùng |

> **Lịch sử:** bảng này trước đây liệt kê `sufficiency_gate`, `completeness_gate`,
> `pipeline_stages`, `mechanism_gate`, `computation_gate`, `structure_gate`,
> `mechanisms`, `operations`, `descriptor`, `families/`, `dsl/manifest`,
> `catalog_conformance` — thẩm quyền của hệ Tin học, gỡ ở
> `LEGACY_INFORMATICS_REMOVAL` và `FINAL_DEAD_EVALUATION_CLEANUP`. Tra chúng
> trong git history, không tra ở đây.

## 0d. Luồng chính (đọc kỹ trước khi thêm nhánh mới)

**Hai lượt LLM, không một lượt thừa.** Nguồn: `pipeline.py::_chay_duong_hinh_hoc`.

1. **Cổng miền** — `/api/analyze` → `run_pipeline` dò miền. Không phải hình học
   ⇒ `unsupported` + `out_of_scope`, **0 lượt gọi**. Fail-closed ở cả biên API
   (`main.py`) lẫn pipeline.
2. **Cổng đường thực thi** — `co_duong_thuc_thi(text, DOMAIN_HINH_HOC)`: đề có
   ánh xạ được tới một nghĩa vụ **có checker** không. Tất định, **trước** mọi
   lượt gọi. Không ⇒ `not_simulation_suitable`.
3. **Analyze [LLM #1]** — `stage_semantic_analyze` đọc đề, trả `RequestContract`
   (điểm, quan hệ, đại lượng phải tính). Contract **đóng băng** từ đây.
4. **Tổng hợp [LLM #2]** — `stage_semantic_program` sinh `SemanticProgramSpec`
   ứng viên từ contract + thẻ văn phạm. ≤ `TRAN_SUA` lượt sửa, lý do từ chối
   nhồi ngược vào prompt — **không** phải retry HTTP.
5. **Chuẩn hoá tất định** — bốn biên trong `contract.py` + `hoisting.py`. Đếm ở
   `coercion_stats.py`: gộp im lặng thì không phân biệt được *"mô hình thỉnh
   thoảng viết dạng khác"* với *"hợp đồng đang mô tả sai"*.
6. **Phán quyết** — `route.verify_and_compile`, thứ tự **có ý nghĩa**:
   grounding → C₁a phủ cấu trúc → thẩm định tĩnh (`ir_static_check`) →
   **interpreter** → C₁b phủ đã hiện thực → bất biến nguồn → C₂ hậu điều kiện →
   transport → bề mặt học sinh. `servable` là thứ duy nhất quyết định có phát
   hay không.
7. **Envelope + Scene3D** — `pipeline_adapter` biên dịch trace thành
   `ValidatedSimulationEnvelope` mang `simulation_id = generic.semantic_program`
   và một `scene3d`.
8. **Frontend** — `store.loadEnvelope` → `module.validateConfig` → `init`;
   `SimulationWorkspace` gắn `Scene3DExplorer` khi `hopLeScene3D(scene3d)`.
   State là **ngữ nghĩa thuần**, không toạ độ pixel; renderer chỉ ĐỌC.
9. **Cache hit** — chỉ cache analyze **thành công**, khoá theo text đã chuẩn hoá
   + `CACHE_VERSION`.
10. **History reopen** — `store.reopenFromHistory` → thẳng vào engine tất định,
    **0 gọi AI** (bất biến #17).
11. **Từ chối** — bất kỳ cổng nào chặn → `unsupported` + `failure_category` +
    thông điệp học sinh; **không** dựng cảnh minh hoạ, không đoán toạ độ.

**Ranh giới R0 nằm giữa bước 4 và 5.** LLM sở hữu *chương trình ứng viên*; mọi
toạ độ, đại lượng, phán quyết đúng/sai đều do tầng tất định tính. Không lượt gọi
nào sau bước 4.

> **Lịch sử:** luồng cũ (analyze → representation plan → classify → ≤1 route
> recovery → 4 cổng computation/mechanism/input-sufficiency/completeness →
> simulate ≤3 lượt) là của hệ Tin học. Không cổng nào trong số đó **phán quyết
> được** về một đề hình học — enum `analyze.md` không có giá trị nào cho miền
> này — nên chúng được **thay**, không phải bỏ; xem docstring
> `_chay_duong_hinh_hoc`.


## 0e. Luật phụ thuộc (không được đảo — chi tiết ở ARCHITECTURE_MAP §4)

- LLM **không** sở hữu kết quả cuối; renderer **không** tính lại kết quả.
- Engine **không** phụ thuộc frontend; validator **không** phụ thuộc renderer.
- Hợp đồng dùng chung **không** phụ thuộc ngược vào implementation của family.
- `generic` **không** nhận `result_authority` kiểu algorithmic.
- Cấm circular import; family **không** import ngược orchestration nếu không cần.

## 0f. Giới hạn đã biết (trung thực)

Giới hạn của hệ **đang chạy** (hình học 3D). Diễn giải + bằng chứng:
`docs/research/CLAIM_EVIDENCE_MAP.md` (bản gốc §4: `docs/legacy/research/THESIS_READINESS.md`); ngữ cảnh kiến trúc: `docs/research/thesis/THESIS_ARCHITECTURE.md` §J.

| giới hạn | trạng thái |
|---|---|
| `CONTROL_FLOW_DEFINITE_ASSIGNMENT` | **PARTIAL** |
| `ANALYZE_SOURCE_FACT_COMPLETENESS` | **PARTIAL** — quan sát trên 4 đề, **chưa đo lặp lại** |
| ~~`SECTION_COPLANAR_EDGE_GAP`~~ | **CLOSED 2026-09-02** — nguyên nhân: một cạnh nằm trong mặt phẳng cắt thuộc HAI mặt kề nên cả hai cùng báo một đoạn, vòng nối vấp bản sao. Sửa bằng **khử trùng đoạn theo cặp đầu mút chính xác**. (SAC), (SBD), ACC′A′ nay dựng được; mặt phẳng trùng một mặt cho ra chính mặt ấy |
| ~~`MISLEADING_MALFORMED_SOLID_MESSAGE`~~ | **CLOSED 2026-09-02** — `MALFORMED_SOLID` nay CHỈ dành cho khối thật sự hỏng; thêm `SECTION_INTERSECTION_DEGENERATE` (giao ở chiều thấp) và `SECTION_CONSTRUCTION_INTERNAL_FAILURE` (lỗi của chính phép dựng) |
| chỉ khối **lồi**, **không** mặt cong (cầu/trụ/nón) | giới hạn phạm vi |
| `CURRICULUM_SUPPORT` | **PARTIAL** — phủ một phần, có chủ đích |
| `LEARNER_IMPACT_NOT_EVALUATED` | **OPEN / ngoài phạm vi** |
| `ANALYZE_STABILITY` | **NOT_MEASURED_BY_SCOPE_DECISION** — không kết luận ổn định/không ổn định |
| Deep hardening PATCH2/PATCH3 | chỉ có trong tag archive, **không merge lại** |

⛔ Giới hạn cũ đã gỡ khỏi mục này (thuộc hệ Tin học):
`database.relational_table_query` PARTIAL · backlog Analyze Integrity ·
coverage gap ở `simulation/coverage.py`.

## 0g. Chính sách cập nhật file này

**Phải cập nhật khi:** thêm/xoá family hoặc target · thêm contract/schema · đổi
entry point · thêm module lớn · đổi dependency quan trọng · đổi source of truth ·
đổi `CACHE_VERSION`/`HISTORY_SCHEMA_VERSION` · di chuyển file kiến trúc chính.

**Không cần cập nhật khi:** đổi tên biến local · thêm helper private nhỏ · sửa
CSS nhỏ · thêm một test lẻ.

> Quy mô hiện tại: **manual tracked index là đủ** — registry/target/family đã có
> generator tất định (`scripts/catalog_runtime_matrix.py`), không dựng thêm
> generator index/call-graph mới.

## 0j. THÀNH PHẦN ĐÃ GỠ (HISTORICAL_REMOVED) — chỉ mục truy vết

Chỉ mục này gom **43 mục ⛔** đang nằm rải trong file. Chúng KHÔNG bị xoá
khỏi index: mỗi mục còn giải thích *vì sao* một khuôn ra đời, và đó là giá trị truy
vết thật. Nhưng đọc xen kẽ mã đang chạy thì dễ tra nhầm — nên có bảng này.
Không ghi số dòng: số dòng trong tài liệu trôi mỗi lần sửa, và một chỉ mục
trỏ sai chỗ còn tệ hơn không có. Tra bằng `grep` theo tên bên dưới.

> **Luật đọc:** mọi mục dưới đây mô tả mã **không còn tồn tại**. Tra hiện thực cũ
> bằng `git log`/`git show`, đừng dựng lại. Năng lực đang chạy: §0b–§0d.

> **Vị trí (2026-10-05, `cuboid-final-review`).** Các mục mô tả chi tiết mã đã gỡ — 94 mục `###` (gồm các mục ⛔
> nói ở trên) và hai mục ⛔ §0h, §0i — không còn nằm rải trong file này: chúng được chuyển **nguyên văn** sang
> [`legacy/CODE_INDEX_REMOVED_ENTRIES.md`](legacy/CODE_INDEX_REMOVED_ENTRIES.md), mỗi khối ghi dòng gốc và sha256.
> Câu "nằm rải trong file" / "ở phần sau của file này" bên dưới đọc theo vị trí mới ấy; tra bằng `grep` ở đó.
> Chỉ mục ngắn dưới đây ở lại.

### SCENE3D_RETURN_TO_PRE_MOCKUP_PRODUCT_STATE 2026-09-12

⛔ **Mười hai file dưới đây KHÔNG còn tồn tại.** Người dùng yêu cầu đưa phần
mô phỏng hình học về đúng trạng thái **trước commit triển khai mockup đầu
tiên** (`7f34286`), tức về nội dung của `e6c2330`. Các mục mô tả chúng ở phần
sau của file này vẫn còn — giữ lại vì chúng ghi *vì sao* từng khuôn ra đời —
nhưng **đọc như lịch sử, không như mã đang chạy**.

Mã sản phẩm (`frontend/src/simulations/domains/geometry/`):

- `scene3d-tokens.ts` + `scene3d-tokens.test.ts` — bảng token mockup
- `scene3d-wide-line.ts` — nét dày theo pixel (`Line2`/`LineMaterial`)
- `scene3d-nhan.ts` — bộ giải đặt nhãn
- `scene3d-silhouette.ts` + `scene3d-silhouette.test.ts` — đường bao khối cong
- `scene3d-visual-language.test.tsx` · `scene3d-progressive-section.test.ts` ·
  `scene3d-dpr.test.ts` · `scene3d-orbit-lifecycle.test.tsx`

Công cụ đo (`frontend/scripts/`) — gỡ vì **không chạy nổi** sau khi phục hồi:
cả hai đọc `scene3d-tokens.ts`, và chủ thể chúng đo đã không còn.

- `scene3d-d2-gate.mjs`
- `scene3d-fidelity-gate.mjs`

⚠️ `scene3d-orbit-gate.mjs` **được giữ**: nó không đọc mã sản phẩm và vẫn chạy
được. Trên bản đã phục hồi nó báo `TRUC_TROI` ở cả ba ca (vòng 71–104°, trục
0,545–0,549) — đó là **phán quyết đúng về sản phẩm**, không phải cổng hỏng.

Báo cáo: `docs/SCENE3D_RETURN_TO_PRE_MOCKUP_PRODUCT_STATE.md`.

### FINAL_DEAD_EVALUATION_CLEANUP 2026-09-02

- `scripts/generate_dsl_contract.py` → `frontend/src/simulations/domains/generic/dsl-contract.json` (M13)
- `backend/scripts/curriculum_support_report.py`
- `evaluation/curriculum_schema.py` (M20 W2)
- `backend/scripts/curriculum_benchmark_report.py` (M20 W2A)
- `evaluation/harness.py`
- `evaluation/m16_schema.py`
- `evaluation/m16_record.py`
- `evaluation/m16_metrics.py`
- `evaluation/m16_offline_scripts.py`
- `evaluation/m16_artifacts.py`
- `evaluation/datasets/m16_catalog.py`
- `scripts/generate_m16_artifacts.py` → `docs/evaluation/m16/*.json` (M16)
- `scripts/generate_m16_live_artifacts.py` → `docs/evaluation/m16/*-baseline.json` (M16 live)
- `evaluation/live.py`

### FRONTEND_LEGACY_FIXTURE_CUTOVER 2026-09-02

- `frontend/src/simulations/domains/color/`
- `frontend/src/simulations/domains/logic/dag-module.tsx`
- `simulations/learner-gate.ts`
- `simulations/domains/generic/model.ts`
- `simulations/domains/generic/validate.ts`
- `simulations/domains/generic/patch.ts`
- `simulations/domains/generic/edit-policy.ts`
- `simulations/domains/generic/EditBar.tsx`
- `simulations/domains/generic/index.ts`
- `simulations/domains/generic/ui.tsx`
- `simulations/domains/algorithm/decision.ts`
- `simulations/domains/algorithm/condition-param.ts`
- `simulations/domains/algorithm/interaction-policy.ts`
- `simulations/domains/network/node-glyph.ts`
- `simulations/domains/network/encap-{model,ui,ui3d}.ts(x)` + `encap.ts`
- `simulations/domains/algorithm/program-module.tsx` (M17 W2C)
- `components/ScanActionZone.tsx`
- `simulations/domains/algorithm/ui.tsx`
- `simulations/domains/web/`
- `data/samples.ts`
- `data/sim-samples.ts`
- `components/SearchStateView.tsx`
- `simulations/domains/web/`
- `simulations/domains/web/`
- `simulations/renderer-fit.ts`
- `simulations/domains/tree/layout-size.ts`
- `frontend/src/simulations/domains/generic/layout-compiler.ts` (G1–G7)
- `frontend/src/simulations/domains/generic/anchor-resolver.ts` (Semantic Anchor System, G5)
- `frontend/src/simulations/domains/generic/disallowed-collision.ts`
- `frontend/scripts/replay-rectangular-pyramid-browser.mjs` — Runner tự động hóa browser replay (Playwright) trên desktop (1440x900) và mobile (390x844), xác minh Scene3D, nhãn A-D/S, thanh bước, chuỗi nhân quả và xử lý từ chối fail-closed cho chóp đáy chữ nhật.
- `frontend/scripts/replay-cuboid-cube-browser.mjs` — Runner Playwright desktop/mobile cho cuboid, cube và square-prism control; kiểm topology 8/12/6 và Euler=2, vị trí chiếu phân biệt, orbit, đủ 9 bước cuboid, bao đóng nhân quả chính xác (cả missing lẫn unexpected), raw-token leak, mobile overflow, console/exception và negative refusal; lỗi bất kỳ làm process thoát khác 0.
- `backend/scripts/generate_cuboid_cube_envelopes.py` — Sinh ba envelope production-route cuboid/cube/square-prism hoàn toàn offline; nhận `CUBOID_EVIDENCE_DIR` để wave mới không ghi đè artifact lịch sử.
- `backend/scripts/generate_cross_family_regression_envelopes.py` — Sinh envelope canonical production-route cho triangular pyramid, triangular prism và rectangular pyramid; chặn `call_gemini`, ghi rõ 0 live request và nhận `CROSS_FAMILY_EVIDENCE_DIR`.
- `frontend/scripts/compiler-scene-replay.mjs` + `compiler-scene-suite.mjs` — CLI replay cũ giữ tương thích; suite mode chạy Tier-A dùng chung cho triangular pyramid, triangular prism, rectangular pyramid, cuboid, cube và cross-section, với semantic polling, trusted pointer orbit có retry hữu hạn, formation tiến/lùi, bounded canvas pixel delta, negative production refusal và structured assertions.
- `frontend/scripts/compiler-scene-replay-lib.mjs` — Pure helpers sở hữu set closure ba nguồn, pairwise missing/unexpected, event-only dependency traversal, topology, formation visibility, computed-style readiness, canonical Git-blob source hashing và manifest validation. `compiler-scene-replay-lib.node-test.mjs` khóa các bất biến này bằng Node test độc lập với Vitest.
- `frontend/scripts/generic-tier-a-scenarios.json` — Frozen scenario manifest: viewport, topology, formation/orbit flags, causal target, independent oracle closure/source hash và section contract gate; không lấy oracle từ `scene3d.events` hay browser runtime.
- `backend/scripts/generate_generic_tier_a_fixtures.py` — (từ regular-square-pyramid-w01 thêm năm fixture `regular_square_pyramid_*`: dương S1 và bốn âm assumption · grounding · construction_binding · kernel — xem mục W1 ở bảng harness) Sinh 18 fixture production-route offline cho sáu family (dương · âm `NON_POSITIVE_LENGTH`/outside-plane · và từ W12 âm `_ungrounded`: một số liệu bị bỏ khỏi câu đề trong khi transport `analyze` giả vẫn khai nó, chương trình là bản biên dịch từ đề đủ, tuyến `LLM_ONLY` mặc định phải từ chối `GIVEN_VALUE_NOT_IN_SOURCE`, 2 lượt transport, không `scene3d`), bảo toàn provenance của canonical cross-section fixture và khóa outside-plane theo `PLANE_DOES_NOT_CUT`; `backend/tests/geometry/test_generic_tier_a_fixture_generator.py` kiểm chuỗi provenance/hash, đúng sáu family, sáu âm nguồn và 0 model call.
- `backend/scripts/build_generic_tier_a_contact_sheet.py` — Loại screenshot blank/sai kích thước bằng dynamic range/variance rồi dựng contact sheet có nhãn family/view/state; wave Scene3D repair hiện có 42 panel được chọn từ 95 screenshot.
- `docs/evaluation/geometry/runs/20260927-cross-family-scene3d-product-semantic-repair/` — Run package của sửa lỗi Scene3D xuyên sáu family: identity (`RUN.json`, `MANIFEST.json`), report, verification log, 12 input fixture, browser evidence, 95 screenshot và contact sheet.

## Backend — `backend/app/`

### `ai/gemini.py` · Change impact: targeted live
Lớp gọi Gemini + bộ nạp skill + **ngân sách API** (M7.14T).
Exports: `MODEL`, `SKILLS_DIR`, `MAX_ATTEMPTS`, `TRANSIENT_STATUS`, `load_skill`,
`call_gemini`, `ApiBudget`, `BudgetExceeded`, `set_budget`, `BUDGET`.
Deps: httpx. Consumers: `ai/pipeline`, `ai/edit`, `ai/explain`, `ingestion/input`
(mỗi module có **binding riêng** — mock một chỗ không che chỗ khác).
Tests: `test_gemini.py` (fake transport), `test_live_budget.py`.
Notes: **biên mạng duy nhất** của hệ. Guard offline nằm ở `conftest.py`, KHÔNG ở
đây (test_gemini có quyền dùng transport giả). `ApiBudget` inert khi `BUDGET=None`.

### `ai/pipeline.py` · Change impact: targeted live
> *2026-10-05 (`cuboid-acceptance`):* phần Tin học của mục này (classify, pattern reuse, M13–M15, các test nêu ở
> Deps/Tests) mô tả đường đã gỡ ở `6d5f5fda`/`e664f683`; bất biến #5/#6/#23 nay là **LỊCH SỬ**, #22 khoá bằng observer
> thụ động và runner nghiệm thu — đối chiếu từng hàng ở `ARCHITECTURE_MAP.md` §5.

Orchestrator: analyze → plan/gate → classify → (pattern reuse | simulate) → envelope.
Exports: `ANALYZE_SCHEMA`, `stage_analyze`, `stage_classify`, `stage_simulate`,
`stage_adapt`, `try_pattern_reuse`, `run_pipeline(text, api_key, pattern_store=None,
observer=None)`, (M15) `classify_with_one_route_recovery`, (vNext)
`stage_semantic_analyze`, `stage_semantic_program(text, analysis, api_key,
contract=None, observer=None)`, `MAX_SEMANTIC_PROGRAM_ATTEMPTS`,
`_envelope_tu_route_sinh`.
Deps: catalog, manifest, representation, semantic, patterns, gemini, (M15)
`mechanism_gate.check_mechanism_consistency_for_target`, `mechanisms.canonical_mechanism`.
Tests: `test_pipeline.py`, `test_reuse.py`, `test_capability_boundary.py`,
(M15) `test_pipeline_mechanism_consistency.py`.
Notes: capability gate chỉ chặn **đường generic** (bất biến #5). `pattern_store`
inject → None = hành vi compose cũ. (M14 bất biến #22) `observer` THỤ ĐỘNG —
`None` → hành vi production không đổi; eval đi CHUNG `run_pipeline`.
(M15) `classify_with_one_route_recovery(text, analysis, classification, api_key, observer=None)` —
route-consistency ordering: **≤ 1 reclassify BOUNDED** chạy TRƯỚC mọi
route-dependent gate khác khi `check_mechanism_consistency_for_target` phát
hiện `ROUTE_MECHANISM_FAMILY_MISMATCH` trên route đầu; reclassify ra
`unsupported` → passthrough (từ chối trung thực, không ép reclassify thêm lần
nữa); mismatch vẫn còn sau 1 lượt → `capability_gap`. Ngân sách cố định: analyze
tối đa 1 call, classify tối đa 2 (gốc + đúng 1 reclassify), simulate tối đa 1 —
không có đường quay lại vô hạn.
**(vNext 2026-08-23) `stage_semantic_program` nay ≤3 lượt**, gửi lỗi validator
ngược cho LLM sửa — khuôn `stage_simulate`. Lý do đo được: tám lượt probe E2E
trên một đề chết ở TÁM lỗi HÌNH DẠNG khác nhau (`container` nhận biểu thức rồi
nhận literal, `pop` viết như biểu thức rồi `peek` viết như câu lệnh…), không lỗi
nào là hiểu sai đề. Trần là HẰNG SỐ ⇒ claim D1 nguyên vẹn (lượt LLM chặn bởi
call graph, không theo độ dài trace). **Và nhánh PHÁT của route sinh nay chạy cả
khi `mismatch_gap` bắn**: trước đó một phán quyết lệch của classifier legacy
return TRƯỚC nhánh phát, giết một outcome `servable=true` (đo được: đề "đảo dãy
bằng ngăn xếp" đạt `stage_reached=served` rồi envelope trả `unsupported`). Cổng
mismatch bảo vệ đường module — chương trình ngữ nghĩa không đi qua target nào.
Envelope dựng ở MỘT chỗ: `_envelope_tu_route_sinh`.

### `ai/explain.py` · Change impact: targeted live
Q&A Socratic trên snapshot state THẬT. Exports: `EXPLAIN_SCHEMA`, `explain_state`.
Notes: **bề mặt hội thoại LLM duy nhất**; không phán đúng/sai, không điều khiển
mô phỏng.

### `ai/skills/*.md` · Change impact: targeted live
`analyze` `classify` `simulate` `explain` `transcribe` `edit`. Prompt là **file
markdown**, nạp qua `load_skill` (cache theo process → **restart backend** sau khi
sửa). Không bao giờ ship xuống trình duyệt.

### `frontend/scripts/after-matrix-w4b3a.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3A — MA TRẬN AFTER cho **toàn bộ** danh mục: ghép ba nguồn (descriptor sinh
từ registry + module frontend đang chạy qua CDP + `measure-1920.json`). Phân loại
trải nghiệm bằng luật KHAI TRƯỚC ở đầu file; **đếm tổng chỉ sau khi có bảng từng
target**. Tách bạch ĐO ĐƯỢC ↔ CHỈ KHAI BÁO (9/23 target chưa có bài mẫu offline
nên không dựng được state để đo) — cộng hai cột lại là tự cho điểm cao hơn bằng
chứng. Ba phép suy BỊ CẤM ghi ngay trong file: `predict` ⇒ thao tác trực tiếp ·
`timeline` ⇒ mô hình tương tác · có trong catalog ⇒ có phủ chương trình.
Artifact: `docs/evaluation/m17/w4b3a-after/after-matrix.{json,md}`.
Notes (M15 Task 16): `sorting` tốt nghiệp `PILOT` → `SUPPORTED` sau formalize
thành family selector (M14) + conformance proof (M15) — note tự giới hạn claim
(live n=4 M14 + n=2 M15 W1 — đếm case live chạm sorting gồm cả near-miss từ
chối đúng — là **targeted acceptance, KHÔNG phải bằng chứng thống kê**, không
được nói mạnh hơn). `binary_system` note bổ sung control cơ
số ≠ 2 (M15 W1: hex/octal → `capability_gap` có 2 lớp phòng thủ, xem
`mechanism_gate.py`).

### `frontend/src/simulations/transport-policy.ts` (M20 W7) · Change impact: offline
NGUỒN DUY NHẤT của chế độ transport: `FULL_TRACE` · `OPTIONAL_TRACE` ·
`RESET_ONLY`, khai cho cả 23 target kèm LÝ DO CƠ CHẾ. `SimulationControls` đọc
nó; `experience-manifest.test.ts` import lại từ đây thay vì giữ bản thứ hai.
⚠️ `transportModeOf` trả `null` cho target chưa khai — KHÔNG có mặc định. Trước
W7, dải điều khiển phân loại bằng `timeline.stepCount(state) > 1`, đúng kiểu suy
diễn kĩ thuật §9 cấm: `base_conversion` có 12 bước nên được dòng thời gian đầy
đủ, dù sau W5 kết quả của nó đọc được ngay. Số hiện tại: **13 / 7 / 3**.

### `frontend/scripts/certify-experience-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi: **ĐÓNG thử thách rồi, học sinh làm được gì có nghĩa trên màn này?** — tầng
thứ ba, khác hai tầng đã có: `interaction-semantics.test.ts` hỏi *module nhận
action gì* (hợp đồng), `certify-viewports-w12.mjs` hỏi *affordance có thấy được
không* (bề mặt).
Phân loại: đổi được đầu vào ⇒ `TOOL_PASS` · không đổi được nhưng tua THAY THẾ ⇒
`TRACE_PASS` · không đổi được và tua chỉ THÊM DỒN ⇒ **`EXPERIENCE_FAIL`**.
⚠️ "Tua thì màn hình đổi" KHÔNG phân biệt được gì — trình chiếu cũng đổi. Nên
phép đo tách **thêm dồn** (bước sau chứa trọn bước trước = bảng in dần từng
dòng, đáp án có sẵn) khỏi **thay thế** (giá trị bị đổi, vùng xét co lại = cơ chế
đang chạy).
⚠️ Ứng viên action sinh từ config, và hình dạng phải ĐỌC `simulations/types.ts`:
đoán `whatif_swap {from,to}` / `toggle {id}` thì action bị **nuốt lặng lẽ** và
`find_max` đọc ra TRACE_PASS trong khi nó là công cụ — đoán sai ở đây luôn đánh
giá THẤP sản phẩm. Hợp đồng thật: `{i,j}` · `{target}` · `{a,b}`.
⚠️ PHÉP ĐO NÀY ĐÃ SAI BỐN LẦN, và **cả bốn lần đều đánh giá THẤP sản phẩm** —
ghi lại để lần sau không lặp:
1. So `st.cursor` (không tồn tại ở tầng store) ⇒ mọi vòng lặp thoát ngay bước
   đầu, báo "1 bước" cho cả 23 target.
2. Đoán hình dạng action (`whatif_swap {from,to}`, `toggle {id}`) ⇒ action bị
   **nuốt lặng lẽ**. Hợp đồng thật ở `simulations/types.ts`: `{i,j}`, `{target}`.
3. Đoán TÊN action theo TÊN field config: `decimal_to_binary` khai
   `decimalValue` nhưng `apply` nhận `set_param {name:'decimal'}` — đọc ra
   `STATIC_ILLUSTRATION` cho một bài mà `narrate` nói thẳng "bấm từng bit".
4. Chỉ đo CHỮ trong `.sim-stage` ⇒ mất hai thứ: dải quan sát
   (`.search-observe` là ANH EM của `.sim-stage`, và chính nó đổi theo bước) và
   MÀU (`ScanWorkspace` chỉ vẽ `ArrayView` — cột nào đang xét mã bằng `fill`).
   Cho ra "13 bước engine, 1 bước màn", một kết luận sai về sản phẩm.
Nay dấu vân = chữ CẢ THẺ (trừ đồ đạc) + `fill`/`class` của mọi phần tử SVG.
Vẫn KHÔNG bắt được vị trí/kích thước — giới hạn, không phải đã phủ.
Số hiện tại: **20 TOOL_PASS · 3 TRACE_PASS · 0 EXPERIENCE_FAIL**. Chênh
engine/màn còn lại (40→14, 33→14…) là trần 14 bước của vòng lặp, không phải lỗi.

### `frontend/scripts/faultcheck-visual-weight-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Chứng minh `certify-visual-weight-w12.mjs` **còn đỏ được**. Phép đo ấy đã bị NỚI
ba lần để nhìn thấy `<canvas>`, DOM thật, rồi `.encap-layer` — mỗi lần nới là
một lần dễ xanh hơn, nên con số 23/23 chưa đáng tin cho tới khi có đối chứng.
Ba nhánh: giấu khối cơ chế thật ⇒ **ĐỎ** · phình vỏ rỗng `.encap-2d` ⇒
**KHÔNG được xanh** · nguyên trạng ⇒ **XANH**. Mỗi nhánh chứng minh
`MUTATION_OBSERVED` trước khi phán — phép tiêm không chạm đối tượng thì kết quả
của nó vô nghĩa.
Số hiện tại: **3/3 đúng kì vọng** (nguyên trạng ink 0,39 · 8 chủ sở hữu).

### `frontend/scripts/certify-visual-weight-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi câu mà MỌI tiêu chí W12 khác bỏ sót: **trên sân khấu, HÌNH chiếm bao nhiêu
so với CHỮ?** Các tiêu chí trước chỉ hỏi "đổi đầu vào thì kết quả có tính lại
không" — nên `network.packet_routing` (4 biểu tượng đứng yên + 4 bước chữ) đạt
hết, trong khi mở ra nhìn thì nó là hình minh hoạ có chú thích.
Đo `inkShare` (diện tích svg/canvas/`.web-page` trên diện tích thẻ) và
`proseChars` (chỉ khối văn xuôi; KHÔNG tính nhãn trong hình, KHÔNG tính ô bảng
— bảng LÀ kết quả engine, phạt nó là phạt nhầm). Bài có bảng được miễn ngưỡng
`inkShare`, và điều đó ghi rõ chứ không miễn lặng lẽ.
⚠️ Ngưỡng `MIN_GLYPHS` của bản đầu ĐÃ GỠ vì nó SAI hai đường: đo kích thước dữ
liệu (dãy 3 phần tử có 5 hình chữ nhật) và không nhìn được vào `<canvas>` — nó
vừa gán "tranh tĩnh" cho cảnh 3D thật. `glyphs` còn trong artifact để đọc.
⚠️ Đo BỀ MẶT, không đo hiểu biết — `LEARNER_IMPACT_NOT_EVALUATED` giữ nguyên.
⚠️ Hai ngoại lệ, cả hai đều KIỂM NGƯỢC được nên không nuốt được luật: bài có
`<table>` (bảng là kết quả engine) và `CODE_IS_THE_MECHANISM`
(`bounded_control_flow` — sân khấu là mã giả có con trỏ dòng, như trình gỡ lỗi;
vẽ thêm hình ở đó là trang trí). Khai "mã là cơ chế" mà lại nhiều hình ⇒ ĐỎ.
Số hiện tại: **23/23 lấy HÌNH làm chính**.

### `frontend/scripts/certify-scroll-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Hỏi: vỏ ứng dụng có đọc thành MỘT khối liền, và máng cuộn có ổn định không?
5 màn × 4 bề rộng trên `browser-runner.mjs`: home · library · history ·
workspace gọn · workspace rất dài — cố ý phủ cả trang KHÔNG cuộn lẫn trang cuộn.
Khẳng định: header trải hết bề rộng vỏ · máng đúng bằng bề rộng thanh cuộn đã
khai (10px) · không tràn ngang · **máng giống nhau giữa trang ngắn và trang
dài** (không nhảy ngang — phép so này mới là câu hỏi thật; đo một màn thì không
bao giờ phát hiện được nhảy).
⚠️ KHÔNG đo được thumb có nhìn thấy hay không: CDP không đọc computed style của
`::-webkit-scrollbar-thumb`. Việc đó do `styles/scrollbar-ownership.test.ts`
khoá ở mức mã nguồn — ranh giới này ghi thẳng vào artifact, không để một con số
trông-như-đã-phủ.
⚠️ KHÔNG đảo quyết định W4B-1A (cuộn thuộc về TÀI LIỆU, không phải panel): vùng
cuộn nội bộ từng giấu 170px nội dung học mà không có tín hiệu ở mức trang.

### `frontend/src/simulations/action-probe.ts` (M20 W12) · Change impact: offline
NGUỒN DUY NHẤT của câu "học sinh có đường nào đổi đầu vào bài này không".
`candidateActions(config)` dẫn ứng viên từ config đã validate; dùng bởi CẢ
`experience-gate.test.ts` (offline, <1s) lẫn `scripts/certify-experience-w12.mjs`
(trình duyệt, qua `session.mods.probe`).
⚠️ TÊN ACTION KHÔNG SUY ĐƯỢC TỪ TÊN FIELD CONFIG — nó nằm trong `module.apply`.
Đã sai ba lần trong W12 và **cả ba đều đánh giá THẤP sản phẩm**, vì action sai
hình dạng không ném lỗi mà bị `apply` trả về state cũ, đọc y hệt "bài này không
tương tác được": `whatif_swap {from,to}`→`{i,j}` · `toggle {id}`→`{target}` ·
`set_param 'decimalValue'`→`'decimal'`. Thêm target mới thì MỞ MODULE RA ĐỌC.

### `frontend/src/simulations/tool-affordance.ts` (M20 W12) · Change impact: offline
NGUỒN DUY NHẤT của câu hỏi "công cụ thao tác của học sinh có được hiện ra
không". `toolAffordanceOpen({exploreOpen, challengeOpen, busy})` — hàm THUẦN,
kiểm được không cần Chrome. Cả `domains/algorithm/ui.tsx` (kéo cột) và
`domains/network/ui.tsx` (ngắt/nối liên kết) đọc nó.
⚠️ Trước W12 hai miền chép tay CÙNG một luật (`exploreOpen && !busy`), nên công
cụ nằm sau một nút học sinh phải tự biết bấm: đo trên trình duyệt được **52/92**
dòng ma trận bề rộng "không có affordance". Luật nay là W12 §6 Policy B — thử
thách ĐÓNG thì công cụ dùng được; MỞ thì có thể siết để câu hỏi đang chờ không
bị chính học sinh vô hiệu hoá. `mode: "hidden"` của `interaction-policy.ts` vẫn
thắng tuyệt đối (kéo ở `sum_if`/`count_if` là trang trí).
⚠️ Bật affordance KHÔNG nâng hạng ngữ nghĩa: `whatif_swap` vẫn là
INPUT_MANIPULATION (W12 §8) — phân loại thuộc `interaction-semantics.test.ts`.

### `frontend/scripts/e2e-stack-production.mjs` (vNext) · **TIÊU QUOTA THẬT**

E2E đường NGƯỜI DÙNG: gõ đề vào `.composer-text`, bấm `.composer-send`, chờ HTTP
`/api/analyze` thật, rồi bấm `button[title="Tiến một bước"]`. **Không**
`loadEnvelope`, không fixture, không sample offline — đó là ranh giới với
`capture-stack-vnext.mjs` bên dưới, thứ chỉ là bằng chứng COMPONENT.

Chộp response `/api/analyze` qua `page.on("response")` làm nguồn sự thật cho
"route nào đã phục vụ" (`simulation_id` / `source`), vì UI không hiển thị điều
đó. Kết quả: `docs/evaluation/semantic-vnext/e2e/`.

⚠️ Mỗi lượt là một request phân tích thật (nhiều lượt LLM phía backend) và tiêu
một lượt dùng thử của khách. Cần `SEMANTIC_ROUTE_MODE=serve` ở container thì
route sinh mới chạy. Backend chạy uvicorn KHÔNG reload dù `app/` được bind-mount
⇒ sửa mã Python xong phải `docker compose restart backend`, nếu không đo phải
bản cũ trong bộ nhớ.

### `frontend/scripts/certify-transport-vnext.mjs` (vNext) · cần dev server + Playwright

Sở hữu tầng bằng chứng **transport qua CONTROL THẬT**: bấm đúng nút "Sau"/"Trước"
trên trang rồi hỏi *màn hình có đổi không*. Ranh giới với `learner-gate.test.ts`:
test đó gọi `mod.timeline` TRỰC TIẾP nên chứng minh hợp đồng ở tầng engine, không
chứng minh nút bấm nối được vào engine — đúng khoảng trống mà sự cố `main.py`
quên `semantic_route` đã phơi ra (mảnh nào cũng xanh mà chưa mảnh nào được ghép).

Dùng **bài mẫu offline** (`data/samples.ts`) nên **0 gọi `/api`, 0 quota, không
inject store** — người dùng chọn bài, bấm nút, trạng thái đổi thật.

Hai điều kiện của anti-pattern #14 đều có: **dấu vân tay trang** (đúng bài + >1
bước, sai thì thoát != 0) và **`--faultcheck`** (chặn sự kiện nút "Sau" ⇒ bản
soát phải TỤT ĐIỂM). Chạy: `node scripts/certify-transport-vnext.mjs --port 3177
[--faultcheck]`.

### `frontend/scripts/certify-transport-vnext.mjs` (vNext) · cần dev server + Playwright

Sở hữu HAI bản soát trên UI THẬT, **không inject store**: §6 transport (Tiến ·
Lùi · Về đầu · Dựng lại · Tự chạy/Dừng) và §5 rõ ràng thị giác ở ba bề rộng.
Dùng **bài mẫu offline** (`data/samples.ts`) nên 0 API call — người dùng chọn
bài, bấm nút, trạng thái đổi thật. Ba miền: array/quét · tree/duyệt · graph/BFS.

Hai cái bẫy đã cắn và nay ghi lại trong code: nút bước là nút ICON chỉ có
`title` (tìm theo chữ trượt IM LẶNG), và `Tự chạy` **đổi nhãn thành `Dừng`** sau
khi bấm. Nhịp tự chạy đo được ~1 bước/giây, tick đầu ~1,2s — chờ 900ms thì bản
soát vu oan cho sản phẩm.

Đo HÌNH HỌC chứ không so pixel (repo không có `@playwright/test`): chữ SVG nằm
trong khung vẽ · không tràn ngang · không chữ kích thước 0 · nút bước còn bấm
được. `--faultcheck` chặn nút Tiến ở tầng capture để chứng minh guard đỏ được.

**`SUPPORTED_MIN_WIDTH = 320px`**, khoá bằng hai viewport `min-320`/`min-344`
trong chính runner. Trước vNext bố cục tràn ngang dưới ~354px và trang mất dữ
liệu ở mép phải; truy được chuỗi `.control-zone` (nowrap, 252/304px) →
`.player` (229px) → `.panel-controls` → `.app-layout` → `html`. Sửa bằng
`flex-wrap` trên `.control-zone` ở `global.css` — một luật ở tầng dùng chung,
không vá theo ảnh chụp, và không breakpoint nào phải nhớ vì wrap chỉ kích hoạt
khi hết chỗ (màn rộng không đổi một pixel).

### `frontend/scripts/capture-stack-vnext.mjs` (vNext) · cần dev server + Playwright

Bằng chứng trình duyệt cho case Stack `{[()]}`: tiêm envelope thẳng qua
`useAppStore.loadEnvelope`, đặt cursor tới 6 khung mốc, chụp ảnh và trích **phép
chiếu ngữ nghĩa từ DOM** (nội dung `<text>` trong SVG) — không so pixel. Kết quả:
`docs/evaluation/semantic-vnext/browser-evidence/` (`stack-visual-acceptance.json`
· 6 ảnh); báo cáo đi kèm ở `semantic-vnext/reports/STACK_VISUAL_ACCEPTANCE.md`.

Hai điều kiện của anti-pattern #14 đều CÓ THẬT trong script: **dấu vân tay trang**
(khẳng định đúng tiêu đề + 7 bước, sai thì thoát `3`) và **`--faultcheck`** (thay
`push`/`pop` bằng `highlight` ⇒ bản soát phải tụt khỏi 6/6, không tụt thì thoát
`4`). Chế độ tiêm lỗi tái hiện đúng triệu chứng gốc — ngăn xếp rỗng ở mọi khung
trong khi narration vẫn kể push/pop.

⚠️ Bộ trích phải LOẠI chú giải trình bày khỏi danh sách phần tử: lượt chạy đầu
nuốt nhãn `← TOP` vào `stack` và báo FAIL nhầm 4 khung. Chú giải không phải dữ
liệu. ⚠️ Cổng 3000 hay bị chiếm bởi dev server khác đang chạy mã CŨ; dùng
`--port` để dựng server riêng, đừng chụp vào cổng lạ (tiền lệ `0a71268`).

### `frontend/scripts/capture-phase-evidence.mjs` (W6) · cần `npm run dev` + Chrome
Chụp CLIP theo `.workspace-card` ở MỘT trạng thái xác định (`--target`,
`--viewport`, `--act`). Ghép với `git checkout <ref> -- <file>` (Vite HMR nạp lại
ngay, không cần dựng lại) thì có cặp TRƯỚC/SAU trên cùng máy, cùng bề rộng, cùng
đề — khác biệt duy nhất là bản vá. Dùng để chứng minh một pha có HẬU QUẢ HỌC SINH
NHÌN THẤY, chứ không chỉ có hợp đồng/test đã đổi.
⚠️ URL module lấy từ `performance.getEntriesByType('resource')`, KHÔNG `import()`
đường trần: Vite băm URL theo phiên nên import trần tạo instance THỨ HAI với store
rỗng. ⚠️ Phải nạp trước bốn module rồi mới dùng — lượt `import()` đầu của module
nặng có thể chưa trả kịp qua CDP, và khi ấy `Runtime.evaluate` trả `undefined`
CHỨ KHÔNG ném. Cả hai đều từng làm script im lặng hỏng.

### `frontend/src/core/predicate.ts` (W5C) · Change impact: offline
CHỦ SỞ HỮU DUY NHẤT của "sáu phép so sánh `> >= < <= == !=` nghĩa là gì".
`compareNumbers(x, op, y)` + `includesBoundary(op)` — hàm THUẦN trên hai SỐ.
⚠️ Trước W5C cùng sáu toán tử được cài BA LẦN: `algorithms.ts::testCondition`
(sum_if/count_if), `scan.ts::opHolds` (algorithm.scan), và nhánh `compare` của
`program.ts` (bounded_control_flow). Ba bản đồng ý nhau vì MAY, không vì có gì
bắt chúng thế — và một lần đổi `>=` thành `>` ở một bản chỉ chấm sai đúng những
học sinh ở NGƯỠNG, tức chỗ bài học nằm ("từ 8,0 trở lên" ≠ "trên 8,0"). Cả ba
nay uỷ quyền xuống đây.
⚠️ `switch` cố ý KHÔNG có `default` — vét cạn để tsc đỏ khi thêm toán tử thứ
bảy. Đó chính là bẫy `program.ts` từng mắc: `default` cũ trả `l >= r`, nên mọi
op không khớp lặng lẽ thành `>=`. Nay op lạ thì NÉM.
⚠️ `program.ts` giữ riêng `==`/`!=`: ở đó hai vế có thể là bool/chuỗi, nên đó là
so sánh đồng nhất chứ không phải so sánh SỐ. Chỉ so sánh THỨ TỰ uỷ quyền xuống.
Khoá bởi `core/predicate-family-w5c.test.ts`: bảng chân trị 6 op × 3 quan hệ
VIẾT TAY (sinh từ code sẽ là test tự xác nhận) + đối chiếu đáp số engine + guard
chống mọc bản cài thứ tư.

### `frontend/src/simulations/color-channels.ts` (W5A) · Change impact: offline
CHỦ SỞ HỮU DUY NHẤT của phép toán BA KÊNH ↔ MỘT MÀU, dùng chung cho
`web.style_model` và `color.rgb_model`. Giữ `Channel`/`CHANNELS`/`CHANNEL_LABEL`/
`CHANNEL_MAX`, mẫu `HEX_COLOR`, `rgbOf`/`hexOf`/`rgbTextOf`/`cssColorOf`,
`isChannelValue`/`clampChannel`, `channelRamp` (vệt màu của thanh trượt) và
`readableInkOn` (chọn màu CHỮ đặt trên ô màu theo luma BT.601).
⚠️ Nâng từ `domains/web/props.ts` trong W5A — trước đó phép toán thuộc sở hữu
của MỘT miền, nên miền thứ hai chỉ có hai lối: import chéo miền (đảo hướng phụ
thuộc) hoặc chép lại (hai bản `hexOf`, và ngày chúng lệch thì hai màn hình nói
hai giá trị khác nhau về cùng một màu).
⚠️ `channelRamp` giữ HAI kênh kia cố định — đó là điều kiện để vệt màu nói thật
về màu sắp nhận được; một vệt đỏ-thuần cố định sẽ nói dối.
⚠️ `clampChannel` dùng ở BIÊN NHẬN (thanh trượt/ô số), KHÔNG dùng để chữa config
sai — kẹp im lặng ở đó biến một đề hỏng thành mô phỏng trông như đúng.

### `frontend/scripts/measure-transport-w7.mjs` (M20 W7) · offline (cần `npm run dev`)
Hỏi: cơ chế to nhỏ khác nhau thì khay điều khiển có đổi bề rộng theo không? Đo
độ LỆCH bề rộng qua nhiều target thay vì so với một con số ma. Đo ở HEAD
104c752: cơ chế lệch 849px, khay lệch **đúng 849px** — bám 1:1; sau W7 khay lệch
**0px**.
⚠️ Đếm HÀNG bằng TÂM DỌC có dung sai, không bằng mép trên: `align-items: center`
khiến ba cụm khác chiều cao có mép trên lệch vài pixel dù cùng một hàng, và bản
đầu vì thế báo 3 hàng cho một dải rõ ràng một hàng. Artifact:
`docs/evaluation/m20/transport-{before,after,catalog,browser}.json`.

### `frontend/scripts/verify-point-projection.mjs` · offline (cần `npm run dev`)

CHIẾU toạ độ thế giới → màn hình rồi BẤM ĐÚNG CHỖ ĐÓ, cho từng đỉnh. **0 API
call.** Dựng lại đúng camera của khung nhìn (`(6,5,8)` nhìn về gốc, FOV 50°),
`Vector3.project`, rồi `Input.dispatchMouseEvent` tại điểm ảnh tính được.

Vì sao cần: wave trước quét MÙ 2907 điểm ảnh và chỉ trúng `A`. Quét mù không
phân biệt được "đích bấm nhỏ" với "vật không nằm ở chỗ nó phải nằm". Bấm đúng
chỗ đã chiếu thì phân biệt được — và nó chỉ ra nguyên nhân thật: vòng dựng
cảnh GHI ĐÈ `position` của điểm bằng khoảng dịch bung hình, kéo mọi đỉnh về
gốc toạ độ. `camera.project` ở đây là CHẨN ĐOÁN TRÌNH BÀY, không giá trị nào
đi vào `GeometryState`/checker/phép đo.

⚠️ Ô soi hiện **NHÃN**, không hiện id (`M` có nhãn *"Trung điểm M của SA"*).
So id với nhãn là phép so sai — nó đã báo `M` trượt oan một lượt.
Kết quả: `docs/evaluation/geometry/manual-demo-5/POINT_PROJECTION.json`.

### `frontend/scripts/demo-geometry-interaction.mjs` · offline (cần `npm run dev`)

DEMO TAY giao diện 3D tương tác trong Chrome **thật** — WebGL thật
(SwiftShader qua cờ `webgl` của `browser-runner`), chuột thật qua
`Input.dispatchMouseEvent`. **0 API call, 0 LLM.** Ghi 8 ảnh +
`DEMO_RESULT.json` vào `docs/evaluation/geometry/manual-demo/`.

Bài demo là **phát lại tất định** của `phase7a-pilot-sau-71/1-trung-diem-lan3`
— một lượt LIVE thật, `served`, oracle đúng — không phải fixture viết tay.

Nó đã trả công: lượt chạy đầu tìm ra một CRASH mà 1674 test vitest bỏ sót
(`visual_transform` khai `ExactVec3` nhưng phép bung sinh `"0.244949"`), và
lộ ra mặt/cạnh có trong cây mà không được dựng trong khung nhìn.

⚠️ Hai cái bẫy của chính bộ đo, đã bịt và đừng lặp lại: `clickText` quét CẢ
TRANG nên bấm nút tên `"A"` trúng logo **AlgoSim** (dùng `bam()` — chỉ trong
`.geo3d-explorer`); và bấm ở bước 0 thì trên màn gần như không có gì, nên phải
kéo thanh trượt tới bước cuối trước khi đo picking.

### `frontend/scripts/png-pixels.mjs` · offline

Sở hữu **giải mã PNG và ĐO BỀ DÀY NÉT TỪ ĐIỂM ẢNH**. Exports: `docPNG` ·
`anhPhang` · `doBeDayNet` · `doBeDayCucBo` · `anhThu`.

Vì sao tồn tại: token khai cạnh thấy 2,8 px, nhưng renderer vẽ cạnh bằng
`THREE.Line` và **WebGL bỏ qua `linewidth`** — giá trị trong mã không nói gì về
thứ hiện trên màn hình. Đọc `linewidth` rồi tuyên bố "2,8 px" là đo BỘ ĐO chứ
không đo HỆ.

⚠ **Hai hàm đo, dùng đúng chỗ.** `doBeDayNet` phân loại theo màu TUYỆT ĐỐI —
chỉ đúng trên ảnh nền phẳng (SVG mockup); trên ảnh sản phẩm nó vỡ vì mặt khối
tô 0,07 và nền thiết diện tô 0,14 nằm đúng trên đoạn nền→màu nét, cùng một ảnh
cho ra trung vị 0,09 px và max 45 px. `doBeDayCucBo` không hỏi màu: nó tìm cực
tiểu độ sáng so với nền NGAY CẠNH rồi tích phân mực — đây là hàm dùng cho ảnh
sản phẩm. ⚠ Nó **bão hoà ở ~2,0** với nét ≤1,6 px (chính xác từ 2,2 px trở
lên), nên số 2,0 đọc là *"không quá 1,6 px"*.

`anhThu(beDay)` dựng nét tổng hợp có bề dày biết trước — bộ đo phải tự kiểm
được bằng nó trước khi ai tin một con số nào.

### `frontend/scripts/scene3d-browser-acceptance.mjs` · offline (KHÔNG cần `npm run dev`)

Sở hữu **cổng trình duyệt chạy trên BẢN DỰNG SẢN PHẨM**. Exports: `TRANG_THAI` ·
`tiLeMuc` · `NGUONG_MUC` · `dungVaDongDau` · `phucVu` · `doDuong` ·
`dungBuocCuoi` · `phanLoai` · `motLuot`.

Vì sao tồn tại: `spot-check-demo.mjs` nạp cảnh bằng `import('/src/state/store.ts')`
— đường **chỉ có trên Vite dev**, tức mọi lượt đo phải đi qua transport đã biết
là chập chờn (dev kẹt 2/15 phiên · bản dựng 0/15). Cổng này phục vụ `dist/` tĩnh
và vào bằng `window.__ALGO_SIM_STORE__`, thứ `main.tsx` phơi ra ở CẢ hai chế độ.
Đo được: baseline 3/3 PASS, candidate 3/3 PASS — nền lập lại được.

⚠ **Hợp đồng sẵn sàng có `EXPECTED_STEP_VISIBLE`, và nó là bắt buộc.**
`loadEnvelope` đặt cảnh ở **bước 0** (chỉ điểm tự do); lượt chạy đầu của cổng
báo PASS 7/7 trên bảy ảnh chỉ có năm chấm đen. Tua bằng nút **"Bước sau"** —
`store.toEnd()` là NO-OP vì tuyến hình học đi thẳng vào `Scene3DExplorer`, bước
nằm ở state của explorer chứ không ở timeline của store.

⚠ Server tĩnh chỉ fallback `index.html` cho đường **không có phần mở rộng**.
Fallback cho mọi đường khiến một chunk `.js` bị mất vẫn trả HTTP 200, và phép
tiêm "entry chunk mất" LỌT.

### `frontend/scripts/scene3d-acceptance-report.mjs` · offline

Gom kết quả các lượt chạy thành `PIXEL_WIDTH_MEASUREMENTS.json` ·
`READINESS_DIAGNOSTICS.json` · `SCREENSHOTS.json` và dựng `CONTACT_SHEET.png`
đặt ảnh sản phẩm cạnh mockup đã duyệt. **Không** tự chạy trình duyệt — tách
phần ĐO khỏi phần KỂ để báo cáo không sửa được một con số nào.

### `frontend/scripts/photo-problem-browser-check.mjs` (2026-09-13) · offline · 0 lượt gọi model
Kiểm luồng ẢNH ĐỀ BÀI → XEM LẠI → DỰNG trên Chrome thật, bản dựng tĩnh `dist/`, ở
1440×900 và 390×844 (DPR 2, `mobile`). Mọi `/api/*` chặn ở biên mạng bằng
`interceptJson`: phản hồi đọc ảnh là fixture do backend dựng, envelope là fixture
p3. Ảnh chọn bằng `DOM.setFileInputFiles`; yêu cầu `/api/*` được ghi TRONG TRANG
(bọc `fetch`), vì `Fetch.requestPaused` không bảo đảm chở thân yêu cầu lớn. Mười ô:
nút Chụp/Tải + `capture` · ảnh xem trước giải mã được · xoay và gửi `rotation` ·
bấm Đọc hai lần = MỘT yêu cầu · ô nội dung có `label` + phải xác nhận ·
`/api/analyze` nhận ĐÚNG văn bản đã sửa, một lần · canvas 3D · không tràn ngang ·
ảnh chỉ có hình ⇒ `role=alert`, 0 yêu cầu dựng · gõ tay không hồi quy. Phép tiêm
`--tiem sai-van-ban | tran-ngang`. Dùng `phucVu` + `kiemDistMoi` (nay được
`export`) của `scene3d-orbit-gate.mjs`. ⚠️ Bằng chứng FIXTURE cho giao diện, không
phải bằng chứng provider.

### `frontend/scripts/compiler-scene-replay.mjs` (2026-09-21) · offline · 0 lượt gọi model

**PHÁT LẠI** cảnh do **primitive compiler tất định** dựng, trên Chrome thật và bản
dựng tĩnh `dist/`, ở 1440×900 và 390×844 (DPR 2, `mobile`). Envelope đọc từ **TỆP**
(`--envelope`, mặc định `REPLAY_ENVELOPE.json` của wave tái kiểm) và được trả ở
biên mạng qua `interceptJson("*/api/*")`; `/api/*` lạ nhận 404. Mười một ô: bấm
được nút gửi · `.geo3d-canvas canvas` tồn tại và có diện tích · `.geo3d-labels` đủ
**bộ nhãn của chính ca đang chạy** · `.geo3d-readout` hiện đáp số · không tràn
ngang · nút *Bước trước / Bước sau* thấy được và **không bị vật khác che**
(`elementFromPoint`) · bước chuyển qua lại rồi về đúng chỗ cũ · chỉ gọi
`/api/analyze`, `/api/health`, `/api/auth/me` · 0 lỗi console nghiêm trọng.
Ghi `BROWSER_REPLAY_RESULT.json` + ảnh chụp mỗi khung.
⚠️ **Ba chỗ từng đo SAI, đã sửa 2026-09-21** — cả ba đều sai về phía **bi quan**,
tức báo hỏng khi sản phẩm đúng, nên không ai đi kiểm chúng:
`sess.eval` trả **giá trị JS** chứ không trả chuỗi `"true"` (mọi phép chờ hết giờ,
cổng báo "không có canvas" trong khi cảnh đã dựng xong) · nút gửi là **biểu tượng
mũi tên** `[aria-label="Phân tích đề bằng AI"]`, chuỗi "Dựng mô phỏng" thuộc
`PhotoProblemPanel` chứ không thuộc bề mặt này · `.geo3d-readout` **chỉ đầy ở bước
cuối**, nên phải bấm "Bước sau" tới cuối rồi mới đọc đáp số.
⚠️ **Tham số hoá từ 2026-09-21**: `--ca <tệp>` mang `input_text`, `labels`,
`volume` của một ca benchmark ⇒ script không còn khoá cứng vào bộ nhãn `S A B C`
của ca controlled cũ.
⚠️ **KHÔNG đọc điểm ảnh từ WebGL**: `toDataURL` trả khung trống nếu không bật
`preserveDrawingBuffer`, mà bật nó là sửa mã sản phẩm để chụp được ảnh. Script chỉ
ghi **khung bao** canvas; phép đo điểm ảnh làm trên ẢNH CHỤP lúc dựng contact sheet.
Dùng `phucVu` + `kiemDistMoi` của `scene3d-orbit-gate.mjs`. Cờ `--tiem`,
`--bo-qua-build`, `--ra`.

### `frontend/scripts/scene3d-orbit-gate.mjs` (2026-09-11) · offline

Sở hữu **CỔNG QUAY** trên `dist/`: quay đủ 360°, chạm được sáu hướng nhìn, trục
ổn định, không snap, không tự khớp khung giữa cú kéo. Exports: `NGUONG` ·
`TRANG_THAI` (9 trạng thái) · `phucVu` · `thaoCuon` · `trucQuay` · `tenTruc` ·
`vongQuanhTruc` · `tongGocKhung` · `sauHuong` · `demSnap` · `motCa` ·
`phanLoai` · `chay`. Cờ: `--ca` · `--ra` · `--tiem` · `--bo-qua-build` ·
**`--dist`**.

⛔ `chuanTruc` **đã gỡ** (2026-09-12) — thay bằng `trucQuay`. Xem cảnh báo dưới.

⚠️ **`--dist <đường dẫn>` đo một bản dựng KHÁC**, thường là `dist/` của worktree
ở commit cũ. Không có cờ này thì không ai đối chiếu được **cùng một cổng** qua
nhiều mốc, và mỗi lần nghi ngờ cổng lại phải viết một bộ đo riêng — bộ đo riêng
ấy tự nó cũng chưa được chứng. Chính cờ này đã lộ ra lỗi bên dưới.

⚠️ **`chuanTruc` cũ đo NHẦM ĐẠI LƯỢNG, và cái tên khiến không ai nghi.** Nó lấy
`dPv / (dPv + dCuc)` với phương vị/cực định nghĩa quanh trục **Z**, nên nó trả
lời *"có quay quanh Z không"* chứ không phải *"trục có cố định không"*. Đo trên
ba bản dựng, cùng cú kéo ngang thuần 300 px:

| bản dựng | ‖trục‖ ĐÚNG | trục thật | `chuanTruc` cũ |
|---|---|---|---|
| `e6c2330` | **1,000** | `[0, 1, 0]` cố định | 0,525–0,532 |
| `1a553b8` | **1,000** | `[0, 1, 0]` cố định | 0,526–0,531 |
| `56350f7` | 0,600–0,610 | `[0,57; −0,05; 0,82]` trôi | 0,546–0,548 |

Hàm cũ chấm bản **trục trôi thật** CAO HƠN hai bản trục cố định tuyệt đối — nó
nghịch chiều với thứ nó khai là đang đo, và chỉ trông đúng khi sản phẩm tình cờ
quay quanh Z. Hậu quả: `TRUC_TROI` phát oan cho mọi bản quay quanh Y.

`trucQuay` dùng công thức của `SCENE3D_INTERACTION_SMOOTHNESS_REGRESSION_
DIAGNOSIS`: `R = Aᵀ·B` giữa hai khung, rút trục từ phần phản đối xứng, chuẩn
hoá **dấu**, rồi trung bình vectơ đơn vị. `‖trung bình‖ = 1` ⇔ mọi khung quay
quanh cùng một trục. Nó **không giả định trục nào** — quay quanh Y cho 1,000 y
như quay quanh Z, và *"trục là Y"* là một **sự kiện** báo qua `tenTruc`, không
phải một lỗi. `vongQuanhTruc` cũng đổi theo: vòng đo quanh **chính trục đã đo**,
vì `thaoCuon(pv)` đọc 12° cho một cú kéo cả nghìn độ khi trục là Y.

Vì sao tách khỏi `scene3d-interaction-probe.mjs`: probe hỏi *"kéo có mượt
không"* và chỉ cần **biến thiên** tư thế giữa hai khung; cổng này hỏi *"người
học quay hết hình được không"* và cần tư thế **tuyệt đối** (phương vị, góc cực).

⚠ **Cách lấy tư thế camera mà không đụng mã sản phẩm.** Gom ma trận qua
`uniformMatrix4fv`, **nhóm theo VỊ TRÍ UNIFORM**, bỏ vị trí nhận nhiều giá trị
trong một khung (đó là `modelViewMatrix`) và bỏ ma trận chiếu (`m[15] === 0`);
phần còn lại là `viewMatrix`. Rồi `phương vị = atan2(m6, m2)`,
`góc cực = acos(m10)` — không cần biết `target`.

⚠ **Bản đầu đếm tần suất GIÁ TRỊ và đã cho một kết luận SAI:** p6/p7 có nhiều
vành cùng tâm nên `modelViewMatrix` trùng nhau, áp đảo `viewMatrix`, và cổng
báo `TRUC_TROI` trong khi sản phẩm hoàn toàn đúng. Phép tự kiểm bắt được nó là
**cửa sổ đứng yên**: 1,6–1,9° khi không ai chạm chuột, phải về 0,0°. Đừng tin
một số nào của cổng khi `yenTong` khác 0.

### `frontend/scripts/scene3d-interaction-probe.mjs` (2026-09-11) · offline

Sở hữu **phép đo ĐỘ MƯỢT VÀ TRỤC QUAY khi kéo**, chạy trên `dist/`. Export duy
nhất: `chay`. Cờ: `--nhan` (`baseline`/`candidate`) · `--lap` · `--ca`
(`p1,p6,p7`) · `--ra` · `--goc`.

Vì sao tồn tại: camera, `OrbitControls` và vật liệu đều nằm trong closure của
`Scene3DWorkspace` — không có đường nào từ ngoài chạm tới, và sửa mã sản phẩm
để gắn móc là đổi chính thứ đang đo. Bộ đo bám ba biên trang không che được,
tiêm bằng `Page.addScriptToEvaluateOnNewDocument`: `requestAnimationFrame`
(nhịp khung) · `HTMLCanvasElement.getContext` rồi `drawElements`/`drawArrays`/
`createBuffer`/`createProgram` (cấp phát) · `uniformMatrix4fv` (ma trận
model-view). Mỗi ca ba cửa sổ: đứng yên 1 s (CHỨNG) → kéo 300 px/1 s → damping.

⚠ **Chỉ số quyết định là `trucQuayTrungBinh`, không phải frame time.**
`ROTATION_AXIS_INSTABILITY` không làm chậm khung nào cả — nó làm **trục quay
đổi mỗi khung**. Đọc bằng chuẩn của trục trung bình: `1,000` = bàn xoay quanh
một trục cố định; `< 1` = lộn nhào. Đo được `0,608–0,680` trước bản vá vòng đời
`camera.up`, `1,000` sau. Xem `docs/SCENE3D_INTERACTION_SMOOTHNESS_REGRESSION_DIAGNOSIS.md`.

⚠ **Cửa sổ đứng yên ở `1440×900` bị nhiễu, ở `390×844` thì sạch.** Ma trận đại
diện mỗi khung là model-view ĐẦU TIÊN, nên thứ tự vẽ đổi giữa hai khung cho ra
"góc quay" giữa hai VẬT KHÁC NHAU — desktop ghi tới 254° khi không ai chạm
chuột. Chốt kết luận trên kênh `390×844`; số desktop phải khai kèm nhiễu này.

### `frontend/scripts/browser-runner.mjs` (M20 W12) · offline (cần `npm run dev`)
MỘT vòng đời trình duyệt cho NHIỀU kịch bản: mở Chrome một lần, chờ trang một
lần, dọn state giữa các kịch bản bằng `store.reset()` + xoá lưu trữ, đóng một
lần. Cách ly bằng DỌN STATE, không bằng khởi động lại tiến trình. Có bộ đếm
`serverStarts` xuất ra artifact để một bản sửa vô ý quay lại kiểu
một-server-mỗi-kịch-bản không lọt im lặng. Cấp sẵn `loadTarget`/`snapshot`/
`dispatch`/`clickText`/`scenario`.
⚠️ `interceptJson(urlPattern, handler)` (2026-09-09) chặn MỘT đường mạng ở CDP
`Fetch` và trả JSON đóng băng — thứ `loadTarget` không thay được, vì
`loadEnvelope` nạp thẳng vào store nên **bỏ qua** đoạn `analyzeViaServer →
res.json() → rẽ theo status`. Cộng thêm `_subs` (đăng ký sự kiện CDP); không ai
đăng ký thì mọi script cũ giữ nguyên hành vi.

### `frontend/scripts/certify-product-ui-rendering.mjs` (2026-09-09) · offline (cần `npm run dev`) · **0 API call**
Chín envelope THẬT của lượt đo cuối `thesis-final-20260908T160224Z`, dựng trong
Chrome có WebGL, qua **đường người dùng**: gõ đề vào ô nhập → bấm nút gửi →
`/api/analyze` bị chặn trả fixture đóng băng. Kiểm mỗi ca dương: canvas dựng
thật (KHÔNG phải lời nhắn dự phòng) · số bước tua khớp `events` · bước đầu chưa
lộ đáp số · tua tới bước cuối rồi đọc đáp số TRÊN MÀN HÌNH · không rò định danh
kỹ thuật; mỗi ca âm: thẻ từ chối đúng lớp · không còn cảnh của ca trước · không
in mã lỗi. Ghi `UI_ACCEPTANCE_MATRIX.json` + 9 ảnh.
`--faultcheck` chạy **6 phép tiêm** và đòi mỗi phép đỏ ở ĐÚNG khẳng định nó
nhắm tới — đỏ vì lý do khác là guard vẫn chưa được chứng minh.
⚠️ Ghi lại một phép tiêm ĐÃ HỎNG: tiêm định danh vào `description` không đỏ
được, vì đề bài nằm sau nút «Xem đề» nên không lên `innerText`. Guard soi thứ
NGƯỜI HỌC THẤY, nên phép tiêm phải đặt vào chỗ người học thấy.

### `frontend/scripts/certify-viewports-w12.mjs` (M20 W12-C) · offline (cần `npm run dev`)
23 target × 4 bề rộng = 92 dòng, dùng lại `browser-runner.mjs`. Hỏi câu KHÁC với
`audit-composition.mjs`: **ở bề rộng này học sinh có DÙNG ĐƯỢC target không** —
sân khấu hiện · affordance chính thấy được · thử thách đóng sẵn · tràn/cắt/chồng.
⚠️ Đếm affordance phải gồm CUE CON TRỎ trên SVG: cột `ArrayView` là một `rect`
gắn pointer handler và React gắn listener ở gốc nên không lộ ra DOM. Bản đầu chỉ
tìm `input/button/[tabindex]` và đọc ra 0 affordance cho mọi target thuật toán —
một kết luận sai vì thước đo hẹp.
Artifact: `docs/evaluation/m20/w12-viewport-matrix.json`.

### `frontend/scripts/quiz-dominance-w12.mjs` (M20 W12-A) · offline (cần `npm run dev`)
Hỏi: khi mở thử thách, CƠ CHẾ còn là khối lớn nhất trên màn hình không? Đo tỉ lệ
`chiều cao khối thử thách / chiều cao sân khấu` — không đo bề rộng, vì cả hai
nằm cùng cột nên bề rộng luôn bằng nhau và phép so sẽ không bao giờ phân biệt
được gì (lỗi "luật không thể sai" đã gặp ở M19).
⚠️ Bản đầu đo ngay ở cursor 0 và chỉ chạm được 2/23 target — `predict.challenge`
trả null ở phần lớn các bước, nên 21 target còn lại bị đọc nhầm thành "không có
thử thách". Nay tiến từng bước tới khi lối vào hiện ra.
Đo được ở HEAD daf9b28: `network.packet_routing` 111px/180px = **0,62** (FAIL).
Sau bản sửa chủ sở hữu chung: 61px/180px = **0,34**, 0 FAIL.
Artifact: `docs/evaluation/m20/w12-quiz-dominance.json`.

### `frontend/scripts/certify-w12.mjs` (M20 W12) · offline (cần `npm run dev`)
Chứng nhận tương tác trong trình duyệt THẬT theo luật: hành động → SimAction →
`module.apply` → **state tất định đổi** → hệ quả nhìn thấy trong DOM. Một cú bấm
không đủ, một hoạt hình không đủ, trả lời thử thách không đủ.
⚠️ Phân biệt `CERTIFIED` với `PROBE_UNVERIFIED`: state không đổi có thể là target
không nhận action ấy HOẶC probe chưa đúng từ vựng miền. Gộp hai ca thành "hỏng"
là đổ lỗi cho sản phẩm vì phép đo hẹp — Wave 1 đã ghi rằng bộ thăm dò chung chỉ
là CẬN DƯỚI. Artifact: `docs/evaluation/m20/w12-interaction.json`.

### `frontend/src/styles/transition-semantics.test.ts` (M20 W10) · offline
Phân biệt HÌNH HỌC DỮ LIỆU (SVG) với CHUYỂN ĐỘNG BỐ CỤC (HTML). `height` trên
`<rect>` encode giá trị mảng — cho chạy là cách kể "giá trị vừa đổi bao nhiêu";
`height` trên `<div>` đẩy mọi thứ bên dưới. Luật đọc NGỮ CẢNH PHẦN TỬ, không cấm
theo tên thuộc tính (cấm theo tên sẽ chặn nhầm `ArrayView`) và không miễn theo
tên file (miễn theo file thì bản vá HTML sau đó cũng lọt).
⚠️ Guard tìm ra một HẠNG MỤC THỨ BA brief không lường: `.web-page` chạy `padding`
— thuộc tính bố cục HTML nhưng chính nó LÀ state mô phỏng đang dạy. Ngoại lệ khai
theo BỘ CHỌN kèm lý do ≥80 ký tự nói vì sao không đẩy chỗ nhìn.

### `frontend/src/styles/tokens.test.ts` (M9-UX5 → W13-A11Y) · offline
Sở hữu NGỮ NGHĨA TOKEN CSS, không chỉ sự tồn tại của tên. Bốn nhóm: `var()` phải
trỏ token có thật (quét cả `.css` LẪN `.tsx` — token ma trong SVG làm stroke
thành `none`) · bóng đổ phải đến từ token (`DESIGN.md §Elevation`) · nền thanh
bên thuộc VỎ không thuộc phần tử dính · và từ W13-A11Y thêm hai trục:
**giảm chuyển động** + **tương phản chữ**.
⚠️ Giảm chuyển động khoá **bộ chọn phổ quát**, không khoá từng lớp: khoá từng
lớp là khoá lần đã xảy ra, còn `transition` viết thêm sau này (kể cả của miền
hình học không gian chưa viết) tự động nằm ngoài tầm. Đường thoát duy nhất còn
lại — `animation`/`transition` mang `!important` đặt NGOÀI khối reduce — bị cấm
riêng. `.composer-spin` là NGOẠI LỆ CÓ CHỦ ĐÍCH (quay chậm 2.4s, không tắt): nó
là chỉ báo duy nhất cho "AI đang phân tích", không kèm chữ, `aria-label` không
đổi khi chạy — tắt nó là lấy mất THÔNG TIN nhân danh khả năng tiếp cận. Guard
khoá cả ngoại lệ để không ai "dọn cho gọn".
⚠️ Tương phản chỉ chấm token THẬT SỰ đứng sau `color:`, và `color:` phải khớp ở
BIÊN KHAI BÁO — bản nháp dùng `/color:\s*var\(/` nên khớp luôn `border-color:`,
làm `--hairline` (1.25:1) hiện ra như "màu chữ" trong khi nó chưa bao giờ là chữ.
Chấm phẳng cả bảng màu sinh 10 phát hiện giả rồi chôn 4 phát hiện thật.
`NO_TUONG_PHAN` **chỉ được ngắn đi** — thêm token trượt mới ĐỎ, trả nợ mà quên
xoá dòng cũng ĐỎ. Còn lại `--accent-orange`/`--accent-green` (bề mặt MODULE,
lượt đo Chrome W13 chưa chạm tới) và `--primary@--canvas-soft` (luật vẫn đúng
cho chữ primary đặt MỚI lên thẻ xám).
⚠️ TÁCH VAI, không phải đổi màu — `--ink-faint` từng gánh HAI vai: chữ phụ 37
chỗ VÀ đường kẻ/cạnh đồ thị/viền chấm "chưa xét" 5 chỗ. Không sửa được giá trị
vì hai vai đòi hai hướng ngược nhau: chữ cần tối đi, mà tối đi thì chấm "nhàn
rỗi" trông như đang hoạt động — đổi NGHĨA sân khấu để chữa lỗi của CHỮ. Đã tách:
chữ sang `--ink-quiet` (#74706c = màu SÁNG NHẤT còn đạt AA trên CẢ HAI nền,
4.91/4.51 — sáng nhất là có chủ đích, xáo trộn "giấy trắng yên tĩnh" ít nhất),
`--ink-faint` giữ nguyên cho nét vẽ. Sự tách vai đó VÔ HÌNH trong mã nên có test
riêng (`token dành cho ĐƯỜNG KẺ không được dùng làm màu chữ`) — thiếu nó thì bản
vá sau viết lại `color: var(--ink-faint)` và mọi test vẫn xanh.
⚠️ `--ink-quiet` là `#716d69`, KHÔNG phải `#74706c` như bản đầu: bản đầu chỉ
tính với hai nền tôi GIẢ ĐỊNH (`--canvas`, `--canvas-soft`), còn lượt quét 26 bề
mặt tìm ra nền thứ ba có thật — `.pseudo-no` trên dải `#e8f2fd` — nơi `#74706c`
chỉ được 4.34:1. Tập nền phải đến từ PHÉP ĐO, không từ trí nhớ về bảng token.
`--accent-green-deep` (#0f6622) là mắt xích còn thiếu của khuôn `-deep` đã có
sẵn (`--accent-orange-deep`, `--accent-purple-deep`), không phải màu mới.
Chứng nhận trình duyệt: `scripts/certify-a11y-w13.mjs` — 26 bề mặt, 884 phần tử
có chữ, **0 cặp trượt** (lượt đầu: 11).

### `frontend/src/evidence-provenance.test.ts` (M20 W8 closure) · offline
Khoá hợp đồng xuất xứ v2 và chứng minh vòng TỰ THAM CHIẾU đã bị phá.
⚠️ Có một test tồn tại vì lỗi thật: `sourceFingerprint` bản đầu chạy `git
ls-files` với cwd của tiến trình (`frontend/`) nên không khớp file nào, và dấu
vân tay ra sha256("") — GIỐNG HỆT ở mọi trạng thái nguồn, tức `STALE_SOURCE`
không bao giờ kích hoạt được. Các test khác vẫn xanh vì chúng so hàm với chính
nó. Test "dấu vân tay PHÂN BIỆT ĐƯỢC" là chỗ bắt được nó.

### `frontend/scripts/impact.mjs` (M20 W8) · T0 IMPACT GATE · offline
Chọn test theo file vừa đổi và **in ra lý do từng lựa chọn**. Ghép ba nguồn: sở
hữu theo thư mục · sổ `SHARED_OWNERS` (mỗi dòng phải nói vì sao bán kính rộng) ·
leo thang bảo thủ.
⚠️ LUẬT: thay đổi mã sản phẩm KHÔNG BAO GIỜ được chọn 0 test — không tra ra chủ
thì trả `IMPACT_MAPPING_MISSING` và leo lên gate rộng. Guard kiến trúc
(`code-index-sync`, `tokens`, `ui-hygiene`) không import file bị đổi nên đồ thị
import không chọn được chúng; chúng phải khai theo sở hữu — đó là lý do bộ chọn
không dùng `vitest --related` một mình. Cờ `--files a,b` cho tập giả định để
`test-tiers.test.ts` kiểm được chính bộ chọn.

### `frontend/scripts/full-gate.mjs` (M20 W8) · T3 · offline
Chủ sở hữu DUY NHẤT của nhãn `FULL_PRODUCT_GATE_PASS`. Danh sách cổng con nằm
trong mảng `GATES` và bị `test-tiers.test.ts` khoá — bỏ một cổng mà vẫn phát
nhãn là chứng nhận một HEAD chưa được kiểm.

### `frontend/scripts/certify-sweep-w12.mjs` (M20 W12) · LƯỢT CHỨNG NHẬN · cần Chrome
Chủ sở hữu của bất biến **source-freeze**: chụp `HEAD`/`sourceFingerprint`/cây
bẩn ở HAI đầu lượt, chạy toàn bộ cổng con W12 (`GATES` — 1 DERIVED + 7 BROWSER),
rồi đòi nguồn y nguyên và `uniqueFingerprints === 1`. Vi phạm ⇒
`CERTIFICATION_SWEEP_INVALID`, thoát != 0.

Vì sao cần dù mọi cổng con đã có `provenance()`: `provenanceVerdict` phán MỘT
artifact tại MỘT thời điểm, nên bảy artifact đo trên bảy trạng thái nguồn khác
nhau vẫn qua được từng cổng rồi được cộng thành một tuyên bố COMPLETE về một sản
phẩm chưa từng tồn tại. Đo được điều đó phải nhìn cả LƯỢT. Khoá bởi
`src/certification-sweep.test.ts` (tiêm lỗi từng ca + chặn cổng con rụng im lặng).

Primitive nằm ở `evidence.mjs`: `sweepBegin/sweepEnd/sweepVerdict`,
`crossCheckFreshness`, `SWEEP_FAULTS`.

### `frontend/src/core/var-label.ts` (M20 · Product Experience) · offline
`varLabel(name)` / `varPhrase(name, fallback)` — đổi TÊN BIẾN ENGINE sang cụm
tiếng Việt đọc lên được. Bảng chỉ phủ biến do chính engine đặt (`tong`, `dem`,
`max`, `min`, `can_tim`, `gia_tri_chen`, `giua`, `vi_tri_cuc_tri`, `vt`); tên do
ĐẶC TẢ cấp (`seed.varName`, LLM sinh) trả `null` ⇒ bên gọi phải nói bằng khái
niệm, không đoán cách viết có dấu (bỏ dấu là ánh xạ mất thông tin: `tong` có thể
là tổng/tông/tống).

Đóng lỗi thật quét được toàn danh mục: `core/scan.ts` và `core/algorithms.ts`
nội suy thẳng tên biến vào câu thuyết minh, nên `algorithm.scan` đọc ra
**"Khởi tạo nguong = 4."** trên màn học sinh. `ui-hygiene` không bắt được vì nó
soi chuỗi TĨNH trong mã, còn đây là chuỗi nội suy LÚC CHẠY.

### `frontend/src/simulations/svg-affordance.ts` (M20 W12) · offline
`svgAffordance({label,onAct,pressed})` trả PROPS cho một hình SVG bấm được:
`role="button"` + `tabIndex` + `aria-label` + `aria-pressed` + Enter/Space (có
`stopPropagation` vì Space là phím tắt Tự chạy toàn cục) + lớp `.sim-affordance`
(vòng tiêu điểm ở `global.css`).

Vì sao trả props chứ không phải component: chỗ gọi trải vào `<g>`/`<line>`/`<rect>`
có hình học riêng, và bọc thêm một `<g>` sẽ làm lệch phép đo hình học đã chứng
nhận (`audit-composition.mjs`, `certify-visual-weight-w12.mjs`).

Đóng lỗi thật: idiom "`<g>` có `cursor:pointer` + `onClick`" dựng ở 5 chỗ, đúng
ở 2. `logic.and_gate` có 13 phần tử focus được, không cái nào là công tắc A/B.
`network/ui.tsx::LinkHandle` và `logic/dag-module.tsx` là nguồn gốc của khuôn và
KHÔNG bị viết lại (đổi mã đã chứng nhận để cho đối xứng = đánh đổi rủi ro hồi
quy lấy cái đẹp). Khoá bởi `scripts/certify-a11y-w12.mjs`.

### `frontend/scripts/certify-a11y-w13.mjs` (M20 W13) · cần Chrome
Giảm chuyển động + tương phản, đo bằng GIÁ TRỊ TÍNH TOÁN sau khi mọi tầng CSS đã
phân giải. Không lặp phép đo của `styles/tokens.test.ts` — vitest dừng ở "luật CÓ
được viết ra", script này đo "trình duyệt CÓ làm theo". Bật/tắt giả lập qua CDP
`Emulation.setEmulatedMedia` (đúng thứ hệ điều hành gửi), đo trước/sau.
⚠️ Tương phản chấm theo CẶP THẬT, không theo bảng màu: leo cây tổ tiên tìm nền
ĐỤC đầu tiên, vì nền thật là kết quả của DOM (thẻ lồng thẻ, nền trong suốt xuyên
xuống) — guard tĩnh chỉ GIẢ ĐỊNH được `--canvas`/`--canvas-soft`. Ngưỡng theo cỡ
chữ đúng WCAG 1.4.3 (≥24px, hoặc ≥18.66px và đậm → 3:1; còn lại 4.5:1); chấm mọi
thứ bằng 4.5 là tự sinh phát hiện giả trên tiêu đề.
⚠️ QUÉT TOÀN DANH MỤC **VÀ ĐI QUA CÁC BƯỚC** — 26 bề mặt (home · library · mọi
target `offlineCatalog()`) × tới 6 bước, 104 bước, 5431 phần tử có chữ. Phạm vi
này lớn dần theo ba lần bị lừa, mỗi lần đều báo CERTIFIED trước khi bị mở rộng:
ba bề mặt bỏ sót 8 lỗi · một-khung-mỗi-target bỏ sót 5 lỗi nữa, vì
`.frontier-tag.is-done`, `.loop-cond-verdict`, `.hold-label`, `.loop-back.is-active`
và nhãn nút mạng **chỉ tồn tại ở TRẠNG THÁI** chứ không ở khung đầu. Bước tới
bằng `nextStep()` (đúng hàm học sinh bấm) và nhận biết hết bước bằng cách so
TRẠNG THÁI ENGINE trước/sau — không đoán tên trường con trỏ, vì con trỏ nằm
trong state của module chứ không ở store.
Bản đầu đo ba bề mặt rồi báo CERTIFIED trong khi **8 lỗi nữa đang tồn tại** ở
những target nó không đi qua
(`.frontier-tag`, `.loop-cond-verdict`, nhãn SVG program-module, huy hiệu bảng):
đúng anti-pattern #13 — guard đặt ở chỗ phụ thuộc route nào tình cờ được ghé.
Một target không nạp được ⇒ `boQua`, và `boQua` khác rỗng thì verdict là RED,
KHÔNG phải "sạch".
⚠️ CHỮ SVG lấy màu từ `fill` chứ không phải `color`, và nền của nó là hình ANH
EM chứ không phải tổ tiên — nên nền dò bằng `elementsFromPoint` tại tâm chữ.
Hai bẫy đã cắn trong lúc dựng: (1) leo cây DOM cho chữ SVG đẻ ra "trắng trên
trắng 1:1"; (2) `elementsFromPoint` trả về CẢ TỔ TIÊN, mà `g`/`svg` có `fill`
mặc định đen ⇒ 8 "nền đen" giả. Nay bỏ tổ tiên và chỉ nhận
rect/circle/ellipse/polygon/path. Phát hiện giả sinh từ chính công cụ đo là
loại nguy hiểm nhất: nó trông y hệt phát hiện thật.
Mục FAULT tự bơm một khối CSS đặt SAU mọi stylesheet — đúng hình dạng lỗi mà
guard tĩnh không thấy: `global.css` vẫn đúng nguyên vẹn, chỉ tầng phân giải cuối
bị luật khác thắng. Artifact: `docs/evaluation/m20/w13-a11y.json`.

### `frontend/scripts/certify-error-boundary.mjs` (2026-09-03) · cần Chrome + `npm run dev`
LƯỚI CHẶN NGOẠI LỆ — 9 ca, và là **cách duy nhất** đo được hành vi thật:
`renderToString` KHÔNG chạy error boundary (SSR không có pha commit), còn kho thì
không có `@testing-library/react` lẫn jsdom.
Tiêm lỗi bằng cách đặt một getter ném trên `id` của một vật trong cảnh rồi nạp
lại envelope với **một cảnh mới cùng mảng vật** — `useMemo([scene])` của xưởng
chỉ tính lại khi danh tính `scene` đổi, giữ nguyên thì phép tiêm không bao giờ
được đọc và lượt đo xanh mà chưa chứng minh gì. Vá **sống trong tab**, gỡ ngay;
không công tắc nào tồn tại trong bản dựng.
Khoá: không trắng màn · thanh điều hướng sống sót · không lộ vết ngăn xếp · nút
phục hồi dựng lại được thật · mở bài khác sau sự cố thì lưới QUÊN lỗi cũ.
⚠️ Ca `§15 phép tiêm phải chạm tới đường dựng` báo ĐỎ khi không chặn được — lượt
đo từ chối báo xanh khi nó chưa chứng minh gì. Đã đỏ thật hai lần lúc dựng.

### `frontend/scripts/certify-display-authority.mjs` (2026-09-03) · cần Chrome + `npm run dev`
MỘT THẨM QUYỀN ĐẶT TÊN — 8 ca, đo trên bề mặt thật. `display_names.py` phát bốn
trường (`label` · `notation` · `reference` · `role`); frontend chỉ bày ra.
Khoá: bốn vùng (tên · vai trò · *Đang dựng* · *Dựa trên*) không in định danh máy
nào ở chế độ mặc định · vai trò do backend đặt và **không lặp lại tên** · câu
lồng nhau bọc toán hạng nhiều chữ bằng `«…»` nên tách được · ký hiệu thiết diện
là chu trình (`ACS`) chứ không phải chuỗi tên dài · **chế độ chi tiết VẪN xem
được `producer`/`depends`** (giáo viên cần, học sinh không).
⚠️ Thứ tự đo có ý nghĩa: quét định danh máy **trước** khi bật chế độ chi tiết —
bật rồi thì `construct_section` hiện ra hợp lệ, và quét sau sẽ đỏ oan.

### `frontend/scripts/certify-construction-bridge-g4.mjs` (2026-09-03) · cần Chrome + `npm run dev`
PHÉP DỰNG MỚI của G4 tới được màn hình — 7 ca, bài mẫu `mp-vuong-goc-duong`.
Khoá bốn điều cùng lúc: cảnh dựng được · mặt phẳng đi qua **tuyến vẽ CŨ**
(`surface`, không loại vẽ mới) · tên hiển thị là câu tiếng Việt chứ không phải
`plane_perpendicular_to_line` · ô soi mở đúng vật và nói được xuất xứ.
⚠️ Phải TUA TỚI BƯỚC CUỐI rồi mới chọn vật: một vật chỉ có mặt trong cảnh từ
bước dựng nó trở đi (bất biến #31), nên chọn ở bước 1 thì không có gì để soi —
ca đỏ đúng như thế lúc dựng.
Số đo dẫn xuất ra `5√6/3`, tức miền căn thức đi qua phép mới nguyên vẹn.

### `frontend/scripts/certify-curved-product.mjs` (2026-09-03) · cần Chrome + `npm run dev`

**KHỐI CONG trong Chrome thật** — 21 phép đo, 0 mạng, 0 LLM. Nạp sáu bài mẫu
cong (`geometry-samples.json`, sinh bởi `build_geometry_samples.py`) thẳng vào
store, cùng đường `certify-section-coplanar-edge.mjs` đi.

Trả lời câu mà 65 ca pytest của `test_curved_foundation.py` **không** trả lời
được: học sinh có thật sự NHÌN THẤY khối cầu · trụ · nón · đường tròn giao
tuyến không — khung dựng được, đáp số chính xác lên dải kết quả, chọn được vật,
ô soi nói tên tiếng Việt, tua bước chạy, mở bài khác thì dựng sạch.

⚠️ Nó cũng canh **bất biến lưới** trên DỮ LIỆU THẬT, không chỉ trên bảng
`_TRUONG`: đọc payload trong store và khẳng định `curved_solid` có ba điểm neo +
`radius_sq` mà **không** có `vertices`/`faces`; `circle3` có tâm + pháp +
**bình phương** bán kính.

⚠️ Tên vật đọc từ **cảnh** (`tenCua`), không đoán bằng chữ tiếng Việt: bản đầu
tìm chữ "cầu" trong cây và đỏ ngay khi nhãn thành `(S)` — một phép đo hỏi sai
câu sẽ đỏ vì lý do sai.

Artifact: `docs/evaluation/integration/curved-product.json` + bốn ảnh
`curved-{ball,cylinder,cone,circle3}.png`.

### `frontend/scripts/certify-section-coplanar-edge.mjs` (2026-09-02) · cần Chrome + `npm run dev`
THIẾT DIỆN THEO MẶT CHÉO `(SAC)` — 7 ca, bài mẫu `mat-cheo-sac`, **0 mạng**.
Mặt phẳng (SAC) chứa trọn hai cạnh `SA`, `SC`; đây là ca mà
`SECTION_COPLANAR_EDGE_GAP` từng ném `MALFORMED_SOLID`.
pytest chứng minh kernel và chuỗi backend đúng; lượt này trả lời câu còn lại —
**học sinh có thật sự thấy thiết diện ấy không**: canvas dựng được, tua tới bước
cuối vẫn dựng, thiết diện có trong cây thành phần, ô soi mở đúng vật, và không
chỗ nào trên màn hình nói khối hỏng.
⚠️ Bài này ở **THƯ VIỆN**, không ở bộ gợi ý trang chủ (`STARTER_SAMPLE_IDS` cố ý
nhỏ, phủ ba loại hoạt động chứ không phủ mọi bài) — lượt đo đi qua thư viện.
⚠️ Cây thành phần nằm trong một NGĂN đóng mặc định; không bấm mở thì quét ra
mảng rỗng và ca vẫn xanh. Đã cắn một lần lúc dựng.
Lượt đo này bắt được một hồi quy thật của wave G1: nhãn chu trình thiết diện
ghép `label` nên ra *"Điểm AĐiểm CĐiểm S"* — nay ghép `notation`.

### `frontend/scripts/certify-display-metadata.mjs` (2026-09-02) · cần Chrome + `npm run dev`
TÊN HIỂN THỊ trên bề mặt học sinh, 4 ca. Khoá kết quả của bản sửa G1/G2: không
định danh máy nào lọt lên DOM (quét **chữ thật**, không quét danh sách tên đã
biết) · khung in KÝ HIỆU chứ không in câu · dải kết quả mang tên đọc được ·
bước 0 không in sentinel `system` của trace.
⚠️ Không thay được bằng pytest hay vitest: pytest khoá *backend phát ra gì*,
vitest khoá *component in gì với dữ liệu dựng tay*; chỉ lượt này trả lời *chữ
nào THẬT SỰ hiện ra sau khi envelope đi hết chuỗi* — và đúng chỗ ấy đã rò hai
lần (`label` rơi về `id`; `events[].object` chở `"system"`).
⚠️ Tua bằng **thanh trượt**, không bằng nút *Bước sau*: giữ tham chiếu nút rồi
bấm nhiều lần thì React dựng lại và mọi cú bấm sau rơi vào nút đã tháo — lượt đo
dừng ở bước 1 mà vẫn báo xanh. Đã cắn một lần lúc dựng.
**0 mạng, 0 LLM.**

### `frontend/scripts/certify-journey-integration.mjs` (2026-09-02) · cần Chrome + `npm run dev`
Hành trình xuyên tầng, bốn nhóm 13 ca: `A` tua bước · `B` chọn vật qua cây → ô
soi · `C` tách/ráp khối · `D` **đổi bài**. Nạp envelope đã niêm phong trong
`docs/evaluation/geometry/` thẳng vào store bằng `loadEnvelope` ⇒ **0 mạng, 0 LLM**.
⚠️ Nhóm `D` là lý do file tồn tại và **không** thay được bằng vitest: kho không
có `@testing-library/react`, mà lỗi chỉ hiện khi một cây React THẬT sống qua hai
lần nạp cảnh — `SimulationWorkspace` dựng `Scene3DExplorer` ở cùng vị trí cho mọi
bài nên React dùng lại component, và `InteractionState` không tự mất. Lỗi đo được
trước bản vá: bài 12 bước tua tới bước 10 rồi mở bài 6 bước ⇒ hiện **"Bước 10/6"**.
Bạn đôi tĩnh: ba ca `tích hợp · trạng thái không được rớt sang bài mới` trong
`Scene3DExplorer.test.tsx` khoá *mã nguồn* có hiệu ứng reset; script này khoá
*hành vi*. Ghi `docs/evaluation/integration/journey.json`.

### `frontend/scripts/certify-refusal-surface.mjs` (2026-09-02) · cần Chrome + `npm run dev`
Bề mặt TỪ CHỐI, 21 ca × 5 hạng (`out_of_scope` · `unsupported_capability` ·
`grounding_failure` · `invalid_program` · `check_failure`). Mỗi hạng đo bốn thứ
độc lập nhau — nhãn đúng hạng · **0 canvas** · không lộ mã kỹ thuật lên UI · còn
đường đi tiếp — vì bốn thứ này hỏng riêng lẻ được: đã từng có lượt từ chối đúng
mà nhãn nói sai hạng.
⚠️ Phần cuối nạp envelope **HỎNG** (`{}` · thiếu `simulation_id` · `scene3d` sai
kiểu · vắng `scene3d`) và khẳng định không ca nào ném lỗi hay làm trắng màn. Đây
là ca đáng giá nhất của file: kho **không có React error boundary nào**, nên một
lần ném là mất cả trang chứ không phải mất một khối.
Mọi envelope dựng tại chỗ ⇒ **0 mạng, 0 LLM**. Ghi
`docs/evaluation/integration/refusal-surface.json`.

### `frontend/scripts/certify-offline-journey.mjs` (2026-09-02) · cần Chrome + `npm run dev`
Đi **đúng đường người dùng đi**, 11 ca: trang chủ → bấm thẻ bài mẫu → xưởng 3D →
tua/chọn/tách → quay ra → mở bài thứ hai. Khác `certify-journey-integration.mjs`
ở chỗ file kia nạp store trực tiếp để cô lập tầng, còn file này bắt lỗi **chỉ
hỏng khi có điều hướng thật** — ví dụ chip "Menu" bấm được nhưng không mở được
gì, vì `AppSidebar` trả `null` khi chưa đăng nhập còn xưởng thì không biết điều
đó. (Lớp lỗi ấy nay KHÔNG dựng lại được: cột trái và chip «Menu» đã gỡ, điều
hướng luôn hiện — xem `components/TopNav.tsx`.)
Catalog bài mẫu chạy hoàn toàn phía client (`src/data/offline-catalog.ts`) ⇒
**0 API call, 0 backend**, chạy được khi chỉ có `npm run dev`. Ghi
`docs/evaluation/integration/offline-journey.json`.


### `frontend/scripts/certify-a11y-w12.mjs` (M20 W12) · cần Chrome
Khả năng tiếp cận đo bằng PHÍM THẬT qua CDP `Input.dispatchKeyEvent` — sự kiện
tự dựng (`isTrusted:false`) không chứng minh được người dùng bàn phím đi được.
Sáu bề mặt đại diện; mỗi ca đòi đủ chuỗi focus → Enter thật → STATE ĐỔI, cộng
`ACCESSIBLE_NAME` · `VISIBLE_FOCUS` (`outline-style !== none`) ·
`STATE_NOT_COLOR_ONLY` · Escape đóng thử thách + trả tiêu điểm · 768px.
Tiêm lỗi: `A11Y_NAME_REMOVED` · `A11Y_KEYBOARD_PATH_REMOVED` ·
`CHALLENGE_ESCAPE_BROKEN` (thay khối bằng bản sao rời fiber) + CONTROL.

### `frontend/scripts/certify-representation-w12.mjs` (M20 W12) · cần Chrome
Hai câu hỏi một chủ đề: mỗi target bày ĐÚNG MỘT cách xem cho học sinh, và target
còn renderer nội bộ thì hai renderer đọc cùng một sự thật. Sinh bảng 23 dòng
(mode công khai · mode khả dụng · bày cho học sinh · bản nội bộ · vi phạm) +
parity 2D↔3D. Tiêm lỗi `PUBLIC_DUAL_MODE_WITHOUT_POLICY` ·
`RENDERER_PARITY_STATE_DIVERGENCE`.
⚠️ Renderer 3D là chunk NẠP LƯỜI ⇒ nó là object, không phải function.

### `frontend/scripts/certify-teaching-walkthrough-w12.mjs` (M20 W12) · cần Chrome
Câu hỏi nghiệm thu duy nhất: bỏ thử thách đi, giáo viên còn phơi bày được cơ chế
không? 11 kịch bản, từ vựng action lấy NGUYÊN từ `certify-w12.mjs::PLAN`.
⚠️ Phạm vi đo là `.workspace-card`, KHÔNG phải `.sim-stage` — cơ chế của
`web.style_model` là DOM thật, của ba target cơ số/bảng là `<table>`, của
`protocol_encapsulation` là `.encap-layer`. Tiêm lỗi
`TEACHING_WALKTHROUGH_CHALLENGE_ONLY`.
⚠️ KHÔNG dùng để nói bất cứ điều gì về kết quả học tập.

### `frontend/scripts/certify-classroom-continuation-w12.mjs` (M20 W12) · cần Chrome + backend
Rời đi rồi quay lại: đăng nhập → mở bài đã giao → thao tác THẬT → ghi tiến độ →
ĐĂNG XUẤT + xoá sạch `localStorage` → đăng nhập lại → tiến độ trở lại. Xoá lưu
trữ là bắt buộc, nếu không phép đo sẽ xanh nhờ LỊCH SỬ CỤC BỘ — cơ chế khác hẳn.
⚠️ `/api/auth/me` trả 200 kèm `user: null` cho khách, KHÔNG trả 401.
⚠️ Cần container backend MỚI (bản cũ không phục vụ `/api/auth/*`) + seed fixture.
Tiêm lỗi `CLASSROOM_PERSISTENCE_REMOVED` · `CLASSROOM_RESTORE_MISMATCH`.

### `frontend/src/test-tiers.test.ts` (M20 W8) · offline
Kiểm chính bộ chọn theo HAI CHIỀU (thiếu: chủ sở hữu dùng chung thu về một test
hẹp ⇒ đỏ · thừa: renderer lẻ kéo cả kho ⇒ đỏ) và khoá ngữ nghĩa nhãn: chỉ T3
được nói `FULL_PRODUCT_GATE_PASS`.
⚠️ Ba guard trong file này từng **khớp rỗng rồi báo đạt** — soi comment thay vì
mảng cổng, mẫu thiếu `
` nên match rỗng, soi phần "Đã đổi" thay vì phần chọn.
Mỗi guard nay tự kiểm rằng nó tìm thấy thứ cần soi trước khi khẳng định.

### `frontend/scripts/runtime-zero-ai-w7.mjs` (M20 W7 closure) · offline (cần `npm run dev`)
ĐẾM request thật thay vì suy từ cấu trúc mã. Bọc `window.fetch` và `module.init`
của mọi module trong registry, chụp số đếm trước/sau từng hành động. Có PHÉP THỬ
DƯƠNG TÍNH mỗi lượt chạy (gọi fetch một lần có chủ đích) để "delta 0" nghĩa là
"không có gọi", không phải "bộ đếm không gắn được".
Phủ: mở/đóng dòng thời gian · trace theo tham số hiện tại · Đặt lại — mỗi cái
kiểm cả fetch, `init`, và ảnh chụp state.
⚠️ Khẳng định "trace theo tham số mới" phải NỐI với giá trị hiện tại (bước chia
đầu = `decimalValue`, chia cho `targetBase`), không so với hằng số: bản đầu tìm
dấu vết "cơ số 2" nhưng mẫu offline vốn đã là cơ số 16 nên phép tiêm giữ
`state.steps` đi qua sạch 23/23. Artifact: `docs/evaluation/m20/w7-runtime.json`.

### `frontend/src/components/transport-w7.test.tsx` (M20 W7) · offline
Khoá ba nhóm: chế độ đến từ chính sách (gồm phép gán `declaredMode ??` — lỗ do
tiêm lỗi tìm ra) · bề rộng khay tách khỏi cơ chế (đòi SÀN ở **cả hai** biến thể
lưới — lỗ thứ hai do tiêm lỗi tìm ra) · dòng thời gian tuỳ chọn mở được thì đóng
được và không đụng store.

### `frontend/scripts/measure-tool-first-w5.mjs` (M20 W5) · offline (cần `npm run dev`)
Trả lời câu §7: **ở cursor 0, DOM có hiện đúng đáp án mà engine đang giữ không?**
Đọc đáp án THẲNG từ store rồi tìm nó trong DOM — kiểm renderer có nói đúng thứ
engine giữ (ranh giới R0); tính đúng của bản thân đáp án do oracle độc lập bên
vitest lo.
⚠️ Ba lần phải sửa chính phép đo trước khi tin được, ghi trong file: (1) hàm tua
gọi `st.next()` — API không tồn tại — nên trả 'ok' mà không tua, mọi target đọc
ra "không bị khoá"; (2) chỉ đếm `table td` nên không thấy bề mặt dựng bằng lưới
div — đo THẺ chứ không đo THÔNG TIN; (3) phán bằng hiệu số nội dung khi tua, sai
tiêu chí vì §1 nói diễn giải NÊN hiện dần. Artifact:
`docs/evaluation/m20/tool-first-{before,after-*}.json`.

### `evaluation/metamorphic.py` (M20 W2B) · Change impact: offline
7 phép biến hình TẤT ĐỊNH giữ nguyên ngữ nghĩa (đổi tên người/thiết bị, cách nói
tương đương, đổi số, đảo dãy, hai phép khoảng trắng) để đo hệ có đọc CƠ CHẾ hay
chỉ khớp mẫu chữ. Hai ràng buộc dễ phá: `shift_numbers` **giữ nguyên 0 và 1** (ở
đề logic/nhị phân chúng là giá trị bit) và `reverse_sequence` chỉ đụng dãy ≥3 số.
`variants()` loại biến thể trùng bản gốc — giữ lại chỉ làm con số phủ to giả.

### `evaluation/product_scope.py` (M20 W2C) · Change impact: offline
`ProductScope` + `SCOPE_OVERRIDES` tách ba loại case bị trộn số: nội dung Tin học
CÔNG KHAI (tính vào phủ) · fixture ENGINE nội bộ (chứng minh DSL, KHÔNG tính) ·
case NGOÀI PHẠM VI (chứng minh từ chối trung thực, KHÔNG tính). Mỗi override phải
nói VÌ SAO theo NỘI DUNG; test từ chối lý do kiểu "nó vốn nằm trong pool khác".

### `persistence/db.py` · Change impact: offline (drift gate) + targeted (Postgres smoke)
SQLAlchemy (SQLite mặc định / Postgres qua `DATABASE_URL`).
Exports: `SimulationCache`, `SimulationPattern`, `ReuseMetric`, `bump_metric`,
`read_metrics`, `init_db(target_engine=None)`, `sqlite_owns_schema`, `db_dialect`,
`SessionLocal`, `IS_SQLITE`, `_engine_kwargs`.
Notes: `load_dotenv()` chạy **lúc import** → key thật vào `os.environ` (vì vậy
conftest phải gỡ key). **Migration = Alembic** (`backend/alembic/`); trên DB bền
Postgres, Alembic sở hữu DUY NHẤT tạo/tiến hoá schema. **Quyền sở hữu schema theo
dialect (DB-HARDEN-2)**: `init_db()` gọi `create_all()` **chỉ khi** `sqlite_owns_schema(engine)`
(`engine.dialect.name == "sqlite"`) — no-op trên Postgres. `_engine_kwargs()` là
pool dialect-aware (SQLite: `check_same_thread`; Postgres: `pool_pre_ping/recycle/
size/max_overflow`). Đổi model → phải tạo migration, nếu không **cổng chống trôi**
`tests/test_migration_drift.py` sẽ ĐỎ.

### `tests/test_db_ownership.py` · Change impact: offline
Khoá quyền sở hữu schema theo dialect: SQLite dùng `create_all`, Postgres KHÔNG;
`_engine_kwargs()` dialect-aware (SQLite không nhận pool option Postgres).

### `tests/test_migration_drift.py` · Change impact: offline
Cổng chống trôi Alembic (chạy trong suite mặc định): `upgrade head` + `alembic
check` trên **SQLite tạm** (không đụng DB dev). Đổi model mà quên migration → ĐỎ.
Đã chứng minh bằng fault-injection (thêm cột không migration → gate bắt được).

### `tests/test_postgres_integration.py` · Change impact: targeted (opt-in `pytest -m postgres`)
Smoke Postgres THẬT (marker `postgres`, mặc định bị loại qua `pytest.ini` addopts).
Container throwaway **không volume** (không đụng `pgdata`), tự skip nếu thiếu
Docker/psycopg2: migrate→head, `alembic_version`==head, ghi/đọc/sửa qua model thật,
**restart+reconnect** (dùng host port cố định vì Docker đổi random port sau restart),
`alembic check` sạch, cleanup `docker rm -f` có kiểm chứng.

### `ingestion/input.py` · Change impact: targeted live (ảnh cần LLM)
Chuẩn hóa text/document/code/image → text. Exports: `ingest_to_text`, `IngestError`.
Tests: `test_ingest.py`.
Notes (PHOTO_PROBLEM_TO_SCENE_END_TO_END, 2026-09-13): nhánh `image` **không còn**
tự kiểm ảnh hay tự gọi Gemini — nó ủy cho `ingestion/image.py` +
`ingestion/image_extraction.py`, và đóng CHẶT HƠN đường mới: bản trích xuất bị từ
chối HOẶC cần người xem lại ⇒ `IngestError`, vì đường cũ không có ai để xem lại.
`MAX_IMAGE_BYTES` / `VALID_IMAGE_MIMES` / `_check_image` đã gỡ khỏi file này.

### `ingestion/image.py` · Change impact: offline
**Thẩm quyền DUY NHẤT chuẩn hoá ảnh đề bài** trước mọi lượt gọi provider.
Exports: `normalize_image`, `decode_image_base64`, `sniff_image_mime`,
`NormalizedImage`, `ImageRejected` (`.code`), `MAX_IMAGE_BYTES` (10 MB),
`MAX_IMAGE_PIXELS` (kiểm từ HEADER, trước `load()`), `MAX_SEND_SIDE`,
`SUPPORTED_IMAGE_MIMES`.
Luồng: base64 có trần → định dạng suy từ NỘI DUNG (magic bytes) so với MIME khai
→ header → trần điểm ảnh → giải mã → xoay EXIF → xoay của người học (`transpose`,
hoán vị chính xác) → RGB nền trắng → thu nhỏ → SHA-256 trên ĐIỂM ẢNH → mã hoá
JPEG lại từ `Image.frombytes` (không mang `info` nào ⇒ không EXIF/GPS/ICC).
Tests: `test_image_normalization.py`. Dep runtime: `pillow` (`requirements.txt`).
⚠ Băm là băm điểm ảnh, không phải băm tệp: cùng ảnh khác metadata ⇒ cùng khoá.

### `ingestion/image_extraction.py` · Change impact: targeted live (prompt `transcribe.md`)
**TẦNG A** của đường ảnh → mô phỏng: provider chép ảnh thành bản ghi có cấu trúc,
SERVER phán. Exports: `ImageProblemExtraction` (+ `MathExpression`,
`UncertainToken`; `extra="forbid"`, chuỗi NFC + gỡ ký tự nhóm C),
`VISION_RESPONSE_SCHEMA` (VIẾT TAY, không `$ref` — test khoá khớp model; lược đồ ĐẦY
ĐỦ, KHÔNG gửi thẳng cho Gemini), `build_gemini_transport_schema` → `VISION_TRANSPORT_SCHEMA`
(bỏ `TRANSPORT_SCHEMA_DROPPED_KEYWORDS` = `maxItems`/`minItems`/`minimum`/`maximum` ở mọi
độ sâu, dựng cấu trúc mới, xác định; thứ THẬT SỰ đi trong request), `canonical_json_bytes`,
`VISION_RESPONSE_SCHEMA_SHA256`, `VISION_TRANSPORT_SCHEMA_SHA256`, `VISION_SCHEMA_IDENTITY`
(= phiên bản + 16 ký tự băm lược đồ gửi, đi vào khoá cache).
⚠️ `GEMINI_VISION_SCHEMA_COMPATIBILITY_FIX` (2026-09-14): request Gemini thật đầu tiên
nhận HTTP 400 *"too many states for serving"* với lược đồ đầy đủ; giới hạn vẫn do Pydantic
áp khi parse. Phản hồi sai ⇒ `VisionContractError.code = VISION_OUTPUT_VALIDATION_FAILED`
(trước là `VISION_OUTPUT_INVALID`), không bao giờ là từ chối đề bài.
`parse_extraction`, `assess_extraction` → `ExtractionAssessment` (TẤT ĐỊNH),
`REJECTION_MESSAGES`, `FLAG_MESSAGES`, `extraction_cache_key`, `vision_identity`,
`extract_problem_from_image` → `ExtractionResult`, `EXTRACTION_CACHE`, lỗi
`VisionContractError` / `VisionUnavailable` / `VisionBusy`.
⚠️ `VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX` (2026-09-14) — **guard nguồn gốc dữ kiện**:
`apply_diagram_only_provenance_guard` (bản ghi đã qua Pydantic → bản CÔNG KHAI · phán quyết ·
`ProvenanceGuardReport`), `FACT_BEARING_FIELDS` (`problem_text_verbatim`/`_normalized` ·
`math_expressions` · `given_relations`), `PROVENANCE_GUARD_EVENT` = `VISION_DIAGRAM_FACTS_QUARANTINED`,
`PROVENANCE_GUARD_SCOPE`. CHỈ khi phán quyết `MISSING_PROBLEM_TEXT`: mọi trường dữ kiện bị cách ly
khỏi bản công khai (không cắt, không đoán lại, không chép sang quan sát); nhãn điểm/vật,
`has_diagram`, `diagram_observations` giữ nguyên; log INFO một sự kiện chỉ mang tên trường · số mục
· SHA-256 (`to_telemetry`), không nội dung. `ExtractionResult` ĐỔI CHỮ KÝ:
`ExtractionResult(raw_extraction, image, identity, cached)` — `extraction`/`assessment`/
`provenance_guard` dựng trong `__post_init__`, nên không lối dựng nào bỏ qua guard; `raw_extraction`
chỉ cho bộ đo, `to_response` không đọc; cache giữ bản mô hình, guard chạy lại tất định mỗi lượt
trúng. Nguyên nhân: lượt C03 thật ghi ba quan hệ vuông góc đọc từ ký hiệu hình vào `given_relations`
(`DIAGRAM_OBSERVATION_PROVENANCE_LEAK`). Không phán nguồn gốc trong tài liệu vừa chữ vừa hình.
⚠️ `VISION_PROMPT_GUARD_SIMPLIFICATION` (2026-09-15): luật 4/9 thêm vào `transcribe.md` cùng wave ấy ĐÃ GỠ — prompt ấy
ReadTimeout 2/2, prompt `b499dc7a…` HTTP 200 2/2 và phản hồi thật (3 `given_relations`) được guard cách ly đủ. Prompt trở
lại đúng blob `d8ad614`; guard là thẩm quyền an toàn, không phụ thuộc mô hình để trống trường dữ kiện. Test khoá prompt
trùng bản đối chứng (`test_A_…`) và băm ngữ nghĩa của guard đã kiểm trên phản hồi thật (`test_B_…`).
Tests: `test_vision_diagram_only_provenance_guard.py` (fixture đầu ra thật
`tests/fixtures/c03_vision_extraction_replay_redacted.json`; khoá
`frontend/src/components/photo-c03-diagram-only.fixture.json` trùng bản công khai backend dựng).
Ranh giới: KHÔNG sinh chương trình, toạ độ hay SVG. TẦNG B là `/api/analyze` dạng
`text` với văn bản người học đã xem lại — Semantic Program, grounding, kernel,
renderer không đổi. Nguồn gốc dữ kiện (chữ/hình) KHÔNG đi vào Semantic Program.
Cache: LRU trong tiến trình (64 mục); khoá = sha điểm ảnh + model + băm prompt ảnh
+ phiên bản lược đồ + băm prompt TẦNG B + `CACHE_VERSION`; không có tên tệp; lỗi
không được cache; hai yêu cầu cùng khoá đồng thời dùng chung MỘT lượt gọi.
Provider: `max_attempts=2`, `timeout_seconds=60`, trần 2 lượt đồng thời.
Tests: `test_image_extraction.py`, `test_image_extract_api.py`,
`test_photo_problem_semantic_integration.py`, `test_vision_transport_schema.py` (lược đồ gửi
không còn giới hạn · lược đồ đầy đủ và Pydantic giữ nguyên · không sửa tại chỗ · xác định ·
request thật mang lược đồ gửi ở biên HTTP · hậu kiểm 502 không phải từ chối đề bài).

### `evaluation/dataset.py` · Change impact: offline
**Chỉ định nghĩa benchmark** (30 đề, không gọi API). Exports: `EvalItem`, `DATASET`.
`tags`: `smoke` (8 đề), `boundary` (4 đề). Đổi group/expect = đổi ngữ nghĩa
benchmark → cân nhắc kỹ.

### `docs/evaluation/m16/` — artifact M16 (committed, machine-readable)
**Offline (sync-locked, tái sinh được):** `m16-case-matrix.json` ·
`m16-coverage-report.json` · `m16-offline-results.json` · `m16-metrics.json` ·
`m16-failure-ledger.json`. **Live baseline (pre-fix, run-output một lần):**
`trace-baseline.json` (24 case + budget 66 HTTP) · `m16-live-results-baseline.json`
· `m16-live-metrics-baseline.json` · `m16-live-failure-ledger-baseline.json` ·
`m16-live-coverage-baseline.json`. Đọc số liệu M16 → lấy từ đây, KHÔNG chép tay.

### `main.py` · Change impact: offline (trừ khi đổi CACHE_VERSION/pipeline)
FastAPI: `POST /api/analyze`, `POST /api/edit`, `POST /api/explain`,
`GET /api/manifest`, `GET /api/health`. Exports: `app`, `CACHE_VERSION`,
`_cache_key`, `_cache_lookup`. Tests: `test_api.py`, `test_edit.py`.
Notes: **bump `CACHE_VERSION`** khi đổi policy classify/manifest/prompt.
2026-09-13 (PHOTO_PROBLEM_TO_SCENE_END_TO_END): thêm `POST /api/image/extract`
(`ImageExtractBody`: `content` base64, `mime_type`, `filename` — KHÔNG vào khoá
cache —, `rotation` ∈ {0, 90, 180, 270}). Thứ tự: cổng lượt thử → chuẩn hoá ảnh
(400 + `reason_code`, không cần key) → key (503) → `extract_problem_from_image`
(429 bận · 502 sai lược đồ · 503 provider lỗi; thông điệp không mang chi tiết
provider). Cổng lượt dùng thử tách thành `_cong_luot_thu`, dùng CHUNG với
`/api/analyze` — chỉ KIỂM, không TIÊU lượt. Tests: `test_image_extract_api.py`.

### `conftest.py` · Change impact: offline
**Hard guard**: patch transport mạng thật của httpx + gỡ `GEMINI_API_KEY`.
Exports: `BLOCK_MESSAGE`, `live_allowed`. Tests: `test_offline_guard.py`.

---

## Frontend — `frontend/src/`

### `simulations/types.ts` · Change impact: offline
Hợp đồng module. Exports: `SimulationModule`, `SimAction`, `TimelineCapability`,
`WorkspaceProps`, `ConfigResult`, `SimulationEnvelope`, `Domain`, `InteractionMode`,
`VisualMode`, `PredictionCapability`, `EditCapability`.
Notes: capability **optional** (vd `timeline?`) là cách mở rộng chuẩn. M8:
`renderers?: Partial<Record<VisualMode, ComponentType>>` — renderer theo mode,
"2d" mặc định là `Workspace` (tương thích ngược). (`applications?` của M9-UX1
đã GỠ ở M9-UX2 — thẻ "Ứng dụng" tay quá nông; transfer-of-learning thật là
việc tương lai cần duyệt riêng.)

### `simulations/renderer.ts` · Change impact: offline
M8 — chọn renderer từ HỢP ĐỒNG module (không switch-case id). Exports:
`rendererFor`, `availableVisualModes` (= tuyên bố ∩ có renderer thật),
`effectiveVisualMode` (rơi an toàn về "2d"). Tests: `visual-mode.test.tsx`.
*2026-10-05 (`cuboid-acceptance`):* test ấy đã gỡ; module duy nhất chỉ khai "2d" và không khai `threeD`, nên chính
sách W4B-2R dưới đây không còn chủ thể (bất biến #16/#18 **LỊCH SỬ**); cảnh hình học đi `Scene3DExplorer`.

**W4B-2R — CHỦ SỞ HỮU CHÍNH SÁCH BIỂU DIỄN** cũng ở đây (đừng đẻ file thứ hai):
`RepresentationPolicy` = `"2d_only" | "3d_only" | "2d_and_3d_justified"`,
`representationPolicyOf(module)` (phân loại — MÔ TẢ) và
`representationPolicyProblems(module)` (phán quyết hợp lệ — trả mảng lý do, rỗng
= hợp lệ). **DẪN XUẤT, không thêm trường vào 22 module**: chính sách đã nằm
trong `supportedVisualModes` (được cấp mode nào) + `threeD.role` (chiều sâu
nghĩa gì); trường thứ ba là nguồn sự thật thứ hai phải đồng bộ tay
(anti-pattern #1). **Điều kiện của `2d_and_3d_justified` là
`threeD.role === "pedagogical"`, KHÔNG phải sự tồn tại của renderer** — đây
chính là phép kiểm hạ `network.packet_routing` về 2D_ONLY (nó tự khai
`architectural_poc`). Danh mục: **21 / 0 / 1**. Guard toàn danh mục **dẫn xuất
từ registry**, không chép tay 22 tên: `representation-policy-w4b2r.test.ts`.
⚠️ File này chỉ được import `./types` — guard khoá đúng danh sách import để chính
sách không bao giờ đọc được tiêu đề/đề bài.

### `simulations/registry.ts` · `legacy.ts` · Change impact: offline
Đăng ký/tra module theo id; `legacy.ts` nâng `algorithm_id` cũ thành envelope.
Exports: `registerSimulation`, `getSimulation`, `listSimulations`,
`clearRegistryForTest`; `toSimulationId`, `fromLegacyAnalysis`.

### `state/store.ts` · Change impact: offline
Zustand, **mù domain**: `active {moduleId, envelope, config, state}` + timeline
actions + `dispatch` + `resetSim` + `replaceSimulation` (M7.14, sau edit) +
`prediction`/`submitPrediction` (M8-PRE-LIP) + `visualMode`/`setVisualMode` (M8 —
lát TRÌNH BÀY: đổi mode không đụng active/cursor/prediction; loadEnvelope reset
về "2d") + M9-UX1: `view` (home/workspace/history), `history` (mirror), `goHome`,
`openHistory`, `reopenFromHistory` (ZERO-AI), `removeHistoryItem`, `clearHistory`;
`loadEnvelope(env, sampleId?, originalInput?)` ghi lịch sử; bước/visualMode
touch tiến độ. Tests: `registry.test.ts`, `visual-mode.test.tsx`,
`view-history.test.tsx`.
Notes: **không** đặt logic domain vào store. Zustand v5 trả INITIAL state khi
renderToString (SSR) — component cần test SSR phải nhận dữ liệu qua PROPS
(ngoại lệ: Home LÀ initial state nên SSR App test được). M13 (Task 6): gọi
`mod.init` được bọc try/catch **domain-blind** (bắt `Error` trần, không riêng
`GenericExecutionError`) — `init` ném lỗi (vd operand không có nguồn giá trị lọt
qua tới runtime) → `analysisError` tiếng Việt thân thiện, `active` giữ `null`
(fail-closed, không dựng cảnh một phần).

W4B-2Z: `sessions`/`activeSessionId` + `newSession`/`switchSession`/`closeSession`
— chuyển phiên là KHÔI PHỤC THUẦN (`activate()` trả về đúng object state cũ; 0
`fetch`, 0 `init`, 0 `validateConfig`). **Đừng "dọn cho gọn" bằng cách gọi
`loadEnvelope` khi chuyển phiên**: fetch vẫn 0 nên guard mạng không thấy gì,
nhưng state bị dựng lại và what-if của học sinh biến mất. Tests:
`sessions.test.ts` (spy `init`/`validateConfig` trên MỌI module đang mở).

W4B-3A: thêm `exploreOpen`/`setExploreOpen` — cờ TRÌNH BÀY thứ hai, cùng tầng
`challengeOpen`, cũng mù domain. **Hai cờ chứ không một** vì hai chế độ khác
nhau ở chỗ ai phán xét: Thử thách đưa cam kết qua `predict.check` (engine phán
đúng/sai), Khám phá đưa thao tác qua `module.apply` (không phán gì). Cả hai:
reset khi `loadEnvelope`/`resetSim`/`reset` (M18-UI: không còn lưu theo phiên).
Trước wave này cờ là `useState` cục bộ tên `labOpen` trong hai renderer miền.

### `state/history.ts` · Change impact: offline
M9-UX1 — lịch sử học BỀN (localStorage, schema v1, `algosim.history.v1`).
Exports: `createHistoryStore` (inject storage — test được), `historyStore`
(singleton; node/SSR → shim in-memory), `historyIdOf` (hash tất định
simulation_id+config → dedup), `HistoryItem`, `HISTORY_SCHEMA_VERSION`,
`HISTORY_MAX_ITEMS` (30, evict theo lastViewedAt), `__resetHistoryForTest`.
Notes: lưu envelope ĐÃ VALIDATE (mở lại zero-AI — bất biến #17) + lastCursor/
visualMode; CHỈ trường whitelist — không secret/blob/prediction/branch/camera;
entry hỏng/version lạ bỏ qua êm. Tests: `history.test.ts`.

### `components/HomeView.tsx` · `HistoryView.tsx` · `data/offline-catalog.ts` · offline
M9-UX1 — Home (hero + composer + gợi ý chọn lọc + "Tiếp tục học" ≤5) và trang
Lịch sử (đủ item, Mở lại/Xóa/Xóa tất cả). `offline-catalog.ts`: danh mục mẫu
hợp nhất (`offlineCatalog` — ĐẦY ĐỦ kể cả fixture, `publicCatalog` — chỉ
Tin học THPT cho học sinh (M9-UX2, nguyên tắc COVERAGE §2.7), `starterEntries`
(6), `DOMAIN_COLOR/LABEL`) dùng chung Home + InputPanel. `App.tsx` route theo
`store.view`; toggle panel chỉ trong workspace. Exports thêm:
`formatRelativeTime` (HomeView). **M9-UX3**: card gợi ý HÀNG NGANG (tranh trái /
chữ phải → mọi card cao bằng nhau bất kể tiêu đề); "xem tất cả" GOM NHÓM theo
domain (nhóm đã nói domain → card trong nhóm bỏ nhãn, tránh nhiễu); `InputPanel`
dùng `publicCatalog()` (KHÔNG phải `offlineCatalog()`) và không lộ `simulation_id`
ra UI — luật phạm vi M9-UX2 nay áp ở MỌI bề mặt học sinh thấy, không riêng Home.
Tests: `catalog.test.tsx`.

### `components/SamplePreview.tsx` · Change impact: offline
M9-UX2 (mở rộng M9-UX3) — preview SVG TĨNH cho starter card (thuần trình bày:
không engine, không fetch, dữ liệu minh hoạ cố định). Exports: `SamplePreview`,
`PreviewKind`, `previewKindOf(simId, explicit?)` — kind suy từ simulation_id hoặc
metadata `preview` tường minh của mẫu (KHÔNG từ tiêu đề); id lạ → "generic".
**M9-UX3 — LUẬT: một tranh = một cơ chế = một bài.** 13 kind: algorithm-bars
(find_max) · bars-min · sum-threshold · count-threshold · linear-scan ·
search-range (binary_search) · sort-swap (bubble) · insertion-lift · binary-bits ·
network-path · logic-gate · web-structure · generic. Trước M9-UX3, 8 bài thuật
toán chen vào 3 tranh và **2 tranh dạy SAI cơ chế** (linear_search mượn
trái/giữa/phải của binary; insertion mượn mũi tên đổi chỗ của bubble) — khoá lại
bằng test "không hai bài thuật toán nào dùng chung một tranh".
Tests: `catalog.test.tsx`.

### `components/ProblemInput.tsx` · Change impact: offline
M9-UX4 — MỘT dạng duy nhất (pill: ô tự cao dần, kẹp tệp + nút gửi nằm TRONG ô,
Enter gửi / Shift+Enter xuống dòng) và **chỉ sống ở Trang chủ**. M9-UX3 từng có
hai vỏ hero/compact vì `InputPanel` cũng nhúng composer; M9-UX4 gỡ composer khỏi
workspace nên vỏ `compact` hết người dùng → gỡ prop `variant`, không nuôi code
chết. `SAMPLE_PROMPTS` hiện thành chip bấm được dưới ô nhập (điền sẵn đề, học
sinh vẫn phải tự bấm gửi — không lén tiêu lượt gọi AI). Tests: `catalog.test.tsx`.
Notes (PHOTO_PROBLEM_TO_SCENE_END_TO_END, 2026-09-13): thêm **Chụp ảnh**
(`capture="environment"`) và **Tải ảnh** cạnh nút `+`, gom trong `.composer-tools`.
MỌI ảnh — kể cả chọn từ `+` — đi luồng xem lại: `/api/image/extract` →
`PhotoProblemPanel` → "Dựng mô phỏng" gửi VĂN BẢN qua `analyzeViaServer`. Luồng gõ
tay và `.docx` giữ nguyên. Chống bấm lặp bằng ref đồng bộ (`readAbortRef`,
`buildingRef`) cộng reducer; thay/xoay/xoá ảnh ⇒ `AbortController.abort()` (huỷ
phía client; lượt gọi provider phía server vẫn chạy hết). Dựng không thành ⇒ GIỮ
ảnh và nội dung, không `loadUnsupported`. Tests: `photo-problem-panel.test.tsx`.

### `components/PhotoProblemPanel.tsx` · Change impact: offline
Khối ẢNH ĐỀ BÀI, thuần trình bày: xem trước (xoay bằng CSS) · Xoay/Thay/Xoá · Đọc
· bản chép nguyên văn · công thức chuẩn hoá · chỗ đọc chưa chắc · vùng mất · mâu
thuẫn chữ–hình · quan sát từ hình (nhãn "chỉ để tham khảo, không dùng làm dữ
kiện") · ô nội dung có `label` · ô xác nhận · Dựng. Không hiện mã từ chối/cờ —
chỉ `learner_message` / `flag_messages` của máy chủ. Chuỗi đọc từ ảnh luôn đi
dạng chữ (React thoát ký tự). CSS: khối `.photo-*` + `.composer-photo-btn` trong
`global.css`. Tests: `photo-problem-panel.test.tsx`.

### `components/photo-problem-flow.ts` · Change impact: offline
Trạng thái THUẦN của luồng ảnh — tách khỏi component vì vitest chạy môi trường
`node`. Exports: `photoReducer`, `initialPhotoState`, `canRead`, `canBuild`,
`buildBlocker`, `needsConfirmation`, `photoStatusText`, `buildOutcome` (chỉ để
chọn lời: `INSUFFICIENT_GEOMETRIC_CONSTRAINTS` / `UNSUPPORTED_PROBLEM`),
`buildFailureMessage`, `clientFileProblem`, `describeUncertainToken`,
`PHOTO_MAX_BYTES`. Ba luật: `requestId` tăng khi ảnh/góc xoay đổi ⇒ phản hồi cũ
bị BỎ; `read-start`/`build-start` là no-op khi chưa đủ điều kiện; bị từ chối hoặc
cần xác nhận ⇒ phải đánh dấu xác nhận mới dựng. Tests: `photo-problem-flow.test.ts`.

### `llm/input.ts` · Change impact: offline
Phân loại tệp người dùng chọn → `InputPayload` (M4): `kindFromFile`, `acceptAttr`,
`kindLabel`, `extOf`, `fileToPayload`, `readAsBase64` (base64 THUẦN, đã bỏ tiền tố
`data:`). Ảnh đề bài (2026-09-13): `IMAGE_MIME_TYPES`, `IMAGE_ACCEPT`,
`isImageFile`, `imageMimeOf` — MIME trình duyệt báo đi TRƯỚC đuôi tệp, vì ảnh máy
ảnh có thể không có đuôi. Máy chủ vẫn là thẩm quyền: nó soi nội dung. Tests:
`input.test.ts`. (Trả nợ `KNOWN_GAPS` của `code-index-sync.test.ts`.)

### `components/icons.tsx` · Change impact: offline
M9-UX5/UX6 — bộ icon SVG nét đậm bo tròn (stroke 2.4, `currentColor`, khung 24×24).
**LUẬT: icon trong UI phải là component ở file này** — CẤM emoji/ký tự Unicode.
Đã cháy: `◧` (U+25E7) không có glyph trong font Windows → ô vuông rỗng trên header.
Khoá bằng `components/ui-hygiene.test.ts` (**quét MÃ NGUỒN**, không quét HTML render).

### `components/LibraryView.tsx` · Change impact: offline
M9-UX5 — trang **Thư viện** (`store.view === "library"`): danh mục ĐẦY ĐỦ, gom nhóm
theo domain + lọc. Nhà riêng của danh mục → Home không phải gánh nó nữa nên
**không bao giờ phình**. M9-UX7: cũng thay luôn vai trò của `InputPanel` (đã gỡ).

### `scripts/audit-layout.mjs` · Change impact: offline (cần `npm run dev`)
M9-UX7 — **soát bố cục trên Chrome thật** qua CDP: `npm run audit:layout`.
Đo 5 thứ trên cả 4 route: icon lệch tâm · chữ bị cắt · phần tử đè nhau · tràn khỏi
khung cha · khoảng cách ngoài thang 4px. Có **dấu vân tay trang** (đo nhầm route →
thoát mã 2) và đã được **chứng minh bằng tiêm lỗi giả**. Đây là thứ DUY NHẤT bắt
được lớp lỗi CSS im lặng (vd `var(--sp-2xl)` không tồn tại) — vitest không chạy CSS.

### `scripts/diagnose-responsive.mjs` · Change impact: offline (cần `npm run dev`)
**Chủ sở hữu phép đo responsive** — trục chiều rộng **và chiều cao**, before/after.
W4B-1A mở rộng: viewport tham số hoá (`--viewports 1366x768,1536x864`), checkpoint
timeline (`--checkpoints initial,mid,final`), chế độ quét danh mục
(`--fixture catalog|stress|all`), dấu vân tay trang (sai route → **thoát 2**),
và **acceptance chấm máy có mã thoát** (vi phạm → **thoát 1**): `HORIZONTAL_OVERFLOW`
· `CONTENT_HIDDEN_IN_PANEL` · `CONTROL_OCCLUDED` (elementFromPoint) ·
`CONTROL_OFFSCREEN` · `TEXT_CLIPPED`.

**Bất biến bố cục nó khoá** (hai cái, hai trục):
1. **Chiều cao** — trang phải cuộn được khi nội dung cao hơn viewport; nội dung
   **không** được biến mất vào thanh cuộn nội bộ của `.panel-center`. Lớp lỗi mà
   mọi breakpoint theo chiều RỘNG không bao giờ bắt được (`global.css` khối
   `@media (min-width: 1101px) and (max-height: 900px)`).
2. **Chiều rộng** (W4B-1A.1) — `LAYOUT_NOT_USING_VIEWPORT`: `.app-layout` phải
   dùng gần trọn khung cha, hoặc đạt đúng `max-width` đã khai khi màn rộng hơn.
   Bề rộng mong đợi **dẫn xuất từ `css_max_width` đo được**, không hard-code.
   Lớp lỗi này guard đầu tiên không thấy: năm điều kiện cũ đều hỏi "có tràn / có
   bị giấu", không cái nào hỏi "app có DÙNG màn hình không".

**Cô lập phiên (W4B-1A.1)** — mỗi lượt chạy sở hữu Chrome riêng:
`--remote-debugging-port=0` rồi đọc cổng thật từ `DevToolsActivePort` trong
profile của chính nó; PID/cổng/profile ghi vào `session` của artifact. Dấu vân
tay kiểm **danh tính** (`store.active.moduleId` so với target đang yêu cầu), không
chỉ hình dạng DOM → lệch thì `WRONG_SIMULATION_OR_FIXTURE` + thoát 2. Mọi lối ra
(thành công · exit != 0 · throw · unhandled rejection · SIGINT/SIGTERM) đi qua
`shutdown()`. Cờ `--self-test-throw` tiêm lỗi tái lập được để chứng minh đường
dọn dẹp. **Lý do tồn tại**: cổng cố định 9337 + thiếu teardown từng khiến hai
lượt chạy song song bám chéo và sinh artifact gắn nhãn sai fixture.

Lệnh hồi quy (0 API call, cần dev server):
```bash
cd frontend && node scripts/diagnose-responsive.mjs --port 3000 --fixture all \
  --routes workspace --checkpoints initial,mid,final --viewports 1366x768,1536x864 --out <dir>
```
Bằng chứng + injected-fault proof: `docs/evaluation/m17/w4b1a-responsive/`.

### `scripts/fixtures.mjs` · Change impact: offline
**Bộ fixture DÙNG CHUNG** cho runner Chrome/CDP (dữ liệu thuần, 0 side effect).
Tách khỏi `visual-stress-audit.mjs` ở W4B-1A — script đó nay `import`, dữ liệu
không đổi. Lý do tồn tại: `offlineCatalog()` của app chỉ phủ **13/22** target,
nên bản soát bố cục cần nguồn bù. Thêm fixture ở ĐÂY, không chép sang runner
khác. Cùng `offlineCatalog()` phủ đủ **22/22** target.

### `components/SessionCard.tsx` · Change impact: offline
M9-UX4 — MỘT thẻ cho phiên đã học, dùng chung `HomeView` ("Tiếp tục học") +
`HistoryView`. Exports: `SessionCard`, `progressOf(item)`.
**Tiến độ SUY TỪ ENGINE TẤT ĐỊNH**, không persist: `progressOf` gọi
`getSimulation(item.simulationId).init(envelope.config)` → `timeline.stepCount`.
Lý do không lưu `totalSteps` vào `HistoryItem`: schema v1 đã nằm trong máy người
dùng, bump version sẽ **xoá sạch lịch sử đang có**. Module KHÔNG khai `timeline`
(exploratory, vd `logic.and_gate`) → trả `null` → **không có thanh tiến độ** (UI
dẫn xuất từ capability, không bịa "1 bước"). Envelope lạ/hỏng → `null`, không ném.
**KHÔNG BAO GIỜ render `simulationId`** ra UI (rò rỉ cũ của `HistoryView`).
Tests: `catalog.test.tsx`.

### `core/` (`algorithms.ts`, `trace-builder.ts`, `pseudocode.ts`, `types.ts`) · offline
Engine của domain `algorithm` (ngoài `simulations/` vì có trước registry).
**Không** dùng làm hạ tầng chung cho domain khác. M9-S1: narration ở BƯỚC QUYẾT
ĐỊNH là câu hỏi (không lộ đáp án sớm — hệ quả thuộc bước kế tiếp); phần tử đã
duyệt/không thỏa được mark `eliminated`; export thêm `OP_TEXT`.
`TraceBuilder` (M12) = **substrate thực thi tái dụng** cho MỌI engine trace
(cùng union `TraceEvent`); 8 engine specialized là 8 driver mệnh lệnh ~15 dòng
trên cùng substrate, KHÔNG phải 8 module rời.

### `core/program.ts` (M17 W2C) · offline
**Interpreter luồng điều khiển hữu hạn**, engine-owned — MIRROR của
`program_spec.py` + `validation/program.py`. Exports: `PROGRAM_VERSION`,
`PROGRAM_LIMITS`, kiểu `ProgramSpec`/`ProgramStatement`/`ProgramExpression`/
`ProgramVariable`/`CompletionState`, `validateProgramSpec(raw)`,
`programLines(spec) → {lines, lineOf}`, `renderExpression(spec, id)`,
`runProgram(spec) → {trace, completion, outputs}`.
Interpreter sở hữu TOÀN BỘ: môi trường biến, thứ tự chạy, kết quả điều kiện,
nhánh được chọn, số lượt lặp, biên dừng. **MỘT NGUỒN cho mã giả**: `programLines`
vừa sinh dòng hiển thị vừa trả `lineOf` mà interpreter dùng để gắn `Step.line`
⇒ highlight không thể trôi khỏi câu lệnh đang chạy.
Dùng lại `TraceBuilder`/`Step`/`Snapshot.vars` (không có trace builder thứ hai).
Chạm biên → `completion="limit_reached"` + câu "chưa kết thúc", KHÔNG treo.
Tests: `program.test.ts`. Consumer: `domains/algorithm/program-module.tsx`.

### `core/scan.ts` (M12) · offline
**Declarative Bounded Scan** — MỘT interpreter tất định, engine-owned, cho họ
bài single-pass trên mảng. Exports: `ScanSpec` (+ `ScanSeed/ScanCompare/
ScanUpdate/ScanMarking/ScanStop`), `runScan(spec, whatIf?) → Trace`,
`validateScanSpec(raw) → {ok, spec|error}`, `SCAN_VERSION`.
Interpreter sở hữu **toàn bộ** vòng lặp/tiến chỉ số/biên dừng (≤ n, non-Turing)/
sinh event/gọi `TraceBuilder`; spec chỉ chọn **enum ĐÓNG** (seed/compare/update/
marking/stop) + hằng đầu vào — **KHÔNG** while/guard/mutation/đệ quy/code. Chứng
minh (`scan.test.ts`): parity NGỮ NGHĨA (decisions + finalMarks + stepCount) với
`runAlgorithm` cho find_max/count_if/sum_if/linear_search — cùng interpreter,
spec khác, **0 primitive theo-thuật-toán**. `validateScanSpec` allowlist mọi
trường + coherence "quét trên GIÁ TRỊ phần tử". (M12-AI-SCAN) `scanPseudocode(spec)` — mã giả
5 dòng DẪN XUẤT từ spec; `runScan` gắn `Step.line`/narration từ CÙNG layout
(một nguồn, chống highlight trôi). Đã wire: module `algorithm.scan`
(`domains/algorithm/scan-module.tsx` — module thứ 9 của domain, adapter mỏng,
prediction/what-if HOÃN) + route NL backend (catalog `algorithm.scan`).
Specialized giữ nguyên làm oracle — KHÔNG thay thế. Mirror Python:
`simulation/scan_engine.py`.

### `scripts/capture-w4b2b-experiment.mjs` · offline (cần Chrome + Vite)
Runner LUỒNG HỌC SINH qua CDP — khác `diagnose-responsive.mjs` (runner ĐO hình
học, không bấm nút). Chứng minh chuỗi: Quan sát không vùng cam kết → mở cổng
BẰNG BÀN PHÍM → cam kết sai/đúng qua `predict.check` → đóng cổng → timeline vẫn
chạy; cộng `JSON.stringify(active.state)` không đổi qua mọi lần bật/tắt trình
bày, và 0 rò rỉ đáp án trong DOM. Cờ: `--port --targets --out`. ⚠️ Chỉ tin kết
quả trên tiến trình Vite MỚI: server đã qua nhiều lượt HMR cho phán quyết sai
(đo được: store `view:"workspace"` mà React vẫn vẽ Home).

### `scripts/capture-w4b2i-interaction.mjs` · offline (cần Chrome + Vite)
Runner CDP của W4B-2I, hai chuỗi hành vi trong một lượt: (A) `binary_search` —
Quan sát 0 vùng bấm → mở Thí nghiệm → **3 vùng bấm trên chính các cột** (nửa
trái / phần tử giữa / nửa phải) → `svg` đổi `role` `img`→`group` → focus bàn
phím → bấm sai: `JSON.stringify(active.state)` KHÔNG đổi; (B) `packet_routing` —
tuyến gốc → ngắt chặng → **không tới được** → nối lại → **Về mạng ban đầu**.
Cờ: `--port --window --out`. Có **dấu vân tay trang** (`active.moduleId`, sai thì
thoát != 0).
⚠️ Hai cái bẫy đã dính trong chính wave này, đừng lặp lại:
(1) `evaluate` phải **thử lại** khi CDP báo `Promise was collected` — lần import
đầu làm Vite pre-bundle rồi RELOAD trang, huỷ execution context; coi đó là lỗi
sản phẩm là tố cáo nhầm. Có `warmup()` nạp trước đồ thị module nặng.
(2) Dừng bước theo nút "Thí nghiệm" là **SAI** — nút đó hiện ở mọi bước chưa
phải bước cuối, nên runner đứng ở bước 0 (không có điểm quyết định) rồi báo FAIL.
Mốc đúng là `.search-observe` (chỉ dựng khi `searchInteractionOf != null`).

### `frontend/scripts/accept-workspace-w4b3b.mjs` — xem mục ở phần script bên dưới.

### `core/trace-builder.ts` — bổ sung W4B-3C
`clearVar(name)` — GỠ một biến TẠM khi thứ nó mô tả hết tồn tại. Không có nó thì
biến mô tả thao tác ĐANG DỞ sống tới hết trace và bước `done` tự mâu thuẫn:
`insertion_sort` tuyên bố đã sắp xong trong khi snapshot vẫn khai đang giữ một
phần tử, và renderer vẽ trung thành cái nó được kể (quân bài ngoài dãy + ô trống).
Chủ sở hữu là ENGINE — **đừng vá bằng `if (bước cuối) ẩn quân bài`**, đó là dạy
renderer nói dối hộ engine và để nguyên mâu thuẫn trong state gửi cho AI giải
thích. Tests: `core/terminal-truth-w4b3c.test.ts` (cả họ sắp xếp × 2 chiều +
quét toàn danh mục + bất biến "hold luôn có bước chèn phía sau").

### `scripts/measure-composition.mjs` · offline (cần Chrome + Vite)
**ĐO bố cục, không cảm nhận** (W4B-2T §4). Với mỗi target chạy được offline, đo
trong Chrome: hộp bao **sân khấu** vs hộp bao **nội dung có nghĩa** (hợp của mọi
`svg`/`table` bên trong), mức dùng bề ngang/bề dọc, số **dải thông tin** quanh mô
phỏng (chú giải · thuyết minh · dải nhân quả · trạng thái tìm kiếm · kết quả ·
teaser · công cụ · khay giữ), và **TRÙNG NGHĨA ở bước cuối** (so tập từ ≥ 60%,
không so chuỗi — hai câu diễn đạt khác nhau vẫn là trùng). Cờ:
`--out --shots --window --port`.
⚠️ **Tỉ lệ dùng KHÔNG phải điểm chất lượng.** Cây cần khoảng thở, bit gom cụm là
đúng, `decimal_to_binary` 17% là ca DISCONFIRMING hợp lệ. Con số là dữ kiện để
phân loại, đừng biến thành mục tiêu tối ưu.
⚠️ Biết trước: encap 2D dựng bằng `div` nên không có `svg/table` ⇒ hộp bao trả
`null`. Đó là giới hạn của phép đo, không phải lỗi sản phẩm.

### `scripts/capture-w4b2r-representation.mjs` · offline (cần Chrome + Vite)
Runner CDP của W4B-2R — chứng minh CHÍNH SÁCH BIỂU DIỄN + vòng đời Quan sát trên
**7 bài làm chứng chọn theo CƠ CHẾ** (§31: tìm kiếm · sắp xếp · logic · hệ cơ số
· cảnh DSL · mạng đổi chính sách · mạng 3D sư phạm), không chọn theo ảnh ai gửi.
Mỗi bài kiểm ba việc: **READY/PAUSED** sau khi nạp (không tự chạy) · **toggle
2D/3D chỉ xuất hiện khi `representationPolicyOf` = `2d_and_3d_justified`** ·
chạy **trọn** canonical bằng nút Tiến với `prediction` vẫn `null`. Sidecar ghi
policy/renderer owner/timeline/capability đọc THẲNG từ store + `renderer.ts`,
không suy từ DOM. Cờ: `--port --window --out`.
⚠️ Dùng lại `warmup()` + thử lại `Promise was collected` của
`capture-w4b2i-interaction.mjs` (Vite pre-bundle làm reload trang giữa lượt đo).

### `docs/SIMULATION_VS_ILLUSTRATION_CONTRACT.md` · tài liệu hợp đồng
Định nghĩa ba mức AlgoSim công nhận — ILLUSTRATION (**cấm admit**) ·
STEP_VISUALIZATION · INTERACTIVE_SIMULATION — phân biệt bằng **ai sở hữu diễn
biến**, không bằng độ đẹp. Chứa PHÉP THỬ BỎ RENDERER (xoá renderer thì engine
vẫn phải sở hữu `state k → k+1 → result`), bảng sở hữu renderer-vs-engine, chỗ
đứng của LLM, hợp đồng **ngữ cảnh đổi NHÃN / cơ chế đổi HÀNH VI**, và phân mức
hiện tại 11/3/8 của 22 target. Đọc trước khi thêm target mới hoặc khi định cho
renderer "tự tính" thứ gì.

### `scripts/audit-search-position.mjs` · offline (cần Chrome + Vite)
Runner ĐO HỆ ĐẾM VỊ TRÍ của họ tìm kiếm (W4B-2D §4) — chỉ ĐỌC, không bấm cam
kết, không mở Thí nghiệm. Ở một bước cam kết của `linear_search`/`binary_search`
nó thu hoạch MỌI bề mặt nói vị trí (nhãn cột `ArrayView` · `SearchActionZone` ·
chip `VarsView` · dải nhân quả · thuyết minh · mã giả) rồi đối chiếu bằng SỐ LẤY
TỪ ENGINE, không bằng chuỗi. Kết luận `SAME_SCREEN_CONTRADICTION` khi cùng một
vị trí ngữ nghĩa hiện hai hệ đếm. Có DẤU VÂN TAY bắt buộc (`active.moduleId` +
sân khấu đã dựng, sai thì exit 2). Cờ: `--port --out`. Artifact:
`docs/evaluation/m17/w4b2d-search-family/position-numbering/`.

### `frontend/scripts/measure-dag-composition.mjs` · offline (cần `npm run dev`)
W4B-4D — ĐO KHOẢNG TRỐNG CHẾT của sân khấu `logic.boolean_dag` ở bốn bề rộng.
Hai phép đo KHÁC NHAU, đừng lẫn: `fillPct` đo MỰC (rect trong SVG) so với thẻ —
sơ đồ to hay nhỏ; `gutterLeft/gutterRight/skew` đo CỤM nội dung so với thẻ —
hình có bị dồn về một bên không. Khiếu nại "dồn sang trái" là phép đo thứ hai,
nên một bản vá chỉ kéo `fillPct` lên vẫn hỏng đúng chỗ bị kêu.

Chính nó bắt được hai lỗi mà SSR không thấy: SVG rơi về bề rộng mặc định 300px
khi cha là `fit-content`, và khung nét đứt của cổng đầu ra bị viewBox cắt mất
7px. Có dấu vân tay trang (không thấy sân khấu DAG ⇒ thoát != 0).
Artifact: `docs/evaluation/m17/w4b4d-composition/`.

### `frontend/scripts/accept-experience-w4b4c.mjs` · offline (cần `npm run dev`)
W4B-4C — NGHIỆM THU TRẢI NGHIỆM: hỏi CÂU HỎI NGHIỆM THU bằng Chrome thật ở bốn
bề rộng. Với mỗi target đã chuyển sang tương tác, nó nạp bài, phát ĐÚNG action
mà bộ điều khiển trên màn hình phát, rồi khẳng định (a) trường kết quả ĐỔI,
(b) `state` đổi tham chiếu, (c) **không** phải bật Play. Vế (c) là vế chính:
một bài chỉ đổi khi chạy timeline thì vẫn là animation-first.
Artifact: `docs/evaluation/m17/w4b4c-experience/acceptance.json`.

### `frontend/scripts/accept-w4b3a.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3A — NGHIỆM THU TRÌNH DUYỆT ở BỐN bề rộng (1920/1536/1366/768) cho 7 target
đại diện: 0 dải `experiment-trigger`; mọi `.sim-secondary-action` phải nằm TRONG
`.player-controls`; không tràn ngang; mở Thử thách ⇒ ≤1 bề mặt cam kết; parity
2D↔3D của `protocol_encapsulation` (cursor/stepCount/`getExplainContext` phải
KHỚP khi đổi cách xem); phiên A→Khám phá→B→A giữ nguyên object state, 0 `fetch`.
Có dấu vân tay trang + `--self-test` (tiêm lỗi giả, exit 1). Cờ:
`--port --out --self-test`. Artifact: `docs/evaluation/m17/w4b3a-after/`.

### `frontend/scripts/accept-workspace-w4b3b.mjs` · Change impact: offline (cần `npm run dev`)
W4B-3B — NGHIỆM THU BỐ CỤC KHÔNG-GIAN-LÀM-VIỆC ở 4 bề rộng, ở các trạng thái
unit test không với tới: **1 phiên · 2 phiên TRÙNG TIÊU ĐỀ · 6 phiên (quá sức
chứa) · chuyển phiên**. Khẳng định: 0 cột phiên thường trực · sân khấu KHÔNG hẹp
đi và KHÔNG bị đẩy sang phải khi số phiên tăng · 0 tràn ngang · tiêu đề 1 dòng ·
đúng 1 tab đang-xem · nhãn không trùng khi tiêu đề trùng · `Mô phỏng mới` tới
được **kể cả khi chỉ có 1 phiên** · dải điều khiển không xuống dòng trên desktop ·
chuyển phiên giữ đúng object state, 0 `fetch`. Có `--self-test` + `--label`.
Artifact: `docs/evaluation/m17/w4b3b-workspace/{before,acceptance}.json`.

**BA BẪY ĐÃ CẮN KHI VIẾT SCRIPT NÀY** (đọc trước khi viết script CDP mới):
1. **Đếm dòng bằng `top` là SAI.** Trong flex row có `align-items:center`, con
   cao thấp khác nhau thì `top` khác nhau — phép đếm đó báo 5–7 dòng cho một
   hàng phẳng. Đếm bằng CHỒNG LẤN DỌC theo thứ tự DOM.
2. **WARMUP PHẢI DÙNG URL ĐÃ GIẢI**, không dùng đường dẫn trần. Warmup bằng
   `import('/src/state/store.ts')` ĐĂNG KÝ chính URL trần vào
   `performance.getEntriesByType('resource')`, nên `pick()` sau đó chọn nó thay
   vì URL `?t=…` app đang chạy ⇒ lại lái store thứ hai. Bẫy hai-instance cắn
   LẦN THỨ HAI, do chính lớp chống nó gây ra vì thêm sai thứ tự.
3. **`Promise was collected`** = Vite tối ưu deps rồi reload GIỮA lúc await.
   Phải có `warmup()` + retry trên lỗi CDP (cùng khuôn `measure-composition.mjs`).
   Và **chú thích bên trong template literal KHÔNG được chứa dấu backtick**.
4. **Đếm dòng bằng `top` là SAI** (xem 1).

**BẪY ĐÃ CẮN MỘT LẦN — đọc trước khi viết script CDP mới.** Vite gắn
`?t=<timestamp>` vào URL module sau HMR, nên `import('/src/state/store.ts')` từ
console có thể trả về **instance THỨ HAI**: script lái một store, trang vẽ theo
store kia, và mọi khẳng định "không thấy X" đều XANH vì lý do sai. Script này
giải URL từ chính trang (`performance.getEntriesByType('resource')`).
`measure-composition.mjs` KHÔNG có lớp bảo vệ đó — nó thất bại ồn ào (null
`querySelectorAll`), nên gặp lỗi đó thì **restart `npm run dev`**, đừng sửa số.

### `components/header-identity.ts` · offline
**Chủ sở hữu DẢI NHẬN DIỆN đầu thẻ mô phỏng** — hai trong ba dòng đầu tiên học
sinh đọc. Export `DOMAIN_BADGE: Record<Domain, string>` (nhãn miền tiếng Việt,
**toàn phần** — thêm miền mà quên nhãn ⇒ `tsc -b` GÃY, thay cho bảng
`Record<string, string>` cũ có fallback `domain.toUpperCase()` từng để lọt
`web`→"WEB" và `geometry`→"GEOMETRY") và `headerSubtitle(modTitle, envelopeTitle)`
trả `string | null` — `null` khi phụ đề lặp nguyên văn tiêu đề (chuẩn hoá hoa/
thường + khoảng trắng), để **shell** không dựng `<span>` thay vì bắt 24 module tự
nhớ. Trả `null` chứ không phải chuỗi rỗng: span rỗng vẫn ăn khoảng cách lưới.
Khoá bởi `components/header-identity.test.ts` (quét cả 24 target: nhãn đủ mọi
miền đã đăng ký · phụ đề không lặp tiêu đề · không liệt kê biến thể mà control
đã bày bằng tiếng Việt · trần 40 ký tự) và `visual-guards.test.tsx` VIS-002.

### `components/SimulationWorkspace.tsx` · `SimulationControls.tsx` · offline
Host sân khấu; thanh điều khiển **capability-driven** (có `timeline` mới hiện
Next/Prev/Play) — tiền lệ cho EditPolicy. M8: Stage = `rendererFor(mod, mode)`
trong `<Suspense>` (renderer lazy); export `VisualModeToggle` (component thuần
theo props — toggle 2D/3D chỉ khi ≥2 mode khả dụng); `PredictionBar` nằm NGOÀI
renderer nên tự nhiên renderer-independent.

**W4B-3A — `SimulationControls` là CHỦ SỞ HỮU DUY NHẤT của lối vào hành động
phụ** (Khám phá + Thử thách), dựng bằng `SecondaryEntry` (component nội bộ, một
hình thức cho cả hai). Trước wave này ba nơi dựng nút — shell + hai renderer
miền — và hai nơi sau đặt nút ngay dưới sân khấu, tức dải `experimentTrigger`
mà bốn lượt đo bố cục đều bắt được. **Renderer miền không được chứa
`sim-secondary-action`** (khoá ở `secondary-actions-w4b2w.test.ts`).

**W4B-4D — `specDrift(mod, state, baseline)`**: mô hình đã RỜI KHỎI đề bài chưa.
Hàm THUẦN (luật chôn trong JSX là luật chỉ kiểm được bằng trình duyệt), so
`mod.currentConfig(state)` với `active.config` (bản validate BẤT BIẾN). Hai luật
dễ làm sai: so bằng **GIÁ TRỊ** chứ không tham chiếu (mọi `apply` dựng config
mới ⇒ so tham chiếu là nhãn kêu vĩnh viễn), và chỉ so **các khoá module khai**
(`web` không giữ `notes` của đề ⇒ so cả khối thì mọi đề có `notes` đều "đã đổi"
ngay khi vừa mở). Module không khai `currentConfig` ⇒ luôn `false`.
Nhãn `.spec-drift` dựng trong `workspace-header`. Bất biến #25.

`SimulationWorkspace` export hai bộ chọn THUẦN mà `SimulationControls` gọi:
`challengeEntry(mod, state, config)` và `exploreEntry(mod, state, config)` →
`PresentationEntry | null`. `null` = module không có chế độ đó ⇒ không nút;
`available: false` = có năng lực nhưng bước này không dùng được ⇒ nút MỜ, không
biến mất (số bước mời được chỉ 4/13 → 21/40 tuỳ bài, tự gỡ mình thì nút nhấp
nháy). Hằng `DEFAULT_CHALLENGE` là câu mời mặc định cho module chưa khai
`predict.entry`. `challengeSurfaceVisible` GIỮ nguyên trách nhiệm cũ — chặn
`PredictionBar` khi module đã bày cam kết trên sân khấu (`presentedInStage`);
đừng dùng nó để tắt LỐI VÀO (đó chính là lỗi đã sinh ra dải).
Tests: `explore-ownership-w4b3a.test.ts`, `secondary-actions-w4b2w.test.ts`,
`dequiz-observe.test.tsx`, `interaction-family-w1.test.tsx`.
*2026-10-05 (`cuboid-acceptance`):* `challengeEntry`, `challengeSurfaceVisible`, `DEFAULT_CHALLENGE` đã gỡ ở W13;
`exploreEntry` và `specDrift` còn nhưng không module nào khai `explore`/`currentConfig`, và cảnh 3D trả về trước khay
2D — bất biến #24/#25/#26 **LỊCH SỬ**; các test nêu trên đã gỡ. Mã còn sót chờ quyết định H-W20-4.

### `llm/client.ts` · Change impact: offline
Exports: `analyzeViaServer`, `editViaServer`, `explainViaServer`, `fetchHealth`,
`EditResponse`. Notes: trình duyệt không bao giờ giữ API key.
*2026-10-05 (`cuboid-acceptance`):* `editViaServer` không còn nơi gọi (backend `/api/edit` đã gỡ — bất biến #15
**LỊCH SỬ**); `explainViaServer` chỉ do panel trợ giúp AI gọi, và panel ấy không được gắn ở đâu (#12; panel vẫn
nằm trong `KNOWN_GAPS` của `code-index-sync.test.ts`).
2026-09-13 (PHOTO_PROBLEM_TO_SCENE_END_TO_END): `extractImageViaServer(req, signal)`
→ `/api/image/extract`, cùng các kiểu `ImageExtractionRequest`,
`ImageExtractionResponse`, `PhotoExtraction`, `PhotoAssessment`,
`PhotoUncertainToken`, `PhotoMathExpression`, `PhotoRotation` (khớp
`ExtractionResult.to_response` phía backend). `postJson` nhận `signal`; huỷ chủ
động (`AbortError`) được ném NGUYÊN, không bị đổi thành lời nhắc bật máy chủ.
Tests: `extract-image.test.ts`.

### `test-setup.ts` · Change impact: offline
Guard offline vitest: stub `fetch` → ném lỗi. Tests: `llm/offline-guard.test.ts`.

## M18 — TẦNG TÀI KHOẢN VÀ LỚP HỌC

> Tầng này KHÔNG sở hữu sự thật mô phỏng. Engine tất định vẫn là nơi duy nhất
> giữ state/timeline/kết quả và là bên duy nhất phán học sinh đúng hay sai
> (bất biến #27). Lớp học chỉ ĐỌC bằng chứng có cấu trúc.

### `backend/app/accounts/` — DANH TÍNH, VAI TRÒ, QUYỀN

Bốn file, bốn tầng, đi một chiều: `policy` (thuần) ← `service` (DB) ←
`router`/`classroom_router` (HTTP).

- **`passwords.py`** — PBKDF2-HMAC-SHA256 từ thư viện chuẩn, salt riêng mỗi tài
  khoản, so constant-time. KHÔNG thêm passlib/bcrypt: cùng thuật toán, thêm một
  dependency mật mã. Chuỗi lưu tự mô tả (`pbkdf2_sha256$vòng$salt$hash`) nên đổi
  số vòng về sau không làm hỏng hash cũ. Định dạng hỏng ⇒ `False`, không ném lỗi
  (một exception riêng là kênh dò tài khoản).
- **`policy.py`** — HÀM THUẦN, test được không cần FastAPI. `resolve_signup_role`
  (đăng ký thường LUÔN ra học sinh; vai trò giáo viên cần mã mời từ môi trường;
  thiếu cấu hình ⇒ ĐÓNG), `entitlement_for` (khách: 1 lượt thử, không lớp, không
  lịch sử bền), `can_observe_class` / `can_read_class`.
- **`service.py`** — phiên (mở/tra/gắn user/đóng), tài khoản, mã lớp. `attach_user`
  GIỮ hàng phiên đang có thay vì mở phiên mới: `guest_trials_used` nằm trên hàng
  đó, mở mới là đăng nhập-rồi-đăng-xuất lại có lượt. Mã lớp bỏ `0O1IL` vì học
  sinh gõ tay mã đó trên bảng.
- **`router.py`** — `/api/auth/*` + `/api/classes*`. Sai email và sai mật khẩu
  trả CÙNG một câu (không cho dò tài khoản). Mã lớp CHỈ hiện cho giáo viên sở
  hữu. `Caller`/`get_caller` là dependency giải danh tính dùng chung.
- **`classroom_router.py`** — `/api/assignments*` + `/api/classes/{id}/observe`.
  `_validated_envelope` là CỔNG: config phải qua đúng `SimSpec.validate` của
  target (bất biến #28). Tiến độ bị KẸP về miền hợp lệ, đếm chỉ TĂNG.

### `backend/app/persistence/classroom_models.py`
Sáu bảng: `users` · `auth_sessions` (phục vụ cả KHÁCH — chỗ đếm lượt thử) ·
`classrooms` · `class_memberships` (unique ở tầng DB) · `assignments` (giữ
envelope ĐÃ VALIDATE, không giữ đề để sinh lại) · `practice_sessions` (bằng chứng
CÓ CẤU TRÚC, không phải ảnh state của renderer).
Đặt cạnh `db.py` chứ không nhét vào: `db.py` sở hữu ngân hàng bài. Chung `Base`
nên Alembic thấy một metadata; `alembic/env.py` phải import file này VÌ TÁC DỤNG
PHỤ, nếu không autogenerate sẽ sinh migration XOÁ các bảng.

### `state/auth.ts` · `state/classroom.ts`
Hai store TÁCH khỏi `state/store.ts` (vốn cố ý mù domain). `auth` giữ danh tính
+ quyền đọc từ `/api/auth/me`; `classroom` là BẢN CHIẾU của lớp/bài/quan sát.
Vai trò ở client là để VẼ, không phải quyền: sửa nó trong devtools thì thấy được
thanh điều hướng giáo viên và không gọi nổi endpoint nào. Vì thế KHÔNG lưu bền.

### `components/TopNav.tsx`
Điều hướng MỨC ỨNG DỤNG, chỉ có sau đăng nhập — **một hàng ngang trong
`.nav-bar`**, hai export vì thanh trên có hai đầu: `TopNav` (tên sản phẩm + mục
theo vai) ở trái, `TopNavAccount` (tài khoản + đăng xuất) ở cuối `.nav-links`
phải; giữa hai cái là hàng hành động của trang, do `App` sở hữu. `itemsForRole()`
export ra để test được danh sách theo vai mà không cần SSR (zustand trả trạng
thái đầu cho server snapshot). Mục dùng lại `.nav-link` (link chữ + gạch chân
khi đang xem, M9-UX5); `.topnav-link` chỉ thêm biểu tượng.

⛔ **Thay `components/AppSidebar.tsx` (đã xoá).** Cột trái 216px ấy phải tự tắt
(`width: 0`, luật `is-canvas-first`) ở mọi bài hình học — tức mọi bài — và ngăn
kéo gọi nó về chỉ được cấp luật phủ đè dưới 900px, nên trên desktop chip «Menu»
mở ra một cột thường trực bóp sân khấu, không nền mờ, không bấm-ra-ngoài. Hàng
ngang bỏ cả ba trạng thái (mở · thu 56px · ngăn kéo) nên không còn gì để lệch,
và «đường ra của xưởng 3D» thành mặc định thay vì một chip phải nhớ truyền. Gỡ
theo: `sidebarCollapsed`/`sidebarDrawerOpen` + 3 action trong `state/store.ts`,
khối `.app-nav*`/`.nav-drawer-btn` trong `global.css`, prop `onMoMenu` của
`Scene3DExplorer`. Về lại `DESIGN_BRIEF §2` ("thanh điều hướng trên cùng").

### `components/AuthGate.tsx`
Hộp thoại đăng nhập/đăng ký, hai chế độ đổi tại chỗ. Ô "mã giáo viên" hiện ra khi
chọn vai giáo viên — nó KHÔNG phải cơ chế bảo mật (giấu nút không ngăn được ai);
`resolve_signup_role` trên máy chủ mới là bên quyết.

### `components/ClassesView.tsx` · `AssignmentsView.tsx` · `ObserveView.tsx`
Một component cho cả hai vai ở lớp/bài (cùng khái niệm, hai phía). `ObserveView`
hỏi lại `/observe` mỗi 5 giây — repo chưa có websocket/SSE và một bảng đổi vài
giây một lần không đáng dựng hạ tầng truyền tin thời gian thực (`§22`). Nó dọn
interval khi đổi lớp; không dọn thì mỗi lần đổi lại thêm một vòng hỏi.

### `components/PracticeReporter.tsx`
Component KHÔNG VẼ GÌ. Chuyển state engine thành bằng chứng thực hành: `cursor`/
`stepCount` đọc qua hợp đồng `timeline` (engine sở hữu), cờ Khám phá/Thử thách
đọc từ store trình bày. Đọc màn hình thay vì đọc hợp đồng chính là lỗi §38.6.
Gửi khi CHỮ KÝ state đổi, chặn nhịp 1500ms — `§22` cấm phát telemetry mỗi khung
hình. Không có bài đang làm ⇒ không gửi gì (tự luyện không đẻ telemetry).

### `components/AssignDialog.tsx`
"Giao cho lớp" — từ mô phỏng ĐANG MỞ tới bài thực hành. Giao từ trong mô phỏng
chứ không từ một trang riêng: giáo viên phải XEM được thứ mình giao, và một
danh sách tên tách quyết định khỏi thứ nó nói về. Gửi envelope của phiên; máy
chủ vẫn kiểm lại qua `SimSpec.validate` vì client không phải nơi luật sống.

### `frontend/scripts/accept-classroom-m18.mjs` · offline (cần dev + uvicorn)
Nghiệm thu tầng lớp học ở bốn bề rộng × ba vai. Kiểm DANH TÍNH BACKEND trước
tiên: container Docker cũ chiếm cổng 8000 sẽ trả 404 cho mọi endpoint mới và
làm mọi kết quả sau đó vô nghĩa (đã cắn một lần). Khẳng định: khách không có
thanh điều hướng và bị 401 ở lớp/bài · học sinh nhận bài, bị 403 khi tạo lớp và
khi quan sát · giáo viên thấy lớp + mã + bảng quan sát, và envelope hỏng bị
chặn 400. Artifact: `docs/evaluation/m18/classroom-acceptance.json`.

### `frontend/scripts/spot-check-demo.mjs` · offline (cần `npm run dev`)

SMOKE trình duyệt cho **tập demo khoá luận** (4 cảnh: `n1`, `n2` từ
`name-contract-probe` + `t3`, `t4` từ `translation-probe`). Ba phép kiểm mỗi
cảnh: nạp envelope qua `store.loadEnvelope` → xưởng 3D dựng được với canvas
WebGL và KHÔNG rơi vào bản dự phòng · ô đọc bước hiện số bước + lời kể · 0 lỗi
console. Ghi `docs/evaluation/geometry/DEMO_SPOT_CHECK.json`.

Có **dấu vân tay trang** trước mọi phép khẳng định (`ARCHITECTURE_MAP §8` #14),
và đã **tiêm lỗi giả** để chứng minh đỏ được: đổi `.geo3d-xuong` thành một lớp
không tồn tại ⇒ 8/12.

⚠️ Phép kiểm bước từng **nói dối**: bản đầu bấm `.geo3d-thanh-nut button` rồi
tự gọi là "tua bước", nhưng đó là thanh CHIP (Xem đề / Thành phần) — `tien=false`
ở cả bốn ca mà phép kiểm vẫn XANH vì nó chỉ đếm nút. Nay nó đọc `.geo3d-buoc-so`
+ `.geo3d-buoc-loi`, và số bước khớp CHÍNH XÁC bộ replay Python (6/7/10/9) —
một phép đối chiếu chéo thật giữa hai bộ đo độc lập.

Đây là SMOKE cho tập demo, **không** phải bản chứng nhận đầy đủ (`certify-*.mjs`).

### `frontend/scripts/spot-check-translation.mjs` · offline (cần `npm run dev`)

Spot check §21 của `FRESH_TRANSLATION_COMPOSITION_PROBE` — hai cảnh ưu tiên:
tịnh tiến DÂY CHUYỀN (`t3`) và tịnh tiến → đo (`t4`). 8/8, 0 lỗi console. Cây
thành phần hiện cả vectơ trung gian (`vec_AD`) lẫn điểm chiếu, tức xuất xứ của
một điểm tịnh tiến đi tới được mặt học sinh.

### `backend/tests/geometry/test_curved_scalar_axis_scale.py` · offline

Authority parity **POINT_MODE ↔ SCALAR_MODE** cho khối cong. Thêm 2026-09-07
(`CURVED_SCALAR_AXIS_SCALE_REPAIR`).

Hỏi một câu và chỉ một câu: *"cùng bán kính, chiều cao, trục và mặt phẳng cắt
thì hai cách khai có cho cùng verdict, cùng elip, cùng diện tích không"*. 4 ca
parity · 8 ca biên (kể cả **vừa CHẠM đáy** — đẳng thức phải được NHẬN — và
**chiều cao VÔ TỈ**) · bất biến tỉ lệ · 5 phép tiêm.

⚠️ `test_02` neo ca chuẩn vào **oracle độc lập** (`tâm (0,0,10)` · `b² = 16` ·
`a² = 80` · `16π√5`): parity mà cả hai nhánh cùng SAI thì vô nghĩa.

⚠️ `test_06` khoá bất biến DỄ MẤT NHẤT: `h² = 300` (`h` vô tỉ) vẫn cắt được.
Nó là lý do bản vá **không** dùng `_ti_le_doc_truc`.

### `backend/scripts/register_oblique_ellipse_final_rerun.py` · offline

Tiền kiểm GOLD + tiền kiểm BỘ CHẤM + đăng ký cho
`OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN`. Xuất `tien_kiem_gold` ·
`tien_kiem_scorer` · `dang_ky`. Thêm 2026-09-07.

Là **CỔNG**: `main()` thoát khác 0 nếu một trong hai tiền kiểm chưa đạt.

⚠️ **Tiền kiểm BỘ CHẤM là phần đáng đọc.** Nó chạy scorer trên bảy fixture
tổng hợp TRƯỚC provider, và nó tồn tại vì lượt trước đã chấm FAIL cho một
chương trình dựng mặt phẳng đúng từng hệ số — bộ đo tụt lại sau hệ đúng một
wave. Một tiền kiểm bộ chấm rẻ hơn một lượt quota.

### `backend/scripts/score_oblique_ellipse_final_rerun.py` · offline

Chấm §10/§11 của lượt cuối và so với hai raw candidate lịch sử (neo bằng BĂM,
không bằng trí nhớ). Ghi `SCORING.json` cạnh artifact bất biến.

⚠️ Hai chỗ dễ sai, đã trả giá và ghi lại: `EXACT_ANSWER` phải đọc từ **HAI**
nguồn (`Radical` trong final memory · chuỗi hiển thị trong trace) vì mỗi nguồn
chỉ có một nửa; và `cham_analyze` phải nhận `nguon="RAW_ANALYZE"`, thiếu nó nó
trả `NOT_CAPTURED` cho mọi chiều fact — đúng hợp đồng của nó, sai với thực tế.

### `backend/scripts/adjudicate_radius_slot_affordance.py` · offline

Phân xử tất định cho `CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION`, 0 lượt gọi.
Xuất `ma_tran` · `menh_de` · `minimal_delta` · `replay` · `chan_doan`. Ghi
`ADJUDICATION.json` + `minimal_delta.json`. Thêm 2026-09-07.

Mọi ô đo bằng máy: ma trận hợp đồng chạy **qua validator thật** (2⁴ tổ hợp mỗi
họ), bốn mệnh đề tra **trên chuỗi thẻ thật**, hai raw candidate đọc **nguyên
byte** từ artifact bất biến.

⚠️ Hợp đồng để replay dựng lại từ raw `analyze` của **lượt chạy thật**, KHÔNG
dùng `REQUEST_CONTRACT_GOLD`: witness live là `dien_tich_e`, gold là
`dien_tich_E`, và chấm bằng gold trả `requested_operation_uncovered` cho một
chương trình hoàn toàn đúng. Cùng bài học đã ghi ở
`replay_plane_from_equation.py`.

### `backend/scripts/register_oblique_ellipse_after_axis_scale.py` · offline

Tiền kiểm §4 + đăng ký cho `OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR`. Xuất
`tien_kiem` · `dang_ky`. Thêm 2026-09-07.

Nó là **CỔNG**, không phải một bản ghi: `main()` thoát khác 0 khi bất kỳ ô nào
của §4 chưa đạt, nên không ai rút được ca lúc tiền kiểm còn đỏ. Scalar mode đi
đường TRUNG THỰC (`h = measure(distance, O, O′)`) — chiều cao do chương trình
TÍNH nên grounding bỏ qua đúng luật; khai thẳng `h = 20` ghim về một fact TOẠ
ĐỘ thì bị từ chối, và đó là ca đối chứng cạnh nó.

⚠️ Runner đọc **ba** khoá của `ngan_sach` mà một đăng ký viết tay dễ quên —
`logical_application_call_limit`, `token_reservation_per_call`,
`token_ceiling_observed`. Thiếu một cái là runner chết ở khâu dựng manifest
(trước provider, nên không tốn quota — nhưng vẫn là một lượt chạy hỏng).

### `backend/scripts/rescore_oblique_ellipse_after_axis_scale.py` · offline

Chấm LẠI artifact bất biến của lượt live, 0 lượt gọi. Ghi `SCORING.json` cạnh
artifact, kèm `sha256` nguồn để đọc ngược được.

Vì sao cần: bộ chấm của lượt chạy **tụt lại sau hệ đúng một wave** — nó chỉ
biết `construct_plane` qua ba điểm nên chấm FAIL cho một chương trình dựng mặt
phẳng đúng bằng `construct_plane_from_equation`. Artifact lượt chạy **giữ
nguyên từng byte**; đây là khuôn đính chính chuẩn của kho: không sửa số cũ, ghi
số đúng sang file mới và nối bằng băm.

### `backend/scripts/register_oblique_ellipse_e2e_rerun.py` · offline

Đăng ký `OBLIQUE_ELLIPSE_FRESH_E2E_RERUN` **trước** kết quả, và ghi phán quyết
tiền kiểm §4. Xuất `dang_ky` · `preflight`. Thêm 2026-09-07.

Ghi `registration.json` + `PREFLIGHT.json`, **không** ghi `manifest` — lượt ấy
dừng trước provider nên không có lượt chạy nào để ghi. Từ chối ghi đè artifact
đã tồn tại (lệ chung của bộ đo hình học).

`preflight()` dựng HAI hình trụ **bằng nhau về hình** rồi so kết quả phép giao
elip — đó là toàn bộ bằng chứng của blocker
`CURVED_SCALAR_AXIS_SCALE_IN_ELLIPSE_CAP_CHECK`, và nó chạy tất định, 0 lượt
gọi.

### `backend/scripts/gold_oblique_ellipse_fresh.py` · offline

Đề + oracle + gold cho `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION` — trụ
`r=4 · h=20`, mặt phẳng `(α): 2x − z + 10 = 0`, `S = 16√5π`.

Khác hai đề elip/nón trước ở một điểm có chủ đích: cho **toạ độ tường minh** và
cho mặt phẳng bằng **phương trình**. IR không có `plane_from_equation`, nên
đường duy nhất là ba điểm thoả phương trình + `construct_plane`.

⚠️ ~~Đề này **chưa từng đi tới model**: `co_duong_thuc_thi` chặn nó ở tầng
`scope`.~~ **Cổng đã sửa 2026-09-07** (`_MANH_MOI_NGHIA_VU` + 4 nghĩa vụ đại
lượng), đề đã chạy live: đi qua `scope` → `analyze` (PASS toàn bộ) → 3 lượt
sinh, **chưa tới `served`**. Cả ba ứng viên đúng mọi chiều trừ mặt phẳng —
`BLOCKER = PLANE_FROM_EQUATION_REPRESENTATION`. Gold vẫn `served` với `16π√5`:
hệ diễn đạt được **qua đường gold**, nhưng đường ấy đòi gắn `source_fact_id`
vào toạ độ đề không nêu. Xem
`docs/SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION.md`.

### `backend/scripts/score_oblique_ellipse_fresh.py` · offline

⚠️ **Bộ chấm phải theo KỊP hệ, và nó đã từng tụt lại.** Bản trước chỉ
biết `construct_plane` qua ba điểm, nên lượt live đầu tiên mà mô hình
tự chọn `construct_plane_from_equation` bị chấm
`PLANE_CONSTRUCTION_CORRECT = FAIL` cho một chương trình **đúng từng hệ
số** (2026-09-07). Nay nó nhận CẢ HAI lối, so hệ số theo **tỉ lệ chính
xác** (không so chữ), và tách `DIRECT_RADIUS_USED` / `RIM_POINT_USED` /
`AXIS_TWO_POINTS` / `RIM_POINT_GROUNDED` — bốn ô ấy là thứ phân loại
được *lựa chọn* của mô hình khỏi *sự bắt buộc* của hệ. Khoá bởi
`tests/geometry/test_scorer_plane_from_equation.py`.

Bộ chấm của wave elip, cắm vào runner qua `registration.scorer_module`. Xuất
`cham_analyze` và `cham_synthesis` — mười chiều của §8, gồm
`PLANE_POINTS_ON_EQUATION` chấm **bằng số học** trên toạ độ mô hình khai chứ
không bằng chữ.

Module RIÊNG chứ không nới hai bộ chấm mặc định của `run_curved_end_to_end`:
chúng hỏi những chiều của **bài nón**, và nới chúng để nhận thêm bài elip là
dựng một bộ chấm biết hai bài — bộ thứ ba sẽ nới lần nữa.

### `backend/scripts/gold_curved_end_to_end.py` · offline

Đề + oracle + gold cho `CURVED_END_TO_END_FRESH_CONFIRMATION` — nón `R=12`,
`h=18`, thiết diện tròn qua điểm chia `1/3` trục, `r(c) = 4`.

Đề buộc dùng **cả năm** mảnh mà ba wave gần đây dựng lên, mỗi mảnh đúng một
lần: ô `radius` của `construct_curved_solid` · `divide_segment` với `t` quy từ
`m:n` · xuất xứ gốc toạ độ · `plane_perpendicular_to_line` ·
`intersect_plane_curved → circle3 → measure(radius)`. Một mảnh hỏng là cả bài
hỏng, và chỗ hỏng chỉ đúng một chỗ.

### `backend/scripts/run_curved_end_to_end.py` · **live** (tiêu quota)

⚠️ **Gold module và scorer module CHỌN ĐƯỢC theo đăng ký** (2026-09-07):
`registration.gold_module` + `registration.scorer_module`, cùng khuôn
`corpus_module` của runner A/B. Lý do: `PROBLEM_HASH`/`ORACLE_HASH`/`GOLD_HASH`
của module cũ đã nằm trong artifact **bất biến** của lượt trước, nên một wave
sau **không** được sửa module ấy. Thiếu `scorer_module` thì rơi về hai bộ chấm
mặc định trong chính file này (chúng hỏi những chiều của bài NÓN).

Runner xác nhận end-to-end. **Khác mọi runner A/B**: gọi thẳng
`pipeline.run_pipeline` — đúng điểm vào sản phẩm, nên có `analyze` thật và
vòng sửa thật (≤3). KHÔNG qua HTTP (không có cache để kết quả cũ lẻn về).

Ba thứ nó sở hữu: **từ chối chạy** nếu `grammar_card("hinh_hoc")` đã trôi khỏi
`card_C_sha256` trong đăng ký (phép đo khi ấy không còn nói về Card C) · giữ
`raw_theo_tang` **gồm cả raw của `semantic_analyze`** — observer của sản phẩm
chỉ phát *số đếm* fact, nên không giữ ở đây thì tầng analyze **không chấm
được** · cưỡng chế trần bằng `ApiBudget(max_logical_calls=…)` ở biên thật.

⚠️ `cham_analyze` trả **`NOT_CAPTURED`** (không phải `FAIL`) khi nguồn hợp đồng
không mang nội dung fact. Bản đầu trả `FAIL` — chấm trượt một tầng nó không
quan sát được; xem `CURVED_END_TO_END_FRESH_CONFIRMATION §6a`.

### `backend/scripts/score_curved_end_to_end.py` · offline

Chấm lại artifact bất biến, 0 lượt gọi → `SCORING.json`. Phân biệt **ba** giá
trị: `PASS/FAIL` (có dữ liệu) · `NOT_CAPTURED` (bộ đo không giữ) · `NOT_REACHED`
(tầng chưa chạy). Đọc đáp số từ `Fraction(a, b)` trong `final_memory` chứ không
từ chuỗi đã format — bộ đo không so bằng một số đã làm tròn ở đâu đó.

### `backend/scripts/run_ratio_affordance_ab.py` · **live** (tiêu quota)

Runner A/B ghép cặp, **một** synthesis mỗi arm, `ANALYZE = 0` · `REPAIR = 0`
(one-shot là cấu hình của runner: hạ `MAX_SEMANTIC_PROGRAM_ATTEMPTS` **trong
tiến trình**, hằng số sản phẩm không đổi).

Ba thứ đọc từ `registration.json`, **đăng ký thắng** cờ dòng lệnh và thắng mặc
định: `arm_labels` (nhãn arm — `A0`/`C`, `P0`/`P1`… tránh nhầm với PRODUCT
VARIANT) · `corpus_module` (qua `_nap_corpus`, hoặc `--corpus`) · lịch chạy
(`lich_chay` đánh số theo corpus ĐẦY ĐỦ, nên khi chạy tập con nó không còn là
thứ tự thật).

⚠️ **`bat_bien_do_dai` + `bat_bien_chia_doan` phải gắn ĐỦ HAI**, đúng thứ tự
`analyze_contract`. Bản trước chỉ gắn cái sau, nên cổng `segment_length` chưa
từng chạy trong hai wave A/B (`RUNNER_SOURCE_INVARIANT_UNDERBINDING`,
2026-09-07) — chương trình khai toạ độ đầu mút **trái độ dài đề cho** đi thẳng
tới `served`.

⚠️ `NganSach.physical` đếm số lần **`call_gemini` được gọi**, KHÔNG phải số
request HTTP (`call_gemini` retry bên trong). Manifest ghi nó dưới tên
`provider_invocations`; số thật ở khối `bo_dem` (xem `wave_counters.py`).

### `backend/scripts/wave_counters.py` · offline

`BoDemWave` — **ba** bộ đếm của một wave đo, mỗi cái một nghĩa:
`logical_application_calls` · `physical_api_attempts` · `candidate_attempts`
(+ `TU_API` / `TU_ARTIFACT` là hai nguồn ứng viên).

⚠️ **Hai trường đầu là `@property` DẪN XUẤT từ `app.ai.gemini.ApiBudget`**, cố
ý — `ApiBudget` đã tách sẵn `logical_calls` ↔ `http_requests` và là chỗ **duy
nhất** nhìn thấy vòng retry bên trong `call_gemini`. Nhờ dẫn xuất chứ không đếm
song song, một ứng viên **đọc từ artifact** không có đường nào làm tăng
`physical_api_attempts`. Đó là lỗ mà `REPAIR_PROBE_COUNTER_DECOMPOSITION` đính
chính (`PHYSICAL_ATTEMPTS = 2` cho một lượt chỉ phát **một** request).

Chỉ `candidate_attempts` đếm tay: `ApiBudget` ở tầng transport, không biết tới
khái niệm "ứng viên". Khoá: `tests/geometry/test_counter_decomposition.py`.

⚠️ **Tổng `candidate_attempts` LUÔN đi kèm `candidate_attempts_theo_tang`.** Một
wave end-to-end gọi model ở nhiều tầng: `analyze` trả một HỢP ĐỒNG,
`semantic_program` trả một CHƯƠNG TRÌNH. Đọc tổng một mình là đúng lớp hiểu
nhầm mà chính đính chính này đi sửa (`CURVED_END_TO_END_FRESH_CONFIRMATION §8`).

### `backend/scripts/gold_minimal_card_confirmation.py` · offline

Corpus **F1/F2** + hợp đồng cố định + gold cho
`MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION`. **Tái dùng** `_ca`/`_bam`
của `gold_ratio_ab` — không chép builder.

⚠️ **Vì sao module RIÊNG chứ không thêm ca vào `gold_ratio_ab.CORPUS`:** bốn
băm của module ấy (`CORPUS_HASH`, `CONTRACT_HASH`, `ORACLE_HASH`, `GOLD_HASH`)
đã nằm trong artifact **bất biến** của ba wave; thêm một ca là làm mọi băm đó
tính ra khác đi, tức phá danh tính các lượt đo đã đóng.

`f2` là ca **duy nhất** trong cả chuỗi wave có đáp số **hữu tỉ không nguyên**
(`28/3`) — nó ở đó để một phép làm tròn ẩn không đi qua được mà không ai thấy.

### `backend/scripts/score_minimal_card_confirmation.py` · offline

Chấm **ba chiều ĐỘC LẬP** rồi ghi `SCORING.json`, 0 lượt gọi. Provenance đọc từ
**raw candidate** nên độc lập với tầng hỏng phía sau. Tách `RATIO_CORRECT`
(tiêu chí đăng ký: phải là `Fraction`) khỏi `RATIO_ARITHMETIC_CORRECT` (số học
đúng dù viết qua tham chiếu gián tiếp) — ghi cả hai để người đọc sau không
phải đoán. `semantic_program` **thuộc** tập `NOT_REACHED`.

### `backend/scripts/translation_probe_cases.py` · offline

Bốn đề probe tịnh tiến + lời giải chuẩn tắc + guard nhiễm chéo (nguồn gồm cả
V1, V2, hạt giống, k=3 và bộ đề đọc thẳng từ mã).

Mỗi ca ghi `translation_required = False` và `duong_vong` — chính tổ hợp
`divide_segment(R, midpoint(P,S), 2)` thay thế được `translate`. Chỉ thị đòi
≥3/4 ca BẮT BUỘC; không ca nào đạt, và đó là sự thật chứ không phải thiếu sót
của bộ đề. Xem đính chính ở `STATUS_LEDGER`.

### `backend/scripts/run_translation_probe.py` · **live** (tiêu quota)

Runner probe. Ba thứ nó sở hữu: §10 chấm lượt ĐẦU **độc lập** với việc pipeline
có sửa tiếp không (sửa không được che việc mô hình có tự tìm ra `translate`);
§12/§14/§15 đếm riêng `translate`, `arith(point,vector)` tái xuất, vectơ→tịnh
tiến, và điểm tịnh tiến có được dùng TIẾP; §19 quét AST mã sản phẩm tìm nhánh
theo dạng bài (`prism`/`parallelogram`/…) — phải bằng 0.

⚠️ `_dang_tinh_tien` từng VỠ khi `translate.vector` là một biểu thức lồng —
đúng thứ kiến trúc cấm, tức bộ đo chết ngay trên một quan sát có nghĩa. Nay
đếm riêng `vector_operand_nested`.

### `frontend/scripts/spot-check-baseline-v2.mjs` · offline (cần `npm run dev`)

Spot check §19 của **CLEAN_BASELINE_V2** — cùng khuôn bản V1, đọc
`clean-baseline-v2/spot-envelopes.json`. Hai cảnh chọn theo §19: thiết diện/độ
sâu cao (`v2_04`) và căn thức/nhiều năng lực (`v2_06`), **không** phải hai ca
đúng đầu tiên — lấy hai ca đầu là hỏi câu nhẹ nhất trong khi §19 muốn hỏi câu
nặng nhất. Chọn bằng `build_baseline_spot_envelopes.py --chon <case_id>…`.
8/8, 0 lỗi console.

### `backend/scripts/clean_baseline_v2_cases.py` · offline

Sáu đề V2 + lời giải chuẩn tắc + guard nhiễm chéo. Nguồn đối chiếu gồm **cả**
`clean-baseline-v1` và bộ đề V1 đọc thẳng từ mã (nó nằm trong `.py`, không
trong artifact — quét thư mục một mình sẽ bỏ sót). Guard so CHỮ KÝ CẤU HÌNH
(khối + bộ số + mệnh đề hỏi), chứng minh bằng `--tiem-de-cu`.

### `backend/scripts/run_stability_k3.py` · **live** (tiêu quota)

Đo **khả năng lặp lại trên CÙNG MỘT đầu vào**: R1 đọc từ hạt giống, R2/R3 gọi
mới, 12 lượt, 0 analyze, 0 sửa.

Gọi **thẳng** `call_gemini` với payload dựng từ artifact, KHÔNG qua
`stage_semantic_program` — hàm ấy tự dựng prompt (đầu vào phụ thuộc mã hiện
tại) và tự chạy vòng sửa (một lượt hỏng kéo theo lượt hai). Đây là cách duy
nhất giữ *"chính xác cùng một đầu vào"* thành khẳng định kiểm được.

**Cổng tiền-gửi**: băm payload, so với hash của R1, lệch thì dừng ca đó —
KHÔNG "chuẩn hoá thêm" để ép khớp, vì đó là sửa phép đo cho vừa kết quả. Số
hiệu repeat/nonce/timestamp không bao giờ đi vào payload.

`_do_sau` đo độ sâu phụ thuộc trên CHƯƠNG TRÌNH, không trên đề: hai chương
trình cùng đúng có thể khác độ sâu, và khác biệt ấy chính là tổ hợp thay thế.
`_hinh_dang` đếm riêng `arith` đặt trong `construct_point` — khuôn hỏng chi
phối, xem `stability-k3/STABILITY_K3_REPORT.md §2`.

### `backend/scripts/capture_stability_seed.py` · **live** (tiêu quota)

Sở hữu câu hỏi *"artifact có ĐỦ để chạy lại không"* — thứ `probe.json` của V2
không trả lời được và vì thế wave đo độ ổn định phải dừng trước API.

Chụp **payload chuẩn tắc** mà mô hình thật sự nhận —
`{system_prompt, user_text, response_schema, temperature}`, trừ `api_key` (bí
mật) và `image` (luôn `None` trên đường hình học) — kèm hash băm với
`sort_keys=True`, để hai lượt chỉ khác thứ tự khoá không bị báo là khác nhau.

`tu_kiem()` kiểm HAI chiều, 0 provider: **tự chứa** (payload trong artifact
băm ra đúng hash đã ghi) và **dựng lại** (ghép từ đề + hợp đồng + thẻ ra đúng
hash ấy). Chiều một chứng minh artifact đứng vững khi mã đã refactor; chiều
hai chứng minh mã hiện tại thật sự tái tạo được. Một chiều là không đủ.

Trần **một** lượt tổng hợp mỗi ca, cưỡng chế ở biên gọi nên lượt thứ hai tiêu
0 token. `repeat_1` được chấm ĐỘC LẬP với `stage_semantic_program`: chặn lượt
hai khiến hàm ấy trả `None` cả cho chương trình mà lượt đầu đã viết đúng, mà
quan sát của wave là *lượt đầu*.

### `backend/scripts/run_clean_baseline_v2.py` · **live** (tiêu quota)

Runner V2. Khác bản V1 ở ba chỗ có chủ đích: token tách theo TẦNG
(`usage_report()` khoá theo stage, nên analyze / tổng hợp đầu / sửa đếm
riêng); tiền kiểm đòi thẻ hình học **có** `construct_point` — đúng lỗi đã giết
V1; và `_dang_rang_buoc` đọc dạng ràng buộc trên chương trình **THÔ**, vì bản
đã chuẩn hoá không còn nói được mô hình đã chọn gì.

### `frontend/scripts/spot-check-baseline.mjs` · offline (cần `npm run dev`)

Spot check §19 của **CLEAN_BASELINE_V1** — cùng khuôn `spot-check-matrix.mjs`,
khác đúng hai thứ: đọc `clean-baseline-v1/spot-envelopes.json`, và envelope
của nó **không bị bộ đo vá** (cổng vận chuyển đã đóng ở wave trước, nên
`compile_semantic_program_to_envelope` ra JSON sạch).

⚠️ Nó phơi ra một lỗi mà JSON không phơi được. Lượt đầu ĐỎ 6/8 với **0 lỗi
console**: envelope hợp lệ, `loadEnvelope` trả `ok`, mà xưởng 3D không hiện.
Nguyên nhân ở bộ dựng envelope phía backend —
`compile_semantic_program_to_envelope` một mình cho ra bản **2D**
(`domain: "generic"`, không `scene3d`); người đổ cảnh 3D là
`pipeline._dung_scene3d`. Một bài hình học đi thiếu bước ấy vẫn "chạy", chỉ là
học sinh mở ra thấy bảng khung 2D. Xem `backend/scripts/build_baseline_spot_envelopes.py`.

### `frontend/scripts/spot-check-matrix.mjs` · offline (cần `npm run dev`)

Spot check §19 của GENERALIZATION MATRIX: ba cảnh **do AI sinh** dựng trong
Chrome thật — WebGL, chọn vật trong cây hình, tua bước, 0 lỗi console. Matrix
đã chứng minh chương trình chạy và `build_scene3d` ra JSON hợp lệ; đây là câu
JSON không trả lời được — *nó có dựng lên màn hình không*.

Nạp qua `useAppStore.loadEnvelope` — ĐÚNG cửa mà Thư viện và bài giáo viên giao
đều đi qua (`validateConfig` → `init`). Cửa sau là chèn thẳng `active` vào
store, và script này KHÔNG làm thế.

⚠️ Envelope đọc từ `spot-envelopes.json` đã được **bộ đo** làm sạch
(`Vec3`/`Fraction`/`Radical` → chuỗi). Đó là vá của bộ đo, KHÔNG phải bản sửa:
bug thật nằm ở `visual_adapter` đặt thẳng giá trị bộ nhớ vào `value_box.value`,
khiến envelope hình học có binding không `json.dumps` được — xem
`backend/scripts/build_matrix_spot_envelopes.py` (hàm `_sach`).

### `backend/scripts/run_generalization_matrix.py` · ⚠️ TIÊU QUOTA (trần 20 lượt)

Chạy 10 đề chưa từng thấy trên RUNTIME ĐÓNG BĂNG, không sửa gì giữa các đề. Đề
+ oracle ở `generalization_matrix_cases.py` (oracle **không bao giờ** gửi cho
mô hình). Chấm bằng oracle TÍNH TAY chứ không bằng `GEOMETRY_CHECKERS`: cổng
chấm tính lại từ CÙNG một kernel đã tính ra đáp số, nên dùng nó là hỏi engine
tự chấm mình. Vì mô hình tự chọn hệ trục, mỗi đề ghim thang bằng số cụ thể.

Bạn đôi: `reanalyze_matrix_offline.py` chạy lại chương trình ĐÃ SINH với 0
token để tách **lỗi của bộ đo** khỏi lỗi của hệ, ghi vào cột riêng
(`offline_class`) — không đè kết quả live. `build_matrix_spot_envelopes.py`
ghép envelope đúng như sản phẩm ghép (adapter + `pipeline._dung_scene3d`, hai
bước tách rời vì `route` không được import `scene3d`).

### `frontend/scripts/accept-product-scope.mjs` · offline (cần dev + uvicorn)

Nghiệm thu **dọn phạm vi sản phẩm**: đi hết các đường điều hướng chính bằng hai
tiến trình Chrome (giáo viên + học sinh), quét **TEXT ĐÃ RENDER** từng trang tìm
nhãn miền và cụm chữ quảng bá đề Tin học. Vì sao không phải test đơn vị: một
`publicCatalog()` sạch KHÔNG đảm bảo màn hình sạch — nhãn còn nằm trong hằng số,
chuỗi còn nằm trong component khác. Bốn lát: bề mặt công khai · lối vào hình học
(bấm gợi ý ⇒ xưởng 3D) · bài giáo viên giao (hồi quy §13, cả hai vai mở được) ·
ba bề rộng. Artifact: `docs/evaluation/geometry/product-scope-acceptance.json`,
có `provenance`.

⚠️ **So khớp KHÔNG phân biệt hoa–thường, và đó là điểm sống còn của guard này.**
`innerText` trả văn bản ĐÃ RENDER, mà `.starter-group-title` mang
`text-transform: uppercase` — nên "Thuật toán" hiện lên màn hình dưới dạng
"THUẬT TOÁN". Bản đầu so khớp nguyên văn và mọi khẳng định "0 nhãn miền Tin học"
đều XANH VÔ NGHĨA. Lộ ra nhờ khẳng định NGƯỢC ("Thư viện phải có nhóm Hình học")
đỏ — bài học: guard vắng-mặt phải đi kèm một guard có-mặt, nếu không nó xanh cả
khi mù. Đã tiêm lỗi (`PRODUCT_DOMAINS += "algorithm"`) để thấy nó đỏ thật.

### `frontend/src/components/HomeWorkStrip.tsx` · offline

Dải MỘT HÀNG trên Trang chủ trả lời ba câu lúc vừa mở app: *học lớp nào · bài
nào đang chờ · vào đâu làm tiếp*. Không phải dashboard — Trang chủ là chỗ BẮT
ĐẦU một việc, và một bảng thống kê nhiều thẻ sẽ đẩy ô nhập đề khỏi màn hình thứ
nhất (đúng thứ M9-UX5 đã gỡ một lần: 5 mục lịch sử ⇒ 5 thẻ).

Luật nằm ở hàm thuần `oViec(laGiaoVien, soLop, baiDangMo)` chứ không trong
component: component đọc ba store, mà zustand ở SSR luôn trả trạng thái đầu
(`§8` #13) nên test dựng component sẽ xanh vì màn hình rỗng. Hai vai đếm hai
thứ khác nhau — học sinh đếm **bài chưa xong**, giáo viên đếm **bài đã giao**
(tiến độ học sinh không được đổi con số của giáo viên). `[]` = không dựng gì:
ô "Bạn chưa có lớp" thường trực chỉ chiếm đất, thẻ bịa thì dạy người dùng rằng
số trên màn hình không đáng tin. 0 gọi LLM. Tests: `home-work-strip.test.tsx`.

### `frontend/scripts/accept-live-classroom.mjs` · offline (cần dev + uvicorn)
Nghiệm thu **phiên dạy trực tiếp**: BA tiến trình Chrome, ba `--user-data-dir`
riêng ⇒ ba kho cookie thật. Đổi vai bằng cách sửa state client thì bài kiểm tự
kiểm giả định của chính nó, nên không làm. Tám lát: bám theo · tự do (hai học
sinh giữ tiêu điểm riêng) · gọi cả lớp về (`syncCmdId` tăng mà `mode` vẫn `free`)
· giơ tay (bảng theo dõi thấy đúng bước + tiêu điểm, học sinh kia KHÔNG bị lây)
· **giao diện + xưởng 3D** · uỷ quyền (bốn ca 403) · kết thúc tiết · **ba bề rộng
phòng máy** (1920/1536/1366: không tràn ngang, điều khiển của vai không bị cắt).
Artifact: `docs/evaluation/geometry/live-classroom-acceptance.json`, có
`provenance` nên sửa mã sản phẩm là nó thành `STALE_SOURCE`.

⚠️ **Dấu vân tay backend soi ROUTE, không soi `/api/auth/me`.** Container Docker
cũ trên cổng 8000 cũng trả 200 cho `/auth/me`, nên bản đầu chạy tiếp rồi đỏ ở
tận Scenario 1 với một thông điệp không liên quan. Nay hỏi thẳng
`/api/classes/999999/session`: FastAPI trả `{"detail":"Not Found"}` khi KHÔNG có
route, còn handler thật trả tiếng Việt của nó — **cùng mã 404, chỉ phần thân
phân biệt được**. Và hỏi qua `:3000` (đường trình duyệt đi), vì `localhost` phân
giải `::1` trước `127.0.0.1` trên Windows: curl vào `127.0.0.1` có thể nói
chuyện với một tiến trình khác hẳn cái mà trang web nói chuyện.

Scenario 5 tồn tại vì bốn lát đầu đi thẳng API và **không hỏi cái gì dựng lên
màn hình** — nó bắt được hai bug chặn cả tính năng mà mọi test API vẫn xanh:
`classroomId` bị bỏ rơi lúc mở bài (⇒ dải lớp không bao giờ dựng) và giáo viên
không có nút mở bài (⇒ không vào được xưởng, nơi dock điều khiển lớp sống).

### `backend/scripts/seed_classroom_fixture.py`
Dữ liệu demo cho nghiệm thu: 1 giáo viên · 2 học sinh · 1 lớp · 1 bài. Mật khẩu
đọc từ `ALGOSIM_FIXTURE_PASSWORD`, không có mặc định trong mã (`§34`) — chạy
nhầm trên máy thật cũng không đẻ ra tài khoản ai cũng biết mật khẩu. Idempotent.

### `frontend/scripts/measure-stage-composition.mjs` · offline (cần `npm run dev`)
Đo bố cục sân khấu cho **mọi** target (khác `measure-dag-composition.mjs` chỉ đo
được `logic.boolean_dag`). Ba số mỗi target: `fillPct` (bề rộng MỰC / bề rộng
trong thẻ) · `skew` (lệch lề trái–phải của mực) · `railSpan` (mép trái của chữ
cách mép trái của mực bao xa — lớn = hai hệ căn lề trong cùng một thẻ).

⚠️ HAI LẦN ĐO SAI TRƯỚC KHI RA SỐ ĐÚNG, ghi lại vì cả hai đều "xanh mà vô nghĩa":
1. bản đầu lấy hộp bao của `querySelectorAll('*')` — div BỌC rộng bằng thẻ nên
   **mọi** target ra "lấp 99.9%, lệch 0", tức báo SẠCH cho đúng bố cục đang bị
   kêu. Nay chỉ đếm `<svg>` và phần tử LÁ thật sự có sơn.
2. bản thứ hai đếm cả bảng `details` gập được nên `boolean_dag` báo lệch 558px
   trong khi sơ đồ của nó đã căn giữa 0px — phép đo tự bịa ra một lỗi không có.

Và một lần nữa dính bẫy **backtick trong template literal** (đã cắn hai lần ở
`capture-*.mjs`): chú thích tiếng Việt trong khối `MEASURE` có \`...\` làm Node
báo `SyntaxError`. Trong khối đó không được có backtick nào.

Artifact: `docs/evaluation/m18/stage-composition.json`.

### `frontend/scripts/audit-composition.mjs` · offline (cần `npm run dev`)
M19 — SOÁT BỐ CỤC DÙNG CHUNG toàn danh mục. Thay `measure-stage-composition.mjs`
(bản đó chỉ đo mực/thẻ, không đo KHUNG và không đo bốn rail).

Mỗi dòng: sân khấu · khung cơ chế · mực có nghĩa · `frameFill` · bốn rail +
`maxRailDelta` · tràn ngang · cắt hình · PHÁN QUYẾT. Hai lỗi tách bạch, không
gộp thành một điểm: **A** = mực < 70% KHUNG mà khung lại chiếm > 90% sân khấu
(cơ chế nhỏ trôi trong khung quá khổ) · **B** = rail lệch > 24px (hình và chữ
hai hệ căn lề).

⚠️ KHÔNG chấm bằng tỉ lệ lấp một mình: 17% là ĐÚNG nếu khung cũng ôm sát 17% ấy.
Lỗi là 17% mực trong khung rộng 100%, nên mẫu số là KHUNG chứ không phải thẻ.

Cách chọn "mực có nghĩa" khai ngay trong file (bắt buộc — ba lần đo trước đều
trả về số mà vẫn sai): tính `<svg>` + phần tử LÁ có sơn; bỏ div BỌC (rộng bằng
thẻ nên nuốt mọi phép đo) và bỏ đồ đạc của thẻ (tiêu đề, chú giải, thuyết minh,
bảng gập, thanh tham số).

Hai hiện vật đã sửa trong chính script: lỗi trong trang bị nuốt thành
"(không trả lời)" nên bốn target hỏng đọc ra như thiếu mẫu — nay lỗi nổi lên; và
lượt nạp nặng thỉnh thoảng không trả kịp nên có THỬ LẠI một lần, vẫn hỏng thì
ghi dòng `KHÔNG ĐO ĐƯỢC` chứ không im lặng bỏ.

### `simulations/stage-size.ts`
M19 — MỘT LUẬT KÍCH THƯỚC SVG SÂN KHẤU, một chủ sở hữu. `stageSvgSize(w)` trả
`width={w}` + `max-width: 100%` (co được, KHÔNG phóng được).

Vì sao gom: sáu renderer cùng viết `width="100%"` + `maxWidth: w`, dạng đó KHÔNG
khai bề rộng riêng nên khi cha là `fit-content` thì `100%` không có gì quy chiếu
và Chrome rơi về 300px mặc định (`boolean_dag` đã dính: sơ đồ 662px vẽ ở 300px).
Nó cũng buộc phải kèm `margin: 0 auto` để trông cân, và chính cú căn giữa đó tạo
RAIL THỨ HAI — đo được `and_gate` lệch 581px, `decimal_to_binary` 673px.

Áp cho `binary/ui` · `logic/ui` · `network/ui` · `algorithm/program-module`.
`ArrayView` giữ bề rộng tự đo từ khung chứa (nó vốn co giãn theo cột) nhưng đã
BỎ `margin: 0 auto` cùng lý do.

### `frontend/scripts/evidence.mjs`
W0 — XUẤT XỨ CỦA BẰNG CHỨNG. `provenance(tool, env)` gắn `head` (git SHA) +
`dirty` (cây có thay đổi chưa commit) + môi trường vào MỌI artifact sinh ra;
`assertFresh(path)` là cổng đọc lại — artifact sinh từ commit khác bị xếp
**STALE_EVIDENCE** và không được chống lưng cho trạng thái DONE.

Vì sao cần: trước đó artifact chỉ có `when` (một dấu thời gian), nên nó có thể
sinh từ một commit khác hẳn commit đang xét mà vẫn trông "mới". Ba artifact
chính (`m19/after.json`, `m18/classroom-acceptance.json`,
`m17/w4b4a-experience/probe.json`) đều KHÔNG có dấu HEAD lúc kiểm.

Đã gắn vào: `audit-composition.mjs` · `accept-classroom-m18.mjs` ·
`accept-experience-w4b4c.mjs`.

---

## Trả nợ sync-lock 2026-08-20 (rơi lại từ `d4c1ef6`, `b06c0e9`, `09c0f49`)

Năm file dưới đây đã landed mà không có entry — `code-index-sync.test.ts` ĐỎ ở
HEAD trước khi wave sinh-ngữ-nghĩa bắt đầu. Ghi **cái chúng sở hữu**, không chỉ tên.

### `frontend/scripts/verify-semantic-e2e-render.mjs` · `verify-live-gemini-render.mjs` · `verify-real-browser-render.mjs` · cần Chrome + `npm run dev`

Ba runner Playwright chụp mô phỏng do đường `semantic_program` sinh, ở 4 viewport
(1920 · 1536 · 1366 · 768), phục vụ các lượt chứng nhận `b06c0e9`/`09c0f49`.

> ⚠️ **Cả ba đều hardcode `ARTIFACT_DIR` trỏ RA NGOÀI REPO**
> (`C:/Users/Bunny/.gemini/antigravity-ide/brain/…`). Bằng chứng ghi ra đó
> **không tái lập được** và theo luật dự án thì không được ghi DONE. Spec
> 2026-08-20 (E13) mới chỉ bắt được **một** trong ba file — Task 13 của plan phải
> sửa **cả ba**.

---

## Miền HÌNH HỌC KHÔNG GIAN (2026-08-24 → nay)

> Đổi đề tài: `STATUS_LEDGER §0-2026-08-24`. Kế hoạch (lưu trữ từ W19): `docs/legacy/geometry/`
> (`GEOMETRY_ROADMAP` · `MIGRATION_PLAN` · `CURRENT_SYSTEM_MAPPING` ·
> `GEOMETRY_ARCHITECTURE_GAP_REPORT`).

### `backend/app/simulation/geometry/` — nhân hình học · offline · **0 API call**

Bốn tầng, phụ thuộc MỘT CHIỀU: `exact` → `predicates` → `kernel` → `measure`,
cộng `section` ở trên cùng.

**QUYẾT ĐỊNH NỀN: số học `Fraction` CHÍNH XÁC, KHÔNG epsilon.** Đề hình học THPT
cho toạ độ hữu tỉ, và đại số tuyến tính trên ℚ ở lại trong ℚ — giao tuyến, hình
chiếu, thiết diện, thể tích đều hữu tỉ. Vô tỉ chỉ ở độ dài/góc, nhốt trong
`measure` bằng cách giữ **bình phương** (`d²`, `cos²θ` đều hữu tỉ). Hệ quả: tầng
vị từ **không có một epsilon nào** — vuông góc ⇔ `u·v == 0`, song song ⇔
`u×v == 0`, đồng phẳng ⇔ `det == 0`. Claim nâng từ *"tất định"* lên **"chính
xác"**: tất định là chạy lại ra cùng kết quả, **kể cả cùng một kết quả sai**.

`predicates` **cố ý KHÔNG phụ thuộc `kernel`**: `postconditions` gọi vị từ để
kiểm chứng, và nếu vị từ dựa vào chỗ dựng thì oracle đang kiểm chính cái nó vừa
dựng ra.

`section` sở hữu thêm (2026-08-30) **so sánh hai thiết diện**:
`canonical_cycle` · `same_section_cycle` — dạng chuẩn bất biến với XOAY và với
ĐẢO HƯỚNG, vét cạn 2n ảnh của nhóm nhị diện rồi lấy dãy nhỏ nhất theo khoá
`Fraction`. Không float ở đường này (`test_dang_chuan_KHONG_dung_float` quét mã
nguồn). `[A,B,C,D] ≡ [B,C,D,A] ≡ [D,C,B,A]` nhưng `[A,C,B,D]` là tứ giác KHÁC.
Và **bốn mã suy biến tách rời** — `PLANE_DOES_NOT_CUT` (không điểm chung) ·
`PLANE_TOUCHES_VERTEX` · `PLANE_TOUCHES_EDGE` · `CONTAINED_INFINITE_INTERSECTION`
(mặt phẳng chứa trọn một mặt của khối — ca này CHƯA hỗ trợ, đã khai). Bản cũ gộp
hai ca đầu vào một mã VÀ một câu *"toàn bộ khối nằm về một phía"*, câu ấy sai cho
ca chạm đỉnh. `_kiem_hau_dieu_kien` là hậu điều kiện của chính `cross_section`
(≥3 đỉnh · không trùng · mọi đỉnh trên mặt cắt), **không** phải checker thứ hai.

`section.cross_section` đi theo **MẶT, không theo ĐIỂM**. Gom giao điểm rồi sắp
quanh trọng tâm cần `atan2` — kéo vô tỉ vào đúng chỗ đang giữ chính xác — **và**
vứt mất thứ tự dựng. Đi theo mặt thì mỗi mặt cho một cạnh, và dãy cạnh ấy chính
là dãy bước học sinh làm trên giấy: timeline có sẵn, không phải bịa sau.

FAIL-CLOSED với mã **phân biệt hai tình huống dạy hai điều khác nhau**:
`PARALLEL_NO_INTERSECTION` (giao rỗng) ≠ `CONTAINED_INFINITE_INTERSECTION` (giao
vô số điểm). Hai đường **chéo nhau** cũng ném — trên hình phẳng chúng trông như
cắt nhau, trả một điểm "gần đúng" ở đó là **dạy sai**.

`measure` sở hữu **năm** phép khoảng cách bình phương và một tầng phân nhánh ở
trên chúng: `distance_sq_point_line` · `distance_sq_point_plane` ·
`distance_sq_parallel_lines` · `distance_sq_skew_lines`, và (2026-08-30)
`distance_sq_lines` · `distance_sq_line_plane` · `distance_sq_planes` —
ba hàm **không tính gì mới**, chúng hỏi `predicates` xem cấu hình nào rồi gọi
đúng hàm cũ. Ba trường hợp suy biến trả `0` chứ không ném: đường **cắt** ·
đường **trong** mặt · hai mặt **trùng**. Tầng gọi vì thế không phải kết luận
quan hệ trước khi đo — đó là lý do ba hàm này nằm ở kernel chứ không ở cầu nối.

Khoá bởi `tests/geometry/test_geometry_kernel.py` (40) + `test_section.py` (15),
đáp án **kiểm tay**, không chép từ đầu ra kernel. ⚠️ Tiêm lỗi lượt đầu chỉ làm
2/37 đỏ vì toạ độ `(0,1,2,½)` float biểu diễn đúng hết — đã thêm ca dùng bộ mẫu
`(3,7,11,13)` tìm bằng **dò số** (`det` float = `1.084e−19` thay vì `0`).

### `backend/app/simulation/semantic_program/geometry_exec.py` · offline

Cầu nối IR ↔ kernel. Export: `build_initial` · `eval_geometry_expr` ·
`exec_construct_point/line/section` · `GEOMETRY_TYPES` · `volume_polyhedron` ·
**`volume_of`**.

`volume_of` (2026-09-03, `VOLUME_VERIFICATION_BRIDGE`) là **cửa điều phối thể
tích dùng chung cho HAI đường**: `_do` (đường chạy) và
`geometry_obligations.check_volume` (đường chấm). Nó chọn giữa `volume_polyhedron`
và `curved.the_tich` theo LỚP runtime, và **không** kiểm kiểu — người gọi kiểm,
vì hai bên từ chối bằng hai thứ tiếng khác nhau. Trước nó, phép điều phối ấy chỉ
nằm ở `_do`, còn checker thì `isinstance(Polyhedron)` — nên hệ tính đúng
`V = 288π` rồi tự từ chối phục vụ (`ball_1`, probe §18). Khoá bởi
`test_geometry_wave2.py::test_MOT_nguon_su_that_cho_the_tich` (đòi CẢ HAI đường
đi qua đúng cửa này và **chỉ** cửa này chạm hai thẩm quyền toán học).

**LUẬT CỐT LÕI**: hàm ở đây nhận **TÊN** đối tượng, đọc từ bộ nhớ, gọi kernel.
Không hàm nào nhận **toạ độ kết quả** từ IR. Thêm một trường `result` vào
`ConstructPointStmt` "cho nhanh" là trao quyền quyết kết quả cho LLM —
`test_R0_*` trong `tests/geometry/test_geometry_ir.py` khoá lại.

`distance` nhận **chín** cặp toán hạng: điểm×{điểm,đường,mặt} và (2026-08-30)
đường×đường · đường×mặt · mặt×đường · mặt×mặt. Cầu nối chỉ **phân loại kiểu**
rồi uỷ cho `measure`; nó không tự phân biệt chéo/song song/cắt. Cặp không hợp lệ
(khối, thiết diện) bị chặn **trước kernel** ở `ir_static_check._KIEU_DO`, nên mô
hình còn cơ hội sửa. Test: `tests/geometry/test_spatial_distance.py` (36).

Biểu thức `intersect_line_line` thêm 2026-08-25 **sau một lượt live**: mô hình
viết đúng nó ở cả ba lượt thử cho `Q = d ∩ AD` (dạng phổ biến của bài thiết
diện) và hợp đồng từ chối, trong khi kernel đã có phép ấy từ đầu. Thêm một biểu
thức hình học phải sửa **BỐN** chỗ — `contract.ValueExpr` ·
`validator._BIEU_THUC_HINH_HOC` · `eval_geometry_expr` · schema đã export — và
`test_MOI_bieu_thuc_hinh_hoc_deu_co_NGUOI_THUC_THI` nay bắt ca quên chỗ thứ hai.

Cũng sở hữu **vị từ "giá trị này có lên được hình không"**: `la_doi_tuong_hinh_hoc`
· `la_dai_luong_do` · `KIEU_DAI_LUONG`. Chúng ở **tầng kernel** có chủ đích — hai
người dùng là `simulation_state.build_scene` (chiếu ra cảnh) và
`learner_surface` (cổng), mà cổng **không được** nhập tầng trình bày. Đây là chỗ
duy nhất cả hai cùng nhìn được mà không đảo chiều phụ thuộc; hai bản `isinstance`
song song sẽ trôi khỏi nhau đúng vào ngày thêm một kiểu hình học mới, và khi ấy
cổng NÓI DỐI. Khoá bởi `tests/geometry/test_learner_surface_3d.py` (14).

**`chuan_hoa_dai_luong`** (2026-09-04, `SCALAR_FACT_VISIBILITY`) đứng cạnh hai vị
từ ấy vì nó trả lời vế còn lại: *làm sao một giá trị TRỞ THÀNH đại lượng*.
Interpreter nạp `initial_value` nguyên văn, nên `IA = 6` nằm trong bộ nhớ dưới
dạng `str "6"` và **cả hai** người đọc đều không nhận ra nó — `build_scene` bỏ
qua, `learner_surface` từ chối phục vụ. Cổng ấy vì thế **không thoả mãn được**
với mọi dữ kiện đề vô hướng: thẻ hình học cấm mô hình khai binding và cũng không
phơi `visual_bindings`.

Chuẩn hoá ở biên nạp bộ nhớ chứ **không** dạy riêng cổng đọc chuỗi thô: cổng
đang nói thật, và nới riêng nó sẽ cho xanh trong khi cảnh vẫn trống — đúng hình
lỗi *"cổng bảo có trên hình, cảnh thì không vẽ"*. Ba ranh giới: kiểu KHAI không
đổi (chỉ đổi biểu diễn runtime) · dùng đúng `parse_exact`, không nới văn phạm ·
đọc không được thì giữ nguyên (fail-closed).

⚠️ **Chỉ áp trong miền hình học** (`mien_hinh_hoc=`, dẫn từ việc spec có khai
kiểu hình học nào không). IR dùng chung với miền Tin học, nơi `int` là **chỉ
số**; bản đầu chuẩn hoá mọi vô hướng và 14 ca Tin học đỏ ngay với
`chars[Fraction(0,1)] ngoài [0,5)`. Khoá bởi
`tests/geometry/test_scalar_fact_visibility.py` (24), gồm ca S0 đỏ được dưới
hành vi trước wave và không dính hình cong.

### `docs/evaluation/geometry/custodian/geometry_oracle.py` · **0 API call**

Oracle độc lập, chỉ `import fractions`. Đầu vào là **tuple số thuần** (dạng dây)
— không có đường nào cho hai bên vô tình dùng chung kiểu rồi dùng chung một lỗi.

**Hai chiến lược theo bản chất câu hỏi**: thiết diện kiểm **6 BẤT BIẾN, không
dựng lại** (kiểm bằng tính chất độc lập hơn kiểm bằng dựng lại — hai bản cài
cùng thuật toán dễ mang cùng lỗi và triệt tiêu nhau); thể tích dùng **phân rã
KHÁC** (kernel chia quạt từ đỉnh chóp, oracle chia tứ diện từ một điểm trong).

Khoá bởi `test_oracle_independence.py` — ba mức, **chỉ mức 3 là bằng chứng**:
không import mã sản phẩm (soi bằng `ast`, không quét chuỗi — bản đầu quét chuỗi
và đỏ oan vì chính docstring nhắc tên module bị cấm) · khớp trên bài kiểm tay
(CẦN, chưa ĐỦ) · **tiêm lỗi vào kernel thì oracle BẮT ĐƯỢC** (4 phép tiêm) ·
cộng hai ca ranh giới chống **bắt oan**.

### `backend/scripts/run_geometry_dev_evaluation.py` · **TIÊU QUOTA THẬT**

Runner đo sinh chương trình hình học. **Hai tập, một mã**: mặc định chạy `dev/`
(được nhìn); `--holdout` chạy `holdout/cases.json` đã niêm phong và **đối chiếu
hai băm trước khi tiêu call đầu tiên** — `seal_hash` (tập đề không bị đổi) và
`measured_system_hash` (hệ không bị sửa kể từ lúc niêm phong). Lệch băm nào cũng
là `DungSach`, không phải cảnh báo.

Trần **nhân theo số bài** (`TRAN_LOGIC_MOI_CASE=6`, `TRAN_HTTP_MOI_CASE=8`, dẫn
từ call graph) — N=10 vẫn ra đúng 60/80 đã duyệt, N=20 ra 120/160. Viết cứng `60`
thì lượt held-out đứt ở bài thứ mười và nhìn hệt như hệ hỏng.

Đường ra dẫn từ cờ: `dev-results/` vs `holdout-results/` — ghi đè baseline cũ là
mất một thứ không lấy lại được. `neo_kho_ma()` ghi **hai phạm vi bẩn** (toàn kho
vs chỉ `MEASURED_SYSTEM_PATHS`) vì hai định nghĩa "sạch" trong kho này khác nhau.
Khoá bởi `tests/geometry/test_geometry_dev_runner.py`.

### `backend/scripts/cache_clear.py` · offline · **0 API call**

Xoá cache phân tích đề. Phải chạy **trong container** (`docker compose exec
backend python scripts/cache_clear.py …`) vì `DATABASE_URL` trỏ `db:5432` — chạy
từ host sẽ lặng lẽ đụng SQLite thay vì DB thật.

Tồn tại vì có **bốn** tầng giữ "bản cũ" và chúng gỡ bằng bốn cách khác nhau
(bảng đầy đủ: `docs/OPERATIONS.md`). Tầng này — cache exact ở Postgres, khoá
theo *(text đề chuẩn hoá + `CACHE_VERSION`)* — là tầng **restart không chạm
tới**, và vì thế là tầng lừa người nhất.

KHÔNG thay `CACHE_VERSION`: bump vẫn là đường chính thức khi đổi prompt/định
tuyến, vì nó là một tuyên bố đọc được trong lịch sử. Script này cho việc thử đi
thử lại một đề trong lúc đang sửa. `--tat-ca` đòi thêm `--toi-chac-chan` — nó
xoá kết quả đã trả cho người học, không phải file tạm.

### `backend/scripts/acceptance_integrity.py` · offline · **0 API call**

**Tầng toàn vẹn cho mọi lượt đo sống**, thêm 2026-09-04
(`ACCEPTANCE_RUNNER_INTEGRITY`). Không chạy lượt đo nào; nó là thứ runner MỚI
phải đi qua. Xuất: `ARTIFACT_SCHEMA_VERSION` · `IntegrityError` · `RunManifest`
· `mo_run` · `ghi_artifact` / `doc_artifact` · `seal_bo_ca` / `kiem_bo_ca` ·
`chuan_hoa_telemetry` / `kiem_bat_bien_token` · `moi_truong_hien_tai` /
`kiem_moi_truong` · `phan_loai_dirty` · `tom_tat_tu_artifact` /
`tu_kiem_tom_tat` · **`TRUONG_MANIFEST_1_1`** · **`kiem_manifest_du_truong`** ·
**`kiem_ghim_bo_do`** · **`kiem_san_sang_live`** · **`PHIEN_BAN_DOC_DUOC`**
(năm cái sau thêm 2026-09-05).

`RunManifest` **1.2** ghim *"đo NHƯ THẾ NÀO"*: bốn băm bộ đo (`scorer_hash` ·
`threshold_policy_hash` · `attribution_rubric_hash` · `policy_loader_hash`) +
danh tính model (`model_provider` · `model_name` ·
`model_version_or_snapshot` · `model_reproducibility` ·
`response_model_version` · `sdk` · `api_endpoint_class`) + `decoding_parameters`
· `repair_limit` · `transport_retry_policy` · `application_call_budget`. Trước
1.1 manifest chỉ ghi `runner_hash`, nên bộ chấm và ngưỡng đổi được sau khi biết
kết quả mà không cổng nào thấy.

⚠️ **1.1 → 1.2 đổi HÌNH DẠNG tham số giải mã**, không chỉ thêm trường: ba
trường phẳng `temperature`/`top_p`/`max_output_tokens` thành một khối có kiểu
`{"mode": …, "value": …}`. Lý do: `None` ở dạng phẳng **gộp** *"không gửi"* với
*"provider có mặc định mà ta không quan sát được"* — cái đầu ta biết hết, cái
sau ta chỉ biết là mình không biết. `PHIEN_BAN_DOC_DUOC` giữ 1.0 và 1.1 đọc
được; `kiem_danh_tinh_model` giữ nhánh phẳng cho 1.1.

⚠️ `kiem_ghim_bo_do` nhận **dict đọc từ đĩa**, không nhận `RunManifest` trong bộ
nhớ — và đó là toàn bộ điểm của nó. Ghim rồi tính lại trong cùng một tiến trình
là phép so **luôn đúng**; trôi chỉ quan sát được khi so bản ĐÃ GHI của lượt
trước với hiện tại.

Sở hữu bảy luật, mỗi luật dựng từ một sự cố ĐÃ XẢY RA:

| luật | sự cố nó chặn |
|---|---|
| `chuan_hoa_telemetry` — MỘT thẩm quyền tên trường, thiếu ≠ 0, trường lạ thì NÉM | runner in `INPUT_TOKENS 0` cho một lượt tiêu hàng chục nghìn token (đọc `input` trong khi `usage_report()` trả `prompt_tokens`) |
| `ghi_artifact` — từ chối đè · ghi nguyên khối (tạm → `fsync` → `os.replace`) · từ chối file ĐÃ ĐỌC trong tiến trình | một glob shell coi artifact đã commit là ĐẦU RA và ghi đè nó |
| `doc_artifact` — hỏng/cụt/sai phiên bản thì NÉM | reader lặng lẽ `continue` sẽ báo tổng nhỏ hơn sự thật |
| `seal_bo_ca` / `kiem_bo_ca` | sửa ca sau khi thấy đầu ra = tự chọn kết quả |
| `kiem_moi_truong` gọi TRƯỚC MỖI lượt gọi | artifact trộn hai phiên bản hệ |
| `phan_loai_dirty` — chỉ chặn ở `DUONG_TRONG_YEU` | không bắt user commit việc dở dang để một cổng xanh |
| `tu_kiem_tom_tat` — đọc LẠI từ đĩa rồi tính lại | ghi trượt đường dẫn · đối tượng sót trong bộ nhớ · file ghi dở |

⚠️ `ARTIFACT_SCHEMA_VERSION` **tách khỏi `CACHE_VERSION`** có chủ đích: cache là
chính sách sản phẩm, đây là hình dạng file bộ đo. Trộn hai thứ là buộc một lượt
bump cache mỗi khi thêm một trường báo cáo.

### `backend/scripts/acceptance_verdict.py` · offline · **0 API call**

Phán quyết MỘT ca. Xuất: `trich_ket_qua` · `co_giai_doan` · `phan_loai` ·
`cham_ca_am` · `sua_duoc` · `nghia_vu_du_noi_dung_hut_ten` · `LOP_PHAN_QUYET`.

**`trich_ket_qua` đọc `outcome.final_memory`, KHÔNG đọc `scene3d`.** Runner
V1/V2 đọc `envelope["scene3d"]`, nên `ball_1` (chặn ở `postconditions` ⇒ không
có cảnh) cho `dai_luong = []` rồi bị xếp `MODEL_COMPOSITION_FAILURE` — một lỗi
HỆ tính vào cột năng lực mô hình. `route.SemanticRouteOutcome.final_memory` nói
thẳng trong docstring rằng nó là thứ **duy nhất** đem so ground truth được.

**`phan_loai` tách lỗi HỆ khỏi lỗi MÔ HÌNH bằng mã lỗi, không bằng văn xuôi.**
Chỗ tinh nhất: `POSTCONDITION_VIOLATED` vừa nổ khi bộ kiểm không với tới chủ thể
(HỆ) vừa nổ khi chương trình khai sai số (MÔ HÌNH). Phân biệt bằng chính lời
checker — `_LECH` (*"giá trị không khớp"*) nghĩa là nó ĐÃ tính lại được từ hình
rồi thấy lệch. Cùng tiêu chí `test_measure_checker_subject_drift` dùng.

**`REQUESTED_OPERATION_UNCOVERED` KHÔNG tự nó là lỗi hệ** (đính chính
2026-09-04, `docs/SMALL_DEVELOPMENT_PROBE.md`). Cùng mã, hai nguyên nhân ngược
nhau, và nhãn cũ sai ở cả hai chiều. Hai hàm trả lời hai câu riêng:
`_cong_phu_hep_hon_bo_kiem` so `OBLIGATION_KINDS` với `kieu_kiem_chung_duoc`
(bắt lại vết `CURVED_MODEL_ACCEPTANCE_V1`); **`nghia_vu_du_noi_dung_hut_ten`**
đọc chính chương trình — witness của nghĩa vụ có được sinh bởi đúng lượng đo,
trên một chủ thể ĐÚNG KIỂU không? Có ⇒ chương trình đã tính đúng thứ được hỏi,
chỉ hụt ràng buộc TÊN ⇒ lỗi HỢP ĐỒNG. Không ⇒ mô hình soạn sai thật.

**`sua_duoc` đọc `stage_reached` + `error_code`**, thay cho bản cũ khớp chuỗi
tiếng Việt trong thông báo lỗi — chênh lệch ấy đã đo được ở probe §18 (*"bộ đo
chạy 2; LUẬT SẢN PHẨM cho 3"*).

**`cham_ca_am`**: fail-closed **chưa** phải chứng minh ranh giới. Ca âm phải khai
trước `target_boundary` + `expected_codes`; chết sớm ở R0 ⇒
`TARGET_BOUNDARY_DEMONSTRATED = NO`, không được gọi là `HONEST_REFUSAL`.

### `backend/scripts/run_curved_acceptance.py` · ⚠️ **TIÊU QUOTA THẬT**

Runner nghiệm thu hình cong. Hai chặng cố ý: **8A** một lượt tổng hợp mỗi ca
(`MAX_SEMANTIC_PROGRAM_ATTEMPTS` ghim xuống 1, ghi kết quả **trước** mọi lượt
sửa nên số one-shot không bao giờ đẹp lên) · **8B** chỉ sửa ca mà đường sản
phẩm **thật sự** gửi lỗi ngược (schema · ir_static · grounding — lỗi runtime
xảy ra ngoài vòng sửa nên KHÔNG repair-eligible).

Từ 2026-09-05 (`V3_RUNNER_MANIFEST_INTEGRATION…`) nó đi qua tầng toàn vẹn.
Xuất thêm: `mo_luot_do_v3` (mười bước tiền kiểm, **tất cả** trước lượt gọi
provider đầu tiên) · `canh_gac_truoc_luot_goi` (trước **mỗi** analyze/tổng
hợp/sửa) · `tran_luot_goi_v3` · `nap_ca_v3` · `kiem_bo_ca_la_pool_v3` ·
`ghi_bang_chung_quy_trach_nhiem` · `quet_bi_mat`.

⚠️ **`CA` là corpus V1/V2, KHÔNG phải pool V3.** 9 đề viết tay, đã chạy,
artifact đã công bố — tức **dữ liệu phát triển**. Dùng nó ở chỗ đáng lẽ là pool
V3 cho ra một con số trông như nghiệm thu held-out mà thật ra là chấm trên bài
đã biết: hỏng im lặng, và hỏng theo chiều **luôn đẹp lên**.
`kiem_bo_ca_la_pool_v3` chặn bằng id.

⚠️ **Và điều đó ĐÃ xảy ra.** Tới `144aa79` (2026-09-05) `main_async` vẫn gán
`chay = CA`: `nap_ca_v3`, `mo_luot_do_v3`, `mo_run`, `canh_gac_truoc_luot_goi`
đều **không** nằm trên đường chạy thật, và không `manifest.json` nào được ghi.
Sửa ở `V3_LIVE_ENTRYPOINT_WIRING_REPAIR` — từ đó `CA` **không với tới được** từ
live path (khoá bởi hai test quét AST trong
`tests/test_v3_live_entrypoint_wiring.py`), và nó chỉ còn hai vai: dữ liệu
phát triển, và tham chiếu cho chính `kiem_bo_ca_la_pool_v3`.

**`nap_ca_v3()` trả BA thứ** kể từ wave đó: `(ca_chuẩn, ca_thô, case_set_hash)`.
`ca_chuẩn` có `mong` là **`set`** — `_chay_mot` chấm bằng `mong <= set(...)`, mà
pool lưu `list` (JSON không có set) nên `list <= set` ném `TypeError` **sau** khi
ca đó đã tiêu lượt analyze lẫn lượt tổng hợp. `ca_thô` giữ `list` vì `seal_bo_ca`
băm bằng `json.dumps`, và giữ nguyên bản đọc từ pool cũng là thứ làm băm khớp
con dấu byte-đối-byte. `case_set_hash` lấy từ **con dấu**, không tính lại.

**`cham_ca_theo_duong_san_pham`** (thêm `ACCEPTANCE_POST_MODEL_PATH_ALIGNMENT`,
2026-09-05) — chấm MỘT ca bằng đúng ba thẩm quyền của sản phẩm: đáp số từ
`acceptance_verdict.trich_ket_qua` → `outcome.final_memory`; cảnh từ
`pipeline._dung_scene3d`; phán quyết từ `acceptance_verdict.phan_loai`. Trả ba
nhóm `execution` / `results` / `classification`.

⚠️ **Bốn cột TÁCH RỜI, và đừng gộp lại.** `runtime_executable` ·
`exact_answer_match` · `scene3d_pass` · `postconditions_pass` · `servable`.
`c7a` của V3 là fixture chuẩn: ba cột đầu True, hai cột sau False — chương
trình ĐÚNG mà hệ không dám phát, tức lỗi **HỆ**. Bản trước runner đọc đại lượng
từ `outcome.envelope["scene3d"]`, mà `route` cố ý không dựng cảnh ⇒ phép chiếu
LUÔN RỖNG ⇒ `dap_so_khop` không bao giờ True được. `phan_lop` (7 lớp) giữ lại
dưới `classification.legacy` để chẩn đoán — nó **không đọc `servable`** nên mù
với `verification_gap`, và **không** tham gia ngưỡng.

⚠️ Cổng canh đặt ở `call_gemini`, **không** ở `_chay_mot`: một ca gọi analyze
một lượt rồi `stage_semantic_program`, mà hàm ấy lặp tới
`MAX_SEMANTIC_PROGRAM_ATTEMPTS` lượt **bên trong**. Cổng trước `_chay_mot` sẽ bỏ
sót mọi lượt sửa. Bọc/gỡ quanh **từng ca** trong `finally` — vá toàn cục sống
sót qua ngoại lệ sẽ rò một cổng trỏ vào thư mục của lượt đã kết thúc.

⚠️ `canh_gac_truoc_luot_goi` đọc lại manifest **từ đĩa mỗi lượt**, không cache
— thứ nó canh là *file đổi giữa hai lượt gọi*, nên giữ trong bộ nhớ là bỏ đúng
thứ cần canh. Và nó **không** tự cập nhật manifest cho khớp file mới: manifest
là ảnh chụp trước kết quả.

### `backend/scripts/measurement_policy.py` · offline · **0 API call**

**Thẩm quyền NGƯỠNG + RUBRIC**, thêm 2026-09-05
(`V3_THRESHOLD_AND_RUN_IDENTITY_POLICY`). Đặt cạnh scorer chứ không nhét vào
scorer: scorer trả lời *"ca này thuộc lớp nào"*, file này trả lời *"ngưỡng và
rubric là gì, và có bị đổi không"*. Xuất: `CHINH_SACH_NGUONG` /
`RUBRIC_QUY_TRACH_NHIEM` (hai file dưới `scripts/policies/`) · `bam_chinh_tac` ·
`doc_chinh_sach` · `nap_nguong` / `nap_rubric` · `TRUONG_BAT_BUOC` /
`TRUONG_DECODING` · `kiem_danh_tinh_model` · `cau_hinh_model_hien_tai` ·
`san_sang_live_tu_cau_hinh` · `kiem_bang_chung_quy_trach_nhiem` ·
`kiem_chinh_sach` · **`CHE_DO_THAM_SO`** / `tham_so` / `kiem_tham_so_giai_ma` ·
**`derive_application_call_budget`** · **`RESPONSE_MODEL_VERSION`**.

`kiem_danh_tinh_model` trả bốn verdict, và thứ tự giữa chúng có ý nghĩa:
`MODEL_IDENTITY_UNPINNED` (alias khi CHƯA cho phép LIMITED — chưa biết đo model
nào thì tham số của nó là câu hỏi sau) → `DECODING_INCOMPLETE` →
`LIMITED_ACCEPTED` → `PINNED`. **`LIMITED_ACCEPTED` không phải `PINNED` đổi
tên**: danh sách "thiếu" vẫn khai alias là alias.

`san_sang_live_tu_cau_hinh` trả **hai** danh sách `(chặn, giới hạn đã khai)`.
Gộp chúng là lỗi đã mắc: alias bị đếm như một *chặn*, nên sau khi người hướng
dẫn chấp nhận `LIMITED` thì readiness vẫn đứng ở `CONDITIONAL` mà không nói
được còn thiếu gì.

Dạng chính tắc `json.dumps(sort_keys=True, ensure_ascii=False,
separators=(",",":"))` — reformat file **không** đổi băm, đổi một **con số**
thì đổi. Hình thức tự do, nội dung bất biến.

⚠️ **`_la_so` không phải phép kiểm thừa.** Phép kiểm tham số giải mã ban đầu là
`is not None`, và `run_curved_ergonomics_v2.py:297` ghi thật
`"repair_attempts": "mặc định sản phẩm"` — một chuỗi văn xuôi lọt qua, đọc như
đã khai, không nói con số nào. Đo bằng máy: guard trước khi cứng trả `PINNED`,
sau khi cứng trả `DECODING_INCOMPLETE`. Loại cả `bool` (`True` là `int` trong
Python). Khoá bởi `tests/test_v3_threshold_and_run_identity.py` (46).

### `backend/scripts/certify_acceptance_runner.py` · offline · **0 API call**

Chứng nhận **lắp ráp**, không phải từng mảnh — năm kịch bản đi trọn vòng đời
(mở lượt → manifest → từng ca → artifact → tóm tắt → tự kiểm). Chỉ **provider**
là giả; `verify_and_compile`, cổng phủ, checker, `final_memory` đều THẬT.

Hai ca là **lỗ đang có thật**, không phải tình huống bịa: `duong_4` dùng
`angle`/`vector3` (mục duy nhất trong `KHONG_KIEM_DUOC`) để sinh
`SYSTEM_VERIFICATION_FAILURE` thật; `am_1` gắn nghĩa vụ `volume` vào `point3` để
cổng phủ bác thật. Khoá bởi `tests/test_acceptance_runner_integrity.py` (36),
gồm ba phép tiêm chứng minh chính bài chứng nhận đỏ được.

`chung_nhan` trả **ba** giá trị từ 2026-09-05: `(ok, sai, chưa_sẵn_sàng)`. Phần
tử thứ ba **không** phải lỗi của bộ đo nên không kéo verdict xuống FAIL — nó là
`READY_FOR_INDEPENDENT_V3_LIVE`, đo trên **cấu hình thật** của kho. Tách vì lượt
chứng nhận chạy trên ca tổng hợp với `model={"provider": "gia"}`: bắt một ca giả
khai danh tính thật thì cách duy nhất để nó xanh là nói dối.

**`chung_nhan_runner_v3`** (thêm 2026-09-05) là bài kiểm **riêng**, 12 phép,
chạm `run_curved_acceptance.py` THẬT với provider giả. Cần riêng vì `chung_nhan`
chạy bài kiểm **tổng hợp của chính nó**: nó xanh suốt quãng runner V3 chưa chạm
`mo_run` một lần nào — *"chứng nhận PASS"* và *"runner V3 đã lắp"* là hai câu,
và một thời gian dài câu thứ hai là SAI trong khi câu thứ nhất vẫn xanh.

**`chung_nhan_live_entrypoint`** (thêm `V3_LIVE_ENTRYPOINT_WIRING_REPAIR`) —
nhãn **`V3_LIVE_ENTRYPOINT_INTEGRATION`**. Cùng bài học, một tầng nữa:
`chung_nhan_runner_v3` gọi **thẳng** `mo_luot_do_v3` bằng hai ca của chính nó,
nên nó chứng minh *hàm* đúng và xanh suốt quãng `main_async` chạy corpus phát
triển. Hàm này chạy **chính `main_async`** với pool/seal tổng hợp đã rút
(`_pool_gia`, 26 bài / 13 ô) + provider stub, rồi chứng minh bảy điều: bộ ca
đến từ con dấu · corpus phát triển không lọt · manifest có **trước** lượt gọi
đầu · mỗi lượt gọi có guard đi trước · trần **78** · `mong` đã chuẩn hoá ·
băm bộ ca V3 ở mọi artifact và **không** có `CA_HASH`. `READY_FOR_INDEPENDENT_
V3_LIVE = YES` chỉ phát khi nhãn này PASS. Khoá bởi
`tests/test_v3_live_entrypoint_wiring.py` (34 test, 7 phép tiêm).

**`chung_nhan_duong_hau_model`** (thêm 2026-09-05) — nhãn
**`ACCEPTANCE_POST_MODEL_PATH_INTEGRATION`**. Chạy trọn đường hậu-model trên
ca servable THẬT (`duong_1_dung`) rồi ca verification-gap THẬT (`duong_4`),
chứng minh sáu điều gồm: thẩm quyền đáp số là `outcome.final_memory`, Scene3D
dựng bằng chính hàm pipeline dùng, và bốn cột **tách được**.
`READY_FOR_FUTURE_CURVED_ACCEPTANCE = YES` đòi **cả hai** nhãn tích hợp — một
lượt đo đi đúng pool mà chấm sai tầng vẫn cho ra con số sai.

⚠️ Hai nhãn cố ý tách và **phạm vi in kèm**: `V3_RUNNER_INTEGRATION` nói về
*hàm* `mo_luot_do_v3`; `V3_LIVE_ENTRYPOINT_INTEGRATION` nói về *đường chạy
thật*. Đọc nhãn thứ nhất theo nghĩa thứ hai chính là chỗ wave trước để lọt.

### `backend/scripts/seal_curved_v3.py` · offline · **0 API call**

Niêm phong pool **V3 hình cong** (`docs/evaluation/geometry/curved-v3/POOL.json`
→ `V3_SEAL.json`) và rút tập đo bằng seed ngoài. Cùng giao thức
`seal_geometry_holdout.py` — một bài mỗi ô, `--seed` không mặc định — nhưng ô ở
đây là **13 ô hình cong** (9 dương `C1–C9` · 4 từ chối `N1–N4`), khai trong
chính POOL chứ không trong mã.

Sở hữu **`CONG_THUC`** — 13 công thức SGK, và đây là điểm khác quan trọng nhất
so với mọi bộ ca trước: `mong` **không được gõ tay**. `_kiem()` tính lại mọi kỳ
vọng từ `cong_thuc` + tham số và **từ chối niêm phong** nếu lệch. Gõ tay 26 đáp
số thì sẽ có đáp số sai, và một kỳ vọng sai đọc ra thành *"mô hình hỏng"* — lỗi
tệ nhất một bộ đo mắc được.

Số chính xác (`So`, `_can`) **cài lại tại chỗ**, cố ý KHÔNG dùng
`geometry/radical.py`: sinh kỳ vọng bằng chính mô-đun sắp bị đo là tự soi
gương. Cùng lý do oracle hình học dùng thuật toán khác kernel.

`--rut` từ chối khi: pool trôi khỏi `pool_hash` · hệ đổi khỏi
`measured_system_hash` · **đã rút một lần rồi**.

⚠️ Con dấu mang `ghi_chu_doc_lap`: pool do agent soạn **sau khi** đọc hết ca
hỏng V1+V2, nên tính độc lập chỉ đến từ hai thứ kiểm được — pool băm trước khi
có seed, và seed do người khác chọn. Seed tự chọn ⇒ phải khai.

### `backend/scripts/seal_geometry_holdout.py` · offline · **0 API call**

Rút + niêm phong tập held-out. Sở hữu **`BANG_O`** — 20 ô đích danh (14 tầng A
phủ đủ tám nghĩa vụ hình học + 6 tầng B ngoài phủ) — và `kiem_pool`.

**Đa dạng là tính chất của thiết kế, không phải may rủi của seed**: rút *một bài
mỗi ô*, seed chỉ chọn *bài nào trong ô*. Mỗi ô một `Random` gieo từ
`(seed, tên ô)` để thêm bài vào ô này không làm trượt phép rút ở ô khác. Ô thiếu
bài ⇒ dừng, **không rút bù** — rút bù là lặng lẽ đổi tập đo thành tập dễ hơn.

**`kiem_du_dieu_kien_rut` sở hữu HAI ngưỡng pool**, cùng `MOI_O_TOI_THIEU = 1`
và `TONG_TOI_THIEU = 40` (`HOLDOUT_PROTOCOL §3①`: *"≥40 bài, phủ ĐỦ 20/20 ô"*).
Hai vế hỏi hai câu khác nhau — **độ phủ** *(mọi ô có bài chưa)* và **độ sâu**
*(seed còn gì để chọn không)*. Trước 2026-08-28 cổng rút chỉ canh vế phủ, còn
`report_holdout_readiness` canh vế sâu bằng một số `40` **viết tay**: pool đúng
một bài mỗi ô thoát `0` trong khi mọi seed cho ra **cùng một tập**, tức tính
held-out mất mà không cổng nào kêu. Tách khỏi `main()` để **đỏ được từ test** —
hai ngưỡng này chỉ chạy một lần trong đời, ngay trước lượt đo duy nhất.

`--seed` **không có mặc định** (tôi chọn seed thì tôi chọn được cả tập).
`kiem_pool` chặn: thiếu `nguon.url` · thiếu `phep_chuyen` · ô B mang
`oracle_result` · `chua_chay_he` không true · **đề trùng tập DEV** · và (từ
2026-08-27) **`can_kiem_tay` còn `true`** — nợ đối chiếu của đề thu bằng công cụ
đọc web, vì nội dung đi qua một mô hình tóm tắt nên `problem_text` là bản chép
LẠI chứ không phải nguyên văn; cờ vắng mặt ⇒ không ảnh hưởng bài soạn tay.

**`status` + `duoc_rut()` (Phase 7A.5)** — `accepted` (mặc định khi vắng) ·
`rejected_capability_boundary` · `needs_manual_review`. Bài không `accepted`
**giữ trong `cases`** (xoá là *loại im lặng*, một dạng chọn tập) nhưng **không
vào rổ rút và không đếm vào độ phủ** — lấp ô bằng bài hệ không phục vụ được là
dựng một ô chắc chắn trượt. Bài ấy chỉ bị đòi `reason` + `nguon.url`; đòi
`oracle_result` ở một bài vừa bị loại **vì** không có oracle biểu diễn được là
một vòng lặp vô nghĩa. Băm hệ thống
mượn thẳng `freeze_evaluation_candidate.measured_system_hash()` để hai con số
không bao giờ trôi khỏi nhau. Giao thức: `docs/evaluation/geometry/HOLDOUT_PROTOCOL.md`.
Khoá bởi `tests/geometry/test_holdout_protocol.py` (25).

### `backend/scripts/run_phase7b_official.py` · **TIÊU QUOTA THẬT**

Lượt đo CHÍNH THỨC Phase 7B: 20 bài đã niêm phong × `k = 3`, trần 360 logic /
480 HTTP. Export: `_kiem_truoc_khi_chay` · `cham_oracle` · `_manifest` · `RA`.
Không viết máy đo mới — nối `measure_geometry_stability.mot_luot` với tập
niêm phong và bộ chấm theo pool (`run_geometry_dev_evaluation.cham_oracle`).

**Cổng 12 mắt xích chạy TRƯỚC lời gọi model đầu tiên**: seal_hash · seed · 20
bài · 20/20 ô · measured_system_hash · metric · capability · expectation · k ·
ngân sách · cây sạch. Kiểm sau thì đã muộn — quota đã tiêu, và một lượt chạy
trên hệ đã đổi thì con số của nó không gắn với bản nào cả.

**TIẾP TỤC ≠ CHẠY LẠI.** `mot_luot` ghi `{case_id}-lan{n}.json` NGAY sau mỗi
lượt, nên sự có mặt của file là bằng chứng bền của một lượt đã hoàn tất; bộ
chạy chỉ BỎ QUA nó. Không có bảng trạng thái thứ hai để lệch. `RUN_MANIFEST`
ghi một lần; manifest cũ khai tập khác ⇒ từ chối.

⚠️ **`TAP_KY_VONG` phải trỏ `holdout`.** `measure_geometry_stability` mặc định
`"pilot"` và cache lại ở cấp module. Quên đổi thì may ra `KeyError`, tệ hơn là
chấm ③a/③b bằng kỳ vọng CỦA BÀI KHÁC mà không cổng nào kêu.

### `backend/scripts/score_phase7b_official.py` · offline · **0 API call**

Chấm lượt chính thức từ artifact đã ghi. Export: `cham` · `hoan_chinh` ·
`_tap` · `_on_dinh` · `_taxonomy`. Mỗi chỉ số báo **bốn số trước tỉ lệ** (tử ·
mẫu áp dụng · N/A · trượt) và không chỉ số nào bị ép về mẫu chung —
`METRIC_CONTRACT §4` cấm gộp `None` vào `False`, vì `construction_match=None`
nghĩa *đề không ra lệnh dựng* còn `False` nghĩa *ra lệnh mà không dựng*. Hai
tập: `ALL_20` và `PUBLIC_SOURCE_19` (bỏ ô A12 `curated_preseal`) — một bài tự
soạn nằm lẫn mà không tách ra thì nó lặng lẽ thổi phồng tuyên bố *"đề từ nguồn
ngoài"*. `hoan_chinh` chặn chấm khi thiếu lượt, trùng lượt, có bản ghi lạ, hay
vượt trần. **Không in PASS/FAIL cho câu hỏi nghiên cứu**: đã soát ba tài liệu
giao thức, KHÔNG có ngưỡng chấp nhận nào đăng ký trước, nên nó in
`EVIDENCE_SUPPORTS_3D_NEXT` và tự khai đó là diễn giải.

### `backend/scripts/provider_health_gate.py` · **1 API call, ĐÚNG MỘT**

Hỏi nhà cung cấp ba câu trước khi tiêu quota cho bất kỳ lượt đo nào:
credential còn hợp lệ · credit dùng được · model gọi tới được. Ép
`ApiBudget(max_attempts=1)` để **tắt thang retry**.

**Vì sao tắt retry ở đây, đo được 2026-08-29**: `MAX_ATTEMPTS = 4` tồn tại để
nuốt sự cố NHẤT THỜI của một lượt đo thật, nhưng `429 credits depleted`
không nhất thời. Lượt canary trước tiêu **12 HTTP** (3 lượt × 4 lần thử) cho
đúng một thông tin đã biết ngay từ request đầu; cổng này tiêu **1**.

Cố ý KHÔNG kèm `responseSchema`, KHÔNG nạp skill: nó kiểm ĐƯỜNG TRUYỀN, không
kiểm khả năng. Trộn hai thứ thì một lỗi schema đọc ra như lỗi credential.
Ghi `wave1-canary/PROVIDER_HEALTH.json`.

### `backend/scripts/run_wave1_dev_stability.py` · **TIÊU QUOTA THẬT**

Bộ đo DEV của wave sửa lỗi sau Phase 7B. Ba chế độ: `--canary` (3 đề × 1
lượt, chứng minh end-to-end trước) · `--mini` (4 đề × k, chỉ chạy SAU canary
PASS) · mặc định 8 đề. Trần cứng wave `90 logic / 120 HTTP`, chặn **trước**
khi vượt chứ không dừng sau.

**Dừng sớm khi hỏng vì NHÀ CUNG CẤP**: quét `su_co` tìm `429`/
`RESOURCE_EXHAUSTED` rồi in `PROVIDER_BLOCKED` và thoát `2`. Phân biệt này là
toàn bộ giá trị của trường `su_co` — trước đó lời nhắn 429 bị rơi mất và một
lượt hết quota đọc y hệt một lượt hệ ném lỗi, hai nhóm khác hẳn nhau trong
taxonomy (E và F).

`_bang_token` cộng token theo **ba mẫu số**: mỗi lượt · mỗi IR **chạy được** ·
mỗi IR **đúng**. Một con số tổng che mất chỗ đắt: 1/3 lượt hỏng thì giá thật
của một kết quả dùng được gấp ba giá trung bình mỗi lượt.

Đề DEV do wave này viết (`w1-goc-dd` · `w1-goc-dm` · `w1-phay`), kỳ vọng ở
`expectations/wave1.json`. **KHÔNG** dùng đề của 20 bài chính thức.

### `backend/scripts/measure_geometry_stability.py` · **TIÊU QUOTA THẬT**

Máy đo độ ổn định: `n` đề × `k` lượt ĐỘC LẬP, không sửa gì giữa chừng. Export
dùng lại được: `BAI` (3 đề nền) · `mot_luot` · `cham_oracle` · `RA` ·
`RUN_ID` · `_dong_nghia_vu` · `TAP_KY_VONG`. Bản ghi mang `run_id` ·
`replicate_index` · bộ đếm `logical_calls`/`http_requests`/`retry_requests`/
`transient_hits` của ĐÚNG lượt ấy — một con số tổng hợp cuối buổi thì không
đối chiếu được với trần đã duyệt. `cham_oracle(ten, fm, hd=None)`: tham số thứ
ba là `RequestContract`, bộ chấm theo pool cần `ob.witness` để biết đọc biến
nào trong `final_memory`. Gọi thẳng `run_pipeline` **không qua HTTP** —
cố ý: không có cache nào cho một kết quả cũ lẻn về. Bọc
`stage_semantic_analyze`/`stage_semantic_program` từ NGOÀI để bắt
`RequestContract` + `SemanticProgramSpec` (telemetry không phát hai thứ ấy, mà
chúng đúng là "model output" cần ghi riêng). **Từ chối ghi đè** thư mục đã có
bản ghi — suýt mất 15 artifact của Phase 6.7 vì quên đổi `--out-dir`.

⚠️ Kỳ vọng nghĩa vụ **KHÔNG** còn ở đây từ Phase 7A.2 → `geometry_expectations`.
Thiếu kỳ vọng cho một đề ⇒ `_ky_vong_cua` **dừng**, không chấm bằng tập rỗng.

### `backend/scripts/run_phase7a_pilot.py` · **TIÊU QUOTA THẬT**

PILOT: **kiểm bộ đo, không đánh giá mô hình** — 5 đề × `k`. Không viết máy đo
thứ hai: nạp `measure_geometry_stability` rồi **thay dữ liệu + thêm hai oracle**
(`khoang_cach_12_5`, `goc_cos_sq_1_4`), ghi đè `M.RA`/`M.BAI`/`M.cham_oracle` ở
cấp module. Hai đề mới chọn số có chủ đích: `12/5` không trùng dữ kiện nào của
đề, và góc **đường–đường** phân biệt được `cos_sq_between_lines` với
`sin_sq_line_plane` (một đề đường–mặt 45° thì không).

### `backend/scripts/geometry_expectations.py` · offline · **0 API call**

Sở hữu **KỲ VỌNG NGHĨA VỤ** của một tập đề, và hai phép so của chỉ số ③. Export:
`nap` · `kinds_kiem` · `vat_phai_dung` · `khop_kiem` · `khop_dung` ·
`cham_mot_luot` · `tap_da_dung` · `TAP_CHO_PHEP_NGUOI_DO`.

**HAI TẬP RỜI NHAU** (Phase 7A.2), vì đề hình học ra hai loại lệnh:
`construction_obligations` = vật đề bảo **dựng** · `verification_obligations` =
mệnh đề đề bảo **kiểm**. Trước pha này chúng là một danh sách phẳng, và kỳ vọng
`{point_on_line, point_on_plane}` của bài thiết diện bị **8 lượt liên tiếp** bác
bỏ — `point_on_plane` là một mệnh lệnh dựng xếp nhầm vào tập kiểm, nên nó không
có witness và **không bao giờ đúng được** (`PHASE_7A_1_REPORT §5`).

**Hai phép so KHÁC NHAU, có chủ đích**: kiểm so **bằng đúng** (khai thừa cũng là
lệch), dựng so **chứa đủ** (điểm trung gian là phần bắt buộc của phép dựng hình,
trừ điểm ở đó là phạt mô hình vì làm đúng). Ba trạng thái như oracle — `None`
tách *không áp dụng* khỏi *không chấm được*.

Không viết lại phép so nào đã có: `khop_kiem` mượn
`reliability_v2.obligation_match`, `tap_da_dung` mượn
`analyze_construction_dependency.phan_tich`, hoà giải tên mượn
`domain_profile.khop_ten_doi_tuong` (**lưới của sản phẩm**, không phải lưới thứ
hai của bộ đo).

`nap()` **fail-closed** ngay lúc nạp, không đợi lúc chấm: tập `holdout` khai
`nguoi_danh_gia.loai = "nguoi_do"` ⇒ từ chối (`TAP_CHO_PHEP_NGUOI_DO` chỉ có
`pilot`); `sinh_tu_model_output` không phải `false` ⇒ từ chối; nghĩa vụ thiếu
`ly_do` ⇒ từ chối. Dữ liệu: `docs/evaluation/geometry/expectations/pilot.json` +
`holdout.template.json`. Khoá bởi
`tests/geometry/test_expectation_contract_7a2.py` (32) — file test ấy cũng khoá
**mốc đóng băng** bốn chỉ số còn lại trong `PHASE7_METRIC_CONTRACT §6`.

**Thêm ở 7B-prep — nối tới ORACLE bằng CON TRỎ.** Tập ngoài `pilot` còn phải có
`slot` và, với ô `A*`, một `oracle_ref = {pool_case_id, khoa}`; ô `B*` **cấm**
mang nó (chấm bằng *từ chối trung thực*, không bằng đáp án) và phải ghi
`ghi_chu_kiem`. Con trỏ chứ không phải bản sao: `holdout/pool.json` sở hữu
`dap_an_chinh_thuc`/`phep_chuyen`/`oracle_result` và là thứ được niêm phong —
chép giá trị sang là tạo bản thứ hai của đáp án. `kiem_noi_oracle(d, pool_cases)`
(tách khỏi `nap()` vì cần pool) bắt: con trỏ trỏ vào hư không · sai khoá oracle ·
`problem_text` lệch giữa hai file. Khoá bởi `test_holdout_readiness_7b.py` (29).

### `backend/scripts/run_m1_pipeline.py` · offline · **0 API call**

Chạy **trọn** chuỗi holdout bằng MỘT lệnh: `ingest → pool → scaffold →
freeze check → coverage → readiness`. `--ghi` để ghi thật, không có thì chỉ soi
(chế độ soi **không đụng** `pool.json` — có test khẳng định).

**Vì sao gộp**: năm lệnh rời có một chỗ hỏng người dùng không thấy — chạy
`ingest --ghi` rồi **quên** `scaffold`, hoặc chạy `coverage` mà quên
`freeze_expectation_check`; pool đổi mà báo cáo không, và lần sau đọc báo cáo
là đọc một trạng thái đã chết.

**Vì sao KHÔNG gộp `seal`**: nó tiêu seed của GVHD và chỉ chạy được một lần;
để trong một lệnh chạy-hàng-ngày là mời một cú `--ghi` lỡ tay tiêu mất con dấu.
Khoá bởi `test_chuoi_KHONG_gop_seal`.

Hỏng thì in đúng ba dòng `FAILED_STAGE` · `REASON` · `FIX_REQUIRED` — không để
người đọc ngược log tìm chặng chết.

Lọc trùng `case_id` đi qua `ingest_holdout_batch.loc_trung` — trước 2026-08-28
chỗ ấy **bỏ qua im lặng**, vô hại với lô một bài nhưng là **mất bài không ai
biết** với gói 47 khối.

### `backend/scripts/make_human_copy_packet.py` · offline · **0 API call**

Sinh `PHASE7B_HUMAN_COPY_PACKET.txt` — **một** file cho toàn bộ phần con người.
Export: `PHAT` (số khối phát mỗi ô) · `DA_SOI` (ứng viên đã soi tận trang) ·
`SOURCE_GAP` · `dung_goi`.

**Xếp theo NGUỒN, không theo ô** — đó là toàn bộ lý do nó tồn tại: cái đắt của
người chép là **mở lại tài liệu**, không phải gõ thêm một đề. Gói gom 20 ô về 4
nhóm nguồn ⇒ mỗi tài liệu mở đúng một lần.

Máy prefill mọi thứ **suy ra được** (`slot` · `capability_tag` · `answer_shape`
· nghĩa vụ · thang chấm · luật sàng của ô · ràng buộc riêng) bằng dòng `#` —
`ingest` gỡ sạch dòng `#` trước khi lấy `problem_text`, nên siêu dữ liệu không
lọt vào đề. **Không** prefill `problem_text`, kể cả bản máy đã đọc từ ảnh
trang: `HOLDOUT_SOURCE_POLICY §4` — hành vi chép của người CHÍNH LÀ bước xác
minh, một bản nháp đặt sẵn ở đó chỉ mời người ta bấm qua.

Phát **dư** (47 khối cho ngưỡng 40): tỉ lệ đạt đo được ở vùng đã soi ≈25%, phát
đúng 40 là chắc hụt. **Không** hạn ngạch cứng từng ô — giao thức chỉ đòi ≥1 mỗi
ô và ≥40 tổng. `--ghi` **từ chối ghi đè** gói đã có: gói điền dở là công sức của
người, máy không dựng lại được.

### `backend/scripts/validate_human_copy_packet.py` · offline · **0 API call**

Soi gói **giữa chừng**, bao nhiêu lần cũng được. Export: `go_khoi_trong` · `soi`.

`go_khoi_trong` là mấu chốt: gói phát dư nên **khối chưa điền là trạng thái
bình thường**, trong khi `ingest` từ chối cả lô khi thấy một chỗ trống (đúng
với một lô đã nộp, sai với một gói đang điền). Nó bỏ khối còn chỗ trống, soi
phần đã điền, và **nói rõ đã bỏ mấy khối**.

Cảnh báo **ký hiệu bị rơi** (`_DAU_HIEU`): ô A06–A08 mà đề không nhắc *vuông
góc* / `⊥`, A03–A05 không nhắc *song song* / `∥`, v.v. Bắt đúng cái hỏng đã đo
được — trích PDF rơi sạch `⊥` (0 lần trong 217 trang) mà văn bản **vẫn đọc trôi
chảy**. Cảnh báo, không tự loại.

**Tách `cần chép` khỏi `reserve`** (2026-08-28): khối đã prefill `NGUỒN:` là
ứng viên máy đã xác minh, người chép phải gõ đề vào; khối để trống hoàn toàn là
**sức chứa**. Bản trước gộp cả hai nên gói 51 khối / 42 ứng viên báo *"50 còn
trống"* khi mới chép 1 — đếm sai theo hướng làm nản. Nguyên nhân là `\s*` quay
lui vô hiệu hoá lookahead `(?!<)`, khiến `NGUỒN: <…>` của khối reserve vẫn khớp;
nay **bắt giá trị rồi kiểm** thay vì lookahead.

⚠️ `PACKET_READY: YES` **không** nói đề đúng nguyên văn nguồn — máy không kiểm
được điều đó, và giả vờ kiểm được là bỏ đúng cái cổng `NGƯỜI CHÉP:` vừa dựng.

### `backend/scripts/run_phase7b_data_pipeline.py` · offline · **0 API call**

MỘT lệnh cho cả tuyến: `soi gói → [sáu chặng của run_m1_pipeline] → ngưỡng ≥40
→ mốc M`. Export: `MOC` · `moc_hien_tai`.

**Gọi lại `run_m1_pipeline`, không chép nó**: hai bản sao của cùng dây chuyền
là hai bản sẽ trôi khỏi nhau, và cái trôi ở đây là *tập đo được niêm phong theo
luật nào*. Phần riêng là hai đầu — soi gói ở trước, ngưỡng + mốc ở sau.

**Nguyên tử, không partial**: một lỗi ⇒ không ghi bài nào. Pool ghi một nửa thì
`pool_hash` trong con dấu không còn nói được nó niêm phong cái gì. Đổi lại, gói
soi được giữa chừng miễn phí. Hỏng thì in `FAILED_CASE` (**đích danh bài**, vì
với 47 khối thì *"có lỗi ở đâu đó"* là câu không dùng được) · `FAILED_STAGE` ·
`REASON` · `FIX_REQUIRED`.

Chế độ soi cộng thêm phần *sẽ* ghi trước khi tính ngưỡng — đọc thẳng pool trên
đĩa thì ngưỡng báo `0` ngay dưới dòng coverage vừa báo `2`, hai con số cùng màn
hình cãi nhau.

### `backend/scripts/finalize_phase7b_holdout.py` · offline · **0 API call**

MỘT lệnh chạy **sau khi người chép xong gói**. Export: `main`. Nó **không thêm
chặng nào** — gọi lại `run_phase7b_data_pipeline` rồi trả lời một câu mà dây
chuyền ấy không trả lời: *sau khi nạp, còn thiếu bao nhiêu và vì sao bài nào bị
loại*. Khoá bởi `test_bo_hoan_tat_KHONG_lap_lai_nghiep_vu_cua_duong_ong` (đo
**lời gọi**, không đo chữ — tên hàm trong docstring là giải thích).

**Vì sao đáng có**: một con số đã sai một lần — **42 ứng viên KHÔNG phải 42
`accepted`**. Báo cáo tách bạch `CANDIDATES / ACCEPTED / REJECTED` và không bao
giờ in số gộp. Thoát `1` khi chưa đủ ngưỡng nhưng **vẫn in báo cáo** (đó chính
là lúc cần nó nhất); chỉ `2` — hỏng dữ liệu — mới dừng sớm.

**Ba loại ô trống, tách riêng, vì gộp là giấu mất loại nguy hiểm nhất**: `A12`
chưa từng có nguồn (biết trước) · ô **chưa chép** (bình thường, không phải lỗi)
· **`DATA_GAP` MỚI** — đã chép mà nạp vào mất sạch, đây mới là dấu hiệu vừa
hỏng. Khi còn ứng viên chưa chép thì **không** kết luận "cần thu thêm N bài".

### `backend/scripts/scaffold_expectation.py` · offline · **0 API call**

Dựng **khung** `expectations/holdout.json` từ bài `accepted` trong pool. Export:
`dung_khung`. Chia theo **một** đường: thứ **suy ra được** máy điền
(`case_id` · `slot` · `problem_text` chép từ pool nên không bao giờ lệch ·
`oracle_ref` · `kind` từ `BANG_O`); thứ cần **phán đoán** để trống
(`nguoi_danh_gia` · `ly_do` · `trich_de` · `construction_obligations`).

**Không đoán nghĩa vụ DỰNG**: `BANG_O` chỉ định nghĩa nghĩa vụ **KIỂM**; nghĩa
vụ dựng đọc từ **động từ của đề**. Máy điền bừa vào đấy là tái lập đúng lỗi
Phase 7A.2 đi tách. Từ chối ghi đè file đã có — ghi đè một tập kỳ vọng đã soạn
là xoá phán quyết của người. Khung sinh ra **chưa nạp được**: `nap()` chặn chỗ
trống `<…>`.

### `backend/scripts/freeze_expectation_check.py` · offline · **0 API call**

Cổng **đóng băng tập kỳ vọng**, chạy TRƯỚC `seal`. Export: `kiem` ·
`bam_ky_vong`.

`geometry_expectations.nap()` kiểm được **một mình** file kỳ vọng; cổng này kiểm
thứ chỉ lộ ra khi đặt nó **cạnh `pool.json`**: bài `accepted` không có kỳ vọng
(⇒ chấm bằng tập rỗng ⇒ luôn trượt, và cái trượt ấy vào báo cáo thành *"mô hình
sai"*) · kỳ vọng mồ côi · ô lệch giữa hai file · nghĩa vụ kiểm không khớp
`BANG_O` · **nghĩa vụ DỰNG lẫn vào tập KIỂM** (cổng chống quay lại đúng lỗi
Phase 7A.2 đi tách) · con trỏ oracle trỏ vào hư không · `problem_text` lệch.
Cả bảy **không sửa được sau khi niêm phong**.

**Tách khỏi `seal` có chủ đích**: `seal` chạy **một lần** với seed của GVHD,
còn cổng này cần chạy **sau mỗi lô** lúc đang soạn — gộp hai nhịp nghĩa là muốn
kiểm kỳ vọng thì phải tiêu một seed. `--bam` in `expectation_hash` cho con dấu;
vắng file thì trả `THIẾU_FILE` chứ không trả một chuỗi trông như băm thật.

### `backend/scripts/report_holdout_readiness.py` · offline · **0 API call**

Sinh `docs/evaluation/geometry/PHASE7B_READINESS_REPORT.md` — **ảnh chụp số** của
mức sẵn sàng: environment (7 băm) · dataset (đếm theo `status`, độ phủ 20 ô, bảng
bài bị loại) · expectation · blockers. Export: `thu_thap` · `blockers` · `_md`.

**Sinh ra chứ không viết tay**, vì nó mang băm và số đếm: viết tay thì đúng đúng
một lần rồi trôi ở commit sau, và một báo cáo *sẵn sàng* nói sai về mức sẵn sàng
còn tệ hơn không có báo cáo. Khoá bởi `test_bao_cao_da_sinh_va_KHONG_TROI`.

Khác `PHASE7B_READINESS.md` — file ấy là **phân tích blocker** do người viết (vì
sao rào tồn tại, ba đường đi, cái giá từng đường). File này là **số**. Hai vai,
đừng gộp. Thoát `1` khi còn blocker.

### `backend/scripts/ingest_holdout_batch.py` · offline · **0 API call**

Nạp một **lô đề do NGƯỜI chép** thành mục `pool.json`. Export: `phan_tich` ·
`thanh_case`. Khuôn vào chỉ **ba dòng mỗi bài** (`[A14]` + đề + `NGUỒN:` +
`ĐÁP ÁN:`); script lo phần còn lại — xếp trường, gán `capability_tag` từ
`NANG_LUC`, dựng `oracle_result`, chạy `check_capability_boundary`.

**Ô tầng B dùng HAI DÒNG KHÁC: `ĐÁP ÁN NGUỒN:` + `NGOÀI PHỦ VÌ:`.** Không phải
tuỳ chọn cho đẹp — trước 2026-08-28 **B01–B06 (6/20 ô) không nạp được bằng bất
kỳ file lô nào**: khuôn lô CẤM ô B mang `ĐÁP ÁN:` (dòng ấy dựng `oracle_result`,
mà tầng B chấm bằng *từ chối trung thực*), còn `kiem_pool` lại ĐÒI mọi bài
`accepted` có `dap_an_chinh_thuc` + `ly_do_ngoai_phu`. Hai luật đều đúng phần
mình, cùng đọc một bài ⇒ chuỗi chết ở `kiem_pool` với `FIX_REQUIRED: "sửa dữ
liệu lô"` — **một việc không làm được**. Lối ra là **tách tên dòng**, không nới
dòng cũ: `ĐÁP ÁN NGUỒN:` chỉ chảy vào `dap_an_chinh_thuc`, không bao giờ thành
`oracle_result`; dùng nó ở ô tầng A thì bị chặn, và ngược lại. 5 test khoá.

**Cổng cốt lõi — dòng `NGƯỜI CHÉP:`.** Giao thức đòi đề NGUYÊN VĂN, và đã đo
được rằng **mọi kênh tự động hỏng IM LẶNG** (công cụ đọc web tóm tắt; trích PDF
rơi `⊥` — 0 lần trong 217 trang về quan hệ vuông góc). Thứ duy nhất chưa hỏng là
người mở sách đọc và gõ lại, nên **hành vi chép CHÍNH LÀ bước xác minh**: thiếu
dòng ấy ⇒ từ chối cả lô. ⚠️ Dòng ấy **do người viết** — agent tự viết là tự cấp
một chứng nhận không có tư cách cấp; `test_bo_nap_KHONG_tu_viet_dong_NGUOI_CHEP`
khoá điều đó vào docstring.

**BA CHẾ ĐỘ XÁC MINH, và TÊN DÒNG mang luôn chế độ** (`_CHE_DO`, 2026-08-29):
`NGƯỜI CHÉP:` → `human_verifier` · `MÁY CHÉP:` → `machine_verifier` ·
`SOẠN NỘI BỘ:` → `internal_author`. Đúng **một** dòng mỗi lô; hai dòng ⇒ đỏ.
Thiết kế bị bỏ: giữ `NGƯỜI CHÉP:` rồi thêm cờ `CHẾ ĐỘ XÁC MINH:` — hai mẩu
phải khớp mới đúng, mà không gì bắt chúng khớp, nên một lô chép máy vẫn ghi
được tên người thật. Trước bản này `verification_note` khẳng định *"Đề do
NGƯỜI chép nguyên văn… không qua OCR"* cho **mọi** bài — câu sinh sẵn, và nó
thành lời khai SAI ngay ở lô đầu tiên chép máy. Kèm trường
`measured_output_used_for_source_verification: false` (lời hứa nặng nhất của
tập held-out, trước chỉ nằm trong văn xuôi giao thức).

**`PHÉP CHUYỂN:` — bắt buộc ở tầng A, cấm ở tầng B.** Đáp án nguồn gần như
không bao giờ ĐÃ ở đơn vị checker: nguồn in `cos = √10/5` mà A09 nhận **cos²**;
in `V = 2a³/3` mà A14 nhận phân số với `a = 1`; kết luận *hình bình hành* mà
`parallel` chỉ nhận quan hệ hai đường. Trước dòng này `phep_chuyen` là **một
câu sinh sẵn dùng chung** (*"đáp án nguồn chép thẳng vào đơn vị checker"*) —
sai ở đúng những ca cần đúng nhất, và sai **bên trong artifact đã niêm phong**,
trong khi `seal` chỉ kiểm trường CÓ MẶT.

**`_tach_nguon` — `nguon.loai` ∈ `web` | `sach_in` | `soan_noi_bo`.** Trước
2026-08-29 cả `ten`/`url`/`vi_tri` nhận **nguyên câu trích dẫn**, nên cổng
`url.startswith("http")` xanh mà không kiểm gì. `web` đòi url thật; `sach_in`
đòi *tên sách + trang*; `KHONG_TRA_NGUOC` là trạng thái ĐỎ.

**`_nhan_trang_thai`** dựng lại `pool.__trang_thai__` TỪ `cases`. Có **hai** bộ
ghi pool song song (`ingest.main` và `run_m1_pipeline`), nên sửa một bộ thì bộ
kia đè lại — sau lượt nạp 41 bài nhãn vẫn đọc *"0 accepted · 0/20 ô"*, tức mời
người sau đi thu thập thêm rồi nạp trùng.

**`curated_preseal` — ngoại lệ DUY NHẤT, có trần cứng.** Ô A12 (khoảng cách
điểm–ĐƯỜNG, hữu tỉ) không lấp được bằng nguồn công khai (3 lượt / 673 url), và
`§5③` cấm rút bù. Bài tự soạn được nhận nhưng phải mang đủ sáu dấu hiệu
(`curated_preseal` · `SOẠN-NỘI-BỘ` · `internal_author` · `loai: soan_noi_bo` ·
`han_che` · `suy_dan` ≥ 2 cách độc lập), và `kiem_pool` đặt **trần ĐÚNG MỘT**:
ngoại lệ không trần thì lối rẻ nhất để "phủ đủ 20/20 ô" là tự soạn nốt phần
khó. Biên bản: `holdout/A12_CURATED_DERIVATION.md`. Luật báo cáo đi kèm: mọi
số nêu **hai lần** — 20/20 ô và **19/20 ô (held-out thật)**.

**Cảnh báo chứ không tự loại** (phán quyết cuối là của người): trắc nghiệm 4
phương án · căn thức · tham chiếu hình vẽ không có trong văn bản · mặt cong ·
Oxyz cho sẵn toạ độ. Chặn cứng thì có: thiếu `NGUỒN`, ô A thiếu `ĐÁP ÁN`, ô B
**có** `ĐÁP ÁN` (trộn hai thang chấm), ô ứng nhiều thẻ. Khoá bởi
`test_holdout_readiness_7b.py`.

### `backend/scripts/harvest_holdout_candidates.py` · **0 API call của hệ**

Thu **ứng viên** đề held-out từ HTML thô. Export: `soi_mot_trang` ·
`tach_khoi_de` · `go_the` · `TU_KHOA` · `LATEX`. **KHÔNG ghi vào `pool.json`** —
nó đặt đề lên bàn, `problem_text_verified` vẫn do **người** hạ.

**Vì sao có nó — hai kênh trước hỏng IM LẶNG**: công cụ đọc web đi qua một mô
hình *tóm tắt*; trích PDF tự động *rơi ký hiệu toán* (đo: `⊥` xuất hiện **0
lần** trong chuyên đề 217 trang về quan hệ vuông góc, `√ ∈ ∥` cũng 0, trong khi
`=` còn 1303 — hai thư viện độc lập cùng kết quả). Cả hai cho văn bản **vẫn đọc
như một đề bài**, mà đề mất một ký hiệu là một **bài toán khác**.

`curl` khác về **bản chất**: byte gốc, toán nằm sẵn dưới dạng LaTeX
(`\(ABCD.MNPQ\)`) — không bước nào diễn giải lại nên không bước nào làm mất.

**Ba cổng trung thực**: ① có khối *Đề bài* tách được (không ⇒ đang **đoán** đâu
là đề) · ② **không** `<img>` trong khối · ③ có dấu vết LaTeX. Cổng ② mất nhiều
nhất — phần lớn nội dung toán web tiếng Việt là **ảnh chụp**.

Sản lượng đo được (mathvn, 2026-08-27): `3883 url → 60 ứng viên → 11 có khối đề
→ 2 sạch → 0 trong ranh giới`. **Kênh đúng, nguồn cạn.** Khoá bởi
`test_holdout_readiness_7b.py`.

### `backend/scripts/holdout_coverage_matrix.py` · offline · **0 API call**

Trả lời **một** câu: *pool held-out còn thiếu ô nào?* Không thêm bài, không chọn
bài, không chấm. Export: `HO` (7 họ nội dung) · `O_HO` (`slot → (họ, hình dạng
đáp án)`) · **`O_NGUON`** (`slot → nguồn đang nhắm`) · **`O_CHO_QUYET_DINH`**
(ô chờ *quyết định*, không chờ dữ liệu — A11·A12) · `doc_pool` · `ma_tran` ·
**`_bang_ke_hoach`**.

**`_bang_ke_hoach` sinh §1b của COVERAGE_MATRIX — bảng kế hoạch 9 cột từng ô**
(cần · thẻ năng lực · oracle · chỉ số chấm · nguồn · số bài · chặn ở · việc kế
tiếp), dẫn thẳng từ `BANG_O` + `NANG_LUC`. Nó thay một bảng **gõ tay** ở
`CANDIDATE_REVIEW §3` đã sai thật: bảng ấy khai hạn ngạch **cứng** từng ô trong
khi kế hoạch cố ý để **mềm** (`≥1` mỗi ô, `≥40` tổng). Sai kiểu ấy không cổng
nào bắt — không test nào đọc markdown — nên nguồn gõ tay bị gỡ hẳn thay vì sửa
con số. Khoá bởi 8 test ở `test_holdout_readiness_7b.py`, gồm cả bẫy `sin²` ô
A10 và luật *"ô B không được mang chỉ số của tầng A"*.

`--md` **từ chối đường dẫn ra ngoài kho**: đường tương đối ghép vào **gốc kho**,
nên `../docs/…` — cách gõ tự nhiên khi đang ở `backend/` — từng lặng lẽ dựng cả
một cây tài liệu lạc bên ngoài repo (2026-08-28).

**Ba trục, cố ý không gộp**: `BANG_O` 20 ô là trục **thiết kế tập đo** (đã có,
không đổi) · `geometry_family` 7 họ là trục **nội dung** · `answer_shape`
(`construction`/`verdict`/`quantity`/`refusal`) là trục **cách chấm** — ba hình
dạng ấy dùng ba kiểu oracle khác nhau, nên lệch phân bố ở đây làm lệch cả ý
nghĩa của chỉ số ②.

Hai chỗ hai trục **không khít**, giữ nguyên có chủ đích và **dẫn từ ánh xạ chứ
không chép tay**: `proof_verification` có **0 ô tầng A** (chứng minh nằm lồng
trong sáu ô quan hệ A03–A08 ⇒ 7B không tách được *"chứng minh được"* khỏi *"nhận
ra được"*), và `B04` (Oxyz viết phương trình) **không thuộc họ nào** — ép nó vào
`plane_construction` thì bảng đủ chỗ mà đọc sai bản chất bài.

Sinh `docs/evaluation/geometry/holdout/COVERAGE_MATRIX.md`; thoát `2` khi còn ô
trống.

### `backend/app/simulation/semantic_program/purpose_analysis.py` · offline

Sở hữu câu hỏi **"bước nào phục vụ đáp án, bước nào là đường cụt"** — ghép
`RequestContract` (đề hỏi gì) với bao đóng phụ thuộc (mỗi đối tượng dựng từ gì).
Không sửa IR, **không thêm trường `why`**: mục đích tự khai thì không kiểm được.

**Ba nhãn, và phải tách ba**: `serves` · `redundant` · `name_mismatch`. Gộp hai
cái sau thì một ca lệch tên (hợp đồng gọi `(ABCD)`, chương trình khai
`ABCD_plane`) bị đọc thành "mô hình dựng hai bước vô ích" — vu oan cho mô hình ở
đúng chỗ ta sai. Nên `redundant` chỉ phát khi **mọi** tên trong nghĩa vụ giải
được, và `ti_le_huu_ich` trả `None` (không phải `0`) khi không đo được.

⚠️ **QUAN TRẮC, KHÔNG GÁC CỬA** — chương trình có bước thừa vẫn là chương trình
đúng. Có test cấm mọi module dưới `app/simulation` gọi nó.

## Đường sinh ngữ nghĩa `generic.semantic_program` (2026-08-20 → 21)

Spec: `docs/legacy/superpowers/specs/2026-08-20-semantic-program-generative-route-design.md`.
Bất biến #31–#34 ở `ARCHITECTURE_MAP §5`.

### `backend/app/simulation/semantic_program/pacer.py` · Change impact: offline

Sở hữu **NGÂN SÁCH TRÌNH BÀY** và phép gộp khung máy → bước xem. Cố ý nằm NGOÀI
`visual_adapter` để adapter giữ song ánh `frame k ⇔ trace[k]` — có song ánh đó
thì bất biến #31 mới là định lý. Bất biến riêng của nó (#32): các đoạn phân hoạch
đầy đủ, không chồng lấn, **không sinh khung mới**. Chạm trần ⇒ hạ mức chi tiết,
KHÔNG cắt.

### `backend/app/simulation/geometry/curved.py` · offline

⚠️ **HAI THANG TRỤC — đọc trước khi đụng bất kỳ phép kiểm nào dùng `L`.**
`huong_truc` cố ý trả hai thứ khác THANG: `truc` (`|u| = h`) khi khối khai bằng
ĐIỂM, `HUONG_TRUC_CANONICAL` (`|u| = 1`) khi khai bằng VÔ HƯỚNG. Nên
`L = (p−anchor)·u/(u·u)` là **tỉ lệ** `0…1` ở nhánh đầu và **khoảng cách tuyệt
đối** `0…h` ở nhánh sau.

Đây là cái bẫy đắt nhất của module: một biểu thức đọc như *"phần còn lại"*
(`1 − L`) chỉ có nghĩa ở một nhánh, và ở nhánh kia nó âm.
`CURVED_SCALAR_AXIS_SCALE_REPAIR` (2026-09-07) đã trả giá đúng chỗ ấy — hình
trụ khai bằng `(bán kính, chiều cao)` **không bao giờ** cắt ra được elip, và
lỗi ấy làm một lượt đo phải dừng trước provider.

**Quy tắc rút ra**: mọi đại lượng của một phép kiểm phải ở **CÙNG hệ đơn vị**,
và hệ đơn vị của module này là **ĐỘ DÀI²** — `d2` so với `height_sq` ở đường
tròn, `duoi_sq`/`h_half_sq`/`_con_cho_toi_day_tren` ở đường elip. Chỉ đổi sang
thang TỈ LỆ khi công thức thật sự cần (`_ti_le_doc_truc`, cho nón), vì phép đổi
ấy đòi `h` hữu tỉ và sẽ từ chối hình trụ chiều cao vô tỉ — thứ hiện đang cắt
được chính xác.

Cổng parity: `tests/geometry/test_curved_scalar_axis_scale.py` — 4 ca parity,
8 ca biên, bất biến tỉ lệ, 5 phép tiêm.

**KHỐI CONG CÓ BIÊN** — cầu · trụ · nón trên **MỘT** thẩm quyền. Thêm
2026-09-03 (Phase 2 của `CURVED_GEOMETRY_FOUNDATION_DESIGN`). Nằm giữa `kernel`
và `measure`: nhập `exact` + `kernel` + `radical`, và `simulation_state`/
`geometry_exec` nhập nó. Cùng vai `section.py` — một HỌ hình học, một module.

Xuất `Circle3` (tâm ℚ³ · pháp tuyến ℚ³ · `radius_sq` ∈ ℚ, **luôn > 0**) ·
`CurvedSolid(kind, anchor, apex_or_top, rim_point, radius_sq_khai,
height_sq_khai, pose_canonical)` · `KhoiCong` · **`KHOI_CONG`**
(bảng ba hàng — thẩm quyền DUY NHẤT của loại khối) · **`GOC_CANONICAL`** ·
**`HUONG_TRUC_CANONICAL`** · `intersect_plane_curved` ·
`the_tich` · `dien_tich_mat_cong` · `dien_tich_hinh_tron` · `ban_kinh` ·
`binh_phuong_ban_kinh` · `PI` · tám mã lỗi riêng ·
`khong_sinh_diem_tren_mat_cong`.

⚠️ **`Ellipse3` + `intersect_plane_curved_ellipse` + `dien_tich_elip`** (thêm
2026-09-07, `CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_
FOUNDATION`) — thiết diện XIÊN của **hình trụ**.

`Ellipse3(center, normal, major_dir, minor_dir, semi_major_sq, semi_minor_sq)`:
**mọi trường ở ℚ**. Bán trục giữ dạng BÌNH PHƯƠNG (cùng mẹo `Circle3.radius_sq`
— bán trục có thể vô tỉ, bình phương thì không); hai PHƯƠNG trục ở ℚ³ vì chúng
là tích có hướng của vectơ hữu tỉ (`minor_dir = u × n`, `major_dir = n ×
minor_dir`) và **cố ý chưa chuẩn hoá độ dài** — chuẩn hoá đá chúng khỏi ℚ³,
renderer làm ở biên hiển thị.

Công thức dẫn từ `u` và `n`: `b² = r²`, `a² = r²|n|²|u|²/(n·u)²`. `S = π√(a²b²)`
— nhân TRONG căn, không `√a²·√b²` (hai căn riêng là hai hạng tử phải hợp nhất).

**Bao đóng V1 hẹp có chủ đích**, hai mã mới: `ERR_ELIP_NGOAI_BAO_DONG`
(∥ trục · ⊥ trục — **nêu tên** `intersect_plane_curved` · cầu · nón) và
`ERR_ELIP_CAT_DAY` (elip bị một đáy cắt ⇒ cung elip ghép cung tròn, không phải
elip đầy đủ). Nón xiên **chưa phân xử** (elip/parabol/hyperbol tuỳ độ dốc).

⚠️ **`nghia_vu_area_la`** (thêm `CURVED_OBLIGATION_SURFACE_ALIGNMENT`,
2026-09-05) — nghĩa vụ `area` của khối này THỰC RA là lượng đo nào. `ball` →
`"lateral_area"`; trụ và nón → `None`. Lý do là hình học: mặt cầu **không có
đáy** nên "diện tích mặt cầu" và "diện tích mặt cong" là cùng một số `4πR²`,
còn `S_tp = S_xq + S_đáy` của trụ/nón thì không. Đọc qua
`measure_contract.nghia_vu_chinh_tac`, và **cả cổng phủ lẫn hậu điều kiện gọi
cùng helper ấy** — hai consumer trôi khỏi nhau là thứ
`test_F_hai_consumer_cung_goi_MOT_helper` khoá bằng quét AST.

⚠️ **BA CỘT NĂNG LỰC của `KhoiCong`** (mở rộng 2026-09-05,
`CURVED_CONSTRUCTION_GROUNDING_FOUNDATION`): `khai_bang_ban_kinh` ·
`can_chieu_cao` · `cho_pose_canonical`. Validator, thẻ văn phạm, static checker
và capability fingerprint đều **dẫn** từ ba cột này — không tầng nào được mọc
một dãy `if ball / if cylinder / if cone` riêng (`test_04c` cấm, và cấm đúng).

⚠️ **`height_sq_khai` là song sinh của `radius_sq_khai`**, và cần vì cùng lý do:
đề *"trụ bán kính 7, chiều cao 10"* không đặt tên điểm nào nên không có
`apex_or_top` nào dựng được; giữ **bình phương** vì `h = √7` không hữu tỉ trong
khi `h² = 7` thì có. `radius_sq` và `height_sq` mỗi cái có **một cửa duy nhất**,
bất kể khai bằng cách nào.

⚠️ **`truc` ≠ `huong_truc`.** `truc` là vectơ MANG độ dài (chỉ có khi biết
`apex_or_top`); `huong_truc` là HƯỚNG, luôn dựng được. Khai bằng chiều cao thì
`truc` không tồn tại trong ℚ³ nhưng hướng thì có — và hướng là thứ duy nhất mà
`axis` và mặt đáy cần.

⚠️ **POSE CANONICAL là hệ quy chiếu TRÌNH BÀY, không phải dữ kiện.** Dùng khi
đề chỉ cho vô hướng. Nó **không bao giờ** vào bộ nhớ ngữ nghĩa dưới một cái
tên — không tên ⇒ không `distance(O, X)` nào viện tới được ⇒ nó không thể thành
chứng cứ cho một phép đo. `pose_canonical` khai TƯỜNG MINH thay vì suy từ
`anchor == gốc`, vì một đề hoàn toàn có thể cho tâm đúng ở gốc toạ độ.

⚠️ **KHAI BẰNG BA ĐIỂM HỮU TỈ, không bằng (trục, bán kính).** Khai `(d, r)` thì
để dựng bất cứ thứ gì trên vành phải tìm `v ⊥ d, |v| = r` — với `d = (1,1,1)`
vectơ vuông góc hữu tỉ gần nhất có `|v| = √2`, và thiết diện qua trục rời ℚ³.
Ba điểm thì mọi toạ độ ở lại ℚ³ **kể cả khi bán kính vô tỉ và trục xiên**. Bán
kính được phép vô tỉ vì nó là ĐẠI LƯỢNG, qua `sqrt_rational` ở đúng biên đo.

Hệ quả: **thiết diện qua trục KHÔNG cần phép dựng mới** — `divide_segment(A, O,
"2")` cho điểm xuyên tâm đối, `construct_polygon` nối, `measure area` đo.

⚠️ **KHÔNG sinh điểm trên mặt cong.** Giao *đường thẳng* với mặt cong cho toạ độ
trong `ℚ(√Δ)³`; phép ấy không tồn tại và `khong_sinh_diem_tren_mat_cong` là lời
từ chối chung. `intersect_plane_curved` khai trả `circle3` và **chỉ** trả
`circle3` — ca tiếp xúc / qua đỉnh nón / mặt phẳng xiên / qua trục đều từ chối
có mã, và mỗi lời từ chối **nêu tên phép dựng đúng** đã có sẵn.

Mã lỗi tách hẳn khỏi `section.py`: `MALFORMED_CURVED_SOLID` cho neo hỏng thật,
`CURVED_SECTION_OUTSIDE_V1_CLOSURE` cho khối LÀNH mà kết quả ngoài biểu diễn —
gộp hai thứ ấy là lặp lỗi `SECTION_COPLANAR_EDGE_GAP` đã phải đi sửa.

Phép đo: `V` và `S_mặt cong` nằm **trong bảng** `KHOI_CONG` (callable mỗi hàng),
`geometry_exec` chỉ tra. **KHÔNG có `surface_area` toàn phần**: `S_tp` nón
`= πrl + πr²` có hai căn thức khác nhau, miền số từ chối tổng ấy.

IR: `+2 MemoryType` (`circle3`, `curved_solid`) · `+1` câu lệnh
(`construct_curved_solid`) · `+1` biểu thức · `+2` lượng đo (`radius`,
`lateral_area`). **Không** `height`/`slant` — chúng là `distance` giữa hai điểm
CÓ TÊN. **0 checker mới** (taxonomy nghĩa vụ đã niêm phong).

Cảnh: `RENDER_HINT` `+circle` `+curved_solid` — HAI loại vẽ cho BA hình.
Payload chở tham số (`curved_kind`, ba điểm neo, `radius_sq`, `height_sq`) và
**không** chở `vertices`/`faces`: lưới của renderer không có đường đi ngược lên
phép đo.

Tests: `tests/geometry/test_curved_foundation.py` (63)

### `backend/app/simulation/geometry/radical.py` · offline

**MIỀN SỐ CHÍNH XÁC MỞ RỘNG** — `he·π^mu·√can` với `he ∈ ℚ`, `can` nguyên dương
phi chính phương, `mu ∈ {0,1}`. Module ĐÁY: chỉ phụ thuộc `fractions`/`math`/`re`,
nên nó nằm dưới cả `exact.py` và không đảo chiều bốn tầng
`exact → predicates → kernel → measure`.

Xuất `Radical` · `ExactNumber = Fraction | Radical` (**thẩm quyền duy nhất** của
union này — module khác import từ đây, không tự khai lại) · `radical()` (cửa DUY
NHẤT vào `Radical`, luôn chuẩn hoá) · `sqrt_rational()` · `square/negate/sign/
times_rational/divided_by_rational/add/multiply` · `to_json/from_json/parse_exact/
display` · `is_exact_number` · `MAX_RADICAND` · `PI_EXPONENT_DOMAIN` ·
`RadicalDomainError`.

⚠️ `parse_exact` **đọc được π từ 2026-09-03 chiều** (`VOLUME_VERIFICATION_BRIDGE`).
Văn phạm `_MAU_CAN` trước đó CỐ Ý đóng với π, và lời chú thích nêu rõ tiền đề:
*"chưa phép đo nào sinh ra π"*. Tiền đề ấy chết từ Phase 2 mà không ai soát lại,
nên đáp số mong đợi của MỌI bài khối cong (`params["value"]` là ô STRING) rơi về
`None` = *"không có gì để so"* — cổng C₂ **fail OPEN** trên đúng họ bài đó. Nay
văn phạm đọc đúng thứ `display()` viết ra; vòng tròn `display → parse_exact →
display` khoá ở `test_volume_verification.py`.

**π thêm 2026-09-03** (`EXACT_MEASURE_FOUNDATION`, Phase 1 của
`CURVED_GEOMETRY_FOUNDATION_DESIGN`). `mu` mặc định `0`, nên `Radical(he, can)`
cũ vẫn dựng đúng số cũ và so BẰNG với số dựng sau. `PI_EXPONENT_DOMAIN = (0, 1)`
**cố ý hẹp**: mọi đại lượng cong THPT có `mu = 1`, không cái nào có `mu = 2`, và
không phép đo nào chia cho một đại lượng chứa π. `multiply` cộng số mũ và từ
chối khi ra ngoài miền; `square` từ chối mọi `mu ≠ 0` (`(π√5)² = 5π²`) — trả một
`Fraction` đúng-hệ-số mà sai-giá-trị sẽ làm bộ chấm nói PASS.

⚠️ **π đi vào ĐẠI LƯỢNG, không đi vào TOẠ ĐỘ.** `Vec3` vẫn là ℚ³ và `hf()` vẫn
từ chối mọi thứ không hữu tỉ. Khoá bởi `test_pi_exact_domain.py::test_N10_*`.
**Chưa phép đo nào sinh ra π** — nó là nền cho Phase 2, `CURVED_GEOMETRY_SUPPORT
= NONE`.

**Bất biến chính tắc**: một số có ĐÚNG MỘT cách viết. `√8` **là** `2√2`; `0·√2`,
`3·√1`, `2·√4`, `0·π·√5`, `π√4` không tồn tại (đã về dạng chính tắc lúc dựng).
Điều kiện về `Fraction` là **`can == 1` VÀ `mu == 0`**, không phải `can == 1` một
mình — `2π` có `can == 1` mà không hữu tỉ. Không có bất biến này thì phép so bằng
của bộ chấm nói dối dù số học đúng.

Mirror TS: `hienSo` + `ExactNumberJson` (kèm `pi?: number`) ở `scene3d-model.ts`.
`to_json` **bỏ** trường `pi` khi `mu == 0` ⇒ payload cũ không đổi một byte.

`sqrt_rational` **không có nhánh thất bại**: `√(p/q) = √(p·q)/q` đưa toàn bộ
phần vô tỉ về một số nguyên rồi rút bình phương ra khỏi nó. Đó là lý do
`GEOMETRY_IRRATIONAL_RESULT` biến mất khỏi đường khoảng cách (2026-08-31) — vấn
đề chưa bao giờ là tính được hay không, nó là BIỂU DIỄN.

⚠️ **RANH GIỚI CỦA MIỀN, cố ý không mở**: `add` chỉ cộng khi **cùng căn thức VÀ
cùng số mũ π** — `√2 + √3`, `π√5 + π`, `π + 1` đều từ chối. Hệ quả thật phải
khai: `S_tp` nón `= πrl + πr²` **không** viết được. Đó không phải giới hạn mới,
nó là `√2 + √3` lộ ra ở chỗ khác. Mở tổng tuỳ ý là bước đầu tiên của một CAS, và
một CAS nửa vời sai ở chỗ không ai kiểm. `parse_exact` dùng văn phạm HẸP
(`sqrt(n)`, `k*sqrt(n)`, `sqrt(n)/m`, `k*sqrt(n)/m`) — **không eval**, không
parser biểu thức, và **cố ý KHÔNG mở cho π**: không tập đo nào có đại lượng chứa
π, nên mở là viết một cửa chưa ai đi. Không có `divide` tổng quát và không có
`sqrt(π)` — cùng lý do. Trần `MAX_RADICAND` để từ chối rõ ràng thay vì treo.

Tests: `tests/geometry/test_radical_domain.py` (66) · `test_radical_distance.py`
· `test_pi_exact_domain.py` (34 — miền π, và **ranh giới toạ độ ℚ³**)
(42, năm năng lực × đo/chấm-đúng/chấm-SAI-được) · `test_radical_end_to_end.py`.
Mirror TS: `hienSo` + `ExactNumberJson` ở `scene3d-model.ts`.

### `backend/scripts/probe_dihedral_synthesis.py` · ⚠️ TIÊU QUOTA THẬT

Phép thử **NĂNG LỰC**, không phải phép thử mô hình: *một dạng bài MỚI có bắt
buộc kéo theo CODE MỚI không?* Gửi đề góc nhị diện chưa từng có template/dataset
nào, để mô hình tự tìm phân rã. Prompt (`geometry_program_generator.md`) **không
nhắc nhị diện, không nhắc `project_onto`** — kiểm bằng `grep`, đó là điều kiện
của phép đo (`§6`).

Ngân sách chặn ở **2 lượt/đề** (1 tổng hợp + 1 sửa) dù sản phẩm cho 3
(`MAX_SEMANTIC_PROGRAM_ATTEMPTS`) — chặn ở script, KHÔNG sửa hằng số sản phẩm.
Đếm `attempts` và `http_calls` RIÊNG: lượt vượt trần bị chặn *trước khi gửi* nên
không tiêu token, gộp hai con số là báo cáo thổi phồng chi phí.

Bộ kiểm `_kiem_phan_ra` xác minh **ĐỊNH LÝ, không phải cách viết**: có cạnh
chung · hai đường cùng ⟂ nó · mỗi đường nằm trong một mặt khác nhau. Cố ý KHÔNG
hỏi *"mô hình có gọi `project_onto` không"* — hỏi thế là chấm theo hình dạng
chương trình, và lượt live đã chứng minh vì sao điều đó sai: ca thành công dựng
`AB ⟂ BC` bằng tam giác vuông có sẵn, **không** dùng `project_onto`, và một
guard soi cách viết sẽ đánh trượt oan một lời giải đúng hơn cả bản viết tay.

Đã chứng minh đỏ được: chương trình "đo thẳng góc giữa hai MẶT" cho cùng con số
nhưng nhận FAIL — nó không phải một phép DỰNG. Artifact:
`docs/evaluation/geometry/dihedral-probe/`, từ chối đè lượt cũ.

### `backend/app/simulation/geometry/measure.py` — `area_polygon` · `area_section`

**MỘT thẩm quyền toán học cho diện tích phẳng.** `S = ½·|Σ Pᵢ × Pᵢ₊₁|`, chính
xác, `Fraction` hoặc `Radical`. Thêm 2026-09-03 (`EXACT_MEASURE_FOUNDATION`) —
đóng lỗ duy nhất mà `CURRENT_ARCHITECTURE_GAP_AUDIT` tìm thấy ở **cả hai** tầng
(IR lẫn kernel). **Không cần mở miền số**: cộng các tích có hướng trong ℚ³ xong
mới lấy MỘT căn.

⚠️ **THỨ TỰ PHÉP TOÁN LÀ ĐIỀU KIỆN TỒN TẠI, không phải tối ưu.** Cộng diện tích
từng tam giác thì mỗi hạng tử đã là một căn, và `radical.add` từ chối tổng nhiều
căn khác căn thức — cách ấy hỏng ở đúng những đa giác thú vị nhất (thiết diện
lục giác `3√3`). Khoá bởi `test_area_polygon.py::test_A2/test_A5`.

`area_section` là **adapter ≤3 câu lệnh**, uỷ quyền cho `area_polygon`; giữ
NGUYÊN thứ tự đỉnh `cross_section` dựng ra (thứ tự ấy **là** biên). Khoá bởi
`test_MOT_tham_quyen_toan_hoc` — nó cấm luôn cả việc đẻ `area_triangle`/
`area_quad` và cấm `sort` trong adapter.

Đồng phẳng thì **kiểm, không giả định** (dùng lại `predicates.coplanar`, so BẰNG
trên `Fraction`). Đa giác suy biến (thẳng hàng) trả **0** — đó là câu trả lời
đúng; từ chối ở đây là đặt luật thẩm định vào một phép ĐO, sai thẩm quyền
(`exec_construct_polygon` mới là nơi quyết dãy đỉnh có hợp lệ không).

IR: `measure_contract.BANG_PHEP_DO["area"]` nhận `polygon3` · `section`, một
toán hạng. **Không** nhận `solid`: diện tích toàn phần là đại lượng khác, và
tổng diện tích các mặt rơi đúng vào tổng nhiều căn thức bị từ chối.
Tên hiển thị: `_CACH_GOI["measure.area"]` → *"Diện tích …"* / `S(…)`.

Tests: `tests/geometry/test_area_polygon.py` (19) ·
`tests/geometry/test_measure_area_ir.py` (12 — đi HẾT đường IR, không chỉ kernel)

### `backend/app/simulation/geometry/measure.py` — `cos_between_vectors`

Góc CÓ DẤU, chính xác. `cos = sign(u·v) · √(cos²)`. Cố ý KHÔNG tính
`dot/(|u||v|)` trực tiếp: mẫu số là tích HAI căn thức, nằm NGOÀI miền `a·√b`;
đi vòng qua `cos²` (hữu tỉ) giữ mọi phép trung gian trong ℚ. Thứ tự phép tính ở
đây không phải chuyện phong cách.

`cos = 0` trả `Fraction(0)`, không phải `0·√b` — miền số chính tắc.

**Thẩm quyền của HƯỚNG nằm ở validator, không ở kernel.** Runtime thấy
`vector3` và `point3` cùng là `Vec3`, nên chỉ tầng KHAI phân biệt nổi.
`angle_cos` trên `line3` bị từ chối kèm lời dạy lại ở HAI cổng —
`validator._check_value_expr` và `ir_static_check._KIEU_DO`. Hai cổng phải nói
CÙNG một luật; lệch nhau thì mô hình nhận hai lời khuyên trái ngược (đã xảy ra:
`vector3` vào bảng SINH RA mà quên bảng ĐƯỢC NHẬN, giết cả 4 ca live).

Sinh vectơ: `vector_from_points` — hoàn thiện một KIỂU ĐÃ KHAI mà không có nơi
sinh. KHÔNG phải đại số vectơ (không cộng/nhân/tích có hướng), và cố ý VẮNG
khỏi `PointExpr`: nó trả `Vec3` cùng lớp với điểm, nên `construct_point` nhận
nó là dựng ra một "điểm" thật ra là một PHƯƠNG. Tests: `test_signed_angle.py`.

### `backend/app/simulation/semantic_program/contract.py` — `declare_point`

Khai điểm GỐC ngay trong `statements`, được **NÂNG** về `memory_declarations` ở
biên phân tích (`SemanticProgramSpec._nang_declare_point`, `mode="before"`).

Vì sao tồn tại: IR vốn CÓ chỗ khai điểm gốc, nhưng mô hình viết theo DÒNG THỜI
GIAN nên nói *"đặt A tại gốc"* như một BƯỚC và với tay sang `construct_point` —
câu lệnh duy nhất trong `statements` có chữ "point". 3/4 ca live đốt trọn lượt
tổng hợp đầu tiên vì đúng chỗ ấy. Ma sát BỀ MẶT, không phải lỗi ngữ nghĩa.

⚠️ **KHÔNG ép kiểu âm thầm.** `construct_point`+toạ độ → khai báo là phép ánh xạ
**không bảo toàn xuất xứ** (`construct_point` không có trường nào chở
`model_assumption`/`source_fact_id`), nên nó đẻ ra điểm gốc KHÔNG xuất xứ — đúng
thứ `grounding_gate` sinh ra để chặn. Vì thế `declare_point` là câu lệnh THẬT
mang đủ hai kênh xuất xứ; grounding vẫn hỏi đúng câu nó vẫn hỏi, có test khoá.

⚠️ **Trùng tên thì GỘP, không báo lỗi.** Mô hình khai `A` ở cả hai chỗ là nói
cùng một điều hai lần, không mâu thuẫn. Bản đầu thêm một khai báo thứ hai rồi
để phép kiểm trùng tên bắt — tự dựng lỗi rồi tự bắt, và nó thống trị 3/4 ca ở
lượt live kế tiếp. Nay điền vào chỗ TRỐNG, không đè giá trị đã có.

Hai chuẩn hoá cùng khuôn ở file này: `description` > 1000 ký tự thì **CẮT** chứ
không từ chối (nó đi đúng một chỗ — envelope hiển thị — nên để một trường TRÌNH
BÀY phủ quyết một chương trình đúng là sai tầng); `arith.op = "/"` thì **TỪ CHỐI
CÓ DẠY**, cố ý KHÔNG alias sang `//` vì hai phép không 1:1
(`Fraction(1)//2 == 0`) và alias sẽ biến chương trình ĐÚNG thành SAI CÂM.

Tests: `test_ir_ergonomics.py` · `test_offline_replay.py`.

### `backend/tests/semantic_program/test_type_authority.py` · offline

Guard chống trôi bảng kiểu, đọc **AST** của `eval_geometry_expr` rồi so với
`_CHU_KY`/`_KIEU_DO`. Chú thích trong `ir_static_check` từng khai một guard tên
`test_chu_ky_phu_het_bieu_thuc_hinh_hoc` **chưa bao giờ tồn tại** — một lời hứa
trong chú thích không chặn được gì, và bảng đã trôi thật hai lần (`section`,
rồi `vector3` giết cả bốn ca live). `validator._BIEU_THUC_HINH_HOC` nay DẪN
XUẤT từ `_CHU_KY`, nên thêm một biểu thức chỉ phải sửa MỘT bảng.

### `backend/app/simulation/semantic_program/transport.py` · offline

**BIÊN VẬN CHUYỂN** — thẩm quyền DUY NHẤT biến giá trị runtime thành giá trị
JSON trên đường ra khỏi backend. Ba hàm cho ba câu hỏi khác nhau:

  `to_transport`  cấu trúc cho MÁY      `{"kind":"radical","coefficient":…}`
  `to_display`    một SCALAR cho NGƯỜI  `"3√2/5"`
  `to_cell`       phần tử tập hợp       số/căn/điểm → chữ; hàng bảng giữ cấu trúc

Tách vì frontend làm `String(v)` trên `value_box.value` và từng `items[i]` —
nhét một dict vào đó là in ra `[object Object]`. Nên `value` giữ SCALAR và cấu
trúc đi ở trường song song `exact`, cùng khuôn `scene3d.quantity`.

⚠️ **FAIL CLOSED, không `str()`.** Kiểu chưa đăng ký thì NÉM kèm `ERR_KIEU_LA`.
Fallback `str()` che mất hợp đồng kiểu: nó biến một lỗi thiết kế thành một
chuỗi trông hợp lệ, và lần sau không ai biết dữ liệu mất hình dạng ở đâu.

`check_envelope_transport(envelope)` là cổng, gọi ở `route.py` **TRƯỚC**
`check_learner_surface` (có test khoá thứ tự). Hai cổng vì hai câu hỏi: bề mặt
học sinh hỏi *"học sinh có thấy đủ không"*, cổng này hỏi *"có ra khỏi backend
được không"*. Gộp lại thì một hôm ai đó nới cổng vì lý do sư phạm sẽ vô tình mở
đường cho một `Vec3` đi tới `json.dumps`.

Bug nó bịt (GENERALIZATION_MATRIX 2026-08-31): `visual_adapter` đặt thẳng
`Vec3`/`Fraction`/`Radical` vào envelope; `main.py` serialize để ghi cache SAU
KHI mọi cổng đã báo PASS ⇒ HTTP 500 không địa chỉ. Tests:
`test_transport_boundary.py` (24 ca, gồm replay chương trình AI thật đã lưu).

### `backend/tests/source_scan.py` · offline

Bản sinh đôi phía Python của `frontend/src/test-source.ts`: bóc docstring +
chú thích **bằng AST** trước khi guard quét mã. `than_ma(hàm|đường_dẫn)` và
`con_du(ma, moc)` (rỗng-là-hỏng). Dùng AST chứ không regex vì Python có
docstring — một biểu thức chuỗi ở vị trí câu lệnh — mà regex không phân biệt
được với chuỗi dữ liệu.

Lớp lỗi nó bịt đã lặp **năm lần**: guard *"không được dùng Y"* đỏ vì chính câu
giải thích rằng nó không dùng Y (`scene3d-page` · `canvas-first-shell` ·
`test_live_session_api` · `live-classroom` · `test_spatial_distance` với
*"`int(n**0.5)**2 == n` thì sai"*). ⚠️ KHÔNG dùng khi thứ bị cấm không được
phép xuất hiện kể cả trong lời bàn — ở đó quét cả chú thích mới đúng.

### `backend/app/simulation/semantic_program/pipeline_adapter.py` · offline

Thẩm định → thực thi tất định → dựng khung → phân nhịp → **envelope**. Xuất
`SIMULATION_ID = "generic.semantic_program"` (khớp nối giữa hai bờ — gõ lệch là
im lặng hỏng) và `compile_semantic_program_to_envelope`.

Xuất thêm **`validate_semantic_envelope_config(config) -> str | None`** — cổng
HÌNH DẠNG cho envelope đã biên dịch, đặt ở đây vì file này *sở hữu* hình dạng
ấy. Nó là bản sao tiếng Python của `validateSemanticConfig`
(`frontend/src/simulations/domains/semantic/model.ts`); chống trôi bằng CÙNG một
bộ ca ở hai bờ (`tests/semantic_program/test_envelope_config_gate.py`). Bẫy chỉ
có ở bờ Python: `bool` **là** `int`, nên `frame_lo: False` lọt thành `0` nếu
không chặn thẳng.

Ai gọi: `classroom_router._validated_envelope`. Tuyến ngữ nghĩa KHÔNG nằm trong
`CATALOG` (nó không phải target chuyên biệt), nên cổng giao bài không dùng được
`CATALOG[sim_id].validate` — và trước bản này nó **từ chối thẳng mọi envelope
hình học**, tức giáo viên không giao được đúng miền mà đề tài nói về. Nhánh này
KHÔNG chuẩn hoá config, có chủ đích: config tuyến ngữ nghĩa là artifact đã biên
dịch, không phải tham số người dùng gõ — không có dạng chính tắc nào để quy về.

### `backend/app/simulation/semantic_program/obligations.py` · offline

Sở hữu **taxonomy nghĩa vụ ngữ nghĩa** (Tin học 11 kind + hình học 9 kind) +
`SEMANTIC_PRESCRIBED_PROCEDURES`. `section_matches` thêm 2026-08-30 — nghĩa vụ
CẤU TRÚC, nhóm thứ ba bên cạnh quan hệ và đại lượng (`coverage_gate.
_CAU_TRUC_HINH_HOC`): nó không có witness, hai toán hạng nằm ở `params.solid` và
`params.plane` và cổng đòi **cả hai** phải được dựng ra.
Khoá vào HỆ KIỂU của IR, **không** vào catalog — số target là mở, số kiểu dữ liệu
thì đóng. Đóng băng trước SEALED; khoá bởi `test_taxonomy_frozen.py`, trong đó có
danh sách bốn nghĩa vụ **cố ý loại** kèm lý do.

### `backend/app/simulation/semantic_program/analyze_contract.py` · offline

Sở hữu **schema `analyze`** (thứ mô hình THẬT SỰ nhìn thấy) + `build_request_contract`.
Export thêm 2026-08-30: `_THAM_SO_LA_TEN` · `_canonical_ten`.

⚠️ **Schema ở đây quyết định câu nào NÓI ĐƯỢC.** Trước 2026-08-30, `witness` là
`STRING` không nullable và nằm trong `required`, nên "nghĩa vụ này không có
witness" là một câu **không biểu diễn được** — lượt live `geo_03` cho ra chuỗi
`"null"` rồi C₁a bác vì `null` không phải tên biến nào. Lỗi HỢP ĐỒNG, không phải
lỗi mô hình. Nay `nullable: True` **và vẫn trong `required`**: "không có" nói
được, còn "quên" vẫn bị bắt.

Cùng lượt, thêm `solid`/`plane` vào schema: `check_section_matches` đọc hai
trường ấy, mà analyze không có đường phát ra chúng — checker mạnh nhất của miền
hình học **chưa từng chấm được lần nào qua đường sản phẩm**.

`_THAM_SO_LA_TEN` (`witness` · `wrt` · `solid` · `plane`) là những tham số bị TRA
NHƯ MỘT CÁI TÊN. Chuỗi rỗng nghĩa (`null`, `none`, `-`, …) bị bỏ ở BIÊN — luật
là *tham số trỏ tới một vật phải là một định danh*, không phải bản vá cho một ca.
Test: `tests/geometry/test_section_witness_contract.py` (22).

### `backend/app/simulation/semantic_program/request_contract.py` · offline

Sở hữu **hợp đồng yêu cầu đã đóng băng** (`frozen=True`). Đây là chỗ luật "stage
sinh không được khai lại nghĩa vụ" trở thành bất khả thay vì lời dặn. Ghi rõ giới
hạn: separation of responsibility, **không phải** independent oracle.

### `backend/app/simulation/semantic_program/plane_equation.py` · offline

Đọc **PHƯƠNG TRÌNH MẶT PHẲNG** từ câu văn của đề rồi phát `SourceInvariant`.
Xuất `KIND` (`plane_equation`) · `KIND_CHUA_GIAI` (`plane_equation_unresolved`,
trạng thái **CHẶN**) · `doc_ve` · `doc_phuong_trinh` · `bat_bien_mat_phang` ·
`tuong_duong`. Thêm 2026-09-07 (`PLANE_FROM_EQUATION_REPRESENTATION`).

**Vì sao tầng này phải tồn tại**: `construct_plane_from_equation` nhận bốn hệ
số là **hằng viết thẳng trong câu lệnh**, mà `check_grounding` chỉ soi
`memory_declarations` — nên bốn con số ấy đi qua nó không bị hỏi câu nào, và
bốn con số ấy xác định một VỊ TRÍ. Phép gác không thể là `source_fact_id` của
mô hình (một chuỗi mô hình tự đặt); nó là dữ liệu **server tự đọc từ đề**, so
tỉ lệ chính xác với mặt phẳng trong trạng thái cuối. Checker nằm ở
`postconditions.check_source_invariants`; nó hỏi **trên HÌNH**, nên phủ luôn
đường dựng `construct_plane` qua ba điểm.

⚠️ **Ngưỡng hẹp ở BA chỗ, và chỗ thứ ba đã trả giá**: chỉ tuyến tính Cartesian
`x,y,z` hệ số hữu tỉ · phải có **cụm chỉ mặt phẳng** trong 48 ký tự trước dấu
`=` · và phép nở quanh dấu `=` phải canh **BIÊN TỪ**. Bản đầu không canh biên
và đọc *"mặt phẳng **đáy** = 12"* thành mặt phẳng `y − 12 = 0`, còn
*"2x + **m**y − z + 10 = 0"* thành `y − z + 10 = 0` — **một mặt phẳng SAI đem
đi đối chiếu**. Nay biên bẩn ⇒ nuốt trọn cụm chữ cái, rồi phân xử bằng
`_BIEN_DOC_LAP`: có biến mà không đọc được ⇒ CHẶN, không có ⇒ IM LẶNG.

### `backend/app/simulation/semantic_program/point_coordinate.py` · offline

Đọc **TOẠ ĐỘ ĐIỂM đề cho tường minh** từ câu văn của đề rồi phát
`SourceInvariant`. Xuất `KIND` (`point_coordinate`) · `KIND_CHUA_GIAI`
(`point_coordinate_unresolved`, trạng thái **CHẶN**) · `doc_toa_do` ·
`bat_bien_toa_do`. Thêm 2026-09-08 (`POINT_COORDINATE_SOURCE_INVARIANT`).

Peer của `plane_equation.py` và `segment_relation.py`: cả ba đọc câu văn của đề
rồi phát một ràng buộc SERVER sở hữu, khác nhau ở chỗ đọc gì.

**Lỗ nó bịt, đo được ở `NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY`**: đề cho
`B(6,0,0)`, chương trình khai `B(99,7,0)`, `source_fact_id` trỏ một fact CÓ
THẬT ⇒ hệ **phục vụ** `V = 540` thay vì `45` với `unjustified_literals = []`.
Nguyên nhân KHÔNG phải *"analyze quên trích toạ độ"* — chạy lại với hợp đồng có
đủ toạ độ trong fact cho kết quả **y hệt**. Nguyên nhân: `source_fact_id` được
kiểm **SỰ TỒN TẠI**, không kiểm **SỰ KHỚP**.

Biểu diễn dùng **hợp đồng `SourceInvariant` HIỆN CÓ**, không nới: `points` giữ
một tên điểm, `coefficients` giữ ba chuỗi phân số `(x, y, z)`. Checker ở
`postconditions.check_source_invariants`, hỏi **trên TRẠNG THÁI CUỐI** nên mọi
đường biểu diễn — khai thẳng · bí danh · dựng bằng một phép — chịu chung một
luật.

⚠️ **Ngưỡng đọc hẹp, và khai ra**: `A(1,2,3)` · `A = (1;2;3)` · số âm · phân
số · thập phân **dấu chấm** · chỉ số `A1`/`A_1`/`A₁` · phẩy `A'`. **KHÔNG**
đọc: thập phân dấu **phẩy** (`A(1,5, 2, 3)` đọc được hai cách — cố ý không
đoán) · tên đứng sau bộ ba · `x_A = 1, y_A = 2` · toạ độ 2D · toạ độ vô tỉ.
Danh sách ấy khoá bằng `test_90_GIOI_HAN_cu_phap_chua_doc_duoc` — nới grammar
thì ô đó ĐỎ, buộc người nới cập nhật phạm vi kết luận.

⚠️ **Fail-OPEN ở chiều "không đọc được", fail-CLOSED ở chiều "đọc được mà mâu
thuẫn"**. Cú pháp lạ ⇒ im lặng (chặn nó là chặn oan cả một lớp đề); cùng một
điểm hai giá trị khác nhau ⇒ `KIND_CHUA_GIAI` ⇒ **chặn**.

⚠️ Đề **không** cho toạ độ ⇒ không phát gì, nên quyền chọn hệ trục bằng
`model_assumption` còn nguyên (`test_13`, `test_14`). Đề **có** cho ⇒ hệ trục
đã do đề quyết.

`analyze_contract.gan_bat_bien_nguon(hd, problem_text)` — tách 2026-09-08 —
là **thẩm quyền duy nhất** chạy mọi bộ phát rồi ghép vào hợp đồng.
`build_request_contract` gọi nó, và bộ đo cũng phải gọi nó: replay của wave này
lúc đầu dựng `RequestContract` thẳng nên không thấy bất biến nào và báo *"bản
vá không đổi gì"* cho một bản vá đúng.

### `backend/scripts/replay_plane_from_equation.py` · offline

Replay **nguyên byte** ba ứng viên của
`SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION`, 0 lượt
gọi. Xuất `nap` · `hop_dong` · `cham` · `canh_va_trace` · `minimal_delta`.

Đọc `ung_vien_tho[i].raw` (chuỗi mô hình trả về) chứ **không** đọc
`semantic_program_cuoi`: bản đã chuẩn hoá sẽ làm mọi kết luận về *"ứng viên có
hợp lệ không"* đo phép chuẩn hoá thay vì đo ứng viên. Hợp đồng dựng lại từ raw
`analyze` của lượt chạy thật, **không** dùng `REQUEST_CONTRACT_GOLD` — gold có
`fact_id` khác nên mọi `source_fact_id` của mô hình sẽ trượt oan.

⚠️ Hỏi `ir_static` **RIÊNG**, không đọc qua `verify_and_compile` (hàm ấy chạy
grounding trước). Đó là ô người đọc tới để xem, vì tầng phép mới gỡ tắc chính
là `ir_static`.

### `backend/app/simulation/semantic_program/scale_normalization.py` · offline

Sở hữu **SOURCE_SYMBOL_BINDING / SCALE_NORMALIZATION** — phép buộc *thang tự do*
của đề hình học về `1`, tất định, do SERVER quyết chứ không do LLM. Đề viết
`AB = a`, `SA = 4a/5` ⇒ hợp đồng ra `1`, `4/5` (giữ **phân số chính xác**, không
đi qua `float`). Điểm vào duy nhất `chuan_hoa_thang(contract, problem_text)`,
gọi từ cuối `build_request_contract` và **chỉ cho `hinh_hoc`**.

Vì sao tồn tại: `_KIEU_DUOC_GIA_THIET` chỉ cho `point3`/`vector3` mang giả thiết
— đúng, và **không được nới** — nên một đại lượng vô hướng hiện thực ký hiệu `a`
không có đường hợp lệ nào. Đó là khoảng trống BIỂU DIỄN, không phải mô hình sai.

Năm chỗ **fail closed**, mỗi chỗ là một cách nói dối mà vẫn xanh: không có biểu
thức thang · **hai** ký hiệu tự do (không được tự kết luận `a = b`) · đề gán số
(`a = 5`) · ký hiệu chính là ẩn số (*"tìm a"*) · biểu thức vô tỉ/nhập nhằng
(`a√2`, `3/2a`). Xuất xứ ba chặng: `values` → `original_values` → `scale_symbol`,
`fact_id` **không đổi**. Cũng sở hữu `la_so_huu_ti` / `bang_huu_ti` — phép so
`'4/5' ≡ 0.8` mà `grounding_gate` phải dùng, nếu không mục đã chuẩn hoá đọc ra
"dữ kiện quan hệ không có gì để so" và biến kênh giả thiết toạ độ thành cửa sau.
Test: `tests/geometry/test_scale_normalization.py` (tám ca A–H của chỉ thị).

### `backend/scripts/audit_geometry_capability.py` · offline · 0 API call

Bộ ĐO năng lực hình học, chạy thật ở HEAD. Gọi thẳng **cầu nối IR**
(`geometry_exec._do`, `eval_geometry_expr`) và `GEOMETRY_CHECKERS` — không hỏi
*"kernel có hàm ấy không"*. Ranh giới ấy là toàn bộ giá trị của nó: kernel CÓ
`distance_sq_skew_lines` mà cầu nối không nối, nên `hp_b01_032` vẫn chết hai
lượt ở V3 — **lỗ ấy đã vá 2026-08-30**, và chính bộ đo này là thứ phát hiện ra
nó, nên ví dụ giữ nguyên làm lý do tồn tại của script. `--md` cho bảng tài liệu, `--json` cho máy đọc.
Kết quả và cách đọc: `docs/legacy/geometry/CAPABILITY_GAP_AUDIT.md`.

### `backend/app/simulation/semantic_program/hoisting.py` · offline

Sở hữu **lớp tiền-chuẩn-tắc cho ô toán hạng TÊN** — chạy TRƯỚC schema, biến một
phép dựng LỒNG thành một ràng buộc có tên đứng trước nó. Export: `O_TEN` ·
`TIEN_TO_TAM` · `SAU_TOI_DA` · `LY_DO_TU_CHOI` · `nang_bieu_thuc_long` ·
`dang_chuan_tac` · `kiem_nang`.

`O_TEN` là **bảng ô TÊN, DẪN XUẤT** từ `_CHU_KY` + `_TOAN_HANG_LENH`
(`measure` tra thẳng `_KIEU_DO` vì kiểu tuỳ `quantity`) — 30 ô. Ba người đọc
cùng bảng ấy: bộ nâng quyết cái gì được nâng, `grammar_card` quyết mô hình ĐỌC
THẤY `tên<T>`, `test_named_operand_slots.py` soi lại từng trường Pydantic. Thêm
một biểu thức vào `_CHU_KY` là cả ba tự đúng theo.

VÌ SAO CẦN: `FRESH_TRANSLATION_COMPOSITION_PROBE` đo được 2/4 lượt tổng hợp đầu
chết ở schema vì **cùng một thứ** — mô hình lồng `vector_from_points` thẳng vào
`translate.vector` (5 lần / 4 đề). Ý định dựng hình đúng hoàn toàn, và chạy lại
offline thì cả hai chương trình thô ấy khớp oracle. Luật *"toán hạng là TÊN"* đã
có mặt trong thẻ VÀ trong prompt; nói to hơn không phải một phép sửa.

**KHÔNG phải cửa sau của cổng trung thực năng lực** — bốn điều kiện ở `_an_toan`:
phải là biểu thức đã có trong `_CHU_KY` · kiểu trả về khớp ô · không mang
`model_assumption` · không sâu quá `SAU_TOI_DA`. Toạ độ thô, `literal`, kind lạ,
sai kiểu đều KHÔNG được nâng. Temp sinh ở **đúng khối** của câu lệnh (§14 — không
mở `CONTROL_FLOW_DEFINITE_ASSIGNMENT`), kiểu suy TĨNH nên không bao giờ `unknown`.

⚠️ Gắn vào `SemanticProgramSpec` bằng `model_validator(mode="before")` **định
nghĩa SAU `_rang_buoc_lan_dau`** — Pydantic chạy `before` theo thứ tự NGƯỢC, và
temp cần `_rang_buoc_lan_dau` cấp khai báo. Đảo hai chỗ là temp chết ở kernel.

Khoá bởi `tests/semantic_program/test_named_operand_slots.py` (16 test, gồm tám
ca A–H của chỉ thị). Audit: `scripts/audit_named_operand_ergonomics.py`;
chạy lại lịch sử: `scripts/replay_nested_operand_history.py`.

### `backend/app/simulation/semantic_program/ir_static_check.py` · offline

Sở hữu **thẩm định TĨNH trước kernel** — `kiem_tinh(spec) → StaticCheckResult`.
V3 đo được: 4/7 lượt hỏng chết ở `execution` với `GEOMETRY_OPERAND_TYPE`, và
cả bốn **đọc được từ chính chương trình**. Chết ở runtime nghĩa là mô hình
không có cơ hội sửa — vòng sửa của `stage_semantic_program` đã đóng trước đó.

Bốn mã, bốn phép sửa khác nhau: `IR_UNDEFINED_OBJECT` ·
`IR_USE_BEFORE_CONSTRUCTION` · `IR_OPERAND_TYPE` · `IR_NOT_EXACT_RATIONAL`.
`StaticIssue` mang **năm trường máy đọc được** (mã · chỉ số câu lệnh · vật ·
mong đợi · thực tế); `phan_hoi()` là chuỗi ngắn gửi ngược vào vòng sửa —
prompt chính KHÔNG phình.

**RANH GIỚI với validator, đo chứ không đoán.** `validate_semantic_program`
đã hỏi *"tên này có tồn tại không"* cho cả toán hạng câu lệnh dựng lẫn toán
hạng biểu thức. Bốn thứ nó KHÔNG hỏi và file này sở hữu: khai báo rỗng (`None`
xuống kernel) · sai KIỂU toán hạng · `ratio` không phải phân số · `measure`
sai loại đối tượng. `test_ranh_gioi_voi_validator` khoá đúng ranh giới ấy.

**`bang_ky_hieu(spec)`** (2026-09-04) — tên → kiểu cho MỌI vật chương trình
CÓ, khai báo **hoặc dựng ra**. Khác `_kieu_khai` (chỉ khai báo) một cách cố ý:
`kiem_tinh` cần bảng KHAI BÁO để giữ phân biệt *"có kiểu ≠ có giá trị"*, còn
`coverage_gate` cần bảng VẬT. Trộn hai câu vào một tên là cách lỗ cũ sinh ra.
Khai báo tường minh thắng khi trùng tên. Xem `docs/OBLIGATION_BINDING_CONTRACT.md`.

`_CHU_KY` là bảng chữ ký của mọi biểu thức hình học — bản sao ngữ nghĩa của
`eval_geometry_expr`, và đó là rủi ro thật: hai bên trôi khỏi nhau thì tĩnh
nói OK còn kernel ném. Nhánh lồng (`if`/`while`) chỉ đòi TỒN TẠI, không đòi
thứ tự — đòi chặt trong nhánh là từ chối oan chương trình đúng.
`"1.2"` được NHẬN: `Fraction("1.2")` là `6/5`, chính xác; thứ bị cấm là `float`
của JSON. `"2:1"` bị bác và **không được tự diễn giải lại** — `AM = 2MB` cho
`t = 2/3` còn đọc lối khác cho `t = 2`.
Gọi từ hai chỗ: `route` (ngay trước interpreter) và vòng sửa của
`pipeline.stage_semantic_program`. Test: `tests/geometry/test_ir_static_check.py`.

### `postconditions.check_source_invariants` — P0 · `NormalizedSourceInvariantGate`

Cổng thứ hai của `postconditions.py`, và nó hỏi câu KHÁC C₂: *"hình dựng ra có
thoả DỮ KIỆN ĐỀ CHO không"* (C₂ hỏi *"có thoả NGHĨA VỤ chương trình tự khai
không"*). Chạy trong `route` sau C₁b, trước C₂ — cần trạng thái cuối, và phải
chặn trước khi có gì được phục vụ.

Vì sao tồn tại, quan sát được ở `wave6-canary-b/w3-thang`: hợp đồng chốt
`AB = 1`, `SA = 4/5`; chương trình dựng `AB = 25`, `SA = 20`. Hình đúng QUAN
HỆ, sai THANG — học sinh đọc `12` cho đáp án `12a/25`. Không cổng nào bắt vì
các điểm đi qua kênh tự do hệ trục nên chẳng ghim mục dữ kiện nào; ở lượt khác
cùng đề mô hình CÓ ghim và bị bắt, tức phép bắt phụ thuộc **trí nhớ mô hình**.

Đầu vào là `RequestContract.source_invariants` — `SourceInvariant` do
`scale_normalization.bat_bien_nguon` phát **từ chính câu văn của đề** (`AB = a`
→ `points=("A","B")`, `expected="1"`), KHÔNG suy từ `fact_id` (thứ lượt
`analyze` tự đặt tên). Cổng **không đọc** `source_fact_id` của chương trình để
quyết định có kiểm hay không — đó là toàn bộ điểm của nó; provenance chỉ dùng
khi viết lời giải thích.

So bằng **bình phương**: `distance_sq(A,B) == q²`, `Fraction` toàn đường. Khai
căn thì mọi đoạn dài vô tỉ thành không-kiểm-được — tức mất phép kiểm ở đúng
những bài phổ biến nhất. Tên điểm hoà giải qua `ten_da_hoa_giai` của C₁a.
`violated` tách hẳn `not_checkable` (§4). Test:
`tests/geometry/test_source_invariant_gate.py` (A–L, 21 ca).

### `backend/app/simulation/semantic_program/section_provenance.py` (2026-09-20) · offline · **0 API call**

**`normalize_section_provenance`** · **`chan_doan_chuan_hoa`** · **`CANONICAL_SECTION_KIND`** (`section`) ·
**`NORMALIZATION_VERSION`** (`section-provenance/1`) · **`TRANG_THAI`** · **`MA_LY_DO`** ·
**`NghiaVuTrucQuan`**-tương đương `HangChuanHoa`/`KetQuaChuanHoa`.

`SECTION_PROVENANCE_NORMALIZATION`. HAI tầng trả lời khác nhau cho câu *"vật này có phải thiết diện
không"*: tầng nghĩa vụ theo QUAN HỆ SEMANTIC (`OBLIGATION_KINDS['section_matches']` nhận cả `polygon3`),
tầng cảnh + frontend theo PHÉP DỰNG (`type === "section"`). Module này bắc cầu — nhưng chỉ khi CÓ BẰNG CHỨNG.

Luật: `section_matches` có `params.solid` → `Polyhedron` và `params.plane` → `Plane3` giải được, và
`same_section_cycle(poly, cross_section(solid, plane).polygon)` ⇒ mới chuẩn hoá. Thẩm quyền hình học là
ĐÚNG hai hàm `check_section_matches` dùng — không cài lại.

⚠️ **KHÔNG import `scene3d`** (nhận cảnh dạng `dict`). **Giữ nguyên** `producer`/`depends`/`sources`/
`origin`; nguồn plane–solid đi ở trường RIÊNG `section_source`. **KHÔNG bịa `steps`** — frontend có nhánh
dự phòng. Bí danh xử lý bằng so GIÁ TRỊ bộ nhớ ⇒ đúng ở mọi độ sâu `assign`. Mâu thuẫn nguồn ⇒
`AMBIGUOUS_SECTION_SOURCE`, không "ai đến trước thắng".

### `backend/tests/semantic_program/test_section_provenance_normalization.py` (2026-09-20) · offline

29 test. ⚠️ `test_B_da_giac_KHAC_khong_bi_keo_theo_khi_CO_mot_thiet_dien_hop_le` sinh ra vì phép tiêm G2
(promote MỌI `polygon3`) **không bắt được gì**: test "đa giác thường" cũ chạy trên hợp đồng không có
`section_matches` nên nhánh chuẩn hoá chưa từng chạy.

### `backend/app/simulation/semantic_program/visual_obligations.py` (2026-09-20) · offline · **0 API call**

**`check_visual_obligations`** · **`ap_dung`** · **`chan_doan_truc_quan`** · **`kieu_canh_yeu_cau`** ·
**`suy_nghia_vu_truc_quan`** · **`NghiaVuTrucQuan`** · **`KetQuaTrucQuan`** · **`DIAGNOSTIC_VERSION`**
(`visual-obligation-coverage/1`) · **`ROUTE_STAGE`** (`visual_coverage`) · từ vựng đóng **`TRANG_THAI`** ·
**`MA_LY_DO`** · **`LOAI_TRUC_QUAN`** · **`KIEU_CANH_HOP_LE`**.

`SYNTHESIS_VISUAL_OBLIGATION_COVERAGE_GATE`. Câu hỏi KHÔNG cổng nào đang hỏi: *vật mà đề bảo VẼ có nằm
trong cảnh không*. B02 (2026-09-15) được `served` với ba đáp số ĐÚNG mà cảnh 0 vật `section`.

Mỗi nghĩa vụ hợp đồng → một nghĩa vụ TRỰC QUAN; `required_scene_kind` **dẫn xuất** từ `OBLIGATION_KINDS`
(nên mở một lượng đo cho kiểu mới là cổng tự nhận). `section_matches` ⇒ đúng `{section}` — CHẶT hơn tầng
kiểu hợp đồng (vốn nhận cả `polygon3`) vì frontend chỉ nhận `type === "section"`. Thứ tự kiểm: MISSING →
TYPE_MISMATCH → PROVENANCE_MISSING → UNVERIFIABLE → TOPOLOGY_MISMATCH → COVERED.

⚠️ **KHÔNG import `scene3d`** — nhận cảnh dạng `dict` thuần làm tham số, nên
`test_KHONG_module_nao_o_TANG_DUOI_nhap_scene3d` vẫn xanh. `KIEU_CANH_HOP_LE` là bản CHÉP của
`scene3d.RENDER_HINT`; sync-lock ở `test_visual_obligation_gate.py::test_KIEU_CANH_HOP_LE_khop_RENDER_HINT…`
(đã đỏ thật ngay lần chạy đầu và bắt được bảng chép thiếu `vector3`).

⚠️ **Xuất xứ KHÔNG chỉ là `producer`**: vật bí danh do `assign` không có `producer` nhưng có `depends`;
điểm do ĐỀ CHO mang `origin="free"`. Hỏi đúng `producer` đánh trượt p4/p5 — hai ca HỢP LỆ (đã đo, đã sửa).
Topology hỏi `geometry.predicates.coplanar` + `geometry.exact.points_of`, không cài lại.

### `backend/tests/semantic_program/test_visual_obligation_gate.py` (2026-09-20) · offline

35 test. Gồm hai test đi qua **đường chạy thật** (`run_pipeline`, 0 mạng) — sinh ra vì phép tiêm lỗi F1
(tháo lời gọi cổng khỏi `pipeline`) **không bắt được gì**: mọi test khác gọi `ap_dung` trực tiếp nên chứng
minh cổng ĐÚNG chứ không chứng minh cổng ĐƯỢC GỌI.

### `backend/app/simulation/semantic_program/coverage_gate.py`

**`TrangThaiNghiaVu`** · **`CoverageResult.trang_thai_nghia_vu`** · **`dau_van_nghia_vu`** ·
**`chan_doan_phu_cau_truc`** (thêm `SYNTHESIS_STRUCTURAL_COVERAGE_REJECTION_DIAGNOSIS`, 2026-09-15) —
`check_structural_coverage` ghi, NGAY TẠI mỗi nhánh quyết, một hàng cho MỖI nghĩa vụ: chỉ số nguồn
(`enumerate(contract.obligations)`), vân tay (16 hex SHA-256 của JSON chính tắc), loại gốc và chính tắc,
`MemoryType` của chủ thể, `COVERED`/`UNCOVERED`/`NOT_EVALUATED`, mã lý do `LY_DO_PHU` (MỘT nhánh MỘT mã — tách ba
nhánh cùng mang `RANG_BUOC_THIEU` và hai nhánh bác không có `chan_doan`), loại/số bằng chứng `BANG_CHUNG_PHU` (gồm
`WITNESS_RESOLUTION_<trạng thái phan_giai_witness>`). `chan_doan_phu_cau_truc` dựng chẩn đoán với con trỏ RFC 6901
TỰ KIỂM trên `contract.model_dump(mode="json")` — vân tay không khớp ⇒ `null`/`AMBIGUOUS`. Không tên, không giá
trị; `missing`/`chan_doan`/phán quyết giữ nguyên từng byte. `route` gắn nó vào `SemanticRouteOutcome.coverage_diagnostic`
CHỈ ở nhánh bác C₁a; `pipeline` phát khoá ấy trong sự kiện `semantic_route` chỉ khi có. Khoá:
`tests/geometry/test_structural_coverage_diagnostic.py`.

**`phan_giai_witness`** + **`WitnessDaPhanGiai`** (thêm
`CURVED_DISTANCE_WITNESS_VERIFICATION`, 2026-09-05) — nghĩa vụ → `params.witness`
→ **câu lệnh sinh ra witness** → toán hạng thật. Tám bước, mỗi bước một trạng
thái chẩn đoán; chữ ký toán hạng đọc từ `BANG_PHEP_DO.hai_toan_hang`, quy đổi
nghĩa vụ đọc từ `nghia_vu_chinh_tac`. **`postconditions` import CHÍNH hàm này**
— hai bản phân giải khác nhau sẽ làm hai cổng nói hai điều khác nhau về cùng
một nghĩa vụ (khoá bởi `test_P7`, quét AST).

⚠️ **Bằng chứng liên kết là `_phu_thuoc`, không phải tên biến.** `c7a` đo
`l = measure(distance, of=T, wrt=A)` cho nghĩa vụ `distance(hinh_non)`; `T`,`A`
là toán hạng dựng của khối, nên `{T,A} ⊆ _phu_thuoc["hinh_non"]`. Chấp nhận
**mọi** distance witness thì một phép đo giữa hai điểm rời khối cũng "chứng
thực" được đường sinh — `test_F8` là phản ví dụ ấy.

⚠️ **Ba chỗ dùng resolver đều đòi `len(operands) > 1`.** Với phép đo MỘT toán
hạng thì `of` chính là container, nên nhận ở đó sẽ vô hiệu hoá đúng phép kiểm
kiểu — đo được ở `test_15b`.

⚠️ **`_theo_witness_do` THU HẸP cùng wave**: chỉ phép đo một toán hạng mới đồng
nhất `container ≡ of`. Với phép đo quan hệ, bí danh ấy rò sang nghĩa vụ anh em
và làm `volume(hinh_non)` bị chấm trên một ĐIỂM. · offline

Sở hữu **C₁a** (structural, trước execution) và **C₁b** (realized, sau execution).
C₁a hỏi "có witness hợp lệ không", C₁b hỏi "witness có THẬT SỰ được tạo ra không"
— hai câu khác nhau, và ví dụ tách chúng là `assign` nằm trong nhánh chết.

**Bảng vật của chương trình DẪN TỪ `ir_static_check`, không đọc
`memory_declarations`** (`OBLIGATION_BINDING_CONTRACT`, 2026-09-04). Ba bản chép
tay từng nói ba điều khác nhau về cùng một chương trình: `declared` bỏ sót MỌI
vật dựng bằng `construct_*` mà mô hình không khai; `_producers` và `_phu_thuoc`
liệt kê sáu `construct_*` và bỏ sót `construct_curved_solid`. Nay cả ba dẫn từ
`bang_ky_hieu` / `_KIEU_DUNG` / `_TOAN_HANG_LENH`.

**Net ⓪ `_theo_witness_do` — nối nghĩa vụ với vật qua WITNESS**, chạy trước ba
lưới tên của `domain_profile` vì nó suy từ CẤU TRÚC chứ không từ chính tả. Chỉ
chạy khi `container` CÓ mặt nhưng SAI KIỂU (vật dẫn xuất đề không đặt tên, vd
mặt cầu ngoại tiếp); container vắng mặt thì KHÔNG — nới ở đó là nhận một
chương trình dựng hình chóp cho đề hỏi lăng trụ. Nhiều ứng viên ⇒ fail closed.

**`ChanDoanNghiaVu` + `LY_DO_CHAN_DOAN`** — bốn mã máy đọc được
(`THIEU_KHAI_BAO` · `KIEU_KHONG_HOP` · `RANG_BUOC_THIEU` · `RANG_BUOC_MO_HO`)
đi kèm `missing`, ra tới `SemanticRouteOutcome.chan_doan_nghia_vu`. Phân loại
bằng chuỗi tiếng Việt là thứ `sua_duoc` đã phải bỏ.

### `backend/app/simulation/semantic_program/grounding_gate.py` · offline

Sở hữu **P2** của chuỗi provenance: mọi `initial_value` không phải HẠT KHỞI TẠO
phải tham chiếu **đúng mục** trong `RequestContract`. Kiểm THAM CHIẾU, không
tìm-theo-giá-trị. Giới hạn P1 khai ở `docs/evaluation/semantic-benchmark/P1_LIMITATION.md`.

Từ Wave 2 (2026-08-25) có **kênh thứ hai**: `model_assumption` — giả thiết mô
hình hoá, cho toạ độ mà chính người giải tự chọn khi đặt hệ trục. Đây KHÔNG phải
nới cổng: nó opt-in, chỉ nhận `point3`/`vector3`, **không bao giờ** nhận biến là
witness của một nghĩa vụ (`MODEL_ASSUMPTION_IS_ANSWER`), đòi lý do viết ra, và
`source_fact_id` vẫn thắng khi khai cả hai. Giả thiết được chấp nhận nằm ở
`GroundingResult.assumptions` để **đếm được**. Vì sao cần: Phase 5 cho thấy 5/10
bài hình học chết ở cổng này trong khi prompt *bảo* mô hình tự đặt hệ toạ độ —
hợp đồng mâu thuẫn với prompt, không phải mô hình sai.

Wave 3 (2026-08-25) nới thêm **hai bậc, đều tất định**. ① `fact_noi_long` khớp
`source_fact_id` sau chuẩn hoá (`CANH-DAY` ≡ `cạnh_đáy`) — không đoán nghĩa.
② Trích dẫn **không giải được** thôi chí mạng **nếu** khai báo đã tự đứng vững
bằng kênh giả thiết; id ấy hạ xuống `unresolved_citations`, ghi lại chứ không
giết. Nguồn: Phase 5 lượt 2 — mô hình khai `model_assumption` ĐÚNG rồi gắn
*thêm* `source_fact_id`, và luật "`source_fact_id` vẫn thắng" phạt nó vì đã nói
nhiều thông tin hơn. **Cố ý KHÔNG** khớp theo `semantic_type`/`entities`: cả hai
phía phép khớp ấy đều do cùng một model đặt tên, và một `float` giữ `2/3` sẽ
khớp fact `semantic_type: volume` — mở thẳng đường tuồn đáp án.

Wave 4 (2026-08-25) thêm **GIẢ THIẾT TOẠ ĐỘ**: với `point3`/`vector3` **không
phải witness**, `source_fact_id` là *chỉ dẫn xuất xứ* chứ không phải hợp đồng
giá trị — nguyên tử `0` bỏ qua (số không cấu trúc của hệ trục), fact **không
chứa số nào** (mệnh đề quan hệ) chấp nhận và ghi quan trắc, còn mọi nguyên tử
khác 0 vẫn phải khớp. Nguồn: Phase 5.5 đo 5/10 bài chết vì P2 đòi `0` trong
`(1,0,0)` phải truy về mục `canh_day`. Điều kiện dựa trên **kiểu**, không dựa
trên việc model có nhớ khai `model_assumption` — bắt phép kiểm phụ thuộc trí nhớ
của model là đo trí nhớ chứ không đo tính có căn cứ. R0 giữ bằng khoá witness.

Wave 5 (2026-08-29) thêm **PHÉP ĐẾM BIỆN MINH**, không thêm luật gác cửa. Ba lớp
`A` tự do hệ trục · `B` ghim về nguồn · `C` hiện thực mô hình theo dữ kiện quan
hệ; không lớp nào ⇒ từ chối (đúng như trước). Mới là hai danh sách
`justified_literals` / `unjustified_literals` (khuôn `tên|kiểu|lớp|lý do`) và
`ti_le_literal_hinh_hoc()` — nguồn DUY NHẤT của
`JUSTIFIED_GEOMETRY_LITERAL_RATE`; bộ đo **hỏi** hàm này chứ không tự định
nghĩa "biện minh" lần thứ hai. Bất biến *"mọi đỉnh dẫn xuất phải do primitive
dựng"* đã bị **bác bỏ**: IR không có tịnh tiến/hoàn thành hình bình hành, nên nó
sẽ buộc `unsupported` gần hết bài hình lập phương.

Wave J (2026-08-31) thêm **CỔNG TRUNG THỰC NĂNG LỰC** — hai mã, cùng một bệnh:

- `UNANCHORED_DERIVED_ASSUMPTION` — thực thể **tự bịa**. `gm_10` khai
  `P_opposite=[2,2,2]` kèm giả thiết, `midpoint` biến nó thành tâm mặt cầu,
  `distance` ra `√3` **đúng** — cho một khái niệm runtime KHÔNG có. Bốn phép
  kiểm Wave 2 hỏi *giả thiết khai đúng cách chưa*; không phép nào hỏi *thứ được
  khai có trong đề không*.
- `DERIVED_ENTITY_WITHOUT_PRODUCER` — thực thể đề **có nêu nhưng là hệ quả**.
  *"Gọi H là hình chiếu…"* ⇒ `H` có trong đề nên mã trên không áp được, mà khai
  `H=[0,0,0]` vẫn là giấu một phép dựng vào một con số.

Chốt đứng ở **hai** nhánh giả thiết: nhánh không có `fid`, VÀ nhánh hạ cấp khi
`fid` không giải được — thiếu nhánh sau thì gắn thêm một `source_fact_id` bịa là
lách qua, cửa sau rộng bằng chính cổng (khoá:
`test_gan_them_source_fact_id_bia_KHONG_lach_duoc`). Thẩm quyền tên nguồn ở
`source_entities.py`. Ranh giới giữ đúng chỗ khó: chọn hệ trục cho đỉnh đề cho
vẫn QUA — cấm nó là giết mọi bài hình học.

### `backend/app/simulation/semantic_program/source_entities.py` · offline

Sở hữu câu hỏi **"cái tên này có trong đề, và đề nói nó là gì"** — thẩm quyền
duy nhất cho hai chốt trung thực năng lực của `grounding_gate`.

`nhan_hinh_hoc(de)` tách nhãn viết gộp: `S.ABCD` → `{S,A,B,C,D}`,
`ABCD.A'B'C'D'` → tám đỉnh. `nhan_suy_ra(de)` trả nhãn mà đề GIỚI THIỆU như hệ
quả (*"Gọi M, N lần lượt là…"*, *"H là hình chiếu"*) — một nhãn ở cả hai tập thì
nó là hệ quả, vì đề đã tự nói. `chuan_hoa_ten` bắc cầu thói quen đặt tên của
model sang thói quen của đề (`point_A`→`A`, `A_prime`→`A'`). `la_ten_nguon` /
`la_ten_suy_ra` là hai vị từ mà cổng gọi.

**Vì sao trích từ ĐỀ, không đoán theo hình dạng tên:** luật "một chữ in hoa thì
là đỉnh" cho `X`, `H`, `O`, `T1` đi qua — đúng những tên mà một lượt rửa năng
lực đổi sang là lách được. Bẫy đã cắn một lần: `Tính` cho ra nhãn `T` vì `í`
không thuộc lớp ký tự nhãn, nên một điểm tên `T` neo được vào chính chữ "Tính"
trong đề. Đề rỗng ⇒ `la_ten_nguon` trả `True` ("chưa kiểm được", cùng quy ước
`provenance="unchecked"`), KHÔNG phải `False`. Giới hạn: khớp mẫu chữ, không
phân tích cú pháp.

Cùng wave, `co_so` hỏi `la_so_huu_ti` thay cho `isinstance(int|float)`: sau chuẩn
hoá thang mục giữ `'4/5'` — một CON SỐ viết chính xác — và hỏi bằng `isinstance`
thì nó đọc ra "fact quan hệ" rồi cho qua mọi toạ độ ghim vào đó.

### `frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx` — XƯỞNG

⚠️ Bố cục ĐÃ THAY (2026-08-30). Bản trước là *một mục có khung 3D đính kèm*:
tiêu đề `<h3>`, đoạn dẫn ba dòng, rồi khung hình bị bóp còn hai phần ba vì một
bảng danh sách luôn mở nằm cạnh. Nay là **xưởng**: khung 3D chiếm gần trọn bề
rộng (đo được 1068px, trước là 732px), và mọi bảng là **lớp phủ neo tuyệt đối
vào sân khấu** nên mở bảng KHÔNG bóp hình lại.

Ba lớp phủ, tất cả gọi theo nhu cầu: `geo3d-ngan` (cây thành phần · đề bài) ·
`geo3d-soi` (ô soi, chỉ khi đang chọn) · `geo3d-noi` (nút nổi góc trái).
Ba `useState`, nhưng **chỉ một** giữ *đang chọn cái gì* — hai cái kia giữ
*bảng nào đang mở* và *có bật Chi tiết không*. Test đếm
`useState<InteractionState>`, KHÔNG đếm `useState`: ràng buộc là một thẩm
quyền CHỌN, không phải một state duy nhất.

`moTaNgan` dịch `producer` sang tiếng học sinh (`construct_point.midpoint` →
*"Trung điểm của S, A"*) — DESIGN_BRIEF §3.4. Metadata kỹ thuật (`producer`,
`depends`, `source`, `type`) chỉ hiện sau nút «Chi tiết»; chế độ ấy không giấu
dữ liệu khỏi model, nó chỉ quyết định ai được mời đọc.

⚠️ `withSubEntities` là BẮT BUỘC ở đây. Một bản viết lại từng bỏ sót nó và mất
sạch mặt/cạnh — cây mất hai hạng mục, raycast chỉ còn trúng khối. Test bắt được.

Nhãn điểm vẽ bằng DOM chồng lên canvas (`.geo3d-labels`, `pointer-events:none`
— bắt chuột thì chữ "B" nuốt đúng cú bấm vào điểm B), chiếu mỗi khung bằng
`cam.project` trong vòng vẽ chứ không qua state React.

### `frontend/src/simulations/domains/geometry/scene3d-edge-visibility.ts` · offline

Chủ sở hữu duy nhất của phép phân loại cạnh theo camera cho Scene3D: dựng pháp
tuyến mặt trong world-space, xác định mặt hướng camera, rồi chia cạnh topology
thành `visible` hoặc `hidden`. Hàm thuần, không import renderer, để policy nét
liền/nét đứt được unit-test độc lập và được tính lại sau mỗi lần orbit.

### `frontend/src/components/ErrorBoundary.tsx` · offline

LƯỚI CHẶN NGOẠI LỆ BẤT NGỜ — `ErrorBoundary` (lớp) + `ErrorFallback` (bề mặt
phục hồi). Đặt **hai mức** ở `App.tsx`: lưới TRONG bọc `<main>` (giữ được thanh
điều hướng và cột trái vì chúng nằm ngoài), lưới NGOÀI bọc cả `App` ở `main.tsx`
(lưới cuối cho vỏ; chỉ một câu và nút tải lại — nó không giữ được điều hướng vì
điều hướng chính là thứ vừa vỡ).

⚠️ Đặt hẹp hơn KHÔNG giữ thêm được gì: với bài hình học `Scene3DExplorer` chính
là cả bề mặt workspace (đề bài truyền vào trong nó), nên bọc riêng khung 3D vẫn
mất đề bài.

`resetKey` dẫn từ bài đang mở — thiếu nó thì `hasError` dính vĩnh viễn và bài
mới bị fallback của bài cũ chặn. Dùng `getDerivedStateFromProps` chứ không
`componentDidUpdate`: nó chạy TRƯỚC lượt dựng lại.

⚠️ **KHÔNG bắt**: ngoại lệ trong trình xử lý sự kiện · promise bị từ chối ·
`setTimeout`/`requestAnimationFrame` (kể cả vòng vẽ Three.js) · lỗi ném từ chính
fallback. Nói *"đã chặn mọi lỗi frontend"* là sai — phân loại đầy đủ ở
`docs/REACT_ERROR_BOUNDARY_HARDENING.md`.

Lỗi MIỀN (từ chối, ngoài phạm vi, không dựng được) **không** đi qua đây: chúng
là kết quả hợp lệ, có bề mặt riêng, và không ném.

### `frontend/src/simulations/domains/geometry/semantic-dumb-frontend.test.ts` · offline
KHOÁ KIẾN TRÚC, không phải test thường: **chỉ backend được dịch ngữ nghĩa hình
học sang tiếng người học**. Quét mọi `.ts/.tsx` không-test dưới `domains/geometry`
và `components/`, bỏ chú thích, rồi bắt hai dấu vết của việc dịch — một định danh
máy (`construct_*`, `measure.*`, tên `MemoryType`…) nằm cùng dòng với một chuỗi
có dấu tiếng Việt · `producer` dùng làm khoá tra bảng hoặc đem so với hằng chuỗi.
⚠️ Guard khoá **bất biến, không khoá tên biến**: đổi tên `TU_PHEP_DUNG` thành thứ
khác vẫn đỏ. Có ca đối chứng giữ lại từ vựng giao diện (*"Dựa trên"*, *"Xem cấu
tạo"*) để guard không thoái hoá thành bộ lọc chính tả.
Đã chứng minh bằng tiêm lỗi giả: thêm một bảng `{"construct_point.midpoint":
"Trung điểm của"}` làm nó ĐỎ ngay.

### `frontend/src/simulations/domains/geometry/scene3d-presentation.ts` · offline

Sở hữu **ba quyết định TRÌNH BÀY** của khung 3D, tách khỏi `scene3d-view` để
kiểm được bằng test thuần. Exports: `kyHieuNgan` · `laVectoDangDiem` ·
`veTrenKhung` · `uuTienNhan` · `NGUONG_CHONG_NHAN` · `locNhanChongNhau`.

**① Nhãn mặc định là KÝ HIỆU, không phải câu.** `label` do tầng sinh cảnh viết
là câu mô tả (*"Hình chiếu vuông góc H của I lên mặt phẳng (SBC)"*); in nó cạnh
một chấm thì bốn vật đã phủ kín hình — ảnh chụp thật cho thấy chúng chồng nhau
rồi chạy ra ngoài mép. `kyHieuNgan` rút ký hiệu từ `label`/`id` (`X_prime` →
`X′`). Câu mô tả chuyển sang ô soi và cây; **không mất thông tin, đổi chỗ**.

**② Vectơ KHÔNG được vẽ như một điểm.** Tầng sinh cảnh phát vectơ với
`type:"point3"`, `render:"point_marker"`, còn `xyz` là **thành phần vectơ** chứ
không phải toạ độ một điểm của hình — nên `vector_AA_prime` hiện thành một chấm
đỏ ở (1,1,3), nơi không có điểm nào. `laVectoDangDiem` nhận diện qua `producer`
và `veTrenKhung` loại nó khỏi khung mặc định; nó **vẫn** nằm trong cây và ô soi.
⚠ Không vẽ thành mũi tên: thêm loại vẽ mới là đổi `RENDER_KINDS`, vốn khoá đồng
bộ hai chiều với backend (`test_scene3d_ts_sync.py`); còn dựng mũi tên từ
`depends` là renderer TỰ SUY vị trí — đúng thứ R0 cấm.

**③ Nhãn chồng nhau thì ẩn cái ưu tiên thấp hơn.** `locNhanChongNhau` xếp theo
`uuTienNhan` (đang chọn > dẫn xuất > gốc) rồi giữ nhãn nào không đè lên nhãn đã
giữ. **Không xê dịch nhãn** — xê dịch làm nhãn rời khỏi vật nó gọi tên.
Lọc chạy trong vòng vẽ vì hai nhãn có chồng nhau hay không phụ thuộc GÓC NHÌN.

Test: `scene3d.test.tsx` (5D) — khoá nó không nhập `three` và không nhắc một
phép hình học nào.

### `frontend/src/simulations/domains/geometry/scene3d-camera.ts` · offline

Sở hữu **KHUNG NHÌN tính từ hộp bao**. Exports: `HopBao` · `KhungNhin` ·
`hopBaoCuaDiem` · `khungNhinVua` · `huongNhin` · `phuongViCuaPhapTuyen` ·
`PHUONG_VI_DO` · `DO_CAO_DO`.

Vì sao tồn tại: bản trước đặt camera bằng một hằng số (`position.set(6,5,8)`)
cho mọi bài, nên bài toạ độ nhỏ thì hình nằm một góc, bài toạ độ lớn thì tràn
ra ngoài — ảnh chụp thật dính cả hai kiểu.

⚠ **VIẾT LẠI 2026-09-11** (`SCENE3D_VISUAL_LANGUAGE_IMPLEMENTATION`). Bản ôm
**cầu ngoại tiếp** + hướng nhìn `[6,5,8]` trong hệ three.js đã bị đo là **0/7
ca đạt**; bản này **7/7**. Hai điều đổi, cả hai đều là quyết định TRÌNH BÀY:

- **fit theo HÌNH CHIẾU của tám đỉnh hộp bao**, không theo cầu ngoại tiếp. Cầu
  lớn hơn hình: lấp 68% khung thì hình thật chỉ lấp `0,68/√3 ≈ 39%` chiều —
  đo được occupancy 0,29–0,47 trên bảy ca. Nay `TI_LE_LAP_KHUNG = 0.66` áp
  thẳng lên hình chiếu, đo lại 0,66–0,685.
- **`up` = trục z CỦA HÌNH HỌC** (`KhungNhin.huongLen`), không phải y của
  three.js. Toạ độ bài toán dùng z làm chiều cao và `toVec3` là ánh xạ đồng
  nhất, nên `up = (0,1,0)` làm **mọi khối nằm nghiêng**; khối chóp `p1` đọc ra
  một tứ giác dẹt. Nơi gọi phải `cam.up.set(...kn.huongLen)` TRƯỚC `update()`.

Tham số thứ tư `phuongViDo` cho phép ghi đè phương vị — dùng cho GUARD thiết
diện bẹp ở `scene3d-view.tsx`. Bỏ trống thì lấy `PHUONG_VI_DO = -55`
(`DO_CAO_DO = 22`).

⚠ **Trả `null` thay vì `NaN`** khi đầu vào hỏng, để nơi gọi GIỮ NGUYÊN khung
nhìn thay vì nhảy tới một chỗ vô nghĩa. Có test khoá cả ca hộp bao suy biến về
một điểm.

⚠ **Không gọi khi đổi bước.** `scene3d-view` chỉ gọi ở ba dịp — nạp cảnh khác,
người dùng bấm xem lại toàn hình (`fitToken`), tách/ráp khối — vì đặt lại khung
nhìn ở mỗi bước biến việc tua bước thành việc đổi góc máy, và hai hình so sánh
bước 5 với bước 12 chỉ có nghĩa khi camera đứng yên.

### `frontend/src/simulations/domains/geometry/pick-target.ts` · offline

Sở hữu **ĐÍCH BẤM** — tách *cỡ nhìn* khỏi *cỡ bấm*. `BAN_KINH_NHIN` (0.09,
giữ nguyên) · `DICH_DIEM_PX`/`DICH_CANH_PX` (12/8 px) · `nguongBam` ·
`banKinhBamDiem` · `nguongBamCanh` · `HANG_CU_THE`/`hangCuThe`.

Vì sao tồn tại, đo bằng lưới 625 điểm ảnh trong Chrome thật: mặt trúng 26 lần,
đường thẳng 10, đa giác 7 — **điểm 0, cạnh 0**. Cơ chế chọn không hỏng (đường
thẳng `SA` cũng là `THREE.Line` mà trúng 10 lần); đích bấm quá nhỏ. Cách sửa
SAI là phóng to chấm: khi ấy một điểm hình học trông như quả cầu. Nên chấm
nhìn thấy giữ nguyên, còn `scene3d-view` bọc thêm một hình cầu **vô hình**
(`colorWrite:false` — `visible=false` KHÔNG dùng được vì `Raycaster` bỏ qua
vật vô hình).

Ngưỡng **dẫn từ khoảng cách camera**, không phải hằng số: `Raycaster` đo ở
không gian thế giới còn ngón tay đo bằng điểm ảnh, nên một ngưỡng vừa tay ở
góc nhìn mặc định thành hạt bụi khi phóng to. Dùng `cam.position.length()`,
KHÔNG dùng phép đo khoảng cách hình học nào (guard cấm ở tầng view). Cả hai
đầu vào fail-safe: hỏng ⇒ ngưỡng mặc định, vì `NaN` trong
`params.Line.threshold` làm raycast im lặng không trúng gì.

`HANG_CU_THE` xếp `điểm → cạnh → mặt → … → khối`; `chonCuThe` ở
`scene3d-view` dùng nó. An toàn vì một vật chỉ vào danh sách va chạm khi tia
THẬT SỰ trúng vùng bấm của nó — "ưu tiên điểm" không cướp được mặt ở xa con
trỏ. Test: `pick-target.test.ts` (A–K, 14 ca).

### `frontend/src/test-source.ts` · offline — ĐỒ NGHỀ CHO GUARD

`docMa(path)` trả nội dung file **đã bóc chú thích**; `maConDu` là phép kiểm
rỗng-là-hỏng đi kèm.

Tồn tại vì MỘT LỚP LỖI ĐÃ LẶP BỐN LẦN: guard *"file X không được chạm Y"* quét
thẳng file rồi ĐỎ vì chính **chú thích giải thích rằng nó không chạm Y** —
`scene3d-page.test.tsx`, `canvas-first-shell.test.tsx`,
`test_live_session_api.py`, `live-classroom.test.tsx`. Mỗi lần đều vá tại chỗ,
nên lần sau lại xảy ra.

⚠️ KHÔNG dùng khi thứ bị cấm không được xuất hiện **kể cả trong lời bàn** (ví
dụ một nguyên thuỷ chiếu màn hình): ở đó quét cả chú thích mới đúng.

### `frontend/src/components/LiveClassDock.tsx` · offline

Sở hữu **ba mảnh giao diện lớp trực tiếp**, đều THUẦN theo props (test SSR
được): `LiveClassDock` (giáo viên) · `StudentLiveIndicator` · `HelpRequestButton`.

Dock nằm TRONG thanh xưởng, **không nổi đè lên canvas**: bản mẫu tham khảo dùng
thanh nổi và phải dựng `ResizeObserver` đo chiều cao rồi cộng padding bù — mà
ảnh chụp vẫn cho thấy nó che đúng hàng nút học sinh cần bấm. Chiếm chỗ thật thì
không có gì để che.

KHÔNG nút giả: mỗi nút hoặc gọi thật một endpoint, hoặc `disabled` kèm `title`
nói vì sao. Không enum kỹ thuật lọt ra bề mặt học sinh (`follow`/`free`/
`cmd_id`) — chỉ "Đang theo cô/thầy" / "Em tự khám phá".

### `frontend/src/components/LiveClassStrip.tsx` · offline

BIÊN duy nhất nối tầng lớp học vào xưởng 3D: đọc `useClassroomStore`, phân vai
(giáo viên → dock, học sinh → chỉ báo + giơ tay), rồi trả xuống một mẩu JSX qua
prop `daiLop`. `Scene3DExplorer` vì thế **không bao giờ import store lớp học**.

`useTeacherStateReport` chặn bão HTTP: chữ ký + nhịp tối thiểu 700ms, chỉ gửi
khi TIÊU ĐIỂM thật sự đổi — một `STATE_UPDATE` mỗi khung hình lúc xoay hình
không phải đồng bộ, là bão.

### `frontend/src/components/MonitorView.tsx` · `MonitorRoute.tsx` · offline

Bảng **theo dõi lớp** — một TRANG riêng, không phải cột cạnh canvas: 32 học
sinh cạnh khung 3D thì cả hai đều không dùng được. `MonitorView` nhận
`classId`/`className` qua props (SSR test được); `MonitorRoute` là cầu nối đọc
store.

Không điểm, không đúng/sai, không "em này đang gặp khó khăn". Bộ lọc mang tên
TRUNG TÍNH — «Chưa hoạt động gần đây» mô tả một sự kiện quan sát được, còn
"đang gặp khó" là một phán quyết mà bảng này không có quyền. Giơ tay lên đầu
danh sách; sắp phần còn lại theo ĐỘ CŨ, không theo số lần bấm.

### `frontend/src/state/classroom-sync.ts` · offline · **0 gọi model**

Sở hữu **luật đồng bộ lớp học** dưới dạng HÀM THUẦN: `apDungPhien` ·
`nenGuiTienDo` · `NHIP_PHIEN_MS` · `NHIP_THEO_DOI_MS` · `CHUA_THAY`.

Ở hàm thuần chứ không trong store vì đây là luật dễ sai nhất của cả tính năng —
*khi nào trạng thái giáo viên được ghi đè lên thao tác học sinh* — và zustand
SSR luôn trả trạng thái đầu (`§8` #8) nên một test qua store xanh vì không có
gì xảy ra.

**BA nhánh, không phải hai.** BÁM THEO → lệnh mới nào cũng áp. TỰ DO → không
áp. GỌI VỀ (`syncCmdId` tăng) → áp ĐÚNG MỘT LẦN rồi trả lại tự do. Gộp "gọi
về" vào "bám theo" thì giáo viên phải đổi chế độ để gọi cả lớp, và quên bật
lại là cả lớp bị khoá mà không ai hiểu vì sao.

`seen.roundId` đặt lại mốc khi đổi tiết: không đặt lại thì một `cmdId` lớn của
tiết cũ nuốt mọi lệnh của tiết mới. Phiên `null` (hết tiết) KHÔNG hoàn nguyên
gì — kéo học sinh về một trạng thái "sạch" là xoá công của em ấy.
Test: `classroom-sync.test.ts` (17).

### `frontend/src/components/canvas-first-shell.test.tsx` · offline

Khoá luật **xưởng 3D KHÔNG có cột điều hướng thường trực**. Soi MÃ NGUỒN + CSS
chứ không render: `App` đọc zustand, mà SSR luôn trả trạng thái đầu (`§8` #8),
nên `renderToString(<App/>)` sau khi nạp envelope vẫn ra màn hình
chưa-đăng-nhập — mọi khẳng định "không chứa cột trái" sẽ xanh vì màn hình rỗng.

Bốn thứ khoá: vỏ rẽ nhánh theo `hopLeScene3D` (cảnh ĐÃ DỰNG) chứ không theo
`visual_mode` (được KHAI) · CSS thu cột về 0 · `:not(.is-drawer-open)` để ngăn
kéo vẫn thắng · xưởng có chip «Menu» làm đường ra. Cộng một phép kiểm HÀNH VI
trên bài mẫu thật. ⚠️ Guard bóc chú thích trước khi quét — chú thích giải thích
*"vì sao không dùng visual_mode"* khớp đúng mẫu cấm.

### `frontend/src/data/geometry-samples.ts` · offline · **0 API call**

Sở hữu **bài mẫu hình học chạy ngay**. Export `GEOMETRY_SAMPLES` ·
`geometrySampleById`. Đọc `geometry-samples.json` — file **SINH RA** bởi
`backend/scripts/build_geometry_samples.py`, **không sửa tay** (chạy lại là ghi
đè).

Vì sao tách khỏi `sim-samples.ts`: mẫu ở đó VIẾT TAY (`config: {inputA: 0}`),
còn ở đây `config.frames` do interpreter sinh và `scene3d` do **kernel** tính —
viết tay chúng là đặt toạ độ kết quả vào tay người, đúng thứ R0 cấm.

Ba bài phủ ba loại hoạt động trong phạm vi đề tài: dựng hình/thiết diện · quan
hệ song song–vuông góc · khoảng cách/thể tích/góc. Đáp án kiểm tay: thiết diện
4 đỉnh hình vuông cạnh 1 ở `z=2` · `sin² = 1` (BC ⊥ (SAB)) · `V = 16/3`, `d = 4`.

⚠️ Đây là lối vào **không-cần-AI** DUY NHẤT của miền hình học. Trước 2026-08-30
`SAMPLES` (17 bài Tin học) là toàn bộ đường ấy, nên mở app không có khoá API thì
không có bài hình học nào chạy được — kể cả để soát giao diện.

### `backend/scripts/build_geometry_samples.py` · offline · 0 API call

Bộ SINH bài mẫu trên. Chương trình dựng do NGƯỜI viết (như `oracle_result` của
tập DEV), nhưng **không một toạ độ kết quả nào** viết tay: đi đúng đường sản
phẩm đi — `compile_semantic_program_to_envelope` → `interpreter` →
`build_simulation_state` → `build_scene3d`. Dừng khi chương trình chạy không
trọn (`status != "completed"`) hoặc cảnh 3D rỗng.

### `frontend/src/simulations/domains/geometry/scene3d-subentities.ts` · offline

Sở hữu **THỰC THỂ CON THỊ GIÁC** — mặt và cạnh của một khối, dựng từ topology
`faces` đã có. `deriveVisualSubEntities` · `withSubEntities` · `faceId` ·
`edgeId` · `parentSolidOf` · `isSubEntity` · `faceLabel` · `entitiesPresentAt`.

Cộng **`canhThietDien(o)`** — thẩm quyền DUY NHẤT cho *"miếng cắt gồm những cạnh
nào, theo thứ tự nào"*: ưu tiên `o.steps` (có `face_index`), rơi về cạnh liên
tiếp của `polygon` khi thiếu. Cây phân rã và **renderer** đều gọi nó. Trước
2026-09-12 phép suy ấy nằm kín trong thân `deriveSectionSubEntities`, nên
renderer không với tới và đành dựng trọn `polygon` — bốn sự kiện `EXTEND` của
trace cho ra bốn khung hình trùng khít (xem `tienTrinhDung` ở `scene3d-model.ts`).

Vì sao cần: `solid` là **một** đối tượng mang `faces` là bảng chỉ số, nên học
sinh nhìn thấy bốn mặt mà không bấm được vào mặt nào. Đây là **dữ liệu nhìn**,
KHÔNG phải `GeometryState` thứ hai: không một toạ độ nào được TÍNH ở đây,
không `cross`, không pháp tuyến. Mặt giữ **id ĐIỂM NGỮ NGHĨA**, không giữ bản
sao toạ độ làm nguồn.

Phụ thuộc **`vertex_ids`** do backend phát: `faces[i][j]` là chỉ số vào
`vertices`, còn `depends` đã bị `dependency_graph` sắp theo thứ tự chữ nên vị
trí thứ `k` của nó không còn là đỉnh thứ `k`. Thiếu `vertex_ids`, lệch số
lượng, hoặc chỉ số mặt ngoài biên ⇒ **bỏ qua cả khối**, không sinh một phần:
cây thiếu vài mặt còn đọc được, cây có mặt gồm điểm sai thì nói dối về hình.
Cạnh khử trùng theo cặp **không hướng**. `entitiesPresentAt` cho mặt/cạnh xuất
hiện đúng lúc khối cha xuất hiện — chúng không có sự kiện riêng, và bịa một sự
kiện là dựng timeline thứ hai. Test: `scene3d-subentities.test.ts` (21 ca).

**THIẾT DIỆN — nhánh thứ hai, cố ý KHÔNG dùng chung với khối** (2026-08-30).
`deriveSectionSubEntities` · `sectionVertexId` · `sectionEdgeId` ·
`sectionFaceId` · `sectionDetails` · `sectionViewIds` · `sectionCycleLabel`.
Khối có `faces` là bảng chỉ số vào những điểm ĐÃ CÓ TÊN; thiết diện thì đỉnh là
**giao điểm mới do kernel tính**, thường không trùng đỉnh nào và không có tên
trong chương trình — nên ở đây không có `vertex_ids` để đọc, chỉ có `polygon`
(đã sắp) và `steps` (mỗi cạnh kèm `face_index`). Cạnh đi theo `steps` vì
`face_index` trả lời *"cạnh này nằm trên mặt nào của khối"*.

Tên đỉnh lấy bằng **trùng toạ độ CHÍNH XÁC** với một `point3` trong cảnh — đây
không phải suy đoán, toạ độ là chuỗi phân số đã tối giản nên `===` là mệnh đề
đúng-hoặc-sai. Hai điểm cùng toạ độ ⇒ **bỏ tên**, không chọn bừa.
`sectionCycleLabel` trả `null` khi còn một đỉnh chưa tên: `"MN-đỉnh 3-Q"` không
phải cách ai gọi một thiết diện. ⚠️ `_banDoDiem` phải **bỏ qua thực thể con** —
đỉnh thiết diện cũng là `point3` cùng toạ độ, tính cả chúng thì mọi đỉnh đều
"trùng hai điểm" và luật khử nhập nhằng xoá sạch mọi cái tên (đã xảy ra thật ở
lượt chạy đầu). `sectionDetails` tra khối/mặt phẳng theo **KIỂU** trong
`depends`, không theo vị trí — `depends` đã bị sắp theo thứ tự chữ.
Test: `scene3d-section.test.ts` (39 ca — 32 gốc + 7 của w15 về phần tô thiết diện khép
kín; cảnh là đầu ra THẬT của backend ở `scene3d-section-fixture.json` và fixture
`cross_section_positive.json` của run w14).

### `frontend/src/simulations/domains/geometry/Scene3DExplorer.tsx` · offline

Khối THĂM DÒ: cây phân rã + khung nhìn + ô soi + thao tác xem. Sở hữu **thẩm
quyền chọn DUY NHẤT** — đúng một `useState<InteractionState>`; cây và khung
nhìn cùng đọc `selected_id` và cùng báo về một hàm `chon`. Không
`treeSelected`/`viewportSelected` (có test khoá, và test ấy **bỏ chú thích
trước khi soi** vì docstring của chính file nhắc hai tên ấy để cấm chúng).

Cây dựng từ `semanticTree(withSubEntities(scene))`: mỗi KHỐI là một nút gốc,
dưới nó là hạng mục `Điểm · Cạnh · Mặt` (tiếng Việt — bề mặt học sinh không
nói tiếng máy). **Không dựng hạng mục rỗng.** Vật chưa dựng tới ở bước hiện
tại vẫn nằm trong cây nhưng **mờ và không bấm được**: giấu hẳn thì cây nhảy
chỗ mỗi bước, cho bấm thì học sinh chọn được một vật chưa tồn tại.
Không `fetch`, không LLM — có test quét cả ba file của cụm.
Test: `Scene3DExplorer.test.tsx` (SSR + hàm thuần; kho không có
`@testing-library/react`, xem `MANUAL_UI_DEMO` trong báo cáo wave).

### `frontend/src/simulations/domains/geometry/interaction-state.ts` · offline

Sở hữu **`InteractionState`** — CÁCH NHÌN, tách hẳn khỏi `GeometryState`.
Thuần, tất định, **0 lời gọi mạng/LLM** (không nhận `fetch`, không nhận client).

`selected_id · hidden_ids · isolated_ids · exploded_groups · transparent_ids ·
current_step`, cùng các phép thuần: `select`/`toggleSelect` ·
`hide`/`show`/`showAll` · `isolate`/`isolateGroup`/`clearIsolate` · `isVisible`
· `explode`/`collapse`/`collapseAll` + `visualTransformOf` ·
`directDependencies`/`dependencyClosure`/`highlightSet` · `setStep` ·
`semanticTree` · `serialize`/`deserialize`/`reset`.

**`directDependencies`/`dependencyClosure` đọc `objects[].depends` do backend
gửi**, KHÔNG dựng lại đồ thị bằng cách bóc chuỗi `producer` — dựng lại là đẻ
nguồn sự thật thứ hai. Hệ quả: chất lượng của chúng bằng đúng chất lượng của
`simulation_state.dependency_graph`. Đã đo được một lần: bộ lọc bên backend cắt
mất mọi cạnh trỏ tới vật DẪN XUẤT, và bấm vào đáp số `R` trả về **rỗng**
(`GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE`, 2026-09-04). Khoá bởi
`scene3d-causal-selection.test.ts` trên **cảnh thật** —
`scene3d-circumsphere-fixture.json`, đầu ra backend của ca `circumsphere`.
⚠️ Phân biệt hai đường: *tua* dùng `objectsAt`/`highlightedAt` (đọc `events`)
nên nó **chưa từng hỏng**; chỉ *chọn* đi qua `depends`.

**Bất biến quan trọng nhất**: bung hình chỉ sinh `visual_transform`, và
`visual_transform` không có mặt trong bất kỳ phép đo, checker hay bất biến
nào — toạ độ trong `Scene3D` nguyên vẹn sau khi bung. Test E khoá điều đó; nó
đỏ nghĩa là hiệu ứng nhìn đã rò vào toán học.

Hai chỗ dễ gộp nhầm, cố ý tách: **`hidden_ids` ≠ `isolated_ids`** (bỏ cô lập
không được hiện lại vật người dùng đã chủ động ẩn), và **`parent` ≠ `depends`**
(`M = midpoint(A,B)` phụ thuộc A, B nhưng không NẰM TRONG chúng).
`dependencyClosure` duyệt có `đã thăm` nên đồ thị có chu trình vẫn dừng.
Phát lại dùng `objectsAt`/`highlightedAt`/`narrationAt` của `scene3d-model`,
KHÔNG tự tính lại. Test: `interaction-state.test.ts` (A–L, 33 ca).

### `frontend/src/simulations/domains/geometry/scene3d-model.ts` · offline

Kiểu dữ liệu + phép chiếu **THUẦN** của cảnh 3D hình học: `Scene3D`,
`SceneObject`, `SceneEvent`, `RENDER_KINDS`, `toNumber`, `toVec3`, `objectsAt`,
`highlightedAt`, `narrationAt`, `stepCount`, `clampStep`, `tienTrinhDung`,
`vatToTrung`, và hai hằng trình bày `PLANE_DISPLAY_SIZE` /
`LINE_DISPLAY_HALF_LENGTH`.

**Dòng thời gian HÌNH HỌC (W12)** — `geometryTimeline(scene)` →
`GeometryStep[]`: một PHÂN HOẠCH liên tiếp của dãy sự kiện (cùng khuôn `pacer`,
bất biến #32); bước mới mở ở sự kiện `GEOMETRY_CONSTRUCTION` làm đổi chữ ký
hình (vật vẽ được + tiến độ thiết diện), `MEASUREMENT`/`EXPLANATION` vào
`solution`, `FINAL_RESULT` vào `results` của bước đang mở; khung hiện là
`anchor` = sự kiện cuối đoạn (bất biến #31 giữ nguyên). Loại đọc từ
`semantic_kind` có cấu trúc; cảnh không gõ loại ⇒ mỗi sự kiện một bước như cũ.
Điều hướng: `geometryStepCount`, `geometryStepOf`, `anchorOfGeometryStep`,
`geometryAnchor`, `nextGeometryStep`, `prevGeometryStep`, `isFirstGeometryStep`,
`isLastGeometryStep`; trình bày: `geometryFocusAt`, `geometryNarrationAt`,
`geometryHighlightedAt` (bước dựng cuối không tô). Lớp lời giải:
`geometryStepList(scene)` → `{index, anchor, label}[]` (regular-square-pyramid-w01): một mục mỗi bước dựng,
nhãn = `geometryActionLabelAt` ‖ lời kể ‖ "Dữ kiện đề cho" — nguồn của panel «Các bước dựng».
`quantityChoices(scene, step)` → `{results, steps, givens}` id đại lượng ở bước, bỏ dòng `same_as` trùng —
nguồn của ngăn «Đại lượng» (`Scene3DExplorer`, `ngan === "dai-luong"`).
`solutionAt(scene, step)` → `SolutionLayer {givens, steps, results}` gồm
`SolutionItem` (công thức chỉ khi có tham chiếu nhất quán, `basis` =
`numericalBasis`, đáp số ở `results` và không lặp ở `steps`). Test:
`scene3d-geometry-timeline.test.tsx` (sáu cảnh w11, kỳ vọng số bước từ phép đếm
độc lập).

⚠️ **`vatToTrung(objs)` trả về những vật KHÔNG được tô mảng nền, vì một vật
khác đã tô đúng khối ấy rồi.** Một trace hoàn toàn hợp lệ có thể mang hai vật
trùng khít: ca `p5` có cả `khối nón` (đỡ nghĩa vụ thể tích) lẫn `hình nón` (đỡ
nghĩa vụ diện tích xung quanh), cùng `radius_sq`/`height_sq`/`apex_or_top`; `p4`
cũng vậy. Mỗi vật tự tô một lớp 0,07 nên chỗ ấy nhận **hai lớp** và mảng tô đọc
ra đậm gấp đôi mockup (đo: mockup `rgb(234,233,231)`, sản phẩm `rgb(224,…)`).
Không sửa được bằng phép kiểm chiều sâu — hai mặt trùng khít có cùng độ sâu nên
mọi `depthFunc` đều cho cả hai qua; cũng không sửa ở backend — hai vật ấy là dữ
liệu đúng. Luật nằm ở tầng trình bày: **mảng tô là thuộc tính của KHỐI, không
phải của mỗi cái tên trỏ tới khối ấy.** Vật sau vẫn dựng đủ cạnh, đường bao và
lớp chiều sâu. Khoá bởi `scene3d-visual-language.test.tsx` (4 test, 4 phép tiêm
lỗi đã chứng).

⚠️ **`objectsAt` chỉ trả lời *"vật đã xuất hiện chưa"*, và câu ấy thiếu một
nửa.** `tienTrinhDung(scene, id, step)` là chỗ DUY NHẤT đọc `SceneEvent.action`:
nó đếm số sự kiện `EXTEND` đã xảy ra (`soCanh`, `null` khi vật không dựng luỹ
tiến) và cho biết sự kiện đóng hình `STEP` đã tới chưa (`daDong`). `EventAction`
khai `"EXTEND"` từ đầu nhưng tới 2026-09-12 mới có nơi đọc; trước đó thiết diện
hiện trọn ngay từ sự kiện đầu và năm bước cuối cho năm khung hình y hệt nhau.
Khoá bằng `scene3d-progressive-section.test.ts` (19 test, 3 phép tiêm lỗi).

**KHÔNG import `three`** — có test khoá (kiểm danh sách `from`, không kiểm chuỗi
thô: chữ `three` nằm trong văn xuôi docstring). Nhờ vậy *cái gì hiện ra ở bước
nào* kiểm được mà không cần WebGL, cùng khuôn `layerDepth`/`sideX` của
`network/encap-ui3d.tsx`.

`toNumber` là **chỗ DUY NHẤT** float xuất hiện trong toàn chuỗi — backend giữ
chuỗi phân số tới tận đây vì kernel so bằng đúng, không epsilon. Chuỗi hỏng
**NÉM** thay vì trả `NaN`: một `NaN` lọt vào buffer three.js làm cả mesh biến
mất không báo gì.

`objectsAt` tính từ `events` chứ **không** từ `objects`: `objects` là trạng thái
CUỐI, chiếu thẳng nó ra thì học sinh thấy ngay hình hoàn chỉnh và mục tiêu sư
phạm (*"hình được hình thành thế nào"*) biến mất.

### `frontend/src/simulations/domains/geometry/scene3d-zup-lifecycle.test.tsx` (2026-09-12) · offline

Khoá **VÒNG ĐỜI khởi tạo camera**: `cam.up.set(0, 0, 1)` phải chạy **trước**
`new OrbitControls(...)`, vì OrbitControls chụp `camera.up` ngay trong hàm dựng.
Đặt muộn hơn thì controls quay vị trí quanh Y trong khi camera dựng khung theo
Z — hợp của hai phép quay quanh hai trục không trùng nhau cho **trục đổi mỗi
khung** (`56350f7`: ‖trục‖ 0,59–0,66 thay vì 1,000).

Hai tầng, cố ý:

- **hành vi** — dựng camera + controls THẬT ở cả hai thứ tự rồi hỏi bằng API
  công khai `getPolarAngle()`: đặt camera tại `target + (0,0,10)`, trục quỹ đạo
  Z cho cực ≈ 0, trục Y cho cực ≈ π/2. Ba nền đỏ đi kèm.
- **ràng buộc vào sản phẩm** — đọc `scene3d-view.tsx` bằng **AST TypeScript**,
  không bằng `indexOf`: một phép so chuỗi vẫn xanh khi dòng ấy nằm trong chú
  thích hoặc một nhánh chết. Kiểm `.up.set` đúng một lần, đối số đúng `0, 0, 1`,
  đứng trước mọi `new OrbitControls`, và controls chỉ tạo một lần.

Ba phép tiêm đã chứng ĐỎ: bỏ hẳn dòng · chuyển xuống sau controls · đổi
`(0,1,0)`. Báo cáo: `docs/SCENE3D_MINIMAL_Z_UP_CAMERA_IMPLEMENTATION.md`.

### `frontend/src/simulations/domains/geometry/scene3d-view.tsx` · offline

Renderer 3D `display(scene, step)` bằng three.js + `OrbitControls`. Sở hữu
`Scene3DWorkspace`, `buildObject3D`, `tryCreateWebGLRenderer`,
`GEOMETRY_WEBGL_FALLBACK`, `matCatBet`.

⚠ **Sở hữu BẢNG MÀU `MAU` — ngôn ngữ hình học, duyệt 2026-09-11.** Luật: mỗi
màu MỘT vai, đọc được không cần chú giải. Bản trước gán màu theo *nguồn gốc*
vật (điểm tự do xanh, điểm dẫn xuất đỏ) — đúng kỹ thuật, vô nghĩa với người
học, và tiêu hai màu mạnh nhất cho thứ không ai hỏi. Nay: `mesh` cạnh thấy +
điểm `#1F1F1F` · `khuat` cạnh khuất `#7D7975` · `section` thiết diện `#D95A43`
· `line` đường dựng `#99948F` · `surface` mặt phẳng `#77736F` · `highlight`
`#0075DE`. `line` và `section` từng là MỘT màu — đó là lý do thiết diện của
`p3`/`p6` đọc ngang hàng với một đường phụ.

⚠ `duongHaiLuot` nay nhận **màu riêng cho phần khuất** (tham số thứ sáu). Cạnh
khối truyền `MAU.khuat`; thiết diện để trống ⇒ hai phần cùng màu, vì chúng là
MỘT vật ở hai trạng thái nhìn thấy. Và **thiết diện đa giác** (`o.type ===
"section"`) nay cũng đi hai lượt — trước đó nó là một `THREE.Line` liền, nên
cạnh sau của thiết diện `p1` hiện y hệt cạnh trước.

⚠ `matCatBet(n, phuongViDo)` — GUARD thiết diện bẹp. Phép so phải **ba chiều**
(`|d̂·n̂| < 0,15`), không phải hiệu phương vị: một ca tổng hợp có thiết diện
chiếu ra tỉ lệ trục **0** mà hiệu phương vị là 125°, nên lối so phương vị bỏ
lọt nó. Khoá bởi `scene3d-visual-language.test.tsx`.

Cùng hợp đồng `network/encap-ui3d.tsx`: KHÔNG engine thứ hai, KHÔNG tính lại,
mesh/camera/vật liệu **renderer-owned** (ref/closure), không vào store.

⚠️ **Không suy luận hình học** — có test cấm `.cross(` `.dot(` `intersect`
`Raycaster` `distanceTo` `angleTo`. Mặt phẳng vô hạn được vẽ bằng cách đặt một
`PlaneGeometry` cỡ cố định tại `point` rồi xoay theo `normal` bằng
`setFromUnitVectors` — pháp tuyến là **dữ liệu đã có**, xoay theo nó là dùng thư
viện chứ không phải suy ra mặt phẳng từ ba điểm.

⚠️ **Không phải GeoGebra**: test cấm `<button` `<input` `<select`
`DragControls` `TransformControls`. Hình ở đây **không dựng được bằng chuột** —
nó chỉ đến từ một chương trình đã qua thẩm định. Người học điều khiển **thời
gian** (bước dựng) và **góc nhìn**, không phải nội dung hình.

`readout` trả `null` có chủ đích: đại lượng đo được không có vị trí hình học,
nên nó hiện ở bảng chữ bên cạnh chứ không phải một nhãn lơ lửng trong khung 3D.

### `frontend/src/simulations/domains/geometry/polygon-triangulate.ts` · offline

Chia tam giác một đa giác **phẳng ĐƠN** trong không gian — **kể cả LÕM**. Sở
hữu `chiaTamGiac(pts) → [i,j,k][]`, `dienTichCoDau(xy)` (shoelace) và kiểu
`Diem3`. Cắt tai (ear clipping) trên một hệ trục 2D cục bộ của mặt phẳng chứa
đa giác. Người dùng duy nhất: `scene3d-view.tsx`, ở **cả hai** nhánh dựng mặt
(`render === "mesh"` và `type === "face"`).

Thêm 2026-09-07 (`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`). Trước đó cả hai
nhánh dùng **quạt tam giác** từ đỉnh đầu — chỉ đúng với mặt LỒI. Với mặt lõm,
quạt **lấp mất phần lõm**: hình vẽ ra trông hợp lý mà sai. Sửa thể tích ở kernel
mà để renderer lấp phần lõm là chữa nửa bệnh — con số đúng, thứ học sinh NHÌN
THẤY vẫn sai. Đo được trên đáy `A(0,0) B(4,0) C(4,4) D(2,1) E(0,4)`: diện tích
thật **10**; quạt từ `A` phủ **14**, quạt từ `E` (đúng winding khối dùng) phủ
**22**.

⚠️ **KHÔNG phải một thẩm quyền hình học thứ hai** — nó không quyết định gì về
hình. Thứ tự đỉnh quanh mặt do kernel quyết; module chỉ **nối** chúng lại, và
mọi tam giác trả về là ba **CHỈ SỐ** vào chính mảng đầu vào, nên không toạ độ
nào do frontend sinh ra. Vì thế nó nằm trong danh sách nguồn được phép của guard
biên ở `scene3d.test.tsx` — kèm lý do viết thẳng trong guard.

Fail-closed: trả `[]` khi đa giác suy biến (< 3 đỉnh, mọi đỉnh thẳng hàng) hoặc
**tự cắt** (không cắt được tai nào). Người gọi khi ấy không vẽ gì, thay vì vẽ
một thứ vô nghĩa.

Test: `polygon-triangulate.test.ts` (module — diện tích, bất biến với
cyclic-shift/chiều duyệt/tịnh tiến/mặt phẳng nghiêng, suy biến, bow-tie) +
`scene3d.test.tsx` khối `(5D-lõm)` (renderer — `RENDERED_PROJECTED_AREA`,
`NOTCH_REMAINS_EMPTY`, `TRIANGLE_OVERLAP_OUTSIDE_FACE`, đo trên buffer THẬT mà
`buildObject3D` phát ra).

### `frontend/src/simulations/domains/geometry/scene3d-playback.tsx` · offline

Trình **PHÁT LẠI** quá trình dựng (Phase 5E): `Scene3DPlayer`. Bọc
`Scene3DWorkspace` và thêm điều khiển **thời gian** — lùi · phát/dừng · tiến ·
thanh chọn bước — cùng bảng *"đang dựng / dựa trên"* (⚠️ **ĐÃ GỠ ở
regular-square-pyramid-w01**, ROADMAP §0.1-8: lặp dòng thuyết minh và ô soi; thay bằng nút + panel
**«Các bước dựng»** `geo3d-cac-buoc` đọc `geometryStepList` — mỗi bước một nút, `aria-current="step"`, bấm ⇒
dừng phát rồi đặt bước theo neo; prop `stepsOpen`/`onStepsOpenChange` do xưởng giữ, vắng thì tự giữ). Từ W12 thanh bước đi qua
BƯỚC DỰNG (`geometryTimeline`), không qua sự kiện: khung hiện luôn là neo của
bước dựng chứa `current_step`, tự phát dừng ở bước dựng cuối, và ngay dưới là
bảng lời giải `Scene3DSolution`.

Tách khỏi `scene3d-view.tsx` vì renderer là `display(scene, step)` và có test
cấm `<button`/`<input` trong đó. Luật ấy không phải "cấm mọi giao diện" mà là
*"khung 3D không được là chỗ dựng hình"* — điều khiển thời gian là việc khác.

⚠️ Ranh giới kiểm được: component này **chỉ phát ra một số nguyên** `step`. Test
cấm nó chạm `xyz`/`normal`/`vertices`/`toNumber`, cấm import `three`, và khoá
**đúng ba** `useState` (bước · phát · panel bước mở/đóng — cái thứ ba từ W1 chỉ là sở thích trình bày; thêm
nữa là dấu hiệu playback bắt đầu sở hữu thứ khác ngoài thời gian). Có test chứng minh `scene` đi vào và ra **nguyên vẹn**.

⚠️ **Giảm chuyển động ở tầng JS**: tự động phát là hoạt cảnh do JavaScript
phát, mà khối `@media (prefers-reduced-motion: reduce)` của W13-A11Y chỉ chạm
tới `animation`/`transition` của CSS. `prefersReducedMotion()` (trong
`scene3d-model.ts`) ẩn nút *Phát*; người học vẫn đi từng bước bằng nút. SSR-an
toàn: không có `window` ⇒ `false`.

### `frontend/src/simulations/domains/geometry/scene3d-playback.test.tsx` · offline

Khoá ranh giới 5E: điều hướng bước thuần · giảm chuyển động ở tầng JS (4 ca gồm
`matchMedia` ném lỗi) · nhãn trình đọc màn hình · và quan trọng nhất — playback
**không đụng nội dung toán học**.

### `frontend/src/simulations/domains/geometry/scene3d-steps-panel.test.tsx` · offline

regular-square-pyramid-w01 — phần kiểm được không cần WebGL của chín chỉnh sửa ROADMAP §0.1 trên payload
thật w11: §0.1-1 card Kết quả ẩn khi lời giải thu gọn · §0.1-2 `quantityChoices` (kết quả → trung gian → dữ
kiện, không trùng `same_as`) + ngăn «Đại lượng» của xưởng chọn rồi đóng · §0.1-3/4/5 `geometryStepList` = đúng
các bước dựng, panel đóng/mở theo `stepsOpen`, chọn bước dừng phát rồi đặt neo, panel cuộn bên trong không phủ
khung · §0.1-8 không còn `geo3d-focus`. Bấm thật, đồng bộ panel ↔ phát lại và bố cục: bộ đo trình duyệt.

### `frontend/src/simulations/domains/geometry/scene3d-roles.ts` · offline

**Bảng MÀU VAI TRÒ** dùng chung (W12): `MAU_VAI_TRO` (`dich` xanh ·
`moi_dung` = `dich` · `du_kien_so` cam đậm · `trung_gian` cam nhạt · `boi_canh`
/ `nen_boi_canh` trung tính · `diem_de_cho` trung tính), `BIEN_CSS_VAI_TRO`
(tên biến CSS mang cùng giá trị) và `hexCss`. Renderer (`scene3d-view.tsx`)
đọc số hex; bảng lời giải đọc bản sao `--geo3d-vai-tro-*` trong `tokens.css`.
Review W12: cam đậm từng mang hai nghĩa (dữ kiện số / vật đang chọn), xanh
cũng hai (điểm đề cho / đích). Khoá: `scene3d-roles.test.ts` (nghĩa + đồng bộ
CSS↔TS) và `scene3d-causal-colors.test.tsx` (màu THẬT trên vật liệu three.js).

### `frontend/src/simulations/domains/geometry/scene3d-solution.tsx` · offline

**Bảng LỜI GIẢI** dưới thanh bước (W12): `Scene3DSolution` + `lopDongLoiGiai`.
Ba mục đọc từ `solutionAt` — Dữ kiện · Các bước tính (công thức, "Dựa trên") ·
Kết quả — đồng bộ với bước dựng đang xem; đáp số hiện ĐÚNG MỘT lần, ở Kết quả. Từ regular-square-pyramid-w01
(§0.1-1) mục Kết quả chỉ hiện khi lời giải MỞ; thu gọn thì đáp số đọc qua ngăn «Đại lượng», nhãn khi chọn và ô soi.
Mỗi dòng là một nút chọn vật (chuỗi nhân quả); lớp dòng theo tầng
`tangNhanManh` (`la-chon` · `la-so-lieu` · `la-trung-gian` · `la-boi-canh` ·
`la-diu`) và màu đọc token `--geo3d-vai-tro-*`, cùng nghĩa với khung 3D. Chú
giải ngắn chỉ hiện khi có vai trò để giải nghĩa (đang chọn, hoặc đang có vật
vừa dựng). Khổ hẹp: Dữ kiện + Các bước tính gập được (nút `geo3d-lg-gap`), Kết
quả luôn hiện. Thay dải số đo từng nổi trên khung (`geo3d-readout`, đã gỡ).

### `frontend/src/simulations/domains/geometry/scene3d.test.tsx` · offline

Khoá bốn ranh giới của 5D: renderer không tính hình học · float chỉ ở
`toNumber` · không primitive ngoài `RENDER_KINDS` · timeline đúng thứ tự dựng và
**ổn định** (cùng state cho cùng kết quả). Đồng bộ TS↔Python do
`backend/tests/geometry/test_scene3d_ts_sync.py` giữ.

### `backend/app/simulation/semantic_program/scene3d.py` · offline

Dữ liệu **CẢNH 3D** cho renderer (Phase 5C):
`SimulationState → **Scene3D** → Renderer 3D`. Xuất `build_scene3d` ·
`build_scene_events` · `RENDER_HINT`.

**Hai cách khai bán kính, MỘT cửa đọc** (2026-09-04,
`CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION`). `CurvedSolid` nhận **đúng một**
trong `rim_point` (điểm đã dựng) hoặc `radius_sq_khai` (bán kính khai thẳng);
`radius_sq` là `@property` nên không tầng nào mọc `if rim_point else`. Cách thứ
hai BẮT BUỘC phải có: không phép dựng nào sinh một điểm từ (điểm, độ dài), và
`r² = 7` không có điểm vành hữu tỉ nào — engine tự dựng cũng bất khả. Loại nào
nhận cách khai ấy là **cột `khai_bang_ban_kinh` của `KHOI_CONG`**, không phải
phép so `kind == "ball"` ở tầng trên (`test_04c` cấm, và nó đã bắt được bản đầu
của chính wave này). `binh_phuong_ban_kinh` là hợp đồng miền số: `mu != 0` hoặc
`r <= 0` ⇒ `CURVED_RADIUS_OUTSIDE_DOMAIN`.

**Ranh giới mạnh nhất trong cả chuỗi, và nó cưỡng chế được bằng MỘT mệnh đề**:
module này **không import gì** ngoài `typing` — nhận `dict`, trả `dict`.
`simulation_state.py` buộc phải biết `Vec3` để đọc bộ nhớ nên ranh giới ở đó
phải quét `ast` tìm tên hàm bị cấm; ở đây thì *"danh sách import phải rỗng"*, và
không có cách nào để một phép hình học lẻn vào.

`RENDER_HINT` là bảng **ĐÓNG** (7 mục): không `cylinder`/`sphere`/`curve` — thêm
là để tầng TRÌNH BÀY đẻ ra năng lực mà tầng SINH không có. `plane3`/`line3` cố ý
**không mang biên**: chúng vô hạn, và cắt chúng là quyết định của renderer, dựa
trên `depends` (tên các điểm sinh ra) mà toạ độ đã có sẵn trong cùng cảnh.

⚠️ **KHÔNG đặt tên `VisualTraceAdapter`** — `visual_adapter.VisualTraceAdapter`
đã tồn tại và làm việc khác hẳn (trace → `VisualFrame[]` cho chín nguyên thuỷ 2D
qua `visual_bindings`). Có test khoá để không ai đặt trùng.

⚠️ Scene3D đi **VÒNG QUA** đường `visual_bindings` → `envelope`, nên nó **KHÔNG
mở khoá `B` (servable)**: `learner_surface` vẫn đòi container biến động có
binding trong tập chín nguyên thuỷ đã đóng băng, và một `solid` vẫn không binding
nổi. Đo được: `geo_09` cho `executable=True · servable=False` nhưng Scene3D vẫn
dựng đủ 7 đối tượng.

> `runtime_identity.py` nay xuất thêm `semantic_environment_fingerprint()` +
> `semantic_environment_hash()` — **cùng một thẩm quyền**, không dựng vân tay
> thứ hai. Năm thành phần: `prompts` (mọi `skills/*.md`, dẫn từ
> `gemini.SKILLS_DIR`) · `grammar_card` · `synthesis_schema` · `analyze_schema` ·
> `capability` (`stable_capability_hash`). KHÔNG băm `pipeline.py` nguyên tệp —
> 794 dòng gần hết là luồng điều khiển, băm cả tệp thì mọi lần sửa logic không
> liên quan đều làm cổng đỏ, và một báo động giả là cách nhanh nhất để một cổng
> bị tắt.

### `backend/scripts/lock_cache_identity.py` + `backend/cache_identity.lock.json` · offline

KHOÁ DANH TÍNH CACHE — ghi lại **một cặp**: `CACHE_VERSION` nào đi với môi
trường sinh ngữ nghĩa nào. Không cờ ⇒ ghi lại; `--verify` ⇒ thoát != 0 khi lệch.
**0 lượt gọi model.**

Bịt lỗ `C1` của `CURRENT_ARCHITECTURE_GAP_AUDIT §12`: khoá cache runtime là
*text chuẩn hoá + `CACHE_VERSION`*, mà `CACHE_VERSION` là con số **người phải
nhớ tăng**. Đổi prompt / lược đồ model-facing / chữ ký IR mà quên bump ⇒ envelope
của một phiên bản hệ không còn tồn tại vẫn được phục vụ, không gì phát hiện.

⚠️ **Đây là CỔNG, không phải khoá cache mới.** `_cache_key` không đổi một dòng;
`test_KHOA_CACHE_san_pham_KHONG_doi` quét mã nguồn để chắc không vân tay nào lọt
vào đường chạy thật. Câu đúng là *"đầu vào tĩnh mang nghĩa không thể đổi mà
không làm cổng đỏ"* — **không** phải *"cache tự vô hiệu hoá"*.

⚠️ **Khoá đặt NGOÀI `app/` có chủ đích.** `MEASURED_SYSTEM_PATHS` gồm
`backend/app`; để khoá trong đó thì mỗi lần làm mới lại làm candidate đánh giá
hết hiệu lực — trộn hai cơ chế không liên quan.

⚠️ **Script KHÔNG tự bump `CACHE_VERSION`.** Quyết định *"envelope cũ còn dùng
được không"* là của người; đoán hộ sẽ đoán sai đúng lúc đắt nhất.

### `backend/tests/test_cache_identity.py` · offline

15 ca. Cổng chính khoá cặp (version ↔ môi trường); bốn ca **TIÊM** chứng minh nó
đỏ được — sửa prompt · thêm file prompt mới · đổi `_CHU_KY` · đổi lược đồ
model-facing. Tiêm bằng cách vá **chính `gemini.SKILLS_DIR`** mà runtime nạp,
nên một prompt mới không thể nằm ngoài vân tay: cả hai đọc cùng một chỗ.
Đã chứng minh trên cây THẬT: thêm một dòng vào `geometry_program_generator.md`
⇒ ĐỎ, nêu đúng `thành phần đổi: ['prompts']`; khôi phục ⇒ xanh.

### `backend/app/simulation/semantic_program/display_names.py` · offline

**THẨM QUYỀN TÊN HIỂN THỊ** — vật ngữ nghĩa được *gọi là gì* trước mặt học sinh.
Xuất `ten_hien_thi(bảng) → {tên: {label, notation}}` và `MO_TA_KIEU`.

Ra đời để đóng **G1** (`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT §5`): trước
đó không tầng nào sở hữu câu hỏi này, nên `label` **rơi về `id`** và học sinh
đọc `khoang_cach_hs √22`. Bốn bậc, **không có bậc thứ năm**: nhãn mô hình đặt →
công thức gọi tên theo phép dựng (`_CACH_GOI`) → mô tả chung theo kiểu → *(cấm)*
`id` thô.

`_CACH_GOI` khoá theo **producer**, tuyệt đối không theo dạng bài; một nhánh
`if "chóp" in …` ở đây là special-case theo họ hình.

`notation` (ký hiệu ngắn in cạnh vật trên khung) ghép ĐỆ QUY từ ký hiệu toán
hạng — `(MNP)`, `d(S, (ABC))`, `V(S.ABCD)` — và **fail-closed**: thiếu một toán
hạng là trả `None`, vì `(M?P)` trông như ký hiệu thật. `None` là câu trả lời hợp
lệ và khung không in gì. Câu hỏi *"chuỗi này có phải ký hiệu toán không"* thuộc
`source_entities.ky_hieu_toan`, **không** tự bóc tiền tố lần thứ hai ở đây.

Khoá bởi `tests/geometry/test_display_names.py` — trong đó có guard TỔNG QUÁT
`test_KHONG_vat_nao_lay_id_lam_ten_hien_thi` (không liệt kê tên cụ thể).

### `backend/app/simulation/semantic_program/simulation_state.py` · offline

Lớp **TRUNG GIAN giữa interpreter và renderer 3D** (Phase 5B):
`Semantic Program → Interpreter → **Simulation State** → Renderer`.
Xuất bốn thứ: `dependency_graph` · `build_scene` · `build_timeline` ·
`build_simulation_state`.

**CHIẾU, KHÔNG TÍNH** — không một phép hình học nào, khoá bằng test quét `ast` ở
tầng import (bắt cả `cross`/`dot`/`intersect_*` chưa ai viết). Hệ quả định hình
cả thiết kế: `Line3`/`Plane3` là **vô hạn**, nên biên để vẽ *không có trong
kernel* — lớp này **không tính biên** mà chở **provenance** (`sources` = tên các
điểm sinh ra đối tượng), và renderer dựng biên từ toạ độ đã có sẵn trong cảnh.
Đó cũng là điều đúng với đề tài: cảnh mô tả *hình được tạo ra thế nào*, không
phải *hình trông thế nào*.

**`dependency_graph` lọc cạnh bằng `ir_static_check.bang_ky_hieu`, KHÔNG bằng
`memory_declarations`** (`GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE`, 2026-09-04).
Bất biến là *"không tên ma"*; cái từng sai là **tập** dùng để kiểm nó —
`construct_*` ghi thẳng `memory[target_var]` mà không cần khai báo, nên mọi
cạnh trỏ tới một vật DẪN XUẤT bị coi là rác rồi lọc mất. Đây là consumer THỨ BA
của câu hỏi *"chương trình có vật nào"*; hai cái kia (runtime, `kiem_tinh`) vốn
đã đúng, và `OBLIGATION_BINDING_CONTRACT` sửa cái thứ tư (cổng phủ) trước đó
nhưng bỏ sót cái này. Hàm này là thứ **học sinh nhìn thấy**: nó nuôi
`interaction-state.dependencyClosure`.

**KHÔNG FLOAT**: mọi số là **chuỗi phân số** (`"1/2"`), đọc ngược được bằng
`Fraction`. Renderer hoá float ở bước cuối trước buffer. Khoá bằng test quét
toàn cây JSON.

`free` vs `derived` **dẫn xuất** từ `_producers`, không phải cờ LLM khai — cờ
khai được là cờ khai sai được, và ở đây khai sai nghĩa là một điểm dẫn xuất tự
nhận mình tự do rồi được phép kéo (Phase 5E).

⚠️ `dependency_graph()` là **API TRÌNH BÀY**, cấm dùng để thẩm định — C₁a có bản
riêng và bản đó mới là cổng. Có test quét toàn `app/simulation` để không module
nào khác gọi nó.

### `backend/app/simulation/semantic_program/domain_profile.py` · offline

Sở hữu **hồ sơ MIỀN** của route ngữ nghĩa: mỗi miền (`tin_hoc` · `hinh_hoc`) có
tập nghĩa vụ, bảng kiểu dữ kiện và cặp skill riêng. Tập nghĩa vụ **dẫn xuất** từ
bảng kiểu container của `obligations.OBLIGATION_KINDS` (nghĩa vụ nào nhận toàn
bộ chủ thể là kiểu hình học thì thuộc miền hình học) — không chép tay thành danh
sách thứ hai. Giữ luôn `detect_domain`, một heuristic từ khoá **fail-safe về phía
`tin_hoc`**: cửa duy nhất nó mở là cửa sang hình học, nên 24 target Tin học
không thể bị nó làm hỏng. Đường ĐO không dùng nó — runner truyền miền thẳng.

**BỐN MỨC, không phải ba** (sửa sau Phase 7B, 2026-08-29). `_MANH_QUAN_HE`
(`thiết diện`, `giao tuyến`, `đồng phẳng`, `chéo nhau`…) thắng cả phủ quyết Tin
học; `_MANH_DANH_TU_KHOI` (`hình chóp`, `lăng trụ`, `mặt cầu`, `hình lập
phương`…) thì **không**. Ranh giới: lớp đầu gọi tên một QUAN HỆ hoặc PHÉP DỰNG,
lớp sau gọi tên một VẬT — đề hỏi *làm gì* chứ không hỏi *có vật gì*. Bản gộp
hai lớp kéo nhầm ba đề Tin học hợp lệ sang hình học (*"viết chương trình tính
thể tích **hình chóp**"*).

⚠️ **Lỗ đã ship và đo được ở Phase 7B**: `hình lập phương` — khối mà bốn ô
`BANG_O` dùng (A06 · A08 · A09 · A10) — không nằm trong cụm mạnh. Đề góc trên
hình lập phương RẤT NGẮN, chỉ gom được hai cụm yếu, dưới ngưỡng ba ⇒ `tin_hoc`
⇒ ngoại lệ hình học của cổng phạm vi không áp ⇒ **hai ô GÓC chết ở `scope` 3/3
lượt mỗi ô**, 0 nghĩa vụ, và học sinh nhận thẻ *"bài này thuộc môn khác"*.

⚠️ **`_MANH_MOI_NGHIA_VU` từng thiếu BỐN nghĩa vụ CÓ CHECKER** — `area` ·
`lateral_area` · `radius` · `section_matches` — nên `co_duong_thuc_thi`
fail-closed cả một LỚP đề chỉ hỏi *"tính diện tích/bán kính…"*, trong khi hệ có
đủ đường (`BANG_PHEP_DO`, `GEOMETRY_CHECKERS`). Sửa 2026-09-07, **một bảng một
thẩm quyền**: `area`/`radius` dùng **danh từ trần** (cổng này định tuyến THÔ —
đúng/sai hình học thuộc grounding · phủ · kernel · checker; bỏ sót một cách viết
là fail-closed một bài giải được), `lateral_area` ba biến thể có định ngữ,
`section_matches` dùng chung cụm *"thiết diện"* với `coplanar` — trước đó nó
định tuyến được là nhờ **MƯỢN** manh mối của `coplanar`. **Không** thêm *"diện
tích toàn phần"*: miền số cố ý từ chối tổng hai căn thức khác nhau. Bất biến
khoá bằng test **dẫn xuất** từ registry — `(analyze enum ∩ GEOMETRY_CHECKERS) −
khoá(_MANH_MOI_NGHIA_VU) = ∅` — chứ không phải danh sách chép tay:
`test_scope_gate_quantity_obligation_clues.py` (43 test, 4 phép tiêm, chấm ở
mức **TẬP** vì ở mức `bool` phép tiêm sẽ xanh giả).

**`geometry_symbol_key` nay chuẩn hoá DẤU PHẨY** — `A'` · `A′` · `A_prime` ·
`Aprime` → `A1`, bậc hai `A''` → `A2`. Trước đó hàm bỏ `_`/`-` rồi đòi
`isalnum()`, nên `'` rớt cả hai vế và `geometry_symbol_key("A'")` trả `None`:
cách viết phổ biến nhất của hình học không gian THPT **không được nhận là ký
hiệu**, và `khop_ky_hieu` không bao giờ nối được witness `A'` của hợp đồng với
biến nào của chương trình. Gộp an toàn vì `khop_ky_hieu` fail-closed sẵn —
trùng khoá ⇒ `None`, không đoán.

### `backend/app/simulation/semantic_program/postconditions.py` · offline

Sở hữu **C₂** — checker server-owned, gộp bảng Tin học với `GEOMETRY_CHECKERS`
(9 kind hình học, ở `geometry_obligations.py`). Mỗi checker tính lại tính chất TỪ
TRẠNG THÁI CUỐI bằng phép toán sơ cấp, **không cài lại thuật toán của chương
trình**; đó là điều kiện để oracle giữ được tính độc lập. `structural_traversal`
cố ý chưa có checker (lý do ghi trong file).

### `backend/app/simulation/semantic_program/geometry_obligations.py` · offline

Sở hữu **chín checker hình học** của C₂. Gọi `predicates`/`measure`, không cài
lại toán — hai tầng hình học sẽ lệch nhau ở một ca nào đó, và lệch im lặng.

`check_volume` nhận **cả `Polyhedron` lẫn `CurvedSolid`** từ 2026-09-03
(`VOLUME_VERIFICATION_BRIDGE`) và uỷ phép tính cho `geometry_exec.volume_of` —
cùng cửa với đường chạy. Nó **không** có `check_ball_volume`/`_cylinder_`/`_cone_`:
hình nào là dữ liệu (`curved_kind`), ba công thức thuộc bảng `KHOI_CONG`.
Bất biến chống tái phát nay do `tests/geometry/test_measure_checker_subject_drift.py`
giữ: **mọi** nghĩa vụ ĐO có checker phải kiểm được **mọi** kiểu chủ thể mà
`BANG_PHEP_DO` cho phép — nó duyệt hết bảng và tự thấy dòng mới.

Cùng file cũng sở hữu **`KHONG_KIEM_DUOC`** + `kieu_kiem_chung_duoc()`
(2026-09-03, `VERIFICATION_CAPABILITY_IDENTITY`): lời khai *"hợp đồng cho phép
kiểu này nhưng bộ kiểm không với tới"*, hiện đúng một mục (`angle`/`vector3`).
Nó **là mã sản phẩm chứ không phải hằng test** — `capability_fingerprint()` băm
hiệu của nó, nên nếu nó nằm trong file test thì vân tay năng lực của sản phẩm sẽ
phụ thuộc bộ đo. Test giữ đúng vai: chứng minh lời khai ấy trung thực
(`test_loi_KHAI_nang_luc_kiem_chung_khop_thuc_te_DO_DUOC` đo thật rồi so với lời
khai). Nợ chỉ đi xuống, và nay thêm một mục là **đổi `stable_capability_hash`**.

`check_section_matches` (2026-08-30) là cái khác hình dạng với tám cái kia: nó
**dựng lại** thiết diện chuẩn từ `params.solid + params.plane` rồi so CHU TRÌNH
(`same_section_cycle`). Khối và mặt phẳng lấy từ **phía ĐỀ**, không từ câu lệnh
chương trình — lấy từ chương trình thì thành tautology và ca *"cắt nhầm mặt
phẳng"* không bao giờ bị bắt. Vì sao không để `coplanar` gánh: mọi đỉnh thiết
diện sinh ra từ giao với đúng MỘT mặt phẳng nên `coplanar` **gần như luôn xanh**,
kể cả khi đa giác thiếu đỉnh. Ca chứng minh:
`test_section_capability.py::test_O_DONG_PHANG_DUNG_nhung_DA_GIAC_SAI_thi_FAIL`
— cùng dữ liệu, `coplanar` nói ĐƯỢC, `section_matches` nói KHÔNG.

### `backend/app/simulation/semantic_program/learner_surface.py` · offline

Cổng CUỐI và là cổng **duy nhất quay về phía màn hình** — mọi cổng khác nhìn về
phía chương trình. Chạy SAU `compile` vì câu hỏi là về những khung **sẽ được
phát**, không phải về ý định của chương trình. Hạ `servable=False` nhưng **giữ
`executable=True`** (`LEARNER_SURFACE_INCOMPLETE` → `verification_gap`): hệ chạy
được bài, cái thiếu là đường lên màn hình.

Bổ khuyết đúng chiều còn trống của bất biến #34: `_assert_bindings_resolvable`
hỏi *mỗi binding có biến không*; cổng này hỏi *mỗi biến đáng thấy có binding
không*. Chỉ đòi HAI lớp — container **biến động** và **witness** của nghĩa vụ —
vì đòi mọi biến là từ chối oan hàng loạt mô phỏng đúng (biến đếm, biến tạm), mà
một cổng kêu oan là một cổng sẽ bị tắt. Bảng tra HẰNG (`pairs`) không đổi giá trị
nên không bị đòi. Cùng danh sách `PLACEHOLDER_LEAKS` với
`frontend/src/simulations/learner-gate.ts` (HISTORICAL_REMOVED) — hai đầu của một luật.

**MÀN HÌNH CÓ HAI NỬA** (2026-08-25). `visual_bindings` là nửa 2D, phải KHAI;
`Scene3D` là nửa 3D, chiếu TẤT ĐỊNH. Chương trình hình học không khai binding
nào và nó ĐÚNG khi không khai — cổng đọc sót nửa kia nên từng từ chối **mọi**
chương trình hình học, kể cả bốn bài đã qua oracle ở Wave 4, và envelope rơi
xuống classifier rồi hiện "NGOÀI DANH MỤC MÔ PHỎNG" cho học sinh. `_tren_canh_3d`
bù nửa còn thiếu bằng vị từ ở `geometry_exec` (KHÔNG nhập tầng trình bày). Câu
hỏi của cổng không đổi một chữ — nó chỉ thôi nhìn sót.

Phát hiện đầu tiên của nó: fixture #18 dựng bảng tần suất suốt lượt chạy mà màn
hình không bao giờ có bảng — vì `map` là `MemoryType` đã admit mà không primitive
nào biểu diễn được. Đó là nguồn gốc của `map_view` (2026-08-23), thêm theo đúng
tiền lệ `graph_view`: mở vì một **lớp trạng thái đã admit**, nguồn phát hiện DEV,
không phải một ca SEALED. Thêm primitive ⇒ đồng bộ BỐN nơi: `contract.py` Literal ·
`visual_adapter.HANDLED_PRIMITIVES` + nhánh adapt · `test_primitive_set_frozen.py` ·
renderer `domains/semantic/ui.tsx`, rồi chạy `export_semantic_program_schema.py`.

### `backend/app/simulation/semantic_program/contract.py` — BIÊN CHUẨN HOÁ · offline

Ngoài các model IR, file này giữ **năm biên gộp cách viết**, tất cả cùng một luật:
*gộp hai cách viết của MỘT thứ, KHÔNG nới ngữ nghĩa*. Chúng tồn tại vì fail-closed
ở tầng cú pháp che mất năng lực ngữ nghĩa thật của chương trình. Mỗi biên gọi
`ghi_coercion()` khi nó thật sự gộp — xem `coercion_stats.py`; **thêm biên thứ
năm mà quên khai lớp ở đó là ĐỎ**.

- `canonical_spec_version` — `1.0` (số) ⇒ `"1.0"`. Nguồn: SEALED `7e5df014…`,
  **17/40 case** chết vì đúng lỗi này. Chặn `bool` tường minh (`True` là subclass
  của `int`). Phiên bản khác 1.0 vẫn bị từ chối.
- `canonical_container_name` — `{"kind":"var","name":X}` ⇒ `X`; mọi kind khác
  **raise có DẠY** thay vì để Pydantic nói "Input should be a valid string".
- `canonical_condition` (2026-08-23) — `hop_le` ⇒ `hop_le == true`. Nguồn: probe
  E2E, LLM viết `if hop_le and …` mà union điều kiện chỉ nhận sáu dạng mệnh đề.
  RANH GIỚI: chỉ gấp dạng mang được bool (`var/field/index/map_get/literal`);
  `arith`/`length`/`neighbors` vẫn bị từ chối vì `2+3` làm điều kiện là lỗi KIỂU
  thật — nới KÝ PHÁP không được thành nới KIỂU.
- `canonical_const_int` (2026-08-24) — `{"kind":"literal","value":1}` ⇒ `1` cho
  `for_range.step`. Nguồn: SEALED `7e5df014…`, 2 case. `start`/`end` là
  `ValueExpr` nên nhận dạng bọc, riêng `step` thì không — mô hình viết cả ba
  cùng kiểu là NHẤT QUÁN, chỉ hợp đồng là không. RANH GIỚI: chỉ gỡ `literal`
  mang số nguyên (`bool` bị chặn); `var`/`arith` vẫn từ chối vì bước nhảy phải
  HẰNG thì vòng lặp mới có biên tất định.
- `canonical_geometry_name` (2026-09-01) — `{"kind":"var","name":X}` ⇒ `X` cho
  **mọi ô toán hạng hình học**, qua alias `GeometryName`. Cùng lớp lỗi với
  `canonical_container_name`, ở miền chưa được vá: `audit_named_operand_
  ergonomics.py` đếm **16 lần** trên artifact live đã commit (`through_a`,
  `of`, `wrt`, `through[]`), nhiều hơn cả số lần lồng biểu thức thật (7). Mọi
  thứ khác — toạ độ thô, `literal`, phép dựng lồng không nâng được — bị TỪ CHỐI
  CÓ DẠY. Ô nào phải mang alias này thì `test_named_operand_slots.py` dẫn từ
  `ir_static_check` rồi soi lại từng trường Pydantic, không chép tay.

Tests: `test_spec_version_canonicalization.py`, `test_container_ref_canonicalization.py`,
`test_condition_canonicalization.py`. Sửa model ⇒ chạy
`scripts/export_semantic_program_schema.py` (ghi HAI bản — `docs/schemas/` và
**`frontend/src/simulations/domains/semantic/`**; bản frontend ở
`domains/generic/` cho tới `FRONTEND_LEGACY_FIXTURE_CUTOVER` 2026-09-02, dời
theo đúng chủ khi domain ấy gỡ — schema là hợp đồng IR **hình học**, không phải
tài sản của renderer generic; khoá bởi
`test_schema_sync.py`). BeforeValidator KHÔNG vào JSON schema nên hash schema chỉ
đổi khi model đổi.

### `backend/app/simulation/semantic_program/coercion_stats.py` · offline

Bộ đếm **bốn biên chuẩn hoá** của `contract.py` đã phải ra tay bao nhiêu lần.
Export: `ghi_coercion` · `reset_coercion` · `coercion_report` · `tong_coercion`
· `LOP_HOP_LE` + bốn hằng `LOP_*`.

VÌ SAO CẦN: bốn biên ấy cứu rất nhiều case, và chính vì thế mà chúng nguy hiểm —
gộp im lặng thì không phân biệt được *"mô hình thỉnh thoảng viết dạng khác"*
(biên làm đúng việc) với *"mô hình LUÔN viết dạng khác"* (hợp đồng đang mô tả
sai thứ mô hình phát, phải sửa ở prompt/thẻ văn phạm chứ không phải thêm lớp gộp
thứ năm). Phân biệt hai thứ đó chỉ cần một con số.

CỐ Ý KHÔNG DÙNG LẠI `app/ai/telemetry.py` dù cùng khuôn (bộ đếm trong tiến
trình, `reset`/`report`): telemetry ấy thuộc tầng `app.ai`, còn `contract.py`
nằm sâu trong `app.simulation` và không được phụ thuộc ngược lên tầng AI.

`coercion_report()` luôn trả **đủ bốn lớp kể cả khi bằng 0** — vắng mặt không
phân biệt được "chưa nổ" với "quên gắn bộ đếm". Không bao giờ ném lỗi (lớp lạ bị
bỏ qua im lặng): quan trắc mà giết được một lượt phân tích thì đắt hơn thứ nó đo.

Khoá bởi `tests/semantic_program/test_coercion_stats.py` (19 test), trong đó
nửa quan trọng là các ca ÂM TÍNH — dạng đã đúng thì KHÔNG được tính là một lượt
gộp, nếu không `coercion_rate` luôn 100% và vô nghĩa. `test_bon_lop_khop_voi_so
_bien_chuan_hoa_trong_contract` đếm bằng cách soi chính `contract.py`, không chép
tay danh sách — nó đã bắt được drift thật ngay lần chạy đầu (`canonical_const_int`
có trong mã mà `CODE_INDEX` vẫn ghi "ba biên").

Runner đọc nó ở `run_sealed_evaluation.py`: `reset_coercion()` đầu mỗi case,
`coercion_report()` vào `sealed_cases.json`, tổng hợp thành khối `coercion_rate`
trong `sealed_summary.json`.

### `backend/tests/semantic_program/test_repair_loop.py` · offline · 0 API call

Khoá **vòng sửa ≤3 lượt** của `stage_semantic_program` — 11 test, và nó tồn tại
vì `test_stage_synthesis.py` **không** phủ được vòng lặp: sáu test ở đó xanh y
hệt nhau dù `range(MAX_SEMANTIC_PROGRAM_ATTEMPTS)` có bị đổi thành `range(1)`.
Cùng loại lỗ đã làm `stage_semantic_program` từng **không ai gọi** mà suite vẫn
xanh.

Bốn nhóm khẳng định: vòng lặp **quay thật** (hỏng lượt 1 → sửa lượt 2 → trả
spec; JSON cụt cũng kích hoạt; thành công lượt 1 KHÔNG gọi thêm) · lỗi validator
**đi vào prompt lượt sau** kèm đề bài và thẻ văn phạm còn nguyên (thử lại mù ≠
vòng sửa) · **dừng đúng ở trần** (ngân sách 520 của `RUN2_PROTOCOL §3` dẫn từ
hằng số này) · mỗi lượt hỏng phát một `semantic_program_attempt` đánh số.

**TIÊM LỖI đã chạy**: hạ `MAX_SEMANTIC_PROGRAM_ATTEMPTS` 3 → 1 thì **7/11 test
ĐỎ**. Bốn test còn xanh là đúng — chúng phủ nhánh một-lượt hoặc dẫn bound từ
chính hằng số.

⚠️ Chọn payload hỏng cho bộ test này có HAI bẫy, đều làm test xanh vì lý do sai:
(1) bốn lớp đã có biên chuẩn hoá (`spec_version`, `container` dạng `var`, `step`
bọc literal, biến bool làm điều kiện) nay được **gộp** nên không kích hoạt được
vòng sửa; (2) ba thứ tưởng hỏng mà validator vẫn cho qua — `statements` **rỗng**,
gán vào **biến chưa khai**, `value_box` trỏ **biến lạ**. Payload dùng được là
`push` vào container chưa khai.

### `backend/scripts/reliability_v2.py` · offline · **0 API call**

Phân loại thất bại 8 tầng + khối chỉ số per-case của `RELIABILITY_EVALUATION_PLAN`.
Export: `phan_loai()` · `chi_so_case()` · `tong_hop()` · `TEN_TANG` · 8 hằng
`LAYER_*`.

TÁCH KHỎI RUNNER CÓ CHỦ ĐÍCH: phân loại là phần dễ viết sai nhất **và** đi thẳng
vào bảng luận văn, nên phải kiểm được offline bằng dữ liệu bịa — còn runner thì
chỉ được chạy một lần.

**Ba lớp dùng CHUNG một mã lỗi.** `semantic_program_invalid` gộp lớp 1
(`generation` — JSON cụt), lớp 2 (`schema` — Pydantic) và lớp 3
(`semantic_validation` — validator ngữ nghĩa). Phân biệt bằng **chuỗi lý do**,
không bằng mã: Pydantic luôn mang `"validation error… for SemanticProgramSpec"`.
Ai phân loại theo `error_code` sẽ làm đỏ `test_ba_lop_nay_dung_CHUNG_ma_loi` —
và đó là mục đích của test ấy. Gộp thì bảng thất bại chỉ **sai chỗ phải sửa**:
lớp 2 chữa được bằng biên chuẩn hoá, lớp 3 thì không.

**Gán theo cổng ĐẦU TIÊN** case chết, mỗi case đúng một tầng (`tong_kiem` phải
bằng `N`). **Lớp 0 báo riêng** — chặn đề ngoài môn là hành vi ĐÚNG.

**`None` ≠ `False` ở `replay_R`/`renderer_V`/`oracle_O`**: `None` = CHƯA ĐO.
Trộn hai thứ là bịa thêm thất bại; bịa theo hướng bi quan cũng vẫn là bịa. Cùng
lý do, `G1`/`G2` là `None` khi case chết ở lớp 0 — `False` ở đó là đổ lỗi sinh
cho một case chưa bao giờ tới bước sinh.

`tong_hop()` **không tính phần trăm**, chỉ phát tử số + mẫu số: §3.3 cấm chia khi
mẫu số < 20, mà mẫu số của `R`/`O`/`V` là *số ca đã qua tầng trước* (ở lượt #1 là
3 và 1). Khoá bởi `test_reliability_v2.py` (23 test).

### `backend/scripts/replay_harness.py` · offline · **0 API call**

Chạy MỘT `SemanticProgramSpec` trên **nhiều đầu vào** rồi so chuỗi hành động.
Export: `replay()` · `KetQuaReplay` · `TIM_MAX` / `GAN_CUNG` (hai chương trình
đối chứng) · `SO_BIEN_THE`.

VÌ SAO: tới 2026-08-24 một chương trình chỉ chạy đúng **một** lần, trên đúng
`initial_value` mà LLM viết cùng nó. Với một mẫu, *"tính ra đáp án"* và *"biết
trước đáp án"* cho cùng kết quả.

**RANH GIỚI VỚI C₁b — đọc trước khi thêm detector.** `coverage_gate` (`3e0d67c`)
đã bịt "gán thẳng đáp án" bằng kiểm **TĨNH** (witness phải có đường phụ thuộc,
kể cả qua nhánh, về container đầu vào). File này **không làm lại**. Nó phủ chỗ
tĩnh không với tới: chương trình *có* đọc container mà vẫn không tính đúng —
`GAN_CUNG` cố ý đọc `a` qua `length` nên **qua được C₁b**, và chỉ replay mới lộ.
Cũng khác `evaluation/metamorphic.py` (cái đó biến đổi **văn bản đề** cho
classifier; đây giữ chương trình, đổi **dữ liệu**).

Ba detector, **không cần oracle** — chạy được trên bất kỳ chương trình sinh nào:
`INPUT_IGNORED` (mọi đầu vào cho cùng một chuỗi hành động) · `DEAD_STATE`
(container khai ra mà không lượt nào đụng) · `HARD_CODED?` (witness hằng qua mọi
biến thể). Truyền `oracle=` thì so thêm.

⚠️ **`HARD_CODED?` là NGHI VẤN, KHÔNG vào `ok`** — một nghĩa vụ có thể hằng
chính đáng, biến nó thành phán quyết là đẻ false rejection ở chỗ khó cãi nhất.
Chỉ `INPUT_IGNORED` và `DEAD_STATE` quyết PASS/FAIL.

Chữ ký hành động cố ý **bỏ giá trị**, chỉ giữ `(action, target)`: giữ giá trị
thì hai lượt luôn khác nhau và `INPUT_IGNORED` xanh vĩnh viễn. Khoá bởi
`test_replay_harness.py` (9 test, nửa là ca ÂM TÍNH — chương trình thật không
được gắn cờ).

### `backend/scripts/classify_run1_failures.py` · offline · **0 API call**

Soi lại các ca trượt thẩm định của SEALED #1 bằng hợp đồng HIỆN TẠI, phân loại
**từng lỗi Pydantic** thành `GOP:<biên đã gộp>` hoặc `TRUOT:<lý do>`. Export:
`chay()` · `tach_loi()` · `phan_loai()` · `BOOL_KINDS`.

Nó trả lời *"bốn biên chuẩn hoá đáng giá bao nhiêu"* mà **không tiêu một lượt
LLM nào** — làm được vì `sealed_cases.json` giữ nguyên văn khối lỗi Pydantic, và
khối ấy liệt kê ĐỦ mọi lỗi của một chương trình. Kết quả 2026-08-24: **22/27 ca
nay qua tầng Pydantic**, 3 vẫn trượt (`kind` bịa ra · `field` ngoài
`{left,right,val,data}`), 2 không kết luận được (JSON cụt).

HAI RANH GIỚI, đừng trích sai: (1) qua Pydantic mới là **chạm cổng kế**, sau đó
còn `validate_semantic_program` → interpreter → C₁a → C₁b → C₂ — ở lượt #1, 9
chương trình qua cú pháp rụng còn 3 chạy được và 1 phát được; (2) nó chạy trên
**40 ca ĐÃ LỘ** nên là **chẩn đoán**, không phải số held-out.

`tach_loi()` phân biệt `None` (không phải lỗi schema — JSON hỏng) với `[]` (có
khối lỗi nhưng rỗng): hai thứ dẫn tới hai kết luận khác nhau, gộp là mất một
nhóm ca. Ba lớp `TRUOT` được ghi thành **dự đoán tiền đăng ký** ở
`RUN2_PREFLIGHT.md §3c` để lượt #2 bác bỏ được.

### `backend/scripts/cross_domain_matrix.py` · offline · 0 API call

Bảy lớp trạng thái (scalar · array · string · stack · derived_sequence · tree ·
graph) đi qua **một** bộ 11 cổng, không nhánh riêng miền nào. Đáp án mong đợi
**kiểm tay** (21=10101₂ · max=89 · "radar" · `{[()]}` · prefix [2,6,7,14,17] ·
preorder A,B,C · BFS 1→5), không chép từ đầu ra của hệ — nếu không
`EXPECTED_RESULT` là tautology. `--json/--md` ghi artifact vào
`docs/evaluation/semantic-vnext/reports/`.

Khoá bởi `tests/semantic_program/test_cross_domain_matrix.py`, và nửa quan trọng
hơn của bộ test ấy là phần TIÊM LỖI: bản đầu của ma trận **rỗng** — gỡ binding
mà 6/7 lớp vẫn xanh, vì cổng chỉ chạm container biến động còn dãy đầu vào
chỉ-đọc thì không ai đòi. Đó là nguồn gốc luật (2) của `learner_surface`.

### `backend/tests/test_mocked_production_e2e.py` · offline · 0 API call

E2E qua ĐƯỜNG HTTP THẬT (`POST /api/analyze` → `main.py` → `run_pipeline` → …
→ `learner_surface` → envelope), chỉ thay `call_gemini`. Không inject envelope,
không inject store. Ba miền: array · graph · map. Chạy TRƯỚC mọi lượt live —
mọi tầng sau LLM là tất định nên tiêu quota để phát hiện lại lỗi tất định là
lãng phí (đã xảy ra ba lượt liên tiếp trong wave này).

### `backend/app/simulation/semantic_program/analyze_contract.py` · offline

Sở hữu **bề mặt `analyze` của route semantic**, tách hẳn enum dẫn xuất catalog
(spec E5). `build_request_contract` LỌC nghĩa vụ ngoài taxonomy ngay tại đây.

### `backend/app/ai/pipeline.py` → `_semantic_shadow` · **live**

Quyết định route sinh **có được thử hay không** — và cố ý KHÔNG hỏi classifier
chọn target nào. Chỉ hai cổng: phạm vi (bỏ qua `GATE_SCOPE_UNDECLARED` vì đó là
lỗi hợp đồng prompt, không phải phán quyết về đề) và `execution_authority`.
Đặt nó trong nhánh generic là làm claim A phụ thuộc classifier legacy — tức đo
classifier chứ không đo route sinh. Việc **PHÁT** thì vẫn nhường module chuyên
biệt (ranh giới: không thay 24 module). Khoá bởi
`test_route_wiring.py::test_shadow_VAN_chay_khi_classifier_chon_module_chuyen_biet`.

### `backend/app/simulation/semantic_program/grammar_card.py` · **live**

Hợp đồng IR ở dạng gọn (~2,3 KB), **sinh 100% từ `contract.py`**, ghép vào
*user message* của `stage_semantic_program`. Nó thay `responseSchema` — thứ
Gemini KHÔNG nhận được vì schema IR đệ quy và nội suy `$ref` nổ ~10× mỗi bậc
(296 KB ở độ sâu 2, 3 MB ở độ sâu 3). Không có nó, mô hình bọc đầu ra trong
khoá `semantic_program`, gọi `variables` thay `memory_declarations`, và
38/40 case trượt thẩm định.

⚠️ **`SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT` (2026-09-15)** — lượt synthesis C02 thật đặt `at`
(trường của câu lệnh `declare_point`) trong `memory_declarations[0]` ⇒ một lượt sửa. Ba chỗ, MỘT nguồn khoá
(`MemoryDeclaration.model_fields`):
- **Thẻ:** dòng `memory_declarations[]:` của `grammar_card("hinh_hoc")` thêm mệnh đề ` — mỗi mục có ĐÚNG các khoá
  này` (6690 → 6733 B, trần 6750). Không liệt kê khoá lần hai.
- **`semantic_program/validator.py`:** `khoa_la_trong_khai_bao(raw)` → mọi khoá lạ trong khai báo kèm JSON Pointer
  RFC 6901 · `blocking` · chủ sở hữu · ô giá trị; `MA_KHOA_BI_BO_IM_LANG = "SCHEMA_SILENTLY_DROPPED_KEY"`;
  `_khoa_bi_bo_im_lang` (giữ tên — runner đọc) trả lời từ chối ngắn `[MÃ] <con trỏ>: … Khoá hợp lệ: …` (không giá
  trị, không chương trình, không lược đồ). LUẬT chặn không đổi: khoá mang dữ liệu bị bác; khoá trang trí (`label`…)
  không bác vì bác chúng làm đỏ replay đóng băng p4/p5 và mọi chương trình AI lịch sử, nhưng được BÁO qua
  `ValidationResult.ignored_keys` (`{"pointer", "key"}`).
- **`ai/pipeline.py`:** sự kiện observer thụ động `semantic_program_ignored_keys` (#22).
Không thêm `at` vào `MemoryDeclaration`; lược đồ xuất không đổi. Khoá: `test_memory_declaration_contract_alignment.py`
(A–M, fixture DẪN XUẤT từ chương trình p6 đóng băng — candidate thật không được lưu), `tests/grammar_card_identity.py`
(dựng lại băm thẻ trước wave 6cbba188…).

Phải liệt kê **cả giá trị enum** chứ không chỉ tên trường: tên trường nói được
*chỗ nào điền*, không nói được *điền gì* (mô hình từng viết `op: "add"` thay
`"+"`). Đặt ở user message chứ không ở `skills/*.md` để ngân sách prompt tĩnh
vẫn đo đúng thứ nó sinh ra để đo. Khoá bởi `test_grammar_card.py` (9 test, gồm
sync-lock từng `kind` và chặn rác kiểu `typing.Annotated` lọt vào).

**THEO MIỀN từ 2026-08-31.** `grammar_card("hinh_hoc")` trả bản THU HẸP —
2.877 B thay vì 4.153 B — bỏ toàn bộ IR Tin học (`enqueue`, `map_set`,
`write_index`, `neighbors`…), bỏ `visual_bindings` (cảnh 3D dựng tất định từ
bộ nhớ, nên chương trình hình học **không khai binding và đúng khi không
khai** — `learner_surface._tren_canh_3d`), và thêm KIỂU TOÁN HẠNG của từng
phép đo ngay dưới `measure`. `domain=None` ⇒ bản đầy đủ, tức hành vi Tin học
nguyên vẹn. Không phải cắt cho gọn: một primitive được LIỆT KÊ là một lựa
chọn được mời gọi — cùng cơ chế đã đo được ở `analyze` khi enum nghĩa vụ mời
cả 9 nghĩa vụ Tin học và mô hình chọn `derived_sequence` cho câu hỏi
`point_on_line`.

**NHÃN LOẠI trên TỪNG DÒNG từ 2026-09-04** (`CARD_CATEGORY_AFFORDANCE`):

```
  [LỆNH] construct_section: target_var solid:tên<solid> plane:tên<plane3> …
  [BIỂU THỨC→assign] intersect_plane_curved: solid:tên<curved_solid> plane:…
  [BIỂU THỨC→assign|construct_point] midpoint: a:tên<point3> b:tên<point3>
```

Loại dẫn từ `_tap_hinh_hoc()`; **cửa tiêu thụ** dẫn từ `_cua_tieu_thu()` — nó
đọc trường nào của câu lệnh là union phân biệt rồi lật ánh xạ, nên
`construct_point` tự hiện ra ở các phép sinh ĐIỂM mà không ai viết tay.
`_nhan_loai` **NÉM** nếu một biểu thức không có cửa nào nhận: im lặng bỏ nhãn
là quay về đúng trạng thái wave này đi sửa, mà không gì đỏ.

⚠️ Vì sao ở TỪNG DÒNG chứ không ở tiêu đề: `AUDIT_MODEL_FACING_SCHEMA_SURFACE`
đo được `intersect_plane_curved` cách tiêu đề nhóm 5 dòng và cách `assign` 15
dòng, trong khi `construct_section` — CÂU LỆNH, cùng toán hạng `solid`+`plane`
— nằm cách 9 dòng, không dấu hiệu nào trên chính dòng. `cylinder_2` (probe V2)
viết phép đầu như một câu lệnh; chín lượt sửa cứu 0 ca.

**`_ten_phep(dong)`** là chỗ DUY NHẤT biết cách đọc tên phép trên một dòng thẻ
(bỏ qua nhãn) — bên sinh và `manh_hop_dong` dùng chung; hai bản tự tách chuỗi
sẽ lệch đúng vào ngày nhãn đổi hình dạng. Khoá bởi
`tests/semantic_program/test_card_category_affordance.py` (61).

Hai bẫy NHÃN đã cắn ở đây, cùng một lớp — *nhãn sai của TA đẻ ra lỗi của NÓ*:
`construct_plane.through` (`list[str]`, **tên ba điểm**) từng bị nhánh
"list dài đúng 3" dán nhãn `[x,y,z] số hoặc chuỗi phân số`, tức dạy mô hình
viết TOẠ ĐỘ THÔ vào đúng chỗ cổng trung thực năng lực vừa dựng để chặn; và
`memory_declarations` từng mang nhãn "khối lệnh". Nhãn phải hỏi KIỂU PHẦN TỬ,
không chỉ hỏi độ dài.

`manh_hop_dong(loi, domain)` trả đúng những DÒNG của thẻ mà lời từ chối nói
tới — nguồn ngữ cảnh cho prompt sửa (§8), thay cho việc gửi lại cả thẻ.

**HAI TẦNG từ 2026-09-04** (`REPAIR_FRAGMENT_COMPLETENESS`). Tầng ① dẫn từ
**cấu trúc lỗi** — tag sai (`Input tag 'X' found using 'kind'`) và đường lược đồ
(`statements.1.assign.expr.vector_from_points.from_point`) — rồi kèm ĐÚNG mục
của phép ấy: tiêu đề nhóm, dòng chữ ký, và với BIỂU THỨC thì kèm `assign` (cửa
duy nhất tiêu thụ biểu thức). Những dòng ấy **miễn trừ khỏi trần**. Tầng ② khớp
định danh như cũ, lấp phần trần còn lại.

⚠️ Vì sao cần tầng ①, đo bằng quota thật (`cylinder_2`, probe V2): mô hình viết
`intersect_plane_curved` như CÂU LỆNH; lời từ chối liệt kê **mọi** tag hợp lệ
nên tầng ② khớp cả chín dòng câu lệnh trước, và dòng định nghĩa phép ấy —
đứng **14/15** — bị trần 12 cắt mất. Mô hình biết *sai ở đâu* mà không biết
*dạng đúng nằm chỗ nào*; chín lượt sửa cứu 0 ca.

Phân loại câu lệnh ↔ biểu thức đọc từ `_tap_hinh_hoc()`; tên toán hạng đến từ
model Pydantic qua thẻ. **Không có bảng chữ ký thứ hai** — `SIGNATURE_AUTHORITIES
= 1`, khoá bởi `test_ten_toan_hang_DAN_TU_THAM_QUYEN_chu_khong_chep`. Tiêu đề
hai nhóm là hằng số `_TIEU_DE_LENH`/`_TIEU_DE_BIEU_THUC`, dùng chung cho bên
dựng thẻ và bên chọn mảnh. Khoá bởi
`tests/geometry/test_repair_fragment_completeness.py` (22), có ca dựng lại bộ
chọn CŨ để chứng minh nó thiếu.

⚠️ **`_tap_hinh_hoc` phải dẫn từ `_KIEU_DUNG`, KHÔNG từ `_TOAN_HANG_LENH`.**
Bảng thứ hai liệt kê câu lệnh dựng có toán hạng là TÊN, và `construct_point`
**cố ý không có mặt** ở đó (toán hạng của nó nằm trong `expr`). Dẫn thẻ từ nó
nên thẻ hình học **chưa bao giờ liệt kê `construct_point`** — và mô hình dựng
mọi điểm phụ bằng `assign M = midpoint(...)`, lối duy nhất nó thấy, lối chết ở
runtime. `CLEAN_BASELINE_V1` mất 4/6 ca vì một cái tên vắng mặt trong một danh
sách. Chọn bảng nguồn ở đây là một quyết định ngữ nghĩa, không phải một chi
tiết.

### `backend/app/simulation/semantic_program/contract.py` — `_rang_buoc_lan_dau`

Sở hữu **ngữ nghĩa RÀNG BUỘC LẦN ĐẦU** của `assign` hình học, chạy ở tầng hợp
đồng nên mọi tầng sau chỉ thấy một dạng chuẩn tắc (cùng khuôn
`_nang_declare_point`).

    sinh ĐIỂM              → viết lại thành `construct_point`  (1:1)
    sinh vectơ/đường/mặt   → giữ `assign` + bổ sung khai báo
    vô hướng, giá trị thô  → KHÔNG đụng

Kiểu dẫn từ `_CHU_KY[k][1]`, không có bảng thứ hai. Vì sao hai đường: IR không
có `construct_vector`, và `construct_line` nhận hai TÊN ĐIỂM chứ không nhận
biểu thức — nên `assign` là lối duy nhất cho chúng và nó phải chạy.

Ba thứ cố ý không làm: **chỉ tầng ngoài cùng** (nâng trong `if`/`while` là mở
rộng nợ `RUNTIME_NONE_OPERAND_REACHABLE`); **không đụng vô hướng** (chúng
không qua kernel hình học và `_record_step` chụp cả scope nên bộ chấm vẫn
thấy); **không tự đăng ký giá trị thô** (nếu không thì đây là cửa sau của cổng
trung thực năng lực).

Hai ca không nâng được nay chết ở tầng TĨNH, nơi vòng sửa với tới:
`CONDITIONAL_UNINITIALIZED_TARGET` và `AMBIGUOUS_FIRST_BINDING`. Mã thứ hai
đóng lỗ `and that != "unknown"` trong `_kiem_ten` — một tên mang kiểu tĩnh
`unknown` từng lọt qua mọi phép kiểm toán hạng hình học rồi chết ở kernel.

Khoá bởi `tests/semantic_program/test_first_binding.py` (16 ca, gồm phép tiêm
lỗi hoàn nguyên `construct_point` → `assign` để chứng minh chuẩn hoá là thứ
đang giữ bất biến).

### `backend/scripts/audit_assign_binding.py` · offline

Bảng sự thật §1: bốn tầng × mỗi dạng `assign`, **đo** chứ không đọc mã. Cột
quyết định là *"giá trị nằm ở ĐÂU"* — `_set_var` đưa tên chưa khai vào
`scope_stack` còn kernel chỉ đọc `memory`, nên phép tính chạy đúng rồi câu
lệnh sau mới chết. Cột thứ hai là `provenance`, ô hay bị quên và là ô §5 cấm
mất.

### `backend/scripts/replay_first_binding.py` · offline

§11 — chạy lại 6 chương trình THÔ của `CLEAN_BASELINE_V1` dưới hợp đồng mới.
Không sửa chương trình, không đổi điểm live (giữ 2/6). Kết quả ghi dưới tên
riêng `OFFLINE_EXECUTABLE_AFTER_FIX`.

⚠️ Grounding ở đây **chỉ so được một nửa**: `probe.json` lưu tóm tắt hợp đồng
chứ không lưu `input_facts`, nên mọi `source_fact_id` đều không giải được và
`INPUT_NOT_GROUNDED` nổ kể cả cho ca đã QUA ở lượt live. Mã trung thực thì so
được (chỉ phụ thuộc `problem_text`) nên vẫn dừng; mã kia chỉ được ghi rồi đi
tiếp.

### `translate(point3, vector3) → point3` · **live** — phép affine của IR

Phép dựng điểm thứ SÁU, thêm 2026-09-01. Nằm ở `kernel.translate` (nhân),
`contract.TranslateExpr` (**cả** `PointExpr` lẫn `ValueExpr`),
`ir_static_check._CHU_KY` (chữ ký), `geometry_exec` (điều phối). Validator,
thẻ văn phạm và provenance đều **dẫn xuất** từ `_CHU_KY`, không bảng thứ hai.

**Vì sao nó tồn tại, và vì sao bằng chứng không phải "mô hình hỏng":**
`SYNTHESIS_STABILITY_K3` đếm 10 lần mô hình viết `construct_point X = arith(+,
var(P), vector_from_points(A,B))` rồi chết ở schema — đó là bằng chứng nó
MUỐN phép ấy. `scripts/audit_translation_gap.py` chứng minh câu còn lại **từ
văn phạm**: không phép sinh điểm nào nhận vectơ, và không câu lệnh nào dựng
đường/mặt từ một điểm + một phương, nên cả đường vòng *"dựng đường qua P
phương v rồi chia đoạn"* cũng đóng (`construct_line` cần hai TÊN ĐIỂM, tức
cần sẵn chính điểm ta muốn dựng).

⇒ Trước phép này `vector3` là kiểu **CHỈ-GHI**: dựng được bằng
`vector_from_points` nhưng không phép dựng nào tiêu thụ, chỉ `angle_cos` đo.

⚠️ **ĐÍNH CHÍNH 2026-09-01 — đó là câu KIỂU, không phải câu NGỮ NGHĨA.**
Báo cáo đầu kết luận `PRE_EXTENSION_EXPRESSIBLE = NO` từ bằng chứng kiểu. Sai:
IR cũ **có** biểu diễn được phép tịnh tiến bằng tổ hợp

    M = midpoint(P, S)
    Q = divide_segment(R, M, 2)      →  R + 2(M − R) = P + S − R

đúng bằng `translate(P, vector_from_points(R, S))`. Đã kiểm chạy
(`audit_translation_gap.audit_to_hop`).

⇒ `translate` là phép **dễ tìm và đúng nghĩa**, KHÔNG phải một năng lực mới.
Lý do giữ nó vẫn đứng, chỉ là một lý do khác và yếu hơn lý do đã khai: đường
vòng dùng `divide_segment` với tỉ lệ `2` để đi RA NGOÀI đoạn, trong khi hợp
đồng của phép ấy khai `t=0 → A, t=1 → B` và nêu nó là miền hợp lệ của thao tác
kéo. Nó chạy, nhưng nó nói dối về việc nó làm gì — và mô hình chưa lần nào tìm
ra nó trong 18 quan sát.

**Hai trường đều là TÊN**, đúng bất biến `test_R0_bieu_thuc_hinh_hoc_chi_nhan_
TEN` — nhận biểu thức lồng là mở đường cho toạ độ đi thẳng từ LLM vào. Muốn
`translate(A, vector_from_points(B,D))` thì viết hai câu; `assign v = …` tự
đăng ký nhờ hợp đồng ràng buộc lần đầu nên không tốn khai báo nào.

**KHÔNG nới `arith`.** `arith` là phép trên ĐẠI LƯỢNG; cho nó nhận điểm và
vectơ là biến nó thành đại số hình học quá tải, nơi `ĐIỂM + ĐIỂM` cũng "chạy"
mà không có nghĩa affine. `LEGACY_ARITH_TRANSLATION_NORMALIZATION = NO`:
payload ấy chưa bao giờ schema-hợp-lệ, nên không có gì để tương thích ngược.

Khoá bởi `tests/geometry/test_translate.py` (26 ca). Ràng buộc thiết kế của
file ấy: **không chỉ kiểm các hình dạng của bộ V2** — nếu thế thì ta đã thêm
một module theo dạng bài và gọi nó là primitive.

### `backend/scripts/audit_translation_gap.py` · offline

Chứng minh khoảng trống **từ văn phạm**, không từ việc mô hình hỏng: đọc
`_CHU_KY` và `_TOAN_HANG_LENH`, hỏi ba câu cơ học (phép nào sinh điểm · trong
số ấy phép nào nhận vectơ · câu lệnh nào dựng đường/mặt từ vectơ). Chạy lại
sau khi thêm `translate` thì nó lật sang `YES` — tức chính nó cũng là guard.

### `backend/scripts/replay_translation_intent.py` · offline

§17 — dịch **cơ học** `arith(+, var(P), V)` → `assign v = V` +
`translate(P, v)` trên các chương trình hỏng đã lưu, rồi chạy qua chuỗi cổng.
Trả lời *"cùng ý định nay biểu diễn được"*, **không** phải *"mô hình đã
đúng"*: 6/6 chương trình, 12 câu lệnh. Điểm lịch sử không đổi.

### `backend/scripts/replay_demo_cases.py` · offline

Tập DEMO của khoá luận, chạy từ **chương trình đã lưu** trong artifact có xuất
xứ rõ. 0 lượt gọi model. Mỗi ca đi trọn chuỗi tất định: thẩm định → grounding +
trung thực → thực thi → checker → transport → Scene3D, và báo cả `producer`/
`depends` trên cảnh (xuất xứ có tới được mặt học sinh không).

Bảng `DEMO` mang cả ca `ky_vong="REFUSAL"`: **"đạt" nghĩa là bị chặn ĐÚNG CHỖ**,
không phải chạy được. Một demo chỉ toàn ca xanh giấu mất nửa luận điểm — hệ
phải nói KHÔNG có địa chỉ, và `n4` là chỗ trình bày điều đó.

`RUT_GON` đếm RIÊNG: `clean-baseline-v2` không lưu `RequestContract` nên ca
thiết diện `v2_04` bỏ được cổng grounding. Gộp nó vào `DEMO_REPLAY` là báo cáo
một chuỗi đủ mà thực ra thiếu một cổng.

### `backend/scripts/audit_demo_crash_surface.py` · offline

Sáu biên **đã từng hỏng thật** trong kho này, mỗi ca kèm nơi nó hỏng — hỏi đúng
một câu: *có đầu vào xấu nào làm hệ CHẾT thay vì TỪ CHỐI không?* Kết quả
2026-09-01: **6/6 đúng tầng chặn, 0 đường ném ra ngoài**.

⚠️ **KHÔNG phải fuzzing** — thêm ca thứ bảy "cho chắc" là mở một bề mặt kiểm
thử mới. Và mỗi ca phải kiểm ĐÚNG thứ nó nói: bản đầu của ca `angle_cos` không
khai `d` nên bị chặn vì *"tên chưa khai"* chứ không vì *sai kiểu* — xanh mà
không chứng minh gì.

### `backend/scripts/name_slot_classifier.py` · offline

Phân loại **từng ô TÊN trong đầu ra THÔ** của mô hình — metric chính của
`NAME_ONLY_CONTRACT_LIVE_PROBE`. Export: `LOAI` · `phan_loai_o_ten` ·
`toa_do_ky_hieu`. Năm kết cục, ĐÓNG: `RAW_NAME` · `WRAPPED_VAR` ·
`NESTED_DERIVED_EXPR` · `RAW_LITERAL` · `WRONG_TYPE`.

⚠️ **KHÔNG gộp `WRAPPED_VAR` với `NESTED_DERIVED_EXPR`** — một cái là cái tên
viết dài ra (gỡ bọc 1:1), cái kia là một phép dựng đặt nhầm chỗ (phải nâng).
Gộp là mất đúng thứ phân biệt *"không biết cú pháp"* với *"không biết tách câu
lệnh"*. `RAW_NAME` nghĩa là đúng hình dạng wire **và** kiểu tương thích khi
kiểu suy được từ chính chương trình thô; kiểu không suy được thì vẫn tính
`RAW_NAME` vì cái sai kiểu đã có thẩm định tĩnh bắt — không đếm hai lần.

Đã kiểm ngược trên dữ liệu biết đáp án trước khi dùng: 4 lời giải chuẩn tắc ra
100% `RAW_NAME`; `t3`/`t4` của translation probe ra đúng 4 và 1 lần lồng;
chương trình `dihedral-probe-ergonomics` ra `WRAPPED_VAR=14` và `WRONG_TYPE=2`
đúng chỗ `angle_cos` trên `line3`.

### `backend/scripts/name_contract_probe_cases.py` · offline

Bốn đề của `NAME_ONLY_CONTRACT_LIVE_PROBE` + `check_contamination()` (quét thêm
`translation-probe`, `named-operand-ergonomics`). Không đề nào nói *"tịnh
tiến"*/*"vectơ"* — nói là đọc hộ mô hình phần khó. `n3` cố ý **không cần**
`translate`, để hỏi `NAME<T>` có tổng quát hay chỉ đúng với phép vừa nhìn thấy.

⚠️ Hai oracle đã bị **thay trước khi seal vì không phân biệt được lời giải
sai**: bản đầu của `n3` hỏi cos² góc giữa `AE` và `(AEF)` — `AE` nằm trong mặt
ấy nên đáp số là 1 với BẤT KỲ mặt nào qua `A`,`E`, tức một `F` dựng sai vẫn
đúng số; bản đầu của `n1` đặt cả hình trong mặt `z=2`, và khi ấy một `Q` phản
chiếu cho đúng cùng khoảng cách. Một oracle không phân biệt được lời giải sai
thì không đo được gì.

### `backend/scripts/run_name_contract_probe.py` · **live — TIÊU QUOTA**

Runner của probe. Trần TUYỆT ĐỐI 8 lượt (4 analyze + 4 tổng hợp), **0 lượt
sửa** — lượt thứ hai bị chặn TRƯỚC khi gửi. Tách hai kết luận không gộp:
`RAW_CONTRACT_COMPLIANT` (mô hình viết gì) vs `ONE_SHOT_CORRECT` (hệ chạy được
không); một chương trình raw KHÔNG đúng hợp đồng mà vẫn đúng nhờ chuẩn hoá là
kết quả HỢP LỆ, ghi `NORMALIZER_RESCUED_PROGRAM`.

`--dry-run` chạy với **provider giả** cố ý phát bản lồng + bọc `var`, 0 token.
Bắt buộc chạy trước mỗi lượt live: hai wave gần nhất đều vỡ giữa lượt live vì
lỗi bộ đo (`__call__` thay `emit`; giả định toán hạng là chuỗi), và lượt chạy
khô ở đây bắt được lỗi thứ ba — `VAR_UNWRAPS` đếm gấp đôi vì chương trình được
thẩm định hai lần trong một ca.

### `backend/scripts/audit_named_operand_ergonomics.py` · offline

Hai câu, 0 lượt gọi model. ① **Ô nào của IR hình học đòi một TÊN** — dẫn từ ba
bảng thẩm quyền (`_CHU_KY` · `_TOAN_HANG_LENH` · `_KIEU_DO`), in 30 ô kèm
`NAME<T>`. ② **Những lần mô hình LỒNG một thứ vào đúng các ô ấy** — quét mọi
chương trình THÔ trong `docs/evaluation/geometry/**`, phân loại BA đường:
`HOISTED` (nâng thành temp) · `NAME_REF_UNWRAPPED` (gỡ bọc `var`) · `REJECTED`.

Kết quả 2026-09-01: **23 lần lồng, 7 nâng + 16 gỡ bọc, 0 từ chối** — tức lớp ma
sát ĐÔNG NHẤT không phải biểu thức lồng mà là `{"kind":"var"}` bọc quanh một
tên. Ba đường phải tách: gộp `var` vào "bị từ chối" là báo cáo sai chuyện đang
xảy ra, và bản đầu của script này đã sai đúng thế.

### `backend/scripts/replay_nested_operand_history.py` · offline

§18/§19 — lấy nguyên chương trình thô model từng phát ra (artifact đã commit,
**không sửa một byte**), cho qua lớp chuẩn hoá mới rồi qua đúng chuỗi cổng sản
phẩm: schema → tĩnh → grounding + trung thực → thực thi → transport.

Đo *"hệ HÔM NAY làm gì với đầu vào HÔM QUA"* — một câu hỏi khác *"lượt ấy được
mấy điểm"*, nên phải gọi bằng tên khác và **không** đổi điểm lịch sử. Không có
đề trong artifact thì BỎ QUA grounding thay vì bịa một đề để cổng chạy được.

Kết quả: 5 chương trình có toán hạng lồng, `EXECUTABLE_AFTER_NORMALIZATION =
2/5`. Ba ca dừng là lỗi ngữ nghĩa THẬT của mô hình (`angle_cos` trên `line3` ×2,
toạ độ ký hiệu ×1) và **cả ba bị bắt trước runtime** — chuẩn hoá không che ca
nào. Chính lượt chạy này lộ ra lỗ toạ độ ký hiệu, nay bịt ở `_kiem_toa_do`.

### `backend/app/simulation/semantic_program/measure_contract.py` · **live**

Sở hữu **kiểu toán hạng, arity và ngữ nghĩa của `measure`** — một bảng,
bốn người đọc: `validator` · `ir_static_check._KIEU_DO` (dẫn xuất) ·
`grammar_card` (render cho mô hình) · thông điệp sửa.

Trước nó luật *"`angle_cos` chỉ nhận vectơ"* được viết **ba lần** (validator,
`_KIEU_DO`, nhánh `isinstance` của kernel) và **không lần nào gửi cho mô
hình**. Giá đã trả hai lần: `vector3` thêm vào `_CHU_KY` mà quên `_KIEU_DO`
⇒ chương trình dựng vectơ ĐÚNG bị từ chối, 4 lượt live chết; và thẻ không nói
kiểu ⇒ `angle_cos` trên `line3` **14 lượt / 220.898 token** (AUDIT).

Hai luật của bảng: **model-facing HẸP HƠN runtime-accepted** (`angle_cos_sq`
chỉ khai `line3|plane3` dù `_DOI_TUONG` rộng hơn — kernel chỉ có nhánh cho
đường và mặt, nên "để kernel quyết" chỉ dời lỗi sang lúc chạy, mà lỗi runtime
KHÔNG được gửi ngược để sửa); và **ngữ nghĩa, không từ khoá** (`nghia` tuyệt
đối không nhắc "nhị diện"/"côsin", vì tên `angle_cos` tự nó đã là một từ khoá
kéo mô hình về phía sai).

⚠️ **Quy kết đã sửa.** 14 lượt hỏng ấy KHÔNG do bảng "nhị diện" trong
`geometry_program_generator.md`: hai tuyến đo sinh ra chúng chạy với
`domain="geometry"`, tức nhận prompt **Tin học**, và chưa bao giờ thấy bảng
ấy. Thứ chúng thấy là dòng enum trần trong thẻ. Xem
`docs/evaluation/geometry/fresh-probe/FRESH_PROBE_REPORT.md §0`.

Ranh giới tầng: validator chỉ canh phép đo nhận `vector3`, vì `vector3` và
`point3` cùng là `Vec3` ở runtime nên khác biệt "có hướng" **chỉ tồn tại ở
tầng khai**. Phần còn lại thuộc `ir_static`/kernel. Khoá bởi
`test_measure_contract.py` (15 test).

**MỘT OPCODE = MỘT ĐẠI LƯỢNG, từ 2026-09-01.** `angle_cos_sq` từng trả cos²
cho ba cặp toán hạng và **sin²** cho cặp (đường, mặt) — một tên, hai đại
lượng, và nửa nói dối **không tự khai ra** vì ở 45° thì cos² = sin². Nay cos²
ở cả bốn cặp qua `measure.cos_sq_giua`. Chi tiết + phạm vi migration:
`docs/evaluation/geometry/ANGLE_SEMANTICS_ERRATUM.md`.

### `backend/app/simulation/geometry/measure.py` — `cos_sq_giua` · **live**

Thẩm quyền DUY NHẤT của phép phân phối góc theo cặp kiểu. Trước nó phép ấy
được viết **hai lần**: `geometry_exec._do` (đường thực thi) và
`geometry_obligations.check_angle` (đường chấm) — và bản sao mang **cùng** con
bug, nên bộ chấm tính lại *cùng một đại lượng sai* và xác nhận thay vì bác bỏ.
Một bộ chấm chép luật của thứ nó chấm thì chỉ chấm được lỗi gõ nhầm.

`cos_sq_line_plane = 1 − sin_sq_line_plane` — phép trừ đi hết trong ℚ nên vẫn
chính xác. `angle_sin_sq` **không** được mở: chỉ thị cho phép cả hai đường, và
đường này ít bề mặt trôi hơn (không đổi schema, không thêm từ vựng cho mô
hình, bộ chấm không cần biết chương trình chọn opcode nào).

Khoá bởi `tests/geometry/test_angle_semantics.py` (27 test). Ràng buộc thiết
kế của file ấy: **mọi ca dùng góc 0° hoặc 90°** — ca 45° không phân biệt được
cos² với sin², nên một bộ test chỉ chạy 45° sẽ báo XANH cho đúng con bug này.

### `backend/tests/semantic_program/test_contract_self_check.py` · offline

`PROMPT_ADVERTISES_NONEXISTENT_IR = impossible`. Quét bề mặt mô hình THẬT SỰ
nhận (skill hình học + thẻ văn phạm) và đòi mọi định danh trong backtick phải
tồn tại ở schema.

Nguồn: `fresh-probe fp_6` phát `{"kind":"perpendicular"}` **cả hai lượt** rồi
hết ngân sách — vì prompt có bảng liệt kê `parallel`/`perpendicular`/
`coplanar` dưới cột "Nghĩa vụ" kèm cột "witness", trong khi
`SemanticProgramSpec` **không có trường `obligations`**. Nghĩa vụ do `analyze`
sinh ở phía HỢP ĐỒNG; mô hình tổng hợp không có ô nào để viết chúng.

Guard này bắt cả prompt sửa lỗi ấy: bản đầu của tôi viết *"đừng phát
`perpendicular`…"* — nêu một token để cấm vẫn là gieo nó. Luật nay nói ở dạng
khẳng định, không nhắc tên.

### `backend/scripts/audit_angle_semantics.py` · offline

Bảng sự thật của `angle_cos_sq` — **đo trên hình biết trước đáp số, không đọc
mã**, vì cả wave sinh ra từ chỗ tài liệu và máy lệch nhau. Cộng phép quét §8:
chương trình đã lưu nào dùng cặp (đường, mặt).

⚠️ Bản quét ĐẦU báo **0 ca** vì chỉ đọc `memory_declarations`, trong khi `fp_5`
dựng toán hạng bằng câu lệnh `construct_*`. Một con số "sạch" sinh ra từ một
bộ quét mù — `_kieu_cua` nay gom kiểu từ cả hai nguồn.

### `backend/scripts/replay_fresh_probe_contract.py` · offline

Replay §13/§16: `fp_5` (cùng JSON, 1/3 → **2/3**, khớp oracle) và `fp_6` (vẫn
không validate — đúng như thế; điều sửa là bề mặt thôi quảng cáo, không phải
schema nhận thêm). Không đổi điểm live, 0 API call.

### `backend/scripts/audit_synthesis_failures.py` · offline

Gom mọi lượt hỏng đã lưu của ba tuyến đo (dihedral probes · declaration-merge ·
generalization matrix) rồi xếp theo **BỆNH**, không theo tầng cổng — `gate`
nói được lượt hỏng ở tầng nào, không nói được vì sao, và bốn ca "SCHEMA" có
thể là bốn bệnh khác hẳn. Mỗi khuôn kèm quy kết `PROMPT|MODEL|SYSTEM` **có lý
do viết ra** để người sau cãi được. Kết quả 2026-08-31: 43/49 lượt xếp được,
PROMPT chiếm 59%.

### `backend/scripts/replay_contract_effect.py` · offline

§11 — hỏi *"hợp đồng mới có NÓI RA điều mà mỗi lượt hỏng cũ vi phạm không"*.
**Không** sửa chương trình cũ rồi tính thành công. Mỗi phán quyết `CAN_NGAN`
phải chỉ ra một chuỗi CÓ THẬT trong thẻ đang chạy, nếu không tự hạ cấp —
`test_measure_contract.test_bang_chung_offline_replay_con_nguyen_trong_the`
biến việc mất chuỗi ấy thành ĐỎ thay vì một dòng báo cáo lặng lẽ sai.

### `backend/scripts/fresh_probe_cases.py` · offline

Sáu đề TƯƠI cho probe §13–§14, kèm oracle tính tay và `check_contamination()`
đối chiếu pool holdout đã niêm phong. Guard hỏi **hai** câu tách bạch: chép
nguyên văn (14-gram cả đề) và trùng câu hỏi (8-gram trong mệnh đề HỎI) — bản
một-câu-8-gram báo 5/6 nhiễm mà mọi cụm đều là văn mẫu SGK (*"có đáy ABCD là
hình vuông cạnh"*). `DA_PHAN_XU` giữ phán quyết tay **kèm lý do đối chiếu cụ
thể** cho ca trùng đúng tên chuyên đề (A09/A13) — trong repo, không trong đầu.

### `backend/app/simulation/semantic_program/route.py` · offline

Sở hữu **thứ tự các cổng tất định** của route và **phán quyết cuối**:
P2 → C₁a → thực thi → C₁b → C₂ → biên dịch. Trả `SemanticRouteOutcome` mang HAI
cờ tách hẳn nhau — `executable` (máy chạy được không) và `servable` (đủ bằng
chứng phát canonical chưa); gộp chúng là bóp hai tỉ lệ của luận văn thành một.
Không có lượt LLM nào ở đây. Điểm dễ sai đã ghi trong file: C₁a trả `ok=False`
cho **cả** mức yếu, nên chỉ `REQUESTED_OPERATION_UNCOVERED` mới được chặn.

### `backend/app/ai/skills/semantic_analyze.md` · **live**

Prompt của `stage_semantic_analyze` — đề bài → dữ liệu đề cho + nghĩa vụ. **Tách
hẳn `analyze.md`** để đề đi đường module không phải trả tiền cho từ vựng nghĩa
vụ. Không được gộp vào lượt viết IR: một lượt sinh cả nghĩa vụ lẫn chương trình
thì C₁a tự đối chiếu một nguồn với chính nó.

### `backend/scripts/build_geometry_demo_artifact.py` · offline (HARNESS)

Sinh **demo artifact** miền hình học từ một lượt đo ĐÃ CHẠY — không chấm lại,
không sửa gì, **0 API call**. Ghép `scene3d` vào bên cạnh `input_text` ·
`semantic_program` · `validation` · `simulation_steps` · `oracle_result` để đọc
trọn chuỗi trong một file.

Đọc lại artifact thay vì chạy mới vì câu hỏi Phase 5G là *"AI có sinh được quá
trình hình thành hình học không"* — chỉ trả lời được bằng thứ **AI thật sự đã
viết**; chạy lại chỉ tốn quota để lấy một bộ IR khác rồi phải chọn giữa hai bộ.

⚠️ `_phan_loai` phân biệt **CONTRACT vs MODEL** ở tầng schema thay vì gộp: 3/4
ca trượt schema ở lượt W4 là CÙNG lỗi `construct_solid.faces` nhận tên đỉnh —
lỗi HỢP ĐỒNG (đã vá ở 5A), không phải *"AI viết sai IR 4 lần"*. Hai câu ấy dẫn
tới hai wave sửa hoàn toàn khác nhau.

### `backend/scripts/api_usage_log.py` · offline (HARNESS)

Sở hữu **chi phí của một lượt đo**: bọc `pipeline.call_gemini` để lấy độ trễ và
**đầu ra thô**, gộp token từ `telemetry.usage_report()`, quy ra USD. Là harness —
`GhiNhanApi.boc()` gọi thẳng hàm gốc và trả nguyên giá trị gốc, ngoại lệ bay qua
nguyên vẹn (và vẫn được tính giờ: lượt 429 là lượt đắt nhất). Ra đời vì PHASE 5
chạy trọn 10 bài rồi **không ghi được nó tiêu bao nhiêu**, dù `telemetry.py` đã
đếm sẵn và docstring của nó bảo phải gọi.

Hai luật giữ cho con số không thành hư cấu: bảng giá + **ngày tra + nguồn** đi
kèm vào artifact (con số USD trong `docs/evaluation/` phải tái lập được sau
nhiều tháng); và model ngoài bảng ⇒ `uoc_tinh_duoc: false`, **không** phải `0.0`.
Ước tính là CHẶN TRÊN, khai rõ trong `khai`. Giữ đầu ra thô vì khi IR trượt
schema, `stage_semantic_program` vứt nó đi và chỉ còn chuỗi lỗi Pydantic — PHASE 5
phải dựng lại *"mô hình bịa `construct_plane`"* từ dấu vết thay vì từ vật chứng.

### `backend/app/ai/skills/geometry_analyze.md` · **live**

Bản của `semantic_analyze.md` cho **miền hình học** — chọn bằng
`domain_profile.analyze_skill_for`. Ba thứ nó dạy mà bản Tin học không dạy được:
dữ kiện hình học có HAI dạng (số đo và **quan hệ** như `SA ⊥ (ABCD)`); bảng dịch
8 nghĩa vụ kèm cột `witness` (nhóm quan hệ nhận ĐỐI TƯỢNG, nhóm đại lượng nhận
CON SỐ); và luật **hệ toạ độ KHÔNG phải dữ kiện** — không nói thì `analyze` khai
`A = (0,0,0)` thành `input_fact` và cả chuỗi provenance ghim vào thứ đề không có.
Ra đời sau Phase 5, nơi 3/6 chương trình hợp lệ khai nghĩa vụ Tin học cho bài
hình học vì enum cũ liệt kê cả 19.

### `backend/scripts/ocr_sgk_ingest.py` · **live** (Cloud Vision), có CACHE

Đọc SGK bản QUÉT thành text. Năm cuốn trong `data/knowledge/sources/` không có
lớp chữ — `pdftotext` trả 60 ký tự cho 60 trang, đúng bằng số dấu ngắt trang.
Repo **không có** RAG/index/cache nào để tái dùng, và `app/ingestion/input.py`
là lớp chuẩn hoá input của **sản phẩm** (text/docx/ảnh), không đọc PDF.

Đường đọc: PyMuPDF dựng ảnh trang → Cloud Vision `document_text_detection`.
Credential lấy từ `.secrets/` qua `GOOGLE_APPLICATION_CREDENTIALS`; **không in
và không ghi** giá trị secret vào artifact.

**Cache là điểm chính**: mỗi trang OCR đúng một lần rồi ghi vào
`data/knowledge/ocr-cache/<sách>.json`. `data/` bị gitignore nên text SGK không
vào kho mã. `--stats` báo trạng thái cache mà **không tốn call nào**.

### `backend/scripts/validate_sealed_submission.py` · offline, CUSTODIAN chạy

Kiểm **hình dạng** tập SEALED trước khi niêm phong: trường thiếu, `case_id`
trùng, `obligation_kind` sai chính tả, 4 metadata guard, và dạng `expected` cũ
`{tên_biến: giá_trị}` (bị bỏ vì tên biến do LLM đặt). Tách khỏi runner có chủ
đích — runner chạy một lần, còn cái này chạy bao nhiêu lần cũng được vì không
gọi API.

**Cố ý KHÔNG kiểm** phạm vi đề và tính đúng của ground truth: ground truth mà
máy kiểm được thì không còn độc lập. Khoá bởi `test_sealed_validator.py`, gồm cả
một test chống chính nó tự nhận là bộ chấm.

### `backend/scripts/run_sealed_evaluation.py` · **live**, chạy ĐÚNG MỘT LẦN

Runner Task 12. Kiểm candidate + vân tay con dấu **trước** khi mở SEALED, chạy
`run_pipeline(semantic_route="shadow")` nên MỘT lượt đo được cả hai route. Ngân
sách 440 logic / 520 HTTP cưỡng chế qua `gemini.ApiBudget` (dùng lại, không viết
bộ đếm mới). Viết **trước** khi thấy SEALED có chủ đích; phần chấm/tổng kết được
khoá offline bởi `tests/semantic_program/test_sealed_runner.py` vì chạy lại là
mất tính held-out.

Bốn thứ trong đây dễ bị viết sai vào luận văn, nên mỗi thứ có một test khoá:
**A−B phải phân rã** (chỉ một nhánh là `verification_gap`) · **B là
STRONG-assurance nội bộ, không phải "đúng"** (oracle độc lập báo riêng, và case
`servable` mà oracle nói sai được nêu đích danh) · **D1 là claim CẤU TRÚC**
(số lượt LLM đứng yên khi số bước trải rộng; token/case chỉ là telemetry hỗ trợ)
· **N=40 khoá**, chạy thiếu thì `evaluation_complete: false` và A/B không được
công bố như kết quả chính.

**`--dataset dev` (2026-08-24) — đường đo KHÔNG cần seed của GVHD.** 20 case ở
`dev/cases.json`, tập tự khai *"DEV **được nhìn**; SEALED thì không"*. Chạy nó
**không đốt** pool 49 bài held-out và **không cần** seed, nên nó là cách duy
nhất biết A/B của hệ hiện tại trước lượt #2. Ba khác biệt so với đường sealed,
đều cố ý: bỏ `_kiem_seal()` (DEV không có con dấu — giả vờ có là nói dối xuất
xứ) · **vẫn** `_kiem_candidate()` (chạy trên cây đã trôi thì số không gắn với
bản nào) · trần riêng `TRAN_LOGIC_DEV`/`TRAN_HTTP_DEV` = 260/310, **dẫn từ cùng
call graph** với N=20 nên đổi một trần không kéo trần kia theo.

⚠️ **Số của DEV không bao giờ là số của luận văn**: hệ đã được chỉnh trên chính
20 case này. Nó trả lời đúng một câu — *bốn biên chuẩn hoá + vòng sửa có làm
phễu thông hơn không*. Oracle sẽ **UNGRADED toàn bộ**: ground truth của DEV còn
ở định dạng cũ (khoá theo TÊN BIẾN), không phải hợp đồng nghĩa-vụ + giá-trị mà
`_cham` đòi — và **không được tự chuyển đổi**, viết lại ground truth là việc của
custodian. Báo cáo tự đeo `dataset` + `canh_bao_dataset`; đầu ra mặc định vào
`dev-results/`, và có **chặn cứng** không cho DEV ghi vào `results/`. Khoá bởi
ba test mới ở `test_sealed_runner.py` §7.

**ĐÃ CHẠY 2026-08-23 — lượt duy nhất, không được gọi lại.** Artifact ở
`docs/evaluation/semantic-benchmark/results/`:

- `sealed_summary.json` — số tổng hợp (A/B/A−B/oracle/D1/D2/ngân sách).
  **Hai khối thêm 2026-08-24, đọc được từ LƯỢT #2 trở đi**:
  `token_dau_ra_theo_route` (token ĐẦU RA = `candidates` **+** `thoughts`, tách
  route sinh ↔ route module — bỏ `thoughts` là báo thấp đi gần ba lần, nó lớn
  hơn `candidates` 2,6× ở stage `semantic_program`; vẫn là telemetry HỖ TRỢ,
  **không** phải D2 vì hai route chạy trên hai population khác nhau) và
  `coercion_rate` (bốn biên chuẩn hoá nổ bao nhiêu lần — xem `coercion_stats.py`).
  Lượt #1 **không có** hai khối này, nhưng token đầu ra của nó vẫn tính lại được
  từ `sealed_cases.json[].token` vì `record_usage` đã ghi đủ năm trường ngay từ
  đầu.
  **Khối thứ ba, 2026-08-24**: `reliability_v2` (8 tầng thất bại + G1/G2/A/R/B/
  V/O) — xem `reliability_v2.py`. Đặt CẠNH `A_generative_executability` và
  `B_internal_servable`, **không thay** chúng: hai cái ấy là chỉ số duy nhất so
  trực tiếp được với lượt #1. Khoá bởi `test_sealed_runner.py §8`
  (`_KHOA_CU` — mất một khoá cũ là ĐỎ).

**Runner BỌC `stage_semantic_program` từ phía harness** để bắt
`SemanticProgramSpec` cho replay. Observer không mang spec, mà phát thêm spec ra
observer là sửa `pipeline.py` — tức sửa engine. Proxy đi qua nguyên vẹn, chỉ ghi
lại, và **khôi phục trong `finally`**: một case ném lỗi mà để lại proxy thì case
sau chạy qua hàm đã bọc chồng nhiều lớp, mỗi lớp thêm một lượt LLM. Khoá bởi
`test_proxy_bat_spec_KHONG_ro_ri_sang_case_sau`.

**Tầng ⑦ (renderer) KHÔNG chạy ở đây** — `renderer_V` luôn `None` ở pha A. Nó
thuộc pha B (trình duyệt, 0 call LLM), chạy lại được mà không phải tiêu quota
lần nữa.
- `sealed_cases.json` — 40 bản ghi case-level: `semantic` (stage_reached,
  executable, servable, error_code, reason), `legacy` (route module để so),
  `contract` (nghĩa vụ khai), `cham` (verdict oracle), `token` theo stage.
- `OFFICIAL_RESULT.md` — **bản diễn giải chính thức, nguồn trích cho luận văn**.
  Chứa cảnh báo bắt buộc: 17/40 case chết ở `spec_version` float vs
  `Literal["1.0"]`, nên A = 3/40 là cận dưới của cận dưới.

Gọi lại runner sẽ ghi đè artifact và **phá tính held-out** — muốn đo lại phải
niêm phong SEALED MỚI, không phải chạy lại tập cũ.

### `backend/app/ai/telemetry.py` · offline

Sở hữu **bộ đếm token theo stage**. Dùng `ContextVar` (`stage_scope`) chứ không
thêm tham số vào `call_gemini`: hàm đó có 13 test double, và một double gãy vì
production thêm tham số QUAN TRẮC là mùi thiết kế.

### `backend/app/ai/route_trace.py` · **live**

Sở hữu **chuỗi sự kiện của một lượt phân tích** — route ngữ nghĩa có chạy
không, tới đâu, chết vì gì. Khác `telemetry.py` (đếm token): file này ghi
*chuyện gì đã xảy ra*. Vòng đệm 20 lượt trong tiến trình, đọc qua
`GET /api/diagnostics/semantic`, bật bằng `SEMANTIC_TELEMETRY=1`.

**Bất biến: mọi thứ trong `_kho` đều `json.dumps` được**, do `_json_an_toan`
giữ, hạ MỘT LẦN ở `ket_thuc` (không ở `emit` — `ket_cuc` đọc thẳng từ envelope
nên sẽ lọt; không ở endpoint — mỗi người đọc `_kho` lại phải tự nhớ).
`Fraction` → chuỗi phân số **không hoá float** (cùng quy ước `scene3d`); kiểu
lạ → `repr`, không ném.

Vì sao bất biến ấy phải là bất biến: `semantic_route` phát kèm `final_memory`,
mà bộ nhớ cuối của interpreter hình học chứa `Fraction`/`Vec3`/`Line3`/`Plane3`
— và nó **chỉ** được phát khi route đi đủ xa. Nên trước bản vá, endpoint chẩn
đoán trả 500 **đúng vào lượt hình học CHẠY ĐƯỢC**, còn lượt hỏng thì đọc bình
thường. Khoá bởi `tests/test_route_trace_json_safe.py`.

### `backend/scripts/seal_benchmark.py` · offline

Khoá/kiểm fingerprint của SEALED benchmark. Thoát != 0 khi seal vỡ.

### `frontend/src/simulations/domains/semantic/` · offline

`model.ts` — đọc frame timeline, **không** tính lại bước; `validateSemanticConfig`
kiểm lại bất biến #32 ở phía nhận (envelope có thể đến từ lịch sử đã lưu).
`ui.tsx` — renderer 2D chỉ ĐỌC khung; `DoThi` vẽ `graph_view` bằng layout vòng
tròn TẤT ĐỊNH (không physics/camera/editor), và `visited`/`current` đến TỪ
BACKEND — renderer không được tự chạy lại BFS. `index.ts` — đăng ký module,
**shadow-only** cho tới hết Task 12.

### `frontend/scripts/l5a-semantic-visual.mjs` (L5a) · cần Chrome + `npm run dev`

Sở hữu **soát thị giác đại diện** của route semantic: 4 ca × 2 bề rộng, đo
`getBoundingClientRect()` thay vì so ảnh pixel (repo không có `@playwright/test`).
Năm phép đo: chữ đè chữ · tràn/clipping · con trỏ chui vào nhãn · **chữ lặp** ·
khung ĐỔI sau 6 bước. Có `--faultcheck` để chứng minh guard đỏ được — bắt buộc
chạy trước khi tin một bản soát "SẠCH" (`ARCHITECTURE_MAP §8` #14). Fixture
`frontend/tests/fixtures/semantic/semantic_l5a.json` **sinh từ backend thật**,
không viết tay. (Trước vNext nó nằm ở `public/` nên bị Vite chép thẳng vào
`dist/` — script đọc nó bằng `fs`, chưa bao giờ qua HTTP. Khoá bởi
`src/public-assets-hygiene.test.ts`.)
Kết quả: `docs/evaluation/semantic-l5a/`.

### `frontend/scripts/capture-stack-vnext.mjs` · cần Chrome + `npm run dev`

Bằng chứng trình duyệt thật cho kịch bản Stack vNext: kiểm tra trạng thái tương tác
thay đổi thật sự khi bấm chuyển bước (khắc phục điểm mù của SSR renderToString).
Đo đạc dấu vân tay trang, kiểm tra render ngăn xếp qua Playwright và hỗ trợ `--faultcheck`.


### `backend/scripts/thesis_acceptance_corpus.py` · offline · **0 API call**

Bộ ca ĐÁNH GIÁ CUỐI của khoá luận (`THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION`,
2026-09-08). Bảy ca dương + hai ca âm, CỐ ĐỊNH — không seed, không rút thăm.
Export: `CA_DUONG` · `CA_AM` · `HO_TRONG_PHAM_VI` (10 họ trong phạm vi) ·
`PHU_THEO_HO` (phép phủ set-cover, DẪN XUẤT) · `theo_id` · `corpus_json` ·
`expected_results_json` · `CORPUS_HASH` · `EXPECTED_RESULTS_HASH` ·
`bam_chinh_tac`.

**`payload_gui_model(ca)` là đường DUY NHẤT được gửi cho mô hình**, và nó trả về
đúng một trường `problem_text`. Gold program, oracle, đáp số và mọi siêu dữ liệu
chấm điểm ở lại phía bộ đo — khoá bởi
`tests/geometry/test_thesis_acceptance_matrix.py::test_A4`.

### `backend/scripts/thesis_acceptance_oracle.py` · offline · **0 API call**

Oracle ĐỘC LẬP cho bộ ca trên. Luật cứng: **không import bất cứ thứ gì dưới
`app.`** — `geometry/` chính là thứ đang bị kiểm, nên một oracle gọi lại nó chỉ
chứng minh nó nhất quán với chính mình. Cổng: quét AST ở `test_B1`, đọc hằng số
`ORACLE_KHONG_DUOC_IMPORT` thay vì gõ lại danh sách.

Export: `the_tich_chop` · `dien_tich_shoelace_2d` · `dien_tich_da_giac_3d`
(`½|Σ Pᵢ×Pᵢ₊₁|`, đúng cho cả đa giác lõm) · `khoang_cach_diem_duong` ·
`khoi_cau`/`khoi_tru`/`khoi_non` · `thiet_dien_tron_cau` ·
**`elip_lay_mau_tru`/`elip_lay_mau_non`** (200 000 mẫu trên giao tuyến +
shoelace 3D — KHÔNG dùng công thức bán trục) · `doc_chuoi_hien_thi` (bộ phân
tích chuỗi hiển thị của riêng nó, ngữ pháp HẸP, dạng lạ thì NÉM) ·
`sai_so_tuong_doi` · `OracleError`.

### `backend/scripts/thesis_final_acceptance_plan.py` · offline · **0 API call**

Điều phối chín chặng dựng-và-kiểm kế hoạch đo cuối; ghi mọi artifact vào
`docs/evaluation/geometry/thesis-final-acceptance/`. Export: `do_danh_tinh` ·
`kiem_trang_thai_du_kien` · `dung_capability_matrix` · `dung_claims_matrix` ·
`phan_loai_bang_chung_lich_su` · `gold_preflight` · `_chay_gold` ·
`negative_preflight` · `scorer_preflight` · `runner_readiness` ·
`dung_identity_lock` · `dung_run_plan` · `_LOP_BANG_CHUNG`.

`runner_readiness()` ĐO trên mã nguồn `run_curved_acceptance.py` — 15 yêu cầu,
và verdict quyết định `NEXT_ACTION`. Nó không tự khai.

### `backend/scripts/policies/thesis_final_acceptance_policy.json` · offline

Ngưỡng + chính sách đo, KHOÁ TRƯỚC kết quả. Nạp bằng
`measurement_policy.doc_chinh_sach(<đường dẫn>)` — module chung KHÔNG phải sửa,
vì hàm ấy vốn đã nhận đường dẫn. Hai nhóm tiêu chí cố ý tách:
`mandatory_correctness_and_safety` (PASS/FAIL) và `behavioural_metrics`
(**mô tả, `no_threshold_by_design`**). Bản sao đối chiếu ở
`docs/evaluation/geometry/thesis-final-acceptance/EVALUATION_POLICY.json`, khoá
byte bằng băm chính tắc (`test_G6`) — cùng khuôn `test_schema_sync`.

### `backend/scripts/run_thesis_final_acceptance.py` · **entrypoint lượt đo cuối**

Runner của lượt đánh giá cuối (`THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT`,
2026-09-08). **Hai chế độ, không có mặc định gọi provider**: `--certify`
(provider stub, 0 lượt gọi thật) và `--live` (⚠️ tiêu quota). Không cờ nào ⇒ in
hướng dẫn rồi thoát.

Export: `BoDo` (bộ nạp bộ ca CỐ ĐỊNH, kiểm **tám** băm trước khi xử lý ca đầu) ·
`nap_bo_do` · `CanhGac` (cổng danh tính + ngân sách, chạy TRƯỚC mỗi lượt gọi) ·
`bao_provider` (vá `call_gemini` ở **cả** `app.ai.pipeline` lẫn `app.ai.gemini`,
hoàn nguyên trong `finally`) · `dang_bi_va` · `ghim_so_luot_tong_hop` ·
`chan_doan_san_pham` · `prompt_sua_chang_b` · `cham_mot_ca` · `chay_lut` ·
`bam_runner` · `RUNNER_ENTRYPOINT` · `RUNNER_MODULE_SET` · `NGUON_ARTIFACT`.

⚠️ **Chặng B TIẾP TỤC, không chạy lại**: nhận hợp đồng đã đóng băng + raw
candidate hỏng + chẩn đoán từ chặng A rồi tiêu đúng MỘT lượt sửa
(`analyze_calls_in_stage_b = 0`). `base` được **CHỤP** ở lượt tổng hợp đầu chứ
không dựng lại; chuỗi chẩn đoán thì dựng lại và bị khoá bằng **phép so BYTE**
với prompt sản phẩm thật (`test_thesis_runner_alignment.py` nhóm A).

⚠️ `RUNNER_HASH` chỉ băm **file entrypoint**. Đưa artifact `.json` vào sẽ tạo
vòng không hội tụ vì `IDENTITY_LOCK.json` chứa chính băm ấy.

### `backend/scripts/certify_thesis_final_acceptance.py` · offline · **0 API call**

Chứng nhận runner trên bằng **chính entrypoint** của `--live`, provider stub.
Export: `chung_nhan` · `dung_stub` · `NHAN` (15 nhãn) ·
`CHUOI_SU_KIEN_TOI_THIEU` · `_dau_vet_v3` (quét **AST**, không quét chuỗi —
bản quét chuỗi tự đỏ vì đọc chính docstring của nó) · `ANALYZE_CA_AM` ·
`_hop_dong_gold_khong_qua_bien` (nhãn `GOLD_CONTRACT_REACHABLE`) ·
`_canh_truoc_moi_goi` · `main_tu_runner`.

Lượt chạy LUÔN ở thư mục tạm; `--out-dir` chỉ nhận bản sao
(`CERTIFICATION.json` + `stub_*.json`).

### ⚠️ `acceptance_integrity.mo_run` — hai tham số THÊM (2026-09-08)

`duong_chinh_sach` (`None` ⇒ giữ nguyên hành vi V3) và `bo_sung` (khối trường
phụ gộp vào manifest, **không** nâng `ARTIFACT_SCHEMA_VERSION` — 1.2 là hợp
đồng về trường BẮT BUỘC). Đồng thời `kiem_ghim_bo_do` nay đọc
`threshold_policy_path` **từ manifest** thay vì hằng số V3; bản cũ làm mọi lượt
đo không-V3 báo `threshold_policy_hash TRÔI` vĩnh viễn.

### ⚠️ `plane_equation.chuan_hoa_dau_tru` — bản vá dấu trừ Unicode (2026-09-08)

`doc_phuong_trinh` trước bản này chỉ đọc được `-` ASCII; `−` (U+2212, dấu trừ
ĐÚNG của toán học), `–`, `—` đều trả `None`, VÀ phép nở span dừng giữa phương
trình rồi tạo ra một mặt phẳng **khác** — nên một chương trình đúng bị từ chối.
Ánh xạ **1:1** (không dùng `unicodedata.normalize`) vì `_ung_vien` trả lát cắt
của chuỗi gốc. `U+00AD` cố ý KHÔNG map. `point_coordinate.py` vốn đã đúng, nên
đây là ngoại lệ chứ không phải quy ước.

### `backend/scripts/score_thesis_final_acceptance.py` · offline · **0 API call**

Chấm LẠI một lượt đo cuối đã chạy, và đóng sổ artifact của nó
(`THESIS_FINAL_ACCEPTANCE_EXECUTION` §8–§9). Export: `cham_lai` ·
`song_anh_tu_artifact` · `bang_bam` · `so_telemetry` · `tong_ket_cuoi` ·
`TEN_THEO_DAC_TA`.

⚠️ **Vì sao tồn tại**: lượt chính thức `thesis-final-20260908T160224Z` báo
`SILENT_WRONG_ANSWER_COUNT = 6` trên một hệ **không phạm lỗi nào** — bộ chấm tra
đáp số bằng `final_memory[<tên biến của GOLD>]`, trong khi tên biến là thứ MÔ
HÌNH tự đặt. Ánh xạ đúng đi qua **`kind` của nghĩa vụ**
(`run_thesis_final_acceptance._song_anh_witness`), thứ `analyze` khai và taxonomy
đóng băng quyết định.

Luật của một bản đính chính: **không sửa một byte** artifact thô, **không gọi
model**, ghi băm của từng file được đính chính, và in **cả hai** con số cạnh
nhau. Ghi ra `SCORING_CORRECTION.json` · `FINAL_SUMMARY.json` ·
`TELEMETRY_BUDGET_LEDGER.json` · `ARTIFACT_HASHES.json`.

### `backend/scripts/doi_chieu_ket_qua_cuoi.py` · offline · **0 API call**

Cổng **đối chiếu số liệu trước khi viết chương** (`THESIS_RESULTS_ANALYSIS_AND_
CHAPTER_DRAFTING` §3). Tái tính mọi con số **từ artifact có băm**, rồi so với
`BANG_CHUAN` — 31 trường chép từ **đặc tả wave**, tức một nguồn NGOÀI kho
artifact. Export: `BANG_CHUAN` · `DAP_SO_CHUAN` · `kiem_bam` ·
`kiem_lien_ket_dinh_chinh` · `tai_tinh` · `doi_chieu`.

⚠️ **Vì sao đối chứng phải ngoài**: một file tự so với chính nó thì luôn đúng.
Giá trị của phép này nằm ở chỗ hai nguồn **độc lập** — đặc tả do người soạn viết,
artifact do máy sinh — trùng nhau. Kết quả `SO_TRUONG_LECH != 0` ⇒
`DOCUMENTATION_INPUT_CONSISTENCY = FAIL` và **cấm viết chương**.

Ghi ra `RECONCILIATION.json` **ngoài thư mục lượt chạy** — cố ý: ghi vào trong sẽ
thành "file ngoài bảng" của `ARTIFACT_HASHES.json` và phá tính bất biến từng byte
của artifact lượt đo.

### `backend/scripts/build_product_ui_fixtures.py` · offline · **0 API call**

Trích **phản hồi SẢN PHẨM** của 9 ca lượt đo cuối để tầng giao diện nghiệm thu
được (`PRODUCT_UI_RESULT_RENDERING_AND_DEMO_ACCEPTANCE` §5). Export:
`lan_cuoi_cua_moi_ca` · `dung_phan_hoi` · `doi_chung` · `dung_fixture`.

Artifact lượt đo giữ `chuong_trinh` (đầu ra mô hình) và `cham` (điểm), **không**
giữ envelope — envelope là thứ tầng TẤT ĐỊNH dựng ra *sau* mô hình, nên dựng lại
được với 0 lượt gọi. Đường dựng là **đúng đường sản phẩm**: `verify_and_compile`
→ `pipeline._dung_scene3d` → `_envelope_tu_route_sinh` / `_that_bai_hinh_hoc` →
`attach_learner_reason`.

⚠️ **Không** dựng bằng `compile_semantic_program_to_envelope` một mình — hàm ấy
khai cứng `domain: "generic"` và không gắn `scene3d`, cho ra envelope 2D hợp lệ
nhưng SAI MIỀN (`build_baseline_spot_envelopes.py` đã trả giá một lượt spot-check
đỏ 6/8 với 0 lỗi console).

⚠️ **Phép đối chứng là toàn bộ giá trị của script**: mỗi ca so lại với `cham`
đóng băng ở `SERVABLE`, tập `scene3d_kinds` và từng `expected_display`; lệch là
NÉM. Hai bảng tên dễ lẫn: `type` là kiểu NGỮ NGHĨA (cùng bảng `cham` dùng),
`render` là loại vẽ — so nhầm bảng thì mọi ca đều "lệch". Và cố ý so với
`expected_display` chứ **không** với `actual_display`, vì đó chính là trường lỗi
bộ chấm làm rỗng ở 6/7 ca (`SCORING_CORRECTION.json`).

Ghi ra `docs/evaluation/geometry/product-ui-result-rendering/fixtures/` +
`FIXTURE_HASHES.json` — **ngoài** thư mục lượt đo, để artifact lượt đo giữ
nguyên byte.

### `frontend/scripts/certify-scene3d-visual-fidelity.mjs` (2026-09-09) · offline (cần `npm run dev`) · **0 API call**

Đo **độ đúng trực quan** của Scene3D bằng ĐIỂM ẢNH, không bằng mắt. Chụp bằng
CDP rồi **đưa ảnh ngược vào trang** để chính trình duyệt giải mã PNG — không
thêm thư viện ảnh nào vào kho. `--nhan before|after` sinh
`BASELINE_VISUAL_MATRIX.json` / `AFTER_VISUAL_MATRIX.json` + `screenshots/<nhãn>/`.

Bốn phép đo: hộp mực (khung nhìn và lề) · hộp bao lớp thiết diện (thiết diện có
hiện TRỌN VÒNG không) · tỉ lệ diện tích/bao lồi của lớp đa giác (đáy có đọc ra
là LÕM không) · quan hệ mặt phẳng ↔ thiết diện tính bằng `khungMatPhang` +
`diemHuuHan` trước khi vẽ.

⚠️ **Phân loại theo SẮC ĐỘ, không theo RGB**: mọi vật vẽ bán trong suốt trên nền
sáng nên màu tới màn hình nhạt hơn hằng số nguồn rất nhiều — bản đầu khớp RGB và
đếm **5 điểm ảnh** cho một elip nhìn thấy rõ.
⚠️ **"Có mực" = điểm ảnh CÓ SẮC**, không phải "khác điểm ảnh góc trên trái": nền
khung là dải xám nhạt, nên phép so với một điểm nền cho *"lề 0px, chiếm 100%"* ở
mọi ca — một phép đo luôn đỏ, tức không đo gì.
⚠️ **Ngưỡng "≥ N điểm ảnh" là con số bịa** và đã bị thay: nó phụ thuộc độ phân
giải, độ dày nét và mức thu phóng. Câu cần hỏi là *thiết diện có hiện trọn vòng
hay chỉ còn nửa cung gần* — một mệnh đề về HÌNH DẠNG, không phụ thuộc tỉ lệ.

### Bộ đo ĐỘ CHẬP CHỜN của chính bộ đo (2026-09-09) · offline · **0 API call**

Năm script sinh ra từ `FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE`, khi
`certify-refusal-surface.mjs` cho `17–19/21` mà không ai biết vì sao. Chúng trả
lời bốn câu **khác nhau**, và gộp lại thì mất hết thông tin:

| script | trả lời câu gì | export |
|---|---|---|
| `frontend/scripts/flake-repeat.mjs` | chạy một cổng N lượt, giữ **từng assertion của từng lượt** — phân bố lộ ra thay vì bị trung bình hoá. `--cwd`, `--artifact`, `--kill-chrome`. `RETRY_COUNTS` đếm **số lần cổng tự mở lại trình duyệt**, KHÔNG phải chạy lại một lượt đỏ | (CLI) |
| `frontend/scripts/diagnose-refusal-flake.mjs` | thẻ từ chối **muộn** hay **không bao giờ** hiện — phân xử nhánh B với nhánh A. Gom `Runtime.exceptionThrown` + `Network.loadingFailed`, chụp ảnh đúng lượt trượt | (CLI) |
| `frontend/scripts/measure-page-boot.mjs` | trang có dựng được không, trên **hai máy chủ** (Vite dev vs bản dựng sản phẩm), và **tải lại có cứu được không** | `choTrang` · `doMotMayChu` |
| `frontend/scripts/measure-relaunch-recovery.mjs` | hỏng thuộc **PHIÊN** hay thuộc **thời điểm** — tức mở một Chrome mới có gỡ được không | `thuMotPhien` |
| `frontend/scripts/faultcheck-refusal-surface.mjs` | cổng vừa sửa **còn răng không**: 4 phép tiêm, mỗi phép dựng lại rồi phục hồi nguyên byte | `tiem` · `chayCong` |

⚠️ **`BUILD_FAILED` tách khỏi `NOT_DETECTED`** trong faultcheck. Phép tiêm đầu
thay `{eyebrow}` bằng `{""}`, khiến `eyebrow` thành biến không dùng và `tsc -b`
ĐỎ; cổng **chưa từng chạy**, mà báo cáo ghi `NOT_DETECTED` — đọc y như "cổng
mù". Một phép tiêm không biên dịch được không phải kết luận về cổng.
⚠️ **Kết luận đo được, và nó KHÔNG phải lỗi sản phẩm**: ~13–25% phiên headless
Chrome không tải nổi module từ **Vite dev** (`Script net::ERR_CONNECTION_REFUSED`
+ `net::ERR_NETWORK_ACCESS_DENIED`, `#root` rỗng 60 s); **bản dựng sản phẩm
0/15 lỗi**. Tải lại trong cùng phiên gỡ **0/2**; mở phiên mới gỡ **6/10** —
nên mở lại có ích nhưng KHÔNG phải thuốc chữa. `127.0.0.1` **tệ hơn**
`localhost` (12/12 kẹt), nên đổi host không phải lối thoát.

### `frontend/scripts/capture-release-demo.mjs` (2026-09-09) · offline (cần `npm run dev`) · **0 API call**

Bộ ảnh demo CUỐI: 9 ca đóng băng + 3 ảnh **SAU XOAY** (`p3`, `p6`, `p7` — thiết
diện nằm trên mặt cong, nơi nét khuất đổi theo camera). Envelope trả tại
`/api/analyze`, tua tới bước cuối bằng nút thật nên ảnh mang đáp số.
Ghi `DEMO_SCREENSHOTS.json`: mỗi ảnh kèm `case_id` · **băm đề bài** · **băm
phản hồi** · `camera_pose` · `candidate_hash` · thời điểm.
⚠️ Ảnh PNG **không** cần trùng byte giữa các máy (`§9` của wave) — phán quyết
thuộc oracle ngữ nghĩa/raster đã đăng ký. Siêu dữ liệu tồn tại để mỗi ảnh
**truy được về mã nguồn**; một thư mục PNG trần không tự nói nó chụp bản nào,
mà đem vào khoá luận thì mỗi ảnh là một khẳng định.

### Bộ đo TÊN HIỂN THỊ (2026-09-10) · offline · **0 API call**

| script | sở hữu gì | export |
|---|---|---|
| `backend/scripts/score_display_names.py` | chấm **12 đại lượng** của 7 ca dương: kiểu ngữ nghĩa thật (tra qua `depends`, KHÔNG khớp chuỗi nhãn) · tên biến mô hình đặt · nhãn · phán quyết. `--from-git <ref>` chấm fixture **tại một ref**, nên nền đo lại được thay vì là một tệp đã ghi | `cham` · `DAU_HIEU_PLACEHOLDER` |
| `backend/scripts/measure_cache_impact_display_names.py` | đo tác động cache bằng **row thật**: ghi row `policy_version` cũ mang nhãn cũ rồi gọi lại `/api/analyze`, xem route có trả THẲNG row ấy không | `do` |
| `backend/scripts/faultcheck_display_names.py` | 4 phép tiêm, trong đó **một phép NGƯỢC CHIỀU** (đổi tên biến, giữ kiểu ⇒ phán quyết phải KHÔNG đổi) | `tiem` |

⚠️ **Nó KHÔNG chấm đáp số.** Giá trị vẫn do `doi_chieu_ket_qua_cuoi.py` và
oracle đối chiếu — một bộ đo vừa chấm tên vừa chấm số thì một bản vá tên có thể
làm đổi phán quyết về số mà không ai thấy.
⚠️ **`kieu_doi_tuong_that` tra qua `depends`, không qua guillemet.** Bản đầu
khớp cụm trong `«…»` với `label` của vật và trả `None` cho **mọi** hàng: thứ
nằm trong guillemet là `reference` (cách gọi ngắn), không phải `label`.

### `backend/scripts/build_release_manifest.py` (2026-09-09) · offline · **0 API call**

Manifest release: `git_commit` · **hai** candidate (`candidate_hash` hiện tại và
`historical_candidate_hash` của lượt live) · `cache_version` · 5 băm model-facing
kèm cờ *đổi hay không so với lượt nghiệm thu* · `api_contract_hash` (lược đồ
chương trình + `error_codes.py`) · `frontend_build_hash` (băm CÂY `dist/`) ·
phạm vi hỗ trợ / ngoài phạm vi / giới hạn đã biết · `test_results` đọc từ
artifact `REPEAT_*.json`. Export: `dung_manifest`.
⚠️ Hai danh tính và hai loại bằng chứng (`live_evidence` bất biến vs
`replay_evidence` dựng lại hôm nay) ghi thành **trường riêng**, không gộp — gộp
là cách im lặng nhất để một con số của lượt đo cũ bị đọc như số của mã hiện tại.

### `backend/scripts/build_photo_problem_corpus.py` (2026-09-13) · offline · **0 API call**
Bộ ảnh nghiệm thu **TỔNG HỢP** cho đường ảnh → mô phỏng
(`PHOTO_PROBLEM_TO_SCENE_END_TO_END §10`): 12 ảnh vẽ bằng Pillow (Arial, chữ
tiếng Việt) rồi làm xấu TẤT ĐỊNH — nghiêng phối cảnh, mờ, thiếu sáng, EXIF
`Orientation=6` kèm GPS, có/không hình minh hoạ, chỉ có hình. Ground truth lấy từ
fixture `product-ui-result-rendering` (p1–p7, n1), không tự viết. Ghi
`docs/evaluation/geometry/photo-problem-to-scene/{corpus/, CORPUS.json,
OFFLINE_NORMALIZATION.json, browser_fixture_*.json}`. Mặc định TỪ CHỐI ghi đè;
`--kiem` đối chiếu băm tệp và chuẩn hoá lại (ảnh EXIF phải trùng TỪNG ĐIỂM ẢNH với
trang đứng; metadata phải bị gỡ). Fixture trình duyệt dựng bằng CHÍNH
`assess_extraction` + `ExtractionResult.to_response`, không chép tay hình dạng.
⚠️ `CORPUS_KIND = SYNTHETIC_RENDERED` · `REAL_PHOTO_CORPUS = NOT_ESTABLISHED` —
không chứng minh provider đọc được ảnh chụp thật.

### `backend/scripts/run_photo_problem_live.py` (2026-09-13, VIẾT LẠI 2026-09-14) · ⚠️ **TIÊU QUOTA THẬT** (trừ `--dry-run`)
`PHOTO_PROBLEM_LIVE_RUNNER_HARDENING` thay bản ba-ca-ghi-cứng (bản ấy chỉ có trần
LOGIC 11 — xấu nhất 38 request HTTP — không dừng khi ca trước hỏng, đo văn bản bằng
`difflib`). Cờ `--gia-lap` và thư mục `.../live/<dấu thời gian>` của bản cũ **không
còn**. `--case C01|C02|C03|all` bắt buộc (thiếu ⇒ in hướng dẫn, thoát 2); `all` chạy
tuần tự, **dừng ở ca đầu tiên không đạt**; C03 chỉ đọc ảnh, không bao giờ gọi tầng B.
`--input-dir`/`--ground-truth`/`--output-dir` phải TUYỆT ĐỐI, thư mục ra mới hoặc
rỗng, kiểm TRƯỚC mọi request. Không chép ảnh; `--include-sanitized-images` cần
`--confirm-no-personal-data`. Mã thoát: 0 đạt · 1 ca hỏng · 2 đầu vào · 3 thiếu
`ALLOW_LIVE_AI=1`/`GEMINI_API_KEY` · 4 chính sách thử lại.
**Ranh giới HTTP mà không đổi mã sản phẩm:** `CongHttp` là transport `httpx` bọc
ngoài transport mạng, chèn bằng `cai_cong_http` (thay `httpx.AsyncClient` mà
`call_gemini` đọc lúc gọi). Nó đếm, chặn và ghi metadata đã khử secret cho MỖI lần
thử — trần `MAX_HTTP_REQUESTS = 11`, chặn cả request không khai tầng
(`telemetry.current_stage`) lẫn mọi request sau lỗi provider đầu tiên. Lần thử lại
đọc từ `ApiBudget.retry_requests`, **không** đoán theo băm thân (vòng sửa của tổng
hợp gửi thân trùng nhau — bản đầu đếm sai đúng chỗ ấy). `ApiBudget(max_attempts=1)`
ép một lần thử; `do_so_lan_thu_moi_tang` dò ĐÚNG ba hàm sản phẩm với provider 503,
khác 1/1/1 ⇒ thoát 4 trước mọi request. `cer` = Levenshtein / độ dài tham chiếu sau
NFC · CRLF · khoảng trắng cuối dòng; `cham_du_kien` chấm nhãn điểm (phải vừa có trong
`named_points` vừa hiện như KÝ HIỆU trong văn bản), công thức, vật, quan hệ, yêu cầu,
và mục THÊM. ⚠️ **Sửa ở `PHOTO_PROBLEM_ACCEPTANCE_SCORER_CORRECTION` (2026-09-14):**
khớp theo TOKEN (`tach_token` · `khop_du_kien` · `khop_moi_van_ban`) — dữ kiện phải là
BIỂU THỨC HOÀN CHỈNH trong CẢ bản nguyên văn lẫn bản chuẩn hoá; trường cấu trúc của model
không còn là nguồn khớp; tương đương ký hiệu khai ở `TUONG_DUONG_DA_KHAI`; ký hiệu ngoài bảng
⇒ `UNVERIFIABLE_AUTOMATICALLY`. Mục thêm phân loại trên GROUND TRUTH (`phan_loai_muc_them`):
`CONFIRMED` · `CONTRADICTED` (nhãn/số lạ, hoặc khác đúng một số/một toán tử quan hệ) ·
`UNVERIFIED` (chờ người) — `ky_hieu_va_so` và suy luận "nhãn thật ⇒ không bịa" đã GỠ.
C03 đòi `expected_rejection_codes` ⊆ `ma_tu_choi_san_pham()` (AST của `assess_extraction`).
Mỗi ca `status` ∈ PASS/FAIL/ERROR/BLOCKED; tóm tắt tách `AUTOMATED_CHECKS` ·
`HUMAN_CRITICAL_FACT_REVIEW` (luôn `PENDING` lúc chạy) · `REAL_PHOTO_ACCEPTANCE`. Mỗi lượt ghi
`HUMAN_REVIEW_PACKET.json` (`goi_duyet`, ràng buộc `rang_buoc_luot`); `--verify-review
--run-dir --human-review` kiểm bản duyệt (`phan_quyet_duyet`: PENDING · SIMULATED_REVIEW ·
STALE_REVIEW · INVALID_REVIEW · FAIL · PASS chỉ cho bản NGƯỜI trên lượt provider thật). `BoKhuBiMat` khử khoá, `?key=`, `Authorization`, `x-goog-api-key`,
`Cookie`, `Set-Cookie`, `access_token`, `refresh_token` ở mọi dòng in và mọi JSON.
Ba chế độ: `REAL_PROVIDER` · `DRY_RUN` (`TransportGiaGemini`, phát lại byte
`dry_run_replay_case`) · `INJECTED_TRANSPORT` (`inner_transport_factory`; provider
kịch bản `TransportKichBan`) — hai chế độ sau chạy trong `ChanMangThat` và **không
bao giờ** ghi `REAL_PROVIDER_EVIDENCE`. Khoá: `tests/test_photo_problem_live_runner.py`.
**Tiếp tục từ checkpoint đọc ảnh (`C01_DOWNSTREAM_CHECKPOINT_ACCEPTANCE`, 2026-09-14):**
`--vision-checkpoint <tuyệt đối>` dùng lại một lượt vision THẬT đã lưu để đo tầng B mà không gọi
lại vision. `doc_vision_checkpoint` kiểm TRƯỚC mọi request — HTTP 200 · ba kết quả PASS · một
request · 0 retry · model · băm prompt · băm hai lược đồ · `VISION_SCHEMA_IDENTITY` · băm ảnh gốc
và ảnh chuẩn hoá · ground truth (trùng tệp, hoặc trùng `derived_from_ground_truth_sha256` tệp ấy
khai) — rồi thẩm định lại `extraction` bằng Pydantic đầy đủ hiện tại và tính lại phán quyết, phải
TRÙNG bản lưu; lệch ⇒ `LoiCheckpoint` (`CHECKPOINT_PROVENANCE_FAILED: <trường>`), thoát 2. Một ca
C01/C02, không `--dry-run`, trần ≤ `MAX_HTTP_REQUESTS_CHECKPOINT` = 4; `CongHttp(tran_theo_tang=
TRAN_THEO_TANG_CHECKPOINT)` chặn vision với trần 0 (`STAGE_BUDGET_EXHAUSTED`) và phép dò thử lại
bỏ vision. Nhãn duyệt `AUTOMATED_CHECKPOINT_REPLAY` (không bao giờ `HUMAN`); cần xác nhận mà không
có `--confirmed-text` ⇒ `REVIEW_CONFIRMATION_REQUIRED`, không analyze. Thêm cho MỌI chế độ: cổng
ghi `logical_call`/`attempt` và `usage_metadata` (chỉ số đếm — `chi_so_token`) mỗi request;
`TOKENS_BY_REQUEST`/`TOKENS_BY_STAGE` (`tong_hop_token`); `kiem_ngang_bang_payload` băm bản xem lại
· bản xác nhận · văn bản trong từng request analyze (`van_ban_trong_than_analyze`);
`DOWNSTREAM_FAILURE_CLASS` (`phan_loai_loi_tang_b`: `ANALYZE_PROVIDER_ERROR` ·
`ANALYZE_OUTPUT_INVALID` · `SYNTHESIS_PROVIDER_ERROR` · `SYNTHESIS_OUTPUT_INVALID` ·
`SYNTHESIS_REPAIR_EXHAUSTED` · `HTTP_BUDGET_EXCEEDED`); `{ca}_ENVELOPE.json` nguyên dạng đã khử
secret. Chế độ checkpoint ghi thêm `RUN_KIND = DOWNSTREAM_FROM_VISION_CHECKPOINT`,
`SINGLE_RUN_END_TO_END = NOT_RUN`, `PRIOR_VISION_TOKENS` · `NEW_*_TOKENS` ·
`COMPOSITE_PIPELINE_TOKENS` · `REFERENCE_VISION_TOKENS_NOT_RESPENT` (`token_checkpoint`). Khoá:
`tests/test_photo_problem_vision_checkpoint.py`.
**Chấm nguồn gốc dữ kiện C03 (`VISION_DIAGRAM_ONLY_PROVENANCE_GUARD_FIX`, 2026-09-14):**
`{ca}_RAW_EXTRACTION.json` ghi `extraction` (bản mô hình trả — chỉ ở thư mục chạy) · `public_extraction`
(bản sau guard) · `provenance_guard`. Ca C03 chấm ĐỘC LẬP với guard trên bản công khai theo
`TRUONG_DU_KIEN_C03` (`truong_du_kien_khong_rong`, không đọc `ie.FACT_BEARING_FIELDS`) và ghi
`RAW_MODEL_FACT_FIELDS_EMPTY` · `SAFE_PUBLIC_FACT_FIELDS_EMPTY` · `PUBLIC_FACT_FIELDS_NOT_EMPTY` ·
`QUARANTINED_FACT_FIELDS` · `QUARANTINED_FACT_COUNT` · `DIAGRAM_OBSERVATIONS_USED_AS_FACTS`;
`C03_SAFE_REJECTION` nay đòi mã đăng ký **và** bản công khai không mang dữ kiện, lọt ⇒
`C03_PUBLIC_FACT_FIELDS_NOT_EMPTY`, `SILENT_HALLUCINATION = 1`. Trước bản sửa, ca bị từ chối không
bao giờ bị soi dữ kiện. Khoá: `tests/test_vision_diagram_only_provenance_guard.py` (E3 · E4 · J2).
**Chẩn đoán từ chối lược đồ — trace `synthesis-repair-trace/2` (`SYNTHESIS_REJECTION_POINTER_TRACE_GAP`, 2026-09-15):**
pilot C02 `20260915T061735Z-7b979fce` bị loại `PROGRAM_SCHEMA / SCHEMA_VALUE_ERROR` mà không biết CHỖ nào — validator biến
`ValidationError` thành chuỗi, runner chỉ giữ `SCHEMA_<type>`; lỗi quá khứ `NOT_RECOVERABLE`. `phan_loai_ung_vien` nay trả
thêm `diagnostics` = `{phase, code, error_count, details}` cho `PROGRAM_SCHEMA`, dựng lại từ lần chạy lại validation trên
ứng viên trong bộ nhớ (mã sản phẩm KHÔNG đổi). Mỗi chi tiết đúng năm trường: `json_pointer` · `pointer_status` ·
`pydantic_error_type` · `rule_id` · `received_json_type`. ⚠️ `loc` của Pydantic trỏ vào dữ liệu SAU
`model_validator(mode="before")` (`_nang_declare_point` gỡ `declare_point` ⇒ chỉ số `statements` DỜI), nên đổi thẳng `loc`
là bịa con trỏ: `_duong_ung_vien` dò trên JSON THÔ (mọi chỉ số là ứng viên, thẻ union phải khớp `kind`, lá bằng `input`
của lỗi — chỉ trong bộ nhớ) và chỉ ghi `EXACT` khi ra đúng một đường, còn lại `AMBIGUOUS` + `null`; loc rỗng ⇒ `""`.
`con_tro_json` escape bằng CHUNG `validator._thoat_con_tro`. `rule_id` của `value_error` = `co_qualname` hàm trong
`semantic_program/` đã ném, đọc từ traceback (`_ham_da_nem`), không từ thông điệp; `SCHEMA_SILENTLY_DROPPED_KEY` giữ con
trỏ của validator (`_chan_doan_khoa_bi_bo`). `chan_doan_tu_loi` sắp xếp theo `khoa_sap_xep_chan_doan`, không theo thứ tự
Pydantic. Trace v2: `rejection_diagnostics` + `rejection_summary_status` (`PRESENT` · `WITHHELD_PYDANTIC_MESSAGE`) — lời
Pydantic bị giữ lại vì `str(ValidationError)` chở `input_value`; mọi pha khác và lỗi provider giữ như v1, chẩn đoán
`null`. `doc_trace_vong_sua` đọc v1/v2 → khung v2 (`source_trace_version`, `rejection_diagnostics_status`), không sửa đầu
vào, phiên bản lạ ⇒ `ValueError`. Khoá: `tests/test_synthesis_rejection_diagnostics.py`.
**Chẩn đoán cổng phủ cấu trúc — trường tuỳ chọn của trace v2 (`SYNTHESIS_STRUCTURAL_COVERAGE_REJECTION_DIAGNOSIS`, 2026-09-15):**
lượt route dừng ở `structural_coverage` ghi `route_coverage_diagnostic` (mọi lượt khác `null`, kể cả lỗi provider), lấy THẲNG
từ `coverage_diagnostic` của sự kiện `semantic_route` — không đọc `reason`/`details`. `rut_gon_chan_doan_phu` giữ đúng khoá cho
phép (`KHOA_CHAN_DOAN_PHU` · `KHOA_DONG_PHU`: con trỏ · trạng thái con trỏ · loại nghĩa vụ gốc/chính tắc · kiểu chủ thể ·
trạng thái phủ · mã lý do · loại/số bằng chứng), mã ngoài từ vựng đóng của `coverage_gate` ⇒ `OUT_OF_VOCABULARY`, bỏ vân tay.
Con trỏ được KIỂM LẠI trên hợp đồng runner tự dựng từ phản hồi analyze (`_giai_con_tro` + `dau_van_nghia_vu`), không khớp ⇒
`null`/`AMBIGUOUS`. Trace giữ `synthesis-repair-trace/2` (trường thêm, nghĩa trường cũ không đổi); `doc_trace_vong_sua` đặt
`route_coverage_diagnostic = null` cho v1 và v2 cũ. Khoá: `tests/geometry/test_structural_coverage_diagnostic.py`.
**Chẩn đoán chất lượng đầu ra được nhận (`SYNTHESIS_ACCEPTED_OUTPUT_QUALITY_DIAGNOSIS`, 2026-09-15):** cờ opt-in
`--accepted-output-quality` ghi `{ca}_ACCEPTED_OUTPUT_QUALITY.json` (`dung_chat_luong_dau_ra`) cho ca có envelope: đầu ra được
phục vụ ⇒ bốn lớp phủ của `accepted_output_quality`; không phục vụ / thiếu hợp đồng / thiếu ứng viên ⇒ `applicable = false`
kèm mã. Nguồn: sự kiện `semantic_route` (servable · final_memory) · ứng viên cuối cùng qua vòng sửa (trong bộ nhớ) · `scene3d`
của envelope · RequestContract dựng lại từ phản hồi analyze; yêu cầu hình CHỈ từ hợp đồng. Observer bật cho trace HOẶC cờ
này (thụ động, #22); trace chỉ ghi khi có `--synthesis-repair-trace`. Request, phản hồi sửa và envelope trùng khi bật/tắt.
Khoá: `tests/test_accepted_output_quality.py`.

### `backend/tests/geometry/test_structural_coverage_diagnostic.py` (2026-09-15) · offline
Viết TRƯỚC bản sửa — nền đỏ 25/25. Fixture là biến thể nhỏ của chương trình p1 đóng băng trên RequestContract p1 dựng từ
`raw/analyze_0.json` đóng băng; KHÔNG dựng lại output live B02. A–C thiếu riêng một nghĩa vụ ⇒ đúng một hàng `UNCOVERED`,
con trỏ `/obligations/<i>` · D thiếu hai, thứ tự nguồn · E phủ đủ ⇒ phục vụ, không chẩn đoán · F hai nghĩa vụ cùng loại, con
trỏ khác, `WITNESS_NOT_DECLARED` tách khỏi `WITNESS_WITHOUT_PRODUCER` · G con trỏ giải đúng nghĩa vụ + vân tay · H hợp đồng
đọc không khớp ⇒ `AMBIGUOUS` · I không tên/giá trị · J bí mật giả trong container/witness không vào trace kể cả khi TẮT che
(cửa sổ chứng: `details` CÓ chở nó) · K xác định · L p1/p3/p4 vẫn phục vụ · M sáu fixture B02 (thiếu, sai lượng đo, hằng số)
đúng route/mã/nhánh/bằng chứng · N lỗi provider không có chẩn đoán giả · O/P tắt–bật trace cùng request và phản hồi sửa ·
Q không trạng thái dùng chung · R reader đọc trace v1 lịch sử và v2 thiếu trường.

### `backend/scripts/accepted_output_quality.py` (2026-09-15) · offline · **0 API call** · chỉ quan sát
`chan_doan_chat_luong_dau_ra(contract, spec, final_memory, scene3d, *, route_served, visual_requirements, registered_answers)`
→ `accepted-output-quality/1`: một hàng mỗi nghĩa vụ (thứ tự nguồn, con trỏ tự kiểm bằng `dau_van_nghia_vu`) với bốn lớp
`computation_coverage` (witness do `measure` đúng lượng đo sinh ra + có giá trị chính xác) · `construction_coverage` (chủ
thể phép đo có câu lệnh dựng; yêu cầu thiết diện ⇒ đúng `construct_section`) · `scene_coverage` (chủ thể có trong cảnh
đúng loại; thiết diện: khép kín, đúng chu trình `same_section_cycle`, mặt phẳng nguồn khớp `parallel_planes` +
`point_on_plane`) · `answer_coverage` (`radical.display` trùng đáp số đăng ký và readout của cảnh), cùng
`SILENT_QUALITY_FAILURE` · `SILENT_VISUAL_OMISSION`. Yêu cầu hình chỉ từ `section_matches` của hợp đồng
(`REQUEST_CONTRACT`, tham chiếu dựng lại bằng `cross_section`) hoặc yêu cầu đăng ký trước của bộ đo
(`REGISTERED_REFERENCE`). Mọi phép hình học/phân giải là hàm sản phẩm (`check_structural_coverage` cho bản đồ tên ·
`phan_giai_witness` · `_cau_lenh_dung`); đầu ra chỉ có con trỏ, loại, trạng thái, số đếm, mã (`CHUOI_CHO_PHEP`). Nằm ngoài
`MEASURED_SYSTEM_PATHS` — không đổi candidate, không đổi quyết định phục vụ.

### `backend/tests/test_accepted_output_quality.py` (2026-09-15) · offline
Viết TRƯỚC — nền đỏ 20/20. Fixture là biến thể nhỏ của chương trình p1 đóng băng trên RequestContract p1 (không có
`section_matches`), yêu cầu hình và đáp số lấy từ manifest benchmark; KHÔNG dựng lại output live đã mất. A đủ bốn lớp · B đa
giác đáy thay thiết diện: route vẫn `served`, chẩn đoán bắt `SILENT_VISUAL_OMISSION` · C `polygon3` cùng toạ độ không thành
thiết diện, kể cả khi hợp đồng có `section_matches` (route vẫn phục vụ) · D thiết diện sai tập đỉnh · E đúng đỉnh sai mặt
phẳng nguồn (sửa cảnh) · F thiếu witness · G witness hằng số không nâng lớp nào (cảnh không phát readout cho nó) · H cảnh
làm rơi thiết diện · J2 thiết diện không khép kín · I hai thiết diện, thứ tự xác định · J con trỏ · K không chuỗi thô · L bí
mật giả không lọt chẩn đoán lẫn artifact runner · M/N/O bật/tắt cùng request, phản hồi sửa, envelope · P B03/B04 đủ bốn lớp ·
Q C01/C02 phát lại cùng cảnh và đủ ba lớp · R không trạng thái dùng chung.

### `backend/tests/test_synthesis_rejection_diagnostics.py` (2026-09-15) · offline
Viết TRƯỚC bản sửa trace v2 — nền đỏ 15/19 (4 xanh là cổng parity L · M · N · P, phải xanh từ trước). A con trỏ lồng
trên JSON thô (kèm cửa sổ chứng: `loc` thô KHÁC con trỏ) · B chỉ số mảng · C RFC 6901 · D lỗi gốc `""` + `rule_id` ·
E `AMBIGUOUS` (thẻ không khớp, hai ứng viên bằng nhau, dữ liệu đã bị biến đổi) · F nhiều lỗi đủ và xác định · G trace
trùng từng byte · H `SCHEMA_SILENTLY_DROPPED_KEY` giữ con trỏ · I lỗi provider không có chẩn đoán giả · J không khoá
`input`/`msg`/`ctx`, không giá trị mốc, không prompt · K bí mật giả trong giá trị và thông điệp ngoại lệ không lọt kể cả
khi TẮT che · L/M/N/P tắt–bật trace cùng envelope, request, phản hồi sửa, ngân sách HTTP · O không trạng thái dùng chung ·
Q reader đọc trace v1 LỊCH SỬ `tests/fixtures/synthesis_repair_trace_v1_c02_redacted.json` (trace thật của run
`20260914T141706Z-9a469909`, chỉ băm/mã/tóm tắt hợp đồng; JSON chính tắc trùng bản gốc).

### `backend/tests/test_photo_problem_vision_checkpoint.py` (2026-09-14) · offline
Viết TRƯỚC chế độ checkpoint — nền đỏ 38/42 (4 ca K14 "xanh" chỉ vì argparse chưa biết cờ, không
chứng minh gì). K01 hợp lệ, nhãn không bao giờ `HUMAN` · K01b ground truth gắn qua
`derived_from` · K02–K05 nguồn gốc sai (ảnh khác · 15 trường danh tính/kết quả · 4 kiểu trượt
Pydantic · phán quyết bị thay bằng ground truth) ⇒ thoát 2, 0 cổng · K05b payload analyze là văn bản
CHECKPOINT, không phải ground truth · K06 không đường nào tới vision (hàm đọc ảnh bị thay bằng bẫy;
cổng trần 0) · K07 ngang bằng payload, có sửa và không sửa · K08 bị từ chối / cần xác nhận ⇒ 0
analyze · K09–K10 trần 4 và phân loại lỗi tầng B (không bao giờ là từ chối an toàn) · K11 secret ·
K12 token theo request, tách PRIOR/NEW · K13 envelope · K14 tổ hợp cờ sai. Dùng lại nền của
`test_photo_problem_live_runner.py`.

### `backend/scripts/prove_photo_live_runner.py` (2026-09-14) · offline · **0 API call**
Sinh `HTTP_BUDGET_PROOF` · `CER_PROOF` · `REDACTION_PROOF` · `RUNNER_DRY_RUN` dưới
`docs/evaluation/geometry/photo-problem-to-scene/live-runner-hardening/` từ
`DRY_RUN_GROUND_TRUTH.json` đăng ký trước (không sinh ở đây), qua đúng
`R.main`/`CongHttp` trong `ChanMangThat`. Đường xấu nhất vẫn đạt được dựng bằng
tổng hợp trả JSON hỏng hai lượt ⇒ đúng 11 request; secret giả chỉ ghi BĂM, kèm
một dấu mốc chứng minh thông điệp thật sự tới stdout/artifact. Từ chối ghi đè.

### `backend/tests/test_photo_problem_live_runner.py` (2026-09-14) · offline
Mười tám yêu cầu của wave, 56 ca. Provider giả là transport BÊN TRONG `CongHttp`
nên vòng thử lại của `call_gemini`, `image_extraction`, pipeline, kernel, scene3d
đều là mã thật; tầng B phát lại byte `thesis-final` p1/p6. Mỗi kịch bản "không
gọi" đều để SẴN phản hồi đúng cho lượt gọi bị cấm — nên 0 lượt là do bị chặn, không
do hết kịch bản. Ba assertion `ACCEPTANCE == "PASS"` (test_01/02/07) đổi ở
`PHOTO_PROBLEM_ACCEPTANCE_SCORER_CORRECTION` — đáp án cũ chính là lỗi nghiệm thu khi chưa có
người duyệt; khai trong `acceptance-scorer-correction/BEFORE_AFTER_TESTS.json`.

### `backend/tests/test_photo_problem_acceptance_scorer.py` (2026-09-14) · offline
Test phản chứng VIẾT TRƯỚC bản sửa, chạy trên runner `684420d` để lưu kết quả "trước": S1
khớp biểu thức hoàn chỉnh (`z = 3` / `z = 30`, `A` / `A′`, `⊥` / `∥`, trường cấu trúc không
che văn bản), S2 mục thêm (`SA ⊥ BD` nhãn thật mà đề không nói ⇒ chờ người; nguồn xác nhận
là ground truth, không phải văn bản của chính model), S3 mã từ chối C03 đăng ký trước, S4 lỗi
provider/timeout/lược đồ/ngân sách/ngoại lệ không phải từ chối an toàn và được phân biệt
FAIL/ERROR/BLOCKED, S5 cổng duyệt thủ công (PENDING mặc định, bản giả không bao giờ PASS, bản
cũ lệch ràng buộc ⇒ STALE). Giao diện dùng đều có ở `684420d` khi có thể.

### `backend/scripts/prove_photo_scorer_correction.py` (2026-09-14) · offline · **0 API call**
Nạp runner `684420d` thẳng từ blob git (`git show`, đăng ký `sys.modules` trước khi thực thi)
và đưa CÙNG đầu vào qua cả hai runner trong `ChanMangThat`. Sinh `BEFORE_AFTER_TESTS` (từ hai
JUnit XML) · `FACT_MATCHING_PROOF` · `C03_REJECTION_PROOF` · `HUMAN_REVIEW_GATE_PROOF` dưới
`.../photo-problem-to-scene/acceptance-scorer-correction/`; mỗi hàng mang `input` · `expected`
· `actual_before` · `actual_after` · `test_name` · `runner_sha256` · `evidence_class` và phán
FIXED / GUARD_ALREADY_PRESENT / NOT_FIXED theo từng khoá. Từ chối ghi đè.

### `backend/tests/photo_problem_identity.py` (2026-09-13) · offline
KHÔNG phải file test. `prompts_neu_transcribe_chua_doi()` dựng lại băm `prompts`
lịch sử (`55ac1ca6…`) từ skill hiện tại, chỉ bằng cách trả `transcribe.md` về băm
tại `085cae6` — bằng chứng máy cho câu "độ lệch `prompts` chỉ do prompt đọc ảnh".
Các ô danh tính lịch sử dựa vào nó (oblique ellipse ×2, nonconvex, thesis runner
alignment, point initialization) thay vì sửa artifact. Khoá kèm hai phép tiêm:
`test_photo_problem_identity.py`.

### `backend/scripts/replay_negative_boundaries.py` — bổ sung 2026-09-13
`doc_raw_theo_thu_tu(case_id)` + `ProviderPhatLaiTheoThuTu`: phát lại byte đóng
băng theo ĐÚNG THỨ TỰ lượt gọi trong chặng, kể cả lượt sửa (`repair_1` của p3).
`doc_raw` cũ giữ một bản ghi mỗi chặng — phát lại p3 bằng nó ra `ir_static` y như
lượt đầu, trông giống hệt một hồi quy sản phẩm. Hết bản ghi mà pipeline còn gọi ⇒
ném; `con_lai()` khác 0 ⇒ pipeline gọi ít hơn lượt đo. Dùng bởi
`test_photo_problem_semantic_integration.py` và `run_photo_problem_live.py --dry-run`.

### `backend/scripts/replay_negative_boundaries.py` (2026-09-09) · offline · **0 API call**

Phát lại **nguyên byte** hai ca âm (`n1`, `n2`) của lượt đo cuối qua đúng
`run_pipeline`, chụp **bảy biên**: `domain` → `scope` → `semantic_analyze` →
`semantic_program` → `verify/execute` → envelope backend → product response
adapter. Export: `NetworkGuard` · `kiem_guard_co_rang` · `doc_raw` ·
`ProviderPhatLai` · `GhiBien` · `replay_case` · `doc_de_bai` ·
`TEN_CHANG_ARTIFACT` · `CA_AM`.

Nó tồn tại vì envelope cuối chỉ mang **một bit** thông tin khi một trường là
`null` — *thiếu* — và bit ấy không phân biệt được "tầng phát hiện chưa biết"
(nhánh A) với "biên chuyển kết quả đánh rơi" (nhánh B). Nhìn từng biên thì thấy
ngay: biên 4 phát đủ `stage_reached` + `error_code`, biên 6 giao `null`.

⚠️ **Ngoại lệ loopback trong `NetworkGuard` KHÔNG phải chỗ hở.**
`ProactorEventLoop` trên Windows tự dựng `socketpair()` loopback để đánh thức
chính nó; chặn thẳng `socket.connect` làm script chết trước ca đầu tiên (đã xảy
ra). Provider thật đi `httpx`, và lớp ấy bị chặn **vô điều kiện**; phép tiêm thử
một địa chỉ NGOÀI loopback để chứng minh ngoại lệ không nới ra.
⚠️ **Hai bảng tên cho hai lượt gọi**: `telemetry.current_stage()` khai
`semantic_analyze`/`semantic_program`, artifact lượt live ghi
`analyze`/`synthesis`. `TEN_CHANG_ARTIFACT` ánh xạ tường minh — khớp tiền tố là
chỗ một tên mới lặng lẽ trượt qua.

### `backend/scripts/faultcheck_response_contract.py` (2026-09-09) · offline · **0 API call**

Bảy phép tiêm vào bản vá hợp đồng phản hồi; mỗi phép sửa tệp THẬT, chạy đúng bộ
test tương ứng (pytest hoặc vitest), rồi **phục hồi nguyên byte** và đối chiếu
lại băm. Export: `tiem` · `FaultError`. Kết quả: **7/7 DETECTED**.
⚠️ Mẫu tiêm thử **cả `\n` lẫn `\r\n`**: kho có cả tệp LF lẫn CRLF, và "khớp 0
lần" trông y hệt "mẫu viết sai".

### `backend/scripts/measure_cache_impact_response_contract.py` (2026-09-09) · offline · **0 API call**

Đo tác động cache bằng **một row thật**: gọi `/api/analyze` qua `TestClient` với
provider stub rồi soi bảng `SimulationCache`. Export: `do`. Đề bị từ chối ghi
**0 row** ⇒ không có row cũ nào để trả thẳng ⇒ **không bump** `CACHE_VERSION`.
Đây là cách §10 của wave đòi: quyết định cache bằng phép đo, không bằng tiền lệ.

### `backend/scripts/scene3d_world_oracles.py` (2026-09-09) · offline · **0 API call**

Oracle **không gian thế giới** cho Scene3D của 9 ca lượt đo cuối: elip/đường
tròn có nằm đúng trên mặt phẳng cắt và trên mặt cong không, khối cong có thoả
bất biến ba điểm neo không, đáy có lõm không. Export: `So` · `diem_tren_elip` ·
`diem_tren_duong_tron` · `tren_mat_phang` · `tren_mat_cau` · `tren_mat_tru` ·
`tren_mat_non` · `trong_doan_truc` · `da_giac_lom` · `soi_mot_ca`.
`--faultcheck` chạy 5 phép tiêm và đòi mỗi phép làm đỏ ít nhất một ca.

Nó đóng **nhánh A** (dữ liệu sai) trước khi ai chạm renderer: kết quả 7/7 với
tolerance **bằng 0**.

⚠️ **`So` — số trong ℚ(√c)**, có vì bản đầu chỉ lấy mẫu được đường cong khi cả
hai bán trục chia cho phương ra số hữu tỉ; `p7` có bán trục nhỏ `√(1/48)` nên nó
**bỏ qua đúng ca ưu tiên cao nhất** và ghi một dấu ✗ trông như lỗi dữ liệu. Rơi
về float là lối thoát sai — khi ấy phải có tolerance, mà tolerance che đúng lớp
lỗi đang đi tìm.
⚠️ **Ghép thiết diện với mặt phẳng bằng PHÉP CHỨA, không bằng pháp tuyến bằng
nhau.** Bản đầu bỏ qua mặt phẳng có `normal` khác, nên phép tiêm "xoay sai pháp
tuyến" **không đỏ**: phép kiểm bị BỎ QUA và oracle im lặng báo đạt.

### `frontend/scripts/certify-scene3d-hidden-lines.mjs` (2026-09-09) · offline (cần `npm run dev`) · **0 API call**

Chứng minh **nét liền / nét khuất** ở hai tầng tách bạch, vì gộp lại thì một
renderer vẽ mọi thứ bằng nét liền vẫn "đạt":

- **A · phân loại** — oracle ĐỘC LẬP, không hỏi renderer một câu nào. Ba thiết
  diện `p3`/`p6`/`p7` nằm **trên mặt** khối lồi, nên: *thấy ⟺ n̂(Q)·(mắt − Q) > 0*.
- **B · dạng nét trên canvas** — tại đúng vị trí oracle chỉ ra, đoạn thấy phải
  liền, đoạn khuất phải có chu kỳ đứt, và hai kiểu phải phân biệt được.

Camera mặc định tính lại bằng chính hàm thuần sản phẩm (`diemHuuHan` →
`hopBaoCuaDiem` → `khungNhinVua`) — không phải vòng luẩn quẩn: hàm ấy là **đặc
tả** camera đứng ở đâu, phần được kiểm là phép che khuất.

⚠️ **Camera sau khi xoay tính được, không đoán**: OrbitControls đổi phương vị
đúng `2π·dx/clientHeight`, damping chỉ đổi đường đi chứ không đổi điểm đến. Kèm
**cổng tự-kiểm**: nếu camera dự đoán sai thì điểm mẫu rơi ra ngoài đường và
"đoạn thấy vẫn liền" tụt xuống — không có cổng ấy thì mọi kết luận sau đó dựa
trên một camera bịa.

⚠️ **Bán kính lấy mẫu phải NHỎ HƠN khe đứt.** Bản đầu lấy ±3px trong khi vành
dày ~9px: mọi điểm mẫu đều "có nét", đoạn khuất đo ra 100%, và phép đo báo
"không có nét đứt" trên một hình đứt rõ trong ảnh.

⚠️ **Phép kiểm xoay đầu tiên RỖNG NGHĨA**: nó so cờ nét tại đúng các vị trí điểm
ảnh cũ sau khi xoay và mừng vì 69/72 điểm "đổi" — nhưng xoay xong đường cong đã
đi chỗ khác, nên nó đo *hình có dịch không*, một điều hiển nhiên. Nay tính lại
camera rồi chạy lại oracle trên chính các điểm thế giới ấy.

### `frontend/src/simulations/domains/geometry/scene3d-hidden-lines.test.tsx` (2026-09-09) · offline

Khoá **cấu trúc** làm cho hidden-line khả thi, không khoá ảnh: lớp chiều sâu vô
hình tồn tại và có `depthWrite` · miếng mặt phẳng **không** được ghi chiều sâu ·
đường dựng hai lượt với `LessEqualDepth`/`GreaterDepth` · có `polygonOffset` ·
thiết diện thôi dùng `depthTest: false`. Thiếu một mảnh thì hidden-line không
hỏng ồn ào — nó **biến mất im lặng**, đúng cách nó đã vắng mặt suốt trước đó.

Tách khỏi `scene3d.test.tsx` vì file ấy cố ý **không nhập `three`**; các khẳng
định ở đây phải so với hằng số thật của thư viện, không với con số ma.

### `docs/legacy/research/CLAIM_EVIDENCE_MATRIX.md` (2026-09-09) · tài liệu · **0 API call**

> Lưu trữ nguyên byte từ W19 (trước đó ở thư mục docs/thesis, nay không còn); thẩm quyền tuyên bố hiện hành:
> `docs/research/CLAIM_EVIDENCE_MAP.md`.

Ma trận **tuyên bố học thuật ↔ bằng chứng** cho khoá luận: 29 hàng (5 mục tiêu
cụ thể · 7 đóng góp · 5 câu hỏi nghiên cứu · 9 claim đã đăng ký trước · 3 phát
biểu phạm vi), mỗi hàng có *câu ĐƯỢC phép viết* và *câu KHÔNG được phép viết*.

Sáu trạng thái đóng: `PROVED_ON_FROZEN_BENCHMARK` · `PARTIAL` · `NOT_MEASURED` ·
`OUT_OF_SCOPE` · `CONTRADICTED` · `NOT_LOCATED`.

⚠️ **Khác `THESIS_READINESS.md`, không thay nó**: `THESIS_READINESS` là bảng
tuyên bố ↔ bằng chứng ở mức **vận hành**; ma trận này ở mức **học thuật** (mục
tiêu, RQ, đóng góp, giới hạn diễn đạt). Số sống vẫn trỏ về `THESIS_READINESS` và
về artifact, không chép lại.

⚠️ §E tách **chín mức năng lực** và cấm gộp chúng thành một chữ "hỗ trợ"; §F
tách phạm vi hình học thành **ba nhóm** (đã chứng minh · `foundation_only` ·
ngoài phạm vi vì kiến trúc); §G giữ **hai** giá trị candidate (lịch sử lúc đo vs
hiện tại của kho) như hai khái niệm riêng, dù chúng đang trùng nhau.

### `backend/scripts/dev_backend.py` (2026-09-15) · offline-testable · **0 API call**

VÒNG PHÁT TRIỂN BACKEND DOCKER. Một lệnh chuẩn (`up`), một quyết định đọc-thuần
(`check`/`status`), và hai lệnh không cần Docker (`classify`, `fingerprint`).

Xuất: `doc_mo_hinh(goc) → MoHinhAnh` (đọc thẳng `Dockerfile` COPY/WORKDIR,
`.dockerignore`, khối `backend` của compose: build args, bind mount, `env_file`) ·
`danh_sach_dau_vao_anh` / `bam_dau_vao` / `dau_van_anh` (dấu vân tay TẤT ĐỊNH của
đầu vào image) · `phan_loai_thay_doi` (5 lớp, ưu tiên migration > rebuild >
recreate > reload > không làm gì) · `doc_chuoi_migration` / `cong_migration` ·
`quyet_dinh` (6 quyết định) · `DieuKhien(goc, chay, ngu, dong_ho, in_ra)` ·
`che` (che bí mật mọi chuỗi ra) · `main`.

⚠️ **`backend/app` KHÔNG nằm trong dấu vân tay** — bind mount `./backend/app:/app/app`
che đích `COPY app ./app`, nên mã ứng dụng đến từ đĩa host lúc chạy. Đó là lý do
sửa `.py` không đòi build lại, và cũng là lý do **Git HEAD không được dùng làm
điều kiện rebuild** (commit tài liệu đổi HEAD mà không đổi image).

⚠️ Chuẩn hoá CRLF dùng chung `freeze_evaluation_candidate.bam_noi_dung` — MỘT chính
sách cho mọi dấu vân tay nội dung của kho, nên clone lại trên máy khác không làm
lệch băm.

⚠️ Docker được gọi qua **transport tiêm được** (`chay`), nên toàn bộ quyết định
test được offline: 0 Docker, 0 mạng, 0 tiến trình con.

Nhãn image do `backend/Dockerfile` ghi (`org.algosim.backend.{git-sha,build-time,
requirements-sha256,image-inputs-sha256}`); build arg tương ứng khai ở
`docker-compose.yml`. Không truyền ⇒ nhãn `unknown` ⇒ launcher đọc là CHƯA BIẾT.

### Bốn runner tuyến QUAN HỆ CÓ CẤU TRÚC (2026-09-21) · ⚠️ ba cái đầu **TIÊU QUOTA THẬT**

Cả bốn gọi **đường sản phẩm** `pipeline.stage_semantic_analyze` (test cấm
`call_gemini` trực tiếp) và dùng lại hạ tầng của `run_photo_problem_live.py` —
`CongHttp` (trần HTTP ở transport), `BoKhuBiMat`, `ChanMangThat` — cùng `cham()`
của `run_primitive_compiler_ab.py`. **Không** runner nào chạm Vision hay
Synthesis: trần tầng `{vision: 0, synthesis: 0}` chặn ở transport.

- **`run_structured_relation_analyze_live.py`** — MỘT request Analyze trên ca
  controlled `S.ABC`. Xuất `CongQuetCam(CongHttp)`: cổng HTTP **cộng** phép quét
  thân request tìm dấu vết ground truth (có cửa sổ chứng: nhét dấu vết giả thì
  phải bắt được).
- **`diagnose_structured_relation_prompt.py`** · **0 request** — quy nguyên nhân
  về `PROMPT_INSTRUCTION_GAP` / `MODEL_NONCOMPLIANCE` / `SCHEMA_CAPABILITY_GAP` /
  `EVALUATOR_ERROR` / `INDETERMINATE`. Xuất `da_ap_dung` · `proposed_prompt_delta`
  · `prompt_delta_simulation_proof` · `classify_test_collection` ·
  `doc_cache_version` (đọc **mã nguồn** `app/main.py`, không import — import nạp
  `.env`).
- **`run_structured_relation_revalidation.py`** — MỘT request tái kiểm sau bản vá
  prompt. `kiem_tuong_duong_request()` dựng lại thân request cũ từ blob prompt
  `eeacd67` và đòi nó băm đúng `e30f0ddd…` — chứng minh hai lượt chỉ khác nhau ở
  prompt.
- **`run_multicase_benchmark.py`** (runner **/2** từ 2026-09-21) — 12 ca đóng băng
  (8 dương, 4 âm), Stage A có cổng đăng ký trước rồi mới tới Stage B. Chỉ còn chạy
  lượt **completion**: `--live` bắt buộc `--tiep-tuc <CASE_RESULTS lịch sử>`, vì
  chạy lại ca đã có kết quả bị cấm. Xuất `canonical_dataset_sha` (băm đề + đáp án
  + **thứ tự**) · `cong_stage_a` · `hang_doi_con_lai` (ca đăng ký trừ ca đã có kết
  cục hợp lệ, theo thứ tự đóng băng) · `tao_cong_completion` (trần transport =
  **độ dài hàng đợi**, không phải hằng 12) · `CongQuanSat` + `quan_sat_request`
  (băm **đúng byte** thân request, model lấy từ URL, băm `responseSchema`; bỏ
  query chứa khoá; request lệch kỳ vọng bị chặn **trước** transport bằng
  `LoiTuongDuongRequest`) · `dung_request_du_kien` (request kỳ vọng qua đúng
  `stage_semantic_analyze` với transport giả) · `ghi_envelope_nguyen_tu` (ghi
  NGAY sau từng ca: tệp tạm → fsync → replace) · `chay_mot_ca` (nay **gọi**
  `quy_ket_that_bai`; ca âm chấm theo registry quan hệ đề nói + đối chiếu từ chối
  đúng khiếm khuyết) · `dung_contact_sheet`.
  ⚠️ **Toàn lượt chạy trong MỘT `asyncio.run`** — một vòng lặp mỗi ca đã đóng
  `AsyncHTTPTransport` dùng chung và bị quy nhầm thành lỗi provider; tốn 2 request.
  ⚠️ `quy_ket_that_bai`, `loai_su_co`, `_wilson` nay **nhập từ** bộ tổng hợp — runner
  không còn bộ phân loại riêng (`test_runner_KHONG_mang_bo_phan_loai_rieng…`).
  **Registry v2** (`N04_TARGETED_REJECTION_REGISTRY_V2_PREREGISTRATION`):
  `kiem_rang_buoc_registry()` chạy sau kiểm khoá, **trước** hàng đợi và request
  đầu tiên — nạp v2 qua bộ nạp, đòi overlay **đã commit và trùng HEAD**
  (`REGISTRY_V2_NOT_COMMITTED`) và mã sản phẩm khớp candidate đã khai
  (`PRODUCT_CANDIDATE_DRIFT`). Hỏng ⇒ `PRECHECK_REGISTRY_BINDING.json` +
  `EXIT_PRECHECK`, 0 request; xanh ⇒ `REGISTRY_BINDING.json` ghi trước request và
  kết quả mang `TARGETED_REGISTRY`. `chay_tang_dung` ghi thêm `ADAPTER_RULE_ID` +
  `ADAPTER_PHASE`; ca âm mang `TARGETED_REJECTION_V2`, `DATASET_ROLE`,
  `TARGETED_REGISTRY_RESOLVED_SHA256`. Thân request, thứ tự ca, ngân sách 6 **không đổi**.
  Test: `tests/geometry/test_multicase_benchmark.py` +
  `tests/geometry/test_completion_runner_repair.py` (G1–G9, kịch bản A–E chạy
  `main()` thật qua transport giả) + `tests/geometry/test_n04_targeted_registry_v2.py`
  (36 ca: khoá v1, bộ nạp fail closed, N04 A–G, N01–N03 parity, ràng buộc runner).
  ⚠️ Mọi test gọi `main()` thật **đỏ trên cây có overlay chưa commit** — đúng thiết
  kế; kiểm chúng ở worktree sạch.
  **Runner /3** (`COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY`, 2026-09-22):
  - **R1 · ràng buộc 17 trường** — `TRUONG_RANG_BUOC` · `DANG_KY` (giá trị đăng ký trước:
    gốc kho, nhánh, cache 99, model, băm registry v2, thứ tự ca, ngân sách 6) ·
    `dung_rang_buoc` (băm từ ĐÚNG byte runner dùng; prompt/schema/model lấy từ request
    kỳ vọng) · `ky_vong_rang_buoc` (kỳ vọng dẫn ĐỘC LẬP: overlay v2, EXPECTED_REQUEST_HASHES,
    `git rev-parse HEAD`, blob đã commit ở HEAD, băm tệp chốt LÚC NẠP module) ·
    `kiem_rang_buoc_day_du` (fail closed: `BINDING_FIELD_MISSING:<trường>`,
    `BINDING_FIELD_TYPE:<trường>`, `BINDING_*_MISMATCH`/`*_DRIFT`, `BINDING_TIMESTAMP_INVALID`) ·
    `ghi_rang_buoc` (ghi nguyên tử + nạp lại + kiểm lại; lượt nối lại phải TRÙNG, trừ mốc
    giờ ⇒ `BINDING_RESUME_MISMATCH`) · `dong_ho` (test thay giờ cố định).
  - **R2 · nhật ký bền** — `ghi_json_nguyen_tu` (MỘT cách ghi: tạm cùng thư mục → fsync →
    `os.replace` → đọc lại; `ghi_envelope_nguyen_tu` gọi nó) · `NhatKyHoanTat`
    (`cases/<ca>.json` là nguồn sự thật, `COMPLETION_INDEX.json` là tóm tắt; trạng thái
    `TRANG_THAI_CA`; `mo_lai` nối lại: `RESERVED` ⇒ `TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH`,
    KHÔNG gửi lại, ngân sách không hoàn; `TRANSPORT_COMPLETED` chưa chấm ⇒
    `SCORING_NOT_COMPLETED_AFTER_CRASH`; `PLANNED` ⇒ chứng minh được CHƯA gửi; dọn `*.tmp`) ·
    `CongBenVung` (nằm GIỮA cổng ngân sách và transport thật: đặt chỗ bền TRƯỚC khi byte
    rời tiến trình, kết cục transport bền NGAY khi có) · `LoiNhatKy` (`BaseException` có
    chủ ý — `CongHttp` bắt `Exception` và sẽ quy nhầm thành lỗi provider) ·
    `ly_do_dung_ca` (chính sách dừng, một định nghĩa cho vòng lặp và nối lại) · `_ket_thuc`.
  - **R3 · lỗi tầng chấm** — `_ban_ghi_van_chuyen` (phần bản ghi do request quyết định) ·
    `_cham_ca` (chấm trên BẢN SAO; ném ⇒ bỏ bản chấm dở) · `ma_loi_cham`
    (`SCORING_EXCEPTION:<lớp trong LOI_CHAM_CHO_PHEP | UNLISTED>` ·
    `SCORING_REGISTRY:<mã bộ nạp>`; không thông điệp, không traceback).
  Test: `tests/geometry/test_completion_measurement_repair_post_safety.py` (54 ca: cổng
  không mạng/không khoá/không `.env` · R1 17 trường thiếu + 18 giá trị sai + 3 trôi thật ·
  R2 bền trước transport, chết ở P07, lỗi provider, nối lại RESERVED/TRANSPORT_COMPLETED/
  SCORED, ghi nguyên tử · R3 lỗi chấm). ⚠️ Chúng gọi `main()` thật và phép so blob tại
  HEAD ⇒ chỉ xanh khi runner/bộ tổng hợp ĐÃ commit — kiểm ở worktree sạch.
- **`aggregate_multicase_completion.py`** (2026-09-21) · offline · **0 request** —
  bộ **TỔNG HỢP TẤT ĐỊNH** và thẩm quyền duy nhất cho: `quy_ket_that_bai`
  (`MA_QUY_KET`: 17 mã của đặc tả + `SERVER_POINT_BINDING_GAP` +
  `PRODUCT_ACCEPTED_DEFECTIVE_INPUT`; chạy được trên bản ghi lịch sử đã khử thô) ·
  `doi_chieu_tu_choi` (`TARGETED_REJECTION_MATCH` — phản hồi `{}` có thể an toàn
  nhưng không bao giờ "đúng khiếm khuyết") · `tong_hop_token` (thiếu usage ⇒
  `UNKNOWN`, không bao giờ 0) · `tong_hop_do_tre` (p50/p95 chỉ HTTP 200 có output
  hợp lệ; thời gian chờ lỗi provider đứng riêng) · `phan_loai` + `NEXT_ACTION`
  (có lớp `UNSAFE`; thứ tự: đo hỏng > không an toàn > im lặng > thiếu ca > ngưỡng) ·
  `doc_lich_su` (đọc 33 artifact lịch sử **qua băm**
  `HISTORICAL_EVIDENCE_LINK.json` — lệch một byte ⇒ `MEASUREMENT_INVALID`) ·
  `tong_hop` (mỗi case ID đúng MỘT kết cục; lượt void và lỗi provider ở lại trong
  lịch sử request; không timestamp ⇒ tái lập trùng byte).
  Registry đăng ký trước nó đọc:
  `completion-runner-repair-offline/NEGATIVE_EXPLICIT_RELATION_REGISTRY.json` ·
  `NEGATIVE_TARGETED_REJECTION_REGISTRY.json` · `EXPECTED_REQUEST_HASHES.json`.
  **Registry v2 = OVERLAY, không phải nguồn sự thật thứ hai** (bộ tổng hợp **/2**):
  `doc_registry_tu_choi_v2` nạp v1 (đòi băm `52bc6379…`) + overlay
  `n04-targeted-rejection-registry-v2-preregistration/NEGATIVE_TARGETED_REJECTION_REGISTRY_V2.json`,
  chỉ cho ghi đè `CHO_PHEP_GHI_DE = ("N04",)`, đòi commit hành vi mang bản sửa
  an toàn, trả registry ĐÃ GIẢI + `META` (băm, vai trò dataset, `EVIDENCE_CLASS`).
  Hỏng ⇒ `LoiRegistry(ma)` mã ổn định, **không bao giờ** lùi về v1.
  `doi_chieu_tu_choi_v2`: ca bị ghi đè ⇒ tuple **chính xác** 9 trường
  (`TRUONG_TUPLE`, đọc qua `_tuple_quan_sat`); ca khác ⇒ đúng luật v1 trên entry v1.
  `tong_hop` báo **riêng** `ORIGINAL_PREREPAIR_EXPECTATION_RESULT` (v1) và
  `POST_REPAIR_REGRESSION_EXPECTATION_RESULT` (v2), thêm `DATASET_ROLE` mỗi ca,
  `TARGETED_REGISTRY`, `EVIDENCE_CLASS`, `UNTOUCHED_HOLDOUT_CLAIM = false`; v2 hỏng
  ⇒ `MEASUREMENT_INVALID`. Phân loại chính **không** đọc TARGETED.
  **Bộ tổng hợp /3** (2026-09-22): `KET_CUC_DO_HONG` — bản ghi `MEASUREMENT_ERROR` /
  `TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH` của runner /3 có `trang_thai = MEASUREMENT_ERROR`,
  không quy kết, và làm lượt đo `MEASUREMENT_INVALID` (`MEASUREMENT_ERROR_IN_COMPLETION`).
- **`diagnose_analyze_failure_cluster.py`** (2026-09-22) · offline · **0 request** —
  công cụ chẩn đoán độc lập cho cụm lỗi Analyze P03/P05 (`MODEL_MALFORMED_RELATION`).
  Tách bạch Pha A (trích xuất bằng chứng, không gán root cause, không đoán raw output) và
  Pha B (phân loại có ràng buộc, kiểm schema capability, audit prompt coverage, replay
  phản chứng qua FactGraph/compiler/scene builder, đánh giá khả năng chuẩn hóa tất định).
  Phân loại độc lập P03 và P05 (`HISTORICAL_EVIDENCE_INSUFFICIENT`, confidence
  `NOT_ESTABLISHED`), kiểm `CLUSTER_HOMOGENEITY` (`PARTIAL`), kiểm N03 code alignment
  (`N03_ACCEPTABLE_CODE_CORRECTION_LAYER_REQUIRED = YES`), đối chiếu alias
  `STRUCTURED_ANALYZE_GENERALIZATION_DIAGNOSIS` ≡ `ANALYZE_FAILURE_CLUSTER_DIAGNOSIS`.
  Xuất 15 artifact JSON tại `docs/evaluation/geometry/photo-problem-to-scene/analyze-failure-cluster-diagnosis/`.
  Test: `tests/geometry/test_analyze_failure_cluster_diagnosis.py` (12 ca, 10 fault injections F1–F10).
- **`run_preregistered_failure_reproduction.py`** (2026-09-22, cập nhật SAFE_STRUCTURE_TRACE_REPAIR_OFFLINE) — runner tái hiện độc lập
  cụm lỗi Analyze P03/P05 qua request đã đăng ký trước (ngân sách 2 Analyze, 0 Vision,
  0 Synthesis, 0 Retry). Hợp đồng dấu vết cấu trúc an toàn `analyze-relation-structure-trace/1`
  trích xuất cấu trúc quan hệ trong bộ nhớ và khử toàn bộ dữ liệu thô (raw model output,
  point labels, problem text, msg, ctx, traceback). Vòng đời async thống nhất (duy nhất một
  `asyncio.run()` tại CLI boundary), máy trạng thái từng ca (`PLANNED` → `RESERVED` →
  `TRANSPORT_COMPLETED` → `TRACE_CAPTURED` → `SCORED` → `VERIFIED`) với ghi bền nguyên tử
  (tempfile → fsync → `os.replace` → read-back verification) bảo vệ độc lập từng ca trước khi
  mở ca tiếp theo. Hỗ trợ `--offline-proof` (18 mock fixtures), `--dry-run` và `--live`.
  Xuất artifact tại `docs/evaluation/geometry/photo-problem-to-scene/safe-structure-trace-repair-offline/`
  và `fresh-preregistered-failure-reproduction/`.
  Test: `tests/geometry/test_preregistered_failure_reproduction.py` (9 ca),
  `tests/geometry/test_safe_structure_trace_repair_offline.py` (37 ca, 18 fixtures, 12 fault injections F1–F12),
  và `tests/geometry/test_safe_structure_trace_repair_evidence_reconciliation.py` (21 ca, 10 fault injections FI-01–FI-10).
- **`kind_aware_trace_evaluator.py`** (2026-09-22, MODEL_VARIANCE_EVIDENCE_REVIEW) — evaluation tooling
  đối soát bằng chứng độc lập cho safe structural trace và token audit. Khắc phục false positive
  `MULTIPLE_STRUCTURAL_DEFECTS` bằng kiểm tra trường kind-aware (loại bỏ lỗi do default tuple rỗng
  từ Pydantic model dump), đảm bảo bất biến quan hệ đã accepted không bao giờ mang nhãn defect
  (`CANONICAL_VALID`). Phân biệt nghiêm ngặt missing/unobserved token usage (`UNKNOWN`) với số 0
  thực sự, cấm biến missing thành 0. Tách bạch rành mạch Current Output Status (`CANONICAL_VALID`, `HIGH`)
  khỏi Historical Failure Root Cause (`NOT_ESTABLISHED`, `NOT_ESTABLISHED`) và Model Variance Hypothesis.
  Test: `tests/geometry/test_model_variance_evidence_review.py` (20 ca, 10 fault injections F1–F10).
- **`provenance_evidence_collector.py`** (2026-09-22, MODEL_VARIANCE_EVIDENCE_PROVENANCE_REPAIR_OFFLINE) — evaluation tooling
  thu thập và xác minh provenance bằng chứng máy. Tách bạch lớp acquisition I/O (chạy Git với argv list,
  parse JUnit XML, parse pytest terminal summary, tạo manifest thư mục hai lượt chạy) khỏi lớp validation
  thuần túy (phân loại commit identity thành COMMIT_ROLE_LABELING_ERROR với HISTORY_DRIFT = NO, đối chiếu
  ancestry và diff vai trò, kiểm tra F1–F10 theo test node JUnit, chứng minh determinism bitwise qua 2 manifest,
  kiểm tra claim provenance matrix, kiểm tra read-only candidate/cache và quét secret/redaction).
  Test: `tests/geometry/test_model_variance_evidence_provenance_repair.py` (16 ca).

### `docker-compose.dev.yml` (2026-09-15)

Lớp phát triển, đè ĐÚNG MỘT biến `DEV_RELOAD: "1"` để bật nhánh reload có sẵn
trong `CMD` của image. Cố ý KHÔNG khai thêm mount, cổng, nguồn biến môi trường,
chính sách tự khởi động lại hay cơ chế đồng bộ file — mọi thứ ấy đã có hoặc sẽ
che lỗi. Chạy không kèm file này thì hành vi production không đổi một byte.

### `backend/tests/test_dev_backend_launcher.py` (2026-09-15) · offline

25 ca, viết TRƯỚC — nền đỏ 23/23 (module và file override chưa tồn tại; hai ca U/V thêm sau khi
máy thật lộ một lượt đọc nhãn hụt nhịp), kèm **10 phép tiêm** (`FAULT_INJECTIONS.json`). A sửa `.py` được mount ⇒ hot reload, dấu vân
tay không đổi · B `requirements.txt` ⇒ `REBUILD_IMAGE` · C `Dockerfile` ⇒ băm đổi ·
D entrypoint được COPY ⇒ đầu vào image · E tài liệu/test/README ⇒ không làm gì ·
F xoá favicon ⇒ không làm gì VÀ không làm `BACKEND_SOURCE_DIRTY` · G thiếu image ·
H khớp nhãn ⇒ dùng lại, không build · I bốn dạng lệch migration · J migration chờ
⇒ không build, không start · K/L/M đọc file THẬT của kho (dev override · `CMD`
production từng byte · healthcheck `/api/health` bằng `urllib`) · N/O dấu vân tay
tất định, không phụ thuộc thứ tự, CRLF ≡ LF · P bí mật giả không lọt output ·
Q đường dẫn có khoảng trắng · R/S/T chỉ đụng service `backend`, không
`down`/`prune`/xoá volume, build hỏng không thử lại.

U đọc nhãn hụt một nhịp sau build ⇒ ĐỌC LẠI có giới hạn rồi vẫn start, đúng một lần build ·
V nhãn không bao giờ khớp ⇒ KHÔNG start, vẫn đúng một lần build.

⚠️ Phép tiêm F6 bắt được **chính cổng của test M đang nói dối**: `/api/healthz`
chứa `/api/health` như chuỗi con, nên phiên bản `in` của phép so sánh không phân
biệt được hai endpoint. Nay so bằng regex có biên (`(?![\w/])`).

### Documentation Information Architecture & Handoff Hardening (2026-09-22)

- **`backend/scripts/audit_docs_information_architecture.py`** — documentation audit tooling
  kiểm tra toàn diện 11 domain tài liệu: tính duy nhất của ownership, phân định stable/mutable separation,
  toàn vẹn liên kết nội bộ Markdown, sự tồn tại của các đường dẫn được index, tính duy nhất của Wave ID và
  Issue ID, chuỗi đính chính không chu trình (Acyclic DAG), một next action duy nhất, kiểm tra độ dài handoff
  (<= 300 dòng), quét secret và đối soát bằng chứng kiểm thử máy.
  Test: `backend/tests/geometry/test_docs_information_architecture.py` (22 invariants, 14 fault injections F1–F14).
  **W19 (2026-10-04)** thêm `audit_docs_layout(repo_root, catalog_text=None)` — gốc `docs/` là danh sách ĐÓNG:
  mỗi `docs/*.md` thuộc `CANONICAL_DOMAINS`, `PROJECT_DOCS`, hoặc có dòng bảng trong
  `HISTORICAL_REPORTS_CATALOG` (`docs/evaluation/HISTORICAL_REPORTS.md`); thư mục con thuộc `DOCS_SUBDIRS`; catalog
  rỗng là FAIL. `NAVIGATION_DOCS` (README gốc + hub research/evaluation/legacy/architecture + bản đồ tuyên bố +
  catalog) vào phạm vi mặc định của `audit_internal_links`. Producer của catalog:
  `docs/evaluation/geometry/runs/w19-docs-organization/diagnostics/build_report_catalog.py`; consumer:
  `audit_docs_layout`. Test thêm: `test_inv_23_docs_root_is_a_closed_list`, `test_inv_24_navigation_hubs_links_resolve`,
  `test_fi_17_stray_root_report_rejected`, `test_fi_18_unreadable_catalog_rejected`.

- **Tài liệu Canonical mới:**
  - `AGENTS.md` (root entry point cho AI sessions và Coding Agents)
  - `docs/ROADMAP.md` (lộ trình ưu tiên khóa luận P0–P6)
  - `docs/OPEN_ISSUES.md` (danh mục vấn đề mở với stable IDs)
  - `docs/MIGRATION_CHECKLIST.md` (20 cổng di chuyển compiler-first)
  - `docs/AI_CONTEXT_BUNDLE.md` (bản tóm tắt handoff <= 300 dòng)
  - `docs/EVIDENCE_INDEX.md` (chỉ mục báo cáo, artifact và chuỗi đính chính)
  - `docs/README.md` (cổng điều hướng tài liệu trung tâm)

### Primitive Compiler Second Family Selection & Preregistration (2026-09-22)

- **`backend/scripts/validate_second_family_preregistration.py`** — preregistration validation tooling
  (chế độ chỉ đọc) kiểm toán và thẩm định độc lập 3 tệp tĩnh: ma trận lựa chọn 3 ứng viên (`SECOND_FAMILY_SELECTION_MATRIX.json`),
  bộ 8 ca kiểm nghiệm (`SECOND_FAMILY_MANIFEST.json`) và ground truth độc lập (`SECOND_FAMILY_GROUND_TRUTH.json`).
  Kiểm tra 18 tiêu chí bắt buộc: tổng trọng số 100, 3 ứng viên A/B/C, họ `right_triangle_base_right_prism_volume` đạt điểm cao nhất,
  5 ca dương / 3 ca âm, không chứa `expected_answer` trong compiler input, nhãn điểm không dấu `'`, tính toán phân số chính xác,
  mã từ chối cô lập, và bất biến sản phẩm/candidate/cache không đổi.
  Test: `backend/tests/geometry/test_second_family_preregistration.py` (18 tests).

### Primitive Compiler Second Family Preregistration Evidence Repair (2026-09-22)

- **`backend/scripts/audit_second_family_preregistration_evidence.py`** — evaluation & correction tooling
  thực hiện kiểm toán bằng chứng và tái thẩm định cho wave preregistration họ lăng trụ:
  Audit A (Curriculum evidence: phát hiện không có tài liệu THPT chính thức trong repo, kết luận NOT_ESTABLISHED_OFFLINE, loại khỏi thang điểm xác nhận);
  Audit B (Recalculated Selection Matrix: tái tính điểm độc lập, Candidate B đạt 75.5/80 = 94.375/100, bảo toàn vị trí đứng đầu với margin +7.5pt / +9.375% khi loại bỏ tiêu chí chưa chứng minh, SELECTION_ROBUSTNESS = PASS);
  Audit C (Vertical Slice Scope Map: phủ nhận tuyên bố "chỉ cần 1 primitive", vạch rõ 12 tầng kỹ thuật cần mở rộng trong vertical slice);
  Audit D (Semantic Ownership: phân định ranh giới giữa SEMANTIC_STRUCTURE, DEFINITIONAL_CONSEQUENCES_OF_PRISM và LAYOUT_DERIVED);
  Audit E (Rejection Code Status: phân loại mã từ chối hiện hữu vs mã dự kiến/đề xuất);
  Audit F (Label Policy: làm rõ quy ước không dùng dấu ' là DATASET_CONVENTION_ONLY, không phải GLOBAL_POINT_LABEL_PROHIBITION);
  Audit G (Commit Role & Worktree: phát hiện COMMIT_ROLE_SCOPE_DRIFT = YES trong commit 2 của wave trước, ghi nhận DIRTY_ONLY_USER_FAVICON).
  Sinh 12 artifacts JSON đính chính tại thư mục correction.
  Test: `backend/tests/geometry/test_second_family_preregistration_evidence_repair.py` (12 tests, 6 fault injections).

### Primitive Compiler Second Family Source Scope Reconciliation (2026-09-22)

- **`backend/scripts/reconcile_second_family_source_scope.py`** — source audit & scope reconciliation tooling
  thực hiện đối soát mã nguồn và ranh giới kỹ thuật thật sự cho họ bài toán lăng trụ đứng đáy tam giác vuông:
  Audit A (Historical score: sửa sai điểm lịch sử 94.0 -> 95.5 / 100, chuẩn hóa 75.5 / 80 = 94.375 / 100);
  Audit B (Registry identity: xác nhận COMPILER_PRIMITIVE_REGISTRY gồm 6 hàm, loại bỏ phantom inventory 7 entries);
  Audit C (Structured relations: xác nhận perpendicular_lines và perpendicular_line_plane đủ cho lăng trụ);
  Audit D (Layer classification: phân loại 12 tầng, chứng minh RequestContract = CHANGE_REQUIRED do thiếu trường chở lăng trụ, kiểm toán 5 kinds của SourceInvariant);
  Audit E (Semantic IR: tái sử dụng nguyên trạng construct_solid cho lăng trụ 6 đỉnh 5 mặt);
  Audit F (Measurement kernel: tái sử dụng nguyên trạng the_tich_da_dien với exact Fraction 30 và 5/4);
  Audit G (Frontend renderer: tái sử dụng Scene3D mesh rendering và nét đứt camera);
  Audit H (Routing: cô lập trong vertical slice, duy trì DEFAULT_MODE = LLM_ONLY);
  Audit I (Semantic ownership: phân định ranh giới 4 tầng RequestContract -> adapter -> FactGraph -> primitive projection);
  Audit J (Final decision: khóa INCOMPLETE do bế tắc RequestContract schema giữa Direction A và Direction B).
  Sinh 14 artifacts JSON tại `docs/evaluation/geometry/photo-problem-to-scene/second-family-source-scope-reconciliation/`.
  Test: `backend/tests/geometry/test_second_family_source_scope_reconciliation.py` (12 tests).

### Generic Solid Topology Contract Design & Preregistration (2026-09-22)

- **`backend/scripts/validate_generic_solid_topology_preregistration.py`** — contract validation & topology audit tooling
  thực hiện kiểm toán và tiền đăng ký thiết kế hợp đồng topology khối đa diện tổng quát offline:
  Audit A (Precheck: bảo toàn nhánh, 103 files candidate, cache version 99, default mode LLM_ONLY, và working tree clean);
  Audit B (SSOT: structured families dùng family fields làm canonical source và suy diễn tất định faces; generic polyhedron dùng faces);
  Audit C (True Discriminated Union: SolidTopologySpec trên solid_kind; phân lập INTERNAL_CANONICAL_CONTRACT và MODEL_FACING_TRANSPORT_SCHEMA);
  Audit D (Gemini Sanitizer: chứng minh flattened transport schema đi qua _sanitize_gemini_schema không bị None; ghi nhận GEMINI_LIVE_SCHEMA_ACCEPTANCE = NOT_ESTABLISHED_UNTIL_LIVE_REVALIDATION);
  Audit E (Supported Topology Class: định nghĩa closed, connected, orientable, genus-zero polygonal 2-manifold; Euler V-E+F=2 không chứng minh tính lồi);
  Audit F (Prism Correspondence: song ánh bảo toàn kề cận chu kỳ D_n trên C_n; bắt chéo/xoắn n=4 bị chặn bởi NON_CYCLIC_CORRESPONDENCE);
  Audit G (Declared Vertex Universe: xác lập cross-contract boundary cho INV-TOPO-01; validator không đọc problem_text);
  Audit H (Fixtures: chạy 5 positive và 11 negative fixtures; chặn đúng mã lỗi);
  Audit I (Provenance: phân định GIVEN vs DEFINITIONAL_DERIVED, cấm engine giả mạo GIVEN);
  Audit J (Hypothesis: PUBLICATION_HYPOTHESIS kiểm định được, 15 benchmark metrics);
  Audit K (Compatibility: 4 chiều tương thích ngược dạng EXPECTED_*);
  Audit L (Provisional Allowlist: 8 files kèm 7 điều kiện audit tiên quyết).
  Sinh 9 artifacts JSON tại `docs/evaluation/geometry/photo-problem-to-scene/generic-solid-topology-contract-design/`.
  Test: `backend/tests/geometry/test_generic_solid_topology_preregistration.py` (14 tests).

### Primitive Compiler Second Family Vertical Slice Offline (2026-09-22)

- **`backend/app/simulation/geometry_compiler/primitives.py`** — bổ sung hàm `construct_prism(name, base_cycle, top_cycle, correspondence)` trả về `construct_solid`, đăng ký vào `REGISTRY["construct_prism"]` (nâng dynamic primitive count lên 7). `memory_declaration` nhận thêm `provenance: str | None = None`.
- **`backend/app/simulation/geometry_compiler/compiler.py`** — bổ sung họ hình học thứ hai `SUPPORTED_FAMILY_PRISM = "right_triangle_base_right_prism_volume"`, dataclass `RangBuocPrism`, bộ đánh giá eligibility `_danh_gia_eligibility_prism` (chặn ca âm N01 thiếu chiều cao, N02 nhiều góc vuông, N03 thiếu vuông góc đáy) và bộ phát hành `_bien_dich_prism` (phát hành tọa độ chính xác, 7 bước dựng `BuocDung` sư phạm, tính thể tích và gán `assign_final_memory`).
- **`backend/app/simulation/geometry_compiler/fact_graph.py`** — thêm `"prism"` vào `LOAI_NUT`, lưu và chuẩn hóa `solid_topology` trong `GeometryFactGraph` và `dung_graph()`.
- **`backend/app/simulation/geometry_compiler/contract_adapter.py`** — chuyển giao `solid_topology` từ `RequestContract` sang `dung_graph()`.
- **`backend/app/simulation/semantic_program/request_contract.py`** — bổ sung `PrismTopologySpec` và trường `solid_topology: Optional[PrismTopologySpec] = None` trong `RequestContract`.
- **`backend/app/simulation/semantic_program/contract.py`** — bổ sung `provenance: Optional[Literal["GIVEN", "MODEL_ASSUMPTION", "LAYOUT_DERIVED"]]` trong `MemoryDeclaration` và `DeclarePointStmt`.
- **`backend/app/simulation/semantic_program/analyze_contract.py`** — bổ sung `_luoc_do_solid_topology` (chỉ cho phép `prism`), hàm đọc và xác thực `_doc_solid_topology` fail-closed, và nạp `solid_topology` vào `build_request_contract`.
- **`backend/app/simulation/semantic_program/grounding_gate.py`** — bổ sung `_extract_declared_vertex_universe` xây dựng universe điểm 100% từ structured contract data (không đọc `problem_text`), kiểm tra nghiêm ngặt `LAYOUT_DERIVED`.
- **`backend/app/simulation/semantic_program/structured_relations.py`** — cập nhật `diem_hop_dong` nhận diện điểm từ `contract.solid_topology` (`base_cycle` + `top_cycle`).
- **`backend/app/main.py`** & **`backend/cache_identity.lock.json`** — bump `CACHE_VERSION = "100"`, relock danh tính cache.
- **`backend/tests/geometry/test_prism_primitive_compiler.py`** — bộ 25 unit tests kiểm chứng toàn diện vertical slice lăng trụ đứng đáy tam giác vuông: 8 ca benchmark P01–P05 / N01–N03, 10 bài test tô-pô đa tạp, bất biến provenance, hoán vị nhãn, phân số chính xác Fraction, và parity với kim tự tháp lịch sử.

### Scene3D occlusion, edge identity & formation repair (2026-09-28)

Wave `CROSS_FAMILY_HIDDEN_LINE_OCCLUSION_ORACLE_AND_FORMATION_REPAIR` — trạng thái `VERIFICATION_NOT_CLEAN`. Quyết định kiến trúc: `docs/architecture/OCCLUSION_AND_SCENE_IDENTITY_AMENDMENT.md`. `R` = `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair`.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Canonical solid-edge ownership + stable machine edge ID | `backend/app/simulation/semantic_program/scene3d.py` (`_canonical_edge_id`, `_attach_topology`) | Edge ID từ endpoint entity IDs (`A_prime`), không từ `display_label`; một logical edge một owner. **Authority: backend** | `build_scene3d` → `scene3d-model.ts` / `scene3d-view.tsx` | `pytest tests/geometry/test_scene3d.py -q` |
| Surface roles + occlusion policy | `backend/app/simulation/semantic_program/scene3d.py` (`surface_role`, `occludes_edges`, `boundary_edge_ids`) | Chỉ `SOLID_FACE` che; `BASE_REGION`/`SECTION_REGION`/`CUTTING_PLANE`/`AUXILIARY_SURFACE` không che. **Authority: backend** | `_attach_topology` → `scene3d-edge-visibility.ts` | `pytest tests/geometry/test_scene3d.py -q` |
| Typed formation semantics | `backend/app/simulation/semantic_program/scene3d.py` (`_build_formation`, `geometry_progress`) | Kind `GEOMETRY_CONSTRUCTION`/`MEASUREMENT`/`EXPLANATION`/`FINAL_RESULT` phát tại producer; frontend không suy từ learner text | `build_scene3d` → `scene3d-view.tsx` | `pytest tests/geometry/test_scene3d.py -q` |
| Section endpoint provenance | `backend/app/simulation/geometry/section.py` (`_vertex_source`, `SectionVertexSource`) | Endpoint `SOLID_VERTEX` / `SOLID_EDGE_INTERSECTION` → section edge ID bền. **Authority: kernel** | `cross_section` → `scene3d.py` | `pytest tests/geometry/test_section.py -q` |
| Adaptive world-space classifier | `frontend/src/simulations/domains/geometry/scene3d-edge-visibility.ts` (`canonicalEdgesOf`, `classifySolidEdgeVisibility`) | Ray/triangle world-space, lưới 16 ô + refine tới ≤0,5 px vật lý; phát span `VISIBLE`/`HIDDEN`/`MIXED`. **Authority: product visibility** | scene → `scene3d-view.tsx` (`updateCanonicalEdgeVisibility`, `canonicalEdgeMaterial`) | `npx vitest run src/simulations/domains/geometry/` |
| Fault gates (ID swap, small occluder, mixed dash, highlight dash, surface policy, 120 immutable frames, duplicate owner) | `frontend/src/simulations/domains/geometry/scene3d-occlusion-gates.test.ts` | Tiêm lỗi cho classifier/renderer | — | `npx vitest run src/simulations/domains/geometry/scene3d-occlusion-gates.test.ts` |
| Independent perspective oracle + ray/triangle reference | `backend/scripts/scene3d_occlusion_oracle.py` | Stdlib-only, **không import** product; clip interval projected + depth perspective-correct (clip `w`); reference thứ hai bằng camera ray/triangle. **Authority: evidence** | → `measure_scene3d_occlusion.py` | `pytest tests/geometry/test_scene3d_occlusion_oracle.py -q` |
| Product ↔ oracle join | `backend/scripts/measure_scene3d_occlusion.py` | So exact ID set + span; drift ghi proposed result vào diagnostics và fail closed, **không** refreeze expectations | browser JSON + oracle → `R/results/OCCLUSION_MEASUREMENT.json` | `pytest tests/geometry/test_scene3d_occlusion_oracle.py -q` |
| Browser / performance gate | `frontend/scripts/compiler-scene-suite.mjs` (hook `__geo3d_occlusion_performance`) | Sáu family, semantic/causal/formation/dash/owner + mobile `immutable_120_frames` | `dist/` → `R/results/BROWSER_EVIDENCE.json` | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Contact sheet + crops | `backend/scripts/build_scene3d_visual_evidence.py` | Dựng contact sheet/crop từ PNG authoritative | screenshots → `R/contact-sheet.png`, `R/crops/` | chạy với `--run-dir` `--browser` |
| Frozen human visibility fixture | `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/inputs/human_expected_visibility.json` | Kỳ vọng người duyệt; product/oracle không được tự sửa | commit `80766b90` → `measure_scene3d_occlusion.py` | `pytest tests/geometry/test_human_expected_visibility.py -q` |
| Worktree recovery inventory | `docs/evaluation/geometry/worktree-recovery/WORKTREE_RECOVERY_INVENTORY.json` (+ `recovered/`) | Phân loại SHA-256 mọi file untracked của 5 worktree tạm trước khi gỡ. Producer: phiên wave, **không có script commit** | commit `09934eb7` → `EVIDENCE_INDEX.md` | đọc `summary` (required/unknown/unique-commit risk = 0) |
| Correction/evidence run | `docs/evaluation/geometry/runs/20260928-cross-family-hidden-line-occlusion-oracle-and-formation-repair/` | `REPORT.md` · `RUN.json` · `MANIFEST.json` · `HANDOFF.md` · `results/VERIFICATION_SUMMARY.json`; bất biến, `LEGACY_LONG_RUN_ID` | commit `09934eb7` → `EVIDENCE_INDEX.md` | `python scripts/audit_docs_information_architecture.py` |

### Verification cleanup after occlusion repair — w09 (2026-09-28)

Run `docs/evaluation/geometry/runs/w09-verify-cleanup/`. Mỗi mục trả lời một bản ghi trong `diagnostics/VERIFICATION_FAILURE_INVENTORY.json`.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Timeline details qua biên vận chuyển | `backend/app/simulation/semantic_program/simulation_state.py` (`_json_an_toan`) | Giá trị hình học trong trace (`Plane3`, `Circle3`, `Ellipse3`…) ra envelope dưới khuôn của `_than_hinh_hoc`; kiểu lạ ném `TransportTypeError`. Từ 50a31e0b `details` đi tới `scene3d.events` ⇒ thiếu bước này là HTTP 500 ở `main.py` | `build_timeline` → `scene3d.build_scene_events` | `pytest tests/geometry/test_scene3d.py -q` |
| Khoá camera chuẩn hoá của classifier | `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (`updateCanonicalEdgeVisibility`, hàm `khoa`) | 10 chữ số có nghĩa, ±0/nhiễu < 1e-12 → 0: nhiễu ULP của damping không còn tính lại mỗi frame; dịch chuyển > 0,5 px vẫn tính lại | camera → edge spans | `npx vitest run src/simulations/domains/geometry/scene3d-occlusion-gates.test.ts` |
| Cổng settle + cửa sổ 120 frame | `frontend/scripts/compiler-scene-replay-lib.mjs` (`cameraMotion`, `settleCamera`, `assessImmutableWindow`, `CAMERA_SETTLE_TOLERANCE`) | Chỉ chụp camera / mở cửa sổ bất biến sau khi camera đứng yên trong ngưỡng 1e-9 tương đối; không hội tụ ⇒ `SETTLING_TIMEOUT` kèm chẩn đoán | `compiler-scene-suite.mjs` (`settleOrRecord`) | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Danh tính camera đóng băng | `backend/scripts/measure_scene3d_occlusion.py` (`canonical_camera`, `canonical_camera_sha256`, `load_camera_preimages`, `camera_identity`, `--camera-preimages`) | Hash thô khớp ⇒ `EXACT`; không khớp ⇒ preimage đã xác minh sha256 + tương đương phép chiếu ≤ 0,5 px ⇒ `CANONICAL_EQUIVALENT`. Registry giữ nguyên từng byte | preimages + browser → `OCCLUSION_MEASUREMENT.json` | `pytest tests/geometry/test_human_expected_visibility.py -q` |
| Preimage camera đã đăng ký | `docs/evaluation/geometry/runs/w09-verify-cleanup/inputs/REGISTERED_CAMERA_PREIMAGES.json` | Chuỗi snapshot có sha256 = đúng hash trong registry 80766b90, khôi phục bằng replay trình duyệt; buộc vào sha256 của registry | → `load_camera_preimages` | `pytest tests/geometry/test_human_expected_visibility.py -q` |
| Interpreter của T3 | `frontend/scripts/full-gate.mjs` (`repoRootOf`, `resolvePython`, `PythonEnvError`, `runGate`) | Root qua `fileURLToPath` (đường dẫn có dấu cách); `--python`/`ALGO_SIM_PYTHON` → venv đang kích hoạt → venv của cây → venv của worktree chính (git common dir) → lỗi có cấu trúc, không rơi về `python` trên PATH; lỗi spawn được in ra | → năm cổng con T3 | `node --test frontend/scripts/full-gate.node-test.mjs` |
| Test của interpreter T3 | `frontend/scripts/full-gate.node-test.mjs` | Đường dẫn có dấu cách · interpreter tường minh / thiếu / sai / lệch phiên bản · worktree không venv · truyền exit code và lỗi spawn | — | `node --test frontend/scripts/full-gate.node-test.mjs` |
| Cửa sổ bất biến bắt đầu từ bộ đếm 0 | `frontend/scripts/compiler-scene-suite.mjs` (lệnh reset) | Trang chỉ công bố lại `__geo3d_occlusion_performance` ở frame kế tiếp ⇒ xoá bản công bố cùng task với reset, poll không đọc được cửa sổ cũ | → `assessImmutableWindow` | chạy suite; `immutable_window.frames` ≥ 120 thật |
| Băm theo nội dung blob | `backend/scripts/measure_scene3d_occlusion.py` (`load_camera_preimages`), `backend/scripts/generate_generic_tier_a_fixtures.py` (`_sha`) | CRLF→LF trước khi băm: worktree `core.autocrlf` checkout ra CRLF, hash đã ghi là LF | — | `pytest tests/geometry/test_human_expected_visibility.py tests/geometry/test_generic_tier_a_fixture_generator.py -q` |
| Precheck chạy được ở detached HEAD | `backend/scripts/diagnose_analyze_failure_cluster.py`, `backend/scripts/run_preregistered_failure_reproduction.py` (`branch_ok`) | Detached HEAD không in tên nhánh; quan hệ tổ tiên của HEAD là bằng chứng | — | `pytest tests/geometry/test_branch_independent_harness.py -q` |

### Human visual review + pedagogical playback — w10 (2026-09-29)

Run `docs/evaluation/geometry/runs/w10-pedagogical-playback/`. Trả lời review người của w09 (`FAIL_REQUIRES_PEDAGOGICAL_VISUAL_REPAIR`). Mọi giải pháp đọc topology/ngữ nghĩa cảnh — không rẽ nhánh theo tên họ bài, case ID, đề hay tên đỉnh.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Máy trạng thái playback | `frontend/src/simulations/domains/geometry/scene3d-playback.tsx` (`moiNhat`, `datTrangThai`, `xemLai`) | Nhịp phát đọc bản MỚI NHẤT qua ref (chế độ điều khiển ngoài từng kẹt ở bước 1); dừng ngay ở bước cuối; nút "Xem lại" đưa bước về 0, bỏ chọn rồi phát. Không bao giờ tự đặt `selected_id` | player → `InteractionState` | `npx vitest run src/simulations/domains/geometry/scene3d-playback.test.tsx` |
| Góc nhìn sư phạm | `frontend/src/simulations/domains/geometry/scene3d-camera.ts` (`danhGiaGocNhin`, `doLuoiGocNhin`, `datNguong`, `NGUONG_GOC_NHIN`, `chonHuongNhin`, `khungNhinSuPham`) | Hướng Z-up chọn trên lưới phương vị 10° × góc ngẩng 15–40° theo diện tích bao chiếu, độ sâu, khoảng đỉnh↔đỉnh, đỉnh↔cạnh (bỏ điểm nằm trên cạnh trong 3D), độ nghiêng mặt. Ngưỡng: khoảng hở ≥ ½ khối lập phương tham chiếu ở hướng cũ; diện tích/độ sâu ≥ 60%/50% cực đại của CHÍNH cảnh; mặt ≥ 6° so với tia nhìn. Khoảng cách vừa khít theo HÌNH CHIẾU + căn giữa. Cảnh không cạnh ⇒ khung cũ | `cauTrucGocNhin` → `scene3d-view.tsx` (`vuaKhungRef`) | `npx vitest run src/simulations/domains/geometry/scene3d-camera.test.ts` |
| Cấu trúc cảnh cho góc nhìn | `frontend/src/simulations/domains/geometry/scene3d-model.ts` (`cauTrucGocNhin`) | Đỉnh (khử trùng) · cạnh · mặt từ `faces` của khối và đa giác; điểm lẻ vào như đỉnh không cạnh. Không suy hình học | scene → `chonHuongNhin`, `planOrbit` | `scene3d-camera.test.ts` |
| Đặt khung nhìn huỷ đà xoay | `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (`datKhungNhin`) | Một `update()` với damping tắt tiêu hết đà của cú kéo trước, rồi mới đặt pose ⇒ "Xem lại toàn hình" về đúng khung trung tính | `vuaKhungRef` | `scene3d-hidden-lines.test.tsx` |
| Nét cạnh đọc được | `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (`MAU.canh`, `canonicalEdgeMaterial`, `lopChieuSau`) | Mực cạnh riêng (≥ 7:1), tách khỏi màu mặt tô; cả hai lớp tắt `depthTest` (phân loại CPU là thẩm quyền: khuất từng mất hết điểm ảnh, thấy từng nhạt vì MSAA); nét ở hàng đợi trong suốt để vẽ SAU mặt tô; lớp chiều sâu lùi bằng `polygonOffset` | classifier → owner cạnh | `scene3d-hidden-lines.test.tsx` |
| Một cạnh một nét | `backend/app/simulation/semantic_program/scene3d.py` (`_attach_topology`, nhánh `segment3`) + `scene3d-view.tsx` (`doanNhuongCanh`) | Đoạn trùng cạnh khối (theo TÊN đầu mút) mang `boundary_edge_ids`; khi khối có mặt cùng vị trí trình bày thì đoạn chỉ còn vùng bấm (+ dấu góc vuông) | backend → renderer | `pytest tests/geometry/test_scene3d_learner_surface.py -q` |
| Mặt thiết diện tô ở bước khép | `backend/app/simulation/semantic_program/scene3d.py` (`_build_formation`, `fill_visible`) + `scene3d-view.tsx` (nhánh `polygon`) | Nối cạnh cuối chỉ khép viền; bước hoàn tất mới tô ⇒ bước ấy đổi thứ học sinh thấy | formation → renderer | `test_scene3d_learner_surface.py` + `scene3d-hidden-lines.test.tsx` |
| Causal phân tầng | `frontend/src/simulations/domains/geometry/interaction-state.ts` (`tangNhanManh`, `TangNhanManh`) + `scene3d-view.tsx` (`MAU_TANG`, `lamDiu`) + `global.css` (`.la-diu`) | Chỉ khi người dùng chọn: đích > trung gian > dữ kiện (vật tự do); ngoài chuỗi làm dịu (sống qua lần dựng lại cạnh khi xoay); nét đứt giữ nguyên; đóng ô soi / "Xem lại toàn hình" ⇒ trung tính | selection → renderer, nhãn, số đo | `interaction-state.test.ts` + `scene3d-hidden-lines.test.tsx` |
| Ô soi khổ hẹp | `frontend/src/styles/global.css` (`@media (max-width: 48rem)` `.geo3d-soi`) | Chảy DƯỚI sân khấu (`position: static`) — neo đáy từng che dòng đáp số và nút "Xem lại" | — | `npx vitest run src/components/ux-shell.test.tsx` |
| Nút nổi khổ hẹp | `frontend/src/styles/global.css` (`@media (max-width: 48rem)` `.geo3d-san` flex cột, `.geo3d-noi` `position: static; order: -1`) | Hai nút "Tách khối" / "Xem lại toàn hình" vào dòng chảy PHÍA TRÊN khung — ở 390×844 đỉnh cao nhất của hình từng nằm dưới nút. Camera không cần biết giao diện | — | `npx vitest run src/components/ux-shell.test.tsx` |
| Cây không lặp bí danh đáp số | `frontend/src/simulations/domains/geometry/interaction-state.ts` (`semanticTree`) + `scene3d-model.ts` (`SceneObject.alias_of`) | Chỉ bí danh KHÔNG hiện (`alias_of` + `render: "non_visual"`, tức bí danh đáp số) không thành dòng riêng — nó cùng nhãn với nguồn. Bí danh VẪN HIỆN (AD := AB ở hình lập phương) giữ dòng | scene → cây thành phần | `npx vitest run src/simulations/domains/geometry/interaction-state.test.ts` |
| Kết luận của bí danh mang phụ thuộc của nguồn | `backend/app/simulation/semantic_program/scene3d.py` (`_ke_lai`) | Sự kiện kết luận trỏ về nguồn thì mang `depends` của sự kiện đo nguồn — không tự phụ thuộc, không hai bộ phụ thuộc cho một vật | events → formation/causal | `pytest tests/geometry/test_scene3d_learner_surface.py -q` |
| Bộ quan sát cây theo nhãn | `frontend/scripts/compiler-scene-replay-lib.mjs` (`isHiddenAlias`, `aliasTreeRowCheck`, `assessFormationSnapshots`) + `compiler-scene-suite.mjs` (`observeTree`) | Bí danh không hiện: số dòng mang nhãn nó = số vật khác cùng nhãn; formation bỏ nó khỏi tập quan sát. Suite chọn causal qua `alias_of` về nguồn | → `BROWSER_EVIDENCE.json` | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Bấm/kéo không mù | `frontend/scripts/compiler-scene-suite.mjs` (`trustedClick`, `trustedOrbit`, `canvas_boxes`) | Kiểm `elementFromPoint` là đích trước khi bấm/kéo; CHỈ cuộn khi đích bị che/ngoài khung, và cuộn vào GIỮA (không `nearest` — thanh nav dính che mép trên); cuộn mọi lúc làm phép so canvas causal mất nghĩa. Bị che ⇒ báo không bấm được / `ORBIT_START_NOT_ON_CANVAS`. Suite ghi hộp canvas NGAY lúc chụp từng trạng thái | dùng chung suite + runner playback | chạy runner playback mobile `--lap-orbit 5` |
| Bề mặt học sinh (tên, vai, kết luận) | `backend/app/simulation/semantic_program/display_names.py` (`_phan_loai_khoi`, `_DANH_TU_KHOI`, `_VAI_DAI_LUONG`), `scene3d.py` (`_danh_dau_bi_danh`, `_ke_lai`), `simulation_state.py` (`_hinh`) | Khối gọi theo loại suy từ topology (chóp/lăng trụ/hộp chữ nhật/lập phương), fail-closed khi lạ; bí danh đáp số là MỘT kết luận; lời kể có cấu trúc | trace → scene | `pytest tests/geometry/test_scene3d_learner_surface.py tests/geometry/test_display_names.py -q` |
| Runner playback người học | `frontend/scripts/scene3d-playback-check.mjs` (`runPlaybackCheck`, `orbitLap`) | Mở bài, bấm Phát MỘT lần, ghi trạng thái theo thời gian; chụp filmstrip + `neutral_final`/`rotated_neutral`/`causal_selected`/`neutral_restored`; số đo góc nhìn từ camera thật; `--lap-orbit N` lặp orbit có chuyển trạng thái + lý do timeout | `dist/` → `PLAYBACK_EVIDENCE.json` | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Lối đọc đáp số + panel bước trong trình duyệt (regular-square-pyramid-w01, ROADMAP §0.1) | `frontend/scripts/compiler-scene-replay-lib.mjs` (`assessQuantityPicker`, `assessStepsPanel`; `assessGeometrySteps`/`assessPlayback` nhận lời giải thu gọn ⇒ không card Kết quả; `evaluateEvidenceGates` phán đáp số ở lời giải MỞ + `RESULT_CARD_SHOWN_COLLAPSED` + mã của hai cổng mới; `validateSuiteManifest` = BẢY kịch bản, thêm `regular_square_pyramid`) + `compiler-scene-suite.mjs` (`stepsPanelState`, `setStepsPanelOpen`, `quantityDrawer`, `closeQuantityDrawer`, `selectViaPicker`, `deselect`, `scrollOffsets` — mỗi ảnh ghi vị trí cuộn trang, §0.1-9; formation đi với panel MỞ, nhãn bước đọc ở panel thay dải "Đang dựng" đã gỡ; nhảy bước từ panel khi đang phát + đóng panel không reset; đích causal và đáp số chọn qua ngăn «Đại lượng») + `scene3d-playback-check.mjs` (đích causal qua ngăn; mẫu ghi `collapsed`) + `generic-tier-a-scenarios.json` (kịch bản `regular_square_pyramid`) + `backend/scripts/generate_generic_tier_a_fixtures.py` (năm fixture `regular_square_pyramid_*` từ builder `test_regular_square_pyramid.chop_deu`) + `backend/scripts/build_scene3d_visual_evidence.py` (`FAMILY_ORDER` bảy họ; ô `quantity_picker`, `steps_panel_open`/`_closed`; `TEN_TU_CHOI_THEO_HO` — chú thích từ chối riêng của họ) + `scene3d-playback-check.mjs` (`FAMILIES` bảy họ) | Card Kết quả vắng khi thu gọn; ngăn liệt kê đúng ba nhóm oracle và mang đáp số; panel đồng bộ mọi bước tiến/lùi, nhảy bước dừng phát, đóng không reset | `dist/` → `BROWSER_EVIDENCE.json` | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Phán quyết playback + orbit hoạch định | `frontend/scripts/compiler-scene-replay-lib.mjs` (`assessPlayback`, `planOrbit`, `hasDepth`, `ORBIT_OFFSETS_DEG`) | `final_result_shown_once` theo đáp số + bí danh (không so giá trị); orbit chọn trước: có chiều sâu + đổi tập khuất dự đoán — dùng bộ đo góc nhìn của CHÍNH sản phẩm (import `.ts`) | → suite, runner playback | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Orbit suite theo điều kiện | `frontend/scripts/compiler-scene-suite.mjs` (khối orbit, `trustedClick`) | Cử chỉ hoạch định đi trước, ba cú kéo cũ làm dự phòng; mỗi lượt ghi `started_ms`/`ended_ms`/`state`/`reason`; `trustedClick` cuộn tới phần tử trước khi bấm | → `BROWSER_EVIDENCE.json` | chạy suite |
| Đổi camera có KHAI BÁO | `backend/scripts/measure_scene3d_occlusion.py` (`scene_sha256`, `geometry_signature`, `transfer_expectation`, `--declared-camera-change`, `--registered-fixture-root`) | Camera mặc định nay được CHỌN nên camera đã duyệt không còn; registry giữ nguyên byte. Kỳ vọng người chỉ được chuyển khi cảnh đăng ký đúng là cảnh đã duyệt, hình học không đổi, và oracle tái tạo đúng tập đã duyệt ở CẢ camera đăng ký lẫn camera mới ⇒ `DECLARED_CAMERA_CHANGE`; không khai ⇒ vẫn fail-closed | browser + registry + preimages → `OCCLUSION_MEASUREMENT.json` | `pytest tests/geometry/test_human_expected_visibility.py -q` |
| Crop trọn cạnh + contact sheet | `backend/scripts/build_scene3d_visual_evidence.py` (`crop_box`, `edge_records`, `stage_box`, `image_scale`, `to_image_px`, `build`) | Crop chứa HAI đầu mút (chiếu bằng oracle từ camera đã ghi), metadata: family · viewport · state · edge ID máy · nhãn · kỳ vọng/quan sát/oracle · đồng thuận · số owner · chữ ký nét đứt → `images/crops/CROPS_INDEX.json`; sheet chính cắt đúng sân khấu (hộp canvas lúc chụp + dải số đo), formation + filmstrip ở phụ lục. Tỉ lệ ẢNH = bề rộng ảnh / bề rộng khung CSS — dpr renderer (1) khác tỉ lệ ảnh mobile (2). Thay crop 128 px quanh một điểm chứng của w09 | browser + measurement + fixtures → `images/` | `pytest tests/geometry/test_scene3d_visual_evidence.py -q` |
| Test chịu được đường dẫn có dấu cách | `frontend/src/test-tiers.test.ts` (guard) + 12 file test | `fileURLToPath`/`URL` thay `URL.pathname.replace(...)` (giữ `%20`); guard cấm mẫu cũ. Đóng `ISSUE-OPS-FRONTEND-TESTS-SPACE-PATH` | — | `npx vitest run src/test-tiers.test.ts` |

### Pedagogical formula + visual polish — w11 (2026-09-29)

Run `docs/evaluation/geometry/runs/w11-pedagogical-polish/`. Trả lời review người của w10 (`FAIL_REQUIRES_TARGETED_PEDAGOGICAL_REPAIR`). Không rẽ nhánh theo tên họ bài, case ID, đề hay tên đỉnh.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Độ dài đề cho trong chương trình compiler | `backend/app/simulation/geometry_compiler/compiler.py` (`_khai_do_dai_de_cho`, dùng ở `bien_dich`, `_bien_dich_prism`) | Hai họ đáy tam giác vuông khai AB, AC, SA/AD thành đại lượng GIVEN; nhãn xuất xứ + nguồn CHÉP từ FactGraph (compiler không tự gán `GIVEN`). Thiếu nó thì `_provenance` không nối được chiều cao vào thể tích | FactGraph → SemanticProgram | `pytest tests/geometry/test_formula_provenance_closure.py -q` |
| Grounding độ dài theo bất biến | `backend/app/simulation/semantic_program/grounding_gate.py` (`_do_dai_bat_bien`) | `XY_length` khớp một bất biến độ dài của hợp đồng (cùng đoạn, cùng giá trị, cùng mục) là có căn cứ — analyze có thể bỏ sót mục độ dài trong khi server đã neo `SA = 5` từ câu đề. Chiều rejected → served | contract → grounding | `pytest tests/semantic_program/test_grounding_gate.py -q` |
| Công thức thể tích + tham chiếu nhất quán | `backend/app/simulation/semantic_program/scene3d.py` (`_attach_formulas`) | `references` = đúng các vật chữ công thức nhắc tới, theo thứ tự chữ (thể tích: [đáy, chiều cao]); hai ứng viên chiều cao ⇒ không in công thức | scene → thẻ công thức, "Dựa trên" | `test_formula_provenance_closure.py` |
| Vết provenance công thức | `backend/scripts/trace_formula_provenance.py` | canonical input → RequestContract → FactGraph → SemanticProgram → Scene3D → thẻ/"Dựa trên", 0 lượt gọi model; ghi `git_head` + mã sản phẩm sạch/bẩn | → `diagnostics/FORMULA_PROVENANCE_TRACE_*.json` | chạy script |
| "Dựa trên" của bước đo | `frontend/src/simulations/domains/geometry/scene3d-model.ts` (`numericalBasis`) + `scene3d-solution.tsx` (dòng "Dựa trên:" khi lời giải mở; dải dưới thanh bước ở `scene3d-playback.tsx` ĐÃ GỠ ở regular-square-pyramid-w01) | Nguồn SỐ trực tiếp theo thứ tự công thức, không kèm khối (ngữ cảnh); bước không có nguồn số giữ phụ thuộc trace. Ô "Chi tiết" giữ `directDependencies` (phụ thuộc máy) | scene → dòng dưới thanh bước | `npx vitest run src/simulations/domains/geometry/scene3d-playback.test.tsx` |
| Causal bốn tầng | `interaction-state.ts` (`tangNhanManh`, `TangNhanManh` = `dich`/`du_kien_so`/`trung_gian`/`boi_canh`) + `scene3d-roles.ts` (`MAU_VAI_TRO`, W12) + `scene3d-view.tsx` (`MAU_TANG`, `MAU_NEN_BOI_CANH`, `__geo3d_causal_tiers`) + `scene3d-solution.tsx` (`lopDongLoiGiai`) + `tokens.css` (`--geo3d-vai-tro-*`) | Chuỗi số đi theo cạnh `numerical` backend gõ loại. Mỗi màu MỘT nghĩa trên khung lẫn bảng (W12): đích xanh · dữ kiện số cam đậm · trung gian cam nhạt · ngữ cảnh cấu trúc trung tính (cạnh khối giữ mực; thiết diện, đường, mặt phẳng, điểm dựng bỏ màu kiểu sang nét xám `boi_canh` qua `net` trong `buildObject3D`; nền xám nhạt) · ngoài chuỗi làm dịu; vật vừa dựng khi phát cũng xanh "đang xét"; điểm đề cho trung tính | selection → renderer, bảng lời giải | `interaction-state.test.ts` + `scene3d-hidden-lines.test.tsx` + `scene3d-roles.test.ts` + `scene3d-causal-colors.test.tsx` |
| Chấm đỉnh theo px | `frontend/src/simulations/domains/geometry/pick-target.ts` (`DAU_DINH_PX`, `KHUNG_HEP_PX`, `DICH_DIEM_HEP_PX`, `coDauDinhPx`, `banKinhBamPx`, `donViMoiPx`) + `scene3d-view.tsx` (`datCoDauDinh`, `__geo3d_vertex_markers`) | Token MỘT nguồn cho mọi họ: 6 / 7,5 (khung < 768 px) / 9 (đang chọn) px CSS đường kính; vùng bấm 12 / 16 px bán kính; áp mỗi khung theo độ sâu camera, không phụ thuộc DPR. Lưới giữ bán kính gốc 0,09 | render loop | `pick-target.test.ts` + `scene3d-hidden-lines.test.tsx` |
| Đường phụ nhẹ | `scene3d-view.tsx` (`HE_SO_DUONG_PHU`, nhánh `render === "line"`) | Đường vô hạn không được nhấn: độ mờ ×0,45; rõ ở bước dựng nó (formation) hoặc khi được chọn | formation/selection → renderer | `scene3d-hidden-lines.test.tsx` |
| Vật mới dựng (w11 cam → W12 xanh "đang xét") | `scene3d-view.tsx` (`MAU.highlight` = `MAU_VAI_TRO.moi_dung` `0x2563eb`; w11 là cam `0xea580c`, trước nữa `0xfbbf24`) | W12 (quyết định user): cam chỉ còn nghĩa dữ kiện số, nên vật vừa dựng dùng chung xanh với vật được chọn; bản `0xfbbf24` vàng nhạt từng gần biến mất trên nền sáng | formation → renderer | `scene3d-causal-colors.test.tsx` · `scene3d-hidden-lines.test.tsx` |
| Khung nhìn bỏ vật vô hạn | `scene3d-view.tsx` (`diemKhungNhin`, `__geo3d_camera_target`) | Hỏi cờ `voHan`/`chieuSau` cả ở tổ tiên (đường vô hạn là NHÓM hai nét), bỏ chấm đỉnh; "Xem lại toàn hình" ở bước cuối bài thiết diện từng dời tâm nhìn theo đoạn BD | `vuaKhungRef` | `scene3d-hidden-lines.test.tsx` |
| Cổng ảnh xoay không suy biến | `frontend/scripts/compiler-scene-replay-lib.mjs` (`NGUONG_ANH_XOAY`, `cauTrucKhoi`, `baDinhGanThangHang`, `danhGiaAnhXoay`, `danhGiaAnhXoayThuc`, `chieuManHinh`) | Trên ẢNH PHỐI CẢNH: diện tích/độ sâu ≥ 60%/50% cực đại; mặt ≥ 12° theo tia từ mắt; hai cạnh chung đỉnh không sụp và đỉnh không sát cạnh khác (≥ ½ khối lập phương tham chiếu); đỉnh trong khung, không dưới lớp phủ | → suite, runner playback | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Cử chỉ xoay hoạch định | `compiler-scene-replay-lib.mjs` (`cameraSauCuChi`, `orbitPlanThuc`, `orbitCandidates`, `ORBIT_OFFSETS_DEG`) + `compiler-scene-suite.mjs` (`trustedZoomOut`, `overlayRects`) | Mô phỏng OrbitControls (xoay quanh Z qua tâm quỹ đạo, lùi 3/6 nấc ×1/0.95), chấm trước bằng cổng; chỉ gửi cử chỉ đạt; ghi sai số ma trận nhìn dự đoán ↔ thật. Nấc con lăn gửi `100 × DPR` (giả lập DPR 2 chia đôi `deltaY`) | → `BROWSER_EVIDENCE.json` | node test + chạy suite |
| Tầng causal + cỡ chấm do bộ đo tự tính | `compiler-scene-replay-lib.mjs` (`expectedCausalTiers`, `LOP_DONG_THEO_TANG`, `doCoDauDinh`, `DAI_SAC_VAI_TRO`, `phanLoaiSac`, `assessCausalCanvasHues`) + suite (`vertexMarkerCheck`, `assessRoleColors`, `roleHueCensus`) | Tầng kỳ vọng tính độc lập từ cảnh; lớp mỗi dòng BẢNG LỜI GIẢI (theo id) phải khớp tầng; màu vạch trái/ô chú giải tính toán = token `--geo3d-vai-tro-*` đọc từ `tokens.css`; đường kính chấm đo qua ma trận camera; KHUNG 3D ở trạng thái causal: điểm ảnh dải cam/xanh (phân loại bằng sắc độ, hàm thuần tiêm vào trang) chỉ được có khi một vật VẼ ĐƯỢC mang tầng ấy, lớp phủ HTML (`.geo3d-noi`, `.geo3d-soi`, `.geo3d-label`) bị bỏ ra vì viền chữ khử răng cưa điểm ảnh con ra cam/xanh — mã `CAUSAL_CANVAS_ROLE_HUE` | → `BROWSER_EVIDENCE.json`, `PLAYBACK_EVIDENCE.json` | node test |
| Bước dựng + lớp lời giải do bộ đo tự tính (W12) | `compiler-scene-replay-lib.mjs` (`expectedGeometryTimeline`, `expectedSolutionRows`, `assessGeometrySteps`, `assessPlayback`) + suite (`solutionState`, `formationEvidence`, `renderedIds`, `pageClip`, `captureElement`) | Oracle đọc snapshot formation, không import sản phẩm: bước mới chỉ ở sự kiện dựng làm đổi hình; mỗi bước quan sát phải đổi vật dựng lên khung (0 khung tĩnh), dòng "Đang dựng" không phải đại lượng/kết luận, bảng lời giải khớp dữ kiện/bước tính/kết quả của khung neo, tua ngược trả đúng khung, "Bước sau" khoá ở bước cuối; đáp số đúng một dòng ở Kết quả; ảnh cắt theo toạ độ TÀI LIỆU (trang đã cuộn) | → `BROWSER_EVIDENCE.json`, `PLAYBACK_EVIDENCE.json` | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Sheet theo họ | `backend/scripts/build_scene3d_visual_evidence.py` (`family_dir`, `family_sheet`, `page_box`, `overview_index`, `build`) | `images/<họ>/SHEET.png` độ phân giải gốc: 4 trạng thái, bảng lời giải (ảnh phần tử, dùng nguyên), lời từ chối desktop/mobile (W12), rồi mọi BƯỚC DỰNG, nhãn chữ 28 px, dải chú giải màu vai trò W12; `images/overview/INDEX.png` chỉ là mục lục; crop cạnh khuất ở `images/<họ>/hidden-edges/`, chỉ mục ở `results/HIDDEN_EDGE_CROPS.json` | browser + measurement + fixtures → `images/`, `results/` | `pytest tests/geometry/test_scene3d_visual_evidence.py -q` |
| Chữ ký hình bỏ vật không vẽ | `backend/scripts/measure_scene3d_occlusion.py` (`NON_GEOMETRIC_TYPES`, `geometry_signature`) | Vật `quantity` (readout, không vẽ) không phải hình học: thêm AB/AC/SA vào cảnh đã duyệt không được làm `SCENE_GEOMETRY_CHANGED`. Chỉ bỏ kiểu đã biết; kiểu lạ vẫn tính | cảnh → `transfer_expectation` | `pytest tests/geometry/test_human_expected_visibility.py -q` |

### Pedagogical timeline + source grounding — w12 (2026-10-01)

Run `docs/evaluation/geometry/runs/w12-pedagogical-grounding-closure/`. Trả lời review người của w11 (`NEEDS_CHANGES`, W11-H1…H5). Dòng thời gian hình học, bảng lời giải và màu vai trò ở frontend đã có mục riêng (`scene3d-model.ts` `geometryTimeline`/`solutionAt`, `scene3d-solution.tsx`, `scene3d-roles.ts`; bất biến #35/#36 ở `ARCHITECTURE_MAP §5`); bảng dưới là chuỗi grounding nguồn ở backend.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| GIVEN phải có bằng chứng trong ĐỀ | `backend/app/simulation/semantic_program/grounding_gate.py` (`ERR_GIVEN_KHONG_CO_TRONG_DE`, `MA_LOI_NGUON`, `_SO_DE`, `_bang_chung_do_dai`, `_xet_do_dai`, `_bac_nguon`; `_NHAN_TRUOC` đã GỠ ở w14 — nhãn đoạn trước số nay do `segment_relation.nhan_doan_truoc` đọc, xem mục w14 bên dưới) | Độ dài GIVEN (số nguyên, thập phân `.`/`,`, phân số, căn) phải đọc được ngay sau nhãn đoạn trong `problem_text`, cùng đơn vị; nguyên tử chỉ P1 mới có phải có trong đề; điểm ghim vào lời khai toạ độ có chữ số đề không ghi ⇒ từ chối điểm. Ba mã ổn định `GIVEN_VALUE_NOT_IN_SOURCE` / `SOURCE_SPAN_MISMATCH` / `SOURCE_EVIDENCE_CONFLICT`, `reason_subjects` = đoạn hoặc điểm | contract + đề → grounding → envelope | `pytest tests/geometry/test_source_grounding_closure.py -q` |
| P1 tính lại từ chữ của đề | `backend/app/simulation/semantic_program/literal_extractor.py` (`gia_tri_khong_chung_minh_duoc`, `_co_thap_phan_phay`) | MỘT hàm, dùng chung bởi biên đóng băng hợp đồng, cổng grounding và các hàm dựng bất biến: giá trị chỉ analyze khai mà đề không chứng minh được là "chưa chứng minh"; thập phân phẩy kiểu Việt; so chuỗi dưới NFKC (A₁ = A1) | đề → P1 → mọi consumer | `pytest tests/semantic_program/test_literal_provenance.py -q` |
| Đọc độ dài đoạn không cắt cụt | `backend/app/simulation/semantic_program/segment_relation.py` (`_SO`, `_HET_SO`, `do_dai_trong_de`, `bat_bien_chia_doan`, `_chia_doan`) | Đọc phân số/thập phân/căn mà không cắt trước `.chữ số` hay `√`; lời khai chưa chứng minh KHÔNG dựng được bất biến chia đoạn nhưng vẫn phủ quyết được phép chia trái nó (`CHUA_GIAI`) | đề → bất biến nguồn | `pytest tests/geometry/test_segment_relation_coverage.py -q` |
| Không gửi đi sửa | `backend/app/ai/pipeline.py` (`KHONG_SUA_NGUON`) | Mã grounding nguồn dừng tuyến: một lượt sửa không thể bịa ra chữ của đề | route → pipeline | `pytest tests/geometry/test_source_grounding_closure.py -q` |
| Lời từ chối nói đúng loại số liệu | `backend/app/learner_messages.py` (`_KY_HIEU_DIEM`, `_doan_hoc_sinh`) | "độ dài AD" / "toạ độ điểm S" / "một số liệu" từ `reason_subjects`; không lộ mã kỹ thuật | envelope → `UnsupportedNotice` | `pytest tests/test_learner_messages.py -q` |
| Cache served → rejected | `backend/app/main.py` (`CACHE_VERSION = "105"`) + `backend/cache_identity.lock.json` | Envelope `ok` cũ có thể chở GIVEN bịa: 104 → 105 (`d17550c3`); vân tay provider không đổi | cache → `/api/analyze` | `cd backend && .venv/Scripts/python.exe scripts/lock_cache_identity.py --verify` |
| Fixture âm "đề thiếu dữ kiện" | `backend/scripts/generate_generic_tier_a_fixtures.py` (`_ungrounded_cases`, `_ungrounded_fixture`) | Mỗi họ: bỏ một câu chứa dữ kiện khỏi đề, transport giả vẫn trả lời khai cũ ⇒ envelope `unsupported` · `GIVEN_VALUE_NOT_IN_SOURCE` qua đúng tuyến sản phẩm, 0 lượt gọi model | generator → suite (âm) | `pytest tests/geometry/test_generic_tier_a_fixture_generator.py -q` |

⚠️ Hai mục cũ ở trên — `scene3d-tokens.ts` (2026-09-12) và `scene3d-wide-line.ts` (2026-09-11) — mô tả module **đã gỡ khỏi kho** (kiểm 2026-09-29: `ls` không thấy); token chấm đỉnh hiện hành ở `pick-target.ts`, nét vẫn 1 px WebGL.

### Phép dò cách viết độ dài của đề (w13) · offline, 0 lượt gọi

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Phép dò cách viết nguồn | `docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/source_grounding_probe.py` | Chạy CHÍNH các bộ đọc của sản phẩm (`segment_relation.do_dai_trong_de`, `grounding_gate._bang_chung_do_dai`, `literal_extractor.extract_literals`) trên 25 cách viết độ dài; không sửa gì, ghi kết quả vào đường dẫn truyền vào (mặc định `SOURCE_GROUNDING_PHRASING_PROBE.json` cạnh nó) và **từ chối ghi đè** kết quả đã có. Nền đỏ của W14 Track C (`standalone_wrong_segment`: *"AB dài 5 cm"* ⇒ khai `AC = 5` lọt) | đề mẫu → bộ đọc sản phẩm → bảng §4 của `docs/architecture/GENERIC_GEOMETRY_FOUNDATION_PREREGISTRATION.md` | `cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe ../docs/evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/source_grounding_probe.py <new-output.json>` |

### Generic formation + assumption foundation — w14 (2026-10-02)

Run `docs/evaluation/geometry/runs/w14-generic-formation-assumption/`. Trả lời review người của w12 (W12-H1…H4) theo tiền đăng ký w13. Không rẽ nhánh theo họ bài, tiêu đề, đề hay tên đỉnh — khoá bởi AST guard `test_planner_khong_re_nhanh_theo_ho`.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Bảng mặt tổ hợp (lá) | `backend/app/simulation/semantic_program/solid_faces.py` (`phan_loai_bang_mat`) | MỘT thẩm quyền tổ hợp: mọi cách đọc chóp (đỉnh, đáy) / lăng trụ (đáy, đáy trên, cả hai chiều) của một bảng mặt; không import gì từ `app`. `display_names._phan_loai_khoi` lấy cách đọc đầu + tinh chỉnh chính xác (lập phương / hộp / lăng trụ đứng) — hành vi không đổi | bảng mặt `construct_solid` → `formation.lop_khoi`, `display_names._phan_loai_khoi` | `pytest tests/geometry/test_shape_class_formation.py -q -k solid_faces` |
| Bước bổ sung dựng hình theo lớp hình | `backend/app/simulation/semantic_program/formation.py` (`VAI_TRO`, `TOI_THIEU`, `lop_khoi`, `chan_duong_cao`, `ke_hoach`, `hoan_thien_dung_hinh`, `KetQuaHoanThien`, `gan_vai_tro_dung`) | Chèn đáy/đáy trên còn thiếu, đường cao (chỉ từ `perpendicular_line_plane` của hợp đồng hoặc chân `project_onto`) và cạnh bên thành câu lệnh thật TRƯỚC `construct_solid`, cho chương trình compiler LẪN LLM (S4). Thẩm quyền topology: hợp đồng → quan hệ có kiểu → bảng mặt không mơ hồ; `AMBIGUOUS_TOPOLOGY` / `UNSUPPORTED_TOPOLOGY` / `TOPOLOGY_CONTRACT_MISMATCH` / `PARTIAL_LATE_OBJECT` / `COMPLETION_REJECTED_INVALID_OUTPUT` để nguyên khối; `MALFORMED_TOPOLOGY` ⇒ route từ chối. Không đổi bản gốc, tất định, lũy đẳng; đầu ra qua `model_validate` + `kiem_tinh` | spec → `route.verify_and_compile` + `pipeline._dung_scene3d` (cùng đầu vào ⇒ cùng spec, #31); `gan_vai_tro_dung` ← `simulation_state.build_simulation_state` | `pytest tests/geometry/test_shape_class_formation.py tests/geometry/test_formation_plan_parity.py -q` |
| Từ chối bảng mặt hỏng | `backend/app/simulation/semantic_program/route.py` (`verify_and_compile`: chặng `formation`, `SOLID_TOPOLOGY_MALFORMED`; `SemanticRouteOutcome.program_sha256_original`, `program_sha256_completed`, `formation_statuses`, `source_check`) | Chỉ số ngoài miền / tên lạ / mặt < 3 đỉnh / đỉnh lặp ⇒ từ chối có cấu trúc, không 500 | route → envelope | `pytest tests/geometry/test_shape_class_formation.py -q -k bang_mat_hong` |
| Vai trò dựng hình trong cảnh | `backend/app/simulation/semantic_program/scene3d.py` (`_TRUONG` + `shape_class`, `formation_requirements`; `formation_roles` trên vật và trên bước của `_build_formation`) | `scene3d` chỉ CHỞ vai trò producer gán; hợp theo bước + ba vai trò theo sự kiện (`DECLARE_ENTITIES`, `CONSTRUCT_INTERSECTION`, `CLOSE_SECTION`); bước MEASUREMENT / FINAL_RESULT mang `[]`. Từ vựng khoá đồng bộ với `formation.VAI_TRO` (kể cả harness và builder) | scene → frontend, harness | `pytest tests/geometry/test_shape_class_formation.py -q -k vai_tro` |
| Chính sách nguồn đề | `backend/app/simulation/semantic_program/grounding_gate.py` (`NguonDe`, `ERR_THIEU_DE`, `check_grounding(..., nguon=)`) + `route.verify_and_compile(..., nguon=)` + `backend/app/ai/pipeline.py` (`KHONG_SUA_NGUON`) + `backend/app/learner_messages.py` | `problem_text` rỗng ⇒ `SOURCE_TEXT_MISSING` (không gửi đi sửa) trừ khi nơi gọi truyền TƯỜNG MINH `NguonDe.FIXTURE_TIN_CAY` (ghi `source_check = UNCHECKED_TRUSTED_FIXTURE`); không đọc từ HTTP, mô hình hay cấu hình | route → envelope; test cô lập → `backend/tests/nguon_fixture.py` | `pytest tests/geometry/test_assumption_gate.py -q -k "fixture_tin_cay or thieu_de or bypass or NguonDe"` |
| Một từ vựng nối độ dài | `backend/app/simulation/semantic_program/segment_relation.py` (`_NOI_DO_DAI`, `_NHAN_TRUOC_SO`, `nhan_doan_truoc`) + `grounding_gate.py` (`_bang_chung`, `bang_chung_doan`) | `=` / `bằng` / `dài` / `có độ dài` cho bộ đọc độ dài và nhãn bằng chứng GIVEN; giá trị phải đứng NGAY sau từ nối (không so khớp mờ). `bang_chung_doan(de, (X, Y), v)` gắn bằng chứng vào ĐÚNG đoạn. Đã gỡ `_DO_DAI_CO` và `_NHAN_TRUOC` (mục w12 ở trên còn nhắc tên cũ) | đề → `do_dai_trong_de`, `_bang_chung_do_dai` | `pytest tests/geometry/test_source_length_reader.py -q` |
| Compiler thôi tự viết dựng hình | `backend/app/simulation/geometry_compiler/compiler.py` (`_bien_dich_rectangular_pyramid`, `_bien_dich_cuboid` chỉ giữ đa giác đáy cho phép đo diện tích; lời kể đỉnh chóp không còn nói "đường cao") · `primitives.py` (gỡ `construct_segment`, `construct_segments_group`) | Đường cao, cạnh bên, đáy trên do bước bổ sung chung sinh | compiler → route | `pytest tests/geometry/test_formation_plan_parity.py -q` |
| Phủ vai trò ba chiều (harness) | `frontend/scripts/compiler-scene-replay-lib.mjs` (`renderedSets`, `assessFormation`, `assessStructuredReferences`; gate `FORMATION_ROLE_COVERAGE`, `STRUCTURED_REFERENCE_NOT_RENDERED`) + `compiler-scene-suite.mjs` (`formationEvidence`) + `generic-tier-a-scenarios.json` (`expected_formation`, `formation_coverage`) | Kỳ vọng ĐỘC LẬP (viết tay từ hợp đồng/gold) ↔ yêu cầu sản phẩm khai ↔ quan sát renderer (lần xuất hiện đầu, theo tập đỉnh); mọi tham chiếu có cấu trúc của bước phải được vẽ hoặc hiện | fixture → trình duyệt → `BROWSER_EVIDENCE.json` | `node --test frontend/scripts/*.node-test.mjs` |
| Filmstrip theo vai trò | `backend/scripts/build_scene3d_visual_evidence.py` (`TEN_VAI_TRO`, `chu_thich_buoc`, `filmstrip`) | `images/<họ>/FILMSTRIP.png`: các bước dựng trái → phải, chú thích tên vai trò tiếng Việt + lời kể; vai trò không có tên ⇒ lỗi, không in token | evidence → người duyệt | `pytest tests/geometry/test_scene3d_visual_evidence.py -q` |
| Chẩn đoán w14 (run) | `docs/evaluation/geometry/runs/w14-generic-formation-assumption/diagnostics/` (`s4_inventory.py`, `assumption_census.py`, `assumption_corpus/build_corpus.py`, `proof_cache_row_w14.py`, `trust_policy_callers.py`, `scene_hash_reconciliation.py`, `section_substeps_compare.py`, `occlusion_transfer_diagnostic.py`, `build_manifest.py`) | Kiểm kê S4, census cổng giả định trên corpus gắn nhãn trước, bằng chứng cache bằng row thật, phân loại nơi gọi chính sách nguồn, so bước thiết diện, phần còn lại của phép chuyển kỳ vọng khuất/hiện, MANIFEST — 0 lượt gọi. Kiểm kê, census, corpus, bằng chứng cache, phân loại nơi gọi và đối soát băm cảnh từ chối ghi đè kết quả đã có; `section_substeps_compare.py`, `occlusion_transfer_diagnostic.py`, `build_manifest.py` ghi lại đầu ra dẫn xuất tất định | → `diagnostics/*.json` | chạy script (lệnh ở docstring) |

### Source-constraint & assumption closure — w15 (2026-10-03)

Run `docs/evaluation/geometry/runs/w15-assumption-closure/`. Thẩm quyền đăng ký (viết TRƯỚC mã): `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md`. Quyết định người dùng U1–U5: `inputs/W15_SCOPE_DECISIONS.json` của run.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Bộ đọc ràng buộc từ đề | `backend/app/simulation/semantic_program/shape_constraint.py` (`RangBuoc`, `doc_rang_buoc`, `neu_khoi_da_dien`, `phan_chua_doc`, `_TAI`, `_TU_NOI`, `_TU_BI_BO`) | Đọc CÂU ĐỀ theo từ vựng ĐÓNG (vuông góc đường–mặt / đường–đường / `góc … = 90°`, ký hiệu chóp/lăng trụ, kiểu khối/đáy, tam giác/đáy vuông tại–ở–ở đỉnh–đỉnh X, một lăng trụ đứng không tên) → `RangBuoc` do server sở hữu, gắn đúng thực thể. Chỉ XÁC NHẬN: không vào fact graph, không nâng fact mô hình thành GIVEN. `neu_khoi_da_dien` = vị từ phạm vi U3; `phan_chua_doc` = phần dữ kiện chưa bộ đọc nào đọc trọn (span + câu độ dài số `segment_relation.MAU_DO_DAI`) | đề → `assumption_gate`, `route` | `pytest tests/geometry/test_shape_constraint.py -q` |
| Chứng chỉ giả định | `backend/app/simulation/semantic_program/assumption_gate.py` (`kiem_gia_dinh`, `danh_gia_doc_lap`, `KetQuaGiaDinh`, `PROVEN_SAFE`/`DEPENDENT`/`UNDETERMINED`/`NOT_APPLICABLE`, `MA_PHU_THUOC`, `MA_CHUA_CHUNG_MINH`, `MA_NHIEU_DINH_NGHIA`, `NGAN_SACH_CHAY_LAI`, `TOAN_HANG`, `KHUNG_TU_DO`, `kieu_ir_chua_phu`, `bat_bien_tu_de`) | Mọi giá trị SỐ người học thấy (bước `MEASUREMENT` + witness nghĩa vụ): lát cắt theo định nghĩa với tới DUY NHẤT trên trace (U5: literal khai báo bị CHÍNH lệnh dựng ghi đè mà không câu lệnh nào tới và gồm lệnh ấy đọc thì không với tới); C0 = mọi literal là `SOURCE_DATUM` cùng thực thể (khoá ký hiệu `domain_profile.geometry_symbol_key`); C1 = khuôn T1–T6 trên ràng buộc đọc được + đối chiếu chạy lại hiện thực chính tắc (thể tích/diện tích/khoảng cách); phản ví dụ chỉ khi đề đọc trọn. `kieu_ir_chua_phu()` tự kiểm bảng toán hạng phủ đủ `contract.py` | trace + hợp đồng + đề → route, census | `pytest tests/geometry/test_assumption_certificate.py tests/geometry/test_assumption_gate.py -q` |
| Chặng `assumption` của route | `backend/app/simulation/semantic_program/route.py` (`_sau_grounding`: `ghi_gd`; `SemanticRouteOutcome.assumption_status`, `assumption_certificate`, `assumption_enforced`) + `backend/app/ai/pipeline.py` (`KHONG_SUA_NGUON` += hai mã) + `backend/app/learner_messages.py` (`_MSG_GIA_DINH_QUYET_DINH`, `_MSG_GIA_DINH_CHUA_CHUNG_MINH`) + `frontend/src/components/SimulationWorkspace.tsx` (`NHAN_GIAI_DOAN.assumption`) | Sau hậu điều kiện, trước biên dịch: chỉ phục vụ `PROVEN_SAFE`/`NOT_APPLICABLE` khi `assumption_enforced` (U3: đề nêu khối đa diện theo từ vựng; U5: nhiều định nghĩa ⇒ mọi vùng). Từ chối `INPUT_NOT_GROUNDED` + `ASSUMPTION_DETERMINES_ANSWER` (nêu đại lượng) / `ASSUMPTION_INVARIANCE_UNPROVEN`; không gửi đi sửa; lỗi bộ đọc ⇒ đóng an toàn | route → envelope → UI | `pytest tests/geometry/test_assumption_gate.py -q` |
| Một mẫu câu độ dài số | `backend/app/simulation/semantic_program/segment_relation.py` (`MAU_DO_DAI`) | Mẫu dùng chung cho `_moi_doan_co_do_dai` và `shape_constraint.phan_chua_doc` (không chép) | đề → hai người đọc | `pytest tests/geometry/test_segment_relation_consistency.py -q` |
| Bảng mặt: tương ứng song ánh | `backend/app/simulation/semantic_program/solid_faces.py` (`phan_loai_bang_mat`) | Cặp nắp có tương ứng KHÔNG song ánh không cho cách đọc lăng trụ nào (trước đây giữ một hướng lặp đỉnh) | bảng mặt → `formation.lop_khoi`, `display_names` | `pytest tests/geometry/test_shape_class_formation.py -q -k solid_faces` |
| Phần tô thiết diện khép kín | `frontend/src/simulations/domains/geometry/scene3d-view.tsx` (`DO_DUC_TO_THIET_DIEN`, `vatThietDienTaiBuoc`, `datHienToThietDien`, `THU_TU_VE_THIET_DIEN`, `THU_TU_TO_THIET_DIEN`; vật `section_fill:<id>`; móc đo `window.__geo3d_set_section_fill_visible`) | Vật tô riêng: độ đục 0.45, vẽ sau MẶT và TRƯỚC NÉT (W16: thứ tự `THU_TU_TO_THIET_DIEN = 7`, cạnh khối chuẩn trong suốt ở 8 vẽ đè lên; W15 ở 10 phủ hổ phách lên cạnh), KHÔNG kiểm và KHÔNG ghi chiều sâu (thiết diện nằm trong khối, sau lớp chiều sâu đục của khối), không là vật che; chỉ có từ bước khép-và-tô theo `geometry_progress`; viền giữ hai lượt thấy/khuất. Móc đo chỉ cho harness | scene → renderer → cổng `SECTION_FILL_DISTINGUISHABLE`, `SECTION_FILL_UNDER_EDGES` | `npx vitest run src/simulations/domains/geometry/scene3d-section.test.ts` |
| Cổng ảnh phần tô (harness) | `frontend/scripts/compiler-scene-replay-lib.mjs` (`NGUONG_TO_THIET_DIEN`, `deltaE76`, `assessSectionFill`, `diemMauThietDien`, `KIEU_TU_CHOI`) + `compiler-scene-suite.mjs` (`giaiMaHaiKhung`, `sectionFillPairs`, `sectionFillEvidence`, `runNegative({expected})`) + `generic-tier-a-scenarios.json` (`negative_fixtures`: ba loại mỗi họ) | Bật/tắt phần tô ở CÙNG khung, mẫu bên trong đa giác chiếu bằng camera thật, cách MỌI cạnh khối và dấu điểm đã chiếu ≥ `margin_px` (W16: bản W15 chỉ chừa lề quanh cạnh của chính đa giác); ngưỡng đăng ký trước (`T_ON 20 · T_ON_MIN 12 · T_OFF 3 · margin 3 px`, khoá bằng node test với văn bản amendment §11); ba loại từ chối mỗi họ, mỗi loại mã riêng | fixture → trình duyệt → `BROWSER_EVIDENCE.json` | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Fixture âm giả định | `backend/scripts/generate_generic_tier_a_fixtures.py` (`_fake_analyze_refusal`, `_BO_KICH_THUOC`, `_assumption_cases`) | Mỗi họ một fixture `_assumption`: đề mất một kích thước, chương trình giữ nó bằng bố cục ⇒ route từ chối ở `assumption` với mã riêng, 0 lượt gọi model | generator → `inputs/fixtures/*_assumption.json` | `pytest tests/geometry/test_generic_tier_a_fixture_generator.py -q` |
| Phán quyết U2 của bộ đo occlusion | `backend/scripts/measure_scene3d_occlusion.py` (`reviewed_sets_transfer`, `--pending-human-review`, `report["human_review_pending"]`, `report["verdict"]`) | Cảnh người đã duyệt trên hình CŨ: `HUMAN_REVIEW_PENDING` (không tính lỗi) CHỈ khi oracle tái hiện tập đã duyệt ở camera đăng ký lẫn camera mới và sản phẩm = oracle; khác đi là lỗi. Mặc định (không cờ) giữ nguyên nghiêm ngặt | browser evidence → `OCCLUSION_MEASUREMENT.json` | `pytest tests/geometry/test_human_expected_visibility.py -q` |
| Chẩn đoán w15 (run) | `docs/evaluation/geometry/runs/w15-assumption-closure/diagnostics/` (`track_b_table.py`, `gold_row_verification.py`, `assumption_corpus_w15/build_corpus.py`, `assumption_corpus_w15b/build_corpus.py`, `assumption_census_w15.py`, `assumption_census_w15_r2.py [round]`, `fault_injection_w15.py`, `run_fault_injections_w15.py`, `proof_cache_row_w15.py`, `w15_gates.sh`, `build_manifest.py`) | Bảng nguyên nhân gốc Track B, kiểm hàng gold bằng oracle độc lập, corpus gắn nhãn trước, census ba vòng theo luật SHIP §9, tiêm lỗi FI1–FI14 (thay nguồn trong bộ nhớ, hỏng neo ⇒ dừng), bằng chứng cache bằng row thật, cổng danh tính, MANIFEST — 0 lượt gọi; census, corpus, tiêm lỗi và bằng chứng cache từ chối ghi đè kết quả đã có | → `diagnostics/*.json`, `diagnostics/logs/*.log` | chạy script (lệnh ở docstring) |

### Pre-merge soundness & visual evidence — w16 (2026-10-03)

Run `docs/evaluation/geometry/runs/w16-premerge-closure/`. Thẩm quyền đăng ký (viết TRƯỚC bản sửa): `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §14.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Tên mặt phẳng đề cho | `backend/app/simulation/semantic_program/plane_equation.py` (`MatPhangDe`, `doc_mat_phang_de`, `ten_mat_phang_cua_bien`, `so_lan_nhac_mat_phang`, `_ung_vien_span`, `_TEN_TRUOC`, `_HY_LAP`, `_phay`) | Mỗi phương trình mặt phẳng ĐỌC TRỌN của đề kèm tên viết trong mệnh đề (`(α): …`, `(P) có phương trình …`, không tên ⇒ None) và span; tên biến IR → các tên mặt phẳng nó có thể mang (chữ Hy Lạp, bảng phiên âm ĐÓNG, một chữ hoa; dấu phẩy trên viết ra, hoặc token `_prime`/`_phay` theo sau, là một phần của tên — `mp_P_prime` mang (P′), không mang (P); `′`/`’` chuẩn hoá thành `'` ở cả hai phía); số lần đề nhắc mặt phẳng. `SourceInvariant plane_equation` (hậu điều kiện tồn tại) KHÔNG đổi | đề → `assumption_gate` | `pytest tests/geometry/test_plane_from_equation.py -q -k w16` |
| Gắn mặt phẳng trong C0 | `backend/app/simulation/semantic_program/assumption_gate.py` (`gan_mat_phang`, `_vai_tro(..., mp)`; detail `PLANE_BINDING`) | Literal `construct_plane_from_equation` là `SOURCE_DATUM` chỉ cho ĐÚNG mặt phẳng đề mà biến gắn được (theo tên, hoặc duy nhất theo đếm: đề nhắc mặt phẳng một lần và chương trình dựng một mặt phẳng từ phương trình) với hệ số tỉ lệ; trùng bộ số không bao giờ là căn cứ (§14.1) | trace + đề → route, census | `pytest tests/geometry/test_assumption_certificate.py -q -k w16` |
| Mệnh đề mục tiêu | `backend/app/simulation/semantic_program/shape_constraint.py` (`khoang_muc_tieu`, `che_muc_tieu`, `_nfc_theo_cum`, `_MUC_TIEU`, `_HET_MENH_DE`, `_TRUOC_CAU_HOI`) + `assumption_gate.kiem_gia_dinh` (tiền đề đọc từ `che_muc_tieu(đề)`; `GOAL_CLAUSE`, `CE_GOAL_CLAUSE_PRESENT`) | Span yêu cầu chứng minh/kiểm tra/câu hỏi (`chứng minh`, `chứng tỏ`, `CMR`, `kiểm tra`, `hỏi`; câu kết `?`), khớp trên bản NFC theo cụm (đề NFD vẫn khớp), che giữ độ dài; mọi tiền đề của chứng chỉ đọc từ đề đã che, ràng buộc trong mục tiêu vẫn chặn phản ví dụ (§14.2) | đề → `assumption_gate` | `pytest tests/geometry/test_shape_constraint.py -q -k w16` |
| Cổng ảnh tô dưới cạnh (harness) | `frontend/scripts/compiler-scene-replay-lib.mjs` (`diemMauThietDien(dinh, snapshot, {canh, cham})`, `diemCanhQuaThietDien`, `assessSectionFillUnderEdges`, `_vungThietDien`) + `compiler-scene-suite.mjs` (`sectionFillPairs(..., scene, {duoiCanh})`, `closed.under_edges`; `runNegative` ghi `refusal_message_box`) | `SECTION_FILL_UNDER_EDGES` (§14.4): mỗi cạnh khối qua vùng thiết diện, lõi = điểm ảnh tối nhất lúc tắt trong dải ±1 px CSS, tham chiếu ±4 px; đạt ⇔ ρ < 1 và tương phản cạnh ≥ `T_ON_MIN`; không cạnh nào ⇒ không áp dụng (không phải đạt) | fixture → trình duyệt → `BROWSER_EVIDENCE.json` | `node --test frontend/scripts/compiler-scene-replay-lib.node-test.mjs` |
| Ô từ chối của sheet | `backend/scripts/build_scene3d_visual_evidence.py` (`TEN_TU_CHOI`, `TEN_TU_CHOI_W17`, `TEN_PHUC_VU`, `W17_STATES`, `ThieuAnhBangChung`, `_loi_tu_choi`, `MUC_TOI_THIEU`, `DO_SANG_MUC`) | Ô âm duyệt `negative[kind][viewport]` của bộ chạy (ba loại W15 bắt buộc × hai viewport; W17: `construction_mismatch`/`system_cause` có ô khi họ khai nó; chú thích tiếng Việt theo loại, loại lạ ⇒ `KeyError`); ảnh đúng `<họ>/negative/<loại>/<viewport>/refusal.png`, bản ghi đạt không canvas có lời, hộp lời có mực ≥ 0,5 %; W17: ô `served[kind][viewport]` (bảng đóng `TEN_PHUC_VU`) và ô tắt nhãn / khôi phục nhân quả khi bản ghi dương có `annotation_toggle` / `causal_restore`; thiếu hoặc không đọc được bất kỳ ô nào ⇒ `ThieuAnhBangChung`, không ô trắng (§14.5) | browser evidence → `SHEET.png`, `FILMSTRIP.png` | `pytest tests/geometry/test_scene3d_visual_evidence.py -q` |
| Chẩn đoán w16 (run) | `docs/evaluation/geometry/runs/w16-premerge-closure/diagnostics/` (`probe_w16_phase1.py`, `assumption_corpus_w16/build_corpus.py`, `assumption_census_w16.py`, `fault_injection_w16.py`, `run_fault_injections_w16.py`, `run_fault_injections_w16_frontend.mjs`, `proof_cache_row_w16.py`, `w16_gates.sh`, `build_manifest.py`) | Tái hiện Phase 1 (cả ca không khai thác được), corpus đối kháng gắn nhãn trước bản sửa, census W16 (luật SHIP §9 trên W14/W15/W15B + nhãn W16 + so vòng 3 W15), tiêm lỗi backend (thay nguồn trong bộ nhớ) và frontend (worktree tách rời, khôi phục nguyên byte), bằng chứng cache bằng row, cổng danh tính, MANIFEST — 0 lượt gọi; từ chối ghi đè kết quả đã có | → `diagnostics/*.json`, `diagnostics/logs/*.log` | chạy script (lệnh ở docstring) |

### Operation binding & on-scene quantities — w17 (2026-10-03)

Run `docs/evaluation/geometry/runs/w17-operation-annotations/`. Thẩm quyền đăng ký (viết TRƯỚC bản sửa): `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §15.

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Câu cắt của đề | `backend/app/simulation/semantic_program/shape_constraint.py` (`QuanHeCat`, `doc_quan_he_cat`, `_CAU_CAT`, `_mp`, `_khoi`, `_td`, `_TAN_NGU_VOI`) | Từ vựng ĐÓNG §15.1 (+ đính chính Task 2): `(X)`/`Mặt phẳng <pt>`/`Mặt phẳng (đi) qua A, B và C` `cắt <khối> theo thiết diện (T)`, bị động `thiết diện (T) của <khối> cắt bởi (X)` và `cắt <khối> bởi (X) (ta) được thiết diện (T)`; đọc trên đề đã che mục tiêu; mặt phẳng đứng ngay sau `với` ("song song/vuông góc với (X)") là tân ngữ, không phải mặt phẳng cắt (tự rà soát cuối); ngoài từ vựng ⇒ không phát | đề → `assumption_gate` | `pytest tests/geometry/test_shape_constraint.py -q -k w17` |
| Kiểm phép dựng (§15.1) | `backend/app/simulation/semantic_program/assumption_gate.py` (`MA_LECH_PHEP_DUNG`, `danh_tinh_mat_phang`, `_kiem_phep_dung`, `_gan_quan_he`, `_mp_cua_cau_cat`, `_mp_cua_chuong_trinh`; detail `OPERATION_BINDING`) | Danh tính mặt phẳng: theo NGUỒN (`source_fact_id` của khai báo → giá trị nguyên văn duy nhất trong đề → đúng một phương trình) rồi luật W16; tên biến ≠ nguồn ⇒ không danh tính; mặt phẳng gọi bằng điểm ⇒ tập điểm. ĐIỀU KIỆN THÊM cho C0/C1: mọi `construct_section` trên lát cắt gắn một câu cắt (một-một · nguồn · tên), cùng danh tính mặt phẳng, cùng tập đỉnh khối; lệch (CẢ HAI danh tính xác định và khác nhau) ⇒ `UNDETERMINED` + `CONSTRUCTION_NOT_TEXT_BOUND`; danh tính không ghim được (mặt phẳng tên không phương trình, khối/thiết diện không ghim) hoặc không đọc được câu cắt ⇒ `ASSUMPTION_INVARIANCE_UNPROVEN` | trace + đề → route (`assumption`), census | `pytest tests/geometry/test_assumption_certificate.py -q -k w17` |
| Grounding không lấy mục tiêu (§15.2) | `backend/app/simulation/semantic_program/grounding_gate.py` (`check_grounding` → `_kiem_grounding(contract, spec, de)`, `ERR_CHI_TRONG_MUC_TIEU`) + `shape_constraint._HET_MENH_DE` (`, biết` kết thúc mục tiêu) + `_MO_BIET` (`…, biết Y?`: Y là giả thiết, câu hỏi là mệnh đề trước) | Bằng chứng GIVEN đọc trên `che_muc_tieu(đề)`; từ chối mã nguồn đổi thành `GIVEN_ONLY_IN_GOAL_CLAUSE` chỉ khi cùng thân chạy trên đề gốc qua được (phân loại, không cấp phép); `GIVEN_ONLY_IN_GOAL_CLAUSE` ∈ `MA_LOI_NGUON` ⊆ `pipeline.KHONG_SUA_NGUON` | hợp đồng + chương trình → route (`grounding`) | `pytest tests/geometry/test_source_grounding_closure.py -q -k w17` |
| Nguyên nhân từ chối (§15.3) | `backend/app/simulation/semantic_program/refusal_cause.py` (`NGUYEN_NHAN_THEO_MA`, `theo_ma`, `do_dai_khong_duong`, `mat_phang_khong_cat`) + `route._hong` (gắn `refusal_cause` theo bảng) + `route` nhánh `execution` (kernel `PLANE_DOES_NOT_CUT`; `geometry_exec.exec_construct_section` gắn `e.mat_phang`) + `pipeline` nhánh compiler `REFUSE` + `pipeline._that_bai_hinh_hoc` (`env.refusal_cause`) + `learner_messages.attach_learner_reason` (mặc định `UNKNOWN`) | `SOURCE`/`CONSTRUCTION`/`UNKNOWN` chỉ từ mã có cấu trúc + bộ đọc đề của server: `NON_POSITIVE_LENGTH` là `SOURCE` khi đề ghi đúng độ dài ≤ 0 cho đúng đoạn (hoặc cạnh lập phương), `PLANE_DOES_NOT_CUT` là `SOURCE` khi mặt phẳng cắt tỉ lệ một phương trình đề cho; còn lại `CONSTRUCTION`; mã ngoài bảng ⇒ `UNKNOWN` | route/pipeline → envelope → `learner_messages`, `UnsupportedNotice` | `pytest tests/geometry/test_refusal_cause.py -q` |
| Lời từ chối theo nguyên nhân | `backend/app/learner_messages.py` (`_MSG_THEO_NGUYEN_NHAN`, `_MSG_CHI_TRONG_MUC_TIEU`, `_DUOI_LOI_HE`, `_msg_lech_phep_dung`; `_MSG_GEOMETRY_GENERATION_FAILED` = lời `UNKNOWN`) + `frontend/src/components/SimulationWorkspace.tsx` (`UnsupportedNotice` đọc `refusal_cause`) + `frontend/src/core/types.ts` (`AnalysisUnsupported.refusal_cause`) | Chỉ `SOURCE` mời sửa dữ kiện trong đề; `CONSTRUCTION` nói đề hợp lệ, lỗi ở hệ; `UNKNOWN` (và envelope cũ) không mời viết lại đề. Lời backend của `SOURCE`/`CONSTRUCTION` đã mang việc nên làm ⇒ thẻ KHÔNG có câu gợi ý nhắc lại (T7); `CONSTRUCTION` ở cổng nguồn (`input_not_grounded`) ⇒ loại vấn đề "hệ dựng lệch với đề bài" | envelope → học sinh | `pytest tests/test_learner_messages.py -q -k w17` · `npx vitest run src/components/refusal-contract.test.tsx` |
| Fixture âm theo nguyên nhân | `backend/scripts/generate_generic_tier_a_fixtures.py` (`_ab_bang_0`, `_zero_ab`, `_tiem_ab_bang_0`; fixture `cube_system_cause.json`) | `_zero_ab` GHI số 0 vào chính đề (lập phương "cạnh bằng 0") ⇒ `SOURCE`; `_tiem_ab_bang_0` giữ đề hợp lệ, chỉ hợp đồng mang AB = 0 ⇒ `CONSTRUCTION` (ảnh lập phương W16) | bộ sinh → bộ duyệt trình duyệt | `pytest tests/geometry/test_generic_tier_a_fixture_generator.py -q` |
| Đối soát fixture âm (run) | `docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/reconcile_negative_fixtures.py` | Sinh lại mọi fixture âm bằng bộ sinh sản phẩm (0 lượt gọi) + hàng A′ + ảnh W16 bất biến → loại (thiếu dữ kiện · dữ kiện suy biến/mâu thuẫn · lệch phép dựng · bộ chạy tiêm sai · lỗi hệ chưa rõ), nguyên nhân phải có vs thực tế; không ghi đè | bộ sinh → `NEGATIVE_FIXTURE_RECONCILIATION_<sha>.json` | chạy từ `backend/` với `--tmp <thư mục tạm>` |
| Tên hành động ≠ xuất xứ (Phase 3) | `backend/app/simulation/semantic_program/scene3d.py` (`build_scene_events`: `display_label` = nhãn vật, rồi nhãn CỦA CÂU LỆNH NHÓM `details.label` không mang `_`) + `frontend/src/simulations/domains/geometry/scene3d-model.ts` (`geometryActionLabelAt`) + `scene3d-playback.tsx` ("Đang dựng" ĐÃ GỠ ở regular-square-pyramid-w01 → nhãn bước của panel «Các bước dựng», `geometryStepList`) | Bước nhóm ("Các cạnh bên AD, BE, CF") nói tên hành động; "— (dữ kiện đề cho)" chỉ còn ở INIT. Kiểm xuất xứ: điểm `LAYOUT_DERIVED` mang nhóm hiển thị nội bộ `given` (bung/cô lập, không hiện chữ) — không bề mặt học sinh nào gọi nó là đề cho; lời kể cạnh thiết diện khớp mặt `mat` của payload | `build_scene_events` → player | `pytest tests/geometry/test_shape_class_formation.py -q -k w17` · `npx vitest run src/simulations/domains/geometry/scene3d-playback.test.tsx` |
| Số đo trên hình (backend) | `backend/app/simulation/semantic_program/quantity_annotations.py` (`gan_so_do`, `_DO`, `_do_dai_de_cho`) + `simulation_state.build_simulation_state` (`annotations`, `annotation_diagnostics`) + `scene3d._gan_so_do` (`category`) + `scene3d.build_scene3d` (`diagnostics` ở gốc cảnh) | §15.4: đại lượng đo ↦ toán hạng IR của `measure` (diện tích → đa giác/thiết diện `region`; thể tích → khối đa diện `solid`; khoảng cách có toán hạng ĐIỂM → `pair`, hai điểm ⇒ `segment`; góc chưa có điểm neo); độ dài đề cho ↦ đoạn đề gọi tên ngay trước span bằng chứng GIVEN (`grounding_gate._bang_chung_do_dai`) VÀ khoảng cách chính xác trong bộ nhớ cuối; một chủ thể một nhãn (dữ kiện trước); bí danh-đích không có nhãn thứ hai; vật cong không gắn; còn lại `ANNOTATION_UNBOUND <id>: <lý do>` | spec + bộ nhớ cuối + đề → state → cảnh | `pytest tests/geometry/test_scene3d_annotations.py -q` |
| Số đo trên hình (frontend) | `frontend/src/simulations/domains/geometry/scene3d-annotations.ts` (`annotationsAt`, `annotationAnchor`, `placeAnnotationLabels`, `NEO_TOI_DA`; ⚠️ **ĐÃ GỠ ở W18**: `hasAnnotationCategory`, `DEFAULT_ANNOTATION_TOGGLES` — thay bằng `AnnotationView`/`DEFAULT_ANNOTATION_VIEW`, xem mục w18) + `scene3d-view.tsx` (lớp `geo3d-so-do-lop`, `vungCheKhung`, móc `__geo3d_annotation_boxes`/`__geo3d_point_label_boxes`) + `Scene3DExplorer.tsx` (`data-che-khung` trên nút nổi/ô soi/ngăn kéo; công tắc "Số đo"/"Kết quả" ĐÃ GỠ ở W18 → một công tắc "Hiện tất cả") + `scene3d-playback.tsx` (chuyển tiếp `annotationToggles` → W18 `annotationView`) + `components/icons.tsx` (`IconRuler`; `IconFlag` còn export nhưng không còn nơi dùng từ W18) + `styles/global.css` (`.geo3d-so-do*`) | Hàm THUẦN: nhãn nào hiện ở bước (luật lớp lời giải: đáp số từ sự kiện kết luận, số đo từ sự kiện tính, dữ kiện khi có mặt; chủ thể phải hiện), neo = trung bình toạ độ backend phát (đoạn → trung điểm, miền/khối → trung bình đỉnh, cặp → điểm của cặp; KHÔNG chân đường vuông góc — 5D), đặt hộp theo vòng khe 6/12/18 px — trên/dưới/phải/trái rồi bốn góc — trong khung, ≤ 24 px tới neo, tránh nhãn điểm + lớp phủ, ưu tiên (kết quả, liên quan vật chọn) đặt trước, hết chỗ thì ẩn. Công tắc vắng khi cảnh không có nhãn loại ấy (§3.2); bật/tắt chỉ đổi danh sách nhãn | `annotation` của cảnh → DOM | `npx vitest run src/simulations/domains/geometry/scene3d-annotations.test.ts src/simulations/domains/geometry/Scene3DExplorer.test.tsx` |
| Kiểm trình duyệt W17 (§15.5) | `frontend/scripts/compiler-scene-replay-lib.mjs` (`NHIEU_KHUNG_TOI_DA` (dung sai nhiễu chụp của khôi phục nhân quả, 1/kênh 8-bit, đăng ký §15.5 sau lượt đo `83f101e4`; `assessCausalRestore({…, canvasDelta})`), `expectedAnnotationIds`, `annotationWorldAnchor`, `assessAnnotationBoxes`, `assessToggleIsolation` (⚠️ ĐÃ GỠ ở W18 → `assessShowAllIsolation`), `assessCausalRestore`, `KIEU_TU_CHOI_W17`, `LOP_PHU_KHUNG` — lớp phủ DOM che khỏi phép đo điểm ảnh của hình: sắc vai trò và mẫu tô thiết diện; camera "đổi" = `cameraMotion` vượt `CAMERA_SETTLE_TOLERANCE`) + `compiler-scene-suite.mjs` (`kenhLech` + `saved_frames` — khác byte ⇒ đo lệch kênh trong trang và lưu hai khung, `annotationState`, `anchorNow`, `runServed`, `BAO_SUA_DE`, `khungOnDinh` — khung canvas lúc nghỉ cho khôi phục nhân quả; dương: `annotations_final`/`_rotated`/`_resized`, `annotation_toggle`, `causal_restore`; mỗi bước dựng tiến/lùi: id nhãn trong DOM = oracle; âm: `refusal_cause` + không bảo sửa đề khi nguyên nhân khác SOURCE) + `browser-runner.mjs` (`setViewport`) + `generic-tier-a-scenarios.json` (kiểu từ chối W17 `system_cause`/`construction_mismatch`, `served_fixtures`) + `backend/scripts/generate_generic_tier_a_fixtures.py` (`cross_section_wrong_plane`/`_correct_plane`) | Oracle ĐỘC LẬP (không nhập `scene3d-annotations.ts`): khả dụng theo luật đã đăng ký, điểm neo chiếu bằng ma trận camera thật từ toạ độ payload; hộp trong khung, ≤ 24 px, không đè nhãn điểm/nhau; công tắc chỉ đổi nhãn; khôi phục nhân quả cùng camera + cùng cuộn (ghi riêng ba thứ); lệch phép dựng từ chối với `CONSTRUCTION`, mặt phẳng đúng phục vụ 16 | fixture → trình duyệt (`dist/`) → `BROWSER_EVIDENCE.json` | `node --test scripts/compiler-scene-replay-lib.node-test.mjs` |
| Số đo trên hình (frontend, test) | `frontend/src/simulations/domains/geometry/scene3d-annotations.test.ts` | Khoá hợp đồng §15.4 phía trình bày: chỉ đại lượng có `annotation` của backend mới có nhãn (không suy từ tên biến), chữ = ký hiệu = giá trị payload, công tắc Số đo/Kết quả (bật mặc định, U-W17-1), không lộ trước khi khả dụng (tiến/lùi), chọn chủ thể thì ưu tiên nhãn liên quan, điểm neo theo chủ thể | scene → nhãn | `npx vitest run src/simulations/domains/geometry/scene3d-annotations.test.ts` |
| Chẩn đoán w17 (run) | `docs/evaluation/geometry/runs/w17-operation-annotations/diagnostics/` (`reproduce_operation_binding.py`, `reconcile_negative_fixtures.py`, `assumption_corpus_w17/build_corpus.py`, `assumption_corpus_w17c/build_corpus.py`, `assumption_census_w17.py [round]`, `fault_injection_w17.py`, `run_fault_injections_w17.py`, `run_fault_injections_w17_frontend.mjs`, `proof_cache_row_w17.py`, `w17_gates.sh`, `build_manifest.py`) | Tái hiện A′ qua `run_pipeline` (chặng LLM đóng băng, 0 lượt gọi); đối soát fixture âm; corpus W17 (O/G) và addendum W17C (nhãn commit cùng test đỏ của tự rà soát) + census vòng 1–2 (luật SHIP §9 không đổi; vòng 2 so từng hàng với vòng 1); tiêm lỗi backend (thay thế nguyên văn TRONG BỘ NHỚ, cơ chế `_tiem` của W15) và frontend (worktree nháp, khôi phục byte-identical); chứng minh hàng cache; cổng danh tính; manifest run. Mọi script từ chối ghi đè kết quả đã có | → `diagnostics/OPERATION_BINDING_REPRODUCTION_*.json`, `NEGATIVE_FIXTURE_RECONCILIATION_*.json`, `ASSUMPTION_CENSUS_W17[_R2].json`, `ASSUMPTION_MECHANISM_DECISION_W17[_R2].json`, `logs/FAULT_INJECTION_W17*.log`, `PROOF_CACHE_ROW_W17.json`, `MANIFEST.json` | chạy script (lệnh ở docstring) |

### Construction binding & focused annotations — w18 (2026-10-04)

Run `docs/evaluation/geometry/runs/w18-binding-focus/`. Thẩm quyền đăng ký (viết TRƯỚC bản sửa): `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §16 (+ đính chính có ngày).

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Quan hệ dựng điểm của đề (§16.1) | `backend/app/simulation/semantic_program/construction_binding.py` (`QuanHeDung`, `doc_quan_he_dung`, `_TRUNG_DIEM`, `_LAN_LUOT`, `_NHAN`, `_HINH_CHIEU`, `_VAI_KHAC`) | Từ vựng ĐÓNG trên đề đã che mục tiêu (`shape_constraint.che_muc_tieu`): "X là trung điểm (của) AB", danh sách "X, Y lần lượt là trung điểm của AB, CD" (số đích = số đoạn, ghép theo thứ tự), "X là hình chiếu (vuông góc) của P lên/trên/xuống <đích>", "X là chân đường vuông góc/đường cao (kẻ/hạ) từ P xuống/đến/tới/lên <đích>"; đích = mặt phẳng gọi bằng điểm, đáy của khối duy nhất, đường qua hai điểm; một đích hai câu khác nhau ⇒ bỏ; vai trò ngoài từ vựng (tâm, trọng tâm, giao điểm…) ⇒ OUT_OF_SCOPE | đề → `doi_chieu_phep_dung` | `pytest tests/geometry/test_construction_binding.py -q` |
| Đối chiếu phép dựng điểm (§16.2–16.4) | `construction_binding.py` (`doi_chieu_phep_dung`, `KetQuaDoiChieu`, `_DanhTinh` (`diem`, `nhan`, `nhan_hoc_sinh`), `_so`, `_cung_nhan`, `_la_trung_diem`, `_quan_he_ct`, `_cau_ct`, `PHEP_TRONG_PHAM_VI`, `_SINH_DIEM`, `MA_LECH_PHEP_DUNG` = `CONSTRUCTION_NOT_TEXT_BOUND`, `MA_CHUA_DOI_CHIEU` = `CONSTRUCTION_BINDING_UNVERIFIED`) + `route.py` (chặng `construction_binding` sau thực thi, trước `source_invariant`; `SemanticRouteOutcome.construction_binding`) + `ai/pipeline.py` (`KHONG_SUA_NGUON` += `CONSTRUCTION_BINDING_UNVERIFIED`) | Danh tính qua thẩm quyền sẵn có (bí danh `assign var`, `assumption_gate._khoa`, nhãn, fact nguồn một ký hiệu, lưới hoà giải C₁a); trùng toạ độ/giá trị KHÔNG là bí danh. MATCHED / MISMATCHED (từ chối mọi vùng, nguyên nhân CONSTRUCTION, `reason_subjects` = [quan hệ đề, quan hệ đã dựng]) / UNVERIFIED (từ chối trong U3, nguyên nhân UNKNOWN) / AUXILIARY / OUT_OF_SCOPE / NOT_REALIZED; lỗi nội bộ ⇒ UNVERIFIED | chương trình + đề → route → envelope | `pytest tests/geometry/test_construction_binding.py -q` |
| Lời từ chối phép dựng điểm | `backend/app/learner_messages.py` (`_msg_lech_phep_dung_diem`, `_DUOI_LECH_PHEP_DUNG`, `_MSG_CHUA_DOI_CHIEU`, `_msg_chua_doi_chieu`) + `frontend/src/components/SimulationWorkspace.tsx` (`NHAN_GIAI_DOAN.construction_binding`; loại vấn đề "hệ chưa đối chiếu được phép dựng với đề" khi nguyên nhân khác CONSTRUCTION) | MISMATCHED nêu cả hai quan hệ ("Đề bài nêu "M là trung điểm của SA", nhưng phép dựng của AlgoSim lại dựng "M là trung điểm của SB"."), không bảo sửa đề; UNVERIFIED nói giới hạn của hệ, KHÔNG BAO GIỜ "đề sai" | envelope → thẻ từ chối | `pytest tests/geometry/test_construction_binding.py -q -k "loi_ or ma_chua"` · `npx vitest run src/components/refusal-contract.test.tsx` |
| Xuất xứ điểm dựng + ký hiệu thiết diện | `backend/app/simulation/semantic_program/simulation_state.py` (`_xuat_xu_hien_thi`: `source.binding` = `TEXT_RELATION` (MATCHED) / `AUXILIARY`, kể cả bí danh; `_ky_hieu_dien_tich_thiet_dien`: `S(T)` từ `doc_quan_he_cat`) | Điểm phụ của hệ mang xuất xứ, không bao giờ thành dữ kiện đề cho; ký hiệu ngắn cho diện tích thiết diện theo tên đề, không theo nhãn mô hình | state → cảnh | `pytest tests/geometry/test_construction_binding.py -q -k xuat_xu` · `pytest tests/geometry/test_scene3d_annotations.py -q -k ky_hieu` |
| Chóp tứ giác đều (regular-square-pyramid-w01) | `backend/app/simulation/semantic_program/shape_constraint.py` (`_CANH_DAY`, `_CANH_BEN`, `_TRUNG_DOAN`, `_TAM_DAY`; `regular_square_pyramid` + `base_square` khi ký hiệu chóp có "tứ giác đều"; `base_square`/`lateral_edge`/`apothem`/`base_centre` chỉ cho chóp đều DUY NHẤT; `phan_chua_doc` không còn báo chữ "đều" đã đọc) + `assumption_gate.py` (`_can_huu_ti`, `_khuon_chop_deu` = khuôn C1 **T7**: cạnh đáy + chiều cao trực tiếp / `SO` qua tâm đề gọi tên / trung đoạn / cạnh bên — cụm "cạnh bên bằng" HOẶC độ dài server đọc cho đoạn nối đỉnh với một đỉnh đáy (`SA = 3`, tự rà soát cuối `ad7172ab`; hai cạnh bên khác nhau ⇒ `TEMPLATE_CONTRADICTION T7: lateral edges`); hai nguồn chiều cao lệch ⇒ `TEMPLATE_CONTRADICTION T7`, h² ≤ 0 ⇒ suy biến, h² không là bình phương hữu tỉ ⇒ `TEMPLATE_NOT_REPRESENTABLE T7`; `_khuon_chop(..., do_dai)`) + `construction_binding.py` (`_GIAO_HAI_DUONG`, `_TAM_DAY`; quan hệ `intersection`/`centre`; `_quan_he_ct`/`_cau_ct`/`_so` cho `intersect_line_line`, trung điểm một đường chéo khớp tâm) + `simulation_state.py` (chiều cao ĐO: khoảng cách đỉnh ngoài đáy → mặt phẳng qua các đỉnh đáy là nguồn số của thể tích; `_nhan_du_kien_tu_fact`: GIVEN không ký hiệu mượn nhãn InputFact) + `scene3d.py` (`_attach_formulas`: luật W1 "một cạnh chỉ là chiều cao khi BẰNG chiều cao đo" ĐÃ THAY ở regular-square-pyramid-w02 bằng quan hệ ⊥ kiểm chính xác — mục w02 dưới) + `domain_profile.py` (`_MANH_MOI_NGHIA_VU["distance"]` += "độ dài") | Năng lực trong họ `convex_polyhedron`/`polyhedron` (không thêm hàng ma trận): AI đọc đề, engine dựng/kiểm/tính chính xác; chóp đáy vuông bất kỳ không thành chóp đều; "chứng minh … đều" không là tiền đề; tâm O gắn bằng danh tính giao hai đường chéo | đề + chương trình → route → cảnh | `pytest tests/geometry/test_regular_square_pyramid.py -q` |
| Vai trò, gộp, nhân chứng (backend, §16.5–16.7) | `backend/app/simulation/semantic_program/quantity_annotations.py` (`_nhan_chung` — chân CHÍNH XÁC qua `kernel.project_point_onto_line/plane`, `marker {u, v}`; neo `witness`; bản đo trùng giữ `same_as` + chẩn đoán `ANNOTATION_SAME_AS`) + `scene3d.py` (`_gan_so_do`: `role` ∈ given/intermediate/result; đáp số không mang `same_as`) | Gộp theo CÙNG chủ thể, không theo giá trị; hai vai trò cùng chủ thể giữ hai nhãn; nhân chứng chỉ cho khoảng cách điểm → đường/mặt | spec + bộ nhớ cuối → cảnh | `pytest tests/geometry/test_scene3d_annotations.py -q -k w18` |
| Nhãn tập trung + một nơi giải thích (frontend) | `frontend/src/simulations/domains/geometry/scene3d-annotations.ts` (`AnnotationView`, `DEFAULT_ANNOTATION_VIEW`, `annotationsAt(scene, step, view, selectedId)` — tiêu điểm qua `tangNhanManh`, `hasHiddenByDefault`, `witnessesShown`, `quantitySources`, `annotationAnchor` neo `witness`) + `scene3d-model.ts` (`QuantityAnnotation.role`/`same_as`/`witness`) + `scene3d-view.tsx` (`annotationView`, nhãn `role="button"` + `tabIndex` + listener mệnh lệnh, `vatNhanChung`, `NHAN_CHUNG_GOC`, `nhanChungRef`, móc `__geo3d_witness_ids`) + `Scene3DExplorer.tsx` (công tắc "Hiện tất cả", ô soi = vùng chi tiết duy nhất: công thức khi lời giải đóng + `geo3d-soi-nguon` "Từ dữ kiện đề cho"/"Tính trực tiếp từ") + `scene3d-solution.tsx` (`open`/`onOpenChange`, thu gọn mặc định, gộp `same_as` qua `goc`/`rieng`) + `scene3d-playback.tsx` (chuyển tiếp) + `styles/global.css` (`.geo3d-soi-nguon`, `.geo3d-so-do[role="button"]`) | Mặc định: tên điểm + dữ kiện; chọn đại lượng ⇒ nhãn của nó + chuỗi số; "Hiện tất cả" ⇒ mọi nhãn khả dụng (không lộ trước bước); không trần số nhãn; nhân chứng vẽ đè khi nhãn khoảng cách hiện; frontend không tính chân (guard 5D) | cảnh → DOM/three | `npx vitest run src/simulations/domains/geometry/` |
| Chọn đại lượng + «Các bước dựng» (regular-square-pyramid-w01, ROADMAP §0.1) | `frontend/src/simulations/domains/geometry/scene3d-model.ts` (`geometryStepList`, `quantityChoices`) + `Scene3DExplorer.tsx` (chip «Đại lượng», ngăn `ngan === "dai-luong"` — chọn ⇒ `chon(id)` rồi đóng ngăn; `moBuoc` giữ panel bước mở/đóng) + `scene3d-playback.tsx` (nút `geo3d-cac-buoc-mo`, panel `geo3d-cac-buoc`; dải `geo3d-focus` ĐÃ GỠ) + `scene3d-solution.tsx` (Kết quả chỉ khi lời giải mở) + `styles/global.css` (`.geo3d-cac-buoc*`, `.geo3d-dai-luong*`; lưới `.geo3d-player.co-cac-buoc` ≥1100px ĐÃ GỠ ở w02 → bảng nổi, mục w02 dưới) | Đáp số không còn card cố định: đọc qua ngăn «Đại lượng» → ô soi (một nơi chi tiết). Panel bước (W1): desktop cột cạnh khung — W2 thay bằng bảng nổi —, mobile trong dòng chảy dưới điều khiển, cuộn bên trong; chọn bước dừng phát và đặt neo, đóng/mở không đổi bước hay chọn | cảnh → DOM | `npx vitest run src/simulations/domains/geometry/scene3d-steps-panel.test.tsx src/simulations/domains/geometry/scene3d-playback.test.tsx` |
| Bảng nổi «Các bước dựng» (regular-square-pyramid-w02 · B, thay cột lưới W1) | `frontend/src/simulations/domains/geometry/scene3d-floating-panel.tsx` (`BangNoi`, `kepBang`, `viTriMacDinh`, `dichBangPhim`, `LE_BANG`, `BUOC_PHIM`; `data-panel-x/y`, `data-che-khung`) + `scene3d-playback.tsx` (`viTriBuoc` giữ vị trí qua đóng/mở, `khungRef` = `.geo3d-canvas`, nút `geo3d-cac-buoc-mo` cuối thanh điều khiển, `aria-controls` chỉ khi bảng có mặt, đóng ⇒ trả tiêu điểm cho nút) + `styles/global.css` (`.geo3d-bang-noi*`; lưới `.co-cac-buoc` ĐÃ GỠ; ≤ 48rem: trong dòng chảy, không kéo) | Desktop: nổi phía phải vùng mô phỏng, kéo bằng tiêu đề (con trỏ không tới canvas ⇒ không orbit), phím mũi tên dời, Escape đóng, nút về mặc định / thu gọn; luôn kẹp trong khung canvas khi kéo và khi đổi cỡ; mở/đóng không đổi cỡ canvas/camera. Khổ hẹp: bảng thu gọn được dưới điều khiển | cảnh → DOM | `npx vitest run src/simulations/domains/geometry/scene3d-steps-panel.test.tsx` |
| Nhãn đoạn chờ đoạn được dựng (regular-square-pyramid-w02 · A) | `frontend/src/simulations/domains/geometry/scene3d-annotations.ts` (`doanCoMat`, `capDiem`; `annotationsAt` bỏ nhãn `anchor: "segment"` khi chưa có đoạn mang nó: `endpoint_ids` của đoạn, cạnh vòng `vertex_ids` của đa giác, `edge_ownership` của khối) + `scene3d-view.tsx` (`data-thieu-cho`, móc `__geo3d_annotation_unplaced` — nhãn hợp lệ nhưng thiếu chỗ) + test `scene3d-label-formation.test.ts` (fixture W1 thật: chóp tam giác AB/AC/SA, lăng trụ AD, đối chứng) | Nhãn số đo chỉ khi đối tượng mang số đo đã dựng, ở mọi chế độ ("Hiện tất cả", đang chọn); dữ kiện vẫn ở ngăn «Đại lượng»; nhãn hợp lệ thiếu chỗ phân biệt với nhãn chưa hợp lệ | cảnh → nhãn | `npx vitest run src/simulations/domains/geometry/scene3d-label-formation.test.ts` |
| Đường cao SO + chiều cao theo quan hệ (regular-square-pyramid-w02 · C/E) | `backend/app/simulation/semantic_program/formation.py` (`_tam_day_deu` — nguồn chân đường cao ③: ràng buộc có kiểu `regular_square_pyramid` từ `shape_constraint` trên đề đã che mục tiêu + điểm dựng bằng giao hai đường chéo đáy / trung điểm một đường chéo ⇒ `DUNG_CAO` "Chiều cao SO") + `quantity_annotations.py` (`_bam_doan_da_dung`: nhân chứng có chân trùng điểm cảnh và đoạn đã dựng ⇒ nhãn bám đoạn, kind `length`; `chieu_cao_the_tich` + `_doan_cua_ten`: chiều cao của thể tích = nguồn số có đoạn ⊥ mặt đáy, một đầu trên đáy, độ dài khớp giá trị — hoặc khoảng cách tới mặt phẳng trùng đáy; ưu tiên dữ kiện đề cho; mơ hồ ⇒ không chọn) + `simulation_state.py` (`volume_heights` trong state) + `scene3d.py` (`_attach_formulas(objects, cao_theo_the_tich)`: luật giá trị bằng nhau của W1 `98e2b8f7` ĐÃ GỠ; ký hiệu đoạn đã dựng cho khoảng cách đo bám đoạn ấy — "V = 1/3 × S(ABCD) × SO", "SO = d(S, (ABC)) = 3") | SO có danh tính, vai trò, xuất xứ thật; không có nó khi đề không nói "đều" hay tâm sai danh tính; cạnh tình cờ bằng chiều cao không thành chiều cao | chương trình → cảnh | `pytest tests/geometry/test_regular_square_pyramid_w02.py tests/geometry/test_formula_provenance_closure.py -q` |
| Kiểm trình duyệt W18 (§16.8 + đính chính Task 7) | `frontend/scripts/compiler-scene-replay-lib.mjs` (`KIEU_TU_CHOI_W18`, `expectedAnnotationIds(scene, step, {showAll, selectedId})`, `annotationWorldAnchor` neo `witness`, `assessShowAllIsolation({before, on, off, back, …})` — mốc là trạng thái TRƯỚC lần bấm đầu, `assessDashFollowsSpans` — mỗi đoạn phân loại khuất vẽ nét đứt ở mọi bước dựng (`DASH_DIFFERS_FROM_OCCLUSION`), `coherentFormulaText`, `assessDetailRegion`, `assessWitness`, `solutionRowOf`, `expectedSolutionRows` bỏ dòng `same_as` khi dòng chủ có mặt) + `compiler-scene-suite.mjs` (`formulaRegions`, `clickSolutionRow`, `setSolutionOpen`, `annotationsMustShow`; khối bật/tắt/bật "Hiện tất cả" → `show_all`; chọn từng đại lượng → `selected_<kind>` + ảnh phần tử ô soi `detail_<kind>`, đáp số có công thức tham chiếu thêm `detail_region_open` khi lời giải mở; `formation.dash_under_highlight`; lượt dương ném lỗi ⇒ `run_completed` FAIL + `run_error`, không chết cả suite; `solution_final` thu gọn, `solution_expanded` mọi cỡ; `runServed` kiểm nhân chứng) + `generic-tier-a-scenarios.json` (ba từ chối W18 + hai ca phục vụ trên mục `cross_section`) + `backend/scripts/generate_generic_tier_a_fixtures.py` (khối W18: năm fixture `w18_*` từ builder của `test_construction_binding`) | Oracle ĐỘC LẬP đọc payload, không nhập module trình bày | fixture → trình duyệt (`dist/`) → `BROWSER_EVIDENCE.json` | `node --test scripts/compiler-scene-replay-lib.node-test.mjs` · `pytest tests/geometry/test_generic_tier_a_fixture_generator.py -q` |
| Sheet W18 | `backend/scripts/build_scene3d_visual_evidence.py` (`TRANG_THAI_CHON`, `TRANG_THAI_CHI_TIET`, `STATE_TITLES` W18, `W17_STATES` = `show_all`/`causal_restored`, tên ô từ chối/phục vụ W18) | Ô "chọn từng loại đo" + ô soi trên sheet; ảnh lời giải mở trên desktop | ảnh trình duyệt → `images/<họ>/SHEET.png` | `pytest tests/geometry/test_scene3d_visual_evidence.py -q` |
| Chẩn đoán w18 (run) | `docs/evaluation/geometry/runs/w18-binding-focus/diagnostics/` (`reproduce_construction_binding.py`, `construction_corpus_w18/build_corpus.py`, `construction_binding_census_w18.py`, `fault_injection_w18.py`, `run_fault_injections_w18.py`, `run_fault_injections_w18_frontend.mjs`, `diag_fw_single.mjs`, `proof_cache_row_w18.py`, `w18_gates.sh`, `build_manifest.py`) | Tái hiện qua `run_pipeline` (0 lượt gọi), corpus 23 hàng nhãn trước bản sửa, census W14–W18 (luật SHIP §9), tiêm lỗi backend (trong bộ nhớ) và frontend (worktree nháp; `diag_fw_single.mjs` chạy lại MỘT phép tiêm trình duyệt giữ toàn bộ stdout/stderr), chứng minh hàng cache, cổng danh tính, manifest run. Script từ chối ghi đè | → `CONSTRUCTION_BINDING_REPRODUCTION_*.json`, `CONSTRUCTION_BINDING_CENSUS_W18.json`, `CONSTRUCTION_BINDING_DECISION_W18.json`, `logs/FAULT_INJECTION_W18*.log`, `PROOF_CACHE_ROW_W18.json` | chạy script (lệnh ở docstring) |

### Coordinate-defined relation targets & frozen-evidence writer — w20 (2026-10-04)

Run `docs/evaluation/geometry/runs/w20-cleanup-premerge/`. Luật: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §17 (ghi SAU bản sửa; đăng ký trước bản sửa là nhãn `diagnostics/literal_target_corpus/LABELS.json`).

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Đích quan hệ đặt bằng toạ độ (§17) | `backend/app/simulation/semantic_program/construction_binding.py` (`DEFINED_BY_COORDINATES`, `MA_TOA_DO_THAY_DUNG` = `CONSTRUCTION_REPLACED_BY_COORDINATES`, `_DanhTinh.chuoi` — chuỗi `assign X = var Y` tới gốc, `goc_cua` = mắt cuối, `_DanhTinh.nguon` — khoá ký hiệu của RIÊNG một tên, `diem` = hợp `nguon` trên nhóm bí danh, `_DanhTinh.toa_do` — `point3` có giá trị không phải hạt giống, dùng `grounding_gate._is_seed`) + `route.py` (từ chối ở MỌI vùng) + `refusal_cause.py` (CONSTRUCTION) + `ai/pipeline.py` (`KHONG_SUA_NGUON`) + `learner_messages.py` (`_msg_toa_do_thay_dung`) | Tên mang đúng một ký hiệu đích của quan hệ §16.1, có toạ độ ở bất kỳ mắt nào của chuỗi bí danh (kể cả rồi mới dựng lại, kể cả lấy trùng một đỉnh đề cho) ⇒ `DEFINED_BY_COORDINATES`; không đọc giá trị toạ độ; thứ tự mã MISMATCHED → toạ độ → UNVERIFIED; chủ thể = [quan hệ đề, việc chương trình đã làm]; lời nói giới hạn kiểm chứng, không bảo sửa đề | chương trình + đề → route → envelope | `pytest tests/geometry/test_construction_binding_literal.py tests/geometry/test_construction_binding.py -q` |
| Đối soát đo trực tiếp không ghi bằng chứng đông cứng | `backend/scripts/reconcile_second_family_live_measurement.py` (`run_reconciliation(out_dir)` — thư mục ra BẮT BUỘC; từ chối `RECONCILIATION_DIR` và mọi thư mục bên trong; CLI `--out`) | Bốn output đi vào thư mục người gọi chọn; trường `note` của `SOURCE_EVIDENCE_INTEGRITY` phụ thuộc một file ngoài kho, nên chạy lại vào thư mục đông cứng là viết lại lịch sử | test (`tmp_path`) → so khớp | `pytest tests/geometry/test_second_family_live_measurement_reconciliation.py -q` |
| Chẩn đoán w20 (run) | `docs/evaluation/geometry/runs/w20-cleanup-premerge/diagnostics/` (`probe_literal_target.py` + `literal_target_corpus/LABELS.json`, `construction_binding_census_w20.py` (nhập nguyên census W18), `fault_injection_w20.py` + `run_fault_injections_w20.py` (FL1–FL9, FE1–FE3; `_tiem` của W15), `proof_cache_row_w20.py` (`corpus`/`envelopes`/`prove`), `scan_literal_then_construct.py`, `inventory_cleanup_w20.py`, `apply_cleanup_w20.ps1`) | Probe qua `run_pipeline` (chặng LLM đóng băng, 0 lượt gọi) với nhãn ghi trước bản sửa; census so từng hàng với W18; tiêm lỗi trong bộ nhớ (FE trỏ thư mục đông cứng sang bản sao tạm); chứng minh hàng cache; quét chương trình đã lưu; kiểm kê dọn dẹp có kiểm cơ giới, xoá theo đường dẫn chính xác có kiểm lại SHA-256. Script từ chối ghi đè | → `results/LITERAL_TARGET_PROBE_*.json`, `diagnostics/CONSTRUCTION_BINDING_{CENSUS,DECISION}_W20.json`, `results/logs/FAULT_INJECTION_W20*.log`, `diagnostics/PROOF_CACHE_ROW_W20.json`, `diagnostics/LITERAL_THEN_CONSTRUCT_SCAN.json`, `inventory/CLEANUP_INVENTORY.json`, `inventory/DELETION_LOG.json` | chạy script (lệnh ở docstring) |

### Docs history split, refusal card — run cuboid-final-review (2026-10-05)

Run `docs/evaluation/geometry/runs/cuboid-final-review/` — lượt chốt của việc `cuboid-visual-semantic-closure`, không
đánh số wave (`docs/evaluation/RUN_NAMING.md`).

| Thành phần | Path | Purpose · authority | Producer → consumer | Verify |
|---|---|---|---|---|
| Thẻ từ chối §17 | `construction_binding.py` (vế sau của chủ thể ở thể bị động, không kèm tên: `được đặt bằng toạ độ` / `được lấy trùng với điểm A`) + `backend/app/learner_messages.py` (`_msg_toa_do_thay_dung`: "Hệ chưa kiểm chứng được ‹quan hệ›, vì điểm này ‹cách› thay vì dựng từ quan hệ trong đề. Hệ tạm dừng để tránh đưa ra kết quả chưa kiểm chứng."; không còn `_DUOI_LOI_HE`) + `frontend/src/core/types.ts` (`AnalysisUnsupported.reason_code`, chỉ để chọn nhãn) + `frontend/src/components/SimulationWorkspace.tsx` (`UnsupportedNotice`: `reason_code` = `CONSTRUCTION_REPLACED_BY_COORDINATES` ⇒ loại vấn đề "chưa kiểm chứng được phép dựng", đọc TRƯỚC `refusal_cause`) | Toạ độ có thể đúng ⇒ nói CHƯA KIỂM CHỨNG, không nói "dựng lệch", không bảo sửa đề, không hứa gửi lại sẽ sửa được; tên và quan hệ đọc từ `reason_subjects`; mã không lên màn hình; nhãn của ca lệch (MISMATCHED) và chưa đối chiếu (UNVERIFIED) giữ nguyên | route → envelope → thẻ từ chối | `pytest tests/geometry/test_construction_binding_literal.py -q -k "chu_the or bien_pipeline or loi_ghep"` · `npx vitest run src/components/refusal-contract.test.tsx` |
| Kiểm thẻ từ chối trên trình duyệt | `frontend/scripts/compiler-scene-suite.mjs` (`runNegative`, `runServed` nay export; kỳ vọng tuỳ chọn `problem_label` = chữ của dòng "Loại vấn đề") + run `diagnostics/refusal_fixtures_cfr.py` (ca corpus đóng băng qua `run_pipeline`, kiểm mã và lời trước khi ghi) + `diagnostics/browser_refusal_cfr.mjs` | Ba ca mã `CONSTRUCTION_REPLACED_BY_COORDINATES` cùng đối chứng lệch / chưa đối chiếu / được phục vụ, hai khổ đã đăng ký, bản dựng production; không đo lại sáu họ | fixture → trình duyệt → `results/` + `images/` | `npm run build` rồi `node …/diagnostics/browser_refusal_cfr.mjs --cases <dir> --images <dir> --report <file>` |
| Tách lịch sử nguyên văn + kiểm kê tài liệu | run `diagnostics/split_history_cfr.py` (`--plan` · `--apply` · `--verify`) + `diagnostics/inventory_docs_cfr.py` | Khối lịch sử cắt từ blob `4048ff83`, chép nguyên văn vào `docs/legacy/*_INFORMATICS_ERA.md` và `CODE_INDEX_REMOVED_ENTRIES.md`; kiểm kê mọi file `docs/` (hàng theo file + nhóm bằng chứng) | tài liệu sống → legacy; kho → `inventory/` | `split_history_cfr.py --verify` |
| Chẩn đoán còn lại của run | run `diagnostics/cache_decision_cfr.py` (đọc envelope trước/sau của công cụ W20 `proof_cache_row_w20.py`; NO_BUMP chỉ khi mọi envelope được phục vụ trùng byte và lời từ chối chỉ khác `reason_subjects`) · `diagnostics/cfr_gates.sh` (cổng danh tính và toàn vẹn trong worktree sạch, khuôn `w20_gates.sh`, thêm kiểm `docs/legacy` và `split --verify`) · `diagnostics/build_manifest.py` (MANIFEST.json: sha256 cơ sở LF, producer, trạng thái đo) | Bằng chứng của quyết định cache và của lượt kiểm chứng `a1c53cdb` | run → `results/` | `bash …/cfr_gates.sh <sha> 4048ff83` từ gốc một worktree sạch |
