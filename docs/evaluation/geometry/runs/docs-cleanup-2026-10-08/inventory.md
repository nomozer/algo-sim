# Inventory — nội dung → consumer → nghiên cứu → tái lập → hành động

Baseline đã đọc: **180/180** báo cáo lịch sử ở gốc `docs/`; **13.174/13.174** file và **3.097/3.097** đường dẫn folder dưới `docs/evaluation`
(9.708 PNG, 2.509 JSON, 493 log, 280 Markdown, 184 file script/text/dữ liệu khác; 1,711 GB). Việc đọc artifact
theo folder đồng nhất dùng nội dung Markdown, manifest/JSON key, tên ca/ảnh, reference ngược và consumer code/test.
Ảnh được phân loại theo manifest/capture set; không chụp lại và không gọi model.

## 1. Báo cáo gốc `docs/`

| nhóm | số đã đọc | consumer / kết luận nghiên cứu | tái lập | hành động |
|---|---:|---|---|---|
| nghiệm thu/khoá luận/phát hành | 13 | chương kết quả, release và claim alignment | report là lớp diễn giải của artifact hình học | giữ nguyên byte |
| đề từ ảnh | 8 | pipeline ảnh → văn bản → Scene3D, phụ lục đánh giá | cần cho attribution và scorer correction | giữ nguyên byte |
| compiler/họ hình | 23 | topology, prism/cuboid, compiler; chương kiến trúc và correctness | chuỗi preregistration/correction | giữ 22; xoá `GENERIC_RULE_SCENE_LLM_BOUNDARY_AUDIT` thuần catalog Tin học |
| hình cong/V3 | 38 | họ cầu/trụ/nón, acceptance V3; claim hình cong | raw JSON và runner tương ứng còn trong geometry | giữ nguyên byte |
| đo chính xác/khối lõm/thiết diện | 8 | exact kernel và verification | report nối code với replay | giữ nguyên byte |
| Scene3D/mô phỏng/trình bày | 23 | UI/renderer hình học và các audit catalog Tin học | phần hình học còn dùng; 9 report catalog 22 target không còn consumer | giữ 14, xoá 9 report Tin học |
| synthesis/analyze/live | 54 | failure analysis và live measurements hình học | dùng cho chương đánh giá/giới hạn | giữ 52, xoá cặp mechanism-first của catalog Tin học |
| tài liệu/phạm vi/vận hành | 9 | scope migration và provenance | W12 là kế hoạch mạng đã đóng, không còn consumer | giữ 8, xoá `W12_REMAINING` |
| khác | 4 | fact graph, expressiveness, repair, scalar visibility | nối trực tiếp code/test hình học | giữ nguyên byte |

Kết quả: **167 giữ / 13 xoá**. `HISTORICAL_REPORTS.md` là catalog 167 mục còn lại, không còn là lý do tự động giữ.

## 2. Artifact ngoài `evaluation/geometry`

| folder/nhóm | nội dung | consumer | claim/chương hiện dùng | giá trị tái lập | hành động |
|---|---|---|---|---|---|
| `curriculum-ui-admission` | admission/UI 22 target Tin học, 226 ảnh | chỉ inventory cũ | không | catalog và code đã gỡ | xoá 242 file |
| `frontier-fix`, `mechanism-fix` | acceptance + 81 ảnh sửa UI Tin học | chỉ inventory cũ | không | không tái lập sản phẩm hiện tại | xoá 83 file |
| `m16` | 10 JSON đánh giá catalog Tin học | đoạn lịch sử trong ARCHITECTURE_MAP/CODE_INDEX | không có claim trong `research/CLAIM_EVIDENCE_MAP` | runner/evaluator đã gỡ | xoá 10 file; giữ nguyên luật orchestration hiện hành trong docs/test |
| `m17` | RC1/W2–W4, 1.564 file, phần lớn ảnh catalog Tin học | test pin + comment/Makefile lịch sử | không | pin không phải consumer sản phẩm; quyết định scope đã chắt vào RULES §3 | xoá folder + test pin; output runtime chuyển `.tmp` |
| `m18`, `m19`, `m20` | classroom/layout/composition/curriculum Tin học | comment lịch sử, code producer đã gỡ | không | không phục vụ luận văn hình học | xoá 62 file, bỏ link sống |
| `semantic-l5a`, `semantic-vnext` | ảnh/probe renderer 2D IR Tin học | CODE_INDEX lịch sử | không | route/fixtures producer đã gỡ | xoá 39 file |
| `simulation-mechanism-audit`, `viewmode-design-audit`, `ui-baseline` | audit 11 family/22 target và 419 ảnh | hai test/comment tự pin dữ liệu cũ | không | không đo UI hình học hiện tại | xoá 479 file và hai guard chỉ kiểm snapshot retire |
| `tier2-live-pilot` | hai báo cáo pilot trước SEALED | không | chính file nói không phải số luận văn | official result thay thế | xoá 2 file |
| `prompt-freeze` | snapshot prompt Tin học | không | không | thuộc lượt prompt/IR riêng theo yêu cầu user | **giữ tạm, deferred** |
| `semantic-benchmark` | SEALED #1 + `EVALUATION_CANDIDATE.json` sống | freeze/verify scripts, tests, CORRECTNESS, STATUS_LEDGER | giới hạn P1, kết quả A/B và identity candidate | bắt buộc cho seal/candidate | **giữ nguyên toàn bộ** |
| `integration` | 4 ảnh khối cong + 4 JSON journey/refusal | scripts + `PRODUCT_*` reports + CODE_INDEX | tích hợp sản phẩm khối cong | đường dẫn nằm trong byte report cần giữ | **giữ nguyên tên/nội dung**; ngoại lệ path-bound cụ thể |

