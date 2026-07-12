# BỘ QUY TẮC HỆ THỐNG (RULES) — Bản nháp v0.3

Hệ mô phỏng thuật toán tương tác kết hợp LLM phân tích bài toán có lời văn,
hỗ trợ dạy học môn Tin học THPT (Chương trình GDPT 2018).

Hệ có **ba nguồn trace** đổ về **một trình phát** duy nhất (tiến/lùi, highlight,
hỏi–đáp dùng chung):

| Nguồn | Bài nào | Độ đúng | Quy tắc |
|---|---|---|---|
| **Catalog** — engine cài sẵn 8 thuật toán | trọng tâm SGK Tin học | 100% cam kết, có what-if kéo thả | Lớp 1–3 |
| **Tầng code** — LLM viết Python, hệ thống chạy thật trong sandbox | mọi bài tính toán ngoài catalog, "đề nào cũng vào được" | trace đúng 100% so với code; code hiện ra kiểm chứng được | Lớp 5 |
| **Vẽ tự do** — LLM sinh kịch bản vẽ | bài phi tính toán, minh họa (VD dựng hình) | không cam kết, nhãn "AI sinh" | Lớp 6 |

> **Nguyên tắc tối cao (R0):** không bao giờ để LLM *tưởng tượng* diễn biến
> từng bước rồi trình chiếu như sự thật. Bước mô phỏng chỉ được sinh từ
> (a) engine tất định của catalog, hoặc (b) **thực thi thật** chương trình
> trong sandbox — LLM chỉ viết code, không tự kể code chạy thế nào. Ngoại lệ
> duy nhất là nguồn vẽ tự do (Lớp 6), bắt buộc dán nhãn xuất xứ và không được
> hưởng cam kết độ đúng. Kênh hỏi–đáp không bao giờ in đáp án cuối của bài.
>
> *Cơ sở khảo sát:* ALGOGEN (arXiv 2605.12159) đo được: LLM sinh mô phỏng
> end-to-end chỉ đạt 82.5% độ chính xác, kiến trúc tách trace + renderer tất
> định đạt 99.8%. Scoping review của Strohmaier et al. (2025) xác nhận LLM
> "không thực sự hiểu" bài toán lời văn — vì vậy phạm vi hiểu phải bị khoanh
> trong danh mục đóng.

---

## LỚP 1 — DANH MỤC THUẬT TOÁN (CATALOG ĐÓNG)

### R1.1 Danh mục

Danh mục áp dụng cho **chế độ chuẩn**. Engine cài đặt đúng 8 thuật toán sau;
LLM chỉ được chọn `algorithm_id` trong bảng này, không được tự đặt id mới —
bài không khớp id nào sẽ được đề nghị chuyển sang chế độ mở (Lớp 5).

| `algorithm_id` | Tên trong dạy học | Dữ liệu bắt buộc | Tham số | Vị trí CT 2018 |
|---|---|---|---|---|
| `find_max` | Tìm giá trị lớn nhất | `array` | — | Tin 10 (duyệt danh sách) |
| `find_min` | Tìm giá trị nhỏ nhất | `array` | — | Tin 10 |
| `sum_if` | Tính tổng theo điều kiện | `array` | `condition` | Tin 10 |
| `count_if` | Đếm theo điều kiện | `array` | `condition` | Tin 10 |
| `linear_search` | Tìm kiếm tuần tự | `array` | `target` | Tin 10 / Tin 11 KHMT |
| `binary_search` | Tìm kiếm nhị phân | `array` **đã sắp thứ tự** | `target` | Tin 11 KHMT |
| `bubble_sort` | Sắp xếp nổi bọt | `array` | `order` (asc/desc) | Tin 11 KHMT |
| `insertion_sort` | Sắp xếp chèn | `array` | `order` | Tin 11 KHMT |

### R1.2 Cài đặt theo SGK

Mỗi thuật toán cài đúng phiên bản SGK mô tả (chiều duyệt, điều kiện dừng,
cách chèn). Trước khi code từng con, đối chiếu lại bài tương ứng trong SGK
(KNTT/Cánh diều) và ghi số bài + trang vào comment đầu file cài đặt.
Mô phỏng lệch sách một bước là giáo viên bắt lỗi — đây là rule cứng.

### R1.3 Điều kiện tiền đề của thuật toán

