# VERIFICATION_CAPABILITY_IDENTITY — vân tay năng lực thấy được thứ bộ kiểm chứng thực

> Thực hiện **2026-09-03**, trên HEAD `9316239`, cây sạch lúc bắt đầu.
> **APPLICATION_LLM_CALLS = 0.** Không đổi hành vi checker, không đổi bề mặt mô
> hình, không băm mã nguồn. `SEALED_RESEARCH_BASELINE = a075e9f5…` **không đụng**
> (nó chỉ tồn tại dưới dạng số đã ghi trong `docs/`, không nằm trong mã).

## 0. Kết luận trước

```
VERIFICATION_SEMANTICS_IN_CAPABILITY_IDENTITY = YES
OLD_VOLUME_CHECKER_VS_CURRENT_HASH_DIFFERENT  = YES
RADIUS_VERIFICATION_CHANGE_HASHES             = YES
SOURCE_TEXT_HASHING                           = NO
MEASURE_SUBJECT_COMPATIBILITY_AUTHORITIES     = 1
VERIFICATION_CAPABILITY_AUTHORITIES           = 1
ANGLE_VECTOR3_EXCEPTION                       = STILL_EXPLICIT
CHECKER_RUNTIME_BEHAVIOR_CHANGED              = NO
MODEL_FACING_CONTRACT_CHANGED                 = NO
CACHE_VERSION                                 = 71 → 71 (KHÔNG bump — §6)
```

## 1. Nguyên nhân gốc

`capability_fingerprint()` có hai trường chạm tới bộ kiểm, và **không trường nào
hỏi đúng câu**:

| trường | câu nó trả lời | với `check_volume` cũ ↔ mới |
|---|---|---|
| `nghia_vu` | hệ có **tên** checker nào | cả hai đều có `"volume"` — giống nhau |
| `nghia_vu_chu_the` | **cổng phủ CHO PHÉP** kiểu nào | cả hai đều `{solid, curved_solid}`; nó dẫn từ `BANG_PHEP_DO`, vốn đã đúng từ `CURVED_OBLIGATION_COVERAGE_BRIDGE` |

Câu còn thiếu: ***bộ kiểm có với tới được không?*** Hệ quả đo được:

```
container A   check_volume BÁC `curved_solid`      →  ball_1 servable = False
container B   check_volume CHỨNG THỰC `curved_solid` →  ball_1 servable = True
                        CÙNG stable_capability_hash 024799b8…
```

Hai hệ nhận và **phục vụ** hai tập chương trình khác nhau; `runtime_doctor`
không phân biệt nổi. Đây là lỗ danh tính **thứ ba** cùng một họ:

1. `CURVED_OBLIGATION_COVERAGE_BRIDGE` — cổng phủ đổi phán quyết, băm đứng im
   → vá bằng `nghia_vu_chu_the`.
2. `RADIUS_VERIFICATION_BRIDGE` / `VOLUME_VERIFICATION_BRIDGE` — bộ kiểm đổi
   thứ nó chứng thực được, băm vẫn đứng im. **Đây là wave này.**

Mỗi lần vá đều đúng, và mỗi lần đều bịt **một tầng nông hơn** tầng tiếp theo.

## 2. Hợp đồng kiểm chứng tối thiểu (§4)

Thông tin đủ để mô tả năng lực chứng thực, và **không thừa một trường**:

```
kiểm chứng được(nv)  =  kieu_chu_the_nghia_vu(nv)  −  KHONG_KIEM_DUOC
                        └── BANG_PHEP_DO ──────┘     └── mới ───┘
```

**Viết dưới dạng HIỆU, không dưới dạng danh sách.** Một danh sách
`volume → [solid, curved_solid]` sẽ là **bản sao thứ hai** của bảng kiểu — và
bản sao chính là con bug cả ba wave vừa rồi đi dọn
(`MEASURE_SUBJECT_COMPATIBILITY_AUTHORITIES = 1` giữ nguyên). Ở đây chỉ khai
phần **trừ đi**, tức đúng phần thông tin chưa nằm ở đâu cả.

Những trường §4 nêu mà tôi **cố ý không đưa vào**, kèm lý do:

| ứng viên | vì sao không |
|---|---|
| trường giá trị mong đợi (`value` / `cos_sq`) | không dẫn xuất được — phải khai tay, tức bảng thứ hai. Và nó chưa từng là chỗ lệch nào đo được |
| miền so sánh chính xác | hằng số dùng chung mọi checker (`ExactNumber`); một trường không bao giờ đổi thì không phân biệt được gì |
| "chế độ kiểm chứng" | chỉ `section_matches` khác hình dạng, và nó không thuộc nhóm ĐO |

## 3. Sở hữu

| | |
|---|---|
| `VERIFICATION_CONTRACT_OWNER` | `geometry_obligations.KHONG_KIEM_DUOC` + `kieu_kiem_chung_duoc()` — **cạnh chính bảng đăng ký checker** |
| `VERIFICATION_CAPABILITY_COMPONENT` | `runtime_identity.capability_fingerprint()["kiem_chung_do"]` |
| `VERIFICATION_CAPABILITY_AUTHORITIES` | **1** |

