#!/data/data/com.termux/files/usr/bin/bash
# Voice-Journal-Loop fuer Termux (Android).
#
# Voraussetzungen auf dem Handy:
#   1. Termux + Termux:API installieren (beide aus F-Droid, NICHT Play Store)
#   2. pkg install termux-api curl
#   3. Mikrofon-Berechtigung fuer Termux:API erteilen
#
# Konfiguration: SERVER und TOKEN unten anpassen (oder als Env setzen).
#
# EHRLICHE EINSCHRAENKUNG: termux-speech-to-text startet pro Aufruf eine
# STT-Session des Android-Systems (endet nach einer Sprechpause). Diese
# Schleife ist also "quasi-kontinuierlich" — zwischen den Sessions gibt es
# kurze Luecken, und Android kann den Prozess im Hintergrund drosseln
# (Akku-Optimierung fuer Termux deaktivieren, termux-wake-lock hilft).
# Echtes Always-On braeuchte eine eigene App mit Foreground-Service.

SERVER="${JOURNAL_SERVER:-http://192.168.0.10:8787}"
TOKEN="${JOURNAL_TOKEN:?JOURNAL_TOKEN muss gesetzt sein}"
QUEUE="$HOME/.journal_queue.jsonl"

termux-wake-lock

send_note() {
    local text="$1" ts="$2"
    curl -sf -X POST "$SERVER/journal/note" \
        -H "Content-Type: application/json" \
        -H "X-Journal-Token: $TOKEN" \
        -d "{\"text\": $(printf '%s' "$text" | jq -Rs .), \"ts\": \"$ts\", \"source\": \"termux\"}" \
        > /dev/null
}

flush_queue() {
    [ -s "$QUEUE" ] || return 0
    local tmp="$QUEUE.tmp" line ok=1
    : > "$tmp"
    while IFS= read -r line; do
        local t ts
        t=$(printf '%s' "$line" | jq -r .text)
        ts=$(printf '%s' "$line" | jq -r .ts)
        if [ "$ok" = 1 ] && send_note "$t" "$ts"; then :; else
            ok=0
            printf '%s\n' "$line" >> "$tmp"
        fi
    done < "$QUEUE"
    mv "$tmp" "$QUEUE"
}

echo "Voice-Journal-Loop laeuft. Server: $SERVER  (Strg+C zum Beenden)"
while true; do
    TEXT=$(termux-speech-to-text 2>/dev/null)
    if [ -n "$TEXT" ]; then
        TS=$(date +%Y-%m-%dT%H:%M:%S)
        echo "[$TS] $TEXT"
        if ! send_note "$TEXT" "$TS"; then
            # Offline? Lokal puffern, beim naechsten Erfolg nachliefern.
            printf '{"text": %s, "ts": "%s"}\n' "$(printf '%s' "$TEXT" | jq -Rs .)" "$TS" >> "$QUEUE"
            echo "  -> Server nicht erreichbar, lokal gepuffert."
        else
            flush_queue
        fi
    fi
    sleep 1
done
