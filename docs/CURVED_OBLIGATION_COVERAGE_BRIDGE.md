# CURVED_OBLIGATION_COVERAGE_BRIDGE — đóng lỗ mà V1 tìm ra

> Thực hiện **2026-09-03**. **0 lượt gọi model.**
> `CURVED_MODEL_ACCEPTANCE_V1` giữ nguyên, không sửa một con số.

---

## 1. Gốc — một sự thật được viết hai lần

`obligations.OBLIGATION_KINDS` giữ **bản sao viết tay** của câu *"nghĩa vụ này
nhận chủ thể kiểu nào"*, trong khi `measure_contract.BANG_PHEP_DO` đã trả lời
đúng câu ấy cho từng lượng đo.

Đo trên HEAD trước khi sửa:

| nghĩa vụ | `OBLIGATION_KINDS` | hợp của `BANG_PHEP_DO` | |
|---|---|---|---|
| `distance` | point3 · line3 · plane3 | point3 · line3 · plane3 | — |
| `angle` | line3 · plane3 | line3 · plane3 · **vector3** | ★ LỆCH |
| `volume` | solid | solid · **curved_solid** | ★ LỆCH |

```
MEASURE_COMPATIBILITY_AUTHORITIES_BEFORE   2  (DUPLICATED_MANUAL_AUTHORITY)
MEASURE_COMPATIBILITY_AUTHORITIES_AFTER    1
```

Chỗ lệch `volume` là thứ đã tốn **26 lượt gọi model** để tìm ra: ba chương
trình cong **hoàn toàn đúng** bị `REQUESTED_OPERATION_UNCOVERED`.

Chỗ lệch `angle` là **lỗi có từ trước, chưa ai thấy**: một chương trình đo
`angle_cos` trên vectơ — đúng hợp đồng phép đo — sẽ bị cổng phủ bác. Lượt soát
này tìm ra nó vì nó so hai bảng thay vì sửa một dòng.

---

## 2. Sửa — dẫn xuất, không chép

```
MEASURE_SIGNATURE_OWNER          measure_contract.BANG_PHEP_DO
OBLIGATION_KIND_OWNER            obligations.OBLIGATION_KINDS  (nghĩa vụ CẤU TRÚC)
COVERAGE_COMPATIBILITY_OWNER     measure_contract.kieu_chu_the_nghia_vu
ANALYZE_OBLIGATION_OWNER         domain_profile.geometry_obligation_kinds (dẫn xuất)
```

`NGHIA_VU_DO` giữ **đúng một** thứ không dẫn xuất được: ánh xạ *nghĩa vụ →
lượng đo*. Nó là một-nhiều và không suy từ tên — `angle` ứng với cả
`angle_cos_sq` (không dấu) lẫn `angle_cos` (có dấu), vì đề hỏi *"góc"* mà không
nói nó cần dấu hay không; chương trình mới nói.

**Kiểu chủ thể thì không nằm ở đó** — nó là hợp của `kieu_of` trên các lượng đo
ấy. Mở một lượng đo cho một kiểu mới là nghĩa vụ tương ứng **tự** nhận kiểu ấy.

```
OBLIGATION_KINDS_ROLE_AFTER
  literal giữ:  point_on_line · point_on_plane · parallel · perpendicular
                · coplanar · section_matches  (+ 10 nghĩa vụ Tin học)
  nạp dẫn xuất: distance · angle · volume
```

`test_OBLIGATION_KINDS_khong_con_ban_sao_VIET_TAY` đọc **literal của bảng** và
cấm ba nghĩa vụ đo quay lại — nếu không, bản sao sống lại và lần trôi sau lại
tốn một lượt đo live để tìm.

```
VOLUME_CURVED_COVERAGE   PASS      MEASURE_COVERAGE_DRIFT   0
```

---

## 3. `radius` · `lateral_area` · `area` — chính sách, không phải bỏ sót

```
RADIUS_OBLIGATION_NEEDED       NO   (chưa có phép đo nào chứng minh là cần)
RADIUS_OBLIGATION              NOT_ADDED
LATERAL_AREA_OBLIGATION        NOT_NEEDED
AREA_CIRCLE_COVERAGE           PASS
```

