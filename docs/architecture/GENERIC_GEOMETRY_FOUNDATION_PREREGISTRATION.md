# Tiền đăng ký nền tảng hình học tổng quát (W13 → W14)

**Ngày:** 2026-10-01 · **Task:** `W13_GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_ARCHITECTURE_PREREGISTRATION`
· **Đọc mã tại:** `bf5a7907` · **Trạng thái:** `PREREGISTERED` — thiết kế và tiêu chí
nghiệm thu, **chưa** đổi mã sản phẩm.

Đầu vào: [`GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md`](GEOMETRY_CAPABILITY_AND_NON_ABSOLUTE_AUDIT.md),
[`geometry_capability_matrix_v2.json`](geometry_capability_matrix_v2.json), review người
W12 (`NEEDS_CHANGES`, W12-H1…H4). Wave kế tiếp được đăng ký ở đây:
**`W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION`** (§6).

## 0. Phạm vi

W14 làm ba việc, theo thứ tự: (A) dựng hình theo **lớp hình** cho khối đa diện,
dùng chung cho mọi họ — đóng W12-H1/H2 mà không có nhánh theo tên họ; (B) chính
sách giả định/mặc định — đóng `ISSUE-ARCH-ASSUMPTION-CHANNEL-UNSTATED-DIMENSION`
(W12-H4); (C) một chuẩn hoá nguồn an toàn — đóng lỗi chấp nhận nhầm *"AB dài 5
cm"* (NA-57). Mọi thứ khác ở §7.

Trước khi W14 bắt đầu, người dùng cần trả lời **D2 và D3** (§8). D1, D4, D5
có thể chờ.

## 1. Sáu trừu tượng dùng chung

| # | Trừu tượng | Thay cho | Ghi chú |
|---|---|---|---|
| 1 | **Lớp hình** (`PYRAMID_LIKE`, `PRISM_LIKE`, `CONE_LIKE`, `SPHERE_LIKE`, `SECTION`) dẫn từ **vai trò tô-pô** (đỉnh + chu trình đáy; hai chu trình tương ứng + phép tịnh tiến; tâm + bán kính; vật cắt × khối) | nhánh theo tên họ trong `compiler.py` | ID họ chỉ còn ánh xạ vào lớp; bộ lập kế hoạch không được rẽ nhánh theo ID họ (khoá bằng quét AST) |
| 2 | **Vai trò dựng** (phép ngữ nghĩa ở §2.1) gắn tại **producer** | suy vai trò từ lời kể | đúng quyết định 5 của tu chính án occlusion |
| 3 | **Kế hoạch dựng**: dãy vai trò bắt buộc của một lớp hình, cộng các vai trò có mặt trong hợp đồng (chiều cao cho/hỏi? chân đường cao ở đâu? có đáy trên?) | chuỗi câu lệnh viết tay của từng họ | một kế hoạch, hai người dùng: compiler (phát câu lệnh) và trace/cảnh (gắn vai trò) |
| 4 | **Lớp xuất xứ giá trị**: `GIVEN_VALUE` · `DERIVED_VALUE` · `MODEL_ASSUMPTION` · `VISUAL_DEFAULT` | `LAYOUT_DERIVED` và `model_assumption` tách rời, không nghĩa vụ chứng minh | `LAYOUT_DERIVED` thành một dạng `MODEL_ASSUMPTION` có nghĩa vụ bất biến đáp số (§3) |
| 5 | **Khả thi đặt toạ độ**: phép kiểm tất định xem một hình có cách đặt chính xác trong ℚ³ dưới hệ trục đã chọn hay không, có mã từ chối ổn định | im lặng / số thập phân xấp xỉ qua `hf()` | điều kiện trước cho mọi họ "đều" (§7) |
| 6 | **Bản ghi năng lực môi trường** cho mỗi cổng đo | ghi cứng GPU/trình duyệt/viewport | §5 |

## 2. Mô hình dựng hình tổng quát

### 2.1 Từ vựng phép ngữ nghĩa — tập **mở**

