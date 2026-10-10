# Ma trận tổng quan tài liệu và khoảng trống: dựng hình từ văn bản bằng thư viện hàm hữu hạn

Ngày tìm: 2026-10-10. Đây là tài liệu nghiên cứu cho run `text-to-geometry-functions`, không phải trạng thái hệ thống.
Mọi nhận định về AlgoSim ở đây là **so sánh định tính với ý tưởng thiết kế** (thư viện hàm dựng hữu hạn, có kiểu,
AI chỉ chọn lời gọi hàm có tham số neo vào đề; engine tất định kiểm tiền điều kiện, giải phụ thuộc, dựng chính xác,
kiểm quan hệ, hiển thị). Chúng **không** là tuyên bố về tính mới.

Quy ước nhãn trong toàn bộ file:

- `[C]` = CONFIRMED BY SOURCE: nội dung có trong trang nguồn đã mở (bản tóm tắt hoặc toàn văn, xem cột mức xác minh).
- `[I]` = INFERENCE: suy luận của người tổng hợp, không phải lời của tác giả.
- `[NV]` = NOT VERIFIED: chưa kiểm được trên nguồn gốc.
- `NR` = không được báo cáo trong phần nguồn đã đọc. `NR` **không** có nghĩa là "không có"; với các mục chỉ đọc tóm tắt,
  toàn văn có thể có thông tin đó.

Mức xác minh từng công trình: `VERIFIED_PRIMARY` (đã mở toàn văn / bản HTML đầy đủ hoặc trang chính thức và nhận định nằm
trong đó), `VERIFIED_ABSTRACT_ONLY` (chỉ đọc trang tóm tắt arXiv/ACL/nhà xuất bản), `NOT_VERIFIED` (không mở được, không dùng
làm bằng chứng).

---

## 1. Phạm vi và phương pháp tìm

**Câu hỏi dẫn đường.** Văn liệu nói gì về (a) dựng hình bằng cách kết hợp một thư viện hàm/phép dựng hữu hạn, (b) ánh xạ
văn bản sang lời gọi hàm có neo nguồn (grounding), (c) ảnh hưởng của biểu diễn trung gian (IR) lên token, độ chính xác và khả
năng mở rộng — trong bối cảnh hình học không gian lớp 11–12.

**Truy vấn đã dùng** (công cụ tìm web, 2026-10-10; sau đó mở trực tiếp trang arXiv/ACL/PMLR/PMC/Crossref/PyPI):

1. `Gulwani Korthikanti Tiwari "Synthesizing geometry constructions" PLDI 2011 pdf`
2. `LLM generate 3D solid geometry diagram from text problem pyramid prism arXiv`
3. `large language model GeoGebra commands generation geometry construction arXiv`
4. `GeoBuildBench interactive executable geometry construction natural language arXiv`
5. `solid geometry problem 3D formalization LLM coordinate system construction verifiable arXiv 2025`
6. Tra trực tiếp theo mã arXiv/DOI đã biết trước cho các công trình mà đề bài nêu tên (AlphaGeometry, AlphaGeometry2,
   Inter-GPS/Geometry3K, GeoQA, UniGeo, PGPS, FormalGeo, PAL, PoT, ToRA, Text2CAD, CAD-Recode, SolidGeo, …). Mã arXiv
   được nhớ trước chỉ là **địa chỉ để mở**; mọi thông tin dưới đây lấy từ trang đã mở, không từ trí nhớ.

**Tiêu chí đưa vào.** (i) Năm 2019–2026, ngoại lệ có lý do: Gulwani et al. 2011 (đề bài nêu tên; là tiền thân trực tiếp
của ý "thư viện phép dựng"). (ii) Liên quan trực tiếp tới ít nhất một trong tám chủ đề của đề bài. (iii) Mở được trang nguồn
gốc. (iv) Ưu tiên công trình có cơ chế (IR, engine, kiểm chứng) hơn bài benchmark thuần.

**Đã sàng nhưng loại** (mở trang tóm tắt hoặc chỉ thấy trong kết quả tìm): UniGeo (arXiv 2212.02746 — trùng vai trò với
GeoQA), DiagrammerGPT (arXiv 2310.12128 — sơ đồ khoa học mở, không phải hình học chính xác), "Don't Mesh with Me" (arXiv
2411.15279 — CSG cơ khí, trùng vai trò CAD), SD-GPS (arXiv 2606.27926 — tự hình thức hoá cho giải bài phẳng, trùng vai trò
FormalGeo/Inter-GPS), GeoAux-Bench (arXiv 2603.18662 — dựng phụ cho suy luận, không dựng cảnh), ALCE (arXiv 2305.14627 —
trích dẫn văn bản, xa hơn LangExtract/SpanBasedSP), GeoGramBench và PAGER (chỉ thấy trong kết quả tìm, **không mở** ⇒
`NOT_VERIFIED`, không dùng).

**Giới hạn phương pháp (phải khai).**

- Trang web được đọc qua một công cụ tải trang có bước tóm tắt tự động. Trừ Gulwani et al. 2011 (văn bản PDF được trích
  thô và đọc trực tiếp), các câu đặt trong ngoặc kép bên dưới là câu do công cụ trích từ trang; **trước khi đưa vào chương
  khoá luận phải đối chiếu lại với bản gốc** (số trang/mục).
- Bản HTML của GGBench chỉ đọc được ~100k/145k ký tự đầu; GeoBuildBench ~100k/105k ký tự.
- GitHub không truy cập được từ môi trường này (lỗi mạng); LangExtract được xác minh qua trang PyPI chính thức của gói.
- Tìm kiếm một người, một ngày, chủ yếu tiếng Anh; **không** quét văn liệu tiếng Việt/tiếng Trung về phần mềm giáo dục hình
  học không gian. Vì vậy mọi "khoảng trống" dưới đây chỉ là khoảng trống **trong tập đã đọc**.

---

## 2. Ma trận văn liệu

26 công trình, mã W01–W26. Bảng tách làm ba phần nối theo mã.

### 2a. Định danh, đầu vào, IR, cách chọn phép dựng, engine

