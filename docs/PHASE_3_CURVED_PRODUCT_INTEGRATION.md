# PHASE_3_CURVED_PRODUCT_INTEGRATION — phần tất định

> Thực hiện **2026-09-03**. Trạng thái: **PARTIAL, có chủ đích.**
>
> §2–§7 và §17 (tất định, **0 lượt gọi model**) đã xong.
> §8 (phép đo mô hình) **chưa chạy** — nó tiêu quota thật, và
> `CLAUDE.md §4` buộc xin quyết định của người trước.

---

## 1. Thứ tự bắt buộc, và ta đang ở đâu trên đó

```
1. gỡ mâu thuẫn prompt ↔ thẻ          ✔ XONG
2. bằng chứng tất định offline + trình duyệt   ✔ XONG
3. một phép đo năng lực trên mô hình   ⏸ CHỜ QUYẾT ĐỊNH — tiêu quota
4. bật năng lực nào ĐẠT               ⏸ phụ thuộc bước 3
```

Bước 3 là **cổng duy nhất** giữa `foundation_only` và `supported`. Không có nó
thì mọi lời bật năng lực đều là lời hứa chưa ai kiểm — đúng thứ
`product_capability.py` được dựng ra để chặn.

---

## 2. Mâu thuẫn đã gỡ (§2)

```
PROMPT_GRAMMAR_CONTRADICTION_BEFORE  1
PROMPT_GRAMMAR_CONTRADICTION_AFTER   0
```

Phase 2 đóng lại ở một trạng thái mâu thuẫn cố ý: thẻ văn phạm **dạy**
`construct_curved_solid` trong khi prompt vẫn **bảo**

> *"Đề cần mặt cầu, mặt nón, mặt trụ hoặc quỹ tích — nói thẳng là không diễn
> đạt được"*

Nay câu ấy thành **ranh giới chính xác**:

```
CURVED_PROMPT_SCOPE
  DỰNG ĐƯỢC   cầu · trụ · nón  (construct_curved_solid, ba ô neo là TÊN ĐIỂM)
  VẪN TỪ CHỐI mặt phẳng cắt XIÊN trụ/nón (elip)
              giao ĐƯỜNG THẲNG với mặt cong (toạ độ vô tỉ)
              hai mặt cong cắt nhau
              khối TRÒN XOAY tổng quát · khối ghép/bù · mọi QUỸ TÍCH
```

Ngôn ngữ fail-closed giữ nguyên: *"nói thẳng là không diễn đạt được"*, *"một mô
phỏng sai hình còn tệ hơn không có mô phỏng"*.

**Ba cổng máy**, không phải một lời hứa trong chú thích:

| cổng | đo gì |
|---|---|
| `test_29` | không câu nào của prompt vừa nhắc một hình cong vừa nói *"không diễn đạt được"* — khoá theo **hình dạng**, không theo một câu cụ thể |
| `test_29b` | bốn ranh giới (`xiên` · `vô tỉ` · `quỹ tích` · `tròn xoay`) và ngôn ngữ fail-closed **phải còn** |
| `test_29c` | §3 — prompt **không** chứa mẫu chương trình theo hình, và **phải** dạy lối hợp thành cho thiết diện qua trục |

### Ngân sách prompt 4800 → 5700

4794 → **5612** byte (+818). Ba khoản đều rơi vào ngoại lệ mà chính ngân sách
thừa nhận — *luật không mã hoá được thành ràng buộc HỮU ÍCH* — và lý do là một
tính chất kiến trúc:

> `construct_curved_solid` thẩm định ở **runtime** (`CurvedSolid.__post_init__`
> kiểm vành ⊥ trục), còn vòng sửa ≤3 lượt đóng ở tầng **tĩnh**. Một lỗi chọn hệ
> trục **giết cả ca, không có lượt sửa nào**. Với luật ấy, *"để validator giữ"*
> không rẻ hơn — nó là mất ca.

Khoản lớn nhất (~440 byte) phần lớn là **viết lại**, không phải thêm.

---

## 3. Bằng chứng tất định (§5, §6)

