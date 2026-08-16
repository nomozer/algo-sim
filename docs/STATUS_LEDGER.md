# STATUS_LEDGER.md — SỔ TRẠNG THÁI SẢN PHẨM

> **Luật của file này:** mỗi dòng phải trỏ tới **bằng chứng chạy được**. Không
> có bằng chứng ⇒ không được ghi DONE. Bằng chứng sinh từ commit khác HEAD ⇒
> `STALE_EVIDENCE`, cũng không được ghi DONE (`evidence.mjs::assertFresh`).
>
> Cập nhật ở CUỐI mỗi wave. Số sống vẫn ở `CURRENT_STATE.md`.

**HEAD lúc lập sổ:** `a3dac3b` (Wave 0–1 làm trên đó, commit ngay sau).

## 1. Kiến trúc & năng lực

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Kiến trúc mô phỏng tất định (R0: LLM đọc đề, engine diễn hoạt) | **DONE** | bất biến #1–#3 + `algorithms.test.ts`, `generic.test.ts`; pytest 1212 | — |
| Danh mục 23 target / 12 family | **DONE** | `catalog_runtime_matrix.py` → 23 target, conformance/ownership/parity 0 | — |
| Đường AI sinh spec (analyze→classify→simulate→validate) | **DONE** | `test_pipeline`, `test_capability_boundary`; bất biến #22 | W2 (oracle mới) |
| Đường demo công khai (thư viện offline) | **DONE** | `sample-coverage-w4b3d.test.ts` | W3 (lọc phạm vi) |
| **Parity demo ↔ AI** | **DONE (W1)** | `generation-parity.test.ts` — 22 target × 4 nguồn pipeline; `docs/evaluation/m20/generation-parity.json` | — |
| Bố cục sân khấu dùng chung (khung theo cơ chế, một rail) | **DONE (M19)** | `audit-composition.mjs` 92/92 ở 4 bề rộng; bất biến #30 | W7 (tách transport) |
| Khay điều khiển (transport) | **PARTIAL** | cùng cột với thẻ nên co theo cơ chế; W7 muốn nó có bề rộng workspace ỔN ĐỊNH | **W7A** |

## 2. Tương tác học sinh theo miền

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Thao tác trực tiếp HTML/CSS (chọn khối, đổi thứ tự) | **DONE** | `direct-manipulation-w4b4d.test.tsx`; mồi hai chiều | W9 (bàn phím/WCAG) |
| Truy vấn CSDL có ràng buộc | **DONE** | `query-first-w4b4b.test.ts` | — |
| Logic (bật/tắt đầu vào, lan truyền) | **DONE** | `dag.test.tsx`, `logic` domain tests | — |
| Điều kiện `count_if`/`sum_if` | **DONE** | `condition-param.test.ts`, `explore-ownership-w4b3a` | — |
| Trải nghiệm toàn danh mục | **PARTIAL — 20/23 thao tác được** | `w4b4a-experience/probe.json`, `VERDICT.md` | **W5F** |
| 3 target giữ trace có lý do cơ chế | **DONE (quyết định)** | `KEEP_TRACE` + guard hai chiều | W5F (rà lại) |
| RGB/CSS color (Tin 12) | **OPEN — chưa có target** | — | **W5A** |
| Nhãn giá trị vị trí theo cơ số | **OPEN** | — | **W5B** |
| Ký tự & mã hoá theo tham số | **PARTIAL** | đổi được `text`/`encoding` | **W5C** |

## 3. Sản phẩm & lớp học

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Trang khách (không thanh bên, một ô nhập, dùng thử 1 lượt) | **DONE** | `accept-classroom-m18.mjs` 4 bề rộng | **W7C** (đổi bản sắc sang LAB) |
| Xác thực + vai trò do máy chủ sở hữu | **DONE** | `test_auth_api.py`, 6 ca từ chối của `§36` | — |
| Lớp · mã vào lớp · giao bài · thực hành | **DONE** | `test_classroom_api.py` | — |
| Giáo viên quan sát (trạng thái có cấu trúc, 5s) | **DONE** | bất biến #27; `accept-classroom-m18.mjs` | — |
| Giáo viên CẤP tài khoản học sinh | **MISSING** | — (khai ở `CLASSROOM_AUTH_CONTRACT §3`) | ngoài chương trình |
| Tiếp tục ở nhà | **PARTIAL** | khôi phục BẢN GHI tiến độ, KHÔNG khôi phục state engine | W5F |
| Vỏ ứng dụng theo vai trò | **DONE** | `ux-shell.test.tsx`, `accept-classroom-m18.mjs` | W7D |

## 4. Đo lường & chất lượng

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| **Xuất xứ bằng chứng (dấu HEAD)** | **DONE (W0)** | `scripts/evidence.mjs`; đã gắn 3 script | — |
| Bằng chứng cũ trước W0 | **STALE_EVIDENCE** | không mang `head` ⇒ phải sinh lại trước phán quyết cuối | W14 |
| Dataset đánh giá AI 30 case | **DONE, đã đổi vai (W2)** | `LEGACY_AI_COMPOSITION_REGRESSION` — còn nguyên 30 case, hết làm thước đo phủ | — |
| Benchmark theo chương trình học | **DONE (W2/W2A/W2B/W2C)** | `curriculum_schema.py` + `metamorphic.py` + `product_scope.py`; `test_curriculum_benchmark.py` 23 test; `docs/evaluation/m20/curriculum-benchmark.json` | W3 dùng làm oracle |
| Phép đếm phủ từng nói dối | **ĐÃ SỬA (W2A)** | đếm chuỗi thô ⇒ 14 đơn vị (6 là câu ghi chú); rút regex ⇒ `T10.CD1` 12 case. Thật: **8 đơn vị**, `T10.CD1` 9–24 tùy pool | — |
| Cổng phạm vi + khả-mô-phỏng | **DONE (W3)** | `simulation/scope_gate.py` — cổng thứ NĂM, trước đường generic; `test_scope_gate.py` 15 test + 4 phép tiêm lỗi | — |
| Phán quyết phạm vi do LLM sở hữu (lỗ R0) | **ĐÃ BỊT (W3)** | trước W3, đề ngoài môn chỉ bị chặn khi `classify` tự từ chối; nay LLM KHAI, server PHÁN | — |
| Lời từ chối cho học sinh | **DONE (W3)** | 3 hạng mục riêng: `out_of_scope` · `not_simulation_suitable` · ngoài danh mục — không hứa sai “sẽ mở rộng dần” | W12 (soát ảnh) |
| Chứng nhận từng target | **PARTIAL (W4)** | manifest `target-certification.test.ts` — 4 cổng ĐỀU ĐÃ có chủ; ghi rõ cổng nào CHƯ A có bằng chứng tươi | W12 (sinh lại bằng chứng trình duyệt) |
| Join target ↔ đơn vị chương trình | **DONE (W4)** | 22/23 có bằng chứng, dẫn xuất từ case; ngoại lệ `binary.base_conversion` (cơ số 8/16 ngoài neo SGK) | — |
| Hai hệ ký hiệu neo trong cùng kho | **ĐÃ BẮC CẦU (W4)** | catalog ghi số BÀI, benchmark ghi mã CHỦ ĐỀ — join qua case thay vì chép tay SGK | W13 (hợp nhất?) |
| Kim tự tháp test (T0–T3) | **OPEN** | hiện chỉ có "chạy hết" | **W8** |
| Nghiệm thu trình duyệt 4 bề rộng | **DONE** | composition + classroom + experience | W12 (mở rộng) |
| Hook chất lượng phân biệt SVG vs HTML | **OPEN** | false positive đã xác định ở `ArrayView` | **W10** |

