# SEGMENT_RELATION_CONSISTENCY_VERIFICATION

> 2026-09-06. **`APPLICATION_LLM_CALLS = 0`** — replay, fixture và phép tiêm.
> Không mở năng lực toán học, không đổi kernel, không đổi bề mặt mô hình.
>
> ```
> R3_A_BEFORE = served, PF = 15/2      R3_A_AFTER = từ chối ở source_invariant
> CACHE_VERSION 81 → 82 (BUMP)         CANDIDATE c39f7358… → 1151bc6f…
> ```

## 1. Root cause — chứng minh, không suy luận

Lượt `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB`, ca `r3` arm A. Đề:

> *"Cho đoạn thẳng EF có độ dài 10. Điểm P nằm trên đoạn EF sao cho
> **FP = 4·PE**. Tính độ dài PF."*

Mô hình viết `divide_segment(E, F, 1/4)` ⇒ `P = (5/2, 0, 0)`, tức `PE = 5/2`
chứ không phải `2`. Hệ trả **`served`** với `PF = 15/2`. Đáp số đúng là `8`.

**Ba tầng đều làm đúng việc của chúng** — và đó mới là chỗ đáng sợ:

| tầng | làm gì | có sai không |
|---|---|---|
| kernel | thi hành `a + t·(b−a)` trên chương trình ĐÃ NHẬN | **không** |
| `check_distance` | tính lại từ hình, ra đúng `PF` của `P` **đã dựng** | **không** |
| `grounding` | thấy `P` có `source_fact_id = 'vi_tri_diem'` ⇒ cho qua | **không** |

> **ROOT_CAUSE.** `source_fact_id` chứng minh **nguồn được viện có tồn tại**.
> Nó không, và không thể, chứng minh **hình dựng ra thoả nội dung của nguồn
> ấy**. Không tầng nào hỏi câu *"điểm này có đúng là điểm đề nói tới không"*,
> nên một quan hệ đoạn thẳng bị hiểu sai hỏng **IM LẶNG**: học sinh nhận một
> đáp số sai được trình bày y hệt một đáp số đúng.

Bản đồ cạnh, mỗi cạnh có bằng chứng:

```
quan hệ trong đề        RequestContract.problem_text          (request_contract.py:121)
   → hợp đồng           InputFact.values = ['P thuộc EF và FP = 4·PE']  ← VĂN BẢN TỰ DO
   → chương trình       construct_point P = divide_segment(E,F,'1/4')
   → bộ nhớ hình học    P = Vec3(5/2, 0, 0)                   (kernel.py:72)
   → coverage           radius/distance: PASS  (đo đúng hình ĐÃ dựng)
   → checker            check_distance → 15/2  (geometry_obligations.py:134)
   → verdict            served                 ← LỖ Ở ĐÂY
```

## 2. Tái hiện — ba lượt, 0 lượt gọi

`docs/evaluation/geometry/segment-relation-verification/REPLAY_R3.json`
(chương trình **nguyên văn** của lượt A/B, `sha256` nguồn ghi trong artifact).

| lượt | tầng | servable | `P` | `PF` | postconditions | scene |
|---|---|---|---|---|---|---|
| `t = 1/4` (nguyên văn) **trước** vá | `served` | **True** | `(5/2,0,0)` | `15/2` | `distance(P)` verified | 5 |
| `t = 1/4` **sau** vá | `source_invariant` | **False** | `(5/2,0,0)` | `15/2` | NOT_REACHED | NOT_REACHED |
| `t = 1/5` (đúng) | `served` | **True** | `(2,0,0)` | **`8`** | `distance(P)` verified | **5** |

Lượt thứ hai là cả điểm của wave: **phép đo vẫn đúng (`15/2` là khoảng cách
thật tới `P` đã dựng), hình thì sai dữ kiện, và verdict nay là từ chối.**

## 3. Khả năng biểu đạt — trước và sau

**`CURRENT_CONTRACT_CAN_EXPRESS_SEGMENT_RELATION = PARTIAL`.** Đo, không đoán:

| thứ cần biểu diễn | trước wave |
|---|---|
| văn bản tự do trong `InputFact.values` | **có** — và chỉ có thế |
| tên điểm / tên đoạn | có (`_MAU_DOAN_THANG`) |
| **độ dài một đoạn**, máy đọc được | **CÓ** — `SourceInvariant(kind="segment_length")` |
| điểm nằm trên đoạn | **không** |
| tỉ lệ hai đoạn con | **không** |
| độ dài từ một đầu đoạn | **không** |
| tham số hướng `t` | **không** |