Đây là vai trò của một **bước dựng**, không phải câu lệnh IR mới. Cột "IR hiện
tại" cho biết phép ấy đã có đường biểu diễn chưa.

| Phép | Ý nghĩa | IR hiện tại | Trạng thái |
|---|---|---|---|
| `DECLARE_ENTITIES` | đặt các điểm dữ kiện / khung | `declare_point` (+ khung khởi tạo) | có |
| `CONSTRUCT_BASE` | dựng mặt đáy | `construct_polygon` | có |
| `CONSTRUCT_AXIS` | dựng trục khối tròn xoay | `construct_line` / `construct_segment` — nhưng `construct_curved_solid` không lộ trục thành vật | một phần |
| `CONSTRUCT_HEIGHT` | dựng đường cao (đỉnh → chân) | `construct_segment`; chân bằng `project_onto` | có (chỉ họ chóp chữ nhật dùng) |
| `CONSTRUCT_CENTER` | tâm đa giác / tâm đáy | tổ hợp `midpoint`, `divide_segment` — không có biểu thức "tâm" riêng | một phần |
| `CONSTRUCT_RADIUS` | đoạn tâm → vành | `construct_segment` (vai trò không có) | một phần |
| `CONSTRUCT_CIRCLE` | đường tròn đáy của khối tròn xoay | chỉ có đường tròn **thiết diện** (`intersect_plane_curved`) | thiếu |
| `CONSTRUCT_TRANSLATED_FACE` | đáy trên = tịnh tiến đáy dưới | `translate` + `construct_polygon` (đường hộp chữ nhật) | có |
| `CONSTRUCT_LATERAL_BOUNDARY` | các cạnh bên | `construct_segment` dạng nhóm | có |
| `CONSTRUCT_GENERATOR` | đường sinh của nón/trụ | `construct_segment` (vai trò không có) | một phần |
| `CONSTRUCT_CURVED_SURFACE` | mặt cong | gộp trong `construct_curved_solid` | một phần |
| `CLOSE_SOLID` | khép khối (mặt tô, cạnh chuẩn) | `construct_solid` / `construct_curved_solid` | có |
| `CONSTRUCT_CUTTING_OBJECT` | mặt phẳng cắt | `construct_plane`, `construct_plane_from_equation`, `plane_perpendicular_to_line` | có |
| `CONSTRUCT_INTERSECTION` | giao điểm, từng cạnh thiết diện | `intersect_*`, sự kiện `EXTEND` của `construct_section` | có |
| `CLOSE_SECTION` | khép thiết diện, tô mặt | bước hoàn tất của `construct_section` | có |
| `CONSTRUCT_AUXILIARY_GEOMETRY` | dựng phụ (chân vuông góc, đoạn khoảng cách, vectơ) | `construct_point/line/segment/plane` + biểu thức | có |

Thêm một phép vào tập này phải kèm: vai trò hình học, lớp hình dùng nó, và điều
kiện bước hợp lệ (§2.2). Không thêm phép chỉ để tăng số bước.

### 2.2 Bước dựng hợp lệ

