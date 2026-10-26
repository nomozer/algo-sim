// Temporary E2E config (not committed): the worktree's own vite.config.ts with only the port and the /api proxy target
// changed, because :3000/:8000 belong to other running servers.
import base from "D:/Documents/projects/algo-sim/.superpowers/worktrees/hybrid-v2-backend-generalization/frontend/vite.config.ts";

const FE = "D:/Documents/projects/algo-sim/.superpowers/worktrees/hybrid-v2-backend-generalization/frontend";
export default {
  ...base,
  root: FE,
  cacheDir: `${FE}/.vite-cache`,
  server: { ...base.server, port: 3291, strictPort: true, host: "127.0.0.1", proxy: { "/api": "http://127.0.0.1:8791" } },
};
