# HỢP ĐỒNG CHỈ SỐ CHO PHASE 7 — chốt trước, không sửa sau khi thấy số

> Chốt ở Phase 6.8, **trước** khi tiêu call đầu tiên của benchmark. Đổi định
> nghĩa một chỉ số sau khi đã thấy kết quả là chọn thước theo điểm — nên mọi
> thay đổi sau mốc này phải nói ra trong báo cáo, kèm số cũ.

---

## 1. Năm chỉ số, và mỗi cái trả lời một câu hỏi KHÁC NHAU

| | Chỉ số | Câu hỏi nó trả lời | Đơn vị |
|---|---|---|---|
| ① | `served` | Hệ có phát ra một mô phỏng không? | `x/k` mỗi đề |
| ② | `oracle` | Mô phỏng ấy có **đúng** không? | `x/k` mỗi đề |
| ③a | `construction_match` | Nó có dựng **những vật đề bảo dựng** không? | `x/k'` mỗi đề |
| ③b | `verification_match` | Nó có **tự biết** mình đúng không? | `x/k` mỗi đề |
| ④ | `construction_validity` | Nó **dựng hình** hay **khai kết quả**? | tỉ lệ trên tổng vật |
| ⑤ | `stability` | Lặp lại có ra cùng kết quả không? | `k` lượt / đề |

> ③ **tách đôi ở Phase 7A.2.** Trước đó nó là một chỉ số tên `obligation_match`
> so một danh sách phẳng. Lý do tách và số cũ: **§7**.

**KHÔNG GỘP.** Mỗi chỉ số đo một thứ khác nhau và chúng **đã đi ngược chiều
nhau** trong dữ liệu thật:

```
Phase 6.7.2, bài thiết diện:   served 5/5   ·   obligation_match 0/5
```

Báo `served` một mình ở đó là nói quá về năng lực hệ. Bốn trong năm lượt ấy dựng
đúng hình mà **không kiểm gì cả**.

---

## 2. Định nghĩa chính xác

### ① `served`

`SemanticRouteOutcome.servable == True` **và** envelope mang
`simulation_id == "generic.semantic_program"`.

Đây là chỉ số **yếu nhất** trong năm, và phải luôn đọc kèm ③.

### ② `oracle`

Đối chiếu với đáp án **độc lập**, so **QUAN HỆ / ĐẠI LƯỢNG**, không so toạ độ —
mô hình tự chọn hệ trục nên toạ độ không phải bất biến.

```
thể tích         phân số đúng bằng đáp án
khoảng cách      phân số (hoặc bình phương, khai rõ đơn vị)
góc              cos²
quan hệ          true / false
vị trí đặc biệt  bất biến tỉ lệ, vd "Q là trung điểm AD"
```

Ba trạng thái, **không phải hai**: `True` (đạt) · `False` (chấm được, trượt) ·
`None` (**không chấm được**). Gộp `None` vào `False` là ghi một lượt không đo
được thành một lượt sai.

### ③ Nghĩa vụ — HAI chỉ số, vì đề ra HAI loại lệnh

Đề hình học nói hai thứ khác nhau, và tới Phase 7A.1 chúng bị nhét chung một
danh sách phẳng:

```
"Hãy DỰNG mặt phẳng (PMN)"      → nghĩa vụ DỰNG   — sinh ra một VẬT
"CHỈ RA RẰNG M nằm trên SA"     → nghĩa vụ KIỂM   — phán một MỆNH ĐỀ
```

Gộp chúng không phải chuyện chữ nghĩa: bài `3-pmn-giao-tuyen` mang kỳ vọng
`{point_on_line, point_on_plane}` và bị **8 lượt liên tiếp** bác bỏ theo cùng
một hướng. `point_on_plane` ở đó chưa bao giờ là nghĩa vụ mô hình bỏ sót — nó là
một **mệnh lệnh dựng bị xếp nhầm vào tập kiểm**, và vì đề không hỏi điểm nào
thuộc `(PMN)` nên nghĩa vụ ấy không có witness và **không bao giờ đúng được**.
Một chỉ số gộp sẽ mãi báo *"mô hình sai"* ở đúng chỗ mô hình đọc đề đúng.

