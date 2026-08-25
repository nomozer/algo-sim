# PHASE 6.6 — GEOMETRY SEMANTIC STABILIZATION (2026-08-26)

> Câu hỏi cuối cùng của pha này, viết nguyên văn:
> *"Hệ thống mô phỏng 3D hình học không gian đã đủ ổn định để đo năng lực AI
> sinh chương trình hay chưa?"*
>
> **Trả lời: CHƯA — nhưng lý do đã thu hẹp lại còn đúng MỘT nguyên nhân, và
> nguyên nhân ấy không vá được bằng code.**

---

## 1. Changed files

`backend/app` — 8 file, +270 dòng:

| File | Đổi gì |
|---|---|
| `semantic_program/contract.py` | `ConstructPolygonStmt` + vào union `SemanticStatement` |
| `semantic_program/geometry_exec.py` | `exec_construct_polygon` — kiểm trùng đỉnh + đồng phẳng |
| `semantic_program/interpreter.py` | nhánh thực thi + một bước timeline |
| `semantic_program/domain_profile.py` | `tach_ky_hieu_diem` · `khop_theo_topo` · `_SO_BANG_TAP_CON` |
| `semantic_program/coverage_gate.py` | dựng bảng topology; `_hoa_giai` ba lưới có thứ tự; ghi lưới nào ra tay |
| `semantic_program/validator.py` | đăng ký `construct_polygon` ở hai chỗ (tham chiếu + tên đọc) |
| `semantic_program/simulation_state.py` | provenance của phép dựng mới |
| `main.py` | `CACHE_VERSION` 44 → 45 |

Artifact sinh lại: `docs/schemas/semantic_program.schema.json` +
`frontend/src/simulations/domains/generic/semantic_program.schema.json` (hai bản
phải khớp byte-đối-byte) + `EVALUATION_CANDIDATE.json`.

**Frontend: 0 dòng.** Không renderer, không UI, không animation.

---

## 2. Tests

`tests/geometry/test_phase66_stabilization.py` — **19 test mới**, ba nhóm:

- **TASK 1** (6) — `đáy ABCD` nói được như một vật · đỉnh trùng NÉM · không đồng
  phẳng NÉM · lên được cảnh 3D **mà không sửa renderer** · R0: chỉ nhận TÊN.
- **TASK 2** (9) — năm cách đặt tên khác nhau đều khớp (gồm `duong_thang_1`,
  **không chia một ký tự nào** với `AD`) · **không che lỗi thật** · mơ hồ ⇒
  fail-closed · kiểu cũng lọc ứng viên · mọi ký hiệu phải là điểm đã khai.
- **CẤM** (4) — không target mới (24) · đúng sáu phép dựng · `_PHU_TO_KIEU` bị
  **ghim độ dài** · kernel không bị sửa.

Cập nhật 3 test cũ, **không nới cái nào**:
`test_symbol_namespace` (thông điệp nay kèm tên lưới) ·
`test_end_to_end_geometry` (tập phép dựng 5 → 6; **giữ nguyên** vai trò bằng
chứng rằng nửa sau của chuỗi `đáy → khối` vẫn chưa có) ·
`test_grammar_card` (trần 3900 → 4000 cho một câu lệnh, ~62 byte).

```
pytest  2825 passed · geometry 689
vitest  1598 passed
```

---

## 3. Architecture impact

**Không đảo chiều phụ thuộc nào, không thêm tầng nào.**

`construct_polygon` không thêm **năng lực tính toán** — mọi mảnh đã có sẵn và
test khoá từng vế:

```
polygon3        MemoryType  từ Wave 2
predicates      coplanar · same_point  đã có trong kernel
RENDER_HINT     "polygon3" → "polygon"  từ Phase 5C
simulation_state  đã chiếu tuple-các-đỉnh thành cảnh
```

Thứ duy nhất còn thiếu là **cách nói**. Câu lệnh này mở một đường khai báo hợp
lệ cho một kiểu đã tồn tại.

`khop_theo_topo` **thay đổi bản chất** của tầng hoà giải, không mở rộng nó. Ba
lưới nay chạy theo thứ tự và `symbol_reconciled` ghi lưới nào đỡ:

```
① topology        vật nào DỰNG TỪ đúng những điểm này        ← nguyên tắc
② ký hiệu điểm    m ≡ M (viết hoa lõi, ≤3 ký tự)
③ phụ tố kiểu     SA ≡ SA_line — LƯỚI CUỐI, dựa vào chính tả
```

Lưới ③ nay chỉ còn phục vụ vật khai bằng `initial_value` (không có topology để
so), và độ dài danh sách của nó **bị test ghim**.

---

## 4. Vì sao đây KHÔNG phải bước về phía GeoGebra

Bốn điều, mỗi điều có test:

