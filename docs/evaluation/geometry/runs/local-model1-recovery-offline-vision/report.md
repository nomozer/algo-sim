# AXO HYBRID /14 — Local Model 1 recovery & offline vision (takeover report)

Run `local-model1-recovery-offline-vision` · branch `feat/local-model1-recovery-offline-vision` (shared worktree
`.superpowers/worktrees/simulation-intent-slm-recovery`) · not merged, not pushed · `main` unchanged (`bc6ff5e33`).
Started by a Codex session (base `fd53c26ab`, `/13` final); taken over on 2026-11-21 after that session hit its usage limit.

## 1. Kết luận

| cổng | kết quả |
|---|---|
| `FULL_PRODUCT_GATE_PASS` (candidate 154, `5c65f795e`, `7988f838…`, 127 file) | **PASS** — backend `15,078 passed / 0 failed`, vitest `2,345/2,345`, build, demo replay, demo crash surface (`1,202.3 s`, exit 0) — [`FULL_T3_CACHE154_RECEIPT.json`](FULL_T3_CACHE154_RECEIPT.json) |
| Full T3 trên candidate 153 (`df31847d`) | **FAIL** — lượt Codex bị ngắt ở 48% (`TEST_INTERRUPTED`); lượt hợp lệ: 2 lỗi vệ sinh bằng chứng (freeze trên cây bẩn, bảng danh tính còn 152) + build EPERM do môi trường — [`FULL_T3_CACHE153_RECEIPT.json`](FULL_T3_CACHE153_RECEIPT.json) |
| `LIVE_SIMULATION_ACCEPTED` (Holdout-2, prospective) | **FALSE** — hoàn tất `29/38 = 0.763 < 0.85` |
| SLM (Holdout-2) | **FALSE** — `2/10 = 0.20 < 0.30`, `2 < 5` cảnh |
| An toàn (Holdout-2 + Holdout-1) | `26/26` ca âm từ chối an toàn; `0` phục vụ sai / vi phạm grounding / quan hệ chưa kiểm / mục tiêu số bịa / số sai; `0` lượt gọi AI ngoài |
| `LOCAL_VISION_REPLACEMENT_VERIFIED` | **FALSE** (ảnh/scan: OCR cục bộ fail-closed đúng nhưng chưa đủ tin cậy; PDF lẫn hình luôn đòi duyệt) |
| `LOCAL_MODEL1_REPLACEMENT_VERIFIED` | **FALSE** |
| `MAIN_MERGE_READY` | **FALSE** — cần quyết định của owner; ngưỡng nghiệm thu chưa đạt |

## 2. Khôi phục trạng thái

- Git: branch `/14` là `feat/local-model1-recovery-offline-vision`, HEAD lúc tiếp quản `4d145f9df` (Codex: `cb88944e4..4d145f9df`, 7 commit),
  2 file kết quả chưa commit (`LIVE_ACCEPTANCE_RESULTS.json`, `OFFLINE_VISION_VALIDATION.json`) — commit nguyên trạng ở `25ead716c`.
- T3 "đang chạy" của Codex: không còn tiến trình; log dừng ở 48% pytest lúc 08:51, đúng lúc host của Codex khởi động lại
  (`The pipe is being closed`) ⇒ `TEST_INTERRUPTED`, không phải lỗi sản phẩm.
- `frontend/dist/v14-cache152|153` do tài khoản sandbox Codex tạo, tài khoản này không xoá được ⇒ chuyển nguyên vẹn sang
  `D:/tmp/codex-v14-dist-preview` (bằng chứng trình duyệt của lượt 153).

## 3. Chẩn đoán CACHE 153 (Holdout-1) — tầng lỗi đầu tiên

Chi tiết từng ca: [`FIRST_FAILING_LAYER_AUDIT.json`](FIRST_FAILING_LAYER_AUDIT.json).

