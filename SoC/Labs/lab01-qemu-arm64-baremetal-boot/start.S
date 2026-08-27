.section .text.boot
.global _start
_start:
    ldr x0, =stack_top
    mov sp, x0
    bl kernel_main
1:  wfe
    b 1b

.section .bss.stack, "aw", %nobits
.align 12
stack_bottom:
    .skip 16384
stack_top:
