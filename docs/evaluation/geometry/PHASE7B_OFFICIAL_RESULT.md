# PHASE 7B — KẾT QUẢ LƯỢT ĐO CHÍNH THỨC

> **Bằng chứng bất biến.** Không sửa hệ dựa trên file này. Wave phát triển sau
> được dùng DEV để sửa; con số ở đây là đường cơ sở, và nó không được chạy lại.

```
RUN_ID              phase7b-official-82917341
SEED                82917341   (nguon_seed = nguoi_van_hanh, KHÔNG phải GVHD)
SEAL                PASS · seal_hash 67896c32644db9fe…
MEASURED_FREEZE     7ab25683ce4e4e4d… (144 file) — trước VÀ sau lượt chạy
MODEL_IDENTITY      gemini-2.5-flash · CACHE_VERSION 46 · commit 8150cc0
RUN_COMPLETENESS    PASS  (60/60 lượt · 0 trùng · 0 bản ghi lạ)
CASES 20 · REPETITIONS 3
LOGICAL_CALLS       225 / 360
HTTP_CALLS          245 / 480   (retry 20 · transient 16)
```

---

## 1. Hai thang, không gộp

`HOLDOUT_PROTOCOL §3`: *"Hai thang không được gộp thành một cột."*

### Tầng B (6 ô, 18 lượt) — thang **TỪ CHỐI TRUNG THỰC**

| | Số |
|---|---|
| từ chối trung thực | **14/18** |
| **BỊA HÌNH** | **0/18** |
| sự cố — ném lỗi thay vì nói không diễn đạt được | 4/18 |

Bốn lượt sự cố: `hp_b05_038-lan3`, `hp_b06_041-lan{1,2,3}`. Chúng **không**
phải bịa hình, cũng **không** phải từ chối trung thực: hệ ném exception thay
vì phát biểu rằng nó không diễn đạt được. Xếp vào ô thứ ba, thấy được.

Đây là kết quả mạnh nhất của cả lượt đo: **0 lần bịa hình trên 18 lượt đề
ngoài phủ**, gồm cả B03 — ô mà giao thức gọi là *"khó nhất và quan trọng
nhất"* vì hệ **tính được** góc mặt–mặt và có thể lặng lẽ dùng nó trả lời câu
hỏi góc nhị diện. Nó không làm thế: 3/3 từ chối.

### Tầng A (14 ô, 42 lượt) — thang **A · O · ③**

| Chỉ số | tử / mẫu áp dụng | N/A | trượt |
|---|---|---|---|
| ① `served` | **20 / 42** | 0 | 22 |
| ② `oracle` | **6 / 33** | 9 | 27 |
| ③a `construction_match` | **14 / 23** | 19 | 9 |
| ③b `verification_match` | **32 / 42** | 0 | 10 |
| ⑤ `stability` | **7 / 14** bài ổn định trên cả 3 lượt | | |

Chỉ 13/14 ô có nguồn công khai (A12 tự soạn). Bỏ A12:
`served 18/39` · `oracle 4/30` · `construction 14/23` · `verification 29/39`
· `stability 7/13`.

**Mẫu < 20 ở ③a nên con số ấy đọc là ĐẾM THÔ**, không phải tỉ lệ
(`METRIC_CONTRACT §4`).

`oracle` N/A = 9 không phải "sai": đó là 9 lượt **không chấm được** vì hợp
đồng không khai nghĩa vụ trùng khoá oracle — A01 (`point_on_line`) 3 lượt,
A09 và A10 (`angle`) 6 lượt. Gộp chúng vào `False` là ghi một lượt không đo
được thành một lượt sai.

---

## 2. Ổn định — không trung bình hoá bất đồng

7/14 bài tầng A cho cùng kết cục trên cả ba lượt. Bảy bài còn lại dao động:

| Bài | served | oracle | kiểm | dựng | nghĩa vụ | chặng |
|---|---|---|---|---|---|---|
| `hp_a01_003` | 2/3 | 0/3 | 0/3 | 0/3 | **1 · 2** | postconditions · served |
| `hp_a02_004` | 1/3 | 0/3 | 2/3 | 0/3 | **1 · 2** | execution · grounding · served |
| `hp_a03_008` | 2/3 | 0/3 | 3/3 | 2/3 | 1 | semantic_program · served |
| `hp_a04_009` | 1/3 | 0/3 | 3/3 | 3/3 | 1 | execution · grounding · served |
| `hp_a08_020` | 2/3 | 0/3 | 3/3 | 3/3 | 2 | grounding · served |
| `hp_a12_001` | 2/3 | **2/3** | 3/3 | 0/3 | 1 | grounding · served |
| `hp_a14_030` | 1/3 | **1/3** | 3/3 | 0/3 | 1 | grounding · served |

Phân bố `so_nghia_vu` dao động `1 · 2` trên cùng một đề (A01, A02) — cùng
hiện tượng đã ghi ở Phase 6.7, và chính phân bố ấy là phát hiện, không phải
trung bình.

Ba bài **ổn định ở trạng thái hỏng**: `hp_a09_024`, `hp_a10_026` (cả hai
`stage = scope`, 0 nghĩa vụ, 3/3 lượt) và `hp_a06_017` (`structural_coverage`
3/3). Ổn định không đồng nghĩa với đúng.

---

## 3. Taxonomy (§18)

| Nhóm | Lượt |
|---|---|
| A · LLM semantic synthesis | 21 |
| C · unsupported capability / **từ chối đúng** | 14 |
| D · deterministic validation/kernel/interpreter | 7 |
| E · metric/scoring/tooling | 6 |
| B · grounding / symbol reconciliation | 6 |
| F · transport/provider | **0** |

