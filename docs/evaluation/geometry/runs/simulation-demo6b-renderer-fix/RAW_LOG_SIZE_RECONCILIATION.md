# Raw-Log Byte-Size & SHA256 Reconciliation (`simulation-demo6b-renderer-fix`)

- **Run ID**: `simulation-demo6b-renderer-fix`
- **Wave ID**: `simulation-demo6b-renderer-fix-w01`
- **Corrects**: `simulation-evidence-repair-w01` (additive correction for prose byte-size table in [`docs/evaluation/geometry/runs/simulation-evidence-repair/report.md`](../simulation-evidence-repair/report.md))
- **Source Repair Branch / Commit**: `research/simulation-evidence-repair` @ `609cb877d9e0177e8408f31c7d3cc0c9cd5f89fc`
- **Original Campaign Commit**: `d86c72031d8fc85cd4eef62d9379cd1690ba1417`
- **Machine Receipt**: [`raw-log-size-reconciliation.json`](raw-log-size-reconciliation.json)

---

## 1. Cause Classification

- **Classification**: `PROSE_REPORTING_METADATA_ERROR_ONLY`
- **All 4 Original Logs 4-Way Byte-Identical**: `true` (`ORIGINAL_RUNTIME == CORRECTIVE_ARCHIVE == GIT_BLOB_AT_609CB877 == CLEAN_CHECKOUT`)
- **Root Cause of Discrepancy**:
  1. [`docs/evaluation/geometry/runs/simulation-evidence-reconciliation/evidence.json`](../simulation-evidence-reconciliation/evidence.json) recorded the true byte lengths of the 4 original T3 logs (`31,647`, `121,261`, `28,606`, `121,261` bytes) alongside their exact SHA256 digests.
  2. In [`docs/evaluation/geometry/runs/simulation-evidence-repair/original-raw-manifest.json`](../simulation-evidence-repair/original-raw-manifest.json) and [`archive-integrity.json`](../simulation-evidence-repair/archive-integrity.json), the machine JSON schemas recorded only SHA256 digests (`e2074c08...`, `bfd6d2ca...`, `013f2e78...`, `47de5827...`) for `original_t3` and omitted a `bytes` field, while `t3/execution.json` recorded `bytes` for the newly executed T3 run (`stdout.log` = `18,257` bytes, `stderr.log` = `332` bytes).
  3. When authoring the prose summary table in [`docs/evaluation/geometry/runs/simulation-evidence-repair/report.md`](../simulation-evidence-repair/report.md) (and `OPUS_CONTINUATION_HANDOFF.md`), the prose table paired the true original SHA256 digests with erroneous byte figures (`17,843`, `1,303`, `18,243`, `332`) conflated from the new `capture.py` T3 run (`332` bytes is the exact byte length of `simulation-evidence-repair/t3/stderr.log`, SHA256 `ccb6bf354a0674eeb1e49df9a880a000b75240079fdb849282bb899d81eeb58c`).
  4. Because two distinct byte sequences cannot share a 256-bit SHA256 digest without a cryptographic collision, direct binary `read_bytes()` inspection across all four storage locations confirms that every archived file and Git blob at `609cb877d9e0177e8408f31c7d3cc0c9cd5f89fc` has the exact true byte lengths `31,647`, `121,261`, `28,606`, and `121,261`.

---

## 2. Four-Way Binary Inspection of Original T3 Logs

All measurements below were computed directly via Python `Path.read_bytes()` and `git show <commit>:<path>` with zero line-ending normalization:

| File | Original Runtime Bytes (`verification/t3/*`) | Corrective Archive Bytes (`raw/original-t3/*`) | Git Blob Bytes (`609cb877:raw/original-t3/*`) | Clean Checkout Bytes (`verify-simulation-evidence-repair`) | Exact Raw SHA256 (All 4 Locations) | CRLF / Lone LF | Historical Git Blob at `d86c7203` (LF-Normalized) | Erroneous Prose Bytes in `simulation-evidence-repair/report.md` |
|---|---:|---:|---:|---:|---|---:|---|---|
| `attempt1-fail.stdout.log` | `31,647` | `31,647` | `31,647` | `31,647` | `e2074c0897550bda185a6f55ea4113e3a8324263fc7a0cf1e2743228207c03f6` | `257` / `126` | `31,390` B (`2620186c4513cb7a9935f83de6397f5aa03fa38e2de4206ece553391701988e4`) | `17,843` (prose error) |
| `attempt1-fail.stderr.log` | `121,261` | `121,261` | `121,261` | `121,261` | `bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5` | `0` / `733` | `121,261` B (`bfd6d2ca0bf9c3f05bf6010dd12a9c949656172434d9579ba24fdc3701be54a5`) | `1,303` (prose error) |
| `attempt2-pass.stdout.log` | `28,606` | `28,606` | `28,606` | `28,606` | `013f2e784e9fa828a055320468afe7137f080d2447615aec3c3d3970a2138e06` | `207` / `126` | `28,399` B (`8274c4c26793ea001f892ee9c90f339f7fdeb93a43b5c92f3c8e409ca547ae6b`) | `18,243` (prose error) |
| `attempt2-pass.stderr.log` | `121,261` | `121,261` | `121,261` | `121,261` | `47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0` | `0` / `733` | `121,261` B (`47de58275e7e069019a5f60938442317568919cd55fcaf2c0cd567fee13589c0`) | `332` (prose error) |

---

## 3. Binary Inspection of `simulation-evidence-repair` New T3 Logs (`t3/*`)

| File | Worktree Bytes | Git Blob Bytes (`609cb877`) | Clean Checkout Bytes | Exact Raw SHA256 |
|---|---:|---:|---:|---|
| `t3/stdout.log` | `18,257` | `18,257` | `18,257` | `d2446b46ba4aba9fae7203cc6be401e820248087430b63b0d7cbe358af0edd33` |
| `t3/stderr.log` | `332` | `332` | `332` | `ccb6bf354a0674eeb1e49df9a880a000b75240079fdb849282bb899d81eeb58c` |

---

## 4. Preservation & Additive Correction Policy

- Historical files in `docs/evaluation/geometry/runs/simulation-coverage-visual-validation/`, `docs/evaluation/geometry/runs/simulation-evidence-reconciliation/`, and `docs/evaluation/geometry/runs/simulation-evidence-repair/` remain **untouched** (`0` bytes modified).
- This report and [`raw-log-size-reconciliation.json`](raw-log-size-reconciliation.json) serve as the authoritative additive correction (`CORRECTED_BY: simulation-demo6b-renderer-fix-w01` in [`docs/EVIDENCE_INDEX.md`](../../../EVIDENCE_INDEX.md)) for the prose byte-size table in `simulation-evidence-repair/report.md`.
