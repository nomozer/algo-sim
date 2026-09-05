# CURVED_DISTANCE_WITNESS_VERIFICATION

> 2026-09-05. **`APPLICATION_LLM_CALLS = 0`** · `V3_REEXECUTED = NO` ·
> `V3_ARTIFACTS_CHANGED = NO` · `PRODUCT_CAPABILITY_CHANGED = NO`.
>
> Fixture `c7a` — **`POST_V3_DEVELOPMENT_FIXTURE`**. V3 đã tiêu; đây là replay
> tất định trên dữ liệu đã công bố, **không** phải một lượt acceptance mới.

## 1. ROOT_CAUSE

`c7a` khai `distance(container="hinh_non", witness="l")` để nói *"đường sinh"*.
Nhưng `distance` là phép đo **quan hệ** — giữa hai đối tượng — nên checker thử
đo trên chính `hinh_non: curved_solid` và trả *"cặp đối tượng không hợp lệ"*.

Phép đo **thật** nằm ở câu lệnh sinh witness:

```
l = measure(distance, of=T, wrt=A)
```

và `T`, `A` là **đỉnh** và **điểm vành** của chính khối ấy.

Nhưng lỗi không chỉ ở checker. Đo hết đường thì có **ba** cổng cùng bác, mỗi
cổng vì một lý do khác:

| tầng | lý do |
|---|---|
| `structural_coverage` — kiểm kiểu | `accepts_container_type("distance", "curved_solid")` = False |
| `structural_coverage` — dẫn xuất witness | *"witness `l` không dẫn xuất từ `hinh_non` — chương trình khai đáp án chứ không tính nó"* |
| `postconditions` | `check_distance` đo trên container ⇒ *"cặp đối tượng không hợp lệ"* |

Cổng thứ hai là cổng đáng giá nhất và cũng là cổng bác **oan** rõ nhất: witness
**có** đo thật, chỉ là đo từ toán hạng **dựng ra** container, không từ container.

## 2. Reproduction trước sửa

```
obligations   distance(hinh_non, witness=l) · volume(hinh_non, witness=V)
              lateral_area(hinh_non, witness=Sxq)
declared      H,T,A: point3 · hinh_non: curved_solid · l,V,Sxq: float
statements    construct_curved_solid hinh_non cone anchor=H apex_or_top=T rim_point=A
              l   = measure(distance, of=T, wrt=A)
              V   = measure(volume, of=hinh_non)
              Sxq = measure(lateral_area, of=hinh_non)

stage         postconditions
executable    True
servable      False
error_code    postcondition_violated / verification_gap
details       ['cặp đối tượng không hợp lệ cho khoảng cách', …]
final_memory  l=13 · V=100π · Sxq=65π      ← ĐÚNG TRỌN
```

Phân biệt sáu khái niệm mà báo cáo cũ trộn làm một:

| | `c7a` |
|---|---|
| obligation container | `hinh_non` |
| witness variable | `l` |
| witness producer | `assign l = measure(...)` |
| measure operands | `of=T`, `wrt=A` |
| operand types | `point3`, `point3` |
| attachment evidence | `{T, A} ⊆ _phu_thuoc["hinh_non"] = {H, T, A}` |

## 3. Attachment — chứng minh được bằng dữ liệu có cấu trúc

Đây là câu hỏi quyết định của §3: nếu không chứng minh được thì wave phải dừng
với `BLOCKED_BY_MISSING_ATTACHMENT_AUTHORITY`.

**Chứng minh được, và bằng một thẩm quyền đã có.** `coverage_gate._phu_thuoc`
tính bao đóng phụ thuộc của mọi biến; với `hinh_non` nó cho `{H, T, A}` — chính
là toán hạng của câu lệnh dựng. Không đọc tên biến, không đọc chữ trong đề,
không rẽ nhánh theo họ hình.

### Phản ví dụ — vì sao chấp nhận mọi distance witness là KHÔNG sound

