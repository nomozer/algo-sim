# Ma trận văn liệu và khoảng trống, bản 2: tuyến AI chọn hàm hình học có neo nguồn

Ngày tìm và đọc: 2026-10-10. Tài liệu nghiên cứu cho run `ai-function-route`. Nó **không** mô tả trạng thái hệ thống và
**không** tuyên bố tính mới của AlgoSim.

**Quan hệ với bản 1.** Bản 1 (`docs/evaluation/geometry/runs/text-to-geometry-functions/LITERATURE_GAP_MATRIX.md`, 26 công
trình, mã W01–W26) là artifact run **bất biến** và không bị sửa. Bản 2 là một lớp mới, gồm ba phần:

1. Nâng mức xác minh của các công trình gần nhất, từ tóm tắt lên toàn văn, và ghi lại toàn văn thêm hoặc đính chính gì so với
   hàng tương ứng ở bản 1 (mục 2).
2. Thêm 11 công trình mới, mã N01–N11 (mục 3).
3. Phân tích khoảng trống (a)–(e) và đề xuất ablation (mục 4–5).

Một nhận định của bản 1 bị đính chính thì chỗ đính chính nằm ở đây. Người trích phải dùng bản 2 cho mục đó.

## 0. Quy ước

- `[C]` CONFIRMED BY SOURCE: nội dung có trong văn bản nguồn đã mở.
- `[I]` INFERENCE: suy luận của người tổng hợp, không phải lời tác giả.
- `[NV]` NOT VERIFIED: chưa kiểm được trên nguồn gốc.
- `NR`: không thấy trong phần nguồn đã đọc. `NR` **không** có nghĩa là "không có". `UNCLEAR`: nguồn có nói nhưng mơ hồ hoặc
  tự mâu thuẫn.
- Mức xác minh:
  - `VERIFIED_PRIMARY`: đã mở toàn văn và nhận định nằm trong đó.
  - `VERIFIED_ABSTRACT_ONLY`: chỉ đọc trang tóm tắt.
  - `NOT_VERIFIED`: không mở được hoặc chỉ thấy trong kết quả tìm. Mục loại này **không** dùng làm bằng chứng.
- Bài arXiv chưa có venue ghi trên trang nguồn được ghi là `preprint`. Venue chỉ ghi khi trang arXiv (comments), PDF (header)
  hoặc trang nhà xuất bản nêu rõ, và có ghi nguồn của thông tin venue.
- DOI chỉ ghi khi thấy trên trang nguồn. Mọi bài arXiv có DOI do arXiv cấp, dạng `10.48550/arXiv.<id>`; mã này đã thấy trên
  từng trang tóm tắt arXiv mở trong lượt này. Không DOI nào được suy đoán.

**Cách lấy văn bản và độ tin của trích dẫn (phải khai).**

- Lượt này tải **PDF gốc** (arXiv `/pdf/<id>`, ACL Anthology, kho PDF của PMLR trên GitHub) rồi trích chữ bằng `pdftotext
  -layout`. Câu trong ngoặc kép ở dưới được chép từ văn bản trích thô đó, **không** qua bước tóm tắt. Bản 1 thì đọc qua công cụ
  tải trang có tóm tắt tự động.
- Chế độ `-layout` trộn cột và bảng. Có ít nhất một bảng bị lệch cột (GeoBuildBench Table 1, xem mục 2). Một số ký tự toán bị
  mất, ví dụ `∠`, `⊥`.
- Ba bài (GeoBuildBench, MagicGeo, SolidGeo) được đọc lượt đầu qua công cụ tóm tắt `WebFetch`, chỉ để định hướng. Mọi con số và
  câu trích dùng ở đây đều đã tìm lại trong văn bản trích thô.
- **Trước khi đưa vào chương khoá luận, mọi câu trích phải đối chiếu lại với PDF gốc và ghi số trang/mục.** Luật này áp dụng cả
  cho các câu trong bản 1 lấy qua công cụ tóm tắt.
- Số trang trong ngoặc như `(tr. 6781)` là số in trên trang PDF.

**Ranh giới lập luận.**

- Không suy ra tính mới của AlgoSim từ việc bài báo vắng một tính năng.
- Không dùng kết quả pilot LLM_ONLY cũ (0/10) làm bằng chứng kiến trúc mới tốt hơn.
- Các hướng "compact DSL, FactGraph, constrained decoding, compiler-in-the-loop, semantic normalization" được đánh giá như
  **ứng viên**, không mặc định là cần thiết.

---

## 1. Phạm vi và phương pháp tìm

**Truy vấn** (công cụ tìm web, 2026-10-10). Sau mỗi truy vấn, mở trực tiếp PDF/trang gốc:

1. `function calling arguments grounded in source text span verification LLM tool use hallucinated arguments arXiv`
2. `Berkeley Function Calling Leaderboard BFCL paper ICML 2025 multiple parallel function calls evaluation AST`
3. `LLM solid geometry symbolic edge length "a" automated solver coordinate method pyramid problems 2025 arXiv`
4. Tra trực tiếp theo mã arXiv đã biết cho các công trình mà đề bài nêu ví dụ: NESTFUL, API-Bank, Self-Debugging, Dr.Spider,
   GSM-Plus, JSONSchemaBench, CRANE. Mã arXiv nhớ sẵn chỉ là **địa chỉ để mở**. Mọi nhận định lấy từ văn bản đã mở.

**Tiêu chí đưa vào bài mới.**

- Năm 2022–2026.
- Nguồn gốc mở được.
- Trả lời trực tiếp ít nhất một câu hỏi của task: neo nguồn tham số; độ tin cậy gọi hàm nhiều lời/lồng/song song; giải mã ràng
  buộc và cái giá về độ chính xác; sửa lỗi bằng phản hồi thực thi; độ bền với diễn đạt lại; hình học có tham số ký hiệu.
- Trần khoảng 10 bài. Ưu tiên bài có số đo hoặc cơ chế cụ thể.

**Thấy trong kết quả tìm nhưng không dùng (`NOT_VERIFIED`, không làm bằng chứng):**

- ToolLLM/ToolBench (arXiv 2307.16789, không mở).
- GSM-Symbolic (arXiv 2410.05229, không mở; chỉ biết qua cách CRANE dùng nó).
- Blog "Say What You Mean: A Response to 'Let Me Speak Freely'" (W. Kurt), chỉ biết qua JSONSchemaBench trích.
- arXiv 2607.00895 (span-level hallucination detection), RLSeek (ACL 2026), mô hình ToolHACE trên Featherless, GeoVLMath (arXiv
  2510.11020). Tất cả chỉ thấy snippet.

**Giới hạn.**

- Một người, một ngày, chủ yếu tiếng Anh. Không quét văn liệu tiếng Việt/Trung về phần mềm giáo dục hình không gian.
- Không đọc lại W02, W03, W05, W06, W13–W21, W23–W26 (mục 2.3).
- Mọi "khoảng trống" dưới đây chỉ là **khoảng trống trong tập đã đọc**.

---

## 2. Nâng mức xác minh các công trình gần nhất (W-cũ)

### 2.1 Bảng thay đổi mức xác minh

| Mã | Công trình | Mức ở bản 1 | Mức ở bản 2 | Nguồn đã mở ở bản 2 |
|---|---|---|---|---|
| W01 | Gulwani et al. 2011 | VERIFIED_PRIMARY | VERIFIED_PRIMARY (không đổi) | PDF đã đọc ở bản 1, không có gì mới cần thêm |
| W04 | Inter-GPS | VERIFIED_ABSTRACT_ONLY | **VERIFIED_PRIMARY** | PDF ACL Anthology `2021.acl-long.528`, tr. 6774–6786 |
| W07 | FormalGeo | VERIFIED_ABSTRACT_ONLY | **VERIFIED_PRIMARY** (preprint) | PDF arXiv 2310.18021v6 |
| W08 | Geoparsing | VERIFIED_PRIMARY (HTML) | VERIFIED_PRIMARY (PDF, grep có mục tiêu) | PDF arXiv 2604.11600 |
| W09 | SolidGeo | VERIFIED_ABSTRACT_ONLY | **VERIFIED_PRIMARY** (preprint) | PDF arXiv 2505.21177v2 |
| W10 | MagicGeo | VERIFIED_PRIMARY (HTML) | VERIFIED_PRIMARY (PDF đầy đủ) | PDF arXiv 2502.13855v1 |
| W11 | GeoBuildBench | VERIFIED_PRIMARY (~95% HTML) | VERIFIED_PRIMARY (PDF đầy đủ) | PDF arXiv 2605.13167v1 |
| W12 | GGBench | VERIFIED_PRIMARY (đọc ~100k/145k) | VERIFIED_PRIMARY (PDF đầy đủ) | PDF arXiv 2511.11134v2 |
| W22 | SpanBasedSP | VERIFIED_ABSTRACT_ONLY | **VERIFIED_PRIMARY** (đọc §2–§3 bằng tìm có mục tiêu) | PDF arXiv 2009.06040 |

W15–W17 (PAL/PoT/ToRA) **không** nâng cấp. Lý do: chúng chỉ trả lời câu hỏi (d) ở mức "IR chương trình + bộ thực thi hơn CoT".
Kết luận đó đã có ở bản 1 và không phân biệt được "lời gọi hàm" với "cả chương trình", nên toàn văn không đổi được phân tích.