## 4b. Wave 5 — hoạt hình → công cụ học tập

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| `binary.base_conversion` trả lời không cần Play | **DONE (W5)** | BEFORE 0 tin@cursor0, đáp án `7EA` vắng mặt → AFTER 17 tin, đọc được; 4 bề rộng | — |
| `binary.character_encoding` bảng đủ hàng | **DONE (W5)** | BEFORE dãy bit của T/i/n vắng ở cursor 0 → AFTER đọc được; 4 bề rộng | — |
| `web.style_model` công cụ màu RGB | **DONE (W5)** | 4 → 7 ô điều khiển; ba kênh 0–255 qua `set_param` → `module.apply` | — |
| `web.style_model` — THAO TÁC TRỰC TIẾP | **DONE ở tầng module (5443c51)** | `direct-manipulation-w4b4d.test.tsx`: chọn nút trên sân khấu + dời khối (`move`, miền HOÁN VỊ) đi qua `module.apply`. Bằng chứng TRÌNH DUYỆT: **NO_EVIDENCE** | **W12** |
| Miền màu nới bảy ô → 24 bit | **DONE (W5)** | validator hai tầng + `CACHE_VERSION` 28→29 (ba chỗ) | — |
| Oracle độc lập ba target | **DONE (W5)** | `parseInt`/`toString(base)` · `codePointAt`/`toString(2)` · số học chuỗi hex | — |
| Tiêm lỗi W5 | **13/13 BỊ BẮT** | hai phép tìm ra LỖ GUARD THẬT (cột thập phân renderer; chiến lược diễn giải sau khi đổi cơ số) — đã vá. #12/#13 chạy ở preflight W6: đổi bảng mã chỉ-đổi-nhãn · mã sản phẩm rẽ nhánh theo nguồn envelope | — |
| Quyết định W3 bị W5 đảo | **ĐÃ KHAI** | ba guard "không lộ đáp án sớm" viết lại về bảng chia + băng kết luận, không xoá | — |
| Yêu cầu transport (đầu vào W7) | **ĐÃ GHI** | base_conversion + character_encoding: TRACE TUỲ CHỌN · web.style_model: RESET ONLY | **W7** |

## 4c. Wave 6 — công cụ là chính, thử thách là phụ

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Thử thách đóng mặc định | **ĐÃ CÓ TỪ W4B-2Z** | `loadEnvelope` đặt `challengeOpen/exploreOpen: false`; nay khoá bằng guard | — |
| Tính đúng sai do engine sở hữu | **DONE** | `PredictionBar` chỉ đọc `prediction.verdict`; guard quét mã sản phẩm | — |
| Băng phán quyết không lấn cơ chế | **DONE** | `.result-banner` giữ `width: fit-content`; guard đọc CSS | — |
| Lối vào/ra thử thách tiếp cận được | **DONE (W6)** | **khiếm khuyết W6 tìm ra**: trước đây chỉ có `setOpened(true)` — cửa MỘT CHIỀU. Nay có nút Đóng + phím Esc + trả tiêu điểm về nút mở | — |
| Manifest trải nghiệm 23 target | **DONE (W6)** | `experience-manifest.test.ts` → `docs/evaluation/m20/experience-manifest.json` | — |
| Phân loại transport (đầu vào W7) | **DONE (W6)** | **13 FULL_TRACE · 7 OPTIONAL_TRACE · 3 RESET_ONLY**, mỗi target một lý do cơ chế | **W7** |
| Con số transport từng giả | **ĐÃ SỬA (W6)** | mặc định "có timeline ⇒ FULL_TRACE" cho ra 18; bỏ mặc định, khai đủ ⇒ 13/7/3 | — |
| Tiêm lỗi W6 | **8/8 BỊ BẮT** | thử thách tự mở · kết quả bị giấu · băng phán quyết to · khám phá chấm điểm · UI tự chấm · cửa một chiều · không trả tiêu điểm · trace-first bị hạ | — |
| Chứng nhận tương tác toàn danh mục | **NO_EVIDENCE** | manifest MÔ TẢ hiện thực, không cấp chứng nhận | **W12** |

## 4d. Wave 7 — khay điều khiển thuộc workspace

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Khay tách khỏi bề rộng cơ chế | **DONE (W7)** | BEFORE cơ chế lệch 849px / khay lệch 849px → AFTER khay lệch **0px**; 4 bề rộng | — |
| Chế độ transport từ CHÍNH SÁCH | **DONE (W7)** | `transport-policy.ts` — 23 target khai đủ, `transportModeOf` không có mặc định | — |
| Suy diễn `stepCount` bị bỏ | **DONE (W7)** | trước W7 dải phân loại bằng `stepCount > 1`; nay đọc chính sách, guard khoá phép gán | — |
| Dòng thời gian tuỳ chọn gập mặc định | **DONE (W7)** | "Xem cách thực hiện" / "Ẩn các bước"; trạng thái TRÌNH BÀY, không vào store | — |
| Soát transport toàn danh mục | **DONE (W7)** | 23/23 khay đúng 1120px, 1 hàng, 0 tràn, 0 hở >24px | — |
| Tiêm lỗi W7 | **8/8 BỊ BẮT** | hai phép tìm ra LỖ GUARD THẬT: phép gán chế độ; sàn cột chỉ khoá một biến thể | — |
| Quyết định M19 bị W7 đảo | **ĐÃ KHAI** | M19 cố ý buộc khay bằng cột nội dung; W7 đổi sang thẳng TÂM thay vì thẳng MÉP | — |
| Tiêm lỗi W7 | **11/11 CÓ BẰNG CHỨNG** | 5 phép tĩnh (W7) + 6 phép bổ sung ở closure: mở trace reset state · mở trace gọi fetch · trace cũ sống sót · hở 16→**169px** · mobile tràn · Đặt lại gọi mạng | — |
| ZERO-AI runtime | **DONE (W7 closure)** | `runtime-zero-ai-w7.mjs` 23/23: mở/đóng trace, trace theo tham số, Đặt lại — fetch delta 0, init delta 0, state trùng khớp | — |
| Dòng thời gian gập lại khi đổi bài | **DONE (W7 closure)** | khiếm khuyết do harness runtime tìm ra: `SimulationControls` không remount nên trace mở ở bài A còn mở ở bài B | — |
| Nghiệm thu trải nghiệm trình duyệt (W6) | **PARTIAL — không đổi** | W7 chỉ chứng minh transport, không chứng minh thứ tự tầng thị giác | **W12** |