- **SLM 1/16 không phải do trọng số model**: 9/16 ca SLM-required có bản hạ `GROUNDED_AND_LOWERED` đúng tập phép, rồi Source Gate
  từ chối vì văn phạm câu đóng của chính nó không đọc được câu (`UNGROUNDED_VALUE`, `SOURCE_PREMISE_UNREAD`, `NOT_ASKED_IN_SOURCE`).
  5/16 model tự báo mơ hồ (`SLM_REFUSED`), 1/16 validator chặn một giá trị đúng ("AB và AC dài 4 và 7"), 1/16 phục vụ (T15).
  Không đổi model (`RETAIN_AXOV9`): lỗi chủ yếu là tầng đọc/kiểm nguồn.
- **File 0/10 không phải "OCR sai hết"**: OCR là tầng lỗi đầu tiên ở **1** ca (I01: mất mọi dấu "="); **2** ca là lỗi dữ liệu đánh giá
  (I02, I05: font Arial không có glyph `⟂`/`⊥`, ảnh chứa ô □ — quan hệ không có trong đầu vào); 2 ca dừng ở chuẩn bị (I04 cờ phân số
  giả do ảnh mờ; P03 chọn trang), 1 ca ở duyệt dữ kiện hình (P04, theo thiết kế); 4 ca OCR/đọc tài liệu **đúng** nhưng văn bản bị
  parser/Gate từ chối như ca văn bản. Gold-OCR intervention: văn bản gốc của I01, P03 được phục vụ tất định.

## 4. Sửa (một thẩm quyền mỗi luật) — `5c65f795e`, `CACHE_VERSION` 153 → 154

| luật | nơi | ca đối chứng vẫn bị từ chối |
|---|---|---|
| `⟂` (U+27C2) → `⊥`, một-đổi-một | `normalize_problem_text` (`local_geometry_parser.py`) | `KL không ⟂ (LMNP)` |
| "trong đó" là lời dẫn dữ kiện | `_C_DAU` (`registry.py`) | — |
| câu mở bằng yêu cầu đại lượng **của chính khối** ("Tính thể tích khối chóp … biết/có …") | `_C_KHOI_HOI` trong `_phan_tich_cau` | yêu cầu mang số riêng (chiều cao 5 ≠ KL = 4); yêu cầu về tam giác |
| cụm định vị khối sau đối tượng hỏi; "có" mở dữ kiện ngay sau nhãn | `_SAU_HOP_LE`, `_SAU_SAU_NHAN`, `_NHAN_CUOI` | "khi DG thay đổi"; "có bằng 4 không"; "có vượt quá 5 không?" |

Test: `test_model1_residual_phrasings.py` (`5` ca dương đỏ trước sửa / xanh sau, `6` ca đối chứng, `153:route-d` MISS). Ba test đột
biến (`test_hybrid_ask_operand_binding`, `test_premise_sentence_generalization`, `test_source_gate_clause_role`) đỏ ở bản đầu — bản đầu
làm văn phạm đuôi đóng chấp nhận câu có/không khi bỏ lớp kiểm có/không; đã sửa bằng loại trừ tường minh và giữ nguyên neo.

Không nới Source Gate: mọi luật mới là văn phạm đóng, giá trị vai trò vẫn chỉ gắn qua câu đọc trọn. Không đổi model, không fine-tune,
không chạm Construction Planner `/2`, Model 2, run `/5–/13`, `§17`, `§19`.

## 5. Nghiệm thu

| tập | phân loại | candidate | hoàn tất | văn bản | file | ca âm | SLM |
|---|---|---|---|---|---|---|---|
| Holdout-1 (41) | `NEW_PROSPECTIVE` ở 153; **regression đã lộ** ở 154 | 153 → 154 | 3/28 → **4/28** | 3/18 → 4/18 | 0/10 → 0/10 | 13/13 → 13/13 | 1/16 → 1/16 |
| Holdout-2 (51) | prospective, tác giả là agent, viết **sau** chẩn đoán, **trước** mọi sửa ([`holdout-2/PROVENANCE.json`](holdout-2/PROVENANCE.json)) | 154 | **29/38 = 0.763** | 21/28 | 8/10 | 13/13 | 2/10 |

