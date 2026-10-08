# COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY

**2026-09-22** · nhánh `feat/photo-problem-to-scene` · START_HEAD `2b3b7d0` ·
commit công cụ `e0fbbb2` · `main` giữ `085cae6` ·
**0 request Gemini · 0 request mạng · không nạp `.env`, không nạp khoá**

```text
COMPLETION_MEASUREMENT_REPAIR_OFFLINE_POST_SAFETY = PASS
R1  ràng buộc 3/17 → 17/17, kiểm fail closed TRƯỚC transport; 27 kiểu trôi/thiếu chặn với 0 request
R2  nhật ký bền theo ca; P06 còn nguyên khi tiến trình chết ở P07; RESERVED không bao giờ gửi lại
R3  lỗi tầng chấm ⇒ MEASUREMENT_ERROR (mã từ vựng đóng), giữ quan sát/ngân sách/token/độ trễ, rồi dừng
REQUEST   6 thân request trùng byte START/END và trùng bản đăng ký; request thứ 7: 0 byte
CANDIDATE 077dbc6b… → 077dbc6b…       CACHE_VERSION 99 → 99      mã sản phẩm: 0 tệp
```

## 1. Ba lỗ, và gốc của chúng

- **R1 — ràng buộc chỉ mang phần ngữ nghĩa của registry.** Runner /2 ghi băm v1,
  băm v2 và candidate (3/17 theo nghĩa; 0/17 theo tên trường của đặc tả). Model,
  prompt, schema và thứ tự ca **có** được ghi, nhưng chỉ ở artifact viết **sau**
  vòng lặp.
- **R2 — mọi bằng chứng sống trong bộ nhớ tới hết vòng lặp.** Gồm bản ghi ca, quan
  sát request, bằng chứng ngân sách. Tái hiện ở START: P06 đọc đúng, tiến trình chết
  ở P07. Chỉ còn `REGISTRY_BINDING`, `STAGE_A_GATE` và envelope P06; bản ghi P06
  **mất** dù request đã trả tiền.
- **R3 — phần chấm sau phản hồi nằm ngoài xử lý lỗi.** Tái hiện ở START: tầng dựng
  của P06 ném `RuntimeError` ⇒ `main()` chết. Không bản ghi ca, không quan sát,
  không ngân sách.

## 2. Sửa

**R1.** `dung_rang_buoc` dựng đủ 17 trường từ **đúng byte runner dùng**. Prompt,
schema và model lấy từ request kỳ vọng dựng qua chính `stage_semantic_analyze`.
`kiem_rang_buoc_day_du` so với kỳ vọng dẫn **độc lập**:

- hằng đăng ký trước commit cùng runner: gốc kho, nhánh, cache 99, model, băm
  registry v2, thứ tự ca, ngân sách 6;
- overlay v2 (đã ghim bằng băm): manifest, ground truth, v1, candidate;
- `EXPECTED_REQUEST_HASHES`: prompt, schema;
- `git rev-parse HEAD`;
- runner và bộ tổng hợp: **giao** của băm chốt lúc nạp module với blob đã commit
  tại HEAD.

Ràng buộc được ghi nguyên tử, nạp lại, kiểm lại, rồi mới tới transport. Mọi lệch
chặn với mã ổn định: `BINDING_FIELD_MISSING:<trường>`, `BINDING_FIELD_TYPE:<trường>`,
`BINDING_*_MISMATCH` / `*_DRIFT`, `BINDING_TIMESTAMP_INVALID`. Runner không tự điền,
không lùi về ràng buộc cũ, không lùi v2 → v1. `created_at_utc` lấy qua `dong_ho` —
test cố định giờ và hai lượt cho **cùng byte**.

**R2.** Nhật ký bền `NhatKyHoanTat`; `cases/<ca>.json` là nguồn sự thật. Mỗi ca đi
qua các trạng thái:

1. `PLANNED` — trước khi dựng request.
2. `RESERVED` — tệp ca, chỉ mục, `REQUEST_BUDGET_PROOF`, `REQUEST_OBSERVATIONS`
   đều bền **trước khi byte rời tiến trình**.
3. `TRANSPORT_COMPLETED | PROVIDER_ERROR` — ngay khi transport trả hoặc ném; usage
   vắng ⇒ `UNKNOWN`.
4. Kết quả đọc đề (đã nhận output, token, độ trễ) bền **trước khi chấm**.
5. `SCORED | MEASUREMENT_ERROR` cùng bản tích luỹ của `COMPLETION_CASE_RESULTS` —
   **trước ca kế**.

Việc đặt chỗ nằm ở `CongBenVung`, lớp transport chen **giữa** cổng ngân sách và
transport thật. Nhờ vậy nó chỉ chạy khi ngân sách đã cho phép.

Mọi tệp đi qua **một** hàm `ghi_json_nguyen_tu`: tạm cùng thư mục → fsync →
`os.replace` → đọc lại; envelope dùng chung hàm ấy.

Nối lại (`mo_lai`):

- `RESERVED` không kết cục ⇒ `TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH`, **không gửi
  lại**, ngân sách **không hoàn**;
- `TRANSPORT_COMPLETED` chưa chấm ⇒ `SCORING_NOT_COMPLETED_AFTER_CRASH` (đầu ra thô
  không lưu nên không chấm lại được);
- `PLANNED` ⇒ chứng minh được là chưa gửi;
- tệp `*.tmp` sót lại được dọn và ghi tên.

Wave này **không** chạy nối lại live.

**R3.** `_cham_ca` chấm trên **bản sao** của phần bản ghi do request quyết định. Ném ⇒
bản chấm dở bị bỏ, bản ghi thành `MEASUREMENT_ERROR` với
`SCORING_EXCEPTION:<lớp trong danh sách cho phép | UNLISTED>` hoặc
`SCORING_REGISTRY:<mã bộ nạp>`. Bản ghi không chứa thông điệp, traceback hay giá
trị thô. Lượt đo dừng trước ca kế. Bộ tổng hợp /3 xếp hai kết cục đo hỏng mới vào
`MEASUREMENT_INVALID` (`MEASUREMENT_ERROR_IN_COMPLETION`).

## 3. Bằng chứng

- **Red → green:** 55 test (54 mới + 1 test cũ đổi kỳ vọng).
  - Ở `2b3b7d0`: **51 đỏ / 4 xanh**. Bốn ca xanh là bốn **cổng** (chặn transport
    thật, không khoá, không đường nạp `.env`, không DNS/socket trong `main()`) —
    đúng từ trước, không phải bản sửa.
  - Ở `e0fbbb2`: **55/55**, trong worktree sạch, **không** plugin dev.
- **Kịch bản `main()` thật ở END:**
  - chết ở P07 ⇒ P06 `SCORED` với token 21, độ trễ, quan sát, ngân sách 2; P07
    `RESERVED`; mọi JSON hợp lệ;
  - nối lại ⇒ 0 request, P07 `TRANSPORT_OUTCOME_UNKNOWN_AFTER_CRASH`, lượt đo
    `MEASUREMENT_INVALID`;
  - chết giữa transport và chấm ⇒ nối lại 0 request,
    `SCORING_NOT_COMPLETED_AFTER_CRASH`, token còn;
  - chết sau P06 `SCORED` ⇒ nối lại gửi đúng P07…N04, tệp P06 trùng byte;
  - lỗi provider ⇒ ghi ngay, token `UNKNOWN`, không gửi ca kế;
  - lỗi chấm ⇒ 1 request, `MEASUREMENT_ERROR`, không lọt chuỗi ngoại lệ.