```
CURVED_OFFLINE_SAMPLES   6/6 PASS · APPLICATION_LLM_CALLS 0
```

| bài | đáp số | kiểm tay |
|---|---|---|
| `cau-the-tich` | `R = 3`, `V = 36π` | ✔ |
| `cau-cat-mat-phang` | `r = 4`, `S = 16π` | `r² = 25 − 9` ✔ |
| `tru-truc-xien` | `V = 15π`, `S_xq = 6π√5`, `h = 3` | trục `(1,2,2)`, `r = √5` **vô tỉ**, toạ độ vẫn hữu tỉ ✔ |
| `tru-thiet-dien-tron` | `r = 2` | qua `plane_perpendicular_to_line` của G4 ✔ |
| `non-duong-sinh` | `l = 5`, `V = 12π`, `S_xq = 15π` | `l` đo bằng `distance(S, A)` — **không** có `slant` ✔ |
| `non-thiet-dien-truc` | `S = 12` | `divide_segment` + `construct_polygon` + `area` — **0 phép dựng mới** ✔ |

Không bài nào có mã riêng theo hình: cả sáu gọi cùng `_khoi_cong()` với
`curved_kind` khác nhau.

```
CURVED_BROWSER_OFFLINE   21/21 PASS · CONSOLE_ERRORS 0
```

`certify-curved-product.mjs` đo trong Chrome thật: khung dựng được cho cả bốn
loại · đáp số chính xác lên dải kết quả · chọn được vật · ô soi nói tên tiếng
Việt · tua bước · mở bài khác dựng sạch · bề mặt không hứa khối tròn xoay/ghép–bù.

⚠️ Nó canh **bất biến lưới trên DỮ LIỆU THẬT**, không chỉ trên bảng `_TRUONG`:
đọc payload trong store và khẳng định `curved_solid` có ba điểm neo + `radius_sq`
mà **không** có `vertices`/`faces`.

---

## 4. Hai lỗi hiển thị do phép đo tìm ra

Cả hai chỉ lộ ra khi nhìn bề mặt thật, không ca pytest nào bắt được:

**① *"khối tròn xoay"* làm danh từ của một khối cầu.** Vừa sai nghĩa, vừa **hứa
đúng một năng lực mà `product_capability` khai là `unsupported`**. Sửa:
`_DANH_TU_NGAN["curved_solid"]` → *"khối cong"*.

**② `reference` bỏ qua nhãn ngắn mô hình đặt.** Khối cầu đã có nhãn `(S)` vẫn bị
nhắc bằng cả câu gọi tên, rồi câu ấy lồng vào tên vật khác:

```
trước:  Đường tròn giao của «Khối cầu tâm I, đi qua A» và (HUW)
sau:    Đường tròn giao của (S) và (HUW)
```

Sửa: nhãn mô hình được xét cho `reference` **khi nó ngắn như một ký hiệu**
(không có dấu cách — cùng phép thử `_boc` đã dùng).

---

## 5. Thẩm quyền năng lực sản phẩm (§7)

`app/simulation/product_capability.py` — **một** chỗ trả lời *"hình này đã hỗ
trợ chưa"*. Trước bản này frontend không có nơi nào để hỏi, nên câu trả lời sẽ
là một **danh sách mong muốn** viết tay trong một component.

```
polyhedron · section              supported        (có artifact)
ball · cylinder · cone            foundation_only  (hệ xong, MÔ HÌNH chưa đo)
solid_of_revolution               unsupported
composite_subtractive             unsupported
curved_oblique_section            unsupported
```

Constructor **NÉM** nếu khai `supported` mà không nêu bằng chứng — cùng luật
`STATUS_LEDGER` áp cho mọi dòng DONE, cưỡng chế ngay ở chỗ khai.

```
BALL_PRODUCT_ENABLED       NO      CYLINDER_PRODUCT_ENABLED   NO
CONE_PRODUCT_ENABLED       NO      SOLID_OF_REVOLUTION_ENABLED NO
COMPOSITE_SUBTRACTIVE_ENABLED NO   SHAPE_SPECIFIC_PRODUCT_MODULES 0
```

