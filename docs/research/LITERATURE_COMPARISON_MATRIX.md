# LITERATURE_COMPARISON_MATRIX — ma trận so sánh

> **Luật của file này.** Mỗi ô khẳng định phải trỏ về **bản gốc đã mở**, không về
> bản tóm tắt của bên thứ ba. Ô không có bằng chứng ghi một trong ba nhãn:
>
> | nhãn | nghĩa |
> |---|---|
> | `NR` | **NOT REPORTED** — bản đã đọc không nói tới |
> | `NA` | **NOT APPLICABLE** — trục này không áp cho công trình ấy |
> | `UNCLEAR` | có nhắc nhưng chưa đủ bằng chứng để phân loại |
>
> ⚠️ **Không suy `Không` từ im lặng.** Ở lượt khảo sát này **không nguồn nào**
> được đọc toàn văn (`FULL_TEXT_READ = 0`) — mọi ô rút từ tóm tắt trên trang công
> bố chính thức hoặc mô tả sản phẩm chính thức. Vì vậy số ô `NR` **cao có chủ
> đích**; đó là mức xác minh thật, không phải sự cẩu thả.
>
> Nguồn máy đọc: `docs/evaluation/geometry/research-gap-formalization/SOURCE_METADATA.json`.
> Giao thức và **sai lệch giao thức**: `RELATED_WORK_SEARCH_PROTOCOL.md` §2.

`COMPARABLE_ENTRIES = 19` công trình/công cụ + 1 hàng **AlgoSim** = **20 hàng**.

---

## Bảng 1 — Danh tính, mục tiêu, đầu vào

| # | Công trình/công cụ (năm) | Loại nguồn | Mục tiêu | Đầu vào | Ngôn ngữ Việt | 2D/3D | Tự động từ đề bài |
|---|---|---|---|---|---|:-:|---|
| 1 | **AlgoSim** (2026) | khoá luận, chưa công bố | **mô phỏng** 3D chạy được + đo | đề tiếng Việt, văn bản tự nhiên | **Có** | **3D** | **Có** |
| 2 | MagicGeo (2025) | preprint | dựng hình (sinh sơ đồ) | mô tả hình bằng văn bản | `NR` | 2D | Có |
| 3 | GeoLoom (2025) | preprint | dựng hình (sinh sơ đồ) | văn bản tự nhiên | `NR` | 2D | Có |
| 4 | GeoBuildBench (2026) | preprint | **đo** năng lực dựng hình thực thi được | đề sách giáo khoa **tiếng Trung** | Không (tiếng Trung) | 2D | Có (là thứ được đo) |
| 5 | Draw2Think (2026) | preprint | giải bài qua tương tác constraint engine | đề + hình | `NR` | **phẳng và không gian** | Có |
| 6 | GF-Reasoner (2025) | preprint | giải bài | đề + hình (VLM) | `NR` | 2D | Có |
| 7 | SDE-GPG (2025) | **ACL 2025 Industry** | **sinh đề** + hình kèm | điểm kiến thức + độ khó | `NR` | `UNCLEAR` | NA (sinh đề, không nhận đề) |
| 8 | SD-GPS (2026) | preprint | giải bài + đề xuất bổ đề | đề + hình | `NR` | `UNCLEAR` | Có |
| 9 | VeriGeo (2026) | preprint | **sinh đề** có kiểm chứng | ràng buộc do người dùng đặt | `NR` | `UNCLEAR` | NA |
| 10 | SolidGeo (2025) | preprint | **đo** suy luận không gian | đề + hình | `NR` | **3D** | NA (benchmark trả lời) |
| 11 | DynaSolidGeo (2025) | preprint | **đo** suy luận không gian, sinh động | đề + hình | `NR` | **3D** | NA |
| 12 | Geoparsing (2026) | **ACL 2026 (đã nhận)** | **phân tích hình** → ngôn ngữ hình thức | **hình vẽ** | `NR` | **phẳng và không gian** | NA (chiều ngược) |
| 13 | AutoGPS (2025) | preprint | giải bài | đề + hình | `NR` | `UNCLEAR` | Có |
| 14 | GGBench (2025) | preprint | **đo** suy luận sinh (dựng hình) | đề | `NR` | `UNCLEAR` | NA |
| 15 | AlphaGeometry (2024) | **Nature** | **chứng minh** định lí | đề hình học olympiad hình thức hoá | Không | 2D phẳng | Một phần |
| 16 | PAL (2023) | **ICML** | giải bài toán chữ nói chung | đề bằng ngôn ngữ tự nhiên | `NR` | NA | Có |
| 17 | Text2CAD (2024) | **NeurIPS** | dựng **mô hình CAD** | chỉ dẫn thiết kế bằng văn bản | `NR` | **3D** | Có |
| 18 | GeoGebra 3D Calculator | tài liệu chính thức | dựng hình / vẽ đồ thị **do người dùng thao tác** | công cụ, lệnh, biểu thức | **Có** (giao diện) | **3D** | **Không** |
| 19 | Desmos 3D Calculator | tài liệu chính thức | vẽ đồ thị 3D | biểu thức, phương trình | `NR` | **3D** | **Không** |
| 20 | Cabri 3D | tài liệu chính thức | dựng hình không gian động | thao tác dựng của người dùng | `NR` | **3D** | **Không** |

