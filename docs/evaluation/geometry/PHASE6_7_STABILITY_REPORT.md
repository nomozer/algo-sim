# PHASE 6.7 — ĐO ĐỘ ỔN ĐỊNH (2026-08-26)

> **Không sửa một dòng code nào của hệ.** Ba đề cố định × 5 lượt độc lập = 15
> lượt, chạy liền một mạch, không vá giữa chừng.
>
> Bản đã đo: `e7ade90` · `CACHE_VERSION 45` · `gemini-2.5-flash` ·
> skill `6208fc2a` · thẻ văn phạm `7441ed3c`. Cây sạch ngoài chính bộ đo.
> Artifact thô: `stability-6.7/` — mỗi lượt một file, kèm `request_contract` và
> `generated_program`.

---

## 1. PASS / k trên từng bài

| Bài | **served** | oracle đạt | obligation_match |
|---|:-:|:-:|:-:|
| 1 · trung điểm | **3/5** | 3/5 | 5/5 |
| 2 · thể tích | **2/5** | 2/5 | 5/5 |
| 3 · thiết diện PMN | **4/5** | 4/5 | **1/5** |
| **Tổng** | **9/15** | 9/15 | 11/15 |

Cả **9/9** lượt `served` đều có `scene3d`, và cả **9/9** đều **qua oracle độc
lập**. Không lượt nào phát ra một mô phỏng SAI.

Độ trễ: 26s – 438s, tổng 1600s cho 15 lượt. Vòng sửa lỗi validator hầu như
không chạy (`so_lan_thu_sinh ∈ {0, 1}`) — chương trình hoặc hợp lệ ngay, hoặc
hỏng ở tầng sau.

### ⚠️ Con số quan trọng nhất KHÔNG phải cột `served`

**Bài 3 — bài KHÓ NHẤT — lại ổn định nhất ở `served` (4/5), nhưng
`obligation_match` chỉ 1/5.** Số nghĩa vụ mà lượt đọc đề khai ra, trên **cùng
một đề, cùng một prompt**:

```
lần 1   0 nghĩa vụ      → served · oracle ✓
lần 2   3 nghĩa vụ      → served · oracle ✓     ← DUY NHẤT khai đúng bộ
lần 3   2 nghĩa vụ      → served · oracle ✓
lần 4   0 nghĩa vụ      → served · oracle ✓
lần 5   4 nghĩa vụ      → TRƯỢT
```

**Hai trong bốn lượt `served` của bài 3 KHÔNG kiểm gì cả** (`nv = 0`): C₁a, C₁b,
C₂ không có nghĩa vụ nào để đối chiếu, nên `servable = true` ở đó nghĩa là
*"chương trình chạy trọn và mọi thứ nó dựng đều lên được hình"* — **không** phải
*"đáp án đã được đối chiếu"*.

Đáp án vẫn đúng — oracle **độc lập của tôi** xác nhận `Q` là trung điểm `AD` ở
cả bốn lượt — nhưng **hệ không tự biết**. Nếu chỉ nhìn cột `served`, bài khó
trông ổn định hơn bài dễ; nhìn thêm một cột thì thấy nó ổn định vì **không bị
kiểm**.

---

## 2. Phân loại từng lượt trượt

Sáu lượt trượt. Phân loại đọc từ `generated_program`, không suy từ mã lỗi.

| Bài | Lần | Khâu | Nhóm | Bằng chứng |
|---|:-:|---|:-:|---|
| 1 | 4 | `structural_coverage` | **A** | chương trình khai **đúng một** biến `point_on_line_M_SA` — không có `SA`, không có `M` |
| 1 | 5 | `grounding` | **A** | 4/5 điểm có `model_assumption`; **riêng `C` để `null`** |
| 2 | 2 | `structural_coverage` | **C** | xem §3 |
| 2 | 3 | `structural_coverage` | **C** | xem §3 |
| 2 | 5 | `execution` | **A** | `construct_point C = arith(B + D)` — tự cộng toạ độ |
| 3 | 5 | `structural_coverage` | **A** | tự thêm `coplanar(PMN, d)` với container là `plane3` |

```
A. Model generation   4/6
B. Contract           0/6      ← KHÔNG lượt nào
C. Validator          2/6
D. Benchmark          0/6
```

