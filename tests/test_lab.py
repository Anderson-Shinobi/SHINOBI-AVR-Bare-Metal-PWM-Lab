"""Independent checks of AVR firmware integrity, circuit and Wokwi VCD."""
from __future__ import annotations

from hashlib import sha256, sha1
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_vcd import analyze  # noqa: E402


class LaboratoryTests(unittest.TestCase):
    def test_verbatim_sources_and_license(self):
        def git_blob_hash(path):
            data = path.read_bytes()
            return sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

        self.assertEqual(git_blob_hash(ROOT / "sketch.ino"),
                         "037cfcba7716752d652765cf5dd9e675097fafe8")
        self.assertEqual(git_blob_hash(ROOT / "diagram.json"),
                         "0bfd6c628c86e034b161155ba9343015ff945288")
        self.assertIn("MIT License", (ROOT / "LICENSE").read_text())
        self.assertIn("SPDX-License-Identifier: MIT", (ROOT / "sketch.ino").read_text())

    def test_wokwi_circuit(self):
        d = json.loads((ROOT / "diagram.json").read_text())
        self.assertEqual(len(d["parts"]), 4)
        edges = {(c[0], c[1]) for c in d["connections"]}
        for edge in (
            ("uno:9", "logic1:D0"),
            ("uno:13", "logic1:D1"),
            ("uno:GND.3", "logic1:GND"),
            ("uno:9", "r1:1"),
            ("r1:2", "led1:A"),
            ("led1:C", "uno:GND.2"),
        ):
            self.assertIn(edge, edges)

    def test_original_vcd_and_results(self):
        capture = ROOT / "evidence/wokwi-logic.vcd"
        self.assertEqual(sha256(capture.read_bytes()).hexdigest(),
                         "ff1776c9ea30cd50fc9a6cf58690bdff75a9f90eee0a602dcc77d1d6e4320cd0")
        measured = analyze(capture)
        self.assertEqual(measured["cycles"], 4586)
        self.assertEqual(measured["period_ns"], 1_024_000)
        self.assertEqual(measured["frequency_hz"], 976.5625)
        self.assertEqual({row["high_us_approx"] for row in measured["rows"]}, {104, 512, 920})
        self.assertEqual(measured["gpio_toggles"], 5)


if __name__ == "__main__":
    unittest.main()