⚠️ **Bảng ngoại lệ đã DỜI từ file test sang mã sản phẩm.** Trước wave này nó là
`NGOAI_LE` trong `test_measure_checker_subject_drift.py`. Chừng nào nó còn ở đó
thì **vân tay năng lực của sản phẩm phụ thuộc một file test** — bộ đo không được
làm thẩm quyền của thứ nó đo (§10). Test giữ đúng vai: `NGOAI_LE` nay chỉ là bí
danh nhập từ mã sản phẩm, và test **chứng minh** lời khai ấy trung thực.

### Phạm vi có chủ đích

`kiem_chung_do` chỉ phủ **nghĩa vụ ĐO có checker** — `distance`, `angle`,
`volume`, `radius`. Đó đúng là tập mà `test_measure_checker_subject_drift`
chứng minh được, và là tập có **tầng so-giá-trị** để một chỗ lệch nấp trong đó.

Khai rộng hơn tập đã đo là tuyên bố một thứ chưa đo — đúng cái nết đã đẻ ra cả
ba lỗ trên. Ranh giới còn lại được ghi ở §7.

## 4. Vòng khoá: lời khai phải khớp thực đo

Một vân tay dựng trên **lời hứa** còn tệ hơn không có vân tay, vì nó trông như
bằng chứng. Nên:

```
mã sản phẩm KHAI   kieu_kiem_chung_duoc(nv)
bộ đo ĐO           thả nhân chứng CỐ TÌNH SAI, đòi đúng lời "giá trị không khớp"
test               khai == đo, cho MỌI nghĩa vụ ĐO
```

`test_loi_KHAI_nang_luc_kiem_chung_khop_thuc_te_DO_DUOC`. Tiêu chí "kiểm chứng
được" là *checker phải nói được câu **"giá trị không khớp"*** — chỉ khi đã tính
lại đại lượng từ hình thì nó mới nói được câu ấy; từ chối kiểu, hay ném vì không
tính nổi, đều không phải câu đó.

## 5. Phép tiêm (§14) — `tests/test_verification_capability_identity.py` (13)

| | phép thử | kết quả |
|---|---|---|
| I1 | hợp đồng kiểm chứng CŨ (`volume` chỉ chứng thực `Polyhedron`) | băm **KHÁC** · `kiem_chung_do.volume` `["curved_solid","solid"]` → `["solid"]` |
| I2 | bỏ `curved_solid` khỏi kiểm chứng `radius` | băm **KHÁC** |
| I3 | nới hợp đồng `distance` sang kiểu bộ kiểm không với tới | băm **KHÁC**; `nghia_vu_chu_the` rộng ra, `kiem_chung_do` thì không — **hai trường phản ứng khác nhau**, và đó là toàn bộ lý do phải có cả hai |
| I3b | thu hẹp kiểm chứng `distance` (bỏ `plane3`) | băm **KHÁC** |
| I4 | đổi TÊN nghĩa vụ (`volume` → `the_tich`) | băm **KHÁC** — chính sách tường minh: tên nghĩa vụ **là** ngữ nghĩa (từ vựng `analyze` phát ra, khoá `CHECKERS` tra) |
| I5 | chú thích / định dạng | **KHÔNG** được là cơ chế đổi băm — khoá hai vế: không đường nào của `capability_fingerprint` chạm `getsource`/`read_text`/`__file__`, và băm là hàm THUẦN của các bảng |
| I6 | ngoại lệ `angle`/`vector3` | khai **trung thực**: `nghia_vu_chu_the.angle` có `vector3`, `kiem_chung_do.angle` = `["line3","plane3"]` |
| I7 | gỡ HẾT mũi tiêm | băm về **đúng** bản gốc (không phải "một giá trị mới nào đó") |

⚠️ **I3 đã sai ở bản đầu và phải sửa.** Tôi vá `BANG_PHEP_DO` rồi khai luôn
ngoại lệ — hai mũi tiêm **triệt tiêu nhau đúng thứ nó định đo**, băm không nhúc
nhích, test đỏ. Nguyên nhân thật: `OBLIGATION_KINDS` là **ảnh chụp lúc import**
(`_nap_nghia_vu_do`), không phải khung nhìn sống trên `BANG_PHEP_DO`; ở sản phẩm
hai bảng luôn khớp vì cùng dựng lúc nạp module, trong một phép tiêm thì không.
Bản sửa vá cả hai bảng — và nhờ vậy I3 nay đo đúng thứ nó tuyên bố.

## 6. Cache (§11) — **KHÔNG bump**, và đây là lý do

Phân biệt mà chính đề bài nêu: *cơ chế danh tính đổi* ≠ *ngữ nghĩa phục vụ đổi*.

Cổng `test_cache_identity` tự ghi đường xử lý, nguyên văn:

> · CÒN đúng ⇒ chỉ chạy lại `scripts/lock_cache_identity.py`.
> · KHÔNG còn ⇒ bump `CACHE_VERSION` … rồi mới chạy lại script.

