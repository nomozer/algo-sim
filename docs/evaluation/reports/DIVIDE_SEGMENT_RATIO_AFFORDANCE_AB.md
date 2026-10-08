# DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB

> 2026-09-06. Hai phần: **§1–3 tất định, 0 lượt gọi** · **§4–7 một lượt A/B
> live, 8 lượt tổng hợp**.
>
> ```
> MEASUREMENT_CLASS = DEVELOPMENT_SYNTHESIS_AB   HELD_OUT_CLAIM = NO
> ANALYZE_LIVE_CALLS = 0     SYNTHESIS_LOGICAL_CALLS = 8/8
> PRODUCT_VARIANT = A (giữ nguyên)   CACHE_VERSION = 81 (không đổi)
> ```
>
> Wave **không đụng một dòng nào** trong `backend/app` hay `frontend/src`;
> candidate `c39f7358…` giữ nguyên, `--verify` exit 0.

## 1. Đính chính fixture `e4` — và một tiền đề bị bác

Bàn giao nêu: *"`e4.json` chứa chương trình sau chuẩn hoá, mất `source_fact_id`,
dù được mô tả là trích nguyên văn"*. Kiểm bằng máy thì **nửa sau không đúng**:

| khoá trong `e4.json` bàn giao | `source_fact_id` ở câu lệnh |
|---|---|
| `chuong_trinh_tho` ← **bản test đọc** | `mat_phang_cat`, `duong_tron_t` — **CÓ ĐỦ** |
| `chuong_trinh_da_parse_luot_ab` | rỗng (bản chuẩn hoá của lượt A/B cũ) |

Cả năm chỗ trong `test_obligation_container_binding.py` đều đọc
`chuong_trinh_tho` (dòng 59 và 69), nên **không** có test nào chạy trên bản bị
tước trường.

**Khiếm khuyết thật thì hẹp hơn, và có thật:** khối `nguon_goc` dán nhãn
*"raw_candidate (NGUYÊN VĂN, chưa qua parse)"* cho **cả bản ghi**, trong khi
bản ghi chứa **hai** chương trình; bản thứ hai không có nhãn xuất xứ riêng, và
không bản nào có hash. Một người đọc sau có thể lấy nhầm bản. Đã sửa: mỗi ca
nay giữ **bốn** bản, mỗi bản một `sha256` và một `duong_dan_nguon`:

| bản | nội dung | dùng làm gì |
|---|---|---|
| `raw_candidate` | CHUỖI JSON mô hình sinh | gốc |
| **`parsed_input`** | sau `json.loads` | **fixture của test** |
| `normalized_program` | sau validator, mã **hiện tại** | đối chiếu |
| `normalized_luot_ab_CU` | bản chuẩn hoá lượt A/B **cũ** | bằng chứng lịch sử |

Delta giữa bản cũ và bản hiện tại chính là thứ wave trước khôi phục:

```
e4  norm_CŨ      decl thiếu xuất xứ của `mat_phang_cat`, `duong_tron_t`
    norm_HIỆN    có đủ cả hai
e5  norm_CŨ      thiếu `plane_j`;   norm_HIỆN có
e1  không lệch   (mô hình không khai `source_fact_id` ở assign nào)
```

Artifact A/B lịch sử **không đổi một byte**; replay mới lưu riêng.

## 2. Replay `e4` từ bản thô — ba lượt, 0 lượt gọi

`docs/evaluation/geometry/divide-segment-ratio-ab/REPLAY_E4_FROM_RAW.json`

| lượt | tầng đạt được | đáp số | postconditions | scene |
|---|---|---|---|---|
| nguyên văn | `execution` · `CURVED_PLANE_DOES_NOT_CUT` | — | NOT_REACHED | NOT_REACHED |
| chỉ đổi `ratio 5/2 → 5/7` | **`served`** | **`ban_kinh_t = 15`** | `radius((t))` **verified** | **12** |
| đổi `ratio` **+ tắt bản vá binding** | `structural_coverage` | — | NOT_REACHED | NOT_REACHED |

Lượt thứ ba là điều phải chứng minh: **sửa `ratio` một mình không cứu được ca.**
Hai nguyên nhân tách bạch, mỗi cái cần một bản vá riêng.

