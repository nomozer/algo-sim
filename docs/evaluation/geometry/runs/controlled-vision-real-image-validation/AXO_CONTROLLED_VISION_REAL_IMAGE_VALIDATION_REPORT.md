# AXO — Controlled Vision benchmark & real-image product validation

**Trạng thái:** `PRODUCT_TESTS_PASS` · `PUBLICATION_RANGE_PASS` · `CANDIDATE_FREEZE_MATCH` ·
`PUBLICATION_HEAD = BLOCKED_PENDING_OWNER_REVIEW` · `FULL_RELEASE_GATE = BLOCKED_GATES_REMAIN` ·
`LIVE_VISION_NOT_MEASURED` · `ARCHITECTURE_DECISION_PENDING_LIVE_EVIDENCE`. Không merge, push hay deploy.

| danh tính | giá trị |
|---|---|
| nhánh / worktree | `feat/local-first-geometry-understanding`, worktree cố định |
| điểm bắt đầu | report HEAD `44807b13b` (candidate cũ `a068b6f6…`, khớp số bàn giao: [baseline_integrity.json](baseline_integrity.json)) |
| sản phẩm | `c53be83db`: sửa đúng một hàm OCR, xem §3 |
| candidate | freeze `a78b1e087`, measured system `cd9b9f518805d305…` / 115 file, `CACHE_VERSION = 132` ([candidate_freeze.json](candidate_freeze.json)) |
| hợp đồng giữ nguyên | planner /26, functions /33, engine /24, height-invariance-certificate /2, output-policy /1 |
| lượt gọi provider | 0; `ALLOW_LIVE_AI = 0` suốt run |

Nhãn: **VF** = VERIFIED FACT, **INF** = INFERENCE, **HYP** = HYPOTHESIS, **NM** = NOT_MEASURED, **BLK** = BLOCKED.

## 1. Kết luận chính

1. **Nút thắt chính của Image-to-3D không nằm ở OCR mà ở parser cục bộ và Source Gate** (VF, chẩn đoán trên bản chép).
   Ngay cả khi nhận nguyên văn bản do agent chép, chỉ 6/23 đề đa diện chạy hết tuyến không-AI: 4 giải đúng, 2 bị từ chối.
   17 đề còn lại dừng ở parser (12) hoặc Source Gate (5).
2. **OCR cục bộ đọc đúng phần lớn dữ kiện toán học, nhưng không ảnh nào được tự động chấp nhận** (VF).
   Tập evaluation khôi phục 124/136 dữ kiện then chốt (91%), 12/19 ảnh đủ mọi dữ kiện. Cổng an toàn vẫn giữ cả 19 ảnh để học sinh xác nhận.
3. **Không có đáp án sai nào được phục vụ** (VF, so với khoá dataset): 0 wrong-served trên 3 đáp án được phục vụ từ ảnh.
4. **Một lỗi OCR thật đã được sửa có bằng chứng**: ảnh đọc lại dính glyph hàng xóm làm nhân đôi dấu `=` mà vẫn mang trạng thái *verified*.
   Lỗi tìm thấy trên tập development; tập evaluation không đổi kết quả.
5. **SQLite hỏng khi 8 upload đồng thời** (VF): 4/24 request lỗi `SQLITE_BUSY`. Đến 4 upload đồng thời thì 21/21 request thành công.

## 2. Trả lời 32 câu hỏi

