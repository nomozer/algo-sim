# Publication risk assessment, Owner decision D4 (read-only): BLOCKED_PENDING_OWNER_DECISION

**Method.** I read the two blobs directly with `git cat-file` and recomputed their size and SHA-256. I checked the
scanner rules (`check_publication_safety.py::RULES`) and did a contextual pattern count. Only counts are recorded
here, never values. No blob, history, registry, scanner or approval was changed, and nothing was written to
`publication_exceptions.json`.

| | entry 1 | entry 2 |
|---|---|---|
| path | `…/source-grammar-adjudication/gate-d-full-backend-pytest.log` | `…/source-grammar-adjudication/gate-d-pre-patch-5e44d5da-identity-12.log` |
| first commit | `1490e3cd` (research branch only; on no remote branch) | `1490e3cd` (same) |
| blob | `395896a0a850d77fab2be0062023d01154c2b9ef` | `21a012bb06690aeb64cfd87ab97c4e2f35aa9d7a` |
| SHA-256 / bytes | `1f9bb9a8…acc2205e` / 24 497 (matches proposal) | `c17f5fa8…185dac5` / 2 981 (matches proposal) |
| data type | raw pytest log (test summary lines and one pytest warning) | raw pytest log (12-node identity run and the same warning) |
| exact scanner finding | `PY_TRACEBACK` ×5: lines 281, 282, 284, 286, 289 | `PY_TRACEBACK` ×5: lines 6, 7, 9, 11, 14 |
| traceback content | `PytestUnhandledThreadExceptionWarning`: a stdlib subprocess reader thread hit `UnicodeDecodeError` (cp1252). Frames come only from `threading.py`, `subprocess.py` and `cp1252.py`. No product stack, no provider output. | same |
| credentials / tokens / keys / email | 0 matches for key, token, bearer, private-key, password and email patterns. The scanner's credential rules give 0 findings. | 0 / 0 |
| personal identifiers | absolute local paths. 4 of them contain the Windows profile (account) name; the rest are repository paths. | same kind; 4 contain the profile name |
| identifiability | The profile name is a local account name and links the log to the Owner's machine. **The same identifier is already on `origin/main`** (`996f114b`): 138 files at the tip and about 100 commits match the profile-path pattern. | same |

**Exception scope.** Each proposed entry exempts exactly `(path, blob, sha256, rules=[PY_TRACEBACK])`, and only
when the Owner writes `owner_decision = APPROVED_BY_USER`. Any changed byte or new content is not covered, because
the scanner keys on path plus blob. An exception lets the scanner pass with disclosure; it does not redact anything.

**Can this be handled safely without rewriting history?**
- **Forward commit that deletes or redacts the logs.** No. The blobs stay in `996f114b..HEAD`, and the range scan
  still blocks.
- **Owner-approved exact exceptions.** Yes, for the scanner gate. The cost is publishing two stdlib warning tracebacks
  and local paths that are already present on `origin/main`.
- **Separate clean publication candidate.** Possible but costly. This would be a new branch from `main` carrying the
  final tree as new commits, without the research commits and without these two raw logs (or with sanitized copies
  plus a correction note). It needs no history rewrite, because the research branch stays private and unchanged.
  It has two costs:
  - Evidence chains that cite research commit SHAs (`1490e3cd`, `ae81b65e`, …) would not resolve publicly.
  - It removes or alters historical receipts in the published tree, so it needs its own Owner GO and its own
    scanner, T3 and evidence-index pass.

  It is not performed here.

**Recommendation.** I recommend APPROVE for each entry. This is a recommendation only, not an approval.
- **Entry 1: APPROVE.** The traceback is a low-sensitivity stdlib decoding diagnostic, with no secret and no product
  stack. The only personal data is a local account name that `origin/main` already discloses. The exception is
  cryptographically narrow.
- **Entry 2: APPROVE**, for the same reasons. The blob is smaller and has the same warning.
- **Condition for both:** the Owner explicitly accepts publishing that local-path disclosure. If the Owner does not
  want any further copy of the profile name published, DECLINE both. The only safe route is then the separate clean
  publication candidate described above, under its own GO.

Until the Owner writes `APPROVED_BY_USER`, or an authorized remediation passes the scanner, publication stays
**BLOCKED**. Replay, T0/T1/T2, freeze and Full T3 are not run.