> **Hàng 18 — một sắc thái phải giữ.** GeoGebra *có* một sản phẩm đọc đề: **Math
> Solver**, mô tả chính thức *"Take a photo of your math homework. Get
> step-by-step solutions with explanations"*. Nhưng đầu ra của nó là **lời giải
> từng bước bằng đại số**, không phải một cảnh 3D dựng được và kiểm chứng được.
> Không được lấy sự tồn tại của Math Solver để nói GeoGebra "đã làm việc AlgoSim
> làm", cũng không được giấu nó đi.

---

## Bảng 2 — Biểu diễn trung gian và kiểm chứng

| # | Công trình | Biểu diễn trung gian | Chương trình thực thi | Kiểm tra kiểu | Kiểm chứng hình học | Số học chính xác | Kiểm tra nguồn dữ kiện |
|---|---|---|:-:|:-:|---|---|:-:|
| 1 | **AlgoSim** | **Semantic Program** — IR có kiểu, toán hạng là **TÊN** vật đã dựng, có `producer`/`depends` | **Có** | **Có** (lược đồ Pydantic + `ir_static_check`) | **Có** — `GEOMETRY_CHECKERS` + hậu điều kiện, oracle cài **độc lập** | **Có** — ℚ + căn + π, **không `float`** trong miền hình học | **Có** — `grounding_gate` + bất biến nguồn |
| 2 | MagicGeo | bài toán **tối ưu toạ độ** + ngôn ngữ hình thức cho solver | Có (sinh mã TikZ) | `NR` | **Có** — solver hình thức bảo đảm tính đúng hình học | **Không** — tối ưu toạ độ (số) | Không |
| 3 | GeoLoom | **GeoLingua** — ngôn ngữ hình thức mã hoá primitive, ràng buộc, **phụ thuộc dựng hình** | Có | `NR` | **Có** — độ đo lệch cấu trúc theo ràng buộc | **Không** — tối ưu **Monte Carlo** | Không |
| 4 | GeoBuildBench | **DSL** dựng hình | **Có** | `NR` | **Có** — ràng buộc nêu tường minh, kiểm được | `NR` | Không |
| 5 | Draw2Think | lệnh cho **constraint engine của GeoGebra** | **Có** | `NR` | **Có** — engine cưỡng chế quan hệ, "algebraic guarantees" | `UNCLEAR` — phụ thuộc engine GeoGebra, bản đã đọc không nói | Không |
| 6 | GF-Reasoner | mã **chạy được bằng solver**, xen kẽ suy luận tự nhiên | **Có** | `NR` | **Có** — solver thực thi và trả phản hồi kiểm chứng | `NR` | Không |
| 7 | SDE-GPG | định nghĩa mở rộng cho **symbolic deduction engine** | Có | `NR` | **Có** — suy diễn ký hiệu + bộ lọc bài không đạt | `NR` | NA |
| 8 | SD-GPS | phát biểu hình thức cho solver | **Có** | `NR` | **Có** — solver là *execution oracle*; bổ đề lọc qua kiểm chứng ký hiệu | `NR` | NA |
| 9 | VeriGeo | vết suy luận **thực thi được** | **Có** | `NR` | **Có** — ba chặng: nhất quán số · khả thi giải tích · nhất quán toàn cục | `UNCLEAR` — bản đã đọc **không** nói cách biểu diễn số | NA |
| 10 | SolidGeo | NA | Không | NA | NA (đo đáp số) | NA | NA |
| 11 | DynaSolidGeo | NA | Không | NA | NA | NA | NA |
| 12 | Geoparsing | **ngôn ngữ hình thức hợp nhất phẳng + không gian** | Không (parsing) | `NR` | NA | `NR` | NA |
| 13 | AutoGPS | biểu diễn hình thức đa phương thức, siêu đồ thị | Có | `NR` | **Có** — suy diễn ký hiệu | `NR` | NA |
| 14 | GGBench | NA (benchmark) | NA | NA | `NR` | `NR` | NA |
| 15 | AlphaGeometry | ngôn ngữ hình thức của engine suy diễn | Có | `NR` | **Có** — chứng minh hình thức | `NR` | NA |
| 16 | PAL | **mã Python đa dụng** | **Có** | Không (Python động) | Không | Không | Không |
| 17 | Text2CAD | chuỗi lệnh **CAD tham số** | Có | `NR` | **Không hình thức** — đo bằng chỉ số thị giác/tham số/hình học | `NR` | NA |
| 18 | GeoGebra 3D | NA | NA | NA | dựng theo ràng buộc do người dùng đặt | `NR` | NA |
| 19 | Desmos 3D | NA | NA | NA | NA (vẽ đồ thị) | `NR` | NA |
| 20 | Cabri 3D | NA | NA | NA | dựng theo ràng buộc do người dùng đặt | `NR` | NA |

