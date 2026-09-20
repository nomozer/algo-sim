# SECTION_PROVENANCE_NORMALIZATION

> Nhánh `feat/photo-problem-to-scene` · 2026-09-20.
> START_HEAD `863c912` · commit mã `569b4f5` · `main` giữ `085cae6` (không đổi).
> Bằng chứng: `docs/evaluation/geometry/photo-problem-to-scene/section-provenance-normalization/`.
> **0 request Gemini · 0 request mạng.**

```text
SECTION_PROVENANCE_NORMALIZATION = PASS
CANONICAL_SECTION_KIND           = section
SOURCE_PLANE_REQUIRED            = YES (giải được thành Plane3)
SOURCE_SOLID_REQUIRED            = YES (giải được thành Polyhedron)
CYCLE_VERIFICATION               = same_section_cycle(poly, cross_section(solid, plane))
ARBITRARY_POLYGON3_PROMOTED      = NO
ALIAS_PROVENANCE_PRESERVED       = YES (mọi độ sâu `assign`)
B02_SILENT_VISUAL_OMISSION       = False (trước: True)
VALID_CASE_BEHAVIOR_PARITY       = PASS (p1 · p3 · p4 · p5 + 4 ca âm)
VISUAL_GATE_BEHAVIOR_PARITY      = PASS (35/35, không sửa một dòng)
TRACE_VERSION                    = synthesis-repair-trace/2 (không đổi)
CACHE_VERSION                    = 96 → 97
CANDIDATE_HASH                   = 8159d5a7… → b42f17f4…  ·  cay_lam_viec_sach = TRUE
FAULT_INJECTIONS                 = 7/7 bắt · 7/7 hoàn nguyên trùng byte · 0 dấu tiêm
```

## 1. Bệnh: hai tầng trả lời khác nhau, và cả hai đều đúng

| tầng | công nhận thiết diện theo | mã |
|---|---|---|
| **nghĩa vụ** | **quan hệ semantic đã kiểm chứng** — dựng lại `cross_section(solid, plane)` rồi so chu trình | `OBLIGATION_KINDS['section_matches'] = {section, polygon3}` · `check_section_matches` nhận cả dãy `Vec3` |
| **cảnh + frontend** | **phép dựng** — lớp runtime của giá trị | `_than_hinh_hoc` · `scene3d-subentities.ts:226` (`type === "section"`) |

Một chương trình dựng đúng các đỉnh thiết diện bằng `construct_polygon`, kèm nghĩa
vụ `section_matches` **đã qua C₂**, vẫn ra cảnh là `polygon3`: frontend không vẽ
thiết diện, và cổng trực quan (863c912) từ chối đúng `VISUAL_OBJECT_TYPE_MISMATCH`.

Cả hai tầng đều đúng theo tiêu chí của nó. `OBLIGATION_KINDS` nhận `polygon3`
**cố ý** (chương trình sinh trước 2026-08-30 khai thiết diện là `polygon3`).
`_than_hinh_hoc` phân loại theo runtime cũng đúng — nó **không có `contract`** để
biết gì hơn.

## 2. Phát hiện của audit: chỉ có MỘT đường sinh ra `polygon3`-là-thiết-diện

`exec_construct_section` **luôn** trả `Section`; không nhánh nào trả dãy đỉnh trần.
Nên **không có** `polygon3` nào "sinh trực tiếp từ `construct_section`" để mà chuẩn
hoá. Đường duy nhất là `construct_polygon` + một nghĩa vụ `section_matches` trỏ vào
nó — tức bằng chứng plane–solid nằm ở **quan hệ semantic**, không ở phép dựng.

Hai hệ quả thiết kế rơi thẳng ra từ đó:

1. Luật chuẩn hoá **phải đọc `contract.obligations`**.
2. Vì `build_scene(spec, final_memory)` không nhận `contract`, chuẩn hoá phải là
   một **lượt sau** trên cảnh đã dựng — không phải sửa `build_scene`.

## 3. Luật