| Mã | Công trình | Năm | DOI/URL | Mức xác minh | Đầu vào | Biểu diễn trung gian | Cách chọn phép dựng | Engine hình học |
|---|---|---|---|---|---|---|---|---|
| W01 | Gulwani, Korthikanti, Tiwari — Synthesizing Geometry Constructions (GeoSynth) | 2011 | DOI 10.1145/1993498.1993505 (bản ghi Crossref); PDF: microsoft.com/en-us/research/publication/synthesizing-geometry-constructions/ | VERIFIED_PRIMARY | Đặc tả hình thức `GIVEN … that satisfy pre / CONSTRUCT … that satisfy post` [C]; front-end tiếng Anh là "ongoing work" [C] | Chương trình tuần tự trên thư viện hàm thước-compa (Table 1) + hàm dẫn xuất (Table 2) [C] | Tìm kiếm vét cạn tiến, cắt tỉa bằng heuristic "goodness" hướng đích [C] | Hàm thư viện là mã thực thi trên đối tượng số cụ thể [C] |
| W02 | Trinh et al. — Solving olympiad geometry without human demonstrations (AlphaGeometry) | 2024 | DOI 10.1038/s41586-023-06747-5 (Nature 625:476–482, hiển thị trên PMC) | VERIFIED_PRIMARY | Bài đã chuyển sang ngôn ngữ hình học chuyên dụng (dòng GEX/JGEX/MMP-Geometer/GeoLogic); bài IMO được "adapted … to a narrower, specialized environment" [C] | Tiền đề kiến thiết, dựng từng đối tượng một [C] | Mô hình ngôn ngữ đề xuất một phép dựng phụ mỗi lượt, beam search k=512 [C] | DD (cơ sở suy diễn) + AR (lập luận đại số, khử Gauss) [C] |
| W03 | Chervonyi et al. — AlphaGeometry2 | 2025 | arXiv:2502.03544; DOI: NR | VERIFIED_ABSTRACT_ONLY (preprint) | Ngôn ngữ AG mở rộng; "progress" hướng tới đầu vào ngôn ngữ tự nhiên [C] | Ngôn ngữ AG mở rộng: chuyển động đối tượng, phương trình tuyến tính góc/tỉ số/khoảng cách, bài không kiến thiết [C] | LM dựa trên Gemini + chia sẻ tri thức giữa các cây tìm kiếm [C] | Engine ký hiệu cải tiến [C]; chi tiết NR |
| W04 | Lu et al. — Inter-GPS | 2021 | arXiv:2105.04165 (ACL 2021 theo comments); DOI arXiv 10.48550/arXiv.2105.04165 | VERIFIED_ABSTRACT_ONLY | Văn bản + sơ đồ [C] | Ngôn ngữ hình thức (Geometry3K chú thích dày) [C] | Văn bản: phân tích theo luật; sơ đồ: phát hiện đối tượng nơ-ron [C] | Luật định lý có điều kiện + bộ dự đoán chuỗi định lý [C] |
| W05 | Chen et al. — GeoQA / NGS | 2021 | arXiv:2105.14517 (Findings of ACL 2021 theo comments); DOI arXiv 10.48550/arXiv.2105.14517 | VERIFIED_ABSTRACT_ONLY | Văn bản + sơ đồ [C] | Chương trình giải có chú thích [C] | Mạng nơ-ron sinh chương trình [C] | Thực thi chương trình số [I] (chi tiết NR) |
| W06 | Zhang, Yin, Liu — PGPS / PGPSNet | 2023 | arXiv:2302.11097 (IJCAI 2023 theo comments); DOI arXiv 10.48550/arXiv.2302.11097 | VERIFIED_ABSTRACT_ONLY | Văn bản + sơ đồ [C] | Mệnh đề văn bản cơ bản mô tả sơ đồ + chương trình lời giải [C] | Bộ giải nơ-ron đa phương thức [C] | NR |
| W07 | Zhang et al. — FormalGeo / FGPS | 2023 | arXiv:2310.18021; DOI arXiv 10.48550/arXiv.2310.18021 | VERIFIED_ABSTRACT_ONLY (preprint) | Bài đã hình thức hoá [C] | Hệ hình thức hình học phẳng: 88 vị từ, 196 định lý [C] | Tìm kiếm (backward DFS) [C] | FGPS (Python): vừa là bộ kiểm tương tác vừa là bộ giải [C] |
| W08 | Wang et al. — Geoparsing (GDP-29K) | 2026 | arXiv:2604.11600 (ACL 2026 theo comments); DOI: NR | VERIFIED_PRIMARY (HTML v2) | Ảnh sơ đồ + chỉ dẫn phân tích; có nhận văn bản đề không: NR [C] | Ngôn ngữ hình thức hợp nhất phẳng + không gian; khối là primitive bậc cao (`solid Pyramid O-ABC`, `solid Cube ABCD-A1B1C1D1`), mặt phẳng là danh sách điểm [C] | MLLM sinh mô tả (SFT + RL với phần thưởng kiểm được) [C] | Không có engine dựng; toạ độ số: NR [C] |
| W09 | Wang et al. — SolidGeo | 2025 | arXiv:2505.21177; DOI: NR | VERIFIED_ABSTRACT_ONLY (preprint) | Bài hình không gian có ngữ cảnh hình ảnh [C] | NR (benchmark đánh giá) | NR | NR |
| W10 | Wang et al. — MagicGeo | 2025 | arXiv:2502.13855; DOI: NR | VERIFIED_PRIMARY (HTML v1, preprint) | Mô tả văn bản của sơ đồ [C] | Ngôn ngữ hình thức gồm biến điểm + ràng buộc [C] | LLM dịch văn bản sang ngôn ngữ hình thức [C] | Bộ giải tự viết dùng "computational analytical geometry methods", duyệt lần lượt từng biến; số hay ký hiệu: NR [C] |
| W11 | Kim, Yang, Zhang — GeoBuildBench | 2026 | arXiv:2605.13167; DOI: NR | VERIFIED_PRIMARY (HTML v1, preprint) | Bài hình phẳng tiếng Trung dạng sách giáo khoa [C] | Chương trình DSL kiến thiết (không phải DSL ràng buộc), `command : inputs -> outputs` [C] | LLM/agent viết toàn bộ chương trình, sửa lặp tối đa 5 vòng [C] | Bộ thực thi DSL + kiểm điều kiện số với dung sai cố định [C] |
| W12 | Wei et al. — GGBench | 2025 | arXiv:2511.11134; DOI: NR | VERIFIED_PRIMARY (HTML v2, đọc một phần; preprint) | Bài dựng hình [C] | Mã GeoGebra từng bước + văn bản + ảnh [C] | Mô hình sinh lập luận + mã [C] | GeoGebra (thực thi mã) [C] |
| W13 | Mouselinos, Michalewski, Malinowski — Beyond Lines and Circles | 2024 | arXiv:2402.03877 (EMNLP Findings 2024 theo comments) | VERIFIED_ABSTRACT_ONLY | Bài dựng hình [C] | NR | LLM; khung đa tác tử đối thoại nội bộ [C] | NR |
| W14 | Macke et al. — Learning to solve geometric construction problems from images | 2021 | arXiv:2106.14195; DOI: NR | VERIFIED_ABSTRACT_ONLY (venue NR) | Chỉ ảnh (trò chơi Euclidea) [C] | NR | Mask R-CNN cải biên + tìm kiếm cây [C] | Môi trường Euclidea [C] |
| W15 | Gao et al. — PAL | 2023 | arXiv:2211.10435; PMLR v202 pp. 10764–10799 (ICML 2023); DOI: NR | VERIFIED_ABSTRACT_ONLY | Bài toán ngôn ngữ tự nhiên [C] | Chương trình Python [C] | LLM viết chương trình [C] | Trình thông dịch Python [C] |
| W16 | Chen et al. — Program of Thoughts | 2023 | arXiv:2211.12588 (TMLR 2023 theo trang arXiv); DOI: NR | VERIFIED_ABSTRACT_ONLY | Bài toán số [C] | Chương trình [C] | LLM (chủ yếu Codex) [C] | Trình thông dịch ngoài [C] |
| W17 | Gou et al. — ToRA | 2024 | arXiv:2309.17452 (ICLR 2024 theo comments); DOI: NR | VERIFIED_ABSTRACT_ONLY | Bài toán [C] | Quỹ đạo xen kẽ ngôn ngữ tự nhiên + lời gọi công cụ [C] | Mô hình huấn luyện bắt chước trên quỹ đạo dùng công cụ [C] | Thư viện tính toán, bộ giải ký hiệu [C] |
| W18 | Patil et al. — Gorilla | 2023 | arXiv:2305.15334; DOI: NR | VERIFIED_ABSTRACT_ONLY (preprint theo trang) | Chỉ dẫn ngôn ngữ tự nhiên [C] | Lời gọi API [C] | LLaMA tinh chỉnh + bộ truy hồi tài liệu [C] | Không phải hình học |
| W19 | Khan et al. — Text2CAD | 2024 | arXiv:2409.17106 (NeurIPS 2024 Spotlight theo comments); DOI: NR | VERIFIED_ABSTRACT_ONLY | Chỉ dẫn văn bản nhiều mức (mới học → chuyên gia) [C] | Chuỗi CAD tham số [C] | Transformer tự hồi quy end-to-end [C] | Nhân CAD (chi tiết NR) |
| W20 | Rukhovich et al. — CAD-Recode | 2024 | arXiv:2412.14042; DOI: NR | VERIFIED_ABSTRACT_ONLY (preprint) | Đám mây điểm [C] | Mã Python dựng lại mô hình CAD [C]; tên thư viện CAD: NR trên trang tóm tắt | LLM nhỏ làm decoder [C] | Thực thi mã Python [C] |
| W21 | Xie, Ju — Text-to-CadQuery | 2025 | arXiv:2505.06507; DOI: NR | VERIFIED_ABSTRACT_ONLY (preprint) | Văn bản [C] | Mã CadQuery, bỏ biểu diễn CAD trung gian [C] | 6 LLM mã nguồn mở tinh chỉnh [C] | CadQuery [C] |
| W22 | Herzig, Berant — Span-based Semantic Parsing | 2021 | arXiv:2009.06040 (ACL 2021 theo comments); DOI: NR | VERIFIED_ABSTRACT_ONLY | Câu ngôn ngữ tự nhiên [C] | Cây span trên câu, mã hoá cách chương trình con hợp thành trên span [C] | Parser span (CKY mở rộng) [C] | Không phải hình học |
| W23 | Ellis et al. — DreamCoder | 2020 | arXiv:2006.08381; DOI: NR | VERIFIED_ABSTRACT_ONLY (venue NR trên trang) | Bài toán quy nạp chương trình [C] | Ngôn ngữ (thư viện) học được [C] | Mạng nơ-ron dẫn tìm kiếm chương trình [C] | Không chuyên hình học; có miền vẽ hình và dựng cảnh [C] |
| W24 | Poesia et al. — Synchromesh | 2022 | arXiv:2201.11227; DOI: NR | VERIFIED_ABSTRACT_ONLY (venue NR trên trang) | Mô tả ngôn ngữ tự nhiên [C] | Chương trình SQL/Vega-Lite/SMCalFlow [C] | GPT-3/Codex + Constrained Semantic Decoding + Target Similarity Tuning [C] | Không phải hình học |
| W25 | Google — LangExtract (thư viện Python, v1.7.1) | — (phần mềm) | pypi.org/project/langextract ; repo github.com/google/langextract (không mở được) | VERIFIED_PRIMARY (trang PyPI chính thức; không phải bài phản biện) | Văn bản phi cấu trúc + chỉ dẫn + ví dụ few-shot [C] | Trích xuất có lược đồ [C] | LLM, sinh có kiểm soát ở mô hình hỗ trợ [C] | Không phải hình học |
| W26 | Tam et al. — Let Me Speak Freely? | 2024 | arXiv:2408.02442; DOI: NR | VERIFIED_ABSTRACT_ONLY (preprint) | Nhiệm vụ suy luận/tri thức [C] | Đầu ra có định dạng (JSON, XML) vs tự do [C] | LLM [C] | Không phải hình học |