**Hai tập RỜI NHAU, khai riêng, không suy ra nhau.**

#### ③a `construction_match` — vật đề RA LỆNH DỰNG

Mỗi vật khai bằng **tên đề bài gọi** (`Q`, `(PMN)`, `d`) + **kiểu IR**
(`point3`/`line3`/`plane3`/…). Đạt khi mọi vật ấy có mặt trong tập vật chương
trình **thật sự dựng** — cùng định nghĩa *"được dựng"* mà ④ dùng, nên hai bảng
không mâu thuẫn nhau được.

Tên chương trình do **mô hình** đặt (`Q` → `Q_point`), nên phép so đi qua
`khop_ten_doi_tuong` — **lưới hoà giải của sản phẩm**, không phải lưới thứ hai
của riêng bộ đo. Trùng lõi ⇒ fail-closed, tính là thiếu.

Ba trạng thái như ②: `True` · `False` · `None`, và `None` ở **hai** chỗ khác
nhau (`vi_sao` phân biệt): đề không ra lệnh dựng gì ⇒ *không áp dụng*; không có
chương trình ⇒ *không chấm được*. Mẫu số vì thế là **số lượt chấm được**, không
phải `k`.

#### ③b `verification_match` — mệnh đề đề YÊU CẦU KIỂM

Tập `kind` mà `RequestContract` khai **bằng đúng** tập kỳ vọng. Đây là chỉ số ③
cũ, **định nghĩa không đổi**, chỉ đổi tên và đổi **nguồn kỳ vọng**.

#### Hai phép so KHÁC NHAU, có chủ đích

```
KIỂM   BẰNG ĐÚNG  (m == k)   — khai thừa CŨNG LÀ LỆCH
DỰNG   CHỨA ĐỦ    (m ⊆ k)    — dựng thêm KHÔNG bị trừ điểm
```

Bất đối xứng vì hai việc không đối xứng. Khai thừa một nghĩa vụ kiểm nghĩa là
mô hình trả lời một câu **không ai hỏi**, và thừa che mất chỗ nó thiếu. Còn dựng
thêm là **bắt buộc**: muốn có giao tuyến `d` thì phải dựng điểm trung gian mà đề
không gọi tên. Trừ điểm ở đó là phạt mô hình vì làm đúng phép dựng hình. Vật
thừa vẫn **quan trắc** được (`thua_dung`), chỉ không trừ.

> ⚠️ **Kỳ vọng phải đến từ NGUỒN NGOÀI.** Điều kiện này lộ ra ở Phase 6.7.2: kỳ
> vọng tôi tự đặt cho bài thiết diện bị **5/5 lượt** bác bỏ theo một hướng nhất
> quán, và đọc lại đề thì mô hình có lý. Nếu tôi tự đặt kỳ vọng, mọi chỗ tôi đọc
> đề khác mô hình sẽ được ghi thành *"mô hình sai"*.
>
> Cùng lớp vấn đề với việc tự soạn held-out, và `HOLDOUT_PROTOCOL §2` đã có cơ
> chế: **đáp án và yêu cầu đến từ nguồn ngoài, người đo không sửa được**.
>
> **Từ Phase 7A.2 điều kiện này là CỔNG, không còn là đoạn văn:** kỳ vọng nằm ở
> `expectations/*.json` (ngoài mã bộ đo, có lịch sử Git, `ly_do` trích từ đề cho
> **từng** nghĩa vụ), và `geometry_expectations.nap()` **từ chối nạp** một tập
> held-out khai `nguoi_danh_gia.loai = "nguoi_do"`. Tập `pilot` được phép — nó
> chấm bộ đo, không chấm mô hình — nhưng phải **khai thẳng** hạn chế ấy.

