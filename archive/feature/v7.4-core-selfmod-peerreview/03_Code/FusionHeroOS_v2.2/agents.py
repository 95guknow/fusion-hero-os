# -*- coding: utf-8 -*-
"""
AGENTS — Multi-Agent Orchestration Framework (v1.0)
===================================================
Reine-Python Multi-Agenten-Orchestrierung fuer das "Fusion Hero OS / ALTE_FRAU_95g Core".

Ziel dieser Datei:
  Eine *lauffaehige*, vollstaendig pure-Python (Standardbibliothek) Orchestrierung von
  kooperierenden Agenten, die sich gegenseitig regelmaessig ueber ihren Status informieren,
  Aufgaben aus einer Warteschlange abarbeiten und die Belegschaft dynamisch hoch- und
  herunterskalieren (hire / fire).

Kein externer LLM-Aufruf, kein Netzwerk, keine optionalen Bibliotheken noetig. Die "Arbeit"
eines Agenten ist standardmaessig eine deterministische, simulierte Funktion (kurzer sleep),
laesst sich aber ueber einen pluggable Executor-Callable austauschen.

Architektur-Bausteine:
  - MessageBus    : thread-sicheres Publish/Subscribe + zentrales Status-Register
  - Task          : eine einzelne Arbeitseinheit
  - TaskQueue     : thread-sichere FIFO-Warteschlange (Wrapper um queue.Queue)
  - Agent         : Basis-Agent mit eigenem Thread, Heartbeat, Hire/Fire fuer Subagenten
  - Supervisor    : Agent, der eine Belegschaft fuehrt, Tasks zuweist und auto-skaliert

HARTE INVARIANTEN (vgl. Projekt-Constraints):
  1. Import-sicher: KEINE Seiteneffekte auf Modulebene, KEIN Netzwerk, KEIN ui.run().
     Die Demo liegt ausschliesslich hinter ``if __name__ == "__main__":``.
  2. Es gibt KEINE Endlosschleife ohne Stop-Event. Jeder Thread laeuft gegen ein
     threading.Event und terminiert sauber via join().
  3. Reines Python (nur Standardbibliothek: threading, queue, time, os, uuid, ...).
  4. House style: deutsche Docstrings/Kommentare.

Numpy wird hier bewusst NICHT benoetigt (keine Numerik), bleibt aber optional importierbar,
damit ein deterministischer Modul-RNG im Projektstil verfuegbar ist, falls Executoren
Zufall brauchen.
"""

from __future__ import annotations

import os
import time
import uuid
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# Optionaler, deterministischer Modul-RNG im Projektstil (rng = np.random.default_rng(7)).
# Guarded: fehlt numpy, faellt das Framework auf die Standardbibliothek zurueck.
try:  # pragma: no cover - reine Verfuegbarkeitspruefung
    import numpy as _np

    rng = _np.random.default_rng(7)
    _HAS_NUMPY = True
except Exception:  # pragma: no cover
    import random as _random

    rng = _random.Random(7)
    _HAS_NUMPY = False


# =====================================================================
# MESSAGE BUS — gegenseitige, regelmaessige Status-Updates
# =====================================================================

@dataclass
class Message:
    """Eine einzelne Nachricht auf dem Bus (z. B. Heartbeat oder Statusmeldung)."""

    sender: str
    topic: str
    payload: Dict[str, Any]
    ts: float = field(default_factory=time.time)


