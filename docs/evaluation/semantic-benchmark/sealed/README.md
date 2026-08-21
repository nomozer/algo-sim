# `sealed/` — chỗ dành riêng cho SEALED chính thức

Thư mục này **đang trống có chủ đích**. Nó chờ tập 40 case do **custodian thứ
ba, độc lập với tác giả hệ thống** soạn.

Custodian đặt vào đây đúng một file:

```
sealed/cases.json
```

rồi chạy, theo thứ tự:

```bash
cd backend
.venv/Scripts/python.exe scripts/validate_sealed_submission.py \
    ../docs/evaluation/semantic-benchmark/sealed/cases.json
.venv/Scripts/python.exe scripts/seal_benchmark.py
```

`seal_benchmark.py` sinh `sealed/FINGERPRINT.txt`. Từ đó, mọi thay đổi trong
`cases.json` đều bị phát hiện.

Quy trình đầy đủ: `../CUSTODIAN_HANDOFF.md`. Mẫu nộp từng case:
`../CUSTODIAN_INTAKE.md`.

## Không tái sử dụng tập cũ

Tập fingerprint `34a10a9c…` đã lưu ở `../pilot/sealed-pilot-34a10a9c/`. Nó là
**pilot nội bộ**, do chính tác nhân viết hệ soạn, và đã bị chạy bốn lượt với hệ
được sửa dựa trên chính nó. Tính held-out của nó bằng không.

**Đừng chép nó vào đây.** Runner so vân tay, nên nó sẽ *chạy được* — và đó
chính là điều nguy hiểm: số thu về trông như Task 12 nhưng không chứng minh
được gì.