### 2b. Kết hợp primitive, phụ thuộc, grounding, kiểm chứng, chiều, dữ liệu

| Mã | Kết hợp primitive | Xử lý phụ thuộc | Grounding | Kiểm chứng | 2D/3D | Dữ liệu thực nghiệm |
|---|---|---|---|---|---|---|
| W01 | Thư viện mở rộng gồm "basic constructions found in textbook chapters" [C]; không có goodness: thư viện mở rộng giải 19/25, thư viện cơ bản không giải được trong 10 phút [C] | Đối tượng là biến chương trình, các bước tuần tự [C] | NR (không nhận ngôn ngữ tự nhiên) [C] | Quy kiểm chứng về kiểm thử ngẫu nhiên trên mô hình cụ thể (dựa trên định lý kiểu kiểm đồng nhất đa thức ngẫu nhiên) + thử lại trên mẫu ngẫu nhiên thứ hai [C] — xác suất, số | 2D (thước-compa) [C] | 25 bài từ sách giáo khoa/đề thi; tất cả giải trong vài giây, 18 bài < 1 s [C] |
| W02 | Phép dựng phụ thêm vào tiền đề [C] | Bộ dựng kiến thiết từng đối tượng [C]; thứ tự chi tiết: NR | NR | Chứng minh ký hiệu DD+AR [C] | 2D: "a theorem prover for Euclidean plane geometry" [C] | 100 triệu ví dụ tổng hợp (~9 triệu có dựng phụ); IMO-AG-30 giải 25 [C] |
| W03 | Ngôn ngữ mở rộng [C] | NR | NR | Engine ký hiệu [C] | NR trên tóm tắt (bài IMO hình học) | Độ phủ IMO 2000–2024: 66%→88%; tỉ lệ giải 54%→84% [C] |
| W04 | NR | NR | Phân tích văn bản theo luật sang ngôn ngữ hình thức [C]; neo span: NR | Lập luận ký hiệu từng bước, diễn giải được [C] | NR trên tóm tắt (Geometry3K: [I] phẳng) | Geometry3K: 3.002 bài; GEOS [C] |
| W05 | NR | NR | NR | NR; kém xa người [C] | NR trên tóm tắt | GeoQA: 4.998 bài có chương trình chú thích [C] |
| W06 | NR | NR | Mệnh đề sinh từ sơ đồ [C]; neo vào đề: NR | NR | NR trên tóm tắt | PGPS9K + Geometry3K [C] |
| W07 | Vị từ + định lý [C] | NR | NR | Chứng minh "readable, traceable, and verifiable" [C] | 2D ("formal plane geometry system") [C] | FormalGeo7K: 6.981 bài (tăng cường tới 133.818); formalgeo-imo: 18 bài [C] |
| W08 | Primitive khối bậc cao [C] | Quan hệ theo nhãn điểm [C] | Neo vào ảnh, không vào văn bản [C] | Phần thưởng: định dạng (nhị phân) + precision có trọng số theo loại primitive so với đáp án chuẩn [C] | 2D + 3D [C] | GDP-29K (20k phẳng, 9k không gian); SGDP-1K overall 94,9, perfect parsing 70,9%; SolidGeo 59,0→62,1 khi thêm mô tả [C] |
| W09 | NR | NR | NR | NR | 3D [C] | 3.113 bài K-12 và thi; chủ đề: hình chiếu, khai triển, đo không gian, vectơ không gian [C] |
| W10 | Ràng buộc là "function names" của bộ giải [C] | Bộ giải duyệt lần lượt từng biến [C] | NR | Bộ giải không tìm được nghiệm ⇒ phản hồi về LLM, tối đa 5 vòng [C]; dung sai: NR; độ chính xác kiểm thủ công [C] | 2D ("our experiments focus on plane geometry") [C] | MagicGeoBench: 220 bài (70 đường tròn, 70 tam giác, 80 tứ giác); CLIP + khảo sát người; độ chính xác tự hình thức hoá 94,7%→98,7% khi có kiểm chứng; bài phức tạp có thể > 1 giờ [C] |
| W11 | 18 lệnh: primitive, toán tử dựng (intersect, parallel_line, orthogonal_line, midpoint, rotate), đo/số học [C]; danh sách lệnh không nhất quán giữa phụ lục và system prompt [C] | Đầu ra có tên, lệnh sau tham chiếu; "Define before use", "One definition per label" [C] | NR | Điều kiện đo/góc đánh giá "under fixed numerical tolerances" [C]; có kiểu: NR | 2D; phần Limitations loại trừ 3D [C] | 489 bài; GPT-5.1 78,9%, Gemini-3-Flash 75,3%, Qwen3-VL-235B 42,2%, LLaMA-3.2-90B-Vision 21,3%; ảo giác thường gặp nhất: "undefined reference" [C] |
| W12 | Bước dựng GeoGebra [C] | NR | NR | Mã GeoGebra là "machine-verifiable ground truth"; chấm bằng VLM (GPT-4o) + Pass@1 thực thi; tương quan với người r=0,9295 [C] | Không nêu rõ (đối chiếu với SolidGeo như công trình 3D) [C]; [I] phẳng | 1.411 bài; mô hình sinh và chạy mã đạt đúng hình học cao hơn rõ; độ đo pixel tương quan yếu với tính hợp lệ hình học [C] |
| W13 | NR | NR | Mô hình "hallucinate objects and their placements" [C] | NR | 2D ("2D spatial relationships") [C] | NR trên tóm tắt; benchmark Euclidea: [NV] |
| W14 | NR | NR | NR | Môi trường trò chơi [I] | 2D [I] | 68 loại bài, 6 gói cấp đầu: ~92%; loại chưa thấy: 31/68 [C] |
| W15 | NR | NR | NR | Thực thi chương trình [C] | — | 13 nhiệm vụ; GSM8K hơn PaLM-540B CoT 15% tuyệt đối top-1 [C] |
| W16 | NR | NR | NR | Thực thi chương trình [C] | — | 5 bộ toán lời văn + 3 bộ QA tài chính; trung bình ~12% so với CoT [C] |
| W17 | Xen kẽ lời gọi công cụ [C] | NR | NR | Kết quả công cụ quay về mô hình [I] | — | 10 bộ; +13–19% tuyệt đối; ToRA-7B 44,6% MATH [C] |
| W18 | NR | NR | Bộ truy hồi tài liệu API lúc kiểm thử [C] | NR trên tóm tắt | — | APIBench (HuggingFace, TorchHub, TensorHub); giảm ảo giác API [C] |
| W19 | Chỉ dẫn mô tả bước kiểu "drawing circles and extruding them" [C] | Chuỗi tuần tự [C] | NR | Đánh giá chất lượng hình, độ chính xác tham số, độ chính xác hình học [C] | 3D (CAD) [C] | ~170K mô hình, ~660K chú thích sinh bởi Mistral + LLaVA-NeXT [C] |
| W20 | Mã Python [C] | Thứ tự thực thi mã [I] | NR | NR trên tóm tắt | 3D [C] | 1 triệu chuỗi CAD sinh thủ tục; DeepCAD, Fusion360, CC3D [C] |
| W21 | Mã CadQuery [C] | Thứ tự thực thi mã [I] | NR | Exact match, Chamfer distance [C] | 3D [C] | 170K chú thích CadQuery trên Text2CAD; top-1 exact match 58,8%→69,3%; Chamfer giảm 48,6% [C] |
| W22 | Chương trình con hợp thành trên span [C] | Cây span [C] | Mỗi chương trình con gắn với một span đầu vào [C] | NR | — | GeoQuery, SCAN, CLOSURE (tách tổ hợp): 61,0→88,9 [C] |
| W23 | Khái niệm mới xây từ khái niệm cũ, biểu diễn ký hiệu nhiều tầng [C] | NR | NR | NR | Miền vẽ/dựng cảnh: NR về chiều | Nhiều miền quy nạp + vẽ hình, dựng cảnh [C] |
| W24 | NR | NR | NR | Giải mã ràng buộc chỉ lấy mẫu chương trình hợp lệ; ít lỗi chạy hơn [C] | — | SQL, Vega-Lite, SMCalFlow [C] |
| W25 | NR | NR | "Maps every extraction to its exact location in the source text" [C] | Người dùng đối chiếu với văn bản gốc (highlight) [C] | — | NR (thư viện, không có thực nghiệm) |
| W26 | NR | NR | NR | NR | — | Định dạng chặt hơn ⇒ suy giảm suy luận lớn hơn [C] |

