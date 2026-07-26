# 95guknow.github.io

Öffentliche Landing Page für **Senfkorn UG · 95guknow · WIR Mesh**.

Statisch, ohne Build-Schritt, ohne Framework. Was im Repo liegt, ist exakt
das, was ausgeliefert wird.

## Stand

- Plattform-Bezug: Fusion Hero OS **v13.0.0** (Orientierung; diese Site führt keinen Mainframe aus)
- Zyklus: BIG OMEGA sealed · BIG ALPHA open
- **UI-Stub:** public-safe · **ohne echte Funktionalität** · Designhandbuch V3.3

## Aufbau

```
index.html              Startseite
ui-stub/                Public-safe UI-Stub (Labor-Frame, dual canvas, disabled HUD)
  index.html
  css/stub.css
  js/stub.js            Canvas-Illustration only — kein fetch
404.html                Fehlerseite (nutzt dasselbe Stylesheet)
css/style.css           Cascade Layers: reset → tokens → base → layout
                        → components → motion → utilities
js/theme-init.js        synchron im <head>, verhindert Theme-Flash
js/app.js               Modul: Theme-Umschalter, Jahreszahl
assets/og.png           Social-Preview 1200×630
assets/favicon.svg      Markenzeichen
assets/avatar.jpg       Profilbild
assets/fonts/           Orbitron (variabel, Latin-Subset) + OFL-Lizenz
manifest.webmanifest    Installierbarkeit
robots.txt sitemap.xml  Indexierung
.nojekyll               GitHub Pages liefert die Dateien unverändert aus
```

## UI-Stub (Kurz)

| Eigenschaft | Wert |
|-------------|------|
| URL | https://95guknow.github.io/ui-stub/ |
| Funktion | **keine** (alle Controls `disabled`) |
| Netzwerk | `connect-src 'none'` — kein GraphAPI, kein Dashboard |
| Doku (V3.3 Langform) | `docs/kompendium/PUBLIC_UI_STUB_95GUKNOW.md` im Plattform-Repo |

Lokal: `python -m http.server 8080` im Ordner `web/95guknow.github.io`, dann `/ui-stub/`.

## Grundsätze

**Keine Drittanbieter-Requests.** Die Seite lädt nichts von fremden Hosts —
keine Font-CDN, keine Analytics, keine Cookies. Das ist kein Selbstzweck: ein
Einbinden der Google-Fonts-CDN überträgt die IP-Adresse jedes Besuchers an
einen Dritten, was für eine deutsche UG datenschutzrechtlich angreifbar ist.
Orbitron liegt deshalb lokal (SIL OFL 1.1, Lizenz in `assets/fonts/OFL.txt`).

**Content-Security-Policy** per `<meta>`: alles `'self'`, `connect-src 'none'`.
`frame-ancestors` fehlt bewusst — die Direktive wird in `<meta>` ignoriert und
GitHub Pages kann keine HTTP-Header setzen.

**Kein geschütztes Bildmaterial.** Die Seite liefert das Meister-Hasch-Motiv
nicht aus. Verbindlich ist der Seal (SHA-256), verlinkt auf den öffentlichen
Frame im Plattform-Repo.

**Zugänglichkeit.** Semantische Landmarks, Skip-Link, sichtbarer Fokus,
`prefers-reduced-motion`, Hell- und Dunkel-Schema. Ohne JavaScript bleibt die
Seite vollständig lesbar und navigierbar; JS liefert nur den Theme-Umschalter
und die Jahreszahl.

## Lokal ansehen

```bash
python3 -m http.server 8080
# http://localhost:8080
```

Ein einfaches `file://`-Öffnen funktioniert nicht vollständig — das
ES-Modul in `js/app.js` und die CSP verlangen einen HTTP-Origin.

## Policy

Public-safe only · kein Vault · Labor Frame · Offensive wird nicht als
Realraum dargestellt.
