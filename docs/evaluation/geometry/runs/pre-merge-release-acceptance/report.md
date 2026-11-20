# Pre-Merge Final Acceptance & Root-Cause Verification Run

- **Ngày:** `2026-11-19`
- **Nhánh kiểm định:** `release/axo-pre-merge-final-acceptance`
- **Trạng thái nghiệm thu:** `READY_FOR_OWNER_REVIEW` (`MERGE_STATUS = NOT_MERGED`, `PUSH_STATUS = NOT_PUSHED`, `DOCKER_CONTAINER_RUNTIME = BLOCKED_ENVIRONMENT`, `OFFICIAL_PG_DUMP_RESTORE = BLOCKED_ENVIRONMENT`)
- **Báo cáo đầy đủ:** [AXO-PRE-MERGE-FINAL-ACCEPTANCE-REPORT.md](AXO-PRE-MERGE-FINAL-ACCEPTANCE-REPORT.md)
- **Tệp cấu hình / metadata run:** [run.json](run.json)

## Chỉ mục bằng chứng

- **Gate A (Migration Safety):** [gate-a-migration-safety-matrix.json](results/gate-a-migration-safety-matrix.json) · [gate-a-forensic.log](logs/gate-a-forensic.log)
- **Gate B (Backup/Restore & Application Rollback):** [gate-b-backup-restore-rollback.json](results/gate-b-backup-restore-rollback.json) · [gate-b-backup-restore-rollback.log](logs/gate-b-backup-restore-rollback.log)
- **Gate C (Runtime Environment & Docker Probe):** [gate-c-runtime-environment.json](results/gate-c-runtime-environment.json) · [gate-c-runtime-environment.log](logs/gate-c-runtime-environment.log)
- **Gate D (Git Scope Audit):** [gate-d-scope-audit.json](results/gate-d-scope-audit.json)
- **Gate E & F (Oracle, Live Browser E2E, REA MCP, PG16 Survival):**
  - [gate-e-independent-geometry-oracle.json](results/gate-e-independent-geometry-oracle.json)
  - [gate-e-f-browser-phase1.json](results/gate-e-f-browser-phase1.json)
  - [gate-e-f-browser-phase2.json](results/gate-e-f-browser-phase2.json)
  - [gate-f-rea-mcp.json](results/gate-f-rea-mcp.json)
  - [gate-f-postgres-live-survival.json](results/gate-f-postgres-live-survival.json)
- **Gate G (Regression Suites, Xfail/Skip Audit & Performance):**
  - [gate-g-performance.json](results/gate-g-performance.json)
  - [gate-g-test-and-xfail-audit.json](results/gate-g-test-and-xfail-audit.json)
  - Logs: [seal-verify.log](logs/seal-verify.log), [backend-postgres.log](logs/backend-postgres.log), [backend-geometry.log](logs/backend-geometry.log), [backend-semantic-program.log](logs/backend-semantic-program.log), [backend-other.log](logs/backend-other.log), [backend-replay-demo.log](logs/backend-replay-demo.log), [backend-crash-audit.log](logs/backend-crash-audit.log), [frontend-tsc.log](logs/frontend-tsc.log), [frontend-vite-build.log](logs/frontend-vite-build.log), [frontend-vitest.log](logs/frontend-vitest.log), [docs-ia-audit.log](logs/docs-ia-audit.log)
- **Ảnh bằng chứng tiêu biểu:**
  - [final-acceptance-1920-sb-rename-P.png](images/final-acceptance-1920-sb-rename-P.png)
  - [final-acceptance-1920-422-rollback.png](images/final-acceptance-1920-422-rollback.png)
  - [final-acceptance-1920-cascade-f5.png](images/final-acceptance-1920-cascade-f5.png)
  - [final-acceptance-post-restart.png](images/final-acceptance-post-restart.png)
  - [final-acceptance-vkb-390x460.png](images/final-acceptance-vkb-390x460.png)
  - [final-acceptance-vp-1280x800.png](images/final-acceptance-vp-1280x800.png)
  - [final-acceptance-vp-320x568.png](images/final-acceptance-vp-320x568.png)
  - [final-acceptance-rea-mcp.png](images/final-acceptance-rea-mcp.png)