Câu phải trả lời: **envelope đã cache có còn đúng dưới bản mới không?** — **CÒN.**
Wave này không đổi một dòng phán quyết nào: `CHECKER_RUNTIME_BEHAVIOR_CHANGED =
NO`, chứng minh bằng `test_CHECKER_RUNTIME_BEHAVIOR_CHANGED_bang_NO` (ba checker
chạy lại đúng như trước). Mọi envelope sinh dưới `CACHE_VERSION 71` trước commit
này **bằng đúng** thứ hệ sinh ra bây giờ. Bump là vô hiệu hoá cache mà không có
lấy một envelope sai để vô hiệu hoá.

Đối chiếu với bump 71 của wave trước (`VOLUME_VERIFICATION_BRIDGE`): ở đó
envelope cũ mang `servable=False` cho đề mà hệ mới phục vụ được — **có** envelope
sai, nên **có** bump. Hai wave, hai kết luận, cùng một tiêu chí.

Hệ quả phải làm: chạy lại `lock_cache_identity.py` để khoá ghi nhận cặp
(`CACHE_VERSION 71`, môi trường mới).

## 7. Danh tính đo được (§1, §12)

| | trước | sau |
|---|---|---|
| `prompts` | `55ac1ca6a6df92ce…` | **không đổi** |
| `grammar_card` | `2463652cd8d328ad…` | **không đổi** |
| `synthesis_schema` | `421e7aff8557dc17…` | **không đổi** |
| `analyze_schema` | `a4d5ed7c65a68007…` | **không đổi** |
| `stable_capability_hash` | `024799b84cf528db…` | **`5b61b9ea76d0c764…`** |
| `semantic_environment_hash` | `a4aa4d6eefa3e9a1…` | **`36be94cf2258e116…`** |
| `CACHE_VERSION` | `71` | `71` |
| candidate (mã sản phẩm) | `5debcf75ba49dd6e` 89 file | `1a9d94ff9ba8bb54` 90 file |

`MODEL_FACING_CONTRACT_CHANGED = NO` — bốn vân tay mô hình khớp byte-đối-byte.

⚠️ `SEMANTIC_ENV_HASH_CHANGED = YES`, và điều đó **đúng**: `capability` là một
thành phần của môi trường sinh. Nhưng phải đọc cho đúng — artifact live chạy
trước wave này ghi `a4aa4d6e…`, artifact chạy sau ghi `36be94cf…`, **trong khi
hành vi đo được y hệt nhau**. Đó không phải "hệ đã đổi"; đó là "cách hệ tự khai
danh tính đã đầy đủ hơn". Khi so hai artifact qua mốc này, so **bốn thành phần
mô hình** — chúng mới là thứ nói prompt/lược đồ có đổi không.

### Ranh giới còn lại, khai thẳng

`kiem_chung_do` **chưa** phủ:

- **6 checker vị từ** (`point_on_line`, `parallel`, `coplanar`, …). Chúng không
  có tầng so-giá-trị, và tiêu chí đo phải khác hẳn — bộ đo hiện tại cho tín hiệu
  nhiễu trên chúng. Khai chúng bây giờ là tuyên bố một thứ chưa đo.
- **Miền so sánh.** Bản vá π của wave trước (`parse_exact` đọc `288π`) đổi thật
  sự thứ hệ kiểm chứng được, và nó **sẽ không** làm đổi băm này. Đưa được nó vào
  đòi mô tả "văn phạm giá trị mong đợi" như một hợp đồng — chưa làm.

Trong lúc soát, cổng còn phát hiện một chỗ đáng ngờ **không thuộc phạm vi wave
này**: `OBLIGATION_KINDS["coplanar"]` cho phép `solid`, nhưng `check_coplanar`
bác nó với *"một KHỐI thì hiển nhiên không đồng phẳng — nghĩa vụ gắn sai chủ
thể"*. Đó có thể là hợp đồng rộng quá chứ không phải bộ kiểm hụt. Ghi lại, không
vá.

## 8. Hồi quy — cây sạch, 0 API call

| cổng | kết quả |
|---|---|
| pytest | **3121 pass**, 1 skip, 1 deselect |
| vitest | **687 pass / 50 file** |
| `tsc -b && vite build` | PASS |
| `replay_demo_cases.py` | **DEMO_REPLAY 5/5** · **REDUCED_CHAIN 1/1** |
| `audit_demo_crash_surface.py` | **6/6 biên đúng kiểu**, ném ra ngoài **0** |
| `freeze_evaluation_candidate.py --verify` | PASS |
| `lock_cache_identity.py --verify` | PASS |

## 9. Việc kế tiếp

```
NEXT_ACTION = ACCEPTANCE_RUNNER_INTEGRITY
```

Nợ đã khai, cố ý chưa trả: `angle`/`vector3` (§5, I6) · vị từ và miền so sánh
chưa vào danh tính (§7) · `coplanar`/`solid` (§7).
