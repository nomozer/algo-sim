# Chương 4. Kết quả thực nghiệm và thảo luận

> Bản thảo. Mọi con số trong chương này được **tái tính từ artifact có băm
> SHA-256**, không chép từ báo cáo — phép đối chiếu ở
> `docs/evaluation/geometry/thesis-final-acceptance/RECONCILIATION.json`
> (`DOCUMENTATION_INPUT_CONSISTENCY = PASS`, 31/31 trường khớp).

---

## 4.1. Thiết kế đánh giá

Hệ thống được xây dựng để **tự sinh mô phỏng hình học không gian từ đề bài
tiếng Việt**. Luận điểm trung tâm là ranh giới **R0**: mô hình ngôn ngữ đọc đề
và *tổng hợp một chương trình có biên* (Semantic Program — các bước dựng hình),
còn toàn bộ việc tính toán, thẩm định và dựng cảnh do các tầng **tất định** đảm
nhiệm. Mô hình không được phép phát ra một toạ độ nào.

Vì vậy phép đánh giá phải trả lời được hai loại câu hỏi khác nhau, và **không
được gộp chúng**:

- hệ *có làm đúng không* — thuộc về các tầng tất định;
- mô hình *có tự tìm ra chương trình không* — thuộc về mô hình.

Thiết kế đánh giá tách chúng bằng cách chấm **mười lăm chiều độc lập** cho mỗi
ca, trong đó ba chiều then chốt — đáp số đúng (`EXACT_ANSWER_MATCH`), hình dựng
đúng (`SCENE3D_PASS`) và hệ dám phát (`SERVABLE`) — được ghi **riêng** và không
chiều nào được suy ra từ chiều khác.

Toàn bộ tiêu chí, ngưỡng, ngân sách và bộ ca được **khoá trước khi có bất kỳ kết
quả nào** (`created_before_live_run = true`, chính sách phiên bản `1.1.0`, băm
`a44469b0…`). Đây là điều kiện để các con số phía sau có nghĩa: một ngưỡng đặt
sau khi thấy kết quả chỉ mô tả lại kết quả.

### 4.1.1. Loại phép đo và những gì nó *không* tuyên bố

| | |
|---|---|
| `EVALUATION_CLASS` | `FROZEN_FINAL_DEVELOPMENT_BENCHMARK` |
| `HELD_OUT_CLAIM` | **NO** |
| `OPERATOR_INDEPENDENCE_REQUIRED` | **NO** |
| tái lập mô hình | `LIMITED_ACCEPTED` |

Bộ đánh giá **không phải held-out**: đề do chính người triển khai soạn và nằm
trong kho mã. Mô hình không nhận đáp số, chương trình mẫu hay bất kỳ siêu dữ
liệu chấm điểm nào — đường gửi tới mô hình trả về đúng **một** trường là đề bài
— nhưng *"mô hình chưa thấy"* khác *"người soạn bộ đo chưa thấy"*, và chương này
giữ đúng sự phân biệt ấy.

---

## 4.2. Bộ dữ liệu và phạm vi

Phạm vi tính năng đã đóng (`FEATURE_SCOPE_COMPLETE = YES`): mười hai họ hình
được lập bản đồ từ mã nguồn, trong đó **mười họ nằm trong phạm vi** và hai họ
`OUT_OF_SCOPE` vì lý do kiến trúc đo được.

Bộ ca gồm **7 ca dương + 2 ca âm**, cố định, không rút thăm. Bảy ca dương là một
lời giải **set-cover**: mỗi họ trong phạm vi được ít nhất một ca phủ, và **bỏ bất
kỳ ca nào cũng làm mất ít nhất một họ**. Tính chất thứ hai quan trọng không kém
tính chất thứ nhất — nó bảo đảm không có lượt gọi mô hình nào tiêu vô ích.

**Bảng 4.1 — Bộ ca và độ phủ họ hình**

