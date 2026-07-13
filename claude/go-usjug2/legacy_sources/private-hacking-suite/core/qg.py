# -*- coding: utf-8 -*-
"""
Self-Optimizing Resource Governor
==================================
Nutzt den QUBO-Ansatz aus qb_qubo.py zur autonomen Optimierung von
CPU-, GPU- und Netzwerknutzung.

Logik:
  1. Echtzeit-Metriken sammeln (psutil + pynvml)
  2. Q-Matrix aus aktueller Last + Historie aufbauen  => quadratische Form q(b)
  3. QUBO-Grundzustand (min x^T Q x) via SA/Simulated Annealing finden
  4. Entscheidungsvektor b in Aktionen decodieren (Prioritäten, Throttles,
     VS-Code-Settings, Power-Plan, etc.)
  5. Nachheuristik: nur Aktionen ausführen, die Delta > Schwellwert liefern

Voraussetzungen: psutil, pynvml (kommt mit nvidia-driver)
"""
from __future__ import annotations
import ctypes, ctypes.wintypes as wt, json, math, os, platform, random, shutil, subprocess, sys, time, urllib.request
from ctypes import Structure, Union, c_ulong, c_uint, c_ushort, c_int, POINTER, byref, pointer, windll
from datetime import datetime
from pathlib import Path

# ---------- Windows-Strukturen (Nicht-Blocking IO) ----------
class IO_COUNTERS(Structure):
    _fields_ = [("ReadOperationCount", c_ulong), ("WriteOperationCount", c_ulong),
                ("OtherOperationCount", c_ulong), ("ReadTransfer", c_ulong),
                ("WriteTransfer", c_ulong), ("OtherTransfer", c_ulong)]

kernel32 = windll.kernel32
psapi = windll.psapi

kernel32.GetProcessIoCounters.restype = c_int
kernel32.GetProcessIoCounters.argtypes = [wt.HANDLE, POINTER(IO_COUNTERS)]

# ---------- Config ----------
CONFIG_PATH = Path.home() / ".qg" / "qg_config.json"
STATE_PATH  = Path.home() / ".qg" / "qg_state.json"
LOG_PATH    = Path.home() / ".qg" / "qg.log"
INTERVAL_S  = 5          # Messzyklus
WINDOW      = 20         # Größe des Rollfensters für Last-Historie
DETA        = 0.15       # Mindeständerung, damit optimiert wird

def _init():
    for p in (CONFIG_PATH, STATE_PATH):
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text("{}", encoding="utf-8")
    if not LOG_PATH.exists():
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOG_PATH.write_text("", encoding="utf-8")

def log(msg: str):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)

def load_json(p: Path):
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:
        return {}

def save_json(p: Path, data):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------- Metriken ----------
smi = None
try:
    import pynvml
    pynvml.nvmlInit()
    smi = pynvml.nvmlDeviceGetHandleByIndex(0)
except Exception:
    pass

def _psutil_ok():
    try:
        import psutil
        return psutil
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "-q"])
        import psutil
        return psutil