### 2c. Trùng và khác với AlgoSim

Toàn bộ cột này là `[I]` (so sánh của người tổng hợp), trừ những chỗ trích nguồn đã đánh `[C]` ở bảng trên.

| Mã | Trùng với AlgoSim [I] | Khác AlgoSim [I] |
|---|---|---|
| W01 | Gần nhất về ý tưởng: thư viện hàm dựng hữu hạn, có hàm dẫn xuất "theo chương sách giáo khoa", chương trình = hợp thành lời gọi hàm | Bộ tổng hợp tự tìm (không có LLM, không đọc đề); kiểm chứng xác suất trên số thực, AlgoSim kiểm chính xác; chỉ 2D |
| W02 | Tách "đề xuất bằng mô hình" khỏi "quyết định bằng engine ký hiệu"; ngôn ngữ kiến thiết làm IR | Mục tiêu chứng minh, không dựng cảnh; bài được chuyển thủ công/bán thủ công sang ngôn ngữ chuyên dụng (cơ chế cụ thể: UNCLEAR); 2D |
| W03 | Đo "độ phủ của ngôn ngữ" trên kho bài thật — giống câu hỏi độ phủ của thư viện hàm | Độ phủ đo trên bài olympiad phẳng; không tách được phần đóng góp của ngôn ngữ với các cải tiến khác |
| W04 | Văn bản → ngôn ngữ hình thức → engine ký hiệu | Mục tiêu giải số đo, không dựng hình 3D; parser theo luật, không phải LLM chọn hàm |
| W05 | IR dạng chương trình có chú thích | Chương trình tính toán đáp số, không phải chương trình dựng; 2D |
| W06 | Mô tả sơ đồ bằng mệnh đề văn bản | Hướng giải bài, đầu vào có ảnh; không dựng |
| W07 | Bộ kiểm hình thức, chứng minh truy vết được | Hệ suy diễn định lý phẳng; không sinh toạ độ, không đọc đề tự do |
| W08 | Primitive khối bậc cao đặt tên theo đỉnh (`Pyramid O-ABC`) gần với hàm dựng khối; có phần không gian | Phân tích ảnh sang mô tả; không dựng, không có toạ độ (NR), không kiểm chính xác |
| W09 | Cùng miền (hình không gian K-12) — ứng viên bộ đánh giá ngoài | Benchmark trả lời câu hỏi, không có cơ chế dựng |
| W10 | LLM không viết toạ độ; bộ giải tất định tính toạ độ; vòng phản hồi khi bộ giải thất bại | IR khai báo (ràng buộc + tối ưu) thay vì lời gọi hàm kiến thiết; 2D; tính chính xác không được nêu |
| W11 | Gần nhất về đường chạy: văn bản → chương trình kiến thiết có đối tượng được đặt tên, "define before use", kiểm điều kiện máy | LLM viết **cả chương trình** (tương ứng tuyến LLM_ONLY cũ của AlgoSim), không chọn từng mệnh đề; dung sai số; 2D; grounding NR |
| W12 | Mã dựng thực thi được làm chuẩn kiểm | Đánh giá bằng VLM-judge, không kiểm quan hệ tất định trong phần đã đọc; [I] phẳng |
| W13 | Bằng chứng LLM bịa đối tượng/vị trí khi dựng hình | Đề xuất đa tác tử, không đề xuất engine tất định |
| W14 | Bài dựng hình có môi trường kiểm | Đầu vào ảnh, không có văn bản |
| W15–W17 | Đẩy tính toán sang bộ thực thi tất định; LLM chỉ lo phân rã | Bộ thực thi đa năng (Python), LLM vẫn viết mã tuỳ ý — ngược với ràng buộc "không viết mã hình học tuỳ ý" |
| W18 | Gọi API có đăng ký; giảm ảo giác bằng truy hồi tài liệu | Không có kiểm tiền điều kiện/quan hệ hình học |
| W19 | Văn bản → chuỗi thao tác dựng 3D có tham số | Hình cơ khí, không phải bài toán có đáp số chính xác; không chọn từ thư viện hữu hạn có kiểu theo đề |
| W20–W21 | IR là mã CAD thực thi được, 3D | LLM viết mã tự do; đo bằng khoảng cách hình học xấp xỉ (Chamfer), không kiểm quan hệ chính xác |
| W22 | Neo từng mảnh chương trình vào span đầu vào; cải thiện tổng quát hoá tổ hợp | Không phải hình học; span là biến ẩn học được, không phải ràng buộc cứng |
| W23 | Thư viện khái niệm hợp thành nhiều tầng | Thư viện **học được**, AlgoSim dùng thư viện **cố định, có kiểu** do người viết |
| W24 | Ràng buộc đầu ra chỉ vào chương trình hợp lệ | Ràng buộc cú pháp/ngữ nghĩa ngôn ngữ đích, không phải tiền điều kiện hình học |
| W25 | Neo mỗi trích xuất vào vị trí chính xác trong văn bản nguồn | Trích xuất thông tin, không sinh lời gọi hàm dựng |
| W26 | Cảnh báo: ép định dạng có thể giảm suy luận — rủi ro cho IR chặt | Không đo IR dạng lời gọi hàm hay hình học |