| ca | họ hình được phủ | nghĩa vụ đo |
|---|---|---|
| `p1` | điểm–đường–vectơ–mặt · đa giác & thiết diện phẳng · đa diện lồi | `volume`, `area`, `distance` |
| `p2` | đa diện **lõm** | `volume` |
| `p3` | hình cầu · thiết diện tròn của khối cong | `volume`, `area` |
| `p4` | hình trụ | `volume`, `lateral_area` |
| `p5` | hình nón | `volume`, `lateral_area` |
| `p6` | thiết diện xiên (elip) của hình **trụ** | `area` |
| `p7` | thiết diện xiên (elip) của hình **nón** | `area` |
| `n1` | *(âm)* khối tròn xoay tổng quát — `OUT_OF_SCOPE` | — |
| `n2` | *(âm)* khối ghép/bù cần boolean — `OUT_OF_SCOPE` | — |

Hai ca âm không phải "bài khó": chúng là **bài hệ phải từ chối**. Ranh giới của
chúng được chứng minh bằng **vắng mặt** — quét mã nguồn cho thấy không có thẩm
quyền tích phân ký hiệu, không có kiểu biểu thức hàm trong `MemoryType`, và
không có thẩm quyền boolean nào trong nhân hình học.

---

## 4.3. Cấu hình lượt đo

**Bảng 4.2 — Danh tính lượt đo**

| trường | giá trị |
|---|---|
| `RUN_ID` | `thesis-final-20260908T160224Z` |
| `RUN_VALIDITY` | **VALID** |
| candidate (mã sản phẩm được đo) | `d72db7c3…` — 92 file |
| `CACHE_VERSION` | 94 |
| corpus / expected results / gold | `2eb3f24d…` / `1099924b…` / `985c8922…` |
| chính sách đo | `1.1.0`, băm `a44469b0…` |
| runner lúc chạy / bộ chấm | `19c4c311…` / `4f7cae90…` |
| mô hình | `gemini-2.5-flash` (alias), `temperature = 0.2` |
| trần cứng | 25 lượt gọi logic · 100 lần thử vật lý · 196 000 token |
| cây làm việc lúc chạy | **sạch** |
| danh tính sau lượt chạy | **không trôi** |

Trước lượt chạy, một cổng tiền kiểm gồm **tám điều kiện** phải đạt toàn bộ, trong
đó có một lượt chứng nhận runner bằng **provider giả** với `REAL_PROVIDER_CALLS =
0`. Chỉ khi cả tám đạt, lượt gọi mô hình đầu tiên mới được phép đi.

Lượt đo chia hai chặng:

- **Chặng A** — mỗi ca: một lượt phân tích đề, một lượt tổng hợp chương trình,
  **không sửa**. Kết quả được ghi xuống đĩa và băm **trước** khi chặng B bắt đầu,
  để con số one-shot không thể được làm đẹp bởi một lượt sửa về sau.
- **Chặng B** — chỉ ca dương chưa phục vụ được và thuộc lớp lỗi mà sản phẩm cho
  sửa: **đúng một** lượt sửa, **tiếp tục** từ hợp đồng đã đóng băng và chương
  trình hỏng của chặng A, không phân tích lại đề và không sinh lại từ đầu.

---

## 4.4. Kết quả tổng hợp

**Bảng 4.3 — Kết quả từng ca dương**

| ca | chặng phục vụ | grounding | phủ | tĩnh | bất biến nguồn | thực thi | hậu điều kiện | vết dựng | cảnh 3D | phục vụ | đáp số |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `p1` | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `72` · `9` · `3√6` |
| `p2` | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `96` |
| `p3` | **B** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `4500π` · `144π` |
| `p4` | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `360π` · `120π` |
| `p5` | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `100π` · `65π` |
| `p6` | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `25π√5` |
| `p7` | A | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | `2π√6` |

**Bảng 4.4 — Kết quả ca âm**

