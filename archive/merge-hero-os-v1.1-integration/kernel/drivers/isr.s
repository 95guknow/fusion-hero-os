// Interrupt Service Routines for SMP
// These are called by the CPU when interrupts occur

.section .text64

.global isr0
isr0:
    cli
    pushq $0
    pushq $0
    pushq %rax
    pushq %rbx
    pushq %rcx
    pushq %rdx
    pushq %rsi
    pushq %rdi
    pushq %r8
    pushq %r9
    pushq %r10
    pushq %r11
    pushq %r12
    pushq %r13
    pushq %r14
    pushq %r15
    movq %rsp, %rdi
    call isr_handler_0
    popq %r15
    popq %r14
    popq %r13
    popq %r12
    popq %r11
    popq %r10
    popq %r9
    popq %r8
    popq %rdi
    popq %rsi
    popq %rdx
    popq %rcx
    popq %rbx
    popq %rax
    addq $16, %rsp
    sti
    iretq

.global isr32
isr32:
    // Local APIC timer interrupt
    // Used for preemptive scheduling in SMP
    cli
    pushq $0
    pushq $32
    // Send EOI to LAPIC
    movl $0xFEE000B0, %eax
    movl $0x0, (%eax)
    // Acknowledge interrupt for all cores (IPI-based)
    movq $smp_timer_tick, %rax
    call *%rax
    iretq

.global isr33
isr33:
    // IPI handler for inter-processor communication
    // Hyperthreading-aware: distinguish between sibling threads
    cli
    pushq $0
    pushq $33
    // Get current APIC ID
    movl $0xFEE00320, %eax
    movl (%eax), %ebx
    // Extract core/thread information for HT decision
    call handle_ipi
    iretq

.global isr34
isr34:
    // IPI handler - scheduler reschedule
    cli
    pushq $0
    pushq $34
    call smp_reschedule
    iretq

.extern isr_handler_0
.extern smp_timer_tick
.extern handle_ipi
.extern smp_reschedule
