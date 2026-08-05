; Fusion Hero OS — Injection table (x86_64 NASM)
; Primary kernel language surface: Assembly
; Max injectability = fixed slot table + atomic generation + trampoline dispatch
;
; Build: nasm -f elf64 -o inject_table.o inject_table.s
; Host note: also mirrored by inject_host.py for Windows control plane

BITS 64
DEFAULT REL

section .data
global fhos_inject_table
global fhos_inject_epoch

; magic "FHOSINJ\0" as little-endian qwords pattern
fhos_inject_table:
    dq 0x004A4E49534F4846   ; magic (loosely FHOSINJ)
    dd 256                  ; n_slots
    dd 0                    ; active_count
fhos_inject_epoch:
    dq 0                    ; epoch
    ; slots[256] * 56 bytes ≈ zero-filled BSS preferred — keep small stub here
    ; Full table lives in .bss (fhos_inject_slots_bss)
    times 16 db 0

section .bss
align 16
global fhos_inject_slots_bss
; each slot: flags(4)+caps(4)+qid(4)+gen(4)+entry(8)+name(32) = 56
fhos_inject_slots_bss:
    resb 256 * 56

section .text

global fhos_inject_init
global fhos_inject_register
global fhos_inject_swap
global fhos_inject_call
global fhos_inject_clear

; void fhos_inject_init(void)
fhos_inject_init:
    push rbx
    lea rdi, [rel fhos_inject_slots_bss]
    mov rcx, (256 * 56) / 8
    xor rax, rax
    rep stosq
    mov dword [rel fhos_inject_table + 12], 0   ; active_count = 0
    inc qword [rel fhos_inject_epoch]
    pop rbx
    ret

; slot layout offsets
; 0 flags, 4 caps, 8 qid, 12 gen, 16 entry, 24 name[32]

; int fhos_inject_register(uint32_t slot, const char *name, uint32_t quantum_id,
;                          uint32_t caps, uint32_t flags, fhos_inject_fn fn)
; Win64/SysV hybrid: we use SysV here (rdi,rsi,rdx,rcx,r8,r9) for freestanding
; slot=edi name=rsi qid=edx caps=ecx flags=r8d fn=r9
fhos_inject_register:
    cmp edi, 256
    jae .err
    push rbx
    push r12
    mov r10d, edi                 ; slot
    mov r11, rsi                  ; name
    ; base = slots_bss + slot*56
    mov eax, 56
    mul r10d
    lea rbx, [rel fhos_inject_slots_bss]
    add rbx, rax

    ; write fields
    or r8d, 1                     ; ACTIVE
    mov dword [rbx + 0], r8d      ; flags
    mov dword [rbx + 4], ecx      ; caps
    mov dword [rbx + 8], edx      ; quantum_id
    inc dword [rbx + 12]          ; generation++
    mov qword [rbx + 16], r9      ; entry

    ; copy name (max 31 + NUL)
    lea rdi, [rbx + 24]
    mov rcx, 31
    xor eax, eax
    test r11, r11
    jz .name_done
.copy_name:
    mov al, [r11]
    mov [rdi], al
    test al, al
    jz .name_done
    inc r11
    inc rdi
    dec rcx
    jnz .copy_name
    mov byte [rdi], 0
.name_done:
    lock inc dword [rel fhos_inject_table + 12]
    lock inc qword [rel fhos_inject_epoch]
    xor eax, eax                  ; success 0
    pop r12
    pop rbx
    ret
.err:
    mov eax, -1
    ret

; int fhos_inject_swap(uint32_t slot, fhos_inject_fn fn, uint32_t holder_caps)
; slot=edi fn=rsi holder_caps=edx
fhos_inject_swap:
    cmp edi, 256
    jae .sw_err
    mov eax, 56
    mul edi
    lea rcx, [rel fhos_inject_slots_bss]
    add rcx, rax
    ; check ACTIVE
    test dword [rcx + 0], 1
    jz .sw_err
    ; check HOT flag bit1
    test dword [rcx + 0], 2
    jz .sw_err
    ; holder_caps must include required
    mov eax, [rcx + 4]
    not edx
    test eax, edx
    jnz .sw_cap_fail
    mov qword [rcx + 16], rsi
    inc dword [rcx + 12]
    lock inc qword [rel fhos_inject_epoch]
    xor eax, eax
    ret
.sw_cap_fail:
    mov eax, -2
    ret
.sw_err:
    mov eax, -1
    ret

; uint64_t fhos_inject_call(slot, a0, a1, a2, a3, holder_caps)
; SysV: edi, rsi, rdx, rcx, r8, r9d
fhos_inject_call:
    cmp edi, 256
    jae .call_zero
    push rbx
    push r12
    push r13
    push r14
    mov r12, rsi                  ; a0
    mov r13, rdx                  ; a1
    mov r14, rcx                  ; a2
    ; r8 = a3, r9d = caps
    mov eax, 56
    mul edi
    lea rbx, [rel fhos_inject_slots_bss]
    add rbx, rax
    test dword [rbx + 0], 1
    jz .call_fail
    mov eax, [rbx + 4]
    mov r10d, r9d
    not r10d
    test eax, r10d
    jnz .call_fail
    mov r11, [rbx + 16]           ; entry
    test r11, r11
    jz .call_fail
    ; call entry(a0,a1,a2,a3)
    mov rdi, r12
    mov rsi, r13
    mov rdx, r14
    mov rcx, r8
    call r11
    pop r14
    pop r13
    pop r12
    pop rbx
    ret
.call_fail:
    pop r14
    pop r13
    pop r12
    pop rbx
.call_zero:
    xor rax, rax
    ret

; int fhos_inject_clear(slot, holder_caps)
fhos_inject_clear:
    cmp edi, 256
    jae .cl_err
    mov eax, 56
    mul edi
    lea rcx, [rel fhos_inject_slots_bss]
    add rcx, rax
    mov eax, [rcx + 4]
    not esi
    test eax, esi
    jnz .cl_cap
    ; zero slot
    mov rdi, rcx
    mov ecx, 56 / 8
    xor eax, eax
    rep stosq
    lock dec dword [rel fhos_inject_table + 12]
    lock inc qword [rel fhos_inject_epoch]
    xor eax, eax
    ret
.cl_cap:
    mov eax, -2
    ret
.cl_err:
    mov eax, -1
    ret