Hai thứ đã có sẵn và wave này **dùng lại nguyên vẹn**:

- `check_source_invariants` (`postconditions.py:638`) chạy ở **P0**
  (`route.py:322`), so bằng `Fraction` bình phương, **không `float`**, và dùng
  chung lưới hoà giải tên `ten_da_hoa_giai`;
- nó đã có **dispatch theo `kind`** — `"chưa có checker cho '{kind}'"` — tức
  được thiết kế sẵn để thêm loại.

Hai thứ còn thiếu: **không có `kind` cho quan hệ chia đoạn**, và bộ phát duy
nhất (`bat_bien_nguon`) chỉ chạy trên đường **chuẩn hoá thang**, nên một đề
cho số như `r3` không phát bất biến nào.

⇒ **Nhánh A**: dùng lại thẩm quyền sẵn có, không dựng thẩm quyền thứ hai.
Consumer trước đây bỏ sót vì nó ra đời để chữa một bệnh khác (*sai THANG* ở
`wave6-canary-b`), và quan hệ chia đoạn chưa từng có ca sai đi qua.

## 4. Biểu diễn đã chọn — không thêm trường nào

```
SourceInvariant(
    kind        = "segment_division"
    points      = (A, B, M)      A→B là HƯỚNG CỦA ĐỀ; M là điểm bị ràng buộc
    expected    = t hữu tỉ chính xác,  M = A + t·(B − A)
    source_fact_id / source_text / scale_symbol   giữ nguyên vai trò cũ
)
```

Ý nghĩa của `points` do `kind` quyết và khai ở **đúng một chỗ**
(`segment_relation.bat_bien_chia_doan`). `m:n` không bị mất: `t = m/(m+n)` là
song ánh với `m:n` khi hướng đã cố định, và thông điệp lỗi in lại `m:n` bằng
`t : (1−t)`.

**Vì sao không thêm trường:** `SourceInvariant` là server-owned, nên thêm
trường vẫn rẻ — nhưng không cần. Không thêm trường nghĩa là **không consumer
nào khác phải đổi**, và `expected` giữ đúng bất biến mà checker đang dựa vào
(*chuỗi phân số chính xác*).

**Vì sao đọc từ ĐỀ, không đọc từ lời khai của mô hình.** Doctrine đã đăng ký
ngay trong `SourceInvariant`: *"toán hạng lấy từ chỗ khác: chính câu văn của
đề"*, và trong `check_source_invariants`: *"không có đường nào để một chương
trình tránh bị kiểm bằng cách im lặng"*. Một cổng gác cửa mà đọc chuỗi do LLM
tự đặt tên thì nó đang gác chính thứ nó phải nghi ngờ.

Ba dạng đọc được, đều đòi neo **"trên đoạn XY"** (không có neo thì không biết
đoạn nào bị chia):

| dạng | ví dụ | `t` |
|---|---|---|
| ① tỉ số | `CN : ND = 2 : 3` | `2/5` |
| ② bội số | `FP = 4·PE` | `1/5` |
| ③ độ dài một nhánh | `AM = 9` + `AB` dài `12` | `3/4` |
| ④ trung điểm | `I là trung điểm của GH` | `1/2` |

**Không khớp ⇒ KHÔNG phát**, theo đúng luật `bat_bien_nguon` đã đặt: *bỏ sót
là kết cục chấp nhận được, đoán bừa thì không* — một bất biến trỏ nhầm vật sẽ
**kết tội một chương trình đúng**, hỏng nặng hơn hẳn kiểm thiếu một dòng.

## 5. Authority và tầng chặn

| câu hỏi | chủ sở hữu |
|---|---|
| quan hệ nào có trong đề | `segment_relation.bat_bien_chia_doan` (**mới**) |
| gắn vào hợp đồng ở đâu | `analyze_contract.build_request_contract` — biên đóng băng, *"MỌI đường gọi đều thấy cùng một hợp đồng"* |
| hình có thoả quan hệ không | `postconditions.check_source_invariants` — **không dựng cổng thứ hai** |
| số học | `Fraction` + `Vec3` hữu tỉ, y như nhánh `segment_length` |

Phép kiểm, tất cả trên **hình**, không trên chuỗi `ratio`:

1. `A`, `B`, `M` có mặt và là `Vec3`; thiếu ⇒ `not_checkable`, **không** vi phạm.
2. `A ≠ B`; suy biến ⇒ `not_checkable`.
3. Giải `t` trên trục có thành phần khác 0, rồi **đối chiếu lại cả ba thành
   phần** — chính phép đối chiếu ấy **là** phép kiểm thẳng hàng, nên không cần
   một phép `cross` riêng và không có đường nào để một điểm lệch khỏi đường
   thẳng lọt qua.
