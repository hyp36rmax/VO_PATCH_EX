bits 32
; Draws the patcher's version in the bottom right of the title screen.
;
; The game's own tile font, the one the menu items on this screen are set
; in: 0x4cd8c3 puts the cursor at a cell and 0x4ceeeb prints through it,
; which is exactly what 0x44b757 does with the table at 0x6537c0.
;
; 0x4ceeeb picks the glyph set itself, out of the four at 0x600ec8: a string
; with lower case in it gets the set that has lower case, which is why this
; one can be mixed case.
;
; Build-time title data supplies cursor positions and ASCII text runs. The
; subordinate build label uses the existing mixed-case face on the next row.
; Its middle dot uses the original period one tile row higher because the
; native printer strips the high bit rather than accepting Unicode.
;
; GDI was the obvious way and the wrong one here. It is what the pause text
; and HOLD TO SKIP use, but the game builds exactly two fonts at 0x5c8cd7 -
; century and modern bold, 24px - and 0x5c991c takes an index into that pair
; rather than a handle. Neither belongs on this screen and neither is small.
; The tile font costs less code than either, since none of the surface
; juggling GDI needs applies: no back buffer, no halving for low resolution.
;
; The hook is the load at 0x5c6500, four instructions past the call the
; overlay took and still ahead of the flip at 0x5c650d, so the two patches
; share no bytes and either can be applied without the other. Nothing here
; needs to run at that point in the frame - the tiles are read on the next
; one - but it is a five-byte site on a path that runs every frame, which is
; what this needs. The displaced load is repeated at the end.
;
; Reserved title data is filled only after source-locked reconstruction.

extern CURSOR                   ; (column, row), cdecl
extern PRINT                    ; (text), cdecl, from the cursor
extern PRIMARY                  ; what the displaced load reads

; 0x1ae3594 picks the machine through the table at 0x5fe5e0 and 0x1ae3690 is
; its state. All three of these are machine 1, the attract one, whose
; dispatcher is 0x44b38c and whose table is 0x5fb238. 6 and 0x17 are the logo
; with the blinking banner - 0x17 is 0x44b89d, which calls 6's own handler at
; 0x545dfa - and 0x11 is the logo with the menu. 7 is the demo match and is
; the reason this is three tests and not a range.
extern MODE
extern SUBMODE
ATTRACT     equ 1
PROMPT      equ 0x06            ; 0x545dfa, the logo and Press A Button
PROMPT2     equ 0x17            ; 0x44b89d, the same screen later in the loop
MENU        equ 0x11            ; 0x44b5bc, 1 PLAYER and the two below it

; Cells, of the 81-wide map, two per character. The copyright line is 59 of
; them from column 1 at row 44, which is what these were measured against.
RIGHT       equ 79              ; one past the last cell the line may use
ROW         equ 48

TEXTLEN     equ 24              ; what the patcher has to write the version in

titlever:
    cmp     dword [MODE], ATTRACT
    jne     .out
    mov     eax, [SUBMODE]
    cmp     eax, PROMPT
    je      .draw
    cmp     eax, PROMPT2
    je      .draw
    cmp     eax, MENU
    jne     .out
.draw:
    pushad
    mov     esi, positions
.next:
    movzx   eax, byte [esi]
    test    eax, eax
    jz      .done
    movzx   edx, byte [esi+1]
    push    edx
    push    eax
    call    CURSOR
    add     esp, 8
    movzx   eax, byte [esi+2]
    add     eax, strings
    push    eax
    call    PRINT
    add     esp, 4
    add     esi, 3
    jmp     .next
.done:
    popad
.out:
    mov     eax, [PRIMARY]
    ret

; Four original-font text runs plus a zero terminator. The separator uses
; the existing period glyph one tile row higher, not an unsupported byte.
; Keep the existing footprint so no neighboring payload changes address.
    times 95-($-$$) db 0x90
    db 1
positions:
    times 15 db 0
strings:
    times 44 db 0
