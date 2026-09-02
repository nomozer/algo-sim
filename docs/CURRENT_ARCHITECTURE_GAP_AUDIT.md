# CURRENT_ARCHITECTURE_GAP_AUDIT

> Soát lại **từ đầu** ở HEAD ngày **2026-09-03**, sau sáu wave: G1 · G2 · G3 ·
> G4 · `DISPLAY_NAME_AUTHORITY_LEFTOVER` · `REACT_ERROR_BOUNDARY_HARDENING`.
>
> **`SOURCE_CHANGES = 0` · `APPLICATION_LLM_CALLS = 0` · `NEW_EXPERIMENTS = 0`.**
>
> ⚠️ `GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT.md` **không còn là thẩm quyền**.
> Nó đã bị sửa tại chỗ sáu lần và nay là bằng chứng lịch sử của một phiên bản
> cũ. Thứ tự ưu tiên của nó bị bỏ; mọi kết luận dưới đây đo lại từ mã.

---

## 1. HEAD

```
HEAD                       6edba80
GIT_CLEAN                  yes (0 tệp)
CACHE_VERSION              63
STABLE_CAPABILITY_HASH     803722ff59dfbdf66d45dffb62c7b6b48bd9c1fcea1f0147cd041f22783e9b42
CURRENT_PRODUCT_CANDIDATE  40edfe75ebb772ca · 87 tệp mã sản phẩm · khớp bản đã đóng băng
SEALED_RESEARCH_BASELINE   a075e9f5…  (không đổi)
pytest                     2829 passed · 1 skipped · 1 deselected
vitest                     685 passed · 50 tệp
build                      PASS
thẻ văn phạm               4431 byte (đầy đủ) · 3316 byte (miền hình học)
```

---

## 2. AUTHORITY_MAP

| thẩm quyền | chủ sở hữu | bản sao dẫn xuất | khoá chống trôi |
|---|---|---|---|
| DOMAIN_ROUTING | `domain_profile.detect_domain` | — | `test_domain_profile` |
| REQUEST_CONTRACT | `request_contract.RequestContract` | — | pydantic |
| IR_TYPES | `contract.MemoryType` (21 giá trị) | lược đồ JSON ×2 | `test_schema_sync` (byte-đối-byte) |
| IR_SIGNATURES | `ir_static_check._CHU_KY` (9) + `_TOAN_HANG_LENH` | `validator._BIEU_THUC_HINH_HOC` (dẫn xuất) · thẻ văn phạm (sinh từ Pydantic) | `test_type_authority` đọc **AST** của `eval_geometry_expr` |
| GROUNDING | `grounding_gate` + `source_entities` | — | `test_grounding_gate` |
| CAPABILITY_HONESTY | `coverage_gate` + `geometry_obligations` | — | — |
| INTERPRETER | `interpreter.py` | — | — |
| EXACT_NUMBER | `geometry/radical.py` + `exact.py` | `ExactNumberJson` ở TS | `to_json`/`from_json` đối xứng |
| GEOMETRY_KERNEL | `geometry/kernel.py` · `measure.py` · `predicates.py` | — | — |
| SOLID_TOPOLOGY | `section.Polyhedron` | — | `__post_init__` |
| SECTION | `section.cross_section` | — | `test_section_coplanar_edge` (19 ca) |
| CHECKERS | `GEOMETRY_CHECKERS` (9) | — | `test_geometry_obligations` |
| DISPLAY_METADATA | `display_names.py` | — | `test_display_names` (30 ca) + `semantic-dumb-frontend.test.ts` |
| TRACE | `interpreter` phát `action`; `build_timeline` chiếu | — | bất biến #31 |
| SCENE3D_PROJECTION | `simulation_state.build_scene` → `scene3d.build_scene3d` | — | `test_scene3d` |
| TRANSPORT | `transport.to_transport` + `check_envelope_transport` | — | `test_KHONG_CO_FLOAT_o_bat_ky_dau` |
| RENDER_CONTRACT | `scene3d.RENDER_HINT` (8 kiểu) | `scene3d-model.RENDER_KINDS` (TS) | **`test_scene3d_ts_sync`** đọc tệp TS |
| INTERACTION_STATE | `interaction-state.ts` | — | `Scene3DExplorer.test` |
| PLAYBACK_STATE | xem §7 | — | — |
| ERROR_CONTAINMENT | `components/ErrorBoundary.tsx` | — | `error-boundary.test` + `certify-error-boundary` |
| CACHE_IDENTITY | `main.CACHE_VERSION` + `runtime_identity` | `cache_identity.lock.json` | **`test_cache_identity`** — khoá cặp (version ↔ môi trường sinh), đóng 2026-09-03 |

