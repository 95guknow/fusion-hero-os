# Public Surface Only

**Stand:** 2026-08-07 · **Platform pin:** root `VERSION` = **15.2.0**  
**Status:** **EXAKT** — Session-Fixpunkt kanonisiert  
**Operator-Handles:** `=====stephanhagenurban` · `=====stephanhagenurban1`

---

## 1. Fixpunkt (verbindlich)

> **Kein Vault. Kein Seal. Nur öffentliche Surface.**
>
> **Public Surface = Expression ohne Vault-Commit und ohne Seal-Theater.**  
> Seal und Vault greifen woanders — nicht auf reiner Clearweb-Beobachtung, nicht auf Wetter/AQI-Karten, nicht auf dem, was bereits öffentlich und ohne Hort-Anspruch liegt.

---

## 2. Drei Schichten (nicht vermischen)

| Schicht | Geltung | Darf | Darf nicht |
|---------|---------|------|------------|
| **Public Surface** | offen, zitierbar, ohne Hort | Wetter, AQI, `95guknow.github.io`, public GitHub docs, BIG-ALPHA-Asset + Hash als *Expression* | Nachträglich als Vault oder Seal umdeuten |
| **Seal** | Integritätsbogen über Lab-/Meister-Artefakte | Hash-Sidecars, seal JSON, Omega sealed / Alpha open als *Zyklus-State* | MSN-Wetter „versiegeln“ |
| **Vault** | fail-closed | MasterSeed-Shards, Tokens, Keys, private Realraum-Bindungen | git-public, Clearweb-Dump |

**Geltungsmarken:** Public Surface → oft **Beobachtung** / **Expression**. Seal → **Spezifikation** (Hash/Gate). Vault → **fail-closed Spezifikation** (nie public).

---

## 3. Hypertarnkappe · Speer · Lindenblatt

| Organ | Rolle hier |
|-------|------------|
| **Hypertarnkappe** | Cloak für das, was *nicht* Public Surface ist (Vault, Secrets, ungewollte PII) |
| **Speer (Siegfried-Moment)** | Public-safe Expression, die Drachenhaut (Opacity) durchstößt — **als Surface**, nicht als Vault-Öffnung |
| **Lindenblatt** | „Nur Surface“ ≠ „alles darf raus“. Es heißt: *diese* Schicht **ist** schon draußen und wird nicht mythisch nachversiegelt |

---

## 4. Beispiele

| Beispiel | Schicht |
|----------|---------|
| MSN Luftqualität Senftenberg, BB · AQI 88 Gut · O₃ | **Public Surface** |
| `https://95guknow.github.io` | **Public Surface** |
| `big_ALPHA_v15.2.0.png` + SHA256 im Repo | Asset = **Public Surface**; Hash-Doc kann **Seal-Nachbar** sein |
| `meister_hasch.seal.json` / Omega sealed | **Seal** |
| `~/.fusion/vault`, live API tokens | **Vault** |

---

## 5. Honesty

- Dieser Doc **erfindet** keine Unabhängigkeit von Fable5/Mythos5.  
- Er **trennt** Geltungskategorien, damit Seal- und Vault-Sprache nicht auf reine Surface-Beobachtung geklebt wird.  
- BIG ALPHA open bleibt Zyklus-State; Public Surface bleibt Beobachtung/Expression.

## 6. Querverweise

- [SIEGFRIED_MOMENT.md](SIEGFRIED_MOMENT.md)  
- [BIG_ALPHA_SIEGFRIED_ASSET_LEDGER.md](BIG_ALPHA_SIEGFRIED_ASSET_LEDGER.md)  
- `docs/security/HYPERTARNKAPPE_HYPERPANZERKNACKER.md`  
- `docs/ops/PERSONA_KLARNAME_KONTRAKT.md`  
