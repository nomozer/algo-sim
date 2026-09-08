# THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT

> **Wave đóng 2026-09-08.** Runner của lượt đánh giá cuối đã tồn tại, đã chứng
> nhận bằng provider stub, và băm của nó đã khoá vào `IDENTITY_LOCK.json`.
> **Lượt đo bằng model vẫn CHƯA chạy.**

```
THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT = PASS
APPLICATION_LLM_CALLS = 0 · REAL_PROVIDER_CALLS = 0
FINAL_ACCEPTANCE_RUNNER_READY = YES
LOCK_STATE = LOCKED_READY_FOR_FINAL_EXECUTION
NEXT_ACTION = THESIS_FINAL_ACCEPTANCE_EXECUTION
```

⚠️ **Wave này KHÔNG chỉ đụng bộ đo như dự kiến.** Lượt chạy stub phơi ra một
**lỗi sản phẩm thật** (§4). Bản vá được thực hiện theo quyết định của user, và
mọi hệ quả — candidate đổi, đóng băng lại, quyết định cache — đo và ghi ở §5.

---

## 1. Năm khoảng trống đã đóng

Wave trước đo `run_curved_acceptance.py` và trả `NO` với năm khoảng trống. Runner
V3 **không được vá** — nó giữ nguyên cho tuyến V3. Lượt cuối có entrypoint riêng:
`backend/scripts/run_thesis_final_acceptance.py`.

| | khoảng trống | đóng thế nào |
|---|---|---|
| **G1** | bộ ca cố định | đọc thẳng `CORPUS.json`; `nap_ca_v3`/`seal_curved_v3` **không xuất hiện trong AST** của runner (guard `_dau_vet_v3`, đọc AST chứ không quét chuỗi) |
| **G2** | giữ mọi raw attempt | mỗi lượt gọi một file `raw/<ca>/<stage>_<n>.json` kèm `raw_text` · `raw_sha256` · `prompt_sha256` · `logical_call_index` · `physical_attempts` · `parse_error`. Response parse lỗi **vẫn giữ nguyên văn** |
| **G3** | scorer canonical | `acceptance_verdict.phan_loai` cho ca dương, `cham_ca_am` cho ca âm. Không danh sách mã hình cong chép tay nào |
| **G4** | hai chặng | A: 1 analyze + 1 tổng hợp (ghim `MAX_SEMANTIC_PROGRAM_ATTEMPTS = 1`). B: đúng **1** lượt sửa. Ca âm **không** được sửa |
| **G5** | policy khoá luận | `mo_run(..., duong_chinh_sach=…)` — tham số thêm mới, mặc định giữ nguyên hành vi V3 |

---

## 2. Chặng B TIẾP TỤC, không chạy lại

Đây là thay đổi thiết kế đáng kể nhất, và nó cắt ngân sách gần một nửa.

```
Chặng A     đề → scope → analyze → ĐÓNG BĂNG hợp đồng → tổng hợp
            → verify_and_compile → chấm → ghi stage_a_first_attempt.json
Chặng B     hợp đồng ĐÃ ĐÓNG BĂNG + raw candidate hỏng + chẩn đoán
            → MỘT lượt sửa → verify_and_compile → chấm
```

Chặng B **không** gọi lại analyze và **không** sinh lại candidate đầu — chứng
minh bằng máy: `analyze_calls_in_stage_b = 0`,
`initial_synthesis_calls_in_stage_b = 0`, và `frozen_contract_sha256` /
`raw_initial_candidate_sha256` của chặng B **trùng băm** artifact chặng A.

### Seam có sẵn, nên không phải chép

`RUNNER_CONTINUATION_SEAM_REQUIRED = NO`. `pipeline` phơi đủ helper để **tái
dùng**: `_prompt_sua` (chính hàm dựng prompt sửa của sản phẩm), `load_skill`,
`program_skill_for`, `generate_json_schema`, `validate_semantic_program`,
`kiem_tinh`, `check_grounding`, `KHONG_DUOC_SUA`.

Còn `base` — đề + dữ kiện + nghĩa vụ + thẻ văn phạm — là biến **cục bộ** của
`stage_semantic_program`. Runner **không dựng lại nó**: ở lượt đầu
`prompt = base` nguyên văn, nên cổng bọc `call_gemini` **chụp** đúng chuỗi ấy.
Không có bản sao nào để trôi.

### ⚠️ Chỗ DUY NHẤT có thể lệch, và cách khoá nó

Ba nhánh chuỗi chẩn đoán (`loi`) nằm trong thân vòng lặp và không lấy ra được,
nên runner phải dựng lại. Khoá bằng **phép so từng BYTE** với prompt mà sản phẩm
THẬT phát ra ở lượt sửa — chạy `stage_semantic_program` với trần 2 lượt, stub
cho hỏng lượt đầu, chụp prompt lượt hai:

| nhánh | fixture | kết quả |
|---|---|---|
| `schema` | `p4` bỏ `apex_or_top` | **trùng byte** |
| `ir_static` | `p1` cắt thiết diện TRƯỚC khi dựng khối | **trùng byte** |
| `grounding` | `p2` bỏ `source_fact_id` của một đỉnh | **trùng byte** |

`test_F17` tiêm thêm **một dấu cách** vào chẩn đoán và đòi phép so ĐỎ — không có
nó thì ba phép so trên có thể đang xanh vì chúng không phân biệt được gì.

---

## 3. Amendment ngân sách

Versioned, `DECIDED_BEFORE_LIVE_RUN = true`,
`APPLICATION_LLM_CALLS_BEFORE_AMENDMENT = 0`. Policy `1.0.0 → 1.1.0`.

| | trước | sau |
|---|---|---|
| chặng B | `7 × (1 analyze + 2 synthesis) = 21` | `7 × (0 analyze + 1 repair) = 7` |
| `MAX_LOGICAL_CALLS` | 39 | **25** |
| `MAX_PHYSICAL_ATTEMPTS` | 156 | **100** |
| `HARD_TOKEN_BUDGET` | 294 000 | **196 000** |
| `EXPECTED_LOGICAL_CALLS` | 18 | 18 (không đổi) |

### ⚠️ Ca âm ĐI QUA provider — đo, không suy

```
NEGATIVE_CASE_PROVIDER_CALLS = 2 mỗi ca (analyze + synthesis)
```

Đo bằng runner stub. `detect_domain` xếp cả hai ca âm vào miền hình học và
`co_duong_thuc_thi` thấy nghĩa vụ `volume` có checker, nên chúng **không** dừng
trước provider. Vì vậy ngân sách **không** giảm thêm xuống `168 000` như dự kiến
ban đầu của đặc tả — **con số đo được thắng con số dự kiến**.

---

## 4. ⚠️ LỖI SẢN PHẨM lượt stub phơi ra

> Đây là phát hiện đắt giá nhất của wave, và nó chỉ lộ ra vì bài chứng nhận
> chạy **đường thật** thay vì một bản mô phỏng nó.

`plane_equation.doc_phuong_trinh` chỉ đọc được dấu trừ **ASCII** `-`. Mọi dấu
trừ Unicode trả `None`:

| ký tự | tên | trước vá |
|---|---|---|
| `−` | U+2212 MINUS SIGN — **dấu trừ ĐÚNG của toán học** | `None` |
| `–` | U+2013 EN DASH | `None` |
| `—` | U+2014 EM DASH | `None` |

Và hậu quả **không phải** "không đọc được" mà tệ hơn hẳn. Phép nở span đi theo
`_TRONG_PT`, trong đó không có `−`, nên nó **dừng giữa phương trình**:

```
đề            "Mặt phẳng (α): 2x − z + 12 = 0"
ứng viên      "z + 12 = 0"              ← cắt cụt, MẤT hạng tử 2x
bất biến so   z + 12 = 0  vs  hình dựng 2x − z + 12 = 0   ⇒ VI PHẠM
```

Tức **một chương trình gold hoàn toàn đúng bị từ chối**, kèm một lời từ chối nói
về một mặt phẳng đề không hề viết. Đây đúng là ca *"một mặt phẳng SAI được đem
đi đối chiếu"* mà docstring `_ung_vien` đã ghi là ca tệ hơn — chỉ khác nguyên
nhân.

⚠️ **Ca `p6` đỏ; ca `p7` cùng lỗi nhưng VẪN xanh** vì phép cắt cụt của nó tình
cờ cho một phương trình tương đương. Một lỗi bật ở một trong hai ca cùng hình
dạng là lỗi tệ hơn một lỗi bật ở cả hai.

### Vì sao KHÔNG né bằng cách sửa đề

Viết lại `p6`/`p7` sang `-` giữ được candidate nguyên vẹn, nhưng đó là **chỉnh
bài thi cho vừa hệ**: lỗi vẫn còn, và một đề thật gõ bằng dấu trừ toán học —
thứ SGK, Word và một mô hình chép lại đề đã soạn đẹp sẽ phát ra — vẫn hỏng.
Benchmark khi ấy mất đúng khả năng phát hiện nó.

### Bản vá

`chuan_hoa_dau_tru` — ánh xạ **1 ký tự ↔ 1 ký tự** (`_ung_vien` trả LÁT CẮT của
chuỗi gốc, nên một phép chuẩn hoá đổi độ dài sẽ làm mọi chỉ số lệch;
`unicodedata.normalize` không dùng được vì lý do ấy). Gọi ở hai biên đọc văn bản.

