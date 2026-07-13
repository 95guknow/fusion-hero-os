# Fusion Hero OS - SMP Kernel

Ein minimal x86-64 OS-Kernel mit Hyperthreading-Unterstützung.

## Features

- **SMP (Symmetric Multi-Processing)**: Unterstützung für mehrere CPU-Kerne
- **Hyperthreading**: Erkennung und Nutzung von Intel SMT (Simultaneous Multithreading)
- **Multiboot 2**: Kompatibel mit GRUB und QEMU
- **LAPIC Timer**: Pro-CPU Timer-Interrupts für präemptive Multitasking
- **IPI-Handler**: Inter-Processor Interrupts für Core-Kommunikation

## Build

```bash
make all    # Kernel kompilieren
make iso    # ISO für QEMU erstellen
make run    # In QEMU mit SMP starten
```

## Verzeichnisstruktur

- `boot.s` - Bootloader mit SMP-Initialisierung
- `kernel.c` - Hauptkernel-Einstiegspunkt
- `smp/smp.c` - SMP-Implementierung
- `smp/smp.h` - SMP-Header
- `drivers/isr.s` - Interrupt Service Routinen
- `include/stdint.h` - Standard integer types
- `linker.ld` - Linker Script
- `Makefile` - Build configuration

## Hyperthreading-Architektur

Der Kernel erkennt:
1. CPUID.1:EDX[28] (HTT-Bit) für Hyperthreading-Unterstützung
2. CPUID.80000008 für logische Prozessoren pro Kern
3. Unterscheidet zwischen physischen Kernen und logischen Threads
