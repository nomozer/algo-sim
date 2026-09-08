# THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING

**Ngày:** 2026-09-08 · **Loại wave:** tài liệu · **0 lượt gọi model**

```
APPLICATION_LLM_CALLS = 0
REAL_PROVIDER_CALLS   = 0
PRODUCT_CODE_CHANGED  = 0 byte
MEASUREMENT_CODE_CHANGED = 0 byte  (runner · certifier · scorer · policy · corpus
                                    · expected results · identity lock)
LIVE_ARTIFACTS_CHANGED   = 0 byte
CACHE_VERSION = 94 (không đổi) · CANDIDATE = d72db7c3… (không đóng băng lại)
```

Wave này **không sửa hệ**. Nó đọc lượt đo cuối đã chạy
(`thesis-final-20260908T160224Z`), đối chiếu số liệu ngoại tuyến, rồi viết hai
chương luận văn từ những con số đã đối chiếu.

---

## 1. Cổng §3 — đối chiếu số liệu TRƯỚC khi viết một chữ nào

Đặc tả wave cấm viết chương khi số liệu chưa đối chiếu. Cổng ấy được hiện thực
hoá thành một script mới:

**`backend/scripts/doi_chieu_ket_qua_cuoi.py`** · offline · 0 lượt gọi.

Nguyên tắc thiết kế quan trọng nhất của nó nằm ở chỗ chọn **đối chứng**:

> Một file tự so với chính nó thì luôn đúng. `BANG_CHUAN` — 31 trường — được chép
> từ **đặc tả wave**, tức một nguồn **ngoài** kho artifact. Giá trị của phép đối
> chiếu nằm ở chỗ hai nguồn độc lập (đặc tả do người soạn viết · artifact do máy
> sinh) **trùng nhau**.

Script tái tính mọi con số **từ artifact có băm**, không đọc một dòng nào của ba
báo cáo wave trước.

```
ĐỐI CHIẾU SỐ LIỆU TRƯỚC KHI VIẾT CHƯƠNG — 0 lượt gọi model

  ARTIFACT_HASH_VERIFICATION   PASS  (26 file · 19 raw)
  CORRECTION_LINKAGE           PASS  (3 artifact được đính chính)
  DAP_SO_KHOP                  PASS  (12/12)
  SO_TRUONG_LECH               0/31

  DOCUMENTATION_INPUT_CONSISTENCY  PASS
```

Bốn kiểm riêng biệt, không cái nào suy ra cái nào:

| kiểm | nội dung |
|---|---|
| `ARTIFACT_HASH_VERIFICATION` | băm lại **26 file** trong thư mục lượt chạy, so với `ARTIFACT_HASHES.json`; **19 file thô** phải khớp từng byte |
| `CORRECTION_LINKAGE` | bản đính chính phải ghi băm của **đúng 3 artifact** nó đính chính, và các băm ấy phải trỏ về file thô còn nguyên |
| `DAP_SO_KHOP` | **12/12** biểu thức — 11 đại lượng của 7 ca dương, tính cả trường hợp một ca trả nhiều đại lượng — khớp **từng ký tự** |
| `SO_TRUONG_LECH` | 31 trường của `BANG_CHUAN` so với giá trị tái tính; lệch **0** |

`RECONCILIATION.json` được ghi **ngoài** thư mục lượt chạy. Đây là quyết định có
chủ đích: ghi vào trong sẽ tạo một "file ngoài bảng" đối với `ARTIFACT_HASHES.json`
và **phá chính tính bất biến từng byte** mà §11 của đặc tả yêu cầu. Một công cụ
kiểm tính bất biến không được là thứ phá nó.

---

## 2. Tài liệu đã viết