| # | câu hỏi | trả lời | nhãn |
|---:|---|---|---|
| 1 | 97 finding publication gồm nhóm nào? | 18 blob: 16 log traceback lịch sử (95 finding, 15 log lộ tên tài khoản Windows + đường dẫn local) và 2 placeholder `Bearer` giả (2 finding). 0 blob mới so với baseline; 0 giá trị trông như secret thật; 18/18 đã có trên `origin/main` | VF |
| 2 | Bao nhiêu mục giải quyết thực sự? | 0. Mọi cách đóng đều cần Owner (duyệt entry) hoặc sẽ sửa bằng chứng đã đóng băng ([quyết định](publication_remediation_decisions.md)) | VF |
| 3 | Bao nhiêu cần owner review? | 97 finding / 18 blob; khuyến nghị duyệt đúng 18 cặp (đường dẫn, blob), không nới luật | VF |
| 4 | Corpus mới có bao nhiêu ảnh trong phạm vi hình học? | 25 ảnh hình học không gian (23 đa diện, 2 khối tròn ngoài phạm vi); 6 development / 19 frozen evaluation. Mục tiêu 15–25 đạt; bao phủ chóp, lăng trụ, hộp, khoảng cách, góc, nhị diện, thể tích. Thiếu thiết diện, tỉ số, chữ viết tay, ảnh chụp giấy | VF |
| 5 | Bao nhiêu ground truth đã xác minh? | 0 HUMAN_VERIFIED; 25 AGENT_TRANSCRIBED_UNVERIFIED. Đáp án = khoá dataset; agent tự giải 19 bài, khớp khoá 19/19 | VF |
| 6 | Local OCR đọc đúng bao nhiêu ảnh? | Nguyên văn: 0/19. Đủ mọi dữ kiện then chốt: 12/19 evaluation, 4/6 development. CER trung vị 0,096; WER 0,209 | VF |
| 7 | Độ chính xác dữ kiện toán học? | Recall 124/136 trên evaluation. Theo loại: góc 7/7, độ dài 33/35, quan hệ 27/29, tên khối 25/28, mục tiêu 32/37. Precision NM | VF / NM |
| 8 | Bao nhiêu ảnh local tự giải hoàn toàn? | 0/25 | VF |
| 9 | Bao nhiêu ảnh cần sửa? | 25/25 cần xác nhận. 3 ảnh được giải chỉ với xác nhận, không sửa ký hiệu nào. Số ảnh cần sửa thật mà vẫn giải được: 0 | VF |
| 10 | Bao nhiêu ảnh cần Vision? | Chưa đo được. Thiếu dữ kiện trên ảnh chỉ là 12 fact; thứ chặn là parser, mà Vision không thay được parser | NM / INF |
| 11 | Gemini live đã được phê duyệt và chạy chưa? | Chưa: `NOT_GRANTED`, 0 lượt gọi ([trạng thái](live_vision_authorization_status.json)) | BLK |
| 12–16 | Chất lượng, lỗi đọc, dữ kiện trên hình, lượt gọi, chi phí/latency của Vision | Không có dữ liệu thật; không tạo payload giả | NM |
| 17 | Adaptive Hybrid có lợi hơn Local OCR? | Chưa đo. 21/21 test offline xác nhận định tuyến an toàn (fail-closed, xung đột dữ kiện buộc xác nhận) | NM; routing VF |
| 18 | Cần thêm model OCR không? | Không có bằng chứng: lỗi còn lại chủ yếu là tách token / bố cục, không phải nhận dạng ký tự | INF |
| 19 | Warm/cold/cache latency? | Prepare HTTP p50 / p95: cold-model 4,29 / 5,16 s; warm miss 1,98 / 2,60 s; cache hit 136 / 186 ms. FastAPI mới: lên 2,37 s, ảnh đầu 5,26 s. Nhanh hơn run trước nhưng CPU máy bận 77% so với 89%, nên không quy cho mã ([số liệu](cold_warm_cache_latency.json)) | VF |
| 20 | Tổng RAM FastAPI + OCR? | Đỉnh lấy mẫu, warm p50 / p95: 799 / 930 MiB (cây OCR 615 / 745, FastAPI ~190). 2–4 upload đồng thời: tới ~1023 MiB. Không có tiến trình mồ côi sau crash/shutdown ([bộ nhớ](combined_process_memory.json)) | VF |
| 21 | Tải đồng thời ổn định không? | 1 / 2 / 4 upload đồng thời: 3/3, 6/6, 12/12. 8 đồng thời: 20/24 (2×500, 2×401, đều `SQLITE_BUSY`). Không tuyên bố năng lực production; PostgreSQL NM ([độ tin cậy](concurrent_upload_reliability.json)) | VF |
| 22 | Học sinh thật đã dùng confirmation UI chưa? | Chưa | NM |
| 23 | Image-to-3D thành công theo route | A_LOCAL_AUTO 0 · B_VISION 0 (NM) · C_USER_REAL NM · C2_SIMULATED 3 đúng · E_CAPABILITY_GAP 2 · 20 dừng ở parse không-AI ([kết quả](real_image_to_scene3d_results.json)) | VF |
| 24 | Wrong-served trong các ca có oracle? | 0 / 3 phục vụ (oracle = khoá dataset) | VF |
| 25 | Scene3D có đúng không? | 3/3 cảnh dựng, 0 vi phạm continuity; trình duyệt thật 6/6 (desktop + mobile). Đúng hình học ngoài kiểm continuity: chưa kiểm độc lập | VF / NM |
| 26 | Máy yếu vật lý? | Chưa | NM |
| 27 | H-1 độc lập? | Chưa. Đã để dành 142 dòng VMMU chưa ai tải/xem làm ứng viên H-1 | NM |
| 28 | Geometry capability gaps còn lại? | Kernel: `EXACT_DOMAIN_EXCEEDED` (thể tích chóp với góc 30°); suy cạnh góc vuông từ cạnh huyền (mang sang). Ngoài kernel: 12 ca parser, 5 ca Source Gate ([backlog](geometry_capability_gap_backlog.json)) | VF |
| 29 | Local-first, Vision-first hay Adaptive? | Giữ local-first + xác nhận theo span. Adaptive Hybrid là ứng viên cần đo live ([ADR](architecture_decision_record.md)) | INF |
| 30 | Đủ điều kiện pilot giới hạn? | Pilot có giám sát kỹ thuật: được, trong phạm vi bài đa diện mà parser hoàn tất. Pilot học sinh rộng: chưa (0 tự giải, parser chặn 17/23, chưa có người dùng thật, publication đang chặn) | INF |
| 31 | Việc cần Owner quyết | 18 blob publication; phê duyệt Vision live (provider, model, SHA ảnh, trần request/USD, điều kiện dừng); có pre-warm OCR worker không (~2 s ảnh đầu so với ~0,5 GB RAM lúc nhàn rỗi) | — |
| 32 | Bước tiếp theo giá trị cao nhất | Mở rộng parser cục bộ và Source Gate theo 17 ca trong backlog (chỉ dùng development, chuyển ca evaluation sang development khi dùng), rồi đo lại cùng corpus | INF |

