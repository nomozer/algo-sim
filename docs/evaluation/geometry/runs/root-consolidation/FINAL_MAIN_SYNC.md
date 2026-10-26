# Main synchronization

Before integration, local `main`, `origin/main` and `git ls-remote origin refs/heads/main` all equal `b7b8358e5f460c6dd873283299882b21f8f67774`.
Root switched non-forcibly from `fe9f5554` to this main after resolving every dirty path.

This commit contains documentation only. Before advancing main, verify its committed detached candidate with the
documentation gate, the explicit changed-path allowlist and equality of the backend/frontend Git trees to `b7b8358e5f460c6dd873283299882b21f8f67774`.
Then fetch, require no remote drift, fast-forward main, perform post-merge smoke and push `origin main:main` without force.

The exact final full SHA cannot be embedded in the same commit that introduces it. The post-push machine receipt
`.superpowers/backups/root-consolidation-20261027/final-verification.json` and local `FINAL_MAIN_SYNC.md` record actual local, fetched and ls-remote SHAs,
root branch/status, final worktree/branch counts, unchanged product trees and snapshot recheck results. Do not treat the
pre-integration equality above as a post-push claim. No research branch or tag is pushed.