| tệp | nội dung |
|---|---|
| `docs/thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md` | 11 mục — thiết kế đánh giá · bộ dữ liệu · cấu hình · kết quả tổng hợp · RQ1–RQ5 · phân tích ca sửa · phân tích an toàn · kiểm soát công cụ đo · thảo luận · threats to validity · đối chiếu C1–C9 |
| `docs/thesis/CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md` | 4 mục — kết luận · đóng góp · giới hạn (4 nhóm) · hướng phát triển (6 mục) |
| `docs/THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING.md` | báo cáo này |

Mười bảng bắt buộc đều có mặt trong Chương 4: bộ ca & độ phủ họ (4.1) · danh tính
lượt đo (4.2) · kết quả từng ca dương (4.3) · kết quả ca âm (4.4) · tổng hợp
(4.5) · đối chiếu 11 đại lượng với oracle (4.6) · lượt gọi & token (4.7) · phân
bổ lượt gọi theo chặng và theo ca (4.8) · threats to validity (4.9) · trạng thái
C1–C9 (4.10).

Mười hai biểu thức đáp số được giữ **nguyên văn**, đúng quy ước hiển thị của sản
phẩm (hữu tỉ · π · căn): `72` · `9` · `3√6` · `96` · `4500π` · `144π` · `360π` ·
`120π` · `100π` · `65π` · `25π√5` · `2π√6`.

---

## 3. Ba chỗ chương viết KHÁC cách trình bày thông thường — và vì sao

**(a) Lỗi của công cụ đo được đặt thành một mục riêng (§4.8), không đẩy xuống phụ
lục.** Lượt chấm đầu tiên báo `SILENT_WRONG_ANSWER_COUNT = 6`; con số ấy sai, và
hệ không phạm lỗi nào. Chương phân loại rõ:

```
MEASUREMENT_FAILURE_COUNT = 1
SYSTEM_FAILURE_COUNT      = 0
```

và nói thẳng rằng đây **không phải** sự cải thiện sản phẩm sau khi xem kết quả:
sửa nằm hoàn toàn trong bộ chấm, thực hiện ngoại tuyến, 0 lượt gọi, artifact thô
nguyên byte, bản sửa nối với bản gốc bằng băm. Chương cũng ghi lý do lượt chứng
nhận bằng provider giả **không thể** bắt được lỗi này — stub trả về chính chương
trình mẫu nên tên biến luôn trùng — và rút thành một mệnh đề dùng lại được: *một
provider giả giống bản mẫu quá mức thì không kiểm được những lỗi chỉ xuất hiện
khi mô hình được tự do lựa chọn.*

**(b) `n1` được ghi là giới hạn của phép đăng ký trước, không phải lỗi hệ.** Ca
này bị từ chối ở `stage_semantic_program` bằng `UNANCHORED_DERIVED_ASSUMPTION`,
tức **trước** khi bất kỳ mã lỗi thẩm định nào tồn tại để đối chiếu với hai mã đã
đăng ký. Chương **giữ nguyên** kỳ vọng đã đăng ký và ghi sai lệch, thay vì sửa kỳ
vọng cho khớp kết quả — vì sửa kỳ vọng sau khi thấy kết quả xoá đúng thứ mà việc
đăng ký trước tồn tại để giữ.

**(c) Chi phí được tách làm hai vai trò.** Dự báo token lệch **+31 %** (97 869 so
với 74 763), nguyên nhân định vị được: `thought_tokens` chiếm 34 % tổng mà trung
vị lịch sử không tách riêng. Chương không gộp điều này thành "ngân sách sai": dự
báo sai, còn **trần cứng vẫn hoàn thành vai trò an toàn** (dư 50 %, kiểm trước
từng lượt gọi). *Một cái phanh không cần dự đoán đúng quãng đường.*

---

## 4. Những gì chương KHÔNG tuyên bố

Ghi lại ở đây để lần sau không ai đọc rộng hơn dữ liệu cho phép:

- **không** phải held-out (`HELD_OUT_CLAIM = NO`) — đề do người triển khai soạn;
- **không** có ước lượng tổng thể — `n = 1` mỗi họ, mọi tỷ lệ in kèm mẫu số;
- **không** tuyên bố ổn định — `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`, khoá
  trước lượt chạy, một lượt duy nhất;
- **không** tuyên bố phủ chương trình phổ thông — chỉ phủ **10/10 họ hình trong
  phạm vi đã tuyên bố**;
- **không** đo chất lượng sư phạm — `C4` xác nhận cảnh 3D dẫn xuất từ trạng thái
  tất định và đủ thành phần, **không** nói cảnh dễ hiểu hay có ích;
- **không** đủ điều kiện bật tính năng — `PRODUCT_PROMOTION_ELIGIBLE = NO`.

Hai kết luận cuối cùng của Chương 4 (`PRODUCT_PROMOTION_ELIGIBLE = NO` ·
`STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`) **đã biết trước lượt đo** và không
suy từ kết quả.

---

## 5. Bề mặt mô hình

**KHÔNG ĐỔI.** Không chạm lược đồ, thẻ văn phạm, prompt hay bảng năng lực.
`CACHE_VERSION` giữ **94** — wave không sửa prompt và không sửa policy định
tuyến, nên không có gì để invalidate.

Candidate **không đóng băng lại**: không đường nào trong `MEASURED_SYSTEM_PATHS`
bị chạm. `freeze --verify` xác nhận vẫn là `d72db7c3…` (92 file).

---

## 6. Cổng đã chạy

| cổng | kết quả |
|---|---|
| `doi_chieu_ket_qua_cuoi.py` | `DOCUMENTATION_INPUT_CONSISTENCY = PASS` · 0/31 lệch · 12/12 đáp số |
| băm 26 artifact lượt chạy | khớp — 19 file thô nguyên byte |
| `pytest -q` | không đỏ (cây sạch) |
| `vitest run` | không đỏ |
| `git diff --check` | sạch |
| `freeze_evaluation_candidate.py --verify` | exit 0 — 92 file, `d72db7c3…` |
| kiểm danh tính cache | exit 0 @ `CACHE_VERSION = 94` |

---

## 7. Reused / created

**Reused** — không viết lại thứ đã có: `acceptance_integrity` (băm & kiểm toàn
vẹn), `score_thesis_final_acceptance` (`bang_bam`, `song_anh_tu_artifact`,
`TEN_THEO_DAC_TA`), `thesis_acceptance_corpus`, `thesis_acceptance_oracle`,
artifact lượt chạy.

**Created** — đúng bốn tệp:

- `backend/scripts/doi_chieu_ket_qua_cuoi.py` (đã ghi vào `docs/CODE_INDEX.md`)
- `docs/thesis/CHAPTER_4_RESULTS_AND_DISCUSSION.md`
- `docs/thesis/CHAPTER_5_CONCLUSION_AND_LIMITATIONS.md`
- `docs/THESIS_RESULTS_ANALYSIS_AND_CHAPTER_DRAFTING.md`

**Duplicate check**: `grep` tìm `doi_chieu|reconcil|RECONCILIATION` trong
`backend/scripts/` — không có script nào đang làm việc đối chiếu này;
`score_thesis_final_acceptance.py` **chấm lại**, không **đối chiếu với nguồn
ngoài**, nên hai việc khác nhau và không gộp được. `docs/thesis/` là thư mục mới,
không trùng ô sở hữu nào trong `REPOSITORY_MAP.md`.

---

```
NEXT_ACTION = THESIS_MANUSCRIPT_INTEGRATION_AND_FINAL_REVIEW
```

Hai chương đã có số và có lập luận; việc còn lại là **ghép vào bản thảo toàn
văn** — thống nhất cách đánh số chương/bảng với các chương 1–3, dựng mục lục
bảng, và soát một lượt cuối để không chương nào tuyên bố rộng hơn §4 của báo cáo
này cho phép.
