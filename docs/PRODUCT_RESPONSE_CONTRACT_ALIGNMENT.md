# `PRODUCT_RESPONSE_CONTRACT_ALIGNMENT`

**2026-09-09 · 0 lượt gọi model · 0 lượt gọi provider thật.**

Khoá luận hứa một *"từ chối có cấu trúc"*. Sản phẩm giao **hai trên bốn** trường
cho ca `n1`. Wave này định vị chỗ tín hiệu bị đánh rơi, sửa tại thẩm quyền sở
hữu nó, và chứng minh bằng phát lại nguyên byte + trình duyệt thật.

```
PRODUCT_RESPONSE_CONTRACT_ALIGNMENT = PASS
ROOT_CAUSE      = biên chuyển kết quả, KHÔNG phải tầng phát hiện
SELECTED_BRANCH = B  (tín hiệu CÓ, bị mất khi chuyển kiểu trả về)
```

---

## §1 · Lời hứa, và khoảng cách đo được

`THESIS_DRAFT §1.6` và `§3.9` cam kết nguyên văn: từ chối phải nêu **giai đoạn
dừng · loại thất bại · mã lỗi**, kèm lý do dễ hiểu. Lượt đo cuối giao:

| ca | `stage_reached` | `error_code` | `failure_category` | lý do học sinh đọc |
|---|---|---|---|---|
| `n1` | **`null`** | **`null`** | `geometry_generation_failed` | "…thử **diễn đạt lại đề** gọn hơn" |
| `n2` | `structural_coverage` | `requested_operation_uncovered` | `geometry_generation_failed` | "…thử **diễn đạt lại đề** gọn hơn" |

`n1` thiếu hai trường. `n2` đủ trường nhưng **nói ngược với chính mã của nó**:
mã có nghĩa *"không có phép dựng nào tạo ra thứ đề yêu cầu"*, còn câu cho học
sinh khuyên viết lại đề — một lời khuyên không bao giờ ăn thua, vì thứ thiếu là
một **phép dựng chưa tồn tại**, không phải một câu văn chưa rõ.

---

## §2 · Phân xử nhánh — bằng dữ liệu ĐƯỜNG CHẠY, không bằng đọc mã

`backend/scripts/replay_negative_boundaries.py` phát lại hai ca âm **nguyên
byte** (provider trả `raw_text` đã đóng băng, đối chiếu `raw_sha256`) qua đúng
`run_pipeline`, và chụp **bảy biên**. Kết quả trước bản vá:

| biên | `n1` | `n2` |
|---|---|---|
| 1 `detect_domain` | `hinh_hoc` | `hinh_hoc` |
| 2 `co_duong_thuc_thi` | `True` | `True` |
| 3 `semantic_analyze` | 5 fact · 1 nghĩa vụ | 9 fact · 1 nghĩa vụ |
| 4 `semantic_program` | **`stage=semantic_program` · `code=semantic_program_invalid`** | *(không dừng ở đây)* |
| 5 `verify/execute` | *(không tới)* | **`stage=structural_coverage` · `code=requested_operation_uncovered` · `cat=semantic_incomplete`** |
| 6 **envelope backend** | `stage=null` · `code=null` | `stage=structural_coverage` · `code=requested_operation_uncovered` |
| 7 adapter | như trên + lý do CHUNG | như trên + lý do CHUNG |

Biên 4 **đã biết** cả tầng lẫn mã và phát chúng cho observer. Biên 6 giao `null`.
Tín hiệu tồn tại rồi bị mất giữa hai biên ⇒ **NHÁNH B**, và chỗ mất định vị
được tới một dòng:

```python
# app/ai/pipeline.py — _semantic_route_attempt, TRƯỚC bản vá
_emit(observer, "semantic_route", stage_reached="semantic_program",
      error_code=ErrorCode.SEMANTIC_PROGRAM_INVALID.value, reason=serr)
return None          # ← kiểu trả về không chở nổi một phán quyết
```

`None` đi tới `_that_bai_hinh_hoc`, nơi `getattr(outcome, …) if outcome else
None` biến hai trường thành `null`. Telemetry đúng, sản phẩm sai — nên mọi cổng
đọc telemetry đều xanh trong khi học sinh nhận một lời từ chối cụt.

