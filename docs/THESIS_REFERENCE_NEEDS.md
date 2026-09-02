# THESIS_REFERENCE_NEEDS — những luận điểm cần nguồn học thuật bên ngoài

> **Mục đích.** `docs/THESIS_DRAFT.md` viết từ **bằng chứng trong kho mã**. Mọi
> luận điểm nào **không** kiểm chứng được bằng kho mã đều bị đánh dấu
> `[CẦN TÀI LIỆU THAM KHẢO]` trong bản thảo và gom vào đây.
>
> **KHÔNG có citation nào được bịa ra.** File này liệt kê *chỗ trống* và *loại
> nguồn cần tìm*, không liệt kê nguồn. Không đi tra cứu web trong lượt soạn bản
> thảo — đó là công việc của bước tiếp theo (`LITERATURE_AND_CITATION_COMPLETION`).
>
> **Cách dùng.** Mỗi mục dưới đây có: vị trí trong bản thảo · phát biểu cần chống
> đỡ · loại nguồn phù hợp · từ khoá tra cứu gợi ý · mức độ bắt buộc.
>
> **Mức độ bắt buộc:**
> **A** — thiếu nguồn thì luận điểm không đứng được, hội đồng sẽ hỏi.
> **B** — nên có, làm mạnh lập luận, nhưng có thể hạ giọng thành nhận định.
> **C** — kiến thức nền phổ thông trong ngành, một nguồn giáo trình là đủ.

---

## 0. Tóm tắt

| # | chủ đề | vị trí | mức |
|:-:|---|---|:-:|
| 1 | Khó khăn nhận thức khi học hình học không gian | Mở đầu §1, Ch.1 §1.1–1.2 | **A** |
| 2 | Trực quan hoá 3D trong dạy học toán — hiệu quả và điều kiện | Mở đầu §1, Ch.1 §1.2 | **A** |
| 3 | Rào cản triển khai công cụ hình học động trên lớp | Mở đầu §1 | **B** |
| 4 | LLM hiểu và giải toán bằng ngôn ngữ tự nhiên | Ch.1 §1.3 | **A** |
| 5 | Tính không tất định và thiếu bảo đảm hình thức của LLM | Ch.2 §2.1 | **A** |
| 6 | Sinh đầu ra có cấu trúc / giải mã ràng buộc theo lược đồ | Ch.2 §2.1 | **A** |
| 7 | LLM sinh mã / sinh chương trình thay vì sinh đáp án | Ch.1 §1.4, Ch.5 §5.5 | **A** |
| 8 | Biểu diễn trung gian trong trình biên dịch | Ch.2 §2.2 | **C** |
| 9 | Hình học tính toán: vị ngữ, độ chắc chắn số học | Ch.2 §2.4–2.5 | **B** |
| 10 | Sai số dấu chấm động và hệ quả với vị ngữ hình học | Ch.2 §2.5 | **A** |
| 11 | Số học chính xác / tính toán ký hiệu | Ch.2 §2.5 | **C** |
| 12 | Thiết kế fail-closed / fail-safe | Ch.2 §2.8 | **B** |
| 13 | Tác hại của nội dung giáo dục sai được trình bày thuyết phục | Mở đầu §1, Ch.2 §2.8 | **A** |
| 14 | Neural-symbolic: mô hình thần kinh + kiểm chứng hình thức | Ch.3 §3.2, Ch.5 §5.2 | **A** |
| 15 | Hình học động và bất biến (định vị đối chiếu) | Ch.3 §3.8, Ch.5 §5.3.1 | **B** |
| 16 | Chuẩn chương trình môn Toán 11–12 (nguồn quy phạm) | Ch.1 §1.1, Ch.4 §4.10 | **A** |

## 0b. TRẠNG THÁI sau lượt tra cứu 2026-09-02

**RESOLVED** = có nguồn đã xác minh, đã chèn vào bản thảo.
**PARTIAL** = có nguồn nhưng chống đỡ hẹp hơn claim ⇒ **câu trong bản thảo đã
được hạ giọng** cho khớp.
**UNRESOLVED** = chưa có nguồn đã xác minh; lý do ghi ở mục tương ứng.

