# E2E and refusal matrix

| Scope | Evidence | State |
|---|---|---|
| Windows normal/nonzero invocation | Actual process exit and log tests | PASS targeted |
| Timeout with parent, child and grandchild | Job accounting + observed PID handles, 3 independent repetitions | PASS targeted |
| Parent exit before child cleanup | Actual child handle observation | PASS targeted |
| Missing executable / denied job creation | Spawn failure, no workload marker | PASS targeted |
| Denied terminate/query / cleanup wait timeout | Win32 fault injection, failure persistence | PASS targeted |
| Runtime failure vs geometry refusal | INCOMPLETE_TIMEOUT / FAILURE_HARNESS retained | PASS targeted |
| cp1252 / broken console | UTF-8 receipt persists, actual exit retained | PASS targeted |
| Sphere-plane geometry | Prior exact oracle 5/5, unchanged source/evidence | REUSED |
| New Hybrid vertical slice | P7 gated on main integration | NOT_STARTED |
| Live NL extraction | No provider approval/calls | UNKNOWN |
| Independent holdout/review | No new independent evidence | DEFERRED / NOT_RUN |
