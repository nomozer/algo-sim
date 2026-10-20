# Source gate hardening — báo cáo run (SG-1..SG-6)

- **Run:** `source-gate-hardening` · nhánh `research/hybrid-source-gate-hardening` từ `main` = `origin/main` = `6973c4b6`
- **Ủy quyền:** `GO_HYBRID_SOURCE_GATE_HARDENING_LOCAL` → `GO_MAIN_SOURCE_GATE_HARDENING_CONDITIONAL` (chỉ tích hợp nghiên cứu offline lên `main`; không bật Hybrid, không Wave 2C, không Adapter /3)
- **Commit sản phẩm (20):** `24103909` SG-1..SG-6 → `3509b705` (2 false refusal lộ trên corpus khoá) → `ee50e87b` (3 lỗ cùng
  nhóm lộ trên BH2A) → `aded2fbf` · `0cefe720` · `6c910a51` · `85e6dd86` · `b3c850e2` · `b6b61061` (review độc lập vòng 1–6)
  → `81e91ebb` · `b6a9fcc6` · `08bad12f` · `6f58c0f5` · `57701200` · `c6592ac2` · `c3b1f905` · `c7b79cce` · `26e1040a` ·
  `07da444c` · `602316ed` (sửa Full T3 và cổng đếm đỉnh nguồn `_kiem_so_dinh_nguon`, review T3-1..T3-11)
- **Đánh giá khoá trước khi đo:** corpus/oracle/harness `53c66941` · BH2A tái dựng `8b6f6316`
- **Candidate cuối:** **`c5a83b74`** (product `602316ed`, 112 file, `0512dbc53e09696dfecee4cec8ed360af4ad66d8816c782c2993c3617a0d2583`);
  19 candidate trước đó bị thay thế (chuỗi trong `inputs/candidate_divergence.json`)
- **Version:** `geometry-functions/9` · `geometry-fact-planner/10` · engine `/7` (không đổi); TypedFact `aa9d93ee…`, `flat`
  `485d3834…`, v3 `4bff35bb…`, tuyến A `5ceb0f99…` / `7ea511a6…` — **không đổi**
- **Live provider calls:** 0 · `CACHE_VERSION` 127 (không bump, §8) · `LLM_ONLY` · Hybrid product NO-GO
- **Review độc lập:** `verification/independent-review.md` — FAIL ở vòng 1–5, **PASS** ở vòng 6 (`1beeec0b`); tiếp nối sau Full T3
  qua vòng T3-1..T3-11, kết thúc bằng **`INDEPENDENT_REVIEW_PASS`** trên candidate `c5a83b74`
- **T3:** **`FULL_PRODUCT_GATE_PASS`** trên `2d0641f4` (`handoff.md` — pytest 11.338 passed, vitest 1.146 passed, build, demo 5/5 + 6/6)

## 1. Sáu nhóm lỗi: nguyên nhân → sửa (đúng một thẩm quyền: cổng nguồn `registry.py`, một dòng planner)

