# So sánh kiến trúc: AI chọn hàm (A) và compiler chọn hàm (B)

Tài liệu đánh giá của run `hybrid-compiler-selection` (2026-10-10). Nó **bổ sung** quyết định kiến trúc
[`TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md`](../../../../architecture/TEXT_TO_GEOMETRY_FUNCTIONS_DECISION.md) và
**không sửa** quyết định đó. ADR vẫn có hiệu lực: kiến trúc đích là Text-to-Geometry Functions với nhánh A. B là ứng viên
nghiên cứu ("FactGraph, compiler-in-the-loop" trong ADR), được dựng để đo, không để thay A.

**Số lời gọi Gemini thật: 0.** Mọi số dưới đây là offline. Đầu ra của "AI" ở cả hai nhánh là dữ liệu viết tay hoặc sinh cơ học,
đóng vai một mô hình trích **đúng**. Không số nào ở đây nói về năng lực của Gemini.

Nhãn kết luận: `VERIFIED` (có lệnh tái lập và log) · `HYPOTHESIS` (cần mô hình thật để kiểm) · `NOT_VERIFIED` · `FAILED` ·
`OUT_OF_SCOPE`.

## 1. Hai nhánh

```
A  đề ─► Gemini function calling (24 khai báo hàm, ANY) ─► {"calls":[…]} ─┐
                                                                          ├─► doc_ke_hoach ─► kiem_nguon (5 tầng)
B  đề ─► Gemini structured output (TypedFact, không có tools) ─► facts     │      ─► engine _Dung (khung affine + Gram)
         ─► planner.lap_ke_hoach (tất định) ─► {"calls":[…]} ──────────────┘      ─► IR ─► interpreter/kernel ─► Scene3D
                                                    sau khi dựng (chỉ B): kiểm điều phải chứng minh · kiểm phủ định ·
                                                    chẩn đoán FIGURE_NOT_UNIQUE
```

B đổ vào **đúng** đường của A từ điểm `{"calls": [...]}` trở đi. Không có back end thứ hai. Lời gọi do planner sinh ra vẫn
phải qua cổng nguồn 5 tầng như lời gọi do mô hình sinh ra. Quote của dữ kiện trở thành quote của lời gọi. `VERIFIED`
(`run_fact_route` gọi `run_function_route`; test `test_khong_lui_ve_llm_only`).

## 2. Ai quyết định cái gì

| quyết định | A | B |
|---|---|---|
| đọc mệnh đề, chép quote | mô hình | mô hình |
| vai trò mệnh đề (giả thiết / phải chứng minh / điều kiện / câu hỏi), phủ định, mơ hồ | mô hình (phải tự **không** phát lời gọi; cổng nguồn bắt một phần qua từ khoá trong quote) | mô hình **gắn nhãn**; planner hành động theo nhãn |
| chọn hàm theo kiểu quan hệ (⊥ đường–mặt, đường–đường, mặt bên–đáy) | mô hình | planner (theo số điểm của toán hạng) |
| mở rộng định nghĩa ("chóp đều" ⇒ đáy đều; "lập phương" ⇒ lăng trụ đứng + đáy vuông; "hộp chữ nhật" ⇒ đáy chữ nhật) | mô hình | planner |
| giải tham chiếu theo vai trò ("cạnh bên", "cạnh đáy", "chiều cao", "cạnh" của khối đều) | mô hình | planner (từ chối khi tham chiếu không xác định) |
| thứ tự dựng, giải phụ thuộc, toạ độ, kiểm mọi dữ kiện | engine | engine (giống hệt) |
| điều phải chứng minh đúng trên hình? | không kiểm | kiểm sau khi dựng; SAI ⇒ `PROOF_GOAL_FALSE` |
| mệnh đề phủ định sai trên hình? | không kiểm; quote có phủ định ⇒ `NEGATED_CLAUSE` | kiểm; ĐÚNG ⇒ `INCONSISTENT_FACTS`; không kiểm được ⇒ `NEGATED_CLAUSE` |
| hình không duy nhất nhưng đại lượng duy nhất | `UNDERDETERMINED_POINT` | `FIGURE_NOT_UNIQUE` + `quantity_invariant` (vẫn từ chối) |

Đếm trên trace của planner, 14 ca holdout (`diagnostics/responsibility_and_surface.log`). Đây là số quyết định B chuyển từ
mô hình sang planner. `VERIFIED` (đếm), nhưng đó chỉ là số luật đã chạy, **không** phải số lỗi tránh được:

| loại quyết định | số lần |
|---|---|
| chọn hàm theo kiểu quan hệ / câu hỏi | 22 |
| khối → phép dựng | 13 |
| mở rộng định nghĩa | 11 |
| giải tham chiếu theo vai trò | 5 |

## 3. Bề mặt mô hình nhìn thấy

| | A | B |
|---|---|---|
| cơ chế | function calling, `ANY` + `allowedFunctionNames` | `responseMimeType` JSON + `responseSchema`, không có tools |
| lược đồ | 24 khai báo hàm, 19 816 ký tự | 1 đối tượng phẳng: 11 loại dữ kiện, 21 ô, 2 999 ký tự |
| prompt hệ thống | 626 ký tự | 743 ký tự |
| `surface_fingerprint()` | `09ec4a9d…` | `83dcfa7a…` |
| `maxOutputTokens`, `temperature` | 8192, như nhau (cùng hằng) | 8192, như nhau |
| lượt gọi / đề | 1 | 1 |
| `REAL_MODEL_TOKEN_USAGE` | `NOT_MEASURED` | `NOT_MEASURED` |