⚠️ `scene` đo bằng `app.ai.pipeline._dung_scene3d`, không bằng
`route.verify_and_compile` — route **cố ý** không dựng cảnh
(`V3_PRODUCT_PATH_PARITY_CORRECTION`).

## 3. Thay đổi được đăng ký — nhỏ đến mức nào

Kernel, xác nhận trực tiếp (`geometry/kernel.py:72`):

```
divide_segment(a, b, t) = a + t·(b − a)      t = 0 → a,  t = 1 → b
chia trong đoạn theo m : n   ⇒   t = m/(m+n)
```

Đề lịch sử `PT = 20`, `PQ = 28`, `a = P`, `b = Q` ⇒ `t = 5/7`. Mô hình viết
`5/2` — tỉ số `m:n`, không phải tham số.

**Vì sao mô hình hiểu vậy — đo được, không suy đoán.** Thẻ in nguyên văn:

```
divide_segment: a:tên<point3>[điểm đầu] b:tên<point3>[điểm cuối] ratio:tên
```

Hai điều cùng lúc: `a`/`b` có chú thích còn `ratio` **không có**, và nhãn kiểu
của nó là **`tên`** — tức thẻ đang nói với mô hình rằng `ratio` là một CÁI TÊN.
Gốc: `_kieu()` gọi `_la_ten()`, mà `_la_ten` trả `True` cho mọi `str` trần; còn
`_vai_tro(f)` — hàm in `Field.description` ra ngoặc — **chỉ chạy ở nhánh ô-tên**.
Nên mô tả `"phân số, vd 2/3"` đã nằm sẵn ở `contract.py:625` **chưa bao giờ tới
thẻ**.

**Arm B = một dòng.** Dùng `_VAN_XUOI` — bảng văn xuôi sẵn có, cùng cơ chế đang
phục vụ `title`/`label`:

```
- ratio:tên
+ ratio:t trong M = a + t(b−a); chia trong đoạn m:n ⇒ t = m/(m+n)
```

| | |
|---|---|
| delta | **+60 byte, đúng 1 dòng** |
| `card_A` | `c7c001c4…` — **byte-đối-byte** với thẻ sản phẩm đang chạy **và** `card_A.txt` của lượt `operation-affordance-ab-v1` |
| `card_B` | `25d43370…` |
| `responseSchema` | **KHÔNG đổi** — `_VAN_XUOI` không đi vào JSON schema, hai arm dùng lược đồ y hệt |
| tên trường · kiểu · kernel · phần thẻ khác | không đổi |

Thiết kế thay thế (đổi `Field.description` + in `_vai_tro` ở nhánh vô hướng) đã
được đo và **loại**: +1857 byte, 17 dòng — nó sẽ làm phép quy kết mất giá trị.

## 4. Chuẩn bị phép đo

Bốn đề ngắn, **không cho toạ độ**, đều hỏi một **độ dài** — nên oracle bất biến
với hệ trục mô hình tự chọn. Hợp đồng **cố định và đã kiểm**; `analyze` = 0.

| ca | dạng | `t` đúng theo chiều | đáp số |
|---|---|---|---|
| `r1` | độ dài từ đầu đoạn + cả đoạn (`AB=12`, `AM=9`) | `A→B` 3/4 · `B→A` 1/4 | `MB = 3` |
| `r2` | tỉ số `m:n` (`CD=10`, `CN:ND = 2:3`) | `C→D` 2/5 · `D→C` 3/5 | `ND = 6` |
| `r3` | **bất đối xứng** (`EF=10`, `FP = 4·PE`) | `E→F` 1/5 · `F→E` 4/5 | `PF = 8` |
| `r4` | **đối chứng** trung điểm (`GH=8`) | 1/2 cả hai chiều | `IH = 4` |

Gold preflight **4/4 `served`**, đáp số khớp, scene 4 mỗi ca.
Bộ chấm tra `t` theo **chiều thực tế** chương trình viết, không theo một chiều
giả định — `r3` tồn tại để bắt đúng lỗi ấy.

Toàn vẹn runner chứng minh **trước** lượt live bằng provider stub, chạy chính
`main_async`: `tests/geometry/test_runner_ratio_ab.py` **23 pass** — analyze = 0,
one-shot, trần sản phẩm được khôi phục, hai arm cùng hợp đồng, payload chỉ khác
**đúng một dòng** đã đăng ký, manifest ghi trước lượt gọi đầu, telemetry tách
được token từng arm, guard ngân sách chặn và báo `INCOMPLETE` mà **vẫn giữ** mọi
attempt đã gọi.