| # | trạng thái | nguồn đã chốt | ghi chú |
|:-:|---|---|---|
| 1 | **PARTIAL** | [MED24] | mẫu là sinh viên kỹ thuật ⇒ đã khai giới hạn ngay tại chỗ trích |
| 2 | **RESOLVED** | [JUA21] [MED24] | |
| 3 | **UNRESOLVED** | — | câu đã hạ giọng, bỏ mệnh đề về tần suất sử dụng |
| 4 | **RESOLVED** | [GAO23] [MIR25] | có đủ **hai vế**: năng lực và giới hạn |
| 5 | **PARTIAL** | [MIR25] | nguồn nói về độ bền trước biến thể đề, không về ngẫu nhiên lấy mẫu |
| 6 | **RESOLVED** | [TAM24] | vế "hình dạng ≠ ngữ nghĩa" giữ là lập luận thiết kế |
| 7 | **RESOLVED** | [GAO23] | dùng để **hạ** tuyên bố đóng góp |
| 8 | **UNRESOLVED** | — | placeholder còn trong bản thảo; mức C |
| 9 | **RESOLVED** | [SHE97] | |
| 10 | **RESOLVED** | [GOL91] [SHE97] | |
| 11 | **UNRESOLVED** | — | không chặn; §2.5 không cần citation riêng |
| 12 | **UNRESOLVED** | — | placeholder còn trong bản thảo; mức B |
| 13 | **PARTIAL** | [PAS22] | báo cáo kỹ thuật, không bình duyệt ⇒ câu đã hạ giọng |
| 14 | **RESOLVED** | [GIB23] [TRI24] | không tự gán nhãn taxonomy |
| 15 | **PARTIAL** | [JUA21] | có nguồn về hiệu quả DGS, chưa có nguồn riêng về *dragging* |
| 16 | **RESOLVED** *(nửa trích dẫn)* | [BGD-TT32] [BGD-TOAN] [BGD-TT13] | xem §16 |

### Tổng kết

| | số | dẫn từ |
|---|:-:|---|
| Mức **A** tổng | **9** | 1 · 2 · 4 · 5 · 6 · 7 · 10 · 13 · 14 · 16 → *(10 mục; xem dưới)* |
| Mức A RESOLVED | **7** | 2 · 4 · 6 · 7 · 10 · 14 · 16 |
| Mức A PARTIAL | **3** | 1 · 5 · 13 |
| Mức A UNRESOLVED | **0** | |
| Mức B RESOLVED | **1** | 9 |
| Mức B PARTIAL | **1** | 15 |
| Mức B UNRESOLVED | **2** | 3 · 12 |
| Mức C UNRESOLVED | **2** | 8 · 11 |

Mức A có **10** mục (1, 2, 4, 5, 6, 7, 10, 13, 14, 16): `7 + 3 + 0 = 10` ✔
Tổng toàn bộ: `10 (A) + 4 (B) + 2 (C) = 16` ✔

**Không mục A nào bị bỏ trống.** Ba mục A ở trạng thái PARTIAL đều đã xử lý bằng
cách **hạ giọng câu trong bản thảo** cho khớp mức chống đỡ thật, chứ không giữ
câu mạnh rồi để trống trích dẫn.

**Hai placeholder `[CẦN TÀI LIỆU THAM KHẢO]` còn lại trong bản thảo** là mục 8
(IR trong trình biên dịch, mức C) và mục 12 (fail-safe defaults, mức B). Cả hai
là **kiến thức nền**, không phải luận điểm nghiên cứu, và mỗi mục chỉ cần một
giáo trình chuẩn. Chúng **không chặn** việc đọc và bảo vệ khoá luận.

---

## 1. Khó khăn nhận thức khi học hình học không gian — mức **A**

**Vị trí.** Mở đầu §1 (đoạn 1); Chương 1 §1.1, §1.2.