| ca | hệ có từ chối? | từ chối ở tầng nào | mã lỗi | phát ra đáp số? | phán quyết |
|---|---|---|---|---|---|
| `n1` | **có** | `stage_semantic_program` (trước khi tới cổng thẩm định) | `UNANCHORED_DERIVED_ASSUMPTION` | **không** | `UNRELATED_FAIL_CLOSED` |
| `n2` | **có** | cổng phủ (`structural_coverage`) | `requested_operation_uncovered` | **không** | `HONEST_UNSUPPORTED_REFUSAL` |

**Bảng 4.5 — Tổng hợp**

| chỉ số | phân số | tỷ lệ |
|---|---|---|
| phục vụ được ngay lần đầu | 6/7 | 85,7 % |
| phục vụ được sau tối đa một lượt sửa | 7/7 | 100 % |
| đáp số chính xác | 7/7 | 100 % |
| bất biến nguồn | 7/7 | 100 % |
| hậu điều kiện | 7/7 | 100 % |
| vết dựng | 7/7 | 100 % |
| cảnh 3D | 7/7 | 100 % |
| ca âm từ chối đúng cách | 2/2 | 100 % |
| lượt sửa thành công | 1/1 | *(mẫu chỉ một ca — chỉ báo cáo mô tả)* |
| **đáp số sai phát ra âm thầm** | **0** | — |
| **ngoại lệ không kiểm soát** | **0** | — |

**Bảng 4.6 — Đối chiếu 11 đại lượng với oracle độc lập**

| ca | đại lượng | biểu thức hệ trả về | oracle độc lập | phương pháp oracle |
|---|---|---|---|---|
| `p1` | thể tích khối chóp | `72` | 72 | shoelace 2D + `h/3` |
| `p1` | diện tích thiết diện | `9` | 9 | `½‖Σ Pᵢ × Pᵢ₊₁‖` |
| `p1` | khoảng cách điểm–đường | `3√6` | 7,348469… | `‖w × u‖ / ‖u‖` |
| `p2` | thể tích chóp đáy lõm | `96` | 96 | shoelace **có dấu** |
| `p3` | thể tích khối cầu | `4500π` | 14 137,166941… | công thức SGK |
| `p3` | diện tích hình tròn thiết diện | `144π` | 452,389342… | `r² = R² − d²` |
| `p4` | thể tích khối trụ | `360π` | 1 130,973355… | công thức SGK |
| `p4` | diện tích xung quanh trụ | `120π` | 376,991118… | công thức SGK |
| `p5` | thể tích khối nón | `100π` | 314,159265… | công thức SGK |
| `p5` | diện tích xung quanh nón | `65π` | 204,203522… | `l = √(r²+h²)` |
| `p6` | diện tích elip xiên của trụ | `25π√5` | 175,620368… | **lấy mẫu 200 000 điểm** + shoelace 3D |
| `p7` | diện tích elip xiên của nón | `2π√6` | 15,390598… | **lấy mẫu 200 000 điểm** theo tia từ đỉnh |

Mười một đại lượng khớp **cả hai** phép kiểm: chuỗi hiển thị đúng từng ký tự, và
giá trị số nằm trong dung sai đã khoá so với oracle. Oracle được cài **độc lập
với nhân hình học** — mã của nó không import bất cứ thứ gì thuộc nhân, và điều
đó được cưỡng chế bằng quét cú pháp trừu tượng.

Với hai ca elip, phép kiểm độc lập đi xa nhất: thay vì dùng lại công thức bán
trục mà nhân hình học dùng, oracle lấy 200 000 điểm nằm trên giao tuyến rồi tính
diện tích đa giác nội tiếp. Hai đường dẫn sai theo hai kiểu khác nhau, nên việc
chúng cho cùng một số là bằng chứng thật.

---

## 4.5. Kết quả theo từng câu hỏi nghiên cứu

### RQ1 — Độ phủ: *Hệ biểu đạt và thực thi được những họ hình nào?*

Bảy ca phủ **10/10 họ trong phạm vi**. Trong suốt lượt đo:
`NEW_IR_OPERATIONS = 0`, `NEW_MEMORY_TYPES = 0`,
`NEW_PER_PROBLEM_MODULES = 0`.

