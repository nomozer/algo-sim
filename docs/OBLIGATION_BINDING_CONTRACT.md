# OBLIGATION BINDING CONTRACT

> `BALL_CENTER_RADIUS_EXPRESSIVENESS_DESIGN`, 2026-09-04.
> **`APPLICATION_LLM_CALLS = 0`** — wave thiết kế + triển khai tất định.
> Không mở năng lực toán học: mặt cầu ngoại tiếp vốn đã diễn đạt được bằng IR
> hiện có, và `SMALL_DEVELOPMENT_PROBE` đã chứng minh bằng replay.

## ROOT_CAUSE

Ba tầng trả lời khác nhau cho **cùng một câu hỏi** — *"chương trình này có
những vật nào, kiểu gì?"*:

| tầng | nguồn | thấy vật dựng bằng `construct_*`? |
|---|---|---|
| runtime (`interpreter`) | `memory[target_var] = …` | **có** |
| kiểm tĩnh (`kiem_tinh`) | `co[target] = _KIEU_DUNG[k]` | **có** |
| cổng phủ (`coverage_gate`) | `memory_declarations` | **KHÔNG** |

Cổng phủ đọc bảng khai báo rồi coi đó là toàn bộ chương trình. Vật dựng ra mà
mô hình không khai là **vô hình** với nó — dù runtime dựng xong và tính đúng.

Cùng module còn hai bảng **liệt kê tay** đã trôi khỏi thẩm quyền `_KIEU_DUNG`:
`_producers` (*ai tạo ra tên này*) và `_phu_thuoc` (*tạo ra từ cái gì*). Cả hai
liệt kê sáu `construct_*` và **bỏ sót `construct_curved_solid`**, thêm
2026-09-03. Hệ quả: witness dựng từ khối cong bị kết luận *"không có producer"*
hoặc *"khai đáp án chứ không tính nó"*. Đo bằng máy, không suy luận:

```
THẨM QUYỀN _KIEU_DUNG   7 kind
_producers  BỎ SÓT      ['construct_curved_solid']
_phu_thuoc  BỎ SÓT      ['construct_curved_solid']
```

Trớ trêu: `_doc` nằm ngay dưới `_producers` đã ghi đúng bài học đó — *"bảng
liệt kê tay sẽ lặng lẽ bỏ sót lớp mới"* — chỉ chưa được áp cho hàng xóm.

Lỗ thứ ba, khác loại: **không luật nào nối `obligation.container` với vật thật
sự mang số đo** khi vật ấy là vật **dẫn xuất** mà đề không đặt tên. `analyze`
buộc phải mượn tên: đề hỏi *"bán kính mặt cầu ngoại tiếp tứ diện OABC"*, mặt
cầu không có tên trong đề, nên `container = "OABC"` — tên đã thuộc về tứ diện.

## AUTHORITY_OWNER

| câu hỏi | chủ sở hữu | trước | sau |
|---|---|---|---|
| câu lệnh nào sinh ra vật gì | `ir_static_check._KIEU_DUNG` | có | **không đổi** |
| toán hạng TÊN của câu lệnh | `ir_static_check._TOAN_HANG_LENH` | có | **không đổi** |
| toán hạng TÊN của biểu thức | `validator._BIEU_THUC_HINH_HOC` | có | **không đổi** |
| nghĩa vụ nhận kiểu chủ thể nào | `measure_contract.BANG_PHEP_DO` | có | **không đổi** |
| **chương trình CÓ vật nào** | *không ai* — ba bản chép | — | `ir_static_check.bang_ky_hieu` |
| **nghĩa vụ nói về vật nào** | ba lưới tên ở `domain_profile` | chỉ theo tên | + net ⓪ theo **witness** |

Không bảng thứ hai nào được dựng. `bang_ky_hieu` là **tổng quát hoá của
`_kieu_khai`**, đặt cạnh nó, trong đúng module đã sở hữu `_KIEU_DUNG`.

## CONTRACT_BEFORE → CONTRACT_AFTER

