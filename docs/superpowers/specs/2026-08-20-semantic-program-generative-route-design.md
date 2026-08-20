# Đường sinh ngữ nghĩa — `generic.semantic_program` (design)

Ngày: 2026-08-20 · Trạng thái: **APPROVED DESIGN** — §1–§6 duyệt từng phần
trong phiên brainstorm; **vòng correction 1** (8 điểm + 3 chỉnh nhỏ + scope
rebaseline) và **vòng correction 2** (khoá phạm vi khoá luận §1.1 · eligibility
rubric §7.2 · freeze protocol §7.3 · luật con dấu §7.4 · tách claim D §6.5 ·
seal-sớm/mở-muộn + `stage_semantic_program` + serving gate §10) đã áp.
Duyệt 2026-08-20. Triển khai theo MỘT execution plan liên tục bám §10;
checkpoint là machine gate (test phải xanh mới đi tiếp), KHÔNG phải cổng xin phép.
Đề tài: "Hệ thống mô phỏng tương tác kết hợp LLM phân tích bài toán bằng ngôn
ngữ tự nhiên, hỗ trợ dạy học môn Tin học THPT."

> **Spec này MỞ LẠI khoá phạm vi.** `docs/STATUS_LEDGER.md §0` và bản cắt phạm
> vi 2026-08 đóng băng tầng năng lực ở 24 target. Hướng dưới đây do **giáo viên
> hướng dẫn** yêu cầu và **thay thế** khoá đó ở đúng phần "sinh mô phỏng".
> §8 là việc bắt buộc: không cập nhật ledger thì phiên sau agent đọc §0 sẽ tự
> dừng vì xếp task này OUT_OF_SCOPE.

## 0. Sự cố kích hoạt

Hai sự kiện độc lập, cùng chỉ về một hướng.

**(a) Yêu cầu của giáo viên hướng dẫn.** Hướng "thêm module thủ công cho từng
target" bị đánh giá là không ổn. Yêu cầu: **AI sinh được mô phỏng từng bước**,
với ba ràng buộc — đầu ra không lỗi · hiển thị chuẩn xác · **tốn ít token**.

**(b) Ảnh chụp một lượt chạy thật của `semantic_program`** (đề: kiểm tra ngoặc
hợp lệ bằng Stack). Thuyết minh dưới cùng đọc: *"Lấy phần tử trên cùng của ngăn
xếp ra: `[`. So sánh với ký tự hiện tại `]`. Vì `[` và `]` là một cặp ngoặc hợp
lệ, chúng khớp nhau."* — **chính xác tuyệt đối**. Cùng lúc đó trên hình: ngăn
xếp **rỗng**, "Ký tự hiện tại" = `0`, "Kết quả" = `0`, con trỏ `i` **đè lên**
dòng chữ.

Chẩn đoán: lời kể đã tới bước 15, hình còn đứng ở bước 0. **Chương trình do AI
sinh đúng, interpreter chạy đúng, trace đúng — chỉ khúc nối vứt trạng thái.**
Đây là lỗi mã tất định, không phải rủi ro cố hữu của việc để AI sinh. Ghi rõ
điều này vì chẩn đoán nhầm ở đây sẽ dẫn tới quyết định kiến trúc sai.

## 1. Mission

Chuyển việc **tạo mô phỏng** từ "người viết thêm một module cho mỗi target"
sang "**LLM viết một chương trình ngữ nghĩa, engine tất định thực thi và diễn
hoạt nó**" — mà không nới ranh giới R0 một milimet: **LLM không bao giờ là
authority của kết quả**.

Ba ràng buộc của giáo viên hướng dẫn ánh xạ thành ba cam kết kiểm được:

| Ràng buộc | Cam kết | Kiểm ở |
|---|---|---|
| Đầu ra không lỗi | Chương trình không hợp lệ **không chạy được**; nghĩa vụ thiếu thì **từ chối** | §5 (C₁a/C₁b/C₂), §7 (L2) |
| Hiển thị chuẩn | Khung hình thứ `k` **suy được hoàn toàn** từ trạng thái bước `k` | §4 (bất biến 4.2), §7 (L3) |
| Tốn ít token | Claim **cấu trúc** (đúng theo cấu tạo) + claim **thực nghiệm** trên matched subset | §6.2, §6.5 |

## 1.1 Phạm vi khoá luận — KHOÁ CỨNG

### Câu phạm vi

> **Khoá luận xây dựng và đánh giá một đường sinh mô phỏng 2D cho một lớp bài
> toán thuật toán rời rạc, hữu hạn và có thủ tục thực thi có biên; LLM chuyển
> yêu cầu ngôn ngữ tự nhiên thành bounded Semantic IR, còn execution,
> correctness checking và visual-state derivation do các thành phần tất định sở
> hữu.**

**Không** phải: *"AI sinh được mọi mô phỏng Tin học THPT."*

Câu này cố ý **không** định nghĩa phạm vi bằng "những gì IR biểu diễn được" —
làm thế là để hiện vật tự định nghĩa phạm vi của chính nó, và population nghiên
cứu trở thành vòng tròn. Population được định nghĩa **trước và độc lập** bằng
eligibility rubric ở §7.2.

### MVP của route

> `generic.semantic_program` v1 = **algorithmic bounded IR + 2D only + không mở
> primitive/type mới.**

### Sáu ranh giới implementation

1. **Chỉ miền thuật toán / cấu trúc dữ liệu.** Không HTML/CSS, CSDL, đóng gói
   giao thức, vật lý, hình học (§9).
2. **Không mở IR theo từng đề.** Case không diễn đạt được → `capability_gap`.
   Chỉ mở IR khi phát hiện một abstraction **tái sử dụng rộng** — và chỉ từ DEV
   (§7.3).
3. **2D only.** Không làm 3D cho route này. 3D không giúp chứng minh claim
   NL→IR→thực thi tất định→visual trace, mà kéo theo renderer, camera, layout,
   visual regression.
4. **Không thay thế 24 module.** Chúng giữ nguyên để phục vụ và làm oracle (§3.7).
5. **Không làm tối ưu sản phẩm phụ.** Không pattern reuse, không explicit context
   caching, không cho mức yếu phục vụ học sinh (§9).
6. **Không biến obligation taxonomy thành dự án theorem prover.** Một tập checker
   nhỏ, đại diện, **đóng băng trước SEALED** (§5.1, §7.3).

### Bốn claim phải chứng minh — và chỉ bốn