Cổng phủ chỉ kiểm **nghĩa vụ ĐÃ KHAI**. Ba lượng đo này không có nghĩa vụ nào
ánh xạ tới, nên chúng **không bị cổng bác** — và đó là lý do `area(circle3)` đi
trọn đường sản phẩm (`test_09b`, kết quả `16π`).

Thêm nghĩa vụ cho chúng sẽ đổi **lược đồ `analyze`** (model-facing) và đổi băm
taxonomy đã niêm phong. §8 của wave cấm dựng taxonomy chết, nên chưa thêm.

⚠️ Khai chính xác điều còn thiếu: `area(circle3)` không bị bác **không phải vì
cổng hiểu nó**, mà vì không có nghĩa vụ nào để kiểm. Khi nào cần thêm: khi đo
được rằng `analyze` gán nhầm một nghĩa vụ khác cho câu *"tính diện tích xung
quanh"*. Chưa có phép đo ấy.

---

## 4. Ba chương trình V1 — và hai giới hạn phải khai

```
CAPTURED_V1_SYSTEM_BLOCKERS_FIXED   3/3   (tại CỔNG PHỦ — thứ wave này sửa)
```

`test_15b` dựng lại **trạng thái CŨ** (bản sao viết tay) rồi khẳng định cổng bác
với đúng mã và đúng thông điệp — chứng minh cầu nối sửa đúng thứ nó nói, thay
vì tin lời kể.

Nhưng *"qua cổng phủ"* ≠ *"chạy trọn đường"*, và gộp hai câu ấy là cách một
wave tự khen:

| ca | cổng phủ | đường đầy đủ | vì sao |
|---|---|---|---|
| `ball_1` | ✔ | **✔ chạy trọn** | — |
| `cylinder_1` | ✔ | **chưa chứng nhận được** | artifact V1 **không lưu `RequestContract`** (thiếu sót của runner V1, đã ghi trong báo cáo ấy), nên `InputFact.values` không tái dựng được và cổng xuất xứ bác vì một lý do KHÔNG có trong lượt thật. Giới hạn của **phép đo**, không của hệ. |
| `cone_1` | ✔ | **không** | có **khiếm khuyết THỨ HAI của mô hình**, trước đây bị cổng phủ che vì cổng phủ chạy trước: `AMBIGUOUS_FIRST_BINDING` trên `S.O`. §16 cấm sửa lỗi mô hình trong wave này. |

`test_15d` khoá cả hai sự thật ấy để chúng không lặng lẽ đổi.

---

## 5. Kiến trúc test — sửa nguyên nhân, không sửa triệu chứng

Lỗ sâu hơn là **các ca "đường đầy đủ" của Phase 2 dừng TRƯỚC
`verify_and_compile`**: chúng gọi `kiem_tinh` → interpreter → `build_scene`, nên
grounding và cổng phủ chưa từng chạy với một khối cong.

```
FULL_PRODUCTION_ROUTE_CERTIFICATION
  _duong_san_pham()  →  verify_and_compile
                     =  grounding → CỔNG PHỦ → tĩnh → interpreter → vết
```

Hai cổng chống tái phát:

- `test_KIEN_TRUC_moi_ca_duong_day_du_phai_qua_verify_and_compile` — cấm một ca
  trong phần chứng nhận gọi thẳng interpreter.
- `test_KIEN_TRUC_verify_and_compile_THAT_SU_chay_ca_hai_cong` — **đọc mã**,
  không tin tên hàm.

---

## 6. Danh tính — một lỗ thật, và đã đóng

Trước wave này:

```
COVERAGE_SEMANTICS_IN_CAPABILITY_IDENTITY   NO
```

Bảng kiểu chủ thể **quyết định chương trình nào được nhận**, mà đổi nó thì
`stable_capability_hash` **không nhúc nhích** — ba chương trình cong bị bác rồi
được nhận, cùng một băm. `runtime_doctor` không phân biệt nổi hai container ấy.