Đăng ký (hash, corpus, oracle, lịch, ngân sách, luật quyết định) chốt **trước**
kết quả: `registration.json`.

## 5. Kết quả — bảng ghép cặp

`ratio_ab_ratio-ab-20260906T115624Z.json` · `RUN_STATUS = COMPLETE` ·
8/8 lượt logic · 8/32 lượt vật lý.

| ca | arm | vị trí | `t` viết | `t` đúng cho chiều | stage | đáp số | token |
|---|---|---|---|---|---|---|---|
| `r1` | A | **PASS** | `9/12` | `3/4` | `served` | `3` | 7027 |
| `r1` | B | NOT_REACHED | `9/12` | `3/4` | **`grounding`** | — | 4382 |
| `r2` | A | **PASS** | `2/5` | `2/5` | `served` | `6` | 6771 |
| `r2` | B | **PASS** | `2/5` | `2/5` | `served` | `6` | 6674 |
| `r3` | A | **FAIL** | `1/4` ✗ | `1/5` | `served` | **`15/2`** | 6057 |
| `r3` | B | NOT_REACHED | `1/5` ✓ | `1/5` | **`grounding`** | — | 6056 |
| `r4` | A | **PASS** | `midpoint` | — | `served` | `4` | 5450 |
| `r4` | B | NOT_REACHED | `midpoint` | — | **`grounding`** | — | 4886 |

### 5a. ĐÍNH CHÍNH BỘ CHẤM — khai trước khi dùng số

`T_CORRECT` so **chuỗi** thay vì so **hữu tỉ**, nên `9/12` bị chấm `FAIL` trong
khi `9/12 = 3/4`. Đã sửa và **chấm lại artifact cũ, 0 lượt gọi**
(`SCORING_CORRECTION.json`); bảng số gốc trong artifact lượt chạy **giữ nguyên**.

Đính chính chạm `r1/A`, `r1/B`, `r3/B` ở cột `t` — và **không** đổi quyết định,
vì luật đăng ký phán theo `POSITION_CORRECT`, cột mà đính chính không chạm tới.

### 5b. Trục `ratio` — thứ wave này đi hỏi

| | A | B |
|---|---|---|
| `t` đúng, ca mục tiêu | **2/3** (`r3` sai: viết `1/4`) | **3/3** |
| cặp thắng / thua | — | **thắng 1 (`r3`) · thua 0** |
| đối chứng `r4` | dùng `midpoint` — cách dựng tương đương, ghi nhận riêng, không trừ điểm | như A |

### 5c. NHIỄU LẤN ÁT: B chết ở `grounding` 3/4 ca

Cả ba lượt hỏng của B là **cùng một nguyên nhân, không liên quan `ratio`**:

```
input_not_grounded — "A: có initial_value nhưng thiếu source_fact_id"
```

Mô hình bỏ `source_fact_id` ở khai báo điểm. A không mắc lỗi này lần nào; B mắc
3/4. Với **n = 4, one-shot, temperature 0.1**, không quy kết được cho delta hay
cho nhiễu lấy mẫu — và nói được cái nào cũng là nói quá. Đây là **giới hạn quyết
định** của lượt đo.

### 5d. Một quan sát về an toàn, đáng ghi

`r3/A` **`served` một đáp số SAI** — `15/2` thay vì `8` — và mọi cổng đều đúng:
checker tính lại từ hình cho đúng điểm `P` mà chương trình dựng; hệ không có
cách nào biết `P` ấy không phải `P` của đề. Nghĩa là **hiểu nhầm `ratio` hỏng
theo kiểu IM LẶNG**, không fail-closed. Đó là lý do mạnh nhất để đóng affordance
này, mạnh hơn cả lý do token.

## 6. Chi phí — và trần đã bị vượt

Công thức: **tổng = `total_tokens`** (`totalTokenCount` của API, **đã gồm**
thoughts). Không cộng `prompt + candidates + thoughts` (đếm trùng);
`cached_content` là **tập con** của prompt. Gồm cả ca thành công lẫn thất bại.