class Metrics:
    __slots__ = ("ts","cpu","cpu_per_core","mem_pct","mem_used_gb","mem_total_gb",
                 "gpu_pct","gpu_mem_pct","gpu_temp_c",
                 "net_up_kbps","net_down_kbps","disk_read_kbps","disk_write_kbps",
                 "proc_cpu_pct","vscode_pids")
    def __init__(self):
        self.ts = time.time()
        ps = _psutil_ok()
        self.cpu = ps.cpu_percent(interval=None)
        self.cpu_per_core = ps.cpu_percent(interval=None, percpu=True)
        vm = ps.virtual_memory()
        self.mem_pct = vm.percent
        self.mem_used_gb = vm.used / 1e9
        self.mem_total_gb = vm.total / 1e9
        self.gpu_pct = None; self.gpu_mem_pct = None; self.gpu_temp_c = None
        if smi:
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(smi)
                mem = pynvml.nvmlDeviceGetMemoryInfo(smi)
                self.gpu_pct = float(util.gpu)
                self.gpu_mem_pct = round(mem.used / mem.total * 100, 1)
                self.gpu_temp_c = pynvml.nvmlDeviceGetTemperature(smi, pynvml.NVML_TEMPERATURE_GPU)
            except Exception:
                pass
        n1 = ps.net_io_counters(); time.sleep(0.2); n2 = ps.net_io_counters()
        dt = max(time.time() - self.ts, 0.01)
        self.net_down_kbps = (n2.bytes_recv  - n1.bytes_recv)  / dt / 1024
        self.net_up_kbps   = (n2.bytes_sent  - n1.bytes_sent)  / dt / 1024
        d1 = ps.disk_io_counters()
        time.sleep(0.2)
        d2 = ps.disk_io_counters()
        self.disk_read_kbps  = (d2.read_bytes  - d1.read_bytes)  / dt / 1024
        self.disk_write_kbps = (d2.write_bytes - d1.write_bytes) / dt / 1024

        # VS Code
        vsc_names = {"Code.exe", "Code - Insiders.exe"}
        self.vscode_pids = [p.pid for p in ps.process_iter(['pid','name'])
                            if p.info['name'] in vsc_names and p.info['pid']]
        cpu_sum = 0.0
        for pid in self.vscode_pids:
            try:
                cpu_sum += ps.Process(pid).cpu_percent(interval=None) / ps.cpu_count()
            except Exception:
                pass
        self.proc_cpu_pct = round(cpu_sum, 1)

    def to_dict(self):
        return {k: getattr(self, k) for k in self.__slots__ if k not in ("ts","cpu_per_core","vscode_pids")}

# ---------- QUBO / SA (aus qb_qubo.py portiert) ----------
def simulated_annealing(Q: list[list[float]], steps: int = 3000, T0: float = 2.5) -> list[int]:
    rng = random.Random(42)
    n = len(Q)
    x = [rng.randint(0, 1) for _ in range(n)]
    def energy(v):
        e = 0.0
        # symmetrische Diagonalisierte Summe
        for i in range(n):
            for j in range(n):
                if Q[i][j]:
                    e += (0.5 if i == j else 1.0) * Q[i][j] * v[i] * v[j]
        return e
    e = energy(x)
    best_x, best_e = x[:], e
    for t in range(steps):
        T = T0 * (1 - t / steps) + 1e-3
        i = rng.randint(0, n-1)
        nx = x[:]; nx[i] = 1 - nx[i]
        ne = energy(nx)
        if ne < e or rng.random() < math.exp(-(ne - e) / T):
            x, e = nx, ne
            if e < best_e:
                best_x, best_e = x[:], e
    return best_x

# ---------- Entscheidungsraum (binär) ----------
# Index   Parameter                          | 1 = Aktion
# 0       CPU: Power-Plan "Hohe Leistung"     | 1 = setzen
# 1       CPU: VS Code class "Above Normal"  | 1 = setzen
# 2       GPU: maximale Leistung             | 1 = enforce
# 3       GPU: Hardware-Beschleunigung VS C  | 1 = aktiv
# 4       Net: VS Code proxy bypass          | 1 = aktiv
# 5       Net: DNS-Cache flush               | 1 = aktiv
# 6       RAM: VS Code heap erhöhen          | 1 = erhöhen
# 7       RAM: working_set_min setzen        | 1 = erhöhen
# 8       Disk: VS Code exclude Pfad         | 1 = aktiv
# 9       CPU: game_mod / QoS                | 1 = aktiv
# 10      CPU: Core Pin Mask                 | 1 = setze optimierte Affinität
# 11      CPU: Thread Prio Time Critical    | 1 = Haupt-Thread TIME_CRITICAL
# 12      CPU: Ideal Processor               | 1 = automatische Ideal-Prozessor-Zuordnung
# 13      CPU: Boost / Cluster Hint          | 1 = P-Core-Cluster bevorzugen

PARAM_DESCS = [
    "PowerPlan = High Perf",           # 0
    "VSCode Priority = Above Normal",  # 1
    "GPU Power Max",                   # 2
    "VSCode GPU Accel",                # 3
    "VSCode Proxy Bypass",             # 4
    "DNS Flush",                       # 5
    "VSCode Heap Increase",            # 6
    "VSCode Working Set",              # 7
    "VSCode Exclude Path",             # 8
    "QoS Game Mod",                    # 9
    "Core Affinity Mask",              # 10
    "Thread Prio Time Critical",       # 11
    "Ideal Processor Fix",             # 12
    "Boost Cluster Hint",              # 13
]