| | Claim | Bằng chứng |
|---|---|---|
| **A** | **Generativity** — có bài held-out **không module** mà LLM vẫn sinh IR hợp lệ và chạy đúng | §7.1–7.3 |
| **B** | **Correctness boundary** — chạy được **chưa đủ**; chỉ case đủ assurance mới phục vụ; `capability_gap` tách khỏi `verification_gap` | §3.6, §5.4 |
| **C** | **Visualization fidelity** — trace→frame có bất biến tất định; không còn "narration bước 15, hình bước 0" | §4.2, §7 (L3) |
| **D** | **Token efficiency** — hai claim tách bạch (§6.5) | §6 |

**A và B là ĐỒNG-PRIMARY**, trả lời hai câu khác nhau: A hỏi *kiến trúc có thoát
được module-per-problem không*; B hỏi *bao nhiêu trong số đó đủ bằng chứng để sản
phẩm thật sự dùng được*. Với một hệ hỗ trợ dạy học, "AI viết được chương trình
chạy" mà phần lớn không đủ an toàn cho học sinh xem thì **chưa đủ mạnh**. Nếu
safe-serve thấp, đó là **limitation quan trọng phải báo cáo**, không phải thất
bại phải giấu — và chính khoảng cách giữa hai số mới là chỗ đáng phân tích.

### Hard scope lock

> **Sau khi SEALED benchmark được niêm phong: KHÔNG thêm `MemoryType`, statement
> kind, visual primitive, obligation checker, hay template theo target để cải
> thiện kết quả SEALED. Mọi thay đổi như vậy làm seal hiện tại MẤT HIỆU LỰC.**

## 2. Bằng chứng source đã xác nhận (đọc tận dòng, 2026-08-20)

Ghi cả **symbol** lẫn số dòng — số dòng sẽ trôi, symbol là neo chính.

| # | Symbol | Vị trí | Hành vi xác nhận |
|---|---|---|---|
| E1 | `compile_semantic_program_to_envelope` | `simulation/semantic_program/pipeline_adapter.py:38` | Lấy `frames[0].objects` rồi **vứt toàn bộ khung còn lại**. Nguyên nhân trực tiếp của §0(b) |
| E2 | idem | `pipeline_adapter.py:41` | Phát `"action": "step"` — **không nằm trong** bộ động từ renderer hiểu |
| E3 | `StepAction.action` | `frontend/src/simulations/domains/generic/model.ts:190` | Chỉ hiểu `highlight \| swap \| set_value \| move_pointer`; chuỗi lạ lọt qua `\| string` rồi **không làm gì** |
| E4 | `MAX_REVEAL_STEPS` | `simulation/dsl/validator.py:26,517` · `dsl/manifest.py:162` | `= 20`; `steps[:MAX_REVEAL_STEPS]` **cắt câm**, không báo lỗi. Interpreter chạy `max_steps=300` |
| E5 | `analyze_exposed_operations` | `ai/pipeline.py:149,164` | `requested_operations` **và** `requested_mechanisms` dùng `enum` **dẫn xuất từ catalog** — khoá phạm vi nằm ngay trong response schema của `analyze` |
| E6 | `check_input_sufficiency` | `simulation/sufficiency_gate.py:286` | `requirements_for(target_id)` — **target-bound**, vô nghĩa khi không có target |
| E7 | `represented_operations` | `simulation/completeness_gate.py:233` | Nhận `target_id`; giá trị ngoài registry bị loại |
| E8 | `check_mechanism_consistency_for_target` | `simulation/mechanism_gate.py:77` | Cần một `SimSpec` từ catalog |
| E9 | `check_computation_ownership` | `simulation/computation_gate.py:6` | `ownership not in ("provided","rule_derivable")` → từ chối; `algorithmic` → gap có chủ đích |
| E10 | `_adapt_single_step` | `semantic_program/visual_adapter.py` | **Không có nhánh nào** cho `bar_chart`, dù contract liệt kê nó trong enum `primitive` → object rỗng, lỗi câm |
| E11 | `call_gemini` | `ai/gemini.py:116-118` | `responseMimeType` + `responseSchema` **đã bật** — constrained decoding không phải việc phải làm mới |
| E12 | — | toàn bộ `backend/app/` | `usage_metadata` / `promptTokenCount` — **0 kết quả**. Token chưa từng được đo |
| E13 | `ARTIFACT_DIR` | `scripts/run_live_gemini_semantic_smoke.py:29` | Artifact chứng nhận ghi ra `C:\Users\Bunny\.gemini\antigravity-ide\brain\…` — **ngoài repo**, không tái lập được |
| E14 | `compile_semantic_program_to_envelope` | grep toàn `backend/` | Chỉ script và test gọi — **chưa nối vào pipeline sản xuất** |

## 3. Kiến trúc — route riêng, cổng phân vai lại

### 3.1 Vị trí

Route mới **`generic.semantic_program`**: `simulation_id` riêng, envelope riêng
mang frame timeline, module frontend riêng đăng ký bằng một dòng
`register…Domain()`. **Không** đi qua `dsl/validator.py`.

Lý do không ký sinh vào `generic.rule_scene`: id đó kéo theo trần 20 bước cắt
câm (E4), bộ động từ 4 action (E3), mô hình object của DSL, pattern-reuse khoá
theo `plan["scene_mode"]`, và toàn bộ contract test của nó — **đúng bộ ràng
buộc đã làm hỏng trục hiển thị**.

### 3.2 Cổng: hai loại, không phải một khối

| Cổng | Cần catalog? | Bản chất | Route mới |
|---|---|---|---|
| `scope_gate` | Không | Phán **phạm vi** | **Giữ nguyên** |
| `computation_gate` | Không | Phán **quyền sở hữu kết quả** | → `execution_authority_gate` (3.3) |
| `mechanism_gate` | **Có** (E8) | Kiểm **khớp module** | Không áp — thuộc đường module |
| `completeness_gate` | **Có** (E7) | Kiểm **khớp module** | → `SemanticCoverageGate` C₁a + C₁b (§5.3) |
| `check_input_sufficiency` | **Có** (E6) | Đủ dữ kiện **theo target** | → `semantic_input_grounding_gate` (3.4) |

Hai cổng đầu là **luật của đề tài**, độc lập route. Ba cổng sau kiểm **sự phù
hợp giữa đề và một module cụ thể** — không có module thì chúng không có nghĩa,
nhưng **không được để trống chỗ**: mỗi cái có một bản thay thế không phụ thuộc
catalog.

### 3.3 `execution_authority_gate` — nâng khái niệm, không nới R0

Luật cũ đọc là "`algorithmic` thì từ chối" (E9). Luật **thật** đằng sau nó luôn
là: *kết quả phải có một authority tất định sở hữu*. Khi chưa có interpreter,
hai câu đó trùng nhau nên viết tắt được. Có interpreter rồi thì phải tách:

