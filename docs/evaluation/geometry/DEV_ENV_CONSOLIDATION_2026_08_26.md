# HỢP NHẤT MÔI TRƯỜNG DEV — và cổng smoke KHÔNG mở (2026-08-26)

> Mục tiêu đặt ra: đảm bảo mọi lượt live dùng đúng **mã hiện tại · prompt hiện
> tại · `CACHE_VERSION` hiện tại · cache DB hiện tại**. Rồi ba smoke test làm
> cổng: chỉ khi cả ba xác nhận mới được chạy benchmark Phase 7.
>
> **Hợp nhất: XONG.** **Cổng: KHÔNG MỞ — 1/3.** Và lý do không mở đã ĐỔI BẢN
> CHẤT giữa chừng, đó mới là kết quả đáng giá của lượt này.

---

## 1. Môi trường — trạng thái cuối, kiểm được bằng máy

```
source : sha=b764091b3c43 cache=44 family=12 target=24 hash=128c33beb913
         skill=11/6208fc2a card=6fedb988
runtime: sha=b764091b3c43 cache=44 family=12 target=24 hash=128c33beb913
         skill=11/6208fc2a card=6fedb988
cờ     : route=serve model=gemini-2.5-flash telemetry=1 reload=0
cache đề: 0 row · cây làm việc: sạch · pytest 2809 passed
```

`runtime_doctor --doi-mode serve --doi-model gemini-2.5-flash` → **PASS**.

### Tiến trình đang chạy

Một backend duy nhất (container). Hai thứ nghe cổng 8000 ngoài nó —
`com.docker.backend.exe` và `wslrelay.exe` — đều là ống dẫn của Docker Desktop,
không phải server thứ hai. Cổng 3000 là vite dev. **Không có uvicorn nào ngoài
container.**

### Ba phiên song song

`algo-sim-f1` (phiên này) · `algo-sim-61` · `algo-sim-85`. Trong lượt này phiên
khác commit `a9052db` (tiêu đề tab), `9698be9` (vòng đệm chẩn đoán) và `e9dc9f8`
(bộ dò miền). **Không commit hộ ai.** Mỗi phiên tự commit phần của mình; cây sạch
là do cả ba cùng dọn.

---

## 2. Bốn lỗ của chính bộ kiểm — "PASS" từng nói dối hai lần

`runtime_doctor` so `git_sha` · `CACHE_VERSION` · catalog hash. **Cả ba đều KHỚP**
trong hai tình huống mà hệ đang chạy sai:

| | Tình huống | Vì sao ba phép so cũ mù |
|---|---|---|
| ① | tiến trình giữ **prompt cũ** trong `_skill_cache` | không phép nào đọc một file `.md` |
| ② | `SEMANTIC_ROUTE_MODE=off` — route sinh **không chạy** | cờ vận hành không thuộc danh tính mã |

Cả hai đều xảy ra THẬT trong lượt này, và cả hai đều được doctor báo PASS.

**Đã bịt:**

- `skill_fingerprint()` băm **thứ tiến trình ĐANG GIỮ**, không phải thứ trên đĩa
  — đọc lại đĩa rồi băm sẽ báo "khớp" trong đúng ca nó sinh ra để bắt.
- `grammar_card` vào vân tay: nó sinh từ `contract.py` và ghép vào user message,
  nên đổi một model Pydantic là đổi thứ LLM đọc mà không file `.md` nào bị sửa.
- Bốn cờ vận hành hiện ra; `--doi-mode` / `--doi-model` cho phép **khai kỳ vọng**
  khi lượt này là một lượt đo. Doctor không tự phán `off` là sai — `off` là lựa
  chọn hợp lệ cho bản chạy thật, và một cổng đỏ ở mọi lượt production sẽ bị tắt.
- Thiếu vân tay ⇒ `PROMPT_FINGERPRINT_MISSING`. Một cổng không đo được phải nói
  *"không đo được"*, không được nói *"khớp"*.

Cộng hai tầng giữ bản cũ ở phía vận hành: `DEV_RELOAD=1` (uvicorn không
`--reload` ⇒ sửa `backend/app` **không có tác dụng gì** cho tới khi restart) và
`scripts/cache_clear.py` (cache Postgres — tầng restart **không** chạm tới).

---

## 3. Năm lỗi HỢP ĐỒNG lộ ra khi chạy smoke

Không lỗi nào là "mô hình hiểu sai đề".

| | Lỗi | Bắt được nhờ |
|---|---|---|
| 1 | IR không có `intersect_line_line` (kernel có sẵn) | bài 3, 3/3 lượt thử |
| 2 | thẻ văn phạm gọi `list[str]` là *"khối lệnh"* | bài 3, mô hình bọc giá trị vào `literal` |
| 3 | biến kiểu hình học **gán được literal** | bài 2, rác nằm trong `polygon3` |
| 4 | lời từ chối nói **"bài thuộc môn khác"** sau 120s dựng hình | bài 2 và 3 |
| 5 | lưới hoà giải tên áp ở C₁a mà **không** áp ở C₂ | bài 3, "chương trình tự mâu thuẫn" |

