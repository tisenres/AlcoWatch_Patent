"""
Patent-grade 2D line-art toolkit for the ACN1408 CAP drawings.

Produces PURE black-on-white line art (no greyscale, no color) as required by the
Indian Patent Act 1970 / Patent Rules 2003 ("2D line diagrams only"). Anti-aliased
matplotlib output is chromatically neutral but full of mid-grey pixels that read as
halftone shading, so every figure is rendered with antialiasing off and the raster
is thresholded to genuine 1-bit black/white. A vector PDF is exported alongside.

Also holds the single source of truth for reference numerals (the 100-series scheme),
so numerals can never drift across figures or the disclosure text.

Usage (from a figure script in patent_cap/gen/):
    from patent_style import new_sheet, box, arrow, numeral_label, save, n
    fig, ax = new_sheet()
    c1 = box(ax, 10, 70, 24, 12, "Smartwatch", n('smartwatch'))
    c2 = box(ax, 50, 70, 24, 12, "AI module", n('ai_module'))
    arrow(ax, c1, c2)
    save(fig, "fig1_system_architecture")
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # headless, deterministic (mirrors scripts/generate_paper_figures.py)
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from pathlib import Path

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Reference-numeral registry (single source of truth) — 100-series by subsystem
# ---------------------------------------------------------------------------
NUMERALS: dict[str, int] = {
    "system": 100,
    # Wearable smartwatch device
    "smartwatch": 110,
    "ppg": 112,
    "eda": 114,            # estimated/derived (no dedicated EDA sensor) — see reconciliation
    "temp": 116,
    "ondevice": 118,       # on-device inference engine
    # AI / ML module
    "ai_module": 120,
    "preproc": 122,        # preprocessing + 10-timestep windowing
    "features": 124,       # feature tensor [10 x 6]
    "bilstm": 126,
    "attention": 128,
    "dense_head": 130,
    "calibration": 132,    # POST-inference climate-adaptive calibration (not a model layer)
    # Link
    "ble": 140,            # secure BLE link (AES-256 per spec)
    # Vehicle control module
    "vehicle_ctrl": 150,
    "ble_rx": 152,
    "safety_logic": 154,
    "relay": 156,          # relay / MOSFET switch
    "ignition": 160,       # ignition / OBD-II / ECU interface
    "indicators": 170,     # LED / buzzer
    "override": 180,
}

# Human-readable component descriptions for the reference-numeral table (single source).
DESCRIPTIONS: dict[str, str] = {
    "system": "AI-based alcohol detection & vehicle ignition prevention system",
    "smartwatch": "Wearable smartwatch device",
    "ppg": "Photoplethysmography (PPG) sensor",
    "eda": "Electrodermal activity (EDA), estimated/derived (no dedicated EDA sensor)",
    "temp": "Skin / ambient temperature sensor",
    "ondevice": "On-device inference engine (quantized TFLite)",
    "ai_module": "AI / ML module performing on-device BAC estimation",
    "preproc": "Signal preprocessing and 10-timestep windowing",
    "features": "Feature tensor of shape [10 timesteps x 6 features]",
    "bilstm": "Bidirectional LSTM (64 units) temporal-encoding stage",
    "attention": "Temporal attention mechanism (Dense-tanh score, softmax, weighted sum)",
    "dense_head": "Dense regression head (32 -> 16 -> 1) producing the BAC estimate",
    "calibration": "Climate-adaptive calibration (post-inference correction; not a network layer)",
    "ble": "Secure Bluetooth Low Energy link (AES-256 per specification)",
    "vehicle_ctrl": "Vehicle control module",
    "ble_rx": "BLE receiver",
    "safety_logic": "Fail-safe decision / safety logic (default: ignition blocked)",
    "relay": "Relay / MOSFET ignition switch",
    "ignition": "Ignition system / OBD-II / ECU interface",
    "indicators": "Status indicators (LED / buzzer)",
    "override": "Manual override button",
}

# Labels forbidden in figure scripts and disclosure text (stale / not-as-built).
# The compliance check (U8) greps for these; kept here as the shared definition.
FORBIDDEN_LABELS = ("22 KB", "5x", "5×")  # AES-256 allowed only as "per spec"


def numeral_table() -> str:
    """Render the reference-numeral lookup table as Markdown (sorted by numeral)."""
    rows = sorted(NUMERALS.items(), key=lambda kv: kv[1])
    out = ["| Reference numeral | Component |", "|---|---|"]
    for key, num in rows:
        out.append(f"| {num} | {DESCRIPTIONS.get(key, key)} |")
    return "\n".join(out)


def validate() -> None:
    """Assert reference numerals are unique. Raises ValueError on collision."""
    values = list(NUMERALS.values())
    dupes = sorted({v for v in values if values.count(v) > 1})
    if dupes:
        raise ValueError(f"Duplicate reference numerals: {dupes}")


validate()  # run at import — no separate smoke-test file


def n(key: str) -> int:
    """Return the reference numeral for a component key."""
    return NUMERALS[key]


# ---------------------------------------------------------------------------
# Drawing primitives — pure black line art on a 0..100 canvas
# ---------------------------------------------------------------------------
_LINE_W = 1.1
_NUM_FONT = 8
_LABEL_FONT = 8.5

Point = tuple[float, float]


def new_sheet(width_in: float = 8.0, height_in: float = 6.0):
    """A blank drawing sheet. Returns (fig, ax) on a 0..100 x 0..100 canvas."""
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def box(ax, x: float, y: float, w: float, h: float, label: str,
        numeral: int | None = None, fontsize: float = _LABEL_FONT) -> dict:
    """Draw a labelled rectangle; optional reference numeral with a short leader.
    (x, y) is the bottom-left corner. Returns a dict of anchor points for arrows:
      'c' center, 'l'/'r'/'t'/'b' edge midpoints (left/right/top/bottom)."""
    ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor="black",
                           linewidth=_LINE_W, antialiased=False))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fontsize, color="black")
    if numeral is not None:
        nx, ny = x - 2.5, y + h + 3.0
        ax.text(nx, ny, str(numeral), ha="center", va="center",
                fontsize=_NUM_FONT, color="black", fontweight="bold")
        ax.plot([nx + 0.8, x + 2.0], [ny - 1.2, y + h - 1.0],
                color="black", linewidth=0.6, antialiased=False)
    cx, cy = x + w / 2, y + h / 2
    return {"c": (cx, cy), "l": (x, cy), "r": (x + w, cy),
            "t": (cx, y + h), "b": (cx, y), "x": x, "y": y, "w": w, "h": h}


def arrow(ax, p0: Point, p1: Point, label: str | None = None) -> None:
    """Directional arrow p0 -> p1 (black line art)."""
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=11,
                                 linewidth=_LINE_W, color="black",
                                 antialiased=False, shrinkA=3, shrinkB=3))
    if label:
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        ax.text(mx, my + 1.5, label, ha="center", va="bottom",
                fontsize=_NUM_FONT, color="black")


def label(ax, x: float, y: float, text: str, fontsize: float = _NUM_FONT,
          ha: str = "center", va: str = "center") -> None:
    """Free-standing black text label."""
    ax.text(x, y, text, ha=ha, va=va, fontsize=fontsize, color="black")


# ---------------------------------------------------------------------------
# Export — vector PDF + genuine 1-bit PNG
# ---------------------------------------------------------------------------
def save(fig, name: str, outdir: str | Path = "patent_cap/figures",
         dpi: int = 300) -> tuple[Path, Path]:
    """Export a vector PDF and a thresholded 1-bit PNG. Returns (pdf, png)."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    pdf_path = outdir / f"{name}.pdf"
    png_path = outdir / f"{name}.png"
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    # Threshold to genuine 1-bit (no dithering) so the raster is bilevel, not greyscale.
    grey = Image.open(png_path).convert("L")
    bilevel = grey.point(lambda p: 255 if p >= 128 else 0).convert("1")
    bilevel.save(png_path)
    return pdf_path, png_path


def mid_grey_fraction(png_path: str | Path) -> float:
    """Fraction of pixels in the mid-grey band [30, 225]. Bilevel art => ~0."""
    arr = np.asarray(Image.open(png_path).convert("L"))
    return float(((arr > 30) & (arr < 225)).sum()) / arr.size


def is_bilevel(png_path: str | Path, tol: float = 0.002) -> bool:
    """True if the PNG is effectively black-and-white (negligible mid-grey)."""
    return mid_grey_fraction(png_path) <= tol
