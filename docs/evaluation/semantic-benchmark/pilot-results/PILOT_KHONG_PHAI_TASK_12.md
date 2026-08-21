# LƯỢT CHẠY PILOT — **KHÔNG PHẢI** Task 12

> Mọi con số trong thư mục này là **kết quả pilot nội bộ**. Chúng **không được**
> trích vào luận văn như A, B, D1 hay D2 của Task 12.

## Vì sao không phải Task 12

Task 12 đòi một tập SEALED do **custodian độc lập** soạn. Tập đang được chạy ở
đây (`sealed/cases.json`, fingerprint `34a10a9c…`) do **chính tác nhân đã viết
hệ** soạn ra: cùng một thực thể đã viết taxonomy nghĩa vụ, các checker, prompt
và schema.

Ground truth thì **độc lập thật** — tính bằng Python thuần trong
`sealed/ground_truth_solver.py`, không import một dòng mã sản phẩm nào, kiểm
được bằng mắt. Nhưng **việc CHỌN ĐỀ** thì không có cách nào chứng minh là không
bị dẫn dắt bởi hiểu biết về năng lực hệ. Đó là thiên lệch chí mạng nhất, và nó
không đo được.

Khai báo đầy đủ nằm ngay trong `sealed/cases.json`, khối
`custodian_declaration` — nó đi cùng dữ liệu nên không thể bị tách rời khỏi số.

## Vậy lượt này dùng để làm gì

Đúng một việc: **chạy toàn tuyến với API thật** và phơi ra những lỗi mà mọi test
offline không bắt được. Cho tới lúc này, đường sinh ngữ nghĩa chưa từng chạy
end-to-end với LLM thật qua `run_pipeline`.

Những thứ lượt này kiểm được, và có giá trị bất kể con số ra sao:

- prompt `semantic_analyze` có làm mô hình phát ra `input_facts` + `obligations`
  đúng hình dạng không;
- mô hình có ghim `source_fact_id` không — nếu không, P2 sẽ chặn hàng loạt;
- hai lượt LLM tách rời có thật sự cho `RequestContract` độc lập với chương
  trình không;
- ngân sách, telemetry, phân rã A−B, và toàn bộ đường ghi artifact có chạy đúng
  dưới tải thật không.

Một lỗi tích hợp tìm ra ở đây là lỗi **không** phải trả giá bằng lượt SEALED
thật sau này.

## Đọc kết quả cho đúng

| trường | đọc thế nào |
|---|---|
| `A_generative_executability` | tỉ lệ pilot, **không** phải claim A |
| `B_internal_servable` | tỉ lệ pilot, **không** phải claim B |
| `dung_theo_oracle_doc_lap` | oracle Python độc lập — phần này đáng tin nhất trong cả lượt |
| `A_tru_B_phan_ra` | hữu ích: nó chỉ ra cổng nào đang chặn |
| `phan_bo_that_bai` | hữu ích nhất cho việc sửa lỗi tích hợp |

## Sau lượt này

Hệ **vẫn không được sửa vì kết quả**. Nếu pilot phơi ra một lỗi tích hợp thật
(không phải "hệ trả lời sai"), việc sửa nó là hợp lệ vì SEALED thật chưa tồn
tại — nhưng phải đóng băng lại candidate và ghi rõ, đúng quy trình đã có.

Muốn có số liệu held-out thật cho luận văn: cần **người thứ ba** chọn đề và dựng
ground truth. `CUSTODIAN_HANDOFF.md` và `CUSTODIAN_INTAKE.md` viết sẵn cho việc
đó.