| Nhóm | Nguyên nhân gốc (ĐỎ trên `6973c4b6`) | Sửa (cuối) |
|---|---|---|
| SG-1 nhãn đoạn | `_co_doan`, `_so_neo`, `_gia_tri_la_phep_bang` khớp MỌI cặp nhãn liền nhau trong một từ ⇒ `BC` trong `S.ABCD`/`ABCD` thành "đoạn", giá trị neo vào số của AB | `_la_doan`: nhãn đoạn là NGUYÊN một từ hai nhãn. Đoạn không được nêu tên chỉ nhận giá trị qua vai trò cấu trúc gắn trong một câu đọc trọn (SG-3) — cạnh bên của chóp đều/lăng trụ ("cạnh bên"), cạnh của mọi cạnh bằng nhau (lập phương / tứ diện đều), cạnh của đáy đều |
| SG-2 tham số `a` | Bộ đọc hình dạng (`semantic_program/shape_constraint`, KHÔNG sửa — đường mặc định) giữ hệ số, bỏ `a`; `_rang_buoc_cuc_bo_khop` so (4, không a) với (4, có a); lát đóng line_ref so `[0]` | Đọc lại token số bộ đọc đã dùng (`_token_rang_buoc`), so đủ (giá trị², tham số) mọi chỗ (`_canh_khop`), xoá vùng đọc tới hết token; "cạnh a" không hệ số đọc token sau span đáy đều và vẫn so; lát đóng ném `UNGROUNDED_VALUE` khi cùng cấu trúc khác giá trị |
| SG-3 nhiều số một câu | "quote cho ô số phải chứa đúng MỘT số" | **Văn phạm mệnh đề ĐÓNG** (`_phan_tich_cau`, `_lien_ket_cau`, `_lien_ket_khop`): một số chỉ gắn vào chiều cao / cạnh đa giác đều / đoạn không tên khi CẢ CÂU chứa nó đọc trọn thành các mệnh đề: khối; đáy (có nhãn) là hình + cạnh n; "(có|với) <cạnh đáy·cạnh bên·chiều cao·đường cao·cạnh> (của <khối đúng loại, đúng nhãn>) bằng n"; đoạn có nhãn = n; vuông góc; định nghĩa điểm thuần; mặt/tam giác; "X là đường cao". Mệnh đề ngoài văn phạm (có số ⇒ câu không đọc; không số ⇒ mờ) và mệnh đề đổi chủ ngữ (mặt, tam giác, đường cao, hình chiếu, "và có <vai trò>" sau định nghĩa điểm) ⇒ không vai trò không nhãn nào của câu được gắn. Không suy chủ sở hữu từ văn xuôi, không danh sách ngoại lệ |
| SG-4 cách nói | Mỗi contract mục tiêu một regex không nhất quán | Token dùng chung `{N}` "điểm/đỉnh", `{J}` "với/và", `{K}` nối danh sách; "có ba đỉnh là" |
| SG-5 nhiều yêu cầu | Đuôi `_SAU_HOP_LE` không nhận động từ hỏi kế tiếp | Đuôi nhận `đồng thời|hãy|tính|tìm|xác định`; đối tượng sau nó vẫn phải là cụm hỏi đã nhận diện; không phục vụ một phần (`REQUEST_NOT_ANSWERED`) |
| SG-6 line_ref | Planner + cổng ép mỗi mặt đúng 3 nhãn; câu producer phải là "Tìm/Dựng giao tuyến…" riêng | Mặt ≥ 3 nhãn phân biệt (đồng phẳng do engine); giao tuyến nhắc ngay trong câu hỏi khoảng cách (điểm có tên hoặc mô tả theo contract Registry) chỉ khi chính câu đó là quote của lời hỏi đọc nó qua `line_ref` |
| (BH2A) | `right_triangle` không ánh xạ sang `right_angle` | Ánh xạ (đỉnh, hai đỉnh còn lại) |

Không `if/else` theo mã ca; không đổi lược đồ, prompt hay bề mặt nhà cung cấp.

## 2. Corpus khoá (A repro · B biến thể chưa có trong test · C âm) — `results/`

| | `main` `6973c4b6` | candidate đầu `73f4d47d` | **candidate cuối `0512dbc5`** (`results/evaluation-after-t3-review-10/`, trùng số với `evaluation-final/`) |
|---|---|---|---|
| Dương phục vụ đúng tuyệt đối | 1/18 | 16/18 | **18/18** |
| Mục tiêu đúng | 1/21 | 19/21 | **21/21** |
| Âm từ chối đúng mã | 6/12 | 12/12 | **12/12** |
| Phục vụ sai | 0/30 | 0/30 | **0/30** |
| Provenance nguyên văn | 1/1 | 16/16 | **18/18** |

**Không đo mù:** hai false refusal của candidate đầu được sửa SAU khi thấy chúng trên corpus này. 7 ca âm đổi mã (vẫn trong tập
mã đăng ký trước): cổng nguồn `UNGROUNDED_VALUE`, `CONDITIONAL_CLAUSE`; phủ yêu cầu `REQUEST_NOT_ANSWERED` (×2); engine
`INCONSISTENT_FACTS`, `PARALLEL_NO_INTERSECTION`, `NON_COPLANAR_POINTS`. Mỗi candidate trung gian có thư mục đo riêng
(`evaluation*`); con số không đổi từ candidate `d11fdd71` trở đi.

## 3. BH2A-01..18 — regression ĐÃ BIẾT (P4-D), không phải đánh giá mù — `bh2a/`