### 2.2 Toàn văn thêm hoặc đính chính gì

**W04 Inter-GPS** (ACL-IJCNLP 2021, long paper; DOI 10.18653/v1/2021.acl-long.528, thấy trên trang ACL Anthology).

- *Thêm, bộ phân tích văn bản:* bộ parser theo luật dùng biểu thức chính quy: "we apply this approach with regular expressions to
  perform text parsing" [C]. Lý do không dùng Seq2Seq: "neural semantic parsers tend to bring noises in generated results while
  geometry solvers with symbolic reasoning are sensitive to such deviations" [C] (§5.1).
- *Thêm, độ chính xác parser:* "The rule-based text parser achieves an accuracy of 97% while only 67% for the semantic text
  parser" (parser BART) [C] (§7, tr. 6781).
- *Thêm, Table 8:*
  - Literal văn bản tự sinh + sơ đồ tự sinh: 57,5. Literal văn bản chuẩn (GT): 58,0. Sơ đồ GT: 75,0. Cả hai GT: 78,3 [C].
  - Tác giả kết luận: "The current text parser performs very well as there is only a slight gap" [C].
  - Nút thắt nằm ở parser sơ đồ, không ở parser văn bản [C].
- *Thêm, ngôn ngữ hình thức:* "There are 91 predicates in our defined" ngôn ngữ hình thức [C] (§3; Table 10–15 ở phụ lục).
- *Thêm, neo ký hiệu sơ đồ:* gán ký hiệu sơ đồ vào primitive được giải như bài tối ưu có ràng buộc hình học. Ví dụ "the
  perpendicular symbol is only valid to two orthogonal lines" [C].
  - [I] Đây là dạng *tiền điều kiện hình học trước khi chấp nhận một quan hệ*. Nhưng nó áp lên ký hiệu sơ đồ, không lên diễn đạt
    văn bản.
- *Thêm, lỗi văn bản:* "It is difficult for the text parser to handle nested expressions and uncertain references" [C] (Failure
  cases).
- *Đính chính / giữ nguyên:* neo vào span văn bản vẫn `NR`. Bản 1 ghi "parser theo luật" là đúng.

**W07 FormalGeo** (preprint; comments arXiv chỉ ghi "44 pages").

- *Thêm, cấu trúc ngôn ngữ:* ngôn ngữ chia hai loại, GDL (định nghĩa vị từ, định lý) và CDL. CDL gồm "construction statements,
  condition statements, and goal statements" [C]. Ngoài ra, "The solver can read and interpret predicate definition language to
  ensure the legitimacy of input problem conditions" [C].
  - [I] Đây là kiểm tính hợp lệ đầu vào theo định nghĩa vị từ, gần với kiểm kiểu/tiền điều kiện.
- *Đính chính (quan trọng khi trích):*
  - Tóm tắt viết "The backward depth-first search method only yields 2.42% problem-solving failure rate on formalgeo7k" [C].
  - Table 1 (timeout 600 s) cho cùng phương pháp BW DFS: solved 33,73%, unsolved 2,42%, timeout 63,84% [C].
  - Tỉ lệ giải cao nhất là FW RS 39,71% [C]. Với timeout 300 s, "the best success rate for problem-solving was approximately
    30%" [C].
  - Vậy con số 2,42% **không tính bài hết giờ** [I]. Không được trích nó như "tỉ lệ giải 97,6%".
- *Giữ nguyên:* hình phẳng. AI làm parser chỉ được nêu như vai trò có thể ("It can act as a parser") [C]; có đo độ chính xác
  parser hay không: NR.

**W08 Geoparsing** (đọc lại trên PDF).

- *Thêm, Limitations:*
  - "the current formal definitions within GDP-29K do not explicitly distinguish between visible and invisible (e.g., dashed)
    elements in solid geometry" [C].
  - Mẫu hình không gian "primarily focusing on basic primitives" [C].
- *Làm rõ một mục `[NV]` của bản 1:*
  - Vuông góc trong ngôn ngữ là quan hệ giữa hai đường, dạng `AB \perp CD on X` [C].
  - Tìm "perpendicular", "line … plane" trong toàn văn không thấy vị từ đường ⊥ mặt phẳng. Mục này chuyển từ `[NV]` sang
    `NR (tìm có mục tiêu trên toàn văn)`, **không** phải "không có".

**W09 SolidGeo** (preprint; comments arXiv: NR).

- *Thêm, ngôn ngữ dữ liệu:* 2.192 bài tiếng Anh (70,4%), 921 bài tiếng Trung (29,6%) [C].
- *Thêm, chủ đề:* có nhóm chủ đề "3D Coordinate and Vector" [C].
- *Thêm, kết quả:* OpenAI-o1 đạt 49,5%, người đạt 77,5% [C].
- *Thêm, phân tích lỗi:* trên 300 dự đoán sai mỗi mô hình, "visual perception errors and reasoning errors dominate, jointly
  accounting for over 70% of total failures" [C].
- *Thêm, cách đánh giá:* chỉ hỏi–đáp (trả lời trực tiếp, CoT, CoT 2-shot). Không đánh giá cách tiếp cận dựng hình, toạ độ hay
  chương trình [C].
- *Thêm, Limitations:* "there currently exists no widely adopted formal language to represent solid geometry problems" [C].
  Tác giả gợi ý biểu diễn hình thức và "programmatic evaluation" là việc tương lai [C].
- *Tham số ký hiệu (cạnh `a`):* ví dụ trong phụ lục dùng số cụ thể. Có bài với độ dài ký hiệu hay không: `NR`.
- *Ghi chú phản biện chéo:* N10 (Hilbert-Geo) viết về SolidGeo: "Its answers, generated by LLMs, are prone to undetected
  errors" [C trong N10]. Đây là tuyên bố của bài khác; chưa kiểm độc lập.

**W10 MagicGeo** (preprint; venue NR).

- *Thêm, bộ bài bị sửa:* bài trong MagicGeoBench **được sửa văn bản** để thêm thông tin còn thiếu (Figure 3: đề gốc hỏi số đo
  góc thì bản sửa cho luôn số đo) [C].
  - [I] Độ chính xác báo cáo đo trên đề đã được làm cho đủ dữ kiện, không phải đề nguyên bản.
- *Thêm, LLM tự chuẩn hoá ngữ nghĩa:* với "triangle ABC is inscribed in circle O", LLM tự suy ra khoảng cách từ O tới A, B, C
  bằng bán kính, "despite the absence of explicit instructions in the manual" [C].
  - [I] Đây là chuẩn hoá ngữ nghĩa do **LLM** làm ngầm, không có tiền điều kiện tường minh. Ngược hướng với thiết kế AlgoSim,
    nơi engine chuẩn hoá có điều kiện.
- *Thêm, lỗi khiến phải hình thức hoá lại:* "non-compliant characters" và "errors in parameter specifications, including
  incorrect value assignments or misalignment of parameter numbers" [C].
- *Thêm, Table 5:* đổi LLM (DeepSeek-V3, Qwen-plus, GPT-4o mini) trên 60 mẫu, chấm thủ công: độ chính xác 0,96–1,00. Tác giả
  kết luận "the choice of LLM has a negligible impact" [C]. Mẫu nhỏ; prompt khác nhau theo từng LLM [C].
- *Thêm, Table 4:* ablation "w/o Coordinates" (LLM viết thẳng TikZ) và "w/o Solver" (LLM tự đoán toạ độ), chấm bằng CLIP [C].
- *Giữ nguyên:* bộ giải "traverse each variable". Danh sách hàm ràng buộc không công bố [C: NR].
  - Bộ giải số hay ký hiệu vẫn `UNCLEAR`. Phần Limitations nhắc "the precision required for diagram generation" [C]; [I] điều này
    gợi ý tìm kiếm số.

**W11 GeoBuildBench** (preprint; đọc PDF đầy đủ).

- *Thêm, chuẩn hoá diễn đạt khi dựng benchmark (Stage 2):*
  - "although the same geometric relation may be expressed in diverse natural-language forms, the output is explicitly
    canonicalized into our finite condition-type set" [C].
  - Bước này do GPT-4.1 làm theo "a fixed schema and a closed set of supported condition types", rồi người kiểm [C].
  - [I] Chuẩn hoá diễn đạt về tập quan hệ hữu hạn nằm ở **khâu xây dữ liệu chấm**, không ở hệ thống được đánh giá. Độ chính xác
    riêng của bước chuẩn hoá: NR.
- *Thêm, lọc bài (Stage 1):* loại bài có "undefined point references, or incomplete constraints", và bài chỉ hiểu được nhờ hình
  [C].
- *Thêm, nguồn thất bại:* "unsuccessful cases are dominated by structural errors rather than execution failures" [C]. Lỗi tham
  chiếu chưa định nghĩa phổ biến nhất "indicates that most failures arise from difficulties in tracking and reusing previously
  constructed geometric objects" [C].
- *Thêm, Table 3 (ablation thị giác):* bật thị giác cho Qwen3-VL-235B tăng thành công 39,1→42,2% nhưng tăng mạnh lỗi do bộ kiểm
  phát hiện: thiếu đối tượng 131→2042, điều kiện hỏng 100→1817, ảo giác cấu trúc 85→928 [C]. Tác giả diễn giải là thị giác
  "destabilizes symbol binding and state tracking" [C].
