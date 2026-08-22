# Chọn 40 case SEALED — hướng dẫn cho GVHD / người thứ ba

Bạn đang giữ mắt xích quyết định của cả phần đánh giá. Việc cần làm nhỏ: **chọn
đúng 40 ID** từ pool. Nhưng nó phải do **bạn** làm, không phải agent viết hệ —
đó là toàn bộ lý do phần này tồn tại.

## Trước khi chọn

Pool đã đóng băng. Kiểm bất cứ lúc nào:

```bash
cd docs/evaluation/semantic-benchmark/custodian
sha256sum EXTERNAL_SELECTION_POOL.json
cat EXTERNAL_SELECTION_POOL_FINGERPRINT.txt
```

Hai dòng phải trùng nhau. Selection chỉ hợp lệ khi thực hiện **sau** thời điểm
này và **trên đúng pool này**.

Bảng chọn: `EXTERNAL_SELECTION_POOL.md` — **89 bài**, cần lấy **40**.

## Hai phương án, cả hai đều hợp lệ

### B. Seed tất định — **khuyến nghị**

Nếu mục tiêu là **giảm chủ quan lựa chọn**, đây là phương án nên dùng. Bạn chỉ
cần đưa một con số bất kỳ; script lấy 40 ID và ghi lại seed để ai cũng chạy lại
kiểm được.

```bash
cd docs/evaluation/semantic-benchmark/custodian
python select_by_seed.py --seed <số của bạn>            # xem trước
python select_by_seed.py --seed <số của bạn> --write    # chốt
```

Script **từ chối chạy** nếu pool đã đổi so với fingerprint đã đóng băng — chọn
trên một pool đã đổi thì tính tái lập cũng vô nghĩa.

Ưu điểm: không ai — kể cả bạn — nghiêng tập theo cảm nhận về bài dễ hay khó.
Nhược: phân bố lớp/chủ đề là ngẫu nhiên, có thể lệch về Tin học 10 vì nó chiếm
phần lớn pool.

### A. Bạn tự chọn 40 bài

Chọn tay nếu bạn muốn kiểm soát **độ đa dạng** về lớp, SGK và chủ đề. Gợi ý cân
đối, không bắt buộc: lấy cả Tin học 10 lẫn Tin học 11 KHMT, và trải trên nhiều
bài khác nhau thay vì dồn vào một chương.

Gửi lại danh sách dạng:

```
T10-C5-014
T10-C5-037
T11CS-C6-006
…
```

đúng 40 dòng.

## Điều quan trọng nhất khi chọn

**Đừng cố đoán hệ làm được bài nào.** Bảng chọn cố ý không hiển thị checker
support, khả năng IR, hay kết quả pilot — vì nếu tập được chọn theo phỏng đoán
"bài này chắc chạy được" thì con số thu về chỉ đo lại chính phỏng đoán đó.

Bài khó mà hệ trượt là **kết quả nghiên cứu có giá trị**, không phải sự cố. Cứ
chọn theo nội dung bài và nguồn.

## Sau khi bạn chốt

Phía phát triển sẽ: dựng `sealed/cases.json` từ đúng 40 ID (chuyển đổi cơ học,
giữ nguyên `problem_text` và provenance) → tính ground truth độc lập bằng Python
thuần → chạy validator → niêm phong → Task 12 **một lần**.

Từ lúc runner đọc SEALED, hệ **không được sửa** vì bất kỳ kết quả nào.