`U+00AD SOFT HYPHEN` **cố ý không** được ánh xạ: nó không phải dấu trừ, và nhận
nó là bịa ra một phép trừ đề không viết.

### Nó là NGOẠI LỆ, không phải quy ước

`point_coordinate.py` **vốn đã** xử lý U+2212 từ trước (`_SO = r"[-−+]?…"` và
`.replace("−", "-")`). `segment_relation._SO` chỉ khớp số không dấu nên không
dính. Vậy `plane_equation.py` là chỗ duy nhất lệch khỏi quy ước của chính kho.

---

## 5. Cache · candidate — ĐO, không suy

```
PRODUCT_CODE_CHANGED          YES  (1 file: plane_equation.py)
MODEL_FACING_CONTRACT_CHANGED NO   (prompt · thẻ · lược đồ · năng lực: 0 byte)
CACHE_VERSION                 94 → 94   KHÔNG bump
CANDIDATE_HASH                ddeb0518… → d72db7c3…   (92 file, đã đóng băng lại)
PRODUCT_CAPABILITY_CHANGED    NO
```

### Vì sao không bump — kiểm bằng một row cache thật

`main.py:865` và `:900` chỉ ghi cache khi `envelope.status == "ok"`. Nên chỉ hai
chiều có thể làm hỏng một row đã có: `served → rejected`, hoặc **đáp số đổi**.
Đo trên cả bảy ca dương (`CACHE_IMPACT.json`, dựng bản trước-vá bằng cách vô
hiệu hoá `chuan_hoa_dau_tru`):

```
SERVED_TO_REJECTED   0
ANSWER_CHANGED       0
REJECTED_TO_SERVED   1        (p6: 'z + 12 = 0' → '2x - z + 12 = 0')
STALE_ROW_HAZARD     false
```

Một đề **từng bị từ chối chưa bao giờ tạo row nào**, nên không có row cũ để trở
thành sai. Cùng lập luận đã ghi ở `main.py:471` cho một wave trước.

### Hồi quy

`pytest` toàn bộ: **0 hồi quy hình học**. `replay_demo_cases` 5/5 ·
`audit_demo_crash_surface` 6/6 ném 0.

---

## 6. Chứng nhận bằng entrypoint THẬT

Certifier gọi `run_thesis_final_acceptance.chay_lut` — **đúng hàm** mà `--live`
gọi, cùng thân, cùng cổng canh, cùng thứ tự ghi artifact. Khác đúng một thứ:
`provider` truyền vào là stub. Đó không phải chi tiết —
`V3_LIVE_ENTRYPOINT_INTEGRATION_BLOCKER` đã trả giá cho lỗ ngược lại.

**Mười lăm nhãn, tất cả PASS:**

```
FIXED_CORPUS_LOADER              MANIFEST_BEFORE_FIRST_CALL
ALL_RAW_ATTEMPTS_RETAINED        CANONICAL_POSITIVE_SCORER
CANONICAL_NEGATIVE_SCORER        STAGE_A_ONE_ATTEMPT
STAGE_B_ONE_REPAIR               STAGE_B_REUSES_FROZEN_CONTRACT
STAGE_B_REUSES_RAW_CANDIDATE     THESIS_POLICY_LOADED
IDENTITY_GUARD_BEFORE_EVERY_CALL BUDGET_GUARD_BEFORE_EVERY_CALL
REAL_PROVIDER_CALLS_ZERO         NETWORK_REFERENCES_RESTORED
GOLD_CONTRACT_REACHABLE
```

Kết quả lượt stub: **7/7 ca dương servable** (6 ngay chặng A, 1 qua
`RECOVERY_WITHIN_ONE_REPAIR`) · **2/2 ca âm fail-closed** ·
`SILENT_WRONG_ANSWER_COUNT = 0` · **19 lượt gọi** (9 analyze + 9 tổng hợp + 1
sửa) · 0 lượt gọi thật.

### Nhãn thứ 15 sinh ra từ một lỗi thật

`GOLD_CONTRACT_REACHABLE` không có trong đặc tả — nó được thêm vì lượt chứng
nhận phát hiện gold preflight của wave trước dùng **thẳng** `request_contract_gold`
với `provenance="confirmed"` viết tay, tức **chưa bao giờ đi qua**
`build_request_contract` — biên duy nhất quyết định hợp đồng thật sự trông thế
nào. Hệ quả: `p6` khai mặt phẳng bằng dấu trừ ASCII trong khi đề dùng U+2212,
extractor không chứng minh được, fact ra `claimed`, bất biến nguồn đỏ.

Nhãn này đòi **mọi hợp đồng gold tái tạo được qua biên thật mà không sinh
`unproven_values`**. Corpus được sửa một ký tự mỗi ca (`-` → `−`, trùng byte với
đề) trong cùng amendment.

### Nhật ký sự kiện