| | |
|---|---|
| **Không phép tính mới** | `construct_polygon` gọi `same_point`/`coplanar` — thứ kernel đã có. Kernel không đổi một dòng. |
| **Không công cụ dựng hình** | Không toolbar, không kéo thả, không click tạo hình, không nhập lệnh. Frontend 0 dòng. |
| **Không phải người dùng dựng** | Người dùng gõ **đề bài**. AI viết chương trình, engine tất định chạy. R0 nguyên vẹn: `ConstructPolygonStmt` nhận **TÊN**, không nhận toạ độ — có test khoá đúng bộ trường. |
| **Chuỗi dựng vẫn bị chặn** | Nửa sau của `đáy → khối` (`extrude`) **vẫn chưa có**, và test cũ giữ nguyên vai trò bằng chứng. Không ai "nâng đáy thành khối" được. |

GeoGebra cho người dùng **dựng hình bằng tay**. Ở đây con người chỉ đưa **đề
bài**, và toàn bộ giá trị nằm ở chỗ chương trình dựng ra **được kiểm chứng** —
không ở chỗ vẽ được nhiều hình hơn.

---

## 5. Smoke result — before / after

### Trước Phase 6.6 (bốn lượt, `docs/…/DEV_ENV_CONSOLIDATION_2026_08_26.md`)

| Lượt | 1 · trung điểm | 2 · thể tích | 3 · thiết diện |
|---|---|---|---|
| ① | ✅ | ❌ `learner_surface` | ❌ `structural_coverage` |
| ② | ❌ `structural_coverage` | ✅ | ❌ `structural_coverage` |
| ③ | ✅ | ✅ | ❌ `postconditions` |
| ④ | ✅ | ❌ `grounding` | ❌ `structural_coverage` |

### Sau Phase 6.6 (hai lượt)

| Lượt | 1 | 2 | 3 |
|---|---|---|---|
| ⑤ | ❌ `structural_coverage` | ❌ `grounding` | ❌ `structural_coverage` |
| ⑥ | ✅ **served** | ✅ **served** | ✅ **served** |

**Lượt ⑥ — 3/3, và cả ba đúng thứ đề hỏi:**

```
1  9 đối tượng · 5 bước   A B D C S ABCD_polygon S_ABCD_solid SA_line M
   nghĩa vụ point_on_line(SA, M) — served

2  8 đối tượng · 4 bước   … ABCD S.ABCD V_S_ABCD
   nghĩa vụ volume(S.ABCD, V_S_ABCD) → V = 12   ✓ kiểm tay 1/3·3²·4 = 12

3  15 đối tượng · 11 bước
   A B D C S M N P ABCD_poly S_ABCD_solid PMN_plane ABCD_plane d AD_line Q
   Q = (0, 2, 0) · d hướng (-80,80,0) ∝ (-1,1,0)
```

Kiểm tay bài 3: `P(2,0,0) M(2,0,5/2) N(0,2,5/2)` ⇒ pháp tuyến `(PMN) = (-5,-5,0)`;
giao với `z = 0` cho phương `(-1,1,0)`; cắt `AD` (`x = 0`) tại `t = 2` ⇒
**`Q = (0,2,0)`**. **Hệ ra đúng.**

### Lỗi nào đã BIẾN MẤT

| Lỗi | Bằng chứng |
|---|---|
| `assign polygon3 = literal` | mô hình nay dùng `construct_polygon` — thấy ở **3/3** bài lượt ⑥ (`ABCD_polygon`, `ABCD`, `ABCD_poly`) |
| `AD` ↔ `line_AD` / `DA` / `SA_line` | lưới topology khớp; lượt ⑥ có `SA_line` và `AD_line` đều served |
| C₂ vu oan *"chương trình tự mâu thuẫn"* | không xuất hiện lại ở hai lượt sau |
| lời từ chối *"bài thuộc môn khác"* | không xuất hiện lại |

### Lỗi nào CÒN TỒN TẠI

Lượt ⑤, ba bài trượt ở **ba khâu khác nhau**, và không lỗi nào là lỗ hợp đồng:

1. **bài 1** — chương trình khai `M` **rồi dựng vào `M_point`**: một khai báo
   chết. C₁a từ chối đúng (hai ứng viên ⇒ fail-closed). *Lỗi mô hình.*
2. **bài 2** — mô hình gán `initial_value` cho biến chứa **thể tích**, tức viết
   sẵn đáp án. Grounding chặn. *Đây là R0 đang làm việc, không phải lỗi hệ.*
3. **bài 3** — lượt **đọc đề** sinh hợp đồng hỏng: 5 nghĩa vụ, một witness tên
   là `"giao tuyến của (PMN) và (ABCD)"` (một câu tiếng Việt làm tên biến),
   `point_on_line` với container là một ĐIỂM. *Lỗi mô hình, ở tầng analyze.*

---

## 6. Remaining blockers

### ⚠️ Blocker chính — và nó KHÔNG phải lỗi hệ

**Hai lượt liên tiếp, cùng một mã, cùng ba đề: 0/3 rồi 3/3.**

