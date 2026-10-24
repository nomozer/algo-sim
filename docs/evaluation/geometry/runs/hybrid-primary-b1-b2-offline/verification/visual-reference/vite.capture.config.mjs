// Capture-only: repo config + a private dep-cache dir (shared node_modules/.vite is Codex-ACL'd). No product change.
import base from 'D:/Documents/projects/algo-sim/.superpowers/worktrees/t3-b1b2/frontend/vite.config.ts';
export default { ...base, root: 'D:/Documents/projects/algo-sim/.superpowers/worktrees/t3-b1b2/frontend', cacheDir: 'D:/vcache-claude' };
