
[comment]: # (Author: Aleix)
[comment]: # (Github: https://github.com/Algafix/)

Raspberry pico - Tesla charging port opener
===

Tesla's charging port signal has been known for years. There are several projects about how to retransmit it, how to sample it for HackRF or other SDR's and how to retransmit it. However, I couldn't find a micropython implementation so I decided to have some fun.

The signal has simple ASK/OOK modulation with 2.5 kHz of sample rate, easy enough to attempt a microcontroller micropython implementation.

For more information about the Tesla's charging port signal and how to reverse engineer it:

* [Original tweet](https://twitter.com/IfNotPike/status/1507818836568858631)
* [HackRF based](https://github.com/rgerganov/tesla-opener)
* [How to reverse engineer](https://github.com/akrutsinger/tesla-charge-port-signal)

How to use
===

Components
---

* Raspberry Pico
* 433.92 MHz transmitter for Europe (315 MHz for USA)
    * FS1000A   - Meh, it may work or it may not, pray 
    * STX882    - Much better option
* Antenna or 17 cm of wire [Optional]
* A way to connect everything

Assembly
---

1. Connect/solder the pins from the transmitter to the pico
    * VCC -> VBUS
    * GND -> GND
    * DATA -> GP0   (change the code if you prefer another pin)

2. Flash the pico with micropython: [official documentation](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html).

3. Load `main.py` onto the board. It auto-detects the board type (Raspberry Pi Pico, Pico W, or Pimoroni Tiny 2040) and configures pins accordingly.


Use
---

You may connect the pico to your phone or get a battery for power on the go :)

Here an example of a portable implementation using a Tiny2040.

<p align="center">
   <img src="docs/front.jpg" height="35%" width="35%" />
   <img src="docs/back.jpg"  height="35%" width="33.7%" />
</p>

Note
---

The script blinks the LED of the board automatically. Pico W is supported and requires MicroPython >= 1.19.1.

Results
===

I've added a recorded signal generated with the pico to the docs folder, sampled at 1MHz with an RTL-SDR.

The raw signal looks like this in [Inspectrum](https://github.com/miek/inspectrum).

![Raw signal image](docs/pico_signal.png)

Once we adjust the min and max power values, we can add an amplitude plot and check that it can really be decoded to the original signal.

![Signal with amplitude thresholds image](docs/pico_signal_amplitude.png)

    101010101010101010101010100010101100101100110010110011001100110011001011010011010010110101001010110100110100110010101011010010110001010110010110011001011001100110011001100101101001101001011010100101011010011010011001010101101001011000101011001011001100101100110011001100110010110100110100101101010010101101001101001100101010110100101

Timing
===

The transmitted signal has a symbol period of 400us. The code uses the RP2040's PIO (Programmable I/O) state machine to output bits at exactly 2500 Hz, giving deterministic 400us symbol timing independent of Python execution overhead. No manual tuning is needed.

Earlier versions used `sleep_us()` which required a manual compensation factor due to Python overhead, resulting in timing drift over the 333-symbol signal. The PIO approach eliminates this entirely.

![Samples too long](docs/samples_delayed.png)
![Samples corrected](docs/samples_corrected.png)