4. So `t` bằng `Fraction`. `t ∉ [0,1]` ⇒ lệch `t` ⇒ bác (điểm ngoài đoạn).
5. Hướng `A→B` lấy từ **đề**, nên chương trình viết `(E,F,1/5)` hay `(F,E,4/5)`
   đều đúng — hai cách viết cùng một điểm.

Mã lỗi giữ **`NORMALIZED_SOURCE_VIOLATED`** (ổn định, đã có), tầng chặn là
`stage_reached = "source_invariant"`, **trước** `served`. Thông điệp nêu đủ năm
thứ (khoá bởi `test_B2`):

```
Điểm P nằm trên đoạn EF sao cho FP = 4·PE: đề cho EP:PF = 1:4 (t = 1/5),
hình dựng có 1:3 (t = 1/4); điểm sai: P (nguồn: vi_tri_diem)
```

## 6. Phản ví dụ, phép tiêm, regression

`backend/tests/geometry/test_segment_relation_consistency.py` — **36 pass**,
0 lượt gọi model.

| # | yêu cầu | test |
|---|---|---|
| 1 | `r3/A` `t=1/4` bị bác | `B1`, `B2` |
| 2 | `r3` `t=1/5` được phục vụ, `PF=8` | `B3` |
| 3 | đảo toán hạng `(F,E,4/5)` vẫn đúng | `B4` |
| 4 | `AM:MB = 2:3` ⇒ `t = 2/5` | `A1[r2]` |
| 5 | phân số tương đương `2/10` ≡ `1/5` | `B5` |
| 6 | trung điểm vẫn đúng | `A1[r4]`, regression `r4` |
| 7 | điểm ngoài đoạn bị bác | `B6` (`t = 2`, `−1/5`, `3/2`) |
| 8 | thẳng hàng nhưng sai tỉ lệ bị bác | `B1` (`r3/A`) |
| 9 | viện sai nguồn | xem §7 — **grounding** lo, cổng này cố ý không đọc |
| 10 | hai ràng buộc, hai điểm, kiểm độc lập | `C7`, `A4` |
| 11 | đo đúng hình nhưng hình sai dữ kiện ⇒ chưa `served` | `B7` |
| 12 | chương trình không có ràng buộc giữ hành vi cũ | `E1`, `C8` |

Biên khác: không thẳng hàng (`C1`) · đoạn suy biến (`C3`) · thiếu điểm (`C4`)
· sai arity (`C5`) · `segment_length` cũ không bị ảnh hưởng (`C8`) · miền
không-hình-học không phát (`E3`) · móc chạy ở đường sản phẩm (`E2`) · năm lối
nói **không** khớp thì không phát (`A2`) · hai ràng buộc cho **cùng** một điểm
thì bỏ cả hai (`A3`).

**Phép tiêm:**

| tiêm | phải xảy ra | test |
|---|---|---|
| gỡ bộ đọc quan hệ | `r3/A` **`served` trở lại** với `15/2` | `D1` |
| đảo hướng bất biến, giữ `t` | đỏ | `D2` |
| thay so `Fraction` bằng `float` | ca `1/3` và biên `3333/10000` đỏ | `D3` |

**Regression giữ nguyên:** `r1`/`r2`/`r3`/`r4` gold **4/4 `served`**, đáp số
đúng, mỗi ca nay mang một bất biến **đang hoạt động** · `e4` `t=5/7` bán kính
`15` · binding container · point initialization · curved distance witness ·
`e1`/`e5`. Toàn bộ suite: **3923 pass**, 0 đỏ — không test cũ nào vỡ.

## 7. Grounding và provenance — giữ nguyên, có chủ đích

Cổng này **không** đọc `source_fact_id` của chương trình để quyết định có kiểm
hay không. Đó là doctrine đã đăng ký (*"đó chính là chỗ hỏng"*), và giữ nó có
hệ quả cụ thể: một chương trình **không thể** tránh bị kiểm bằng cách im lặng
hay bằng cách viện sai nguồn.

Việc *"viện sai `source_fact_id`"* vẫn do **`grounding_gate`** xử — không đổi
một dòng. `source_fact_id` trong bất biến là **server tự tra** và chỉ dùng để
viết lời giải thích. **`GROUNDING_AND_PROVENANCE_PRESERVED = YES`.**

## 8. Identity, cache, candidate

