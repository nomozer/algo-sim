# PHASE 7A.2 — ĐÓNG BĂNG GIAO THỨC ĐÁNH GIÁ (2026-08-27)

> **Không** sửa năng lực hệ. **Không** sửa prompt. **Không** sửa DSL. Pha này
> chỉ đụng **bộ đo** và **hợp đồng chỉ số**, trước khi Phase 7B tiêu call đầu
> tiên trên tập held-out.
>
> Bằng chứng cây sạch: `freeze_evaluation_candidate.py --verify` **PASS** —
> *"Candidate khớp bản đã đóng băng (mã sản phẩm: 144 file, `7ab25683ce4e4e4d…`)"*.
> `CACHE_VERSION 46` không đổi · thẻ prompt không đổi · `pytest 2950` (2920 + 32
> test mới) · 0 API call.

---

## 0. Vì sao pha này tồn tại

Phase 7A.1 sửa hai sai lệch đo lường rồi để lại một cái **chưa sửa được bằng mã**:

```
3-pmn-giao-tuyen   obligation_match  0/3
```

Con số ấy **không phải lỗi mô hình**. Kỳ vọng `{point_on_line, point_on_plane}`
là do người đo đặt, và 8 lượt liên tiếp (5 ở 6.7.2 + 3 ở 7A.1) bác bỏ nó theo
**cùng một hướng**. Đọc lại đề thì mô hình có lý — nhưng báo cáo lúc ấy chỉ ghi
được điều đó thành một đoạn văn cảnh báo. Đoạn văn không chặn được lần sau.

Pha này biến ba cảnh báo thành ba cơ chế.

---

## 1. VIỆC ① — tách `obligation_match` làm hai

### Chẩn đoán: không phải kỳ vọng sai, mà là **hai loại lệnh bị gộp**

Đề hình học nói hai thứ có bản chất khác nhau:

```
"Hãy DỰNG mặt phẳng (PMN)"        → sinh ra một VẬT      → nghĩa vụ DỰNG
"CHỈ RA RẰNG M nằm trên SA"       → phán một MỆNH ĐỀ     → nghĩa vụ KIỂM
```

`RequestContract.obligations` chỉ diễn đạt được loại **thứ hai** — cả tám
`kind` hình học đều là mệnh đề kiểm được. Nên khi kỳ vọng nhét `(PMN)` vào tập
kiểm dưới nhãn `point_on_plane`, nghĩa vụ ấy **không có witness** (đề không hỏi
điểm nào thuộc `(PMN)`) và **không bao giờ đúng được**. Chỉ số gộp sẽ mãi báo
*"mô hình sai"* ở đúng chỗ mô hình đọc đề đúng.

⇒ Lỗi không nằm ở một giá trị kỳ vọng. Nó nằm ở chỗ **một chỉ số đang đo hai
câu hỏi**.

### Hai chỉ số, hai phép so — bất đối xứng CÓ CHỦ ĐÍCH

| | ③a `construction_match` | ③b `verification_match` |
|---|---|---|
| Đo gì | vật đề RA LỆNH DỰNG có được dựng không | `kind` hợp đồng khai có đúng đề hỏi không |
| Khai bằng | tên đề bài gọi + kiểu IR | `kind` trong taxonomy |
| Đối chiếu với | tập vật chương trình **thật sự dựng** | `RequestContract.obligations` |
| Phép so | **CHỨA ĐỦ** (`m ⊆ k`) | **BẰNG ĐÚNG** (`m == k`) |
| Dựng/khai thừa | **không trừ điểm**, chỉ quan trắc | **là lệch** |
| Trạng thái | `True` · `False` · `None` | `True` · `False` |

Bất đối xứng vì hai việc không đối xứng: khai thừa một nghĩa vụ kiểm là **trả
lời câu không ai hỏi** và che mất chỗ thiếu; còn dựng thêm điểm trung gian là
**bắt buộc** để có giao tuyến `d`. Trừ điểm ở đó là phạt mô hình vì làm đúng
phép dựng hình.

`None` tách **hai** ca mà thước cũ không phân biệt: *đề không ra lệnh dựng gì*
(`2-the-tich`) và *không có chương trình để chấm*. Mẫu số của ③a vì thế là **số
lượt chấm được**, không phải `k` — cùng luật đã áp cho `oracle` từ Phase 6.8.

### Không viết máy đo thứ hai

| Việc | Mượn của |
|---|---|
| so tập kiểm | `reliability_v2.obligation_match` (đã có 25 test khoá hành vi) |
| "vật nào đã được dựng" | `analyze_construction_dependency.phan_tich` — **cùng** khái niệm mà ④ dùng |
| tên chương trình ↔ tên đề | `domain_profile.khop_ten_doi_tuong` — **lưới của sản phẩm** |

