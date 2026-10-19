# Source gate hardening — báo cáo run (SG-1..SG-6)

- **Run:** `source-gate-hardening` · nhánh `research/hybrid-source-gate-hardening` từ `main` = `origin/main` = `6973c4b6`
- **Ủy quyền:** `GO_HYBRID_SOURCE_GATE_HARDENING_LOCAL` (không merge/push, không bật Hybrid, không Wave 2C, không Adapter /3)
- **Commit sản phẩm:** `24103909` (SG-1..SG-6) → `3509b705` (2 false refusal lộ ra trên corpus khoá) → `ee50e87b` (3 lỗ cùng nhóm lộ ra trên BH2A)
- **Đánh giá:** corpus/oracle/harness khoá `53c66941` (trước mọi lần đo) · BH2A tái dựng khoá `8b6f6316` (trước mọi lần chạy)
- **Candidate:** `382604f5` (`73f4d47d…`) → `66893205` (`d11fdd71…`) → **`c228bf4e`** (112 file, `b71487235f29fb12881506b619452a58806c9278768611dd80e3769460788e3a`)
- **Version:** `geometry-functions/9` · `geometry-fact-planner/10` · engine `/7` (không đổi); TypedFact `aa9d93ee…`, `flat` `485d3834…`, v3 `4bff35bb…`, tuyến A `5ceb0f99…` / `7ea511a6…` — **không đổi**
- **Live provider calls:** 0 · `CACHE_VERSION` 127 (không bump, §8) · `LLM_ONLY` · Hybrid product NO-GO
- **T3 / review độc lập:** `handoff.md`

## 1. Sáu nhóm lỗi: nguyên nhân → sửa (đúng một thẩm quyền: cổng nguồn `registry.py`, trừ một dòng planner)

