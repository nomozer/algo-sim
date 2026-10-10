# Cập nhật khoảng trống văn liệu: AI chọn hàm (A) hay compiler chọn hàm (B)

Ngày tìm và đọc: 2026-10-10. Tài liệu nghiên cứu cho run `hybrid-compiler-selection`. Nó **không** mô tả trạng thái hệ
thống, **không** kết luận B tốt hơn A và **không** tuyên bố tính mới của AlgoSim.

**Quan hệ với các lớp trước.**

- Bản 1 (`docs/evaluation/geometry/runs/text-to-geometry-functions/LITERATURE_GAP_MATRIX.md`, W01–W26) và bản 2
  (`docs/evaluation/geometry/runs/ai-function-route/LITERATURE_GAP_MATRIX_V2.md`, thêm N01–N11; tổng 37 công trình) là
  artifact **bất biến**. Tệp này không sửa chúng. Mã W/N giữ nguyên nghĩa của bản 2.
- Tệp này thêm 10 công trình mới, mã **H01–H10**, và phân tích riêng cho câu hỏi A/B.
- Quyết định kiến trúc đang hiệu lực (`docs/architecture/TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md`) xếp "FactGraph,
  compiler-in-the-loop" là **ứng viên nghiên cứu**, chỉ thêm khi có phép đo riêng. Tệp này tôn trọng ranh giới đó: B được
  đánh giá như ứng viên.

## 0. Quy ước

Giữ nguyên quy ước của bản 2 (§0):

- `[C]` có trong văn bản nguồn đã mở; `[I]` suy luận của người tổng hợp; `[NV]` chưa kiểm được trên nguồn gốc.
- `NR`: không thấy trong phần đã đọc, **không** có nghĩa là "không có". `UNCLEAR`: nguồn mơ hồ, hoặc bảng bị trích lệch cột.
- Mức xác minh: `VERIFIED_PRIMARY` (đã mở toàn văn), `VERIFIED_ABSTRACT_ONLY`, `NOT_VERIFIED` (không dùng làm bằng chứng).
- Preprint ghi `preprint`. Venue chỉ ghi khi trang arXiv (comments), header PDF hoặc trang nhà xuất bản nêu. DOI chỉ ghi khi
  thấy trên trang nguồn; mã `10.48550/arXiv.<id>` đã thấy trên từng trang tóm tắt arXiv mở trong lượt này. Không DOI nào được
  suy đoán.

**Cách lấy văn bản (phải khai).**

- Mọi công trình mới được tải **PDF gốc** (arXiv `/pdf/<id>`, kho HAL, trang tác giả ở Purdue) rồi trích chữ bằng
  `pdftotext -layout`. Câu trong ngoặc kép được chép từ văn bản trích thô đó. **Không** câu nào lấy qua công cụ tóm tắt.
- Công cụ tìm web chỉ dùng để **tìm địa chỉ**. Lời tóm tắt kèm kết quả tìm không được dùng làm bằng chứng. Ví dụ: kết quả tìm
  nêu hai bộ số tập/trang khác nhau cho H08; tệp này không dùng bộ nào.
- `-layout` trộn cột và làm lệch bảng. Mọi số lấy từ bảng mà lời văn không nhắc lại đều ghi `UNCLEAR` cho tới khi đối chiếu
  PDF. Ký hiệu toán (∀, →, ⊥, ¬) thường bị mất khi trích.
- **Trước khi đưa vào chương khoá luận, mọi câu trích ở đây và ở bản 1/bản 2 phải đối chiếu lại với PDF gốc và ghi số
  trang/mục.** Câu trích nào từng đi qua công cụ tải trang có tóm tắt (một phần bản 1) càng phải đối chiếu.

**Ranh giới lập luận.**

- Không suy ra tính mới từ việc văn liệu vắng một tính năng. Mọi "khoảng trống" là khoảng trống **trong tập đã đọc**.
- Không dùng pilot `LLM_ONLY` cũ (0/10) làm bằng chứng cho A hay cho B. Nó đo một kiến trúc thứ ba (mô hình viết cả Semantic
  Program) và không có đối chứng.
- Kết quả A/B **offline** của run này (dữ kiện B sinh cơ học từ ca có sẵn, theo `plan.md` cùng thư mục) giả định trích dữ kiện
  hoàn hảo. Nó kiểm planner, **không** kiểm nhánh trích dữ kiện của mô hình, nên không trả lời được các giả thuyết ở mục 5 [I].

---

## 1. Hai nhánh được so sánh

Cả hai nhánh dùng chung một back end tất định: registry đóng 24 hàm hình học có kiểu → engine (khung affine + metric Gram hữu
tỉ) → kernel chính xác → Scene3D. Chúng chỉ khác ở chỗ **ai chọn và kết hợp hàm**.

| | A — AI chọn hàm | B — compiler chọn hàm (lai, thực nghiệm) |
|---|---|---|
| Mô hình phát ra | Lời gọi hàm registry (Gemini function calling) + trích dẫn nguyên văn | Dữ kiện hình học nhỏ có kiểu: đối tượng, quan hệ, giá trị (cả ký hiệu `a`), vai trò mệnh đề (giả thiết / cần chứng minh / điều kiện / câu hỏi), phủ định, cờ mơ hồ, trích dẫn |
| Ai chọn hàm | Mô hình | Planner/compiler tất định: mở rộng định nghĩa ("hình chóp đều", "lập phương"), tham chiếu theo vai trò ("cạnh bên", "cạnh đáy", "chiều cao"), chọn hàm theo kiểu quan hệ (⊥(đường, mặt) khác ⊥(mặt, mặt)) |
| Mục tiêu chứng minh | Do mô hình tự tránh dùng làm giả thiết | Không dùng làm giả thiết; kiểm **sau** khi dựng |
| Dữ kiện phủ định | Do mô hình xử lý | Kiểm là **sai** trên cấu hình đã dựng |

[I] Dùng khung "parsing / planning / execution" của H01 (SatLM): A giao cho mô hình *phân tích đề* và một phần *lập kế hoạch
dựng* (chọn hàm nào hiện thực một quan hệ, mở rộng định nghĩa). B chỉ giao *phân tích đề*; lập kế hoạch dựng chuyển sang mã.
Engine đã giải phụ thuộc ở cả hai nhánh, nên A **không** phải "chương trình mệnh lệnh" thuần như PAL. Đây là lý do bằng chứng
ngoài hình học (H01, H02) chỉ chuyển sang được một phần.

---

## 2. Ánh xạ A và B lên ma trận bản 2