```
section_matches(container, params={solid, plane})
  → container giải được về một vật trong cảnh
  → params.solid  → Polyhedron trong bộ nhớ      (không ⇒ SOURCE_SOLID_UNRESOLVED)
  → params.plane  → Plane3 trong bộ nhớ          (không ⇒ SOURCE_PLANE_UNRESOLVED)
  → cross_section(solid, plane)                  (ném ⇒ SECTION_DEGENERATE)
  → same_section_cycle(poly, chuẩn)              (không ⇒ CYCLE_MISMATCH)
  ⇒ NORMALIZED_FROM_PLANE_SOLID_INTERSECTION
```

Thẩm quyền hình học là **đúng hai hàm `check_section_matches` dùng** — không có bản
cài thứ hai.

**Không bao giờ dùng làm bằng chứng:** tên chứa "section"/"thiết diện" · ID có tiền
tố · đúng ba đỉnh · đồng phẳng · đáp số diện tích đúng · vật tự khai `type = section`.

**Giữ nguyên** `producer`/`depends`/`sources`/`origin`: chương trình ấy dựng bằng
`construct_polygon`, và nói khác đi là nói dối về cách vật được tạo ra. Nguồn
plane–solid đi ở trường **riêng** `section_source`.

**Không bịa `steps`** — frontend đã có nhánh dự phòng (`scene3d-subentities.ts:258`),
và bịa bước dựng là bịa một thao tác chương trình chưa từng làm.

**Bí danh**: so **giá trị bộ nhớ**, không đi theo `depends`. `assign` không vào
`_NGUON_CUA_PHEP_DUNG` nên bí danh có `producer: null`; đi theo `depends` phải đoán
đâu là "chuỗi bí danh". So giá trị thì chính xác ở **mọi** độ sâu, và cảnh không bao
giờ rơi vào trạng thái nửa vời.

**Mâu thuẫn**: hai nghĩa vụ cùng chủ thể khai nguồn khác nhau ⇒ `AMBIGUOUS_SECTION_SOURCE`,
không "ai đến trước thắng" — nếu không, đảo thứ tự nghĩa vụ sẽ đổi kết quả.

## 4. Vị trí

```
build_simulation_state → build_scene3d
  → normalize_section_provenance      ← wave này
  → outcome.scene3d
  → CỔNG PHỦ NGHĨA VỤ TRỰC QUAN (863c912, KHÔNG sửa một dòng)
  → servable → envelope → cache
```

Cổng trực quan **giữ nguyên vai trò fail-closed**: normalizer chạy trước nó và chỉ
đổi thứ **có bằng chứng**; thứ không đủ bằng chứng vẫn là `polygon3` khi tới cổng.
`test_N` chứng minh trực tiếp — cùng chương trình, `solid` không giải được ⇒ vẫn bị
từ chối.

## 5. Bộ đo sai một lần, và nó là phát hiện đáng giá nhất

**Phép tiêm G2 (promote MỌI `polygon3`) không bắt được gì — 28/28 vẫn xanh.**

`test_B_da_giac_thuong_KHONG_bi_promote` chạy trên hợp đồng **không có**
`section_matches`, nên nhánh chuẩn hoá **chưa từng chạy**. Nó chứng minh *"không làm
gì khi không có gì để làm"*, không chứng minh *"không kéo theo vật khác"*.

Bản sửa: `test_B_da_giac_KHAC_khong_bi_keo_theo_khi_CO_mot_thiet_dien_hop_le` — hợp
đồng **có** một thiết diện hợp lệ, và `ABCD_base` (đáy hình vuông, z = 0) phải đứng
yên. Chạy lại G2 ⇒ đỏ.

Cùng lớp với F1 của wave trước: một test gọi thẳng hàm chứng minh **hàm đúng**, không
chứng minh **hàm được gọi đúng chỗ** — hay ở đây, **không chứng minh nhánh đã chạy**.

Một phát hiện thứ hai, từ cổng grounding: fixture bản đầu khai bốn đỉnh bằng
`declare_point` ⇒ bị từ chối (`initial_value` không có `source_fact_id`). Đó là hành
vi **đúng**, và nó nói thêm một điều: đường "polygon3 là thiết diện" chỉ tồn tại khi
các đỉnh được **dẫn xuất**. Fixture cuối dùng `midpoint(S, A/B/C/D)` — thiết diện
z = 3 của chóp S(0,0,6) đúng bằng bốn trung điểm ấy, nên không bịa một toạ độ nào.

