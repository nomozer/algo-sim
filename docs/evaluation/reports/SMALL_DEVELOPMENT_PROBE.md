# SMALL DEVELOPMENT PROBE — hai ca, đo tác động ba wave hợp đồng

> **DỮ LIỆU PHÁT TRIỂN.** Không phải nghiệm thu. Không bật năng lực sản phẩm.
> `BALL_PRODUCT_ENABLED` · `CYLINDER_PRODUCT_ENABLED` · `CONE_PRODUCT_ENABLED`
> = **NO**, không đổi. **V3 = NOT RUN · pool sealed · seed undrawn.**

Đo tác động sống của ba wave đã đóng — `CARD_CATEGORY_AFFORDANCE`,
`REPAIR_FRAGMENT_COMPLETENESS`, `OPERAND_ROLE_HINTS` — lên đúng hai ca phát
triển: `cylinder_2` và `circumsphere`.

## 0. Danh tính lượt đo

| | |
|---|---|
| run_id ① | `probe-contract-waves` — `cylinder_2` |
| run_id ② | `probe-contract-waves-2` — `circumsphere` |
| HEAD ① / ② | `45f5baa` / `763f237`, cây SẠCH cả hai lượt |
| `CACHE_VERSION` | 74 (không bump — không có gì hướng-mô-hình đổi) |
| `stable_capability_hash` | `5b61b9ea76d0c764…` |
| `semantic_environment_hash` | `e6161b15ccef73ce…` |
| candidate | `345eabfda7a0d507…` (89 file) — **không đổi suốt wave** |
| `APPLICATION_LLM_CALLS` | **6** (① 2 · ② 4) |
| `SYSTEM_FAILURES` (sau đính chính §3) | ① 0 · ② 1 |
| `RAW_CANDIDATE_PERSISTED` | **YES** — 1 + 3 ứng viên thô, đủ mọi lượt |

Sửa mã trong wave này **chỉ chạm `backend/scripts/` và `backend/tests/`** — bộ
đo, ngoài `MEASURED_SYSTEM_PATHS`. Candidate xác nhận nguyên vẹn sau cùng.

## 1. Câu trả lời trực tiếp

### `CYLINDER_2_CATEGORY_ERROR_AFTER = 0`

Lỗi mà `CARD_CATEGORY_AFFORDANCE` nhắm tới **không tái diễn**.

| | trước (`curved-ergonomics-v2-run2`) | sau (lượt này) |
|---|---|---|
| one-shot | `construct_plane.through` — số ở ô danh sách | **schema hợp lệ** |
| repair-01 | `Input tag 'intersect_plane_curved' … expected 'assign'` | *không cần sửa* |
| `stage_reached` | `khong_toi_route` | `structural_coverage` |
| phân lớp | `MODEL_SCHEMA_FAILURE` | qua schema + grounding |

Mô hình đặt đúng `plane_perpendicular_to_line` và `measure` **bên trong**
`assign`, đúng như nhãn `[BIỂU THỨC→assign]` trên thẻ dạy. `SCHEMA_MISUSE = 0`
ở cả hai ca.

### `CIRCUMSPHERE_RAW_OPERANDS` — đọc từ RAW, không suy từ lỗi Pydantic

3 ứng viên thô, **60 ô toán hạng** được điền qua 4 lượt sinh. Tên ô mô hình gõ:

```
construct_curved_solid  curved_kind · anchor · rim_point      (cầu: bỏ apex_or_top — ĐÚNG)
midpoint                a · b
translate               point · vector
vector_from_points      from_point · to_point
measure                 quantity · of                          (bỏ wrt — ĐÚNG, radius không có wrt)
construct_polygon       vertices
construct_solid         vertices · faces
declare_point           at · source_fact_id · model_assumption
```

Không một ô nào sai tên, rỗng, hay thiếu.

### CHIA BỐN

| | |
|---|---|
| `MODEL_TYPED_WRONG_KEYS` | **0** |
| `MODEL_TYPED_NULL` | **0** |
| `MODEL_OMITTED_FIELDS` | **0** |
| `MODEL_USED_CORRECT_NAMES_BUT_OTHER_FAILURE` | **2 / 2** |

**Danh xưng toán hạng hết là nút thắt.** `OPERAND_ROLE_HINTS` giữ được lời hứa:
mô hình gán `anchor = M` (tâm mặt cầu) và `rim_point = O` (điểm trên mặt cầu)
đúng vai, không đảo — đúng thứ vai trò in trên thẻ nói. Cả hai ca chết vì lý do
**sau** chuyện tên gọi.

