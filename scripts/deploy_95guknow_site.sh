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

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/web/95guknow.github.io"
REPO="git@github.com:95guknow/95guknow.github.io.git"
BRANCH="site/refresh-v12.1.0"
DIRECT=0
[[ "${1:-}" == "--direct" ]] && DIRECT=1

[[ -d "$SRC_DIR" ]] || { echo "FEHLER: $SRC_DIR fehlt." >&2; exit 1; }
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

git commit --quiet -m "site: Design und Inhalt auf Fusion Hero OS v12.1.0

- Plattformversion durchgaengig v12.1.0
- geschuetztes Meister-Hasch-Motiv wird nicht mehr ausgeliefert;
  an seiner Stelle eine Integritaetskarte mit Seal-Hash
- toter Link auf docs/dissertation/assets/meister_hasch.png entfernt
- Orbitron self-hosted statt Google-Fonts-CDN, strikte CSP
- Hell-/Dunkel-Schema, 404-Seite, sitemap.xml, Manifest, OG-Bild"

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
