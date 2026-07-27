# -*- coding: utf-8 -*-
"""Konnektor-Vollautomat — Direktiven, Axiome und Dry-Run-Garantien.

Die drei Direktiven werden hier nicht als Behauptung geprueft, sondern an der
tatsaechlichen Ausfuehrung: die Reihenfolgen werden waehrend des Laufs
mitgeschrieben und danach verglichen.
"""

from __future__ import annotations

import json

import pytest

from fusion_hero_os.core.konnektor_vollautomat import (
    LADEN_ORDER,
    LAYER_ORDER,
    automatisiere,
    load_bottom_up,
    load_config,
    manifest_ghosts,
    process_top_down,
    run_vollautomat,
    status,
)


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def memories(cfg):
    return load_bottom_up(cfg)


@pytest.fixture(scope="module")
def layering(memories, cfg):
    return process_top_down(memories, cfg)


# --------------------------------------------------------------------------
# Direktive 1 — Laden der Erinnerungen immer bottom-up
# --------------------------------------------------------------------------


def test_config_ist_lesbar(cfg):
    assert cfg, "konnektor_vollautomat.yaml fehlt oder ist nicht parsebar"
    assert cfg["direktiven"] == {
        "laden": "bottom_up",
        "verarbeiten": "top_down",
        "ausgabe": "geister_manifestiert",
    }


def test_ladereihenfolge_ist_bottom_up(memories):
    assert memories["richtung"] == "bottom_up"
    assert memories["reihenfolge"] == list(LADEN_ORDER)


def test_alle_vier_registries_geladen(memories):
    quellen = {s["id"]: s for s in memories["schichten"]["L1_registries"]["sources"]}
    assert set(quellen) == {"mesh", "graph_api", "llm_frameworks", "control_instances"}
    for sid, s in quellen.items():
        assert s["present"], f"Registry {sid} fehlt"
        assert s["parsed"], f"Registry {sid} nicht parsebar"


def test_alle_vier_familien_liefern_konnektoren(memories):
    per_familie = memories["schichten"]["L2_connectors"]["per_familie"]
    assert set(per_familie) == {"mesh", "graph_api", "llm_frameworks", "control_instances"}
    assert all(n > 0 for n in per_familie.values())


def test_l4_remotes_macht_keinen_netzwerk_probe(memories):
    assert memories["schichten"]["L4_remotes"]["probe_durchgefuehrt"] is False


# --------------------------------------------------------------------------
# Direktive 2 — Verarbeiten immer top-down
# --------------------------------------------------------------------------


def test_verarbeitungsreihenfolge_ist_top_down(layering):
    assert layering["richtung"] == "top_down"
    assert layering["reihenfolge"] == list(LAYER_ORDER)


def test_axiom_1_teilmengenkette(layering):
    """L_n ist Teilmenge von L_{n+1} — Aenderung nur aus der Schicht darueber."""
    mengen = {name: set(layering["mengen"][name]) for name in LAYER_ORDER}
    for oben, unten in zip(LAYER_ORDER, LAYER_ORDER[1:]):
        assert mengen[unten] <= mengen[oben], f"{unten} ist keine Teilmenge von {oben}"
    assert layering["axiome"]["1_top_down_teilmengen"] is True


def test_axiom_2_distanz_strikt_monoton(layering):
    """d(L6)=0 und die Distanz zum MasterSeed waechst strikt nach unten."""
    dist = layering["distanz_zum_masterseed"]
    folge = [dist[name] for name in LAYER_ORDER]
    assert folge[0] == 0.0
    for a, b in zip(folge, folge[1:]):
        assert a < b, f"Distanzfolge nicht strikt monoton: {folge}"
    assert layering["axiome"]["2_kontraktion_strikt_monoton"] is True


def test_axiom_2_inkremente_kontrahieren(layering):
    """Die Inkremente schrumpfen — das ist die eigentliche Banach-Kontraktion."""
    dist = layering["distanz_zum_masterseed"]
    folge = [dist[name] for name in LAYER_ORDER]
    inkremente = [b - a for a, b in zip(folge, folge[1:])]
    for a, b in zip(inkremente, inkremente[1:]):
        assert b < a, f"Inkremente kontrahieren nicht: {inkremente}"