```
result_ownership = provided       → OK
result_ownership = rule_derivable → cần deterministic rule authority
result_ownership = algorithmic    → cần deterministic program/interpreter authority
không có authority                → capability_gap
```

Giữ nguyên phép giao với `known_gap_roles()`.

**R0 nguyên vẹn**: LLM vẫn không bao giờ là authority. Thay đổi duy nhất là
`SemanticProgramInterpreter` **được công nhận** là authority cho một lớp
algorithmic computation có biên.

### 3.4 `semantic_input_grounding_gate` — hai chiều, và chuỗi provenance HAI ĐOẠN

**Chiều đủ (đề → IR)**: mọi dữ liệu bắt buộc của RequestContract phải xuất hiện
trong IR. Thiếu → `insufficient_specification`. *"Tìm max của dãy sau"* mà không
có dãy → hỏi lại, **không** để LLM tự bịa `[3,7,1]`.

**Chiều nguồn gốc (IR → đề)** không phải một bước mà là **một chuỗi hai đoạn**,
và phải nói rõ vì hai đoạn có mức đảm bảo **khác hẳn nhau**:

```
Original input
     ↓  P1
RequestContract input fact
     ↓  P2
SemanticProgram input reference
```

**P2 (IR → RequestContract) — kiểm tất định, mạnh.** Mỗi literal mang nghĩa
input phải **tham chiếu đúng mục dữ liệu nào** trong RequestContract; cổng kiểm
mục đó tồn tại và giá trị khớp. Ghim *cái nào*, không phải *có tồn tại đâu đó* —
khớp theo giá trị đơn thuần dễ trùng ngẫu nhiên. Đề *"tìm max của 4, 7, 2"* mà
IR khai `a = [4,7,2,9]` → **fail**, vì `9` không tham chiếu được.

**P1 (RequestContract → đề gốc) — chỉ mạnh nếu có bằng chứng nguồn.** Nghĩa là
`source_span`, vị trí nguồn có cấu trúc, hoặc bằng chứng từ extractor tất định.
Không có thứ đó thì P1 là **khẳng định của `analyze`**, không phải sự kiện kiểm
được.

> **Giới hạn phải khai, không được lấp liếm.** Nếu wave này chưa làm full
> source-span thì P1 còn hở: `analyze` bịa `[4,7,2,9]` → RequestContract chứa
> `9` → IR tham chiếu đúng mục chứa `9` → **P2 vẫn PASS**. Do đó **không được
> tuyên bố `semantic_input_grounding_gate` đã diệt mọi hallucination của
> `analyze`**. Nó là điều kiện **cần, chưa đủ**: nó đóng hoàn toàn đoạn P2, và
> thu hẹp — chứ không đóng — đoạn P1.

### 3.5 Taxonomy: tách đôi

Tách **Catalog operation taxonomy** (dẫn xuất từ 24 target, phục vụ đường
module) khỏi **Semantic obligation taxonomy** (§5.1). Trên route semantic,
`analyze` **không** dùng enum dẫn xuất catalog (E5).

### 3.6 Kết cục

Giữ nguyên bốn `failure_category` đang chạy (`capability_gap`,
`insufficient_specification`, `semantic_incomplete`, `synthesis_exhausted`),
**thêm một cái thứ năm**:

| `failure_category` | Câu hỏi nó trả lời |
|---|---|
| `capability_gap` | *"Máy có thực thi được không?"* → **KHÔNG** |
| **`verification_gap`** (mới) | *"Máy thực thi được, nhưng có đủ bằng chứng để phát canonical cho học sinh không?"* → **CHƯA** |

Gộp hai cái này làm một là lẫn *"hệ không làm được"* với *"hệ làm được nhưng
chưa chứng minh được"* — hai mệnh đề khác nhau về nhận thức luận, và **chính sự
phân biệt đó là đóng góp của luận văn**. Nó cũng tách được hai chỉ số phải báo
cáo riêng:

```
Generative executability rate   ≠   Safe serve rate
```

`error_code` cho những cách hỏng chỉ route này mới có:

| Mã | Nghĩa |
|---|---|
| `SEMANTIC_PROGRAM_INVALID` | Validator tĩnh từ chối |
| `INTERPRETER_BUDGET_EXHAUSTED` | Hết **execution budget** — phải báo, **không được cắt câm** |
| `REQUESTED_OPERATION_UNCOVERED` | C₁a: nghĩa vụ không có witness hợp lệ về cấu trúc |
| `OBLIGATION_WITNESS_UNREALIZED` | C₁b: witness hợp lệ trên giấy nhưng **không được hiện thực hoá** trong lượt chạy (dead branch, không đạt tới) |
| `SEMANTIC_VERIFICATION_UNAVAILABLE` | Mức yếu — chạy được nhưng **chưa có checker độc lập**; `failure_category = verification_gap` (§5.4) |
| `POSTCONDITION_VIOLATED` | **Hậu điều kiện server-owned / executable bị vi phạm.** KHÔNG diễn giải là "chứng minh AI hiểu sai đề" — hậu điều kiện do LLM đề xuất mà vi phạm thì chỉ chứng minh chương trình **tự mâu thuẫn** |
| `ORACLE_SEMANTIC_MISMATCH` | Lệch oracle. **Telemetry-only, không bao giờ lên UI.** Exact-trace mismatch là **subtype** |

### 3.7 Shadow — module phục vụ, đường sinh chạy bóng

Đề rơi vào 24 target: **module vẫn render cho học sinh như hiện nay**; đường
sinh chạy song song, so với module, ghi kết quả đối chứng. Đề ngoài 24 target:
đường sinh phục vụ trực tiếp (trong giới hạn §5.4).

Vì sao không tắt module ngay: (1) không làm thụt lùi sản phẩm đã chứng nhận;
(2) oracle **sống** — mỗi lượt dùng thật là một điểm dữ liệu, thay vì một lần
chạy 24 case rồi thôi; (3) số cho luận văn tự lớn lên và không do mình tự chọn
tập test.

Shadow chạy **theo tỉ lệ mẫu, có cờ tắt** — không bắt buộc mọi lượt (§6).
Chuyển công tắc sang "tắt module" là quyết định **sau**, khi có số.

> **Shadow là SUPPORTING, không phải bằng chứng trung tâm.** Khi đã có sealed
> benchmark (§7.1) thì claim A đứng được mà không cần shadow. Hạ ưu tiên —
> *nếu còn thời gian* (§9, §10.1).

## 4. Trục hiển thị — chương trình → hoạt hình

Đây là trục **kiểm chứng được tất định và toàn diện trên bounded contract** —
không phải "chứng minh tuyệt đối". Cả hai đầu đều tất định và không gian trạng
thái có biên, nên bất biến 4.2 kiểm được **cạn** trong phạm vi hợp đồng đó; nói
quá lên thành "tuyệt đối" là tuyên bố vượt khỏi thứ đo được.