Đo bằng **ký tự** (`VERIFIED`). Không quy ra token. Lược đồ B ngắn hơn khoảng 6,6 lần theo ký tự, nhưng đầu vào thật còn có đề
bài và cách provider mã hoá lược đồ. Đầu ra của B có thể **dài hơn** A (nhiều dữ kiện nhỏ, mỗi dữ kiện kèm quote và cờ, so với
một lời gọi hợp thành). Chiều nào thắng là `HYPOTHESIS` (H-AB3).

## 4. Kết quả offline tóm tắt

Chi tiết: [`AB_OFFLINE_RESULTS.md`](AB_OFFLINE_RESULTS.md).

- **Parity, 58 ca cũ** (27 + 23 + 8): dữ kiện B sinh **cơ học** từ lời gọi A. Trạng thái, mã và đáp số trùng 58/58.
  `VERIFIED`. Ý nghĩa hẹp: planner tái tạo được lời gọi A khi dữ kiện đúng. Không nói gì về tổng quát hoá.
- **Holdout, 14 ca mới** (tiền đăng ký ở `f6b1a551`, trước khi có planner): cả hai nhánh khớp kỳ vọng 14/14. Phân hạng
  giống nhau: 8 phục vụ đúng, 4 từ chối đúng, 2 ngoài năng lực, 0 phục vụ sai, 0 từ chối oan, 0 lỗi hạ tầng. `VERIFIED`.
- Cảnh A và B của mọi ca phục vụ trùng điểm và metric. Renderer kiểm 16/16 cảnh. `VERIFIED`.
- Khác nhau ở **chẩn đoán**, không ở kết cục: H05 (`FIGURE_NOT_UNIQUE` thay vì `UNDERDETERMINED_POINT`), H08
  (`UNSUPPORTED_CAPABILITY` thay vì `UNSUPPORTED_PLANE`), H13 (B chứng minh mâu thuẫn trên hình; A từ chối vì quote có
  phủ định). H07: B còn xác nhận điều phải chứng minh đúng (`HOLDS`). `VERIFIED`.

## 5. Kết luận và giới hạn

| kết luận | nhãn |
|---|---|
| B dựng được trên cùng registry/engine/IR/kernel/Scene3D, không back end thứ hai, không đổi mặc định | `VERIFIED` |
| Khi đầu ra AI đúng, A và B tương đương về kết cục trên 72 ca offline | `VERIFIED` (chỉ trong giả định AI trích đúng) |
| B kiểm được điều phải chứng minh và mệnh đề phủ định trên hình; A thì không | `VERIFIED` (cơ chế: holdout H07/H13, 4 test riêng, đột biến m1 m2 m8 m9 m10) |
| B giảm lỗi chọn hàm của mô hình thật | `HYPOTHESIS` (H-AB1) — chưa đo |
| B tăng lỗi bỏ sót dữ kiện / gắn sai vai trò của mô hình thật | `HYPOTHESIS` (H-AB1) — chưa đo |
| B kiêng trả lời tốt hơn trên đề thiếu / không duy nhất | `HYPOTHESIS` (H-AB2) — offline hai nhánh đều từ chối đúng |
| B tốn ít token đầu ra hơn | `HYPOTHESIS` (H-AB3) — `NOT_MEASURED` |
| Hybrid là kiến trúc tốt hơn | `NOT_VERIFIED` — **không** tuyên bố |
| Đổi kiến trúc đích hay mặc định | `OUT_OF_SCOPE` của run này |

Giới hạn chính:

1. Tác giả viết cả lời gọi A, dữ kiện B, kỳ vọng và oracle. Độc lập đánh giá là `PARTIAL`. Oracle toạ độ
   (`diagnostics/independent_oracle_check.py`) không import engine, nhưng cùng tác giả.
2. Dữ kiện của 58 ca parity sinh từ lời gọi A, nên parity là vòng tròn có chủ đích. Nó chỉ kiểm planner.
3. Planner là bộ luật viết tay. Loại dữ kiện ngoài 11 loại, hay quan hệ ngoài các cặp kiểu đã viết, sẽ thành
   `UNSUPPORTED_CAPABILITY`. Độ phủ của planner nhỏ hơn hoặc bằng độ phủ của registry.
4. Chẩn đoán `FIGURE_NOT_UNIQUE` chỉ có một mẫu: đỉnh chóp chưa xác định + có chiều cao + chỉ hỏi thể tích. Trường hợp không
   duy nhất khác vẫn là `UNDERDETERMINED_POINT`.
5. Điều phải chứng minh mà checker không kiểm được thì ghi `UNVERIFIABLE` và **vẫn phục vụ** đáp số (mục tiêu không phải giả
   thiết nên không đổi hình). Chưa có quyết định sản phẩm về cách hiển thị.
6. Từ khoá cổng nguồn "lập phương", "chữ nhật" được thêm cho **cả hai** nhánh. Đây là nới cổng nguồn, có khai báo:
   [`AB_OFFLINE_RESULTS.md`](AB_OFFLINE_RESULTS.md) §6.