## 4e. Wave 8 — kim tự tháp test

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Hợp đồng 4 tầng | **DONE (W8)** | `docs/TEST_TIERS.md` + `test-tiers.test.ts` khoá ngữ nghĩa nhãn | — |
| Bộ chọn T0 | **DONE (W8)** | `impact.mjs` — ba nguồn, in lý do, leo thang khi không tra ra chủ | — |
| Luật không-chọn-rỗng | **DONE (W8)** | mã sản phẩm luôn chọn ≥1 đơn vị; `IMPACT_MAPPING_MISSING` leo thang | — |
| **pytest 57s → 15,6s** | **DONE (W8)** | nguyên nhân đo được: 365ms/lần băm × mỗi lượt đăng ký; hạ vòng KDF TRONG TEST, mức production khoá bởi `test_kdf_cost.py` (marker `real_kdf_cost`) | — |
| T0 thực đo | **DONE (W8)** | renderer 3,2s · engine 3,4s · chủ sở hữu chung 4,9s · tài liệu 3,0s · hợp đồng backend 26s (leo thang đúng) | — |
| Tiêm lỗi W8 | **8/8 BỊ BẮT** | 3 guard từng KHỚP RỖNG rồi báo đạt — đúng lỗi wave này tồn tại để chống, xuất hiện trong chính guard chống nó | — |
| Live AI tách tầng | **DONE (W8)** | guard cấm `ALLOW_LIVE_AI` xuất hiện trong bộ chọn tất định | — |
| Xuất xứ bằng chứng v2 | **DONE (W8 closure)** | mô hình W0 TỰ MÂU THUẪN: artifact ghi `head=A`, commit xong HEAD thành B ⇒ STALE vĩnh viễn. Nay buộc vào `sourceFingerprint` (loại trừ `docs/`) — commit bằng chứng không đổi dấu vân tay | — |
| Năm trạng thái xuất xứ | **DONE (W8 closure)** | FRESH · STALE_SOURCE · DIRTY_SOURCE · INCOMPATIBLE_TOOL · UNKNOWN_PROVENANCE; thiếu trường KHÔNG mặc định thành FRESH | — |
| `binary.base_conversion` | **SUPPORTING_CAPABILITY** | catalog neo `T10 B4` (nhị phân, đã được `decimal_to_binary` phủ); case duy nhất tự khai NOT_ANCHORED cho cơ số 16. KHÔNG bịa mã SGK để đạt 23/23 | — |
| Gộp server trình duyệt (§21) | **OPEN** | chưa làm — W12 mới biết cần kịch bản nào | **W12** |
| Phân tầng benchmark (§24) | **OPEN** | chưa làm | **W12** |
| Gộp test trùng / property (§25–26) | **OPEN** | chưa làm | — |

## 0. KHOÁ PHẠM VI ĐỀ TÀI — ràng buộc cho mọi wave còn lại

### TÊN ĐỀ TÀI CANONICAL (chốt 2026-08-16)

> **Hệ mô phỏng thuật toán tương tác kết hợp LLM phân tích bài toán có lời văn,
> hỗ trợ dạy học môn Tin học THPT**

Đây là tên GỐC, tra được ở `docs/RULES.md` v0.3 và bị xoá ở commit `1f95e92`
(*"M9-UX1 … vệ sinh RULES"*). Nó **không bị thay bằng một quyết định phạm vi** —
nó rụng kèm một lượt dọn tài liệu, rồi bản rộng ở README (`0621910`) sống một
mình. Phạm vi nới ra do TRÔI. Khôi phục là trả về chỗ cũ, không phải đổi hướng.

Vì sao tên hẹp đúng hơn tên rộng: hệ **không sinh** mô phỏng mới (R0 — điều đề
tài cố ý từ chối), nên mỗi miền đều dựng tay. Bề rộng vì thế đo LƯỢNG CODE đã
gõ, không đo cái kiến trúc làm được. Chiều sâu mới đo được kiến trúc: 14 target
thuộc trọng tâm dùng CHUNG một `interaction-policy`, một chủ sở hữu vị từ, một
engine điểm-quyết-định, một khe thuyết minh.

**TIÊU ĐIỂM = BA ĐIỂM NGHẼN NHẬN THỨC (chốt 2026-08-16)**

Khung tổ chức của luận văn KHÔNG phải "độ phủ chương trình" mà là **điểm nghẽn
nhận thức**: chỗ trực giác học sinh hỏng, nên mới đáng bỏ công trực quan hoá.
Khung này trả lời được câu "vì sao cái này đáng mô phỏng?" — điều mà khung độ
phủ không trả lời nổi — và nó khớp gốc hình học động: KÉO để thấy bất biến,
đúng ở chỗ nghĩ thầm không ra.

⚠️ **CÁCH PHÁT BIỂU BẮT BUỘC.** Nói *"ba điểm nghẽn LỚN NHẤT"* là tuyên bố THỰC
NGHIỆM, mà kho này giữ nhãn `LEARNER_IMPACT_NOT_EVALUATED` — không có khảo sát
trên người học. Phát biểu đúng: *"ba điểm nghẽn được CHỌN theo yêu cầu cần đạt
của chương trình GDPT 2018 và các khó khăn đã ghi nhận trong tài liệu về người
mới học lập trình"*. Chọn có căn cứ, không tự phong.

| # | Điểm nghẽn | Vì sao trực giác hỏng | Target (13) |
|---|---|---|---|
| 1 | **Trạng thái tích luỹ qua vòng lặp** | không giữ nổi "max đến giờ" / "tổng đến giờ" trong đầu khi duyệt, và không thấy nó đổi lúc nào | `find_max` `find_min` `sum_if` `count_if` `linear_search` `scan` `bounded_control_flow` |
| 2 | **Bất biến & tiền điều kiện** | không hiểu vì sao tìm nhị phân ĐÒI dãy đã sắp; không thấy thuật toán KHÔNG nhìn lại vùng đã duyệt | `binary_search` `bubble_sort` `insertion_sort` `selection_sort` |
| 3 | **Thứ tự duyệt quyết định kết quả** | cùng một cây/đồ thị, đổi kiểu duyệt ra dãy khác — thứ tự LÀ định nghĩa | `tree.traversal` `network.graph_traversal` |

Bộ ba này KHÔNG được gán cho vừa: mỗi nghẽn ứng đúng một tương tác ĐÃ CÓ trong
`interaction-policy.ts` — đổi ngưỡng/điều kiện (1) · kéo cột vào vùng đã duyệt,
phá thứ tự đã sắp (2) · đổi kiểu duyệt (3). Nó mô tả thứ hệ ĐÃ LÀM ĐƯỢC, không
phải thứ hứa sẽ làm.

