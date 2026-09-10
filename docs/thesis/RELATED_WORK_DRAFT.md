# RELATED_WORK_DRAFT — bản thảo mục *Công trình liên quan*

> **Vai trò của file này.** Bản thảo thay thế cho `THESIS_DRAFT.md §1.8`, viết
> lại sau lượt khảo sát 2026-09-10. Mục §1.8 hiện hành dựa trên **sáu** nguồn và
> kết bằng một phát biểu khoảng trống **rộng hơn bằng chứng cho phép**; bản này
> dựa trên **26** nguồn và thu hẹp phát biểu ấy lại.
>
> ⚠️ **Không hợp nhất vào `THESIS_DRAFT.md` trong wave này.** Bản thảo chính còn
> một nợ đã ghi (§D-4: thân Chương 4 đang là **hai thân rời nhau**); hợp nhất
> thuộc wave tích hợp bản thảo. Giữ bản gốc §1.8 làm bằng chứng lịch sử.
>
> Khoá trích dẫn: `docs/thesis/references_geometry_systems.bib`.
> Ma trận: `docs/research/LITERATURE_COMPARISON_MATRIX.md`.
> Giao thức + **sai lệch giao thức**: `docs/research/RELATED_WORK_SEARCH_PROTOCOL.md`.

---

## 1.8. Công trình liên quan

Mục này định vị đề tài trong sáu hướng đã có và kết bằng khoảng trống mà hệ
thống nhắm tới. Nó đặt **trước** phần cơ sở lý thuyết vì mỗi hướng dưới đây dẫn
tới một quyết định thiết kế cụ thể ở Chương 3.

**Về phương pháp khảo sát.** Phần này dựa trên một *structured scoping review*
thực hiện ngày 10/09/2026: 14 chuỗi truy vấn, 111 kết quả xem sơ bộ, 26 nguồn
được chọn (23 nguồn học thuật + 3 tài liệu chính thức của sản phẩm). Đây **không**
phải một systematic review theo PRISMA, và có một sai lệch phải khai: mọi truy
vấn đi qua một giao diện tìm kiếm web tổng quát chứ không qua giao diện native
của IEEE Xplore, ACM Digital Library hay SpringerLink. Vì vậy mọi phát biểu dưới
đây mang giới hạn *"trong phạm vi đã khảo sát"*. Ngoài ra, **12 trong 23 nguồn
học thuật là tiền ấn bản** — phần lớn công trình gần đề tài nhất mới xuất hiện
trong 12–18 tháng gần đây và chưa qua phản biện; chúng được trích với đúng nhãn
ấy.

### A. Công cụ hình học động và trực quan hoá 3D trong dạy học

Phần mềm hình học động là hướng lâu đời nhất và đã được đánh giá định lượng: một
phân tích tổng hợp 29 nghiên cứu trên 2 111 học sinh cho hiệu quả cao so với dạy
học truyền thống \cite{juandi2021geogebra}, và công cụ trực quan hoá không gian
được ghi nhận là hỗ trợ đúng chỗ người học thiếu hụt \cite{medina2024spatial}.
Cả hai kết quả phải trích kèm giới hạn do chính các tác giả khai: mẫu của nghiên
cứu thứ nhất chỉ gồm các nghiên cứu tại Indonesia 2010–2020, mẫu của nghiên cứu
thứ hai là sinh viên kỹ thuật — **không** phải học sinh THPT Việt Nam.

Ba sản phẩm tiêu biểu đã được đối chiếu bằng **tài liệu chính thức của nhà cung
cấp**: GeoGebra 3D Calculator \cite{geogebra2026apps}, Desmos 3D Calculator
\cite{desmos2023threed} và Cabri 3D \cite{cabrilog2026cabri3d}.

**Khác biệt về nhiệm vụ.** Cả ba nhận **thao tác dựng hình của người dùng** hoặc
**biểu thức**; không tài liệu chính thức nào mô tả khả năng nhận một đề bài bằng
ngôn ngữ tự nhiên rồi tự dựng hình. Toàn bộ công đoạn *đọc đề → dịch thành chuỗi
dựng* vẫn thuộc về người. Đề tài này tự động hoá đúng công đoạn đó, và đánh đổi
lại một thứ mà phần mềm hình học động có còn nó không có: **kéo liên tục** (§3.8).

