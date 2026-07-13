# Branching Strategy — Fusion Hero OS → AscensionOS (Final v8.8+)

> **Stand:** v8.3.0 · 2026-07-13

## Versionierung (kanonisch ab v8.3.0)

**Quelle der Wahrheit ist der annotierte Git-Tag `vMAJOR.MINOR.PATCH` auf
`main` dieses Repos** (`95guknow/fusion-hero-os`), gespiegelt in der Datei
`VERSION` im Root. Jeder Tag bekommt ein GitHub-Release. Alles andere ist
abgeleitet — kein Dokument, Branch oder Manifest führt eine eigene Zählung.

- **MAJOR** = Ära. 8 = operativer FuHOS-Kanon. 9 wird erst vergeben, wenn der
  Ascension-Track tatsächlich Kanon wird — bis dahin ist „v9.x" reines
  Roadmap-Label und nie ein Release.
- **MINOR** = Feature-/Konsolidierungsstand (neue Layer, Mesh-Ausbau, …).
- **PATCH** = Fixes.
- Vorab-Stände aus `develop`/`ascension`: `v8.4.0-rc.1` usw.

**Mechanik:**

- `VERSION` (Root) trägt die Plattform-Version ohne `v`-Prefix.
- `scripts/bump_version.py` setzt sie und gleicht alle Manifeste an
  (`package.json` Root + workstation, `pyproject.toml`, beide Crate-
  `Cargo.toml`). CI-Gate: `bump_version.py --check` (fail bei Drift).
- Release: `python scripts/bump_version.py X.Y.Z` → Commit → Merge nach
  `main` → `git tag -a vX.Y.Z` → `gh release create vX.Y.Z --generate-notes`.
- Commits folgen Conventional Commits (`feat:`, `fix:`, `docs:`, …), damit
  MINOR/PATCH ableitbar sind und Release-Notes automatisch entstehen.
- **Keine Versionsnummern mehr in Branch- oder Dateinamen.** Neue Doku trägt
  den Stand nur im Header (`> Stand: vX.Y.Z`). Bestehende `archive/v*`-
  Branches und `_v7.x_`-Dateien bleiben unangetastete Historie.

**Ökosystem:** Vorgänger-Repos (`fusion-hero-os-v1`, `Fusion_Hero_OS_v1.1`,
`fusion-hero-core`, `alte-frau-95g-heroic-core`, `AscensionOS`, `FuHOS_pub`)
sind auf GitHub archiviert. Aktive Satelliten-Repos (`normalOS`,
`fusion-hero-vault`, `mister-jailbait-gui`, `dashboard`,
`fusion-hero-os-daily-plans`) versionieren unabhängig nach demselben Schema
und deklarieren ihre Plattform-Kompatibilität in `fuhos_compat.yaml`
(z. B. `fuhos_compat: ">=8.3 <9"`).

## Aktuelles Modell (Hyperthreading + Archive)

### `main` (Stable Release Line)
- Geschützt. Direkte Pushes sind blockiert.
- Nur Merges via Pull Request von `develop` oder `ascension`.

### `develop` – Option A Track (Evolutionary)
- Aktive Weiterentwicklung des bestehenden Heroic Core.

### `ascension` – Option B Track (Strong Ascension Path)
- Radikalere Entwicklungslinie für AscensionOS.
- `ascension_os/` und `AscensionCore` sind jetzt auch auf `main` verfügbar.

### `archive`
- Sinnvoll organisiertes Archiv für alles Alte.

**Ziel:** Alles seit April 2026 entwickelte soll in AscensionOS münden.