Kèm luôn `so_nghia_vu` thô. `so_nghia_vu = 0` là ca **đặc biệt phải nêu riêng**:
`served` khi ấy nghĩa là *"chạy trọn và mọi thứ lên được hình"*, **không** phải
*"đáp án đã được đối chiếu"*.

### ④ `construction_validity` — chỉ số MỚI, chốt ở Phase 6.8

Đo **cấu trúc chương trình**, không đo pass/fail. Ba số, không gộp:

```
literal_substitution   vật ĐÁNG LẼ PHẢI DỰNG mà khai sẵn:
                       · witness khai bằng `initial_value`  → khai ĐÁP ÁN
                       · line3/plane3/solid/polygon3 khai `initial_value`
                                                            → khai sẵn HÌNH
                       MỤC TIÊU: 0%

dependency_construction  vật sinh ra từ một phép dựng đọc TÊN vật khác

witness_derived        witness nằm trong tập vật được dựng/đo
                       MỤC TIÊU: 100%
```

**Mẫu số là phần đáng lẽ phải dựng, KHÔNG phải tổng khai báo.** Chia cho tổng
thì chương trình khai nhiều **điểm gốc** tự động "tệ" đi — mà điểm gốc là **dữ
kiện**, không phải kết quả. Điểm gốc khai toạ độ kèm `model_assumption` là hành
vi **đúng**: đề hình học không cho toạ độ và prompt bảo mô hình tự đặt hệ trục.

Kèm `do_sau_max` (chuỗi phụ thuộc dài nhất) — nó phân biệt *"dựng một bước"* với
*"dựng theo dây"*, và Phase 5G từng đo trần 2 do hợp đồng.

Công cụ: `scripts/analyze_construction_dependency.py`, **0 API call**, chạy trên
artifact đã lưu.

### ⑤ `stability`

**Mỗi đề chạy `k ≥ 3` lượt độc lập.** Báo cáo là `x/k`, **không phải pass/fail**.

Lý do có điều kiện này, đo được: cùng một mã, cùng ba đề, hai lượt liên tiếp cho
**0/3 rồi 3/3** (Phase 6.6). Một lượt duy nhất sẽ cho một con số mà lượt sau bác
bỏ.

Kèm **phân bố**, không chỉ tỉ lệ: `so_nghia_vu` của bài thiết diện dao động
`0 · 1 · 2 · 3 · 4` trên cùng một đề, và chính phân bố ấy — chứ không phải trung
bình — là phát hiện.

---

## 3. Phân loại thất bại — bốn nhóm, ĐÓNG

| | Nhóm | Ghi vào đây khi |
|---|---|---|
| 1 | **model generation** | chương trình sai mà hợp đồng có đường đúng đang mở |
| 2 | **contract** | hợp đồng **không diễn đạt được**, hoặc **cho phép** thứ engine cấm |
| 3 | **validator** | chương trình đúng mà cổng từ chối |
| 4 | **routing** | không tới được route sinh |

**Nhóm 2 và 3 chỉ ghi khi CHỨNG MINH ĐƯỢC.** Cách chứng minh đã dùng hai lần và
là chuẩn cho Phase 7: **chạy lại chính IR đã lưu** sau khi sửa, không sửa một ký
tự nào của chương trình. Qua ⇒ lỗi thuộc hệ. Không qua ⇒ thuộc mô hình.

Phân biệt này không phải chữ nghĩa. Ghi một lỗi validator vào nhóm 1 thì luận
văn báo một con số **thấp hơn thực tế** *và* **kết tội mô hình ở đúng chỗ nó làm
đúng** — đã xảy ra một lần (Phase 6.7, 2/15 lượt).

---

## 4. Điều báo cáo Phase 7 KHÔNG được làm