### AUTHORITY_DUPLICATIONS

**Không tìm thấy thẩm quyền nào bị nhân đôi mà không có khoá.** Ba cặp
đáng nghi đều là **bản sao có cổng đồng bộ**, không phải hai nguồn sự thật:

| cặp | phân loại |
|---|---|
| `_CHU_KY` ‖ luồng `if` của `eval_geometry_expr` | **mirror có khoá** — `test_type_authority` đọc AST, so hai tập |
| `RENDER_HINT` ‖ `RENDER_KINDS` | **mirror có khoá** — `test_scene3d_ts_sync` đọc thẳng tệp TS |
| lược đồ Pydantic ‖ 2 bản JSON | **artifact sinh có khoá byte** — `test_schema_sync` |

⚠️ Lượt soát trước từng ghi cặp thứ hai là *"không có khoá"*. **Sai** — nó chỉ
soi phía TS. Khoá có thật và đã bắt lỗi thật khi thêm `non_visual`.

---

## 3. CLOSED_WAVES_VERIFIED — đọc từ mã, không đọc doc

| wave | mệnh đề kiểm | nơi | kết quả |
|---|---|---|---|
| G1 | `label` không rơi về `id` | `simulation_state.py:330` dùng `ht["label"]`, không còn `or ten` | ✅ |
| G2 | kiểu KHAI thắng lớp runtime | `_KHAI_TUONG_THICH` + `_loai_ngu_nghia` (:219, :229) | ✅ |
| G3 | khử trùng đoạn thiết diện | `section.py:281,286` `frozenset(c)` + `da_gap` | ✅ |
| G4 | cầu nối kernel | `geometry_exec.py:350` gọi `plane_through_point_perpendicular_to`; `_CHU_KY` có 9 mục | ✅ |
| DISPLAY | 0 bảng dịch ở frontend | `semantic-dumb-frontend.test.ts` xanh; `grep` producer→tiếng Việt = 0 | ✅ |
| BOUNDARY | lưới chặn tồn tại, hai mức | `ErrorBoundary.tsx`; `App.tsx:180` + `:243`; `main.tsx:19` | ✅ |

---

## 4. SEMANTIC_TYPES & PIPELINE

`MemoryType` = 21 giá trị; **8 kiểu hình học** đi qua cảnh.

`Kh` khai được · `Dg` dựng được · `Ne` neo xuất xứ · `Th` thực thi · `Xx`
provenance · `Ht` siêu dữ liệu hiển thị · `Vt` vào trace · `Tr` qua transport ·
`Ve` vẽ được · `Tt` tương tác · `Do` đo được · `Ki` kiểm được.

| kiểu | Kh | Dg | Ne | Th | Xx | Ht | Vt | Tr | Ve | Tt | Do | Ki |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `point3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `vector3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ *chính sách* | ✅ | ✅ | ❌ |
| `line3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `plane3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `polygon3` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ⚠️ chỉ `coplanar` |
| `solid` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `section` | ❌ *cố ý* | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `quantity` | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ `readout` | ❌ | — | ✅ |

**`vector3` không phải gap.** `RENDER_HINT["vector3"] = "non_visual"` là **chính
sách được nói ra**: một vectơ tự do không có vị trí, nên vẽ nó ở đâu cũng là
renderer tự quyết một dữ kiện hình học. Kiểu được giữ nguyên qua transport, vật
vẫn chọn/soi/đo được.

`SEMANTIC_BUT_NOT_RENDERABLE = {}` · `TYPE_MISMATCH = 0` ·
`FRONTEND_SEMANTIC_INFERENCE = 0` · `RENDERER_INVENTED_SEMANTICS = 0`.

---

## 5. IR, KERNEL, VÀ KHẢ NĂNG VỚI TỚI

