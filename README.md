# AlgoSim — Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích bài toán bằng ngôn ngữ tự nhiên hỗ trợ dạy học môn Tin học THPT

**[Chạy nhanh](#11-chạy-dự-án) · [Kiến trúc](#4-kiến-trúc-và-ranh-giới-r0) · [Phạm vi](#8-right-or-refuse-và-capability_gap) · [Tài liệu](#12-tài-liệu-dành-cho-developer)**

---

## 1. AlgoSim là gì?

Đề tài khoá luận cho chương trình Tin học THPT (GDPT 2018). Học sinh nhập một
bài toán Tin học bằng tiếng Việt; **LLM phân tích yêu cầu, lựa chọn hoặc cấu
hình năng lực mô phỏng phù hợp, còn engine tất định sinh trạng thái, diễn biến
và phản hồi tương tác để hiển thị bằng 2D hoặc 3D.** Hệ thống bám nội dung
chương trình GDPT 2018 (không tuyên bố phủ toàn bộ chương trình).

Câu chốt của cả đề tài: **LLM đọc đề, engine tất định diễn hoạt.** Ranh giới đó
được giữ ở mọi tầng — mục 3 và 4 giải thích vì sao nó là *luận điểm* chứ không
phải chi tiết kĩ thuật.

## 2. Vấn đề hệ thống giải quyết

Cơ chế của thuật toán, cổng logic hay giao thức mạng là **ẩn**. Tài liệu tĩnh
khó biểu diễn *đồng thời* quá trình thay đổi trạng thái và nguyên nhân của từng
bước — học sinh thấy kết quả cuối nhưng không thấy *tại sao* biến `max` đổi ở
đúng bước đó, *nửa nào* của dãy bị loại và *vì sao*.

Thứ đáng mô phỏng là **cơ chế ẩn** đó. Bài không có cơ chế ẩn thì mô phỏng chỉ
là trang trí — nguyên tắc này được ghi trong [docs/COVERAGE.md](docs/COVERAGE.md)
và ràng buộc những gì AlgoSim nhận mô phỏng.

## 3. Vì sao không để LLM sinh code / hoạt hình tự do?

Đây là câu hỏi trung tâm. Ba luận điểm:

1. **Output đúng schema vẫn có thể sai ngữ nghĩa** — một config hợp cú pháp
   không đảm bảo nó biểu diễn đúng bài toán.
2. **Structural validation không chứng minh một thuật toán tùy ý là đúng** —
   kiểm cấu trúc bắt được config méo, không bắt được một tiến trình do LLM tạo
   ra mà thường không có oracle độc lập nào để chứng minh đúng.
3. **Một mô phỏng sai nguy hiểm hơn `capability_gap`** — dạy sai tệ hơn không
   dạy, nên hệ thống chọn *đúng-hoặc-từ-chối* thay vì render xấp xỉ gây hiểu lầm.

Không phải suy đoán: các thử nghiệm phát triển ghi nhận LLM có thể **bỏ sót
thuộc tính quan trọng trong prompt dài** (đo được trong pha M8-PRE); vì vậy các
giá trị suy ra chắc chắn được xử lý bằng luật tất định phía hệ thống, không đi
xin LLM. Chi tiết mô hình đúng đắn: [docs/CORRECTNESS.md](docs/CORRECTNESS.md)
và [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md).

## 4. Kiến trúc và ranh giới R0

Mô phỏng là **xương sống**; LLM chỉ phân tích/ánh xạ, không điều khiển engine.

```
Đầu vào ngôn ngữ tự nhiên (text / .docx / code / ảnh)
→ analyze          trích semantic requirements (vai trò ngữ nghĩa, nguồn kết quả…)
→ representation    plan tất định (từ manifest năng lực DSL)
→ classify          định tuyến theo NĂNG LỰC: module chuyên biệt hoặc generic.rule_scene
→ computation gate  server quyết accept / capability_gap (đường generic)
→ simulate          LLM điền config được validate
→ validation        cấu trúc + tương thích ngữ nghĩa (vai trò + nguồn giá trị)
→ engine tất định   sinh trạng thái / diễn biến / phản hồi
→ renderer 2D hoặc 3D (dùng chung state)
```

Ai sở hữu cái gì — bảng này là hiện vật rõ nhất của ranh giới R0:

| Thành phần | Sở hữu | Không sở hữu |
|---|---|---|
| **LLM (Gemini)** | phân tích, chọn capability / `simulation_id`, điền *candidate config/spec* | canonical state, timeline, kết quả, correctness |
| **Validator & Capability Gate** | schema, giới hạn, coherence, khả năng biểu diễn, quyết định accept / gap | *không tự tạo diễn biến để vá capability thiếu* |
| **Engine tất định** | `init`, transitions, timeline, result, learner consequence | pixel, layout, camera |
| **Renderer 2D/3D** | layout, camera, animation, ánh xạ trực quan | semantic truth và correctness |

Ba tầng dữ liệu chảy một chiều:

```
Validated Config/Spec  →  Authoritative Engine State  →  2D/3D Render Model
```

Chính ba tầng này cho phép **2D và 3D dùng chung `config`/`state`/`timeline`,
không fork engine** — chuyển chế độ hiển thị không đụng tới sự thật ngữ nghĩa.

## 5. Các họ capability hiện có

Mô tả theo **họ năng lực** (không phải theo tên môn hay số lượng module) — mỗi
họ phơi bày một cơ chế ẩn:

| Họ năng lực | Mô phỏng | Cơ chế ẩn được phơi bày |
|---|---|---|
| Tìm kiếm & duyệt dãy | tìm max/min, đếm/tổng theo điều kiện, tìm tuần tự, tìm nhị phân | biến trạng thái đổi ở bước nào và vì sao; vùng nào bị loại khỏi phạm vi tìm |
| Sắp xếp | nổi bọt, chèn | so sánh nào dẫn tới đổi chỗ (nổi bọt) hay dời chỗ (chèn) — hai cơ chế khác nhau |
| Quét dãy khai báo (bounded scan) | interpreter chạy một *spec quét-một-lượt* thay vì một module viết tay | biến thể duyệt-một-lượt mới không cần thêm module (xem mục 6) |
| Biểu diễn dữ liệu | thập phân → nhị phân | từng bit sinh ra từ phép chia lấy dư |
| Logic số | cổng AND (tương tác, không có timeline) | bảng chân trị hình thành từ chính thao tác bật/tắt của học sinh |
| Mạng | định tuyến gói tin; đóng gói/mở gói TCP/IP qua 4 tầng | đường đi và chi phí; PDU biến đổi qua từng tầng |
| Cảnh theo luật (DSL generic) | cảnh do LLM compose từ primitive có sẵn — **chỉ khi** primitive hiện có biểu diễn trung thực được cơ chế | quan hệ và luật mà đề mô tả |

Danh mục thi hành đầy đủ (kèm `simulation_id`) ở
[docs/CODE_INDEX.md](docs/CODE_INDEX.md) — README không liệt kê id vì đó là chuỗi
kĩ thuật và thay đổi theo milestone. **DSL generic không phải "fallback chung"**:
nếu primitive hiện có không biểu diễn trung thực được cơ chế thì kết quả là
`capability_gap` (mục 8), không phải ép vào generic.

## 6. Những bài không cần module riêng trong họ đã hỗ trợ

Đây là tuyên bố kiến trúc mạnh của đề tài, và ranh giới của nó phải nêu cùng chỗ.
Một **interpreter khai báo** nhận một *spec quét-một-lượt* phủ được biến thể
**mới** mà không thêm module — ví dụ đã chạy trọn từ NL đến kết quả: *"tìm ngày
đầu tiên nhiệt độ vượt 35°C"*, bài mà không module chuyên biệt nào khớp (tìm
tuần tự chỉ so *bằng*, không so *vượt ngưỡng*).

