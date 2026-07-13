# Tails OS als Ultimate Tarnkappe-Layer für Fusion Hero OS (v8.2)

**Was ist Tails?** (einfach erklärt)
Tails ist eine Linux-Version, die du von einem USB-Stick startest. Sie verlässt **keine Spuren** auf dem Computer (amnesisch = vergesslich). Alles, was du im Internet machst, läuft automatisch durch das Tor-Netzwerk (wie ein unsichtbarer Tunnel). Nach dem Herunterfahren ist nichts mehr da – außer du aktivierst bewusst einen verschlüsselten Speicherbereich auf dem Stick.

Das ist die stärkste "Tarnkappe", die es derzeit gibt: Der Computer weiß nicht, dass du da warst, und im Netz bist du schwer zurückzuverfolgen.

## Warum das perfekt zu deinem Setup passt

Aus den tarnkappe.info-Screenshots und der vorherigen Optimierung:
- Du willst weniger Spuren beim Provider und bei Tracking (AdGuard Home + Tailscale auf dem Haupt-PC).
- Für besonders sensible Dinge (Theorie-Tests, anonyme Recherche, Field-Experiments, sensible Gespräche) brauchst du noch eine stärkere Schicht.
- Tails gibt dir genau das: Vollständige Unsichtbarkeit auf dem Gerät + Tor-Zwang.

Du kannst dein normales System (mit AdGuard + Tailscale) für den Alltag nutzen und Tails nur für die Momente, in denen du wirklich unsichtbar sein musst.

## Praktische Einrichtung (Schritt-für-Schritt, ohne Fachchinesisch)

### 1. Tails herunterladen und USB-Stick erstellen

1. Gehe auf die offizielle Seite: https://tails.net/
2. Lade die neueste Version herunter (aktuell um die 6.9+).
3. **Wichtig**: Lade auch die Signatur-Datei und prüfe sie (Anleitung auf der Seite – das schützt vor manipulierten Downloads).
4. USB-Stick mit mindestens 8 GB erstellen:
   - Unter Windows: Balena Etcher (einfachste Variante)
   - Unter Linux: `dd` Befehl oder Etcher

Beispiel mit `dd` (Linux):
```bash
# Achtung: /dev/sdX durch deinen USB-Stick ersetzen (mit lsblk prüfen!)
sudo dd if=tails-amd64-6.x.img of=/dev/sdX bs=4M status=progress && sync
```

### 2. Tails starten

- Computer neu starten
- Im BIOS/UEFI Boot-Menü (meist F12, F10 oder Esc) den USB-Stick auswählen
- Tails startet automatisch im "Live"-Modus (keine Installation nötig)

### 3. Optional: Verschlüsselten Speicherbereich anlegen (Persistent Storage)

Falls du Dateien oder Einstellungen zwischen den Sessions behalten willst (z. B. Notizen zur Theorie):
- Beim ersten Start die Option "Persistent Storage" aktivieren
- Ein starkes Passwort vergeben
- Der Bereich ist verschlüsselt, aber der Stick selbst ist nicht versteckt (wenn jemand den Stick in die Hand bekommt, sieht er, dass Tails drauf ist)

### 4. Im Internet surfen

- Alles läuft automatisch durch Tor
- Nutze den mitgelieferten Tor Browser (hat schon uBlock Origin drin)
- Keine Spuren auf dem Computer, keine normalen Logs

## Wie du Tails mit deinem bisherigen Setup kombinierst

**Haupt-PC / Alltag:**
- AdGuard Home + Tailscale (wie im vorherigen Guide)
- Normale Arbeit, Musik-Server (Navidrome), Banking etc.

**Tails-USB für Tarnkappe-Momente:**
- Booten, wenn du besonders unsichtbar sein willst (z. B. sensible Recherche, anonyme Tests, Dinge, bei denen du keine Spuren hinterlassen möchtest)
- Nach dem Runterfahren: Alles weg
- Dateien bei Bedarf über OnionShare (im Tails enthalten) oder den Persistent Storage austauschen

## Vergleich mit ähnlichen Systemen (kurz)

- **Tails**: Beste Wahl, wenn du "benutzen und verschwinden" willst. Ideal für unterwegs oder fremde Computer.
- **Whonix**: Besser für täglichen anonymen Betrieb in virtuellen Maschinen auf deinem normalen PC. Mehr Komfort, aber Spuren auf dem Host.
- **Qubes OS**: Sehr sicher durch Trennung in verschiedene virtuelle Maschinen. Gute Kombi mit Whonix, aber aufwändiger.

Für deine Ziele (Privatsphäre + Theorie-Arbeit + minimale Spuren) ist **Tails als Ergänzung** die stärkste Tarnkappe.

## Einschränkungen (ehrlich)

- Langsamer als normales Internet (wegen Tor)
- Nicht für schwere Grafik- oder Gaming-Arbeit gedacht
- Persistent Storage ist praktisch, aber nicht perfekt unsichtbar, wenn der Stick beschlagnahmt wird
- Funktioniert nicht auf Handys (nur PC/Laptop)

## Nächste Schritte

1. Einen Tails-USB-Stick anlegen und einmal testen (kannst du parallel zu deinem normalen System machen).
2. Die vorherige Datei (Tarnkappe_Cloak_Practical_Guide) + diese hier zusammen als dein "Stealth-Setup" nutzen.
3. Bei sensiblen Aktionen: Haupt-PC mit AdGuard/Tailscale + Tails für die kritischen Teile.

Das erweitert die Tarnkappe-Optimierung um die bisher stärkste amnesische Schicht. Alles bleibt einfach und praxisnah.