```
IR_OPERATIONS   9 biểu thức (_CHU_KY) + 6 câu lệnh dựng (_KIEU_DUNG)
                + declare_point + 4 lượng đo
CONSTRUCTION_MODEL   COMPOSITIONAL
SOLID_MODEL          GENERIC_TOPOLOGY  (vertices + faces, không enum họ)
```

### KERNEL_WITHOUT_IR_REACHABILITY — đo lại

`grep` mọi `def` trong `kernel.py`/`measure.py`/`predicates.py`, trừ lời gọi
trong chính lớp ấy:

| hàm | 0 người gọi ngoài kernel? | phân loại |
|---|:-:|---|
| `plane_through_point_parallel_to` | ✅ | **NOT_A_GAP** — hợp thành được (G4 chứng minh bằng witness chạy thật) |
| `line_through_point_parallel_to` | ✅ | **NOT_A_GAP** — như trên |
| `perpendicular_foot_line` | ✅ | **NOT_A_GAP** — như trên |
| `measure.degrees` | ✅ (chỉ 1 test) | **P2** — cửa thoát sang độ, cố ý không dùng trong đường chính xác |
| `predicates.collinear` | ✅ (0 người gọi, kể cả test) | **P2** — trùng vai với phép kiểm bên trong `Plane3.through` |

Mọi `cos_sq_*`, `parallel_vectors`, `perpendicular_vectors`, `volume_pyramid_fan`
**có** người gọi (nội bộ lớp, hoặc oracle độc lập ở `test_oracle_independence`).

`COMPOSITION_BREAKS` sau G4: **không còn phép dựng nào của nhóm "qua một điểm,
song song/vuông góc" bất khả**. Còn lại một thiếu thật ở **cả hai tầng**:
`area` — không có trong IR **và** không có trong kernel.

`IR_WITHOUT_RUNTIME_PATH` = **0**.

---

## 6. NEW_PROBLEM_WITHIN_IR_REQUIRES_CODE = **NO**

`grep -niE "chop|pyramid|prism|cube|tetrahedron|simulation_id ==|demo_id|problem_text =="`
trên `app/simulation/**` và `app/ai/pipeline.py`, sau khi trừ chú thích:

| còn lại | phân loại |
|---|---|
| `measure.volume_tetrahedron` · `volume_pyramid_fan` | helper hình học tổng quát (4 điểm / đỉnh + đáy bất kỳ) |
| `section.pyramid_square` · `box` | **test-only**, 0 lượt import từ mã sản phẩm |
| `obligations.TERM_TRANSFORMS` / `postconditions` `"cube"` | phép `x³` của miền số học |

**0 nhánh theo họ hình · 0 dispatch theo `simulation_id` · 0 nhánh theo văn bản
đề** trên tuyến ngữ nghĩa. Frontend: `registerAllSimulations()` gọi đúng **một**
dòng.

---

## 7. TRẠNG THÁI TƯƠNG TÁC & PLAYBACK

`INTERACTION_STATE_AUTHORITIES = 1` — `interaction-state.ts` giữ cả sáu trường
(`selected_id` · `hidden_ids` · `isolated_ids` · `exploded_groups` ·
`transparent_ids` · `current_step`). `classroom-sync.apDungPhien` là **reducer
thuần** chiếu một chiều vào đó, không phải store thứ hai.

`PLAYBACK_AUTHORITIES = 2`, và **không trùng nhau**:

| bề mặt | ai giữ bước | ai hiện |
|---|---|---|
| xưởng 3D (hình học) | `InteractionState.current_step` | `scene3d-playback` |
| đường 2D (di sản) | engine: `timeline.currentStep(active.state)` | `SimulationControls` |

Hai bề mặt **không cùng lúc hiện**: `App.tsx:209` ẩn khay 2D khi `canvasFirst`.
`scene3d-playback` có `stepTrong` cục bộ nhưng nó chỉ sống khi không nhận
`interaction` — trong xưởng thì luôn nhận, nên là mã dự phòng, không phải thẩm
quyền thứ hai.

`STATE_WITHOUT_RESET` = **0**: `useEffect([scene])` đặt lại trạng thái khi đổi
bài (bản vá `Bước 10/6`), và `ErrorBoundary.resetKey` đặt lại lưới theo cùng
danh tính.