- *Thêm, phục hồi:* 1,17–1,79 bước/ảo giác [C].
- *Thêm, Limitations:* "We therefore recommend interpreting the reported numbers primarily as evidence about failure modes" [C].
  3D nằm ngoài phạm vi [C].
- *Xác nhận `NR` (đã đọc hết):*
  - Không có ablation có/không vòng sửa (ngân sách cố định 5 vòng).
  - Không có số token.
  - Không mô tả hệ kiểu cho lệnh DSL, không neo đối số vào span đề.
  - Dung sai: "fixed numerical tolerances", giá trị cụ thể NR. Khoảng cách "normalized to be invariant to global scaling" [C].
- *Cảnh báo trích:* Table 1 bị lệch cột khi trích chữ. Hàng số "missing objects/failed constraints" theo từng mô hình là
  `UNCLEAR` cho tới khi đối chiếu PDF. Tỉ lệ thành công (78,9 / 75,3 / 42,2 / 21,3) và số ảo giác/bài (GPT-5.1 0,40; Gemini 0,34)
  khớp với lời văn §5.3–5.4 [C].

**W12 GGBench** (preprint; đọc PDF đầy đủ).

- *Thêm, phân loại lỗi:* bốn loại lỗi [C]:
  1. "geometric logic errors";
  2. "structural and contextual errors" (nhầm quan hệ chứa nhau);
  3. "conflation of construction and numeric goals";
  4. "code-level failures from syntax misuse or reserved keyword conflicts".
- *Thêm, độ tương đồng mã không thay được thực thi:* "code-similarity metrics (e.g., BLEU or ROUGE-L) do not necessarily predict
  executable success" [C]. Một số mô hình "despite generating coherent plans, often fail to produce executable code" [C].
- *Thêm:* "token" trong bài là độ dài câu hỏi (68–483, trung bình 189,83) [C]. Đây **không** phải chi phí token của IR.
- *Giữ nguyên:* chiều 2D/3D không nêu tường minh; SolidGeo được gọi là benchmark "solid/3D" [C]; [I] GGBench là hình phẳng.

**W22 SpanBasedSP** (ACL 2021 theo comments ở bản 1).

- *Thêm, cách huấn luyện:* huấn luyện được "without access to gold trees, treating trees as latent variables" bằng hard-EM, hoặc
  có cây chuẩn [C].
- *Thêm, span không liền:* mở rộng CKY cho một lớp cây "non-projective", tức span không liền [C]. Có đặc trưng khớp dựa trên "a
  small lexicon" [C].
- [I] Liên quan trực tiếp tới AlgoSim: một quan hệ trong đề tiếng Việt có thể rải trên đoạn không liền (ví dụ chủ ngữ ở mệnh đề
  trước). Một luật neo nguồn yêu cầu trích dẫn **liền một khúc** sẽ từ chối những trường hợp này.

### 2.3 Công trình cũ không đọc lại

W02, W03, W05, W06, W13–W21, W23–W26 giữ nguyên mức xác minh và nội dung như bản 1. Bốn cột mới cho chúng nằm ở mục 3.5, dựa
trên phần đã đọc ở bản 1.

---

## 3. Ma trận các công trình mới (N01–N11) và bốn cột mới

Mọi bài mới đều mở toàn văn (PDF) ⇒ `VERIFIED_PRIMARY`. Tìm có mục tiêu trong toàn văn không phải đọc từng dòng: khi một mục
ghi `NR`, nghĩa là các lượt tìm và đoạn đã đọc không thấy.

### 3.1 Định danh, đầu vào, IR, cách chọn, engine (cột của bản 1)

| Mã | Công trình | Năm | DOI/URL | Mức xác minh | Đầu vào | Biểu diễn trung gian | Cách chọn hàm/phép dựng | Engine |
|---|---|---|---|---|---|---|---|---|
| N01 | Patil et al. — Berkeley Function Calling Leaderboard (BFCL) | 2025 | PMLR 267:48371–48392 (ICML 2025, trang PMLR); DOI: NR; https://proceedings.mlr.press/v267/patil25a.html | VERIFIED_PRIMARY | Câu hỏi người dùng + tài liệu hàm [C] | Lời gọi hàm Python-callable; chế độ FC (trường `tools` gốc) hoặc chế độ prompt [C] | LLM chọn hàm + điền tham số; có loại simple/multiple/parallel/parallel-multiple/irrelevance, nhiều lượt, agentic [C] | Bộ khớp AST + thực thi thật cho một phần; trạng thái/response cho nhiều lượt [C] |
| N02 | Basu et al. — NESTFUL | 2024 (v3 2025) | arXiv:2409.03797; DOI 10.48550/arXiv.2409.03797; preprint | VERIFIED_PRIMARY | Câu hỏi + đặc tả API có kiểu [C] | Chuỗi lời gọi JSON có `label` (`$var_1`), đối số tham chiếu `$var_k.result$` [C] | LLM sinh cả chuỗi lồng (ICL hoặc ReAct) [C] | Thực thi các hàm (đều thực thi được) [C] |
| N03 | Li et al. — API-Bank | 2023 | arXiv:2304.08244 (comments: EMNLP 2023); DOI 10.48550/arXiv.2304.08244 | VERIFIED_PRIMARY | Hội thoại + mô tả API [C] | `[ApiName(key1='value1', …)]` [C] | LLM gọi API, có/không truy hồi API và lập kế hoạch [C] | Hệ API mô phỏng thực thi được [C] |
| N04 | Sequeira et al. — Agent-Sentry | 2026 | arXiv:2603.22868v2 (cs.CR); DOI 10.48550/arXiv.2603.22868; preprint | VERIFIED_PRIMARY | Vết thực thi tác tử [C] | Đồ thị provenance: mỗi đối số mang tập nguồn + loại dẫn xuất `{verbatim, derived, generated}` [C] | Không chọn hàm; kiểm hành động do tác tử đề xuất [C] | Bộ phân loại cấu trúc + allowlist tất định + LLM judge cho phần dư [C] |
| N05 | Banerjee et al. — CRANE | 2025 | arXiv:2502.09061 (comments: "Accepted at ICML 2025"; header PDF: PMLR 267); DOI 10.48550/arXiv.2502.09061 | VERIFIED_PRIMARY | Bài toán lời văn (GSM-Symbolic), câu suy luận (FOLIO) [C] | Biểu thức ký hiệu trong `<< >>` / công thức FOL; ngữ pháp CFG mở rộng [C] | Giải mã xen kẽ tự do ↔ ràng buộc [C] | Z3 kiểm tương đương biểu thức; Prover9 [C] |
| N06 | Geng et al. — JSONSchemaBench | 2025 | arXiv:2501.10868v3 (PDF: "Preprint. Under review."); DOI 10.48550/arXiv.2501.10868 | VERIFIED_PRIMARY | 10K JSON Schema thật [C] | JSON tuân schema [C] | 6 framework giải mã ràng buộc, gồm OpenAI và Gemini [C] | Bộ kiểm tuân thủ schema; 3 nhiệm vụ suy luận [C] |
| N07 | Chen et al. — Teaching LLMs to Self-Debug | 2023 | arXiv:2304.05128v2; DOI 10.48550/arXiv.2304.05128; venue: NR trên trang arXiv/PDF ⇒ preprint | VERIFIED_PRIMARY | Đặc tả bài lập trình / câu hỏi SQL [C] | SQL, Python, dịch C++→Python [C] | LLM viết mã, rồi tự sửa theo phản hồi [C] | Thực thi + unit test khi có [C] |
| N08 | Chang et al. — Dr.Spider | 2023 | arXiv:2301.08881 (comments và header PDF: ICLR 2023); DOI 10.48550/arXiv.2301.08881 | VERIFIED_PRIMARY | Câu hỏi NL + CSDL [C] | SQL [C] | Mô hình text-to-SQL [C] | Thực thi SQL [I] |
| N09 | Li et al. — GSM-Plus | 2024 | arXiv:2402.19255 (comments: ACL 2024); DOI 10.48550/arXiv.2402.19255 | VERIFIED_PRIMARY | Bài GSM8K + 8 kiểu biến đổi [C] | Lời giải NL hoặc chương trình [C] | 25 LLM, 4 kỹ thuật prompt [C] | Chấm đáp số [C] |
| N10 | Xu et al. — Hilbert-Geo | 2026 | arXiv:2605.16385v3 (comments: CVPR 2026); DOI 10.48550/arXiv.2605.16385 | VERIFIED_PRIMARY | Đề hình không gian (văn bản + hình) [C] | CDL: 120 vị từ (35 cơ bản), 220 định lý [C] | MLLM được prompt với ví dụ phủ mọi vị từ cơ bản, sinh CDL [C] | SGRE: tìm kiếm định lý + tính đại số [C] |
| N11 | Wu et al. — DynaSolidGeo | 2025 | arXiv:2510.22340v2; DOI 10.48550/arXiv.2510.22340; preprint (comments chỉ có link mã) | VERIFIED_PRIMARY | 503 bài gốc hình không gian, tiếng Trung + Anh [C] | Chương trình Python + MATLAB có tham số [C] | Benchmark; VLM trả lời [C] | MATLAB dựng hình/video; đáp án tính lại theo tham số [C] |

