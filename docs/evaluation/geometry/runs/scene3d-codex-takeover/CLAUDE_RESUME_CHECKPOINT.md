# Claude resume checkpoint — Codex #2 → Claude (2026-10-26)

Checkpoint A of the Owner's "resume from Codex limit" prompt. Written before any product edit.
This file sits in `scene3d-codex-takeover/` because the Owner named this path; the run directory of
the work being resumed is `../claude-to-codex-takeover/`.

## 1. Source of truth at takeover (14:36 +07)

Lineage is linear — nothing was lost between agents:

| step | commits | worktree | branch |
|---|---|---|---|
| base | `08929b89` | — | — |
| Codex #1 | `7c4162cc` … `11188e7a` (09:26) | `scene3d-codex-takeover` | `research/scene3d-codex-takeover` |
| Claude | `f3ae506c` … `3dcd6d9f` (11:26) + 112 uncommitted files | `s3d-hybrid-v2` | `research/scene3d-to-hybrid-v2-replacement` |
| Codex #2 | `f9e86972`, `75c89ade`, `e336e0df` (14:06) + 69 untracked evidence files (to 14:15) | `s3d-hybrid-v2-codex` | `research/scene3d-hybrid-v2-codex` |
| **Claude resume** | from `e336e0df` | `s3d-hybrid-v2-claude` (new) | `research/scene3d-hybrid-v2-claude-resume` (new) |

`11188e7a` is an ancestor of `3dcd6d9f`; `3dcd6d9f` is an ancestor of `e336e0df`.
Root checkout stays on `research/hybrid-wave3a-volume-reasoning` @ `fe9f5554` with the Owner's
uncommitted UI work (19 tracked files, 60 untracked paths) — not touched, not staged.

Running processes: no pytest / vitest / full-gate process alive. Two idle `codex.exe app-server`
processes and three Vite dev servers (3172, 3173, 3191) are alive and were left alone. Because a Codex
session could resume, Claude does **not** write into `s3d-hybrid-v2-codex` or `s3d-hybrid-v2`; it works in
a new worktree.

## 2. Preservation evidence

- Claude's 112 uncommitted files in `s3d-hybrid-v2`: re-hashed against
  `.superpowers/backups/claude-to-codex-20261026-133857/manifest.json` → `ok=112 mismatch=0`;
  archive `uncommitted.zip` sha256 `8db6107d…a2f2401ca01` (unchanged).
- New backup `.superpowers/backups/codex-to-claude-20261026-1440/` (ignored, outside Git):
  - `codex-untracked.tar` sha256 `f056c48f…aeaf70` + per-file `codex-untracked.sha256` (69 files)
  - Owner root tree: `root-modified-raw.tar` `d9c16203…7b49b01` (raw bytes of 19 modified tracked files),
    `root-untracked.tar` `df024143…83f9be`, `root-owner-tracked.patch` `326493ea…aeac953`,
    `root-files.sha256` (79 files), `root-status.txt`, `codex-status.txt`.
- Transfer Codex worktree → Claude worktree: tar extract, `sha256sum -c` → **69/69 byte-identical**.

## 3. Full T3 at "27%" — what actually happened

Launcher: `.superpowers/claude-to-codex-t3-e336e0df-owned/running.json` PID 22628, head `e336e0df`,
started 07:08:16Z. PID 22628 **no longer exists**; `stdout.log` last write 14:14:14; `stderr.log` empty;
**no receipt**. Status: `INCOMPLETE` (killed with the Codex session) — not PASS, not a FAIL verdict.
An earlier attempt failed before any test ran (`../claude-to-codex-takeover/t3-startup-failure.json`,
git ownership preflight).

Pytest `-q` prints names only at the end, so failures were located by mapping character positions
of the 3273 progress characters onto `pytest --co -q` order of the same clean tree
(`verify-s3d-hybrid-v2-codex` @ `e336e0df`, 12000 tests), then confirmed by re-running exactly those ids:

| pos | test | reproduced | class |
|---|---|---|---|
| 1678 | `test_docs_information_architecture.py::test_inv_15_stable_rules_contain_no_mutable_state` | FAIL | real docs-gate failure: `AI_CONTEXT_BUNDLE.md` 303 lines > 300 (Codex added 3 lines) |
| 1680 | `test_docs_information_architecture.py::test_inv_17_handoff_bundle_under_line_limit` | FAIL | same root cause |
| 2088–2089 | `test_generalized_goal_entry.py::test_length_goal_refusal[…]` | `x` | declared xfail, not a failure |
| 3228 | `test_hybrid_backend_integration.py::test_version_constants_surface_fingerprints_and_historical_receipt_preservation` | FAIL | `TEST_OR_HARNESS_DEFECT`: Codex bumped `ENGINE_VERSION` to `/12` (new `SKEW_CLAIM_CONTRADICTED` refusal — bump justified) but left three test pins and the docs at `/11` |

The remaining 73 % of pytest and all of vitest / build / replay / audit were `UNKNOWN` at takeover; see
`../claude-to-codex-takeover/claude-resume/` for the diagnostic full-pytest run.

## 4. LF/CRLF — root cause and scope

- `core.autocrlf=true` is set at **system** level (`C:/Program Files/Git/etc/gitconfig`); no repo-wide
  `.gitattributes`. On `add`, CRLF is normalised to LF in the blob; on checkout, LF becomes CRLF.
- Evidence manifests (`FIXTURE_MANIFEST.json`, `BROWSER_EVIDENCE.json`, browser receipts) hash **raw bytes**.
  Measured on the 98 paths Codex listed in `scene3d-to-hybrid-v2-replacement/.gitattributes`:
  53 text files written with CRLF had an LF blob (blob ≠ manifest, e.g. `cube_positive.json`
  manifest `6c6ad252…` = disk, blob `dfe57fc5…`); 11 written with LF were turned into CRLF by a fresh
  checkout (`verify-s3d-hybrid-v2-codex`); 34 PNGs unaffected.
- The product candidate hash is **not** affected: `freeze_evaluation_candidate.py::bam_noi_dung`
  normalises CRLF→LF before hashing.
- Fix (completes Codex's uncommitted work, repo convention of per-run `.gitattributes`, as in 10 earlier runs):
  `claude-to-codex-takeover/.gitattributes` `* -text` (Codex); per-path `-text` list in
  `scene3d-to-hybrid-v2-replacement/.gitattributes` (Codex) + two lines for Codex's untracked
  `official-inputs-e336e0df*` (52 + 3 LF files, same raw-hash manifest). No global `-text`/`eol=lf`,
  no change to source-code or ordinary fixture policy.
- 14 files the fresh Claude checkout had already turned into CRLF were restored from the worktree that
  wrote them (`s3d-hybrid-v2` / `s3d-hybrid-v2-codex`), then `git add --renormalize`; every staged blob
  was compared with the disk bytes: equal (except the `.gitattributes` config file itself).
- Not done: other historical runs without `-text` may carry the same latent mismatch; not audited
  (out of this takeover's scope).

## 5. Rules kept

No merge, no push, no branch/worktree deletion, no live model, `LLM_ONLY` default unchanged,
`CACHE_VERSION` unchanged by this checkpoint, no ACL change, no `reset`/`clean`/`restore`,
no `Co-Authored-By` trailer.