## 2. Vì sao mỗi ca chết — hai nguyên nhân NGƯỢC NHAU, cùng một mã lỗi

Cả hai dừng ở `structural_coverage` với `REQUESTED_OPERATION_UNCOVERED`. Giống
nhau đến đó là hết.

### `cylinder_2` — mô hình soạn sai thật

```
construct_section  target_var=C  solid=cylinder<curved_solid>  plane=cutting_plane
assign             R  <- measure(radius, of=C<section>)
```

Thẻ gửi cho mô hình ghi rõ **cả hai ô**:

```
[LỆNH]            construct_section: … solid:tên<solid>[khối] …
[BIỂU THỨC→assign] intersect_plane_curved: solid:tên<curved_solid>[khối cong] …
                  radius(of:tên<circle3|curved_solid>) — không có wrt
```

Đường đúng — `intersect_plane_curved` → `circle3` → `radius` — **có sẵn trên
thẻ**, và chính mô hình đã với tới nó ở lượt đo trước (sai *phạm trù*, đúng
*phép*). Lần này nó bỏ phép đúng để lấy `construct_section`, một phép thẻ khai
là chỉ nhận `solid`. Cổng phủ phán **ĐÚNG**.

> ⚠️ Quan sát n = 1, không phải nhân quả: nhãn phạm trù chữa xong lỗi phạm trù,
> nhưng lượt này mô hình đổi sang một lựa chọn sai kiểu khác. Một mẫu không đủ
> để nói thẻ đẩy nó sang đó.

### `circumsphere` — chương trình ĐÚNG, hợp đồng chặn

Lượt 3 (sau 2 lần sửa grounding) mô hình viết:

```
M            <- midpoint(O, D)                 D = đỉnh đối của hộp, dựng bằng translate
circumsphere <- construct_curved_solid(ball, anchor=M, rim_point=O)
R            <- measure(radius, of=circumsphere<curved_solid>)
```

Đúng lượng đo · đúng witness hợp đồng đòi (`R`) · đúng kiểu chủ thể. Cổng vẫn
bác: `radius(OABC): kiểu 'solid' không hợp với nghĩa vụ này` — vì `container`
của nghĩa vụ là `OABC`, tứ diện.

**Chạy lại tất định, 0 lượt gọi model,** chính chương trình ấy qua bốn biến thể:

| | biến thể | kết quả |
|---|---|---|
| ① | nguyên văn | `structural_coverage` · `requested_operation_uncovered` |
| ② | + khai đủ mọi vật dựng ra | `structural_coverage` · y hệt |
| ③ | + đổi tên quả cầu thành `OABC` | `structural_coverage` · `container chưa khai báo` |
| ④ | **khai đủ + đổi tên** | **`served` · `R = √3`** ✅ |

Đáp số mong đợi là `√3`. **Hệ làm được bài này.** Hai thứ chặn nó, và **không
thứ nào có trong thẻ văn phạm lẫn skill prompt** (đã grep cả hai):

1. mọi vật dựng ra phải có mặt trong `memory_declarations` — cổng phủ đọc
   **chỉ** `spec.memory_declarations`, nên vật đã dựng mà chưa khai là vô hình
   với nó;
2. vật mang số đo phải **trùng tên** `container` của nghĩa vụ.

Cần **cả hai**: ② một mình không đủ, ③ một mình không đủ. Và thông điệp sửa gửi
ngược không nêu cái nào — nó nói *"kiểu 'solid' không hợp"*, nên vòng sửa không
có đường hội tụ. Đó là lý do 2 lượt sửa không cứu được ca này.

Một đòi hỏi không khai với mô hình mà vẫn bác chương trình là **lỗi hợp đồng**,
tức lỗi HỆ theo bất biến §14.

### Từ vựng KHÔNG thiếu — câu hỏi `BALL_CENTER_RADIUS_EXPRESSIVENESS` đã có đáp

Mặt cầu ngoại tiếp diễn đạt được trọn vẹn bằng từ vựng hiện có, không cần thêm
`kind` nào: `midpoint` → `construct_line` → `plane_perpendicular_to_line` (mặt
trung trực) → `intersect_plane_plane` → `intersect_line_plane` (tâm) →
`construct_curved_solid` → `measure radius`. Biến thể ④ **chứng minh bằng máy**
rằng tuyến chạy tới `served`.

## 3. ĐÍNH CHÍNH — bộ đo xếp sai CẢ HAI ca, mỗi cái một chiều

