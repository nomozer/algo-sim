"""Windows-only offline child ownership, attached atomically at CreateProcess.

Job membership is inherited by descendants. Closing our non-inherited job handle
kills the entire tree even if the observer fails; no process enumeration service
or taskkill permission is required. Windows 10+ JOB_LIST avoids a spawn/attach race.
"""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import math
import msvcrt
import os
import subprocess
import time


class _StartupInfo(C.Structure):
    _fields_ = [("cb", W.DWORD), ("reserved", W.LPWSTR), ("desktop", W.LPWSTR), ("title", W.LPWSTR),
                *[(name, W.DWORD) for name in ("x", "y", "width", "height", "xchars", "ychars", "fill", "flags")],
                ("show", W.WORD), ("reserved_size", W.WORD), ("reserved_data", W.LPVOID),
                ("stdin", W.HANDLE), ("stdout", W.HANDLE), ("stderr", W.HANDLE)]


class _StartupInfoEx(C.Structure):
    _fields_ = [("startup", _StartupInfo), ("attributes", W.LPVOID)]


class _ProcessInfo(C.Structure):
    _fields_ = [("process", W.HANDLE), ("thread", W.HANDLE), ("pid", W.DWORD), ("tid", W.DWORD)]


class _BasicLimits(C.Structure):
    _fields_ = [("process_time", C.c_longlong), ("job_time", C.c_longlong), ("flags", W.DWORD),
                ("min_working_set", C.c_size_t), ("max_working_set", C.c_size_t), ("process_limit", W.DWORD),
                ("affinity", C.c_size_t), ("priority", W.DWORD), ("scheduling", W.DWORD)]


class _ExtendedLimits(C.Structure):
    _fields_ = [("basic", _BasicLimits), ("io", C.c_ulonglong * 6),
                *[(name, C.c_size_t) for name in ("process_memory", "job_memory", "peak_process", "peak_job")]]


class _Accounting(C.Structure):
    _fields_ = [("times", C.c_longlong * 4), ("faults", W.DWORD), ("total", W.DWORD),
                ("active", W.DWORD), ("terminated", W.DWORD)]


_kernel = C.WinDLL("kernel32", use_last_error=True)
for _name, _restype, _args in (
    ("CreateJobObjectW", W.HANDLE, [W.LPVOID, W.LPCWSTR]),
    ("SetInformationJobObject", W.BOOL, [W.HANDLE, C.c_int, W.LPVOID, W.DWORD]),
    ("QueryInformationJobObject", W.BOOL, [W.HANDLE, C.c_int, W.LPVOID, W.DWORD, W.LPVOID]),
    ("TerminateJobObject", W.BOOL, [W.HANDLE, W.UINT]),
    ("CloseHandle", W.BOOL, [W.HANDLE]),
    ("GetCurrentProcess", W.HANDLE, []),
    ("DuplicateHandle", W.BOOL, [W.HANDLE, W.HANDLE, W.HANDLE, C.POINTER(W.HANDLE), W.DWORD, W.BOOL, W.DWORD]),
    ("InitializeProcThreadAttributeList", W.BOOL, [W.LPVOID, W.DWORD, W.DWORD, C.POINTER(C.c_size_t)]),
    ("UpdateProcThreadAttribute", W.BOOL, [W.LPVOID, W.DWORD, C.c_size_t, W.LPVOID, C.c_size_t, W.LPVOID, W.LPVOID]),
    ("DeleteProcThreadAttributeList", None, [W.LPVOID]),
    ("CreateProcessW", W.BOOL, [W.LPCWSTR, W.LPWSTR, W.LPVOID, W.LPVOID, W.BOOL, W.DWORD, W.LPVOID,
                               W.LPCWSTR, C.POINTER(_StartupInfoEx), C.POINTER(_ProcessInfo)]),
    ("WaitForSingleObject", W.DWORD, [W.HANDLE, W.DWORD]),
    ("GetExitCodeProcess", W.BOOL, [W.HANDLE, C.POINTER(W.DWORD)]),
):
    _function = getattr(_kernel, _name)
    _function.restype, _function.argtypes = _restype, _args


def _check(ok):
    if not ok:
        raise C.WinError(C.get_last_error())