---

## 8. ĐỊNH TUYẾN MIỀN — và câu hỏi đúng về nó

`detect_domain` là **tất định, chạy trên văn bản, 0 lượt gọi model**. Bốn mức:
cụm quan hệ mạnh → phủ quyết Tin học → danh từ khối → ≥3 cụm yếu → mặc định
`tin_hoc`.

| | |
|---|---|
| `FALSE_NEGATIVE_RISK` | đề hình học dùng danh từ ngoài danh sách (*hình chóp cụt*, *bát diện đều*) và quá ngắn ⇒ bị đẩy sang `GATE_OUT_OF_SCOPE` |
| `FALSE_POSITIVE_RISK` | đề Tin học mượn từ vựng hình học ⇒ đi vào đường sinh rồi bị từ chối ở cổng sau |
| `MODEL_COST_IMPACT` | âm tính giả: **0 lượt gọi** (`pipeline.py:772` rẽ TRƯỚC mọi lời gọi). Dương tính giả: tốn lượt analyze + tổng hợp |
| **`CORRECTNESS_IMPACT`** | **KHÔNG** — định tuyến sai **không bao giờ** cho ra hình học sai; nó cho ra một lời từ chối |

Đây là câu hỏi §19 đặt ra, và câu trả lời quyết định mức ưu tiên: đây là vấn đề
**phủ và trải nghiệm**, không phải vấn đề **đúng sai**.

---

## 9. R0 / TRUNG THỰC NĂNG LỰC — **PASS**

- Mọi toán hạng hình học trong IR là `GeometryName` (`str`), cưỡng chế ở lược
  đồ. Phép mới của G4 cũng vậy — `test_C_R0_toan_hang_chi_nhan_TEN` khoá.
- `construct_point` chỉ nhận `PointExpr`; `tu_choi_toa_do_trong_construct_point`
  chặn toạ độ đi thẳng.
- `grounding_gate` chốt ⑤/⑥ chặn **rửa năng lực**: điểm không có trong đề không
  được khai toạ độ; nhãn đề giới thiệu như hệ quả thì phải DỰNG.
- G4 **không** mở cửa mới: chính hai cổng ấy là thứ chứng minh khoảng trống của
  nó là thật.

---

## 10. CHẶN LỖI — ma trận, không phải một boolean

| lớp | trạng thái | bằng chứng |
|---|---|---|
| `REACT_RENDER_BOUNDARY` | **CLOSED** | hai mức; `certify-error-boundary` 9/9 (tiêm lỗi thật) |
| `EVENT_HANDLER_EXCEPTION` | **NOT_COVERED** *(P2)* | React không bắt; xem dưới |
| `PROMISE_REJECTION` | **NOT_COVERED** *(P2)* | 6 tệp có `await`, 5 tệp có `catch` cục bộ |
| `RAF_EXCEPTION` | **NOT_COVERED** *(P2)* | vòng vẽ Three.js |
| `WEBGL_INITIALIZATION_FAILURE` | **HANDLED** | `tryCreateWebGLRenderer` → `GEOMETRY_WEBGL_FALLBACK` |
| `WEBGL_CONTEXT_LOSS` | **NOT_COVERED** *(P2)* | không có listener `webglcontextlost` |

### Rủi ro async, đo thật

| tệp | `await`/`then` | `catch` | đánh giá |
|---|:-:|:-:|---|
| `state/classroom.ts` | 44 | 18 | có xử lý cục bộ |
| `state/auth.ts` | 11 | 5 | có |
| `llm/client.ts` | 5 | 3 | có |
| `components/ProblemInput.tsx` | 3 | 1 | có |
| `components/AuthGate.tsx` | 2 | **0** | **không phải lỗ**: `login`/`register` ở store đã `.catch(() => null)` và đặt `error`; chúng không ném |

`CAN_WHITE_SCREEN` = **0** đường async tìm được. Một promise bị từ chối trong
trình xử lý sự kiện **không** gỡ cây React — nó thành ngõ cụt, không thành màn
trắng.

### Vòng đời WebGL — không rò sau sự cố

