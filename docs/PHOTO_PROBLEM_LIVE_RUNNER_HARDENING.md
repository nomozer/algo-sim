# PHOTO_PROBLEM_LIVE_RUNNER_HARDENING

> Nhánh `feat/photo-problem-to-scene` · 2026-09-14 · **0 request mạng · 0 lượt gọi provider thật.**
> Wave này siết **bộ đo** cho lượt nghiệm thu provider thật của đường ảnh đề bài. Nó
> không đo gì, và không nói Gemini đọc được ảnh chụp thật hay không.

```text
LIVE_RUNNER_HARDENING     = PASS
READY_FOR_REAL_PHOTO_RUN  = YES — cần người: GEMINI_API_KEY + ảnh C01 thật + ground truth viết TRƯỚC
REAL_PROVIDER_EVIDENCE    = NOT_ESTABLISHED
MERGE_ALLOWED             = NO
PRODUCT_CODE_CHANGED      = NO   (git diff eeb0562 -- backend/app, frontend/src: rỗng)
MODEL_FACING_CHANGED      = NO
CANDIDATE_HASH            = 13e2aaaac929672e… → 13e2aaaac929672e…
CACHE_VERSION             = 95 → 95
```

## 1. Runner cũ đo được gì — kiểm trên mã, trước khi sửa

| câu hỏi | trả lời | chỗ |
|---|---|---|
| trần lượt gọi logic | 11 | `run_photo_problem_live.py` tại `eeb0562` |
| trần request HTTP | **không có** | — |
| số lần thử mỗi lượt đọc ảnh | 2 | `image_extraction.VISION_MAX_ATTEMPTS` |
| số lần thử mỗi lượt đọc đề / tổng hợp | 4 | `gemini.MAX_ATTEMPTS` |
| request HTTP xấu nhất | **38** = 3 × 2 + 8 × 4 | 3 đọc ảnh + 2 ca × (1 đọc đề + 3 tổng hợp) |
| dừng khi C01 hỏng | không | — |
| đếm theo tầng | không | — |
| đo văn bản | `difflib.SequenceMatcher`, không phải CER | — |

## 2. Thiết kế — không sửa một dòng mã sản phẩm

**Trần đặt ở transport.** `call_gemini` dựng `httpx.AsyncClient` mới mỗi lượt và đọc
tên ấy lúc gọi. `cai_cong_http` thay nó bằng một nhà máy chèn `transport=CongHttp`.
Cổng chạy SAU khi request đã dựng và TRƯỚC transport mạng, đúng một lần mỗi lần thử:
xác định ca và tầng (`telemetry.current_stage`) → kiểm trần → đếm → ghi metadata đã
khử secret. Vượt trần ⇒ `HttpBudgetExceeded`, con của `BudgetExceeded`, nên
`image_extraction` không nuốt nó thành `VisionUnavailable`. Request không khai tầng,
request khi chưa đặt ca, và mọi request sau lỗi provider đầu tiên cũng bị chặn. Truyền
`transport` thì `httpx` bỏ proxy của môi trường — không có lối vòng quanh cổng.

**Một lần thử mỗi lượt gọi.** `ApiBudget(max_attempts=1)` hạ cả ba tầng về 1 bằng cơ
chế sẵn có. Không tin bằng lời: trước mỗi lượt, `do_so_lan_thu_moi_tang` gọi đúng
`extract_problem_from_image`, `stage_semantic_analyze` và `stage_semantic_program`
trên một transport luôn trả 503. Khác 1/1/1 ⇒ `RETRY_POLICY_NOT_ENFORCEABLE`, thoát 4
trước mọi request thật.

**Trần 11** = C01 (1 đọc ảnh + 1 đọc đề + 3 tổng hợp) + C02 (như C01) + C03 (chỉ đọc
ảnh — runner không bao giờ gọi tầng B cho C03). Nay dẫn từ hằng số và bằng đúng
`MAX_HTTP_REQUESTS`; trường hợp ấy được dựng thật trong `HTTP_BUDGET_PROOF`.