`test_F8` dựng chương trình đo `distance(of=X, wrt=Y)` giữa hai điểm **rời
khối** rồi gán vào `l`. Nếu bỏ phép kiểm attachment, chương trình ấy cũng
"chứng thực" được đường sinh của nón — phép kiểm mất sạch giá trị. Nó phải bị
bác, và nó bị bác.

## 4. Resolver

`coverage_gate.phan_giai_witness(spec, ob, declared) -> WitnessDaPhanGiai`

```
witness_target · producer_statement · quantity · operands
operand_types  · binding_evidence   · diagnostic_status
```

Tám bước, mỗi bước một trạng thái chẩn đoán riêng:

| bước | trạng thái khi hỏng |
|---|---|
| ① `params.witness` là chuỗi | `WITNESS_KHONG_KHAI` |
| ② đúng **một** câu lệnh sinh witness | `WITNESS_KHONG_CO_PRODUCER` · `WITNESS_NHIEU_PRODUCER` |
| ③ producer là `measure` | `PRODUCER_KHONG_PHAI_MEASURE` |
| ④ `quantity` khớp nghĩa vụ **sau canonical hoá** | `QUANTITY_LECH` |
| ⑤ chữ ký toán hạng từ `BANG_PHEP_DO` | — |
| ⑥ toán hạng đủ và đúng kiểu | `THIEU_TOAN_HANG` · `TOAN_HANG_SAI_KIEU` |
| ⑦ toán hạng ⊆ bao đóng dựng của container | `KHONG_GAN_VOI_CHU_THE` |
| ⑧ | `OK` |

Bước ④ gọi `nghia_vu_chinh_tac` — tức nó **kế thừa** phép quy đổi
`area(ball) → lateral_area` của wave trước, không dựng bản thứ hai.

Bước ⑤ đọc `PhepDo.hai_toan_hang` — **không** chép tay danh sách toán hạng.

**MỘT thẩm quyền cho cả hai consumer.** `coverage_gate` định nghĩa,
`postconditions` import. `test_P7` quét AST cả hai file để chứng minh không ai
dựng bản phân giải riêng.

## 5. Hợp đồng sau sửa

**`distance` GIỮ nghĩa quan hệ.** Postconditions dựng một nghĩa vụ **tương
đương** trên đúng toán hạng đã phân giải rồi gọi **checker cũ** — không viết
phép đo thứ hai. Checker vẫn tính lại từ hình; `l` chỉ là giá trị khai để đối
chiếu, không phải bằng chứng tự xác nhận.

**Đường unary giữ nguyên.** `_lien_ket_khong_truc_tiep` chỉ cho phép đi đường
witness khi chủ thể **không** nhận nghĩa vụ trực tiếp. `radius(ball)`,
`volume(curved_solid)`, `lateral_area(curved_solid)`, `area(ball)` chấm thẳng
như trước.

### ⚠️ Một hồi quy do chính wave này gây ra, và cách sửa

Bản đầu của tôi nhận resolver cho **mọi** nghĩa vụ mà kiểu chủ thể không khớp —
kể cả phép đo **một** toán hạng, nơi `of` chính *là* container. `test_15b` bắt
được ngay: nó replay một trạng thái CŨ để chứng minh cổng phủ vẫn bác
`volume(of=S)`, và bản đầu cho qua — tức vô hiệu hoá đúng phép kiểm kiểu mà
nhánh ấy tồn tại để làm.

Sửa: cả ba chỗ dùng resolver đều đòi `len(operands) > 1`.

### ⚠️ Một phép nối cũ phải thu hẹp

`_theo_witness_do` (hợp đồng buộc tên, wave `circumsphere`) đề xuất
`container ≡ of` khi witness đo đúng lượng đo. Với `c7a` nó nối `hinh_non ≡ T`,
rồi bí danh ấy **rò sang hai nghĩa vụ anh em** — `volume(hinh_non)` bị chấm
trên một ĐIỂM. Một chương trình đúng trọn vẹn hỏng vì một phép nối đúng ý nhưng
sai chỗ.

Chỉ phép đo **một** toán hạng mới đồng nhất được chủ thể với `of`; với phép đo
quan hệ, `of` là một trong hai toán hạng nên nó không định danh chủ thể. Arity
đọc từ `BANG_PHEP_DO`, không phải một danh sách ngoại lệ.