Điểm cuối quan trọng nhất: bộ đo **không** được có lưới hoà giải riêng. Hai lưới
sẽ trôi khỏi nhau đúng lúc cần so hai vòng đo, và khi ấy không ai chỉ ra được
chỗ lệch.

### Đo lại trên artifact CŨ — không sửa một ký tự nào của chương trình

`phase7a-pilot-sau-71/3-pmn-giao-tuyen-lan1`:

```
thước CŨ   obligation_match     False   (kỳ vọng đòi thêm point_on_plane)
thước MỚI  verification_match   True    (khai đúng {point_on_line})
           construction_match   True    (6/6 vật: M · N · P · (PMN) · d · Q)
```

`(PMN)` khớp `plane_PMN` qua lưới hoà giải — thứ thước cũ **không nhìn thấy**,
vì nó chưa bao giờ hỏi câu *"có dựng không"*.

---

## 2. VIỆC ② — kỳ vọng ra khỏi mã bộ đo

Trước pha này kỳ vọng nằm ngay trong `measure_geometry_stability.BAI`:

```python
{"id": "3-pmn-giao-tuyen", "de": "…",
 "nghia_vu_mong_doi": ["point_on_line", "point_on_plane"],   # ← thước, nằm trong máy
 "oracle": "Q_trung_diem_AD"}
```

Nghĩa là **người viết bộ đo sửa được thước ngay trong lượt đang đo**, và không
ai tra ngược được kỳ vọng đã đổi lúc nào.

Nay: `docs/evaluation/geometry/expectations/pilot.json` — có lịch sử Git, có
`ly_do` **trích từ đề** cho từng nghĩa vụ, có khai báo ai là người phán.

### Tôi vẫn là người phán cho pilot — và khai thẳng điều đó

Năm đề pilot là đề tôi tự soạn (tập DEV), nên không có nguồn ngoài nào phán hộ
được. Giả vờ có là tệ hơn. File khai `nguoi_danh_gia.loai = "nguoi_do"` kèm hạn
chế: **số của tập này không bao giờ là số luận văn**.

Chỗ điều kiện ⑨ trở thành cổng thật là **held-out**:

```
geometry_expectations.nap("holdout")  ⇒  ValueError nếu loai == "nguoi_do"
```

Lý do phải là cổng chứ không phải lời hứa: trên pilot một kỳ vọng sai lộ ra sau
8 lượt; trên held-out chỉ có **một** lượt (`HOLDOUT_PROTOCOL §2`), nên cùng lỗi
ấy sẽ đi thẳng vào luận văn mà không có lượt thứ hai để phát hiện.

### Phân chia thẩm quyền — không khai một thứ ở hai chỗ

```
holdout/pool.json            ĐỀ + ĐÁP ÁN CHÍNH THỨC + nguồn (đề thi ngoài)
expectations/holdout.json    NGHĨA VỤ, tách dựng/kiểm, ly_do trích từ đề
BANG_O                       ô slot nào đòi nghĩa vụ kiểm nào
```

Ba nguồn, ba thẩm quyền, và một cổng đối chiếu chúng (`test_neu_da_co_holdout_*`,
hiện `skip` cho tới khi tập thật xuất hiện — soạn xong pool mà quên soạn kỳ vọng
thì test đỏ chứ không im).

### Lần đổi kỳ vọng được khai kèm SỐ CŨ

Đổi **chỉ ở bài 3**, và ghi vào `lich_su_doi` ngay trong file:

```
gia_tri_cu   {point_on_line, point_on_plane}      so_cu  0/5 · 1/3 · 0/3
gia_tri_moi  {point_on_line}
```