Cần đọc con số "0 phép IR mới" cho đúng. Nó **không** nói hệ làm được mọi bài
hình học. Nó nói: bảy bài thuộc bảy dạng khác nhau — từ đa diện lồi tới thiết
diện elip của hình nón — được phục vụ **bằng cách ghép các phép sẵn có**, không
bài nào cần một nhánh mã riêng. Đó là mệnh đề *"bài mới ≠ mã mới"*, và nó là một
mệnh đề **có điều kiện**: điều kiện là bài phải biểu diễn được bằng IR hiện có.
Bài ngoài IR bị **từ chối**, không được xấp xỉ — hai ca âm là bằng chứng cho vế
sau.

**Mức bằng chứng: end-to-end.**

### RQ2 — Tính đúng: *Kernel, checker, vết dựng và cảnh 3D có đồng thuận với oracle độc lập không?*

11/11 đại lượng khớp chuỗi hiển thị và khớp oracle độc lập; 7/7 ca đạt bất biến
nguồn, hậu điều kiện, vết dựng và cảnh 3D.

Đáng chú ý là các giá trị vô tỉ: `3√6`, `25π√5`, `2π√6` được giữ **chính xác**
suốt chuỗi tính toán và hiển thị, không làm tròn ở bất kỳ khâu nào. Đây là hệ
quả trực tiếp của việc miền số được đóng ở `ℚ(√, π)` thay vì dùng dấu phẩy động.

**Mức bằng chứng: end-to-end + đúng tất định** (oracle cài độc lập).

### RQ3 — Khả năng tự sinh: *Mô hình có tự phân tích đề và ghép đúng các phép IR không?*

6/7 ca dương (**85,7 %**) được phục vụ ngay lần thử đầu; 7/7 (**100 %**) sau tối
đa một lượt sửa.

Đây là kết quả **trên bộ đánh giá này**, với `n = 1` mỗi họ. Nó không phải ước
lượng tổng thể, và luận văn không đặt ngưỡng cho chỉ số này — chính sách đo khoá
sẵn `no_threshold_by_design = true`, vì đặt một vạch sau khi thấy kết quả là mô
tả lại kết quả, còn đặt trước mà không có nguồn là bịa ra một tiêu chuẩn.

**Mức bằng chứng: model discoverability**, mẫu nhỏ.

### RQ4 — An toàn: *Hệ có từ chối đúng thay vì phục vụ một kết quả sai không?*

2/2 ca âm từ chối đúng cách, **không ca nào phát ra một đại lượng nào**.
`SILENT_WRONG_ANSWER_COUNT = 0`, `UNHANDLED_EXCEPTION_COUNT = 0`.

Đây là nhóm tiêu chí **bắt buộc** của phép đo: một giá trị khác 0 ở đây phá chính
luận điểm của đề tài, nên chúng là đạt/không-đạt chứ không phải số liệu mô tả.

**Mức bằng chứng: end-to-end.**

### RQ5 — Hiệu quả: *Một mô phỏng phục vụ đúng tốn bao nhiêu?*

**Bảng 4.7 — Phân bổ lượt gọi và token**

| | |
|---|---|
| lượt gọi logic | **19** = 9 phân tích + 9 tổng hợp + 1 sửa |
| lần thử vật lý | **19** |
| retry tầng vận chuyển | **0** |
| token vào / ra / suy nghĩ / đệm | 49 481 / 14 390 / 33 998 / 1 859 |
| **tổng token** | **97 869** |
| trần cứng | 196 000 (còn dư 98 131) |
| token trên mỗi mô phỏng phục vụ đúng | **13 981** |
| lượt gọi trên mỗi mô phỏng phục vụ đúng | **2,71** |

Chín ca tiêu 19 lượt gọi — đúng bằng call graph dự đoán, không một lượt thừa.
Không có retry vận chuyển nào, nên số lần thử vật lý bằng số lượt gọi logic.

