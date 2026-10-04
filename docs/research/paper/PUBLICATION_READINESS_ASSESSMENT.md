# PUBLICATION_READINESS_ASSESSMENT — đánh giá tiềm năng bài báo

> Ngày **2026-09-10**, HEAD `df8ad21`. `APPLICATION_LLM_CALLS = 0`.
> Căn cứ: `LITERATURE_COMPARISON_MATRIX.md` · `CLAIM_TO_EVIDENCE_MAP.md` ·
> `RESEARCH_GAP_AND_CONTRIBUTIONS.md`.
>
> Thang: `STRONG` · `MODERATE` · `WEAK` · `NOT_MEASURED`.

## 1. Tám mục

| mục | mức | căn cứ |
|---|---|---|
| `PROBLEM_SIGNIFICANCE` | **STRONG** | Miền 3D được chính tài liệu xác nhận là chỗ mô hình còn yếu: SolidGeo (3 113 bài) kết luận MLLM *"còn cách xa mức người"*; DynaSolidGeo báo sụt mạnh ở xoay/tưởng tượng không gian. Phía giáo dục có meta-analysis 29 nghiên cứu / 2 111 học sinh (Juandi 2021). Bài toán có người cần và có bằng chứng là khó. |
| `GAP_STRENGTH` | **MODERATE** | Khoảng trống **có thật nhưng hẹp hơn** bản thảo hiện viết. GeoBuildBench (2026) đã đặt đúng khuôn *đề tự nhiên → DSL → hình kiểm được*; Draw2Think (2026) đã dựng hình **có cả hình không gian** qua constraint engine. Phần còn trống là **giao** của: 3D + số học chính xác + song ánh khung⇔bước + từ chối có cấu trúc hướng người học. Phát biểu được ở dạng giao, **không** phát biểu được ở dạng "chưa ai làm". |
| `METHOD_NOVELTY` | **MODERATE** | 1 `NOVELTY_CANDIDATE` (nhân số học chính xác làm thẩm quyền đáp số) + 3 đóng góp tích hợp. Từng thành phần đều có tiền lệ; **tổ hợp** thì chưa thấy trong tập khảo sát. Đây là novelty của một **system paper**, không phải của một bài phương pháp. |
| `SYSTEM_COMPLETENESS` | **STRONG** | Chạy đầu-cuối: đề tiếng Việt → analyze → semantic program → 6 tầng thẩm định → kernel chính xác → trace → Scene3D → UI, kèm từ chối có cấu trúc. 10/10 họ trong phạm vi có nền; `FEATURE_SCOPE_COMPLETE = YES`; demo tất định 5/5 và 12/12 đáp số đọc được **trên màn hình** trong Chrome thật. |
| `EVALUATION_STRENGTH` | **WEAK** | Đây là chỗ yếu nhất và không nên tô. **Một** lượt đo, **9 ca**, **n = 1 mỗi họ**, **không held-out**, `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`, **không có baseline so sánh**. Hai RQ (tự sinh, hiệu quả) cố ý **không có ngưỡng**. Với hội nghị hạng A, riêng mục này đủ để bị từ chối. |
| `REPRODUCIBILITY` | **MODERATE** | Mạnh ở phần tất định: candidate đóng băng kiểm được bằng máy, artifact có băm SHA-256 (26 file), corpus/policy/scorer đều ghim băm, `FINAL_SYSTEM_RELEASE = PASS`, `FLAKE_RATE 0.9 → 0`. Yếu ở phần model: `MODEL_REPRODUCIBILITY = LIMITED_ACCEPTED` — gọi bằng **alias** `gemini-2.5-flash` chứ không phải snapshot bất biến. **Không** được tuyên bố tái lập bit-for-bit. |
| `LIMITATIONS_DISCLOSED` | **STRONG** | Khai giới hạn là điểm mạnh nhất của kho này. Chín tuyên bố bị cấm được liệt kê tường minh; `PRODUCT_PROMOTION_ELIGIBLE = NO` khoá **trước** lượt đo; và báo cáo tự khai **bộ đo của chính mình đã sai một lần** (`SILENT_WRONG_ANSWER` gốc 6 → sửa 0). Mức tự phê bình này cao hơn mặt bằng system paper. |
| `PUBLICATION_READINESS` | **MODERATE** | Đủ cho khoá luận và cho **workshop/demo**. **Chưa** đủ cho hội nghị chính hạng A vì `EVALUATION_STRENGTH = WEAK`. Ba việc A1–A3 ở `CLAIM_TO_EVIDENCE_MAP.md §3` là điều kiện cần. |