- **Đề:** nguyên văn `original_holdout_report.md`; `sha256(text)[:16]` khớp `orig_text_hash` của Gemini **18/18**.
- **TypedFact: RECONSTRUCTED** từ "Facts & Goals" của báo cáo (không có script của Gemini; KHÔNG khẳng định trùng byte).
  Chạy trên mã Gemini đã đo (`224328a2`): trạng thái + mã trùng Gemini **16/18** (lệch BH2A-13: dạng fact Wave 2B; BH2A-18:
  quote nguyên câu — cả hai từ chối).
- **Oracle:** của báo cáo, không sửa.

| Nhánh | 12 dương (15 mục tiêu) | Sentinel BH2A-13 | 5 âm | Phục vụ sai |
|---|---|---|---|---|
| Wave 2A `224328a2` | 3/12 (3/15) | REFUSED `SCHEMA_INVALID` | 5/5 | 0 |
| `main` `6973c4b6` (sau 2B) | 3/12 (3/15) | REFUSED `AMBIGUOUS_VALUE_QUOTE` | 5/5 | 0 |
| trước bản sửa BH2A | 8/12 (9/15) | REFUSED | 5/5 | 0 |
| **candidate cuối** (`bh2a/results-after-t3-review-10/`, trùng số với `bh2a/results-final/`) | **11/12 (14/15)** | **SERVED `a²√3` = oracle** | **5/5** | **0** |

BH2A-03 còn REFUSED, ngoài SG: đặc tả fact ghi mặt đáy `["A","B","C"]` cho đề (ABCD) ⇒ `SOURCE_OBJECT_MISMATCH`; bản trung
thực (ABCD) dừng ở văn phạm đóng của lát line_ref với câu tiền đề ghép (`ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE`). Sentinel
BH2A-13 bị SG-3 chặn trên `main` sau 2B, nay phục vụ đúng. BH2A-15 nay dừng ở engine `COLLINEAR_POINTS`, BH2A-18
`UNDERDETERMINED_POINT` (đúng mã báo cáo kỳ vọng). BH2A-10 tái dùng G đã khai. SGH-01..18 của Gemini không dùng.

## 4. Review độc lập (6 vòng + xác nhận phần chênh lệch) — `verification/independent-review.md`

Vòng 1–5 FAIL với phục vụ sai TÁI HIỆN được, cùng một lớp: gắn số vào vai trò từ văn xuôi tự do (chủ sở hữu suy ra sai,
ngoại lệ theo danh sách từ, mệnh đề đổi chủ ngữ). Kết thúc bằng văn phạm đóng không ngoại lệ (§1, SG-3). Vòng 6 PASS; ca còn
tranh luận N1/N2 vẫn được siết; xác nhận phần chênh lệch cuối PASS. Mọi probe tái hiện của mọi vòng là test âm
(`test_source_gate_hardening.py`: 226 test sau vòng T3-1..T3-11; 56 ĐỎ của vòng 1–6 trên `6973c4b6`).

## 5. Tương thích ngược

- **Hồi quy 174 dòng:** không đổi. **41/41 fixture Adapter `/2`** qua chuỗi danh tính (`/8 → /9`, `/9 → /10`).
- **NLU gold** (lớp `results/historical-gold-delta.json`): L27 REFUSED → SERVED (ba giá trị = kỳ vọng đăng ký trước; 11 → 12);
  L28 vẫn REFUSED, đổi mã (`QUESTION_LOCAL_GIVEN_UNVERIFIED` → `QUESTION_CONTEXT_UNSUPPORTED`).
- **Ma trận v3 offline (8 ô):** không đổi.
- **Fixture khoá** (nhãn giữ nguyên lịch sử; kết cục hiện hành khai trong test): G7/N13 REFUSED → SERVED `18√3`; cùng
  phán quyết REFUSED nhưng sớm hơn một tầng: NEG2 (`SOURCE_PREMISE_UNREAD` → `UNGROUNDED_VALUE`), N03
  (`PREDICATE_NOT_IN_QUOTE` → `UNGROUNDED_VALUE`), N07 (`NEGATED_CLAUSE` → `UNGROUNDED_VALUE`) — câu có mệnh đề ngoài văn
  phạm (phủ định, đường cao của tam giác) không gắn vai trò nào.