**Nhóm B bằng KHÔNG trên 15 lượt.** Đó là xác nhận độc lập cho kết luận Phase
6.6: lỗ biểu đạt hợp đồng đã đóng. `construct_polygon` được dùng tự nhiên —
thấy trong chương trình ở nhiều lượt (`base_ABCD`, `ABCD`).

**Ghi chú về bài 3 lần 5** — mô hình muốn nói *"d nằm trong (PMN)"* và taxonomy
**không có kind nào** cho quan hệ ấy (`line_in_plane` có ở kernel, không có ở
taxonomy nghĩa vụ). Nó với tay lấy `coplanar` và bị kiểm kiểu từ chối.

Vẫn xếp **A**, không phải B, và lý do phải nói rõ: đề **không yêu cầu chứng
minh** `d ⊂ (PMN)` — đó là hệ quả hiển nhiên của việc `d` là giao tuyến. Mô hình
**tự thêm** một nghĩa vụ đề không hỏi. Đường đúng (không khai nghĩa vụ ấy) vẫn
mở, nên không chứng minh được hợp đồng đã ép nó trượt. Điều kiện *"B chỉ ghi
nhận nếu chứng minh được"* không thoả.

---

## 3. 🔴 LỖI HỆ THỐNG — validator so sai tên (nhóm C, 2/6)

Đây là phát hiện nặng nhất của pha này, và nó **không lộ ra** ở bất kỳ lượt
smoke nào trước đó.

Bài 2, lần 2 và lần 3, hợp đồng khai `volume(container="S.ABCD",
witness="V_S_ABCD")`. Chương trình **CÓ TÍNH** thể tích:

```json
lần 2   {"kind":"construct_solid","target_var":"S_ABCD_solid", …}
        {"kind":"assign","target_var":"V_S_ABCD",
         "expr":{"kind":"measure","quantity":"volume","of":"S_ABCD_solid"}}

lần 3   {"kind":"construct_solid","target_var":"S_ABCD", …}
        {"kind":"assign","target_var":"V_S_ABCD",
         "expr":{"kind":"measure","quantity":"volume","of":"S_ABCD"}}
```

Cổng vẫn từ chối, và lời từ chối **nói sai sự thật**:

> `volume(S.ABCD): witness 'V_S_ABCD' không dẫn xuất từ 'S.ABCD' — chương trình
> khai đáp án chứ không tính nó`

**Chương trình không hề khai đáp án. Nó gọi `measure`.**

Nguyên nhân, ở `coverage_gate.check_structural_coverage`:

```python
if ten_hh and con not in declared:
    ...  con = thay          # ← `S.ABCD` đã hoà giải thành `S_ABCD_solid`
...
elif ob.container not in goc:  # ← nhưng ở ĐÂY lại dùng ob.container
```

Phép kiểm dẫn xuất tra **tên HỢP ĐỒNG** trong một bao đóng chứa **tên CHƯƠNG
TRÌNH**. Lưới hoà giải đã làm đúng việc của nó và kết quả bị vứt đi ở dòng kế.

Đây là **lần thứ ba** cùng một lớp lỗi trong dự án — lưới áp ở chỗ này mà không
áp ở chỗ kia (trước đó: C₁a có mà C₂ không; `_semantic_shadow` có mà cổng phạm vi
đường module không). Lần này nó nằm **ngay trong cùng một hàm**, cách nhau vài
chục dòng.

**Vì sao nó có tính HỆ THỐNG chứ không ngẫu nhiên**: nó nổ **mỗi khi** mô hình
đặt tên khối khác tên trong hợp đồng — tức mỗi khi lưới hoà giải phải ra tay. Hai
lượt `served` của bài 2 (lần 1, lần 4) là hai lượt mô hình tình cờ dùng đúng tên
`S.ABCD`.

⚠️ **KHÔNG SỬA trong pha này** — Phase 6.7 cấm sửa lỗi của từng lượt fail, và
tôi giữ đúng điều đó. Ghi lại kèm bằng chứng để pha sau xử.

**Chiếu (nói rõ là CHIẾU, không phải đo)**: nếu chỉ lỗi này được sửa, bài 2 lẽ ra
**4/5** thay vì 2/5, và tổng lẽ ra **11/15**. Con số ấy chưa được đo và không
được dùng thay số thật.

---

## 4. Lỗi LẶP LẠI vs lỗi NGẪU NHIÊN

