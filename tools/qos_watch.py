"""Keep a render's processes off Windows' power throttling (EcoQoS): Windows 11 can park a background app's helper processes
on the efficiency cores (measured 2026-11-11 on the i5-12600K: HyperFrames' Chrome workers ran on the 4 E-cores only and a
capture took 2-3x as long). boost(pid) marks one process "never throttle"; watch(root_pid, stop_event) does it for the whole
process tree of root_pid twice a second until stop_event is set. No-ops off Windows."""
import os, threading, time
try:
    import ctypes, ctypes.wintypes as wt
    import psutil
    k32 = ctypes.windll.kernel32 if os.name == 'nt' else None
except Exception:
    k32 = None


def boost(pid):
    if not k32: return False
    class PPT(ctypes.Structure): _fields_ = [('Version', wt.ULONG), ('ControlMask', wt.ULONG), ('StateMask', wt.ULONG)]
    h = k32.OpenProcess(0x0200, False, pid)                  # PROCESS_SET_INFORMATION
    if not h: return False
    s = PPT(1, 1, 0)                                         # EXECUTION_SPEED controlled, throttling off = HighQoS
    ok = k32.SetProcessInformation(h, 4, ctypes.byref(s), ctypes.sizeof(s)); k32.CloseHandle(h)
    return bool(ok)


def watch(root_pid, stop):
    done = set()
    while not stop.is_set():
        try:
            for p in [psutil.Process(root_pid)] + psutil.Process(root_pid).children(recursive=True):
                if p.pid not in done and boost(p.pid): done.add(p.pid)
        except Exception:
            pass
        stop.wait(0.5)
    return len(done)


def start(root_pid=None):
    """Start watching (default: this process and everything it starts). Returns a function that stops it."""
    if not k32: return lambda: None
    stop = threading.Event()
    threading.Thread(target=watch, args=(root_pid or os.getpid(), stop), daemon=True).start()
    return stop.set
