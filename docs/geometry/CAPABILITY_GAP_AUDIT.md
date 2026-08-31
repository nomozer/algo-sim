# SOÁT KHOẢNG TRỐNG NĂNG LỰC — hình học không gian THPT

> **Bản soát TĨNH, 0 lời gọi LLM.** Mọi ô trong bảng dưới đây do
> `backend/scripts/audit_geometry_capability.py` chạy ra ở HEAD, không suy từ
> tên hàm. Chạy lại: `PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe
> scripts/audit_geometry_capability.py`.
>
> Bản này **thay phần nhật ký đo** của `GEOMETRY_CURRICULUM_COVERAGE.md §5`
> (đo trên `8b4025e`). Bảng chủ đề §2–§4 của file kia vẫn còn hiệu lực.

---

## 0. Luật đọc bảng

Một năng lực chỉ là **SUPPORTED** khi đi trọn **bốn** chặng:

```
biểu đạt được (IR) → thẩm định qua (validator) → CHẠY RA SỐ (kernel)
                   → kiểm chứng tất định được (checker server-owned)
```

Kernel có hàm mà **cầu nối IR** không nối thì năng lực ấy **không tồn tại với
hệ**. Đây không phải chuyện chữ nghĩa: `measure.distance_sq_skew_lines` nằm
sẵn trong kho, và `hp_b01_032` vẫn chết ở V3 với *"cặp đối tượng không hợp lệ
cho khoảng cách"* — hai lượt liền. **Cầu nối ấy đã nối ngày 2026-08-30**; xem
§4b, và lưu ý ba ô mới chỉ lên **PARTIAL**, không lên SUPPORTED.

---

## 1. Cầu nối IR — đo ở HEAD

**19/23** năng lực đi trọn tới một con số (2026-08-30; trước đó 15/22).

| Năng lực | Cầu nối | Bằng chứng |
|---|:-:|---|
| khoảng cách điểm–điểm | ✅ | `1` |
| khoảng cách điểm–đường | ✅ | `1` |
| khoảng cách điểm–mặt | ✅ | `1` |
| khoảng cách đường–đường CHÉO (hữu tỉ) | ✅ | `2` |
| khoảng cách đường–đường CHÉO (**vô tỉ**) | ✅ | `1` — trả `a·√b` chính xác từ 2026-08-31 |
| khoảng cách đường–đường ∥ | ✅ | `1` |
| khoảng cách đường–mặt (∥) | ✅ | `1` |
| khoảng cách mặt–mặt (∥) | ✅ | `1` |
| góc đường–đường (cos²) | ✅ | `0` |
| góc đường–mặt (sin²) | ✅ | `1/2` |
| góc mặt–mặt theo pháp tuyến | ✅ | `1` |
| thể tích khối | ✅ | `1/6` |
| giao đường × mặt | ✅ | `Vec3(0,1,0)` |
| giao mặt × mặt | ✅ | `Line3(…)` |
| giao đường × đường | ✅ | `Vec3(0,0,0)` |
| trung điểm · chia đoạn | ✅ | `Vec3(1/2,0,0)` · `Vec3(2/3,0,0)` |
| chiếu vuông góc lên mặt / đường | ✅ | `Vec3(0,0,0)` |
| **chiếu SONG SONG theo phương** | ❌ | `biểu thức hình học lạ` |
| **cộng/trừ vectơ · tích vô hướng** | ❌ | `biểu thức hình học lạ` |
| **khoảng cách VÔ TỈ (√2)** | ✅ | `a·√b` chính xác — `geometry/radical.py` |

Checker tất định: **8/8** kind của `GEOMETRY_CHECKERS` đều có
(`point_on_line` · `point_on_plane` · `parallel` · `perpendicular` ·
`coplanar` · `distance` · `angle` · `volume`).

### 1b. Chỗ dễ đọc nhầm nhất

**~~`distance` chỉ trả lời khi kết quả HỮU TỈ.~~ — GIỚI HẠN NÀY ĐÃ GỠ 2026-08-31.**

Bản trước: vô tỉ thì `_do` ném `GEOMETRY_IRRATIONAL_RESULT` thay vì làm tròn.
Quyết định **đúng** — `√2` lặng lẽ thành `1.414…` là sai số float quay lại qua
cửa sau — nhưng hệ quả về phủ thì lớn: đáp án của đề thật thường có dạng
`a√3/2`, `a√6/3`, nên năm ô khoảng cách đều phải khai PARTIAL.

Chẩn đoán ấy sai chỗ, và chỗ sai đáng ghi lại: **vấn đề chưa bao giờ là tính
được hay không** — kernel đã có `d²` chính xác từ đầu. Nó là BIỂU DIỄN. Miền số
`a·√b` (`app/simulation/geometry/radical.py`) viết được mọi `√(p/q)` với
`p/q ≥ 0`, nên `sqrt_rational` **không có nhánh thất bại** và lời từ chối biến
mất khỏi đường khoảng cách.

Điều KHÔNG đổi: vẫn không làm tròn, vẫn không float trên đường đúng đắn. Điều
ĐỔI: hệ thôi từ chối. Hai chuyện khác nhau, và bản cũ gộp chúng làm một.

Ranh giới fail-closed không mất, nó **dời** tới chỗ thật sự ngoài miền: tổng hai
căn khác căn thức (`√2 + √3`) và căn thức vượt `MAX_RADICAND`.

**Góc mặt–mặt ≠ góc NHỊ DIỆN.** `cos_sq_between_planes` đo góc giữa hai *pháp
tuyến*, tức góc giữa hai mặt phẳng (0°–90°). Góc nhị diện của một cạnh cụ thể
có **miền** và có thể tù. Hai khái niệm khác nhau; hệ chỉ có cái thứ nhất.

---

## 2. Bảng năng lực

| Năng lực | Q.trọng | IR | Thẩm định | Chạy | Kiểm | Vẽ | TRẠNG THÁI | Khoảng trống |
|---|:-:|:-:|:-:|:-:|:-:|:-:|---|---|
| giao tuyến / giao điểm | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| điểm ∈ đường / mặt | 4 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| ∥ đường–đường | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| ∥ đường–mặt | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| ∥ mặt–mặt | 4 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| ⊥ đường–đường | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| ⊥ đường–mặt | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| ⊥ mặt–mặt | 4 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| góc đường–đường | 4 | ✅ | ✅ | ✅ | ✅ | ⚠️ | **SUPPORTED** | trả `cos²`, không có cung góc trên cảnh |
| góc đường–mặt | 4 | ✅ | ✅ | ✅ | ✅ | ⚠️ | **SUPPORTED** | trả `sin²` |
| đồng phẳng | 3 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | — |
| thể tích đa diện | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | chỉ khối LỒI |
| thiết diện | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **PARTIAL** | checker riêng `section_matches` (2026-08-30); còn: mặt phẳng TRÙNG một mặt của khối, và chỉ khối LỒI |
| k/c điểm–mặt | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | vô tỉ ⇒ căn thức chính xác (2026-08-31) |
| k/c điểm–đường | 4 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | vô tỉ ⇒ căn thức chính xác (2026-08-31) |
| góc NHỊ DIỆN có miền | 4 | ❌ | — | — | — | — | **UNSUPPORTED** | chỉ có góc giữa hai pháp tuyến |
| k/c đường–đường (chéo · ∥ · cắt) | 5 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | cầu nối 2026-08-30 + miền căn thức 2026-08-31 |
| k/c đường–mặt | 3 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | miền số đã mở (2026-08-31) |
| k/c mặt–mặt | 3 | ✅ | ✅ | ✅ | ✅ | ✅ | **SUPPORTED** | miền số đã mở (2026-08-31) |
| phép toán VECTƠ | 4 | ❌ | — | — | — | — | **UNSUPPORTED** | `vector3` là kiểu, không có biểu thức |
| Oxyz (toạ độ hoá) | 5 | ❌ | — | — | — | — | **UNSUPPORTED** | Toán 12 — cả một chương |
| phép chiếu song song | 3 | ❌ | — | — | — | — | **UNSUPPORTED** | chỉ có chiếu vuông góc |
| căn thức chính xác | 5 | ❌ | — | — | — | — | **UNSUPPORTED** | nền số là `Fraction` |
| mặt cầu · nón · trụ | 4 | ❌ | — | — | — | — | **DEFERRED** | đổi nền toán từ đa diện sang mặt cong |

---

## 3. P0 — bất biến phải đóng TRƯỚC khi mở rộng