`phan_loai` ánh xạ thẳng `REQUESTED_OPERATION_UNCOVERED → SYSTEM_COVERAGE_FAILURE`,
vì sự cố sinh ra nhánh ấy (`CURVED_MODEL_ACCEPTANCE_V1`) đúng là lỗi hệ.

| ca | nhãn lượt chạy ghi | nhãn ĐÚNG |
|---|---|---|
| `cylinder_2` | `SYSTEM_COVERAGE_FAILURE` | `MODEL_COMPOSITION_FAILURE` |
| `circumsphere` | `MODEL_COMPOSITION_FAILURE` | `SYSTEM_COVERAGE_FAILURE` |

Đây là **cùng một bệnh** đã đính chính một lần cho `LEARNER_SURFACE_INCOMPLETE`:
đọc **mã lỗi** thay vì đọc câu §14 thật sự hỏi — *chương trình có hợp lệ theo
hợp đồng gửi cho mô hình không?* Giá phải trả lần này đo được: luật
DỪNG-KHI-LỖI-HỆ nổ nhầm ở `cylinder_2` và giết lượt đo **trước** ca thứ hai,
buộc phải mở run_id ② để chạy nốt.

Đã sửa ở `763f237` + `1b2479a`, bằng cách hỏi hai thẩm quyền thay vì đoán:

- `_cong_phu_hep_hon_bo_kiem()` — cổng phủ có hẹp hơn thứ bộ kiểm chứng thực
  được không (bắt lại đúng vết V1). Cây hiện tại: rỗng.
- `nghia_vu_du_noi_dung_hut_ten(contract, spec)` — witness của nghĩa vụ có được
  sinh bởi **đúng lượng đo** trên một chủ thể **đúng kiểu** không.

Runner ghi kết quả hàm thứ hai vào artifact **kể cả khi rỗng** — rỗng chính là
thứ chứng minh `cylinder_2` sai thật chứ không bị oan. Ba test khoá hai chiều,
kèm một lượt **tiêm lệch bảng** (`volume:curved_solid`) để chứng minh nhãn lật
lại được: `test_F2b1` · `test_F2b2` · `test_F2c`.

**Artifact hai lượt giữ nguyên nhãn cũ** — bằng chứng lịch sử không viết lại;
đính chính sống ở bảng trên.

## 4. Nợ còn mở, phát hiện trong wave này

- **`OBLIGATION_BINDING_CONTRACT`** (mới, chặn `circumsphere` và mọi bài hỏi số
  đo của một vật **đề không đặt tên**: mặt cầu ngoại tiếp, đường tròn thiết
  diện, trọng tâm…). Hai luật ràng buộc tên chưa hề khai với mô hình. Ba hướng,
  chưa chọn: khai luật vào thẻ · cho `analyze` phát nghĩa vụ trỏ **vật dẫn
  xuất** thay vì vật đề nêu tên · nới cổng phủ chấp nhận witness đã đo đúng
  kiểu bất kể tên container.
- **Thông điệp cổng phủ không nêu được luật đã vi phạm** — nói *"kiểu X không
  hợp"* trong khi bệnh thật là thiếu khai báo hoặc lệch tên. Vòng sửa vì thế
  không hội tụ.
- Từ trước, chưa động: `STRICT_OPERAND_DIAGNOSTIC` · `DOMAIN_ROOT_TIGHTENING` ·
  khoảng trống kiểm chứng `angle`/`vector3`.

## 5. NEXT_ACTION

**`BALL_CENTER_RADIUS_EXPRESSIVENESS_DESIGN`** — chọn một, và **định lại phạm
vi**, vì lượt đo đã trả lời phần "expressiveness" của nó:

- từ vựng dựng hình **không thiếu gì** (chứng minh ở §2, biến thể ④ → `served`,
  `R = √3`);
- phần còn sống dưới nhãn này là **hợp đồng buộc tên** giữa nghĩa vụ và vật
  dựng — tức `OBLIGATION_BINDING_CONTRACT` ở §4.

Hai lựa chọn kia bị loại bằng số đo, không bằng cảm tính:

- **`STRICT_OPERAND_DIAGNOSTIC_AUDIT`** — chia bốn cho `0 / 0 / 0 / 2`. Không
  còn tín hiệu ở tầng tên toán hạng để mà soát.
- **`PREPARE_V3`** — có **một lỗi hệ đang mở** (§2, `circumsphere`). Chạy V3 lúc
  này lặp đúng sự cố mà cả tuyến probe sinh ra để chặn: tiêu quota niêm phong
  để đo lại một khiếm khuyết hợp đồng đã biết. Pool V3 vẫn niêm phong,
  seed chưa rút.