`scene3d-view.tsx:493-535`: cờ `song` chặn vòng RAF, `removeEventListener` ×3,
`dieuKhien.dispose()`, `renderer.dispose()`, gỡ canvas khỏi DOM, xoá 3 ref.
Không rò RAF, không nhân đôi canvas, không nhân đôi listener sau crash → retry.

---

## 11. FAIL-CLOSED MATRIX

| tình huống | thông điệp | dựng cảnh? | lượt gọi model | lối thoát |
|---|---|:-:|:-:|---|
| ngoài miền | *"Hệ thống này mô phỏng HÌNH HỌC KHÔNG GIAN…"* | 0 | **0** | nhập đề khác |
| năng lực không hỗ trợ | *"BÀI NÀY KHÔNG CẦN MÔ PHỎNG"* | 0 | ≥1 | có |
| xuất xứ không đủ | *"CHƯA DỰNG ĐƯỢC MÔ PHỎNG"* | 0 | ≥1 | có |
| chương trình không hợp lệ | như trên | 0 | ≤4 | có |
| lỗi hình học lúc chạy | như trên | 0 | ≤4 | có |
| checker không qua | như trên | 0 | ≤4 | có |
| envelope hỏng | bề mặt phòng thủ, không ném | 0 | 0 | có |
| ngoại lệ frontend | *"Có lỗi khi hiển thị phần này…"* | — | 0 | **Thử lại** / mở bài khác |

`certify-refusal-surface` **21/21**: 5 hạng đúng nhãn, 0 canvas, 0 mã kỹ thuật
lọt UI, 4 dạng envelope hỏng không ném. `FAKE_SCENE = 0` ·
`WRONG_CATEGORY_MESSAGE = 0` · `TECHNICAL_LEAK = 0`.

---

## 12. CACHE IDENTITY — *(đã đóng 2026-09-03, xem cuối mục)*

| thứ đổi | có làm cache mất hiệu lực không? |
|---|---|
| `CACHE_VERSION` | ✅ theo định nghĩa |
| chữ ký IR (`_CHU_KY`…) | ⚠️ **không tự động** — nó đổi `stable_capability_hash`, mà hash ấy **không nằm trong khoá cache** |
| prompt `app/ai/skills/*.md` | ⚠️ **không tự động** |
| thẻ văn phạm | ⚠️ **không tự động** (dẫn từ contract, nhưng khoá cache không đọc) |

Khoá cache = *text đã chuẩn hoá + `CACHE_VERSION`*. Ba dòng ⚠️ ở trên chỉ được
xử lý bằng **kỷ luật con người**: `CLAUDE.md` dặn *"đổi prompt ⇒ bump"*, và lịch
sử cho thấy quy ước được tuân thủ nghiêm (63 lần bump, mỗi lần một chú thích lý
do). Nhưng **không có test nào bắt buộc**.

`grep` xác nhận: không guard nào nối `prompt fingerprint` ↔ `CACHE_VERSION`.
`runtime_doctor` **có** so vân tay prompt, nhưng nó trả lời câu *"container có
đang chạy mã cũ không"* — một câu hỏi triển khai, không phải câu hỏi hiệu lực
cache.

**Hệ quả nếu quên bump:** một đề đã phân tích tiếp tục được phục vụ bằng
envelope sinh từ **một phiên bản hệ không còn tồn tại**, và không gì phát hiện.
Đây là *"meaning changes but cache identity does not"* mà §25 gọi tên. Nó không
làm hình học sai — kernel vẫn tính đúng — nhưng nó làm **phép đo sai**: chạy lại
sau khi sửa prompt sẽ đo phải bản cũ ở mọi đề đã cache.

⚠️ Chính kho này đã dùng đúng lập luận *"một bảng phải nhớ cập nhật là một bảng
sẽ quên"* để gỡ `TU_PHEP_DUNG`. Lập luận ấy áp vào đây không yếu hơn.

