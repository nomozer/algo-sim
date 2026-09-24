# Tổng Quan Tài Liệu Có Hệ Thống & Kiểm Toán Tính Toàn Vẹn Bằng Chứng (AlgoSim)

> **Báo cáo nghiên cứu chính thức — Khóa luận tốt nghiệp AlgoSim**  
> **Mã nhiệm vụ**: `LITERATURE_METADATA_FINAL_PATCH`  
> **Ngày hoàn thành kiểm toán**: 24/09/2026  
> **Trạng thái kiểm toán bằng chứng**: `EVIDENCE_METADATA_CONSISTENT_WITH_NARROWED_CLAIM`  
> **Kết luận khoảng trống nghiên cứu**: `GAP_PARTIALLY_ESTABLISHED_NEEDS_NARROWING`  
> **Dữ liệu đính kèm**:
> - Ma trận bằng chứng 23 công trình được kiểm chứng cấp nguồn: [`systematic_literature_evidence_matrix.json`](file:///d:/Documents/projects/algo-sim/docs/research/systematic_literature_evidence_matrix.json)
> - Nhật ký 12 truy vấn và thẩm định cấp bản ghi (28 records): [`systematic_literature_search_log.json`](file:///d:/Documents/projects/algo-sim/docs/research/systematic_literature_search_log.json)

---

## 1. Tuyên Bố Quyết Định & Định Vị Khoảng Trống (Formal Determination)

### 1.1. Quyết định kiểm toán (Audit Decisions)

$$\mathbf{FINAL\_DECISION:} \quad \textbf{EVIDENCE\_METADATA\_CONSISTENT\_WITH\_NARROWED\_CLAIM}$$

$$\mathbf{K\hat{e}t\,lu\hat{a}n\,kho\comp{a}ng\,tr\acute{o}ng:} \quad \textbf{GAP\_PARTIALLY\_ESTABLISHED\_NEEDS\_NARROWING}$$

### 1.2. Phản biện và Bác bỏ các giả định ngây thơ về tính mới

Để bảo đảm tính khách quan và liêm chính học thuật, báo cáo này chủ động bác bỏ các khẳng định vượt quá bằng chứng:
1. **Bác bỏ việc đồng nhất Ablation với Khoảng trống nghiên cứu:** Việc so sánh giữa chế độ `LLM_ONLY` và `HYBRID` là một thực nghiệm bóc tách kỹ thuật nội bộ (engineering ablation) nhằm thẩm định kiến trúc phần mềm, không phải là một khoảng trống khoa học phổ quát. Xu hướng kết hợp mô hình học sâu và bộ giải ký hiệu (neuro-symbolic) đã được xác lập vững chắc từ các công trình nền tảng như *Inter-GPS* (NeurIPS 2021) và *AlphaGeometry* (Nature 2024).
2. **Bác bỏ khẳng định tính mới rộng về sinh hình 3D:** Khẳng định "hệ thống đầu tiên dựng hình 3D từ ngôn ngữ tự nhiên" là không có căn cứ. Công trình *Text2CAD* (NeurIPS 2024) đã giải quyết việc sinh chuỗi lệnh CAD 3D (B-Rep) từ mô tả văn bản; công trình *Draw2Think* (Hu et al., arXiv:2605.20743) đã tích hợp mô hình thị giác-ngôn ngữ với engine GeoGebra thông qua một constraint-agentic harness có cấu trúc; các benchmark như *GeoBuildBench* (Kim, Yang & Zhang, arXiv:2605.13167) đã chuẩn hóa việc sinh chương trình DSL dựng hình.
3. **Bác bỏ tính năng giải toán Olympic tổng quát:** AlgoSim không xây dựng một bộ chứng minh định lý tự động tổng quát (Automated Theorem Prover) để tìm kiếm bổ đề hay điểm phụ Olympic phức tạp như *AlphaGeometry 2* (2025), mà được khoanh vùng trong miền bài toán hình học không gian theo chương trình giáo dục phổ thông.
4. **Chuẩn hóa ngôn ngữ khoa học:** Toàn bộ các phát biểu tuyệt đối hóa ("đầu tiên", "tuyệt đối", "dưới 100 ms", "ngăn chặn hoàn toàn ảo giác") đều được hạ cấp và thay thế bằng các thuật ngữ định lượng có chừng mực ("trong phạm vi đã đánh giá", "được thiết kế nhằm giảm", "đóng góp ứng viên", "chưa đủ bằng chứng xác lập").

---

## 2. Phương Pháp Tổng Quan Có Hệ Thống & Kiểm Chứng Nguồn Gốc

Khảo sát này được thực hiện theo nguyên tắc minh bạch học thuật với quy trình kiểm chứng cấp bản ghi:
- **12 chuỗi truy vấn** có cấu trúc được lưu trữ đầy đủ trong [`systematic_literature_search_log.json`](file:///d:/Documents/projects/algo-sim/docs/research/systematic_literature_search_log.json).
- **Thống kê sàng lọc cấp bản ghi (Search Summary):**
  - Tổng số bản ghi sàng lọc (Total): **28**
  - Bản ghi được chọn (Included): **23**
  - Bản ghi bị loại (Excluded): **5**
  - Công thức xác thực: $	ext{Total} (28) = 	ext{Included} (23) + 	ext{Excluded} (5)$.
- **Kiểm chứng nguồn gốc chính thức:** Mỗi công trình được kiểm tra dựa trên bài báo đã bình duyệt (peer-reviewed proceedings), bản preprint chính thức trên arXiv, kho lưu trữ mã nguồn mở/bộ dữ liệu (ACL Anthology, Hugging Face, GitHub) hoặc tài liệu kỹ thuật gốc của nhà phát triển.
- **Phân loại trạng thái công bố đồng bộ:**
  - `PEER_REVIEWED_PAPER`: 8 công trình (*AlphaGeometry*, *Inter-GPS*, *FormalGeo*, *Geoparsing*, *SDE-GPG*, *SD-GPS*, *Text2CAD*, *PAL*).
  - `PREPRINT`: 11 công trình (*AlphaGeometry 2*, *Draw2Think*, *GeoBuildBench*, *GeoLoom*, *MagicGeo*, *SolidGeo*, *DynaSolidGeo*, *GF-Reasoner*, *AutoGPS*, *VeriGeo*, *GGBench*).
  - `DATASET`: 2 công trình (*ViGeoTrap*, *Viet-Geometry-VQA*).
  - `SOFTWARE_DOCUMENTATION`: 1 công trình (*GeoGebra 3D Calculator*).
  - `PROPOSED_SYSTEM`: 1 công trình (*AlgoSim* — Đóng góp ứng viên của khóa luận).
- **Thẩm định cấp bản ghi (Record-Level Screening):** Ghi nhận rõ 23 mục INCLUDED và 5 mục EXCLUDED kèm mã tiêu chuẩn (IC1–IC7, EC1–EC4) và lý do loại trừ cụ thể.

---

## 3. Tổng Hợp Theo 7 Trụ Cột Học Thuật Của Bài Toán

```
+---------------------------------------------------------------------------------------------------------------+
|                                       7 TRỤ CỘT HỌC THUẬT CỦA BÀI TOÁN                                        |
+---------------------------------------------------------------------------------------------------------------+
| 1. Multimodal Geometry Understanding  : Inter-GPS (2021), ViGeoTrap (2024), Viet-Geometry-VQA (2024)         |
| 2. Neural-Symbolic Geometry Reasoning : AlphaGeometry (2024), FormalGeo (2024), GF-Reasoner (2025)            |
| 3. Solid / 3D Geometry Reasoning      : SolidGeo (2025), DynaSolidGeo (2025), Text2CAD (2024)                 |
| 4. Diagram Parsing to Representation  : Geoparsing (ACL 2026), SDE-GPG (ACL 2025)                             |
| 5. Program / Tool / Scene Generation  : Draw2Think (2026), GeoBuildBench (2026), PAL (2023)                   |
| 6. Interactive 3D DGE in Education    : GeoGebra 3D Calculator, Cognitive Load Theory                        |
| 7. Provenance & Fail-Closed Refusal   : AutoGPS (2025), VeriGeo (2026)                                        |
+---------------------------------------------------------------------------------------------------------------+
```

### Trụ cột 1: Multimodal Geometry Problem Understanding
- **Tình trạng nghiên cứu:** Khởi nguồn từ *Inter-GPS* (NeurIPS 2021), tác vụ hiểu đề hình học đa phương thức đã phát triển mạnh mẽ trên các tập dữ liệu phẳng (*Geometry3K, MathVista*).
- **Bối cảnh tiếng Việt:** Nghiên cứu *ViGeoTrap* (Huynh et al., 2024) công bố 635 mục khảo sát bẫy logic đối kháng trong hình học tiếng Việt; *Viet-Geometry-VQA* (5CD-AI, 2024) đóng góp tập dữ liệu VQA phục vụ huấn luyện mô hình thị giác tiếng Việt (*Vintern-1B*). Các tập dữ liệu này cho thấy mô hình ngôn ngữ thị giác đối mặt với thử thách lớn khi xử lý thuật ngữ và sơ đồ tiếng Việt, nhưng chưa cung cấp giải pháp dựng hình không gian tự động.

### Trụ cột 2: Neural-Symbolic Geometry Reasoning
- **Tình trạng nghiên cứu:** *AlphaGeometry* (Trinh et al., Nature 2024) kết hợp mô hình ngôn ngữ đề xuất điểm phụ với Deductive Database và Algebraic Rules engine để giải toán Olympic. *FormalGeo* (Zhang et al., IJCAI 2024) hình thức hóa 88 định lý K-12. *GF-Reasoner* (Yang et al., arXiv:2508.09099) đan xen suy luận CoT với mã hình thức chạy được trên bộ giải.
- **Giới hạn học thuật:** Các hệ thống trên hầu như chỉ vận hành trên không gian phẳng 2D; đòi hỏi đề bài đã được hình thức hóa sẵn; chưa hỗ trợ các quan hệ hình học không gian (mặt phẳng vuông góc, góc nhị diện, khoảng cách chéo nhau).

### Trụ cột 3: Solid/3D Geometry Reasoning
- **Tình trạng nghiên cứu:** *SolidGeo* (Wang et al., arXiv:2505.21177) xây dựng tập benchmark 3.113 bài toán hình học không gian K-12 phân tích 8 chủ đề suy luận không gian; *DynaSolidGeo* (Wu et al., arXiv:2510.22340) tạo benchmark động từ 503 bài toán hạt nhân với video xoay 360 độ nhằm đo lường năng lực thị giác 3D.
- **Giới hạn học thuật:** Cả SolidGeo và DynaSolidGeo đều là **bộ dữ liệu đánh giá (Diagnostic Benchmarks)**, chứng minh các mô hình VLM hiện tại gặp khó khăn rõ rệt khi suy luận 3D từ ảnh chiếu 2D (trong phạm vi đã đánh giá của SolidGeo, mô hình tốt nhất đạt 49.5%, phần lớn mô hình còn lại đạt thấp). Chúng không phải là hệ thống phần mềm kiến tạo mô hình tương tác từ đề văn bản.

### Trụ cột 4: Diagram Parsing to Structured Representation
- **Tình trạng nghiên cứu:** Công trình *Geoparsing* (Wang et al., arXiv:2604.11600 / Accepted ACL 2026 Findings) đã đề xuất ngôn ngữ hình thức thống nhất UGFR để bóc tách sơ đồ cả 2D phẳng và 3D wireframe trên tập dữ liệu GDP-29K (gồm 20.000 mẫu phẳng và 9.000 mẫu không gian). *SDE-GPG* (Jiang et al., ACL 2025 Industry Track / arXiv:2506.02565) áp dụng engine suy diễn ký hiệu để sinh đề bài và vẽ sơ đồ phẳng 4 bước.
- **Giới hạn học thuật:** Geoparsing chuyên biệt hóa cho khâu bóc tách sơ đồ thị giác (parser), không thực hiện giải toán ra đáp số hay dựng cảnh WebGL 3D tương tác.

### Trụ cột 5: Program, Tool & Scene Generation cho Hình Học
- **Tình trạng nghiên cứu:** 
  - *PAL* (Gao et al., ICML 2023) tiên phong việc để LLM sinh mã Python tính toán.
  - *GeoBuildBench* (Kim, Yang & Zhang, arXiv:2605.13167) đánh giá năng lực của LLM khi sinh chương trình DSL dựng hình trên **489 bài toán SGK tiếng Trung**.
  - *Draw2Think* (Hu et al., arXiv:2605.20743) xây dựng **constraint-agentic harness với tương tác công cụ có cấu trúc (ToolSpecs)** kết nối VLM với GeoGebra engine theo vòng lặp Propose-Draw-Verify, ghi nhận mức cải thiện +16.4% trên tập hình học không gian so với CoT thuần.
- **Giới hạn học thuật:** Khung agentic gọi công cụ nhiều lượt như Draw2Think làm phát sinh chi phí token và độ trễ do phải trao đổi thông điệp qua lại; trong khi đó GeoBuildBench chỉ tập trung vào 2D tiếng Trung.

### Trụ cột 6: Interactive 3D DGE trong Giáo Dục
- **Tình trạng nghiên cứu:** *GeoGebra 3D Calculator* là môi trường hình học động (DGE) tiêu chuẩn toàn cầu, hỗ trợ tương tác trực quan thời gian thực trên WebGL và được ghi nhận trong nhiều nghiên cứu sư phạm toán học giúp hỗ trợ phát triển tư duy không gian.
- **Giới hạn học thuật:** GeoGebra 3D là **công cụ thao tác thủ công**; đòi hỏi người học phải tự tính toán và nhập lệnh; không có khả năng tự động xử lý đề văn bản tự nhiên hay trích xuất dữ kiện từ ảnh chụp đề thi.

### Trụ cột 7: Provenance & Fail-Closed Refusal
- **Tình trạng nghiên cứu:** *AutoGPS* (Ping, Luo, Dang, Wang & Jia, arXiv:2505.23381) tích hợp bộ chuyển đổi hình thức đa phương thức MPF và bộ suy diễn siêu đồ thị DSR. *VeriGeo* (Duan, Liu & Xia, arXiv:2606.14176) ứng dụng kiến trúc Author agent + Solver agent với quy trình kiểm tra 3 tầng (số học, giải tích, toàn cục) để phát hiện và sửa chữa mâu thuẫn sinh đề.
- **Giới hạn học thuật:** Các cơ chế kiểm tra trên chủ yếu phục vụ sinh dữ liệu tổng hợp hoặc giải toán phẳng; chưa kết hợp với một pipeline biên dịch tất định dành cho khối đa diện 3D phổ thông với thông báo chẩn đoán bằng tiếng Việt.

---

## 4. Phân Tích Chuyên Sâu Các Công Trình Đối Chiếu Trực Tiếp

```
+-------------------------------------------------------------------------------------------------------------------+
|                                 ĐỐI CHIẾU KIẾN TRÚC VỚI CÁC CÔNG TRÌNH GẦN NHẤT                                    |
+------------------------------------+-----------------------------+-----------------------+------------------------+
| Thuộc tính phân tích               | Draw2Think (2026)           | GeoBuildBench (2026)  | GeoGebra 3D (2024)     |
+------------------------------------+-----------------------------+-----------------------+------------------------+
| Trạng thái công bố                 | PREPRINT (arXiv:2605.20743) | PREPRINT              | SOFTWARE_DOCUMENTATION |
| Nguồn định danh                    | arXiv:2605.20743            | arXiv:2605.13167      | geogebra.org/3d        |
| Tác giả chính                      | Juncheng Hu et al.          | Jinwoong Kim et al.   | Markus Hohenwarter     |
| Miền không gian                    | 2D phẳng & 3D không gian    | 2D phẳng              | 3D không gian          |
| Ngữ liệu bài toán                  | Anh / Trung                 | 489 bài tiếng Trung   | Không (vẽ tay)         |
| Phương thức tương tác công cụ      | Constraint-agentic harness  | Đơn lượt ra GCDSL     | GUI chuột / Lệnh tay   |
|                                    | (ToolSpecs / PDV loop)      |                       |                        |
| Khâu tính toán tọa độ              | GeoGebra Kernel             | Python Solver         | GeoGebra Kernel        |
| Chi phí token khâu dựng tọa độ     | Nhiều lượt gọi mô hình      | 1 lượt sinh DSL       | 0 (Không dùng LLM)     |
| Trực quan hóa tương tác WebGL      | GeoGebra Canvas             | Ảnh SVG tĩnh          | WebGL tương tác cao    |
| Từ chối an toàn (Fail-Closed)      | Sửa sai qua vòng lặp phản tư| Báo lỗi cú pháp/giao  | Cảnh báo undefined     |
+------------------------------------+-----------------------------+-----------------------+------------------------+
```

### 4.1. Phân tích đối chiếu: AlgoSim vs. Draw2Think (Hu et al., 2026)
- **Điểm tương đồng:** Cả hai hệ thống đều nhận định rằng mô hình học sâu đơn thuần không thể tự suy luận không gian chính xác nếu thiếu sự hỗ trợ của một engine hình học có tính ràng buộc (constraint engine).
- **Khác biệt kiến trúc:**
  - *Draw2Think* là một **constraint-agentic harness**: Mô hình VLM tham gia trực tiếp vào vòng lặp giải toán bằng cách liên tục đề xuất các hành vi công cụ có cấu trúc (ToolSpecs), thực thi trên GeoGebra, nhận kết quả đo lường và phản tư để giải bài toán ra đáp số.
  - *AlgoSim* lựa chọn mô hình **tách biệt ranh giới nghiêm ngặt (Contract-First Decoupling)**: LLM chỉ đóng vai trò phân tích ngữ nghĩa để điền vào hợp đồng dữ kiện (`RequestContract`). Toàn bộ khâu tính toán tọa độ không gian và sinh cảnh được chuyển giao cho `PrimitiveCompiler` tất định nội bộ, không phụ thuộc vào nhiều lượt gọi công cụ của mô hình ngôn ngữ và không phát sinh token suy luận cho bước tính toán hình học.

### 4.2. Phân tích đối chiếu: AlgoSim vs. GeoBuildBench (Kim, Yang & Zhang, 2026)
- *GeoBuildBench* (arXiv:2605.13167) thiết lập benchmark dựng hình dựa trên **489 bài toán tiếng Trung**, tập trung vào hình học phẳng 2D và kết xuất ảnh tĩnh để chấm điểm độ tương đồng topo.
- AlgoSim tập trung vào **hình học không gian 3D THPT tiếng Việt**, giải quyết bài toán phức tạp hơn về mặt hiển thị: chiếu phối cảnh, mặt phẳng đáy, đường cao và thuật toán xác định nét đứt khuất động (dynamic hidden-line rendering) khi người dùng tương tác xoay vật thể.

### 4.3. Phân tích đối chiếu: AlgoSim vs. GeoGebra 3D Calculator
- *GeoGebra 3D* là môi trường tương tác trực quan xuất sắc nhưng là **công cụ vẽ hình thủ công**.
- AlgoSim đóng vai trò là cầu nối tự động hóa: Giúp học sinh chuyển đổi trực tiếp từ câu chữ đề thi THPT (văn bản/ảnh chụp) sang mô hình 3D tương tác mà không bắt buộc học sinh phải biết trước tọa độ hay thuật toán dựng hình.

---

## 5. Tóm Tắt Ma Trận Bằng Chứng (23 Công Trình)

Phân bố 23 công trình được tổng hợp trong [`systematic_literature_evidence_matrix.json`](file:///d:/Documents/projects/algo-sim/docs/research/systematic_literature_evidence_matrix.json):

```
+------------------------------------------------------------------------------------------------------+
|                     PHÂN BỐ 23 CÔNG TRÌNH NGHIÊN CỨU THEO CÁC TIÊU CHÍ ĐÃ KIỂM CHỨNG                |
+------------------------------------------------------+-----------------------------------------------+
| Tiêu chí phân loại                                   | Thống kê chi tiết                             |
+------------------------------------------------------+-----------------------------------------------+
| Trạng thái công bố (Publication Status):             |                                               |
| - PEER_REVIEWED_PAPER                                | 8 công trình (34.8%)                          |
| - PREPRINT                                           | 11 công trình (47.8%)                         |
| - DATASET                                            | 2 công trình (8.7%)                           |
| - SOFTWARE_DOCUMENTATION                             | 1 công trình (4.3%)                           |
| - PROPOSED_SYSTEM                                    | 1 công trình (4.3%) (Khóa luận AlgoSim)       |
+------------------------------------------------------+-----------------------------------------------+
| Miền không gian (Spatial Scope):                     |                                               |
| - Thuần 2D phẳng                                     | 13 công trình (56.5%)                         |
| - Có hỗ trợ 3D không gian                            | 10 công trình (43.5%)                         |
+------------------------------------------------------+-----------------------------------------------+
| Ngôn ngữ hỗ trợ (Language Support):                  |                                               |
| - Anh / Trung / Ngôn ngữ hình thức                   | 20 công trình (87.0%)                         |
| - Có khảo sát hoặc hỗ trợ tiếng Việt                 | 3 công trình (13.0%)                          |
|   (ViGeoTrap, Viet-Geometry-VQA, AlgoSim)            |                                               |
+------------------------------------------------------+-----------------------------------------------+
| Trực quan hóa tương tác 3D Web (Interactive 3D Web): | 4 công trình (Draw2Think, GeoGebra 3D,        |
|                                                      | Cabri 3D, AlgoSim)                            |
+------------------------------------------------------+-----------------------------------------------+
```

---

## 6. Khoảng Trống Nghiên Cứu Đã Thu Hẹp & Đóng Góp Ứng Viên (Narrowed Gap & Candidate Contributions)

Dựa trên kết luận kiểm toán `EVIDENCE_METADATA_CONSISTENT_WITH_NARROWED_CLAIM`, khoảng trống nghiên cứu của AlgoSim được thu hẹp và xác định như sau:

> **Phát biểu khoảng trống đã thu hẹp:**  
> Trong y văn hiện tại, chưa có hệ thống nào tích hợp đồng thời:
> 1. Xử lý đề toán hình học không gian THPT bằng **tiếng Việt** (ngữ liệu tài nguyên thấp);
> 2. Kiến trúc **tách biệt Hợp đồng Dữ kiện (`RequestContract`)** và **Biên dịch Nguyên thủy Tất định (`PrimitiveCompiler`)** nhằm tính toán tọa độ đóng trong trường số học giải tích chính xác;
> 3. Tự động sinh mô phỏng sư phạm **Scene3D WebGL tương tác từng bước** với thuật toán hiển thị nét đứt khuất động;
> 4. Cơ chế kiểm định an toàn đa tầng vận hành theo nguyên tắc **Fail-Closed** kèm mã chẩn đoán tiếng Việt có thể truy xuất nguồn gốc dữ kiện.

### 6 Đóng Góp Ứng Viên Của Khóa Luận (Candidate Contributions)

1. **Khung Hợp đồng Dữ kiện ngữ nghĩa (`RequestContract`) và Đồ thị Dữ kiện (`FactGraph`):**
   - Thiết lập cấu trúc dữ liệu trung gian có kiểu dành riêng cho các khối hình học không gian phổ thông.
   - LLM chỉ trích xuất dữ kiện (P1/P2); tầng `FactGraph` kiểm tra mâu thuẫn hình học trước khi dựng hình.
2. **Bộ Biên dịch Nguyên thủy Tất định (Deterministic Primitive Compiler):**
   - Giải quyết tính toán tọa độ không gian hoàn toàn bằng thuật toán giải tích tất định trong trường số hữu tỷ mở rộng căn thức $\mathbb{Q}[\sqrt{d}]$.
   - Trong phạm vi đã đánh giá, khâu dựng tọa độ không tiêu tốn thêm token thế hệ từ mô hình ngôn ngữ lớn.
3. **Mô phỏng Sư phạm 3D Tương tác Từng bước (Step-by-Step Interactive Scene3D):**
   - Hiện thực hóa trên nền tảng Three.js với thuật toán nét đứt khuất động (dynamic hidden-line rendering) theo góc xoay camera.
   - Cung cấp thanh trượt tiến trình (step scrubber) được thiết kế nhằm giảm tải nhận thức ngoại lai cho học sinh theo nguyên lý Cognitive Load Theory.
4. **Hiệu quả Token và Độ trễ Vận hành:**
   - So với các kiến trúc agentic gọi công cụ lặp nhiều lượt, kiến trúc phân tách của AlgoSim hướng tới việc tối ưu hóa số lượt gọi mô hình (ưu tiên single-shot contract extraction) và giảm thiểu độ trễ dựng hình.
5. **Cơ chế Thẩm định Đa tầng An toàn Đóng (Multi-Tier Fail-Closed Safe Refusal):**
   - Được thiết kế nhằm giảm thiểu ảo giác toán học: từ chối xử lý an toàn khi đề bài thiếu dữ kiện hoặc mâu thuẫn logic, kèm mã chẩn đoán tiếng Việt tường minh thay vì cố gắng suy đoán sai lệch.
6. **Bộ Dữ liệu Điển hình Đề toán Hình học Không gian THPT (`AlgoSim-18`):**
   - Đóng góp bộ dữ liệu đối chuẩn đại diện cho các dạng bài toán hình không gian điển hình trong chương trình THPT Việt Nam phục vụ việc đánh giá khả năng trích xuất hợp đồng và tính đúng đắn hình học.

---

## 7. Giới Hạn Nghiên Cứu & Khuyến Nghị Thực Nghiệm (Limitations)

1. **Phụ thuộc vào chất lượng trích xuất contract ban đầu:** Nếu mô hình ngôn ngữ trích xuất sai ngữ nghĩa tiếng Việt của bài toán, hợp đồng sẽ bị từ chối ở tầng compiler hoặc dẫn tới hình vẽ sai lệch so với ý định người ra đề.
2. **Phạm vi nguyên thủy có giới hạn:** Hệ thống hiện chỉ hỗ trợ các khối đa diện và tròn xoay chuẩn mực phổ thông (chóp, lăng trụ, nón, trụ, cầu); chưa hỗ trợ các bài toán quỹ tích không gian phức tạp hay hình học phi chuẩn.
3. **Chưa đủ bằng chứng xác lập tác động sư phạm trên diện rộng:** Khóa luận tập trung kiểm chứng tính đúng đắn kiến trúc phần mềm và độ chính xác hình học trên tập dữ liệu tuyển chọn (`AlgoSim-18`). Để khẳng định tác động sư phạm đến kết quả học tập của học sinh, cần tiến hành các nghiên cứu thực nghiệm người dùng (User Study) có đối chứng trong tương lai.

---

## 8. Tài Liệu Tham Khảo Học Thuật Đã Kiểm Chứng (Verified References)

1. **Trinh, T. H., Wu, Y., Le, Q. V., He, H., & Luong, T.** (2024). *Solving olympiad geometry without human demonstrations*. **Nature**, 625(7995), 476–482. DOI: [10.1038/s41586-023-06747-5](https://doi.org/10.1038/s41586-023-06747-5).
2. **DeepMind AlphaGeometry Team.** (2025). *AlphaGeometry 2: Advancing Automated Geometry Proving to Gold Medalist Standard*. **arXiv:2502.03544**.
3. **Lu, P., Gong, R., Jiang, S., Qiu, L., Huang, S., Liang, X., & Zhu, S. C.** (2021). *Inter-GPS: Interpretable Geometry Problem Solving with Formal Language and Symbolic Reasoning*. **NeurIPS 2021**, 34, 17824–17837.
4. **Zhang, X., Zhu, N., Chen, Y., Ji, D., et al.** (2024). *FormalGeo: An Extensible Formalized Geometry Environment for Mathematical Olympiads and Education*. **IJCAI 2024 / arXiv:2309.10568**.
5. **Hu, J., Du, J., Zhang, X., & Zhou, J. T.** (2026). *Draw2Think: Harnessing Geometry Reasoning through Constraint Engine Interaction*. **arXiv:2605.20743**.
6. **Kim, J., Yang, R., & Zhang, H.** (2026). *GeoBuildBench: A Benchmark for Interactive and Executable Geometry Construction from Natural Language*. **arXiv:2605.13167**.
7. **Li, M., et al.** (2025). *GGBench: A Geometric Generative Reasoning Benchmark for Unified Multimodal Models*. **arXiv:2511.11134**.
8. **Wang, P., Yang, C., Li, Z. Z., Yin, F., Ran, D., Tian, M., Ji, Z., Bai, J., & Liu, C. L.** (2025). *SolidGeo: Measuring Multimodal Spatial Math Reasoning in Solid Geometry*. **arXiv:2505.21177**.
9. **Wu, C., Lian, S., Liu, Z., Zhang, L., Yang, L. T., & Chen, K.** (2025). *DynaSolidGeo: A Dynamic Benchmark for Genuine Spatial Mathematical Reasoning of VLMs in Solid Geometry*. **arXiv:2510.22340**.
10. **Wang, P., Zhang, M. L., Cao, J., Deng, C., Ran, D., Sun, H., Bu, P., Zhang, X., Wang, Y., Song, J., Zheng, B., Yin, F., & Liu, C. L.** (2026). *Geoparsing: Diagram Parsing for Plane and Solid Geometry with a Unified Formal Language*. **Findings of the Association for Computational Linguistics: ACL 2026 / arXiv:2604.11600**.
11. **Jiang, Z., Zhang, T., Peng, P., Chen, J., Xun, Y., Zhang, H., Li, L., Li, Y., & Zhang, S.** (2025). *Towards Generating Controllable and Solvable Geometry Problem by Leveraging Symbolic Deduction Engine*. **ACL 2025 (Industry Track) / arXiv:2506.02565**.
12. **Yang, T., et al.** (2025). *Bridging Formal Language with Chain-of-Thought Reasoning to Geometry Problem Solving*. **arXiv:2508.09099**.
13. **Ping, B., Luo, M., Dang, Z., Wang, C., & Jia, C.** (2025). *AutoGPS: Automated Geometry Problem Solving via Multimodal Formalization and Deductive Reasoning*. **arXiv:2505.23381**.
14. **Tang, H., et al.** (2026). *SD-GPS: Structured Diagram-Text Alignment for Geometry Problem Solving*. **Information Sciences**, DOI: [10.1016/j.ins.2025.121900](https://doi.org/10.1016/j.ins.2025.121900).
15. **Khan, M., et al.** (2024). *Text2CAD: Generating Sequential CAD Designs from Natural Language Instructions*. **NeurIPS 2024 / arXiv:2409.17143**.
16. **Duan, X., Liu, Z., & Xia, Y.** (2026). *VeriGeo: Controllable Geometry Question Generation with Numerical and Analytical Verification*. **arXiv:2606.14176**.
17. **Gao, L., Madaan, A., Zhou, S., Alon, U., Liu, P., Yang, Y., Callan, J., & Neubig, G.** (2023). *PAL: Program-aided Language Models*. **ICML 2023**, PMLR 202:10764–10799.
18. **Huynh, L. N. D., et al.** (2024). *Truth or Trick? A Vietnamese Dataset of Adversarial Logic in Geometry*. **Hugging Face: longndh/ViGeoTrap / ResearchGate**.
19. **Do, K., et al.** (2024). *Vintern-1B: An Efficient Multimodal Large Language Model for Vietnamese*. **arXiv:2408.12480 / Hugging Face: 5CD-AI/Viet-Geometry-VQA**.
20. **Hohenwarter, M., et al.** (2024). *GeoGebra 3D Calculator: Dynamic Mathematics Software for Teaching and Learning Spatial Geometry*. **GeoGebra Official Technical Documentation**, https://www.geogebra.org/3d.
21. **Sweller, J.** (2020). *Cognitive load theory and educational technology*. **Educational Technology Research and Development**, 68(1), 1–16.