### 3.2 Kết hợp, phụ thuộc, grounding, kiểm chứng, chiều, dữ liệu (cột của bản 1)

| Mã | Kết hợp primitive | Xử lý phụ thuộc | Grounding | Kiểm chứng | 2D/3D | Dữ liệu thực nghiệm |
|---|---|---|---|---|---|---|
| N01 | Nhiều hàm, gọi song song, nhiều lượt [C] | Nhiều lượt: kiểm chuỗi gọi tối thiểu (response-based) [C] | NR | AST: "function name matches exactly and if all parameter values fall within their respective possible answers" [C]; AST tương quan mạnh với thực thi [C] | — | 2.251 mục crowd-sourced, 1000 truy vấn nhiều lượt [C]; trung bình 3 hàm lựa chọn, 4 tham số/hàm [C] |
| N02 | Hàm toán học/API ghép lồng [C] | Model phải tự gán nhãn biến và truyền `$var.result$` [C] | NR | Partial/Full sequence match, Win Rate (thực thi) [C] | — | 1800+ chuỗi lồng; tốt nhất ≤28% full match, ≤60% win rate [C] |
| N03 | Gọi một/nhiều API [C] | Plan+Retrieve+Call [C] | NR | So khớp lời gọi chuẩn + ROUGE câu trả lời [C] | — | Bảng phân bố lỗi theo mô hình (xem 3.4) [C] |
| N04 | Chuỗi tool call của tác tử [C] | Đồ thị provenance giữa các lời gọi [C] | Schema công cụ thêm trường bắt buộc "source and derivation"; giá trị "unverifiable" nếu nguồn khai báo "does not contain the value" [C] | Chặn 94,3% injection thành công, cho qua 95,1% lần chạy lành (AgentDojo, AgentDyn) [C] | — | Bộ AgentDojo, AgentDyn [C] |
| N05 | NR | NR | Ràng buộc ngữ nghĩa: biểu thức "contain only valid problem-defined variables" [C] | Z3 kiểm tương đương với biểu thức chuẩn [C] | — | GSM-Symbolic; FOLIO 203 mẫu [C] |
| N06 | NR | NR | NR | Tuân thủ schema; độ phủ khai báo/thực nghiệm; over/under-constrained [C] | — | 10K schema; nhiệm vụ Last Letters, Shuffle Objects, GSM8K [C] |
| N07 | NR | NR | NR | Unit test (khi có), giải thích mã, vết thực thi [C] | — | Spider, TransCoder, MBPP [C] |
| N08 | NR | NR | NR | NR trong phần đọc | — | 17 phép nhiễu (3 CSDL, 9 câu hỏi, 5 SQL) [C] |
| N09 | NR | NR | NR | Đáp số; PDR [C] | — | 8 kiểu biến đổi; 25 LLM [C] |
| N10 | Vị từ + định lý không gian, ví dụ `PerpendicularBetweenLineAndPlane(AB,U)`, `PerpendicularBetweenPlane(U,V)`, `HeightOfTriangularPrism(ABC,DEF)` [C] | Cây tìm kiếm định lý (Algorithm 1) [C] | Văn bản/hình → CDL; neo span văn bản: NR | Lập luận ký hiệu truy vết được; Fuzzy Jaccard cho chất lượng parse [C] | 3D (+ phẳng) [C] | SolidFGeo2k, PlaneFGeo3k, MathVerse-Solid [C] |
| N11 | NR | NR | NR | Đáp số + đánh giá quá trình theo chuỗi suy luận chuyên gia [C] | 3D [C] | 503 bài gốc sinh vô hạn biến thể [C] |

### 3.3 Trùng và khác với AlgoSim (toàn bộ `[I]`)

| Mã | Trùng với AlgoSim [I] | Khác AlgoSim [I] |
|---|---|---|
| N01 | Chuẩn đo cho "LLM chọn hàm từ danh mục + điền tham số", gồm cả gọi song song, nhiều hàm | Không có hình học, tiền điều kiện hay neo nguồn; đúng = tham số thuộc tập giá trị chấp nhận, không phải quan hệ được kiểm |
| N02 | Đúng loại lỗi AlgoSim gặp khi một lời gọi dùng đầu ra lời gọi khác (đỉnh, chân đường cao, …) | Model phải tự quản nhãn biến; AlgoSim để engine giải phụ thuộc theo tên đối tượng |
| N03 | Phân loại lỗi tham số: thiếu, sai định dạng, placeholder làm giá trị | Không có kiểm hình học; API đời thường |
| N04 | **Cơ chế gần nhất** với neo nguồn của AlgoSim: thêm trường nguồn bắt buộc vào schema hàm, kiểm tất định "giá trị có nằm trong nguồn khai báo không" | Mục tiêu an ninh (chặn injection), không đo độ chính xác hiểu đề; nguồn là vết công cụ, không phải đề bài |
| N05 | Ràng buộc "chỉ dùng biến có trong đề" ≈ đóng từ vựng tên; biến ký hiệu + kiểm tương đương bằng solver ≈ độ dài ký hiệu `a`, `2a` | Ràng buộc ở mức giải mã token; kiểm biểu thức số học, không phải hình |
| N06 | AlgoSim dùng Gemini function calling ⇒ chịu giới hạn hỗ trợ schema của Gemini | Bộ đo của schema JSON tổng quát, không phải hàm hình học |
| N07 | Vòng "engine trả chẩn đoán → model sửa" | Mã tuỳ ý; phản hồi là unit test, không phải tiền điều kiện hình học |
| N08 | Đo độ bền của bộ phân tích ngữ nghĩa với diễn đạt lại | SQL, không phải hình |
| N09 | Bằng chứng về diễn đạt lại và thiếu dữ kiện | Đo giải bài, không đo phân tích thành biểu diễn |
| N10 | Cùng miền hình không gian; thư viện vị từ có đường ⊥ mặt phẳng; LLM chỉ sinh biểu diễn hình thức, engine ký hiệu quyết định | Mục tiêu giải số đo bằng định lý, không dựng toạ độ hay cảnh; LLM viết CDL tự do (không chọn từ registry có kiểu); không neo span |
| N11 | Hình không gian, tham số hoá nhãn điểm và độ dài để chống học thuộc | Tham số được **thế số** khi sinh đề; không có độ dài ký hiệu tự do trong lời giải |

### 3.4 Bốn cột mới cho N01–N11 và các W đã nâng cấp

