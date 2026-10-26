# Windows watchdog recovery

## Root cause and classification

Both original tests reproduced FAIL on the unchanged candidate in an ordinary sandbox process. A separate owned-child probe recorded `taskkill /F /PID … /T` returning 1 with `ERROR: Access denied`; the child remained alive, while direct handle termination succeeded. Spawning and timeout detection worked. The failing phase was process-tree termination, not geometry evaluation or console output.

This combines an environment restriction with a harness/runtime ownership defect. `taskkill /T` was the only descendant cleanup mechanism; its fallback killed and reaped only the parent. The reproduction's child PID 29560 remained live after the old watchdog failed; it was explicitly terminated through an owned process handle and observed signaled. Thus this is not classified merely from one isolated PASS or attributed to scheduling without evidence. The exact Windows policy behind taskkill denial is UNKNOWN; ACLs were not changed.

The old test's missing-handle branch also accepted an unobservable process. It now accepts only Windows error 87 (PID no longer exists); access denial fails the observation.

## Fix and boundaries

`run_schema_contract_offline.invoke` now creates Windows workloads through `windows_process_job.WindowsJobProcess`. The OS helper uses a non-inherited kill-on-close Job Object and `STARTUPINFOEX` `JOB_LIST` to attach the command before its initial thread runs. All descendants inherit membership. A separate `HANDLE_LIST` limits stdio inheritance to NUL input and the invocation log. This avoids a spawn/attach race and dependence on taskkill's process enumeration permissions. See [Microsoft's atomic job creation explanation](https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812/) and [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

Normal/nonzero exit codes remain actual command codes. A timeout remains `INCOMPLETE_TIMEOUT`, with no geometry refusal. Cleanup terminates remaining job members even when the parent has already exited and checks job accounting until ActiveProcesses is zero, with a five-second cleanup deadline. The original .3-second and 2-second watchdog tests are unchanged. No retry, timeout inflation, dependency, skip or xfail was added.

OS query/terminate errors and cleanup wait expiration remain `WATCHDOG_TERMINATION_FAILED`; the matrix persists `FAILURE_HARNESS` and leaves later cells NOT_STARTED. Kill-on-close provides exception-path cleanup without changing the failed verdict. Internal review found that an unnormalized cleanup wait could escape persistence; its new regression was observed RED, then GREEN after normalization.

The helper requires Windows 10+ Job List support. Unsupported/restricted job creation fails before workload execution. Other platforms keep the existing process-group watchdog. It is an offline harness fix; backend/app, renderer, schema, refusal taxonomy, CACHE_VERSION 130 and default LLM_ONLY remain unchanged.

## Verification

- Original two watchdog tests: RED on the old implementation, included in every GREEN run.
- Watchdog/receipt suites: 26 PASS, repeated three times in independent pytest processes (78 PASS). One repetition overlapped related schema tests. See `targeted-repetitions.json` for job PID snapshots, total process counts, zero active members, independently observed stopped PIDs and log hashes.
- Parent/child/grandchild sleep processes require no cooperation. The real job snapshots include the interpreter wrapper as well as the three workload PIDs; all job members were gone before return.
- Normal success, actual exit 7, child left by a normally exited parent, nonexistent executable, denied job creation, denied terminate/query and bounded cleanup wait are covered. Permission/termination denial is injected at the Win32 API boundary; this does not claim a real protected-process/ACL test.
- Unicode log read and rename after return exercise stdio closure; related schema/runtime tests: 153 PASS. No file lock or stdout pipe blockage was observed. Arbitrary machine-load behavior is not claimed from these bounded repetitions.
- Internal native API review: no remaining actionable findings after the cleanup-timeout correction. Independent review remains DEFERRED, not PASS.

## Console publication

The previous external wrapper's cp1252 print failure happened after receipt persistence and is separate from watchdog termination. The new run-local `tools/run_t3.py` writes explicit UTF-8 artifacts before printing an ASCII-escaped JSON summary. It preserves the actual gate exit code even if console output fails. Three tests cover strict cp1252 output, success/failure codes and a broken console. Old receipt/log bytes are preserved.