**Từng ca.** `--case` bắt buộc; `all` chạy C01 → C02 → C03 và dừng ở ca đầu tiên
không đạt; ca chưa chạy ghi `NOT_RUN_PREVIOUS_CASE_FAILED`. Đầu vào tuyệt đối, kiểm
trước mọi request. Ảnh không bao giờ bị chép.

**Chấm đọc ảnh.** `cer` = Levenshtein / độ dài tham chiếu, sau đúng ba phép chuẩn hoá
(NFC · CRLF → LF · bỏ khoảng trắng cuối dòng). Ngưỡng đăng ký trong mã: C01 0,02 ·
C02 0,05. Cùng với CER, ca chỉ đạt khi nhãn điểm, công thức, vật, quan hệ, yêu cầu đều
đúng và không có dữ kiện bịa — một CER thấp không che được một nhãn sai.

**Khử secret.** `BoKhuBiMat` áp lên mọi dòng in và mọi JSON: giá trị khoá, `?key=`,
`Authorization`, `x-goog-api-key`, `Cookie`, `Set-Cookie`, `access_token`,
`refresh_token`. Metadata request chỉ ghi scheme + host + path.

**Ba chế độ.** `REAL_PROVIDER` · `DRY_RUN` · `INJECTED_TRANSPORT`. Hai chế độ sau
chạy trong `ChanMangThat` và không bao giờ ghi `REAL_PROVIDER_EVIDENCE`; transport tiêm
vào vẫn phải qua đủ cổng khoá và cổng chính sách thử lại như lượt thật.

## 3. Bằng chứng

| thứ | kết quả |
|---|---|
| `backend/tests/test_photo_problem_live_runner.py` | 18 yêu cầu (+ 18b), **56/56** |
| `HTTP_BUDGET_PROOF.json` | 12 lượt logic, trần 11 ⇒ ATTEMPTED 12 · SENT 11 · BLOCKED 1 · transport giả 11 · mạng 0. Đường xấu nhất vẫn đạt (tổng hợp trả JSON hỏng hai lượt) dùng đúng 11, RETRIES 0; cùng đường dưới trần 10 ⇒ ảnh C03 bị chặn |
| `CER_PROOF.json` | 13/13 cặp khớp đáp số. 5 ca dữ kiện: đối chứng đúng PASS · thêm mục trung thành với đề PASS · sai nhãn (CER 0,0069) FAIL · sai công thức (CER 0,0035) FAIL · quan hệ bịa con số FAIL |
| `REDACTION_PROOF.json` | 3 lỗi provider chở 5 secret giả: 0 lần lộ trên stdout, stderr, mọi artifact; dấu mốc đi kèm có mặt ở stdout và `RUN_SUMMARY` ⇒ thông điệp thật sự tới nơi |
| `RUNNER_DRY_RUN.json` | ảnh TỔNG HỢP c01/c05/c11: 3/3 PASS · 7 request · 0 mạng · 0 provider thật · 0 tệp ảnh |
| `FAULT_INJECTIONS.json` | 6 bắt buộc + 2 thêm: **8/8 đỏ đúng test, 8/8 hoàn lại trùng từng byte** |
| pytest backend | 4969 pass; `test_holdout_readiness_7b` đỏ khi cây làm việc bẩn (có chủ đích), kiểm lại sau commit |
| `freeze_evaluation_candidate.py --verify` | khớp `13e2aaaa…`, 94 file |

## 4. Đính chính — bộ đo sai hai lần trong chính wave này

Giữ lại vì cả hai đều trông như đúng cho tới khi có một cửa sổ chứng.

