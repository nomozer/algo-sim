# Protocol & Harness Pilot Ngôn ngữ Học sinh `S-2` (Continuation 11 — §5.2)

> **Trạng thái thực thi Live**: **`NOT_EXECUTED` (`0` live provider calls, ngân sách live = `$0`)**.
> **Bộ chấm điểm tất định offline**: `backend/scripts/score_s2_student_language_pilot.py` + `backend/tests/geometry/test_s2_student_language_pilot_harness.py`.
> **Cô lập tuyệt đối**: Pilot phát triển `S-2` **tách biệt hoàn toàn** với đợt đánh giá đối chứng 60 bài live (`live-evaluation-protocol.md`) và với các tập Independent Holdout (Waves 1–3). Không bao giờ dùng ví dụ development làm independent holdout.

---

## 1. Mục tiêu Nghiên cứu của Pilot `S-2`

Đo lường thực nghiệm hành vi của tầng trích xuất LLM (`/4` `TypedFactNextPayloadV2` + `unresolved` + `route-d-clarification/1`) trên văn phong học sinh thực tế (viết tắt, chỉ yêu cầu vẽ/mô phỏng `SL-1`, câu hỏi thiếu toán hạng `SL-2`, thuật ngữ sai, gõ lệch nhẹ, nhiều câu hỏi gộp) mà gold-fact replay offline không thể đo thay được.

---

## 2. Tám Chỉ số Đo lường Bắt buộc (§5.2)

Bộ chấm `backend/scripts/score_s2_student_language_pilot.py` tính toán tất định 8 chỉ số chuẩn hóa:

1. **`extraction_accuracy`**: Tỷ lệ ca trích xuất đúng toàn bộ chữ ký dữ kiện hình học (khối, ràng buộc hình dạng, quan hệ vuông góc/song song, kích thước số) so với nhãn chuẩn.
2. **`goal_completeness`**: Tỷ lệ ca trích xuất đủ 100% mục tiêu mô phỏng/tính toán trong đề (không rơi vế câu hỏi phụ).
3. **`operand_preservation`**: Tỷ lệ ca bảo toàn chính xác tên đỉnh, giá trị số và trích dẫn `quote` nguyên văn trong `raw_source` (`quotes_verbatim_in_raw = True`).
4. **`ambiguity_detection`**: Trên tập ca thực sự mơ hồ/thiếu toán hạng, tỷ lệ hệ thống phát hiện đúng sự mơ hồ (`CLARIFY` hoặc gắn cờ `unresolved`).
5. **`clarification_correctness`**: Trên tập ca hệ thống trả `CLARIFY`, tỷ lệ ca thực sự cần làm rõ **và** trả đúng mã lý do làm rõ hợp lệ.
6. **`false_clarification`**: Trên tập ca rõ nghĩa (đủ dữ kiện hoặc phải từ chối thẳng), tỷ lệ hệ thống hỏi lại `CLARIFY` sai (chống lạm dụng `unresolved`).
7. **`unsupported_classification`**: Trên tập ca ngoài miền hỗ trợ (Oxyz, chóp cụt, phép biến hình, quỹ tích cực trị, ...), tỷ lệ hệ thống phân loại đúng về nhánh từ chối `unsupported` an toàn.
8. **`wrong_served_end_to_end`**: Tỷ lệ ca trả `SERVED` sai trên toàn tập đo được (trả `SERVED` cho đề mơ hồ/mâu thuẫn/ngoài miền, rơi mục tiêu, sai đáp số chính xác, hoặc thiếu chứng chỉ Kernel). **Ngưỡng chấp nhận bắt buộc: `wrong_served_end_to_end == 0`**.

Tuân thủ `AGENTS.md` §4: mọi bản ghi lỗi mạng/timeout hoặc chưa chạy live đều được ghi nhận tường minh là `"NOT_MEASURED"` / `"NOT_RECOVERABLE"` / `"UNKNOWN"`, tuyệt đối không gán bằng `0`.

---

## 3. Phân tầng Tập mẫu Pilot Đề xuất (36 câu phát triển riêng, tách khỏi 60 bài Live Paired)