| Mã | Phương pháp đã công bố | AlgoSim kế thừa được gì [I] | Hạn chế được bài báo xác nhận | Chưa kiểm trong tập đọc |
|---|---|---|---|---|
| W04 | Parser văn bản theo luật (regex) + parser sơ đồ nơ-ron → 91 vị từ → bộ giải định lý [C] | Đo riêng "parse đúng" và "giải đúng" bằng thay literal GT (Table 8): cùng thiết kế đo cho tầng chọn hàm của AlgoSim | "nested expressions and uncertain references"; parser sơ đồ là nút thắt [C] | Đề không gian; LLM làm parser; neo span |
| W07 | GDL/CDL + FGPS kiểm/giải [C] | Kiểm tính hợp lệ đầu vào theo định nghĩa vị từ trước khi suy diễn | Phần lớn bài không giải được là do hết giờ (63,84% ở BW DFS) [C]; nguồn khác: "code bugs, equation solving timeouts, and the omission of theorems" [C] | Văn bản → CDL bằng LLM có đo độ chính xác |
| W08 | MLLM ảnh → ngôn ngữ hình thức phẳng + không gian, SFT + RL [C] | Từ vựng primitive khối `Pyramid O-ABC` | Không phân biệt nét khuất/hiện cho khối; mẫu khối thưa [C] | Đường ⊥ mặt phẳng; toạ độ; đầu vào văn bản |
| W09 | Benchmark hỏi–đáp 3.113 bài [C] | Nguồn bài ngoài để thử độ phủ registry (có phần tiếng Trung, có "3D Coordinate and Vector") | Chỉ EN/CN; chưa có ngôn ngữ hình thức chung cho hình không gian [C] | Độ dài ký hiệu `a`; dựng/toạ độ |
| W10 | LLM → biến + ràng buộc; bộ giải tự viết; phản hồi ≤5 vòng; TikZ [C] | Bằng chứng (nhỏ, chấm tay) cho vòng phản hồi bộ giải → LLM: 94,7→98,7% | Dịch "not yet flawless"; có thể >1 giờ; thí nghiệm chỉ hình phẳng [C]; đề đã sửa cho đủ dữ kiện [C] | Bộ giải chính xác hay số; 3D; neo nguồn |
| W11 | LLM viết cả chương trình DSL kiến thiết, sửa ≤5 vòng theo phản hồi bộ kiểm [C] | Phân loại lỗi (undefined reference, thiếu đối tượng, điều kiện hỏng) làm danh mục lỗi đăng ký trước | Chỉ hình phẳng tiếng Trung, tập quan hệ đóng; kết quả phụ thuộc giao thức; nên đọc như bằng chứng về kiểu lỗi [C] | Có/không vòng sửa; token; kiểu; neo nguồn |
| W12 | Benchmark ba phương thức (lập kế hoạch, mã GeoGebra, ảnh) [C] | Không dùng độ giống bề mặt (BLEU, pixel) làm thước đúng | Độ đo pixel tương quan yếu với hình hợp lệ [C] | 3D; kiểm quan hệ tất định |
| W22 | Parser span (CKY + mở rộng non-projective), cây ẩn hard-EM [C] | Luật neo nguồn phải cho phép trích dẫn nhiều khúc không liền | Một số cây chuẩn non-projective không parse được bằng CKY gốc [C] | Hình học; LLM |
| N01 | AST substring matching; FC vs prompt mode; nhiều lượt có trạng thái [C] | Chấm lời gọi bằng so tập giá trị chấp nhận cho từng tham số ⇒ chấm offline không cần dựng | Chế độ FC giảm lỗi giải mã nhưng "can limit the flexibility … in complex function calling scenarios" [C]; mô hình đơn lượt tốt, còn "memory, dynamic decision-making, and long-horizon reasoning remain open challenges" [C] | Hàm có tiền điều kiện; neo nguồn; miền toán |
| N02 | Benchmark chuỗi lồng có nhãn biến [C] | Tránh bắt model tự quản biến trung gian; nếu phải có, đo riêng mẫu `{A,B}→C` | Mô hình "struggle with tasks such as assigning variables … correctly passing variable names and corresponding output parameters" [C]; kiểu dữ liệu vào/ra [C] | Engine giải phụ thuộc thay model |
| N03 | Benchmark 3 mức (Call, Retrieve+Call, Plan+Retrieve+Call) [C] | Mã lỗi tham số làm nhãn cho phân loại lỗi neo nguồn | Lỗi tham số (exception, tham số không hợp lệ, lời gọi không parse được) "collectively contribute to 32% of the overall errors", ví dụ "passing a placeholder as a value" [C]; con số thuộc bảng nào là `UNCLEAR` do bố cục cột (ba loại đó ở Table 5/Lynx cộng lại ≈31,75% [I]) | Neo nguồn; tiền điều kiện |
| N04 | Schema có trường nguồn bắt buộc, kiểm giá trị trong nguồn, allowlist [C] | Thiết kế trường `source` + `derivation` (`verbatim`/`derived`) và kiểm "nguồn khai có chứa giá trị" | "self-reported provenance is not always reliable"; kiểm tra "reduce rather than eliminate the dependence on a self-reporting LLM" [C] | Tác động của trường nguồn lên độ chính xác gọi hàm |
| N05 | Giải mã xen kẽ: lập luận tự do rồi đoạn ràng buộc trong delimiter [C] | Cho phép một trường lập luận tự do trước lời gọi có cấu trúc thay vì ép khuôn ngay | Ngữ pháp chỉ cho đáp án hợp lệ làm giảm năng lực suy luận (định lý của bài) [C]; thí nghiệm trên mô hình mở ≤32B [C] | Mô hình đóng (Gemini); function calling gốc |
| N06 | Bộ đo hiệu quả/độ phủ/chất lượng của 6 framework [C] | Kiểm từ khoá JSON Schema mà Gemini hỗ trợ; giữ schema hàm đơn giản; luôn kiểm lại sau giải mã | Gemini (bản 2024-10-31): độ phủ khai báo 0,86 (GlaiveAI) và 0,08 (GitHub Easy), tuân thủ 1,00 và 0,88 [C] | Hành vi Gemini 2026 |
| N07 | Tự gỡ lỗi bằng few-shot, phản hồi nhiều dạng [C] | Phản hồi phải chứa **thông tin thực thi**; một vòng thường đủ ⇒ trần 1 vòng sửa là cấu hình ứng viên rẻ | Không có unit test thì phản hồi đơn giản không cải thiện rõ trên Spider [C]; MBPP không thực thi: Codex 61,4→57,6 [C] | Hình học; phản hồi tiền điều kiện |
| N08 | 17 phép nhiễu, sinh diễn đạt lại bằng PLM + chuyên gia lọc [C] | Phương pháp dựng bộ diễn đạt lại: chuyên gia kiểm diễn đạt có **giữ nghĩa** không | Mô hình bền nhất vẫn giảm 14,0%; 50,7% ở phép nhiễu khó nhất [C]; chỉ 270/500 diễn đạt lại từ crowdsourcing là giữ nghĩa [C] | Hình học; LLM đời mới |
| N09 | 8 kiểu biến đổi bài toán lời văn [C] | Nhóm biến đổi "thiếu dữ kiện" là phép thử fail-closed | Mô hình "may generate a hallucinated solution instead of acknowledging the absence of the required information" [C] | Phân tích sang biểu diễn |
| N10 | Parse2Reason: MLLM → CDL → SGRE [C] | Bảng vị từ không gian để đối chiếu độ phủ registry; thiết kế đo "CDL chuẩn vs CDL parse" | Bài không giải được phần lớn do "combinatorial explosion", CDL sai, hoặc đề lỗi [C]; giới hạn 300 s [C] | Dựng toạ độ; độ dài ký hiệu; neo span |
| N11 | Bài gốc tham số hoá, sinh biến thể theo seed [C] | Ý sinh biến thể (đổi nhãn điểm, đổi số) để đo độ bền tầng chọn hàm | Giảm tới 20,4% ở thiết lập động (Claude-Sonnet-4.5) [C] | Biến thể diễn đạt lại; độ dài ký hiệu |

### 3.5 Bốn cột mới cho các W cũ không đọc lại (dựa trên phần đọc ở bản 1)

| Mã | Phương pháp đã công bố | AlgoSim kế thừa được gì [I] | Hạn chế được bài báo xác nhận | Chưa kiểm trong tập đọc |
|---|---|---|---|---|
| W01 | Tổng hợp chương trình thước-compa, thư viện mở rộng, heuristic goodness [C] | Thư viện hàm dẫn xuất theo chương sách; so thư viện cơ bản vs mở rộng | Đề tiếng Anh "often ambiguous"; front-end NL là "ongoing work" [C] | LLM; 3D; kiểm chính xác |
| W02 | LM đề xuất dựng phụ + DD/AR [C] | Tách đề xuất (model) khỏi quyết định (engine ký hiệu) | Phạm vi hình phẳng Euclid [C] | Đọc đề tự nhiên |
| W03 | Ngôn ngữ AG mở rộng, đo độ phủ [C] | Đo độ phủ registry trên kho bài thật | NR trên tóm tắt | Cơ chế dịch NL |
| W05 | Sinh chương trình giải (NGS) [C] | — | Kém xa người [C] | Dựng hình |
| W06 | Mệnh đề văn bản từ sơ đồ [C] | — | NR trên tóm tắt | Neo vào đề |
| W13 | Đánh giá LLM dựng hình, khung đa tác tử [C] | Danh mục ảo giác đối tượng/vị trí | Mô hình bịa đối tượng, yếu quan hệ không gian 2D [C] | Engine tất định |
| W14 | Mask R-CNN + tìm kiếm cây trên Euclidea [C] | — | Loại chưa thấy 31/68 [C] | Văn bản |
| W15–W17 | LLM viết chương trình, bộ thông dịch tính [C] | Đẩy tính toán sang engine | NR trên tóm tắt | IR lời gọi hàm |
| W18 | LLaMA tinh chỉnh + truy hồi tài liệu API [C] | Truy hồi thẻ hàm theo ngữ cảnh khi registry lớn | NR trên tóm tắt | Tiền điều kiện |
| W19–W21 | Văn bản/đám mây điểm → chuỗi/mã CAD [C] | IR dựng 3D thực thi được | W21: so sánh đổi đồng thời IR và mô hình [I] | Kiểm quan hệ chính xác |
| W23 | Học thư viện bằng wake-sleep [C] | — | NR trên tóm tắt | Thư viện cố định có kiểu |
| W24 | Constrained Semantic Decoding [C] | Ràng buộc giải mã theo ngôn ngữ đích | NR trên tóm tắt | Cái giá về suy luận |
| W25 | Trích xuất neo vị trí nguồn (phần mềm) [C] | Hiển thị đoạn đề được neo cho người dùng | Không có số đo [C] | Tác động lên độ chính xác |
| W26 | So sánh có/không ràng buộc định dạng [C] | Rủi ro khi ép khuôn chặt | "stricter format constraints generally lead to greater performance degradation in reasoning tasks" [C] | Phản chứng: xem N05, N06 |

---

## 4. Phân tích khoảng trống

### (a) Dựng hình hợp thành từ một thư viện hàm hữu hạn

**CONFIRMED BY SOURCE**

- **W01:** thư viện + hàm dẫn xuất là ý có từ 2011 (bản 1).
- **W11:** chương trình DSL kiến thiết. Thất bại chủ yếu là lỗi cấu trúc, "rather than execution failures". Lỗi đứng đầu là tham
  chiếu chưa định nghĩa, do khó "tracking and reusing previously constructed geometric objects".
- **N10 (Hilbert-Geo, CVPR 2026):**
  - Có thư viện 120 vị từ không gian, gồm đường ⊥ mặt phẳng, mặt ⊥ mặt, chiều cao lăng trụ, cùng 220 định lý.
  - LLM chỉ sinh CDL; engine định lý quyết định.
  - Gemini 2.5 Pro + Hilbert-Geo đạt 77,3%; dùng CDL chuẩn đạt 78,7%.
  - Hai con số này **không** đo dựng hình.