Sửa theo **phương án A**: mở rộng chính thẩm quyền đã có
(`capability_fingerprint`) thêm `nghia_vu_chu_the`. Không dựng vân tay thứ hai.

```
COVERAGE_SEMANTICS_IN_CAPABILITY_IDENTITY   YES
STABLE_CAPABILITY_HASH   8d51b70f2d52fd2d… → 100c71f0bd01ed1d…   ĐỔI
cổng danh tính cache: ĐỎ trước khi làm mới, `thành phần đổi: ['capability']`
```

---

## 7. Hợp đồng gửi cho mô hình — **không đổi một byte**

```
MODEL_FACING_ANALYZE_SCHEMA_CHANGED   NO   (2145 byte, enum 9 nghĩa vụ y nguyên)
SYNTHESIS_SCHEMA_CHANGED              NO   (111.152 byte)
GRAMMAR_CARD_CHANGED                  NO   (4035 byte)
PROMPT_CHANGED                        NO
```

`geometry_obligation_kinds()` không đổi vì `vector3` và `curved_solid` đều đã là
kiểu hình học — phép thử *"nhận toàn bộ chủ thể là kiểu hình học"* vẫn cho đúng
9 nghĩa vụ.

```
CACHE_VERSION   66 → 67
```

Model-facing không đổi, **nhưng runtime đổi phán quyết**: một chương trình từng
bị `REQUESTED_OPERATION_UNCOVERED` nay chạy trọn. Envelope đã cache cho những đề
ấy là một **lời từ chối** của một hệ không còn tồn tại.

---

## 8. Taxonomy niêm phong — §18

`OBLIGATION_KINDS` đổi giá trị ở hai nghĩa vụ, nên **băm taxonomy đổi** và
candidate sản phẩm được đóng băng lại.

```
SEALED_RESEARCH_OBLIGATION_TAXONOMY   giữ nguyên, gắn với baseline a075e9f5…
CURRENT_PRODUCT_OBLIGATION_COVERAGE   mở rộng 2026-09-03 (wave này)
```

⚠️ Đây là **mở rộng của sản phẩm hiện tại SAU baseline đã niêm phong**. Điểm số
lịch sử vẫn gắn với taxonomy/phiên bản gốc của chúng, và **không được** so với
số đo sau này mà không nói rõ phiên bản. Baseline `a075e9f5…` không đổi, không
chạy lại.

---

## 9. R0 và ranh giới — không nới một ly

```
R0                            PASS      CURVED_GEOMETRY_LAUNDERING   0
_KIEU_DUOC_GIA_THIET          {point3, vector3}   không đổi
mặt phẳng xiên ∩ trụ          vẫn bị từ chối (test_17)
```

Cầu nối chỉ chạm **bảng kiểu của nghĩa vụ**. Một lượng đo hợp lệ không được làm
một *phép hình học* ngoài bao đóng thành chạy được — `test_17` khoá đúng điều
đó bằng một chương trình đi trọn đường rồi vẫn phải chết.

---

## 10. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **3009 passed**, 1 skipped (+26 ca mới) |
| `vitest` | **687 passed** (50 tệp) |
| `npm run build` | PASS |
| `replay` · `crash surface` | 5/5 · 1/1 · 6/6 ném 0 |
| `lock_cache_identity --verify` | exit 0 · version 67 |
| `freeze --verify` | 89 file · `9e9137f315cd5b31…` |

⚠️ **Đính chính con số frontend.** Báo cáo Phase 3 ghi *"vitest 690"*; con số ấy
đo lúc **việc chưa hoàn thành của người dùng còn trong cây làm việc**. Trên cây
sạch ở HEAD, số đúng là **687**. Không test nào của tôi mất; ba ca kia thuộc về
công việc đã được revert.

```
CURVED_PRODUCT_ENABLED   NO   (ball · cylinder · cone vẫn `foundation_only`)
APPLICATION_LLM_CALLS    0
CURVED_OBLIGATION_COVERAGE_GAP   CLOSED
```