```
Interpreter ──trace──► VisualTraceAdapter ──frames (1:1)──► PresentationPacer ──bước xem──► envelope
     ▲                         ▲                                    ▲
 execution budget         bất biến 4.2                     presentation budget
```

### 4.1 Envelope mang frame timeline, renderer câm

Envelope mang **toàn bộ chuỗi khung**. Renderer chỉ **đọc** khung thứ `k`:
không đánh giá lại biểu thức, không suy diễn trạng thái ngữ nghĩa.

**Nội suy thị giác được phép.** Renderer tự do làm chuyển động mượt giữa hai
khung — trượt con trỏ, đổi màu dần, chuyển vị trí phần tử. Ranh giới là: **pixel
được nội suy, trạng thái ngữ nghĩa thì không**. Mọi giá trị hiển thị (nội dung ô,
giá trị biến, chiều cao cột, đỉnh ngăn xếp) phải đọc từ một khung có thật; không
được sinh ra một trạng thái trung gian nào không tồn tại trong trace.

**Snapshot đầy đủ mỗi khung, không dùng delta.** Đắt hơn về byte, đổi lại
renderer không cần logic replay — mà logic replay chính là chỗ trục hiển thị sẽ
lại lệch khỏi trục ngữ nghĩa.

> **Kích thước payload chưa đo.** Không có ước lượng nào trong spec này. Đo thật
> khi có timeline đầu tiên (§10.1 bước 3), và ghi số vào artifact. Nếu payload
> thành vấn đề thì cân nhắc delta **lúc đó**, có số trên tay — không quyết trước
> bằng cảm tính theo hướng nào.

### 4.2 Bất biến khoá trục hiển thị

> Với mọi `k`: khung hình thứ `k` **suy được hoàn toàn** từ
> `trace[k].memory_snapshot` qua `visual_bindings`, không phụ thuộc gì khác.

Test thuần Python, không cần trình duyệt, mili-giây. **Đỏ ngay trước E1.**

### 4.3 Hai ngân sách, tách hẳn

Gộp "chạy được bao xa" với "xem được bao nhiêu" vào một con số chính là nguyên
nhân gốc của E4.

- **Execution budget** — số bước máy interpreter được chạy. Chạm trần →
  `INTERPRETER_BUDGET_EXHAUSTED`, **báo ra**.
- **Presentation budget** — số bước xem của người học. Chạm trần **không phải
  lỗi**: `PresentationPacer` hạ mức chi tiết (mịn nhất: mỗi bước máy một bước
  xem → thô hơn: mỗi vòng lặp một bước xem) cho tới khi vừa. Chỉ khi mức thô
  nhất còn tràn mới báo. **Luôn khai đang xem ở mức gộp nào**, không im lặng.

### 4.4 `PresentationPacer` — gộp nằm NGOÀI adapter

Gộp **không** được đặt trong `VisualTraceAdapter`: adapter giữ song ánh
`frame k ⇔ trace[k]` thì 4.2 mới là **định lý**.

Bất biến của pacer (yếu hơn, vẫn kiểm được): **mỗi bước xem là một đoạn liên
tiếp các khung máy; các đoạn phân hoạch đầy đủ, không chồng lấn; không sinh
khung mới.** Khung máy được *gộp*, không bị *bỏ*.

### 4.5 Neo không phân giải được → fail-closed

Con trỏ `i` đè chữ trong §0(b) do neo vào container rỗng.

Luật **không phải** "bỏ con trỏ rồi vẫn render phần còn lại" — đó là hạ cấp âm
thầm, đúng loại lỗi §0(b). Một `visual_binding` **bắt buộc** mà không phân giải
được là **hỏng hợp đồng**: adapter/validation **thất bại**, và **không phát
canonical envelope**. Học sinh thà không thấy gì còn hơn thấy một cảnh thiếu
thành phần mà không ai nói cho biết là đang thiếu.

Bất biến kèm theo: **mọi binding bắt buộc phải phân giải được; không có đường
render một phần.**

### 4.6 `bar_chart` — vá kèm cổng chống tái phát

Thêm nhánh `bar_chart` vào `_adapt_single_step` (E10), **kèm test đối sánh
enum ↔ adapter**: mọi giá trị trong `VisualContainerBinding.primitive` bắt buộc
có nhánh xử lý, thiếu là ĐỎ. Vá một nhánh thì primitive kế tiếp lại rơi y hệt.

## 5. Tầng đối chứng

### 5.1 Obligation taxonomy khoá vào hệ kiểu của IR

Nghĩa vụ ngữ nghĩa là **vị từ thực thi được trên cấu trúc dữ liệu**, không phải
trên mục tiêu chương trình:

| Nghĩa vụ | Kiểm trên |
|---|---|
| `extremum(container, cmp)` | array, matrix |
| `count_matching(container, pred)` | array, set, map |
| `ordering(container, cmp)` | array |
| `membership(container, item)` | set, map, array |
| `total_mapping(map, domain)` | map |
| `reachability(graph, src, set)` | graph |
| `structural_traversal(tree, order)` | tree_node |

**Nguồn của taxonomy là ba thứ, không phải một.** Chỉ dựa vào `MemoryType` là
chưa đủ — kiểu dữ liệu nói được *cấu trúc*, không nói được *quan hệ* đang bị
ràng buộc:

```
IR type semantics                     (array/map/set/graph/tree… — cấu trúc)
+ expression / statement semantics    (so sánh, tích luỹ, duyệt, biến đổi)
+ reusable server-owned checker       (phải có bộ kiểm tất định do server sở hữu)
```

Điều kiện thứ ba là điều kiện **chặn**: một nghĩa vụ không có checker
server-owned rõ ràng thì **không được vào bảng**, dù nó có gọi tên đẹp tới đâu.

Vì sao thoát khoá catalog — phát biểu đúng mức, không nói quá:

> **Thêm đề mới không mặc nhiên làm taxonomy tăng.** Taxonomy chỉ mở khi xuất
> hiện một **lớp quan hệ ngữ nghĩa tái sử dụng mới** có checker server-owned rõ
> ràng. Điều kiện mở rộng là "lớp quan hệ này tái dùng được và kiểm được", không
> phải "có đề mới cần nó" — nếu lấy đề làm cớ thì taxonomy trôi thành catalog
> thứ hai, đúng cái vừa gỡ.

Bảng trên là **hạt giống**, không phải danh sách đóng vĩnh viễn.

