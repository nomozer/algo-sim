# SCORER_ERRATUM #3 — chỉ số ② của MỌI nghĩa vụ QUAN HỆ không mang thông tin

**Ngày**: 2026-08-29 · **Lượt**: `phase7b-official-82917341` ·
**Số lời gọi model lặp lại: 0.** Không artifact thô nào bị sửa.
Bản gốc **không bị xoá**; phần `POST_HOC_SCORER_CORRECTION` ở cuối file ghi
con số chấm lại **cạnh** con số cũ, theo yêu cầu vận hành 2026-08-29.

## 1. Lỗi

`run_geometry_dev_evaluation.cham_oracle` so `oracle_result[kind]` với giá
trị trong `final_memory` theo hai nhánh:

```python
de = mong[kind]
if isinstance(de, bool):     # nhánh QUAN HỆ
    ...
else:                        # nhánh ĐẠI LƯỢNG
    Fraction(str(may)) != Fraction(str(de))
```

`pool.json` lưu quan hệ dưới dạng **CHUỖI** `"true"` (nó sinh từ dòng
`ĐÁP ÁN:` của gói chép, và mọi thứ ở đó là chuỗi). Nên `isinstance(de, bool)`
là **False**, nhánh đại lượng chạy, và `Fraction("true")` ném lỗi ⇒ mọi
nghĩa vụ quan hệ đều ra *"không so được"* hoặc *"máy=None, đề mong 'true'"*.

Quan sát trực tiếp trên artifact chính thức:

```
hp_a03_008-lan1  oracle=False  FAIL: ["parallel: không so được máy=Line3(…)"]
hp_a05_013-lan1  oracle=False  FAIL: ["parallel: máy=None, đề mong 'true'"]
hp_a07_019-lan1  oracle=False  FAIL: ["perpendicular: không so được máy=Plane3(…)"]
```

Cả ba đều `served = True`.

## 2. Phạm vi

Năm nghĩa vụ quan hệ — `parallel` · `perpendicular` · `point_on_line` ·
`point_on_plane` · `coplanar` — phủ **9/14 ô tầng A** của `BANG_O`:
A01 · A02 · A03 · A04 · A05 · A06 · A07 · A08 · A13.

Chỉ 5 ô đo lường (A09 · A10 · A11 · A12 · A14) đi nhánh đại lượng và được
chấm đúng. Đó chính là 5 ô mà lượt chính thức ghi nhận `oracle` có giá trị
dương.

## 3. Vì sao sai từ gốc, không chỉ sai kiểu dữ liệu

Sửa `"true"` → `True` là chưa đủ. So `final_memory[witness]` với một hằng là
**đọc nhầm hợp đồng**: với nghĩa vụ quan hệ, `witness` là **đối tượng thứ
hai** của quan hệ (`perpendicular(container="AC", witness="B'D'")`), không
phải kết quả tính ra. Quan hệ được chứng minh bằng **checker server-owned**
chạy lại tính chất từ trạng thái cuối, quy ước `None` ⇒ thoả.

Phép sửa vì thế định tuyến nghĩa vụ quan hệ sang `GEOMETRY_CHECKERS`, và áp
bí danh hoà giải trước khi gọi — nếu không, checker tra trượt tên hợp đồng
(`B'D'` ≠ `B_prime_D_prime`) và trả *"cặp đối tượng không hợp lệ"*, một lỗi
TRA TÊN sẽ bị đọc thành SAI.

## 4. Cách đọc đúng con số đã công bố

Chỉ số ② của lượt chính thức đã công bố:

```
oracle   6/33 áp dụng · N/A 9 · trượt 27
```

**27 lượt "trượt" ấy gồm phần lớn là lượt KHÔNG CHẤM ĐƯỢC**, không phải lượt
sai. Cách đọc đúng: với 9 ô quan hệ, chỉ số ② của lượt chính thức **không
mang thông tin** — nó không nói mô hình đúng, cũng không nói mô hình sai.

Ba chỉ số còn lại **không** bị ảnh hưởng: ① `served`, ③a `construction_match`,
③b `verification_match` không đi qua `cham_oracle`. `verification_match
32/42` giữ nguyên nghĩa, và nó là chỉ số duy nhất còn nói được về nhóm quan
hệ trong lượt ấy.