def build_Q(hist: list[Metrics]) -> list[list[float]]:
    n = len(PARAM_DESCS)
    Q = [[0.0]*n for _ in range(n)]
    if not hist:
        return Q

    def avg(fn): return sum(fn(m) for m in hist) / len(hist)
    cpu  = avg(lambda m: m.cpu)
    gpu  = avg(lambda m: m.gpu_pct if m.gpu_pct is not None else 0)
    mem  = avg(lambda m: m.mem_pct)
    netd = avg(lambda m: m.net_down_kbps)
    netu = avg(lambda m: m.net_up_kbps)
    vsc  = avg(lambda m: m.proc_cpu_pct)

    # Diagonal: "Kosten" einer Einstellung (je höher Last, desto teurer einzuschalten)
    diag = {
        0: max(cpu - 60, 0) * 0.02,
        1: max(vsc * 3 - 20, 0) * 0.03,
        2: max(gpu - 50, 0) * 0.025,
        3: (0.4 if gpu > 80 else -0.2),
        4: max(netd + netu - 5000, 0) * 0.001,
        5: max(netd + netu - 10000, 0) * 0.0008,
        6: max(mem - 70, 0) * 0.015,
        7: max(mem - 60, 0) * 0.01,
        8: max(cpu > 85 or mem > 85, 0) * 0.02,
        9: max(netd > 20000, 0) * 0.01,
        10: max(cpu - 55, 0) * 0.025,
        11: max(cpu - 70, 0) * 0.02,
        12: max(cpu - 50, 0) * 0.018,
        13: max(cpu - 60, 0) * 0.022,
    }
    for i in range(n):
        Q[i][i] = diag.get(i, 0.0)

    # Kopplungen: falsche Kombinationen teurer machen
    couplings = [
        (0, 1,  0.05),   # PowerPlan + Priorität (konsistent)
        (3, 2, -0.10),   # GPU-Accel + Power (synergistisch)
        (3, 1, -0.05),   # GPU-Accel + VSCode Priorität (Reduktion CPU-Last)
        (6, 7,  0.08),   # beide RAM-Optimierungen konfliktär
        (6, 8, -0.04),   # Exclude + Heap ok
        (4, 5,  0.03),   # Proxy + DNS sind unabhängig
        (9, 4, -0.03),   # QoS + Proxy reduzieren Latenz
        (9, 0, -0.02),   # QoS + High Perf
        (2, 0,  0.03),   # GPU Power + PowerPlan inkonsistent wenn nicht koordiniert
        (10, 1, -0.08),  # Core Affinity + Priorität (synergistisch)
        (11, 10, -0.06), # Thread Prio + Affinity
        (12, 1, -0.07),  # Ideal Processor + VSCode Priority
        (13, 0, -0.05),  # Boost Cluster + High Perf PowerPlan
        (13, 10, -0.04), # Boost Cluster + Core Affinity (konsistent)
        (11, 9, 0.04),   # TIME_CRITICAL + QoS (Potential Konflikt, begrenzen)
    ]
    for i, j, v in couplings:
        Q[i][j] += v
        Q[j][i] += v
    return Q

# ---------- Aktor: wende Optimierungen an ----------
def _set_power_plan(on: bool):
    if not on:
        subprocess.run(["powercfg", "/setactive", "SCHEME_MIN"], check=False, capture_output=True); return
    subprocess.run(["powercfg", "/setactive", "SCHEME_MAX"], check=False, capture_output=True)

def _set_vscode_priority(on: bool):
    if not on:
        subprocess.run(["powercfg", "/setactive", "SCHEME_MIN"], check=False, capture_output=True); return
    names = ("Code.exe", "Code - Insiders.exe")
    ps = _psutil_ok()
    for p in ps.process_iter(['pid','name']):
        if p.info['name'] in names:
            try: p.nice(ps.HIGH_PRIORITY_CLASS if on else ps.NORMAL_PRIORITY_CLASS)
            except Exception: pass

