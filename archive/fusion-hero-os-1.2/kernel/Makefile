# Makefile für Fusion Hero OS Kernel
# Unterstützung für SMP und Hyperthreading

# Compiler und Linker
CC = gcc
CFLAGS = -ffreestanding -mno-red-zone -mno-mmx -mno-sse -mno-sse2 -nostdlib -nostartfiles -nostdinc
LDFLAGS = -T linker.ld -nostdlib -nostartfiles -static

# Verzeichnisse
ASM_SRC = boot.s drivers/isr.s
C_SRC = kernel.c smp/smp.c management/monitor.c management/database.c \
        ai/request_optimizer.c ai/hybrid_cognition.c \
        gui/gui_core.c ide/ide_shell.c
AI_SRC = ai/request_optimizer.c ai/hybrid_cognition.c
MONITOR_SRC = management/monitor.c management/database.c
OBJ_DIR = obj
BIN_DIR = bin

# Ziele
.PHONY: all clean iso

all: $(BIN_DIR)/kernel.bin

$(OBJ_DIR):
	mkdir -p $(OBJ_DIR)

$(BIN_DIR):
	mkdir -p $(BIN_DIR)

# Assemble bootloader
$(OBJ_DIR)/boot.o: boot.s | $(OBJ_DIR)
	nasm -f bin -o $(OBJ_DIR)/boot.bin $<
	ld -Ttext 0x100000 -o $(OBJ_DIR)/boot.o $(OBJ_DIR)/boot.bin

# Compile C files
$(OBJ_DIR)/kernel.o: kernel.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I. -c -o $@ $<

$(OBJ_DIR)/smp.o: smp/smp.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I. -c -o $@ $<

$(OBJ_DIR)/isr.o: drivers/isr.s | $(OBJ_DIR)
	nasm -f elf64 -o $@ $<

$(OBJ_DIR)/monitor.o: management/monitor.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I. -c -o $@ $<

$(OBJ_DIR)/database.o: management/database.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I. -c -o $@ $<

$(OBJ_DIR)/req_opt.o: ai/request_optimizer.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I. -c -o $@ $<

$(OBJ_DIR)/hybrid.o: ai/hybrid_cognition.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I. -c -o $@ $<

$(OBJ_DIR)/llm_merge.o: ai/llm_merge.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I. -c -o $@ $<

$(OBJ_DIR)/persistent_db.o: management/persistent_db.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -I. -c -o $@ $<

# Link kernel
$(BIN_DIR)/kernel.bin: $(OBJ_DIR)/kernel.o $(OBJ_DIR)/smp.o $(OBJ_DIR)/isr.o \
    $(OBJ_DIR)/monitor.o $(OBJ_DIR)/database.o $(OBJ_DIR)/req_opt.o \
    $(OBJ_DIR)/hybrid.o $(OBJ_DIR)/llm_merge.o $(OBJ_DIR)/persistent_db.o \
    $(OBJ_DIR)/gui.o $(OBJ_DIR)/ide.o | $(BIN_DIR)
	ld $(LDFLAGS) -o $@ $^

# Create ISO for QEMU
iso: $(BIN_DIR)/kernel.bin
	mkdir -p iso/boot/grub
	cp $(BIN_DIR)/kernel.bin iso/boot/kernel.bin
	echo 'set timeout=0' > iso/boot/grub/grub.cfg
	echo 'set default=0' >> iso/boot/grub/grub.cfg
	echo 'menuentry "Fusion Hero OS" {' >> iso/boot/grub/grub.cfg
	echo '  multiboot2 /boot/kernel.bin' >> iso/boot/grub/grub.cfg
	echo '  boot' >> iso/boot/grub/grub.cfg
	echo '}' >> iso/boot/grub/grub.cfg
	grub-mkrescue -o os.iso iso

clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR) iso os.iso

run: iso
	qemu-system-x86_64 -cdrom os.iso -smp 2 -cpu host
