# RADIUS_VERIFICATION_BRIDGE — đóng khoảng safe-serve

> Thực hiện **2026-09-03**. **0 lượt gọi model.**
> `CURVED_ACCEPTANCE_V1` và `V2` bất biến. `SEALED_RESEARCH_BASELINE = a075e9f5…`
> không đổi, không chạy lại.

---

## 1. Khoảng phải đóng

`RADIUS_OBLIGATION_COVERAGE` mở nghĩa vụ `radius` và **cố ý không** thêm
checker — vì thêm checker là một tuyên bố năng lực riêng, phải là một quyết
định riêng. Hệ quả đúng nhưng khó chịu:

```
RADIUS_VERIFICATION_BEFORE   NONE
RADIUS_SAFE_SERVE_BEFORE     executable = True  ·  servable = False
                             weak_kinds = ['radius']  ·  verification_gap
```

Hệ tính ra đúng `√3` rồi **không dám phục vụ** con số nó vừa tính xong.

---

## 2. §3 — có checker đo tổng quát để dùng lại không? **KHÔNG**

```
CHECKER_REGISTRY_OWNER    geometry_obligations.GEOMETRY_CHECKERS
CHECKER_SIGNATURE_OWNER   callable(snapshot, ob) -> str | None
SAFE_SERVE_OWNER          obligations.has_server_owned_checker → postconditions.CHECKERS
MEASURE_RESULT_OWNER      geometry_exec._do  (qua curved.ban_kinh)
GENERIC_MEASURE_CHECKER_REUSED   NO
```

Registry khoá theo **obligation kind**, và mỗi checker đo lường nhúng phép
**tính lại riêng của nó** (`distance_sq_*`, `volume_polyhedron`). Không có
thẩm quyền *"tính lại lượng đo tên X"* nào để tái dùng — nên `check_radius` là
cần thật, và nó dài 15 dòng.

`postconditions.CHECKERS` dẫn xuất bằng `**GEOMETRY_CHECKERS`, nên đăng ký một
chỗ là đủ; **không có bảng thứ hai để quên**.

---

## 3. Checker — một hàm, bốn chủ thể

```
RADIUS_CHECKER   geometry_obligations.check_radius
SHAPE_SPECIFIC_RADIUS_CHECKERS   0
```

Hình nào là **dữ liệu** (`curved_kind`), và `radius_sq` là một `@property` dẫn
từ ba điểm neo — **cùng một công thức** cho cầu, trụ, nón. `Circle3` vào cùng
cửa vì nó cũng chở `radius_sq`. Ba checker sẽ là ba bản của một phép trừ vectơ,
và chúng sẽ lệch nhau ở ca thứ ba.

**So trên miền BÌNH PHƯƠNG**, cùng lý do `check_distance`: `square()` của một
căn **luôn hữu tỉ**, nên phép so đi hết trong ℚ kể cả khi đáp số là `√3`. Bộ
chấm càng biết ít về miền số thì càng khó sai theo cùng một cách.

⚠️ Lấy `radius_sq` từ chính vật, **không** gọi `ban_kinh` rồi bình phương lại:
`ban_kinh` *là* `sqrt_rational(radius_sq)`, nên đi vòng chỉ thêm một phép căn
rồi một phép bình phương để về đúng chỗ cũ. Và `radius_sq` tính lại từ ba điểm
neo mỗi lần, nên **không có bản lưu nào để trôi**.

---

## 4. Kết quả

```
RADIUS_VERIFICATION_AFTER   check_radius đăng ký, has_server_owned_checker = True
RADIUS_SAFE_SERVE_AFTER     executable = True  ·  servable = True
RADIUS_CIRCLE               PASS      RADIUS_CURVED_SOLID   PASS
RADIUS_IRRATIONAL           PASS      (R² = 3 ⇒ R = √3, so chính xác)
WRONG_RADIUS_VALUE          REJECTED  (4 giá trị sai, cả hai đường vào)
```

**Checker có răng, chứng minh chứ không kể**: `test_T4` cho nó `2`, `4`, `√2`,
`2√3` trên một khối `R = √3` và đòi nó bác cả bốn. `test_T4b` làm chiều thứ hai
— giá trị **đề mong** (`params.value`) sai cũng phải bác. `test_T4c` cho đề
viết `sqrt(3)` bằng chữ, đi qua văn phạm hẹp của `parse_exact`.

### Hai nhân chứng đường đầy đủ

```
V1_BALL_CLEAN_ROUTE       PASS · servable=True · R = 6 · V = 288π
CIRCUMSPHERE_CLEAN_ROUTE  PASS · servable=True · tâm (1,1,1) · R = √3
```

Nhân chứng mặt cầu ngoại tiếp dựng **bằng hợp thành đã có** — ba mặt trung trực
qua `plane_perpendicular_to_line` của G4, giao hai mặt lấy đường, giao với mặt
thứ ba lấy tâm. **Không một primitive nào thêm cho riêng bài toán này**, và tâm
do **kernel tính**, không do chương trình khai.

