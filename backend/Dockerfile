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

# DEV_AUTO_REFRESH (2026-09-15) — NHÃN để quyết định build lại bằng ĐẦU VÀO IMAGE,
# không bằng Git HEAD. `image-inputs-sha256` là dấu vân tay tất định của đúng
# những file các lệnh COPY ở trên chép vào image mà bind mount của compose KHÔNG
# che (`backend/app` bị che, nên nó KHÔNG nằm trong dấu vân tay — sửa mã ứng dụng
# không đòi build lại). Thẩm quyền: `scripts/dev_backend.py`.
#
# Đặt SAU `pip install` và các COPY: đổi nhãn không làm hỏng cache lớp dependency.
# Không truyền thì nhãn là `unknown` — launcher đọc là CHƯA BIẾT, không phải KHỚP.
ARG REQUIREMENTS_SHA256=unknown
ARG IMAGE_INPUTS_SHA256=unknown
LABEL org.algosim.backend.git-sha=$GIT_SHA       org.algosim.backend.build-time=$BUILD_TIME       org.algosim.backend.requirements-sha256=$REQUIREMENTS_SHA256       org.algosim.backend.image-inputs-sha256=$IMAGE_INPUTS_SHA256

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