> **Thẩm quyền hợp đồng: TÌM THẤY**, không phải `CONTRACT_AUTHORITY_NOT_FOUND`.
> `error_code` ← `app/simulation/error_codes.py::ErrorCode` (28 mã, 8 thuộc
> tuyến hình học) · `failure_category` ← `SEMANTIC_FAILURE_CATEGORY` **là một
> HÀM của `error_code`** · `stage_reached` ← chuỗi do `route._hong(stage, …)` và
> `pipeline` phát. Không enum mới, không taxonomy thứ hai.

---

## §3 · Bản vá — ba chỗ, đều tại thẩm quyền sở hữu

1. **`route.hong_truoc_khi_dung_ir()`** *(mới)* — dựng `SemanticRouteOutcome`
   cho thất bại xảy ra **trước** khi có IR. Đặt ở `route` chứ không ở `pipeline`
   vì `route` là nơi duy nhất tra `SEMANTIC_FAILURE_CATEGORY`; dựng bản thứ hai
   trong `pipeline` là bảo đảm hai bản sẽ trôi khỏi nhau.
2. **`pipeline._semantic_route_attempt`** — hai nhánh `return None` trả phán
   quyết. `n1` nay giao `semantic_program` + `semantic_program_invalid`; nhánh
   `analyze` hỏng (chưa ca nào chạm ở lượt đo cuối) giao `semantic_analyze`.
3. **`learner_messages.learner_reason`** — tra `error_code` **trước**
   `failure_category`. Mã chi tiết hơn loại, và lời khuyên đúng cho mã này là
   lời hứa sai cho mã kia — đúng cách đã sửa hai lần cho `out_of_scope` vs
   `not_simulation_suitable`.

`failure_category` ở envelope **giữ nguyên** `geometry_generation_failed`. Đây
là lựa chọn có chủ đích: đổi nó sang `semantic_incomplete` cho `n2` sẽ kích
nhánh *"TÁCH THÀNH TỪNG YÊU CẦU"* của frontend — đúng lời khuyên sai mà wave
này đi sửa. Không mất thông tin: `SEMANTIC_FAILURE_CATEGORY` là hàm của
`error_code`, nên `error_code` có mặt là loại chi tiết tra lại được.

### Bề mặt học sinh

`UnsupportedNotice` nay dựng khối `.refusal-facts` — **Dừng ở bước** và **Loại
vấn đề** — bằng cách tra hai bảng nhãn tiếng Việt. Khoá kĩ thuật vào, tên tiếng
Việt ra: đúng cách dùng mà `ui-hygiene.test.ts` cho phép và là cách duy nhất
thoả cả `§8` của wave lẫn luật *"định danh kĩ thuật không lọt lên UI"*. Mã lạ
hoặc envelope cũ ⇒ *"Không xác định được từ phản hồi cũ"*; **không** dò chuỗi.

---

## §4 · Ba lỗi ẢNH CHỤP bắt được mà phép kiểm tự động thì không

Cả ba chỉ lộ ra khi mở ảnh `n2` bằng mắt.

**(a) Học sinh đọc gần y nguyên một câu hai lần.** `learner_reason` (backend,
vừa thêm) và câu gợi ý (frontend, thêm từ wave trước như một bản vá tạm khi
backend CHƯA có thông điệp) cùng liệt kê một danh sách năng lực. Mọi phép kiểm
lúc ấy xanh — chúng hỏi *"có mặt không"*, không hỏi *"có thừa không"*. Nay câu
gợi ý nói việc **nên làm tiếp**, và certifier đo **đoạn trùng dài nhất** giữa
hai khối văn bản (ngưỡng 40 ký tự; đo được `n1` 12 · `n2` 6).

**(b) Nhãn thẻ hứa ngầm.** Cả hai ca âm mang *"CHƯA DỰNG ĐƯỢC MÔ PHỎNG"*. Chữ
**"chưa"** đúng với `n1` (mô hình viết hỏng — thử lại còn cửa) nhưng sai với
`n2` (không phép IR nào tạo ra vật ấy — thử bao nhiêu lần cũng thế). `n2` nay
mang **"NGOÀI PHẠM VI DỰNG HÌNH"**.

**(c) Câu chốt tự khai năng lực THẤP hơn thực tế.** Nhánh mặc định còn ghi
*"khối đa diện **lồi**; mặt cong chưa mô phỏng được"* — hết đúng từ 2026-09-03
(cầu/trụ/nón) và 2026-09-07 (đa diện lõm), và chính lượt đo cuối phục vụ đủ cả
bốn ở `p2`–`p5`. Nói dối theo chiều khiêm tốn vẫn là nói dối, và nó đuổi học
sinh khỏi đúng những bài hệ làm được.