**Đóng băng trước SEALED.** Tập checker được chọn từ phân tích **DEV** (§7.3),
rồi đóng băng. Sau khi seal, **không thêm checker để cứu từng held-out case** —
hard scope lock §1.1.

### 5.2 RequestContract — nghĩa vụ do `analyze` khai, server đóng băng

`analyze` trích nghĩa vụ từ đề; **server đóng băng** thành `RequestContract`.
`stage_semantic_program` **không có quyền khai lại hay sửa** nghĩa vụ.

Đây là R0 áp cho chính khâu chấm điểm: **tiêu chuẩn chấm được cố định trước khi
chương trình được viết ra**, nên chương trình không thể nới tiêu chuẩn cho vừa
nó. Nếu để cùng một lượt sinh ra cả chương trình lẫn tiêu chuẩn chấm nó thì việc
hai thứ khớp nhau không chứng minh được điều gì.

> **Đây là separation of responsibility, KHÔNG phải independent oracle.** Đóng
> băng nghĩa vụ chặn được việc chương trình *tự sửa đề bài cho vừa mình*. Nó
> **không** chặn được việc **cùng một model hiểu sai đề một cách nhất quán** ở cả
> hai lượt — nghĩa vụ sai và chương trình khớp với nghĩa vụ sai đó vẫn qua hết
> mọi cổng. Oracle độc lập thật nằm ở §3.7 và §7.1, không nằm ở đây.

### 5.3 C₁a, C₁b, C₂ — ba câu hỏi khác nhau

**C₁a — structural coverage, TRƯỚC execution.** *Mỗi nghĩa vụ có witness hợp lệ
về cấu trúc không?*

```
- mỗi obligation có witness
- witness ref tồn tại
- type tương thích
- witness không rỗng / không dangling
- program có producer hợp lệ cho witness
```

Thiếu → `REQUESTED_OPERATION_UNCOVERED`. Đây là chỗ "đề hỏi cả max lẫn min mà
chỉ làm max" bị chặn.

**C₁b — realized coverage, SAU execution.** *Witness đó có thật sự được hiện
thực hoá trong lượt chạy này không?*

```
- witness thực sự được tạo / đạt tới trong execution này
- không chỉ tồn tại trên giấy
- không nằm trong dead branch không bao giờ chạy
- output/return/state cần thiết thực sự xuất hiện trong trace/result
```

Không đạt → `OBLIGATION_WITNESS_UNREALIZED`.

> Ví dụ tách được hai tầng: `O1 = MIN_OF(a)`, witness `min_value`. Biến khai
> đúng kiểu, có câu `assign min_value = …` → **C₁a PASS**. Nhưng câu `assign` đó
> nằm trong nhánh không bao giờ được thực thi → **C₁b FAIL**. C₁a một mình không
> phân biệt được "có viết" với "có chạy".

**C₂ — hậu điều kiện, SAU execution**, chỉ trên nghĩa vụ đã qua C₁a **và** C₁b:
*chạy xong có thoả tính chất không?* Vi phạm → `POSTCONDITION_VIOLATED`.

Câu một dòng cho cả ba: **C₁a kiểm nghĩa vụ có witness hợp lệ về cấu trúc; C₁b
kiểm witness đó đã thực sự được hiện thực hoá trong execution trace; C₂ kiểm
tính chất của kết quả.**

Không cái nào thay cái nào. C₂ **không** là bản thay thế của `completeness_gate`
— C₁a/C₁b mới là.

### 5.4 Hai mức đảm bảo — ranh giới khoa học, khai tường minh

- **Mức mạnh** — mục tiêu đề diễn đạt được bằng vị từ ở 5.1 → coverage gate xác
  nhận, engine kiểm tất định.
- **Mức yếu** — IR thực thi được nhưng mục tiêu **chưa có checker độc lập** →
  postcondition của LLM chỉ tính là **self-consistency**; correctness phải đánh
  giá bằng oracle/benchmark ngoài.

**Quyết định sản phẩm cho bản luận văn: mức yếu KHÔNG phục vụ học sinh như
canonical simulation.** Chỉ chạy ở evaluation / shadow / preview có chủ đích.
Đề rơi vào mức yếu trên đường phục vụ → **`verification_gap`** /
`SEMANTIC_VERIFICATION_UNAVAILABLE` — **không phải** `capability_gap`. Hệ **làm
được**; thứ còn thiếu là bằng chứng, và nói nhầm thành "không làm được" là báo
cáo sai năng lực của chính mình (§3.6).

Đây không phải nợ kỹ thuật. Không thể đồng thời có *bài hoàn toàn mới, ngữ
nghĩa hoàn toàn mới* và *oracle tổng quát chứng minh kết quả*. Ranh giới này là
kết luận, và nên được viết vào luận văn như kết luận.

### 5.5 Oracle so ngữ nghĩa; exact trace là một trường hợp

- **Đề có ép thủ tục** (`prescribed_procedure` ≠ null): đề đang dạy *chính thủ
  tục đó* → so **canonical semantic / mechanism events** (so sánh nào, hoán đổi
  nào, thăm đỉnh theo thứ tự nào), **không** mặc định so raw trace 1:1. Hai cài
  đặt cùng một thủ tục có thể khác nhau về số bước máy mà vẫn **cùng một cơ
  chế** — bắt trùng từng bước thô là bắt trùng chi tiết cài đặt, không phải bắt
  trùng thủ tục.
  **Raw-step equality chỉ dùng khi hợp đồng thật sự quy định một canonical
  sequence.** Lệch → subtype exact-trace của `ORACLE_SEMANTIC_MISMATCH`.
- **Đề không ép thủ tục**: so **tương đương ngữ nghĩa** — kết quả cuối + tập
  nghĩa vụ thoả. Lệch → `ORACLE_SEMANTIC_MISMATCH`.

Cả hai **telemetry-only**.

## 6. Token

### 6.1 Điều kiện tiên quyết — đo trước mọi tối ưu (§10.1 bước 5)

Ghi **đủ** token metadata **theo từng stage**: `promptTokenCount`,
`candidatesTokenCount`, `cachedContentTokenCount`, `totalTokenCount`, và
`thoughtsTokenCount` nếu model trả về. Kết vào artifact trong `docs/evaluation/`.
Hiện **chưa ghi ở đâu cả** (E12) — chưa có baseline thì mọi tối ưu là cảm tính,
và cũng không có gì báo cáo giáo viên hướng dẫn.

### 6.2 Kinh tế route (chờ số thật xác nhận)