**`MODEL_FACING_CONTRACT_CHANGED = NO`** — đo bằng cách so với HEAD:

| thành phần | trước | sau |
|---|---|---|
| `prompts` | `55ac1ca6…` | **không đổi** |
| `grammar_card` | `e0fbbc84…` (thẻ sản phẩm == `card_A.txt`) | **không đổi** |
| `synthesis_schema` | `8c57c9de…` | **không đổi** |
| `analyze_schema` | `515001b5…` | **không đổi** |
| `capability` | `85bd3167…` | **không đổi** |
| `semantic_environment` | `f7def620…` | **không đổi** |

`source_invariants` **không có trong lược đồ analyze** (kiểm bằng máy) — nó là
dữ liệu **server tự phát**, nên mở rộng nó không chạm bề mặt mô hình.

**`CACHE_DECISION = 81 → 82, BUMP.`** Và đây là bump **ngược chiều** hai wave
trước — lý do phải nói rõ:

| wave | chiều đổi | `main.py` cache gì | stale? |
|---|---|---|---|
| `CURVED_SCALAR…`, `POINT_INIT…` | *từ chối → phục vụ* | chỉ `status == "ok"` | **không** — bản từ chối chưa bao giờ được cache |
| **wave này** | **phục vụ → từ chối** | chỉ `status == "ok"` | **CÓ** — bản phục vụ **sai** ĐÃ được cache |

Chứng minh bằng **một row thật**, không bằng suy luận: ghi envelope
`{"status":"ok","final_memory":{"do_dai_pf":"15/2"}}` ở `policy_version = 81`,
rồi gọi `_cache_lookup` ⇒ **HIT**, envelope sai được trả về nguyên vẹn, và
`main.py:638` trả thẳng từ row nên **không đi qua cổng mới**. Đó là bằng chứng
trực tiếp cần invalidation.

Bốn chỗ đồng bộ đã sửa: `main.py` · `test_api.py` (kèm lý do) ·
`docs/CURRENT_STATE.md` · manifest candidate. `lock_cache_identity.py` chạy
lại và tự xác nhận *"môi trường không đổi, chỉ version lệch"*.

**`CANDIDATE_BEFORE_AFTER = c39f7358… → 1151bc6f…`** (89 → **90** file,
`--verify` exit 0).

⚠️ **Đính chính một khoá liên-wave.** `test_CA1` của
`POINT_INITIALIZATION_CONTRACT_ALIGNMENT` ghim `CACHE_VERSION == "81"`. Kết
luận *"wave ấy không bump"* **vẫn đúng**; nhưng một con số toàn cục không thuộc
về một wave, nên phần ghim hằng số đã bỏ, phần bản chất (*row ghi ở version
hiện tại thì HIT*) giữ nguyên. Ghi chú đính chính viết ngay trong docstring.

## 9. Phạm vi và chi phí

`APPLICATION_LLM_CALLS = 0`. `PRODUCT_CAPABILITY_CHANGED = NO` — tập phép,
kernel, ranh giới hỗ trợ không đụng; **ball/cylinder/cone vẫn
`foundation_only`**. V3 và mọi artifact lịch sử **không đổi một byte**; replay
mới lưu riêng.

Wave này dựng **nền tính đúng**, chưa đưa ra kết luận nào về token:

- `r3/A` là bằng chứng **AI đã sinh một mô phỏng SAI và hệ đã phục vụ nó**;
- bản sửa chứng minh hệ **ngăn được** lỗi đó, ở đúng tầng, trước `served`;
- **`MODEL_DISCOVERABILITY = NOT_MEASURED`** — wave không gọi model, nên khả
  năng mô hình tự sinh đúng quan hệ chưa đo;
- **`TOKEN_EFFICIENCY = NOT_MEASURED`** — token trên một ca thành công toàn
  pipeline chưa đo.

## 10. Giới hạn còn lại

- **Bộ đọc phủ bốn lối nói, không phải mọi lối nói.** Đo được: đề `e4`
  (*"cắt PQ tại điểm T sao cho PT = 20, tính từ đỉnh P"*) **không** khớp mẫu
  nào ⇒ không phát bất biến ⇒ ca ấy **giữ nguyên hành vi cũ**. Đây là fail-
  closed theo hướng *bỏ sót*, đúng luật đã đăng ký — nhưng nó có nghĩa là lỗ
  chỉ đóng cho những đề diễn đạt theo bốn mẫu trên.