class MessageBus:
    """
    Thread-sicheres Publish/Subscribe mit zentralem Status-Register.

    Zwei Funktionen in einem:
      - publish/subscribe: lose gekoppelte Themen-Kanaele (Callbacks).
      - status-Register   : jeder Agent hinterlegt periodisch seinen *letzten* Status;
        beliebige Agenten koennen ``latest_status()`` lesen und sich so gegenseitig
        regelmaessig auf dem Laufenden halten.

    Alle oeffentlichen Methoden sind durch ein RLock geschuetzt.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscribers: Dict[str, List[Callable[[Message], None]]] = {}
        self._status: Dict[str, Dict[str, Any]] = {}
        self._history: List[Message] = []
        self._max_history = 1000

    def subscribe(self, topic: str, callback: Callable[[Message], None]) -> None:
        """Registriert ein Callback fuer ein Thema. Callbacks werden synchron aufgerufen."""
        with self._lock:
            self._subscribers.setdefault(topic, []).append(callback)

    def publish(self, sender: str, topic: str, payload: Dict[str, Any]) -> None:
        """Veroeffentlicht eine Nachricht; benachrichtigt alle Abonnenten des Themas."""
        msg = Message(sender=sender, topic=topic, payload=dict(payload))
        with self._lock:
            self._history.append(msg)
            if len(self._history) > self._max_history:
                # Ringpuffer-Verhalten: aelteste Eintraege verwerfen.
                self._history = self._history[-self._max_history:]
            callbacks = list(self._subscribers.get(topic, []))
        # Callbacks ausserhalb des Locks aufrufen, um Deadlocks zu vermeiden.
        for cb in callbacks:
            try:
                cb(msg)
            except Exception:
                # Ein fehlerhaftes Callback darf den Bus nicht blockieren.
                pass

    def update_status(self, agent_id: str, status: Dict[str, Any]) -> None:
        """Hinterlegt/aktualisiert den letzten bekannten Status eines Agenten."""
        with self._lock:
            entry = dict(status)
            entry["ts"] = time.time()
            self._status[agent_id] = entry

    def latest_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Liest den letzten Status eines bestimmten Agenten (oder None)."""
        with self._lock:
            s = self._status.get(agent_id)
            return dict(s) if s is not None else None

    def all_status(self) -> Dict[str, Dict[str, Any]]:
        """Schnappschuss aller bekannten Agenten-Status (flache Kopie)."""
        with self._lock:
            return {aid: dict(s) for aid, s in self._status.items()}

    def history(self) -> List[Message]:
        """Schnappschuss der Nachrichten-Historie (flache Kopie)."""
        with self._lock:
            return list(self._history)


# =====================================================================
# TASK + TASK QUEUE
# =====================================================================

@dataclass
class Task:
    """Eine einzelne Arbeitseinheit, die ein Agent ausfuehrt."""

    name: str
    payload: Dict[str, Any] = field(default_factory=dict)
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    result: Any = None
    done: bool = False
    assigned_to: Optional[str] = None


class TaskQueue:
    """
    Thread-sichere FIFO-Warteschlange.

    Duenner Wrapper um ``queue.Queue``, der genau die im Framework benoetigten
    Operationen bereitstellt (put / get_nowait / depth). ``queue.Queue`` ist
    selbst bereits thread-sicher; der Wrapper haelt die API klein und benannt.
    """

    def __init__(self) -> None:
        self._q: "queue.Queue[Task]" = queue.Queue()

    def put(self, task: Task) -> None:
        """Reiht eine Aufgabe ein."""
        self._q.put(task)

    def get_nowait(self) -> Optional[Task]:
        """Nimmt eine Aufgabe ohne Blockieren; None, wenn die Queue leer ist."""
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def depth(self) -> int:
        """Aktuelle (approximative) Anzahl wartender Aufgaben."""
        return self._q.qsize()

    def empty(self) -> bool:
        """True, wenn aktuell keine Aufgabe wartet."""
        return self._q.empty()


# =====================================================================
# DEFAULT EXECUTOR — deterministische, simulierte Arbeit
# =====================================================================

def default_executor(agent: "Agent", task: Task) -> Any:
    """
    Standard-Executor: simuliert deterministische Arbeit.

    Schlaeft eine kleine, konfigurierbare Zeit (``agent.work_seconds``) und liefert
    ein Ergebnis-Dict zurueck. KEIN Netzwerk, KEIN LLM, vollstaendig deterministisch
    abgesehen von der realen Wanduhrzeit. Pluggable: ein eigener Executor mit der
    Signatur ``(agent, task) -> result`` kann uebergeben werden.
    """
    time.sleep(max(0.0, agent.work_seconds))
    return {
        "task_id": task.task_id,
        "name": task.name,
        "worker": agent.name,
        "echo": task.payload,
    }


# =====================================================================
# AGENT (BASIS)
# =====================================================================