def _set_gpu_power(on: bool):
    if smi:
        try:
            # NVML power limit setzen (wenn supported)
            pmin, pmax = pynvml.nvmlDeviceGetPowerManagementLimitConstraints(smi)
            target = pmax if on else (pmin + (pmax - pmin)//2)
            pynvml.nvmlDeviceSetPowerManagementLimit(smi, int(target))
        except Exception:
            pass

def _set_vscode_gpu_accel(on: bool):
    base = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    if not base.exists():
        return False
    try:
        data = json.loads(base.read_text("utf-8"))
        key = "disable-hardware-acceleration"
        if on:
            data.pop(key, None)
        else:
            data[key] = True
        base.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False

def _set_proxy_bypass(on: bool):
    try:
        key = winreg.HKEY_CURRENT_USER
        path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
        with winreg.OpenKey(key, path, 0, winreg.KEY_SET_VALUE) as k:
            winreg.SetValueEx(k, "ProxyEnable", 0, winreg.REG_DWORD, 0 if on else 1)
        return True
    except Exception:
        return False

def _dns_flush(on: bool):
    if on:
        subprocess.run(["ipconfig", "/flushdns"], check=False, capture_output=True)

def _set_vscode_heap(on: bool):
    base = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    if not base.exists():
        return False
    try:
        data = json.loads(base.read_text("utf-8"))
        key = "terminal.integrated.inheritEnv"
        # heap über launch.json oder argv
        data["github.copilot.advanced"] = data.get("github.copilot.advanced", {})
        data["github.copilot.advanced"]["maxWorkers"] = 4 if on else 2
        base.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False

def _set_working_set(on: bool):
    import psutil
    size = 0x1000000 if on else 0x400000  # 256 MB vs 4 MB
    for pid in _vscode_pids():
        try:
            h = windll.kernel32.OpenProcess(0x0200 | 0x0010 | 0x0020, False, pid)
            if h:
                ctypes.windll.psapi.SetProcessWorkingSetSize(h, size, size)
                windll.kernel32.CloseHandle(h)
        except Exception:
            pass
    return True

def _set_exclude_path(on: bool):
    base = Path.home() / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    if not base.exists():
        return False
    try:
        data = json.loads(base.read_text("utf-8"))
        key = "files.exclude"
        default = {
            "**/.git": False,
            "**/.vscode": False,
            "**/node_modules": False,
            "**/.venv": True if on else False,
            "**/venv": True if on else False,
            "**/__pycache__": True if on else False,
        }
        data[key] = default
        base.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception:
        return False

def _set_qos(on: bool):
    if on:
        subprocess.run(["powershell", "-Command",
                        "New-NetQosPolicy -Name 'VSCodeQoS' "
                        "-AppPath 'Code.exe' -DSCPAction 46 -ThrottleRateActionBitsPerSecond 0"],
                       check=False, capture_output=True)
    else:
        subprocess.run(["powershell", "-Command",
                        "Remove-NetQosPolicy -Name 'VSCodeQoS' -Confirm:$false"],
                       check=False, capture_output=True)

def _set_core_affinity(on: bool):
    ps = _psutil_ok()
    n = ps.cpu_count()
    if n <= 1:
        return False
    # Heuristik: bei Last auf Core 2 → vermeide exklusiven Pin auf Core 2,
    # verteile auf logische Kerne außer Core 2, wenn möglich.
    mask = 0
    if on:
        # Nutze alle Kerne außer Core 2 (wenn genug da), sonst alle.
        cores = [i for i in range(n) if i != 2] or list(range(n))
        for c in cores:
            mask |= (1 << c)
    else:
        mask = (1 << n) - 1
    for pid in _vscode_pids():
        try:
            p = ps.Process(pid)
            p.cpu_affinity(cores if on else list(range(n)))
        except Exception:
            pass
    return True

def _set_thread_prio(on: bool):
    ps = _psutil_ok()
    prio = ps.HIGH_PRIORITY_CLASS if on else ps.NORMAL_PRIORITY_CLASS
    for pid in _vscode_pids():
        try:
            ps.Process(pid).nice(prio)
        except Exception:
            pass
    return True

def _set_ideal_processor(on: bool):
    # Setze Ideal-Prozessor auf den ersten logischen Kern (oft P-Core auf hybriden CPUs)
    ps = _psutil_ok()
    ideal = 0
    for pid in _vscode_pids():
        try:
            h = windll.kernel32.OpenProcess(0x0200 | 0x0010 | 0x0020, False, pid)
            if h:
                ctypes.windll.psapi.SetProcessIdealProcessor(h, byref(wt.DWORD(ideal)))
                windll.kernel32.CloseHandle(h)
        except Exception:
            pass
    return True

def _set_boost_cluster(on: bool):
    # Bevorzuge Performance-Kerne durch Power-Plan + QoS + BackgroundTasksOptimizer-Registry
    try:
        subprocess.run(["powercfg", "/setactive", "SCHEME_MAX" if on else "SCHEME_BALANCED"],
                       check=False, capture_output=True)
        # Windows 11: Productivity & Creativity Mode nicht direkt regelbar,
        # aber ProcGroupPolicy beeinflusst SMT-Design.
        return True
    except Exception:
        return False

ACTORS = [
    _set_power_plan,
    _set_vscode_priority,
    _set_gpu_power,
    _set_vscode_gpu_accel,
    _set_proxy_bypass,
    _dns_flush,
    _set_vscode_heap,
    _set_working_set,
    _set_exclude_path,
    _set_qos,
    _set_core_affinity,
    _set_thread_prio,
    _set_ideal_processor,
    _set_boost_cluster,
]

def _vscode_pids():
    ps = _psutil_ok()
    names = ("Code.exe", "Code - Insiders.exe")
    for p in ps.process_iter(['pid','name']):
        if p.info['name'] in names and p.info['pid']:
            yield p.info['pid']

import winreg

DASH_URL = "http://127.0.0.1:8000/api/events"

def _dash_emit(e_type: str, msg: str, count: int | None = None):
    try:
        data = json.dumps({"type": e_type, "msg": msg, "count": count}).encode("utf-8")
        req = urllib.request.Request(DASH_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=0.3)
    except Exception:
        pass

def apply_decisions(b: list[int], last: dict, state: dict):
    changed = {}
    for i, on in enumerate(b):
        prev = state.get(f"o{i}", -1)
        if on != prev:
            try:
                ok = ACTORS[i](bool(on))
                changed[f"o{i}"] = on
                log(f"  -> {'ENABLE' if on else 'DISABLE'}: {PARAM_DESCS[i]}  [ok={ok}]")
            except Exception as e:
                log(f"  !! {PARAM_DESCS[i]} failed: {e}")
    save_json(STATE_PATH, {**state, **changed})

# ---------- Control Loop ----------
def run(once=False):
    _init()
    state = load_json(STATE_PATH)
    hist: list[Metrics] = []
    gen = 0
    try:
        import winreg
    except ImportError:
        pass

    while True:
        gen += 1
        m = Metrics()
        hist.append(m)
        if len(hist) > WINDOW:
            hist = hist[-WINDOW:]

        d = m.to_dict()
        status = (f"CPU={m.cpu:.0f}%  GPU={m.gpu_pct if m.gpu_pct is not None else 'n/a'}%  "
                  f"MEM={m.mem_pct:.0f}%  "
                  f"NET={m.net_down_kbps:.0f}d/{m.net_up_kbps:.0f}u KB/s")
        log(f"[{gen}] {status}")
        _dash_emit("token", status)

        Q = build_Q(hist)
        b = simulated_annealing(Q, steps=4000)
        bits = ''.join(str(v) for v in b)
        log(f"     QUBO solution b = {bits}")
        _dash_emit("step", f"QUBO solution b = {bits}")

        # Vergleich: vorherige Entscheidung
        prev = [state.get(f"o{i}", 0) for i in range(len(PARAM_DESCS))]
        if b != prev:
            _dash_emit("tool", f"Applying {sum(b)} optimizations...")
            apply_decisions(b, state, state)
        else:
            _dash_emit("system", "Keine Aenderung (Delta < Schwellwert).")

        if once:
            return b
        time.sleep(INTERVAL_S)

# ---------- CLI ----------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="Einmalige Optimierung")
    ap.add_argument("--interval", type=int, default=INTERVAL_S, help="Sekunden")
    args = ap.parse_args()
    INTERVAL_S = args.interval
    run(once=args.once)