Một sắc thái phải giữ để không bị bắt lỗi: GeoGebra *có* một sản phẩm đọc đề —
**Math Solver**, mô tả chính thức là *"chụp ảnh bài tập, nhận lời giải từng bước
kèm giải thích"* \cite{geogebra2026apps}. Nhưng đầu ra của nó là **lời giải đại
số**, không phải một cảnh 3D dựng được và kiểm chứng được.

### B. Năng lực và giới hạn suy luận toán của mô hình ngôn ngữ

Hai vế, và cả hai đều cần cho luận điểm. Vế thứ nhất: mô hình **phân rã tốt** bài
toán phát biểu bằng ngôn ngữ tự nhiên \cite{gao2023pal}. Vế thứ hai: chúng **sai
ở phần tính**, và kết quả kém bền trước những thay đổi nhỏ của đề — đổi giá trị
số làm kết quả dao động, thêm một mệnh đề thừa làm hiệu năng giảm tới 65 %
\cite{mirzadeh2025gsmsymbolic}.

Riêng ở miền hình học **không gian**, hai bộ đo gần đây cho thấy khoảng cách còn
lớn: SolidGeo với 3 113 bài K-12 và bài thi kết luận các mô hình đa phương thức
*còn cách xa mức người* \cite{wang2025solidgeo}, và DynaSolidGeo báo hiệu năng
sụt mạnh ở các tác vụ đòi trí tuệ không gian bậc cao như xoay và tưởng tượng hình
\cite{wu2025dynasolidgeo}.

**Hệ quả thiết kế.** Ba kết quả ấy hợp lại thành lập luận cho ranh giới R0: dùng
mô hình ở đúng vế thứ nhất, và **không** để nó chạm vào vế thứ hai — đặc biệt ở
miền 3D, nơi nó yếu nhất.

Một chi phí phải khai: ép mô hình viết ra một định dạng có cấu trúc **làm giảm**
năng lực suy luận của nó, và ràng buộc càng chặt thì giảm càng nhiều
\cite{tam2024format}. Thiết kế IR của đề tài vì thế là một đánh đổi có ý thức,
không phải một lựa chọn miễn phí.

### C. Mô hình ngôn ngữ sinh chương trình cho bộ giải

Đây là hướng gần đề tài nhất về **nguyên tắc**. *Program-aided Language Models*
\cite{gao2023pal} đề xuất đúng ý: mô hình đọc đề và sinh **chương trình** làm
bước suy luận trung gian, còn bước giải giao cho một runtime tất định. Hướng này
đã được đẩy xa trong hình học: GF-Reasoner huấn luyện với một bộ giải trong vòng
lặp và báo cải thiện tới 15 % \cite{yang2025gfreasoner}; AutoGPS hình thức hoá đa
phương thức rồi suy diễn, đạt 99 % mạch lạc logic theo bước
\cite{ping2025autogps}; SD-GPS coi bộ giải là *execution oracle* xuyên suốt cả
quá trình hình thức hoá lẫn suy diễn \cite{li2026sdgps}.

**Khác biệt.** Ở PAL, chương trình là **mã Python đa dụng** và runtime là trình
thông dịch — không có ràng buộc nào ngăn một chương trình gán thẳng đáp số. Ở ba
hệ hình học vừa kể, chương trình hình thức phục vụ mục tiêu **đáp số**. Ở đây,
chương trình là một **IR chuyên biệt cho hình học không gian**: có kiểu, có xuất
xứ, và cố ý bị giới hạn để mọi toán hạng hình học là **tên của vật đã dựng**
(§3.4.3) — nên mô hình không có chỗ nào để phát ra một toạ độ kết quả.

### D. Sinh sơ đồ hình học từ văn bản