## 3. Thay đổi sản phẩm duy nhất

`backend/app/ingestion/ocr_reconcile.py`:

- **Lỗi:** khi đọc lại một ô toán đang tranh chấp, ảnh cắt có đệm ngang nên lẫn glyph của ô kề. Hai bộ đọc lại cùng ra `SA =`, thắng phiếu `SA` của RapidOCR. Ô `=` kế bên vẫn được giữ, nên đề thành `SA= = a` mà mọi span đều *verified*.
- **Sửa:** bỏ đúng một từ đầu hoặc cuối của bản đọc lại, khi từ đó tách bằng khoảng trắng và trùng bản đọc chính của ô kề. Token dính liền như `SA=` không bị cắt.
- **Test:** 2 test đỏ → xanh, 1 test đối chứng ([test](../../../../../backend/tests/test_image_first_local_ocr.py)).
- **Đo trên ảnh thật, trước / sau:**

| tập | trước | sau |
|---|---|---|
| development | 35/40 fact; `r476` không phục vụ | 36/40 fact; `r476` phục vụ đúng sau xác nhận |
| evaluation (không dùng để tìm lỗi) | 124/136 fact | 124/136 fact, kết quả giải không đổi |

Không đổi geometry, parser, Source Gate, hợp đồng hay cache version. Ba template phê duyệt đang chờ (K-1, R-1, S-2) được gắn lại vào measured system mới; vẫn `PENDING_OWNER_DECISION` ([receipt](pending_template_refresh.json)).

## 4. Corpus và tách lỗi theo tầng

- **Nguồn:** VMMU `full_vqa`. Tác giả dataset khai MIT; quyền của đề thi gốc chưa xác minh, nên ảnh để ngoài Git.
- **Loại trùng:** bỏ 163 câu đã có trong các corpus trước.
- **Chọn ảnh:** sàng từ khoá bằng Tesseract, rồi agent xem từng ảnh trúng. Agent cũng xem 43 ảnh không trúng của lô đầu và không bỏ sót bài đa diện nào. Thiên lệch vẫn có thể làm số OCR đẹp hơn thực tế ([audit](corpus_contamination_audit.json)).
- **Split:** chỉ phụ thuộc hash của dataset id, đóng băng trước khi chạy OCR ([manifest](new_in_scope_image_manifest.json)).

Mỗi ảnh được đo riêng từng tầng:

| tầng | receipt | kết quả chính |
|---|---|---|
| Nhận dạng | [local_ocr_baseline.json](local_ocr_baseline.json), [critical_mathematical_fact_evaluation.json](critical_mathematical_fact_evaluation.json) | Đối chiếu hai engine khôi phục 124 fact; riêng Tesseract 46, riêng RapidOCR 67 |
| Định tuyến | [image_evaluation_summary.json](image_evaluation_summary.json) | 0 chấp nhận tự động; 0 false acceptance. 16 ảnh đủ fact vẫn bị giữ, chủ yếu do `DIAGRAM_FACTS_UNVERIFIED` + `UNCERTAIN_SPANS` |
| Giải trên văn bản chuẩn | [transcription_solver_diagnostic.json](transcription_solver_diagnostic.json) | 4 giải được, 2 gap, 17 dừng không-AI, 2 ngoài phạm vi |
| Ảnh → kết quả | [api_acceptance_*.json](api_acceptance_frozen_external_evaluation.json) | 3 đúng sau xác nhận. `r247`: OCR tách tên khối `4BCD-` + `A'B'C'D'`; sửa span không xoá được khoảng trắng giữa hai token nên parser không nhận (phát hiện UX, ca evaluation, không sửa) |