- **Tiêm lỗi 10/10 bị bắt**, hoàn nguyên trùng byte:
  - F1 bỏ trường · F2 ràng buộc sau transport · F3 bỏ ngân sách trước transport;
  - F4 dồn bản ghi · F5 bỏ replace nguyên tử;
  - F6 lỗi chấm truyền ra · F7 lỗi chấm mất token · F8 gửi lại `RESERVED`;
  - F9 lỗi provider token 0 · F10 lùi v2 → v1.

  Tám phép chỉ bị **1–2 test** bắt. ⚠️ Phép tiêm chạy với plugin dev so blob với
  **đĩa**. Không có nó, mọi phép tiêm vào runner đều bị chính cổng R1
  (`BINDING_RUNNER_DRIFT`) chặn trước, và không đo được test đích.
- **Parity:**
  - START/END: sáu thân request trùng byte, mọi trường request trùng, khớp
    `EXPECTED_REQUEST_HASHES`; không chuỗi registry/ràng buộc nào trong thân
    request; request thứ 7 bị chặn, 0 byte;
  - registry v1/v2, manifest, ground truth, `CASE_REGISTRY`, candidate và khoá
    cache trùng byte;
  - 0 tệp lịch sử bị sửa.
- **Toàn bộ:** full backend **5861 passed, 0 failed** ở `e0fbbb2` (worktree sạch)
  = 5807 của START + 54 test mới.
  - Ở `2b3b7d0` là 5806 passed + **1 failed**, không phải hồi quy:
    `test_holdout_readiness_7b` đòi cây sạch, mà worktree START mang bản sao test
    red-before chưa track. Cùng suite ấy ở `d01254c`, worktree sạch, là 5807 passed.
  - Suite liên quan 218/218. Candidate `--verify` PASS, cache identity `--verify`
    PASS.

## 4. Giới hạn

- **Hai test cũ đổi kỳ vọng, có lý do.**
  - `test_nap_that_bai_thi_chay_mot_ca_FAIL_CLOSED_khong_lui_ve_v1` nay kỳ vọng bản
    ghi `MEASUREMENT_ERROR` thay vì ngoại lệ, vì R3 bắt buộc điều đó. Điều nó khoá
    (không lùi về v1) giữ nguyên.
  - `test_G2_A…` không đổi: bằng chứng ngân sách cuối vẫn trải các số HTTP ở mức
    đỉnh. Trên lượt nối lại, các số `HTTP_*` là của **tiến trình**; `RESERVED_*` là
    của cả lượt.
- **Chuỗi lỗi cũ trong bản ghi ca** (`PROVIDER_ERROR`, `RUNNER_EXCEPTION`) vẫn mang
  văn bản ngoại lệ đã khử khoá, như các lượt trước. Bộ tổng hợp dùng chúng để nhận
  lỗi của bộ đo. Trường mới của nhật ký chỉ mang **tên lớp**. Không đổi trong wave
  này.
- **Test đi qua `main()` chỉ xanh khi runner và bộ tổng hợp đã commit** (phép so blob
  tại HEAD). Đó là thiết kế: runner sửa dở không được chạy live.
- **Mỗi lượt `main()` ghi và fsync ~14 lần mỗi ca.** Suite mới mất ~40 s.

## 5. Artifact

`docs/evaluation/geometry/photo-problem-to-scene/completion-measurement-repair-offline-post-safety/`:

- `PRECHECK` · `GAP_REPRODUCTION` · `REGISTRY_BINDING_CONTRACT`
- `ATOMIC_PERSISTENCE_PROOF` · `PROCESS_DEATH_RECOVERY_PROOF`
- `SCORING_EXCEPTION_PROOF` · `PROVIDER_ERROR_PERSISTENCE_PROOF`
- `REQUEST_BYTE_PARITY` · `REGISTRY_PARITY` · `FAULT_INJECTIONS`
- `OFFLINE_GATES` · `IDENTITY_AND_CACHE_DECISION` · `SECRET_SCAN`

```text
NEXT_ACTION = RETRY_REMAINING_PREREGISTERED_CASES_POST_SAFETY_REPAIR
```