### Lặp lại (cùng nguyên nhân, ≥2 lượt)

| Lỗi | Số lượt | Nhóm |
|---|:-:|:-:|
| validator so tên hợp đồng với bao đóng tên chương trình | 2 | C |
| lượt đọc đề khai **thiếu hoặc thừa** nghĩa vụ (bài 3: 0·3·2·0·4) | 4/5 | A |

### Ngẫu nhiên (một lần, không lặp)

| Lỗi | Bài |
|---|---|
| khai đúng một biến đặt tên theo nghĩa vụ, không dựng gì | 1 |
| bỏ sót `model_assumption` cho **đúng một** điểm trong năm | 1 |
| tự cộng hai điểm bằng `arith` để tính toạ độ | 2 |
| tự thêm một nghĩa vụ đề không hỏi, sai kiểu container | 3 |

Bốn lỗi ngẫu nhiên này **không chung một nguyên nhân kỹ thuật**. Chúng chung một
tính chất: mỗi lần mô hình đi chệch một luật khác nhau, và luật nào cũng đã có
trong prompt hoặc trong thẻ văn phạm.

Đó là chữ ký của **B. Model generation instability** — không phải của một lỗ hệ
còn sót.

### Lỗi HỆ THỐNG (không phải "lặp lại nhiều lần" mà là "sẽ luôn xảy ra")

1. **Validator so sai tên** (§3) — tất định: cứ lệch tên khối là nổ.
2. **`served` không đồng nghĩa `đã kiểm chứng`** — 2/9 lượt served có `nv = 0`.
   Đây không phải bug; đây là **giới hạn của chỉ số `served`**, và mọi báo cáo
   dùng `served` mà không kèm `obligation_match` sẽ nói quá.

---

## 5. Recommendation

# NEED_MORE_ANALYSIS

**Không phải vì 9/15 quá thấp.** Mà vì hai điều dưới đây làm cho *bất kỳ* con số
Phase 7 nào đo bây giờ cũng sẽ phải đo lại.

**① Có một lỗi validator đã chứng minh được, chưa sửa.** Nó bóp méo số theo
hướng **thấp hơn thực tế**, và nó đổ cho mô hình (*"khai đáp án chứ không tính
nó"*) đúng cái lỗi mô hình không phạm. Đo năng lực AI bằng một thước có lỗi đã
biết thì con số ấy không dùng được, và tệ hơn: nó **vu oan** ở đúng chỗ luận văn
đang muốn kết luận về AI.

**② `served` một mình không phải chỉ số đúng để benchmark.** Bài khó nhất đạt
4/5 `served` nhưng 1/5 `obligation_match`, và 2 lượt served **không kiểm gì**.
Một Phase 7 báo cáo `served = x/n` sẽ nói quá về năng lực hệ. Chỉ số phải là
**cặp** — `served` **và** `obligation_match` — và không được gộp.

### Việc cần làm trước Phase 7, theo thứ tự

1. **Sửa lỗi validator §3** (một dòng: dùng tên đã hoà giải ở phép kiểm dẫn
   xuất) + test hồi quy dựng đúng hiện trường lần 2/lần 3. Đây là nhóm C, không
   phải nới cổng theo một lỗi LLM.
2. **Đo lại 15 lượt** trên cùng ba đề, cùng bộ đo này. So với bảng ở §1 để biết
   lỗi ấy đã ăn bao nhiêu — và đó là một phép đo, không phải một phép chiếu.
3. **Chốt chỉ số của Phase 7 là một CẶP** (`served`, `obligation_match`), và
   benchmark chạy **k lượt mỗi đề** chứ không một lượt.

### Điều KHÔNG nên làm

Không vá bốn lỗi ngẫu nhiên ở §4. Chúng thuộc nhóm A, mỗi cái một luật khác
nhau, và vá theo chúng là nới cổng theo lỗi cụ thể — đúng thứ `RULES §3c` gọi
DEEP_HARDENING. Độ ổn định của mô hình là **thứ cần ĐO trong Phase 7**, không
phải thứ cần triệt tiêu trước Phase 7.

---

## 6. Chi phí

15 lượt × ~6 lượt LLM ≈ **90 lượt**, `gemini-2.5-flash`. Không lượt nào chạm
cache: bộ đo gọi thẳng `run_pipeline`, đường không đi qua bảng cache.