Ranh giới bắt buộc, nêu ngay tại đây:

- interpreter xét **tối đa n phần tử**; execution/trace có giới hạn **tuyến tính
  theo n**;
- spec **không tự định nghĩa vòng lặp / control flow**; enum đóng; không biểu
  thức/mã tùy ý; không `while`/`for`;
- **non-Turing-complete** — không phải một ngôn ngữ lập trình ẩn;
- vòng lặp trên biến tự do vẫn bị từ chối trung thực.

AlgoSim **không** tuyên bố sinh mô phỏng phổ quát.

## 7. Hỗ trợ dạy học và tương tác 2D/3D

- **Ba chế độ tương tác** suy từ capability của module: `progressive` (có
  timeline → có Next/Prev), `exploratory` (không timeline, ví dụ cổng AND),
  `hybrid`. Module không khai `timeline` thì UI không bịa ra "một bước".
- **Dự đoán**: học sinh đoán trước, **engine chấm bằng chính trace tất định** —
  LLM không bao giờ là giám khảo.
- **3D là renderer, không phải domain**: cùng `config`/`state`/`timeline`, không
  fork engine. Chiều sâu 3D phải **trung thực** — module đóng gói TCP/IP dùng
  Z = *tầng giao thức* (3D sư phạm); còn `network.packet_routing` được **tài liệu
  phân loại là `architectural_poc`** (Z chỉ là bố cục, không mang nghĩa khái
  niệm). README không tuyên bố "3D luôn giúp học".