**TẦNG HAI — 11 target, GIỮ TRONG HỆ, CẮT KHỎI TIÊU ĐIỂM**

`decimal_to_binary` `base_conversion` `character_encoding` `color.rgb_model` ·
`and_gate` `boolean_dag` `generic.rule_scene` · `protocol_encapsulation` ·
`relational_table_query` · `web.style_model` · `network.packet_routing`

⚠️ **CẮT KHỎI TIÊU ĐIỂM ≠ XOÁ KHỎI HỆ.** Không demo, không chương, không đo —
một bảng phụ lục nửa trang là đủ. Nhưng KHÔNG xoá code, vì xoá là mất đúng ba
thứ đang đứng vững: (a) bằng chứng mở rộng — luận cứ kiến trúc mạnh nhất, số đo
W5A: thêm miền tốn một `SimSpec` + một dòng đăng ký, 0 dòng pipeline; (b) ranh
giới TỪ CHỐI — `generic.rule_scene` chính là chỗ chứng minh đúng-hoặc-
`capability_gap`, xoá nó thì Phase M không còn đối tượng; (c) 24 target đang bị
khoá bởi test đếm, migration và artifact chứng nhận, nên xoá là một wave gỡ rối
mà KHÔNG thêm một chữ nào cho quyển luận văn.
Loãng đề tài là do KỂ CHUYỆN dàn trải, không phải do code tồn tại.

`network.packet_routing` xuống tầng hai vì định tuyến không nằm gọn trong ba
nghẽn trên; nhét vào nghẽn 3 là làm hỏng sự sạch của bộ ba để lấy một con số.

**VIỆC CÒN LẠI ĐỂ TIÊU ĐIỂM THÀNH THẬT (W5P — chưa làm)**

Quyết định ba tầng hiện MỚI NẰM Ở TÀI LIỆU. Thư viện vẫn bày đủ 11 target tầng
hai cho học sinh, nên sản phẩm vẫn loãng đúng như trước khi chốt. Cách làm đã
thử và ĐÃ BIẾT chính xác cần gì:

Khai MỘT danh sách `FOCUS_SIM_IDS` (13 target) ở `data/offline-catalog.ts`, rồi
`publicCatalog()` lọc theo `visibility === "public" && FOCUS_SIM_IDS.includes(...)`.
KHÔNG rải 13 cờ `visibility` khắp `sim-samples.ts`: tiering là quyết định SẢN
PHẨM đổi theo phạm vi đề tài, rải thành cờ thì mỗi lần đổi phải sửa mười mấy chỗ
và không ai đọc ra ý định.

Bốn guard sẽ đỏ, và cả bốn đều mã hoá GIẢ ĐỊNH CŨ (mọi target đăng ký đều bày ở
Thư viện) — phải migrate chứ không vá:

1. `catalog.test.tsx::starterEntries` — `STARTER_SIM_IDS` đang chứa ba target
   tầng hai (`binary.decimal_to_binary`, `network.packet_routing`,
   `logic.and_gate`); thay bằng target tiêu điểm.
2. `capability-descriptors.test.ts::library_discoverable ⟹ có mẫu công khai` —
   BACKEND còn khai `ReachabilityLevel.LIBRARY_DISCOVERABLE` cho 11 target tầng
   hai. Phải bỏ mức đó trong `catalog.py` rồi chạy
   `scripts/generate_capability_descriptors.py`. GIỮ `AI_REACHABLE_PUBLIC`:
   học sinh gõ đề màu RGB thì hệ vẫn phải dựng được — từ chối lúc ấy mới là sai.
3. `ux-shell.test.tsx` ×3 — đếm thẻ Trang chủ/Thư viện.
4. `interaction-semantics.test.ts` — quét qua danh mục công khai.

⚠️ Đây là một cuộc DI TRÚ, không phải một dòng sửa: nó chạm backend catalog +
artifact sinh lại + 4 file test. Làm trọn một lượt, đừng bỏ dở.

**NGOÀI PHẠM VI:** LMS · IDE tự do · sinh hình không ràng buộc · chứng minh cải
thiện kết quả học tập → `POST_THESIS_BACKLOG.md`.


**Lõi đề tài**: yêu cầu học bằng ngôn ngữ tự nhiên → LLM đề xuất *spec ứng viên
có ràng buộc* → validate năng lực/phạm vi tất định → engine tất định → biểu diễn
2D/3D tương tác khi có vai trò sư phạm → học sinh thao tác/quan sát cơ chế →
trace/giải thích/thử thách tuỳ chọn → bối cảnh lớp học nhẹ.

**KHÔNG phải mục tiêu** (nếu một ý tưởng rơi vào đây, nó thuộc
`POST_THESIS_BACKLOG`, không phải wave mới): LMS đầy đủ · quản lý trường học ·
điểm danh · học phí · sổ điểm · thời khoá biểu · diễn đàn · nền tảng soạn khoá
học · IDE HTML/CSS/JS tuỳ ý · IDE lập trình tuỳ ý · hệ mô phỏng cho mọi môn ·
sinh hình tuỳ ý không ràng buộc · thay thế giáo viên · chứng minh cải thiện kết
quả học tập khi chưa có nghiên cứu trên người học.

**Tầng lớp học ĐÓNG BĂNG ở mức**: đăng nhập · lớp · giao mô phỏng đã hỗ trợ ·
học sinh luyện tập · giáo viên quan sát trạng thái có cấu trúc.

**Kỷ luật tuyên bố**: chỉ nói điều có bằng chứng. Giữ
`CURRICULUM_SUPPORT_PARTIAL` khi phủ chương trình còn dở, và
`LEARNER_IMPACT_NOT_EVALUATED` vì kho này không chứa nghiên cứu đối chứng trên
người học.

## 4f. Wave 10 — guard ngữ nghĩa chuyển động

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Phân biệt hình học SVG ↔ bố cục HTML | **DONE (W10)** | `transition-semantics.test.ts` — đọc NGỮ CẢNH PHẦN TỬ, không cấm theo tên thuộc tính | — |
| `ArrayView` giữ chuyển động dạy học | **DONE (W10)** | cột `<rect>` chạy `y`/`height` vì chúng encode giá trị mảng | — |
| Hạng mục THỨ BA do guard tìm ra | **ĐÃ KHAI (W10)** | `.web-page` chạy `padding` — thuộc tính bố cục HTML nhưng CHÍNH LÀ state mô phỏng đang dạy; cấm nó là cấm bài học | — |
| Tiêm lỗi W10 | **5/5 BỊ BẮT** | HTML chạy height · HTML chạy margin · inline `<div>` chạy width · ngoại lệ wildcard · gỡ hình học SVG | — |