"Giống A" nghĩa là mô hình phát trực tiếp lời gọi hoặc chương trình thực thi được. "Giống B" nghĩa là mô hình phát biểu diễn
khai báo (dữ kiện, vị từ, ràng buộc) và một bộ máy tất định quyết định cách dựng hoặc giải. Mọi xếp loại là `[I]`. Căn cứ là
hàng bản 2 được trích, hoặc trang gốc được mở lại trong lượt này.

### 2.1 Giống A

| Mã | Căn cứ (hàng bản 2) | Vì sao giống A [I] | Khác A [I] |
|---|---|---|---|
| N01 BFCL | §3.1: "LLM chọn hàm + điền tham số"; §3.4 | Chuẩn đo cho đúng dạng đầu ra của A | Không hình học, không tiền điều kiện |
| N02 NESTFUL | §3.1/§3.4: mô hình tự gán nhãn biến, ≤28% full match | Lỗi ghép lời gọi lồng = rủi ro của A khi hàm sau dùng đầu ra hàm trước | Ở A engine giải phụ thuộc theo tên |
| N03 API-Bank | §3.4: lỗi tham số ≈32% tổng lỗi (bảng `UNCLEAR`) | Danh mục lỗi tham số áp cho A | API đời thường |
| W11 GeoBuildBench | §2.2/§3.4: LLM viết **cả** chương trình DSL kiến thiết; lỗi đứng đầu là tham chiếu chưa định nghĩa | Gần A nhất trong miền hình học | Viết cả chương trình (gần biến thể A4a của bản 2), hình phẳng |
| W12 GGBench | §2.2: mã GeoGebra từng bước; lỗi "conflation of construction and numeric goals" | Mô hình phát bước dựng thực thi được | Mã tự do, hình phẳng |
| W15–W17 PAL/PoT/ToRA | §3.5 (`VERIFIED_ABSTRACT_ONLY`) | Mô hình viết chương trình, bộ thông dịch thực thi | Chương trình tính toán, không phải dựng |
| W18–W21 Gorilla, CAD | §3.5 | Lời gọi API / mã CAD do mô hình phát | Không kiểm quan hệ chính xác |

### 2.2 Giống B

| Mã | Căn cứ | Vì sao giống B [I] | Khác B [I] |
|---|---|---|---|
| W10 MagicGeo | §2.2/§3.4; **mở lại PDF arXiv 2502.13855v1** trong lượt này | LLM chuyển đề thành "a set of points and associated constraints"; bộ giải tự viết dùng "the constraints of the formal language as function names" và "traverse each variable" để tìm toạ độ [C]. Đây là "LLM nêu ràng buộc, máy tìm cấu hình" | Bộ giải tìm kiếm, nhiều khả năng là số (bản 2: `UNCLEAR`); hình phẳng; đề đã sửa cho đủ dữ kiện; không vai trò mệnh đề |
| N10 Hilbert-Geo | §3.1–§3.4; **mở lại PDF arXiv 2605.16385** | CDL tách bốn phần: "construction cdl", "text cdl", "image cdl", "goal cdl" (mục tiêu là "a single canonicalized predicate") [C]. Hệ "ensures entities in text cdl and image cdl are declared in construction cdl" [C]. Vậy mục tiêu được tách khỏi giả thiết, gần với vai trò mệnh đề của B | Engine giải số đo bằng định lý, không dựng toạ độ; không neo span |
| W07 FormalGeo | §2.2: CDL gồm "construction statements, condition statements, and goal statements" [C]; solver kiểm hợp lệ đầu vào theo định nghĩa vị từ [C] | Tách giả thiết/mục tiêu + kiểm định nghĩa trước suy diễn | Hình phẳng, suy diễn định lý |
| W04 Inter-GPS | §2.2: văn bản → literal (91 vị từ) → bộ giải ký hiệu [C] | Biểu diễn khai báo + bộ giải tất định | Parser theo luật (regex), không phải LLM; mục tiêu giải số đo |
| N05 CRANE | §3.1: LLM phát biểu thức ký hiệu, Z3 kiểm [C] | Biểu diễn khai báo, biến ký hiệu | Số học, ràng buộc ở mức token |
| W02 AlphaGeometry | §3.5: "LM đề xuất dựng phụ + DD/AR" [C] | Engine ký hiệu quyết định; mô hình chỉ đề xuất | Đề đã ở ngôn ngữ chuyên dụng, không đọc văn bản tự nhiên |

### 2.3 Gần với phần planner của B (không có LLM)

| Mã | Căn cứ | Vì sao [I] |
|---|---|---|
| W01 GeoSynth | §3.5: tổng hợp chương trình thước-compa từ đặc tả logic, thư viện mở rộng theo chương sách [C] | Bộ tổng hợp tự tìm chuỗi dựng từ quan hệ, đúng vai planner của B. Tiền lệ "thư viện cơ bản vs mở rộng" ~ mở rộng định nghĩa |
| H07–H10 (mục 3) | Văn liệu GCS và lập kế hoạch dựng | Nền lý thuyết cho "biên dịch quan hệ thành phép dựng" và cho câu hỏi thiếu/thừa ràng buộc |

### 2.4 Áp cho cả hai nhánh

- **N04 Agent-Sentry, W22 SpanBasedSP, W25 LangExtract:** neo nguồn/span áp cho lời gọi (A) và cho dữ kiện (B) như nhau.
- **N08 Dr.Spider, N09 GSM-Plus, N11 DynaSolidGeo:** phương pháp dựng bộ diễn đạt lại / thiếu dữ kiện cho phép đo A/B.

**Tóm tắt ánh xạ [I].** Phía hình học có cả hai dạng: A (W11, W12) và B (W10, N10, W07, W04). Nhưng mỗi công trình chỉ hiện
thực **một** dạng, trên dữ liệu và mô hình riêng. Trong tập đọc của bản 2 không có cặp A/B nào cùng mô hình, cùng bài.

---

## 3. Công trình mới H01–H10

### 3.1 Định danh