**Phát biểu cần chống đỡ.**
> Học sinh phải suy luận về cấu hình ba chiều trong khi mọi phương tiện trình bày
> đều là hai chiều; hình biểu diễn là một phép chiếu đã làm mất thông tin, và
> bước "dựng lại chiều thứ ba trong đầu" chính là chỗ thất bại thường xảy ra.

**Loại nguồn cần.** Nghiên cứu giáo dục toán học hoặc tâm lý học nhận thức về tư
duy không gian; nghiên cứu về lỗi thường gặp của học sinh trong hình học không
gian.

**Từ khoá tra cứu.** spatial ability and geometry achievement · spatial
visualization 3D geometry students · misconceptions solid geometry · van Hiele
levels spatial geometry · mental rotation mathematics learning · khó khăn học
sinh hình học không gian.

**Ghi chú.** Nếu tìm được nguồn Việt Nam (luận án, bài báo giáo dục toán học
trong nước) về khó khăn cụ thể của học sinh THPT Việt Nam thì tốt hơn — nó nối
thẳng với phạm vi Toán 11–12 của đề tài.

---

## 2. Trực quan hoá 3D trong dạy học toán — mức **A**

**Vị trí.** Mở đầu §1 (đoạn 3); Chương 1 §1.2.

**Phát biểu cần chống đỡ.**
> Mô phỏng ba chiều tương tác giúp gỡ khó khăn tri giác: cấu hình được dựng thật,
> người học xoay và nhìn từ hướng khác, quan hệ hình học trở thành thứ quan sát
> được thay vì thứ phải tưởng tượng.

**Loại nguồn cần.** Nghiên cứu thực nghiệm về hiệu quả của trực quan hoá 3D /
thực tại ảo trong dạy hình học; tổng quan hệ thống nếu có.

**Từ khoá tra cứu.** 3D visualization mathematics education effectiveness ·
interactive geometry software learning outcomes · virtual manipulatives spatial
geometry · dynamic visualization geometry meta-analysis.

⚠️ **Cảnh báo về mức độ phát biểu.** Bản thảo hiện phát biểu điều này ở dạng
*"về nguyên tắc"* và Chương 5 §5.3.5 khai rõ `LEARNER_IMPACT_NOT_EVALUATED`. Khi
thêm nguồn, **giữ nguyên mức phát biểu ấy** — nguồn bên ngoài chống đỡ cho *động
cơ thiết kế*, không chống đỡ cho hiệu quả của **hệ thống này**, vốn chưa được đo.

---

## 3. Rào cản triển khai công cụ hình học động trên lớp — mức **B**

**Vị trí.** Mở đầu §1 (đoạn 4).

**Phát biểu cần chống đỡ.**
> Các công cụ hình học động đòi người dùng tự dựng hình bằng thao tác; muốn mô
> phỏng một bài trong đề, giáo viên phải tự dịch đề sang chuỗi thao tác. Công
> việc này lặp lại cho từng bài, và đó là lý do mô phỏng 3D vẫn là ngoại lệ chứ
> không phải thói quen.

**Loại nguồn cần.** Nghiên cứu về rào cản áp dụng công nghệ trong dạy toán; khảo
sát mức độ sử dụng phần mềm hình học động; nghiên cứu về thời gian chuẩn bị bài
của giáo viên.

**Từ khoá tra cứu.** teacher barriers adopting dynamic geometry software ·
technology integration mathematics classroom barriers · GeoGebra adoption
teachers survey · teacher preparation time educational technology.

