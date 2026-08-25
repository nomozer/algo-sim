FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

# M17-RC1 §A — DANH TÍNH BUILD nướng vào image. Không có nó thì không cách nào
# biết container đang chạy code của commit nào (đã cháy: container chạy
# CACHE_VERSION "7" suốt nhiều milestone mà không ai hay).
ARG GIT_SHA=unknown
ARG BUILD_TIME=unknown
ENV ALGOSIM_GIT_SHA=$GIT_SHA
ENV ALGOSIM_BUILD_TIME=$BUILD_TIME

EXPOSE 8000

# NẠP LẠI KHI SỬA MÃ — chỉ khi được BẬT TƯỜNG MINH (`DEV_RELOAD=1`).
#
# VÌ SAO CẦN: `docker-compose.yml` mount `./backend/app:/app/app`, nên file trên
# đĩa luôn mới. Nhưng uvicorn đã **import** module lúc khởi động và giữ chúng
# trong bộ nhớ, nên sửa `backend/app/**` KHÔNG CÓ TÁC DỤNG GÌ cho tới khi
# restart. Triệu chứng đúng như người dùng mô tả: *"sửa rồi mà nó vẫn nhận bản
# cũ"* — và nó im lặng, không lỗi, không cảnh báo.
#
# `WATCHFILES_FORCE_POLLING` là BẮT BUỘC cho bind mount từ host Windows:
# inotify không lan qua ranh giới ấy, nên không có nó thì `--reload` bật mà
# không bao giờ nạp lại — tức đổi một lỗi im lặng lấy một lỗi im lặng khác.
#
# MẶC ĐỊNH TẮT: `--reload` sinh tiến trình con nên uvicorn thôi là PID 1 và mất
# đường nhận SIGTERM sạch; đó là hành vi cho máy lập trình, không cho lượt đo
# hay bản chạy thật.
ENV DEV_RELOAD=0

# Tiến hoá schema (Alembic) TRƯỚC khi phục vụ — trên DB bền (Postgres) đây là
# đường DUY NHẤT đổi schema. `exec` để uvicorn thành PID 1, nhận đúng SIGTERM.
CMD alembic upgrade head &&     if [ "$DEV_RELOAD" = "1" ]; then       WATCHFILES_FORCE_POLLING=1 exec uvicorn app.main:app --host 0.0.0.0         --port 8000 --reload --reload-dir /app/app;     else       exec uvicorn app.main:app --host 0.0.0.0 --port 8000;     fi
