# -*- coding: utf-8 -*-
"""connectors.py — Typisierte Wrapper für die HEROIC_SKILL.md-Connectoren.

Dieses Modul stellt typisierte Wrapper-Klassen für die in ``HEROIC_SKILL.md``
beschriebenen Service-Anbindungen bereit:

    GitHubConnector, DriveConnector, VercelConnector, GmailConnector, XAPIConnector

sowie eine ``ConnectorRegistry``, die diese Connectoren hält und meldet, welche
davon ``available`` (verfügbar) sind.

==============================================================================
SICHERHEITS-LEITSATZ — KEINE ECHTEN AUSSENWIRKUNGEN PER DEFAULT
==============================================================================
Jeder Connector ist ein *typisierter Wrapper* mit klarer Schnittstelle. Ohne
einen explizit injizierten echten Client (``client``/Callable) führt **keine**
Methode eine echte Aktion aus. Stattdessen liefert jede Operation einen
strukturierten DRY-RUN-Plan als ``dict`` zurück:

    {
        "connector": "<Name>",
        "action":    "<Operationsname>",
        "args":      { ... },          # die übergebenen Argumente
        "would_execute": False,        # False = es passiert nichts real
        "available": False,            # ob ein echter Client vorhanden ist
        "note":      "<Erläuterung>",
    }

Erst wenn ein echter Client injiziert wird (``available == True``), werden die
Operationen an diesen Client delegiert (``would_execute == True``). Die
Delegation ist die einzige Stelle, an der eine reale Aussenwirkung möglich
wäre — und sie ist vollständig in der Hand des Aufrufers, der den Client
bereitstellt. Dieses Modul selbst öffnet niemals von sich aus Netzwerk,
versendet keine E-Mails, deployt nichts und schreibt keine API-Aufrufe.

Import-Sicherheit:
- Keine Top-Level-Seiteneffekte, keine Netzwerkaufrufe beim Import.
- Optionale Bibliotheken werden defensiv geladen (try/except -> available=False).
- Eine Demo (Ausdruck der DRY-RUN-Pläne) ist hinter ``if __name__ == "__main__"``
  gekapselt.

Hausstil: deutsche Docstrings; optionaler Modul-RNG nur falls benötigt.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Optionaler RNG im Hausstil (deterministisch). Wird hier nicht zwingend
# gebraucht, ist aber zur Konsistenz mit den anderen Modulen vorhanden.
# ---------------------------------------------------------------------------
try:  # pragma: no cover - rein defensiv, numpy ist im Projekt vorhanden
    import numpy as _np

    rng = _np.random.default_rng(7)
except Exception:  # pragma: no cover
    rng = None  # numpy nicht verfügbar -> kein RNG, aber Modul bleibt importierbar


# ---------------------------------------------------------------------------
# Basis-Connector
# ---------------------------------------------------------------------------
class BaseConnector:
    """Gemeinsame Basis für alle Connectoren.

    Ein Connector kapselt einen optional injizierten echten ``client``. Solange
    kein Client vorhanden ist, ist der Connector *nicht verfügbar*
    (``available == False``) und jede Operation liefert ausschliesslich einen
    DRY-RUN-Plan zurück — es findet keine reale Aktion statt.

    Parameter
    ---------
    client:
        Optionaler echter Client (beliebiges Objekt) oder Callable. Wird er
        übergeben, gilt der Connector als verfügbar und Operationen werden an
        ihn delegiert. Ohne Client bleibt alles ein DRY-RUN.
    name:
        Optionaler Anzeigename; default ist der Klassenname.
    """

    #: Sprechender Modul-Name aus HEROIC_SKILL.md (Connectoren-Abschnitt).
    skill_module: str = "GenericCoreModule"

    def __init__(self, client: Optional[Any] = None, name: Optional[str] = None) -> None:
        self._client = client
        self.name = name or self.__class__.__name__

    # -- Verfügbarkeit ------------------------------------------------------
    @property
    def available(self) -> bool:
        """True, wenn ein echter Client injiziert wurde, sonst False."""
        return self._client is not None

    def _dry_run(self, action: str, **args: Any) -> Dict[str, Any]:
        """Erzeugt einen strukturierten DRY-RUN-Plan (keine reale Aktion).

        Der Plan dokumentiert die *beabsichtigte* Operation und ihre Argumente,
        ohne irgendetwas auszuführen. ``would_execute`` ist immer ``False``.
        """
        return {
            "connector": self.name,
            "skill_module": self.skill_module,
            "action": action,
            "args": dict(args),
            "would_execute": False,
            "available": False,
            "note": (
                "DRY-RUN: kein echter Client injiziert — es wurde nichts "
                "ausgefuehrt. Injiziere einen Client, um real zu delegieren."
            ),
        }

    def _delegate(self, action: str, method_name: str, **args: Any) -> Dict[str, Any]:
        """Delegiert eine Operation an den echten Client — oder DRY-RUN.

        Ohne Client wird ein DRY-RUN-Plan zurückgegeben. Mit Client wird
        versucht, ``client.<method_name>(**args)`` aufzurufen; das Ergebnis wird
        in eine strukturierte Antwort verpackt (``would_execute == True``).

        Diese Methode ist die einzige Stelle mit potenzieller Aussenwirkung —
        und nur dann, wenn der Aufrufer bewusst einen echten Client bereitstellt.
        """
        if not self.available:
            return self._dry_run(action, **args)

        client = self._client
        # Client kann ein Objekt mit Methode ODER ein generisches Callable sein.
        if callable(client) and not hasattr(client, method_name):
            result = client(action, args)
        else:
            method = getattr(client, method_name, None)
            if method is None or not callable(method):
                raise NotImplementedError(
                    f"Injizierter Client fuer {self.name} besitzt keine "
                    f"aufrufbare Methode '{method_name}'."
                )
            result = method(**args)

        return {
            "connector": self.name,
            "skill_module": self.skill_module,
            "action": action,
            "args": dict(args),
            "would_execute": True,
            "available": True,
            "result": result,
            "note": "Operation an echten Client delegiert.",
        }

    def status(self) -> Dict[str, Any]:
        """Knappe Statusbeschreibung des Connectors."""
        return {
            "connector": self.name,
            "skill_module": self.skill_module,
            "available": self.available,
        }

    def __repr__(self) -> str:  # pragma: no cover - kosmetisch
        return f"<{self.__class__.__name__} name={self.name!r} available={self.available}>"


# ---------------------------------------------------------------------------
# Konkrete Connectoren
# ---------------------------------------------------------------------------
class GitHubConnector(BaseConnector):
    """Wrapper für GitHub-Operationen (vgl. GitHubCoreModule).

    Repos verwalten, Methodik-Änderungen committen, Versions-Tags setzen.
    Ohne injizierten Client liefert jede Methode einen DRY-RUN-Plan; es wird
    nichts committed, gepusht oder getaggt.
    """

    skill_module = "GitHubCoreModule"

    def commit(
        self,
        repo: str,
        message: str,
        files: Optional[Dict[str, str]] = None,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """Plant/führt einen Commit aus (DRY-RUN ohne Client)."""
        return self._delegate(
            "commit",
            "commit",
            repo=repo,
            message=message,
            files=files or {},
            branch=branch,
        )

    def tag(self, repo: str, tag: str, ref: str = "HEAD") -> Dict[str, Any]:
        """Plant/setzt einen Versions-Tag (DRY-RUN ohne Client)."""
        return self._delegate("tag", "tag", repo=repo, tag=tag, ref=ref)

    def create_repo(self, name: str, private: bool = True) -> Dict[str, Any]:
        """Plant/legt ein Repository an (DRY-RUN ohne Client)."""
        return self._delegate("create_repo", "create_repo", name=name, private=private)


class DriveConnector(BaseConnector):
    """Wrapper für Drive-Ablage (vgl. DriveCoreModule).

    Archive ablegen/abrufen, mit Datumsstempel versionieren. Ohne injizierten
    Client liefert jede Methode einen DRY-RUN-Plan; es werden keine Dateien
    hochgeladen oder heruntergeladen.
    """

    skill_module = "DriveCoreModule"

    def upload(self, path: str, folder: Optional[str] = None) -> Dict[str, Any]:
        """Plant/führt einen Upload aus (DRY-RUN ohne Client)."""
        return self._delegate("upload", "upload", path=path, folder=folder)

    def download(self, file_id: str, dest: str) -> Dict[str, Any]:
        """Plant/führt einen Download aus (DRY-RUN ohne Client)."""
        return self._delegate("download", "download", file_id=file_id, dest=dest)

    def list_files(self, folder: Optional[str] = None) -> Dict[str, Any]:
        """Plant/listet Dateien (DRY-RUN ohne Client)."""
        return self._delegate("list_files", "list_files", folder=folder)


class VercelConnector(BaseConnector):
    """Wrapper für Vercel-Deployments (vgl. VercelDeploymentConnectorCoreModule).

    Statische/dynamische Deployments. Pre-Build-Checks (Tests, Lints,
    Schema-Validierung) sind frei wählbar und werden hier nur als Plan-Metadaten
    geführt. Ohne injizierten Client liefert jede Methode einen DRY-RUN-Plan; es
    wird nichts real deployt.
    """

    skill_module = "VercelDeploymentConnectorCoreModule"

    def deploy(
        self,
        project: str,
        directory: str = ".",
        production: bool = False,
        pre_build_checks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Plant/führt ein Deployment aus (DRY-RUN ohne Client)."""
        return self._delegate(
            "deploy",
            "deploy",
            project=project,
            directory=directory,
            production=production,
            pre_build_checks=list(pre_build_checks or []),
        )

    def list_deployments(self, project: str) -> Dict[str, Any]:
        """Plant/listet Deployments (DRY-RUN ohne Client)."""
        return self._delegate("list_deployments", "list_deployments", project=project)