| Mã | Tiêu chí |
|---|---|
| V1 | **Thay đổi quan sát được**: mỗi bước hình học đổi tập vật hiện hoặc tiến độ thiết diện (bất biến #35). Không có khung tĩnh. |
| V2 | **Một vai trò chính**, gắn ở producer, lấy từ tập §2.1 — không suy từ lời kể. |
| V3 | **Lời kể ⇔ vật**: mọi vật mà lời kể của bước nhắc tới phải có mặt trong cảnh của bước ấy (gốc của W12-H1: lời kể "dựng đường cao" mà không có vật đường cao). |
| V4 | **Thứ tự phụ thuộc**: một vật chỉ hiện khi mọi vật trong bao đóng `depends` của nó đã hiện. |
| V5 | **Không bước giả**: không bước nào tồn tại để đạt một con số; bước lặp lại một vật đã hiện mà không đổi gì là không hợp lệ. |
| V6 | **Một cạnh, một chủ hình**: cạnh bên dựng thành đoạn trước khi khép khối phải trao quyền vẽ cho cạnh chuẩn của khối sau khi khép (đúng quyết định 2 và 11 của tu chính án occlusion) — không vẽ đôi. |
| V7 | **Gộp vai trò**: khi hai vai trò trùng một vật (đường cao trùng cạnh bên tại đỉnh góc vuông), vật ấy mang cả hai vai trò và hiện **một** lần. |
| V8 | **Khép sau cùng**: `CLOSE_SOLID` đến sau đáy và biên bên của nó, và đổi hình (mặt tô / cạnh chuẩn); nếu không đổi gì thì gộp vào bước trước. |
| V9 | **Frame k ⇔ trace[k]** (bất biến #31): bước con là sự kiện trace thật, như `EXTEND` của thiết diện — không có khung nội suy ở frontend. |

### 2.3 Độ phủ ngữ nghĩa tối thiểu theo lớp — **không** số đếm

| Lớp | Các vai trò phải xuất hiện, theo thứ tự | Có điều kiện |
|---|---|---|
| `PYRAMID_LIKE` | `DECLARE_ENTITIES` → `CONSTRUCT_BASE` → `CONSTRUCT_LATERAL_BOUNDARY` → `CLOSE_SOLID` | `CONSTRUCT_HEIGHT` khi chiều cao được cho, hỏi, hoặc dùng trong lời giải (gộp với cạnh bên khi chân là một đỉnh đáy, V7); `CONSTRUCT_CENTER` trước nó khi chân là tâm đáy hoặc một điểm dẫn xuất |
| `PRISM_LIKE` | `DECLARE_ENTITIES` → `CONSTRUCT_BASE` → `CONSTRUCT_TRANSLATED_FACE` → `CONSTRUCT_LATERAL_BOUNDARY` → `CLOSE_SOLID` | với lăng trụ xiên, vectơ tịnh tiến thấy được qua cạnh bên đầu tiên; `CONSTRUCT_HEIGHT` (phụ) khi chiều cao được cho/hỏi và không trùng cạnh bên |
| `CONE_LIKE` | `DECLARE_ENTITIES` → `CONSTRUCT_AXIS` → `CONSTRUCT_RADIUS` → `CONSTRUCT_CIRCLE` (đáy; trụ thêm đáy trên) → `CONSTRUCT_GENERATOR` → `CONSTRUCT_CURVED_SURFACE` → `CLOSE_SOLID` | **cần đổi IR/sự kiện** — hôm nay khối cong là một bước |
| `SPHERE_LIKE` | `DECLARE_ENTITIES` (tâm) → `CONSTRUCT_RADIUS` → `CONSTRUCT_CURVED_SURFACE` (gộp `CLOSE_SOLID`) | đường tròn lớn làm vật phụ khi lời giải cần |
| `SECTION` | `CONSTRUCT_CUTTING_OBJECT` → `CONSTRUCT_INTERSECTION` (từng cạnh) → `CLOSE_SECTION` | đã đúng hôm nay cho đa diện; đường cong hiện một bước |

Một bài cụ thể có thể có thêm bước (dựng phụ, giao điểm), nhưng không được thiếu
vai trò bắt buộc của lớp, và không được có bước vi phạm §2.2.

### 2.4 W12-H1/H2 nhìn qua mô hình

- Chóp tam giác (đáy vuông tại đỉnh `A`, `SA ⊥ đáy`): thiếu `CONSTRUCT_HEIGHT`
  (gộp với cạnh bên `SA`), `CONSTRUCT_LATERAL_BOUNDARY`, `CLOSE_SOLID` riêng.
- Lăng trụ tam giác: thiếu `CONSTRUCT_TRANSLATED_FACE`,
  `CONSTRUCT_LATERAL_BOUNDARY`, `CLOSE_SOLID` riêng.
- Hai họ chữ nhật đã đủ — bằng chuỗi viết tay của **chính họ ấy**. W14 thay cả
  bốn chuỗi bằng một kế hoạch theo lớp; hình hộp không được đổi hành vi nhìn thấy
  (hồi quy là tiêu chí S6).

## 3. Chính sách giả định và mặc định

### 3.1 Bốn lớp giá trị

| Lớp | Là gì | Ví dụ hôm nay |
|---|---|---|
| `GIVEN_VALUE` | đề nói, có bằng chứng nguồn | `AB = 5` đọc được ở câu đề |
| `DERIVED_VALUE` | tính từ GIVEN bằng phép dựng/đo chính xác | `BD` từ hai cạnh hình vuông |
| `MODEL_ASSUMPTION` | lựa chọn tự do mà đề **cho phép**: gốc, hướng trục, (với đáp số không đổi theo tỉ lệ) thang | đỉnh góc vuông đặt tại gốc (`LAYOUT_DERIVED`), `model_assumption` của tuyến LLM |
| `VISUAL_DEFAULT` | chỉ để trình bày | hướng camera, màu, cỡ miếng mặt phẳng, vị trí nhãn |

### 3.2 Luật

- **P1** Mọi số đi tới đáp số phải truy về `GIVEN_VALUE` qua `DERIVED_VALUE`
  (bao đóng phụ thuộc của witness), trừ các lựa chọn khung mà đáp số **chứng
  minh được** là không đổi theo.
- **P2** Một `MODEL_ASSUMPTION` chỉ được cố định những bậc tự do đề để ngỏ **và**
  đáp số bất biến theo (chuyển động cứng; thêm phép đồng dạng nếu đáp số là tỉ
  số/góc). Đáp số phụ thuộc vào nó ⇒ đó là một dữ kiện bị giấu ⇒ **từ chối**,
  trừ khi (a) đề cho phép lựa chọn ấy tường minh (*"chọn hệ trục…"*, *"giả sử cạnh
  bằng 1"*) hoặc (b) người dùng xác nhận — khi ấy nó hiện cho người học như một
  giả thiết, không như dữ kiện.
- **P3** Bố cục của compiler (`LAYOUT_DERIVED`) phải không phụ thuộc thang, hoặc
  tách khỏi chứng minh đo đạc: mọi độ dài của nó lấy từ FactGraph (đúng như hôm
  nay); compiler không bao giờ dùng `VISUAL_DEFAULT` cho đáp số.
- **P4** Mặc định tất định chỉ dùng cho trình bày; một mặc định đổi được đáp số
  là lỗi.
- **P5** Giả thiết còn lại (lựa chọn khung) vẫn được kể ra cho người học là giả
  thiết toạ độ, ghi rõ nó **không** đổi đáp số.
- **P6** Không quy tắc nào được dựa vào **chữ** của lời khai giả thiết; kiểm bằng
  cấu trúc/đại số.

### 3.3 Tiêu chí nghiệm thu

| Mã | Tiêu chí |
|---|---|
| AC1 | Phép dò `ASSUMPTION_CHANNEL_PROBE_79eb1e59` (lăng trụ thiếu *"AD = 5"*): cả biến thể `LAYOUT_DERIVED` lẫn `model_assumption` bị từ chối hoặc gắn nhãn giả thiết, **không** được phục vụ như dữ kiện. Nền đỏ có sẵn trong log. |
| AC2 | Không từ chối oan: sáu họ w12, các chương trình gold của corpus khoá luận và mọi bài mẫu offline vẫn được phục vụ, cùng đáp số. |
| AC3 | Phát hiện là cấu trúc/đại số, không theo chữ (P6). |
| AC4 | Tiêm lỗi: (i) gỡ phép kiểm ⇒ phép dò được phục vụ trở lại; (ii) đánh dấu một kích thước có GIVEN là "tự do" ⇒ thấy từ chối oan; (iii) phép nhiễu chỉ chạm tham số tự do, không bao giờ phá ràng buộc GIVEN. |
| AC5 | Mã từ chối ổn định, có thông điệp tiếng Việt cho người học, không gửi đi vòng sửa nếu viết lại chương trình không thêm được dữ kiện (cùng lý lẽ ba mã nguồn W12). |
| AC6 | `CACHE_VERSION` quyết định bằng bằng chứng (chiều *served → rejected* ⇒ gần như chắc phải bump). |
| AC7 | 0 lượt gọi model để đo. |

### 3.4 Cơ chế ứng viên — phải đo, chưa chọn

**Kiểm độ nhạy chính xác**: chạy lại chương trình (interpreter, offline, chính
xác) với mỗi tham số tự do của toạ độ giả thiết bị nhiễu (ví dụ nhân một thành
phần không bị ràng buộc với 2); witness đổi ⇒ tham số ấy quyết định đáp số. Chỉ
nhiễu tham số không bị bất biến nguồn nào ràng buộc. Phương án khác: **truy vết
chiều** — mỗi thành phần toạ độ giả thiết hoặc bằng 0/khung, hoặc gắn với một
GIVEN qua một bất biến nguồn, hoặc tự do; witness phụ thuộc thành phần tự do ⇒
từ chối. W14 đo cả hai trên AC1–AC2 rồi mới chọn.

### 3.5 Không được

Nới cổng grounding cho xanh; đoán ý định từ lời khai; xấp xỉ; gắn `GIVEN` cho
một con số đề không viết; chuyển lựa chọn khung thành lỗi (đó là `MODEL_ASSUMPTION`
hợp lệ).

## 4. Tổng quát hoá grounding nguồn

Đo bằng phép dò offline, 0 lượt gọi, chạy chính bộ đọc của sản phẩm:
[`diagnostics/SOURCE_GROUNDING_PHRASING_PROBE.json`](../evaluation/geometry/runs/w13-geometry-preregistration/diagnostics/SOURCE_GROUNDING_PHRASING_PROBE.json)
(25 hàng, script cạnh nó).

| Cách viết | Hôm nay (đo) | Phân loại | Quyết định |
|---|---|---|---|
| `AB = 5`, `AB bằng 5` | gắn đoạn `AB`; GIVEN hợp lệ | `CURRENT_SUPPORTED` | giữ |
| `độ dài đoạn AB bằng 5`, `cạnh AB có độ dài 5`, `đoạn AB có độ dài 5` | gắn đoạn | `CURRENT_SUPPORTED` | giữ |
| `AB dài 5 cm` | **không** gắn đoạn ⇒ số đứng một mình ⇒ khai `AC = 5` **lọt** | `SAFE_NORMALIZATION` — **lỗi đúng/sai** | W14 Track C: đọc `XY dài v [đơn vị]` như một độ dài có nhãn |
| `AA' = 5`, `AA′ = 5` | gắn đoạn | `CURRENT_SUPPORTED` | giữ |
| `AB = 2.5`, `AB = 2,5` | gắn đoạn, `5/2` | `CURRENT_SUPPORTED` | giữ (toạ độ vẫn cố ý không đọc dấu phẩy) |
| `AB = 5/2` | gắn đoạn | `CURRENT_SUPPORTED` | giữ |
| `AB = 2√3`, `AB = 3√2/2` | GIVEN đối chiếu bằng chữ + nhãn (đoạn sai bị bắt); bất biến độ dài **không** đọc căn | `SAFE_NORMALIZATION` | backlog: mở `do_dai_trong_de` sang `Radical`, so chính xác |
| `AB = 5 cm`, `AB = 5cm` | gắn đoạn, ghi đơn vị | `CURRENT_SUPPORTED` | giữ; tập đơn vị đóng, không đổi đơn vị |
| `AB = AC = 5` | chỉ `AC` được gắn; khai `AB = 5` bị từ chối `SOURCE_EVIDENCE_CONFLICT` | `UNSUPPORTED_FAIL_CLOSED` | backlog: chuỗi bằng nhau = cùng một giá trị cho mọi đoạn |
| `tứ diện đều ABCD cạnh 5`, `chóp tam giác đều … cạnh đáy bằng 5`, `lập phương cạnh 5` | số đứng một mình cho **một** cạnh đại diện | `FUTURE_PARSER` | tính đều phải là quan hệ trong hợp đồng, không phải phép so chữ |
| hộp: `AB = 3` ⇒ khai `CD = 3` là GIVEN | từ chối `SOURCE_EVIDENCE_CONFLICT` | `CURRENT_SUPPORTED_BY_DESIGN` | cạnh suy từ tô-pô phải **tính** ra (`DERIVED`), không khai GIVEN |

Luật chung: **không** so khớp mờ, không độ tương tự; mỗi cách viết mới là một cụm
đóng có test âm. Bảng này **không** tuyên bố hỗ trợ tiếng Việt đầy đủ: chưa có
corpus cách diễn đạt; mọi tuyên bố giới hạn trong các hàng đã đo.

## 5. Chính sách môi trường theo năng lực

Mỗi cổng đo ghi một bản ghi:

```
capability_required · how_measured · minimum_condition · environment_observed
· result (PASS | FAIL | SKIP | NOT_MEASURED) · reason
```

`SKIP` luôn có lý do và **không bao giờ** tính là `PASS`; thiếu năng lực ⇒
`NOT_MEASURED`, không phải `PASS`.

| Chiều | Năng lực yêu cầu | Đo bằng | Điều kiện tối thiểu | Đã quan sát (w12) | Ghi chú |
|---|---|---|---|---|---|
| GPU | WebGL dựng được ngữ cảnh | tạo context trong trang | software WebGL đủ cho cổng **đúng/sai** | ANGLE SwiftShader | số **hiệu năng** phải ghi GPU thật; chưa có ⇒ `BASELINE_NOT_ESTABLISHED` |
| Trình duyệt | Chromium nói DevTools protocol | `BrowserSession` | CDP trả lời trong timeout | Chrome 154.0.8037.59 headless=new | engine khác: `NOT_MEASURED`; đường dẫn cài là môi trường (F) |
| WebGL | Scene3D cần WebGL | cổng kiểm canvas có ngữ cảnh | có ngữ cảnh, hoặc hiện lời nhắn thay canvas | có | không WebGL ⇒ lời nhắn, không phải lỗi im lặng |
| OS | không nhánh sản phẩm theo OS | grep | 0 nhánh | Windows 11 | lệnh dev giả định Windows (F) |
| Hệ tệp / đường dẫn | chạy được từ đường dẫn có dấu cách; test không đọc đường dẫn cá nhân | `full-gate.node-test.mjs`; grep test | 0 đường dẫn ngoài kho trong suite mặc định | **1 vi phạm** (NA-05) | bằng chứng ngoài kho ⇒ marker opt-in |
| Viewport | bề rộng đo khai trong registry | `generic-tier-a-scenarios.json` | mỗi bề rộng khai báo đều đo | 1440×900 (DPR 1), 390×844 (DPR 2) | bề rộng khác: `NOT_MEASURED` |
| Mạng / offline | test 0 lượt gọi thật; cổng trình duyệt chặn `/api` | `conftest.py`, `test-setup.ts`; fixture đóng băng | 0 lượt gọi | 0 | lượt live cần `ALLOW_LIVE_AI` + ngân sách đăng ký trước |
| Python / Node | phiên bản tối thiểu | `RUN.json` | Python 3.12, Node 20+ (README) | Python 3.12.10, Node v24.13.0 | ghi phiên bản thật vào mỗi run |

## 6. Tiền đăng ký W14 — `W14_GENERIC_FORMATION_AND_ASSUMPTION_FOUNDATION`

**Run:** `docs/evaluation/geometry/runs/w14-generic-formation-assumption/` (theo
`RUN_NAMING.md`). **Nhánh:** nhánh hiện tại hoặc nhánh người dùng chỉ định;
không merge, không push.

### 6.1 Ba track

| Track | Giả thuyết | Thay đổi dự kiến |
|---|---|---|
| A — dựng hình theo lớp | Một kế hoạch theo lớp (`PYRAMID_LIKE`, `PRISM_LIKE`) dẫn từ vai trò tô-pô cho đủ vai trò §2.3 ở **mọi** họ đa diện của compiler, và — bằng việc tách `construct_solid` thành bước con có vai trò (đáy → biên bên → khép, theo khuôn `EXTEND` của thiết diện) — cả trên tuyến LLM | `geometry_compiler` (kế hoạch + phát câu lệnh), sự kiện trace/`scene3d` (vai trò, bước con), test đếm bước chuyển sang test độ phủ ngữ nghĩa (NA-15) |
| B — chính sách giả định | Kiểm bất biến đáp số (§3.4) phân biệt lựa chọn khung hợp lệ với kích thước bị giấu | `grounding_gate` / tầng hậu điều kiện; một mã từ chối mới; thông điệp người học |
| C — chuẩn hoá nguồn | Đọc `XY dài v` như độ dài có nhãn đóng lỗi chấp nhận nhầm, không đổi hàng nào khác của phép dò | `segment_relation` / `grounding_gate` (một thẩm quyền đọc độ dài) |

### 6.2 Tiêu chí thành công

| Mã | Tiêu chí |
|---|---|
| S1 | Mọi envelope họ chóp (tam giác, chữ nhật) có `CONSTRUCT_BASE`, `CONSTRUCT_HEIGHT` (gộp vai trò được phép), `CONSTRUCT_LATERAL_BOUNDARY`, `CLOSE_SOLID` là các bước quan sát được riêng, sinh bởi **cùng một** đường mã; quét AST: bộ lập kế hoạch không rẽ nhánh theo ID họ |
| S2 | Mọi họ lăng trụ có `CONSTRUCT_BASE`, `CONSTRUCT_TRANSLATED_FACE`, `CONSTRUCT_LATERAL_BOUNDARY`, `CLOSE_SOLID` |
| S3 | §2.2 V1–V9 kiểm bằng test trên trace/cảnh, không bằng số đếm; số bước chỉ còn là số **dẫn xuất** |
| S4 | Chương trình gold tuyến LLM có `construct_solid` (corpus khoá luận) nhận cùng bước con, kiểm offline |
| S5 | AC1–AC7 của §3.3 |
| S6 | Hồi quy: hộp chữ nhật, lập phương, chóp chữ nhật, thiết diện giữ hình dạng dựng đã duyệt tạm (`PROVISIONAL_PASS`), cùng đáp số; nét khuất ↔ oracle 0 bất đồng |
| S7 | Phép dò nguồn chạy lại: hàng `standalone_wrong_segment` từ **lọt** thành **bị từ chối**; mọi hàng khác giữ kết quả |
| S8 | T3 xanh trong worktree sạch; bộ trình duyệt 6 họ × 2 viewport chạy lại để người duyệt; trạng thái tối đa `READY_FOR_HUMAN_VISUAL_REVIEW` |

### 6.3 Tiêm lỗi bắt buộc

(1) Khôi phục chuỗi viết tay của họ chóp tam giác ⇒ S1 đỏ. (2) Bỏ một vai trò khỏi
kế hoạch `PRISM_LIKE` ⇒ S2 đỏ. (3) Thêm một bước không đổi hình ⇒ V1/V5 đỏ.
(4) Lời kể nhắc vật không có trong cảnh ⇒ V3 đỏ. (5) Gỡ kiểm giả định ⇒ AC1 đỏ.
(6) Gỡ cụm `XY dài v` ⇒ S7 đỏ. (7) Thêm một nhánh `if family_id ==` vào bộ lập kế
hoạch ⇒ guard AST đỏ.

### 6.4 Luật dừng

Dừng và báo, không tự mở rộng phạm vi, khi: kế hoạch dựng đòi đổi **bề mặt mô
hình** (thẻ văn phạm, prompt, lược đồ gửi đi); kiểm giả định từ chối oan bất kỳ
chương trình gold nào; tách `construct_solid` phá #31/#35 hoặc bằng chứng nét
khuất mà không sửa được trong phạm vi; cần lượt gọi model.

### 6.5 Đo và danh tính

`MEASUREMENT_CLASS = OFFLINE_DETERMINISTIC + BROWSER_FIXTURE` · `HELD_OUT_CLAIM = NO`
· 0 lượt gọi model · red test trước mỗi sửa sản phẩm · đóng băng lại candidate
sau **mỗi** commit chạm `backend/app` hoặc `frontend/src` rồi mới đo ·
`CACHE_VERSION` quyết định bằng bằng chứng (bốn chỗ cùng commit nếu bump) ·
không đổi `DEFAULT_MODE`.

### 6.6 Ngoài phạm vi W14

Dựng hình kiểu nón/cầu (cần đổi IR/sự kiện — D3), họ "đều" và phép kiểm khả thi
đặt toạ độ (D5), nhiều khối, nón cụt (D4), sửa prompt NA-52, mọi lượt live.

## 7. Backlog sửa chữa (thứ tự đề xuất, mỗi mục một wave hoặc một commit riêng)

1. **NA-05** test đòi đường dẫn `D:/tmp` — marker opt-in (nhỏ, không đụng sản phẩm).
2. **NA-52** prompt `geometry_program_generator.md` còn nói thiết diện xiên không
   diễn đạt được — wave đổi bề mặt mô hình (băm prompt, cache, đo lại).
3. **Khả thi đặt toạ độ** (NA-54) + **NA-42** (`hf()`): đo trước bằng một phép dò 0
   lượt gọi (tứ diện đều viết bằng toạ độ thập phân), rồi thêm mã từ chối ổn định;
   sau đó mới cân nhắc bố cục đồng dạng với hệ số thang `Radical` hoặc toạ độ
   ℚ(√d).
4. Ngữ nghĩa **"đều"** trong hợp đồng (quan hệ, FactGraph, checker) — sau mục 3.
5. **Dựng hình kiểu nón/cầu** — khi khối cong rời `foundation_only` hoặc người dùng
   quyết định (D3).
6. **Nhiều khối**: `occluders` cho bộ phân loại nét khuất (NA-48), hợp đồng nhiều
   tô-pô — theo lộ trình v1 (`wave_2`).
7. Vặt: NA-11 (bản sao `HUONG`), NA-23 (ghim `CACHE_VERSION`), NA-31 (bảng màu
   kiểu vào token), NA-40 (timeout CDP), hiệu chỉnh ngưỡng góc nhìn theo lớp hình
   (NA-10), đọc căn trong bất biến độ dài và chuỗi bằng nhau (§4).
8. Tài liệu: README §9–10, THESIS_ARCHITECTURE §A/§J, sửa phần còn lại của NA-53.

## 8. Quyết định cần người dùng

| Mã | Câu hỏi | Ảnh hưởng | Cần trước W14? |
|---|---|---|---|
| D1 | Thiết diện tô hổ phách ở chế độ trung tính (W12-D1): giữ hay đổi? | chỉ trình bày; W14 không đụng màu | không |
| D2 | Chính sách giả định: chỉ **từ chối + gắn nhãn** (đề xuất cho W14), hay thêm **xác nhận của người dùng** trên giao diện? | P2(b) cần UI | có |
| D3 | Dựng hình kiểu nón/cầu có vào W14 không? Đề xuất: **không** (đổi IR, sản phẩm cong còn `foundation_only`) | phạm vi W14 | có |
| D4 | Nón cụt / trụ cụt có vào phạm vi khoá luận không? | thêm một loại `KHOI_CONG` | không |
| D5 | Hình đều: phép kiểm khả thi + từ chối trước (đề xuất), hay đi thẳng tới toạ độ ℚ(√d)? | thay đổi kernel lớn | không |
