# Nghiên cứu và xây dựng hệ thống mô phỏng 3D hình học không gian

Khoá luận. Học sinh nhập một bài hình học không gian bằng **tiếng Việt**; hệ
thống dựng lại hình trong không gian ba chiều, chạy từng bước dựng, và trả lời
bằng **số chính xác tuyệt đối** — không làm tròn ở bất kỳ đâu.

**[Chạy dự án](#11-chạy-dự-án) · [Kiến trúc](#3-kiến-trúc) · [Demo](#7-demo) ·
[Phạm vi](#9-phạm-vi) · [Giới hạn](#10-giới-hạn)**

Bảng đối chiếu **tuyên bố ↔ bằng chứng ↔ giới hạn**:
[`docs/THESIS_READINESS.md`](docs/THESIS_READINESS.md) — đó là nguồn thẩm quyền
duy nhất cho mọi con số; README này không chép lại chúng.

---

## 1. Mục tiêu

Nhận đề hình học không gian ở dạng ngôn ngữ tự nhiên, để **LLM tổng hợp một
chương trình có cấu trúc** (Semantic Program), rồi để các tầng **tất định** thẩm
định, thực thi và xác nhận; từ trạng thái ấy dẫn xuất dòng thời gian dựng hình
và một cảnh 3D tương tác.

Câu hỏi nghiên cứu đứng sau: *một bài toán mới có buộc phải viết mã mới không?*
Câu trả lời mà hệ này đưa ra là **không — miễn bài ấy biểu diễn được bằng IR
hiện có**. Đó là một mệnh đề có điều kiện, và điều kiện ấy quan trọng.

## 2. Nguyên lý — ranh giới R0

**LLM đọc đề, engine tất định diễn hoạt.** Đây là *luận điểm* của đề tài chứ
không phải một chi tiết kĩ thuật.

```
đề tiếng Việt
   → LLM: đọc đề        → RequestContract  (dữ kiện + nghĩa vụ, ĐÓNG BĂNG)
   → LLM: tổng hợp      → Semantic Program (các BƯỚC DỰNG, không có toạ độ kết quả)
   ─────────────────── từ đây trở đi KHÔNG có LLM ───────────────────
   → thẩm định lược đồ · thẩm định tĩnh
   → grounding + trung thực năng lực
   → thực thi (số hữu tỉ + căn, CHÍNH XÁC)
   → checker (kiểm lại kết luận từ HÌNH, không tin con số chương trình khai)
   → transport
   → trace + Scene3D
```

LLM **không bao giờ** được phát một toạ độ kết quả. Nó nói *"giao tuyến của
(SAB) và (SCD)"*; toạ độ do nhân hình học tính. Mọi toán hạng hình học trong IR
là **TÊN** của một vật đã dựng — bất biến này được cưỡng chế ở lược đồ, không
phải nhắc trong prompt.

Điều hệ **không** làm: LLM không sinh hoạt hình, không sinh toạ độ, không quyết
đúng/sai. Nó sinh *các bước dựng*.

## 3. Kiến trúc

| tầng | vị trí | sở hữu |
|---|---|---|
| Đọc đề | `backend/app/ai/` (`geometry_analyze.md`) | LLM → `RequestContract` |
| Tổng hợp | `backend/app/ai/` (`geometry_program_generator.md`) | LLM → Semantic Program |
| Hợp đồng IR | `app/simulation/semantic_program/contract.py` | lược đồ Pydantic, biên chuẩn hoá |
| Thẩm định tĩnh | `…/ir_static_check.py` | định-nghĩa-trước-khi-dùng · kiểu toán hạng · số hữu tỉ |
| Cổng ngữ nghĩa | `…/grounding_gate.py`, `coverage_gate.py`, `postconditions.py` | dữ kiện có thật · trung thực năng lực |
| Thực thi | `…/interpreter.py` + `app/simulation/geometry/` | trạng thái, dòng thời gian, kết quả |
| Nhân hình học | `app/simulation/geometry/` | `exact → predicates → kernel → measure`, **một chiều** |
| Cảnh | `…/scene3d.py`, `simulation_state.py` | `Scene3D` (dữ liệu, không phải hình vẽ) |
| Mặt 3D | `frontend/src/simulations/domains/geometry/` | dựng hình, chọn, cô lập, tua bước |

Renderer **chỉ đọc** trạng thái; không có đường ngược. Nhân hình học không
import `app.ai` — ranh giới ấy là bất biến kiến trúc, kiểm bằng test.

Chi tiết cho khoá luận — sơ đồ, vùng LLM/tất định, đường từ chối:
[`docs/THESIS_ARCHITECTURE.md`](docs/THESIS_ARCHITECTURE.md).
Chi tiết cho người sửa mã (bất biến đánh số, anti-pattern):
[`docs/ARCHITECTURE_MAP.md`](docs/ARCHITECTURE_MAP.md).

## 4. Semantic Program (IR)

Một chương trình gồm **khai báo bộ nhớ** và **các câu lệnh dựng**. Mỗi câu lệnh
dựng là **một bước học sinh nhìn thấy** — đó là lý do chúng là *câu lệnh* chứ
không phải *biểu thức*: biểu thức tính ra giá trị nhưng không để lại dấu vết.

```json
{"kind": "construct_point", "target_var": "M",
 "expr": {"kind": "midpoint", "a": "S", "b": "C"}}
{"kind": "construct_plane", "target_var": "SAD", "through": ["S", "A", "D"]}
{"kind": "assign", "target_var": "d",
 "expr": {"kind": "measure", "quantity": "distance", "of": "A", "wrt": "SAD"}}
```

Hợp đồng gửi cho mô hình được **sinh từ chính `contract.py`**, nên nó không thể
trôi khỏi thứ hệ cưỡng chế. Ô toán hạng khai luôn kiểu ngay tại chỗ dùng —
`through: [tên<point3>, …]`, `vector: tên<vector3>`.

**Bài mới trong phạm vi IR không cần module riêng theo dạng bài.** Điều này đo
được: mã sản phẩm không có một nhánh nào rẽ theo dạng bài (guard quét AST), và
runtime giữ nguyên qua nhiều đợt đề mới. Nó **không** có nghĩa là mọi bài hình
học đều chạy được — bài ngoài IR bị **từ chối**, không được tự nới.

## 5. Nhân hình học

**Số học chính xác tuyệt đối.** `Fraction` cho hữu tỉ, `Radical` cho căn thức.
**Không có `float` ở bất kỳ đâu trong miền hình học** — mất tính chính xác là
mất khả năng so bằng đúng, tức mất thứ phân biệt hệ này với một bộ vẽ hình.
Đáp số ra dạng `3√89/5`, không phải `5.6603…`.

Đang hỗ trợ:

- **Kiểu:** `point3` `vector3` `line3` `plane3` `polygon3` `solid` `section`
- **Phép dựng:** `midpoint` · `divide_segment` · `project_onto` ·
  `intersect_line_plane` · `intersect_plane_plane` · `intersect_line_line` ·
  `vector_from_points` · `translate`
- **Câu lệnh:** `construct_point/line/plane/polygon/solid/section` ·
  `declare_point` · `assign`
- **Phép đo:** `distance` · `angle_cos_sq` · `angle_cos` · `volume`

`angle_cos_sq` trả **cos² của góc**, không trả độ: góc hình học phần lớn vô tỉ
còn cos² của nó hữu tỉ, nên trả về độ là ép một phép làm tròn vào giữa một chuỗi
tất định.

Danh sách trên là **toàn bộ** năng lực đang hoạt động, không phải một mẫu.

## 6. Scene3D và tương tác

Cảnh dựng **tất định từ trạng thái** — chương trình không khai gì để hiển thị.
Mỗi vật mang `producer` (phép dựng nào sinh ra nó) và `depends` (nó dựa vào
đâu), nên cảnh trả lời được cả *hình trông thế nào* lẫn *hình được tạo ra thế
nào*.

Học sinh làm được: xoay/thu phóng · chọn một vật và soi xuất xứ · xem cây thành
phần · cô lập, bung hình · **tua từng bước dựng**. Bất biến `frame k ⇔ trace[k]`
giữ song ánh giữa khung hình và bước thực thi.

Có chế độ **lớp học trực tiếp** (giáo viên chiếu, học sinh theo cùng bước).

## 7. Demo

Tập demo đóng, chạy **hoàn toàn tất định, 0 lượt gọi model**, từ chương trình đã
lưu trong artifact có xuất xứ rõ:

| ca | nội dung | đáp số |
|---|---|---|
| `n1` | dựng đỉnh thứ tư của hình thoi từ vectơ → đo tới đường chéo | `√3` |
| `n2` | lăng trụ **xiên**: hai vectơ dẫn xuất + trung điểm → khoảng cách | `3√3` |
| `t3` | dây chuyền tịnh tiến bốn đỉnh, chuỗi phụ thuộc sâu | `3√89/5` |
| `t4` | hình chiếu trong chuỗi phụ thuộc | `2√2` |
| `n4` | **ca TỪ CHỐI** — chương trình trích dẫn dữ kiện không có trong hợp đồng | bị chặn ở grounding |

Ca thứ năm là **cố ý**. Một demo chỉ toàn ca xanh giấu mất nửa luận điểm: hệ
phải nói KHÔNG **có địa chỉ**, chứ không chết câm.

**Thiết diện** (`v2_04`) chạy ở chế độ rút gọn và được đếm riêng — artifact của
nó ra đời trước khi bộ đo lưu `RequestContract`, nên không chạy được cổng
grounding. Gộp nó vào con số demo là báo cáo một chuỗi đủ mà thực ra thiếu một
cổng.

⚠️ Ca `n3` **không** được dùng làm bằng chứng đúng đắn ngữ nghĩa: oracle của nó
không phân biệt được hai cách dựng khác nhau (cùng cho số 4). Đây là lỗi của
artifact đánh giá, đã ghi thành đính chính.

Kịch bản trình bày — thứ tự, thao tác, chỗ cần chỉ vào:
[`docs/THESIS_DEMO.md`](docs/THESIS_DEMO.md).

## 8. Kiểm thử và bằng chứng

Hồi quy offline **không tiêu một lượt gọi model nào**: guard nằm ở biên mạng,
suite xanh ⇔ không có call nào.

Bằng chứng đánh giá nằm ở [`docs/evaluation/geometry/`](docs/evaluation/geometry/)
và **không được sửa lại** khi chạy lượt mới — mỗi lượt là một mốc so sánh, kể cả
lượt thất bại.

Số liệu, phân loại và giới hạn: [`docs/THESIS_READINESS.md`](docs/THESIS_READINESS.md).

## 9. Phạm vi

- Hình học **không gian** ba chiều, chương trình Toán 11–12.
- Chỉ những gì **IR hiện có biểu diễn được**; bài ngoài đó bị từ chối.
- Chỉ khối **đa diện lồi**. Không mặt cong (cầu, nón, trụ).
- Ba loại hoạt động: dựng hình/thiết diện · quan hệ song song–vuông góc ·
  khoảng cách/thể tích/góc.

Phủ chương trình là **một phần và có chủ đích** — hệ **không** tuyên bố phủ toàn
bộ hình học THPT.

Kéo–thả liên tục kiểu GeoGebra nằm **ngoài phạm vi**: nó liên tục, và phá song
ánh `frame k ⇔ trace[k]` mà cả kiến trúc dựng lên để giữ.

## 10. Giới hạn

Dẫn từ [`docs/THESIS_READINESS.md`](docs/THESIS_READINESS.md):

- `ANALYZE_SOURCE_FACT_COMPLETENESS = PARTIAL` — tầng đọc đề có lần **không**
  đưa toạ độ đề cho vào hợp đồng. Quan sát trên 4 đề, **chưa đo lặp lại**, nên
  không gọi nó là ngẫu nhiên hay hệ thống.
- `CONTROL_FLOW_DEFINITE_ASSIGNMENT = PARTIAL` — một vật chỉ dựng trong một
  nhánh có thể không chạy thì bị **từ chối tĩnh**, không chạy sai.
- `SECTION_VERTEX_INTERSECTION_GAP` — còn mở.
- Mặt cong: ngoài phạm vi hiện tại.
- **Tác động lên người học: chưa đánh giá.**

## 11. Chạy dự án

Yêu cầu: Python 3.12 + venv ở `backend/.venv`, Node 20+, Docker (chỉ khi cần
đường phân tích LLM).

```bash
# --- giao diện, KHÔNG cần backend, KHÔNG cần API key ---
cd frontend && npm install && npm run dev        # http://localhost:3000

# --- backend + Postgres ---
docker compose up -d --build

# --- kiểm thử (0 lượt gọi model) ---
cd backend  && .venv/Scripts/python.exe -m pytest -q
cd frontend && npx vitest run && npm run build

# --- demo tất định, 0 lượt gọi model ---
cd backend  && .venv/Scripts/python.exe scripts/replay_demo_cases.py
cd backend  && .venv/Scripts/python.exe scripts/audit_demo_crash_surface.py

# --- demo trong trình duyệt thật (cần `npm run dev` ở cửa sổ khác) ---
cd frontend && node scripts/spot-check-demo.mjs
```

Đường phân tích LLM là **opt-in và tiêu quota thật**; nó không cần cho demo,
kiểm thử hay phát triển giao diện.

## 12. Hướng phát triển

- Mở rộng IR khi có **bằng chứng** rằng một lớp bài cần nó — không mở trước.
- Hình học mặt cong, nếu nghiên cứu tiếp.
- Cải thiện độ đầy đủ của tầng đọc đề.
- Đánh giá tác động lên người học.
- Tương tác nâng cao trên cảnh 3D.

Kiến trúc (ranh giới R0, Semantic Program, biên tất định) không gắn với hình
học và **có thể** dùng lại cho môn khác. Đó là hướng của kiến trúc, **không
phải năng lực hiện tại** của hệ thống.

---

Tài liệu cho người phát triển: [`docs/`](docs/) — bắt đầu từ
[`RULES.md`](docs/RULES.md), [`ARCHITECTURE_MAP.md`](docs/ARCHITECTURE_MAP.md),
[`CURRENT_STATE.md`](docs/CURRENT_STATE.md).