Hướng này bùng lên trong hai năm gần đây và là **đối chứng gần nhất về nhiệm
vụ**. MagicGeo hình thức hoá mô tả thành bài toán tối ưu toạ độ rồi giải bằng bộ
giải hình thức, kèm benchmark 220 mô tả \cite{wang2025magicgeo}. GeoLoom tách
đôi bài toán thành *hình thức hoá logic* và *hiện thực hoá không gian*, với một
ngôn ngữ hình thức riêng — GeoLingua — mã hoá tường minh cả **phụ thuộc dựng
hình**, rồi giải toạ độ bằng tối ưu Monte Carlo \cite{wei2025geoloom}.
GeoBuildBench đi xa hơn một bước và biến chính bài toán ấy thành thước đo: cho
một đề bằng văn bản, tác tử phải sinh một chương trình DSL dựng ra hình thoả các
**ràng buộc kiểm được**; trên 489 đề sách giáo khoa tiếng Trung, các mô hình
mạnh nhất vẫn *"ảo giác cấu trúc, thiếu đối tượng và không thoả ràng buộc hình
học"* \cite{kim2026geobuildbench}. Ở nhánh sinh đề, SDE-GPG dùng bộ suy diễn ký
hiệu để sinh bài toán kiểm soát được về điểm kiến thức và độ khó
\cite{jiang2025sdegpg}, còn VeriGeo bổ sung một pipeline ba chặng kiểm — nhất
quán số, khả thi giải tích, nhất quán toàn cục — rồi **sửa hoặc loại bỏ**
\cite{duan2026verigeo}. Xu hướng ấy đã đủ rõ để hình thành thước đo riêng:
GGBench lấy chính việc **dựng hình** làm phép thử cho "suy luận sinh", với lập
luận rằng các bộ đo hiện có tách rời khả năng *hiểu* khỏi khả năng *tạo ra*
\cite{wei2025ggbench}.

**Ba khác biệt, và phải nói đủ cả ba.** Thứ nhất, **toàn bộ nhóm này làm hình học
phẳng**. Thứ hai, đầu ra là **một hình tĩnh** hoặc một đề bài, không phải một
cảnh tua được theo bước dựng. Thứ ba, toạ độ được tìm bằng **tối ưu số** — nên
không có khái niệm đáp số ở dạng chính xác như `3√6` hay `25π√5`.

⚠️ Điều **phải** thừa nhận: GeoBuildBench đã đặt đúng khuôn *"đề tự nhiên →
chương trình thực thi được → hình kiểm chứng được"*. Khoá luận này **không** tuyên
bố phát minh ra khuôn ấy; nó làm khuôn ấy ở **hình học không gian**, với một
thẩm quyền số khác, và cho một mục đích khác — trình bày cho người học thay vì
chấm điểm mô hình.

### E. Neural-symbolic, suy luận và phân tích hình học tự động

Ghép thành phần nơ-ron với thành phần ký hiệu là một hướng có tên và có khảo sát
\cite{gibaut2023neurosymbolic}; khoá luận **không** tự gán mình vào một ô taxonomy
nào của hướng này, vì bản khảo sát vừa dẫn là tiền ấn bản và chưa được đọc toàn
văn. Ở đỉnh của hướng, AlphaGeometry đạt mức gần huy chương vàng olympiad, giải
25 trong 30 bài, bằng cách để một mô hình ngôn ngữ dẫn đường cho engine suy diễn
ký hiệu \cite{trinh2024alphageometry}.

Hai công trình 2026 chạm tới hình học **không gian** và phải được nêu tên riêng,
vì chúng là chỗ phát biểu khoảng trống của đề tài dễ bị bác nhất:

**Geoparsing** \cite{wang2026geoparsing} xây một **ngôn ngữ hình thức hợp nhất
cho cả hình phẳng và hình không gian** — trong tập đã khảo sát, đây là công trình
duy nhất làm điều đó. Nhưng nó chạy **chiều ngược**: từ **hình vẽ** ra ngôn ngữ
hình thức. Đề tài này đi chiều *đề bài → chương trình → hình*.