### 3a. `SCALE_CONSISTENCY_INVARIANT` — đã quan sát được, không phải giả định

Hợp đồng chuẩn hoá thang tất định (`AB = a → 1`, `SA = 4a/5 → 4/5`), nhưng
**hiện thực toạ độ** đi qua kênh tự do hệ trục (`model_assumption`) thì không
ghim về mục dữ kiện nào — nên **không cổng nào đối chiếu được thang nó chọn**.

Bằng chứng, `wave6-canary-b/w3-thang-lan1`:

```
A(−16,0,0)  B(9,0,0)  S(0,0,12)   ⇒ AB = 25, SA = 20 = 4·25/5, d = 12
hợp đồng đã chốt: ab_length = 1, sa_length = 4/5
```

Hình **đúng**, thang **sai**. Học sinh đọc `12` cho bài có đáp án `12a/25`.
Ở wave5 cùng ca này **bị bắt** — vì lượt ấy mô hình có ghim về `ab_length`.
⇒ Phép bắt đang phụ thuộc **trí nhớ của mô hình**, không phải bất biến.

**Thiết kế: `NormalizedSourceInvariantGate`.**

| | |
|---|---|
| **Đặt ở đâu** | `route._sau_grounding`, **sau C₂**, trước biên dịch envelope |
| **Vì sao chỗ đó** | Cần trạng thái cuối (phải sau thực thi), và phải chặn trước khi phục vụ. C₂ hỏi *"chương trình có thoả NGHĨA VỤ nó khai không"*; gate này hỏi *"nó có thoả DỮ KIỆN đề cho không"* — hai câu khác nhau, nên là hai cổng |
| **Dùng lại thẩm quyền nào** | `geometry.measure.distance_sq` cho độ dài · `resolved_names` (C₁a) cho tên · `Fraction` cho phép so. **Không** viết checker toán học thứ hai |
| **Đầu vào** | `contract.input_facts` có `scale_symbol` — tức mục đã được chuẩn hoá, nên giá trị mong đợi là một số hữu tỉ CHÍNH XÁC |
| **Suy toán hạng** | `fact_id` → đoạn thẳng, cùng quy ước `_MAU_DOAN` mà bộ chấm DEV đã dùng (`ab_length` → `AB`) |
| **Không phụ thuộc provenance** | Gate chạy **bất kể** mô hình có gắn `source_fact_id` hay không — đó là toàn bộ điểm của nó. Provenance chỉ dùng để **giải thích** vi phạm |
| **Vi phạm** | fail-closed, mã riêng `NORMALIZED_SOURCE_VIOLATED`, chi tiết `AB: đề cho 1, hình dựng 25` |
| **Không kiểm được** | `fact_id` không suy ra đoạn ⇒ **bỏ qua**, không bác. Fail-closed chỉ ở chỗ có phán quyết thật |

**Rủi ro phải khai:** quy ước `fact_id → đoạn thẳng` là **suy từ tên**, thứ mà
phần còn lại của kho cố tránh. Nó chấp nhận được ở đây vì sai theo hướng *bỏ
sót* (không suy ra được thì không kiểm), không sai theo hướng *kết tội oan*.
Bản chặt hơn cần `InputFact` mang toán hạng có cấu trúc — một thay đổi hợp
đồng, nên để sau.

### 3b. `SAFE_TECHNICAL_DEBT`

`BRANCH_UNDEFINED_OBJECT` / `RUNTIME_NONE_OPERAND_REACHABLE = YES` — một điểm
chỉ dựng trong nhánh **không chạy** vẫn lọt xuống kernel dưới dạng `None`
(`ir_static_check` fail-open trong nhánh lồng, có chủ đích, để không từ chối
oan). Kernel **vẫn fail-closed** ở đó ⇒ kết cục AN TOÀN, chỉ bắt muộn một tầng
và mô hình mất cơ hội sửa. Khoá bởi
`test_GIOI_HAN_nhanh_khong_chay_van_lot`. **Không chặn 3D.**

---

## 4. Xếp hạng mở rộng

`GT` giá trị chương trình · `KT` chi phí kiến trúc · `3D` giá trị tương tác ·
`RR` rủi ro phụ thuộc — **1–5, thang thấp là tốt cho KT/RR**.

