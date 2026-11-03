# Continuation 19 — Đánh giá Hybrid-first: khung đánh giá độc lập, pilot trích xuất, phân bổ lỗi

**Kết luận: `OFFLINE_READY_AWAITING_OWNER_GO`.** Mọi phép đo live (S-2, R-1, K-1) và đánh giá Hybrid-only độc lập là
`NOT_MEASURED`: không có file phê duyệt của Owner, không có tác giả độc lập. Phần offline có giá trị đã xong và dừng đúng
cổng Owner. Không thay đổi sản phẩm; candidate `15d236eb` được giữ nguyên. Kết luận Planner giữ nguyên:
`GENUINE_DISCOVERY_NOT_ESTABLISHED`.

## 1. Baseline C18 và danh tính candidate (`VERIFIED_OFFLINE`)
- Nhánh `research/hybrid-master-backend-replacement`; bắt đầu C19 tại HEAD `ba1f50ff`, cây sạch.
- Candidate `15d236eb`, product `51ba6135`, 118 file `3711d4eeee260ffd…`; `--verify` MATCH (kiểm trực tiếp, không suy từ
  tài liệu). Registry /31, planner /26, engine /22, `/2`, adapter `/4`, `CACHE_VERSION` 131, `LLM_ONLY`.
- Full T3 gần nhất: `full-t3-15d236eb.json` (không chạy lại: product tree không đổi — §XIII, §XVI).
- File phê duyệt: **không có** (chỉ template). Không có `.env` trong worktree; `ALLOW_LIVE_AI` không đặt.

## 2. Kiến trúc đánh giá (tái dùng, không dựng lại)
Một runner duy nhất `backend/scripts/run_s2_student_language_pilot.py` (transport, ngân sách, send guard, guard danh tính,
replay gold, attribution, receipt của paired harness) nay đo bốn study: `S-2`, `R-1`, **`K-1`** (mới), **`H-1`** (mới).
Scorer 8 chỉ số giữ nguyên byte. Bổ sung (commit `af3bea32`):
- kết cục `REFUSED_UNDERDETERMINED` (từ chối thuộc nhóm `MISSING_DATA`: dữ kiện đã nêu không xác định duy nhất đối tượng);
- **đúng trạng thái phải đúng lý do** (`reason_verified`, sau review vòng 1–2): từ chối chỉ đúng khi cùng mã với replay
  gold **và** cùng dữ kiện với gold; làm rõ chỉ đúng khi **mọi** mục `unresolved` nằm đúng cụm mơ hồ của gold (vị trí giao
  nhau trong đề, phủ quá nửa số từ, dài không quá gấp đôi); không có gì để so ⇒ `REASON_NOT_VERIFIED`, không bao giờ tính
  đúng. Cùng một phán quyết cho `end_to_end_correct`, theo nhóm, nhãn tổ hợp; chỉ 8 chỉ số của scorer (không đổi) là chỉ
  xét trạng thái. Bảo thủ: cách trích tương đương nhưng khác gold, hay làm rõ chỉ nêu một nửa cụm, đều bị tính sai;
- `constraint_check` (loại ràng buộc, toán hạng, quote, không tự bịa phép dựng);
- `hybrid_outcome` cho mỗi dòng: `SERVED_CORRECT`, `SERVED_WRONG`, `CORRECT_REFUSAL`, `FALSE_REFUSAL`,
  `WRONG_REASON_REFUSAL`, `CORRECT_CLARIFICATION`, `WRONG_REASON_CLARIFICATION`, `FALSE_CLARIFICATION`,
  `REASON_NOT_VERIFIED`, `INFRASTRUCTURE_FAILURE`;
  `cases_not_measured` cho ca chưa chạy (không bao giờ thành 0);
- cổng `H-1`: live bị từ chối nếu corpus không mang xác nhận độc lập do Owner, thiếu nhóm nào, hoặc có **ca nào** không
  có gold đã được tác giả xác nhận (CLARIFY phải có `unresolved`) (so khớp mục tiêu/toán hạng chỉ tồn tại khi có gold). Các trường xác nhận tự chúng
  không chứng minh gì; kiểm soát thật là Owner phê duyệt hash của file corpus.