## 4g. Wave 12 — chứng nhận trình duyệt (ĐANG DỞ)

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Runner dùng chung một server | **DONE (W12)** | `browser-runner.mjs` — 23 kịch bản, `serverStarts: 1`; cách ly bằng `store.reset()` + xoá lưu trữ, không khởi động lại tiến trình | — |
| Chứng nhận tương tác 23 target | **14/23 CERTIFIED** | `certify-w12.mjs` → `w12-interaction.json`, mang `sourceFingerprint`. Luật: hành động → SimAction → apply → state tất định đổi → hệ quả DOM | **W12 tiếp** |
| 9 target còn lại | **PROBE_UNVERIFIED** | **KHÔNG phải khiếm khuyết sản phẩm.** Probe chưa dùng đúng từ vựng action của miền (`logic` chỉ nhận `toggle`, `network` nhận `net_*`, `tree`/`database` chưa đọc hợp đồng). Phải đọc hợp đồng rồi chạy lại trước khi kết luận bất cứ điều gì | **W12 tiếp** |
| Mùi quiz — `packet_routing` | **ĐÃ SỬA (W12-A)** | đo được 111px/180px = **0,62** (thử thách gần bằng ⅔ cơ chế). Sửa ở CHỦ SỞ HỮU CHUNG `.predict-bar` (dải ngang biết xuống dòng), không vá riêng network → **0,34**, 2 hàng → 1 hàng | — |
| Guard W6 đo sai tầng | **ĐÃ SỬA (W12-A)** | W6 chỉ soi `.result-banner` có `fit-content`; băng gọn thật nhưng HỘP CHỨA nó thì không. Guard mới đo cả khối | — |
| Ma trận 23×4 bề rộng | **39/92** | 0 tràn · 0 cắt · thử thách đóng sẵn ở mọi dòng. 52 dòng hỏng là họ `algorithm` + `graph_traversal`/`packet_routing`: affordance kéo bị HOÃN theo luật cam kết (`interaction-policy.ts` §15) ở bước mặc định · 1 dòng `web.style_model` @768 sân khấu chồng khay | **W12 tiếp** |
| Nguyên nhân "quiz-first" đã truy được | **XÁC ĐỊNH (W12-C)** | `whatIfDragAllowed` cố ý hoãn kéo khi còn cam kết chờ. Hành vi được thiết kế, nhưng hệ quả: ở bước mặc định thứ duy nhất nhìn thấy được là ô dự đoán — đúng điều quan sát từ màn hình thật | **cần quyết định sản phẩm** |
| `commit_decision` | **POST_THESIS_BACKLOG** | `docs/POST_THESIS_BACKLOG.md` — mở rộng đáng làm, không cần cho chứng nhận trung thực kiến trúc hiện có | — |
| Chứng nhận tương tác trình duyệt | **23/23** | 20 CERTIFIED qua thao tác THẬT (action đọc từ config + hợp đồng miền) + 3 TRACE_MODEL đã xác nhận (`apply` đồng nhất). `PROBE_LIMITED` = **0** | W12-C tiếp |
| Ngữ nghĩa tương tác 23 target | **11 / 9 / 3** | `INTERACTIVE_MODEL` 11 (đụng ĐỐI TƯỢNG HỌC) · `BOUNDED_PARAMETER_TOOL` 9 (họ algorithm — chỉ đổi ĐẦU VÀO) · `TRACE_MODEL` 3 | — |
| Năm lần probe sai từ vựng | **ĐÃ GIẢI** | logic dùng `N/G/K` không phải `A`; mạng dùng trường `a`/`b` không phải `from`/`to`, id `client`/`router`; tree dùng `variant` không phải `order`; generic dùng `a`/`b` không phải `0`; database dùng `filter.column` không phải `threshold`. Mọi giá trị nay ĐỌC từ config mẫu + hợp đồng miền | — |
| Bảng "6/9/3/5" cũ | **ĐÃ THAY** | 5 `PROBE_LIMITED` đã giải bằng id thật, 4 trong đó hoá ra là INTERACTIVE_MODEL | — | `INTERACTIVE_MODEL` 6 (đụng ĐỐI TƯỢNG HỌC) · `BOUNDED_PARAMETER_TOOL` 9 (chỉ đổi ĐẦU VÀO) · `TRACE_MODEL` 3 · `PROBE_LIMITED` 5. Con số giảm so với lượt trước và đó là kết quả TRUNG THỰC HƠN | **W12 tiếp** |
| Cả họ `algorithm` chưa có đường cam kết cơ chế | **KHIẾM KHUYẾT ĐÃ XÁC ĐỊNH** | quyết định "promote/keep max" chỉ sống trong `predict` (thử thách); `module.apply` KHÔNG có action nào cho nó. Nên 9 target thuật toán là công cụ tham số + trace, chưa phải mô phỏng tương tác theo nghĩa cơ chế | **W12-B0.5 tiếp** |
| Ngữ nghĩa tương tác (bảng 15/3/5 cũ) | **ĐÃ HUỶ** | nó tính `whatif_swap` là thao tác mô hình, trong khi sắp xếp lại dãy là đổi ĐỀ BÀI chứ không phải tham gia phép quét | — | `INTERACTIVE_MODEL` 15 · `TRACE_MODEL` 3 (xác nhận `apply` đồng nhất) · `PROBE_LIMITED` 5 (chưa kết luận). Câu hỏi cổng: "đóng thử thách rồi, học sinh thao tác lên cái gì?" | **W12 tiếp** |
| `find_max` — ca tham chiếu | **ĐÃ LÀM RÕ (W12-B0)** | hai nút "Đặt 9 làm max mới"/"Giữ max = 7.5" là THỬ THÁCH (nuôi `predict.check`). Thao tác mô hình thật là kéo cột `ArrayView` → `whatif_swap` → nhánh what-if, còn nguyên khi đóng thử thách | — |
| Con số "14 CERTIFIED" cũ | **ĐÃ HUỶ** | nó chưa phân biệt thao tác mô hình với trả lời dự đoán | — |
| Quét mùi quiz 23 target | **PARTIAL** | 2/23 chạm được bề mặt thử thách sau khi tiến bước; 21 target còn lại CHƯA kết luận được — không đọc thành "không có thử thách" | **W12 tiếp** |
## W12 — BỐN CHIỀU CÒN LẠI ĐÃ ĐÓNG (2026-08-16)

| chiều | trạng thái | bằng chứng |
|---|---|---|
| Khả năng tiếp cận trình duyệt | **DONE** | `w12-a11y.json` — 6/6 bề mặt, phím THẬT qua CDP; Escape đóng thử thách + trả tiêu điểm về nút mở; 4/4 tiêm lỗi đỏ đúng chỗ |
| Tiếp nối lớp học | **DONE** | `w12-classroom-continuation.json` — đăng nhập → luyện → ĐĂNG XUẤT + xoá sạch lưu trữ → quay lại → tiến độ về từ MÁY CHỦ; 2/2 tiêm lỗi |
| Kịch bản dạy học | **DONE** | `w12-teaching-walkthrough.json` — 11/11 dùng được KHI thử thách đóng |
| Biểu diễn công khai + parity 2D↔3D | **DONE** | `w12-representation.json` — 23 target, **0** bày công tắc cho học sinh, 0 vi phạm; `protocol_encapsulation` parity 2D↔3D đạt trên trình duyệt |