**Trước.** Ngầm, không khai ở đâu, và mô hình không có cách nào biết:

1. mọi vật muốn cổng phủ nhìn thấy phải nằm trong `memory_declarations`;
2. vật mang số đo phải **trùng tên** `obligation.container`.

Cả hai **không có trong thẻ văn phạm lẫn skill prompt** (đã grep). Một đòi hỏi
không khai với mô hình mà vẫn bác chương trình là lỗi hợp đồng.

**Sau.** Cả hai biến mất khỏi nghĩa vụ của mô hình:

1. **Khai báo suy dẫn được thì hệ tự suy.** Kiểu của vật dựng ra đọc từ
   `_KIEU_DUNG`; xuất xứ nằm ở chính câu lệnh dựng, không ở dòng khai báo — nên
   suy dẫn **không mất provenance**. Khai báo tường minh vẫn THẮNG khi trùng
   tên. Mô hình không phải viết boilerplate cho thứ máy tự biết.
2. **Nghĩa vụ nối với vật qua WITNESS của chính nó** (net ⓪):

```
obligation.container  ──┐
                        ├─ nối được ⟺ cùng trỏ một vật
obligation.witness ─── program: witness = measure(quantity, of = S)
                        └─ S phải ĐÚNG KIỂU nghĩa vụ nhận
```

Bốn danh tính được tách bạch, không cái nào suy ra cái kia bằng chính tả:
`target_var` (tên ngữ nghĩa mô hình đặt) · `obligation.container` (tên hợp đồng
mượn từ đề) · `label` (nhãn hiển thị, **không** tham gia nối) · id máy (không
tồn tại trong IR — không có gì để cắt chuỗi).

### Net ⓪ hẹp đến đâu, và vì sao

| điều kiện | vì sao |
|---|---|
| chỉ chạy khi cổng **sẽ bác** | không chương trình nào đang qua bị đổi phán quyết |
| `container` phải **có mặt** trong chương trình, **sai kiểu** | tên vắng mặt = chương trình chưa dựng thứ đề gọi tên. Nới ở đây là nhận một chương trình dựng hình chóp cho đề hỏi lăng trụ |
| lượng đo phải khớp `ob.kind` | đo `volume` không nối được cho nghĩa vụ `radius` |
| chủ thể phải đúng kiểu | `cylinder_2` đo `radius` trên `section` ⇒ **không nối**, vẫn bác |
| nhiều chủ thể ⇒ `RANG_BUOC_MO_HO` | fail closed, hệ không chọn hộ |

Điều kiện thứ hai là kết quả của một lần **sửa sai giữa wave**: bản đầu chỉ đòi
"witness đo đúng lượng đo trên vật đúng kiểu", và nó làm đỏ hai test cũ đang
canh đúng chỗ (`test_C1a_khong_bo_qua_khi_hop_dong_thieu_truong`). Hai test ấy
đúng, bản vá sai — đã thu hẹp.

### Nửa còn lại: C₂ phải dùng lại ánh xạ của C₁a

Nối ở cổng phủ chưa đủ. `check_postconditions` gán **bí danh** cho tên hợp đồng
chỉ khi `ten_hd not in snap`, mà `OABC` **có** trong snapshot (tứ diện) — nên
`check_radius` nhận tứ diện và báo *"cần một `circle3` hoặc một
`curved_solid`"*, vu oan một chương trình đã tính đúng `R = √3`.