| Nhóm | Nguyên nhân gốc (tái hiện ĐỎ trên `6973c4b6`) | Sửa |
|---|---|---|
| SG-1 nhãn đoạn | `_co_doan`, `_so_neo`, `_gia_tri_la_phep_bang` khớp MỌI cặp nhãn liền nhau trong một từ ⇒ `BC` trong `S.ABCD`/`ABCD` được coi là đoạn; giá trị BC neo vào số đầu tiên sau `S.ABCD` (= số của AB) | `_la_doan`: nhãn đoạn là NGUYÊN một từ hai nhãn. Hệ quả lộ ra khi test đối kháng: đoạn không được nêu ⇒ luật "quote có đúng một số" mượn số của đoạn khác (PHỤC VỤ SAI ở bước trung gian; `6973c4b6` từ chối ca này). Bịt bằng `_doan_theo_vai_tro`: giá trị của đoạn không được nêu tên chỉ nhận khi đoạn là cạnh bên của khối đã khai ("cạnh bên"; "cạnh" của lập phương/tứ diện đều) hoặc cạnh của đa giác ĐỀU đã khai trong cùng câu |
| SG-2 tham số `a` | Bộ đọc ràng buộc hình dạng (`semantic_program/shape_constraint`, KHÔNG sửa — nằm trên đường mặc định) giữ hệ số, bỏ `a` (`cạnh 2a` → 2) và span dừng trước `a`; `_rang_buoc_cuc_bo_khop` so (4, không a) với (4, có a) ⇒ từ chối nhầm; lát đóng line_ref lại so `[0]` ⇒ coi 2 và 2a như nhau | Đọc lại token số mà bộ đọc đã dùng (`_token_rang_buoc`), so đủ (giá trị², tham số) ở MỌI chỗ (`_canh_khop`), xoá vùng đọc tới hết token (`_span_rang_buoc`); "cạnh a" (không hệ số, bộ đọc không giữ giá trị) đọc token ngay sau span đáy đều và vẫn so; lát đóng ném `UNGROUNDED_VALUE` khi cùng cấu trúc khác giá trị |
| SG-3 nhiều số một câu | Luật "quote cho ô số phải chứa đúng MỘT số" | `_so_theo_vai_tro`: chỉ khi MỌI số của quote đứng ngay sau danh từ vai trò của nó bằng phép bằng (cạnh đáy · cạnh bên · chiều cao · đường cao · cạnh) hoặc thuộc một nhãn đoạn bằng phép bằng ("SA = 3a", "cạnh bên AA' = a"), và đúng MỘT số mang vai trò của ô; còn lại vẫn `AMBIGUOUS_VALUE_QUOTE` ("lần lượt", "lớn hơn", hai chiều cao) |
| SG-4 cách nói | Mỗi contract mục tiêu một regex, không nhất quán (độ dài không nhận "đỉnh"; diện tích không nhận "với"; "có ba đỉnh là" đòi hai lần khoảng trắng) | Token dùng chung trong `_mau_muc_tieu_mo_ta`: `{N}` "điểm/đỉnh" trước nhãn, `{J}` "với/và" của "nối … …", `{K}` nối danh sách; ràng buộc toán hạng theo ô giữ nguyên |
| SG-5 nhiều yêu cầu | Đuôi đóng `_SAU_HOP_LE` sau cụm hỏi không nhận động từ hỏi kế tiếp ⇒ "Tính SB và tính SC" đọc SB là không được hỏi | Đuôi nhận `đồng thời|hãy|tính|tìm|xác định`; đối tượng sau nó vẫn phải là cụm hỏi đã nhận diện; cổng phủ yêu cầu vẫn chặn phục vụ một phần (`REQUEST_NOT_ANSWERED`) |
| SG-6 line_ref | Planner + cổng ép mỗi mặt đúng 3 nhãn; câu producer bắt buộc là câu "Tìm/Dựng giao tuyến…" riêng | Mặt ≥ 3 nhãn phân biệt (`_mat_nhan_hop_le`; đồng phẳng do engine kiểm `NON_COPLANAR_POINTS`); giao tuyến nhắc NGAY trong câu hỏi khoảng cách (điểm có tên hoặc điểm mô tả theo contract Registry) chỉ khi chính câu đó là quote của lời hỏi đọc nó qua `line_ref` |
| (BH2A) | "tam giác vuông tại A" (`right_triangle`) không có ánh xạ sang lời gọi `right_angle` ⇒ tiền đề gốc "chưa bảo toàn" khi câu hỏi có dữ kiện cục bộ | Ánh xạ (đỉnh, hai đỉnh còn lại) ↔ `right_angle(vertex, rays)` |

Không thêm `if/else` theo mã ca; không đổi lược đồ, prompt hay bề mặt nhà cung cấp.

## 2. Corpus khoá (A repro · B biến thể chưa có trong test · C âm) — `results/`

| | `main` `6973c4b6` | candidate đầu `73f4d47d` | **candidate cuối `b7148723`** |
|---|---|---|---|
| Dương phục vụ đúng tuyệt đối | 1/18 | 16/18 | **18/18** |
| Mục tiêu đúng | 1/21 | 19/21 | **21/21** |
| Âm từ chối đúng mã | 6/12 | 12/12 | **12/12** |
| Phục vụ sai | 0/30 | 0/30 | **0/30** |
| Provenance nguyên văn (mọi quote của lời gọi có trong đề) | 1/1 | 16/16 | **18/18** |

**Không phải đo mù:** hai false refusal của candidate đầu ("cạnh a" không hệ số; "có ba đỉnh là") được sửa SAU khi thấy chúng trên chính corpus này; 16/18 là con số trước sửa. 7 ca âm đổi mã, tất cả vẫn trong tập mã đăng ký trước, phân loại theo tầng: cổng nguồn `UNGROUNDED_VALUE`, `CONDITIONAL_CLAUSE`; cổng phủ yêu cầu `REQUEST_NOT_ANSWERED` (×2); engine `INCONSISTENT_FACTS`, `PARALLEL_NO_INTERSECTION`, `NON_COPLANAR_POINTS` — trước đó các ca này dừng sớm hơn (`AMBIGUOUS_VALUE_QUOTE`, `FACT_INCOMPLETE`, `QUESTION_CONTEXT_UNSUPPORTED`, `NOT_ASKED_IN_SOURCE`).

