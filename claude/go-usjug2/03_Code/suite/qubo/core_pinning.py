import os
import platform

def pin_to_cores(core_list: list):
    """Pinning für Threadripper / Ryzen.
    
    Windows: Volles CPU-Affinity-Pinning für den aktuellen Prozess ist
    mit Standard-Python eingeschränkt (braucht psutil oder win32api + Admin).
    
    Hier eine sichere Fallback-Implementierung:
    - Unter Linux: os.sched_setaffinity
    - Unter Windows: Nur Hinweis + Umgebungsvariable setzen.
    """
    system = platform.system()
    if system == "Linux":
        try:
            os.sched_setaffinity(0, core_list)
            print(f"[PIN] Erfolgreich auf Cores {core_list} gepinnt (Linux).")
        except Exception as e:
            print(f"[PIN] Linux pinning fehlgeschlagen: {e}")
    elif system == "Windows":
        # Real Windows: Empfehlung - Starte das Script mit 
        # start /affinity <mask> python pool.py
        # Oder installiere psutil: pip install psutil
        # Hier nur Logging + Versuch mit psutil falls vorhanden.
        try:
            import psutil
            p = psutil.Process(os.getpid())
            p.cpu_affinity(core_list)
            print(f"[PIN] Erfolgreich auf Cores {core_list} gepinnt (Windows + psutil).")
        except ImportError:
            print(f"[PIN-WARNING] psutil nicht installiert. "
                  f"Starte mit 'start /affinity 0xFF python ...' oder installiere psutil.")
            print(f"[PIN] Gewünschte Cores: {core_list} (nicht angewendet).")
        except Exception as e:
            print(f"[PIN] Windows pinning fehlgeschlagen: {e}")
    else:
        print(f"[PIN] Nicht unterstütztes OS: {system}")

def get_threadripper_cores(num_cores: int = 12) -> list:
    """Beispiel: Für Ryzen 5 3600 (6C/12T) oder Threadripper.
    Passe an deine Hardware an."""
    return list(range(num_cores))