⚠️ Đây **là** một lần đổi thước sau khi thấy số. Luật `§4` cho phép với điều
kiện khai ra — và phán quyết dựa trên **văn bản đề** (*"Hãy dựng mặt phẳng
(PMN)"* nằm sau động từ **dựng**), không dựa trên đầu ra mô hình. 8 lượt bác bỏ
là thứ khiến tôi đi đọc lại đề, không phải thứ quyết định giá trị mới.

---

## 3. VIỆC ③ — đóng băng bốn chỉ số còn lại

`PHASE7_METRIC_CONTRACT §6`: `served` · `oracle` · `construction_validity` ·
`stability` **đóng băng định nghĩa** cho tới khi lượt held-out chạy xong. ③ là
chỉ số duy nhất đổi ở pha này, và đổi **trước** khi 7B tiêu call.

Ranh giới ghi rõ để không bị lạm dụng theo cả hai hướng:

- *đổi định nghĩa* ⇒ **cấm** (mọi số đã đo hết so được, held-out phải chạy lại);
- *sửa để bộ đo khớp đúng định nghĩa đã chốt* ⇒ **phải làm** — Phase 7A.1 đã làm
  đúng thế — nhưng báo cáo kèm số trước/sau.

Và đóng băng này **độc lập** với `freeze_evaluation_candidate` / `HOLDOUT_SEAL`:
cái kia khoá **hệ được đo**, cái này khoá **thước**. Một lượt đo đáng tin cần cả
hai, và chúng hỏng theo hai cách khác nhau.

---

## 4. Thay đổi chỉ số — bảng tóm tắt để báo cáo 7B trích thẳng

| Chỉ số | Trạng thái sau 7A.2 |
|---|---|
| ① `served` | **không đổi** · đóng băng |
| ② `oracle` | **không đổi** · đóng băng |
| ③ `obligation_match` | **TÁCH ĐÔI** → ③a `construction_match` + ③b `verification_match` |
| ③a `construction_match` | **MỚI** — chưa có giá trị đo nào |
| ③b `verification_match` | định nghĩa **giữ nguyên** ③ cũ; đổi tên + đổi nguồn kỳ vọng |
| ④ `construction_validity` | **không đổi** · đóng băng |
| ⑤ `stability` | **không đổi** · đóng băng |

Số cũ dưới thước cũ (giữ nguyên, **không** chấm lại):

| Vòng đo | `obligation_match` | bài 3 |
|---|---|---|
| `stability-6.7` + `-6.7.2` | 11/15 → 10/15 | 0/5 |
| `phase7a-pilot` | 12/15 | 1/3 |
| `phase7a-pilot-sau-71` | 12/15 | 0/3 |

⚠️ **Hai thước khác nhau.** Số trên và số của 7B không được nằm chung một bảng
mà không nhắc lần tách này.

⚠️ **③a chưa từng được đo.** Giá trị đầu tiên của nó phải đến từ một lượt chạy
thật. Chấm lại artifact cũ rồi gọi đó là kết quả của ③a là dựng một con số cho
một lượt đo chưa xảy ra — bản báo cáo này cố ý **không** làm thế, dù dữ liệu có
sẵn.

---

## 5. Cổng mới (32 test, `test_expectation_contract_7a2.py`)

| Nhóm | Chặn cái gì |
|---|---|
| hai tập rời nhau | vật dựng mang tên một `kind`; `kieu` khai bằng `kind` — **dấu hiệu sớm nhất của việc gộp lại** |
| lý do | nghĩa vụ không có `ly_do` ≥ 20 ký tự; tập dựng rỗng mà không ghi vì sao rỗng |
| nguồn | held-out dùng kỳ vọng người đo; `sinh_tu_model_output` ≠ `false` |
| hồi quy mã | `"nghia_vu_mong_doi": [` quay lại mã runner |
| trước khi chạy | đề trong `BAI_PILOT` chưa có kỳ vọng (bắt với **0 call**, thay vì nổ giữa lượt live) |
| phép so | thừa vật không trừ điểm · thiếu vật là lệch · vật khai sẵn ≠ vật đã dựng · ba trạng thái |
| artifact thật | bài 3 dưới thước mới: `verification` khớp, `construction` 6/6 |
| đóng băng | `§6` còn nêu đủ bốn chỉ số; `lich_su_doi` có số cũ |

Hai test `skip` có chủ đích: chúng canh `holdout.json` và `pool.json` — chưa
tồn tại, và sẽ tự bật khi 7B soạn xong.

**Giới hạn tự khai:** `test_bon_chi_so_dong_bang_van_co_mat` bắt được ca **mất
hẳn** một chỉ số, **không** bắt được ca sửa tinh vi bên trong định nghĩa. Thứ ấy
phải đọc diff — không có test nào thay được, và nói rằng có là nói dối về mức
bảo đảm.

---

## 6. Chưa làm, có chủ đích

- **Chưa đo lại vòng nào dưới thước mới.** Đúng luật: pha này không chạy LLM.
- **`dev/cases.json` chưa tách hai tập.** Nó là tập DEV, dùng cho
  `run_geometry_dev_evaluation`; tách nó là việc của lượt DEV kế tiếp, không
  phải điều kiện của 7B.
- **`expectations/holdout.json` mới có khuôn.** Nội dung thật cần pool thật, mà
  pool cần đề từ nguồn ngoài — mắt xích ấy nằm ngoài kho mã.