| | Generic hiện tại | `generic.semantic_program` |
|---|---|---|
| Lượt LLM | analyze + classify (+1 reclassify) + simulate **≤3 lượt** | analyze + classify + program **1 lượt** |
| Chi phí theo số **bước runtime** | **tuyến tính — chỉ trên đường `step_sequence`** (LLM viết ra từng bước). Các generic case khác (cảnh tĩnh, `rules`, `interactions`) **không** phát token theo bước | **không tiêu thêm token LLM** — interpreter sinh bước. ⚠️ **Không** đồng nghĩa "tổng token độc lập với độ khó bài": bài phức tạp hơn thì **IR dài hơn**, và IR do LLM viết |
| Shadow | — | +1 lượt, theo tỉ lệ mẫu, có cờ tắt |

### 6.3 Bốn đòn giảm, xếp theo tỉ lệ ăn/công

1. **Gỡ luật đặt sai tầng.** Constrained decoding đã cưỡng chế cấu trúc và enum
   (E11), nên phần phình trong `analyze.md` là **hướng dẫn chọn giá trị nào
   trong enum**. Phần lớn không phải việc của LLM: phân biệt
   `binary_positional_weights` / `non_binary_base` / `character_code_mapping` là
   **hàm tất định của kiểu dữ liệu đầu vào và cơ số được hỏi** — server tự quyết
   được, chính xác hơn, 0 token. Prompt ngắn lại vĩnh viễn **và** độ chính xác
   tăng.
2. **Ít sửa prompt ⇒ ít xoá cache.** Mỗi lần sửa `skills/*.md` buộc bump
   `CACHE_VERSION`, **xoá sạch exact-cache**; chi phí thật của một bản vá prompt
   gồm cả đợt gọi lại toàn bộ. Chuyển luật sang mã tất định **có thể tránh được
   bump** — nhưng chỉ khi thay đổi đó **không làm đổi hợp đồng analyze/classify
   đang được cache**. Luật tất định nào đổi chính đầu ra được cache thì vẫn phải
   bump như thường. Không phải mọi sửa tất định đều miễn phí về cache.
3. **Context caching** — implicit đã bật mặc định trên 2.5+; explicit chiết khấu
   tới 90% phần cache nhưng **có ngưỡng token tối thiểu và phí lưu theo giờ**.
   Prompt hiện vài nghìn token nên **chưa chắc bõ**. Quyết **sau** 6.1.
4. **Độ dài mô phỏng miễn phí** (6.2).

### 6.4 Cổng token — hard-fail chỉ ở tầng tĩnh

- **Offline / static guard → hard-fail build**: kích thước prompt (byte, và
  token đếm offline), kích thước schema, số lượt LLM mỗi route. Tất định, không
  nhiễu, không tốn call.
- **Live token regression → BÁO CÁO, không làm gãy CI mặc định.** Số live nhiễu
  và tốn tiền; để nó gác cổng mặc định là vừa đắt vừa hay đỏ oan.

### 6.5 Claim D tách làm HAI — hai mức đảm bảo khác nhau

Gộp hai claim này làm một sẽ kéo cái đúng-theo-cấu-tạo xuống mức "chưa chứng
minh", và mời đúng câu hỏi *"rẻ hơn ở đâu, trên tập nào?"*.

**D1 — claim CẤU TRÚC, đúng theo cấu tạo, không cần đo:**

> Sau khi Semantic IR đã được sinh, **số bước runtime do interpreter tạo thêm
> không tiêu thêm token LLM**.

Phát biểu **đúng chừng đó, không hơn**. Cụ thể **không** được nói "tổng token độc
lập với độ dài mô phỏng" — bài phức tạp hơn vẫn có IR dài hơn, mà IR do LLM viết.

**D2 — claim THỰC NGHIỆM, cần tập so khớp:**

> Đo **chỉ trên matched subset** — những bài **cả hai route đều phục vụ thành
> công**. Báo **token theo stage** và **token trên mỗi mô phỏng giao thành công**.
> **Chi phí shadow báo riêng**, không trộn vào.

So tổng token của hai route trên hai population khác nhau là apples-to-oranges:
route mới nhận cả những bài đường cũ từ chối thẳng.

## 7. Bằng chứng — tầng nào bắt lỗi gì

| Tầng | Trạng thái | Bắt được |
|---|---|---|
| L1 constrained decoding | **đã có** (E11) | Loại **gần hết** lỗi cấu trúc/enum. **KHÔNG phải đảm bảo tuyệt đối** — có ghi nhận Flash rơi vào vòng lặp lặp token trong literal số cho tới `MAX_TOKENS`, trả JSON không parse được. Vẫn cần timeout + thử lại + xử lý lỗi parse |
| L2 validator tĩnh | **đã có** | Biến chưa khai, binding không phân giải, quá giới hạn |
| **L3 bất biến** | **mới — ưu tiên 1** | Bất biến 4.2 · phân hoạch của pacer (4.4) · enum↔adapter đủ nhánh (4.6) · binding bắt buộc phân giải được (4.5). Thuần Python, **0 call** |
| **L4 golden + oracle shadow** | mới — **SUPPORTING** | Hồi quy chất lượng sinh; tụt điểm là gãy build (phần offline). Oracle shadow **không** là bằng chứng trung tâm khi đã có sealed benchmark → hạ ưu tiên, *nếu còn thời gian* |
| **L5a visual regression (nhỏ, đại diện)** | mới — **BẮT BUỘC** | Chữ đè, clipping, con trỏ chui vào label, vỡ bố cục responsive. **L3 chứng minh semantic visual fidelity; nó KHÔNG chứng minh màn hình nhìn được.** Ràng buộc "hiển thị chuẩn xác" của giáo viên hướng dẫn đòi đúng tầng này. `toHaveScreenshot()`; Playwright **đã có** |
| **L5b visual regression (toàn danh mục, đa trình duyệt)** | mới — **tuỳ chọn** | Phủ rộng; ngoài phạm vi bắt buộc của khoá luận |

L3 làm trước tiên: đỏ ngay trước E1 mà không tốn gì.

L1–L3 + L5 thuộc T0–T3 offline (`docs/TEST_TIERS.md`). Phần đối chứng **live**
của L4 là **opt-in có ngân sách**, không nằm trong bốn tầng.

### 7.1 Held-out no-module benchmark — bằng chứng TRỰC TIẾP cho claim trung tâm

Đối chứng với 24 module (§3.7) **về mặt cấu tạo chỉ đo được trong catalog**. Nó
không đo được đúng thứ đang tuyên bố: *nhận được bài không có module*. Phải có
một bộ đề riêng, và nó là bằng chứng trực tiếp cho claim "không cần
module-per-problem".

**Chia đôi dataset:**

```
DEV                     → được nhìn, dùng sửa schema/prompt
SEALED HELD-OUT TEST    → khoá fingerprint
                        → KHÔNG dùng để tuning
                        → chỉ mở ở milestone evaluation
```

