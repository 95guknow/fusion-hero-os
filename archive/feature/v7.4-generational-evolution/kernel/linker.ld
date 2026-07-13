/* Linker Script für 64-bit Kernel */
OUTPUT_FORMAT(elf64-x86-64)
ENTRY(_start)

SECTIONS {
    /* Load kernel at 1MB */
    . = 0x100000;

    .multiboot_header : {
        *(.multiboot_header)
    }

    .text : {
        *(.text)
        *(.text64)
    }

    .rodata : {
        *(.rodata)
    }

    .data : {
        *(.data)
    }

    .bss : {
        __bss_start = .;
        *(.bss)
        __bss_end = .;
    }

    /DISCARD/ : {
        *(.eh_frame)
    }
}
