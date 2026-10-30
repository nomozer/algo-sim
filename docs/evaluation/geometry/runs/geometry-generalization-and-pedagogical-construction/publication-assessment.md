# W4 publication assessment — BLOCKED on one Owner decision (synthetic test vector)

Scanner: `backend/scripts/check_publication_safety.py`. It was not modified, and no exception was approved by the agent.

| scan | result |
|---|---|
| `--range e5dc3d28..HEAD` (W4) | 1 violation, now `exception=PENDING_OWNER_DECISION` → **BLOCKED** |
| `--head` (W4 tip) | 104 violations, all historical `PENDING` entries; **0 unexcepted** |
| `--head` (pre-W4 `main`, recorded at `996f114b`/`e5dc3d28` lineage) | 105 violations: 104 pending plus **1 unexcepted** `GOOGLE_API_KEY` |

**The single finding:**
- Location: blob `24d45cd6304f1194340c27e043c402fca1762052` of `backend/tests/geometry/test_docs_information_architecture.py`, line 396, rule `GOOGLE_API_KEY`.
- First committed in `039fa606`, the W4 cache 130→131 pin edit. SHA-256 `b74ee7c7…a4512d`, 20 710 bytes.
- Content: the **deliberately fake** key written by `test_fi_14_secret_leak_rejected`, which checks that the docs audit catches secret-shaped values. Its key text is byte-identical to the line already on `origin/main` (blob `0f726dfb`, line 395), which the pre-W4 head scan already reported unexcepted.
- No real credential, token or personal data. The scanner's other rules give 0 findings in this blob.

**Why it appeared, and what was done:**
- The scanner keys on (path, blob). Any edit of that test file creates a "new" blob carrying the same fake key.
- `00d09f3b` now builds the value at runtime (`"AIza" + …`), which is the technique the scanner file uses for itself. The runtime value is byte-identical and the test passes (42/42). The tip therefore no longer carries the literal, and the W4 head scan drops the pre-existing unexcepted finding.
- The historical blob remains in `039fa606…00d09f3b`. History is not rewritten.

**Options for the Owner:**

1. **Recommended: approve exactly this blob** with one command run by the Owner, from the W4 worktree root:

   ```powershell
   $p = "docs\evaluation\geometry\runs\publication-safety-remediation\publication_exceptions.json"
   $t = Get-Content -Raw $p
   $t = [regex]::Replace($t, "(`"blob`": `"24d45cd6304f1194340c27e043c402fca1762052`"[^}]*?`"owner_decision`": `")PENDING_OWNER_DECISION", '${1}APPROVED_BY_USER')
   [IO.File]::WriteAllText((Resolve-Path $p), $t)
   ```

   It is keyed on the blob SHA, cannot cross an entry and does not reformat the file. After it runs, the range scan must
   give 0 violations, and integration can proceed under the scoped W4 rule.
2. Decline: integration stays blocked. The alternative would be a history-free publication candidate, which needs its
   own GO.

`APPROVED_BY_USER` is never written by the agent (AGENTS.md).
