# Kernel-Build — Befund

**Stand:** 2026-07-27
**Gegenstand:** `kernel/` — „Kernel on Assembly · Maximum Injectability"
**Geltung:** Befund = **Satz** (jede Zeile hier ist mit Assembler-/Compiler-Ausgabe belegt)

---

## Kurzfassung

Der Assembly-Kern **hat nie gebaut**. Nicht „läuft nicht", sondern: er ist nie
durch Assembler und Compiler gekommen. `docs/architecture/KERNEL_ASSEMBLY_MAX_INJECTABILITY.md`
führte den freestanding-Pfad als **Modell** — tatsächlich war er **Fragment**.

Dieser Befund korrigiert die Geltungsmarke und listet jeden Defekt einzeln.

## Was jetzt baut (nach diesem Commit)

| Objekt | vorher | nachher |
|---|---|---|
| `obj/isr.o` | unmöglich — GAS-Datei mit `nasm` assembliert | **OK** |
| `obj/inject_table.o` | baute, wurde aber **nie gelinkt** | **OK + gelinkt** |
| `obj/smp.o` | scheiterte an `<stdint.h>` unter `-nostdinc` | **OK** |
| `obj/ide.o` | **keine Make-Regel vorhanden** | **OK** |
| `obj/gui.o` | **keine Make-Regel vorhanden** | Regel da, C-Fehler offen |

`make` erreichte vorher nicht einmal die Assembly — es starb an einem falschen
Include-Pfad im ersten C-Ziel. Jetzt läuft es bis zum ersten echten C-Defekt.

## Offene Defekte

### A · `boot.s` — assembliert unter keinem Assembler

Die Datei ist in GNU-as-Syntax geschrieben (`.section`, `.long`, `.quad`),
das Makefile rief `nasm` auf. Aber auch als GAS ist sie defekt:

| Zeile | Defekt | Belegt durch |
|---|---|---|
| 7 | Multiboot-Prüfsumme rechnet über Sektionsgrenzen | `Error: invalid operands (*UND* and .multiboot_header sections) for '-'` |
| 26 | `movq %rdi, multiboot_info_ptr` | `Error: operand type mismatch for 'movq'` |
| 31 | `orq $0x200, %rax` nach `movq %cr4` | `Error: operand type mismatch for 'or'` |
| 36 | `retf` im 64-Bit-Modus (dort `lretq`) | `Warning: no instruction mnemonic suffix given` |
| 65 / 71 | Label `no_ht` **doppelt definiert** | `Error: symbol 'no_ht' is already defined` |

Zusätzlich semantisch fragwürdig, aber nicht assembler-belegbar:

- `enable_paging` schreibt `movq %rax, pml4_table(%rax)` — `rax` ist zugleich
  einzutragender Wert *und* Index. Die Seitentabellen werden damit nicht
  aufgebaut, sondern an einer aus dem Wert errechneten Adresse überschrieben.
- `init_bsp_apic` / `wake_up_aps` schreiben auf absolute Adressen `0xf0`,
  `0x300` statt auf die APIC-MMIO-Basis.
- `init_gdt` ist ein leeres `ret`, `lgdt gdt_descriptor` läuft also auf eine
  nicht initialisierte Tabelle.

**Nicht in diesem Commit repariert.** Eine Korrektur ist ein Neuschreiben des
Long-Mode-Einstiegs und muss gebootet werden, um mehr als Behauptung zu sein.
QEMU ist in dieser Umgebung nicht installierbar (Paketquelle liefert 404 für
`qemu-system-x86`). Ungetesteten Boot-Code als „behoben" auszuliefern wäre
genau die Sorte plausibler, unbelegter Artefakt, gegen die die Geltungsmarken
dieses Repos existieren.

Solange das offen ist, bleibt `boot.o` bewusst **aus der Link-Liste**.

### B · C-Quellen — 44 Fehler in 6 von 8 Dateien

Gemessen mit den Flags des Makefiles (`-ffreestanding -nostdinc -I. -Iinclude`):

| Datei | Fehler |
|---|---:|
| `gui/gui_core.c` | 37 |
| `management/monitor.c` | 3 |
| `kernel.c` | 1 |
| `management/database.c` | 1 |
| `ai/request_optimizer.c` | 1 |
| `ai/hybrid_cognition.c` | 1 |
| `smp/smp.c` | 0 |
| `ide/ide_shell.c` | 0 |

Der Fehler in `kernel.c` ist kein vergessenes `extern`: `cpus` ist in
`smp/smp.c` als `static cpu_info_t cpus[256]` deklariert, also absichtlich
dateilokal. `kernel.c` greift auf fremden Übersetzungseinheits-Zustand zu.
Das sauber zu lösen heißt, eine Zugriffsfunktion in `smp.h` zu ergänzen oder
`cpus` bewusst zu exportieren — eine Designentscheidung, keine Zeilenkorrektur.

Ebenfalls offen: `console_init`, `console_print`, `smp_start_scheduler` werden
in `kernel.c` ohne Deklaration aufgerufen.

## Was in diesem Commit repariert wurde

1. **`kernel.c`** — `../include/stdint.h` und `../smp/smp.h` zeigten vom
   Repo-Root aus ins Leere. Korrekt ist `include/…` bzw. `smp/…`.
   (`smp/smp.c` nutzt `../include/` **richtig** — es liegt eine Ebene tiefer.)
2. **`CFLAGS`** — `-Iinclude` ergänzt. Mehrere Header ziehen `<stdint.h>` in
   spitzen Klammern; unter `-nostdinc` war der freestanding-Header unauffindbar.
3. **`isr.o`-Regel** — `nasm` → `as --64`. Die Datei war immer GAS.
4. **`gui.o` / `ide.o`** — Regeln ergänzt. Beide standen als Link-Voraussetzung
   ohne Bauregel; `make` konnte den Link-Schritt deshalb nie erreichen.
5. **`inject_table.o`** — in die Link-Liste aufgenommen. Die Slot-Tabelle, um
   die es in der Architektur-Doku geht, wurde gebaut und dann weggeworfen.

## Sprachaufteilung — was das Repo bereits festlegt

`KERNEL_ASSEMBLY_MAX_INJECTABILITY.md` weist die Ebenen schon zu:

| Ebene | Sprache | Rolle |
|---|---|---|
| Slot-Tabelle + Dispatch | **ASM** | Wahrheit der Hooks |
| Freestanding glue | C (minimal) | console, smp |
| Host control plane | **Python** | gleiche ABI-Semantik |

Das ist bereits die Antwort auf „Kern maschinennah, aufbauende Elemente in der
zugänglichsten Sprache". Sie steht nur noch nicht auf eigenen Füßen, weil die
unterste Ebene nicht baut.

## Nächster Schritt

Der ehrliche Weg zu **Satz** führt über QEMU:

1. `boot.s` neu schreiben — ein Dialekt, ein sauberer Long-Mode-Einstieg.
2. `make iso && qemu-system-x86_64 -cdrom os.iso` grün bekommen.
3. Erst dann Geltung von Fragment auf Modell, nach reproduzierbarem Boot auf Satz.

Ohne Schritt 2 bleibt jede Aussage über den freestanding-Pfad eine Behauptung.
