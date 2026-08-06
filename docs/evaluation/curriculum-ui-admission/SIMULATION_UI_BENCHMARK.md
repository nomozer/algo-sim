# SIMULATION_UI_BENCHMARK — mở thật 5 hệ tham khảo, đo, rút nguyên tắc

**Cách đo.** Chrome thật qua CDP, viewport 1440×1000, chờ JS dựng xong sân khấu,
chụp ảnh và đo DOM. **Không** đọc trang giới thiệu rồi suy diễn. Với PhET có
**bấm vào màn hình mô phỏng** rồi mới đo (pass 2), vì màn chọn ban đầu không phản
ánh sân khấu thật.

Số liệu thô: [benchmark-observations.json](benchmark-observations.json),
[benchmark-observations-pass2.json](benchmark-observations-pass2.json).
Ảnh: [benchmark-screenshots/](benchmark-screenshots/).

**Chỉ rút nguyên tắc. Không sao chép theme, màu, layout hay icon của bất kỳ hệ nào.**

## 1. Số đo

| Hệ | Sân khấu / viewport | Chữ (ký tự) | Nút | Panel | Khối mã | Ghi chú |
|---|---|---|---|---|---|---|
| **PhET — Build an Atom** (đã bấm vào sim) | **100 %** (svg) | 2364 | 32 | 1 | không | Sân khấu chiếm trọn khung; bảng phụ ("Net Charge", "Mass Number") **gập lại mặc định** |
| **VisuAlgo — Sorting** | 35 % (svg) | 3588 | 4 | 2 | **có** | Mã giả nằm cạnh sân khấu, luôn hiện |
| **Python Tutor** | ~0 % (không có sân khấu đồ hoạ lớn) | 4930 | 9 | **10** | **có** | Lấy mã làm trung tâm; hình vẽ là phụ trợ cho khung stack/heap |
| **CS Field Guide — Sorting** | ~0 % | 940 | 5 | 2 | không | Dạng **bài đọc** có hình minh hoạ, không phải mô phỏng điều khiển được |
| **Algorithm Visualizer** | — | — | — | — | — | **NOT_VERIFIED** — SPA không dựng được trong headless, thử **2 lượt** đều trắng trang. Không đưa ra bất kỳ nhận định nào về hệ này. |

## 2. Bốn nguyên tắc đo được (không phải cảm nhận)

**NT-1 — Sân khấu phải là thứ lớn nhất, và chênh lệch phải rõ.**
PhET để sân khấu chiếm 100 % khung nhìn. VisuAlgo 35 % nhưng phần còn lại là mã giả
— tức vẫn là "một sân khấu + một thứ hai". Không hệ nào để **bảng tra cứu lớn hơn
cơ chế chính**. Đây chính là lỗi đo được ở `logic.boolean_dag` trước pilot: sơ đồ
**11 %** còn bảng chân lý **24 %** — bảng to gấp đôi cơ chế.

**NT-2 — Thông tin phụ thì gập lại, không bày sẵn.**
PhET có 32 nút nhưng hai bảng số phụ **đóng mặc định**; học sinh mở khi cần. Bày
sẵn mọi thứ là cách nhanh nhất để làm nặng khung nhìn mà không thêm thông tin.

**NT-3 — Lượng chữ tự nó không nói lên điều gì; vị trí của chữ mới nói.**
PhET **2364 ký tự** — nhiều hơn CS Field Guide (940) — nhưng phần lớn là **nhãn dán
trên sân khấu** (tên hạt, số proton/neutron), không phải văn xuôi giải thích. Python
Tutor 4930 ký tự nhưng nằm trong **10 panel**. Vì vậy tiêu chí đúng không phải
"ít chữ hơn" mà là **"chữ có dính vào vật thể học sinh đang nhìn không"**.

**NT-4 — Có hệ cố tình KHÔNG hiển thị mã, và vẫn dạy được.**
PhET không có khối mã nào. VisuAlgo và Python Tutor thì lấy mã làm trung tâm. Hai
trường phái này phục vụ hai mục tiêu khác nhau: *hiểu hiện tượng* vs *đọc chương
trình*. AlgoSim đang đứng ở giữa — mã giả có mặt ở **11/22** target. Điều này là
lựa chọn thiết kế, không phải khuyết điểm, nhưng nên **có chủ đích theo từng target**
chứ không mặc định.

## 3. Điều KHÔNG kết luận được

- **Không** đo được hệ nào **dạy tốt hơn**. Toàn bộ bảng trên là số đo **bố cục**,
  không phải số đo **học được**.
- **Không** có dữ liệu học sinh của bất kỳ hệ nào trong bảng, kể cả PhET (PhET có
  công bố nghiên cứu riêng, nhưng tôi **không** tra trong lượt này nên không viện dẫn).
- **Algorithm Visualizer** phải giữ nguyên trạng thái **NOT_VERIFIED**; hai lượt thử
  đều thất bại, không được suy đoán bù.