- `binary_search` yêu cầu dãy đã sắp thứ tự. Nếu dữ liệu trích từ đề chưa sắp:
  engine **tự sắp trước khi mô phỏng** và hiển thị chú thích sư phạm
  *"Dãy đã được sắp xếp trước — tìm kiếm nhị phân chỉ chạy trên dãy có thứ tự"*.
  (Giai đoạn 2 có thể nâng cấp: mời học sinh chạy mô phỏng sắp xếp trước.)
- `condition` chỉ nhận các phép so sánh: `>`, `>=`, `<`, `<=`, `==`, `!=`.

---

## LỚP 2 — HỢP ĐỒNG JSON GIỮA LLM VÀ HỆ THỐNG

### R2.1 Schema kết quả phân tích đề

LLM bắt buộc trả về đúng cấu trúc sau (ép bằng `responseSchema` của Gemini):

```jsonc
{
  "status": "ok",                    // "ok" | "unsupported"
  "reason": null,                    // bắt buộc khác null khi unsupported
  "problem": {
    "summary": "Tìm học sinh có điểm cao nhất trong lớp",   // tóm tắt 1 câu
    "input":   "Danh sách điểm số của 40 học sinh",          // bước "xác định bài toán"
    "output":  "Học sinh có điểm cao nhất và giá trị điểm đó"
  },
  "algorithm_id": "find_max",
  "data": {
    "array":  [7.5, 9.0, 6.5, 8.0, 5.5],
    "labels": ["An", "Bình", "Chi", "Dũng", "Em"],  // tùy chọn, độ dài phải khớp array
    "target": null,                   // bắt buộc với linear_search / binary_search
    "condition": null,                // bắt buộc với sum_if / count_if: {"op": ">=", "value": 8}
    "order": null                     // bắt buộc với bubble_sort / insertion_sort: "asc" | "desc"
  },
  "data_generated": false,            // true nếu đề không cho số liệu, hệ tự sinh mẫu
  "notes": null                       // ghi chú cho người dùng, tiếng Việt
}
```

Ví dụ từ chối:

```json
{
  "status": "unsupported",
  "reason": "Bài toán tính diện tích hình thang không thuộc dạng duyệt dãy / tìm kiếm / sắp xếp mà hệ thống mô phỏng được."
}
```

### R2.2 Quy tắc trích xuất dữ liệu (nằm trong system prompt)

- **R2.2a** — Không bịa số liệu: đề cho số nào dùng đúng số đó, đúng thứ tự xuất hiện.
- **R2.2b** — Đề không cho số liệu cụ thể (VD "lớp có 40 học sinh với điểm khác
  nhau"): sinh dữ liệu mẫu **10 phần tử** hợp ngữ cảnh (điểm ∈ [0,10], tuổi ∈
  [15,18]...), đặt `data_generated: true` và giải thích trong `notes`.
- **R2.2c** — Giới hạn mô phỏng: `array` từ 2 đến **15** phần tử. Đề cho nhiều
  hơn: lấy 12 phần tử ĐẦU + ghi `notes` "rút gọn để mô phỏng quan sát được".
- **R2.2d** — `labels` (tên người/vật gắn với từng giá trị) chỉ đặt khi đề có;
  độ dài phải khớp `array`, không tự bịa tên.
- **R2.2e** — Đề nằm ngoài danh mục → `unsupported` + `reason` nêu rõ vì sao,
  bằng tiếng Việt thân thiện với giáo viên. Cấm đoán mò sang thuật toán "gần
  giống". `unsupported` không phải ngõ cụt — LLM trả thêm trường
  `fallback: "code" | "draw" | "none"`: bài tính toán được → định tuyến sang
  tầng code (Lớp 5); bài minh họa được → vẽ tự do (Lớp 6); còn lại từ chối hẳn.
- **R2.2f** — Đề mơ hồ giữa hai thuật toán (VD "sắp xếp rồi tìm..."): chọn thuật
  toán ứng với **câu hỏi cuối cùng** của đề, nêu lựa chọn trong `notes`.
- **R2.2g** — Mọi trường văn bản viết tiếng Việt, giọng phù hợp học sinh THPT.

### R2.3 Quy tắc kiểm tra & chuẩn hóa (lớp validation, chạy trong code)

