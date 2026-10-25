import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  /* Cache tối ưu dependency (và kết quả vitest) của RIÊNG checkout này, không phải `node_modules/.vite` mặc định.
   * Worktree và clone của các agent dùng chung `node_modules` của root qua junction/symlink, nên cache mặc định là
   * MỘT thư mục ghi được bởi nhiều user Windows: bản do sandbox Codex tạo (owner `CodexSandboxOffline`, Bunny chỉ có
   * Write+Read) làm `npm run dev` chết với `EPERM … unlink node_modules/.vite/deps/chunk-*.js` mỗi lần Vite cần tối ưu
   * lại. Mỗi checkout có `frontend/` riêng ⇒ cache riêng, đúng chủ. Gitignore: `.vite-cache/`. */
  cacheDir: ".vite-cache",
  server: {
    port: 3000,
    /* W4B-2D §0 — MỘT CỔNG DUY NHẤT, HỎNG THÌ KÊU TO.
     *
     * Mặc định của Vite là nhảy sang 3001/3002/… khi 3000 bận. Với dev thường
     * thì tiện; với kho này thì đó là một nguồn BẰNG CHỨNG SAI đã ship hai lần:
     * `scripts/capture-*.mjs` đều mặc định `--port 3000`, nên khi Vite lặng lẽ
     * nhảy cổng, runner vẫn chụp được ảnh — của một server CŨ đang giữ 3000.
     * Hai artifact phải gỡ vì đúng lỗi đó: `0a71268` (poisoned server) và
     * `7ce27e3` (wrong port). Cùng họ với anti-pattern #14 (ARCHITECTURE_MAP §8):
     * một bản soát "SẠCH" đo nhầm trang.
     *
     * `strictPort` biến lỗi im lặng đó thành lỗi khởi động: 3000 bận ⇒ Vite
     * thoát, người chạy biết ngay phải dọn process cũ. Hạ tầng dev thuần —
     * không đụng build production, không đụng hành vi sản phẩm.
     */
    strictPort: true,
    proxy: {
      // Chuyển tiếp API sang backend (docker compose up -d, cổng 8000)
      "/api": "http://localhost:8000",
    },
  },
  test: {
    // M7.14T: guard offline — mọi fetch trong test đều ném lỗi (0 network call)
    setupFiles: ["./src/test-setup.ts"],
  },
});