- **Không** báo `served` mà thiếu ③.
- **Không** gộp `oracle = None` vào `False`, và **không** gộp
  `construction_match = None` vào `False`.
- **Không** báo pass/fail cho một đề chạy `k` lượt.
- **Không** dùng kỳ vọng nghĩa vụ do người đo tự đặt **trên tập held-out**.
- **Không** gộp ③a với ③b thành một tỉ lệ — kể cả khi bảng trông gọn hơn.
- **Không** đổi định nghĩa chỉ số sau khi thấy số; đổi thì phải nói ra kèm số cũ.
- **Không** suy tỉ lệ khi mẫu `< 20` (`RELIABILITY_EVALUATION_PLAN §3.3`) — dưới
  ngưỡng ấy con số đọc là **đếm thô**.

---

## 5. Trạng thái các chỉ số ở mốc chốt

Đo trên `stability-6.7` + `stability-6.7.2`, 30 chương trình:

| Chỉ số | Giá trị |
|---|---|
| `served` | 9/15 → **14/15** (sau Phase 6.7.1) |
| `oracle` | 9/15 → **14/15** |
| `obligation_match` | 11/15 → 10/15 |
| `construction_validity` · literal_substitution | **0/231 = 0.0%** |
| `construction_validity` · dependency_construction | **209/231 = 90.5%** |
| `construction_validity` · witness_derived | **27/27 = 100%** |
| `construction_validity` · do_sau_max | **1 – 4** |
| `stability` | k = 5, hai vòng độc lập |

Đây là **đường cơ sở**, không phải mục tiêu. Phase 7 đo trên tập held-out, và số
của tập DEV không bao giờ là số của luận văn.

---

## 6. ĐÓNG BĂNG — chốt ở Phase 7A.2, trước 7B

Bốn chỉ số dưới đây **đóng băng định nghĩa**. Không sửa cách tính, không sửa
mẫu số, không thêm điều kiện, cho tới khi lượt held-out chạy xong:

| | Chỉ số | Đóng băng từ |
|---|---|---|
| ① | `served` | Phase 6.8 |
| ② | `oracle` | Phase 6.8 |
| ④ | `construction_validity` | Phase 6.8 |
| ⑤ | `stability` | Phase 6.8 |

③ là chỉ số **duy nhất** đổi ở 7A.2, và đổi **trước** khi tiêu call của 7B —
xem §7. Từ mốc này nó cũng đóng băng.

**Đóng băng nghĩa là gì, cụ thể:**

- Sửa cách tính một trong bốn chỉ số ⇒ mọi số đã đo **hết so được**, và lượt
  held-out phải chạy lại từ đầu. Đó là cái giá, nên hãy sửa *bây giờ* nếu định
  sửa.
- Đóng băng **chỉ số**, không đóng băng **bộ đo**: sửa lỗi khiến bộ đo tính sai
  chính định nghĩa đã chốt là **được** — Phase 7A.1 đã làm đúng thế. Ranh giới:
  *đổi định nghĩa* thì cấm, *sửa để bộ đo khớp định nghĩa* thì phải làm, và phải
  báo cáo kèm số trước/sau.
- Đóng băng này **độc lập** với `freeze_evaluation_candidate.py` và với
  `HOLDOUT_SEAL`: cái kia khoá **hệ được đo** (`backend/app`), cái này khoá
  **thước**. Một lượt đo đáng tin cần cả hai, và chúng hỏng theo hai cách khác
  nhau.

Cổng kiểm: `backend/tests/geometry/test_expectation_contract_7a2.py`.

---

## 7. Nhật ký đổi chỉ số — bắt buộc kèm SỐ CŨ

Luật §4 nói *"đổi thì phải nói ra kèm số cũ"*. Đây là chỗ nói.

### 7A.2 · ③ `obligation_match` → `construction_match` + `verification_match`

