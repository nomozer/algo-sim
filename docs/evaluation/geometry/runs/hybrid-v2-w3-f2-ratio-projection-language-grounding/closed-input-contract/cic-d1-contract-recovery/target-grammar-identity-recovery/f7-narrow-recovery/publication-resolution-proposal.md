# Publication resolution proposal: the simplest one-time path (awaiting Owner decision)

**Status:** `PUBLICATION_BLOCKED`. The two entries for the `1490e3cd` logs are in the registry as
`PENDING_OWNER_DECISION` (commit `a0fd2377`). They are verified in `publication-exception-verification.json`.
`AGENTS.md:49` stays in force, so the agent does not write the approval value. Two earlier manual JSON edits failed:
one was never saved, and the other changed all 29 entries and was then reverted.

## Recommended: option 1, one Owner-run command (no JSON editing, no policy change)

The Owner pastes this into PowerShell, from the research worktree root:

```powershell
$p = "docs\evaluation\geometry\runs\publication-safety-remediation\publication_exceptions.json"
$t = Get-Content -Raw $p
foreach ($b in '395896a0a850d77fab2be0062023d01154c2b9ef','21a012bb06690aeb64cfd87ab97c4e2f35aa9d7a') {
  $t = [regex]::Replace($t, "(`"blob`": `"$b`"[^}]*?`"owner_decision`": `")PENDING_OWNER_DECISION", '${1}APPROVED_BY_USER') }
[IO.File]::WriteAllText((Resolve-Path $p), $t)
```

**What the command does:**
- It is keyed on the two exact blob SHAs. The pattern cannot cross an entry boundary (`}`), so the other 27 entries
  cannot change.
- It does not reformat the file.
- I dry-ran it on a scratch copy of the `a0fd2377` file: exactly 2 `owner_decision` values became approved, and no
  other line changed. The copy was then deleted. No repository file was touched.

**Why this needs no policy change:** the Owner executes the command, so the approval is still Owner-written.

**After the Owner runs it**, the agent will:
- verify the semantic diff (exactly two values on those two blobs);
- run `check_publication_safety.py --range 996f114b..HEAD`, which must give 0 violations;
- commit;
- run freeze → 11 identity tests → Full T3 → final independent review.

The Wave 3 replay and T0/T1/T2 receipts stay valid if the product is unchanged.

## Alternatives

| option | what changes | impact |
|---|---|---|
| 2. **Policy change**: an agent may write `APPROVED_BY_USER` when an Owner GO names exact (path, blob, sha256) | `AGENTS.md:49`, the scanner docstring and the registry `policy` text | Fully hands-off for the Owner. But it weakens a deliberate guard: an agent could then self-approve after misreading a GO. Not recommended for a one-time need. |
| 3. **Clean publication candidate** | A new branch from `main` with the final tree as fresh commits, without the two raw logs (or with sanitized copies and a correction note) | No exceptions are needed. The research branch stays private and unchanged. Costs: evidence that cites research SHAs (`1490e3cd`, `ae81b65e`, `dd17fbfb`, …) does not resolve publicly; historical receipts are altered in the published tree; and it needs a full new scan, T3 and evidence-index pass. This is the heaviest option. |
| 4. **Leave blocked** | nothing | No freeze, no T3, no integration. |

**Decision needed:** option 1 (run the command), 2, 3 or 4. Until then, publication stays blocked and nothing is frozen.