class WindowsJobProcess:
    """Own one command and all descendants; fail closed on any cleanup failure."""

    def __init__(self, command, cwd, stream, env):
        self.command, self.job, self.process, self.pid = command, None, None, None
        try:
            self.job = _kernel.CreateJobObjectW(None, None)
            _check(self.job)
            limits = _ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway permission.
            _check(_kernel.SetInformationJobObject(self.job, 9, C.byref(limits), C.sizeof(limits)))
            self._spawn(command, cwd, stream, env)
        except BaseException:
            self.close()
            raise

    def _spawn(self, command, cwd, stream, env):
        size = C.c_size_t()
        _kernel.InitializeProcThreadAttributeList(None, 2, 0, C.byref(size))
        attributes = C.create_string_buffer(size.value)
        _check(_kernel.InitializeProcThreadAttributeList(attributes, 2, 0, C.byref(size)))
        inherited = []
        try:
            current = _kernel.GetCurrentProcess()
            with open(os.devnull, "rb") as null_input:
                for file in (null_input, stream):
                    duplicate = W.HANDLE()
                    _check(_kernel.DuplicateHandle(current, msvcrt.get_osfhandle(file.fileno()), current,
                                                   C.byref(duplicate), 0, True, 2))
                    inherited.append(duplicate.value)
                handles = (W.HANDLE * 2)(*inherited)
                jobs = (W.HANDLE * 1)(self.job)
                _check(_kernel.UpdateProcThreadAttribute(attributes, 0, 0x20002, C.byref(handles), C.sizeof(handles), None, None))
                _check(_kernel.UpdateProcThreadAttribute(attributes, 0, 0x2000D, C.byref(jobs), C.sizeof(jobs), None, None))
                startup = _StartupInfoEx()
                startup.startup.cb = C.sizeof(startup)
                startup.startup.flags = 0x100  # STARTF_USESTDHANDLES; inherit only our NUL/log handles.
                startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = inherited[0], inherited[1], inherited[1]
                startup.attributes = C.cast(attributes, W.LPVOID)
                info = _ProcessInfo()
                environment = C.create_unicode_buffer("\0".join(f"{k}={v}" for k, v in sorted(env.items())) + "\0\0")
                _check(_kernel.CreateProcessW(None, C.create_unicode_buffer(subprocess.list2cmdline(command)),
                                              None, None, True, 0x08080400, environment, str(cwd), C.byref(startup), C.byref(info)))
                self.process, self.pid = info.process, info.pid
                _check(_kernel.CloseHandle(info.thread))
        finally:
            for handle in inherited:
                _kernel.CloseHandle(handle)
            _kernel.DeleteProcThreadAttributeList(attributes)

    def wait(self, timeout):
        result = _kernel.WaitForSingleObject(self.process, min(0xFFFFFFFE, math.ceil(max(0, timeout) * 1000)))
        if result == 258:
            raise subprocess.TimeoutExpired(self.command, timeout)
        if result != 0:
            raise C.WinError(C.get_last_error())
        code = W.DWORD()
        _check(_kernel.GetExitCodeProcess(self.process, C.byref(code)))
        return code.value

    def _accounting(self):
        info = _Accounting()
        _check(_kernel.QueryInformationJobObject(self.job, 1, C.byref(info), C.sizeof(info), None))
        return info

    def stop_tree(self):
        info = self._accounting()
        # Leave room for concurrent forks; failure to obtain a complete snapshot still fails closed.
        class Pids(C.Structure):
            _fields_ = [("assigned", W.DWORD), ("count", W.DWORD), ("pids", C.c_size_t * (info.active + 64))]
        pids = Pids()
        _check(_kernel.QueryInformationJobObject(self.job, 3, C.byref(pids), C.sizeof(pids), None))
        observed = list(pids.pids[:pids.count])
        if info.active:
            _check(_kernel.TerminateJobObject(self.job, 1))
        deadline = time.monotonic() + 5
        while True:
            info = self._accounting()
            if not info.active:
                try:
                    self.wait(max(0, deadline - time.monotonic()))
                except subprocess.TimeoutExpired as exc:
                    raise OSError("WINDOWS_JOB_PROCESS_STILL_ACTIVE") from exc
                return {"method": "windows_job", "parent_pid": self.pid, "pids_before_cleanup": observed,
                        "total_processes": info.total, "active_processes": info.active}
            if time.monotonic() >= deadline:
                raise OSError("WINDOWS_JOB_STILL_ACTIVE")
            time.sleep(.01)

    def close(self):
        if self.job:
            job, self.job = self.job, None
            _check(_kernel.CloseHandle(job))
        if self.process:
            try:
                self.wait(5)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("WATCHDOG_TERMINATION_FAILED") from exc
            finally:
                process, self.process = self.process, None
                _check(_kernel.CloseHandle(process))

    def __enter__(self):
        return self

    def __exit__(self, *exception):
        self.close()