Mười tám loại sự kiện, kiểm cả **thứ tự**: `write_manifest` trước mọi `*_call`;
`freeze_contract` trước `synthesis_call`; `write_stage_a` trước `repair_call`.
Cổng danh tính và cổng ngân sách kiểm **trước từng** lượt gọi — `_canh_truoc_moi_goi`
đếm theo khoảng chứ không đếm tổng, vì một cổng chạy hai lần ở đầu rồi im lặng
về sau vẫn cho tổng đẹp.

---

## 7. Khoá danh tính — và chỗ cắt vòng

```
RUNNER_HASH   19c4c311e1ae7274…      LOCK_STATE  LOCKED_READY_FOR_FINAL_EXECUTION
SCORER_HASH   4f7cae906500e0b6…      CERTIFICATION_HASH  88f020afa135f95b…
POLICY_HASH   a44469b001a62d22…      CANDIDATE_HASH      d72db7c324cf61f3…
CORPUS_HASH   2eb3f24df4b3e124…      EXPECTED_RESULTS    1099924b73bf8e54…
GOLD_PREFLIGHT 985c8922f11d9f5e…     CACHE_VERSION       94
```

`IDENTITY_LOCK.json` **chứa** `RUNNER_HASH`, nên nếu phép băm runner đọc file ấy
thì mỗi lần ghi sẽ đổi băm và không bao giờ hội tụ. Vòng bị cắt bằng **tập file**,
không bằng một mẹo tính toán:

| | |
|---|---|
| trong `RUNNER_HASH` | đúng **một** file: `backend/scripts/run_thesis_final_acceptance.py` |
| ghim RIÊNG (`RUNNER_MODULE_HASHES`) | `thesis_acceptance_corpus.py` · `thesis_acceptance_oracle.py` · `acceptance_integrity.py` · `measurement_policy.py` |
| **ngoài** băm | mọi artifact `.json` — kể cả chính `IDENTITY_LOCK.json` |

Chạy `--lock-runner` hai lần cho **cùng một băm**, và certifier chạy lại **sau**
khi khoá vẫn PASS — §16 bước ⑥⑦.

⚠️ **Một lỗ đã bịt trong chính wave này**: `dung_identity_lock` đặt
`RUNNER_HASH = None`, nên một lượt sinh lại artifact SAU khi khoá sẽ **mở khoá
im lặng**. Nay khoá cũ được mang sang, và chỉ mất **có tiếng** khi runner thật
sự đổi (kèm băm trước/sau).

---

## 8. Cổng

| cổng | kết quả |
|---|---|
| `test_thesis_runner_alignment.py` | **50 pass** (17 phép tiêm nhóm F) |
| `test_thesis_acceptance_matrix.py` | **49 pass** |
| `pytest -q` toàn bộ backend | xem §9 |
| chứng nhận runner (stub) | **15/15 nhãn PASS**, 0 lượt gọi thật |
| gold preflight | 7/7 servable · exact · oracle · postconditions · scene3d |
| `freeze_evaluation_candidate --verify` | exit 0 — 92 file, `d72db7c3…` |
| `lock_cache_identity --verify` | exit 0 @ v94 |
| `replay_demo_cases` | 5/5 |
| `audit_demo_crash_surface` | 6/6, ném 0 |
| frontend + build | **INHERITED** — `FRONTEND_TRACKED_BYTES_CHANGED = NO` |

**Mười bảy phép tiêm** (§15 đòi ≥10). Bốn cái bắt lỗi **thật** trong lúc dựng:
stub nhận nhầm ca vì so 80 ký tự đầu (`p4`/`p6` trùng tiền tố); ca âm `servable`
với đáp số `0` vì hợp đồng stub rỗng nghĩa vụ; `SILENT_WRONG_ANSWER_COUNT` không
đếm ca âm được phục vụ; guard V3 tự đỏ vì đọc chính docstring của nó.

---

## 9. Việc kế tiếp

```
NEXT_ACTION = THESIS_FINAL_ACCEPTANCE_EXECUTION
```

Lượt đánh giá cuối chạy trên **đúng** `IDENTITY_LOCK.json` này:

```bash
cd backend && ALLOW_LIVE_AI=1 PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe \
  scripts/run_thesis_final_acceptance.py --live --out-dir <thư mục MỚI>
```

⚠️ **Trần cứng: 25 lượt gọi logic · 100 lần thử vật lý · 196 000 token.** Runner
dừng khi chạm trần. Trước khi chạy, chạy lại `--certify` để chứng minh mọi băm
còn khớp — một lượt live trên artifact đã trôi không gắn với bản nào cả.

⚠️ **Không sửa corpus, policy hay identity lock để kết quả đẹp hơn.** Chúng khoá
TRƯỚC kết quả, và đó là toàn bộ giá trị của chúng.