- **N02 (NESTFUL):** khi lời gọi sau dùng đầu ra lời gọi trước, mô hình tốt nhất ≤28% full-sequence match. Mẫu `{A,B}→C` giảm
  mạnh so với `A→B`.
- **N01 (BFCL):** mô hình mạnh đã tốt ở gọi đơn lượt. Tác giả đặt *giả thuyết* rằng gọi song song "may adversely affect accuracy
  when function calls are chained".

**INFERENCE**

- Có hai trục khác nhau: (i) *ai quản phụ thuộc giữa các lời gọi*, (ii) *thư viện thô hay mịn*.
  - Bằng chứng ở N02/W11 chỉ cho thấy để model tự quản phụ thuộc thì lỗi nhiều.
  - Văn liệu đã đọc **chưa** có thí nghiệm "engine giải phụ thuộc vs model giải phụ thuộc" trên cùng mô hình và cùng bài.
- Trong tập đã đọc, chưa công trình nào **báo cáo** đồng thời bốn điều sau. Đây là khoảng trống *trong tập đọc*, không phải bằng
  chứng tính mới:
  1. đề hình không gian bằng ngôn ngữ tự nhiên;
  2. registry hàm dựng 3D hữu hạn có kiểu mà mô hình chỉ *chọn*;
  3. engine tất định giải phụ thuộc và dựng toạ độ chính xác;
  4. kiểm mọi quan hệ.
- N10 làm hẹp khoảng trống so với bản 1, vì nó đã có thư viện vị từ không gian + LLM chỉ sinh biểu diễn + engine ký hiệu. Khác
  biệt còn lại là *dựng/hiển thị* so với *giải số đo*, và *chọn có kiểu* so với *viết CDL tự do*.
- N10 và W08 cùng tự nhận là khung hình thức thống nhất cho hình không gian. Khoá luận không nên lặp kiểu tuyên bố "đầu tiên".

**NOT VERIFIED**

- Phần mềm giáo dục (GeoGebra 3D, phần mềm Việt/Trung) có cơ chế đề → lệnh dựng hay không: chưa khảo sát.

### (b) Ánh xạ văn bản → lời gọi hàm có neo nguồn và neo span đối số

**CONFIRMED BY SOURCE**

- **N04 (Agent-Sentry)** có cơ chế cấu trúc gần nhất:
  - schema công cụ thêm trường bắt buộc "source and derivation";
  - `derivation ∈ {verbatim, derived, generated}`;
  - giá trị là "unverifiable" khi nguồn khai báo "does not contain the value".
  - Tác giả xác nhận hạn chế: provenance do chính LLM tự khai "not always reliable". Kiểm tra chỉ "reduce rather than eliminate"
    sự phụ thuộc đó.
  - Số đo của bài là về **an ninh** (94,3% / 95,1%), không về độ chính xác hiểu yêu cầu.
- **W25:** trích xuất neo vị trí, không có số đo. **W22:** span là biến ẩn hoặc có giám sát; cần mở rộng cho span không liền.
- **N05:** ràng buộc biểu thức chỉ dùng biến có trong đề. **N03:** lỗi tham số chiếm khoảng 32% tổng lỗi (bảng gốc `UNCLEAR`), gồm điền placeholder làm giá
  trị.
- **W04:** parser văn bản theo luật đúng 97% so với BART 67%. Literal văn bản chuẩn chỉ hơn literal tự sinh 0,5 điểm.

**INFERENCE**

- Trong tập đã đọc **không có số đo** nào cho câu hỏi: "bắt mô hình trích dẫn nguyên văn cho từng đối số, rồi kiểm tất định"
  làm tăng hay giảm độ chính xác gọi hàm.
- Văn liệu chỉ cho (i) cơ chế (N04, W25) và (ii) lý do kỳ vọng nó giúp: N03/W13 cho thấy tham số bịa và đối tượng bịa là lỗi
  thật.
- Lợi ích của neo nguồn trong AlgoSim phải được **đo**, không trích. Rủi ro đối xứng, từ N04 và W22:
  - neo nguồn tự khai có thể sai mà vẫn qua kiểm (trích đúng chữ nhưng gán sai vai trò);
  - luật trích liền một khúc có thể từ chối diễn đạt hợp lệ.

### (c) Chuẩn hoá ngữ nghĩa diễn đạt về quan hệ hình học chính tắc dưới tiền điều kiện tường minh

**CONFIRMED BY SOURCE**

- **W11:** chuẩn hoá diễn đạt về tập quan hệ hữu hạn **có làm**, nhưng ở khâu xây benchmark (GPT-4.1 + người kiểm). Không đo
  riêng độ chính xác.
- **W10:** LLM tự suy quan hệ ngầm ("inscribed" ⇒ cách đều tâm), không có luật tường minh.
- **W04:** gán ký hiệu sơ đồ có ràng buộc khả thi hình học, kiểu "ký hiệu vuông góc chỉ hợp lệ giữa hai đường vuông góc". Đây
  là tiền điều kiện, nhưng trên sơ đồ.
- **N08:** chỉ 270/500 diễn đạt lại từ crowdsourcing là giữ nghĩa, "as a small change to a question could alter its meaning".
  Mô hình bền nhất vẫn giảm 14,0%.
- **N09:**
  - Với "numerical substitution and problem understanding" (diễn đạt lại), mô hình "maintain their performance and even show
    slight improvements".
  - Khi bỏ một dữ kiện thiết yếu, mô hình (trừ người và mô hình đóng) có thể bịa lời giải.
- **N11:** đổi tham số/nhãn làm giảm tới 20,4%.

**INFERENCE**

- Bằng chứng về độ bền với diễn đạt lại **trái chiều theo nhiệm vụ**. N09 (giải bài) thấy diễn đạt lại gần như vô hại. N08 (phân
  tích sang SQL) thấy suy giảm rõ.
- AlgoSim là phân tích sang biểu diễn, gần N08 hơn N09. Nhưng N08 đo mô hình text-to-SQL, không phải LLM gọi hàm. **Chưa** có
  số cho hình học.
- **Chưa** thấy công trình nào đo chuẩn hoá *có tiền điều kiện* ("SA là đường cao" ⇒ SA ⊥ (ABC) chỉ khi ngữ cảnh chứng minh
  được). Ví dụ W10 là phía ngược lại: LLM chuẩn hoá ngầm, không điều kiện.
- Bài học của N08 áp thẳng vào thiết kế bộ đo: một bộ diễn đạt lại phải được **chuyên gia kiểm giữ nghĩa**. Nó cũng phải có cặp
  *đối chứng* mà tiền điều kiện sai, ví dụ hình chiếu của S là H ≠ A. Thiếu cặp này thì không phân biệt được "chuẩn hoá đúng"
  với "luôn ánh xạ".

### (d) Ảnh hưởng của biểu diễn trung gian (lời gọi hàm / cả chương trình / DSL) lên token và độ chính xác

**CONFIRMED BY SOURCE**

- **N01 (BFCL)** là so sánh có kiểm soát gần nhất: *cùng mô hình*, hai chế độ đầu ra.
  - Chế độ FC (function calling gốc) cho đầu ra "easier to parse". Mô hình chế độ prompt có 412,93 vấn đề giải mã so với 182,5 ở
    FC, trên 4.251 mục.
  - Nhưng trong nhóm multiple, mô hình FC có nhiều lời gọi sai số lượng hơn (77,5 so với 21). Tác giả viết mô hình mạnh thường
    tốt hơn ở chế độ prompt.
  - Lời văn nói "three times more", trong khi số cho tỉ lệ ≈2,3 ⇒ `UNCLEAR`, đối chiếu PDF.
- **N05 (CRANE):** token theo phương pháp, Table 3 (Qwen2.5-1.5B, GSM-Symbolic).
  - Ràng buộc không lập luận: ~25–34 token, độ chính xác ≈ tự do không CoT (ví dụ 21 so với 20).
  - CoT tự do: ~129–131 token.
  - CRANE: ~131–141 token, độ chính xác cao nhất (28–31%).
  - Đây là bằng chứng *token–độ chính xác* duy nhất trong tập đọc, nhưng cho biểu thức số học, không cho lời gọi hàm.
- **N06 phản chứng một phần W26:** trên Llama-3.1-8B, cả 4 framework ràng buộc đều ≥ "LM only" (GSM8K 80,1% → 81,6–83,8%).
  Schema để trường `reasoning` **trước** `answer`. Tác giả dẫn lập luận của Kurt rằng suy giảm ở W26 đến từ prompt/schema kém
  (blog Kurt chưa mở ⇒ `[NV]` cho lập luận gốc).
- **W11, W12:** không báo token của IR. **W12:** độ giống mã bề mặt không dự báo thực thi được.

**INFERENCE**

- Văn liệu đã đọc **không** có thí nghiệm "lời gọi hàm theo mệnh đề vs cả chương trình DSL vs DSL gọn" trên cùng mô hình, cùng
  bài hình học, có đếm token.
- N01 gợi ý không có câu trả lời một chiều: FC giảm lỗi cú pháp nhưng có thể giảm linh hoạt ở nhiều lời gọi.
- N05 và N06 gợi ý cái giá về suy luận của ép khuôn chủ yếu đến từ việc *không chừa chỗ cho lập luận*, chứ không từ bản thân ràng
  buộc. Cả hai đều chỉ đo mô hình mở ≤32B.
