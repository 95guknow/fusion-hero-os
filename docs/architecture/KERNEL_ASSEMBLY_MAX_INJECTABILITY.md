# Kernel on Assembly · Maximum Injectability

**Stand:** 2026-07-26 · **Quantum:** Q10 (+ Q0 gates)  
**Platform:** Fusion Hero OS v13+  
**Geltung:** Host-Pfad **Satz** (Windows inject_host) · Freestanding ASM **Fragment**

> **Korrektur 2026-07-27:** Der freestanding-Pfad stand hier als *Modell*. Das
> war zu hoch gegriffen — er hat nie assembliert. `boot.s` ist unter keinem
> Assembler übersetzbar (u. a. doppeltes Label, Prüfsumme über
> Sektionsgrenzen), `drivers/isr.s` wurde mit dem falschen Assembler
> aufgerufen, und `inject_table.o` wurde gebaut, aber nie gelinkt.
> Jeder Defekt ist mit Werkzeugausgabe belegt in
> [`KERNEL_BUILD_BEFUND.md`](KERNEL_BUILD_BEFUND.md); ein Teil ist dort auch
> bereits repariert. Geltung steigt erst auf *Modell*, wenn der QEMU-Boot
> grün ist.

---

## 1. Direktive

| Anforderung | Umsetzung |
|-------------|-----------|
| **Kernel läuft auf Assembly** | Primärsprache Q10 = **Assembly** (NASM x86_64); C nur noch dünne Freunde |
| **Maximale Injectability** | 256 Slots · hot-swap · generation counter · capability bits · Quantum-ID pro Slot |

**Nicht** gemeint: fremde Prozesse missbrauchen.  
**Gemeint:** jedes Quantum kann **kooperativ** in den Kernel-Hook-Raum **eingehängt** werden — maximal, aber **capability-gated**.

---

## 2. Architektur

```text
┌─────────────────────────────────────────────┐
│  inject_table (Assembly .data/.bss)         │
│  256 × slot { flags, caps, qid, gen, fn }   │
└──────────────────┬──────────────────────────┘
                   │ fhos_inject_call / swap
     ┌─────────────┼─────────────┐
     ▼             ▼             ▼
  Q2 compute    Q4 intel      Q1 control …
  (Rust)        (Python)      (Python)
```

| Layer | Sprache | Rolle |
|-------|---------|--------|
| Slot table + dispatch | **ASM** | Wahrheit der Hooks |
| Freestanding glue | C (minimal) | console, smp helpers |
| Host control plane | **Python** `inject_host.py` | Windows: gleiche ABI-Semantik |
| Integrity | Q0 caps `CAP_PRIV` | Swap/clear nur mit Priv |

---

## 3. API (Assembly + Host)

```c
fhos_inject_init();
fhos_inject_register(slot, name, quantum_id, caps, flags, fn);
fhos_inject_swap(slot, fn, holder_caps);   /* HOT only */
fhos_inject_call(slot, a0,a1,a2,a3, holder_caps);
fhos_inject_clear(slot, holder_caps);
```

Python:

```python
from kernel.inject import get_inject_host, CAP_HOOK, CAP_QUANTUM
h = get_inject_host()
h.register(2, "Q2_anneal", quantum_id=2, caps=CAP_HOOK|CAP_QUANTUM, fn=my_hook, hot=True)
h.call(2, batch_id, 0, 0, 0)
```

Defaults: Slots 0–12 = Q0–Q12 no-op hooks (sofort injizierbar).

---

## 4. Capability-Modell (max inject ≠ unauthenticated inject)

| Cap | Bit | Nutzung |
|-----|-----|---------|
| READ | 0 | call read-only hooks |
| HOOK | 1 | register/call hooks |
| SWAP | 2 | hot-replace entry |
| ISR | 3 | interrupt-class slots |
| QUANTUM | 4 | quantum-owned handlers |
| PRIV | 7 | Q0/Q12 sensitive |

Holder ohne Bits → call/swap returns 0 / -2.

---

## 5. Dateien

| Pfad | Inhalt |
|------|--------|
| `kernel/inject/inject_table.s` | NASM slot table + register/swap/call |
| `kernel/inject/include/inject.h` | C ABI |
| `kernel/inject/inject_host.py` | Host max-inject (operativ) |
| `kernel/boot.s` | bestehender Multiboot-Einstieg |
| `kernel/drivers/isr.s` | ISR stubs |

---

## 6. Integration

- Preload: `preload_kernel_inject()` in universal_startup_preload  
- Persist: `~/.fusion/kernel/inject_table.json`  
- Quantum map: `Q10_ipc_bridge.language.primary = assembly`  

---

## 7. Ehrlichkeit

- Freestanding `kernel.c` + `boot.s` sind **Experiment / Modell** (kein produktionsreifer Hypervisor).  
- Auf dem Mainframe (Windows) ist **inject_host** der **operative** Kernel-Injektionsraum.  
- Max injectability = **maximale kooperative Erweiterbarkeit**, nicht Exploit-Primitive gegen Drittsysteme.

**Satz:** Hook-Tabelle + Caps + Host-Runtime.  
**Modell:** reiner Assembly-Kernel unter QEMU bis Build/Boot grün.