**Lỗi sản phẩm THẬT tìm ra và đã sửa** (không phải lỗi phép đo):

1. **Affordance cơ chế nằm ngoài bàn phím.** `logic.and_gate` có 13 phần tử
   focus được trên màn, KHÔNG cái nào là công tắc A/B. Cùng họ ở
   `binary.decimal_to_binary` và `generic.rule_scene`. Idiom "một `<g>` có
   `cursor:pointer` + `onClick`" được dựng ở năm chỗ, làm ĐÚNG ở hai. Gom về
   `simulations/svg-affordance.ts`.
2. **Không có vòng tiêu điểm** cho chính những affordance vừa nối bàn phím —
   vào được cơ chế mà không thấy mình đang ở đâu. Thêm `.sim-affordance:focus-visible`.
3. **Công tắc 2D/3D bày cho học sinh mà không có luật.**
   `protocol_encapsulation` khai `primary: "2d"` nhưng `alternate:
   ALTERNATE_FOR_EXPLANATION`, trong khi chính lời khai lý do lại mô tả 2D là
   "biểu diễn nội bộ" — một cấu hình không mô tả sản phẩm nào. Nay 3D là bản
   NỘI BỘ, học sinh không bị hỏi chọn cách xem.

**PACKET_ROUTING_3D_DEFERRED.** Lý do kỹ thuật, không phải thẩm mỹ: renderer 3D
DUY NHẤT trong kho là `encap-ui3d.tsx`, dựng cho trục Z = tầng giao thức. Định
tuyến cần Z = TUYẾN THAY THẾ — một ngữ nghĩa khác, tức renderer mới chứ không
phải một lời khai. Và 2D hiện tại đã chứng nhận đủ chuỗi tương tác có thẩm
quyền (`net_disconnect` → `module.apply` → tính lại tuyến → hệ quả nhìn thấy),
có đường bàn phím, dùng được ở cả bốn bề rộng. Bày 3D trang trí mà không có
tương tác có thẩm quyền là đúng thứ `PUBLIC_3D_INTERACTION_FAIL` cấm.

**PRIMARY_CAPABILITY_PARITY_CERTIFICATION = NOT_CURRENTLY_EVIDENCED.** Hai con
số `10/23` và `13/23` từng được mang theo qua nhiều báo cáo. Grep toàn kho:
không mã, không test, không artifact nào sinh ra chúng — chúng sống sót vì lượt
trước đã nói ra chúng. Cổng parity CÓ THẬT là `generation-parity.test.ts`, và nó
chứng minh một trục KHÁC: **nguồn spec (mẫu vs AI) không chọn đường đi**, 22
target × 4 nguồn pipeline. Artifact nay có provenance + danh tính target. Không
dựng lại 23 fixture chỉ để cứu một thống kê — mục tiêu là toàn vẹn bằng chứng.
Khoá bởi `certification-sweep.test.ts`.

## W12 — ĐÃ GIẢI: MỘT LƯỢT, MỘT DẤU VÂN TAY (2026-08-16, `80c7c05`)

> Mục ngay dưới (`9609cc6`) là **chẩn đoán**, giữ lại để đọc *vì sao*. Trạng
> thái hiện hành là mục này.

**`FINAL_SOURCE_HEAD = 80c7c05` · `FINAL_SOURCE_FINGERPRINT = de3007604b68ca47`**

| | |
|---|---|
| artifact W12 FRESH | **9/9** (8 cổng con + chính bản ghi lượt) |
| `UNIQUE_CERTIFICATION_SOURCE_FINGERPRINT_COUNT` | **1** |
| STALE_SOURCE · DIRTY_SOURCE · UNKNOWN_PROVENANCE | **0 · 0 · 0** |
| phán quyết lượt | `CERTIFICATION_SWEEP_VALID` — HEAD và vân tay y nguyên hai đầu, `DIRTY_AFTER` rỗng |

Bằng chứng: `docs/evaluation/m20/w12-sweep.json`. Công cụ:
`frontend/scripts/certify-sweep-w12.mjs`, khoá bởi `src/certification-sweep.test.ts`.

**Cái đã đổi về CHẤT.** Hệ quả vận hành ở mục dưới trước đây là *lời nhắc* — và
nó bị bỏ qua đúng như mọi lời nhắc khác trong kho này. Nay nó là **cổng**: một
lượt chứng nhận chụp `HEAD` + vân tay + cây bẩn ở hai đầu, và mọi vi phạm có mã
lý do riêng (`SOURCE_DIRTY_AT_SWEEP_START` · `SOURCE_DIRTY_AT_SWEEP_END` ·
`HEAD_MOVED_DURING_SWEEP` · `SOURCE_FINGERPRINT_CHANGED_DURING_SWEEP`). Nhắc thì
trôi, đỏ thì không.

**Hai lỗi đường ống bắt được trong lúc làm, cả hai đều là cổng tự miễn trừ:**

1. `w12-interaction-semantics.json` là **đầu vào** của `certify-viewports-w12.mjs`
   nhưng chỉ có `generatedAt` ⇒ `UNKNOWN_PROVENANCE` vĩnh viễn. Một mắt xích của
   bộ bằng chứng nằm ngoài mọi cổng.
2. `w12-sweep.json` — artifact *chứng minh* kỷ luật xuất xứ — cũng
   `UNKNOWN_PROVENANCE` ở lượt cuối đầu tiên. Guard mới đã **đỏ thật** trên chính
   bản ghi hỏng ấy trước khi nó bị bỏ đi.

**Kết quả sản phẩm không đổi khi đo lại trên nguồn sạch** — 20 TOOL_PASS ·
3 TRACE_PASS · 23/23 sức nặng thị giác · 92/92 viewport · 20/20 cuộn ·
23/23 tương tác · 0 FAIL mùi quiz · 3/3 tiêm lỗi. Tức các con số lịch sử vốn
đúng; thứ thiếu đúng là **chứng minh chúng thuộc về nguồn hiện tại**, và nay có.

## W12 — XUẤT XỨ BẰNG CHỨNG: KHÔNG ARTIFACT NÀO FRESH (2026-08-15, `9609cc6`)

Đo bằng chính hợp đồng provenance (`sourceFingerprint` hiện tại `551c75b4…`):

| artifact | trạng thái |
|---|---|
| `w12-experience-audit.json` · `w12-visual-weight-faults.json` | **STALE_SOURCE** |
| `w12-interaction.json` · `w12-quiz-dominance.json` · `w12-scroll-shell.json` · `w12-viewport-matrix.json` · `w12-visual-weight.json` | **DIRTY_SOURCE** — đo trên mã chưa commit |
| `w12-interaction-semantics.json` | **UNKNOWN_PROVENANCE** — sinh trước hợp đồng v2 |