---

## 3. Ghi chú từng công trình (nguồn của nhận định)

- **W01 Gulwani et al. 2011.** Nguồn: PDF trên trang Microsoft Research, văn bản trích thô và đọc trực tiếp (Abstract, §1, §6,
  §6.1, kết luận); DOI từ bản ghi Crossref (Proc. PLDI 2011, tr. 50–61). Tóm tắt nêu ba ý: "reduction of symbolic reasoning
  to concrete reasoning", "extending the instruction set of the programming language with higher level primitives
  (representing basic constructions found in textbook chapters …)", "pruning the forward exhaustive search using a
  goal-directed heuristic". §6: "GeoSynth successfully solved all the problems in a few seconds: 18 problems were solved in
  less than a second". Kết luận: front-end ngôn ngữ tự nhiên là "ongoing work"; §6.1 ghi "the English text specification of
  a geometry construction problem is often ambiguous".
- **W02 AlphaGeometry.** Nguồn: toàn văn trên PMC (PMC10794143). Ngôn ngữ chuyên dụng "used in GEX, JGEX, MMP/Geometer and
  GeoLogic"; 100 triệu ví dụ tổng hợp; IMO-AG-30 "solves 25"; phạm vi "Euclidean plane geometry"; bài test được
  "adapted … to a narrower, specialized environment". Bài không dùng chữ "manually" theo bản đọc — cách chuyển: UNCLEAR.
- **W03 AlphaGeometry2.** Nguồn: tóm tắt arXiv (v3, 2025-12-08), preprint. Mở rộng ngôn ngữ; độ phủ 66%→88%; giải 54%→84%;
  "progress" hướng tới đầu vào ngôn ngữ tự nhiên — cơ chế dịch: NR.
- **W04 Inter-GPS.** Nguồn: tóm tắt arXiv. Geometry3K 3.002 bài; "rule-based text parsing and neural object detecting";
  bộ dự đoán định lý. Con số độ chính xác: NR trên tóm tắt.
- **W05 GeoQA.** Nguồn: tóm tắt arXiv. 4.998 bài có chương trình chú thích; NGS sinh chương trình; còn xa người.
- **W06 PGPS.** Nguồn: tóm tắt arXiv. Sơ đồ → "basic textual clauses"; PGPS9K có chú thích sơ đồ chi tiết + chương trình lời giải.
- **W07 FormalGeo.** Nguồn: tóm tắt arXiv (v6), preprint. 88 vị từ, 196 định lý; FGPS là bộ kiểm tương tác + bộ giải;
  FormalGeo7K 6.981 bài. Tên GDL/CDL: NR trên tóm tắt.
- **W08 Geoparsing.** Nguồn: HTML toàn văn v2. Ví dụ `solid Pyramid O-ABC` (Table 7); phần thưởng định dạng + precision có
  trọng số; SGDP-1K (Table 4–5); kết quả hạ nguồn (Table 6), tác giả viết "moderate yet positive gains" cho hình không
  gian. Vị từ đường vuông góc mặt phẳng: không thấy trong phần đọc (NR).
- **W09 SolidGeo.** Nguồn: tóm tắt arXiv (v2), preprint. 3.113 bài; khoảng cách lớn so với người.
- **W10 MagicGeo.** Nguồn: HTML toàn văn v1, preprint. "a set of points and associated constraints"; phản hồi tối đa 5 vòng;
  TikZ; "While our experiments focus on plane geometry"; 94,7%→98,7%; "processing times can exceed one hour" cho hình rất
  phức tạp. Không có tỉ lệ thành công tổng; đánh giá bằng CLIP và khảo sát người.
