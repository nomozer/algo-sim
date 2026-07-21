# M17-RC1 — lệnh kiểm tra tái lập được.
# Windows không có `make` sẵn: mọi target đều gọi thẳng script, có thể chạy tay
# đúng dòng lệnh bên dưới nếu không có make.

PY := backend/.venv/Scripts/python.exe
ARTIFACTS := docs/evaluation/m17/rc1

.PHONY: runtime-doctor rebuild-backend catalog-matrix rc1-tier1 help

help:
	@echo "runtime-doctor   - So khop danh tinh source <-> container dang chay"
	@echo "rebuild-backend  - Build lai backend KEM danh tinh (GIT_SHA/BUILD_TIME)"
	@echo "catalog-matrix   - Sinh ma tran catalog tu registry (khong viet tay)"
	@echo "rc1-tier1        - Tier 1: toan bo suite offline (khong LLM live)"

## Phát hiện container chạy code cũ. Thoát != 0 khi lệch.
##   Chạy tay: backend/.venv/Scripts/python.exe backend/scripts/runtime_doctor.py
runtime-doctor:
	$(PY) backend/scripts/runtime_doctor.py --json $(ARTIFACTS)/runtime_identity.json

## Build lại backend KÈM danh tính build — thiếu bước này thì doctor không so
## được git SHA (chỉ so được cache/hash).
##   Chạy tay: GIT_SHA=$$(git rev-parse HEAD) BUILD_TIME=$$(date -u +%FT%TZ) \
##             docker compose up -d --build --force-recreate backend
rebuild-backend:
	GIT_SHA=$$(git rev-parse HEAD) BUILD_TIME=$$(date -u +%FT%TZ) \
	  docker compose up -d --build --force-recreate backend

## Ma trận catalog sinh TỪ REGISTRY (không hard-code danh sách target).
catalog-matrix:
	$(PY) backend/scripts/catalog_runtime_matrix.py --json $(ARTIFACTS)/catalog_runtime_matrix.json

## Tier 1 — deterministic, không gọi LLM, không tốn HTTP budget.
rc1-tier1:
	cd backend && .venv/Scripts/python.exe -m pytest -q
	cd frontend && npx vitest run && npm run build