## 6. `c7a` — replay sau sửa

```
C7A_COVERAGE_PASS       YES
C7A_RUNTIME_PASS        YES
C7A_POSTCONDITIONS_PASS YES
C7A_EXACT_RESULTS       l=13 · V=100π · Sxq=65π
C7A_SCENE3D_PASS        YES
C7A_SERVABLE            YES
```

## 7. Tests

`backend/tests/geometry/test_curved_distance_witness.py` — **18 test**.
Nền ĐỎ trước sửa: **7 failed / 11 passed**.

| nhóm | nội dung |
|---|---|
| R (2) | ba đáp số đúng · attachment chứng minh bằng `_phu_thuoc` |
| C (2) | resolver trả đủ cấu trúc · chữ ký dẫn từ `BANG_PHEP_DO` |
| P (6) | `c7a` servable · tên witness trung tính (`zzz`) · phép đo một toán hạng · sibling giữ binding · `c1a` vẫn served · hai consumer chung resolver |
| F (5) | witness không tồn tại · producer không phải `measure` · quantity lệch · thiếu `wrt` · **witness không gắn với container** |
| S (3) | không so tên `l` · không nhánh `cone` · không chép tay chữ ký |

### Fault injection

Mười phép, và ba phép được **đo thật** khi chúng đỏ trong lúc phát triển:

| # | tiêm | test đỏ |
|---|---|---|
| ① | bỏ đọc `params.witness` | `test_C1` · `test_P1` |
| ② | đổi quantity của producer | `test_F4` |
| ③ | bỏ toán hạng `wrt` | `test_F5` |
| ④ | bỏ kiểm kiểu toán hạng | `test_C1` (`operand_types`) |
| ⑤ | **bỏ attachment proof** | `test_F8` — phản ví dụ hai điểm rời khối |
| ⑥ | cho phép nhiều producer | `WITNESS_NHIEU_PRODUCER` |
| ⑦ | hai resolver khác nhau | `test_P7` (quét AST) |
| ⑧ | checker tin thẳng giá trị `l` | `test_F3` — `l = literal 13` bị bác |
| ⑨ | **ghi đè binding dùng chung** | `test_P6` — đo được THẬT trong lúc sửa |
| ⑩ | khôi phục chấm thẳng trên container | `test_P1` |

⑨ và phép nhận nhầm unary (§5) là hai lỗi **wave này tự gây ra rồi tự bắt** —
ghi ra vì chúng là dữ liệu về hình dạng của bài toán, không phải phiền toái.

## 8. Test cũ phải đổi — và vì sao

**Sáu test trong `test_acceptance_post_model_path.py`** dùng `c7a` làm fixture
cho hình dạng *"executable nhưng không servable"*. Wave này **đóng** đúng lỗ đó,
nên `c7a` không còn đóng được vai ấy.

Chuyển sang `duong_4_he_hut_verification` của certifier — `angle` trên
`vector3`, một verification gap **thật và vẫn đang mở**. Hợp đồng bốn cột giữ
nguyên chỗ dựa; `c7a` cập nhật thành `CORRECT_SERVABLE_RESULT`.

Đây là lần thứ ba trong chuỗi wave này một test phải đổi vì nó khoá **trạng
thái** thay vì khoá **luật**. Lần này khác hai lần trước ở một điểm đáng ghi:
trạng thái ấy là *một lỗi hệ đang mở*, và test dùng nó làm ví dụ. Ví dụ thì hết
hạn khi lỗi được sửa — nên hợp đồng phải trỏ vào một lỗi **khác còn mở**, chứ
không phải bỏ hợp đồng.

## 9. Identity và cache

