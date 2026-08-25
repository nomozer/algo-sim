# HELD-OUT HÌNH HỌC — giao thức

> Trả lời câu *"hệ làm được với bài **chưa từng thấy** không?"*. Tập DEV **không**
> trả lời được câu đó: nó đã bị nhìn, và hệ đã được sửa theo nó qua bốn wave.

---

## 0. Vấn đề cốt lõi, và vì sao nó không tự giải được

**Tôi không thể tự tạo một tập held-out.** Bất kỳ đề nào tôi viết ra, tôi đã
nhìn — và mọi bản vá sau đó đều có thể vô tình nhắm vào nó. Tập DEV hiện tại
chính là ví dụ: 10 bài tôi viết, rồi bốn wave sửa hệ theo đúng chỗ chúng hỏng.

Nên giao thức này đặt trên một nguyên tắc khác: **đề và đáp án đều phải đến từ
NGOÀI hệ thống và NGOÀI tôi.**

---

## 1. Nguồn: đề thi công khai, KHÔNG phải đề tôi soạn

| | Đề tôi soạn | **Đề thi công khai** |
|---|---|---|
| Ai viết đề | tôi | Bộ GD-ĐT / sở / trường |
| Ai tính đáp án | tôi | **đáp án chính thức** |
| Tôi đã nhìn trước chưa | rồi | rồi — nhưng **không sửa được đề** |
| Đại diện chương trình | tự nhận | **có căn cứ** |

Điểm mạnh không nằm ở chỗ *"tôi chưa nhìn"* — mà ở chỗ **tôi không viết được ra
chúng, và không sửa được đáp án**. Một đề tôi tự soạn có thể vô thức né đúng
những chỗ hệ yếu; một câu trong đề tốt nghiệp thì không.

**Nguồn dùng** (xem §7): đề tốt nghiệp THPT chính thức, đề minh hoạ của Bộ, và
chuyên đề ôn thi có đáp án chi tiết.

---

## 2. Ba tính chất bắt buộc

**① Đáp án đến từ ĐÁP ÁN CHÍNH THỨC, không từ hệ và không từ tôi.**
Chạy hệ rồi chép kết quả làm đáp án biến phép đo thành phép lặp lại chính nó —
đúng lỗi mà `cases.json` của DEV đã ghi ra để tránh.

**② Niêm phong TRƯỚC khi chạy.** Băm nội dung tập đã chọn, commit con dấu, rồi
mới chạy. Không có con dấu thì không có cách nào chứng minh tập không bị sửa sau
khi thấy kết quả.

**③ Chạy MỘT LƯỢT.** Trượt thì ghi nhận là trượt. Sửa hệ rồi chạy lại trên cùng
tập held-out thì tập ấy **thành DEV** — và phải nói ra điều đó, không được im.

---

## 3. Quy trình

```
① SOẠN POOL          ≥30 bài trích từ nguồn công khai
                      pool.json — CÓ đề, CÓ đáp án chính thức, CÓ nguồn
                      chưa chạy hệ trên bất kỳ bài nào

② GVHD CHO SEED      một số nguyên. KHÔNG do tôi chọn — nếu tôi chọn seed
                      thì tôi chọn được cả tập.

③ RÚT TẤT ĐỊNH       seed → chọn N=10, phân tầng theo chủ đề
                      scripts/seal_geometry_holdout.py

④ NIÊM PHONG         băm tập đã chọn → HOLDOUT_SEAL.json → COMMIT
                      cây phải SẠCH, freeze --verify PASS

⑤ CHẠY MỘT LƯỢT      runner cũ, --out-dir holdout-results
                      không sửa prompt, không bỏ bài, không retry riêng

⑥ BÁO CÁO            G1 · G2 · A · O · obligation_match
                      cộng: bao nhiêu bài NGOÀI phủ (§coverage) — trượt vì
                      hợp đồng không diễn đạt được, không vì mô hình sai
```

---

## 4. Phân tầng — bắt buộc, và vì sao