Tổng token thực **cao hơn dự báo 31 %** (97 869 so với 74 763). Nguyên nhân đọc
được từ sổ ghi: `thought_tokens` chiếm **34 %** tổng, mà trung vị lịch sử dùng để
dẫn dự báo không tách riêng phần này.

Cần phân biệt hai vai trò khác nhau: **dự báo chi phí** đã sai 31 %, còn **bộ
giới hạn ngân sách** vẫn hoàn thành vai trò an toàn — trần 196 000 dư 50 %, và
runner kiểm ngân sách trước từng lượt gọi. Một cái phanh không cần dự đoán đúng
quãng đường; nó chỉ cần dừng được xe.

**Bảng 4.8 — Phân bổ lượt gọi theo chặng và theo ca**

| ca | chặng A: phân tích | chặng A: tổng hợp | chặng B: sửa | tổng | phục vụ ở |
|---|---|---|---|---|---|
| `p1` | 1 | 1 | 0 | 2 | A |
| `p2` | 1 | 1 | 0 | 2 | A |
| `p3` | 1 | 1 | **1** | **3** | **B** |
| `p4` | 1 | 1 | 0 | 2 | A |
| `p5` | 1 | 1 | 0 | 2 | A |
| `p6` | 1 | 1 | 0 | 2 | A |
| `p7` | 1 | 1 | 0 | 2 | A |
| `n1` | 1 | 1 | 0 | 2 | *(từ chối)* |
| `n2` | 1 | 1 | 0 | 2 | *(từ chối)* |
| **tổng** | **9** | **9** | **1** | **19** | 7 phục vụ · 2 từ chối |

Chặng B tiêu **đúng một** lượt: `analyze_calls_in_stage_b = 0` và số lượt sinh
chương trình đầu trong chặng B cũng bằng 0 — thiết kế "tiếp tục" thay vì "chạy
lại" được xác nhận trên số liệu, không chỉ trong mô tả.

**Mức bằng chứng: end-to-end**, báo cáo mô tả.

---

## 4.6. Phân tích ca cần sửa

Ca `p3` (mặt cầu và thiết diện tròn) là ca dương duy nhất không phục vụ được ở
chặng A.

**Nguyên nhân — thuộc lớp lỗi mô hình.** Chương trình mô hình viết ra khai một
vật là `curved_solid` nhưng dùng nó ở vị trí đòi `solid`; tầng thẩm định tĩnh bác
với thông điệp `IR_OPERAND_TYPE: 'S' — cần solid, có curved_solid`. Không tầng
nào của hệ phát sinh lỗi; cổng làm đúng việc của nó.

**Lượt sửa — tiếp tục, không chạy lại.** Chặng B nhận lại:

- `RequestContract` đã đóng băng từ chặng A (băm `d2d7b46f…`),
- chương trình hỏng nguyên văn (băm `445d7b45…`),
- chuỗi chẩn đoán của chính sản phẩm (băm `a59bcc13…`),

rồi tiêu **đúng một** lượt gọi. Số lượt phân tích đề trong chặng B là **0**, số
lượt sinh chương trình đầu là **0**. Kết quả: ca được phục vụ với `4500π` và
`144π` — đúng cả hai đại lượng.

**Ý nghĩa và giới hạn.** Kết quả này cho thấy cơ chế sửa **có tác dụng trên ca
này**, và cho thấy đường "tiếp tục" hoạt động trên **đầu ra thật của mô hình**
chứ không chỉ trên dữ liệu mô phỏng. Nhưng mẫu là `1/1`: một ca thành công không
cho phép phát biểu một tỷ lệ phục hồi. Luận văn chỉ báo cáo mô tả.

---

## 4.7. Phân tích an toàn — hai ca âm

Ba câu hỏi cho mỗi ca âm.

### `n1` — khối tròn xoay tổng quát

