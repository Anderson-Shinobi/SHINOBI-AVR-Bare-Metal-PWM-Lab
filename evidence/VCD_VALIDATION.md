# Experimental validation — ATmega328P Timer1 PWM (Wokwi VCD)

**Project:** [SHINOBI AVR Bare-Metal PWM Lab](https://wokwi.com/projects/477357756254868481)  
**Capture:** user-provided `wokwi-logic.vcd`, Wokwi.com export, header date 2026-10-09 00:05:34 GMT  
**Trace SHA-256:** `ff1776c9ea30cd50fc9a6cf58690bdff75a9f90eee0a602dcc77d1d6e4320cd0`  
**Capture size:** 135,763 bytes; **timescale:** 1 ns; **duration:** 4.697675250 s  
**Channels:** D0 = Arduino Uno D9/OC1A (PWM); D1 = D13/PB5 (status GPIO)

## Measurement method

Parse the VCD digital transitions using its 1 ns timestamps. Remove adjacent same-state duplicates. For each **complete** D0 PWM cycle, measure rising-to-rising time `T` and rising-to-falling high time `tHIGH`; compute `f = 1/T` and `duty = 100 × tHIGH/T`. Ignore incomplete cycles at the capture boundaries. Separate duty phases by the measured pulse widths (104, 512 or 920 microseconds). Separately compute D1 transition intervals.

The trace yields **4,586 complete D0 periods**. The median period is **1,024,000 ns = 1.024 ms**, giving **976.5625 Hz**. The captured period range is 1,023,999–1,024,001 ns (1 ns timestamp granularity).

| Register OCR1A | Label printed over UART | Measured HIGH | Measured LOW | Duty measured | Complete periods |
|---:|---:|---:|---:|---:|---:|
| 26 | 10% | 104 µs | 920 µs | **10.15625%** | 2,054 |
| 128 | 50% | 512 µs | 512 µs | **50.00000%** | 1,525 |
| 230 | 90% | 920 µs | 104 µs | **89.84375%** | 1,007 |

Measured values correspond to `OCR1A / 256` for the three states in this simulation. **The earlier estimates of 10.55% and 90.23% are contradicted by the actual VCD measurements.** The UART strings indicate approximate *targets*, not independent measured duty cycles.

## Phase sequence

| Segment | State | First complete period start | Last complete period start | Periods |
|---:|---:|---:|---:|---:|
| 1 | 10% | 0.001081 s | 1.071161 s | 1,046 |
| 2 | 50% | 1.072185 s | 2.103353 s | 1,008 |
| 3 | 90% | 2.104377 s | 3.134521 s | 1,007 |
| 4 | 10% | 3.135545 s | 4.166713 s | 1,008 |
| 5 | 50% | 4.167737 s | 4.696121 s | 517 |

D1 contains five GPIO transitions after its initial state. Four completed transition intervals are approximately **1.032967125 s**, **1.031934250 s**, **1.031928313 s**, **1.031927687 s**, with median **1.031931282 s**. This is approximately 3.19% longer than the nominal one-second delay. The VCD verifies GPIO toggling, *not* a precisely one-second toggle interval.

## Engineering acceptance

**PASS — Wokwi simulated digital timing:** D0 produces all three expected states; measured PWM frequency matches the Timer1 8-bit Fast PWM configuration at 16 MHz with prescaler 64: `16,000,000/(64 × 256) = 976.5625 Hz`. D1 toggling is captured. The experiment therefore verifies the **simulated digital waveform**, not the electrical characteristics of real hardware.

**Not tested:** physical Arduino oscillator tolerance, electrical output amplitude, rise/fall times, current through the LED, loading effects, power consumption, oscilloscope data, or matching of the live Wokwi editor to a particular Git commit.

### Provenance and reproducibility

This report is derived from a VCD supplied by the project author during a ChatGPT review. The original VCD **is not committed** in this change; it is identified by the SHA-256 fingerprint above. Preserve the original VCD alongside other laboratory artifacts if complete third-party reproduction is required. To repeat the measurements, extract D0 rising and falling edges from a Wokwi VCD with the same wiring, and recompute cycle durations and the D1 transition intervals. The machine-readable summary is in [measurements.csv](./measurements.csv).

**Result:** simulator PWM timing verified; **physical hardware verification remains open**.