def test_axiom_3_l0_nur_ueber_operator_c(layering):
    l0 = set(layering["mengen"]["L0_fundament"])
    l3 = set(layering["mengen"]["L3_internalisierung"])
    assert l0 <= l3, "L0 enthaelt Eintraege, die L3 nie passiert haben"
    assert layering["axiome"]["3_integration_ueber_operator_c"] is True


def test_axiom_4_keine_widerspruechliche_doppelprojektion(layering):
    assert layering["invarianz_brueche"] == []
    assert layering["axiome"]["4_invarianz"] is True


def test_lambda_ist_geklemmt(layering):
    assert 0.15 <= layering["lambda_contract"] <= 0.95


# --------------------------------------------------------------------------
# Direktive 3 — Ausgabe immer Geister manifestiert
# --------------------------------------------------------------------------


def test_kein_geist_bleibt_latent(memories, layering, cfg):
    geister = manifest_ghosts(memories, layering, cfg, live=False)
    assert geister, "Bei dieser Datenlage muss es Befunde geben"
    assert all(g["manifest"] is True for g in geister), "Ein Geist blieb latent"


def test_geister_sind_nach_aktivierung_sortiert(memories, layering, cfg):
    geister = manifest_ghosts(memories, layering, cfg, live=False)
    aktivierungen = [g["activation"] for g in geister]
    assert aktivierungen == sorted(aktivierungen, reverse=True)


def test_jeder_ausfall_beim_abstieg_wird_zum_geist(memories, layering, cfg):
    """Wer zwischen zwei Schichten herausfaellt, taucht in der Ausgabe auf."""
    geister = manifest_ghosts(memories, layering, cfg, live=False)
    benannt = {g["label"] for g in geister}
    mengen = {name: set(layering["mengen"][name]) for name in LAYER_ORDER}
    for oben, unten in zip(LAYER_ORDER, LAYER_ORDER[1:]):
        for cid in mengen[oben] - mengen[unten]:
            schlicht = cid.replace("erwaehnt:", "")
            assert schlicht in benannt, f"{cid} faellt bei {unten} heraus, fehlt aber im Manifest"


def test_geist_ids_sind_deterministisch(memories, layering, cfg):
    a = manifest_ghosts(memories, layering, cfg, live=False)
    b = manifest_ghosts(memories, layering, cfg, live=False)
    assert [g["id"] for g in a] == [g["id"] for g in b]


def test_dry_run_gehaltene_konnektoren_werden_ausgewiesen(memories, layering, cfg):
    geister = manifest_ghosts(memories, layering, cfg, live=False)
    dry = {g["label"] for g in geister if g["klasse"] == "dry_run_gehalten"}
    assert dry == set(layering["mengen"]["L0_fundament"])


# --------------------------------------------------------------------------
# Policy — Dry-Run, keine Secrets
# --------------------------------------------------------------------------


def _alle_credential_envs(memories):
    envs = set()
    for rec in memories["schichten"]["L2_connectors"]["_records"]:
        envs.update(rec["credential_envs"])
    return envs


def test_ohne_token_und_ohne_live_erreicht_niemand_l0(memories, monkeypatch):
    monkeypatch.delenv("FUSION_KONNEKTOR_LIVE", raising=False)
    for name in _alle_credential_envs(memories):
        monkeypatch.delenv(name, raising=False)

    frisch = load_bottom_up()
    lay = process_top_down(frisch)
    assert lay["groessen"]["L1_verkoerperung"] == 0
    assert lay["groessen"]["L0_fundament"] == 0

    auto = automatisiere(lay)
    assert auto["live_enabled"] is False
    assert auto["modus"] == "DRY-RUN"
    assert auto["ausgefuehrt"] == 0