`network.packet_routing` minh hoạ đường đi trên mạng bằng BFS — **không phải một
engine Dijkstra có trọng số tổng quát.**

## 8. Right-or-refuse và `capability_gap`

Sau khi phân tích yêu cầu và **trước khi một cấu hình generic được chấp nhận để
thực thi**, hệ thống kiểm tra capability coverage. Vai trò ngữ nghĩa nào không có
primitive phủ, hoặc một yêu cầu mà **kết quả phải được tính qua cơ chế thuật toán
không engine nào sở hữu** → dừng với `status: unsupported`,
`failure_category: capability_gap`, thay vì ép sai primitive.

Đây là chỗ tuyên bố *đúng-hoặc-từ-chối* thành hành vi đo được. Ví dụ đã xác nhận
bằng chạy LLM thật: đề *"mô phỏng thuật toán Dijkstra tìm đường ngắn nhất"* —
không engine tất định nào sở hữu cơ chế (khoảng cách tạm, chọn đỉnh gần nhất,
nới cạnh…) — trả về `capability_gap`, **không** dựng một cảnh minh hoạ giả.

Phân biệt hai loại đúng đắn ([docs/CORRECTNESS.md](docs/CORRECTNESS.md)):

- **Mô phỏng hệ sinh**: right-or-refuse — đúng hoặc từ chối.
- **Thao tác / dự đoán của học sinh**: *được phép sai* và nhận phản hồi tất định
  — sai là cơ hội học, không phải lỗi hệ thống.

Không có luật tất định để phán đúng/sai → `unsupported_to_verify`, hệ **không**
nhờ LLM chấm bừa.

## 9. Bằng chứng correctness / evaluation

README nêu các **hợp đồng ổn định**, không đóng đinh con số (số sống trỏ
[docs/CURRENT_STATE.md](docs/CURRENT_STATE.md)):

- **Test mặc định không gọi API LLM thật** — guard chặn ở tầng transport, nên
  một suite xanh *chính là* bằng chứng không tốn quota; test nào quên mock sẽ
  chết ở guard.
- **Engine / validator / renderer được kiểm offline.**
- **Đánh giá LLM tách khỏi test correctness**: eval đo *LLM có compose nổi một
  spec hợp lệ không* (classification accuracy, `valid_spec_first_attempt_rate`,
  `gap_gate_recall`…), không đo engine.
- **Live evaluation là opt-in** có ngân sách gọi API (`ALLOW_LIVE_AI=1`).
- Bộ case dùng để tinh chỉnh prompt **không phải held-out benchmark** — không
  được trình bày như benchmark độc lập.

Test suite **không nói gì về hiệu quả học tập** — đề tài chưa có thực nghiệm sư
phạm và không tuyên bố hiệu quả học tập.

## 10. Ví dụ end-to-end

Một đường đi trọn vẹn, dùng chính bài flagship của mục 6:

1. Học sinh nhập *"tìm ngày đầu tiên nhiệt độ vượt 35°C"* (tiếng Việt).
2. **analyze** trích yêu cầu: duyệt một dãy số, điều kiện *vượt ngưỡng*, dừng sớm.
3. **kiểm capability coverage** — không rơi vào `capability_gap` (duyệt-một-lượt
   trên dãy cho sẵn nằm trong năng lực).
