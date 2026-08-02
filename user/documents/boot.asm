; Simple Bootloader Example
section .text
    global _start

_start:
    ; Print "Hello World!" to the screen
    mov si, message
    call print_string

    ; Infinite loop
    jmp $

print_string:
    ; Print string pointed by SI
    mov ah, 0x0E
.next_char:
    lodsb
    cmp al, 0
    je .done
    int 0x10
    jmp .next_char
.done:
    ret

section .data
message db 'Hello World!', 0