> ### ✅ ĐÓNG 2026-09-03 — `CACHE_IDENTITY_COMPLETENESS`
>
> `runtime_identity.semantic_environment_fingerprint()` gom **năm** đầu vào
> tĩnh: `prompts` · `grammar_card` · `synthesis_schema` · `analyze_schema` ·
> `capability`. `backend/cache_identity.lock.json` ghi cặp *(CACHE_VERSION ↔
> băm môi trường)*, và `tests/test_cache_identity.py` đỏ khi cặp lệch — theo
> **cả hai chiều**: môi trường đổi mà version đứng yên, hoặc version bump mà
> khoá chưa làm mới.
>
> **Khoá cache runtime không đổi một dòng.** Đây là *kỷ luật phiên bản được máy
> cưỡng chế*, không phải *cache địa chỉ theo nội dung*.
>
> Còn lại một phần **nhỏ và có biên rõ**: vài câu bọc tiếng Việt trong
> `pipeline.py` (*"Hãy sửa ĐÚNG chỗ đó…"*, tiêu đề khối dữ kiện/nghĩa vụ) chưa
> vào vân tay — băm cả tệp 794 dòng sẽ đỏ theo mọi lần sửa logic không liên
> quan, và báo động giả là cách nhanh nhất để một cổng bị tắt. Mảnh hợp đồng
> gửi kèm lượt sửa (`manh_hop_dong`) thì **đã** được phủ: nó chọn các dòng của
> chính thẻ.

---

## 13. MIỀN SỐ · ĐIỀU KHIỂN · TRACE · TRANSPORT

```
EXACT_NUMERIC_DOMAIN   Fraction ∪ Radical(he·√can), can không chính phương,
                       MAX_RADICAND = 10¹². Toạ độ LUÔN Fraction thuần.
                       `√2 + √3` TỪ CHỐI tường minh.
SYMBOLIC_DOMAIN        KHÔNG CÓ. Không tham số ký hiệu, không CAS.
                       Đề "cạnh a" xử lý bằng CHUẨN HOÁ TỈ LỆ (a := 1).
CONTROL_FLOW_MODEL     HYBRID trong lược đồ (if/while/for/break/return — di sản
                       Tin học), STRAIGHT_LINE trong thực tế hình học.
CONTROL_FLOW_DEFINITE_ASSIGNMENT = PARTIAL — fail-open trong nhánh lồng.
                       Tác động thực tế trong phạm vi hiện tại: ≈ 0 (không dạng
                       bài nào cần rẽ nhánh; thiết diện lặp trong kernel).
TRANSPORT              `check_envelope_transport` là cổng riêng; 0 float lọt.
                       TRANSPORT_LOSS = 0 · NON_SERIALIZABLE_STATE = 0.
```

### TRACE_CONTRACT — trường và người tiêu thụ

| trường | người phát | số người đọc ở frontend | phân loại |
|---|---|:-:|---|
| `step_index` | `build_scene_events` | nhiều | ACTIVELY_USED |
| `object` | như trên | `objectsAt`, `highlightedAt` | ACTIVELY_USED |
| `depends` | như trên | `highlightedAt` | ACTIVELY_USED |
| `explanation` | như trên | `narrationAt` | ACTIVELY_USED |
| **`action`** | như trên | **0** | **DEAD** |

`grep '\.action\b'` trên toàn `frontend/src` (trừ test) = **0 kết quả**. Phân
biệt sư phạm mà backend cố ý tính (`MEASURE` tách khỏi `CREATE`) hiện **không
tồn tại trên màn hình**. Không xoá — xem §15.

---

## 14. HIỂN THỊ, HỢP ĐỒNG VẼ, PHẠM VI SẢN PHẨM

```
DISPLAY_AUTHORITY                 BACKEND_ONLY
  label · notation · reference · role  — bốn vai, một chủ
FRONTEND_OPERATION_TO_LANGUAGE_MAP  0
RAW_ID_LEARNER_FALLBACK             NO
NESTED_DESCRIPTION_AMBIGUITY        CLOSED (bọc «…» khi toán hạng nhiều chữ)
RENDER_CONTRACT_SYNC                CÓ KHOÁ (test_scene3d_ts_sync)
```

**Nhãn vẫn có thể dài** — dài nhất trong 5 bài mẫu: **59 ký tự**
(*"Khoảng cách giữa S và «Mặt phẳng qua B và vuông góc với SC»"*). Phân loại:
**PRODUCT_QUALITY**, không phải ARCHITECTURE — nghĩa đúng, ranh giới rõ, chỉ
dài. Sửa triệt để cần một ô nhãn cho `assign`, tức **đổi lược đồ model-facing**
và bắt mô hình sinh thêm token; không tự mở.

