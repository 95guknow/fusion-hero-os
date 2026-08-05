#!/usr/bin/env bash
#
# Überträgt den in web/95guknow.github.io/ vorbereiteten Seitenstand nach
# 95guknow/95guknow.github.io.
#
# Warum dieses Skript existiert: Sessions, die auf Senfkorn-UG/fusion-hero-os
# beschränkt sind, können nicht nach 95guknow/* schreiben. Der Seitenstand wird
# deshalb hier gepflegt und von einer Umgebung mit Push-Recht übertragen.
#
# Aufruf:
#   scripts/deploy_95guknow_site.sh            # Branch anlegen, PR selbst öffnen
#   scripts/deploy_95guknow_site.sh --direct   # direkt nach main (geht sofort live)
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$REPO_ROOT/web/95guknow.github.io"
REPO="git@github.com:95guknow/95guknow.github.io.git"

# Branch- und Commit-Text folgen der Plattform-Version, statt sie zu wiederholen.
# Vorher standen hier feste Strings: der Branch nannte v13.0.0, die Commit-
# Message v12.1.0, und beide blieben bei jedem Bump stehen.
PLATFORM_VERSION="$(tr -d '[:space:]' < "$REPO_ROOT/VERSION")"
BRANCH="site/refresh-v${PLATFORM_VERSION}"
DIRECT=0
[[ "${1:-}" == "--direct" ]] && DIRECT=1

[[ -d "$SRC_DIR" ]] || { echo "FEHLER: $SRC_DIR fehlt." >&2; exit 1; }
[[ -n "$PLATFORM_VERSION" ]] || { echo "FEHLER: $REPO_ROOT/VERSION ist leer." >&2; exit 1; }
command -v rsync >/dev/null || { echo "FEHLER: rsync wird benötigt." >&2; exit 1; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "→ klone 95guknow/95guknow.github.io"
git clone --quiet "$REPO" "$WORK/site"

echo "→ übertrage Seitenstand"
# --delete entfernt alles, was nicht mehr zum Stand gehört. Das ist gewollt:
# unter anderem fliegt damit assets/meister_hasch.png raus, das dort aus
# Urheberrechtsgründen nicht mehr liegen soll.
rsync -a --delete --exclude='.git/' "$SRC_DIR/" "$WORK/site/"

cd "$WORK/site"
if git diff --quiet && git diff --cached --quiet && [[ -z "$(git status --porcelain)" ]]; then
  echo "→ keine Änderungen — die Seite ist bereits auf diesem Stand."
  exit 0
fi

echo "→ geänderte Dateien:"
git add -A
git --no-pager diff --cached --stat | sed 's/^/     /'

git commit --quiet -m "site: Stand aus web/95guknow.github.io/ auf Fusion Hero OS v${PLATFORM_VERSION}

Uebertragen per rsync --delete aus dem Plattform-Repo; der Quellstand dort
ist massgeblich. Geschuetztes Meister-Hasch-Motiv wird nicht ausgeliefert,
an seiner Stelle steht eine Integritaetskarte mit Seal-Hash."

if [[ "$DIRECT" == "1" ]]; then
  echo "→ pushe nach main (die Seite geht damit live)"
  git push origin HEAD:main
  echo "fertig: https://95guknow.github.io/"
else
  echo "→ pushe nach $BRANCH"
  git push -u origin "HEAD:$BRANCH"
  echo
  echo "fertig. PR öffnen:"
  echo "  https://github.com/95guknow/95guknow.github.io/compare/$BRANCH?expand=1"
  echo "Erst nach dem Merge ist die Seite live."
fi