| Mã | Công trình | Năm | DOI / URL | Venue | Mức xác minh | Nhóm |
|---|---|---|---|---|---|---|
| H01 | Ye, Chen, Dillig, Durrett — SatLM: Satisfiability-Aided Language Models Using Declarative Prompting | 2023 | DOI 10.48550/arXiv.2305.09656 (arXiv v3) | NeurIPS 2023 (comments arXiv) | VERIFIED_PRIMARY | (a) |
| H02 | He-Yueya, Poesia, Wang, Goodman — Solving Math Word Problems by Combining Language Models With Symbolic Solvers | 2023 | DOI 10.48550/arXiv.2304.09102 (v1) | preprint (PDF ghi "Preprint.") | VERIFIED_PRIMARY | (a) |
| H03 | Liu, Jiang, Zhang, Liu, Zhang, Biswas, Stone — LLM+P: Empowering Large Language Models with Optimal Planning Proficiency | 2023 | DOI 10.48550/arXiv.2304.11477 (v3) | preprint (comments: NR) | VERIFIED_PRIMARY | (a)(d) |
| H04 | Pan, Albalak, Wang, Wang — Logic-LM: Empowering Large Language Models with Symbolic Solvers for Faithful Logical Reasoning | 2023 | DOI 10.48550/arXiv.2305.12295 (v2) | Findings of EMNLP 2023 (comments arXiv) | VERIFIED_PRIMARY | (a) |
| H05 | Olausson, Gu, Lipkin, Zhang, Solar-Lezama, Tenenbaum, Levy — LINC: A Neurosymbolic Approach for Logical Reasoning by Combining Language Models with First-Order Logic Provers | 2023 | DOI 10.48550/arXiv.2310.15164 (v2) | EMNLP 2023 Main (comments arXiv) | VERIFIED_PRIMARY | (a) |
| H06 | Jambor, Bahdanau — LAGr: Label Aligned Graphs for Better Systematic Generalization in Semantic Parsing | 2022 (v2) | DOI 10.48550/arXiv.2110.07572 | preprint (comments: NR). Tiêu đề trên trang arXiv ("Labeling Aligned Graphs for Improving…") khác tiêu đề PDF | VERIFIED_PRIMARY | (c) |
| H07 | Hoffmann, Lomonosov, Sitharam — Decomposition Plans for Geometric Constraint Systems, Part I: Performance Measures for CAD | 2001 | DOI 10.1006/jsco.2000.0402 (in trên header PDF); https://www.cs.purdue.edu/cgvlab/www/resources/papers/Hoffmann-Journal_of_Symbolic_Computation-2001-Decomposition_Plans_Geometric_Constraint_System_part_I.pdf | J. Symbolic Computation 31, 367–408 (header PDF) | VERIFIED_PRIMARY (bản PDF trên trang nhóm tác giả) | (b) nền tảng |
| H08 | Jermann, Trombettoni, Neveu, Mathis — Decomposition of Geometric Constraint Systems: a Survey | 2006 | DOI: NR; https://hal.science/hal-00481267 | International Journal of Computational Geometry & Applications (header PDF; tập/trang: NR) | VERIFIED_PRIMARY (bản tác giả nộp HAL, dàn trang "WSPC/Guidelines") | (b)(d) nền tảng |
| H09 | Zou, Tang, Feng, Gao, Zhou, Liu — A review on geometric constraint solving | 2022 | DOI 10.48550/arXiv.2202.13795 (v2) | preprint (header PDF còn để "XXXXX, 202X") | VERIFIED_PRIMARY | (b) |
| H10 | Marinković, Janičić — Towards Understanding Triangle Construction Problems | 2012 | DOI 10.48550/arXiv.1207.4432 (v1) | preprint (comments và PDF: NR) | VERIFIED_PRIMARY | (d) nền tảng |

H07, H08, H10 có trước 2015. Chúng được giữ vì là nền tảng (định nghĩa thiếu/đủ/thừa ràng buộc, DR-plan, tìm chuỗi dựng) và
đã mở toàn văn.

### 3.2 Năm cột cho từng công trình

**H01 SatLM.**

- *Phương pháp [C]:* chia lời giải thành "parsing, planning, and execution". LLM chỉ "parse an NL input into a declarative task
  specification (a set of logical constraints)". SAT/SMT solver làm planning + execution. So với PROGLM (PAL-like) dùng
  "the same exemplar sets" để công bằng. Mô hình chính code-davinci-002; có thêm gpt-3.5-turbo, text-davinci-003,
  code-davinci-001.
- *Số đo [C]:*
  - Bảng 1 (greedy), GSM-SYS: SATLM 69,4 so với PROGLM 43,4. GSM: 71,8 so với 72,7 ("on par").
  - Bảng 5 ghi PROGLM GSM-SYS là 43,3 ⇒ lệch 0,1 với Bảng 1, `UNCLEAR`.
  - Selective accuracy "especially on GSM-SYS (77% vs 45%)".
  - Phản hồi solver có ba loại: ERROR, UNSAT ("conflicting formulas"), AMBIG ("existence of multiple feasible solutions").
    "Unlike the executor used in PROGLM that can only detect errors in code execution, SAT solver can spot UNSAT and AMBIG".
  - Ablation tách hai thành phần: chỉ khai báo, giải bằng CoT (SATCOTSOLVER) đã hơn COT 7,9 và 8,1 điểm trên GSM-SYS và
    CLUTRR.
- *B kế thừa được [I]:*
  - Khung tách "parsing" khỏi "planning" để đặt tên chính xác cái B chuyển sang mã.
  - **Ablation ba nhánh** để tách hiệu ứng: (A) mô hình chọn hàm; (B′) mô hình trích dữ kiện rồi **chính mô hình** chọn hàm từ
    dữ kiện; (B) dữ kiện + planner. Thiếu B′ thì không biết lợi/hại đến từ "cách nói khai báo" hay từ "planner tất định".
  - Thước selective accuracy và coverage cho từ chối fail-closed.
- *Hạn chế bài xác nhận [C]:*
  - "The NL description of some problems may already be more compatible with an imperative solving procedure, and our approach
    is likely to be less effective in these cases (e.g., SATLM slightly lags PROGLM on GSM)".
  - Kế thừa giới hạn diễn đạt và chi phí của solver.
  - Chỉ một vòng, không sửa theo UNSAT/AMBIG.
- *Chưa kiểm trong tập đọc:*
  - Hình học, dựng hình.
  - Đầu ra function calling gốc.
  - Số token: chỉ có log-likelihood ở Bảng 4; token/bài là `NR`.
  - GSM-SYS là tập con chọn theo lời giải có hệ phương trình, nên có thể ưu ái biểu diễn khai báo [I].

**H02 He-Yueya et al. (preprint).**

- *Phương pháp [C]:* LLM "incrementally formalize word problems as variables and equations"; SymPy giải. So với PAL và CoT trên
  cùng Codex (code-davinci-002), "top-1 decoding and a temperature of 0", "max_tokens to be 600".
- *Số đo [C], chỉ lấy từ lời văn vì Bảng 2 bị trích lệch:*
  - "comparable accuracy to the original PAL on GSM8K and improves over PAL by an absolute 20%" trên ALGEBRA (222 bài).
  - Trên GSM8K: "PAL outperforms DECLARATIVE across both sets of comparable examples".
  - Bắt LLM tự giải hệ phương trình thay SymPy: "dramatic drop in accuracy (from 69.4% to 22.4%)".
  - Bản tăng dần hơn bản "ONE-STEP".