- Chỉ mở quan hệ **chia đoạn**. Quan hệ hình học khác (song song, vuông góc,
  thuộc mặt phẳng, tỉ số thể tích) chưa có ca sai đi qua cùng đường ⇒ vào
  backlog, không mở theo suy đoán.
- Bất biến gắn theo **tên điểm của đề**; chương trình đặt tên khác thì phải
  nhờ lưới hoà giải `ten_da_hoa_giai`. Không hoà giải được ⇒ `not_checkable`,
  **không** phải vi phạm.
- Hai ràng buộc cho cùng một điểm ⇒ bỏ cả hai (tầng này chỉ đọc rời rạc, không
  đủ tư cách phân xử).

## 11. Kết luận

```
ROOT_CAUSE = source_fact_id chung minh NGUON TON TAI, khong chung minh HINH
             DUNG THOA NOI DUNG cua nguon; khong tang nao hoi "diem nay co
             dung la diem de noi toi khong" ⇒ hong IM LANG
CURRENT_CONTRACT_CAN_EXPRESS_SEGMENT_RELATION = PARTIAL
             (co SourceInvariant + dispatch theo kind + cong P0;
              thieu kind chia doan va bo phat ngoai duong chuan hoa thang)
SELECTED_REPRESENTATION = SourceInvariant(kind="segment_division",
             points=(A,B,M) huong A→B cua DE, expected=t huu ti) — 0 truong moi
RELATION_VERIFICATION_AUTHORITY = postconditions.check_source_invariants
             (MOT cong, khong dung cong thu hai) · doc:
             segment_relation.bat_bien_chia_doan · moc:
             analyze_contract.build_request_contract
R3_A_BEFORE = served · PF = 15/2 · postconditions verified · scene 5
R3_A_AFTER  = TU CHOI o stage `source_invariant` ·
              NORMALIZED_SOURCE_VIOLATED · thong diep neu du 5 thu
R3_CORRECT_PROGRAM = served · PF = 8 · postconditions verified · scene 5
SILENT_WRONG_ANSWER_CLOSED = YES cho bon loi noi da phu (§10 khai gioi han)
OPERAND_DIRECTION_VERIFIED = YES  ((E,F,1/5) va (F,E,4/5) deu duoc phuc vu)
EXACT_RATIO_VERIFIED       = YES  (Fraction; 2/10 ≡ 1/5; bien 3333/10000 bi bat)
GROUNDING_AND_PROVENANCE_PRESERVED = YES (cong khong doc source_fact_id cua
              chuong trinh — doctrine giu nguyen; grounding khong doi mot dong)
MODEL_FACING_CONTRACT_CHANGED = NO (6 bam byte-identical)
CACHE_DECISION   = 81 → 82, BUMP — chieu doi la `served → tu choi`, ma
              `served` LA thu duoc cache. Chung minh bang ROW THAT: envelope
              PF=15/2 ghi o v81 van HIT va duoc tra ve khong qua cong moi
CANDIDATE_BEFORE_AFTER = c39f7358… → 1151bc6f…  (89 → 90 file, verify exit 0)
APPLICATION_LLM_CALLS = 0
MODEL_DISCOVERABILITY = NOT_MEASURED
TOKEN_EFFICIENCY      = NOT_MEASURED
PRODUCT_CAPABILITY_CHANGED = NO (ball/cylinder/cone van foundation_only)
RECOMMENDED_NEXT_ACTION = RATIO_AB_CONFOUND_REMOVAL_REPEAT
```

## 12. Cổng đã chạy

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| `pytest -q` (cây sạch @ `c0c6c68`) | **3923 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| wave suite | **36 pass** | **mới** |
| gold `r1`–`r4` qua cổng mới | **4/4 served**, đáp số đúng | **mới** |
| `test_api` · `test_cache_identity` · `test_current_state_identity` | **37 pass** | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `certify_acceptance_runner.py` | **PASS**, 0 lượt gọi, 4 nhãn | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file | **mới** |
| `git diff --check` | sạch | **mới** |
| vitest · `npm run build` | — | **kế thừa** (frontend không đụng: `git diff --stat -- frontend/` rỗng) |

**Việc kế tiếp.** Lỗi phục vụ sai đã đóng, nên quay lại đúng việc đang treo:
**`RATIO_AB_CONFOUND_REMOVAL_REPEAT`** với ngân sách nhỏ. Phép đo ấy nay báo
được đồng thời **ba** con số mà lượt trước không tách nổi: tỉ lệ sinh đúng ·
tỉ lệ `served` **đúng** (nay có cổng này bảo đảm `served` nghĩa là đúng dữ
kiện) · token trên một kết quả đúng.
