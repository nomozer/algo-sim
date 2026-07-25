# W2B — QUYẾT ĐỊNH PHẠM VI: LOẠI DEEP HARDENING KHỎI TUYẾN CHÍNH

**Ngày:** 2026-07-25 · **Tuyến phát triển chính:** `main` · **Baseline main:**
`f2b28e2` (PATCH1 implementation `8bd2324` + PATCH1 live evidence `f2b28e2`) ·
**Archive:** `archive/m17-w2b-deep-hardening` → `feb12d8`

Tài liệu này ghi lại một quyết định **phạm vi**, không phải một kết quả kỹ thuật
mới. Không có dòng engine/validator/renderer/orchestration nào bị sửa.

Tên đề tài giữ nguyên:

> *Hệ thống mô phỏng tương tác 2D/3D kết hợp LLM phân tích bài toán bằng ngôn ngữ
> tự nhiên hỗ trợ dạy học môn Tin học THPT*

Kiến trúc cốt lõi cần chứng minh — và **đã** được chứng minh ở baseline này:

```
bài toán ngôn ngữ tự nhiên
  → LLM phân tích
  → đặc tả ứng viên ĐƯỢC KIỂM ĐỊNH
  → engine tất định
  → trạng thái/timeline có thẩm quyền
  → renderer 2D/3D tương tác
```

---

## A. BASELINE TUYẾN CHÍNH

| Hạng mục | Giá trị |
|---|---|
| Active development branch | **`main`** |
| Main baseline | **`f2b28e2`** |
| PATCH1 implementation | `8bd2324` (tag `m17-w2b-patch1-thesis-baseline`) |
| PATCH1 live evidence | `f2b28e2` — **nằm ngay trong mainline** |
| `CACHE_VERSION` | **20** |
| `HISTORY_SCHEMA_VERSION` | **2** |
| Family / Target | **10 / 20** |
| `config_contract_version` (bảng) | `table-1.1` |
| Renderer `relational_table_query` | **REAL_VISUAL** (Chrome thật, 2 viewport) |
| Deterministic table executor | **REAL** |

Hệ thống **tiếp tục được phát triển trực tiếp trên `main`** từ baseline này.

---

## B. TRẠNG THÁI

| | Trạng thái |
|---|---|
| **Product Wave 2B** | **NOT CLOSED** |
| **PATCH2 / PATCH3 / PATCH4** | **REMOVED FROM MAINLINE** · **PRESERVED ONLY IN ARCHIVE** · **WILL NOT BE MERGED BACK INTO MAIN** |

- PATCH4 **chưa triển khai và sẽ không triển khai**.
- Wave 2C **không mở**.
- Archive là **read-only evidence**: không merge, không cherry-pick sang `main`,
  không phát triển capability mới trên đó, không sửa artifact lịch sử.

---

## C. CLAIM ĐƯỢC PHÉP — KÈM BẰNG CHỨNG

Mọi bằng chứng dưới đây **nằm trong mainline** (`f2b28e2` trở về trước).

### C.1 — Bằng chứng live vòng grounding (`0afcb37`)

`docs/evaluation/m17/rc1/live_table_query_report.md` — gemini-2.5-flash, 18 HTTP,
0 retry, 0 reclassify; **case 3/6 đạt**, grounding perfect 3/3 trên case sinh
được spec, generic-leak 0, false-positive-sim 0, result-leakage 0.

| Claim | Ca | Bằng chứng |
|---|---|---|
| **Lọc + chọn cột (filter + projection) có live success** | L1 ĐẠT | spec đúng ngay lượt đầu; grounding perfect (6→6 dòng, 3→3 cột, 0 ô bị sửa); engine final khớp oracle |
| **Sắp xếp ổn định (stable sort) có live success** | L2 ĐẠT | `sort desc` theo cột Điểm; dòng bằng điểm giữ nguyên thứ tự STT gốc; final khớp oracle |
| **Nhiều mục tiêu độc lập bị từ chối an toàn** | L6 ĐẠT | từ chối `semantic_incomplete`, không dựng mô phỏng nửa vời |