1. **Hệ có từ chối không?** Có.
2. **Từ chối ở tầng nào?** Ở `stage_semantic_program`. Mô hình cố xấp xỉ khối
   tròn xoay bằng cách **bịa ba điểm** (`O`, `P_x2_y0`, `P_x2_y4`) không có
   trong đề; cổng xuất xứ chặn bằng `UNANCHORED_DERIVED_ASSUMPTION` — một mã
   thuộc nhóm *"không được sửa"*, nên vòng tổng hợp dừng hẳn.
3. **Có phát ra đáp số hay ngoại lệ không?** Không, cả hai.

**Một giới hạn của phép đăng ký trước, cần ghi rõ.** Ca này đã đăng ký trước hai
mã lỗi kỳ vọng. Không mã nào quan sát được — vì lời từ chối xảy ra **bên trong**
vòng tổng hợp, trước khi `verify_and_compile` được gọi, nên không có mã lỗi tầng
thẩm định nào để đối chiếu. Đây là giới hạn về **tầng quan sát** của phép đăng ký
trước, không phải khiếm khuyết của hệ: hành vi fail-closed vẫn đạt, và lý do từ
chối đúng bản chất — hệ không cho mô hình bịa dữ kiện.

Luận văn **không** sửa lại danh sách mã kỳ vọng cho khớp kết quả. Sửa kỳ vọng sau
khi thấy kết quả sẽ xoá đúng thứ mà việc đăng ký trước tồn tại để giữ.

### `n2` — khối ghép/bù cần hình học boolean

1. **Hệ có từ chối không?** Có.
2. **Từ chối ở tầng nào?** Cổng phủ, `structural_coverage`, mã
   `requested_operation_uncovered` — đúng mã đã đăng ký trước.
3. **Có phát ra đáp số hay ngoại lệ không?** Không, cả hai.

Đây là trường hợp lời từ chối **chạm đúng ranh giới** đã tuyên bố: đề hỏi thể
tích của một vật mà không phép IR nào tạo ra được, và cổng phủ nói đúng điều đó.

**Tổng kết an toàn:** `NEGATIVE_FAIL_CLOSED = 2/2` (tiêu chí bắt buộc, đạt);
`TARGET_BOUNDARY_PASS = 1/2` (chỉ số **đo**, không phải ngưỡng — điều này được
khoá trước lượt chạy, vì hệ không có mã lỗi nào mang tên hai họ ngoài phạm vi).

---

## 4.8. Kiểm soát tính đúng của công cụ đo

> Tiểu mục này ghi lại một **lỗi của công cụ đo**, không phải lỗi của hệ thống,
> và cũng không phải một cải thiện sản phẩm sau khi xem kết quả.

Lượt chấm đầu tiên báo `SILENT_WRONG_ANSWER_COUNT = **6**` — tức sáu lần hệ phát
ra đáp số sai một cách âm thầm. Nếu con số ấy đúng, nó phá chính luận điểm trung
tâm của đề tài.

**Nó không đúng.** Bộ chấm tra đáp số bằng tên biến lấy từ **chương trình mẫu**
(`V`, `S_T`, `S_E`…), trong khi tên biến là thứ **mô hình tự đặt**. Trong lượt
chạy thật, mô hình dùng `the_volume_sabcd`, `V_S_MNPQR`, `dien_tich_elip_e`,
`dist_S_BD`… Kết quả là sáu trên bảy ca **có đáp số hoàn toàn đúng** bị đọc thành
`None` và bị chấm là sai.

**Vì sao lượt chứng nhận bằng provider giả không phát hiện được.** Provider giả
trả về **chính chương trình mẫu**, nên tên biến của "mô hình" luôn trùng tên
mẫu, và phép tra sai không bao giờ lộ ra. Bài học có thể phát biểu tổng quát:
*một provider giả giống bản mẫu quá mức thì không kiểm được những lỗi chỉ xuất
hiện khi mô hình được tự do lựa chọn.*