1. **Đếm lần thử lại theo băm thân request.** Lượt đầu của `HTTP_BUDGET_PROOF` ghi
   `RETRIES = 2` cho đường xấu nhất, trong khi `call_gemini` không thử lại lần nào:
   hai lượt SỬA của tổng hợp gửi thân **y hệt** nhau (cùng đầu ra hỏng, cùng lời báo
   lỗi) — đó là hai lượt gọi LOGIC. Nay cổng đọc `ApiBudget.retry_requests`, thứ chính
   `call_gemini` khai ngay trước `client.post`. Khoá: `test_10`; phép tiêm F7.
2. **Đếm mọi mục thừa là dữ kiện bịa.** `transcribe.md` dặn vision chép "những gì
   VIẾT trong đề chữ", nên một lượt đọc trung thành sẽ kê quan hệ, công thức, nhãn thiết
   diện `(T)` mà ground truth không liệt kê — và bản đầu đánh trượt nó. Lượt thật chỉ có
   một lần. Nay mục thừa chỉ là bịa khi mang một nhãn hay một con số KHÔNG có trong đề
   gốc (`ky_hieu_va_so`); mục thừa trung thành được liệt kê trong `details`. Khoá:
   `test_15`; phép tiêm F8.

⚠️ Lỗi thứ hai lộ ra **sau** commit runner `c351d95`, nên bản sửa (runner, test, script
bằng chứng) nằm trong commit thứ hai cùng artifact — **lệch** phân chia "commit 1 =
runner + test, commit 2 = artifact + tài liệu" của đặc tả. Thêm commit thứ ba hay viết
lại `c351d95` đều trái đặc tả; giữ hai commit và khai ở đây.

## 5. Giới hạn đã khai

- **Chưa có bằng chứng provider thật.** Mọi con số trên là offline; ảnh dry-run là ảnh
  tổng hợp.
- **Khớp dữ kiện là khớp chuỗi sau gộp khoảng trắng**, có phương án thay thế trong
  ground truth. `"z = 3"` cũng khớp bên trong `"z = 30"`; cách viết khác (`z=3`) phải
  khai phương án.
- **Nhãn điểm** nhận `A`–`Z` kèm chỉ số và dấu phẩy trên; không nhận chữ có dấu hay chữ
  Hy Lạp. **Con số** là dãy chữ số thập phân; `²` không tính.
- **Dữ kiện bịa** chỉ bắt được khi thứ bịa là một nhãn hay một con số. Một quan hệ sai
  chỉ dùng nhãn và số có thật (`SA ⊥ BD` khi đề không nói) không bị bắt.
- **C03** đạt với MỌI mã từ chối của tầng đọc ảnh, không riêng `MISSING_PROBLEM_TEXT`.
- Trong lượt full-suite đầu tiên,
  `test_repair_loop::test_luot_1_hong_luot_2_sua_duoc_thi_TRA_VE_SPEC` và
  `test_point_initialization_contract::test_D2_sua_dung_o_thi_luot_ke_tiep_DI_TRON`
  đỏ **một lần** khi chạy song song với script bằng chứng; xanh khi chạy riêng và ở
  lượt full-suite sau. Chưa truy tới gốc.

## 6. Chạy thật — việc của người

```bash
cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
  scripts/run_photo_problem_live.py --case C01 \
  --input-dir <tuyệt đối> --ground-truth <tuyệt đối> --output-dir <tuyệt đối, thư mục mới>
```

Ground truth của **chính ảnh ấy** phải viết TRƯỚC khi chạy — khuôn là
`live-runner-hardening/DRY_RUN_GROUND_TRUTH.json`, bỏ `dry_run_replay_case`. Nhãn khai
trước in trong `RUN_SUMMARY.json`: `INTERNAL_ONE_SHOT_ACCEPTANCE` · `HELD_OUT_CLAIM =
NO` · `OPERATOR_IS_DEVELOPER`. Không commit ảnh thật.

`NEXT_ACTION = USER_PROVIDES_GEMINI_KEY_AND_C01_REAL_PHOTO`
