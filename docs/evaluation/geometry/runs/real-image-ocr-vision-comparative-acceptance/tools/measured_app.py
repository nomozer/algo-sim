"""Loopback-only measurement wrapper; never imported by the product entry point.

Run with uvicorn measured_app:app --host 127.0.0.1, PYTHONPATH=backend;tools.
Diagnostics sample FastAPI and every descendant process, without recording request data.

The OCR interpreter is a Windows venv `python.exe`: a ~4 MiB launcher that starts the real
interpreter as ITS child. `Popen.pid` is therefore the launcher, and the models live in the
grandchild. Sampling only `local_ocr_worker_pid()` under-reports OCR memory by two orders of
magnitude, so this wrapper walks the whole process tree below FastAPI.
"""
import ctypes
from ctypes import wintypes
import os
import threading
import time

assert os.environ.get("ALLOW_LIVE_AI") == "0"
from app.main import app
from app.ingestion import local_ocr as ocr

failure_events = []


@app.middleware("http")
async def record_failure(request, call_next):
    try:
        return await call_next(request)
    except Exception as error:
        original = getattr(error, "orig", None)
        failure_events.append({"path": request.url.path, "exception_type": type(error).__name__,
                               "original_type": type(original).__name__ if original else None,
                               "sqlite_errorname": getattr(original, "sqlite_errorname", None),
                               "database_locked": "database is locked" in str(original),
                               "time": time.perf_counter()})
        raise


@app.get("/__evaluation/failures")
def failures():
    return {"events": failure_events[-40:]}


class Counters(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in
        ("peak_rss", "rss", "peak_pool", "pool", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile")
    ]


class ProcessEntry(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD), ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG), ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_char * 260)]


kernel = ctypes.windll.kernel32
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
kernel.Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
psapi = ctypes.windll.psapi
psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
INVALID_HANDLE = wintypes.HANDLE(-1).value


def memory(pid):
    if pid is None:
        return None
    handle = kernel.OpenProcess(0x1000 | 0x10, False, pid)
    if not handle:
        return None
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return None
        return {"rss_mib": counters.rss / 1048576, "process_lifetime_peak_rss_mib": counters.peak_rss / 1048576}
    finally:
        kernel.CloseHandle(handle)


def processes():
    """{pid: (parent_pid, exe_name)} for every process visible to this user."""
    snap = kernel.CreateToolhelp32Snapshot(0x2, 0)
    if not snap or snap == INVALID_HANDLE:
        return {}
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        table = {}
        ok = kernel.Process32First(snap, ctypes.byref(entry))
        while ok:
            table[entry.th32ProcessID] = (entry.th32ParentProcessID, entry.szExeFile.decode("mbcs", "replace"))
            ok = kernel.Process32Next(snap, ctypes.byref(entry))
        return table
    finally:
        kernel.CloseHandle(snap)


def descendants(root, table):
    """Parent links only; a pid recycled by an unrelated parent is not followed."""
    found, frontier = [], [root]
    while frontier:
        parent = frontier.pop()
        for pid, (ppid, _name) in table.items():
            if ppid == parent and pid != root and pid not in found:
                found.append(pid)
                frontier.append(pid)
    return found


class MemoryStatus(ctypes.Structure):
    _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD)] + [
        (name, ctypes.c_ulonglong) for name in
        ("total_phys", "avail_phys", "total_page", "avail_page", "total_virtual", "avail_virtual", "avail_extended")]


def machine():
    """Whole-machine context: other applications share this host, so latency is only comparable with it."""
    status = MemoryStatus()
    status.dwLength = ctypes.sizeof(status)
    kernel.GlobalMemoryStatusEx(ctypes.byref(status))
    idle, kern, user = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
    kernel.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kern), ctypes.byref(user))
    ticks = lambda ft: (ft.dwHighDateTime << 32) | ft.dwLowDateTime
    return {"available_physical_mib": status.avail_phys / 1048576, "total_physical_mib": status.total_phys / 1048576,
            "logical_cpus": os.cpu_count(), "cpu_idle_ticks": ticks(idle), "cpu_total_ticks": ticks(kern) + ticks(user)}


samples = []
sample_lock = threading.Lock()
sampling = True


def sample():
    fastapi = memory(os.getpid())
    table = processes()
    tree = []
    for pid in descendants(os.getpid(), table):
        usage = memory(pid)
        if usage:
            tree.append({"pid": pid, "parent_pid": table[pid][0], "exe": table[pid][1], **usage})
    child_rss = sum(p["rss_mib"] for p in tree)
    return {"time": time.perf_counter(), "fastapi": fastapi, "launcher_pid": ocr.local_ocr_worker_pid(),
            "descendants": tree, "descendant_rss_mib": child_rss,
            "combined_rss_mib": fastapi["rss_mib"] + child_rss if fastapi else None}


def monitor():
    while True:
        if sampling:
            row = sample()
            with sample_lock:
                samples.append(row)
                if len(samples) > 60000:
                    del samples[:10000]
        time.sleep(0.025)


threading.Thread(target=monitor, daemon=True).start()


@app.get("/__evaluation/resources")
def resources():
    with sample_lock:
        rows = samples[:]
    return {"pid": os.getpid(), "current": sample(), "samples": rows, "machine": machine(), "sampling": sampling,
            "ocr_cache_entries": len(ocr._CACHE), "ocr_cache_limit_base": ocr._CACHE_MAX,
            "worker_started_at": ocr._WORKER.started_at if ocr._WORKER else None,
            "sample_interval_ms": 25, "units": "MiB", "live_ai": os.environ["ALLOW_LIVE_AI"]}


@app.post("/__evaluation/reset")
def reset(cold: bool = False, keep_caches: bool = False):
    """cold: stop the OCR worker. keep_caches: only restart the sample window (cache-hit runs)."""
    before = [p["pid"] for p in sample()["descendants"]]
    if cold:
        ocr.shutdown_local_ocr()
    if not keep_caches:
        ocr.clear_local_ocr_cache()
        from app.ai.local_geometry_parser import clear_local_geometry_parser_cache
        clear_local_geometry_parser_cache()
    with sample_lock:
        samples.clear()
    return {"cold": cold, "keep_caches": keep_caches, "launcher_pid": ocr.local_ocr_worker_pid(),
            "descendant_pids_before": before}


@app.post("/__evaluation/sampler")
def sampler(enabled: bool):
    """Pause the 25 ms sampler so its own cost on request latency can be measured (A/B)."""
    global sampling
    sampling = enabled
    return {"sampling": sampling}


@app.get("/__evaluation/alive")
def alive(pids: str):
    """Which of the given pids still exist as python processes (orphan check after worker shutdown)."""
    table = processes()
    return {"alive": [pid for pid in map(int, filter(None, pids.split(",")))
                      if pid in table and "python" in table[pid][1].lower()]}


@app.post("/__evaluation/crash_worker")
def crash_worker():
    """Kill only the launcher, as an external crash would; the product must recover on the next request."""
    pid = ocr.local_ocr_worker_pid()
    before = [p["pid"] for p in sample()["descendants"]]
    if pid:
        ocr._WORKER.proc.kill()
        ocr._WORKER.proc.wait(timeout=5)
    ocr.clear_local_ocr_cache()
    return {"killed_pid": pid, "descendant_pids_before": before}