## 3. BH2A-01..18 — regression ĐÃ BIẾT (P4-D), không phải đánh giá mù — `bh2a/`

- **Đề:** chép nguyên văn từ `original_holdout_report.md` (Gemini 4 Argon); `sha256(text)[:16]` khớp `orig_text_hash` của `reconciliation_receipt.json` **18/18**.
- **TypedFact: RECONSTRUCTED** từ mục "Facts & Goals" của báo cáo — script payload của Gemini không được cung cấp, KHÔNG khẳng định trùng byte (`exec_payload_hash`). Đối soát: chạy bản tái dựng trên mã Gemini đã đo (`224328a2`) ⇒ trạng thái + mã trùng `locked_results` của Gemini **16/18**; hai ca lệch: BH2A-13 (bản tái dựng dùng dạng fact Wave 2B `divide_segment` ⇒ 2A `SCHEMA_INVALID`; Gemini `PLANE_NOT_UNIQUE`), BH2A-18 (quote nguyên câu ⇒ 2A `AMBIGUOUS_VALUE_QUOTE`; Gemini `UNDERDETERMINED_POINT`) — cả hai đều từ chối.
- **Oracle:** của báo cáo, chép nguyên (`ORACLE` trong `bh2a_regression.py`), không sửa.

| Nhánh | 12 dương (15 mục tiêu) | Sentinel BH2A-13 | 5 âm | Phục vụ sai |
|---|---|---|---|---|
| Wave 2A `224328a2` | 3/12 (3/15) | REFUSED `SCHEMA_INVALID` | 5/5 | 0 |
| `main` `6973c4b6` (sau 2B) | 3/12 (3/15) | REFUSED `AMBIGUOUS_VALUE_QUOTE` | 5/5 | 0 |
| candidate `d11fdd71` (trước bản sửa BH2A) | 8/12 (9/15) | REFUSED `AMBIGUOUS_VALUE_QUOTE` | 5/5 | 0 |
| **candidate cuối `b7148723`** | **11/12 (14/15)** | **SERVED `a²√3` = oracle** | **5/5** | **0** |

- **Bản sửa trên BH2A, cùng nhóm SG** (test đỏ/xanh với nhãn và số khác, `test_source_gate_hardening.py`): số thuộc nhãn đoạn trong câu có vai trò (BH2A-08, 10, 13 — SG-3), tiền đề `right_triangle` (BH2A-11 — lộ ra sau SG-5), giao tuyến hỏi từ điểm mô tả (BH2A-03 — SG-6). 8/12 là con số trước sửa.
- **BH2A-03 còn REFUSED**, hai nguyên nhân không thuộc SG-1..SG-6: (1) đặc tả TypedFact của báo cáo ghi mặt đáy `["A","B","C"]` trong khi đề viết (ABCD) ⇒ `SOURCE_OBJECT_MISMATCH` (toán hạng lệch nhãn nguồn — từ chối đúng); (2) bản trung thực với (ABCD) (`BH2A-03-variant-ABCD`, chẩn đoán, không tính) dừng ở văn phạm đóng của lát line_ref: câu tiền đề ghép ("…, SA vuông góc … và SA = 3a") ⇒ `SOURCE_PREMISE_UNREAD` (`ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE`).
- **Sentinel BH2A-13:** primitive Wave 2B (`divide_segment` + mặt qua điểm ⊥ đường) đủ cho bài này, nhưng trên `main` sau 2B nó vẫn bị SG-3 chặn ("cạnh 3a … SA = 3a" một câu); sau run này phục vụ đúng.
- **Âm:** BH2A-15 nay dừng ở engine `COLLINEAR_POINTS` (mã báo cáo kỳ vọng; trước: `SOURCE_OBJECT_MISMATCH`), BH2A-18 `UNDERDETERMINED_POINT` (mã kỳ vọng); 14, 16, 17 giữ mã. BH2A-10 tái dùng G đã khai (một lời gọi `centroid`, không dựng thêm).
- Bộ SGH-01..18 Gemini đang giữ kín **không dùng**.

