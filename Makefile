# M17-RC1 — lệnh kiểm tra tái lập được.
# Windows không có `make` sẵn: mọi target đều gọi thẳng script, có thể chạy tay
# đúng dòng lệnh bên dưới nếu không có make.

PY := backend/.venv/Scripts/python.exe
ARTIFACTS := docs/evaluation/m17/rc1

.PHONY: runtime-doctor rebuild-backend rc1-tier1 help

help:
	@echo "runtime-doctor   - So khop danh tinh source <-> container dang chay"
	@echo "rebuild-backend  - Build lai backend KEM danh tinh (GIT_SHA/BUILD_TIME)"
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

## ⛔ BỐN TARGET ĐÃ GỠ (FINAL_DEAD_EVALUATION_CLEANUP, 2026-09-02):
##   catalog-matrix · archetype-matrix · completeness · curriculum-support
##
## Cả bốn gọi script đo DANH MỤC 24 TARGET TIN HỌC. Danh mục ấy gỡ ở
## LEGACY_INFORMATICS_REMOVAL, nên bốn script đã CHẾT KHI IMPORT từ trước —
## `make catalog-matrix` trả ModuleNotFoundError chứ không phải một ma trận.
## Artifact chúng từng sinh vẫn còn nguyên trong `docs/evaluation/` như bằng
## chứng của thời điểm đo. Đừng viết lại chúng sang hình học: bộ đo hình học
## là `scripts/run_geometry_dev_evaluation.py`, `run_sealed_evaluation.py`,
## `replay_demo_cases.py` — xem CLAUDE.md §4.

## Tier 1 — deterministic, không gọi LLM, không tốn HTTP budget.
rc1-tier1:
	cd backend && .venv/Scripts/python.exe -m pytest -q
	cd frontend && npx vitest run && npm run build