**Draw2Think** \cite{hu2026draw2think} chuyển việc giải hình học thành tương tác
với bộ máy ràng buộc của GeoGebra qua vòng *Propose–Draw–Verify*, khai phủ cả
hình phẳng lẫn hình không gian và báo cải thiện 16,4 % ở hình không gian. Vậy
*"dựng hình 3D từ đề bài"* **không còn** là chỗ trống. Khác biệt còn lại nằm ở
**mục đích** và **thẩm quyền số**: Draw2Think dựng hình để **giải đúng hơn**, với
thẩm quyền số thuộc về một bộ máy có sẵn; đề tài này dựng hình để **người học xem
được quá trình**, và bắt mọi đại lượng đi qua một nhân số học chính xác riêng có
oracle độc lập đối chiếu.

### F. Đối chứng ranh giới: sinh vật thể 3D từ văn bản

Để định vị đúng, cần một đối chứng ở phía *"sinh 3D từ văn bản nhưng không phải
hình học giáo dục"*. Text2CAD sinh **mô hình CAD tham số** dạng chuỗi lệnh từ chỉ
dẫn bằng văn bản, huấn luyện trên ~170 K mô hình \cite{khan2024text2cad}. Nó có
đúng thứ AlgoSim có — một biểu diễn trung gian tuần tự, chạy lại được — nhưng
đánh giá bằng **chỉ số thị giác, tham số và hình học**, không bằng kiểm chứng
hình thức, và mục tiêu là thiết kế công nghiệp chứ không phải dạy học.

Cần thêm một điểm neo lý thuyết cho quyết định số học: vị ngữ hình học cài bằng
số dấu chấm động có thể cho kết quả **sai hoặc không nhất quán**
\cite{shewchuk1997predicates}. Đây là bằng chứng rằng *độ chắc chắn của vị ngữ* là
vấn đề ngành đã nhận diện từ lâu — không phải bằng chứng rằng mọi engine dùng
`float` đều không dùng được.

Bối cảnh chung của cả sáu hướng được hệ thống hoá trong khảo sát mới nhất về học
sâu cho giải toán hình học \cite{ma2026dl4gps}.

### Khoảng trống mà đề tài nhắm tới

Gộp sáu hướng lại, khoảng trống **không** nằm ở bất kỳ điều kiện đơn lẻ nào —
mỗi điều kiện đều đã có người làm. Nó nằm ở **giao**:

> **đầu vào là đề hình học KHÔNG GIAN bằng tiếng Việt** (khác A, khác D) ·
> **biểu diễn trung gian có KIỂU, mọi toán hạng hình học là tên của vật đã dựng**
> (khác C) · **mọi đại lượng tính bằng SỐ HỌC CHÍNH XÁC trên ℚ mở rộng bởi căn
> thức và π, không dùng `float` trong miền hình học** (khác D, khác F) ·
> **đầu ra là cảnh 3D TUA ĐƯỢC giữ song ánh giữa khung hình và bước dựng** (khác
> mọi hướng) · và **TỪ CHỐI CÓ CẤU TRÚC hướng người học** — nêu giai đoạn dừng,
> loại thất bại và mã lỗi — khi không kiểm chứng được (khác mọi hướng; VeriGeo
> có *sửa-hoặc-loại* nhưng ở bên trong pipeline, không đưa ra tới người học).

Kết quả khảo sát cho thấy còn thiếu một hệ đồng thời thoả năm điều kiện ấy. Điều
kiện thứ ba và thứ năm là hai điều kiện ít hiển nhiên nhất, và là chỗ khoá luận
đóng góp nhiều nhất — Chương 3 §3.4.3 và Chương 5 §5.2 nói rõ.

⚠️ **Ba giới hạn của chính phát biểu này**, ghi ngay tại đây thay vì ở cuối
chương: (i) nó là phát biểu về **phạm vi đã khảo sát**, với sai lệch giao thức đã
nêu ở đầu mục; (ii) phần lớn công trình gần nhất là **tiền ấn bản**, nên bức
tranh có thể đổi trong vài tháng; (iii) bằng chứng nội bộ chống đỡ vế *"hệ làm
được"* của phát biểu này là **một lượt đo trên 9 ca, n = 1 mỗi họ, không
held-out** — nó không chống đỡ được bất kỳ vế nào về độ ổn định.