| Phân tầng (`stratum`) | Số câu đề xuất | Nội dung kiểm định | Kết quả chuẩn kỳ vọng |
| --- | ---: | --- | --- |
| `S2-A: Simulation-only (SL-1)` | 6 | *"Vẽ hình chóp đều..."*, *"Mô phỏng lăng trụ đứng..."* đủ kích thước | `SERVED` (dựng Scene3D đúng, 0 câu hỏi số giả) |
| `S2-B: Compound Multi-Goal` | 6 | Vẽ thiết diện + tính diện tích + tính khoảng cách trong cùng đề | `SERVED` (đủ mọi goal, 0 dropped goal) |
| `S2-C: Incomplete / Elliptical Goal (SL-2)` | 6 | *"Vẽ hình rồi tính."*, *"Tính góc giữa SB và mặt phẳng."* | `CLARIFY` (`route-d-clarification/1`) |
| `S2-D: Contradictory Shape / Terminological Error` | 6 | Hình lập phương có đáy chữ nhật `2×3` (PE-2), cạnh đáy vuông góc mặt đáy | `REFUSED` (`INCONSISTENT_FACTS` / `SOURCE_MISMATCH`) |
| `S2-E: Out-of-Scope School Topics` | 6 | Tọa độ `Oxyz`, hình chóp cụt, cực trị thể tích | `REFUSED_UNSUPPORTED` |
| `S2-F: Colloquial / Noisy Phrasing` | 6 | Văn phong học sinh tự nhiên có dấu nhưng viết gọn (`mp(SBC)`, `đt SC`, `k/c`) | `SERVED` hoặc `CLARIFY` an toàn (`0` wrong-served) |
| **Tổng cộng** | **36** | **1 request / câu (`max 36 requests`, dừng ngay nếu gặp lỗi hệ thống)** | **`wrong_served_end_to_end == 0`** |

---

## 4. Sáu Cổng Cấp quyền Bắt buộc của Owner trước khi Chạy Live (§5.2)

Công cụ chấm điểm khóa cứng `ALLOW_LIVE_AI=0`. Không một request live nào được phép gửi đi khi Owner chưa phê duyệt đủ **6 thông số**:

1. **Quyền thực hiện (`Execution Authorization`)**: Owner GO tường minh cho `S-2 Pilot` (riêng hoặc kèm 60 bài paired evaluation).
2. **Model (`Model ID`)**: Tên model cụ thể (ví dụ `gemini-2.5-flash` hoặc model được chỉ định).
3. **Project / API Key hợp lệ**: Xác nhận nguồn khóa/project được phép dùng.
4. **Giới hạn số lượng request (`Hard Request Cap`)**: Trần cứng `<= 36` requests kèm circuit-breaker dừng ngay sau 3 lỗi liên tiếp.
5. **Ngân sách tối đa (`Hard Budget Cap`)**: Trần chi phí USD cụ thể trước khi chạy.
6. **Phạm vi dữ liệu (`Data Scope`)**: Xác nhận tập 36 câu pilot phát triển (không chạm tập Holdout độc lập).

---

## 5. Sửa đổi trước khi chạy — Continuation 12 (2026-11-01), vẫn `0` live call

§1–§4 giữ nguyên. Phần này thêm đúng những gì §2–§4 thiếu để chạy được khi Owner GO; đều cố định **trước** mọi lượt live.

**5.1 Corpus** — `s2-student-language-pilot-corpus.json` (sinh bởi `tools/build_s2_pilot_corpus.py`, ghi một lần),
`corpus_sha256 = 3f1682bd6adbc5f21cb504a6b25f6ccc226c9b0d791f05fcb2eeb6a9a6fc6791`. 36 ca, 6 tầng × 6 đúng §3.
21 ca lấy nguyên văn bản + gold + kỳ vọng viết tay của `student_language_probe.py` (C10); 15 ca viết mới cho tầng
probe thiếu (E: Oxyz, chóp cụt, cực trị, quỹ tích, phép tịnh tiến, bài toán thực tế; F: `k/c`, `mp(SBC)`, `đt`;
C: góc thiếu mặt phẳng, "Vẽ hình rồi tính.", hình vuông thiếu cạnh; D: lập phương đáy chữ nhật/cao lệch, cạnh đáy ⊥ đáy,
đường chéo sai). Oracle là chuỗi chính xác viết tay; với ca tái dùng, builder đối chiếu từng giá trị với oracle bình
phương/cos² độc lập của probe. **Tác giả: implementer (agent) — không độc lập, không held-out.** Văn bản đã có trong kho:
pilot đo cách model đọc chữ, không đo tổng quát hoá của tầng tất định.

**5.2 Runner** — `backend/scripts/run_s2_student_language_pilot.py` (+ `tests/geometry/test_s2_student_language_pilot_runner.py`,
28 test, 5 mutant đều bị giết). Một arm: đường opt-in Hybrid `/4` (domain gate → trích xuất → Source Gate → planner →
engine → Adapter /4), 1 request mỗi ca. Budget USD theo payload, guard send, transport (retry/timeout như `call_gemini`)
**là của** `run_paired_route_evaluation.py`, không chép. Scorer 8 chỉ số không đổi; runner chỉ dựng bản ghi:
- `facts_signature` / `extracted_goals` / `operands`: MỘT phép chiếu (`project`) cho cả gold lẫn observed — bỏ id, quote,
  thứ tự; id khối/thiết diện thay bằng ký hiệu. Chỉ có trên ca có gold không chứa `unresolved` (khi có `unresolved`,
  cả payload bị từ chối nên dữ kiện đi kèm không xác định). So khớp **nghiêm ngặt về dạng**: hai cách trích tương đương
  khác `kind` premise bị tính là khác — `extraction_accuracy` là cận dưới của độ đúng ngữ nghĩa.
