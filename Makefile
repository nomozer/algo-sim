# M17-RC1 — lệnh kiểm tra tái lập được.
# Windows không có `make` sẵn: mọi target đều gọi thẳng script, có thể chạy tay
# đúng dòng lệnh bên dưới nếu không có make.

PY := backend/.venv/Scripts/python.exe
ARTIFACTS := docs/evaluation/m17/rc1

.PHONY: runtime-doctor rebuild-backend catalog-matrix archetype-matrix completeness curriculum-support rc1-tier1 help

help:
	@echo "runtime-doctor   - So khop danh tinh source <-> container dang chay"
	@echo "rebuild-backend  - Build lai backend KEM danh tinh (GIT_SHA/BUILD_TIME)"
	@echo "catalog-matrix   - Sinh ma tran catalog + conformance tu registry"
	@echo "archetype-matrix - RC1-C: coverage 8 slot x 19 target + gap + ledger"
	@echo "completeness     - RC1-D: probe chinh sach so luong thao tac"
	@echo "curriculum-support - W4B-3A: bang ho tro theo chuong trinh (SupportKind)"
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
	$(PY) backend/scripts/catalog_runtime_matrix.py \
	  --json $(ARTIFACTS)/catalog_runtime_matrix.json \
	  --md $(ARTIFACTS)/catalog_conformance_report.md

## RC1-C — coverage 8 archetype slot × 19 target (chạy 77 case qua run_pipeline).
archetype-matrix:
	$(PY) backend/scripts/rc1c_archetype_matrix.py --out $(ARTIFACTS)

## RC1-D — probe chính sách số lượng thao tác (sinh từ registry chính sách).
completeness:
	$(PY) backend/scripts/semantic_completeness_report.py \
	  --json $(ARTIFACTS)/semantic_completeness_report.json \
	  --md $(ARTIFACTS)/semantic_completeness_report.md

## W4B-3A — bảng hỗ trợ theo CHƯƠNG TRÌNH (hướng giáo viên), sinh từ coverage.py.
##   Khác `catalog-matrix` (hướng kĩ sư) và `after-matrix` (hướng sản phẩm).
curriculum-support:
	$(PY) backend/scripts/curriculum_support_report.py \
	  --json docs/evaluation/m17/w4b3a-after/curriculum-support.json \
	  --md docs/evaluation/m17/w4b3a-after/curriculum-support.md

## Tier 1 — deterministic, không gọi LLM, không tốn HTTP budget.
rc1-tier1:
	cd backend && .venv/Scripts/python.exe -m pytest -q
	cd frontend && npx vitest run && npm run build