def test_kein_would_execute_ohne_live_flag(monkeypatch):
    monkeypatch.delenv("FUSION_KONNEKTOR_LIVE", raising=False)
    r = run_vollautomat(schreiben=False)
    assert r["automatisierung"]["modus"] == "DRY-RUN"
    for e in r["automatisierung"]["ergebnisse"]:
        assert e["would_execute"] is False


def test_report_enthaelt_keinen_token_wert(memories, monkeypatch):
    """Gegenprobe mit gesetztem Fake-Token: der Wert darf nirgends auftauchen."""
    geheim = "fh-os-testtoken-DARF-NICHT-IM-REPORT-STEHEN"
    envs = sorted(_alle_credential_envs(memories))
    assert envs, "Ohne Credential-Envs waere die Gegenprobe wertlos"
    monkeypatch.setenv(envs[0], geheim)
    monkeypatch.delenv("FUSION_KONNEKTOR_LIVE", raising=False)

    r = run_vollautomat(schreiben=False)
    blob = json.dumps(r, ensure_ascii=False)
    assert geheim not in blob
    # Der Env-*Name* soll sehr wohl auftauchen — sonst weiss niemand, was fehlt.
    assert envs[0] in blob


def test_report_traegt_keine_rohdaten(monkeypatch):
    monkeypatch.delenv("FUSION_KONNEKTOR_LIVE", raising=False)
    r = run_vollautomat(schreiben=False)

    def _privat(obj):
        if isinstance(obj, dict):
            return any(str(k).startswith("_") for k in obj) or any(
                _privat(v) for v in obj.values()
            )
        if isinstance(obj, list):
            return any(_privat(v) for v in obj)
        return False

    assert not _privat(r), "Rohdaten (_-Schluessel) sind im Report gelandet"


def test_lauf_ist_ok_trotz_offener_befunde(monkeypatch):
    """Befunde sind das Produkt des Laufs, nicht sein Scheitern."""
    monkeypatch.delenv("FUSION_KONNEKTOR_LIVE", raising=False)
    r = run_vollautomat(schreiben=False)
    assert r["ok"] is True
    assert r["befunde_offen"] is True
    assert r["counts"]["geister_latent"] == 0


# --------------------------------------------------------------------------
# Zwei Sichten — operativ vs. deklariert
# --------------------------------------------------------------------------


def test_operative_sicht_befragt_die_umgebung(memories, monkeypatch):
    envs = sorted(_alle_credential_envs(memories))
    monkeypatch.setenv(envs[0], "vorhanden")
    lay = process_top_down(load_bottom_up())
    assert lay["groessen"]["L2_bindung"] > 0
    assert lay["groessen"]["L1_verkoerperung"] >= 1


def test_deklarierte_sicht_ignoriert_die_umgebung(memories, monkeypatch):
    """Der eingecheckte Report darf nicht davon abhaengen, wer ihn erzeugt."""
    for name in _alle_credential_envs(memories):
        monkeypatch.setenv(name, "vorhanden")
    lay = process_top_down(load_bottom_up(deklariert=True))
    assert lay["groessen"]["L1_verkoerperung"] == 0
    assert lay["groessen"]["L0_fundament"] == 0


def test_deklarierte_sicht_traegt_keine_maschinenpfade(monkeypatch):
    monkeypatch.delenv("FUSION_KONNEKTOR_LIVE", raising=False)
    laden = load_bottom_up(deklariert=True)
    blob = json.dumps(laden, ensure_ascii=False)
    for muster in ("/home/", "/root/", "/Users/", "C:\\"):
        assert muster not in blob, f"Maschinenpfad {muster!r} in der deklarierten Sicht"
    assert laden["schichten"]["L0_state"]["entries"] == []
    # Die Schicht wird trotzdem zuerst besucht — Bottom-up bleibt unangetastet.
    assert laden["reihenfolge"] == list(LADEN_ORDER)


def test_status_meldet_direktiven():
    st = status()
    assert st["ok"] is True
    assert st["laden_reihenfolge"] == list(LADEN_ORDER)
    assert st["verarbeiten_reihenfolge"] == list(LAYER_ORDER)
    assert st["policy"] == "dry_run_default"