| | A | B |
|---|---:|---:|
| prompt | 13 643 | 13 743 |
| candidates | 2 117 | 1 993 |
| thoughts | 9 545 | **6 262** |
| cached (tập con của prompt) | 1 993 | 1 993 |
| **tổng** | **25 305** | **21 998** |
| ca đúng vị trí | 3/4 | 1/4 |
| ca `served` **và** khớp đáp số | 3/4 | 1/4 |
| **token / ca đúng vị trí** | **8 435** | **21 998** |
| **token / ca served đúng** | **8 435** | **21 998** |

Cả hai mẫu số dương ⇒ phép so **xác định**: **B ĐẮT HƠN ~2,6 lần** trên một kết
quả đúng. Prompt của B chỉ dài hơn 100 token (khớp thẻ +60 byte); chỗ chênh
tổng nằm ở **thoughts**, và B nghĩ ít hơn — nhưng lợi ích ấy bị nuốt sạch vì B
chỉ cho 1 kết quả dùng được.

⚠️ **`TOKEN_CEILING_EXCEEDED`: 47 303 / 40 000.** Guard kiểm **trước mỗi cặp**
nên nó chặn được việc *bắt đầu* một cặp khi đã quá hạn, nhưng không cắt được
giữa cặp — cặp cuối đẩy tổng vượt trần. Giới hạn thiết kế của guard, ghi lại để
lượt sau đặt trần theo cặp chứ không theo tổng.

## 7. Quyết định — theo luật đã đăng ký, không nới

Luật đăng ký: *"Tín hiệu cải thiện cần B đúng **vị trí** ở cả ba ca mục tiêu, có
ít nhất một cặp thắng và giữ đối chứng đúng."*

B đúng vị trí ở **1/3** ca mục tiêu (`r2`) ⇒ **tín hiệu KHÔNG đạt**.

```
GIU_BASELINE_A = YES        PRODUCT_VARIANT = A
B = ỨNG VIÊN, chưa đủ bằng chứng — và bị NHIỄU GROUNDING lấn át
```

Không nới luật sau khi xem số. Trục `ratio` có tín hiệu dương yếu (3/3 vs 2/3,
thắng 1 thua 0) nhưng nó **không phải** tiêu chí đã đăng ký, nên nó được báo
riêng như một quan sát, không dùng để nhận B.

### Ba câu hỏi kết luận

1. **AI dựng đúng hơn chưa?** — *Chưa kết luận được.* Trên trục `ratio` B viết
   `t` đúng 3/3 so với A 2/3 (thắng 1, thua 0), nhưng trên tiêu chí đã đăng ký
   — **đúng vị trí** — B chỉ đạt 1/3 vì 3/4 chương trình của nó chết ở
   `grounding` **vì một lý do không liên quan**. n = 4, one-shot ⇒ không tách
   được delta khỏi nhiễu.
2. **Có bằng chứng giảm token trên một kết quả đúng chưa?** — **KHÔNG.** Ngược
   lại: 21 998 (B) so với 8 435 (A) trên một kết quả đúng, cả hai mẫu số dương.
3. **Bằng chứng thuộc loại nào?** — **Tổng hợp với hợp đồng CỐ ĐỊNH.** Không
   phải toàn pipeline: `analyze` = 0, repair = 0. **`CHI_PHI_TOAN_PIPELINE =
   NOT_MEASURED`** — chưa được phép nói *"hệ sinh mô phỏng tiết kiệm token hơn"*.

## 8. Cổng đã chạy

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| `pytest -q` (cây sạch @ `3b499ad`) | **3887 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| `test_runner_ratio_ab` (stub, 0 lượt gọi) | **23 pass** | **mới** |
| `test_obligation_container_binding` | **27 pass** | **mới** (fixture đổi khoá) |
| gold preflight 4 ca | **4/4 served**, khớp oracle | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, `c39f7358…` | **mới** |
| vitest · `npm run build` | — | **kế thừa** (frontend không đụng) |

**Cache/candidate.** Wave chạm `backend/scripts`, `backend/tests`, `docs` —
**không** chạm `MEASURED_SYSTEM_PATHS`. `CACHE_VERSION` **81 → 81, không bump**
(không đổi prompt, lược đồ, thẻ sản phẩm hay policy định tuyến); candidate
`c39f7358…` **không đóng băng lại**. `card_B.txt` là **artifact**, không phải mã
sản phẩm — thẻ sống vẫn là A, khoá bởi `test_AB1`/`test_E8` và
`test_I2` của wave trước.