Thứ tự kiểm: schema → ngữ nghĩa → tiền đề thuật toán.

- **R2.3a** — Đúng JSON Schema (tự động nhờ responseSchema, nhưng vẫn kiểm lại).
- **R2.3b** — Ngữ nghĩa: `array` 2–15 phần tử, toàn số; `labels` khớp độ dài;
  `target` bắt buộc với 2 thuật toán tìm kiếm; `condition` bắt buộc và
  đúng dạng với `sum_if`/`count_if`; `order` bắt buộc với 2 thuật toán sắp xếp.
- **R2.3c** — Tiền đề: `binary_search` + dãy chưa sắp → tự sắp + chú thích (R1.3).
- **R2.3d** — Sai ở bước nào: gửi lại LLM đúng thông báo lỗi đó, tối đa **2 lần
  retry**; vẫn sai → báo người dùng "không phân tích được, thử diễn đạt lại đề".
- **R2.3e** — Kết quả phân tích hợp lệ được lưu vào **ngân hàng bài** (cache);
  bài trùng đề không gọi lại API.

---

## LỚP 3 — ĐỊNH DẠNG TRACE (NGÔN NGỮ CHUNG ENGINE ⇄ RENDERER)

> *Cơ sở khảo sát:* mô phỏng theo ALGOGEN — trace là biểu diễn trung gian độc
> lập renderer; một trace nuôi cả 2D lẫn 3D, nhờ đó nút chuyển 2D⇄3D giữ nguyên
> bước đang xem.

### R3.0 Trace có ba nguồn, một định dạng

Mọi trace mang trường `source: "engine" | "code_exec" | "llm_script"`. Trình
phát, highlight và hỏi–đáp đối xử ba nguồn như nhau; chỉ mức what-if (R3.3,
R5.7) và nhãn UI (R5.6, R6.4) phân biệt. Đây là điểm nối cho phép "đề nào
cũng vào được" mà không đổi khung tương tác.

### R3.1 Cấu trúc một bước

Ở chế độ chuẩn, engine sinh ra **danh sách bước tính sẵn toàn bộ** ngay khi
nạp bài (tiến/lùi/tua = di chuyển con trỏ, không tính lại):

```ts
type Step = {
  index: number;
  snapshot: {                        // trạng thái SAU bước này — lưu đầy đủ, không lưu delta
    array: number[];
    vars: Record<string, number | boolean | null>;  // i, j, max, count, left, right, mid...
    marks: Record<number, "considering" | "sorted" | "found" | "eliminated">;
  };
  events: TraceEvent[];              // những gì XẢY RA trong bước → renderer highlight/animate
  narration: string;                 // lời thuyết minh — sinh từ TEMPLATE tất định, KHÔNG gọi LLM
};
```

- **R3.1a** — Snapshot đầy đủ mỗi bước (dãy ≤ 15 phần tử nên bộ nhớ không đáng
  kể); đổi lấy tiến/lùi O(1) và what-if fork đơn giản.
- **R3.1b** — `narration` sinh từ template có tham số (VD template `compare`:
  `"So sánh {a[i]} với {max}: {kết quả}"`). Tất định 100%, dịch được, kiểm được.

### R3.2 Bảng sự kiện chuẩn

| Sự kiện | Trường | Dùng bởi | Renderer thể hiện |
|---|---|---|---|
| `compare` | `i, j, result` | mọi thuật toán so sánh 2 phần tử | highlight 2 cột, hiện dấu >/< |
| `compare_value` | `i, value, result` | tìm kiếm, điều kiện | highlight cột i + hộp giá trị |
| `swap` | `i, j` | bubble_sort | hoạt cảnh đổi chỗ 2 cột |
| `shift` | `from, to` | insertion_sort | hoạt cảnh dời phần tử |
| `insert` | `index, value` | insertion_sort | hoạt cảnh chèn |
| `assign_var` | `name, value` | max/min/count/sum, con trỏ | cập nhật hộp biến, nháy sáng |
| `set_range` | `left, right` | binary_search | khoanh vùng đang xét, làm mờ ngoài vùng |
| `mark` | `index, status` | sắp xếp (đã xong), tìm kiếm (thấy) | đổi màu cố định |
| `done` | `result` | mọi thuật toán | khung kết quả + tổng kết số phép so sánh |