class Agent:
    """
    Basis-Agent mit eigenem Worker-Thread.

    Eigenschaften:
      - id / name / role / inbox (thread-sichere Task-Queue je Agent)
      - laeuft auf eigenem Thread gegen ein Stop-Event (terminiert garantiert)
      - fuehrt zugewiesene Tasks ueber einen pluggable Executor-Callable aus
      - postet alle ``heartbeat_interval`` Sekunden einen Heartbeat auf den Bus
        und aktualisiert das zentrale Status-Register
      - kann Subagenten anstellen (``spawn_subagent``) und entlassen (``dismiss``);
        ein gefuehrtes Roster der Kinder wird mitgefuehrt. ``dismiss`` stoppt den
        Kind-Thread sauber.

    Der Agent ist passiv bis ``start()`` aufgerufen wird; ``stop()``/``join()``
    beenden ihn deterministisch.
    """

    def __init__(
        self,
        name: str,
        role: str = "worker",
        bus: Optional[MessageBus] = None,
        executor: Callable[["Agent", Task], Any] = default_executor,
        heartbeat_interval: float = 0.1,
        work_seconds: float = 0.02,
        poll_interval: float = 0.005,
    ) -> None:
        self.id: str = uuid.uuid4().hex[:8]
        self.name: str = name
        self.role: str = role
        self.bus: MessageBus = bus if bus is not None else MessageBus()
        self.executor = executor
        self.heartbeat_interval = heartbeat_interval
        self.work_seconds = work_seconds
        self.poll_interval = poll_interval

        # Persoenliche Eingangs-Warteschlange (Tasks, die DIESEM Agenten zugewiesen sind).
        self.inbox: TaskQueue = TaskQueue()

        # Roster der angestellten Subagenten (Kinder).
        self._children: Dict[str, "Agent"] = {}
        self._children_lock = threading.RLock()

        # Lebenszyklus-Steuerung.
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_heartbeat = 0.0

        # Buchhaltung.
        self.tasks_done = 0
        self.state = "created"

    # ---- Lebenszyklus -------------------------------------------------

    def start(self) -> None:
        """Startet den Worker-Thread (idempotent)."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self.state = "running"
        self._thread = threading.Thread(target=self._run, name=f"agent-{self.name}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signalisiert dem Worker-Thread das saubere Beenden (nicht blockierend)."""
        self._stop.set()

    def join(self, timeout: Optional[float] = None) -> None:
        """Wartet auf das Ende des Worker-Threads."""
        if self._thread is not None:
            self._thread.join(timeout=timeout)

    def shutdown(self, timeout: float = 2.0) -> None:
        """
        Beendet diesen Agenten UND rekursiv alle Subagenten sauber.

        Reihenfolge: zuerst Kinder entlassen, dann den eigenen Thread stoppen/joinen.
        """
        with self._children_lock:
            children = list(self._children.values())
        for child in children:
            child.shutdown(timeout=timeout)
        with self._children_lock:
            self._children.clear()
        self.stop()
        self.join(timeout=timeout)
        self.state = "stopped"

    # ---- Hire / Fire --------------------------------------------------

    def spawn_subagent(self, name: Optional[str] = None, **kwargs: Any) -> "Agent":
        """
        Stellt einen Subagenten an ("hire").

        Der neue Agent teilt standardmaessig den Bus und Executor des Elternteils,
        wird gestartet und ins Roster aufgenommen. Zusaetzliche kwargs werden an den
        Agent-Konstruktor durchgereicht.
        """
        child_name = name if name is not None else f"{self.name}.sub{len(self._children) + 1}"
        child = Agent(
            name=child_name,
            role=kwargs.pop("role", "worker"),
            bus=kwargs.pop("bus", self.bus),
            executor=kwargs.pop("executor", self.executor),
            heartbeat_interval=kwargs.pop("heartbeat_interval", self.heartbeat_interval),
            work_seconds=kwargs.pop("work_seconds", self.work_seconds),
            poll_interval=kwargs.pop("poll_interval", self.poll_interval),
            **kwargs,
        )
        with self._children_lock:
            self._children[child.id] = child
        child.start()
        self.bus.publish(self.name, "roster", {"event": "hire", "child": child.name, "parent": self.name})
        return child

    def dismiss(self, subagent: "Agent", timeout: float = 2.0) -> bool:
        """
        Entlaesst einen Subagenten ("fire") und stoppt dessen Thread sauber.

        Gibt True zurueck, wenn der Agent im Roster war und beendet wurde.
        """
        with self._children_lock:
            present = subagent.id in self._children
            if present:
                del self._children[subagent.id]
        if present:
            subagent.shutdown(timeout=timeout)
            self.bus.publish(
                self.name, "roster", {"event": "fire", "child": subagent.name, "parent": self.name}
            )
        return present

    def children(self) -> List["Agent"]:
        """Schnappschuss des aktuellen Subagenten-Rosters."""
        with self._children_lock:
            return list(self._children.values())

    # ---- Arbeit -------------------------------------------------------

    def assign(self, task: Task) -> None:
        """Weist diesem Agenten eine Aufgabe zu (legt sie in die persoenliche Inbox)."""
        task.assigned_to = self.name
        self.inbox.put(task)

    def _post_heartbeat(self, extra: Optional[Dict[str, Any]] = None) -> None:
        """Sendet einen Heartbeat auf den Bus und aktualisiert das Status-Register."""
        status = {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "state": self.state,
            "tasks_done": self.tasks_done,
            "backlog": self.inbox.depth(),
        }
        if extra:
            status.update(extra)
        self.bus.update_status(self.id, status)
        self.bus.publish(self.name, "heartbeat", status)
        self._last_heartbeat = time.time()

    def _run(self) -> None:
        """
        Worker-Hauptschleife. Laeuft, bis das Stop-Event gesetzt ist.

        Pro Iteration: ggf. Heartbeat senden, dann eine Task aus der Inbox ziehen
        und ausfuehren. Niemals ohne Stop-Bedingung blockieren.
        """
        self._post_heartbeat()
        while not self._stop.is_set():
            now = time.time()
            if now - self._last_heartbeat >= self.heartbeat_interval:
                self._post_heartbeat()

            task = self.inbox.get_nowait()
            if task is None:
                # Leerlauf: kurz schlafen, damit der Stop schnell greift und die CPU schont.
                self._stop.wait(self.poll_interval)
                continue

            self.state = "busy"
            try:
                task.result = self.executor(self, task)
            except Exception as exc:  # Executor-Fehler werden als Ergebnis vermerkt.
                task.result = {"error": repr(exc)}
            task.done = True
            self.tasks_done += 1
            self.state = "running"
            self.bus.publish(self.name, "task_done", {"task_id": task.task_id, "worker": self.name})

        # Sauberer Abschluss-Heartbeat.
        self.state = "stopping"
        self._post_heartbeat()


