# BRANCH_STRATEGY_v8.md (refined)

**ALTE_Frau_95g Heroic Core v8 – Fusion Hero OS Branch Model (refined)**

## Ziel
Klare, sichere und zukunftssichere Branch-Struktur für ein selbst-modifizierendes heroic Core-Repository.

## Branch-Modell (gültig ab v8)

### main (protected, stable)
- Einziger stabiler Release-Branch
- Nur vollständig peer-reviewed + archivierte v8-Code + Docs
- **Force-Push streng verboten**
- Alle Änderungen nur über Merge aus develop nach erfolgreicher 5/6-Dimensions-PeerReview + AutomaticArchiving
- Tags: v8.0, v8.1, v8.2... (heroic semver)

### develop (active integration)
- Täglicher Arbeits-Branch
- Feature-Branches werden hier integriert
- Regelmäßige Merges nach main (nach vollständigem Review)

### feature/<kurzname>
**Namenskonvention (verbindlich):**
- feature/v8-<thema>
- feature/hyperthreading-<thema>
- feature/horkrux-<thema>
- feature/optimizer-<thema>
- feature/structure-<thema>

Beispiele:
- feature/v8-branch-structure-implementation
- feature/hyperthreading-metrics
- feature/horkrux-full-propagation

Kurzlebig → nach Merge in develop löschen

### hotfix/<name>
- Nur für kritische Fixes direkt auf main
- Sofortiger Rückfluss in develop

### archive/ oder Tags
- Historie über Tags + archive/-Ordner

## Regeln (im Core verankert)
- Branch-Namen immer heroic-konform und präzise
- Vor jedem Merge in main oder develop: 5-stufiger Prozess + PeerReview + LiveProcessTracking
- AutomaticArchiving bei jedem Merge in main
- main ist geschützt (Branch Protection empfohlen: require reviews, status checks, no force-push)

**Status:** v8 refined | A+B+D ausgeführt
