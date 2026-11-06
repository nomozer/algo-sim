# Handoff — axo-postmerge-consolidation

- Nhánh `chore/axo-postmerge-branding-consolidation` (từ `main` 64847c1e), worktree `.superpowers/worktrees/axo-postmerge-consolidation`.
  Commit: 9904265b (branding + scope doc), 14810326 (đóng băng lại candidate), commit tài liệu run. **Chưa merge, chưa push.**
- Tab trình duyệt: favicon Axo `frontend/public/favicon.svg` (blob `0ff1b07e`, cùng hình học với `AxoMarkGeometry`) + tiêu đề
  theo trang từ `frontend/src/branding.ts`. Đừng gỡ favicon theo bản ghi cũ "xoá favicon" (f89a1a8b là favicon AlgoSim cũ).
- Seal: `--verify` MATCH ở nhánh này; `main` hiện ĐỎ (`product_commit_sha` 8db058d3 không có trên `main`) cho tới khi nhánh này vào.
- Kiểm lại identity: `cd frontend && npm run build && node scripts/axo-branding-browser-check.mjs --dist dist --out <fresh> --expect-axo`.
- Bằng chứng của worktree tích hợp: lưu trữ riêng tư `algo-sim-private-archive/axo-hybrid4-integration-2026-11-07/` (cạnh thư mục
  kho): `files/`, `MANIFEST.json`, `SHA256SUMS`, `integration-axo-hybrid4-reliability.bundle` (blob đã đánh dấu — không đẩy lên đâu).
  Kiểm: `tr -d '\r' < SHA256SUMS | sha256sum -c --quiet -` và `git bundle verify <bundle>`.
- Chờ chủ kho: xoá thư mục còn sót `.superpowers/worktrees/axo-hybrid4-integration/` (report §E, §K.1); sao lưu ngoài máy;
  merge/push nhánh này.
- Task sau đề xuất: `docs/architecture/AXO_RESEARCH_SCOPE.md §6`.
