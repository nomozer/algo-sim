# DERIVED_POINT_CONSTRUCTION_ENFORCEMENT

> 2026-09-07. **`APPLICATION_LLM_CALLS = 0`** — replay, fixture, phép tiêm.
> Không mở năng lực toán học, không đổi kernel, không đổi bề mặt mô hình.
>
> ```
> TRƯỚC: khai thẳng toạ độ P, bỏ phép dựng  →  served, PF = 8
> SAU  : bác ở grounding, DERIVED_ENTITY_WITHOUT_PRODUCER
> CACHE_VERSION 84 → 85 (BUMP)   CANDIDATE a9289410… → 36e81713…
> ```

## 1. Trạng thái đầu — khớp bàn giao

HEAD `0835857` · cây **sạch** · `CACHE_VERSION` **84** · candidate
`a9289410…` (verify exit 0, 90 file) · `PRODUCT_VARIANT` **A**
(`grammar_card` == `card_A.txt`).

Sáu băm model-facing @ v84: `prompts 55ac1ca6…` · `grammar_card e0fbbc84…` ·
`synthesis_schema 8c57c9de…` · `analyze_schema 515001b5…` ·
`capability 85bd3167…` · `semantic_environment f7def620…`.

## 2. Tái hiện và nguyên nhân — theo đường chạy thật

`docs/evaluation/geometry/derived-point-construction-enforcement/TRUOC_SUA.json`

Đề: *"Cho đoạn thẳng EF có độ dài 10. Điểm P nằm trên đoạn EF sao cho
FP = 4·PE. Tính độ dài PF."*

Chương trình khai thẳng `P = [2,0,0]`, **bỏ câu lệnh dựng**:

| | trước sửa |
|---|---|
| stage | **`served`** |
| `PF` | **`8`** — đáp số **đúng** |
| số câu lệnh còn lại | **1** (`assign do_dai_pf`) |
| khung trace | **0** |
| `P` trong scene | **không có** |

**Nguyên nhân, hai nửa.** Chốt ⑥ của `grounding_gate` hỏi **đúng** câu này rồi
(*"đề giới thiệu nhãn này như điểm phải dựng ra"*), nhưng:

- nó đọc `source_entities.nhan_suy_ra`, mà bộ ấy chỉ khớp `"gọi/lấy X là …"`
  và `"X là trung điểm|hình chiếu|giao điểm|trọng tâm|chân đường|tâm|điểm đối
  xứng"`. Lối nói *"Điểm P nằm trên đoạn EF **sao cho** …"* không khớp cái nào
  ⇒ `la_ten_suy_ra("P") = False`;
- và chốt ⑥ **chỉ chạy trong nhánh `model_assumption`**. Đo được: lỗ đi được
  **cả hai** kênh xuất xứ — `initial_value + model_assumption` **và**
  `initial_value + source_fact_id` đều `served`.

> **Thẩm quyền sở hữu yêu cầu này** là `grounding_gate` (chốt ⑥/⑦), không phải
> bất biến nguồn: bất biến hỏi *"điểm ấy có đúng chỗ không"*, grounding hỏi
> *"giá trị ấy ở đâu ra"*. Cả hai đều cần, và chúng không thay nhau được.

## 3. Ranh giới, chốt trước khi sửa

| lớp | định nghĩa | quyền |
|---|---|---|
| **điểm đầu vào** | đề cho toạ độ hoặc dữ kiện tương ứng | khai toạ độ — **giữ nguyên** |
| **lựa chọn hệ trục** | đặt vị trí cho điểm đầu vào | `model_assumption` — **giữ nguyên** |
| **điểm dẫn xuất** | vị trí do quan hệ chia đoạn **đã giải được** xác định | **phải dựng** |

Hai chốt hẹp, cả hai đều là ranh giới §2:

- **Chỉ *"M thuộc AB"* thì CHƯA ĐỦ.** Phải có quan hệ **giải được ra `t`** —
  tức `segment_division`, không phải `segment_division_unresolved`. Bản chưa
  giải nghĩa là hệ mới thấy đề *nói về* một phép chia (`test_C3`).
- **Chỉ vế thứ ba `M`.** Hai đầu mút `A`, `B` là điểm đầu vào (`test_C1`).

## 4. Sửa tại thẩm quyền hiện có

Thêm **chốt ⑦** trong `grounding_gate`, đặt **sau** chốt `computed` (đã biết
chương trình không tính ra vật này) và **trước** khi rẽ theo kênh xuất xứ —
nên nó phủ cả hai kênh, khác chốt ⑥.

Tín hiệu **dùng lại**, không dựng bộ nhận diện thứ hai: `_diem_phai_dung()`
đọc `SourceInvariant(kind="segment_division")` đã có sẵn trên hợp đồng — chính
kết quả nhận diện bộ ba của `segment_relation`. Nới `nhan_suy_ra` thay vì đọc
tín hiệu có sẵn sẽ đổi hành vi **mọi** wave khác dùng chung hàm ấy.

Mã lỗi **dùng lại** `ERR_THIEU_NGUOI_DUNG = "DERIVED_ENTITY_WITHOUT_PRODUCER"`
— đúng nghĩa, đã tồn tại. Thông điệp nêu đủ bốn thứ (`test_A3`):

```
P: được đề xác định bằng một QUAN HỆ CHIA ĐOẠN, nên vị trí của nó là HỆ QUẢ
phải dựng ra, không phải dữ kiện để khai. Hãy dựng bằng
`divide_segment(<đầu này>, <đầu kia>, <tỉ lệ>)` — engine sẽ tính toạ độ và
ghi bước dựng vào trace.
```

### Producer giả — ba đường, ba thẩm quyền, **không nới thêm**

§3 cảnh báo *"bí danh hoặc câu lệnh không liên quan không chứng minh được bước
dựng"*. Đo từng đường thay vì gộp (`test_C7`):

| đường | ai chặn | mã |
|---|---|---|
| `literal` thẳng vào `P` | `ir_static` | `AMBIGUOUS_FIRST_BINDING` |
| bí danh sang điểm **có thật** (`P = E`) | `source_invariant` | sai vị trí |
| bí danh qua điểm **bịa** đặt sẵn đúng chỗ | `grounding` ⑤ | `UNANCHORED_DERIVED_ASSUMPTION` |

Cả ba đã có chủ ⇒ chốt ⑦ **giữ nguyên phạm vi**, không mở rộng theo suy đoán.

## 5. Kiểm chứng

`backend/tests/geometry/test_derived_point_construction.py` — **23 pass**,
1 phép tiêm; cộng `test_frame_origin_provenance.py` **15 pass**.

| nhóm | nội dung |
|---|---|
| `A1`–`A4` | khai sẵn + bỏ phép dựng ⇒ **bác** (cả `P` lẫn `N`) · bác **dù đáp số đúng** · thông điệp đủ bốn thứ · **cả ba tổ hợp kênh xuất xứ** đều bác |
| `B1` | dựng bằng `divide_segment` ⇒ **served**: `(E,F,1/5)` và **đảo chiều** `(F,E,4/5)` cùng cho `8`; `(C,D,2/5)` và `(D,C,3/5)` cùng cho `6` |
| `B2` | dựng **sai tỉ lệ** ⇒ vẫn bị `source_invariant` chặn — chốt ⑦ **không thay** bất biến |
| `B3` | khai toạ độ **nhưng vẫn có** lệnh dựng ⇒ qua (giá trị đến từ phép dựng) |
| `C1`–`C6` | điểm đầu vào · lựa chọn hệ trục · quan hệ **chưa giải được** · hợp đồng không bất biến · **hai đoạn** ràng buộc đúng bộ ba · đổi tên và đổi số |
| `C7` | ba đường producer giả (bảng §4) |
| `D1` | ca đúng: `P` có `origin = "derived"`, `producer = "construct_point.divide_segment"`, `depends ⊇ {E, F}` |
| `D2` | ca thiếu bước dựng **không bao giờ tới scene** — dừng trước execution |
| `E1` | **phép tiêm**: ngắt tín hiệu ⇒ ca khai sẵn **lọt lại**, `served` với `8` |