Sáu lượt tổng cộng (bốn trước + hai sau) chưa lượt nào lặp lại lượt trước. Đây
là **B. Model generation instability**, và nó xuất hiện ở **cả ba tầng**:

```
đọc đề       số nghĩa vụ dao động 0 · 1 · 2 · 3 · 5 trên CÙNG một đề
viết chương  khai một biến rồi dựng vào biến khác; gán initial_value cho đáp án
đặt tên      SA_line · line_AD · DA · M_point — mỗi lượt một kiểu
```

### ⚠️ Blocker thứ hai — `nghĩa vụ = []` ở bài 3

Lượt ⑥, bài 3 served với **KHÔNG nghĩa vụ nào**. Nên C₁a/C₁b/C₂ không có gì để
kiểm, và `servable = true` ở đó nghĩa là *"chương trình chạy trọn và mọi thứ nó
dựng đều lên được hình"*, **không** phải *"đáp án đã được đối chiếu"*.

Đáp án đúng — tôi kiểm tay — nhưng **hệ không tự biết** nó đúng. Đó chính là chỗ
luận điểm của đề tài mỏng nhất, và một lượt 3/3 không được phép che nó.

### Phân loại theo đúng ba nhóm đã yêu cầu

| | Nhóm | Trạng thái |
|---|---|---|
| **A** | Contract problem | **ĐÃ XỬ.** Không lỗi nào ở hai lượt sau là lỗ biểu đạt. `construct_polygon` được dùng 3/3; resolver topology khớp mọi biến thể tên. |
| **B** | Model generation instability | **CÒN, và là blocker duy nhất còn lại.** Không vá được bằng thêm primitive hay thêm lưới. |
| **C** | Benchmark limitation | **CÒN.** N = 1 mỗi bài mỗi lượt; ba đề do tôi chọn; `servable` không đồng nghĩa "đã kiểm chứng" khi hợp đồng rỗng. |

---

## 7. Recommendation

### ⚠️ NOT READY cho Phase 7 **theo tiêu chuẩn đã đặt** — nhưng lý do đã đổi

Tiêu chuẩn viết là *"3/3 smoke served"*. Đạt được ở lượt ⑥. Nhưng **một lượt
3/3 sau một lượt 0/3 trên cùng mã không phải một tuyên bố về độ ổn định** — nó
là một mẫu, và mẫu bên cạnh nó nói ngược lại.

**Điều Phase 6.6 đã làm xong**: nhóm A đóng lại. Sáu lượt trước pha này, mỗi lượt
lộ ra một lỗ hợp đồng thật; hai lượt sau, không lỗ nào. Cổng smoke đã hết vai trò
tìm lỗi hợp đồng.

**Điều không nên làm tiếp**: vá thêm. Ba lỗi ở lượt ⑤ đều là mô hình, và mỗi bản
vá nhắm vào chúng sẽ là nới một cổng theo một lỗi cụ thể — đúng thứ `RULES §3c`
gọi là DEEP_HARDENING và đúng thứ Phase 6.6 cấm.

**Đề xuất — chọn một trong hai, và đây là quyết định của người hướng dẫn:**

**(I) Đo độ ổn định TRƯỚC, rồi mới Phase 7.** Chạy k = 5 lượt trên cùng ba đề,
ghi `served` bao nhiêu / k. Chi phí ≈ 90 lượt LLM. Kết quả cho một con số thật
về nhóm B, và con số ấy **thuộc về luận văn**: *"AI sinh được chương trình đúng,
nhưng chỉ x/5 lượt trên cùng một đề"* là một phát hiện, không phải một thất bại.

**(II) Vào Phase 7 và coi độ ổn định là MỘT BIẾN ĐƯỢC ĐO.** Benchmark chạy mỗi
đề nhiều lượt thay vì một. Tốn quota gấp k lần, nhưng nó trả lời đúng câu hỏi mà
sáu lượt vừa rồi đã đặt ra.

**Tôi nghiêng về (II)**, vì (I) là (II) trên một tập ba bài do tôi chọn — cùng
chi phí về bản chất, ít giá trị hơn về bằng chứng.

**Điều KHÔNG nên chọn**: chạy Phase 7 một lượt mỗi đề. Với biên độ vừa đo được,
một lượt duy nhất sẽ cho ra một con số mà lượt sau bác bỏ.

---

## Chi phí pha này

Hai lượt smoke × ba đề ≈ **40 lượt LLM**, `gemini-2.5-flash`, không lượt nào
dùng cache (dọn sạch trước mỗi lượt, `cached=false` trong mọi bản ghi).

Môi trường lúc đo:

```
sha=5e42fa0ea02a cache=45 skill=11/6208fc2a card=7441ed3c
route=serve model=gemini-2.5-flash telemetry=1 reload=0
runtime_doctor --doi-mode serve --doi-model gemini-2.5-flash → PASS
```