- **W11 GeoBuildBench.** Nguồn: HTML toàn văn v1 (~95%), preprint, nộp 2026-05-13. "the DSL is a construction language rather
  than a declarative constraint language"; "outputs are named objects that can be referenced by later commands"; "fixed
  numerical tolerances"; Table 1 tỉ lệ thành công; "the most frequent hallucination type is undefined reference". Chi phí
  token: NR.
- **W12 GGBench.** Nguồn: HTML v2, đọc ~100k/145k ký tự, preprint. 1.411 bài; mã GeoGebra là "machine-verifiable ground
  truth"; GPT-4o làm giám khảo; r=0,9295; "reasoning-grounded models that produce and execute code achieve substantially
  higher geometric correctness".
- **W13 Beyond Lines and Circles.** Nguồn: tóm tắt arXiv. "biases in target variable selection", "struggle with 2D spatial
  relationships", bịa đối tượng và vị trí. Tên Euclidea không có trên tóm tắt ⇒ [NV].
- **W14 Macke et al.** Nguồn: tóm tắt arXiv. Euclidea, chỉ ảnh, 68 loại bài, 31/68 trên loại chưa thấy. Venue: NR.
- **W15 PAL.** Nguồn: tóm tắt arXiv + trang PMLR v202 (ICML 2023, tr. 10764–10799).
- **W16 PoT.** Nguồn: tóm tắt arXiv; trang ghi TMLR 2023. "To disentangle computation from reasoning".
- **W17 ToRA.** Nguồn: tóm tắt arXiv; comments ghi ICLR 2024.
- **W18 Gorilla.** Nguồn: tóm tắt arXiv; trang không ghi venue ⇒ trình bày như preprint. Cách chấm AST: NR trên tóm tắt.
- **W19 Text2CAD.** Nguồn: tóm tắt arXiv; comments ghi NeurIPS 2024 Spotlight.
- **W20 CAD-Recode.** Nguồn: tóm tắt arXiv (v2), preprint. "translates a point cloud into Python code that, when executed,
  reconstructs the CAD model". Tên CadQuery không có trên tóm tắt.
- **W21 Text-to-CadQuery.** Nguồn: tóm tắt arXiv, preprint. 58,8%→69,3% exact match. Lưu ý [I]: so sánh đồng thời đổi IR và
  đổi mô hình, nên không quy được toàn bộ mức tăng cho IR.
- **W22 SpanBasedSP.** Nguồn: tóm tắt arXiv; comments "ACL 2021 camera ready". 61,0→88,9 trên các tách tổ hợp.
- **W23 DreamCoder.** Nguồn: tóm tắt arXiv; trang không ghi venue. Học ngôn ngữ miền bằng wake-sleep.
- **W24 Synchromesh.** Nguồn: tóm tắt arXiv; trang không ghi venue. Constrained Semantic Decoding "without retraining or
  fine-tuning" (diễn đạt của công cụ đọc; đối chiếu lại câu gốc).
- **W25 LangExtract.** Nguồn: trang PyPI chính thức (v1.7.1, Apache-2.0); trang ghi "not an officially supported Google
  product". Phần mềm, không phải công trình phản biện; không có số đo.
- **W26 Let Me Speak Freely?** Nguồn: tóm tắt arXiv (v3), preprint. "stricter format constraints generally lead to greater
  performance degradation in reasoning tasks".

---

## 4. Phân tích khoảng trống

### (a) Dựng hình hợp thành từ một thư viện hàm hữu hạn

**CONFIRMED BY SOURCE**

- Ý "thư viện phép dựng + hàm dẫn xuất theo chương sách giáo khoa, chương trình = hợp thành lời gọi hàm" có từ W01 (2011),
  kèm số đo: với thư viện mở rộng (không heuristic) giải 19/25 bài, với thư viện cơ bản không giải được bài nào trong 10
  phút. Ý này **không mới**.
- W11 (2026) đã đặt bài toán văn bản → chương trình DSL kiến thiết (18 lệnh, đầu ra có tên, "define before use") và đo trên
  489 bài; nhưng chỉ 2D, kiểm bằng dung sai số, và LLM viết cả chương trình.
- W08 (2026) có primitive khối không gian bậc cao (`Pyramid O-ABC`, `Cube ABCD-A1B1C1D1`) trong một ngôn ngữ mô tả hợp nhất
  phẳng + không gian — nhưng dùng để **phân tích ảnh**, không để dựng; toạ độ: NR.
- W02/W03 dùng ngôn ngữ kiến thiết làm IR cho chứng minh hình phẳng; W03 đo độ phủ ngôn ngữ (66%→88%).
- W19–W21 có IR dựng 3D (chuỗi CAD, mã Python/CadQuery) nhưng cho hình cơ khí, đo xấp xỉ (Chamfer), LLM viết mã tự do.

**INFERENCE**

- Trong 26 nguồn đã mở, không công trình nào **báo cáo** đồng thời: (i) đầu vào là đề hình học không gian bằng ngôn ngữ tự
  nhiên, (ii) thư viện hàm dựng 3D hữu hạn có kiểu mà mô hình chỉ được *chọn*, (iii) dựng và kiểm quan hệ bằng số học chính
  xác. Đây là **khoảng trống trong tập đã đọc**, không phải bằng chứng tính mới: tìm kiếm có giới hạn (mục 1) và nhiều mục
  chỉ đọc tóm tắt.
- Gần nhất theo từng trục: W01 (thư viện + hợp thành), W11 (văn bản → chương trình kiến thiết), W08 (primitive khối),
  W10 (LLM không viết toạ độ, bộ giải tính). Một khoá luận nên định vị đóng góp là **tổ hợp và điều kiện kiểm chứng** của các
  trục này cho hình không gian lớp 11–12, và phải trích W01/W11 như tiền thân trực tiếp.
- W11 tương ứng gần với tuyến LLM_ONLY cũ của AlgoSim (mô hình viết cả chương trình có giới hạn) và báo cáo lỗi thường gặp
  nhất là tham chiếu chưa định nghĩa — cùng họ lỗi mà việc chuyển sang "chọn hàm + engine giải phụ thuộc" nhắm tới.

**NOT VERIFIED**

- DSL của W11 có kiểu hay không; bộ giải W10 là số hay ký hiệu; W08 có ràng buộc đường–mặt vuông góc hay không.
- Phần mềm giáo dục hình không gian (GeoGebra 3D, phần mềm Việt Nam/Trung Quốc) có cơ chế "đề → lệnh dựng" hay không — chưa
  khảo sát.

### (b) Ánh xạ văn bản → lời gọi hàm có neo nguồn

**CONFIRMED BY SOURCE**

- W22: neo mỗi chương trình con vào một span đầu vào cải thiện tổng quát hoá tổ hợp (61,0→88,9 trên GeoQuery/SCAN/CLOSURE).
- W25: thư viện trích xuất ánh xạ "every extraction to its exact location in the source text" (phần mềm, không có số đo).
- W18: truy hồi tài liệu API lúc kiểm thử giảm ảo giác lời gọi API. W24: giải mã ràng buộc chỉ cho chương trình hợp lệ, ít
  lỗi chạy hơn.
- Họ lỗi trong hình học: W13 — mô hình bịa đối tượng và vị trí; W11 — "undefined reference" là ảo giác thường gặp nhất.
- W04: văn bản đề được phân tích theo luật sang ngôn ngữ hình thức (không phải LLM).