| # | Năng lực | GT | KT | 3D | RR | Nhận xét |
|---|---|:-:|:-:|:-:|:-:|---|
| ~~1~~ | ~~k/c đường–đường chéo · đường–mặt · mặt–mặt~~ | 5 | 1 | 3 | 1 | **ĐÃ LÀM 2026-08-30** — xem §7 |
| 2 | **căn thức chính xác** (`√` hữu tỉ hoá) | 5 | 4 | 2 | 3 | mở phần lớn đề khoảng cách/độ dài; đụng cách khai đáp án và oracle |
| 3 | phép toán vectơ ở tầng biểu thức | 4 | 2 | 3 | 2 | không đụng kernel; mở trọn chủ đề vectơ |
| 4 | góc nhị diện có miền | 4 | 3 | 4 | 2 | cần khái niệm nửa-mặt-phẳng ở kernel |
| ~~5~~ | ~~thiết diện: checker riêng~~ | 4 | 2 | 5 | 2 | **ĐÃ LÀM 2026-08-30** — xem §4c. VẪN PARTIAL, không lên SUPPORTED |
| 6 | Oxyz | 5 | 5 | 2 | 4 | cả một chương Toán 12; gần như một miền thứ hai |
| 7 | chiếu song song | 3 | 3 | 3 | 2 | chủ đề *hình biểu diễn* |
| 8 | mặt cầu · nón · trụ | 4 | **5** | 3 | **5** | đổi nền toán từ đa diện hữu tỉ sang mặt cong |

---

## 4b. Đã làm: ba cặp khoảng cách (2026-08-30)

Đo lại bằng `scripts/audit_geometry_capability.py`, không suy từ tên hàm:

```
✅ khoảng cách đường–đường CHÉO (hữu tỉ)   2
❌ khoảng cách đường–đường CHÉO (VÔ TỈ)    GEOMETRY_IRRATIONAL_RESULT
✅ khoảng cách đường–đường SONG SONG       1
✅ khoảng cách đường–mặt (∥)               1
✅ khoảng cách mặt–mặt (∥)                 1
```

**Không ô nào lên SUPPORTED trọn**, và lý do là một giới hạn đã khai chứ không
phải một bug: nền số là `Fraction`, nên một khoảng cách như `a√3/2` **không
biểu diễn được** và hệ từ chối thay vì trả `0.866…`. Ba ô này vì thế là
**PARTIAL — miền hữu tỉ**.

Hệ quả phải nói thẳng: đề thi thật rất hay cho khoảng cách vô tỉ, nên "nối
được ba cặp" **không** đồng nghĩa với "làm được các bài khoảng cách trong sách
giáo khoa". Muốn thế thì phải làm hạng mục #2 của bảng trên — **căn thức chính
xác** — và đó là một wave riêng.

Ba trường hợp suy biến đều trả 0 chứ không ném, vì chúng có kết luận hình học
đúng: hai đường **cắt** nhau · đường **nằm trong** mặt · hai mặt **trùng** nhau.
`distance_sq_lines` tự phân ba nhánh (cắt · song song · chéo) nên tầng gọi
không phải kết luận trước khi tính.

---

## 4c. Đã làm: thiết diện thành kết quả hạng nhất (2026-08-30)

Sáu điều kiện SUPPORTED của §15 chỉ thị đều đạt: biểu đạt được · thẩm định qua ·
chạy ra đa giác · **có checker riêng** · giữ thứ tự chu trình · dùng được trong
Scene3D (chọn · cô lập · soi · phát lại). Nhưng ô vẫn là **PARTIAL**, vì hai
giới hạn còn nguyên và cả hai đều là *loại thiết diện chưa xử lý*, không phải
chuyện đẹp xấu:

| Giới hạn | Hành vi hiện tại |
|---|---|
| mặt phẳng cắt **TRÙNG một mặt** của khối | `CONTAINED_INFINITE_INTERSECTION` — về toán, thiết diện khi ấy *là chính mặt ấy*; hệ chưa trả ra |
| khối **KHÔNG LỒI** | ngoài phạm vi từ đầu (thiết diện có thể gồm nhiều mảnh rời) |