- `clarification_code` = `nlu_class` của `route-d-clarification/1` (server viết, từ vựng đóng). `unresolved` loại
  `unsupported` không có câu hỏi ⇒ `REFUSED` + mã unsupported, không phải `CLARIFY` (luật của server).
- `answers` = đại lượng mục tiêu người học thấy, theo loại, so như số chính xác. `certificate_verified` = engine `VERIFIED`.
- Lỗi hạ tầng (`HYBRID_INFRASTRUCTURE` của harness paired) ⇒ `NOT_RECOVERABLE`, không bao giờ thành 0.

**5.3 Chỉ số phụ (ngoài 8 chỉ số §2)** — scorer không có false refusal: gold replay cho thấy cả 8 chỉ số hoàn hảo trong
khi 3 ca phải SERVED bị từ chối. Directive Master §V đòi end-to-end, nên runner báo cạnh 8 chỉ số, không thay chúng:
`end_to_end_correct`, `false_refusal` (trên ca kỳ vọng SERVED), theo tầng, `gold_replay_ceiling`, và `attribution` mỗi
dòng hỏng: `INFRASTRUCTURE` · `DETERMINISTIC_LAYER_REPRODUCED_WITH_GOLD` (gold cũng hỏng như vậy) · `DOMAIN_GATE` ·
`LLM_EXTRACTION_DIFFERS_FROM_GOLD` · `UNATTRIBUTED`. Định nghĩa cố định trong mã trước khi chạy.

**5.4 Mốc quy lỗi (gold replay, `s2-pilot-gold-replay.jsonl`, 0 request)** — end-to-end 33/36; 0 wrong-served;
3 false refusal, cả ba tại Source Gate trên **gold**: `S07_typo_tone` (`UNGROUNDED_VALUE`, "hình chop"),
`F05_kc_mp_shorthand` và `F06_dt_mp_shorthand` (`SOURCE_OBJECT_MISMATCH`: `k/c`, `mp`, `đt` không được đọc là tên
đối tượng). Lượt live không thể vượt 33/36; ba ca này không được tính là lỗi của model *khi lượt live hỏng giống gold* (cùng trạng
thái và mã — luật đã chặt lại ở §5.8–§5.9). Không sửa product trước pilot:
sửa sẽ đổi candidate mà approval bind vào, và chưa có bằng chứng tần suất — pilot là phép đo đó.

**5.5 Cổng §4 thành trường approval** (Owner ghi; runner không bao giờ ghi): `owner_decision = "APPROVED_BY_USER"`,
`pilot = "S-2"`, `model`, `paid_project_confirmed = true`, `max_requests` (số nguyên 1..36, tính cả retry),
`max_usd`, `input_usd_per_million`, `output_usd_per_million`, `corpus_sha256` (phạm vi dữ liệu), và các giá trị
`measured_system`, `runner_sha256`, `paired_harness_sha256` do `--manifest` in ra **trên đúng cây sẽ chạy**
(`core.autocrlf=true`: hash là của byte thô trong cây đó). Từ chối trước request đầu nếu thiếu/lệch bất kỳ trường nào,
nếu `max_requests × ước tính mỗi request > max_usd`, hoặc thiếu `ALLOW_LIVE_AI=1` + `GEMINI_API_KEY`.

**5.6 Dừng** — trần request, trần USD (dự trữ trần của chính payload trước mỗi send), provider block, 3 lỗi hạ tầng
liên tiếp, đổi danh tính. Dừng giữa chừng ⇒ `completed = false`, báo `INCOMPLETE`, không báo thành công.

**5.7 Chi phí ước tính** (giá 0.30/2.50 USD mỗi triệu token, `provider-facts.md`): trần mỗi request ≈ USD 0.0244
(input ≤ byte payload, output ≤ 8 192 token của `/4`), 36 request ≈ USD 0.88. Chi phí thật lấy từ `usageMetadata`; trước
khi chạy là `NOT_MEASURED`.

**5.8 Review vòng 1 (fresh-context, cùng continuation; vẫn trước mọi lượt live)** — verdict `NOT_READY`, 0 BLOCKER,
3 MAJOR, 6 MINOR. Mọi MAJOR đã sửa, có test khoá và lỗi tiêm. Định nghĩa thay đổi so với §5.2–§5.3:
- **M1:** thứ tự nhãn của toán hạng không có thứ tự (đầu mút đoạn/đường, nhãn mặt phẳng, cặp `line1/line2` và
  `plane1/plane2`) được chuẩn hoá trong `project`. Thứ tự đa giác vẫn giữ. Trước đó, "CS" thay cho "SC" làm một ca đúng
  thành wrong-served.