**INFERENCE**

- Trong các công trình hình học đã mở (W01–W14), neo tham số dựng vào span của đề là **NR** — không công trình nào trong phần
  đã đọc mô tả cơ chế này. Không suy ra "chúng không làm".
- Neo nguồn ở W22 là biến ẩn học được; ở W25 là thuộc tính đầu ra để người kiểm. Ý của AlgoSim (tham số phải trỏ về đoạn
  đề, engine tất định kiểm) là một biến thể *cưỡng chế* — hiệu quả của nó chưa có số đo trong văn liệu đã đọc.

**NOT VERIFIED**

- Toàn văn Inter-GPS/PGPS/GeoQA có thể có căn chỉnh văn bản–mệnh đề chi tiết hơn; chưa đọc.
- Cách W18 chấm lời gọi API (AST): không có trên tóm tắt.

### (c) Ảnh hưởng của biểu diễn trung gian lên token, độ chính xác, khả năng mở rộng

**CONFIRMED BY SOURCE**

- Độ chính xác: IR chương trình + bộ thực thi hơn chain-of-thought — W15 (+15% tuyệt đối GSM8K so với PaLM-540B CoT), W16
  (~12% trung bình), W17 (+13–19%). W12: mô hình sinh và chạy mã đạt đúng hình học cao hơn rõ. W21: đổi sang IR CadQuery cùng
  tinh chỉnh LLM: exact match 58,8%→69,3%.
- Chiều ngược: W26 — ép định dạng chặt hơn làm suy luận giảm nhiều hơn.
- Khả năng mở rộng: W01 — thư viện mở rộng biến bài không giải được (thư viện cơ bản, 10 phút) thành giải được; W03 — mở rộng
  ngôn ngữ tăng độ phủ 66%→88%; W10 — bài rất phức tạp có thể > 1 giờ ở bộ giải ràng buộc.
- Vòng kiểm chứng: W10 — 94,7%→98,7% độ chính xác tự hình thức hoá khi có kiểm chứng.

**INFERENCE**

- **Token: không nguồn nào trong 26 nguồn đã đọc báo cáo số token theo loại IR (NR toàn bộ).** Đây là chỗ đo được mà văn
  liệu đã đọc để trống.
- Các so sánh độ chính xác ở W03, W21 bị lẫn yếu tố (đổi IR cùng lúc với đổi mô hình/engine/dữ liệu), nên không quy được
  mức tăng riêng cho IR. Muốn kết luận cho AlgoSim phải giữ mô hình và tập bài cố định, chỉ đổi IR.
- W26 gợi ý IR "chỉ chọn hàm" có thể có cái giá về suy luận nếu ép mô hình trả ra một khuôn chặt trong cùng một bước; đây là
  rủi ro cần đo, không phải kết luận.

**NOT VERIFIED**

- Có công trình nào đo token/chi phí của IR hình học (DSL vs mã tự do vs lời gọi hàm) ngoài tập đã đọc — chưa tìm.

---

## 5. Giả thuyết nghiên cứu (là GIẢ THUYẾT, chưa được kiểm)

Mọi phép đo cần gọi mô hình thật phải có quyết định của người dùng, ngân sách và luật dừng đăng ký trước theo luật của kho.

**H1 — IR "chọn hàm" so với IR "viết cả chương trình" (độ chính xác).**
- *Tuyên bố:* Cùng mô hình, cùng tập bài, tỉ lệ bài được phục vụ đúng (positive served) của tuyến LLM chọn lời gọi hàm theo
  từng mệnh đề + engine giải phụ thuộc cao hơn tuyến LLM viết cả chương trình (LLM_ONLY), và lỗi tham chiếu chưa định nghĩa
  (họ lỗi hàng đầu ở W11) giảm về gần 0.
- *Bác bỏ khi:* trên tập bài đăng ký trước, tỉ lệ phục vụ đúng của tuyến chọn hàm không cao hơn (hoặc thấp hơn) tuyến cũ, hoặc
  lỗi tham chiếu chỉ chuyển thành một họ lỗi khác với tần suất tương đương.
- *Đo tối thiểu:* 16 bài của pilot cũ, cùng `gemini-2.5-flash`, k ≥ 3 mỗi tuyến; đếm số bài phục vụ đúng và phân loại lỗi
  (tham chiếu chưa định nghĩa, tiền điều kiện hỏng, neo nguồn hỏng, quan hệ không thoả).

**H2 — Neo nguồn bắt buộc (grounding).**
- *Tuyên bố:* Bắt mỗi tham số mang span của đề và để engine tất định kiểm span đó làm giảm tham số bịa (giá trị không có trong
  đề, không được dẫn xuất) mà không làm giảm độ phủ quá một ngưỡng đăng ký trước.
- *Bác bỏ khi:* tỉ lệ tham số bịa không giảm, hoặc độ phủ giảm vượt ngưỡng (ví dụ nhiều bài đúng bị từ chối chỉ vì span sai).
- *Đo tối thiểu:* ablation trên cùng tập: có/không trường span; tỉ lệ tham số có span không chứa giá trị (kiểm tất định, 0 lượt
  gọi thêm), tỉ lệ bài phục vụ đúng.

**H3 — Token theo loại IR.**
- *Tuyên bố:* Số token đầu ra mỗi bài của IR chọn hàm thấp hơn IR viết cả chương trình ở độ chính xác bằng hoặc cao hơn — điểm
  mà mọi nguồn đã đọc để `NR`.
- *Bác bỏ khi:* token đầu ra không thấp hơn, hoặc thấp hơn nhưng kèm độ chính xác thấp hơn.
- *Đo tối thiểu:* ghi `usage` token (đầu vào/đầu ra) do API trả về cho từng lượt của H1 — không thêm lượt gọi; báo trung vị và
  khoảng theo bài, tách token prompt cố định (thẻ hàm, văn phạm) khỏi token đầu ra.

---

## 6. Danh mục tham khảo