**Luật `chỉ FRESH mới đỡ được COMPLETE` ⇒ hiện KHÔNG chiều trình duyệt nào
được phép khai COMPLETE**, kể cả những chiều có con số đẹp (23/23 sức nặng thị
giác, 92/92 viewport, 20/20 cuộn). Con số vẫn đúng với lúc đo; cái thiếu là
**chứng minh chúng đúng với nguồn HIỆN TẠI**.

### Nguyên nhân, và nó mang tính cấu trúc

`sourceFingerprint` phủ `frontend/scripts` — nên **commit chính script vừa sinh
artifact sẽ làm artifact ấy STALE ngay lập tức**. Cùng họ với lỗi tự-tham-chiếu
đã sửa một lần ở W8 (`assertFresh` đòi `head === gitHead()`, khiến artifact vừa
commit vĩnh viễn cũ). Lần ấy sửa bằng cách loại `docs/` khỏi vân tay; lần này
lộ ra vế còn lại.

### Hệ quả vận hành — thứ tự BẮT BUỘC

1. Đóng băng nguồn (`src/` + `scripts/`), commit hết.
2. **Rồi mới** chạy lại toàn bộ script chứng nhận trong MỘT lượt.
3. Commit **chỉ artifact** — `docs/` không nằm trong vân tay nên bước này
   không tự huỷ kết quả.

Chạy chứng nhận trước khi source đóng băng là **lãng phí**: mọi artifact sinh ra
đều DIRTY, và một bản chứng nhận DIRTY không đỡ được bất kỳ tuyên bố nào.

## W12 — trạng thái theo TỪNG CHIỀU (2026-08-15, `28a0c20`)

**`ALGOSIM_WAVE12_BROWSER_CERTIFICATION_PARTIAL`.**

### COMPLETE / ĐÓNG BĂNG — không soát lại trừ khi có hồi quy

| chiều | bằng chứng |
|---|---|
| hợp đồng sinh đặc tả | `test_web_contract_sync.py` · `CACHE_VERSION` 30 ba chủ sở hữu |
| hành vi sinh, **6/6 họ** | `test_web_generated_behavior.py` · `..._families.py` · `..._db_network.py` |
| soát hợp đồng cả catalog | `test_catalog_contract_audit.py` (23/23 dẫn từ `CATALOG`) |
| preflight PDF + soát OCR | 5/5 IMAGE_ONLY · 804 trang · 15/15 mẫu → 0 ký tự · không công cụ OCR nào |

### BLOCKED_EXTERNAL_EVIDENCE — **nhánh đóng băng, KHÔNG chặn phần còn lại**

```
CURRICULUM_SOURCE_PRESENT  = YES (5/5)
CURRICULUM_SOURCE_FORMAT   = IMAGE_ONLY
CURRICULUM_TARGETED_OCR    = UNAVAILABLE
CURRICULUM_BLOCKER         = CURRICULUM_EXTRACTION_REQUIRES_EXTERNAL_EVIDENCE
```

Thiếu cụ thể: mục lục 5 quyển + các trang bài để neo 24 mục công khai.
**Không** chạm engine tất định, hành vi trình duyệt, hay hợp đồng sinh.

### PARTIAL — việc độc lập còn lại, theo thứ tự thi hành

1. parity mẫu↔AI ở mức trường lõi (23 target)
2. phân loại trải nghiệm cuối + teaching-tool audit cả catalog
3. chứng nhận tương tác trình duyệt thật (INTERACTIVE_MODEL) + discoverability
4. chứng nhận BOUNDED_PARAMETER_TOOL + TRACE_MODEL
5. soát animation-only + quiz-first
6. chính sách biểu diễn công khai · `packet_routing` · `protocol_encapsulation`
7. parity 2D↔3D nội bộ
8. thao tác trực tiếp HTML/CSS · tiếp cận · tiếp nối lớp học
9. ma trận viewport tươi · hồi quy cuộn · walkthrough dạy học
10. ma trận lỗi cuối · provenance · T3 kỹ thuật

Hạ tầng đã đủ: `browser-runner.mjs` · `certify-{viewports,experience,visual-weight,scroll}-w12.mjs`
· `canonical_config.py` · mẫu FAULT/CONTROL ở `test_web_contract_sync.py`.

### Giữ nguyên

`CURRICULUM_SUPPORT_PARTIAL` · `LEARNER_IMPACT_NOT_EVALUATED` ·
`WAVE4_INTERACTION_CERTIFICATION = NO_EVIDENCE` · `WAVE6_BROWSER_EXPERIENCE = PARTIAL`

### Rủi ro kỹ thuật đã ghi nhận (không phải khiếm khuyết tất định)

`GENERATION_CONTRACT_RESIDUAL_ENGINEERING_RISK` — schema thuật toán dùng chung
không diễn đạt được `required` theo từng target. Validator vẫn fail-closed nên
runtime an toàn; giá phải trả là một lượt sinh hỏng, không phải mô phỏng sai.

## W12 — trạng thái đóng (2026-08-14, `1647af3`)

**Verdict: `ALGOSIM_WAVE12_BROWSER_CERTIFICATION_PARTIAL`.**

Blocker **đúng hai mục**, chi tiết thi hành ở `docs/W12_REMAINING.md`:

1. `network.packet_routing` chưa có renderer 3D — cần dựng cảnh + đường chọn
   liên kết phát `net_disconnect` + đường bàn phím tương đương.
2. Benchmark theo đơn vị chương trình — chặn bởi **thiếu danh sách mã SGK có
   thẩm quyền**, không phải bởi code. KHÔNG tự chế mã (`COVERAGE.md §15`).

Đã đóng: cuộn 20/20 · viewport 92/92 · ngữ nghĩa 11/9/3 · trải nghiệm 19 TOOL /
4 TRACE / 0 FAIL · **sức nặng thị giác 23/23** · bề mặt công cụ CSS dẫn từ đặc
tả · `protocol_encapsulation` 3D công khai · rò rỉ liên môn 0.

Giữ nguyên: `CURRICULUM_SUPPORT_PARTIAL` · `LEARNER_IMPACT_NOT_EVALUATED` ·
`WAVE4_INTERACTION_CERTIFICATION = NO_EVIDENCE` ·
`WAVE6_BROWSER_EXPERIENCE = PARTIAL`.

## W12 §A — quyền sở hữu cuộn của vỏ ứng dụng (2026-08-14)

**Triệu chứng người dùng chụp được.** Thanh cuộn gần như tàng hình · một khe dọc
xấu cạnh header · mép trang và mép header không đọc thành một vỏ liền.