| | trước | sau |
|---|---|---|
| `ANALYZE_SCHEMA_HASH` | `515001b503af5c7c…` | *không đổi* |
| `SYNTHESIS_SCHEMA_HASH` | `8c57c9de49824d61…` | *không đổi* |
| `GRAMMAR_CARD_HASH` | `e0fbbc8456da57ae…` | *không đổi* |
| `PROMPT_HASH` | `55ac1ca6a6df92ce…` | *không đổi* |
| `STABLE_CAPABILITY_HASH` | `85bd316781b86576…` | *không đổi* |
| `SEMANTIC_ENVIRONMENT_HASH` | `f7def6207f5741d9…` | *không đổi* |
| `CACHE_VERSION` | 80 | **81** |
| `CANDIDATE_HASH` | `9e25d5f92a1b3f87…` | **đo ở §10** |

```
MODEL_FACING_CONTRACT_CHANGED        NO
CHECKER_OR_COVERAGE_BEHAVIOR_CHANGED YES
PRODUCT_CAPABILITY_CHANGED           NO
```

### Vì sao bump lần này KHÁC lần trước

Wave trước tôi kiểm và thấy **không** envelope nào hoá sai (chỉ `status == "ok"`
được cache, nên bản từ chối chưa bao giờ vào cache) — bump theo luật.

Lần này có **stale thật**, và nó đến từ chiều **thu hẹp**: `_theo_witness_do`
không còn đồng nhất chủ thể cho phép đo quan hệ, nên một chương trình từng qua
**nhờ** bí danh ấy nay bị bác. Một envelope đã cache có thể đang phục vụ thứ hệ
hiện tại sẽ từ chối. Đó là lý do bump đúng nghĩa.

### V3 giữ nguyên

```
V3_POOL_HASH · V3_CASE_SET_HASH · V3_SEED · 4 artifact gốc   byte-identical
V3_REEXECUTED = NO
```

## 10. Gates

| | |
|---|---|
| `tests/geometry/test_curved_distance_witness.py` (MỚI) | **18 passed** |
| obligation-binding contract · curved foundation · obligation surface · post-model alignment | passed (trong full suite) |
| full backend pytest | **3671 passed** · 1 skipped · 1 deselected, exit 0 (cây sạch) |
| cache identity | passed |
| `replay_demo_cases.py` | **5/5** · reduced-chain 1/1 |
| `audit_demo_crash_surface.py` | biên **6/6** · ném ra ngoài **0** |
| `certify_acceptance_runner.py` | exit **0** · 4 nhãn PASS · 2 readiness YES |
| candidate verification | exit **0** |
| `git diff --check` | exit **0** |

Frontend **không chạy**: không file frontend nào đổi.

## 11. Giới hạn

**① Wave này về TÍNH ĐÚNG và KHẢ NĂNG KIỂM CHỨNG của witness.** Mọi tuyên bố về
khả năng AI **tự tổng hợp** tiếp tục ở trạng thái `NOT_MEASURED`.

**② Attachment dùng bao đóng phụ thuộc, không dùng vai trò dựng.** `{T, A} ⊆
{H, T, A}` chứng minh chúng *tham gia dựng* khối, không chứng minh `T` là
**đỉnh** và `A` là **điểm vành**. Với `c7a` điều đó đủ — khoảng cách đỉnh↔vành
đúng là đường sinh — nhưng một đề hỏi *"khoảng cách từ tâm đáy tới vành"*
(= bán kính) cũng sẽ qua cổng này. Checker vẫn tính lại nên **số không sai**;
thứ chưa chặt là *"witness này đúng là đại lượng đề hỏi"*. Hợp đồng vai trò
dựng là một wave riêng.

**③ `angle` trên `vector3` vẫn là verification gap đang mở** — nay nó là fixture
chuẩn cho hình dạng ấy.

**④ Chưa có lượt live nào chạy qua đường mới.** Chứng minh bằng fixture tất
định và replay; chưa được kiểm bởi một phép đo thật.

## 12. RECOMMENDED_NEXT_ACTION

```
CURVED_SECTION_RADIUS_COVERAGE
```

`radius` của một `circle3` sinh từ `intersect_plane_curved` — khoảng trống hệ
đã khai trong `contract.py` và là nguyên nhân của hai ca `SYSTEM_COVERAGE_
FAILURE` (`c5b`, `c9b`) trong lượt V3.
