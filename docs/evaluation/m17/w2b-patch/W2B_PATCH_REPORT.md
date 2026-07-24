# M17 Wave 2B-PATCH — Pipeline Completeness · Empty Markers · Refusal Precedence

Bản vá đóng **3 finding** còn mở của Wave 2B (live run `0afcb37`, 3/6 case đạt).
Không mở Wave 2C. **Không sửa và không ghi đè** artifact live của run `0afcb37`
(`docs/evaluation/m17/rc1/live_table_*`); mọi artifact của bản vá nằm ở thư mục
riêng này.

## 0. Trạng thái

| Mục | Trước vá | Sau vá (offline) |
|---|---|---|
| pytest | 959 (2 skip, 1 deselect) | **996** (2 skip, 1 deselect) |
| vitest | 572 / 45 file | **596** / 46 file |
| build | sạch | sạch |
| catalog conformance | 20 target · 0 vi phạm | **20 target · 0 vi phạm** |
| `CACHE_VERSION` | 19 | **20** |
| `config_contract_version` (bảng) | `table-1.0` | **`table-1.1`** |
| family / target | 10 / 20 | 10 / 20 (KHÔNG mở family mới) |

**Live: CHƯA CHẠY LẠI** — chờ duyệt ngân sách riêng (§7).

## 1. L4 — đủ TẦNG pipeline, không chỉ đủ family

**Khuyết tật.** Đề hỏi `filter → projection → sort → limit → aggregate`; spec
chỉ dựng 3 tầng đầu, hệ vẫn trả `status=ok`. Học sinh nhận 5 dòng không giới
hạn và KHÔNG có trung bình, mà không được báo là đề đã bị trả lời thiếu.

**Nguyên nhân gốc.** Completeness PHA 2 so ở tầng **target**
(`satisfies_semantic_operations`), mà `database.relational_table_query` khai nó
đáp ứng CẢ CHÍN operation của family ⇒ mọi spec đều "đủ". Cái phải so là **spec
ĐÃ VALIDATE thực sự dựng được tầng nào**.

**Bản vá.**
- `simulation/table_query_engine.py::stages_of` — tầng spec biểu diễn, đọc
  THẲNG cấu trúc config (không đọc `notes`/narration).
- `simulation/pipeline_stages.py` (MỚI) — đăng ký theo FAMILY: ánh xạ yêu cầu
  semantic → tầng, so `requested` × `represented`, so tham số **chỉ những thứ
  chắc chắn** (số dòng giới hạn · hàm tổng hợp · chiều sắp xếp). Tên cột KHÔNG
  so (analyze nói nhãn "Điểm", spec nói id "diem" — so bừa sẽ chặn oan); ghi ở
  `unverified_parameters`.
- **Hai lớp, không lớp nào thừa**: thiếu tầng là lỗi SỬA ĐƯỢC nên báo đích danh
  bước còn thiếu ngược cho lượt `stage_simulate` sau (đề hợp lệ vẫn chạy được);
  cạn lượt vẫn thiếu thì cổng PHA 2 từ chối **fail-closed**.
- Bản ghi máy-đọc: `requested_pipeline`, `represented_pipeline`,
  `dropped_pipeline_stages`, `mismatched_stage_parameters`,
  `authoritative_stage_order`, `completeness_decision`.

**Thứ tự tầng (§A.3).** Công bố MỘT NGUỒN `PIPELINE_STAGE_ORDER =
filter → projection → sort → limit → aggregate`; `aggregate` tính TRÊN kết quả
SAU `limit`. Khoá bằng số chứ không bằng lời: fixture L4 cho AVG **8.5** (3 bạn
sau khi cắt) — nếu aggregate chạy trước limit thì phải ra 7.5. Hợp đồng prompt
nay ghi rõ thứ tự này và ghi rõ "đề cần thứ tự khác = truy vấn lồng → từ chối,
KHÔNG đổi thứ tự".

> **Giới hạn trung thực:** analyze KHÔNG có trường nào diễn đạt "thứ tự khác",
> nên hệ **không phát hiện được** yêu cầu đảo thứ tự bằng tín hiệu có cấu trúc.
> Điều này chấp nhận được vì engine chỉ có ĐÚNG MỘT thứ tự và các thứ tự khác
> đều rơi vào truy vấn lồng — vốn đã nằm trong `known_gaps` và bị từ chối ở
> classify. Hệ **không âm thầm đảo thứ tự rồi trả `ok`** (đó mới là điều cấm).

**Kết quả L4 (offline, qua `run_pipeline` thật):** spec đủ 5 tầng → 3 dòng
An/Dũng/Lan · AVG **8.5** · counted **3** · 0 rò rỉ kết quả vào spec.

## 2. L5 — thứ tự ưu tiên của lý do từ chối

**Khuyết tật.** Đề "lọc điểm ≥8 rồi sắp xếp giảm dần" **không kèm bảng nào** bị
báo `semantic_incomplete` — "hãy tách thành hai truy vấn". Học sinh làm theo sẽ
vẫn bị từ chối, vì lỗi thật là CHƯA CÓ BẢNG.

**HAI khuyết tật độc lập, đã sửa cả hai:**

1. **Cổng đủ-dữ-kiện quá dễ dãi.** `_has_table` nhận "≥2 object + có con số nào
   đó" là đã có bảng ⇒ đề không có bảng vẫn lọt. Nay bằng chứng phải có **nội
   dung ô thật** (`values`/`labels`), không chỉ danh từ.
