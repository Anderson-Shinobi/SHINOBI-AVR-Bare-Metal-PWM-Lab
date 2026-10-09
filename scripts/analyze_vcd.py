#!/usr/bin/env python3
"""Measure PWM edges and GPIO timing in a Wokwi VCD capture.

Python standard library only; this measures simulated logic timestamps.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
from statistics import median

TIME_UNITS_TO_NS = {
    "s": 1_000_000_000, "ms": 1_000_000, "us": 1_000, "ns": 1,
    "ps": 0.001, "fs": 0.000001,
}


def parse_vcd(path: Path):
    definitions = {}
    changes = defaultdict(list)
    current = 0
    previous = {}
    timescale = None
    header = True
    with path.open(encoding="utf-8") as stream:
        for row in stream:
            row = row.strip()
            if header:
                if row.startswith("$var"):
                    tokens = row.split()
                    if len(tokens) >= 5 and tokens[2] == "1":
                        definitions[tokens[4]] = tokens[3]
                if row.startswith("$timescale"):
                    data = row.replace("$timescale", "").replace("$end", "").strip()
                    match = re.fullmatch(r"(\d+)\s*(fs|ps|ns|us|ms|s)", data)
                    if match:
                        timescale = int(match.group(1)) * TIME_UNITS_TO_NS[match.group(2)]
                if row.startswith("$enddefinitions"):
                    header = False
                continue
            if row.startswith("#"):
                current = int(row[1:])
                continue
            if len(row) >= 2 and row[0] in "01":
                value, identifier = row[0], row[1:].strip()
                if identifier in previous and previous[identifier] == value:
                    continue
                previous[identifier] = value
                changes[identifier].append((current, int(value)))
    if timescale is None:
        raise ValueError("Unsupported or missing VCD timescale")
    return definitions, changes, timescale


def pwm_cycles(events):
    rises = [tick for tick, state in events if state == 1]
    falls = [tick for tick, state in events if state == 0]
    j = 0
    cycles = []
    for start, end in zip(rises, rises[1:]):
        while j < len(falls) and falls[j] <= start:
            j += 1
        if j < len(falls) and falls[j] < end:
            cycles.append((end - start, falls[j] - start))
    return cycles


def analyze(path: Path, pwm="D0", gpio="D1"):
    names, changes, tick_ns = parse_vcd(path)
    for name in (pwm, gpio):
        if name not in names:
            raise ValueError(f"Channel {name} not defined. Available: {', '.join(names)}")
    cycles = pwm_cycles(changes[names[pwm]])
    if not cycles:
        raise ValueError(f"Channel {pwm} has no complete PWM periods")
    groups = defaultdict(list)
    for total, high in cycles:
        groups[round(high * tick_ns / 1000)].append((total, high))
    median_ticks = median([period for period, _ in cycles])
    period_ns = median_ticks * tick_ns
    rows = []
    for key, segment in sorted(groups.items()):
        group_period = median([period for period, _ in segment]) * tick_ns
        high_ns = median([high for _, high in segment]) * tick_ns
        rows.append({
            "high_us_approx": key, "cycles": len(segment),
            "high_us": high_ns / 1000,
            "low_us": (group_period - high_ns) / 1000,
            "duty_percent": 100 * high_ns / group_period,
        })
    toggles = [tick for tick, state in changes[names[gpio]][1:]]
    intervals = [(b - a) * tick_ns for a, b in zip(toggles, toggles[1:])]
    return {
        "cycles": len(cycles),
        "period_ns": period_ns,
        "frequency_hz": 1_000_000_000 / period_ns,
        "rows": rows,
        "gpio_toggles": len(toggles),
        "gpio_median_interval_s": median(intervals) / 1_000_000_000 if intervals else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vcd", type=Path)
    parser.add_argument("--pwm", default="D0")
    parser.add_argument("--gpio", default="D1")
    opts = parser.parse_args()
    result = analyze(opts.vcd, opts.pwm, opts.gpio)
    print(f"Complete PWM cycles: {result['cycles']}")
    print(f"PWM period: {result['period_ns']:.3f} ns")
    print(f"PWM frequency: {result['frequency_hz']:.6f} Hz")
    for row in result["rows"]:
        print(f"High ≈ {row['high_us_approx']} us: n={row['cycles']}, "
              f"HIGH={row['high_us']:.3f} us, LOW={row['low_us']:.3f} us, "
              f"duty={row['duty_percent']:.5f}%")
    print(f"D1 transitions: {result['gpio_toggles']}")
    if result["gpio_median_interval_s"] is not None:
        print(f"D1 median interval: {result['gpio_median_interval_s']:.9f} s")


if __name__ == "__main__":
    main()