| | |
|---|---|
| **Đổi cái gì** | một danh sách phẳng ⇒ hai tập rời nhau; kỳ vọng ra khỏi mã bộ đo |
| **Vì sao** | `PHASE_7A_1_REPORT §5` — kỳ vọng của người đo ghi `0/3` ở đúng chỗ mô hình đọc đề đúng |
| **Đổi sau khi thấy số?** | **CÓ.** Khai thẳng: 8 lượt bác bỏ là thứ làm tôi đi đọc lại đề |
| **Phán quyết dựa vào đâu** | **văn bản đề**, không phải đầu ra mô hình: *"Hãy dựng mặt phẳng (PMN)"* nằm sau động từ **dựng** |
| **Trước 7B chưa?** | **RỒI** — chưa tiêu một call nào của benchmark held-out |

**Số cũ, ghi lại để không ai so nhầm hai thước:**

| Vòng đo | `obligation_match` (thước CŨ) | ghi chú |
|---|---|---|
| `stability-6.7` + `-6.7.2` | 11/15 → 10/15 | bài thiết diện 0/5 |
| `phase7a-pilot` | 12/15 | bài 3: 1/3 |
| `phase7a-pilot-sau-71` | 12/15 | bài 3: 0/3 |

Kỳ vọng đổi **chỉ ở bài `3-pmn-giao-tuyen`**:
`{point_on_line, point_on_plane}` → `{point_on_line}`. Bốn đề còn lại không đổi
một ký tự, nên số của chúng so trực tiếp được.

⚠️ **Số của bốn vòng trên và số của 7B nằm trên hai thước khác nhau.** Nhắc lại
điều này ở mọi bảng có cả hai, hoặc đừng để chúng chung một bảng.

⚠️ **Chưa có lượt đo nào chạy trên thước mới.** Bảng trên là số **cũ**; ③a chưa
có giá trị nào vì nó chưa từng được đo. Con số đầu tiên của nó sẽ đến từ 7B —
không được điền vào đây bằng cách chấm lại artifact cũ rồi gọi đó là kết quả.

### 7A.3 · ⑤ `stability` — ĐIỀU KIỆN LẤY MẪU, **không** phải định nghĩa

| | |
|---|---|
| **Định nghĩa chỉ số** | **KHÔNG ĐỔI.** Cả năm chỉ số giữ nguyên từng chữ |
| **Đổi cái gì** | `k` của lượt held-out: chốt **`k = 3`** cho cả 20 ô |
| **Vì sao ghi vào đây** | ⑤ có `k ≥ 3` **nằm trong định nghĩa** (`§2⑤`), nên chốt `k` là chốt một tham số của chỉ số đã đóng băng — dù không sửa cách tính |
| **Trước 7B chưa?** | **RỒI** — chưa tiêu một call nào của benchmark |
| **Ngân sách** | `20 × 3 × 6 = 360` logic · `20 × 3 × 8 = 480` HTTP |

Việc phải làm rõ đi kèm: `HOLDOUT_PROTOCOL §2` viết *"chạy MỘT LƯỢT"*, đọc được
theo hai nghĩa, và nghĩa rộng thì nó chống với `§2⑤` của file này. Đã làm rõ ở
`HOLDOUT_PROTOCOL §2`: *một lượt* = **một phiên đã niêm phong gồm `k` lượt độc
lập**, cấm **lặp CÓ SỬA** chứ không cấm cỡ mẫu. Đó là **làm rõ**, không phải nới
lỏng — hai tài liệu vốn nói về hai chuyện khác nhau.

Quyết định đầy đủ + phương án lui: `HOLDOUT_K_FINAL.md`, phân tích ba phương án:
`HOLDOUT_K_DECISION.md`.

⚠️ **Không có số nào đổi ở mục này.** ⑤ chưa từng được đo trên held-out, nên
không có "số cũ" để so — khác hẳn lần đổi 7A.2 ở trên.