Test RED/GREEN + tiêm lỗi (kiểm ràng buộc luôn-đúng và "lỗi kỹ thuật tính là từ chối đúng" đều bị bắt).

## 3. Giao thức Hybrid-only (`hybrid-only-independent-evaluation/1`)
`hybrid-only-independent-evaluation-protocol.md`: đăng ký trước, có phiên bản. Hybrid là kiến trúc đích; **không so với
LLM_ONLY**; giao thức paired 60 bài cũ giữ nguyên, chuyển vai trò thành `OPTIONAL_LEGACY_MIGRATION_COMPARISON` (không
sửa). 13 nhóm bắt buộc, kỳ vọng lấy từ hợp đồng năng lực, không đặt ngưỡng đạt, không đổi tiêu chí sau khi xem kết quả.

## 4. Nguồn gốc corpus và tác giả độc lập
| corpus | tác giả | lớp đo nếu chạy live |
|---|---|---|
| S-2 (36) | implementer | `LIVE_DEVELOPMENT_PILOT` |
| R-1 (18) | implementer | `LIVE_DEVELOPMENT_PILOT` |
| K-1 (16) | implementer (bộ sinh C17/C18) | `LIVE_DEVELOPMENT_PILOT` |
| H-1 | **chưa có** — không có tác giả độc lập được Owner chỉ định | `INDEPENDENT_HYBRID_EVALUATION`: `NOT_MEASURED` |

Không corpus nào ở trên là held-out độc lập. Không có tuyên bố khái quát hoá độc lập.

## 5–9. S-2, R-1, K-1: live `NOT_MEASURED`; trần replay gold (`VERIFIED_OFFLINE`, extraction = gold)
| study | end-to-end | SERVED_CORRECT | wrong-served | FALSE_REFUSAL | CORRECT_REFUSAL | CORRECT_CLARIFICATION |
|---|---|---|---|---|---|---|
| S-2 (`s2-pilot-gold-replay-c19-r3.jsonl`) | 35/36 | 17 | 0 | 1 | 12 | 6 |
| R-1 (`r1-live-pilot-gold-replay-c19-r3.jsonl`) | 16/18 | 11 | 0 | 2 | 3 | 2 |
| K-1 (`k1-live-pilot-gold-replay-r3.jsonl`) | 16/16 | 10 | 0 | 0 | 4 | 2 |

**Độ chính xác trích xuất / độ đầy đủ mục tiêu / giữ toán hạng** trên replay gold đều 100% vì extraction *là* gold —
đây là trần của các tầng tất định, **không** phải độ chính xác của Gemini (`NOT_MEASURED`). K-1: kiểm ràng buộc 6/6 và
điểm định nghĩa (kind) 8/8 trên gold — cùng lưu ý.

K-1 sửa trước mọi lần chạy live (phát hiện bởi replay gold, không bởi đầu ra model): K-B01 đổi từ CLARIFY sang
`REFUSED_UNDERDETERMINED` cho khớp giao thức C18 (§2 ghi "REFUSED"); K-E có gold "lối ra trung thực" (`unresolved`).

## 10–15. Chỉ số theo yêu cầu
| chỉ số | trạng thái |
|---|---|
| extraction accuracy, relation/described/constraint extraction (Gemini) | `NOT_MEASURED` |
| goal completeness, served-correct, wrong-served, false/correct refusal | chỉ trần gold, bảng trên |
| missing-data / contradiction / clarification detection | trần gold: S-2 6/6, R-1 2/2, K-1 2/2 phát hiện mơ hồ; K-B02, K-D từ chối đúng vì mâu thuẫn |

## 16. Phân loại Planner
Trên các ca phục vụ của replay gold: S-2 không có bước planner; R-1: 7 `SOURCE_EXPLICIT_SEQUENCE` + 4
`REGISTERED_DECOMPOSITION`; K-1: 10 `REGISTERED_DECOMPOSITION`; kiểm toán Scene3D: 41 source-explicit + 31 registered.
**Không có ca `PROVEN_REACHABLE_BUT_SEARCH_MISSED`** ở bất kỳ corpus nào: các ca trượt đều tái hiện ở Source Gate (§22).
Vì vậy Planner không được mở lại (§X). `GENUINE_DISCOVERY_NOT_ESTABLISHED` giữ nguyên.