## 2. Loại bài phù hợp — xếp hạng

| hạng | loại bài | vì sao | điều kiện |
|:-:|---|---|---|
| **1** | **System paper / demo paper** (workshop hoặc demo track của hội nghị NLP–giáo dục, ví dụ BEA, AIED, EDM) | Điểm mạnh của công trình là **hệ chạy được, kiểm chứng được, khai giới hạn thật**. Demo track chấm đúng thứ đó và **không** đòi đánh giá quy mô lớn. | gần như đã đủ; cần bản demo chạy từ **bản dựng** (đã có `DEMO_RUNBOOK.md`) |
| **2** | **Educational technology paper** (tạp chí công nghệ giáo dục) | Khung *trung thực năng lực* + *từ chối có cấu trúc* là luận điểm sư phạm thật: hệ dạy học không được sai trong im lặng. | cần **A6 nghiên cứu người dùng**. ⚠️ Không được trộn kết quả người dùng vào bảng số kỹ thuật hiện có |
| **3** | **Thesis-only contribution** | Toàn bộ nội dung hiện tại đã đủ chặt cho khoá luận: có bảng tuyên bố ↔ bằng chứng ↔ giới hạn, có đính chính, có artifact băm. | không cần thêm gì |
| **4** | Hội nghị chính hạng A (ACL/EMNLP main) | `EVALUATION_STRENGTH = WEAK` và **không có baseline**. Reviewer sẽ hỏi ngay: *"9 ca, n = 1, không held-out, so với cái gì?"* | cần A1 + A2 + A3 + A4 |

**Khuyến nghị:** nhắm **hạng 1** trước. Nó biến công trình thành một mục có thể
trích dẫn mà không phải hứa những gì chưa đo, và phần đánh giá A1–A4 có thể làm
sau như một bài thứ hai.

## 3. Nếu muốn nhắm bài về **hiệu quả giáo dục**

Phải làm một nghiên cứu người dùng **riêng**, với thiết kế riêng (nhóm đối chứng,
tiền/hậu kiểm, cỡ mẫu tính trước). Và:

⛔ **Không trộn kết quả ấy vào bảng số kỹ thuật hiện tại.** Bảng hiện tại đo
*hệ có phục vụ đúng không*; nghiên cứu người dùng đo *người học có khá lên
không*. Gộp hai thứ vào một bảng là cách nhanh nhất để mất cả hai.

## 4. Ba câu reviewer sẽ hỏi đầu tiên — và câu trả lời trung thực

| câu hỏi | trả lời hiện có |
|---|---|
| *"Khác gì GeoBuildBench và Draw2Think?"* | GeoBuildBench là **benchmark 2D tiếng Trung**, đo chứ không phục vụ. Draw2Think dựng hình để **giải đúng hơn**, thẩm quyền số nằm ở engine có sẵn. AlgoSim phục vụ **người học**, mang nhân số học chính xác riêng, và từ chối có cấu trúc. — Câu này **phải** nằm trong bài, không được để reviewer tự tìm ra. |
| *"9 ca thì nói được gì?"* | Nói được rằng hệ **biểu đạt và phục vụ được** 10/10 họ trong phạm vi với đáp số chính xác tuyệt đối. **Không** nói được gì về độ ổn định — và bài phải viết đúng như vậy. |
| *"Số học chính xác có thật sự cần không?"* | Có bằng chứng nội bộ: trước bản vá khối lõm, hệ **phục vụ** thể tích `28` thay vì `20`. Đó là loại lỗi mà dung sai số học không bắt được. |
