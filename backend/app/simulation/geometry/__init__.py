# -*- coding: utf-8 -*-
"""Geometry kernel — nhân hình học không gian CHÍNH XÁC và TẤT ĐỊNH.

Bốn tầng, phụ thuộc một chiều, không được đảo:

    exact       kiểu + số học ℚ + lỗi fail-closed
      ↑
    predicates  đúng/sai — KHÔNG dựng gì, KHÔNG epsilon
      ↑
    kernel      phép DỰNG (giao tuyến, hình chiếu, chân đường vuông góc)
      ↑
    measure     đại lượng — chỗ DUY NHẤT vô tỉ được phép xuất hiện

`predicates` cố ý **không** phụ thuộc `kernel`: `postconditions` gọi vị từ để
kiểm chứng, và nếu vị từ dựa vào chỗ dựng thì oracle đang kiểm chính cái nó vừa
dựng ra.

Nhân này **không biết gì về LLM**, không import `app.ai`. Đó là điều kiện để
ranh giới R0 kiểm được bằng mắt: LLM nói *"lấy giao tuyến của (SAB) và (SCD)"*,
nhân tự tính; LLM không có đường nào chạm vào toạ độ kết quả.
"""
from .exact import (  # noqa: F401
    ERR_CHUA_TRONG,
    ERR_SONG_SONG,
    ERR_THANG_HANG,
    ERR_TRUNG_DIEM,
    ERR_VECTO_KHONG,
    GeometryError,
    Line3,
    Plane3,
    Point3,
    Vec3,
    det3,
    hf,
)