**0 lỗi hạ tầng.** 20 lần retry transport và 16 lần chạm transient đều được
policy đã đóng băng nuốt trọn (`TRANSIENT_STATUS {429,500,502,503,504}` ×
`MAX_ATTEMPTS 4`), không lượt nào chạm trần ngân sách. Không lỗi hạ tầng nào
bị quy thành lỗi mô hình.

Nhóm E gồm 4 lượt tầng B ném lỗi + 2 lượt tầng A `served` mà oracle không
chấm được — **khuyết tật của bộ đo và của đường xử lý lỗi, không phải của mô
hình**.

Hai phát hiện đáng chú ý nhất, cả hai đều là **thu hẹp năng lực chứ không
phải sai số học**:

1. **A09 · A10 (góc) bị chặn ở `scope`, 3/3 lượt, 0 nghĩa vụ.** Hệ không nhận
   đề hỏi *góc* là trong phạm vi. Đây là ô mà `BANG_O` khai là trong phủ.
2. **A01 (`point_on_line`) sinh hợp đồng không mang nghĩa vụ ấy**, nên oracle
   không nối được — dù 2/3 lượt vẫn `served`.

---

## 4. Điều báo cáo này KHÔNG tuyên bố

```
OFFICIAL_HELDOUT_COVERAGE            20/20 ô
PUBLIC_SOURCE                        19/20
CURATED_PRESEAL                      1/20   (hp_a12_001, ô A12)
A01_A02_A13_LIMITATION               PRESERVED
FULL_SOURCE_PROBLEM_CORRECTNESS      KHÔNG đo, KHÔNG tuyên bố
EVALUATED_SCOPE                      PRE_REGISTERED_EXECUTABLE_OBLIGATIONS
SYSTEM_CHANGED_DURING_RUN            NO
EXPECTATION_CHANGED_DURING_RUN       NO
SEAL_CHANGED_DURING_RUN              NO
CONTAMINATION                        NONE
```

**A01 · A02 · A13 vẫn hẹp hơn đề gốc.** A01 chấm *điểm thuộc giao tuyến*, không
chấm **phương** giao tuyến; A02 chấm quan hệ thuộc, không chấm **danh tính**
giao điểm; A13 chấm đồng phẳng, không chấm **số cạnh** thiết diện. Không được
suy ra *"hệ giải đúng bài gốc"* từ những nghĩa vụ này.

**Một sửa bộ đo SAU khi thấy số, khai thẳng.** Bản chấm đầu tiên gộp hai
thang: nó đọc 18 lượt tầng B `servable = False` như 18 lượt TRƯỢT và xếp
chúng vào `A_llm_synthesis`. Đó là vi phạm `HOLDOUT_PROTOCOL §3` và là đúng
lớp sai lệch mà `METRIC_CONTRACT §3` ghi là đã xảy ra một lần. Sửa **bộ đo**,
không sửa hệ được đo, không đổi định nghĩa chỉ số nào; số tầng A không đổi
một đơn vị. Con số bị bản đầu bóp méo: `served 20/57` → `20/42` tầng A cộng
`14/18` từ chối đúng tầng B.

---

## 5. Bằng chứng cho quyết định wave sau

**Đã soát `PHASE7_METRIC_CONTRACT`, `HOLDOUT_PROTOCOL`, `HOLDOUT_K_FINAL`:
KHÔNG có ngưỡng chấp nhận số nào được đăng ký trước.** Nên phần này là **diễn
giải**, không phải một phép kiểm giả thuyết đã đăng ký, và nó không được đọc
như GO/NO-GO.

```
EVIDENCE_SUPPORTS_3D_NEXT:  MIXED
```

**Vì sao MIXED, không phải WEAK.** Hai trụ của luận điểm R0 đứng vững:

- **Ranh giới năng lực giữ được**: 0/18 bịa hình, kể cả ở B03. Hệ không trả
  lời câu hỏi nó không tính được — đó chính là tính chất mà một mô phỏng dạy
  học cần nhất, vì *"một mô phỏng sai hình còn tệ hơn không có mô phỏng"*.
- **Tầng tất định không phải nút thắt**: `verification_match 32/42` cho thấy
  hợp đồng đọc đúng nghĩa vụ ở phần lớn lượt; F = 0 và D = 7 (17%).

**Vì sao không phải STRONG.** Tầng sinh chưa đủ tin cậy để làm nền:

- `served 20/42` — chưa tới một nửa số lượt ra được envelope phục vụ được;
- `oracle 6/33` chấm được — trong đó A09/A10 còn không vào nổi phạm vi;
- `stability 7/14` — nửa số bài đổi kết cục giữa ba lượt trên **cùng một mã**.

Nút thắt nằm ở **A (21 lượt)** và **B-grounding (6 lượt)**, tức ở khâu LLM
sinh chương trình và nối ký hiệu — **không** ở kernel, không ở hạ tầng.

### NEXT_PROJECT_STAGE — một khuyến nghị

**Mở wave sửa `scope` cho họ GÓC (A09 · A10) trên DEV trước, không bắt đầu
3D.** Đó là lỗi có biên rõ nhất trong bảng: hai ô, 6/6 lượt, cùng một chặng
`scope`, 0 nghĩa vụ sinh ra — nghĩa là đề bị loại **trước** khi tầng sinh có
cơ hội nào. Nó rẻ hơn mọi mục khác trong taxonomy, và cho tới khi khâu này
thông thì con số `oracle` chưa nói được gì về chất lượng sinh chương trình,
vì mẫu chấm được còn quá hẹp.

Dựng 3D lúc này là dựng bề mặt cho một tầng ngữ nghĩa mà **nửa số bài đổi kết
cục giữa các lượt**.