### C.2 — Bằng chứng live vòng PATCH1 (`f2b28e2` — HEAD baseline của main)

`docs/evaluation/m17/w2b-patch/live_table_query_patch_report.md` — **strict 1/3**,
**dừng vì chạm trần ngân sách 14/14 HTTP** nên ca thứ tư không kịp chạy.

| Claim | Ca | Kết quả |
|---|---|---|
| **Đề thiếu bảng → từ chối an toàn, đúng lý do** | P3 **ĐẠT** | `insufficient_specification`, đòi bảng, KHÔNG xui "tách truy vấn" — đóng finding L5 |
| **Ô trống không bị coi là 0** | P1 **KHÔNG ĐẠT tổng thể** | spec thừa một tầng `filter` làm rơi 2 dòng khỏi bảng hiển thị; **nhưng** `empty→0 = 0` và `AVG 8.25 / counted 4` **đúng** — lỗi ở tầng spec, không phải luật ô trống |
| **Pipeline thiếu tầng không được trả `status=ok`** | P2 **từ chối** | trả `unsupported` thay vì `ok` với spec 3 tầng; trước PATCH1 chính ca này từng trả `ok` với spec thiếu 2 tầng (L4 ở `0afcb37`) |

Khoá offline + review ảnh Chrome thật cho ba hành vi trên:
`tests/test_table_failure_precedence.py`, `tests/test_table_missing_values.py`
(+ mirror FE `table-missing-values.test.tsx`),
`tests/test_table_pipeline_completeness.py`; ảnh `docs/evaluation/m17/w2b-patch/`
(REAL_VISUAL 5/5, 18 ảnh, 2 viewport).

### C.3 — Claim thuần deterministic (không phụ thuộc LLM)

- **Engine tất định hỗ trợ bounded single-table operations**: `filter →
  projection → sort → limit → aggregate`, đúng một tầng mỗi loại, thứ tự công bố
  từ MỘT nguồn (`PIPELINE_STAGE_ORDER`), aggregate **sau** limit.
- **Renderer đã được đánh giá trên Chrome thật**, không phải chỉ SSR/unit:
  REAL_VISUAL 9/9 (`88618ac`) + REAL_VISUAL 5/5 sau PATCH1.

---

## C.4 — GIỚI HẠN PHẢI GHI KÈM

| Phạm vi | Trạng thái |
|---|---|
| Truy vấn bảng đơn giản (1–2 tầng) | **VERIFIED** |
| Pipeline nhiều tầng bằng ngôn ngữ tự nhiên | **PARTIAL / EXPERIMENTAL** |

- Pipeline **năm tầng chưa được chứng minh ổn định end-to-end** với production
  LLM. Ở lượt live cuối cùng còn trong mainline (`f2b28e2`), ca năm tầng **không
  đạt**; các lượt hardening sau đó (archive) cũng chưa đạt.
- Lượt live PATCH1 là **strict 1/3** và **dừng vì chạm trần 14/14 HTTP** — không
  được đọc là "đã live-verified toàn phần".
- Điều **thật sự** được chứng minh ở hai ca không đạt: hệ **từ chối** hoặc dựng
  **thiếu/thừa tầng có thể phát hiện được**, chứ **không bịa dữ liệu, không rò
  kết quả, không dựng cảnh minh hoạ cho một đáp án không engine nào tính**
  (`fp-sim 0`, `result-leak 0`, `generic-leak 0`, `semantic-loss 0`).
- Khi đặc tả thiếu tầng hoặc grounding không trung thực, hệ **từ chối thay vì tạo
  mô phỏng sai** — đúng R0, không phải thất bại cần che.

---

## C.5 — KHÔNG ĐƯỢC CLAIM

- ❌ five-stage live pipeline PASS
- ❌ live strict 4/4
- ❌ full table-query grounding 100%
- ❌ mọi natural-language table prompt đều được hỗ trợ
- ❌ PATCH2 / PATCH3 là một phần của mainline

