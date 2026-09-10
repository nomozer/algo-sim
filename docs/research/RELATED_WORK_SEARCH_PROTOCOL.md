# RELATED_WORK_SEARCH_PROTOCOL — giao thức khảo sát tài liệu

> **Loại khảo sát: `STRUCTURED_SCOPING_REVIEW`.** Không gọi là *systematic
> review*, và lý do được ghi ngay dưới đây chứ không giấu ở cuối. Nguồn máy đọc:
> `docs/evaluation/geometry/research-gap-formalization/SEARCH_LOG.json`.
>
> Ngày khảo sát **2026-09-10**, trên HEAD `df8ad21`.
> `APPLICATION_LLM_CALLS = 0` — tra cứu web không đi qua `backend/app`, không
> dùng `GEMINI_API_KEY`, không sinh Semantic Program nào.

## 1. Vì sao KHÔNG được gọi là systematic review

Ba điều kiện của PRISMA đều thiếu, và mỗi cái thiếu một cách cụ thể:

| điều kiện PRISMA | trạng thái ở đây |
|---|---|
| giao thức đăng ký **trước** khi tìm | ❌ giao thức viết **cùng lúc** với lượt tìm |
| hai người sàng lọc độc lập, đo độ đồng thuận | ❌ một tác nhân sàng lọc |
| PRISMA flow diagram kiểm toán được | ❌ có sổ truy vấn (`SEARCH_LOG.json`) nhưng không có flow diagram chuẩn |

Nên mọi phát biểu rút ra ở đây là **phát biểu về phạm vi đã đọc**, không phải
phát biểu về toàn bộ tài liệu của lĩnh vực.

## 2. ⚠️ SAI LỆCH GIAO THỨC — phải khai khi trích

Wave yêu cầu tìm tại Google Scholar · IEEE Xplore · ACM DL · SpringerLink hoặc
ScienceDirect · arXiv · trang chính thức của công cụ.

**Thực tế:** mọi truy vấn đi qua **một** giao diện tìm kiếm web tổng quát. Giao
diện ấy *có* bắt kết quả từ arXiv, ACL Anthology, NeurIPS Proceedings, OpenReview
và trang nhà cung cấp — nhưng đó **không** phải truy vấn native trong từng cơ sở
dữ liệu.

| | |
|---|---|
| chạm tới được qua web tổng quát | arXiv · ACL Anthology · NeurIPS Proceedings · OpenReview · trang chính thức của GeoGebra, Desmos, Cabrilog |
| **KHÔNG truy vấn native** | Google Scholar · IEEE Xplore · ACM Digital Library · SpringerLink · ScienceDirect |

**Hệ quả:** độ phủ cho mảng IEEE/ACM/Springer **chưa** tuyên bố được. Mọi phát
biểu khoảng trống phải mang giới từ *"trong phạm vi đã khảo sát"*, và **không**
được dùng *"duy nhất"* hay *"lần đầu tiên"*. Cách đóng nợ: chạy lại đúng 14 chuỗi
truy vấn trong giao diện native của ba cơ sở dữ liệu ấy và ghi lại số kết quả —
việc này **phải làm trước khi nộp bài báo**, không bắt buộc cho khoá luận.

## 3. Phạm vi

| | |
|---|---|
| khung thời gian chính | **2018–2026** |
| ngoại lệ được phép | tài liệu nền cũ hơn khi cần giải thích dynamic geometry software hoặc kiến trúc symbolic geometry — dùng đúng **một** lần (Shewchuk 1997, độ chắc chắn của vị ngữ hình học) |
| ngôn ngữ truy vấn | 13 chuỗi tiếng Anh · 1 chuỗi tiếng Việt |

## 4. Sổ truy vấn — tóm tắt

Chi tiết từng dòng ở `SEARCH_LOG.json`. Tổng hợp:

| | |
|---|---|
| truy vấn đã chạy | **14** |
| kết quả xem sơ bộ | **111** |
| đọc tiêu đề/tóm tắt | **111** |
| mở trang công bố (tóm tắt hoặc toàn văn) | **24 lượt**, thành công **19**, hỏng **5** |
| nguồn được chọn | **26** |
| nguồn bị loại | **8** |
| nguồn hiện ra nhưng **chưa thẩm định** | **7** |

Năm lượt mở hỏng đều là trang công cụ, đã ghi mã lỗi trong sổ: `help.geogebra.org`
HTTP 403 · `cabri.com/en/cabri-3d/` HTTP 404 · `geogebra.github.io/docs` HTTP 404 ·
`geogebra.org/3d` không có văn bản mô tả · Google Play nội dung bị cắt. Hai trang
chính thức thay thế đã dùng: `geogebra.org/download` và
`cabri.com/en/instructor/cabri-3d/`.

### Năm chuỗi truy vấn của wave CHƯA chạy

`text to geometry diagram generation` · `verified geometry diagram generation` ·
`constraint-based geometry diagram` · `Vietnamese geometry problem visualization` ·
`sinh hình học 3D từ đề bài`.