- *B kế thừa được [I]:*
  - Bằng chứng cùng mô hình rằng khai báo + bộ giải tất định **không** thắng đều: thua trên bài thủ tục, thắng trên bài cần
    lập luận khai báo.
  - Gợi ý trích dữ kiện **theo từng mệnh đề, tăng dần** thay vì một lượt.
- *Hạn chế bài xác nhận [C]:* bài chỉ có phần Kết luận, không có mục Limitations riêng. Bài tự nêu thua PAL trên GSM8K ở các cặp
  ví dụ so được.
- *Chưa kiểm:* hình học; số token thực dùng (`NR`); phân loại lỗi định lượng (`NR`).

**H03 LLM+P (preprint).**

- *Phương pháp [C]:* LLM dịch mô tả bài sang **problem PDDL**. **Domain PDDL do người cung cấp**. Planner cổ điển (Fast Downward)
  tìm kế hoạch. Giả định: "A domain PDDL is provided to define the actions that the robot is capable of". GPT-4, nhiệt độ 0.
- *Số đo [C]:*
  - "LLM+P produces an optimal plan for the majority of problems".
  - "Most failed cases are due to mis-specified problem files, such as missing one of the initial conditions … causing the
    planning problem to be unsolvable".
  - Không có ví dụ ngữ cảnh: "LLMs fail to produce correct problem PDDL files".
  - Ví dụ GPT-4 không ngữ cảnh: đúng cú pháp nhưng "uses a made-up predicate (empty) and misses the initial condition".
  - Bảng I bị trích lệch cột ⇒ số theo từng miền là `UNCLEAR`.
- *B kế thừa được [I]:*
  - Cấu trúc gần B nhất ngoài hình học: miền hành động cố định do người viết (≈ registry 24 hàm + luật planner); mô hình chỉ
    điền "trạng thái đầu + mục tiêu" (≈ dữ kiện có vai trò).
  - Kiểu lỗi chính đã biết trước: **thiếu dữ kiện** và **vị từ bịa**. B cần đo đúng hai kiểu này.
- *Hạn chế bài xác nhận [C]:* "we do not ask the LLM to recognize that it has been posed a prompt that is suitable for processing
  using the proposed LLM+P pipeline"; phụ thuộc thông tin do người cung cấp.
- *Chưa kiểm:* nhánh "LLM phát kế hoạch dạng lời gọi hành động thực thi được + bộ kiểm" (tương đương A). Đối chứng của bài là
  LLM-AS-P bằng ngôn ngữ tự nhiên, không phải lời gọi có kiểu. Token: `NR`.

**H04 Logic-LM (Findings of EMNLP 2023).**

- *Phương pháp [C]:* Problem Formulator (LLM) → biểu diễn ký hiệu (LP, FOL, CSP, SAT) → solver tất định. Self-Refiner sửa theo
  "the error messages from the symbolic solver".
- *Số đo [C]:*
  - Trung bình hơn standard prompting 39,2% và hơn CoT 18,4%.
  - GPT-4 có Exe_Rate gần 100% trên bộ tổng hợp, nhưng 79,9% (FOLIO) và 32,6% (AR-LSAT).
  - Self-refinement tăng Exe_Rate trung bình 5,01. Nhưng "the accuracy tends to stagnate in subsequent rounds, even though the
    Exe_Rate continues to increase", vì "a valid symbolic representation does not necessarily equate to a 'correct' problem
    formulation".
  - Ví dụ lỗi: mô hình "fails to distinguish between the meanings of 'below' and 'above'".
- *B kế thừa được [I]:*
  - Tách hai thước: "dữ kiện hợp lệ cú pháp" và "dữ kiện đúng nghĩa".
  - Vòng sửa theo thông điệp lỗi chỉ sửa được lỗi hợp lệ, không sửa được lỗi nghĩa. Lỗi **đảo chiều quan hệ** (trên/dưới ~
    vai trò đỉnh/chân, đường/mặt) là kiểu lỗi trích dữ kiện cần đăng ký trước.
- *Hạn chế bài xác nhận [C]:* phạm vi bị giới hạn bởi "the expressiveness of the symbolic solver"; khó với "logical
  representations with intricate grammar".
- *Chưa kiểm:* so với nhánh chương trình (PAL) — đối chứng là Standard/CoT; hình học; token.

**H05 LINC (EMNLP 2023).**

- *Phương pháp [C]:* LLM làm "semantic parser" dịch tiền đề + kết luận sang FOL. Prover9 suy diễn. Bỏ phiếu đa số K=10.
- *Số đo [C]:*
  - Phân tích lỗi GPT-4 trên FOLIO cho thấy LINC và CoT "have completely different failure modes".
  - Lỗi của LINC:
    - L1 "FOL fails to capture implicit information not mentioned in the premises";
    - L2 "fails to capture information explicitly mentioned … due to the choice of representation";
    - L3 lỗi cú pháp ở 38% (StarCoder+), 24% (GPT-3.5), 13% (GPT-4) các lần sinh, phổ biến nhất là một ký hiệu dùng với nhiều
      arity.
  - Precision True/False: LINC 93% so với CoT 81%. Recall: 60% so với 75%.
  - Trong 74 mẫu ít nhất một phương pháp sai, chỉ 21 mẫu cả hai cùng sai.
- *B kế thừa được [I]:*
  - Dự báo **dịch chuyển kiểu lỗi** chứ không phải "ít lỗi hơn": nhánh khai báo + bộ máy tất định thường **chính xác hơn khi trả
    lời nhưng trả lời ít hơn**, và hỏng do **bỏ sót dữ kiện ngầm**.
  - Với B, dữ kiện ngầm chính là phần mở rộng định nghĩa ("hình chóp đều" ⇒ đáy đều + chân đường cao là tâm). Lỗi kiểu L1 sẽ rơi
    vào planner nếu thiếu luật mở rộng, hoặc vào mô hình nếu nó không gắn nhãn khái niệm.
- *Hạn chế bài xác nhận [C]:*
  - Phạm vi hẹp (đúng/sai/không xác định của một kết luận).
  - Chi phí API và bỏ phiếu đa số.
  - "it is unclear if this result also holds true in similar scenarios, such as the ones considered in PAL …, Logic-LM, and
    SATLM".
- *Chưa kiểm:* so với nhánh chương trình; hình học; token cụ thể (`NR`).

**H06 LAGr (preprint).**