## 6. Đính chính wave trước — đáp án cũ chính là lỗi

`test_accepted_output_quality::test_C_…` khẳng định: có `section_matches` thì cảnh
**vẫn** `FAIL` và **vẫn** `SILENT_VISUAL_OMISSION = True`. Đó đúng là **bệnh wave này
chữa**, không phải bất biến cần giữ.

Kỳ vọng mới: `scene_coverage = PASS` · `SILENT_VISUAL_OMISSION = False`. Nửa đầu test
(không có `section_matches`) **giữ nguyên**.

Hai sửa kèm ở **bộ đo** (`backend/scripts/`, ngoài `MEASURED_SYSTEM_PATHS`):

- `_kiem_thiet_dien` đọc thêm `section_source.plane` — thiết diện chuẩn hoá có
  `depends` là các **đỉnh**, nên tìm mặt phẳng trong `depends` sẽ báo
  `SECTION_PLANE_UNRESOLVED` oan.
- Cờ `SILENT_VISUAL_OMISSION` bỏ `construction_coverage` khỏi phép OR. Cảnh **có**
  vật thì không phải *"bỏ sót TRỰC QUAN"*. `construction_coverage = FAIL` (chương
  trình không gọi `construct_section`) vẫn là quan sát đúng và vẫn vào
  `SILENT_QUALITY_FAILURE` — không quan sát nào mất.

⚠️ **Không làm yếu phát hiện B02**: ở B02 cảnh **không có** vật `section` nào ⇒
`scene_coverage = FAIL` ⇒ cờ vẫn bật. Fixture B (đa giác đáy, sai chu trình) không
qua `same_section_cycle` ⇒ không chuẩn hoá ⇒ cũng vẫn bật. Cả hai còn xanh.

## 7. Cache và candidate

Bump **96 → 97**: nội dung **cảnh** trong envelope `ok` đổi (`type`, `polygon`,
`closed`, `section_source`), mà cache hit trả envelope **thẳng**, không dựng lại cảnh.
Chiều đổi là `rejected → served` nên **không row nào hoá sai** — nhưng envelope `ok`
sinh dưới v96 cho một đề có `section_matches` mang cảnh `polygon3`, tức cảnh frontend
không vẽ được thiết diện. Năm băm model-facing **không đổi một byte**.

✅ **Candidate đóng băng trong CLEAN VERIFICATION WORKTREE** tại `569b4f5`:
`cay_lam_viec_sach = true`. Wave trước phải ghi `false` vì cây nguồn mang việc xoá
favicon của user; wave này trả xong khoản nợ ấy **mà không đụng tới favicon**.

## 8. Giới hạn — phải đi kèm mọi con số

1. **Output live B02 không phục hồi được.** Mọi fixture là `DERIVED_STRUCTURAL_FIXTURE`.
   Wave này **không** chứng minh lượt B02 cũ sẽ được cứu — nó chứng minh **lớp** thất
   bại ấy nay được chuẩn hoá đúng khi có bằng chứng.
2. **0 lượt provider thật.** Normalizer chưa từng gặp một output mô hình mới.
3. **Khoảng trống hợp đồng vẫn còn**: một `area` đơn độc vẫn không nói được nó là
   thiết diện. Chỉ `section_matches` mới kích hoạt chuẩn hoá. Đề không khai
   `section_matches` vẫn rơi vào `UNVERIFIABLE` như ở wave trước.
4. **Hai test đỏ TỪ TRƯỚC wave**, đã chứng minh bằng worktree sạch tại `863c912`:
   `test_thesis_runner_alignment::test_H6` và
   `test_v3_product_path_parity::test_01…[manifest.json]`. Nợ cũ, không thuộc wave này.

```text
GEOMETRY_PRIMITIVE_COMPILER = NOT_RUN
TOKEN_OPTIMIZATION          = NOT_RUN
MERGE_ALLOWED               = NO
NEXT_ACTION                 = GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE
```