Rút ngẫu nhiên thuần từ pool sẽ cho một tập lệch: đề thi có **rất nhiều** bài
thể tích và khoảng cách, rất ít bài thiết diện. Một tập 10 bài toàn thể tích sẽ
cho điểm cao mà không nói được gì.

Phân tầng theo **bảng phủ** (`GEOMETRY_CURRICULUM_COVERAGE.md`):

| Tầng | Số bài | Vì sao |
|---|:-:|---|
| Chủ đề **ĐƯỢC** phủ | 7 | đo NĂNG LỰC mô hình |
| Chủ đề **MỘT PHẦN / KHÔNG** phủ | 3 | đo hệ có **từ chối trung thực** không |

⚠️ **Ba bài tầng hai không phải để lấy điểm.** Chúng kiểm một thứ khác: gặp đề
ngoài khả năng, hệ **nói thẳng là không diễn đạt được** hay **bịa ra một hình
gần giống**? Prompt đã dặn phải nói thẳng; đây là chỗ kiểm lời dặn ấy có tác
dụng không. Một mô phỏng sai hình còn tệ hơn không có mô phỏng.

Nên tập held-out có **hai thang chấm**, không được gộp:

```
tầng ĐƯỢC phủ     chấm A · O · obligation_match
tầng NGOÀI phủ    chấm DUY NHẤT: có từ chối trung thực không
```

---

## 5. Điều giao thức này KHÔNG bảo đảm

- **Không phải blind thật.** Tôi soạn pool nên tôi đã đọc mọi đề trong đó. Bảo
  đảm thật là *"tôi không viết ra đề và không sửa được đáp án"*, yếu hơn *"tôi
  chưa từng thấy"*. Phải khai đúng mức ấy khi báo số.
- **N = 10 quá nhỏ để ra tỉ lệ.** `RELIABILITY_EVALUATION_PLAN §3.3` cấm chia
  khi mẫu < 20. Kết quả đọc là **đếm thô**.
- **Không đo tần suất chương trình.** Chưa ai đếm mỗi chủ đề chiếm bao nhiêu
  phần trăm đề thi thật, nên tập này *đại diện chủ đề*, không *đại diện tần suất*.

---

## 6. Trạng thái

```
pool.json          CHƯA CÓ  — việc kế tiếp
seed từ GVHD       CHƯA CÓ  — chặn bước ③
HOLDOUT_SEAL.json  CHƯA CÓ
```

**Chặn cứng ở seed.** Không có seed của người ngoài thì bước rút không có tính
độc lập, và cả giao thức tụt xuống thành "tôi chọn 10 bài tôi thích".

---

## 7. Nguồn đề

- [Lời giải chi tiết đề thi Toán tốt nghiệp THPT 2025 chính thức (MathVN)](https://www.mathvn.com/2025/07/loi-giai-chi-tiet-e-thi-toan-tot-nghiep.html)
- [Đề minh hoạ môn Toán kì thi tốt nghiệp THPT từ 2025 — đề tham khảo và đáp án](https://cmcu.edu.vn/de-minh-hoa-mon-toan-ki-thi-tot-nghiep-thpt-tu-nam-2025-de-tham-khao-va-dap-an/)
- [Chuyên đề hình học không gian ôn thi tốt nghiệp THPT 2025, giải chi tiết (Thư Viện Học Liệu)](https://thuvienhoclieu.com/chuyen-de-hinh-hoc-khong-gian-on-thi-tot-nghiep-thpt-giai-chi-tiet/)
- [Chuyên đề hình học không gian ôn thi tốt nghiệp THPT (HOCMAI)](https://hocmai.vn/kho-tai-lieu/read.php?id=17710)
- [100 bài tập Toán 11 chương Quan hệ vuông góc, có đáp án (VietJack)](https://vietjack.com/toan-11-ct/trac-nghiem-chuong-8-quan-he-vuong-goc-trong-khong-gian.jsp)