**Ground truth không nhất thiết phải người viết tay từng case.** Chấp nhận ba
nguồn:

- đáp án do người soạn;
- **reference solver độc lập**;
- **property / invariant oracle**.

Ràng buộc duy nhất, và là ràng buộc cứng: **không được dùng chính bản
`SemanticProgramInterpreter` đang bị kiểm để tạo ground truth.** Lấy hệ đang
kiểm làm thước đo chính nó thì mọi con số thu được đều rỗng.

**Metadata guard cho mỗi case held-out** — kiểm được, không phải lời hứa:

```
no_specialized_module = true     (không có module chuyên biệt phục vụ bài này)
no_target_template   = true      (không có template dựng sẵn theo bài)
not_prompt_example   = true      (không xuất hiện trong prompt/skill nào)
expressible_in_ir    = true      (kết quả AUDIT TRƯỚC KHI SEAL theo rubric §7.2 —
                                  KHÔNG phải bộ lọc áp sau khi thấy hệ chạy hỏng)
```

### 7.2 Eligibility rubric — định nghĩa population TRƯỚC, độc lập với cài đặt

Rubric này **chốt trước khi dựng benchmark** và **không tham chiếu tới IR đang
làm**. Ai đọc rubric cũng phân loại được một đề là in-scope hay không **mà không
cần chạy hệ** — đó là điều kiện để population thôi tự tham chiếu.

Một bài **in-scope** khi thoả **tất cả**:

1. **Rời rạc, đầu vào hữu hạn.**
2. **Có thủ tục tất định**, execution **hữu hạn / có biên**.
3. **Trạng thái** gồm scalar và các cấu trúc dữ liệu rời rạc: dãy/chuỗi, stack,
   queue, set, map, matrix, tree, graph.
4. **Thao tác** thuộc các nhóm: gán · so sánh · truy cập · cập nhật · duyệt ·
   push/pop · enqueue/dequeue.
5. **Không** phụ thuộc solver liên tục, môi trường bên ngoài, hay miền
   phi-thuật-toán.

Bài không thoả rubric → **ngoài population**, không đưa vào benchmark. Bài thoả
rubric nhưng IR hiện tại không diễn đạt được → **vẫn ở trong benchmark**, và kết
quả là `capability_gap` — đó là một **phát hiện phải báo cáo**, không phải sự cố
cần vá.

### 7.3 Freeze protocol — cái gì đóng băng, đóng băng lúc nào

**Đóng băng TRƯỚC khi seal** (ghi vào artifact, không sửa về sau):

```
- eligibility rubric (§7.2)
- N và cách lấy mẫu
- primary metrics (A và B — đồng-primary)
- assurance policy (thanh STRONG/WEAK cố định)
- ground-truth procedure
- cách tính refusal / success
- các trường hợp bị loại khỏi thống kê
- obligation taxonomy (chọn từ DEV — xem dưới)
```

**Không** đặt một "pass mark" tuỳ tiện kiểu *"≥80% thì luận văn thành công"* khi
chưa có cơ sở nào để chọn con số đó. Luận văn **báo kết quả như nó là**. Thứ phải
đóng băng là **cách đo**, không phải mức điểm mong muốn.

Với **release cho học sinh** thì tiêu chuẩn khác hẳn: canonical case **biết là
sai** thì **fail release**, và **tuyệt đối không hạ thanh assurance để tỉ lệ đẹp
hơn**.

**Chống rủi ro safe-serve ≈ 0** — làm trên **DEV, trước khi seal**: thống kê các
**lớp nghĩa vụ thực tế xuất hiện** trong bài thuật toán THPT, chọn một tập
checker nhỏ **đại diện** cho các lớp đó, rồi **đóng băng taxonomy trước SEALED**.
**Không** thêm checker để cứu từng held-out case.

### 7.4 Luật con dấu — DEV đổi hệ, SEALED đổi kết luận

> **DEV được phép làm thay đổi IR. SEALED chỉ được phép làm thay đổi kết luận
> của luận văn.**

Hệ quả, không có ngoại lệ:

- Case SEALED ngoài năng lực → ghi `capability_gap`. **Không** mở
  primitive/type/checker để cứu nó (hard scope lock §1.1).
- Nếu vì lý do nghiên cứu **bắt buộc** phải sửa hệ sau khi đã mở seal, thì dataset
  đó **trở thành DEV/history**, và phải **tạo một SEALED mới**.
- Mọi thay đổi IR đều phải **dẫn nguồn từ DEV**, không bao giờ từ SEALED.

**Artifact phải về repo.** Bằng chứng chứng nhận hiện nằm ngoài repo (E13) —
chuyển về `docs/evaluation/`, kể cả lượt thất bại. Theo luật dự án, không bằng
chứng tái lập được thì không được ghi DONE.

## 8. Scope rebaseline — BƯỚC 0, trước mọi việc khác

Đây **không** phải việc dọn dẹp cuối wave. Nó là **bước 0** (§10): chừng nào
ledger còn xếp hướng này là ngoài mục tiêu thì mọi phiên agent sau — kể cả
phiên đang làm đúng spec này — đều có nghĩa vụ **tự dừng** theo `RULES.md §3d`.
Làm code trước rồi sửa tài liệu sau là tự đặt bẫy cho chính mình.

1. **`docs/STATUS_LEDGER.md §0`** — khoá phạm vi hiện liệt "sinh mô phỏng tự
   động" ngoài mục tiêu. Cập nhật để phản ánh chỉ đạo mới, **kèm ngày và nguồn
   (giáo viên hướng dẫn)**.
2. **`docs/RULES.md`** — luật cứng đổi, phải ghi vào nơi có thẩm quyền:
   - **R0 được làm sắc, không nới**: kết quả phải có **authority tất định** sở
     hữu; `SemanticProgramInterpreter` được công nhận là một authority. LLM vẫn
     không bao giờ là authority (§3.3).
   - **Cấm cắt câm**: chạm trần ngân sách phải **báo**, không được lặng lẽ giao
     một phần (§4.3) — luật này sinh ra từ E4.
   - **Nghĩa vụ đóng băng trước khi sinh chương trình** (§5.2).
   - Giữ `RULES.md` đúng vai con trỏ — `rules-hygiene.test.ts` đang khoá file
     này, thêm kiến trúc dài dòng vào là ĐỎ.