---

## 6. Phiên bản (§17, §18)

Cổng danh tính cache **đỏ trước khi làm mới**, và nêu đúng **một** thành phần:

```
thành phần đổi: ['prompts']
```

Đúng chữ ký §18 dự đoán cho một wave chỉ đổi prompt.

```
CACHE_VERSION            65 → 66
SEMANTIC_ENV_HASH        15ac9710ffb2dd1d… → 6aefad0315e6f8c0…
STABLE_CAPABILITY_HASH   8d51b70f2d52fd2d…  **KHÔNG ĐỔI**  ← §18 đúng
PRODUCT_CANDIDATE        25de3a88ba6f8dc9… → 4fd333419f9b760f…  (88 → 89 file)
SEALED_RESEARCH_BASELINE a075e9f5…  không đổi, không chạy lại
HISTORICAL_BENCHMARKS_RERUN  NO    HISTORICAL_SCORES_CHANGED  NO
```

Lý do bump: envelope đã cache cho một đề hình cong là **một LỜI TỪ CHỐI**, sinh
bởi một hệ nay dựng được chính hình ấy.

---

## 7. Cổng

| cổng | kết quả |
|---|---|
| `pytest` | **2979 passed**, 1 skipped |
| `vitest` | **690 passed** (50 tệp) |
| `npm run build` | PASS |
| `replay_demo_cases` · `crash_surface` | 5/5 · 1/1 · 6/6 ném 0 |
| `lock_cache_identity --verify` | exit 0 · version 66 |
| chín phép đo trình duyệt | **21/21** (cong, mới) · 8/8 · 7/7 · 7/7 · 9/9 · 4/4 · 13/13 · 11/11 · 21/21 · **CONSOLE_ERRORS 0** |

⚠️ Hai cổng *"đòi cây sạch"* (`test_holdout_readiness_7b`,
`test_candidate_ghi_dung_commit_va_cay_sach`) đang đỏ vì cây làm việc có **việc
đang dở của người dùng** (`TopNav.tsx` + ba tệp frontend). Không phải lỗi của
wave này, và **không được** commit hộ để làm chúng xanh.

---

## 8. Điều CHƯA làm, và vì sao

**ĐÃ CHẠY 2026-09-03** — xem `docs/CURVED_MODEL_ACCEPTANCE_V1.md`.

```
MODEL_CASES_TOTAL   9      APPLICATION_LLM_CALLS   26   TOTAL_TOKENS  146.444
ONE_SHOT_CORRECT    2      ONE_SHOT_EXECUTABLE_IR   0
ONE_SHOT_HONEST_REFUSALS  2/2            CURVED_GEOMETRY_LAUNDERING  0
BLOCKER  CURVED_OBLIGATION_COVERAGE_GAP
         OBLIGATION_KINDS['volume'] chỉ nhận 'solid'; không có nghĩa vụ cho
         radius/lateral_area ⇒ chương trình cong ĐÚNG bị cổng phủ từ chối.
BALL/CYLINDER/CONE_PRODUCT_ENABLED   NO · NO · NO
```

Phép đo **DỪNG** theo §19: lỗ nền không được vá giữa chừng rồi chạy tiếp cùng
bộ ca. Sửa thành wave riêng, rồi chạy một acceptance mới ghi rõ version.

§8 cần khoảng 8 ca × (1 lượt phân tích + 1 lượt tổng hợp) ≈ **16–24 lượt gọi
thật**, cộng lượt sửa nếu pipeline tự kích hoạt.

`CLAUDE.md §4` viết thẳng: **"Xin quyết định của user trước khi tiêu call
thật"**, và `§0` vẫn ghi benchmark ĐÓNG. Đây là một phép đo **MỚI** (không phải
chạy lại benchmark lịch sử), nên nó không phạm `§0` — nhưng nó tiêu quota, nên
quyết định thuộc về người.

```
SYSTEM_CURVED_FOUNDATION   CLOSED
CURVED_PRODUCT_CAPABILITY  PARTIAL   (tất định xong, mô hình chưa đo)
PHASE_3                    PARTIAL
```