---

## §5 · Bằng chứng

| cổng | kết quả |
|---|---|
| phát lại biên `n1`,`n2` (0 lượt gọi) | trước/sau đều ghi artifact · `network_touch_attempts = []` |
| guard mạng — tiêm lỗi | `socket_ngoai` RAISED · `httpx_sync` RAISED · **PASS** |
| pytest | **4805 pass**, 1 skip, 1 deselect — **0 đỏ, cây sạch** @ `82673fa` |
| vitest | **813 pass** / 55 file (+15 test mới) |
| `npm run build` | PASS |
| nghiệm thu trình duyệt | **73/73** · 9 ảnh · ngoại lệ 0 · 7/7 dương + 2/2 âm |
| tiêm lỗi hợp đồng phản hồi | **7/7 DETECTED** |
| `replay_demo_cases` · `audit_demo_crash_surface` | PASS · 6/6 biên, 0 ném |
| freeze candidate `--verify` | exit 0 (92 file) |
| artifact lượt đo cuối | **45/45 BYTE-IDENTICAL** (git: 0 thay đổi) |

### Cache — đo bằng ROW THẬT, không bằng tiền lệ

`measure_cache_impact_response_contract.py` gọi `/api/analyze` thật qua
`TestClient` với provider stub, rồi **soi bảng `SimulationCache`**:

```
đề bị từ chối → HTTP 200 · status=unsupported
                stage_reached=semantic_analyze · error_code=semantic_program_invalid
                SO_ROW_CACHE_DUOC_GHI = 0
```

`main.py` chỉ ghi cache khi `status == "ok"`. Không có row nào thì **không tồn
tại đường** cho một phản hồi tiền-bản-vá quay lại. Chiều thay đổi không phải
`served→rejected` cũng không phải `rejected→served` — phán quyết cả 9 ca giữ
nguyên, chỉ **nội dung của một phản hồi không-được-cache** đổi.
⇒ `CACHE_VERSION 94 → 94`, **KHÔNG bump**.

---

## §6 · Hệ quả nặng nhất: candidate rời khỏi bản đã đo

Đây là lần **ĐẦU TIÊN** `backend/app` đổi sau lượt nghiệm thu cuối
(`d72db7c3… → e40de3b1…`, 92 file).

Trước wave này hai câu khác hẳn nhau vẫn trùng nhau nên không ai phải tách:

1. *chính sách đăng ký trước trỏ đúng hệ mà lượt đo ĐÃ đo* — sự thật **lịch sử**, vĩnh viễn;
2. *kho hiện đang ở đúng hệ ấy* — sự thật **tạm thời**.

`test_C1`/`test_C2` cưỡng chế cả hai bằng cùng một phép so với mã đang chạy.
Cưỡng chế (2) mãi mãi thì guard không còn bảo vệ pre-registration nữa — **nó
cấm sửa lỗi**. Nên:

- **`test_C2`** so chính sách với `IDENTITY_LOCK.json` — artifact **bất biến**
  của chính lượt đo, băm nằm trong `ARTIFACT_HASHES.json`. Chứng cứ **mạnh hơn**
  so với mã đang chạy: mã đổi theo mỗi commit, con dấu thì không.
- **`test_C2b`** *(mới)* nhận lại đúng cái răng vừa nhả: candidate hiện tại phải
  được **KHAI** ở `CANDIDATE_DIVERGENCE.json`, kèm lý do và wave. Sửa
  `backend/app` mà quên khai ⇒ đỏ; khai một băm không phải băm thật ⇒ cũng đỏ.
- **`chinh_sach_da_tieu`** mở rộng theo **đúng luật đã có** (tuyến V3 dùng
  `V3_SEAL.da_rut`): bằng chứng "đã tiêu" của lượt cuối là con dấu danh tính của
  một lượt **đã chạy xong** ghim đúng candidate ấy.
- **`test_B1_G1`** xét `CANDIDATE_HASH_MATCH` riêng và đòi nó **khớp văn bản
  khai**. Runner nay **từ chối chạy lại** trên mã hiện tại — đó là hành vi ĐÚNG.
- **`test_F12/F13`** (về TRẦN ngân sách) dựng bộ đo ghim candidate hiện tại;
  cổng danh tính vẫn được chứng minh có răng ở `test_F4` và **`test_F14b`** *(mới)*.