**Checker mới mạnh hơn `coplanar` ở đâu — đo được, không phải lời khai.**
`coplanar` trên một thiết diện **gần như luôn xanh**: mọi đỉnh của nó sinh ra từ
giao với đúng MỘT mặt phẳng, nên chúng đồng phẳng theo định nghĩa. Ca
`test_O_DONG_PHANG_DUNG_nhung_DA_GIAC_SAI_thi_FAIL` đưa cùng một dữ liệu qua hai
checker: `coplanar` → ĐƯỢC, `section_matches` → KHÔNG. Không có ca ấy thì câu
"checker mới mạnh hơn" không kiểm được.

**Bốn ca suy biến nay có bốn mã**, vì kernel phân biệt được: không chạm ·
chạm một đỉnh · chạm một cạnh · chứa trọn một mặt. Bản cũ gộp hai ca đầu vào
cùng một mã VÀ cùng một câu *"toàn bộ khối nằm về một phía"* — câu ấy sai cho ca
chạm đỉnh.

⚠️ **Khoảng trống ĐO LƯỜNG, khác khoảng trống năng lực.** Ô `A13` của bảng
held-out **đã niêm phong** vẫn gắn `coplanar`. Không gắn lại: sửa dụng cụ đo sau
khi niêm phong là đúng thứ con dấu tồn tại để ngăn. Nên trên held-out, thiết diện
vẫn được chấm bằng phép kiểm yếu — khai ở
`tests/geometry/test_wave1_oracle_connectivity.py::KHONG_CO_O_DO`.

---

## 5. Sẵn sàng cho 3D

**Hai loại thao tác phải tách bạch**, và ranh giới này là R0 áp cho tương tác:

| VIEW INTERACTION — KHÔNG đổi `GeometryState` | GEOMETRY INTERACTION — ĐỔI state |
|---|---|
| select / inspect · hide / show · isolate · explode / collapse · dependency highlight · step playback | constrained drag |
| chạy thuần ở renderer, không qua kernel | **phải** đi qua kernel + mọi cổng, sinh state mới |

Sáu thao tác cột trái **không cần năng lực hình học mới nào** — chúng cần
dữ liệu cảnh. `Scene3D` hiện đã có:

```
id · label · type · render · origin(free|derived) · producer · depends
+ events(timeline) + free_objects
```

`producer` + `depends` + `free_objects` là đủ cho **dependency highlight**,
**step playback** và **tính hợp lệ của kéo** — ba thứ khó nhất, và chúng đã có.

**Còn thiếu bốn trường**, đều là dữ liệu chứ không phải toán:

| Trường | Dùng cho | Ghi chú |
|---|---|---|
| `parent` | isolate · explode | cạnh/mặt thuộc khối nào |
| `display_group` | isolate · hide theo nhóm | "đáy", "mặt bên", "thiết diện" |
| `visual_transform` | explode / collapse | thuần trình bày, KHÔNG vào state |
| `source` | inspect ("dữ kiện nào sinh ra vật này") | trỏ `fact_id`; `origin` hiện chỉ có `free`/`derived` |

**Constrained drag** là thao tác duy nhất cần hạ tầng mới: kéo một điểm tự do
⇒ chạy lại chương trình ⇒ qua lại toàn bộ cổng. `free_objects` đã trả lời
*"kéo cái gì thì hợp lệ"*; chưa có là vòng chạy lại và ngân sách của nó.

---

## 6. Điều bản soát này KHÔNG nói

- **Không** nói hệ phủ bao nhiêu phần trăm **đề thi**. Nó đếm *chủ đề*, và chưa
  ai đo tần suất mỗi chủ đề trong đề thật.
- **Không** nói AI sinh đúng bao nhiêu. Đó là hai trục độc lập; số của trục kia
  nằm ở `PHASE7B_OFFICIAL_RESULT.md` và các lượt xác nhận.
- **Không** được đọc thành *"hệ làm được hình học không gian THPT"*. Câu đúng:
  **12/24 chủ đề khảo sát ở mức SUPPORTED, 6 PARTIAL, 5 UNSUPPORTED, 1 DEFERRED**
  — trên đa diện lồi, số hữu tỉ, không mặt cong, không Oxyz.
  (2026-08-30: ba ô khoảng cách rời UNSUPPORTED sang PARTIAL, KHÔNG sang
  SUPPORTED — miền hữu tỉ là giới hạn còn nguyên.)