**Cách sửa.** Ánh xạ tên biến đi qua **loại nghĩa vụ** (`volume`, `area`,
`lateral_area`, `distance`) — thứ do tầng phân tích đề khai và do taxonomy đã
đóng băng quyết định, không do mô hình đặt tên. Loại nghĩa vụ là khoá duy nhất
trong mọi ca của bộ dữ liệu, và bộ chấm **dừng có báo lỗi** nếu điều đó không còn
đúng. Đồng thời, lượt chứng nhận được bổ sung một ca **đổi tên toàn bộ biến**, và
một phép tiêm lỗi khôi phục hành vi cũ để chứng minh guard mới thật sự bắt được.

**Quy trình đính chính.** Thực hiện **ngoại tuyến**, **không gọi lại mô hình**,
**không chạy lại ca nào**. Toàn bộ dữ liệu thô giữ **nguyên từng byte**; bản đính
chính ghi băm SHA-256 của ba tệp mà nó đính chính, để bản sửa truy ngược được về
bản gốc. Kết quả sau đính chính: `SILENT_WRONG_ANSWER_COUNT = 0`,
`EXACT_ANSWER_PASS = 7/7`.

**Phân loại:** `MEASUREMENT_FAILURE_COUNT = 1`, `SYSTEM_FAILURE_COUNT = 0`.

Việc ghi lại sự cố này là một phần của kết quả, không phải một phụ lục. Nó cho
thấy công cụ đo cũng cần được kiểm chứng như đối tượng được đo — và trong trường
hợp này, sai lệch chỉ bị phát hiện vì con số phi lý đủ lớn để buộc phải soi lại.

---

## 4.9. Thảo luận

**Tính đúng.** Kết quả trên bộ đánh giá cho thấy khi mô hình tổng hợp được một
chương trình hợp lệ, phần tất định của hệ cho đáp số **chính xác tuyệt đối**
trong mọi ca đã kiểm tra, bao gồm ba đại lượng vô tỉ. Điều này củng cố lựa chọn
kiến trúc trung tâm: đặt toàn bộ việc tính toán ở phía tất định, và không cho mô
hình chạm vào một con số nào.

**Khả năng tự sinh.** Trong phạm vi các ca đã kiểm tra, mô hình tự tìm được
chương trình đúng ở 6/7 ca ngay lần đầu, kể cả những dạng khó như đa diện lõm và
thiết diện elip xiên của hình nón. Ca còn lại hỏng ở một lỗi kiểu — mô hình dùng
đúng phép nhưng khai sai kiểu vật — và tự sửa được khi nhận lại chính thông điệp
từ chối. Điều này gợi ý rằng nút thắt của lớp bài này nằm ở **cách hệ mô tả hợp
đồng cho mô hình** hơn là ở năng lực suy luận hình học của mô hình; nhưng với
`n = 1` mỗi họ, đây là một quan sát chứ chưa phải một kết luận.

**An toàn.** Hệ từ chối cả hai bài ngoài bao đóng mà không phát ra một con số
nào. Đáng chú ý là **cách** nó từ chối: ở `n1`, mô hình đã cố bịa dữ kiện để đi
tiếp, và tầng chặn nó là cổng xuất xứ — đúng cơ chế mà ranh giới R0 dựng ra.
Điều này cho thấy R0 không chỉ là một nguyên tắc thiết kế mà là một ràng buộc
được cưỡng chế trên đường chạy thật.

**Hiệu quả.** 13 981 token cho một mô phỏng phục vụ đúng, với 2,71 lượt gọi mỗi
ca. Con số này chỉ có nghĩa khi đi kèm mẫu số (7 ca đạt) và không so sánh được
với một lượt đo có tỷ lệ đạt khác.

---

## 4.10. Nguy cơ ảnh hưởng đến độ tin cậy

**Bảng 4.9 — Threats to validity**

