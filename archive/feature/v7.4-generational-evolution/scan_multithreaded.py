import os
import stat
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator, Tuple

ROOT = r"C:\Users\Admin\Desktop\ALTE_Frau_95g_Beste_Version"
# Dynamische Thread-Anzahl: I/O-gebunden => mehr Threads als CPU-Kerne
MAX_WORKERS = max(4, min(32, (os.cpu_count() or 4) + 4))


def _iter_files(root: str) -> Iterator[str]:
    """Rekursiver Datei-Scan mittels os.scandir (cached stat-info)."""
    root_path = Path(root)
    for p in root_path.rglob('*'):
        if p.is_file():
            yield str(p)


def _inspect(path: str) -> Tuple[str, int, float]:
    """Datei-Metadaten; gibt (pfad, size, mtime) zurueck."""
    try:
        st = os.stat(path, follow_symlinks=False)
        return path, st.st_size, st.st_mtime
    except OSError as exc:
        return path, -1, -1.0


def main():
    t0 = time.perf_counter()

    # 1) Alle Pfade sammeln (single-threaded, I/O durch OS-Paging gecached)
    files = list(_iter_files(ROOT))
    collect_t = time.perf_counter() - t0

    # 2) Parallele Inspektion
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_inspect, p): p for p in files}
        for future in as_completed(futures):
            results.append(future.result())

    inspect_t = time.perf_counter() - t0 - collect_t

    # 3) Ausgabe (vorsortiert nach Pfad)
    results.sort(key=lambda x: x[0])
    for path, size, mtime in results:
        print(f"{path}\n  size={size}\n  mtime={mtime}")

    total = time.perf_counter() - t0
    print(f"\nDateien gefunden: {len(files)}")
    print(f"Threads: {MAX_WORKERS}")
    print(f"Sammlung: {collect_t*1000:.1f} ms | Inspektion: {inspect_t*1000:.1f} ms | Gesamt: {total*1000:.1f} ms")


if __name__ == "__main__":
    main()