C₁a đã học đúng bài này ngày 2026-08-29 (*"hoà giải CŨNG phải chạy khi tên CÓ
mà sai kiểu"*); C₂ thì chưa. Nay C₂ **buộc lại từng nghĩa vụ**
(`ob.model_copy(update={"container": …})`) thay vì ghi đè `snap` — `snap` dùng
chung, ghi đè `OABC` sẽ phá một nghĩa vụ khác nói đúng về tứ diện.

## ERROR_CONTRACT

`CoverageResult.chan_doan` → `SemanticRouteOutcome.chan_doan_nghia_vu`, dạng cấu
trúc, song song với `details` (văn xuôi cho người đọc). Bốn mã, bốn cách chữa:

| mã | nghĩa | tầng sửa phải làm gì |
|---|---|---|
| `THIEU_KHAI_BAO` | vật hợp đồng gọi tên không có trong chương trình | dựng nó |
| `KIEU_KHONG_HOP` | vật CÓ, kiểu nghĩa vụ không nhận | dựng đúng loại (`kieu_chap_nhan` nêu sẵn) |
| `RANG_BUOC_THIEU` | không nối được nghĩa vụ với vật nào | kiểm witness |
| `RANG_BUOC_MO_HO` | nối được **nhiều** vật | phân định — `ung_vien` liệt kê |

Mỗi mục mang `nghia_vu · container · witness · kieu_container · kieu_chap_nhan
· ung_vien`. **Không phân loại bằng chuỗi tiếng Việt** — chính lỗi mà `sua_duoc`
đã phải bỏ, vì đổi một chữ là đổi con số.

`error_code` giữ nguyên `REQUESTED_OPERATION_UNCOVERED`: đúc thêm mã mới sẽ lan
sang `phan_loai`, luật repair-eligible và `SEMANTIC_FAILURE_CATEGORY` — vượt
phạm vi wave, mà `ly_do` đã đủ phân biệt.

## IDENTITY / CACHE — đo, không đoán

| | |
|---|---|
| `MODEL_FACING_CONTRACT_CHANGED` | **NO** — `grammar_card` `e0790ba8…` không đổi |
| `MODEL_FACING_PROMPT_CHANGED` | **NO** — `prompts` `55ac1ca6…` không đổi |
| `IR_SCHEMA_CHANGED` | **NO** — `synthesis_schema` `8e47707d…`, `analyze_schema` `a4d5ed7c…` không đổi |
| `CAPABILITY_HASH_CHANGED` | **NO** — `5b61b9ea…` không đổi |
| `CHECKER_RUNTIME_BEHAVIOR_CHANGED` | **YES** — checker không sửa, nhưng C₂ trao cho nó **chủ thể khác** khi C₁a đã hoà giải |
| `CACHE_VERSION_REQUIRED` | **YES — 74 → 75** |

`semantic_environment_hash` **giữ nguyên** `e6161b15…`; `test_cache_identity`
tự xác nhận *"thành phần đổi: (không — chỉ version lệch)"*. Đây là bằng chứng
độc lập rằng bề mặt mô hình đứng yên.

Bump vì tiêu chí của chính cổng, không vì thói quen — cùng loại **69/71/72**
(hợp đồng đứng yên, **phán quyết sản phẩm đổi**), khác loại 70/73/74 (bề mặt mô
hình đổi). Envelope đã cache cho một đề hỏi số đo của vật dẫn xuất mang
`servable=False` + `requested_operation_uncovered`, trong khi hệ nay chạy tới
`served`. Trả lại nó là phát mãi một lời từ chối hệ không còn đưa ra.

Năm cổng bump, không phải ba: `main.py` · `test_api.py` · `CURRENT_STATE.md` ·
`test_evaluation_candidate.py` · **`cache_identity.lock.json`**
(`scripts/lock_cache_identity.py` — CLAUDE.md §3 còn ghi "ba chỗ", nay là năm).

## ACCEPTANCE

```
NEW_AUTHORITIES          = 1  (ir_static_check.bang_ky_hieu — tổng quát hoá _kieu_khai)
NEW_IR_OPERATIONS        = 0
NEW_CURVED_TEMPLATES     = 0
NEW_FAMILY_SPECIAL_CASES = 0
MODEL_FACING_CONTRACT_CHANGED   = NO
PROMPT_CHANGED                  = NO
CAPABILITY_HASH_CHANGED         = NO
CHECKER_RUNTIME_BEHAVIOR_CHANGED= YES (chủ thể được trao, không phải checker)
CACHE_VERSION                   = 74 → 75
HISTORICAL_ARTIFACTS_CHANGED    = NO
CIRCUMSPHERE_REPLAY             = PASS  (nguyên văn → served, R = √3)
R0                              = PASS
REGRESSION                      = PASS
APPLICATION_LLM_CALLS           = 0
```

Ba symbol mới, mỗi cái một lý do sở hữu và một test khoá:

| symbol | vì sao không có chủ cũ | test khoá |
|---|---|---|
| `ir_static_check.bang_ky_hieu` | `_kieu_khai` trả lời *"khai gì"*; sửa tại chỗ sẽ xoá phân biệt "có kiểu ≠ có giá trị" mà `kiem_tinh` dựa vào | `test_A4` |
| `coverage_gate._do_theo_witness` | không ai lập bản đồ `witness → phép đo`; `_producers` chỉ biết *ai tạo ra* | `test_A1`, `test_A3` |
| `coverage_gate.ChanDoanNghiaVu` + 4 mã | chỉ có `missing: list[str]` — văn xuôi, phân loại phải khớp chuỗi | `test_B1`–`test_B5` |

## KIỂM CHỨNG

`tests/geometry/test_obligation_binding_contract.py` — 14 test, fixture là
artifact **thật** (`probe-contract-waves-2` / `probe-contract-waves`), không
phải chương trình viết lại cho vừa.

- **A1** tiêm lại trạng thái trước bản vá (bỏ net ⓪) ⇒ lượt bác cũ trở lại,
  `details` khớp **y hệt chuỗi artifact đã ghi**. Guard chưa từng đỏ là guard
  chưa được chứng minh.
- **A2** chương trình **nguyên văn** của mô hình → `served`, `R = √3`.
- **B2** `cylinder_2` vẫn bị bác, `KIEU_KHONG_HOP` — net ⓪ không phải cửa sau.
- **B3** hai chủ thể hợp lệ ⇒ fail closed.
- **C2** hình **trụ** đi đúng đường (`intersect_plane_curved`) → `served`,
  `r = 5`, và **không lưới nào phải ra tay** — chứng minh từ vựng khối cong đủ,
  và bản vá không ưu ái hình cầu.
- **C3** quét mã: cấm nhánh so sánh `curved_kind` với một loại cụ thể ở cả hai cổng.
- **D1** điểm có toạ độ mà thiếu xuất xứ **vẫn chết ở grounding** — R0 không nới.
- **D2** 42 chương trình lịch sử vẫn parse. (Quét theo khoá `chuong_trinh` /
  `semantic_program`, **không** theo hình dạng: artifact cố ý giữ cả ứng viên
  thô HỎNG lược đồ, nên "mọi dict trông giống chương trình" là tiền đề sai.)

## KHÔNG LÀM (giữ nguyên phạm vi)

`BALL_2` dựng điểm từ tâm + bán kính · khối cong mới · sửa prompt · đổi tên
toán hạng · `extra="forbid"` · `DOMAIN_ROOT_TIGHTENING` · V3 · lượt gọi provider.

## NỢ MỞ, KHÔNG TỰ Ý ĐÓNG

- **`analyze` mượn tên vật dẫn xuất.** Net ⓪ vá được ở tầng cổng, nhưng nguồn
  vẫn là `analyze` phát `radius(OABC)` cho một đại lượng thuộc mặt cầu. Sửa tại
  nguồn = đổi **hợp đồng gửi cho mô hình** (`analyze_schema` cho phép nghĩa vụ
  trỏ vật dẫn xuất) ⇒ blast radius: lược đồ analyze, prompt analyze, cache, mọi
  artifact so sánh. **Đề xuất wave riêng**, không gộp vào đây.
- **`ten_da_hoa_giai` phẳng** — hai nghĩa vụ ánh xạ cùng một tên hợp đồng sang
  hai vật thì cái sau đè cái trước. Có sẵn từ trước wave này; chưa gặp ca thật.
- Thông điệp `missing` vẫn nói *"kiểu X không hợp"* cho ca thiếu khai báo. Nay
  đã có `chan_doan` cấu trúc bên cạnh; hợp nhất văn xuôi là việc của wave sau.