| nguy cơ | loại | mức độ | biện pháp đã áp dụng |
|---|---|---|---|
| Bộ đánh giá không phải held-out | ngoại suy | **cao** | khai rõ `HELD_OUT_CLAIM = NO`; mô hình không nhận đáp số/chương trình mẫu; chính sách cấm gọi bộ này là held-out |
| Mẫu nhỏ: `n = 1` mỗi họ | thống kê | **cao** | không đặt ngưỡng cho chỉ số hành vi; mọi tỷ lệ in kèm mẫu số |
| Chỉ một lượt đánh giá | ổn định | **cao** | `STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED`, khoá trước lượt chạy |
| Tái lập mô hình ở mức hạn chế | tái lập | **trung bình** | alias mô hình, thời điểm UTC, tham số gửi/không-gửi đều ghi lại; không tuyên bố tái lập từng bit |
| Người soạn bộ đo cũng là người triển khai | thiên lệch | **trung bình** | tiêu chí, ngưỡng, ngân sách khoá **trước** kết quả và băm được |
| Công cụ đo có thể sai | đo lường | **đã hiện thực hoá** | một lỗi đã xảy ra và được ghi ở §4.8; đã bổ sung guard và phép tiêm lỗi |
| Đăng ký trước có thể không quan sát được | đo lường | **đã hiện thực hoá** | `n1` — ghi rõ ở §4.7, không sửa kỳ vọng cho khớp |
| Dự báo chi phí lệch 31 % | vận hành | **thấp** | trần cứng vẫn dư 50 %; nguyên nhân đã định vị (`thought_tokens`) |

---

## 4.11. Đối chiếu chín tuyên bố của đề tài

**Bảng 4.10 — Trạng thái C1–C9**

| | tuyên bố | trạng thái | bằng chứng | giới hạn |
|---|---|---|---|---|
| **C1** | Bài mới được phục vụ bằng cách ghép phép IR tổng quát | **đạt** | 0 phép IR mới, 0 kiểu mới, 0 module theo bài; 7 ca / 7 dạng | chỉ đúng trong IR hiện có |
| **C2** | Mọi đại lượng tính trong miền số chính xác | **đạt** | 11/11 khớp chuỗi hiển thị **và** oracle độc lập | bao đóng `ℚ(√, π)` |
| **C3** | Toạ độ, phương trình mặt phẳng, độ dài được đối chiếu ngược với đề | **đạt** | 7/7 bất biến nguồn | chỉ kiểm được thứ đề có nêu |
| **C4** | Vết dựng và cảnh 3D dẫn xuất từ trạng thái tất định | **đạt** | 7/7 vết dựng và cảnh 3D | đo cấu trúc cảnh, không đo chất lượng thị giác |
| **C5** | Đáp số đúng và hình đúng là hai chiều độc lập | **đạt** *(phương pháp)* | ba cột ghi riêng trong mọi artifact | là tuyên bố về phương pháp đo |
| **C6** | Mô hình tự phân tích đề và ghép đúng các phép IR | **PARTIAL** | 6/7 lần đầu; 7/7 sau ≤1 lượt sửa | `n = 1` mỗi họ, một lượt; **không ngưỡng** |
| **C7** | Bài ngoài bao đóng bị từ chối bằng mã ổn định | **đạt** | 2/2 fail-closed; 0 đáp số sai; 0 ngoại lệ | chạm đúng ranh giới 1/2 — xem §4.7 |
| **C8** | Chi phí một mô phỏng đúng đo được | **đạt** *(mô tả)* | 19 lượt · 97 869 token · 13 981 token/ca | mẫu số thay đổi ⇒ không so liên lượt |
| **C9** | Hai họ ngoài phạm vi vì lý do kiến trúc | **PARTIAL** | chứng minh vắng mặt bằng máy; fail-closed 2/2 | bằng chứng thuộc lớp *vắng mặt*, không phải mã lỗi có tên |

```
PRODUCT_PROMOTION_ELIGIBLE = NO
STABILITY_UNDER_ACCEPTANCE = NOT_MEASURED
```

Hai kết luận này **đã biết trước lượt đo**, không suy từ kết quả: bộ ca có đúng
một ca mỗi họ và chạy đúng một lần, nên điều kiện *"đã đo độ ổn định"* của chính
sách không thể thoả. Một lượt đánh giá tốt không phải là giấy phép bật tính năng.