Lỗi 4 tệ nhất: nó **đổ cho đề bài** cái sai của hệ, và học sinh đọc xong sẽ đi
tìm bài khác trong khi bài của em vốn đúng chủ đề.

---

## 4. ⚠️ CỔNG KHÔNG MỞ — và lý do đã đổi bản chất

Bốn lượt smoke, **cùng một mã** ở ba lượt cuối:

| Lượt | 1 · trung điểm | 2 · thể tích | 3 · thiết diện |
|---|---|---|---|
| ① | ✅ served | ❌ `learner_surface` | ❌ `structural_coverage` |
| ② | ❌ `structural_coverage` | ✅ served | ❌ `structural_coverage` |
| ③ | ✅ served | ✅ served | ❌ `postconditions` |
| ④ | ✅ served (20 đối tượng) | ❌ `grounding` | ❌ `structural_coverage` |

**Chưa lượt nào 3/3, và tập bài trượt ĐỔI mỗi lượt.**

Mỗi bản vá đều có tác dụng thật — lỗi nó nhắm tới biến mất và không quay lại.
Nhưng lượt sau mô hình viết một chương trình khác, và chương trình khác trượt ở
một cổng khác. Đó đúng là chữ ký `RULES §3c` gọi tên: **DEEP_HARDENING** —
đuổi theo một biến ngẫu nhiên.

**Nên lượt này DỪNG vá.** Cổng smoke đã làm xong việc của nó: nó phân biệt được
"môi trường lệch" (đã sửa, kiểm được bằng máy) với "sinh không ổn định" (chưa
sửa, và không sửa được bằng thêm một lưới nữa).

### Hai gốc còn lại, đều đã đủ dữ liệu để gọi tên

**(a) Hợp đồng thiếu cách nói "đa giác từ các điểm đã đặt tên".** Bài 2 dựng
`ABCD` là đáy hình vuông; mô hình với tay tìm nó ở **2/4 lượt**, một lần qua
`assign literal`, một lần qua `initial_value` — hai đường khác nhau, cùng một ý
định. IR có `construct_solid(vertices: list[str])` nhưng **không có**
`construct_polygon`. Đây là lỗ hợp đồng có biên rõ, không phải nhiễu.

**(b) Hai lượt LLM đặt tên khác nhau cho cùng một vật.** Bài 3 trượt vì tên ở
**3/4 lượt**, mỗi lượt một biến thể:

```
hợp đồng `SA`  ·  chương trình `SA_line`
hợp đồng `AD`  ·  chương trình `line_AD`
hợp đồng `AD`  ·  chương trình `DA`          ← cùng đoạn thẳng, viết ngược
```

Prompt **đã** dặn *"CẢ HAI tên dưới đây đều phải có mặt trong
`memory_declarations`, đúng từng chữ"* (`_obligations_for_prompt`). Mô hình vẫn
không theo ở miền hình học, nơi nó có thiên kiến mạnh về cách gọi tên đường và
mặt. Đó là một **quan trắc về mô hình**, không phải một bug chờ vá.

Lưới hoà giải tất định là kiến trúc đúng cho lớp này (kiểm được, fail-closed khi
mơ hồ). Nhưng mở rộng nó theo từng biến thể quan sát được là đuổi theo đuôi —
quyết định mở rộng tới đâu phải là một quyết định có chủ đích, không phải phản
xạ sau mỗi lượt đỏ.

---

## 5. Điều lượt này KHÔNG chứng minh

- **N = 1 mỗi bài mỗi lượt.** Bốn lượt trên ba đề. Không tỉ lệ nào đọc được từ
  đây; các con số ở §4 là **đếm thô** và chỉ dùng để nói *"kết quả không ổn
  định"*, không dùng để nói *"tỉ lệ thành công là X"*.
- **Cổng smoke không phải benchmark.** Ba đề do tôi chọn, xếp theo độ khó tăng
  dần, để phân biệt "đường dây hỏng" với "sinh chưa tới". Nó không đại diện
  chương trình phổ thông.
- **Số nghĩa vụ dao động 0–3 trên cùng một đề.** Lượt đọc đề cũng không ổn định,
  và khi nó khai 0 nghĩa vụ thì `servable=true` **không** còn nghĩa là "đáp án đã
  được đối chiếu" — nó chỉ nghĩa là "chương trình chạy trọn". Ghi rõ vì một lượt
  đẹp không được phép che chỗ luận điểm mỏng nhất.

---

## 6. Chi phí

Bốn lượt × ba đề, `gemini-2.5-flash`, khoảng **60–80 lượt LLM**. Không lượt nào
dùng cache (cache dọn sạch trước mỗi lượt, có kiểm `cached=false` trong artifact).