> **Không sửa** `thesis_final_acceptance_policy.json`. Toàn bộ giá trị của nó
> nằm ở chỗ được khoá TRƯỚC kết quả. Số liệu lượt đo cuối **không được chấm
> lại** theo mã mới — chúng mô tả `d72db7c3…`.

---

## §7 · Giới hạn — nói thẳng

- **`n1` KHÔNG được khai là "ngoài bao đóng".** Ma trận năng lực xếp khối tròn
  xoay tổng quát là `OUT_OF_SCOPE`, nhưng lượt chạy **dừng trước** cổng phủ
  (`cham.ghi_chu` của chính artifact: *"DỪNG SỚM… fail-closed đúng, nhưng KHÔNG
  chứng minh ranh giới ấy"*). Hệ chỉ biết *chương trình không hợp lệ*. Gán cho
  nó một phán quyết mạnh hơn là khai một điều lượt đo không thiết lập — nên câu
  gợi ý của `n1` giữ dạng **có điều kiện**.
- **Nhánh `semantic_analyze` chưa có ca thật.** Nó được vá cùng lúc vì hỏng cùng
  một kiểu, và chỉ kiểm bằng stub (`test_analyze_hong_van_co_tang_va_ma`).
- **`certify-refusal-surface.mjs` chập chờn — CÓ TRƯỚC wave này.** 5 lượt cho
  17–19/21, luôn là *kịch bản chạy ĐẦU* và luôn là "nhãn rỗng" (thẻ chưa kịp
  dựng), chưa lần nào là nhãn SAI. Đã kiểm trên cây **trước bản vá** (`git
  stash`): **19/21, cùng triệu chứng, kèm 1 lỗi console**. ⇒ flake của bộ đo,
  không phải hồi quy. Chưa sửa — ngoài phạm vi wave.
  ⚠️ Hệ quả phải nói ra: `docs/evaluation/integration/refusal-surface.json`
  **KHÔNG được làm mới** trong wave này, vì không lượt nào sạch để ghi. Nó vẫn
  là bản ghi của lượt trước bản vá. Commit một bản 17/21 sẽ đọc như một hồi quy
  mà nó không phải; giữ bản cũ thì nó tả một bề mặt đã đổi (nay có thêm khối
  `.refusal-facts`). Chọn cách thứ hai và ghi rõ ở đây — cả hai đều không lý
  tưởng, và im lặng là lựa chọn duy nhất không chấp nhận được.
  ⇒ follow-up hẹp: `REFUSAL_SURFACE_CERTIFIER_WARMUP_FLAKE`.
- **Một lượt pytest đầy đủ cho 2 đỏ thừa** ở `test_live_session_api.py`; file ấy
  **34/34 khi chạy riêng**, và lượt đầy đủ kế tiếp xanh. Cùng lớp flake đã ghi ở
  `THESIS_OBJECTIVE_AND_CLAIM_ALIGNMENT_REVIEW §8b`. Ghi lại, không giấu.
- **`product_capability.py` giữ nguyên** — nợ chuỗi lý do *"MÔ HÌNH: chưa đo"*
  không phải thẩm quyền tạo ra phản hồi sai ở đây.
- `DISPLAY_NAME_AUTHORITY_ELLIPSE_AND_CURVED_KIND` giữ `OPTIONAL_POLISH`.

---

## §8 · Artifact

`docs/evaluation/geometry/product-response-contract-alignment/`

| tệp | nội dung |
|---|---|
| `BOUNDARY_REPLAY_BEFORE.json` · `_AFTER.json` | 7 biên × 2 ca, trước và sau |
| `CANDIDATE_DIVERGENCE.json` | khai độ lệch candidate (khoá bởi `test_C2b`) |
| `CACHE_IMPACT.json` | đo bằng row thật · `BUMP_REQUIRED = false` |
| `ERROR_CODE_MAP.json` | 28 mã × loại × nhãn, **dẫn xuất** từ thẩm quyền |
| `FAULT_INJECTIONS.json` | 7/7 DETECTED |
| `IDENTITY_BEFORE_AFTER.json` | candidate · 5 băm model-facing · `CACHE_VERSION` |
| `ARTIFACT_HASHES.json` | 45 băm nguồn (bất biến) + 9 artifact của wave |
| `screenshots/` | `n1`, `n2` sau bản vá, Chrome thật 1440×900 |
