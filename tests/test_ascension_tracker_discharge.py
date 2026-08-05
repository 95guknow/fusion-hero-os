# -*- coding: utf-8 -*-
"""Discharge der Tracker-/Protokoll-Schicht: Stage9, Oszillation, Psycholyse-Logger.

Belegt die STRUKTURELLEN Invarianten dreier Module, deren Anspruch bisher
nur im Docstring stand. Ein Befund verdient Hervorhebung: Der Stage-Schaetzer
kann mit vorhandener Historie die Stufe 0 nicht erreichen — sie ist
ausschliesslich der Kein-Daten-Fall. Das folgt aus der Zufriedenheitsuntergrenze
0.3 (ASC-SISYPHOS-REDUNDANZ-BEFUNDE) und macht das Label "Unbestimmt (keine
Daten)" zur exakt richtigen Beschreibung.

Was hier ausdruecklich NICHT behauptet wird:
  * dass der Stage-Wert eine psychologische Entwicklungsstufe misst. Er ist
    ein Proxy ueber eine Zeitreihe; die Deutung bleibt MODELL (Dissertation
    4.1). Das Modul sagt das selbst — hier wird nur die Rechnung geprueft.
  * dass die Oszillationsschwelle 7 empirisch begruendet ist. Sie stammt aus
    einer Quelle ohne Einheitsangabe und ist hier als Richtungswechsel-Anzahl
    interpretiert (MODELL, so im Modul deklariert).

Konvention: In proof_registry.yaml zitierte Knoten sind NICHT parametrisiert.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ascension_os.core.persistent_sisyphos import PersistentSisyphosCycle
from ascension_os.core.psycholyse_protocol_logger import (
    VALID_STATUS_TAGS,
    PsycholyseProtocolLogger,
)
from ascension_os.core.sisyphos_oscillation_visualizer import (
    SPARK_CHARS,
    SisyphosOscillationVisualizer,
)
from ascension_os.core.stage9_tracker import STAGE_LABELS, Stage9AscensionTracker


def _cycle(tmp_path: Path, loads=(), **kw) -> PersistentSisyphosCycle:
    c = PersistentSisyphosCycle(persistence_path=str(tmp_path / "s.json"), **kw)
    for l in loads:
        c.step(l)
    return c


# ==========================================================================
# Stage9AscensionTracker — Wertebereich, Totalitaet, Nullstufe
# ==========================================================================

def test_stage_estimate_always_within_zero_to_nine(tmp_path: Path) -> None:
    """Der Schaetzwert verlaesst [0, 9] nie — auch bei Extremverlaeufen nicht."""
    for loads in (
        (),                       # keine Historie
        (0.0,),                   # ein Punkt
        (0.0,) * 60,              # dauerhaft minimale Last
        (1.0,) * 60,              # dauerhaft maximale Last
        (0.0, 1.0) * 30,          # maximale Amplitude
        tuple(i / 60 for i in range(60)),
    ):
        c = _cycle(tmp_path / f"c{len(loads)}{loads[:1]}", loads)
        snap = Stage9AscensionTracker(sisyphos=c).get_stage_estimate()
        assert 0 <= snap.stage_estimate <= 9, f"ausserhalb bei {loads[:4]}..."


def test_stage_label_mapping_is_total(tmp_path: Path) -> None:
    """Zu jedem erreichbaren Schaetzwert existiert ein Label."""
    assert set(STAGE_LABELS) == set(range(10))
    for loads in ((), (0.5,), (0.2,) * 40, (0.95,) * 40):
        c = _cycle(tmp_path / f"l{len(loads)}", loads)
        snap = Stage9AscensionTracker(sisyphos=c).get_stage_estimate()
        assert snap.label == STAGE_LABELS[snap.stage_estimate]


def test_stage_zero_is_exclusively_the_no_data_case(tmp_path: Path) -> None:
    """Stufe 0 ist mit Historie unerreichbar.

    Aus satisfaction >= 0.3 (ASC-SISYPHOS-REDUNDANZ-BEFUNDE) folgt
    avg_satisfaction * 6 >= 1.8, also int(...) >= 1. Zusaetzlich vergibt schon
    eine einpunktige Historie den Amplituden-Bonus. Damit ist Stufe 0 exakt
    der Fall "keine Sisyphos-Historie" — genau das, was ihr Label sagt.
    """
    leer = Stage9AscensionTracker(sisyphos=None).get_stage_estimate()
    assert leer.stage_estimate == 0
    assert leer.label == STAGE_LABELS[0]
    assert "keine" in leer.basis.get("reason", "").lower()

    ohne_history = _cycle(tmp_path / "leer", ())
    assert Stage9AscensionTracker(sisyphos=ohne_history).get_stage_estimate().stage_estimate == 0

    for loads in ((1.0,), (1.0,) * 40, (0.0,) * 40, (0.0, 1.0) * 20):
        c = _cycle(tmp_path / f"h{len(loads)}{loads[0]}", loads)
        snap = Stage9AscensionTracker(sisyphos=c).get_stage_estimate()
        assert snap.stage_estimate >= 1, (
            f"Stufe 0 trotz Historie bei {loads[:3]}... — Untergrenze verletzt"
        )


def test_stage_snapshots_accumulate_and_carry_their_basis(tmp_path: Path) -> None:
    """Jede Schaetzung wird protokolliert und traegt ihre Rechengrundlage."""
    c = _cycle(tmp_path, (0.3, 0.4, 0.35, 0.45))
    t = Stage9AscensionTracker(sisyphos=c)
    t.get_stage_estimate()
    t.get_stage_estimate()
    assert len(t.snapshots) == 2
    basis = t.snapshots[-1].basis
    for key in ("avg_satisfaction", "is_currently_sustainable",
                "oscillation_amplitude", "total_cycles", "window"):
        assert key in basis, f"Basis unvollstaendig: {key} fehlt"


# ==========================================================================
# SisyphosOscillationVisualizer — Sparkline, Amplitude, Schwelle
# ==========================================================================

def test_sparkline_length_matches_series_and_uses_only_declared_chars(tmp_path: Path) -> None:
    """Ein Zeichen je Datenpunkt, ausschliesslich aus SPARK_CHARS."""
    c = _cycle(tmp_path, tuple(i / 25 for i in range(25)))
    rep = SisyphosOscillationVisualizer(sisyphos=c).build_report(last_n=25)
    assert rep.n_points == 25
    assert len(rep.sparkline) == 25
    assert set(rep.sparkline) <= set(SPARK_CHARS)
    assert len(rep.series) == 25


def test_constant_series_does_not_divide_by_zero(tmp_path: Path) -> None:
    """Konstante Last: Spannweite 0 wird abgefangen, Amplitude ist 0."""
    c = _cycle(tmp_path, (0.5,) * 10)
    rep = SisyphosOscillationVisualizer(sisyphos=c).build_report(last_n=10)
    assert rep.amplitude == pytest.approx(0.0)
    assert len(rep.sparkline) == 10
    assert len(set(rep.sparkline)) == 1
    assert rep.reversal_count == 0


def test_empty_history_yields_an_empty_but_valid_report() -> None:
    """Ohne Historie: kein Absturz, keine erfundene Kennzahl."""
    rep = SisyphosOscillationVisualizer(sisyphos=None).build_report()
    assert rep.n_points == 0
    assert rep.sparkline == ""
    assert rep.series == []
    assert rep.amplitude == pytest.approx(0.0)
    assert rep.within_threshold is None, "ohne Daten darf keine Schwelle behauptet werden"


def test_within_threshold_tracks_the_reversal_bound(tmp_path: Path) -> None:
    """within_threshold ist genau reversal_count < reversal_threshold."""
    c = _cycle(tmp_path, (0.1, 0.9) * 12)  # viele Umkehrungen
    vis = SisyphosOscillationVisualizer(sisyphos=c)
    rep = vis.build_report(last_n=24, reversal_threshold=7)
    assert rep.reversal_count >= 7
    assert rep.within_threshold is False

    ruhig = _cycle(tmp_path / "ruhig", tuple(0.3 + i / 200 for i in range(20)))
    rep2 = SisyphosOscillationVisualizer(sisyphos=ruhig).build_report(
        last_n=20, reversal_threshold=7
    )
    assert rep2.within_threshold == (rep2.reversal_count < 7)


def test_svg_render_is_wellformed_and_honest_when_empty(tmp_path: Path) -> None:
    """SVG ohne Fremdbibliothek; ohne Daten wird das ausgesprochen."""
    leer = SisyphosOscillationVisualizer(sisyphos=None).render_svg()
    assert leer.startswith("<svg") and leer.rstrip().endswith("</svg>")
    assert "Keine Sisyphos-Historie" in leer

    c = _cycle(tmp_path, (0.2, 0.6, 0.4, 0.8))
    svg = SisyphosOscillationVisualizer(sisyphos=c).render_svg()
    assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")
    assert "Keine Sisyphos-Historie" not in svg


# ==========================================================================
# PsycholyseProtocolLogger — Pflicht-Status, keine stille Verifikation
# ==========================================================================

def test_psycholyse_status_tag_is_mandatory_and_checked(tmp_path: Path) -> None:
    """Ein unbekannter Status wird abgewiesen — kein Default auf 'verifiziert'.

    Das ist die eigentliche Leistung des Moduls: Eine Sitzung laesst sich nicht
    ablegen, ohne zu erklaeren, welchen Beleggrad ihre Angaben haben.
    """
    log = PsycholyseProtocolLogger(persistence_path=str(tmp_path / "p.json"))
    for bad in ("verifiziert", "verified", "", "SELF_REPORTED", "sonstiges"):
        with pytest.raises(ValueError):
            log.log_session("protokoll", bad)

    assert "unverified" in VALID_STATUS_TAGS
    for good in VALID_STATUS_TAGS:
        entry = log.log_session("protokoll", good)
        assert entry.status == good


def test_psycholyse_session_ids_are_consecutive(tmp_path: Path) -> None:
    """Fortlaufende Nummerierung ohne Luecken."""
    log = PsycholyseProtocolLogger(persistence_path=str(tmp_path / "p.json"))
    ids = [log.log_session("p", "self_reported").session_id for _ in range(5)]
    assert ids == [1, 2, 3, 4, 5]


def test_psycholyse_entries_survive_a_roundtrip(tmp_path: Path) -> None:
    """Eintraege ueberleben einen Neustart aus der Datei."""
    path = tmp_path / "p.json"
    log = PsycholyseProtocolLogger(persistence_path=str(path))
    log.log_session("oster", "self_reported", notes="n1")
    log.log_session("regulaer", "observed", notes="n2")

    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    # Auf Platte liegt ein Objekt mit Schluessel "entries", keine nackte Liste.
    assert isinstance(payload, dict) and "entries" in payload
    assert len(payload["entries"]) == 2

    log2 = PsycholyseProtocolLogger(persistence_path=str(path))
    assert [e.notes for e in log2.entries] == ["n1", "n2"]
    assert [e.status for e in log2.entries] == ["self_reported", "observed"]
    # Fortsetzung nummeriert korrekt weiter.
    assert log2.log_session("p", "unverified").session_id == 3
