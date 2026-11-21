"""Fault injection for I06: suspend / resume every llama-server.exe process (Windows NtSuspendProcess / NtResumeProcess).

A suspended llama-server keeps its socket open but never answers, so the product runtime meets its own SLM deadline and
classifies LOCAL_SLM_TIMEOUT — the real failure path, not a mock. Product code untouched.
usage: python suspend_process.py suspend|resume
"""

import ctypes
import subprocess
import sys

PROCESS_SUSPEND_RESUME = 0x0800
pids = [int(l.split(",")[1].strip('"')) for l in subprocess.run(
    ["tasklist", "/FI", "IMAGENAME eq llama-server.exe", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout.splitlines()
    if l.startswith('"llama-server')]
fn = {"suspend": ctypes.windll.ntdll.NtSuspendProcess, "resume": ctypes.windll.ntdll.NtResumeProcess}[sys.argv[1]]
for pid in pids:
    h = ctypes.windll.kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
    assert h, f"OpenProcess failed for {pid}"
    assert fn(h) == 0, f"{sys.argv[1]} failed for {pid}"
    ctypes.windll.kernel32.CloseHandle(h)
print(sys.argv[1], pids)
