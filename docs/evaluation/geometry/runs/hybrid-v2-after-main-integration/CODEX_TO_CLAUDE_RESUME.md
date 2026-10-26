# Codex → Claude resume (2026-10-26)

Codex hit its usage limit during cleanup. Claude took over from the Git state, not from the narrative. Order kept:
P0 backup → P1 main → P2 interrupted edits → P3 cleanup → P4 backend → P5 tests → P6 handoff.

## Forensic state at takeover

| Question | Evidence | Finding |
|---|---|---|
| Any process still writing? | `Win32_Process` command lines | No backup/copy/git/python writer. Codex app-server idle. Vite on 3172/3173/3191/3197/3198, uvicorn :8000, Chrome PID 2276 viewing `windows-watchdog-recovery/.../OWNER_VISUAL_REVIEW.html` |
| Backup finished? | `IGNORED_ARTIFACT_BACKUP_REPORT.md` | Copy complete vs its manifest (5078/5078); source-side only 103/5078 verifiable ⇒ `IGNORED_ARTIFACT_BACKUP_INCOMPLETE` |
| Was main merged? | `git reflog show main` | **Yes, before the limit:** `main@{2026-10-26 20:50:06 +0700}: merge a9889031…: Fast-forward` from `9978e512`. Backup started 20:54 |
| Recovery worktree clean? | `git status --short` re-run | Clean, HEAD `a9889031` = `main` |
| Three edited files | `git show --stat a9889031` | Committed in `a9889031` (20:49:28), then fast-forwarded into main |

## `CODEX_INTERRUPTED_EDITS_RECOVERED`

Nothing was uncommitted, so nothing needed recovering and no duplicate commit was made. Verified per file: no diff vs
index, no diff vs HEAD, worktree bytes = bytes at `main`.

| File | Blob at `main` | SHA-256 (worktree = main) |
|---|---|---|
| `OWNER_VISUAL_APPROVAL.md` | `fd8615ad` | `4e38c6e3eb29da24ce213bbaf36226cb1e803f6e6ca1033db09dac44a0cb44ed` |
| `owner-visual-go.json` | `3602a167` | `f64a9b18c5640aeed6f4bcb28ae66f16554c26c1ec93a5d3437190bb56d48b19` |
| `run.json` | `e3488b17` | `caeeb190cbb99fef022b6adee146e54a7d4df07bba56e2d73400458710d7cd59` |

Content check: `owner-visual-go.json` quotes the Owner GO for the six existing sphere images of renderer `e047235e`,
bound to T3 candidate `3d6351d8`, with `production_approval: false`, the authorized local sequence (recheck → local
fast-forward → post-merge smoke → safe cleanup → new backend branch → one Hybrid V2 slice) and the constraints (no push,
no live provider, Hybrid opt-in, LLM_ONLY, CACHE_VERSION 130). This matches the takeover instruction; no new authority
was added. `run.json` at `a9889031` still says `main_merge: PREFLIGHT_VERIFIED`, `cleanup: NOT_STARTED`: it was written
38 s before the fast-forward. The run record is updated in this takeover (new keys; the old values stay in Git history).

## Post-merge verification (the missing "post-merge smoke")

Run in `.superpowers/worktrees/local-main-integration` (checks out `main`; clean before and after):

- source identity: `backend/app` tree `280ffac0…` and `frontend/src` tree `f61fe7e9…` identical at `3d6351d8` and `main`;
  `git diff --name-only 3d6351d8 main` touches only `docs/` (12 files) — the Full T3 PASS (12009 / 1417) still describes
  the merged product, so Full T3 was not re-run;
- `freeze_evaluation_candidate.py --verify`: MATCH (118 files, `3850e787d86f81be…`);
- `pytest -k che_do_mac_dinh / cache_version`: 2 passed (LLM_ONLY default, `CACHE_VERSION = "130"` in source);
- root Owner checkout: 79/79 protected files byte-identical to `preflight.json`, no file added or removed since preflight,
  branch `research/hybrid-wave3a-volume-reasoning` HEAD `fe9f5554` unchanged.

Classification: `LOCAL_MAIN_INTEGRATION_VERIFIED` at `a9889031`. No push. No second merge.