## 3. `evaluation/geometry`

| nhóm đồng nhất | nội dung → consumer → nghiên cứu | tái lập | hành động |
|---|---|---|---|
| `runs/` (8.711 file lúc baseline) | packages w09–w20 và các run theo việc → EVIDENCE_INDEX/CLAIM_EVIDENCE_MAP → claims C1–C8, B2/D5/D6 và chương 4–5 | manifest, raw result, ảnh duyệt, correction chain | giữ nguyên byte/tên; run ID và đường dẫn nội bộ ràng buộc |
| compiler/solid (`generic-tier-*`, `cuboid-*`, `rectangular-*`, `phase7*`, `holdout`, `expectations`) | preregistration, topology, prism/cuboid, holdout → báo cáo compiler/acceptance → chương phương pháp + correctness | raw cases/oracle/measurement | giữ nguyên byte |
| curved (`curved-*`, `oblique-*`, `radius-*`) | replay/acceptance cầu-trụ-nón → 38 report hình cong → claim family coverage/V3 | chuỗi before/after và manifest live | giữ nguyên byte |
| relation/exact/provenance (`segment-*`, `point-*`, `frame-*`, `divide-*`, `ratio-*`, `obligation-*`) | checker và repair → report correctness → chương kiến trúc/giới hạn | raw replay cần attribution | giữ nguyên byte |
| Scene3D/UI (`scene3d-*`, `display-*`, `product-*`, `final-system-release`) | ảnh/JSON browser → visual/presentation reports → chương giao diện | browser evidence còn được claim/review dùng | giữ nguyên byte |
| photo problem (659 file) | corpus, live/offline traces, redaction proofs → 8 report ảnh → phụ lục pipeline ảnh | cần đối soát request/scorer | giữ nguyên byte |
| dev/stability/probe series | raw canary, failure reproduction và retries → các report chẩn đoán → phần giới hạn/model variance | thứ tự trước/sau là dữ liệu, không phải bản trùng | giữ nguyên byte |
| `manual-demo`, `manual-demo-5` | demo đang được script đọc và kiểm point projection | producer còn chạy | đổi thật → `geometry-demo`, `point-projection-check`; byte artifact giữ nguyên |
| `manual-demo-2/3/4/6` | ảnh lặp trung gian, không report/code/index consumer | không | xoá 42 file; `manual-demo-5` là kết quả có consumer nên tách giữ |
| `worktree-recovery` | inventory + recovered screenshots của correction run → EVIDENCE_INDEX wave occlusion | inventory chứng minh không mất file độc nhất | giữ nguyên byte |
| `custodian/__pycache__` | bytecode ignored tái sinh | không | không | xoá file local + folder rỗng; `geometry_oracle.py` giữ |

Ngoại lệ đường dẫn: một số artifact provenance còn dùng (ví dụ classification JSON, báo cáo readiness và inventory của các run cũ)
chứa chuỗi đường dẫn `m16`–`m20`, `manual-demo*` hoặc folder Tin học tại đúng thời điểm đo. Đây không phải link sống hay consumer;
chúng được giữ nguyên byte để không viết lại lịch sử. Khả năng phục hồi các file đã xoá nằm ở commit `4acd1f61`, không bằng compatibility
stub trong cây hiện tại. Riêng `integration` là path-bound còn consumer thật nên giữ nguyên cả tên lẫn byte.

## 4. Tổng hành động

- Xoá tracked: **2.538 file** (157.329.129 byte / 150,04 MiB), gồm 2.523 artifact, 13 report và 2 test chỉ pin snapshot retire; 221 đường dẫn folder tracked biến mất.
- Rename tracked: **22 file** trong 2 folder (`manual-demo` → `geometry-demo`; `manual-demo-5` → `point-projection-check`).
- Giữ: 167 report; 10.650 tracked/committed artifact còn lại trong `docs/evaluation` (file ignored không tính).
- Dọn local: 1 bytecode ignored và folder `__pycache__` rỗng; tổng cộng 222 đường dẫn folder baseline không còn.
- Không sửa byte artifact giữ lại; thay đổi nội dung chỉ ở policy, index, consumer/comment/test hiện hành và run cleanup này.
- Mọi deletion khôi phục được từ `4acd1f61` bằng `git show`; không rewrite history.