---

## Bảng 3 — Đầu ra, tương tác, từ chối

| # | Công trình | Trace dựng hình | Tương tác 3D | Nét thấy–nét khuất động | Từ chối khi không kiểm chứng được |
|---|---|:-:|:-:|---|---|
| 1 | **AlgoSim** | **Có** — song ánh `khung k ⇔ bước k` (bất biến #31) | **Có** — chọn vật, tách khối, tua bước | **Có** — lớp chiều sâu + vẽ hai lượt, oracle che khuất độc lập | **Có** — từ chối có cấu trúc: giai đoạn dừng · loại thất bại · **mã lỗi** · thông điệp tiếng Việt |
| 2 | MagicGeo | Không (hình tĩnh) | Không | NA | **Một phần** — không giải được thì **quay lại** bước hình thức hoá |
| 3 | GeoLoom | `NR` — ngôn ngữ có mã hoá phụ thuộc dựng hình, nhưng bản đã đọc không nói có phát lại | Không | NA | `NR` |
| 4 | GeoBuildBench | `NR` | **Một phần** — "interactive construction task", vòng lặp có trần | NA | NA (là benchmark; **đo** tỉ lệ không thoả ràng buộc) |
| 5 | Draw2Think | **Một phần** — vòng Propose-Draw-Verify để lại vết tương tác | `UNCLEAR` — canvas GeoGebra, bản đã đọc không mô tả tương tác của người học | `NR` | **Một phần** — verify rồi sửa; không có từ chối hướng người học |
| 6 | GF-Reasoner | Không | Không | NA | `NR` |
| 7 | SDE-GPG | Không | Không | NA | **Một phần** — **lọc bỏ** bài không đạt |
| 8 | SD-GPS | Không | Không | NA | **Một phần** — lọc bổ đề qua kiểm chứng ký hiệu |
| 9 | VeriGeo | **Có** — "executable reasoning traces" | Không | NA | **Có** — *repair or reject* sau ba chặng kiểm |
| 10 | SolidGeo | NA | Không | NA | NA |
| 11 | DynaSolidGeo | NA | Không | NA | NA |
| 12 | Geoparsing | NA | Không | NA | NA |
| 13 | AutoGPS | **Một phần** — lời giải suy diễn đọc được, 99% mạch lạc theo bước | Không | NA | `NR` |
| 14 | GGBench | NA | NA | NA | NA |
| 15 | AlphaGeometry | **Có** — chứng minh đọc được | Không | NA | NA (không chứng minh được thì không ra chứng minh) |
| 16 | PAL | Không | Không | NA | Không |
| 17 | Text2CAD | **Có** — chuỗi lệnh CAD tuần tự | `NR` | NA | Không |
| 18 | GeoGebra 3D | NA (người dùng tự dựng) | **Có** — kéo–thả liên tục, AR | `NR` | NA |
| 19 | Desmos 3D | NA | **Có** — xoay, phóng, slider | `NR` | NA |
| 20 | Cabri 3D | NA | **Có** — di chuyển điểm nhìn, nhiều hình chiếu | `NR` | NA |

> ⚠️ **Cột "nét thấy–nét khuất động" trả về `NR` ở gần như mọi hàng.** Đó **không**
> phải bằng chứng rằng các công cụ ấy không làm được — Cabri 3D chẳng hạn hầu như
> chắc chắn có xử lý che khuất. Nó chỉ nói: tài liệu đã đọc không phát biểu về
> trục này. Không được đọc cột này thành lợi thế của AlgoSim.

---

## Bảng 4 — Kết quả đánh giá, giới hạn, khác biệt với AlgoSim

| # | Công trình | Kết quả đánh giá (dataset · số ca · metric) | Giới hạn **theo chính tác giả** | Khác biệt với AlgoSim |
|---|---|---|---|---|
| 1 | **AlgoSim** | bộ 9 ca đóng băng (7 dương + 2 âm), **1 lượt**: servable 7/7 · first-attempt 6/7 · đáp số chính xác 12/12 · ca âm fail-closed 2/2 · silent-wrong 0 · 19 lượt gọi / 97 869 token | **không held-out** · **n = 1 mỗi họ** · `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` · `PRODUCT_PROMOTION_ELIGIBLE = NO` · bộ đo đã sai một lần trong chính lượt ấy | — |
| 2 | MagicGeo | **MagicGeoBench**, 220 mô tả hình; vượt các phương pháp hiện có ở cả định tính và định lượng | `NR` | 2D · hình **tĩnh** · không tua bước · không từ chối hướng người học · toạ độ giải bằng **tối ưu số** |
| 3 | GeoLoom | **GeoNF**; vượt baseline SOTA ở cả hai loại chỉ số; nhanh, hợp thời gian thực | `NR` | 2D · hình tĩnh · **Monte Carlo** ⇒ không có đáp số dạng chính xác |
| 4 | GeoBuildBench | **489 đề tiếng Trung**; mô hình *"structural hallucinations, missing objects, failures to satisfy geometric constraints"*, kém tự sửa | tự khai là benchmark hình học **phẳng** | **Cùng bài toán, khác chiều không gian và khác vai**: nó **đo**, AlgoSim **phục vụ**; 2D vs 3D |
| 5 | Draw2Think | GeoGoal: 95,9% predicate-level · 84,0% problem-level; +4,1% phẳng, **+16,4% hình không gian**; GenExam-math 68,2% strict | `NR` | **Đối chứng mạnh nhất.** Mục tiêu là **độ chính xác giải bài**, không phải mô phỏng cho người học; thẩm quyền số là engine GeoGebra chứ không phải nhân số học chính xác riêng; không có từ chối có cấu trúc |
| 6 | GF-Reasoner | +15% trên benchmark GPS chuẩn; RL tăng Pass@1 26%; vết ngắn hơn | `NR` | đầu ra là **đáp số**, không phải cảnh 3D |
| 7 | SDE-GPG | `NR` (bản đã đọc không nêu số) | `NR` | **sinh đề**, không phục vụ đề có sẵn |
| 8 | SD-GPS | vượt MLLM/neural/neuro-symbolic trên Geometry3K và PGPS9K | `NR` | đầu ra là **lời giải/định lí** |
| 9 | VeriGeo | GeoQA — "best reported performance" sau SFT trên đề tổng hợp | `NR` | **sinh đề**; gần AlgoSim nhất ở trục *kiểm rồi mới nhận*, xa nhất ở trục *mô phỏng* |
| 10 | SolidGeo | **3 113 bài** K-12 và thi; MLLM còn **cách xa** mức người | tự khai khoảng cách so với người | benchmark **trả lời**, không dựng hình |
| 11 | DynaSolidGeo | 503 câu gốc sinh nhiều biến thể; sụt mạnh ở tình huống động, kém ở xoay/tưởng tượng không gian | tự khai | như trên |
| 12 | Geoparsing | SOTA parsing; mô tả hình thức làm "giàn giáo nhận thức" cho suy luận sau đó | `NR` | **chiều ngược**: hình → ngôn ngữ hình thức. AlgoSim đi đề → chương trình → hình |
| 13 | AutoGPS | SOTA trên các bộ chuẩn; **99%** mạch lạc logic theo bước (đánh giá bởi người) | `NR` | đầu ra là lời giải |
| 14 | GGBench | nêu khoảng trống đánh giá: hiểu và sinh bị đo tách rời | `NR` | benchmark |
| 15 | AlphaGeometry | 25/30 bài olympiad, gần mức huy chương vàng | miền olympiad phẳng | **hình phẳng · chứng minh**, không phải mô phỏng không gian |
| 16 | PAL | vượt CoT trên nhiều bộ toán chữ | `NR` | Python **đa dụng** — không có ràng buộc kiểu chặn mô hình phát ra kết quả |
| 17 | Text2CAD | ~170K mô hình / ~660K chú thích; đo thị giác · tham số · hình học | không kiểm chứng **hình thức** | miền **CAD**, không phải hình học giáo dục; không kiểm chứng hình thức |
| 18 | GeoGebra 3D | NA (sản phẩm) | NA | **không nhận đề bài**; đổi lại có **kéo liên tục** mà AlgoSim cố ý không có |
| 19 | Desmos 3D | NA | tự khai là **beta** lúc ra mắt (2023) | máy tính **đồ thị** theo biểu thức, không dựng hình tổng hợp |
| 20 | Cabri 3D | NA | NA | không nhận đề bài |

---

## Đọc ngang ma trận — bốn điều đọc được

**① Trục *sinh hình từ văn bản có kiểm chứng* đã đông.** MagicGeo, GeoLoom,
GeoBuildBench, SDE-GPG, VeriGeo, GGBench đều ở đây. Không được viết như thể
AlgoSim là công trình đầu tiên nghĩ tới việc bắt một solver kiểm lại LLM.

**② Nhưng trục ấy gần như hoàn toàn 2D.** Trong sáu công trình vừa kể, không cái
nào khai phủ hình học không gian. Hai công trình 3D thật (SolidGeo,
DynaSolidGeo) là **benchmark trả lời**, không dựng hình.

**③ Hai ngoại lệ phải nêu tên, không được giấu.** *Geoparsing* (ACL 2026) có
ngôn ngữ hình thức hợp nhất phẳng **và không gian** — nhưng chạy **chiều ngược**.
*Draw2Think* khai phủ cả hình không gian, dựng hình qua constraint engine, và báo
+16,4% ở hình không gian. Bất kỳ phát biểu khoảng trống nào của khoá luận
**phải** đứng vững sau khi đọc hai công trình này.

**④ Ba trục chưa thấy ai đứng cùng lúc**, trong phạm vi đã khảo sát:
số học **chính xác không dùng `float`** làm thẩm quyền đáp số · **song ánh khung
⇔ bước** để tua lại quá trình dựng · **từ chối có cấu trúc hướng người học** (nêu
giai đoạn dừng và mã lỗi) thay vì im lặng hạ chất lượng. VeriGeo chạm trục thứ ba
ở dạng *repair or reject* nội bộ pipeline; không công trình nào trong tập đã đọc
đưa lời từ chối ấy **ra tới người học** như một đầu ra hạng nhất.
