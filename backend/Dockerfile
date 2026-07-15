FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

EXPOSE 8000

# Tiến hoá schema (Alembic) TRƯỚC khi phục vụ — trên DB bền (Postgres) đây là
# đường DUY NHẤT đổi schema. `exec` để uvicorn thành PID 1, nhận đúng SIGTERM.
CMD alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000