- Với AlgoSim (Gemini, function calling gốc), đây là giả thuyết để đo, không phải kết luận.

### (e) DSL / FactGraph / constrained decoding / compiler-in-the-loop có lợi ích đo được đủ để thêm một lớp vào AlgoSim?

| Ứng viên | Bằng chứng có lợi trong tập đọc | Điều kiện / lẫn yếu tố | Kết luận cho AlgoSim |
|---|---|---|---|
| **DSL gọn** thay JSON function calling | Không có so sánh có kiểm soát nào. N01: chế độ prompt (gần DSL dạng văn bản) linh hoạt hơn nhưng lỗi giải mã cao hơn ≈2,3× [C]. W21 đổi IR cùng lúc với mô hình (bản 1) | Mọi số đều lẫn yếu tố hoặc không phải hình | **Thiếu bằng chứng.** Không thêm lớp. Chỉ đo nếu số token prompt/đầu ra là nút thắt thật (A5) |
| **FactGraph** (đồ thị dữ kiện trung gian) | W04/W07/N10 dùng tập literal/CDL làm IR cho *suy luận*, có kết quả tốt [C]. Không bài nào so "có lớp đồ thị dữ kiện" với "không có" cho *dựng hình* | Lợi ích đo được nằm ở bộ giải định lý, không ở khâu dựng | **Thiếu bằng chứng** cho vai trò này. Không suy ra được là cần |
| **Constrained decoding** | N06: ràng buộc ≥ tự do khi chừa trường lập luận [C]. N05: +đến 10 điểm so với baseline, mô hình mở [C]. W26: chiều ngược [C]. W24: ít lỗi chạy hơn [C, tóm tắt] | Đều là mô hình mở hoặc framework cục bộ. Với Gemini chỉ có số độ phủ schema cũ (2024-10-31) [C] | **Không có bằng chứng cho Gemini.** Đáng kiểm là có/không trường lập luận tự do trước lời gọi, không phải thêm một bộ giải mã |
| **Compiler-in-the-loop** (phản hồi engine → model sửa) | N07: một vòng thường đủ, cải thiện sau vòng 1 ≤0,1 điểm; phản hồi cần thông tin thực thi [C]. W10: 94,7→98,7% với ≤5 vòng (60–220 bài, chấm tay) [C]. W11: phục hồi 1,17–1,79 bước nhưng **không** có ablation có/không [C] | Chỉ W10 là hình học, chấm tay, đề đã sửa cho đủ dữ kiện. N07 không phải hình | **Có tín hiệu nhưng yếu cho hình học.** Ứng viên rẻ nhất là trần 1 vòng sửa với chẩn đoán tất định. Phải đo (A1–A4 có biến thể) trước khi coi là cần. Không được để vòng sửa mở cửa cho model tự đưa toạ độ (R0) |
| **Semantic normalization có tiền điều kiện** | Không có số đo trực tiếp. W11 chuẩn hoá ở khâu dữ liệu; W10 chuẩn hoá ngầm bằng LLM; N08 cảnh báo diễn đạt lại đổi nghĩa [C] | — | **Thiếu bằng chứng ngoài.** Giá trị phải đến từ ablation A3 trên bộ diễn đạt lại có cặp đối chứng |

**Độ dài ký hiệu (`a`, `2a`, `a√3`).**

- N05 dùng GSM-Symbolic: "names and numerical values are replaced with symbolic variables", và kiểm tương đương bằng Z3 [C].
  Đây là tiền lệ cho *chấm đáp án ký hiệu bằng solver*, ngoài hình học.
- W11 chuẩn hoá khoảng cách bất biến theo tỉ lệ toàn cục [C]. W01 quy suy luận ký hiệu về kiểm trên mô hình số ngẫu nhiên (bản
  1) [C].
- N11 tham số hoá độ dài rồi **thế số** [C]. W09 ví dụ dùng số cụ thể; có độ dài ký hiệu: NR.
- Trong tập đọc, **chưa thấy** công trình dựng hình không gian với độ dài tự do ký hiệu và kiểm quan hệ chính xác. Đây là khoảng
  trống trong tập đọc, không phải tuyên bố mới.

---

## 5. Đề xuất ablation

Luật chung:

- Đăng ký trước tập bài, mô hình, k lần lặp, ngân sách và luật dừng.
- Mọi lượt gọi mô hình thật cần quyết định của người dùng theo luật kho.
- Không dùng pilot LLM_ONLY 0/10 làm nhánh so sánh hay bằng chứng.
- Ablation nào làm được **0 lượt gọi** (chạy lại engine trên đầu ra đã ghi, hoặc fixture) thì ghi rõ và làm trước.
- Thước chính ở mọi ablation:
  - tỉ lệ bài được phục vụ đúng (positive served, mọi quan hệ được kiểm);
  - tỉ lệ từ chối đúng (fail-closed trên bài thiếu dữ kiện/ngoài phạm vi, theo N09);
  - phân loại lỗi đăng ký trước, theo danh mục của W11/N03: tham chiếu chưa định nghĩa, hàm không tồn tại, tham số thiếu/sai
    kiểu, trích dẫn không khớp, tiền điều kiện hỏng, quan hệ không thoả;
  - token đầu vào/đầu ra lấy từ `usage` của API.

**A1 — Chọn hàm từ registry (function selection).**

- *Bỏ gì:* thay "chọn lời gọi từ registry đóng có kiểu, theo mệnh đề" bằng "mô hình viết một chương trình kiến thiết hoàn chỉnh"
  trên cùng từ vựng hàm (dạng W11). Giữ nguyên engine phía sau, cùng mô hình, cùng prompt nền.
- *Đo gì:*
  - tỉ lệ phục vụ đúng;
  - tỉ lệ "undefined reference" và "hàm không tồn tại";
  - token đầu ra/bài.
- *Bác bỏ giá trị khi:* nhánh "viết cả chương trình" đạt tỉ lệ phục vụ đúng không thấp hơn quá biên đăng ký trước, **và** không
  có nhiều lỗi tham chiếu/hàm lạ hơn. Khi đó tầng chọn hàm theo mệnh đề không có giá trị đo được ngoài engine.

**A2 — Neo nguồn (source grounding).**

- *Bỏ gì:* ba nhánh.
  - (i) đầy đủ: trích dẫn bắt buộc + kiểm tất định;
  - (ii) giữ trường trích dẫn nhưng engine **không** kiểm;
  - (iii) bỏ hẳn trường trích dẫn khỏi schema hàm.
  - Tách (ii) khỏi (iii) vì N04 cho thấy chỉ riêng việc thêm trường nguồn đã đổi bề mặt mô hình.
- *Đo gì:*
  - tỉ lệ lời gọi có đối số không được đề hỗ trợ, so với nhãn dữ kiện chuẩn của từng bài. Phần kiểm này tất định, làm được 0 lượt
    gọi trên đầu ra đã ghi;
  - tỉ lệ **từ chối oan**: lời gọi đúng bị loại vì trích dẫn lệch dấu, Unicode, khoảng trắng hay span không liền (W22);
  - tỉ lệ phục vụ đúng.
- *Bác bỏ giá trị khi:* (i) không giảm đối số không được hỗ trợ so với (ii)/(iii), **hoặc** tỉ lệ từ chối oan vượt ngưỡng đăng ký
  trước làm tỉ lệ phục vụ đúng thấp hơn nhánh (iii).

**A3 — Chuẩn hoá ngữ nghĩa (semantic normalization).**

- *Bỏ gì:* ba nhánh.
  - (i) đầy đủ: luật chuẩn hoá có tiền điều kiện;
  - (ii) không chuẩn hoá: engine chỉ nhận quan hệ chính tắc, ví dụ chỉ `perpendicular_line_plane` tường minh;
  - (iii) chuẩn hoá **không** tiền điều kiện: luôn ánh xạ "SA là đường cao" ⇒ SA ⊥ (ABC).
- *Đo gì:*
  - trên bộ diễn đạt lại có chuyên gia kiểm giữ nghĩa (theo N08): tỉ lệ cho cùng tập dữ kiện chính tắc giữa các diễn đạt;
  - trên **cặp đối chứng** mà tiền điều kiện sai: tỉ lệ chuẩn hoá sai.
  - Nếu đầu vào là tập lời gọi cố định (fixture), toàn bộ đo được 0 lượt gọi.
- *Bác bỏ giá trị khi:* (ii) đạt độ nhất quán ngang (i), tức mô hình đã tự chuẩn hoá như W10/W11 ⇒ lớp chuẩn hoá thừa. **Hoặc**
  (iii) ngang (i) trên cặp đối chứng, tức tiền điều kiện chưa từng có tác dụng ⇒ chưa chứng minh được giá trị của tiền điều kiện.
  Muốn kết luận phải có cặp đối chứng trước.

**A4 — Hợp thành hàm (function composition).**

- *Bỏ gì:* hai biến thể độc lập.
  - A4a: bỏ việc engine giải phụ thuộc/thứ tự. Mô hình phải phát lời gọi theo thứ tự thực thi được với nhãn tường minh (kiểu N02).
  - A4b: bỏ các hàm hợp thành bậc cao (`pyramid`, `prism`, `regular_polygon`), chỉ còn primitive. Tương tự thư viện cơ bản vs
    mở rộng ở W01.
