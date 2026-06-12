"""Compliance gate for the ACN1408 CAP drawings package.

Asserts, for a legal filing:
  1. all five figure PNGs exist and are genuinely BILEVEL (no greyscale shading) — the
     real patent-compliance invariant (a "no chromatic pixels" test is insufficient
     because anti-aliased black is grey);
  2. no forbidden / stale literal ('22 KB', '5x'/'5×', bare 'AES-256') appears in any
     figure script or the disclosure text;
  3. reference-numeral integrity — every numeral in the registry is cited in both the
     disclosure text and the numeral table, and every numeral drawn in a figure script
     belongs to the registry (no orphans).

Exit code 0 = compliant; non-zero = blocking issue (prints all failures).
"""
from __future__ import annotations

import re
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import patent_style as ps  # noqa: E402

FIGURES = [
    "fig1_system_architecture",
    "fig2_sequence",
    "fig3_ai_framework",
    "fig4_model_architecture",
    "fig5_vehicle_state_machine",
]


def _fail(msgs, text):
    msgs.append(text)


def main() -> int:
    failures: list[str] = []

    # 1. figures present + bilevel
    for name in FIGURES:
        png = HERE / "figures" / f"{name}.png"
        if not png.exists():
            _fail(failures, f"[missing] {png}")
            continue
        frac = ps.mid_grey_fraction(png)
        if frac > 0.002:
            _fail(failures, f"[greyscale] {name}.png mid-grey fraction {frac:.4f} > 0.002 "
                            "(not bilevel — would read as shading)")

    # 2. forbidden / stale literals in figure scripts + disclosure
    scan_files = [HERE / "gen" / f"{n}.py" for n in FIGURES]
    scan_files.append(HERE / "disclosure_ai_section.md")
    for f in scan_files:
        txt = f.read_text(encoding="utf-8")
        for lit in ps.FORBIDDEN_LABELS:
            if lit in txt:
                _fail(failures, f"[stale-label] '{lit}' found in {f.name}")
        # AES-256 only allowed adjacent to 'per spec'
        for m in re.finditer(r"AES-256", txt):
            window = txt[m.start():m.start() + 40].lower()
            if "per spec" not in window:
                _fail(failures, f"[aes-claim] 'AES-256' in {f.name} not qualified 'per spec'")

    # 3. numeral integrity
    disclosure = (HERE / "disclosure_ai_section.md").read_text(encoding="utf-8")
    table = (HERE / "reference_numerals.md").read_text(encoding="utf-8")
    registry = set(ps.NUMERALS.values())
    for num in sorted(registry):
        if f"({num})" not in disclosure and f" {num} " not in disclosure:
            _fail(failures, f"[uncited] numeral {num} not cited in disclosure_ai_section.md")
        if f"| {num} |" not in table:
            _fail(failures, f"[untabled] numeral {num} missing from reference_numerals.md")
    # orphan numerals drawn in figures but not in registry
    for n in FIGURES:
        src = (HERE / "gen" / f"{n}.py").read_text(encoding="utf-8")
        for m in re.finditer(r'ps\.n\("([a-z_]+)"\)', src):
            if m.group(1) not in ps.NUMERALS:
                _fail(failures, f"[orphan] {n}.py references unknown numeral key '{m.group(1)}'")

    if failures:
        print("COMPLIANCE: FAIL")
        for msg in failures:
            print("  -", msg)
        return 1
    print("COMPLIANCE: PASS — 5 bilevel figures, no stale labels, %d numerals consistent"
          % len(registry))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