**Nhóm sự kiện thực thi code** (cho tầng code — Lớp 5):

| Sự kiện | Trường | Renderer thể hiện |
|---|---|---|
| `exec_line` | `line_no` | highlight dòng code đang chạy |
| `var_change` | `name, old, new` | hộp biến nháy sáng, giá trị mới |
| `list_change` | `name, index, old, new` | cột tương ứng đổi giá trị |
| `output` | `text` | vùng "màn hình" in kết quả |
| `loop_iter` | `var, value` | đếm vòng lặp hiện hành |

**Nhóm sự kiện vẽ hình tổng quát** (chủ yếu cho nguồn vẽ tự do — Toán hình và
minh họa; renderer 2D bắt buộc hỗ trợ, 3D tùy chọn):

| Sự kiện | Trường | Ví dụ (bài trung điểm tam giác) |
|---|---|---|
| `draw_point` | `id, x, y, label` | vẽ đỉnh A, B, C |
| `draw_segment` | `id, from, to, style` | vẽ lần lượt từng cạnh AB, BC, CA |
| `draw_polygon` | `id, points, style` | tô tam giác ABC |
| `show_formula` | `latex, anchor` | hiện M = ((xB+xC)/2, (yB+yC)/2) |
| `label` | `target_id, text` | ghi "M là trung điểm BC" |
| `highlight_obj` | `target_id, on` | nhấn mạnh cạnh đang xét |

Renderer (2D lẫn 3D) chỉ được vẽ dựa trên `events` + `snapshot`; cấm renderer
tự suy diễn logic thuật toán.

### R3.3 Quy tắc what-if (kéo thả)

- **R3.3a** — Chỉ có ở trace `source: "engine"` (chế độ chuẩn) — vì cần engine
  chạy lại từ trạng thái đã sửa. Học sinh chỉ thao tác được khi mô phỏng
  **đang dừng** tại bước k.
- **R3.3b** — Thao tác cho phép: đổi chỗ 2 phần tử (kéo thả), sửa giá trị 1 ô.
- **R3.3c** — Hệ **fork**: giữ nguyên trace gốc, tạo nhánh mới = engine chạy lại
  thuật toán từ snapshot đã sửa tại bước k. UI ghi rõ đang ở "nhánh thử nghiệm",
  có nút "quay về dòng chính".
- **R3.3d** — Nhánh thử nghiệm cũng là trace tất định đầy đủ — lùi/tua được như thường.

### R3.4 Nhịp chạy của trình phát

- **R3.4a — Từng bước (mặc định)**: dừng ở mỗi bước, đi tiếp bằng nút tiến/lùi.
  Hỏi–đáp mở ở mọi điểm dừng nhưng **không bao giờ** là điều kiện để đi tiếp.
- **R3.4b — Tự chạy**: chạy liên tục, thanh tốc độ, dừng bất cứ lúc nào.
- **R3.4c — Dự đoán (predict-then-verify)**: hệ chủ động dừng ở các *bước
  quyết định* (trước swap, trước chọn nửa dãy, trước cập nhật max...) và đặt
  câu hỏi dự đoán; học sinh trả lời hoặc bỏ qua rồi bấm tiến kiểm chứng.
  Bước quyết định do engine đánh dấu sẵn trong trace (`checkpoint: true`) —
  với nguồn engine là tất định; nguồn code/vẽ tự do dùng heuristic đơn giản
  (mỗi `var_change` quan trọng / mỗi đối tượng mới).

---

## LỚP 4 — QUY TẮC SƯ PHẠM CHO KÊNH HỎI–ĐÁP

> *Cơ sở khảo sát:* nguyên tắc "rule-integrated LLM tutoring" (Computers &
> Education: AI, 2026) — tutor LLM cần bị trói bằng quy tắc tường minh, nếu
> không sẽ giải hộ học sinh.

### R4.1 Ngữ cảnh gửi kèm mỗi câu hỏi

Đề bài gốc + kết quả phân tích + **snapshot bước đang dừng** (dãy, biến, marks,
narration của bước) + tối đa 6 lượt chat gần nhất. Không gửi các bước tương lai.

### R4.2 Quy tắc trả lời (system prompt của kênh hỏi–đáp)