## 17–18. Exact Kernel và hợp đồng Scene3D backend (`scene3d-contract-audit-r3.json`, `VERIFIED_OFFLINE`)
105 dòng qua đúng đường `/4` (gold), 72 ca phục vụ, 33 không phục vụ, **0 vi phạm**:
- đa diện (S-2) 17 phục vụ / 19 không; điểm mô tả (R-1) 11/7; mặt ràng buộc (thiết diện, K-1) 4; điểm định nghĩa (K-1) 6;
  từ chối (K-1) 4; làm rõ (K-1) 2; khối cong 17/1; khối ghép 17.
- Mỗi ca phục vụ: envelope `ok`, engine `VERIFIED` + `kernel_check`, **mọi mục tiêu toán được trả lời** (có mặt; giá
  trị đúng là việc của oracle ở §5–9), có đối tượng scene (id, type), mọi trường toạ độ (`xyz`, `polygon`, …) là số chính
  xác (`fullmatch`, không số thực), có construction trace.
- Mọi ca (phục vụ và từ chối): không có mã máy (`UPPER_SNAKE`) hay id thực thể (`khoi_S_ABCD`, `A_prime`) hay
  `simulation_id` trong bất kỳ trường chữ hiển thị nào của envelope và `route_d` (trừ trace kỹ thuật của planner, và
  `route_d.sections[].vertices[].label` — theo hợp đồng frontend đây là **id tham chiếu** đối tượng scene, không phải chữ
  hiển thị; ghi chú đặt tên: khoá `label` dễ gây hiểu nhầm). Ca từ chối: có mã, không có đáp số.
- Tự kiểm của công cụ bắt đúng các lỗi cài sẵn, gồm mọi lỗi reviewer vòng 1–2 chứng minh đã lọt qua bản trước.
- Không kiểm: mục tiêu mô phỏng bị bỏ (chỉ mục tiêu toán), giá trị đáp số, và **chưa có nhóm thiết diện mặt qua ba điểm có
  tên riêng** (thiết diện chỉ có ở mặt ràng buộc, mặt qua điểm mô tả, khối cong).
Đây là JSON backend; **không** chứng minh người học thấy bản dựng đúng (không có trình duyệt trong task này).

## 19–21. Độ trễ, token, USD
- Live: `NOT_MEASURED` (không có lượt live).
- Thời gian toàn tuyến offline với extraction ghi sẵn (không gồm provider): trung vị 0,012 s (S-2), 0,022 s (R-1),
  0,032 s (K-1); tối đa ~0,8 s. Độ trễ từng tầng (Source Gate/planner/engine): `UNKNOWN_NOT_INSTRUMENTED`.
- Token, USD thực: `NOT_MEASURED`. USD ước tính cận trên theo template: S-2 ≤ 0,88; R-1 ≤ 0,44; K-1 ≤ 0,39.

## 22. Phân bổ lỗi (tái hiện bằng gold, `VERIFIED_OFFLINE`)
| ca | kỳ vọng → quan sát | phân kỳ đầu tiên | tầng | nguyên nhân |
|---|---|---|---|---|
| S2-F-S07 | SERVED → REFUSED `UNGROUNDED_VALUE` | Source Gate | SOURCE GATE | "hình chop" thiếu dấu thanh; chính sách S-1 (không đoán dấu) — cố ý |
| R1-G01 | SERVED → REFUSED `SOURCE_OBJECT_MISMATCH` | Source Gate | SOURCE GATE | văn phạm góc chưa đọc "đường thẳng đi qua A và trung điểm của SC" |
| R1-G02 | SERVED → REFUSED `SOURCE_OBJECT_MISMATCH` | Source Gate | SOURCE GATE | cụm "điểm chính giữa cạnh SB" không thuộc văn phạm "trung điểm" |

Cả ba tái hiện y hệt với extraction gold ⇒ **không** phải lỗi Gemini, không phải planner/kernel. Đều fail-closed (không
phục vụ sai). R1-G01/G02 là thiếu độ phủ cách nói (`INFERRED`: thêm hai mẫu câu đóng sẽ phục vụ được), không phải lỗi
đúng/sai. Không sửa trong C19 (§23).

