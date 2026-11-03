"""Child processes that die with this one. Windows keeps a child running when its parent is killed, so a killed run would leave workers writing into the store beside the next run.

Each child goes in a job object whose last handle is this process's. The system closes that handle however this process ends, and the job takes the child and everything it started with it,
the browser and encoder included. Nothing outside that tree is ever touched. If the job cannot be made, a child runs untied, as any child would.

On macOS and Linux each child leads its own process group, and a small watcher kills that group once this process is gone.
"""
import ctypes
import os
import signal
import subprocess
from ctypes import wintypes

KILL_ON_JOB_CLOSE = 0x2000
EXTENDED_LIMIT_INFORMATION = 9
SET_QUOTA_AND_TERMINATE = 0x0100 | 0x0001


class BasicLimits(ctypes.Structure):
    _fields_ = [("user_time", ctypes.c_longlong), ("job_user_time", ctypes.c_longlong), ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t), ("max_working_set", ctypes.c_size_t),
                ("active_processes", wintypes.DWORD), ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", BasicLimits), ("io", ctypes.c_ulonglong * 6), ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]


def kernel():
    lib = ctypes.WinDLL("kernel32", use_last_error=True)
    lib.CreateJobObjectW.restype = wintypes.HANDLE
    lib.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    lib.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    lib.OpenProcess.restype = wintypes.HANDLE
    lib.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    lib.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    lib.CloseHandle.argtypes = [wintypes.HANDLE]
    return lib


_job = None


def job():
    """This process's job, made once. Held open on purpose: closing it is what kills the children."""
    global _job
    if _job is None:
        lib = kernel()
        handle = lib.CreateJobObjectW(None, None)
        limits = ExtendedLimits()
        limits.basic.flags = KILL_ON_JOB_CLOSE
        if not handle or not lib.SetInformationJobObject(handle, EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise OSError(ctypes.get_last_error(), "could not make a job object")
        _job = handle
    return _job


def tie(pid):
    """True if this process is now in the job."""
    try:
        lib = kernel()
        handle = lib.OpenProcess(SET_QUOTA_AND_TERMINATE, False, pid)
        if not handle:
            return False
        try:
            return bool(lib.AssignProcessToJobObject(job(), handle))
        finally:
            lib.CloseHandle(handle)
    except (OSError, AttributeError):
        return False


# Waits while this process ($1) and the child's group ($2) are both alive; if this process went first, kills the group.
WATCH = 'while kill -0 "$1" 2>/dev/null && kill -0 -- "-$2" 2>/dev/null; do sleep 0.5; done; kill -0 "$1" 2>/dev/null || kill -KILL -- "-$2" 2>/dev/null'


def watch(pid):
    """POSIX has no job object, and a child in its own session outlives a killed parent, so a watcher does the job's work.
    It sits in a session of its own, so the Ctrl-C or kill that ends this process never reaches it. True if it started."""
    try:
        subprocess.Popen(["/bin/sh", "-c", WATCH, "sh", str(os.getpid()), str(pid)], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


def spawn(args, **kwargs):
    grouped = os.name != "nt"
    if grouped:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(args, **kwargs)
    process.grouped = grouped
    process.tied = tie(process.pid) if os.name == "nt" else watch(process.pid)
    return process


def kill_tree(process):
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(process.pid)], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
