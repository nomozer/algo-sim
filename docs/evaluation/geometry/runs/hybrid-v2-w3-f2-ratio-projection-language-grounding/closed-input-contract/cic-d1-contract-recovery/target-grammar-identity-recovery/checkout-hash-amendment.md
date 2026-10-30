# Checkout hash normalization amendment

Clean detached 6a09c06a exposed a harness defect: Git autocrlf checks out cases.json as CRLF, while preregistration hashed its original LF bytes. The single frozen-input integrity test failed (expected 5f94f71ec4304af41b17783d91ad46e87dbc53e466a8ff8978762e1683ba130d; raw CRLF checkout af6f95738ddedd5c40e1c460d415fac1a395d2b031bd0af98a6c7638c3acdbda). Independently read Git blob at 6a09c06a and verified its SHA-256 equals the preregistered hash. Input and oracle bytes in Git remain unchanged.

The integrity assertion now normalizes CRLF to LF, as all existing historical case integrity checks in this suite already do. This changes only the cross-platform test harness, not the frozen expected hash, cases, product or locked V2 oracle. The full compatibility run will use a clean detached source tree at the subsequent normal commit. The earlier green.json still accurately reports the original worktree measurement.