## 4. Tương thích ngược

- **Hồi quy 174 dòng:** không đổi. **41/41 fixture Adapter `/2`** qua chuỗi danh tính khai báo (`/8 → /9`, `/9 → /10`; engine không đổi — test lấy giá trị mới nhất THEO TỪNG KHOÁ).
- **NLU gold** (`results/historical-gold-delta.json`, lớp thứ năm): L27 REFUSED `NOT_ASKED_IN_SOURCE` → SERVED, ba giá trị = kỳ vọng đăng ký trước (phục vụ 11 → 12); L28 vẫn REFUSED, đổi mã `QUESTION_LOCAL_GIVEN_UNVERIFIED` → `QUESTION_CONTEXT_UNSUPPORTED` ("dựa vào SM" là chỉ dẫn phương pháp, chưa đọc).
- **Fixture khoá G7 / N13** ("cạnh đáy bằng 2, chiều cao bằng 3"): REFUSED `AMBIGUOUS_VALUE_QUOTE` → SERVED `18√3` (tính tay); nhãn fixture giữ nguyên lịch sử, kết cục hiện hành khai trong test (`KET_CUC_HIEN_HANH`, cùng cách `MA_HIEN_HANH`).
- **Ca lập phương có tham số** (`test_source_grounding_review`): vẫn `UNGROUNDED_VALUE` (giữ mã nhờ lát đóng ném đúng mã).
- Wave 1 chứng chỉ, Wave 2A composition, Wave 2B năng lực, tuyến A cô lập: test xanh (Full T3 ở `handoff.md`).

## 5. Ảnh hưởng lên composition

Tổ hợp hàm không đổi luật; cổng nguồn để nhiều bài TỚI được planner hơn: corpus khoá 3 bài phục vụ có chuỗi `effect-chain`; BH2A 01, 02, 04, 08, 12 (điểm mô tả → hàm hỏi) nay qua cổng; BH2A-13 dùng `divide_segment` + luật `MAT_VUONG_DUONG` của 2B.

## 6. Mã từ chối còn lại / false refusal đã biết

`ISSUE-RESEARCH-HYBRID-SOURCE-GATE-REMAINING-GAPS` (`docs/OPEN_ISSUES.md`): câu tiền đề ghép trên lát line_ref; "giao tuyến đó" (đại từ); "lần lượt bằng"; mặt ba nhãn cho một mặt bốn nhãn của đề; chỉ dẫn phương pháp trong câu hỏi ("dựa vào SM").

## 7. Đánh giá theo nhóm

| | `main` | cuối |
|---|---|---|
| SG-1 | 1/3 | 3/3 |
| SG-2 | 0/2 | 2/2 |
| SG-3 | 0/3 | 3/3 |
| SG-4 | 0/3 | 3/3 |
| SG-5 | 0/3 | 3/3 |
| SG-6 | 0/4 | 4/4 |

(ca dương VERIFIED của corpus khoá theo nhóm; BH2A ở §3.)

## 8. Quyết định cache

Không bump (127): mọi thay đổi nằm ở `geometry_functions/registry.py` và `planner.py`; `/api/analyze` mặc định không nạp chúng ở mức module (import lười chỉ khi preview bật; preview không ghi cache; khoá bởi `test_version_constants_surface_fingerprints_and_historical_receipt_preservation`). `semantic_program/shape_constraint.py` (đường mặc định) KHÔNG sửa — tham số `a` được đọc lại ở cổng tuyến D. Envelope preview: version registry/planner trong `runtime_identity` đổi, khai bằng chuỗi danh tính.