- **R4.2a** — Gợi mở kiểu Socratic: trả lời bằng giải thích + câu hỏi ngược,
  không đưa đáp án cuối của bài toán.
- **R4.2b** — Cấm tiết lộ kết quả các bước chưa chạy tới ("bước sau sẽ đổi chỗ
  7 và 2" → thay bằng "em dự đoán xem, rồi bấm tiến để kiểm chứng").
- **R4.2c** — Chỉ nói về trạng thái đang có trên màn hình; không nhận xét
  chung chung sách vở.
- **R4.2d** — Câu hỏi ngoài phạm vi bài học → kéo về bài trong 1 câu, không sa đà.
- **R4.2e** — Trả lời ≤ 120 từ, tiếng Việt, xưng hô thầy/cô–em.
- **R4.2f** — Học sinh đang ở nhánh what-if: ưu tiên hỏi "em quan sát thấy gì
  khác so với dòng chính?" trước khi giải thích.

---

## LỚP 5 — QUY TẮC TẦNG CODE (LLM VIẾT CHƯƠNG TRÌNH → CHẠY THẬT)

> Vai trò trong đề tài: **tầng tổng quát** — trả lời yêu cầu "đề nào cũng vào
> được, đến cả code" mà vẫn giữ R0: LLM chỉ viết chương trình, diễn biến từng
> bước là **bản ghi thực thi thật**, không phải LLM kể. Đồng thời khớp trực
> tiếp SGK Tin 10 (lập trình Python): học sinh thấy đúng quy trình "xác định
> bài toán → viết chương trình → chạy thử".
>
> *Cơ sở khảo sát:* paradigm "LLM sinh tracker, thực thi sinh trace" của
> ALGOGEN (99.8% so với 82.5% khi LLM tự kể bước); tiền lệ giao diện là
> Python Tutor.

- **R5.1 — Kích hoạt**: khi phân tích trả `unsupported` với `fallback: "code"`
  và người dùng bấm đồng ý. Không tự động chuyển ngầm.
- **R5.2 — Sinh chương trình**: LLM viết Python **≤ 40 dòng**, chỉ dùng tập
  cú pháp SGK Tin 10 (biến, rẽ nhánh, for/while, list, hàm đơn giản, print);
  cấm import thư viện; kèm 1–2 dòng `assert` tự kiểm kết quả.
- **R5.3 — Thực thi trong sandbox**: Pyodide chạy ngay trên trình duyệt;
  giới hạn 2 giây CPU, tối đa 500 bước trace, không mạng, không file.
- **R5.4 — Ghi trace**: móc theo dõi từng dòng lệnh sinh sự kiện `exec_line`,
  `var_change`, `list_change`, `output`, `loop_iter` (bảng ở Lớp 3) đổ về
  schema `Step` chung; `narration` sinh từ template tất định dựa trên sự kiện.
- **R5.5 — Hiển thị song song**: khung code + khung mô phỏng cùng màn hình,
  dòng đang chạy được highlight đồng bộ với hoạt cảnh biến/dữ liệu.
- **R5.6 — Nhãn & xử lý lỗi**: nhãn *"Chương trình do AI viết — diễn biến là
  kết quả thực thi thật"*. `assert` fail hoặc lỗi runtime → gửi thông báo lỗi
  cho LLM sửa tối đa **2 lần**; vẫn hỏng → báo người dùng, không trình chiếu
  bản lỗi.
- **R5.7 — What-if mức đầu vào**: cho phép sửa dữ liệu đầu vào rồi **chạy lại
  từ đầu** (tất định, rẻ). Không hỗ trợ sửa trạng thái giữa chừng như catalog.
- **R5.8 — Ngân hàng bài**: bài tầng code lưu kèm chương trình; chỉ chia sẻ
  chung sau khi giáo viên duyệt.

---

## LỚP 6 — QUY TẮC NGUỒN VẼ TỰ DO (AI SINH KỊCH BẢN MINH HỌA)

> Vai trò trong đề tài: **demo tính mở rộng** sang bài phi tính toán (dựng
> hình minh họa, quy trình không chạy được thành code). Không phải sản phẩm
> cốt lõi; làm ở mức chạy được + vài bài minh họa.

- **R6.1 — Kích hoạt**: `unsupported` với `fallback: "draw"` + người dùng đồng ý.
- **R6.2 — Sinh kịch bản**: LLM sinh danh sách `Step` đúng schema Lớp 3 (nhóm
  sự kiện vẽ hình), tối đa **30 bước**; `narration` do LLM viết, tiếng Việt.
- **R6.3 — Validation chỉ ở mức cú pháp**: đúng schema, số bước trong giới
  hạn, tọa độ trong khung vẽ, id tham chiếu tồn tại. **Không** kiểm được
  đúng/sai nội dung — tài liệu phải nói thẳng điều này.
- **R6.4 — Nhãn xuất xứ bắt buộc**: *"Kịch bản do AI sinh — cần giáo viên
  kiểm tra"* trên mọi khung hình; trace ghi `source: "llm_script"`.
- **R6.5 — Không what-if**: kéo-thả ẩn hẳn, tooltip giải thích lý do.
- **R6.6 — Hỏi–đáp**: áp dụng nguyên Lớp 4, thêm: học sinh nghi ngờ một bước
  sai → AI không khẳng định chắc, khuyên đối chiếu với giáo viên.
- **R6.7 — Ngân hàng bài**: chỉ lưu chung sau khi giáo viên duyệt thủ công.

---

## PHỤ LỤC A — KHUNG BỘ ĐỀ TEST (thước đo cho Lớp 2)

Tổng ~40 đề lời văn tiếng Việt bám ngữ cảnh SGK, dùng để đo độ chính xác
phân tích và tinh chỉnh prompt (quy trình: chạy bộ đề → đếm lỗi → vá rule → chạy lại):

| Nhóm | Số đề | Mục đích kiểm tra |
|---|---|---|
| Mỗi thuật toán × 3 đề đủ dữ liệu | 24 | phân loại + trích số liệu đúng |
| Đề không cho số liệu cụ thể | 5 | `data_generated` hoạt động đúng |
| Đề mơ hồ / nhiễu (thừa thông tin, hỏi 2 ý) | 5 | R2.2f, độ bền của phân loại |
| Đề tính toán ngoài danh mục (trung bình cộng, chu vi, xử lý xâu) | 4 | định tuyến `fallback: "code"`, chương trình chạy đúng, assert pass |
| Đề phi tính toán (dựng hình, minh họa) | 3 | định tuyến `fallback: "draw"`, kịch bản đúng schema, nhãn AI hiển thị |
| Đề ngoài phạm vi hẳn (văn học, lịch sử...) | 3 | `fallback: "none"` — từ chối rõ ràng, không đoán mò |

Đề mẫu:

1. *"Lớp 10A có 40 học sinh với điểm kiểm tra khác nhau. Hãy tìm bạn có điểm cao nhất."* → `find_max`, `data_generated: true`
2. *"Cho dãy điểm 7.5; 9; 6.5; 8 của các bạn An, Bình, Chi, Dũng. Đếm số bạn đạt từ 8 trở lên."* → `count_if`, condition `>= 8`, labels đủ 4
3. *"Sổ điểm đã xếp tăng dần: 4; 5.5; 6; 7; 8.5; 9; 10. Kiểm tra xem có bạn nào được 8.5 không, tìm nhanh nhất có thể."* → `binary_search`, target 8.5
4. *"Tính chu vi hình chữ nhật có chiều dài 8m, rộng 5m."* → tầng code: LLM viết `dai = 8; rong = 5; chu_vi = 2 * (dai + rong); print(chu_vi)` → chạy thật trong Pyodide, học sinh xem từng dòng chạy, biến đổi giá trị
5. *"Cho tam giác ABC với A(0;0), B(6;0), C(2;4). Vẽ tam giác và xác định trung điểm mỗi cạnh."* → vẽ tự do: LLM sinh kịch bản `draw_point` A,B,C → `draw_segment` từng cạnh → `show_formula` + `draw_point` trung điểm M, N, P — học sinh tiến/lùi từng bước, hỏi–đáp tại chỗ

## PHỤ LỤC B — VIỆC RULES **KHÔNG** QUẢN (để khỏi lạm quy tắc)

- Màu sắc, bố cục, tốc độ hoạt cảnh → tài liệu thiết kế UI riêng.
- Cách viết code, cấu trúc thư mục → convention của repo.
- Nội dung câu chữ template narration từng thuật toán → viết cùng lúc cài engine.