| Mã | Tham khảo | Mức xác minh |
|---|---|---|
| W01 | Gulwani, S., Korthikanti, V. A., Tiwari, A. (2011). Synthesizing geometry constructions. *Proc. 32nd ACM SIGPLAN PLDI*, 50–61. DOI 10.1145/1993498.1993505. PDF: https://www.microsoft.com/en-us/research/publication/synthesizing-geometry-constructions/ | VERIFIED_PRIMARY |
| W02 | Trinh, T. H., Wu, Y., Le, Q. V., He, H., Luong, T. (2024). Solving olympiad geometry without human demonstrations. *Nature* 625, 476–482. DOI 10.1038/s41586-023-06747-5. https://pmc.ncbi.nlm.nih.gov/articles/PMC10794143/ | VERIFIED_PRIMARY |
| W03 | Chervonyi, Y., Trinh, T. H., Olšák, M., et al. (2025). Gold-medalist Performance in Solving Olympiad Geometry with AlphaGeometry2. Preprint, arXiv:2502.03544. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W04 | Lu, P., Gong, R., Jiang, S., Qiu, L., Huang, S., Liang, X., Zhu, S.-C. (2021). Inter-GPS: Interpretable Geometry Problem Solving with Formal Language and Symbolic Reasoning. ACL 2021 (theo trang arXiv). arXiv:2105.04165 | VERIFIED_ABSTRACT_ONLY |
| W05 | Chen, J., Tang, J., Qin, J., Liang, X., Liu, L., Xing, E. P., Lin, L. (2021). GeoQA: A Geometric Question Answering Benchmark Towards Multimodal Numerical Reasoning. Findings of ACL 2021 (theo trang arXiv). arXiv:2105.14517 | VERIFIED_ABSTRACT_ONLY |
| W06 | Zhang, M.-L., Yin, F., Liu, C.-L. (2023). A Multi-Modal Neural Geometric Solver with Textual Clauses Parsed from Diagram. IJCAI 2023 (theo trang arXiv). arXiv:2302.11097 | VERIFIED_ABSTRACT_ONLY |
| W07 | Zhang, X., Zhu, N., He, Y., et al. (2023). FormalGeo: An Extensible Formalized Framework for Olympiad Geometric Problem Solving. Preprint, arXiv:2310.18021 | VERIFIED_ABSTRACT_ONLY |
| W08 | Wang, P., Zhang, M.-L., Cao, J., et al. (2026). Geoparsing: Diagram Parsing for Plane and Solid Geometry with a Unified Formal Language. ACL 2026 (theo comments arXiv). arXiv:2604.11600. DOI: NR | VERIFIED_PRIMARY |
| W09 | Wang, P., Yang, C., Li, Z.-Z., et al. (2025). SOLIDGEO: Measuring Multimodal Spatial Math Reasoning in Solid Geometry. Preprint, arXiv:2505.21177. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W10 | Wang, J., Zhang, T., Yu, H., Wang, J., Huang, H. (2025). MagicGeo: Training-Free Text-Guided Geometric Diagram Generation. Preprint, arXiv:2502.13855. DOI: NR | VERIFIED_PRIMARY |
| W11 | Kim, J., Yang, R., Zhang, H. (2026). GeoBuildBench: A Benchmark for Interactive and Executable Geometry Construction from Natural Language. Preprint, arXiv:2605.13167. DOI: NR | VERIFIED_PRIMARY |
| W12 | Wei, J., Jia, C., Bai, X., et al. (2025). GGBench: A Geometric Generative Reasoning Benchmark for Unified Multimodal Models. Preprint, arXiv:2511.11134. DOI: NR | VERIFIED_PRIMARY (đọc một phần) |
| W13 | Mouselinos, S., Michalewski, H., Malinowski, M. (2024). Beyond Lines and Circles: Unveiling the Geometric Reasoning Gap in Large Language Models. EMNLP Findings 2024 (theo trang arXiv). arXiv:2402.03877. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W14 | Macke, J., Sedlar, J., Olsak, M., Urban, J., Sivic, J. (2021). Learning to solve geometric construction problems from images. arXiv:2106.14195 (venue: NR). DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W15 | Gao, L., Madaan, A., Zhou, S., et al. (2023). PAL: Program-aided Language Models. *Proc. ICML 2023*, PMLR 202, 10764–10799. arXiv:2211.10435. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W16 | Chen, W., Ma, X., Wang, X., Cohen, W. W. (2023). Program of Thoughts Prompting: Disentangling Computation from Reasoning for Numerical Reasoning Tasks. TMLR 2023 (theo trang arXiv). arXiv:2211.12588. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W17 | Gou, Z., Shao, Z., Gong, Y., et al. (2024). ToRA: A Tool-Integrated Reasoning Agent for Mathematical Problem Solving. ICLR 2024 (theo trang arXiv). arXiv:2309.17452. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W18 | Patil, S. G., Zhang, T., Wang, X., Gonzalez, J. E. (2023). Gorilla: Large Language Model Connected with Massive APIs. Preprint (trang arXiv không ghi venue), arXiv:2305.15334. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W19 | Khan, M. S., Sinha, S., Sheikh, T. U., Stricker, D., Ali, S. A., Afzal, M. Z. (2024). Text2CAD: Generating Sequential CAD Models from Beginner-to-Expert Level Text Prompts. NeurIPS 2024 Spotlight (theo trang arXiv). arXiv:2409.17106. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W20 | Rukhovich, D., Dupont, E., Mallis, D., Cherenkova, K., Kacem, A., Aouada, D. (2024). CAD-Recode: Reverse Engineering CAD Code from Point Clouds. Preprint, arXiv:2412.14042. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W21 | Xie, H., Ju, F. (2025). Text-to-CadQuery: A New Paradigm for CAD Generation with Scalable Large Model Capabilities. Preprint, arXiv:2505.06507. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W22 | Herzig, J., Berant, J. (2021). Span-based Semantic Parsing for Compositional Generalization. ACL 2021 (theo trang arXiv). arXiv:2009.06040. DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W23 | Ellis, K., Wong, C., Nye, M., et al. (2020). DreamCoder: Growing generalizable, interpretable knowledge with wake-sleep Bayesian program learning. arXiv:2006.08381 (trang không ghi venue). DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W24 | Poesia, G., Polozov, O., Le, V., Tiwari, A., Soares, G., Meek, C., Gulwani, S. (2022). Synchromesh: Reliable code generation from pre-trained language models. arXiv:2201.11227 (trang không ghi venue). DOI: NR | VERIFIED_ABSTRACT_ONLY |
| W25 | Goel, A. (maintainer), google/langextract (v1.7.1). LangExtract — Python library. Apache-2.0. https://pypi.org/project/langextract/ (repo https://github.com/google/langextract chưa mở được). Phần mềm, không phải bài phản biện. DOI: NR | VERIFIED_PRIMARY (trang PyPI) |
| W26 | Tam, Z. R., Wu, C.-K., Tsai, Y.-L., Lin, C.-Y., Lee, H.-y., Chen, Y.-N. (2024). Let Me Speak Freely? A Study on the Impact of Format Restrictions on Performance of Large Language Models. Preprint, arXiv:2408.02442. DOI: NR | VERIFIED_ABSTRACT_ONLY |

Ghi chú DOI: với các bài arXiv, trang arXiv cấp DOI dạng 10.48550/arXiv.NNNN.NNNNN; chỉ ghi ở mục 2a cho những bài mà công cụ đọc
trả lại DOI đó (W04–W07). Không DOI nào ở đây được suy đoán.

Đã loại (không dùng làm bằng chứng): UniGeo (arXiv:2212.02746, VERIFIED_ABSTRACT_ONLY, loại vì trùng vai trò), DiagrammerGPT
(arXiv:2310.12128, VERIFIED_ABSTRACT_ONLY), Don't Mesh with Me (arXiv:2411.15279, VERIFIED_ABSTRACT_ONLY), SD-GPS
(arXiv:2606.27926, VERIFIED_ABSTRACT_ONLY), GeoAux-Bench (arXiv:2603.18662, VERIFIED_ABSTRACT_ONLY), ALCE (arXiv:2305.14627,
VERIFIED_ABSTRACT_ONLY), GeoGramBench (arXiv:2505.17653, NOT_VERIFIED), PAGER (arXiv:2605.15963, NOT_VERIFIED).
