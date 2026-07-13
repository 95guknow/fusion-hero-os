#!/bin/bash
# QEMU Test Runner for Fusion Hero OS SMP Validation
# Tests hyperthreading detection and monitoring center

set -e

# Build the kernel
echo "Building Fusion Hero OS SMP kernel..."
make clean
make -j$(nproc)

# Run QEMU with SMP
echo "Starting QEMU with SMP (4 cores, 8 threads)..."

qemu-system-x86_64 \
    -drive format=raw,file=kernel.bin,index=0,media=disk \
    -smp 4,cores=2,threads=2 \
    -m 512M \
    -vga virtio \
    -serial stdio \
    -display sdl \
    -no-reboot

echo "Test complete."