**`test_C1` của wave trước đã lật.** Nó ra đời như một test **đang xanh** ghi
nhận lỗ, kèm lời hứa *"wave sau đóng thì nó ĐỎ, và đỏ là đúng"*. Nay nó khẳng
định hành vi đúng, **giữ nguyên** chú thích lịch sử và **giữ** khẳng định
`la_ten_suy_ra("P") is False` — gốc của lỗ chưa đổi, chỉ có tín hiệu khác lo.

## 6. Bảo toàn kết quả đúng đã đạt

`.../derived-point-construction-enforcement/BAO_TOAN.json`

| replay | kết quả |
|---|---|
| `r2`/ratioB sau delta provenance | **served · 6** |
| `r3`/ratioB sau delta provenance | **served · 8** |
| `r3` sai ratio | **bác** ở `source_invariant` (`15/2`) |
| `e4` đúng | **served · bán kính 15** |
| `e4` sai tỉ lệ **trong khối** | **bác** ở `source_invariant` (`21/2`) |
| phản ví dụ `F = [99,0,0]` | **bác** ở `source_invariant` (`396/5`) |

Dòng cuối là **chuỗi trước/sau mà artifact bàn giao còn thiếu**: wave trước chỉ
lưu bản *trước* của `396/5`; nay có cả bản *sau*.

## 7. Identity, cache, candidate

**`MODEL_FACING_DELTA = NONE`** — sáu băm **byte-identical**
(`f7def620…` không đổi), chỉ version lệch.

**`CACHE_DECISION = 84 → 85, BUMP`**, đo bằng **row thật**: envelope
`{"do_dai_pf": "8"}` ghi ở `policy_version 84` vẫn **HIT** và trả về nguyên
vẹn, **không đi qua cổng mới**.

⚠️ Ca này **khác ba bump trước ở một chỗ đáng ghi**: envelope cũ có **đáp số
ĐÚNG**. Thứ sai là **mô phỏng** — không có bước dựng nào cho `P`, trace 0
khung, `P` không có trong scene. `served` vẫn là thứ được cache, nên row cũ
vẫn phải bỏ.

**`CANDIDATE_BEFORE_AFTER = a9289410… → 36e81713…`** (90 file, verify exit 0).
`PRODUCT_VARIANT` **A → A** · `PRODUCT_CAPABILITY_CHANGED = NO`.

## 8. Cổng đã chạy

| cổng | kết quả | mới / kế thừa |
|---|---|---|
| test wave | **23 pass**, 1 phép tiêm | **mới** |
| `test_frame_origin_provenance` (C1 đã lật) | **15 pass** | **mới** |
| grounding · source invariant · producer · trace | trong hai suite trên | **mới** |
| `pytest -q` (cây cuối) | **3999 pass**, 1 skip, 1 deselect, **0 đỏ** | **mới** |
| `test_api` · `test_cache_identity` · `test_current_state_identity` | **37 pass** | **mới** |
| `replay_demo_cases.py` | **5/5**, `REDUCED_CHAIN 1/1` | **mới** |
| `audit_demo_crash_surface.py` | **6/6 biên**, ném **0** | **mới** |
| `certify_acceptance_runner.py` | **PASS**, 0 lượt gọi | **mới** |
| `freeze_evaluation_candidate --verify` | **exit 0**, 90 file | **mới** |
| `git diff --check` | sạch | **mới** |
| vitest · `npm run build` | — | **kế thừa** (frontend không đụng) |

## 9. Giới hạn còn lại

