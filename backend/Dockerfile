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

# Tiến hoá schema (Alembic) TRƯỚC khi phục vụ — trên DB bền (Postgres) đây là
# đường DUY NHẤT đổi schema. `exec` để uvicorn thành PID 1, nhận đúng SIGTERM.
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000