Ghi chú trung thực bổ sung: `simulation/coverage.py` vẫn xếp đơn vị kiến thức
`database_table_query` (T11 CĐ4) ở mức `CAPABILITY_GAP`. Đây là **đánh giá dè dặt
hơn** khả năng thật hiện có, không phải overclaim, nên giữ nguyên — không tạo
descriptor drift chỉ để phục vụ quyết định phạm vi này.

---

## D. LÝ DO LOẠI KHỎI TUYẾN CHÍNH

PATCH2/PATCH3 tập trung vào **self-repair và deterministic stage recovery**:

- PATCH2 — *Stage-Preserving Spec Generation*: dựng manifest tầng tất định từ
  analyze rồi **merge** vào spec ứng viên, để LLM không còn là nguồn duy nhất
  quyết định spec có tầng nào.
- PATCH3 — *Analyze Parameter Grounding*: validator tất định + **một lượt repair
  có giới hạn** để điền tham số tầng còn thiếu ngay ở tầng analyze.

Đây là **production hardening hữu ích**, nhưng:

1. **vượt quá phạm vi cần thiết** — luận điểm của đề tài là *LLM phân tích ngôn
   ngữ tự nhiên + engine tất định giữ thẩm quyền kết quả*, và điều đó đã được
   chứng minh ở PATCH1 (kể cả bằng các ca từ chối trung thực);
2. **làm lệch trọng tâm** khỏi xây dựng mô phỏng giáo dục 2D/3D sang độ bền của
   một pipeline truy vấn bảng;
3. **không tạo đủ giá trị học tập** tương ứng với độ phức tạp: mỗi lượt vá đóng
   một lớp rồi lộ lớp kế tiếp (PATCH2 → tham số analyze trống; PATCH3 → nhãn cột
   bị đổi tên), không có điểm dừng tự nhiên, trong khi học sinh **không** có thêm
   chức năng nào;
4. **không mất gì**: toàn bộ code và bằng chứng giữ nguyên vẹn tại
   `archive/m17-w2b-deep-hardening` làm **research evidence + future work**.

Đây chính là mẫu hành vi mà `docs/RULES.md §3` nay phân loại là
**DEEP_HARDENING** và bắt buộc dừng lại xin quyết định.

---

## E. FUTURE WORK

Trình bày như **hướng phát triển**, không phải tính năng hiện có:

- *Stage-preserving candidate generation* — dựng tầng tất định từ analyze rồi
  merge, thay vì phụ thuộc hoàn toàn vào lượt sinh spec của LLM.
- *Analyze parameter repair* — một lượt repair có giới hạn để hoàn chỉnh tham số
  tầng trước khi định tuyến.
- *Source-table authenticity lock* — khoá nhãn cột/nội dung ô theo đúng bảng đề
  cho, chặn dạng lỗi "đổi tên cột" quan sát được ở lượt live cuối.
- *Provenance prompt → analyze* — source-span cho từng object/relation, để một
  hallucination **có định danh** không thể tạo false evidence (backlog Analyze
  Integrity, còn mở).
- *Complex multi-stage query reliability* — độ tin cậy của truy vấn nhiều tầng
  bằng ngôn ngữ tự nhiên nói chung.

---

## F. BẢN ĐỒ BẰNG CHỨNG

| Ref | Trỏ tới | Nội dung |
|---|---|---|
| `main` | `f2b28e2` + commit tài liệu | **Tuyến phát triển chính** |
| `m17-w2b-patch1-thesis-baseline` | `8bd2324` | Tag baseline code PATCH1 |
| `archive/m17-w2b-deep-hardening` | `feb12d8` | Toàn bộ deep hardening (read-only) |
| `m17-w2b-deep-hardening-archive` | `feb12d8` | Tag archive |
| `9f717df` / `4d9e8ac` | (archive-only) | PATCH2 implementation / live |
| `0513740` / `feb12d8` | (archive-only) | PATCH3 implementation / live |

**Không xoá, không viết lại, không squash** bất kỳ bằng chứng lịch sử nào. Các
lượt live thất bại được giữ nguyên làm research evidence — một hệ thống từ chối
trung thực khi chưa đủ khả năng là **dữ liệu**, không phải điều cần giấu.