### CURRENT_PRODUCT_SCOPE — từ mã, không từ mong muốn

```
POLYHEDRAL_SCOPE   đa diện LỒI bất kỳ, khai bằng đỉnh + bảng mặt.
                   lõm/mặt hở/không manifold: REJECTED (fail-closed)
                   mặt suy biến (đỉnh thẳng hàng): REJECTED
                   giao chiều thấp (điểm/đoạn): REJECTED có mã riêng
CONSTRUCTION_SCOPE điểm (5 phép) · vectơ (1) · đường (2) · mặt (3) ·
                   đa giác (1) · khối (1) · thiết diện (1) · tịnh tiến (1).
                   Không quay/vị tự/đối xứng.
MEASUREMENT_SCOPE  distance (6 cặp) · angle_cos_sq (4 cặp) · angle_cos (vectơ) ·
                   volume (khối lồi). KHÔNG có area, ratio.
CHECKER_SCOPE      9 nghĩa vụ.  VISUAL_SCOPE 6 loại vẽ + non_visual.
INTERACTION_SCOPE  chọn · soi · ẩn · cô lập · tách khối · tua · camera · reset.
                   KHÔNG kéo–thả liên tục (phá bất biến #31, cố ý).
CURVED_GEOMETRY    NONE ở cả 5 tầng, cưỡng chế ở 3 chỗ (MemoryType đóng ·
                   RENDER_HINT đóng · ca vitest cấm Cylinder/Cone/Torus…).
                   Prompt dặn mô hình TỪ CHỐI THẲNG thay vì thay bằng khối
                   gần giống.
```

### MODEL_COST_FLOW

```
NORMAL_NEW_PROBLEM_MODEL_CALLS   2   (analyze 1 + tổng hợp 1)
MAX_REPAIR_CALLS                 3   (MAX_SEMANTIC_PROGRAM_ATTEMPTS)
OFFLINE_MODEL_CALLS              0   — 8 lượt đo trình duyệt chạy KHÔNG có backend
PLAYBACK_MODEL_CALLS             0
INTERACTION_MODEL_CALLS          0
định tuyến miền                  0   (tất định, trên văn bản)
```

`OFFLINE_ZERO_MODEL_FLOW` = **PASS**, và đó không phải suy luận: cả 8 kịch bản
`certify-*` chạy chỉ với `npm run dev`.

---

## 15. PHÂN LOẠI

### P0_ARCHITECTURE — **KHÔNG CÓ**

Bảy tiêu chí P0 đều không trúng: không tuyên bố lõi nào sai · không hard-code
theo họ hình · không thẩm quyền nào bị nhân đôi mà thiếu khoá · renderer không
suy ngữ nghĩa · không thẩm quyền tất định nào bị đi vòng · R0 nguyên vẹn · bài
mới trong IR không cần mã.

### P1_PRODUCT

| id | gap | vì sao P1 |
|---|---|---|
| ~~**C1**~~ | ~~`CACHE_IDENTITY` không phủ prompt và chữ ký IR~~ — ✅ **ĐÓNG 2026-09-03** (`CACHE_IDENTITY_COMPLETENESS`). `runtime_identity` xuất thêm `semantic_environment_fingerprint()` (5 thành phần), và `backend/cache_identity.lock.json` khoá cặp *(CACHE_VERSION ↔ môi trường)*. Khoá cache runtime **không đổi** — đây là kỷ luật phiên bản được máy cưỡng chế, không phải cache địa chỉ theo nội dung. | — |

**`P1_PRODUCT_GAPS = 0`** sau khi C1 đóng. Không nâng P2 nào lên thay chỗ.

### P2_IMPROVEMENT

| id | gap |
|---|---|
| P2-a | `events[].action` — **DEAD**, 0 người đọc |
| P2-b | định tuyến miền bằng danh sách từ khoá — âm tính giả trên danh từ khối lạ; **0 tác động đúng-sai**, 0 lượt gọi |
| P2-c | `EVENT_HANDLER_EXCEPTION` · `PROMISE_REJECTION` · `RAF_EXCEPTION` chưa chặn — chưa có ca hỏng đo được, `CAN_WHITE_SCREEN = 0` |
| P2-d | `WEBGL_CONTEXT_LOSS` chưa phục hồi (khởi tạo thì đã fail-safe) |
| P2-e | nhãn dài (59 ký tự) — nghĩa đúng, chỉ dài |
| P2-f | `predicates.collinear` · `measure.degrees` — 0 người gọi |
| P2-g | `polygon3` chỉ có `coplanar`; `section` không đo được |