# =====================================================================
# SUPERVISOR
# =====================================================================

class Supervisor(Agent):
    """
    Fuehrt eine Belegschaft von Worker-Agenten.

    Verantwortlichkeiten:
      - zieht Tasks aus der gemeinsamen ``TaskQueue`` und weist sie Workern zu
        (least-loaded: der Worker mit der kleinsten Inbox bekommt die naechste Task)
      - SKALIERT HOCH (hire), wenn die Backlog-/Queue-Tiefe einen Schwellwert
        ueberschreitet und noch nicht ``max_workers`` erreicht sind
      - SKALIERT HERUNTER (fire), wenn Worker laenger leer laufen
        (mehr als die Mindestbesetzung vorhanden und Queue + Inboxen leer)
      - aggregiert Worker-Status zu einer Zusammenfassung (``summarize``)
      - faehrt am Ende alle Threads sauber herunter (``shutdown`` der Basisklasse)

    Der Supervisor laeuft selbst auf einem eigenen Thread (geerbt von Agent), nutzt
    aber eine eigene Steuerschleife ``_supervise`` statt der reinen Worker-Schleife.
    """

    def __init__(
        self,
        name: str = "supervisor",
        bus: Optional[MessageBus] = None,
        task_queue: Optional[TaskQueue] = None,
        executor: Callable[["Agent", Task], Any] = default_executor,
        min_workers: int = 1,
        max_workers: Optional[int] = None,
        scale_up_threshold: int = 3,
        idle_rounds_before_fire: int = 3,
        tick_interval: float = 0.02,
        worker_work_seconds: float = 0.02,
        heartbeat_interval: float = 0.1,
    ) -> None:
        super().__init__(
            name=name,
            role="supervisor",
            bus=bus,
            executor=executor,
            heartbeat_interval=heartbeat_interval,
            work_seconds=0.0,
        )
        self.task_queue: TaskQueue = task_queue if task_queue is not None else TaskQueue()
        self.min_workers = max(0, min_workers)
        # Standard-Obergrenze bindet an die Hyperthreading-Kernanzahl (os.cpu_count()).
        self.max_workers = max_workers if max_workers is not None else (os.cpu_count() or 1)
        self.max_workers = max(self.min_workers, self.max_workers)
        self.scale_up_threshold = scale_up_threshold
        self.idle_rounds_before_fire = idle_rounds_before_fire
        self.tick_interval = tick_interval
        self.worker_work_seconds = worker_work_seconds

        # Metriken fuers Abschlussreport.
        self.hires = 0
        self.fires = 0
        self.peak_workforce = 0
        self._idle_rounds = 0

    # ---- Hilfen -------------------------------------------------------

    def _hire(self) -> Agent:
        """Stellt einen Worker an und zaehlt die Einstellung."""
        worker = self.spawn_subagent(
            name=f"{self.name}.w{self.hires + 1}",
            role="worker",
            work_seconds=self.worker_work_seconds,
        )
        self.hires += 1
        return worker

    def _fire_one_idle(self) -> bool:
        """Entlaesst einen leer laufenden Worker, sofern ueber Mindestbesetzung. True bei Erfolg."""
        kids = self.children()
        if len(kids) <= self.min_workers:
            return False
        # Bevorzugt einen Worker mit leerer Inbox entlassen.
        for w in kids:
            if w.inbox.empty():
                self.dismiss(w)
                self.fires += 1
                return True
        return False

    def _least_loaded(self) -> Optional[Agent]:
        """Liefert den Worker mit der geringsten Inbox-Tiefe (oder None, wenn keiner da)."""
        kids = self.children()
        if not kids:
            return None
        return min(kids, key=lambda w: w.inbox.depth())

    def _outstanding(self) -> int:
        """Summe aus Queue-Tiefe und allen noch nicht abgearbeiteten Worker-Inboxen."""
        return self.task_queue.depth() + sum(w.inbox.depth() for w in self.children())

    def summarize(self) -> Dict[str, Any]:
        """
        Aggregiert die aktuellen Worker-Status zu einer Zusammenfassung.

        Liest bewusst aus dem zentralen Status-Register des Bus (gegenseitige Updates),
        nicht direkt aus den Worker-Objekten, um den Bus-Mechanismus zu nutzen.
        """
        kids = self.children()
        per_worker = []
        total_done = 0
        for w in kids:
            s = self.bus.latest_status(w.id) or {}
            done = int(s.get("tasks_done", w.tasks_done))
            total_done += done
            per_worker.append(
                {"name": w.name, "state": s.get("state", w.state), "backlog": s.get("backlog", w.inbox.depth()), "done": done}
            )
        return {
            "supervisor": self.name,
            "workers": len(kids),
            "queue_depth": self.task_queue.depth(),
            "outstanding": self._outstanding(),
            "worker_tasks_done": total_done,
            "per_worker": per_worker,
        }

    # ---- Steuerschleife (ueberschreibt die reine Worker-Schleife) ----

    def _run(self) -> None:
        """Startet die Supervisions-Schleife statt der Basis-Worker-Schleife."""
        self._supervise()

    def _supervise(self) -> None:
        """
        Haupt-Steuerschleife des Supervisors. Terminiert beim Stop-Event ODER wenn
        keine Arbeit mehr aussteht (Queue leer und alle Inboxen leer).

        Pro Tick:
          1) Heartbeat / Status aktualisieren.
          2) Tasks aus der Queue an least-loaded Worker verteilen.
          3) Auto-Skalierung: hire bei Backlog ueber Schwelle, fire bei anhaltendem Leerlauf.
        """
        # Mindestbesetzung sicherstellen.
        while len(self.children()) < self.min_workers:
            self._hire()

        self._post_heartbeat()
        while not self._stop.is_set():
            now = time.time()
            if now - self._last_heartbeat >= self.heartbeat_interval:
                summary = self.summarize()
                self._post_heartbeat(extra={"summary": summary})

            # --- (2) Verteilung: alle aktuell verfuegbaren Tasks zuteilen. ---
            # Bei Bedarf VOR der Zuteilung hochskalieren, damit neue Worker sofort Last bekommen.
            if self.task_queue.depth() >= self.scale_up_threshold and len(self.children()) < self.max_workers:
                self._hire()

            assigned_this_tick = 0
            # Nicht mehr Tasks ziehen als (lose) sinnvoll: ein paar pro Worker pro Tick.
            max_pull = max(1, len(self.children()))
            while assigned_this_tick < max_pull:
                if len(self.children()) == 0:
                    self._hire()
                task = self.task_queue.get_nowait()
                if task is None:
                    break
                worker = self._least_loaded()
                if worker is None:
                    # Sollte nicht passieren, aber sicher ist sicher: Task zuruecklegen.
                    self.task_queue.put(task)
                    break
                worker.assign(task)
                assigned_this_tick += 1

            # Peak-Belegschaft mitschreiben.
            self.peak_workforce = max(self.peak_workforce, len(self.children()))

            # --- (3) Skalierung herunter / Terminierung pruefen. ---
            outstanding = self._outstanding()
            if outstanding == 0 and assigned_this_tick == 0:
                self._idle_rounds += 1
                # Leer laufende Worker abbauen.
                if self._idle_rounds >= self.idle_rounds_before_fire:
                    fired = self._fire_one_idle()
                    if not fired:
                        # Nichts mehr zu tun und Belegschaft auf Minimum: fertig.
                        break
            else:
                self._idle_rounds = 0

            self._stop.wait(self.tick_interval)

        # Abschluss-Heartbeat mit finaler Zusammenfassung.
        self.state = "stopping"
        self._post_heartbeat(extra={"summary": self.summarize()})

    # ---- Komfort ------------------------------------------------------

    def run_until_drained(self, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Startet den Supervisor, wartet bis die Queue abgearbeitet ist (oder timeout),
        faehrt dann alles sauber herunter und liefert den Abschlussreport.
        """
        self.start()
        self.join(timeout=timeout)
        self.shutdown(timeout=2.0)
        return self.report()

    def report(self) -> Dict[str, Any]:
        """Erstellt den Abschlussreport (Tasks done, Peak-Belegschaft, Hires, Fires)."""
        # Tasks done summieren wir aus dem letzten bekannten Status der (ehemaligen) Worker.
        statuses = self.bus.all_status()
        worker_done = sum(
            int(s.get("tasks_done", 0))
            for aid, s in statuses.items()
            if s.get("role") == "worker"
        )
        return {
            "tasks_done": worker_done,
            "peak_workforce": self.peak_workforce,
            "hires": self.hires,
            "fires": self.fires,
            "remaining_in_queue": self.task_queue.depth(),
        }


# =====================================================================
# DEMO (nur unter __main__ — import-sicher)
# =====================================================================

def _demo() -> None:
    """
    Kleine, schnelle Demonstration:
      - Supervisor anlegen, ~20 Tasks einreihen
      - zusehen, wie hoch- (hire) und herunterskaliert (fire) wird
      - periodische Cross-Updates aus dem Bus ausgeben
      - Abschlussreport drucken

    Laeuft in wenigen Sekunden.
    """
    bus = MessageBus()
    tq = TaskQueue()

    # Live-Mitschnitt der gegenseitigen Updates (Roster-Events + ein paar Heartbeats).
    log_lock = threading.Lock()

    def on_roster(msg: Message) -> None:
        with log_lock:
            ev = msg.payload.get("event")
            print(f"  [roster] {ev:>4}  {msg.payload.get('child')}  (durch {msg.payload.get('parent')})")

    bus.subscribe("roster", on_roster)

    sup = Supervisor(
        name="boss",
        bus=bus,
        task_queue=tq,
        min_workers=1,
        max_workers=min(6, (os.cpu_count() or 1)),
        scale_up_threshold=3,
        idle_rounds_before_fire=3,
        tick_interval=0.02,
        worker_work_seconds=0.03,
        heartbeat_interval=0.15,
    )

    # ~20 Tasks einreihen.
    for i in range(20):
        tq.put(Task(name=f"job-{i:02d}", payload={"i": i}))

    print(f"Fusion Hero OS — Multi-Agent Demo  (cpu_count={os.cpu_count()}, numpy={_HAS_NUMPY})")
    print(f"Eingereiht: {tq.depth()} Tasks. Starte Supervisor (max_workers={sup.max_workers}) ...\n")

    sup.start()

    # Periodische Cross-Updates ausgeben, bis der Supervisor-Thread terminiert.
    last_print = 0.0
    while sup._thread is not None and sup._thread.is_alive():
        now = time.time()
        if now - last_print >= 0.2:
            summ = sup.summarize()
            print(
                f"  [status] workers={summ['workers']} queue={summ['queue_depth']} "
                f"outstanding={summ['outstanding']} done={summ['worker_tasks_done']}"
            )
            last_print = now
        time.sleep(0.05)

    sup.join(timeout=5.0)
    sup.shutdown(timeout=2.0)

    report = sup.report()
    print("\n=== ABSCHLUSSREPORT ===")
    print(f"  Tasks erledigt    : {report['tasks_done']}")
    print(f"  Peak-Belegschaft  : {report['peak_workforce']}")
    print(f"  Einstellungen     : {report['hires']}")
    print(f"  Entlassungen      : {report['fires']}")
    print(f"  Rest in Queue     : {report['remaining_in_queue']}")


if __name__ == "__main__":
    _demo()