**Không đảo quyết định cũ.** Mẫu "vỏ cố định + main tự cuộn" mà brief §3 nêu
nghe đúng, nhưng **W4B-1A đã đo và cố ý đi hướng ngược**: vùng cuộn nội bộ giấu
170px nội dung học ở 1920×768 mà `page_scrollable_y` vẫn `false` — học sinh
không có tín hiệu nào ở mức trang. Chủ sở hữu cuộn đúng vẫn là TÀI LIỆU, và §3
cho phép giữ nếu đã có chủ sở hữu đúng.

**Nguyên nhân thật, đo bằng chuỗi bố cục.**

```
innerW 1902 · html clientWidth 1902 · body 1892 ← hụt đúng 10px
```

`html { scrollbar-gutter: stable }` giữ 10px ở content box của html, nên body —
và header bên trong nó — hẹp hơn 10px. Dải ấy lộ nền `--canvas-soft` cạnh header
`--canvas`, chạy suốt chiều cao tài liệu.

Nó đọc ra là KHE HỞ chứ không phải máng cuộn vì `scrollbar-color: transparent
transparent` + thumb webkit `background: transparent`: **mặc định không thấy
gì**. "Mảnh, chìm" đã trượt thành "vô hình" — đúng thứ W12 §4 cấm.

**Sửa.** Ba mức đậm dần qua token (`--scroll-thumb` · `-strong` · `-hover`),
có mặt sẵn ở mức mờ. Giữ nguyên `scrollbar-gutter: stable` — bỏ nó đi để "hết
khe hở" là đổi một lỗi thị giác lấy lỗi nhảy ngang mà §5 cấm.

**Một lỗi TIÊU CHÍ của chính phép đo.** Bản đầu so header với
`de.clientWidth` (padding-box, không phản ánh việc giữ chỗ) nên báo HỎNG 20/20 —
tức đòi header phủ luôn cả máng cuộn, điều không trang cuộn-tài-liệu nào làm
được. Đo lại bằng body: header **trải hết vỏ** ở mọi dòng.

**Kết quả:** `certify-scroll-w12.mjs` — **20/20** (5 màn × 4 bề rộng), máng
đúng 10px và **giống nhau giữa trang ngắn (985px, không cuộn) và trang dài
(2045px, cuộn)** ⇒ không nhảy ngang; 0 tràn ngang.

⚠️ Thumb có thấy được không thì trình duyệt không trả lời được (CDP không đọc
computed style của pseudo-element). Khoá ở `styles/scrollbar-ownership.test.ts`,
kèm đối chứng dương dựng lại đúng bản CSS cũ.

## W12 §6 — Policy B: công cụ hiện ra khi thử thách ĐÓNG (2026-08-14)

**Quan sát khởi nguồn (của người dùng).** `algorithm.find_max` đọc ra: nhìn hình
→ đọc câu hỏi → bấm một trong hai nút. Tức một bài kiểm tra, không phải công cụ.

**Đo trước khi sửa.** `certify-viewports-w12.mjs` (23 target × 4 bề rộng, HEAD
`99548af`): **39/92** dòng ĐẠT.

**Nguyên nhân — một luật bị chép tay ba lần.** Ba nơi cùng đòi `exploreOpen`
trước khi dựng công cụ, mà trang vừa mở thì cờ đó `false`:

| nơi | công cụ bị giấu |
|---|---|
| `domains/algorithm/ui.tsx` | kéo cột (`whatif_swap`) |
| `domains/network/ui.tsx` | vùng bấm ngắt/nối liên kết |
| `domains/algorithm/ui.tsx` — `ConditionBar` | ngưỡng + phép so sánh (`set_param`) |

Lý do gốc của cổng là "đừng cho né cam kết", nhưng cam kết chỉ tồn tại KHI THỬ
THÁCH ĐANG MỞ. Nay cả ba đi qua **`simulations/tool-affordance.ts`**.

**Một bug thứ hai, chỉ trình duyệt mới thấy.** Trong `traverse-module.tsx`, dòng
JSX gọi `TraverseParamBar` nằm SAU câu `return` của một `useEffect`: cú pháp hợp
lệ, tên không "unused", TypeScript im — nên control BFS↔DFS **không bao giờ được
render**. `network.graph_traversal` là công cụ tham số mà học sinh không có cách
nào đổi tham số. Không unit test nào bắt được vì không test nào hỏi "control có
trên màn hình không".

**Ba lỗi TIÊU CHÍ của chính phép đo, sửa luôn** — mỗi cái đều xác minh bằng dò
tận nơi, không suy đoán:

1. `getBoundingClientRect` trên `<line>` ngang trả `150×0` (Chrome không cộng
   stroke) ⇒ ba vùng bấm liên kết bấm được của `packet_routing` bị vứt đi.
2. Đòi affordance ở target **TRACE_MODEL** (`apply` đồng nhất) — 0 affordance ở
   đó là ĐÚNG. Danh sách nay ĐỌC TỪ bảng phân loại, vì bản viết tay của tôi sai
   ngay lần đầu (ghi nhầm `tree.traversal`).
3. Khay điều khiển `position: sticky` nổi trên nội dung dài bị đọc là "chồng
   lấn" — đó chính là việc của neo (quyết định W7).

**Sau khi sửa: 92/92.** Diễn tiến đo được: 39 → 67 (Policy B ở miền thuật toán)
→ 75 (miền mạng + thanh điều kiện) → 87 → 91 → 92 (ba lỗi tiêu chí).

**KHÔNG nâng hạng target nào** (W12 §8): `whatif_swap` vẫn là INPUT_MANIPULATION.
Bảng ngữ nghĩa giữ nguyên **11 INTERACTIVE_MODEL · 9 BOUNDED_PARAMETER_TOOL ·
3 TRACE_MODEL · PROBE_LIMITED = 0**.

| `WAVE4_INTERACTION_CERTIFICATION` | **NO_EVIDENCE — không đổi** | chỉ nâng khi đủ 23/23 có bằng chứng tươi | **W12** |
| `WAVE6_BROWSER_EXPERIENCE` | **PARTIAL — không đổi** | chín màn trải nghiệm chưa chạy | **W12** |

## 5. Phủ chương trình

| Owner / Feature | Trạng thái | Bằng chứng | Wave kế |
|---|---|---|---|
| Ma trận phủ chương trình | **PARTIAL** | `COVERAGE.md` + `catalog_runtime_matrix` + báo cáo W2A (8 đơn vị, mọi đơn vị ≥3 case) | **W13** |
| Đơn vị chương trình mỏng (<3 case) | **DONE (W2A)** | T10.CD2 2→3, T12CS.CD7 1→3 (3 case cross-domain mới); khoá bởi guard ngưỡng | — |
| Tuyên bố bị cấm (không claim phủ toàn chương trình) | **DONE** | `COVERAGE.md §O` | giữ nguyên |
| `CURRICULUM_SUPPORT_PARTIAL` | **GIỮ** | — | W13 |
| `LEARNER_IMPACT_NOT_EVALUATED` | **GIỮ** | chưa có nghiên cứu trên người học | — |
