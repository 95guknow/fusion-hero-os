.section .multiboot_header
.align 8
.multiboot_header:
    .long 0xe85250d6
    .long 0
    .long multiboot_end - multiboot_start
    .long 0x100000000 - (0xe85250d6 + 0 + (multiboot_end - multiboot_start))
    .word 0
    .word 0
    .long 8

multiboot_start:

.section .text
.global _start
.extern kernel_main

_start:
    cli
    movq $0x80000, %rsp
    movq %rdi, multiboot_info_ptr
    call init_smp
    call enable_paging
    call init_gdt
    lgdt gdt_descriptor
    movq $pml4_table, %cr3
    movq %cr4, %rax
    orq $0x200, %rax
    movq %rax, %cr4
    movq %cr0, %rax
    orq $0x80000000, %rax
    movq %rax, %cr0
    movabs $_start64, %rax
    pushq $0x08
    pushq %rax
    retf

.section .text64
.extern kernel_main

_start64:
    movq $bss_start, %rdi
    movq $bss_end, %rcx
    subq %rdi, %rcx
    shrq $3, %rcx
    xorq %rax, %rax
    rep stosq
    movq multiboot_info_ptr, %rdi
    call kernel_main
hang:
    hlt
    jmp hang

init_smp:
    pushq %rbp
    movq %rsp, %rbp
    movq $1, %rax
    cpuid
    testl $(1 << 28), %edx
    jz no_ht
    movq $0x80000008, %rax
    cpuid
    movb %al, logical_per_core
    andb $0xff, %al
no_ht:
    call init_bsp_apic
    call wake_up_aps
    popq %rbp
    ret

no_ht:
    popq %rbp
    ret

init_bsp_apic:
    pushq %rbp
    movq %rsp, %rbp
    movq $0x1b, %rcx
    rdmsr
    orq $0x800, %rax
    wrmsr
    movl $0x0, 0xf0
    movl $0x0, 0xf4
    popq %rbp
    ret

wake_up_aps:
    pushq %rbp
    movq %rsp, %rbp
    movl $0xC4500, 0x300
    call delay
    movl $0xC4600, 0x300
    call delay
    movl $0xC4600, 0x300
    call delay
    popq %rbp
    ret

delay:
    pushq %rbp
    movq %rsp, %rbp
    movq $1000000, %rcx
.delay_loop:
    decq %rcx
    jnz .delay_loop
    popq %rbp
    ret

enable_paging:
    pushq %rbp
    movq %rsp, %rbp
    movq $pml4_table, %rax
    orq $0x3, %rax
    movq %rax, pml4_table(%rax)
    movq $pdpt_table, %rax
    orq $0x3, %rax
    movq %rax, pml4_table(%rax)
    movq $pd_table, %rax
    orq $0x3, %rax
    movq %rax, pdpt_table(%rax)
    movq $0, %rcx
.pd_loop:
    movq %rcx, %rax
    shl $30, %rax
    orq $0x83, %rax
    movq %rax, pd_table(,%rcx,8)
    incq %rcx
    cmpq $4, %rcx
    jne .pd_loop
    popq %rbp
    ret

init_gdt:
    ret

.section .rodata
.align 16
gdt_start:
    .quad 0x0
gdt_code:
    .quad 0x00AF9A000000FFFF
gdt_data:
    .quad 0x00AF92000000FFFF
gdt_end:
gdt_descriptor:
    .word gdt_end - gdt_start - 1
    .quad gdt_start

.section .bss
.align 4096
pml4_table:
    .skip 4096
pdpt_table:
    .skip 4096
pd_table:
    .skip 4096
bss_start:
    .skip 8192
bss_end:

.section .data
multiboot_info_ptr:
    .quad 0
logical_per_core:
    .byte 1