- **Chỉ trong lớp quan hệ đã kiểm chứng**: chia đoạn, và chỉ khi bộ đọc **giải
  được** ra `t`. Lối nói ngoài ba neo × bốn quan hệ vẫn là `NOT_EXTRACTED` —
  hệ **không chặn**, và đó là giới hạn **phủ**, không phải fail-closed.
- **"Độ dài mâu thuẫn ⇒ không phát bất biến"** tiếp tục đúng và tiếp tục được
  khai. Wave này là *yêu cầu dựng điểm*, không phải giải quyết mọi mâu thuẫn
  đầu vào.
- Chốt ⑥ và `nhan_suy_ra` **không đổi** — lối nói *"nằm trên … sao cho"* vẫn
  không được nhận ở đó. Chốt ⑦ lo phần chia đoạn; các họ quan hệ khác nếu cần
  thì phải có tín hiệu riêng.
- Ba mức bằng chứng **không được trộn**: *"đáp số đúng"* · *"có bước dựng
  đúng"* (wave này đóng) · *"AI tự sinh ổn định"* (**chưa đo** — 0 lượt gọi).

## 10. Kết luận

```
NGUYEN_NHAN        = chot ⑥ doc `nhan_suy_ra`, bo ay khong nhan loi noi
                     "nam tren … sao cho"; va chot ⑥ chi chay trong nhanh
                     `model_assumption` trong khi lo di duoc CA HAI kenh
THAM_QUYEN_SUA     = grounding_gate, chot ⑦ `_diem_phai_dung` — doc lai tin
                     hieu segment_relation, KHONG dung bo nhan dien thu hai
CA_THIEU_BUOC_DUNG = TRUOC served · PF = 8 · 1 cau lenh · trace 0 khung
                     SAU   bac o grounding · DERIVED_ENTITY_WITHOUT_PRODUCER
CA_DUNG_DUNG       = (E,F,1/5) → served · 8   ·  (C,D,2/5) → served · 6
DAO_CHIEU          = (F,E,4/5) → served · 8   ·  (D,C,3/5) → served · 6
TRACE_PRODUCER_DEP = P: origin=derived · producer=construct_point.divide_segment
                     · depends ⊇ {E, F}
CHONG_BAC_OAN      = diem dau vao · lua chon he truc · quan he CHUA GIAI ·
                     hop dong khong bat bien · hai doan · doi ten/doi so ·
                     3 duong producer gia (moi duong mot tham quyen san co)
MODEL_FACING_DELTA = NONE (6 bam byte-identical)
CACHE_VERSION      = 84 → 85 (BUMP, do bang row that; envelope cu co DAP SO
                     DUNG — thu sai la MO PHONG)
CANDIDATE          = a9289410… → 36e81713…
PRODUCT_VARIANT    = A → A     PRODUCT_CAPABILITY_CHANGED = NO
TEST               = 3999 pass, 1 skip, 1 deselect, 0 do
COMMITS            = 2         WORKING_TREE = sach
APPLICATION_LLM_CALLS = 0
RECOMMENDED_NEXT_ACTION = PROVENANCE_AFFORDANCE_AB_4_LUOT
```

**Việc kế tiếp.** Wave đạt, nên bàn giao đúng thứ đã chuẩn bị: **A/B
provenance, 4 lượt live**, cả hai arm dùng **cùng nền hướng dẫn `ratio`**
(artifact B của `RATIO_AFFORDANCE_STAGED_RECHECK`), **chỉ khác** hướng dẫn
provenance. Nền đo nay vững hơn hẳn: `served` từ wave này trở đi có nghĩa
*"dựng đúng **bằng các bước dựng**"*, không chỉ *"ra đúng số"* — nên chỉ số
`served đúng` của lượt A/B ấy mới đo được thứ đề tài thật sự hứa.

⚠️ Token của Claude Code **không** tính vào token vận hành AlgoSim; replay,
checker và Scene3D không dùng token Gemini.