Lý do: chúng phủ chung chủ đề với Q01–Q06 và Q14, và bốn truy vấn cuối không trả
về hệ thống mới nào ngoài tập đã chọn — **bão hoà**. Nhưng bão hoà là một *nhận
định*, không phải một phép đo; ghi ra đây để lần sau chạy bổ sung.

## 5. Tiêu chí chọn và loại

**Chọn** nếu thuộc ít nhất một nhóm: N1 dynamic geometry / phần mềm toán 3D ·
N2 sinh sơ đồ hình học từ văn bản · N3 LLM giải bài hình bằng chương trình hình
thức · N4 neuro-symbolic geometry · N5 kiểm chứng ràng buộc hình học · N6 mô
phỏng 3D phục vụ giáo dục · N7 sinh lời giải/hình minh hoạ từng bước · N8
text-to-3D liên quan tới tính chính xác hình học.

**Loại**: bài quảng cáo không mô tả kỹ thuật · bản tổng hợp không truy được nguồn
gốc · text-to-3D thuần thị giác (trừ khi dùng làm đối chứng) · tài liệu không đủ
thông tin xác định chức năng.

Tám mục bị loại và lý do từng mục: `EXCLUDED_SOURCES.json`. Đáng chú ý hai mục:

- **`G-reasoner` (arXiv:2509.24276)** — tên gần giống `GF-Reasoner` nhưng là suy
  luận trên đồ thị tri thức, khác hẳn miền. Ghi lại để lần sau không ai nhầm.
- **`MathKernel`** (dự án mã nguồn mở) — ý tưởng gần (typed MathIR, nhãn tin cậy,
  từ chối khi đầu vào xấp xỉ) nhưng **không có bài báo phương pháp**, không đánh
  giá độc lập. Không điền được vào ma trận.

## 6. Ưu tiên loại nguồn

1. bài báo có phản biện → 2. hội nghị/tạp chí chính thức → 3. preprint có đủ
phương pháp và thực nghiệm → 4. tài liệu chính thức của sản phẩm (chỉ để xác nhận
tính năng sản phẩm).

**Preprint không được trình bày như bài đã phản biện.** Trong 26 nguồn:

| loại | số |
|---|:-:|
| tạp chí bình duyệt | 4 |
| hội nghị bình duyệt (đã in kỷ yếu) | 6 |
| hội nghị bình duyệt (**đã nhận**, bản arXiv) | 1 |
| **preprint** | **12** |
| tài liệu chính thức của sản phẩm | 3 |
| **tổng** | **26** |

`PRIMARY_ACADEMIC_SOURCES = 23` · `OFFICIAL_TOOL_SOURCES = 3` ·
`COMPARABLE_ENTRIES = 19` (+1 hàng AlgoSim = 20 hàng ma trận).

⚠️ **Mười hai trên hai mươi ba nguồn học thuật là preprint.** Đó là hình dạng
thật của mảng này: phần lớn công trình gần đề tài nhất mới ra trong 12–18 tháng
và chưa kịp qua phản biện. Phải khai khi viết tổng quan, và không được xếp chúng
ngang hàng với Nature/ACL/NeurIPS.

## 7. Mức xác minh — không ô nào suy từ im lặng

| mức | nghĩa |
|---|---|
| `FULL_TEXT_READ` | đã đọc toàn văn |
| `ABSTRACT_PAGE_READ` | đã mở trang công bố chính thức và đọc tóm tắt |
| `REPO_PREVERIFIED` | đã xác minh ở wave trước, ghi ở `docs/THESIS_REFERENCES.md` |
| `LISTING_ONLY` | chỉ xác minh ở trang liệt kê |

**Luật cứng của ma trận:** không ô nào được ghi `No` chỉ vì tóm tắt không nhắc
tới. Trường hợp ấy ghi `NR` (không công bố) hoặc `UNCLEAR`. Ở lượt này **không
nguồn nào** đạt `FULL_TEXT_READ` — mọi ô đều rút từ tóm tắt hoặc mô tả chính
thức, nên số ô `NR`/`UNCLEAR` trong ma trận là **cao một cách có chủ đích**.

## 8. Một cái bẫy đã bắt được

Truy vấn tiếng Việt (Q08) trả về một bản tóm tắt tự động kết luận rằng GeoGebra
và Cabri *"cung cấp khả năng mô phỏng và sinh tự động các hình học 3D từ các đề
bài"*. Câu ấy **sai**, và nó sai theo đúng hướng có lợi cho việc viết ẩu: nếu tin
nó thì khoảng trống của đề tài biến mất.

Đã bác bằng hai trang chính thức (Q10, Q11): mô tả của nhà cung cấp chỉ nói
*"Graph functions and perform calculations in 3D"* và *"explore geometric
concepts and constructions in a dynamic environment"*; không mô tả nào nhận đề
bài bằng văn bản tự nhiên. Đây là lý do §7 bắt mọi ô khẳng định phải trỏ về
**bản gốc**, không về bản tóm tắt của bên thứ ba.
