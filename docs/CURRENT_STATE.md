# CURRENT_STATE.md — Trạng thái hiện tại

Cập nhật **sau mỗi milestone**. Chỉ ghi việc **đã thật sự xong** (có commit +
test). Không ghi việc đang định làm vào mục "đã xong".

> ## 🧭 ĐỌC FILE NÀY THEO HAI PHẦN — nhầm phần là hiểu ngược hệ thống
>
> **TRẠNG THÁI HIỆN TẠI** — bảng danh tính ngay dưới, rồi **§1a** (vận hành
> cuối), **§3** (năng lực đang hỗ trợ), **§4** (capability gap cố ý).
>
> **NHẬT KÝ PHÁT TRIỂN** — mọi khối `>` từ *vNext (2026-08-23)* xuống tới hết
> `W4B-3F`, cùng **§1b** và **§2** (milestone), **§5** (known issue theo wave).
> Chúng là **bằng chứng của thời điểm ghi**, phần lớn nói về hệ **Tin học** đã
> gỡ (`LEGACY_INFORMATICS_REMOVAL`, 2026-09-02). Số liệu, tên module và tên
> lệnh trong đó **không** mô tả hệ đang chạy — và không được sửa lại, vì sửa
> bằng chứng lịch sử là làm mất mốc so sánh.
>
> Kiến trúc hiện tại: **`docs/THESIS_ARCHITECTURE.md`**. Tuyên bố ↔ bằng chứng ↔
> giới hạn: **`docs/THESIS_READINESS.md`**.

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
> | `CACHE_VERSION` | **95** — kiểm: `grep -n 'CACHE_VERSION = ' backend/app/main.py` |
> | `HISTORY_SCHEMA_VERSION` | **2** — kiểm: `grep -n 'HISTORY_SCHEMA_VERSION' frontend/src/state/history.ts` |
> | Năng lực hình học | **11 phép dựng · 8 câu lệnh · 7 phép đo** — kiểm: `backend/.venv/Scripts/python.exe backend/scripts/audit_named_operand_ergonomics.py` |
> | `simulation_id` sản phẩm | **`generic.semantic_program`** — duy nhất. Danh mục 24 target Tin học đã gỡ (`LEGACY_INFORMATICS_REMOVAL`, 2026-09-02); xem `docs/SCOPE_ALIGNMENT_AUDIT.md` |
> | Archive (read-only) | tag **`m17-w2b-deep-hardening-archive`** → `feb12d8` — kiểm: `git rev-parse m17-w2b-deep-hardening-archive` (nhánh cùng tên đã xoá 2026-08-24) |
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

### 1a-bis. Trạng thái vận hành HIỆN TẠI (2026-09-05) — đọc bảng này trước

⚠️ **§1a bên dưới tự xưng là "CUỐI" nhưng đông cứng ở 2026-09-02.** Nó là bằng
chứng lịch sử, không phải trạng thái hiện tại: số của nó (pytest 2760 · vitest
646/47 · candidate `a075e9f5…` 86 file) đã bị các wave sau đó vượt qua. Giữ
nguyên khối ấy theo policy của file; đính chính nằm ở đây.

⚠️ **Và chính bảng này cũng đã trôi một lần** — bản 2026-09-04 ghi pytest 3335 ·
`CACHE_VERSION` 78 · candidate `0f5d126b…`, tức đứng yên trong khi bốn wave cong
(`ANALYZE…` → `CURVED_DISTANCE_WITNESS_VERIFICATION`) đẩy cache 78 → 81 và đóng
băng lại candidate hai lần. Đo lại bằng lệnh ở `CLAUDE.md §3` thay vì tin bảng;
mỗi wave đóng phải sửa **ở đây**, không chỉ thêm một mục mới bên dưới.

Đo lại trên cây SẠCH **2026-09-08** sau `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION`.
**0 API call thật** ở toàn bộ bảng này.

⚠️ **VÀ NÓ ĐÃ TRÔI LẦN THỨ BA — sửa 2026-09-08.** Bản trước ghi pytest **4436** ·
`CACHE_VERSION` **89** · candidate `adbb3514…` (91 file), trong khi nguồn đã ở
pytest **4707** · `CACHE_VERSION` **94** · candidate `ddeb0518…` (92 file). Tức
cùng MỘT file mang hai giá trị `CACHE_VERSION` khác nhau: bảng danh tính đầu
file (**có** sync-lock) nói 94, bảng này (**không** có) nói 89. Ba lần trôi
liên tiếp ở cùng một chỗ không còn là sơ suất — nó là hình dạng của một bảng
không có cổng. Cho tới khi có cổng: **lấy số ở bảng danh tính, hoặc đo lại**.

⚠️ **Bảng này đã trôi LẦN THỨ HAI, và lần này trôi đúng ô người ta tới đây để
đọc.** Bản 2026-09-05 ghi `CACHE_VERSION` **81** trong khi nguồn đã ở **85** —
bốn wave (`OBLIGATION_BINDING_CONTRACT` → `DERIVED_POINT_CONSTRUCTION_ENFORCEMENT`)
bump mà không sửa ở đây. Hệ quả vận hành, ghi ra để khỏi lặp:

> **Bảng danh tính ở đầu file có sync-lock (`test_current_state_identity.py`);
> bảng này thì KHÔNG.** Số nào quyết định điều gì thì lấy ở bảng danh tính, hoặc
> đo lại bằng lệnh ở `CLAUDE.md §3`. Bảng này là ảnh chụp một lượt chạy, và
> **mỗi wave đóng phải sửa Ở ĐÂY**, không chỉ thêm mục mới bên dưới.

> ⚠️ **TRÔI LẦN THỨ TƯ — đo lại 2026-09-10 (`RESEARCH_GAP_AND_SYSTEM_CONTRIBUTION_FORMALIZATION`).**
> Hai hàng dưới đây **SAI** so với nguồn, đã kiểm bằng máy hôm nay:
> `CACHE_VERSION` thật là **95** (`lock_cache_identity.py --verify` exit 0) và
> freeze verify cho **`96a9368b50603c79…`**, 92 file — không phải `94` /
> `d72db7c3…` như bảng ghi. Hai hàng `pytest`/`vitest` **chưa đo lại** trong wave
> ấy (wave tài liệu, 0 byte mã sản phẩm đổi) nên **không** được sửa mò: chúng vẫn
> là ảnh chụp 2026-09-09, và các commit sau đó ghi **pytest 4807 / vitest 813**.
> Lấy số ở **bảng danh tính đầu file** (có sync-lock) hoặc đo lại bằng lệnh ở
> `CLAUDE.md §3`. **Không** sửa bảng này bằng số chép lại từ commit message.

| | |
|---|---|
| pytest | **4781 pass, 1 skipped, 1 deselected** — cây SẠCH @ `f44756a`, **0 đỏ** (đo 2026-09-09 sau `SCENE3D_VISUAL_SEMANTIC_FIDELITY_REVIEW`). ⚠️ **Đính chính**: bản trước ghi **4772** — đó là số đo **trước** bản vá ánh xạ tên witness của chính wave `THESIS_FINAL_ACCEPTANCE_EXECUTION` (nhóm test `H*` thêm sau lượt live) và **không được đo lại**. Kiểm: `pytest --collect-only -q` cho **4777 collected** ở CẢ `HEAD` lẫn `HEAD~1`, nên chênh lệch là **nợ đo**, không phải test mới của wave này |
| vitest | **790 pass / 53 file** — đo 2026-09-09 sau `SCENE3D_VISUAL_SEMANTIC_FIDELITY_REVIEW`, **0 đỏ** |
| build | `tsc -b && vite build` — **PASS** |
| tập demo (tất định) | `replay_demo_cases.py` — **5/5**, `REDUCED_CHAIN 1/1` |
| bề mặt sập | `audit_demo_crash_surface.py` — **6/6 biên đúng kiểu**, ném ra ngoài **0** |
| cache identity | `lock_cache_identity.py --verify` — **PASS** @ **v94** |
| freeze verify | `freeze_evaluation_candidate.py --verify` — **PASS** (**92 file**, **`d72db7c3…`** — đổi ở `THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT`, bản vá dấu trừ Unicode) |
| `CACHE_VERSION` | **94** (93 → 94 ở `OBLIQUE_CONE_SECTION_FOUNDATION` — một chuỗi `description` đổi, nằm đồng thời trong thẻ và trong lược đồ ⇒ hai băm đổi) |
| `PRODUCT_VARIANT` thẻ | **C + từ vựng elip** (`58ae082c…`, 6042 B). Hai affordance đã đo của C còn NGUYÊN VĂN; phần chênh chỉ là từ vựng |
| `semantic_environment_hash` | `a483ced9fd7546df…` (was `4d2a555a…`) |
| `grammar_card` component | `cc105e4f1da84d23…` (was `2cc55280…`) · `synthesis_schema` `6ccef323…` · `capability` `72edf39f…` — **cả hai KHÔNG đổi** |
| `stable_capability_hash` | `72edf39f6c10220d…` (đổi — `_TOAN_HANG_LENH` có thêm một ô) |

**Năm wave đã đóng sau 2026-09-02.** Bốn wave đầu KHÔNG chạm bề mặt mô hình;
wave thứ năm chạm thật (thẻ + lược đồ tổng hợp + năng lực), `prompts` thì không:

| wave | sửa gì | cache |
|---|---|---|
| `VOLUME_VERIFICATION_BRIDGE` | `check_volume` nhận `curved_solid` | 71 |
| `SCALAR_FACT_VISIBILITY` · `CARD_CATEGORY_AFFORDANCE` · `OPERAND_ROLE_HINTS` | cổng học sinh + thẻ văn phạm | 72–74 |
| `OBLIGATION_BINDING_CONTRACT` | nghĩa vụ nối vật qua witness; cổng phủ thấy vật dựng ra | 75 |
| `GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE` | cạnh phụ thuộc của vật dẫn xuất trở lại cảnh | 76 |
| `CENTER_RADIUS_CURVED_CONSTRUCTION_FOUNDATION` | khối cầu khai được bằng tâm + bán kính | 77 |
| `ANALYZE_OBLIGATION_SURFACE_COMPLETION` | `area` + `lateral_area` thành nghĩa vụ có checker | **78** |

✅ **V3 ĐÃ niêm phong lại** (2026-09-04,
`CURVED_V3_RESEAL_AFTER_SURFACE_COMPLETION`). `measured_system_hash` nay trỏ
candidate hiện tại `a696200e…`; `pool_hash 36c2153e…` và `seed = null` giữ
nguyên. Diff con dấu đúng HAI dòng (`measured_system_hash`, `niem_phong_luc`);
`POOL.json` không đổi một byte.

Chặn cuối trước lượt live đã gỡ: bề mặt nghĩa vụ đạt **18/18**, center+radius
**4/4**. Lượt live cần **seed từ ngoài** và **evaluator độc lập** — xem
`docs/CURVED_V3_RESEAL_AFTER_SURFACE_COMPLETION.md` §10.

**Hai wave nữa đã đóng sau đó, cả hai 0 lượt gọi model, KHÔNG chạm candidate**
(`a696200e…` giữ nguyên · `CACHE_VERSION` vẫn **78** · pool và con dấu không
đổi một byte · `seed` vẫn `null`):

| wave | sửa gì | cache |
|---|---|---|
| `ACCEPTANCE_SCORER_EXPRESSIVENESS_CLASS` | tách "hệ chưa biểu đạt được" khỏi "mô hình viết sai" | — |
| `V3_THRESHOLD_AND_RUN_IDENTITY_POLICY` (2026-09-05) | ngưỡng + rubric máy đọc được, băm và ghim vào `RunManifest` **1.1** | — |
| `V3_RUNNER_MANIFEST_INTEGRATION_AND_LIMITED_REPRODUCIBILITY_DECISION` (2026-09-05) | runner V3 **thật** gọi `mo_run`; tham số giải mã thành giá trị có kiểu (`RunManifest` **1.2**); trần lượt gọi dẫn xuất; quyết định `LIMITED` | — |

Đo lại trên cây sạch sau wave cuối 2026-09-05: **pytest 3518 pass**, 1 skip, 1
deselect · `certify_acceptance_runner.py` **PASS** + `V3_RUNNER_INTEGRATION
PASS`, 0 lượt gọi · freeze verify **exit 0** (89 file, `a696200e…`). Frontend
không đụng nên vitest/build giữ nguyên số ở bảng trên.

⛔ ~~**Lượt live V3 NAY được phép chạy** — `READY_FOR_INDEPENDENT_V3_LIVE = YES`.~~
**BỊ BÁC BỎ 2026-09-05** bởi một phiên evaluator **độc lập** đo lại tiền kiểm.
Điều kiện *con người* đã đạt (phiên ấy không viết `radius_sq_khai` ·
`area`/`lateral_area` · scorer · runner, chưa đọc nội dung V3) — nhưng **bộ đo**
chưa sẵn sàng, và cả hai lỗi nằm ở **đường chạy live**:

- `LIVE_ENTRYPOINT_NOT_WIRED_TO_SEALED_POOL` — `main_async:558` gán
  `chay = CA`, tức **corpus phát triển V1/V2** (9 đề đã công bố), không phải
  pool V3 đã rút; call graph `main`+`main_async`+`_chay_mot` **không gọi**
  `nap_ca_v3` · `mo_luot_do_v3` · `mo_run` · `canh_gac_truoc_luot_goi`; không
  ghi `manifest.json`; trần đặt `3n+5` (n=9 ⇒ 32) thay vì **78**.
  `V3_RUNNER_INTEGRATION PASS` xanh vì certifier gọi **thẳng** `mo_luot_do_v3`
  bằng 2 ca của chính nó — nó chưa bao giờ chạy `main_async`.
- `POOL_MONG_TYPE_INCOMPATIBLE` — `mong` pool V3 là `list`, runner dòng 467 làm
  `c["mong"] <= set(…)` ⇒ `TypeError`, **sau** khi ca đó đã tiêu quota.

Cả hai ở `backend/scripts/` ⇒ **ngoài `MEASURED_SYSTEM_PATHS`** ⇒ candidate
`a696200e…` và `pool_hash 36c2153e…` **giữ nguyên**, **không cần reseal**.
`EXTERNAL_SEED = 5324284654432805119` vẫn **chưa dùng**, `seed = null`,
`APPLICATION_LLM_CALLS = 0`; `_rut` **từ chối lần hai** — nên dừng **trước** khi
rút là thứ giữ được pool.

✅ **CẢ HAI ĐÃ ĐÓNG cùng ngày** — `V3_LIVE_ENTRYPOINT_WIRING_REPAIR`
(`docs/V3_LIVE_ENTRYPOINT_WIRING_REPAIR.md`). `main_async` nạp bộ ca từ
`nap_ca_v3()` (trả `(ca_chuẩn, ca_thô, case_set_hash)`; `mong` chuẩn hoá thành
`set` **ở loader**, `POOL.json` giữ nguyên byte), gọi `mo_luot_do_v3` trước lượt
gọi đầu, đặt cổng canh ở ranh giới **`call_gemini`** — không phải `_chay_mot`,
vì một ca gọi tới 1 analyze + 3 tổng hợp — và mang trần dẫn xuất **78** ở
`max_logical_calls`. Cả 11 consumer `CA`/`CA_HASH` trong live path đã chuyển,
gồm chỗ nguy hiểm nhất: tra ca nhánh 8B (trước đó `next(x for x in CA …)` ném
`StopIteration` với id ô). Bằng chứng: `tests/test_v3_live_entrypoint_wiring.py`
**37 pass** chạy chính `main_async`, 10 phép tiêm lỗi; certifier có nhãn mạnh
**`V3_LIVE_ENTRYPOINT_INTEGRATION`** và `READY_FOR_INDEPENDENT_V3_LIVE = YES`
chỉ phát khi nhãn ấy PASS.

Bộ đo đổi băm — runner `55be22b6…` → **`6570b57bd6ac1fe4…`**, certifier
`81799613…` → **`070189b54af2b2ae…`**; scorer · threshold · rubric · loader ·
candidate · pool · seal · `CACHE_VERSION` **không đổi**, không reseal, seed vẫn
`null`. Trạng thái hiện hành:

```
READY_FOR_INDEPENDENT_V3_LIVE = YES
RECOMMENDED_NEXT_ACTION       = INDEPENDENT_CURVED_V3_LIVE_ACCEPTANCE
```

Bản ghi blocker: `docs/V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER.md`; bằng chứng
máy `docs/evaluation/geometry/curved-v3/PREDRAW_GUARD_2026-09-05_INDEPENDENT.json`
(`3ade2a9e891ab3fe…`).

### WITNESS ĐẠI LƯỢNG KIỂM QUA CÂU LỆNH SINH NÓ — 2026-09-05

`c7a` khai `distance(container="hinh_non", witness="l")` để nói *"đường sinh"*.
`distance` là phép đo QUAN HỆ nên ba cổng cùng bác, và cổng đáng giá nhất bác
**oan**: *"witness không dẫn xuất từ `hinh_non`"* — trong khi witness **có** đo
thật, chỉ là đo từ `T` và `A`, tức toán hạng **dựng ra** chính khối ấy.

Sửa bằng resolver dùng chung `coverage_gate.phan_giai_witness`: nghĩa vụ →
`params.witness` → câu lệnh sinh witness → toán hạng thật. Attachment chứng
minh bằng `_phu_thuoc` (bao đóng dựng), chữ ký toán hạng đọc từ `BANG_PHEP_DO`.
`postconditions` import **chính** hàm ấy và dựng một nghĩa vụ tương đương trên
toán hạng đã phân giải rồi gọi **checker cũ** — không viết phép đo thứ hai.

`c7a` nay **servable**: `l=13 · V=100π · Sxq=65π`.

⚠️ Hai thứ phải nhớ. **`distance` giữ nghĩa quan hệ** — checker vẫn tính lại từ
hình, `l` chỉ là giá trị khai để đối chiếu. Và **`_theo_witness_do` thu hẹp**:
chỉ phép đo MỘT toán hạng mới đồng nhất `container ≡ of`; với phép đo quan hệ,
bí danh ấy rò sang nghĩa vụ anh em và làm `volume(hinh_non)` bị chấm trên một
ĐIỂM. Chính chiều thu hẹp này tạo stale thật ⇒ `CACHE_VERSION` 80 → 81.

Bề mặt mô hình không đổi. Báo cáo:
`docs/CURVED_DISTANCE_WITNESS_VERIFICATION.md`.

### NGHĨA VỤ `area` CỦA MẶT CẦU ĐÃ THÔNG — 2026-09-05

`analyze` phát `area` cho *"diện tích mặt cầu"* (đúng cách SGK gọi) nhưng `area`
chỉ nhận `polygon3|section|circle3`; mặt cong là `lateral_area`. Ca cầu đơn
giản nhất chết ở cổng phủ vì một lệch **từ vựng**, không phải thiếu năng lực.

Sửa bằng **một cột** `KHOI_CONG.nghia_vu_area_la` (`ball` → `lateral_area`;
trụ/nón → `None`) + helper `measure_contract.nghia_vu_chinh_tac`, và **cả cổng
phủ lẫn hậu điều kiện gọi chung helper ấy**. Lý do tương đương là hình học: mặt
cầu **không có đáy**, còn `S_tp = S_xq + S_đáy` của trụ/nón thì hai số khác
nhau — nên trụ và nón **giữ** phân biệt.

`c1a` nay đi trọn: `volume 972π` · `area 324π` · servable. Bề mặt mô hình
**không đổi một byte** (lược đồ · thẻ · prompt · `stable_capability_hash` ·
`semantic_environment_hash` đều nguyên) — thứ đổi là cách **hệ đọc nghĩa vụ của
đề**. `CACHE_VERSION` 79 → 80 theo LUẬT (đổi policy định tuyến); kiểm cache cho
thấy **không** envelope nào hoá sai, vì `main.py` chỉ cache `status == "ok"` nên
bản từ chối chưa bao giờ được cache.

Báo cáo: `docs/CURVED_OBLIGATION_SURFACE_ALIGNMENT.md`.

### BỘ ĐO THẲNG HÀNG VỚI SẢN PHẨM — 2026-09-05

Hai wave liên tiếp sửa hai tầng khác nhau của cùng một bệnh *"guard/bộ đo không
nằm trên đường chạy thật"*:

| wave | tầng | nhãn certifier |
|---|---|---|
| `V3_LIVE_ENTRYPOINT_WIRING_REPAIR` | **pool** — `main_async` nay nạp bộ ca từ con dấu | `V3_LIVE_ENTRYPOINT_INTEGRATION PASS` |
| `ACCEPTANCE_POST_MODEL_PATH_ALIGNMENT` | **chấm điểm** — đáp số từ `outcome.final_memory`, cảnh từ `pipeline._dung_scene3d`, phán quyết từ `acceptance_verdict.phan_loai` | `ACCEPTANCE_POST_MODEL_PATH_INTEGRATION PASS` |

`READY_FOR_FUTURE_CURVED_ACCEPTANCE = YES` đòi **cả hai** — một lượt đo đi đúng
pool mà chấm sai tầng vẫn cho ra con số sai.

Bốn cột nay **tách rời**: `runtime_executable` · `exact_answer_match` ·
`scene3d_pass` · `postconditions_pass` · `servable`. `c7a` là fixture chuẩn: ba
cột đầu True, hai cột sau False — chương trình ĐÚNG mà hệ không dám phát.

Danh tính: runner `6570b57b…` → **`3cabd207…`**, certifier `ce0d44d9…` →
**`bbbed77b…`**; scorer · threshold · rubric · loader · candidate `93c47d9a…` ·
`CACHE_VERSION 79` **không đổi**. 0 lượt gọi model, V3 gốc byte-identical.
Báo cáo: `docs/ACCEPTANCE_POST_MODEL_PATH_ALIGNMENT.md`.

### LƯỢT V3 ĐÃ CHẠY — 2026-09-05, kết quả `FAIL`

```
EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED       ← KHÔNG độc lập, miễn trừ có khai
MEASUREMENT_CLASS      = INTERNAL_ONE_SHOT_ACCEPTANCE
DRAW_COUNT = 1 · seed 5324284654432805119 · CASE_SET_HASH eb1c402a…
LOGICAL_CALLS 26/78 · RUN_VALIDITY = VALID
```

**0/9 ca dương servable.** ball 0/3 · cylinder 0/3 · cone 0/3 · exact-answer ~~0/9~~ → **1/9** sau đính chính (`V3_PRODUCT_PATH_PARITY_CORRECTION` 2026-09-05: runner đọc đáp số từ `envelope['scene3d']` mà `route` cố ý không dựng ⇒ phép chiếu luôn rỗng; `c7a` thật ra ĐÚNG cả ba đáp số và là lỗi **HỆ**, không phải mô hình). Ca âm 4/4 fail-closed nhưng chỉ **1/4** chạm đúng ranh giới cong — ba ca
còn lại chết ở cùng cổng grounding đã giết các ca dương, tức fail-closed **vì
lý do sai**. `PRODUCT_CAPABILITY_CHANGED = NO`; ba family giữ `foundation_only`.

Nút thắt **không phải** thứ đã dự đoán. Wave trước chuẩn bị đo khoảng trống
**derived-scalar** (đường kính → bán kính) — và **không ca nào rút trúng** nó,
nên nó vẫn `NOT_MEASURED`. Thứ lộ ra là **CONSTRUCTION-GROUNDING**, chứng minh
tất định (0 lượt gọi) ở `CURVED_V3_LIVE_ACCEPTANCE.md` §8:

- `construct_curved_solid` **bắt buộc** một `anchor: point3`; grounding gate
  check ⑤ đòi `la_ten_nguon(tên, đề)` — tên biến phải có trong đề. Đề "khối cầu
  bán kính 9" **không đặt tên điểm nào** ⇒ 5/5 biến thể khai tâm đều bị chặn.
- `radius` **chỉ dùng cho khối cầu** (`khai_bang_ban_kinh`); trụ/nón bắt buộc
  `rim_point` — một điểm trên vành, thứ đề SGK không bao giờ đặt tên. 5/5 đường
  bị chặn, **kể cả** đường DỰNG bằng `translate`.
- ~~`radius` của `circle3` sinh từ phép giao không suy ra được ⇒ 2 ca
  `SYSTEM_COVERAGE_FAILURE`.~~ → **ĐÍNH CHÍNH** (`CURVED_SECTION_RADIUS_PATH_
  ADJUDICATION`, 2026-09-05): **suy ra được**, và đã suy được từ trước lượt V3.
  Replay tất định trên chính hai chương trình ấy cho `r=9 · S=81π` (`c5b`) và
  `r=6` (`c9b`). Hai ca chết vì mô hình gọi `construct_section` — phép của khối
  **đa diện** — thay vì `intersect_plane_curved`. Phân loại đúng là
  **`MODEL_FAILURE`**, không phải `SYSTEM_COVERAGE_FAILURE`. Xem mục dưới.

⚠️ Lượt đo chỉ đo được **one-shot**: `REPAIR_ELIGIBLE_FAILURES = 0` nên 8B không
chạy, và `EVENTUAL` bằng `FIRST_ATTEMPT` **theo cấu trúc**, không theo đo đạc.

```
RECOMMENDED_NEXT_ACTION = CURVED_CONSTRUCTION_GROUNDING_FOUNDATION
```

Ba việc sửa đều đụng `backend/app` ⇒ phá đóng băng candidate ⇒ cần quyết định
riêng + reseal. Và pool V3 **đã tiêu**: đo lại phải niêm phong pool mới.
Báo cáo: `docs/CURVED_V3_LIVE_ACCEPTANCE.md`; artifact
`docs/evaluation/geometry/curved-acceptance-v3/`.

⚠️ **Giới hạn phương pháp phải khai trong khoá luận**: model gọi bằng **alias**
`gemini-2.5-flash`, tái lập ở mức **`LIMITED`** — quyết định của người hướng
dẫn, khoá trước kết quả (policy `1.1.0`, băm `460e0ce5…`). Ghi đủ alias, thời
điểm UTC, SDK, tham số gửi và raw output; **không** tuyên bố tái lập
bit-for-bit. Chi tiết:
`docs/V3_RUNNER_MANIFEST_INTEGRATION_AND_LIMITED_REPRODUCIBILITY_DECISION.md`
§1, §8, §15.

### THIẾT DIỆN TRÒN: KHÔNG CÓ KHOẢNG TRỐNG — 2026-09-05

Wave trước đặt việc kế tiếp là `CURVED_SECTION_RADIUS_COVERAGE`, gọi nó là
*"khoảng trống hệ đã khai trong `contract.py`"*. **Dự đoán ấy sai**, và replay
tất định (0 lượt gọi model) chứng minh ngược lại: đường
`intersect_plane_curved → circle3 → measure(radius|area)` đã thông **đủ mười
tầng**, từ lược đồ IR tới `scene3d-view.tsx:171`, trên đúng candidate đang đóng
băng. `contract.py` không khai một khoảng trống — nó khai một **hợp đồng kiểu
hẹp có chủ đích**: phép giao trả `circle3` và **chỉ** `circle3`, các ca suy biến
bị từ chối kèm **tên phép dựng đúng** (`project_onto` cho tiếp xúc,
`construct_polygon` cho thiết diện qua trục).

Ablation vét cạn trên **chính chương trình mô hình đã sinh** cho bảng delta tối
thiểu — và nó nhỏ hơn tưởng:

| ca | delta tối thiểu | đáp số |
|---|---|---|
| `c5b` | **2** — `khai[C: section→circle3]` + `producer[construct_section→intersect_plane_curved]` | `r_C = 9` · `area_C = 81π` |
| `c9b` | **3** — hai cái trên + `ratio[9/6→3/5]` | `ban_kinh_c = 6` |

Hai điều đáng nhớ. **`hinh_tru: solid → curved_solid` KHÔNG load-bearing** — bỏ
nó vẫn `served`, vì `ir_static_check` suy kiểu từ **câu lệnh dựng**, không từ
dòng khai báo. Và **`c9b` có hai khiếm khuyết mô hình độc lập**: cổng phủ bác
trước nên khiếm khuyết thứ hai (`ratio` — mô hình đọc dữ kiện thành tỉ số
`SM:MO` thay vì tham số `t` mà `DivideSegmentExpr` định nghĩa) chỉ lộ ra sau khi
vá cái thứ nhất.

**Không một dòng mã sản phẩm nào đổi.** Lược đồ · prompt · `CACHE_VERSION` (81)
· candidate (`d105f83e…`) đều nguyên. Thứ wave này thêm là 32 test khoá năng lực
đang có, trong đó **11 phép tiêm lỗi** đã chứng minh đỏ được — đáng chú ý nhất
là tiêm ⑩ (gỡ hệ số đồng dạng `(1−t)²` của nón): **không cổng nào bắt được**, hệ
vẫn xanh và chỉ trả sai số. Đó là lý do bộ test khoá **giá trị**, không khoá
riêng `servable`.

⚠️ **Phát hiện phụ, chưa sửa, đã khoá**: `coverage_gate` đọc
`memory_declarations` để biết kiểu, còn `ir_static_check` suy kiểu từ câu lệnh
dựng — **hai nguồn sự thật cho một câu hỏi**. Khi lệch, một chương trình tính
đúng vẫn bị bác vì một dòng khai báo. Ngoài charter của wave này; `test_T4b`
khoá hành vi đang có và nói rõ nó khoá *trạng thái*, không tuyên bố trạng thái
ấy đúng.

```
RECOMMENDED_NEXT_ACTION = CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE
```

Câu hỏi còn mở không phải *"hệ có làm được không"* mà **vì sao mô hình không
tìm ra `intersect_plane_curved`** dù phép ấy có trong văn phạm được gửi. Wave ấy
**tiêu quota** và cần pool niêm phong mới — V3 đã tiêu.
Báo cáo: `docs/CURVED_SECTION_RADIUS_PATH_ADJUDICATION.md`.

### MÔ HÌNH KHÔNG TỰ TÌM RA `intersect_plane_curved` — 2026-09-05

Wave trước đóng câu *"hệ có làm được không"* bằng replay: **có**, đủ mười tầng.
Wave này đo câu còn lại — *"mô hình có tự tìm ra không"* — trên 8 đề mới, ký
hiệu khác V3 hoàn toàn. `MEASUREMENT_CLASS = DEVELOPMENT_DIAGNOSTIC`,
`HELD_OUT_CLAIM = NO`, 26 lượt gọi logic (trần 32), 150 854 token.

**Lượt đầu: 0/6 ca cong chọn đúng. 8/8 ca chọn `construct_section`** — kể cả ca
đối chứng đa diện (ở đó nó **đúng**, và `served` với `8√3` chính xác) lẫn ca âm.
Quỹ đạo toán tử:

```
d1 CS→IPC   d2 CS→IPC→IPC   d3 CS→CS→IPC   d4 CS→IPC
d5 CS→IPC   d6 CS→IPC       d7 CS (đúng)   d8 CS→CS→CS
```

Sau **một** lượt sửa, **6/6** chuyển sang `intersect_plane_curved` + `circle3`.
Bộ dạy là chính câu báo lỗi tĩnh: `IR_OPERAND_TYPE: cần solid, có curved_solid`.
Nên `construct_section` không phải một nhầm lẫn ngẫu nhiên — nó là **mặc định
phổ quát** của mô hình cho mọi bài có chữ *"thiết diện"*, và `c5b`/`c9b` của V3
chỉ là hai mẫu của cùng thiên lệch ấy.