## 23. Sửa sản phẩm
Không có. Lý do: không phát hiện lỗi đúng/sai; ba ca trượt là độ phủ văn phạm và chính sách đã khai; mở rộng văn phạm
cần candidate mới, review, T3 và làm mất hiệu lực template — đề xuất thành quyết định Owner (§28).

## 24. Review độc lập
Fresh-context, đối kháng, chỉ đọc.
- Vòng 1 (`2ecde5ee`): **NOT_READY** — MAJOR-1 (đúng trạng thái nhưng sai lý do vẫn được chấm đúng: mô hình bỏ ràng
  buộc ở K-B01 vẫn ra cùng `PLANE_NOT_UNIQUE`; làm rõ trên cụm khác vẫn được chấm đúng), MAJOR-2 (định nghĩa
  SERVED_CORRECT của giao thức H-1 không khớp mã: không có gold thì không so mục tiêu/toán hạng), MINOR-3..5, NIT-6/7.
  Xác nhận đúng: oracle K-1, đổi nhãn K-B01, phân bổ ba lỗi, template, đường live cần file Owner.
- Đã đóng ở `b7926eae` / `697a59ad`. Không đổi: NIT-6 (`composition_label` gọi một ca làm rõ đúng là `CORRECT_REFUSAL`,
  có từ R-1) và NIT-7 (`evaluate()` gọi trực tiếp bằng code với dict điều khoản bỏ qua kiểm `owner_decision`; CLI không
  tới được, và transport vẫn đòi `ALLOW_LIVE_AI=1`).
- Vòng 2 (`697a59ad`): **NOT_READY** — MAJOR-A (tỷ lệ tổng vẫn chỉ xét trạng thái), MAJOR-B (so quote làm rõ quá lỏng:
  một từ "với" cũng qua), MAJOR-C (không có gold thì kiểm lý do tự tắt), MINOR-D (điểm mù của kiểm toán). Đóng ở
  `32d945f4` / `1af18bf0`.
- Vòng 3 (`1af18bf0`): **READY**, 0 BLOCKER, 0 MAJOR. Mọi đòn vòng 2 nay bị chấm sai; ca đối chứng (đưa gold làm đầu ra
  live) vẫn được chấm đúng; hai vùng loại khỏi kiểm toán (`planner`, `sections`) được xác nhận đúng với frontend hiện
  tại — phải xem lại nếu giao diện từng hiển thị trace planner hay nguồn gốc thiết diện. NIT còn lại: `REASON_NOT_VERIFIED`
  tính là không đúng (bảo thủ; với H-1 không xảy ra vì bắt buộc gold); một làm rõ sai lý do mà dữ kiện trùng gold được
  gán `UNATTRIBUTED`.

## 25. Hồi quy và Full T3
Không có product change ⇒ không tạo candidate, không chạy lại T3. Runner/test: 152 test runner + paired harness xanh;
replay S-2/R-1 chỉ thêm trường mới (kết quả không đổi); cổng tài liệu xanh.

## 26. Sẵn sàng migration
Không đổi: `LLM_ONLY` mặc định, `CACHE_VERSION` 131, rollback, compiler C, adapter `/3`, frontend. Hybrid chưa sẵn sàng
production: thiếu bằng chứng live, đánh giá độc lập, tích hợp D-10 frontend, QA thủ công và Owner GO.
`HYBRID_NOT_READY`.

## 27. Git
Chưa merge, chưa push. Thư mục tồn dư `hm-t3-7e9e479d`: kiểm lại (không `.git`, không đăng ký, chỉ bản sao tracked +
artefact tái sinh được); lệnh xoá bị bộ phân loại an toàn từ chối lần nữa ⇒ cần Owner tự xoá.

## 28. Quyết định Owner còn thiếu
Xem addendum 19 của `owner-go-request.md`: S-2, R-1, K-1 live (blob-keyed, chưa có file nào); tác giả độc lập cho H-1;
tuyên bố khoá luận về discovery; có mở rộng văn phạm Source Gate cho R1-G01/G02 hay không; tích hợp; xoá thư mục tồn dư.