**Nếu không tìm được nguồn.** Hạ giọng thành nhận định định tính (*"trong thực
tế…"*) hoặc bỏ mệnh đề về *tần suất sử dụng*, giữ lại mệnh đề về *bản chất công
việc* (dựng thủ công cho từng bài) — mệnh đề sau là quan sát về công cụ, không
cần dữ liệu khảo sát.

---

## 4. LLM hiểu và giải toán bằng ngôn ngữ tự nhiên — mức **A**

**Vị trí.** Chương 1 §1.3.

**Phát biểu cần chống đỡ.**
> Các mô hình ngôn ngữ hiện nay đọc được đề toán viết tự nhiên: nhận ra cấu hình
> mà đề mô tả và đại lượng mà câu hỏi đòi. Đây là năng lực **ngôn ngữ**, không
> phải năng lực **hình học**.

**Loại nguồn cần.** Nghiên cứu về LLM trên bài toán lời văn / toán học; các bộ
benchmark toán học cho LLM; nghiên cứu phân tích *ranh giới* giữa hiểu ngôn ngữ
và suy luận toán học của LLM.

**Từ khoá tra cứu.** large language models mathematical word problems · LLM
mathematical reasoning benchmark · GSM8K MATH benchmark · chain-of-thought
mathematical reasoning · limitations LLM formal reasoning · LLM geometry problem
solving.

**Ghi chú quan trọng.** Cần **cả hai chiều**: nguồn cho thấy LLM đọc đề tốt, *và*
nguồn cho thấy LLM suy luận toán học không đáng tin cậy. Chiều thứ hai chính là
biện minh cho ranh giới R0 — nó quan trọng hơn chiều thứ nhất.

---

## 5. Tính không tất định và thiếu bảo đảm hình thức của LLM — mức **A**

**Vị trí.** Chương 2 §2.1 (đoạn 1).

**Phát biểu cần chống đỡ.**
> Mô hình ngôn ngữ sinh văn bản theo phân phối xác suất; đầu ra không tất định và
> không có bảo đảm hình thức nào về tính đúng đắn.

**Loại nguồn cần.** Tài liệu nền về kiến trúc mô hình ngôn ngữ tự hồi quy và
chiến lược lấy mẫu; nghiên cứu về hiện tượng bịa (hallucination).

**Từ khoá tra cứu.** autoregressive language model sampling temperature ·
hallucination in large language models survey · LLM output variability
reproducibility · calibration and reliability of LLM outputs.

---

## 6. Sinh đầu ra có cấu trúc / giải mã ràng buộc theo lược đồ — mức **A**

**Vị trí.** Chương 2 §2.1 (đoạn 2–4).

**Phát biểu cần chống đỡ.**
> Kỹ thuật structured output ràng buộc đầu ra theo một lược đồ. **Nhưng lược đồ
> ràng buộc *hình dạng*, không ràng buộc *ngữ nghĩa*** — một chương trình khớp
> lược đồ hoàn toàn vẫn có thể dựng sai hình.

**Loại nguồn cần.** Tài liệu về constrained decoding / grammar-constrained
generation / function calling theo JSON Schema; nếu có, nghiên cứu chỉ ra giới
hạn ngữ nghĩa của ràng buộc cú pháp.

**Từ khoá tra cứu.** constrained decoding language models · grammar-constrained
generation · JSON schema structured output LLM · function calling reliability ·
syntactic validity versus semantic correctness generated code.

**Ghi chú.** Mệnh đề thứ hai (*lược đồ không ràng buộc ngữ nghĩa*) là mệnh đề
**quan trọng nhất** của mục này — nó biện minh cho việc tồn tại của grounding,
thẩm định tĩnh và checker (bảy cổng ở §3.6.1). Nếu tìm được nguồn thực nghiệm cho
riêng mệnh đề này thì nên ưu tiên.

---

## 7. LLM sinh chương trình thay vì sinh đáp án — mức **A**

**Vị trí.** Chương 1 §1.4 (cách C); Chương 5 §5.5.

**Phát biểu cần chống đỡ.**
> Một chương trình có thể kiểm chứng được, còn một đáp số hay một cảnh 3D thì
> không. Do đó nên để mô hình phát ra *chương trình*, rồi để hệ tất định thực thi
> và kiểm chứng.

**Loại nguồn cần.** Nghiên cứu về LLM sinh mã có kiểm chứng; hướng
"program-of-thought" / "program-aided" trong suy luận toán học; công cụ dùng
solver hoặc CAS làm backend cho LLM.

**Từ khoá tra cứu.** program-aided language models · program of thought prompting ·
LLM tool use symbolic solver · verified code generation LLM · LLM theorem prover
autoformalization · LLM + SMT solver.

**Ghi chú định vị.** Đây là **họ công trình gần đề tài nhất**, và Chương 5 §5.2
hiện **không** tuyên bố tính mới học thuật quốc tế. Sau khi khảo sát họ này, có
thể định vị đóng góp của khoá luận chính xác hơn — nhiều khả năng ở chỗ: *IR
chuyên biệt cho một miền giáo dục cụ thể, kèm dẫn xuất trực quan hoá từ vết thực
thi*, chứ không ở ý tưởng "để LLM sinh chương trình" nói chung.

---

## 8. Biểu diễn trung gian trong trình biên dịch — mức **C**

**Vị trí.** Chương 2 §2.2.

**Phát biểu cần chống đỡ.** Khái niệm IR; ba tính chất được mượn lại (kiểm tra
tĩnh được, có đồ thị phụ thuộc, tách bạch hai đầu).

**Loại nguồn cần.** Một giáo trình trình biên dịch tiêu chuẩn là đủ.

**Từ khoá tra cứu.** compiler intermediate representation · static single
assignment form · dataflow analysis textbook.

---

## 9. Hình học tính toán — vị ngữ và độ chắc chắn số học — mức **B**

**Vị trí.** Chương 2 §2.4, §2.5.

**Phát biểu cần chống đỡ.** Phạm vi hình học affine/metric trên đa diện lồi; các
vị ngữ (thuộc, song song, vuông góc, đồng phẳng) và phép dựng cơ bản; khái niệm
*robustness* của thuật toán hình học.

**Loại nguồn cần.** Giáo trình hình học tính toán; tài liệu về vấn đề robustness
và tính toán chính xác trong hình học.

**Từ khoá tra cứu.** computational geometry textbook · robustness geometric
predicates · exact geometric computation paradigm · adaptive precision floating
point predicates · degeneracy handling geometric algorithms.

**Ghi chú.** Mục này chống đỡ trực tiếp cho quyết định thiết kế "không dùng
`float` trong miền hình học" — nó là một quyết định **đã được biết trong ngành**,
không phải phát minh của khoá luận, và nói rõ điều đó là trung thực.

---

## 10. Sai số dấu chấm động và hệ quả với vị ngữ hình học — mức **A**

**Vị trí.** Chương 2 §2.5 (đoạn 1).

**Phát biểu cần chống đỡ.**
> `float` không biểu diễn chính xác phần lớn số hữu tỉ và sai số tích luỹ. Với
> hình học, hệ quả là **các vị ngữ trở thành không quyết định được**: "ba điểm có
> đồng phẳng không" biến thành "định thức có nhỏ hơn ε không", và ε trở thành một
> tham số tuỳ ý quyết định câu trả lời.

**Loại nguồn cần.** Tài liệu nền về số học dấu chấm động; ví dụ cụ thể về thất
bại của vị ngữ hình học do sai số.

**Từ khoá tra cứu.** IEEE 754 floating point arithmetic · what every computer
scientist should know about floating-point · geometric predicate failure floating
point · orientation predicate exact arithmetic.

**Ghi chú.** Đây là mục **quan trọng nhất** trong nhóm kỹ thuật, vì nó là biện
minh cho một trong năm đóng góp (§5.2 mục 4). Nên có ví dụ số cụ thể.

---

## 11. Số học chính xác và tính toán ký hiệu — mức **C**

**Vị trí.** Chương 2 §2.5 (đoạn 3).

**Phát biểu cần chống đỡ.** Biểu diễn số hữu tỉ chính xác; biểu diễn căn thức
dạng `a·√b`.

**Loại nguồn cần.** Giáo trình đại số máy tính, hoặc tài liệu về số học hữu tỉ
chính xác.

**Từ khoá tra cứu.** exact rational arithmetic · computer algebra system
algebraic numbers · symbolic computation radicals.

---

## 12. Thiết kế fail-closed — mức **B**

**Vị trí.** Chương 2 §2.8.

**Phát biểu cần chống đỡ.** Nguyên tắc: khi không xác định được tính hợp lệ thì
từ chối, chứ không cho qua.

**Loại nguồn cần.** Tài liệu về thiết kế hệ thống an toàn / bảo mật (fail-safe
defaults); nếu có, tài liệu về xử lý sự không chắc chắn trong hệ AI triển khai
thật.

**Từ khoá tra cứu.** fail-safe defaults security design principles · fail-closed
system design · selective prediction abstention machine learning · safe
deployment of AI systems uncertainty.

---

## 13. Tác hại của nội dung giáo dục sai được trình bày thuyết phục — mức **A**

**Vị trí.** Mở đầu §1 (đoạn 6); Chương 2 §2.8; Chương 5 §5.5.

**Phát biểu cần chống đỡ.**
> Một mô phỏng sai còn tệ hơn không có mô phỏng, **vì học sinh sẽ tin nó**. Trong
> dạy học, một hình sai được trình bày thuyết phục là tác hại chứ không phải
> thiếu sót.

**Loại nguồn cần.** Nghiên cứu về sự hình thành và độ dai dẳng của quan niệm sai;
nghiên cứu về automation bias / overreliance trên đầu ra của máy.

**Từ khoá tra cứu.** misconception persistence science education · conceptual
change resistant misconceptions · automation bias decision support · overreliance
on AI assistance · student trust in educational technology.

**Ghi chú.** Đây là **luận điểm đạo đức trung tâm** của khoá luận — nó biện minh
cho toàn bộ thiết kế fail-closed và cho cơ chế trung thực năng lực. Hiện nó đang
được phát biểu như một điều hiển nhiên. Có nguồn thì nó thành một luận điểm; không
có nguồn thì nó vẫn là một điều hiển nhiên, nhưng yếu hơn khi bị hội đồng hỏi.

---

## 14. Neural-symbolic: mô hình thần kinh kết hợp kiểm chứng hình thức — mức **A**

**Vị trí.** Chương 3 §3.2 (ranh giới R0); Chương 5 §5.2.

**Phát biểu cần chống đỡ.** Định vị kiến trúc R0 trong bối cảnh học thuật: tách
thành phần xác suất khỏi thành phần tất định, với biên kiểm chứng ở giữa.

**Loại nguồn cần.** Tổng quan về neural-symbolic AI; công trình về LLM kết hợp
solver / prover / engine tất định; nếu có, công trình về hình học tự động
(automated geometry reasoning).

**Từ khoá tra cứu.** neuro-symbolic AI survey · LLM formal verification loop ·
automated geometry theorem proving · AlphaGeometry · LLM with deterministic
execution engine · guardrails constrained AI systems.

**Ghi chú định vị — quan trọng.** Đây là mục quyết định **khoá luận tự định vị
như thế nào**. Cần trả lời được: (i) mẫu hình "LLM đề xuất, hệ tất định kiểm
chứng" đã có tên trong tài liệu chưa? (ii) nếu có, đóng góp của khoá luận là *áp
dụng vào một miền mới với một IR mới*, chứ không phải phát minh mẫu hình. Chương 5
§5.2 hiện đã tự hạn chế đúng như vậy — sau khảo sát, có thể phát biểu chính xác
hơn thay vì chỉ hạn chế.

---

## 15. Hình học động và bất biến — định vị đối chiếu — mức **B**

**Vị trí.** Chương 3 §3.8; Chương 5 §5.3.1.

**Phát biểu cần chống đỡ.** Đối chiếu với mô hình hình học động (kéo một đối
tượng, quan sát bất biến được giữ), và giải thích vì sao đề tài **chọn không**
làm điều đó: kéo liên tục phá song ánh khung ⇔ bước.

**Loại nguồn cần.** Tài liệu về hình học động, "dragging" như một hoạt động học
tập, và giá trị sư phạm của nó.

**Từ khoá tra cứu.** dynamic geometry dragging invariants · Cabri GeoGebra
dragging modalities · conjecturing through dragging.

**Ghi chú.** Mục này cần thiết vì hội đồng **sẽ hỏi** *"sao không làm như
GeoGebra?"*. Câu trả lời hiện có trong bản thảo là một lập luận kiến trúc; kèm
nguồn về giá trị của dragging sẽ làm cho việc **khai đây là đánh đổi** (chứ không
phải chê phương pháp kia) rõ ràng hơn.

---

## 16. Chuẩn chương trình môn Toán 11–12 — mức **A**

**Vị trí.** Chương 1 §1.1; Chương 4 §4.10 (bảng phủ chương trình).

**Hai trạng thái tách rời — đừng gộp:**

| | trạng thái |
|---|---|
| `COVERAGE_COUNT` | **RESOLVED** (2026-09-02) |
| `OFFICIAL_CURRICULUM_SOURCE` | **VERIFIED** (2026-09-02) |
| `PROJECT_GRANULARITY_MAPPING` | **PARTIAL** — còn một bảng ánh xạ nên dựng |
| `TEXTBOOK_CITATION` | **STILL_NEEDED** — sách giáo khoa cụ thể |

**`COVERAGE_COUNT = RESOLVED`.** Con số: **21 chủ đề — 15 trọn / 2 một phần / 4
không**, đối chiếu từng hàng với `audit_geometry_capability.py` trên hệ đóng băng,
mỗi số kèm cột dẫn xuất và một lệnh đếm (`GEOMETRY_CURRICULUM_COVERAGE.md §1`).

**`OFFICIAL_CURRICULUM_SOURCE = VERIFIED`.** Đã xác minh và đã đọc:

| | |
|---|---|
| Văn bản | **Thông tư số 32/2018/TT-BGDĐT** ngày **26/12/2018**, Bộ Giáo dục và Đào tạo, hiệu lực **15/02/2019**, ký bởi Bộ trưởng Phùng Xuân Nhạ |
| Phụ lục dùng | **Chương trình giáo dục phổ thông môn Toán** (123 trang), phần *Hình học và Đo lường · Hình học không gian*: lớp 11 tr. 97–101, lớp 12 tr. 108–109 |
| Văn bản sửa đổi | **Thông tư số 13/2022/TT-BGDĐT** ngày **03/8/2022** — sửa chương trình tổng thể và môn Lịch sử; **môn Toán KHÔNG đổi** |
| Cách xác minh | mở trang văn bản trên cổng tư liệu văn kiện (số hiệu · ngày · cơ quan · người ký); tải PDF chương trình môn Toán và **đọc trực tiếp** mục hình học không gian |

Metadata đầy đủ: `docs/THESIS_REFERENCES.md` mục `[BGD-TT32]` `[BGD-TOAN]`
`[BGD-TT13]`.

⛔ Năm liên kết tài liệu ôn thi trước đây đóng vai nguồn chương trình **đã bị hạ
xuống** *tài liệu thứ cấp tham khảo* trong file phủ chương trình.

### Ba câu hỏi độ mịn — VĂN BẢN GỐC ĐÃ TRẢ LỜI CẢ BA

Lượt trước ghi ba chỗ chưa quyết và nói *"kéo tổng theo hai chiều ngược nhau nên
không đoán được kết quả ròng"*. Nay đọc được bản gốc, cả ba đều có câu trả lời:

| chỗ | văn bản gốc nói gì | kết luận |
|---|---|---|
| `#12` / `#13` | *"Khoảng cách trong không gian"* là **MỘT** đầu mục, và văn bản nêu rõ nó gồm cả khoảng cách hai đường chéo nhau | phép tách của khung đo là **theo cài đặt**, không theo chương trình |
| `#16b` | quan hệ liên thuộc điểm–đường–mặt nằm trong đầu mục **đại cương** (cùng chỗ với `#1`) | `#16b` là hàng do khung đo tách ra vì **có checker** |
| `#18`, `#19` | lớp 12 có **bốn** đầu mục riêng (toạ độ vectơ · phương trình mặt phẳng · phương trình đường thẳng · phương trình mặt cầu); khối tròn xoay thuộc **lớp 9**; *"quỹ tích"* **không xuất hiện** trong toàn bộ chương trình | `#19` và `#20` nằm **ngoài phạm vi lớp 11–12** |

**Số đầu mục chính thức**, đếm từ bảng "Yêu cầu cần đạt":

| | số |
|---|:-:|
| Lớp 11 — hình học không gian | **11** |
| Lớp 12 — hình học không gian | **4** |
| **Tổng** | **15** |

⇒ **21 ≠ 15, và đó không phải lỗi.** 21 là **taxonomy đo lường của đề tài**; 15
là số đầu mục của văn bản. Bản thảo nay nêu **cả hai** ở §4.10 và giải thích ba
nguồn chênh lệch ở §5.3.6.

### `PROJECT_GRANULARITY_MAPPING = PARTIAL` — việc còn lại

Nên dựng một **bảng ánh xạ 21 hàng ↔ 15 đầu mục** để người đọc theo được cả hai
chiều. Đây là việc **trình bày**, không phải việc đo, và không chặn nội dung.

⛔ **Không chia lại khung 21 hàng** để cho khớp 15 đầu mục. Làm thế là đổi
**phương pháp đo**, và mọi con số đã báo trước đó sẽ không so được nữa.

### `TEXTBOOK_CITATION = STILL_NEEDED`

Sách giáo khoa Toán 11 và Toán 12 hiện hành, **nêu rõ bộ sách**. Cần khi bản thảo
nhắc tới cách trình bày cụ thể của một chủ đề trong sách; hiện bản thảo chỉ nhắc
tới **chương trình**, nên đây không phải blocker.

---

## 17. Việc KHÔNG cần tài liệu tham khảo

Ghi ra để khỏi mất công tra cứu thừa. Những mục sau **kiểm chứng được bằng kho
mã**, và nguồn của chúng là artifact trong `docs/evaluation/`:

- mọi con số ở Chương 4 (bốn lượt thực nghiệm, bộ kiểm thử, tập demo, smoke
  trình duyệt);
- từ vựng IR (8 biểu thức · 6 câu lệnh dựng · 4 phép đo · 9 checker);
- bảng phủ chương trình — **phần kết quả đo** (phần *khung chương trình* thì cần
  nguồn, xem mục 16);
- kiến trúc, thứ tự cổng, các bất biến;
- ba đính chính ở §4.8.

Với những mục này, trích dẫn đúng là **trỏ về artifact**, không phải trỏ về tài
liệu bên ngoài.

---

## 18. Quy trình bước tiếp theo

1. **Tra cứu theo thứ tự ưu tiên:** mục 16 (quy phạm, bắt buộc) → các mục **A** →
   các mục **B** → các mục **C**.
2. **Với mỗi mục:** tìm 1–3 nguồn, ghi đầy đủ thông tin trích dẫn, và **kiểm rằng
   nguồn thật sự nói điều mình cần** — không trích theo tiêu đề.
3. **Sau khi có nguồn cho mục 7 và 14:** viết lại phần định vị đóng góp ở Chương 5
   §5.2. Đây là phần duy nhất của bản thảo **cố ý để mở** chờ khảo sát tài liệu.
4. **Không hạ chuẩn phát biểu thực nghiệm.** Nguồn bên ngoài không làm cỡ mẫu
   n = 4–6 lớn hơn. Các cảnh báo ở §4.7 và §5.3.4 giữ nguyên.
5. **Nếu một mục không tìm được nguồn:** hạ giọng phát biểu trong bản thảo (từ
   khẳng định xuống nhận định), đừng giữ nguyên giọng rồi bỏ trống citation.