`EVENTUAL_SERVABLE = 0/6` cong, vì sau khi toán tử được sửa thì các ca chết ở
**tầng khác**: 3/6 vì `analyze` đặt container là nhãn đề `(σ)`/`(δ)`/`(λ)` —
trái chính chỉ dẫn của nó (`geometry_analyze.md:38`: *"tên biến snake_case,
không dấu"*) — và `stage_semantic_analyze` **không có vòng sửa** nên không cứu
được; 2/6 vì điểm phải-dựng-ra khai bằng toạ độ (nút thắt
CONSTRUCTION-GROUNDING của V3, **vẫn mở**); 1/6 vì bịa `source_fact_id`.

```
CURVED_SECTION_MODEL_DISCOVERABILITY = WEAK   (tự phát hiện 0/6 · dùng được sau sửa 6/6)
DOMINANT_FAILURE = STATEMENT_EXPR_OR_OPERATOR_AFFORDANCE
RECOMMENDED_NEXT_ACTION = MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT
```

✅ **Lỗi hệ nêu dưới đây ĐÃ ĐÓNG cùng ngày** —
`CURVED_SCALAR_AXIS_INTERSECTION_FIX`, xem mục ngay sau mục này. Giữ nguyên mô
tả bên dưới làm bằng chứng rằng probe tìm ra nó **trước** khi tiêu quota.

⚠️ **Một lỗi hệ tìm được trong gold preflight, CHƯA sửa** *(trạng thái lúc probe
chạy)*: `CURVED_SCALAR_DECLARED_SOLID_CANNOT_BE_CUT`. Trụ/nón khai bằng `height` (vô
hướng) — đúng đường mà `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` mở cho đề
không đặt tên điểm — **không cắt được**: `_giao_tron_xoay` đọc `s.truc` (vectơ
trục, **bằng vectơ không** khi khai bằng chiều cao) thay vì `s.huong_truc`,
chính thuộc tính wave ấy thêm cho ca này. Kết quả là `ZeroDivisionError` trần,
phân loại sai thành `capability_gap`, và tên ngoại lệ Python rò lên `details`.
Lại đúng hình dạng lỗi cả loạt wave vừa rồi đuổi theo: **một sửa chữa không nằm
trên đường chạy thật**. Nó **không kích hoạt** trong lượt đo (mô hình khai bằng
`apex_or_top` 8/8), và điều đó khẳng định được vì luật quy kết đã đăng ký trước.
Khoá bằng `test_LOI_HE_*` — hai test ấy sẽ ĐỎ khi lỗi được sửa, và đỏ là đúng.

Mã sản phẩm · lược đồ · thẻ văn phạm · prompt · `CACHE_VERSION` 81 · candidate
`d105f83e…` đều không đổi; V3 không chạy lại.
Báo cáo: `docs/CURVED_SECTION_MODEL_DISCOVERABILITY_PROBE.md`; artifact
`docs/evaluation/geometry/curved-section-discoverability-dev-v1/`.

### KHỐI CONG KHAI BẰNG VÔ HƯỚNG NAY CẮT ĐƯỢC — 2026-09-05

Đóng lỗi mà probe tìm ra ở mục trên. `_giao_tron_xoay` đọc `truc` — vectơ trục,
**bằng vectơ không** khi khối khai bằng `height` — thay vì `huong_truc`, chính
thuộc tính `CURVED_CONSTRUCTION_GROUNDING_FOUNDATION` thêm cho ca này. Hai hỏng
chứ không một: chốt ⊥ trục **im lặng nhận mọi mặt phẳng** (tích có hướng với
vectơ không thì luôn bằng không), và `d·d = 0` ném `ZeroDivisionError` trần.

Bản vá, bốn điểm:

- chốt ⊥ trục đọc **hướng**;
- tâm đường tròn **là** giao điểm trục × mặt phẳng — bỏ hẳn `anchor + truc·t`,
  phép cần một vectơ mang độ dài mà cách khai vô hướng không có;
- kiểm biên bằng **bình phương** (`L² · u·u ≤ h²`) nên không cần `√h` — nhờ vậy
  trụ chiều cao vô tỉ vẫn cắt được chính xác;
- đổi thang `L → t` **chỉ** ở nhánh vô hướng. `huong_truc` không chuẩn hoá: khai
  bằng điểm thì `|u| = h` nên `L` đã là tỉ lệ, khai bằng vô hướng thì `|u| = 1`
  nên `L` là khoảng cách tuyệt đối. Quên điều này thì **trụ vẫn đúng còn nón sai
  im lặng** — hai phép tiêm riêng canh đúng chỗ ấy.

Nhánh khai bằng điểm **tương đương đại số** với luật cũ (`L²h² > h² ⟺ L > 1`),
nên không đổi một bit nào. Oracle 7/7 khớp giá trị tính trực tiếp từ dữ kiện;
parity điểm ↔ vô hướng 7/7 trên tâm · mặt phẳng · `radius_sq` · bán kính · diện
tích. Đường sản phẩm `served` 2/2: trụ `9`/`81π`, nón `6`.

Biên còn nguyên mã cũ, và có thêm một biên **được nói ra**: nón với `h` vô tỉ trả
`CURVED_SECTION_OUTSIDE_V1_CLOSURE` kèm lối đi thay thế (khai bằng điểm trên
trục), vì `r'² = r²(h−L)²/h²` chứa `h` nên rơi ngoài ℚ.

`CACHE_VERSION` **81 → 81, KHÔNG bump**: sáu băm model-facing byte-identical, và
`main.py` chỉ cache `status == "ok"` trong khi bản vá chỉ biến *từ chối → phục
vụ*. Candidate `d105f83e…` → **`a5b63aa3…`**. 0 lượt gọi model.
Báo cáo: `docs/CURVED_SCALAR_AXIS_INTERSECTION_FIX.md`.

### THẺ NÓI RA KIỂU KẾT QUẢ — CHỌN PHÉP HẾT LÀ NÚT THẮT — 2026-09-05

A/B ghép cặp, 24 lượt gọi logic (trần 24). Một `analyze` mỗi đề, hợp đồng dùng
**y nguyên** cho cả hai arm; hai arm chỉ khác thẻ văn phạm; lịch A→B/B→A luân
phiên, khoá trước khi xem kết quả.

| lượt tổng hợp ĐẦU, 6 ca cong | A | B |
|---|--:|--:|
| chọn đúng toán tử cho kết quả được hỏi | **1/6** | **6/6** |
| `served` ngay lượt đầu | **0/6** | **3/6** (đáp số đúng 3/3) |

Ghép cặp **5 thắng · 0 thua**. Ca đối chứng đa diện: cả hai arm chọn
`construct_section` — B không khái quát hoá quá tay.

Nguyên nhân đã sửa: **thẻ in TOÁN HẠNG của mọi phép và không in kiểu KẾT QUẢ
của phép nào**, dù cả hai vế đã nằm sẵn trong thẩm quyền (`_CHU_KY` vế phải,
`_KIEU_DUNG`). Nhãn `[BIỂU THỨC→assign]` nói **cửa tiêu thụ**, không nói **kiểu
ra** — hai câu khác nhau, và câu thứ hai mới là thứ nối *"tính bán kính đường
tròn thiết diện"* với một phép cụ thể. Bằng chứng phân biệt: ở `dev-v1`, lượt
đầu khai `curved_solid` **5/8** dù thẻ không liệt kê kiểu ấy, nhưng khai
`circle3` **0/8** — và `circle3` chỉ tồn tại với tư cách kiểu kết quả.

Phụ, cùng gói: danh sách kiểu khai được là bản **chép tay đã trôi** (thiếu
`circle3`/`curved_solid` từ wave cong 2026-09-03), nay **dẫn xuất** theo luật
*"mọi kiểu thẻ nhắc tới đều phải khai được"*.

Delta **+203 byte** (178 mũi tên trên 17 dòng · 25 danh sách kiểu), phân loại
**NHÃN THIẾU**; trần thẻ hình học 5510 → 5720. **Thẻ đầy đủ không đổi.**
`CACHE_VERSION` **81 → 81, KHÔNG bump** — thẻ đổi thứ mô hình *viết ra*, không
đổi nghĩa chương trình nào, và `main.py` chỉ cache `status == "ok"`; identity
khoá lại `9a230794…`. Candidate `a5b63aa3…` → **`67ad7f4f…`**.

⚠️ **Nút thắt đã DỜI, không biến mất.** Ba ca B chọn đúng phép mà vẫn không
phục vụ được, và 4/8 ca hỏng ở **cùng một chỗ**: xuất xứ của điểm có tên — khai
`point3` không giá trị và không câu lệnh dựng (`e2`,`e6`) · có `initial_value`
mà thiếu `source_fact_id` (`e7`) · có giá trị cho một tên grounding không khớp
(`e8`). Thêm liên kết tên `analyze`/`synthesis` (`e4`, và `dev-v1` 3/6).

```
SELECTOR_GAIN_OBSERVED = YES   ·   CHANGE_ACCEPTED = YES
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
RECOMMENDED_NEXT_ACTION = NAMED_POINT_PROVENANCE_AFFORDANCE_ALIGNMENT
```

Báo cáo: `docs/MODEL_FACING_OPERATION_AFFORDANCE_ALIGNMENT.md`; artifact
`docs/evaluation/geometry/operation-affordance-ab-v1/`.

### KHAI BÁO ĐIỂM: `at` BỊ BỎ IM LẶNG — ĐÃ ĐÓNG — 2026-09-06

`MemoryDeclaration` không khai `model_config`, nên Pydantic dùng mặc định
`extra="ignore"`. Mô hình gửi `{"name":"X","type":"point3","at":[0,0,0]}` — ô
của **câu lệnh** `declare_point` đặt trong **khai báo** — và `at` **biến mất
không dấu vết**. Lời từ chối cuối cùng nó nhận được là *"có khai báo nhưng chưa
có giá trị"*: **đúng sự thật, sai chỗ**. Toạ độ đã được cho; chỉ để nhầm ô.

Vá tại `validate_semantic_program`, **trước** `model_validate` — biên cuối cùng
còn giữ đầu vào thô. Chẩn đoán nêu đủ bốn thứ, **dẫn xuất hết từ model**: đường
dẫn JSON · trường đã gửi · chủ sở hữu (`declare_point`) · ô chính tắc
(`initial_value`). **Từ chối chứ không quy đổi**, theo đúng doctrine đã ghi
trong `DeclarePointStmt`: *"ánh xạ ấy không bảo toàn xuất xứ"*.

Replay hai ca của A/B qua đúng đường sản phẩm:

| ca | gốc | +đổi ô | +xuất xứ |
|---|---|---|---|
| `e6` | `validator` | **`served` · `400π` · scene 8** | — (đã đủ) |
| `e2` | `validator` | `grounding` (`X` thiếu `source_fact_id`) | **`served` · `121π` · scene 12** |

⚠️ **Luật đã THU HẸP sau khi replay corpus lịch sử.** Bản đầu bác mọi khoá lạ
và bác oan **3/5** chương trình AI sinh — chúng đặt `label` trong khai báo.
`label` là `Optional[str]`, trang trí; `at` là `list[Any]`, **ô giá trị thô**.
Chỉ báo khi có **dữ liệu bị mất**, và phép phân biệt dẫn từ annotation.

⚠️ **ĐÍNH CHÍNH quyết định A/B của wave trước.** Luật đăng ký liệt sáu điều
kiện giữ B; điều kiện *"B trả đúng ranh giới ở ca âm"* **không đạt** (`e8` không
arm nào chạm bao đóng v1). Báo cáo wave ấy ghi "ghi riêng" rồi vẫn nhận B — đọc
sai luật của chính nó. Nhánh đăng ký đã được thực hiện: **thẻ sản phẩm về A**
(`grammar_card e0fbbc84…`, `semantic_environment f7def620…` — đúng giá trị
tiền-A/B), B đóng băng thành `card_B.txt` làm ứng viên thử nghiệm, runner A/B
nay đọc **cả hai** thẻ từ artifact. Lợi ích của B **giữ nguyên kết luận**:
1/6 → 6/6, thắng 5 thua 0, `SELECTOR_GAIN_OBSERVED = YES`.

`CACHE_VERSION` **81 → 81, KHÔNG bump**, kiểm bằng **một row cache thật**:
`_cache_lookup` so `policy_version`, row baseline vẫn hit sau bản vá. Candidate
`67ad7f4f…` → **`4f813a38…`**. 0 lượt gọi model.

```
RECOMMENDED_NEXT_ACTION = OBLIGATION_CONTAINER_NAME_BINDING
```

Lỗi còn lại mạnh nhất, đếm qua hai lượt đo độc lập: `container` không phải định
danh — `dev-v1` 3/6 + `ab-v1` `e4` = **4 ca**. Cùng hình dạng vừa xử ở đây: một
luật được nói trong prompt (`geometry_analyze.md:38`) mà **không ai cưỡng chế**,
rồi nổi lên hai stage sau dưới một mã không nói gì về nguyên nhân.
Báo cáo: `docs/POINT_INITIALIZATION_CONTRACT_ALIGNMENT.md`.

### NGHĨA VỤ NỐI VỚI VẬT QUA XUẤT XỨ DỮ KIỆN — 2026-09-06

⚠️ **Đính chính chẩn đoán của mục ngay trên.** Mục ấy ghi lỗi còn lại là
*"`container` không phải định danh"*. Câu ấy **SAI**, và artifact bác nó ngay:
`e5` có `container = "(j)"` — cũng dấu ngoặc — và **served**. Dấu ngoặc không
phân biệt được thành công với thất bại.

Nguyên nhân thật: khi container là **nhãn đề đặt cho vật DẪN XUẤT** và vật ấy
vắng mặt khỏi chương trình dưới cái tên đó, việc nối nghĩa vụ với vật rơi
**hoàn toàn** vào ba lưới CHÍNH TẢ.

```
e5  `(j)` ↔ `(j)`             trúng thẳng, không cần lưới
e1  `(u)` ↔ `u`               lưới ③ — MAY RỦI chính tả
e4  `(t)` ↔ `duong_tron_t`    KHÔNG lưới nào (`ten_loi` → `tront`)
```

Net ⓪ không cứu được vì nó cố ý đòi container **có mặt** với kiểu sai.

Lỗ thứ hai, tìm được khi đi tìm bằng chứng: mô hình **đã tự khai**
`source_fact_id` ở `assign` — dữ kiện *"Mặt phẳng cắt hình nón theo đường tròn
(t)"*, đúng container — nhưng `AssignStmt` không có ô ấy nên Pydantic
`extra="ignore"` **vứt im lặng**. Đúng lớp lỗi ô `at` của mục trên.

Sửa hai chỗ: `_nang_xuat_xu_cau_lenh` chở lời khai về khai báo (chỉ điền chỗ
trống, không đẻ khai báo mới) + net ⓪b `_theo_xuat_xu_du_kien` ở cổng phủ,
chạy khi container VẮNG MẶT và đòi dữ kiện được viện **nêu đúng tên** — điều
kiện chặn phản ví dụ `hinh_lang_tru`/`chop`. Net ⓪b đứng **SAU** ba lưới, nên
`e1`/`e5` không đổi một chút nào. Bộ lọc witness rút ra **dùng chung** với net ⓪.

⚠️ **KHÔNG thêm ô vào `AssignStmt`** — bản thử đầu làm thế và đỏ 9 test, gồm
`test_AB1`/`test_E8`: `generate_json_schema()` là `responseSchema` thật và thẻ
dẫn từ `model_fields`, nên thêm ô là đổi **affordance**, thứ phải đo bằng A/B
mà wave này có ngân sách 0. Kết quả: schema `9b186828…` · thẻ == `card_A.txt` ·
prompt · capability **nguyên vẹn**; `PRODUCT_VARIANT` vẫn **A**.

**Gỡ tấm che thì `e4` lộ khiếm khuyết THỨ HAI, của MÔ HÌNH, độc lập:**
`ratio 5/2` (quy ước chia đoạn `m:n`) thay vì tham số `t = 5/7` ⇒
`CURVED_PLANE_DOES_NOT_CUT`. Sửa **một token** trên hợp đồng nguyên văn ⇒
`served`, **bán kính 15**. Delta ấy một mình KHÔNG cứu được ca (`test_B2b`).
Cùng lớp `c9b` — đây là lần tái hiện **thứ hai**.

`tests/geometry/test_obligation_container_binding.py` **27 pass** (nền đỏ
**11/27**), 11 phép tiêm/phản ví dụ. `CACHE_VERSION` **81 → 81, KHÔNG bump**,
ba căn cứ đo được: bề mặt mô hình nguyên · chiều đổi chỉ là *từ chối → phục vụ*
mà `main.py` chỉ cache `ok` · phép nâng **không** làm grounding chặt thêm (bịa
`source_fact_id` ở mọi `assign` của `e1`/`e5` thì cả hai vẫn `served`).
Candidate `4f813a38…` → **`c39f7358…`**. 0 lượt gọi model.

```
RECOMMENDED_NEXT_ACTION = DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB
```

Đường tất định của binding đã thông, nên theo luật *"thông rồi thì đo tác động
lên khả năng tự sinh"*, việc kế tiếp là một **A/B phát triển nhỏ** trên đúng
lỗi đã tái hiện hai lần. Thẻ in `ratio:tên` **không chú thích**, trong khi `a`
và `b` đều có — nên thẻ chưa từng nói `ratio` là tham số `t`.
Báo cáo: `docs/OBLIGATION_CONTAINER_NAME_BINDING.md`.

### A/B AFFORDANCE `divide_segment.ratio` — 2026-09-06, GIỮ BASELINE A

Lượt A/B tổng hợp đầu tiên chạy với **`ANALYZE_LIVE_CALLS = 0`**: hợp đồng cố
định, đã kiểm tất định (gold 4/4 `served`), nên phép đo hỏi đúng một câu —
*"cho CÙNG một hợp đồng, thẻ nào làm mô hình soạn đúng hơn"*.

`ROOT_CAUSE` affordance đo được: thẻ in **`ratio:tên`** — nhãn **KIỂU SAI**
(`_la_ten` trả `True` cho mọi `str` trần) **và không có chú thích**, vì
`_vai_tro` (hàm in `Field.description`) chỉ chạy ở nhánh ô-TÊN. Mô tả
`"phân số, vd 2/3"` nằm sẵn ở `contract.py:625` **chưa bao giờ tới thẻ**.

Delta đăng ký: **+60 byte, đúng 1 dòng** (`_VAN_XUOI['ratio']`);
`responseSchema` **không đổi** — hai arm dùng lược đồ y hệt.

| | A | B |
|---|---|---|
| `t` đúng, ca mục tiêu | 2/3 | **3/3** (thắng 1 · thua 0) |
| **`POSITION_CORRECT`** ← tiêu chí ĐĂNG KÝ | **3/4** | **1/4** |
| token / ca served đúng | **8 435** | **21 998** |

⚠️ **Nhiễu lấn át:** 3/4 lượt B chết ở `grounding` vì thiếu `source_fact_id` —
**không liên quan `ratio`**. `n = 4` one-shot không tách được delta khỏi nhiễu,
nên tín hiệu đăng ký **không đạt** ⇒ **giữ baseline A**, không nới luật.

⚠️ Ba điều phải khai kèm mọi lần dẫn số: `TOKEN_CEILING_EXCEEDED`
47 303/40 000 (guard kiểm theo CẶP) · đính chính bộ chấm (`T_CORRECT` so chuỗi
thay vì hữu tỉ — `9/12` vs `3/4`; đã chấm lại 0 lượt gọi, **không đổi quyết
định**) · `CHI_PHI_TOAN_PIPELINE = NOT_MEASURED`.

⚠️ **Phát hiện an toàn:** `r3/A` **`served` một đáp số SAI** (`15/2` thay vì
`8`). Mọi cổng đều đúng — checker tính lại từ hình cho đúng điểm chương trình
dựng — nên hiểu nhầm `ratio` hỏng theo kiểu **IM LẶNG**, không fail-closed.

Wave **không chạm `MEASURED_SYSTEM_PATHS`**: `CACHE_VERSION` 81 → 81, candidate
`c39f7358…` không đóng băng lại, `PRODUCT_VARIANT` vẫn **A**.

```
RECOMMENDED_NEXT_ACTION = RATIO_AB_CONFOUND_REMOVAL_REPEAT
```

Lặp lại đúng phép đo này sau khi gỡ nhiễu — `k = 2` mỗi arm mỗi ca, trần token
**theo cặp**, giữ nguyên luật quyết định. **Không** mở thêm delta.
Báo cáo: `docs/DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB.md`.

### HÌNH DỰNG PHẢI THOẢ QUAN HỆ CHIA ĐOẠN CỦA ĐỀ — 2026-09-06

Wave trước phát hiện `r3/A` **`served` một đáp số SAI** (`15/2` thay vì `8`).
Wave này đóng nó.

`ROOT_CAUSE`: `source_fact_id` chứng minh **nguồn được viện tồn tại**; nó
không chứng minh **hình dựng thoả nội dung** của nguồn ấy. Ba tầng đều làm
đúng việc của chúng — kernel thi hành đúng chương trình đã nhận,
`check_distance` đo đúng khoảng cách tới điểm **đã dựng**, grounding thấy có
`source_fact_id` nên cho qua — và không tầng nào hỏi *"điểm này có đúng là
điểm đề nói tới không"*.

**Khả năng biểu đạt = PARTIAL**, đo chứ không đoán: hợp đồng ĐÃ có
`SourceInvariant` có cấu trúc, server sở hữu, verify ở **P0** bằng `Fraction`,
và **đã có dispatch theo `kind`**. Thiếu đúng hai thứ: một `kind` cho quan hệ
chia đoạn, và một bộ phát ngoài đường chuẩn hoá thang. ⇒ **nhánh A** — dùng
lại thẩm quyền, **không dựng cổng thứ hai**.

Biểu diễn: `kind="segment_division"`, `points=(A,B,M)` với A→B là hướng **của
đề**, `expected = t` hữu tỉ — **không thêm trường nào**. Đọc từ **câu văn đề**
(bốn mẫu), không khớp ⇒ **không phát**, theo luật `bat_bien_nguon` đã đặt.

| | trước | sau |
|---|---|---|
| `r3/A` (`t=1/4`) | **`served`**, `PF = 15/2` | **từ chối** ở `source_invariant` |
| `r3` đúng (`t=1/5`) | `served`, `PF = 8` | `served`, `PF = 8`, scene 5 |

⚠️ **`CACHE_VERSION` 81 → 82 — BUMP, và ngược chiều hai wave trước.** Chiều
đổi ở đây là `served → từ chối`, mà `served` **là** thứ được cache. Chứng minh
bằng **row thật**: envelope `PF = 15/2` ghi ở v81 vẫn **HIT** và được trả về
nguyên vẹn, **không đi qua cổng mới**. Bề mặt mô hình **không đổi** — sáu băm
byte-identical, chỉ version lệch. Candidate `c39f7358…` → **`1151bc6f…`**
(89 → 90 file). 0 lượt gọi model.

⚠️ Giới hạn phải khai: bộ đọc phủ **bốn lối nói**, không phải mọi lối nói —
đề `e4` nằm ngoài mẫu nên **không phát bất biến** và giữ nguyên hành vi cũ.
Fail-closed theo hướng *bỏ sót*, đúng luật đã đăng ký.

```
RECOMMENDED_NEXT_ACTION = RATIO_AB_CONFOUND_REMOVAL_REPEAT
```

Lỗi phục vụ sai đã đóng, nên quay lại việc đang treo. Phép đo ấy nay báo được
**ba** con số mà lượt trước không tách nổi: tỉ lệ sinh đúng · tỉ lệ `served`
**đúng** (nay `served` đã có nghĩa là đúng dữ kiện) · token trên một kết quả
đúng. Báo cáo: `docs/SEGMENT_RELATION_CONSISTENCY_VERIFICATION.md`.

### PHỦ QUAN HỆ CHIA ĐOẠN CHO LỚP CÂU TỔNG QUÁT — 2026-09-06

Wave trước đóng `r3/A` nhưng bộ đọc khi ấy gộp neo và quan hệ vào **một** mẫu,
nên nó **không đọc được `e4`** — ca có thật, đã chạy bằng quota thật. Ba thứ
lệch cùng lúc: neo dạng **cắt**, từ nối **"bằng"**, độ dài cả đoạn ở **câu
khác**. Hệ quả đo được: `divide_segment(P,Q,1/2)` — sai dữ kiện nhưng **vẫn
dựng được thiết diện** — được **`served`** với bán kính `21/2` thay vì `15`.

Sửa bằng **tách hai pha** thay vì thêm mẫu: neo → bộ ba `(A,B,M)`; quan hệ và
độ dài tìm trên **toàn bộ đề + mọi `InputFact`**. Luật ghép là *"cùng xác định
một bộ ba"*, không phải *"cùng một câu"*. Phủ **3 neo × 4 quan hệ**.

| `e4` | trước | sau |
|---|---|---|
| `t = 5/7` | `served`, 15 | `served`, **15**, scene 12 |
| `t = 1/2` | **`served`, 21/2** | **bác** ở `source_invariant` |
| `(Q,P,2/7)` đảo hướng | `served`, 15 | `served`, **15** |

**Trạng thái CHẶN mới:** `SOURCE_INVARIANT_NOT_CHECKABLE` (trường `unresolved`,
tách hẳn khỏi `not_checkable` vốn **không** chặn). Thấy bộ ba + mảnh quan hệ +
nguồn mà không tính được `t` ⇒ bác, vì im lặng khi ấy là phục vụ một hình chưa
chứng minh được.

⚠️ **Đính chính từ vựng của wave trước.** Lối nói ngoài mẫu là
**`NOT_EXTRACTED`** — hệ **không chặn** gì cả, nên gọi nó *"fail-closed"* là
sai. Bốn từ dùng thống nhất: `COVERED` · `VIOLATED` · `NOT_CHECKABLE` (chặn) ·
`NOT_EXTRACTED` (không chặn).

⚠️ **`CACHE_VERSION` 82 → 83, BUMP** — cùng loại `81 → 82`, đo bằng **row `e4`
thật**: envelope `ban_kinh_t = 21/2` ghi ở v82 vẫn **HIT** và trả về không qua
cổng mới. Bề mặt mô hình **không đổi** — sáu băm byte-identical. Candidate
`1151bc6f…` → **`179793db…`**. 0 lượt gọi model.

```
RECOMMENDED_NEXT_ACTION = RATIO_AFFORDANCE_STAGED_RECHECK
```

Theo **bậc**: 2 ca × 2 arm = 4 lượt tổng hợp, chỉ mở thêm cặp khi **cả** tín
hiệu chất lượng **và** ngân sách đều đạt.
Báo cáo: `docs/SEGMENT_RELATION_COVERAGE_HARDENING.md`.

### A/B THEO BẬC VỀ `divide_segment.ratio` — 2026-09-06, GIỮ A

**2 đề × 2 arm = 4 lượt synthesis**, `ANALYZE_CALLS = 0`, `REPAIR_CALLS = 0`,
TOKENS 20 198/30 000. Ngân sách nay **theo lượt chạy** và **dự trữ đủ cả cặp**
trước khi bắt đầu — sửa đúng giới hạn guard mà lượt trước ghi.

| | A | B |
|---|---|---|
| `t` đúng | **0/2** | **2/2** (thắng 2 · thua 0) |
| `served` đúng | 0/2 | 0/2 |
| token | 10 263 → `UNDEFINED`/kết quả đúng | 9 935 → **4 968**/kết quả đúng |

`B_RATIO_SIGNAL = POSITIVE`. A viết `2/3` cho `CN:ND = 2:3` và `1/4` cho
`FP = 4·PE` — lần **tái hiện thứ BA** của quy ước chia đoạn `m:n`.

⚠️ **Nhưng cả bốn lượt, cả hai arm, chết ở `grounding` vì CÙNG một điều.** Raw
candidate giống hệt nhau: gốc toạ độ khai `[0,0,0]` mà **thiếu cả
`source_fact_id` lẫn `model_assumption`**, trong khi đầu mút kia ghim đúng
`do_dai_doan`. Đặt gốc toạ độ là **lựa chọn hệ trục**, và hợp đồng **có sẵn**
ô `model_assumption` cho đúng việc ấy. Grounding **không sai** — đây là lỗ
**affordance**, cùng hình dạng với `ratio`.

⚠️ So token giữa hai arm **bị nhiễu**: `cached_content` A **2 989** · B **0**.
Chênh tổng không quy cho delta thẻ được.

⚠️ Thẩm quyền khi hai nguồn mâu thuẫn, đo trong tiền kiểm: **không nguồn nào
thắng** — mâu thuẫn đọc được ⇒ `unresolved` ⇒ chặn **cả** chương trình theo
dữ kiện **lẫn** theo đề. Hệ không giả vờ đã phân xử được.

**Không đụng mã sản phẩm**: `CACHE_VERSION` 83 → 83, candidate `179793db…`
không đóng băng lại, sáu băm model-facing không đổi, `PRODUCT_VARIANT` = **A**.
`CAUSAL_ATTRIBUTION = LIMITED` · `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`.

```
RECOMMENDED_NEXT_ACTION = FRAME_ORIGIN_PROVENANCE_AFFORDANCE
```

Delta kế tiếp: **một dòng, chỉ về provenance của gốc toạ độ**, đo **riêng**
(không gộp với delta `ratio`), lại theo bậc 2 ca × 2 arm.
Báo cáo: `docs/RATIO_AFFORDANCE_STAGED_RECHECK.md`.

### XUẤT XỨ GỐC TOẠ ĐỘ, VÀ ĐỘ DÀI ĐỀ CHO NAY ĐƯỢC KIỂM — 2026-09-07

Wave định đo affordance về xuất xứ gốc toạ độ, nhưng **dừng phần live ở 0 lượt
gọi** theo đúng luật: replay tất định tìm ra một **lỗ kiểm chứng nặng hơn**.

**Replay chứng minh ① — kênh xuất xứ ĐÃ ĐỦ.** Chỉ cần **MỘT** trong hai trường
trên khai báo gốc toạ độ (`model_assumption` **hoặc** `source_fact_id`) là
chương trình qua grounding: ratioB → `served` với **6** và **8**, scene 4;
ratioA(MULTIPLE) → qua grounding rồi bị `source_invariant` chặn vì ratio sai.
**Không cần trường mới.**

**Replay chứng minh ② — và đây là lý do dừng.** Đề `EF = 10`, chương trình
khai **`F = [99,0,0]`** kèm `model_assumption` **hợp lệ** rồi chia đúng tỉ lệ
⇒ hệ **`served`** với **`396/5`** thay vì `8`. `segment_division` kiểm **tỉ
lệ**, không kiểm **thang**.

Sửa tối thiểu: checker `segment_length` vốn hỏi đúng câu ấy **và chạy đúng** —
chỉ chưa bao giờ được phát cho đề cho **SỐ**. Thêm `bat_bien_do_dai` dùng lại
chính `_do_dai_doan`, khử trùng với đường chuẩn hoá thang.

⚠️ **`CACHE_VERSION` 83 → 84, BUMP** — đo bằng **row thật**: envelope `396/5`
ở v83 vẫn HIT, không qua cổng mới. Sáu băm model-facing **byte-identical**.
Candidate `179793db…` → **`a9289410…`**. `PRODUCT_VARIANT` **A → A**.

⚠️ **LỖ CÒN LẠI, ghi bằng test ĐANG XANH** (`test_C1`): điểm đề giới thiệu như
**phải dựng ra** vẫn khai thẳng toạ độ được và **bỏ câu lệnh dựng** — đáp số
vẫn đúng, thứ mất là **BƯỚC DỰNG**. Gốc: `nhan_suy_ra` không nhận lối nói
*"nằm trên … sao cho"*. Test xanh nghĩa là lỗ **còn**; wave sau đóng thì nó ĐỎ.

```
RECOMMENDED_NEXT_ACTION = DERIVED_POINT_CONSTRUCTION_ENFORCEMENT
```

Đóng nó xong mới quay lại bốn lượt A/B affordance **chưa dùng** — khi ấy
`served` mới có nghĩa *"dựng đúng bằng các bước dựng"*, không chỉ *"ra đúng
số"*. Báo cáo: `docs/FRAME_ORIGIN_PROVENANCE_AFFORDANCE.md`.

### ĐIỂM DẪN XUẤT PHẢI ĐƯỢC DỰNG — 2026-09-07

Wave trước để lại một lỗ và ghi nó bằng một **test đang xanh**; wave này đóng
nó, nên test ấy **đỏ** đúng như đã hứa, rồi được lật thành khẳng định đúng.

| ca `r3` | trước | sau |
|---|---|---|
| khai thẳng toạ độ `P`, **bỏ phép dựng** | **`served`**, `PF = 8`, trace **0 khung** | **bác** ở `grounding`, `DERIVED_ENTITY_WITHOUT_PRODUCER` |
| dựng `(E,F,1/5)` · đảo chiều `(F,E,4/5)` | served · 8 | **served · 8** |
| dựng sai tỉ lệ | bác | **bác** (bất biến, không đổi) |

`ROOT_CAUSE`: chốt ⑥ hỏi **đúng** câu này rồi, nhưng nó đọc `nhan_suy_ra` —
bộ ấy không nhận lối nói *"nằm trên … **sao cho**"* — **và** nó chỉ chạy trong
nhánh `model_assumption`, trong khi lỗ đi được **cả hai** kênh xuất xứ.

Sửa: **chốt ⑦** đặt sau `computed`, **trước** khi rẽ kênh, đọc lại tín hiệu
`segment_relation` đã có trên hợp đồng. **Không** dựng bộ nhận diện thứ hai,
**không** nới `nhan_suy_ra` (hàm dùng chung nhiều wave).

Ranh giới: **chỉ** bất biến **đã giải được**, **chỉ** vế thứ ba `M` — hai đầu
mút là **điểm đầu vào**, giữ nguyên quyền khai toạ độ và quyền đặt hệ trục.
Ba đường producer giả **đều đã có chủ** (`ir_static` · `source_invariant` ·
grounding ⑤) nên chốt ⑦ không nới thêm.

⚠️ **`CACHE_VERSION` 84 → 85, BUMP** — và ca này **khác ba bump trước**:
envelope cũ có **đáp số ĐÚNG** (`8`); thứ sai là **mô phỏng** (không bước dựng,
trace 0 khung). Đo bằng row thật. Sáu băm model-facing **byte-identical**.
Candidate `a9289410…` → **`36e81713…`**. `PRODUCT_VARIANT` **A → A**.

⚠️ Ba mức bằng chứng **không được trộn**: *"đáp số đúng"* · *"có bước dựng
đúng"* (wave này đóng) · *"AI tự sinh ổn định"* (**chưa đo**, 0 lượt gọi).

```
RECOMMENDED_NEXT_ACTION = PROVENANCE_AFFORDANCE_AB_4_LUOT
```

Bốn lượt live đã chuẩn bị: cả hai arm cùng nền hướng dẫn `ratio`, **chỉ khác**
hướng dẫn provenance. Nền đo nay vững hơn — `served` đã có nghĩa *"dựng đúng
**bằng các bước dựng**"*.
Báo cáo: `docs/DERIVED_POINT_CONSTRUCTION_ENFORCEMENT.md`.

### VÒNG SỬA TỰ ĐÓNG ĐƯỢC LỖ `at` — 2026-09-07, 1 LƯỢT GỌI, GIỮ A

Đo **vòng sửa của chính sản phẩm** (`pipeline.stage_semantic_program` +
`_prompt_sua`) trên raw candidate hỏng của lượt P1/RATIO wave trước.
`MEASUREMENT_CLASS = DEVELOPMENT_REPAIR_PROBE` · `HELD_OUT_CLAIM = NO`.

```
REPAIR_LOGICAL_CALLS = 1/1   PHYSICAL = 2   TOKENS = 3123   STAGE = served
```

`PHYSICAL = 2` **không** phải hai lượt gọi model: lượt 0 là raw candidate lịch
sử do probe trả thẳng, chỉ lượt 1 ra mạng.

Mười một chiều chấm đều **PASS**: `SLOT_REPAIRED` · `PROVENANCE_PRESERVED` ·
`RATIO_PRESERVED` (`2/5`, `C->D`) · `GROUNDING` · `SOURCE_INVARIANTS` ·
`RUNTIME` · `POSTCONDITIONS` · `EXACT_ANSWER` (**`ND = 6`**) ·
`TRACE_CONSTRUCTION` (producer `construct_point.divide_segment`,
`depends = [C,D]`) · `SCENE3D` · `SERVABLE`.

Bản sửa: `at` → **`initial_value`** (tương đương chính tắc, ghi trong tiêu chí
**trước** lượt gọi), không dựng thêm `declare_point`. `N` vẫn không có toạ độ;
`C` giữ `model_assumption`; `D` giữ `source_fact_id`; `model_assumption`
**không** lan sang `N`.

```
POINT_INITIALIZATION_DIAGNOSTIC_DISCOVERABLE = YES
ONE_REPAIR_RECOVERS_CORRECT_SIMULATION       = YES
PERMANENT_SLOT_INSTRUCTION_NEEDED            = NOT_PROVED
RECOMMENDED_NEXT_ACTION = MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION
```

**Kết luận có sức nặng nhất là kết luận phủ định.** Wave trước bàn giao đề xuất
*"thêm một dòng hướng dẫn về ô chứa toạ độ"*; phép đo này cho thấy **chưa
chứng minh được là cần** — vòng sửa sẵn có đóng được lỗ, tốn 3123 token. Chưa
chứng minh cần ≠ chứng minh không cần; `n = 1`.

Token ba số, **không trộn**: `CURRENT_WAVE_REPAIR = 3123` ·
`HISTORICAL_INITIAL_SYNTHESIS = 5023` · `COMBINED_OBSERVED_RECOVERY = 8146`.

⚠️ **Hai lỗ BỘ ĐO, cùng một hậu quả: chốt chặn mạng offline mất tác dụng TRONG
IM LẶNG** — tức đe doạ chính câu *"pytest = 0 API call thật"*.
(a) fixture test probe chỉ vá `G.call_gemini`, nên `goc_call` mà probe khôi
phục **chính là stub**, `PL.call_gemini` ở lại = stub **vĩnh viễn** ⇒
`test_offline_guard::test_pipeline_quen_mock_cung_bi_chan` hết raise cho mọi
test chạy **sau**. (b) `block_real_network` gỡ `GEMINI_API_KEY` nhưng `db.py`
gọi `load_dotenv` **lúc import** và điền lại — ẩn vì phụ thuộc **thứ tự thu
thập**, xác nhận **có sẵn từ trước** bằng `git stash`.
**Runner giữ nguyên từng byte** (`runner_sha256` đã nằm trong artifact bất
biến); thay vào đó khoá tiền đề bằng test `A2b`/`A2c`, và fixture chuyển sang
`MonkeyPatch.context()` vì `monkeypatch` chỉ hoàn nguyên lúc **teardown**.
Tiêm lỗi tái hiện **đúng triệu chứng gốc**. Cả hai lỗ thuộc **bộ đo**, ngoài
`MEASURED_SYSTEM_PATHS`.

**Không đụng mã sản phẩm**: `CACHE_VERSION` 85 → 85, candidate `36e81713…`
không đóng băng lại, sáu băm model-facing **byte-identical**,
`PRODUCT_VARIANT` = **A**. `CAUSAL_ATTRIBUTION = LIMITED` (n = 1) ·
`STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`.
Báo cáo: `docs/POINT_INITIALIZATION_REPAIR_EFFICACY.md`.

### A/B PROVENANCE 4 LƯỢT — 2026-09-07, GIỮ A

Hai arm chỉ khác **đúng một dòng** (+323 byte): **P0** = `card_B` của lượt
ratio **nguyên byte**, **P1** = P0 + hướng dẫn provenance (quy tắc chung,
không tên điểm/fact/đáp số).

| | P0 | P1 |
|---|---:|---:|
| **provenance đúng** | **1/2** | **2/2** |
| ratio đúng · điểm dẫn xuất được dựng | 2/2 · 2/2 | 2/2 · 2/2 |
| `served` đúng | 1/2 | 1/2 |
| token · token/provenance đúng | 11 089 · 11 089 | 11 893 · **5 946** |

`P1_PROVENANCE_SIGNAL = POSITIVE` · `P1_SERVABLE_SIGNAL = NEUTRAL`
(ghép cặp 1 thắng 1 thua).

⚠️ **Hai lượt hỏng ở HAI trục khác nhau** — điểm đọc chính. P0/MULTIPLE hỏng
**đúng trục wave đo** (`E` khai toạ độ mà thiếu **cả hai** kênh xuất xứ).
P1/RATIO hỏng ở trục **không liên quan**: đặt `at` vào `memory_declarations` —
lớp lỗi `POINT_INITIALIZATION` đã đóng, chẩn đoán của wave ấy phát đúng. Về
**provenance**, ứng viên ấy làm **đúng**.

⚠️ **Đính chính bộ chấm:** lượt dừng ở `semantic_program` từng bị chấm
`GROUNDING = PASS` — chấm PASS cho tầng **chưa chạy**. Đã sửa và chấm lại
0 lượt gọi; đổi `P1 grounding` 2/2 → 1/2, **không** đổi kết luận provenance.

`cached_content` **0 cho cả hai arm** ⇒ lần này **không có nhiễu cache**.
**Không đụng mã sản phẩm**: `CACHE_VERSION` 85 → 85, candidate `36e81713…`
không đóng băng lại, sáu băm model-facing không đổi, `PRODUCT_VARIANT` = **A**.
`CAUSAL_ATTRIBUTION = LIMITED` (n = 2) · `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`.

```
RECOMMENDED_NEXT_ACTION = PROVENANCE_INSTRUCTION_SLOT_DISAMBIGUATION
```

Hướng dẫn provenance **đạt** mục tiêu của nó; lượt hỏng duy nhất của P1 là đặt
`at` **sai ô**, mà dòng hướng dẫn hiện nói về hai trường *của khai báo* và
**không** nói toạ độ thuộc ô nào. Delta kế tiếp: **một dòng, chỉ làm rõ ô chứa
toạ độ**, đo riêng, lại theo bậc 2 ca × 2 arm.
Báo cáo: `docs/PROVENANCE_AFFORDANCE_AB_4_LUOT.md`.

### 1a-tresquadragies. `PHOTO_PROBLEM_LIVE_RUNNER_HARDENING` (2026-09-14)

Siết **bộ đo** trước lượt provider thật của đường ảnh đề bài, trên nhánh
`feat/photo-problem-to-scene`. **0 request mạng, 0 dòng mã sản phẩm.** Không đo gì.

- **Runner cũ có trần LOGIC 11 nhưng không có trần HTTP** — xấu nhất 38 request
  (3 × 2 + 8 × 4), không dừng khi C01 hỏng, đo văn bản bằng `difflib`.
- **Trần HTTP đặt ở transport** (`CongHttp`, chèn qua `httpx.AsyncClient` mà
  `call_gemini` đọc lúc gọi) — `backend/app` không đổi. Một lần thử mỗi lượt gọi,
  kiểm bằng phép dò trên đúng ba hàm sản phẩm. `--case` bắt buộc, dừng ở ca hỏng
  đầu tiên. CER Levenshtein + chấm dữ kiện. Khử secret trên mọi bề mặt.
- **Bộ đo sai hai lần, tự bắt trong wave:** đếm lần thử lại theo băm thân (vòng sửa
  gửi thân trùng) và đếm mọi mục thừa là dữ kiện bịa (đánh trượt một lượt đọc trung
  thành). Cả hai có khoá và phép tiêm. Bản sửa thứ hai nằm ở commit bằng chứng — lệch
  phân chia commit của đặc tả, đã khai.

```
test runner   56/56 · tiêm lỗi 8/8 đỏ, 8/8 hoàn lại trùng byte
trần HTTP     12 lượt logic → gửi 11 · chặn 1 · transport giả 11 · mạng 0
xấu nhất đạt  đúng 11 request · trần 10 chặn ảnh C03
CER           13/13 cặp · sai nhãn / công thức dưới ngưỡng CER vẫn FAIL
secret        3 lỗi provider · 5 secret giả · 0 lần lộ
dry-run       3/3 PASS trên ảnh TỔNG HỢP · 7 request · 0 mạng
candidate     13e2aaaa… → 13e2aaaa… · CACHE_VERSION 95 → 95
```

`RECOMMENDED_NEXT_ACTION = USER_PROVIDES_GEMINI_KEY_AND_C01_REAL_PHOTO`

⚠️ `REAL_PROVIDER_EVIDENCE = NOT_ESTABLISHED` · `MERGE_ALLOWED = NO`. Báo cáo:
`docs/PHOTO_PROBLEM_LIVE_RUNNER_HARDENING.md`.

### 1a-duoquadragies. `PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION` (2026-09-13)

Đường **ảnh đề bài → xem lại → dựng**, trên nhánh `feat/photo-problem-to-scene`.
**CHƯA merge vào `main`** — không có lượt provider thật nào trong phiên.

- **Không có pipeline thứ hai.** Tầng A (`ingestion/image.py` +
  `ingestion/image_extraction.py`, `POST /api/image/extract`) chép ảnh thành bản
  ghi có cấu trúc và phán tất định; người học sửa và xác nhận; tầng B là
  `/api/analyze` dạng `text`. Semantic Program, thẻ văn phạm, kernel, renderer
  không đổi.
- **Danh tính:** `CACHE_VERSION` giữ 95 (cache khoá theo văn bản; khoá danh tính
  làm lại). `prompts` gộp đổi CHỈ vì `transcribe.md` — chứng minh bằng
  `tests/photo_problem_identity.py`; năm ô danh tính lịch sử khai đính chính,
  artifact giữ nguyên.
- **Bộ đo tự sửa:** ô "không tràn ngang" của kiểm tra trình duyệt so với
  `innerWidth` — phình theo nội dung dưới giả lập di động nên không đỏ được; phép
  tiêm lộ ra, nay so với bề rộng thiết bị. Và `replay_negative_boundaries` không
  phát lại được lượt SỬA — p3 trông như hồi quy; thêm phát lại theo thứ tự.
- ⚠️ **Cổng quay trên chính `085cae6` cho `THIEU_HUONG_NHIN` ở p2/p4/p5** — cùng
  phán quyết với nhánh, đường dựng hình 0 dòng khác. Không phải hồi quy, nhưng bác
  giả định "085cae6 đạt TOP/BOTTOM ở mọi ca".

```
tầng A        chuẩn hoá ảnh + bản ghi có cấu trúc + phán quyết tất định · cache LRU theo sha điểm ảnh
tầng B        4 họ (chóp+thiết diện · cầu · trụ · nón) status ok, scene3d không rỗng (phát lại byte thật)
trình duyệt   10/10 ô @1440×900 · 10/10 ô @390×844 · 0 lỗi trang (FIXTURE)
tiêm lỗi      9/9 đỏ đúng chỗ
provider thật NOT_ESTABLISHED · 0 lượt gọi · runner 3 ca đăng ký trước sẵn sàng
candidate     96a9368b… → 13e2aaaa… · CACHE_VERSION 95 → 95
vitest 869 · tsc ✓ · build ✓ · demo 5/5 · bề mặt sập 6/6
```

`RECOMMENDED_NEXT_ACTION = USER_TESTS_REAL_PHOTO_INPUT`

⚠️ Blocker merge: `REAL_PROVIDER_EVIDENCE = NOT_ESTABLISHED`. Bộ ảnh nghiệm thu là
**tổng hợp** (`REAL_PHOTO_CORPUS = NOT_ESTABLISHED`). Báo cáo:
`docs/PHOTO_PROBLEM_TO_SCENE_END_TO_END_IMPLEMENTATION.md`.
### 1a-unquadragies. `SCENE3D_MINIMAL_Z_UP_CAMERA_IMPLEMENTATION` (2026-09-12)

Bản vá camera Z-up **tối thiểu** trên sản phẩm đã phục hồi: đúng **một**
file sản phẩm, +25 dòng (1 dòng mã, 24 chú thích).

- **`cam.up.set(0, 0, 1)` đặt TRƯỚC `new OrbitControls`.** Thứ tự mới là
  vấn đề, không phải giá trị: OrbitControls chụp `camera.up` ngay trong hàm
  dựng; đặt muộn hơn thì controls quay quanh Y còn camera dựng khung theo Z,
  cho trục đổi mỗi khung — đúng con bọ `56350f7`.
- **Kiểm thử hai tầng**, 9 test, 3/3 phép tiêm đỏ: *hành vi* (dựng controls
  thật ở cả hai thứ tự rồi hỏi `getPolarAngle()`) và *ràng buộc sản phẩm*
  (đọc `scene3d-view.tsx` bằng **AST TypeScript**, không `indexOf` — phép so
  chuỗi vẫn xanh khi dòng ấy nằm trong chú thích).
- **Nhìn được TRÊN và DƯỚI**, thứ bản `1a553b8` không bao giờ tới được.

```
trục quay      Z[0,0,1] ‖1,000‖   (nền Y[0,1,0] ‖1,000‖ · chứng âm chéo ‖0,59–0,62‖)
tổng góc 300px 151,8–154,5°       (nền 148,6–151,9° ⇒ lệch +1,65 %, ngưỡng ≤ 5 %)
cos z          ±1,000             (nền [−0,35; 0,00]) · THIEU_HUONG_NHIN = NO
camera.up ĐO   [0,0,1]            bán kính trôi 0 % · tâm trôi ≤ 2,1e-3
nhịp khung     p50 10,45 / p95 17,40 / p99 20,90 ms  (nền 10,45 / 17,45 / 20,90)
cấp phát khi kéo 0/0/0            pointer→paint 0,20 ms
hồi quy        70 ảnh, 0 rỗng, hình hữu hạn không clipping
vitest 826 · pytest 4823 · candidate 96a9368b… không đổi · CACHE_VERSION 95
```

`RECOMMENDED_NEXT_ACTION = PHOTO_PROBLEM_TO_SCENE_END_TO_END`

⚠️ Ba giới hạn đã khai: `FRAMES_OVER_33_3_MS = 0` không đạt ở **cả hai** bản
(5/5840, khung khởi động shader) — ngưỡng sai chứ không phải bản vá · reset ở
`p1` nhỏ hơn mặc định 52,6 % nhưng **nền cho 53,1 %**, là hành vi có sẵn của
phép khớp khung với mặt phẳng vô hạn · cổng quay chập chờn ở `p6` 1/4 lượt
(thiếu ba hướng NGANG, không phải trên/dưới).
### 1a-quadragies. `SCENE3D_ORBIT_GATE_AXIS_AUDIT` (2026-09-12)

Sản phẩm **giữ nguyên tại `1a553b8`** — 0 dòng mã sản phẩm, 0 dòng camera.
Chỉ kiểm toán cổng quay, vì sau khi phục hồi nó báo `TRUC_TROI` cả ba ca.

- **Phán quyết ấy SAI.** Kéo ngang thuần 300 px, cùng khung nhìn, cùng DPR,
  cùng công thức trục của wave chẩn đoán (`R = AᵀB`, rút trục, chuẩn hoá
  DẤU, trung bình vectơ): **‖trục‖ = 1,000** ở cả `e6c2330` lẫn `1a553b8`,
  trục `[0, 1, 0]`. Trục **cố định tuyệt đối** — nó chỉ là trục **Y**.
- **Gốc lỗi: hai đại lượng cùng tên "trục".** `chuanTruc` cũ lấy
  `dPv/(dPv+dCuc)` quanh **Z**, tức hỏi *"có quay quanh Z không"*. Trên cùng
  một cú kéo: `e6c2330` ‖1,000‖ → hàm cũ 0,525–0,532; `56350f7` (trục TRÔI
  thật) ‖0,600–0,610‖ → hàm cũ **0,546–0,548**. Hàm cũ chấm bản **trôi cao
  hơn** bản cố định — nghịch chiều với thứ nó khai là đang đo.
- ⚠️ **Một chỗ tôi đoán sai giữa chừng.** Cửa sổ yên 1,6–2,9° ở p6/p7, tôi
  ghi vào mã là nhiễu số học — sai. Để cảnh lắng thêm 2 giây rồi mở cửa sổ
  thì thu **0 khung** (renderer vẽ theo yêu cầu), nên chuyển động ấy có
  thật: đuôi damping sau loạt bấm "Bước sau". Cổng nay đợi lắng, đọc 0,0–0,3°.

```
① trục cố định   e6c2330 ‖1,000‖ · 1a553b8 ‖1,000‖ · 56350f7 ‖0,600–0,610‖
② trục là gì     Y [0,1,0]       · Y [0,1,0]       · chéo [0,57;−0,05;0,82]
③ tổng góc 300px 149,3–154,0°    · 149,8–153,0°    · 109,1–109,7°
④ camera.up ĐO   [0,1,0]         · [0,1,0]         · [0,0,1]
⑤ screen-up      (0,40;0,894;0,20)·(0,40;0,894;0,19)·(−0,05;−0,05;0,998)
SAU SỬA: TRUC_TROI biến mất ở hai bản trục cố định, vẫn phát ở 56350f7
GIỮ NGUYÊN: THIEU_HUONG_NHIN — cos ∈ [−0,31;0,00], Y-up không nhìn được từ trên/dưới
PRODUCT_CHANGED = NO · vitest 817/817 · build xanh
```

`RECOMMENDED_NEXT_ACTION = USER_REVIEWS_ORBIT_GATE_AUDIT`
### 1a-novicies. `SCENE3D_RETURN_TO_PRE_MOCKUP_PRODUCT_STATE` (2026-09-12)

Người dùng yêu cầu đưa phần mô phỏng hình học về **trước commit triển khai
mockup đầu tiên** (`7f34286`) — không phải trước D2. Mốc: `e6c2330`, xác
nhận bằng `git rev-parse 7f34286^`, không đi bằng giả định.

- **Dựng lại bản cũ để ĐO trước khi đổi mã.** Worktree tại mốc: build ✓,
  vitest 817/817 ✓. Camera **Y-up** (up = −0,268; 0,894; −0,358); p4/p5 cho
  (−0,268; −0,358; −0,894) ⇒ trụ và nón **nằm ngang**. Màu tím/nâu/cam theo
  NGUỒN GỐC VẬT. Khối cong **không có đường bao**. DPR 1. Bước 8 ≡ bước 11.
- ⚠️ **Một lỗi BỘ ĐO suýt vào báo cáo.** Lượt đầu đọc *"quay được 13°"* —
  nghe như bản cũ không xoay nổi. Phép đo phân tích phương vị quanh trục **z**
  còn bản cũ quay quanh **y**, nên phương vị theo z không cộng dồn. Đo lại
  bằng tổng góc giữa hai hướng nhìn liên tiếp (không phụ thuộc trục) ra
  **940°**: bản cũ xoay tự do, chỉ **quanh trục sai**.
- **Phục hồi không rewrite.** 17 commit vẫn nguyên trong `git log`. Đường sản
  phẩm đưa về đúng nội dung mốc; bất biến kiểm được bằng máy:
  `git diff e6c2330 HEAD -- domains/geometry styles` ⇒ **rỗng**. Không chạm
  `backend/**`, `frontend/src/data/**`, hay tài liệu của wave cũ.

```
P1_P7_RESULT       7/7 khớp ĐIỂM ẢNH với e6c2330 (mực 49452·3149·37931·60127·23966·39276·29262)
BAI_THAT           băm b1/b6/b8/b11 giống hệt bản chụp từ worktree mốc
ROTATION_RESULT    quét 940°, quanh Y 1052°, quanh Z 12° — quay được, quanh TRỤC Y
CỔNG QUAY          KHÔNG ĐẠT — TRUC_TROI 3/3, trục 0,545–0,549
vitest 817/817 (bằng đúng số ở mốc) · tsc ✓ · build ✓ · pytest 4821 pass
backend 0 byte · CANDIDATE_HASH 96a9368b… không đổi · CACHE_VERSION 95 → 95
```

`RECOMMENDED_NEXT_ACTION = USER_REVIEWS_RESTORED_PRE_MOCKUP_STATE`

⚠️ **Lỗi cũ quay lại, khai đủ**: trục quay trôi (con bọ người dùng từng tự
phát hiện bằng video) · khối nằm nghiêng · khối cong không nét bao · bảng màu
theo nguồn gốc vật · bước 8 ≡ bước 11. **Mất**: nét dày theo pixel, đường bao
khối cong, nhãn thiết diện/đường tròn/trục, DPR 2, thiết diện hiện dần, token
mockup, bộ giải nhãn, hai cổng thị giác. Chi tiết ở §6 của báo cáo wave.
### 1a-octricies. `SCENE3D_MOCKUP_TOKEN_RESTORATION` (2026-09-12)

Người dùng đặt bộ mockup `p1`–`p7` đã chốt cạnh sản phẩm và nói *"bạn toàn
sửa đâu đâu"*. Kiểm lại thì đúng, và đúng theo cách tệ hơn tưởng.

- **Không dòng nào trong bảng thị giác còn khớp mockup.** Chú thích in ngay
  trong mockup ghi *"cạnh thấy 2,8 px · cạnh khuất 1,6 px · thiết diện 3,5
  px"*; token ghi 2,4 / 1,4 / 3,2. Mảng tô 0,07 → 0,035 và 0,022. Chấm điểm
  đường kính 8 px → 4,4. Nền giấy `#FAF9F7` → trắng phủ gradient. Thiết diện
  khuất từ *cùng cam mờ 0,55* thành `#e79a84` đặc.
  ⚠️ **Ba cổng vẫn xanh suốt** — vì chúng đọc token, và token là thứ đã trôi.
  Cổng thị giác còn ghi cứng *"token D2 = 2,4 px"* kèm dải 1,6–3,4: một bản
  sao thứ hai của thiết kế, che đúng lượt trôi mà nó phải bắt. Nay nó đo
  **lệch so với chính token** (`CANH_THAY_SAI_SO = 0,6`).
- **Mảng tô vẫn đậm sau khi chép lại số — ba nguyên nhân, không cái nào ở
  token.** Một *cửa sổ chứng* (đặt tô = 0,5 rồi đo) tách được cả ba:
  *(a)* `MeshStandardMaterial` + `AmbientLight(0,75)` làm màu chạm khung tối
  hơn token — lượt đo trả `rgb(107,…)`, **tối hơn cả chính màu tô** `#77736F`,
  nên thủ phạm không phải số lớp; năm mảng tô chuyển `MeshBasicMaterial`.
  *(b)* Sau đó cửa sổ chứng trả đúng `1−(1−0,5)² = 0,75` ⇒ **hai lớp**: trace
  hợp lệ mang hai vật trùng khít (`khối nón` + `hình nón`). Sửa ở tầng trình
  bày bằng `vatToTrung` — mảng tô là thuộc tính của KHỐI.
  *(c)* Mặt được nêu tên tô ở mức thiết diện 0,14 ⇒ hạ về mức khối 0,07.
  ⚠️ Một giả thuyết đã bị **thí nghiệm bác**: `DoubleSide` khiến mặt sau cũng
  tô — đổi `FrontSide` không đổi một điểm ảnh nào.

```
MẢNG TÔ p5   rgb(224,223,221) → rgb(234,233,232)   mockup rgb(234,233,231)
BỀ DÀY CẠNH  trung vị 2,35 – 2,81 px CSS           token 2,8
P1_P7_BROWSER_ACCEPTANCE  22/28 → 24/28 ô ĐẠT (p6 và p3@dpr2 hết lỗi)
FAULT_INJECTIONS          4/4 đã chứng ĐỎ, cây khôi phục nguyên trạng
vitest 924 → 931 · tsc xanh · cổng quay ĐẠT · cổng thị giác ĐẠT 10/10
CANDIDATE_HASH 96a9368b… không đổi · CACHE_VERSION 95 → 95 · backend 0 byte
GEOMETRY_MODIFIED = false · BACKEND_CHANGED = NO · MODEL_FACING_CHANGED = NO
```

`RECOMMENDED_NEXT_ACTION = USER_REVIEWS_MOCKUP_PARITY`

⚠️ Bốn ô `NHAN_QUA_SAT_NET` còn lại, và **chính ngưỡng ấy nghiêm hơn mockup**:
trong `p4`/`p6` nhãn `OK` nằm ĐÈ lên đường dựng, viền giấy 3,2 px cắt nét ra
cho chữ đọc được. Luật *"cách mực ≥ 6 px"* là luật tự đặt ở vòng trước, không
chép từ đâu — cần người dùng quyết theo mockup hay giữ nghiêm.
### 1a-septricies. `SCENE3D_D2_FRONTEND_IMPLEMENTATION` (2026-09-12)

Hướng thị giác **D2 đã vào sản phẩm**. Năm commit `eb6d7d5 → 0d9b67d`, chỉ
chạm `frontend/src/simulations/domains/geometry/` và `frontend/scripts/`.

- **Thiết diện hiện dần theo `EXTEND`.** Trace luôn có bốn sự kiện nối cạnh
  kèm `face_index`; `EventAction` khai `"EXTEND"` từ đầu mà không dòng mã
  nào đọc nó, nên năm bước cuối cho năm khung hình trùng khít. Nay bước 7→10
  đo được 8606 → 8650 → 8695 → 8856 điểm mực, bốn băm khác nhau.
  ⚠️ **Bước 11 vẫn trùng BYTE với bước 10**: mảng tô dựng ở tầng đối tượng
  (test đơn vị xanh) nhưng không ra điểm ảnh nào. Khuyết tật có từ wave
  trước; wave này làm nó lộ ra vì lần đầu có ai so hai bước liền nhau.
- **DPR có trần `min(dpr, 2)`.** Trước đó `setPixelRatio` chưa bao giờ được
  gọi. Đoạn chuyển 10→90 % hẹp đi một nửa: 1,506 → 0,748 px CSS.
  ⚠️ `setSize(…, true)` là điều kiện đi kèm bắt buộc — giữ `false` thì canvas
  phình gấp đôi theo px CSS và `overflow: hidden` giấu chỗ vỡ đi.
- **Token gom về một nguồn** `scene3d-tokens.ts`. Δ màu nhỏ nhất giữa sáu
  vai 10,4 → 69,9; thiết diện thấy/khuất hết dùng chung một màu.
- **Bộ giải nhãn ràng buộc CỨNG**, không giấu chữ và không nới ngầm. Sửa kèm
  ba lệch THỨ TỰ cùng lớp (bố trí không chạy lại khi cảnh đổi · hai thẩm
  quyền cho câu hỏi "vật nào đang có mặt" · neo nhãn nạp sau lượt dựng).
- **Cổng mới `scene3d-d2-gate.mjs`** — 28 ô. ⚠️ Cổng thị giác CŨ đang đo sai
  ba chỗ và đã sửa: ghi cứng bảng màu · lấy điểm ảnh xám làm đại diện cho
  "có đường bao" (đường bao khối cong phần lớn là phần THẤY) · phép đo bề
  dày thổi phồng nét nghiêng.

```
P1_P7_BROWSER_ACCEPTANCE      = 22/28 ô ĐẠT (trước khi sửa hai lỗi bộ giải: 18/28)
LABELS_HIDDEN = 0 · LABEL_OVERLAPS = 0 · control overlay che nhãn = 0
LABEL_LAYOUT_UNSATISFIABLE    = 6 ô, đã khai tên (p1@mobile, p3@dpr2, p6)
P1_P7_FINAL_GEOMETRY_PARITY   = 8/8 EXACT (băm tổng 559d0e8eb275f8a4)
CANDIDATE_HASH 96a9368b… không đổi · CACHE_VERSION 95 → 95 · backend 0 byte
vitest 921 · tsc xanh · orbit gate ĐẠT · fidelity gate ĐẠT
REAL_PHONE_GPU_NOT_ESTABLISHED · một lượt để bàn DPR2 p95 = 20,8 ms > 16,7
```

`RECOMMENDED_NEXT_ACTION = USER_REVIEWS_IMPLEMENTED_D2_EVIDENCE`

⚠️ Đọc kèm §0e: tuyến khoá luận vẫn treo
`THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW`, và mục này KHÔNG đóng nó.
### 1a-sextricies. `SCENE3D_CAMERA_AND_MOCKUP_FIDELITY` (2026-09-11)

Đóng **cả ba lỗi thị giác** mà lượt nghiệm thu trước đo được, cộng một lỗi thứ
tư mà chỉ video `af.mp4` của người dùng mới lộ ra: **trục quay trôi**.

- **Gốc lỗi trục quay** — `OrbitControls` chụp `camera.up` **một lần trong hàm
  dựng** (`_quat`, `OrbitControls.js:406`), trong khi `scene3d-view.tsx` đặt
  `cam.up = (0,0,1)` **sau** đó. Controls quay quanh Y, `lookAt` dựng tư thế
  theo Z ⇒ trục quay đổi mỗi khung. Chuẩn trục trung bình **0,608–0,680**, một
  cú kéo chỉ đi **~60 %** biên độ. ⚠️ Đây **không** phải hồi quy hiệu năng —
  p95 gần như không đổi, và đi tối ưu hiệu năng sẽ chữa một bệnh không có.
- **Bảy commit, mỗi giai đoạn một cổng riêng**: bằng chứng chẩn đoán · sửa vòng
  đời camera · tách vai ngữ nghĩa khỏi trạng thái chọn · nét có bề dày thật ·
  đường bao khối cong · nhãn T·C·E·OK·OS · cắt chi phí tô + cổng thị giác.
- **Số sau khi sửa**: ‖trục‖ **0,999–1,000** · một cú kéo **437–443°** · chạm cả
  đỉnh lẫn đáy · 0 snap · 0 cấp phát khi kéo · bề dày nét **2,74–3,47 px**
  (trước: 1,89 px cho mọi vai) · **0 điểm ảnh xanh** khi chưa chọn gì · cổng thị
  giác **10/10 DAT** · tiêm lỗi **10/10 bị bắt**.
- ⚠️ **`PERFORMANCE_REGRESSION` ở `390×844`**: p95 **12,1 ms** so với trần 9,1
  (baseline 7,9). p50 không đổi (7,0 / 6,9) nên khung điển hình y như cũ, chỉ
  đuôi dày lên. `1440×900` thì **p95 = 20,9 = đúng baseline**. Mọi số đo dưới
  **SwiftShader**; chưa có phép đo nào trên GPU thật.
- ⚠️ **Bốn lỗi của chính bộ đo** đã cho kết luận sai trong wave này và đều đã
  sửa — xem §4 của báo cáo. Đáng nhớ nhất: một phép tiêm lỗi **đo phải `dist/`
  của phép tiêm trước đó** vì build đỏ mà cờ `--bo-qua-build` bỏ qua. Cổng
  `kiemDistMoi()` nay có ở **cả hai** cổng trình duyệt.
- `CACHE_VERSION` **95 → 95** · candidate `96a9368b…` **không đổi** (miền
  `geometry/` không nằm trong `MEASURED_SYSTEM_PATHS`) · backend **0 byte** ·
  `APPLICATION_LLM_CALLS = 0`.

Báo cáo: `docs/SCENE3D_CAMERA_AND_MOCKUP_FIDELITY.md`. Bằng chứng cho người dùng
duyệt nằm **ngoài repository**: `D:	mplgosim-fidelity\CONTACT_P1_P7.png`,
`CONTACT_GOC_NHIN.png`, `after-camera-and-visual-fix.webm`.

```
USER_VISUAL_APPROVAL = PENDING
RECOMMENDED_NEXT_ACTION = USER_REVIEW_OF_MOTION_AND_CONTACT_SHEET
```

⚠️ Tuyến **khoá luận** vẫn còn nguyên việc của nó —
`THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW` chưa ai đóng. Đọc `CLAUDE.md §0e`
trước khi coi nhãn trên là việc kế tiếp duy nhất.

### 1a-quintricies. `SCENE3D_VISUAL_LANGUAGE_BROWSER_ACCEPTANCE` (2026-09-11)

**Cổng trình duyệt ĐÃ KHÔI PHỤC — và ảnh sản phẩm bác ba chỗ.** Wave ĐO: không
sửa renderer, không sửa camera. `CANDIDATE 96a9368b…` không đổi · `CACHE_VERSION`
95 không đổi · backend 0 byte · `APPLICATION_LLM_CALLS = 0`.

**Nguyên nhân cổng cũ không lập được nền, định vị được:** `spot-check-demo.mjs`
nạp cảnh bằng `import('/src/state/store.ts')` — đường **chỉ có trên Vite dev**,
nên mọi lượt đo phải đi qua transport đã biết là chập chờn (dev kẹt 2/15 ·
bản dựng 0/15). Cổng mới phục vụ `dist/` tĩnh, vào bằng `window.__ALGO_SIM_STORE__`
(thứ `main.tsx` đã phơi ở cả hai chế độ). **`BASELINE 3/3 PASS · CANDIDATE 3/3
PASS`** ⇒ `BROWSER_EVIDENCE = ESTABLISHED`. Phép tiêm **8/8 bị bắt**.

⚠️ **Ba lỗi CỦA CHÍNH CỔNG bị bắt lúc dựng, mỗi lỗi từng cho một kết quả xanh
sai:** ① cổng **PASS 7/7 trên cảnh RỖNG** — `loadEnvelope` đặt cảnh ở bước 0,
bảy tấm ảnh chỉ có năm chấm đen; sửa bằng `EXPECTED_STEP_VISIBLE` + ngưỡng mực.
② `store.toEnd()` là **NO-OP** trên tuyến hình học (bước nằm ở `Scene3DExplorer`,
không ở timeline store) — cảnh đứng ở *"Bước 1/13"* mà cổng tưởng đã tua; sửa
bằng bấm nút **"Bước sau"** thật. ③ server tĩnh fallback `index.html` cho MỌI
đường nên chunk `.js` mất vẫn trả HTTP 200 — phép tiêm "entry chunk mất" **lọt**.

⚠️ **Bộ đo bề dày tự nói dối hai lần trước khi dùng được**: phân loại theo màu
tuyệt đối vỡ trên ảnh thật (cùng một ảnh cho trung vị **0,09 px** và max **45
px** vì nhặt cả mảng tô); lọc lõi 0,55 **giết đúng ca 1 px** cần phát hiện; và
nhãn DOM đè lên canvas làm bộ đo trả về **15,3 px** = độ dày thân chữ. Bản cuối
dùng tích phân mực trên nền cục bộ, tự kiểm chính xác từ 2,2 px trở lên,
**bão hoà ở ~2,0** với nét ≤1,6 px.

**`VISUAL_ACCEPTANCE = FAIL`, ba lý do — chỉ thị dự kiến một:**
① `FAIL_VISIBLE_EDGE_WIDTH` — p25 = **1,46 px ở cả bảy ca**, mục tiêu 2,8 px;
profile thô `253 253 215 148 216` cho thấy nét chỉ chiếm một điểm ảnh.
② `FAIL_HIGHLIGHT_OVERRIDES_ROLE_COLOR` — **chưa từng được nêu**: vật nhóm
`target` vẽ bằng `MAU.highlight` đè lên toàn bộ bảng vai, nên thiết diện `p3`/
`p6`/`p7` ra **màu xanh** chứ không đỏ cam, và trụ/nón `p4`/`p5` tô xanh đục
0,24. Đây là lý do sáu trong bảy ca đo được **0 mẫu** cho màu thiết diện.
③ `FAIL_CURVED_SOLID_HAS_NO_LINEWORK` — **chưa từng được nêu**: `p4`/`p5` ra
một khối đặc **không một nét viền nào**; nhánh `curved_solid` không gọi
`duongHaiLuot` như nhánh đa diện.

Đạt: z-up đúng trong sản phẩm · clipping 0 · nhãn ngoài khung 0 · nhãn chồng 0 ·
console error 0 · xoay cập nhật cảnh (p1/p6/p7) · responsive 390×844 dựng được.
⚠️ Quan sát phụ: ở mobile canvas rộng **439 px** trong viewport **390 px** —
tràn ngang, chưa điều tra.

⚠️ **Một sự cố hạ tầng do chính wave này gây ra và đã sửa:** worktree baseline
dùng junction tới `node_modules`, và `git worktree remove --force` xoá **xuyên
qua junction** vào `node_modules` thật. Khôi phục bằng `npm ci`; vitest **829/56**
và build xanh trở lại, đúng số cũ. Lần sau: gỡ junction TRƯỚC khi gỡ worktree.

Artifact: `docs/evaluation/geometry/scene3d-visual-language-browser-acceptance/`
(9 JSON + `CONTACT_SHEET.png` + 50 ảnh). `DEMO_SPOT_CHECK.json` và artifact lịch
sử **không bị chạm**. Báo cáo:
`docs/SCENE3D_VISUAL_LANGUAGE_BROWSER_ACCEPTANCE.md`.

```
NEXT_ACTION_TUYEN_KHOA_LUAN  = THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW   (MỞ)
NEXT_ACTION_TUYEN_GIAO_DIEN  = SCENE3D_WIDELINE_DEPTH_PASS_IMPLEMENTATION       (MỞ)
RECOMMENDED_NEXT_ACTION      = SCENE3D_WIDELINE_DEPTH_PASS_IMPLEMENTATION
                               ⚠️ phải xử CẢ BA lỗi ở §5, không chỉ bề dày nét
```

### 1a-quattuortricies. `SCENE3D_VISUAL_LANGUAGE_IMPLEMENTATION` (2026-09-11)

**Ngôn ngữ hình học đã duyệt được đưa vào renderer sản phẩm.** `USER_APPROVAL =
APPROVED` ở vòng mockup tĩnh; `APPROVAL_SCOPE = SCENE3D_VISUAL_LANGUAGE_AND_CAMERA_ONLY`.
Chỉ chạm `domains/geometry/` + `global.css`. `CANDIDATE 96a9368b…` **không đổi**
(geometry KHÔNG nằm trong `MEASURED_SYSTEM_PATHS`) · `CACHE_VERSION` **95 → 95,
không bump** (không chạm prompt/thẻ/lược đồ/policy) · `BACKEND_CHANGED = NO`.

**Camera viết lại — 0/7 → 7/7 ca đạt.** Hai lỗi tách rời: ① fit theo **cầu
ngoại tiếp** (cầu lấp 68 % khung ⇒ hình thật lấp `0,68/√3 ≈ 39 %`; đo được
occupancy 0,29–0,47) ② ⚠️ **`up` sai hệ — lỗi này KHÔNG có trong chẩn đoán ban
đầu**: toạ độ bài dùng **z** làm chiều cao còn camera dùng `up = (0,1,0)` của
three.js, nên **mọi khối nằm nghiêng** và khối chóp `p1` đọc ra một tứ giác
dẹt. Suốt vòng trước lỗi ấy bị quy cho màu sắc. Nay fit theo **hình chiếu** tám
đỉnh hộp bao + `up` = trục z hình học + phương vị `−55°`/độ cao `22°`; đo lại
occupancy **0,66–0,685**.

**Bảng màu theo VAI, không theo nguồn gốc vật.** Bản trước gán điểm tự do xanh
/ điểm dẫn xuất đỏ — đúng kỹ thuật, vô nghĩa với người học, và tiêu hai màu
mạnh nhất cho câu hỏi không ai đặt. Nay cạnh thấy + điểm `#1F1F1F` · cạnh khuất
`#7D7975` (**một vai riêng**, không phải bản mờ) · thiết diện `#D95A43` ·
đường dựng `#99948F` · mặt phẳng `#77736F` · chọn `#0075DE`. Độ đục khối/mặt
phẳng/mặt cong đều về **0,07**. ⚠️ `MAU.line` và `MAU.section` từng là MỘT —
đó là lý do thiết diện `p3`/`p6` đọc ngang hàng một đường phụ. Thiết diện đa
giác nay đi **hai lượt** (trước là một `THREE.Line` liền, nên cạnh sau của
thiết diện `p1` hiện y hệt cạnh trước). Nhãn bỏ ô nền, 15 px/600, viền trắng.

⚠️ **GUARD thiết diện bẹp: bản đầu SAI, ca tổng hợp bắt được.** Nó so **hiệu
phương vị** với 90°; nhưng "nhìn nghiêng cạnh" là quan hệ **ba chiều**. Ca tổng
hợp có thiết diện chiếu ra tỉ lệ trục **0** mà hiệu phương vị là **125°** ⇒
guard không nổ. Sửa thành `matCatBet`: `|d̂·n̂| < 0,15`.
`GUARD_STATUS = VALIDATED_ON_SYNTHETIC_CASE` (0 → 0,514); trên bảy ca THẬT
guard **không nổ lần nào**, đúng dự kiến.

⚠️ **Toàn bộ bản vá chạy qua suite cũ mà KHÔNG một test nào đỏ** — trước đó
không có gì canh ngôn ngữ thị giác. Nay có `scene3d-visual-language.test.tsx`
**12 test**, kèm **6/6 phép tiêm bị bắt** (up, fit, màu khuất, màu điểm, thiết
diện một lượt, khối đặc). `tsc -b` bắt một lỗi kiểu mà vitest bỏ qua.

Cổng: vitest **829/56** (trước 828) · `npm run build` PASS · `freeze --verify`
exit 0 (92 file, `96a9368b…`) · `lock_cache_identity --verify` exit 0 @ v95.

⚠️ **`BROWSER_EVIDENCE = NOT_ESTABLISHED`.** `spot-check-demo.mjs` cho 4/12,
nhưng chạy lại **trên mã CHƯA sửa** cũng chỉ **6/12** (nền tài liệu 12/12), cùng
một kiểu hỏng `xuong=false canvas=0`. Không lập được nền thì cổng không chứng
minh gì cho cả hai phía. WebGL **có** chạy (probe: SwiftShader OK) — nguyên
nhân chưa định vị. Nghĩa là **chưa có điểm ảnh nào của sản phẩm được nhìn** với
bản vá này. `DEMO_SPOT_CHECK.json` bị hai lượt chạy ghi đè và **đã trả về bản
2026-09-02**.

Nợ mở: `EDGE_WIDTH_IN_PIXELS` — token duyệt ghi cạnh 2,8 px nhưng renderer vẽ
cạnh khối bằng `THREE.Line`, mà WebGL **bỏ qua `linewidth`** nên mọi cạnh dày
đúng 1 px; đạt bề dày thật cần `LineSegments2` và việc ấy chạm cơ chế hai lượt
đang bị khoá ⇒ wave riêng.
Báo cáo: `docs/SCENE3D_VISUAL_LANGUAGE_IMPLEMENTATION.md`.

```
NEXT_ACTION_TUYEN_KHOA_LUAN  = THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW   (MỞ)
NEXT_ACTION_TUYEN_GIAO_DIEN  = SCENE3D_VISUAL_LANGUAGE_BROWSER_ACCEPTANCE       (MỞ)
RECOMMENDED_NEXT_ACTION      = SCENE3D_VISUAL_LANGUAGE_BROWSER_ACCEPTANCE
                               ⚠️ chỉ là tuyến giao diện, KHÔNG phải toàn bộ
```

### 1a-tretricies. `RESEARCH_GAP_AND_SYSTEM_CONTRIBUTION_FORMALIZATION` (2026-09-10)

**Wave khảo sát tài liệu và định hình đóng góp. 0 byte mã sản phẩm đổi.**
`APPLICATION_LLM_CALLS = 0` · `PRODUCT_CODE_CHANGED = NO` ·
`MODEL_FACING_CHANGED = NO` · `CACHE_VERSION` **95 → 95, không bump**.

`STRUCTURED_SCOPING_REVIEW` (**không** phải systematic review — không đăng ký
trước, một người sàng lọc, không PRISMA flow). 14 truy vấn · 111 kết quả xem sơ
bộ · 24 lượt mở trang công bố (19 thành công, 5 hỏng) ⇒
`PRIMARY_ACADEMIC_SOURCES 23` · `OFFICIAL_TOOL_SOURCES 3` ·
`COMPARABLE_ENTRIES 19` (+1 hàng AlgoSim = 20 hàng ma trận).

⚠️ **SAI LỆCH GIAO THỨC đã khai:** mọi truy vấn đi qua **một** giao diện web
tổng quát; **chưa** truy vấn native IEEE Xplore · ACM DL · SpringerLink ·
Google Scholar. Mọi phát biểu khoảng trống mang giới từ *"trong phạm vi đã khảo
sát"*. Đóng nợ trước khi nộp **bài báo**, không bắt buộc cho khoá luận.

⚠️ **Phát hiện làm HẸP khoảng trống của bản thảo — hai công trình 2026:**
**GeoBuildBench** (arXiv:2605.13167) đã đặt đúng khuôn *đề tự nhiên → chương
trình DSL → hình thoả ràng buộc kiểm được* (nhưng 2D, tiếng Trung, là **thước
đo**); **Draw2Think** (arXiv:2605.20743) dựng hình qua constraint engine
GeoGebra và **khai phủ cả hình không gian**, báo +16,4 % ở hình không gian
(nhưng mục tiêu là **giải đúng hơn**, thẩm quyền số thuộc engine có sẵn). Nghĩa
là câu *"chưa ai dựng hình 3D từ đề bài"* **KHÔNG dùng được**. Phát biểu còn
đứng vững là phát biểu dạng **giao**: 3D + số học chính xác + song ánh khung ⇔
bước + từ chối có cấu trúc hướng người học. **Geoparsing** (ACL 2026, đã nhận)
là công trình duy nhất trong tập khảo sát có ngôn ngữ hình thức hợp nhất phẳng +
không gian — nhưng chạy **chiều ngược** (hình → ngôn ngữ hình thức).

Đóng góp phân loại: **C1 = 1** (nhân số học chính xác làm thẩm quyền đáp số —
⚠️ **VeriGeo** arXiv:2606.14176 là đối thủ gần nhất, đọc toàn văn thấy nó giữ
dạng chính xác thì **hạ xuống C2**) · **C2 = 3** · **C3 = 4** · **C4 = 3**.
`RQS_MAPPED = 5/5`, đề nghị **tách RQ4** làm fail-closed / boundary-accuracy vì
gộp lại làm `TARGET_BOUNDARY_PASS = 1/2` biến mất khỏi tầm mắt.
`UNSUPPORTED_SUPERLATIVE_CLAIMS = 0` (quét 4 file, 6 lần khớp, phân loại hết).

⚠️ **Trôi danh tính phát hiện thêm:** `docs/thesis/CLAIM_EVIDENCE_MATRIX.md` §G
ghi *"hai giá trị hiện trùng nhau"* và *"`CACHE_VERSION = 94` ở cả hai thời
điểm"* — **đúng lúc viết, sai hôm nay**. Đo lại 2026-09-10: candidate lịch sử
`d72db7c3…` @ v94, candidate **hiện tại `96a9368b…` @ v95**. Giữ nguyên bản gốc,
đính chính ở `docs/research/CLAIM_TO_EVIDENCE_MAP.md §0`.

Cổng: `freeze --verify` exit 0 (92 file, `96a9368b…`) · `lock_cache_identity
--verify` exit 0 @ v95 · `git diff --check` sạch · 16 test danh tính ·
`code-index-sync` + `rules-hygiene` 8/8 · 5/5 JSON hợp lệ · bib **26/26 khớp
1:1** với khoá được trích. pytest toàn bộ và `npm run build`: **KẾ THỪA** — 0
byte mã sản phẩm đổi.
Báo cáo: `docs/RESEARCH_GAP_AND_SYSTEM_CONTRIBUTION_FORMALIZATION.md`.

⚠️ **HAI TUYẾN ĐANG MỞ SONG SONG — mục này KHÔNG thay thế tuyến kia.** Khối
`RECOMMENDED_NEXT_ACTION` dưới đây chỉ nói về tuyến **giao diện**. Việc
**`THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW`** vẫn **MỞ** — nó được bốn
mục `1a-*` trước đó đề xuất và wave này **không** làm nó (wave này chỉ hình thức
hoá khoảng trống nghiên cứu, không hợp nhất bản thảo). Nợ cụ thể của nó còn
nguyên: thân Chương 4 của `THESIS_DRAFT.md` và `docs/thesis/CHAPTER_4_*.md` hiện
là **hai thân rời nhau** (`CLAIM_EVIDENCE_MATRIX §D-4`).

Đọc "việc kế tiếp" bằng **một** mục mới nhất là sai từ đây trở đi — phải đọc cả
hai dòng dưới:

```
NEXT_ACTION_TUYEN_KHOA_LUAN  = THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW   (MỞ)
NEXT_ACTION_TUYEN_GIAO_DIEN  = STATIC_VISUAL_MOCKUP_BEFORE_CODE                 (MỞ)
RECOMMENDED_NEXT_ACTION      = STATIC_VISUAL_MOCKUP_BEFORE_CODE
                               ⚠️ chỉ là tuyến giao diện, KHÔNG phải toàn bộ
```

### 1a-duotricies. `DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH` (2026-09-10)

**`DISPLAY_NAME_PASS 10/12 → 12/12` · `PLACEHOLDER_DISPLAY_NAMES 2 → 0`.**
0 lượt gọi model. Đáp số **không đổi một ký tự**.

```
ROOT_CAUSE = `ellipse3` vắng ở BA bảng của `display_names`, không phải một
pytest 4823 pass, 1 skip, 1 deselect — 0 đỏ, cây sạch · vitest 816
trình duyệt 73/73 · refusal 21/21 · hidden-line 23/23 · oracle 7/7 · tiêm lỗi 4/4
CACHE_VERSION 94 → 95 (BUMP) · CANDIDATE e40de3b1… → 96a9368b…
MODEL_FACING 5/5 KHÔNG đổi · LIVE_ARTIFACTS 45/45 byte-identical
```

⚠️ **Giả thuyết bàn giao ĐÚNG NHƯNG CHƯA ĐỦ.** Wave trước đoán *"`_DANH_TU_NGAN`
thiếu `ellipse3`"*. Thực tế cùng một kiểu vắng ở **ba** bảng, mỗi bảng một lối
rơi: `_CACH_GOI[intersect_plane_curved_ellipse]` (không có CÂU gọi tên) ·
`MO_TA_KIEU` (nhãn vật → `Đối tượng`) · `_DANH_TU_NGAN` (cách gọi ngắn →
`đối tượng`). `ellipse3` vào `MemoryType` từ 2026-09-07 mà tầng trình bày không
đi theo — và **không có gì bắt nó phải đi theo**. Đó mới là lỗ thật.

⚠️ **Bản vá soi gương ca ĐƯỜNG TRÒN**, không phát minh cách viết thứ hai: `p3`
đã cho `Diện tích «Đường tròn giao của khối cong và mặt phẳng»`, nên elip dùng
đúng khuôn ấy. Ví dụ *"Diện tích elip E"* ở đặc tả không dùng được nguyên văn vì
ghép `E` đòi coi `id` biến là ký hiệu, mà `_KIEU_KY_HIEU_LA_TEN` cố ý chỉ nhận
`point3`/`vector3`.

⚠️ **Bằng chứng nhãn KHÔNG dẫn từ tên biến**: `p6` đặt `dien_tich_elip_e`, `p7`
đặt `dien_tich_E` — hai tên khác hẳn, **một nhãn giống hệt**.

> ### ⚠️ CACHE: BUMP, VÀ ĐÂY LÀ HẠNG BUMP KHÁC HẲN MỌI LẦN TRƯỚC
>
> Wave trước kết luận *"không bump"* vì nó chỉ đổi phản hồi TỪ CHỐI, mà
> `main.py` chỉ cache `status == "ok"`. Ở đây ngược hẳn: nhãn nằm **bên trong**
> `scene3d.objects[].label` của envelope `ok` — đúng loại **được** cache.
> Đo bằng ROW THẬT: ghi row `policy_version = 94` mang nhãn cũ, gọi lại
> `/api/analyze` ⇒ route trả **THẲNG** envelope cũ (`provider_bi_goi = 0`), học
> sinh đọc `«đối tượng»` trên mã đã sửa. Bump là cách DUY NHẤT làm row ấy miss.
> Đủ bốn chỗ một commit + khoá lại `lock_cache_identity`.

> ### ⚠️ BUMP LÀM **HAI** CỜ CỦA CON DẤU LỆCH, KHÔNG CHỈ MỘT
>
> Sáu guard đỏ theo, tất cả cùng lớp đã xử ở wave trước: chúng cưỡng chế *"kho
> vẫn ở đúng hệ đã đo"* — câu **tạm thời** viết như bất biến. Bốn guard đăng ký
> lịch sử đã có sẵn khuôn *"đăng ký giữ N, hệ ở M vì wave X"* nên chỉ cập nhật M
> kèm lý do; thứ chúng thật sự bảo vệ là **năm băm model-facing**, và năm băm ấy
> không đổi một byte. `test_B1_G1` xét `CACHE_VERSION_MATCH` riêng cùng lý do
> với `CANDIDATE_HASH_MATCH` và đòi cả hai khớp văn bản khai.

⚠️ **Chống tái phát là phần đáng giá nhất**: guard mới quét **mọi kiểu hình học
trong `MemoryType`** và đòi mỗi kiểu có tên tiếng Việt — thêm kiểu mà quên bảng
là ĐỎ ở test, thay vì hiện *"đối tượng"* trên màn hình vài wave sau.

⚠️ **Phép tiêm bắt lỗi trong chính guard của tôi**: guard kiến trúc bản đầu hỏi
`{o.label}` trên CẢ TỆP, mà chuỗi ấy còn ở chỗ vẽ nhãn điểm — nên bỏ nhãn ô đọc
số vẫn xanh. Đã siết vào đúng khối `geo3d-readout`.

⚠️ **Nợ đã khai, không sửa ở wave này**: `curved_solid` vẫn được NHẮC bằng danh
từ chung *«khối cong»* ở bốn nhãn dù `curved_kind` biết là trụ hay nón. Sửa được
nhưng nó đổi **bốn** nhãn, trong đó hai thuộc mười nhãn mà `§5.3` đòi giữ
nguyên ⇒ `CURVED_KIND_IN_SHORT_REFERENCE`.

```
RECOMMENDED_NEXT_ACTION = THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW
```

Báo cáo: `docs/DISPLAY_NAME_FINAL_POLISH_AND_RELEASE_REFRESH.md`; artifact:
`docs/evaluation/geometry/display-name-final-polish/`.

### 1a-undetricies. `FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE` (2026-09-09)

**Wave kỹ thuật CUỐI. `FINAL_SYSTEM_RELEASE = PASS`.**
`FEATURE_DEVELOPMENT_STATUS = CLOSED` — từ đây đề xuất mới đi vào *Hướng phát
triển*, không nhập tiếp vào bản khoá luận.

```
ROOT_CAUSE = transport headless Chrome ↔ Vite DEV SERVER · SELECTED_BRANCH = C
             (+ khiếm khuyết NHÃN thuộc nhánh B trong chính bộ đo)
FLAKE_RATE 0.9 → 0 · targeted 10/10 · browser 3/3 · visual oracle 3/3
pytest 4807 pass, 1 skip, 1 deselect — 0 đỏ, cây sạch · vitest 813 · tiêm lỗi 4/4
CANDIDATE e40de3b1… KHÔNG ĐỔI · CACHE_VERSION 94 → 94 · MODEL_FACING 5/5 không đổi
PRODUCT_CODE_CHANGED = NO · LIVE_ARTIFACTS 45/45 byte-identical
```

⚠️ **Flake KHÔNG phải "nhãn sai" — trang chưa bao giờ dựng.** Đỏ luôn đi theo
CẶP, luôn ở kịch bản chạy đầu, và **không lần nào** là một nhãn SAI. Chẩn đoán:
`readyState=complete`, `#root` **rỗng suốt 60 giây**, nhật ký mạng ghi
`Script net::ERR_CONNECTION_REFUSED` + `net::ERR_NETWORK_ACCESS_DENIED`.

> ### ⚠️ BỐN PHÉP ĐO PHÂN XỬ NHÁNH — không suy, không đoán
>
> **chậm hay kẹt?** kiên nhẫn 60 s ⇒ **kẹt**. · **sản phẩm hay máy chủ?** Vite
> dev **kẹt 2/15**, bản dựng sản phẩm **0/15**. · **tải lại cứu được?** **0/2**.
> · **phiên Chrome mới cứu được?** **6/10** — có ích, KHÔNG phải thuốc chữa.
> Một giả thuyết bị bác bằng số: `127.0.0.1` **tệ hơn** `localhost` (12/12 kẹt).

> ### ⚠️ NHƯNG BỘ ĐO VẪN CÓ LỖI THẬT, VÀ NÓ TỆ HƠN CHẬP CHỜN
>
> Cổng cũ báo *"nhãn rỗng"* — khẳng định về **NỘI DUNG** — cho một sự cố **HẠ
> TẦNG**. Ai đọc `17/21` sẽ đi sửa `UnsupportedNotice`, tức sửa đúng thứ đang
> chạy tốt. Ba nguyên nhân: ngủ cố định 3000 ms · không phân biệt "chưa tải"
> với "tải rồi mà sai" · **locator không neo** —
> `document.querySelector('.eyebrow')` lấy thẻ `.eyebrow` ĐẦU TIÊN của tài
> liệu, mà trang chủ còn khối *"Gợi ý khám phá"* mang lớp ấy. Phát hiện bằng
> PHÉP TIÊM: bỏ nhãn thẻ từ chối mà cổng vẫn xanh vì nó đọc nhãn thẻ hàng xóm.
>
> Vá: cổng chạy trên **BẢN DỰNG SẢN PHẨM**, đi qua **UI thật + biên
> `/api/analyze`** (bỏ `import('/src/state/…')`), chờ theo trạng thái, quá hạn
> thì ném **`PAGE_NOT_LOADED`** chứ không ghi 21 khẳng định rác. Vẫn đủ **21**
> phép kiểm — không assertion nào bị bỏ.

⚠️ **`RETRY_COUNTS` báo RIÊNG, không gộp vào số lượt đạt.** Cổng đã chuyển sang
bản dựng cần **0 lần mở lại** trong 10 lượt; hai cổng còn trên dev server cần
**1–2 lần mỗi lượt**. Cùng một nguyên nhân, nhìn từ hai phía.

⚠️ **Nợ đã khai, KHÔNG làm trong wave này**: `certify-product-ui-rendering` và
`certify-scene3d-hidden-lines` còn dùng `s.mods.store` (đường dẫn NGUỒN) nên
chưa chạy được trên bản dựng. Chuyển chúng là việc đúng, nhưng sửa ba bộ đo vào
phút cuối kỳ đóng băng đổi lấy rủi ro lớn hơn thứ nó gỡ ⇒
`BROWSER_GATES_ON_PRODUCTION_BUILD` trong `POST_THESIS_BACKLOG`.

**Bàn giao**: `RELEASE_MANIFEST.json` (HAI candidate — hiện tại `e40de3b1…` và
lịch sử `d72db7c3…` — 5 băm model-facing, băm cây `dist/`, phạm vi, giới hạn) ·
12 ảnh demo có xuất xứ đầy đủ (9 ca + 3 ảnh SAU XOAY) · `docs/DEMO_RUNBOOK.md`
12 mục, **chỉ dẫn chạy demo từ BẢN DỰNG, không từ dev server**.

```
RECOMMENDED_NEXT_ACTION = THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW
```

Báo cáo: `docs/FINAL_SYSTEM_REPRODUCIBILITY_AND_RELEASE_FREEZE.md`; artifact:
`docs/evaluation/geometry/final-system-release/`.

### 1a-duodetricies. `PRODUCT_RESPONSE_CONTRACT_ALIGNMENT` (2026-09-09)

**Từ chối nay nêu đủ giai đoạn dừng, loại thất bại, mã lỗi và lý do.**
0 lượt gọi model. `PRODUCT_RESPONSE_CONTRACT_ALIGNMENT = PASS`.

```
ROOT_CAUSE = biên chuyển kết quả · SELECTED_BRANCH = B (tín hiệu CÓ, bị mất)
n1  stage null → semantic_program · code null → semantic_program_invalid
n2  code/tầng GIỮ NGUYÊN · lý do "diễn đạt lại đề" → "ngoài các phép dựng"
pytest 4805 pass, 1 skip, 1 deselect — 0 đỏ, cây sạch @ `82673fa`
vitest 813 pass · trình duyệt 73/73 · tiêm lỗi 7/7
CANDIDATE d72db7c3… → e40de3b1… (92 file) · CACHE_VERSION 94 → 94
MODEL_FACING_CHANGED = NO · LIVE_ARTIFACTS 45/45 byte-identical
```

⚠️ **Tín hiệu chưa bao giờ THIẾU — nó bị ĐÁNH RƠI.** Phát lại nguyên byte qua
bảy biên cho thấy `pipeline` đã phát `stage_reached="semantic_program"` +
`error_code="semantic_program_invalid"` cho observer ngay tại biên 4, rồi
`return None` — một kiểu trả về không chở nổi phán quyết. Telemetry đúng, sản
phẩm sai, nên **mọi cổng đọc telemetry đều xanh** trong khi học sinh nhận một
lời từ chối cụt. Sửa bằng `route.hong_truoc_khi_dung_ir()` (thẩm quyền duy
nhất tra `SEMANTIC_FAILURE_CATEGORY`).

⚠️ **`failure_category` CỐ Ý giữ `geometry_generation_failed`.** Đổi nó sang
`semantic_incomplete` cho `n2` sẽ kích nhánh *"TÁCH THÀNH TỪNG YÊU CẦU"* của
frontend — đúng lời khuyên sai wave này đi sửa. Không mất thông tin: loại là
một HÀM của mã, nên `error_code` có mặt là tra lại được.

> ### ⚠️ BA LỖI CHỈ ẢNH CHỤP BẮT ĐƯỢC, PHÉP KIỂM TỰ ĐỘNG THÌ KHÔNG
>
> **(a)** `learner_reason` (backend, vừa thêm) và câu gợi ý (frontend, vá tạm
> từ wave trước) liệt kê **gần y hệt** một danh sách năng lực ⇒ học sinh đọc
> hai lần cùng một điều. Mọi phép kiểm lúc ấy xanh vì chúng hỏi *"có mặt
> không"*, không hỏi *"có thừa không"*. Nay certifier đo **đoạn trùng dài
> nhất** (ngưỡng 40 ký tự; đo được `n1` 12 · `n2` 6).
> **(b)** Nhãn *"CHƯA DỰNG ĐƯỢC MÔ PHỎNG"* dùng chung cho cả hai ca âm. Chữ
> **"chưa"** đúng với `n1` (thử lại còn cửa), **sai** với `n2` (không phép IR
> nào tạo ra vật ấy). `n2` nay mang *"NGOÀI PHẠM VI DỰNG HÌNH"*.
> **(c)** Câu chốt còn ghi *"khối đa diện **lồi**; mặt cong chưa mô phỏng
> được"* — hết đúng từ 2026-09-03/09-07, và chính lượt đo cuối phục vụ đủ cầu,
> trụ, nón, đáy lõm ở `p2`–`p5`. Tự khai năng lực THẤP hơn thực tế vẫn là nói
> sai, và nó đuổi học sinh khỏi đúng những bài hệ làm được.

> ### ⚠️ LẦN ĐẦU `backend/app` ĐỔI SAU LƯỢT NGHIỆM THU CUỐI
>
> Trước wave này hai câu khác hẳn nhau vẫn trùng nhau: *(i)* chính sách đăng ký
> trước trỏ đúng hệ ĐÃ đo — sự thật **lịch sử**; *(ii)* kho hiện ở đúng hệ ấy —
> sự thật **tạm thời**. `test_C1`/`test_C2` cưỡng chế cả hai bằng một phép so
> với mã đang chạy; cưỡng chế *(ii)* mãi mãi thì guard **cấm sửa lỗi** chứ
> không còn bảo vệ pre-registration.
>
> `test_C2` nay so với `IDENTITY_LOCK.json` — artifact **bất biến**, chứng cứ
> mạnh hơn mã đang chạy. **`test_C2b`** nhận lại đúng cái răng vừa nhả:
> candidate hiện tại phải được **KHAI** ở `CANDIDATE_DIVERGENCE.json` kèm lý do
> và wave (quên khai ⇒ đỏ; khai sai băm ⇒ đỏ). Runner nay **từ chối chạy lại**
> trên mã hiện tại — hành vi ĐÚNG, khoá bởi `test_B1_G1`.
> **KHÔNG sửa** `thesis_final_acceptance_policy.json`; số liệu lượt đo cuối
> **không chấm lại** — chúng mô tả `d72db7c3…`.

⚠️ **Cache đo bằng ROW THẬT, không bằng tiền lệ**: gọi `/api/analyze` qua
`TestClient` rồi soi bảng — đề bị từ chối ghi **0 row**, nên không có row cũ nào
để trả thẳng. Chiều thay đổi không phải `served→rejected` cũng không phải
`rejected→served`; phán quyết cả 9 ca giữ nguyên ⇒ **không bump**.

⚠️ **Hai flake đã ghi, không giấu**: `certify-refusal-surface.mjs` cho 17–19/21,
luôn ở kịch bản chạy ĐẦU và luôn là "nhãn rỗng" — kiểm trên cây **trước bản vá**
(`git stash`) cho **19/21 cùng triệu chứng** ⇒ có trước wave này. Và một lượt
pytest đầy đủ cho 2 đỏ thừa ở `test_live_session_api.py` (34/34 khi chạy riêng,
lượt kế tiếp xanh) — cùng lớp flake đã ghi ở `§1a-septvicies`.

⚠️ **`n1` KHÔNG được khai là "ngoài bao đóng"**, dù ma trận năng lực xếp khối
tròn xoay tổng quát là `OUT_OF_SCOPE`: lượt chạy **dừng trước** cổng phủ, nên hệ
chỉ biết *chương trình không hợp lệ*. Gán phán quyết mạnh hơn là khai một điều
lượt đo không thiết lập.

```
RECOMMENDED_NEXT_ACTION = THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW
```

Báo cáo: `docs/PRODUCT_RESPONSE_CONTRACT_ALIGNMENT.md`; artifact:
`docs/evaluation/geometry/product-response-contract-alignment/`.

### 1a-septvicies. `THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW` (2026-09-09)

**Wave RÀ SOÁT. 0 lượt gọi model, 0 byte mã sản phẩm.** Đối chiếu 29 tuyên bố
học thuật với bằng chứng đóng băng.

```
OBJECTIVE_SOURCE = docs/THESIS_DRAFT.md §3·§4·§6·§1.6·§1.7   (KHÔNG phải NOT_LOCATED)
OBJECTIVES 5 (MT) + 7 (ĐG) · RQ 5 · CLAIMS_REVIEWED 29
PROVED_ON_FROZEN_BENCHMARK 13 · PARTIAL 8 · NOT_MEASURED 2 · OUT_OF_SCOPE 2
CONTRADICTED 4 · DOCUMENTATION_CORRECTIONS 4
pytest 4781 pass, 1 skip, 1 deselect — 0 đỏ, cây sạch @ `a411ea8` · vitest 798
CANDIDATE d72db7c3… · CACHE_VERSION 94 → 94
```

⚠️ **Mọi số bàn giao ĐO LẠI, không mặc định** — 14 con số tra lại từ artifact có
băm; tất cả khớp. Cộng hai phép chạy tất định: `doi_chieu_ket_qua_cuoi.py` PASS
(0/31 lệch · 12/12) và `scene3d_world_oracles.py` 7/7 tolerance 0.

> ### ⚠️ BỐN TUYÊN BỐ ĐÃ TRÔI — ĐÍNH CHÍNH, GIỮ NGUYÊN BẢN GỐC
>
> **D-2 · Bảng "ngoài phạm vi" của bản thảo bị chính bằng chứng bác.**
> `THESIS_DRAFT §4` khai **mặt cong**, **khối không lồi**, **phương trình mặt
> phẳng** là NGOÀI phạm vi; tóm tắt khai *"chỉ khối đa diện lồi, không mặt
> cong"*. Lượt đo cuối **phục vụ đúng cả ba**: `p3` cầu · `p4` trụ · `p5` nón ·
> `p2` đáy ngũ giác **LÕM** · `p6` mặt phẳng cho bằng phương trình. Đã ghi đính
> chính **bên trên** bảng gốc; bảng gốc giữ nguyên.
>
> **D-4 · Bản thảo có HAI THÂN CHƯƠNG 4 RỜI NHAU.** `THESIS_DRAFT` mô tả bốn
> lượt niêm phong `n = 4–6` và **không nhắc một chữ** về lượt đo cuối (`rg` cho
> 0 kết quả); `docs/thesis/CHAPTER_4` mô tả lượt cuối 9 ca. Hợp nhất thuộc wave
> tích hợp bản thảo.
>
> **D-1** ma trận đăng ký ghi "11 đại lượng" (artifact nói 12) — **không sửa**
> văn bản đăng ký trước. **D-3** `product_capability.py` ghi lý do *"MÔ HÌNH:
> chưa đo"* cho khối cong, trong khi mô hình ĐÃ được đo 5/5 — nhưng **trạng thái
> `foundation_only` vẫn đúng** (`n = 1` không đủ để bật); chỉ chuỗi lý do cũ, và
> sửa nó chạm `backend/app` nên chuyển thành nợ.

⚠️ **Một khoảng trống truy xuất đã vá.** Báo cáo UI ghi *"6/6 phép tiêm"* nhưng
`UI_ACCEPTANCE_MATRIX.json` trên đĩa ghi `FAULT_INJECTIONS = 0` — lượt chạy SẠCH
cuối đã ghi đè artifact của lượt `--faultcheck`. Con số **đúng** nhưng **không
dẫn về đâu**. Chạy lại (0 lượt gọi): artifact nay ghi 6/6, 66/66. Đúng lớp lỗi
cổng "mọi số liệu truy được tới artifact" tồn tại để chặn.

⚠️ **Ranh giới đã giữ**: hidden-line PASS **không** được dùng để đổi visual
fidelity tổng thể từ `PARTIAL` sang `PASS` (giữ 39/41) · không câu nào tuyên bố
ổn định (quét `rg`: ba lần xuất hiện chữ ấy đều không phải tuyên bố — `C7` dùng
theo nghĩa *mã lỗi không đổi tên*) · phạm vi hình học tách **ba nhóm** thay vì
"đã hỗ trợ đầy đủ" · candidate **lịch sử** và **hiện tại** ghi thành hai trường
dù đang trùng `d72db7c3…`.

**Hai follow-up, quyết định dẫn NGUYÊN VĂN mục tiêu:**
`DISPLAY_NAME_AUTHORITY…` = **OPTIONAL_POLISH** — `§1.6` cam kết *"các đại lượng
được hỏi, tính bằng số học chính xác"*, không cam kết chất lượng tên gọi; `rg`
toàn bản thảo không có cam kết nào về nhãn cho người học.
`PRODUCT_RESPONSE_CONTRACT_ALIGNMENT` = **REQUIRED_BEFORE_FINAL_DEMO** — `§1.6`
và `§3.9` cam kết nguyên văn *"từ chối có cấu trúc — nêu **giai đoạn dừng, loại
thất bại, mã lỗi**"*, mà `n1` giao `stage_reached: null` và `error_code: null`,
tức **hai trên bốn** trường đã hứa.

```
RECOMMENDED_NEXT_ACTION = PRODUCT_RESPONSE_CONTRACT_ALIGNMENT
```

Báo cáo: `docs/THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW.md`; ma trận:
`docs/thesis/CLAIM_EVIDENCE_MATRIX.md`.

### 1a-sexvicies. `SCENE3D_DYNAMIC_HIDDEN_LINES_AND_READABILITY` (2026-09-09)

**Nét liền / nét khuất nay cập nhật theo camera. `DYNAMIC_HIDDEN_LINES = PASS`.**
0 lượt gọi model, `backend/app` 0 byte.

```
OCCLUSION_CLASSIFICATION PASS (3/3, oracle ĐỘC LẬP) · RASTER_LINE_STYLE PASS
CURVED_SOLID_READABILITY PASS · SECTION_READABILITY PASS · PLANE_PATCH_FIT 3/3
CAMERA_AND_TRACE_REGRESSION 9/9 · EXACT_VALUES 12/12 · TIÊM LỖI 6/6
hidden-lines 23/23 · visual-fidelity 39/41 · product-ui 66/66 · vitest 798 · pytest 4781
CANDIDATE d72db7c3… · CACHE_VERSION 94 → 94
```

> ### ⚠️ TRƯỚC WAVE NÀY KHÔNG CÓ HIDDEN-LINE NÀO CẢ
>
> Không phải "làm chưa tốt" — **chưa từng có**. Mọi khối khai `depthWrite:
> false`, nên không gì che được gì và một cạnh sau quả cầu vẽ y hệt cạnh trước
> nó. Wave trước còn đi ngược: thiết diện mang `depthTest: false` để "luôn nhìn
> thấy", tức vẽ đè lên mọi thứ — và khi mọi phần đều vẽ đè thì phần thấy và
> phần khuất hiện y hệt nhau.
>
> Sửa bằng hai mảnh, không mảnh nào cần phép hình học mới: **lớp chiều sâu vô
> hình** cho khối THẬT (miếng mặt phẳng KHÔNG có — nó là vật minh hoạ, không
> được che gì), và **vẽ hai lượt** (`LessEqualDepth` / `GreaterDepth`). GPU
> quyết theo TỪNG ĐIỂM ẢNH ⇒ một cạnh tự chia nhiều đoạn, và xoay camera thì
> phân loại đổi theo — không có cache nào để lỗi thời.

⚠️ **Ba lỗi phải gỡ, và cả ba VÔ HÌNH trong một ảnh tĩnh ở một góc.**
(a) `polygonOffsetFactor` co giãn theo ĐỘ DỐC: mặt cắt dốc (`p3`,`p7` ở góc mặc
định) khuếch đại độ lệch tới mức cả vành thắng phép kiểm chiều sâu — `p7` **0
lần đổi nét**, `p3` chỉ đứt SAU khi xoay. (b) Lớp chiều sâu khai `transparent`
nên nằm trong hàng đợi còn sắp theo KHOẢNG CÁCH, ghi chiều sâu SAU khi vành đã
hỏi. (c) 24 nét trên vành ~120px cho khe đứt ~2,5px — không đọc ra, không đo
được.

⚠️ **Chẩn đoán quyết định là tô lượt khuất MÀU ĐỎ.** Ảnh `p3` góc mặc định cho
thấy ĐỎ và HỔ PHÁCH **chồng nhau trên cùng một cung** ⇒ cả hai lượt cùng vẽ.
Không có phép thử ấy thì triệu chứng trỏ nhầm sang phép kiểm chiều sâu, sang độ
lệch, hoặc sang bộ đo.

⚠️ **Một ngưỡng phải hiệu chỉnh vì phép tiêm lọt lưới.** Tiêu chí "nét đứt" đầu
tiên (đổi ≥2 lần, tỉ lệ 0,1–0,95) **không bắt được** phép tiêm *"vẽ liền hết"*:
khi ấy cung khuất chẳng vẽ gì, chỉ còn răng cưa 15–37% với 2 lần đổi, và tiêu
chí đọc "thưa" thành "đứt". Hai quần thể tách bạch (thật 62–80%, tiêm 15–37%)
⇒ vạch đặt ở **0,5**. Sau đó: nền 20/21, tiêm 15/21.

⚠️ **Một phép kiểm xoay RỖNG NGHĨA đã bỏ.** Bản đầu so cờ nét tại vị trí điểm
ảnh CŨ sau khi xoay rồi mừng vì 69/72 điểm "đổi" — nhưng xoay xong đường cong đã
đi chỗ khác, nên nó đo *hình có dịch không*. Nay tính lại camera
(`2π·dx/clientHeight`) rồi chạy lại oracle trên chính các điểm thế giới ấy, kèm
**cổng tự-kiểm** để camera dự đoán sai thì lộ ra ngay.

⚠️ **Phép tiêm miếng mặt phẳng ban đầu làm cổng TỰ TẮT chứ không đỏ** (báo 38/38
vì không còn cặp nào để so) — cùng lớp lỗi đã sửa ở oracle. Nay cảnh có mặt
phẳng và có thiết diện mà không tính được miếng là ĐỎ.

Giới hạn còn lại: nét khuất của khối đa diện dùng chu kỳ theo ĐỘ DÀI THẾ GIỚI
(chưa đo ở dải thu phóng cực trị) · oracle pháp tuyến chỉ đúng cho khối LỒI ·
`VISUAL_REVIEW` do chính tác giả wave kiểm.

```
DYNAMIC_HIDDEN_LINES = PASS
RECOMMENDED_NEXT_ACTION = THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW
```

⚠️ Wave trước vẫn **PARTIAL** — bản này KHÔNG chuyển nó thành PASS. Thứ PASS ở
đây là hợp đồng hiển thị MỚI.
Báo cáo: `docs/SCENE3D_DYNAMIC_HIDDEN_LINES_AND_READABILITY.md`; artifact ở
`docs/evaluation/geometry/scene3d-hidden-lines/` (8 ảnh + 18 khung xoay).

### 1a-quinvicies. `SCENE3D_VISUAL_SEMANTIC_FIDELITY_REVIEW` (2026-09-09)

**Hình trên màn hình nay thể hiện đúng quan hệ hình học. `PARTIAL`, không phải
`PASS` — ba lý do nêu tên ở dưới.** 0 lượt gọi model.

```
WORLD_SPACE_GEOMETRY 7/7 (hữu tỉ chính xác, tolerance 0) · TIÊM LỖI ORACLE 5/5
PLANE_SECTION_RELATION 3/3 (nền 0/3) · CAMERA_FRAMING 7/7 (nền 6/7)
CONCAVITY 1/1 · NEGATIVE_MESSAGE_CONSISTENCY 2/2 (nền 0/2)
DISPLAY_NAME 10/12 (KHÔNG đổi) · SECTION_VISIBILITY KHÔNG THIẾT LẬP ĐƯỢC
BROWSER 39/41 (nền 34/38) · 18 ảnh · ngoại lệ 0 · vitest 790 · pytest 4781
BACKEND 0 byte · CANDIDATE d72db7c3… · CACHE_VERSION 94 → 94
```

⚠️ **Nhánh A đóng bằng SỐ HỌC trước khi chạm renderer.**
`scene3d_world_oracles.py` kiểm 16 điểm mẫu mỗi đường cong bằng `Fraction`,
tolerance **bằng 0**: `p7` có elip `P(t) = (1−2cos t, √3 sin t, 8+2cos t)` thoả
`x+z=9` với mọi `t` **và** `x²+y² = (6−z/2)²`. Dữ liệu đúng tuyệt đối; mọi thứ
sửa được đều ở tầng trình bày. Oracle phải mở sang **ℚ(√c)** mới làm được — bản
đầu bỏ qua đúng `p7` vì bán trục nhỏ là `√(1/48)`, và rơi về float thì phải có
tolerance, mà tolerance che đúng lớp lỗi đang tìm.

⚠️ **Oracle từng có lỗ TỰ TẮT**: nó ghép thiết diện với mặt phẳng bằng cách so
pháp tuyến bằng nhau, nên phép tiêm "xoay sai pháp tuyến" **không đỏ** — phép
kiểm bị BỎ QUA và oracle im lặng báo đạt. Nay ghép bằng **phép chứa**.

> ### ⚠️ MIẾNG MẶT PHẲNG — LỖI LỚN NHẤT, ĐO ĐƯỢC BẰNG SỐ
>
> `PLANE_DISPLAY_SIZE = 6` là ô vuông **cố định** đặt tại `plane3.point`, mà
> `point` chỉ là **một điểm bất kỳ** trên một mặt phẳng vô hạn. Ở `p7` nó ở
> `(9,0,0)` còn thiết diện ở `(1,0,8)`: cách **11,31** trong khi nửa đường chéo
> miếng là **4,24** — miếng KHÔNG chạm tới thiết diện, và ảnh đọc ra đúng vậy.
> Nay `khungMatPhang` chiếu mọi điểm **có biên** xuống mặt phẳng, tâm = tâm hình
> chiếu, cạnh = đường kính × 1,15. Phủ hết ở cả 3/3 ca.

⚠️ **Khung nhìn có HAI lỗi độc lập cùng triệu chứng, cộng một lỗi của chính bản
vá.** (a) auto-fit tính ở **bước 0** khi cảnh mới có vài điểm ⇒ mặt cầu `p3` xuất
hiện sau và bị CẮT (`lề 0px · chiếm 100%`); (b) miếng mặt phẳng và đoạn đại diện
đường thẳng **vô hạn** tham gia tính khung ⇒ quyết định trình bày tự khuếch đại;
(c) `diemHuuHan` nở bán kính theo cả ba trục toạ độ, kể cả **dọc trục khối** ⇒
hộp bao hình nón cao 22 thay vì 12, hình chỉ chiếm 21% khung.

⚠️ **`THREE.Line` luôn dày một điểm ảnh** (WebGL bỏ `linewidth`): đường tròn
thiết diện `p3` chiếm **6 điểm ảnh** trên cả khung 1318×545. Nay thiết diện là
**dải**, dày theo `SECTION_STROKE_RATIO × đường kính cảnh`, cộng
`depthTest: false` + `renderOrder` để nửa vòng xa không bị khối nuốt.

> ### ⚠️ TÊN HIỂN THỊ: SỬA ĐƯỢC, RỒI HOÀN TÁC CÓ CHỦ ĐÍCH
>
> Nguyên nhân định vị chính xác: `_DANH_TU_NGAN` thiếu `ellipse3` từ wave thiết
> diện xiên; bảng ấy là lối rơi cuối của `goi_ngan` nên thiếu một kiểu là kiểu ấy
> mất tên trong MỌI câu — mất im lặng. Bản vá hai dòng cho đúng `Diện tích elip`.
>
> **Hoàn tác**, vì nó đổi `CANDIDATE_HASH d72db7c3… → ff508b36…` và làm
> `test_C2_policy_tro_dung_corpus_va_candidate` ĐỎ: hợp đồng đo
> (`created_before_live_run = true`) ghim `candidate_hash = d72db7c3…`, nên giữ
> bản vá đồng nghĩa **viết lại một văn bản ĐĂNG KÝ TRƯỚC cho khớp mã sửa SAU
> lượt đo**. Theo §10 của đặc tả: dừng, hoàn tác, báo. `backend/app` **0 byte**.

⚠️ **`SECTION_VISIBILITY` KHÔNG thiết lập được, và phải nói ra.** Ngưỡng "≥ N
điểm ảnh" là con số bịa (phụ thuộc độ phân giải, bề dày nét, mức thu phóng); chỉ
số thay thế không phụ thuộc tỉ lệ thì **đạt cả ở nền** (`p3`: 0,924). Hai chỉ số
đều không cô lập được khác biệt mà `depthTest` tạo ra. Bằng chứng còn lại là
**ảnh** — thật, nhưng không tự động, nên không được ghi thành một con số PASS.

⚠️ **Ba phép tiêm ở tầng trình duyệt KHÔNG đỏ, và đó là phát hiện.** Hai phép
không đỏ *vì bản vá làm đúng việc* (miếng tự co giãn nên vẫn phủ; cổng phát hiện
pháp tuyến sai là **oracle**, và oracle đỏ). Phép thứ ba cho thấy chỉ số lõm
không nhạy như tưởng. Phép nói lên bản vá rõ nhất: dời `plane3.point` **500 đơn
vị dọc mặt phẳng** không đổi gì cả — trước bản vá chính nó đẩy miếng ra khỏi màn
hình.

```
VISUAL_DEMO_FIDELITY_ON_FROZEN_CASES = PARTIAL
RECOMMENDED_NEXT_ACTION = THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW
FOLLOW_UP = DISPLAY_NAME_AUTHORITY_ELLIPSE_AND_CURVED_KIND
FOLLOW_UP = PRODUCT_RESPONSE_CONTRACT_ALIGNMENT
```

Báo cáo: `docs/SCENE3D_VISUAL_SEMANTIC_FIDELITY_REVIEW.md`; artifact ở
`docs/evaluation/geometry/scene3d-visual-fidelity/` (4 JSON · 18 ảnh
before/after · băm đủ).

### 1a-quatervicies. `PRODUCT_UI_RESULT_RENDERING_AND_DEMO_ACCEPTANCE` (2026-09-09)

**Chín envelope của lượt đo cuối ĐÃ DỰNG THÀNH MÔ PHỎNG trong Chrome thật.**
0 lượt gọi model, 0 lượt gọi provider.

```
UI_RESULT_RENDERING = PASS · 66/66 phép kiểm · 9 ảnh · ngoại lệ 0
POSITIVE_RENDERED 7/7 · NEGATIVE_PRESENTED 2/2 · EXACT_DISPLAY 12/12
TRACE_PLAYBACK 7/7 · STATE_ISOLATION 9/9 · TIÊM LỖI 6/6 ĐỎ ĐÚNG CHỖ
CANDIDATE d72db7c3… KHÔNG đổi · CACHE_VERSION 94 → 94 · BACKEND 0 byte
LIVE_ARTIFACTS 0 byte · vitest 788 pass · pytest 4779 pass
```

Đường đã chứng minh: `/api/analyze` (chặn ở biên mạng, trả fixture đóng băng) →
`analyzeViaServer` → rẽ theo `status` → `loadEnvelope`/`loadUnsupported` →
`hopLeScene3D` → `Scene3DExplorer` → canvas WebGL → tua bước → **đáp số đọc
trên màn hình**.

⚠️ **Chặn ở biên mạng chứ không nạp thẳng store, và đó là điểm khác của wave
này.** `loadEnvelope` là đúng cửa Thư viện đi qua — mọi spot-check trước đều
dùng nó — nhưng nó **bỏ qua** đoạn `onAnalyze → analyzeViaServer → rẽ theo
status`, tức đúng đoạn "response adapter". Ở đây: gõ đề vào ô nhập thật, bấm nút
thật.

⚠️ **Envelope phải DỰNG LẠI, không chép được.** Artifact lượt đo giữ
`chuong_trinh` + `cham`, **không** giữ envelope. Dựng lại bằng đúng đường sản
phẩm (`verify_and_compile` → `_dung_scene3d` → `_envelope_tu_route_sinh` /
`_that_bai_hinh_hoc` → `attach_learner_reason`), rồi **đối chứng** với `cham`
đóng băng ở `SERVABLE` · kiểu ngữ nghĩa · từng `expected_display`; lệch là NÉM.
Hai bẫy đã mắc: (a) `scene3d_kinds` là kiểu NGỮ NGHĨA chứ không phải `render` —
so nhầm bảng thì MỌI ca "lệch"; (b) **không** được so với `actual_display`, vì
đó chính là trường lỗi bộ chấm wave trước làm rỗng ở 6/7 ca.

> ### ⚠️ NHÁNH B — MỘT BẢN VÁ TẦNG TRÌNH BÀY, VÌ THẺ TỪ CHỐI HỨA SAI
>
> Ảnh `n1`/`n2` cho thấy hai bài **ngoài bao đóng** đọc được câu *"Dạng bài này
> hệ có mô phỏng — thử diễn đạt lại đề gọn hơn"*. Khối tròn xoay tổng quát và
> khối ghép/bù là `OUT_OF_SCOPE` **vì lý do kiến trúc** — hệ sẽ không bao giờ mô
> phỏng chúng, nên câu ấy là lời hứa sai.
>
> `geometry_generation_failed` gộp hai tình huống ngược nhau: bài TRONG bao đóng
> mà mô hình viết hỏng (diễn đạt lại thì giúp) vs bài NGOÀI bao đóng (viết lại
> bao nhiêu lần cũng vậy). Cổng phủ ĐÃ phân biệt sẵn bằng
> `requested_operation_uncovered`; chỗ thiếu là bề mặt học sinh chưa đọc mã ấy.
> Cùng lớp lỗi đã sửa hai lần cho `out_of_scope` vs `not_simulation_suitable`,
> cùng cách sửa: đọc `error_code` TRƯỚC khi rơi về câu chung.
>
> Bản vá đổi **duy nhất câu gợi ý** trong `UnsupportedNotice`. Có nền đỏ ghi
> nguyên văn trước khi sửa. `failure_category`, `error_code`, `learner_reason`
> và hành vi fail-closed **không đụng** — chúng do backend sở hữu.
>
> **Candidate KHÔNG đổi**: `components/` và `domains/geometry/` không nằm trong
> `MEASURED_SYSTEM_PATHS`; `freeze --verify` vẫn `d72db7c3…`. Bề mặt mô hình
> KHÔNG đổi ⇒ `CACHE_VERSION` giữ 94.

⚠️ **Phần CHƯA sửa được — bằng chứng Nhánh C.** `n1` bị chặn ở
`stage_semantic_program` nên envelope mang `error_code: null`, `stage_reached:
null`: **phản hồi không chở tín hiệu nào để phân biệt**, tầng trình bày không có
gì để đọc. Và thẻ `n2` nay nói **hai giọng** — câu gợi ý đã đúng, nhưng thân
`learner_reason` (do `backend/app/learner_messages.py` sở hữu) vẫn khuyên "diễn
đạt lại". Sửa nó là sửa `backend/app` ⇒ đóng băng lại candidate, mà đặc tả wave
cấm. Bản vá vẫn là cải thiện chặt: nó **gỡ một khẳng định SAI SỰ THẬT**.

> ### ⚠️ ĐÍNH CHÍNH — 11 → 12 ĐẠI LƯỢNG
>
> `THESIS_FINAL_ACCEPTANCE_EXECUTION`, ledger, mục §1a-duovicies và hai chương
> đều ghi *"11/11 đại lượng"*. Artifact nói **12** (p1 ba · p3/p4/p5 hai ·
> p2/p6/p7 một). Hai nguồn độc lập xác nhận: `SCORING_CORRECTION.json` có 12 mục
> `quantities_SUA` đều `exact_answer_match = true`, và cảnh 3D phát đúng 12 số
> đo — đọc được trên màn hình ở lượt nghiệm thu này.
>
> Con số 11 đến từ `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION §76` rồi được
> chép lại, và **chưa từng được máy đối chiếu**: `doi_chieu_ket_qua_cuoi.py` vốn
> đã chấm `DAP_SO_KHOP 12/12` và ĐẠT — không ai đối chiếu con số kể bằng chữ.
>
> Đã sửa ở tài liệu KẾT QUẢ. **KHÔNG** sửa văn bản ĐĂNG KÝ TRƯỚC — sửa nó sau
> khi thấy kết quả là xoá đúng thứ nó tồn tại để giữ. Nay có test neo con số vào
> `SCORING_CORRECTION.json`.

⚠️ **Guard `A5` của bộ đánh giá phải nới, và nới theo lối kiểm được.**
`test_A5_de_bai_MOI__khong_trung_corpus_phat_trien` quét mọi JSON dưới
`docs/evaluation/geometry/` tìm `problem_text` và loại trừ **theo đường dẫn**.
Fixture hiển thị chở lại `problem_text` (để gõ vào ô nhập) nhưng nằm thư mục
khác ⇒ guard kết luận lượt đo cuối đã chấm trên bài cũ — sai theo hướng nghiêm
trọng nhất. Nới bằng **lời khai kiểm được** (`source_artifact_path` phải trỏ tới
artifact CÓ THẬT dưới thư mục lượt đo), kèm `A5b` chứng minh quyền miễn trừ
không mua được bằng chuỗi đặt bừa và `A5c` chứng minh nó trúng đúng đích.

⚠️ **Một phép tiêm ĐÃ HỎNG, giữ lại vì nó dạy được**: tiêm định danh vào
`description` **không đỏ**, vì đề bài nằm sau nút «Xem đề» nên không lên
`innerText`. Guard soi thứ NGƯỜI HỌC THẤY ⇒ phép tiêm cũng phải đặt vào chỗ
người học thấy.

Ghi thêm, không sửa: dải đáp số ca elip đọc *"Diện tích «đối tượng»"* — thẩm
quyền đặt tên ở `display_names.py`, tức `MEASURED_SYSTEM_PATHS`, ngoài phạm vi.
Con số và hình đều đúng.

```
DEMO_READY_ON_FROZEN_CASES = YES · PRODUCT_DEPLOYMENT_READY = NOT_CLAIMED
RECOMMENDED_NEXT_ACTION = THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW
```

`DEMO_READY_ON_FROZEN_CASES` nói đúng chín ca đã đóng băng, một bề rộng
(1440×900), một trình duyệt, WebGL phần mềm — **không** nói sản phẩm sẵn sàng
triển khai.
Báo cáo: `docs/PRODUCT_UI_RESULT_RENDERING_AND_DEMO_ACCEPTANCE.md`; artifact ở
`docs/evaluation/geometry/product-ui-result-rendering/` (9 fixture · 9 ảnh ·
`UI_ACCEPTANCE_MATRIX.json` · `FIXTURE_HASHES.json`).

### 1a-tervicies. `THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING` (2026-09-08)

**Wave TÀI LIỆU. 0 lượt gọi model, 0 byte mã sản phẩm, 0 byte bộ đo, 0 byte
artifact lượt đo.** Đối chiếu số liệu ngoại tuyến rồi viết hai chương luận văn.

```
APPLICATION_LLM_CALLS = 0 · REAL_PROVIDER_CALLS = 0
DOCUMENTATION_INPUT_CONSISTENCY = PASS
  ARTIFACT_HASH_VERIFICATION  PASS (26 file · 19 raw nguyên byte)
  CORRECTION_LINKAGE          PASS (3 artifact được đính chính)
  DAP_SO_KHOP                 PASS (12/12, khớp TỪNG KÝ TỰ)
  SO_TRUONG_LECH              0/31
CACHE_VERSION 94 → 94 · CANDIDATE d72db7c3… KHÔNG đóng băng lại
BỀ MẶT MÔ HÌNH: KHÔNG ĐỔI
```

Cổng §3 hiện thực hoá thành `backend/scripts/doi_chieu_ket_qua_cuoi.py` — tái
tính mọi con số **từ artifact có băm**, không đọc một dòng nào của ba báo cáo
wave trước.

⚠️ **Điểm thiết kế đáng giữ: đối chứng phải NGOÀI.** `BANG_CHUAN` (31 trường)
chép từ **đặc tả wave**, tức nguồn ngoài kho artifact. *Một file tự so với chính
nó thì luôn đúng* — giá trị nằm ở chỗ hai nguồn độc lập (đặc tả do người soạn ·
artifact do máy sinh) trùng nhau.

⚠️ **`RECONCILIATION.json` ghi NGOÀI thư mục lượt chạy**, có chủ đích: ghi vào
trong sẽ thành "file ngoài bảng" của `ARTIFACT_HASHES.json` và **phá chính** tính
bất biến từng byte mà wave này phải giữ. Một công cụ kiểm tính bất biến không
được là thứ phá nó.

Tài liệu: `docs/thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md` (11 mục, **10 bảng**)
· `docs/thesis/CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md` (4 mục). Mười hai biểu
thức đáp số giữ **nguyên văn** theo quy ước hiển thị hữu tỉ · π · căn.

Ba chỗ chương viết khác lệ thường, ghi lại vì đó là **kết quả**, không phải phụ
lục: (a) lỗi bộ chấm thành mục riêng §4.8 với
`MEASUREMENT_FAILURE_COUNT = 1 · SYSTEM_FAILURE_COUNT = 0`, kèm lý do stub không
bắt được; (b) `n1` ghi là giới hạn của **phép đăng ký trước**, giữ nguyên kỳ vọng
đã đăng ký; (c) chi phí tách hai vai — dự báo lệch +31 %, trần cứng vẫn đúng vai
trò *một cái phanh, không phải một dự báo*.

Chương **không** tuyên bố: held-out · ước lượng tổng thể · độ ổn định · phủ
chương trình phổ thông · chất lượng sư phạm · đủ điều kiện bật tính năng.

Cổng: `doi_chieu_ket_qua_cuoi.py` **PASS** (0/31 lệch · 12/12 đáp số) · `pytest`
**4775 pass, 1 skip, 1 deselect — 0 đỏ** (cây sạch @ `4524840`, đo hai lượt) ·
`vitest` **718 pass / 52 file, 0 đỏ** · `git diff --check` sạch ·
`freeze --verify` exit 0 (92 file, `d72db7c3…`) · cache identity exit 0 @ v94.

⚠️ Trên cây **bẩn**, `test_holdout_readiness_7b.py::test_bao_cao_da_sinh_va_KHONG_TROI`
đỏ theo **đúng thiết kế** — nó soi `blockers()` và *"cây làm việc bẩn"* là một
blocker. Đỏ ấy là guard làm việc, không phải hồi quy; đo số phải trên cây sạch.

```
RECOMMENDED_NEXT_ACTION = THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW
```

Ghép hai chương vào bản thảo toàn văn: thống nhất đánh số chương/bảng với chương
1–3, dựng mục lục bảng, soát cuối để không chương nào tuyên bố rộng hơn danh sách
"không tuyên bố" ở trên.
Báo cáo: `docs/THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING.md`.

### 1a-duovicies. `THESIS_FINAL_ACCEPTANCE_EXECUTION` (2026-09-08)

**Lượt đánh giá cuối ĐÃ CHẠY. `RUN_VALIDITY = VALID`. Hệ phục vụ 7/7 bài trong
phạm vi với đáp số CHÍNH XÁC TUYỆT ĐỐI và từ chối 2/2 bài ngoài bao đóng.**

```
PRE_LIVE_GUARD = PASS (8/8) · RUN_ID = thesis-final-20260908T160224Z
APPLICATION_LLM_CALLS = 19 (analyze 9 · synthesis 9 · repair 1)
PHYSICAL 19 · TRANSPORT_RETRIES 0 · TOKENS 97 869 / trần 196 000
FIRST_ATTEMPT_SERVABLE 6/7 · RECOVERY_WITHIN_ONE_REPAIR 1/1 · FINAL 7/7
EXACT_ANSWER 7/7 · ORACLE 7/7 · SOURCE_INVARIANTS 7/7 · SCENE3D 7/7
NEGATIVE_FAIL_CLOSED 2/2 · TARGET_BOUNDARY_PASS 1/2 (đo, không phải ngưỡng)
SILENT_WRONG_ANSWER 0 · UNHANDLED_EXCEPTION 0 · SYSTEM_FAILURE 0
CANDIDATE d72db7c3… KHÔNG đổi · CACHE_VERSION 94 · IDENTITY_AFTER_RUN_STABLE
```

Đáp số: `72`·`9`·`3√6` (chóp+thiết diện+khoảng cách) · `96` (đáy ngũ giác LÕM) ·
`4500π`·`144π` (cầu+thiết diện tròn) · `360π`·`120π` (trụ) · `100π`·`65π` (nón) ·
`25π√5` (elip xiên TRỤ) · `2π√6` (elip xiên NÓN). **12/12 đại lượng** khớp cả
chuỗi hiển thị lẫn oracle độc lập.

**Chặng B tiếp tục chạy được trên đầu ra THẬT của mô hình**: `p3` hỏng ở
`IR_OPERAND_TYPE: 'S' — cần solid, có curved_solid`, một lượt sửa dùng lại hợp
đồng đã đóng băng + raw candidate + chẩn đoán (`analyze_calls_in_stage_b = 0`)
rồi `served`.

> ### ⚠️ MỘT LỖI ĐO, VÀ NÓ SUÝT TỐ CÁO HỆ
>
> Lượt gốc báo `SILENT_WRONG_ANSWER_COUNT = **6**` — sáu lần hệ phát ra đáp số
> sai. Nếu đúng, nó phá chính luận điểm của đề tài. **Nó không đúng**: bộ chấm
> tra đáp số bằng `final_memory[<tên biến của GOLD>]`, trong khi tên biến là thứ
> **mô hình tự đặt** (`the_volume_sabcd`, `V_S_MNPQR`, `dien_tich_elip_e`…).
> Nên `actual_display = None` ở 6/7 ca **có đáp số hoàn toàn đúng**.
>
> ⚠️ **Chứng nhận stub KHÔNG bắt được**, và lý do đáng ghi: stub trả về CHÍNH
> gold program, nên tên witness của "mô hình" luôn TRÙNG tên gold. *Một provider
> giả giống bản mẫu quá mức thì không kiểm được thứ chỉ sai khi mô hình được tự
> do.*
>
> Sửa: ánh xạ theo **`kind` của nghĩa vụ** — thứ `analyze` khai và taxonomy đóng
> băng quyết định, không do mô hình đặt tên; `kind` là khoá duy nhất trong mọi ca
> (đo trên cả 9) và guard NÉM khi điều đó thôi đúng. Thêm nhãn chứng nhận thứ
> **16** `SCORING_SURVIVES_MODEL_CHOSEN_WITNESS_NAMES` với một ca stub ĐỔI TÊN
> witness, kèm phép tiêm khôi phục hành vi cũ. Đính chính OFFLINE, 0 lượt gọi,
> artifact thô **nguyên byte**, băm ba file được đính chính ghi vào
> `SCORING_CORRECTION.json`. `SILENT_WRONG_ANSWER 6 → 0`, `EXACT_ANSWER 1 → 7`.

⚠️ **`n1` không chạm được mã đã pre-register, và điều đó ĐÚNG.** Mô hình bịa ba
điểm để xấp xỉ khối tròn xoay và bị chặn bằng `UNANCHORED_DERIVED_ASSUMPTION` —
mã thuộc `KHONG_DUOC_SUA`, nên `stage_semantic_program` trả `(None, …)` TRƯỚC
khi tới `verify_and_compile`, và không có `error_code` nào để so. Đó là giới hạn
của phép pre-registration, không phải của hệ. **Không** hồi tố sửa
`expected_codes` cho khớp — sửa kỳ vọng sau khi thấy kết quả là xoá đúng thứ nó
tồn tại để giữ.

⚠️ **Token thực 97 869 so với dự kiến 74 763 (+31 %)**: `thoughts_tokens` chiếm
34 % tổng, và trung vị lịch sử dẫn ngân sách không tách riêng phần ấy. Trần
196 000 vẫn thừa 50 % — ngân sách đúng ở chỗ nó phải đúng: một cái phanh, không
phải một dự báo.

⚠️ Runner đổi SAU lượt đo (bản vá ánh xạ tên witness), nên khoá tự rơi về
`PENDING` kèm băm trước/sau — guard làm đúng việc. Đã chứng nhận lại (16/16) rồi
khoá lại; `IDENTITY_LOCK.LUOT_DA_CHAY` giữ `RUNNER_HASH_AT_RUN = 19c4c311…` để
không ai phải suy từ thời điểm commit.

```
PRODUCT_PROMOTION_ELIGIBLE = NO · STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
```

Cả hai là kết luận **đã biết trước lượt đo** (một ca mỗi họ, chạy một lần), không
suy từ kết quả.

Cổng: alignment **62 pass** · matrix **49 pass** · `pytest` **4772 pass + 1 skip,
0 đỏ** (cây sạch) · certifier **16/16**, 0 lượt gọi thật · `freeze --verify` exit
0 (92 file, `d72db7c3…`) · `cache identity` exit 0 @ v94 · sản phẩm **INHERITED**
(0 byte mã sản phẩm đổi).

```
RECOMMENDED_NEXT_ACTION = THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING
```

Báo cáo: `docs/THESIS_FINAL_ACCEPTANCE_EXECUTION.md`; artifact 26 file ở
`docs/evaluation/geometry/thesis-final-acceptance/thesis-final-20260908T160224Z/`.

### 1a-unvicies. `THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT` (2026-09-08)

**Runner của lượt đo cuối đã tồn tại, đã chứng nhận, và băm đã khoá.
`LOCK_STATE = LOCKED_READY_FOR_FINAL_EXECUTION`. Lượt đo vẫn CHƯA chạy.**

```
APPLICATION_LLM_CALLS = 0 · REAL_PROVIDER_CALLS = 0
FINAL_ACCEPTANCE_RUNNER_READY = YES · 15/15 nhãn chứng nhận PASS
MAX_LOGICAL_CALLS 39 → 25 · HARD_TOKEN_BUDGET 294 000 → 196 000
CANDIDATE ddeb0518… → d72db7c3… · CACHE_VERSION 94 → 94 (KHÔNG bump, có đo)
PRODUCT_CODE_CHANGED = YES (1 file) · MODEL_FACING_CONTRACT_CHANGED = NO
stub: 7/7 dương servable · 2/2 âm fail-closed · 19 lượt gọi · silent 0
```

Năm khoảng trống của wave trước đóng bằng một **entrypoint riêng**
(`run_thesis_final_acceptance.py`); runner V3 **không được vá**, nó giữ nguyên
cho tuyến V3.

**Chặng B TIẾP TỤC, không chạy lại** — nhận hợp đồng đã đóng băng + raw
candidate hỏng + chẩn đoán từ chặng A rồi tiêu đúng MỘT lượt sửa. Nhờ vậy trần
chặng B tụt `21 → 7`. `base` được **CHỤP** ở lượt tổng hợp đầu (lượt đầu
`prompt = base` nguyên văn) chứ không dựng lại; chuỗi chẩn đoán thì phải dựng
lại, và đó là chỗ DUY NHẤT có thể lệch — khoá bằng **phép so BYTE** với prompt
mà `stage_semantic_program` THẬT phát ra ở lượt sửa, trên cả ba nhánh
(`schema` · `ir_static` · `grounding`).

> ### ⚠️ LƯỢT STUB PHƠI RA MỘT LỖI SẢN PHẨM THẬT
>
> `plane_equation.doc_phuong_trinh` chỉ đọc được dấu trừ **ASCII**. `−`
> (U+2212 — dấu trừ ĐÚNG của toán học, thứ SGK và một mô hình chép đề đã soạn
> đẹp sẽ phát ra), `–`, `—` đều trả `None`. Và hậu quả **không phải** "không
> đọc được": phép nở span dừng giữa phương trình, biến `2x − z + 12 = 0` thành
> `z + 12 = 0`, rồi báo bất biến nguồn VI PHẠM trên một chương trình gold
> **hoàn toàn đúng** — kèm lời từ chối nói về một mặt phẳng đề không hề viết.
> Đúng ca *"một mặt phẳng SAI được đem đi đối chiếu"* mà docstring `_ung_vien`
> đã ghi là ca tệ hơn.
>
> ⚠️ `p6` đỏ, `p7` **cùng lỗi nhưng VẪN xanh** vì phép cắt cụt của nó tình cờ
> cho một phương trình tương đương. Một lỗi bật ở một trong hai ca cùng hình
> dạng là lỗi tệ hơn một lỗi bật ở cả hai.
>
> Sửa (theo quyết định của user, không tự quyết): `chuan_hoa_dau_tru`, ánh xạ
> **1:1** vì `_ung_vien` trả lát cắt của chuỗi gốc. `U+00AD` cố ý KHÔNG map.
> `point_coordinate.py` VỐN đã xử lý `−` từ trước ⇒ `plane_equation.py` là
> **ngoại lệ**, không phải quy ước của kho.

⚠️ **KHÔNG bump `CACHE_VERSION` — kiểm bằng một row cache thật.** Dựng bản
trước-vá rồi so từng ca: `SERVED_TO_REJECTED = 0` · `ANSWER_CHANGED = 0` ·
`REJECTED_TO_SERVED = 1`. `main.py:865`/`:900` chỉ ghi cache khi
`envelope.status == "ok"`, nên một đề TỪNG BỊ TỪ CHỐI chưa bao giờ tạo row nào
— không có row cũ để trở thành sai. Bằng chứng: `CACHE_IMPACT.json`.

⚠️ **Nhãn chứng nhận thứ 15 sinh ra từ một lỗi khác.** Gold preflight của wave
trước dùng THẲNG `request_contract_gold` với `provenance="confirmed"` viết tay,
tức **chưa bao giờ đi qua** `build_request_contract` — biên duy nhất quyết định
hợp đồng thật sự trông thế nào. `GOLD_CONTRACT_REACHABLE` nay đòi mọi hợp đồng
gold tái tạo được qua biên thật mà không sinh `unproven_values`.

⚠️ **Một lỗ tự gây, đã bịt**: `dung_identity_lock` đặt `RUNNER_HASH = None`,
nên một lượt sinh lại artifact SAU khi khoá sẽ **mở khoá im lặng**. Nay khoá cũ
được mang sang và chỉ mất **có tiếng** khi runner thật sự đổi.

Vòng danh tính cắt bằng **tập file**: `RUNNER_HASH` băm đúng file entrypoint;
mọi artifact `.json` — kể cả `IDENTITY_LOCK.json` — nằm NGOÀI. Khoá hai lần cho
cùng một băm, và certifier chạy lại SAU khi khoá vẫn PASS.

Cổng: alignment **52 pass** (19 phép tiêm, 5 cái bắt lỗi THẬT khi dựng) ·
matrix **49 pass** · `pytest` **4765 pass + 1 skip, 0 đỏ** (cây sạch) ·
`freeze --verify` exit 0 (92 file, `d72db7c3…`) · `cache identity` exit 0 @ v94 ·
replay 5/5 · crash 6/6 ném 0 · frontend + build **INHERITED**.

```
RECOMMENDED_NEXT_ACTION = THESIS_FINAL_ACCEPTANCE_EXECUTION
```

Trần cứng **25 lượt gọi · 100 lần thử vật lý · 196 000 token**. Chạy lại
`--certify` trước lượt live để chứng minh mọi băm còn khớp. **Không sửa
corpus/policy/lock để kết quả đẹp hơn.**
Báo cáo: `docs/THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT.md`.

### 1a-vicies. `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION` (2026-09-08)

**Chuyển từ XÂY TÍNH NĂNG sang ĐÁNH GIÁ. Kế hoạch đo cuối đã khoá; lượt đo chưa
chạy và không chạy trong wave này.**

```
THESIS_ACCEPTANCE_MATRIX = PASS · APPLICATION_LLM_CALLS = 0
FEATURE_DEVELOPMENT = CLOSED · FEATURE_SCOPE_COMPLETE = YES
PRODUCT_CODE_CHANGED = NO · CACHE_VERSION 94 → 94 · candidate ddeb0518… KHÔNG đổi
7 ca dương + 2 ca âm · set-cover phủ 10/10 họ trong phạm vi
GOLD_PREFLIGHT 7/7 servable · 7/7 exact · 7/7 oracle · 7/7 scene3d · weak 0
ORACLE_SELF_CHECK 12/12 · SCORER 15/15 lớp có fixture (5 REAL_PATH)
EXPECTED_LOGICAL_CALLS 18 · MAX 39 · HARD_TOKEN_BUDGET 294 000
EVALUATION_CLASS = FROZEN_FINAL_DEVELOPMENT_BENCHMARK · HELD_OUT_CLAIM = NO
FINAL_ACCEPTANCE_RUNNER_READY = NO (5 khoảng trống)
```

Bảy ca dương là một lời giải **set-cover**, và test kiểm **cả hai chiều**: thiếu
một họ là đỏ, mà **bỏ một ca đi mà không mất họ nào cũng đỏ** — một ca không phủ
thêm gì là một lượt gọi model tiêu vô ích.

⚠️ **`KHOP_CANDIDATE_HIEN_TAI = 0`.** Quét 113 artifact có danh tính trong
`docs/evaluation/`: **không cái nào** được sinh trên candidate `ddeb0518…`. Mọi
con số live trong kho thuộc về một bản hệ CŨ. Không phải khiếm khuyết —
candidate vừa đổi cùng ngày ở `OBLIQUE_CONE_SECTION_FOUNDATION` — nhưng đó là lý
do lượt cuối **phải** chạy, và là câu phải viết cạnh mọi số dẫn lại. Thêm: 90 ca
trong số ấy **không ghi candidate nào** (có trước cơ chế đóng băng).

⚠️ **Ba đính chính, cả ba do phép đo bác điều tôi đã viết.**

1. **Quy ước hiển thị.** Bản nháp ghi đáp số elip là `25√5π`; sản phẩm in
   `25π√5`. Bảy ca "sai" trong khi không con số nào lệch một li. Nay `display`
   ghi đúng quy ước `radical.display()`, và `oracle_value` đứng cạnh để một lần
   đổi quy ước không phá được phép kiểm SỐ.
2. **Oracle lấy mẫu bị gán giá trị công thức.** `p6`/`p7` khai
   `oracle_method: SAMPLED` nhưng `oracle_value` là số dẫn từ **công thức bán
   trục** — cùng công thức kernel dùng. Hậu quả đo được: siết dung sai từ `1e-8`
   xuống `1e-12` vẫn XANH, tức tính độc lập chỉ có trên nhãn. Đã sửa sang số
   **lấy mẫu** (200 000 điểm trên giao tuyến + shoelace 3D); `test_H4` ghim rằng
   siết dung sai phải làm nó ĐỎ.
3. **Guard corpus của V3 là DANH SÁCH CẤM, không phải danh sách cho phép.** Tôi
   khẳng định *"guard V3 phải bác bộ ca khoá luận"*; đo ra **KHÔNG** —
   `kiem_bo_ca_la_pool_v3` chỉ ném khi id trùng corpus V1/V2. Và lý do thật còn
   khác: `main_async` lấy bộ ca **duy nhất** từ `nap_ca_v3()`, hàm ấy vẫn trả về
   13 ca V3 **đã rút**. Nên runner V3 không "từ chối" bộ ca mới — nó **không có
   đường nào để nhận**, và chạy lên sẽ lặng lẽ đo lại một pool đã tiêu.

⚠️ **Hai lớp §10 mà scorer canonical KHÔNG sinh ra được**, ghi ra thay vì để
runner tự phát minh cách đếm: `MODEL_ANALYZE_FAILURE` (analyze hỏng ⇒ không có
contract ⇒ `phan_loai` chưa từng được gọi) và `SYSTEM_SCENE3D_FAILURE`
(`servable` ⇒ `CORRECT_SERVABLE_RESULT`, nhãn không hạ khi cảnh hỏng). Cả hai
thuộc trách nhiệm **runner**.

⚠️ **`SCORER_CONTAINER_NAME_ONLY_HEURISTIC` — giới hạn đã đo.**
`nghia_vu_du_noi_dung_hut_ten` kết luận *"đúng nội dung, hụt TÊN"* khi chương
trình đo đúng lượng trên đúng **kiểu** chủ thể; nó không phân biệt *đúng vật* với
*một vật khác cùng kiểu*. Dò `n2-b` (trả thể tích khối hộp cho câu hỏi *"phần
còn lại sau khi khoan"*) bị xếp `SYSTEM_COVERAGE_FAILURE` — đổ lỗi cho HỆ một ca
mà mô hình trả lời bài khác. Không sai số đo ở ca âm (nhánh ấy không chạy), có
thể sai ở ca dương. Ghi vào giới hạn, KHÔNG sửa scorer trong wave khoá phạm vi.

⚠️ **Ranh giới ca âm thuộc lớp `BOUNDARY_BY_ABSENCE_PROOF`**, không phải
`BOUNDARY_BY_NAMED_ERROR_CODE`: hệ **không có** mã lỗi nào mang tên hai họ ngoài
phạm vi. Nên `NEGATIVE_FAIL_CLOSED` là ngưỡng bắt buộc 2/2, còn
`TARGET_BOUNDARY_DEMONSTRATED` được đo và báo cáo mà **không** đặt thành ngưỡng
— đòi nó là đòi một tín hiệu chưa tồn tại. Đây là bài học sự cố ⑥ của V3 áp theo
chiều đúng.

`RUNNER_HASH = null` **cố ý**: runner lượt cuối chưa tồn tại. Điền tạm băm một
runner khác là khoá danh tính vào thứ không chạy lượt đo — đúng lớp lỗi
`V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER`.

Cổng: wave **49 pass** (nền đỏ 49/49 ở `097f4e6` — bốn module chưa tồn tại; **9
phép tiêm** ở nhóm H, ba trong số đó bắt lỗi thật khi dựng) · `pytest` **4709
pass + 1 skip, 0 đỏ** (cây sạch @ `6965a7a`) · `freeze --verify` exit 0 (92 file, `ddeb0518…`) · `cache
identity --verify` exit 0 @ v94 · frontend + build **INHERITED @ `13b811b`**.

```
RECOMMENDED_NEXT_ACTION = THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT
```

Đóng năm khoảng trống runner, rồi mới tới `THESIS_FINAL_ACCEPTANCE_EXECUTION`
trên **đúng** `IDENTITY_LOCK.json` này. **Không sửa corpus/policy/lock để runner
dễ viết hơn** — chúng khoá TRƯỚC kết quả, và đó là toàn bộ giá trị của chúng.
Báo cáo: `docs/THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION.md`.

### 1a-undevicies. `OBLIQUE_CONE_SECTION_FOUNDATION` (2026-09-08)

**Họ hình cuối cùng trong phạm vi đã có nền. `FEATURE_SCOPE_COMPLETE = YES`.**

```
APPLICATION_LLM_CALLS = 0 · ROOT_CAUSE = KERNEL_BRANCH_MISSING
NEW_MEMORY_TYPES = 0 · NEW_IR_OPERATIONS = 0 · NEW_AUTHORITIES = 0
OBLIQUE_CONE_ELLIPSE_AREA = 12π√6/5   (a² = 32/5 · b² = 27/5)
CONIC_CLASSIFICATION_EXACT = YES · FINITE_CONE_CONTAINMENT = YES
POINT_SCALAR_PARITY = YES · CHECK_AREA/TRACE/SCENE3D = PASS
CACHE_VERSION 93 → 94 · CARD_DELTA = +18 byte, CAPABILITY_SYNC
oblique_cone_section: EXPRESSIBLE_ONLY → FOUNDATION_ONLY
```

Phân xử ba nhánh conic là một **phép so hữu tỉ**: `(n·u)²(r²+h²)` vs
`r²|n|²|u|²`, kiểm chéo bằng dấu của `k`. Hai bán trục `b² = t·d²/K`,
`a² = t·d²·|n|²/K²` cũng hữu tỉ ⇒ `S = π√(a²b²)` ở lại trong `Radical`. Ba
oracle độc lập; oracle số lệch `< 1e-4`.

⚠️ **Chỗ khó thật không phải bán trục mà là TÂM, và tôi dẫn SAI lần đầu.** Với
trụ, tâm elip *là* giao điểm trục × mặt phẳng; với nón thì **không**. Hệ số đầu
tiên tôi dẫn cho tâm lệch **97.8** so với oracle — trong khi `2a` đã đúng ngay
từ đầu, nên **nếu chỉ kiểm diện tích thì lỗi ấy đi lọt hoàn toàn**. Dẫn lại:
`C = T − (q·t·(h/√(u·u))/K)·major_dir` với `major_dir = |n|²u − (n·u)n`. Bài
học ghi lại: *một phép kiểm diện tích không kiểm được vị trí* — `test_20` nay
đòi bốn đầu mút thoả **cả hai** phương trình (mặt phẳng và mặt nón) và nằm
trong đoạn hữu hạn, tức kiểm `center`, hai `dir` và hai bán trục cùng lúc.

⚠️ **Không dùng điểm đỉnh**: ở scalar mode đỉnh nón không hữu tỉ khi `h = √7`.
Công thức đi qua `_ti_le_doc_truc` — thẩm quyền ĐÃ CÓ, và nó từ chối đúng ca
ấy. `NEW_AUTHORITIES = 0` là thật vì lý do này.

⚠️ **Một hồi quy đổi khẳng định, và phép đo bác điều tôi đoán.** Viết lại
`test_12` (ca nón cũ), tôi đoán nó là hyperbol; đo ra là **ELIP** — ngưỡng elip
là `m < cot α`, không phải `m < tan α`. Nó vẫn bị từ chối, nhưng bằng đúng mã
`ERR_ELIP_CAT_DAY` mà bản cũ ghim là *"khác"*: dòng ấy khẳng định một điều SAI
về chính ca nó chọn.

Fail-closed: `CURVED_CONE_SECTION_PARABOLIC` · `..._HYPERBOLIC` (kể cả mặt
phẳng ∥ trục — với NÓN điều đó đúng, khác hẳn trụ) · `CROSSES_CAP` ·
`PLANE_DOES_NOT_CUT`. Chạm đáy được **NHẬN**.

Bump 93 → 94: đúng **một** chuỗi đổi (`description` của trường `solid`), nhưng
nó nằm đồng thời trong thẻ và trong lược đồ ⇒ **hai** băm đổi
(`grammar_card cc105e4f → 6cbba188`, `synthesis_schema 6ccef323 → 08dae8dc`).
`prompts`/`analyze_schema`/`capability` không đổi một byte. Chiều envelope:
**rejected → served** và chỉ chiều ấy.

```
RECOMMENDED_NEXT_ACTION = THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION
```

Mọi họ trong phạm vi đã có foundation; hai họ còn lại `OUT_OF_SCOPE` vì lý do
kiến trúc đã đo. Việc còn lại của khoá luận là **đánh giá** — độ phủ, độ đúng,
tỉ lệ tự sinh thành công, token, giới hạn — **không phải thêm hình**.
Báo cáo: `docs/OBLIQUE_CONE_SECTION_FOUNDATION.md`.

### 1a-duodevicies. `MISSING_FAMILY_ROADMAP_REFRESH` (2026-09-08)

**Bản đồ năng lực lập lại từ MÃ NGUỒN, và nó bác một ghi chú tôi đã tin suốt
hai wave.**

```
APPLICATION_LLM_CALLS = 0 · PRODUCT_CODE_CHANGED = NO
CACHE_VERSION 93 → 93 · candidate 9bb796e9 không đổi
SELECTED_NEXT_FAMILY = oblique_cone_section
NEXT_ACTION = OBLIQUE_CONE_SECTION_FOUNDATION
FEATURE_SCOPE_COMPLETE = NO  (đúng MỘT họ còn lại; sau nó thì YES)
```

Mười hai họ, mười một cột mỗi hàng, **kiểm được bằng máy**:
`docs/evaluation/geometry/missing-family-roadmap-refresh/CAPABILITY_MATRIX.json`
+ `tests/geometry/test_missing_family_roadmap.py` (26 ca, soát **cả hai
chiều** — thứ khai "đã sẵn sàng" phải có mặt, thứ khai "chưa có" phải thật sự
vắng).

```
SUPPORTED              điểm/đường/vectơ/mặt · đa giác & thiết diện · đa diện lồi
DEVELOPMENT_CONFIRMED  đa diện lõm · elip xiên của trụ
FOUNDATION_ONLY        cầu · trụ · nón · thiết diện tròn
EXPRESSIBLE_ONLY       thiết diện xiên của NÓN
OUT_OF_SCOPE           khối tròn xoay tổng quát · khối ghép/bù
```

⚠️ **ĐÍNH CHÍNH một ghi chú registry.** Nó viết *"nón cắt xiên cho elip,
parabol hoặc hyperbol tuỳ độ dốc — ba nhánh chưa phân xử"*. Câu ấy đúng về
**việc chưa làm** và im lặng về **miền số**; tôi đã đọc nó như thể nói cả hai.
Đo lại: `a² = c²t(1+m²)/k²`, `b² = c²t/k` với `t = r²/h²`, `k = 1 − m²t` —
**cả hai hữu tỉ**, nên diện tích `π√(a²b²)` nằm trọn trong `Radical` đã có. Bốn
ca đối chiếu **oracle số độc lập** (400 000 mẫu, shoelace 3D), lệch `~1e-9`. Và
phân xử ba nhánh là một **phép so hữu tỉ**: `(n·u)²(r²+h²)` vs `r²|n|²|u|²`,
kiểm chéo bằng dấu của `k`.

Khoảng trống thật của họ ấy: **một nhánh kernel** + **một chuỗi gợi ý** trong
thẻ. `NEW_MEMORY_TYPES = 0` · `NEW_IR_OPERATIONS = 0` · checker/trace/Scene3D
**đều đã sẵn** (`ellipse3` có trong `BANG_PHEP_DO['area']`, render kind
`ellipse` có ở cả hai đầu).

Hai họ còn lại `OUT_OF_SCOPE` vì lý do **kiến trúc đo được**, không vì *"chưa
ai làm"*: không có thẩm quyền tích phân nào và không có kiểu biểu thức hàm
trong `MemoryType` (quét 45 file); còn boolean cần đúng điều kiện **toàn cục**
mà `kiem_mat_phang_don` đã khai là không kiểm được. ⚠️ Lối tắt *"tổng đại số
các thể tích"* cho **đáp số** đúng mà **hình** sai — đúng lớp lỗi
`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` vừa đóng.

⚠️ Wave **không nâng registry sản phẩm**: ma trận chia họ mịn hơn, nhưng
`nonconvex_polyhedron` và `curved_oblique_section` vẫn `foundation_only`. Hai
câu khác nhau; `test_19` khoá rằng chúng không nói ngược nhau.

```
RECOMMENDED_NEXT_ACTION = OBLIQUE_CONE_SECTION_FOUNDATION
```

Phạm vi nhỏ nhất chứng minh được: thiết diện của **nón hữu hạn** cắt bởi mặt
phẳng **xiên**, khi phép phân xử hữu tỉ cho `ellipse` **và** elip nằm trọn giữa
đỉnh và đáy; hai nhánh `parabol`/`hyperbol` **fail-closed** bằng hai mã riêng.
`EXPECTED_MODEL_CALLS_FOR_FOUNDATION = 0`. Sau họ này, next action đã xác định
trước: `THESIS_ACCEPTANCE_MATRIX_AND_DOCUMENTATION`.
Báo cáo: `docs/MISSING_FAMILY_ROADMAP_REFRESH.md`.

### 1a-septdecies. `POINT_COORDINATE_SOURCE_INVARIANT` (2026-09-08)

**`grounded` trên toạ độ điểm nay có nghĩa là *"con số khớp dữ kiện"*, không
còn là *"có nêu tên một fact"*.**

```
APPLICATION_LLM_CALLS = 0 · NEW_IR_OPERATIONS = 0 · NEW_MEMORY_TYPES = 0
ROOT_CAUSE = SOURCE_FACT_CONTENT_UNCHECKED
SELECTED_BRANCH = A (hợp đồng SourceInvariant hiện tại đã đủ)
NEW_SOURCE_INVARIANT_KINDS = 2   point_coordinate · *_unresolved
CACHE_VERSION 92 → 93 · MODEL_FACING_CONTRACT_CHANGED = NO
NONCONVEX_POLYHEDRON_SEQUENCE = CLOSED_AT_DEVELOPMENT_FOUNDATION
```

⚠️ **Phép đo BÁC giả thuyết mà wave trước để lại.** Giả thuyết: *"analyze
không trích toạ độ nên grounding không có gì đối chiếu"*. Đo một biến: chạy
`B(6,0,0) → B(99,7,0)` với hợp đồng **kể chuyện** và với hợp đồng **CÓ toạ
độ** — kết quả **y hệt**, cả hai `served` với `V = 540`. Lỗ ở **grounding**:
`source_fact_id` kiểm **SỰ TỒN TẠI**, không kiểm **SỰ KHỚP**. Bản vá vì thế
đặt ở **bất biến nguồn**, không ở grounding.

Bảy ca trước vá đều `served` với số sai (`540` · `63` · `540` · `540`); sau vá
cả năm ca sai dừng ở `source_invariant`, hai ca đúng vẫn `served · 45`.

⚠️ **Bộ đo của chính wave này vấp đúng cái bẫy kho hay gọi tên.** Replay dựng
`RequestContract` **thẳng** nên không qua biên đóng băng, không thấy bất biến
nào, và báo *"bản vá không đổi gì"* cho một bản vá đúng. Chữa **không** bằng
cách chép danh sách bộ phát sang bộ đo mà bằng cách tách
`analyze_contract.gan_bat_bien_nguon` — **một thẩm quyền**, cả sản phẩm lẫn bộ
đo cùng gọi. Cột "trước" cũng sinh lại bằng chính bộ đo ấy (`--bo-bat-bien`):
hai cột, một nhạc cụ, một biến.

⚠️ **Hai khẳng định cũ ĐỔI, cả hai có lý do đo được.** (a) `test_J` từng ghim
*"không có bản đồ C₁a ⇒ `not_checkable`"* — đó là mô tả một **giới hạn**, và
giới hạn ấy làm cổng im lặng đúng lúc cần nói (`O'(0,0,20)` vs biến `Oprime`).
`_diem` nay có nấc ③ dùng `source_entities.chuan_hoa_ten` — thẩm quyền ĐÃ CÓ,
không phải lưới thứ chín — và **DUY NHẤT-hoặc-KHÔNG**, không bao giờ chọn cái
đầu tiên. (b) `test_21b` của wave trước, một test **xanh mô tả lỗ**, nay đảo
chiều thành khẳng định hành vi đúng.

**Bảy phép tiêm**, cả bảy lật đúng ô nó nhắm. ⚠️ Phép tiêm ② lúc đầu vá
`PC.KIND` — **vô hiệu**, vì bộ phát và checker cùng đọc hằng ấy nên nó đổi cả
hai vế và tự triệt tiêu; phải vá đúng MỘT vế, ở `route` (nơi import ở mức
module), không ở `postconditions`.

**Cache bump 92 → 93**, chiều `served (số SAI) → rejected`, chứng minh bằng
**ROW THẬT** (`PROOF_CACHE_ROW.json`): row `status="ok"` mang `540` vẫn **HIT**
dưới v92 và **MISS** sau bump. Sáu băm model-facing đứng yên từng byte — lần
thứ **hai liên tiếp** bump vì *phán quyết* đổi chứ không vì *đầu vào của mô
hình* đổi. Cổng thứ năm lại xuất hiện: ba test ghim danh tính lượt đo cũ, sửa
**test** và giữ artifact.

⚠️ **Giới hạn khai bằng test đang XANH** (`test_90`): chưa đọc được thập phân
dấu **phẩy** (cố ý — `A(1,5, 2, 3)` đọc được hai cách) · tên đứng sau bộ ba ·
`x_A = 1, y_A = 2` · toạ độ 2D · toạ độ **vô tỉ**. `test_91` khoá rằng giới hạn
ấy không bao giờ thành lời kết tội oan.

```
RECOMMENDED_NEXT_ACTION = MISSING_FAMILY_ROADMAP_REFRESH
```

Nền tất định của khối lõm đã đóng ở mức development, và lỗ kiểm chứng nặng
nhất phát hiện được cũng đã bịt. Việc kế tiếp là rà lại bản đồ **họ hình còn
thiếu** thay vì đi sâu thêm vào họ vừa đóng.
Báo cáo: `docs/POINT_COORDINATE_SOURCE_INVARIANT.md`.

### 1a-sedecies. `NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY` (2026-09-08)

**Mô hình TỰ viết được bảng mặt của khối chóp đáy lõm — ngay lượt đầu, 0 lượt
sửa.** Và phép đo tìm ra một **lỗ nặng hơn ở chỗ khác**.

```
MEASUREMENT_CLASS = DEVELOPMENT_DIAGNOSTIC · HELD_OUT_CLAIM = NO
EVALUATOR_INDEPENDENCE = OPERATOR_WAIVED
APPLICATION_LLM_CALLS = 2/3 · PHYSICAL 2 · retry 0 · 11 388/25 000 token
FIRST_ATTEMPT_DISCOVERABLE = YES   MODEL_DISCOVERABLE_ON_THIS_PROBE = YES
FACE_TABLE_VALID = PASS · EXACT_VOLUME = 45 · SCENE3D_CONCAVITY_PRESERVED = YES
NONCONVEX_POLYHEDRON_SEQUENCE = CLOSED_AT_DEVELOPMENT_LEVEL
CAPABILITY = foundation_only · PRODUCT_PROMOTION_ELIGIBLE = NO
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
```

Đề MỚI: `S.ABCDE`, đáy `z = 0`, `A(0,0,0) B(6,0,0) C(6,4,0) D(3,1,0) E(0,4,0)`,
đỉnh `S(2,2,9)`. Đề cho **thứ tự đỉnh quanh biên** và **không** cho bảng mặt —
bảng mặt là thứ đang được đo. Oracle `V = 45` từ **bốn** nguồn độc lập.

Mô hình viết đúng một đáy ngũ giác + năm mặt bên, `measure(volume)`, `served`,
Scene3D 8 vật giữ nguyên chỗ lõm. ⚠️ Nó viết theo lối **KHÁC gold** (đáy
`A→B→C→D→E`, mặt bên `[S,X,Y]`, `S` đứng đầu danh sách đỉnh) — nên **bộ chấm
bất biến với cách viết là thứ cứu ô trung tâm của wave**; ghim chính tả thì ô
ấy đã ĐỎ cho một chương trình ĐÚNG.

⚠️ **Phát hiện ngược trực giác ở tiền kiểm**: khai đáy bằng **quạt tam giác**
cho biên KÍN và `V = 45` **ĐÚNG** — nhưng ba tam giác ấy là thứ renderer VẼ, và
`A-C-D` nằm ngoài đáy ⇒ phần lõm bị lấp. Nên `EXACT_VOLUME` ·
`FACE_TABLE_VALID` · `SCENE3D_CONCAVITY_PRESERVED` **không được gộp làm một**.

⚠️ **LỖ MỚI, đo một biến, và nó BÁC giả thuyết đầu tiên của tôi.** Hợp đồng
analyze của lượt live có **ba fact kể chuyện**, không fact nào mang toạ độ, thế
mà chương trình khai đủ sáu điểm và grounding cho qua. Tôi ngờ nguyên nhân là
analyze; chạy lại với hợp đồng GOLD (mỗi điểm một fact **CÓ** toạ độ) thì kết
quả **y hệt**: đổi `B(6,0,0)` → `B(99,7,0)` vẫn `served` với **`V = 540`**,
`unjustified_literals = []`. Vậy lỗ ở **grounding**: `source_fact_id` được kiểm
**SỰ TỒN TẠI**, không kiểm **SỰ KHỚP**. Kho có bất biến nguồn cho
`plane_equation` · `segment_length` · `segment_division` · thang đo — **không
có** cái nào cho **toạ độ điểm đề cho tường minh**. Đổi `D(3,1,0)` → `D(3,3,0)`
cho `V = 63`, đúng con số của bẫy "quạt lấp lõm". `test_21b` khoá lỗ bằng một
test **ĐANG XANH**: xanh nghĩa là lỗ còn.

Wave giữ product bytes nguyên vẹn: `PRODUCT_CODE_CHANGED = NO` ·
`MODEL_FACING_CONTRACT_CHANGED = NO` · `CACHE_VERSION` 92 → **92** · candidate
`6362674e…` không đổi · `PRODUCT_CAPABILITY_CHANGED = NO`.

```
RECOMMENDED_NEXT_ACTION = POINT_COORDINATE_SOURCE_INVARIANT
```

Đóng lỗ §7 bằng đúng khuôn `bat_bien_do_dai`/`bat_bien_mat_phang` đã dựng: một
bất biến nguồn cho **toạ độ điểm đề cho tường minh**, để `grounded` nghĩa là
*"con số khớp dữ kiện"* chứ không phải *"có nêu tên một fact"*. Đây là điều kiện
độc lập thứ hai để `nonconvex_polyhedron` rời `foundation_only`.
Báo cáo: `docs/NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY.md`.

### 1a-quindecies. `NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION` (2026-09-07)

**Hệ không hề từ chối khối lõm — nó PHỤC VỤ khối lõm với một con số SAI.** Wave
mở ra để hỏi một câu về năng lực, và trả lời bằng một phát hiện về tính đúng.

```
APPLICATION_LLM_CALLS = 0 · NEW_IR_OPERATIONS = 0 · NEW_MEMORY_TYPES = 0
SYSTEM_EXPRESSIBLE         = YES          DETERMINISTICALLY_CORRECT = YES
MODEL_DISCOVERABLE         = NOT_MEASURED STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
MODEL_FACING_CONTRACT_CHANGED = NO        CACHE_VERSION 91 → 92
nonconvex_polyhedron: (không có dòng) → foundation_only
```

`volume_polyhedron` cộng `volume_tetrahedron`, tức lấy `abs` cho **từng** tứ
diện. Với khối lồi vô hại; với khối LÕM là lỗi — phần lõm phải đóng góp **âm**.
Chóp đáy ngũ giác lõm `A(0,0,0) B(4,0,0) C(4,4,0) D(2,1,0) E(0,4,0)`, đỉnh
`S(2,½,6)`: **ba oracle độc lập cho 20**, mã cũ cho **28** — và cho `served`
với 28, vì runtime lẫn checker dùng CHUNG một hàm sai. **Một thẩm quyền duy
nhất bảo vệ tính NHẤT QUÁN, không bảo vệ tính ĐÚNG.**

Chữa: tổng có dấu trên mặt biên, `abs` **đúng một lần** ở cuối
(`section.the_tich_da_dien`), cộng **tự định hướng lại** các mặt bằng BFS — nhờ
vậy **hợp đồng khai mặt không đổi một byte**. Năm mã lỗi mới:
`POLYHEDRON_BOUNDARY_OPEN` · `NON_ORIENTABLE` · `DEGENERATE` ·
`FACE_NOT_PLANAR` · `FACE_NOT_SIMPLE`.

Nửa kia — renderer từng dùng **quạt tam giác** ở cả hai nhánh dựng mặt, tức
**lấp mất phần lõm**. Thay bằng `polygon-triangulate.ts` (cắt tai, trả CHỈ SỐ,
không sinh toạ độ). Đo trên buffer thật của `buildObject3D`:
`RENDERED_PROJECTED_AREA = 10` · `NOTCH_REMAINS_EMPTY = YES` ·
`TRIANGLE_OVERLAP_OUTSIDE_FACE = 0`.

Gold đi trọn chuỗi bằng **đúng `construct_solid` đã có**: `servable` · `V = 20`
· `weak_kinds = []` · trace `init → construct_solid(chop) → assign(V)` ·
`V → [chop] → [A,B,C,D,E,S]` · cảnh giữ nguyên ngũ giác lõm 5 đỉnh.

**Bump 92 là lần đầu tiên KHÔNG vì "đầu vào của mô hình đổi"** — sáu băm
model-facing đứng yên từng byte. Lý do nặng hơn: envelope `status="ok"` mang
`V = 28` là có thật (đo ở mức route), và `main.py` cache **cả** `envelope_json`.
Cổng thứ năm ngoài `CLAUDE.md §3`: hai test ghim danh tính lượt đo live cũ —
sửa **test**, giữ nguyên artifact.

⚠️ **Ba đính chính trong chính wave này**, cả ba là tự bác mình: `TIEM_2` (mặt
chứa gốc quạt đóng góp 0 nên hộp hở vẫn ra số đúng) · `TIEM_3` (phép đo BÁC
tuyên bố "bỏ định hướng lại thì khối lồi sai" — phải lật đúng mặt 3) · và
**"đáy tự cắt cho 24" SAI TIỀN ĐỀ**: chu trình `A→B→D→C→E` không tự cắt, nó là
một ngũ giác lõm khác và `24` là đáp số đúng. Bow-tie thật là `A→C→B→D→E`, và
ở đó lỗ là thật (hệ từng phục vụ `V = 4`) — hai mã `FACE_NOT_*` sinh ra từ lần
đo lại ấy.

⚠️ **Phạm vi đã chứng minh, hẹp:** *khối đa diện có biên KÍN, một vỏ, mọi MẶT
phẳng và đơn* — **không** phải "mọi đa diện không lồi". Hai mặt KHÁC NHAU xuyên
qua nhau vẫn ngoài bao đóng v1. `MODEL_DISCOVERABLE` chưa đo vì chỉ thị wave
ghi `APPLICATION_LLM_CALLS = 0`.

```
RECOMMENDED_NEXT_ACTION = NONCONVEX_POLYHEDRON_MODEL_DISCOVERABILITY
```

Hệ đã đúng và trình bày đúng; thứ **chưa ai biết** là mô hình có tự viết nổi
bảng mặt của một đáy lõm từ đề hay không. Đó là điều kiện duy nhất còn thiếu để
`nonconvex_polyhedron` rời `foundation_only` — cùng luật đang treo
ball/cylinder/cone.
Báo cáo: `docs/NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION.md`.

### 1a-quaterdecies. `OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN` (2026-09-07)

**Đường end-to-end của thiết diện elip ĐÃ CHẠY TRỌN.** `served` ngay attempt 0,
**không lượt sửa nào**.

```
FIRST_ATTEMPT_SERVABLE = YES · EVENTUAL_SERVABLE = YES
CURRENT_PIPELINE_E2E = PASS  · EXACT_ANSWER = 16π√5
ELLIPSE_FOUNDATION_SEQUENCE = CLOSED
logical 2/5 · physical 2 · retry 0 · candidate 1 · 7 927/40 000 token
```

**Hai tiền kiểm cùng PASS trước provider.** Gold: point mode và scalar mode
cùng `served · 16π√5`, parity PASS, **sáu** phản ví dụ giữ đúng (kể cả
*grounded named rim point vẫn hợp lệ* — dòng Card mới không cấm lối ấy).
⚠️ **Tiền kiểm BỘ CHẤM là mới ở wave này**, dựng vì lượt trước đã chấm
`PLANE_CONSTRUCTION_CORRECT = FAIL` cho một chương trình dựng mặt phẳng **đúng
từng hệ số**: chạy bộ chấm trên bảy fixture tổng hợp **trước** provider là cách
rẻ nhất để bộ đo không tụt lại sau hệ thêm lần nữa.

**Ứng viên duy nhất, mọi chiều PASS**: `construct_plane_from_equation` với hệ
số `(2,0,−1,10)` · `intersect_plane_curved_ellipse` · `ellipse3` ·
`measure(area, of=E)` · **`DIRECT_RADIUS_USED = True`, `RIM_POINT_USED =
False`** — lần ĐẦU trong cả chuỗi. Scene3D 7 vật · 5 sự kiện; trace kết bằng
`Gán dien_tich_e = 16π√5.`

**Đáp số xác nhận từ HAI nguồn độc lập**: `Radical(he=16, can=5, mu=1)` trong
final memory, và chuỗi `16π√5` trong lời kể trace. ⚠️ Bản đầu của bộ chấm chỉ
tra một nguồn (`FINAL_MEMORY`, nơi chỉ có `repr`) và trả `KHONG DOC DUOC` cho
một đáp số **ĐÚNG** — bộ chấm hỏi sai chỗ, không phải chương trình sai.

**Hiệu quả dòng Card** — lịch sử `direct-radius 0/2`, `rim_point 2/2`; lượt này
`1 / 0 / 0`. `CARD_LINE_ASSOCIATED_WITH_DESIRED_SELECTION = YES`.
⚠️ **`CAUSAL_ATTRIBUTION = LIMITED` không phải rào đón — có BIẾN SỐ THỨ HAI đo
được**: hợp đồng analyze lượt này `PASS` toàn bộ trong khi lượt trước `FAIL`
bốn ô, và trong bốn ô ấy có **phương trình mặt phẳng** cùng **toạ độ hai tâm**.
Một hợp đồng đầy đủ hơn tự nó đã làm bài dễ hơn, nên `n = 1` không tách được
đóng góp của dòng Card. `test_07` khoá chính lời thú nhận ấy và còn **kiểm
lại** rằng lượt trước thật sự `FAIL`.

⚠️ **Một đính chính lan sang wave trước, khai ra chứ không giấu**:
`cham_analyze` cần `nguon="RAW_ANALYZE"`, thiếu nó nó trả `NOT_CAPTURED` cho
MỌI chiều fact. `SCORING.json` của `oblique-ellipse-after-axis-scale-repair`
dính lỗi ấy, đã chấm lại — nay `FAIL` với bốn ô cụ thể, **khớp đúng** báo cáo
wave ấy (báo cáo trích từ `cham` của artifact, không từ `SCORING.json`), nên
**không kết luận nào phải sửa**. Artifact lượt chạy của cả hai wave **nguyên
byte**.

**Danh tính không trôi**: `RUN_IDENTITY_STABLE = YES` · cache 91 → 91 ·
candidate `adbb3514…` không đổi · năm băm model-facing không đổi · Card
`ed9ad641…` (6672 B, manifest ghi đúng thẻ ấy) · runner không đổi.
`PRODUCT_CAPABILITY_CHANGED = NO`.

⚠️ **Đóng cái gì, và KHÔNG đóng cái gì.** Đóng: *"pipeline sản phẩm hiện tại đi
trọn đường trên ca elip xiên này"*. **Không** đóng:
`STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` (một lượt không nói gì về ổn định —
lượt trước cùng đề đã hỏng) · `CURVED_OBLIQUE_SECTION = foundation_only` ·
`PRODUCT_PROMOTION_ELIGIBLE = NO` · **không phải held-out acceptance** (ca này
đã dùng để TÌM lỗi hệ thống suốt sáu wave, nên `DEVELOPMENT_REGRESSION_SIGNAL`
là hạng cao nhất nó mang được) · **không khái quát sang hình khác** (nón xiên
vẫn ngoài bao đóng V1).

```
RECOMMENDED_NEXT_ACTION = NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION
```

Theo §16, Card **đã chốt** cho ca elip: việc kế tiếp thuộc hình học mới hoặc
repair policy, không thuộc thêm hướng dẫn Card. ⚠️ Nợ còn treo, ghi để không
mất: `CURVED_RIM_POINT_REPAIR_ELIGIBILITY` — `DIAGNOSTIC_IDENTIFIES_RADIUS_SLOT
= NO` và `REPAIR_POLICY_DISTINGUISHES_SAFE_SUBCASE = NO` vẫn đúng, sáu tín hiệu
cấu trúc đã đo sẵn; nó không còn chặn ca elip nhưng lớp lỗi ấy sẽ gặp lại ở họ
hình khác.
Báo cáo: `docs/OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN.md`.

### 1a-terdecies. `CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION` (2026-09-07)

**Phân xử, rồi sửa đúng thứ được chứng minh là thiếu.** `APPLICATION_LLM_CALLS
= 0` · `NEW_GEOMETRY_OPERATIONS = 0` · `NEW_MEMORY_TYPES = 0`.

```
SELECTED_BRANCH = A     CARD_CONTRACT_COMPLETE = NO → YES
MISSING_PROPOSITIONS = [P1, P3]
RAW_FAILURES_MATCH = YES · CURVED_RIM_POINT_AFFORDANCE = REPLICATED
MINIMAL_DELTA = 2 trường (−343 B) → served · 16π√5
```

⚠️ **Phát hiện then chốt: thẻ KHÔNG hề cấm điều mô hình đã làm.** Nó tả
`rim_point` là *"một ĐIỂM trên mặt cầu, hoặc trên vành đáy"* — mô tả **HÌNH
HỌC thuần**, mà `(4,0,0)` **thật sự** nằm trên vành đáy bán kính 4. Còn dòng
`Xuất xứ:` phủ đúng **ba** ca điểm (gốc hệ toạ độ · giá trị lấy thẳng từ đề ·
điểm do một QUAN HỆ xác định) — và *"điểm đề KHÔNG hề nhắc tới"* không thuộc ca
nào. Nên theo thẻ, mô hình không sai; luật nó vi phạm sống ở `grounding_gate`,
một tầng thẻ không nói tới.

**Ma trận hợp đồng đo bằng máy** (9 tổ hợp × 3 họ, chạy qua validator): hai cặp
XOR bắt buộc — `{rim_point, radius}` và `{apex_or_top, height}` (cặp sau chỉ
cho trụ/nón). **Bốn mệnh đề**: P2 ✅ (nhưng không đủ, xem trên) · P4 ✅ · **P1
THIẾU** (*đề cho bằng SỐ thì dùng ô đại lượng* — luật CHỌN, không validator nào
encode được) · **P3 THIẾU** (thẻ nói *"thay cho điểm trên mặt"* = THAY THẾ,
nhưng cả hai ô mang `?` nên người đọc suy ra *"đều tuỳ chọn"*, trong khi
validator đòi **đúng một, bắt buộc**).

**Hai raw candidate của hai lượt live ĐỘC LẬP khớp TOÀN BỘ chín điều kiện** —
`radius` vắng · `rim_point` có · điểm không được đề đặt tên · không
`source_fact_id` · không dùng ở đâu khác · trục đã xác định · đề cho bán kính
bằng số · direct-radius hợp lệ cho họ ấy. Lời khai của chính mô hình nói thẳng
lý do: *"Chọn một điểm trên vành đáy dưới để xác định bán kính, tại (4,0,0) vì
bán kính đáy bằng 4."* ⇒ `REPLICATED`.

**Nhánh A**: thêm **một dòng** nói hai mệnh đề thiếu. Thẻ hình học 6386 → 6672
(**+286 B**); thẻ ĐẦY ĐỦ **không đổi**. Đây là **dòng văn xuôi viết tay THỨ
HAI** của thẻ, cùng bậc ngoại lệ với `_DONG_XUAT_XU` — và nó trả giá bằng bằng
chứng: hai lượt độc lập, cùng hình dạng, bản sửa nhỏ nhất **hai trường**
(`−343 B`) đi thẳng tới `served` với `16π√5`.

⚠️ **Parity thì VẪN dẫn xuất**: test dò **TẬP CHẤP NHẬN** của validator (2⁴
phép thử mỗi họ) rồi kết luận `{a,b}` là XOR ⇔ mọi tổ hợp được nhận chứa đúng
một trong hai. Thêm cặp XOR thứ ba mà quên thẻ ⇒ ĐỎ. ⚠️ **Phép dò phải sửa một
lần**: bản đầu dựng nền bằng *"hai ô còn lại"* — mà hai ô ấy chính là cặp XOR
kia — nên nền luôn bất hợp lệ và phép dò trả **RỖNG**; một `test_01` chạy trên
tập rỗng thì xanh mà không khẳng định gì. `test_02` neo phép dò vào hai cặp đọc
tay từ `contract.py`, và nó bắt đúng ca xanh-giả ấy.

⚠️ **Đính chính bộ đo thứ hai**: bản đầu của replay chấm minimal delta bằng
`REQUEST_CONTRACT_GOLD` và trả `requested_operation_uncovered` cho một chương
trình **hoàn toàn đúng** — hợp đồng live đặt witness `dien_tich_e`, gold đặt
`dien_tich_E`. Chấm bằng gold là chấm ứng viên bằng một **đề khác**, đúng bài
học đã ghi ở `replay_plane_from_equation.py`.

**Diagnostic và policy đo được, KHÔNG sửa** (Nhánh B/C chưa tới lượt):
`DIAGNOSTIC_IDENTIFIES_RADIUS_SLOT = NO` · `REPAIR_POLICY_DISTINGUISHES_SAFE_
SUBCASE = NO`. ⚠️ Thông điệp còn **chỉ SAI đường** — nó bảo *"phải được DỰNG"*,
nhưng với ca này không phép dựng nào sinh ra một điểm vành hữu tỉ, đúng lý do ô
`radius` ra đời (định lý ba bình phương hữu tỉ). `test_14`/`test_15` khoá hai ô
ấy để một wave sau sửa thì phải cập nhật kết luận.

**Identity**: ĐÚNG MỘT băm model-facing đổi — `grammar_card` 2cc55280 →
cc105e4f. ⚠️ **`capability` KHÔNG đổi**, và đó là khẳng định đáng ghi: wave
không đụng `_CHU_KY`/`_KIEU_DUNG`/`_TOAN_HANG_LENH` — **không thêm phép, không
thêm kiểu, không đổi luật hợp lệ**, chỉ **NÓI RA** một luật đã có. `CACHE_
VERSION` 90 → 91 (cache giữ CẢ envelope ⇒ đề đã phân tích trả lại chương trình
sinh bởi thẻ cũ; không envelope `ok` nào hoá sai vì luật hợp lệ không đổi).
Candidate `27f5c076…` → **`adbb3514…`**.

```
RECOMMENDED_NEXT_ACTION = OBLIQUE_ELLIPSE_E2E_ONE_FINAL_RERUN
```

Đúng **một** lượt, trần 5 logical calls. Nếu `served` ⇒ đóng
`ELLIPSE_FOUNDATION_SEQUENCE`, chuyển sang
`NONCONVEX_POLYHEDRON_VOLUME_FOUNDATION`. Nếu vẫn `rim_point` ⇒ giả thuyết
*"thẻ chưa nói rõ"* **bị bác bằng đo**, và Nhánh B/C lên lịch với sáu tín hiệu
cấu trúc đã đo sẵn. ⚠️ Hiệu quả của dòng thẻ với mô hình giữ **`NOT_MEASURED`**
— wave này sửa tính ĐẦY ĐỦ của hợp đồng, không đo hành vi.
Báo cáo: `docs/CURVED_RADIUS_SLOT_AFFORDANCE_ADJUDICATION.md`.

### 1a-duodecies. `OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR` (2026-09-07)

**Lượt live chạy được, và chặn ở đúng MỘT chỗ.**

```
GOLD_PREFLIGHT = PASS        FIRST_ATTEMPT_SERVABLE = NO
CURRENT_PIPELINE_E2E = FAIL  EVENTUAL_SERVABLE = NO
BLOCKER = CYLINDER_RADIUS_OR_RIM
CURVED_RIM_POINT_AFFORDANCE = REPLICATED
logical 2/5 · physical 2 · retry 0 · candidate 1 · 8 740/40 000 token
```

Tiền kiểm §4 **PASS toàn bộ** trước provider — point mode và scalar mode
(đường TRUNG THỰC `h = measure(distance, O, O′)`) cùng `served · 16π√5`, parity
PASS, năm phản ví dụ giữ đúng. Ô `DIRECT_RADIUS_ELLIPSE_PATH = VALID` là điều
kiện để §10 đọc được — lượt trước phải dừng vì chính ô ấy `FAIL`.

**Ứng viên duy nhất đúng 9/10 chiều**: `construct_plane_from_equation` với hệ
số `(2, 0, −1, 10)` **ngay lượt đầu** · `intersect_plane_curved_ellipse` ·
`ellipse3` · `measure(area, of=E)` đúng chủ thể · `anchor` + `apex_or_top` đủ
trục. Hỏng đúng một chỗ: thêm `rim_point` bịa `(4,0,0)` khai bằng
`model_assumption`, grounding bác.

⚠️ **Hình dạng lần này sắc hơn lần trước.** Trục **đã hoàn toàn xác định** bằng
hai điểm CÓ TÊN; `rim_point` được thêm **chỉ để mã hoá bán kính 4**, và mô hình
nói thẳng điều ấy: *"Chọn một điểm trên vành đáy dưới để xác định bán kính, tại
(4,0,0) vì bán kính đáy bằng 4."* Tức nó **dùng một ĐIỂM để chở một ĐỘ DÀI**,
trong khi ô `radius` tồn tại và thẻ có in ra. Affordance của **cách sinh chương
trình**, không phải kernel gap — tiền kiểm đã chứng minh cả hai đường vô hướng
hợp lệ.

⚠️ **`REPAIR_CALLS = 0` dù ngân sách cho 3**, và đó là chính sách chứ không
phải hết ngân sách: `UNANCHORED_DERIVED_ASSUMPTION` nằm trong `KHONG_DUOC_SUA`
(*"gửi đi sửa là trả tiền cho một lượt giấu khéo hơn"*). Ghi một quan sát về
**phạm vi** chính sách ấy, `OBSERVATION`, `n = 1`: lập luận gốc viết cho ca
*giấu ĐÁP SỐ vào toạ độ*, còn ở đây `P_rim` mã hoá một **dữ kiện đề CÓ NÊU**.
Hai ca cùng mã lỗi, khác bệnh. Chưa đủ để nới một cổng đang gác đúng.

⚠️ **Một lỗ BỘ ĐO tìm được và sửa trong wave.** Artifact ghi
`PLANE_CONSTRUCTION_CORRECT = FAIL` cho một chương trình dựng mặt phẳng **đúng
từng hệ số** — bộ chấm chỉ biết `construct_plane` qua ba điểm, tức **tụt lại
sau hệ đúng một wave**. Đúng lớp *"bộ đo không nằm trên đường chạy thật"* đã trả
giá ba lần. Bộ chấm nay nhận cả hai lối và so hệ số theo **tỉ lệ chính xác**;
artifact lượt chạy **giữ nguyên từng byte**, kết quả đúng ở `SCORING.json` kèm
`sha256` nguồn. `test_09` khoá mối nối: cùng `raw_sha256`, hai bản chấm.

⚠️ **Analyze yếu hơn lượt trước** — `ANALYZE_CONTRACT = FAIL`: bốn ô
`NOT_CAPTURED` (fact mang `["O"]`, `["(α)"]` — mất toạ độ và mất phương trình).
Cùng đề, cùng prompt, cùng schema ⇒ **biến động giữa hai lượt**, `OBSERVATION`,
`n = 1` mỗi bên. Nó **không** chặn gì: mô hình đọc thẳng đề nên vẫn viết đúng
hệ số, và bất biến `plane_equation` do SERVER phát từ `problem_text` — đúng lý
do nó được thiết kế đọc câu văn của đề.

**Danh tính ổn định**: `RUN_IDENTITY_STABLE = YES` · cache 90 → 90 · candidate
`27f5c076…` không đổi · sáu băm model-facing không đổi · `PRODUCT_CAPABILITY_
CHANGED = NO`. Đúng một băm đổi và nó CỐ Ý: `scorer` `6f7d0251…` →
`23b76967…`, sửa **sau** lượt chạy. Runner **không** đổi — `690bcdd2…` (manifest,
`read_text`/LF) và `8003dc46…` (`read_bytes`/CRLF) là hai quy ước băm của **cùng
một file**.

⚠️ **`ELLIPSE_FOUNDATION_SEQUENCE` KHÔNG đóng** —
`CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` giữ `NOT_MEASURED`, điều kiện là
*eventual served*.

```
RECOMMENDED_NEXT_ACTION = CURVED_RADIUS_SLOT_AFFORDANCE
```

Hai giả thuyết model-facing **cần phân biệt**, và raw artifact chứng minh cả
hai đứng được ⇒ đây là ca §15 cho phép mở A/B: ① thẻ chưa nói *"đề cho bán kính
bằng SỐ thì dùng `radius`"*; ② mô hình mặc định nghĩ bằng ĐIỂM. ⚠️ Làm phép rẻ
hơn TRƯỚC, đúng lệ `CURVED_SECTION_RADIUS_PATH_ADJUDICATION`: đọc thẻ hiện hành
và hỏi *"một người đọc thẻ này có suy ra được luật ấy không"* — suy ra được thì
① bị bác mà không tốn lượt nào.
Báo cáo: `docs/OBLIQUE_ELLIPSE_E2E_AFTER_AXIS_SCALE_REPAIR.md`.

### 1a-undecies. `CURVED_SCALAR_AXIS_SCALE_REPAIR` (2026-09-07)

**Một hình trụ, hai cách khai, MỘT hình học.** `APPLICATION_LLM_CALLS = 0`.

```
CURVED_SCALAR_AXIS_SCALE_REPAIR = PASS
DIRECT_RADIUS_ELLIPSE_PATH      = VALID
POINT_SCALAR_PARITY             = PASS (4 ca parity + 8 ca biên + bất biến tỉ lệ)
```

`ROOT_CAUSE`: `tren = 1 − L` là khoảng cách tới đáy trên theo **TỈ LỆ**, chỉ
đúng khi `|u| = h`. `huong_truc` trả vectơ ĐƠN VỊ ở nhánh vô hướng, nên `L` là
khoảng cách TUYỆT ĐỐI và `1 − L` mất nghĩa (`L = 10` ⇒ `−9`) — mọi hình trụ
khai bằng `(bán kính, chiều cao)` bị `CURVED_ELLIPSE_CROSSES_CAP` **oan**.

⚠️ **Phân tích đơn vị mới là thứ quyết định bản vá, không phải ca chuẩn.** Đo
ba vế của cap check: `h_half_sq` **64 ↔ 64** · `duoi_sq` **100 ↔ 100** — cả hai
đã ở **ĐỘ DÀI²** và BẤT BIẾN THANG; chỉ `tren_sq` lệch **100 ↔ 81**. Hai trong
ba vế đã đúng đơn vị, nên đơn vị chuẩn của cả phép kiểm là ĐỘ DÀI² — **cùng đơn
vị đường ĐƯỜNG TRÒN đã chọn** (`_giao_tron_xoay` so `d2` với `height_sq`).

`_con_cho_toi_day_tren` hỏi `h − duoi ≥ h_half` bằng **số hữu tỉ thuần** (bình
phương hai lần: `A ≥ 0 ∧ A² ≥ 4·duoi_sq·h_half_sq`), nên nó **không cần biết
`h` là số nào**.

⚠️ **KHÔNG dùng `_ti_le_truc` như brief gợi ý, và lý do đo được**: nó đổi sang
thang tỉ lệ, và để làm thế nó cần `h` **hữu tỉ** — chính nó từ chối có mã khi
`h` vô tỉ. Nhưng hình trụ không cần `h` (bán kính hằng dọc trục), nên `h² = 300`
hiện **vẫn cắt được chính xác**. Dùng nó sẽ **thu hẹp một năng lực đang chạy**
để chữa một lỗi thang. Giữ ý định của brief (*"một cap check chỉ dùng một hệ
đơn vị"*), chọn hệ đơn vị mã hiện hành đã dùng. `test_06` khoá bất biến ấy.

**Bản vá là TỔNG QUÁT HOÁ, không phải nhánh riêng**: khi `|u| = h` thì
`(h−duoi)² = (1−L)²·(u·u)`, đúng `tren_sq` cũ ⇒ `POINT_MODE_REGRESSION = KHÔNG`.

**Hội tụ toán hạng `height`** — một dòng thêm vào `_TOAN_HANG_LENH` sửa **BỐN**
consumer (`ir_static` · `hoisting.O_TEN` · thẻ văn phạm · `coverage_gate.
_phu_thuoc`, ba cái sau đều DẪN XUẤT); chỉ `_NGUON_CUA_PHEP_DUNG` (viết tay có
chủ đích) sửa riêng. Trước đó `height: <tên point3>` **lọt** thẩm định tĩnh rồi
vỡ ở `execution` — mà lỗi runtime KHÔNG được gửi ngược cho vòng sửa.

Thẻ **6302 → 6386 B (+84)**, **THUẦN đồng bộ schema–thẻ**: mô tả đã nằm ở
`contract.py` từ 2026-09-04, thẻ không in nó chỉ vì `O_TEN` thiếu ô. Card C và
hai affordance ratio/provenance **nguyên văn**.

**Replay §7**: point mode và scalar mode trung thực (`h = measure(distance, O,
O′)`) **cùng** `served` · `16π√5` · `nguồn passed=1` · trace + Scene3D đầy đủ.
Đường scalar trước bản vá chết ở `execution`. Ca `height = 20` khai thẳng thiếu
nguồn **giữ nguyên** verdict grounding — fixture ấy chứng minh grounding còn
chặt, KHÔNG chứng minh kernel lỗi.

**Bảo toàn**: `plane_equation` vẫn bác `2x − z + 11 = 0` · điểm vành tự tạo vẫn
chịu grounding · circle3 parity · nón/cầu giữ verdict. **5 phép tiêm.**

**`CACHE_VERSION` 89 → 90.** Quyết định bằng HAI bằng chứng: chiều envelope =
**rejected → served** (không có chiều ngược lại, nên không envelope `ok` nào
hoá sai) và **model-facing đổi** (`grammar_card` 285292fe→2cc55280 ·
`capability` 4b1e2f80→72edf39f). ⚠️ **`synthesis_schema` KHÔNG đổi** — lược đồ
Pydantic vốn đã có ô `height`; thứ đổi là những gì hệ KIỂM và những gì mô hình
ĐỌC THẤY về ô ấy. Candidate `422a9e7b…` → **`27f5c076…`**.

**§10 — bốn cổng gap của wave trước đã chuyển thành khẳng định hành vi ĐÚNG**,
giữ nguyên chú thích lịch sử: `test_10_pv7b` (khoá lỗi → parity) · `test_12`
(*"đóng hoàn toàn"* → parity, mạnh hơn vì `h` nhỏ thì **cả hai cùng từ chối**)
· `test_13` (tiền đề bị bác → tiền đề nay ĐỨNG) · `test_16` (bất đối xứng thẻ
→ đủ kiểu + vai trò).

`PRODUCT_CAPABILITY_CHANGED = NO` — `curved_oblique_section` giữ
`foundation_only`; bao đóng V1 **không nới**. Việc mô hình có tự chọn
direct-radius hay rim-point giữ **`NOT_MEASURED`**.

```
RECOMMENDED_NEXT_ACTION = OBLIQUE_ELLIPSE_FRESH_E2E_RERUN
```

Đề · oracle · gold · registration đã sẵn; cập nhật identity mới, trần **5
logical application calls**. Tiền đề §10 của lượt ấy nay **đứng vững**, nên kết
luận về `rim_point` đọc được.
Báo cáo: `docs/CURVED_SCALAR_AXIS_SCALE_REPAIR.md`.

### 1a-decies. `OBLIQUE_ELLIPSE_FRESH_E2E_RERUN` (2026-09-07)

**DỪNG TRƯỚC PROVIDER.** `APPLICATION_LLM_CALLS = 0` — không tiêu một lượt
quota nào, và đó là kết quả ĐÚNG chứ không phải một lượt hỏng.

```
GOLD_PREFLIGHT              = PASS   (gold qua phép mới, served, 16π√5)
CYLINDER_DIRECT_RADIUS_PATH = FAIL   ← điều kiện dừng §4 của brief
BLOCKER = CURVED_SCALAR_AXIS_SCALE_IN_ELLIPSE_CAP_CHECK · loại KERNEL
```

⚠️ **Cùng một hình trụ, hai cách khai, hai kết quả khác nhau.** Hai khối bằng
nhau về hình (`radius_sq` 16 = 16 · `height_sq` 400 = 400 · trục cùng phương),
nhưng khai bằng **hai điểm** thì cắt ra elip `16π√5`, còn khai bằng **`radius`
+ `height`** thì bị từ chối `CURVED_ELLIPSE_CROSSES_CAP`.

Gốc lỗi là **một biểu thức** trong `intersect_plane_curved_ellipse`:
`tren = 1 − L`. `huong_truc` trả `truc` (`|u| = h`) ở nhánh ĐIỂM nhưng
`HUONG_TRUC_CANONICAL` (`|u| = 1`) ở nhánh VÔ HƯỚNG, nên `L` là **tỉ lệ**
`0…1` ở nhánh đầu và **khoảng cách tuyệt đối** `0…h` ở nhánh sau — `L = 10` cho
`tren = −9`. `duoi_sq = L²·|u|²` đúng ở CẢ HAI nhánh (= 100), nên chỉ phép kiểm
đáy TRÊN hỏng.

⚠️ **Đúng lớp lỗi mà chính file ấy đã cảnh báo**: docstring `_ti_le_truc` viết
ra khác biệt thang này, nhưng viết cho đường ĐƯỜNG TRÒN (kết quả không phụ
thuộc vị trí dọc trục). Phép ELIP thêm sau **có** một phép kiểm phụ thuộc vị
trí và **không** áp phép đổi thang. Đường tròn đối chứng vẫn đúng ở cả hai
nhánh — chỉ phép elip hỏng, và hỏng **fail-closed** (từ chối oan, chưa ca nào
trả đáp số sai). Không phải một ca xui: `h² ∈ {100, 400, 1600, 2500}` đều bị từ
chối ⇒ **nhánh vô hướng đóng hoàn toàn** với phép elip.

**Vì sao dừng là đúng chứ không phải quá cẩn thận.** §10 của brief bắt *chứng
minh bằng chữ ký* rằng `radius + height` là đường hợp lệ TRƯỚC khi rút ca — chỉ
khi ấy mới đọc được việc mô hình bịa `rim_point` là *"lựa chọn của chương
trình, không phải yêu cầu của hệ"*. Phép đo **bác chính tiền đề ấy**, nên chạy
live sẽ làm mọi kết luận về `rim_point` mất giá trị: đúng lớp lỗi *"bộ đo không
nằm trên đường chạy thật"* kho này đã trả giá hai lần.

⚠️ **Hai phát hiện ở ca ⑦, đừng trộn**: (a) `h = 20` khai thẳng ghim về
`tam_day_tren` bị grounding từ chối — **KHÔNG phải lỗi**, đề cho tâm đáy trên
là một ĐIỂM chứ không cho chiều cao; (b) đường height TRUNG THỰC
(`h = measure(distance, O, O′)`) mới lộ ra lỗi kernel thật.

Sáu phản ví dụ còn lại của §4 đều đúng tầng. Ca ① đáng nhắc: `2x − z + 11 = 0`
song song nên elip **bằng hệt** — bỏ bất biến nguồn thì nó `served` với đáp số
ĐÚNG.

**Replay §5, 0 lượt gọi**: attempt 1 `SCHEMA PASS` · `STATIC PASS` ·
`SERVABLE NO` (chặn bởi `P_rim`) · minimal delta 2 trường → `served`, `16π√5` ·
attempt 2 vẫn `UNANCHORED_DERIVED_ASSUMPTION`. Hai ô giữ phân biệt, không gộp.

**Không đụng mã sản phẩm**: `CACHE_VERSION` 89 → 89 · candidate `422a9e7b…`
không đóng băng lại · **cả NĂM băm model-facing không đổi một byte** ·
`curved_oblique_section` giữ `foundation_only`. ⚠️
`ELLIPSE_FOUNDATION_SEQUENCE` **KHÔNG đóng** —
`CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` giữ `NOT_MEASURED` vì điều kiện là
*eventual served* trong một lượt live, và chưa có lượt nào.

```
RECOMMENDED_NEXT_ACTION = CURVED_SCALAR_AXIS_SCALE_REPAIR
```

Dùng lại `_ti_le_truc` (thẩm quyền đã có) thay vì viết phép quy đổi thứ hai.
Cổng chống tái phát đã sẵn: `test_10_pv7b…` **tự khai sẽ đỏ khi lỗi được sửa**,
và thông điệp assert nói thẳng phải xoá nó rồi mở lại lượt live này. Đáng làm
cùng wave, đo được ở đây nhưng KHÔNG sửa: `height` vắng trong `_TOAN_HANG_LENH`
(không kiểm kiểu tĩnh) · vắng trong `_NGUON_CUA_PHEP_DUNG` (đồ thị phụ thuộc
mất mắt xích chiều cao — đúng lập luận chú thích đã dùng cho `radius`) · vắng
trong `O_TEN` (thẻ in `height?:tên` không kèm vai trò, trong khi `radius?` có).
Báo cáo: `docs/OBLIQUE_ELLIPSE_FRESH_E2E_RERUN.md`.

### 1a-nonies. `PLANE_FROM_EQUATION_REPRESENTATION` (2026-09-07)

**Thêm ĐÚNG MỘT phép dựng, và nó đóng một khoảng trống BIỂU ĐẠT chứ không
thêm tiện nghi.** `APPLICATION_LLM_CALLS = 0`.

```
construct_plane_from_equation(a, b, c, d) → plane3
NEW_MEMORY_TYPES = 0 · NEW_IR_OPERATIONS = 1 · NEW_PER_PROBLEM_MODULES = 0
PLANE_FROM_EQUATION_FOUNDATION = CLOSED
```

Wave trước đo được: mặt phẳng cho bằng phương trình có ba lối biểu đạt và
**chỉ một lối chạy được**, lối ấy đòi gắn `source_fact_id` vào **toạ độ đề
không hề nêu** — tức hệ buộc mô hình khai xuất xứ không trung thực để đi được.
Wave này chữa nguyên nhân thay vì nới grounding (nới là làm yếu một cổng đang
gác đúng).

Kernel giữ biểu diễn: `Plane3.from_equation` đặt **cạnh `Plane3.through`**,
điểm neo canonical dồn `−d` vào trục đầu tiên có hệ số khác 0 ⇒ **toạ độ ở lại
ℚ³**. Suy biến `(a,b,c) = (0,0,0)` chặn ở **hai tầng** — lược đồ (lỗi đi ngược
về mô hình qua vòng sửa) và kernel (tiền điều kiện của hàm công khai); phép
tiêm ② chứng minh đó là hai tầng chứ không nhân đôi thẩm quyền.

⚠️ **Hệ số là SỐ, và grounding KHÔNG hỏi chúng câu nào** — nó chỉ soi
`memory_declarations`. Nên phép gác là `SourceInvariant kind="plane_equation"`:
**server tự đọc phương trình từ câu văn của đề** rồi so **tỉ lệ chính xác**
(định thức con 2×2, không dung sai) với mặt phẳng có thật trong trạng thái
cuối. Nó hỏi **trên HÌNH, không trên câu lệnh**, nên phủ luôn đường dựng ba
điểm cũ — không có cửa sau.

⚠️ **Ca đắt nhất, và là lý do tầng ấy không bỏ được**: `2x − z + 11 = 0` SONG
SONG với mặt phẳng đề cho nên elip **bằng hệt** — `16π√5`, đúng đáp số. Mọi
cổng hỏi *đáp số* đều xanh, hình thì sai chỗ. Phép tiêm ③ đo thẳng cái giá: gỡ
bất biến ⇒ ca ấy **`served`** kèm đáp số ĐÚNG, không cổng nào kêu.

⚠️ **Bộ đọc phương trình có HAI lỗi thật, bắt được bằng test trước khi nhập.**
Bản đầu không hỏi biên từ: *"Diện tích mặt phẳng **đáy** = 12"* đọc thành mặt
phẳng `y − 12 = 0`; nặng hơn, *"(α): 2x + **m**y − z + 10 = 0"* đọc thành
`y − z + 10 = 0` — một phương trình **KHÁC hẳn** đề, tức một mặt phẳng SAI được
đem đi đối chiếu. Bản sửa nuốt trọn cụm chữ cái ở biên bẩn rồi phân xử bằng
**biến độc lập**: có mà không đọc được ⇒ CHẶN (`plane_equation_unresolved`),
không có ⇒ IM LẶNG. Chặn oan một lớp đề còn tệ hơn bỏ sót một phép kiểm.

**Replay §11 nguyên byte, 0 lượt gọi.** Ứng viên attempt 1 — mô hình **tự viết
ở lượt trước**, tự đặt đúng tên và đúng chữ ký — nay `SCHEMA PASS` ·
**`STATIC PASS`** (trước: schema TỪ CHỐI). Vẫn `SERVABLE = NO`, nhưng **không
vì mặt phẳng**: grounding bác `P_rim`, điểm vành mô hình bịa cho hình trụ —
lớp lỗi `ball_2` có sẵn từ trước, trong khi mô hình **đã khai sẵn** `R` với
`source_fact_id`. Delta **HAI trường** (bỏ `P_rim`, `rim_point` → `radius: R`),
**không chạm một byte nào của câu lệnh mặt phẳng** ⇒ `served`, `16π√5`,
`checked=1 passed=1`, trace và Scene3D PASS.

**Thẻ 6042 → 6302 B (+260)**, toàn bộ trên dòng lệnh mới. Luật in vai trò ô số
hẹp dần HAI lần trước khi chốt: in cho mọi ô = **+1791 B**; in cho cả ô *"giá
trị thô"* = +132 B nhưng 27 trong đó nói lại đúng thứ tên ô đã nói, trên dòng
`memory_declarations` mọi chương trình đều đọc. Bản chốt +78 B, và dòng ấy giữ
nguyên từng byte. Card C nguyên vẹn.

**`CACHE_VERSION` 88 → 89.** Ba băm model-facing đổi (`grammar_card` ·
`synthesis_schema` · `capability`); `prompts` và `analyze_schema` **không đổi
một byte** — hợp đồng `SourceInvariant` do SERVER sở hữu, không bao giờ gửi
cho mô hình. ⚠️ Lần bump này **mạnh hơn 86/87/88**: wave đổi cả **PHÁN QUYẾT**,
không riêng đầu vào — một envelope `ok` cache dưới v88 có thể là chương trình
hệ HÔM NAY từ chối. Candidate `f48e768b…` → **`422a9e7b…`** (90 → 91 file).

`PRODUCT_CAPABILITY_CHANGED = NO` — `curved_oblique_section` giữ
`foundation_only`.

```
RECOMMENDED_NEXT_ACTION = OBLIQUE_ELLIPSE_FRESH_E2E_RERUN
```

Đề · oracle · gold · registration đã sẵn; trần **5 logical calls**. Nó cũng đo
miễn phí câu thứ hai: ⚠️ **`CURVED_RIM_POINT_AFFORDANCE`** — mô hình khai `R`
với `source_fact_id` rồi **vẫn** bịa `P_rim`, dù ô `radius` đã có từ
2026-09-04. `n = 1`, phân loại **`HYPOTHESIS`**.
Báo cáo: `docs/PLANE_FROM_EQUATION_REPRESENTATION.md`.

### 1a-octies. `SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION` (2026-09-07)

**Pha A đóng đúng lỗ nó nhắm; Pha B chạy được và CHƯA tới `served`.**

```
Pha A  SCOPE_GATE_REPAIR   = XONG   (4 nghĩa vụ · 43 test · 4 phép tiêm)
Pha B  ELLIPSE_END_TO_END  = CHƯA `served`
BLOCKER = PLANE_FROM_EQUATION_REPRESENTATION · SYSTEM_GAP + OPERATOR_AFFORDANCE
```

`_MANH_MOI_NGHIA_VU` nay phủ **cả bốn** nghĩa vụ vừa analyze-emittable vừa
checker-backed — `area` · `lateral_area` · `radius` · `section_matches`. Bất
biến khoá bằng test **dẫn xuất** từ registry (`analyze enum ∩ GEOMETRY_CHECKERS`
⊆ khoá của bảng), không phải danh sách chép tay:

```
"Tính diện tích elip (E)."             → True   ['area']
"Tính diện tích xung quanh hình trụ."  → True   ['area', 'lateral_area']
"Tính bán kính mặt cầu."               → True   ['radius']
đề nón, BỎ cụm "vuông góc"             → True   ['radius']   ← trước đây chết
```

⚠️ **Phép tiêm phải chấm ở mức TẬP, không mức `bool`.** Bỏ `lateral_area` thì
*"diện tích xung quanh…"* vẫn mở cổng nhờ `area` ⇒ khẳng định boolean xanh mà
**không chứng minh gì**.

⚠️ **Một mục `NGOAI_NANG_LUC` là SAI PHÂN LOẠI, đã sửa.** Đề nón *"bán kính 3,
đường sinh 5, tính diện tích xung quanh"* chưa bao giờ ngoài năng lực — hệ tính
đúng `15π`. Nó nằm đó vì **cổng từ chối nó**, và cổng từ chối vì bảng manh mối
thiếu `lateral_area`: một danh sách *"ngoài năng lực"* dẫn từ hành vi của cổng
là **vòng lặp** — cổng sai thì danh sách sai theo, và cả hai cùng xanh.
`test_scope_gate_quantity_obligation_gap.py` (12 test khoá lỗ) đã **xoá** vì lỗ
đóng; chống tái phát nay là test parity, mạnh hơn.

**Pha B, lượt live `oblique-ellipse-after-scope-repair-20260907T050244Z`:**

```
STAGE = semantic_program · servable = False · envelope = unsupported
ANALYZE 1 · SYNTHESIS 1 · REPAIR 2 · LOGICAL 4/5 · PHYSICAL 4 · RETRY 0
CANDIDATE_PROGRAM_ATTEMPTS 3 · TOKENS 20 725/40 000
ANALYZE_CONTRACT = PASS (toàn bộ 7 chiều)
```

Cổng phạm vi **đã mở đúng** — đề đi qua `scope` → `analyze` → ba lượt sinh.
Cả ba ứng viên chọn đúng `intersect_plane_curved_ellipse` **ngay attempt 0**,
khai `ellipse3`, dựng đúng hình trụ, đo đúng `area` của `E`. **Cả ba chỉ hỏng ở
mặt phẳng**: `IR_USE_BEFORE_CONSTRUCTION` → tự đặt tên phép còn thiếu
`construct_plane_from_equation` (schema bác) → ba điểm khai `model_assumption`
(`UNANCHORED_DERIVED_ASSUMPTION`). Ba điểm ấy **thoả đúng** `2x − z + 10 = 0`;
thứ bị bác là **xuất xứ**, không phải toạ độ.

⚠️ **Đo tất định, 0 lượt gọi: mặt phẳng cho bằng PHƯƠNG TRÌNH có ba lối biểu
đạt và chỉ MỘT lối chạy được** — (A) `plane3` + `initial_value` → grounding bác
*"giá trị không có trong mục"*; (B) điểm + `model_assumption` → bác; (C) điểm +
`source_fact_id` → chạy. Lối C đòi gắn `source_fact_id` vào **toạ độ đề không
hề nêu**, tức **buộc mô hình khai xuất xứ không trung thực để đi được**. Đó là
khoảng trống biểu đạt của **hệ**, không phải lỗi mô hình. `_KIEU_DUNG` không có
phép nào chứa chữ `equation`.

**Cache 87 → 88 theo LUẬT** (đổi policy định tuyến), đúng tiền lệ bump 80.
Kiểm bằng row thật: `main.py:746`/`:781` chỉ cache `status == "ok"` nên refusal
ở `scope` **chưa bao giờ được cache** — không có row stale. Sáu băm model-facing
**không đổi một byte**: Pha A chỉ sửa **đường vào**, không sửa bề mặt mô hình.
Candidate `e8c6150f…` → **`f48e768b…`**. `curved_oblique_section` giữ
`foundation_only`; `ELLIPSE_FOUNDATION_SEQUENCE` **KHÔNG đóng** —
`CARD_C_CURVED_ELLIPSE_PATH_CONFIRMED` vẫn `NOT_MEASURED` vì điều kiện là
*eventual served*.

```
RECOMMENDED_NEXT_ACTION = PLANE_FROM_EQUATION_REPRESENTATION
```

Hai đường, chọn bằng kiểm toán chữ ký: **(1)** thêm phép dựng
`construct_plane_from_equation(a,b,c,d) → plane3` — mô hình đã **tự đặt đúng
tên và đúng chữ ký**, hệ số hữu tỉ nên toạ độ ở lại ℚ³, và xuất xứ dẫn **thẳng**
từ fact phương trình; **(2)** nới grounding cho điểm dẫn xuất từ fact phương
trình — rẻ hơn nhưng nới một cổng đang gác đúng. Bằng chứng nghiêng về **(1)**:
nó đóng cả hai `SYSTEM_GAP` cùng lúc.
Báo cáo: `docs/SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR_AND_ELLIPSE_CONFIRMATION.md`.

### 1a-septies. `OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION` (2026-09-07)

**DỪNG TRƯỚC PROVIDER.** `APPLICATION_LLM_CALLS = 0` — không tiêu một lượt
quota nào, và đó là kết quả ĐÚNG chứ không phải một lượt hỏng.

```
GOLD_PREFLIGHT = PASS · SYSTEM_EXPRESSIBLE = YES
MODEL_DISCOVERABILITY = NOT_MEASURED   (cổng chặn TRƯỚC analyze)
BLOCKER = SCOPE_GATE_MISSING_QUANTITY_OBLIGATION_CLUES · loại SYSTEM_GAP
```

Đề mới `r=4 · h=20 · (α): 2x−z+10=0` đi trọn đường tới `served` với **`16π√5`
chính xác**, hai oracle độc lập (công thức bán trục · thế thẳng bốn đầu mút vào
`x²+y²=16` và `2x−z+10=0` — chúng ra `(4,0,18)`, `(−4,0,2)`, `(0,±4,10)`, toàn
hữu tỉ, biên dọc `z ∈ [2,18]`).

⚠️ **`co_duong_thuc_thi` từ chối đề ở tầng `scope`.** `_MANH_MOI_NGHIA_VU`
thiếu **bốn** nghĩa vụ CÓ CHECKER — `area` · `lateral_area` · `radius` ·
`section_matches` — nên đề chỉ hỏi *"tính diện tích …"* bị bác trong khi hệ
**có** đủ đường. Cả LỚP câu hỏi ấy trượt, không phải một cách viết xui.

⚠️ **Đính chính CÁCH ĐỌC wave trước**: đề bài nón hỏi `radius` nhưng qua cổng
nhờ manh mối **`perpendicular`** từ cụm *"vuông góc với SO"* ở phần MÔ TẢ. Bỏ
hai chữ ấy thì nó cũng chết ở `scope`. Cổng cho đúng câu trả lời **vì một lý do
sai**. Mọi con số của `CURVED_END_TO_END_FRESH_CONFIRMATION` **giữ nguyên** —
thứ sửa là cách đọc, không phải số liệu.

Lỗ sống sót qua ba wave vì ba wave đầu **không đi qua cổng** (runner A/B dùng
hợp đồng cố định; wave nền elip dùng `verify_and_compile`), còn wave thứ tư đi
qua **nhờ một từ trong phần mô tả**.

**Không đụng mã sản phẩm**: cache 87 → 87 · candidate `e8c6150f…` không đóng
băng lại · sáu băm model-facing không đổi · `curved_oblique_section` giữ
`foundation_only`. `ELLIPSE_FOUNDATION_SEQUENCE` **KHÔNG đóng** — điều kiện là
*eventual served*, và phép đo chưa chạy được.

Bộ đo: runner nay chọn được **gold module và scorer module theo đăng ký** thay
vì viết runner thứ hai; runner cũ vẫn 21 pass.

```
RECOMMENDED_NEXT_ACTION = SCOPE_GATE_QUANTITY_OBLIGATION_CLUE_REPAIR
```

Sửa đúng một bảng, kèm phép tiêm chứng minh cổng đỏ được cho cả bốn nghĩa vụ.
Sau đó **chạy lại chính wave này** — registration và gold đã sẵn, đề chưa tiêu
lượt nào.
Báo cáo: `docs/OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION.md`.

### 1a-sexies. `CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION` (2026-09-07)

**Chuyển từ tối ưu khả năng sinh sang MỞ RỘNG NĂNG LỰC HÌNH HỌC.**
`APPLICATION_LLM_CALLS = 0`.

```
SYSTEM_EXPRESSIBLE = YES · DETERMINISTICALLY_CORRECT = YES (9√2π, hai oracle)
MODEL_DISCOVERABLE = NOT_MEASURED · STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
```

**Bản đồ bốn họ còn thiếu**, đọc thẳng mã nguồn — mỗi ô trỏ chữ ký hoặc `grep`
trên cây hiện tại. Chọn **thiết diện cong xiên** vì nó thắng **5/7** tiêu chí và
không thua ở đâu: miền số `Radical` (`he·√can·π^mu`) **đã** chở được `9√2π` ·
checker và trace **dẫn xuất** nên tự nhận kiểu mới · khoảng trống thu về **một
kiểu + một phép**.

Ba họ còn lại, lý do đã kiểm lại: **tròn xoay tổng quát** vướng **miền số**
(cần tích phân) · **ghép–bù** không có một phép boolean nào trong `geometry/`
(grep 0 hit) · **đa diện không lồi** là ứng viên gần thứ hai, và nó mang một
khiếm khuyết **có sẵn chưa ai ghi**: `volume_pyramid_fan` kiểm đáy *phẳng*
nhưng **không kiểm lồi** ⇒ đáy lõm cho số sai **im lặng**.

**Tái hiện trước khi sửa**: chương trình cắt xiên qua schema · `ir_static` ·
grounding · phủ · **cả hai** bất biến nguồn rồi chết ở `execution` với
`CURVED_SECTION_OUTSIDE_V1_CLOSURE` — khoảng trống ở **kernel + hệ kiểu**.

**Thêm đúng một kiểu (`ellipse3`) và đúng một phép
(`intersect_plane_curved_ellipse`).** Mọi trường ở ℚ: bán trục dưới dạng
**bình phương**, hai phương trục là tích có hướng của vectơ hữu tỉ (chưa chuẩn
hoá — renderer chuẩn hoá ở biên hiển thị). Phép RIÊNG chứ không phải kiểu trả
về "tuỳ lúc chạy": kiểu động lấy đi đúng thứ `ir_static_check` sinh ra để làm.
Ca chuẩn `r=3 · h=20 · z=10+x` cho **`9√2π` chính xác**, hai oracle độc lập.
Năm biên, năm mã riêng. Đường `circle3` cũ, cầu và nón **không suy suyển**.

⚠️ **Sửa một lỗ ĐÃ TRÔI HAI LẦN.** Dòng `type nhận đúng một trong` của thẻ là
danh sách **chép tay**, thiếu `circle3`+`curved_solid` từ 2026-09-03. Hậu quả
đo được ở wave trước: mô hình khai thiết diện là `section` rồi hỏng ở
`ir_static`. Nay dẫn xuất bằng cách **loại trừ** tập Tin học đã đóng băng —
chiều trôi đảo lại, thêm kiểu hình học là thẻ tự nhắc.

**Ba tầng tự nhận, không sửa một dòng logic**: `OBLIGATION_KINDS["area"]` ·
`check_area` · `_BIEU_THUC_HINH_HOC` (trace/depends) — cả ba **dẫn xuất**. Đó
là bằng chứng cho thiết kế một-thẩm-quyền.

`CACHE_VERSION` **86 → 87** (ba băm model-facing đổi: `grammar_card`,
`synthesis_schema`, `capability`; `prompts` và `analyze_schema` không đổi một
byte). Candidate `138db7b1… → e8c6150f…`.
Capability `curved_oblique_section`: **`unsupported` → `foundation_only`**;
ball/cylinder/cone **giữ nguyên**.

⚠️ **Hai giả định của chính bộ test đã sai và được sửa bằng phép đo**: kiểu
**dựng ra** thắng kiểu **khai** ở mọi tầng (hành vi có sẵn, không do wave này);
và phép tiêm dependency ban đầu nhắm sai bảng nên **vẫn xanh** — tức không gác
gì. Cả hai ghi lại trong báo cáo §9.

```
RECOMMENDED_NEXT_ACTION = OBLIQUE_ELLIPSE_FRESH_END_TO_END_CONFIRMATION
```

Báo cáo:
`docs/CURVED_MISSING_FAMILY_ROADMAP_AND_OBLIQUE_CYLINDER_ELLIPSE_FOUNDATION.md`.

### 1a-quinquies. `CURVED_END_TO_END_FRESH_CONFIRMATION` (2026-09-07)

**Xác nhận Card C ngoài họ đoạn thẳng, đi TRỌN đường sản phẩm.** 1 đề hình
CONG mới. `DEVELOPMENT_CURVED_END_TO_END_CONFIRMATION` · `HELD_OUT_CLAIM = NO`.
Khác mọi wave A/B trước ở hai điều: `analyze` là **một lượt LLM thật**, và vòng
sửa của sản phẩm **không bị tắt**.

```
CURVED_END_TO_END_FRESH_CONFIRMATION = PASS   ·   CARD_OPTIMIZATION_SEQUENCE = CLOSED
CARD_C_OUTSIDE_SEGMENT_FAMILY = CONFIRMED_ON_ONE_CASE
```

Đề: nón đỉnh `S`, tâm đáy `O`, bán kính đáy 12, chiều cao `SO` 18; `T` trên
`SO` với `ST:TO = 1:2`; mặt phẳng qua `T` ⊥ `SO` cắt nón theo `(c)`. Oracle
`r(c) = 4`, kiểm chéo **ba lối độc lập** (tỉ lệ trục · chiều cao từ đáy ·
KERNEL).

`SYSTEM_EXPRESSIBLE = YES` (7/7 câu, mỗi câu trỏ chữ ký hoặc test) ·
`GOLD_PREFLIGHT = PASS` (19 test, **7 phản ví dụ** mỗi cái chặn đúng tầng).

**Lượt live: `served`, `EXACT_ANSWER = 4`.** 4 lượt logic (analyze 1 +
chương trình 3) · 0 retry · **19 263/37 500** token · `cached_content = 0`.
`FIRST_ATTEMPT_SERVABLE = NO` — đạt được **nhờ 2 lượt sửa**, và cả hai lỗi đều
là **lớp đã biết**: `at` sai ô (lớp `POINT_INITIALIZATION`, tự đóng — bằng
chứng **thứ hai** cho `PERMANENT_SLOT_INSTRUCTION_NEEDED = NOT_PROVED`), và
`construct_section` cho khối **cong** (lớp `c5b`/`c9b` của
`CURVED_SECTION_RADIUS_PATH_ADJUDICATION`, tái hiện và vẫn sửa được).

**Hai delta của Card C hiện rõ trên bài hình cong**: `ratio 1/3` quy đúng từ
`m:n`, và **cả ba** điểm đầu vào đi kênh `model_assumption`. Không attempt nào
hỏng ở hai trục ấy.

⚠️ **Đính chính bộ chấm:** bản inline ghi `ANALYZE_CONTRACT_CORRECT = FAIL`
trong khi runner **chưa giữ** raw analyze — chấm trượt một tầng nó không quan
sát được. Bộ chấm nay phân biệt `PASS/FAIL` · **`NOT_CAPTURED`** ·
`NOT_REACHED`; runner đã sửa để giữ raw. Giá trị đúng: nghĩa vụ **PASS**, nội
dung fact **`NOT_CAPTURED`** (8 fact quan sát được). Cũng đã thêm **phân rã
theo tầng** cho `candidate_attempts` — tổng `4` gồm 1 lượt analyze, đọc một
mình sẽ bị hiểu thành 4 ứng viên chương trình.

**Không đụng mã sản phẩm**: `CACHE_VERSION` 86 → 86 · candidate `138db7b1…`
không đóng băng lại · sáu băm model-facing không đổi ·
`PRODUCT_CAPABILITY_CHANGED = NO`.

⚠️ **Giới hạn:** `n = 1` · không tách được đóng góp từng tầng · **không phải
lượt sinh đúng ngay** · một ca **chưa đủ** để chuyển `ball`/`cylinder`/`cone`
sang `supported`. Hai `HYPOTHESIS` chưa phân biệt được: thẻ không liệt kê
`circle3`/`curved_solid` trong kiểu khai được (khớp với chỗ attempt 1 hỏng), và
mô hình chọn `rim_point` thay vì ô `radius`.

```
RECOMMENDED_NEXT_ACTION = CURVED_MISSING_FAMILY_ROADMAP_AND_FIRST_IMPLEMENTATION
```

Báo cáo: `docs/CURVED_END_TO_END_FRESH_CONFIRMATION.md`.

### 1a-quater. `MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION` (2026-09-07)

**Wave đầu tiên trong chuỗi ĐỔI MÃ SẢN PHẨM.** 2 đề MỚI × 2 arm = 4 lượt
synthesis. `DEVELOPMENT_SYNTHESIS_AB` · `HELD_OUT_CLAIM = NO` ·
`ANALYZE_CALLS = 0` · `REPAIR_CALLS = 0` · 23 801/30 000 token.

```
CARD_C_ADOPTED = YES      PRODUCT_VARIANT  A → C      CACHE_VERSION 85 → 86
```

Thẻ **C** = thẻ sản phẩm + **hai** hướng dẫn đã đo riêng ở hai wave trước
(`ratio` định nghĩa `t`; dòng `Xuất xứ:` nói ba ô xuất xứ dùng khi nào), và nó
**trùng byte** với `card_P1` của wave provenance — dùng nguyên byte để giữ liền
chuỗi bằng chứng.

| trên 2 đề CHƯA TỪNG đo | A0 (thẻ cũ) | C |
|---|---:|---:|
| `t` đúng (Fraction) | **0/2** | **2/2** |
| xuất xứ đúng | 1/2 | **2/2** |
| điểm dẫn xuất được dựng | 2/2 | 2/2 |
| mô phỏng `served` đúng | **0/2** | **2/2** |

Ghép cặp: **C thắng 2 · thua 0**. `A0_CORRECT_AND_C_INCORRECT = 0`. A0 mắc
đúng hai lỗi mà hai dòng nhắm tới — `f2/A0` viết `1/2` cho `KH = 2·GK` (đúng
`t` là `1/3`); `f1/A0` khai gốc toạ độ với **cả hai** ô xuất xứ trống, **và**
đi vòng qua một biến `ratio_for_M` — đúng thứ nhãn `ratio:tên` mời gọi.

Sáu điều kiện áp dụng khoá **trước** lượt gọi đầu, đủ cả sáu. Bề mặt mô hình:
đúng **một** thành phần đổi (`grammar_card e0fbbc84 → 9685b06a`);
`prompts` · `synthesis_schema` · `analyze_schema` · `capability` **không đổi
một byte**. Candidate đóng băng lại `36e81713… → 138db7b1…`.

⚠️ **Hai đính chính bộ đo, làm xong TRƯỚC lượt gọi đầu**, cả hai tìm bằng stub:
`REPAIR_PROBE_COUNTER_DECOMPOSITION` (`PHYSICAL_ATTEMPTS = 2` của wave trước
đếm **ứng viên**, không đếm request; đúng là `physical_api_attempts = 1`) và
`RUNNER_SOURCE_INVARIANT_UNDERBINDING` (runner A/B thiếu `bat_bien_do_dai`, nên
cổng `segment_length` **chưa từng chạy** trong hai wave A/B trước). Chấm lại
artifact cũ, 0 lượt gọi: **không kết luận cũ nào đổi**.

⚠️ **Giới hạn:** delta **GỘP** hai dòng, `n = 2` cặp, cả hai đề cùng một họ
(điểm chia đoạn thẳng). Token có **nhiễu cache** (C nhận 997, A0 nhận 0).
`STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`.

```
RECOMMENDED_NEXT_ACTION = CURVED_END_TO_END_FRESH_CONFIRMATION
```

Thẻ vừa đổi và cache vừa bump, nên thứ chưa ai biết là **thẻ mới cư xử thế nào
ngoài họ đoạn thẳng** — và đường sản phẩm thật có `analyze` cùng vòng sửa, hai
tầng mà bốn lượt vừa rồi **cố ý** không chạy. Một phép xác nhận **nhỏ**,
end-to-end, trên bài hình **cong** mới.
Báo cáo: `docs/MINIMAL_CARD_CONSOLIDATION_AND_FRESH_CONFIRMATION.md`.

### 1a. Trạng thái vận hành CUỐI — hệ đã đóng băng cho khoá luận (2026-09-02)

Đo trên cây sạch, sau `FINAL_DEAD_EVALUATION_CLEANUP`, candidate đã đóng băng
lại. **0 API call thật** ở toàn bộ bảng này.

| | |
|---|---|
| pytest | **2760 pass, 1 skipped, 1 deselected** |
| vitest | **646 pass / 47 file** |
| build | `tsc -b && vite build` — **PASS** |
| tập demo (tất định) | `scripts/replay_demo_cases.py` — **DEMO_REPLAY 5/5**, **REDUCED_CHAIN 1/1** |
| bề mặt sập | `scripts/audit_demo_crash_surface.py` — **6/6 biên đúng kiểu**, ném ra ngoài **0** |
| smoke trình duyệt | `frontend/scripts/spot-check-demo.mjs` — **12/12**, 0 lỗi console (Chrome thật, CDP) |
| freeze verify | `scripts/freeze_evaluation_candidate.py --verify` — **PASS** (86 file, `a075e9f5…`) |
| import cây `app/` | **ACTIVE_APP_IMPORT_FAILURES = 0** (91 → 69 module sau khi gỡ bộ đo chết) |
| Docker | `docker compose up -d --build` OK (backend :8000 + Postgres) |

**Không chạy full live eval theo mặc định.** Diễn giải bằng chứng (claim ↔
evidence ↔ limitation) nằm ở **`docs/THESIS_READINESS.md`** — bảng đó là chủ
sở hữu duy nhất; đừng chép số benchmark vào đây.

### 1b. ⛔ Baseline CŨ — BẰNG CHỨNG LỊCH SỬ, không phải trạng thái hiện tại

Đo 2026-07-25/26 trên hệ **Tin học** (danh mục 24 target, DSL, catalog — đã gỡ).
Giữ lại để đối chiếu lịch sử, **không** đọc như hiện tại:

| | |
|---|---|
| pytest | 1106 pass, 2 skipped, 1 deselected (2026-07-26, sau W3) |
| vitest | 664 pass / 49 file (2026-07-26, sau W3-VR) |
| catalog conformance | 22 target · conformance 0 · ownership 0 · parity 0 · PASS (`scripts/catalog_runtime_matrix.py` — script đã gỡ) |
| audit bố cục | `npm run audit:layout` — 4/4 route sạch (Task 13; Chrome thật, CDP; đã chứng minh bằng tiêm lỗi giả ở M9-UX7) |
| build | bundle chính ~357KB; chunk Three.js 544KB code-split (2026-07-25) |
| nghiệm thu M10 | CDP browser thật (SwiftShader WebGL) — 15/15 |
| Live smoke (M7.14T) | 8/8 OK · 22 HTTP request · 0 retry · 0 transient · `gap_gate_recall = 1.0` |

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

Miền **duy nhất**: hình học không gian (Toán 11–12). `simulation_id` duy nhất:
`generic.semantic_program`. Danh sách dưới đây **dẫn từ thẩm quyền**, kiểm bằng
`GET /api/diagnostics/runtime` hoặc `runtime_identity()` — đừng chép tay.

**8 biểu thức** (`ir_static_check._CHU_KY`) — `divide_segment`,
`intersect_line_line`, `intersect_line_plane`, `intersect_plane_plane`,
`midpoint`, `project_onto`, `translate`, `vector_from_points`.

**6 câu lệnh dựng** (`_KIEU_DUNG`) — `construct_point`, `construct_line`,
`construct_plane`, `construct_polygon`, `construct_section`, `construct_solid`.
Mỗi câu lệnh dựng là **một bước học sinh nhìn thấy**.

**5 phép đo** (`measure_contract.BANG_PHEP_DO`) — `distance`, `angle_cos`,
`angle_cos_sq`, `volume`, `area`. Tính bằng `Fraction` + `Radical`, **không
float**. `area` nhận `polygon3` và `section`, một thẩm quyền toán học
(`measure.area_polygon`), thêm 2026-09-03 cùng `EXACT_MEASURE_FOUNDATION`.

**Miền số chính xác** (`geometry/radical.py`) — `he · π^mu · √can` với
`mu ∈ PI_EXPONENT_DOMAIN = (0, 1)`. π có mặt để chở các đại lượng cong sắp tới;
**chưa phép đo nào sinh ra nó** — `CURVED_GEOMETRY_SUPPORT = NONE`. Toạ độ vẫn
là **ℚ³ thuần** (`Vec3` chỉ nhận `Fraction`): mở miền ĐO không mở miền TOẠ ĐỘ.

**10 nghĩa vụ có checker** (`geometry_obligations.GEOMETRY_CHECKERS`) —
`point_on_line`, `point_on_plane`, `parallel`, `perpendicular`, `coplanar`,
`distance`, `angle`, `volume`, `section_matches`, `radius` (2026-09-03).

⚠️ **`SEALED_GEOMETRY_CHECKERS` vẫn là 9.** `radius` là mở rộng của sản phẩm
hiện tại SAU baseline đã niêm phong, nên mọi con số *"safe serve rate"* lịch sử
gắn với bản 9 — so hai bên mà không nói rõ phiên bản là so hai hệ khác nhau.

**Mặt 3D:** dựng hình theo bước, chọn/soi đối tượng (kèm `producer`/`depends`),
tách khối, tua bước. **Hạ tầng:** exact cache theo `CACHE_VERSION`; lớp học trực
tiếp; mở lại từ lịch sử với 0 lượt gọi AI.

> **Bài mới không cần mã mới** *nếu* biểu diễn được bằng IR trên — LLM kết hợp
> các primitive ấy thành chương trình khác. Điều này **không** có nghĩa mọi bài
> hình học THPT đều được hỗ trợ; ngoài IR ⇒ từ chối, không xấp xỉ.

⛔ Năng lực cũ (24 target Tin học: `algorithm.*`, `logic.and_gate`,
`binary.decimal_to_binary`, `network.packet_routing`, `generic.rule_scene` +
DSL v1, chỉnh sửa tăng dần/EditPolicy) **đã gỡ hết** ở
`LEGACY_INFORMATICS_REMOVAL`. Tra ở git history.

## 4. Capability gap CỐ Ý (không phải bug — `docs/CORRECTNESS.md §5`)

Không biểu diễn được bằng IR → **từ chối có cấu trúc**, tuyệt đối **không**
render xấp xỉ:

| gap | vì sao cố ý |
|---|---|
| **mặt cong** — cầu, trụ, nón | nhân hình học không thi hành; xấp xỉ bằng đa diện là nói dối về đáp số |
| **khối không lồi** | ngoài phạm vi `kernel`/`section` hiện tại |
| **quỹ tích, đường tròn ngoại tiếp** | chưa có primitive; không đoán |
| **kéo liên tục kiểu GeoGebra** | phá song ánh `frame k ⇔ trace[k]` (bất biến #31) — tương tác là chọn/tách/tua |
| **mọi miền không phải hình học không gian** | `out_of_scope`, chặn ở biên API và pipeline, **0 lượt gọi model** |
| đề không ánh xạ tới nghĩa vụ **có checker** | `not_simulation_suitable`, chặn trước mọi lượt gọi (`co_duong_thuc_thi`) |

Một mức riêng, **không** phải gap: chương trình *chạy được* nhưng thiếu checker
⇒ `SEMANTIC_VERIFICATION_UNAVAILABLE`, `executable=True` mà `servable=False`.
Gộp nó vào gap là khai hệ không làm được một bài mà nó làm được.

⛔ Danh sách gap cũ (`geometric_projection`, `geometric_perpendicular`,
`geometric_intersection`, `numeric_threshold`, `continuous_motion`,
`arbitrary_algorithm`) là của hệ Tin học — và **ba cái đầu nay là năng lực lõi**
(`project_onto`, checker `perpendicular`, ba phép `intersect_*`). Đọc danh sách
cũ như hiện tại là hiểu ngược hệ thống.

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