## 9. Giới hạn

- **Nhiễu grounding lấn át** — 3/4 lượt B hỏng vì thiếu `source_fact_id`; n = 4
  one-shot không tách được nguyên nhân.
- **`TOKEN_CEILING_EXCEEDED`** 47 303/40 000; guard theo cặp, không theo tổng.
- Đo **một** ứng viên B, **một** lượt, `temperature 0.1` — không đo lặp lại.
- Tái lập **`LIMITED`**: model gọi bằng **alias** `gemini-2.5-flash`, không phải
  snapshot bất biến; `model_version_or_snapshot` để **trống** trong manifest.
- `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED` · `CHI_PHI_TOAN_PIPELINE =
  NOT_MEASURED`.
- Nhãn kiểu **`ratio:tên`** là một lỗi rộng hơn `divide_segment`: `_la_ten` trả
  `True` cho **mọi** `str` trần, nên mọi ô vô hướng kiểu `str` đều đang được
  giới thiệu với mô hình là "tên". Chưa đo phạm vi.

## 10. Kết luận

```
ROOT_CAUSE_AFFORDANCE   = the in `ratio:tên` (nhan KIEU sai) va BO chu thich;
                          `Field.description` co san nhung `_vai_tro` chi chay
                          o nhanh o-TEN nen no chua bao gio toi the
REGISTERED_DELTA        = +60 byte · 1 dong · `_VAN_XUOI['ratio']`
                          responseSchema KHONG doi; hai arm dung luoc do y het
FIXTURE_CORRECTION      = e1/e4/e5 nay giu 4 ban co hash; test doc `parsed_input`
E4_REPLAY_FROM_RAW      = nguyen van → execution · +ratio(5/7) → served 15 ·
                          +ratio nhung tat binding → structural_coverage
T_CORRECT_TARGET        = A 2/3 · B 3/3   (thang 1 · thua 0)
POSITION_CORRECT        = A 3/4 · B 1/4   ← tieu chi DA DANG KY
CONFOUND                = B chet `grounding` 3/4 ca vi thieu `source_fact_id`
                          — KHONG lien quan ratio; n=4 khong quy ket duoc
SILENT_WRONG_ANSWER     = r3/A served `15/2` thay vi `8` — hieu nham ratio hong
                          theo kieu IM LANG, khong fail-closed
TOKEN_PER_CORRECT       = A 8 435 · B 21 998   (B DAT hon ~2,6x)
TOKEN_CEILING           = EXCEEDED 47 303/40 000
SCORING_ERRATUM         = T_CORRECT so chuoi thay vi huu ti (9/12 vs 3/4);
                          da cham lai 0 luot goi; KHONG doi quyet dinh
DECISION                = GIU BASELINE A — tin hieu dang ky KHONG dat
PRODUCT_VARIANT         = A        CACHE_VERSION = 81 (khong bump)
CANDIDATE               = c39f7358… (khong dong bang lai)
APPLICATION_LLM_CALLS   = 8 (tong hop) · ANALYZE_LIVE_CALLS = 0
EVIDENCE_CLASS          = SYNTHESIS_WITH_FIXED_CONTRACT
                          (KHONG phai toan pipeline)
MODEL_DISCOVERABILITY   = NOT_MEASURED
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
RECOMMENDED_NEXT_ACTION = RATIO_AB_CONFOUND_REMOVAL_REPEAT
```

**Vì sao việc kế tiếp là thế.** Lượt này trả lời được câu *"delta có làm mô hình
viết `t` đúng hơn không"* ở mức **tín hiệu yếu, dương** — nhưng câu trả lời bị
một lỗi khác che mất ở tầng dưới, và `n = 4` one-shot không đủ để tách. Việc kế
tiếp là **lặp lại đúng phép đo này sau khi gỡ nhiễu**, không phải mở thêm delta:
tăng lên `k = 2` mỗi arm mỗi ca (16 lượt tổng hợp), đặt trần token **theo cặp**
thay vì theo tổng, và giữ nguyên luật quyết định đã đăng ký. Chỉ khi tín hiệu
`POSITION_CORRECT` đạt mới bàn tới đo **toàn pipeline** để nói được câu về chi
phí thật.
