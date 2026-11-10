#!/usr/bin/env python3
"""Check that stated values in the packaged CSVs match the manuscript prose."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(name: str) -> list[dict[str, str]]:
    path = DATA / name
    comments_ok = False
    with path.open(encoding="utf-8") as f:
        # skip comment lines
        lines = [ln for ln in f if not ln.startswith("#") and ln.strip()]
    reader = csv.DictReader(lines)
    rows = list(reader)
    if not rows:
        raise SystemExit(f"{name}: no data rows")
    comments_ok = True
    return rows


def get(rows, key, field, value_field="value"):
    hits = [r for r in rows if r[field] == key]
    if len(hits) != 1:
        raise SystemExit(f"expected one row for {field}={key!r}, found {len(hits)}")
    return hits[0][value_field]


def parse_range(s: str) -> tuple[float, float]:
    a, b = s.split("-")
    return float(a), float(b)


def main() -> int:
    results = load("oled-stated-results.csv")
    params = load("oled-fabrication-parameters.csv")
    arch = load("oled-device-architecture.csv")
    market = load("oled-section6-market-projections-as-stated.csv")
    lit = load("literature-cited-values-not-this-work.csv")

    print("Printable OLED manuscript: stated-number checks")
    print("----------------------------------------------")

    # Luminance wording is consistent in abstract and §5.1 (same CSV row).
    lum = get(results, "maximum_luminance", "quantity")
    assert lum == ">2350", lum
    print(f"Maximum luminance (abstract and §5.1): {lum} cd/m²")

    rh = get(results, "humidity_response_range", "quantity")
    lo, hi = parse_range(rh)
    assert (lo, hi) == (30.0, 90.0)
    print(f"Humidity range (abstract, §3.2, §5.2): {lo:.0f}–{hi:.0f} % RH")

    sens = get(results, "humidity_sensitivity", "quantity")
    assert sens == "up to 52", sens
    print(f"Sensitivity as stated in §5.2: {sens}%")

    retained = get(results, "luminance_retained_at_90_deg_bend", "quantity")
    assert retained == ">85", retained
    bend = get(results, "bending_curvature", "quantity")
    assert bend == "90", bend
    cycles = get(results, "bending_cycles_stable", "quantity")
    assert cycles == ">200", cycles
    print(f"Bend test (§5.1): retain {retained}% of initial luminance at {bend}°; stable over {cycles} cycles")

    wet = get(results, "interactive_wetting_dewetting_cycles_tested", "quantity")
    assert wet == "2000", wet
    print(f"Interactive cycles tested (§5.3): {wet}")

    # Electrode spacing appears in both the hypothesis and the process section.
    spacing_result = get(results, "electrode_spacing", "quantity")
    spacing_param = get(
        [r for r in params if r["parameter"] == "electrode_spacing"],
        "electrode_spacing",
        "parameter",
    ) if False else None
    spacing_rows = [r for r in params if r["parameter"] == "electrode_spacing"]
    assert len(spacing_rows) == 1
    spacing_param = spacing_rows[0]["value"]
    assert spacing_result == "0.5" and spacing_param == "0.5"
    print(f"Electrode spacing (§3.2 and §4.2): {spacing_param} mm (matches in both CSVs)")

    # Process range arithmetic: each stated min–max range is well ordered.
    range_params = [
        "nozzle_diameter",
        "printing_speed",
        "curing_temperature",
        "blade_height",
    ]
    for r in params:
        if r["parameter"] in range_params and "-" in r["value"]:
            a, b = parse_range(r["value"])
            assert a < b, r
            print(f"  range OK: {r['step']} {r['parameter']} = {r['value']} {r['unit']} ({a} < {b})")

    # Both blade-coated functional films use the stated coating speed of 5 mm/s.
    speeds = [r["value"] for r in params if r["parameter"] == "coating_speed"]
    assert speeds == ["5", "5"], speeds
    print("Dielectric and emitting-layer coating speed (§4.2): both 5 mm/s")

    # Architecture has five layers from the substrate upward.
    assert [r["order_from_substrate"] for r in arch] == ["1", "2", "3", "4", "5"]
    assert "PET" in arch[0]["layer"]
    print("Architecture (§4.1): 5 layers, PET substrate first")

    # Market and literature files load and have the stated counts (transcription checks only).
    assert len(market) == 3
    assert len(lit) == 7
    print(f"Section 6 market-projection rows loaded: {len(market)}")
    print(f"Literature-cited (not this work) rows loaded: {len(lit)}")

    print()
    print("RESULT: PASS (stated values match the packaged CSVs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