class GmailConnector(BaseConnector):
    """Wrapper für Gmail (vgl. GmailCoreModule).

    Strukturierte Reports versenden, Antworten parsen. Ohne injizierten Client
    liefert jede Methode einen DRY-RUN-Plan; es wird **keine** E-Mail versendet.
    """

    skill_module = "GmailCoreModule"

    def send(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Plant/versendet eine E-Mail (DRY-RUN ohne Client)."""
        return self._delegate(
            "send",
            "send",
            to=to,
            subject=subject,
            body=body,
            attachments=list(attachments or []),
        )

    def parse_replies(self, query: str = "is:unread") -> Dict[str, Any]:
        """Plant/parst Antworten (DRY-RUN ohne Client)."""
        return self._delegate("parse_replies", "parse_replies", query=query)


class XAPIConnector(BaseConnector):
    """Wrapper für die X-API (vgl. XAPICoreModule).

    Recherche und Trend-Beobachtung. Per Default nur Lese-/Suchoperationen.
    Schreiboperationen (``post``) sind bewusst gesperrt: ohne explizit
    schreibfähigen Client wird **nicht** gepostet. Ohne injizierten Client
    liefert jede Methode einen DRY-RUN-Plan.

    Parameter
    ---------
    allow_write:
        Muss ausdrücklich ``True`` sein, damit ``post`` überhaupt an einen
        echten Client delegiert. Andernfalls bleibt ``post`` ein DRY-RUN bzw.
        meldet, dass Schreiben nicht freigegeben ist.
    """

    skill_module = "XAPICoreModule"

    def __init__(
        self,
        client: Optional[Any] = None,
        name: Optional[str] = None,
        allow_write: bool = False,
    ) -> None:
        super().__init__(client=client, name=name)
        self.allow_write = bool(allow_write)

    def search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Plant/führt eine Suche aus (Lese-Operation; DRY-RUN ohne Client)."""
        return self._delegate("search", "search", query=query, limit=limit)

    def trends(self, region: str = "worldwide") -> Dict[str, Any]:
        """Plant/liest Trends (Lese-Operation; DRY-RUN ohne Client)."""
        return self._delegate("trends", "trends", region=region)

    def post(self, text: str) -> Dict[str, Any]:
        """Schreiboperation — per Default GESPERRT.

        Ohne ``allow_write=True`` wird niemals gepostet; es kommt ein
        DRY-RUN-Plan mit deutlichem Hinweis zurück.
        """
        if not self.allow_write:
            plan = self._dry_run("post", text=text)
            plan["note"] = (
                "DRY-RUN: Schreiben ist gesperrt (allow_write=False). Es wurde "
                "NICHTS gepostet. Setze allow_write=True UND injiziere einen "
                "schreibfaehigen Client, um real zu posten."
            )
            return plan
        return self._delegate("post", "post", text=text)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
@dataclass
class ConnectorRegistry:
    """Hält die Connectoren und meldet deren Verfügbarkeit.

    Per Default werden alle fünf Connectoren *ohne* echten Client angelegt —
    d. h. ``available()`` liefert für alle ``False`` und sämtliche Operationen
    sind DRY-RUNs. Echte Clients können nachträglich via :meth:`inject`
    bereitgestellt werden.
    """

    connectors: Dict[str, BaseConnector] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "ConnectorRegistry":
        """Erzeugt eine Registry mit allen fünf Standard-Connectoren (DRY-RUN)."""
        reg = cls()
        reg.register(GitHubConnector())
        reg.register(DriveConnector())
        reg.register(VercelConnector())
        reg.register(GmailConnector())
        reg.register(XAPIConnector())
        return reg

    # -- Verwaltung ---------------------------------------------------------
    def register(self, connector: BaseConnector) -> None:
        """Registriert einen Connector unter seinem ``name``."""
        self.connectors[connector.name] = connector

    def get(self, name: str) -> Optional[BaseConnector]:
        """Gibt den Connector zu ``name`` zurück (oder None)."""
        return self.connectors.get(name)

    def inject(self, name: str, client: Any) -> bool:
        """Injiziert nachträglich einen echten Client in einen Connector.

        Gibt True zurück, wenn der Connector existiert, sonst False. Erst nach
        dieser Injektion ist der betreffende Connector ``available``.
        """
        connector = self.connectors.get(name)
        if connector is None:
            return False
        connector._client = client
        return True

    # -- Berichte -----------------------------------------------------------
    def available(self) -> Dict[str, bool]:
        """Verfügbarkeits-Übersicht: ``{name: available}``."""
        return {name: c.available for name, c in self.connectors.items()}

    def plan(self) -> Dict[str, Dict[str, Any]]:
        """Plan-Übersicht: pro Connector Status + Sicherheitshinweis.

        Reine Beschreibung; löst keinerlei Operation aus.
        """
        summary: Dict[str, Dict[str, Any]] = {}
        for name, c in self.connectors.items():
            summary[name] = {
                "skill_module": c.skill_module,
                "available": c.available,
                "mode": "LIVE" if c.available else "DRY-RUN",
                "note": (
                    "Echter Client injiziert — Operationen wirken real."
                    if c.available
                    else "Kein Client — alle Operationen sind DRY-RUNs."
                ),
            }
        return summary


# ---------------------------------------------------------------------------
# Demo (nur bei direktem Aufruf; keine Seiteneffekte beim Import)
# ---------------------------------------------------------------------------
def _demo() -> None:
    """Druckt die DRY-RUN-Pläne aller Standard-Connectoren."""
    import json

    reg = ConnectorRegistry.default()

    print("=== Verfuegbarkeit (alle False = DRY-RUN) ===")
    print(json.dumps(reg.available(), indent=2, ensure_ascii=False))

    print("\n=== Plan-Uebersicht ===")
    print(json.dumps(reg.plan(), indent=2, ensure_ascii=False))

    print("\n=== Beispiel-DRY-RUN-Plaene ===")
    gh = reg.get("GitHubConnector")
    dr = reg.get("DriveConnector")
    vc = reg.get("VercelConnector")
    gm = reg.get("GmailConnector")
    xa = reg.get("XAPIConnector")

    plans = [
        gh.commit("95guknow/fusion-hero-os", "docs: update HEROIC_SKILL.md",
                  files={"HEROIC_SKILL.md": "..."}, branch="main"),
        gh.tag("95guknow/fusion-hero-os", "v5.26"),
        dr.upload("Archiv_2026-06-28.zip", folder="HeroicArchive"),
        vc.deploy("dashboard", directory="03_Code/Dashboard",
                  production=False, pre_build_checks=["pytest", "ruff"]),
        gm.send("user@example.com", "Report Stufe 5/5",
                "Zusammenfassung im Anhang.", attachments=["report.pdf"]),
        xa.search("QUBO annealing", limit=10),
        xa.post("Dieser Post wird NICHT gesendet (allow_write=False)."),
    ]

    for plan in plans:
        print(json.dumps(plan, indent=2, ensure_ascii=False))

    # Nachweis: nichts davon hat real gewirkt.
    assert all(not p["would_execute"] for p in plans), "DRY-RUN-Garantie verletzt!"
    print("\nOK: Alle Operationen waren DRY-RUNs (would_execute=False).")


if __name__ == "__main__":
    _demo()
