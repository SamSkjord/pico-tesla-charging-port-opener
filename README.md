
[comment]: # (Author: Aleix)
[comment]: # (Github: https://github.com/Algafix/)

Raspberry Pico - Tesla charging port opener
===

Tesla's charging port signal has been known for years. There are several projects about how to retransmit it, how to sample it for HackRF or other SDRs and how to retransmit it. However, I couldn't find a MicroPython implementation so I decided to have some fun.

The signal has simple ASK/OOK modulation with 2.5 kHz of sample rate, easy enough to attempt a microcontroller MicroPython implementation.

For more information about the Tesla's charging port signal and how to reverse engineer it:

* [Original tweet](https://twitter.com/IfNotPike/status/1507818836568858631)
* [HackRF based](https://github.com/rgerganov/tesla-opener)
* [How to reverse engineer](https://github.com/akrutsinger/tesla-charge-port-signal)

Supported boards
---

A single `main.py` file auto-detects the board at startup using `os.uname().machine` and configures pin assignments accordingly.

| Board | Data pin | LED feedback | Notes |
|-------|----------|-------------|-------|
| Raspberry Pi Pico | GP0 | On-board LED (GP25) toggles during transmission | |
| Raspberry Pi Pico W | GP0 | On-board LED toggles during transmission | Requires MicroPython >= 1.19.1 |
| Pimoroni Tiny 2040 | GP29 | Red toggles during transmission, blue blinks between bursts | Active-low RGB LEDs |

How to use
===

Components
---

* One of the supported boards listed above
* 433.92 MHz transmitter for Europe (315 MHz for USA)
    * FS1000A - May or may not work reliably
    * STX882 - Much better option
* Antenna or 17 cm of wire [Optional]
* A way to connect everything

Assembly
---

1. Connect or solder the pins from the transmitter to the board:
    * VCC -> VBUS
    * GND -> GND
    * DATA -> GP0 (or GP29 on Tiny 2040)

2. Flash the board with MicroPython: [official documentation](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html).

3. Load `main.py` onto the board. The script detects the board type automatically and sets up the correct data pin and LED configuration.

Use
---

You may connect the board to your phone or get a battery for power on the go :)

Here an example of a portable implementation using a Tiny2040.

<p align="center">
   <img src="docs/front.jpg" height="35%" width="35%" />
   <img src="docs/back.jpg"  height="35%" width="33.7%" />
</p>

How it works
===

Signal
---

The 333-symbol signal is transmitted 10 times per burst with a 5-symbol (2 ms) gap between each repetition. After a full burst, the script waits 3 seconds (or 2 seconds on the Tiny 2040 with blue LED feedback) before starting the next burst.

At startup, all 10 repetitions are packed into a continuous bitstream of 32-bit words. This avoids per-repetition Python loop overhead during transmission and ensures the inter-repetition gaps are exactly 5 symbols long.

Timing
---

The transmitted signal has a symbol period of 400 us (2.5 kHz). The code uses the RP2040's PIO (Programmable I/O) state machine to shift out bits at exactly 2500 Hz, giving deterministic 400 us symbol timing that is independent of Python execution speed. No manual tuning is needed.

The PIO program is a single instruction:

```python
@rp2.asm_pio(out_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_RIGHT,
             autopull=True, pull_thresh=32)
def tx_bit():
    out(pins, 1)
```

With `freq=2500`, the RP2040's 125 MHz system clock is divided by 50,000, so each `out` instruction takes exactly 400 us. Autopull transparently refills the output shift register from the TX FIFO at 32-bit word boundaries without adding any extra clock cycles. Python feeds words into the FIFO via `sm.put()`, which blocks when the FIFO is full. The 4-word FIFO depth provides 51.2 ms of buffer, which is more than enough headroom for Python to keep up.

When the FIFO empties (during the inter-burst delay), the state machine stalls and the output pin holds its last value. Since the final bits in the bitstream are always zeros, the pin stays low between bursts.

Earlier versions used `sleep_us()` to bit-bang the signal directly from Python. This required a manual compensation factor (`sleep_us(384)` instead of `sleep_us(400)`) to account for Python execution overhead, and the correction was fragile across different MicroPython versions and clock configurations. The PIO approach eliminates this problem entirely.

![Samples too long](docs/samples_delayed.png)
![Samples corrected](docs/samples_corrected.png)

Results
===

I've added a recorded signal generated with the pico to the docs folder, sampled at 1MHz with an RTL-SDR.

The raw signal looks like this in [Inspectrum](https://github.com/miek/inspectrum).

![Raw signal image](docs/pico_signal.png)

Once we adjust the min and max power values, we can add an amplitude plot and check that it can really be decoded to the original signal.

![Signal with amplitude thresholds image](docs/pico_signal_amplitude.png)

    101010101010101010101010100010101100101100110010110011001100110011001011010011010010110101001010110100110100110010101011010010110001010110010110011001011001100110011001100101101001101001011010100101011010011010011001010101101001011000101011001011001100101100110011001100110010110100110100101101010010101101001101001100101010110100101
