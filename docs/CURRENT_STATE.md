# CURRENT_STATE.md — Trạng thái hiện tại

Cập nhật **sau mỗi milestone**. Chỉ ghi việc **đã thật sự xong** (có commit +
test). Không ghi việc đang định làm vào mục "đã xong".

> ## ⛳ DANH TÍNH KHO MÃ — ĐỌC TRƯỚC MỌI THAY ĐỔI (2026-08-11)
>
> Ba hàng số sống dưới đây **có sync-lock**: `backend/tests/test_current_state_identity.py`
> dẫn xuất chúng từ nguồn (`app.main.CACHE_VERSION`, `build_matrix()` đọc registry)
> và ĐỎ khi bảng này trôi. Test không viết số nào — sửa **tài liệu**, đừng sửa mã.
>
> | | |
> |---|---|
> | Active development branch | **`main`** — hệ thống được phát triển tiếp TRỰC TIẾP ở đây |
> | Main baseline | **`f2b28e2`** = PATCH1 implementation `8bd2324` + PATCH1 live evidence `f2b28e2` |
> | `CACHE_VERSION` | **46** — kiểm: `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
> | `HISTORY_SCHEMA_VERSION` | **2** — kiểm: `grep -n 'HISTORY_SCHEMA_VERSION' frontend/src/state/history.ts` |
> | Family / Target | **12 / 24** — kiểm: `backend/.venv/Scripts/python.exe backend/scripts/catalog_runtime_matrix.py` |
> | ↳ phân rã family | **10 mô phỏng cơ chế tính toán** (`result_authority = computation`) + **2 biểu diễn** (`representation` — `structural_progressive_representation`, `web_presentation`). **Không** đếm phẳng cả 12 là "mô phỏng thuật toán" |
> | Trình bày 2D / 3D | **23 chỉ 2D · 1 có 2D+3D** (`network.protocol_encapsulation`) — W4B-2R: chính sách biểu diễn chọn theo CƠ CHẾ, `architectural_poc` không đủ tư cách bày toggle. Nguồn: `SimSpec.visual_modes` + `renderer.ts::representationPolicyOf`; guard toàn danh mục ở `representation-policy-w4b2r.test.ts` |
> | Archive (read-only) | `archive/m17-w2b-deep-hardening` → `feb12d8`, tag `m17-w2b-deep-hardening-archive` |
>
> ### Bốn tài liệu CANONICAL — mọi agent phải đọc trước khi sửa code
>
> | Vai trò | File canonical |
> |---|---|
> | Agent bootstrap + PRE-FLIGHT | **`docs/RULES.md` §1–2** |
> | Scope guard (phân loại + luật dừng) | **`docs/RULES.md` §3** |
> | Current state (file này) | **`docs/CURRENT_STATE.md`** |
> | Project index / architecture memory | **`docs/CODE_INDEX.md`** (module/symbol) + **`docs/ARCHITECTURE_MAP.md`** (kiến trúc, sở hữu, hướng phụ thuộc, bất biến) |
>
> ### 🔒 ĐÓNG BĂNG MÃ — chờ lượt đo chính thức #2 (từ 2026-08-23)
>
> **KHÔNG sửa** `backend/app`, `app/ai/skills/*.md`, schema, taxonomy, primitive,
> route, checker cho tới khi SEALED #2 chạy xong. Áp cho **mọi phiên**, không
> riêng phiên nào — ngày 2026-08-23 có hai phiên cùng sửa `semantic_program/` và
> candidate phải đóng băng lại **6 lần trong một ngày**; còn trôi thì con số đo
> được không gắn với bản nào cả.
>
> Được phép: `backend/scripts/`, `backend/tests/`, `docs/` (harness, không thuộc
> `MEASURED_SYSTEM_PATHS`). Cổng kiểm: `freeze_evaluation_candidate.py --verify`.
>
> Giao thức đầy đủ: **`docs/evaluation/semantic-benchmark/RUN2_PROTOCOL.md`** —
> ngân sách 520/620 (bound 11 → 13) và cơ chế loại 40 bài đã đo đều đã chốt
> TRƯỚC khi có seed. Mắt xích còn thiếu: **seed #2 do GVHD cấp**.
>
> ### vNext — ROUTE SINH ĐÃ PHỤC VỤ ĐƯỢC MỘT ĐỀ THẬT (2026-08-23, sau SEALED)
>
> Bằng chứng: `docs/evaluation/semantic-vnext/SERVE_PROBE_CHAIN.md` (tầng 2 —
> engineering evidence, **không phải** số luận văn).
>
> - Đề *"đảo dãy 5,2,8,1 bằng ngăn xếp"* → `status=ok` ·
>   `simulation_id=generic.semantic_program` · `source=semantic_program` · **5
>   khung**, qua `run_pipeline` sản phẩm với `SEMANTIC_ROUTE_MODE=serve`. Đo lặp
>   **3/4 lượt**, `retry=0`. Trước lượt này route **chưa từng phục vụ** một đề
>   nào cho người dùng thật.
> - Tám lượt probe trên đề ghép ngoặc chết ở **tám lớp lỗi HÌNH DẠNG khác nhau**,
>   không lượt nào là hiểu sai đề. Sửa theo hai nguyên tắc thay cho chín bản vá:
>   mã hoá được ⇒ validator giữ (`canonical_condition`); không mã hoá được ⇒
>   **đưa lỗi ngược cho LLM sửa** (`stage_semantic_program` ≤3 lượt, khuôn
>   `stage_simulate`). Trần là hằng số ⇒ **claim D1 nguyên vẹn**.
> - Sửa một lỗi ĐỊNH TUYẾN: `mismatch_gap` return trước nhánh phát, nên phán
>   quyết lệch của classifier legacy giết một outcome `servable=true`.
> - **`predicate_verdict` ĐÃ MỞ (2026-08-24), và đề ghép ngoặc nay chạy được.**
>   Phản đối cũ ("kiểm nó đòi cài lại chính thuật toán đang kiểm") áp quá rộng:
>   `_extremum` cũng tính lại `max`, `_membership` cũng tính lại `in`. Thứ giữ
>   tính oracle là *tính lại TỪ DỮ LIỆU ĐỀ, không đọc witness để suy đáp án* —
>   và `balanced_delimiters` thoả. Mở thêm `scalar_accumulation` vì đo cơ học
>   cho thấy **0/10 nghĩa vụ nhận được chủ thể vô hướng**, trong khi vòng lặp
>   tích luỹ trên một biên số là kiến trúc cơ bản nhất của Tin học 10. Taxonomy:
>   **11 nghĩa vụ**. Nguồn cả hai: DEV.
> - `CACHE_VERSION` **35 → 36**. Candidate đóng băng lại ở `d6b7b30`
>   (`464887dd…`, 128 file). Offline: pytest **1845** · vitest **1530 / 127
>   file** · tsc 0 lỗi · build sạch.
> - **CHƯA làm:** đo lại `A` (phải niêm phong SEALED MỚI) · bằng chứng thị giác
>   cho envelope do route PHÁT ra (bản đang có chụp envelope tiêm thẳng).
>
> ### M21 — ROUTE SINH NGỮ NGHĨA: ĐÃ ĐO CHÍNH THỨC trên SEALED (2026-08-23)
>
> Bằng chứng: `docs/evaluation/semantic-benchmark/` (`README.md` ·
> `freeze_protocol.md` · `CUSTODIAN_HANDOFF.md` · `EVALUATION_CANDIDATE.json` ·
> **`results/OFFICIAL_RESULT.md`** ← số chính thức của luận văn).
>
> - **Bản đem đo: `4e13e2b`** — danh tính máy kiểm được là
>   `measured_system.tree_hash` = `024f627b…` (126 file). Từ mốc này **không sửa**
>   prompt · schema · taxonomy · primitive · route · checker · runner · ngân
>   sách vì kết quả SEALED. `--verify` là cổng kiểm. (Bản `36bae92`/`5608fbfe…`
>   là lần đóng băng TRƯỚC pilot 4; candidate cuối cùng đem đo là `4e13e2b`.)
> - **⚠️ `EVALUATION_CANDIDATE.json` nay trỏ `dacd240`, KHÔNG phải bản đã đo.**
>   Sau Task 12, vNext sửa mã sản phẩm (routing · frame · renderer · biên
>   `spec_version`) nên tree hash trôi khỏi `024f627b…` và hai cổng con dấu ĐỎ
>   đúng như thiết kế. Xử lý theo luật *"DEV được phép làm thay đổi HỆ, SEALED
>   chỉ được phép làm thay đổi KẾT LUẬN"*: đóng băng lại candidate ở `dacd240`
>   (`706be2ad…`, vẫn 126 file) và lưu danh tính bản đã đo ở
>   `EVALUATION_CANDIDATE.baseline-4e13e2b.json`. **Số chính thức ở
>   `results/OFFICIAL_RESULT.md` vẫn là số của `4e13e2b` và KHÔNG được đọc như
>   số của `dacd240`** — muốn đo lại phải niêm phong SEALED MỚI. Hợp đồng
>   (taxonomy `4dd712a3` · primitive `1a127502` · schema `b87aeb18` · DEV
>   `8a3de7a3`) **không đổi** qua lượt này: chỉ cài đặt đổi.
> - **Route nay ĐI QUA `run_pipeline` thật** (bất biến #22). Trước 2026-08-21
>   `stage_semantic_program` **không có một ai gọi**: mọi mảnh đều xanh nhưng
>   chưa mảnh nào được ghép — unit test xanh **không** chứng minh đường
>   orchestration tồn tại.
> - **Cờ `semantic_route`**: `off` (mặc định, production không đổi một bit) ·
>   `shadow` · `serve`. Shadow chạy **độc lập với classifier legacy** — đặt
>   trong nhánh generic thì claim A hoá ra là claim về *classifier*.
> - **Hai tỉ lệ tách hẳn**: `A` executability · `B_internal_servable`
>   (STRONG-assurance nội bộ, **không phải "đúng"**). `A − B` phải **phân rã**:
>   chỉ một nhánh là `verification_gap`, còn lại là C₁b/C₂/binding.
> - **Ngân sách chốt cuối**: N=40 · 440 lượt logic · 520 HTTP, cưỡng chế ở cả
>   hai trục trong `ApiBudget`. 440 = 11 × 40 với 11 là upper bound **dẫn từ
>   call graph**.
> - `CACHE_VERSION` **33 → 34**. Taxonomy `4dd712a3` · primitive `1a127502` ·
>   schema `b87aeb18` · DEV `8a3de7a3` — **không đổi** qua cả bốn lần đóng băng.
> - Offline (đo lại lúc Task 13 closeout, 2026-08-23): pytest **1758** (17 skip,
>   1 deselect) · vitest **1473 / 123 file** · tsc 0 lỗi · vite build sạch.
> - **SEALED chính thức ĐÃ SẴN SÀNG** (2026-08-23), fingerprint `7e5df014…`,
>   N=40. Chuỗi provenance bốn tầng: SOURCE UNIVERSE V2 `4a9c3564…` (189 bài,
>   **audit cả 5 SGK**, 708 trang) → POOL `34d11adc…` (89 bài) → EXTERNAL
>   SELECTION `6efe2450…` (**seed `23082026` do GVHD cấp**) → SEALED. Ground
>   truth do `custodian/sealed_ground_truth.py` tính bằng Python thuần, không
>   import mã sản phẩm; 31/40 chấm được, 9 UNGRADED vì taxonomy cố ý không có
>   `predicate_verdict`.
> - **Ba SGK bổ sung chỉ cho 5/189 bài eligible.** Corpus bài toán thuật toán
>   của chương trình tập trung ở TH10 CĐ5 và TH11-KHMT CĐ6. Phủ chương trình
>   ghi đúng theo đó: `CURRICULUM_SUPPORT_PARTIAL`; tác động người học:
>   `LEARNER_IMPACT_NOT_EVALUATED`.
> - **TASK 12 ĐÃ CHẠY — MỘT LẦN, `2026-08-23T05:10:39Z`.** `evaluation_complete
>   = true`, 40/40 case, ngân sách dùng **205/440** logic · **207/520** HTTP ·
>   2 retry. Ba con số **tách hẳn nhau**:
>   **A** executability **3/40 (7,5 %)** · **B** internal servable **1/40
>   (2,5 %)** · oracle độc lập **PASS 2 · FAIL 0 · UNGRADED 9 · NO_RESULT 29**.
>   `A − B = 2`, **cả hai là `C2_postcondition_violated`**, `verification_gap`
>   = **0**.
> - **0 case "phát nhưng oracle nói SAI"** — biên assurance không sai-chấp-nhận.
>   **1 false rejection** (`T11CS-C6-041`: oracle ĐÚNG, C₂ vẫn chặn) ⇒ cổng nội
>   bộ **bảo thủ**, không phải lỏng.
> - **A = 3/40 KHÔNG đo được năng lực ngữ nghĩa.** 27 case chết ở
>   `semantic_program_invalid`, trong đó **17 case hỏng vì ĐÚNG MỘT lỗi kiểu**:
>   LLM phát `spec_version: 1.0` (số JSON) còn schema đòi `Literal["1.0"]`
>   (chuỗi) ⇒ Pydantic fail-closed trước mọi tầng ngữ nghĩa. Con số đứng nguyên
>   theo luật con dấu; muốn đo lại **phải niêm phong SEALED MỚI**, cấm vá rồi
>   chạy lại.
> - **D1 giữ được** (claim CẤU TRÚC): số bước interpreter 2 → 22 (biến thiên 11
>   lần) trong khi lượt LLM/case chỉ nằm trong `[2,4,5,6,7,8]`, chặn trên bởi
>   call graph. Telemetry hỗ trợ: 23 733,7 token/case toàn stage · 6 066,6
>   token/case chỉ stage ngữ nghĩa; tổng 949 347 token / 205 lượt.
> - **D2 = `D2_NOT_ESTIMABLE_ON_THIS_SEALED`** — `matched_N = 0`. Case ngữ nghĩa
>   phục vụ được duy nhất (`T10-C5-025`) thì route legacy `error`; giao rỗng.
>   **Không** suy D2 từ case không khớp.
> - Tập `34a10a9c…` ở `pilot/` là INTERNAL LIVE PILOT (tầng 2), **không** phải
>   số của luận văn. Chỉ `results/` (tầng 3) được trích dẫn.
>
> ### M19 — BỐ CỤC DÙNG CHUNG: khung theo cơ chế, một rail (2026-08-13)
>
> Bằng chứng: `docs/evaluation/m19/` (`before-1920.json` · `after.json`).
> Công cụ: `frontend/scripts/audit-composition.mjs`.
>
> - **TRƯỚC: 23/23 target hỏng @1920.** Thẻ cứng 1624px trong khi mực 276–1597px
>   (`decimal_to_binary` lấp 17%, `and_gate` 28%), và chữ lệch khỏi hình tới
>   722px. Hai lỗi — khung quá khổ (A) và hai hệ căn lề (B) — cùng một nguyên
>   nhân: thẻ là flex column STRETCH.
> - **SAU: 92/92 dòng OK** (23 target × 4 bề rộng). Khung nay 552–1401px thay vì
>   1624 cứng; rail lệch **0** ở mọi target trừ 1px ở `web.style_model`; không
>   tràn ngang, không cắt hình ở bề rộng nào.
> - **Chủ sở hữu đổi:** `.app-layout` (cột `auto`, căn giữa) + `.workspace-card`
>   (`fit-content` + sàn `min-width`) + `.workspace-card > * { width: 100% }`
>   + `simulations/stage-size.ts` (bề rộng SVG khai thật, bỏ `margin: 0 auto`).
>   KHÔNG có giá trị pixel riêng cho target nào.
> - **Hai ngoại lệ KHAI TƯỜNG MINH:** `web.style_model` được bám cửa sổ (trang
>   web lấp bề rộng khả dụng là hành vi đang dạy) · `logic.boolean_dag` được đặt
>   chú giải cạnh sơ đồ.
> - **`logic.boolean_dag`: khung NGOÀI đã sửa, đồ thị TRONG không còn lệch** —
>   rail 722 → 0, và bỏ `margin-inline: auto` của `.dag-stage` vì việc căn giữa
>   nay thuộc về khung. Không phát hiện lỗi bố cục đồ thị bên trong.
> - Offline: vitest **1275 / 92 file** · build sạch · pytest không đụng tới.
> - **CHƯA làm:** nhãn giá trị vị trí (10³ 10² 10¹ 10⁰) cho `binary.base_conversion`
>   — đó là ngữ pháp thị giác cấp miền, KHÔNG thuộc wave bề rộng này (§15).
>
> ### M18 — TẦNG LỚP HỌC: khách thử được, lớp học dùng được (2026-08-13)
>
> Hợp đồng còn hiệu lực: **`docs/CLASSROOM_AUTH_CONTRACT.md`**.
> Nghiệm thu: `docs/evaluation/m18/classroom-acceptance.json`.
>
> Trước wave này repo **không có tí xác thực nào**: không bảng user, không
> phiên, không router frontend. Nên đây là nền mới, và nó cố ý KHÔNG thêm
> dependency: PBKDF2 lấy từ thư viện chuẩn, phiên là token đục trong bảng
> (không JWT — đăng xuất phải thu hồi được ngay), điều hướng MỞ RỘNG trường
> `view` sẵn có thay vì dựng hệ điều hướng thứ hai bằng react-router.
>
> - **Trước đăng nhập KHÔNG có thanh bên.** Trang chủ giữ nguyên tiêu đề + một ô
>   nhập đề; chỉ thêm lối vào Đăng nhập/Đăng ký. Khách chạy được **một mô phỏng
>   THẬT** qua đúng pipeline production, đếm ở phiên máy chủ chứ không ở
>   localStorage — một cờ phía client thì xoá cache là có lượt mới. Lượt chỉ tính
>   khi mô phỏng RA ĐƯỢC: đề bị từ chối trung thực không ăn mất cơ hội duy nhất.
> - **Sau đăng nhập: thanh điều hướng theo VAI TRÒ**, thu gọn được, thành ngăn
>   kéo dưới 900px. Nó nằm **NGOÀI** lưới workspace — cột 208px bị gỡ ở W4B-3B
>   nằm TRONG lưới nên trải qua cả hàng sân khấu lẫn hàng điều khiển; đặt ngoài
>   thì lỗi ấy không tái diễn được.
> - **Nhiều phiên đã GỠ (M18-UI).** `SessionTabs` + `sessions`/`switchSession`/
>   `closeSession` + ~5.2KB CSS đã xoá: mỗi lúc đúng MỘT mô phỏng, mở bài khác là
>   THAY bài đang xem. Bài cũ không mất — nó nằm trong Lịch sử, mở lại 0 gọi AI.
>   Lý do: nạp mô phỏng vốn đã thay phiên, nên tab thứ hai chỉ hiện sau khi bấm
>   "+ Mô phỏng mới" — không đường nào vào bài đi qua nó. Cái giá đã biết: mở lại
>   từ Lịch sử dựng lại state từ envelope nên what-if học sinh tự làm không khôi
>   phục được.
> - **Lớp học tối thiểu**: tạo lớp → mã 6 ký tự (bỏ `0O1IL` vì học sinh gõ tay
>   mã đó) → học sinh vào lớp → giáo viên giao mô phỏng đang mở → học sinh làm →
>   giáo viên quan sát. Mã thu hồi/sinh lại được và mã cũ chết ngay.
> - **Giao bài đi qua `SimSpec.validate`** (bất biến #28). Mở bài KHÔNG gọi LLM:
>   ba mươi học sinh mở ra MỘT mô phỏng. Lời dặn của giáo viên là CHỮ.
> - **Quan sát bằng trạng thái CÓ CẤU TRÚC** (bất biến #27), hỏi lại mỗi 5 giây.
>   Không chiếu màn hình, không chụp DOM, và **không trường đúng/sai nào** —
>   correctness vẫn thuộc engine tất định.
> - Offline: pytest **1212** (2 skip, 1 deselect) · vitest **1284 / 93 file** ·
>   build sạch. Chrome CDP: **4 bề rộng × 3 vai SẠCH** (1920/1536/1366/768).
>   Tiêm lỗi bỏ kiểm vai trò ⇒ nghiệm thu ĐỎ ở cả 4 bề rộng, khôi phục XANH.
> - **CHƯA làm (không claim):** giáo viên CẤP tài khoản cho học sinh —
>   **MISSING**, chỉ có đường học sinh tự đăng ký rồi vào lớp bằng mã · xác minh
>   giáo viên là **mã mời dùng chung**, không phải hệ xác minh danh tính
>   (**PARTIAL**) · lượt thử chống được xoá localStorage, KHÔNG chống được xoá
>   cookie · quan sát gần-thời-gian-thực 5 giây, không tức thời · **chưa đo trên
>   người học**.
>
> ### W4B-4 — SOÁT TRẢI NGHIỆM TOÀN DANH MỤC: thao tác được, hay chỉ xem được (2026-08-13)
>
> **Phán quyết: `ALGOSIM_EXPERIENCE_AUDIT_COMPLETE`** —
> `docs/evaluation/m17/w4b4a-experience/VERDICT.md`.
> Ma trận SAU: `docs/evaluation/m17/w4b4a-experience/matrix-after.md` (SINH từ
> `probe.json`, không chép tay). Nghiệm thu Chrome:
> `w4b4c-experience/acceptance.json`. Tiêm lỗi: `w4b4d-composition/fault-log.md`.
> Commit: `211628c`→`dc67e2f`.
>
> Câu hỏi nghiệm thu, hỏi cho từng target: *"Bỏ hết Play/Next/đúng-sai đi, học
> sinh còn thao tác được lên mô hình và quan sát hệ quả tất định không?"*
>
> - **Phép đo chạy bằng HÀNH VI, không đọc metadata.** `experience-audit-w4b4a.
>   test.ts` phát ĐÚNG action mà từng miền nhận vào `module.apply` rồi ghi target
>   nào đổi được state **không dùng timeline**. Bản đầu ĐOÁN tên action và cho
>   **3 âm tính giả** — một phép đo sai im lặng đọc y hệt một phép đo sạch, nên
>   mồi hai chiều nằm ngay trong file.
> - **15 → 20 / 23 thao tác được** (đo từng bước: `211628c` 15 · `a49f951` 16 ·
>   `27c93d2` 20). Chuyển sang tương tác có ràng buộc: `database.
>   relational_table_query` (truy vấn là thứ ĐỔI, không phải thứ XEM),
>   `binary.base_conversion`, `binary.character_encoding`,
>   `network.graph_traversal`, `tree.traversal`.
> - **3 target CỐ Ý giữ trace, lý do CƠ CHẾ khoá trong `KEEP_TRACE`**
>   (`bounded_control_flow` · `scan` · `protocol_encapsulation`). Guard hai
>   chiều: không-thao-tác-được mà thiếu lý do là ĐỎ, và lý do còn sót khi target
>   đã có tương tác cũng ĐỎ (giải thích lỗi thời đánh lừa người đọc sau). Lý do
>   phải nói về CƠ CHẾ — "chưa kịp"/"TODO" bị từ chối.
> - **`count_if`/`sum_if`: con số không đổi nhưng NGHĨA đổi.** Chúng đã tính là
>   "thao tác được" từ baseline 15 — bằng `whatif_swap` mà chính sách của chúng
>   TẮT, tức **dương tính giả**. Phép đo đọc `!!mod.explore` (mọi module thuật
>   toán khai chung một khối) thay vì CỬA thật `explore.entry()`. Nay đọc cửa, và
>   hai bài có tương tác thật: **đổi chính ĐIỀU KIỆN** (`condition-param.ts`, miền
>   đóng). Tiền đề cũ vẫn giữ và nay được ĐO: kéo vẫn tắt, và hoán vị vẫn không
>   đổi kết quả cuối.
> - **`web.style_model` thao tác THẲNG lên trang**: bấm vào phần nào là chọn phần
>   ấy (khối ↔ bộ chọn ↔ nhóm control sáng cùng lúc), và dời được khối trong thân
>   trang — miền là một HOÁN VỊ của tập khối đã có, không thêm/xoá thẻ. Dời khối
>   đổi HTML mà **không** đổi CSS: chỗ lệch đó chính là bài học, và nó là test.
> - **`logic.boolean_dag`: một cổng không phải một mạch.** Đo được 1920: sơ đồ
>   chiếm **25%** bề ngang thẻ, 1217px trống dồn sang phải. Nguyên nhân KHÔNG ở
>   bố cục — mẫu công khai là đúng một cổng XOR, nên target mang tên "tổ hợp" chỉ
>   có 3 node và 1 bước lan truyền. Mẫu mới 3 đầu vào / 3 cổng / 2 tầng; chú giải
>   về đứng cạnh sơ đồ, cả cụm căn giữa → **lệch lề 0px ở cả 4 bề rộng**, mực lấp
>   **65%**. Hai lỗi Chrome-only lộ ra khi đo: SVG rơi về bề rộng mặc định 300px
>   dưới cha `fit-content`, và khung nét đứt cổng đầu ra bị viewBox cắt 7px (có
>   từ lâu).
> - **Nhãn "Đã đổi so với đề bài"** (`specDrift`, shell sở hữu): từ khi đổi được
>   tham số, tiêu đề (ĐỀ BÀI) và mô hình có thể nói hai điều khác nhau — đề viết
>   "từ 8,0 trở lên" trong khi học sinh vừa kéo ngưỡng về 6. So theo ĐÚNG các
>   khoá module khai (`currentConfig`), so bằng GIÁ TRỊ nên quay về giá trị cũ là
>   nhãn tắt. Chrome xác nhận: im lúc mở, lên tiếng sau khi đổi, và **im** với
>   `logic` (bật một đầu vào không mâu thuẫn với đề).
> - Offline: pytest **1148** (2 skip, 1 deselect) · vitest **1280 / 93 file** ·
>   build sạch · `catalog_runtime_matrix` **23 target, conformance/ownership/
>   parity 0, PASS**. Chrome CDP: nghiệm thu **6 target × 4 viewport SẠCH**
>   (1920/1536/1366/768) — tính lại KHÔNG cần Play.
> - **Tiêm lỗi 11 mutation, 8 bị bắt, 2 LỖ THẬT được vá, 1 mutant tương đương.**
>   Đợt chạy đầu vô giá trị (runner làm cả 92 file fail lúc collect ⇒ mọi fault
>   "đỏ" vì lý do sai; lượt đối chứng không tiêm gì cũng đỏ y hệt). Hai lỗ:
>   ngưỡng ngoài miền bị **KẸP** thay vì từ chối lọt qua 1276 test (luật
>   "từ-chối-không-kẹp" chỉ sống trong comment) → `condition-param.test.ts`; và
>   **gỡ hẳn một target khỏi catalog offline** lọt qua vì sàn đo là
>   `rows.length > 10` → nay phép đo phải phủ ĐÚNG registry.
> - **CHƯA làm (không claim):** chưa đo trên người học · 3 target giữ trace là
>   quyết định, không phải "đã xong" · nhãn lệch-đề chỉ nói CÓ lệch, không nói
>   lệch ở đâu · `web` dời khối chưa có đường kéo-thả (hai nút mũi tên, bàn phím
>   tới được) · chưa soát lại 7 target `ENGINE_CONTRACT_MISSING` (nợ từ W4B-2R).
>
> ### W4B-2S — biểu diễn phù hợp sư phạm + vai trò miền chở bằng hình (2026-08-10)
>
> Chính sách: `docs/PEDAGOGICAL_REPRESENTATION_POLICY.md`.
>
> - **Tiêu chí 2D/3D nới ĐÚNG CHỖ.** W4B-2R phán bằng một câu hỏi ("Z có mã hoá
>   biến khái niệm không") — loại đúng target nhưng vì lý do sai, và sẽ loại nhầm
>   về sau. Nay target có 3D phải khai `threeD.pedagogicalFit[]` + `whyNot2d`;
>   `role: "pedagogical"` một mình KHÔNG còn đủ (nó chỉ là nhãn tự nhận).
> - **Con số không đổi (21 / 0 / 1) nhưng LÝ DO đổi.** `packet_routing` chấm lại
>   bằng 10 tiêu chí: 3D **không thắng tiêu chí nào**, thua ở quan hệ (che khuất),
>   thao tác (chọn theo chiều sâu), rủi ro ngộ nhận (phối cảnh làm topology trông
>   có metric) — nên `2D_ONLY` đứng vững bằng ĐO. `encap` khai
>   `["relation_clarity","dimensional_value","mechanism_fidelity"]`.
> - **`DOMAIN_ROLE_CARRIED_BY_TEXT` đã SỬA** (W4B-2R mới chỉ đo). Audit cả 22:
>   `packet_routing` là target DUY NHẤT vẽ nhiều vai trò bằng cùng một hình tròn.
>   Chủ sở hữu mới `domains/network/node-glyph.ts` — `NodeType` (engine) → laptop
>   / router / tủ rack / switch / đám mây, vẽ tay bằng `path`, **không asset**.
>   Nguồn/đích tách khỏi loại thiết bị (vòng ngắm kép cho đích).
>   **KHÔNG dựng framework icon toàn hệ**: mảng/cây/đồ thị dùng hình trừu tượng
>   là ĐÚNG, thay bằng tranh vẽ sẽ làm hỏng chỗ đang đúng.
> - Offline: pytest **1135** (2 skip, 1 deselect) · vitest **1100/73** · build
>   sạch. Browser CDP **39/39 × 4 viewport** (1920/1536/1366/768). Tiêm lỗi
>   **4/4 ĐỎ** (gồm chính lỗi gốc), khôi phục XANH.
> - **CHƯA làm:** 3D `packet_routing` không dựng lại (điều kiện tái xét: topology
>   có tầng thật) · dấu hiệu NGUỒN nhạt hơn dấu hiệu ĐÍCH · 7 target vẫn
>   `ENGINE_CONTRACT_MISSING` · chưa đo trên người học.
>
> ### W4B-2R — biểu diễn theo cơ chế + vòng đời Quan sát (2026-08-10)
>
> Bằng chứng: `docs/MECHANISM_FIRST_REPRESENTATION_INTERACTION_EVIDENCE.md`;
> ma trận 22 dòng: `docs/MECHANISM_FIRST_REPRESENTATION_INTERACTION_AUDIT.md`.
> Commit: `eebc22a`.
>
> - **Chính sách biểu diễn có chủ sở hữu khai báo** — `renderer.ts::
>   representationPolicyOf` + `representationPolicyProblems`. **Dẫn xuất** từ
>   `supportedVisualModes` + `threeD.role`, KHÔNG thêm trường vào 22 module.
>   Điều kiện bày cả 2D lẫn 3D là `threeD.role === "pedagogical"` — sự tồn tại
>   của renderer KHÔNG phải lý do.
> - **Danh mục: 21 × `2D_ONLY` · 0 × `3D_ONLY` · 1 × `2D_AND_3D_JUSTIFIED`.**
>   Đúng MỘT target đổi chính sách: `network.packet_routing` (2D+3D → 2D_ONLY),
>   kết tội bằng lời khai của chính nó (`architectural_poc`, `meaningOfZ` =
>   "bố cục, không mang nghĩa khái niệm"). `ui3d.tsx` + `render3d.test.tsx` đã gỡ.
>   3D sư phạm còn nguyên ở `protocol_encapsulation` (Z = tầng giao thức).
> - **Ba luật vòng đời Quan sát ĐÃ ĐÚNG từ trước, nay khoá TOÀN DANH MỤC**
>   (`observe-lifecycle-w4b2r.test.ts`): learner khởi động lượt đầu · canonical
>   chạy trọn không cần trả lời · `nextStep` không đọc `prediction`.
> - **`m8-acceptance` từng XANH VÌ LÝ DO SAI** — nó "nghiệm thu 3D" sau khi 3D bị
>   gỡ, vì `setVisualMode` chỉ ghi cờ trình bày. Bài làm chứng nay dẫn xuất từ
>   chính sách.
> - Offline: pytest **1135** (2 skip, 1 deselect) · vitest **1089/72** · build
>   sạch. Browser CDP **39/39 × 3 viewport**. Tiêm lỗi **7/8 ĐỎ** (G không áp
>   dụng — chính sách cố ý không đòi baseline), khôi phục XANH.
> - **CHƯA làm (không claim):** §11/§26 *vai trò miền chở bằng CHỮ* — ĐÃ ĐO
>   (packet_routing vẽ 4 hình tròn giống hệt) nhưng **chưa sửa**, phải sửa ở chủ
>   sở hữu hình dạng dùng chung sau khi đo cả tree/graph/database · 7 target vẫn
>   `ENGINE_CONTRACT_MISSING` · `tree.traversal`/`algorithm.scan` chưa có mẫu
>   offline nên vắng trong bộ ảnh · KHÔNG dựng `BASELINE_OBSERVED` (§16) — lý do
>   ở evidence §6.
>
> ### W4B-2I — thao tác trên sân khấu + thí nghiệm cấu trúc (2026-08-10)
>
> Bằng chứng đầy đủ: `docs/W4B2I_INTERACTIVE_SIMULATION_EVIDENCE.md`; audit và
> lý do bác bỏ `BASELINE_OBSERVED`: `docs/W4B2I_INTERACTION_MODEL_AUDIT.md`.
> Commit: `96c3075` (audit) · `8ddf93a` (cổng 9/9) · `ebed0b3` (sân khấu + bàn
> phím) · `fce4f39` (what-if mạng).
>
> - **Cổng Thí nghiệm nay phủ 9/9 target thuật toán.** `bubble_sort` và
>   `selection_sort` là hai bài cuối; trước đó chúng là nơi DUY NHẤT còn bày vùng
>   cam kết ở Quan sát. Từ đây **không còn "bài làm chứng chưa gác"** — luật phát
>   biểu trên toàn danh mục.
> - **Họ tìm kiếm thao tác trên chính các cột**, không phải hàng nút:
>   `searchSceneRegions` ánh xạ `visualRole` (có từ W2, tới nay chỉ dùng làm tên
>   class) sang chỉ số cột. Có bàn phím đầy đủ; `svg` đổi `role` `img`→`group` khi
>   có vùng bấm. **Tất cả-hoặc-không**: không ánh xạ được thì hàng nút quay lại
>   nguyên vẹn, không có trạng thái lai.
> - **`network.packet_routing` có what-if CẤU TRÚC** (`net_connect` /
>   `net_disconnect` / `net_reset`) — target thứ hai đạt
>   `WHAT_IF_STRUCTURE_READY`. **Đổi engine CÓ KHAI BÁO**: `route: []` nay là
>   trạng thái hợp lệ "không tới được" (trước đây `buildSteps` ném lỗi).
>   `validateNetworkConfig` **vẫn** từ chối config đứt — hệ thì đúng-hoặc-từ-chối,
>   học sinh thì được phép làm đứt.
> - **KHÔNG dựng `BASELINE_OBSERVED`.** Tiền đề "lượt chạy đầu bị chặn chờ trả
>   lời" **sai** (5 bất biến liên quan đã đúng + đã khoá từ trước); thêm cổng sẽ
>   lấy đi quyền và là wave thứ SÁU trên cùng capability (`RULES.md §3c`).
>   User duyệt bỏ.
> - Offline: pytest **1135** (2 skip, 1 deselect) · vitest **1089/71** · build
>   sạch. Browser CDP **20/20 × 3 viewport** (1920×1080 · 1366×768 · 768×900).
>   Tiêm lỗi **8/8 ĐỎ** rồi khôi phục XANH.
> - **CHƯA làm (không claim):** 7/9 target vẫn SCENE_ADJACENT (họ scan/sort cần
>   thêm chỉ số vào model trước) · `sum_if` accumulator vẫn
>   REPRESENTATION_BLOCKED · 8 target vẫn `WHAT_IF_BLOCKED` · thêm/xoá **nút**
>   mạng cố ý ngoài phạm vi · chưa đo trên người học.
>
> ### Wave 3 — mã hoá ký tự (XONG offline)
>
> Target thứ **22** `binary.character_encoding` trong family **cũ**
> `positional_representation` — **KHÔNG** tạo family thứ 12. Cơ chế mới duy nhất:
> `character_code_mapping`. Học sinh xem từng bước: **ký tự → mã (ASCII / Unicode
> code point) → thập phân → nhị phân**.
>
> - **Ranh giới kiến trúc:** backend **chỉ kiểm định** (hợp đồng, kiểu, phạm vi
>   code point, cổng đủ-dữ-kiện) — **không engine, không chuyển nhị phân, không
>   trace**. Frontend sở hữu thực thi và **dùng lại `toBase()` của
>   `base_conversion`** ⇒ **không có bộ chuyển đổi thứ hai** (khoá bằng test).
> - **Chain:** `character_code_mapping → non_binary_base`. KHÔNG dùng
>   `binary_positional_weights`: `decimal_to_binary` chặn cứng 0–255 / 8 bit,
>   trong khi BMP cần tới 65535 = đúng `CONV_MAX_VALUE` của base_conversion.
> - **Hợp đồng nhỏ nhất dự án từng có:** chỉ `text` + `encoding`.
> - **Unicode theo CODE POINT ở cả hai tầng:** Python lặp theo code point; FE
>   dùng `Array.from` + `codePointAt`. Nếu FE dùng `text.length`/`charCodeAt` thì
>   😀 thành **hai** ký tự BMP "hợp lệ" trong khi BE từ chối — sai câm, mà đường
>   mở-lại-từ-lịch-sử (bất biến #17) đi thẳng vào engine FE. Có test khoá đúng
>   chênh lệch đó.
> - precomposed `U+1EBF` giữ **một** code point; decomposed giữ **ba** —
>   **không normalize**. Fixture dùng escape sequence để editor không tự ghép.
> - **Giới hạn (không được claim quá):** chỉ BMP (≤ U+FFFF); **emoji, ký tự ngoài
>   BMP, dãy byte UTF-8/UTF-16, Base64, nén, mã hoá bảo mật, mã hoá ảnh/âm thanh
>   đều NGOÀI phạm vi**. Quy ước nhị phân **không đệm số 0** — lấy từ chính
>   `toBase()`, không tự đặt convention mới.
> - **Learner action hiện chỉ là điều khiển timeline** (Previous/Next/Reset).
>   Chưa có prediction/what-if ⇒ đây là năng lực **quan sát**, chưa phải tương tác.
>
> #### W3-SIM — nâng lên REAL_SIMULATION (2026-07-27)
>
> Audit authenticity xếp W3 là **PARTIAL_SIMULATION**: engine gọi thẳng
> `toBase()` và **công bố** dãy bit, trong khi `divideSteps()` đã chạy sẵn ở
> chính module nó import. Nay W3 chạy **CHÍNH cơ chế chia lấy dư** đó:
>
> - phần thuần của đổi cơ số tách ra `binary/base-conversion.ts` (không React);
>   `convert-module.tsx` re-export ⇒ **một nguồn**, `base_conversion` không đổi
>   hành vi (41 test xanh);
> - `toBase()` **không còn** ở runtime W3 — kết quả **dẫn ra từ chuỗi số dư**;
> - `EncStepMeta` song ánh 1:1 với `trace.steps` (charIndex/phase/division/
>   committed). **Bỏ `floor((cursor+1)/4)`** — số bước chia nay phụ thuộc giá trị
>   mã nên số học trên cursor sai;
> - **ký tự đầu bung đầy đủ**, ký tự sau rút gọn và **nói rõ** "cùng quy tắc" —
>   cùng một `divideSteps`, không lệch kết quả;
> - Chrome **12 ảnh**, 1 lỗi lặp thuyết minh (W3-SIM-VR1, cùng lớp W3-VR1/
>   W2C-VR3 — **lần thứ ba**) đã vá + test hồi quy.
>
> **REAL_SIMULATION · TIMELINE_CONTROL · 2D.** Live NL integration: **PARTIAL**.
> Bằng chứng: `docs/evaluation/m17/w3-sim/` (offline) ·
> `docs/evaluation/m17/w3-live/` (live).
> - Chưa khai `library_discoverable` (chưa có đề mẫu công khai).
> - `CACHE_VERSION` **22→23** · family **11** · target **21→22**.
> - **Review thị giác Chrome: XONG** (`w3/character_encoding_visual_review.md`) —
>   4 fixture · **16 ảnh** (desktop 11 · 768px 5) · **REAL_VISUAL 4/4 · BROKEN 0**
>   · 2 lỗi trình bày phát hiện và đã vá (thuyết minh lặp ở bước cuối; ký tự chữ
>   số `'7'` in trần dễ đọc thành **số** 7 → nay bọc nháy). Chứng minh bằng ảnh:
>   bảng hiện DẦN thật (DOM bước đầu không chứa 65/dãy bit), `ế` → U+1EBF → 7871
>   → `1111010111111` không đệm, emoji bị từ chối sạch không hiện hai hàng
>   surrogate, 768px không tràn.
> - Giới hạn nhận: chip domain hiện "HỆ CƠ SỐ" (nhãn domain `binary`, đổi sẽ ảnh
>   hưởng cả hai target đổi số — ngoài phạm vi VR).
>
> #### W3-LIVE — smoke NL → spec (2026-07-29): **PARTIAL**
>
> 6 case × 2 lượt · `gemini-2.5-flash` · 27/45 HTTP · 0 transient · IN-PROCESS
> (Docker không chạy ⇒ artifact **không nói gì** về container).
> Bằng chứng: `docs/evaluation/m17/w3-live/`.
>
> - **7/12 PASS · 5/12 thất bại AN TOÀN · mọi trục an toàn = 0**
>   (`semantic_loss` · `fabricated_input` · `result_leakage` · `generic_leak` ·
>   `unsafe_acceptance` · `wrong_target_acceptance`).
> - **Phân loại đúng 6/6**: classify chọn `binary.character_encoding` mọi lượt;
>   ranh giới ký tự↔số sạch (`"Đổi số 65 sang nhị phân"` → `decimal_to_binary`
>   2/2). Thiếu dữ kiện và emoji ngoài BMP đều từ chối an toàn 2/2.
> - **BLOCKER (chưa sửa — cần quyết định phạm vi):** 5/6 lượt của ba case được hỗ
>   trợ bị chặn ở cổng cơ chế — `capability_gap` / `gate_mechanism_ownership`.
>   `check_mechanism_consistency_for_target` chỉ kiểm **sở hữu ĐƠN**, trong khi
>   taxonomy khai năng lực này là **CHUỖI** `character_code_mapping →
>   non_binary_base`; target cố ý chỉ sở hữu mắt xích đầu. Đề nêu mắt xích thứ
>   hai ("chuyển mã sang nhị phân") ⇒ gate fail-closed. Lượt PASS duy nhất rơi
>   vào nhánh permissive (`prescribed = none`) ⇒ **MODEL_VARIABILITY** trên đúng
>   một trường analyze.
> - **Hệ quả phải nêu thẳng:** ở baseline này `binary.character_encoding` gần như
>   **không tiếp cận được end-to-end bằng NL**, dù offline VERIFIED + REAL_VISUAL
>   + REAL_SIMULATION.
> - **CHƯA làm (không claim):** engine handoff — engine W3 ở FE, harness FE duy
>   nhất chạy Chrome (checkpoint cấm) ⇒ `NOT_EXECUTED`; bằng chứng engine là
>   **kế thừa** offline, không đo ở lượt live này. Ký tự tiếng Việt `U+1EBF`
>   **chưa đo được** (ENC-3 bị chặn trước khi có candidate).
>
> #### W3-LIVE-C1 — sửa cổng cơ chế + E2E đại diện (2026-07-29)
>
> Bằng chứng: `docs/evaluation/m17/w3-live-c1/`. Artifact baseline `w3-live/`
> **giữ nguyên** để so sánh.
>
> - **Root cause GIẢ ĐỊNH của checkpoint là SAI, đã đo bằng probe live (3 HTTP):**
>   analyze phát `binary_positional_weights` (ENC-3) hoặc `null` (ENC-1/2) —
>   **không** phải `non_binary_base`. Thiết kế "chain-aware gate" sẽ vô hiệu.
> - **Root cause THẬT — tái phát anti-pattern #1:** họ positional trong
>   `analyze_exposed_values()` được liệt kê bằng string VIẾT TAY, nên khi W3 thêm
>   `character_code_mapping` vào `FAMILY_MECHANISMS` thì enum analyze không đi
>   theo ⇒ **cơ chế duy nhất W3 sở hữu là bất khả phát** ⇒ nhánh direct-ownership
>   không bao giờ thoả mãn (đúng bệnh `_GENERIC_SCHEMA` thiếu `drag`).
> - **Sửa:** splat `FAMILY_MECHANISMS[POSITIONAL_REPRESENTATION]` vào enum
>   (**+1 giá trị**). `mechanism_gate.py` **không đổi một dòng** — cổng vẫn là
>   phép thử sở hữu đơn, fail-closed. Không cấp ownership giả, không hard-code
>   target id, không đụng analyze/classify prompt, spec, validator.
> - `CACHE_VERSION` **23→24** (chính sách định tuyến đổi — cùng tiền lệ W2C
>   20→21). `HISTORY_SCHEMA_VERSION` giữ **2**. family **11** · target **22**.
> - **W3 live natural-language integration = PARTIAL** (7/12 → **9/12 PASS**;
>   `mechanism_gate_failure` 5 → **2**; mọi trục an toàn vẫn **0**; 29/45 HTTP).
>   ENC-1/ENC-2 nay có candidate hợp lệ; ENC-1 run2 trượt ở cổng ĐỦ DỮ KIỆN
>   (không phải cổng cơ chế) do model variability.
> - **Giới hạn còn lại:** ENC-3 vẫn bị chặn ĐÚNG LUẬT — đề nói "chuyển mã sang
>   nhị phân" nên analyze chọn `binary_positional_weights`, cơ chế của
>   `decimal_to_binary` vốn chặn 0–255/8 bit nên không chở nổi code point 7871.
>   ⇒ **`U+1EBF` CHƯA đo được ở đường live.** Sửa tiếp phải chạm `analyze.md`
>   hoặc ngữ nghĩa cổng — cả hai là stop condition, **chưa mở**.
> - **Representative live-to-browser handoff = VERIFIED** cho `E2E-ENC-1`:
>   candidate live nạp qua chính `store.loadEnvelope`, **hash artifact ↔ hash spec
>   engine trùng khít** (`0217f627de31…`), 13 bước, mốc giữa có phép chia thật
>   `65 : 2 = 32 dư 1`, DOM bước đầu chưa có `1000001`. 3 ảnh · 0 LLM call.
>   `E2E-ENC-2` (Unicode) = **NOT_MEASURED** — không dựng config bằng tay.
> - **pedagogical alignment = EVIDENCED cho case W3 đại diện · learner impact =
>   NOT EVALUATED.** Interaction giữ `TIMELINE_CONTROL`, không nâng hàng loạt.
> - Container Docker đang chạy nhưng **STALE** (`cache=22 · family=10 ·
>   target=20`) — live chạy IN-PROCESS, artifact **không** nói gì về container.
>
> #### W3-LIVE-C2 — luật phát cơ chế cho họ positional (2026-07-29): **PARTIAL — CLOSED**
>
> Bằng chứng: `docs/evaluation/m17/w3-live-c2/` (+ preflight read-only ở
> `w3-live-c2-preflight/`). Artifact `w3-live/`, `w3-live-c1/` **giữ nguyên**.
>
> - **Khiếm khuyết nhắm tới ĐÃ ĐÓNG:** `mechanism_gate_failure` **5 → 2 → 0**.
>   `prescribed_procedure = character_code_mapping` ở **6/6** lượt ENC-1/2/3
>   (trước là `binary_positional_weights`). `prescribed_mechanism_error` = 0 ·
>   `classification_error` = 0 · `spec_synthesis_error` = 0.
> - **Sửa gì:** `analyze.md` thêm luật phát cho họ positional quyết theo **HÌNH
>   DẠNG ĐẦU VÀO** (ký tự ↔ số) + luật cho 3 giá trị `bounded_control_flow.*`
>   vốn cũng bị phơi mà không được dạy. **GUIDANCE LOCK**: mọi giá trị trong
>   `analyze_exposed_values()` phải có hướng dẫn trong `analyze.md` (uncovered
>   **4 → 0**), đã **chứng minh bằng tiêm lỗi giả**. `CACHE_VERSION` **24→25**.
> - **KHÔNG đụng:** `mechanism_gate.py`, taxonomy, catalog ownership,
>   `CharacterEncodingSpec`, validator, `classify.md`, pipeline schema, engine,
>   renderer, `base-conversion.ts`, E2E adapter. Production diff = **2 file**
>   (`analyze.md`, `CACHE_VERSION`).
> - **W3 live NL integration = PARTIAL — CLOSED.** 8/12 PASS · 4 FAIL_SAFE · mọi
>   trục an toàn **0** · 28/45 HTTP. PASS giảm 1 so với C1 **không phải hồi quy**:
>   lượt đó vốn do analyze may mắn phơi đủ dữ kiện, không do cơ chế.
> - **Thất bại còn lại đã DỊCH XUỐNG HẠ NGUỒN, đều an toàn:** ENC-1 (2/2) và
>   ENC-3 run2 trượt cổng **đủ dữ kiện** (analyze không phơi `quoted_characters`/
>   `encoding_name`); ENC-3 run1 trượt cổng **đủ ngữ nghĩa** — dương tính giả
>   `multiple_operations_not_supported` do analyze tách một quy trình thành hai
>   việc. Cả hai ngoài phạm vi C2.
> - **`U+1EBF` VẪN chưa đo được ở đường live** ⇒ **E2E-ENC-2 KHÔNG chạy** (§15:
>   không dựng config tay, không lấy candidate C1, không sửa adapter). **0 ảnh.**
>   E2E ASCII của C1 vẫn nguyên giá trị.
> - **C2 one-round policy COMPLETED · hard stop APPLIED · KHÔNG mở C3 · không có
>   correction wave tiếp theo.** Interaction giữ `TIMELINE_CONTROL`, không nâng.
>   `learner impact = NOT_EVALUATED`. Part B vẫn `BLOCKED_NO_DOCX`.
>
> ### Wave 2C — luồng điều khiển hữu hạn (XONG offline)
>
> Family thứ **11** `bounded_control_flow` / target thứ **21**
> `algorithm.bounded_control_flow`: chạy TỪNG BƯỚC một đoạn chương trình hữu
> hạn (gán · if/else · while có biên · hiển thị). Học sinh thấy câu lệnh đang
> chạy, biểu thức được tính, điều kiện đúng/sai, nhánh được chọn, biến đổi giá
> trị, số lượt lặp. **KHÔNG phải trình thông dịch Python**: không hàm, đệ quy,
> mảng, chuỗi, số thực, nhập xuất, break/continue, eval/exec, sandbox.
>
> - **Ngữ pháp ĐÓNG + giới hạn MỘT NGUỒN** (`simulation/program_spec.py`): ≤12
>   câu lệnh · lồng ≤2 · ≤8 biến · biểu thức ≤4 tầng · ≤200 bước · while ≤50
>   lượt. Cấu trúc spec là **danh sách phẳng + tham chiếu id** (đúng tiền lệ
>   `logic.boolean_dag`) vì structured output của Gemini KHÔNG biểu diễn được
>   schema đệ quy.
> - **Validator fail-closed** (`validation/program.py`): loại câu lệnh/biểu thức
>   ngoài ngữ pháp, biến chưa khai báo, sai kiểu, chia 0 tĩnh, điều kiện không
>   phải đúng/sai, while thiếu biên, tham chiếu vòng, câu lệnh mồ côi/dùng hai
>   khối, spec mang kết quả. **KHÔNG coercion**: `"5"`≠`5`, `true`≠`1`, `1`≠`true`.
> - **Vòng lặp KHÔNG BAO GIỜ treo**: chạm biên → dừng và nói thật *"Chương
>   trình chưa kết thúc trong giới hạn mô phỏng"*, KHÔNG trình bày như đã chạy xong.
> - **Đủ ngữ nghĩa**: `pipeline_stages.py` được MỞ RỘNG (không tạo module song
>   song) để đọc cấu trúc spec đã validate — đề hỏi gán + rẽ nhánh mà spec chỉ
>   có gán thì KHÔNG trả `ok`. Thứ tự ở family này **không** authoritative (thứ
>   tự chạy do chính chương trình quyết định) và gợi ý học sinh theo đúng lĩnh vực.
> - **Đủ dữ kiện**: InputKind mới `program_statements` + normalizer dùng chung —
>   "Mô phỏng vòng lặp while." (không giá trị nào) → `insufficient_specification`,
>   hệ **không bịa** chương trình mẫu.
> - FE: `core/program.ts` (interpreter tất định, dùng lại `TraceBuilder`/
>   `Step.line`/`Snapshot.vars`) + `domains/algorithm/program-module.tsx` (dùng
>   lại `PseudocodeView`/`VarsView`, **2D-only** — chiều sâu 3D không mã hoá
>   biến nào của chương trình nên làm 3D sẽ là chiều sâu giả, bất biến #18).
>   **Mã giả DẪN XUẤT từ `statements[]`** và interpreter gắn `Step.line` từ
>   CHÍNH bản đồ đó — highlight không thể trôi.
> - **W2C-C1 (contract alignment, `238a8a0`)** — đóng hai root cause do live bắt:
>   **L1** biến được **khai báo mà chưa khởi tạo** (hệ KHÔNG bịa 0/false) + lượt
>   **definite-assignment** (if/else = GIAO hai nhánh; if-không-else và while
>   KHÔNG mở rộng); **L2** bề mặt LLM đổi sang **biểu thức INLINE, nông, phi đệ
>   quy** (bỏ bảng `expressions[]` + tham chiếu id) kèm **normalizer TẤT ĐỊNH**
>   sang biểu diễn nội bộ; **L3** giữ nhãn `insufficient_specification` cho ca
>   classify tự từ chối. Contract `program-1.0 → program-2.0`,
>   `CACHE_VERSION` **21→22**. Live rerun (lượt 2): L1/L2 **hết lỗi cũ**, lỗi
>   dịch sang **nối khối bằng id câu lệnh** (mồ côi / `body` rỗng) — còn mở,
>   xem `w2c/bounded_control_flow_live_smoke.md`.
> - `CACHE_VERSION` **20→21** (thêm family/target AI-reachable + enum analyze).
>   `HISTORY_SCHEMA_VERSION` **giữ 2**. `scan-1.0` và hợp đồng bảng **không đụng**.
> - Offline: pytest **1047** (2 skip, 1 deselect) · vitest **626/48** · build
>   sạch · conformance 21/0 · descriptors không trôi.
> - **CHƯA làm (không claim):** review thị giác Chrome thật · live LLM ·
>   prediction/what-if · `for` đếm (hoãn có chủ đích, ưu tiên `while` trước).
>   ⚠️ `classify.md` đã đổi ⇒ **phải restart backend** trước bất kỳ lượt live nào.
>
> #### `algorithm.bounded_control_flow` — bốn mức bằng chứng (2026-08-03)
>
> Tách bạch, **không gộp thành một câu**:
>
> | Mức | Trạng thái |
> |---|---|
> | ENGINE | **VERIFIED** — trace `2→5→8→11→14→17`, `completion=completed`, khớp oracle độc lập |
> | HANDOFF backend→frontend | **VERIFIED** (`c6f4c5d`) — envelope đã chuẩn hoá nay frontend tiêu thụ được; trước đó backend `ok` mà trình duyệt từ chối |
> | THỊ GIÁC + TƯƠNG TÁC (bằng **fixture**) | **VERIFIED** — Chrome thật 1440×1000 và 768×900, click/kéo/phím thật trên Tiến·Lùi·Tự chạy·Dừng·thanh tua·Đặt lại |
> | **NL LIVE end-to-end** | **NOT_VERIFIED** — xem dưới |
>
> Live smoke (`gemini-2.5-flash`, IN-PROCESS, 3 lượt, **12/12 HTTP**, 0 retry
> transient): **0/3 pass**. Một lượt ghi được phán quyết đầy đủ — analyze phát
> đúng `bounded_control_flow.bounded_loop`, classify chọn đúng
> `algorithm.bounded_control_flow`, mechanism gate **không** chặn — nhưng simulate
> hỏng **cả 3 lần** với `structural_invalid`: *"Vòng lặp … phải có ít nhất một câu
> lệnh trong thân."* Hai lượt còn lại bị trần ngân sách cắt trước khi kết luận.
>
> Đây **đúng khiếm khuyết W2C đã ghi ở trên là "còn mở"** — LLM không nối được
> khối lệnh bằng id (`body` rỗng). Phạm vi rộng hơn một case benchmark, nên
> **không** vá bằng prompt trong lượt này. `m11-loop-gap` vì thế được sửa theo
> **năng lực** (engine sở hữu cơ chế) chứ không theo độ tin cậy của đường NL.
> Container Docker lúc đo là **STALE** (thiếu `bounded_control_flow`); lượt live
> chạy IN-PROCESS nên số liệu **không** nói gì về container.
>
> ### Phạm vi W2B
>
> | | Trạng thái |
> |---|---|
> | **Product Wave 2B** | **NOT CLOSED** |
> | **PATCH2 / PATCH3 / PATCH4** | **REMOVED FROM MAINLINE** · **PRESERVED ONLY IN ARCHIVE** · **WILL NOT BE MERGED BACK INTO MAIN** |
>
> - PATCH2/PATCH3 là deep production hardening (stage-preserving spec generation;
>   analyze parameter grounding + bounded repair) — hữu ích nhưng **vượt quá phạm
>   vi cần thiết**, làm lệch trọng tâm khỏi mô phỏng giáo dục 2D/3D, và không tạo
>   giá trị học tập tương ứng độ phức tạp. **PATCH4 chưa triển khai và sẽ không
>   triển khai.** Wave 2C **không mở**. Archive **không bao giờ merge lại**.
> - **`database.relational_table_query` — độ mạnh claim đúng:** truy vấn bảng
>   **đơn giản** (1–2 tầng) **VERIFIED** (live L1 lọc+chọn-cột, L2 sắp-xếp-ổn-định,
>   L6 từ-chối-nhiều-mục-tiêu — `docs/evaluation/m17/rc1/live_table_query_report.md`);
>   pipeline **nhiều tầng bằng ngôn ngữ tự nhiên** là **PARTIAL / EXPERIMENTAL** —
>   **chưa** được chứng minh ổn định end-to-end với production LLM.
> - Ba hành vi do PATCH1 vá (đề thiếu bảng → từ chối đúng lý do; ô trống không
>   thành 0; pipeline thiếu tầng không trả `ok`) được khoá **offline + review ảnh
>   Chrome thật**, và có **xác minh live ngay trong mainline** tại `f2b28e2`
>   (strict 1/3 — P3 đạt; P1/P2 không đạt nhưng **không bịa dữ liệu**).
> - Chi tiết, bằng chứng từng claim và future work:
>   [`docs/evaluation/m17/W2B_THESIS_SCOPE_DECISION.md`](evaluation/m17/W2B_THESIS_SCOPE_DECISION.md).
>
> Các mục lịch sử bên dưới **giữ nguyên**, kể cả các lượt live thất bại — hệ từ
> chối trung thực khi chưa đủ khả năng là **dữ liệu**, không phải điều cần giấu.

> **M17-RC1 — Catalog Runtime Conformance & Browser Stress Audit: XONG**
> (`c388606..fa9c21d`). Checkpoint **đo lường + siết cổng**, KHÔNG mở family mới
> (vẫn 9 family / 19 target). **§A** `runtime_identity.py` + `runtime_doctor.py`
> — bắt container chạy code CŨ (đúng lỗi user gặp thật: container còn CACHE "7"
> thời M10 nên không có `tree.traversal`); Dockerfile/compose nhận `GIT_SHA`/
> `BUILD_TIME`. **§B** `catalog_conformance.py` — ma trận sinh TỪ REGISTRY, 19
> target 0 vi phạm. **§D+§C1.1 SEMANTIC COMPLETENESS**: bất biến **`status=ok`
> ⟹ không yêu cầu nào bị bỏ sót**. Đề hỏi nhiều việc mà family chỉ dựng được
> một → từ chối trung thực (ca gốc: "cả 4 kiểu duyệt cây"). Định danh yêu cầu
> là **operation** (mục tiêu) chứ KHÔNG phải mechanism (cơ chế) — `find_max` và
> `find_min` dùng chung `track_extreme` nhưng là HAI việc; `operations.py` dẫn
> xuất 24 operation từ `(target, variant)`, phủ **9/9 family** (mechanism chỉ
> phơi 3). §C1.1 thêm tầng **semantic**: ba target logic cùng đáp ứng một
> `boolean.evaluate_expression` nên analyze gợi ý dao động không còn gây từ
> chối oan — route chọn *implementation*, KHÔNG được xoá *yêu cầu*. **§C2 CỔNG
> ĐỦ DỮ KIỆN DÙNG CHUNG** (`input_requirements.py` + `sufficiency_gate.py`):
> tổng quát hoá structure-gate của tree ra **17/19 target APPLICABLE** (2
> NOT_APPLICABLE có lý do dẫn xuất từ hợp đồng); MỘT cổng + normalizer theo
> **nhóm dữ kiện**, KHÔNG gate riêng từng target (test khoá bằng glob). **§C**
> ma trận archetype 8 slot × 19 target: **105 PASS / 0 FAIL / 44 GAP / 3 N-A**,
> 98 case qua production `run_pipeline`, generic-leak 0 · false-positive-sim 0 ·
> false-refusal 0 · semantic-loss 0 · result-leak 0. **§R1+§E** tách HAI chế độ
> replay: `historical_reproduction` (worktree + generator lịch sử → W0/W1
> DATA_IDENTICAL, chỉ `run_meta` nondeterministic) vs `current_policy_replay`
> (đầu vào lịch sử + pipeline hiện tại → migration report, 0 thay đổi không
> giải thích được). **§L1 live** (14 lượt analyze, 14/16 HTTP, 0 retry): analyze
> THẬT cung cấp grounded evidence ổn định — sufficiency **12/12 PASS**, dữ liệu
> cụ thể còn nguyên 12/12, hai đối chứng thiếu dữ kiện **FAIL 2/2 và KHÔNG bịa**
> ⇒ giữ §C2 nguyên, stub lịch sử là *superseded fixture contract*. **§E+§E1
> AUDIT THỊ GIÁC** 6 renderer / 25 fixture / **134 ảnh** Chrome thật, 2 viewport:
> **5 REAL_VISUAL + 1 PARTIAL (generic)**, 0 BROKEN. Ba lỗi trình bày đã sửa
> (nhãn dài đè nút ở graph; nhãn chồng + badge `GENERIC` ở generic; so le 3
> hàng) — **chỉ lớp trình bày, engine state không đụng**. CACHE **15→17** (hai
> bump: `requested_mechanisms`, rồi `requested_operations`) + frontend
> `HISTORY_SCHEMA_VERSION` **1→2** (envelope lưu TRƯỚC cổng có thể là mô phỏng
> nửa vời). Offline tại close: pytest **891** · vitest **536/43** · build sạch.
> **Ba điều trung thực phải giữ khi trích dẫn:** (1) **VIS-003 là ARTEFACT PHÉP
> ĐO, không phải lỗi sản phẩm** — runner cũ đổi viewport SAU khi trang dựng ở
> 1440px nên ảnh 768px không phản ánh layout thật; chẩn đoán DOM chứng minh
> không overflow/clipping/rigid-min-width; production CSS **không** sửa gì.
> (2) Runtime parity **xác minh tại `e9ec370`** (PASS), **KHÔNG** chạy lại tại
> HEAD `fa9c21d` vì Docker không khả dụng — `backend/app` không đổi trong range
> nên kết quả cũ còn hiệu lực, nhưng đây **không** phải một lần xác minh mới.
> (3) generic giữ **PARTIAL** cả visual lẫn engine authenticity — audit thị giác
> KHÔNG nâng hạng. **Wave 2B chưa mở.**
>
> **M17-Lite — Curriculum Capability Expansion & Simulation Authenticity: ĐANG
> MỞ** (proposal duyệt `620a09a`). **Wave 2A XONG (offline)** — family MỚI
> **`tree_traversal`** (target `tree.traversal`), duyệt cây nhị phân 4 biến thể
> preorder/inorder/postorder/level_order. FE domain mới `tree/tree-module.tsx`:
> executor KHUNG NGĂN XẾP mirror đệ quy (DFS pre/in/post) + HÀNG ĐỢI (level);
> renderer cây phân tầng (layout in-order, panel stack/queue theo biến thể,
> CẤM nhãn generic); oracle ĐỆ QUY ĐỘC LẬP 4 variant trên cây chuẩn + single/
> skewed/incomplete/uneven/label-số + duplicate-label-stable-id (39 test). BE:
> `FamilyId.TREE_TRAVERSAL` + mechanisms `tree_traversal.{preorder,inorder,
> postorder,level_order}` (prefix=family_id theo canonical convention, KHÔNG
> `binary_tree.*` — giữ `mechanism_family()` matching) + validator mirror
> (multi-parent/cycle/disconnected/depth≤5) + catalog `tree-1.0` + classify.md
> 2f (tree vs graph; thiếu cấu trúc → unsupported KHÔNG dựng cây mặc định) +
> authenticity contract + routing/near-miss test (BST/AVL/heap/n-ary →
> unsupported, KHÔNG leak). **ĐÓNG regression Wave 0:** tree honest+adversarial
> nay route `tree.traversal` (ROUTED_SPECIALIZED) — **CONDITIONAL_LEAK = 0**;
> case thiếu-cấu-trúc → unsupported. Audit W2A: 73 case, 0 leak, 18 REAL + 1
> PARTIAL. Visual fixtures 6 case (renderer = **NEEDS_VISUAL_REVIEW** — SSR cấu
> trúc đạt, chờ review browser). **M16 frozen bất khả xâm phạm:** pin
> `M16_FAMILY_VALUES` (8) thay live `FamilyId` → thêm family M17 KHÔNG làm trôi
> artifact/dataset frozen (content không đổi 1 byte). CACHE **14→15**. Catalog
> **18→19 target / 9 family**. **HAI PHÒNG THỦ THÊM sau live:** (a)
> **structure gate v2** (`simulation/structure_gate.py`) — live run 1 cho thấy
> LLM **bịa cây** cho đề thiếu cấu trúc (false-positive simulation); gate v1
> (đếm số lượng) **bị chứng minh không đủ** ở run 2 (analyze mô tả trừu tượng
> "quan hệ cha-con giữa các nút" đếm ra rel=1/obj=2 → cho qua); **v2 đòi MỘT
> item nêu ≥2 ĐỊNH DANH NÚT phân biệt** (quan hệ giữa hai nút có tên) + adapter
> gộp dict-relation; test dùng **analyze output THẬT** từ live. (b)
> **consistency gate** — phơi bày `tree_traversal.*` vào analyze-exposed để
> **tái dùng recovery M15 khoá 3** (mechanism + ownership, KHÔNG keyword):
> classify lạc generic → 1 reclassify bounded → vẫn lệch thì fail-closed, KHÔNG
> tạo generic simulation. **LIVE (3 run, 53 HTTP tổng):** run 3 **pha A 6/6
> functional safety · 5/6 exact-path** (case insufficient = `EARLY_SAFE_REFUSAL`,
> gate `NOT_RUN_BY_DESIGN`, evidence linked=0 — forced-route regression offline
> chứng minh gate SẼ chặn đúng mã) + **pha B stability 5/5** (initial route
> **5/5** và final route **5/5** = `tree.traversal`, variant inorder 5/5, 0
> reclassify, 0 leak, 0 false-positive, 0 false refusal; n=5 là mẫu nhỏ, KHÔNG
> tuyên bố ổn định tuyệt đối). Offline sau W2A: pytest **775** (2 skip, 1
> deselect) · vitest **532/42** · build sạch. **Wave 2A CLOSE về
> correctness/routing**. **M17-VR1 (browser visual review, `bfd2dc3`):**
> renderer **NEEDS_VISUAL_REVIEW → REAL_VISUAL** sau 3 fix bounded, review bằng
> Chrome THẬT qua CDP (6 fixture / 16 ảnh, xem ảnh trực tiếp — SSR không dùng
> làm bằng chứng). Ba lỗi chỉ browser mới thấy: **(1) BROKEN** `var(--border)`
> là **token ma** → `stroke` SVG thành `none` → **toàn bộ cạnh cây vô hình**,
> lan sang cả `network.graph_traversal` (W1); nguyên nhân gốc: `tokens.test.ts`
> chỉ quét `.css` → **nay quét cả `.tsx/.ts`**. **(2)** Inspector lộ toàn bộ
> thứ tự duyệt từ bước 0 → hiện dần. **(3)** `HomeView` có bản sao notice đọc
> thẳng `reason` KỸ THUẬT, bỏ qua `learner_reason` của W0 → gộp về
> `UnsupportedNotice` + tiêu đề "CHƯA ĐỦ DỮ KIỆN" cho
> `insufficient_specification`.
>
> **Wave 2B — `database.relational_table_query`: ĐANG MỞ, CHƯA CLOSE.** Family
> thứ 10 / target thứ 20 (`f0acbc2`), goal-aware completeness (`82a90e5`),
> review thị giác REAL_VISUAL 9/9 (`88618ac`), live grounding (`0afcb37`):
> **3/6 case đạt · grounding perfect 3/3 trên case sinh được spec · 18 HTTP ·
> 0 retry · 0 reclassify · generic-leak 0 · false-positive-sim 0**. Ba finding
> live đã được đóng bằng **W2B-PATCH** (chưa chạy lại live):
> **(L4) ĐỦ TẦNG PIPELINE** — completeness PHA 2 từng so ở tầng TARGET (target
> khai đáp ứng cả 9 operation ⇒ mọi spec đều "đủ") nên spec bỏ 2 tầng cuối vẫn
> trả `ok`; nay `simulation/pipeline_stages.py` so `requested` × **tầng spec ĐÃ
> VALIDATE thực sự dựng được** (`stages_of`, đọc thẳng cấu trúc, KHÔNG đọc
> narration) + so tham số chắc chắn (limit/hàm tổng hợp/chiều sắp xếp; tên cột
> KHÔNG so để khỏi chặn oan). Hai lớp: thiếu tầng báo ĐÍCH DANH ngược cho lượt
> simulate sau (đề hợp lệ vẫn chạy được), cạn lượt thì PHA 2 từ chối
> fail-closed. Thứ tự tầng công bố MỘT NGUỒN `filter→projection→sort→limit→
> aggregate` (aggregate SAU limit), khoá bằng SỐ (AVG 8.5 ≠ 7.5) chứ không bằng
> lời. *Giới hạn trung thực: analyze không có trường diễn đạt thứ tự khác, nên
> hệ KHÔNG phát hiện được yêu cầu đảo thứ tự — chấp nhận được vì engine chỉ có
> một thứ tự và các thứ tự khác đều là truy vấn lồng, vốn đã bị từ chối ở
> classify; hệ không bao giờ ÂM THẦM đảo thứ tự rồi trả `ok`.*
> **(L5) THỨ TỰ LÝ DO TỪ CHỐI** — hai khuyết tật độc lập: (a) `_has_table` nhận
> "≥2 object + có con số" là đã có bảng nên đề KHÔNG có bảng vẫn lọt cổng rồi bị
> báo sai bản chất ("tách hai truy vấn"); nay đòi **nội dung ô thật**
> (`values`/`labels`); (b) lọc và sắp xếp là hai TẦNG của MỘT truy vấn nhưng bị
> đếm thành hai truy vấn độc lập ⇒ **CHẶN OAN đề hợp lệ CÓ bảng** (chưa lộ ở
> live vì case L5 chết trước ở chỗ thiếu bảng); luật đếm mới dẫn xuất từ HỢP
> ĐỒNG SPEC (một spec mang ≤1 tầng mỗi loại ⇒ số truy vấn = số chữ ký khác nhau
> nhiều nhất TRONG CÙNG một loại tầng), `query_group` do analyze khai vẫn được
> tin như cũ.
> **(L3) MARKER Ô TRỐNG THEO LƯỢC ĐỒ** — MỘT biên duy nhất (ô thô → chuẩn hoá
> → ép kiểu → validate): ô rỗng là thiếu ở mọi kiểu cột; chữ "trống"/"—"/"N/A"/
> "null" chỉ là thiếu ở cột **số/đúng-sai** (hoặc cột khai `nullable: true`);
> cột chữ GIỮ literal; `0`/`"0"`/`false`/"không" KHÔNG bao giờ là ô trống; chữ
> sai kiểu vẫn fail-closed; `nullable: false` + ô trống → từ chối. Mỗi ô đổi để
> lại bằng chứng trong `config.normalizations`. **Mirror FE là lỗ THẬT đã bịt:**
> validator FE trước đây không ép kiểu ô nào nên chuỗi "trống" lọt vào engine FE
> và AVG đếm cả ô trống (`counted=6` thay vì `4` — sai câm), mà đường mở-lại-từ-
> lịch-sử (bất biến #17) đi THẲNG vào engine FE.
> **Lỗi chỉ REVIEW ẢNH mới thấy (unit + SSR đều xanh):** thông điệp "chưa dựng
> được 2 bước" lại đội tiêu đề "TÁCH THÀNH TỪNG YÊU CẦU" — lời khuyên SAI vì đề
> vốn là MỘT truy vấn nhiều bước; nguyên nhân gốc là notice chọn tiêu đề chỉ
> theo `failure_category`, mà `semantic_incomplete` nay gộp hai ca cần lời
> khuyên NGƯỢC NHAU. Thêm mã `PIPELINE_STAGE_INCOMPLETE`, notice đọc
> `error_code` trước; `failure_category` GIỮ NGUYÊN để không làm trôi taxonomy.
> `CACHE_VERSION` **19→20**; `config_contract_version` bảng **table-1.0→1.1**
> (luật validate đổi) trong khi `specVersion` trên dây GIỮ "table-1.0" vì thay
> đổi chỉ THÊM trường tuỳ chọn — config cũ trong lịch sử vẫn hợp lệ. Offline sau
> patch: pytest **996** (2 skip, 1 deselect) · vitest **596/46** · build sạch ·
> catalog conformance 20 target 0 vi phạm · review thị giác **REAL_VISUAL 5/5**
> (18 ảnh Chrome thật, 2 viewport). Artifact: `docs/evaluation/m17/w2b-patch/`.
> **Wave 2B vẫn CHƯA CLOSE.** Wave 2C KHÔNG mở.
>
> *Cập nhật 2026-07-25 (quyết định phạm vi):* lượt live rerun của PATCH1 **đã
> chạy** tại `f2b28e2` — **nay là HEAD baseline của `main`**, artifact nằm ngay
> trong mainline (`docs/evaluation/m17/w2b-patch/`). Kết quả **strict 1/3**, dừng
> vì chạm trần ngân sách **14/14 HTTP** nên ca thứ tư không kịp chạy. Ca **P3
> ĐẠT** (thiếu bảng → `insufficient_specification`, không xui tách truy vấn —
> đúng finding L5 đã vá). Hai ca không đạt: **P1** spec thừa một tầng `filter`
> làm rơi 2 dòng hiển thị, *nhưng* `empty→0 = 0` và `AVG 8.25 / counted 4`
> **đúng**; **P2** (năm tầng) hệ **từ chối** thay vì trả `ok` với spec thiếu
> tầng. Ở cả hai: `fp-sim 0`, `result-leak 0`, `generic-leak 0`,
> `semantic-loss 0` — **hệ không bịa dữ liệu**.
>
> Các lượt vá tiếp theo (PATCH2/PATCH3) **đã bị loại khỏi tuyến chính** và chỉ
> còn ở `archive/m17-w2b-deep-hardening`; **không merge lại**. Xem
> [`W2B_THESIS_SCOPE_DECISION.md`](evaluation/m17/W2B_THESIS_SCOPE_DECISION.md).
>
> **Backlog Analyze Integrity CÒN MỞ:**
> provenance/source-span của từng object/relation chưa xác minh — analyze
> hallucination CÓ ĐỊNH DANH vẫn có thể tạo false evidence; gate v2 chỉ chặn
> được dạng hallucination trừu tượng đã quan sát.
>
> Trước đó **Wave 1 XONG (offline+live)** — mở rộng 4 family hiện có bằng **4
> target mới**, catalog
> **14 → 18**, `CACHE_VERSION` **13 → 14** (một bump coherent Wave 1). **(A)**
> `algorithm.selection_sort` — variant thứ 3 của `comparison_sort` (gap
> `select_extreme_repeated` flip OWNED); engine `runSelectionSort` (event
> set_range/compare/assign_var/swap/mark/done, oracle `sort()` 5 case) +
> decision point + what-if free. **(B)** `binary.base_conversion` — đổi cơ số
> tổng quát {2,8,10,16} (gap `non_binary_base` flip OWNED); engine 3 chiến
> lược (chia-lấy-dư / trọng-số-vị-trí / hai-giai-đoạn), oracle
> `parseInt/toString` 12 cặp cơ số; cơ số ngoài {2,8,10,16} → unsupported.
> **(C)** `logic.boolean_dag` — mạch nhiều cổng {AND,OR,NOT,XOR} + bảng chân
> trị (mechanism MỚI `boolean_composition.bounded_gate_dag`); validator
> fail-closed (cycle/arity/dangling), oracle đệ quy độc lập mọi gán trị.
> **(D)** `network.graph_traversal` — BFS/DFS tổng quát (mechanism MỚI
> `breadth_first`/`depth_first`; `packet_routing` GIỮ là application variant);
> DFS mark-on-pop khớp đệ quy giáo khoa, oracle BFS/DFS độc lập, unreachable =
> kết quả hợp lệ. **(E)** classify.md 2d/2e/4c + rule-2-logic cập nhật; audit
> W1 rerun **68 case · 61/61 ok-archetype · near-miss 2/2 · 0 leak vô điều
> kiện · 17 REAL + 1 PARTIAL**; expectation overlay (changelog, M16 frozen
> KHÔNG đổi 1 byte); 6 artifact wave1 FROZEN pin. **INTENTIONAL_GAP còn 2**
> (quicksort `partition_recursive`, Dijkstra weighted). Offline sau W1: pytest
> **732** (2 skip, 1 deselect) · vitest **487/38** · build sạch. **LIVE SMOKE
> Wave 1 (user duyệt ≤6 case/≤20 HTTP, `gemini-2.5-flash`, production
> `run_pipeline`): 16/20 HTTP · 0 retry · 0 transient · 0 reclassify** — 4/4
> supported đúng trọn route+family+executor (selection_sort không bubble/
> insertion · base_conversion hex 3A→2 với config KHÔNG chứa đáp số LLM ·
> boolean_dag không hạ and_gate · graph_traversal **DFS** không về
> packet_routing); generic leak **0**, false-positive sim **0**, false refusal
> **0**; near-miss quicksort → `capability_gap` đúng. **Một lệch NON-BLOCKING
> (user chấp nhận + backlog):** base ngoài {2,8,10,16} (base-5) ra plain
> `unsupported` an toàn (0 false-sim, 0 leak, đúng phải từ chối) thay vì
> `capability_gap` — classify từ chối thẳng; cơ chế `non_binary_base` vẫn
> owned nên gap ở mức THAM SỐ không phải mechanism gate. **BACKLOG M17
> (NON-BLOCKING):** cân nhắc để base ngoài {2,8,10,16} → `capability_gap`
> (route base_conversion + validator phát gap) ở wave sau, vd khi làm coverage
> dashboard W3. Runner reproducible `scripts/live_smoke_m17_wave1.py` +
> artifact `live_smoke.json` + report. **"17 REAL + 1 PARTIAL":** PARTIAL =
> `generic.rule_scene` — nhãn heuristic audit cho target DUAL-AUTHORITY
> (computation rule-DAG + representation reveal/move), KHÔNG phải contract
> chưa đạt hay renderer yếu, KHÔNG ảnh hưởng learner (ship từ M7); backlog:
> tinh chỉnh heuristic PARTIAL cho khớp ý kế hoạch. **BACKLOG NON-BLOCKING
> (2 mục, cân nhắc W3):** (1) base ngoài {2,8,10,16} → `capability_gap`;
> (2) heuristic PARTIAL audit (dual-authority ≠ partial-authenticity).
> **Wave 1 COMPLETE (offline + live), closeout `f64fc67`.** Wave 2A
> (tree_traversal) mở sau.
>
> **Wave 0 XONG**
> (authenticity audit + learner error mapping, đo lường + trình bày — 0
> capability mới, 0 đổi routing/gate/prompt production, CACHE_VERSION giữ
> "13"): **(1)** `simulation/authenticity.py` — authenticity contract máy-đọc
> cho 14/14 AI-reachable target (state/trace/result/renderer requirements +
> `generic_allowed` + `near_miss_mechanisms`), nhúng vào
> `capability-descriptors.json` (sync-lock) + cross-lock vitest chạy ENGINE
> THẬT trên config thật. **(2)** audit matrix **55 case** SINH TỪ REGISTRY
> (`evaluation/authenticity_{fixtures,matrix,audit,artifacts}.py`) chạy qua
> production `run_pipeline` (bất biến #22): **46/46** ok-archetype đúng route
> (direct/paraphrase/changed-input 14+14+14, boundary 4) · 4/4 near-miss gap
> trung thực (`gate_mechanism_ownership`) · phân loại **13 REAL + 1 PARTIAL**
> (generic dual-authority) · 0 BROKEN · 0 chặn oan. (Số 56/47 trong commit
> message `f1cdce0` là LỖI TƯỜNG THUẬT — artifact máy-sinh là nguồn đúng;
> xem `docs/evaluation/m17/wave0/PROVENANCE.md`.) **(3)** regression duyệt
> cây: honest analyze → fail-closed ✔; probe adversarial (analyze khai man
> ownership) → **CONDITIONAL_LEAK_CONFIRMED**, PIN bằng test — **limitation
> ĐÃ BIẾT, user chấp nhận phương án (a)**: KHÔNG siết gate trong W0; claim
> đúng là (i) 0 generic leak VÔ ĐIỀU KIỆN trong audit hiện tại, (ii) luồng
> production PHỤ THUỘC analyze cung cấp `result_ownership` đúng — KHÔNG
> tuyên bố gate chống được analyze khai sai, (iii) adversarial đã ghi
> ledger + pin regression; limitation này PHẢI kiểm lại và đóng khi
> `tree_traversal` ship (Wave 2).
> **(4)** learner error mapping (`app/learner_messages.py` + biên API +
> `UnsupportedNotice` FE): học sinh không thấy token kỹ thuật/JSON path;
> `reason` kỹ thuật + `error_detail` giữ cho dev. **(5)** 6 artifact
> sync-locked `docs/evaluation/m17/wave0/`. Offline sau W0: pytest **682**
> (2 skip, 1 deselect) · vitest **443/38** · build sạch. Wave 1 CHƯA mở —
> chờ user duyệt báo cáo audit W0.

Cập nhật lần cuối: sau **M16 — Comprehensive End-to-End LLM Evaluation
(Task 1–7 + 5 fix review + live baseline, làm việc trên `main`, range
`c93a7a4..1cc0123`)**. Audit A–H (`a650783`) · design (`0766c1f`) · plan
(`6c84db1`). M16 là milestone **đo lường** — 0 capability mới, 0 executor mới,
0 thay đổi routing/gate/validator production (diff `pipeline.py` toàn milestone
= 2 dòng `_emit` observer-only, no-op khi `observer=None`), **FE production
diff = 0**, `CACHE_VERSION` giữ **"13"** (không prompt/schema production nào
đổi, 0 correction round). Hạ tầng đánh giá mới (`backend/app/evaluation/`):
**(1)** `m16_schema.py` — `M16Expectation` (archetype đóng 6 giá trị,
expected_family/route/gate/error_code máy-đọc, applicability flags) gắn qua
MỘT trường optional `EvalItem.m16` + `frozen_dataset_fingerprint()` (SHA-256,
PIN ở 3 nơi độc lập — frozen 30 case bất khả xâm phạm có khóa nội dung).
**(2)** `m16_record.py` + accessor observer mới + per-case budget-delta —
`M16CaseRecord` 29 field dựng THUẦN từ structured events/envelope (message
text không tham gia phân loại). **(3)** `m16_metrics.py` — 17 metric công
thức khóa trước khi chạy (denominator 0 → **N/A, không phải 0.0**; #17
parity đo trên MỌI evaluated case không lọc), failure taxonomy 15 category
structured-only, aggregation micro/macro/per-family/confusion-matrix,
applicability report máy-đọc — lớp SONG SONG, `EvalReport.metrics()` lịch sử
không đổi. **(4)** pool `m16` (`datasets/m16_catalog.py`) — **50 case** phủ
**14/14 AI-reachable public targets** (explicit + paraphrase mỗi target) +
**8/8 family** (valid-boundary + near-miss/gap mỗi family) + 2 cross-family
recovery + 2 authority control; admission kép (cũ + M16); coverage locks
đếm thật. **(5)** offline end-to-end: 50/50 case qua **production
`run_pipeline`** (bất biến #22) với provider scripted per-case + fault
injection (false-refusal/leak/transient) — hard correctness đạt trọn:
FP-sim **0/9** · generic-leak **0/5** · integrity **41/41** · parity
**50/50**; final_route 41/41 · initial_route 40/41 · recovery **1/1**
(offline controlled). **(6)** 5 artifact offline sync-locked
(`docs/evaluation/m16/`) + live runner `--label/--out/--resume-from`.
**LIVE BASELINE** (user duyệt 24 case/trần 80 HTTP, `gemini-2.5-flash`,
provenance `183eb1a`, artifacts `1cc0123`): **24/24 case đúng kỳ vọng · 66/80
HTTP · 0 retry · 0 transient · 0 correction** — hard correctness live: FP-sim
**0/9**, leak **0/5**, integrity **15/15**, parity **24/24**, token-leak **0**;
quality: initial/final route **15/15**, family **15/15**, variant **2/2**,
analyze-mechanism **7/7**, valid-spec-first **14/15** (scan 1 semantic retry),
false-refusal **0/15**, unsupported recall/precision **9/9**; reclassify 2/24
(hex-gap + cr-positional-fail — cả hai fail-closed ĐÚNG qua route-mismatch
recovery, không sinh generic config); recovery-success live **0/0 = N/A**
(không mismatch nào có supported route hợp lệ phát sinh — nhánh thành công đã
kiểm chứng offline 1/1, nhánh fail đã kiểm chứng fail-closed live). 14 HTTP
còn lại = unused budget. 5 limitation ghi trung thực ở §5-M16 (đại diện,
không thống kê; legacy plan-channel gap_gate nhiễu = BACKLOG — NON-BLOCKING
DIAGNOSTIC). Offline cuối: pytest **660** (2 skip, 1 deselect) · vitest
**406/33** · build sạch. **Capability expansion: NOT STARTED.** Xem hàng
**M16** ở §2.

> **M16 — Comprehensive End-to-End LLM Evaluation: COMPLETE.** Final
> whole-branch review (fable, `c93a7a4..HEAD`) 0 BLOCKING · claim boundary:
> *"AlgoSim đã được đánh giá đầu-cuối trên toàn bộ AI-reachable public
> capability catalog hiện có bằng production orchestration thật. Trong live
> suite gồm 24 case, hệ thống đạt final-route accuracy 15/15,
> valid-spec-first-attempt 14/15, unsupported recall 9/9, không sinh
> false-positive simulation và không để unsupported algorithmic request rò
> sang generic representation."* · scope: *"Kết quả áp dụng cho 14 capability
> thuộc 8 family hiện có trong phạm vi nguyên mẫu nghiên cứu; đây là targeted
> catalog-wide evaluation, không phải bằng chứng bao phủ toàn bộ chương trình
> Tin học THPT hoặc mọi cách diễn đạt tự nhiên."*

Trước đó: sau **M15 — Public Capability Contract Formalization &
Migration (Task 1–16, nhánh làm việc trên `main`)**. Design rev2
(`docs/superpowers/specs/2026-07-18-m15-*.md`, `cd1b8e5`); plan rev2
(`docs/superpowers/plans/2026-07-18-m15-*.md`, `b54e507`). Formalize toàn bộ
capability đã tồn tại (KHÔNG registry mới, KHÔNG selector mới ngoài sorting đã
có từ M14): **(1)** `mechanisms.py` — taxonomy cơ chế **canonical namespaced,
ĐÓNG, đủ 8 family** + `INTENTIONAL_GAP_MECHANISMS` registry (giá trị analyze-
exposed cố ý không target nào sở hữu, khai tường minh — không rơi tự do) +
alias **MỘT CHIỀU** legacy sorting → canonical (`canonical_mechanism` là
compatibility boundary DUY NHẤT; analyze vẫn giữ giá trị sorting cũ live-
verified ở M14, không đổi để khỏi vỡ hợp đồng LLM đã kiểm chứng). **(2)**
`owned_mechanisms` khai ở mức MEMBERSHIP (`FamilyMembership`, không phải mức
target) — đủ **14/14 entry CATALOG** (K1 lock kích hoạt đầy đủ ở Task 15).
**(3)** `config_contract_version` khai ở mức DESCRIPTOR (8× `algo-cfg-1` +
`scan-1.0` + `logic-cfg-1` + `binary-cfg-1` + `net-cfg-1` + `encap-cfg-1` +
`dsl-1.0`) — KHÔNG vào envelope, KHÔNG chạm Alembic/DB. **(4)** route-
consistency ordering trong `run_pipeline`: `classify_with_one_route_recovery`
chạy **≤ 1 reclassify BOUNDED, TRƯỚC** mọi route-dependent gate khác, với
**HAI mã lỗi tách bạch** — `ROUTE_MECHANISM_FAMILY_MISMATCH` (cross-family, ở
`classify_with_one_route_recovery`) khác `GATE_MECHANISM_OWNERSHIP` (cùng-
family nhưng cơ chế không sở hữu, ở `check_mechanism_consistency_for_target`,
chạy trên route CUỐI). **(5)** direct-route ownership gate — mechanism-
consistency nay sống trên CẢ HAI lifecycle (selector M14 + direct-entry M15).
**(6)** `ANALYZE_SCHEMA.prescribed_procedure` enum dẫn xuất
`analyze_exposed_values()` (+2 giá trị `positional_representation.*`). **(7)**
per-entry policy lock cho `algo-cfg-1` (required/bounds/normalize/annotation)
+ proof `binary_search` normalize-không-refuse dãy chưa sắp (BE+FE,
`docs/CORRECTNESS.md §9`). **(8)** suite eval `m15_wave1` (4 case mới: hex-gap
· octal-gap · binary-positive · binsearch-unsorted, + 2 case `m14_sorting` tái
dùng tag). `CACHE_VERSION` **= "13", HAI bump — ACCEPTED WITH EVIDENCE** (user
duyệt khi đóng M15): 11→12 = planned W1 contract/analyze/gate update (Task 10);
12→13 = live-discovered Binary Search classify-policy correction (Task 11
hotfix `f52f1a2` — bề mặt classify khoá "dãy ĐÃ SẮP" mâu thuẫn policy
normalize-not-refuse đã lock); lần bump thứ hai được GIỮ vì nó loại bỏ
false-refusal đã được chứng minh trong live Task 11 (nhật ký §1). **(9)** coverage matrix
(Task 16): `sorting` tốt nghiệp `PILOT` → `SUPPORTED` (claim boundary tự giới
hạn — targeted acceptance, KHÔNG phải bằng chứng thống kê); `binary_system`
note bổ sung control cơ số ≠ 2. Offline cuối: pytest **529 pass, 2 skipped, 1
deselected** · vitest **406 pass (33 files)** · build sạch · FE production
diff toàn M15 **= 0** (chỉ `capability-descriptors.json` sinh lại + 2 file
test). Live Task 11 (user duyệt ≤6 case/≤20 HTTP, nhật ký đầy đủ ở §1): run 1
**16 HTTP, 5/6** (hex/octal fail-closed qua recovery đúng; binary-positive
không chặn oan; sorting-paraphrase/selection đúng; binsearch-unsorted bị từ
chối oan ở classify — root cause CHỨNG MINH: bề mặt classify mâu thuẫn chính
policy đã lock) + hotfix prompt-only (`f52f1a2`, dùng ĐÚNG MỘT quyền prompt-fix)
+ rerun **3 HTTP OK** → **tổng 19/20 · 0 retry · 0 transient**. KHÔNG: selector
mới, đổi executor/renderer, Alembic, M16 (chưa mở). Xem hàng **M15** ở §2.

> **M15 — Public Capability Contract Formalization & Migration: COMPLETE.**
> Final whole-branch review (18 commit) ĐÃ DUYỆT · COMPLETE §R **13/13** (mục
> cache/version: ACCEPTED WITH EVIDENCE — xem đoạn CACHE_VERSION ở trên) · bất
> biến **#23 ĐÃ ĐĂNG** (`ARCHITECTURE_MAP.md` §5) · 13 minor findings giữ
> **BACKLOG** có ghi nhận (ledger) · claim boundary sau M15 GIỮ NGUYÊN.
> HEAD trước close: `6e31a2c` · range M15: `b54e507..6e31a2c` (trước commit
> đóng) · offline: pytest **529** · vitest **406/33 files** · build sạch ·
> live: **19/20 HTTP · 0 retry · 0 transient · 1 approved prompt-only fix** ·
> FE production diff **= 0**. **M16: NOT STARTED.**

Trước đó: sau **M14 — Capability Family Formalization & End-to-End
Pilot (Task 1–14, nhánh làm việc trên `main`)**. Offline: pytest **450 pass, 1
deselected** · vitest **403 pass (32 files)** · build sạch. Live pilot
`m14_sorting` (user duyệt ngân sách ≤16 call/≤4 case) **ĐÃ CHẠY — 4/4 OK, 11 HTTP,
0 retry, 0 transient**: sorting formalize thành family selector LLM-facing +
adapter về executor bubble/insertion HIỆN CÓ; final_route/family_selection/
variant_selection = 1.0; selection-sort → từ chối trung thực; token
`comparison_sort` KHÔNG lọt vào envelope. Eval NAY đi chung `run_pipeline` (bất
biến #22), `_simulate_with_metrics` đã retire. Xem hàng **M14** ở §2. Trước đó:
sau **M13-SOUNDNESS Task 1–14 + hotfix role-compat — ĐÃ MERGE FF vào `main`**
(`db5ba3f`→`e8c9dba`). Task 14 live smoke ĐÃ CHẠY (user
duyệt, 37 HTTP tổng + 4 HTTP rerun xác nhận hotfix); live phát hiện MỘT false
positive M13 (`boolean → value_box` bị check role từ chối oan) và đã VÁ bằng
role compatibility một chiều `logical→numeric` — canonical rerun ✅ OK. Offline
cuối: pytest **377** · vitest **393** · build sạch. Xem hàng **M13-SOUNDNESS**
ở §2 + known-issue 7f. Trước đó: sau **M12-AI-SCAN** (tiếp nối
M12-SCAN-PROOF trên main) — M11: LLM compose chuỗi rule boolean lồng qua trung
gian trên đường generic (validator cấm trùng target 2 tầng, probe
`nested_boolean`, vòng lặp biến tự do từ chối trung thực); M12: scan-interpreter
tất định (engine sở hữu) tái tạo đúng ngữ nghĩa 4 engine specialized
single-pass qua spec khai báo bounded — KHÔNG ngôn ngữ lập trình ẩn, LLM/UI của
scan HOÃN có chủ đích.

> ## ✅ M8 SLICE 1+2 HOÀN THÀNH — SCOPE FREEZE §5b VẪN HIỆU LỰC CHO PHẦN CÒN LẠI
>
> - **M8 đã chứng minh tuyên bố kiến trúc**: cùng config → cùng engine tất định →
>   cùng state/timeline/action/prediction → renderer 2D **hoặc** 3D
>   (`network.packet_routing` là PoC duy nhất, đúng kế hoạch).
> - **3D là renderer, không phải domain**: không có simulation_id "_3d" nào,
>   không fork engine (bất biến #16, `ARCHITECTURE_MAP.md §5`).
> - **M8 Slice 3 (mạng phân tầng) HOÃN post-M8**: cần năng lực tất định MỚI
>   (đóng gói/mở gói qua tầng — biến đổi trạng thái PDU), không fake bằng
>   reveal-boxes (xem §6).
> - M7.15 (geometry) vẫn KHÔNG nằm trong kế hoạch; danh sách §5b vẫn áp dụng
>   cho mọi thứ không phải blocker renderer.


## W4B-2Z — mô hình web có ràng buộc + phiên đang mở (2026-08-11)

- **Danh mục**: 23 target · 12 family. Mới: `web.style_model`
  (`FamilyId.WEB_PRESENTATION`, `ResultAuthority.REPRESENTATION`, cơ chế
  `web_presentation.bounded_style_properties`). `CACHE_VERSION = "26"`.
- **Baseline test**: backend 1139 passed / 2 skipped · frontend 1182 passed
  (83 file) · `npm run build` xanh.
- **Hợp đồng miền giá trị web**: `web_style_domain()` là NGUỒN, đi ra
  `capability_descriptors()["bounded_domains"]`; `props.ts` là bản sao và bị
  sync-lock so từng giá trị (`web/contract-parity.test.ts`).
- **Phiên đang mở**: `sessions` + `activeSessionId` trong `state/store.ts`;
  chuyển phiên là khôi phục thuần (0 `fetch`, 0 `init`). Khác Lịch sử.
- **`code_experiment` vẫn DEFERRED** — không có đường thực thi mã tuỳ ý.

> ⚠️ **Đoạn W4B-2Z ở trên là LỊCH SỬ.** Baseline test, số mẫu và cách trình bày
> phiên trong đó mô tả trạng thái tại thời điểm wave đó đóng. Trạng thái HIỆN
> HÀNH ở mục **W4B-3B…3D** cuối file. Cụ thể: cột phiên trái đã bị thay bằng
> hàng tab, và 23/23 target nay có mẫu offline.

### Giới hạn CÒN LẠI (đo được, không phải "chưa kịp làm")

- ~~`experimentTrigger` vẫn là một dải dưới mô hình ở 8 target thuật toán.~~
  **ĐÃ ĐÓNG ở W4B-3A** — xem mục dưới.
- **`CURRICULUM_SUPPORT_PARTIAL`** giữ nguyên. **`LEARNER_IMPACT_NOT_EVALUATED`**
  giữ nguyên.

## W4B-3A — tách KHÁM PHÁ khỏi THỬ THÁCH, gỡ dải cổng (2026-08-11)

**Vấn đề thật không phải chỗ đặt cái nút.** Một nút tên "Thí nghiệm" do CHÍNH
renderer miền dựng mở CÙNG LÚC hai thứ khác loại: vùng cam kết (nộp qua
`predict.check` — engine PHÁN đúng/sai) và kéo-thả/sửa tôpô (đi qua
`module.apply` — KHÔNG ai phán gì). Một cửa cho hai việc khác loại dạy học sinh
rằng kéo một cột cũng là "trả lời đúng/sai".

Dải `experimentTrigger` chỉ là **triệu chứng**: shell chỉ dựng lối vào Thử thách
khi module KHÔNG tự bày cam kết trên sân khấu (`presentedInStage`), nên đúng ở
những bước có vùng cam kết thì họ thuật toán không có cửa nào của shell và phải
tự dựng lấy — cái nút tự dựng ấy nằm ngay dưới sân khấu.

- **Phân vai sau wave**: store sở hữu `challengeOpen`/`exploreOpen` (mù domain,
  theo phiên) · `SimulationControls` là chủ sở hữu **DUY NHẤT** của lối vào phụ ·
  module cấp CÂU MỜI (`predict.entry` / `explore.entry`, dẫn xuất từ config đã
  validate) · renderer miền dựng bộ điều khiển và phát `SimAction` · engine vẫn
  là bên duy nhất phán đúng/sai.
- **`presentedInStage` trả về đúng việc của nó**: chặn `PredictionBar` khi sân
  khấu đã hỏi rồi — KHÔNG chặn cửa. Một cửa, nhiều nhất một bề mặt.
- **Nút MỜ chứ không biến mất** ở bước không dùng được: số bước mời được chỉ
  4/13 (binary_search) → 21/40 (bubble_sort), nên tự gỡ mình là nhấp nháy mỗi
  lần bấm Tiến. Cùng thành ngữ `:disabled` với transport ngay cạnh.
- **Đo được (Chrome thật, 4 bề rộng 1920/1536/1366/768)**: 8 target thuật toán
  `bands 3 → 2`, `network.packet_routing` `2 → 1`; **0 dải `experiment-trigger`**
  ở mọi target/bề rộng; 0 tràn ngang; mở Thử thách ≤1 bề mặt cam kết.
  Artifact: `docs/evaluation/m17/w4b3a-after/`.
- **Protocol parity ĐÓNG bằng bằng chứng trình duyệt** (trước đây PARTIAL): đổi
  2D↔3D ở bước 3/9 của `protocol_encapsulation` giữ nguyên cursor, stepCount và
  `getExplainContext` từng byte; quay lại 2D khôi phục đúng.
- **Phiên**: chính sách khai tường minh — Khám phá **theo phiên** (khôi phục khi
  quay lại, KHÔNG rò sang phiên mới, đóng khi `resetSim`). A→Khám phá→B→A giữ
  ĐÚNG object state cũ, **0 `fetch`**.
- **Ma trận AFTER toàn danh mục** (`after-matrix.md`, sinh từ nguồn): 23 target ·
  12 family. Đo được trong trình duyệt **14/23** (9 target chưa có bài mẫu
  offline ⇒ chỉ đọc được năng lực KHAI BÁO — đếm riêng, không cộng vào). Thao
  tác trực tiếp **11 đo được** (7 sau cổng Khám phá + 4 luôn mở trên sân khấu),
  cam kết thuật toán **8 đo được**, khai `predict` **11**.
- **Bảng hỗ trợ theo chương trình** (`curriculum-support.md`, trục `SupportKind`
  mới): 25 đơn vị — 8 SUPPORTED_INTERACTIVE · 2 SUPPORTED_TRACE · 1
  SUPPORTED_BOUNDED_ARTIFACT · 5 PARTIAL · 2 UNSUPPORTED · 7
  NOT_SIMULATION_SUITABLE. **`CURRICULUM_SUPPORT_PARTIAL` GIỮ NGUYÊN** (7 đơn vị
  in-scope còn dang dở) — và nay có test canh, không phải lời hứa.
- **Tiêm lỗi đã chứng minh ĐỎ 8/8** (dải quay lại · Khám phá phụ thuộc chuỗi
  ngữ cảnh · renderer bỏ qua `apply` · renderer tự phán đúng/sai · rò chế độ
  A→B · chuyển phiên qua `loadEnvelope` · phá parity 2D/3D · màu web lậu).
  **Ba guard hụt bị phát hiện nhờ chính đợt tiêm lỗi và đã vá**: quét ngữ-cảnh
  toàn kho không đi qua `components/` và bỏ lọt optional chaining; `ArrayView`
  viết lại id trước khi nộp mà không guard nào thấy.

## W4B-3B…3D — sân khấu lấy lại bề ngang · sự thật ở bước cuối · hết điểm mù (2026-08-12)

**Đây là mục TRẠNG THÁI HIỆN HÀNH.** Mọi mô tả trình bày phiên ở các mục W4B-2Z
trở về trước là lịch sử.

### 3B — điều hướng phiên thôi lấn sân khấu

Cột phiên trái (`SessionRail`, 208px) có `grid-area: rail` trải qua **cả** hàng
`center` lẫn hàng `controls`, nên nó bóp sân khấu VÀ bóp dải điều khiển đúng
ngần ấy. Hai triệu chứng, một nguyên nhân.

| bề rộng | sân khấu 1 phiên → 2 phiên | dải điều khiển |
|---|---|---|
| 1920 | 1672 → **1448** px (dời phải 224) | 1 → **2** dòng |
| 1536 | 1460 → **1236** px (dời phải 224) | 1 → **2** dòng |
| 1366 | 1290 → **1066** px (dời phải 224) | đã 2 dòng sẵn |

Kèm một **lỗi chức năng**: `+ Mô phỏng mới` chỉ nằm trong đầu cột, mà cột ẩn khi
<2 phiên ⇒ đang mở đúng một bài thì **không có đường mở bài thứ hai** (đo được
`newSession=false` ở cả 4 bề rộng).

Nay: `SessionTabs` là hàng ngang trên sân khấu, chỉ dựng khi ≥2 phiên, tối đa 4
tab rồi gộp `+N` (danh sách bung ra liệt kê đủ phiên); ≤860px đổi thành bộ chọn
`Mô phỏng: … ▾` bằng CSS (không đọc `window` trong JS). Lối vào `Mô phỏng mới`
về header. **Sân khấu nay RỘNG BẰNG NHAU ở 1, 2 và 6 phiên** tại cả 4 bề rộng.
Nhãn đầy đủ của Khám phá/Thử thách rút còn hai chữ trên dải điều khiển (câu đầy
đủ + teaser vào `aria-label`/`title`, khung giải thích hiện khi MỞ chế độ) ⇒
1366 còn **1 dòng**, 768 còn **2**. Kiến trúc phiên KHÔNG đổi.

### 3C — sự thật ở bước cuối

`insertion_sort` ở bước 33/33 tuyên bố đã sắp xong nhưng vẫn vẽ quân bài 2 ngoài
dãy + ô trống nét đứt. **Renderer không sai** — nó vẽ đúng snapshot có thẩm
quyền. `TraceBuilder` chỉ có `setVar`, nên biến mô tả thao tác ĐANG DỞ
(`gia_tri_chen`, `vi_tri_cuc_tri`) sống tới hết trace và bước `done` tự mâu
thuẫn. Thêm `clearVar`, gỡ biến ĐÚNG LÚC thứ nó mô tả hết tồn tại. Bất biến khoá
cho cả họ sắp xếp × 2 chiều, cộng một bất biến mạnh hơn: **hold luôn phải có
bước chèn phía sau**, không bao giờ treo.

### 3D — hết điểm mù bằng chứng

14/23 target có mẫu offline ⇒ **9 target chưa từng được đo trong trình duyệt**.
Nay 23/23 có mẫu (config lấy từ chính fixture đã validate ở
`authenticity-cross-lock`). Ba lỗi lộ ra ngay khi có mẫu:

- `base_conversion`: panel Giải thích không đọc cursor — đọc y hệt ở bước 1 và
  bước cuối;
- `tree.traversal`: in `Thứ tự thăm (engine)` — từ vựng máy trên bề mặt học sinh;
- `LibraryView.GROUP_ORDER` thiếu `tree`, mà danh sách đó vừa là thứ tự vừa là
  BỘ LỌC ⇒ mẫu công khai của `tree.traversal` render vào không nhóm nào và biến
  mất khỏi Thư viện, im lặng. Khoá lại theo TẬP MIỀN (đếm chỉ đỏ khi miền bị
  quên tình cờ có mẫu công khai);
- `algorithm.scan` lặp kết quả ở bước cuối (`dupTerminal` cả 4 bề rộng) — dùng
  lại `processLeadOf`, không viết luật thứ hai.

**Bốn tập KHÁC NHAU, không đánh đồng** (§9): registry **23** · học-sinh-tới-được
(`ai_reachable_public`) **23** · nội bộ **0** · có mẫu offline **23** · trong Thư
viện học sinh **22** (`algorithm.scan` cố ý ở ngoài: có mẫu để ĐO, không quảng bá
vì nó trùng nghĩa với tám bài chuyên biệt) · **đo được trong trình duyệt 23**.

**Đo bố cục toàn danh mục**: 23 target × 4 bề rộng = **92 phép đo**,
`experimentTrigger` **0**, trùng nghĩa bước cuối **0**.

**Ma trận AFTER** (`docs/evaluation/m17/w4b3d-after/after-matrix.md`): 23 target ·
12 family · **đo được 23/23, không còn cột "chỉ khai báo"**. Thao tác trực tiếp
**13 đo được** (8 sau cổng Khám phá + 5 luôn mở trên sân khấu), cam kết **9**,
khai `predict` **11**.

**Bảng chương trình** (`curriculum-support.md`): 25 đơn vị — 8
SUPPORTED_INTERACTIVE · 2 SUPPORTED_TRACE · 1 SUPPORTED_BOUNDED_ARTIFACT · 5
PARTIAL · 2 UNSUPPORTED · 7 NOT_SIMULATION_SUITABLE.
**`CURRICULUM_SUPPORT_PARTIAL` GIỮ NGUYÊN** (7 đơn vị in-scope còn dang dở).
**`LEARNER_IMPACT_NOT_EVALUATED` GIỮ NGUYÊN.**

## W4B-3E…3F — dải điều khiển có bố cục · bài HTML là một trang (2026-08-12)

### 3E — dải điều khiển

Đo trước khi sửa: khoảng hở **633px** giữa hai phần tử CÙNG hàng @1920 (1536:
421 · 1366: 251). Hở **scale theo bề rộng màn hình** ⇒ nó là CHỖ THỪA, không
phải khoảng cách ai chọn. Nguyên nhân: `.speed-control { margin-left:auto }` —
một THÀNH VIÊN quyết bố cục cả hàng, mọi thứ sau nó bị đẩy theo.

Nay ba VÙNG tường minh (transport · đặt lại+bước · tốc độ+năng lực) và thanh tua
nằm TRONG hàng với `flex:1` để **ăn hết chỗ thừa** — ba vùng thôi thì chỉ DỜI
chỗ trống (633 → 796). Kết quả: desktop **1 hàng, hở 16px**; 768 **2 tầng**
(trước 3). Chữ trong dải 76 → 48; câu phím tắt và câu "mô phỏng khám phá" rời
khỏi hàng nhưng **còn nguyên ở `aria-label`**.

**Cùng lỗi ở chủ sở hữu thứ hai**: domain generic dùng lại class
`.player-controls` và có `marginLeft:"auto"` trên MỘT NÚT — hở **1390px** @1920,
lớn hơn lỗi gốc, và guard chỉ-quét-CSS không thấy. Guard nay đi qua MỌI file
dựng `.player-controls`.

### 3F — bài HTML/CSS

Ảnh "Trang giới thiệu (từng bước)" **không phải** `web.style_model` — nó là
`generic.rule_scene` chạy `reveal_sequence` (khung → tiêu đề → đoạn văn). HTML
không hình thành theo thời gian, nên đó là trục thời gian BỊA — đúng thứ W4B-2Z
đã gỡ cho phần CSS rồi bỏ sót phần cấu trúc. Đo được: **fill 37% bề ngang**.

`web.style_model` không nhận nổi bài đó vì nó chỉ mô hình MỘT khối chữ. Nay mô
hình là một TRANG: `.trang` chứa `h1` + `p`, tiêu đề có màu/cỡ riêng. Hợp đồng
backend đi trước (nguồn), rồi mirror + descriptor + **`CACHE_VERSION` 26→27**.
Kết quả đo: **fill 97% × 93%** @1920, và bảng CSS có **ba bộ chọn** thật.

Mẫu công khai của generic nay là `gen-rule-library` (quy tắc mượn sách — công
tắc thật, luật thật, không bước giả).

**Toàn danh mục**: 23/23 target đo được, `experimentTrigger` **0**, trùng kết
quả cuối **0**, không tràn ngang ở cả 4 bề rộng.

**Tiêm lỗi lộ ra ba guard hụt** (đều đã vá): sân khấu web tụt về một ô mà suite
vẫn xanh · renderer dựng nguồn sự thật riêng (`artifact_reflects_style_state`
chưa ai kiểm) · renderer ghi thẳng vào state, bỏ qua `module.apply` (bất biến #6).

## 1. Baseline

| | |
|---|---|
| pytest | **1106 pass, 2 skipped, 1 deselected** (đo lại 2026-07-26 sau W3; 0 API call thật — guard là bằng chứng) |
| vitest | **664 pass / 49 file** (đo lại 2026-07-26 sau W3-VR; 0 network call) |
| catalog conformance | **22 target · conformance 0 · ownership 0 · parity 0 · PASS** (`scripts/catalog_runtime_matrix.py`, 2026-07-26) |
| audit bố cục | `npm run audit:layout` — **4/4 route sạch** (đo lại tại Task 13: vẫn 4/4 — M13 chỉ đổi nguồn text nhãn, không đổi CSS/layout; Chrome thật, CDP; đã chứng minh bằng tiêm lỗi giả ở M9-UX7) |
| build | `tsc -b && vite build` sạch (đo lại 2026-07-25) — bundle chính ~357KB; chunk Three.js 544KB **code-split**, chỉ tải khi bấm 3D |
| nghiệm thu M10 | CDP browser thật (SwiftShader WebGL) — **15/15**: 2D đóng gói→truyền→mở gói→giao đúng payload; dự đoán sai → phản hồi tất định; 3D canvas dựng thật + caption; parity 2D↔3D; **0 gọi /api/analyze\|edit\|explain** |
| Docker | `docker compose up -d --build` OK (backend :8000 + Postgres) |
| Live smoke gần nhất (M7.14T) | 8/8 OK · 22 HTTP request · 0 retry · 0 transient · `gap_gate_recall = 1.0` · không false positive |

**Không chạy full live eval theo mặc định.**

### Nhật ký live call (ghi chính xác, không ghi khoảng)

| Khi nào | Suite/case | HTTP request | retry | transient |
|---|---|---|---|---|
| M7.14T | smoke suite (8 đề) | **22** | 0 | 0 |
| M7.14D — run A (code trước fix empty-ops) | 3 case edit: structural+đoạn văn (1) · structural+"thêm điểm P1" (2) · spatial+"thêm D nối A" (1) | **4** | 0 | 0 |
| M7.14D — run B (sau fix, chỉ case 2) | LLM đề xuất `node` trước → policy reject → retry → từ chối | **3** | 0 | 0 |
| M7.14D — run C (sau fix, chỉ case 2, đo lại) | LLM từ chối ngay lần đầu | **1** | 0 | 0 |
| **Tổng M7.14D** | | **8** | 0 | 0 |
| M8-PRE (S3) | verify có mục tiêu: đề "phân tích hệ thống" + guard quan hệ đời thường; 3 lần diag đếm object/attempt; 1 lần probe schema | **55** | 6 | 9 (1 ReadTimeout + 8× HTTP 503 "high demand" ở lần chạy cuối) |
| M8-PRE (plan C) | inspect composition (2 dump) + verify sau nén (V1 + V2) | **15** | 1 | 1 |
| M8-PRE (stability smoke) | đề "phân tích hệ thống" × **5 lần hoàn tất** | **19** | 2 | 2 (429/5xx — retry nuốt trọn, **0 run bị hỏng**) |
| **M8 (Slice 1+2)** | frontend-only: kiến trúc renderer + network 3D; nghiệm thu bằng bài mẫu offline trên browser thật | **0** | 0 | 0 |
| **M9-UX1..7 · M10-3D-PED · DB-HARDEN-2** | frontend/UX + engine + DB infra — offline-first, không đụng hợp đồng AI | **0** | 0 | 0 |
| **M10-AI-ROUTE — run 1** (menu classify mới, prompt CŨ) | suite `m10_route` (5 case: 2 encap + mixed + routing tương phản + unsupported) | **18** | 6 | 6 (429) — **2/5 đúng**: 2 đề encap rơi về generic, TCP nâng cao ép về generic |
| **M10-AI-ROUTE — run 2** (sau vá classify.md) | cùng 5 case | **19** | 5 | 5 (429) — **5/5 đúng**: classification 1.0, unsupported recall/precision 1.0, valid_spec_first_attempt 1.0, 0 retry validation |
| **Tổng M10-AI-ROUTE** | | **37** | 11 | 11 |
| **M11 — baseline** (prompt CŨ) | suite `m11_compose`, 3 case đầu (canonical + access + paraphrase) | **10** | 0 | 0 — canonical ✅ 8/8 chuỗi 2 rule (câu hỏi trung tâm trả lời CÓ ngay baseline) · access ✅ · paraphrase ❌ probe đếm 7 "nguồn" (label trang trí có value → lỗi PROBE, không phải LLM) |
| **M11 — chẩn đoán** | 1 case paraphrase, dump spec | **3** | 0 | 0 — spec lần này HOÀN HẢO (2 rule chuỗi, 3 toggle) → xác nhận lỗi probe + bất ổn định lấy mẫu |
| **M11 — rerun sau vá probe** (prompt CŨ) | trọn suite 5 case | **20** | 0 | 0 — canonical ✅ · NOT ✅ 4/4 · access ❌ ép PHẲNG 1 rule · paraphrase ❌ invalid 3 attempt · **loop-gap ❌ bị ép về generic (misroute có bằng chứng)** |
| **M11 — sau vá contract+analyze+classify** | trọn suite 5 case | **17** | 0 | 0 — access ✅ · paraphrase ✅ 8/8 (k=1 về generic, đúng quyết định) · **loop-gap ✅ gate=fired, unsupported recall/precision 1.0, 0 false positive** · canonical ❌ spec chết tương tác (switch không value — probe bắt đúng) · NOT ❌ misroute and_gate |
| **M11 — rerun có mục tiêu sau vá ranh giới and_gate** | NOT + a-and (đối chứng) | **7** | 1 | 1 (429) — NOT ✅ generic 4/4 · a-and ✅ vẫn specialized (không over-correction) |
| **Tổng M11** | 16 lượt case logic | **57** | 1 | 1 |
| **M12-AI-SCAN — smoke** (prompt mới) | suite `m12_scan` (4 case: flagship first-above + count/linear đối chứng + loop-gap M11) | **11** | 0 | 0 — **4/4 OK**: flagship → `algorithm.scan` spec valid lần đầu + semantic bounded_scan PASS (dừng đúng vị trí 4); count_if/linear_search không bị nuốt; loop-gap vẫn unsupported (gate fired). Lưu ý: `gap_gate_false_positives` ghi flagship (analyze gắn numeric_threshold — metric-only, xem §5) |
| **M12-AI-SCAN — rerun flagship sau vá carve-out analyze** | 1 case | **3** | 0 | 0 — vẫn OK routing + semantic; gate VẪN fired (salience prompt dài — dừng đuổi theo bài học M8-PRE S3, ghi known-issue) |
| **Tổng M12-AI-SCAN** | 5 lượt case logic | **14** | 0 | 0 |
| **M13 Task 14 — tier 1** | `cap-dijkstra-gap` (1 case, trần 15) | **2** | 0 | 0 — ✅ `unsupported`, gate=fired, KHÔNG sinh generic config; classification/unsupported recall/precision đều 1.0; 0 gap-gate false positive |
| **M13 Task 14 — tier 2a** | trọn suite `m11_compose` (5 case, trần 20) | **17** | 0 | 0 — **4/5**: access ✅ · paraphrase ✅ · NOT ✅ (bảng chân trị hợp thành đúng toàn bộ, semantic 1.0) · loop-gap ✅ gate=fired · **canonical ❌ `unknown_primitive` invalid 3 attempt** |
| **M13 Task 14 — rerun chẩn đoán canonical** | 1 case (trần 6) | **5** | 0 | 0 — ❌ CÙNG chữ ký `unknown_primitive` → stop-condition, dừng chẩn đoán live (xem §5, known-issue 7f) |
| **M13 Task 14 — tier 2b** | trọn suite `m12_scan` (4 case, trần 15) | **13** | 0 | 0 — **4/4** ✅: flagship → `algorithm.scan` (valid sau retry, semantic bounded_scan PASS) · count_if/linear_search giữ route chuyên biệt · loop-gap unsupported gate=fired; specialized_selection 1.0, 0 FP |
| **Tổng M13 Task 14** | 11 lượt case logic | **37** | 0 | 0 (trần tuyệt đối 39 — không vượt; MỌI failure là semantic, KHÔNG có lỗi 429/network) |
| **M14 Task 13 — live pilot** (user duyệt ≤16 call/≤4 case) | suite `m14_sorting` (bubble explicit · insertion explicit · bubble paraphrase-CƠ-CHẾ · selection-sort near-miss) | **11** | 0 | 0 — **4/4 OK**: classification 1.0, final_route/family_selection/variant_selection 1.0 (n=3), unsupported recall/precision 1.0, valid_spec_first_attempt 1.0. 3 sorting positive: classify → token `algorithm.comparison_sort` → adapter → envelope CONCRETE (bubble/insertion) đúng; token KHÔNG lọt vào envelope. selection-sort → từ chối ngay ở classify (mechanism gate là backstop, không cần fire live — offline đã khoá). Paraphrase-theo-cơ-chế (không nêu tên "nổi bọt") → đúng bubble → định tuyến theo CƠ CHẾ. Không prompt-fix (4/4 lần đầu) |
| **M15 T11 — run 1** (user duyệt ≤6 case/≤20 HTTP) | suite `m15_wave1` (hex-gap · octal-gap · binary-positive · binsearch-unsorted · sorting-paraphrase · selection-near-miss) | **16** | 0 | 0 — **5/6**: hex/octal → unsupported KHÔNG generic config (classify chọn generic nhưng recovery mismatch fail-closed — mỗi đề +1 reclassify; mechanism_gate không cần fire); binary-positive ✅ không chặn oan; sorting-paraphrase ✅ token→concrete (family/variant 1.0, n=1); selection ✅ gate=fired · **binsearch-unsorted ❌ classify trả unsupported** — root cause CHỨNG MINH: bề mặt classify (description + classify.md 2c) khoá "dãy ĐÃ SẮP", mâu thuẫn policy normalize-not-refuse đã lock (CORRECTNESS §9); LLM từ chối ĐÚNG theo prompt cũ |
| **M15 T11 — rerun sau hotfix prompt-only** (`f52f1a2`: vá description+2c, CACHE 12→13; dùng đúng MỘT quyền prompt-fix) | 1 case `m15-binsearch-unsorted` (qua `--case` mới) | **3** | 0 | 0 — ✅ `algorithm.binary_search`, valid spec lần đầu, final_route 1.0; chuẩn hoá + chú thích đảm bảo TẤT ĐỊNH bởi validator (lock Task 8) vì envelope chỉ phát sau `validate_algorithm_config` |
| **Tổng M15 T11** | 7 lượt case logic | **19** | 0 | 0 (trần duyệt 20 — không vượt; 0 lỗi transient/mạng) |
| **M16 — live baseline** (user duyệt ≤24 case/trần 80 HTTP, `--dataset m16 --suite m16_catalog_live --label baseline`) | 24 case (14 positive đủ 14 target · 8 near-miss đủ 8 family · 2 recovery control) | **66** | 0 | 0 — **24/24 đúng kỳ vọng, 0 correction round**: 15 envelope ok (initial/final route 15/15, valid-spec-first 14/15 — scan 1 semantic retry), 9 từ chối trung thực (recall/precision 9/9, FP-sim 0/9, leak 0/5); hex-gap + cr-positional-fail đi đường classify→generic → route-mismatch → 1 reclassify vẫn lệch → fail-closed (đường phòng thủ hợp lệ đã khai trong notes); token-leak 0; trace + artifacts pre-fix commit `1cc0123`; 14 HTTP unused |

**TRẠNG THÁI của đề "phân tích hệ thống" — sau STABILITY SMOKE 5 lần chạy hoàn tất:**
- Định tuyến: ✅ **đã sửa** — **0/5** lần `unsupported` im lặng; **5/5** vào `generic.rule_scene`.
- Vai trò hệ thống: ✅ **5/5** có đủ actor + process + data_store (4/5 có cả input/output).
- Chiều luồng dữ liệu: ✅ **39/39 edge (100%) có `directed`** — cổng suy tất định hoạt
  động ổn định (LLM vẫn không tự khai, đúng như đã đo).
- Kết quả: ✅ **5/5 validate end-to-end**, đều là `executable_simulation`
  (`reveal_sequence` 5/5; `move_along_path` 3/5) — **result mode khai báo trung thực**.
- Ngân sách object: **KHÔNG cảnh hợp lệ nào cần > 20** (spec cuối: 13, 14, 15, 17, 17).
  Khẳng định lại kết luận plan C: **không nâng hạn mức, không cần capability-aware budget.**
- **Nén dư thừa: fired 0/5.** Nó là LƯỚI AN TOÀN, không phải thứ đang gánh tính năng.
  Ở run 4 có một bản nháp 27 object bị từ chối vì hạn mức — nén **cố ý KHÔNG cứu** vì
  các label đó **không trùng hệt** nhãn inline nào (không có dư thừa chứng minh được),
  đúng thiết kế bảo thủ; **retry của pipeline** phục hồi (27 → 16 → 15 ✅).
- Cách diễn đạt ĐƯỢC PHÉP: *"Repeated targeted live verification showed consistent
  end-to-end success across a five-run stability sample."*
  **CẤM** nói: ~~"đã chứng minh tin cậy về mặt thống kê"~~ (n = 5, không đủ).

**M8-PRE (S3) — điều live PHÁT HIỆN ra mà offline không thấy được:**
1. LLM dựng đúng `actor→process→data_store` trong `from`/`to` nhưng **KHÔNG BAO GIỜ khai
   `directed`** — kể cả khi contract yêu cầu tường minh, kể cả sau khi bị từ chối kèm
   lý do (3 attempt liên tiếp). Probe riêng chứng minh **schema KHÔNG phải thủ phạm**
   (gọi trực tiếp thì Gemini phát `directed: true` bình thường) → **không phải
   anti-pattern #1**, mà là *salience* trong prompt dài.
   → **Xử lí đúng kiến trúc: SUY tất định ở server**, không đi xin LLM. Chiều đã nằm
   sẵn trong `from`/`to`; validator (cả hai tầng) tự gắn `directed` cho cạnh nối hai
   node vai trò hệ thống. Không đụng hình học, không đụng topology mạng (2 chiều).

Case 2 tốn 1 hoặc 3 request tùy LLM có thử đề xuất `node` trước hay không —
**cả hai đường đều ra đúng phán quyết** `policy.operation_not_allowed`.
M7.14D.1 là **UI-only: 0 live call**.

## 2. Milestone đã hoàn thành (có commit)

| Milestone | Commit | Nội dung |
|---|---|---|
| **M16 — Comprehensive End-to-End LLM Evaluation (Task 1–7 + live baseline)** | `c93a7a4..1cc0123` | **Đánh giá đầu-cuối toàn bộ AI-reachable public catalog (14 target / 8 family) bằng CHÍNH production `run_pipeline` — milestone đo lường thuần: 0 capability/executor mới, routing/gate/validator không đổi (diff pipeline = 2 dòng `_emit` observer-only), FE diff = 0, CACHE_VERSION giữ "13", 0 correction round.** Hạ tầng: `m16_schema.py` (M16Expectation — archetype đóng 6 giá trị, expected route/gate/error_code máy-đọc; `frozen_dataset_fingerprint` PIN 3 nơi) · `m16_record.py` (M16CaseRecord 29 field từ structured events; observer accessor reclassify + emit đối xứng direct-gate + per-case budget delta) · `m16_metrics.py` (17 metric công thức KHÓA, denominator-0 → N/A, taxonomy 15 category structured-only, micro/macro/per-family/confusion — SONG SONG, metric lịch sử không đổi) · pool `m16` 50 case (admission kép, coverage lock đếm thật: 14/14 explicit+paraphrase, 8/8 boundary+near-miss, 2 recovery, 2 authority control; 24 live-eligible) · offline e2e 50/50 qua production pipeline với scripted provider + fault injection — hard correctness **FP-sim 0/9 · leak 0/5 · integrity 41/41 · parity 50/50**, final_route 41/41, recovery 1/1 (offline controlled) · 5 artifact offline sync-locked + 5 artifact live (`docs/evaluation/m16/`) · live runner `--label/--out/--resume-from`. **Live baseline (user duyệt ≤24/≤80)**: 24/24 · 66 HTTP · 0 retry · 0 transient — initial/final route **15/15**, family **15/15**, variant **2/2**, analyze-mech **7/7**, valid-spec-first **14/15**, semantic 1/1, false-refusal **0/15**, recall/precision **9/9**, FP-sim **0/9**, leak **0/5**, integrity **15/15**, parity **24/24**, token-leak **0**; reclassify 2/24 — hex-gap + cr-positional-fail fail-closed đúng đường khai trong notes; recovery-success live 0/0 = **N/A** (không mismatch có supported route hợp lệ phát sinh; nhánh thành công đã chứng minh offline 1/1). 5 limitation ghi §5-M16 (đại diện không thống kê; scan 1 retry; recovery N/A; legacy gap_gate nhiễu BACKLOG NON-BLOCKING; analyze-mech chỉ 2 family exposed). Claim boundary tự giới hạn (xem blockquote đầu file). Audit `a650783` · design `0766c1f` · plan `6c84db1` · provenance `183eb1a`. Verify: pytest **660** · vitest **406/33** · build sạch. **Capability expansion: NOT STARTED.** |
| **M15 — Public Capability Contract Formalization & Migration (Task 1–16)** | `3d1a0a2`→`b5fef42` | **Formalize TOÀN BỘ capability đã tồn tại thành hợp đồng công khai, máy-đọc — 0 family cần MIGRATE_SPEC_SURFACE.** Design rev2 (`cd1b8e5`) sửa 6 điểm review; plan rev2 (`b54e507`) sửa 3 điểm ordering/isolation/STOP-GATE. **(1) Taxonomy** (`mechanisms.py`) — canonical namespaced (`family.mechanism`) ĐÓNG đủ **8 family**, `INTENTIONAL_GAP_MECHANISMS` (giá trị cố ý không target nào sở hữu, khai tường minh — không rơi tự do), alias **MỘT CHIỀU** `LEGACY_ALIASES` (legacy sorting bare id → canonical; `canonical_mechanism()` là compatibility boundary DUY NHẤT, KHÔNG phải nguồn sự thật thứ hai — analyze GIỮ NGUYÊN giá trị sorting live-verified M14, không đổi để khỏi vỡ hợp đồng LLM đã kiểm chứng). **(2) Ownership membership-level**: `owned_mechanisms` trên từng `FamilyMembership` (không phải mức target — generic có 2 membership, `boolean_composition`/`structural_progressive_representation`, mỗi cái owned riêng) — đủ **14/14 entry CATALOG** (khoá K1) qua 4 wave conformance-proof theo family (W2 scan — KHÔNG selector mới, `algorithm.scan` = catch-all trong-family; W3 boolean dual-surface — `single_gate_truth_table` ↔ `composed_rule_dag` tách bạch, KHÔNG hợp nhất 2 bề mặt; W4 network — routing owned `unweighted_hop_bfs` + `known_gaps` máy-đọc ghi Dijkstra, encap owned `encapsulate_decapsulate_4layer`; W5 representation — owned DẪN XUẤT `manifest.process_types()`, hai membership của generic có `ResultAuthority` khác nhau, pin bất biến #21 làm lock). **(3) `config_contract_version` descriptor-level** (8× `algo-cfg-1` + `scan-1.0` + `logic-cfg-1` + `binary-cfg-1` + `net-cfg-1` + `encap-cfg-1` + `dsl-1.0`) — KHÔNG vào envelope, KHÔNG Alembic; per-entry policy lock cho `algo-cfg-1` (required/bounds/normalize/annotation) + proof `binary_search` **normalize-không-refuse** trên dãy chưa sắp (BE+FE, `CORRECTNESS.md §9`). **(4) Route-consistency ordering trong `run_pipeline`**: `classify_with_one_route_recovery` chạy **≤ 1 reclassify BOUNDED, TRƯỚC** mọi route-dependent gate; **HAI mã lỗi tách bạch** — `ROUTE_MECHANISM_FAMILY_MISMATCH` (cross-family, tại recovery) ≠ `GATE_MECHANISM_OWNERSHIP` (cùng-family nhưng cơ chế không sở hữu, tại `check_mechanism_consistency_for_target` — nay sống trên CẢ HAI lifecycle: selector M14 + direct-entry M15 mới); mismatch KHÔNG BAO GIỜ tới `stage_simulate` trên target mâu thuẫn; ngân sách cố định (analyze ≤1/classify ≤2/simulate ≤1, không recursion). **(5) `ANALYZE_SCHEMA.prescribed_procedure`** enum dẫn xuất `analyze_exposed_values()` (+2 giá trị `positional_representation.*`); `null`/`"none"` vẫn permissive (không ép cơ chế, không từ chối oan). **(6) Hai control offline khoá 9**: hex/octal (đổi cơ số ≠ 2) → `capability_gap` qua HAI lớp phòng thủ độc lập (ownership gate trên direct entry + route-mismatch recovery khi bị misroute sang generic); binary_search dãy chưa sắp → normalize + annotate, KHÔNG refuse. **(7) suite eval `m15_wave1`** (4 case mới hex-gap/octal-gap/binary-positive/binsearch-unsorted + 2 case `m14_sorting` tái dùng tag). `CACHE_VERSION` 11→12 (Task 10) → **13** (Task 11 hotfix prompt-only — vá bề mặt classify `binary_search` mâu thuẫn chính policy normalize-not-refuse đã lock, dùng ĐÚNG MỘT quyền prompt-fix). **(8, Task 16) Coverage matrix**: `sorting` `PILOT`→`SUPPORTED` (claim tự giới hạn — targeted acceptance n nhỏ, KHÔNG phải bằng chứng thống kê); `binary_system` note += control cơ số ≠ 2. **Verify offline**: pytest **529 pass, 2 skipped, 1 deselected** (+79 so với 450) · vitest **406 pass, 33 files** (+3/+1) · build sạch · **FE production diff toàn M15 = 0** (chỉ `capability-descriptors.json` sinh lại + 2 file test — `binary-normalized.test.ts` mới, `scan-module.test.ts` +3 dòng). **Verify LIVE Task 11** (STOP GATE — user duyệt ≤6 case/≤20 HTTP, suite `m15_wave1`): run 1 **16 HTTP, 5/6** OK (hex/octal fail-closed qua recovery đúng; binary-positive không chặn oan; sorting-paraphrase/selection đúng; binsearch-unsorted bị từ chối oan ở classify — root cause CHỨNG MINH bằng live: bề mặt classify khoá "dãy ĐÃ SẮP" mâu thuẫn chính policy normalize-not-refuse đã lock ở Task 8) → hotfix prompt-only (`f52f1a2`, CACHE 12→13) → rerun có mục tiêu **3 HTTP, OK** → **tổng 19/20 · 0 retry · 0 transient** (chi tiết đầy đủ §1). **KHÔNG**: selector mới (ngoài sorting đã có từ M14), đổi executor/renderer, capability mới, Alembic, mở M16. Claim hợp lệ: *"Toàn bộ 8 capability family hiện có đã formalize thành hợp đồng ownership + version tường minh, máy-đọc, kiểm chứng cả offline lẫn live trên đúng MỘT wave slice (W1) — không cần di trú bề mặt LLM nào (0/8 MIGRATE_SPEC_SURFACE)."* Design: `docs/superpowers/specs/2026-07-18-m15-*.md` (rev2); plan: `docs/superpowers/plans/2026-07-18-m15-*.md` (rev2). Close report: `.superpowers/sdd/m15-close-report.md` (gitignored). |
| **M14 — Capability Family Formalization & End-to-End Pilot (Task 1–14)** | `cdb56dd`→(HEAD) | **Uniform LLM-facing spec surface, heterogeneous deterministic execution — pilot family SORTING, end-to-end trên production lifecycle thật.** Formalize abstraction capability SẴN CÓ (không registry mới): **(1) descriptor** trên chính `SimSpec` — `family_memberships[]` (đa membership; generic thuộc HAI family với `result_authority` khác nhau: boolean_composition=computation + structural_progressive_representation=representation) + `executor_id`/`reachability`/`curriculum_anchor`/`known_gaps`; taxonomy 8 family đóng (`descriptor.py`); coverage matrix enum đóng {SUPPORTED/PARTIAL/PILOT/CAPABILITY_GAP/OUT_OF_SCOPE} (`coverage.py`, §O guardrail — không claim phủ toàn chương trình, gap khai trung thực). **(2) FAMILY_SELECTORS** (`families/`) = bề mặt LLM của family (span nhiều target, fact KHÁC CATALOG, cross-lock song ánh chống drift); `comparison_sort` là **selector token**, KHÔNG phải SimSpec, KHÔNG BAO GIỜ là envelope id. `llm_choices()` DẪN XUẤT (ẩn 2 sort concrete, +token). Descriptor artifact `capability-descriptors.json` sinh-từ-nguồn + sync-lock BE + cross-lock FE test-only (production FE KHÔNG import — điểm 6). **(3) SortingFamilySpec** đóng (`family_version/variant/array/order/labels?`) + `validate_family_spec` fail-closed. **(4) mechanism-consistency gate** (`mechanism_gate.py`, §E4): tín hiệu analyze `prescribed_procedure` (enum đóng theo THAO TÁC, không tên thuật toán, không kết quả) + `owned_mechanisms` → tầng 1 selection/quick/other_unspecified → `capability_gap`; tầng 2 variant sai cơ chế → `mechanism_variant_mismatch`→retry. `null`/`none` = permissive (đề sắp-xếp-thường, không từ chối oan). **(5) adapter** `selector.resolve` tất định (variant→concrete id, FamilySpec→config AnalysisOk) → validation KÉP qua `validate_algorithm_config` HIỆN CÓ → envelope CONCRETE; executor/renderer/FE **KHÔNG viết lại** (FE production diff=0). `CACHE_VERSION` 10→11. **(6) production/eval convergence (bất biến #22)**: `evaluate_item` đi CHUNG `run_pipeline` + observer THỤ ĐỘNG; computation gate M13 + mechanism gate M14 NAY sống trong eval; `_simulate_with_metrics` (known-issue #1 drift) RETIRE sau transcript-parity proof; side-effect isolation lock 0-row; fault-injection (classify qua nhưng gate chặn → honest refusal). **(7) metric split** family_selection/variant_selection/final_route (đo trên FINAL envelope, không lẫn classification cũ) + suite `m14_sorting`. **Verify offline**: pytest **450** (+73 so với 377) · vitest **403** (+10) · build sạch · FE diff=0. **Verify LIVE** (user duyệt ≤16/≤4): **4/4 OK · 11 HTTP · 0 retry · 0 transient** (nhật ký §1). **KHÔNG**: migrate family thứ hai (M15), eval toàn catalog (M16), universal DSL, module riêng từng đề. Claim hợp lệ: *"MỘT public specialized capability family (sorting) đã formalize thành bounded LLM-facing FamilySpec, validate, chuyển vào executor tất định HIỆN CÓ, kiểm chứng end-to-end trên production lifecycle thật."* Design: `docs/superpowers/specs/2026-07-17-m14-*.md` (rev2+§O); plan: `docs/superpowers/plans/2026-07-18-m14-*.md`. |
| **M13-SOUNDNESS (Task 1–14 + hotfix role-compat — ĐÃ MERGE main)** | `db5ba3f`→`e8c9dba` *(đã merge FF vào `main`)* | **Generic semantic soundness + algorithmic right-or-refuse.** Hai lỗi ngữ nghĩa gốc đã sửa: (1) **numeric silent-zero** — `weighted_sum` ăn input không có nguồn giá trị hợp lệ (vd id của một `edge`) từng bị runtime lặng lẽ hoá 0, cảnh "chạy" đủ bước nhưng kết quả sai câm; (2) **misroute kiểu "pseudo-Dijkstra"** — đường generic từng chấp nhận dựng cảnh MINH HOẠ một thuật toán tối ưu (tìm đường ngắn nhất) mà không engine tất định nào thật sự SỞ HỮU cơ chế tính đó, tạo ảo giác "đã tính đúng". Ba workstream: **(A)** hợp đồng ngữ nghĩa numeric/logical CANONICAL dẫn xuất từ manifest (`dsl_semantic_contract()` → sinh `dsl-contract.json`, sync-lock chống trôi) + validator hai tầng từ chối operand không có nguồn giá trị / role sai (`INVALID_SOURCE`, coercion DENY mặc định) + runtime hai tầng fail-closed (`GenericEvaluationError`/`GenericExecutionError`, 4 mã lỗi, KHÔNG còn seed/fallback 0) + store fail-closed khi `init` ném lỗi; cũng gỡ `object.weight` (field được dạy/validate/patch nhưng KHÔNG runtime nào đọc — silent semantic no-op). **(B)** `computation_gate.py` — SERVER quyết accept/gap trên đường generic bằng **hai kênh tín hiệu có cấu trúc bổ sung nhau** (known-gap roles lọt vào representation plan; `analysis.result_ownership` fail-closed — chỉ `provided`/`rule_derivable` được đi tiếp, `algorithmic` hoặc thiếu/ngoài enum → gap) + mở rộng taxonomy `arbitrary_algorithm` sẵn có (KHÔNG keyword-patch) + vá analyze.md/classify.md dạy ranh giới bằng ví dụ + `CACHE_VERSION` 9→10. **(C)** `displayLabel` — sanitize nhãn hiển thị runtime theo 3 điều kiện (thiếu ∨ label===id ∨ dạng kỹ thuật snake_case/kebab-case) để id kỹ thuật không còn lộ ra làm nhãn học sinh thấy. **Hai lớp regression khoá lại phát hiện**: fixture pseudo-Dijkstra TÁI DỰNG (Task 7 — artifact gốc không khôi phục được từ cache/localStorage, ghi rõ là reconstructed) bị chặn ở cả validator backend lẫn history-reopen frontend; FP-budget offline xác nhận cảnh cấu trúc/nested-boolean hợp lệ vẫn xanh sau khi siết (Task 8); pattern-reuse vẫn phải qua đủ `run_gates`, không có đường tắt bỏ qua gate mới (Task 10); eval case `cap-dijkstra-gap` + `COVERAGE.md §7b` ghi nhận trung thực Dijkstra ngoài phạm vi công khai (Task 12); patch `add_object` fail-closed trên field lạ thay vì strip im lặng, allowlist `PATCH_ADD_FIELDS` vào hợp đồng sinh (Task 12b). **Verify Task 13 (đo lại, offline)**: pytest **372 pass, 1 deselected**; vitest **390 pass**; `npm run build` sạch; `npm run audit:layout` **4/4 route sạch** (M13 chỉ đổi nguồn text nhãn). **Task 14 (live, user duyệt `ALLOW_LIVE_AI=1`, trần tuyệt đối 39 call) ĐÃ CHẠY — 37 HTTP · 0 retry · 0 transient** (nhật ký §1): **Dijkstra → `unsupported` gate=fired, KHÔNG generic config** ✅ · **m12_scan 4/4** ✅ (flagship scan + 2 control chuyên biệt + loop-gap) · **m11_compose 4/5** — canonical ❌ đỏ ×2 cùng chữ ký, dán nhãn `unknown_primitive` bởi harness lúc đó (nhãn SAI — xem sửa lại ở known-issue 7f): rerun chẩn đoán dump được message thật, xác nhận đây **LÀ M13 chặn oan** (check rule-output→target-role từ chối `boolean → value_box`, một chuỗi hợp lệ ngữ nghĩa), categorizer khớp nhầm vì message chứa cụm "object type" trong câu gợi ý. Đã vá bằng role compatibility một chiều `logical→numeric` + categorizer nhóm `role_mismatch` + message dẫn xuất từ contract (nhánh `m13-hotfix-role-compat`, chi tiết ở 7f). Không phát sinh gap-gate false positive nào ở cả 11 lượt case. Chi tiết đầy đủ 13 task + finding: `.superpowers/sdd/progress.md`; spec nguồn: `docs/superpowers/specs/2026-07-16-m13-generic-semantic-soundness-design.md`; plan: `docs/superpowers/plans/2026-07-16-m13-generic-semantic-soundness.md`. |
| **M12-AI-SCAN** | `439d12e`→`d14ded3`+ | **Đóng gap M12 deferred: NL tiếng Việt → `algorithm.scan` + pseudocode dẫn xuất + UI.** (1) `scanPseudocode(spec)` — mã giả 5 dòng kiểu SGK DẪN XUẤT từ spec, `runScan` gắn `Step.line`/narration từ CÙNG layout (một nguồn, chống highlight trôi; narration bước quyết định là CÂU HỎI — M9-S1); vét cạn mọi combo enum hợp lệ. (2) Module **`algorithm.scan`** (adapter mỏng, module thứ 9 domain algorithm): init = `runScan` → Trace; ScanWorkspace/Inspector tái dùng ArrayView/VarsView/PseudocodeView (thêm prop `lines`); prediction + what-if HOÃN có chủ đích. (3) Backend: port `scan_engine.py` (mirror scan.ts — validator + run_scan cho harness chấm HÀNH VI) + semantic kind **`bounded_scan`** + catalog entry với schema/contract **DẪN XUẤT từ hằng scan_engine** (anti-pattern #1) + `validate_scan_config` (R0) + classify quy tắc 2c (scan CHỈ cho biến thể ngoài 8 bài chuyên biệt; ưu tiên chuyên biệt; loop biến tự do vẫn unsupported). `CACHE_VERSION` 8→9. (4) Suite `m12_scan` 4 case (2 mới + 2 case sẵn gắn tag). **Live smoke 4/4 OK ngay lần đầu** (11 HTTP · 0 retry · 0 429): flagship "tìm ngày đầu tiên vượt 35°C" — bài KHÔNG bài chuyên biệt nào biểu diễn được — chạy trọn NL→scan spec→interpreter dừng đúng vị trí. Known-issue metric: gap-gate false positive trên flagship (§5). pytest **335** · vitest **359** · build sạch |
| **M12-SCAN-PROOF** | `85495af`→`47fbb95` *(nhánh `m12-bounded-scan`, đã merge)* | **Declarative Bounded Scan Proof — giảm nhu cầu "một module thực thi cho mỗi bài".** Audit xác nhận [TraceBuilder](../frontend/src/core/trace-builder.ts) ĐÃ là substrate thực thi tái dụng; gap thật = driver thuật toán còn viết mệnh lệnh bằng TS. **NO-GO cho universal imperative kernel** (thành ngôn ngữ lập trình ẩn → LLM sở hữu semantics, validator không chứng minh được đúng, bài mới không oracle). **GO cho MỘT họ toàn phần rất hẹp: single bounded scan.** `core/scan.ts` — `ScanSpec` (enum ĐÓNG: seed/compare/update/marking/stop, không while/guard/mutation do spec định nghĩa) + `runScan` interpreter **sở hữu toàn bộ** vòng lặp/tiến chỉ số/biên dừng (≤ n → non-Turing)/sinh event/gọi TraceBuilder. **Parity NGỮ NGHĨA** (decisions + finalMarks + stepCount, KHÔNG đòi narration/line) với **4 oracle specialized giữ nguyên**: find_max, count_if, sum_if, linear_search (tìm thấy + không thấy) — MỘT interpreter, spec khác nhau, **0 primitive đặt tên theo thuật toán**. `validateScanSpec` (allowlist mọi trường + coherence "quét trên GIÁ TRỊ phần tử" chống cấu hình vô nghĩa). Test tất định + biên. **Giữ nguyên** mọi engine specialized (oracle), sort/binary/routing/encap KHÔNG đụng (hình khác, ngoài họ). **HOÃN có chủ đích** (đúng scope): tích hợp LLM (analyze/classify/simulate sinh ScanSpec) + wiring UI/renderer — chỉ sau khi proof offline xanh (đã xanh). **0 live AI.** vitest 348 trên nhánh · sau merge M11: **350** · build sạch |
| **M11-COMPOSE** | `9d93153`→`48a1f31` | **Generic composition hardening + đo trung thực composition LỒNG.** KHÔNG phải "tạo generic composition lần đầu" (cảnh phẳng đã compose được từ trước): câu hỏi là LLM có tự dựng CHUỖI rule qua object trung gian không — **CÓ, ngay với prompt cũ** (canonical `A ∧ (B ∨ C)` pass 8/8 ở baseline). Hardening tái dụng, 0 đổi từ vựng manifest: (1) validator 2 tầng **cấm hai rule cùng target** (điểm bất động → rule sau thắng → phụ thuộc thứ tự khai báo); (2) expectation kind **`nested_boolean`** cho harness — dò bảng chân trị theo ĐẦU VÀO TOGGLE của học sinh, id-agnostic, vá âm tính giả của probe `boolean_gate` với rule lồng; (3) contract dạy **chuỗi rule qua trung gian** bằng ví dụ TRỪU TƯỢNG (`kq_phu`, shape khác mọi case đánh giá — chống overfit); (4) analyze/classify chặn **vòng lặp biến tự do** (`x+=3` dừng theo ngưỡng → gate fired, unsupported trung thực; ngoại lệ tường minh: "ít nhất MỘT trong hai" = OR thuần, KHÔNG phải ngưỡng) + ranh giới năng lực `logic.and_gate` (phủ định/≥3 điều kiện/ghép → generic; `a-and` đối chứng vẫn specialized). 5 case dev tag `m11_compose` (curriculum pool; là case REGRESSION đã dùng tune prompt — không được trình bày như held-out). `CACHE_VERSION` 7→8. Live tổng **57 HTTP · 1 retry transient · 0 full dataset**. Bất ổn định lấy mẫu ghi nhận trung thực (n nhỏ, không claim thống kê). pytest **317** · vitest **325** · build sạch |
| **M10-AI-ROUTE** | `422297b`→`45c0aa3` | **Đóng gap M10 deferred: định tuyến NL tiếng Việt → `network.protocol_encapsulation`.** Đề tiếng Việt về đóng gói dữ liệu qua tầng TCP/IP nay được pipeline LLM phân tích → classify → chọn module encapsulation → config v1 được validate → engine tất định 9 bước (LLM **không** sở hữu tầng/PDU/timeline). Đăng ký backend: `_ENCAP_SCHEMA` (bề mặt v1 nhỏ: payloadLabel/appProtocol/notes) + `validate_encapsulation_config` (R0 + cấm khóa engine-owned) + `SimSpec` mang phân biệt ngữ nghĩa (biến đổi PDU qua TẦNG ↔ đường đi qua NÚT). `CACHE_VERSION` 6→7. Vá `classify.md`: tách **tiến trình diễn biến** (engine tự dựng) khỏi **dựng cảnh từng bước** (generic) + quy tắc mạng 3d (encap/routing/unsupported). **Live smoke có mục tiêu: 2/5 → 5/5** sau vá (tổng 37 HTTP call, 0 full dataset). **Merge M10-3D-PED vào main** (FF `1c05d4e`→`422297b`). Còn HOÃN: click 3D trực tiếp, TCP/UDP branching/handshake/phân mảnh. pytest **307** · vitest 323 · build sạch |
| **M10-3D-PED** | `810b5ed`→`dcd31ca` *(đã merge vào main)* | **3D SƯ PHẠM đầu tiên: đóng gói/mở gói TCP/IP.** Module THỨ HAI của domain network (`network.protocol_encapsulation`) — engine tất định **9 bước** dựng PDU phân đoạn với **delta tường minh** `{kind, layer, componentIds[]}` (add/remove/transmit/deliver); LINK+FCS **thêm/gỡ NGUYÊN TỬ**. 2D (stack MÁY GỬI/MÁY NHẬN, phân đoạn trải ngang) + **3D CÓ NGHĨA**: X = chiều truyền, **Z = tầng giao thức** (`meaning_of_z`), PDU đi xuống→băng ngang→đi lên. Dùng chung `PredictionCapability` (LINK+FCS là MỘT đáp án gộp; chấm bằng engine). Thêm field hợp đồng **`threeD`** phân loại TRUNG THỰC: encapsulation = `pedagogical`, packet_routing hạ về `architectural_poc`. **Bất biến #18**. Một mẫu công khai (Thư viện) + preview phân đoạn. **Định tuyến AI HOÃN** (frontend + mẫu offline; **0 gọi AI**); **click 3D trực tiếp HOÃN**; không TCP/UDP branching / handshake / phân mảnh. `practice_activity` vẫn PARTIAL. pytest 289 · vitest 323 · build sạch · audit 4/4 · nghiệm thu browser 15/15 |
| M7.13A | `7fa4046` | Generic interaction semantics: `drag` (allowlist `node`), constraints (bounds/axis/snap), ownership rule, **position state-owned** (`GenericState.pos`), scene-mode consistency (exploratory/progressive/hybrid) truyền vào simulate |
| M7.13B | `d1d518c` | Exact cache version-aware (`simulation_cache`), validated **pattern reuse** (`simulation_patterns`), matcher tất định (không embedding), hybrid adaptation (deterministic fill + 1 call adapt), metrics reuse |
| M7.14 | `7835330` | **Correctness audit** (8 gap role, canonical↔learner policy, `docs/CORRECTNESS.md`), **SimulationPatch v1** + NL edit + manual edit generic, viewport safety (fit/reset, layering, label flip, edge label) |
| M7.14T | `72a715d` | Offline-first testing: hard network guard, gỡ key khỏi env test, `ALLOW_LIVE_AI=1` opt-in, suite smoke/full/boundary, API budget, metric **`gap_gate_recall`** song song |
| Phase 0 | `9034d7c` | Context docs: `ARCHITECTURE_MAP` / `CODE_INDEX` / `CURRENT_STATE` |
| M7.14D | `27c0f1f` | **EditPolicy v1**: affordance sửa suy từ spec (spatial/structural/value_only/observation), reason_code `policy.*` vs `structure.*`, enforce 3 tầng; EditBar tách component (fix lag); stable control shell; Esc hủy công cụ |
| M7.14D.1 | `af6dc4f` | UI-only: ẩn nút "Chỉnh sửa" khi policy không có công cụ thật (`hasMeaningfulEditAffordance`) — value_only/observation không còn chế độ sửa RỖNG; backend policy giữ nguyên |
| **M7.FREEZE** | `7452cbf` | **Đóng M7.x.** Gỡ bố cục pixel khỏi `NetworkState` (blocker 3D duy nhất): state chỉ còn topology + route + steps + cursor; `layout2d` chuyển sang renderer. Quy tắc **renderer-neutral state** vào ARCHITECTURE_MAP. Danh sách **DO NOT ADD BEFORE M8** |
| **M8-PRE** | `cb31adc` | **Coverage + Pedagogical audit → hardening trước M8** (`docs/COVERAGE.md`). **S1**: metadata `EvalItem` (optional, backward-compat) + 4 pool đề mới (`curriculum`/`capability`/`cross_domain`/`thesis` 12 case) + **luật kết nạp** thực thi bằng code; `dataset.py` 30 case **ĐÓNG BĂNG**. Vá lỗ hổng bằng chứng **sắp xếp** (engine có từ lâu, benchmark 0 case). **S2**: `edge.directed` (manifest-first) + node_type mở rộng (actor/process/data_store/input/output) + mũi tên ở renderer + analyze/classify/simulate hỗ trợ **sơ đồ hệ thống thông tin** → đề "phân tích hệ thống" **không còn bị từ chối im lặng**. `CACHE_VERSION` 5→6 |
| M8-PRE-LIP | `f4e3793` | **PredictionCapability** (`predict?` cùng khuôn `timeline?`/`edit?`) + **một** `PredictionBar` dùng chung 2 domain (network: chọn nút; algorithm: có/không); engine tất định chấm; kết quả ở `store.prediction` TÁCH khỏi engine state |
| **M9-UX2** | `08a9a7a` | **Onboarding trực quan + simulation-first + phạm vi luận văn.** `OfflineSample.visibility` (metadata tường minh; "public" mặc định · "internal_fixture") — `publicCatalog()` 12 mẫu Tin học THPT cho học sinh; tam giác + 3 bản "(tổng quát)" thành fixture nội bộ (giữ năng lực + parity coverage; lịch sử vẫn reopen bằng envelope — không phụ thuộc danh mục). `SamplePreview` — 8 preview SVG tĩnh theo simulation_id/metadata (fallback generic). Home: rộng 1040, card preview + chữ, recent card khác biệt ("Tiếp tục ▸"), trạng thái máy chủ im khi ổn. Workspace: cột 264/1fr/300, panel trái đóng mặc định — sân khấu là tiêu điểm. GỠ thẻ "Ứng dụng của cơ chế này" + metadata `applications` (chỉ nuôi thẻ đó). Nguyên tắc #7 vào COVERAGE §2. Acceptance browser 22/22; 0 live AI |
| **M9-UX7** | *(nhánh `m9-ux3-home-preview`)* | **Gỡ panel trái + trình soát bố cục.** `InputPanel` **XOÁ HẲN**: sau khi có trang Thư viện, danh mục tồn tại ở BA nơi (Home 6 gợi ý / Thư viện đầy đủ / panel trái đầy đủ) — panel trái là **bản sao thứ ba**, đúng lỗi "hai nơi làm một việc" mà M9-UX4 đã dùng để gỡ composer khỏi chính panel đó. Workspace còn **2 cột** (sân khấu 700 → **1028px**), header bớt 1 nút, store bớt `leftOpen`/`toggleLeft`. Đổi bài đi qua **Thư viện**. **Độ phủ test KHÔNG mất** dù bỏ 2 test của `InputPanel`: "chỉ mẫu công khai" nay do `ux-shell.test.tsx` kiểm trên `LibraryView`; "không lộ chuỗi kĩ thuật" nay do `ui-hygiene.test.ts` **quét mã nguồn** — mạnh hơn hẳn vì soi mọi component, không chỉ component có test đi qua. **`scripts/audit-layout.mjs`** (`npm run audit:layout`) — soát bố cục trên **Chrome thật** qua CDP: icon lệch tâm · chữ bị cắt · phần tử đè nhau · tràn khung cha · khoảng cách ngoài thang 4px, trên cả 4 route. Đây là công cụ DUY NHẤT bắt được lớp lỗi CSS im lặng (vitest không chạy CSS). Có **dấu vân tay trang** (đo nhầm route → exit 2) và **đã chứng minh bằng tiêm lỗi giả** trước khi tin kết quả "sạch" — anti-pattern #14. Kết quả trên code thật: **4/4 route sạch**. **0 live AI** |
| **M9-UX6** | *(nhánh `m9-ux3-home-preview`)* | **Tuân thủ DESIGN.md + guard vệ sinh đặt ĐÚNG CHỖ.** Bản thiết kế thanh dự đoán trước đó **vi phạm chính `DESIGN.md`**: lấy TÍM (sticker palette) tô nút "Có"/"Kiểm tra", tô nền thẻ, viền trái tím → biến màu **trang trí** thành **accent cấu trúc thứ hai**. `DESIGN.md` §Don't cấm cả hai. Làm lại đúng tài liệu: thẻ nổi bằng **surface tint** (`canvas-soft` + hairline + `rounded-md`, khuôn `pricing-plan-card-featured` — *"distinguished by surface tint rather than a coloured border"*); lựa chọn = `button-utility` trắng, đang-chọn dùng `--primary` (đúng vai *active signal*); phán quyết đúng/sai **được phép** dùng sticker vì §Semantic nói *"status is carried by the sticker palette"*. **Nút primary disabled → XÁM TRUNG TÍNH** (trước đây `opacity: .4` toàn cục biến nút xanh thành **xanh-nhạt-như-hỏng**). Ô tìm kiếm gỡ bo tròn viên thuốc (§Don't: form field giữ `rounded-xs`). **GUARD ĐẶT SAI CHỖ (anti-pattern #13)**: guard cấm-emoji của M9-UX5 quét `renderToString(<App/>)` — SSR chỉ đi qua trạng thái đầu (Home) nên **không bao giờ chạm workspace**; emoji 🔮 và chuỗi `find_max` **lọt qua guard xanh lè**. Thay bằng `ui-hygiene.test.ts` **quét MÃ NGUỒN** → lập tức lộ thêm ⚠, ✓, ⤺, 🔍, 💡. Gỡ `find_max` khỏi `AnalysisCard` (lần **thứ ba** chuỗi kĩ thuật lọt lên UI). Anti-pattern #12/#13. **0 live AI** |
| **M9-UX5** | *(nhánh `m9-ux3-home-preview`)* | **Vỏ ứng dụng + AI hết ngang hàng + TOKEN CSS MA.** **Lỗi im lặng lớn nhất từ trước tới nay**: `global.css` gọi `var(--sp-2xl)` nhưng token thật là `--sp-xxl` → trình duyệt **vứt cả dòng khai báo, không báo gì** → `.home-composer` mất `margin: 0 auto` (ô nhập **lệch hẳn trái**), `.home-title` mất margin (**chữ dí sát ô**), `.app-single` mất padding đáy. Trôi im từ **M9-UX1**; chỉ lộ khi **đo `getBoundingClientRect` trong browser thật** qua CDP. Cùng lúc lộ `--border`/`--radius-sm`/`--radius-md` (M8-PRE-LIP) → `PredictionBar` suốt nay **không viền, không bo góc**. Khoá bằng `styles/tokens.test.ts`: mọi `var()` phải có định nghĩa (anti-pattern #11). Thêm `--sp-3xl`/`--sp-4xl`. **Header**: điều hướng thành LINK CHỮ đẩy phải + gạch chân trang đang xem (trước là 2 nút pill dính wordmark); thêm mục **Thư viện**. **`LibraryView`** (`view: "library"`) — nhà riêng của danh mục đầy đủ, gom nhóm + lọc. Nhờ đó **Home KHÔNG BAO GIỜ phình**: bỏ nút "Xem tất cả (12)", "Tiếp tục học" chỉ **1 thẻ** (học dở 30 bài vẫn y nguyên chiều cao — khoá bằng test), bỏ phụ đề + hàng chip `SAMPLE_PROMPTS` (3 đề đó trùng nội dung 3 bài mẫu ngay dưới, chỉ khác là tốn API → Home có ĐÚNG MỘT đường dùng AI: gõ đề). **AI hết ngang hàng với mô phỏng**: gỡ cặp tab `[Quan sát][Hỏi AI]` (một nửa cột phải, lúc nào cũng vậy, là AI — trái với chính R0); cột phải LUÔN là Quan sát, AI là mục thu gọn ở đáy (`aiOpen` thay `inspectorTab`). **`components/icons.tsx`** — bộ icon SVG nét đậm bo tròn; **cấm emoji/ký tự Unicode làm icon** (khoá bằng test quét ký tự); kẹp giấy thay `+` (nút chỉ gửi tệp, không phải menu). Composer: pill → **HỘP** nhiều dòng. **Thanh cuộn** mảnh, tự ẩn (`scrollbar-gutter: stable` nên nội dung không nhảy). Nghiệm thu browser thật qua CDP + đo bố cục; **0 live AI** |
| **M9-UX4** | *(nhánh `m9-ux3-home-preview`)* | **Thẻ phiên học dùng chung + panel một việc + hết rò chuỗi kĩ thuật.** `SessionCard` — MỘT thẻ cho Home ("Tiếp tục học") lẫn Lịch sử; **thanh tiến độ SUY TỪ ENGINE** (`progressOf`: `init(config)` → `timeline.stepCount`), KHÔNG persist `totalSteps` vào localStorage (bump schema v1 sẽ **xoá sạch lịch sử đang có**). Module không khai `timeline` (exploratory, vd `logic.and_gate`) → **không có thanh tiến độ** — UI dẫn xuất từ capability, không bịa "1 bước". **Vá 2 lỗi thật**: `HistoryView` in thẳng `{item.simulationId}` (`algorithm.bubble_sort`) ra cho học sinh — cùng loại rò rỉ đã vá ở `InputPanel` (M9-UX3) nhưng còn sót; header dùng ký tự `◧`/`◨` (U+25E7/25E8) → font Windows không có glyph → **ô vuông rỗng (tofu)**, thay bằng SVG `PanelIcon`. **Panel trái = MỘT việc (đổi bài)**: gỡ composer khỏi workspace (Trang chủ ĐÃ LÀ nơi phân tích đề), thêm bộ lọc + tranh nhỏ mỗi hàng; `ProblemInput` gỡ luôn prop `variant` (vỏ `compact` hết người dùng — không nuôi code chết). `SAMPLE_PROMPTS` thành **chip bấm được** dưới ô nhập ở Home (điền sẵn đề, học sinh vẫn tự bấm gửi). Dọn CSS chết (`recent-*`, `history-row*`, `sample-dot`, `upload-row`). **BẪY ĐÃ GHI LẠI**: `renderToString(<App/>)` KHÔNG thấy state đã mutate (zustand v5 + `useSyncExternalStore` → SSR lấy *initial state*) — mọi test SSR chỉ hợp lệ ở trạng thái đầu; kiểm view có dữ liệu thì render thẳng component với prop. Nghiệm thu browser thật qua CDP (click thật: mở bài → bước 12/40 → Home → Lịch sử); **0 live AI** |
| **M9-UX3** | *(nhánh `m9-ux3-home-preview`)* | **Home gọn + preview ĐÚNG CƠ CHẾ + vá rò rỉ fixture.** `SamplePreview` 7 → **13 kind**, luật mới **một tranh = một cơ chế = một bài**: 8 bài thuật toán có 8 tranh riêng (`algorithm-bars` find_max · `bars-min` · `sum-threshold` Σ · `count-threshold` bộ đếm · `linear-scan` · `search-range` binary · `sort-swap` bubble · `insertion-lift`). Vá **2 tranh DẠY SAI** (không chỉ trùng): `linear_search` mượn trái/giữa/phải của binary (tìm tuần tự không có mid); `insertion_sort` mượn mũi tên đổi chỗ của bubble (chèn là DỜI — chính `decision.ts` hỏi hai câu khác nhau). Vi phạm nguyên tắc sư phạm #6 (COVERAGE §2.6), nay khoá bằng test "không hai bài thuật toán nào dùng chung một tranh". `ProblemInput` **hai vỏ một lõi** (`variant` hero pill / compact) — hết textarea 5 dòng rỗng + nút xanh kín chiều ngang. Home: card **hàng ngang** (cao bằng nhau bất kể tiêu đề), 2 cột, chấm màu `DOMAIN_COLOR` (hằng số có sẵn, Home chưa từng dùng), cột 1040 → **920**, "xem tất cả" **gom nhóm** theo domain. `InputPanel`: `offlineCatalog()` → **`publicCatalog()`** + bỏ `simulation_id` khỏi UI — luật phạm vi M9-UX2 trước đó **mới chỉ áp ở Home**, panel trái vẫn rò tam giác + 3 bản "(tổng quát)" + chuỗi `algorithm.find_max`. Nghiệm thu browser thật (headless Chrome); **0 live AI** |
| **M9-UX1** | `1f95e92` | **Home + phiên học + lịch sử zero-AI + vệ sinh RULES.** Home thật (view mặc định): MỘT hành động chính + gợi ý chọn lọc + "Tiếp tục học"; không inspector/timeline rỗng trước khi có bài. `state/history.ts`: lịch sử BỀN (localStorage schema v1, whitelist, dedup theo id tất định, max 30 evict, corrupt-safe) lưu **envelope đã validate** → **mở lại ZERO-AI** (bất biến #17) + khôi phục lastCursor/visualMode; reset/goHome không phá lịch sử. Header gọn [Trang chủ][Lịch sử]; HistoryView đủ item + xóa. §17: `applications?` trên module (tĩnh, không LLM) cho 4 domain chuyên biệt. RULES.md → con trỏ ngắn (thứ tự đọc + 10 luật cứng); bản v0.3 lưu `docs/legacy/RULES_v0.3.md` kèm cảnh báo LEGACY (khoá bằng `rules-hygiene.test.ts`). Acceptance browser thật 23/23 (reload + reopen 0 /api/analyze); 0 live AI |
| **M9-S1** | `548f1fc` | **Mechanism-aligned interactions (algorithm).** `decision.ts` — điểm quyết định theo cơ chế từng bài: max/min "có cập nhật?", sum/count "cộng/tăng?", linear "tìm thấy chưa?", binary "**nửa nào bị loại**" (3 lựa chọn, hỏi ở bước lấy mid), sorts "đổi chỗ?/dời?"; đáp án + bằng chứng nhân quả (số thật, biến trước → sau) DẪN XUẤT từ sự kiện trace kế tiếp; MỘT nguồn nuôi cả predict lẫn dải nhân quả. `interaction-policy.ts` — hết "một swap cho cả 8 bài": free (sorts) · framed (linear: chi phí) · challenge (find_max/min: bất biến vùng-đã-duyệt; binary: tiền điều kiện dãy-đã-sắp — ẩn mặc định, mở qua nút thí nghiệm có khung) · hidden (sum/count). Engine: narration bước quyết định thành CÂU HỎI (không lộ đáp án sớm), marks `eliminated` cho phần tử đã duyệt. Nguyên tắc sư phạm #6 vào `COVERAGE.md §2`. UX acceptance 18/18 trên browser thật; 0 live AI |
| **M8 Slice 1+2** | `f83b635`, `18e4c2a`, `cce75fc` | **Shared 2D/3D renderer.** S1: `renderers?` trên SimulationModule ("2d" mặc định = Workspace), `simulations/renderer.ts` (khả dụng = tuyên bố ∩ có renderer thật), `store.visualMode` (lát TRÌNH BÀY — đổi mode không đụng active/cursor/prediction, không rebuild, không AI), `VisualModeToggle` theo capability. S2: `network/ui3d.tsx` — Three.js thuần (KHÔNG R3F), `React.lazy` code-split; `layout3d` renderer-owned (route z=0, ngoài route lùi sâu); OrbitControls xoay+zoom khoá pan; reset GÓC NHÌN ≠ reset mô phỏng; WebGL fail → fallback tiếng Việt; nội suy HÌNH ẢNH gói tin, sự thật vẫn là `packetAt`. Nghiệm thu browser thật 16/16 (headless Chrome + SwiftShader, bài mẫu offline). **Bất biến #16** vào ARCHITECTURE_MAP. Slice 3 (mạng phân tầng) HOÃN — cần semantics đóng gói tất định mới |

Milestone trước đó (M1–M7.12) đã có trong lịch sử commit gộp/ban đầu; kiến trúc
của chúng được mô tả trong `ARCHITECTURE_MAP.md`.

**Lưu ý hồ sơ (M14 discovery):** chỉ M9-UX3, M10-3D-PED và M13 có design
doc/plan độc lập trong `docs/superpowers/`; **M11-COMPOSE, M12-SCAN-PROOF,
M12-AI-SCAN KHÔNG có file design/plan riêng** — hồ sơ thiết kế của chúng là
chính các hàng §2 ở trên + commit messages. Không dẫn chiếu "M11/M12 design
doc" như thể file tồn tại.

## 3. Năng lực đang hỗ trợ

**Chuyên biệt (engine tất định riêng, không dùng DSL):**
- `algorithm.*`: find_max, find_min, sum_if, count_if, linear_search,
  binary_search, bubble_sort, insertion_sort. **M9-S1**: mỗi bài có ĐIỂM QUYẾT
  ĐỊNH riêng theo cơ chế ẩn (dự đoán + dải nhân quả cùng nguồn `decision.ts`) và
  **chính sách what-if theo cơ chế** (`interaction-policy.ts`) — what-if branch
  chỉ mở nơi nó dạy được điều gì đó.
- `logic.and_gate` (bảng chân trị), `binary.decimal_to_binary` (bits⇄decimal),
  `network.packet_routing` (**route = BFS tất định**, không phải LLM) — M8:
  module DUY NHẤT có renderer **2D + 3D** (cùng engine state; các module khác
  CỐ Ý 2D-only vì 3D không thêm giá trị sư phạm, `COVERAGE.md §8`).

**Generic (`generic.rule_scene`, DSL v1):**
- Object: `switch`, `lamp`, `value_box`, `node`, `edge`, `moving_entity`, `label`,
  `container`, `group`, `heading`, `paragraph`, `text`.
- Rule: `boolean` (and/or/not/xor), `weighted_sum`. **M11: rule NỐI CHUỖI qua
  object trung gian** (target của rule này làm input rule khác — DAG, cấm chu
  trình, mỗi target đúng MỘT rule) — engine điểm bất động vốn hỗ trợ sẵn, nay
  được validator/probe/contract bảo vệ tường minh; LLM compose được biểu thức
  ghép `A ∧ (B ∨ C)`, `A ∧ ¬B` không cần module chuyên biệt.
- Interaction: `toggle`, `drag` (chỉ `node`; bounds/axis/snap).
- Process: `reveal_sequence`, `move_along_path`.
- Scene mode: exploratory / progressive / hybrid (tất định từ analysis).
- Chỉnh sửa tăng dần: 5 patch op + NL edit; viewport fit/reset.
- **EditPolicy v1 (M7.14D)**: công cụ sửa suy từ spec — `spatial` (thêm điểm/nối/
  xóa) · `structural` (thêm/sửa/xóa nội dung, KHÔNG thêm điểm) · `value_only`
  (chỉ tương tác sẵn có) · `observation` (có `move_along_path` → khóa topology).
  M7.14D.1: cảnh không có công cụ thật (value_only/observation) **không hiện nút
  "Chỉnh sửa"** — không quảng bá affordance rỗng; toggle/kéo vẫn chạy.

**Hạ tầng:** exact cache + pattern reuse; eval harness (30 đề, suite smoke/full/
boundary); ingest text/docx/code/image.

## 4. Capability gap CỐ Ý (không phải bug — `docs/CORRECTNESS.md §5`)

Không primitive nào cover → `capability_gap`, **không** render xấp xỉ:

`geometric_projection` · `geometric_perpendicular` · `geometric_intersection` ·
`geometric_circle` · `geometric_locus` · `numeric_threshold` ·
`continuous_motion` · `arbitrary_algorithm`

Hệ quả đã verify live: bài hình học phức tạp (chân đường cao / giao điểm / đường
tròn ngoại tiếp / quỹ tích), "đèn sáng khi ít nhất 2 trong 3", quỹ đạo hành tinh,
"thuật toán em tự nghĩ" → **unsupported đúng và ổn định**.

## 5. Known issues / giới hạn đã biết

### §5-M16 — Limitation của đánh giá M16 (ghi trung thực, không phải bug)

1. **Live evaluation gồm 24 case, một model (`gemini-2.5-flash`) và một lần
   chạy** — kết quả là *targeted catalog-wide acceptance*, chưa phải ước lượng
   thống kê cho mọi đề bài tự nhiên.
2. **`valid_spec_first_attempt` đạt 14/15** vì `algorithm.scan` cần một
   semantic retry; final result vẫn đúng và không có transient retry.
3. **Live recovery-success là N/A (0/0)** — trong live baseline không có
   mismatch nào có một supported route hợp lệ để tính recovery-success; nhánh
   recovery thành công đã được kiểm chứng offline 1/1, còn live recovery-fail
   đã kiểm chứng fail-closed behavior.
4. **Legacy plan-channel `gap_gate_recall` đạt 0.444 và có hai false-positive
   signal** ở find_max/binsearch paraphrase do analyze-role noise đã biết
   (7c); metric này nằm NGOÀI primary M16 routing metrics và final route của
   cả hai case vẫn đúng. Trạng thái: **BACKLOG — NON-BLOCKING DIAGNOSTIC.**
5. **`analyze_mechanism_accuracy` chỉ áp dụng cho các family có structured
   mechanism signal được expose trong schema** (comparison_sort +
   positional_representation — claim boundary M15 giữ nguyên).

1. **[ĐÃ XỬ LÍ — M14 Task 9–10, bất biến #22]** `_simulate_with_metrics` (harness)
   mirror `stage_simulate` — drift đã đo cụ thể ở M14 discovery: (a) harness
   không gọi `run_pipeline`; (b) không chạy `check_semantic_compatibility` trong
   retry; (c) không gọi `check_computation_ownership`; (d) `classify_error`
   string-match. **Nay `evaluate_item` đi CHUNG `run_pipeline` + observer thụ
   động** (computation gate + mechanism gate sống trong eval); `_simulate_with_metrics`
   + `_evaluate_item_legacy` ĐÃ RETIRE sau transcript-parity proof (`test_eval_parity`
   — non-gate khớp; gate-refusal là khác biệt hợp lệ). `classify_error` còn làm
   FALLBACK khi attempt không mang error_code có cấu trúc. Side-effect isolation:
   eval 0 row mới (`test_eval_side_effects`).
1b. **[M14] mechanism gate (E4) là BACKSTOP, không phải cổng duy nhất.** Live
   pilot cho thấy LLM từ chối selection-sort NGAY ở classify (predicted=None) →
   mechanism gate không cần fire. Gate chỉ nổ khi classify LỠ route một đề cơ-chế-
   ngoài-family về `comparison_sort` (offline test khoá nhánh đó). Residual risk
   (đã ghi §E4): nếu analyze phán SAI `prescribed_procedure` (đề selection nhưng
   nói null) thì tầng 1 không nổ — lỗi Ở TẦNG ANALYZE, đo được bằng eval near-miss;
   không keyword-patch tên thuật toán trong code.
2. **`move_along_path` không bắt path phải đi theo edge có thật** (waypoint tường
   minh vẫn hợp lệ) — giữ có chủ đích; bài routing thật được specialized bảo vệ.
3. **Multi-family edit chưa hỗ trợ** (M7.14D): cảnh LAI (vừa structural vừa
   node/edge) dùng precedence bảo thủ → chỉ sửa được theo family thắng.
4. **StrictMode nhân đôi render ở dev** — chỉ ảnh hưởng cảm nhận khi chạy
   `npm run dev`, không ảnh hưởng bản build.
5. **`CLAUDE.md` bị gitignore** → sự thật bền vững phải nằm ở `docs/*`.
6. **[ĐÃ XỬ LÍ — Alembic + DB-HARDEN-2]** Trước chỉ có `create_all` (thêm bảng
   OK, ALTER bảng cũ thì không). Nay có **Alembic** (`backend/alembic/`, migration
   đầu `72095b7dd318`): entrypoint Docker chạy `alembic upgrade head` trước khi
   phục vụ (đường DUY NHẤT đổi schema trên DB bền); đổi model → `alembic revision
   --autogenerate`. env.py dùng chung `DATABASE_URL`+`Base.metadata` của app
   (chống drift), `render_as_batch` để ALTER được cả trên SQLite.

   **DB-HARDEN-2 (quyền sở hữu schema theo dialect — chất lượng triển khai, KHÔNG
   phải đóng góp học thuật):**
   - `init_db()` gọi `create_all()` **chỉ khi** dialect là SQLite
     (`sqlite_owns_schema(engine)` — đọc `engine.dialect.name`, không string-check
     URL). Trên **Postgres bền `init_db()` là no-op**: Alembic sở hữu DUY NHẤT
     tạo & tiến hoá schema; runtime KHÔNG lặng lẽ vá schema thiếu.
   - **Cổng chống trôi** `tests/test_migration_drift.py` chạy trong suite mặc định
     (`upgrade head` + `alembic check` trên SQLite tạm, không đụng DB dev): đổi
     model mà quên tạo migration → test ĐỎ. Đã chứng minh bằng fault-injection.
   - **Smoke Postgres thật** opt-in: `pytest -m postgres` (marker bị `pytest.ini`
     addopts loại khỏi run mặc định → default vẫn nhanh/offline, không cần Docker).
     Container throwaway KHÔNG volume (không đụng `pgdata`): migrate→head,
     `alembic_version`==head, ghi/đọc/sửa qua model thật, restart+reconnect,
     `alembic check` sạch, cleanup có kiểm chứng.
   - Pool dialect-aware giữ nguyên (SQLite: `check_same_thread`; Postgres:
     `pool_pre_ping/recycle/size/max_overflow`, chỉnh qua env).

   *Volume Postgres CŨ* (tạo bằng `create_all`, chưa có `alembic_version`) khi
   chuyển sang có HAI đường AN TOÀN: **(A)** dữ liệu bỏ được → `docker compose
   down -v` cho volume mới sạch; **(B)** giữ dữ liệu → `alembic stamp head` **chỉ
   khi** đã xác nhận schema khớp head. **Không tự động stamp DB lạ** (giấu drift).
   Bảng `problems` cũ vẫn orphan vô hại.
7. **Pattern chứa bool op lưu `status="candidate"`** → không auto-reuse (chống
   mẫu AND bị dùng cho đề OR). Cần benchmark/người duyệt để nâng `verified`.
7c. **[M12-AI-SCAN] gap-gate false positive trên đề scan-ngưỡng (metric-only).** Analyze gắn `numeric_threshold` cho "tìm ngày đầu tiên vượt 35 độ" dù đề là duyệt DÃY CHO SẴN (n=2/2 lần, kể cả sau khi vá carve-out — salience prompt dài, đúng loại hiện tượng M8-PRE S3). KHÔNG ảnh hưởng routing: gate chỉ chặn đường generic (bất biến #5), classify chọn `algorithm.scan` đúng cả 2 lần và spec/semantic đều pass. Rủi ro còn lại: nếu classify chệch một bài scan về generic thì bị từ chối oan. Hướng xử lý NẾU cắn thật: sửa tất định server-side (bỏ numeric_threshold khỏi required_roles khi analysis có dãy số cụ thể) — không đuổi tiếp bằng prompt.
7d. **[M13] `gap_gate_recall` (harness) chỉ phản ánh KÊNH 1 của `computation_gate.py` (known-gap roles lọt vào `unsupported_capabilities`), CHƯA phản ánh KÊNH 2 (`result_ownership` fail-closed).** **[SỬA — M14 discovery, đối chiếu source]** Câu từng ghi ở đây ("outcome mỗi case eval vẫn đi qua `run_pipeline` thật, cả hai kênh cùng sống ở đó") là **SAI so với source**: `evaluate_item` (`harness.py`) tự tái dựng chuỗi stage (`stage_analyze` → `stage_classify` → `_simulate_with_metrics`) và **không gọi `run_pipeline`, không gọi `check_computation_ownership`** (grep toàn `app/evaluation/`: 0 match) — KÊNH 2 không sống trong đường eval. Đây vì thế không chỉ là giới hạn metric mà là giới hạn **lifecycle của harness**: production nghiêm ngặt hơn eval; hướng lệch là eval có thể chấm FAIL (`unsupported_as_generic`) ở case mà production từ chối ĐÚNG bằng gate. Metric kênh 1 giữ nguyên cách tính để còn so sánh với baseline M7.14T; hợp nhất lifecycle là target bắt buộc của M14 (xem known-issue 1).
7e. **[M13] Fixture nội bộ `GENERIC_REVEAL_SPEC` (label === id, ví dụ `"A"`/`"B"`/`"C"`) nay hiển thị "Điểm 1"/"Điểm 2"/"Điểm 3"** thay vì đúng chữ cái gốc — lệch với narration cũ ("Dựng điểm C"). Đây là **hệ quả trực tiếp, đã duyệt** của luật `displayLabel` sanitize (Task 11: label === id bị coi là kỹ thuật, không phải nhãn thân thiện — đúng ca lộ id Dijkstra mà M13 phải chặn). Fixture này là **internal** (không thuộc `publicCatalog()`), không lộ ra học sinh; không sửa vì sửa đúng sẽ làm yếu chính luật sanitize.
7f. **[M13 HOTFIX] `m11-nested-canonical` đỏ ×2 live — ĐÃ CHẨN ĐOÁN ĐÚNG và VÁ. Kết luận trước ("KHÔNG phải M13 chặn oan") là SAI, đã bị đảo lại bằng bằng chứng.** Sau khi harness được vá lưu message lỗi thật (commit `c3a11b9`), rerun có mục tiêu (ngân sách nhỏ, controller giữ) dump được message live nguyên văn: `Rule boolean sinh giá trị vai trò "logical" nhưng target "vbOR" (value_box) không nhận được vai trò đó — dùng object type có vai trò logical làm target (vd value_box/lamp).` **Đây LÀ M13 chặn oan thật** (check rule-output→target-role, `validator.py` §3.2/Task 3): đề canonical "A ∧ (B ∨ C)" dựng trung gian bằng `value_box` (`{numeric}`) thay vì `lamp` (`{logical, numeric}`) — shape hợp lệ ngữ nghĩa trước M13 (boolean executor sinh đúng 0/1, 0/1 LÀ số) nhưng check role cũ đòi EXACT match nên từ chối. 4 case m11 khác xanh chỉ vì LLM tình cờ chọn `lamp`. **Nguyên nhân chẩn đoán sai ban đầu**: `classify_error` (harness) khớp nhầm — message role-mismatch CHỨA cụm "object type" trong chính câu gợi ý ("dùng object type ... làm target"), nên bị nhánh `unknown_primitive` (dựa trên cụm chung "object type") khớp trước, che mất chữ ký thật. Message gốc còn TỰ MÂU THUẪN: gợi ý "dùng object type có vai trò logical (vd value_box/lamp)" ngay sau khi vừa từ chối `value_box` vì KHÔNG có vai trò đó → LLM retry lại đúng thứ vừa bị cấm → 3 attempt đỏ. **Đã sửa (nhánh `m13-hotfix-role-compat`)**: (1) role compatibility MỘT CHIỀU `logical → numeric` trong contract (`dsl_semantic_contract()["role_compatibility"]`, helper `role_satisfies()`) — chiều `numeric ↛ logical` VẪN DENY (đây chính là coercion `v>=1` mà M13 Task 3 sinh ra để diệt, canary `test_derived_target_sai_role_bi_tu_choi_weighted_sum_nuoi_boolean` còn xanh); KHÔNG runtime conversion, KHÔNG thêm role `logical` cho `value_box`, `value_provider_types("logical")` vẫn `{switch, lamp}`; (2) message lỗi hai tầng nay DẪN XUẤT gợi ý target type từ contract thay vì hardcode, nên không còn tự mâu thuẫn; (3) `classify_error` thêm nhóm `role_mismatch` kiểm TRƯỚC `unknown_primitive`, regression test dùng nguyên văn message live ở trên + test case-(b) nối message-generator thật với categorizer (fault-injection: không có nhánh → rơi `invalid_value`). `.superpowers/sdd/hotfix-role-compat-report.md` có đầy đủ bằng chứng/test. **XÁC NHẬN LIVE sau vá** (ngân sách 4 HTTP · 0 retry · 0 transient): `m11-nested-canonical` nay **✅ OK** — `generic.rule_scene`, bảng chân trị hợp thành đúng toàn bộ (8 tổ hợp, 2 rule nối chuỗi); FP đã hết. Offline sau vá: pytest **377** · vitest **393** · build sạch.
7b. **[M11] `nested_boolean` là probe HARNESS-ONLY** — pipeline production không
   chấm bảng chân trị (chỉ role-compat + system-flow); một spec lồng cú-pháp-đúng
   nhưng hành-vi-sai vẫn có thể ship tới học sinh (giống mọi expectation khác —
   không phải regression mới). Đo live M11 cho thấy hai kiểu spec kém do LẤY MẪU:
   ép phẳng nhiều mức thành 1 rule; cảnh "chết tương tác" (switch không `value` →
   0 toggle). Contract đã dạy chống cả hai nhưng KHÔNG có cổng tất định production;
   nâng cấp (nếu cần) là milestone riêng. **Route/compose ổn định qua nhiều lần
   lấy mẫu CHƯA chứng minh thống kê** (n = 2–4 mỗi case) — chỉ được nói "mỗi case
   đã pass live sau vá ít nhất một lần".
8. **[M8-PRE plan C — ĐÃ XỬ LÍ bằng nén dư thừa; hạn mức GIỮ NGUYÊN 20]**
   Cảnh sơ đồ hệ thống từng vượt `max_objects = 20` → 422.
   **Ngữ nghĩa của con số 20** (đã inspect): **KHÔNG phải bất biến ngữ nghĩa** —
   vào repo từ `0621910` cùng DSL v1, không có lý do ghi trong RULES.md. Thực chất
   là **ngân sách CHỨA đầu ra LLM + ngân sách DỄ ĐỌC của renderer** (canvas 600×340,
   toạ độ miền 0–100). Engine không phụ thuộc con số này. Khoá bởi
   `test_manifest.py` (assert `== 20`) + test dẫn xuất; **hard-code ngoài manifest
   đúng MỘT chỗ**: `frontend/.../generic/validate.ts` (mirror `MAX_OBJECTS`).
   **Bằng chứng quyết định (đo live):** MỌI cảnh hệ thống HỢP LỆ về ngữ nghĩa đều
   **nằm gọn trong 20** (đếm được: 11, 12, 14, 14, **19** object). Chỉ các bản nháp
   BỊ PHỒNG mới vượt — do Gemini vừa đặt `label` inline cho node/edge, VỪA tạo thêm
   **một object `label` rời lặp lại đúng chuỗi đó** (11 label rời cho 5 node + 6 edge).
   → **Không nâng hạn mức. Không cần capability-aware budget.** Thay vào đó:
   `compact_redundant_labels` (validator, cả hai tầng) gỡ **chỉ** label rời TRÙNG HỆT
   nhãn inline của node/edge có thật, **chỉ khi cảnh đã vượt hạn mức**, và **không bao
   giờ** gỡ label mang chữ riêng hay đang bị tham chiếu cấu trúc. Cảnh trong hạn mức
   không bị đụng tới → **0 bề mặt regression**.

## 5b. DO NOT ADD BEFORE M8 (scope freeze tạm thời)

Cho tới khi M8 bắt đầu, **không thêm** — trừ khi một **blocker 3D thật sự** đòi hỏi:

- specialized domain module mới;
- geometry solver (projection/perpendicular/intersection/circle/locus);
- theorem prover / CAS;
- code playground (`code_experiment`);
- mở rộng RAG / OCR;
- edit mode mới;
- primitive DSL mới tùy hứng;
- hệ learner-feedback mới — **đã MỞ HẸP MỘT LẦN cho M8-PRE-LIP, nay ĐÓNG LẠI** (xem §5c);
- undo/redo · pan/zoom · style editor · topology editing;
- rule DSL mới không liên quan blocker M8.

Mục đích: chấm dứt vòng lặp M7.x tự nuôi chính nó.

## 5c. M8-PRE-LIP — Learning Interaction Proof (ĐÃ XONG, ĐÃ RE-FREEZE)

**Đây KHÔNG phải `practice_activity` đầy đủ.** Đây là **bằng chứng tối thiểu** rằng
**MỘT** optional capability + **MỘT** UI dùng chung phục vụ được **NHIỀU** domain:

> Quan sát → Dự đoán/Chọn → Nộp → **engine TẤT ĐỊNH chấm** → phản hồi là **dữ liệu
> kết quả** → **mô phỏng canonical KHÔNG ĐỔI**.

- `PredictionCapability` (`predict?` trong `SimulationModule`) — cùng khuôn
  `timeline?` / `edit?`: **không khai → không có UI** (3 domain còn lại giữ nguyên).
- Một component **duy nhất** `components/PredictionBar.tsx` phục vụ **cả hai**:
  `network` (N lựa chọn — chọn nút) và `algorithm` (2 lựa chọn — có/không).
- Ground truth **có sẵn miễn phí** trong engine: BFS route (network) · trace thật
  (algorithm). **Không engine mới, không LLM, không gọi mạng.**
- `network.packet_routing` **hết watch-only**: trước đây `apply: (state) => state`.
- Kết quả chấm sống ở `store.prediction`, **TÁCH KHỎI** engine state → học sinh sai
  cũng không đụng được dòng chính (khoá bằng test).
- Phát ngôn thận trọng (network): chỉ nói *"không phải chặng kế tiếp trên đường đi
  ngắn nhất mà engine BFS đã tính"*; nếu nút học sinh chọn **cũng** nằm trên một
  đường ngắn nhất khác thì **phải nói rõ**. **Cấm** nói "đi lối đó là không thể".

**FREEZE ĐÃ ĐÓNG LẠI.** Mở rộng tiếp (chấm điểm, mục tiêu/nhiệm vụ, theo dõi tiến
độ, gợi ý, phản hồi hội thoại, dashboard) → **post-M8**, cần duyệt riêng.

**M9-S1 dùng LẠI capability này, không thêm framework thứ hai**: nội dung câu hỏi
của domain algorithm được nâng từ MỘT câu chung ("có biến nào được cập nhật
không?") thành câu hỏi ĐÚNG CƠ CHẾ từng bài (kể cả 3 lựa chọn cho binary_search —
hợp đồng `PredictionCapability` vốn đã hỗ trợ N lựa chọn). Không đổi
`PredictionBar`, không đổi store, không đổi hợp đồng module.

> **`practice_activity` vẫn là PARTIAL / CHƯA IMPLEMENT** (xem `COVERAGE.md` §6).
> M9-S1 **không** thay đổi điều này: vẫn không có chấm điểm / mục tiêu-nhiệm vụ /
> theo dõi tiến độ / gợi ý / dashboard.

## 6. Việc hoãn CÓ CHỦ ĐÍCH

- **M7.11 Slice 2 — CHƯA hoàn thành.**
- **M7.15 — Minimal Constraint-Aware Geometry**: projection/perpendicular/
  intersection/circle thành rule tất định. Chỉ khi đó `invalid_with_feedback` mới
  có producer thật và generic experimental branch mới có nền.
- **`invalid_with_feedback`**: đã có trong taxonomy, **chưa có producer** nào.
- **`code_experiment`**: deferred — cần sandbox, không được bypass engine tất
  định, **không** pivot thành IDE.
- **3D phân tầng (M8 Slice 3)**: ✅ **đã ship ở M10** (`network.protocol_encapsulation`,
  engine 9 bước tất định) và **định tuyến AI đã ship ở M10-AI-ROUTE**. Còn hoãn
  TRONG module: click 3D trực tiếp, TCP/UDP branching / handshake ba bước / phân
  mảnh / retransmission / congestion / DNS — các đề này classify trả **unsupported
  trung thực** (kiểm bằng case `cur-t12-tcp-advanced`), **cấm** ép vào mô hình v1.
- **M9-S2 / M9-S3** (theo M9-PED-AUDIT §8): *binary — thử thách dựng số N* và
  *packet routing — học sinh tự dẫn gói tin, engine so chi phí với BFS*. Chưa làm.
- **Topology editing cho cảnh network-like**: chỉ mở khi EditPolicy cho phép
  tường minh.
- **Embeddings/pgvector/RAG/OCR/GraphRAG**: cố ý không làm.

## 7. Roadmap

1. ~~Phase 0 — 3 file context~~ (`9034d7c`).
2. ~~M7.14D / D.1 — capability-driven EditPolicy + UI/UX~~ (`27c0f1f`, `af6dc4f`).
3. ~~M7.FREEZE — gỡ blocker 3D, đóng M7.x~~ (`7452cbf`).
4. ~~M8-PRE — coverage/pedagogical audit + S1 dataset + S2 directed data-flow~~
   (`cb31adc`). Quyết định mở #8 (`max_objects`) đã chốt ở plan C: giữ 20 + nén.
5. ~~M8-PRE-LIP — PredictionCapability (2 domain, 1 UI)~~ (`f4e3793`).
6. ~~**M8 Slice 1+2 — shared 2D/3D renderer + network 3D PoC**~~ (nhánh
   `m8-shared-renderer`). Đã chứng minh: cùng config/state/timeline/action/
   prediction → renderer 2D hoặc 3D; 3D là renderer, không phải domain.
   - **Tuyên bố được phép**: "AlgoSim dùng lại config/state/timeline tất định trên
     nhiều renderer, và **chỉ** áp dụng 3D cho nội dung mà chiều sâu/phân tầng thực
     sự mang giá trị biểu diễn." **CẤM** tuyên bố "3D luôn giúp học tốt hơn"
     (`COVERAGE.md §8`).
   - **KHÔNG 3D hoá** (giữ nguyên): cổng logic · nhị phân · **sắp xếp** · **mảng** ·
     trang web · **bảng CSDL**.
   - **Slice 3 (mạng phân tầng) HOÃN post-M8**: có cơ sở sư phạm (T12 B4; 12CS
     B22–24) nhưng đòi năng lực tất định MỚI — trạng thái PDU biến đổi khi qua
     tầng (đóng gói/mở gói). Reveal-boxes chỉ là progressive visualization,
     KHÔNG được gọi là executable simulation.
   - Chưa làm (không phải blocker M8): `z?` optional cho `pos`/`SimAction.move`;
     3D cho cảnh generic `node+edge+moving_entity` — mở khi có nhu cầu thật.
7. ~~**M9-PED-AUDIT** — audit chất lượng sư phạm + tham chiếu bên ngoài (PhET
   implicit scaffolding; Mayer coherence)~~. Kết luận: kiến trúc đúng, nhưng
   nhiều cảnh còn *watch-heavy*; **một** affordance kéo-đổi-chỗ dùng cho cả 8
   thuật toán là khiếm khuyết lớn nhất (hệ quả hầu như bằng 0, riêng
   binary_search còn gây hiểu lầm vì phá tiền điều kiện mà không có khung).
8. ~~**M9-S1 — mechanism-aligned interactions (algorithm)**~~ (`548f1fc`). Vá đúng
   khiếm khuyết trên: điểm quyết định theo cơ chế + chính sách what-if 4 mode.
   **Bất biến mới** (`COVERAGE.md §2.6`): *mọi tương tác phải chạm cơ chế ẩn và
   sinh hệ quả tất định; tương tác trang trí không được admit.*
9. ~~**M9-UX1 — Home + lịch sử học cục bộ zero-AI + vệ sinh RULES**~~ (`1f95e92`).
   Nền sản phẩm: vào cửa đơn giản → phiên học → liên tục học không tốn AI;
   RULES.md hết gây nhiễu cho coding agent tương lai.
9b. ~~**M9-UX2 — onboarding trực quan + simulation-first + phạm vi luận văn**~~
   (`08a9a7a`). Preview trực quan cho starter; sân khấu là tiêu điểm; danh mục
   công khai khoanh Tin học THPT (nguyên tắc COVERAGE §2.7); gỡ thẻ Ứng dụng.
9c. ~~**M9-UX3 — Home gọn + preview đúng cơ chế**~~ (nhánh `m9-ux3-home-preview`).
   Composer pill; card hàng ngang; gom nhóm khi mở rộng. Sửa **2 tranh dạy sai cơ
   chế** và đóng lỗ hổng "luật phạm vi chỉ áp ở Home" (`InputPanel` vẫn rò fixture).
   Bất biến mới khoá bằng test: **một tranh = một cơ chế = một bài**.
9d. ~~**M11-COMPOSE — generic composition hardening + đo composition lồng**~~
   (nhánh `m11-generic-composition`, `9d93153`→`48a1f31`). Đảo ưu tiên có ý thức
   (M11 chạm câu hỏi lõi luận văn trước M9-S2/S3). Tuyên bố ĐƯỢC PHÉP: *"AlgoSim
   dùng phân tích LLM để compose bộ năng lực khai báo generic sẵn có thành cảnh
   tương tác khám phá đã validate cho một LỚP GIỚI HẠN bài Tin học THPT, không
   cần module chuyên biệt riêng cho từng bài trong lớp đó."* **CẤM** nói: sinh
   mô phỏng/code tùy ý · hỗ trợ mọi bài · reveal = executable · thay thế module
   chuyên biệt · tin cậy thống kê (n nhỏ). Phát hiện kiến trúc công bố được:
   ranh giới declarative↔executable TRÙNG ranh giới generic↔specialized.
10. **Kế tiếp — M9-S2: binary "dựng số N"** (`COVERAGE.md §6`, M9-PED-AUDIT §8):
   `binary.decimal_to_binary` là cảnh thao-tác-trực-tiếp tốt nhất nhưng học sinh
   **không thể sai** (không có đích) → thêm thử thách tất định dùng LẠI
   `PredictionCapability`, ground truth `bitsOf`/`decimalOf`/`placeValues` có sẵn.
   Sau đó M9-S3 (packet routing: học sinh tự dẫn đường, engine so chi phí với BFS).
11. Sau M9: `table/grid` (mở khoá CSDL) · practice_activity đầy đủ (cần duyệt
    riêng — vẫn **PARTIAL / CHƯA IMPLEMENT**).
12. Không có M7.15.