4. **classify** chọn họ quét dãy khai báo (không module chuyên biệt nào so
   *vượt ngưỡng*).
5. **spec khai báo được validate** (enum đóng, giới hạn tuyến tính theo n).
6. **interpreter tất định** chạy, dừng đúng vị trí đầu tiên vượt 35°C và dựng
   trace từng bước — LLM không sở hữu bước nào.

## 11. Chạy dự án

```bash
# 1. Frontend (một lần)
cd frontend && npm install

# 2. Cấu hình key Gemini cho backend
#    Sao chép backend/.env.example → backend/.env, dán key thật vào
#    (lấy key miễn phí: https://aistudio.google.com/apikey)

# 3. Backend + PostgreSQL (Docker)
docker compose up -d --build

# 4. Frontend (cửa sổ lệnh riêng, giữ hot-reload khi dev)
cd frontend && npm run dev     # mở http://localhost:3000
```

Lệnh hay dùng: `docker compose logs -f backend` (xem log) ·
`docker compose down` (dừng) · `docker compose up -d --build` (chạy lại sau khi
sửa backend).

**Không có key vẫn dùng được**: chọn **bài mẫu** trong giao diện — các mô phỏng
phân tích sẵn chạy offline hoàn toàn client-side, không cần backend.

**Kiểm thử:**

```bash
cd frontend && npm test          # vitest: engine + simulation domains + generic DSL
cd backend  && python -m pytest  # pipeline, DSL validator, semantic checks
```

Cơ sở dữ liệu, migration Alembic, quyền sở hữu schema/dependency →
[docs/OPERATIONS.md](docs/OPERATIONS.md).

## 12. Tài liệu dành cho developer

Thứ tự đọc bắt buộc trước mọi thay đổi không tầm thường, và luật vàng: **nếu tài
liệu mâu thuẫn với code/test — code/test thắng.**

| Tài liệu | Mục đích |
|---|---|
| [docs/ARCHITECTURE_MAP.md](docs/ARCHITECTURE_MAP.md) | Bản đồ kiến trúc: data flow, bảng sở hữu, các bất biến đánh số (mỗi cái kèm file thực thi + test khoá), anti-pattern đã ship bug |
| [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md) | Trạng thái sống: pass count, gì shipped mỗi milestone, capability gap *cố ý*, known issues, scope freeze |
| [docs/CODE_INDEX.md](docs/CODE_INDEX.md) | Index module/export + mức phải re-verify khi đụng mỗi cái |
| [docs/CORRECTNESS.md](docs/CORRECTNESS.md) | Mô hình đúng đắn canonical ↔ learner |
| [docs/COVERAGE.md](docs/COVERAGE.md) | Phủ chương trình + nguyên tắc "chỉ mô phỏng khi có cơ chế ẩn" + tuyên bố bị cấm |
| [docs/RULES.md](docs/RULES.md) | Con trỏ ngắn: thứ tự đọc + luật cứng |

Thêm một domain chuyên biệt chạm **hai điểm**, không sửa lõi: một `SimSpec` ở
`backend/app/simulation/catalog.py` và một dòng `register…Domain()` ở
`frontend/src/simulations/index.ts`.

⚠️ `DESIGN.md` (ở gốc repo) **không phải** thiết kế đề tài — nó là file token UI
(màu/typography), dễ hiểu nhầm vì cái tên.

## 13. Trạng thái và giới hạn

Số sống (pass count, milestone) ở [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md).
Các giới hạn **cố ý**:

- Phủ ở **mức tên bài** theo SGK, không phải toàn văn chương trình GDPT 2018.
- TCP nâng cao (bắt tay ba bước, phân mảnh, rẽ nhánh TCP/UDP) **cố tình** trả
  `unsupported`, không ép vào mô hình v1.
- Đường đi ngắn nhất có trọng số (Dijkstra) **ngoài phạm vi công khai** của đề
  tài ([docs/COVERAGE.md](docs/COVERAGE.md)) — `capability_gap` là câu trả lời
  đúng, không phải thiếu sót tạm thời.
- Đang có scope freeze; mở rộng cần approval riêng.

Đề tài **chưa có thực nghiệm sư phạm** nên không tuyên bố hiệu quả học tập.