- *Đo gì:*
  - tỉ lệ phục vụ đúng;
  - lỗi thứ tự/tham chiếu, tách riêng mẫu nhiều đầu vào `{A,B}→C` theo N02;
  - số lời gọi và token đầu ra/bài.
- *Bác bỏ giá trị khi:* A4a không tăng lỗi tham chiếu/thứ tự và không giảm tỉ lệ phục vụ đúng ⇒ việc engine giải phụ thuộc không
  có giá trị đo được. A4b không giảm tỉ lệ phục vụ đúng và không tăng token đáng kể ⇒ hàm hợp thành chỉ là tiện lợi kỹ thuật,
  không phải đóng góp đo được.

**A5 — Biểu diễn gọn (compact representation). CÓ ĐIỀU KIỆN.**

- *Điều kiện chạy:* chỉ chạy khi số đo token từ A1–A4 cho thấy token chiếm phần đáng kể chi phí/độ trễ, **hoặc** schema hàm chạm
  giới hạn hỗ trợ schema của Gemini (N06). Với bằng chứng hiện có (mục 4e), **chưa** có lý do để chạy.
- *Bỏ gì:* thay JSON function calling gốc bằng DSL dòng gọn, parse tất định, cùng ngữ nghĩa registry. Thêm biến thể có/không
  trường lập luận tự do đứng trước (N05/N06).
- *Đo gì:*
  - token đầu vào (khai báo hàm) và đầu ra;
  - tỉ lệ lỗi parse;
  - tỉ lệ phục vụ đúng.
- *Bác bỏ giá trị khi:* DSL không giảm token quá ngưỡng đăng ký trước, **hoặc** giảm token nhưng tăng lỗi parse / giảm tỉ lệ phục
  vụ đúng. N01 cho thấy chế độ văn bản tự do có ≈2,3× lỗi giải mã.

---

## 6. Danh mục tham khảo (bài mới và mức xác minh cập nhật)

| Mã | Tham khảo | Mức xác minh |
|---|---|---|
| W04 | Lu, P., Gong, R., Jiang, S., Qiu, L., Huang, S., Liang, X., Zhu, S.-C. (2021). Inter-GPS: Interpretable Geometry Problem Solving with Formal Language and Symbolic Reasoning. *Proc. ACL-IJCNLP 2021 (Long Papers)*, 6774–6786. DOI 10.18653/v1/2021.acl-long.528. https://aclanthology.org/2021.acl-long.528/ | VERIFIED_PRIMARY |
| W07 | Zhang, X., Zhu, N., He, Y., et al. (2023). FormalGeo: An Extensible Formalized Framework for Olympiad Geometric Problem Solving. Preprint, arXiv:2310.18021 (v6). DOI 10.48550/arXiv.2310.18021 | VERIFIED_PRIMARY |
| W08 | Wang, P., Zhang, M.-L., Cao, J., et al. (2026). Geoparsing: Diagram Parsing for Plane and Solid Geometry with a Unified Formal Language. ACL 2026 (theo comments arXiv, bản 1). arXiv:2604.11600. DOI: NR (bản 1) | VERIFIED_PRIMARY |
| W09 | Wang, P., Yang, C., Li, Z.-Z., et al. (2025). SOLIDGEO: Measuring Multimodal Spatial Math Reasoning in Solid Geometry. Preprint, arXiv:2505.21177 (v2). DOI 10.48550/arXiv.2505.21177 | VERIFIED_PRIMARY |
| W10 | Wang, J., Zhang, T., Yu, H., Wang, J., Huang, H. (2025). MagicGeo: Training-Free Text-Guided Geometric Diagram Generation. Preprint, arXiv:2502.13855 (v1) | VERIFIED_PRIMARY |
| W11 | Kim, J., Yang, R., Zhang, H. (2026). GeoBuildBench: A Benchmark for Interactive and Executable Geometry Construction from Natural Language. Preprint, arXiv:2605.13167 (v1) | VERIFIED_PRIMARY |
| W12 | Wei, J., Jia, C., Bai, X., et al. (2025). GGBench: A Geometric Generative Reasoning Benchmark for Unified Multimodal Models. Preprint, arXiv:2511.11134 (v2) | VERIFIED_PRIMARY |
| W22 | Herzig, J., Berant, J. (2021). Span-based Semantic Parsing for Compositional Generalization. ACL 2021 (theo comments arXiv, bản 1). arXiv:2009.06040 | VERIFIED_PRIMARY |
| N01 | Patil, S. G., Mao, H., Yan, F., Ji, C. C.-J., Suresh, V., Stoica, I., Gonzalez, J. E. (2025). The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models. *Proc. ICML 2025*, PMLR 267, 48371–48392. DOI: NR. https://proceedings.mlr.press/v267/patil25a.html | VERIFIED_PRIMARY |
| N02 | Basu, K., Abdelaziz, I., Kate, K., et al. (2024). NESTFUL: A Benchmark for Evaluating LLMs on Nested Sequences of API Calls. Preprint, arXiv:2409.03797 (v3, 2025). DOI 10.48550/arXiv.2409.03797 | VERIFIED_PRIMARY |
| N03 | Li, M., Zhao, Y., Yu, B., Song, F., Li, H., Yu, H., Li, Z., Huang, F., Li, Y. (2023). API-Bank: A Comprehensive Benchmark for Tool-Augmented LLMs. EMNLP 2023 (theo comments arXiv). arXiv:2304.08244. DOI 10.48550/arXiv.2304.08244 | VERIFIED_PRIMARY |
| N04 | Sequeira, R., Damianakis, S., Iqbal, U., Psounis, K. (2026). Agent-Sentry: Bounding LLM Agents via Execution Provenance. Preprint, arXiv:2603.22868 (v2). DOI 10.48550/arXiv.2603.22868 | VERIFIED_PRIMARY |
| N05 | Banerjee, D., Suresh, T., Ugare, S., Misailovic, S., Singh, G. (2025). CRANE: Reasoning with constrained LLM generation. ICML 2025 (theo comments arXiv; header PDF ghi PMLR 267). arXiv:2502.09061. DOI 10.48550/arXiv.2502.09061 | VERIFIED_PRIMARY |
| N06 | Geng, S., Cooper, H., Moskal, M., Jenkins, S., Berman, J., Ranchin, N., West, R., Horvitz, E., Nori, H. (2025). JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models. Preprint (PDF: "Under review"), arXiv:2501.10868 (v3). DOI 10.48550/arXiv.2501.10868 | VERIFIED_PRIMARY |
| N07 | Chen, X., Lin, M., Schärli, N., Zhou, D. (2023). Teaching Large Language Models to Self-Debug. Preprint (trang arXiv/PDF v2 không ghi venue), arXiv:2304.05128. DOI 10.48550/arXiv.2304.05128 | VERIFIED_PRIMARY |
| N08 | Chang, S., Wang, J., Dong, M., et al. (2023). Dr.Spider: A Diagnostic Evaluation Benchmark towards Text-to-SQL Robustness. ICLR 2023 (comments arXiv + header PDF). arXiv:2301.08881. DOI 10.48550/arXiv.2301.08881 | VERIFIED_PRIMARY |
| N09 | Li, Q., Cui, L., Zhao, X., Kong, L., Bi, W. (2024). GSM-Plus: A Comprehensive Benchmark for Evaluating the Robustness of LLMs as Mathematical Problem Solvers. ACL 2024 (theo comments arXiv). arXiv:2402.19255. DOI 10.48550/arXiv.2402.19255 | VERIFIED_PRIMARY |
| N10 | Xu, R., Cheng, H., Dong, B., Wang, Q. (2026). Hilbert-Geo: Solving Solid Geometric Problems by Neural-Symbolic Reasoning. CVPR 2026 (theo comments arXiv). arXiv:2605.16385 (v3). DOI 10.48550/arXiv.2605.16385 | VERIFIED_PRIMARY |
| N11 | Wu, C., Lian, S., Liu, Z., et al. (2025). DynaSolidGeo: A Dynamic Benchmark for Genuine Spatial Mathematical Reasoning of VLMs in Solid Geometry. Preprint, arXiv:2510.22340 (v2). DOI 10.48550/arXiv.2510.22340 | VERIFIED_PRIMARY |

Các W còn lại giữ nguyên tham khảo và mức xác minh như bản 1.

**Thống kê mức xác minh** (37 công trình trong hai bản; không tính mục bị loại):

- `VERIFIED_PRIMARY`: 22. Gồm 7 từ bản 1 (W01, W02, W08, W10, W11, W12, W25), 4 nâng cấp (W04, W07, W09, W22) và 11 mới (N01–N11).
- `VERIFIED_ABSTRACT_ONLY`: 15 (W03, W05, W06, W13–W21, W23, W24, W26).
- `NOT_VERIFIED`, loại và không dùng: ToolLLM (2307.16789), GSM-Symbolic (2410.05229), blog Kurt "Say What You Mean", arXiv
  2607.00895, RLSeek (ACL 2026), mô hình ToolHACE (Featherless), GeoVLMath (2510.11020). Cộng thêm hai mục `NOT_VERIFIED` đã
  loại ở bản 1: GeoGramBench, PAGER.
