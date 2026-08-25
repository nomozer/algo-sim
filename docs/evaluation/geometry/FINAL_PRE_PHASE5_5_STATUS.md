# FINAL PRE-PHASE 5.5 STATUS

Wave 3 + Wave 3.5 đã đóng. Không gọi API, không chạy Phase 5.5, không chạy
`vitest`, không đụng dataset · oracle · prompt.

---

## Trạng thái

| | |
|---|---|
| HEAD | `f4d686e` · nhánh `main` |
| working_tree | **CLEAN** — 0 mục, toàn kho **và** hệ được đo |
| freeze | **PASS** (exit 0) |
| candidate | `343af5c` · `cay_lam_viec_sach = true` |
| `measured_system_hash` | `dccf1934e4db27b0` · 141 file |
| pytest | **2497 passed** · 18 skipped · **0 failed** |
| geometry tests | **379 passed** |
| `CACHE_VERSION` | **40** |

Hai commit của wave:

```
343af5c  feat(geometry-eval): close wave3 grounding observability
f4d686e  eval: đóng băng candidate sau Wave 3 + 3.5
```

### `measured_system_hash` đổi — và đổi ĐÚNG phạm vi

`24e80b8f → dccf1934`, số file **không đổi** (141). Nguồn: đúng bốn file, cả bốn
là PRODUCT của wave này và đều nằm trong `MEASURED_SYSTEM_PATHS`.

```
request_contract.py  +52   fact_noi_long + _chuan_hoa_id
grounding_gate.py    +59   hạ cấp trích dẫn hỏng + unresolved_citations
coverage_gate.py     +25   C₁a details kèm cả hai phía
route.py             +41   quan trắc grounding + details tầng execution
```

Taxonomy · primitive set · schema · DEV fingerprint **không đổi** — wave này
không chạm **hợp đồng**, chỉ chạm cách hợp đồng được **kiểm** và được **kể lại**.

---

## Security boundary

### Assumption boundary

Kênh `model_assumption` giữ **ba khoá độc lập**, và Wave 3 nới grounding mà
không mở khoá nào:

| Khoá | Kiểm |
|---|---|
| chỉ `point3` / `vector3` | 10 kiểu khác đều bị chặn, tham số hoá |
| **không bao giờ** là witness | quét **19/19** nghĩa vụ trong taxonomy |
| phải có lý do viết ra | 3 dạng rỗng/khoảng trắng |

Ba **lối vòng** mà chính Wave 3 mở ra cũng đã bịt: witness kèm `source_fact_id`,
witness kèm giả thiết, và cả ba cùng lúc.

### Grounding boundary

| Ca âm | Kết quả |
|---|---|
| `float "2/3"` + giả thiết | `MODEL_ASSUMPTION_TYPE_NOT_ALLOWED` |
| `point3` + `source_fact_id`, **không** giả thiết | `INPUT_NOT_GROUNDED` |
| im lặng bịa toạ độ | `INPUT_NOT_GROUNDED` — kênh vẫn OPT-IN |
| ghim **đúng** mục mà khai **sai** số | `INPUT_NOT_GROUNDED` |
| trích dẫn khớp theo **giá trị** (`"2/3"`) | `INPUT_NOT_GROUNDED` |

Nới đúng nghĩa là **mọi ca âm cũ vẫn âm** — đó là điều đã kiểm, không phải điều
đã tin.

### No fuzzy matching

Khớp id chỉ có **hai bậc tất định**: `exact`, rồi `chuan_hoa` (bỏ dấu · thường
hoá · gộp `-_ `). Không `semantic_type`, không entity/attribute, không embedding.

Cưỡng chế ở **tầng import**, không chỉ tầng hành vi: `request_contract.py` bị
cấm import `difflib` · `rapidfuzz` · `fuzzywuzzy` · `Levenshtein` · `numpy` ·
`sklearn` · `sentence_transformers` · `openai` · `torch`. Test hành vi chỉ bắt
được ca ta nghĩ ra; cấm ở tầng import bắt cả thứ **chưa ai viết**.

Lý do gốc: cả hai phía của một phép khớp ngữ nghĩa đều do **cùng một model** đặt
tên. Cho nó khớp mờ là để model tự chứng minh chính nó.

Và một tách bạch được khoá riêng: `_chuan_hoa_id("2/3") == _chuan_hoa_id("23")`
nhưng `norm_value("2/3") != norm_value("23")`. Chuẩn hoá là phép của **định
danh**; đem sang so **giá trị** thì hai số khác nhau thành một.

---

## Known limitation

**① C₁a chưa sửa — cố ý.** Bằng chứng cho *"lệch tên witness"* là **suy từ dấu
vết**: artifact lượt 2 không lưu `RequestContract`, nên tên witness thật là ẩn
số, và ít nhất ba nguyên nhân khác nhau cùng khớp dấu vết ấy. Thiết kế một bộ
khớp dựa trên suy đoán — mà lại là bộ khớp **làm yếu một cổng an toàn** — là thứ
tự sai: đoán → nới cổng → mất khả năng phát hiện. Wave này làm **phần đo**; C₁a
nay phát ra cả hai phía vào `details`, nên Phase 5.5 sẽ **đọc** được nguyên nhân
thay vì để suy.

**② `geo_10` chưa sửa — cố ý.** Mô hình bọc thừa `{"kind":"literal","value":…}`
quanh `through`/`vertices`. Vá được bằng một `BeforeValidator`, nhưng đó là nới
hợp đồng dựa trên **một** quan sát — chế độ hỏng `RULES §3c` gọi tên. Một lần là
giai thoại, hai lần là lớp lỗi.

**③ `B` (servable) chưa đo được.** Tập nguyên thuỷ thị giác **không có nguyên
thuỷ 3D nào**, nên `solid` đổi giá trị trong lượt chạy là không bày được. Việc
của wave renderer.

**④ Chưa chứng minh Wave 3 sẽ nâng điểm 5.5.** Đo offline trên IR thật cho
`grounding 0/6 → 3/6`, nhưng với **hợp đồng rỗng** — ca xấu nhất. Hợp đồng thật
sẽ khác, cả hai chiều. Ba ca giữ lại đều đúng, trong đó `geo_05` là mô hình khai
thẳng `perpendicular = True`.

---

## READY_FOR_PHASE5_5 = **YES**

Sáu cổng đều xanh:

```
repository   CLEAN (0 dirty)        freeze      PASS · dccf1934 · 141 file
candidate    cay_lam_viec_sach TRUE regression  2497 passed · 0 failed
dataset      10/10 · 8/8 nghĩa vụ   prompt      12 test rò rỉ PASS
runner       12/12 trường + request_contract + failure_details + do_tre
```

Bất biến Tin học: **24 target · 19 obligation (11+8) · 18 checker** — không đổi.

### Trước khi chạy

⚠️ **Không chạy `vitest` xen giữa.** Ba trong năm artifact bằng chứng đổi sau
mọi lượt chạy chỉ vì `generatedAt` (đo được ở `8c0e34a`), nên cây sạch là trạng
thái **nhất thời** và dấu của candidate sẽ hết hiệu lực.

Phase 5.5 sẽ đo: `G1` · `G2` · `A` · `O` · `obligation_match`.
**Không** đo: `B`, renderer, tương tác 3D — nên dù kết quả thế nào, không được
kết luận *"AI sinh mô phỏng 3D"*.

**Chờ duyệt ngân sách API.**