3. **`docs/ARCHITECTURE_MAP.md`** — đây **là** thay đổi kiến trúc thật, đúng
   loại mà file này tồn tại để ghi:
   - **Bảng sở hữu** thêm hàng: interpreter sở hữu trace · adapter sở hữu frame
     · pacer sở hữu bước xem · renderer vẫn chỉ ĐỌC.
   - **Hướng phụ thuộc**: `contract ← validator ← interpreter ← adapter ← pacer
     ← envelope`, không được đảo.
   - **Bất biến đánh số mới**, mỗi cái kèm nơi thực thi và test khoá: bất biến
     4.2 (khung ⇔ trạng thái) · 4.4 (phân hoạch của pacer) · 4.6 (enum ↔ adapter)
     · 4.5 (binding bắt buộc phân giải được — fail-closed).
   - **Anti-pattern** thêm mục: "cầu nối giữ khung đầu rồi phát narration chạy"
     — đã ship bug thật, §0(b).
4. **`docs/CURRENT_STATE.md`** — thêm route mới vào bảng danh tính khi wave đóng.
5. **`docs/CODE_INDEX.md`** — mọi module/symbol mới (khoá bởi
   `code-index-sync.test.ts`).
6. **`docs/CORRECTNESS.md`** — ghi 5.4 (hai mức đảm bảo) vào trục canonical.
7. **Tên đề tài** chốt 18/08 **giữ nguyên** (đã duyệt): "kết hợp LLM phân tích
   bài toán" bao được hướng này.

## 9. Không thuộc spec này

- Tắt hẳn 24 module chuyên biệt — quyết định **sau**, khi có số đối chứng (3.7).
- Mở rộng IR sang miền phi-thuật-toán (HTML/CSS, đóng gói giao thức, bảng CSDL).
- Pattern-reuse cho route mới.
- Explicit context caching — chờ số ở §6.1 (xem §6.3 mục 3).
- Mức yếu phục vụ học sinh — đã chốt **không**, trong bản luận văn (5.4).
- **Oracle shadow** (3.7, 5.5) — **SUPPORTING**, *nếu còn thời gian*. Không phải
  bằng chứng trung tâm khi đã có sealed benchmark.
- **L5b** visual regression toàn danh mục / đa trình duyệt — tuỳ chọn (§7).

## 10. Thứ tự thực thi

### 10.0 Ba pha của con dấu — SEAL SỚM, MỞ MUỘN

Đây là chỗ bản trước **sai**: nó vừa nói "niêm phong trước khi tinh chỉnh
prompt/schema", vừa đặt việc dựng dataset ở bước 9. Hai câu đó chỉ cùng đúng nếu
trước bước 9 chưa ai động vào semantic prompt/schema — mà thực tế
`stage_semantic_program` chắc chắn phải làm trước evaluation. Nên tách hẳn:

```
EARLY   ── dựng DEV
        ── dựng SEALED
        ── đóng băng eligibility rubric (§7.2) + freeze protocol (§7.3)
        ── khoá fingerprint
        ── KHÔNG mở SEALED

DEVELOP ── CHỈ dùng DEV để chỉnh IR / schema / prompt

LATE    ── mở SEALED ĐÚNG MỘT LẦN, ở milestone evaluation
```

**"Seal dataset" thuộc pha EARLY; "open/evaluate seal" mới ở cuối.** Trộn hai
việc này là mất tính held-out ngay từ đầu.

### 10.1 Thứ tự bước

| # | Việc | Pha |
|---|---|---|
| **0** | **Scope rebaseline** (§8.1–8.3): ledger + `RULES.md` + `ARCHITECTURE_MAP.md`. Không xong thì mọi phiên agent sau có nghĩa vụ tự dừng vì OUT_OF_SCOPE | — |
| **1** | **Dựng DEV + SEALED, đóng băng rubric/protocol/fingerprint** (§7.2–7.4). **Không mở SEALED** | **EARLY** |
| **2** | **L3 bất biến 4.2** trên mã hiện tại → **đỏ**, chứng minh E1 là thật | DEVELOP |
| **3** | Sửa E1/E2 + frame timeline (4.1) · `PresentationPacer` (4.4) · hai ngân sách (4.3) · `bar_chart` + cổng enum (4.6) · binding fail-closed (4.5) → **L3 xanh**. Đo kích thước payload thật (4.1) | DEVELOP |
| **4** | **`stage_semantic_program` — lõi của Mission**: `SemanticProgram schema → LLM synthesis → static validator → interpreter wiring → VisualTraceAdapter` | DEVELOP |
| **5** | Telemetry token (6.1) + static guard (6.4) → có baseline | DEVELOP |
| **6** | `RequestContract` (5.2) + obligation taxonomy **đóng băng từ DEV** (5.1, 7.3) + **C₁a** (5.3) | DEVELOP |
| **7** | Tách `analyze` khỏi enum catalog (E5) + `semantic_input_grounding_gate` với **P2 tất định** (3.4); khai giới hạn P1 vào tài liệu ngay tại bước này | DEVELOP |
| **8** | `execution_authority_gate` (3.3) + `verification_gap` / `SEMANTIC_VERIFICATION_UNAVAILABLE` (3.6, 5.4) + **đăng ký route nội bộ/shadow** (3.1) — xem 10.2 | DEVELOP |
| **9** | **C₁b realized coverage** (5.3) — cần trace, nên sau bước 3 và 6 | DEVELOP |
| **10** | **C₂** (5.3) | DEVELOP |
| **11** | **L5a** visual regression nhỏ, đại diện (§7) — **bắt buộc** | DEVELOP |
| **12** | **Mở SEALED đúng một lần**, chạy evaluation, báo A và B (đồng-primary) + D1/D2 (6.5) | **LATE** |
| **13** | Artifact về repo (E13) + phần còn lại của §8 (8.4–8.6) | LATE |
| — | *Oracle shadow · golden L4 · L5b — SUPPORTING, nếu còn thời gian* (§9) | — |

Bước 2–3 đã trả xong toàn bộ §0(b) và chứng minh được cách tiếp cận chạy được,
**trước khi tiêu bất kỳ call thật nào**.

### 10.2 Serving gate — đăng ký route ≠ bật cho học sinh

> **Đăng ký route KHÔNG đồng nghĩa bật serving cho học sinh.**

Bước 8 chỉ được đăng ký route ở chế độ **nội bộ / shadow, sau feature flag**.
Learner-facing chỉ được bật khi **toàn bộ chuỗi assurance đã tồn tại**:

```
RequestContract
  → grounding P2
  → C₁a
  → SemanticProgram validator
  → interpreter
  → C₁b
  → C₂
  → STRONG assurance
```

Vì bước 8 đứng **trước** C₁b (bước 9) và C₂ (bước 10), execution plan **phải ghi
rõ feature flag / shadow-only** cho tới khi bước 10 xong. Bật serving sớm là phát
canonical simulation cho học sinh trong khi hai tầng kiểm cuối chưa tồn tại —
đúng thứ §5.4 dựng lên để chặn.