## 5. Trải nghiệm học sinh (tự động, không phải nghiên cứu người dùng)

| bộ kiểm thử | kết quả | phạm vi |
|---|---|---|
| [Ảnh trong phạm vi](browser_in_scope_audit.json) | 6/6 | 3 ảnh × desktop 1440×900 và mobile 390×844: upload → crop span → xác nhận bằng bàn phím → dựng → canvas Scene3D; không tràn ngang |
| [Xác nhận span](browser_confirmation_audit.json) | 4/4 | sửa làm mất xác nhận cũ; huỷ không gọi analyze; CSS zoom 1,1 |
| [Kịch bản cũ](browser_existing_scenarios.json) | 6/6 | gồm chọn bài khi ảnh có nhiều đề; chặn khi đề phụ thuộc hình vẽ |

- **Phát hiện UX:** với bài hỏi góc, màn hình hiện `cos²(BC′, (ACC′A′)) = 1/4`, không hiện `60°` như phương án trắc nghiệm. Đúng về toán, nhưng học sinh phải tự quy đổi. Thuộc `output-policy/1` (phải giữ nguyên), nên chỉ ghi lại.
- **Usability thật:** `REAL_STUDENT_USABILITY = NOT_MEASURED` ([trạng thái](human_usability_status.json)).

## 6. Hiệu năng

| khía cạnh | phát hiện |
|---|---|
| Nút thắt | Suy luận RapidOCR (~1,5 s của ~1,7 s OCR khi warm). Worker lạnh cộng thêm ~1,0 s import và ~0,8 s nạp model lười. Đọc lại 0,1–0,4 s; đối chiếu, fidelity, parse mỗi bước < 0,1 s ([profile](ocr_bottleneck_profile.json)) |
| Tối ưu | Không triển khai: chưa có phương án nào vừa giảm thời gian vừa giữ fidelity mà không cần Owner chọn đánh đổi RAM |
| Cache | OCR và đọc lại dùng chung một bộ đệm 16 mục. Sau 8 ảnh, OCR của ảnh đầu còn trong cache nhưng phần đọc lại thì không; sau 20 ảnh thì mất cả hai |
| Huỷ giữa chừng | Đo không kết luận được |
| Máy đo | i5-11400H, 6 nhân / 12 luồng, 16 GB, máy dev dùng chung. Máy yếu vật lý: NM |

## 7. Regression ([tổng hợp](full_regression_summary.json))

| gate | kết quả |
|---|---|
| backend pytest canonical | **PASS** — 14262 passed, 7 skipped, 3 deselected, 15 xfailed. Gồm Dev72, C26, height-invariance, continuity, Source Gate, region detection, fidelity, planner, strict xfail. Loại trừ: `postgres`, `external_evidence` |
| frontend `test:wave` | **PASS** — 2018/2018 test, `tsc -b`, production build |
| demo replay / crash audit | **PASS** — 5/5 · 6/6 |
| docs IA | **PASS** |
| publication range | **PASS** |
| freeze verify | **PASS** (`cd9b9f518805d305…`) |
| publication HEAD | **BLOCKED** — 97 pending, như baseline |

Lần chạy đầu có hai gate đỏ; cả hai được lưu lại trong receipt:

- **backend:** 2 test khoá template phê duyệt đỏ do measured system đổi. Xử lý bằng gắn lại template, giữ `PENDING`.
- **frontend:** `vite build` lỗi `EPERM`, vì `frontend/dist/assets` thuộc tài khoản sandbox Codex. Thư mục cũ được chuyển vào `.superpowers/offline-logs/`, không xoá file nào.

## 8. Giới hạn

- Một dataset, toàn bộ là ảnh render; không có ảnh chụp, chữ viết tay, trang nhiều đề.
- Tham chiếu do agent chép; không có H-1.
- Xác nhận là kịch bản tự động, không có thời gian đọc thật của học sinh.
- Không có Vision live, học sinh thật, PostgreSQL hay máy yếu.
- Độ trễ đo trên máy đang chạy ứng dụng khác.
- Recall dữ kiện dùng so khớp chuỗi trên dạng chuẩn hoá, không phải chấm ngữ nghĩa.