- **M2:** `REFUSED_INCONSISTENT` chỉ đúng end-to-end khi nhóm từ chối là `INVALID_DATA` (cùng luật `CONTRADICTORY_DATA`
  của harness paired), không phải mọi lần từ chối.
- **M3:** chỉ quy cho tầng tất định khi gold kết thúc **cùng** trạng thái và mã. Một ca SERVED không bao giờ được miễn
  lỗi; quote không nguyên văn quy về trích xuất.
- **m1:** `max_usd` và hai giá phải là số hữu hạn, dương, không phải bool (NaN hay ≤ 0 sẽ vô hiệu trần USD).
  `max_requests` phải là số nguyên thật.
- **m3:** `spent_reported_usd = UNKNOWN` nếu có dòng thiếu usage; dòng không gửi request nào có chi phí 0.
- **Nit:** summary có `run_status` `COMPLETE` / `INCOMPLETE`.

m2 giữ nguyên có chủ đích: `owner_decision` chỉ kiểm ở `authorize_live`, vì test không bao giờ được ghi giá trị
approval. Approval nay là template `PENDING_OWNER_DECISION` cộng một lệnh khoá theo blob (m6; `owner-go-request.md`).
Tần suất ở bản đính chính `/4` được sửa thành 3/60, có biên nhận (m4).

Gold replay theo định nghĩa mới: `s2-pilot-gold-replay-r1.jsonl`, **thay thế** `s2-pilot-gold-replay.jsonl` (giữ nguyên,
không sửa). Kết quả: 33/36 end-to-end, 0 wrong-served, 3 false refusal cùng ba ca, tầng D 6/6. Test của runner: 41.

**5.9 Review vòng 2** — verdict `READY` (0 BLOCKER, 0 MAJOR). Ba MINOR đã sửa trước khi có bất kỳ approval nào, mỗi cái có
test và lỗi tiêm:
- Nhãn bên trong cặp `line1/line2`, `plane1/plane2` và `segment_a/segment_b` cũng được chuẩn hoá. Bản §5.8 chỉ đổi chỗ cả
  cặp, nên nói quá so với mã.
- `segment` đi kèm `ratio` (`divide_segment`) giữ hướng.
- Một ca SERVED sai mà vẫn mang đúng dữ kiện của gold được quy cho tầng tất định.

Runner mới có sha `b25830f2…`; template được phát hành lại với blob `a3590e6b…`. Gold replay `s2-pilot-gold-replay-r2.jsonl`
thay `-r1`, kết quả không đổi: 33/36, 0 wrong-served. Test của runner: 44.

**5.10 Continuation 13 (R-1 + SL-3, review phản biện vòng 2 `READY`, vẫn trước mọi lượt live)** —
- `SL-3` (`registry.py` `/29`) đọc `k/c` (không phân biệt hoa/thường) và `đt` trước hai nhãn điểm của đường thẳng; hai ca
  `S2-F-F05_kc_mp_shorthand` và `S2-F-F06_dt_mp_shorthand` nay `SERVED` đúng trên gold (`√2` và `2/3`), chỉ còn
  `S2-F-S07_typo_tone` (`"hình chop"`, thuộc chính sách `S-1`) từ chối an toàn `UNGROUNDED_VALUE`.
- `project()` trong `run_s2_student_language_pilot.py` chuẩn hoá `described_points` (`@id -> described:...`, bỏ `described_id`,
  bỏ các trường tuỳ chọn mang giá trị `None` do OpenAPI `nullable: True` sinh ra và cắt khoảng trắng hai đầu chuỗi `@id`).
- Gold replay mới trên product `9503482a`: `s2-pilot-gold-replay-r3.jsonl` (giữ nguyên `-r2.jsonl` lịch sử): **35/36**
  end-to-end (`97.22%`), `0` wrong-served, `1/18` false refusal (`S2-F-S07`). Test của runner: **46**.
- Danh tính mới do `--manifest` in ra: `measured_system = 773e440de0385d577040a9eca107706bfb2d3e4aec1d827b52c99c89d42ac7c3`,
  `runner_sha256 = a274eabcb86079203fa6fb10be4b4efaf53a405142bb8e7fa427e382fc9696aa`; `s2-owner-approval.template.json`
  được phát hành lại với blob `d6c6e6b01b115621600054f611a7ff5f8657aec2` (`owner_decision = "PENDING_OWNER_DECISION"`,
  `paid_project_confirmed = false`).