## 5. Con số gốc KHÔNG bị thay, con số mới đứng CẠNH nó

Một baseline được chấm lại sau khi người ta đã thấy nó thì không còn là
baseline — nên `SCORE.json` và `PHASE7B_OFFICIAL_RESULT.md` giữ nguyên từng
chữ. Người vận hành đã yêu cầu (2026-08-29) một lượt chấm lại hậu nghiệm từ
artifact thô, công bố **kèm cả hai con số**; nó nằm ở cuối file này dưới nhãn
`POST_HOC_SCORER_CORRECTION` / `NOT_A_BENCHMARK_RERUN`.

## 6. Chỗ này là lần thứ SÁU của cùng một lớp lỗi

C₁a → C₁b → C₂ → `learner_surface` → bộ chấm DEV → bộ chấm pool: **một
thành phần đọc `final_memory` thô thay vì hỏi thành phần chính tắc**. Bốn
lần đầu ở hệ và làm hệ trông tốt hơn thật; hai lần sau ở bộ đo và làm hệ
trông tệ hơn thật.

Phép sửa lần này đóng cả hai vế cho đường pool: hỏi checker, và áp bí danh
trước khi hỏi.

---

# POST_HOC_SCORER_CORRECTION — **NOT_A_BENCHMARK_RERUN**

**0 lời gọi model.** Đọc lại artifact THÔ bất biến của lượt chính thức bằng
bộ chấm đã sửa. Không artifact nào bị ghi đè; `SCORE.json` gốc và
`PHASE7B_OFFICIAL_RESULT.md` giữ nguyên từng chữ.

## Hai con số, cả hai đều phải đọc

```
ORIGINAL_REPORTED_ORACLE (tầng A, 42 lượt)
    PASS  6 · FAIL 27 · N/A  9

CORRECTED_POST_HOC_ORACLE (cùng artifact, bộ chấm đã sửa)
    PASS 16 · FAIL 17 · UNGRADED 3 · N/A 6
```

**Con số gốc không bị xoá.** Nó là thứ đã công bố, và một baseline được sửa
sau khi người ta thấy nó thì không còn là baseline. Con số chấm lại nói về
cùng những lượt chạy ấy, chỉ khác cái thước.

## Mười lượt đổi phán quyết — tất cả đều `False → PASS`

```
hp_a02_004-lan1   hp_a03_008-lan1   hp_a03_008-lan3
hp_a05_013-lan2   hp_a05_013-lan3   hp_a07_019-lan{1,2,3}
hp_a08_020-lan{1,2}
```

Tất cả là nghĩa vụ **quan hệ** (`point_on_plane` · `parallel` ·
`perpendicular`) — đúng nhóm mà `Fraction("true")` làm hỏng. Không lượt nào
đi theo chiều ngược lại: phép sửa **không** biến một lượt đúng thành sai.

## Ba lượt thành `UNGRADED`, và vì sao đó là tiến bộ

Ba lượt đo lường trở thành `UNGRADED` vì **thang tự do**: đề để `a` tự do,
chương trình chọn một thang, và so giá trị tuyệt đối không hợp lệ khi không
suy được thang. Trước đây chúng bị đếm là **sai**.

Phát hiện đi kèm, đo được: **5/5 ô đo lường của pool** (A11×2 · A12 · A14×2)
đều có `a` tự do. Nên chỉ số ② cho `distance`/`volume` ở bản gốc đo *"mô hình
có tình cờ chọn a = 1 không"*, không đo hình học.

## Điều KHÔNG đổi

`served 20/42` · `construction_match 14/23` · `verification_match 32/42` ·
`stability 7/14` · `RUN_COMPLETENESS` · `LOGICAL_CALLS 225/360` ·
`HTTP_CALLS 245/480` · `seal_hash` · `measured_system_hash`. Không chỉ số nào
trong nhóm ấy đi qua `cham_oracle`.

## Kết luận phải giữ nguyên

Con số chấm lại **không** làm `READY_FOR_3D` đổi. Nó sửa một lời khai sai về
mô hình, không sửa mức sẵn sàng của hệ.
