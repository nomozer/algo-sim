# CHUỖI PROBE `serve` — route sinh đi từ 0 tới PHỤC VỤ ĐƯỢC

> Bằng chứng kỹ thuật (tầng 2 — **engineering evidence**, KHÔNG phải số luận
> văn). Số held-out chính thức vẫn là `results/OFFICIAL_RESULT.md` trên
> `4e13e2b`. Lượt này chạy trên candidate `d6b7b30`, `CACHE_VERSION 36`,
> `SEMANTIC_ROUTE_MODE=serve`, API thật, qua `run_pipeline` sản phẩm.

## 0. Vì sao có tài liệu này

`A = 3/40` nói *bao nhiêu* case chạy được, không nói *vì sao* các case còn lại
không. Chuỗi probe dưới đây trả lời câu thứ hai trên MỘT đề, bằng cách chạy đi
chạy lại đúng đường sản phẩm và đọc `stage_reached` sau mỗi lần sửa.

Kết quả quan trọng nhất **không phải** bản vá, mà là hình dạng của các thất bại.

## 1. Đề ghép ngoặc — tám lượt, tám lớp lỗi KHÁC NHAU

Đề: *"Kiểm tra tính hợp lệ của chuỗi đóng mở ngoặc bằng ngăn xếp Stack với chuỗi
`{[()]}`"*.

| # | `stage_reached` | Lỗi | Loại |
|---|---|---|---|
| 1 | `semantic_program` | `container: {"kind":"var","name":"stack"}` ×4 | ký pháp |
| 2 | `semantic_program` | `container: {"kind":"literal","value":"([{"}` ×2 | ký pháp |
| 3 | `semantic_program` | `pop` dùng như **biểu thức** | ký pháp |
| 4 | `semantic_program` | visual binding neo vào `str` | mô hình dữ liệu |
| 5 | `semantic_program` | biến bool dùng **thẳng** làm điều kiện | ký pháp |
| 6 | `semantic_program` | lồng 5 tầng > trần 4 | cấu trúc |
| 7 | `grounding` | hằng thuật toán không truy được về đề | chính sách |
| 8 | `semantic_program` | `peek` dùng như **câu lệnh** | ký pháp |
| — | `postconditions` | `membership(chuoi_ngoac)`: witness `None` | **taxonomy** |

**Không lượt nào là hiểu sai đề.** Ở mọi lượt, chương trình dựng đúng nghĩa vụ,
chọn đúng ngăn xếp, viết đúng vòng duyệt. Sáu trong chín lớp là *model viết dạng
tự nhiên, IR đòi dạng khác*.

Lượt 8 là chỗ quy luật lộ ra: sửa `pop` xong thì model rơi vào `peek` — **ảnh
gương của chính lỗi vừa vá**. Đuổi theo từng lớp là đuổi theo một biến ngẫu
nhiên (`RULES §3c`: DEEP_HARDENING).

## 2. Hai nguyên tắc thay cho chín bản vá

1. **Mã hoá được thì để validator giữ.** `canonical_condition` gấp `x` ⇒
   `x == true`, cùng họ `canonical_container_name`. Ranh giới giữ chặt: chỉ gấp
   dạng mang được bool; `arith`/`length` vẫn bị từ chối vì đó là lỗi KIỂU thật.
2. **Không mã hoá được thì đưa lỗi ngược cho LLM sửa.**
   `stage_semantic_program` ≤3 lượt, gửi lại đúng thông báo validator — khuôn
   `stage_simulate` đã dùng từ M3. Trần là HẰNG SỐ nên **claim D1 nguyên vẹn**:
   lượt LLM chặn bởi call graph, không đi theo độ dài trace.

`MAX_NESTING_DEPTH` 4 → 6 vì IR **không có `elif`**: mỗi bậc *"ngược lại, nếu…"*
ăn một tầng, nên bài ngăn xếp kinh điển cần 5 tầng là mức **sàn**.

## 3. Một lỗi ĐỊNH TUYẾN, không phải lỗi năng lực

Đề *"đảo dãy 5, 2, 8, 1 bằng ngăn xếp"* đạt `stage_reached=served`,
`servable=true`, 5 khung — rồi envelope trả **`unsupported`**.

Nguyên nhân: `mismatch_gap` `return` **trước** nhánh phát, nên một phán quyết
lệch của **classifier legacy** phủ quyết một kết quả ngữ nghĩa đã phục vụ được.
Cổng mismatch sinh ra để bảo vệ *đường module* — chương trình ngữ nghĩa không đi
qua target nào nên không nằm trong tầm bảo vệ ấy.

Cùng khiếm khuyết đã từng sửa cho lượt **THỬ** (`_semantic_shadow` đặt ngoài
nhánh generic có chủ đích) nhưng sống sót ở lượt **PHÁT**.

## 4. Kết quả sau khi sửa

| Đề | Trước | Sau |
|---|---|---|
| đảo dãy bằng ngăn xếp | `unsupported` | **`ok` · `generic.semantic_program` · `source=semantic_program` · 5 khung** |
| ghép ngoặc bằng ngăn xếp | `unsupported` | `unsupported` — **đúng thiết kế**, §5 |

Đo lặp: **3/4 lượt phục vụ được**, `retry=0` (chương trình hợp lệ ngay lượt
đầu). Một lượt trượt — route **chưa ổn định 100%**, và con số 3/4 không đủ mẫu
để gọi là tỉ lệ.

## 5. Ranh giới KHÔNG đụng tới — và vì sao

Đề ghép ngoặc dừng ở `postconditions` vì nghĩa vụ đúng của nó là
`predicate_verdict`, thứ `obligations.py` khai **cố ý không có**:

> kiểm nó đòi cài lại chính thuật toán đang kiểm, nên oracle mất tính độc lập.

Ví dụ nêu trong chính file đó là *"dấu ngoặc có hợp lệ không"* — đúng đề này. Nó
**chạy được** (`executable=true`, 8 bước) nhưng **không phát được**, và từ chối
ở đây là hành vi đúng: hệ không phát thứ nó không tự kiểm chứng nổi.

**Taxonomy giữ nguyên 9 nghĩa vụ, hash `4dd712a3…` qua cả năm lần đóng băng.**
Không nghĩa vụ nào được thêm để cứu case.

## 6. Điều tài liệu này KHÔNG nói

- **Không** phải số held-out. N = 2 đề, tự chọn, không niêm phong.
- **Không** đo lại `A`. Muốn biết bốn biên ký pháp + vòng sửa nâng `A` lên bao
  nhiêu thì phải **niêm phong SEALED MỚI** — cấm vá rồi chạy lại trên tập cũ.
- **Không** nói gì về người học: `LEARNER_IMPACT_NOT_EVALUATED`.
- Bằng chứng thị giác của lượt phát này **chưa có**: `capture-stack-vnext.mjs`
  chụp envelope TIÊM THẲNG, không phải envelope do route sinh phát ra.