- Wave 1 chứng chỉ, Wave 2A composition, Wave 2B năng lực, tuyến A: test xanh (Full T3 ở `handoff.md`).

## 6. Bằng chứng khoa học SGH-01..18 (Blind Evaluation) & Bàn giao Task kế tiếp

### 6.1 Biên nhận đánh giá mù SGH-01..18 (`GO_MAIN_SOURCE_GATE_HARDENING_CONDITIONAL`)
- **SGH original blind evaluation:** `6/10` positive, `10/16` mathematically correct goals.
- **Strict tuple scoring:** `8/16` do khác biệt ngữ nghĩa trường `dim`.
- **Negative exact refusal:** `5/5`.
- **Ambiguous locked expectation:** `1/2`.
- **SGH-17:** sai lệch thiết kế oracle đã được phân xử riêng, không sửa manifest gốc.
- **Bốn false refusal:** `SGH-02`, `SGH-04`, `SGH-09`, `SGH-10`.
- **Thời điểm đo:** đánh giá mù gốc được thực hiện trước các bản sửa dựa trên phản hồi (feedback-based fixes).
- **Hai nhóm lỗi cổng nguồn còn lại:** `NOT FIXED` (xem §6.2).
- **Ngưỡng SGH đăng ký trước nghiêm ngặt (strict preregistered SGH threshold):** `NOT MET`.
- **Quyết định tích hợp:** Conditional GO MAIN (`GO_MAIN_SOURCE_GATE_HARDENING_CONDITIONAL`) được ủy quyền **chỉ cho tích hợp nghiên cứu offline (offline research integration ONLY)**.

### 6.2 Hai nhóm lỗi còn lại — Bàn giao cho Follow-Up Task riêng (`ISSUE-RESEARCH-HYBRID-SOURCE-GATE-REMAINING-GAPS`)
Hai nhóm lỗi dưới đây **không sửa trong GO MAIN** và được tách sang một follow-up task riêng:
- **Nhóm A:** `_kiem_don_vi_hoi` không nhận diện ranh giới mục tiêu kế tiếp có điểm mô tả chưa đặt tên.
- **Nhóm B:** `_kiem_nguon_dong` từ chối tiền đề ghép trong lát `line_ref` dù đã có các typed facts có nguồn và có thể kiểm tra độc lập.

Các giới hạn đã ghi nhận khác trong `docs/OPEN_ISSUES.md`:
- **False refusal có mã (đánh đổi chủ ý của văn phạm đóng và `_kiem_so_dinh_nguon`):** câu tiền đề có mệnh đề ngoài văn phạm, mệnh đề đổi chủ ngữ (mặt/tam giác/hình chiếu), "giao tuyến đó", "lần lượt bằng", mặt 3 nhãn cho mặt 4 nhãn của đề, "dựa vào SM tính …", hoặc danh từ "tam giác"/"hình vuông" không nhãn trong câu nói về khối.
- **Giới hạn phủ tiền đề có từ trước (không do run này):** một tiền đề trong câu mà một fact trích NGUYÊN câu được tính là đã đọc dù không lời gọi nào mã hoá nó (review K1/K2/K5); `6973c4b6` cũng phục vụ cùng tiền đề khi quote chỉ có một số.

## 7. Ảnh hưởng lên composition

Luật tổ hợp không đổi; cổng nguồn để nhiều bài tới planner hơn: corpus khoá 3 bài phục vụ có `effect-chain`; BH2A 01, 02, 04,
08, 12 (điểm mô tả → hàm hỏi) nay qua cổng; BH2A-13 dùng `divide_segment` + `MAT_VUONG_DUONG` của 2B.

## 8. Quyết định cache

Không bump (127): mọi thay đổi nằm ở `geometry_functions/registry.py` và `planner.py`; `/api/analyze` mặc định không nạp
chúng ở mức module (import lười chỉ khi preview bật; preview không ghi cache; khoá bởi
`test_version_constants_surface_fingerprints_and_historical_receipt_preservation`). `semantic_program/shape_constraint.py`
KHÔNG sửa. Envelope preview: version registry/planner trong `runtime_identity` đổi, khai bằng chuỗi danh tính.
