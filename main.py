# Author: Aleix
# Github: https://github.com/Algafix/
#
# Tesla charging port opener using RP2040 PIO for deterministic timing.
# Auto-detects board: Raspberry Pi Pico, Pico W, or Pimoroni Tiny 2040.

import os
import rp2
from machine import Pin
from time import sleep, sleep_ms

# --- Board detection ---
_board = os.uname().machine
_is_tiny = 'Tiny 2040' in _board

if _is_tiny:
    DATA_PIN = 29
    red = Pin(18, Pin.OUT, value=1)    # Active-low: value=1 is OFF
    green = Pin(19, Pin.OUT, value=1)
    blue = Pin(20, Pin.OUT, value=1)
else:
    DATA_PIN = 0
    led = Pin('LED' if 'Pico W' in _board else 25, Pin.OUT, value=0)
del _board

# --- Signal ---
# Tesla charging port ASK/OOK signal: 333 symbols at 2.5 kHz (400 us/symbol)
_signal = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1]

# Pack into 32-bit words for PIO (LSB-first shift order)
signal_words = []
for _i in range(0, len(_signal), 32):
    _w = 0
    for _j, _b in enumerate(_signal[_i:_i + 32]):
        _w |= _b << _j
    signal_words.append(_w)
del _signal

REPEAT = 10

# --- PIO program: output one bit per cycle ---
@rp2.asm_pio(out_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_RIGHT,
             autopull=True, pull_thresh=32)
def tx_bit():
    out(pins, 1)

# freq=2500 -> each PIO cycle = 1/2500s = exactly 400 us per symbol
sm = rp2.StateMachine(0, tx_bit, freq=2500, out_base=Pin(DATA_PIN))
sm.active(1)

# --- Main loop ---
while True:
    for _r in range(REPEAT):
        for w in signal_words:
            sm.put(w)
        # Zero-padding in last word provides inter-repetition gap
        if _is_tiny:
            red.toggle()
        else:
            led.toggle()

    sm.put(0)  # Ensure output returns to low

    if _is_tiny:
        red.value(1)
        for _ in range(2):
            blue.value(0)
            sleep_ms(500)
            blue.value(1)
            sleep_ms(500)
    else:
        led.value(0)
        sleep(3)