- *Phương pháp [C]:* sinh biểu diễn nghĩa trực tiếp dưới dạng **đồ thị căn theo vị trí từ của câu vào** ("multi-layer
  input-aligned graph"). Gán nhãn nút/cạnh độc lập. Bản "weakly-supervised" suy ra phép căn bằng MAP xấp xỉ (Hungarian).
- *Số đo [C]:* cải thiện tổng quát hoá hệ thống so với seq2seq trên COGS và CFQ. Trên COGS, mô hình tốt nhất "already predict
  node labels perfectly". Lỗi còn lại nằm ở cạnh (tác giả đề xuất điều kiện hoá cạnh theo nút).
- *B kế thừa được [I]:*
  - Tiền lệ cho "dữ kiện = đồ thị (đối tượng, quan hệ) mà mỗi nút neo vào vị trí trong câu". Đó là hình dạng của Typed Facts có
    trích dẫn.
  - Gợi ý đo **riêng** lỗi nhận đối tượng (nút) và lỗi quan hệ (cạnh).
- *Hạn chế bài xác nhận [C]:* cần dữ liệu huấn luyện (giám sát mạnh hoặc yếu). Thuật toán suy ra phép căn là xấp xỉ.
- *Chưa kiểm:* LLM prompt (không huấn luyện); hình học; trích dẫn nhiều khúc không liền (xem W22 ở bản 2).

**H07 Hoffmann, Lomonosov, Sitharam 2001.**

- *Phương pháp [C]:* hình thức hoá bài toán lập **DR-plan** (decomposition–recombination). Lặp: tìm hệ con nhỏ giải được → giải
  → gộp lại. Kế hoạch được lập "a priori … without access to the algebraic solver". Định nghĩa:
  - "An underconstrained system is not solvable, i.e. its set of real zeroes is not discrete";
  - well-constrained = giải được và bỏ bất kỳ ràng buộc nào thì thành thiếu;
  - overconstrained = vẫn giải được khi bỏ một ràng buộc.
- *Điểm liên quan trực tiếp [C]:*
  - "whenever a subsystem … has no real solutions, then the solution process would have to immediately halt and inform the
    designer".
  - Một hệ con được phân tích bậc tự do coi là giải được vẫn "may, in a degenerate case, turn out to be underconstrained or have
    infinitely many solutions".
  - "inferred or understood constraints are often added to an incomplete constraint specification at the discretion of the CAD
    system".
- *B kế thừa được [I]:*
  - Từ vựng chuẩn để phân loại đầu ra của planner: thiếu / đủ / thừa nhất quán / thừa mâu thuẫn ràng buộc.
  - Câu hỏi thiết kế: ràng buộc do planner **tự thêm** (mở rộng định nghĩa, bố cục `LAYOUT_DERIVED`) phải được ghi tách khỏi
    ràng buộc của đề, như "understood constraints" ở CAD.
  - Fail-closed khi vô nghiệm thực.
- *Hạn chế bài xác nhận [C]:* phân tích theo đồ thị ràng buộc ước lượng "generic solvability". Có "solvable, even minimal dense
  graphs whose corresponding systems are not generically solvable".
- *Chưa kiểm:* văn bản tự nhiên; hình học giáo dục; số học chính xác. Phần II (thuật toán mới) **không mở** ⇒ `NOT_VERIFIED`.

**H08 Jermann, Trombettoni, Neveu, Mathis 2006.**

- *Phương pháp [C]:* tổng quan phân rã hệ ràng buộc hình học, chia bốn loại: recursive division, recursive assembly, single-pass
  (maximum matching), propagation of degrees of freedom. Định nghĩa:
  - "well-constrained if Sol(S) is finite, over-constrained if Sol(S) = ∅ and under-constrained if Sol(S) is infinite";
  - "well-constrained modulo G" khi tập quỹ đạo Sol(S)/G hữu hạn (G là nhóm dời hình).
- *Điểm liên quan trực tiếp [C]:*
  - Đặc trưng theo mẫu/luật dựng "generally … correct", nhưng "necessarily incomplete because no finite repertoire of patterns
    can cover every well-constrained component".
  - Độ cứng cấu trúc "is only an approximate characterization", với phản ví dụ "double-banana" (cấu trúc đủ ràng buộc nhưng thực
    ra thừa).
  - Đặc trưng cấu trúc "does not handle correctly projective and other boolean constraints such as incidences and
    parallelisms".
  - Kết luận đề xuất dùng "predefined guarded patterns" cùng một kiểm tra đủ ràng buộc tổng quát.
- *B kế thừa được [I]:*
  - Planner của B là một **repertoire mẫu có điều kiện** (luật mở rộng định nghĩa + chọn hàm theo kiểu quan hệ). Văn liệu GCS nói
    trước: cách này đúng khi khớp nhưng **không đầy đủ** ⇒ phải đo tỉ lệ "không có luật", không được coi là lỗi mô hình.
  - Khung affine + metric Gram của AlgoSim tương ứng với cố định nhóm G: chỉ "đủ ràng buộc modulo đồng dạng/dời hình". Khi kiểm
    "bài có xác định duy nhất hình không", phải nói rõ **modulo nhóm nào**.
  - Đếm bậc tự do không đủ để kết luận thiếu/thừa khi có song song/liên thuộc. Mà hình không gian lớp 11–12 đầy quan hệ loại này.
- *Hạn chế bài xác nhận [C]:* "Among the methods classified in the proposed four categories, none satisfies all these
  requirements simultaneously".
- *Chưa kiểm:* đầu vào ngôn ngữ tự nhiên; LLM; số học chính xác hữu tỉ + căn.

**H09 Zou et al. 2022 (preprint).**

- *Phương pháp [C]:* tổng quan GCS trong CAD tham số, nhấn mạnh 15 năm gần đây. Hệ do người viết "usually contains under- and
  over-constrained parts, and … such parts must be correctly detected and resolved before numerical solving can work". Phân
  biệt "consistently over-constrained" và "inconsistently over-constrained". Phương pháp theo luật mã hoá "an axiomatic
  description of elementary geometry for ruler-and-compass construction" thành luật viết lại.
- *Điểm liên quan [C]:* với cách theo luật, "the main difficulty … lies in a complete repertoire of patterns". Witness
  configuration method (WCM) có giới hạn được thảo luận riêng (§6).
- *B kế thừa được [I]:*
  - Phân biệt thừa nhất quán (đề cho dư nhưng đúng: kiểm được) với thừa mâu thuẫn (đề hoặc trích sai: phải từ chối).
  - B kiểm dữ kiện thừa sau dựng, nên tự nhiên phân được hai loại này. A chỉ phân được nếu mô hình phát cả lời gọi kiểm.
- *Hạn chế bài xác nhận [C]:* tiêu chí trạng thái ràng buộc "restricted in specific geometries … and constraints"; WCM có các
  "Limitation 0/I/II".
- *Chưa kiểm:* LLM; đầu vào văn bản; hình học giáo dục.

**H10 Marinković, Janičić 2012 (preprint).**

- *Phương pháp [C]:* tách tri thức thành "definitions, lemmas (geometry properties), and construction primitives". Tìm chuỗi dựng
  theo kiểu thác nước: áp primitive khi mọi tiền đề đã dựng, dừng khi dựng được mọi điểm mục tiêu. Chỉ dựng đối tượng có xuất
  hiện trong định nghĩa/bổ đề để thu hẹp tìm kiếm.
- *Số đo và nhận xét [C]:*
  - "the program can solve 58 Wernick's problems, each in less than 1s".
  - Chuỗi sạch dài nhất 11 bước.
  - Duy trì "non-degeneracy conditions".
  - "for problems with several different solutions, the one found by the system depends on the order of available primitive
    constructions/definitions/lemmas".
  - Dùng 67 luật dựng cấp cao thì tìm không khó: "what is problematic is how to represent the underlying geometry knowledge".
- *B kế thừa được [I]:*
  - Planner hướng mục tiêu, tất định, có **điều kiện không suy biến** gắn với từng bước. Đó là tiền điều kiện của hàm registry.
  - Cảnh báo: kết quả phụ thuộc **thứ tự luật**. Planner B phải cố định thứ tự và có test chứng minh đầu ra không đổi khi hoán vị
    dữ kiện vào.
- *Hạn chế bài xác nhận [C]:* một họ bài (dựng tam giác từ ba điểm đặc biệt); còn bài giải được mà chương trình chưa giải (liệt
  kê 14 bài).
- *Chưa kiểm:* hình không gian; đầu vào ngôn ngữ tự nhiên; LLM. Các bản kế tiếp (ArgoTriCS, LNCS 2023; EPTCS 398) chỉ thấy qua
  kết quả tìm ⇒ `NOT_VERIFIED`.

### 3.3 Thấy trong kết quả tìm nhưng không dùng (`NOT_VERIFIED`)

- Hoffmann, Lomonosov, Sitharam, Part II (JSC 2001).
- ArgoTriCS (Marinković, LNCS 13900, 2023).
- Marinković, Šukilović, Marić (EPTCS 398).
- Luận án Marinković.
- Các công trình chỉ biết qua trích dẫn trong H08/H09: Gao & Zhang 2003; Schreck & Mathis 2006; Owen 1991; Sitharam 2005;
  Hoffmann & Joan-Arinyo 2005 ("A brief on constraint solving").
- Faithful CoT (Lyu et al. 2023), chỉ biết qua H01.

---

## 4. Phân tích khoảng trống

### (i) Có so sánh có kiểm soát "LLM trích dữ kiện + planner tất định" và "LLM phát lời gọi/chương trình thực thi được", cùng mô hình, cùng dữ liệu không?

**CONFIRMED BY SOURCE**

- **Ngoài hình học, có — hai công trình.**
  - H01: cùng mô hình, cùng bộ exemplar. SATLM hơn PROGLM trên đa số bộ dữ liệu. Ngang hoặc thua nhẹ trên GSM (greedy).
  - H02: cùng Codex, nhiệt độ 0. Ngang PAL trên GSM8K, nhưng PAL hơn ở các cặp ví dụ so được. Hơn PAL 20 điểm tuyệt đối trên
    ALGEBRA.
  - Cả hai tự nêu điều kiện: bài có lời giải thủ tục tự nhiên thì nhánh chương trình không thua.
- **Đối chứng khác tuyến:**
  - H04/H05 so nhánh khai báo với Standard/CoT, **không** với chương trình.
  - H03 so với LLM lập kế hoạch bằng ngôn ngữ tự nhiên, **không** với lời gọi hành động có kiểu.
  - H05 tự nêu là chưa rõ kết luận có đúng cho bối cảnh PAL/SatLM không.
- **Trong hình học (mở lại W10):**
  - MagicGeo Bảng 4 có ba nhánh cùng hệ: "w/o Coordinates" (LLM viết thẳng TikZ), "w/o Solver" (LLM tự đoán toạ độ), và LLM
    ràng buộc + bộ giải.
  - CLIP Img-Txt trung bình: 31,00 / 31,51 / 32,65 [C].
  - Không nhánh nào là "LLM chọn hàm dựng từ registry, engine tất định dựng". Thước là CLIP, không phải tính đúng quan hệ.

**INFERENCE**

- Trong tập đọc (bản 1 + bản 2 + H01–H10), **chưa có** thí nghiệm A/B đúng nghĩa của câu hỏi này cho **dựng hình**: cùng mô hình,
  cùng bài, cùng registry, một nhánh mô hình chọn hàm và một nhánh mô hình trích dữ kiện. Đây là khoảng trống trong tập đọc,
  không phải tính mới.
- Bằng chứng ngoài hình học **trái chiều theo loại bài**. Nó không cho dự đoán một chiều cho AlgoSim.
- Nó chuyển sang AlgoSim yếu vì hai lẽ:
  1. Nhánh "chương trình" ở H01/H02 là mã mệnh lệnh tự do. Nhánh A của AlgoSim là lời gọi có kiểu với engine giải phụ thuộc,
     tức đã nửa khai báo.
  2. Mô hình (Codex 2022–2023) khác hẳn Gemini function calling 2026.

**NOT VERIFIED**

- Văn liệu tiếng Việt/Trung về phần mềm giáo dục hình không gian: chưa quét (như bản 2).

### (ii) Mỗi nhánh dịch chuyển kiểu lỗi nào?

**CONFIRMED BY SOURCE**

- **Phía giống A:**
  - Tham chiếu chưa định nghĩa đứng đầu (W11).
  - Truyền biến giữa lời gọi lồng (N02).
  - Lỗi tham số ≈32% tổng lỗi (N03, bảng `UNCLEAR`).
  - Nhầm mục tiêu dựng với mục tiêu số (W12).
  - PROGLM mắc "planning errors (e.g., manipulating equations incorrectly)" (H01).
- **Phía giống B:**
  - Thiếu dữ kiện ngầm (H05 L1).
  - Mất thông tin do chọn biểu diễn (H05 L2).
  - Thiếu điều kiện đầu khiến bài vô nghiệm (H03).
  - Vị từ bịa (H03).
  - Đảo chiều quan hệ "below/above" (H04).
  - Dữ kiện hợp lệ mà sai nghĩa; vòng sửa không chữa được (H04).
  - Lỗi arity (H05 L3).
- **Hình dạng dịch chuyển:**
  - H05: precision cao hơn, recall thấp hơn; ít trùng mẫu sai.
  - H01: trả lời ít hơn nhưng selective accuracy cao hơn.
- **Phía planner (GCS):**
  - Repertoire mẫu không đầy đủ (H08, H09).
  - Kết quả phụ thuộc thứ tự luật (H10).

**INFERENCE**

- Giả thuyết hợp lý từ văn liệu: B **chuyển** lỗi từ "chọn sai hàm / tham chiếu sai / ghép sai" sang hai chỗ. Một là "bỏ sót hoặc
  biểu diễn sai dữ kiện" ở mô hình. Hai là "không có luật" ở planner. Chưa có số cho hình học ⇒ giả thuyết H-AB1.
- Không thấy trong tập đọc phép đo nào riêng cho **lỗi vai trò mệnh đề**: lấy mục tiêu chứng minh làm giả thiết, hoặc bỏ phủ
  định. N10/W07 tách `goal` khỏi giả thiết **về biểu diễn** [C], nhưng không báo tỉ lệ mô hình gán sai vai trò (`NR`).

### (iii) Bằng chứng về khác biệt token/chi phí

**CONFIRMED BY SOURCE**

- H01–H05, H06: số token/bài theo từng nhánh là `NR`.
  - H01 chỉ báo log-likelihood của chuỗi sinh (Bảng 4).
  - H02 chỉ báo trần `max_tokens` 600.
  - H05 chỉ nêu định tính chi phí API và bỏ phiếu đa số.
- Duy nhất trong cả ba lớp: N05 CRANE (bản 2) báo token theo phương pháp, cho biểu thức số học trên mô hình mở ≤32B.

**INFERENCE**

- **Không có bằng chứng** để nói B rẻ hơn hay đắt hơn A. Hai lực ngược chiều:
  - dữ kiện nhỏ hơn lời gọi có đủ tham số ⇒ ít token ra;
  - nhưng B vẫn cần trích dẫn cho từng dữ kiện, cờ vai trò/phủ định/mơ hồ, và có thể cần nhiều mục hơn một lời gọi hợp thành
    (một `pyramid(...)` so với nhiều dữ kiện).
- Đo được rẻ từ trường `usage` của API ⇒ giả thuyết H-AB3.

### (iv) Phát hiện cấu hình thiếu xác định hoặc không duy nhất

**CONFIRMED BY SOURCE**

- **GCS có định nghĩa chín muồi** (H07, H08, H09): thiếu / đủ / thừa nhất quán / thừa mâu thuẫn, và "modulo nhóm G".
- Nhưng mọi đặc trưng rẻ đều có lỗ:
  - Độ cứng cấu trúc chỉ xấp xỉ (double-banana);
  - xử lý sai liên thuộc/song song (H08);
  - đồ thị giải được mà hệ không giải được tổng quát (H07);
  - suy biến làm hệ con "giải được" thành thiếu (H07);
  - WCM có giới hạn riêng (H09).
- **Trong pipeline LLM, chỉ H01 vận hành hoá điều này:**
  - UNSAT và AMBIG ("multiple feasible solutions") được dùng để kiêng trả lời; selective accuracy tăng.
  - Bảng 5 có số AMBIG theo bộ (ví dụ CLUTRR) nhưng bị trích lệch ⇒ `UNCLEAR`.
- H03: thiếu điều kiện đầu khiến planner báo vô nghiệm. Đó là tín hiệu phát hiện được, nhưng bài không đo nó như cơ chế từ chối.
- Bản 2: N09 cho thấy mô hình có thể "hallucinated solution" khi thiếu dữ kiện. MagicGeo (W10) đưa thất bại của bộ giải về LLM.
  Phát hiện nghiệm không duy nhất ở W10: `NR` (tìm "multiple solution", "unique" trên PDF: không thấy).

**INFERENCE**

- B có lợi thế **cấu trúc** cho câu hỏi này: planner thấy toàn bộ tập dữ kiện trước khi dựng. Nó có thể nhận ra "còn một lựa chọn
  tự do không do đề cố định" (khác với lựa chọn bố cục modulo đồng dạng mà khung affine + Gram cố định hợp lệ). Ở A, sự thiếu xác
  định bị che: mô hình chọn hàm nào thì engine dựng hàm đó.
- Nhưng H07/H08 cảnh báo rằng đếm bậc tự do hay khớp mẫu **không** chứng minh được tính duy nhất. Với AlgoSim, cách chắc chắn
  hơn là dựa vào **dựng tường minh**:
  - bước dựng nào phải chọn giữa nhiều nghiệm (giao đường tròn/mặt cầu, hai phía mặt phẳng) thì phải được đề cố định;
  - nếu không, bước đó bị đánh dấu.
  
  Đây là thiết kế cần đo, không phải kết luận từ văn liệu.
- Chưa thấy trong tập đọc công trình nào phát hiện bài **hình không gian bằng ngôn ngữ tự nhiên** thiếu xác định rồi từ chối có lý
  do. Đây là khoảng trống trong tập đọc.

---

## 5. Giả thuyết kiểm chứng được (A và B)

Luật chung (theo bản 2 §5 và luật kho):

- **Đăng ký trước** tập bài, mô hình, `k`, nhiệt độ, ngân sách, luật dừng và danh mục lỗi.
- Mọi lượt gọi mô hình thật cần **quyết định của người dùng** trước.
- Cùng mô hình, cùng phiên bản, cùng bộ bài, cùng `k` mẫu/bài, cùng nhiệt độ. Cùng bộ ví dụ minh hoạ, viết lại cho từng định
  dạng đầu ra như H01 làm.
- Bộ bài gồm:
  - cặp diễn đạt lại có chuyên gia kiểm giữ nghĩa (N08);
  - bài thiếu dữ kiện / ngoài phạm vi (N09);
  - bài có mệnh đề cần chứng minh và mệnh đề phủ định;
  - **không** sửa đề cho đủ dữ kiện (khác MagicGeo).
- Chấm tất định trên đầu ra đã ghi (0 lượt gọi thêm): đối chiếu tập lời gọi/dữ kiện chuẩn và kiểm quan hệ trên cảnh dựng.
- Nên có nhánh phụ **B′** (mô hình trích dữ kiện rồi chính mô hình chọn hàm) để tách "cách nói khai báo" khỏi "planner tất định"
  (H01 §4.3). Thiếu B′ thì khác biệt A/B không quy được về planner.

**H-AB1 — Dịch chuyển kiểu lỗi.**

- *Phát biểu:* so với A, B có tỉ lệ lỗi "chọn sai hàm cho kiểu quan hệ / tham chiếu chưa định nghĩa / mở rộng định nghĩa sai"
  thấp hơn. Đổi lại, B có tỉ lệ "bỏ sót dữ kiện / sai vai trò mệnh đề / không có luật planner" cao hơn.
  - Cơ sở: W11, N02 cho phía A; H03, H04, H05, H08 cho phía B.
- *Bác bỏ khi:*
  - (a) tỉ lệ lỗi nhóm thứ nhất của B **không** thấp hơn A quá biên đăng ký trước; **hoặc**
  - (b) tỉ lệ lỗi nhóm thứ hai của B **không** cao hơn A.
  - (a) bác bỏ lợi ích; (b) bác bỏ dự báo về cái giá.
- *Đo tối thiểu:* N bài × k mẫu × 2 nhánh. Phân loại lỗi theo danh mục đăng ký trước. Gán nhãn bằng diff tất định với tập chuẩn
  của từng bài. Báo theo từng loại, kèm khoảng tin cậy bootstrap.

**H-AB2 — Kiêng trả lời có chọn lọc trên bài thiếu/không duy nhất.**

- *Phát biểu:* B (kiểm tập dữ kiện trước và sau dựng: mâu thuẫn, mục tiêu chứng minh không thoả, phủ định không sai, bước dựng có
  lựa chọn tự do không được cố định) đạt **selective accuracy** cao hơn A, và **tỉ lệ từ chối đúng** trên bài thiếu dữ kiện cao
  hơn A. Coverage có thể thấp hơn.
  - Cơ sở: H01 UNSAT/AMBIG; H07–H09.
- *Bác bỏ khi:*
  - selective accuracy của B không vượt A quá biên đăng ký trước; **hoặc**
  - trên tập bài thiếu dữ kiện, tỉ lệ từ chối đúng của B không cao hơn A; **hoặc**
  - B mất coverage trên bài **đủ** dữ kiện quá trần đăng ký trước, tức từ chối oan.
- *Đo tối thiểu:* cùng N × k. Mỗi lần chạy có một trong sáu kết cục đã đăng ký: phục vụ đúng / phục vụ sai / từ chối đúng / từ chối
  oan / ngoài phạm vi / hạ tầng. Tính coverage và selective accuracy theo H01.

**H-AB3 — Token đầu ra.**

- *Phát biểu:* trung vị token đầu ra/bài của B **không** cao hơn A.
  - Văn liệu không có số (mục 4-iii). Đây là giả thuyết đo, không phải dự đoán có căn cứ.
- *Bác bỏ khi:* trung vị token đầu ra/bài của B cao hơn A quá ngưỡng đăng ký trước (ví dụ 10%) trên cùng tập bài.
  - Nếu B rẻ hơn nhưng phục vụ đúng thấp hơn (H-AB1/H-AB2), báo cả hai; không gộp thành một điểm.
- *Đo tối thiểu:* lấy `usage` (token vào/ra) của API cho cùng N × k lượt mỗi nhánh. Báo riêng token khai báo hàm/schema (đầu vào
  cố định) và token đầu ra. Không đổi `MAX_OUTPUT_TOKENS` giữa hai nhánh.

---

## 6. Danh mục tham khảo (H01–H10)

| Mã | Tham khảo | Mức xác minh |
|---|---|---|
| H01 | Ye, X., Chen, Q., Dillig, I., Durrett, G. (2023). SatLM: Satisfiability-Aided Language Models Using Declarative Prompting. NeurIPS 2023 (theo comments arXiv). arXiv:2305.09656 (v3). DOI 10.48550/arXiv.2305.09656 | VERIFIED_PRIMARY |
| H02 | He-Yueya, J., Poesia, G., Wang, R. E., Goodman, N. D. (2023). Solving Math Word Problems by Combining Language Models With Symbolic Solvers. Preprint, arXiv:2304.09102 (v1). DOI 10.48550/arXiv.2304.09102 | VERIFIED_PRIMARY |
| H03 | Liu, B., Jiang, Y., Zhang, X., Liu, Q., Zhang, S., Biswas, J., Stone, P. (2023). LLM+P: Empowering Large Language Models with Optimal Planning Proficiency. Preprint, arXiv:2304.11477 (v3). DOI 10.48550/arXiv.2304.11477 | VERIFIED_PRIMARY |
| H04 | Pan, L., Albalak, A., Wang, X., Wang, W. Y. (2023). Logic-LM: Empowering Large Language Models with Symbolic Solvers for Faithful Logical Reasoning. Findings of EMNLP 2023 (theo comments arXiv). arXiv:2305.12295 (v2). DOI 10.48550/arXiv.2305.12295 | VERIFIED_PRIMARY |
| H05 | Olausson, T. X., Gu, A., Lipkin, B., Zhang, C. E., Solar-Lezama, A., Tenenbaum, J. B., Levy, R. (2023). LINC: A Neurosymbolic Approach for Logical Reasoning by Combining Language Models with First-Order Logic Provers. EMNLP 2023 Main (theo comments arXiv). arXiv:2310.15164 (v2). DOI 10.48550/arXiv.2310.15164 | VERIFIED_PRIMARY |
| H06 | Jambor, D., Bahdanau, D. (2022). LAGr: Label Aligned Graphs for Better Systematic Generalization in Semantic Parsing. Preprint (venue NR trên trang arXiv/PDF), arXiv:2110.07572 (v2). DOI 10.48550/arXiv.2110.07572 | VERIFIED_PRIMARY |
| H07 | Hoffmann, C. M., Lomonosov, A., Sitharam, M. (2001). Decomposition Plans for Geometric Constraint Systems, Part I: Performance Measures for CAD. *J. Symbolic Computation* 31, 367–408. DOI 10.1006/jsco.2000.0402 | VERIFIED_PRIMARY |
| H08 | Jermann, C., Trombettoni, G., Neveu, B., Mathis, P. (2006). Decomposition of Geometric Constraint Systems: a Survey. *International Journal of Computational Geometry & Applications* (header PDF; tập/trang NR). Bản tác giả: https://hal.science/hal-00481267. DOI: NR | VERIFIED_PRIMARY |
| H09 | Zou, Q., Tang, Z., Feng, H.-Y., Gao, S., Zhou, C., Liu, Y. (2022). A review on geometric constraint solving. Preprint, arXiv:2202.13795 (v2). DOI 10.48550/arXiv.2202.13795 | VERIFIED_PRIMARY |
| H10 | Marinković, V., Janičić, P. (2012). Towards Understanding Triangle Construction Problems. Preprint, arXiv:1207.4432 (v1). DOI 10.48550/arXiv.1207.4432 | VERIFIED_PRIMARY |

**Thống kê lượt này.**

- Mới: 10 công trình, cả 10 `VERIFIED_PRIMARY`. 0 `VERIFIED_ABSTRACT_ONLY`. 0 mục mới dùng làm bằng chứng ở mức `NOT_VERIFIED`.
- Các mục `NOT_VERIFIED` ở §3.3 bị loại.
- Mở lại để xác nhận ánh xạ: W10 (MagicGeo, PDF v1) và N10 (Hilbert-Geo, PDF). Mức xác minh không đổi (`VERIFIED_PRIMARY`).
  Nội dung bản 2 không bị đính chính; chỉ thêm hai trích dẫn ở §2.2 (Bảng 4 của W10, cấu trúc bốn phần CDL của N10).