### NOT_ACTUALLY_GAPS — đánh giá lại từ đầu (§33)

| ứng viên cũ | phán quyết |
|---|---|
| `skew_lines` / `line_in_plane` chưa có checker | **NOT_A_GAP** — không nghĩa vụ nào của phạm vi hiện tại cần chúng; kernel có vị từ, và checker chỉ tồn tại cho nghĩa vụ mà đề đặt ra |
| 3 hàm kernel "0 người gọi" | **NOT_A_GAP** — hợp thành được, đã có witness chạy thật ở G4 |
| `vector3` không vẽ | **NOT_A_GAP** — chính sách được nói ra |
| `assign` thiếu ô nhãn | **NOT_A_GAP ở tầng kiến trúc** — P2-e ở tầng chất lượng |
| hình học cong | **OUT_OF_SCOPE** — vắng mặt có chủ đích, cưỡng chế ba tầng, mô hình được dặn từ chối thẳng |
| `CONTROL_FLOW_DEFINITE_ASSIGNMENT = PARTIAL` | **NOT_A_GAP trong phạm vi** — không dạng bài nào cần rẽ nhánh; kernel vẫn fail-closed |

### OUT_OF_SCOPE

mặt cong · CAS / tham số ký hiệu · khối lõm & mặt hở · `area`/`ratio` · kéo–thả
liên tục kiểu GeoGebra · phép biến hình quay/vị tự/đối xứng.

---

## 16. KẾT

```
ARCHITECTURE_GENERALITY   STRONG
```

Lượt soát trước xếp **MIXED** vì tiêu chí *"renderer phải tự suy semantics"*
đang bị vi phạm ở hai chỗ. Hai chỗ ấy nay **bằng 0**, và mọi tiêu chí P0 khác
cũng sạch. Phần lõi thì vốn đã vững và vẫn vững: khối tổng quát thật (chạy đúng
trên bát diện đều không có helper), 0 special-case theo họ hình, bài mới không
cần mã, R0 cưỡng chế ở lược đồ.

**`TITLE_FIT = ACCEPTABLE_WITH_SCOPE`** — không đổi, và lý do không đổi: kiến
trúc **là** tổng quát trong phạm vi đã tuyên bố, nhưng tên đề rộng hơn thứ dựng
được (không mặt cong, chỉ khối lồi, không đại số ký hiệu). Bản thảo phải nói
phạm vi ở chỗ người đọc gặp tên; §5.3 đang làm việc đó.

```
SOURCE_CHANGES          0
APPLICATION_LLM_CALLS   0
NEW_EXPERIMENTS         0
```

---

## 17. NEXT_ACTION

**`P0 = 0`, `P1 = 1`** ⇒ theo luật quyết định, chọn đúng P1 ấy:

> **`CACHE_IDENTITY_COMPLETENESS`** — nối khoá cache với **thứ thật sự quyết
> định ý nghĩa của một envelope**: vân tay prompt + băm năng lực, chứ không chỉ
> một con số người phải nhớ tăng.

Hình dạng nhỏ nhất, đủ để nó thôi là kỷ luật con người: một guard tất định băm
`app/ai/skills/*.md` cùng `stable_capability_hash()` và **ĐỎ khi băm đổi mà
`CACHE_VERSION` không đổi** — cùng khuôn sync-lock kho đã dùng cho lược đồ và
cho `RENDER_KINDS`. Không đổi cấu trúc cache, không đổi hành vi phục vụ.

⚠️ Đây là **P1, không phải P0**: nó không làm hình học sai, và quy ước hiện đang
được tuân thủ. Nhưng nó là chỗ duy nhất còn lại trong kho nơi **một thay đổi có
ý nghĩa không để lại dấu vết nào trong danh tính**, và kho này đã dùng đúng lập
luận ấy để gỡ hai thẩm quyền trùng trước đó.