Holdout-2 không có lượt đo trình duyệt trên 153; baseline duy nhất là phân tầng parser lúc đóng băng (18/28 COMPLETE ở 153 → 20/28 ở
154). Vì vậy 0.763 **không** được trình bày như mức cải thiện do bản sửa — phần lớn đề Holdout-2 viết theo dạng sách giáo khoa mà
parser vốn đã đọc được. Holdout-2 cũng không mù với các họ câu đã thăm dò trước khi ghi hash (`⟂`, câu hỏi đứng trước).

Ca Holdout-2 chưa hoàn tất: B10 (một chủ ngữ hai vị ngữ), B12/B15 ("ba cạnh / các cạnh … đôi một vuông góc, độ dài …" — SLM báo mơ hồ),
B14 ("vuông góc với nhau từng đôi một"), B17 ("OA = OB = 3"), B18 (`OA ⊥ (OBC)` + `OB ⊥ OC` ⇒ `MISSING_DIMENSION`, khoảng trống năng lực),
B22 ("chiều cao lăng trụ bằng 5"), J03 (lỗi dữ liệu: glyph `⊥` thiếu, công khai trước khi đo), Q04 (duyệt dữ kiện hình theo thiết kế).

Kết quả máy: [`holdout-2/LIVE_ACCEPTANCE_RESULTS.json`](holdout-2/LIVE_ACCEPTANCE_RESULTS.json),
[`LIVE_REGRESSION_HOLDOUT1_CACHE154.json`](LIVE_REGRESSION_HOLDOUT1_CACHE154.json) (biên nhận thô ở `.superpowers/offline-logs/…/candidate154-h2-run2`,
`candidate154-h1`; lượt `candidate154-h2` đầu hỏng vì build preview thiếu `--base`, 0 ca được đo).

## 6. Vai trò của Gemini trong phạm vi Axo (sau /14)

| vai trò | thay thế cục bộ | trạng thái |
|---|---|---|
| Hiểu đề văn bản → dữ kiện có kiểu | parser tất định + AxoV9 + Source Gate | `PARTIAL` — an toàn (0 phục vụ sai) nhưng độ phủ diễn đạt dưới ngưỡng |
| Đọc tài liệu số (PDF text, DOCX) | `document_reader` | đọc đúng nguyên văn; độ phủ phụ thuộc parser |
| Đọc ảnh / PDF scan | OCR cục bộ hai bộ đọc + cổng bất định | `PARTIAL` — fail-closed đúng; mất "=", chữ khi nghiêng, cờ phân số giả |
| Dữ kiện từ hình vẽ | không có | `NOT_VERIFIED` — luôn đòi người học duyệt (đúng R0) |
| Tương đương Gemini, độc lập bên ngoài, phần cứng đích | — | `NOT_MEASURED` |

## 7. Việc tiếp theo (đề xuất, cần owner)

1. Họ câu còn hở (theo thứ tự tần suất ở hai tập): "đôi một / từng đôi (một) vuông góc" với danh sách độ dài đi kèm, một chủ ngữ hai vị
   ngữ ("SA dài 4 và vuông góc với đáy"), giá trị "lần lượt / tương ứng", đẳng thức chuỗi, "chiều cao (lăng trụ) bằng", yêu cầu mô phỏng
   trần ("Hãy mô phỏng."), và phủ dữ kiện trong câu hỏi ở cổng ngữ cảnh câu hỏi; `OA ⊥ (OBC)` + `OB ⊥ OC` ở planner.
2. Bộ dựng đề ảnh: font có glyph `⊥` (ví dụ Cambria Math / Segoe UI Symbol) cho mọi tập sau — không sửa Holdout-1/2 đã đóng băng.
3. OCR: dấu "=" bị mất, xoay ảnh, cờ `FRACTION_STRUCTURE_LOSS` giả trên ảnh mờ.
4. Một tập prospective mới khoá trước khi sửa tiếp; Holdout-1 và Holdout-2 nay đều đã lộ.
5. Merge `main`, Construction Planner `/2`, Model 2: chỉ sau khi Model 1 đạt ngưỡng và owner phê duyệt.