⚠️ Cố ý **không** dùng chương trình V2 cho nhân chứng này: nó hỏng vì lỗi mô
hình (dựng `circumsphere` mà không khai), và một nhân chứng phải chứng minh
**HỆ**, không chứng minh một lượt sinh cụ thể.

---

## 5. Điều wave này KHÔNG làm

```
MEASURE_COMPATIBILITY_AUTHORITIES   1   (không đụng tới)
R0                                  PASS
CURVED_GEOMETRY_LAUNDERING          0
checker thêm ngoài `radius`         0
```

Checker trả lời *"con số này có đúng không"*; `BANG_PHEP_DO` trả lời *"chủ thể
này có hợp không"*. Trộn hai câu ấy là dựng lại đúng bản sao mà
`CURVED_OBLIGATION_COVERAGE_BRIDGE` vừa gỡ — `test_T11` khoá luôn việc checker
không được chép danh sách kiểu (nó `isinstance`, tức hỏi lớp **runtime**).

`test_T8_T9` cấm thêm tiện tay `lateral_area`/`surface_area`/`skew_lines`/
`line_in_plane`. `lateral_area` vẫn là **UNKNOWN_NEED** — không phải NO.

---

## 6. Hợp đồng và phiên bản

```
MODEL_FACING_CONTRACT_CHANGED   NO
  ANALYZE_SCHEMA    2155 byte   không đổi
  SYNTHESIS_SCHEMA  111.152     không đổi
  GRAMMAR_CARD      4035        không đổi
  PROMPT                        không đổi
```

Checker tất định — mô hình không cần biết thêm gì.

Cổng danh tính cache **đỏ trước khi làm mới**, nêu đúng **một** thành phần:

```
thành phần đổi: ['capability']
CAPABILITY_HASH   917c037ab5f7ad7c… → 024799b84cf528db…
CACHE_VERSION     68 → 69
```

Lý do bump: model-facing không đổi, **nhưng phán quyết sản phẩm đổi**. Một
envelope đã cache cho đề hỏi bán kính mang `servable=False`; hệ hiện tại kiểm
chứng được và phục vụ được. Trả lại envelope cũ là nói với học sinh rằng hệ
không dám phát một đáp số nó đã kiểm xong.

---

## 7. Taxonomy checker — §15

```
SEALED_GEOMETRY_CHECKERS            9    (gắn với baseline a075e9f5…)
CURRENT_PRODUCT_GEOMETRY_CHECKERS  10    (+ radius, 2026-09-03)
HISTORICAL_SAFE_SERVE_SCORES_CHANGED   NO
```

⚠️ Mọi con số *"safe serve rate"* lịch sử gắn với bản **9**. So chúng với số đo
sau này mà không nói rõ phiên bản là so hai hệ khác nhau. Đã ghi vào
`CURRENT_STATE.md` ngay cạnh danh sách checker, và vào
`test_co_that_it_nhat_mot_nghia_vu_muc_yeu`.

`radius` **vẫn không có ô held-out** — pool niêm phong trước khi nó tồn tại.
Nên held-out không đo câu hỏi bán kính, và số của nó không nói gì về năng lực
ấy.

---

## 8. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **3057 passed**, 1 skipped (+25 ca mới) |
| `vitest` | **687 passed** (50 tệp) |
| `npm run build` | PASS |
| `replay` · `crash surface` | 5/5 · 1/1 · 6/6 ném 0 |
| `lock_cache_identity --verify` | exit 0 · version 69 |
| `freeze --verify` | 89 file · `d62545e5b5f917db…` |
| chín phép đo trình duyệt | 21/21 · 8/8 · 7/7 · 7/7 · 9/9 · 4/4 · 13/13 · 11/11 · 21/21 · **CONSOLE_ERRORS 0** |

```
BALL_PRODUCT_ENABLED  NO   CYLINDER_PRODUCT_ENABLED  NO   CONE_PRODUCT_ENABLED  NO
APPLICATION_LLM_CALLS  0
RADIUS_VERIFICATION_BRIDGE   CLOSED
```

Checker closure **không phải** bằng chứng model-discoverability. Ba dòng năng
lực sản phẩm không đổi một chữ.

---

## 9. Một ca thử đổi chiều trong cùng ngày

`test_R7c` của wave trước khẳng định `not kq.servable` — đúng lúc ấy. Wave này
làm nó thành `kq.servable`. Ca được **giữ lại và đổi chiều kèm chú thích**, thay
vì xoá: nó là chỗ duy nhất trong kho đọc được rằng **cổng phủ** và **cổng kiểm
chứng** là hai thứ, và chúng được mở ở hai lượt khác nhau vì hai lý do khác
nhau.