2. **Đếm sai số truy vấn độc lập → CHẶN OAN.** Lọc và sắp xếp là hai TẦNG của
   MỘT truy vấn nhưng chữ ký mục tiêu khác nhau nên bị đếm thành hai truy vấn —
   nghĩa là **đề hợp lệ CÓ bảng cũng bị từ chối** (khuyết tật này chưa từng lộ
   ra ở live vì case L5 thiếu bảng nên chết trước). Luật đếm mới DẪN XUẤT TỪ HỢP
   ĐỒNG SPEC: một spec mang nhiều nhất MỘT tầng mỗi loại, nên số truy vấn độc
   lập = số chữ ký khác nhau nhiều nhất **trong cùng một loại tầng**. Analyze có
   khai `query_group` thì vẫn tin lời khai đó (hành vi cũ nguyên vẹn).

**Bất biến thứ tự (đã có sẵn, nay được khoá bằng test):**
`route → đủ dữ kiện → completeness → validation → execution`. Thiếu dữ kiện
BẮT BUỘC là lý do CHÍNH; chẩn đoán phụ vẫn giữ trong evidence cho dev.

## 3. L3 — chuẩn hoá marker ô trống THEO LƯỢC ĐỒ

**Khuyết tật.** Đề viết ô numeric trống bằng chữ "trống"; LLM chép đúng nguyên
văn (grounding ĐÚNG) nhưng validator từ chối ⇒ cạn 3 lượt ⇒ `status=error`.

**Bản vá — MỘT biên duy nhất:** ô thô → chuẩn hoá theo lược đồ → ép kiểu →
validate. Executor chỉ nhận `null` hoặc giá trị đã đúng kiểu.

| Trường hợp | Kết quả |
|---|---|
| ô rỗng / chỉ khoảng trắng | `null` (mọi kiểu cột) |
| "trống" · "—" · "N/A" · "null" ở cột **số/đúng-sai** | `null` |
| "trống" ở cột **chữ** | GIỮ NGUYÊN literal |
| `0` · `"0"` · `false` · "không" | GIỮ NGUYÊN, không bao giờ là ô trống |
| "abc" · "tám" · "8 điểm" · "không rõ" ở cột số | **fail-closed** (từ chối) |
| cột khai `nullable: false` + ô trống | **từ chối** |

Mỗi ô đã chuẩn hoá để lại bằng chứng `{row, column, column_type, original,
normalized, reason}` trong `config.normalizations`.

**Mirror hai tầng.** Validator FE trước đây **không ép kiểu ô nào** — nên chuỗi
"trống" lọt vào engine FE và AVG đếm luôn cả ô trống (`counted=6` thay vì `4`,
sai câm). Đường mở-lại-từ-lịch-sử (bất biến #17) đi thẳng vào engine FE nên đây
là lỗ thật, nay đã bịt.

**Kết quả L3:** AVG **8.25** · counted **4** · `empty→0 = 0`, cả BE lẫn FE.

## 4. Lỗi PHÁT HIỆN KHI REVIEW ẢNH (không test nào bắt được)

Thông điệp "chưa dựng được 2 bước" hiện ra dưới tiêu đề **"TÁCH THÀNH TỪNG YÊU
CẦU"** kèm gợi ý "mỗi lần hỏi một yêu cầu" — lời khuyên **SAI** cho đề vốn là
MỘT truy vấn nhiều bước. Nguyên nhân gốc: notice chọn tiêu đề chỉ theo
`failure_category`, mà `semantic_incomplete` nay gộp hai ca cần lời khuyên
NGƯỢC NHAU.

Đã sửa: thêm mã `PIPELINE_STAGE_INCOMPLETE`, notice đọc `error_code` trước rồi
mới lùi về `failure_category`. `failure_category` **giữ nguyên**
`semantic_incomplete` để không làm trôi taxonomy/artifact đã đóng băng.

## 5. Không hồi quy (§D)

Giữ xanh: L1 lọc+chiếu · L2 sắp xếp ổn định · L6 hai mục tiêu độc lập · S1
goal-aware completeness · max+min · BFS+DFS · hai biến thể sắp xếp · bốn biến
thể duyệt cây · canonicalize sibling-target boolean · toàn bộ fixture thiếu
dữ kiện · 0 generic leak · 0 rò rỉ kết quả.

**Bất biến sau bản vá:** `status=ok` ⟹ `dropped_semantic_requirements=[]` **VÀ**
`dropped_pipeline_stages=[]` **VÀ** `mismatched_stage_parameters=[]` **VÀ** dữ
kiện bắt buộc đã đủ.

## 6. Review thị giác (§E)

18 ảnh Chrome THẬT, 2 viewport (1440 · 768), người xem trực tiếp PNG:
`w2b_patch_visual_review.md`. Verdict **REAL_VISUAL 5/5 fixture**; assertion
trong trình duyệt: 0 tràn ngang · 0 phần tử bị cắt · 0 `stroke:none` (token ma).
KHÔNG chạy lại 42 ảnh toàn danh mục của RC1 §E vì cấu trúc renderer các family
khác không đổi.

Viewport được đặt **trước khi trang dựng** và trang nạp lại cho từng viewport —
không lặp lại artefact phép đo VIS-003 của RC1 §E1.

## 7. Live — CHƯA CHẠY, chờ duyệt

Đề xuất đúng §G: **4 case** (L3 · L4 · L5 + một đối chứng L1/L2), trần **14
HTTP**, `gemini-2.5-flash`, production `run_pipeline`, tối đa 1 retry toàn run.
Artifact sẽ sinh RIÊNG: `live_table_query_patch.json`,
`live_table_query_patch_report.md`, `live_table_patch_failure_ledger.md`.
