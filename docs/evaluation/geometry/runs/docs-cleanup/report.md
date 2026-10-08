# docs-cleanup — báo cáo hợp nhất

Run `docs-cleanup` hợp nhất ba trách nhiệm đã cùng phạm vi: cleanup tài liệu/tên, artifact cleanup và report
organization. Metadata độc lập không bị ghi đè: `run.json`, `run-artifact-cleanup.json`,
`run-report-organization.json`; log từng phép kiểm ở `diagnostics/`. Toàn lượt: 0 model call, 0 screenshot.

## 1. Inventory và xử lý vật lý

| phạm vi | đã phân loại | giữ | xoá | đổi tên/chuyển |
|---|---:|---:|---:|---:|
| report | 180/180 | 167 | 13 | 156 move tổ chức; 1 report đổi sang tên chức năng |
| artifact | 13.174/13.174 | 10.650 | 2.523 artifact + 2 test pin | 2 folder / 22 file ở artifact cleanup |
| folder path | 3.097/3.097 | theo consumer/claim | folder rỗng sau kiểm | 2 hồ sơ cleanup dư được gộp rồi xoá |

Phần Tin học retire (`curriculum-ui-admission`, m16–m20 không còn consumer, `semantic-l5a/vnext`, audit UI catalog,
demo trùng) được xoá sau khi kiểm code/test/tooling/docs/manifest; Git commit `4acd1f61` là đường khôi phục. Nhóm trộn
được xử lý theo file: 167 report và 10.650 artifact còn phục vụ kiến trúc, correctness, luận văn hoặc tái lập được giữ.

167 report được bố trí: 33 cạnh package đo, 123 tại `docs/evaluation/reports/`, 11 ngoại lệ path-bound ở gốc; 167/167
blob report giữ nguyên byte. `CURRENT_ARCHITECTURE_GAP_AUDIT.md` đổi R100 thành
`architecture-gap-audit-2026-09.md`; tiêu đề lịch sử trong blob không sửa. Hai folder `docs-cleanup-2026-10-08` và
`docs-organization` đã bị gỡ sau khi manifest/log độc lập được chuyển nguyên byte vào run này.

Các ngoại lệ giữ tên có căn cứ:

- `n04-targeted-rejection-registry-v2-preregistration`: scripts/tests đọc package; N04 là case preregistered, V2 là
  schema registry; 14 artifact tự ghim path.
- `second-family-*`: correction/preregistration/live-reconciliation chain còn được scripts, tests và research registry
  dùng.
- `SEMANTIC_PROGRAM_ROUTE_DESIGN/PLAN`: RULES §11 trích design §3.3; plan giữ giao thức SEALED mà test còn pin. Đây là
  thiết kế legacy có consumer, không phải contract runtime hiện hành.

## 2. Tên và hồ sơ cleanup trước đó

Các commit trước trong cùng run vẫn có hiệu lực: `a993aa8f` đổi tên 123 hàm pytest + 118 tiêu đề test theo hành vi;
`c1a291ba` gỡ 17 luật CSS chết; `8c66249d` gỡ `RULES_v0.3.md` và guard chỉ canh bản đó; `9efb8af6` đưa contract còn
hiệu lực về `docs/architecture/`, xoá plan/spec đã được thực thi hoặc hết consumer và cập nhật luật vị trí tài liệu.
Chi tiết từng file/consumer nằm ở `inventory.md`; bảng tên cũ → mới ở `docs/evaluation/RUN_NAMING.md`.

Tag `SEMANTIC_PROGRAM_CONTRACT_V1` là lightweight tag trỏ commit `8dbd5bc7`, nơi khởi tạo contract/validator/schema V1.
Không runtime/script hiện hành nào resolve tag; contract đã tiến hoá. Tag được giữ như mốc lịch sử, còn authority hiện
hành là model Pydantic + hai schema được đồng bộ.

## 3. Kiến trúc thực tế

`docs/ARCHITECTURE_MAP.md` có bảng yêu cầu → đã có → còn thiếu → caller thật → bằng chứng. Tuyến sản phẩm là:

`đề/ảnh + checkpoint` → `RequestContract` → mặc định `LLM_ONLY` sinh `SemanticProgram` → validator/interpreter/kernel +
cổng grounding/assumption/construction/postcondition/visual → response envelope/store → frontend Scene3D.

AI đọc nghĩa và chọn primitive; backend sở hữu trạng thái, hình học, kiểm chứng và quyết định phục vụ. FactGraph/compiler
hiện chỉ là route opt-in cho miền hẹp; OCR tổng quát, reflection và compiler-first chưa được tuyên bố hoàn tất.

## 4. Lát cắt backend duy nhất

Đóng `ISSUE-ARCH-MISSING-SIZE-REASON-ON-AFFINE-CHART` cho dependency slice `measure(volume)` của chóp tam giác đều T8.
`assumption_gate` tái sử dụng ràng buộc nguồn, phép đo độ dài và graph phụ thuộc hiện có để xác định cạnh đáy/chiều cao
thiếu theo `V = sqrt(3)*b²*h/12`. Đầu ra vẫn `unsupported`; chỉ nguyên nhân đổi từ
`ASSUMPTION_INVARIANCE_UNPROVEN / UNKNOWN` thành `ASSUMPTION_DETERMINES_ANSWER / SOURCE` với subject cụ thể.

Caller thật: `POST /api/analyze` → pipeline → route → assumption gate. Miền giới hạn: một chóp tam giác đều có tên,
văn bản nguồn đọc trọn, ràng buộc T8 được nhận diện, không mâu thuẫn; không áp dụng cho tứ diện, họ mới hoặc constraint
ngoài từ vựng đóng. Vì cached refusal envelope đổi, `CACHE_VERSION` tăng 117 → 118. Prompt, grammar card, schema,
capability và semantic environment không đổi; candidate mới `7f3f042309dd1c54…`, 102 file, product `f967ba24`.

## 5. Kiểm chứng và Git

- Focused backend/API trước commit: 46 passed; sync regression sau khi cập nhật fixture/guard: 413 passed.
- Detached clean checkout `838237fe`: backend **7239 passed, 1 skipped, 2 deselected**; frontend **67 files / 1023
  tests passed**; `tsc -b` + Vite build đạt.
- Docs audit PASS: 0 link hỏng, 0 stale path, 167 report catalogued, không file gốc chưa phân lớp.
- Candidate verify `7f3f042309dd1c54…` / 102 file; cache verify 118 / `b1714b566e25c912…`; `diff --check` sạch.
- Lần thử backend đầu bị ACL basetemp rồi timeout được giữ riêng ở `final-backend-temp-acl-failed.log` và không tính là
  kết quả. Gate hợp lệ dùng temp ngoài checkout, log `final-backend.log`, exit code 0.
- Commit: `f967ba24` (product + consolidation), `267c195a` (candidate), `838237fe` (consumer/guard sync). Không push,
  merge, PR hay sửa lịch sử. `frontend/public/favicon.svg` vẫn ngoài staging.

Prompt/IR và `semantic_*` được hoãn đúng yêu cầu, theo issue có caller evidence riêng. Duyệt hình vẫn **NOT_APPROVED**;
D5 mobile chưa được người dùng quyết định.

## 6. Nhiệm vụ sản phẩm kế tiếp duy nhất

Thực hiện human visual review trên các gói hiện có (`exact-dimensions`, `regular-triangular-pyramid-w01`, W5/W4) và
chốt phương án D5 mobile; chưa mở họ hình hay cleanup mới trước quyết định đó.
